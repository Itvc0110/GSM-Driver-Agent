# Research — Cấu trúc thu nhập tài xế Xanh SM

Ngày nghiên cứu: 2026-07-20 · Trạng thái: đợt 1 (chưa kiểm chứng chéo toàn bộ) · Nguồn: T-001
Độ tin cậy: `official` (greensm.com/xanhsm.com) > `press` (báo chí) > `community` (trung gian/tự khai) — số từ community tối đa medium confidence.

> **⚠ BỔ SUNG 2026-07-24 — mô hình accounting đổi.** Chính sách **Vận Doanh 23/02/2026** chuyển tính doanh số **theo TUẦN (khoán tuần)** thay vì theo ngày; không đạt khoán tuần → **truy thu 20%** (HN/HCM tới 40% — 04/05/2026) phần thiếu, **cấn trừ ví** ⇒ đây là **khoản khấu trừ vào driver payout** (giống chức năng phạt cũ nhưng theo doanh số tuần). Gap #3 "chính sách phạt chính thức" bên dưới **nay đã có văn bản** (Bộ QTƯX 05/06/2026 + clawback 23/02/2026) — nhưng 2 nguồn **mâu thuẫn** về phạt <70%. `driver_payout` và `estimated_net` phải model được **clawback** như một deduction versioned. Chi tiết: [../policy/policy-refresh-2026-07-24.md](../policy/policy-refresh-2026-07-24.md).

## Kết luận chính (đọc nhanh)

Có **3 hình thức hợp tác**, cấu trúc thu nhập khác hẳn nhau — hệ thống phải coi chiết khấu/tỷ lệ chia là **tham số cấu hình theo thời gian**, không phải hằng số (chính sách đổi ít nhất 4 lần từ 2023):

| Hình thức | Cấu trúc thu nhập | Con số chính (kèm thời điểm) |
| --- | --- | --- |
| (a) Xe cá nhân chạy platform | Chia doanh thu, tự chịu chi phí xe/pin | Bike: chiết khấu 21% (press 07/2025); lúc ra mắt 15,5% (press 11/2023); Car: chia tới 87% doanh thu (official, n.d.) |
| (b) Thuê/mua trả góp xe công ty (RTO) | Chia doanh thu + phí thuê xe | 60.000đ/ngày hoặc 1,5–1,7tr/tháng, cọc 3tr, chia 90% năm 1 / 85% năm sau, sau 24 tháng sở hữu xe (community/press 2026); xe công ty chiết khấu ~31% (press 07/2025, chưa xác minh trực tiếp) |
| (c) Nhân viên (taxi Car) | Lương cứng + thưởng doanh số + BHXH | Lương cơ bản ~4,96tr/tháng + thưởng 25–60% doanh số/ngày (HN) + thâm niên 0,5–1tr/tháng (official 06/2025) |

Chi phí năng lượng Bike rất thấp: ~1.000đ sạc/chuyến, ~10.000đ/ngày (press 2023); đổi pin 9.000đ/lần, tối đa 20 lần/tháng (press 05/2026); nhiều chương trình miễn phí pin đến 2028–2029.

## Findings chi tiết

### Official

