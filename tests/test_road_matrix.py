"""SIM-XANH Phase 1 — gate cho RoadMatrix (đường thật OSRM, offline).

Ba thứ phải giữ: (1) offline — matrix là file tĩnh, KHÔNG bao giờ gọi mạng trong test/sim;
(2) cổng an toàn — `routing.enabled=false` trở về đúng hành vi detour cũ; (3) hệ số nằm
trong biên vật lý và fallback hoạt động.
"""

from __future__ import annotations

import copy

import pytest

from gsm_sim.config import Config
from gsm_sim.geo import RoadMatrix, build_grid, load_road_matrix
from gsm_sim.metrics import summarize
from gsm_sim.runner import _data, run_once

MATRIX = "research/simulation/data/osrm_matrix_dd.parquet"


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def grid(cfg):
    return build_grid(geom_path=_data(cfg, "geom_file"), stations_path=_data(cfg, "stations_file"),
                      poi_path=_data(cfg, "poi_file"), res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))


@pytest.fixture(scope="module")
def rm(cfg, grid):
    return RoadMatrix.load(MATRIX, grid.cell_centroid)


def test_matrix_committed_and_offline(rm):
    """Matrix phải TỒN TẠI trong repo (fetch một lần) và đủ dày — sim/test không gọi mạng."""
    assert len(rm._f) > 90_000, "matrix quá thưa — fetch hỏng?"


def test_factor_within_physical_bounds(rm):
    """Đường lái không thể NGẮN hơn chim bay (factor ≥ 1); trần 3.5 chặn outlier OSM."""
    fs = list(rm._f.values())
    assert all(RoadMatrix.FACTOR_MIN <= f <= RoadMatrix.FACTOR_MAX for f in fs)


def test_factor_median_above_constant_detour(rm):
    """Phát hiện lõi của Phase 1: detour hằng 1.3 ƯỚC NON đường Hà Nội thật (median ~1.46).
    Nếu median tụt về ≤1.3 thì hoặc matrix hỏng hoặc ai đó đổi nguồn — phải xem lại."""
    import statistics as st
    med = st.median(rm._f.values())
    assert 1.3 < med < 1.7, f"factor median {med:.3f} ngoài vùng đã đo (1.46)"


def test_missing_pair_falls_back(rm):
    got = rm.factor("8affffffffffff1", "8affffffffffff2", default=1.3)
    assert got == 1.3
    assert rm.misses >= 1


def test_core_coverage_high(rm, grid):
    core = set(grid.core_cells)
    covered = sum(1 for (a, b) in rm._f if a in core and b in core)
    assert covered / len(core) ** 2 > 0.95, "phủ core×core phải >95%"


def test_routing_disabled_restores_old_behavior(cfg):
    """CỔNG AN TOÀN: tắt routing ⇒ sim y hệt đường detour cũ, và metrics KHÁC đường bật
    (nếu giống hệt nghĩa là routing chưa từng có tác dụng — tính năng vỏ)."""
    on = summarize(run_once(cfg, seed=11))
    c2 = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c2.data["routing"]["enabled"] = False
    off1 = summarize(run_once(c2, seed=11))
    off2 = summarize(run_once(c2, seed=11))
    assert off1 == off2, "đường routing-off không deterministic"
    assert on != off1, "bật/tắt routing cho metrics GIỐNG HỆT — matrix không có tác dụng"


def test_event_orders_accept_road_param(cfg, grid):
    """REGRESSION (lỗi thật đã dính): `_add_event_orders` từng KHÔNG nhận `road=` — chỉ nổ
    khi config có `environment.events` (config thường không có nên smoke im lặng bỏ qua).
    """
    from gsm_sim.demand import generate_orders
    from gsm_sim.environment import EnvironmentContext
    from gsm_sim.policy import PolicyBundle
    data = copy.deepcopy(cfg.data)
    data.setdefault("environment", {})["events"] = [{
        "venue_cell": grid.core_cells[0], "t_start_min": 1140, "t_end_min": 1320,
        "attendance": 5000, "capture_rate": 0.1, "sigma_cells": 2.0,
    }]
    c2 = Config(data, cfg.root_dir)
    env = EnvironmentContext(grid, c2, seed=1)
    road = load_road_matrix(c2, grid)
    orders = generate_orders(grid, c2, PolicyBundle.from_config(c2), seed=1, env=env, road=road)
    assert orders, "không sinh được đơn khi có event + road"


def test_fare_uses_road_km(cfg, grid):
    """Cước phải tính trên km LỘ TRÌNH: cùng seed, tổng gross đường bật routing phải CAO hơn
    đường tắt (factor median 1.46 > 1.0 nhân vào fare-km)."""
    from gsm_sim.demand import generate_orders
    from gsm_sim.policy import PolicyBundle
    road = load_road_matrix(cfg, grid)
    pol = PolicyBundle.from_config(cfg)
    with_road = sum(o.gross_vnd for o in generate_orders(grid, cfg, pol, seed=3, road=road))
    without = sum(o.gross_vnd for o in generate_orders(grid, cfg, pol, seed=3, road=None))
    assert with_road > without * 1.05, "fare không phản ánh km lộ trình thật"
