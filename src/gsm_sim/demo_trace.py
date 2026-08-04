"""Canonical, post-run projection used by the Web demo.

The simulator remains the only component that mutates actor/order state.  This module only
reads a completed ``RunResult`` and turns existing events, observer snapshots, segments and
checkpoint records into a deterministic actor timeline.  It must not import SimPy or draw
randomness.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any


_BASE_DATE = date(2026, 7, 1)
_VISIBLE_EVENT_KINDS = frozenset({
    "go_online", "order_matched", "order_declined", "order_skipped_soc",
    "order_cancelled_after_accept", "pickup", "dropoff", "rest",
    "charge_home_start", "charge_home_end", "go_swap", "swap_done", "swap_failed",
    "relocate", "end_shift", "censored_end_of_run", "advice_given",
    "advice_suppressed", "advice_bonus_gate", "advice_shift_extend",
    "advice_rest_window", "standby_followed",
})


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()[:24]


def minute_from_iso(value: str | None) -> float | None:
    """Convert a simulator trace ISO timestamp back to minutes from the base day."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    start = datetime.combine(_BASE_DATE, datetime.min.time(), tzinfo=parsed.tzinfo)
    return (parsed - start).total_seconds() / 60.0


def _driver_snapshot(raw: dict[str, Any], run_id: str, seed: int) -> dict[str, Any]:
    return {
        "driver_id": f"d-{raw['actor_id']}",
        "actor_id": int(raw["actor_id"]),
        "state": raw.get("state"),
        "simulation_time_min": float(raw.get("t_min", 0.0)),
        "position": {
            "lat": float(raw.get("lat", 0.0)),
            "lng": float(raw.get("lon", 0.0)),
            "cell": raw.get("cell"),
        },
        "soc_pct": float(raw.get("soc_pct", 0.0)),
        "payout_vnd": int(raw.get("payout_vnd", 0)),
        "gross_vnd": int(raw.get("gross_vnd", 0)),
        "points": int(raw.get("points", 0)),
        "trips_done": int(raw.get("trips_done", 0)),
        "orders_offered": int(raw.get("orders_offered", 0)),
        "orders_accepted": int(raw.get("orders_accepted", 0)),
        "orders_completed": int(raw.get("orders_completed", 0)),
        "orders_cancelled": int(raw.get("orders_cancelled", 0)),
        "online_min": float(raw.get("online_min", 0.0)),
        "rest_min": float(raw.get("rest_min", 0.0)),
        "charge_min": float(raw.get("charge_min", 0.0)),
        "shift_start_min": raw.get("shift_start_min"),
        "shift_end_min": raw.get("shift_end_min"),
        "provenance": {
            "run_id": run_id, "seed": seed, "data_mode": "sim-engine", "is_mock": True,
        },
    }


def _order_map(result: Any) -> dict[int, Any]:
    return {int(order.order_id): order for order in getattr(result, "orders", [])}


def _trip(order: Any, state: str) -> dict[str, Any]:
    return {
        "trip_id": f"trip-{int(order.order_id)}",
        "order_id": int(order.order_id),
        "state": state,
        "pickup": {"lat": float(order.pickup_lat), "lon": float(order.pickup_lon),
                    "cell": order.pickup_cell},
        "destination": {"lat": float(order.drop_lat), "lon": float(order.drop_lon),
                         "cell": order.drop_cell},
        "dist_km": float(order.dist_km),
        "gross_vnd": int(order.gross_vnd),
    }


def _state_for_event(kind: str) -> str | None:
    return {
        "order_matched": "MATCHED", "order_declined": "DECLINED",
        "order_skipped_soc": "SKIPPED_SOC", "order_cancelled_after_accept": "CANCELLED_AFTER_ACCEPT",
        "pickup": "PICKED_UP", "dropoff": "COMPLETED",
    }.get(kind)


def _segment_for(segments: list[dict], actor_id: int, t_min: float,
                 order_id: int | None) -> dict | None:
    candidates = [s for s in segments
                  if int(s.get("actor_id", -1)) == actor_id
                  and (order_id is None or s.get("order_id") == order_id)]
    if not candidates:
        return None
    exact_start = [s for s in candidates if abs(float(s.get("t0", -1)) - t_min) < 1e-6]
    if exact_start:
        # On a pickup boundary, prefer the passenger leg over the just-finished pickup leg.
        exact_start.sort(key=lambda s: (s.get("kind") != "on_trip", s.get("segment_id", "")))
        return dict(exact_start[0])
    exact_end = [s for s in candidates if abs(float(s.get("t1", -1)) - t_min) < 1e-6]
    if exact_end:
        exact_end.sort(key=lambda s: (s.get("kind") != "on_trip", s.get("segment_id", "")))
        return dict(exact_end[0])
    covering = [s for s in candidates
                if float(s.get("t0", -1)) <= t_min <= float(s.get("t1", -1))]
    return dict(sorted(covering, key=lambda s: (s.get("t0", 0), s.get("segment_id", "")))[0]) \
        if covering else None


def _checkpoint_minute(checkpoint: dict) -> float | None:
    refs = checkpoint.get("validity") or {}
    value = refs.get("valid_from") or checkpoint.get("created_at")
    return minute_from_iso(value)


def _checkpoint_for(checkpoints: list[dict], driver_id: str, t_min: float) -> dict | None:
    candidates = []
    for checkpoint in checkpoints:
        if checkpoint.get("driver_id") != driver_id:
            continue
        observed = _checkpoint_minute(checkpoint)
        if observed is not None and abs(observed - t_min) < 1e-6:
            candidates.append(checkpoint)
    if not candidates:
        return None
    return dict(sorted(candidates, key=lambda c: c.get("checkpoint_id", ""))[0])


