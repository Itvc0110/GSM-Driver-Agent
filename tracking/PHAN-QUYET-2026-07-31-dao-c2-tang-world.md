# PHÁN QUYẾT 2026-07-31 — đảo C2 ở TẦNG WORLD, giữ nguyên ở tầng advisor/báo cáo

Trạng thái: **THỬ NGHIỆM — Cường định hướng 2026-07-31**: *"Việc đảo C2 nên được coi như 1
thử nghiệm - xem có thể khai thác nếu có ích không - do đã có phán quyết từ trước."*
⇒ HỆ QUẢ THI HÀNH: (1) phán quyết 2026-07-29 **GIỮ HIỆU LỰC MẶC ĐỊNH** — văn bản này KHÔNG
thay thế nó, chỉ mở một nhánh thí nghiệm; (2) E11 là EXPERIMENT — không phải chương trình
chính, **không ưu tiên** (chỉ đạo cùng ngày: *"tập trung hoàn thành kế hoạch dang dở, fix
lỗi thay vì mở rộng sim"*); (3) mọi kết quả E11 nếu chạy sau này mang nhãn THỬ NGHIỆM, không
tự động đổi ranh giới sản phẩm. Khung BA RANH GIỚI + 6 điều kiện dưới đây là điều kiện của
NHÁNH THỬ NGHIỆM đó.
Thay thế MỘT PHẦN: `PHAN-QUYET-2026-07-29-diem3-met-nghi.md` + spec `advisor-objective-model-v2`
§1.2b. Bối cảnh: chỉ đạo Cường 2026-07-31 *"thiết kế nghỉ phải đi kèm thiết kế mệt → giảm hiệu
suất → việc khuyên nghỉ phải đem lại giá trị (trong sim, và thực tế). Thực tế khi triển khai
AI chỉ GỢI Ý (nhẹ hơn khuyên) nghỉ khi thấy tài xế làm quá sức"* (kèm ghi chú: là thắc mắc +
hướng hiểu, mời debate — không phải lệnh).

## 1. Phán quyết

**ĐẢO trụ (a) của phán quyết cũ Ở TẦNG WORLD — world được phép mô hình mệt→hiệu-suất, như một
TRỤC QUÉT không hiệu chuẩn. GIỮ NGUYÊN trụ (a) ở tầng advisor và tầng báo cáo. GIỮ NGUYÊN
TOÀN BỘ trụ (b).**

## 2. Lỗ trong lập luận cũ (vì sao đảo — không phải vì "dữ liệu mới")

Phán quyết cũ coi "không mô hình hoá" là lựa chọn trung lập. Sai:

> **Không mô hình = mô hình với β=0. β=0 cũng là một lựa chọn hiệu chuẩn — và là lựa chọn
> THIÊN VỊ CHỐNG NGHỈ.**

- World β=0 làm mọi can thiệp TĂNG nghỉ trông như chi phí thuần (gợi ý nghỉ không bao giờ
  "đáng") và mọi can thiệp HOÃN nghỉ trông miễn phí. Chính phán quyết cũ đã thừa nhận: dưới
  world có mệt, kênh hoãn sẽ ÂM HƠN — tức world hiện hành đang NỊNH kênh hoãn.
- Ngoài đời `∂payout/∂F ≠ 0` là sự thật của lãnh thổ. Từ chối vẽ nó lên bản đồ không xoá nó —
  chỉ làm sim mù, và mù đúng theo hướng có hại cho tài xế. Thế giới "an toàn đạo đức" hoá ra
  là thế giới thân-vắt-sức.
- Nỗi sợ thật (advisor mặc cả sức khoẻ lấy tiền) nằm ở tầng ADVISOR/BÁO CÁO. Trong world có
  mệt, tối ưu tiền và nghỉ-hợp-lý phần lớn CÙNG CHIỀU; phần còn lệch được trám bằng ràng buộc
  cứng (`rest_min_per_4h`) + trần hoãn KHOÁ (`POLICY_LOCKED_KEYS`, có thật từ 2026-07-31).

