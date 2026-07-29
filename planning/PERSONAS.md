# PERSONAS — 5 hồ sơ tài xế mock (Bike, Hà Nội)

Cập nhật: 2026-07-29 · Trạng thái: **ACTIVE** — không còn "nháp chờ review"; 5 persona này là archetype **đang được sim sản xuất** từ SIM-1 (UPDATE-044) trở đi.
Mọi con số là **MOCK** được tổng hợp/suy luận từ `research/` (nguồn ghi trong đó); trường chưa có căn cứ đánh dấu `TBD`.

**⚠ Phân biệt PRODUCT vs SIM (2026-07-29):** persona **PRODUCT** (bảng dưới đây, F0–F3) = **5** (P1–P5). Archetype **SIM** = **7** — sim thêm **P6 "ca sáng sớm"** (tỷ trọng 0.18) và **P7 "ca tối-đêm"** (tỷ trọng 0.12) để phủ khung giờ ngoài 5 persona gốc, định nghĩa tại `src/gsm_sim/archetypes.py`. **ĐA-08 tiêu chí (1b)** (no-harm guard công bằng, `specs/advisor-objective-model-v2.md` §5) yêu cầu báo cáo đủ **P1..P7**, không chỉ 5 persona product.

## Trường hồ sơ chuẩn (nháp schema cho T-011)

`persona_id`, tên gọi, track hợp tác (xe cá nhân platform / RTO thuê-mua xe công ty / nhân viên), thâm niên (tháng), giờ chạy/ngày, ngày/tuần, khung giờ quen, khu vực hoạt động, mục tiêu **driver payout**/tháng, estimated net (optional + completeness + definition version), tỷ lệ nhận đơn, tỷ lệ hoàn thành, điểm thưởng tuần điển hình, quyền lợi đang hưởng (ĐBTN, miễn phí pin, thâm niên/loyalty), am hiểu app (1–5), rủi ro chính, nhu cầu chính với F0–F3.

**Quy ước tiền:** mọi con số mục tiêu dưới đây là **MOCK driver payout**, trừ khi hàng ghi rõ estimated net. Các mức thu nhập tự khai trong research không thống nhất gross/payout/net nên chỉ dùng calibration range, không coi là fact cùng định nghĩa.

## P1 — "Sinh viên part-time" (Minh, 21 tuổi)

| Trường | Giá trị (MOCK) |
| --- | --- |
| Track | Xe cá nhân (Feliz S mua cũ), chiết khấu ~21% |
| Thâm niên | 4 tháng |
| Giờ chạy | 3–4h/ngày (tối 17h–21h) + T7/CN thêm sáng |
| Mục tiêu driver payout | 7–8 triệu/tháng (căn cứ: tự khai ~4h/ngày → ~8tr) |
| Tỷ lệ nhận / hoàn thành | 82% / 95% — **rủi ro**: dưới điều kiện nhận thưởng tuần HN của policy version 12/2025 (85%/85%); threshold hiện hành phải lấy từ Policy KB theo profile/effective date |
| Điểm tuần điển hình | ~350–500 điểm; có thể chạm mốc điểm nhưng **không đủ điều kiện nhận thưởng** nếu acceptance vẫn 82% |
| Am hiểu app | 3/5 |
| Rủi ro chính | Không đủ chuyến lấy thưởng tuần; từ chối đơn kéo tỷ lệ nhận xuống |
| Cần từ hệ thống | F1: chỉ tiêu vừa sức theo quỹ giờ; F0: "tối nay chạy thêm mấy cuốc thì lên mốc 400 điểm?"; F3: cảnh báo tỷ lệ nhận |

## P2 — "Trụ cột full-time RTO" (Hùng, 32 tuổi)

