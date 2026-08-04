from __future__ import annotations


def checkpoint(action="SWAP", **extra):
    value = {
        "checkpoint_id": "ckpt-strategy-1",
        "current_action": {"code": action, "label_id": f"action.{action.lower()}"},
        "future_plan": [], "surface": "nudge", "topic": "energy",
        "reason_code": "soc_low",
    }
    value.update(extra)
    return value


def test_simple_and_repeated_advice_are_template_only():
    from gsm_core.advisor.presentation_strategy import decide_presentation

    simple = decide_presentation(
        checkpoint("SWAP"), facts=[{"id": "F1", "value": "pin thấp"}],
        numbers=[], caveats=[], mode="internal_live", provider_enabled=True)
    repeated = decide_presentation(
        checkpoint("REST", reason_code="repeated_advice"), facts=[], numbers=[],
        caveats=[], mode="internal_live", provider_enabled=True)

    assert (simple.strategy, simple.reason_code) == ("TEMPLATE", "simple_known_template")
    assert (repeated.strategy, repeated.reason_code) == ("TEMPLATE", "repeated_advice")


def test_complex_context_uses_llm_only_in_internal_live_or_shadow():
    from gsm_core.advisor.presentation_strategy import decide_presentation

    value = decide_presentation(
        checkpoint("ONLINE", presentation_complexity="complex"),
        facts=[{"id": f"F{i}", "value": str(i)} for i in range(4)],
        numbers=[], caveats=[{"id": "C1", "value": "uncertainty"}],
        mode="internal_live", provider_enabled=True)
    shadow = decide_presentation(
        checkpoint("ONLINE", presentation_complexity="complex"), facts=[], numbers=[],
        caveats=[{"id": "C1", "value": "uncertainty"}],
        mode="shadow", provider_enabled=True)

    assert (value.strategy, value.reason_code) == ("LLM", "complex_multi_fact")
    assert shadow.strategy == "LLM"


def test_disabled_provider_moving_and_missing_checkpoint_fail_closed():
    from gsm_core.advisor.presentation_strategy import decide_presentation

    disabled = decide_presentation(
        checkpoint("ONLINE", presentation_complexity="complex"), facts=[], numbers=[],
        caveats=[{"id": "C1", "value": "uncertainty"}], mode="internal_live",
        provider_enabled=False)
    moving = decide_presentation(
        checkpoint("SWAP"), facts=[], numbers=[], caveats=[], mode="internal_live",
        provider_enabled=True, is_driving=True)
    silent = decide_presentation(
        None, facts=[], numbers=[], caveats=[], mode="internal_live", provider_enabled=True)

    assert (disabled.strategy, disabled.reason_code) == ("TEMPLATE", "provider_unavailable")
    assert (moving.strategy, moving.reason_code) == ("SILENT", "unsafe_while_moving")
    assert (silent.strategy, silent.reason_code) == ("SILENT", "no_checkpoint")


def test_non_presentable_checkpoint_states_are_silent():
    from gsm_core.advisor.presentation_strategy import decide_presentation

    for state in ("suppressed", "queued", "expired", "superseded"):
        result = decide_presentation(
            checkpoint("SWAP", state=state), facts=[], numbers=[], caveats=[],
            mode="internal_live", provider_enabled=True)
        assert result.strategy == "SILENT"
        assert result.reason_code == "checkpoint_not_presentable"


def test_why_request_is_llm_reason_code_without_changing_canonical_context():
    from gsm_core.advisor.presentation_strategy import decide_presentation

    result = decide_presentation(
        checkpoint("SWAP"), facts=[], numbers=[], caveats=[], mode="internal_live",
        provider_enabled=True, user_requested_why=True)
    assert (result.strategy, result.reason_code) == ("LLM", "user_requested_why")
