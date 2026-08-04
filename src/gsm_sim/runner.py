"""Runner — chạy 1 sim run: seed → config → world → event log.

Slice v0: 1 arm (B). Trả về (events, actors) để metrics/logging xử lý.
"""

from __future__ import annotations

import hashlib
import json
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
    trace_snapshots: list[dict] = field(default_factory=list)
    segments: list = field(default_factory=list)
    stations: list = field(default_factory=list)
    order_states: dict = field(default_factory=dict)
    advice_artifacts: list = field(default_factory=list)
    advice_checkpoints: list = field(default_factory=list)
    advice_checkpoint_events: list = field(default_factory=list)
    execution_links: list = field(default_factory=list)
    pending_execution_observations: list = field(default_factory=list)


def _data(cfg: Config, fname_key: str) -> Path:
    data_dir = cfg.resolve_path("world.data_dir")
    return data_dir / cfg.get(f"world.{fname_key}")


# Tên rút gọn cho kênh advice trong run_id — thứ tự cố định (không phụ thuộc dict order)
_CHANNEL_ABBREV = (("shift_plan", "sp"), ("accept_lift", "al"),
                   ("shift_extend", "se"), ("rest_window", "rw"))


def derive_run_id(cfg: Config, seed: int) -> str:
    """Run identity DETERMINISTIC từ (cfg advice, seed) — ĐA-05 Cycle W.

    Khác `logging_ev.write_run` (wall-clock, chỉ đặt tên folder): run_id này derive thuần
    nên exact-repeat cùng cfg+seed cho cùng ID — điều kiện để lifecycle event của sim
    replay/join được. Cặp A/B của `run_pair` CÙNG seed nhưng khác arm ⇒ khác run_id;
    A được cache xuyên ladder giữ MỘT run_id (nó là một run vật lý — chốt plan Cycle W).
    Multi-day: mỗi ngày một seed (`multiday.day_seed`) nên ngày đã nằm trong seed.

    ## Vì sao có digest — phần đọc-được KHÔNG đủ làm identity

    Bản đầu chỉ đọc block `advice`, nên hai run vật lý KHÁC HẲN nhau (đổi
    `environment.scenario`/`dow`, `demand.orders_per_day`, `advice.bucket_min`,
    `advice.share`…) nhận CÙNG run_id. Hai review đối kháng độc lập cùng chứng minh hậu
    quả tại store canonical: `INSERT OR IGNORE` coi event của run thứ hai là trùng và
    **nuốt im lặng** (đo được 128 event_id + 889 decision_id đụng nhau giữa hai run chỉ
    khác `dow`). Vì thế ID mang thêm digest của TOÀN BỘ config, trừ `meta` (thuần mô tả:
    nhãn mock/version, không đổi hành vi).

    Dạng: `{seed}-{A|B}-{kênh|none}-{coverage[.actor]}[-pos.{mode}]-c{digest8}`
    """
    adv = cfg.get("advice", {}) or {}
    arm = "B" if adv.get("enabled") else "A"
    ch = adv.get("channels", {}) or {}
    on = "+".join(abbr for name, abbr in _CHANNEL_ABBREV if ch.get(name)) or "none"
    cov = str(adv.get("coverage", "single"))
    if cov == "single" and adv.get("single_actor_id") is not None:
        cov += f".{adv['single_actor_id']}"
    rid = f"{seed}-{arm}-{on}-{cov}"
    pos = adv.get("positioning_overrides", "off")
    if pos and pos != "off":
        rid += f"-pos.{pos}"
    body = {k: v for k, v in (cfg.data or {}).items() if k != "meta"}
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, default=_digest_default).encode()
    ).hexdigest()[:8]
    return f"{rid}-c{digest}"


def _digest_default(v):
    """Encoder cho digest run_id — X-2 (review batch 2): `default=str` phá identity
    CẢ HAI chiều: np.int64(30) ≠ 30 (cùng semantic, khác ID — str thêm ngoặc kép);
    `set` ⇒ ID đổi theo PYTHONHASHSEED (phá exact-repeat, đo được 6 process 6 ID);
    datetime(2026,1,1) == chuỗi "2026-01-01 00:00:00" (khác semantic, CÙNG ID — chiều
    nuốt-run của W-1). Normalize semantic-preserving; kiểu lạ nổ TypeError tường minh."""
    import datetime as _dt
    if (getattr(v, "item", None) is not None
            and type(v).__module__ != "builtins"
            and getattr(v, "ndim", None) == 0):
        return v.item()                                  # numpy scalar → Python thuần
    if isinstance(v, (_dt.datetime, _dt.date)):
        return f"__dt__{v.isoformat()}"                  # tag để không trùng chuỗi thường
    raise TypeError(
        f"config chứa kiểu {type(v).__name__} không digest được deterministic — "
        f"run_id là identity của store append-only, không được phụ thuộc str() ngẫu nhiên")


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
    world = World(grid, cfg, policy, orders, actors, seed, environment=env, congestion=congestion,
                  run_id=derive_run_id(cfg, seed))
    events = world.run()
    segments, trace = finalize_checkpoint_trace(world, events)
    return RunResult(seed=seed, events=events, actors=actors, orders=orders,
                     config=cfg, policy=policy, grid=grid, env=env,
                     congestion=congestion, traj=world.traj, segments=segments,
                     trace_snapshots=world.trace_snapshots,
                     stations=world.stations, order_states=world.order_states,
                     **trace)


def finalize_checkpoint_trace(world: World, events: list[Event]) -> tuple[list, dict]:
    """Attach diagnostic identities and resolve observations after the run."""
    sink = world.checkpoint_trace
    if not sink.enabled:
        return world.segments, {
            "advice_artifacts": [], "advice_checkpoints": [],
            "advice_checkpoint_events": [], "execution_links": [],
            "pending_execution_observations": [],
        }
    from .checkpoint_trace import annotate_segment_ids
    segments = annotate_segment_ids(world.run_id, world.segments)
    sink.finalize_execution_links(segments, events)
    return segments, {
        "advice_artifacts": sink.artifacts,
        "advice_checkpoints": sink.checkpoints,
        "advice_checkpoint_events": sink.events,
        "execution_links": sink.execution_links,
        "pending_execution_observations": sink.pending_execution_observations,
    }
