from __future__ import annotations


def test_safe_defaults_are_template_and_why_disabled(monkeypatch, tmp_path):
    from app.services.advice_checkpoint import AdviceCheckpointService, ProductSolverResult
    from gsm_core.lifecycle.checkpoint_store import CheckpointStore

    for key in ("ADVICE_PRESENTATION_MODE", "ADVICE_WHY_AGENT_ENABLED",
                "ADVICE_AGENT_ALLOWLIST"):
        monkeypatch.delenv(key, raising=False)
    with CheckpointStore(tmp_path / "defaults.db") as store:
        service = AdviceCheckpointService(
            store, type("O", (), {"solve": lambda self, *a, **k: ProductSolverResult()})())
        assert service.presentation_mode == "template"
        assert service.why_agent_enabled is False
        assert service.agent_provider is None
