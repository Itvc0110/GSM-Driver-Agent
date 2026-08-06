from __future__ import annotations

from types import SimpleNamespace


def _actor():
    return SimpleNamespace(actor_id=7, archetype="P4", fleet=SimpleNamespace(value="swap"))


def _snapshot(t_min: float, event_index: int):
    return {
        "event_index": event_index, "t_min": t_min, "actor_id": 7,
        "state": "idle", "cell": "home", "lat": 21.01, "lon": 105.81,
        "soc_pct": 80.0, "payout_vnd": 0, "gross_vnd": 0, "points": 0,
        "trips_done": 0, "orders_offered": 0, "orders_accepted": 0,
        "orders_completed": 0, "orders_cancelled": 0, "online_min": 0.0,
        "rest_min": 0.0, "charge_min": 0.0,
    }


def _checkpoint(checkpoint_id: str, *, topic="energy", urgency="medium"):
    return {
        "checkpoint_id": checkpoint_id, "driver_id": "d-7", "topic": topic,
        "surface": "nudge", "current_action": {"code": "SWAP", "label_id": "action.swap"},
        "future_plan": [], "action_window": None,
        "validity": {
            "valid_from": "2026-07-01T09:00:00+07:00",
            "valid_until": "2026-07-01T10:00:00+07:00",
            "freshness_deadline": "2026-07-01T10:00:00+07:00",
        },
        "urgency_band": urgency, "material_revision": checkpoint_id,
        "reason_code": "solver_recommendation", "confidence_band": "high",
        "snapshot_ref": "snapshot:1", "solver_artifact_ref": "report:1",
        "source_decision_id": checkpoint_id, "run_id": "run-1",
        "solver_input_refs": [], "solver_report_refs": [], "solver_set": ["S2"],
        "data_mode": "synthetic", "is_mock": True,
        "created_at": "2026-07-01T09:00:00+07:00",
    }


def _result(events, snapshots, checkpoints):
    lifecycle_events = []
    for cp in checkpoints:
        lifecycle_events.extend([
            {"event_id": f"created:{cp['checkpoint_id']}", "checkpoint_id": cp["checkpoint_id"],
             "driver_id": "d-7", "display_id": None, "event_type": "created",
             "occurred_at": cp["created_at"], "actor": "system", "origin": "checkpoint",
             "reason_code": None, "relation_type": None, "confidence": None, "payload": {}},
            {"event_id": f"ready:{cp['checkpoint_id']}", "checkpoint_id": cp["checkpoint_id"],
             "driver_id": "d-7", "display_id": None, "event_type": "ready",
             "occurred_at": cp["created_at"], "actor": "advisor", "origin": "simulator",
             "reason_code": None, "relation_type": None, "confidence": None, "payload": {}},
        ])
    return SimpleNamespace(
        run_id="run-1", seed=1000, actors=[_actor()], orders=[], events=events,
        trace_snapshots=snapshots, segments=[], advice_checkpoints=checkpoints,
        advice_artifacts=[], advice_checkpoint_events=lifecycle_events,
    )


def test_ready_checkpoint_after_fractional_event_is_attached_once():
    from gsm_sim.demo_trace import build_demo_trace

    events = [SimpleNamespace(t_min=540.5, actor_id=7, kind="go_online", cell="home", detail={})]
    trace = build_demo_trace(_result(events, [_snapshot(540.5, 0)], [_checkpoint("ckpt-1")]), 7)

    attached = [t for t in trace["transitions"]
                if (t.get("checkpoint") or {}).get("checkpoint_id") == "ckpt-1"]
    assert len(attached) == 1
    assert not [item for item in trace["checkpoint_audit"] if item["checkpoint_id"] == "ckpt-1"]


def test_attach_skips_moving_transition_to_first_safe_within_validity():
    """UPDATE-147: card không được gắn vào transition đang di chuyển nếu còn
    transition an toàn TRONG validity — trước đây 12 card/seed mất kiểu này."""
    from gsm_sim.demo_trace import build_demo_trace

    events = [
        SimpleNamespace(t_min=540.5, actor_id=7, kind="pickup", cell="home",
                        detail={"order_id": 1}),
        SimpleNamespace(t_min=548.0, actor_id=7, kind="dropoff", cell="home",
                        detail={"order_id": 1}),
    ]
    moving = {**_snapshot(540.5, 0), "state": "enroute"}
    safe = {**_snapshot(548.0, 1), "state": "idle"}
    trace = build_demo_trace(_result(events, [moving, safe], [_checkpoint("ckpt-1")]), 7)

    attached = [(t["kind"], t["checkpoint"]["checkpoint_id"])
                for t in trace["transitions"] if t.get("checkpoint")]
    assert attached == [("dropoff", "ckpt-1")]


def test_attach_moving_only_window_still_attaches_for_queued_trail():
    """Di chuyển SUỐT validity ⇒ vẫn gắn vào transition đầu để moving-gate ghi
    `queued` (dấu vết lifecycle), thay vì card biến mất không vết."""
    from gsm_sim.demo_trace import build_demo_trace

    events = [
        SimpleNamespace(t_min=545.0, actor_id=7, kind="pickup", cell="home",
                        detail={"order_id": 1}),
        SimpleNamespace(t_min=630.0, actor_id=7, kind="dropoff", cell="home",
                        detail={"order_id": 1}),  # sau valid_until 10:00 (600)
    ]
    moving = {**_snapshot(545.0, 0), "state": "on_trip"}
    late = {**_snapshot(630.0, 1), "state": "idle"}
    trace = build_demo_trace(_result(events, [moving, late], [_checkpoint("ckpt-1")]), 7)

    attached = [(t["kind"], t["checkpoint"]["checkpoint_id"])
                for t in trace["transitions"] if t.get("checkpoint")]
    assert attached == [("pickup", "ckpt-1")]


def test_attach_expired_before_any_transition_is_audited():
    from gsm_sim.demo_trace import build_demo_trace

    events = [SimpleNamespace(t_min=630.0, actor_id=7, kind="go_online",
                              cell="home", detail={})]
    trace = build_demo_trace(
        _result(events, [_snapshot(630.0, 0)], [_checkpoint("ckpt-1")]), 7)

    assert not [t for t in trace["transitions"] if t.get("checkpoint")]
    audit = [item for item in trace["checkpoint_audit"]
             if item["checkpoint_id"] == "ckpt-1"]
    assert audit and audit[0]["reason"] == "expired_before_transition"


def test_same_time_non_primary_ready_checkpoint_has_explicit_policy_reason():
    from gsm_sim.demo_trace import build_demo_trace

    events = [SimpleNamespace(t_min=540.5, actor_id=7, kind="go_online", cell="home", detail={})]
    first = _checkpoint("ckpt-energy", topic="energy", urgency="high")
    second = _checkpoint("ckpt-rest", topic="rest", urgency="medium")
    trace = build_demo_trace(_result(events, [_snapshot(540.5, 0)], [first, second]), 7)

    attached_ids = [t["checkpoint"]["checkpoint_id"] for t in trace["transitions"]
                    if t.get("checkpoint")]
    assert attached_ids == ["ckpt-energy"]
    assert {item["checkpoint_id"] for item in trace["checkpoint_audit"]} == {"ckpt-rest"}
    assert trace["checkpoint_audit"][0]["reason"] == "non_primary_same_time"
