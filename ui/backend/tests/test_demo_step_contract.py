from __future__ import annotations

from types import SimpleNamespace


def _result():
    actor = SimpleNamespace(actor_id=7, archetype="P4", fleet=SimpleNamespace(value="swap"))
    order = SimpleNamespace(
        order_id=11, t_min=540.0, pickup_cell="pickup", drop_cell="drop",
        dist_km=3.2, gross_vnd=16_000, pickup_lat=21.03, pickup_lon=105.83,
        drop_lat=21.04, drop_lon=105.84,
    )
    events = [
        SimpleNamespace(t_min=500.0, actor_id=7, kind="go_online", cell="home", detail={}),
        SimpleNamespace(t_min=540.0, actor_id=7, kind="order_matched", cell="home",
                        detail={"order_id": 11}),
        SimpleNamespace(t_min=550.0, actor_id=7, kind="pickup", cell="pickup",
                        detail={"order_id": 11}),
    ]
    snapshots = []
    for index, (t_min, state, cell, lat, lon, soc, accepted) in enumerate([
        (500.0, "idle", "home", 21.01, 105.81, 80.0, 0),
        (540.0, "enroute", "home", 21.01, 105.81, 79.0, 1),
        (550.0, "on_trip", "pickup", 21.03, 105.83, 78.0, 1),
    ]):
        snapshots.append({
            "event_index": index, "t_min": t_min, "actor_id": 7, "state": state,
            "cell": cell, "lat": lat, "lon": lon, "soc_pct": soc,
            "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
            "orders_offered": int(accepted), "orders_accepted": int(accepted),
            "orders_completed": 0, "orders_cancelled": 0, "online_min": t_min - 500,
            "rest_min": 0.0, "charge_min": 0.0, "shift_start_min": 360.0,
            "shift_end_min": 1080.0,
        })
    return SimpleNamespace(
        run_id="run-1", seed=1000, actors=[actor], orders=[order], events=events,
        trace_snapshots=snapshots, advice_checkpoints=[], advice_artifacts=[],
        advice_checkpoint_events=[], segments=[{
            "segment_id": "seg-1", "actor_id": 7, "t0": 540.0, "t1": 550.0,
            "kind": "enroute", "order_id": 11, "from_lat": 21.01,
            "from_lon": 105.81, "to_lat": 21.03, "to_lon": 105.83,
        }],
    )


def _route(waypoints):
    return {
        "coords": [[p["lat"], p["lng"]] for p in waypoints],
        "total_dist_km": 1.7, "total_duration_min": 6,
        "source": "osrm_real_proxy", "route_is_real_road": True,
        "data_mode": "synthetic", "is_mock": True,
    }


def test_step_response_contains_canonical_driver_trip_map_and_route():
    from app.services.demo_session import DemoSessionService

    service = DemoSessionService(run_factory=lambda seed: _result(),
                                 session_id_factory=lambda: "s-1", route_factory=_route)
    service.create()
    service.select_actor("s-1", 7)
    service.advance("s-1", client_step_id="1", expected_step_version=0)
    step = service.advance("s-1", client_step_id="2", expected_step_version=1)

    assert {"simulation_time_min", "driver", "state_delta", "trip", "map", "routes",
            "advice", "timeline", "provenance"} <= set(step)
    assert step["trip"]["state"] == "MATCHED"
    assert step["driver"]["soc_pct"] == 79.0
    assert step["map"]["driver"]["lat"] == 21.01
    assert step["routes"][0]["leg"] == "driver_to_pickup"
    assert step["routes"][0]["route_id"].startswith("route-")
    assert step["advice"] == {"status": "silent", "reason_code": "no_checkpoint"}
    assert [item["kind"] for item in step["timeline"]] == ["go_online", "order_matched"]


def test_route_failure_is_a_fallback_and_does_not_fail_step():
    from app.services.demo_session import DemoSessionService

    def unavailable(_waypoints):
        raise TimeoutError("OSRM timeout")

    service = DemoSessionService(run_factory=lambda seed: _result(),
                                 session_id_factory=lambda: "s-2", route_factory=unavailable)
    service.create()
    service.select_actor("s-2", 7)
    service.advance("s-2", client_step_id="1", expected_step_version=0)
    step = service.advance("s-2", client_step_id="2", expected_step_version=1)

    assert step["routes"][0]["source"] == "fallback_straight_line"
    assert step["routes"][0]["route_is_real_road"] is False
    assert step["routes"][0]["is_mock"] is True
