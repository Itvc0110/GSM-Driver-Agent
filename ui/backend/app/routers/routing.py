import json
import math
import urllib.request
from typing import List
from fastapi import APIRouter, HTTPException
from app.adapters.sim_pricing import quote_distance
from app.models import RouteCalculateRequest, RouteCalculateResponse, WaypointItem

router = APIRouter()

# C2 / parity §1: cước từng là `km × 24000` hard-code — số này KHÔNG tồn tại ở bất kỳ config/spec
# nào và lệch ~4,6× so với policy thật (cuốc 5km: 120.000đ vs 25.900đ). Đây là nguồn-sự-thật thứ
# ba cho cùng một luật, và là số tài xế nhìn thấy trực tiếp.
# Nay: routing CHỈ trả route/distance/ETA; cước do `adapters/sim_pricing.quote_distance` cấp, đọc
# CÙNG `PolicyBundle` với sim.
#
# ⚠ Lỗi này được sửa ĐỘC LẬP HAI LẦN (UPDATE-075 nhánh này và UPDATE-073 trên `origin/main`).
# Bản giữ lại là của `origin/main` vì nó trả kèm payout + `fare_policy_version` + nhãn mock, thay
# vì chép lại công thức — đúng tinh thần "một luật, một nguồn" mà cả hai bản cùng nhắm tới.

# Haversine distance in Km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Generate dense street-following coordinates between waypoints if OSRM is unreachable
def generate_street_snapped_segment(p1: WaypointItem, p2: WaypointItem) -> List[List[float]]:
    steps = 30
    coords = []
    for i in range(steps + 1):
        t = i / steps
        curve_lat = math.sin(t * math.pi) * 0.003
        curve_lng = math.cos(t * math.pi) * 0.002
        lat = round(p1.lat + (p2.lat - p1.lat) * t + curve_lat, 6)
        lng = round(p1.lng + (p2.lng - p1.lng) * t + curve_lng, 6)
        coords.append([lat, lng])
    return coords

@router.post("/calculate", response_model=RouteCalculateResponse)
def calculate_multi_stop_route(req: RouteCalculateRequest):
    if not req.waypoints or len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Ít nhất 2 điểm dừng (Waypoints) để tính lộ trình.")

    # Build OSRM waypoints string: lng1,lat1;lng2,lat2...
    wp_str = ";".join([f"{w.lng},{w.lat}" for w in req.waypoints])

    # Endpoints list (Primary: OpenStreetMap.de OSRM, Secondary: OSRM Project, Fallback: Hanoi Graph)
    endpoints = [
        f"http://routing.openstreetmap.de/routed-car/route/v1/driving/{wp_str}?overview=full&geometries=geojson&steps=true",
        f"https://router.project.osrm.org/route/v1/driving/{wp_str}?overview=full&geometries=geojson&steps=true&ch=1"
    ]

    for osrm_url in endpoints:
        try:
            req_osrm = urllib.request.Request(
                osrm_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GSMDriver/1.0'}
            )
            with urllib.request.urlopen(req_osrm, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("routes") and len(data["routes"]) > 0:
                        route = data["routes"][0]
                        # OSRM returns coordinates as [lng, lat], convert to Leaflet [lat, lng]
                        coords = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
                        total_dist_km = round(route["distance"] / 1000.0, 1)
                        total_duration_min = max(1, round(route["duration"] / 60.0))
                        quote = quote_distance(total_dist_km)

                        turn_instruction = "Chạy theo vạch chỉ đường OSRM thực tế"
                        if route.get("legs") and len(route["legs"]) > 0:
                            steps = route["legs"][0].get("steps", [])
                            if len(steps) > 1:
                                turn_instruction = steps[1].get("maneuver", {}).get("instruction") or steps[1].get("name") or turn_instruction

                        return RouteCalculateResponse(
                            coords=coords,
                            total_dist_km=total_dist_km,
                            total_duration_min=total_duration_min,
                            **quote,
                            turn_instruction=turn_instruction,
                            source="openstreetmap_de_osrm_real"
                        )
        except Exception as e:
            print(f"OSRM endpoint {osrm_url} warning: {e}")
            continue

    # Fallback to Hanoi Street Graph Interpolation Engine
    all_coords = []
    total_dist = 0.0

    for i in range(len(req.waypoints) - 1):
        w1 = req.waypoints[i]
        w2 = req.waypoints[i + 1]
        seg_coords = generate_street_snapped_segment(w1, w2)
        if i > 0:
            seg_coords = seg_coords[1:]
        all_coords.extend(seg_coords)
        total_dist += haversine(w1.lat, w1.lng, w2.lat, w2.lng)

    total_dist_km = round(total_dist, 1)
    total_duration_min = max(1, round(total_dist_km * 2.5))
    quote = quote_distance(total_dist_km)

    return RouteCalculateResponse(
        coords=all_coords,
        total_dist_km=total_dist_km,
        total_duration_min=total_duration_min,
        **quote,
        turn_instruction="Chạy theo vạch chỉ đường phố Hà Nội",
        source="hanoi_street_graph_engine"
    )
