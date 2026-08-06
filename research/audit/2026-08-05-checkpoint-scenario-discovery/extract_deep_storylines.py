#!/usr/bin/env python3
"""Extract continuous demo-story evidence from one existing simulator trajectory.

Selected actors are passed explicitly so the choice remains reviewable against
``deep-opportunity-by-actor.csv``.  This is an observer: it does not alter the run,
checkpoint policy, or actor behavior.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.services.demo_session import _default_run
from gsm_core.lifecycle.checkpoint import project_checkpoint_events
from gsm_sim.demo_trace import minute_from_iso
from gsm_sim.journey import build_journey


KEY_EVENTS = {
    "go_online", "order_skipped_soc", "go_swap", "swap_failed", "swap_done",
    "charge_home_start", "charge_home_end", "battery_stranded", "rest",
    "mission_completed", "newbie_guarantee_topup", "newbie_week1_bonus",
    "order_cancelled_after_accept", "end_shift", "day_end_settle",
}


def _states(result) -> dict[str, str]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in result.advice_checkpoint_events:
        grouped[str(event["checkpoint_id"])].append(event)
    return {
        str(checkpoint["checkpoint_id"]): str(
            project_checkpoint_events(grouped[str(checkpoint["checkpoint_id"])])["state"]
        )
        for checkpoint in result.advice_checkpoints
    }


def _checkpoint(checkpoint: dict, state: str, execution: list[dict]) -> dict:
    validity = checkpoint.get("validity") or {}
    return {
        "checkpoint_id": checkpoint["checkpoint_id"],
        "created_min": minute_from_iso(validity.get("valid_from") or checkpoint.get("created_at")),
        "state": state,
        "solver_set": checkpoint.get("solver_set"),
        "topic": checkpoint.get("topic"),
        "current_action": checkpoint.get("current_action"),
        "future_plan": checkpoint.get("future_plan"),
        "action_window": checkpoint.get("action_window"),
        "validity": validity,
        "reason_code": checkpoint.get("reason_code"),
        "numbers": checkpoint.get("numbers"),
        "caveats": checkpoint.get("caveats"),
        "execution_links": execution,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--actors", type=int, nargs="+", default=[35, 70, 37])
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("deep-demo-storylines.json"))
    args = parser.parse_args()

    result = _default_run(args.seed)
    states = _states(result)
    links_by_checkpoint: dict[str, list[dict]] = defaultdict(list)
    for link in result.execution_links:
        links_by_checkpoint[str(link.get("checkpoint_id"))].append(dict(link))

    stories = []
    for actor_id in args.actors:
        actor = next(actor for actor in result.actors if int(actor.actor_id) == actor_id)
        journey = build_journey(result, actor_id)
        checkpoints = [
            _checkpoint(checkpoint, states[str(checkpoint["checkpoint_id"])],
                        links_by_checkpoint[str(checkpoint["checkpoint_id"])])
            for checkpoint in result.advice_checkpoints
            if checkpoint.get("driver_id") == f"d-{actor_id}"
        ]
        checkpoints.sort(key=lambda item: (item["created_min"] or -1, item["checkpoint_id"]))
        key_events = [
            {
                "t_min": float(event.t_min),
                "kind": str(event.kind),
                "detail": dict(event.detail or {}),
            }
            for event in result.events
            if int(event.actor_id) == actor_id and str(event.kind) in KEY_EVENTS
        ]
        idle_blocks = [
            {"t0": block.t0, "t1": block.t1, "minutes": round(block.minutes, 3)}
            for block in journey.timeline if block.kind == "idle" and block.minutes >= 30
        ]
        stories.append({
            "seed": args.seed,
            "run_id": result.run_id,
            "actor_id": actor_id,
            "driver_id": f"d-{actor_id}",
            "archetype": actor.archetype,
            "fleet": actor.fleet.value,
            "shift": [actor.shift_start_min, actor.shift_end_min],
            "journey_metrics": journey.metrics,
            "checkpoints": checkpoints,
            "key_events": key_events,
            "long_idle_blocks_30m": idle_blocks,
        })

    payload = {
        "evidence_type": "read_only_storyline_projection",
        "provenance": {"data_mode": "sim-engine", "is_mock": True,
                       "seed": args.seed, "run_id": result.run_id},
        "selection_note": (
            f"Actors {args.actors} were selected explicitly from measured actor/derived-state "
            "artifacts for reviewable storylines. Selection is not a fixture or runtime change."
        ),
        "stories": stories,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "actors": [
            {"actor_id": story["actor_id"], "checkpoints": len(story["checkpoints"]),
             "key_events": len(story["key_events"]),
             "long_idle_blocks": len(story["long_idle_blocks_30m"])}
            for story in stories
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
