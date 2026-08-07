# UPDATE-181 — Cycle 1 (phần 1/2): **một công thức pha** cho đường sản phẩm + **R-08** cho nhánh nén

- **Ngày:** 2026-08-07
- **Loại:** implementation đường sản phẩm — **CÓ đổi hành vi đo** (không đổi thứ tài xế nhìn thấy)
- **Thuộc:** `PLAN-2026-08-07` Cycle 1 · thực thể `A2`, `A11`, `D-L4-M5`
- **Còn lại của Cycle 1:** `A3` (hằng nhịp v2), `A4` (ngân sách trọn đời), `D-L4-M3` (trạng thái
  hấp thụ) — **chưa làm**, xem §4

## 1. `A2` — hai công thức PHA CA trong CÙNG một request

`get_advice:195` tính pha bằng `shift_start_min` **từ query**; `_phase_of:126` đọc **hằng module**
`SHIFT_START_MIN = 360`. Docstring của `_phase_of` tuyên bố *"MỘT công thức duy nhất"* — **nhãn
sai**: `F4` bỏ được neo **KẾT ca** cứng nhưng **để nguyên neo MỞ ca**.

**Hệ quả:** với **mọi tài xế không mở ca đúng 06:00**, nút **"Bỏ qua"** hoặc vô tác dụng, hoặc làm
advisor im ở một pha **chưa hề bị tắt**.

### Đo được (bản CŨ vs bản MỚI, 12 mốc × 3 kiểu ca)

| ca | bản CŨ lệch | bản MỚI lệch |
| --- | --- | --- |
| ngày 06:00→22:00 | 0/4 (trùng hằng nên đúng tình cờ) | 0/4 |
| chiều 14:00→23:00 | **2/4** | 0/4 |
| **đêm 22:00→02:00** | **4/4** | 0/4 |
| **tổng** | **6/12** | **0/12** |

Ví dụ ca đêm lúc **01:36**: đường đọc nói `late`, `_phase_of` cũ nói **`early`** — ngược hẳn.

**Sửa:** `_phase_of(at_min, shift_end_min, shift_start_min)`; và vế thứ hai của cùng lỗi — `at_min`
là phút **wall-clock** nên ca vắt nửa đêm cho `90 − 1320 < 0` ⇒ pha `early` **vĩnh viễn**; nay wrap
sang ngày hôm sau, **đối xứng với `_norm_shift_end`** đã làm cho vế kết ca.

## 2. `A11` — tham số khai mà không đọc

`_cadence_memory(driver_id, date, **phase**, shift_end_min)`: chữ ký nói ký ức nhịp có phạm vi
theo **PHA**, thân hàm dựng ký ức cho **CẢ NGÀY**. Đã bỏ `phase`, thêm `shift_start_min`.

## 3. `D-L4-M5` — nén một lời khuyên **KHÔNG TỒN TẠI**

`_note_suppressed` được gọi **trước khi biết advisor có gì để nói**, trong khi `_note_shown` có
cổng `if not items`. Sửa: tính `advisor.advice()` trước, chỉ ghi `suppressed` khi **thật sự có gì
để nén**. Đây đúng **R-08** mà sim đã áp cho **5 kênh** (`should_defer_rest:919-921`).

### ⚠ Nhưng HAI con số của agent thì tôi **BÁC BẰNG ĐO**

Agent `L4` báo *"**26,7%** (3880/14550) driver-phút có `advice()` trả `items == []`"*.

**Tôi đo** trên **110 tài xế BIKE × 3 ngày × 64 mốc = 21.120 driver-phút**: **20 = 0,1%**.

**Nguồn của 26,7%:** catalog có **150 tài xế, 40 là car/premium**, và `40/150 = **26,7%** chính
xác`. `advisor.py:227` chặn chúng **ngay ở cửa** với `no_active_channel` ⇒ agent đếm *"advisor CỐ Ý
không phủ đội này"* thành *"advisor không có gì để nói"*.

> Đây **đúng cái bẫy** mà lượt quét đầu của `mm-03` đã sập (sai ~2× vì đếm cả `ce-*`) và bản đồ đã
> **cảnh báo tường minh ở §5.7**. Vòng audit sau vẫn sập lại.

Vế *"660/660 event suppressed là MA"* **chưa kiểm lại** và nhiều khả năng nhiễm cùng lỗi ⇒
**cấm trích cả hai số**. Hạ severity `D-L4-M5` **CAO → THẤP**.

