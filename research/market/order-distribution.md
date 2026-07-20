# Research — Phân phối đơn theo giờ/ngày & số liệu tham chiếu cho mock

Ngày nghiên cứu: 2026-07-20 · Trạng thái: đợt 1 · Nguồn: T-001
Quy ước: nguồn gắn **[PROXY]** (dữ liệu quốc tế) chỉ dùng cho **hình dạng phân phối/hệ số**, KHÔNG dùng mức tuyệt đối.

## Đề xuất tham số mock (tổng hợp từ findings — dùng cho T-003)

1. **Hình dạng 24h**: peak sáng 6–9h (đỉnh 7–8h30), peak chiều 17–20h — theo Grab VN official + quy định giờ cao điểm Hà Nội (6h–9h, 16h–19h30). Peak chiều > peak sáng ~1.2–1.5× và giữa trưa KHÔNG tụt sâu ([PROXY] Didi Chengdu/Bắc Kinh). Tối 20–24h giữ cao cho app-hailing (tới ~24% tổng chuyến ở [PROXY] NYC FHV).
2. **Hệ số ngày trong tuần**: ngày thường commute-shape; T6/T7 boost tối muộn 21h–1h; sáng cuối tuần giảm; tổng Thứ Bảy ≥ ngày thường ([PROXY] Chicago CMAP); Thứ Năm/Sáu cao ([PROXY] NYC).
3. **Hệ số thời tiết**: mưa ×~1.2 ([PROXY] Chicago: Uber +22%, Lyft +19%); scale theo cường độ ~+0.6%/mm·h ([PROXY] Hải Khẩu) → mưa to HN 20–50mm/h có thể +12–30%.
4. **Mức tuyệt đối** (nguồn VN): toàn thị trường ~1,45tr chuyến/ngày (Q4/2025); Xanh SM ~1tr chuyến/ngày với >100.000 xe (8/2025) → **~10 chuyến/xe/ngày** trung bình đội xe; tài xế bike full-time **~15–30 cuốc/ngày** (suy từ doanh thu 300–700k/ngày, giá cuốc bike ~15–30k — suy luận, không phải số gốc).
5. **Bike vs Car**: 2 bánh chiếm **61,36%** thị phần chuyến VN 2025 (Mordor); chi tiêu tháng car ≈ 2.4× bike (Rakuten).
6. **Khớp chéo với chính sách Xanh SM** (từ research bonus/pain-points): khung nhân điểm thưởng 6–8h & 16–18h và "cuốc Điểm Vàng" 16h–19h59 — hãng tự xác nhận đây là khung cao điểm → dùng làm anchor cho mock.

## Findings — nguồn Việt Nam

