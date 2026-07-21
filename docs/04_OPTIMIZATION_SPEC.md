> ⚠️ **DEFERRED — 2026-07-20.** Tài liệu thuộc cách tiếp cận cũ (full multi-variable constrained optimization). Scope hiện hành: `CLAUDE.md` + `planning/SCOPE.md`. Chỉ dùng tham khảo (xem `tracking/DEFERRED.md`, mục D-001).

# 04 — Optimization Specification

## 1. Problem class

Đây là **stochastic sequential decision support**: state và forecasts đổi theo thời gian, action hiện tại ảnh hưởng pin/bonus/thời gian/end zone, người dùng có thể không làm theo, và recommendation có network externality. Thiết kế ban đầu là scenario-based Model Predictive Control (MPC) trên rolling horizon; mỗi event/tick giải lại một cửa sổ ngắn rồi chỉ trình bày next best action/plan.

## 2. Notation

- `s_t`: snapshot tại thời điểm `t`.
- `A(s_t)`: candidate plans phù hợp capability.
- `ω ∈ Ω`: scenario demand/traffic/trip/charger/adherence.
- `x_{a,k}`: chọn action/plan `a` ở time bucket `k`.
- `N(a,ω)`: net earnings theo definition version.
- `T`, `E`, `W`: active time, empty km, wait time.
- `L`: late-end/deviation from end zone.
- `F`: recommendation friction/change cost.
- `G`: platform/service/fleet metrics.

## 3. Economic definition

Không dùng một công thức net chung. `NetEarningsDefinition` versioned chỉ rõ ledger components và economic owner. Một dạng tổng quát:

`N = trip_share + eligible_bonus + approved_adjustments - driver_borne_energy - driver_borne_fees - driver_borne_penalties - other_in_scope_costs`.

Opportunity cost của time/empty/wait có thể nằm trong utility nhưng không được trừ lần hai khi report net. Report đồng thời total net và net/hour; optimizer dùng profile-specific utility/minimum goal để tránh ratio gaming.

## 4. Hierarchical objective

### Level 0 — hard feasibility/veto

Safety/legal/policy, battery reserve, action eligibility, required consent/freshness, hard end time nếu user đặt hard, charger compatibility/capacity, Phase 2 zone capacity.

### Level 1 — platform/network guardrails

`G_served ≥ floor`, passenger ETA/cancel non-inferiority, zone imbalance/capacity, charger congestion, contribution-margin floor và fairness exposure bounds. Threshold do business/ops phê duyệt, versioned.

### Level 2 — driver utility

Ví dụ cho mỗi plan:

`U(a)=E[N(a,ω)] - λrisk·CVaRα(loss) - λtime·T - λempty·E - λwait·W - λlate·L - λfriction·F`.

`λ` đến từ mode/profile đã phê duyệt, không tự học vô hạn. Stable/Balanced/Stretch có risk/goal settings khác nhau. Tài xế có hard minimum total goal hoặc reservation-wage threshold khi phù hợp.

### Level 3 — tie-break/preferences

Familiar zone, lower plan churn, explicit preferred break, lower variance. Explicit preference > learned preference; confidence thấp thì giảm personalization.

Giải bằng lexicographic/epsilon-constraint hoặc tuần tự: filter hard → filter platform → Pareto/risk rank driver utility → tie-break preference. Không dùng một weighted sum để safety có thể bị bù bởi tiền.

## 5. Action/decision space

Phase 1 action enum trong master prompt. Plan gồm time buckets với activity `ONLINE_CURRENT_MODE`, `BREAK`, `CHARGE`, `HOMEWARD`, `END`; bonus tier/target là plan parameters. Phase 1 không có order decision/route-to-order.

Phase 2 thêm zone transitions với:

- reachable within horizon;
- travel/time/energy cost;
- opportunity capacity và active reservations;
- predicted realized supply có tính acceptance probability;
- service-level/fairness constraints.

## 6. Constraints

- one activity per bucket; legal transitions/state machine;
- SOC balance và minimum reserve theo scenario quantile;
- charger compatibility, opening/capacity, travel + queue + charge time;
- hard/soft shift end, max online/continuous-driving/rest policy;
- bonus eligibility/tier logic và effective time;
- target/availability and explicit max displacement;
- action allowlist theo market/service/profile;
- fleet capacity, service floor và fairness budget ở Phase 2;
- notification/replan friction budget;
- data freshness/quality/consent prerequisites.

