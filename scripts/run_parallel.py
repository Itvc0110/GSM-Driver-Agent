"""SIM-4 — chạy thế giới song song và in bảng Δ + CI.

    uv run python scripts/run_parallel.py --seeds 30
    uv run python scripts/run_parallel.py --seeds 30 --archetype P2 --json out.json

Đọc kỹ trước khi diễn giải:
  - Δ là **hiệu theo cặp** (cùng seed, chung ngoại sinh) — không phải hiệu hai trung bình rời rạc.
  - `CÓ Ý NGHĨA` = CI 95% **không chứa 0**. CI chứa 0 là một KẾT QUẢ, không phải thất bại.
  - `n_pos` = số seed có Δ>0. Mean dương nhưng `n_pos` ~ nửa số seed nghĩa là **phân phối lệch**:
    thắng lớn ở vài ngày, thua nhỏ ở nhiều ngày. Đừng đọc mean như "ngày nào cũng lợi".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config          # noqa: E402
from gsm_sim.parallel import run_ladder    # noqa: E402

KEYS = ("payout_vnd", "day_bonus_vnd", "trip_payout_vnd", "trips_completed",
        "acceptance_rate", "utilization", "idle_min", "online_min")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "configs" / "pilot_dongda.yaml"))
    ap.add_argument("--seeds", type=int, default=30, help="số seed (≥30 cho kết luận)")
    ap.add_argument("--seed0", type=int, default=2000)
    ap.add_argument("--archetype", default="P4", help="archetype của tài xế đích")
    ap.add_argument("--json", default=None, help="ghi kết quả đầy đủ ra file")
    args = ap.parse_args()

    if args.seeds < 30:
        print(f"[!] {args.seeds} seed < 30 — đủ để thăm dò, KHÔNG đủ để kết luận.\n")

    cfg = Config.load(args.config)
    seeds = list(range(args.seed0, args.seed0 + args.seeds))
    res = run_ladder(cfg, seeds, archetype=args.archetype)

    for step, r in res.items():
        print(f"\n=== {step}  (n={r['n_seeds']} seed · tài xế {args.archetype}) ===")
        print(f"{'metric':20s}{'World A':>12s}{'World B':>12s}{'Δ':>12s}"
              f"{'CI95':>26s}{'n_pos':>7s}")
        for k in KEYS:
            d = r["driver"].get(k)
            if not d:
                continue
            ci = f"[{d['ci95'][0]:,.1f}, {d['ci95'][1]:,.1f}]"
            mark = " *" if d["significant"] else "  "
            print(f"{k:20s}{d['mean_a']:>12,.2f}{d['mean_b']:>12,.2f}"
                  f"{d['delta_mean']:>+12,.2f}{ci:>26s}{d['n_positive']:>5d}/{r['n_seeds']}{mark}")
        print("  -- guardrail hệ thống (tầng 1-4, cổng HAI CHIỀU) --")
        for k, d in r["system"].items():
            # E1a (r07-F1): lọc theo "có significant không" thay vì chỉ né one_way_gate —
            # hàng SCOPE_KEYS (n_actors_scope) chỉ mang `role`, bản cũ KeyError ở đây làm
            # CLI chết TRƯỚC khi in per-archetype (bảng P1..P7 chưa bao giờ in ra được).
            if "significant" not in d:
                continue          # tầng 5 (one_way_gate) + mẫu số (role) in riêng ở dưới
            mark = "  <-- ĐỘNG TỚI HỆ THỐNG" if d["significant"] else ""
            print(f"  {k:24s} Δ={d['delta_mean']:>+12,.4f} "
                  f"CI=[{d['ci95'][0]:,.4f}, {d['ci95'][1]:,.4f}]{mark}")
        health = {k: d for k, d in r["system"].items() if "one_way_gate" in d}
        if health:
            # Tầng 5 (D-M3-05) là cổng MỘT CHIỀU: chỉ tố giác SUY GIẢM sức khoẻ, cố ý KHÔNG
            # có chiều khen. In riêng, KHÔNG gắn nhãn "ĐỘNG TỚI HỆ THỐNG" — veto tăng nghĩa
            # là tài xế chạm mệt/cạn pin NHIỀU HƠN, đọc thành "tốt lên" là đúng hướng
            # Goodhart mà tầng 5 sinh ra để chặn.
            print("  -- tầng 5 SỨC KHOẺ (quan sát, cổng MỘT CHIỀU — không có dấu * ) --")
            for k, d in health.items():
                print(f"  {k:24s} Δ={d['delta_mean']:>+12,.4f} "
                      f"CI=[{d['ci95'][0]:,.4f}, {d['ci95'][1]:,.4f}]")
            print("     ↳ verdict một chiều đọc từ `sim_metrics.health_guardrail_flags`")

    print("\n(*) = CI 95% không chứa 0. MOCK — không phải số thật của GSM.")
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                   encoding="utf-8")
        print(f"đã ghi: {args.json}")


if __name__ == "__main__":
    main()
