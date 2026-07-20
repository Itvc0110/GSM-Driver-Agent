# RESEARCH — Kế hoạch nghiên cứu thực tế

Cập nhật: 2026-07-20 · Trạng thái: **CHƯA CHẠY** — đây là việc ưu tiên cao nhất song song với xây khung.

## 1. Mục tiêu nghiên cứu

1. **Features thực tế ảnh hưởng thu nhập** của một tài xế Xanh SM: cấu trúc thu nhập (cước, thưởng, phụ phí, phần chia cho app, chi phí tự chịu: xăng→điện/sạc, thuê xe, khấu hao, phạt).
2. **Các cách tài xế có thể tăng thu nhập**: chương trình thưởng (theo chuyến/doanh thu/khung giờ), khung giờ cao điểm, khu vực, duy trì tỷ lệ nhận/hoàn thành, tier.
3. **Lý do tài xế chưa tối ưu được thu nhập** (root cause của pain point): không nắm chính sách, sạc sai thời điểm, từ chối đơn ảnh hưởng hồ sơ, chạy giờ thấp điểm, không đủ điều kiện thưởng, v.v.
4. **Số liệu để mock sát thực**: phân phối đơn theo khung giờ/ngày trong tuần/khu vực; thu nhập trung bình theo loại tài xế.

## 2. Nguồn cần tra cứu (tất cả trang/nguồn liên quan tài xế Xanh SM)

- Trang chính sách chính thức greensm.com, ví dụ seed: <https://www.greensm.com/vn-vi/news/chinh-sach-dam-bao-thu-nhap-cho-green-bike-platform> (chính sách đảm bảo thu nhập Green Bike platform).
- Các trang news/chính sách khác của greensm.com: tuyển dụng tài xế (car/bike, thuê xe vs xe cá nhân), chính sách thưởng, chương trình đối tác.
- App/Google Play listing (Green SM Driver) — mô tả tính năng phía tài xế.
- Cộng đồng tài xế: nhóm Facebook, YouTube review, diễn đàn — pain point và con số thực tế do tài xế tự chia sẻ (đánh dấu độ tin cậy thấp hơn nguồn chính thức).
- Báo chí về thu nhập tài xế công nghệ VN (Xanh SM, so sánh Grab/Be) — mức thu nhập, giờ chạy điển hình.
- Nghiên cứu/thống kê về phân phối đơn ride-hailing theo giờ/ngày (để mock phân phối).

## 3. Câu hỏi nghiên cứu cụ thể

- Cơ cấu chia app/tài xế của Xanh SM theo từng hình thức (xe cá nhân platform vs thuê xe công ty vs nhân viên)?
- Các mốc thưởng hiện hành: điều kiện (số chuyến, doanh thu, tỷ lệ nhận đơn, khung giờ), giá trị, chu kỳ (ngày/tuần)?
- Tỷ lệ nhận đơn / hoàn thành ảnh hưởng gì (ưu tiên phân đơn, thưởng, phạt, khóa app)?
- Chính sách phạt phổ biến và quy trình giải trình?
- Giờ/khu vực cao điểm thực tế ở Hà Nội (thị trường thử nghiệm) và hình dạng phân phối đơn trong ngày/tuần?
- Chi phí sạc/đổi pin (bike), thuê xe theo ngày/tháng — ai chịu, bao nhiêu?

## 4. Đầu ra & nơi lưu

- Findings lưu vào `research/` (chia theo loại, xem `research/README.md`): `research/policy/`, `research/economics/`, `research/community/`, `research/market/`; mỗi claim kèm **nguồn + ngày truy cập + độ tin cậy** (chính thức / cộng đồng / báo chí / suy luận).
- Kết quả dùng để: xác nhận pain point & root cause, thiết kế 2–3 hồ sơ mock, tham số hóa mock phân phối đơn, viết knowledge base chính sách cho F0.
- Số chưa xác nhận được phải đánh dấu `TBD`/giả định — không đưa vào sản phẩm như fact.
