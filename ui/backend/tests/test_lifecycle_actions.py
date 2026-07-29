"""ĐA-05 Cycle W — POST /advice/action ghi store canonical (AdviceEventLog).

Ngữ nghĩa mới đáng test nhất: double-click cùng nút trong CÙNG GIÂY quan sát = MỘT
event (F-3: khoá theo `at_min` từng cho cửa sổ dedupe CẢ NGÀY vì frontend gửi at_min
là hằng số theo loại card — 'Làm theo → Bỏ qua → Làm theo lại' bị nuốt); JSONL vẫn
append đủ (debug export, không canonical).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.routers import advice as advice_router
from gsm_core.lifecycle.event_log import AdviceEventLog

client = TestClient(app)

BODY = {"advice_id": "s1-driver-01-2026-07-29-840", "driver_id": "driver-01",
        "date": "2026-07-29", "action": "followed", "card_kind": "brief",
        "at_min": 840}


class _FrozenDatetime(datetime):
    """F-S8: idempotency khoá theo GIÂY — hai POST thật có thể vắt qua ranh giới giây
    ⇒ test flaky. Đóng băng đồng hồ để test khẳng định đúng ngữ nghĩa, không may rủi."""

    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 29, 14, 0, 7, tzinfo=tz or timezone.utc)


def _patch(tmp_path, monkeypatch, freeze: bool = False):
    monkeypatch.setattr(advice_router, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_router, "ACTIONS_FILE", tmp_path / "a.jsonl")
    if freeze:
        monkeypatch.setattr(advice_router, "datetime", _FrozenDatetime)


def test_double_click_is_one_lifecycle_event(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch, freeze=True)
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        evs = log.events(decision_id=BODY["advice_id"])
    assert len(evs) == 1, "double-click cùng GIÂY phải là MỘT event (INSERT OR IGNORE)"
    assert evs[0]["event_type"] == "followed" and evs[0]["origin"] == "ui"
    # JSONL debug export vẫn ghi đủ 2 dòng (không phải store canonical)
    assert len((tmp_path / "a.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    # GET đọc từ store canonical ⇒ 1 hàng
    rows = client.get("/api/v1/advice/actions").json()["actions"]
    assert len(rows) == 1 and rows[0]["advice_id"] == BODY["advice_id"]


def test_calendar_invalid_date_rejected_422(tmp_path, monkeypatch):
    """X-1 (batch 2): `2026-02-31` qua regex `\\d{2}` nhưng không tồn tại trên lịch —
    trước sửa: HTTP 200, record độc persist VĨNH VIỄN (store append-only) rồi giết mọi
    decision_state về sau. Router phải chặn 422 TRƯỚC store."""
    _patch(tmp_path, monkeypatch)
    for bad in ("2026-02-31", "2026-13-01", "2026-00-10"):
        r = client.post("/api/v1/advice/action", json={**BODY, "date": bad})
        assert r.status_code == 422, (bad, r.status_code)
    assert not (tmp_path / "advice_lifecycle.db").exists() or not AdviceEventLog(
        tmp_path / "advice_lifecycle.db").events()
    assert not (tmp_path / "a.jsonl").exists(), "JSONL cũng không được ghi (F-8)"


def test_empty_ids_rejected_422(tmp_path, monkeypatch):
    """X-6: advice_id/driver_id rỗng từng đi xuyên tới store rồi nổ HTTP 500 —
    boundary validate phải đối xứng (422 tại pydantic như date/at_min)."""
    _patch(tmp_path, monkeypatch)
    assert client.post("/api/v1/advice/action",
                       json={**BODY, "advice_id": ""}).status_code == 422
    assert client.post("/api/v1/advice/action",
                       json={**BODY, "driver_id": ""}).status_code == 422


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
