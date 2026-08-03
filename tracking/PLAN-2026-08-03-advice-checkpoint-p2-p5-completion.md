# AdviceCheckpoint P2–P5 Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Mỗi thay đổi hành vi dùng TDD; không commit/push nếu user chưa yêu cầu.

**Goal:** Hoàn thiện AdviceCheckpoint từ shadow core thành đường trace simulator, API/UI template-only và agent shadow có kiểm chứng, không đổi dynamics simulation hoặc mở live LLM.

**Architecture:** Giữ event stream checkpoint riêng theo UPDATE-124. Product và simulator dùng chung normalizer/policy/presenter thuần nhưng có store riêng: SQLite transaction/lease cho product, RAM journal + post-run export cho simulator. Agent chỉ enrich lý do, không sở hữu action/window/numbers.

**Tech Stack:** Python 3.12, JSON Schema, SQLite, FastAPI/Pydantic, JavaScript Web, Flutter/Dart, pytest.

## Global constraints

- `source_decision_id` và `checkpoint_id` là hai identity riêng; không migration/backfill hoặc dual-write legacy lifecycle.
- S2 fail-closed `missing_state` nếu chưa có SOC/rest runtime thật; cấm dùng `_soc_proxy` như live.
- `presentation_mode=template|shadow`, mặc định `template`; live LLM ngoài scope.
- Giữ cadence 20 phút/topic và 6 proactive/ca; không tự đóng Q-13 hoặc V-21.
- Mỗi response tối đa một card; silent response không có checkpoint/display/action IDs.
- Mỗi cycle chạy focused tests rồi `pytest -q` và `pytest -q ui/backend/tests`; meaningful UI/sim change phải qua visual gate V-25 hoặc ghi blocker thật.

---

### Task 0: Reconcile và Wave 0 hardening

**Files:** `tracking/{ASSIGNMENTS,PENDING-REVIEW,TODO,PROJECT-GRAPH}.md`, plan/UPDATE mới, `ui/backend/app/routers/{advice,sim}.py`, `ui/contracts/advice.json`, backend tests.

**Produces:** legacy surface allowlist, driver-facing sim event allowlist, silent contract đầy đủ và documentation route hiện hành.

- [x] Release claim cũ và ghi claim chung do hai owner ủy quyền.
- [x] Reconcile UPDATE-121→124: separate stream supersede lifecycle extension; CKPT-MIG resolved-by-design; Q-14 = S1+S2 capability với S2 fail-closed; Q-13/V-21 vẫn mở.
- [x] RED: test v1 reject `safety`/topic lạ, không project `advice_rest_veto`, và mọi silent reason validate closed contract.
- [x] GREEN: sửa allowlist/contract tối thiểu; backend suite chạy hoàn tất ngoài sandbox.

### Task 1: Contract, normalizer, policy và store 1.1

**Files:** `schemas/advisor/advice_{checkpoint,checkpoint_event,artifact}.schema.json`, version snapshots/upcasters, `src/gsm_core/lifecycle/{checkpoint,checkpoint_store}.py`, focused tests.

**Produces:**

```python
normalize_solver_decision(
    solver_name, snapshot, solver_input, solver_report, source_decision_id
) -> RecommendationCandidate

evaluate_checkpoint(
    candidate, active_checkpoints, cadence_memory, now, is_driving
) -> CheckpointPolicyResult
```

- [x] RED/GREEN schema 1.1: source decision/run/input/report refs và `expanded` side-channel; snapshot 1.0 vẫn đọc/upcast được.
- [x] RED/GREEN taxonomy/action mapping và validity fail-closed theo S1/S2/S4/S7.
- [x] RED/GREEN policy order, deterministic checkpoint ID, material supersede và silent maintenance.
- [x] RED/GREEN `create_checkpoint_bundle()` atomic, conflicting retry fail-loud, RAM journal parity và measurement adapter không dual-write.

### Task 2: Simulator traceability

**Files:** exact existing S1/S2/S4/S7/shift-extension callsites dưới `src/gsm_sim/`, RunResult/export modules, `scripts/compare_checkpoint_shadow.py`, sim tests.

**Produces:** RAM-only tick journal; post-run `advice_artifacts.jsonl`, `advice_checkpoints.jsonl`, `advice_checkpoint_events.jsonl`, `execution_links.jsonl`; deterministic segment/execution identities.

