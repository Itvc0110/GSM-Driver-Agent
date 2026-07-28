"""ĐA-05 Cycle W — POST /advice/action ghi store canonical (AdviceEventLog).

Ngữ nghĩa mới đáng test nhất: double-click cùng nút trong cùng phút = MỘT event
(idempotent theo event_id); JSONL vẫn append đủ (debug export, không canonical).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routers import advice as advice_router
from gsm_core.lifecycle.event_log import AdviceEventLog

client = TestClient(app)

BODY = {"advice_id": "s1-driver-01-2026-07-29-840", "driver_id": "driver-01",
        "date": "2026-07-29", "action": "followed", "card_kind": "brief",
        "at_min": 840}


def _patch(tmp_path, monkeypatch):
    monkeypatch.setattr(advice_router, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_router, "ACTIONS_FILE", tmp_path / "a.jsonl")


def test_double_click_is_one_lifecycle_event(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        evs = log.events(decision_id=BODY["advice_id"])
    assert len(evs) == 1, "double-click cùng phút phải là MỘT event (INSERT OR IGNORE)"
    assert evs[0]["event_type"] == "followed" and evs[0]["origin"] == "ui"
    # JSONL debug export vẫn ghi đủ 2 dòng (không phải store canonical)
    assert len((tmp_path / "a.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    # GET đọc từ store canonical ⇒ 1 hàng
    rows = client.get("/api/v1/advice/actions").json()["actions"]
    assert len(rows) == 1 and rows[0]["advice_id"] == BODY["advice_id"]


def test_dismiss_and_expand_map_to_lifecycle(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    for action, expected in (("dismissed", "dismissed"), ("expanded", "displayed")):
        body = {**BODY, "action": action}
        assert client.post("/api/v1/advice/action", json=body).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        types = {e["event_type"] for e in log.events()}
    assert types == {"dismissed", "displayed"}
    # dismiss mang reason_code typed (nguyên liệu cho cadence memory ĐA-04)
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        dis = [e for e in log.events() if e["event_type"] == "dismissed"]
    assert dis[0]["reason_code"] == "dismissed_for_window"
