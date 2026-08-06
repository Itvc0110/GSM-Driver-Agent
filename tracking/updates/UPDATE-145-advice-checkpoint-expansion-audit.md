# UPDATE-145 — AdviceCheckpoint expansion coverage audit (read-only)

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Loại:** research / evidence-only
- **Trạng thái:** `DONE-CODE` cho artifact phân tích; **không** thay đổi runtime, solver, policy, cadence, UI, flag hoặc producer
- **TODO / User story liên quan:** mở thiết kế coverage AdviceCheckpoint; chưa claim implementation/production-ready

## Tóm tắt

Đã audit cách mở rộng từ baseline AdviceCheckpoint 5 seed và chạy dry-run candidate rules trên cùng `app.services.demo_session._default_run`. Kết luận chính: không bật 450 `ONLINE` suppressed; nên bổ sung pre-shift brief, S2 future-SWAP material advice, income/plan insights và post-shift recap theo surface khác nhau, sau khi sửa snapshot boundary `dropoff` và bổ sung trace fields cần thiết.

## Chi tiết cập nhật

- Baseline: 864 checkpoint trên 450 driver-run; 413 READY, 450 SUPPRESSED (đều `shift_timing/ONLINE`), 1 EXPIRED; 0 QUEUED/SUPERSEDED/recap trong sample.
- Dry-run candidate: pre-shift 450, bonus 198, SWAP_SOON 381, SWAP_NOW 162, REST 54, income pace proxy 284 raw/157 giữ sau safety proxy, plan deviation proxy 61, long-idle proxy 880 raw/36 giữ, empty-efficiency proxy 279 raw/156 giữ, recap 450.
- Gói Balanced giữ sau safety/cooldown cho median 5 và mean khoảng 4,60 touchpoint/driver-run; đây là estimate exploratory, chưa chứng minh mean 5–10 cho ca production.
- Phát hiện boundary cần xử lý trước producer mới: `src/gsm_sim/world.py:_serve_trip` gọi `log("dropoff")` sau payout/location/order mutation nhưng trước state chuyển về `IDLE`; trace `dropoff` còn `on_trip`. Không dùng proxy idle/efficiency như production evidence trước khi có regression.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `research/audit/2026-08-05-advice-expansion/advice-expansion-audit.md` | tạo | Báo cáo catalog, coverage, cadence proposal, MVP và open decisions |
| `research/audit/2026-08-05-advice-expansion/analyze_advice_expansion.py` | tạo | Offline analysis harness; không mutate simulator/policy/RNG |
| `research/audit/2026-08-05-advice-expansion/advice-expansion-summary.json` | tạo | Baseline + candidate instances/frequency |
| `research/audit/2026-08-05-advice-expansion/candidate-frequency.csv` | tạo | Tần suất raw/giữ/coverage/safety/cooldown/overlap |
| `research/audit/2026-08-05-advice-expansion/candidate-by-actor.csv` | tạo | Join theo run/actor, existing checkpoint state |
| Runtime/source files | không đổi | Không bật checkpoint mới, không sửa cadence, không gọi external API/LLM |

## Docs đã cập nhật kèm theo

`SCOPE`, `TODO`, `DEFERRED`, `PROJECT-GRAPH` và runtime tracking claims **không đổi**; artifact này chỉ mở evidence/design follow-up, không tự đóng V-21/Q-13/V-25.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| 864/413/450/1 baseline | `FACT` | RunResult 5 seed, summary JSON, prior inventory | Cao trong synthetic run | Không đại diện production |
| ONLINE là maintenance silent | `OBSERVED-CODE` | `checkpoint.py:221,286-287` | Cao | Unsuppress hàng loạt sẽ spam |
| SWAP_SOON = future SWAP trong ≤2 bucket | `PROXY` | S2 `future_plan` trong artifacts | Trung bình | Cần owner chốt material window |
| Income pace ratio 0.80/1.20 | `ASSUMPTION` | Dry-run control chỉ để ước lượng | Thấp | Không được đưa vào policy trực tiếp |
| Long-idle gap ≥30 phút | `ASSUMPTION` + `PROXY` | Event gaps; trace thiếu `idle_streak_min` | Thấp | Có thể nhầm rest/route/ON_TRIP |
| Empty share ≥0.40 | `ASSUMPTION` + `PROXY` | Segment durations | Thấp–trung bình | Không phải evidence lợi ích |
| `dropoff` state boundary | `BUG/RISK` | `world.py:709-729`, trace seed 1000 | Cao | Sai safety/state khi tạo producer |
| 5–10 touchpoint không phải 5–10 popup | `OPEN DECISION` | Product framing trong yêu cầu | Chưa chốt | Ảnh hưởng budget/UX metric |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Scenario | Kết quả | Chưa kiểm chứng |
|---|---|---|---|---|
| `PYTHONPATH=src:ui/backend .venv/bin/python research/audit/2026-08-05-advice-expansion/analyze_advice_expansion.py --seeds 1000 1001 1002 1003 1004` | 1000–1004 | Web demo cached run factory | exit 0; 450 driver-run, 864 checkpoint, 413 READY | 30-seed distribution, real data |
| `PYTHONPATH=src:ui/backend .venv/bin/python -m py_compile research/audit/2026-08-05-advice-expansion/analyze_advice_expansion.py` | — | syntax | pass | runtime producer tests |
| `git diff --check` | — | worktree | pass | full backend/sim/solver suite |

Không chạy full backend/simulator/solver suite theo scope audit. Không chạy browser/visual; visual status bên dưới là `NOT_APPLICABLE`.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** không có UI/runtime thay đổi; chỉ đọc và xuất CSV/JSON/Markdown
- **Seed / scenario đã xem:** không mở browser
- **Người review + verdict:** chưa có human visual verdict
- **Lý do:** docs/data-only audit, không thay đổi visual encoding hoặc cadence runtime

## Adversarial self-review / flaws found

1. Không dùng `checkpoint_id` đơn độc; candidate/baseline join theo `run_id + actor_id` và checkpoint event theo run.
2. Không coi `accepted`, `displayed` hoặc execution link `coincident` là adherence/causal uplift.
3. Không coi raw candidate là lời khuyên; bảng tách raw, kept, safety/cooldown và overlap existing.
4. Threshold income/idle/efficiency đều được đánh dấu proposal; không dùng để sửa policy.
5. `dropoff` snapshot state phát hiện là blocker; mọi kết luận idle/efficiency cần lặp lại sau boundary fix.
6. 5 seed là exploratory; coverage claim cần 30 seed và sensitivity trước khi owner chốt cadence.

## Expansion checkpoint (T-039)

1. **Schema:** chưa sửa. Đề xuất owner duyệt fields `idle_streak_min`, plan revision/as-of và surface `brief|passive|recap` trong cycle riêng.
2. **Bài toán tối ưu:** chưa thêm solver. Income pace/plan deviation là analytics/producer trước, không tự mở solver mới.
3. **Tính năng:** có thể mở pre-shift brief, SWAP_SOON, recap và template catalog; chưa triển khai.

## Follow-up / defer phát sinh

- **P0 blocker:** regression cho post-mutation snapshot `dropoff`; không mở producer idle/efficiency trước khi pass.
- **P1:** thiết kế topic/reason `SWAP_SOON` tách `ONLINE` maintenance; dry-run 30 seed.
- **P1:** pure analytics adapter cho income pace/plan deviation với typed facts và owner-approved thresholds.
- **P1:** quyết định brief/passive/recap có tính vào target 5–10 hay không.
- **DEFERRED:** weather, traffic, events, external demand, live station availability; không gọi API trong phase này.
