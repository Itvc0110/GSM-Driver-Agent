import random
from datetime import datetime, timezone
from app.models import (
    MapContextResponse, DriverLocation, DemandZone,
    ChargingStation, AlertItem, DriverStateResponse, PayoutSummary,
    TripStepResponse
)

# Baseline center: Hanoi Center (Hoan Kiem / Ba Dinh, Hanoi)
BASE_LAT = 21.0285
BASE_LNG = 105.8542

# D-M3-17 (2026-08-01): trước đây file này tính tầm pin bằng `soc * 3.2` ⇒ 320 km ở SOC 100%,
# tức 5,1× giá trị của engine và vô lý với xe máy điện (dải tham chiếu Feliz S: 100–130 km).
# Endpoint dùng nó đã `deprecated` nhưng VẪN phục vụ được qua HTTP, nên số sai vẫn ra ngoài.
# Nay lấy hệ số từ CÙNG nguồn cấu hình mà engine dùng, và chọn mức thận trọng (tầm ngắn hơn) —
# xem `adapters/mockdata._range_band()` để biết vì sao không thể chọn theo đội pin.
def _km_per_soc_pct() -> float:
    """km đi được trên mỗi 1% SOC — mức THẬN TRỌNG, đọc từ `configs/pilot_dongda.yaml`."""
    from pathlib import Path as _P
    from gsm_sim.runner import Config
    root = _P(__file__).resolve().parents[3]
    veh = Config.load(str(root / "configs" / "pilot_dongda.yaml")).get("vehicle")
    return 1.0 / max(float(veh["swap_consume_pct_per_km"]),
                     float(veh["charge_consume_pct_per_km"]))

# Geo-fence bounding box for Hanoi
HANOI_BOUNDS = {
    "min_lat": 20.8000,
    "max_lat": 21.2500,
    "min_lng": 105.6000,
    "max_lng": 106.0500
}

# Synthetic Hanoi Trip Sequences for Fast-Forward Simulation
HANOI_TRIPS = [
    {
        "trip_id": "GSM_HN_9011",
        "customer_name": "Nguyễn Hoàng Nam",
        "customer_phone": "0988 123 456",
        "pickup_address": "Nhà hát Lớn Hà Nội, Tràng Tiền, Hoàn Kiếm",
        "dropoff_address": "Vincom Mega Mall Royal City, Nguyễn Trãi, Thanh Xuân",
        "payment_method": "Tiền mặt (Khuyến mại -20k)",
        "pickup_lat": 21.0243,
        "pickup_lng": 105.8576,
        "dropoff_lat": 21.0029,
        "dropoff_lng": 105.8152,
        "estimated_minutes": 18,
        "notes": "Khách mang theo 1 kiện hành lý nhỏ"
    },
    {
        "trip_id": "GSM_HN_9012",
        "customer_name": "Trần Thị Mai Anh",
        "customer_phone": "0912 654 321",
        "pickup_address": "Royal City R2, Thanh Xuân, Hà Nội",
        "dropoff_address": "Tháp Vincom Bà Triệu, Hai Bà Trưng",
        "payment_method": "Ví VinID",
        "pickup_lat": 21.0029,
        "pickup_lng": 105.8152,
        "dropoff_lat": 21.0118,
        "dropoff_lng": 105.8496,
        "estimated_minutes": 12,
        "notes": "Chờ khách ở sảnh chính R2"
    },
    {
        "trip_id": "GSM_HN_9013",
        "customer_name": "Lê Anh Tuấn",
        "customer_phone": "0977 888 999",
        "pickup_address": "Lotte Center Liễu Giai, Ba Đình",
        "dropoff_address": "KĐT Vinhomes Smart City, Tây Mỗ, Nam Từ Liêm",
        "payment_method": "Thẻ tín dụng (GSM Pay)",
        "pickup_lat": 21.0315,
        "pickup_lng": 105.8123,
        "dropoff_lat": 21.0062,
        "dropoff_lng": 105.7460,
        "estimated_minutes": 25,
        "notes": "Đi đường Đại lộ Thăng Long"
    }
]

