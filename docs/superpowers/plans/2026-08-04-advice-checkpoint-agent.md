# AdviceCheckpoint Agent Implementation Plan

> **Implementation status (2026-08-04):** Tasks 1–12 have code and focused evidence; Task 13 is implemented as a disabled/allowlisted gate but no live provider smoke was run; Task 14 evidence is recorded in `tracking/updates/UPDATE-134-advice-checkpoint-agent.md`. HTTP TestClient/AnyIO portal and Flutter/device visual remain open gates. The plan is retained as the dependency record; no full backend/simulator/solver sweep is claimed.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement this plan task-by-task. Each task is independently testable and ends with its own commit.

**Goal:** Build a template-first AdviceCheckpoint presentation path with deterministic strategy selection, strict provider isolation, and lazy “Vì sao?” explanations without weakening canonical simulator/lifecycle ownership.

**Architecture:** Repair canonical trace/session/lifecycle invariants first. Then add a pure template registry and `SILENT|TEMPLATE|LLM` strategy. Provider calls are orchestration-only, use allowlisted structured context, deterministic verification, generation claim/cache and immutable lease content; Web owns no canonical state.

**Tech Stack:** Python 3.12, FastAPI/Pydantic, SQLite checkpoint store, OpenAI-compatible SDK through existing `uv` llm extra, vanilla Web JavaScript, pytest and Node smoke tests.

## Global Constraints

- Do not call a provider before canonical prerequisite focused tests pass.
- Keep `ADVICE_V2_ENABLED=0`, `ADVICE_PRESENTATION_MODE=template`, `ADVICE_WHY_AGENT_ENABLED=0` as defaults.
- LLM cannot change action, action window, future plan, expiry, numbers, provenance, route, payout, SOC, trip or lifecycle.
- No provider tools; no simulator tick calls; no solver rerun on Next Step or Why.
- No raw credential, authorization header, PII, raw coordinates or full solver report in provider input/log/artifact.
- Template fallback must be built before every eligible provider attempt.
- Use TDD: add one failing focused test, run it RED, implement the minimum, run GREEN, then commit.
- Preserve unrelated dirty files and do not claim full-suite verification.

---

### Task 1: Propagate canonical `run_id`

**Files:**
- Modify: `src/gsm_sim/runner.py` (`RunResult`, `run_once`)
- Modify: `src/gsm_sim/world.py` only where the canonical run ID is already derived
- Modify: `src/gsm_sim/demo_trace.py` (`build_demo_trace`)
- Modify: `ui/backend/app/services/demo_session.py` (`_summary`, step response provenance)
- Test: `tests/test_demo_trace.py`, `ui/backend/tests/test_demo_step_contract.py`

**Interfaces:**
- `RunResult.run_id: str` is the deterministic ID emitted by the world/event log.
- `build_demo_trace(result, actor_id)` must expose the same non-empty `run_id`.

- [ ] Add a failing test that runs the existing demo configuration and asserts `result.run_id == result.events[0].run_id`, trace/session/step all expose that value.
- [ ] Run `uv run pytest -q tests/test_demo_trace.py::test_run_result_and_trace_propagate_run_id`; verify RED because `RunResult` has no field.
- [ ] Add the field without changing event generation or RNG; thread it through trace and session summaries.
- [ ] Run the focused test and `uv run pytest -q tests/test_demo_trace.py`; expect GREEN.
- [ ] Commit `fix: propagate simulator run identity into demo replay`.

### Task 2: Make checkpoint projection exactly-once and policy-aware

**Files:**
- Modify: `src/gsm_sim/demo_trace.py` (`_checkpoint_minute`, `_checkpoint_for`, `_checkpoint_transitions`)
- Test: `tests/test_demo_trace.py`, new `tests/test_demo_checkpoint_alignment.py`

**Interfaces:**
- `build_demo_trace()` returns one transition reference per READY checkpoint at most once.
- Dropped checkpoints carry an explicit trace reason (`not_ready`, `expired`, `superseded`, `missing_alignment`) instead of silently disappearing.

- [ ] Add a real-run fixture test counting READY checkpoint records and asserting every one is attached exactly once or has a reason in the trace audit list; assert no duplicate checkpoint IDs.
- [ ] Run `uv run pytest -q tests/test_demo_checkpoint_alignment.py`; verify RED with the current fractional timestamp/equality behavior.
- [ ] Use exact source decision/event identity where available; otherwise use a deterministic time bucket/tolerance and a stable tie-break that preserves policy primary selection. Do not sort raw IDs as the policy.
- [ ] Add same-time multi-candidate tests for primary selection and non-primary audit reasons.
- [ ] Run alignment tests plus `tests/test_demo_trace.py`; expect GREEN.
- [ ] Commit `fix: align demo checkpoints exactly once`.

