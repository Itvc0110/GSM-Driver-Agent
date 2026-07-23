"""C6 integration — 3 driver × 4 feature (template mode) → 12 advice pass registry.

Đường LLM-off (deterministic). SolverReport S1 là THẬT (gọi solver `solve()` trên
policy L0); S2/S3/S4 là fixture gắn nhãn MOCK để render nhánh template F1/F2/F3.
Assert: (1) 12/12 advice hợp schema composed_advice; (2) 2 HARD invariant =1.0
(number_traceability, faithfulness); (3) verifier không lỗi; (4) fallback_used=True.
"""

from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.bonus_feasibility import solve
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.advisor.observability import (
    ObservabilityRecorder, compute_faithfulness, compute_number_traceability)
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                    "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _s1_report(policy, points_now):
    """SolverReport S1 THẬT từ solver (số có source)."""
    gi = {"schema_version": "1.0.0", "driver_id": "d", "t_now": "2026-07-01T18:00:00+07:00",
          "points_now": points_now,
          "next_tiers": [[t, v] for t, v in POLICY_REC["day_bonus_tiers"] if t > points_now],
          "historical_points_per_hour": {"offpeak": 15.0, "peak": 25.0},
          "hours_budget_remaining": 3.0, "acceptance_rate": 0.9, "completion_rate": 0.9,
          "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0", "source": "MOCK"}
    return solve(gi, policy)


def _s2_report():  # fixture MOCK — nhánh next_action cho F1/F2
    return {"schema_version": "1.0.0", "solver": "shift_dp",
            "problem_digest": "Kế hoạch: chạy dồn khung 17-20h.",
            "inputs_used": [{"view_id": "sp:d", "version": "1.0.0",
                             "freshness": "2026-07-01T18:00:00+07:00"}],
            "solution": {"feasible": True,
                         "next_action": {"action": "REST", "bucket": "14:00-15:00",
                                         "reason": "khung vắng khách"}},
            "numbers": [{"value": 2, "unit": "hours", "source": "dp:shift-v1"}],
            "sensitivity": [], "confidence": 0.7, "caveats": [], "infeasible_reason": None}


def _s3_report():  # fixture MOCK — top_pattern cho F3
    return {"schema_version": "1.0.0", "solver": "f3_patterns",
            "problem_digest": "Tổng kết ca.",
            "inputs_used": [{"view_id": "ss:d", "version": "1.0.0",
                             "freshness": "2026-07-01T22:00:00+07:00"}],
            "solution": {"top_pattern": {"pattern_id": "idle_gap",
                                          "heuristic_note": "Anh/chị có 45 phút trống lúc 15h."}},
            "numbers": [{"value": 45, "unit": "minutes", "source": "historical:ss-v1"}],
            "sensitivity": [], "confidence": 0.65, "caveats": [], "infeasible_reason": None}


def _reports_for(feature, policy, points_now):
    if feature == "F0":
        return [_s1_report(policy, points_now)]
    if feature == "F1":
        return [_s1_report(policy, points_now), _s2_report()]
    if feature == "F2":
        return [_s2_report()]
    return [_s3_report()]  # F3


def test_integration_3x4_template_mode(reg, tmp_path, policy):
    recorder = ObservabilityRecorder(parquet_path=tmp_path / "spans.parquet")
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db",
                           llm_mode="off", recorder=recorder)
    drivers = [("d-1", 140), ("d-2", 100), ("d-3", 40)]
    features = ["F0", "F1", "F2", "F3"]
    n = 0
    for did, pts in drivers:
        for feat in features:
            reports = _reports_for(feat, policy, pts)
            req = {"schema_version": "1.0.0", "request_id": f"r-{did}-{feat}",
                   "driver_id": did, "feature": feat, "free_text_query": None,
                   "l3_view_refs": [], "session_id": "s",
                   "t_request": "2026-07-01T18:00:00+07:00", "trigger_source": "user_ask"}
            advice = pipe.handle(req, solver_reports=reports, kb_track="platform")
            assert reg.validate("composed_advice", advice) == [], f"{did}/{feat} schema fail"
            assert advice["fallback_used"] is True
            assert pipe.last_verify_result["passed"] is True, f"{did}/{feat} verify fail"
            # HARD: faithfulness advice↔solver = 1.0
            assert compute_faithfulness(advice["numbers"], reports) == 1.0
            n += 1
    assert n == 12
    assert pipe.store.count_episodes() == 12
    # recorder: mọi span giữ HARD invariant
    assert len(recorder.rows) == 12
    assert all(row["hard_invariant_ok"] for row in recorder.rows)
    assert all(row["solver_number_traceability"] == 1.0 for row in recorder.rows)
    # parquet ghi được (dual-channel headless)
    assert recorder.flush().exists()


# ---------- observability HARD invariant unit ----------

def test_number_traceability_all_sourced():
    reps = [{"numbers": [{"value": 20, "unit": "points", "source": "policy_v:x"}]}]
    assert compute_number_traceability(reps) == 1.0


def test_number_traceability_catches_missing_source():
    reps = [{"numbers": [{"value": 20, "unit": "points", "source": ""}]}]
    assert compute_number_traceability(reps) < 1.0


def test_faithfulness_catches_fabricated_number():
    reports = [{"numbers": [{"value": 20, "unit": "points", "source": "policy_v:x"}]}]
    # advice có số 999 KHÔNG tồn tại trong solver → faithfulness < 1.0 (bịa)
    advice_numbers = [{"value": 20, "unit": "points", "source": "policy_v:x"},
                      {"value": 999, "unit": "vnd", "source": "policy_v:x"}]
    assert compute_faithfulness(advice_numbers, reports) < 1.0


def test_faithfulness_exact_match_is_one():
    reports = [{"numbers": [{"value": 20, "unit": "points", "source": "policy_v:x"},
                            {"value": 115000, "unit": "vnd", "source": "policy_v:x"}]}]
    assert compute_faithfulness(reports[0]["numbers"], reports) == 1.0
