"""pb2 — PHẢN BIỆN THIẾT KẾ của S4 / kênh vị trí (kênh DUY NHẤT đang ship).

Bốn câu hỏi thiết kế, trả lời bằng CODE + ĐO (không trích nhãn):

(a) HÀM MỤC TIÊU của S4 là gì? Tối ưu cho AI? Ai trả giá?
(b) Trần tính trên MỘT ô res-9 (~0,35 km) trong khi dispatcher phục vụ từ ~2,22 km
    ⇒ người rảnh bị đẩy VÀO ô đông, cạnh tranh với người ĐÃ Ở ĐÓ mà trần không thấy.
    ĐO: đơn của nhóm bận có giảm không? giảm ở đâu? có tương quan với luồng relocate ĐẾN không?
(c) S4 có mô hình hoá CHI PHÍ CƠ HỘI của người bị đẩy đi không (km rỗng, thời gian)?
(d) Có ràng buộc CÔNG BẰNG nào không?

Ba arm CÙNG CRN, n=30 seed (cùng cửa sổ 3300–3329 với c9a–c9d):
  A    = advisor TẮT
  B    = advisor BẬT (kênh positioning, coverage=all) — đường đang ship
  SHUF = như B nhưng hoán vị `assigned_target` giữa chính các allocation (bản MÙ của c9d)

⚠ `probe.wait_stats` được BẬT để lấy panel (actor, bucket) → ô đang đứng rỗi.
   Đã KIỂM bit-identity (payout + toàn bộ event stream, seed 3300/3301) trước khi dùng.

Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb2-thiet-ke-S4.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import random
import statistics
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_core.solvers import capacity_alloc as CA  # noqa: E402
from gsm_sim.config import Config  # noqa: E402
from gsm_sim.geo import cell_distance_km  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_name("pb2-DO-raw.json")   # dữ liệu THÔ; findings ở pb2-thiet-ke-S4.json
SEEDS = list(range(3300, 3330))
NBOOT = 2000
_THAT_SOLVE = CA.solve


# ---------------------------------------------------------------- ghi lại batch S4
class _Ghi:
    """Bọc solver THẬT: không đổi gì, chỉ chép lại (ai, report) từng lô."""

    def __init__(self):
        self.lo = []

    def __call__(self, ai):
        rep = _THAT_SOLVE(ai)
        self.lo.append((copy.deepcopy(ai), copy.deepcopy(rep)))
        return rep


class _Hoanvi:
    """Bản MÙ (y hệt c9d): giữ nguyên ai/bao nhiêu/tập ô + số suất, chỉ phá GHÉP CẶP."""

    def __init__(self, seed: int):
        self.rng = random.Random(900000 + seed)

    def __call__(self, ai):
        rep = _THAT_SOLVE(ai)
        al = (rep.get("solution") or {}).get("allocations") or []
        if len(al) > 1:
            d = [a["assigned_target"] for a in al]
            self.rng.shuffle(d)
            for a, t in zip(al, d):
                a["assigned_target"] = t
        return rep


# ---------------------------------------------------------------- phân tích hàm mục tiêu
def _phan_tich_lo(ai: dict, rep: dict) -> dict:
    """Tái hiện ĐÚNG hàm mục tiêu của `_assign_kind` cho nhánh standby_zone."""
    cands = [c for c in ai["candidates"] if c["advice_kind"] == "standby_zone"]
    zone_cap = {(z["zone"], z["bucket"]): int(z["capacity"]) for z in ai["zone_supply"]}
    nS = sum(zone_cap.values())
    nC = len(cands)
    pen = {c["driver_id"]: (c["priority_soc"] / 100.0 if c.get("priority_soc") is not None
                            else 0.5) for c in cands}
    tgt = {c["driver_id"]: c["target"] for c in cands}

    allocs = [a for a in (rep.get("solution") or {}).get("allocations") or []
              if a["advice_kind"] == "standby_zone"]
    cost_H = sum(pen[a["driver_id"]] for a in allocs) \
        + 10.0 * sum(1 for a in allocs if a["assigned_target"] != tgt[a["driver_id"]])

    # GREEDY tầm thường: sắp theo (pen, driver_id) — ĐÚNG thứ tự solver tự sắp (`cand`
    # sorted key ((priority_soc), driver_id)) — cho đúng target nếu còn chỗ, hết thì nhét
    # vào bất kỳ suất trống nào còn lại.
    free = Counter({z: c for (z, _b), c in zone_cap.items()})
    order = sorted(cands, key=lambda c: ((c.get("priority_soc")
                   if c.get("priority_soc") is not None else 999.0), c["driver_id"]))
    da_gan, con = [], []
    for c in order:
        if free[c["target"]] > 0:
            free[c["target"]] -= 1
            da_gan.append((c["driver_id"], 0))
        else:
            con.append(c)
    for c in con:
        for z in sorted(free):
            if free[z] > 0:
                free[z] -= 1
                da_gan.append((c["driver_id"], 1))
                break
    cost_G = sum(pen[d] for d, _m in da_gan) + 10.0 * sum(m for _d, m in da_gan)

    # NGẪU NHIÊN (đối chứng ĐỘ PHÂN GIẢI của hàm mục tiêu): lấy nC' = min(nC,nS) người
    # ĐẦU danh sách driver_id (bỏ qua pen) và nhét vào suất trống theo alphabet.
    free2 = Counter({z: c for (z, _b), c in zone_cap.items()})
    ng = sorted(cands, key=lambda c: c["driver_id"])[:min(nC, nS)]
    cost_R = 0.0
    for c in ng:
        cost_R += pen[c["driver_id"]]
        if free2[c["target"]] > 0:
            free2[c["target"]] -= 1
        else:
            for z in sorted(free2):
                if free2[z] > 0:
                    free2[z] -= 1
                    cost_R += 10.0
                    break
    return {
        "nC": nC, "nS": nS, "n_gan": len(allocs),
        "n_stagger": sum(1 for a in allocs if a["assigned_target"] != tgt[a["driver_id"]]),
        "cost_H": cost_H, "cost_G": cost_G, "cost_R": cost_R,
        "khan": nC > nS,
        "zone_keys": sorted(ai["zone_supply"][0].keys()) if ai["zone_supply"] else [],
        "cand_keys": sorted(cands[0].keys()) if cands else [],
        "soc_gan": [round(100.0 - pen[a["driver_id"]] * 100.0, 1) for a in allocs],
    }


# ---------------------------------------------------------------- tiện ích thống kê
def _boot(xs, rng, n=NBOOT):
    if not xs:
        return (0.0, 0.0)
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return (m[int(0.025 * n)], m[int(0.975 * n)])


def _gini(vs):
    v = sorted(float(x) for x in vs)
    n = len(v)
    s = sum(v)
    if n == 0 or s <= 0:
        return 0.0
    return (2.0 * sum((i + 1) * x for i, x in enumerate(v)) / (n * s)) - (n + 1.0) / n


def _tom(r):
    """Rút các đại lượng per-actor + panel từ một RunResult."""
    ac = {a.actor_id: a for a in r.actors}
    gan, di = set(), set()
    arrivals = []          # (t, to_cell, actor)
    for e in r.events:
        d = e.detail or {}
        if e.kind == "standby_alloc":
            gan.update(d.get("assigned_ids") or [])
        elif e.kind == "standby_followed":
            di.add(e.actor_id)
            arrivals.append((e.t_min, d.get("to_cell"), e.actor_id, e.cell))
    served = Counter(e.cell for e in r.events
                     if e.kind == "order_matched" and (e.detail or {}).get("reason") == "accepted")
    panel = []             # (t, {actor: cell})
    for e in r.events:
        if e.kind == "probe_wait_stats":
            panel.append((e.t_min, {int(k): v[0] for k, v in (e.detail or {})
                                    .get("streaks", {}).items()}))
    return {
        "payout": {i: float(a.payout_vnd) for i, a in ac.items()},
        "trips": {i: int(a.orders_completed) for i, a in ac.items()},
        "idle": {i: float(a.idle_min) for i, a in ac.items()},
        "empty": {i: float(a.empty_min) for i, a in ac.items()},
        "km": {i: float(a.km_driven) for i, a in ac.items()},
        "gan": gan, "di": di, "arrivals": arrivals, "served": served, "panel": panel,
        "expired": sum(1 for e in r.events if e.kind == "order_expired"),
        "dropoff": sum(1 for e in r.events if e.kind == "dropoff"),
    }


def _phoi_nhiem(tb, b_min):
    """exposure = số lượt probe mà ô đang đứng rỗi của actor NHẬN ít nhất 1 lượt
    relocate-standby của NGƯỜI KHÁC trong cửa sổ ±bucket."""
    ex = defaultdict(int)
    for t, mp in tb["panel"]:
        for aid, cell in mp.items():
            k = sum(1 for (ta, tc, aa, _fc) in tb["arrivals"]
                    if tc == cell and aa != aid and abs(ta - t) <= b_min)
            if k:
                ex[aid] += 1
    return ex


def main() -> None:
    raw = copy.deepcopy(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml")
                                       .read_text(encoding="utf-8")))
    raw.setdefault("probe", {})["wait_stats"] = True
    cfg = Config(raw, ROOT)
    b_min = float(cfg.get("advice.bucket_min", 30))

    lo_all, rows = [], []
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        ghi = _Ghi()
        CA.solve = ghi
        try:
            rb = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                    coverage="all"), seed)
        finally:
            CA.solve = _THAT_SOLVE
        hv = _Hoanvi(seed)
        CA.solve = hv
        try:
            rs = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                    coverage="all"), seed)
        finally:
            CA.solve = _THAT_SOLVE

        ta, tb, ts = _tom(ra), _tom(rb), _tom(rs)
        lo_all += [_phan_tich_lo(ai, rp) for ai, rp in ghi.lo]

        # khoảng cách relocate-standby THẬT (km) — S4 không hề có số này trong cost
        km_st = [cell_distance_km(rb.grid, fc, tc)
                 for (_t, tc, _a, fc) in tb["arrivals"] if tc and fc]

        ids = sorted(ta["payout"])
        dpay = {i: tb["payout"][i] - ta["payout"][i] for i in ids}
        dtrip = {i: tb["trips"][i] - ta["trips"][i] for i in ids}
        xep = sorted(ids, key=lambda i: ta["idle"][i])
        t3 = len(xep) // 3
        nhom_idle = {"it": xep[:t3], "giua": xep[t3:2 * t3], "nhieu": xep[2 * t3:]}

        g_di = sorted(tb["di"])
        g_gan_ko_di = sorted(tb["gan"] - tb["di"])
        g_ko = sorted(set(ids) - tb["gan"])

        ex_b = _phoi_nhiem(tb, b_min)
        ko_co_ex = [i for i in g_ko if ex_b.get(i, 0) > 0]
        ko_khong_ex = [i for i in g_ko if ex_b.get(i, 0) == 0]

        # ô NHẬN người: cầu được phục vụ có tăng theo không?
        inflow = Counter(tc for (_t, tc, _a, _f) in tb["arrivals"] if tc)
        d_served_in = sum(tb["served"][c] - ta["served"][c] for c in inflow)
        # ô NGUỒN (nơi người rời đi)
        outflow = Counter(fc for (_t, _tc, _a, fc) in tb["arrivals"] if fc)
        d_served_out = sum(tb["served"][c] - ta["served"][c] for c in outflow)

        # SHUF: cùng phép đo phơi nhiễm, để biết phơi nhiễm có cần THÔNG TIN không
        dpay_s = {i: ts["payout"][i] - ta["payout"][i] for i in ids}
        ex_s = _phoi_nhiem(ts, b_min)
        s_ko = sorted(set(ids) - ts["gan"])
        s_ex = [i for i in s_ko if ex_s.get(i, 0) > 0]
        s_kex = [i for i in s_ko if ex_s.get(i, 0) == 0]

        rows.append({
            "seed": seed,
            "n_gan": len(tb["gan"]), "n_di": len(tb["di"]), "n_actor": len(ids),
            "km_standby_tong": sum(km_st), "km_standby_tb": statistics.mean(km_st) if km_st else 0.0,
            "d_payout_toan_doi": statistics.mean(list(dpay.values())),
            "d_payout_tuyet_doi": statistics.mean([abs(v) for v in dpay.values()]),
            "d_trip_toan_doi": sum(dtrip.values()),
            "d_dropoff": tb["dropoff"] - ta["dropoff"],
            "d_expired": tb["expired"] - ta["expired"],
            "gini_A": _gini(ta["payout"].values()), "gini_B": _gini(tb["payout"].values()),
            "p10_A": sorted(ta["payout"].values())[len(ids) // 10],
            "p10_B": sorted(tb["payout"].values())[len(ids) // 10],
            "nhom": {k2: {"n": len(v),
                          "dpay": statistics.mean([dpay[i] for i in v]) if v else 0.0,
                          "dtrip": statistics.mean([dtrip[i] for i in v]) if v else 0.0}
                     for k2, v in (("di", g_di), ("gan_ko_di", g_gan_ko_di), ("ko_cham", g_ko),
                                   *nhom_idle.items())},
            "empty_di": statistics.mean([tb["empty"][i] - ta["empty"][i] for i in g_di])
            if g_di else 0.0,
            "km_di": statistics.mean([tb["km"][i] - ta["km"][i] for i in g_di]) if g_di else 0.0,
            "phoi_nhiem": {
                "n_co": len(ko_co_ex), "n_khong": len(ko_khong_ex),
                "dpay_co": statistics.mean([dpay[i] for i in ko_co_ex]) if ko_co_ex else 0.0,
                "dpay_khong": statistics.mean([dpay[i] for i in ko_khong_ex])
                if ko_khong_ex else 0.0,
                "dtrip_co": statistics.mean([dtrip[i] for i in ko_co_ex]) if ko_co_ex else 0.0,
                "dtrip_khong": statistics.mean([dtrip[i] for i in ko_khong_ex])
                if ko_khong_ex else 0.0,
            },
            "phoi_nhiem_SHUF": {
                "n_co": len(s_ex), "n_khong": len(s_kex),
                "dpay_co": statistics.mean([dpay_s[i] for i in s_ex]) if s_ex else 0.0,
                "dpay_khong": statistics.mean([dpay_s[i] for i in s_kex]) if s_kex else 0.0,
            },
            "inflow_cells": len(inflow), "inflow_n": sum(inflow.values()),
            "d_served_o_nhan": d_served_in, "d_served_o_nguon": d_served_out,
        })
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed")

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "n_lo_S4": len(lo_all)}

    # ---- (a) HÀM MỤC TIÊU
    zk = Counter(tuple(x["zone_keys"]) for x in lo_all)
    ck = Counter(tuple(x["cand_keys"]) for x in lo_all)
    n_khan = sum(1 for x in lo_all if x["khan"])
    n_stag = sum(x["n_stagger"] for x in lo_all)
    bang = sum(1 for x in lo_all if abs(x["cost_H"] - x["cost_G"]) < 1e-9)
    bang_R = sum(1 for x in lo_all if abs(x["cost_H"] - x["cost_R"]) < 1e-9)
    out["a_ham_muc_tieu"] = {
        "n_lo": len(lo_all),
        "zone_supply_keys": {"/".join(k): v for k, v in zk.items()},
        "candidate_keys": {"/".join(k): v for k, v in ck.items()},
        "lo_khan_nC>nS": n_khan, "pct_khan": n_khan / max(1, len(lo_all)),
        "tong_n_gan": sum(x["n_gan"] for x in lo_all),
        "tong_stagger": n_stag,
        "lo_greedy_bang_hungarian": bang, "pct_greedy_bang": bang / max(1, len(lo_all)),
        "lo_naive_bang_hungarian": bang_R, "pct_naive_bang": bang_R / max(1, len(lo_all)),
        "nC_tb": statistics.mean([x["nC"] for x in lo_all]),
        "nS_tb": statistics.mean([x["nS"] for x in lo_all]),
        "soc_gan_min": min([min(x["soc_gan"]) for x in lo_all if x["soc_gan"]], default=None),
        "n_gan_soc_duoi_20": sum(1 for x in lo_all for s in x["soc_gan"] if s < 20.0),
    }
    print("\n=== (a) HÀM MỤC TIÊU S4 ===")
    print(f"  lô standby: {len(lo_all)} | zone_supply mang khoá: {list(zk)} ")
    print(f"  candidate mang khoá: {list(ck)}")
    print(f"  nC trung bình {out['a_ham_muc_tieu']['nC_tb']:.2f} vs nS {out['a_ham_muc_tieu']['nS_tb']:.2f}"
          f" | lô KHAN (nC>nS) {n_khan}/{len(lo_all)}")
    print(f"  tổng gán {out['a_ham_muc_tieu']['tong_n_gan']} | tổng stagger {n_stag}")
    print(f"  GREEDY tầm thường đạt ĐÚNG cost tối ưu: {bang}/{len(lo_all)}"
          f" ({bang / max(1, len(lo_all)):.1%})")
    print(f"  NAIVE (bỏ qua pen, theo alphabet) đạt đúng cost: {bang_R}/{len(lo_all)}")
    print(f"  SOC thấp nhất từng được gán: {out['a_ham_muc_tieu']['soc_gan_min']}%"
          f" | số lượt gán SOC<20%: {out['a_ham_muc_tieu']['n_gan_soc_duoi_20']}")

    # ---- (b)(c)(d) các nhóm
    def _bc(key, sub=None):
        xs = [(r[key][sub] if sub else r[key]) for r in rows]
        lo, hi = _boot(xs, rng)
        return {"mean": statistics.mean(xs), "ci95": [lo, hi],
                "sig": "SIG" if (lo > 0 or hi < 0) else "ns"}

    print("\n=== (b)(d) PHÂN RÃ Δpayout (B−A), n=30 seed, ghép cặp CÙNG ACTOR ===")
    out["b_nhom"] = {}
    for ten, nhan in (("di", "ĐI THEO (mover)"), ("gan_ko_di", "được gán, KHÔNG đi"),
                      ("ko_cham", "KHÔNG hề được gán"), ("it", "tercile rảnh ÍT"),
                      ("giua", "tercile giữa"), ("nhieu", "tercile rảnh NHIỀU")):
        xs = [r["nhom"][ten]["dpay"] for r in rows]
        ns = [r["nhom"][ten]["n"] for r in rows]
        ts_ = [r["nhom"][ten]["dtrip"] for r in rows]
        lo, hi = _boot(xs, rng)
        lo2, hi2 = _boot(ts_, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        out["b_nhom"][ten] = {"nhan": nhan, "n_tb": statistics.mean(ns),
                             "dpay": statistics.mean(xs), "ci95": [lo, hi], "sig": sig.strip(),
                             "dtrip": statistics.mean(ts_), "dtrip_ci95": [lo2, hi2],
                             "dtrip_sig": "SIG" if (lo2 > 0 or hi2 < 0) else "ns"}
        print(f"  {nhan:<24} n≈{statistics.mean(ns):>5.1f}  Δpayout {statistics.mean(xs):>+10,.0f}đ"
              f"  CI[{lo:>+9,.0f};{hi:>+9,.0f}] {sig}   Δcuốc {statistics.mean(ts_):>+6.3f}"
              f" [{lo2:>+6.3f};{hi2:>+6.3f}]")

    print("\n=== (b) CƠ CHẾ: người KHÔNG được gán, CÓ vs KHÔNG phơi nhiễm luồng đến ===")
    for k2, nhan in (("dpay_co", "Δpayout | ô có người ĐẾN"), ("dpay_khong", "Δpayout | ô KHÔNG"),
                     ("dtrip_co", "Δcuốc  | ô có người ĐẾN"), ("dtrip_khong", "Δcuốc  | ô KHÔNG")):
        r_ = _bc("phoi_nhiem", k2)
        out.setdefault("b_phoi_nhiem", {})[k2] = r_
        print(f"  {nhan:<28} {r_['mean']:>+11,.3f}  CI[{r_['ci95'][0]:>+11,.3f};"
              f"{r_['ci95'][1]:>+11,.3f}] {r_['sig']}")
    for k2 in ("n_co", "n_khong"):
        out["b_phoi_nhiem"][k2] = statistics.mean([r["phoi_nhiem"][k2] for r in rows])
    print(f"  cỡ nhóm TB: có phơi nhiễm {out['b_phoi_nhiem']['n_co']:.1f} người"
          f" · không {out['b_phoi_nhiem']['n_khong']:.1f} người")
    print("  ĐỐI CHỨNG MÙ (SHUF, cùng phép đo):")
    for k2 in ("dpay_co", "dpay_khong"):
        r_ = _bc("phoi_nhiem_SHUF", k2)
        out.setdefault("b_phoi_nhiem_SHUF", {})[k2] = r_
        print(f"    {k2:<26} {r_['mean']:>+11,.0f}đ CI[{r_['ci95'][0]:>+9,.0f};"
              f"{r_['ci95'][1]:>+9,.0f}] {r_['sig']}")

    print("\n=== (b) CẦU CÓ ĐƯỢC PHỤC VỤ THÊM KHÔNG (tổng hệ thống) ===")
    for k2, nhan in (("inflow_n", "lượt relocate-standby/ngày"),
                     ("inflow_cells", "số ô nhận người"),
                     ("d_served_o_nhan", "Δ đơn nhận ở ô NHẬN người"),
                     ("d_served_o_nguon", "Δ đơn nhận ở ô NGUỒN"),
                     ("d_dropoff", "Δ tổng chuyến hoàn thành (toàn hệ)"),
                     ("d_expired", "Δ đơn HẾT HẠN (toàn hệ)")):
        r_ = _bc(k2)
        out.setdefault("b_he_thong", {})[k2] = r_
        print(f"  {nhan:<34} {r_['mean']:>+10,.2f}  CI[{r_['ci95'][0]:>+9,.2f};"
              f"{r_['ci95'][1]:>+9,.2f}] {r_['sig']}")

    print("\n=== (c) CHI PHÍ CƠ HỘI của người bị đẩy đi ===")
    for k2, nhan in (("km_standby_tb", "km/lượt relocate-standby"),
                     ("km_standby_tong", "km rỗng standby/ngày (toàn đội)"),
                     ("empty_di", "Δ phút chạy rỗng của MOVER"),
                     ("km_di", "Δ km của MOVER")):
        r_ = _bc(k2)
        out.setdefault("c_chi_phi", {})[k2] = r_
        print(f"  {nhan:<34} {r_['mean']:>+10,.3f}  CI[{r_['ci95'][0]:>+9,.3f};"
              f"{r_['ci95'][1]:>+9,.3f}] {r_['sig']}")

    print("\n=== (d) CÔNG BẰNG ===")
    dg = [r["gini_B"] - r["gini_A"] for r in rows]
    lo, hi = _boot(dg, rng)
    out["d_cong_bang"] = {
        "gini_A": statistics.mean([r["gini_A"] for r in rows]),
        "gini_B": statistics.mean([r["gini_B"] for r in rows]),
        "d_gini": statistics.mean(dg), "d_gini_ci95": [lo, hi],
        "d_gini_sig": "SIG" if (lo > 0 or hi < 0) else "ns",
        "d_p10": _bc("p10_B")["mean"] - _bc("p10_A")["mean"],
        "d_payout_toan_doi": _bc("d_payout_toan_doi"),
        "d_payout_tuyet_doi": _bc("d_payout_tuyet_doi"),
        "d_trip_toan_doi": _bc("d_trip_toan_doi"),
    }
    dcb = out["d_cong_bang"]
    print(f"  Gini payout: A {dcb['gini_A']:.4f} → B {dcb['gini_B']:.4f}"
          f"  Δ {dcb['d_gini']:+.4f} CI[{lo:+.4f};{hi:+.4f}] {dcb['d_gini_sig']}")
    print(f"  p10 payout:  A {_bc('p10_A')['mean']:,.0f}đ → B {_bc('p10_B')['mean']:,.0f}đ"
          f"  Δ {dcb['d_p10']:+,.0f}đ")
    print(f"  Δ payout TRUNG BÌNH toàn đội {dcb['d_payout_toan_doi']['mean']:+,.0f}đ"
          f" | Δ payout TUYỆT ĐỐI trung bình {dcb['d_payout_tuyet_doi']['mean']:,.0f}đ"
          f" ⇒ tỷ lệ xáo/ròng ="
          f" {dcb['d_payout_tuyet_doi']['mean'] / max(1e-9, abs(dcb['d_payout_toan_doi']['mean'])):.1f}×")

    out["per_seed"] = rows
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
