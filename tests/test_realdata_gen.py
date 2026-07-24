"""PI-2/PI-2b — generator realdata (profile-driven) sinh 13 bảng l1r hợp lệ + nhất quán.

R1 schema+FK, R3 cross-table (aggregate↔trips), R4 bounds. + PI-2b: acceptance realistic
(không degenerate 1.00), profile universe đa dạng (car/bike/premium).
"""

import statistics as st
from collections import defaultdict
from pathlib import Path

import pytest

from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.schema_registry import SchemaRegistry, L1R_ENTITIES

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def res(tmp_path_factory):
    out = tmp_path_factory.mktemp("realdata")
    return generate_realdata(days=8, seed_base=100, out_dir=out)


@pytest.fixture(scope="module")
def gen(res):
    return res["tables"]


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


def test_all_13_tables_present(gen):
    assert set(gen) == set(L1R_ENTITIES)
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
    inc = {(r["driver_id"], r["order_date"]): r for r in gen["driver_income_daily"]}
    for r in gen["driver_orders_rush_hours"]:
        key = (r["driver_id"], r["local_date"])
        assert inc[key]["total_fee"] == r["total_fee"]
        assert r["total_fee_normal_hour"] + r["total_fee_rush_hour"] == r["total_fee"]
        assert r["total_order_normal_hour"] + r["total_order_rush_hour"] == r["total_order"]
        assert r["commission_normal_hour"] + r["commission_rush_hour"] == r["commission"]


def test_r3_commission_per_driver_share(res):
    """commission = round(total_fee × driver_share) — share theo profile (bike .75/rto .90/car .25/.75)."""
    uni = res["universe"]
    for r in res["tables"]["driver_income_daily"]:
        share = uni[r["driver_id"]]["driver_share"]
        assert r["commission"] == int(round(r["total_fee"] * share))


def test_r3_completed_equals_orders(gen):
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


# ---------- PI-2b: realism + diversity ----------

def test_acceptance_realistic_not_degenerate(gen):
    """Caveat R2 fixed: acceptance KHÔNG degenerate ở 1.00 — median < 0.98, có spread."""
    accs = [s["acceptance_rate"] for s in gen["driver_statistic_daily"]]
    assert st.median(accs) < 0.98, f"acceptance median {st.median(accs)} vẫn quá cao"
    assert min(accs) < 0.85, "phải có tài xế acceptance thấp (newbie ~0.74)"
    assert st.pstdev(accs) > 0.02, "acceptance phải có variance (randomness)"


def test_profile_universe_diverse(res):
    kinds = {p["kind"] for p in res["universe"].values()}
    assert {"bike_platform", "car_platform", "car_employee", "car_premium"} <= kinds
    services = {p["service_type"] for p in res["universe"].values()}
    assert services == {"bike", "car"}


def test_car_drivers_present_in_data(gen, res):
    """Tài xế car/premium (rule-based) xuất hiện trong KPI tables."""
    car_ids = {d for d, p in res["universe"].items() if p["service_type"] == "car"}
    income_ids = {r["driver_id"] for r in gen["driver_income_daily"]}
    assert car_ids & income_ids, "car drivers phải có income record"
    # car premium fare cao → có driver payout/ngày cao hơn bike
    car_trips = [t for t in gen["trips"] if t["driver_id"] in car_ids]
    assert car_trips and max(t["gross_vnd"] for t in car_trips) > 40000
