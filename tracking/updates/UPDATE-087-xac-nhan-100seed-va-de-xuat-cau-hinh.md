# UPDATE-087 — Xác nhận n=100 seed TƯƠI: kênh vị trí PASS 9/9; shift_plan không thêm giá trị

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** measurement (confirmatory — seed chưa từng dùng)
- **Artifact:** `25-confirm-100seed.json` — seeds **3000–3099** × (A · B1 · B3w), 300 run,
  `coverage: all`, estimator không bias (Q-11), veto 8(b)+9(b) (Q-10/Q-12)
- **Vì sao seed tươi:** dải 2000–2029 đã dùng cho MỌI quyết định thăm dò (α, Cycle R, artifact
  21–24) — xác nhận trên seed đã nhìn là tự chấm bài mình. 3000–3099 chưa từng chạm.

## Kết quả

| Δ vs A (n=100) | B1 (shift_plan + positioning) | **B3w (CHỈ positioning)** |
|---|---|---|
| **payout_mean_all** | **+5.758đ/người SIG** | **+6.016đ/người SIG** ✅ |
| payout_mean_P4 | −187 ns | −272 ns (CI ±1,4k — đủ power: không hại, không lợi) |
| served_rate | +1,41đp SIG | **+1,74đp SIG** |
| đơn hết hạn | −19,3 SIG | **−23,4 SIG** |
| Gini | GIẢM SIG | **GIẢM SIG** (−0,0069) |
| HHI cung/ô | GIẢM SIG | **GIẢM SIG** |
| tổng payout đội | +518k SIG | **+541k SIG** |
| km rỗng / veto 8(b) | +0,86đp / **PASS** | +0,81đp / **PASS** |
| đổi pin / chờ / veto 9(b) | +8,6 / ns / **PASS** | +3,9 / ns / **PASS** |

### So biến thể HỢP LỆ đầu tiên của chương trình (n=100 ≥ `MIN_SEEDS_FOR_VARIANT_COMPARISON`)

**B1 vs B3w** (= *shift_plan có thêm gì trên nền positioning?*): thu nhập **ns** (−258đ);
hệ thống **TỆ nhẹ SIG**: served −0,33đp · đơn chết +4,1/ngày · Gini +0,0029 · HHI +0,0005 ·
đổi pin +4,7. ⇒ shift_plan không những không thêm giá trị mà còn gây nhiễu nhẹ.

## Đề xuất trình Cường (KHÔNG tự bật)

Điều khoản ĐA-07 Cường đặt sẵn: *"bản cuối trước khi chốt: TẮT shift_plan để advisor IM LẶNG
nếu không đem lại hiệu quả"* — bằng chứng nay đủ và đúng chuẩn (n=100, seed tươi, so biến thể
hợp lệ). **Cấu hình đề xuất làm mặc định:**

```yaml
advice:
  channels:
    shift_plan: false        # ĐA-07 điều khoản bản-cuối — không hiệu quả (n=100, ns) + nhiễu nhẹ
  positioning_overrides: wait_only   # PASS 9/9 ĐA-08 (Q-11/Q-10b/Q-12b) trên mẫu xác nhận
```

Giữ: cảnh báo đỏ shift_plan trong khu Mô phỏng (đổi nội dung thành "đã tắt theo ĐA-07, bằng
chứng UPDATE-087") · `accept_lift` vẫn TẮT · mọi cờ tắt được về baseline.

**Lưu ý equity đi kèm** (không giấu): lợi ích +6k/người KHÔNG chia đều — P4 tân binh ≈ 0
(không hại). Gini vẫn giảm vì nhóm hưởng nhiều là nhóm thu nhập thấp-giữa. Nếu Cường muốn
tân binh cũng phải dương ⇒ cần kênh riêng cho P4 (việc mới, chưa hứa).

## Kiểm chứng

300 run CRN · veto verdict tự in trong script · artifact per-seed đầy đủ · suite trước đo
**633 passed / 5 skipped**.

## Visual verification

`BLOCKED` — gộp V-17 (nay xem với cấu hình đề xuất B3w).

## Adversarial self-review / flaws found

1. B1 vs B3w n=100 nhưng chỉ MỘT mode (wait_only) — chưa lặp cho wait_and_relocate (B2/B3r);
   quyết định mode dựa trên wait_only là bảo thủ có chủ ý (ghi đè ít nhất).
2. `swap_wait_mean` B1 +0,40′ CI (−0,07, +0,87) — SÁT ngưỡng SIG; nếu chọn B1 thì veto 9(b)
   mong manh. B3w thì thoải mái (+0,03′). Thêm một lý do cho B3w.
3. Adoption 100% (`coverage: all`) — đường cong phủ thấp hơn đo ở Cycle Q (artifact 28).
4. Thế giới 1 ngày; hiệu ứng nhiều-ngày (D-SIM-10 memory) chưa đo với positioning.

## ⏳ Nhắc PENDING-REVIEW

**MỚI: đề xuất cấu hình trên — chờ Cường duyệt bật.** V-01..V-17 · Q-03/Q-04/Q-07 · B-02 treo.
