"""R2 statistical verify (P3 §3) — phân phối mock l1r vs benchmark, ≥30 seeds.

Gen N seed (1 ngày/seed) → driver-day → percentile so `realism-benchmarks.md`.
KHÔNG hard-fail gap sim đã biết (T-021: FT ~16 cuốc/~300k/~4.5h là biên dưới) — LABEL.

**BUG-PI2b-01 fix:** TÁCH THEO service_type. `realism-benchmarks.md` là benchmark BIKE
Hà Nội; gộp chung car/premium (fare cao gấp 3-5×) làm median payout bị thổi → verdict
SAI (nhìn "PASS" nhờ car, che việc bike vẫn biên dưới). Car = OBSERVE-ONLY (chưa có
benchmark VN cho car trong research).

Chạy:  uv run python scripts/verify_realdata_stats.py --seeds 30
"""

from __future__ import annotations

import argparse
import statistics as st
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from gsm_core.mockgen.realdata import generate_realdata

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "research" / "experiments" / "mockgen-realdata" / "ROUND-2-stats-report.md"

# (label, benchmark note, target range hoặc None nếu chỉ observe). Nguồn: realism-benchmarks.md
BENCH = {
    "trips_per_driver_day": ("cuốc/tài xế/ngày", "sim baseline ~16 (biên dưới); thực FT median 18-22", (10, 30)),
    "payout_per_driver_day": ("payout(commission)/ngày VND", "sim ~300k (thiếu lớp thưởng); thực 380-480k", (150000, 550000)),
    "online_hours": ("giờ online/ngày", "sim FT median ~4.5h (T-021 gap; thiết kế 8-10h)", (2, 12)),
    "acceptance_rate": ("tỷ lệ nhận", "eligibility thưởng ≥0.85; archetype 0.74-0.97", (0.6, 1.0)),
    "rush_order_share": ("% cuốc khung rush", "2 đỉnh 6-8h,16-18h", (0.1, 0.7)),
    "five_star_share": ("% cuốc 5 sao", "mock N(0.78)", (0.5, 1.0)),
}


def _pct(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[k]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed-base", type=int, default=200)
    args = ap.parse_args()

    # TÁCH population: bike (có benchmark) vs car (observe-only)
    samples: dict[str, dict[str, list[float]]] = {"bike": {k: [] for k in BENCH},
                                                   "car": {k: [] for k in BENCH}}
    d0 = date(2026, 7, 1)
    n_dd = {"bike": 0, "car": 0}
    for i in range(args.seeds):
        with TemporaryDirectory() as td:
            res = generate_realdata(days=1, seed_base=args.seed_base + i, out_dir=Path(td),
                                    start_date=(d0 + timedelta(days=i)).isoformat())
            t, uni = res["tables"], res["universe"]
        stat = {r["driver_id"]: r for r in t["driver_statistic_daily"]}
        inc = {r["driver_id"]: r for r in t["driver_income_daily"]}
        onl = {r["driver_id"]: r for r in t["driver_online_hours_sap_id"]}
        rush = {r["driver_id"]: r for r in t["driver_orders_rush_hours"]}
        for drv, s in stat.items():
            if s["completed_count"] <= 0:
                continue
            svc = uni.get(drv, {}).get("service_type", "bike")
            g = samples.setdefault(svc, {k: [] for k in BENCH})
            n_dd[svc] = n_dd.get(svc, 0) + 1
            g["trips_per_driver_day"].append(s["completed_count"])
            g["payout_per_driver_day"].append(inc[drv]["commission"])
            g["online_hours"].append(onl[drv]["online_time"])
            g["acceptance_rate"].append(s["acceptance_rate"])
            ro = rush[drv]
            g["rush_order_share"].append(
                ro["total_order_rush_hour"] / ro["total_order"] if ro["total_order"] else 0.0)
            g["five_star_share"].append(
                s["count_rating_5_star"] / s["total_order_rating"] if s["total_order_rating"] else 0.0)

    lines = ["# ROUND 2 — Statistical realism (mock l1r vs benchmark)\n",
             f"Seeds: {args.seeds} (base {args.seed_base}). driver-days: "
             f"bike={n_dd.get('bike', 0)}, car={n_dd.get('car', 0)}. "
             "Nguồn benchmark: `research/simulation/realism-benchmarks.md`.\n",
             "> **TÁCH POPULATION (fix BUG-PI2b-01):** benchmark là của **BIKE Hà Nội**. "
             "Gộp car/premium (fare cao 3-5×) sẽ thổi median payout → verdict sai. "
             "**Car = OBSERVE-ONLY** (chưa có benchmark VN cho car trong research).\n",
             "> Gap sim đã biết (T-021) được LABEL, không hard-fail — mock kế thừa sim calibration.\n"]
    n_gap = 0
    for svc in ("bike", "car"):
        if not n_dd.get(svc):
            continue
        judged = svc == "bike"
        lines += [f"\n## {svc.upper()} ({'vs benchmark' if judged else 'OBSERVE-ONLY'})\n",
                  "| metric | median | p10 | p90 | target | verdict | ghi chú |",
                  "|---|---|---|---|---|---|---|"]
        for key, (label, note, rng_t) in BENCH.items():
            xs = samples[svc][key]
            med, p10, p90 = _pct(xs, 0.5), _pct(xs, 0.1), _pct(xs, 0.9)
            fmt = (lambda v: f"{v:,.0f}") if "payout" in key else (lambda v: f"{v:.2f}")
            if not judged:
                verdict, tgt = "OBSERVE", "—"
            else:
                in_range = rng_t is None or (rng_t[0] <= med <= rng_t[1])
                verdict = "PASS" if in_range else "GAP-T021"
                tgt = f"{rng_t[0]}–{rng_t[1]}" if rng_t else "observe"
                if not in_range:
                    n_gap += 1
            lines.append(f"| {label} | {fmt(med)} | {fmt(p10)} | {fmt(p90)} | {tgt} | {verdict} | "
                         f"{note if judged else 'car — không dùng benchmark bike'} |")
    lines.append(f"\n**Tổng (BIKE, có benchmark):** {len(BENCH)-n_gap}/{len(BENCH)} PASS, "
                 f"{n_gap} GAP-T021 (labeled). GAP = sim baseline biên dưới (cuốc/payout/online) — "
                 "dư địa advisor + **thiếu lớp thưởng tuần** (sẽ cộng ở S5/rule), không phải bug mock. "
                 "Aggregate consistency pass R1/R3/R4 (`test_realdata_gen`).")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"R2 report: {REPORT} | driver-days={n_dd} | bike-gaps={n_gap}")


if __name__ == "__main__":
    main()
