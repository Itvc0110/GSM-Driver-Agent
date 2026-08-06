#!/usr/bin/env python3
"""Offline candidate-frequency analysis for AdviceCheckpoint expansion.

This module is deliberately an analysis harness, not a simulator producer or a
policy change.  It runs the same cached Web-demo factory used by the inventory
audit, reads the immutable RunResult, and estimates candidate touchpoints from
facts already present in the trace.  Thresholds used for proxies are explicitly
labelled proposals; they must not be copied into production policy without an
owner decision and a separate implementation cycle.

Example::

    PYTHONPATH=src:ui/backend .venv/bin/python \
      research/audit/2026-08-05-advice-expansion/analyze_advice_expansion.py \
      --seeds 1000 1001 1002 1003 1004
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from app.services.demo_session import _default_run
from gsm_core.lifecycle.checkpoint import project_checkpoint_events
from gsm_sim.demo_trace import build_demo_trace


OUT_DIR = Path(__file__).resolve().parent
SUMMARY_JSON = OUT_DIR / "advice-expansion-summary.json"
CANDIDATE_CSV = OUT_DIR / "candidate-frequency.csv"
ACTOR_CSV = OUT_DIR / "candidate-by-actor.csv"

# These are analysis proposals, not production policy values.  The report keeps
# them visible so an owner can change or reject them without a hidden threshold.
INCOME_LOW_RATIO = 0.80
INCOME_HIGH_RATIO = 1.20
IDLE_GAP_PROPOSAL_MIN = 30.0
EMPTY_SHARE_PROPOSAL = 0.40
MIN_TRIPS_FOR_EFFICIENCY = 3
SWAP_SOON_FUTURE_BUCKETS = 2

# Cadence values below are dry-run controls only.  They are intentionally not
# the production AdviceCadencePolicy and must be approved before implementation.
CANDIDATE_COOLDOWN_MIN = {
    "pre_shift_plan": 0.0,
    "bonus_progress": 60.0,
    "swap_now": 60.0,
    "swap_soon": 120.0,
    "planned_rest": 60.0,
    "income_pace": 120.0,
    "long_idle": 120.0,
    "empty_efficiency": 180.0,
    "plan_deviation": 120.0,
    "post_shift_recap": 0.0,
}


def _payload(artifact: dict[str, Any] | None) -> dict[str, Any]:
    return dict((artifact or {}).get("payload") or {})


def _minute(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.hour * 60.0 + parsed.minute + parsed.second / 60.0 + parsed.microsecond / 60_000_000.0
    except (TypeError, ValueError, OSError):
        return None


def _percentile(values: Iterable[float], p: float) -> float | None:
    data = sorted(float(v) for v in values if v is not None)
    if not data:
        return None
    if len(data) == 1:
        return round(data[0], 3)
    pos = (len(data) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(data) - 1)
    return round(data[lo] + (data[hi] - data[lo]) * (pos - lo), 3)


def _median(values: Iterable[float]) -> float | None:
    data = [float(v) for v in values if v is not None]
    return round(statistics.median(data), 3) if data else None


def _event_kind(event: Any) -> str:
    return str(getattr(event, "kind", event.get("kind", ""))) if isinstance(event, dict) else str(getattr(event, "kind", ""))


def _event_actor(event: Any) -> int:
    return int(event.get("actor_id", -1)) if isinstance(event, dict) else int(getattr(event, "actor_id", -1))


def _event_time(event: Any) -> float:
    return float(event.get("t_min", 0.0)) if isinstance(event, dict) else float(getattr(event, "t_min", 0.0))


def _event_detail(event: Any) -> dict[str, Any]:
    return dict(event.get("detail") or {}) if isinstance(event, dict) else dict(getattr(event, "detail", {}) or {})


def _cp_state(events: list[dict[str, Any]], fallback: str | None) -> str:
    if not events:
        return str(fallback or "unknown")
    try:
        return str(project_checkpoint_events(events)["state"])
    except Exception:
        return str(fallback or "unknown")


def _cp_key(run_id: str, checkpoint_id: str) -> tuple[str, str]:
    return run_id, checkpoint_id


def _future_codes(cp: dict[str, Any]) -> list[str]:
    return [str(item.get("code")) for item in cp.get("future_plan") or [] if item.get("code")]


def _haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Small analysis-only distance helper for segment ratios."""
    lat1, lon1 = math.radians(float(a["lat"])), math.radians(float(a["lon"]))
    lat2, lon2 = math.radians(float(b["lat"])), math.radians(float(b["lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def _safe_json(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(v) for v in value]
    return str(value)


def _add_candidate(bucket: list[dict[str, Any]], *, seed: int, run_id: str,
                   actor_id: int, candidate_type: str, t_min: float | None,
                   source: str, status: str, overlap: bool = False,
                   reason: str | None = None, safe: bool = True,
                   presentation: str = "proactive") -> None:
    bucket.append({
        "seed": seed,
        "run_id": run_id,
        "actor_id": actor_id,
        "candidate_type": candidate_type,
        "t_min": round(float(t_min), 3) if t_min is not None else None,
        "source": source,
        "status": status,
        "overlap_existing": bool(overlap),
        "safe_at_estimate": bool(safe),
        "reason": reason,
        "presentation": presentation,
    })


def _first_transition_at(transitions: list[dict[str, Any]], target: float) -> dict[str, Any] | None:
    return next((t for t in transitions if float(t.get("t_min", 0.0)) >= target), None)


def _state_at(transitions: list[dict[str, Any]], target: float) -> str | None:
    if not transitions:
        return None
    previous = None
    for transition in transitions:
        if float(transition.get("t_min", 0.0)) > target:
            break
        previous = transition
    chosen = previous or transitions[0]
    return str((chosen.get("driver") or {}).get("state") or "")


def _actual_action_in_bucket(events: list[Any], start: float, end: float) -> str | None:
    kinds = {_event_kind(e) for e in events if start <= _event_time(e) < end}
    if "go_swap" in kinds or "swap_done" in kinds:
        return "SWAP"
    if "rest" in kinds:
        return "REST"
    if "end_shift" in kinds:
        return "END"
    if "go_online" in kinds or "order_matched" in kinds or "pickup" in kinds:
        return "ONLINE"
    return None


def _run(seed: int) -> dict[str, Any]:
    result = _default_run(int(seed))
    run_id = str(getattr(result, "run_id", ""))
    artifacts = {
        str(item.get("artifact_id")): item
        for item in getattr(result, "advice_artifacts", [])
    }
    raw_events = [dict(item) for item in getattr(result, "advice_checkpoint_events", [])]
    events_by_cp: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in raw_events:
        events_by_cp[_cp_key(run_id, str(event.get("checkpoint_id")))].append(event)
    checkpoints: list[dict[str, Any]] = []
    for raw in getattr(result, "advice_checkpoints", []):
        cp = dict(raw)
        key = _cp_key(run_id, str(cp.get("checkpoint_id")))
        cp["state"] = _cp_state(events_by_cp[key], cp.get("state"))
        cp["snapshot_payload"] = _payload(artifacts.get(str(cp.get("snapshot_ref"))))
        report_ref = (cp.get("solver_report_refs") or [None])[0]
        cp["solver_report_payload"] = _payload(artifacts.get(str(report_ref)))
        cp["solver_input_payload"] = _payload(artifacts.get(str((cp.get("solver_input_refs") or [None])[0])))
        checkpoints.append(cp)

    events_by_actor: dict[int, list[Any]] = defaultdict(list)
    for event in getattr(result, "events", []):
        events_by_actor[_event_actor(event)].append(event)
    for events in events_by_actor.values():
        events.sort(key=_event_time)

    traces: dict[int, dict[str, Any]] = {}
    transitions_by_actor: dict[int, list[dict[str, Any]]] = {}
    for actor in getattr(result, "actors", []):
        aid = int(actor.actor_id)
        trace = build_demo_trace(result, aid)
        traces[aid] = trace
        transitions_by_actor[aid] = list(trace.get("transitions") or [])

    checkpoint_by_actor: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cp in checkpoints:
        aid = int(str(cp.get("driver_id", "d--1")).removeprefix("d-"))
        checkpoint_by_actor[aid].append(cp)
    for cps in checkpoint_by_actor.values():
        cps.sort(key=lambda cp: _minute(cp.get("created_at")) or 0.0)

    candidate_rows: list[dict[str, Any]] = []
    actor_rows: list[dict[str, Any]] = []
    actor_map = {int(actor.actor_id): actor for actor in getattr(result, "actors", [])}
    event_kinds = {
        aid: [_event_kind(event) for event in events]
        for aid, events in events_by_actor.items()
    }

    for aid, actor in sorted(actor_map.items()):
        actor_events = events_by_actor.get(aid, [])
        transitions = transitions_by_actor.get(aid, [])
        cps = checkpoint_by_actor.get(aid, [])
        first_online = next((e for e in actor_events if _event_kind(e) == "go_online"), None)
        first_online_t = _event_time(first_online) if first_online is not None else float(actor.shift_start_min)
        shift_start = float(actor.shift_start_min)
        shift_end = float(actor.shift_end_min)
        duration = max(0.0, shift_end - shift_start)
        s2 = [cp for cp in cps if "S2" in (cp.get("solver_set") or [])]
        s1 = [cp for cp in cps if cp.get("topic") == "bonus_eligibility"]
        energy = [cp for cp in cps if cp.get("topic") == "energy" and
                  (cp.get("current_action") or {}).get("code") == "SWAP"]
        rest = [cp for cp in cps if cp.get("topic") == "rest" and
                (cp.get("current_action") or {}).get("code") == "REST"]
        online = [cp for cp in cps if cp.get("topic") == "shift_timing" and
                  (cp.get("current_action") or {}).get("code") == "ONLINE"]

        # One brief per actor/run is a product artifact candidate, not a nudge.
        _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                       candidate_type="pre_shift_plan", t_min=first_online_t,
                       source="actor+first_S2_report", status="available",
                       presentation="brief")

        for cp in s1:
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="bonus_progress", t_min=_minute(cp.get("created_at")),
                           source="existing_S1", status=cp.get("state", "unknown"),
                           overlap=True, reason=str((cp.get("solver_report_payload") or {})
                                                    .get("solution", {}).get("infeasible_reason") or "progress"))
        for cp in energy:
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="swap_now", t_min=_minute(cp.get("created_at")),
                           source="existing_S2", status=cp.get("state", "unknown"), overlap=True)
        for cp in rest:
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="planned_rest", t_min=_minute(cp.get("created_at")),
                           source="existing_S2", status=cp.get("state", "unknown"), overlap=True)

        # A future SWAP already exists in the silent ONLINE plan records.  Keep the
        # first material signal for this actor/run so this estimate does not count
        # repeated polling as repeated advice.
        swap_soon = [cp for cp in online if "SWAP" in _future_codes(cp)[:SWAP_SOON_FUTURE_BUCKETS]]
        for index, cp in enumerate(swap_soon):
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="swap_soon", t_min=_minute(cp.get("created_at")),
                           source="existing_S2_ONLINE_future_plan", status="raw" if index else "available",
                           overlap=True, reason="future_SWAP_in_next_two_buckets")

        # Income pace proxy: compare the state at the middle of the shift with
        # the first S2 forecast.  This is intentionally a proposal, not a policy.
        first_s2 = s2[0] if s2 else None
        report_solution = (first_s2 or {}).get("solver_report_payload", {}).get("solution", {})
        expected = float(report_solution.get("expected_payout") or 0.0)
        midpoint = _first_transition_at(transitions, shift_start + duration * 0.5)
        if midpoint is not None and expected > 0.0 and duration > 0:
            driver = midpoint.get("driver") or {}
            elapsed = max(0.0, min(duration, float(midpoint.get("t_min", shift_start)) - shift_start))
            expected_to_date = expected * (elapsed / duration)
            actual = float(driver.get("payout_vnd") or 0.0)
            ratio = actual / expected_to_date if expected_to_date > 0 else 1.0
            if ratio <= INCOME_LOW_RATIO or ratio >= INCOME_HIGH_RATIO:
                label = "behind_plan" if ratio <= INCOME_LOW_RATIO else "ahead_of_plan"
                _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                               candidate_type="income_pace", t_min=float(midpoint.get("t_min", 0.0)),
                               source="snapshot+first_S2_forecast", status="proxy",
                               reason=f"{label};ratio={ratio:.3f}",
                               safe=str((driver or {}).get("state") or "") not in {"enroute", "on_trip"})

        # Plan-deviation proxy: compare the first S2 current action with the
        # action observed during its 60-minute bucket.  A proper producer needs
        # a transition-time plan state and must not infer causality from this audit.
        if first_s2 is not None:
            current = str((first_s2.get("current_action") or {}).get("code") or "")
            t0 = _minute(first_s2.get("created_at"))
            actual = _actual_action_in_bucket(actor_events, t0 or shift_start, (t0 or shift_start) + 60.0)
            if actual and current and actual != current:
                _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                               candidate_type="plan_deviation", t_min=t0,
                               source="first_S2+observed_events", status="proxy",
                               reason=f"planned={current};observed={actual}",
                               safe=_state_at(transitions, t0 or shift_start) not in {"enroute", "on_trip"})

        # Long-idle proxy: gaps after a completed trip and before the next
        # accepted order.  The current observer does not persist idle_streak_min,
        # so this cannot be promoted without adding a canonical trace field.
        boundaries = [e for e in actor_events if _event_kind(e) in {"go_online", "dropoff"}]
        matches = [e for e in actor_events if _event_kind(e) == "order_matched"]
        for previous in boundaries:
            next_match = next((e for e in matches if _event_time(e) > _event_time(previous)), None)
            if next_match is None:
                continue
            gap = _event_time(next_match) - _event_time(previous)
            if gap >= IDLE_GAP_PROPOSAL_MIN:
                _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                               candidate_type="long_idle", t_min=_event_time(previous),
                               source="event_gap_proxy", status="proxy",
                               reason=f"gap_min={gap:.3f}",
                               safe=_state_at(transitions, _event_time(previous)) not in {"enroute", "on_trip"})

        # Empty efficiency proxy at shift midpoint: relocate + pickup-enroute
        # duration divided by empty + occupied segment duration.  Segments are
        # canonical simulation observations, but the threshold is still a proposal.
        midpoint_t = shift_start + duration * 0.5
        segs = [dict(s) for s in getattr(result, "segments", []) if int(s.get("actor_id", -1)) == aid]
        empty = occupied = 0.0
        for segment in segs:
            t0, t1 = float(segment.get("t0", 0.0)), float(segment.get("t1", 0.0))
            if t0 >= midpoint_t:
                continue
            end = min(t1, midpoint_t)
            minutes = max(0.0, end - t0)
            if segment.get("kind") in {"relocate", "enroute"}:
                empty += minutes
            elif segment.get("kind") == "on_trip":
                occupied += minutes
        mid_transition = _first_transition_at(transitions, midpoint_t)
        trips = int(((mid_transition or {}).get("driver") or {}).get("trips_done") or 0)
        ratio = empty / (empty + occupied) if empty + occupied > 0 else None
        if ratio is not None and trips >= MIN_TRIPS_FOR_EFFICIENCY and ratio >= EMPTY_SHARE_PROPOSAL:
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="empty_efficiency", t_min=midpoint_t,
                           source="segments+snapshot", status="proxy",
                           reason=f"empty_share={ratio:.3f};trips={trips}",
                           safe=_state_at(transitions, midpoint_t) not in {"enroute", "on_trip"})

        # End-of-shift recap is a passive artifact candidate; it is not an END
        # recommendation.  Censored runs still have a clear report boundary.
        end_event = next((e for e in reversed(actor_events)
                          if _event_kind(e) in {"end_shift", "censored_end_of_run", "day_end_settle"}), None)
        if end_event is not None:
            _add_candidate(candidate_rows, seed=seed, run_id=run_id, actor_id=aid,
                           candidate_type="post_shift_recap", t_min=_event_time(end_event),
                           source="final_actor_snapshot+events", status="available",
                           presentation="recap")

        actor_rows.append({
            "seed": seed,
            "run_id": run_id,
            "actor_id": aid,
            "archetype": str(actor.archetype),
            "fleet": str(getattr(getattr(actor, "fleet", None), "value", getattr(actor, "fleet", ""))),
            "shift_start_min": round(shift_start, 3),
            "shift_end_min": round(shift_end, 3),
            "shift_duration_min": round(duration, 3),
            "existing_checkpoints": len(cps),
            "existing_ready": sum(cp.get("state") == "ready" for cp in cps),
            "existing_suppressed": sum(cp.get("state") == "suppressed" for cp in cps),
            "existing_expired": sum(cp.get("state") == "expired" for cp in cps),
            "existing_bonus": len(s1),
            "existing_swap_now": len(energy),
            "existing_rest": len(rest),
            "existing_online_suppressed": sum(cp.get("state") == "suppressed" for cp in online),
            "has_two_route_legs": int(any(
                (t.get("trip") or {}).get("state") in {"MATCHED", "PICKED_UP", "COMPLETED"}
                for t in transitions
            )),
        })

    return {
        "seed": seed,
        "run_id": run_id,
        "checkpoint_count": len(checkpoints),
        "checkpoint_states": dict(Counter(cp.get("state") for cp in checkpoints)),
        "raw_checkpoint_events": len(raw_events),
        "execution_links": len(getattr(result, "execution_links", [])),
        "candidate_rows": candidate_rows,
        "actor_rows": actor_rows,
    }


