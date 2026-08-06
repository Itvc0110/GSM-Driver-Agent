#!/usr/bin/env python3
"""Inventory AdviceCheckpoint records from the completed simulator trace.

This is an analysis-only tool.  It imports the same demo run factory used by the Web
demo, then projects the immutable RunResult into checkpoint/lifecycle/actor tables.
It never changes simulator configuration, writes telemetry, or calls the product
checkpoint service/lease path.  Run it from the repository root with:

    PYTHONPATH=src:ui/backend .venv/bin/python \
      research/audit/2026-08-05-checkpoint-inventory/analyze_checkpoints.py \
      --seeds 1000 1001 1002 1003 1004

The default output directory is this script's directory.  The simulator used here is
``app.services.demo_session._default_run``; this intentionally matches the Web demo
fixture (all-driver shadow trace, adherence forced to zero, template presentation
metadata) and is not a new simulation arm.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from app.services.demo_session import _default_run
from gsm_core.advisor.checkpoint_templates import CheckpointTemplateRegistry
from gsm_core.lifecycle.checkpoint import project_checkpoint_events
from gsm_sim.demo_trace import build_demo_trace, minute_from_iso


OUTPUT_DIR = Path(__file__).resolve().parent
REPORT_NAME = "checkpoint-audit.md"
ACTOR_CSV = "checkpoint-by-actor.csv"
TYPE_CSV = "checkpoint-by-type.csv"
TIMELINE_JSON = "checkpoint-timeline.json"


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _median(values: Iterable[float]) -> float | None:
    data = [float(v) for v in values if v is not None]
    return round(statistics.median(data), 3) if data else None


def _percentile(values: Iterable[float], percentile: float) -> float | None:
    data = sorted(float(v) for v in values if v is not None)
    if not data:
        return None
    if len(data) == 1:
        return round(data[0], 3)
    position = (len(data) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(data) - 1)
    fraction = position - lower
    result = data[lower] + (data[upper] - data[lower]) * fraction
    return round(result, 3)


def _time_minute(iso: str | None) -> float | None:
    return minute_from_iso(iso) if iso else None


def _action_code(checkpoint: dict[str, Any]) -> str:
    return str((checkpoint.get("current_action") or {}).get("code") or "NO_ACTION")


def _future_codes(checkpoint: dict[str, Any]) -> list[str]:
    return [str(item.get("code")) for item in checkpoint.get("future_plan") or []
            if item.get("code")]


def _solver_key(checkpoint: dict[str, Any]) -> str:
    values = checkpoint.get("solver_set") or []
    if isinstance(values, str):
        return values
    return "+".join(sorted(str(value) for value in values)) or "UNKNOWN"


def _checkpoint_key(checkpoint: dict[str, Any]) -> tuple[str, str]:
    """Keep repeated deterministic checkpoint IDs separate across simulator runs."""
    return (str(checkpoint.get("run_id") or ""), str(checkpoint.get("checkpoint_id") or ""))


def _state(events: list[dict[str, Any]], checkpoint: dict[str, Any]) -> str:
    if not events:
        return str(checkpoint.get("state") or "unknown")
    try:
        return str(project_checkpoint_events(events)["state"])
    except Exception:
        return str(checkpoint.get("state") or "unknown")


def _compact_transition(transition: dict[str, Any], seed: int, run_id: str) -> dict[str, Any]:
    driver = transition.get("driver") or {}
    position = driver.get("position") or {}
    trip = transition.get("trip") or {}
    segment = transition.get("segment") or {}
    trip_state = trip.get("state")
    if trip_state == "MATCHED":
        route_leg = "driver_to_pickup"
    elif trip_state in {"PICKED_UP", "COMPLETED"}:
        route_leg = "pickup_to_destination"
    else:
        route_leg = "NOT_REQUIRED"
    return {
        "seed": seed,
        "run_id": run_id,
        "actor_id": int(transition.get("driver", {}).get("actor_id", -1)),
        "sequence": int(transition.get("sequence", -1)),
        "transition_id": transition.get("transition_id"),
        "event_index": transition.get("event_index"),
        "t_min": float(transition.get("t_min", 0.0)),
        "kind": transition.get("kind"),
        "driver_state": driver.get("state"),
        "soc_pct": driver.get("soc_pct"),
        "payout_vnd": driver.get("payout_vnd"),
        "points": driver.get("points"),
        "trips_done": driver.get("trips_done"),
        "position": {"lat": position.get("lat"), "lng": position.get("lng"),
                      "cell": position.get("cell")},
        "trip_id": trip.get("trip_id"),
        "order_id": trip.get("order_id"),
        "trip_state": trip_state,
        "route_leg": route_leg,
        "segment_id": segment.get("segment_id"),
        "segment_kind": segment.get("kind"),
        "segment_t0": segment.get("t0"),
        "segment_t1": segment.get("t1"),
        "checkpoint_id": (transition.get("checkpoint") or {}).get("checkpoint_id"),
    }


def _checkpoint_row(checkpoint: dict[str, Any], events: list[dict[str, Any]],
                    links: list[dict[str, Any]], attached: list[dict[str, Any]],
                    seed: int, run_id: str, snapshot: dict[str, Any] | None = None,
                    solver_report: dict[str, Any] | None = None) -> dict[str, Any]:
    validity = checkpoint.get("validity") or {}
    start = _time_minute(validity.get("valid_from") or checkpoint.get("created_at"))
    end = _time_minute(validity.get("valid_until"))
    duration = end - start if start is not None and end is not None else None
    event_counts = Counter(str(event.get("event_type")) for event in events)
    return {
        "seed": seed,
        "run_id": run_id,
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "driver_id": checkpoint.get("driver_id"),
        "actor_id": int(str(checkpoint.get("driver_id", "d--1")).removeprefix("d-")),
        "topic": checkpoint.get("topic"),
        "source_solver": _solver_key(checkpoint),
        "solver_set": list(checkpoint.get("solver_set") or []),
        "canonical_action": _action_code(checkpoint),
        "current_action": checkpoint.get("current_action"),
        "future_plan": checkpoint.get("future_plan") or [],
        "future_action_codes": _future_codes(checkpoint),
        "surface": checkpoint.get("surface"),
        "trigger_type": checkpoint.get("trigger_type"),
        "reason_code": checkpoint.get("reason_code"),
        "urgency_band": checkpoint.get("urgency_band"),
        "confidence_band": checkpoint.get("confidence_band"),
        "action_window": checkpoint.get("action_window"),
        "validity": validity,
        "validity_minutes": round(duration, 3) if duration is not None else None,
        "created_at": checkpoint.get("created_at"),
        "created_min": start,
        "state": _state(events, checkpoint),
        "event_types": sorted(event_counts),
        "event_counts": dict(event_counts),
        "execution_observed": event_counts.get("execution_observed", 0) > 0,
        "execution_link_count": len(links),
        "execution_links": links,
        "attached_transition_count": len(attached),
        "attached_transition_ids": [item["transition_id"] for item in attached],
        "attached_sequences": [item["sequence"] for item in attached],
        "presentation_observed": bool(event_counts.get("offered") or
                                       event_counts.get("displayed")),
        "offered_count": event_counts.get("offered", 0),
        "displayed_count": event_counts.get("displayed", 0),
        "accepted_count": event_counts.get("accepted", 0),
        "dismissed_count": event_counts.get("dismissed", 0),
        "expanded_count": event_counts.get("expanded", 0),
        "data_mode": checkpoint.get("data_mode"),
        "is_mock": checkpoint.get("is_mock"),
        "source_decision_id": checkpoint.get("source_decision_id"),
        "capture_driver_state": (snapshot or {}).get("actor_state"),
        "capture_soc_pct": (snapshot or {}).get("soc_pct"),
        "capture_points": (snapshot or {}).get("points"),
        "solver_report_confidence": (solver_report or {}).get("confidence"),
        "solver_report_number_count": len((solver_report or {}).get("numbers") or []),
        "solver_report_caveat_count": len((solver_report or {}).get("caveats") or []),
    }


def _run_bundle(seed: int) -> dict[str, Any]:
    result = _default_run(seed)
    run_id = str(getattr(result, "run_id", ""))
    checkpoints = [dict(item) for item in getattr(result, "advice_checkpoints", [])]
    events = [dict(item) for item in getattr(result, "advice_checkpoint_events", [])]
    links = [dict(item) for item in getattr(result, "execution_links", [])]
    by_checkpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_checkpoint[str(event.get("checkpoint_id"))].append(event)
    links_by_checkpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in links:
        links_by_checkpoint[str(link.get("checkpoint_id"))].append(link)
    artifacts_by_id = {
        str(item.get("artifact_id")): item for item in getattr(result, "advice_artifacts", [])
    }

    traces: dict[int, dict[str, Any]] = {}
    compact_transitions: list[dict[str, Any]] = []
    attached_by_checkpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    audit_rows: list[dict[str, Any]] = []
    actor_rows: list[dict[str, Any]] = []
    for actor in getattr(result, "actors", []):
        actor_id = int(actor.actor_id)
        trace = build_demo_trace(result, actor_id)
        traces[actor_id] = trace
        transitions = [_compact_transition(item, seed, run_id)
                       for item in trace.get("transitions", [])]
        compact_transitions.extend(transitions)
        for item in transitions:
            checkpoint_id = item.get("checkpoint_id")
            if checkpoint_id:
                attached_by_checkpoint[str(checkpoint_id)].append(item)
        for item in trace.get("checkpoint_audit", []):
            audit_rows.append({"seed": seed, "run_id": run_id, "actor_id": actor_id,
                               **dict(item)})
        actor_checkpoints = [item for item in checkpoints
                             if item.get("driver_id") == f"d-{actor_id}"]
        actor_transitions = [item for item in transitions if item["actor_id"] == actor_id]
        attached = [item for item in actor_transitions if item.get("checkpoint_id")]
        state_counts = Counter(
            _state(by_checkpoint.get(str(item.get("checkpoint_id")), []), item)
            for item in actor_checkpoints)
        event_counts = Counter(
            event.get("event_type") for item in actor_checkpoints
            for event in by_checkpoint.get(str(item.get("checkpoint_id")), []))
        cp_minutes = defaultdict(list)
        for item in actor_checkpoints:
            cp_minutes[(str(item.get("topic")), _solver_key(item))].append(
                _time_minute((item.get("validity") or {}).get("valid_from") or
                             item.get("created_at")))
        attached_sequences = sorted(int(item["sequence"]) for item in attached)
        sequence_gaps = [b - a for a, b in zip(attached_sequences, attached_sequences[1:])]
        topic_names = sorted({str(item.get("topic")) for item in actor_checkpoints})
        action_names = sorted({_action_code(item) for item in actor_checkpoints})
        route_legs = {item["route_leg"] for item in actor_transitions}
        actor_rows.append({
            "scope": "seed", "seed": seed, "run_id": run_id,
            "actor_id": actor_id, "driver_id": f"d-{actor_id}",
            "archetype": str(getattr(actor, "archetype", "")),
            "fleet": str(getattr(getattr(actor, "fleet", None), "value",
                                    getattr(actor, "fleet", ""))),
            "total_checkpoints": len(actor_checkpoints),
            "ready": state_counts.get("ready", 0),
            "queued": state_counts.get("queued", 0),
            "suppressed": state_counts.get("suppressed", 0),
            "expired": state_counts.get("expired", 0),
            "superseded": state_counts.get("superseded", 0),
            "offered": event_counts.get("offered", 0),
            "displayed": event_counts.get("displayed", 0),
            "accepted": event_counts.get("accepted", 0),
            "dismissed": event_counts.get("dismissed", 0),
            "expanded": event_counts.get("expanded", 0),
            "execution_observed": event_counts.get("execution_observed", 0),
            "attached": len(attached),
            "unattached": max(len(actor_checkpoints) - len(attached), 0),
            "first_checkpoint_min": min((x for x in (
                _time_minute((item.get("validity") or {}).get("valid_from") or
                             item.get("created_at")) for item in actor_checkpoints)
                if x is not None), default=None),
            "first_attached_step": min((int(item["sequence"]) + 1 for item in attached),
                                        default=None),
            "median_steps_between_attached": _median(sequence_gaps),
            "trip_transition_count": sum(1 for item in actor_transitions if item.get("trip_id")),
            "two_route_legs": int({"driver_to_pickup", "pickup_to_destination"}
                                   <= route_legs),
            "topics": ";".join(topic_names),
            "actions": ";".join(action_names),
            "final_payout_vnd": int(getattr(actor, "payout_vnd", 0)),
            "final_trips_done": int(getattr(actor, "trips_done", 0)),
        })

    rows = []
    for checkpoint in checkpoints:
        checkpoint_id = str(checkpoint.get("checkpoint_id"))
        rows.append(_checkpoint_row(
            checkpoint, by_checkpoint.get(checkpoint_id, []),
            links_by_checkpoint.get(checkpoint_id, []),
            attached_by_checkpoint.get(checkpoint_id, []), seed, run_id,
            snapshot=(artifacts_by_id.get(str(checkpoint.get("snapshot_ref"))) or {}).get("payload"),
            solver_report=(artifacts_by_id.get(str((checkpoint.get("solver_report_refs") or [None])[0])) or {}).get("payload")))
    return {
        "seed": seed,
        "run_id": run_id,
        "checkpoints": rows,
        "transitions": compact_transitions,
        "audit": audit_rows,
        "actors": actor_rows,
        "traces": traces,
        "raw_event_counts": dict(Counter(event.get("event_type") for event in events)),
        "raw_checkpoint_event_count": len(events),
        "raw_execution_link_count": len(links),
        "checkpoint_id_counts": dict(Counter(str(item.get("checkpoint_id")) for item in checkpoints)),
    }


def _aggregate_type_rows(checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for checkpoint in checkpoints:
        groups[(str(checkpoint.get("source_solver")), str(checkpoint.get("topic")),
                str(checkpoint.get("canonical_action")))].append(checkpoint)
    rows = []
    total_count = len(checkpoints)
    for (source, topic, action), items in sorted(groups.items()):
        drivers = {item["driver_id"] for item in items}
        states = Counter(item.get("state") for item in items)
        validities = [item["validity_minutes"] for item in items
                      if item.get("validity_minutes") is not None]
        by_driver: dict[str, list[float]] = defaultdict(list)
        for item in items:
            if item.get("created_min") is not None:
                by_driver[item["driver_id"]].append(float(item["created_min"]))
        gaps = [b - a for times in by_driver.values() for a, b in
                zip(sorted(times), sorted(times)[1:])]
        event_total = Counter()
        for item in items:
            for key, value in (item.get("event_counts") or {}).items():
                event_total[key] += int(value)
        ready_count = states.get("ready", 0)
        rows.append({
            "scope": "all_seeds", "seed": "ALL", "source_solver": source,
            "topic": topic, "canonical_action": action,
            "count": len(items), "driver_count": len(drivers),
            "share_of_checkpoints": (round(len(items) / total_count, 6)
                                      if total_count else None),
            "ready": ready_count, "queued": states.get("queued", 0),
            "suppressed": states.get("suppressed", 0),
            "expired": states.get("expired", 0),
            "superseded": states.get("superseded", 0),
            "offered": event_total.get("offered", 0),
            "displayed": event_total.get("displayed", 0),
            "accepted": event_total.get("accepted", 0),
            "dismissed": event_total.get("dismissed", 0),
            "expanded": event_total.get("expanded", 0),
            "execution_observed": event_total.get("execution_observed", 0),
            "ready_rate": round(ready_count / len(items), 6) if items else None,
            "display_rate_of_ready": (round(event_total.get("offered", 0) / ready_count, 6)
                                      if ready_count else None),
            "mean_validity_minutes": round(statistics.mean(validities), 3)
            if validities else None,
            "median_gap_minutes": _median(gaps),
            "p90_gap_minutes": _percentile(gaps, 0.90),
            "template_key": _template_key(action),
        })
    return rows


def _aggregate_actor_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[int(row["actor_id"])].append(row)
    result = []
    for actor_id, items in sorted(groups.items()):
        numeric = ("total_checkpoints", "ready", "queued", "suppressed", "expired",
                   "superseded", "offered", "displayed", "accepted", "dismissed",
                   "expanded", "execution_observed", "attached", "unattached",
                   "trip_transition_count", "final_payout_vnd", "final_trips_done")
        row = {"scope": "all_seeds", "seed": "ALL", "actor_id": actor_id,
               "driver_id": f"d-{actor_id}", "archetype": items[0]["archetype"],
               "fleet": items[0]["fleet"]}
        for key in numeric:
            row[key] = sum(int(item.get(key) or 0) for item in items)
        row["two_route_legs"] = int(any(item.get("two_route_legs") for item in items))
        row["first_checkpoint_min"] = min(
            (item["first_checkpoint_min"] for item in items
             if item.get("first_checkpoint_min") is not None), default=None)
        row["first_attached_step"] = min(
            (item["first_attached_step"] for item in items
             if item.get("first_attached_step") is not None), default=None)
        row["median_steps_between_attached"] = _median(
            item["median_steps_between_attached"] for item in items
            if item.get("median_steps_between_attached") is not None)
        topics = set()
        actions = set()
        for item in items:
            topics.update(filter(None, str(item.get("topics", "")).split(";")))
            actions.update(filter(None, str(item.get("actions", "")).split(";")))
        row["topics"] = ";".join(sorted(topics))
        row["actions"] = ";".join(sorted(actions))
        result.append(row)
    return result


def _template_key(action: str) -> str:
    return {
        "PROTECT_ELIGIBILITY": "S1_BONUS_PROGRESS",
        "ONLINE": "S2_ONLINE_NOW[_SWAP_LATER]",
        "SWAP": "S2_SWAP_NOW",
        "REST": "S7_REST_WINDOW",
        "END": "S2_END_SHIFT",
        "EXTEND": "S2_EXTEND_SHIFT",
        "REPOSITION_SIM_ONLY": "S4_RELOCATE",
    }.get(action, "FALLBACK_NO_ACTION")


def _template_preview(checkpoint: dict[str, Any]) -> dict[str, str]:
    registry = CheckpointTemplateRegistry()
    rendered = registry.resolve(checkpoint, facts=[], numbers=[], caveats=[],
                                locale="vi-VN", surface=str(checkpoint.get("surface") or "nudge"))
    return {"template_key": rendered.template_key, "title": rendered.title,
            "summary": rendered.summary, "why": rendered.why,
            "template_version": rendered.template_version}


def _scenario_record(name: str, availability: str, checkpoint: dict[str, Any] | None,
                     transition: dict[str, Any] | None, reason: str | None = None,
                     extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"scenario_name": name, "availability": availability,
                           "reason": reason}
    if checkpoint is None:
        row.update({"seed": None, "actor_id": None, "checkpoint_id": None,
                    "topic": None, "source_solver": None, "canonical_action": None,
                    "current_action": None, "future_plan": [], "action_window": None,
                    "transition_kind": None, "transition_start_min": None,
                    "steps_to_checkpoint": None, "driver_state": None,
                    "template_key": None, "card_title": None, "card_summary": None,
                    "card_why": None, "execution_observed": None,
                    "expected_intent": "không có checkpoint trong dữ liệu đã chạy"})
        if transition:
            row.update({
                "seed": transition.get("seed"), "actor_id": transition.get("actor_id"),
                "transition_kind": transition.get("kind"),
                "transition_start_min": transition.get("t_min"),
                "steps_to_checkpoint": int(transition.get("sequence", -1)) + 1,
                "driver_state": transition.get("driver_state"),
            })
    else:
        preview = _template_preview(checkpoint)
        row.update({
            "seed": checkpoint.get("seed"), "actor_id": checkpoint.get("actor_id"),
            "checkpoint_id": checkpoint.get("checkpoint_id"),
            "topic": checkpoint.get("topic"),
            "source_solver": checkpoint.get("source_solver"),
            "canonical_action": checkpoint.get("canonical_action"),
            "current_action": checkpoint.get("current_action"),
            "future_plan": checkpoint.get("future_plan"),
            "action_window": checkpoint.get("action_window"),
            "transition_kind": transition.get("kind") if transition else None,
            "transition_start_min": transition.get("t_min") if transition else None,
            "steps_to_checkpoint": (int(transition["sequence"]) + 1
                                     if transition else None),
            "driver_state": transition.get("driver_state") if transition else None,
            "template_key": preview["template_key"],
            "card_title": preview["title"], "card_summary": preview["summary"],
            "card_why": preview["why"],
            "execution_observed": checkpoint.get("execution_observed"),
            "expected_intent": "xem; accepted/dismissed/expanded là intent UI, không phải execution",
        })
    if extra:
        row.update(extra)
    return row


def _choose_scenarios(bundles: list[dict[str, Any]], checkpoints: list[dict[str, Any]],
                      actor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions_by_cp: dict[tuple[str, str], dict[str, Any]] = {}
    for bundle in bundles:
        for transition in bundle["transitions"]:
            if transition.get("checkpoint_id"):
                transitions_by_cp.setdefault(
                    (str(transition.get("run_id")), str(transition["checkpoint_id"])),
                    transition)
    actor_topic_count = {int(row["actor_id"]): len(row["topics"].split(";"))
                         for row in _aggregate_actor_rows(actor_rows)}

    def first(predicate):
        return next((cp for cp in checkpoints if predicate(cp)), None)

    def transition_for(cp):
        return transitions_by_cp.get(_checkpoint_key(cp)) if cp else None

    def safe_ready(cp):
        transition = transition_for(cp)
        return (cp["state"] == "ready" and cp["attached_transition_count"] == 1
                and transition is not None
                and transition.get("driver_state") not in {"enroute", "on_trip"})

    def with_name(name, predicate, reason, *, displayable: bool = True):
        candidates = [item for item in checkpoints if predicate(item)]
        cp = min(candidates, key=lambda item: (
            (transition_for(item) or {}).get("sequence", 10**9),
            str(item.get("run_id")), str(item.get("checkpoint_id")))) if candidates else None
        availability = ("AVAILABLE" if displayable else "AVAILABLE_LIFECYCLE_ONLY") if cp else "NOT_AVAILABLE"
        return _scenario_record(name, availability, cp,
                                transition_for(cp),
                                (None if displayable and cp else
                                 ("historical lifecycle only; no re-offer" if cp else reason)))

    scenarios = [
        with_name("current_action_vs_future_plan",
                  lambda cp: safe_ready(cp) and cp["canonical_action"] == "ONLINE"
                  and "SWAP" in cp.get("future_action_codes", []),
                  "Không thấy checkpoint ONLINE với SWAP trong future_plan ở các seed đã chạy."),
        with_name("low_battery_or_swap", lambda cp: safe_ready(cp)
                  and (cp["canonical_action"] == "SWAP" or cp["topic"] == "energy"),
                  "Không có checkpoint energy/SWAP READY được attach trong các seed đã chạy."),
        with_name("bonus_milestone", lambda cp: safe_ready(cp)
                  and (cp["topic"] == "bonus_eligibility" or
                       cp["canonical_action"] == "PROTECT_ELIGIBILITY"),
                  "Không có checkpoint S1 trong các seed đã chạy."),
        with_name("rest_or_safety", lambda cp: safe_ready(cp)
                  and (cp["canonical_action"] == "REST" or cp["topic"] == "rest"),
                  "Không có checkpoint REST READY được attach trong các seed đã chạy."),
        with_name("queued_while_moving", lambda cp: cp["state"] == "queued",
                  "Trace capture hiện đánh giá is_driving=False; không quan sát được queued trong nhóm seed này."),
        with_name("expired_or_superseded", lambda cp: cp["state"] in {"expired", "superseded"},
                  "Không có lifecycle expired/superseded trong RunResult; đây là product polling path.",
                  displayable=False),
    ]

    multi = first(lambda cp: actor_topic_count.get(int(cp["actor_id"]), 0) >= 2)
    scenarios.append(_scenario_record(
        "actor_with_multiple_checkpoint_types", "AVAILABLE" if multi else "NOT_AVAILABLE", multi,
        transition_for(multi),
        None if multi else "Không có actor có từ hai topic trong các seed đã chạy."))

    no_cp = next((row for row in _aggregate_actor_rows(actor_rows)
                  if int(row["total_checkpoints"]) == 0), None)
    scenarios.append(_scenario_record(
        "actor_with_no_checkpoint", "AVAILABLE" if no_cp else "NOT_AVAILABLE", None, None,
        None if no_cp else "Mọi actor đều có ít nhất một checkpoint trong nhóm seed đã chạy.",
        {"seed": "ALL", "actor_id": no_cp["actor_id"] if no_cp else None,
         "expected_intent": "xem empty/silent state; không có card hay fake ID"}))

    two_leg = None
    for row in _aggregate_actor_rows(actor_rows):
        if row.get("two_route_legs"):
            two_leg = row
            break
    two_leg_transition = None
    if two_leg:
        for bundle in bundles:
            if any(int(item["actor_id"]) == int(two_leg["actor_id"]) for item in bundle["actors"]):
                candidates = [item for item in bundle["transitions"]
                              if int(item["actor_id"]) == int(two_leg["actor_id"]) and
                              item.get("route_leg") != "NOT_REQUIRED"]
                if candidates:
                    two_leg_transition = candidates[0]
                    break
    scenarios.append(_scenario_record(
        "trip_with_two_route_legs", "AVAILABLE" if two_leg_transition else "NOT_AVAILABLE",
        None, two_leg_transition,
        None if two_leg_transition else "Không thấy actor có cả MATCHED và PICKED_UP/COMPLETED leg.",
        {"seed": two_leg_transition.get("seed") if two_leg_transition else None,
         "actor_id": two_leg_transition.get("actor_id") if two_leg_transition else None,
         "expected_intent": "xem driver→pickup rồi pickup→destination; route chỉ là geometry display"}))

    recap = first(lambda cp: cp["topic"] == "recap" or cp["surface"] == "recap")
    scenarios.append(_scenario_record(
        "end_shift_recap", "AVAILABLE" if recap else "NOT_AVAILABLE", recap,
        transition_for(recap),
        None if recap else "Schema có surface recap nhưng simulator hiện không tạo recap checkpoint."))
    return scenarios


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            encoded = {key: (json.dumps(value, ensure_ascii=False, sort_keys=True)
                             if isinstance(value, (dict, list)) else value)
                       for key, value in row.items()}
            writer.writerow(encoded)


def _md(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _build_report(seeds: list[int], bundles: list[dict[str, Any]],
                  checkpoints: list[dict[str, Any]], actor_rows: list[dict[str, Any]],
                  type_rows: list[dict[str, Any]], scenarios: list[dict[str, Any]]) -> str:
    state_counts = Counter(item.get("state") for item in checkpoints)
    capture_state_counts = Counter(item.get("capture_driver_state") for item in checkpoints)
    event_counts = Counter()
    for bundle in bundles:
        event_counts.update(bundle["raw_event_counts"])
    attached = sum(int(item.get("attached_transition_count") or 0) for item in checkpoints)
    attached_once = sum(item.get("attached_transition_count") == 1 for item in checkpoints)
    unattached = sum(item.get("attached_transition_count") == 0 for item in checkpoints)
    duplicate = sum(item.get("attached_transition_count", 0) > 1 for item in checkpoints)
    offered = event_counts.get("offered", 0)
    displayed = event_counts.get("displayed", 0)
    accepted = event_counts.get("accepted", 0)
    dismissed = event_counts.get("dismissed", 0)
    expanded = event_counts.get("expanded", 0)
    executions = event_counts.get("execution_observed", 0)
    intervals = []
    hour_counts = Counter()
    by_actor_type: dict[tuple[int, str], list[float]] = defaultdict(list)
    for item in checkpoints:
        if item.get("created_min") is not None:
            hour_counts[int(float(item["created_min"]) // 60) % 24] += 1
            by_actor_type[(int(item["actor_id"]), str(item["topic"]))].append(
                float(item["created_min"]))
    for times in by_actor_type.values():
        intervals.extend(b - a for a, b in zip(sorted(times), sorted(times)[1:]))
    first_steps = [row["first_attached_step"] for row in actor_rows
                   if row.get("first_attached_step") is not None]
    actor_all = _aggregate_actor_rows(actor_rows)
    no_cp_count = sum(int(row["total_checkpoints"]) == 0 for row in actor_all)
    id_groups: dict[str, set[str]] = defaultdict(set)
    for item in checkpoints:
        id_groups[str(item.get("checkpoint_id"))].add(str(item.get("run_id")))
    repeated_ids = {key: values for key, values in id_groups.items() if len(values) > 1}
    top_actors = sorted(actor_all, key=lambda row: (-int(row["total_checkpoints"]),
                                                     int(row["actor_id"])))[:10]
    lines = [
        "# AdviceCheckpoint inventory audit (read-only)", "",
        f"- Analysis date: 2026-08-05", f"- Demo seeds: `{', '.join(map(str, seeds))}`",
        "- Run factory: `ui/backend/app/services/demo_session.py:_default_run`",
        "- Scope: completed simulator observer trace + pure Web demo projection; no product lease or UI interaction was injected.",
        "- Provenance: `data_mode=synthetic`, `is_mock=true` in the simulator trace.", "",
        "## Executive summary", "",
        f"The five Web-demo runs produced **{len(checkpoints)} checkpoint records** across "
        f"{len(seeds)} seeds. Final projected lifecycle states are "
        f"`ready={state_counts.get('ready', 0)}`, `suppressed={state_counts.get('suppressed', 0)}`, "
        f"`queued={state_counts.get('queued', 0)}`, `expired={state_counts.get('expired', 0)}`, "
        f"`superseded={state_counts.get('superseded', 0)}`.",
        f"The trace attached {attached} checkpoint references: {attached_once} exactly once, "
        f"{unattached} with no attached transition and {duplicate} with more than one attachment.",
        f"The simulator stream contains {executions} `execution_observed` events/links, but "
        f"`offered={offered}`, `displayed={displayed}`, `accepted={accepted}`, "
        f"`dismissed={dismissed}`, `expanded={expanded}` are all product presentation events and "
        "are not produced by `_default_run`; they must not be interpreted as driver adherence.",
        f"The deterministic checkpoint identity repeats across runs: {len(repeated_ids)} checkpoint IDs "
        f"occur in more than one run ({sum(len(values) - 1 for values in repeated_ids.values())} extra "
        "run records). The audit therefore joins by `(run_id, checkpoint_id)`; any product join that "
        "uses checkpoint_id alone would be ambiguous.",
        "",
        "## Runtime checkpoint flow (verified)", "",
        "1. Existing solver/rule callsites call `AdviceActionBridge._capture_checkpoint` after the solver report is created (`src/gsm_sim/advice_bridge.py:597,747,903,950`; S4 is `src/gsm_sim/world.py:455`).",
        "2. `CheckpointTraceSink.capture` records an immutable snapshot, exact solver input/report and normalized checkpoint in RAM only (`src/gsm_sim/checkpoint_trace.py:128-213`). It does not call a solver or consume simulator RNG.",
        "3. Lifecycle is projected from `created` plus the policy event by `project_checkpoint_events` (`src/gsm_core/lifecycle/checkpoint.py:234-290`; `checkpoint_store.py:145-189` supplies the created event).",
        "4. `build_demo_trace` attaches only projected `ready` checkpoints to the first visible actor event at/after the checkpoint bucket; non-ready and same-time non-primary candidates are audit entries (`src/gsm_sim/demo_trace.py:176-251`).",
        "5. Product presentation is a separate boundary: `DemoSessionService._advice` bridges an existing trace checkpoint to `present_existing_checkpoint`, while the API service owns lease/offered/displayed/intent (`ui/backend/app/services/demo_session.py:323-408`; `ui/backend/app/services/advice_checkpoint.py:393-489`).",
        "",
        "## Canonical checkpoint catalog",
        "",
        "The catalog below is derived from the canonical taxonomy/normalizer and the actual producer callsites. `observed` is over the five runs; `0` means no producer output in this sample, not that the schema forbids the type.",
        "",
        "| Topic / source | Trigger and driver-facing purpose | Canonical/current/future action | Presentation/template | Observed | Risk / boundary |",
        "|---|---|---|---|---:|---|",
        "| `bonus_eligibility` / S1 | `check_bonus_gate` when acceptance/bonus progress is below a recoverable policy threshold; protect eligibility. | `PROTECT_ELIGIBILITY`; no future action required by normalizer. | READY if valid/actionable; otherwise suppressed. `S1_BONUS_PROGRESS`: “Bảo vệ điều kiện thưởng”, progress sentence and policy reason. | " + str(sum(item.get("topic") == "bonus_eligibility" for item in checkpoints)) + " | Numbers must be typed; do not call accepted an execution. |",
        "| `shift_timing` / S2 | `AdviceActionBridge.consult` after `shift_dp.solve`; schedules the current bucket and future buckets. | `ONLINE`, `SWAP`, `REST`, `END` as current; future plan is a separate list. | `S2_ONLINE_NOW[_SWAP_LATER]`, `S2_SWAP_NOW`, `S7_REST_WINDOW`, `S2_END_SHIFT`; policy may make maintenance silent. | " + str(sum(item.get("source_solver") == "S2" and item.get("topic") == "shift_timing" for item in checkpoints)) + " | Current/future wording must not be reversed. |",
        "| `energy` / S2 | Same S2 plan when current action is `SWAP`; energy continuity. | `SWAP`; future schedule may contain `ONLINE`/`REST`. | `S2_SWAP_NOW`: “Chuẩn bị đổi pin”. | " + str(sum(item.get("topic") == "energy" for item in checkpoints)) + " | Simulator trace can link a coincident segment, not causal execution. |",
        "| `rest` / S2 or S7 | S2 REST bucket or S7 notable rest-window recommendation; supports safe rest. | `REST`; future plan may resume `ONLINE`. | `S7_REST_WINDOW`: “Nghỉ trong khung này”. Moving driver is silent/queued at product boundary. | " + str(sum(item.get("topic") == "rest" for item in checkpoints)) + " | Do not display while enroute/on-trip; S7 is not an automatic rest command. |",
        "| `shift_boundary` / S2 or RULE | END/EXTEND boundary decisions. | `END` or `EXTEND`; current action owns the immediate boundary. | `S2_END_SHIFT` or `S2_EXTEND_SHIFT`. | " + str(sum(item.get("topic") == "shift_boundary" for item in checkpoints)) + " | No recap checkpoint is emitted by current simulator. |",
        "| `positioning_sim_only` / S4 | Allocation/standby assignment in simulator; not a product dispatch instruction. | `REPOSITION_SIM_ONLY`; simulator-only. | `S4_RELOCATE`: explicitly “chỉ mô phỏng”. | " + str(sum(item.get("topic") == "positioning_sim_only" for item in checkpoints)) + " | Must remain internal/simulator-only; no production card. |",
        "| `policy_info`, `safety_reserved` | Closed schema topics; no observed producer in these runs. Safety is trusted-server-only. | No canonical action generated by current trace. | No current template. | " + str(sum(item.get("topic") in {"policy_info", "safety_reserved"} for item in checkpoints)) + " | Do not invent a card to fill the demo. |",
        "",
        "## Actual driver-facing content and lifecycle rules", "",
        "- `CheckpointTemplateRegistry` owns deterministic title/summary/why (`src/gsm_core/advisor/checkpoint_templates.py:72-142`, version `checkpoint-template-v1`). The current/future boundary is explicit for `ONLINE` now + future `SWAP`.",
        "- The Web renders title, canonical action code, summary, action window, future plan, numbers and `MOCK/LIVE` provenance with DOM APIs (`ui/web/js/app.js:336-392`). It sends displayed only after mount and sends accepted/dismissed/expanded as intent events. `accepted` is not an execution link.",
        "- No checkpoint is represented by a silent response: no checkpoint/display IDs and no buttons (`ui/backend/app/services/demo_session.py:363-408`; `ui/contracts/advice_v2.json`). Moving actor state (`enroute`/`on_trip`) is passed to the bridge as `is_driving=True` and becomes silent `unsafe_while_moving`.",
        "- In this simulator trace, `execution_observed` is a side-channel matched post-run by `CheckpointTraceSink.finalize_execution_links` (`src/gsm_sim/checkpoint_trace.py:215-292`) with default relation `coincident` and confidence `0.6`; it is not evidence that an intent caused the segment.",
        "",
        "### Template wording currently in code",
        "",
        "| Action/context | Card title | Bây giờ / Sắp tới | Vì sao |",
        "|---|---|---|---|",
        "| `PROTECT_ELIGIBILITY` | Bảo vệ điều kiện thưởng | Bây giờ: Giữ nhịp để đạt mốc (hoặc giữ nhịp để bảo vệ điều kiện nếu thiếu typed number). | Lý do: tiến độ hiện tại chưa đủ theo chính sách. |",
        "| `ONLINE` + future `SWAP` | Tiếp tục online | Bây giờ: Tiếp tục online. Sắp tới: Cân nhắc/đổi pin trong khung kế tiếp. | Lý do: kế hoạch hiện tại giữ trạng thái online trước khi đổi pin. |",
        "| `SWAP` | Chuẩn bị đổi pin | Đổi pin trong cửa sổ được đề xuất. | Lý do: cần bảo vệ phần ca còn lại. |",
        "| `REST` | Nghỉ trong khung này | Nghỉ trong cửa sổ đang còn hiệu lực. | Lý do: kế hoạch đã tính trạng thái nghỉ và thời gian trong ca. |",
        "| `END` | Kết ca | Kết ca theo ranh giới kế hoạch hiện tại. | Lý do: chạy thêm không cải thiện kế hoạch hiện tại. |",
        "| `EXTEND` | Cân nhắc kéo dài ca | Kéo dài trong giới hạn đang hiển thị. | Lý do: mốc kế tiếp còn nằm trong trần kéo dài đã khóa. |",
        "| `REPOSITION_SIM_ONLY` | Tái định vị (chỉ mô phỏng) | Bây giờ: Tái định vị trong mô phỏng. | Lý do: tín hiệu positioning chỉ dùng cho simulator. |",
        "| `ONLINE` maintenance | Tiếp tục online | Bây giờ: Tiếp tục online. | Lý do: đây là trạng thái duy trì, không phải chỉ định vị trí. |",
        "",
        "### Presentation decision (policy, not a new demo rule)",
        "",
        "- `READY` + valid + primary + safe-to-read → product may create one lease/offered card; the simulator trace alone does not do that.",
        "- `QUEUED` / `unsafe_while_moving` → no text card while the actor is moving; the product bridge can retain a queue reason.",
        "- `SUPPRESSED`, expired, superseded, duplicate, missing validity/state, non-primary → silent/no fake IDs.",
        "- Maintenance `ONLINE` and low-evidence candidates may be policy-silent even when a normalized candidate exists.",
        "- Accepted/dismissed/expanded are UI intent; only a later execution observation can produce an execution link.",
        "",
        "## Lifecycle funnel (all sampled seeds)", "",
        "| Measure | Count | Interpretation |",
        "|---|---:|---|",
        f"| checkpoint records | {len(checkpoints)} | immutable records emitted by observer trace |",
        f"| created events | {event_counts.get('created', 0)} | one store-created event per checkpoint |",
        f"| final READY | {state_counts.get('ready', 0)} | policy accepted; not yet offered |",
        f"| final QUEUED | {state_counts.get('queued', 0)} | trace capture does not model moving at capture; product bridge can queue |",
        f"| final SUPPRESSED | {state_counts.get('suppressed', 0)} | policy/dedup/cadence/evidence gate |",
        f"| expired / superseded | {state_counts.get('expired', 0)} / {state_counts.get('superseded', 0)} | one expired trace record; no superseded record in this sample |",
        f"| offered / displayed | {offered} / {displayed} | absent because product lease/UI was not run in this analysis |",
        f"| accepted / dismissed / expanded | {accepted} / {dismissed} / {expanded} | absent; must be measured in Web session separately |",
        f"| execution observed | {executions} | post-run side-channel links/events; not adherence |",
        f"| no timeline attachment | {unattached} | includes non-ready and missing alignment at the Web projection boundary |",
        f"| duplicate timeline attachment | {duplicate} | count of checkpoint records attached to >1 transition |",
        "",
        "Capture-time actor state distribution (from `state_snapshot` artifacts): " +
        ", ".join(f"`{key}={value}`" for key, value in sorted(capture_state_counts.items())),
        "",
        "## Statistics by checkpoint type",
        "",
        "| Source | Topic | Action | Count | Share | Drivers | READY | READY rate | Suppressed | Execution observed | Validity mean (min) | Median gap (min) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in type_rows:
        lines.append("| " + " | ".join(_md(row.get(key)) for key in (
            "source_solver", "topic", "canonical_action", "count", "share_of_checkpoints",
            "driver_count", "ready", "ready_rate", "suppressed", "execution_observed",
            "mean_validity_minutes", "median_gap_minutes")) + " |")
    lines.extend([
        "",
        "## Statistics by driver",
        "",
        f"Observed driver rows: {len(actor_all)} unique actors across the seed set; actors with no checkpoint: {no_cp_count}.",
        "",
        "| Actor | Archetype | Fleet | Checkpoints | READY | Suppressed | Attached | First attached step | Median steps between attached | Topics | Two route legs |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ])
    for row in top_actors:
        lines.append("| " + " | ".join(_md(row.get(key)) for key in (
            "actor_id", "archetype", "fleet", "total_checkpoints", "ready", "suppressed",
            "attached", "first_attached_step", "median_steps_between_attached", "topics",
            "two_route_legs")) + " |")
    lines.extend([
        "",
        "## Frequency and distribution",
        "",
        f"- Checkpoints per unique actor (aggregated over seeds): min={min((int(row['total_checkpoints']) for row in actor_all), default=0)}, median={_median(int(row['total_checkpoints']) for row in actor_all)}, p75={_percentile((int(row['total_checkpoints']) for row in actor_all), 0.75)}, p90={_percentile((int(row['total_checkpoints']) for row in actor_all), 0.90)}, max={max((int(row['total_checkpoints']) for row in actor_all), default=0)}.",
        f"- First attached checkpoint step: median={_median(first_steps)}, p75={_percentile(first_steps, 0.75)}, p90={_percentile(first_steps, 0.90)}, max={max(first_steps, default='n/a')} (step is Web cursor sequence + 1, not wall-clock seconds).",
        f"- Intervals between same actor/topic checkpoint timestamps: median={_median(intervals)} minutes, p75={_percentile(intervals, 0.75)}, p90={_percentile(intervals, 0.90)}, max={max(intervals, default='n/a')}.",
        "- Checkpoints by simulator hour: " + ", ".join(f"{hour:02d}:00={hour_counts[hour]}" for hour in sorted(hour_counts)) + ".",
        "- Capture-time actor-state distribution is shown above; this sample captures all solver checkpoints while actors are `idle`. Transition-time states can differ and the product bridge re-checks moving safety.",
        "- Full time-of-day, driver-state and transition distributions are available in `checkpoint-timeline.json` and can be regenerated without changing dynamics; this report deliberately does not infer a production cadence from a one-day synthetic trace.",
        "",
        "## Real-data demo candidates",
        "",
        "The table below is generated from the sampled RunResults. `NOT_AVAILABLE` is an evidence result, not an invitation to manufacture a checkpoint. A scenario is considered short when the attached transition's sequence is at most five clicks from the actor's initial cursor.",
        "",
        "| Scenario | Availability | Seed | Actor | Checkpoint/type | Start transition | Steps | Driver state | Card/template | Execution side-channel | Reason |",
        "|---|---|---:|---:|---|---|---:|---|---|---|---|",
    ])
    for scenario in scenarios:
        checkpoint_id = scenario.get("checkpoint_id")
        cp_label = (f"{scenario.get('topic')} / {scenario.get('canonical_action')} / {checkpoint_id}"
                    if checkpoint_id else "—")
        card = (f"{scenario.get('card_title')}: {scenario.get('card_summary')}"
                if scenario.get("card_title") else "—")
        reason = scenario.get("reason") or "available from sampled trace"
        lines.append("| " + " | ".join(_md(value) for value in (
            scenario.get("scenario_name"), scenario.get("availability"), scenario.get("seed"),
            scenario.get("actor_id"), cp_label, scenario.get("transition_kind"),
            scenario.get("steps_to_checkpoint"), scenario.get("driver_state"), card,
            scenario.get("execution_observed"), reason)) + " |")
    lines.extend([
        "",
        "For an actual 3–5-click browser demonstration, choose an `AVAILABLE` checkpoint whose `steps_to_checkpoint <= 5` and then call the Web session API. The current sample does not produce queued, superseded, recap, or necessarily current/future `ONLINE→SWAP` cases; its single expired record is lifecycle-only. These remain open scenarios rather than synthetic fixtures.",
        "",
        "## Product-purpose classification",
        "",
        "- Driver-facing: S1 bonus eligibility, S2 energy/rest/shift timing and shift boundary when `READY`, valid, primary and the driver is safe to read.",
        "- Simulator/internal-only: S4 `positioning_sim_only`; the template itself says “chỉ mô phỏng” and should not become a production dispatch card.",
        "- Analytics-only: execution links and `execution_observed`; they are evidence for measurement, not a recommendation or acceptance state.",
        "- Not currently produced: `policy_info`, `safety_reserved`, recap surface. Do not create them solely for a demo.",
        "",
        "## Findings and risks",
        "",
        "1. **FACT:** Many records are suppressed by the policy, and the Web projection intentionally attaches only final `ready` records. A long wait for the first visible card can therefore be normal policy behavior, not automatically a trace bug (`evaluate_checkpoint` and `_prepare_checkpoint_attachments`).",
        "2. **IMPORTANT boundary:** `CheckpointTraceSink.capture` calls policy with `is_driving=False`; moving safety is enforced later in `DemoSessionService._advice` from the transition driver state. Trace `ready` is therefore not equivalent to a displayable card.",
        "3. **FACT:** The sampled simulator RunResult has no product `offered/displayed/accepted/dismissed/expanded`; these counts must be collected by a Web session audit, not inferred from simulator execution links.",
        "4. **RISK:** `execution_observed` links use default relation `coincident`/0.6. They cannot prove the checkpoint caused the segment, including when the action matches the actor's instinct.",
        "5. **OPEN:** The sampled runs expose one expired trace record but no superseded, queued or recap scenario. A scenario selector/Next Checkpoint control would be a product decision, not a justification to alter policy in this audit.",
        "6. **IMPORTANT identity evidence:** Deterministic `checkpoint_id` is intentionally stable for the same driver/fingerprint, so repeated IDs occur across runs. `run_id` is present and must remain part of every inventory/session join; the repeated-ID count is not duplicate attachment within one run.",
        "7. **IMPORTANT validity edge:** The one expired S2/SWAP record has `valid_until` earlier than `valid_from`; it is correctly non-displayable as `expired`, but this boundary should remain a regression case for product revalidation and must never acquire a lease.",
        "",
        "## Template and future LLM recommendation",
        "",
        "- Keep S1, ordinary S2 ONLINE/SWAP/REST/END/EXTEND, and S7 repeated advice on deterministic templates. They already have tested wording and typed code-owned actions/windows/numbers.",
        "- Keep S4 simulator-only and template-only; an LLM cannot turn a simulator signal into a production target.",
        "- Consider a future lazy LLM only for a verified complex current/future explanation or multiple caveats, after a real Web lease/display audit. No LLM was called for this inventory.",
        "",
        "## Open decisions for owner",
        "",
        "- Should the demo expose “Next checkpoint” or scenario selection, given policy-suppressed records and no guaranteed 3–5-click case for every topic?",
        "- Should product analytics persist a separate checkpoint-inventory view so offered/displayed/intent can be joined to these simulator records without treating execution as adherence?",
        "- Which evidence/owner decision is required before presenting `positioning_sim_only` or any safety-reserved channel to a human reviewer?",
        "- Should the trace explicitly record capture-time driver state for later comparison with product moving-state suppression? (This audit did not change it.)",
        "",
        "## Reproduction",
        "",
        "```text",
        "PYTHONPATH=src:ui/backend .venv/bin/python research/audit/2026-08-05-checkpoint-inventory/analyze_checkpoints.py --seeds 1000 1001 1002 1003 1004",
        "```",
        "",
        "Generated files: `checkpoint-by-actor.csv`, `checkpoint-by-type.csv`, `checkpoint-timeline.json`. No runtime, tracking claim, solver objective, cadence or UI file was modified by the analysis script.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1000, 1001, 1002, 1003, 1004])
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundles = [_run_bundle(seed) for seed in args.seeds]
    checkpoints = [item for bundle in bundles for item in bundle["checkpoints"]]
    actor_rows = [item for bundle in bundles for item in bundle["actors"]]
    type_rows = _aggregate_type_rows(checkpoints)
    scenarios = _choose_scenarios(bundles, checkpoints, actor_rows)
    timeline = {
        "analysis_version": "checkpoint-inventory-v1",
        "seeds": args.seeds,
        "run_ids": [bundle["run_id"] for bundle in bundles],
        "run_factory": "app.services.demo_session._default_run",
        "provenance": {"data_mode": "synthetic", "is_mock": True},
        "checkpoints": checkpoints,
        "transitions": [item for bundle in bundles for item in bundle["transitions"]],
        "checkpoint_audit": [item for bundle in bundles for item in bundle["audit"]],
        "scenarios": scenarios,
        "run_summaries": [{"seed": bundle["seed"], "run_id": bundle["run_id"],
                            "checkpoint_count": len(bundle["checkpoints"]),
                            "raw_event_counts": bundle["raw_event_counts"],
                            "raw_checkpoint_event_count": bundle["raw_checkpoint_event_count"],
                            "raw_execution_link_count": bundle["raw_execution_link_count"]}
                           for bundle in bundles],
    }
    (output / TIMELINE_JSON).write_text(
        json.dumps(timeline, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    _write_csv(output / ACTOR_CSV, actor_rows + _aggregate_actor_rows(actor_rows))
    _write_csv(output / TYPE_CSV, type_rows)
    (output / REPORT_NAME).write_text(
        _build_report(args.seeds, bundles, checkpoints, actor_rows, type_rows, scenarios),
        encoding="utf-8")
    print(json.dumps({
        "output": str(output), "seeds": args.seeds,
        "checkpoint_count": len(checkpoints),
        "type_count": len(type_rows),
        "actor_rows": len(actor_rows),
        "scenario_count": len(scenarios),
        "run_ids": [bundle["run_id"] for bundle in bundles],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
