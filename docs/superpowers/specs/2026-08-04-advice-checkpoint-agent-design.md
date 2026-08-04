# AdviceCheckpoint Agent — Template-first + lazy “Vì sao?” Design

**Ngày:** 2026-08-04  
**Trạng thái:** IMPLEMENTED-CODE / WAITING-VERDICT
**Phạm vi:** AdviceCheckpoint presentation cho Web demo và API v2; không mở conversational agent, what-if solver, dispatcher hoặc simulator live engine.

## Mục tiêu

Giữ lời khuyên lặp lại, đơn giản và canonical bằng template deterministic. Chỉ dùng provider LLM khi một checkpoint có nhu cầu diễn giải phức tạp hoặc tài xế chủ động bấm “Vì sao?”. LLM chỉ viết `reason/why`; code vẫn sở hữu action, action window, future plan, số liệu, provenance và lifecycle.

## Code hiện tại đã xác minh trước implementation

1. `DemoSessionService` chạy `run_once()` trước, sau đó cursor replay transition; Next Step không gọi solver.
2. `AdviceCheckpointService._prepare_presentation()` hiện chạy pure `PresentationStrategy` sau primary selection; template fallback được dựng trước mọi provider branch.
3. `LLMComposerClient` hiện phục vụ `AdvisorPipeline` legacy và có output `advice_spec`; không được tái sử dụng cho AdviceCheckpoint.
4. Web demo gọi lazy Why endpoint sau click, không pre-render Agent explanation; `cards.js` legacy renderer cũng dùng safe DOM APIs.
5. Các blocker canonical đã có focused fixes/tests: `RunResult.run_id`, checkpoint alignment, post-mutation snapshot, session/store isolation, immutable lease content, silent schema, atomic cursor/response và Web stale/ACK retry. HTTP TestClient/AnyIO portal timeout vẫn được phân loại là chưa kiểm chứng.

## Kiến trúc đã chốt

```text
canonical solver/trace
  → checkpoint policy + primary READY
  → PresentationStrategy (pure): SILENT | TEMPLATE | LLM
  → deterministic template fallback
  → (LLM only when internal_live + complex, or Why request)
  → allowlisted provider input
  → closed output schema + deterministic verifier
  → revalidate checkpoint/session/time/safety
  → immutable presentation artifact + pinned lease
  → offered/envelope
  → Web render + displayed ACK
```

Provider adapter không có tools và không được gọi simulator, solver, store, dispatcher, OSRM hoặc runtime provider. Network/store/claim/telemetry do orchestration service sở hữu; `CheckpointPresenter` vẫn side-effect-free.

## Canonical prerequisite gate

Internal-live bị khóa cho đến khi focused tests chứng minh:

- `run_id` đi qua `RunResult → demo trace → session → checkpoint → response`;
- mỗi READY checkpoint attach đúng một lần hoặc bị loại bởi policy với reason;
- snapshot của transition phản ánh state sau mutation;
- store/session replay không kế thừa sai lifecycle của run khác;
- lease lưu presentation artifact ID, content digest và source/version;
- silent response đúng AdviceEnvelopeV2 shape;
- cursor và response cache publish atomic, retry idempotent;
- Web bỏ qua response có `step_version` cũ và retry displayed ACK sau failure;
- HTTP contract test không còn treo hoặc đã có root-cause fixture chứng minh boundary khác.

Không dùng Agent để che bất kỳ blocker nào trong gate.

## PresentationStrategy

Interface pure:

```python
class PresentationDecision(TypedDict):
    strategy: Literal["SILENT", "TEMPLATE", "LLM"]
    reason_code: str

decide_presentation(
    checkpoint: Mapping[str, Any],
    facts: Sequence[Mapping[str, Any]],
    numbers: Sequence[Mapping[str, Any]],
    caveats: Sequence[Mapping[str, Any]],
    *, mode: str, is_moving: bool,
) -> PresentationDecision
```

Rules:

- no checkpoint, suppressed, queued, expired, superseded hoặc unsafe moving → `SILENT`;
- known/repeated action, simple facts, no complex caveat/uncertainty và có registry template → `TEMPLATE`;
- complex multi-fact, complex caveat hoặc current/future explanation dài → `LLM` chỉ khi `mode=internal_live` và provider enabled;
- `mode=template` luôn ép về `TEMPLATE`; `mode=shadow` giữ card template và chỉ cho phép shadow evaluation;
- provider disabled/unavailable được ghi reason (`llm_disabled` hoặc `provider_unavailable`) và rơi về template.

Reason codes đóng:

`simple_known_template`, `repeated_advice`, `complex_multi_fact`, `complex_caveat`, `current_future_explanation`, `user_requested_why`, `llm_disabled`, `provider_unavailable`, `unsafe_while_moving`.

## Template registry

Registry immutable, versioned theo `solver/topic`, canonical action, reason code, current/future shape, locale và surface. Mỗi entry khai báo:

- `template_key`, `template_version`;
- supported current action/future plan;
- required fact/number/caveat IDs;
- `now`, `next`, `why` fragments;
- max lengths và deterministic fallback reason.

Template render current action và future plan riêng. Ví dụ `ONLINE` hiện tại + `SWAP` tương lai phải tạo “Bây giờ: Tiếp tục online” và “Sắp tới: Đổi pin trong …”, không được đổi current action thành SWAP. Số chỉ được lấy từ typed number registry và format bởi code.

