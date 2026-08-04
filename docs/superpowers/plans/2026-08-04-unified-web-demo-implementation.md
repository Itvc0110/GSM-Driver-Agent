# Unified Web Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Each task is independently testable and ends with its own commit.

**Goal:** Hợp nhất Web `/app/` với một simulator replay server-owned, projection trip/route canonical, AdviceCheckpoint trace và template-first Agent presentation.

**Architecture:** Simulator vẫn chạy một `run_once()` đầy đủ trước khi mở demo. Một trace hậu xử lý tạo các transition có ý nghĩa cho actor; `DemoSession` giữ cursor, step version và idempotency trong bộ nhớ của backend. `POST /api/v1/demo/sessions/{id}/steps` chỉ trả canonical snapshot từ trace, gọi OSRM online để lấy geometry hiển thị (có fallback), rồi trình bày checkpoint đã có trong trace. Agent không có tool; template luôn render được và mọi generation lỗi/stale chỉ rơi về template.

**Tech Stack:** Python 3.11+, FastAPI/Pydantic, existing `gsm_sim`/`CheckpointStore`, Leaflet Web ES modules, focused pytest/Node smoke tests.

## Global Constraints

- Không refactor SimPy thành live mutable engine và không gọi solver lại trong mỗi click.
- Trace chỉ quan sát; không thêm RNG draw, không đổi objective, cadence hoặc simulator dynamics.
- Backend là nguồn canonical của SOC, payout, trip state, route status và advice; Web chỉ render.
- OSRM online chỉ cung cấp geometry/metadata route; simulator giữ thời gian, khoảng cách, SOC và payout canonical.
- Agent tool access = NONE; agent chỉ trả structured reason/why và used fact/number/caveat IDs.
- `accepted`/`dismissed` trong demo là intent lifecycle, không phân nhánh trajectory.
- `ADVICE_V2_ENABLED=0` và `presentation_mode=template` giữ mặc định; không bật live provider.
- Không chạm các thay đổi dirty có trước trong worktree.
- Mỗi task: RED test → GREEN implementation → focused verification → một commit riêng → một UPDATE tracking tương ứng.

## Implementation status (2026-08-04)

Tasks 1–5 are implemented in focused commits `9cccfbc`, `3cb655d`, `926bf11`, `0785728`,
and `f7d1b8c`; the presentation provenance follow-up is `1def318`. Focused evidence is
recorded in UPDATE-128..132 and the final evidence/rollback note is UPDATE-133. The live
default simulator run, browser visual review, multi-worker deployment and Agent provider are
intentionally **not** claimed: they remain `WAITING-VERDICT`/open gates.

---

### Task 1: Observable replay trace và canonical transition projection

**Files:**
- Modify: `src/gsm_sim/world.py` (`Event`/`World.log`, `World.__init__`)
- Modify: `src/gsm_sim/runner.py` (`RunResult`, `run_once`)
- Create: `src/gsm_sim/demo_trace.py`
- Test: `tests/test_demo_trace.py`

**Interfaces:**
- Produces `RunResult.trace_snapshots: list[dict]` containing only post-observation state and `event_index`.
- Produces `build_demo_trace(result, actor_id) -> dict` with `run_id`, actor metadata, ordered `transitions`, `checkpoints`, and provenance.
- A transition has `transition_id`, `event_index`, `t_min`, `kind`, `driver`, `state_delta`, `trip`, `segment`, `checkpoint`, `timeline_event`.

- [ ] Write tests proving snapshots contain state/time/position/SOC/payout/points/trip order reference and enabling trace does not change semantic simulator fingerprint.
- [ ] Write tests proving visible event ordering is deterministic, one transition ID is stable across repeated projection, and no raw phone/name/PII is introduced.
- [ ] Run `pytest -q tests/test_demo_trace.py` and observe RED because `trace_snapshots`/projection do not exist.
- [ ] Add `World.trace_snapshots`; make `World.log` append a state snapshot after appending the existing event. The snapshot must not call RNG or mutate actor state.
- [ ] Thread snapshots through `RunResult` without changing existing fields or `semantic_fingerprint` inputs.
- [ ] Implement pure event-to-transition projection using existing events, annotated segments, orders and checkpoint artifacts. Filter only driver-visible events; derive trip state from events, never from client input.
- [ ] Run focused tests and the existing trace tests; commit `feat: add canonical simulator demo trace`.

### Task 2: Server-owned demo session and cursor semantics

**Files:**
- Create: `ui/backend/app/services/demo_session.py`
- Create: `ui/backend/app/routers/demo.py`
- Modify: `ui/backend/app/main.py`
- Test: `ui/backend/tests/test_demo_session_api.py`

