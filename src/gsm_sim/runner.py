"""Runner — chạy 1 sim run: seed → config → world → event log.

Slice v0: 1 arm (B). Trả về (events, actors) để metrics/logging xử lý.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .archetypes import sample_actors
from .config import Config
from .demand import Order, generate_orders
from .geo import Grid, build_grid
from .policy import PolicyBundle
from .world import Event, World


@dataclass
class RunResult:
    seed: int
    events: list[Event]
    actors: list
    orders: list[Order]
    config: Config
    policy: PolicyBundle
    grid: Grid


def _data(cfg: Config, fname_key: str) -> Path:
    data_dir = cfg.resolve_path("world.data_dir")
    return data_dir / cfg.get(f"world.{fname_key}")


def run_once(cfg: Config, seed: int) -> RunResult:
    grid = build_grid(
        geom_path=_data(cfg, "geom_file"),
        stations_path=_data(cfg, "stations_file"),
        poi_path=_data(cfg, "poi_file"),
        res=int(cfg.get("world.h3_res")),
        res_report=int(cfg.get("world.h3_res_report")),
    )
    policy = PolicyBundle.from_config(cfg)
    orders = generate_orders(grid, cfg, policy, seed)
    actors = sample_actors(grid, cfg, seed)
    world = World(grid, cfg, policy, orders, actors, seed)
    events = world.run()
    return RunResult(seed=seed, events=events, actors=actors, orders=orders,
                     config=cfg, policy=policy, grid=grid)