def _aggregate(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = [row for run in runs for row in run["candidate_rows"]]
    actors = [row for run in runs for row in run["actor_rows"]]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[row["candidate_type"]].append(row)
    actor_keys = {(row["run_id"], row["actor_id"]) for row in actors}
    out: list[dict[str, Any]] = []
    for candidate_type, rows in sorted(grouped.items()):
        per_actor = Counter((r["run_id"], r["actor_id"]) for r in rows)
        unique = len(per_actor)
        cooldown = float(CANDIDATE_COOLDOWN_MIN.get(candidate_type, 60.0))
        rows_by_actor: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            rows_by_actor[(str(row["run_id"]), int(row["actor_id"]))].append(row)
        kept_rows: list[dict[str, Any]] = []
        safety_blocked = cooldown_blocked = dedup_blocked = 0
        for key, actor_rows in rows_by_actor.items():
            actor_rows.sort(key=lambda row: row.get("t_min") if row.get("t_min") is not None else float("inf"))
            last_kept: float | None = None
            for row in actor_rows:
                if not row.get("safe_at_estimate", True):
                    safety_blocked += 1
                    continue
                t_min = row.get("t_min")
                if last_kept is not None and t_min is not None and (float(t_min) - last_kept) < cooldown:
                    cooldown_blocked += 1
                    continue
                # For the existing checkpoint families, an immutable material
                # record is already a dedup unit.  For new proxy rows, the
                # cooldown above is the dry-run dedup gate.
                kept_rows.append(row)
                if t_min is not None:
                    last_kept = float(t_min)
            if candidate_type in {"pre_shift_plan", "post_shift_recap"} and len(actor_rows) > 1:
                dedup_blocked += max(0, len(actor_rows) - 1)
        kept = len(kept_rows)
        kept_counts = Counter((r["run_id"], r["actor_id"]) for r in kept_rows)
        counts = list(kept_counts.values())
        overlap = sum(bool(r["overlap_existing"]) for r in rows)
        safe = sum(bool(r["safe_at_estimate"]) for r in rows)
        out.append({
            "candidate_type": candidate_type,
            "raw_candidates": len(rows),
            "unique_driver_runs": unique,
            "dedup_kept_touchpoints": kept,
            "driver_runs_total": len(actor_keys),
            "coverage_rate": round(unique / len(actor_keys), 6) if actor_keys else None,
            "mean_per_driver_run": round(kept / len(actor_keys), 6) if actor_keys else None,
            "p50_per_covered_driver": _percentile(counts, 0.50),
            "p75_per_covered_driver": _percentile(counts, 0.75),
            "p90_per_covered_driver": _percentile(counts, 0.90),
            "max_per_covered_driver": max(counts) if counts else 0,
            "overlap_existing_records": overlap,
            "additional_not_existing": sum(1 for r in kept_rows if not r["overlap_existing"]),
            "safety_blocked": safety_blocked,
            "cooldown_blocked": cooldown_blocked,
            "dedup_blocked": dedup_blocked,
            "safe_estimate_records": safe,
            "cooldown_proposal_min": cooldown,
            "proxy_thresholds": {
                "income_low_ratio": INCOME_LOW_RATIO if candidate_type == "income_pace" else None,
                "income_high_ratio": INCOME_HIGH_RATIO if candidate_type == "income_pace" else None,
                "idle_gap_min": IDLE_GAP_PROPOSAL_MIN if candidate_type == "long_idle" else None,
                "empty_share": EMPTY_SHARE_PROPOSAL if candidate_type == "empty_efficiency" else None,
                "swap_future_buckets": SWAP_SOON_FUTURE_BUCKETS if candidate_type == "swap_soon" else None,
            },
        })
    return out, actors


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: row.get(key) for key in fields} for row in rows])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[1000, 1001, 1002, 1003, 1004])
    args = parser.parse_args()
    runs = [_run(seed) for seed in args.seeds]
    candidate_rows, actor_rows = _aggregate(runs)
    total_driver_runs = len(actor_rows)
    baseline = {
        "runs": len(runs),
        "seeds": list(args.seeds),
        "driver_runs": total_driver_runs,
        "checkpoint_created": sum(run["checkpoint_count"] for run in runs),
        "checkpoint_states": dict(Counter(
            state for run in runs for state, count in run["checkpoint_states"].items()
            for _ in range(int(count))
        )),
        "checkpoint_per_driver_run": round(
            sum(run["checkpoint_count"] for run in runs) / total_driver_runs, 6
        ) if total_driver_runs else None,
        "ready_per_driver_run": round(sum(
            run["checkpoint_states"].get("ready", 0) for run in runs
        ) / total_driver_runs, 6) if total_driver_runs else None,
        "execution_links": sum(run["execution_links"] for run in runs),
    }
    summary = {
        "analysis_version": "advice-expansion-candidates-v1",
        "provenance": {
            "run_factory": "app.services.demo_session._default_run",
            "data_mode": "synthetic",
            "is_mock": True,
            "policy_mutated": False,
            "external_api_called": False,
            "llm_called": False,
        },
        "baseline": baseline,
        "proxy_thresholds": {
            "income_low_ratio": INCOME_LOW_RATIO,
            "income_high_ratio": INCOME_HIGH_RATIO,
            "idle_gap_min": IDLE_GAP_PROPOSAL_MIN,
            "empty_share": EMPTY_SHARE_PROPOSAL,
            "min_trips_for_efficiency": MIN_TRIPS_FOR_EFFICIENCY,
            "swap_future_buckets": SWAP_SOON_FUTURE_BUCKETS,
        },
        "candidate_frequency": candidate_rows,
        "candidate_instances": [row for run in runs for row in run["candidate_rows"]],
        "run_summaries": [{k: v for k, v in run.items()
                           if k not in {"candidate_rows", "actor_rows"}} for run in runs],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(_safe_json(summary), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(CANDIDATE_CSV, candidate_rows)
    _write_csv(ACTOR_CSV, actor_rows)
    print(json.dumps({
        "output": str(OUT_DIR),
        "seeds": args.seeds,
        "driver_runs": total_driver_runs,
        "checkpoint_created": baseline["checkpoint_created"],
        "ready": baseline["checkpoint_states"].get("ready", 0),
        "candidate_types": len(candidate_rows),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
