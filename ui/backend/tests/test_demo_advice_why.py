from __future__ import annotations

import pytest

from test_advice_generation_flow import _get, _solver_result


class WhyProvider:
    model_version = "why-model-v1"

    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def generate(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        from gsm_core.advisor.advice_agent import ProviderResult
        return ProviderResult({
            "schema_version": "1.0.0",
            "checkpoint_id": request.input["checkpoint_id"],
            "display_id": request.input["display_id"],
            "explanation_template": "Giải thích từ {{F1}} và {{C1}}.",
            "used_fact_ids": ["F1"], "used_number_ids": [],
            "used_caveat_ids": ["C1"],
        }, self.model_version, {"input_tokens": 9, "output_tokens": 7, "cost_usd": None})


def _service(tmp_path, provider):
    from app.services.advice_checkpoint import AdviceCheckpointService
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    orchestrator = type("O", (), {"solve": lambda self, *a, **k:
                                   _solver_result(caveats=["forecast only"])})()
    store = CheckpointStore(tmp_path / "why.db")
    service = AdviceCheckpointService(
        store, orchestrator, presentation_mode="template", agent_provider=provider,
        why_agent_enabled=True)
    return store, service


def test_why_is_lazy_and_retry_is_idempotent(tmp_path):
    provider = WhyProvider()
    store, service = _service(tmp_path, provider)
    try:
        card = _get(service)["items"][0]
        assert provider.calls == 0
        first = service.explain_why(
            card["checkpoint_id"], display_id=card["display_id"],
            client_request_id="why-1", generated_at="2026-08-03T09:00:00+07:00")
        retry = service.explain_why(
            card["checkpoint_id"], display_id=card["display_id"],
            client_request_id="why-1", generated_at="2026-08-03T09:00:00+07:00")
        assert provider.calls == 1
        assert first == retry
        assert first["status"] == "ready"
        assert first["is_historical"] is False
        assert store.state(card["checkpoint_id"])["expanded_event_ids"]
    finally:
        store.close()


def test_why_rejects_wrong_display_and_does_not_create_checkpoint(tmp_path):
    from app.services.advice_checkpoint import CheckpointConflictError

    provider = WhyProvider()
    store, service = _service(tmp_path, provider)
    try:
        card = _get(service)["items"][0]
        with pytest.raises(CheckpointConflictError, match="lease"):
            service.explain_why(
                card["checkpoint_id"], display_id="wrong", client_request_id="why-2",
                generated_at="2026-08-03T09:00:00+07:00")
        assert provider.calls == 0
        assert len(store.checkpoints()) == 1
    finally:
        store.close()


def test_why_provider_failure_falls_back_and_moving_is_silent(tmp_path):
    provider = WhyProvider(error=TimeoutError("slow"))
    store, service = _service(tmp_path, provider)
    try:
        card = _get(service)["items"][0]
        fallback = service.explain_why(
            card["checkpoint_id"], display_id=card["display_id"],
            client_request_id="why-3", generated_at="2026-08-03T09:00:00+07:00")
        assert fallback["status"] == "ready"
        assert fallback["presentation_source"] == "template"
        assert provider.calls == 1
        silent = service.explain_why(
            card["checkpoint_id"], display_id=card["display_id"],
            client_request_id="why-4", generated_at="2026-08-03T09:00:00+07:00",
            is_driving=True)
        assert silent["status"] == "silent"
        assert silent["silent"]["reason_code"] == "unsafe_while_moving"
    finally:
        store.close()


def test_expired_card_can_explain_historical_context_without_reoffer(tmp_path):
    provider = WhyProvider()
    store, service = _service(tmp_path, provider)
    try:
        card = _get(service)["items"][0]
        checkpoint = store.checkpoint(card["checkpoint_id"])
        store.append_event({
            "schema_version": "1.1.0", "event_id": "expired:why-history",
            "checkpoint_id": card["checkpoint_id"], "driver_id": "d-1",
            "display_id": card["display_id"], "event_type": "expired",
            "occurred_at": "2026-08-03T09:21:00+07:00", "actor": "system",
            "origin": "product", "reason_code": "expired", "relation_type": None,
            "confidence": None, "payload": {},
        })
        answer = service.explain_why(
            card["checkpoint_id"], display_id=card["display_id"],
            client_request_id="why-history", generated_at="2026-08-03T09:22:00+07:00")
        assert answer["status"] == "ready"
        assert answer["is_historical"] is True
        assert answer["no_reoffer"] is True
        assert len(store.checkpoints()) == 1
    finally:
        store.close()
