from __future__ import annotations

from ui.backend.tests.test_demo_advice_bridge import _checkpoint_bundle, _result


def test_demo_display_ack_and_response_share_checkpoint_lease(tmp_path):
    from app.services.demo_session import DemoSessionService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    checkpoint, artifacts = _checkpoint_bundle()
    result = _result(checkpoint, artifacts)
    service = DemoSessionService(
        run_factory=lambda seed: result,
        session_id_factory=lambda: "ack-session",
        checkpoint_store_path=tmp_path / "checkpoint.db",
    )
    service.create()
    service.select_actor("ack-session", 7)
    step = service.advance("ack-session", client_step_id="step-1",
                           expected_step_version=0)
    item = step["advice"]["items"][0]
    display = {
        "display_id": item["display_id"], "client_event_id": "mount-1",
        "mounted_at": "2026-07-01T08:20:01+07:00",
    }
    assert service.acknowledge_demo_display("ack-session", checkpoint["checkpoint_id"], **display)["ok"]
    replay = service.acknowledge_demo_display("ack-session", checkpoint["checkpoint_id"], **display)
    assert replay["idempotent_replay"] is True
    response = service.record_demo_response(
        "ack-session", checkpoint["checkpoint_id"],
        display_id=item["display_id"], client_event_id="accept-1",
        response="accepted", occurred_at="2026-07-01T08:20:02+07:00")
    assert response["event_type"] == "accepted"
    with CheckpointStore(service.checkpoint_path("ack-session")) as store:
        event_types = [event["event_type"] for event in store.events(checkpoint["checkpoint_id"])]
    assert event_types[-2:] == ["displayed", "accepted"]