### Task 3: Capture post-mutation observer snapshots and prove neutrality

**Files:**
- Modify: `src/gsm_sim/world.py` (`log` call boundaries for order/cancel transitions)
- Test: new `tests/test_demo_trace_neutrality.py`, existing checkpoint trace tests

**Interfaces:**
- A visible transition snapshot is a completed state boundary; if a before-state is needed for audit it is labeled separately and is never used as the canonical driver snapshot.

- [ ] Add a failing real-run test asserting `order_matched` snapshot is `ENROUTE` (or the documented post-match state) and cancellation snapshot is `IDLE`.
- [ ] Run the focused test and observe RED from the current pre-mutation log calls.
- [ ] Move only observer capture boundaries; do not add RNG draws or alter dispatcher/solver dynamics.
- [ ] Add a paired advice-trace off/on comparator for one exact demo configuration, checking order outcomes, terminal actor state, payout, SOC, trips and segment sequence for seeds `1000..1004`.
- [ ] Run focused neutrality tests; expect GREEN.
- [ ] Commit `fix: capture canonical post-mutation demo snapshots`.

### Task 4: Isolate demo checkpoint state and pin lease presentation

**Files:**
- Modify: `ui/backend/app/services/demo_session.py` (session-scoped store path/namespace)
- Modify: `src/gsm_core/lifecycle/checkpoint_store.py` (lease record content fields)
- Modify: `ui/backend/app/services/advice_checkpoint.py` (`_envelope`, existing lease replay)
- Test: `ui/backend/tests/test_demo_advice_bridge.py`, `tests/test_checkpoint_store.py`

**Interfaces:**
- A lease record contains `presentation_artifact_id`, `content_digest`, `presentation_source`, `template_version`, `model_version`, `prompt_version`, `schema_version`, `verifier_version`, and `policy_version`.
- Existing lease retry returns the exact stored envelope/presentation artifact, not a fresh render.

- [ ] Add RED tests for two demo sessions using the same deterministic checkpoint and for retry after presentation mode changes; expect current shared DB/renderer behavior to fail.
- [ ] Add a session/run namespace to demo persistence while preserving product store compatibility.
- [ ] Persist immutable presentation artifact and include its digest/version metadata in the lease record; keep `acquire_presentation_lease` atomic.
- [ ] Return the pinned artifact on lease retry and reject conflicting content under the same display ID.
- [ ] Run store/bridge focused tests; commit `fix: isolate replay state and pin presentation leases`.

### Task 5: Normalize silent envelopes and make cursor publication atomic

**Files:**
- Modify: `ui/backend/app/services/demo_session.py` (`_advice`, `advance`/`next_step`)
- Test: `ui/backend/tests/test_demo_step_contract.py`, `ui/backend/tests/test_demo_session_api.py`

**Interfaces:**
- Every demo `advice` response is either a schema-valid ready envelope or `{status,surface,generated_at,silent,items:[]}`.
- A failed response build does not leave a committed cursor/version; same client request returns the exact cached response.

- [ ] Add RED schema validation for no-checkpoint, suppressed, moving and expired advice; add a response-build exception test that inspects cursor/version.
- [ ] Run focused tests and reproduce the HTTP TestClient hang with a 20-second timeout; record whether it is application or anyio boundary behavior.
- [ ] Stage cursor/version/cache update with response construction under the existing lock; publish only after all canonical projections are complete.
- [ ] Validate request payload digest when reusing a `client_step_id`; conflicting reuse returns `409`.
- [ ] Run direct service tests and the isolated HTTP contract test; do not claim API pass unless the hang is resolved or explicitly classified with a deterministic fixture.
- [ ] Commit `fix: make demo step responses atomic and schema-valid`.

### Task 6: Add Web monotonic response and ACK retry guards

**Files:**
- Modify: `ui/web/js/app.js` (`renderDemoStep`, `nextDemoStep`, display ACK)
- Modify: `ui/web/js/api.js` for Why request helper later shared by Task 9
- Test: `ui/web/tests/unified-demo.mjs`, new focused Node assertions

**Interfaces:**
- Web renders only responses whose `step_version` is not older than the current rendered version.
- `ackedDisplayIds` is updated after successful ACK; failed ACK remains retryable.

- [ ] Add RED Node tests for stale response rejection and failed ACK retry.
- [ ] Run `node ui/web/tests/unified-demo.mjs`; verify RED against current pre-mark ACK and missing monotonic guard.
- [ ] Implement a response version check and pending ACK state without using raw HTML.
- [ ] Run Node smoke/syntax tests; commit `fix: guard replay responses and retry display acknowledgements`.

### Task 7: Implement versioned template registry

