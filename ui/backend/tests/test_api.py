from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# U2 (UPDATE-061): gateway v2 — "/" redirect sang web app; map-context mặc định đọc
# mock-realdata, đường synthetic của Khánh giữ qua scenario_id="synthetic".

def test_read_root_redirects_to_webapp():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app/"

def test_get_map_context_synthetic_path_kept():
    response = client.get("/api/v1/map-context?scenario_id=synthetic&seed=100")
    assert response.status_code == 200
    data = response.json()
    assert data["data_mode"] == "synthetic"
    assert len(data["demand_zones"]) > 0
    assert len(data["charging_stations"]) > 0

def test_get_map_context_default_is_mock_realdata():
    response = client.get("/api/v1/map-context?hour=18")
    assert response.status_code == 200
    data = response.json()
    assert data["data_mode"] == "mock-realdata"
    assert len(data["charging_stations"]) > 0

def test_get_driver_state():
    response = client.get("/api/v1/driver/state?scenario_id=test_scenario&seed=100")
    assert response.status_code == 200
    data = response.json()
    assert data["shift_status"] == "ON_SHIFT"
    assert data["payout_summary"]["is_mock"] is True


def test_trip_step_requires_route_quote_instead_of_static_fare():
    """Fare tĩnh của ba trip demo từng mâu thuẫn với Simulator policy."""
    response = client.get("/api/v1/trip/step?trip_index=0&step=INCOMING")
    assert response.status_code == 200
    assert response.json()["fare_vnd"] is None


def test_demo_endpoints_do_not_mutate_driver_money():
    """Quote/lifecycle demo không được ghi vào ledger ngày của tài xế."""
    state_url = "/api/v1/driver/state-synthetic?scenario_id=ledger-check&seed=91"
    before = client.get(state_url).json()["payout_summary"]
    assert client.get("/api/v1/trip/step?trip_index=1&step=COMPLETED").status_code == 200
    after = client.get(state_url).json()["payout_summary"]
    assert after == before