**Fix vẫn ĐÚNG và vẫn giữ:** bất đối xứng có thật, `R-08` là nguyên tắc của chính repo, và test
đối chứng `test_l4_04_bi_nen_phai_duoc_ghi_nhan` (đã có sẵn) xác nhận lời khuyên **thật** bị nén
**vẫn được ghi**. Chỉ **bán kính nhỏ hơn nhiều** so với báo cáo.

## 4. Cái CHƯA làm của Cycle 1 (nói trước, không để tưởng đã xong)

`A3` (v2 chép luật nhịp bằng hằng riêng `>= 6` / `20*60` thay vì `cadence.effective_gap_min = 30`)
· `A4` (ngân sách thẻ đếm **trọn đời**) · `D-L4-M3` (`suppressed` là **trạng thái hấp thụ** ⇒ một
cú nén cooldown 20′ **giết vĩnh viễn** lời khuyên còn hạn cả ngày). Ba mục này nằm ở
`lifecycle/checkpoint.py` + `advice_checkpoint.py` — **đường v2**, mà `ADVICE_V2_ENABLED` mặc định
`"0"`. Chúng là **điều kiện tiên quyết của việc bật v2**, không phải việc gấp.

## Kiểm chứng

- **Test vi phân MỚI** `test_A2_hai_duong_tinh_pha_phai_KHOP` — lưới **3 ca × 3 vị trí**, ĐỎ-trước.
  ⚠ Lần chạy đầu đỏ vì **chữ ký** (chưa nhận `shift_start_min`), **không phải** vì logic ⇒ tôi đo
  riêng độ lệch thật của bản cũ (bảng §1) thay vì coi "test đỏ" là đã chứng minh.
- `test_A11_...` (AST: tham số khai phải được đọc) · `test_M5_...` (kèm **vế ngược**: có lời khuyên
  thật bị nén thì PHẢI ghi — chống test-ghim-vô-hiệu).
- `ui/backend/tests`: **216 passed** (baseline 205 + 11 test mới). ⚠ **`tests/` chưa chạy lại**
  trong update này — thay đổi chỉ ở `ui/backend/app/routers/advice.py`, nhưng theo `CLAUDE.md`
  chưa chạy thì chưa được nói "suite xanh".
- **Chưa kiểm chứng:** Δ số **event `suppressed` THẬT** bị cắt (tôi mới đo tỷ lệ driver-phút im
  lặng, **không phải** tỷ lệ event bị cắt — hai đại lượng khác nhau, đã ghi cảnh báo trong probe).

## Visual
🔴 **BLOCKED — CẦN CƯỜNG XEM.** Đây là đường sản phẩm và **có đổi hành vi**: pha ca đổi với mọi
tài xế không mở ca 06:00 ⇒ nút *"Bỏ qua"* nay tắt đúng pha. Cần Cường mở card ở một
`(driver, date, now_min)` **ca chiều hoặc ca đêm** và xác nhận. Không gộp im lặng vào V-31/V-32.

## Adversarial self-review / flaws found

1. **Test vi phân của tôi đỏ vì SAI LÝ DO** ở lần chạy đầu (chữ ký, không phải logic). Nếu tôi
   dừng ở đó và gọi là "đỏ-trước xong", tôi đã chứng minh nhầm. Phải đo riêng bản cũ mới ra
   được bảng 6/12.
2. **Hai con số agent bị bác trong CÙNG một vòng** (`M1` coverage=single, `M5` car/premium). Tỷ lệ
   sai của soi độc lập hôm nay là **2/5 finding định lượng** — cao hơn mức ~1/4 tôi từng ghi.
   ⇒ Giữ nguyên luật: **không relay số của agent, đo lại cái nào định trích**.
3. **Cả hai lần sai đều cùng một cơ chế**: mẫu số nhiễm những ca **cố ý không thuộc phạm vi**
   (một tài xế thay vì cả đội; cả đội thay vì đội được phủ). Đây là khuôn đáng ghi thành luật:
   *"trước khi chia, hỏi mẫu số có gồm ca ngoài phạm vi không"*.
4. **Cycle 1 mới xong 3/6 thực thể.** Tôi tách UPDATE thay vì chờ trọn cycle vì phần đã làm
   **đứng độc lập** (khác file, khác cơ chế với 3 mục còn lại) và đã có test riêng.

## ⏳ Nhắc PENDING-REVIEW

🔴 **MỚI — blocking:** visual gate cho card ở **ca chiều/ca đêm** (§Visual).
**Vẫn chờ:** **V-32** (blocking) · V-31 · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/09/10/13 · amendment ĐA-08 — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`.
⏸ Khánh: 2 test đỏ + Flutter.
