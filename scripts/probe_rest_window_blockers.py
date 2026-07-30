"""Probe: vì sao kênh `rest_window` không nói được lời nào trong A/B đơn ngày?

Trả lời điểm 3 của Cường (2026-07-29): *"trong sim kiểm tra có thiết kế độ mệt của tài xế
chưa? ... kiểm tra xem liệu có thực sự đủ khả năng thiết kế môi trường phức tạp đến thế
không?"* — trước khi bàn có nên mô hình hoá HẬU QUẢ của mệt, phải biết kênh khuyên nghỉ
hiện tại chết ở đâu.

Instrument, không phải test: bọc `should_defer_rest` và `idle_reduction.solve` để đếm phân
phối lý do. Chạy:

    uv run python scripts/probe_rest_window_blockers.py [--seeds 4200 4201 4202]

⚠ HAI BẪY ĐÃ SẬP khi viết probe này — đừng lặp lại:

1. `_cfg_with(..., coverage=...)` mặc định `"single"`. Truyền `actor_id=None` cùng
   `coverage="single"` ⇒ `single_actor_id=None` ⇒ `covers()` trả False cho **mọi** tài xế
   ⇒ advisor tắt hoàn toàn, `idle_reduction.solve` chỉ được gọi 1 lần/3 seed, và toàn bộ
   `no_window` chỉ có nghĩa "không được phủ". Phải dùng `coverage="all"`.
2. `CHANNEL_LADDER["rest_window"]` **có** `shift_plan: True`. Tự dựng dict kênh chỉ bật
   `rest_window` là đo một cấu hình không tồn tại trong artifact nào.

Mọi số ra từ đây là MOCK (`configs/pilot_dongda.yaml`), không phải số thật GSM.
"""
from __future__ import annotations

import argparse
import collections

from gsm_core.solvers import idle_reduction
from gsm_sim import advice_bridge as AB
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, run_once
from gsm_sim.runner import Config

CONFIG = "configs/pilot_dongda.yaml"
DEFAULT_SEEDS = (4200, 4201, 4202)

# Lý do nào là LAN CAN SỨC KHOẺ (đúng theo thiết kế, KHÔNG được "sửa" để tăng Δ tiền) —
# xem `advice_bridge.should_defer_rest` và ranh giới "sức khoẻ không phải biến để tối ưu".
RAILS = ("soc_low", "fatigued", "defer_cap")


def _probe(base: Config, ladder: str, seeds) -> tuple[collections.Counter, collections.Counter, list[float]]:
    reasons: collections.Counter = collections.Counter()
    solver_out: collections.Counter = collections.Counter()
    idle_when_not_notable: list[float] = []

    orig_defer = AB.AdviceActionBridge.should_defer_rest
    orig_solve = idle_reduction.solve

    def spy_defer(self, actor, now_min, hour, hint, soc):
        out = orig_defer(self, actor, now_min, hour, hint, soc)
        # reason rỗng = cadence nén (chỉ xảy ra khi advice.cadence.enabled=true)
        reasons["NÓI" if out[0] else (out[1] or "cadence_nén")] += 1
        return out

    def spy_solve(ii):
        rep = orig_solve(ii)
        sol = rep.get("solution") or {}
        worst = sol.get("worst_window")
        if not sol.get("notable"):
            solver_out["notable=False (chờ chưa đủ nhiều)"] += 1
            idle_when_not_notable.append(float(ii.get("total_idle_min") or 0.0))
        elif not worst:
            solver_out["worst=None (không giờ nào demand thấp)"] += 1
        else:
            solver_out[f"worst_window → {int(worst['hour']):02d}h"] += 1
        return rep

    AB.AdviceActionBridge.should_defer_rest = spy_defer
    idle_reduction.solve = spy_solve
    try:
        cfg = _cfg_with(base, enabled=True, actor_id=None,
                        channels=CHANNEL_LADDER[ladder], coverage="all")
        for s in seeds:
            run_once(cfg, s)
    finally:
        AB.AdviceActionBridge.should_defer_rest = orig_defer
        idle_reduction.solve = orig_solve

    return reasons, solver_out, idle_when_not_notable


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    ap.add_argument("--ladders", nargs="+", default=["rest_window", "all"])
    args = ap.parse_args()

    base = Config.load(CONFIG)
    print(f"MOCK · {CONFIG} · seeds={args.seeds} · coverage=all")

    for ladder in args.ladders:
        reasons, solver_out, idle_ns = _probe(base, ladder, args.seeds)
        tot = sum(reasons.values()) or 1
        print(f"\n{'=' * 66}\nladder={ladder!r} · {tot} lần gọi should_defer_rest")
        for k, v in reasons.most_common():
            tag = "  ← LAN CAN SỨC KHOẺ" if k in RAILS else ""
            print(f"  {k:16s} {v:6d}  {100 * v / tot:5.1f}%{tag}")
        rails = sum(reasons[r] for r in RAILS)
        print(f"  → lan can sức khoẻ chặn {rails}/{tot} = {100 * rails / tot:.1f}% "
              f"(trần trên của kênh = {100 * (tot - rails) / tot:.1f}%)")
        print(f"  → THỰC SỰ NÓI: {reasons['NÓI']} ({100 * reasons['NÓI'] / tot:.2f}%)")

        stot = sum(solver_out.values()) or 1
        print(f"  idle_reduction.solve: {stot} lần")
        for k, v in solver_out.most_common(8):
            print(f"    {k:42s} {v:6d}  {100 * v / stot:5.1f}%")
        if idle_ns:
            idle_ns.sort()
            n = len(idle_ns)
            print(f"    total_idle_min khi notable=False: median={idle_ns[n // 2]:.1f} "
                  f"p90={idle_ns[min(n - 1, int(n * 0.9))]:.1f} max={idle_ns[-1]:.1f} "
                  f"(ngưỡng IDLE_TOTAL_ALERT_MIN={idle_reduction.IDLE_TOTAL_ALERT_MIN})")


if __name__ == "__main__":
    main()
