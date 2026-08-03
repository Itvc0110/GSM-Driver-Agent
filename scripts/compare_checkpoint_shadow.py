"""Verify that checkpoint shadow capture does not change simulator outcomes."""

from __future__ import annotations

import argparse
import copy
import json
from enum import Enum
from typing import Any

from gsm_sim.config import Config
from gsm_sim.runner import run_once


def _value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return getattr(value, "value", value)


def semantic_fingerprint(result: Any) -> dict[str, Any]:
    """Return only behavior-bearing outcomes required by the P2 comparator."""
    order_states = getattr(result, "order_states", {}) or {}
    orders = []
    for order in getattr(result, "orders", []):
        order_id = getattr(order, "order_id", None)
        state = order_states.get(order_id, getattr(order, "state", None))
        if isinstance(state, (tuple, list)) and state:
            state = state[0]
        orders.append({"order_id": order_id, "state": _value(state)})

    actors = []
    for actor in getattr(result, "actors", []):
        actors.append({
            "actor_id": getattr(actor, "actor_id", None),
            "state": _value(getattr(actor, "state", None)),
            "payout_vnd": getattr(actor, "payout_vnd", 0),
            "soc_pct": getattr(actor, "soc_pct", None),
            "trips_done": getattr(actor, "trips_done", 0),
        })

    segments = [{
        "actor_id": segment.get("actor_id"),
        "kind": segment.get("kind"),
        "t0": segment.get("t0"),
        "t1": segment.get("t1"),
    } for segment in getattr(result, "segments", [])]
    return {"orders": orders, "actors": actors, "segments": segments}


def _with_shadow(base: Config, enabled: bool) -> Config:
    data = copy.deepcopy(base.data)
    shadow = data.setdefault("checkpoint_shadow", {})
    shadow["enabled"] = enabled
    return Config(data, base.root_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seeds", nargs="+", required=True, type=int)
    args = parser.parse_args()

    base = Config.load(args.config)
    mismatches: list[int] = []
    for seed in args.seeds:
        plain = semantic_fingerprint(run_once(_with_shadow(base, False), seed))
        shadow = semantic_fingerprint(run_once(_with_shadow(base, True), seed))
        equal = plain == shadow
        print(json.dumps({"seed": seed, "identical": equal}, sort_keys=True), flush=True)
        if not equal:
            mismatches.append(seed)
    if mismatches:
        print(json.dumps({"status": "DIFF", "seeds": mismatches}, sort_keys=True))
        return 1
    print(json.dumps({"status": "IDENTICAL", "seeds": args.seeds}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
