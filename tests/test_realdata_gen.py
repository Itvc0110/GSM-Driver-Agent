"""PI-2 — generator realdata (sim→aggregate) sinh 13 bảng l1r hợp lệ + nhất quán chéo.

Gen dataset nhỏ (8 ngày) → R1 schema+FK + R3 cross-table (aggregate↔event nền).
"""

from collections import defaultdict
from pathlib import Path

import pytest

from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.schema_registry import SchemaRegistry, L1R_ENTITIES

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def gen(tmp_path_factory):
    out = tmp_path_factory.mktemp("realdata")
    res = generate_realdata(days=8, seed_base=100, out_dir=out)
    return res["tables"]


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


def test_all_13_tables_present(gen):
    assert set(gen) == set(L1R_ENTITIES)
    # bảng KPI daily phải có record (sim sinh trips)
    assert gen["driver_statistic_daily"] and gen["driver_income_daily"] and gen["trips"]


def test_r1_schema_valid(reg, gen):
    for entity, records in gen.items():
        bad = reg.validate_many(entity, records)
        assert not bad, f"{entity}: {list(bad.items())[:2]}"


def test_r1_fk_no_orphan(gen):
    drivers = {r["driver_id"] for r in gen["driver_income_daily"]}
    for e in gen["trips"]:
        assert e["driver_id"] in drivers
    missions = {m["id"] for m in gen["mission_catalog"]}
    for eh in gen["mission_earn_history"]:
        assert eh["mission_id"] in missions


def test_r3_income_matches_rush_split(gen):
    """income.total_fee == orders_rush.total_fee; normal+rush=total (cùng driver-day)."""
    inc = {(r["driver_id"], r["order_date"]): r for r in gen["driver_income_daily"]}
    for r in gen["driver_orders_rush_hours"]:
        key = (r["driver_id"], r["local_date"])
        assert inc[key]["total_fee"] == r["total_fee"]
        assert r["total_fee_normal_hour"] + r["total_fee_rush_hour"] == r["total_fee"]
        assert r["total_order_normal_hour"] + r["total_order_rush_hour"] == r["total_order"]
        assert r["commission_normal_hour"] + r["commission_rush_hour"] == r["commission"]


def test_r3_commission_from_share(gen):
    """commission = round(total_fee × driver_share=0.75)."""
    for r in gen["driver_income_daily"]:
        assert r["commission"] == int(round(r["total_fee"] * 0.75))


def test_r3_completed_equals_orders(gen):
    """statistic.completed == income.total_order == #trips (cùng driver-day)."""
    inc = {(r["driver_id"], r["order_date"]): r["total_order"] for r in gen["driver_income_daily"]}
    trips_ct = defaultdict(int)
    for t in gen["trips"]:
        trips_ct[(t["driver_id"], t["complete_time"][:10])] += 1
    for s in gen["driver_statistic_daily"]:
        key = (s["driver_id"], s["local_date"])
        assert s["completed_count"] == inc.get(key, 0)
        assert s["completed_count"] == trips_ct.get(key, 0)


def test_r4_rates_bounded(gen):
    for s in gen["driver_statistic_daily"]:
        for f in ("acceptance_rate", "fulfillment_rate", "cancellation_rate"):
            assert 0.0 <= s[f] <= 1.0
        assert s["completed_count"] <= s["accepted_count"]
        assert s["count_rating_5_star"] <= s["total_order_rating"]


def test_r4_progress_le_target(gen):
    for p in gen["user_mission_progress"]:
        assert p["progress_count"] <= p["target_count"]


def test_weekly_rollup_covers_drivers(gen):
    daily_drivers = {r["driver_id"] for r in gen["driver_income_daily"]}
    weekly_drivers = {r["driver_id"] for r in gen["kpi_weekly_calculator"]}
    assert weekly_drivers == daily_drivers
