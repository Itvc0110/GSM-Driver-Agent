"""Smoke LIVE — chạy AdvisorPipeline với Composer LLM thật (deepseek qua ai-box.vn).

NGOÀI test-suite (gọi mạng, không deterministic). In 4 advice mẫu (F0–F3) để Cường
xem chất lượng text + kiểm 2 HARD invariant (faithfulness/number_traceability=1.0).

Chạy:  uv sync --extra llm && uv run python scripts/smoke_advisor_live.py
Cần .env (OPENAI_BASE_URL/OPENAI_API_KEY/DEFAULT_MODEL) — KHÔNG commit.
Nếu LLM lỗi/403 → composer tự hạ template (fail-closed); script vẫn in advice + cờ fallback.
"""

from __future__ import annotations

import json
from pathlib import Path

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.bonus_feasibility import solve
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.advisor.composer import Composer
from gsm_core.advisor.observability import ObservabilityRecorder, compute_faithfulness

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300}, "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                    "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


def _s1(policy):
    gi = {"schema_version": "1.0.0", "driver_id": "d", "t_now": "2026-07-01T18:00:00+07:00",
          "points_now": 140, "next_tiers": [[160, 115000], [200, 170000]],
          "historical_points_per_hour": {"offpeak": 15.0, "peak": 25.0},
          "hours_budget_remaining": 3.0, "acceptance_rate": 0.9, "completion_rate": 0.9,
          "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0", "source": "MOCK"}
    return solve(gi, policy)


def _s2():
    return {"schema_version": "1.0.0", "solver": "shift_dp",
            "problem_digest": "Kế hoạch: nghỉ khung trưa, chạy dồn khung 17-20h.",
            "inputs_used": [{"view_id": "sp:d", "version": "1.0.0",
                             "freshness": "2026-07-01T18:00:00+07:00"}],
            "solution": {"feasible": True, "next_action": {"action": "REST",
                         "bucket": "14:00-15:00", "reason": "khung vắng khách"}},
            "numbers": [{"value": 2, "unit": "hours", "source": "dp:shift-v1"}],
            "sensitivity": [], "confidence": 0.7, "caveats": [], "infeasible_reason": None}


def _s3():
    return {"schema_version": "1.0.0", "solver": "f3_patterns", "problem_digest": "Tổng kết ca.",
            "inputs_used": [{"view_id": "ss:d", "version": "1.0.0",
                             "freshness": "2026-07-01T22:00:00+07:00"}],
            "solution": {"top_pattern": {"pattern_id": "idle_gap",
                         "heuristic_note": "Anh/chị có 45 phút trống lúc 15h."}},
            "numbers": [{"value": 45, "unit": "minutes", "source": "historical:ss-v1"}],
            "sensitivity": [], "confidence": 0.65, "caveats": [], "infeasible_reason": None}


def main():
    policy = PolicyBundle.from_record(POLICY_REC)
    reports_by_feat = {"F0": [_s1(policy)], "F1": [_s1(policy), _s2()],
                       "F2": [_s2()], "F3": [_s3()]}
    queries = {"F0": "tuần này cần bao nhiêu điểm để được thưởng"}

    try:
        from gsm_core.advisor.llm_client import LLMComposerClient
        composer = Composer(llm=LLMComposerClient())
        mode = "live"
        print("LLM: live (deepseek qua ai-box.vn)\n")
    except Exception as e:  # noqa: BLE001 — thiếu deps/.env → chạy template
        composer, mode = None, "off"
        print(f"LLM không khả dụng ({type(e).__name__}: {str(e)[:80]}) → template mode\n")

    recorder = ObservabilityRecorder()
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=":memory:",
                           llm_mode=mode, composer=composer, recorder=recorder)
    for feat in ("F0", "F1", "F2", "F3"):
        reports = reports_by_feat[feat]
        req = {"schema_version": "1.0.0", "request_id": f"smoke-{feat}", "driver_id": "d-1",
               "feature": feat, "free_text_query": queries.get(feat), "l3_view_refs": [],
               "session_id": "s", "t_request": "2026-07-01T18:00:00+07:00",
               "trigger_source": "user_ask"}
        adv = pipe.handle(req, solver_reports=reports, kb_track="platform")
        faith = compute_faithfulness(adv["numbers"], reports)
        print(f"=== {feat} | fallback={adv['fallback_used']} "
              f"verify={pipe.last_verify_result.get('passed')} faithfulness={faith} ===")
        print(adv["message"])
        if adv["advice_spec"]:
            print("  advice_spec:", json.dumps(adv["advice_spec"], ensure_ascii=False))
        if adv["citations"]:
            print("  cite:", adv["citations"][0])
        print()

    print("HARD invariant OK:", all(r["hard_invariant_ok"] for r in recorder.rows))


if __name__ == "__main__":
    main()
