"""PI-1 — 13 schema l1r (mirror bảng thật gsm-data-prod) validate được.

Mỗi entity: 1 record ví dụ hợp lệ + kiểm PII/TBC annotation + registry nhận layer.
"""

import json
from pathlib import Path

import pytest

from gsm_core.schema_registry import SchemaRegistry, L1R_ENTITIES

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


# record ví dụ hợp lệ per entity (đủ required, nhãn MOCK)
EXAMPLES = {
    "driver_statistic_daily": {
        "schema_version": "1.0.0", "source": "MOCK", "local_date": "2026-07-01",
        "driver_id": "d-7", "completed_count": 18, "accepted_count": 20, "cancelled_count": 1,
        "total_request_calculate_accept": 22, "acceptance_rate": 0.9,
        "fulfillment_rate": 0.9, "cancellation_rate": 0.05,
        "total_rating": 84.6, "total_order_rating": 18, "count_rating_5_star": 15,
        "count_cancel_not_relate_driver": 1,
        "total_request_calculate_complete": 20, "total_request_calculate_cancel": 2},
    "driver_online_hours": {
        "schema_version": "1.0.0", "source": "MOCK", "local_date": "2026-07-01",
        "driver_id": "d-7", "online_time": 8.5, "driver_type": "bike",
        "full_name": "MOCK Driver 0007", "phone_number": "+8490MOCK007"},
    "driver_orders_rush_hours": {
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": "d-7",
        "local_date": "2026-07-01", "total_order": 18, "commission": 270000, "total_fee": 360000,
        "revenue_not_relate_driver": 90000, "total_order_normal_hour": 10,
        "commission_normal_hour": 150000, "total_fee_normal_hour": 200000,
        "revenue_not_relate_driver_normal_hour": 50000, "total_order_rush_hour": 8,
        "commission_rush_hour": 120000, "total_fee_rush_hour": 160000,
        "revenue_not_relate_driver_rush_hour": 40000},
    "driver_bike_stoppoints": {
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": "d-7",
        "local_date": "2026-07-01", "total_stoppoints": 22, "total_stoppoints_rush_hour": 9},
    "kpi_weekly_calculator": {
        "schema_version": "1.0.0", "source": "MOCK", "id": "kpi-1", "driver_id": "d-7",
        "week_key": "2026-W27", "week_start": "2026-06-29", "week_end": "2026-07-05",
        "status": "active", "type": "platform"},
    "driver_income_daily": {
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": "d-7",
        "order_date": "2026-07-01", "commission": 270000, "total_order": 18,
        "total_fee": 360000, "revenue_not_relate_driver": 90000,
        "avg_daily_revenue": 20000.0, "total_core_order": 17},
    "trips": {
        "schema_version": "1.0.0", "source": "MOCK", "trip_id": "o-7-3", "driver_id": "d-7",
        "service_type": "bike", "status": "completed", "request_time": "2026-07-01T17:00:00+07:00",
        "pickup_h3": "8abc", "drop_h3": "8def", "gross_vnd": 20000, "commission_vnd": 15000,
        "rush_hour": True, "distance_km": 3.2},
    "driver_hex_tracking": {
        "schema_version": "1.0.0", "source": "MOCK", "id": "hx-1", "driver_id": "d-7",
        "current_hex": "8abc", "last_seen_at": "2026-07-01T17:05:00+07:00",
        "stay_duration_seconds": 320, "tracking_status": "idle"},
    "mission_catalog": {
        "schema_version": "1.0.0", "source": "MOCK", "id": "m-1", "mission_type": "trip_count",
        "name": "20 chuyến khung vàng", "start_time": "2026-07-01T16:00:00+07:00",
        "end_time": "2026-07-01T19:59:00+07:00", "rewards": {"vnd": 30000}},
    "mission_earn_history": {
        "schema_version": "1.0.0", "source": "MOCK", "id": "eh-1", "mission_id": "m-1",
        "driver_id": "d-7", "earn": 30000, "count_order": 20, "count_stoppoint": 5},
    "user_mission_progress": {
        "schema_version": "1.0.0", "source": "MOCK", "id": "ump-1", "driver_id": "d-7",
        "mission_id": "m-1", "progress_count": 12, "target_count": 20, "state": "in_progress",
        "started_at": "2026-07-01T16:00:00+07:00", "progress_value_vnd": 0, "target_value_vnd": 30000},
    "driver_penalization": {
        "schema_version": "1.0.0", "source": "MOCK", "penalization_id": "pen-1", "driver_id": "d-7",
        "local_date": "2026-07-05", "penalty_type": "clawback_khoan", "amount_vnd": 40000,
        "status": "applied", "created_at": "2026-07-05T23:00:00+07:00"},
    "fraud_flag": {
        "schema_version": "1.0.0", "source": "INFERRED", "fraud_id": "f-1", "driver_id": "d-7",
        "detected_at": "2026-07-01T18:00:00+07:00", "fraud_type": "route_deviation",
        "severity": "low", "confidence": 0.4, "status": "open",
        "created_at": "2026-07-01T18:00:00+07:00"},
}


def test_all_13_registered():
    assert len(L1R_ENTITIES) == 13
    assert set(L1R_ENTITIES) == set(EXAMPLES)


@pytest.mark.parametrize("entity", sorted(EXAMPLES))
def test_example_validates(reg, entity):
    assert reg.validate(entity, EXAMPLES[entity]) == []
    assert reg.schema_version(entity) == "1.0.0"


@pytest.mark.parametrize("entity", sorted(EXAMPLES))
def test_additional_props_rejected(reg, entity):
    bad = dict(EXAMPLES[entity], _junk=1)
    assert reg.validate(entity, bad) != []


def test_pii_scrubbed_record_still_valid(reg):
    """Record sau khi tool P4 DROP PII (bỏ full_name/phone) vẫn validate (PII optional)."""
    rec = dict(EXAMPLES["driver_online_hours"])
    rec.pop("full_name"); rec.pop("phone_number")
    assert reg.validate("driver_online_hours", rec) == []


def test_engineered_tables_flagged_tbc():
    """4 bảng ENGINEER (thiếu cột thật) phải có nhãn x-availability TBC."""
    for entity in ("trips", "user_mission_progress", "driver_penalization", "fraud_flag"):
        s = json.loads((ROOT / "schemas" / "l1r" / f"{entity}.schema.json").read_text(encoding="utf-8"))
        assert "TBC" in s.get("x-availability", ""), f"{entity} thiếu nhãn TBC"


def test_pii_columns_annotated():
    """Bảng có driver_id phải khai x-pii-columns (cho tool scrub)."""
    for entity in ("driver_statistic_daily", "kpi_weekly_calculator", "trips"):
        s = json.loads((ROOT / "schemas" / "l1r" / f"{entity}.schema.json").read_text(encoding="utf-8"))
        assert "driver_id" in s.get("x-pii-columns", [])
