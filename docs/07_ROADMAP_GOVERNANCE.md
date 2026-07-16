# 07 — Roadmap and Governance

## 1. Phase roadmap

### PHASE-000 — Discovery and definitions

Deliver: driver/ops interviews, journey/shadowing plan, dispatch boundary, economics/metric definitions, data/policy ownership, repo audit, risk register. Exit: Product/Ops/Data/Legal owners xác nhận MVP scope và unknowns; không cần live schema hoàn chỉnh.

### PHASE-001 — Synthetic vertical slice

Deliver: contracts, deterministic scenarios, state→forecast fixture→optimizer→policy→recommendation API→template explanation, trace/tests. Exit: acceptance criteria PRD pass; no order/reposition action; artifacts reproducible.

### PHASE-002 — Safe MVP domains

Deliver: shift planner, bonus navigator, charge/break, homeward, post-shift, what-if; UX prototype và offline evaluation. Exit: product usability + policy/economic correctness trên fixtures/replay; synthetic label.

### PHASE-003 — Official adapters and shadow

Deliver: data mappings, data quality/freshness, privacy/security impact review, forecast baseline/calibration, shadow dashboards. Exit: source owners/SLA, no mock leak, policy bundle approved, shadow gates pass.

### PHASE-004 — Pilot safe MVP

Deliver: feature flags, limited cohort, causal experiment, support/runbook, ROI model populated bằng baseline. Exit: driver primary metric material, guardrails non-inferior, zero hard-policy breach, realistic unit economics positive hoặc decision pivot.

### PHASE-005 — Fleet-aware opportunity

Deliver: capacity allocator/reservations, supply-impact simulator, fairness, zone stay/reposition, cluster/switchback pilot. Exit: network-level benefit and no oversupply/service harm.

### PHASE-006 — Adaptive personalization

Deliver: calibrated adherence/trust, card timing/ranking bandit, exploration caps, logged propensities/off-policy eval. Exit: incremental lift vs deterministic baseline và fairness/privacy pass.

## 2. PHASE protocol

Tên: `PHASE-###-slug.md`. Một phase có owner, status, problem/outcome, facts/assumptions, in/out, dependencies, contracts/data, design/ADR, acceptance/test, metrics/guardrails, rollout/rollback và decision log. Không viết “build optimizer” như một phase không đo được.

Status: `DRAFT → APPROVED → IN_PROGRESS → VALIDATING → DONE | PAUSED | ABORTED`. Scope material change phải update phase/ADR trước code. Exit chưa đạt thì không đánh DONE.

## 3. FIX protocol

Tên: `FIX-###-slug.md`. Bắt buộc reproduction, impact, root cause (không chỉ symptom), containment, solution, regression test, data/model/policy backfill nếu có, deployment/rollback và prevention. Incident privacy/safety/platform phải follow incident process ngoài FIX.

## 4. MEMORY protocol

`MEMORY.md` là handoff ngắn, không phải log toàn bộ. Cập nhật sau mỗi meaningful change:

- current phase/status và last verified commit/artifact;
- decisions/assumptions đang active;
- contracts/model/policy/data versions;
- tests/evidence đã chạy;
- known issues/blockers/next safe step;
- files/modules đang được mỗi developer sở hữu.

Không ghi secrets/PII/raw location. Khi quyết định cần bối cảnh dài, tạo ADR rồi MEMORY link.

## 5. ADR requirements

Cần ADR cho: dispatch boundary, net earnings definition, optimizer/solver class, fleet coupling, policy hierarchy, personalization/consent, data retention, service split, experiment design và bất kỳ schema breaking change. ADR có context/options/decision/consequences/reversal.

## 6. Change taxonomy

| Change | Required artifacts |
| --- | --- |
| Feature trong scope | PHASE update + tests + MEMORY |
| Bug | FIX + regression + MEMORY |
| Hard-to-reverse architecture/policy | ADR + PHASE/FIX |
| Contract breaking | version bump + migration + compatibility + consumer approval |
| Model/weight/policy config | eval card + shadow/canary + approval + rollback |
| Live data purpose/PII | privacy/legal review + data contract/retention update |

## 7. Risk register

| Risk | Impact | Mitigation/early signal |
| --- | --- | --- |
| Conflict with dispatch | platform/customer harm | MVP boundary, action enum denylist, owner review |
| Mass herding/oversupply | earnings/service fall | Phase 2 capacity reservation, fleet sim, cluster tests |
| Wrong net definition | false advice/ROI | versioned ledger reconciliation, economic owner |
| Mock mistaken as live | trust/decision harm | data-mode isolation, label, release gate |
| Forecast miscalibration | bad recommendations | intervals/calibration, minimum-value gate, fallback |
| Incentive gaming | policy/financial loss | eligibility source of truth, abuse review, no loophole advice |
| Overwork/fatigue | safety/legal | hard policy gate, break planner, no revenue override |
| Privacy/home inference | legal/trust | blurred zones, consent, minimization, retention |
| Fairness disparity | driver harm | eligible-cohort metrics, exposure budget, worst-cohort gate |
| LLM hallucination | misleading output | structured tools/schema/numeric validator/template fallback |
| Premature infra/RL | delivery delay | modular monolith, baseline-first exit gates |
| Recommendation fatigue | opt-out/trust loss | friction budget, cooldown, high-value threshold |
| Causal misread | bad investment decision | pre-registered experiments, interference-aware design |

## 8. Governance roles to assign

- Product owner: objective/scope/UX/metrics.
- Dispatch/Fleet owner: platform floors/capacity/integration boundary.
- Driver Operations: workflows/policies/support.
- Finance/Compensation: net earnings/bonus/cost ownership.
- Data owners/stewards: sources/SLA/quality.
- Legal/Privacy/Safety: effective policies/consent/retention.
- Engineering/ML/OR owners: implementation/evaluation/oncall.
- Experiment approver: causal design/ramp/stop rules.

Một người có thể giữ nhiều vai trong prototype, nhưng approval domain không được ẩn trong model code.

## 9. Upgrade and rollback

Mỗi release bundle pin code, schema, model, policy, solver config, prompt/template. Upgrade qua offline → shadow → canary; compare quality, latency, cost, output schema và guardrails. Rollback ưu tiên feature/config/model pointer; DB migration phải backward-compatible hoặc có roll-forward plan. Không deploy Friday-style big bang cho model/prompt/contract cùng lúc mà không tách impact.
