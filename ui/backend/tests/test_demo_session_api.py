from __future__ import annotations

from types import SimpleNamespace

import pytest


def _result():
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
    return SimpleNamespace(
        run_id="run-1", seed=1000, actors=[actor], orders=[], events=[event],
        trace_snapshots=[snapshot], segments=[], advice_checkpoints=[],
        advice_artifacts=[], advice_checkpoint_events=[],
    )


def test_session_requires_actor_and_advance_is_idempotent():
    from app.services.demo_session import DemoSessionConflict, DemoSessionService

    service = DemoSessionService(
        run_factory=lambda seed: _result(), session_id_factory=lambda: "sess-1")
    created = service.create(seed=1000)
    assert created["session_id"] == "sess-1"
    assert created["run_id"] == "run-1"
    assert created["status"] == "awaiting_actor"
    assert created["actors"] == [{"actor_id": 7, "archetype": "P4", "fleet": "swap"}]

    selected = service.select_actor("sess-1", 7)
    assert selected["status"] == "active"
    assert selected["step_version"] == 0

    first = service.advance("sess-1", client_step_id="step-1", expected_step_version=0)
    retry = service.advance("sess-1", client_step_id="step-1", expected_step_version=0)
    assert first == retry
    assert first["step_version"] == 1
    assert first["run_id"] == "run-1"
    assert first["transition"]["kind"] == "go_online"

    with pytest.raises(DemoSessionConflict, match="step_version"):
        service.advance("sess-1", client_step_id="step-2", expected_step_version=0)


def test_unknown_actor_and_end_of_timeline_fail_loudly():
    from app.services.demo_session import DemoSessionNotFound, DemoSessionService

    service = DemoSessionService(run_factory=lambda seed: _result(), session_id_factory=lambda: "sess-2")
    service.create()
    with pytest.raises(DemoSessionNotFound):
        service.select_actor("missing", 7)
    with pytest.raises(ValueError, match="actor"):
        service.select_actor("sess-2", 99)

    service.select_actor("sess-2", 7)
    service.advance("sess-2", client_step_id="step-1", expected_step_version=0)
    with pytest.raises(DemoSessionNotFound, match="completed"):
        service.advance("sess-2", client_step_id="step-2", expected_step_version=1)


def test_http_contract_uses_idempotent_step_and_version_conflict(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import demo
    from app.services.demo_session import DemoSessionService

    service = DemoSessionService(
        run_factory=lambda seed: _result(), session_id_factory=lambda: "http-session")
    monkeypatch.setattr(demo, "DEMO_SESSIONS", service)
    client = TestClient(app)

    created = client.post("/api/v1/demo/sessions", json={"seed": 1000})
    assert created.status_code == 200
    assert client.put("/api/v1/demo/sessions/http-session/driver",
                      json={"actor_id": 7}).status_code == 200
    body = {"client_step_id": "client-step-1", "expected_step_version": 0}
    first = client.post("/api/v1/demo/sessions/http-session/steps", json=body)
    retry = client.post("/api/v1/demo/sessions/http-session/steps", json=body)
    assert first.status_code == retry.status_code == 200
    assert first.json() == retry.json()
    stale = client.post("/api/v1/demo/sessions/http-session/steps", json={
        "client_step_id": "client-step-2", "expected_step_version": 0,
    })
    assert stale.status_code == 409
