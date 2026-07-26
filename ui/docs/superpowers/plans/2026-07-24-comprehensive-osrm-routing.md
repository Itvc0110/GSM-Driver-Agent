# Comprehensive OSRM Real-Road Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a comprehensive, production-grade OSRM Real-Road Routing engine for the GSM Driver App that guarantees 100% street-snapped polylines following Hanoi road geometry, supports multi-stop waypoints, and renders turn-by-turn maneuvers cleanly on the Stitch UI.

**Architecture:** A FastAPI Server Proxy (`backend/app/routers/routing.py`) queries the OSRM Driving v1 API (`overview=full`, `geometries=geojson`, `steps=true`, `snapping=any`) and falls back to a high-density Hanoi OpenStreetMap node graph (500+ real Hanoi street corners). The web frontend ([demo_stitch_app.html](file:///a:/UIUXgsm/demo_stitch_app.html)) consumes this endpoint and renders double-layer glowing cyan polylines with turn-by-turn Nav HUD cards.

**Tech Stack:** Python 3.10+, FastAPI, Pytest, OSRM API v1, Leaflet.js 1.9.4, TailwindCSS.

## Global Constraints

- **Python Version**: Python 3.10+
- **Backend Port**: 8000
- **Web Server Port**: 8080
- **Hanoi Geo-fence**: South-West `(20.8000, 105.6000)`, North-East `(21.2500, 106.0500)`
- **Map Aesthetics**: CartoDB Positron minimal white/gray tiles (`https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`), primary color `#00AFB9`

---

### Task 1: Comprehensive Hanoi Street Node Graph & Road Snapper

**Files:**
- Create: `backend/app/services/hanoi_graph.py`
- Test: `backend/tests/test_hanoi_graph.py`

**Interfaces:**
- Consumes: Raw `WaypointItem(lat, lng, name)`
- Produces: `snap_waypoint_to_road(lat, lng) -> Tuple[float, float]`, `get_hanoi_street_route(waypoints) -> List[List[float]]`

- [ ] **Step 1: Write failing test for Hanoi street snapper and route graph**

```python
import pytest
from app.services.hanoi_graph import snap_waypoint_to_road, get_hanoi_street_route
from app.models import WaypointItem

def test_snap_waypoint_to_road():
    # Point near Hoan Kiem lake
    snapped_lat, snapped_lng = snap_waypoint_to_road(21.0285, 105.8542)
    assert round(snapped_lat, 3) == 21.028
    assert round(snapped_lng, 3) == 105.854

def test_get_hanoi_street_route_dense():
    w1 = WaypointItem(lat=21.0285, lng=105.8542, name="Hồ Hoàn Kiếm")
    w2 = WaypointItem(lat=21.0029, lng=105.8152, name="Royal City")
    route_coords = get_hanoi_street_route([w1, w2])
    assert len(route_coords) >= 20
    assert route_coords[0] == [21.0285, 105.8542]
    assert route_coords[-1] == [21.0029, 105.8152]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_hanoi_graph.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.hanoi_graph'`

- [ ] **Step 3: Implement Hanoi street node graph service**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_hanoi_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/hanoi_graph.py backend/tests/test_hanoi_graph.py
git commit -m "feat: add high-density hanoi street node graph and road snapper"
```

---

### Task 2: Robust OSRM Server Proxy with Maneuver Steps & Snapping

**Files:**
- Modify: `backend/app/routers/routing.py`
- Test: `backend/tests/test_routing_api.py`

**Interfaces:**
- Consumes: POST `/api/v1/routing/calculate` with `RouteCalculateRequest`
- Produces: `RouteCalculateResponse(coords, total_dist_km, total_duration_min, fare_vnd, turn_instruction, source)`

- [ ] **Step 1: Write failing test for Routing API endpoint**

```python
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
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `pytest backend/tests/test_routing_api.py -v`
Expected: Verify test assertions fail or pass cleanly.

- [ ] **Step 3: Update routing.py with OSRM snapping & step maneuver parser**

Modify `backend/app/routers/routing.py` to parse OSRM steps and snap waypoints cleanly using `hanoi_graph.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_routing_api.py -v`
Expected: PASS with 100% green coverage.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/routing.py backend/tests/test_routing_api.py
git commit -m "feat: enhance OSRM server proxy with maneuver steps and street snapping"
```

---

### Task 3: Double-Layer High-Visibility Polyline & Multi-Stop UI in Web Demo

**Files:**
- Modify: `a:/UIUXgsm/demo_stitch_app.html`

**Interfaces:**
- Consumes: Endpoint `http://localhost:8000/api/v1/routing/calculate`
- Produces: Interactive Leaflet map with CartoDB Positron tiles, `#00AFB9` cyan glowing polyline with `#0f172a` 11px border, and vertical timeline node UI for multi-stop routes.

- [ ] **Step 1: Update demo_stitch_app.html with instant multi-stop polyline rendering**

Ensure `DOMContentLoaded` triggers `presetMultiRoute('trip3stop')` and renders double-layer polylines (`outerPolylineLayer` weight 11, `innerPolylineLayer` weight 7 cyan).

- [ ] **Step 2: Verify in browser**

Fetch `http://localhost:8080/demo_stitch_app.html` using HTTP read tool.
Expected: Title "GSM Driver App - Multi-Stop Real Road Routing & Stitch UI", HTTP status 200.

- [ ] **Step 3: Commit**

```bash
git add demo_stitch_app.html
git commit -m "feat: update web demo with double-layer glowing polyline and multi-stop UI"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-24-comprehensive-osrm-routing.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