1. **Grab VN định nghĩa giờ cao điểm HN & HCM: 06:00–09:00 và 17:00–20:00** (chương trình giá giờ cao điểm, 14/05/2024). — [grab.com](https://www.grab.com/vn/en/blog/gia-grabbike-re-nhat-tu-giam-them-gio-cao-diem/), **official/high**.
2. **Quy định Hà Nội**: cao điểm sáng 6h–9h, chiều 16h–19h30 (từ 20/10/2020); ùn tắc thực tế 7h–8h30 & 16h–18h30. — [CAND](https://cand.vn/Giao-thong/Ha-Noi-thay-doi-khoang-thoi-gian-gio-cao-diem-tu-20-10-i583608/), **official/high**.
3. **Xanh SM vượt 1 triệu chuyến/ngày, >100.000 xe** (8/2025, sau ~2 năm hoạt động). — [MarketTimes](https://markettimes.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam-87806.html), 03/08/2025, **press/high**.
4. **Q2/2025**: thị trường 4 bánh 97,9tr chuyến/quý (GMV 353,41tr USD); Xanh SM 44,68% thị phần 4 bánh, Grab 36,08%. — [Dân Việt](https://danviet.vn/xanh-sm-can-moc-1-trieu-chuyen-ngay-huong-toi-clb-100-trieu-giao-dich-thang-d1353440.html), 06/08/2025, **press/high**.
5. **Q4/2025**: Xanh SM 51,5% thị phần GMV; toàn thị trường 133,31tr chuyến/quý (~1,45tr/ngày), GMV ~490,72tr USD; Grab 42,64%, Be 5,86%. — [VOV dẫn Mordor](https://vov.vn/doanh-nghiep/them-mot-bao-cao-cho-thay-xanh-sm-vuot-50-thi-phan-goi-xe-cong-nghe-viet-nam-post1267413.vov), 07/02/2026, **press/high**.
6. **Mordor**: thị trường ride-hailing VN 1,06 tỷ USD (2025), CAGR 19,53% (2026–2031); **2 bánh 61,36% thị phần**; app-based 88,82% doanh thu. — [mordorintelligence.com](https://www.mordorintelligence.com/industry-reports/vietnam-ride-hailing-market), **research/medium**.
7. **Rakuten Insight 2025** (n=7.436): Grab 55% người dùng, Xanh SM 32%, Be 9%; 77% đặt ≥3 lần/tháng; use case: xã hội 42%, ăn uống 37%, mua sắm 36%, sự kiện 33%, đi làm 32%, về nhà 30% → demand tối/cuối tuần ngang commute; chi tiêu tháng car 252.101đ vs bike 104.907đ. — [insight.rakuten.com](https://insight.rakuten.com/2025-ride-hailing-app-landscape-in-vietnam/), **research/high**.
8. **Q&Me** (n=300, HN+HCM): ride-hailing ưu tiên khi nhậu/tiệc tối, trời mưa, đi xa; >70% nhắc an toàn. — [qandme.net](https://qandme.net/en/report/ride-hailing-in-viet-nam-usage-expectations.html), **research/medium**.
9. **Thu nhập tham chiếu GrabBike** (sanity check): full-time 8–10h → 300–700k/ngày, 10–18tr/tháng trước chi phí; GrabCar 800k–1,5tr/ngày. — [Sforum](https://cellphones.com.vn/sforum/chay-grab-thu-nhap-bao-nhieu), 09/07/2026, **community/medium**. Ca thật 2020: 12h chạy → 475k doanh thu → ~190k thực nhận (biên dưới lịch sử). — [Znews](https://znews.vn/hien-thuc-cay-dang-cua-giac-mo-chay-grab-kiem-30-trieu-dongthang-post1162784.html), **press/medium**.

## Findings — [PROXY] quốc tế (chỉ dùng hình dạng/hệ số)

10. **Didi (Chengdu/Bắc Kinh)**: peak sáng 7–10h, chiều 17–20h; **peak chiều > peak sáng**; không có đáy sâu giữa trưa. — [Transportation Research Part D](https://www.sciencedirect.com/science/article/abs/pii/S1361920920307823), 2020, **research/medium**. ← proxy chính (châu Á, app-hailing).
11. **NYC TLC 47tr chuyến**: tăng sáng, đi ngang trưa, đỉnh 15–18h ngày thường; Thứ Năm cao nhất. — [Medium/NYC TLC](https://medium.com/@iqramuzaffar2002/the-problem-big-data-eb776fc4791e), **community/medium**.
12. **NYC TLC 2016**: app-based FHV có **24% chuyến trong 20h–24h**; taxi truyền thống đỉnh 18–20h (~9% chuyến tuần); đỉnh tuyệt đối tối Thứ Sáu. — [TLC Magazine](http://tlc-mag.com/jun16_02.html), **press/medium**.
13. **Chicago CMAP (~45tr chuyến TNP)**: đỉnh tối T6/T7 + giờ cao điểm ngày thường; **Thứ Bảy ridership đặc biệt cao**. — [cmap.illinois.gov](https://cmap.illinois.gov/news-updates/new-data-allows-an-initial-look-at-ride-hailing-in-chicago/), 2019, **official/medium**.
14. **Gridwise Chicago (hướng tài xế)**: cuối tuần 22h–3h "BIG hours"; ngày thường 5–10h & 15–18h; sáng CN chậm. — [gridwise.io](https://gridwise.io/blog/chicago/peak-rideshare-driving-times-in-chicago/), 2017, **community/low**.
15. **Mưa**: Chicago — Uber +22%, Lyft +19%, taxi +5%; NYC taxi +20–25% ngày mưa. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2590198225004919), 2025, **research/medium**. Hải Khẩu: +0,59%/1mm·h cường độ mưa. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2214367X21000302), 2021, **research/medium**.

## Gaps (TBD)

1. **Không có phân phối %-theo-giờ công bố cho VN** — hình dạng 24h phải proxy (Didi là proxy chính).
2. Số chuyến Xanh SM tách theo **thành phố** (HN vs HCM) và theo **bike vs car** — chỉ có tổng quốc gia.
3. Số cuốc TB/ngày/tài xế VN không có nguồn chính thức (chỉ suy luận ~10/xe/ngày đội xe; 15–30 full-time bike).
4. Hệ số ngày-trong-tuần **định lượng** cho VN.
5. Hệ số mưa riêng Hà Nội.
6. Khác biệt hình dạng giờ bike vs car tại VN (bike có lệch giờ ăn/giao ngắn?).

## Ghi ý cho thiết kế mock (T-003)

- Generator nên tách: `base_demand(zone) × hour_shape(h) × dow_factor(dow) × weather_factor(rain_mm)` — mỗi thành phần cite nguồn ở trên, gắn nhãn PROXY khi áp dụng.
- Anchor VN cho hour_shape: 2 khung điểm-vàng của chính Xanh SM (6–8h, 16h–19h59) phải là 2 đỉnh.
- Sanity check output: tài xế full-time mock nên rơi vào 15–30 cuốc/ngày, doanh thu 300–700k/ngày.
