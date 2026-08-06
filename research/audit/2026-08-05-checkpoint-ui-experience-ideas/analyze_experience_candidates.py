#!/usr/bin/env python3
"""Measure UI-experience derived states without changing simulator behavior.

This observer deliberately measures *episodes and windows*, not raw-signal inventory.
All thresholds are discovery probes only and are emitted in the artifact as non-policy.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import polars as pl

from app.services.demo_session import _default_run
from gsm_core.lifecycle.checkpoint import project_checkpoint_events
from gsm_sim.demo_trace import minute_from_iso
from gsm_sim.journey import build_journey


DEFAULT_OUT = Path(__file__).resolve().parent


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))
    return round(float(ordered[index]), 3)


def _state_map(result: Any) -> dict[str, str]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in result.advice_checkpoint_events:
        grouped[str(event["checkpoint_id"])].append(event)
    return {
        str(checkpoint["checkpoint_id"]): str(
            project_checkpoint_events(grouped[str(checkpoint["checkpoint_id"])])["state"]
        )
        for checkpoint in result.advice_checkpoints
    }


def _checkpoint_min(checkpoint: dict) -> float:
    validity = checkpoint.get("validity") or {}
    return float(minute_from_iso(validity.get("valid_from") or checkpoint.get("created_at")) or 0)


def _future_head(checkpoint: dict) -> tuple[str | None, str | None, str | None]:
    plan = checkpoint.get("future_plan") or []
    head = next((step for step in plan if isinstance(step, dict) and step.get("code")), {})
    window = head.get("window") or {}
    return head.get("code"), window.get("start"), window.get("end")


def _overlap(block: Any, lo: float, hi: float) -> float:
    return max(0.0, min(float(block.t1), hi) - max(float(block.t0), lo))


def _simulator_patterns(seeds: list[int]) -> dict[str, Any]:
    observations: dict[str, list[dict]] = defaultdict(list)

    def add(name: str, seed: int, actor: Any, at_min: float, **detail: Any) -> None:
        observations[name].append({
            "seed": seed,
            "actor_id": int(actor.actor_id),
            "archetype": str(actor.archetype),
            "at_min": round(float(at_min), 3),
            "shift_start_min": round(float(actor.shift_start_min), 3),
            "shift_end_min": round(float(actor.shift_end_min), 3),
            **detail,
        })

    for seed in seeds:
        result = _default_run(seed)
        states = _state_map(result)
        events_by_actor: dict[int, list[Any]] = defaultdict(list)
        checkpoints_by_actor: dict[int, list[dict]] = defaultdict(list)
        execution_ids = {str(link.get("checkpoint_id")) for link in result.execution_links}
        for event in result.events:
            if int(event.actor_id) >= 0:
                events_by_actor[int(event.actor_id)].append(event)
        for checkpoint in result.advice_checkpoints:
            actor_id = int(str(checkpoint["driver_id"]).removeprefix("d-"))
            checkpoints_by_actor[actor_id].append(checkpoint)

        for actor in result.actors:
            actor_id = int(actor.actor_id)
            events = sorted(events_by_actor[actor_id], key=lambda item: item.t_min)
            checkpoints = sorted(checkpoints_by_actor[actor_id], key=_checkpoint_min)
            ready = [c for c in checkpoints if states[str(c["checkpoint_id"])] == "ready"]
            s2 = [c for c in checkpoints if "S2" in (c.get("solver_set") or [])]
            journey = build_journey(result, actor_id)
            idle_blocks = [b for b in journey.timeline if b.kind == "idle" and b.minutes >= 30]
            event_times: dict[str, list[float]] = defaultdict(list)
            for event in events:
                event_times[str(event.kind)].append(float(event.t_min))

            if not ready:
                add("quiet_shift_with_recap", seed, actor, actor.shift_end_min)
            if len(ready) >= 2:
                add("multiple_ready_touchpoints", seed, actor, _checkpoint_min(ready[1]),
                    count=len(ready))
            topics = {str(c.get("topic")) for c in ready}
            if len(topics) >= 2:
                add("multiple_ready_topics", seed, actor, _checkpoint_min(ready[-1]),
                    topics=sorted(topics))

            semantic_changes: list[float] = []
            window_changes: list[float] = []
            previous_semantic = previous_window = None
            for checkpoint in s2:
                current = (checkpoint.get("current_action") or {}).get("code")
                future_code, future_start, future_end = _future_head(checkpoint)
                semantic = (current, future_code)
                window = (current, future_code, future_start, future_end)
                at_min = _checkpoint_min(checkpoint)
                if previous_semantic is not None and semantic != previous_semantic:
                    semantic_changes.append(at_min)
                    add("semantic_plan_revision", seed, actor, at_min,
                        current=current, future=future_code)
                if previous_window is not None and window != previous_window:
                    window_changes.append(at_min)
                    add("plan_window_revision", seed, actor, at_min)
                previous_semantic, previous_window = semantic, window

            for i, at_min in enumerate(semantic_changes):
                if len([t for t in semantic_changes if at_min - 120 <= t <= at_min]) >= 3:
                    add("plan_churn_3_in_120m", seed, actor, at_min)
                    break

            disruption_times = sorted(
                event_times["order_skipped_soc"]
                + event_times["order_cancelled_after_accept"]
                + event_times["swap_failed"]
            )
            for disruption in disruption_times:
                later = next((t for t in semantic_changes if disruption < t <= disruption + 60), None)
                if later is not None:
                    add("plan_revision_after_disruption_60m", seed, actor, later,
                        disruption_min=round(disruption, 3))

            action_events = {"SWAP": event_times["go_swap"], "REST": event_times["rest"],
                             "END": event_times["end_shift"]}
            for checkpoint in ready:
                action = (checkpoint.get("current_action") or {}).get("code")
                if action not in action_events:
                    continue
                start = _checkpoint_min(checkpoint)
                validity = checkpoint.get("validity") or {}
                end = float(minute_from_iso(validity.get("valid_until")) or start)
                observed = next((t for t in action_events[action] if start <= t <= end), None)
                if observed is not None:
                    add("ready_action_observed_in_validity", seed, actor, observed, action=action)
                else:
                    late = next((t for t in action_events[action] if end < t <= end + 60), None)
                    if late is not None:
                        add("ready_action_observed_late_60m", seed, actor, late, action=action)

            future_windows_seen: set[tuple] = set()
            for checkpoint in s2:
                current = (checkpoint.get("current_action") or {}).get("code")
                future_code, future_start, future_end = _future_head(checkpoint)
                if current != "ONLINE" or future_code != "SWAP" or not future_start or not future_end:
                    continue
                start = float(minute_from_iso(future_start) or 0)
                end = float(minute_from_iso(future_end) or start)
                key = (start, end)
                if key in future_windows_seen:
                    continue
                future_windows_seen.add(key)
                observed = next((t for t in event_times["go_swap"] if start <= t <= end), None)
                if observed is not None:
                    add("future_swap_observed_in_window", seed, actor, observed,
                        window_start=start, window_end=end)

            for skipped in event_times["order_skipped_soc"]:
                swap = next((t for t in event_times["go_swap"] if skipped < t <= skipped + 90), None)
                name = "energy_disruption_recovered_90m" if swap is not None else "energy_disruption_unrecovered_90m"
                add(name, seed, actor, swap if swap is not None else skipped, skipped_min=skipped)
            for event in events:
                if event.kind == "swap_failed" or (
                    event.kind == "swap_done" and float(event.detail.get("wait_min") or 0) > 5
                ):
                    add("swap_friction_episode", seed, actor, event.t_min,
                        kind=event.kind, wait_min=event.detail.get("wait_min"))

            for block in idle_blocks:
                add("long_idle_window_30m", seed, actor, block.t1, minutes=round(block.minutes, 3))
                rest = next((t for t in event_times["rest"] if block.t1 < t <= block.t1 + 60), None)
                if rest is not None:
                    add("long_idle_then_rest_60m", seed, actor, rest,
                        idle_end=block.t1)
            if len(idle_blocks) >= 2:
                add("repeated_long_idle_windows", seed, actor, idle_blocks[1].t1,
                    count=len(idle_blocks))
            if idle_blocks and event_times["rest"]:
                add("idle_and_rest_same_shift", seed, actor, event_times["rest"][0])

            lo, hi = float(actor.shift_start_min), float(actor.shift_end_min)
            mid = (lo + hi) / 2
            halves = []
            for a, b in ((lo, mid), (mid, hi)):
                occupied = sum(_overlap(block, a, b) for block in journey.timeline
                               if block.kind == "on_trip")
                empty = sum(_overlap(block, a, b) for block in journey.timeline
                            if block.kind in {"enroute", "relocate"})
                active = occupied + empty
                halves.append((occupied / active if active else 0.0,
                               empty / active if active else 0.0))
            if abs(halves[1][0] - halves[0][0]) >= 0.15:
                add("utilization_phase_shift_15pp", seed, actor, mid,
                    early=round(halves[0][0], 3), late=round(halves[1][0], 3))
            if halves[1][1] - halves[0][1] >= 0.15:
                add("empty_share_rising_15pp", seed, actor, mid,
                    early=round(halves[0][1], 3), late=round(halves[1][1], 3))

            for kind, name in (("order_cancelled_after_accept", "cancellation_cluster_2_in_120m"),
                               ("order_declined", "decline_cluster_2_in_120m")):
                times = event_times[kind]
                if any(len([x for x in times if t <= x <= t + 120]) >= 2 for t in times):
                    add(name, seed, actor, times[-1], count=len(times))

            s1_ready = [c for c in ready if "S1" in (c.get("solver_set") or [])]
            if s1_ready and event_times["mission_completed"]:
                add("bonus_and_mission_same_shift", seed, actor,
                    event_times["mission_completed"][0])
            energy_times = sorted(event_times["order_skipped_soc"] + event_times["go_swap"])
            if any(abs(mission - energy) <= 60 for mission in event_times["mission_completed"]
                   for energy in energy_times):
                add("mission_and_energy_overlap_60m", seed, actor,
                    event_times["mission_completed"][0])

            money = journey.metrics
            source_values = [money["trip_payout_vnd"], money["day_bonus_vnd"],
                             money["mission_reward_vnd"], money["newbie_vnd"]]
            if sum(value > 0 for value in source_values) >= 2:
                add("multiple_income_sources", seed, actor, actor.shift_end_min,
                    source_count=sum(value > 0 for value in source_values))
            if float(money["bonus_share"]) >= 0.2:
                add("incentive_share_20pct", seed, actor, actor.shift_end_min,
                    share=money["bonus_share"])
            if any(t >= actor.shift_end_min - 90 for t in energy_times):
                add("late_shift_energy_pressure_90m", seed, actor, energy_times[-1])
            if any(str(c["checkpoint_id"]) in execution_ids for c in ready):
                add("ready_checkpoint_with_execution_link", seed, actor,
                    _checkpoint_min(ready[0]))

    summaries = []
    for name, rows in sorted(observations.items()):
        actor_runs = {(row["seed"], row["actor_id"]) for row in rows}
        archetype_actor_runs: dict[str, set[tuple[int, int]]] = defaultdict(set)
        for row in rows:
            archetype_actor_runs[row["archetype"]].add((row["seed"], row["actor_id"]))
        relative = []
        phases = Counter()
        for row in rows:
            duration = max(1.0, row["shift_end_min"] - row["shift_start_min"])
            fraction = (row["at_min"] - row["shift_start_min"]) / duration
            relative.append(fraction)
            phases["early" if fraction < 1 / 3 else "mid" if fraction < 2 / 3 else "late"] += 1
        summaries.append({
            "derived_state": name,
            "candidate_occurrences": len(rows),
            "actor_runs": len(actor_runs),
            "archetype_actor_runs": {
                archetype: len(items)
                for archetype, items in sorted(archetype_actor_runs.items())
            },
            "shift_fraction_p50": _pct(relative, 0.5),
            "shift_fraction_p75": _pct(relative, 0.75),
            "phase_occurrences": dict(phases),
            "examples": rows[:5],
        })
    return {"seeds": seeds, "actor_runs": len(seeds) * 90, "derived_states": summaries}


def _multiday_patterns() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3] / "data/mock/realdata-v1"
    # The income table uses ``order_date`` while daily KPI/rush tables use
    # ``local_date``. Keep the source schemas explicit instead of normalizing a
    # column name that does not exist in the committed MOCK contract.
    income = pl.read_parquet(root / "driver_income_daily.parquet").sort(["driver_id", "order_date"])
    stats = pl.read_parquet(root / "driver_statistic_daily.parquet").sort(["driver_id", "local_date"])
    rush = pl.read_parquet(root / "driver_orders_rush_hours.parquet").sort(["driver_id", "local_date"])

    low_days = low_streak_drivers = rebound_days = 0
    comparable_drivers = set()
    for rows in income.partition_by("driver_id", maintain_order=True):
        prior: list[float] = []
        streak = 0
        had_streak = False
        flagged_previous = False
        for row in rows.iter_rows(named=True):
            value = float(row["commission"])
            if len(prior) >= 7:
                comparable_drivers.add(str(row["driver_id"]))
                median = statistics.median(prior[-7:])
                low = median > 0 and value < 0.8 * median
                if low:
                    low_days += 1
                    streak += 1
                    had_streak = had_streak or streak >= 2
                else:
                    if flagged_previous and value >= median:
                        rebound_days += 1
                    streak = 0
                flagged_previous = low
            prior.append(value)
        low_streak_drivers += int(had_streak)

    acceptance_streak = acceptance_recovery = 0
    for rows in stats.partition_by("driver_id", maintain_order=True):
        rates = [float(value) for value in rows["acceptance_rate"].to_list()]
        if any(rates[i] < 0.85 and rates[i + 1] < 0.85 for i in range(len(rates) - 1)):
            acceptance_streak += 1
        if any(rates[i] < 0.85 and rates[i + 1] >= 0.85 for i in range(len(rates) - 1)):
            acceptance_recovery += 1

    rush_drivers = rush["driver_id"].n_unique()
    return {
        "provenance": "MOCK 90-day corpus; shape evidence only, not live availability",
        "drivers_with_7day_comparable_history": len(comparable_drivers),
        "income_low_days_below_80pct_prior7_median": low_days,
        "drivers_with_2day_low_income_streak": low_streak_drivers,
        "income_rebound_days_after_low_day": rebound_days,
        "drivers_with_2day_acceptance_risk": acceptance_streak,
        "drivers_with_acceptance_recovery_next_day": acceptance_recovery,
        "drivers_with_rush_split_history": rush_drivers,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[1000, 1001, 1002, 1003, 1004])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT / "experience-coverage.json")
    args = parser.parse_args()
    payload = {
        "evidence_type": "read_only_ui_experience_derived_state_probe",
        "runtime_changed": False,
        "production_policy_changed": False,
        "thresholds_are_probes_not_rules": {
            "long_idle_min": 30,
            "episode_window_min": 60,
            "energy_recovery_window_min": 90,
            "cluster_window_min": 120,
            "utilization_or_empty_delta": 0.15,
            "income_low_ratio_to_prior7_median": 0.8,
        },
        "simulator": _simulator_patterns(args.seeds),
        "mock_multiday": _multiday_patterns(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "derived_states": len(payload["simulator"]["derived_states"]),
        "actor_runs": payload["simulator"]["actor_runs"],
        "mock_multiday": payload["mock_multiday"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
