from __future__ import annotations

from types import SimpleNamespace


def _checkpoint_bundle():
    from gsm_core.lifecycle.checkpoint import checkpoint_record, normalize_solver_decision
    from gsm_core.lifecycle.checkpoint_store import build_artifact_record

    snapshot = {
        "driver_id": "d-7", "surface": "nudge", "trigger_type": "poll",
        "observed_at": "2026-07-01T08:20:00+07:00",
        "freshness_deadline": "2026-07-01T08:40:00+07:00",
        "shift_end": "2026-07-01T18:00:00+07:00", "run_id": "run-1",
        # AdviceCheckpoint schema owns the solver provenance vocabulary; the enclosing
        # demo step still carries ``data_mode=sim-engine`` separately.
        "data_mode": "synthetic", "is_mock": True,
    }
    solver_input = {"driver_id": "d-7", "schema_version": "1.1.0"}
    solver_report = {"status": "optimal", "confidence": 0.9,
                     "numbers": [{"value": 37.5, "unit": "percent", "source": "SIM"}],
                     "caveats": ["mock state"],
                     "solution": {"already_maxed": False, "feasible": True}}
    candidate = normalize_solver_decision(
        "S1", snapshot, solver_input, solver_report, "decision-1")
    state_artifact = build_artifact_record("state_snapshot", snapshot,
                                           created_at=snapshot["observed_at"])
    input_artifact = build_artifact_record("solver_input", solver_input,
                                           created_at=snapshot["observed_at"])
    report_artifact = build_artifact_record("solver_report", solver_report,
                                            created_at=snapshot["observed_at"])
    solver_artifact = build_artifact_record(
        "solver_artifact", {"solver_name": "S1",
                             "solver_input_ref": input_artifact["artifact_id"],
                             "solver_report_ref": report_artifact["artifact_id"]},
        created_at=snapshot["observed_at"])
    candidate.update({"snapshot_ref": state_artifact["artifact_id"],
                      "solver_input_refs": [input_artifact["artifact_id"]],
                      "solver_report_refs": [report_artifact["artifact_id"]],
                      "solver_artifact_ref": solver_artifact["artifact_id"]})
    return checkpoint_record(candidate), [state_artifact, input_artifact,
                                          report_artifact, solver_artifact]


def _result(checkpoint, artifacts):
    actor = SimpleNamespace(actor_id=7, archetype="P4", fleet=SimpleNamespace(value="swap"))
    event = SimpleNamespace(t_min=500.0, actor_id=7, kind="go_online", cell="home", detail={})
    snapshot = {
        "event_index": 0, "t_min": 500.0, "actor_id": 7, "state": "idle",
        "cell": "home", "lat": 21.01, "lon": 105.81, "soc_pct": 80.0,
        "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
        "orders_offered": 0, "orders_accepted": 0, "orders_completed": 0,
        "orders_cancelled": 0, "online_min": 0.0, "rest_min": 0.0,
        "charge_min": 0.0, "shift_start_min": 360.0, "shift_end_min": 1080.0,
    }
    return SimpleNamespace(run_id="run-1", seed=1000, actors=[actor], orders=[],
                           events=[event], trace_snapshots=[snapshot], segments=[],
                           advice_checkpoints=[checkpoint], advice_artifacts=artifacts,
                           advice_checkpoint_events=[])


def test_demo_step_persists_existing_checkpoint_and_offers_template_envelope(tmp_path):
    from app.services.demo_session import DemoSessionService

    checkpoint, artifacts = _checkpoint_bundle()
    service = DemoSessionService(
        run_factory=lambda seed: _result(checkpoint, artifacts),
        session_id_factory=lambda: "advice-session",
        checkpoint_store_path=tmp_path / "checkpoint.db",
    )
    service.create()
    service.select_actor("advice-session", 7)
    step = service.advance("advice-session", client_step_id="step-1",
                           expected_step_version=0)

    advice = step["advice"]
    assert advice["status"] == "ready"
    assert advice["presentation_source"] == "template"
    item = advice["items"][0]
    assert item["checkpoint_id"] == checkpoint["checkpoint_id"]
    assert item["display_id"]
    assert item["canonical_action"]["code"] == "PROTECT_ELIGIBILITY"
    assert item["provenance"]["is_mock"] is True


def test_demo_step_with_no_checkpoint_is_silent(tmp_path):
    from app.services.demo_session import DemoSessionService

    actor = SimpleNamespace(actor_id=7, archetype="P4",
                            fleet=SimpleNamespace(value="swap"))
    event = SimpleNamespace(t_min=500.0, actor_id=7, kind="go_online", cell="home", detail={})
    snapshot = {
        "event_index": 0, "t_min": 500.0, "actor_id": 7, "state": "idle",
        "cell": "home", "lat": 21.01, "lon": 105.81, "soc_pct": 80.0,
        "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
        "orders_offered": 0, "orders_accepted": 0, "orders_completed": 0,
        "orders_cancelled": 0, "online_min": 0.0, "rest_min": 0.0,
        "charge_min": 0.0, "shift_start_min": 360.0, "shift_end_min": 1080.0,
    }
    result = SimpleNamespace(run_id="run-1", seed=1000, actors=[actor], orders=[],
                             events=[event], trace_snapshots=[snapshot], segments=[],
                             advice_checkpoints=[], advice_artifacts=[],
                             advice_checkpoint_events=[])
    service = DemoSessionService(run_factory=lambda seed: result,
                                 session_id_factory=lambda: "silent-session",
                                 checkpoint_store_path=tmp_path / "checkpoint.db")
    service.create()
    service.select_actor("silent-session", 7)
    step = service.advance("silent-session", client_step_id="step-1",
                           expected_step_version=0)
    assert step["advice"] == {"status": "silent", "reason_code": "no_checkpoint"}
