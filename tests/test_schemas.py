"""T-038 C0 — schema registry tests (TDD: viết trước, đỏ → xanh).

Mọi entity trong spec core-data-schema §1.2–1.5 + advisor I/O §2–3 phải có JSON Schema
parse được, validate đúng record hợp lệ, và bắt đúng record hỏng.
"""

from pathlib import Path

import pytest

from gsm_core.schema_registry import SchemaRegistry, ALL_ENTITIES

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


# Danh sách entity BẮT BUỘC theo spec (23 schema)
EXPECTED = {
    # L0
    "policy_bundle", "driver_profile", "station_registry", "zone_map", "service_catalog",
    # L1
    "app_event", "trip_record", "gps_ping", "swap_transaction", "payout_ledger",
    "policy_change_event",
    # L2
    "supply_field", "demand_field", "station_state", "driver_day_state",
    # L2i
    "inferred_activity",
    # L3
    "shift_plan_input", "bonus_gap_input", "session_summary_input", "allocation_input",
    # advisor
    "advice_request", "solver_report", "composed_advice",
}


def test_all_entities_registered():
    assert set(ALL_ENTITIES) == EXPECTED


def test_all_schemas_load_and_have_version(reg):
    for e in ALL_ENTITIES:
        s = reg.schema(e)
        assert s["$id"], e
        assert reg.schema_version(e) == "1.0.0", e


VALID = {
    "app_event": {
        "schema_version": "1.0.0", "event_id": "ev-1", "driver_id": "d-1",
        "t": "2026-07-23T08:00:00+07:00", "kind": "go_online", "source": "MOCK",
    },
    "trip_record": {
        "schema_version": "1.0.0", "order_id": "o-1", "driver_id": "d-1",
        "service_type": "bike", "t_request": "2026-07-23T08:00:00+07:00",
        "t_assign": "2026-07-23T08:01:00+07:00", "t_pickup": "2026-07-23T08:05:00+07:00",
        "t_complete": "2026-07-23T08:20:00+07:00",
        "pickup": {"lat": 21.01, "lon": 105.82, "h3": "892ab13a677ffff"},
        "drop": {"lat": 21.02, "lon": 105.83, "h3": "892ab13a67bffff"},
        "dist_km": 3.2, "gross_vnd": 22000, "source": "MOCK",
    },
    "payout_ledger": {
        "schema_version": "1.0.0", "entry_id": "p-1", "driver_id": "d-1",
        "t": "2026-07-23T08:20:00+07:00", "kind": "trip_payout", "amount_vnd": 16500,
        "basis": {"trip_id": "o-1", "policy_bundle_version": "sim-policy-v0"},
        "gross_vnd": 22000, "source": "MOCK",
    },
    "solver_report": {
        "schema_version": "1.0.0", "solver": "bonus_feasibility",
        "problem_digest": "Gap 40 điểm tới mốc 160; quỹ 3h",
        "inputs_used": [{"view_id": "bonus_gap_input:d-1", "version": "1.0.0",
                         "freshness": "2026-07-23T08:00:00+07:00"}],
        "solution": {"trips_needed": 8, "hours_needed": 2.5, "feasible": True},
        "numbers": [{"value": 115000, "unit": "vnd", "source": "policy_v:sim-policy-v0"}],
        "sensitivity": [], "confidence": 0.9, "caveats": [], "infeasible_reason": None,
    },
}


@pytest.mark.parametrize("entity", sorted(VALID))
def test_valid_records_pass(reg, entity):
    assert reg.validate(entity, VALID[entity]) == []


def test_invalid_kind_rejected(reg):
    bad = dict(VALID["app_event"], kind="teleport_home")  # ngoài enum action-space
    errs = reg.validate("app_event", bad)
    assert errs, "kind ngoài enum phải fail"


def test_negative_money_rejected(reg):
    bad = dict(VALID["trip_record"], gross_vnd=-5000)
    assert reg.validate("trip_record", bad), "tiền âm phải fail"


def test_missing_source_label_rejected(reg):
    bad = {k: v for k, v in VALID["trip_record"].items() if k != "source"}
    assert reg.validate("trip_record", bad), "thiếu nhãn source (MOCK/REAL) phải fail"


def test_latent_fields_absent_from_l1():
    """Taxonomy §3.5: latent (meals_taken, fatigue, belief, patience) KHÔNG được có trong L1."""
    import json
    for name in ("app_event", "trip_record", "gps_ping", "swap_transaction", "payout_ledger"):
        raw = json.dumps(json.load(open(ROOT / "schemas" / "l1" / f"{name}.schema.json", encoding="utf-8")))
        for latent in ("meals_taken", "fatigue", "belief", "patience", "demand_prior"):
            assert latent not in raw, f"latent '{latent}' lọt vào L1 {name}"


def test_inferred_activity_requires_rule_version(reg):
    rec = {"schema_version": "1.0.0", "driver_id": "d-1",
           "t_start": "2026-07-23T12:00:00+07:00", "t_end": "2026-07-23T12:40:00+07:00",
           "label": "rest_likely", "confidence": 0.7, "source": "MOCK"}
    errs = reg.validate("inferred_activity", rec)
    assert errs, "thiếu inference_rule_version phải fail (INFERRED bắt buộc có rule version)"
    rec["inference_rule_version"] = "infer-v1"
    assert reg.validate("inferred_activity", rec) == []