**Files:**
- Create: `src/gsm_core/advisor/checkpoint_templates.py`
- Modify: `src/gsm_core/advisor/checkpoint_presenter.py` to consume the registry
- Test: new `tests/test_checkpoint_templates.py`, `tests/test_checkpoint_presenter.py`

**Interfaces:**
- `CheckpointTemplateRegistry.resolve(checkpoint, facts, numbers, caveats, locale, surface) -> TemplateRender`
- `TemplateRender` contains code-owned `title`, `summary`, `why`, `template_key`, `template_version`, required IDs and fallback reason.

- [ ] Add RED tests for S1 bonus, S2 ONLINE-now/SWAP-future, SWAP, REST, END and unknown action fallback; assert current/future wording never swaps actions.
- [ ] Run the focused template tests and observe RED because current presenter uses one action-only tuple.
- [ ] Implement versioned entries keyed by topic/action/reason/current-future/locale/surface; format numbers only from typed registries.
- [ ] Run template/presenter adversarial tests; commit `feat: add deterministic checkpoint template registry`.

### Task 8: Add pure PresentationStrategy

**Files:**
- Create: `src/gsm_core/advisor/presentation_strategy.py`
- Modify: `ui/backend/app/services/advice_checkpoint.py` to call the strategy after primary selection
- Test: `tests/test_presentation_strategy.py`, `ui/backend/tests/test_demo_advice_bridge.py`

**Interfaces:**
- `decide_presentation(...) -> PresentationDecision(strategy, reason_code)` is pure and deterministic.

- [ ] Add RED cases for simple/repeated→TEMPLATE, complex facts/caveats/current-future→LLM only in internal_live, no checkpoint/moving→SILENT and disabled provider→TEMPLATE.
- [ ] Run focused strategy tests; observe RED because no strategy exists.
- [ ] Implement reason-code rules and wire template fallback creation before any provider branch.
- [ ] Assert strategy reason is included in redacted telemetry/artifact metadata.
- [ ] Run focused tests; commit `feat: select checkpoint presentation deterministically`.

### Task 9: Add strict Agent schemas and provider adapter

**Files:**
- Create: `src/gsm_core/advisor/advice_agent.py`
- Create: `schemas/advisor/agent_presentation_input@1.1.0.schema.json`
- Modify: `src/gsm_core/advisor/checkpoint_presenter.py` verifier for future-plan/action/control checks
- Test: `tests/test_advice_agent_provider.py`, `tests/test_checkpoint_presenter.py`

**Interfaces:**
- `AdviceAgentProvider.generate(request: AgentRequest) -> ProviderResult`
- `build_agent_input(...)` emits only allowlisted fields, including typed `future_plan`.
- `verify_agent_output(...)` accepts only the closed reason/why contract.

- [ ] Add RED tests with a fake provider for structured JSON, timeout, provider exception, credential-redaction and tool absence; add future/current conflict cases.
- [ ] Run focused provider tests; verify RED because only legacy Composer client exists.
- [ ] Implement `OpenAIAdviceProvider` using lazy `openai.OpenAI`, `.env` values, bounded timeout, JSON mode and redacted errors. Do not reuse `LLMComposerClient`.
- [ ] Keep credentials out of provider result, artifacts and logs; record model/latency/usage only.
- [ ] Run tests without network; commit `feat: add strict AdviceCheckpoint provider adapter`.

### Task 10: Wire proactive shadow/internal-live generation

**Files:**
- Modify: `ui/backend/app/services/advice_checkpoint.py` (`_prepare_presentation`, generation state, revalidation)
- Modify: `src/gsm_core/lifecycle/checkpoint_store.py` generation artifact/metric helpers if required
- Modify: `src/gsm_core/advisor/checkpoint_presenter.py` mode handling (`template|shadow|internal_live`)
- Test: new `ui/backend/tests/test_advice_generation_flow.py`, existing presenter/lease tests

**Interfaces:**
- `template` never calls provider;
- `shadow` calls only eligible complex generation off the driver response and stores evaluation artifact;
- `internal_live` calls only after primary READY/strategy and before lease; on any failure returns template.

- [ ] Add RED tests for template zero calls, complex shadow artifact, internal-live verified output, timeout/provider/verifier/stale fallback and one repair maximum.
- [ ] Run focused generation tests; verify RED because current presenter only knows shadow and envelope always says template.
- [ ] Implement claim/cache namespace with request type/version digest, template-first fallback, provider call, verifier, post-call state/session/time safety revalidation and immutable artifact persistence.
- [ ] Never let provider exception escape `Next Step`; retain template response and redacted metrics.
- [ ] Run focused generation/lease tests. Do not call `.env` provider yet unless the canonical gate (Tasks 1–6) is green.
- [ ] Commit `feat: add safe selective checkpoint agent presentation`.

### Task 11: Add lazy Why service and API

