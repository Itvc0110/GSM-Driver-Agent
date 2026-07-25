"""Smoke test: 1 sim run đầy đủ + determinism + invariants."""

from pathlib import Path

import pytest

from gsm_sim.config import Config
from gsm_sim.metrics import summarize
from gsm_sim.runner import run_once

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cfg():
    return Config.load(ROOT / "configs" / "pilot_dongda.yaml")


def test_run_completes(cfg):
    r = run_once(cfg, seed=1)
    assert len(r.events) > 0
    # SIM-1: đọc từ config (trước đây khoá cứng 50 → đỏ mỗi lần hiệu chỉnh cung)
    assert len(r.actors) == int(cfg.get("actors.n"))


def test_determinism_same_seed(cfg):
    m1 = summarize(run_once(cfg, seed=7))
    m2 = summarize(run_once(cfg, seed=7))
    # metrics tổng phải khớp (determinism sơ bộ)
    assert m1 == m2


def test_different_seed_differs(cfg):
    m1 = summarize(run_once(cfg, seed=1))
    m2 = summarize(run_once(cfg, seed=2))
    assert m1["orders_total"] != m2["orders_total"] or m1["orders_completed"] != m2["orders_completed"]


def test_invariants(cfg):
    r = run_once(cfg, seed=3)
    for a in r.actors:
        assert 0.0 <= a.soc_pct <= 100.0
        assert a.orders_completed <= a.orders_accepted <= a.orders_offered
        assert a.trips_done == a.orders_completed
        assert a.payout_vnd >= 0
        assert a.points >= 0
    m = summarize(r)
    # served rate hợp lý (không âm, không > 1)
    assert 0.0 <= m["served_rate"] <= 1.0
    # với cung hiện tại / ~1200 đơn: có phục vụ được đáng kể
    # (ngưỡng CHÍNH XÁC cho served nằm ở gate SIM-1 `tests/test_sim_realism.py`)
    assert m["orders_completed"] > 300


def test_full_time_trips_plausible(cfg):
    # calibration sơ bộ (KHÔNG phải gate T-021): full-time median trong dải rộng
    m = summarize(run_once(cfg, seed=5))
    assert 8 <= m["trips_fulltime_median"] <= 35, m["trips_fulltime_median"]
