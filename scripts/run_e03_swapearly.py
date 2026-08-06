"""E4/E-03 — đo QUAN SÁT kênh đổi-pin-sớm (swap_early), 30 seed, coverage=all, cô lập 1 cơ chế.

    uv run python scripts/run_e03_swapearly.py --seeds 30 --json <path>

Đọc kèm: swap_wait_mean (chờ trạm), charge_min percentiles theo fleet, battery_stranded,
số lần kênh nói (advice_swap_early). n=30 — chỉ đọc hướng, KHÔNG claim. Mọi số MOCK.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config               # noqa: E402
from gsm_sim.parallel import compare, run_pair  # noqa: E402

CH = {"shift_plan": False, "accept_lift": False, "shift_extend": False,
      "rest_window": False, "swap_early": True, "positioning_overrides": "off"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    cfg = Config.load(str(ROOT / "configs/pilot_dongda.yaml"))
    t0 = time.time()
    pairs, spoke = [], 0
    for i, s in enumerate(range(args.seed0, args.seed0 + args.seeds), 1):
        p = run_pair(cfg, s, channels=CH, coverage="all")
        pairs.append(p)
        print(f"   seed {s} ({i}/{args.seeds})  {(time.time()-t0)/60:.1f}'", flush=True)
    cmp_ = compare(pairs)

    print(f"\n=== E-03 swap_early · {len(pairs)} seed · coverage=all ===")
    for k in ("payout_mean_all", "trips_mean_all", "swap_wait_mean",
              "charge_min_p90_F_swap", "served_rate", "gini_payout",
              "rest_min_total", "work_span_p90"):
        r = cmp_["system"].get(k)
        if r:
            tag = "  (một chiều — quan sát)" if "one_way_gate" in r else ""
            print(f"  {k:>22}  Δ={r['delta_mean']:>12,.3f}  CI={r['ci95']}{tag}")
    if args.json:
        art = {"what": "E-03 swap_early A/B — quan sát", "mock": True, "n": len(pairs),
               "channels": CH, "compare": cmp_,
               "canh_bao_doc": ["n=30 — CHỈ đọc hướng, không claim",
                                "kênh THỜI GIAN: giá trị kỳ vọng ở swap_wait/stranded, "
                                "không nhất thiết ở payout"]}
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  artifact → {p}")
    print(f"  tổng {(time.time()-t0)/60:.1f}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
