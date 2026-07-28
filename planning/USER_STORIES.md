# USER STORIES — Nháp ban đầu (DRAFT)

Cập nhật trạng thái: 2026-07-27. Story là **giả thuyết** cho đến khi được xác nhận bằng nghiên cứu (`planning/RESEARCH.md`). Mở rộng scope = thêm story ở đây trước, xác nhận pain point, rồi mới làm.

Quy ước ID: `US-<khối>-<số>` (khối: F0 policy, F1 trước ca, F2 trong ca, F3 sau ca).

## F0 — FAQ chính sách có cấu trúc

- **US-F0-01** · Là tài xế Bike mới, tôi muốn chọn câu hỏi định sẵn "tuần này chạy bao nhiêu chuyến thì được thưởng gì" và nhận câu trả lời template đúng với hồ sơ, kèm nguồn chính sách, để không bỏ lỡ thưởng mà không phụ thuộc chat tự do.
- **US-F0-02** · Là tài xế thuê xe công ty, tôi muốn biết policy bundle nào áp dụng riêng cho track thuê/RTO (phí thuê, platform share, khấu trừ), để phân biệt đúng driver payout và estimated net.
- **US-F0-03** · Là tài xế, tôi muốn được cảnh báo khi chính sách/mức thưởng thay đổi so với lần tôi xem trước, để không hành động theo thông tin cũ.

## F1 — Trước ca

- **US-F1-01** · Là tài xế mở app đầu ca, tôi muốn thấy ngay các chương trình thưởng/giới hạn mới áp dụng cho tôi hôm nay, để lên kế hoạch ca.
- **US-F1-02** · Là tài xế, tôi muốn tự đặt/chỉnh/bỏ mục tiêu **driver payout theo tuần** và chỉ xem estimated net khi hệ thống biết đủ chi phí, để mục tiêu rõ ràng và không nhầm với gross, khoán policy hoặc mission.
- **US-F1-03** · Là tài xế part-time đặt chỉ tiêu quá cao so với quỹ thời gian, tôi muốn agent chỉ ra vì sao khó đạt và gợi ý mức hợp lý, để không thất vọng/quá sức.
- **US-F1-04** · Là tài xế, tôi muốn được tư vấn cách tối ưu để đạt mức thưởng gần nhất (cần thêm bao nhiêu chuyến/giờ), để quyết định có theo hay không.

## F2 — Trong ca

- **US-F2-01** · Là tài xế đang trong ca, tôi muốn biết **demand proxy** trong những giờ tới tương đối cao/thấp (dữ liệu mock, không phải đơn chắc chắn được phân), để chọn lúc chạy và lúc nghỉ — không phải để reposition hay quyết định một cuốc cụ thể.
- **US-F2-02** · Là tài xế bike, tôi muốn được gợi ý khung giờ thấp điểm phù hợp để nghỉ/sạc, để không mất đơn giờ cao điểm.
- **US-F2-03** · Là tài xế, tôi muốn nhận cập nhật voucher/ưu đãi mới ngay trong ca, để tận dụng kịp.
- **US-F2-04** · (mở 2026-07-21 sau verify — có điều kiện) Là tài xế đang idle giữa các cuốc, tôi muốn được gợi ý khu vực đứng chờ có demand tương đối cao gần đây (heatmap mock, capacity-aware chống dồn cung, kèm cảnh báo "đơn có thể được phát khi đang di chuyển — từ chối ảnh hưởng tỷ lệ nhận"), để giảm thời gian chờ — hệ thống không hứa thu nhập và không khuyên nhận/từ chối đơn nào.

## F3 — Sau ca

> **Ghi chú 2026-07-24:** "tỷ lệ nhận gần ngưỡng policy" (US-F3-02) và "từ chối ảnh hưởng tỷ lệ nhận" (US-F2-04) — sau Vận Doanh 23/02/2026, ngưỡng còn hiệu lực là **eligibility thưởng tuần (≥85% HN)** + đạt **khoán tuần**, KHÔNG phải phạt <70% (đã bỏ). Diễn giải phải nói "lỡ thưởng/truy thu khoán", không "bị phạt". Xem [research/policy/policy-refresh-2026-07-24.md](../research/policy/policy-refresh-2026-07-24.md).

- **US-F3-01** · Là tài xế kết thúc ca, tôi muốn bản tổng hợp tách gross revenue, driver payout và estimated net (nếu known costs đủ), cùng thời gian chạy/chờ và so với chỉ tiêu payout, để hiểu đúng kết quả ca.
- **US-F3-02** · Là tài xế, tôi muốn được chỉ ra tối đa vài pattern chưa tối ưu kèm giải thích (vd: sạc trong khung demand cao, thiếu tiến độ tới mốc thưởng versioned, tỷ lệ nhận gần ngưỡng policy), để ca sau làm tốt hơn mà không bị phán xét theo từng cuốc.
- **US-F3-03** · Là tài xế, tôi muốn một gợi ý cụ thể duy nhất cho ca tới (không phải danh sách dài), để dễ thực hiện.

## Backlog story chưa phân loại

- (trống — thêm vào đây khi có ý tưởng mới, kèm pain point giả định và cách xác nhận)
