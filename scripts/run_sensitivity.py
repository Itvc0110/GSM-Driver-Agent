"""SIM-XANH Phase 3 — D-SIM-06: quét ĐỘ NHẠY kết luận advisor (kênh accept_lift).

    uv run python scripts/run_sensitivity.py --seeds 30 --out research/experiments/sensitivity

Vì sao (F-SIM4-A/C + D-SIM-04): mọi kết luận A/B hiện đo trên MỘT tài xế P4 của MỘT config,
với `adherence` và `lift_max` là ASSUMPTION. UPDATE-047 từng thấy `lift_max` 0.15 vs 0.19
**đổi cả DẤU** kết luận trên 1 seed. Câu hỏi của sweep: kết luận "+Δ có ý nghĩa" SỐNG hay CHẾT
khi các giả định đó dao động?

Grid CÓ CHỦ ĐÍCH (không nổ tổ hợp):
  - archetype ĐÍCH: P4 (tân binh — baseline Cường), P1 (part-time, accept 0.85 sát ngưỡng).
    P2 (0.95, TRÊN ngưỡng thưởng) chỉ kiểm 5 seed để xác nhận advisor IM LẶNG — không đốt
    30 seed cho ô biết-trước-bằng-0.
  - adherence: 0.3 (lão làng ít nghe) · 0.75 (mặc định P4) · 1.0 (trần lý thuyết).
  - lift_max: 0.10 · 0.15 (mặc định) · 0.19 (mức từng lật dấu trên 1 seed).
30 seed/ô, hiệu theo cặp + CI bootstrap (máy đo SIM-4). ~25-30 phút.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                          # noqa: E402
from gsm_sim.parallel import (                             # noqa: E402
    PairResult, _cfg_with, _driver_metrics, _system_metrics, compare, pick_target,
)
from gsm_sim.runner import run_once                        # noqa: E402

CHANNELS = {"shift_plan": False, "accept_lift": True, "shift_extend": False,
            "rest_window": False}   # CÔ LẬP kênh accept_lift — sweep đo đúng một thứ


def sweep(cfg: Config, seeds: list[int], archetype: str,
          adherences: list[float], lifts: list[float]) -> dict:
    """Sweep 1 archetype. World A chạy MỘT lần mỗi seed (không phụ thuộc ô)."""
    cfg_a = _cfg_with(cfg, enabled=False, actor_id=None, channels=None)
    cache_a = {}
    aid = None
    out = {}
    for s in seeds:
        cache_a[s] = run_once(cfg_a, s)
    aid = pick_target(cache_a[seeds[0]], archetype)

    for adh in adherences:
        for lift in lifts:
            pairs = []
            for s in seeds:
                cb = _cfg_with(cfg, enabled=True, actor_id=aid, channels=CHANNELS)
                cb.data["advice"]["adherence_by_archetype"] = {archetype: adh}
                cb.data["advice"]["accept_lift_max"] = lift
                cb.data["advice"]["accept_lift_step"] = min(0.10, lift)
                # max_realized_accept PHẢI nhất quán với trần lift (D-SIM-07): ước bảo thủ
                cb.data["advice"]["max_realized_accept"] = min(0.98, 0.80 + lift + 0.03)
                rb = run_once(cb, s)
                ra = cache_a[s]
                pairs.append(PairResult(
                    seed=s, actor_id=aid,
                    a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                    system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid)))
            cell = compare(pairs)
            d = cell["driver"]["payout_vnd"]
            out[f"adh={adh}|lift={lift}"] = {
                "delta_mean": d["delta_mean"], "ci95": d["ci95"],
                "significant": d["significant"], "n_positive": d["n_positive"],
                "delta_bonus": cell["driver"]["day_bonus_vnd"]["delta_mean"],
                "served_guard": cell["system"]["served_rate"]["delta_mean"],
            }
            print(f"[{archetype}] adh={adh} lift={lift}: Δ={d['delta_mean']:+,.0f} "
                  f"CI[{d['ci95'][0]:+,.0f},{d['ci95'][1]:+,.0f}] "
                  f"{'SIG' if d['significant'] else 'ci-chứa-0'} n_pos={d['n_positive']}")
    return {"target_actor": aid, "cells": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=2000)
    ap.add_argument("--out", default=str(ROOT / "research" / "experiments" / "sensitivity"))
    args = ap.parse_args()
    cfg = Config.load(ROOT / "configs" / "pilot_dongda.yaml")
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    res = {}
    for arch in ("P4", "P1"):
        print(f"\n=== {arch} ({args.seeds} seed/ô) ===")
        res[arch] = sweep(cfg, seeds, arch,
                          adherences=[0.3, 0.75, 1.0], lifts=[0.10, 0.15, 0.19])
    # P2: xác nhận im lặng với 5 seed (accept 0.95 > ngưỡng 0.85 — advisor không có gì để nói)
    print("\n=== P2 (5 seed — xác nhận IM LẶNG, không đốt 30) ===")
    res["P2_silence_check"] = sweep(cfg, seeds[:5], "P2",
                                    adherences=[1.0], lifts=[0.19])

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "dsim06_sweep.json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                              encoding="utf-8")
    print(f"\nghi {outdir / 'dsim06_sweep.json'}")
    print("MOCK — không phải số thật của GSM. Đọc kèm: mean ≠ 'ngày nào cũng lợi' (xem n_pos).")


if __name__ == "__main__":
    main()
