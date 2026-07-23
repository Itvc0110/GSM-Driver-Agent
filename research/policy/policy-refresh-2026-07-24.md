# Research — Policy refresh đợt 3 (2026-07-24): khoán tuần, bỏ phạt ≤70%, clawback

Ngày nghiên cứu: **2026-07-24** · Trạng thái: đợt 3 (refresh) · Người thực hiện: AI agent (yêu cầu Cường "research vòng nữa, tìm flaw, enrich")
Phương pháp: web research official greensm.com/xanhsm.com + cross-check ngày hiệu lực. Mỗi con số gắn nguồn/ngày/confidence. **Số khóa trong ảnh official → để `image-locked/TBD`, giải bằng data thật GSM (partnership), KHÔNG OCR.**

> Mục đích: research đợt 1/2 (`bonus-programs.md`, `pain-points.md`, dated 2026-07-20) **lỗi thời & thiếu** ở một thay đổi lớn. File này đính chính + bổ sung; KHÔNG xóa file cũ (chúng là snapshot có ngày). Corpus T-004 (Khánh) cũng thiếu phần này — xem "Gap cho corpus owner".

## 0. TL;DR — 3 đính chính quan trọng nhất

1. **Bỏ phạt tỷ lệ nhận/hoàn thành ≤70%** kể từ **Chính sách Vận Doanh 23/02/2026** (toàn quốc). Repo/corpus đang encode phạt <70% (nguồn 15/07/2025) → **có thể trả F0 SAI**. Xem F-1/F-2.
2. **Mô hình chuyển sang KHOÁN TUẦN**: doanh số tính theo **tuần** (không theo ngày); không đạt khoán → **truy thu 20%** phần thiếu (HN/HCM 04/05/2026 nhắc "tới 40%") cấn trừ ví. Đây là **cơ chế kinh tế MỚI** solver chưa mô hình. Xem F-1/F-3.
3. **Mâu thuẫn official chưa reconcile**: Vận Doanh 23/02 (bỏ phạt) vs Bộ Quy Tắc Ứng Xử 05/06/2026 (vẫn liệt kê phạt <70%, Nhóm 4). F0 phải cite **đúng doc + ngày**, không khẳng định tuyệt đối. Xem F-2.

## 1. Chính sách Vận Doanh mới (nguồn official, trích text)

