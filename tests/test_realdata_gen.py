"""PI-2/PI-2b — generator realdata (profile-driven) sinh 13 bảng l1r hợp lệ + nhất quán.

R1 schema+FK, R3 cross-table (aggregate↔trips), R4 bounds. + PI-2b: acceptance realistic
(không degenerate 1.00), profile universe đa dạng (car/bike/premium).
"""

import statistics as st
from collections import defaultdict
from pathlib import Path

import pytest

from gsm_core.mockgen.realdata import generate_realdata, write_table_parquet
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
    missions = {m["id"] for m in gen["public_mission"]}
    for eh in gen["public_mission_earn_history"]:
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
    for p in gen["public_user_mission_progress"]:
        assert p["progress_count"] <= p["target_count"]


def test_weekly_rollup_covers_drivers(gen):
    daily_drivers = {r["driver_id"] for r in gen["driver_income_daily"]}
    weekly_drivers = {r["driver_id"] for r in gen["kpi_driver_platform_calculator_gbq"]}
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


# ---------- regression: 4 flaw phát hiện khi audit PI-2b ----------

def test_bug02_no_trips_while_offline(gen):
    """BUG-PI2b-02: KHÔNG được có cuốc khi online_time=0 (impossible state / conservation)."""
    onl = {(r["driver_id"], r["local_date"]): r["online_time"] for r in gen["driver_online_hours_sap_id"]}
    for r in gen["driver_income_daily"]:
        if r["total_order"] > 0:
            h = onl.get((r["driver_id"], r["order_date"]), 0.0)
            assert h > 0.0, f"{r['driver_id']} {r['order_date']}: {r['total_order']} cuốc nhưng online={h}"


def test_bug02_trips_per_hour_plausible(gen):
    """Hệ quả BUG-02: cuốc/giờ phải hợp lý (≤6/h) — sàn online = trip_hours/0.55."""
    onl = {(r["driver_id"], r["local_date"]): r["online_time"] for r in gen["driver_online_hours_sap_id"]}
    for r in gen["driver_income_daily"]:
        h = onl.get((r["driver_id"], r["order_date"]), 0.0)
        if h > 0.5 and r["total_order"] > 0:
            assert r["total_order"] / h <= 6.0, f"{r['driver_id']}: {r['total_order']/h:.1f} cuốc/h"


def test_bug03_trips_stay_within_day(gen):
    """BUG-PI2b-03: complete_time không tràn sang ngày khác (giữ bất biến R3 mọi seed)."""
    for t in gen["trips"]:
        assert t["complete_time"][:10] == t["request_time"][:10], t["trip_id"]


def test_bug04_fields_not_degenerate(gen):
    """BUG-PI2b-04: core_order và stoppoints KHÔNG được == total_order với mọi record."""
    inc = gen["driver_income_daily"]
    assert any(r["total_core_order"] < r["total_order"] for r in inc), "core_order degenerate"
    assert all(r["total_core_order"] <= r["total_order"] for r in inc), "core_order > total"
    tot = {(r["driver_id"], r["order_date"]): r["total_order"] for r in inc}
    stops = gen["driver_bike_stoppoints"]
    assert any(s["total_stoppoints"] != tot.get((s["driver_id"], s["local_date"]), -1) for s in stops), \
        "stoppoints degenerate (== số cuốc mọi record)"
    for s in stops:  # stoppoint ≥ số cuốc (mỗi cuốc ≥1 điểm trả) + rush ⊆ total
        assert s["total_stoppoints"] >= tot.get((s["driver_id"], s["local_date"]), 0)
        assert s["total_stoppoints_rush_hour"] <= s["total_stoppoints"]


def test_bug05_sparse_nullable_column_writes(tmp_path):
    """BUG-PI2b-05: cột THƯA (None 120 dòng đầu rồi mới có str) phải ghi parquet được.

    Trước fix: `pl.DataFrame` chỉ suy kiểu 100 dòng đầu → Null dtype → ComputeError
    "could not append value ... to the builder" (crash phụ thuộc seed).
    """
    records = [{"id": f"r{i}", "campaign_id": None, "target_hex": None} for i in range(120)]
    records.append({"id": "r120", "campaign_id": "repo-01", "target_hex": "8amock42"})
    n = write_table_parquet(records, tmp_path / "sparse.parquet")
    assert n == 121
    import polars as pl
    back = pl.read_parquet(tmp_path / "sparse.parquet")
    assert back.height == 121
    assert back["campaign_id"].to_list()[-1] == "repo-01"


def test_car_drivers_present_in_data(gen, res):
    """Tài xế car/premium (rule-based) xuất hiện trong KPI tables."""
    car_ids = {d for d, p in res["universe"].items() if p["service_type"] == "car"}
    income_ids = {r["driver_id"] for r in gen["driver_income_daily"]}
    assert car_ids & income_ids, "car drivers phải có income record"
    # car premium fare cao → có driver payout/ngày cao hơn bike
    car_trips = [t for t in gen["trips"] if t["driver_id"] in car_ids]
    assert car_trips and max(t["gross_vnd"] for t in car_trips) > 40000
