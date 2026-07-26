import pytest
from app.services.hanoi_graph import snap_waypoint_to_road, get_hanoi_street_route
from app.models import WaypointItem

def test_snap_waypoint_to_road():
    snapped_lat, snapped_lng = snap_waypoint_to_road(21.0285, 105.8542)
    assert round(snapped_lat, 3) == 21.029
    assert round(snapped_lng, 3) == 105.854

def test_get_hanoi_street_route_dense():
    w1 = WaypointItem(lat=21.0285, lng=105.8542, name="Hồ Hoàn Kiếm")
    w2 = WaypointItem(lat=21.0029, lng=105.8152, name="Royal City")
    route_coords = get_hanoi_street_route([w1, w2])
    assert len(route_coords) >= 20
    assert route_coords[0][0] == 21.0285
    assert route_coords[-1][0] == 21.0029

