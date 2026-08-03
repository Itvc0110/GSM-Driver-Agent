import json
import math
import os
import urllib.parse
import urllib.request
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.adapters.sim_pricing import quote_distance
from app.models import RouteCalculateRequest, RouteCalculateResponse, WaypointItem
from gsm_core.advisor.llm_client import load_env

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
#
# UPDATE-120: 3 tier rõ ràng — OSRM public (thật) → GraphHopper (thật, cần GRAPHHOPPER_API_KEY) →
# ước lượng đường thẳng (KHÔNG còn fake sine-curve giả làm "hanoi_street_graph_engine" — tên đó
# ngụ ý một đồ thị đường phố thật không hề tồn tại). Mọi tier trả cùng field `route_is_real_road`
# để frontend phân biệt trung thực, không phải suy đoán qua chuỗi `source`.

load_env()

_HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GSMDriver/1.0'}


# Haversine distance in Km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_route_response(coords, total_dist_km, total_duration_min, turn_instruction,
                          source, route_is_real_road) -> RouteCalculateResponse:
    quote = quote_distance(total_dist_km)
    return RouteCalculateResponse(
        coords=coords,
        total_dist_km=total_dist_km,
        total_duration_min=total_duration_min,
        **quote,
        turn_instruction=turn_instruction,
        source=source,
        route_is_real_road=route_is_real_road,
    )


DEFAULT_OSRM_BASE_URL = "https://router.project-osrm.org"
# Mirror thứ nhất: FOSSGIS routed-car. KHÔNG cấu hình được qua env vì nó có đường dẫn khác
# (`/routed-car/route/v1/...`), không phải một base URL thả vào là chạy.
OSRM_DE_BASE_URL = "http://routing.openstreetmap.de/routed-car"


def osrm_endpoints(wp_str: str) -> List[str]:
    """Danh sách mirror OSRM sẽ thử, theo thứ tự.

    Hai thứ được sửa ở đây (kiểm bằng gọi thật 2026-08-03, UPDATE-128):

    1. **`OSRM_BASE_URL` trước đây KHÔNG ai đọc ở đường runtime.** `.env`/`.env.example` mô tả nó
       như tầng 1 của routing, nhưng file này viết cứng host ⇒ Cường sửa biến thì hành vi endpoint
       không đổi. Đúng họ *"cấu hình khai báo nhưng không có đường chạy"* mà repo đã trả giá 4 lần
       (`D-R12` · UPDATE-114 lỗ (a) · `D-M3-13` · `D-M3-15`). Nay biến có người đọc thật.
    2. **Mirror thứ hai viết SAI tên miền**: `router.project.osrm.org` (dấu chấm) thay vì
       `router.project-osrm.org` (gạch ngang). Nó phân giải được sang một IP khác nên trông như
       host thật, nhưng TLS trả `CERTIFICATE_VERIFY_FAILED: Hostname mismatch` ⇒ mirror này
       **chưa từng chạy được lần nào**. Suite cũ không bắt vì test monkeypatch `urlopen`, nên tên
       miền không bao giờ bị phân giải thật.

    ⚠ Điều đáng biết khi rate limit: `router.project-osrm.org` và `routing.openstreetmap.de`
    **cùng phân giải về `5.148.170.168`** (cùng hạ tầng FOSSGIS) ⇒ hai mirror này KHÔNG cho thêm
    hạn mức. Thứ thật sự đỡ rate limit là tầng 2 (GraphHopper) và cache, không phải đổi mirror.
    """
    base = os.environ.get("OSRM_BASE_URL", "").strip().rstrip("/") or DEFAULT_OSRM_BASE_URL
    qs = "overview=full&geometries=geojson&steps=true"
    urls = [f"{OSRM_DE_BASE_URL}/route/v1/driving/{wp_str}?{qs}",
            f"{base}/route/v1/driving/{wp_str}?{qs}"]
    # cùng một base cấu hình trùng mirror mặc định ⇒ đừng gọi hai lần cho một server
    return list(dict.fromkeys(urls))


_OSRM_HOST_SOURCE = {
    "routing.openstreetmap.de": "openstreetmap_de_osrm_real",
    "router.project-osrm.org": "project_osrm_real",
}


def _osrm_source(url: str) -> str:
    """Nhãn nguồn suy từ **HOST thật** của URL đã trả lời, không từ so chuỗi.

    Bản đầu của UPDATE-128 làm `"openstreetmap_de_osrm_real" if OSRM_DE_BASE_URL in osrm_url else
    "project_osrm_real"` — so CHUỖI CÓ SCHEME. Soi độc lập 2026-08-03 tái lập được: đặt
    `OSRM_BASE_URL=https://routing.openstreetmap.de/routed-car` (https, mirror A viết cứng là
    http) ⇒ dữ liệu đến TỪ openstreetmap.de mà nhãn nói `project_osrm_real`. Và self-host
    (`http://localhost:5000`) bị khẳng định là project-OSRM.

    Nhãn là **dữ liệu**, không phải chú thích — nói sai xuất xứ chính là họ lỗi
    `hanoi_street_graph_engine` mà `UPDATE-120` vừa dọn ở tầng 3. Nên host lạ trả
    `osrm_custom_real`: vẫn khai **đây là OSRM thật**, nhưng KHÔNG khẳng định của ai.
    """
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return _OSRM_HOST_SOURCE.get(host, "osrm_custom_real")


