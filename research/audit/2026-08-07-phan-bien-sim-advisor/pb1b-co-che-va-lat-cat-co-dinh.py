"""PB1b — đóng nốt (c) và kiểm CƠ CHẾ ở arm NULL-NOISE.

Câu hỏi còn treo sau `pb1-do-lai.py`:
 1. Ở arm B, tercile `idle_A` cao nhất có `Δidle = −36,8′` (SIG). Đó là *"advisor cắt chờ"*
    hay chỉ là **hồi quy về trung bình của chính biến dùng để chia nhóm**? ⇒ đo `Δidle` ở arm
    `N` (advice OFF, chỉ rút lại nhiễu niềm tin). Nếu `N` cũng ≈ −37′ ⇒ hiện vật.
 2. Lát cắt theo biến **PHÂN LOẠI CỐ ĐỊNH** (archetype, fleet, home_cell) — không có nhiễu đo,
    không hồi quy về trung bình được. Mẫu hình còn không?

Ghi luôn `pb1b-raw.json.gz` (snapshot per-actor 3 arm × 30 seed) để lần sau khỏi chạy lại.

Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb1b-co-che-va-lat-cat-co-dinh.py
"""
from __future__ import annotations

import gzip
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

HERE = pathlib.Path(__file__).parent
OUT = HERE / "pb1b-co-che-va-lat-cat-co-dinh.json"
RAW = HERE / "pb1b-raw.json.gz"
SEEDS = list(range(3300, 3330))
NB = 2000
NHOM = ("t0 (thấp nhất)", "t1 (giữa)", "t2 (cao nhất)")
FIELDS = ("payout", "gross", "idle", "online", "empty", "rest", "trips", "offered")


class NoisyWorld(World):
    """Bản sao `_actor_demand_hint` của world (neo: `self._belief_cache`,
    `grid_disk(actor.cell, 2)`), chỉ đổi khoá RNG `+7919` ⇒ rút LẠI nhiễu niềm tin."""

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
            rng_c = np.random.default_rng((self.seed + 7919, actor.actor_id, hour, int(c, 16)))
            hint[c] = field.get(c, 0.0) * math.exp(rng_c.normal(0.0, sigma))
        self._belief_cache[key] = hint
        return hint


def _snap(r) -> dict[str, dict]:
    out = {}
    for a in r.actors:
        out[str(a.actor_id)] = {
            "payout": float(a.payout_vnd), "gross": float(a.gross_vnd),
            "idle": float(a.idle_min), "online": float(a.online_min),
            "empty": float(a.empty_min), "rest": float(a.rest_min),
            "trips": float(a.trips_done), "offered": float(a.orders_offered),
            "archetype": a.archetype, "fleet": str(getattr(a.fleet, "value", a.fleet)),
            "home": a.home_cell, "shift_len": float(a.shift_end_min - a.shift_start_min),
        }
    return out