def generate_synthetic_map_context(scenario_id: str = "default_hanoi", seed: int = 42) -> MapContextResponse:
    rng = random.Random(seed)
    
    # Driver location near Hanoi Center with small random offset
    driver_lat = BASE_LAT + rng.uniform(-0.005, 0.005)
    driver_lng = BASE_LNG + rng.uniform(-0.005, 0.005)
    
    # 5 Demand Zones around Hanoi
    demand_zones = []
    h3_placeholders = ["8865a00001fffff", "8865a00003fffff", "8865a00005fffff", "8865a00007fffff", "8865a00009fffff"]
    for i, h3_idx in enumerate(h3_placeholders):
        d_lat = driver_lat + rng.uniform(-0.015, 0.015)
        d_lng = driver_lng + rng.uniform(-0.015, 0.015)
        intensity = round(rng.uniform(0.4, 0.95), 2)
        demand_zones.append(DemandZone(
            h3_index=h3_idx,
            lat=d_lat,
            lng=d_lng,
            intensity=intensity,
            freshness_sec=rng.randint(10, 60)
        ))
    
    # 3 Charging Stations in Hanoi
    stations = [
        ChargingStation(
            id="st_hn_01",
            name="Trạm Sạc VinFast Vincom Bà Triệu (Hà Nội)",
            lat=21.0118,
            lng=105.8496,
            available_ports=4,
            total_ports=10,
            distance_km=0.8
        ),
        ChargingStation(
            id="st_hn_02",
            name="Trạm Sạc GSM Royal City (Thanh Xuân, Hà Nội)",
            lat=21.0029,
            lng=105.8152,
            available_ports=6,
            total_ports=16,
            distance_km=3.2
        ),
        ChargingStation(
            id="st_hn_03",
            name="Trạm Sạc VinFast Smart City (Nam Từ Liêm, Hà Nội)",
            lat=21.0062,
            lng=105.7460,
            available_ports=8,
            total_ports=24,
            distance_km=8.5
        )
    ]
    
    # Synthetic Alerts for Hanoi
    alerts = [
        AlertItem(
            id="alt_weather_hn_01",
            type="weather_rain",
            title="Cảnh báo mưa lớn Q. Hoàn Kiếm & Hai Bà Trưng (Hà Nội)",
            message="Mưa giông dồn dập trong 15 phút tới. Nhu cầu xe tăng cao ở khu vực Trung tâm Hà Nội.",
            severity="warning"
        ),
        AlertItem(
            id="alt_soc_hn_01",
            type="soc_warning",
            title="Dung lượng Pin SOC < 25%",
            message="Khuyến nghị di chuyển tới trạm sạc Vincom Bà Triệu (cách 0.8 km).",
            severity="critical"
        )
    ]
    
    return MapContextResponse(
        scenario_id=scenario_id,
        seed=seed,
        data_mode="synthetic",
        timestamp=datetime.now(timezone.utc).isoformat(),
        driver_location=DriverLocation(
            lat=driver_lat,
            lng=driver_lng,
            heading=rng.uniform(0, 360),
            speed_kmh=round(rng.uniform(15, 45), 1)
        ),
        demand_zones=demand_zones,
        charging_stations=stations,
        alerts=alerts
    )

def generate_synthetic_driver_state(scenario_id: str = "default_hanoi", seed: int = 42) -> DriverStateResponse:
    rng = random.Random(seed)
    soc = rng.randint(18, 85)
    range_km = round(soc * _km_per_soc_pct(), 1)   # D-M3-17: không còn hệ số bịa
    trips = rng.randint(6, 16)
    payout_val = trips * rng.randint(45000, 65000)
    
    return DriverStateResponse(
        driver_id="DRV_GSM_HN8899",
        driver_name="Nguyễn Văn Tài Xế (Hà Nội)",
        shift_status="ON_SHIFT",
        soc_percent=soc,
        vehicle_range_km=range_km,
        payout_summary=PayoutSummary(
            value=float(payout_val),
            currency="VND",
            trips_count=trips,
            scenario_id=scenario_id,
            seed=seed,
            data_mode="synthetic",
            is_mock=True
        )
    )

def generate_synthetic_trip_step(trip_index: int = 0, step: str = "INCOMING") -> TripStepResponse:
    trip_data = HANOI_TRIPS[trip_index % len(HANOI_TRIPS)]
    return TripStepResponse(
        trip_id=trip_data["trip_id"],
        customer_name=trip_data["customer_name"],
        customer_phone=trip_data["customer_phone"],
        pickup_address=trip_data["pickup_address"],
        dropoff_address=trip_data["dropoff_address"],
        fare_vnd=None,
        payment_method=trip_data["payment_method"],
        step=step,
        pickup_lat=trip_data["pickup_lat"],
        pickup_lng=trip_data["pickup_lng"],
        dropoff_lat=trip_data["dropoff_lat"],
        dropoff_lng=trip_data["dropoff_lng"],
        estimated_minutes=trip_data["estimated_minutes"],
        notes=trip_data["notes"]
    )