def try_osrm(req: RouteCalculateRequest) -> Optional[RouteCalculateResponse]:
    # Build OSRM waypoints string: lng1,lat1;lng2,lat2...
    wp_str = ";".join([f"{w.lng},{w.lat}" for w in req.waypoints])

    for osrm_url in osrm_endpoints(wp_str):
        try:
            req_osrm = urllib.request.Request(osrm_url, headers=_HTTP_HEADERS)
            with urllib.request.urlopen(req_osrm, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("routes") and len(data["routes"]) > 0:
                        route = data["routes"][0]
                        # OSRM returns coordinates as [lng, lat], convert to Leaflet [lat, lng]
                        coords = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
                        total_dist_km = round(route["distance"] / 1000.0, 1)
                        total_duration_min = max(1, round(route["duration"] / 60.0))

                        turn_instruction = "Chạy theo vạch chỉ đường OSRM thực tế"
                        if route.get("legs") and len(route["legs"]) > 0:
                            steps = route["legs"][0].get("steps", [])
                            if len(steps) > 1:
                                turn_instruction = steps[1].get("maneuver", {}).get("instruction") or steps[1].get("name") or turn_instruction

                        return build_route_response(coords, total_dist_km, total_duration_min,
                                                     turn_instruction, _osrm_source(osrm_url),
                                                     True)
        except Exception as e:
            print(f"OSRM endpoint {osrm_url} warning: {e}")
            continue
    return None


def try_graphhopper(req: RouteCalculateRequest) -> Optional[RouteCalculateResponse]:
    api_key = os.environ.get("GRAPHHOPPER_API_KEY", "").strip()
    if not api_key:
        return None

    # GraphHopper `point` là lat,lon (NGƯỢC thứ tự lng,lat của OSRM ở try_osrm) — lặp lại theo
    # từng waypoint, hỗ trợ N≥2 điểm trong 1 request.
    params = [("point", f"{w.lat},{w.lng}") for w in req.waypoints]
    params += [
        ("profile", "car"), ("locale", "vi"),
        ("instructions", "true"), ("calc_points", "true"), ("points_encoded", "false"),
        ("key", api_key),
    ]
    url = "https://graphhopper.com/api/1/route?" + urllib.parse.urlencode(params)

    try:
        gh_req = urllib.request.Request(url, headers=_HTTP_HEADERS)
        with urllib.request.urlopen(gh_req, timeout=5) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        # KHÔNG log url/e.url — key nằm trong query string
        print(f"GraphHopper routing warning: {type(e).__name__}")
        return None

    paths = data.get("paths")
    if not paths:
        return None
    path = paths[0]
    # GraphHopper geometry cũng [lon,lat] (GeoJSON) — swap giống hệt OSRM ở trên
    coords = [[c[1], c[0]] for c in path["points"]["coordinates"]]
    total_dist_km = round(path["distance"] / 1000.0, 1)
    # `time` của GraphHopper là MILI-giây (khác `duration` giây của OSRM)
    total_duration_min = max(1, round(path["time"] / 60000.0))

    turn_instruction = "Chạy theo tuyến đường GraphHopper thực tế"
    instructions = path.get("instructions") or []
    if len(instructions) > 1:
        turn_instruction = instructions[1].get("text") or turn_instruction

    return build_route_response(coords, total_dist_km, total_duration_min,
                                 turn_instruction, "graphhopper_real", True)


def interpolate_straight_line_segment(p1: WaypointItem, p2: WaypointItem) -> List[List[float]]:
    steps = 30
    coords = []
    for i in range(steps + 1):
        t = i / steps
        lat = round(p1.lat + (p2.lat - p1.lat) * t, 6)
        lng = round(p1.lng + (p2.lng - p1.lng) * t, 6)
        coords.append([lat, lng])
    return coords


def straight_line_fallback(req: RouteCalculateRequest) -> RouteCalculateResponse:
    all_coords = []
    total_dist = 0.0

    for i in range(len(req.waypoints) - 1):
        w1 = req.waypoints[i]
        w2 = req.waypoints[i + 1]
        seg_coords = interpolate_straight_line_segment(w1, w2)
        if i > 0:
            seg_coords = seg_coords[1:]
        all_coords.extend(seg_coords)
        total_dist += haversine(w1.lat, w1.lng, w2.lat, w2.lng)

    total_dist_km = round(total_dist, 1)
    total_duration_min = max(1, round(total_dist_km * 2.5))

    return build_route_response(
        all_coords, total_dist_km, total_duration_min,
        "Ước lượng đường thẳng — không dựa trên dữ liệu đường phố thực",
        "fallback_straight_line_estimate", False,
    )


@router.post("/calculate", response_model=RouteCalculateResponse)
def calculate_multi_stop_route(req: RouteCalculateRequest):
    if not req.waypoints or len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Ít nhất 2 điểm dừng (Waypoints) để tính lộ trình.")

    result = try_osrm(req)
    if result is None:
        result = try_graphhopper(req)
    if result is None:
        result = straight_line_fallback(req)
    return result