## 3. Cái gì SỐNG SÓT từ phán quyết cũ (không được quên khi trích)

1. **Trụ (b) nguyên vẹn**: 0 dữ liệu mệt/tai nạn ⇒ CẤM vĩnh viễn claim điểm; chỉ được báo
   Δ(β) có điều kiện; lưới β khoá prereg TRƯỚC khi đo; CẤM chọn β theo Δ.
2. **"Sức khoẻ không phải biến để TỐI ƯU"** giữ nguyên nghĩa ở tầng advisor: advisor MÙ với
   F/latent — trigger gợi ý nghỉ chỉ đọc QUAN SÁT ĐƯỢC (work_span/online_min — tầng 5).
   Enforce bằng scanner cơ chế 2 (manifest class `WORLD_PHYSIOLOGY` cho world, advisor đọc
   F vẫn ĐỎ).
3. **Không quy tiền**: cột sức khoẻ tách vĩnh viễn khỏi cột tiền trong mọi artifact; tiền của
   nudge gọi là "bảo toàn thu nhập (điều kiện theo β)".
4. LƯỢNG nghỉ = ràng buộc cứng; ba lan can `should_defer_rest` nguyên bit; tầng 5 canh.

## 4. Sáu điều kiện ràng (điều kiện thi hành của phán quyết này)

(1) Phase A — POLICY_LOCKED_KEYS · scanner AST · guardrail tầng 5 — PHẢI xanh trước (đã xong
2026-07-31, UPDATE-111); (2) lưới β khoá prereg trước khi đo, β=0 bit-identical có test;
(3) advisor mù latent — scanner enforce; (4) kỷ luật báo cáo hai cột; (5) nudge là GỢI Ý
(coin adherence riêng thấp hơn — quét, cadence + dismissed-window, không nói khi chở khách);
(6) chính văn bản này — đảo tường minh, không ghi đè im lặng.

## 5. Giả thuyết giá trị (đặt TRƯỚC khi đo — E11 sẽ kiểm)

- V1 bảo toàn thu nhập: nudge nghỉ tại TRŨNG CẦU giữ "pin người" cho giờ vàng 17–20h ⇒
  Δ(β) > 0 với β > 0; Δ(0) ≈ −chi phí nhỏ. Kênh HOÃN âm dần theo β (kỳ vọng ghi trước).
- V2 sức khoẻ: rest_min_total ↑, work_span p90 ↓ — không quy tiền.
- V3 niềm tin (thực tế, sim không đo được — ASSUMPTION, trục UX §12 PROACTIVE CARDS).
- V4 nền tảng/pháp lý: cảm biến quá sức sẵn sàng nếu quy định mở rộng sang 2 bánh.

⚠ Kỹ thuật quyết định (đã kiểm): `online_min` GỘP cả thời gian nghỉ (world.py — "chờ + serve
+ charge") — đơn điệu, nghỉ không hồi. E11 phải dựng **liều-có-hồi-phục riêng** (tích khi làm
việc, hồi khi rest/charge ≥ ngưỡng); dùng `online_min` làm liều sẽ đo ra "số 0 giả" và kết
luận nhầm "gợi ý nghỉ vô ích". `online_min` của bản năng giữ nguyên từng bit.

## 6. Phạm vi hiệu lực

Phán quyết này MỞ CỬA cho spec E11 (world-có-mệt + kênh `rest_nudge`) đi vào plan mode; nó
KHÔNG tự phê duyệt E11 — spec + prereg E11 vẫn qua plan mode duyệt riêng. Bảng "Có thật chưa?"
§1.2b cập nhật theo Phase A; phần văn bản "C2 HUỶ VĨNH VIỄN ở mọi tầng" của §1.2b được thay
bằng tham chiếu tới văn bản này khi Cường xác nhận verdict.
