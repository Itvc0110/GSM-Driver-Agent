# UPDATE-028 — Solver S3 F3Patterns + L2i inference + session_summary (C4)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE C4)
- **Loại:** feature / test
- **TODO / User story liên quan:** Track CORE; US-F3-01/02/03; pain #1/#2/#3

## Tóm tắt

Solver thứ 3 (3/4): F3 sau ca — phát hiện hành vi chưa tối ưu từ observable+inferred, trả patterns có cấu trúc cho agent diễn giải. Rule/stat thuần. Brainstorm chốt: **L2i inference layer riêng** (taxonomy §3.5), **4 pattern**, loss = **observed + HEURISTIC** (KHÔNG số tuyệt đối như `detect_flaws` sim — tuân §5). 13 test + integration mock (18/20 driver có pattern, 0 số loss tuyệt đối); full suite 113 pass.

## Chi tiết cập nhật

### `gsm_core/features/infer_activity.py` — L2i (tầng inferred riêng)
Suy `inferred_activity` từ observable gaps: `charging_likely` (quanh swap_transaction, conf 0.9), `rest_likely` (gap ≥20ph không swap, conf 0.6), `idle_wait` (gap 5-20ph, conf 0.5). Mỗi record nhãn `INFERRED` + `inference_rule_version="infer-v1"` — KHÔNG BAO GIỜ trình bày như đo được.

### `gsm_core/features/session_summary.py` — L3
trips + inferred_activities + payout_breakdown (**tách gross/payout**, estimated_net=null vì chưa known costs) + day_state_end (điểm/acceptance/completion).

### `gsm_core/solvers/f3_patterns.py` — 4 pattern
Mỗi pattern **tách observed + severity ordinal + heuristic_note** (không số VND):
- `charge_rest_peak`: sạc/nghỉ (L2i) trong point_peak_hours → HIGH/MED.
- `acceptance_cliff`: acceptance <0.5 (forced) hoặc sát ngưỡng thưởng → cảnh báo (nối S1).
- `bonus_progress_gap`: thiếu ít điểm đã bỏ lỡ mốc → "thiếu Xđ đạt Yk" (Y source policy_v).
- `idle_peak`: idle dài giờ cao điểm → cảnh báo, KHÔNG chỉ vùng (ranh giới F2-04).
Output: patterns[] sort theo severity, `top_pattern` (US-F3-03), `n_patterns`. numbers[] chỉ số có source; **KHÔNG số loss tuyệt đối** (test enforce §5).

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_core/features/infer_activity.py` | tạo (L2i) |
| `src/gsm_core/features/session_summary.py` | tạo (L3) |
| `src/gsm_core/solvers/f3_patterns.py` | tạo |
| `tests/test_f3_patterns.py` | tạo (13 test) |
| `tracking/TODO.md` | C4 DONE |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| Không số loss tuyệt đối (§5) | OBSERVED-CODE | test_no_absolute_loss + integration loss_abs=0 | Cao | vi phạm §5 |
| Inferred tách tầng + nhãn INFERRED | OBSERVED-CODE | test_infer_schema (source=INFERRED) | Cao | trình bày suy diễn như đo được |
| Mọi số có source | OBSERVED-CODE | test_number_traceability | Cao | vi phạm §5 |
| Pattern hợp lý trên data thật | OBSERVED-CODE | integration 18/20; bonus_gap 14/charge_peak 6/cliff 2 | Trung | — |

## Kiểm chứng

### Seeds và scenarios

| Run | Kết quả |
|---|---|
| `pytest tests/test_f3_patterns.py` | **13/13 pass** (failing-first) |
| Full suite | **113/113 pass** |
| Integration `data/mock/v1` 20 driver | 18/20 có pattern; **0 số loss tuyệt đối**; top pattern personalize đúng |
| Determinism | test_determinism |

## Visual verification

- **Status:** `NOT_APPLICABLE` — solver layer, không UI. patterns[] visualize ở M3 (flaw callout).

## Adversarial self-review / flaws found

1. **Số loss bịa (đã tránh):** khác `detect_flaws` sim (`loss_vnd` số cụ thể) — S3 chỉ observed + HEURISTIC note + severity ordinal. Test + integration xác nhận 0 số loss tuyệt đối.
2. **Inferred as measured?** Không — nhãn INFERRED + confidence + rule_version giữ nguyên; observed{inferred:true} đánh dấu rõ.
3. **Số bịa?** numbers[] chỉ điểm/mốc (policy_v) + duration/acceptance (observed) — traceability test.
4. **Ranh giới F2-04:** idle_peak chỉ cảnh báo, KHÔNG chỉ vùng (ghi trong note).
5. **Simplification (ghi rõ):** rest/idle từ gap trip (chưa dùng GPS đứng-im vì mock GPS nội suy liên tục); relocating pattern skip (cần GPS reliable). confidence phản ánh.
6. **Flaw còn mở → C5+:** relocating inference cần GPS thật; net_income chờ known costs; severity threshold (40ph=HIGH) là heuristic — calibrate khi có feedback.

## Expansion checkpoint (T-039)

1. **Schema**: `inferred_activity` đủ cho 3 label dùng; `relocating` label có sẵn nhưng chưa sinh (cần GPS) — không thêm field. `session_summary.day_state_end` là object tự do — cân nhắc schema hóa chặt hơn khi ổn định.
2. **Bài toán tối ưu mới?** Từ inferred_activities: "phân bổ nghỉ tối ưu retrospective" (so lịch thực vs S2 khuyến nghị) — đối chiếu F3 vs F1, khả thi. C5+.
3. **Tính năng mới?** patterns[] + severity sẵn cho **flaw timeline visualize** (M3) và **"1 gợi ý duy nhất" (top_pattern) render** (C6 Composer).

(Không tự triển khai — đề xuất để Cường duyệt.)

## Follow-up / defer phát sinh

- **C5 (tiếp theo):** S4 CapacityAlloc (chống herding, scipy linear_sum_assignment) — brainstorm+plan riêng. Solver cuối.
- relocating inference (GPS thật); net_income (known costs); severity calibration.
