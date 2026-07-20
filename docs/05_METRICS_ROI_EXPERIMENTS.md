> ⚠️ **DEFERRED — 2026-07-20.** Tài liệu thuộc cách tiếp cận cũ (full multi-variable constrained optimization). Scope hiện hành: `CLAUDE.md` + `planning/SCOPE.md`. Chỉ dùng tham khảo (xem `tracking/DEFERRED.md`, mục D-001).

# 05 — Metrics, ROI and Experiments

## 1. Metric contract

Mỗi metric có definition/version, numerator/denominator, eligible population, time window, data source, owner, freshness, exclusions và direction. Không đổi definition giữa experiment. Monetary metrics phải reconcile với ledger; provisional tách finalized.

## 2. Metric tree

### Driver value

- North star: causal lift `net_earnings_per_eligible_active_hour`.
- Companion: total net earnings/shift/week, active hours, goal attainment.
- Efficiency: productive-time ratio, empty-km ratio, wait, pickup/reposition/charge time.
- Risk: P10 outcome, CVaR/downside, variance, plan failure.
- Personal constraints: on-time end, end-zone distance, charge/break compliance.
- Trust/UX: qualified acceptance, ignore reason, opt-out, explanation usefulness, recommendation fatigue.

### Platform/customer guardrails

- contribution margin/eligible hour or trip;
- fulfilled/served demand, passenger ETA/wait, cancel/abandonment;
- zone supply-demand mismatch, fleet utilization, empty km;
- charger congestion, depot/ops impact;
- complaint/support rate và driver retention (longer horizon).

### Safety, fairness, privacy

- hard-policy violation = zero tolerance release gate;
- required-break/continuous-driving policy outcomes;
- exposure, acceptance, predicted/realized value by eligible cohort/profile/zone/time;
- concentration/Gini or approved fairness metric; worst-cohort non-inferiority;
- consent/retention/deletion failures, PII/log incident.

### Model/system

- forecast WAPE/MAE where appropriate; quantile loss, interval coverage, calibration.
- optimizer feasibility/status/gap/regret vs oracle on small cases; compute latency.
- predicted vs realized option delta; policy veto/fallback/no-recommendation rate.
- API p50/p95/p99, error, freshness, cost per recommendation/explanation.
- schema/model/policy drift và recommendation churn.

## 3. What success is not

- Acceptance/adoption cao nhưng earnings/platform không tăng.
- Before/after tăng trong mùa cao điểm.
- Net/hour tăng do tài xế chỉ chạy giờ tốt nhưng total income/availability bị tác động không chấp nhận.
- Synthetic simulation uplift.
- Forecast accuracy tốt nhưng recommendation không tạo incremental value.

## 4. Evaluation ladder

1. **Unit/oracle:** correctness, invariants, toy optimality.
2. **Synthetic scenarios:** failure coverage, UX/contract; không claim uplift.
3. **Historical replay:** calibration, feasibility, policy comparison; xử lý selection/confounding.
4. **Simulation/digital twin:** fleet externality, capacity/fairness, sensitivity; validate simulator separately.
5. **Shadow:** live freshness/latency/forecast residual, no driver exposure.
6. **Limited pilot:** feature flags, operational owner, randomized/causal design, rollback.
7. **Canary/scale:** sequential monitoring, non-inferiority, cost/SLO/drift.

## 5. Experiment design

### Phase 1 individual decisions

Shift/charge/bonus/homeward ít gây supply interference hơn nhưng vẫn có time/zone selection. Có thể randomize eligible driver-day hoặc recommendation eligibility, stratify theo market/profile/history; dùng intent-to-treat là chính, treatment-on-treated là secondary với assumptions.

### Phase 2 repositioning

Driver-level A/B vi phạm no-interference vì treatment đổi supply/demand của control. Dùng cluster randomization hoặc switchback theo zone×time/market period; thiết kế buffer/spillover measurement, pre-register primary/guardrails và dùng cluster-robust inference. Không vừa thay dispatch/pricing vừa test nếu không factorial/control được.

### Common controls

- eligibility và exclusion frozen; sample-size/power/MDE dựa baseline variance.
- novelty/ramp; weekday/weather/event strata.
- logged exposure/propensity/expiry; distinguish not-seen/seen/accepted.
- SRM, instrumentation, contamination và attrition checks.
- stop rules cho safety/platform harm; correction cho repeated peeking nếu dùng fixed horizon.

## 6. Offline policy evaluation caveat

Logged data đến từ policy cũ và chỉ quan sát outcome của action đã chọn; direct replay không biết counterfactual. Với bandit/ranking cần logged propensity, overlap/positivity và IPS/DR estimator được kiểm chứng. Nếu thiếu overlap, không ngoại suy; chuyển shadow/pilot có giới hạn.

## 7. ROI model

Không có số chính thức nên không điền một ROI giả. Workbook/model phải có scenario và owner cho từng input.

### Driver economic benefit

`B_driver = active_drivers × eligibility_rate × adoption_rate × eligible_hours × baseline_net_per_hour × causal_relative_lift`

Tách redistribution từ new value: zone guidance có thể chuyển thu nhập giữa tài xế; fleet total/dispersion phải được đo.

### Platform benefit

`B_platform = incremental_contribution_margin + retention_value + served_demand_value + support/ops_saving - cannibalization - incentive_increment`

Không tự coi toàn bộ driver benefit là platform revenue.

### Total cost

`C = discovery + build + integration + data/license + cloud + model/LLM + maps/traffic + security/privacy/compliance + experiments + monitoring/oncall + support/training + opportunity cost`

### ROI and break-even

`ROI = (approved_benefit - C) / C`  
`Payback months = cumulative one-time cost / monthly net benefit` nếu monthly benefit ổn định; nếu không dùng cash-flow by month/NPV.

Chạy best/realistic/worst với confidence range; sensitivity tornado cho adoption, causal lift, eligible hours, platform margin, inference/map cost và support load. Mock data chỉ test calculator.

## 8. Decision gates

- Discovery → prototype: metric definitions/data availability/policy owners đủ.
- Prototype → shadow: all invariants pass; official adapters/privacy/security review.
- Shadow → pilot: calibration/freshness/latency và operational support đạt threshold đã duyệt.
- Pilot → scale: primary metric significant/practically valuable; platform/safety/fairness non-inferior; unit economics positive realistic case.
- Kill/pivot: persistent guardrail harm, no causal driver value, low trust do calibration, data cost vượt benefit hoặc cần can thiệp dispatch ngoài charter.

## 9. Example hypothesis — not commitment

Sau khi có baseline, Product có thể pre-register một target như “tăng tối thiểu X% net earnings/hour với total net không giảm quá Y, passenger ETA/cancel và platform contribution margin đạt non-inferiority, safety violations bằng 0”. `X/Y` phải đến từ power analysis, business materiality và dữ liệu thật; không lấy số demo làm target.
