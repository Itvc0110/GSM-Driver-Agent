"""Scaffold 13 schema `l1r/*` (L1-real) mirror bảng thật gsm-data-prod (P2/PI-1).

Emit JSON (canonical sau khi emit — hand-edit về sau). 5 bảng thiếu cột được ENGINEER
sáng tạo, nhãn `x-availability: TBC-với-GSM`. PII field = optional (record sau khi
tool scrub bỏ PII vẫn validate). source enum + schema_version const bắt buộc.

Chạy:  uv run python scripts/build_l1r_schemas.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "schemas" / "l1r"
SV = "1.0.0"

_STR = {"type": "string"}
_STR_N = {"type": ["string", "null"]}
_INT = {"type": "integer", "minimum": 0}
_NUM = {"type": "number"}
_RATE = {"type": "number", "minimum": 0, "maximum": 1}
_VND = {"type": "integer", "description": "VND nguyên (không âm)", "minimum": 0}
_TS = {"type": "string", "description": "ISO-8601 UTC+7"}
_TS_N = {"type": ["string", "null"]}
_META_N = {"type": ["object", "null"], "description": "CDC Datastream metadata — không dùng logic"}


def schema(entity: str, title: str, desc: str, props: dict, required: list[str],
           pii: list[str] | None = None, tbc: bool = False) -> dict:
    p = dict(props)
    p["source"] = {"type": "string", "enum": ["MOCK", "REAL", "ESTIMATED", "COARSE", "INFERRED"],
                   "description": "Nhãn nguồn bắt buộc (CLAUDE.md §5)"}
    p["schema_version"] = {"const": SV}
    s = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://gsm-driver-agent/schemas/l1r/{entity}",
        "title": title, "description": desc, "type": "object",
        "properties": p,
        "required": sorted(set(required + ["source", "schema_version"])),
        "additionalProperties": False,
    }
    if pii:
        s["x-pii-columns"] = pii  # tool P4 đọc để drop/hash
    if tbc:
        s["x-availability"] = "TBC-với-GSM (bảng thiếu cột — field ENGINEER)"
    return s


SCHEMAS: dict[str, dict] = {}

# ---------- KPI daily (8 known-column tables) ----------

SCHEMAS["driver_statistic_daily"] = schema(
    "driver_statistic_daily", "driver_statistic_daily",
    "Snapshot KPI vận doanh daily (UC1/UC4). rate = count/request.",
    {
        "local_date": {"type": "string", "format": "date"}, "driver_id": _STR,
        "completed_count": _INT, "accepted_count": _INT, "cancelled_count": _INT,
        "total_request_calculate_complete": _INT, "total_request_calculate_cancel": _INT,
        "total_request_calculate_accept": _INT, "count_cancel_not_relate_driver": _INT,
        "total_rating": {"type": ["number", "null"]}, "total_order_rating": _INT,
        "count_rating_5_star": _INT,
        "acceptance_rate": _RATE, "fulfillment_rate": _RATE, "cancellation_rate": _RATE,
    },
    ["local_date", "driver_id", "completed_count", "accepted_count", "cancelled_count",
     "acceptance_rate", "fulfillment_rate", "cancellation_rate"],
    pii=["driver_id"])

SCHEMAS["driver_online_hours"] = schema(
    "driver_online_hours", "driver_online_hours",
    "Số giờ online/ngày (UC1). PII (full_name/phone/sap) optional — tool scrub bỏ.",
    {
        "local_date": {"type": "string", "format": "date"},
        "schedule_date": {"type": ["string", "null"], "format": "date"},
        "driver_id": _STR, "full_name": _STR_N, "sap_profile_id": _STR_N,
        "hub_id": _STR_N, "depot_id": _STR_N, "phone_number": _STR_N,
        "driver_type": _STR_N, "online_time": {"type": "number", "minimum": 0, "description": "giờ"},
    },
    ["local_date", "driver_id", "online_time"],
    pii=["driver_id", "full_name", "sap_profile_id", "phone_number"])

SCHEMAS["driver_orders_rush_hours"] = schema(
    "driver_orders_rush_hours", "driver_orders_rush_hours",
    "Doanh số tách rush/normal hour (UC2). normal+rush=total.",
    {
        "driver_id": _STR, "local_date": {"type": "string", "format": "date"},
        "total_order": _INT, "commission": _VND, "total_fee": _VND,
        "revenue_not_relate_driver": _VND,
        "total_order_normal_hour": _INT, "commission_normal_hour": _VND,
        "total_fee_normal_hour": _VND, "revenue_not_relate_driver_normal_hour": _VND,
        "total_order_rush_hour": _INT, "commission_rush_hour": _VND,
        "total_fee_rush_hour": _VND, "revenue_not_relate_driver_rush_hour": _VND,
    },
    ["driver_id", "local_date", "total_order", "commission", "total_fee"],
    pii=["driver_id"])

SCHEMAS["driver_bike_stoppoints"] = schema(
    "driver_bike_stoppoints", "driver_bike_stoppoints",
    "Số điểm dừng/ngày (UC2/UC5 idle proxy). rush ⊆ total.",
    {
        "driver_id": _STR, "local_date": {"type": "string", "format": "date"},
        "total_stoppoints": _INT, "total_stoppoints_rush_hour": _INT,
    },
    ["driver_id", "local_date", "total_stoppoints", "total_stoppoints_rush_hour"],
    pii=["driver_id"])

SCHEMAS["kpi_weekly_calculator"] = schema(
    "kpi_weekly_calculator", "kpi_weekly_calculator",
    "Tính KPI tuần + thưởng (UC3) — NỀN S5 khoán. PII optional (scrub). "
    "Số target/threshold có thể ở meta → TBC.",
    {
        "id": _STR, "driver_id": _STR, "driver_name": _STR_N, "sap_id": _STR_N,
        "status": _STR_N, "week_key": _STR, "week_start": {"type": "string", "format": "date"},
        "week_end": {"type": "string", "format": "date"},
        "kpi_month": {"type": ["integer", "null"]}, "kpi_year": {"type": ["integer", "null"]},
        "email": _STR_N, "tel": _STR_N, "engname": _STR_N,
        "depot_code": _STR_N, "depot_name": _STR_N,
        "vehicle_vin_number": _STR_N, "vehicle_license_plate": _STR_N,
        "vehicle_model": _STR_N, "country": _STR_N, "type": _STR_N,
        "last_updated_date": _TS_N,
    },
    ["id", "driver_id", "week_key", "week_start", "week_end"],
    pii=["driver_id", "driver_name", "sap_id", "email", "tel",
         "vehicle_vin_number", "vehicle_license_plate"])

SCHEMAS["driver_income_daily"] = schema(
    "driver_income_daily", "driver_income_daily",
    "Thu nhập daily (UC3/UC4). commission=driver_payout; total_fee=gross; "
    "revenue_not_relate_driver=phần nền tảng. total_core_order ⊆ total_order.",
    {
        "driver_id": _STR, "order_date": {"type": "string", "format": "date"},
        "commission": _VND, "total_order": _INT, "total_fee": _VND,
        "revenue_not_relate_driver": _VND, "avg_daily_revenue": _NUM,
        "total_core_order": _INT,
    },
    ["driver_id", "order_date", "commission", "total_order", "total_fee"],
    pii=["driver_id"])

# ---------- events / mission (append) ----------

SCHEMAS["trips"] = schema(
    "trips", "trips",
    "Trip-level dispatch (UC5 mật độ cuốc). ENGINEER shape từ trip_record ta. customer_id drop.",
    {
        "trip_id": _STR, "driver_id": _STR, "customer_id": _STR_N,
        "service_type": _STR, "status": {"type": "string",
            "enum": ["completed", "cancelled", "assigned"]},
        "request_time": _TS, "assign_time": _TS_N, "pickup_time": _TS_N, "complete_time": _TS_N,
        "pickup_h3": _STR, "drop_h3": _STR,
        "distance_km": _NUM, "duration_seconds": {"type": ["integer", "null"]},
        "gross_vnd": _VND, "commission_vnd": _VND,
        "rush_hour": {"type": "boolean"}, "travel_mode": _STR_N,
        "created_at": _TS, "datastream_metadata": _META_N,
    },
    ["trip_id", "driver_id", "service_type", "status", "request_time",
     "pickup_h3", "drop_h3", "gross_vnd"],
    pii=["driver_id", "customer_id"], tbc=True)

SCHEMAS["driver_hex_tracking"] = schema(
    "driver_hex_tracking", "driver_hex_tracking",
    "Chuyển động H3 + reposition (UC5). target_hex/reached = reposition mission GSM.",
    {
        "id": _STR, "driver_id": _STR, "campaign_id": _STR_N, "log_id": _STR_N,
        "init_hex": _STR_N, "current_hex": _STR, "last_hex": _STR_N, "target_hex": _STR_N,
        "last_seen_at": _TS, "entered_current_hex_at": _TS_N,
        "stay_duration_seconds": _INT,
        "reached_target": {"type": ["boolean", "null"]}, "reached_target_at": _TS_N,
        "hex_history": {"type": ["array", "null"], "items": {"type": "string"}},
        "created_at": _TS, "updated_at": _TS_N, "schedule_job_id": _STR_N,
        "datastream_metadata": _META_N,
        "tracking_status": {"type": "string", "enum": ["moving", "idle", "offline"]},
    },
    ["id", "driver_id", "current_hex", "last_seen_at", "stay_duration_seconds", "tracking_status"],
    pii=["driver_id"])

SCHEMAS["mission_catalog"] = schema(
    "mission_catalog", "mission_catalog (public_mission)",
    "Catalog mini-task (UC8) — NỀN S6 knapsack. rewards + khung giờ + rule.",
    {
        "id": _STR, "created_at": _TS, "updated_at": _TS_N, "deleted_at": _TS_N,
        "created_by": _STR_N, "updated_by": _STR_N,
        "mission_type": {"type": "string",
            "enum": ["trip_count", "revenue", "rush_hour", "reposition", "rating", "stoppoint"]},
        "parent_id": _STR_N, "name": _STR, "state": _STR_N, "audience": _STR_N,
        "description": _STR_N, "start_time": _TS, "end_time": _TS,
        "point_id": _STR_N,
        "rewards": {"type": "object", "description": "phần thưởng (vnd/point) + điều kiện"},
        "mission_claim": _STR_N, "mission_code": _STR_N, "time_claim_reward": _STR_N,
        "rule_code": _STR_N, "meta_data": {"type": ["object", "null"]},
        "contract_type": _STR_N, "qualify_execute_code": _STR_N, "status": _STR_N,
        "datastream_metadata": _META_N, "business_code": _STR_N,
        "show_only": {"type": ["boolean", "null"]}, "is_ddi_mission": {"type": ["boolean", "null"]},
    },
    ["id", "mission_type", "name", "start_time", "end_time", "rewards"])

SCHEMAS["mission_earn_history"] = schema(
    "mission_earn_history", "mission_earn_history",
    "Lịch sử nhận thưởng mission (UC3/UC8). earn từ mission.rewards. customer_id drop.",
    {
        "id": _STR, "created_at": _TS, "updated_at": _TS_N, "deleted_at": _TS_N,
        "mission_id": _STR, "order_id": _STR_N, "order_status": _STR_N,
        "driver_id": _STR, "customer_id": _STR_N, "service_type": _STR_N,
        "order_time": _TS_N, "complete_time": _TS_N, "travel_mode": _STR_N,
        "sap_contract_type": _STR_N, "type": _STR_N,
        "count_order": _INT, "count_stoppoint": _INT, "earn": _VND,
        "description": _STR_N, "datastream_metadata": _META_N, "reward_level": _STR_N,
    },
    ["id", "mission_id", "driver_id", "earn", "count_order"],
    pii=["driver_id", "customer_id"])

# ---------- ENGINEER (thiếu cột) ----------

SCHEMAS["user_mission_progress"] = schema(
    "user_mission_progress", "user_mission_progress",
    "Tiến độ mission per driver (UC8) — ENGINEER. progress ≤ target.",
    {
        "id": _STR, "driver_id": _STR, "mission_id": _STR,
        "progress_count": _INT, "target_count": _INT,
        "progress_value_vnd": _VND, "target_value_vnd": _VND,
        "state": {"type": "string", "enum": ["in_progress", "completed", "claimed", "expired"]},
        "started_at": _TS, "updated_at": _TS_N, "claimed_at": _TS_N,
        "datastream_metadata": _META_N,
    },
    ["id", "driver_id", "mission_id", "progress_count", "target_count", "state"],
    pii=["driver_id"], tbc=True)

SCHEMAS["driver_penalization"] = schema(
    "driver_penalization", "driver_penalization (penalization_ATA)",
    "Sự kiện phạt/trừ tiền (UC6) — ENGINEER. amount có source policy.",
    {
        "penalization_id": _STR, "driver_id": _STR,
        "local_date": {"type": "string", "format": "date"}, "week_key": _STR_N,
        "penalty_type": {"type": "string",
            "enum": ["clawback_khoan", "conduct", "late", "acceptance", "other"]},
        "amount_vnd": _VND, "reason": _STR_N,
        "related_metric": _STR_N, "ata_code": _STR_N,
        "status": {"type": "string", "enum": ["applied", "pending", "waived"]},
        "created_at": _TS,
    },
    ["penalization_id", "driver_id", "local_date", "penalty_type", "amount_vnd", "status"],
    pii=["driver_id"], tbc=True)

SCHEMAS["fraud_flag"] = schema(
    "fraud_flag", "fraud_flag (public_frauds)",
    "Cờ bất thường (UC7) — ENGINEER, nhãn INFERRED, KHÔNG kết tội.",
    {
        "fraud_id": _STR, "driver_id": _STR, "detected_at": _TS,
        "fraud_type": {"type": "string",
            "enum": ["route_deviation", "gps_anomaly", "off_app", "abnormal_cancel", "multi_account"]},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "confidence": _RATE, "evidence_ref": _STR_N,
        "status": {"type": "string", "enum": ["open", "reviewing", "cleared", "confirmed"]},
        "created_at": _TS, "datastream_metadata": _META_N,
    },
    ["fraud_id", "driver_id", "detected_at", "fraud_type", "severity", "confidence", "status"],
    pii=["driver_id"], tbc=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(SCHEMAS) == 13, f"phải 13 schema, có {len(SCHEMAS)}"
    for entity, s in SCHEMAS.items():
        path = OUT / f"{entity}.schema.json"
        path.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.name}")
    print(f"OK: {len(SCHEMAS)} l1r schemas")


if __name__ == "__main__":
    main()