| Trường | Giá trị (MOCK) |
| --- | --- |
| Track | **MOCK RTO track assumption**: 60k/ngày, chia 90% năm 1, sau 24 tháng sở hữu xe — chưa được dùng chung với policy Bike Platform nếu chưa map đúng policy bundle |
| Thâm niên | 7 tháng |
| Giờ chạy | 9–10h/ngày, 6 ngày/tuần; đủ 2 khung cao điểm |
| Mục tiêu driver payout | 16–18 triệu/tháng (căn cứ: tự khai 8–10h → 15–20tr) |
| Tỷ lệ nhận / hoàn thành | 93% / 97% |
| Điểm tuần điển hình | MOCK 1.100–1.400 theo bảng KV1 được nghiên cứu; hệ thống phải lấy mốc thật từ policy bundle đúng effective date |
| Quyền lợi | MOCK RTO benefit: miễn phí đổi pin theo chương trình tham chiếu; phí thuê 60k/ngày là known cost nếu policy bundle xác nhận |
| Am hiểu app | 4/5 |
| Rủi ro chính | Theo đuổi mốc thưởng cao bằng cách kéo dài giờ → mệt mỏi; kẹt hợp đồng 24 tháng |
| Cần từ hệ thống | F1: lộ trình thưởng versioned; F2: giờ nghỉ/sạc tránh khung demand cao; F3: estimated net sau known phí thuê |

## P3 — "Top performer xe riêng" (chị Liên, 38 tuổi)

| Trường | Giá trị (MOCK — mô phỏng theo case báo chí 07/2025) |
| --- | --- |
| Track | Xe cá nhân Feliz S (34,9tr), chiết khấu ~21% |
| Thâm niên | 14 tháng |
| Giờ chạy | 10–11h/ngày; quy tắc riêng "hết 2 pack pin mới nghỉ"; sạc ~3h giữa trưa kết hợp nghỉ ăn |
| Mục tiêu driver payout | 22–23 triệu/tháng |
| Tỷ lệ nhận / hoàn thành | 96% / 98% |
| Điểm tuần | MOCK >1.400 theo bảng KV1 tham chiếu; event/điểm vàng phải lấy từ policy bundle còn hiệu lực |
| Quyền lợi | Thâm niên/Loyalty (mức Bike cụ thể `TBD`); tự chịu khấu hao xe |
| Am hiểu app | 5/5 |
| Rủi ro chính | Quá tải giờ chạy; phụ thuộc sức khỏe; nhạy cảm khi chính sách đổi (mốc điểm/tỷ lệ chia) |
| Cần từ hệ thống | F0: delta chính sách mới vs cũ ngay khi đổi; F3: phân tích vi mô (cuốc/giờ, điểm/giờ theo khung) |

## P4 — "Tân binh mới dùng app" (Đạt, 24 tuổi) ← persona mới

| Trường | Giá trị (MOCK) |
| --- | --- |
| Track | **MOCK candidate RTO track** tham chiếu chương trình "Vào Xanh, Tặng Xe"; cọc/phí chỉ dùng nếu policy bundle/cohort được xác nhận |
| Thâm niên | Tuần thứ 2. **MOCK eligibility assumption:** có thể thuộc cohort ĐBTN 3 tháng đầu; hệ thống phải map đúng track/cohort/policy bundle trước khi kết luận đủ điều kiện |
| Giờ chạy | 8h/ngày nhưng chưa biết chọn khung giờ; hay online lệch khung cao điểm |
| Mục tiêu driver payout | Chưa biết đặt — dùng default của hệ thống |
| Tỷ lệ nhận / hoàn thành | 74% / 90% — gần/có thể dưới ngưỡng tùy policy version; phải truy xuất Policy KB thay vì hard-code |
| Điểm tuần | <400 (chưa hiểu cơ chế điểm theo policy version hiện hành) |
| Am hiểu app | 1–2/5; chưa biết quy trình hủy; **"Hủy chuyến hợp lệ" hiện chỉ có nguồn official cho Taxi/Car, chưa xác nhận cho Bike** |
| Rủi ro chính | Mất quyền lợi nếu map nhầm track/cohort hoặc thiếu điều kiện; bị tác động bởi ngưỡng policy hiện hành mà chưa hiểu |
| Cần từ hệ thống | F0 dạng onboarding: giải thích ĐBTN + điểm thưởng bằng ngôn ngữ đơn giản; F1: checklist "hôm nay cần gì để giữ ĐBTN"; F3: 1 lời khuyên duy nhất/ngày |

