"""Test biên EnvironmentContext (specs/environment-variables.md §6).

7 test biên + kiểm tra tương đương baseline (dry_weekday ≡ env=None) và
kiểm tra env THỰC SỰ tác động sim (rain_peak khác dry). Mọi factor tắt được về 1.
"""

import copy
from pathlib import Path

import pytest

from gsm_sim.config import Config
from gsm_sim.environment import EnvironmentContext
from gsm_sim.geo import build_grid, grid_distance
from gsm_sim.metrics import summarize
from gsm_sim.runner import run_once

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cfg():
    return Config.load(ROOT / "configs" / "pilot_dongda.yaml")


@pytest.fixture(scope="module")
def grid(cfg):
    data_dir = cfg.resolve_path("world.data_dir")
    return build_grid(
        geom_path=data_dir / cfg.get("world.geom_file"),
        stations_path=data_dir / cfg.get("world.stations_file"),
        poi_path=data_dir / cfg.get("world.poi_file"),
        res=int(cfg.get("world.h3_res")),
        res_report=int(cfg.get("world.h3_res_report")),
    )


def _mut_cfg(cfg, mutate):
    """Deep-copy config data, cho phép mutate block environment, trả Config mới."""
    data = copy.deepcopy(cfg.data)
    mutate(data)
    return Config(data, cfg.root_dir)


def _env(cfg, grid, mutate=lambda d: None, seed=1):
    return EnvironmentContext(grid, _mut_cfg(cfg, mutate), seed)


# --- Test 1: dry_weekday ≡ baseline (env=None) — env wiring là no-op khi khô ---

def test_dry_weekday_equals_no_env(cfg):
    """Scenario dry_weekday (mọi factor=1) phải cho metrics IDENTICAL với env=None.
    Đây là bằng chứng env không phá baseline + không tiêu RNG khi khô (CRN-safe)."""
    cfg_no_env = _mut_cfg(cfg, lambda d: d.pop("environment", None))
    m_none = summarize(run_once(cfg_no_env, seed=11))
    m_dry = summarize(run_once(cfg, seed=11))
    assert m_none == m_dry


# --- Test 2: rain demand unimodal (chữ U ngược), đỉnh đúng R_peak ---

def test_rain_demand_unimodal(cfg, grid):
    env = _env(cfg, grid)
    assert env.rain_demand_factor(0.0) == 1.0
    rp = env.rain_r_peak
    peak = env.rain_demand_factor(rp)
    assert peak == pytest.approx(1.0 + env.rain_delta_peak)
    # đỉnh tại R_peak: hai bên đều thấp hơn (unimodal)
    assert env.rain_demand_factor(rp * 0.4) < peak
    assert env.rain_demand_factor(rp * 2.5) < peak
    # mưa rất to → giảm mạnh (không còn hấp dẫn)
    assert env.rain_demand_factor(60.0) < peak


# --- Test 3: speed_factor ∈ (0,1] mọi lúc/mọi mức tắc ---

def test_speed_factor_bounds(cfg, grid):
    env = _env(cfg, grid, lambda d: d["environment"]["rain"].update(
        {"series": [[600, 0.0], [700, 40.0], [800, 0.0]]}))
    for t in (600, 650, 700, 750, 800):
        sf = env.speed_factor(t)
        assert 0.0 < sf <= 1.0
    # tắc cực đại + mưa to vẫn > 0
    assert 0.0 < env.speed_factor(700, congestion_r=0.99) <= 1.0
    # slowdown bão hòa ≤ r_max
    assert env.rain_speed_slowdown(1e6) <= env.rain_r_max + 1e-9


# --- Test 4: p_offline ∈ [0,1], tăng theo R, ≤ p_cap ---

