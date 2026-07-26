import math
from typing import List, Tuple
from app.models import WaypointItem

# High-density Hanoi street intersections graph
HANOI_STREET_NODES = [
    [21.0285, 105.8542], # Hồ Hoàn Kiếm (Tràng Tiền)
    [21.0235, 105.8570], # Ngã tư Tràng Tiền - Lê Thánh Tông
    [21.0220, 105.8558], # Phan Chu Trinh
    [21.0205, 105.8540], # Trần Hưng Đạo
    [21.0195, 105.8522], # Đầu Phố Bà Triệu
    [21.0160, 105.8512], # Bà Triệu - Lý Thường Kiệt
    [21.0130, 105.8502], # Bà Triệu - Trần Nhân Tông
    [21.0118, 105.8496], # Vincom Bà Triệu
    [21.0090, 105.8488], # Ngã tư Bà Triệu - Đại Cồ Việt
    [21.0085, 105.8440], # Phố Đại Cồ Việt
    [21.0092, 105.8380], # Hầm Kim Liên - Xã Đàn
    [21.0110, 105.8320], # Phố Xã Đàn
    [21.0125, 105.8280], # Ô Chợ Dừa
    [21.0110, 105.8250], # Phố Nguyễn Lương Bằng
    [21.0080, 105.8230], # Gò Đống Đa
    [21.0050, 105.8210], # Phố Tây Sơn
    [21.0035, 105.8190], # Ngã Tư Sở
    [21.0029, 105.8152]  # Royal City Nguyễn Trãi
]

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def snap_waypoint_to_road(lat: float, lng: float) -> Tuple[float, float]:
    min_dist = float('inf')
    best_node = (lat, lng)
    for node in HANOI_STREET_NODES:
        dist = haversine(lat, lng, node[0], node[1])
        if dist < min_dist:
            min_dist = dist
            best_node = (node[0], node[1])
    return best_node if min_dist < 0.5 else (lat, lng)

def get_hanoi_street_route(waypoints: List[WaypointItem]) -> List[List[float]]:
    if not waypoints or len(waypoints) < 2:
        return []
    coords = []
    for i in range(len(waypoints) - 1):
        p1 = waypoints[i]
        p2 = waypoints[i + 1]
        steps = 20
        for k in range(steps + 1):
            t = k / steps
            curve_lat = math.sin(t * math.pi) * 0.002
            curve_lng = math.cos(t * math.pi) * 0.0015
            lat = round(p1.lat + (p2.lat - p1.lat) * t + curve_lat, 6)
            lng = round(p1.lng + (p2.lng - p1.lng) * t + curve_lng, 6)
            coords.append([lat, lng])
    return coords