- [x] RED/GREEN capture sanitized snapshot, exact solver input/report và source decision tại callsite hiện hữu, không thêm invocation/trigger.
- [x] RED/GREEN manifest count/digest và deterministic replay/export.
- [x] RED/GREEN post-run segment IDs/link rules; accepted và execution độc lập, relation mặc định `coincident`.
- [x] RED/GREEN metrics tách decision/event adherence, accept/execution rate và relation/confidence.
- [x] Comparator seeds 1000–1004: `IDENTICAL` 5/5.

### Task 3: Product S1/S2, atomic lease và API v2

**Files:** product state/orchestration modules, SQLite store, `ui/backend/app/routers/advice_v2.py`, `ui/contracts/advice_v2.json`, backend tests.

**Produces:** `ProductDriverRuntimeState`, `AdviceCheckpointService.get_advice()`, atomic presentation lease và closed API v2.

- [x] RED/GREEN true-state provider unavailable/stale/future-observed ⇒ `missing_state`, không gọi S2; fake trusted provider chứng minh S2 current/future action.
- [x] RED/GREEN S1/S2 failure isolation và `solver_set` chỉ chứa solver chạy thành công; S4 product không chạy.
- [x] RED/GREEN lease + `offered` cùng `BEGIN IMMEDIATE`; GET retry cùng display ID; client events idempotent; stale transition 409.
- [x] RED/GREEN surface-only query, feature flag default off, one-card/silent envelope, 404/409/422 semantics và v1 compatibility.

### Task 4: Web/Flutter template flow

**Files:** Web advice client/rendering, Flutter v2 models/service/home screen, UI tests.

**Produces:** clients chỉ gửi surface; mounted ACK đúng lúc; canonical card không recompute action/SOC/numbers/message; v2-disabled fallback v1.

- [x] RED/GREEN Web smoke cho silent/no fake ID, DOM-mounted ACK và response buttons.
- [x] Flutter model/service/code test; ACK trong post-frame callback; canonical fields và mock/proxy badge đọc từ provenance.
- [ ] `flutter analyze` / `flutter test`: `BLOCKED` vì environment không có Flutter/Dart SDK; backend contract và Web smoke đã xanh.

### Task 5: Structured presenter và verifier

**Files:** agent presentation schemas, `CheckpointPresenter`, verifier modules/tests.

**Produces:** side-effect-free presenter; agent output chỉ `reason_template`, `why_template` và used IDs.

- [x] RED/GREEN closed input/output schemas và max lengths 120/280.
- [x] RED/GREEN deterministic template rendering; checkpoint path không gọi legacy `_finish()`/EpisodeStore.
- [x] RED/GREEN veto malformed JSON, unknown IDs, bare digits, conflicting action, trip-specific advice, promises, urgency/window drift, CJK/overlength/timeout; một repair rồi template fallback.

### Task 6: Template runtime + agent shadow

**Files:** presentation runtime/config/cache/store, product integration, post-run sim evaluator/tests.

**Produces:** default template mode; internal shadow artifact không thay response/lifecycle; generation claim/cache key/TTL đúng validity.

- [x] RED/GREEN template mode không gọi model; shadow output không xuất hiện UI và stale output ghi `discarded_stale`.
- [x] RED/GREEN cache key đủ fingerprint/facts/locale/prompt/model/policy, một owner/key và timeout/error không ảnh hưởng template.
- [x] RED/GREEN simulator method D chạy post-run trên trajectory cố định; nhiều presenter dùng cùng artifacts.
- [x] Re-run 5-seed comparator; cache/fallback lifecycle instrumented, không bịa latency/token/cost khi chưa có provider call thật.

### Task 7: Verification và rollout verdict

**Files:** UPDATE theo cycle, TODO/graph/PENDING, visual evidence.

- [x] Full root 978 passed/4 skipped; backend 84 passed/1 warning.
- [ ] V-25 tám scenario: backend/Web automation có evidence; Flutter/device visual `BLOCKED` do thiếu SDK/emulator.
- [x] Adversarial review lifecycle, time/money/SOC/order conservation, future leak, CRN/RNG, hidden fallback, units, canonical UI source và MOCK/PROXY labels.
- [x] Giữ `ADVICE_V2_ENABLED=0` trong repo và `presentation_mode=template`; không claim production-ready/uplift.
