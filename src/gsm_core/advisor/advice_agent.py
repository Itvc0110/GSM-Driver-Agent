"""Strict, tool-free provider adapter for AdviceCheckpoint language enrichment."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import threading
from typing import Any, Callable, Protocol


class ProviderError(RuntimeError):
    """Redacted provider boundary error."""


class ProviderTimeout(ProviderError):
    pass


class ProviderUnavailable(ProviderError):
    pass


@dataclass(frozen=True)
class AgentRequest:
    request_type: str
    input: dict
    prompt_version: str
    schema_version: str
    policy_version: str
    model_version: str


@dataclass(frozen=True)
class ProviderResult:
    output: Any
    model_version: str
    usage: dict
    latency_ms: float | None = None


class AdviceAgentProvider(Protocol):
    model_version: str

    def generate(self, request: AgentRequest) -> ProviderResult: ...


def build_agent_request(input_payload: dict, *, request_type: str = "proactive",
                        prompt_version: str = "advice-checkpoint-v1",
                        policy_version: str = "unknown",
                        model_version: str = "unknown") -> AgentRequest:
    """Wrap an already schema-validated allowlist payload.

    The adapter intentionally does not accept solver reports, stores or driver
    objects; callers must construct the structured input before this boundary.
    """
    if not isinstance(input_payload, dict):
        raise TypeError("agent input phải là object")
    return AgentRequest(
        request_type=request_type, input=dict(input_payload),
        prompt_version=prompt_version,
        schema_version=str(input_payload.get("schema_version", "1.0.0")),
        policy_version=policy_version, model_version=model_version)


class OpenAIAdviceProvider:
    """OpenAI-compatible JSON adapter with no tool access.

    It is lazy: importing/constructing the SDK happens only on the first
    generation call.  Credentials are never included in results or errors.
    """

    def __init__(self, *, api_key: str, base_url: str | None, model: str,
                 timeout_s: float = 8.0,
                 max_output_tokens: int = 256,
                 max_calls: int | None = 20,
                 kill_switch: bool = False,
                 client_factory: Callable[..., Any] | None = None):
        if not api_key:
            raise ProviderUnavailable("provider credentials unavailable")
        if not model:
            raise ProviderUnavailable("provider model unavailable")
        self._api_key = api_key
        self.base_url = base_url
        self.model_version = model
        self.timeout_s = float(timeout_s)
        self.max_output_tokens = max(1, int(max_output_tokens))
        self.max_calls = None if max_calls is None else max(0, int(max_calls))
        self.kill_switch = bool(kill_switch)
        self._calls = 0
        self._budget_lock = threading.Lock()
        self._client_factory = client_factory
        self._client: Any | None = None

    @classmethod
    def from_env(cls, *, timeout_s: float = 8.0) -> "OpenAIAdviceProvider":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ProviderUnavailable("provider credentials unavailable")
        configured_timeout = os.getenv("ADVICE_AGENT_TIMEOUT_S")
        try:
            timeout = float(configured_timeout) if configured_timeout else timeout_s
        except ValueError:
            raise ProviderUnavailable("provider timeout configuration invalid") from None
        configured_max_calls = os.getenv("ADVICE_AGENT_MAX_CALLS", "20")
        try:
            max_calls = int(configured_max_calls)
        except ValueError:
            raise ProviderUnavailable("provider budget configuration invalid") from None
        configured_max_tokens = os.getenv("ADVICE_AGENT_MAX_OUTPUT_TOKENS", "256")
        try:
            max_tokens = int(configured_max_tokens)
        except ValueError:
            raise ProviderUnavailable("provider token budget configuration invalid") from None
        return cls(api_key=key, base_url=os.getenv("OPENAI_BASE_URL"),
                   model=os.getenv("DEFAULT_MODEL", ""), timeout_s=timeout,
                   max_output_tokens=max_tokens, max_calls=max_calls,
                   kill_switch=os.getenv("ADVICE_AGENT_KILL_SWITCH", "0") == "1")

    def __repr__(self) -> str:  # never expose credential in diagnostics
        # A base URL can itself contain userinfo/query credentials in a misconfigured
        # environment; omit it rather than relying on callers to redact repr output.
        return (f"OpenAIAdviceProvider(model={self.model_version!r}, "
                f"timeout_s={self.timeout_s!r}, max_calls={self.max_calls!r})")

    def _client_instance(self) -> Any:
        if self._client is not None:
            return self._client
        factory = self._client_factory
        if factory is None:
            try:
                from openai import OpenAI
            except Exception as exc:  # SDK is optional until internal-live is enabled
                raise ProviderUnavailable("provider sdk unavailable") from exc
            factory = OpenAI
        try:
            kwargs = {"api_key": self._api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = factory(**kwargs)
        except Exception as exc:
            raise ProviderUnavailable("provider client unavailable") from exc
        return self._client

    @staticmethod
    def _usage(response: Any) -> dict:
        usage = getattr(response, "usage", None)
        if usage is None:
            return {"input_tokens": None, "output_tokens": None, "cost_usd": None}
        def read(name: str):
            if isinstance(usage, dict):
                return usage.get(name)
            return getattr(usage, name, None)
        return {
            "input_tokens": read("prompt_tokens") or read("input_tokens"),
            "output_tokens": read("completion_tokens") or read("output_tokens"),
            "cost_usd": None,
        }

    def generate(self, request: AgentRequest) -> ProviderResult:
        import time

        with self._budget_lock:
            if self.kill_switch:
                raise ProviderUnavailable("provider kill switch enabled")
            if self.max_calls is not None and self._calls >= self.max_calls:
                raise ProviderUnavailable("provider call budget exhausted")
            self._calls += 1
        client = self._client_instance()
        body = json.dumps(request.input, ensure_ascii=False, sort_keys=True)
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": (
                        "Chỉ trả JSON theo schema agent_presentation_output. "
                        "Không thay đổi hành động, khung giờ, số liệu hoặc provenance.")},
                    {"role": "user", "content": body},
                ],
                response_format={"type": "json_object"},
                max_tokens=self.max_output_tokens,
                timeout=self.timeout_s,
            )
        except Exception as exc:
            name = type(exc).__name__.lower()
            if isinstance(exc, TimeoutError) or "timeout" in name:
                raise ProviderTimeout("provider timeout") from None
            raise ProviderError("provider request failed") from None
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            content = response.choices[0].message.content
        except Exception:
            raise ProviderError("provider response malformed") from None
        try:
            output = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            output = content
        return ProviderResult(output=output, model_version=self.model_version,
                              usage=self._usage(response), latency_ms=latency_ms)
