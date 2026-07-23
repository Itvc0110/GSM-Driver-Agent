# UPDATE-027 — Solver S2 ShiftDP + shift_plan_input derivation (C3)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE C3)
- **Loại:** feature / fix (model gap) / test / refactor
- **TODO / User story liên quan:** Track CORE; US-F1-04, US-F2-02; pain #2

## Tóm tắt

Solver thứ 2: DP timing-only tối ưu lịch online/nghỉ/sạc/kết-ca cả ca để max E[payout] gồm terminal mốc thưởng ngày. Thuần numpy (không LLM/scipy). Brainstorm chốt: timing-only (không cell), forecast historical (no future-leak), output full schedule + next-action + delta. **Phát hiện + sửa model gap khi integration** (fatigue-as-money làm delta âm). 12 test + integration mock; full suite 100 pass.

## Chi tiết cập nhật

### Model gap phát hiện qua integration (root-cause protocol §4b)
Bản đầu dùng `lambda_fatigue_vnd` phạt online → objective = payout − fatigue_ảo → baseline "online liên tục" luôn payout thuần cao hơn → **delta_payout ÂM** (min −34,998 trên mock). Reproduce → classify **MODEL GAP** (không phải bug code): fatigue-as-money bịa số tài chính (vi phạm §5) và sai bản chất US-F2-02.

**Fix:** bỏ fatigue penalty; mô hình đúng = tài xế **SẼ nghỉ R bucket** (nhu cầu sinh lý, ràng buộc cứng `rest_min_per_4h`), DP **đặt nghỉ vào bucket demand thấp nhất**. Baseline đổi thành "nghỉ ngây thơ đầu ca". State augment `rests_left`. Kết quả: **delta_payout ≥ 0 mọi driver** (min +2,499, max +40,008 / 20 driver). Thêm: ONLINE chỉ chọn khi expected payout > 0 (demand=0 → END/REST, không phí online).

### `gsm_core/solvers/shift_dp.py`
- State `(bucket, soc_band, points_band, rests_left)` ~ B×10×16×R — trivial. Backward DP + reconstruct forward.
- Actions {ONLINE, REST, SWAP, END}; terminal END hợp lệ khi nghỉ đủ; SWAP nạp SOC đầy; tie-break ONLINE>REST>SWAP>END.
- No future-leak: solver signature chỉ `(spi, policy, params)` — không nhận orders/l1 (test enforce).

### `gsm_core/features/shift_plan.py` + `_common.py`
- derive `shift_plan_input`: buckets_remaining, points_now, demand_forecast = **historical hour-shape ngày TRƯỚC** (test_derive_no_future_leak: bỏ trip hôm nay → forecast không đổi).
- Refactor helper chung (`_common.py`: hour/date/points_on_date...) dùng cho cả bonus_gap + shift_plan.

### SolverReport
schedule[] + next_action{action,bucket,reason} + expected/baseline/delta_payout + projected_points/tier. numbers[] mọi số có source (traceability=1.0). sensitivity demand −20%/−40%. digest tiếng Việt.

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_core/solvers/shift_dp.py` | tạo |
| `src/gsm_core/features/shift_plan.py` | tạo |
| `src/gsm_core/features/_common.py` | tạo (shared helpers) |
| `src/gsm_core/features/bonus_gap.py` | sửa (import shared) |
| `tests/test_shift_dp.py` | tạo (12 test) |
| `tracking/TODO.md` | C3 DONE |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| delta_payout ≥ 0 (DP ≥ baseline) | OBSERVED-CODE | integration 20 driver min +2499; test_delta_nonnegative | Cao | advice vô giá trị |
| No future-leak | OBSERVED-CODE | test_no_future_leak (signature) + test_derive_no_future_leak | Cao | vi phạm §3.5 |
| Mọi số có source | OBSERVED-CODE | test_number_traceability | Cao | vi phạm §5 |
| Nghỉ đặt vào demand thấp | OBSERVED-CODE | integration schedule (nghỉ 14-15h demand~0) | Cao | — |

## Kiểm chứng

### Seeds và scenarios

| Run | Kết quả |
|---|---|
| `pytest tests/test_shift_dp.py` | **12/12 pass** (failing-first) |
| Full suite | **100/100 pass** |
| Integration `data/mock/v1` 20 driver | delta ∈ [+2499, +40008], all ≥ 0; schedule đặt nghỉ đúng demand thấp |
| Determinism | test_tiebreak_deterministic |

## Visual verification

- **Status:** `NOT_APPLICABLE` — solver layer, không UI. Schedule là JSON (visualize Gantt ở M3).

## Adversarial self-review / flaws found

1. **Fatigue-as-money (đã sửa):** bịa số tài chính → bỏ, thay bằng ràng buộc nghỉ cứng. Delta giờ là giá trị THẬT của đặt nghỉ đúng chỗ + chốt mốc.
2. **Số bịa?** Không — payout_per_order từ policy fare; điểm từ policy; forecast từ historical. Test enforce.
3. **Future-leak?** Signature không nhận orders; forecast chỉ historical — 2 test.
4. **Model đơn giản hóa (ghi rõ):** p_accept=0.9 hằng số (cá nhân hóa sau); avg_dist=3.0 hằng; SOC chưa suy từ swap (None→default đầy); rest_min heuristic 1/4h. Đều params override được.
5. **Points_band rời rạc** (15đ/band) có thể sai số terminal ±1 tier ở biên — chấp nhận cho bản đầu, ghi.
6. **Flaw còn mở → C4+:** p_accept/avg_dist cá nhân hóa từ ledger; SOC derivation từ swap; demand forecast tốt hơn = EXP-003.

## Expansion checkpoint (T-039)

1. **Schema**: `shift_plan_input.demand_forecast[].bucket` desc nói "15ph" nhưng dùng 30ph — đề xuất minor: làm rõ resolution field hoặc bỏ ràng buộc desc. `soc_pct` nên có `soc_label` như driver_day_state khi suy từ swap (ESTIMATED).
2. **Bài toán tối ưu mới?** DP state đã có points → có thể mở "khuyến nghị mốc mục tiêu tối ưu" (chọn tier đáng cố) — hiện chỉ report tier đạt được. C4+.
3. **Tính năng mới?** schedule[] sẵn sàng cho **Gantt visualize hành trình khuyến nghị** (M3) — nối được ngay khi có UI.

(Không tự triển khai — đề xuất để Cường duyệt.)

## Follow-up / defer phát sinh

- **C4 (tiếp theo):** S3 F3Patterns (rule/stat, sau ca) — brainstorm+plan riêng.
- p_accept/avg_dist/SOC cá nhân hóa; EXP-003 demand forecast model; points_band mịn hơn nếu cần.
