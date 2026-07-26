import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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
