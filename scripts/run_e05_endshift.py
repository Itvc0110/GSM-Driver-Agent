"""E4/E-05 — đo QUAN SÁT kênh con kết-ca-sớm (shift_plan_end_only), 30 seed, coverage=all.

    uv run python scripts/run_e05_endshift.py --seeds 30 --json <path>

KHÔNG claim: n=30 chỉ đọc hướng; kênh GIẢM giờ làm nên đọc kèm tầng 5 (rest/work_span
kỳ vọng CẢI THIỆN — cổng một chiều không khen, chỉ ghi quan sát). Mọi số MOCK.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                  # noqa: E402
from gsm_sim.parallel import compare, run_pair     # noqa: E402

CH = {"shift_plan": True, "accept_lift": False, "shift_extend": False,
      "rest_window": False, "positioning_overrides": "off"}   # cô lập MỘT cơ chế


def cfg_e05(base: Config) -> Config:
    data = copy.deepcopy(base.data)
    data.setdefault("advice", {})["shift_plan_end_only"] = True
    return Config(data, base.root_dir)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    base = Config.load(str(ROOT / "configs/pilot_dongda.yaml"))
    cfg = cfg_e05(base)
    assert cfg.get("advice").get("shift_plan_end_only") is True

    t0 = time.time()
    pairs, n_end, n_spoke = [], 0, 0
    for i, s in enumerate(range(args.seed0, args.seed0 + args.seeds), 1):
        p = run_pair(cfg, s, channels=CH, coverage="all")
        pairs.append(p)
        print(f"   seed {s} ({i}/{args.seeds})  {(time.time()-t0)/60:.1f}'", flush=True)
    cmp_ = compare(pairs)

    print(f"\n=== E-05 end-shift-only · {len(pairs)} seed · coverage=all ===")
    for k in ("payout_mean_all", "trips_mean_all", "rest_min_total", "work_span_p90",
              "gini_payout", "served_rate"):
        r = cmp_["system"].get(k)
        if r:
            print(f"  {k:>18}  Δ={r['delta_mean']:>12,.2f}  CI={r['ci95']}"
                  + ("  (một chiều — quan sát)" if "one_way_gate" in r else ""))
    if args.json:
        art = {"what": "E-05 shift_plan_end_only A/B — quan sát", "mock": True,
               "n": len(pairs), "channels": CH, "compare": cmp_,
               "canh_bao_doc": ["n=30 — CHỈ đọc hướng, không claim",
                                "tầng 5 một chiều: cải thiện KHÔNG được khen, chỉ ghi nhận"]}
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  artifact → {p}")
    print(f"  tổng {(time.time()-t0)/60:.1f}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
