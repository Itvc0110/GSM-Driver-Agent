"""Ghi event log ra parquet + manifest JSON.

Manifest gắn nhãn MOCK + version theo CLAUDE.md §5.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from .metrics import summarize


def write_run(result, cfg, out_root: Path) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + f"_seed{result.seed}"
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # events → parquet
    rows = []
    for e in result.events:
        row = {"t_min": e.t_min, "actor_id": e.actor_id, "kind": e.kind, "cell": e.cell}
        for k, v in e.detail.items():
            row[f"d_{k}"] = v
        rows.append(row)
    df = pl.DataFrame(rows) if rows else pl.DataFrame({"t_min": [], "actor_id": [], "kind": [], "cell": []})
    df.write_parquet(run_dir / "events.parquet")

    # actor summary → parquet
    actor_rows = [{
        "actor_id": a.actor_id, "archetype": a.archetype, "fleet": a.fleet.value,
        "trips": a.trips_done, "offered": a.orders_offered, "accepted": a.orders_accepted,
        "completed": a.orders_completed, "cancelled": a.orders_cancelled,
        "gross_vnd": a.gross_vnd, "payout_vnd": a.payout_vnd, "points": a.points,
        "acceptance_rate": round(a.acceptance_rate, 3), "completion_rate": round(a.completion_rate, 3),
        "online_min": round(a.online_min, 1), "empty_min": round(a.empty_min, 1),
        "stranded": a.stranded_count, "soc_end": round(a.soc_pct, 1),
    } for a in result.actors]
    pl.DataFrame(actor_rows).write_parquet(run_dir / "actors.parquet")

    manifest = {
        "run_id": run_id,
        "seed": result.seed,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "data_mode": cfg.get("meta.data_mode", "synthetic"),
        "is_mock": cfg.get("meta.is_mock", True),
        "spec_version": cfg.get("meta.spec_version", "sim-core-slice-v0"),
        "policy_bundle_version": result.policy.version,
        "arm": "B",
        "config": cfg.data,
        "metrics": summarize(result),
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_dir