**[Toàn quốc] Cập nhật chính sách vận doanh — hiệu lực 23/02/2026** ([greensm.com](https://www.greensm.com/vn-vi/news/cap-nhat-chinh-sach-van-doanh-moi-danh-cho-bac-tai-xanh-bike), **official/high**):
- **Tính doanh số theo TUẦN** thay vì theo ngày.
- **"Không áp dụng hình thức xử phạt khi tỷ lệ nhận chuyến và tỷ lệ hoàn thành chuyến ≤ 70%"** — bỏ phạt acceptance/completion.
- **Truy thu khi không đạt khoán tuần**: mức **20% phần doanh số chưa đạt**, cấn trừ từ ví tài xế.
- Vẫn phải đảm bảo **tổng doanh số tối thiểu/tuần + số ngày vận doanh tối thiểu** để nhận thưởng tuần (kể cả khi nghỉ 1–2 ngày).

**[Hà Nội & TP.HCM] Cập nhật chính sách vận doanh — 04/05/2026** ([greensm.com](https://www.greensm.com/vn-vi/news/cap-nhat-chinh-sach-van-doanh-moi-tai-ha-noi-tp-hcm), **official/medium** — số chính trong ảnh):
- Nhắc cơ chế điều chỉnh truy thu **"tới 40%"** (Q&A) — ⇒ **clawback_rate là tham số versioned/market** (20% toàn quốc vs tới 40% HN/HCM), không phải hằng số.
- "Cơ chế này không ảnh hưởng đến Bác Tài duy trì hoạt động đều đặn."
- **Con số khoán tuần tối thiểu + số ngày tối thiểu = image-locked.**

## 2. Bảng timeline version chính sách (nền cho Policy KB versioned)

| Ngày hiệu lực | Doc / chủ đề | Track/Market | Điểm chính | Confidence |
|---|---|---|---|---|
| 06/11/2024 | Thu nhập Bike | HCM/BD/ĐN | chia sẻ "tới 91%" theo khung giờ (LỖI THỜI) | official/high |
| 15/07/2025 | Kỷ luật acceptance | Bike | <50% ép auto-accept 23h59; <70% phạt 100–200k/tuần | press/medium (**superseded 23/02/2026**) |
| 01/08/2025 | Thưởng Bike Platform | toàn quốc | thưởng theo khung cao/thấp điểm (gồm Ngon/Food) | official/high |
| 30/10/2025 | Bộ QTƯX Bike Platform | Platform | Nhóm 4: <70% phạt | official/high |
| 01/12/2025 | Thêm mốc điểm mới | HN/HCM/BD/ĐN | thêm mốc-2 thưởng tuần; điều kiện điều chỉnh (bảng ảnh) | official/high |
| 12/2025 | PDF Q&A thu nhập | HN/HCM/BD/ĐN | HN ≥5 ngày + nhận ≥85% + hoàn thành ≥85% (mốc 2: 4 ngày); HCM/BD/ĐN 90/90; điểm **5-10-15-20-30 theo dịch vụ**; điểm tính theo **thời điểm khách ĐẶT** | official/high |
| 15/12/2025 | Bộ QTƯX Bike (bản cập nhật) | Bike | version conduct nối tiếp | official/high |
| **23/02/2026** | **Vận Doanh (khoán tuần)** | **toàn quốc** | **khoán tuần; BỎ phạt ≤70%; truy thu 20%** | **official/high** |
| 02/03/2026 | Thu nhập Bike | HN/HCM/ĐN(+HP/NA/BR-VT) | chia sẻ **tới 75%**; thưởng tuần tới 1,2tr; thâm niên/Loyalty giữ nguyên | official/high |
| 30/03/2026 | ĐBTN 3 tháng đầu | HN/HCM (+tỉnh) | FT 600k/ngày (≥15 cuốc HN/HCM), PT 360k; bù 36k/cuốc; ≥1 khung cao điểm/ngày | official/high |
| 04/05/2026 | Vận Doanh + Điểm Vàng | HN/HCM | Điểm Vàng 16h–19h59 T2–T6; truy thu "tới 40%" | official/medium |
| 05/06/2026 | Bộ QTƯX Bike | Bike | 4 nhóm vi phạm; **Nhóm 4 vẫn ghi <70% phạt** ⚠ mâu thuẫn 23/02 | official/high |
| 15/06/2026 | Ưu đãi gia nhập | Bike Platform | đồng phục 810k + miễn phí sạc; giữ quà ≥200 chuyến/tháng×2 | official/medium |

## 3. Flaws + reconcile

- **F-2 mâu thuẫn phạt <70%**: Vận Doanh 23/02/2026 nói **bỏ** phạt; QTƯX 05/06/2026 (ngày SAU) vẫn **liệt kê** phạt Nhóm 4. **Giả thuyết** (chưa xác nhận): cơ chế phạt-theo-ngày được **thay bằng truy thu khoán-tuần**, còn văn bản QTƯX là bản hợp nhất kỷ luật lag chưa gỡ mục cũ. **Không kết luận chắc** — F0 phải trả kèm cite doc+ngày và cờ "có nguồn khác biệt, kiểm tra app". **Cần data thật GSM** (bản policy đang active cho từng driver) để chốt.
- **F-4 điểm theo dịch vụ**: khung giờ cho **10 điểm (peak 6–8h·16–18h) / 5 điểm (thường)** vẫn xuất hiện ở bài HN hiện hành; song song có **5-10-15-20-30 theo dịch vụ** (Bike/Food/Express, PDF Q&A 12/2025). ⇒ điểm = f(khung_giờ) **×/theo** service_type. Schema `policy_bundle.points` hiện chỉ có trục peak/normal → **thiếu chiều service_type**.
- **Xác nhận đúng**: chia sẻ doanh số **75%** là hiện hành (02/03/2026). "91%" là số 2024 HCM **lỗi thời**, đừng dùng.

## 4. Image-locked → giải bằng DATA THẬT GSM (partnership), không OCR

Các số công khai chỉ có trong ảnh/PDF; partnership cho quyền data thật → nên pull thay vì đoán:
1. **Doanh số khoán tuần tối thiểu** (VND/tuần) theo market/track + **số ngày vận doanh tối thiểu**.
2. **clawback_rate** thực tế đang active (20% vs tới 40%) theo market.
3. **Bảng mốc điểm → thưởng tuần** bản mới nhất (sau khi "thêm mốc điểm" 01/12/2025).
4. **Điểm/cuốc theo service_type** (Bike/Food/Express) chính xác.
5. **Thâm niên/Loyalty Bike** (mức/điều kiện) — TBD kéo dài từ đợt 1.
6. Cohort/điều kiện **ĐBTN** còn hiệu lực sau 07/2026.

## 5. Ghi ý downstream (chi tiết trong DEFERRED F-1..F-6)

- **MODEL GAP**: mô hình kinh tế đổi từ "phạt acceptance theo ngày" → **khoán tuần + truy thu 20-40%**. S1/S2 chưa mô hình quota tuần & clawback → ứng viên solver mới / mở rộng S1 (T-039). "Thiếu tiến độ khoán tuần" là bài toán feasibility gần S1 nhưng đơn vị = **doanh số tuần**, không phải điểm.
- **SCHEMA GAP**: `policy_bundle.points` cần `service_type`; thêm `weekly_quota`/`clawback_rate` versioned.
- **PERSONA**: risk P1/P4 "acceptance <ngưỡng = phạt" cần reframe quanh **eligibility thưởng (≥85%)** + **đạt khoán tuần**, không phải phạt tuyệt đối.
- **CORPUS T-004** (Khánh): thêm record Vận Doanh 23/02/2026 + đánh dấu mâu thuẫn phạt để F0 cite đúng version.

## 6. Nguồn (official, đã fetch/verify 2026-07-24)

- Vận doanh toàn quốc 23/02/2026 — https://www.greensm.com/vn-vi/news/cap-nhat-chinh-sach-van-doanh-moi-danh-cho-bac-tai-xanh-bike
- Vận doanh HN/HCM 04/05/2026 — https://www.greensm.com/vn-vi/news/cap-nhat-chinh-sach-van-doanh-moi-tai-ha-noi-tp-hcm
- Bộ QTƯX Bike 05/06/2026 — https://www.greensm.com/vn-vi/news/cap-nhat-bo-quy-tac-ung-xu-danh-cho-doi-tac-tai-xe-bike
- Thêm mốc điểm 01/12/2025 — https://www.greensm.com/vn-vi/news/chinh-sach-thuong-xanh-sm-bike-tai-ha-noi-tphcm-binh-duong-dong-nai
- Thu nhập 75% 02/03/2026 — https://www.greensm.com/vn-vi/news/chinh-sach-thu-nhap-tai-xe-xanh-sm-bike-ha-noi-tphcm-binh-duong-dong-nai
- ĐBTN — https://www.greensm.com/vn-vi/news/chinh-sach-dam-bao-thu-nhap-cho-green-bike-platform

**Guardrail giữ nguyên**: số community ≤ medium; số image-locked = TBD; mọi con số vào sản phẩm phải qua Policy KB versioned + citation; không hard-code.