def _boot(xs, rng):
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    data = []
    for k, seed in enumerate(SEEDS, 1):
        A = _snap(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        Bx = _snap(run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                      coverage="all"), seed))
        RUNNER.World = NoisyWorld
        try:
            N = _snap(run_once(_cfg_with(cfg, enabled=False, actor_id=None,
                                         channels=None), seed))
        finally:
            RUNNER.World = World
        data.append({"seed": seed, "A": A, "B": Bx, "N": N})
        print(f"  ... {k}/{len(SEEDS)} seed", flush=True)
    with gzip.open(RAW, "wt", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS}

    # ---- 1. CƠ CHẾ: cùng bảng cho arm B và arm N (tercile theo idle_A) -------------------
    def terc(A):
        xep = sorted(A, key=lambda i: A[i]["idle"])
        t = len(xep) // 3
        return [xep[:t], xep[t:2 * t], xep[2 * t:]]

    coche: dict = {}
    for arm in ("B", "N"):
        rows = []
        for j in range(3):
            row = {"nhom": NHOM[j]}
            for w in FIELDS:
                v = [st.mean([r[arm][i][w] - r["A"][i][w] for i in terc(r["A"])[j]])
                     for r in data]
                lo, hi = _boot(v, rng)
                row[w] = {"mean": st.mean(v), "ci95": [lo, hi],
                          "sig": "SIG" if (lo > 0 or hi < 0) else "ns"}
            rows.append(row)
        coche[arm] = rows
    out["co_che"] = coche
    for arm in ("B", "N"):
        nhan = "B = advisor THẬT" if arm == "B" else "N = KHÔNG advisor, chỉ rút lại nhiễu"
        print(f"\n=== CƠ CHẾ theo tercile `idle_A` — arm {arm} ({nhan}) ===")
        print(f"{'nhóm':<16}{'Δidle′':>11}{'Δtrips':>11}{'Δempty′':>11}"
              f"{'Δoffered':>11}{'Δonline′':>11}{'Δpayout':>13}")
        for row in coche[arm]:
            print(f"{row['nhom']:<16}"
                  + "".join(f"{row[w]['mean']:>10,.1f}{'*' if row[w]['sig'] == 'SIG' else ' '}"
                            for w in ("idle", "trips", "empty", "offered", "online"))
                  + f"{row['payout']['mean']:>12,.0f}"
                  + ("*" if row["payout"]["sig"] == "SIG" else " "))

    # ---- 2. LÁT CẮT PHÂN LOẠI CỐ ĐỊNH ---------------------------------------------------
    catout: dict = {}
    for keyname in ("archetype", "fleet"):
        vals = sorted({r["A"][i][keyname] for r in data for i in r["A"]})
        blk = []
        for v in vals:
            rb, rn, ns = [], [], []
            for r in data:
                g = [i for i in r["A"] if r["A"][i][keyname] == v]
                if not g:
                    continue
                ns.append(len(g))
                rb.append(st.mean([r["B"][i]["payout"] - r["A"][i]["payout"] for i in g]))
                rn.append(st.mean([r["N"][i]["payout"] - r["A"][i]["payout"] for i in g]))
            lo, hi = _boot(rb, rng)
            nlo, nhi = _boot(rn, rng)
            blk.append({"gia_tri": v, "n_tb": st.mean(ns),
                        "B_mean": st.mean(rb), "B_ci95": [lo, hi],
                        "B_sig": "SIG" if (lo > 0 or hi < 0) else "ns",
                        "N_mean": st.mean(rn), "N_ci95": [nlo, nhi],
                        "N_sig": "SIG" if (nlo > 0 or nhi < 0) else "ns"})
        catout[keyname] = blk
        print(f"\n=== LÁT CẮT `{keyname}` (thuộc tính CỐ ĐỊNH của tài xế) ===")
        print(f"{'giá trị':<10}{'n/seed':>8}{'B mean':>12}{'B CI95':>26}{'sig':>5}"
              f"{'N mean':>12}{'N CI95':>26}{'sig':>5}")
        for d in blk:
            print(f"{str(d['gia_tri']):<10}{d['n_tb']:>8.1f}{d['B_mean']:>11,.0f}đ"
                  f"  [{d['B_ci95'][0]:>9,.0f};{d['B_ci95'][1]:>9,.0f}]{d['B_sig']:>5}"
                  f"{d['N_mean']:>11,.0f}đ  [{d['N_ci95'][0]:>9,.0f};{d['N_ci95'][1]:>9,.0f}]"
                  f"{d['N_sig']:>5}")

    # home_cell: quá nhiều mức ⇒ chia tercile theo payout TRUNG BÌNH của ô ở arm A
    ocell: dict[str, list[float]] = {}
    for r in data:
        for i in r["A"]:
            ocell.setdefault(r["A"][i]["home"], []).append(r["A"][i]["payout"])
    rank = {c: st.mean(v) for c, v in ocell.items()}
    cs = sorted(rank, key=lambda c: rank[c])
    t = len(cs) // 3
    nhomo = {c: (0 if x < t else 1 if x < 2 * t else 2) for x, c in enumerate(cs)}
    blk = []
    for j in range(3):
        rb, rn = [], []
        for r in data:
            g = [i for i in r["A"] if nhomo.get(r["A"][i]["home"]) == j]
            if not g:
                continue
            rb.append(st.mean([r["B"][i]["payout"] - r["A"][i]["payout"] for i in g]))
            rn.append(st.mean([r["N"][i]["payout"] - r["A"][i]["payout"] for i in g]))
        lo, hi = _boot(rb, rng)
        nlo, nhi = _boot(rn, rng)
        blk.append({"nhom": f"home_cell {NHOM[j]}", "B_mean": st.mean(rb), "B_ci95": [lo, hi],
                    "B_sig": "SIG" if (lo > 0 or hi < 0) else "ns",
                    "N_mean": st.mean(rn), "N_ci95": [nlo, nhi],
                    "N_sig": "SIG" if (nlo > 0 or nhi < 0) else "ns"})
    catout["home_cell_tercile"] = blk
    print(f"\n=== LÁT CẮT `home_cell` (chia tercile theo payout TB của ô ở arm A, "
          f"{len(cs)} ô) ===")
    for d in blk:
        print(f"{d['nhom']:<26}{d['B_mean']:>11,.0f}đ  [{d['B_ci95'][0]:>9,.0f};"
              f"{d['B_ci95'][1]:>9,.0f}]{d['B_sig']:>5}"
              f"{d['N_mean']:>11,.0f}đ  [{d['N_ci95'][0]:>9,.0f};{d['N_ci95'][1]:>9,.0f}]"
              f"{d['N_sig']:>5}")
    out["lat_cat_co_dinh"] = catout

    # ---- 3. PHÂN TÁN GIỮA TÀI XẾ: can thiệp có làm CHÊNH LỆCH rộng ra không? -------------
    disp = {}
    for arm in ("A", "B", "N"):
        sd = [st.pstdev([r[arm][i]["payout"] for i in r["A"]]) for r in data]
        gini = []
        for r in data:
            xs = sorted(r[arm][i]["payout"] for i in r["A"])
            n = len(xs)
            s = sum(xs)
            gini.append((2 * sum((k + 1) * x for k, x in enumerate(xs)) / (n * s) - (n + 1) / n)
                        if s else 0.0)
        disp[arm] = {"sd_mean": st.mean(sd), "gini_mean": st.mean(gini)}
    for arm in ("B", "N"):
        d = [x - y for x, y in zip([st.pstdev([r[arm][i]["payout"] for i in r["A"]]) for r in data],
                                   [st.pstdev([r["A"][i]["payout"] for i in r["A"]])
                                    for r in data])]
        lo, hi = _boot(d, rng)
        disp[arm]["d_sd_vs_A"] = {"mean": st.mean(d), "ci95": [lo, hi],
                                  "sig": "SIG" if (lo > 0 or hi < 0) else "ns"}
    out["phan_tan"] = disp
    print("\n=== PHÂN TÁN payout GIỮA TÀI XẾ (nếu 'phân phối lại' là thật thì phải đổi) ===")
    for arm in ("A", "B", "N"):
        extra = disp[arm].get("d_sd_vs_A")
        tail = (f"   Δsd vs A = {extra['mean']:+,.0f} "
                f"[{extra['ci95'][0]:,.0f};{extra['ci95'][1]:,.0f}] {extra['sig']}"
                if extra else "")
        print(f"  arm {arm}: sd={disp[arm]['sd_mean']:,.0f}đ  gini={disp[arm]['gini_mean']:.4f}"
              + tail)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}\nraw → {RAW}")


if __name__ == "__main__":
    main()
