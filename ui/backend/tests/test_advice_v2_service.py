"""P3B presentation lease and v2 lifecycle semantics."""

from __future__ import annotations

import pytest

from gsm_core.lifecycle.checkpoint_store import CheckpointStore


class FakeOrchestrator:
    def __init__(self, result):
        self.result = result

    def solve(self, *args, **kwargs):
        return self.result


def _solver_result():
    from app.services.advice_checkpoint import (
        ProductSolverResult,
        _normalize_with_artifacts,
    )

    snapshot = {
        "driver_id": "d-1", "surface": "nudge", "trigger_type": "poll",
        "observed_at": "2026-08-03T09:00:00+07:00",
        "freshness_deadline": "2026-08-03T09:20:00+07:00",
        "shift_end": "2026-08-03T18:00:00+07:00",
        "data_mode": "mock-realdata", "is_mock": True, "run_id": None,
    }
    solver_input = {"driver_id": "d-1", "policy_effective_boundary": None}
    report = {
        "confidence": 0.8,
        "numbers": [{"value": 15, "unit": "points", "source": "policy_v:test"}],
        "caveats": ["forecast only"],
        "solution": {"already_maxed": False, "feasible": True, "gap_points": 15},
    }
    candidate, artifacts = _normalize_with_artifacts(
        "S1", snapshot, solver_input, report, "s1-d-1-2026-08-03-540")
    return ProductSolverResult(
        candidates=[candidate], artifacts=artifacts, solver_set=["S1"])


def _get(service, *, driving=False):
    return service.get_advice(
        surface="nudge", driver_id="d-1", date="2026-08-03", now_min=540,
        shift_start_min=360, shift_end_min=1080, is_driving=driving)


