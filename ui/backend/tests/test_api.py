from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_map_context():
    response = client.get("/api/v1/map-context?scenario_id=test_scenario&seed=100")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "test_scenario"
    assert data["seed"] == 100
    assert data["data_mode"] == "synthetic"
    assert len(data["demand_zones"]) > 0
    assert len(data["charging_stations"]) > 0

def test_get_driver_state():
    response = client.get("/api/v1/driver/state?scenario_id=test_scenario&seed=100")
    assert response.status_code == 200
    data = response.json()
    assert data["shift_status"] == "ON_SHIFT"
    assert data["payout_summary"]["is_mock"] is True
