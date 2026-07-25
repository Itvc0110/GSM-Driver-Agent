# Research đợt 4 (2026-07-24) — TÍNH NĂNG APP TÀI XẾ: đính chính giả định nền tảng

Ngày: **2026-07-24** · Người thực hiện: AI agent (yêu cầu Cường: "research thêm về app thật, tài xế, pain point")
Phương pháp: web research official greensm.com + press. Mỗi claim gắn nguồn/ngày/confidence.

> **⚠ FILE NÀY ĐÍNH CHÍNH MỘT GIẢ ĐỊNH NỀN TẢNG** của thiết kế advisor. Đọc trước khi động vào phạm vi tư vấn khu vực (D-004/D-004b) hoặc cảnh báo bất thường (UC7).

## 0. TL;DR — 4 phát hiện, 3 cái đổi thiết kế

| # | Phát hiện | Ảnh hưởng |
|---|---|---|
| **F-1** | **App ĐÃ CÓ bản đồ nhiệt + "Nhiệm Vụ Tiếp Theo"** (15/04/2026, app v3.6.1) | ❗ Đảo giả định "Xanh KHÔNG có heatmap" — nền tảng của D-004 |
| **F-2** | **"Mức độ cảnh báo gian lận"** in-app từ 10/10/2025, **4 mức: Không / Thấp / Cao / Rất cao** | S9 phải dùng ĐÚNG thang chính thức |
| **F-3** | **"Giải trình trực tuyến"** từ 15/12/2025 — **BẮT BUỘC trong 48 GIỜ** | S8/S9 phải nhắc hạn 48h (thời gian tính bằng giờ!) |
| **F-4** | Rebrand **Xanh SM → Green SM** (13/04/2026) | Thuật ngữ trong text tư vấn |

## 1. F-1 — App CÓ bản đồ nhiệt (ĐÍNH CHÍNH QUAN TRỌNG)

