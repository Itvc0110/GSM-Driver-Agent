"""Contract tests — response của backend PHẢI khớp JSON Schema trong ui/contracts/.

Đây là điểm đồng bộ web ↔ Flutter (contract-first): schema đỏ = một trong hai UI
sẽ vỡ ở runtime. Chạy: uv run pytest ui/backend/tests -q (cần extra `ui`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import validate

from app.main import app

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"
client = TestClient(app)


def _schema(name: str) -> dict:
    return json.loads((CONTRACTS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dv() -> dict:
    r = client.get("/api/v1/driver/default-view")
    assert r.status_code == 200
    return r.json()


def test_driver_state_matches_contract(dv):
    r = client.get(f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}")
    assert r.status_code == 200
    body = r.json()
    validate(body, _schema("driver_state"))
    # ranh giới tiền (CLAUDE §5): payout PHẢI bằng tổng breakdown — không rò tiền
    m = body["money"]
    assert m["payout_vnd"] == sum(m["payout_breakdown"].values())
    assert m["gross_vnd"] >= m["payout_breakdown"]["trip_payout_vnd"]
    assert m["est_net_vnd"] is None, "est_net chỉ được có số khi đủ known costs"


def test_map_context_matches_contract(dv):
    r = client.get(f"/api/v1/map-context?date={dv['date']}&hour=18")
    assert r.status_code == 200
    validate(r.json(), _schema("map_context"))


def test_advice_matches_contract_all_hours(dv):
    for now_min in (9 * 60, 14 * 60, 21 * 60 + 30):
        r = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}&now_min={now_min}")
        assert r.status_code == 200
        body = r.json()
        validate(body, _schema("advice"))
        # im lặng và có-items phải loại trừ nhau
        assert body["silent"]["is_silent"] == (len(body["items"]) == 0)


def test_advice_car_fleet_is_silent_not_wrong(dv):
    """Đội car không có policy bike — advisor phải IM LẶNG chứ không áp bừa số."""
    r = client.get(f"/api/v1/advice?driver_id=cp-0&date={dv['date']}&now_min=840")
    body = r.json()
    validate(body, _schema("advice"))
    assert body["silent"]["is_silent"] and body["silent"]["reason_code"] == "no_active_channel"


def test_state_deterministic(dv):
    """Cùng driver/ngày → byte-identical (không random trong adapter)."""
    url = f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}"
    assert client.get(url).content == client.get(url).content


def test_history_days_bounded(dv):
    r = client.get(f"/api/v1/driver/history?driver_id={dv['driver_id']}&date={dv['date']}&days=14")
    body = r.json()
    assert 1 <= len(body["days"]) <= 14
    assert body["days"][-1]["date"] == dv["date"]
    assert all(d["payout_vnd"] <= d["gross_vnd"] for d in body["days"])