Soft constraints chỉ gồm user preference/business trade-off được phép. Safety/legal không được slack; nếu infeasible, output diagnostic/no recommendation.

## 7. Uncertainty

Forecast output là distribution/quantiles cho demand, trip arrival/duration/fare/destination, travel time, charger wait, energy và driver action adherence. Phase 1 dùng scenario sampling/robust bounds; report P10/P50/P90 và downside risk. Calibration được đo theo segment/time/zone; confidence thấp thu hẹp action set hoặc tăng conservative reserve.

Không giả định recommendation được làm theo. State chỉ thay sau observed action/event. Phase 2 capacity tính expected realized supply và reservation TTL; ignore/accept history giúp estimate response nhưng không mang tính trừng phạt.

## 8. Candidate generation và ranking

1. Luôn tạo baseline `KEEP_CURRENT_PLAN`/do-nothing.
2. Tạo bounded candidates từ templates/capability/policy.
3. Fast feasibility pre-check loại ứng viên rõ ràng sai.
4. Solver đánh giá horizon dưới scenarios.
5. Policy gate kiểm tra lại bằng independent invariants.
6. Loại dominated options; giữ tối đa ba diverse options.
7. Recommended option chỉ khi minimum expected value, confidence, significance/practical delta và notification threshold đạt.

Không ép luôn phải có recommendation. Nếu options gần nhau hoặc data yếu, `recommended_option_id=null` và giữ plan.

## 9. Algorithms by phase

| Phase | Algorithm | Lý do |
| --- | --- | --- |
| 0 | transparent rules/greedy + oracle toy solver | baseline, debug, invariant |
| 1 | CP-SAT/MIP scenario MPC; shortest path/DP cho plan đơn giản | constraints/time buckets minh bạch |
| 2 | min-cost flow/assignment + capacity reservation; coupled with per-driver plans | manage supply externality |
| 3 | contextual bandit cho card timing/ranking có exploration cap | personalization có logged propensity |
| Later | constrained RL/MARL only if qualified | long-horizon/adaptive, nhưng rủi ro cao |

OR-Tools CP-SAT dùng integer values; tiền/time/energy scale thành integer và test overflow/precision. Solver abstraction lưu status `OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN`, time limit, bound/gap và incumbent.

## 10. Reposition/fleet externality

Đơn vị opportunity có `capacity` dựa trên forecast demand, committed/idle supply, uncertainty và platform reserve. Recommendation service phải atomic-reserve token, trừ active exposures dự kiến được chấp nhận và đóng opportunity khi capacity hết. Fleet objective penalizes both under- and over-supply. Fairness kiểm soát exposure/value theo eligible cohorts và không luôn ưu tiên cùng nhóm.

Đánh giá supply-impact trong simulator/replay trước exposure. Driver-level optimization không được tự phát zone recommendation nếu fleet allocator vắng mặt.

## 11. Fallback policies

- Missing/stale noncritical forecast: conservative heuristic + lower confidence.
- Critical safety/policy/SOC missing: fail closed/no recommendation.
- Timeout có feasible: dùng incumbent nếu independent policy gate pass; disclose FEASIBLE.
- Infeasible: minimal conflict set/diagnostic; không relax hard constraints.
- Model drift/calibration fail: disable affected action via flag, revert baseline.

## 12. Verification

- Unit tests cho economics, transitions, constraint compilation.
- Property tests: money conservation, SOC bounds, no overlap, hard end, enum only.
- Differential tests heuristic vs solver trên toy cases; oracle on small instances.
- Golden scenarios và metamorphic tests (giảm SOC không thể làm charge need thấp hơn nếu mọi thứ khác giữ nguyên, trừ policy rõ).
- Performance tests theo candidate/scenario/driver count; time-limit behavior.
- Calibration, stability/churn, sensitivity to weights/scenarios.
- Phase 2 game/supply simulation và fairness/non-inferiority.

## 13. Anti-patterns

- Heatmap demand = earnings map.
- Maximize expected value mà bỏ downside/uncertainty.
- Dùng acceptance rate làm objective duy nhất.
- Đưa mọi constraint vào penalty.
- Train RL on synthetic rồi gọi production policy.
- So sánh solver với “không làm gì” duy nhất; cần heuristic/operations baseline.
- Giải thích bằng feature importance như causal reason khi chỉ là correlation.
