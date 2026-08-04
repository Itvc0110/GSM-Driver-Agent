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

    why = service.explain_demo_why(
        "advice-session", item["checkpoint_id"], display_id=item["display_id"],
        client_request_id="demo-why-1", expected_step_version=1)
    assert why["status"] == "ready"
    assert why["presentation_source"] == "template"
    assert why["checkpoint_id"] == item["checkpoint_id"]


def test_existing_checkpoint_retry_returns_pinned_presentation(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    checkpoint, artifacts = _checkpoint_bundle()
    with CheckpointStore(tmp_path / "pinned.db") as store:
        store.create_checkpoint_bundle(artifacts, checkpoint)
        service = AdviceCheckpointService(store)
        first = service.present_existing_checkpoint(
            checkpoint["checkpoint_id"], surface="nudge",
            generated_at="2026-07-01T08:20:00+07:00")
        card = first["items"][0]

        def rerender_must_not_run(*args, **kwargs):
            raise AssertionError("existing lease retry must not rerender")

        service._prepare_presentation = rerender_must_not_run
        second = service.present_existing_checkpoint(
            checkpoint["checkpoint_id"], surface="nudge",
            generated_at="2026-07-01T08:20:00+07:00")
        assert second["items"][0] == card


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
    assert step["advice"]["status"] == "silent"
    assert step["advice"]["silent"]["reason_code"] == "no_checkpoint"
    assert step["advice"]["items"] == []


def test_demo_does_not_present_advice_while_actor_is_moving(tmp_path):
    from app.services.demo_session import DemoSessionService

    checkpoint, artifacts = _checkpoint_bundle()
    result = _result(checkpoint, artifacts)
    result.trace_snapshots[0]["state"] = "enroute"
    service = DemoSessionService(
        run_factory=lambda seed: result,
        session_id_factory=lambda: "moving-session",
        checkpoint_store_path=tmp_path / "checkpoint.db",
    )
    service.create()
    service.select_actor("moving-session", 7)
    step = service.advance("moving-session", client_step_id="step-1",
                           expected_step_version=0)
    assert step["advice"]["status"] == "silent"
    assert step["advice"]["silent"]["reason_code"] == "unsafe_while_moving"


def test_demo_sessions_isolate_checkpoint_lifecycle(tmp_path):
    from app.services.demo_session import DemoSessionService

    checkpoint, artifacts = _checkpoint_bundle()
    result_factory = lambda seed: _result(checkpoint, artifacts)
    root = tmp_path / "checkpoint.db"
    first = DemoSessionService(run_factory=result_factory,
                               session_id_factory=lambda: "session-a",
                               checkpoint_store_path=root)
    second = DemoSessionService(run_factory=result_factory,
                                session_id_factory=lambda: "session-b",
                                checkpoint_store_path=root)
    first.create()
    first.select_actor("session-a", 7)
    second.create()
    second.select_actor("session-b", 7)

    first_step = first.advance("session-a", client_step_id="step-1", expected_step_version=0)
    second_step = second.advance("session-b", client_step_id="step-1", expected_step_version=0)

    assert first_step["advice"]["status"] == "ready"
    assert second_step["advice"]["status"] == "ready"
    assert first.checkpoint_path("session-a") != second.checkpoint_path("session-b")