def test_get_retry_reuses_lease_and_does_not_imply_display(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        service = AdviceCheckpointService(store, FakeOrchestrator(_solver_result()))
        first = _get(service)
        second = _get(service)

        assert len(first["items"]) == 1
        assert first["items"][0]["display_id"] == second["items"][0]["display_id"]
        checkpoint_id = first["items"][0]["checkpoint_id"]
        event_types = [event["event_type"] for event in store.events(checkpoint_id)]
        assert event_types.count("offered") == 1
        assert "displayed" not in event_types
        assert first["items"][0]["solver_set"] == ["S1"]
        assert first["items"][0]["numbers"][0]["artifact_ref"]


def test_lease_replays_pinned_presentation_artifact_without_rerender(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        service = AdviceCheckpointService(store, FakeOrchestrator(_solver_result()))
        first = _get(service)
        card = first["items"][0]
        lease = store.lease(card["checkpoint_id"])

        assert lease["presentation_artifact_id"].startswith("presentation:")
        artifact = store.artifact(lease["presentation_artifact_id"])
        assert artifact is not None
        assert artifact["digest"] == lease["content_digest"]
        assert artifact["payload"]["summary"] == card["summary"]

        def rerender_must_not_run(*args, **kwargs):
            raise AssertionError("lease retry must not rerender presentation")

        service._prepare_presentation = rerender_must_not_run
        second = _get(service)
        assert second["items"][0] == card


def test_mounted_ack_and_response_are_idempotent_and_lease_bound(tmp_path):
    from app.services.advice_checkpoint import (
        AdviceCheckpointService,
        CheckpointConflictError,
    )

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        service = AdviceCheckpointService(store, FakeOrchestrator(_solver_result()))
        card = _get(service)["items"][0]
        ack = dict(
            checkpoint_id=card["checkpoint_id"], display_id=card["display_id"],
            client_event_id="client-display-1",
            mounted_at="2026-08-03T09:00:01+07:00")
        assert service.acknowledge_display(**ack)["idempotent_replay"] is False
        assert service.acknowledge_display(**ack)["idempotent_replay"] is True
        with pytest.raises(CheckpointConflictError, match="stale"):
            service.acknowledge_display(**{**ack, "display_id": "wrong-display"})

        accepted = service.record_response(
            card["checkpoint_id"], display_id=card["display_id"],
            client_event_id="client-response-1", response="accepted",
            occurred_at="2026-08-03T09:00:02+07:00")
        assert accepted["event_type"] == "accepted"
        state = store.state(card["checkpoint_id"])
        assert state["state"] == "accepted"
        assert state["execution_links"] == []
        assert [e["event_type"] for e in store.events(card["checkpoint_id"])].count(
            "displayed") == 1


def test_driving_and_missing_state_are_silent_without_presentation_ids(tmp_path):
    from app.services.advice_checkpoint import (
        AdviceCheckpointService,
        ProductSolverResult,
    )

    with CheckpointStore(tmp_path / "driving.db") as store:
        driving = _get(AdviceCheckpointService(store, FakeOrchestrator(_solver_result())),
                       driving=True)
        encoded = str(driving)
        assert driving["status"] == "silent"
        assert driving["silent"]["reason_code"] == "unsafe_while_moving"
        assert "checkpoint_id" not in encoded and "display_id" not in encoded

    missing_result = ProductSolverResult(reasons={"S2": "missing_state"})
    with CheckpointStore(tmp_path / "missing.db") as store:
        missing = _get(AdviceCheckpointService(store, FakeOrchestrator(missing_result)))
        encoded = str(missing)
        assert missing["silent"]["reason_code"] == "missing_state"
        assert "checkpoint_id" not in encoded and "display_id" not in encoded


def test_shadow_output_is_artifact_only_and_never_changes_driver_card(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    class ShadowAgent:
        model_version = "shadow-test-v1"
        last_usage = {"input_tokens": 11, "output_tokens": 7, "cost_usd": 0.001}

        def __init__(self):
            self.calls = 0

        def generate(self, payload):
            self.calls += 1
            return {
                "schema_version": "1.0.0", "checkpoint_id": payload["checkpoint_id"],
                "reason_template": "SHADOW_MARKER {{F1}}",
                "why_template": "SHADOW_MARKER {{F1}}",
                "used_fact_ids": ["F1"], "used_number_ids": [],
                "used_caveat_ids": [],
            }

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        agent = ShadowAgent()
        service = AdviceCheckpointService(
            store, FakeOrchestrator(_solver_result()),
            presenter=CheckpointPresenter(agent=agent, mode="shadow"))
        body = _get(service)

        assert "SHADOW_MARKER" not in str(body)
        artifacts = store.artifacts("agent_shadow_output")
        assert len(artifacts) == 1
        assert artifacts[0]["payload"]["status"] == "verified"
        assert "SHADOW_MARKER" in str(artifacts[0]["payload"]["shadow_output"])

        checkpoint = store.checkpoint(body["items"][0]["checkpoint_id"])
        service._prepare_presentation(
            checkpoint, "2026-08-03T09:00:02+07:00", allow_shadow=True)
        metrics = store.presentation_metrics()
        assert agent.calls == 1
        assert metrics[0]["cache_hit"] is False
        assert metrics[0]["input_tokens"] == 11
        assert metrics[0]["output_tokens"] == 7
        assert metrics[0]["cost_usd"] == 0.001
        assert metrics[0]["latency_ms"] >= 0
        assert metrics[1]["cache_hit"] is True
        assert metrics[1]["avoided_calls"] == 1


def test_shadow_result_is_discarded_if_checkpoint_supersedes_during_generation(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    with CheckpointStore(tmp_path / "checkpoint.db") as store:
        class SupersedingAgent:
            def generate(self, payload):
                store.append_event({
                    "schema_version": "1.1.0", "event_id": "shadow-supersede",
                    "checkpoint_id": payload["checkpoint_id"], "driver_id": "d-1",
                    "display_id": None, "event_type": "superseded",
                    "occurred_at": "2026-08-03T09:00:00+07:00",
                    "actor": "system", "origin": "product",
                    "reason_code": "material_change", "relation_type": None,
                    "confidence": None, "payload": {},
                })
                return {
                    "schema_version": "1.0.0", "checkpoint_id": payload["checkpoint_id"],
                    "reason_template": "{{F1}}", "why_template": "{{F1}}",
                    "used_fact_ids": ["F1"], "used_number_ids": [],
                    "used_caveat_ids": [],
                }

        service = AdviceCheckpointService(
            store, FakeOrchestrator(_solver_result()),
            presenter=CheckpointPresenter(agent=SupersedingAgent(), mode="shadow"))
        body = _get(service)

        assert body["status"] == "silent"
        assert body["silent"]["reason_code"] == "discarded_stale"
        assert store.db.execute(
            "SELECT COUNT(*) FROM advice_presentation_leases").fetchone()[0] == 0
        artifact = store.artifacts("agent_shadow_output")[0]
        assert artifact["payload"]["status"] == "discarded_stale"
        assert store.generation_cache_get(
            "not-a-real-key", "2026-08-03T09:00:00+07:00") is None
