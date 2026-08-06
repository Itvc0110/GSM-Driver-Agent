"""E4/E-03 â€” Ä‘o QUAN SÃT kÃªnh Ä‘á»•i-pin-sá»›m (swap_early), 30 seed, coverage=all, cÃ´ láº­p 1 cÆ¡ cháº¿.

    uv run python scripts/run_e01_station.py --seeds 30 --json <path>

Äá»c kÃ¨m: swap_wait_mean (chá» tráº¡m), charge_min percentiles theo fleet, battery_stranded,
sá»‘ láº§n kÃªnh nÃ³i (advice_swap_early). n=30 â€” chá»‰ Ä‘á»c hÆ°á»›ng, KHÃ”NG claim. Má»i sá»‘ MOCK.
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
      "rest_window": False, "station_choice": True, "positioning_overrides": "off"}


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

    print(f"\n=== E-01 station_choice Â· {len(pairs)} seed Â· coverage=all ===")
    for k in ("payout_mean_all", "trips_mean_all", "swap_wait_mean",
              "charge_min_p90_F_swap", "served_rate", "gini_payout",
              "rest_min_total", "work_span_p90"):
        r = cmp_["system"].get(k)
        if r:
            tag = "  (má»™t chiá»u â€” quan sÃ¡t)" if "one_way_gate" in r else ""
            print(f"  {k:>22}  Î”={r['delta_mean']:>12,.3f}  CI={r['ci95']}{tag}")
    if args.json:
        art = {"what": "E-01 station_choice A/B â€” quan sÃ¡t", "mock": True, "n": len(pairs),
               "channels": CH, "compare": cmp_,
               "canh_bao_doc": ["n=30 â€” CHá»ˆ Ä‘á»c hÆ°á»›ng, khÃ´ng claim",
                                "kÃªnh THá»œI GIAN: giÃ¡ trá»‹ ká»³ vá»ng á»Ÿ swap_wait/stranded, "
                                "khÃ´ng nháº¥t thiáº¿t á»Ÿ payout"]}
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  artifact â†’ {p}")
    print(f"  tá»•ng {(time.time()-t0)/60:.1f}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
