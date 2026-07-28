# BUG gốc: sim dựng bucket 60′ nhưng S2 tính như 30′ — nguyên nhân trực tiếp của "98,5% ONLINE"

Ngày: 2026-07-27 · Phát hiện khi chuẩn bị T-042 việc 3b. **Đây là BUG thường, không phải model gap.**

## 1. Sự việc

| Nơi | Giá trị |
|---|---|
| `configs/pilot_dongda.yaml:263` | `advice.bucket_min: 60` — *"bucket của shift_dp (khớp `derive_shift_plan_input_l1r`)"* |
| `advice_bridge.py:123` | `self.bucket_min = int(adv.get("bucket_min", 60))` |
| `advice_bridge.py:187` | dựng `starts` **cách nhau 60 phút** ⇒ `demand_forecast` là bucket 60′ |
| `advice_bridge.py:222` | **`shift_dp.solve(spi, self.policy)`** — **KHÔNG truyền `params`** |
| `shift_dp.DEFAULT_PARAMS` | `bucket_min: 30` |

⇒ **DP tin mỗi bucket dài 30 phút trong khi sim tiến 60 phút.**

`shift_dp.solve` là hàm **duy nhất** nhận `params`, và **không caller nào trong repo truyền gì**
(`grep shift_dp.solve` → đúng một chỗ, ở dòng 222).

## 2. Ba hệ quả, đều lệch về phía "cứ chạy tiếp"

| Tham số | Công thức | Với bucket 30′ (sai) | Đúng ra (60′) |
|---|---|---|---|
| `_soc_cost` | `soc_cost_per_bucket · bucket_min/30` | **1** band/bucket | **2** band/bucket |
| `_required_rest` | `(B · bucket_min // 240) · rest_min_per_4h` | **một nửa** số bucket nghỉ bắt buộc | đủ |
| cap cuốc/bucket | `bucket_min / service_min_per_trip` | 30/25 = **1,2** cuốc | 60/25 = **2,4** cuốc |

Pin được cho là bền **gấp đôi**, nghỉ bắt buộc bị **giảm nửa**. Cả hai đều đẩy nghiệm về ONLINE.

## 3. Đo tác động — 25 tài xế, seed 1000, cùng `spi`, chỉ đổi `params`

**Lịch khác nhau ở 18/25 (72%) tài xế.** Ví dụ:

```
actor 0:  bucket_min=30 (đang chạy)  ->  O O O
          bucket_min=60 (đúng)       ->  O O R
actor 3:  30 -> O O O   |   60 -> O O R
actor 5:  30 -> O O O   |   60 -> O O R
```

Đúng chiều đã đo ở [`09`](09-baseline-30seed-coverage-all.md): advisor giữ tài xế online thay vì
cho nghỉ, dẫn tới **+25,9 phút rỗi và −1,6 cuốc** với **cùng số giờ online**.

## 4. Vì sao lọt — cùng mẫu với UPDATE-076

AUDIT S2-6 (UPDATE-069) đã **thêm** tham số `bucket_min` và ghi rõ trong `DEFAULT_PARAMS`:
*"bucket KHÔNG còn ngầm định 30' — producer sim/l1r dùng 60'"*. Tham số được thêm đúng, **nhưng
caller duy nhất không bao giờ được cập nhật để truyền nó**.

Y hệt mẫu của [`08` §1b/§1c](08-parity-sim-vs-ui.md): **sửa ở một tầng, consumer/caller không biết**.
Đây là lần thứ ba trong cùng một phiên.

Và đây cũng chính là lý do **mutation MUT10 sống sót** (UPDATE-074): không test nào phủ
`bucket_min ≠ 30` **vì đường chạy thật cũng chưa bao giờ dùng ≠ 30**.

## 5. Còn hai tham số nữa cùng cảnh

`shift_dp.DEFAULT_PARAMS` tự ghi *"CALLER NÊN TRUYỀN số thật"* cho:

- `p_accept: 0.9` (AUDIT S2-4) — sim biết `actor.accept_base`/tỷ lệ thật;
- `avg_dist_km: 3.0` (AUDIT S2-5) — sim biết quãng đường thật.

Cả hai **cũng chưa bao giờ được truyền**. Và `acceptance_rate`/`completion_rate` không được truyền
⇒ `_bonus_eligible` trả `(True, False)` = **luôn coi như đủ điều kiện thưởng**, dù sim biết thừa
tỷ lệ thật của actor. Tức S2 trong sim **hứa thưởng cho cả người sẽ không được trả** — cùng loại
lỗi §1b nhưng ở kênh đang bật mặc định.

## 6. Việc phải làm (cycle riêng, có đo lại)

1. Test đỏ: bridge phải truyền `bucket_min` **bằng đúng** `self.bucket_min`.
2. Truyền đủ: `bucket_min`, `p_accept`, `avg_dist_km`, `acceptance_rate`, `completion_rate`.
3. **Đo lại 30 seed `coverage: all` + chỉ tiêu kép** — baseline [`09`](09-baseline-30seed-coverage-all.md)
   **sẽ đổi**, và đây là thay đổi được kỳ vọng làm advisor **bớt hại**.
4. Chỉ sau khi sửa bug này mới đánh giá được các số hạng chi phí của spec objective v2 (T-041
   bước 2) — nếu không sẽ đi hiệu chỉnh mô hình để bù cho một bug.

## 7. Ảnh hưởng tới kết luận đã công bố

Kết luận **"advisor làm tài xế nghèo đi −17.310đ/ngày"** vẫn **đúng như một mô tả hiện trạng** (đó
là hệ đang chạy). Nhưng **chẩn đoán nguyên nhân phải sửa**: hồ sơ 09 §1 và spec objective v2 §0 quy
toàn bộ cho *"REST/SWAP cộng 0.0"* (model gap). Nay biết thêm: **một phần đáng kể đến từ BUG tham
số**, làm ràng buộc nghỉ giảm nửa và pin tưởng bền gấp đôi. **Chưa biết tỷ lệ đóng góp của mỗi
nguyên nhân** — phải đo sau khi sửa (bước 3).
