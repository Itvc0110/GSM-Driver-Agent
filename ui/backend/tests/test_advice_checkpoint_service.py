"""P3A product solver orchestration and true runtime-state gate."""

from __future__ import annotations

from dataclasses import replace


def _s1_report():
    return {
        "confidence": 0.8,
        "solution": {"already_maxed": False, "feasible": True, "gap_points": 15},
    }


def _base_spi():
    return {
        "schema_version": "1.0.0", "driver_id": "d-1",
        "t_now": "2026-08-03T09:00:00+07:00", "buckets_remaining": 2,
        "soc_pct": None, "points_now": 30,
        "demand_forecast": [
            {"bucket": "2026-08-03T09:00:00+07:00", "cell_cluster": "h3-a",
             "expected_orders": 1.0},
            {"bucket": "2026-08-03T10:00:00+07:00", "cell_cluster": "h3-a",
             "expected_orders": 1.0},
        ],
        "policy_bundle_version": "test", "view_version": "l1r-v1", "source": "REAL",
    }


def test_missing_true_state_skips_s2_without_using_soc_proxy(monkeypatch):
    from app.services import advice_checkpoint as svc

    calls = {"s2": 0}
    monkeypatch.setattr(svc.advisor, "build_gi", lambda *a, **kw: {"driver_id": "d-1"})
    monkeypatch.setattr(svc.bonus_feasibility, "solve", lambda *a, **kw: _s1_report())
    monkeypatch.setattr(svc.shift_dp, "solve",
                        lambda *a, **kw: calls.__setitem__("s2", calls["s2"] + 1))
    orchestrator = svc.ProductSolverOrchestrator(
        runtime_state_provider=svc.UnavailableRuntimeStateProvider(),
        l1r_provider=lambda: {},
    )

    result = orchestrator.solve(
        "d-1", "2026-08-03T09:00:00+07:00", 360, 1080)

    assert calls["s2"] == 0
    assert result.reasons["S2"] == "missing_state"
    assert result.solver_set == ["S1"]
    assert [candidate["solver_set"] for candidate in result.candidates] == [["S1"]]


def test_trusted_state_injects_latest_s2_schema_and_preserves_current_future(monkeypatch):
    from app.services import advice_checkpoint as svc

    state = svc.ProductDriverRuntimeState(
        soc_pct=37.5, rest_taken_min=25.0, shift_elapsed_min=180.0,
        observed_at="2026-08-03T08:59:00+07:00",
        freshness_deadline="2026-08-03T09:10:00+07:00", source="LIVE",
    )
    seen = {}
    monkeypatch.setattr(svc.advisor, "build_gi", lambda *a, **kw: {"driver_id": "d-1"})
    monkeypatch.setattr(svc.bonus_feasibility, "solve",
                        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("s1 down")))
    monkeypatch.setattr(svc, "derive_shift_plan_input_l1r", lambda *a, **kw: _base_spi())

    def solve_s2(spi, policy):
        seen.update(spi)
        return {"confidence": 0.9, "solution": {
            "schedule": [
                {"bucket": "2026-08-03T09:00:00+07:00", "action": "ONLINE"},
                {"bucket": "2026-08-03T10:00:00+07:00", "action": "SWAP"},
            ],
            "next_action": {
                "bucket": "2026-08-03T10:00:00+07:00", "action": "SWAP",
            },
        }}

    monkeypatch.setattr(svc.shift_dp, "solve", solve_s2)
    orchestrator = svc.ProductSolverOrchestrator(
        runtime_state_provider=svc.StaticRuntimeStateProvider(state),
        l1r_provider=lambda: {},
    )

    result = orchestrator.solve(
        "d-1", "2026-08-03T09:00:00+07:00", 360, 1080)

    assert result.reasons["S1"] == "solver_error"
    assert result.solver_set == ["S2"]
    assert seen["schema_version"] == "1.1.0"
    assert seen["soc_pct"] == 37.5
    assert seen["rest_taken_min"] == 25.0
    assert seen["shift_elapsed_min"] == 180.0
    candidate = result.candidates[0]
    assert candidate["current_action"]["code"] == "ONLINE"
    assert candidate["future_plan"][0]["code"] == "SWAP"
    assert candidate["solver_set"] == ["S2"]
    artifact_ids = {artifact["artifact_id"] for artifact in result.artifacts}
    assert candidate["solver_input_refs"][0] in artifact_ids
    assert candidate["solver_report_refs"][0] in artifact_ids


def test_stale_runtime_state_is_missing_state(monkeypatch):
    from app.services import advice_checkpoint as svc

    stale = svc.ProductDriverRuntimeState(
        soc_pct=50, rest_taken_min=0, shift_elapsed_min=60,
        observed_at="2026-08-03T08:00:00+07:00",
        freshness_deadline="2026-08-03T08:30:00+07:00", source="REAL",
    )
    monkeypatch.setattr(svc.advisor, "build_gi", lambda *a, **kw: {"driver_id": "d-1"})
    monkeypatch.setattr(svc.bonus_feasibility, "solve", lambda *a, **kw: _s1_report())
    monkeypatch.setattr(svc.shift_dp, "solve",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must skip")))
    result = svc.ProductSolverOrchestrator(
        runtime_state_provider=svc.StaticRuntimeStateProvider(stale),
        l1r_provider=lambda: {},
    ).solve("d-1", "2026-08-03T09:00:00+07:00", 360, 1080)

    assert result.reasons["S2"] == "missing_state"
    assert result.solver_set == ["S1"]


def test_future_observed_runtime_state_is_missing_state(monkeypatch):
    """A freshness deadline alone must not admit state observed in the future."""
    from app.services import advice_checkpoint as svc

    future = svc.ProductDriverRuntimeState(
        soc_pct=50, rest_taken_min=0, shift_elapsed_min=60,
        observed_at="2026-08-03T09:05:00+07:00",
        freshness_deadline="2026-08-03T09:20:00+07:00", source="LIVE",
    )
    monkeypatch.setattr(svc.advisor, "build_gi", lambda *a, **kw: {"driver_id": "d-1"})
    monkeypatch.setattr(svc.bonus_feasibility, "solve", lambda *a, **kw: _s1_report())
    monkeypatch.setattr(svc.shift_dp, "solve",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must skip")))

    result = svc.ProductSolverOrchestrator(
        runtime_state_provider=svc.StaticRuntimeStateProvider(future),
        l1r_provider=lambda: {},
    ).solve("d-1", "2026-08-03T09:00:00+07:00", 360, 1080)

    assert result.reasons["S2"] == "missing_state"
    assert result.solver_set == ["S1"]
