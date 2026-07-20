# Research Summary — Đợt 1 (T-001)

Ngày: 2026-07-20 · 4 file chi tiết: [income-structure.md](income-structure.md) · [bonus-programs.md](bonus-programs.md) · [pain-points.md](pain-points.md) · [order-distribution.md](order-distribution.md)
Phương pháp: 4 agent nghiên cứu web song song + kiểm chứng chéo; claim trung tâm (chính sách ĐBTN — URL seed) đã được xác minh trực tiếp lần 2 trên trang official.

## 10 điều quan trọng nhất rút ra

1. **Công thức thu nhập Bike (official):** `Thu nhập = Doanh số × tỷ lệ chia sẻ + Thưởng tuần (tích điểm) + Thưởng khác`. Hà Nội hiện hành (02/03/2026): chia sẻ "lên tới 75%", thưởng tuần tới 1,2tr (mốc điểm HN: 400/700/1.100/1.400+ → 200k/400k/800k/1,2tr).
2. **Điểm thưởng gắn khung giờ**: cuốc 6–8h & 16–18h = 10 điểm, giờ thường = 5 điểm; "cuốc Điểm Vàng" 16h–19h59 T2–T6 → khung giờ là đòn bẩy thu nhập số 1 mà agent có thể tư vấn.
3. **ĐBTN 3 tháng đầu (từ 30/03/2026, đã xác minh 2 lần):** HN/HCM full-time đến 600k/ngày (≥15 cuốc/ngày, hệ thống đảm bảo phát tới 17 cuốc, thiếu bù 36k/cuốc, cần ≥1 khung cao điểm 6h–8h59/16h–18h59); part-time tối thiểu 360k/ngày.
4. **Ngưỡng kỷ luật là ràng buộc cứng cho mọi lời khuyên:** tỷ lệ nhận/hoàn thành <70% → phạt 100–200k/tuần, 3 tuần → có thể chấm dứt; <50% → ép auto-accept tới 23h59; một số ĐBTN yêu cầu ≥90%. Không bao giờ khuyên hành vi nhóm 1–2 (hủy cuốc vẫn chở khách: ≥2tr + chấm dứt).
5. **3 track hợp tác, kinh tế khác hẳn nhau** (hồ sơ mock phải ghi track): xe cá nhân platform (chiết khấu ~21%, bike), thuê/RTO xe công ty (60k/ngày hoặc 1,5–1,7tr/tháng, chia 90/85%, chiết khấu ~31% bản cũ), nhân viên taxi Car (lương ~4,96tr + 25–60% doanh số).
6. **Chi phí Bike rất thấp**: sạc ~10k/ngày hoặc đổi pin 9k/lần; nhiều chương trình miễn phí pin tới 2028–2029 → net ≈ gross × (1−chiết khấu) − chi phí nhỏ.
7. **Thu nhập tự khai ≈ tuyến tính theo giờ chạy**: 4h→~8tr/tháng; 8–10h→15–20tr; >10h→22tr+ → F1 dùng làm baseline nhận xét chỉ tiêu theo quỹ giờ.
8. **Pain point số 1 (4+ nguồn): sạc/đổi pin** — chờ 45ph–1h, tủ pin HN quá tải giờ cao điểm; pattern tốt của tài xế top: sạc ~3h giữa trưa (giờ 5-điểm) kết hợp nghỉ ăn → đúng bài F2.
9. **Mock phân phối đơn**: anchor VN = 2 khung cao điểm 6–9h & 17–20h (Grab official + quy định HN + chính khung điểm vàng Xanh SM); hình dạng chi tiết proxy Didi (peak chiều > sáng ~1.2–1.5×, trưa không tụt sâu); T6/T7 boost tối; mưa ×~1.2. Mức tuyệt đối: ~10 chuyến/xe/ngày đội xe Xanh SM; full-time bike 15–30 cuốc/ngày.
10. **Chính sách đổi rất thường xuyên và bảng chi tiết nằm trong ẢNH/in-app** → knowledge base F0 phải version theo effective date + trích ảnh gốc; cần người vào app tài xế chụp/OCR bảng thưởng hiện hành (gap lớn nhất).

## Gap tổng hợp cần xử lý tiếp (đề xuất việc mới)

- ~~OCR/nhập tay ảnh official~~ → Cường quyết 2026-07-20: **không OCR** — chạy research đợt 2 (T-012); không tìm ra thì mock có reasoning.
- Kinh nghiệm khu vực đứng chờ tại HN — research đợt 2 tìm qua bài FB public/repost; không có thì suy luận + mock.
- Quy trình khiếu nại/giải trình → **DEFERRED (D-007)**: bài toán khác.
- Phân phối đơn theo giờ của VN không có số công bố → đã mock có reasoning tại `specs/mock-order-distribution.md` (nhãn PROXY).

## Mapping research → features

| Feature | Research dùng trực tiếp |
| --- | --- |
| F0 policy Q&A | bonus-programs (bảng thưởng/phạt + effective date), income-structure (3 track) |
| F1 trước ca | pain-points §thu nhập tự khai (baseline theo giờ), bonus-programs (mốc thưởng tuần, ĐBTN, điểm vàng) |
| F2 trong ca | order-distribution (hour shape, dow, mưa), pain-points (sạc trưa, ngưỡng 70/90%) |
| F3 sau ca | pain-points (hành vi chưa tối ưu: sạc giờ cao điểm, thiếu điểm tới mốc, tỷ lệ nhận gần ngưỡng) |
| Hồ sơ mock (T-002) | 3 persona: part-time 4h/~8tr; full-time 8–10h/15–20tr; full-time xe riêng >10h/22tr+ |
