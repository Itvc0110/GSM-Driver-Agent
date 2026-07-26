# UPDATE-051 — D-SIM-09: nối solver **S1 `bonus_feasibility`** vào kênh `accept_lift`

Ngày: 2026-07-26 · Track: **A** · Tiếp nối UPDATE-050 (`c5c6a7e`)

## 1. Vì sao

Nợ kiến trúc **do chính tôi tạo ra** ở SIM-4 và tự nêu tên ở UPDATE-050: `check_bonus_gate`
**tự cài lại lý lẽ của advisor** thay vì gọi solver — đúng lỗi "hai nguồn sự thật" mà SIM-1 (data
0.88 vs sim 0.96) và SIM-3 (hai lớp `PolicyBundle`) đã phải đi sửa.

| việc | bridge tự làm (cũ) | S1 đã có |
|---|---|---|
| so tỷ lệ nhận với ngưỡng | `acc < thr` | `ok_acc` |
| khả thi theo quỹ giờ | `_tier_reachable()` tự ước điểm/giờ | `enough_hours` + `historical_points_per_hour` |
| **ngưỡng HOÀN THÀNH** | ❌ **KHÔNG kiểm** | `ok_comp` |

Hệ quả cụ thể: sim **bỏ sót ràng buộc `completion`** ⇒ có thể khuyên tài xế nâng tỷ lệ **nhận**
trong khi thứ đang chặn thưởng của họ là tỷ lệ **hoàn thành**. **Lời khuyên sai địa chỉ.**

## 2. Đã làm gì

- `build_bonus_gap_input()` → record `bonus_gap_input` (schema L3) từ trạng thái hiện tại;
  `historical_points_per_hour` ước từ **chính tài xế trong ca**, thiếu lịch sử thì để rỗng cho
  S1 dùng fallback lý thuyết của nó (không tự chế ước lượng song song).
- `_advice_would_help()` **gọi `bonus_feasibility.solve()`**; chỉ khuyên khi nghẽn **DUY NHẤT**
  ở tỷ lệ nhận. Nghẽn ở **quỹ giờ** hoặc **completion** ⇒ `blocked_elsewhere`, im lặng.
- **Xoá `_tier_reachable()`** (S1 đã bao).
- **Giữ `_acceptance_recoverable()`** — S1 chỉ kiểm TĨNH (`acceptance ≥ ngưỡng`), không trả lời
  được *"tỷ lệ LUỸ KẾ còn gỡ kịp không?"*. Ranh giới solver/sim ghi rõ trong docstring.

> ⚠️ **ĐÍNH CHÍNH 2026-07-26 (UPDATE-053):** diễn giải mục này SAI. Mức sụt +32.276→+20.473 và
> "advisor im lặng 16/30 ca" hoá ra phần lớn là **artifact của BUG-DSIM13-02**: ở đầu ca chưa có
> offer nào, `actor.acceptance_rate` (0/0) mặc định **1.0**, khiến nhánh `already_qualified` chặn
> NHẦM lời khuyên phòng ngừa đầu ca. Sau khi sửa (dùng đúng ước lượng lịch sử/base), kết quả 30
> seed **trở lại đúng +32.276đ, 16/30** — tức các blocker THẬT của S1 (quỹ giờ, completion) hiếm
> khi bind ở đầu ca trong config này. Giá trị còn lại của D-SIM-09 là KIẾN TRÚC (một nguồn sự
> thật, ràng buộc completion được kiểm ở giữa ca) — không phải con số. Xem UPDATE-053.

## 3. Kết quả: **mean giảm, độ chính xác tăng mạnh** (ĐÃ ĐÍNH CHÍNH — đọc khung trên)

Đo lại 30 seed (cùng tài xế P4, cùng seed) và so với UPDATE-047:

| bậc | Δ payout TRƯỚC (tự chế) | Δ payout SAU (gọi S1) | CI 95% sau |
|---|---|---|---|
| `accept_lift` | +32.276đ | **+20.473đ** | [+4.017, +40.306] ✳ |
| `all` | +42.471đ | **+28.576đ** | [+12.060, +48.435] ✳ |

