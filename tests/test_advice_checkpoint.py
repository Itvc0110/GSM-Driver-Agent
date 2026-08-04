"""GĐ1 AdviceCheckpoint — contract, projection và store shadow.

Các test này cố ý không gọi simulator/backend. Checkpoint là presentation lifecycle
riêng; `decision_id` legacy không được dùng làm định danh thay thế.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from gsm_core.lifecycle.checkpoint import (
    CheckpointTransitionError,
    checkpoint_fingerprint,
    deduplicate_candidates,
    normalize_shift_plan,
    normalize_validity,
    project_checkpoint_events,
    select_primary_candidate,
)

ROOT = Path(__file__).resolve().parents[1]


def _checkpoint(**overrides) -> dict:
    record = {
        "schema_version": "1.0.0",
        "checkpoint_id": "ckpt-1",
        "driver_id": "d-1",
        "topic": "energy",
        "surface": "nudge",
        "trigger_type": "state_change",
        "current_action": {"code": "SWAP", "label_id": "action.swap"},
        "future_plan": [],
        "action_window": {"start": "2026-08-03T09:00:00+07:00",
                           "end": "2026-08-03T10:00:00+07:00"},
        "validity": {"valid_from": "2026-08-03T09:00:00+07:00",
                     "valid_until": "2026-08-03T10:00:00+07:00",
                     "freshness_deadline": "2026-08-03T09:30:00+07:00"},
        "urgency_band": "high",
        "material_revision": "rev-1",
        "reason_code": "soc_low",
        "confidence_band": "medium",
        "snapshot_ref": "sha256:snapshot-1",
        "solver_artifact_ref": "sha256:solver-1",
        "solver_set": ["S2"],
        "data_mode": "synthetic",
        "is_mock": True,
        "created_at": "2026-08-03T09:00:00+07:00",
    }
    record.update(overrides)
    return record


def _event(event_type: str, event_id: str, **overrides) -> dict:
    record = {
        "schema_version": "1.0.0",
        "event_id": event_id,
        "checkpoint_id": "ckpt-1",
        "driver_id": "d-1",
        "display_id": None,
        "event_type": event_type,
        "occurred_at": "2026-08-03T09:00:00+07:00",
        "actor": "system",
        "origin": "checkpoint",
        "reason_code": None,
        "relation_type": None,
        "confidence": None,
        "payload": {},
    }
    record.update(overrides)
    return record


def _happy_path() -> list[dict]:
    return [
        _event("created", "e-1"),
        _event("ready", "e-2", occurred_at="2026-08-03T09:00:01+07:00"),
        _event("generation_started", "e-3", occurred_at="2026-08-03T09:00:02+07:00",
               actor="system"),
        _event("generated", "e-4", occurred_at="2026-08-03T09:00:03+07:00",
               actor="system"),
        _event("offered", "e-5", occurred_at="2026-08-03T09:00:04+07:00",
               display_id="display-1"),
        _event("displayed", "e-6", occurred_at="2026-08-03T09:00:05+07:00",
               display_id="display-1", actor="client"),
        _event("accepted", "e-7", occurred_at="2026-08-03T09:00:06+07:00",
               actor="driver"),
    ]


def test_checkpoint_fingerprint_ignores_poll_and_presentation_metadata():
    a = _checkpoint(message="poll-a", solver_invocation_id="run-a")
    b = _checkpoint(message="poll-b", solver_invocation_id="run-b")
    assert checkpoint_fingerprint(a) == checkpoint_fingerprint(b)
    assert checkpoint_fingerprint({"topic": "energy", "recommendation": None})


def test_validity_is_normalized_per_solver_and_fails_closed_when_missing():
    assert normalize_validity(
        "S1", shift_end="2026-08-03T18:00:00+07:00",
        policy_effective_boundary="2026-08-03T09:30:00+07:00",
        freshness_deadline="2026-08-03T09:45:00+07:00",
    ) == "2026-08-03T09:30:00+07:00"
    assert normalize_validity(
        "S2", solver_bucket_end="2026-08-03T10:00:00+07:00",
        shift_end="2026-08-03T18:00:00+07:00",
        freshness_deadline="2026-08-03T09:45:00+07:00",
    ) == "2026-08-03T09:45:00+07:00"
    assert normalize_validity(
        "S4", allocation_bucket_end="2026-08-03T11:00:00+07:00",
        freshness_deadline="2026-08-03T10:30:00+07:00",
    ) == "2026-08-03T10:30:00+07:00"
    assert normalize_validity(
        "S7", rest_window_end="2026-08-03T12:00:00+07:00",
        shift_end="2026-08-03T18:00:00+07:00",
        freshness_deadline="2026-08-03T12:30:00+07:00",
    ) == "2026-08-03T12:00:00+07:00"
    assert normalize_validity("S2") is None


def test_shift_plan_normalizer_separates_current_from_future():
    current, future = normalize_shift_plan({
        "schedule": [
            {"bucket": "09:00", "action": "ONLINE"},
            {"bucket": "10:00", "action": "SWAP"},
        ],
        "next_action": {"bucket": "10:00", "action": "SWAP"},
    })
    assert current == {"bucket": "09:00", "action": "ONLINE"}
    assert future == [{"bucket": "10:00", "action": "SWAP"}]


def test_policy_deduplicates_and_selects_one_primary_deterministically():
    base = {"topic": "energy", "current_action": {"code": "SWAP"},
            "action_window": {"start": "2026-08-03T09:00:00+07:00"},
            "urgency_band": "high", "material_revision": "r1",
            "reason_code": "soc_low", "valid_until": "2026-08-03T10:00:00+07:00",
            "expected_impact": 10.0, "confidence": 0.7, "created_at": "2026-08-03T09:00:00+07:00"}
    duplicate = {**base, "message": "khác do polling"}
    later = {**base, "topic": "shift_timing", "reason_code": "maintenance",
             "valid_until": "2026-08-03T09:05:00+07:00"}
    unique = deduplicate_candidates([base, duplicate, later])
    assert len(unique) == 2
    assert select_primary_candidate(unique) is unique[0]


def test_checkpoint_replay_keeps_accepted_state_when_execution_is_observed():
    events = _happy_path() + [
        _event("execution_observed", "e-8", occurred_at="2026-08-03T09:10:00+07:00",
               actor="observer", relation_type="coincident", confidence=0.4,
               payload={"segment_id": "seg-1"}),
    ]
    state = project_checkpoint_events(events)
    assert state["state"] == "accepted"
    assert state["display_id"] == "display-1"
    assert state["execution_links"] == [
        {"event_id": "e-8", "segment_id": "seg-1", "relation_type": "coincident",
         "confidence": 0.4}
    ]


def test_expanded_is_side_channel_and_does_not_change_presentation_state():
    events = _happy_path()[:6] + [
        _event("expanded", "e-expand", occurred_at="2026-08-03T09:00:05.500000+07:00",
               display_id="display-1", actor="driver"),
    ]
    state = project_checkpoint_events(events)
    assert state["state"] == "displayed"
    assert state["expanded_event_ids"] == ["e-expand"]


def test_checkpoint_replay_rejects_terminal_regression():
    with pytest.raises(CheckpointTransitionError, match="terminal"):
        project_checkpoint_events(_happy_path() + [
            _event("offered", "e-8", occurred_at="2026-08-03T09:00:07+07:00",
                   display_id="display-2")
        ])


def test_checkpoint_replay_requires_created_before_state_events():
    with pytest.raises(CheckpointTransitionError, match="created"):
        project_checkpoint_events([_event("offered", "e-1")])


def test_checkpoint_replay_allows_deterministic_fallback_after_generation_failure():
    events = [
        _event("created", "e-1"),
        _event("ready", "e-2", occurred_at="2026-08-03T09:00:01+07:00"),
        _event("generation_started", "e-3", occurred_at="2026-08-03T09:00:02+07:00"),
        _event("generation_failed", "e-4", occurred_at="2026-08-03T09:00:03+07:00",
               reason_code="verifier_rejected"),
        _event("offered", "e-5", occurred_at="2026-08-03T09:00:04+07:00",
               display_id="display-1", origin="product"),
    ]
    assert project_checkpoint_events(events)["state"] == "offered"


def test_checkpoint_replay_is_deterministic_for_input_order():
    events = _happy_path()
    assert project_checkpoint_events(events) == project_checkpoint_events(list(reversed(events)))


def test_checkpoint_store_is_idempotent_and_persistent(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    path = tmp_path / "checkpoint.db"
    with CheckpointStore(path) as store:
        assert store.put_artifact("state_snapshot", {"driver_id": "d-1", "soc": 42})
        assert not store.put_artifact("state_snapshot", {"driver_id": "d-1", "soc": 42})
        assert store.create_checkpoint(_checkpoint()) is True
        assert store.create_checkpoint(_checkpoint()) is False
        assert store.append_event(_event("ready", "e-2")) is True
        assert store.append_event(_event("ready", "e-2")) is False
        assert store.state("ckpt-1")["state"] == "ready"

    with CheckpointStore(path) as store:
        assert store.state("ckpt-1")["state"] == "ready"
        assert len(store.events("ckpt-1")) == 2


def test_checkpoint_store_rejects_invalid_transition_before_persist(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        store.create_checkpoint(_checkpoint())
        with pytest.raises(CheckpointTransitionError):
            store.append_event(_event("displayed", "e-2", display_id="display-1",
                                      actor="client"))
        assert store.events("ckpt-1") == [_event("created", "created:ckpt-1")]


def test_checkpoint_store_rejects_conflicting_idempotency_retry(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        store.create_checkpoint(_checkpoint())
        store.append_event(_event("ready", "e-2"))
        with pytest.raises(ValueError, match="event_id.*payload khác nhau"):
            store.append_event(_event("suppressed", "e-2", reason_code="duplicate"))


def test_checkpoint_1_0_upcasts_to_1_1_without_inventing_source_refs():
    from gsm_core.schema_registry import SchemaRegistry
    from gsm_core.upcasters import upcast

    reg = SchemaRegistry(ROOT / "schemas")
    old = _checkpoint()
    assert reg.validate("advice_checkpoint", old) == []
    new = upcast("advice_checkpoint", old)
    assert new["schema_version"] == "1.1.0"
    assert new["source_decision_id"] is None
    assert new["run_id"] is None
    assert new["solver_input_refs"] == []
    assert new["solver_report_refs"] == []
    assert reg.validate("advice_checkpoint", new) == []
    assert old["schema_version"] == "1.0.0", "upcaster phải pure"


def test_normalizer_builds_deterministic_s2_checkpoint_with_trace_refs():
    from gsm_core.lifecycle.checkpoint import normalize_solver_decision

    snapshot = {
        "driver_id": "d-1", "run_id": "run-7", "surface": "nudge",
        "observed_at": "2026-08-03T09:00:00+07:00",
        "shift_end": "2026-08-03T18:00:00+07:00",
        "freshness_deadline": "2026-08-03T10:00:00+07:00",
        "data_mode": "synthetic", "is_mock": True,
    }
    solver_input = {"bucket_end": "2026-08-03T10:00:00+07:00"}
    report = {"status": "optimal", "confidence": 0.8, "solution": {
        "schedule": [
            {"bucket": "09:00", "action": "ONLINE"},
            {"bucket": "10:00", "action": "SWAP"},
        ],
        "next_action": {"bucket": "10:00", "action": "SWAP"},
    }}

    first = normalize_solver_decision("S2", snapshot, solver_input, report, "s2-dec-1")
    second = normalize_solver_decision("S2", snapshot, solver_input, report, "s2-dec-1")

    assert first == second
    assert first["checkpoint_id"].startswith("ckpt-")
    assert first["current_action"]["code"] == "ONLINE"
    assert first["future_plan"][0]["code"] == "SWAP"
    assert first["source_decision_id"] == "s2-dec-1"
    assert first["run_id"] == "run-7"
    assert first["solver_input_refs"] and first["solver_report_refs"]


def test_policy_fails_closed_and_supersedes_only_material_same_topic():
    from gsm_core.lifecycle.checkpoint import evaluate_checkpoint

    candidate = {
        "checkpoint_id": "ckpt-new", "fingerprint": "fp-new", "topic": "energy",
        "current_action": {"code": "SWAP"},
        "validity": {"valid_until": "2026-08-03T10:00:00+07:00"},
        "confidence": 0.8, "solver_status": "optimal", "maintenance": False,
    }
    old = {"checkpoint_id": "ckpt-old", "fingerprint": "fp-old", "topic": "energy",
           "state": "ready"}
    result = evaluate_checkpoint(candidate, [old], {}, "2026-08-03T09:00:00+07:00", False)
    assert result.verdict == "ready"
    assert result.superseded_checkpoint_ids == ("ckpt-old",)

    missing = evaluate_checkpoint(
        {**candidate, "validity": {"valid_until": None}}, [], {},
        "2026-08-03T09:00:00+07:00", False)
    assert (missing.verdict, missing.reason) == ("suppressed", "missing_validity")

    driving = evaluate_checkpoint(candidate, [], {}, "2026-08-03T09:00:00+07:00", True)
    assert (driving.verdict, driving.reason) == ("queued", "unsafe_while_moving")


def test_checkpoint_bundle_rolls_back_artifacts_when_checkpoint_insert_fails(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore, build_artifact_record

    artifact = build_artifact_record("state_snapshot", {"driver_id": "d-1"})
    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        store.db.execute("""
            CREATE TRIGGER fail_bundle BEFORE INSERT ON advice_checkpoints
            BEGIN SELECT RAISE(ABORT, 'boom'); END
        """)
        with pytest.raises(sqlite3.IntegrityError, match="boom"):
            store.create_checkpoint_bundle([artifact], _checkpoint())
        assert store.db.execute("SELECT COUNT(*) FROM advice_artifacts").fetchone()[0] == 0
        assert store.db.execute("SELECT COUNT(*) FROM advice_checkpoint_events").fetchone()[0] == 0


def test_in_memory_journal_matches_sqlite_projection(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore, InMemoryCheckpointJournal

    journal = InMemoryCheckpointJournal()
    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        for target in (journal, store):
            assert target.create_checkpoint(_checkpoint())
            assert target.append_event(_event("ready", "e-ready"))
        assert journal.state("ckpt-1") == store.state("ckpt-1")


def test_atomic_lease_is_reused_and_offered_exactly_once(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    path = tmp_path / "checkpoint.db"
    with CheckpointStore(path) as store:
        store.create_checkpoint(_checkpoint())
        store.append_event(_event("ready", "e-ready"))
        first = store.acquire_presentation_lease(
            "ckpt-1", "2026-08-03T09:00:02+07:00",
            display_id_factory=lambda: "display-first")
        second = store.acquire_presentation_lease(
            "ckpt-1", "2026-08-03T09:00:03+07:00",
            display_id_factory=lambda: "display-must-not-be-used")

        assert first == second
        assert first["display_id"] == "display-first"
        assert [e["event_type"] for e in store.events("ckpt-1")].count("offered") == 1


def test_lease_pins_immutable_presentation_content(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        store.create_checkpoint(_checkpoint())
        store.append_event(_event("ready", "e-ready"))
        pinned = {
            "presentation_artifact_id": "presentation:1",
            "content_digest": "sha256:content-1",
            "presentation_source": "template",
            "template_version": "checkpoint-v2",
            "model_version": None,
            "prompt_version": None,
            "schema_version": "1.0.0",
            "verifier_version": "1.0.0",
            "policy_version": "policy-v1",
        }
        first = store.acquire_presentation_lease(
            "ckpt-1", "2026-08-03T09:00:02+07:00", presentation=pinned,
            display_id_factory=lambda: "display-first")
        second = store.acquire_presentation_lease(
            "ckpt-1", "2026-08-03T09:00:03+07:00", presentation={**pinned, "content_digest": "sha256:other"},
            display_id_factory=lambda: "display-must-not-be-used")

        assert first == second
        assert first["content_digest"] == "sha256:content-1"


def test_concurrent_lease_acquisition_has_one_owner(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    path = tmp_path / "checkpoint.db"
    with CheckpointStore(path) as store:
        store.create_checkpoint(_checkpoint())
        store.append_event(_event("ready", "e-ready"))

    def acquire(display_id):
        with CheckpointStore(path) as store:
            return store.acquire_presentation_lease(
                "ckpt-1", "2026-08-03T09:00:02+07:00",
                display_id_factory=lambda: display_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(acquire, ["display-a", "display-b"]))

    assert leases[0]["display_id"] == leases[1]["display_id"]
    with CheckpointStore(path) as store:
        assert [e["event_type"] for e in store.events("ckpt-1")].count("offered") == 1


def test_lease_and_offered_event_roll_back_together(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    path = tmp_path / "checkpoint.db"
    with CheckpointStore(path) as store:
        store.create_checkpoint(_checkpoint())
        store.append_event(_event("ready", "e-ready"))
        store.db.execute("""
            CREATE TRIGGER fail_offer BEFORE INSERT ON advice_checkpoint_events
            WHEN json_extract(NEW.record, '$.event_type') = 'offered'
            BEGIN SELECT RAISE(ABORT, 'offer boom'); END
        """)
        with pytest.raises(sqlite3.IntegrityError, match="offer boom"):
            store.acquire_presentation_lease(
                "ckpt-1", "2026-08-03T09:00:02+07:00",
                display_id_factory=lambda: "display-first")
        assert store.db.execute(
            "SELECT COUNT(*) FROM advice_presentation_leases").fetchone()[0] == 0


def test_generation_cache_claim_has_one_owner_and_bounded_ttl(tmp_path):
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        assert store.claim_generation(
            "cache-1", "owner-a", "2026-08-03T09:00:00+07:00",
            "2026-08-03T09:20:00+07:00") is True
        assert store.claim_generation(
            "cache-1", "owner-b", "2026-08-03T09:00:01+07:00",
            "2026-08-03T09:20:00+07:00") is False
        with pytest.raises(ValueError, match="owner"):
            store.put_generation_cache(
                "cache-1", "owner-b", {"status": "verified"},
                "2026-08-03T09:20:00+07:00")
        store.put_generation_cache(
            "cache-1", "owner-a", {"status": "verified"},
            "2026-08-03T09:20:00+07:00")
        assert store.generation_cache_get(
            "cache-1", "2026-08-03T09:10:00+07:00") == {"status": "verified"}
        assert store.generation_cache_get(
            "cache-1", "2026-08-03T09:20:00+07:00") is None
