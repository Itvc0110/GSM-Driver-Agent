"""Probe SABOTAGE end-to-end cho guardrail TẦNG 5 (D-M3-05) — bằng chứng sống, không phải dict.

Câu hỏi: nếu ai đó XOÁ lan can `fatigued` (kịch bản "mua Δ bằng cách xoá lan can" mà
guardrail 4 tầng từng CÂM), tầng 5 có tố giác trên RUN THẬT không?

Ba thế giới × N seed:
  A      — advice off (baseline lan can: rails vẫn bắn vì check TRƯỚC channel-gate)
  B      — ladder all, coverage all (arm bình thường — kỳ vọng: KHÔNG flag)
  B_sab  — như B nhưng lan can `fatigued` bị VÔ HIỆU (monkeypatch nâng ngưỡng lên ∞ CHỈ
           trong lúc gọi `should_defer_rest` — bản năng nghỉ của behavior giữ nguyên vì nó
           đọc threshold lúc khác) — kỳ vọng: flag "lan can `fatigued` SỤP VỀ 0"

    uv run python scripts/probe_rest_rails.py [n_seeds]     # mặc định 5, seeds 5100+

Mọi số là MOCK. Artifact: research/audit/2026-07-27-current-state/42-rest-rails-sabotage-probe.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from gsm_sim import advice_bridge as AB
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
from gsm_sim.runner import Config, run_once
from gsm_sim.sim_metrics import health_guardrail, health_guardrail_flags

OUT = Path("research/audit/2026-07-27-current-state")
KEYS = ("rest_min_total", "veto_calls_n", "veto_fired_n", "veto_soc_low_n",
        "veto_fatigued_n", "veto_defer_cap_n", "work_span_p90", "work_span_max",
        "drive_min_p90", "drive_min_max")


def _mean(rows: list[dict]) -> dict:
    return {k: round(float(np.mean([r[k] for r in rows])), 2) for k in KEYS}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    seeds = list(range(5100, 5100 + n))
    base = Config.load("configs/pilot_dongda.yaml")
    cfg_a = _cfg_with(base, enabled=False, actor_id=None, channels=None)
    cfg_b = _cfg_with(base, enabled=True, actor_id=None,
                      channels=CHANNEL_LADDER["all"], coverage="all")

    orig = AB.AdviceActionBridge.should_defer_rest

    def sabotaged(self, actor, now_min, hour, hint, soc):
        """Kẻ tấn công 'nới ngưỡng mệt' — lan can fatigued không bao giờ bắn."""
        keep = actor.fatigue_threshold_min
        actor.fatigue_threshold_min = float("inf")
        try:
            return orig(self, actor, now_min, hour, hint, soc)
        finally:
            actor.fatigue_threshold_min = keep

    rows = {"A": [], "B": [], "B_sab": []}
    for s in seeds:
        rows["A"].append(health_guardrail(run_once(cfg_a, s)))
        rows["B"].append(health_guardrail(run_once(cfg_b, s)))
        AB.AdviceActionBridge.should_defer_rest = sabotaged
        try:
            rows["B_sab"].append(health_guardrail(run_once(cfg_b, s)))
        finally:
            AB.AdviceActionBridge.should_defer_rest = orig
        print(f"  seed {s}: A/B/B_sab xong", flush=True)

    a, b, bs = _mean(rows["A"]), _mean(rows["B"]), _mean(rows["B_sab"])
    flags_b = health_guardrail_flags(a, b)
    flags_sab = health_guardrail_flags(a, bs)
    art = {"what": "Tầng 5 sabotage end-to-end — lan can fatigued bị vô hiệu ở B_sab",
           "mock": True, "seeds": seeds,
           "mean": {"A": a, "B": b, "B_sab": bs},
           "flags_B_vs_A": flags_b, "flags_B_sab_vs_A": flags_sab,
           "verdict": ("TẦNG 5 TỐ GIÁC ĐÚNG" if
                       (not flags_b and any("fatigued" in f and "SỤP VỀ 0" in f
                                            for f in flags_sab))
                       else "🔴 KIỂM LẠI — hành vi không như thiết kế")}
    out = OUT / "42-rest-rails-sabotage-probe.json"
    out.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {out}")
    print(f"A:     fatigued={a['veto_fatigued_n']:.0f} calls={a['veto_calls_n']:.0f}")
    print(f"B:     fatigued={b['veto_fatigued_n']:.0f} calls={b['veto_calls_n']:.0f} "
          f"flags={flags_b or 'KHÔNG (đúng)'}")
    print(f"B_sab: fatigued={bs['veto_fatigued_n']:.0f} calls={bs['veto_calls_n']:.0f}")
    print("flags B_sab:", flags_sab or "🔴 KHÔNG CÓ — tầng 5 câm!")
    print("VERDICT:", art["verdict"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