## P5 — "Lão làng" (bác Sơn, 45 tuổi) ← persona mới

| Trường | Giá trị (MOCK) |
| --- | --- |
| Track | Xe cá nhân, chiết khấu ~21%; cân nhắc có nên đổi xe mới theo chương trình RTO không |
| Thâm niên | 26 tháng — có thể thuộc nhóm thâm niên/Loyalty, nhưng mức/điều kiện **Bike = `TBD`**; số Car không được dùng làm fact Bike |
| Giờ chạy | 8–9h/ngày, nghỉ CN; khung giờ và điểm đứng thuộc lòng (kinh nghiệm trước cả app) |
| Mục tiêu driver payout | 15–17 triệu/tháng, ưu tiên ổn định hơn max |
| Tỷ lệ nhận / hoàn thành | 97% / 99% |
| Điểm tuần | MOCK 900–1.200; ưu tiên ổn định, không cố ép lên mốc cao nhất của policy snapshot tham chiếu |
| Am hiểu app | 3/5 — thao tác tốt việc quen, ngại tính năng mới |
| Rủi ro chính | **Kinh nghiệm cũ bị lỗi thời khi chính sách đổi** (mốc điểm, khung giờ vàng thay đổi mà bác không để ý); bỏ lỡ thưởng mới |
| Cần từ hệ thống | F0: chủ động báo "chính sách X vừa đổi, ảnh hưởng tới bác thế nào" (đúng US-F0-03); F1: so sánh "thói quen hiện tại vs lịch tối ưu" — chỉ đề xuất thay đổi nhỏ |

## Ghi chú thiết kế

- **⚠ Cập nhật 2026-07-24 (risk-framing):** cơ chế **phạt tỷ lệ nhận <70% đã bị BỎ** (Vận Doanh 23/02/2026) — xem [research/policy/policy-refresh-2026-07-24.md](../research/policy/policy-refresh-2026-07-24.md). Vì vậy rủi ro "tỷ lệ nhận thấp" của P1 (82%) / P4 (74%) **KHÔNG còn là "bị phạt"** mà là: (1) **không đủ eligibility nhận thưởng tuần** (HN ≥85% nhận & hoàn thành, version 12/2025), và (2) **không đạt khoán tuần → truy thu 20-40%**. Các ô "rủi ro"/"tỷ lệ nhận" dưới đây vốn đã version-aware (dẫn Policy KB theo effective date) nên GIỮ NGUYÊN, nhưng khi F1/F3 diễn giải phải nói đúng: *lỡ thưởng / truy thu khoán*, không nói *bị phạt vì tỷ lệ nhận*.
- P4/P5 thể hiện 2 chiều **kinh nghiệm dùng app** và **thâm niên → tiền thưởng** như Cường yêu cầu; P1–P3 phủ trục **quỹ giờ** (part-time → full-time → top) và **track hợp tác**.
- Thứ tự triển khai đề xuất: P4 và P2 trước (đại diện 2 nhu cầu F0/F1 rõ nhất), rồi P1, P5, P3.
- Research đợt 2 cung cấp các **policy snapshots có ngày/market** — xem `research/policy/bonus-programs.md`. Persona dùng chúng làm MOCK calibration, không hard-code thành policy hiện hành. `TBD` thật sự: mức thâm niên/Loyalty Bike; % chia chi tiết theo khung giờ; mapping quyền lợi theo Platform/RTO/cohort.