**Interfaces:**
- `DemoSessionService.create(seed: int = 1000) -> dict`.
- `DemoSessionService.select_actor(session_id: str, actor_id: int) -> dict`.
- `DemoSessionService.state(session_id: str) -> dict`.
- `DemoSessionService.advance(session_id: str, *, client_step_id: str, expected_step_version: int) -> dict`.
- `POST /api/v1/demo/sessions` body `{seed}`.
- `PUT /api/v1/demo/sessions/{session_id}/driver` body `{actor_id}`.
- `GET /api/v1/demo/sessions/{session_id}/state`.
- `POST /api/v1/demo/sessions/{session_id}/steps` body `{client_step_id, expected_step_version}`.

- [ ] Add RED tests for create/select, actor-not-found, no-selected-actor, cursor `-1`, one transition per advance, same client idempotency, stale version `409`, and completed session.
- [ ] Implement an in-process session registry with `RLock`, immutable cached `RunResult`/trace, selected actor, cursor, step version, status and response cache. Use an explicit demo-session ID, never `driver_id` as session identity.
- [ ] Reuse simulator run cache and enable only observational trace capture in the demo config; do not enable new solver behavior.
- [ ] Add router exception mapping: `404` unknown session/actor, `409` version/session conflict, `422` invalid body, `410` completed session where appropriate.
- [ ] Run `pytest -q ui/backend/tests/test_demo_session_api.py`; commit `feat: add server-owned demo session cursor`.

### Task 3: Canonical step response, trip projection and geometry route

**Files:**
- Modify: `ui/backend/app/services/demo_session.py`
- Modify: `ui/backend/app/routers/demo.py`
- Modify: `ui/backend/app/routers/routing.py` only to expose a provider-neutral geometry helper if needed
- Modify: `ui/backend/app/models.py` only for new response models if validation is shared
- Test: `ui/backend/tests/test_demo_step_contract.py`, `ui/backend/tests/test_demo_route_projection.py`

**Interfaces:**
- Step response fields: `session_id`, `run_id`, `seed`, `actor_id`, `step_version`, `simulation_time`, `transition`, `driver`, `state_delta`, `trip`, `map`, `routes`, `advice`, `timeline`, `provenance`.
- Route leg fields: `route_id`, `leg` (`driver_to_pickup|pickup_to_destination`), `coords`, `distance_km`, `duration_min`, `source`, `route_is_real_road`, `is_mock`.

- [ ] Add RED contract tests asserting the response is closed enough for Web rendering, includes driver/trip/map/route/advice/timeline together, and never exposes a fake advice ID on silent steps.
- [ ] Add RED tests for two separate legs, route cache reuse, route timeout/provider failure fallback, and canonical simulator payout/SOC remaining unchanged by route distance.
- [ ] Implement deterministic trip projection from `Order` plus event-derived lifecycle (`OFFERED`, `DECLINED`, `MATCHED`, `PICKED_UP`, `COMPLETED`, `CANCELLED_AFTER_ACCEPT`, `SKIPPED_SOC`).
- [ ] Implement route projection using existing online routing tiers and an in-session cache keyed by rounded endpoints/leg; strip fare fields from route and use simulator payout only.
- [ ] Return straight-line fallback metadata on provider failure; never fail the step solely because OSRM is unavailable.
- [ ] Run focused contract/route tests; commit `feat: return canonical demo step snapshots`.

### Task 4: AdviceCheckpoint bridge and safe presentation source

**Files:**
- Modify: `ui/backend/app/services/demo_session.py`
- Modify: `ui/backend/app/services/advice_checkpoint.py` only to add `present_existing_checkpoint(...)` if direct reuse is not possible
- Modify: `src/gsm_core/advisor/checkpoint_presenter.py` for deterministic text escaping/forbidden control characters
- Test: `ui/backend/tests/test_demo_advice_bridge.py`, `tests/test_checkpoint_presenter.py`

**Interfaces:**
- `present_existing_checkpoint(checkpoint, artifacts, *, surface, now_iso) -> AdviceEnvelopeV2 | silent` reuses persisted trace refs and existing lease/event store; it never invokes a solver.
- Demo response `advice` is either `{status: "silent", reason_code}` or the existing canonical envelope with `checkpoint_id`, `display_id`, action/window/numbers/provenance and `presentation_source`.