Thoạt nhìn như hồi quy. Nhưng phân tách phân phối cho thấy điều ngược lại:

| | lãi | **LỖ** | không đổi (advisor IM LẶNG) |
|---|---|---|---|
| **sau S1** | 10 seed · +745.411đ | **4 seed · −131.210đ** | **16 seed** |

Trước đây advice **luôn** được đưa ra, nên phần lớn 14 seed không-lãi là **lỗ thật**. Nay advisor
**im lặng ở 16/30 ca** nó không giúp được; lỗ chỉ còn **4 seed**, tỷ lệ lợi/hại ≈ **5,7:1**.

**Kết luận: mean thấp hơn nhưng đây là CẢI THIỆN.** Một advisor biết im lặng khi không giúp được
thì tốt hơn advisor lúc nào cũng nói — và đúng ranh giới sản phẩm (không hứa, không khuyên bừa).
Mean giảm vì **mẫu số gồm cả những ngày advisor cố tình không nói**, không phải vì lời khuyên kém đi.

## 4. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/advice_bridge.py` | sửa — `build_bonus_gap_input`, gọi S1, bỏ `_tier_reachable` |
| `tests/test_advice_bridge.py` | sửa — thay 2 test cũ bằng 3 test đường S1 |

## 5. Kiểm chứng

- **Full suite: 453 passed, 5 skipped** (trước 452).
- **Ràng buộc `completion` thật sự được áp** — test riêng: tài xế accept 1.00 nhưng completion
  0.25 ⇒ **không** được khuyên nâng tỷ lệ nhận (đúng: sai địa chỉ). Bản cũ sẽ khuyên.
- **Nghẽn ở quỹ giờ** ⇒ `blocked_elsewhere` (test riêng).
- **Input đúng schema** — test chặn khoá lạ, và `next_tiers` chỉ chứa mốc CHƯA đạt.
- Cổng an toàn + CRN + không rò tương lai: giữ nguyên từ SIM-3/4.

## 6. Adversarial self-review / flaws found

1. **Đọc "Δ giảm" thành hồi quy** — đã tránh: tách phân phối lãi/lỗ/im-lặng trước khi kết luận.
   Nếu chỉ nhìn mean thì đã revert một thay đổi tốt. ✅
2. **Logic của tôi ban đầu CHƯA CHẶT**: khi cả quỹ giờ *và* tỷ lệ nhận cùng nghẽn, tôi vẫn cho
   qua như "ca đáng khuyên". Test bắt được; đã sửa thành: nghẽn ở giờ/completion ⇒ im lặng. ✅
3. **Ranh giới solver/sim** — ghi rõ cái gì thuộc S1, cái gì sim bổ sung (và VÌ SAO). ✅

**FLAW ghi nhận:**

- **F-DSIM09-A (TB) — nhận diện nguyên nhân nghẽn bằng CHUỖI TIẾNG VIỆT** (`"quỹ" in reason`,
  `"tỷ lệ nhận" in reason`). Đổi câu chữ trong S1 sẽ **âm thầm** làm hỏng gate này. Nên để S1
  trả về mã lý do có cấu trúc (vd `blockers: ["hours", "acceptance"]`) thay vì parse text.
- **F-DSIM09-B (TB) — 4 seed vẫn LỖ.** Advisor vẫn khuyên trong vài ca không đáng. Cần soi
  4 ca đó để tìm điều kiện còn thiếu.
- Kế thừa: `D-SIM-10` (sim nhiều ngày — đòn bẩy lớn nhất), `Q-01` thưởng tân binh.

## 7. Visual review

`NOT_APPLICABLE` — không đổi giao diện; thay đổi hành vi đã đo bằng 30 seed. V-01..V-07 vẫn chờ Cường.

## 8. Follow-up

- **`D-SIM-11`** (F-DSIM09-A): S1 trả mã lý do có cấu trúc thay vì để sim parse tiếng Việt.
- **`D-SIM-10`**: sim nhiều ngày — mở khoá S3/S5/S7/S8/S9.
