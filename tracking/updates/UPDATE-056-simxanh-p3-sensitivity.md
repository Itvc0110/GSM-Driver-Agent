# UPDATE-056 — SIM-XANH Phase 3: quét độ nhạy D-SIM-06 (trước D-SIM-16 theo lệnh Cường)

Ngày: 2026-07-26 · Track: **A** · Sau Phase 4 (`c61f8f8`) · Kết quả: `research/experiments/sensitivity/dsim06_sweep.json`
Grid: {P4, P1} × adherence {0.3, 0.75, 1.0} × lift_max {0.10, 0.15, 0.19}, **30 seed/ô**, kênh
`accept_lift` CÔ LẬP (shift_plan tắt), hiệu theo cặp + CI bootstrap. P2 kiểm im-lặng 5 seed.
Đính chính nhỏ: commit `de70ff6` ghi "494 passed" — số đúng là **493** (bỏ thói quen ghi số dự đoán).

## 1. P4 (tân binh) — advice giúp, nhưng mỏng hơn con số cũ và vẫn là canh bạc

| adherence | lift 0.10 | lift 0.15 | lift 0.19 |
|---|---|---|---|
| 0.3 | +6.110 (ns) | +9.248 (ns) | +11.403 (ns) |
| 0.75 | **+11.941 ✳** | +11.688 (ns) | **+16.678 ✳** |
| 1.0 | **+11.941 ✳** | +10.688 (ns) | **+15.678 ✳** |

✳ = CI 95% không chứa 0 · ns = chứa 0 · n_pos tốt nhất chỉ **16/30**.

- **Đơn điệu đúng chiều**: Δ tăng theo lift và theo adherence; **adherence 0.3 giết significance
  ở mọi lift** — advisor mà tài xế không nghe thì không đo được giá trị (D-SIM-04 định lượng).
- **Con số +32.276đ cũ KHÔNG tái lập** và không nên so: nó thuộc **baseline đã nghỉ hưu**
  (engine detour, n=74 — UPDATE-054 §4). Trên engine đường-thật/n=90: ô mặc định (0.75/0.15)
  chỉ **+11.688, CI CHỨA 0**. Kết luận trung thực: với config hiện tại, hiệu ứng kênh
  accept_lift cho P4 là **dương-mỏng, chỉ chắc chắn ở lift 0.19 hoặc 0.10**, và vẫn là xổ số
  (14-16/30 ngày lợi). Cận trên tự nhiên: Δthưởng ~+10-15k ≈ đúng cỡ một bậc thưởng ngày.

## 2. P1 (part-time) — ZERO tuyệt đối, và lý do là CẤU TRÚC (không phải bug)

Cả 9 ô Δ = 0, n_pos 0/30 — B ≡ A từng đồng. Truy nguyên:
- **Đầu ca** (chưa đủ mẫu): ước lượng = `accept_base` P1 = **0.85 = đúng ngưỡng** ⇒ "đã đạt" ⇒ im.
- **Giữa/cuối ca**: ca P1 chỉ **3-4h** ⇒ S1 `bonus_feasibility` chặn đúng — không đủ quỹ giờ
  với tới mốc điểm nào (`blocked_elsewhere`).

⇒ Kênh này **không có đòn bẩy với part-timer sát ngưỡng ca ngắn** — advisor im lặng là hành vi
đúng (D-SIM-09 hoạt động như thiết kế). Muốn giúp P1 phải là kênh KHÁC (khung giờ/điểm-per-giờ),
không phải nâng tỷ lệ nhận.

## 3. P2 "kiểm im-lặng" — kỳ vọng của TÔI sai, và cái sai này có giá trị

Kỳ vọng: P2 (base 0.95 > ngưỡng 0.85) ⇒ advisor im ⇒ Δ ≈ 0. **Đo được: Δ +52.995 (5 seed).**
Root-cause: gate ước lượng bằng tỷ lệ **REALIZED trong ngày** — P2 gặp chuỗi xui (3/4 nhận =
0.75) bị ước lượng dưới ngưỡng ⇒ advice bắn. Và điều đó **ĐÚNG về sản phẩm**: `day_bonus` chấm
trên realized, nên ngày xui P2 **mất thưởng THẬT**; cảnh báo dip cứu lại **+24.000đ thưởng TB**.

**Reframe quan trọng**: giá trị kênh accept_lift không chỉ dành cho người propensity thấp (P4) —
mà cho **bất kỳ ai đang có một ngày xui**, vì điều kiện thưởng là con số realized.

**F-P3-B (chuyển cho MATH AUDIT — đúng loại câu hỏi Cường đặt ở §4 DIRECTIVES):** ước lượng
tỷ lệ hiện tại nhảy giữa hai chế độ (base/memory khi <5 offer, realized thô khi ≥5). Mẫu 4-5
offer quantize thô (0.75/0.80) → advice theo NHIỄU. Câu hỏi mô hình: có nên dùng **shrinkage
estimator** (prior = lịch sử memory, trọng số theo cỡ mẫu trong ngày)? Đây là quyết định
mô hình hoá, thuộc audit — không sửa ad-hoc.

## 4. Trung thực về phạm vi

Kết luận **chỉ đúng cho config này** (ngưỡng 0.85, tiers hiện tại, thị trường 1-quận n=90).
Không suy rộng "advisor giúp +X" cho mọi tài xế. `max_realized_accept` trong sweep được buộc
nhất quán với trần lift (nợ D-SIM-07 xử lý trong scope sweep).

## 5. Trạng thái DEFERRED liên quan

- **D-SIM-06 → DONE** (sweep này). **D-SIM-04** (adherence là giả định) → định lượng được:
  adherence <0.75 thì đừng hứa hẹn gì; giả định vẫn cần số thật để thay.
- **D-SIM-12** (4 seed lỗ thời D-SIM-09): thay bằng bức tranh mới — n_pos 14-16/30, đuôi thua
  nhỏ, thắng lớn khi flip bậc thưởng.

## 6. Kiểm chứng
Sweep 610 run · World A cache mỗi seed · guardrail served per-cell không có ô nào SIG xấu ·
mechanism P1/P2 truy nguyên bằng event thật (không đoán).