**Nguồn:** [greensm.com — "Cập Nhật Tính Năng: Nhiệm Vụ Tiếp Theo — Tối Ưu Nhận Cuốc"](https://www.greensm.com/vn-vi/news/cap-nhat-tinh-nang-nhiem-vu-tiep-theo-toi-uu-nhan-cuoc), đăng **15/04/2026** — **official/high**.

Trích: hệ thống *"dựa trên khu vực có nhu cầu cao gần vị trí hiện tại của Bác Tài nhất"*; *"**Kết hợp với bản đồ nhiệt** để xác định khu vực 'có nhiều khách'"*; gợi ý **không bắt buộc** (tài xế có thể không theo); dùng bằng cách nhấn **"Dẫn đường"** ở chế độ Trực tuyến; yêu cầu app **v3.6.1**.

### Vì sao đây là vấn đề
`research/simulation/action-space.md` §Phạm vi advisor viết: *"Xanh **không có heatmap demand cho tài xế** (khác Grab…)"* → đây là **căn cứ chính** để D-004 cấm/hạn chế tư vấn khu vực, và để lập luận "advice khu vực của ta là BỔ SUNG, không chồng đè". **Căn cứ đó nay SAI** (ít nhất từ 15/04/2026).

### Hệ quả thiết kế (quan trọng)
1. **KHÔNG xây heatmap riêng** — GSM đã có; làm thêm là **chồng đè và mâu thuẫn** với tối ưu của hãng (rủi ro đưa tài xế đi ngược gợi ý chính thức).
2. **Cách đúng = TRỎ VỀ TÍNH NĂNG CHÍNH THỨC**, giống cách đã làm với A14 "Danh sách chuyến hẹn giờ": *"anh/chị bật 'Dẫn đường' để xem Nhiệm vụ tiếp theo của hãng"*.
3. Thiết kế S7 IdleReduction hiện tại (**chỉ khuyên MỨC THỜI GIAN, không tự chọn ô H3**) **vẫn đúng** — nhưng nay có lý do mạnh hơn: không phải "vì hãng thiếu heatmap", mà **"vì hãng đã có, ta không cạnh tranh"**.
4. D-004/D-004b cần cập nhật căn cứ (không phải mở rộng phạm vi).

## 2. F-2 — "Mức độ cảnh báo gian lận" đã có in-app, 4 MỨC

**Nguồn:** press đưa tin đồng loạt về thử nghiệm từ **10/10/2025** ([CafeF](https://cafef.vn/xanh-sm-ra-mat-tinh-nang-moi-188251015150625646.chn) và tổng hợp) — **press/medium**.

- Tài xế xem được cảnh báo **hiện tại + 6 ngày gần nhất**.
- **4 mức rủi ro: Không · Thấp · Cao · Rất cao** — kèm **khuyến cáo cụ thể** để điều chỉnh hành vi.

**Hệ quả:** S9 AnomalyAlert đang tự đặt thang `low/medium/high`. Phải **map sang đúng thang chính thức** để lời tư vấn khớp cái tài xế NHÌN THẤY trong app (tránh gây rối: app nói "Cao", advisor nói "medium").

## 3. F-3 — "Giải trình trực tuyến": HẠN 48 GIỜ (rất actionable)

**Nguồn:** [greensm.com — Giải trình trực tuyến](https://www.greensm.com/vn-vi/news/giai-trinh-truc-tuyen) + press ([24hmoney](https://24hmoney.vn/news/tu-15-12-tai-xe-xanh-sm-co-nghi-van-vi-pham-bat-buoc-giai-trinh-truc-tuyen-c2a2702814.html), CafeBiz, Soha) — **official + press/high**. Hiệu lực **15/12/2025**.

- Cuốc bị **nghi vấn vi phạm** → tài xế **BẮT BUỘC giải trình trực tuyến trong 48 GIỜ**.
- Tài xế có thể **cung cấp thông tin, hình ảnh chứng minh + chọn lý do** nếu thấy hệ thống đánh giá chưa chính xác.
- Không hoàn tất đúng hạn → **ảnh hưởng tài khoản**.

**Hệ quả:** đây là **nhu cầu có tính thời gian gấp** (48h) — đúng loại việc advisor nên nhắc. S8 (giải thích khoản trừ) và S9 (cảnh báo dấu hiệu) nên nêu: *có quyền giải trình + hạn 48 giờ + làm trên app*. Lưu ý ranh giới **D-007**: ta **không** xây quy trình khiếu nại (dự án khác) — chỉ **nhắc quyền + hạn**, không thay tài xế giải trình.

## 4. F-4 — Rebrand & tên gọi
Xanh SM → **Green SM** chính thức **13/04/2026**. Text tư vấn nên dùng "Green SM" (hoặc trung tính "hãng"), tránh lẫn lộn.

## 5. Pain point MỚI rút ra (bổ sung `community/pain-points.md`)

| # | Pain point | Bằng chứng | Feature phục vụ |
|---|---|---|---|
| P-5 | **Bị nghi vấn vi phạm mà không biết/không kịp giải trình trong 48h** → mất tài khoản | F-3 | S8/S9 nhắc hạn 48h |
| P-6 | **Không hiểu mức cảnh báo gian lận đang ở đâu** (4 mức) và phải làm gì | F-2 | S9 map đúng thang + khuyến cáo |
| P-7 | Không biết/không dùng tính năng tối ưu sẵn có (Nhiệm vụ tiếp theo, Danh sách chuyến hẹn giờ) | F-1 + A14 | F2 trỏ về tính năng chính thức |

## 6. Ý tưởng tính năng MỚI (đề xuất — chưa triển khai, chờ Cường duyệt)

1. **Nhắc hạn giải trình 48h** (từ F-3): đếm ngược khi có cờ nghi vấn — giá trị cao, rủi ro thấp, dùng data `public_frauds.detected_at`. **Ưu tiên 1.**
2. **Đối chiếu "mức cảnh báo" với hành vi**: chỉ ra hành vi nào kéo mức lên (từ `driver_statistic_daily` + hex) — **không** nêu ngưỡng phát hiện (chống dạy lách).
3. **Nhắc dùng tính năng chính thức** (Nhiệm vụ tiếp theo / chuyến hẹn giờ) khi tài xế idle nhiều — thay vì ta tự gợi ý khu.
4. **Cảnh báo phiên bản app**: tính năng mới yêu cầu v3.6.1 — tài xế không cập nhật sẽ mất công cụ tối ưu (cần biết version, có thể ngoài data hiện có).

## 7. Gap / chưa xác minh
- Chi tiết thang 4 mức (tiêu chí từng mức) — chỉ có press, **chưa có trang official text**; cần xác nhận GSM.
- "Nhiệm vụ tiếp theo" có ảnh hưởng tỷ lệ nhận chuyến không → tài liệu **không nêu**; không được suy đoán.
- Heatmap có mở cho **Bike** hay chỉ Car/dịch vụ khác — bài không tách rõ; **cần hỏi GSM**.
