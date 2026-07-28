# Sim KHÔNG THỂ chấm điểm lời khuyên nghỉ — và bài học về việc kết luận vội

Ngày: 2026-07-27 · Nối tiếp [`10`](10-bug-bucket-min-khong-truyen.md).

> **⚠ HỒ SƠ NÀY ĐÃ ĐƯỢC VIẾT LẠI.** Bản đầu (cùng ngày) kết luận *"sửa BUG-S2-PARAMS làm advisor
> tệ hơn, vì nghỉ bắt buộc tăng 4×"*. **Kết luận đó KHÔNG được số liệu ủng hộ** — xem §3. Giữ lại
> câu chuyện sai ở đây thay vì xoá, vì bài học phương pháp mới là phần giá trị nhất.

## 1. Sự thật về code — phần này KHÔNG đổi

```
src/gsm_sim/behavior.py:142   fatigue = actor.online_min / actor.fatigue_threshold_min
src/gsm_sim/behavior.py:144   fatigue > 0.35 → có thể nghỉ ăn
src/gsm_sim/behavior.py:149   fatigue > 1.0  → có thể nghỉ ngắn
```

`grep fatigue` toàn `src/` chỉ ra ba dòng trên. `fatigue` **chỉ điều khiển việc tài xế tự nghỉ**.
Nó **KHÔNG** tác động tới: xác suất nhận đơn · tốc độ · tỷ lệ huỷ · rating · rủi ro sự cố.

⇒ **Trong thế giới này: nghỉ = mất tiền; không nghỉ = mất KHÔNG GÌ.**

**Hệ quả vẫn đứng vững (độc lập với §3):** chỉ tiêu kép ĐA-08 **không có tầng nào** đo được lợi ích
của nghỉ, nên sim **không thể** thưởng cho một lời khuyên nghỉ đúng — dù nó đúng đến đâu ngoài đời.
Đây là **MODEL GAP của simulator**, và nó chặn số hạng **C2 "giá trị nghỉ"** của spec objective v2:
đưa C2 vào solver bây giờ thì solver khuyên nghỉ nhiều hơn và thước đo chấm tệ hơn — **tối ưu hoá
vào một cái thước không có vạch cho thứ cần đo**.

## 2. Sửa BUG-S2-PARAMS làm nghỉ bắt buộc tăng 4× — cũng là sự thật

`_required_rest = (B · bucket_min // 240) · rest_min_per_4h`:

| Ca còn lại | `bucket_min=30` (bug) | `bucket_min=60` (đúng) |
|---|---|---|
| 10 giờ | 30 phút | **120 phút** |
| 6 giờ | 0 phút | **60 phút** |

## 3. ❌ Cái tôi kết luận SAI, và số liệu thật

### 3.1 Kết luận vội

Bản đầu nối §1 với §2 thành: *"sửa bug ⇒ nghỉ nhiều hơn ⇒ payout xấu đi từ −17.310đ xuống
−24.960đ"*. Nghe rất khớp. **Nhưng cách kiểm chứng thì sai**: tôi so **hai lần chạy 30-seed khác
nhau về code** rồi gán nguyên nhân, chứ không so **ghép cặp** và không tính CI của chính hiệu số.

### 3.2 Ablation 10 seed đã cảnh báo — và tôi lại kết luận vội lần hai

| biến thể (10 seed, ghép cặp) | Δ payout |
|---|---|
| `none_bug` (như trước fix) | −19.776đ |
| **`bucket` (chỉ `bucket_min`)** | **−11.136đ** |
| `pacc_dist` | −19.776đ (**y hệt** `none_bug`) |
| `rates` | −19.776đ (**y hệt**) |
| `all` | −11.136đ |

Số này gợi ý **ngược lại** (fix giúp). Tôi báo cáo lại theo hướng đó — **cũng vội**, vì 10 seed
là tập con khác, không đủ CI.

### 3.3 Phép đo ĐÚNG: 30 seed, ghép cặp, cùng World A, bootstrap CI của hiệu số

| | giá trị |
|---|---|
| Δ payout **trước** fix | −17.309,63đ |
| Δ payout **sau** fix | −24.959,73đ |
| **hiệu số của fix** | **−7.650,10đ** |
| **CI95 của hiệu số** | **[−24.390,08 · +9.521,79]** |
| có ý nghĩa thống kê? | **KHÔNG** |
| số seed fix GIÚP | **12/30** |
| spread hiệu số theo seed | **min −90.651 · max +96.237** |

**Kết luận đúng: tác động của fix lên payout KHÔNG đo được ở n=30.** Ước lượng điểm âm, nhưng CI
trùm cả hai phía. Cả *"fix làm tệ hơn"* lẫn *"fix làm tốt hơn"* đều **không có căn cứ**.

## 4. Bài học phương pháp — phần giá trị nhất của hồ sơ này

1. **Hai lần chạy khác code KHÔNG phải một phép so ghép cặp.** Muốn so hai biến thể advice thì
   phải cố định World A theo seed và chạy cả hai nhánh B trên **đúng seed đó**, rồi bootstrap
   **hiệu của hiệu**.
2. **n=30 đủ cho A/B advice, KHÔNG đủ cho variant-vs-variant.** SD của hiệu số ở đây ~40k trong
   khi hiệu ứng ~7,6k ⇒ cần **n ≈ (1,96·40.000/7.650)² ≈ 105 seed**. `MIN_SEEDS_FOR_SIGNIFICANCE
   = 30` được hiệu chỉnh cho bài toán khác. **Phải ghi rõ điều này ở `parallel.py`.**
3. **Một câu chuyện nhân quả khớp đến đâu cũng không thay được CI.** §1 + §2 đều đúng, ghép lại
   nghe rất thuyết phục, và vẫn sai.

## 5. Phát hiện phụ, vững: `p_accept`/`avg_dist_km`/gate thưởng là **inert**

`pacc_dist` và `rates` cho kết quả **giống hệt đến từng chữ số** với `none_bug`. Giải thích: chúng
chỉ **scale `online_pay`**, trong khi `REST`/`SWAP` cộng đúng `0.0` ⇒ **argmax không đổi**.

Đây là bằng chứng độc lập, mạnh, cho model gap trung tâm của spec objective v2 §0: **khi nhánh
không-chạy không có giá trị, mọi thay đổi về ĐỘ LỚN thu nhập đều vô nghĩa** — chỉ ràng buộc
(nghỉ/SOC) mới đổi được nghiệm. Đó cũng là lý do `bucket_min` là tham số duy nhất có tác dụng.

## 6. Việc phải làm

1. **Cơ chế mệt mỏi trong sim** (T-041 bước 1c) — vẫn là điều kiện tiên quyết của C2, theo §1.
   Không phụ thuộc vào việc §3 kết luận thế nào.
2. **Ghi ngưỡng seed theo loại so sánh** vào `parallel.py` — A/B advice ≥30; variant-vs-variant
   ≥100 (hoặc dùng thiết kế giảm phương sai).
3. Ablation 30 seed thay vì 10 nếu cần khẳng định `pacc_dist`/`rates` inert ngoài 10 seed đã chạy.

## 7. Chưa kiểm (trung thực)

- Chưa chạy n≈105 seed để kết luận về hiệu số của fix. **Chưa biết fix giúp hay hại.**
- `rest_min_per_4h = 0` **cố ý chưa đo** — con số đó dễ bị trích dẫn thành *"nên bỏ ràng buộc nghỉ"*.
- Chỉ archetype P4, một config, một kênh.
