"""PB1 — PHẢN BIỆN C9: có bác được "kênh positioning phân phối lại thu nhập" không?

Bốn đường tấn công (a)(b)(c)(d) của nhiệm vụ, đo lại từ đầu trên CÙNG cửa sổ seed 3300..3329.

Arm:
  A     advice OFF                                  (đúng như c9b)
  B     advice ON, coverage=all                     (đúng như c9b)
  N     advice OFF + **nhiễu niềm tin được rút lại** (NULL-NOISE, KHÔNG có advisor nào)

`N` là placebo mà `c9c` thiếu: `c9c` cho arm null **bit-identical 30/30 seed** ⇒ phương sai
bằng 0 ⇒ **không mang một bit thông tin nào** về hồi-quy-về-trung-bình. `N` giữ nguyên actor,
đơn hàng, lưới, chính sách — chỉ RÚT LẠI nhiễu niềm tin per-(actor,giờ,ô) ở
`world._actor_demand_hint` (đổi khoá RNG). Tài xế vẫn đi chỗ khác, nhưng **không có lời khuyên
nào tồn tại** ⇒ mọi mẫu hình tercile thấy ở `N` là HIỆN VẬT ĐO, không thể là "phân phối lại".

Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb1-do-lai.py
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from gsm_sim import runner as RUNNER  # noqa: E402
from gsm_sim.config import Config  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402
from gsm_sim.world import World  # noqa: E402

OUT = pathlib.Path(__file__).with_name("pb1-do-lai.json")
SEEDS = list(range(3300, 3330))
NB = 2000
NHOM = ("t0 (thấp nhất)", "t1 (giữa)", "t2 (cao nhất)")


class NoisyWorld(World):
    """Rút LẠI nhiễu niềm tin (đổi khoá RNG) — mọi thứ khác y hệt World thật.

    Sao chép thân `_actor_demand_hint` (world.py, hàm `_actor_demand_hint`, neo bằng
    `self._belief_cache` + `grid_disk(actor.cell, 2)`); chỉ khác khoá RNG `+ 7919`.
    """

    def _actor_demand_hint(self, actor, hour):  # type: ignore[override]
        key = (actor.actor_id, hour, actor.cell)
        cached = self._belief_cache.get(key)
        if cached is not None:
            return cached
        field = self.demand_field.get(hour, {})
        if not field:
            self._belief_cache[key] = {}
            return {}
        sigma = actor.demand_prior_sigma
        hint: dict[str, float] = {}
        from gsm_sim.geo import grid_disk
        for c in sorted(grid_disk(actor.cell, 2)):
            base = field.get(c, 0.0)
            rng_c = np.random.default_rng((self.seed + 7919, actor.actor_id, hour, int(c, 16)))
            hint[c] = base * math.exp(rng_c.normal(0.0, sigma))
        self._belief_cache[key] = hint
        return hint


def _snap(r) -> dict[int, dict]:
    out = {}
    for a in r.actors:
        out[a.actor_id] = {
            "payout": float(a.payout_vnd), "gross": float(a.gross_vnd),
            "idle": float(a.idle_min), "online": float(a.online_min),
            "empty": float(a.empty_min), "rest": float(a.rest_min),
            "charge": float(a.charge_min), "trips": float(a.trips_done),
            "offered": float(a.orders_offered),
            "archetype": a.archetype, "fleet": str(getattr(a.fleet, "value", a.fleet)),
            "home": a.home_cell,
            "shift_len": float(a.shift_end_min - a.shift_start_min),
            "shift_start": float(a.shift_start_min),
        }
    return out


def _boot(xs, rng):
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def _terc(ids, key):
    xep = sorted(ids, key=key)
    t = len(xep) // 3
    return [xep[:t], xep[t:2 * t], xep[2 * t:]]


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    per_seed = []
    for k, seed in enumerate(SEEDS, 1):
        A = _snap(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        B = _snap(run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                     coverage="all"), seed))
        RUNNER.World = NoisyWorld
        try:
            N = _snap(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        finally:
            RUNNER.World = World
        per_seed.append({"seed": seed, "A": A, "B": B, "N": N})
        print(f"  ... {k}/{len(SEEDS)} seed", flush=True)

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "bang": {}}

    # ---------- kiểm N có THỰC SỰ phân kỳ không (nếu = 0 thì placebo vô nghĩa như c9c) -------
    dose = {}
    for arm in ("B", "N"):
        v = [st.mean([abs(r[arm][i]["payout"] - r["A"][i]["payout"]) for i in r["A"]])
             for r in per_seed]
        dose[arm] = st.mean(v)
    out["lieu_MAD_payout"] = dose
    print(f"\n[LIỀU] |Δpayout| trung bình mỗi tài xế:  B={dose['B']:,.0f}đ   N={dose['N']:,.0f}đ")

    # ---------- (a)(b)(c) tercile theo NHIỀU tiêu chí tiền-can-thiệp ------------------------
    TIEU_CHI = {
        "idle_A (như c9b)": lambda A, i: A[i]["idle"],
        "payout_A": lambda A, i: A[i]["payout"],
        "trips_A": lambda A, i: A[i]["trips"],
        "online_A": lambda A, i: A[i]["online"],
        "offered_A": lambda A, i: A[i]["offered"],
        "shift_len (CỐ ĐỊNH)": lambda A, i: A[i]["shift_len"],
        "shift_start (CỐ ĐỊNH)": lambda A, i: A[i]["shift_start"],
        "actor_id (giả)": lambda A, i: i,
    }
    for ten, f in TIEU_CHI.items():
        rows_b, rows_n, rows_key = [], [], []
        for r in per_seed:
            A = r["A"]
            ids = sorted(A)
            gs = _terc(ids, lambda i: f(A, i))
            rows_b.append([st.mean([r["B"][i]["payout"] - A[i]["payout"] for i in g]) for g in gs])
            rows_n.append([st.mean([r["N"][i]["payout"] - A[i]["payout"] for i in g]) for g in gs])
            rows_key.append([st.mean([f(A, i) for i in g]) for g in gs])
        blk = []
        for j in range(3):
            b = [x[j] for x in rows_b]
            n = [x[j] for x in rows_n]
            lo, hi = _boot(b, rng)
            nlo, nhi = _boot(n, rng)
            blk.append({
                "nhom": NHOM[j], "gia_tri_key": st.mean([x[j] for x in rows_key]),
                "B_mean": st.mean(b), "B_median": st.median(b), "B_ci95": [lo, hi],
                "B_sig": "SIG" if (lo > 0 or hi < 0) else "ns",
                "B_iqr": [st.quantiles(b, n=4)[0], st.quantiles(b, n=4)[2]],
                "B_seed_am": sum(1 for x in b if x < 0), "B_seed_duong": sum(1 for x in b if x > 0),
                "N_mean": st.mean(n), "N_median": st.median(n), "N_ci95": [nlo, nhi],
                "N_sig": "SIG" if (nlo > 0 or nhi < 0) else "ns",
                "N_seed_am": sum(1 for x in n if x < 0),
            })
        out["bang"][ten] = blk
        print(f"\n=== TERCILE theo `{ten}` (đo ở arm A) · n=30 seed ===")
        print(f"{'nhóm':<16}{'key TB':>10}{'B mean':>11}{'B median':>11}"
              f"{'B CI95':>26}{'seed<0':>8} | {'N mean':>11}{'N CI95':>26}{'sig':>5}")
        for d in blk:
            print(f"{d['nhom']:<16}{d['gia_tri_key']:>10,.0f}{d['B_mean']:>10,.0f}đ"
                  f"{d['B_median']:>10,.0f}đ  [{d['B_ci95'][0]:>9,.0f};{d['B_ci95'][1]:>9,.0f}]"
                  f"{d['B_seed_am']:>6}/30 | {d['N_mean']:>10,.0f}đ"
                  f"  [{d['N_ci95'][0]:>9,.0f};{d['N_ci95'][1]:>9,.0f}] {d['N_sig']:>4}")

    # ---------- (d) idle_min là gì: tương quan với các đại lượng khác ----------------------
    def _corr(xs, ys):
        mx, my = st.mean(xs), st.mean(ys)
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else 0.0

    cor = {}
    for what in ("payout", "online", "trips", "empty", "rest", "shift_len", "offered"):
        cs = []
        for r in per_seed:
            A = r["A"]
            ids = sorted(A)
            cs.append(_corr([A[i]["idle"] for i in ids], [A[i][what] for i in ids]))
        cor[what] = st.mean(cs)
    out["tuong_quan_idleA"] = cor
    print("\n=== (d) `idle_min` ở arm A tương quan với gì (TB 30 seed, Pearson trong seed) ===")
    for k2, v in cor.items():
        print(f"   corr(idle_A, {k2:<10}) = {v:+.3f}")

    # ---------- cơ chế: tercile idle_A có được advisor làm giảm idle / tăng trips không? ----
    mech = []
    for j in range(3):
        row = {"nhom": NHOM[j]}
        for what in ("idle", "trips", "online", "empty", "offered", "gross"):
            v = []
            for r in per_seed:
                A = r["A"]
                gs = _terc(sorted(A), lambda i: A[i]["idle"])
                v.append(st.mean([r["B"][i][what] - A[i][what] for i in gs[j]]))
            lo, hi = _boot(v, rng)
            row[what] = {"mean": st.mean(v), "ci95": [lo, hi],
                         "sig": "SIG" if (lo > 0 or hi < 0) else "ns"}
        mech.append(row)
    out["co_che_theo_tercile_idleA"] = mech
    print("\n=== CƠ CHẾ: Δ(B−A) của các đại lượng khác, theo tercile `idle_A` ===")
    print(f"{'nhóm':<16}{'Δidle′':>12}{'Δtrips':>12}{'Δonline′':>12}"
          f"{'Δempty′':>12}{'Δoffered':>12}{'Δgross':>13}")
    for row in mech:
        print(f"{row['nhom']:<16}"
              + "".join(f"{row[w]['mean']:>11,.1f}{'*' if row[w]['sig'] == 'SIG' else ' '}"
                        for w in ("idle", "trips", "online", "empty", "offered"))
              + f"{row['gross']['mean']:>12,.0f}{'*' if row['gross']['sig'] == 'SIG' else ' '}")

    # ---------- tổng kiểm: tổng Δ toàn đội, và Δ chuẩn hoá theo giờ online -----------------
    allb = [st.mean([r["B"][i]["payout"] - r["A"][i]["payout"] for i in r["A"]]) for r in per_seed]
    alln = [st.mean([r["N"][i]["payout"] - r["A"][i]["payout"] for i in r["A"]]) for r in per_seed]
    lo, hi = _boot(allb, rng)
    nlo, nhi = _boot(alln, rng)
    out["toan_doi"] = {"B_mean": st.mean(allb), "B_ci95": [lo, hi],
                       "B_median": st.median(allb),
                       "B_seed_am": sum(1 for x in allb if x < 0),
                       "N_mean": st.mean(alln), "N_ci95": [nlo, nhi],
                       "N_seed_am": sum(1 for x in alln if x < 0)}
    print(f"\nTOÀN ĐỘI  B={st.mean(allb):,.0f}đ [{lo:,.0f};{hi:,.0f}] "
          f"median={st.median(allb):,.0f} seed<0={sum(1 for x in allb if x < 0)}/30"
          f"  |  N={st.mean(alln):,.0f}đ [{nlo:,.0f};{nhi:,.0f}]")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
