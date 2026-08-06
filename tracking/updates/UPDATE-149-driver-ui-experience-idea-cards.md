# UPDATE-149 — Chuyển AdviceCheckpoint discovery thành 33 UI Idea Cards

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent theo yêu cầu trực tiếp của Khánh
- **Loại:** research / product ideation / docs
- **TODO / User story liên quan:** tiếp nối UPDATE-148; T-039
- **Trạng thái:** `RESEARCH-DONE / IMPLEMENTATION-NOT-STARTED`

## Tóm tắt

Chuyển evidence UPDATE-148 thành 33 trải nghiệm cụ thể cho tài xế. Mỗi Idea Card có driver problem,
raw evidence, derived-state logic, kết luận, UI form, copy tiếng Việt, uniqueness, real-data
feasibility, measured coverage và guard. Báo cáo còn gom thành 16 composite, 8 product clusters,
6 end-to-end storylines và tự chọn top priorities.

Không sửa runtime, solver, policy, cadence, schema, Web hay LLM.

## Chi tiết cập nhật

- Viết 33 Idea Cards; toàn bộ là composite/rolling/journey synthesis, không dùng event-acknowledgment
  để bù số lượng.
- Đo 27 derived-state pattern trên 450 actor-run: semantic plan revisions, plan churn,
  disruption→revision, future-SWAP execution, plan-versus-actual, energy recovery, repeated idle,
  utilization/empty-share phase shift, cancellation/decline clusters và income-source mix.
- Bổ sung MOCK multiday probes: 150 profiles đủ seven-day history; 125 có two-day low-income streak,
  1.041 rebound days, 88 acceptance-risk profiles và 130 acceptance-recovery profiles. Mọi threshold
  là research probe, không phải trigger.
- Trích exact seed-1000 storylines cho actors 35, 70, 37, 1 và 10; thêm một multiday scenario
  dùng machinery thật nhưng ghi rõ chưa chạy/đo.
- Chọn dứt khoát top quick wins, top uniqueness, top real-data portability, top composites và top demos.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/audit/2026-08-05-checkpoint-ui-experience-ideas/ui-experience-idea-cards.md` | tạo | deliverable chính |
| `research/audit/2026-08-05-checkpoint-ui-experience-ideas/analyze_experience_candidates.py` | tạo | read-only episode/window probe |
| `research/audit/2026-08-05-checkpoint-ui-experience-ideas/experience-coverage.json` | tạo | 27 derived-state summaries |
| `research/audit/2026-08-05-checkpoint-ui-experience-ideas/ui-experience-storylines.json` | tạo | exact actors 35/70/37/1/10 |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/extract_deep_storylines.py` | sửa nhỏ | selection note phản ánh actor arguments thay vì hard-code ba actor |
| `tracking/PROJECT-GRAPH.md` | sửa tối thiểu | thêm UPDATE-149 |
| `tracking/TODO.md` | sửa tối thiểu | research handoff, không đổi implementation status |

## Docs đã cập nhật kèm theo

- Report/UPDATE/graph/TODO: có.
- SCOPE/DEFERRED/USER_STORIES/schema: không đổi; chưa có capability được duyệt để implement.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| plan revision phủ 426/450 actor-run | FACT/SIMULATED | `experience-coverage.json` | cao | giảm ưu tiên plan narrative |
| energy recovery phủ 90 actor-run | FACT/SIMULATED | SOC-skip→swap probe 90′ | trung bình | window probe chưa phải causal link |
| idle là observed rest | REJECTED | journey gap is INFERRED | cao | cấm dùng idle như health fact |
| 33 ideas là 33 trigger mới | REJECTED | report phân surface/grouping | cao | tránh biến portfolio thành popup stream |
| daily table shape là live service | REJECTED | manifest MOCK + data catalog | cao | phải thêm authority/freshness contract |

## Kiểm chứng

### Seeds và scenarios

| Command/run | Seeds | Kết quả/artifact | Chưa kiểm chứng |
| --- | --- | --- | --- |
| `analyze_experience_candidates.py` | 1000–1004 | 450 actor-run, 27 derived states | threshold precision/human usefulness |
| `extract_deep_storylines.py` | 1000; actors 35/70/37/1/10 | exact checkpoint/event/journey JSON | visual UI presentation |
| MOCK parquet scan | 90-day/150 profiles | baseline/streak/rebound evidence | live service/production representativeness |

Không chạy full backend/simulator/solver suite vì không đổi runtime. Gate cuối gồm py_compile,
deterministic artifact rerun/cmp, structural validation 33×11 fields, JSON validation và
`git diff --check`.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch/artifact:** text-only research report; chưa sửa UI.
- **Seed/scenario:** exact story artifact seed 1000.
- **Verdict:** human visual review chỉ cần khi các selected ideas được thiết kế UI/implemented.

## Adversarial self-review / flaws found

1. Probe windows/thresholds được chọn để tìm opportunity, không đo precision; report không dùng
   chúng làm production rules.
2. Semantic revisions có thể gồm natural rolling-horizon changes; IC-12 yêu cầu stability/material
   semantics trước khi coi là churn driver-facing.
3. Matching action trong validity là observed consistency, không adherence hoặc causality.
4. Exact demo actors được chọn từ measured artifacts nên không out-of-sample.
5. MOCK multiday có thể quá đều/khác production; feasibility chỉ được claim ở schema shape level.
6. IC-32/33 có machinery nhưng zero current Web-demo coverage; giữ SIMULATOR-SHOWCASE.
7. Report dài là product catalog, không phải đề nghị render đồng thời tất cả concepts.

## Expansion checkpoint (T-039)

1. **Schema:** nếu implement, cần derived-state/view contract trước checkpoint producer; không thêm
   33 topic. Card composite nên reference component signals + evidence window + confidence.
2. **Bài toán tối ưu:** không solver mới trong phase đầu. Candidate grouping/primary arbitration là
   deterministic policy; S4 giữ ownership positioning.
3. **Tính năng:** quick wins được chọn là journey recap, plan-change explanation, income-source
   breakdown, shift compass và energy plan strip.

## Follow-up / defer phát sinh

- Implementation chưa bắt đầu. Cycle kế tiếp nên thiết kế contract cho đúng **một** vertical slice,
  ưu tiên IC-11 hoặc IC-29; không triển khai 33 cards cùng lúc.
- 30-seed + human usefulness/wording review trước khi biến probe thành trigger.
- V-25 và các gate pre-existing không được UPDATE này đóng.
