# 08 — Decisions, Assumptions and Open Questions

## 1. Locked design decisions (v0.1)

- `DEC-001`: Product là decision-support/advisory layer, không phải dispatch/agent tự hành.
- `DEC-002`: MVP action scope = shift/goal/bonus/charge/break/homeward/post-shift; no order/reposition.
- `DEC-003`: LLM outside numeric/policy control loop; structured read-only tools + schema validation.
- `DEC-004`: synthetic-first for contracts/testing, not model/uplift proof.
- `DEC-005`: hierarchical constrained objective; safety/legal/platform guardrails trước driver utility.
- `DEC-006`: scenario MPC + baseline solver trước RL.
- `DEC-007`: modular monolith + worker cho team hai người.
- `DEC-008`: explicit preferences win; blurred home/end zone; privacy-by-design.
- `DEC-009`: Zone guidance requires fleet capacity/fairness/service-level allocator.
- `DEC-010`: causal, interference-aware experiments; no naive before/after.

## 2. Reversible working assumptions

- `ASM-001`: Official schemas unavailable; canonical contract can evolve versioned.
- `ASM-002`: Compensation differs by engagement model/market/service and is policy data.
- `ASM-003`: App can receive recommendation cards/timeline and optional chat/voice in future.
- `ASM-004`: Phase 1 can access aggregated completed-trip/session/earnings/vehicle/bonus/charger state, not live order choice.
- `ASM-005`: Platform owners can later supply service-level floors and capacity interface.
- `ASM-006`: Exact home address unnecessary; zone/geofence đủ cho initial homeward utility.
- `ASM-007`: Python stack acceptable absent conflicting existing repo standards.

## 3. Questions for GSM/project owner, with default until answered

| Priority | Question | Why it changes design | Safe default |
| --- | --- | --- | --- |
| P0 | Tài xế Car/Bike/Premium là employee, partner hay mixed theo market? | economics, working policy, UX | enum `unknown`; no universal net formula |
| P0 | Chính xác thành phần “thu nhập ròng” và ai chịu điện/thuê/commission/phạt? | objective/ROI correctness | ledger components versioned; unknown excluded/disclosed |
| P0 | Dispatch boundary/API/data owner là ai; action nào bị cấm? | avoid conflict | no order/reposition advice |
| P0 | Policy hiện hành về giờ lái/nghỉ/sạc/depot/service là gì? | hard constraints | policy service required; fail closed when unknown |
| P0 | Có được xử lý location/history/home zone cho personalization không? | privacy/architecture | opt-in blurred zone only; no exact home |
| P0 | Dữ liệu nào có real-time, SLA/freshness và historical depth? | viable features/forecast | fixture interface; disable unavailable action |
| P1 | Bonus definitions có machine-readable/effective-dated không? | bonus navigator | demo mock only; no live advice |
| P1 | Charger availability/queue/reservation có API không? | charge precision | conservative no exact wait/station claim |
| P1 | Platform guardrail/margin/served-demand metrics là gì? | objective hierarchy | Phase 1 no supply-shifting action |
| P1 | Driver app interaction restrictions while moving? | UX/safety | voice/passive only; interaction when stopped |
| P1 | Eligible pilot market/cohort và support/oncall owner? | experiment/rollout | no live pilot |
| P2 | Có thể issue capacity token cho zone opportunities không? | Phase 2 feasibility | do not build reposition exposure |
| P2 | Existing feature/model/infra standards? | stack/reuse | modular adapters; audit before scaffold |

## 4. Questions to research with drivers

- Hiện họ định nghĩa ngày “tốt” bằng total, per-hour, stability hay goal?
- Ba quyết định gây tiếc nhất; họ dùng nhóm chat/heatmap/kinh nghiệm nào?
- Chi phí nào họ thực sự cảm nhận/chịu; có tự tính empty km/wait/charge không?
- Khi nào bonus “không đáng”; điều kiện nào khó hiểu?
- Charge/break/homeward constraints khác giữa Bike/Car/Premium/employee/partner?
- Recommendation nào hữu ích, phiền hoặc bị xem là kiểm soát?
- Họ cần action ngắn, range, comparison hay explanation tới mức nào?
- Vì sao họ ignore; trust thay đổi sau recommendation sai thế nào?

Method: 10–15 interviews đa nhóm + shadowing ca + 5–7 ngày diary + ops workshop + behavioral data. Sample phải cover market/service/experience/schedule, không chỉ top earners/active volunteers.

## 5. Self-questions and answers

**Nếu hệ thống không chọn cuốc, giá trị có đủ không?** Có hypothesis rõ ở shift/bonus/charge/break/homeward và post-shift; đây còn là cách chứng minh trust/data/economics trước khi xin quyền sâu hơn. Nếu pilot không tạo material value, pivot có bằng chứng thay vì chạm dispatch sớm.

**Nên trả một action hay ba plan?** Trước ca: tối đa ba plan đa dạng. Trong ca: một recommended action + baseline/alternative mở khi cần; tránh overload.

**Nên optimize doanh thu hay lợi nhuận?** Driver utility dùng net theo economic owner; nhưng luôn report gross/reconciliation để giải thích. Platform contribution là guardrail/benefit riêng, không lẫn driver net.

**Có nên dùng penalty/cancellation rate?** Chỉ khi approved policy và causal relevance rõ. Không khuyên cách né phạt; penalty đã finalized có thể là ledger component, predicted penalty cần conservative/disclosed.

**Có nên học từ tài xế thu nhập cao?** Có thể dùng hypothesis/behavioral features nhưng dễ survivorship/selection bias và leak privileged conditions. So sánh với self/comparable contexts, đánh giá causal trước coaching.

**Traffic data dùng thế nào?** Travel-time distributions, charger/zone reachability, opportunity cost và uncertainty; không chỉ shortest path. External provider chưa chọn; adapter/contract trước.

**Nếu data official khác mock?** Adapter mapping + schema version + dual-run; domain contract chỉ đổi khi semantics thật sự khác, có migration/compatibility.

**Nếu platform profit và driver income mâu thuẫn?** Product owner đặt service/margin floors; optimizer tối ưu driver trong feasible region. Nếu không có feasible compromise, no recommendation/escalate objective decision, không giấu trong weight.

**Nếu tất cả cùng làm theo?** Phase 1 tránh supply-shifting; Phase 2 centralized capacity/reservations + adherence uncertainty + fleet simulation.

**Nếu LLM không cần thiết?** Không dùng cho card/timeline tính toán. Chỉ bật explanation/constraint/policy QA khi measured UX value vượt cost/latency/risk.

## 6. Blockers before live

1. Approved net earnings definition và policy bundles.
2. Data inventory/owners/SLA + privacy purpose/consent/retention.
3. Dispatch/fleet boundary sign-off.
4. Safety/legal/compliance review theo current rules; không dùng legal assumptions trong docs làm production rules.
5. Official source adapters + shadow data quality/calibration.
6. Experiment owner/design, operational support, kill switch/rollback.
7. Platform/customer/fairness guardrail thresholds.

Không blocker cho synthetic vertical slice; là blocker cho production claims/exposure.
