from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class DriverLocation(BaseModel):
    lat: float
    lng: float
    heading: float = 0.0
    speed_kmh: float = 0.0

class DemandZone(BaseModel):
    h3_index: str
    lat: float
    lng: float
    intensity: float
    freshness_sec: int = 30

class ChargingStation(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    available_ports: int
    total_ports: int
    distance_km: float

class AlertItem(BaseModel):
    id: str
    type: str
    title: str
    message: str
    severity: str

class MapContextResponse(BaseModel):
    scenario_id: str
    seed: int
    data_mode: str = "synthetic"
    timestamp: str
    driver_location: DriverLocation
    demand_zones: List[DemandZone]
    charging_stations: List[ChargingStation]
    alerts: List[AlertItem]

class PayoutSummary(BaseModel):
    value: float
    currency: str = "VND"
    trips_count: int
    scenario_id: str
    seed: int
    data_mode: str = "synthetic"
    is_mock: bool = True

class DriverStateResponse(BaseModel):
    driver_id: str
    driver_name: str
    shift_status: str
    soc_percent: int
    vehicle_range_km: float
    payout_summary: PayoutSummary

class TripStepResponse(BaseModel):
    trip_id: str
    customer_name: str
    customer_phone: str
    pickup_address: str
    dropoff_address: str
    # Giá hợp lệ cần route distance; endpoint lifecycle chỉ trả metadata nên để null.
    fare_vnd: Optional[int] = None
    payment_method: str
    step: str  # SEARCHING, INCOMING, PICKING_UP, IN_PROGRESS, COMPLETED
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    estimated_minutes: int
    notes: Optional[str] = None

class WaypointItem(BaseModel):
    lat: float
    lng: float
    name: Optional[str] = None

class RouteCalculateRequest(BaseModel):
    waypoints: List[WaypointItem]

class RouteCalculateResponse(BaseModel):
    coords: List[List[float]]  # Array of [lat, lng]
    total_dist_km: float
    total_duration_min: int
    fare_vnd: int  # gross fare từ sim-policy, giữ tên field để tương thích client cũ
    driver_payout_vnd: int  # payout cuốc, chưa gồm bonus
    driver_share: float
    fare_policy_version: str
    data_mode: Literal["synthetic"] = "synthetic"
    is_mock: bool = True
    turn_instruction: str
    source: str = "osrm_real_proxy"
    route_is_real_road: bool  # True: OSRM/GraphHopper bám đường thật. False: ước lượng đường thẳng.

