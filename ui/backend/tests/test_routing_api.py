import json

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers import routing

client = TestClient(app)


class _OsrmResponse:
    status = 200

    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _osrm_payload(distance_m: float = 3500.0) -> dict:
    return {
        "routes": [{
            "distance": distance_m,
            "duration": 600.0,
            "geometry": {"coordinates": [[105.8542, 21.0285], [105.8152, 21.0029]]},
            "legs": [{"steps": [
                {"maneuver": {"instruction": "Đi thẳng"}, "name": "Phố A"},
                {"maneuver": {"instruction": "Rẽ phải"}, "name": "Phố B"},
            ]}],
        }],
    }

def test_routing_calculate_multistop():
    payload = {
        "waypoints": [
            {"lat": 21.0285, "lng": 105.8542, "name": "Hồ Hoàn Kiếm"},
            {"lat": 21.0118, "lng": 105.8496, "name": "Trạm sạc Vincom Bà Triệu"},
            {"lat": 21.0029, "lng": 105.8152, "name": "Royal City"}
        ]
    }
    response = client.post("/api/v1/routing/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "coords" in data
    assert len(data["coords"]) >= 20
    assert data["total_dist_km"] > 0
    assert data["fare_vnd"] > 0
    assert "source" in data


def test_osrm_route_uses_simulator_policy_quote(monkeypatch):
    """Bắt lỗi cũ `distance * 24_000`: 3,5 km phải dùng sim-policy-v0."""
    monkeypatch.setattr(
        routing.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _OsrmResponse(_osrm_payload()),
    )
    response = client.post("/api/v1/routing/calculate", json={
        "waypoints": [
            {"lat": 21.0285, "lng": 105.8542, "name": "A"},
            {"lat": 21.0029, "lng": 105.8152, "name": "B"},
        ],
    })

    assert response.status_code == 200
    data = response.json()
    assert data["total_dist_km"] == 3.5
    assert data["fare_vnd"] == 19_450
    assert data["driver_payout_vnd"] == 14_588
    assert data["driver_share"] == 0.75
    assert data["fare_policy_version"] == "sim-policy-v0"
    assert data["data_mode"] == "synthetic"
    assert data["is_mock"] is True


def test_fallback_route_uses_same_base_fare(monkeypatch):
    """Bắt nhánh fallback còn dùng 24k/km; route 0 km vẫn phải có base fare."""
    def _offline(*_args, **_kwargs):
        raise OSError("offline fixture")

    monkeypatch.setattr(routing.urllib.request, "urlopen", _offline)
    point = {"lat": 21.0285, "lng": 105.8542, "name": "A"}
    response = client.post("/api/v1/routing/calculate", json={"waypoints": [point, point]})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "hanoi_street_graph_engine"
    assert data["total_dist_km"] == 0.0
    assert data["fare_vnd"] == 13_000
    assert data["driver_payout_vnd"] == 9_750
    assert data["fare_policy_version"] == "sim-policy-v0"
