"""Closed HTTP contract for AdviceEnvelopeV2 and lease lifecycle."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import validate

from app.main import app


ROOT = Path(__file__).resolve().parents[3]
client = TestClient(app)


class FakeOrchestrator:
    def solve(self, driver_id, t_now, shift_start_min, shift_end_min, surface="nudge"):
        from app.services.advice_checkpoint import (
            ProductSolverResult,
            _normalize_with_artifacts,
        )
        snapshot = {
            "driver_id": driver_id, "surface": surface, "trigger_type": "poll",
            "observed_at": t_now,
            "freshness_deadline": "2026-08-03T09:20:00+07:00",
            "shift_end": "2026-08-03T18:00:00+07:00",
            "data_mode": "mock-realdata", "is_mock": True, "run_id": None,
        }
        report = {"confidence": 0.8, "numbers": [], "caveats": [],
                  "solution": {"already_maxed": False, "feasible": True}}
        candidate, artifacts = _normalize_with_artifacts(
            "S1", snapshot, {"driver_id": driver_id}, report,
            f"s1-{driver_id}-2026-08-03-540")
        return ProductSolverResult(
            candidates=[candidate], artifacts=artifacts, solver_set=["S1"])


def _enable(monkeypatch, tmp_path):
    from app.routers import advice_v2

    monkeypatch.setenv("ADVICE_V2_ENABLED", "1")
    monkeypatch.setattr(advice_v2, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_v2, "ORCHESTRATOR_FACTORY", FakeOrchestrator)


def _query():
    return {
        "surface": "nudge", "driver_id": "d-1", "date": "2026-08-03",
        "now_min": 540, "shift_start_min": 360, "shift_end_min": 1080,
        "is_driving": False,
    }


def test_flag_disabled_returns_explicit_fallback_status(monkeypatch):
    monkeypatch.delenv("ADVICE_V2_ENABLED", raising=False)
    response = client.get("/api/v2/advice", params=_query())
    assert response.status_code == 503
    assert response.json() == {"status": "disabled", "fallback": "v1"}


def test_query_is_surface_only_and_envelope_matches_closed_contract(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    assert client.get("/api/v2/advice", params={**_query(), "topic": "energy"}).status_code == 422
    assert client.get("/api/v2/advice", params={**_query(), "priority": "high"}).status_code == 422

    response = client.get("/api/v2/advice", params=_query())
    assert response.status_code == 200
    body = response.json()
    # `encoding="utf-8"` là BẮT BUỘC, không phải cho gọn: `read_text()` không khai encoding sẽ dùng
    # cp1252 trên Windows ⇒ `UnicodeDecodeError` ngay khi contract có một ký tự tiếng Việt. Bảy
    # contract còn lại trong `ui/contracts/` ĐỀU đã có tiếng Việt (advice.json: 796 byte phi-ASCII);
    # `advice_v2.json` từng là cái duy nhất ASCII thuần, nên dòng này xanh **nhờ may**. Nó đỏ ngay
    # khi QĐ-4 thêm cảnh báo ranh giới bằng tiếng Việt vào đó — tức bug tiềm ẩn, không phải hồi quy.
    schema = json.loads((ROOT / "ui/contracts/advice_v2.json").read_text(encoding="utf-8"))
    validate(body, schema)
    assert len(body["items"]) == 1


def test_http_ack_response_status_and_idempotency(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    card = client.get("/api/v2/advice", params=_query()).json()["items"][0]
    ack_body = {
        "display_id": card["display_id"], "client_event_id": "mount-1",
        "mounted_at": "2026-08-03T09:00:01+07:00",
    }
    url = f"/api/v2/advice/{card['checkpoint_id']}/display"
    assert client.post(url, json=ack_body).json()["idempotent_replay"] is False
    assert client.post(url, json=ack_body).json()["idempotent_replay"] is True
    stale = client.post(url, json={**ack_body, "display_id": "stale", "client_event_id": "m2"})
    assert stale.status_code == 409

    response_url = f"/api/v2/advice/{card['checkpoint_id']}/response"
    accepted = client.post(response_url, json={
        "display_id": card["display_id"], "client_event_id": "response-1",
        "response": "accepted", "occurred_at": "2026-08-03T09:00:02+07:00",
    })
    assert accepted.status_code == 200
    missing = client.post("/api/v2/advice/ckpt-missing/display", json=ack_body)
    assert missing.status_code == 404
    invalid = client.post(response_url, json={
        "display_id": card["display_id"], "client_event_id": "response-2",
        "response": "followed", "occurred_at": "2026-08-03T09:00:03+07:00",
    })
    assert invalid.status_code == 422
