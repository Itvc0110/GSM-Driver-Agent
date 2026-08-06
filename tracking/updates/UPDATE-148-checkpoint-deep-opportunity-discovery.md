# UPDATE-148 — Deep opportunity discovery cho AdviceCheckpoint portfolio

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent theo yêu cầu trực tiếp của Khánh
- **Loại:** research / docs / data-analysis
- **TODO / User story liên quan:** AdviceCheckpoint coverage research; kế thừa UPDATE-146/138; T-039
- **Trạng thái:** `RESEARCH-DONE / OWNER-DECISIONS-PENDING`

## Tóm tắt

Mở rộng discovery sau UPDATE-147 từ inventory checkpoint sang toàn bộ không gian raw signal,
derived state và portfolio UI. Kết quả: simulator không thiếu event nhưng thiếu projection/producer
cho journey-level value; phương án phù hợp là 1 brief + 2–4 actionable nudge + 1–3
passive/composite + 1 recap, không mass-unsuppress ONLINE và không tăng cadence để đạt quota.

Lượt này không sửa runtime, solver, policy, cadence, schema, Web hay LLM. Mọi phép đo dùng current
worktree sau foundation fixes, Web-demo factory và corpus 90 ngày `MOCK`.

## Chi tiết cập nhật

### Evidence chính

- 5 seed 1000–1004, 450 actor-run: 40.009 event, 18.699 segment, 4.705 checkpoint record;
  462 READY = 1,027/driver-run; p50/p75/p90/max READY = 1/2/2/4.
- 4.126 S2 ONLINE suppressed + 116 expired: volume audit lớn nhưng không phải 4.242 touchpoint.
- Coverage probe: brief/recap inputs 450/450; future-SWAP 387; SOC-skip 95; swap friction 110;
  inferred idle ≥30′ 379; empty share ≥40% 361; cancel-after-accept 169; mission complete 282;
  newbie event 76 actor-run.
- `DriverJourney`, `DriverMemory`, event detail, L1R daily history và checkpoint revision là các
  substrate giá trị cao chưa có consumer driver-facing đầy đủ.
- Corpus MOCK 90 ngày chứng minh rolling baseline có thể tính, đồng thời probe ±20% bắt cả
  150/150 driver ít nhất một lần — threshold này quá nhạy và không được dùng làm production rule.

### Thiết kế được khuyến nghị

1. Project derived state có provenance/freshness/confidence trước khi thêm producer.
2. Ưu tiên brief, passive current-plan, mission completion và recap để tăng value mà không tăng
   interruption.
