"""UPDATE-147 — moving gate của replay phải để lại dấu vết lifecycle và resume được.

Trước đây `present_existing_checkpoint(is_driving=True)` trả silent KHÔNG event ⇒
không phân biệt được "im vì đang lái" với "card mất"; và checkpoint không bao giờ
được xem xét lại khi state an toàn trở lại (goal #6/#7 của yêu cầu).
"""

from __future__ import annotations

from tests.test_demo_advice_bridge import _checkpoint_bundle


def _service(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    checkpoint, artifacts = _checkpoint_bundle()
    store = CheckpointStore(tmp_path / "checkpoint.db")
    store.create_checkpoint_bundle(artifacts, checkpoint)
    return AdviceCheckpointService(store), store, checkpoint


def test_moving_presentation_records_queued_event_then_resumes(tmp_path):
    service, store, checkpoint = _service(tmp_path)
    checkpoint_id = checkpoint["checkpoint_id"]

    moving = service.present_existing_checkpoint(
        checkpoint_id, surface="nudge",
        generated_at="2026-07-01T08:25:00+07:00", is_driving=True)
    assert moving["status"] == "silent"
    assert moving["silent"]["reason_code"] == "unsafe_while_moving"
    assert store.state(checkpoint_id)["state"] == "queued"
    queued_events = [e for e in store.events(checkpoint_id)
                     if e["event_type"] == "queued"]
    assert queued_events and queued_events[0]["reason_code"] == "unsafe_while_moving"

    # cùng transition replay lại (idempotent) — không nhân đôi event
    again = service.present_existing_checkpoint(
        checkpoint_id, surface="nudge",
        generated_at="2026-07-01T08:25:00+07:00", is_driving=True)
    assert again["status"] == "silent"
    assert len([e for e in store.events(checkpoint_id)
                if e["event_type"] == "queued"]) == 1

    # state an toàn trở lại TRONG validity ⇒ resume queued→ready→offered, có card
    resumed = service.present_existing_checkpoint(
        checkpoint_id, surface="nudge",
        generated_at="2026-07-01T08:30:00+07:00", is_driving=False)
    assert resumed["status"] == "ready"
    assert resumed["items"][0]["checkpoint_id"] == checkpoint_id
    assert store.state(checkpoint_id)["state"] == "offered"
    types = [e["event_type"] for e in store.events(checkpoint_id)]
    assert types.count("queued") == 1 and "ready" in types and "offered" in types
    store.close()


def test_queued_checkpoint_expires_honestly_if_never_safe(tmp_path):
    service, store, checkpoint = _service(tmp_path)
    checkpoint_id = checkpoint["checkpoint_id"]

    service.present_existing_checkpoint(
        checkpoint_id, surface="nudge",
        generated_at="2026-07-01T08:25:00+07:00", is_driving=True)
    # quá freshness 08:40 ⇒ expired, không lease, kể cả khi đã dừng xe
    late = service.present_existing_checkpoint(
        checkpoint_id, surface="nudge",
        generated_at="2026-07-01T08:45:00+07:00", is_driving=False)
    assert late["status"] == "silent"
    assert late["silent"]["reason_code"] == "expired"
    assert store.state(checkpoint_id)["state"] == "expired"
    store.close()
