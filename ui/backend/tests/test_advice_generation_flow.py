from __future__ import annotations


def _solver_result(*, caveats):
    from app.services.advice_checkpoint import ProductSolverResult, _normalize_with_artifacts

    snapshot = {
        "driver_id": "d-1", "surface": "nudge", "trigger_type": "poll",
        "observed_at": "2026-08-03T09:00:00+07:00",
        "freshness_deadline": "2026-08-03T09:20:00+07:00",
        "shift_end": "2026-08-03T18:00:00+07:00",
        "data_mode": "mock-realdata", "is_mock": True, "run_id": "run-agent-1",
    }
    solver_input = {"driver_id": "d-1", "policy_effective_boundary": None}
    report = {
        "confidence": 0.8,
        "numbers": [{"value": 15, "unit": "points", "source": "policy:test"}],
        "caveats": caveats,
        "solution": {"already_maxed": False, "feasible": True, "gap_points": 15},
    }
    candidate, artifacts = _normalize_with_artifacts(
        "S1", snapshot, solver_input, report, "s1-agent-1")
    return ProductSolverResult(candidates=[candidate], artifacts=artifacts, solver_set=["S1"])


def _get(service):
    return service.get_advice(
        surface="nudge", driver_id="d-1", date="2026-08-03", now_min=540,
        shift_start_min=360, shift_end_min=1080, is_driving=False)


class FakeProvider:
    model_version = "fake-model-v1"

    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        from gsm_core.advisor.advice_agent import ProviderResult
        return ProviderResult(self.output, self.model_version,
                              {"input_tokens": 10, "output_tokens": 8, "cost_usd": None})


def _agent_output():
    return {
        "schema_version": "1.0.0", "checkpoint_id": "PLACEHOLDER",
        "reason_template": "Theo {{F1}}.",
        "why_template": "Lưu ý {{C1}}.",
        "used_fact_ids": ["F1"], "used_number_ids": [],
        "used_caveat_ids": ["C1"],
    }


def test_template_mode_does_not_call_provider_for_simple_repeated_advice(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    provider = FakeProvider(output=_agent_output())
    with CheckpointStore(tmp_path / "template.db") as store:
        service = AdviceCheckpointService(
            store, type("O", (), {"solve": lambda self, *a, **k:
                                   _solver_result(caveats=[])})(),
            presentation_mode="template", agent_provider=provider)
        body = _get(service)
        assert provider.calls == 0
        assert body["presentation_source"] == "template"


def test_shadow_mode_also_skips_simple_repeated_provider_call(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    provider = FakeProvider(output=_agent_output())
    with CheckpointStore(tmp_path / "shadow-simple.db") as store:
        service = AdviceCheckpointService(
            store, type("O", (), {"solve": lambda self, *a, **k:
                                   _solver_result(caveats=[])})(),
            presentation_mode="shadow", agent_provider=provider)
        body = _get(service)
        assert provider.calls == 0
        assert body["presentation_source"] == "template"


def test_internal_live_uses_verified_reason_why_and_pins_source(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    provider = FakeProvider(output=_agent_output())
    with CheckpointStore(tmp_path / "live.db") as store:
        orchestrator = type("O", (), {"solve": lambda self, *a, **k:
                                       _solver_result(caveats=["forecast only"])})()
        service = AdviceCheckpointService(
            store, orchestrator, presentation_mode="internal_live", agent_provider=provider)
        checkpoint_id = None
        # The fake output must use the canonical id produced by the normalized candidate.
        candidate = _solver_result(caveats=["forecast only"]).candidates[0]
        provider.output = {**_agent_output(), "checkpoint_id": candidate["checkpoint_id"]}
        body = _get(service)
        checkpoint_id = body["items"][0]["checkpoint_id"]
        assert provider.calls == 1
        assert body["presentation_source"] == "agent"
        assert "Theo" in body["items"][0]["summary"]
        lease = store.lease(checkpoint_id)
        assert lease["presentation_source"] == "agent"
        assert store.state(checkpoint_id)["state"] == "offered"


def test_provider_failure_keeps_template_and_next_step_healthy(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    provider = FakeProvider(error=TimeoutError("slow"))
    with CheckpointStore(tmp_path / "fallback.db") as store:
        orchestrator = type("O", (), {"solve": lambda self, *a, **k:
                                       _solver_result(caveats=["forecast only"])})()
        service = AdviceCheckpointService(
            store, orchestrator, presentation_mode="internal_live", agent_provider=provider)
        body = _get(service)
        assert provider.calls == 1
        assert body["presentation_source"] == "template"
        assert body["status"] == "ready"
        checkpoint_id = body["items"][0]["checkpoint_id"]
        assert store.state(checkpoint_id)["state"] == "offered"


def test_shadow_keeps_template_driver_card_and_stores_evaluation(tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    candidate = _solver_result(caveats=["forecast only"]).candidates[0]
    provider = FakeProvider(output={**_agent_output(), "checkpoint_id": candidate["checkpoint_id"]})
    with CheckpointStore(tmp_path / "shadow.db") as store:
        orchestrator = type("O", (), {"solve": lambda self, *a, **k:
                                       _solver_result(caveats=["forecast only"])})()
        service = AdviceCheckpointService(
            store, orchestrator, presentation_mode="shadow", agent_provider=provider)
        body = _get(service)
        assert provider.calls == 1
        assert body["presentation_source"] == "template"
        assert store.artifacts("agent_shadow_output")
