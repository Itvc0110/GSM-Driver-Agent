# UPDATE-133 — Unified Web Demo evidence và handoff

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / WAITING-VERDICT`
- **TODO:** `WEB-DEMO-UNIFIED`

## Commit chain

| Commit | Scope |
|---|---|
| `58f47b7` | implementation plan và dependency/invariant/rollback docs |
| `9cccfbc` | observer-only simulator snapshots + deterministic trace projection |
| `3cb655d` | server-owned session/actor/cursor/version/idempotency API |
| `926bf11` | canonical step, trip lifecycle projection, two-leg route/fallback |
| `0785728` | trace artifact/checkpoint bridge, READY/validity gate, lease, verifier hardening |
| `f7d1b8c` | Web actor picker/Next Step/canonical render và demo ACK endpoints |
| `1def318` | `presentation_source=template` contract field |
| `546f732` | fail-closed `unsafe_while_moving` gate for replay advice |

## Focused verification evidence

Đã chạy, không chạy full backend/simulator/solver suite:

```text
pytest tests/test_demo_trace.py                                      3 passed
pytest checkpoint_trace focused tests                                2 passed
pytest presenter + demo bridge/ACK/step/session tests                23 passed, 1 warning
pytest ui/backend/tests/test_advice_v2_api.py test_contracts.py      28 passed, 1 warning
node ui/web/tests/unified-demo.mjs                                   PASS
node ui/web/tests/advice-v2.mjs                                     PASS
node ui/web/tests/demo-pricing.mjs                                  PASS
node --check ui/web/js/app.js ui/web/js/api.js                      PASS
JSON.parse(ui/contracts/advice_v2.json)                              PASS
python -m compileall (changed Python modules)                        PASS
git diff --check                                                     PASS
```

Evidence means contract/projection behavior is verified with focused fixtures. It does not
mean a full simulator seed was rerun in this session, nor that a live browser/OSRM network
request completed.

## Handoff flow

```text
POST /api/v1/demo/sessions
→ PUT .../driver
→ POST .../steps (idempotent client_step_id + expected_step_version)
→ canonical trace snapshot + trip/map/routes
→ trace checkpoint bridge (or honest silent)
→ template presentation + immutable lease
→ Web DOM mount
→ POST demo .../advice/.../display (mounted ACK)
→ accepted|dismissed|expanded intent (no trajectory mutation)
```

No solver is called by Next Step. No Agent tool is exposed. The browser does not own trip
state, SOC, payout, route geometry, canonical action, or advice IDs. `ADVICE_V2_ENABLED=0`
and `ADVICE_PRESENTATION_MODE=template` remain safe defaults; demo ACK writes the same
checkpoint event stream without enabling product polling or live LLM.

## Dirty-worktree preservation

Pre-existing unrelated modifications remain unstaged and untouched:

```text
data/mock/realdata-v1/manifest.json
research/audit/2026-07-27-current-state/41-e10-preflight-n30.json
scripts/run_parallel.py
tests/test_advisor_pipeline.py
tests/test_cadence_policy.py
requirements.txt (untracked)
scripts/measure_fleetwide_multi_horizon.py (untracked)
tracking/updates/UPDATE-114-requirements-and-simulator-setup.md (untracked)
```

## Adversarial review / remaining gates

1. The default demo `run_factory` uses a deep-copied observer config: existing S1/S2 trace
   callsites are enabled, adherence is zero, and positioning overrides are off. This is
   designed to create trace artifacts without a demo treatment arm, but a fresh semantic
   comparator is still required before treating it as dynamics-neutral evidence.
2. Session and route caches are in-process. Multi-worker or multi-replica hosting needs a
   shared session/idempotency store before any canary.
3. A real browser review must inspect actor selection, one-transition stepping, route source
   badges, silent/no-button advice, displayed ACK, and MOCK provenance. Flutter/device V-25
   remains open and no `flutter`/`dart` claim is made.
4. OSRM online latency/timeout behavior is covered by provider-failure fixture, not by a live
   network run. The straight-line fallback must remain visible and non-canonical.
5. Live Agent/provider credentials, canary allowlist, budget, kill-switch and production
   rollout are outside this implementation; template-only is the rollback.

## T-039 expansion checkpoint

1. **Schema:** Advice v2 now permits optional `presentation_source`; a future cycle may add a
   closed `demo_step` schema after owner accepts nested response fields.
2. **Optimization:** no objective/cadence change; no solver is added to cursor advancement.
3. **Feature:** same trace can support template and future shadow evaluation; no live output
   reaches the driver in this cycle.

## Owner decisions

- Choose fixed seed/actor for V-25 browser review (implementation default: seed `1000`).
- Decide whether `/app/` is the sole stakeholder demo while `/app/mo-phong/` stays analytical.
- Approve a narrow real-run semantic comparator and browser/OSRM smoke before changing any
  flag or claiming production readiness.
