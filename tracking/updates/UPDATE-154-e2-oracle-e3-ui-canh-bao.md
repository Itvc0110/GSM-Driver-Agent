# UPDATE-154 — E2 arm ORACLE-ADHERENCE (số chốt 100 seed) + E3.1/E3.3 UI cảnh báo thu nhập

- **Ngày:** 2026-08-06
- **Loại:** research (phép đo mới) + feature đo lường + UI backend
- **Liên quan:** UPDATE-151 (r04/r06) · plan E2/E3 · T-041 1b' · D-SIM-K3

## E2 — LẦN ĐẦU tách "giá trị NỘI DUNG" khỏi "mức CHỊU NGHE" (câu hỏi arm-100% của Cường)

`scripts/run_oracle_adherence.py`: 3 arm/seed (A off · B_real adherence thực tế · B_oracle
`adherence_by_archetype=1.0` trên **cfg GỐC** — bẫy ORACLE-03 né đúng, gate |z|>4 **OK cả hai
arm**). Kênh ship (positioning `wait_only`), coverage=**all** (hết pha loãng 1/k của r07-F2).

### Số chốt (100 seed, ĐẠT chuẩn biến-thể-vs-biến-thể T-041 1b'; artifact `research/audit/2026-08-06-e2/oracle-100.json`)

| | Δ vs arm A (/tài xế/ngày) |
| --- | --- |
| **B_real** (nghe theo hồ sơ 0,30–0,75) | **+4.457đ** |
| **B_oracle** (nghe 100%) — TRẦN nội dung | **+7.998đ** |
| **Mất vì không nghe** (hiệu-của-hiệu ghép cặp) | **+3.541đ** CI95 **[2.407; 4.669]** — SIG ở n=100 |
| gini / served_rate | ~0 — không đánh đổi công bằng/hệ thống |

Smoke 30 seed cho +3.480 [1.211; 5.754] — **nhất quán** với số chốt (lần này n nhỏ không lừa,
nhưng vẫn chỉ trích số 100).

**Đọc đúng:** ~44% giá trị kênh ship đang mất ở khâu NGHE, không phải khâu NỘI DUNG ⇒ đầu tư vào
cách TRÌNH BÀY/THUYẾT PHỤC (sản phẩm) có trần giá trị ~3,5k/tài xế/ngày — lớn hơn nhiều kênh mới.
⚠ Caveat bắt buộc: (1) coin nghe lời là **ASSUMPTION** (`DEFAULT_ADHERENCE` chưa có số thật —
UPDATE-046); con số này đo "khoảng cách tới trần NẾU hồ sơ nghe đúng như giả định"; (2) Δ lẫn
random-stream divergence (`D-SIM-K3`, oracle là cực đại phân kỳ); (3) MOCK toàn phần.

### Kèm theo
- 4 cổng `tests/test_e2_oracle_arm.py` (ORACLE-03 pin · cấm sửa DEFAULT_ADHERENCE · đủ 7 hồ sơ ·
  min_seeds=100 cho diff-of-diff).
- Dashboard tab A/B: bảng **Δ theo hồ sơ (P1..P7) + theo đội pin** (expander, chỉ phép trừ từ
  `pr.system_a/b`, caveat pha loãng coverage=single). → V-31.

## E3.1 + E3.3 — UI cảnh báo "chỉ số sắp hại thu nhập" (backend+web tôi làm, Flutter → Khánh)

1. **Thẻ cliff phòng ngừa**: S1 đã tính `sensitivity[acceptance_cliff]` (tỷ lệ nhận trong
   [ngưỡng, ngưỡng+3pp]) mà adapter **vứt** — nay `_cliff_item()` nối vào CẢ nhánh feasible lẫn
   infeasible: `reason_code=acceptance_near_threshold`, id `s1-…-cliff` (giữ namespace L4-07),
   **0 số tiền** (không thành lời hứa), message dùng note của solver.
2. **`policy_thresholds` đi cùng MỌI payload advice** (`bonus_min_acceptance/completion` +
   `policy_v:`) — client thôi hardcode ngưỡng (họ D-M3-17).

Test: `ui/backend/tests/test_e3_canh_bao_thu_nhap.py` (4) — suite ui/backend **198 passed**.

**Chưa làm (chuyển tiếp):** E3.2 S8 penalty→recap (cần plumbing topic ở router) · E3.4 "còn gỡ
kịp" (`_advice_would_help` semantics sang UI — cần field gi) · HANDOFF Khánh cập nhật (Flutter
đọc `policy_thresholds` + render thẻ cliff).

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| Oracle smoke 30 → chốt 100 | 2 artifact; adherence gate OK cả 4 arm-lượt |
| `tests/test_e2_oracle_arm.py` | 4 passed |
| ui/backend suite | **198 passed** |
| Suite chính (sau toàn bộ E1) | **1106 passed / 5 F đỏ sẵn / 0 hồi quy** (ghi ở UPDATE-153) |

## Visual
`WAITING → gom V-31`: bảng Δ P1..P7 trên dashboard + thẻ cliff trên web demo — nhắc Cường xem
MỘT LẦN cuối chương trình như đã dặn.

## Adversarial self-review
1. Oracle đo trên **kênh ship duy nhất** — chưa chạy config all-sau-fix (plan có ghi; để sau E4
   để đo một lần với kênh mới).
2. "Mất vì không nghe" phụ thuộc **tuyến tính vào giả định adherence** — nếu hồ sơ thật nghe
   nhiều hơn giả định, phần mất co lại. Không trích số này mà thiếu caveat (1).
3. Cliff card chưa có test END-TO-END qua route `/advice` (unit + source-wired only) — route test
   nằm trong nhóm E3.2 khi đụng router.

## Follow-up
E4 (E-05 end-shift đầu tiên — đường thi hành đã nối sẵn) · E5 (lọc test r13) · UPDATE-155+.