3. Sau đó thêm energy-continuity, plan-revision/plan-versus-actual và progress composites.
4. Baseline cá nhân/income pace chỉ sau khi có minimum-history, comparable-day và intraday ledger.
5. Positioning/environment giữ `SIMULATOR-ONLY` tới khi có live capacity/governance/data contract.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/discovery-report.md` | sửa | thêm Phase II deep discovery sau UPDATE-147 |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/analyze_deep_opportunities.py` | tạo | observer 5 seed + reader corpus MOCK 90 ngày; không đổi runtime/RNG |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/extract_deep_storylines.py` | tạo | trích exact trajectory seed 1000 actors 35/70/37 |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/deep-opportunity-evidence.json` | tạo | aggregate evidence + probe warnings |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/deep-opportunity-by-actor.csv` | tạo | 450 actor-run |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/deep-event-inventory.csv` | tạo | event count/detail-key inventory |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/deep-demo-storylines.json` | tạo | continuous story evidence |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/raw-signal-coverage.csv` | tạo | 35 signal group |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/opportunity-catalog.csv` | tạo | 33 candidate capability |
| `tracking/PROJECT-GRAPH.md` | sửa tối thiểu | thêm UPDATE-148 research node |
| `tracking/TODO.md` | sửa tối thiểu | ghi research handoff/owner decisions, không đổi runtime status |

## Docs đã cập nhật kèm theo

- Discovery report: có.
- UPDATE/PROJECT-GRAPH/TODO: có.
- SCOPE/DEFERRED/USER_STORIES: không đổi vì chưa duyệt capability hoặc runtime scope mới.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| 462 READY/450 actor-run | FACT / SIMULATED | `deep-opportunity-evidence.json`; `_default_run` seeds 1000–1004 | cao | sai baseline ưu tiên/coverage |
| idle block là trạng thái quan sát | INFERENCE, không phải FACT | `journey.py:_timeline_of`; gaps giữa segments | trung bình | không được dùng nudge nếu chưa có confidence contract |
| daily schemas có thể map product | REAL-DATA-READY về shape; MOCK về values | `from_l1r.py`, mock manifest/data catalog | trung bình | cần contract/service/freshness mới |
| ±20% rolling median là trigger tốt | REJECTED ASSUMPTION | bắt 150/150 driver trong corpus MOCK | cao | ship threshold này sẽ spam |
| execution gần checkpoint là causal | REJECTED | links `coincident`, confidence 0,6 | cao | tránh claim uplift sai |
| 5–10 touchpoint nên gồm non-popup | IDEA / OWNER DECISION | portfolio §15 report | chưa chốt | định nghĩa quota/budget thay đổi |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Scenario | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `analyze_deep_opportunities.py --seeds ...` | 1000–1004 | Web-demo `_default_run` | 450 actor-run; artifacts JSON/CSV | chưa 30 seed; không human usefulness |
| `extract_deep_storylines.py --seed 1000 --actors 35 70 37` | 1000 | exact current trajectory | 3 storylines, no fixture | actor selection không out-of-sample |
| đọc parquet 90 ngày | corpus manifest MOCK | 150 profiles/90 days | rolling/history/mission/hex/trip counts | không chứng minh production live contract |

Không chạy full backend/simulator/solver suite vì lượt này không đổi runtime. Verification cuối
chỉ compile script, deterministic rerun/cmp, validate JSON/CSV và `git diff --check`.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** report/CSV/JSON, không đổi UI.
- **Seed / scenario đã xem:** artifact seed 1000 actors 35/70/37; không browser visual.
- **Người review + verdict:** chưa cần visual gate cho research-only; V-25 pre-existing vẫn mở.

## Adversarial self-review / flaws found

1. Coverage probe có thể trông rất cao vì thresholds cố ý rộng; report ghi rõ không phải rule.
2. Idle/empty là projection/inference; dropoff state boundary UPDATE-147 còn follow-up nên không
   đủ căn cứ cho producer actionable.
3. 90-day values là MOCK; schema/deriver không đồng nghĩa API/live service tồn tại.
4. Story actors chọn sau khi xem CSV, thích hợp demo discovery nhưng không đo effect tổng quát.
5. Không có future leak trong script: day baseline chỉ dùng 7 quan sát trước; tuy nhiên chưa
   seasonality-match weekday/shift.
6. Không có CRN comparison/treatment claim trong lượt này; không nói advice gây outcome.
7. Current worktree có foundation diff chưa commit; evidence phản ánh worktree sau UPDATE-147,
   không chỉ HEAD. Report công khai điều này.

## Expansion checkpoint (T-039)

1. **Schema:** đề xuất entity/view `derived_signal` hoặc `driver_journey_view` có
   `signal_id`, `driver_id`, `window`, `observed_or_inferred`, `source_refs`, `freshness`,
   `confidence`, `material_revision`; thêm surface passive/composite chỉ sau owner approval.
2. **Bài toán tối ưu:** chưa cần solver mới. Residual trước mắt là deterministic arbitration/
   grouping giữa candidates và plan-versus-actual projection. Capacity positioning đã có S4,
   không tạo solver thay thế thiếu anti-herding data.
3. **Tính năng:** brief, current-plan strip, mission completion passive và recap khả thi với
   wiring nhỏ; energy/plan composites khả thi sau derived-state contract.

## Follow-up / defer phát sinh

- Owner chốt định nghĩa 5–10 touchpoint và budget proactive/non-proactive.
- Owner chọn P0 slice và taxonomy/surface/schema policy.
- Cycle riêng xử lý dropoff/activity boundary trước idle/efficiency producer.
- 30-seed calibration + human usefulness review trước mọi threshold/cadence proposal.
- Trusted contracts cho SOC, intraday ledger, activity, station và policy trước promotion live.
- Q-13, V-21, V-25 tiếp tục mở; UPDATE này không đóng.
