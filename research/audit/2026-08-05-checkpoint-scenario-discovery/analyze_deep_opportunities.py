#!/usr/bin/env python3
"""Read-only evidence collector for deep AdviceCheckpoint opportunity discovery.

The script deliberately stays outside runtime code.  It runs the existing Web-demo
factory, projects DriverJourney from the immutable RunResult, and reads the committed
90-day MOCK L1R parquet corpus.  It never changes simulator config, policy, cadence,
checkpoint state, or RNG consumption.

Research-only probes (not production rules):

* long idle: one inferred journey idle block >= 30 minutes;
* high empty share: empty / (empty + occupied) >= 40%;
* income deviation: current daily commission outside 80%-120% of the previous seven
  observed driver-days' median, after seven prior observations;
* repeated KPI risk: at least two consecutive observed days below the configured
  bonus acceptance threshold.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import polars as pl

from app.services.demo_session import _default_run
from gsm_sim.journey import build_journey


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = Path(__file__).resolve().parent


def _pct(values: Iterable[float], q: float) -> float | None:
    vals = sorted(float(value) for value in values)
    if not vals:
        return None
    index = max(0, min(len(vals) - 1, round(q * (len(vals) - 1))))
    return round(vals[index], 3)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _checkpoint_state_map(result: Any) -> dict[str, str]:
    from gsm_core.lifecycle.checkpoint import project_checkpoint_events

    by_checkpoint: dict[str, list[dict]] = defaultdict(list)
    for event in result.advice_checkpoint_events:
        by_checkpoint[str(event["checkpoint_id"])].append(event)
    states: dict[str, str] = {}
    for checkpoint in result.advice_checkpoints:
        checkpoint_id = str(checkpoint["checkpoint_id"])
        states[checkpoint_id] = str(
            project_checkpoint_events(by_checkpoint[checkpoint_id])["state"]
        )
    return states


def _sim_evidence(seeds: list[int]) -> dict[str, Any]:
    event_counts: Counter[str] = Counter()
    event_actor_runs: dict[str, set[tuple[int, int]]] = defaultdict(set)
    event_detail_keys: dict[str, set[str]] = defaultdict(set)
    checkpoint_counts: Counter[str] = Counter()
    checkpoint_actor_runs: dict[str, set[tuple[int, int]]] = defaultdict(set)
    rows: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []

    for seed in seeds:
        result = _default_run(seed)
        states = _checkpoint_state_map(result)
        checkpoints_by_actor: dict[int, list[dict]] = defaultdict(list)
        execution_by_checkpoint = {
            str(link.get("checkpoint_id")): link for link in result.execution_links
        }
        for checkpoint in result.advice_checkpoints:
            actor_id = int(str(checkpoint["driver_id"]).removeprefix("d-"))
            checkpoints_by_actor[actor_id].append(checkpoint)
            current = (checkpoint.get("current_action") or {}).get("code") or "NONE"
            future = tuple(
                str(step.get("code")) for step in (checkpoint.get("future_plan") or [])
                if isinstance(step, dict) and step.get("code")
            )
            key = "/".join((str(checkpoint.get("solver_set", ["?"])[0]),
                            str(checkpoint.get("topic")), str(current),
                            states.get(str(checkpoint["checkpoint_id"]), "unknown")))
            checkpoint_counts[key] += 1
            checkpoint_actor_runs[key].add((seed, actor_id))

        events_by_actor: dict[int, list[Any]] = defaultdict(list)
        for event in result.events:
            event_counts[str(event.kind)] += 1
            event_detail_keys[str(event.kind)].update((event.detail or {}).keys())
            if int(event.actor_id) >= 0:
                event_actor_runs[str(event.kind)].add((seed, int(event.actor_id)))
                events_by_actor[int(event.actor_id)].append(event)

        for actor in result.actors:
            actor_id = int(actor.actor_id)
            actor_events = sorted(events_by_actor.get(actor_id, []), key=lambda event: event.t_min)
            event_kind = Counter(str(event.kind) for event in actor_events)
            journey = build_journey(result, actor_id)
            idle_blocks = [block.minutes for block in journey.timeline if block.kind == "idle"]
            long_idle_blocks = [minutes for minutes in idle_blocks if minutes >= 30.0]
            energy_events = [event for event in actor_events if event.kind in {
                "order_skipped_soc", "go_swap", "swap_failed", "swap_done",
                "battery_stranded", "charge_home_start", "charge_home_end",
            }]
            swap_waits = [float(event.detail.get("wait_min") or 0.0)
                          for event in actor_events if event.kind == "swap_done"]
            checkpoints = checkpoints_by_actor.get(actor_id, [])
            ready = [checkpoint for checkpoint in checkpoints
                     if states.get(str(checkpoint["checkpoint_id"])) == "ready"]
            current_future = []
            future_swap = []
            executed = 0
            topic_revisions: dict[str, set[str]] = defaultdict(set)
            for checkpoint in checkpoints:
                current = (checkpoint.get("current_action") or {}).get("code")
                future = [step.get("code") for step in (checkpoint.get("future_plan") or [])
                          if isinstance(step, dict)]
                if future and future[0] and future[0] != current:
                    current_future.append(checkpoint)
                if current == "ONLINE" and "SWAP" in future[:2]:
                    future_swap.append(checkpoint)
                if str(checkpoint["checkpoint_id"]) in execution_by_checkpoint:
                    executed += 1
                topic_revisions[str(checkpoint.get("topic"))].add(
                    str(checkpoint.get("fingerprint") or checkpoint.get("checkpoint_id")))

            moving = float(actor.empty_min) + float(actor.occupied_min)
            empty_share = _safe_ratio(float(actor.empty_min), moving)
            rows.append({
                "seed": seed,
                "run_id": result.run_id,
                "actor_id": actor_id,
                "archetype": actor.archetype,
                "fleet": actor.fleet.value,
                "checkpoints": len(checkpoints),
                "ready_checkpoints": len(ready),
                "checkpoint_topics": ";".join(sorted({str(c.get("topic")) for c in checkpoints})),
                "current_future_distinct": len(current_future),
                "swap_soon_candidates": len(future_swap),
                "checkpoint_execution_links": executed,
                "max_topic_revisions": max((len(items) for items in topic_revisions.values()), default=0),
                "trips": int(actor.trips_done),
                "payout_vnd": int(actor.payout_vnd),
                "points": int(actor.points),
                "soc_end_pct": round(float(actor.soc_pct), 3),
                "online_min": round(float(actor.online_min), 3),
                "rest_min": round(float(actor.rest_min), 3),
                "charge_min": round(float(actor.charge_min), 3),
                "idle_min": round(float(actor.idle_min), 3),
                "longest_inferred_idle_min": round(max(idle_blocks, default=0.0), 3),
                "long_idle_blocks_30m": len(long_idle_blocks),
                "empty_share": empty_share,
                "high_empty_share_40pct": bool(empty_share is not None and empty_share >= 0.4),
                "soc_skips": event_kind["order_skipped_soc"],
                "repeated_soc_skips": event_kind["order_skipped_soc"] >= 2,
                "swap_started": event_kind["go_swap"],
                "swap_failed": event_kind["swap_failed"],
                "swap_done": event_kind["swap_done"],
                "swap_wait_max_min": round(max(swap_waits, default=0.0), 3),
                "battery_stranded": event_kind["battery_stranded"],
                "rest_events": event_kind["rest"],
                "cancel_after_accept": event_kind["order_cancelled_after_accept"],
                "decline_economics": sum(
                    event.kind == "order_declined" and event.detail.get("reason") == "economics"
                    for event in actor_events
                ),
                "decline_behavior": sum(
                    event.kind == "order_declined" and event.detail.get("reason") == "base_behavior"
                    for event in actor_events
                ),
                "mission_completed": event_kind["mission_completed"],
                "newbie_events": event_kind["newbie_guarantee_topup"]
                                  + event_kind["newbie_week1_bonus"],
                "ratings": event_kind["trip_rated"],
                "recap_inputs_present": bool(event_kind["end_shift"] or event_kind["day_end_settle"]),
                "energy_event_count": len(energy_events),
            })

        run_summaries.append({
            "seed": seed,
            "run_id": result.run_id,
            "actors": len(result.actors),
            "events": len(result.events),
            "segments": len(result.segments),
            "checkpoints": len(result.advice_checkpoints),
            "checkpoint_events": len(result.advice_checkpoint_events),
            "execution_links": len(result.execution_links),
        })

    n_actor_runs = len(rows)

    def actor_runs_where(key: str, predicate=lambda value: bool(value)) -> int:
        return sum(predicate(row[key]) for row in rows)

    summary = {
        "seeds": seeds,
        "runs": len(seeds),
        "actor_runs": n_actor_runs,
        "run_summaries": run_summaries,
        "coverage": {
            "pre_shift_brief_inputs": n_actor_runs,
            "post_shift_recap_inputs": actor_runs_where("recap_inputs_present"),
            "ready_checkpoint": actor_runs_where("ready_checkpoints", lambda value: value > 0),
            "current_future_distinct": actor_runs_where("current_future_distinct", lambda value: value > 0),
            "swap_soon": actor_runs_where("swap_soon_candidates", lambda value: value > 0),
            "soc_skip_awareness": actor_runs_where("soc_skips", lambda value: value > 0),
            "repeated_soc_skip_pattern": actor_runs_where("repeated_soc_skips"),
            "swap_friction": sum(bool(row["swap_failed"] or row["swap_wait_max_min"] > 5)
                                 for row in rows),
            "long_idle_30m": actor_runs_where("long_idle_blocks_30m", lambda value: value > 0),
            "high_empty_share_40pct": actor_runs_where("high_empty_share_40pct"),
            "cancel_after_accept": actor_runs_where("cancel_after_accept", lambda value: value > 0),
            "mission_completed": actor_runs_where("mission_completed", lambda value: value > 0),
            "newbie_event": actor_runs_where("newbie_events", lambda value: value > 0),
        },
        "distributions": {
            "ready_checkpoint_per_actor_run": {
                "p50": _pct((row["ready_checkpoints"] for row in rows), 0.5),
                "p75": _pct((row["ready_checkpoints"] for row in rows), 0.75),
                "p90": _pct((row["ready_checkpoints"] for row in rows), 0.9),
                "max": max(row["ready_checkpoints"] for row in rows),
            },
            "longest_inferred_idle_min": {
                "p50": _pct((row["longest_inferred_idle_min"] for row in rows), 0.5),
                "p75": _pct((row["longest_inferred_idle_min"] for row in rows), 0.75),
                "p90": _pct((row["longest_inferred_idle_min"] for row in rows), 0.9),
                "max": max(row["longest_inferred_idle_min"] for row in rows),
            },
            "empty_share": {
                "p50": _pct((row["empty_share"] for row in rows if row["empty_share"] is not None), 0.5),
                "p75": _pct((row["empty_share"] for row in rows if row["empty_share"] is not None), 0.75),
                "p90": _pct((row["empty_share"] for row in rows if row["empty_share"] is not None), 0.9),
            },
            "soc_skips": {
                "p50": _pct((row["soc_skips"] for row in rows), 0.5),
                "p90": _pct((row["soc_skips"] for row in rows), 0.9),
                "max": max(row["soc_skips"] for row in rows),
            },
        },
        "event_inventory": [
            {
                "event_kind": kind,
                "count": count,
                "actor_runs": len(event_actor_runs.get(kind, set())),
                "detail_keys": sorted(event_detail_keys.get(kind, set())),
            }
            for kind, count in sorted(event_counts.items())
        ],
        "checkpoint_inventory": [
            {
                "kind": kind,
                "count": count,
                "actor_runs": len(checkpoint_actor_runs.get(kind, set())),
            }
            for kind, count in sorted(checkpoint_counts.items())
        ],
    }
    return {"summary": summary, "actor_rows": rows}


def _longest_below_streak(rows: list[dict], threshold: float) -> int:
    longest = current = 0
    for row in rows:
        if float(row["acceptance_rate"]) < threshold:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _realdata_evidence() -> dict[str, Any]:
    folder = ROOT / "data/mock/realdata-v1"
    income = pl.read_parquet(folder / "driver_income_daily.parquet").sort(
        ["driver_id", "order_date"]
    ).to_dicts()
    stats = pl.read_parquet(folder / "driver_statistic_daily.parquet").sort(
        ["driver_id", "local_date"]
    ).to_dicts()
    online = pl.read_parquet(folder / "driver_online_hours_sap_id.parquet")
    rush = pl.read_parquet(folder / "driver_orders_rush_hours.parquet")
    stoppoints = pl.read_parquet(folder / "driver_bike_stoppoints.parquet")
    missions = pl.read_parquet(folder / "public_mission.parquet")
    mission_progress = pl.read_parquet(folder / "public_user_mission_progress.parquet")
    mission_earn = pl.read_parquet(folder / "public_mission_earn_history.parquet")
    penalties = pl.read_parquet(folder / "driver_penalization_ATA.parquet")
    frauds = pl.read_parquet(folder / "public_frauds.parquet")
    trips = pl.scan_parquet(folder / "trips.parquet")
    hex_tracking = pl.scan_parquet(folder / "public_driver_hex_tracking.parquet")

    income_by_driver: dict[str, list[dict]] = defaultdict(list)
    for row in income:
        income_by_driver[str(row["driver_id"])].append(row)
    deviation_low = deviation_high = eligible_days = 0
    drivers_with_deviation: set[str] = set()
    for driver_id, driver_rows in income_by_driver.items():
        prior: list[float] = []
        for row in driver_rows:
            value = float(row["commission"])
            if len(prior) >= 7:
                baseline = statistics.median(prior[-7:])
                if baseline > 0:
                    eligible_days += 1
                    ratio = value / baseline
                    if ratio < 0.8:
                        deviation_low += 1
                        drivers_with_deviation.add(driver_id)
                    elif ratio > 1.2:
                        deviation_high += 1
                        drivers_with_deviation.add(driver_id)
            prior.append(value)

    stats_by_driver: dict[str, list[dict]] = defaultdict(list)
    for row in stats:
        stats_by_driver[str(row["driver_id"])].append(row)
    repeated_acceptance_risk = {
        driver_id for driver_id, driver_rows in stats_by_driver.items()
        if _longest_below_streak(driver_rows, 0.85) >= 2
    }

    hex_summary = hex_tracking.select(
        pl.len().alias("rows"),
        pl.col("driver_id").n_unique().alias("drivers"),
        (pl.col("tracking_status") == "idle").sum().alias("idle_rows"),
        ((pl.col("tracking_status") == "idle")
         & (pl.col("stay_duration_seconds") >= 300)).sum().alias("idle_rows_ge_300s"),
        pl.col("campaign_id").is_not_null().sum().alias("campaign_rows"),
        pl.col("target_hex").is_not_null().sum().alias("target_rows"),
        pl.col("reached_target").is_not_null().sum().alias("reached_labeled_rows"),
        pl.col("stay_duration_seconds").median().alias("stay_median_seconds"),
        pl.col("stay_duration_seconds").quantile(0.9).alias("stay_p90_seconds"),
    ).collect().to_dicts()[0]
    trip_summary = trips.select(
        pl.len().alias("rows"),
        pl.col("driver_id").n_unique().alias("drivers"),
        pl.col("distance_km").is_not_null().sum().alias("distance_rows"),
        pl.col("duration_seconds").is_not_null().sum().alias("duration_rows"),
        pl.col("pickup_h3").is_not_null().sum().alias("pickup_rows"),
        pl.col("drop_h3").is_not_null().sum().alias("drop_rows"),
    ).collect().to_dicts()[0]

    return {
        "provenance": {
            "label": "MOCK",
            "generator": "gsm_core.mockgen.realdata v4",
            "days": 90,
            "source_manifest": "data/mock/realdata-v1/manifest.json",
        },
        "daily_history": {
            "income_rows": len(income),
            "income_drivers": len(income_by_driver),
            "stat_rows": len(stats),
            "online_rows": online.height,
            "rush_split_rows": rush.height,
            "stoppoint_rows": stoppoints.height,
            "income_rolling7_eligible_days": eligible_days,
            "income_below_80pct_prior7_median": deviation_low,
            "income_above_120pct_prior7_median": deviation_high,
            "drivers_with_income_deviation": len(drivers_with_deviation),
            "drivers_with_2day_acceptance_risk": len(repeated_acceptance_risk),
        },
        "mission": {
            "catalog_rows": missions.height,
            "progress_rows": mission_progress.height,
            "progress_drivers": mission_progress["driver_id"].n_unique(),
            "earn_rows": mission_earn.height,
            "earn_drivers": mission_earn["driver_id"].n_unique(),
        },
        "risk_records": {
            "penalty_rows": penalties.height,
            "penalty_drivers": penalties["driver_id"].n_unique(),
            "fraud_rows": frauds.height,
            "fraud_drivers": frauds["driver_id"].n_unique(),
        },
        "hex_tracking": hex_summary,
        "trips": trip_summary,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[1000, 1001, 1002, 1003, 1004])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    sim = _sim_evidence(args.seeds)
    realdata = _realdata_evidence()
    payload = {
        "evidence_type": "read_only_research",
        "runtime_changed": False,
        "production_thresholds_changed": False,
        "simulator": sim["summary"],
        "mock_90_day_l1r": realdata,
        "probe_thresholds_not_production_policy": {
            "long_idle_min": 30,
            "high_empty_share": 0.4,
            "income_ratio_low": 0.8,
            "income_ratio_high": 1.2,
            "income_prior_observations": 7,
            "acceptance_threshold": 0.85,
            "acceptance_consecutive_days": 2,
        },
    }
    (args.output / "deep-opportunity-evidence.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_csv(args.output / "deep-opportunity-by-actor.csv", sim["actor_rows"])
    _write_csv(args.output / "deep-event-inventory.csv", sim["summary"]["event_inventory"])
    print(json.dumps({
        "simulator": sim["summary"]["coverage"],
        "distributions": sim["summary"]["distributions"],
        "mock_90_day_l1r": realdata,
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
