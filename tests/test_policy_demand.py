"""Test policy bundle + demand generator."""

from pathlib import Path

import pytest

from gsm_sim import geo
from gsm_sim.config import Config
from gsm_sim.demand import generate_orders
from gsm_sim.policy import PolicyBundle

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "research" / "simulation" / "data"


@pytest.fixture(scope="module")
def cfg():
    return Config.load(ROOT / "configs" / "pilot_dongda.yaml")


@pytest.fixture(scope="module")
def policy(cfg):
    return PolicyBundle.from_config(cfg)


@pytest.fixture(scope="module")
def grid():
    return geo.build_grid(DATA / "dd_geom.json", DATA / "batt_dd.json", DATA / "poi_dd.json", 9, 8)


# --- Policy ---


def test_fare_median_trip(policy):
    # cuốc 3.5km: 13000 + (3.5-2)*4300 = 19450
    assert policy.gross_fare(3.5) == 19450


def test_payout_share(policy):
    assert policy.driver_payout_from_gross(20000) == 15000  # 75%


def test_trip_points(policy):
    assert policy.trip_points(7) == 10   # peak (06-08h bucket 6,7)
    assert policy.trip_points(17) == 10  # peak chiều
    assert policy.trip_points(12) == 5   # giờ thường trong window
    assert policy.trip_points(23) == 0   # ngoài window điểm


def test_day_bonus_tiers(policy):
    # đủ điều kiện tỷ lệ
    assert policy.day_bonus(50, 0.9, 0.9) == 0       # dưới mốc thấp nhất (60)
    assert policy.day_bonus(60, 0.9, 0.9) == 30000
    assert policy.day_bonus(199, 0.9, 0.9) == 115000  # mốc 160
    assert policy.day_bonus(200, 0.9, 0.9) == 170000
    # thiếu điều kiện tỷ lệ → 0 dù đủ điểm
    assert policy.day_bonus(200, 0.5, 0.9) == 0


def test_next_tier_gap(policy):
    gap = policy.next_tier_gap(50)
    assert gap == (10, 30000)
    assert policy.next_tier_gap(200) is None


# --- Demand ---


def test_orders_count_near_target(grid, cfg, policy):
    orders = generate_orders(grid, cfg, policy, seed=1)
    # Poisson quanh 1200 (chỉ giờ trong window) — dải rộng
    assert 950 <= len(orders) <= 1450, len(orders)


def test_orders_deterministic(grid, cfg, policy):
    o1 = generate_orders(grid, cfg, policy, seed=42)
    o2 = generate_orders(grid, cfg, policy, seed=42)
    assert len(o1) == len(o2)
    assert [(o.order_id, o.pickup_cell, o.drop_cell, o.gross_vnd) for o in o1] == \
           [(o.order_id, o.pickup_cell, o.drop_cell, o.gross_vnd) for o in o2]


def test_orders_different_seed(grid, cfg, policy):
    o1 = generate_orders(grid, cfg, policy, seed=1)
    o2 = generate_orders(grid, cfg, policy, seed=2)
    assert len(o1) != len(o2) or [o.pickup_cell for o in o1] != [o.pickup_cell for o in o2]


def test_evening_peak_higher_than_midday(grid, cfg, policy):
    orders = generate_orders(grid, cfg, policy, seed=7)
    by_hour = {}
    for o in orders:
        h = int(o.t_min // 60)
        by_hour[h] = by_hour.get(h, 0) + 1
    # đỉnh chiều 18h > giữa trưa 13h
    assert by_hour.get(18, 0) > by_hour.get(13, 0)


def test_pickup_in_core(grid, cfg, policy):
    orders = generate_orders(grid, cfg, policy, seed=3)
    assert all(grid.is_core(o.pickup_cell) for o in orders)


# ---------- AUDIT A1 DEMAND-1 (UPDATE-065): vệ sinh config — không nuôi cờ chết ----------


def test_no_dead_demand_config_keys():
    """Mọi key dưới `demand:` trong config PHẢI được demand.py đọc — cờ chết làm
    người chỉnh config tưởng mình đang đổi hành vi (hour_interp từng như vậy)."""
    from pathlib import Path
    import yaml
    root = Path(__file__).resolve().parent.parent
    cfg = yaml.safe_load((root / "configs" / "pilot_dongda.yaml").read_text(encoding="utf-8"))
    src = (root / "src" / "gsm_sim" / "demand.py").read_text(encoding="utf-8")
    dead = [k for k in cfg["demand"] if f"demand.{k}" not in src]
    assert dead == [], f"key demand.* không được code đọc (cờ chết): {dead}"