**Files:**
- Modify: `ui/backend/app/services/advice_checkpoint.py` with `explain_why(...)`
- Modify: `ui/backend/app/routers/demo.py` with `/why`
- Test: new `ui/backend/tests/test_demo_advice_why.py`

**Interfaces:**
- `explain_why(session_id, checkpoint_id, display_id, client_request_id, expected_step_version) -> explanation envelope`
- Same request ID/context returns the same cached explanation; no solver/checkpoint creation.

- [ ] Add RED tests for zero call before click, one call/cache hit after click, relation mismatch `409`, historical expired explanation, moving suppression, provider failure fallback and expanded-only event.
- [ ] Run focused Why tests and observe RED because no endpoint/service exists.
- [ ] Implement immutable context lookup, `why_explanation` cache/claim key, strict output verification, historical flag, stale step guard and idempotent expanded side-channel.
- [ ] Run focused Why tests; commit `feat: add lazy AdviceCheckpoint why explanation`.

### Task 12: Wire Web lazy Why UI safely

**Files:**
- Modify: `ui/web/js/api.js` (`demoAdviceWhy`)
- Modify: `ui/web/js/app.js` (`renderDemoAdvice`, Why handler)
- Test: `ui/web/tests/unified-demo.mjs`, new focused DOM/source assertions

**Interfaces:**
- Why button sends checkpoint/display/client request/step version and mounts only matching response.
- Dynamic text uses `textContent`/DOM APIs only.

- [ ] Add RED tests for no-click zero requests, loading state, success, retry, stale response rejection and fallback explanation.
- [ ] Run Node tests and observe RED because current code toggles pre-rendered `item.why` locally.
- [ ] Implement lazy request, local loading/disabled state, matching identity checks and safe text mounting without blocking Next Step.
- [ ] Run Node smoke and syntax tests; commit `feat: add lazy why explanation to replay card`.

### Task 13: Enable selective internal-live only after gate

**Files:**
- Modify: `ui/backend/app/services/advice_checkpoint.py` flag parsing and provider construction
- Modify: `.env.example` (never `.env`) with redacted flag names/defaults
- Test: `ui/backend/tests/test_advice_generation_flow.py`, `ui/web/tests/unified-demo.mjs`

**Interfaces:**
- Defaults remain template/Why disabled; an allowlisted internal environment may set `ADVICE_WHY_AGENT_ENABLED=1` while proactive remains template.

- [ ] Add RED config tests proving every default disables network and Why click falls back without provider.
- [ ] Run config tests; then execute all canonical prerequisite focused tests from Tasks 1–6.
- [ ] Only after those tests pass, configure a single provider smoke call using `.env`; output must redact key and contain only status/model/latency/usage.
- [ ] Enable internal-live only for the explicit allowlisted demo process; verify timeout/kill-switch returns template.
- [ ] Commit `feat: gate selective AdviceCheckpoint agent demo mode`.

### Task 14: Evidence, adversarial review and rollback documentation

**Files:**
- Create: `tracking/updates/UPDATE-134-advice-checkpoint-agent.md`
- Modify: `tracking/TODO.md` and `tracking/PROJECT-GRAPH.md` for the verified Agent demo status
- Test/evidence: focused commands from Tasks 1–13

- [ ] Record exact test commands/counts, provider smoke redacted result, strategy counts, cache hits, fallbacks, verifier rejects, latency/tokens/cost when available.
- [ ] Run adversarial review for lifecycle terminal states, future/current confusion, stale provider results, credential leakage, XSS/control characters, ACK retry, run/session identity and template-only rollback.
- [ ] Keep Flutter/device and production/canary gates open; use `DONE-CODE` only for verified code and `WAITING-VERDICT`/`BLOCKED` for unverified visual/provider gates.
- [ ] Commit `docs: record AdviceCheckpoint Agent demo evidence`.

## Rollback strategy

Set `ADVICE_PRESENTATION_MODE=template`, `ADVICE_WHY_AGENT_ENABLED=0`, `ADVICE_AGENT_ALLOWLIST=0`, `ADVICE_AGENT_KILL_SWITCH=1` and keep `ADVICE_V2_ENABLED=0`. Template presenter and deterministic checkpoint lifecycle remain usable without importing or instantiating the provider. No simulator dynamics or solver objective changes are part of rollback.

## Focused verification commands

```bash
uv run pytest -q tests/test_demo_trace.py tests/test_checkpoint_presenter.py
uv run pytest -q ui/backend/tests/test_demo_advice_bridge.py ui/backend/tests/test_demo_advice_why.py ui/backend/tests/test_demo_step_contract.py
node ui/web/tests/unified-demo.mjs
node --check ui/web/js/app.js ui/web/js/api.js
git diff --check
```

The HTTP TestClient contract is run separately with a timeout until its existing hang is diagnosed; no full backend/simulator/solver suite is required for this cycle.
