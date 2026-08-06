"""RC-03 — PROBE CHỒNG LẤN: idle THÊM của kênh station_choice có gặp ĐƠN CHẾT không?

Phân xử H1 (lệch pha giờ) vs H2 (lệch vị trí) vs H3 (dispatcher) vs H4 (metric đo sai)
cho nghịch lý "−698 phút-đội chết ở trạm được giải phóng nhưng không chảy vào đơn".

## Nguyên tắc: CHỈ ĐỌC, KHÔNG SỬA REPO

Script này monkeypatch hai chỗ Ở RUNTIME (không sửa file nào trong repo):

1. `World.log` — bọc để, đúng KHOẢNH KHẮC một đơn hết hạn (`kind == "order_expired"`),
   chụp ảnh trạng thái + vị trí của MỌI actor. Đây là phép đo CHÍNH XÁC tại t_expire, không
   phải tái dựng gần đúng từ event log.
2. `World.run` — bọc để cắm thêm MỘT observer process lấy mẫu mỗi `SAMPLE_MIN` phút:
   đếm actor đang `state == IDLE` theo (cell, giờ) ⇒ bản đồ phút-idle theo ô/giờ.

Cả hai chỉ ĐỌC state, 0 RNG draw, 0 mutation. Rủi ro duy nhất về lý thuyết là thứ tự
tie-break của SimPy (eid) khi thêm process — nên có `--verify`: chạy cùng seed CÓ và KHÔNG
có probe rồi so từng số. Không xanh thì mọi kết luận dưới đây là rác.

## Định nghĩa ELIGIBLE (khớp rc-01, world.py:628)

Nhận được đơn ⇔ `state == ActorState.IDLE`. REST/CHARGING/ENROUTE/ON_TRIP/OFFLINE vô hình
với dispatcher. Probe đếm ĐÚNG điều kiện này (không dùng `actor.idle_min`) — đó là mũi kiểm H4.

Chạy:
    uv run python <path>/probe_idle_overlap.py --seeds 5 --seed0 1000 --out <json>
    uv run python <path>/probe_idle_overlap.py --verify        # cổng nhiễu-loạn
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics as st
import sys
import time
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve()
# Tìm root repo: đi lên tới khi thấy configs/pilot_dongda.yaml (script sống ở scratchpad
# HOẶC trong research/audit/... nên không hardcode số cấp).
_CAND = [
    pathlib.Path(r"C:/Users/Cuong/OneDrive - Hanoi University of Science and Technology/Documents/GitHub/My/GSM-Driver-Agent"),
]
for p in list(ROOT.parents):
    _CAND.append(p)
REPO = None
for c in _CAND:
    if (c / "configs/pilot_dongda.yaml").exists():
        REPO = c
        break
if REPO is None:
    raise SystemExit("không tìm được repo root (configs/pilot_dongda.yaml)")
sys.path.insert(0, str(REPO / "src"))

from gsm_sim.config import Config                      # noqa: E402
from gsm_sim.entities import ActorState                # noqa: E402
from gsm_sim.geo import grid_disk, haversine_km        # noqa: E402
from gsm_sim.metrics import summarize                  # noqa: E402
from gsm_sim.parallel import _cfg_with                 # noqa: E402
from gsm_sim.runner import run_once                    # noqa: E402
from gsm_sim.world import World                        # noqa: E402

# Kênh đo: ĐÚNG bộ của scripts/run_e01_station.py (E-01 station_choice, cô lập 1 cơ chế)
CH = {"shift_plan": False, "accept_lift": False, "shift_extend": False,
      "rest_window": False, "station_choice": True, "positioning_overrides": "off"}

SAMPLE_MIN = 1.0        # nhịp lấy mẫu observer idle (WAIT accrue theo lát 2′ ⇒ 1′ đủ mịn)

_ORIG_LOG = World.log
_ORIG_RUN = World.run

# `world.py` import `match_batch` vào namespace của nó ⇒ patch ĐÚNG tên đó.
import gsm_sim.world as _wmod                          # noqa: E402
_ORIG_MATCH = _wmod.match_batch
_CUR: dict = {}          # probe của world ĐANG chạy (tuần tự, một luồng)


def _counting_match(*a, **k):
    """Đếm phép gán Hunganian TRẢ VỀ và phép gán bị CỔNG COOLDOWN nuốt im lặng.

    Cổng ở `world.py:644` `continue` KHÔNG log gì: đơn được Hungarian gán cho đúng một tài xế
    trong tick đó, cặp bị cooldown ⇒ đơn MẤT TRỌN TICK (không ai khác được chào thay). Wrapper
    đánh giá ĐÚNG điều kiện đó, tại đúng `env.now`, TRƯỚC khi vòng chào ghi `offer_history`
    ⇒ số đếm khớp từng lượt với đường thật. Chỉ ĐỌC.
    """
    out = _ORIG_MATCH(*a, **k)
    pr = _CUR.get("probe")
    w = _CUR.get("world")
    if pr is None or w is None:
        return out
    now = float(w.env.now)
    pr["n_assign"] += len(out)
    for asg in out:
        t_last = w.offer_history.get((asg.order_id, asg.actor_id))
        if t_last is not None and (now - t_last) < w.offer_cooldown:
            pr["n_assign_cooldown_blocked"] += 1
            pr["cool_block_orders"][asg.order_id] += 1
            # phân biệt "slot gán bị lãng phí" (đếm lặp mỗi tick) với "CẶP khác nhau bị chặn"
            pr["cool_block_pairs"].add((asg.order_id, asg.actor_id))
    return out


def _probe_log(self, actor_id: int, kind: str, cell: str = "", **detail):
    _ORIG_LOG(self, actor_id, kind, cell, **detail)
    if kind != "order_expired":
        return
    pr = getattr(self, "_probe", None)
    if pr is None:
        return
    _snap_expired(self, int(detail.get("order_id", -1)),
                  str(detail.get("reason", "") or ""))


def _count_candidates(world: World, o, now: float) -> tuple:
    """Đếm ứng viên của đơn `o` tại thời điểm `now` — ĐÚNG hai tầng của dispatcher.

    `hex`  = actor IDLE có cell ∈ grid_disk(pickup, k_max)      → shortlist tầng 1
    `eta`  = actor IDLE có ETA(actor→pickup) ≤ eta_max          → ràng buộc THẬT tầng 2
    `both` = ỨNG VIÊN THẬT (qua cả hai) — tập mà Hungarian được phép gán
    `eta_not_hex` = DẢI MÙ của BUG-DISPATCH-SHORTLIST: với tới được nhưng bị loại âm thầm
    ETA tính y hệt `dispatcher._eta`: haversine × road_factor(cặp cell) ÷ eff_speed(pickup cell).
    """
    pr = world._probe
    hour = int(now // 60) % 24
    pc = o.pickup_cell
    disk = pr["disk_cache"].get(pc)
    if disk is None:
        disk = set(grid_disk(pc, pr["k_max"]))
        pr["disk_cache"][pc] = disk
    speed = world._eff_speed(hour, pc)          # ĐÚNG speed_fn mà dispatcher dùng
    eta_max = pr["eta_max"]
    cool = world.offer_cooldown
    oid = o.order_id

    n_idle = n_hex = n_eta = n_both = n_eta_not_hex = n_both_cool = 0
    min_km = math.inf
    min_eta = math.inf
    for a in world.actors.values():
        if a.state != ActorState.IDLE:          # eligibility DUY NHẤT (world.py:628)
            continue
        n_idle += 1
        d = haversine_km(a.lat, a.lon, o.pickup_lat, o.pickup_lon)
        fac = world._dfac(a.cell, pc)
        eta = d * fac / speed * 60.0
        in_hex = a.cell in disk
        feas = eta <= eta_max
        if d < min_km:
            min_km = d
        if eta < min_eta:
            min_eta = eta
        n_hex += in_hex
        n_eta += feas
        if in_hex and feas:
            n_both += 1
            t_last = world.offer_history.get((oid, a.actor_id))
            if t_last is not None and (now - t_last) < cool:
                n_both_cool += 1
        elif feas and not in_hex:
            n_eta_not_hex += 1
    return (n_idle, n_hex, n_eta, n_both, n_eta_not_hex, n_both_cool,
            None if min_km is math.inf else round(min_km, 3),
            None if min_eta is math.inf else round(min_eta, 2))


def _snap_expired(world: World, oid: int, reason: str) -> None:
    """Chụp ảnh ĐÚNG lúc đơn `oid` hết hạn: ai đang IDLE, cách pickup bao xa, ETA bao nhiêu."""
    pr = world._probe
    o = pr["orders"].get(oid)
    if o is None:
        return
    now = float(world.env.now)
    hour = int(now // 60) % 24
    pc = o.pickup_cell
    (n_idle, n_hex, n_eta, n_both, n_eta_not_hex, n_both_cool,
     min_km, min_eta) = _count_candidates(world, o, now)

    # đã từng được CHÀO cho ai chưa (offer_history sống suốt run)
    n_offered = pr["offer_count"].get(oid, 0)
    live = pr["order_live"].get(oid) or {}
    pr["expired"].append({
        "life_max_both": int(live.get("max_both", 0)),
        "life_max_eta": int(live.get("max_eta", 0)),
        "life_samples": int(live.get("n", 0)),
        "life_samples_with_cand": int(live.get("n_with_cand", 0)),
        "oid": oid, "t": round(now, 2), "hour": hour, "cell": pc, "reason": reason,
        "n_idle_world": n_idle,          # tổng tài xế rảnh TOÀN THÀNH PHỐ lúc đó (mũi H1)
        "n_hex": n_hex,                  # trong shortlist hex k=6 (~2,22 km)
        "n_eta": n_eta,                  # thoả ETA <= eta_max (bán kính THẬT của ràng buộc)
        "n_both": n_both,                # ỨNG VIÊN THẬT của dispatcher tại t_expire
        "n_eta_not_hex": n_eta_not_hex,  # DẢI MÙ BUG-DISPATCH-SHORTLIST (2,2–3,1 km)
        "n_both_cooldown": n_both_cool,  # ứng viên thật nhưng bị cooldown cặp chặn
        "min_km": min_km,                # đã round/None trong _count_candidates
        "min_eta": min_eta,
        "n_offers_ever": n_offered,
    })


def _idle_observer(world: World):
    """Observer LOG-ONLY: mỗi SAMPLE_MIN phút — (a) đếm actor IDLE theo (cell, giờ);
    (b) với MỌI đơn đang MỞ, đếm ứng viên khả thi ⇒ biết đơn có ứng viên ở BẤT KỲ lúc nào
    trong đời nó hay không (mũi phân xử H3 vs H2 mạnh hơn ảnh chụp tại t_expire). 0 RNG."""
    pr = world._probe
    per_cell_hour = pr["idle_cell_hour"]
    per_hour = pr["idle_hour"]
    live = pr["order_live"]
    while world.env.now < world.end_min:
        now = float(world.env.now)
        h = int(now // 60) % 24
        n = 0
        for a in world.actors.values():
            if a.state == ActorState.IDLE:
                per_cell_hour[(a.cell, h)] += SAMPLE_MIN
                n += 1
        per_hour[h] += n * SAMPLE_MIN
        pr["idle_sampled_min"] += n * SAMPLE_MIN
        pr["n_samples"] += 1
        for oid, o in world.open_orders.items():
            _, _, n_eta, n_both, _, _, _, _ = _count_candidates(world, o, now)
            row = live.get(oid)
            if row is None:
                row = live[oid] = {"max_both": 0, "max_eta": 0, "n": 0, "n_with_cand": 0}
            row["n"] += 1
            row["max_both"] = max(row["max_both"], n_both)
            row["max_eta"] = max(row["max_eta"], n_eta)
            row["n_with_cand"] += int(n_both >= 1)
        yield world.env.timeout(SAMPLE_MIN)


def _probe_run(self):
    disp = self.cfg.get("dispatcher")
    self._probe = {
        "orders": {o.order_id: o for o in self.orders},
        "k_max": int(disp["candidate_ring_k_max"]),
        "eta_max": float(disp["eta_max_min"]),
        "disk_cache": {},
        "expired": [],
        "idle_cell_hour": defaultdict(float),
        "idle_hour": defaultdict(float),
        "idle_sampled_min": 0.0,
        "n_samples": 0,
        "order_live": {},
        "n_assign": 0,
        "n_assign_cooldown_blocked": 0,
        "cool_block_orders": Counter(),
        "cool_block_pairs": set(),
        "offer_count": defaultdict(int),
        "station_cells": sorted({s.cell for s in self.stations}),
    }
    # đếm số lần một đơn được CHÀO (mỗi cặp mới = một lần chào) — đọc offer_history sau run
    self.env.process(_idle_observer(self))
    _CUR["probe"], _CUR["world"] = self._probe, self
    try:
        out = _ORIG_RUN(self)
    finally:
        _CUR.clear()
    pr = self._probe
    oc = Counter(oid for (oid, _aid) in self.offer_history)
    pr["offer_count"] = dict(oc)
    # bù lại n_offers_ever cho các bản ghi đã chụp (chụp lúc t_expire thấy lịch sử TỚI LÚC ĐÓ,
    # nhưng offer chỉ có thể xảy ra TRƯỚC khi đơn hết hạn ⇒ hai số phải trùng; giữ cả hai để
    # lỡ lệch thì thấy được)
    for r in pr["expired"]:
        r["n_offers_total"] = int(oc.get(r["oid"], 0))
        r["n_cool_blocked_assigns"] = int(pr["cool_block_orders"].get(r["oid"], 0))
    return out


def install() -> None:
    World.log = _probe_log
    World.run = _probe_run_capture
    _wmod.match_batch = _counting_match


def uninstall() -> None:
    World.log = _ORIG_LOG
    World.run = _ORIG_RUN
    _wmod.match_batch = _ORIG_MATCH


# ---------------------------------------------------------------- chạy một arm

def run_arm(cfg: Config, seed: int, arm: str):
    c = (_cfg_with(cfg, enabled=False, actor_id=None, channels=None) if arm == "A"
         else _cfg_with(cfg, enabled=True, actor_id=None, channels=CH, coverage="all"))
    res = run_once(c, seed)
    return res


# `run_once` không trả world ⇒ cất probe của run VỪA CHẠY vào đây (single-thread, tuần tự)
_LAST: dict = {}


def _probe_run_capture(self):
    out = _probe_run(self)
    _LAST["probe"] = self._probe
    _LAST["world"] = None          # không giữ world (tránh giữ RAM)
    return out


def _kinds_by_order(res) -> dict:
    """Hậu kiểm từ event log: mỗi đơn bị TỪ CHỐI / BỎ VÌ PIN bao nhiêu lần."""
    dec: Counter = Counter()
    soc: Counter = Counter()
    for e in res.events:
        oid = e.detail.get("order_id")
        if oid is None:
            continue
        if e.kind == "order_declined":
            dec[int(oid)] += 1
        elif e.kind == "order_skipped_soc":
            soc[int(oid)] += 1
    return {"declined": dec, "soc": soc}


def collect(cfg: Config, seed: int, arm: str) -> dict:
    res = run_arm(cfg, seed, arm)
    pr = _LAST["probe"]
    ko = _kinds_by_order(res)
    for r in pr["expired"]:
        r["n_declined"] = int(ko["declined"].get(r["oid"], 0))
        r["n_soc_skip"] = int(ko["soc"].get(r["oid"], 0))
    s = summarize(res)
    idle_counter = sum(float(a.idle_min) for a in res.actors)
    rest_counter = sum(float(a.rest_min) for a in res.actors)
    charge_counter = sum(float(a.charge_min) for a in res.actors)
    empty_counter = sum(float(a.empty_min) for a in res.actors)
    occ_counter = sum(float(a.occupied_min) for a in res.actors)
    online_counter = sum(float(a.online_min) for a in res.actors)
    return {
        "seed": seed, "arm": arm,
        "served_rate": s["served_rate"], "orders_completed": s["orders_completed"],
        "orders_total": len(res.orders),
        "expired_events": sum(1 for e in res.events if e.kind == "order_expired"),
        "expired": pr["expired"],
        "idle_cell_hour": {f"{c}|{h}": v for (c, h), v in pr["idle_cell_hour"].items()},
        "idle_hour": {str(h): v for h, v in pr["idle_hour"].items()},
        "idle_sampled_min": pr["idle_sampled_min"],
        "n_samples": pr["n_samples"],
        "station_cells": pr["station_cells"],
        "n_assign": pr["n_assign"],
        "n_assign_cooldown_blocked": pr["n_assign_cooldown_blocked"],
        "n_cool_block_pairs": len(pr["cool_block_pairs"]),
        "n_offer_pairs": len(pr["offer_count"]) if isinstance(pr["offer_count"], dict) else 0,
        "offers_made": sum(int(a.orders_offered) for a in res.actors),
        "ledger": {"idle_min": round(idle_counter, 1), "rest_min": round(rest_counter, 1),
                   "charge_min": round(charge_counter, 1), "empty_min": round(empty_counter, 1),
                   "occupied_min": round(occ_counter, 1),
                   "online_min": round(online_counter, 1)},
    }


# ---------------------------------------------------------------- verify (cổng nhiễu-loạn)

def verify(cfg: Config, seed: int) -> dict:
    def _fp(res) -> dict:
        s = summarize(res)
        return {"served_rate": s["served_rate"], "orders_completed": s["orders_completed"],
                "expired": sum(1 for e in res.events if e.kind == "order_expired"),
                "n_events": len(res.events),
                "payout": sum(int(a.payout_vnd) for a in res.actors),
                "idle_min": round(sum(float(a.idle_min) for a in res.actors), 3),
                "charge_min": round(sum(float(a.charge_min) for a in res.actors), 3)}
    uninstall()
    base_a = _fp(run_arm(cfg, seed, "A"))
    base_b = _fp(run_arm(cfg, seed, "B"))
    install()
    World.run = _probe_run_capture
    p_a = _fp(run_arm(cfg, seed, "A"))
    p_b = _fp(run_arm(cfg, seed, "B"))
    p_a2 = _fp(run_arm(cfg, seed, "A"))
    return {"seed": seed, "no_probe_A": base_a, "probe_A": p_a, "probe_A_repeat": p_a2,
            "no_probe_B": base_b, "probe_B": p_b,
            "A_identical": base_a == p_a, "B_identical": base_b == p_b,
            "A_exact_repeat": p_a == p_a2}


# ---------------------------------------------------------------- tổng hợp

def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 4)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return _pearson(rank(xs), rank(ys))


def agg_arm(rows: list[dict]) -> dict:
    """Gộp nhiều seed của MỘT arm."""
    n = len(rows)
    real = []          # đơn hết hạn THẬT (không phải end_of_run)
    eor = 0
    for r in rows:
        for e in r["expired"]:
            if e["reason"] == "end_of_run":
                eor += 1
            else:
                real.append(e)
    def _sh(pred) -> float:
        return round(sum(1 for e in real if pred(e)) / len(real), 4) if real else 0.0
    idle_ch: dict[str, float] = defaultdict(float)
    for r in rows:
        for k, v in r["idle_cell_hour"].items():
            idle_ch[k] += v / n
    idle_h: dict[int, float] = defaultdict(float)
    for r in rows:
        for k, v in r["idle_hour"].items():
            idle_h[int(k)] += v / n
    exp_cell: Counter = Counter()
    exp_hour: Counter = Counter()
    for e in real:
        exp_cell[e["cell"]] += 1.0 / n
        exp_hour[e["hour"]] += 1.0 / n
    idle_cell: dict[str, float] = defaultdict(float)
    for k, v in idle_ch.items():
        idle_cell[k.split("|")[0]] += v
    return {
        "n_seeds": n,
        "expired_real_per_day": round(len(real) / n, 2),
        "expired_end_of_run_per_day": round(eor / n, 2),
        "n_records": len(real),
        "share_zero_idle_world": _sh(lambda e: e["n_idle_world"] == 0),
        "share_has_candidate": _sh(lambda e: e["n_both"] >= 1),
        "share_has_eta_feasible": _sh(lambda e: e["n_eta"] >= 1),
        "share_hex_only": _sh(lambda e: e["n_hex"] >= 1),
        "share_blind_band_only": _sh(lambda e: e["n_both"] == 0 and e["n_eta_not_hex"] >= 1),
        "share_candidate_all_cooldown": _sh(
            lambda e: e["n_both"] >= 1 and e["n_both"] == e["n_both_cooldown"]),
        "share_ever_offered": _sh(lambda e: e["n_offers_total"] >= 1),
        # --- ĐỜI ĐƠN (mỗi 1′ trong 5–10′ nó sống), không chỉ ảnh chụp lúc chết ---
        "share_life_had_candidate": _sh(lambda e: e["life_max_both"] >= 1),
        "share_life_had_eta_feasible": _sh(lambda e: e["life_max_eta"] >= 1),
        "share_life_cand_never_offered": _sh(
            lambda e: e["life_max_both"] >= 1 and e["n_offers_total"] == 0),
        "share_life_cand_offered_fewer": _sh(
            lambda e: e["life_max_both"] >= 2 and e["n_offers_total"] <= 1),
        "mean_life_max_both": round(st.mean([e["life_max_both"] for e in real]), 3) if real else 0,
        "mean_life_samples": round(st.mean([e["life_samples"] for e in real]), 2) if real else 0,
        # --- ảnh chụp t_expire: phân rã 'có ứng viên' theo lịch sử chào ---
        "share_cand_at_death_never_offered": _sh(
            lambda e: e["n_both"] >= 1 and e["n_offers_total"] == 0),
        "share_cand_at_death_declined": _sh(
            lambda e: e["n_both"] >= 1 and e["n_declined"] >= 1),
        "hist_n_both_at_death": {
            "0": _sh(lambda e: e["n_both"] == 0), "1": _sh(lambda e: e["n_both"] == 1),
            "2": _sh(lambda e: e["n_both"] == 2), "3+": _sh(lambda e: e["n_both"] >= 3)},
        "hist_min_km_band": {
            "<=2.22 (trong hex)": _sh(lambda e: e["min_km"] is not None and e["min_km"] <= 2.22),
            "2.22-3.14 (dải mù)": _sh(lambda e: e["min_km"] is not None
                                      and 2.22 < e["min_km"] <= 3.14),
            ">3.14": _sh(lambda e: e["min_km"] is not None and e["min_km"] > 3.14),
            "khong co ai idle": _sh(lambda e: e["min_km"] is None)},
        "share_declined_once": _sh(lambda e: e["n_declined"] >= 1),
        # --- cổng cooldown nuốt phép gán (H3 đo trực tiếp) ---
        "assign_per_day": round(st.mean([r["n_assign"] for r in rows]), 1),
        "assign_cooldown_blocked_per_day": round(
            st.mean([r["n_assign_cooldown_blocked"] for r in rows]), 1),
        "share_assign_dropped_by_cooldown": round(
            st.mean([r["n_assign_cooldown_blocked"] / r["n_assign"] for r in rows]), 4),
        "offers_made_per_day": round(st.mean([r["offers_made"] for r in rows]), 1),
        "cool_block_distinct_pairs_per_day": round(
            st.mean([r["n_cool_block_pairs"] for r in rows]), 1),
        "check_assign_minus_blocked_minus_offers": round(
            st.mean([r["n_assign"] - r["n_assign_cooldown_blocked"] - r["offers_made"]
                     for r in rows]), 2),
        "share_dead_with_cool_blocked_assign": _sh(lambda e: e["n_cool_blocked_assigns"] >= 1),
        "mean_cool_blocked_assigns_per_dead": round(
            st.mean([e["n_cool_blocked_assigns"] for e in real]), 2) if real else 0,
        "share_soc_skipped": _sh(lambda e: e["n_soc_skip"] >= 1),
        "mean_n_idle_world": round(st.mean([e["n_idle_world"] for e in real]), 2) if real else 0,
        "mean_n_both": round(st.mean([e["n_both"] for e in real]), 3) if real else 0,
        "mean_n_eta": round(st.mean([e["n_eta"] for e in real]), 3) if real else 0,
        "mean_n_eta_not_hex": round(st.mean([e["n_eta_not_hex"] for e in real]), 3) if real else 0,
        "median_min_km": round(st.median([e["min_km"] for e in real if e["min_km"] is not None]), 3) if real else None,
        "median_min_eta": round(st.median([e["min_eta"] for e in real if e["min_eta"] is not None]), 2) if real else None,
        "idle_sampled_min_per_day": round(st.mean([r["idle_sampled_min"] for r in rows]), 1),
        "idle_counter_min_per_day": round(st.mean([r["ledger"]["idle_min"] for r in rows]), 1),
        "ledger": {k: round(st.mean([r["ledger"][k] for r in rows]), 1)
                   for k in rows[0]["ledger"]},
        "served_rate": round(st.mean([r["served_rate"] for r in rows]), 4),
        "orders_completed": round(st.mean([r["orders_completed"] for r in rows]), 2),
        "expired_events": round(st.mean([r["expired_events"] for r in rows]), 2),
        "_idle_cell_hour": dict(idle_ch),
        "_idle_cell": dict(idle_cell),
        "_idle_hour": {str(k): round(v, 1) for k, v in sorted(idle_h.items())},
        "_exp_cell": {k: round(v, 3) for k, v in exp_cell.items()},
        "_exp_hour": {str(k): round(v, 2) for k, v in sorted(exp_hour.items())},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    cfg = Config.load(str(REPO / "configs/pilot_dongda.yaml"))
    t0 = time.time()

    if args.verify:
        v = verify(cfg, args.seed0)
        print(json.dumps(v, ensure_ascii=False, indent=1))
        print(f"  {(time.time()-t0)/60:.1f}'")
        return 0 if (v["A_identical"] and v["B_identical"] and v["A_exact_repeat"]) else 1

    install()
    World.run = _probe_run_capture
    rows_a, rows_b = [], []
    for s in range(args.seed0, args.seed0 + args.seeds):
        rows_a.append(collect(cfg, s, "A"))
        rows_b.append(collect(cfg, s, "B"))
        print(f"   seed {s}  A exp={rows_a[-1]['expired_events']} "
              f"B exp={rows_b[-1]['expired_events']}  {(time.time()-t0)/60:.1f}'", flush=True)

    A, B = agg_arm(rows_a), agg_arm(rows_b)
    station_cells = set(rows_a[0]["station_cells"])

    # --- (2) bản đồ cell: Δidle vs đơn chết
    cells = set(A["_idle_cell"]) | set(B["_idle_cell"]) | set(A["_exp_cell"]) | set(B["_exp_cell"])
    d_idle_cell = {c: round(B["_idle_cell"].get(c, 0.0) - A["_idle_cell"].get(c, 0.0), 2)
                   for c in cells}
    top_didle = sorted(d_idle_cell.items(), key=lambda kv: -kv[1])[:10]
    top_exp = sorted(A["_exp_cell"].items(), key=lambda kv: -kv[1])[:10]
    d_station = round(sum(v for c, v in d_idle_cell.items() if c in station_cells), 1)
    d_total = round(sum(d_idle_cell.values()), 1)
    idleA_station = round(sum(v for c, v in A["_idle_cell"].items() if c in station_cells), 1)
    idleA_total = round(sum(A["_idle_cell"].values()), 1)
    expA_station = round(sum(v for c, v in A["_exp_cell"].items() if c in station_cells), 2)
    expA_total = round(sum(A["_exp_cell"].values()), 2)

    cl = sorted(cells)
    xs = [d_idle_cell.get(c, 0.0) for c in cl]
    ys = [A["_exp_cell"].get(c, 0.0) for c in cl]
    zs = [A["_idle_cell"].get(c, 0.0) for c in cl]

    # --- (3) giờ
    hours = [str(h) for h in range(24)]
    d_idle_hour = {h: round(float(B["_idle_hour"].get(h, 0.0)) - float(A["_idle_hour"].get(h, 0.0)), 1)
                   for h in hours}
    hx = [d_idle_hour[h] for h in hours]
    hy = [float(A["_exp_hour"].get(h, 0.0)) for h in hours]
    hz = [float(A["_idle_hour"].get(h, 0.0)) for h in hours]

    out = {
        "arm_A": A, "arm_B": B,
        "delta": {
            **{k: round(B[k] - A[k], 4) for k in A
               if not k.startswith("_") and isinstance(A[k], (int, float))
               and not isinstance(A[k], bool) and k != "n_seeds"},
            "ledger": {k: round(B["ledger"][k] - A["ledger"][k], 1) for k in A["ledger"]},
        },
        "map_cell": {
            "top10_delta_idle": [{"cell": c, "d_idle_min": v, "is_station": c in station_cells,
                                  "expired_A": A["_exp_cell"].get(c, 0.0),
                                  "idle_A": round(A["_idle_cell"].get(c, 0.0), 1)}
                                 for c, v in top_didle],
            "top10_expired_A": [{"cell": c, "expired_A": round(v, 2),
                                 "is_station": c in station_cells,
                                 "d_idle_min": d_idle_cell.get(c, 0.0),
                                 "idle_A": round(A["_idle_cell"].get(c, 0.0), 1)}
                                for c, v in top_exp],
            "station_cells_n": len(station_cells),
            "d_idle_in_station_cells": d_station, "d_idle_total": d_total,
            "d_idle_station_share": round(d_station / d_total, 4) if d_total else None,
            "idleA_in_station_cells": idleA_station, "idleA_total": idleA_total,
            "idleA_station_share": round(idleA_station / idleA_total, 4) if idleA_total else None,
            "expiredA_in_station_cells": expA_station, "expiredA_total": expA_total,
            "expiredA_station_share": round(expA_station / expA_total, 4) if expA_total else None,
            "corr_pearson_dIdle_vs_expired": _pearson(xs, ys),
            "corr_spearman_dIdle_vs_expired": _spearman(xs, ys),
            "corr_pearson_idleA_vs_expired": _pearson(zs, ys),
            "corr_spearman_idleA_vs_expired": _spearman(zs, ys),
        },
        "map_hour": {
            "idle_A": A["_idle_hour"], "idle_B": B["_idle_hour"], "d_idle": d_idle_hour,
            "expired_A": A["_exp_hour"], "expired_B": B["_exp_hour"],
            "corr_pearson_dIdle_vs_expired": _pearson(hx, hy),
            "corr_spearman_dIdle_vs_expired": _spearman(hx, hy),
            "corr_pearson_idleA_vs_expired": _pearson(hz, hy),
        },
        "per_seed": {
            "A": [{k: r[k] for k in ("seed", "served_rate", "orders_completed",
                                     "expired_events", "idle_sampled_min", "ledger")}
                  for r in rows_a],
            "B": [{k: r[k] for k in ("seed", "served_rate", "orders_completed",
                                     "expired_events", "idle_sampled_min", "ledger")}
                  for r in rows_b],
        },
        "sample_records_A_seed0": [r for r in rows_a[0]["expired"]
                                   if r["reason"] != "end_of_run"][:15],
        "params": {"k_max": 6, "eta_max_min": 11, "sample_min": SAMPLE_MIN,
                   "channels": CH, "coverage": "all", "seeds": list(range(args.seed0, args.seed0 + args.seeds))},
    }
    for k in ("_idle_cell_hour", "_idle_cell"):
        out["arm_A"].pop(k, None)
        out["arm_B"].pop(k, None)
    if args.out:
        p = pathlib.Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        # bản ghi THÔ từng đơn chết (để cross-tab hậu kiểm, KHÔNG đưa vào artifact repo)
        rec = p.with_suffix(".records.json")
        rec.write_text(json.dumps(
            {"A": [r["expired"] for r in rows_a], "B": [r["expired"] for r in rows_b]},
            ensure_ascii=False), encoding="utf-8")
        print(f"  records: {rec}")
        print(f"  artifact: {p}")
    else:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"  total {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
