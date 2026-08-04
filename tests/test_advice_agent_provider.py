from __future__ import annotations


def request():
    from gsm_core.advisor.advice_agent import AgentRequest

    return AgentRequest(
        request_type="proactive",
        input={
            "schema_version": "1.0.0", "checkpoint_id": "ckpt-agent-1",
            "surface": "nudge", "locale": "vi-VN", "topic": "energy",
            "canonical_action": {"code": "SWAP", "label_id": "action.swap"},
            "current_action": {"code": "SWAP", "label_id": "action.swap"},
            "future_plan": [], "action_window": None, "facts": [], "numbers": [],
            "confidence_band": "high", "caveats": [], "summary_max_chars": 120,
            "why_max_chars": 280,
        },
        prompt_version="advice-checkpoint-v1", schema_version="1.0.0",
        policy_version="policy-v1", model_version="model-v1",
    )


def test_provider_uses_structured_json_without_tools_and_redacts_credentials():
    from gsm_core.advisor.advice_agent import OpenAIAdviceProvider

    class Message:
        content = '{"schema_version":"1.0.0","checkpoint_id":"ckpt-agent-1","reason_template":"Ổn.","why_template":"Vì sao.","used_fact_ids":[],"used_number_ids":[],"used_caveat_ids":[]}'

    class Choice:
        message = Message()

    class Completions:
        def __init__(self):
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("Response", (), {
                "choices": [Choice()],
                "usage": type("Usage", (), {"prompt_tokens": 12,
                                              "completion_tokens": 8})(),
            })()

    completions = Completions()

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": completions})()

    provider = OpenAIAdviceProvider(
        api_key="super-secret", base_url="https://provider.invalid/v1",
        model="demo-model", timeout_s=2.0, client_factory=lambda **kwargs: Client())
    result = provider.generate(request())

    assert result.output["checkpoint_id"] == "ckpt-agent-1"
    assert completions.kwargs["response_format"] == {"type": "json_object"}
    assert "tools" not in completions.kwargs
    assert result.usage["input_tokens"] == 12
    assert "super-secret" not in repr(result)


def test_provider_timeout_is_typed_and_does_not_expose_secret():
    from gsm_core.advisor.advice_agent import OpenAIAdviceProvider, ProviderTimeout

    class Completions:
        def create(self, **kwargs):
            raise TimeoutError("request timed out")

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {
                "completions": Completions(),
            })()

    provider = OpenAIAdviceProvider(
        api_key="super-secret", base_url="https://provider.invalid/v1",
        model="demo-model", client_factory=lambda **kwargs: Client())
    try:
        provider.generate(request())
    except ProviderTimeout as exc:
        assert "super-secret" not in str(exc)
    else:
        raise AssertionError("expected typed provider timeout")


def test_provider_requires_model_name():
    import pytest
    from gsm_core.advisor.advice_agent import OpenAIAdviceProvider, ProviderUnavailable

    with pytest.raises(ProviderUnavailable, match="model unavailable"):
        OpenAIAdviceProvider(api_key="redacted", base_url=None, model="")


def test_provider_kill_switch_and_call_budget_fail_closed():
    import pytest
    from gsm_core.advisor.advice_agent import OpenAIAdviceProvider, ProviderUnavailable

    class Completions:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": "{}"})(),
                })()], "usage": None,
            })()

    completions = Completions()
    client = lambda **kwargs: type(
        "Client", (), {"chat": type("Chat", (), {"completions": completions})()})()
    provider = OpenAIAdviceProvider(
        api_key="redacted", base_url=None, model="demo-model", max_calls=1,
        client_factory=client)
    provider.generate(request())
    with pytest.raises(ProviderUnavailable, match="budget exhausted"):
        provider.generate(request())
    assert completions.calls == 1

    stopped = OpenAIAdviceProvider(
        api_key="redacted", base_url=None, model="demo-model", kill_switch=True,
        client_factory=client)
    with pytest.raises(ProviderUnavailable, match="kill switch"):
        stopped.generate(request())
