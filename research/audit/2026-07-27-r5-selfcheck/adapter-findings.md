# R5-B — Double-check `ui/backend/app/adapters/mockdata.py` (reviewer #1)

Ngày: 2026-07-27 · 14 finding · TÔI ĐÃ TỰ KIỂM CHỨNG 5 cái nặng nhất bằng repro độc lập
(không tin agent suông) — **tất cả đều THẬT**.

## CAO — đã tự xác nhận

| ID | Lỗi | Bằng chứng tôi tự chạy |
|---|---|---|
| **F-01** | Map prefix fleet SAI một bậc | generator `profiles.py:65` dùng `cp`=car_platform, `px`=car_premium; adapter ghi `cp→car-premium`, `px→premium` ⇒ 15 tài xế VF5 bị gắn nhãn "premium" trên picker |
| **F-02** | Demand zones cắt top-12 TRƯỚC khi loại hex giả | **52% trips (86.368/167.575) có `pickup_h3='8amock…'`** (nhánh rule-based) → hex giả chiếm chỗ, bị `except: continue` nuốt ⇒ khung 07h chỉ còn 2/12 zone; `max_n` lấy từ hex đã loại ⇒ thang màu sai; alert mô tả zone KHÔNG tồn tại trên bản đồ |
| **F-03** | `payout > gross` ở 40 driver-day, không giải thích | d-1 2026-09-26: payout 248.338 > gross 237.784 (mission 70.000 nằm ngoài cước) — UI in "gộp 237.784đ" bên dưới số lớn hơn |
| **F-04** | Test invariant tiền chỉ chạy 1 tài xế | `payout <= gross` xanh vì `dv`=d-19; đổi sang d-1 là ĐỎ (8 driver vi phạm) |
| **F-05** | `_missions()` BỎ QUA tham số `date` | d-19 ngày 02/07 và 28/09 trả tiến độ GIỐNG HỆT `[12,5,1]` — luôn là snapshot ngày cuối; docstring nói "nhãn rõ" nhưng payload KHÔNG có nhãn nào (OVERCLAIM) |

## TB / THẤP (chưa tự kiểm từng cái)

`F-06` driver_location bịa theo hex nóng nhất (Flutter có đọc!) · `F-07` `date=2026-09` khớp
prefix → gộp cả tháng, HTTP 200 · `F-08` history nhận date rác trả 200 · `F-09` cửa sổ "14 ngày
có dữ liệu" ≠ 14 ngày lịch (51/150 tài xế có lỗ) · **`F-10` bảng `driver_penalization_ATA`
(75 dòng, 8.420.000đ) KHÔNG BAO GIỜ được đọc** — payout bỏ qua tiền phạt · `F-11` docstring nói
có nhãn PROXY, payload không có · `F-12` cap top-12 không nói ở đâu · `F-13` `shift_status` luôn
ON_SHIFT (nhánh chết) · `F-14` "tủ pin gần đây" nhưng distance=None, không sắp xếp.

## Reviewer đã thử bác nhưng KHÔNG bắt được (cân bằng)

Ngữ nghĩa tiền cơ bản ĐÚNG (`commission` là phần tài xế, khớp `realdata.py:171`) · timezone
không sót · rating chia đúng (0 dòng lỗi trên toàn bảng) · SOC thật sự deterministic ·
`[-days:]` không off-by-one · `driver_state` 404 sạch · `REPO_ROOT` đúng · không trùng mission id.

## Trạng thái xử lý

F-01 fix ngay (nhãn sai rõ ràng). F-02/03/05/10 + F-04 chờ 4 reviewer còn lại xong mới sửa —
tránh race với mutation-testing đang chạy trên `src/` và `tests/`.
