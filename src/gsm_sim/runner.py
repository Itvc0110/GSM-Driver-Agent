"""Runner — chạy 1 sim run: seed → config → world → event log.

Slice v0: 1 arm (B). Trả về (events, actors) để metrics/logging xử lý.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .archetypes import sample_actors
from .config import Config
from .congestion import CongestionField
from .demand import Order, generate_orders
from .environment import EnvironmentContext
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
    env: EnvironmentContext | None = None
    congestion: CongestionField | None = None
    traj: list = field(default_factory=list)
    segments: list = field(default_factory=list)
    stations: list = field(default_factory=list)
    order_states: dict = field(default_factory=dict)


def _data(cfg: Config, fname_key: str) -> Path:
    data_dir = cfg.resolve_path("world.data_dir")
    return data_dir / cfg.get(f"world.{fname_key}")


def build_environment(grid: Grid, cfg: Config, seed: int) -> EnvironmentContext | None:
    """Tạo EnvironmentContext nếu config có block `environment`. Scenario mặc định
    dry_weekday (mọi factor=1) ⇒ tương đương env=None (baseline). Không tiêu RNG khi
    không mưa/sự kiện ⇒ giữ CRN với các run không-env."""
    if cfg.get("environment", None) is None:
        return None
    return EnvironmentContext(grid, cfg, seed)


def run_once(cfg: Config, seed: int) -> RunResult:
    grid = build_grid(
        geom_path=_data(cfg, "geom_file"),
        stations_path=_data(cfg, "stations_file"),
        poi_path=_data(cfg, "poi_file"),
        res=int(cfg.get("world.h3_res")),
        res_report=int(cfg.get("world.h3_res_report")),
    )
    policy = PolicyBundle.from_config(cfg)
    env = build_environment(grid, cfg, seed)
    from .geo import load_road_matrix
    road = load_road_matrix(cfg, grid)      # SIM-XANH: fare theo đường thật (None = tắt)
    orders = generate_orders(grid, cfg, policy, seed, env=env, road=road)
    congestion = CongestionField(orders, cfg, env=env)
    actors = sample_actors(grid, cfg, seed)
    world = World(grid, cfg, policy, orders, actors, seed, environment=env, congestion=congestion)
    events = world.run()
    return RunResult(seed=seed, events=events, actors=actors, orders=orders,
                     config=cfg, policy=policy, grid=grid, env=env,
                     congestion=congestion, traj=world.traj, segments=world.segments,
                     stations=world.stations, order_states=world.order_states)
