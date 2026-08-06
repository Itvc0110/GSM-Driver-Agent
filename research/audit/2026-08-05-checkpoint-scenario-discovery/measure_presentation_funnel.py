"""Measure the REAL presentation funnel of the Web demo replay (read-only).

For every actor in the given seeds, walk the full replay via DemoSessionService.advance
(the exact path the Web UI uses) and record what the driver would actually see per step:
card vs silent, silent reason codes, steps-to-first-card, card density.

This does NOT modify runtime/policy/cadence. It only drives the existing product
service in-process, like the Web client would.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict

from app.services.demo_session import DemoSessionService, DemoSessionNotFound, _default_run

SEEDS = [int(s) for s in (sys.argv[1:] or ["1000"])]

out = {"seeds": SEEDS, "actors": [], "totals": {}}
status_counter = Counter()
silent_reasons = Counter()
card_topics = Counter()
card_actions = Counter()
card_state = Counter()
transition_kinds_all = Counter()
transition_kinds_card = Counter()

def _no_network_routes(waypoints):
    raise RuntimeError("funnel measurement: skip network routing, use fallback")

for seed in SEEDS:
    service = DemoSessionService(run_factory=_default_run, route_factory=_no_network_routes)
    created = service.create(seed=seed)
    actor_ids = [a["actor_id"] for a in created["actors"]]

    for actor_id in actor_ids:
        sess = service.create(seed=seed)
        sid = sess["session_id"]
        service.select_actor(sid, actor_id)
        version = 0
        steps = 0
        card_steps = []
        seen_ckpt = set()
        per_actor_silent = Counter()
        while True:
            try:
                step = service.advance(
                    sid, client_step_id=f"funnel-{actor_id}-{steps}",
                    expected_step_version=version)
            except DemoSessionNotFound:
                break
            version = step["step_version"]
            steps += 1
            tr = step.get("transition") or {}
            kind = tr.get("kind")
            drv_state = ((tr.get("driver") or {}).get("state"))
            transition_kinds_all[kind] += 1
            advice = step.get("advice") or {}
            status = advice.get("status")
            status_counter[status] += 1
            if status == "silent":
                rc = (advice.get("silent") or {}).get("reason_code")
                silent_reasons[rc] += 1
                per_actor_silent[rc] += 1
            else:
                transition_kinds_card[kind] += 1
                card_state[drv_state] += 1
                for item in advice.get("items") or []:
                    cid = item.get("checkpoint_id")
                    if cid:
                        seen_ckpt.add(cid)
                    card_topics[item.get("presentation_topic") or item.get("topic")] += 1
                    action = item.get("action") or {}
                    if isinstance(action, dict):
                        card_actions[action.get("code") or action.get("canonical_action")] += 1
                    else:
                        card_actions[str(action)] += 1
                card_steps.append(steps)
        out["actors"].append({
            "seed": seed, "actor_id": actor_id, "total_steps": steps,
            "card_steps": card_steps, "n_card_steps": len(card_steps),
            "unique_checkpoints": len(seen_ckpt),
            "first_card_step": card_steps[0] if card_steps else None,
            "silent_reasons": dict(per_actor_silent),
        })

rows = out["actors"]
firsts = [r["first_card_step"] for r in rows if r["first_card_step"] is not None]
n_cards = [r["n_card_steps"] for r in rows]
tot_steps = [r["total_steps"] for r in rows]
gaps = []
for r in rows:
    cs = r["card_steps"]
    gaps.extend(b - a for a, b in zip(cs, cs[1:]))

def q(data, p):
    if not data:
        return None
    s = sorted(data)
    idx = min(len(s) - 1, max(0, round(p * (len(s) - 1))))
    return s[idx]

out["totals"] = {
    "n_actor_runs": len(rows),
    "total_steps": sum(tot_steps),
    "steps_per_actor": {"min": min(tot_steps), "median": statistics.median(tot_steps), "max": max(tot_steps)},
    "advice_status": dict(status_counter),
    "silent_reason_codes": dict(silent_reasons),
    "actors_with_zero_cards": sum(1 for r in rows if r["n_card_steps"] == 0),
    "cards_per_actor": {"min": min(n_cards), "median": statistics.median(n_cards),
                        "p90": q(n_cards, 0.9), "max": max(n_cards)},
    "first_card_step": {"median": statistics.median(firsts) if firsts else None,
                        "p75": q(firsts, 0.75), "p90": q(firsts, 0.9),
                        "max": max(firsts) if firsts else None, "n": len(firsts)},
    "steps_between_cards": {"median": statistics.median(gaps) if gaps else None,
                            "p90": q(gaps, 0.9), "max": max(gaps) if gaps else None, "n": len(gaps)},
    "card_share_of_steps": (status_counter.total() - status_counter.get("silent", 0)) / max(1, status_counter.total()),
    "transition_kinds_all": dict(transition_kinds_all),
    "transition_kinds_with_card": dict(transition_kinds_card),
    "card_topics": dict(card_topics),
    "card_actions": dict(card_actions),
    "card_driver_state": dict(card_state),
}

import os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    f"funnel-seed{'-'.join(map(str, SEEDS))}.json")
with open(path, "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out["totals"], ensure_ascii=False, indent=1))
print("written:", path)