## Proactive Agent contract

Input schema mới `agent_presentation_input@1.1.0` giữ input 1.0 upcast được, bổ sung typed `future_plan`:

```json
{
  "schema_version": "1.1.0",
  "checkpoint_id": "...",
  "surface": "nudge",
  "locale": "vi-VN",
  "topic": "energy",
  "current_action": {"code": "ONLINE", "label_id": "action.online"},
  "future_plan": [{"code": "SWAP", "label_id": "action.swap", "window": {"start": "...", "end": "..."}}],
  "action_window": null,
  "facts": [{"id": "F1", "value": "..."}],
  "numbers": [{"id": "N1", "value": 37.5, "unit": "percent", "source": "..."}],
  "caveats": [{"id": "C1", "value": "..."}],
  "confidence_band": "medium",
  "summary_max_chars": 120,
  "why_max_chars": 280
}
```

Output remains closed:

```json
{
  "schema_version": "1.0.0",
  "checkpoint_id": "...",
  "reason_template": "... {{F1}} ...",
  "why_template": "... {{N1}} ...",
  "used_fact_ids": ["F1"],
  "used_number_ids": ["N1"],
  "used_caveat_ids": ["C1"]
}
```

Verifier vetoes extra fields, ID mismatch, unknown IDs, free digits, action/window/future conflict, fabricated zone/route/payout/SOC, trip acceptance advice, promises, unsafe markup/control characters, overlength and stale context. No LLM-as-judge is required for MVP; deterministic verifier is authoritative. Maximum one repair; otherwise template fallback.

## Provider adapter

```python
class AdviceAgentProvider(Protocol):
    model_version: str
    def generate(self, request: AgentRequest) -> ProviderResult: ...
```

`OpenAIAdviceProvider` loads `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `DEFAULT_MODEL` at runtime through the existing safe env loader. It uses JSON mode, timeout and one bounded request; no tools. Authorization values, raw headers and key material are never included in errors, logs or artifacts. Usage is redacted to token counts/latency/cost when provider supplies cost; unknown cost remains `null`.

## Generation and lease states

Generation artifact state:

```text
NOT_REQUESTED → CLAIMED → GENERATING → VERIFIED → STORED
                         ├→ TIMEOUT
                         ├→ PROVIDER_ERROR
                         └→ VERIFIER_REJECTED → TEMPLATE_FALLBACK
```

`DISCARDED_STALE` is an artifact/telemetry outcome, not a checkpoint presentation state. `CACHE_HIT` avoids generation. Lease record pins `presentation_artifact_id`, `content_digest`, `presentation_source`, template/model/prompt/schema/verifier/policy versions. Retrying a display ID returns the exact pinned content.

## Lazy “Vì sao?”

Demo-scoped endpoint:

```text
POST /api/v1/demo/sessions/{session_id}/advice/{checkpoint_id}/why
```

Body:

```json
{"display_id":"...", "client_request_id":"...", "expected_step_version": 3}
```

Response is a closed explanation envelope containing checkpoint/display IDs, `explanation`, `is_historical`, `presentation_source`, provenance/version metadata and a fallback/status field. Server validates session/checkpoint/display relation and immutable presentation context. It never calls a solver or creates a checkpoint. Expired historical cards may be explained with `is_historical=true`, never re-offered. A successful request appends `expanded` side-channel event idempotently; it does not create `accepted` or execution.

If actor is currently moving, no long text/provider call is mounted; return a deterministic safety fallback/status. If provider fails, return deterministic explanation fallback and keep Next Step usable.

## UI behavior

Main card renders code-owned fields and verified reason/why using `textContent`/DOM APIs. The Why button is not pre-populated from `item.why`; it sends the lazy request, shows local loading, checks checkpoint ID/display ID/step version, then mounts the response. Older responses are ignored. ACK retry marks display as acknowledged only after a successful response. Next Step remains enabled except its own request busy state.

## Flags and rollback

Defaults remain:

```text
ADVICE_V2_ENABLED=0
ADVICE_PRESENTATION_MODE=template
ADVICE_WHY_AGENT_ENABLED=0
ADVICE_AGENT_ALLOWLIST=0
ADVICE_AGENT_KILL_SWITCH=0
ADVICE_AGENT_TIMEOUT_S=8
ADVICE_AGENT_MAX_CALLS=20
ADVICE_AGENT_MAX_OUTPUT_TOKENS=256
```

`template`, `shadow`, `internal_live` are supported. MVP can run proactive template plus Why `internal_live` only after owner enables the Why flag in an allowlisted demo environment. Disabling either flag returns immediately to template-only; no simulator, solver or legacy lifecycle mutation is required for rollback.

## Verification and evidence

Focused tests are mandatory after each phase. No full backend/simulator/solver sweep is required for this cycle. Before any provider call, canonical prerequisite tests and the HTTP timeout diagnosis must pass. Provider smoke, if run, must redact key and output only endpoint/model/latency/status.

Implementation evidence: canonical/Agent/Why focused Python gates pass (`118 passed, 1 deselected`), Web Node smoke and syntax checks pass, and the 5-seed checkpoint shadow comparator is `IDENTICAL`. No provider network call was made. HTTP contract timeout and Flutter/device V-25 remain open.

## Remaining owner decisions

No architecture decision remains open. The only operational approval required before `internal_live` is enabling the explicit Why/proactive flag in an allowlisted environment with a budget and kill-switch; default configuration stays disabled.