def _checkpoint_transitions(checkpoints: list[dict], driver_id: str,
                            existing_times: set[float], snapshots: list[dict],
                            run_id: str, seed: int) -> list[dict]:
    extra: list[dict] = []
    for checkpoint in checkpoints:
        if checkpoint.get("driver_id") != driver_id:
            continue
        t_min = _checkpoint_minute(checkpoint)
        if t_min is None or any(abs(t_min - value) < 1e-6 for value in existing_times):
            continue
        previous = [snapshot for snapshot in snapshots
                    if float(snapshot.get("t_min", -1)) <= t_min]
        if not previous:
            continue
        raw = previous[-1]
        driver = _driver_snapshot({**raw, "t_min": t_min}, run_id, seed)
        transition_id = "transition-" + _digest({
            "run_id": run_id, "actor_id": raw["actor_id"], "kind": "advice_checkpoint",
            "t_min": t_min, "checkpoint_id": checkpoint["checkpoint_id"],
        })
        extra.append({
            "transition_id": transition_id, "event_index": None, "t_min": t_min,
            "kind": "advice_checkpoint", "driver": driver, "state_delta": {},
            "trip": None, "segment": None, "checkpoint": checkpoint,
            "timeline_event": {"kind": "advice_checkpoint",
                                "checkpoint_id": checkpoint["checkpoint_id"]},
        })
    return extra


def build_demo_trace(result: Any, actor_id: int) -> dict[str, Any]:
    """Build the immutable timeline consumed by ``DemoSessionService``."""
    actor = next((item for item in getattr(result, "actors", [])
                  if int(item.actor_id) == int(actor_id)), None)
    if actor is None:
        raise ValueError(f"actor {actor_id} không tồn tại trong run")

    run_id = str(getattr(result, "run_id", ""))
    seed = int(getattr(result, "seed", 0))
    raw_snapshots = [dict(item) for item in getattr(result, "trace_snapshots", [])
                     if int(item.get("actor_id", -1)) == int(actor_id)]
    snapshots_by_event = {int(item["event_index"]): item for item in raw_snapshots
                          if item.get("event_index") is not None}
    order_by_id = _order_map(result)
    segments = [dict(item) for item in getattr(result, "segments", [])]
    checkpoints = [dict(item) for item in getattr(result, "advice_checkpoints", [])]
    events = list(getattr(result, "events", []))
    lifecycle: dict[int, str] = {}
    previous_driver: dict[str, Any] | None = None
    transitions: list[dict[str, Any]] = []
    event_times: set[float] = set()

    for event_index, event in enumerate(events):
        if int(getattr(event, "actor_id", -1)) != int(actor_id):
            continue
        kind = str(getattr(event, "kind", ""))
        if kind not in _VISIBLE_EVENT_KINDS:
            continue
        raw = snapshots_by_event.get(event_index)
        if raw is None:
            # Existing hand-built tests/runs can omit observer snapshots.  Keep the projection
            # explicit and fail-safe instead of fabricating dynamic state.
            continue
        detail = dict(getattr(event, "detail", {}) or {})
        order_id = detail.get("order_id")
        if order_id is not None:
            order_id = int(order_id)
            state = _state_for_event(kind)
            if state is not None:
                lifecycle[order_id] = state
        driver = _driver_snapshot(raw, run_id, seed)
        state_delta = {}
        if previous_driver is not None:
            for key in ("state", "soc_pct", "payout_vnd", "gross_vnd", "points",
                        "trips_done", "orders_offered", "orders_accepted",
                        "orders_completed", "orders_cancelled", "online_min",
                        "rest_min", "charge_min"):
                if previous_driver.get(key) != driver.get(key):
                    state_delta[key] = driver[key]
        previous_driver = driver
        order = order_by_id.get(order_id) if order_id is not None else None
        trip = _trip(order, lifecycle[order_id]) if order is not None and order_id in lifecycle else None
        segment = _segment_for(segments, int(actor_id), float(event.t_min), order_id)
        checkpoint = _checkpoint_for(checkpoints, f"d-{actor_id}", float(event.t_min))
        transition_id = "transition-" + _digest({
            "run_id": run_id, "actor_id": actor_id, "event_index": event_index,
            "kind": kind, "t_min": float(event.t_min), "detail": detail,
        })
        transitions.append({
            "transition_id": transition_id, "event_index": event_index,
            "t_min": float(event.t_min), "kind": kind, "driver": driver,
            "state_delta": state_delta, "trip": trip, "segment": segment,
            "checkpoint": checkpoint,
            "timeline_event": {"event_index": event_index, "kind": kind,
                                "t_min": float(event.t_min), "detail": detail},
        })
        event_times.add(float(event.t_min))

    transitions.extend(_checkpoint_transitions(
        checkpoints, f"d-{actor_id}", event_times, raw_snapshots, run_id, seed))
    transitions.sort(key=lambda item: (float(item["t_min"]), item["event_index"] is None,
                                       item["event_index"] if item["event_index"] is not None else -1,
                                       item["transition_id"]))
    for index, transition in enumerate(transitions):
        transition["sequence"] = index
    return {
        "run_id": run_id, "seed": seed, "actor_id": int(actor_id),
        "driver_id": f"d-{actor_id}", "archetype": getattr(actor, "archetype", None),
        "fleet": getattr(getattr(actor, "fleet", None), "value", getattr(actor, "fleet", None)),
        "transitions": transitions,
        "checkpoints": checkpoints,
        "provenance": {"run_id": run_id, "seed": seed,
                        "data_mode": "sim-engine", "is_mock": True},
    }