1. **Mô hình nhân viên taxi Car** — lương cơ bản ~4.960.000đ/tháng (theo vùng); thưởng trách nhiệm & doanh số = doanh số/ngày × tỷ lệ thưởng, 25% tạm ứng ngay sau mỗi chuyến; thâm niên: 6–9 tháng 500k/tháng, 9–12 tháng 700k/tháng, ≥12 tháng 1tr/tháng; thưởng chất lượng Premium ≥4.85 sao; thu nhập tham chiếu HN/HCM 25–30tr/tháng; thưởng giới thiệu 2tr, hỗ trợ tài xế mới 6tr (HN/HCM). — [greensm.com/news/chinh-sach-tai-xe-xanh-sm](https://www.greensm.com/news/chinh-sach-tai-xe-xanh-sm), 05/06/2025, **official/high**.
2. **Bike TP.HCM–BD–ĐN 11/2024**: "tỷ lệ chia sẻ doanh số lên tới 91%" tùy khung giờ cao/thấp điểm; thưởng tuần cho T7–CN–T2. Chi tiết nằm trong ảnh, không đọc được text; chưa thấy bản riêng cho Hà Nội. — [greensm.com](https://www.greensm.com/news/cap-nhat-chinh-sach-thu-nhap-danh-cho-doi-tac-tai-xe-xanh-sm-bike-tai-tphcm-binh-duong-dong-nai), 06/11/2024, **official/high**.
3. **Bike Platform toàn quốc từ 01/08/2025**: bổ sung đối tượng/thời gian áp dụng mức chia sẻ doanh số; thêm thưởng giờ cao/thấp điểm cho đơn Xanh SM Ngon (giao đồ ăn). Số cụ thể nằm trong 5 ảnh. — [greensm.com](https://www.greensm.com/news/chinh-sach-thuong-danh-cho-doi-tac-tai-xe-xanh-sm-bike-platform), 31/07/2025, **official/high**.
4. **Car platform xe cá nhân**: chia "lên tới 87% doanh thu chuyến xe"; gói vay mua xe tới 70%; doanh thu cập nhật real-time. — [greensm.com/driver-platform](https://www.greensm.com/driver-platform), n.d., **official/high**.

### Press

5. **Thu nhập thực tế 1 tháng taxi nhân viên HN (02/2024)**: 24.012.000đ/30 công × 12h/ngày (gồm 1tr thưởng nóng); trừ: thuế TNCN 10% (~2,4tr, hoàn một phần), rửa xe 250k, sạc điện 735đ/km (~2,2tr/tháng), gửi xe 1tr → còn >18tr. Tài xế taxi tự trả tiền sạc + gửi xe. — [CafeBiz](https://cafebiz.vn/mot-tai-xe-taxi-xanh-sm-cong-khai-tien-thu-ve-sau-1-thang-cao-hay-thap-so-voi-binh-quan-lao-dong-ha-noi-176240226203822547.chn), 26/02/2024, **press/high**.
6. **Bike lúc ra mắt (11/2023)**: chiết khấu 15,5% (thấp hơn 20–25% app khác); 5 nguồn thu nhập: chia doanh số + đảm bảo thu nhập (gói 5h=200k, 8h=320k, 10h=400k/ngày) + thưởng vượt mốc chuyến/ngày + thưởng điểm tuần + thưởng nóng; cọc 4tr nhận xe Feliz S. — [VnExpress](https://vnexpress.net/yeu-to-hut-tai-xe-cong-nghe-cua-xanh-sm-bike-4681734.html), 27/11/2023, **press/high** (chính sách cũ).
7. **Bike 2025, tài xế nữ 22,5tr/tháng, >10h/ngày, 2 cục pin/ngày**: mua xe riêng Feliz S 34,9tr → chiết khấu xe riêng **21%**; bảo dưỡng 5.000km "mấy chục nghìn", 20.000km >200k. Mức **31% cho xe công ty** xuất hiện trong search snippet, chưa xác minh trực tiếp. — [Thế Giới Tiếp Thị/Dân Việt](https://thegioitiepthi.danviet.vn/nu-tai-xe-xanh-sm-bike-225-trieu-thang-10-tieng-ngay-chuyen-sang-xe-dien-thay-khoe-hon-vi-d1344543.html), 02/07/2025, **press/high**.
8. **"Vào Xanh, Tặng Xe" (đến 30/04/2026, HN & HCM)**: cọc 3tr, trả góp Evo từ 1,5tr/tháng hoặc Feliz II từ 1,7tr/tháng; chia 90% năm 1 / 85% các năm sau; miễn phí thuê pin đến 31/3/2029, đổi pin không giới hạn; thưởng gia nhập 500k; trọn gói đăng ký/bảo hiểm/bảo trì. Tham chiếu: 15tr/tháng (100+ chuyến/tuần), 8,5tr/tháng (60+ chuyến/tuần). — [Vietnamnet](https://vietnamnet.vn/chinh-sach-uu-dai-cua-xanh-sm-bike-giup-tai-xe-lai-nguyen-chiec-xe-2501406.html), 29/03/2026, **press/high**.
9. **Đổi pin VinFast tại trạm**: 9.000đ/lần, tối đa 20 lần/tháng/xe (ưu đãi 10/02/2026–30/06/2028, Evo/Feliz II/Viper bản thuê pin); gói thuê pin tháng ~175–300k. vinfastauto.com trả 403, chưa xác nhận trực tiếp. — [iMotorbike News](https://news-vn.imotorbike.com/2026/05/doi-pin-xe-may-dien-vinfast-bao-nhieu-tien/), 05/2026, **press/medium**.

### Community (cẩn trọng — nhiều domain giả official)

10. **Tính lương taxi HN**: thưởng doanh số 25–60% doanh thu/ngày theo mốc, giờ cao điểm tỷ lệ cao hơn; thưởng ý thức chất lượng 940k–1.340k/tháng (Premium, hiệu lực đến 25/05/2025); thưởng nóng tới 3tr (HN)/6tr (HCM); thu nhập thực tế 15–25tr/tháng. — [hamireview.com](https://www.hamireview.com/tinh-luong-chi-tiet-cho-tai-xe-taxi-sm), n.d., **community/medium**.
11. **Lead bị chặn — phí gia nhập taxi nhân viên**: trang nhái official nêu tổng 8tr (2tr ngày đầu + 6tr trừ dần lương 2 tháng). — `taixexanhsm.com`, **T4/blocked lead**; không dùng làm economic/policy fact cho tới khi T1/T2 xác nhận.
12. **Lead bị chặn — Bike 12/2025**: trang nhái official nêu tài xế nhận 73% doanh số và các điều kiện online/tỷ lệ/chuyến. — `bike-xanhsm.com`, **T4/blocked lead**; không dùng làm policy/financial config hoặc output.
13. **RTO Evo 2026**: 60k/ngày (gồm VAT), cọc 3tr (2tr xe + 1tr pin), 24 tháng, chia 90%/85%, sau 24 tháng sở hữu xe; miễn phí đổi pin 5 lần/ngày đến 06/2028; miễn phí thuê pin tháng khi đạt 250+ chuyến và 10tr doanh thu/tháng. Đảm bảo thu nhập 3 tháng đầu HN/HCM: full-time 600k/ngày (≥17 chuyến, ≥10h online), part-time 360k/ngày (≥10 chuyến, ≥6h). — [vinfastvietnam3s.com.vn](https://vinfastvietnam3s.com.vn/chinh-sach-thue-so-huu-rto-xe-may-dien-vinfast-evo-cung-xanh-sm-gsm-moi-nhat-2026/), 2026, **community/medium**.
14. **Thuê ô tô điện chạy platform**: VF5 ~15,5tr/tháng qua HTX Bạn Hữu Đường Xa. — [banhuuduongxa.com](https://banhuuduongxa.com/san-pham/cho-thue-xe-dien-vinfast-vf5-chay-app-be-car-xanh-sm-flatform/), n.d., **community/low**.

## Gaps (TBD — chưa tìm được)

1. Bảng tỷ lệ chia doanh số Bike hiện hành (2025–2026) cho **Hà Nội** dạng số cụ thể — trang official chỉ đăng **ảnh**, không có text (bản 91% chỉ cho HCM/BD/ĐN).
2. **Mâu thuẫn chiết khấu Bike chưa giải quyết**: 15,5% (2023) vs 21% xe cá nhân / 31% xe công ty (2025) vs 27% (trung gian 12/2025) — cần bảng chính thức theo từng hình thức để đối chiếu.
3. Chính sách **phạt/trừ tiền chính thức** (mức VND theo lỗi, trừ điểm, khóa app) — không có văn bản công khai.
4. Khấu hao xe/pin cho xe cá nhân.
5. Giá thuê xe máy điện thuần (không RTO) tại HN từ nguồn chính thức.
6. Bảng so sánh đầy đủ Bike vs Car vs Premium về thưởng.
7. Phụ phí khách trả (đêm, thời tiết, lễ) — phần tài xế được hưởng.

## Ghi ý cho thiết kế hệ thống

- Chiết khấu/tỷ lệ chia = **policy có version + effective date + scope (thành phố, hình thức, loại xe)**.
- Cảnh giác domain giả official: `bike-xanhsm.com`, `xanhsmbike.com`, `taixexanhsm.com`, `xanhsmcar.com` — chỉ `xanhsm.com`/`greensm.com` là chính thức (xanhsm.com redirect sang greensm.com).
- Theo quyết định 2026-07-20, **không OCR/nhập tay ảnh official** trong giai đoạn này. Chính sách không xác minh được từ nguồn text phải để `TBD`, hoặc mock có provenance riêng; không dùng làm fact trong F0.