- [ ] Add RED tests for a matching READY checkpoint, driver mismatch, expired/superseded checkpoint, silent/no checkpoint, and template fallback when the provider is disabled.
- [ ] Add RED verifier tests for `<script>`, HTML tags, control characters, action/window conflicts, and stale result completion after validity expiry.
- [ ] Persist trace artifact/checkpoint records through `CheckpointStore.create_checkpoint_bundle` once per session, append only the existing `ready` event, and acquire one immutable presentation lease. Do not dual-write legacy lifecycle.
- [ ] Use `CheckpointPresenter(mode="template")` by default. If a future demo provider is configured, keep `agent_presentation_input/output` and existing generation claim/cache/verifier boundaries; no tool object is passed to the agent.
- [ ] Pin rendered presentation in the lease response cache so retries cannot change text. Revalidate at generation completion time, not generation start time.
- [ ] Run focused presenter/advice bridge tests; commit `feat: bridge traced checkpoints to demo presentation`.

### Task 5: Web migration to server-owned demo session

**Files:**
- Modify: `ui/web/index.html`
- Modify: `ui/web/js/api.js`
- Modify: `ui/web/js/app.js`
- Modify: `ui/web/js/cards.js` only for safe text DOM rendering and demo envelope mounting
- Test: `ui/web/tests/demo-session.mjs`, `ui/web/tests/advice-v2.mjs`

**Interfaces:**
- Web sends only `create session`, `select actor`, and `Next Step` with `client_step_id`/`expected_step_version`.
- Web renders the canonical response and sends mounted ACK after DOM insertion. Product Advice
  v2 uses `/api/v2/advice/{checkpoint_id}/display`; the internal trace-backed demo uses its
  scoped `/api/v1/demo/sessions/{session_id}/advice/{checkpoint_id}/display` endpoint while
  `ADVICE_V2_ENABLED=0`, writing the same lease/event store without enabling product polling.

- [ ] Add RED Node tests proving no `tripStep` state or `/api/v1/trip/step` call remains in the demo flow, retries reuse step response, and silent advice renders no action buttons/fake IDs.
- [ ] Add RED DOM-level helper tests for text-only rendering of Agent reason/why; no raw `innerHTML` for model-owned strings.
- [ ] Add session controls/selected actor status and a single `Next Step` button to `/app/`; retain existing income/settings screens but stop using scripted trip state as source of truth.
- [ ] Add API methods for session create/select/state/step. Generate stable client step IDs for retries; keep latest step version and ignore older responses.
- [ ] Replace hard-coded trip lifecycle/map mutation with one render function consuming `step.transition`, `step.driver`, `step.trip`, `step.routes`, `step.advice`, and provenance. Render route legs separately and show OSRM/fallback source.
- [ ] Mount AdviceCheckpoint card only from the response, ACK after DOM insertion, and keep accepted/dismissed/expanded as intent events only.
- [ ] Run Node smoke tests and `git diff --check`; commit `feat: migrate web demo to canonical replay steps`.

### Task 6: Documentation, adversarial review and focused verification

**Files:**
- Create: `tracking/updates/UPDATE-128-unified-web-demo.md`
- Modify: `tracking/TODO.md`, `tracking/PROJECT-GRAPH.md`
- Modify: `ui/contracts/` only if the new step envelope is versioned as a JSON Schema

- [ ] Run only focused verification: new simulator trace tests, new backend demo tests, existing AdviceCheckpoint/presenter tests, Web Node smoke tests, Python compile and `git diff --check`. Do not rerun the full backend/simulator/solver suites unless the owner explicitly requests it.
- [ ] Perform adversarial review for lifecycle/terminal states, retry/idempotency, stale Agent/OSRM responses, RNG neutrality, canonical UI rendering, MOCK provenance and route leg correctness.
- [ ] Record exact commands, counts, dirty-worktree preservation, unverified Flutter/device gate and visual status in UPDATE-128.
- [ ] Update TODO/graph with `DONE-CODE` only for code gates actually verified; keep V-25/device and live-provider gates open.
- [ ] Commit `docs: record unified web demo implementation evidence`.

## Rollback Strategy

The old `/api/v1/trip/step` endpoint remains available for compatibility but is no longer used by the unified demo page. A deployment can roll Web back to the previous static bundle, disable the demo route behind its server flag, or keep `presentation_mode=template` and `ADVICE_V2_ENABLED=0`; no simulator, solver or legacy lifecycle data is mutated by the new session layer.

## Open Decisions

1. Owner must choose whether `/app/` is the sole demo surface (recommended) while `/app/mo-phong/` remains analytical replay.
2. Owner must choose one fixed demo seed/actor list for V-25 visual review; implementation defaults to seed `1000` and allows actor selection.
3. Owner must approve any provider credential/allowlist before enabling an internal-live Agent; this cycle implements safe template-first wiring only.
4. Flutter/device visual review remains outside this environment and is not closed by the Web implementation.