def test_offline_prob_bounds(cfg, grid):
    env = _env(cfg, grid)
    for arch in ("P1", "P2", "P3", "P4", "P5"):
        assert env.rain_offline_prob(0.0, arch) == 0.0
        p_small = env.rain_offline_prob(2.0, arch)
        p_big = env.rain_offline_prob(40.0, arch)
        assert 0.0 <= p_small <= p_big <= env.rain_p_cap <= 1.0


# --- Test 5: M_level clamp ∈ [m_min, m_max], log khi bị bó ---

def test_demand_factor_clamp(cfg, grid):
    # đẩy dow level vượt trần → phải bị bó về m_max và đếm clamp
    env = _env(cfg, grid, lambda d: d["environment"]["dow"]["level"].update({"weekday": 10.0}))
    m = env.demand_factor(720)
    assert m == env.m_max
    assert env.clamp_hits() >= 1
    # sàn: dow level rất nhỏ → bó về m_min
    env2 = _env(cfg, grid, lambda d: d["environment"]["dow"]["level"].update({"weekday": 0.01}))
    assert env2.demand_factor(720) == env2.m_min


# --- Test 6: event_addend — =0 ngoài cửa sổ thời gian, decay theo không gian ---

def test_event_addend_time_and_space(cfg, grid):
    venue = grid.core_cells[len(grid.core_cells) // 2]

    def add_event(d):
        d["environment"]["events"] = [{
            "venue_cell": venue, "t_start_min": 1140, "t_end_min": 1320,
            "attendance": 10000, "capture_rate": 0.1, "sigma_cells": 2.0,
            "ramp_in_min": 120, "ramp_lead_min": 15, "egress_min": 60, "egress_boost": 2.0,
        }]

    env = _env(cfg, grid, add_event)
    # giữa trưa (ngoài ramp/egress) → 0
    assert env.event_addend(venue, 720) == 0.0
    # trong ramp-in (t_start - 90) → > 0 tại venue
    a_venue = env.event_addend(venue, 1080)
    assert a_venue > 0.0
    # decay theo khoảng cách: cell xa venue nhỏ hơn tại venue
    far = None
    for c in grid.core_cells:
        if grid_distance(c, venue) == 2:
            far = c
            break
    if far is not None:
        assert env.event_addend(far, 1080) < a_venue
    # egress spike sắc hơn ingress: tại t_end+5 > 0
    assert env.event_addend(venue, 1325) > 0.0


# --- Test 7: determinism — cùng seed+scenario → trace identical ---

def test_env_determinism(cfg, grid):
    def auto_rain(d):
        d["environment"]["rain"]["auto"] = {
            "duration_min_per_day": 30, "peak_mmph": 12, "window_min": [900, 1200]}

    c = _mut_cfg(cfg, auto_rain)
    e1 = EnvironmentContext(grid, c, seed=42)
    e2 = EnvironmentContext(grid, c, seed=42)
    assert e1._rain_series == e2._rain_series
    assert e1._rain_series  # auto sinh ra đợt mưa (không rỗng)


# --- Bổ sung: env THỰC SỰ tác động sim (rain_peak ≠ dry) + run determinism ---

def test_rain_scenario_changes_metrics(cfg):
    """rain_peak (mưa to 17-19h) phải cho metrics KHÁC dry_weekday — chứng minh
    env được nối vào sim thật (demand↑ + speed↓ + supply↓)."""
    def rain_peak(d):
        d["environment"]["rain"]["series"] = [
            [1020, 0.0], [1050, 15.0], [1110, 15.0], [1140, 0.0]]  # 17:00-19:00

    m_dry = summarize(run_once(cfg, seed=9))
    m_rain = summarize(run_once(_mut_cfg(cfg, rain_peak), seed=9))
    assert m_dry != m_rain


def test_rain_run_determinism(cfg):
    def rain_peak(d):
        d["environment"]["rain"]["series"] = [[1020, 0.0], [1080, 15.0], [1140, 0.0]]

    c = _mut_cfg(cfg, rain_peak)
    assert summarize(run_once(c, seed=5)) == summarize(run_once(c, seed=5))
