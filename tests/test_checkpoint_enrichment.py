"""Regression tests cho UPDATE-147 — nền móng AdviceCheckpoint.

Mỗi test tái hiện một lỗi/gap đã đo được trong discovery UPDATE-146:

1. validity 1 phút giả (freshness hardcode now+1) che boundary thật của solver;
2. action_window = None trên 100% record dù schedule có bucket labels;
3. numbers/caveats của solver report bị vứt khi normalize;
4. fingerprint không chứa future head ⇒ plan đổi vẫn bị dedup;
5. record thiếu fingerprint sau persist ⇒ dedup product không bao giờ khớp;
6. ready→queued không được phép ⇒ moving gate không để lại dấu vết lifecycle;
7. record 1.1.0 cũ phải upcast được lên 1.2.0.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.lifecycle.checkpoint import (
    CHECKPOINT_RECORD_FIELDS,
    checkpoint_fingerprint,
    checkpoint_record,
    normalize_solver_decision,
    project_checkpoint_events,
)
from gsm_core.upcasters import upcast
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parents[1]


def _snapshot(**overrides) -> dict:
    snap = {
        "run_id": "run-1",
        "driver_id": "d-7",
        "now_min": 540.0,
        "observed_at": "2026-07-01T09:00:00+07:00",
        "freshness_deadline": "2026-07-01T09:30:00+07:00",
        "shift_end": "2026-07-01T18:00:00+07:00",
        "actor_state": "idle",
        "zone_h3": "cell-1",
        "soc_pct": 42.0,
        "points": 10,
        "data_mode": "synthetic",
        "is_mock": True,
    }
    snap.update(overrides)
    return snap


def _s2_report(schedule=None, numbers=None, caveats=None) -> dict:
    return {
        "schema_version": "1.0.0",
        "solver": "shift_dp",
        "confidence": 0.8,
        "solution": {
            "schedule": schedule or [
                {"bucket": "2026-07-01T09:00:00+07:00", "action": "SWAP"},
                {"bucket": "2026-07-01T10:00:00+07:00", "action": "ONLINE"},
                {"bucket": "2026-07-01T11:00:00+07:00", "action": "REST"},
            ],
            "next_action": {"action": "SWAP",
                            "bucket": "2026-07-01T09:00:00+07:00",
                            "reason": "đổi pin trước khi cạn"},
        },
        "numbers": numbers if numbers is not None else [
            {"value": 512000.0, "unit": "vnd", "source": "dp:historical_forecast"},
        ],
        "caveats": caveats if caveats is not None else [
            "số cuốc thực phụ thuộc nhu cầu (forecast lịch sử) — không đảm bảo",
        ],
    }


def _normalize_s2(**snap_overrides) -> dict:
    return normalize_solver_decision(
        "S2", _snapshot(**snap_overrides), {"schema_version": "1.1.0"},
        _s2_report(), "slth-run-1-7-shift_plan-18")


# ---------- 1. validity thật, không phải +1 phút ----------

def test_s2_validity_uses_bucket_end_hint_not_fake_freshness():
    candidate = _normalize_s2(bucket_end="2026-07-01T10:00:00+07:00")
    # min(bucket_end 10:00, shift_end 18:00, freshness 09:30) = 09:30 (chu kỳ consult thật)
    assert candidate["validity"]["valid_until"] == "2026-07-01T09:30:00+07:00"
    # còn khi freshness xa hơn bucket ⇒ bucket_end thắng
    candidate = _normalize_s2(bucket_end="2026-07-01T10:00:00+07:00",
                              freshness_deadline="2026-07-01T12:00:00+07:00")
    assert candidate["validity"]["valid_until"] == "2026-07-01T10:00:00+07:00"


def test_s7_validity_uses_rest_window_end_hint():
    report = {"schema_version": "1.0.0", "solver": "idle_reduction",
              "confidence": 0.7,
              "solution": {"notable": True, "worst_window": {"hour": 13}}}
    candidate = normalize_solver_decision(
        "S7", _snapshot(rest_window_end="2026-07-01T14:00:00+07:00",
                        freshness_deadline="2026-07-01T16:00:00+07:00"),
        {}, report, "slth-run-1-7-rest_window-18")
    assert candidate["validity"]["valid_until"] == "2026-07-01T14:00:00+07:00"


# ---------- 2. action_window tổng hợp từ bucket labels ----------

def test_s2_action_window_derived_from_schedule_buckets():
    candidate = _normalize_s2()
    assert candidate["current_action"]["code"] == "SWAP"
    assert candidate["action_window"] == {
        "start": "2026-07-01T09:00:00+07:00",
        "end": "2026-07-01T10:00:00+07:00",
    }
    # future: normalize_shift_plan prepend next_action (hành vi có sẵn) rồi tới
    # ONLINE 10:00 / REST 11:00 — mọi bucket label đều được gắn window grid
    fut = candidate["future_plan"]
    assert fut[0]["code"] == "SWAP"  # echo next_action của solver (pre-existing)
    assert fut[0]["window"] == {"start": "2026-07-01T09:00:00+07:00",
                                "end": "2026-07-01T10:00:00+07:00"}
    assert fut[1]["code"] == "ONLINE"
    assert fut[1]["window"] == {"start": "2026-07-01T10:00:00+07:00",
                                "end": "2026-07-01T11:00:00+07:00"}


def test_s2_single_bucket_schedule_uses_bucket_end_hint_for_window():
    report = _s2_report(schedule=[
        {"bucket": "2026-07-01T09:00:00+07:00", "action": "SWAP"}])
    candidate = normalize_solver_decision(
        "S2", _snapshot(bucket_end="2026-07-01T10:00:00+07:00"),
        {}, report, "sd-1")
    assert candidate["action_window"] == {
        "start": "2026-07-01T09:00:00+07:00",
        "end": "2026-07-01T10:00:00+07:00",
    }


def test_s2_missing_bucket_labels_keeps_window_none_not_invented():
    report = _s2_report(schedule=[{"bucket": None, "action": "SWAP"},
                                  {"bucket": None, "action": "ONLINE"}])
    candidate = normalize_solver_decision("S2", _snapshot(), {}, report, "sd-2")
    assert candidate["action_window"] is None


# ---------- 3. numbers/caveats vào candidate + record ----------

def test_record_carries_numbers_caveats_fingerprint():
    candidate = _normalize_s2()
    record = checkpoint_record(candidate)
    assert record["schema_version"] == "1.2.0"
    assert record["numbers"] == candidate["numbers"]
    assert record["numbers"][0]["unit"] == "vnd"
    assert record["caveats"][0].startswith("số cuốc thực")
    assert record["fingerprint"] == candidate["fingerprint"]
    assert {"numbers", "caveats", "fingerprint"} <= set(CHECKPOINT_RECORD_FIELDS)


# ---------- 4. fingerprint phân biệt future head ----------

def test_fingerprint_changes_when_future_head_changes():
    swap_at_10 = _s2_report(schedule=[
        {"bucket": "2026-07-01T09:00:00+07:00", "action": "ONLINE"},
        {"bucket": "2026-07-01T10:00:00+07:00", "action": "SWAP"},
    ])
    swap_at_11 = _s2_report(schedule=[
        {"bucket": "2026-07-01T09:00:00+07:00", "action": "ONLINE"},
        {"bucket": "2026-07-01T11:00:00+07:00", "action": "SWAP"},
    ])
    a = normalize_solver_decision("S2", _snapshot(), {}, swap_at_10, "sd-a")
    b = normalize_solver_decision("S2", _snapshot(), {}, swap_at_11, "sd-b")
    assert a["fingerprint"] != b["fingerprint"]
    assert a["checkpoint_id"] != b["checkpoint_id"]


def test_fingerprint_stable_for_identical_material():
    a = normalize_solver_decision("S2", _snapshot(), {}, _s2_report(), "sd-a")
    b = normalize_solver_decision("S2", _snapshot(), {}, _s2_report(), "sd-b")
    assert a["fingerprint"] == b["fingerprint"]


def test_persisted_record_fingerprint_matches_recompute():
    """Dedup product so record đã persist với candidate mới — phải khớp được."""
    candidate = _normalize_s2()
    record = checkpoint_record(candidate)
    assert checkpoint_fingerprint(record) == record["fingerprint"]


# ---------- 5. ready→queued→ready (moving gate để lại dấu vết) ----------

def test_ready_to_queued_and_back_is_legal():
    events = [
        {"event_id": "e1", "checkpoint_id": "c", "driver_id": "d",
         "event_type": "created", "occurred_at": "2026-07-01T09:00:00+07:00"},
        {"event_id": "e2", "checkpoint_id": "c", "driver_id": "d",
         "event_type": "ready", "occurred_at": "2026-07-01T09:00:01+07:00"},
        {"event_id": "e3", "checkpoint_id": "c", "driver_id": "d",
         "event_type": "queued", "occurred_at": "2026-07-01T09:05:00+07:00"},
        {"event_id": "e4", "checkpoint_id": "c", "driver_id": "d",
         "event_type": "ready", "occurred_at": "2026-07-01T09:10:00+07:00"},
        {"event_id": "e5", "checkpoint_id": "c", "driver_id": "d",
         "event_type": "offered", "occurred_at": "2026-07-01T09:10:01+07:00",
         "display_id": "disp-1"},
    ]
    projected = project_checkpoint_events(events)
    assert projected["state"] == "offered"


# ---------- 6. schema 1.2.0 + upcaster ----------

def _registry() -> SchemaRegistry:
    return SchemaRegistry(ROOT / "schemas")


def test_new_record_validates_against_schema_1_2_0():
    record = checkpoint_record(_normalize_s2())
    # sim capture điền refs artifact; unit test tự điền tham chiếu tối thiểu
    record["snapshot_ref"] = "state_snapshot:sha256:abc"
    record["solver_artifact_ref"] = "solver_artifact:sha256:abc"
    record["solver_input_refs"] = ["solver_input:sha256:abc"]
    record["solver_report_refs"] = ["solver_report:sha256:abc"]
    assert _registry().validate("advice_checkpoint", record) == []


def test_old_1_1_0_record_upcasts_to_1_2_0():
    old = {
        "schema_version": "1.1.0",
        "checkpoint_id": "ckpt-old", "driver_id": "d-1",
        "topic": "energy", "surface": "nudge", "trigger_type": "solver_update",
        "current_action": {"code": "SWAP", "label_id": "action.swap"},
        "future_plan": [], "action_window": None,
        "validity": {"valid_from": "2026-07-01T09:00:00+07:00",
                     "valid_until": "2026-07-01T09:01:00+07:00",
                     "freshness_deadline": "2026-07-01T09:01:00+07:00"},
        "urgency_band": "medium", "material_revision": "1",
        "reason_code": "solver_recommendation", "confidence_band": "medium",
        "snapshot_ref": "state_snapshot:sha256:x",
        "solver_artifact_ref": "solver_artifact:sha256:x",
        "source_decision_id": "sd", "run_id": "run-1",
        "solver_input_refs": ["solver_input:sha256:x"],
        "solver_report_refs": ["solver_report:sha256:x"],
        "solver_set": ["S2"], "data_mode": "synthetic", "is_mock": True,
        "created_at": "2026-07-01T09:00:00+07:00",
    }
    assert _registry().validate("advice_checkpoint", old) == []
    up = upcast("advice_checkpoint", old)
    assert up["schema_version"] == "1.2.0"
    assert up["numbers"] == []
    assert up["caveats"] == []
    assert up["fingerprint"] == checkpoint_fingerprint(old)
    assert _registry().validate("advice_checkpoint", up) == []


def test_store_created_event_keeps_event_entity_version():
    """Checkpoint 1.2.0 KHÔNG được kéo event sang 1.2.0 (event là entity riêng 1.1.0)."""
    from gsm_core.lifecycle.checkpoint_store import _created_event
    record = checkpoint_record(_normalize_s2())
    event = _created_event(record)
    assert event["schema_version"] == "1.1.0"
    assert _registry().validate("advice_checkpoint_event", event) == []
