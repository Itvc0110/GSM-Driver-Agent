# A2 — nút **"Bỏ qua"** đang làm **ngược ý tài xế** ở ca không mở lúc 06:00

> Bằng chứng cho visual gate của `UPDATE-181`. Không cần dựng server: hệ quả nằm trọn trong
> phép tính pha, và bảng dưới đây là **đầu ra thật** của hai bản code.

## Cơ chế

`get_advice` tính pha bằng `shift_start_min` **từ query**; `_phase_of` (đường ghi nhận *"Bỏ qua"*)
đọc **hằng module** `SHIFT_START_MIN = 06:00`. Hai công thức, **cùng một request**.

Nút *"Bỏ qua"* ghi *"im pha này"*. Nếu pha bị ghi sai thì hệ thống **im một khung khác** với khung
tài xế vừa xin im.

## Tài xế ca đêm 22:00 → 02:00 (đầu ra THẬT của bản CŨ)

| bấm "Bỏ qua" lúc | pha ĐÚNG | pha bị ghi (CŨ) | hậu quả với tài xế |
| --- | --- | --- | --- |
| **22:24** | `early` | `late` | im nhầm khung **00:40–02:00**, còn **22:00–23:20** *(khung vừa xin im)* **VẪN NÓI** |
| **23:24** | `mid` | `late` | im nhầm khung **00:40–02:00**, còn **23:20–00:40** **VẪN NÓI** |
| **00:24** | `mid` | `early` | im nhầm khung **22:00–23:20** *(đã trôi qua)*, còn **23:20–00:40** **VẪN NÓI** |
| **01:36** | `late` | `early` | im nhầm khung **22:00–23:20** *(đã trôi qua)*, còn **00:40–02:00** **VẪN NÓI** |

**4/4 mốc sai.** Hai mốc cuối tệ nhất: hệ thống làm im một khung **đã trôi qua** — tức cú bấm
của tài xế **không có tác dụng nào cả**, trong khi khung họ thật sự muốn im vẫn tiếp tục hiện thẻ.

## Ca chiều 14:00 → 23:00 (bản CŨ)

**2/4 mốc sai** — lệch một pha (`early`→`mid`, `mid`→`late`).

## Ca ngày 06:00 → 22:00

**0/4 sai** — nhưng **đúng do tình cờ**: giờ mở ca trùng đúng hằng `SHIFT_START_MIN`. Đây là lý do
lỗi sống lâu: ca mặc định của demo che nó hoàn toàn.

## Sau khi sửa

**0/12 mốc lệch** trên cả ba kiểu ca (`test_A2_hai_duong_tinh_pha_phai_KHOP`, lưới 3 ca × 3 vị trí).

## Cường cần xác nhận gì

Mở card ở một `(driver, date, now_min)` thuộc **ca chiều hoặc ca đêm**, bấm **"Bỏ qua"**, rồi hỏi
lại trong **cùng pha** — thẻ phải im; hỏi ở **pha khác** — thẻ phải hiện lại. Trước bản sửa, hai
điều đó đảo nhau ở ca đêm.
