"""SIM-XANH Phase 3 — D-SIM-06: quét ĐỘ NHẠY kết luận advisor (kênh accept_lift).

    uv run python scripts/run_sensitivity.py --seeds 30 --out research/experiments/sensitivity

Vì sao (F-SIM4-A/C + D-SIM-04): mọi kết luận A/B hiện đo trên MỘT tài xế P4 của MỘT config,
với `adherence` và `lift_max` là ASSUMPTION. UPDATE-047 từng thấy `lift_max` 0.15 vs 0.19
**đổi cả DẤU** kết luận trên 1 seed. Câu hỏi của sweep: kết luận "+Δ có ý nghĩa" SỐNG hay CHẾT
khi các giả định đó dao động?

Grid CÓ CHỦ ĐÍCH (không nổ tổ hợp):
  - archetype ĐÍCH: P4 (tân binh — baseline Cường), P1 (part-time, accept 0.85 sát ngưỡng).
    P2 (0.95, TRÊN ngưỡng): ô kiểm 5-seed — AUDIT STATS-4: kỳ vọng "im lặng" ban đầu đã bị
    CHÍNH DATA bác bỏ (UPDATE-056 §3: thưởng chấm REALIZED nên ngày xui P2 vẫn được dip-alert
    cứu thưởng thật) → đổi tên ô thành `P2_dip_rescue_check`, đo và ghi n_advice thay vì
    tuyên bố im lặng.
  - adherence: 0.3 (lão làng ít nghe) · 0.75 (mặc định P4) · 1.0 (trần lý thuyết).
  - lift_max: 0.10 · 0.15 (mặc định) · 0.19 (mức từng lật dấu trên 1 seed).
30 seed/ô, hiệu theo cặp + CI bootstrap (máy đo SIM-4). ~25-30 phút.

AUDIT STATS-3/BEHAV-4 (UPDATE-069): `max_realized_accept` nay suy từ ANCHOR ĐO của config
(0.93 tại nominal 0.95 ⇒ realized ≈ nominal − 0.02), theo BASE CỦA ARCHETYPE — công thức cũ
`0.80 + lift + 0.03` vừa hardcode base P4 vừa CỘNG lạc quan ngược chiều anchor.
AUDIT STATS-7: mỗi ô ghi thêm `n_advice_events`/`n_offers` — phân biệt "advice không hiệu ứng"
với "cơ chế không kích hoạt" (P1 zero tuyệt đối là loại sau).
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

# Anchor ĐO trong config: max_realized_accept=0.93 tại effective nominal 0.95
# (accept_base P4 0.80 + lift_max 0.15) ⇒ realized ≈ nominal − REALIZED_GAP.
REALIZED_GAP = 0.02

BASE_BY_ARCHETYPE = {"P1": 0.85, "P2": 0.95, "P4": 0.80}   # khớp archetypes.py


def realized_cap(archetype: str, lift: float) -> float:
    """Trần realized-accept NHẤT QUÁN anchor đo (STATS-3): nominal − gap, kẹp ≤0.98."""
    base = BASE_BY_ARCHETYPE[archetype]
    return round(min(0.98, base + lift - REALIZED_GAP), 4)


def _count_advice(rb, aid: int) -> tuple[int, int]:
    n_adv = sum(1 for e in rb.events if e.actor_id == aid and e.kind.startswith("advice_"))
    offers = next((a.orders_offered for a in rb.actors if a.actor_id == aid), 0)
    return n_adv, offers


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
            n_advice_total = 0
            n_offers_total = 0
            for s in seeds:
                cb = _cfg_with(cfg, enabled=True, actor_id=aid, channels=CHANNELS)
                cb.data["advice"]["adherence_by_archetype"] = {archetype: adh}
                cb.data["advice"]["accept_lift_max"] = lift
                cb.data["advice"]["accept_lift_step"] = min(0.10, lift)
                # STATS-3: nhất quán anchor đo theo archetype (D-SIM-07)
                cb.data["advice"]["max_realized_accept"] = realized_cap(archetype, lift)
                rb = run_once(cb, s)
                ra = cache_a[s]
                na, no = _count_advice(rb, aid)
                n_advice_total += na
                n_offers_total += no
                pairs.append(PairResult(
                    seed=s, actor_id=aid,
                    a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                    system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid)))
            cell = compare(pairs)
            d = cell["driver"]["payout_vnd"]
            out[f"adh={adh}|lift={lift}"] = {
                "delta_mean": d["delta_mean"], "ci95": d["ci95"],
                "significant": d["significant"],
                "n_seeds": cell["n_seeds"], "n_insufficient": cell["n_insufficient"],
                "n_positive": d["n_positive"],
                # STATS-7: hiển thị cơ chế — 0 advice ⇒ Δ=0 là "không kích hoạt", không phải "vô dụng"
                "n_advice_events": n_advice_total, "n_offers": n_offers_total,
                "delta_bonus": cell["driver"]["day_bonus_vnd"]["delta_mean"],
                "served_guard": cell["system"]["served_rate"]["delta_mean"],
                "max_realized_accept_used": realized_cap(archetype, lift),
            }
            sig_txt = "SIG" if d["significant"] else (
                "n<30—không kết luận" if cell["n_insufficient"] else "ci-chứa-0")
            print(f"[{archetype}] adh={adh} lift={lift}: Δ={d['delta_mean']:+,.0f} "
                  f"CI[{d['ci95'][0]:+,.0f},{d['ci95'][1]:+,.0f}] {sig_txt} "
                  f"n_pos={d['n_positive']} advice={n_advice_total}", flush=True)
    return {"target_actor": aid, "cells": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=2000)
    ap.add_argument("--out", default=str(ROOT / "research" / "experiments" / "sensitivity"))
    args = ap.parse_args()
    cfg = Config.load(ROOT / "configs" / "pilot_dongda.yaml")
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    res = {"_meta": {
        "note": "MOCK — không phải số thật GSM. significant cần n>=30 (AUDIT STATS-5); "
                "n_advice_events=0 nghĩa là cơ chế KHÔNG kích hoạt (AUDIT STATS-7).",
        "realized_cap_rule": f"min(0.98, base_archetype + lift - {REALIZED_GAP}) — anchor đo 0.93",
    }}
    for arch in ("P4", "P1"):
        print(f"\n=== {arch} ({args.seeds} seed/ô) ===", flush=True)
        res[arch] = sweep(cfg, seeds, arch,
                          adherences=[0.3, 0.75, 1.0], lifts=[0.10, 0.15, 0.19])
    # P2 5-seed: kiểm CƠ CHẾ dip-rescue (STATS-4 — nhãn cũ "silence_check" đã bị data bác);
    # n<30 nên ô này KHÔNG mang kết luận thống kê — chỉ đếm advice + chiều Δ.
    print("\n=== P2 (5 seed — kiểm cơ chế dip-rescue, KHÔNG phải kết luận thống kê) ===", flush=True)
    res["P2_dip_rescue_check"] = sweep(cfg, seeds[:5], "P2",
                                       adherences=[1.0], lifts=[0.19])

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "dsim06_sweep.json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                              encoding="utf-8")
    print(f"\nghi {outdir / 'dsim06_sweep.json'}")
    print("MOCK — không phải số thật của GSM. Đọc kèm: mean ≠ 'ngày nào cũng lợi' (xem n_pos).")


if __name__ == "__main__":
    main()
