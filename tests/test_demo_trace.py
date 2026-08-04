from __future__ import annotations

from types import SimpleNamespace


def test_run_result_accepts_canonical_run_id():
    from gsm_sim.runner import RunResult

    result = RunResult(
        run_id="run-1", seed=1000, events=[], actors=[], orders=[],
        config=object(), policy=object(), grid=object(),
    )

    assert result.run_id == "run-1"


def _actor(**overrides):
    values = {
        "actor_id": 7,
        "archetype": "P4",
        "fleet": SimpleNamespace(value="swap"),
        "state": SimpleNamespace(value="idle"),
        "cell": "892ab13a677ffff",
        "lat": 21.02,
        "lon": 105.82,
        "soc_pct": 42.5,
        "payout_vnd": 12_000,
        "gross_vnd": 16_000,
        "points": 18,
        "trips_done": 1,
        "orders_offered": 2,
        "orders_accepted": 1,
        "orders_completed": 1,
        "orders_cancelled": 0,
        "online_min": 80.0,
        "rest_min": 10.0,
        "charge_min": 0.0,
        "shift_start_min": 360.0,
        "shift_end_min": 1080.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _result():
    order = SimpleNamespace(
        order_id=11,
        t_min=540.0,
        pickup_cell="pickup-cell",
        drop_cell="drop-cell",
        dist_km=3.2,
        gross_vnd=16_000,
        pickup_lat=21.03,
        pickup_lon=105.83,
        drop_lat=21.04,
        drop_lon=105.84,
    )
    events = [
        SimpleNamespace(t_min=500.0, actor_id=7, kind="go_online", cell="home", detail={}),
        SimpleNamespace(t_min=540.0, actor_id=7, kind="order_matched", cell="home",
                        detail={"order_id": 11}),
        SimpleNamespace(t_min=550.0, actor_id=7, kind="pickup", cell="pickup-cell",
                        detail={"order_id": 11}),
        SimpleNamespace(t_min=565.0, actor_id=7, kind="dropoff", cell="drop-cell",
                        detail={"order_id": 11, "gross": 16_000, "dist_km": 3.2}),
    ]
    snapshots = [
        {"event_index": 0, "t_min": 500.0, "actor_id": 7, "state": "idle",
         "cell": "home", "lat": 21.01, "lon": 105.81, "soc_pct": 80.0,
         "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
         "orders_offered": 0, "orders_accepted": 0, "orders_completed": 0,
         "orders_cancelled": 0, "online_min": 0.0, "rest_min": 0.0,
         "charge_min": 0.0},
        {"event_index": 1, "t_min": 540.0, "actor_id": 7, "state": "enroute",
         "cell": "home", "lat": 21.01, "lon": 105.81, "soc_pct": 79.0,
         "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
         "orders_offered": 1, "orders_accepted": 1, "orders_completed": 0,
         "orders_cancelled": 0, "online_min": 40.0, "rest_min": 0.0,
         "charge_min": 0.0},
        {"event_index": 2, "t_min": 550.0, "actor_id": 7, "state": "on_trip",
         "cell": "pickup-cell", "lat": 21.03, "lon": 105.83, "soc_pct": 78.0,
         "payout_vnd": 0, "gross_vnd": 0, "points": 0, "trips_done": 0,
         "orders_offered": 1, "orders_accepted": 1, "orders_completed": 0,
         "orders_cancelled": 0, "online_min": 50.0, "rest_min": 0.0,
         "charge_min": 0.0},
        {"event_index": 3, "t_min": 565.0, "actor_id": 7, "state": "idle",
         "cell": "drop-cell", "lat": 21.04, "lon": 105.84, "soc_pct": 75.0,
         "payout_vnd": 12_000, "gross_vnd": 16_000, "points": 18, "trips_done": 1,
         "orders_offered": 1, "orders_accepted": 1, "orders_completed": 1,
         "orders_cancelled": 0, "online_min": 65.0, "rest_min": 0.0,
         "charge_min": 0.0},
    ]
    return SimpleNamespace(
        run_id="run-1", seed=1000, actors=[_actor()], orders=[order], events=events,
        trace_snapshots=snapshots,
        segments=[{
            "segment_id": "seg-1", "actor_id": 7, "t0": 540.0, "t1": 550.0,
            "kind": "enroute", "order_id": 11, "from_lat": 21.01,
            "from_lon": 105.81, "to_lat": 21.03, "to_lon": 105.83,
        }, {
            "segment_id": "seg-2", "actor_id": 7, "t0": 550.0, "t1": 565.0,
            "kind": "on_trip", "order_id": 11, "from_lat": 21.03,
            "from_lon": 105.83, "to_lat": 21.04, "to_lon": 105.84,
        }],
        advice_checkpoints=[], advice_artifacts=[], advice_checkpoint_events=[],
        config=SimpleNamespace(get=lambda key: 1440.0 if key == "time.end_min" else 0),
    )


def test_demo_trace_projects_canonical_driver_trip_and_delta():
    from gsm_sim.demo_trace import build_demo_trace

    trace = build_demo_trace(_result(), actor_id=7)

    assert [item["kind"] for item in trace["transitions"]] == [
        "go_online", "order_matched", "pickup", "dropoff"
    ]
    matched = trace["transitions"][1]
    assert matched["driver"]["soc_pct"] == 79.0
    assert matched["trip"] == {
        "trip_id": "trip-11", "order_id": 11, "state": "MATCHED",
        "pickup": {"lat": 21.03, "lon": 105.83, "cell": "pickup-cell"},
        "destination": {"lat": 21.04, "lon": 105.84, "cell": "drop-cell"},
        "dist_km": 3.2, "gross_vnd": 16_000,
    }
    completed = trace["transitions"][-1]
    assert completed["trip"]["state"] == "COMPLETED"
    assert completed["driver"]["payout_vnd"] == 12_000
    assert completed["state_delta"]["payout_vnd"] == 12_000
    assert completed["segment"]["segment_id"] == "seg-2"


def test_demo_trace_is_deterministic_and_keeps_provenance():
    from gsm_sim.demo_trace import build_demo_trace

    first = build_demo_trace(_result(), actor_id=7)
    second = build_demo_trace(_result(), actor_id=7)

    assert first == second
    assert first["provenance"] == {
        "run_id": "run-1", "seed": 1000, "data_mode": "sim-engine", "is_mock": True,
    }


def test_demo_trace_rejects_unknown_actor():
    from gsm_sim.demo_trace import build_demo_trace

    try:
        build_demo_trace(_result(), actor_id=999)
    except ValueError as exc:
        assert "actor" in str(exc)
    else:
        raise AssertionError("unknown actor must fail loudly")
