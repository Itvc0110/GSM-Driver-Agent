"""Schema registry — load + validate JSON Schema cho mọi entity L0–L3/advisor.

Spec: core-data-schema-and-advisor-architecture.md §1. Registry là NGUỒN SỰ THẬT
về contract dữ liệu; solver/agent/mockgen đều validate qua đây.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

# entity -> layer folder (23 entity theo spec §1.2–1.5 + §2–3)
LAYER_OF: dict[str, str] = {
    "policy_bundle": "l0", "driver_profile": "l0", "station_registry": "l0",
    "zone_map": "l0", "service_catalog": "l0",
    "app_event": "l1", "trip_record": "l1", "gps_ping": "l1",
    "swap_transaction": "l1", "payout_ledger": "l1", "policy_change_event": "l1",
    "supply_field": "l2", "demand_field": "l2", "station_state": "l2",
    "driver_day_state": "l2",
    "inferred_activity": "l2i",
    "shift_plan_input": "l3", "bonus_gap_input": "l3",
    "session_summary_input": "l3", "allocation_input": "l3",
    # PI-4b: view cho S5 (khoán tuần) + S6 (mission knapsack)
    "weekly_khoan_input": "l3", "mission_select_input": "l3",
    "advice_request": "advisor", "solver_report": "advisor", "composed_advice": "advisor",
    # l1r = L1-real: mirror 13 bảng thật gsm-data-prod (re-ground — UPDATE-033, PI-1)
    "driver_statistic_daily": "l1r", "driver_online_hours": "l1r",
    "driver_orders_rush_hours": "l1r", "driver_bike_stoppoints": "l1r",
    "kpi_weekly_calculator": "l1r", "driver_income_daily": "l1r",
    "trips": "l1r", "driver_hex_tracking": "l1r", "mission_catalog": "l1r",
    "mission_earn_history": "l1r", "user_mission_progress": "l1r",
    "driver_penalization": "l1r", "fraud_flag": "l1r",
}
ALL_ENTITIES: list[str] = sorted(LAYER_OF)
L1R_ENTITIES: list[str] = sorted(e for e, layer in LAYER_OF.items() if layer == "l1r")


class SchemaRegistry:
    def __init__(self, schemas_dir: str | Path):
        self.dir = Path(schemas_dir)

    @lru_cache(maxsize=None)
    def schema(self, entity: str) -> dict:
        layer = LAYER_OF[entity]
        path = self.dir / layer / f"{entity}.schema.json"
        return json.loads(path.read_text(encoding="utf-8"))

    @lru_cache(maxsize=None)
    def _validator(self, entity: str) -> Draft202012Validator:
        return Draft202012Validator(self.schema(entity))

    def schema_version(self, entity: str) -> str:
        return self.schema(entity)["properties"]["schema_version"]["const"]

    def validate(self, entity: str, record: dict) -> list[str]:
        """Trả list lỗi (rỗng = hợp lệ)."""
        return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
                for e in self._validator(entity).iter_errors(record)]

    def validate_many(self, entity: str, records: list[dict]) -> dict[int, list[str]]:
        """Validate hàng loạt: {index: errors} chỉ chứa record lỗi."""
        out: dict[int, list[str]] = {}
        for i, r in enumerate(records):
            errs = self.validate(entity, r)
            if errs:
                out[i] = errs
        return out
