# UPDATE-174 — TỰ KIỂM hai con số đang đỡ quyết định của Cường: **cả hai tái tạo được**

- **Ngày:** 2026-08-07
- **Loại:** verification (tôi tự đo, không tin relay) — **0 dòng code sản phẩm/sim thay đổi**
- **Artifact:** `v1-tu-kiem-arm-null-dm320.py` + `.json` · `v2-tu-kiem-cong-hep-dadv02.py` + `.json`
- **Lý do:** hôm nay tôi đã trả giá vì tin số của agent hơn số của repo (`UPDATE-173` rút lại đính chính
  65,3%). Hai con số dưới đây **đang đỡ hai quyết định Cường phải ra** ⇒ không được để chúng ở trạng thái
  *"agent báo"*.

## 1. `D-M3-20` — arm NULL: nhiễu trôi-stream **CÓ THẬT**, và lớn hơn tôi tưởng

Thiết kế: A = `advice.enabled=False` · **Bnull** = kênh `rest_window` **BẬT** + patch `coin_follows` →
**luôn False** ⇒ **đúng 0 can thiệp**. Multiday **3 ngày × 6 seed** (7000–7005), cùng seed (CRN).

| đại lượng | SD nhiễu (tôi đo) | % nền | khác 0 |
| --- | --- | --- | --- |
| `rest_min_total` | **376,4′** | 3,12% | **6/6 seed** |
| payout đội | **807.129đ** | 1,19% | **6/6 seed** |
| `work_span_p90` *(proxy của tôi)* | 3,3′ | 0,49% | 6/6 seed |

**⇒ Bnull ≠ A ở 6/6 seed dù KHÔNG một lời khuyên nào được thi hành** ⇒ toàn bộ chênh lệch là **nhiễu
trôi-stream thuần**. Claim gốc **ĐỨNG**.

**Dấu hiệu tái tạo mạnh:** seed 7000 của tôi ra **Δrest +519,1′** và **Δpayout −1.625.279đ** — **trùng
khít** số `pb-01` báo (+519,07′ / −1.625.279đ) ⇒ probe của nó là thật, không phải bịa.

**Đối chiếu bộ acceptance `UPDATE-142`** (SD ≈ nửa-CI/1,96×√30): `rest_min_total` SD_nhiễu **376,4′** vs
SD_UPDATE-142 ≈ **140,4′** ⇒ **tỷ số 2,68**. Nghĩa là **nhiễu một mình LỚN HƠN toàn bộ độ phân tán quan
sát được** — còn nặng hơn con số 1,12 mà `pb-02` báo.

⚠ **Một dòng của tôi KHÔNG so được:** `work_span_p90` của tôi là **proxy** (p90 của `online_min` trên mọi
actor-day), **không** phải `work_span` của tầng sức khoẻ (đại lượng reset theo quãng nghỉ) ⇒ tỷ số 0,18
của tôi **không** xác nhận cũng **không** bác con số 22,4′ / 1,22 của `pb-02`. Ai cần dòng đó phải đo
bằng chính `sim_metrics`.

## 2. `D-ADV-02` — `cổng-HẸP`: tái tạo **đến từng chữ số**

Arm B (chỉ `shift_extend`), coverage=all, 5 seed (1000–1004):

| tôi đo | `pb-03`/`pb-04` báo |
| --- | --- |
| **77 lượt ÁP** (15/ngày) | 77 ✓ |
| **16/77 = 20,8%** lượt có cửa sổ kéo **hoàn toàn** ngoài khung điểm | 20,8% (mẫu "áp") / 18,2% (mẫu "nói", n=88) ✓ |
| **128,1′** phút kéo vô căn / **1.392,3′** tổng = **9,2%** | 128,1′ / 1.392,3′ ✓ |
| **16/16** lượt vô căn có giờ kết ca **23h** | "old_shift_end 23:17–24:00" ✓ |

`cổng-HẸP` (im lặng khi **điểm khả thi trong cửa sổ kéo = 0**, cổng **một chiều**) cắt **đúng** tập vô căn
⇒ **giữ 61/77 = 79,2%** lượt, **0 lượt hợp lệ bị cắt oan**.

⇒ **Hướng sửa `cổng-HẸP` ĐỨNG**, và hai phương án của tôi (`W_END` cắt xuống 13,6% · `W_NOW` tắt một lan
can sức khoẻ chặn 36% lượt gọi) đều **can thiệp quá mức cần thiết**. Giữ quyết định dùng `cổng-HẸP`.

## 3. Hệ quả cho hàng đợi duyệt

Hai quyết định của Cường **nay dựa trên số tôi đã tự đo**, không phải relay:
- **Plan `D-M3-20`**: nhiễu ≥ toàn bộ độ phân tán quan sát ⇒ mọi Δ của `rest_window` **không đọc được**;
  và acceptance của cycle (fingerprint IDENTICAL khi ép coin từ chối) là **bất biến nhị phân**, kiểm được
  ngay. *(Riêng "A==B_fix 60/60" tôi **chưa** kiểm được — fix chưa được duyệt để viết.)*
- **`D-ADV-02`**: dùng `cổng-HẸP`, không dùng hai bản của tôi.

## Kiểm chứng

- V1 patch `AdviceActionBridge.coin_follows` ở **lớp**, restore trong `finally`; cfg dựng bằng deepcopy
  ⇒ không đụng file config. V2 patch `check_shift_extend` tương tự.
- V1 chạy **multiday** có chủ ý: `pb-01` đã chỉ ra run **1 ngày** cho **0 lượt** tới điểm rút RNG ⇒ đo
  1 ngày sẽ ra `Δ=0` và kết luận **sai** là "không có nhiễu". Tôi tránh đúng bẫy đó.
- **Chưa kiểm chứng:** `work_span_p90` (proxy, §1) · `A==B_fix 60/60` (cần fix, chưa duyệt) · V2 dùng
  `policy.trip_points` để tính "điểm khả thi" thay vì gọi `S1._points_possible` thật ⇒ **cùng đại lượng
  về nguyên tắc** nhưng không phải cùng đường code; khi thi hành phải gọi solver thật.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim đổi.

## Visual
`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. Việc **trùng khít đến từng chữ số** (519,07′ · 1.625.279đ · 77 · 16 · 128,1′ · 1.392,3′) là bằng chứng
   mạnh rằng probe của refuter là thật — **nhưng nó cũng nghĩa là tôi và nó dùng cùng harness**, nên
   trùng khớp **không** loại trừ một lỗi CHUNG của harness. Cái nó loại trừ là "agent bịa số".
2. Tôi **không** kiểm được vế `A==B_fix` — đó là vế *"fix có hoạt động"*, và nó vẫn là **claim chưa
   verify** khi Cường duyệt. Đã nói rõ thay vì để nó lẫn vào phần đã kiểm.
3. `SD` của tôi tính trên **6 seed** ⇒ bản thân SD có sai số lớn; tôi dùng nó để nói **bậc** (nhiễu ≥ hiệu
   ứng), **không** để nói con số chính xác.
4. V2 kết luận *"cắt đúng tập vô căn, 0 lượt oan"* là **đúng theo định nghĩa** của cổng (điểm khả thi = 0
   ⇒ im) — nó **không** chứng minh cổng đó là *tốt nhất*, chỉ chứng minh nó **không cắt oan**.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13 ·
**amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
