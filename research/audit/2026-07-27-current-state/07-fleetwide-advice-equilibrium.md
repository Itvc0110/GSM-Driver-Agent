# Khuyên DIỆN RỘNG thì sao? — đo cân bằng hệ thống, công bằng và tác động lên khách

Ngày: 2026-07-27 · Câu hỏi của Cường: *"với việc khuyên diện rộng, các tài xế có đều được tăng
thu nhập, hay sẽ gây ra hỗn loạn, người tăng người giảm, mất cân bằng distribution do sạc cùng
giờ, săn cùng 1 khu nhiều khách, từ chối đơn hàng cũng gây ảnh hưởng đến khách hàng?"*

**Trạng thái trước phiên này**: hồ sơ `02`/`04`/`05` có ghi *fairness / fleet effect* như hạng mục
**cần kiểm**, nhưng **chưa ai từng đo**. Cờ `advice.coverage: all` tồn tại trong sim từ lâu và
**chưa từng được chạy**. Đây là lần đầu có số.

## 1. Thiết kế thí nghiệm

`run_once` cùng seed, hai kịch bản: **A** = không advice · **B** = `coverage: all` (advice cho
**toàn bộ 90 tài xế**), **kênh MẶC ĐỊNH của config**.

> **ĐÍNH CHÍNH ATTRIBUTION (viết ngay khi phát hiện, cùng phiên):** bản nháp đầu của hồ sơ này
> ngầm quy tác hại cho `accept_lift`. **SAI.** Kênh mặc định trong `configs/pilot_dongda.yaml` là
> `shift_plan: true` · **`accept_lift: false`** · `shift_extend: false` · `rest_window: false`.
> Nghĩa là toàn bộ tác động hệ thống đo dưới đây đến từ **`shift_plan` (S2 ShiftDP → REST/SWAP/END)**,
> KHÔNG phải `accept_lift`. Hai hồ sơ đo hai thứ khác nhau:
> - [`06`](06-why-advice-loses-money.md) = **một** tài xế, kênh `all` (bật thủ công) → thủ phạm `accept_lift`;
> - `07` (đây) = **toàn đội**, kênh mặc định → thủ phạm `shift_plan`.
>
> Điều này khiến kết luận **nặng hơn**, không nhẹ đi: kênh đang BẬT mặc định — thứ đang chạy
> trong mọi demo — chính là kênh gây hại ở quy mô đội.

> **⚠ ĐỌC KÈM [`09`](09-baseline-30seed-coverage-all.md) — đã chạy lại ở 30 seed (2026-07-27).**
> Kết quả 30 seed **giữ nguyên hướng nhưng làm YẾU đi** phần kết luận hệ thống của hồ sơ này:
> `served_rate` giảm ở **16/30** seed (không phải 6/10 ≈ 60%) và đơn hết hạn **+4,8/ngày với CI
> chứa 0**. Ngược lại, tác hại ở **tầng cá nhân** trở nên **có ý nghĩa thống kê** (payout
> −17.310đ, CI [−29.294, −5.820]). Khi trích dẫn, dùng số của `09`.

Quy mô: **10 seed (1000-1009)**. Đo ở mức HỆ THỐNG, không phải một tài xế: `served_rate`, đơn hết
hạn (khách không được phục vụ), phân phối payout theo percentile, hệ số Gini, mật độ đổi pin theo
giờ, thời gian chờ tủ pin.

## 2. Kết quả (10 seed)

| chỉ số | kết quả |
|---|---|
| **served_rate** (tỷ lệ đơn được phục vụ) | **GIẢM 6/10** seed · tăng 3/10 · hoà 1/10 · TB **−0,0072** |
| **đơn HẾT HẠN** (khách bị bỏ) | **TĂNG 6/10** seed · giảm 3/10 · TB **+7,9 đơn/ngày** |
| median payout tài xế | tăng 5/10 · giảm 4/10 · TB +2.760đ |
| **Gini** (bất bình đẳng) | **TĂNG 5/10** · giảm 4/10 |
| **% vị trí percentile tăng thu nhập** | TB **33/90 ≈ 36%** (min 0 · max 54/90) |
| mật độ đổi pin/giờ · chờ tủ pin | **không đổi đáng kể** — lo ngại "dồn sạc cùng giờ" KHÔNG xảy ra ở config này |

Seed 1007 là ca đối chứng tự nhiên: advice **không kích hoạt** (0 thay đổi trên mọi chỉ số) —
xác nhận đo đúng, không phải nhiễu ngẫu nhiên.

## 3. Kết luận thẳng

**Không có chuyện "khuyên rộng thì ai cũng tăng".** Trung bình chỉ **36% vị trí percentile** tăng
thu nhập — tức **phần lớn tài xế không được lợi, nhiều người bị thiệt**. Đây là *fallacy of
composition* kinh điển: lời khuyên tối ưu cho MỘT người (nhận thêm đơn, chạy thêm giờ) mất tác
dụng khi TẤT CẢ cùng làm, vì tổng cầu là hữu hạn.

**Nghiêm trọng hơn — khách hàng bị ảnh hưởng thật.** `served_rate` giảm ở 6/10 seed và số đơn hết
hạn **tăng trung bình ~8 đơn/ngày**. Advice không tạo thêm cuốc; nó **xáo trộn phân bố cung** làm
matching kém đi. Đúng lo ngại Cường nêu, và nó **định lượng được**.

**Về hai lo ngại cụ thể**:
- "săn cùng một khu" → có, gián tiếp: phân phối lại + matching kém đi.
- "dồn sạc cùng giờ" → **chưa xảy ra** ở config này. Đo trực tiếp đỉnh theo giờ (seed 1002/1003):
  `swap_peak` 11→11 và 11→10; `rest_peak` 34→32 và 34→35 — không có dấu hiệu dồn cục.
  ⇒ Tác hại KHÔNG đến từ "cùng lúc đi sạc/nghỉ", mà đến từ việc **90 tài xế cùng nhận một logic
  lập lịch** làm phân bố cung lệch đi so với thế cân bằng tự nhiên. Đây là dạng herding tinh vi
  hơn: không dồn về một điểm, nhưng cùng *rời khỏi* thị trường vào những khoảng giống nhau.

## 4. Vì sao — nối với finding 06

Hồ sơ [`06`](06-why-advice-loses-money.md) cho thấy ở mức MỘT tài xế, `accept_lift` gây lỗ vì mô
hình coi năng suất là hằng số ngoại sinh. Ở mức TOÀN ĐỘI, khuyết điểm đó cộng dồn thành **thiếu
vòng phản hồi cân bằng thị trường**: không solver nào biết rằng lời khuyên của nó, khi nhân lên 90
lần, làm đổi chính cái môi trường mà nó dựa vào để tính.

Đây là **giới hạn mô hình hoá**, không phải bug code — đúng như Cường nhận định *"mô hình hoá bài
toán chưa đủ tốt hoặc sim chưa đủ chi tiết"*.

## 5. Hệ quả bắt buộc

0. **Kênh đang bật mặc định (`shift_plan`) là kênh gây hại ở quy mô đội** — nghiêm trọng hơn
   `accept_lift` (vốn đã tắt). Không được coi "đã tắt accept_lift" là đã an toàn.
1. **Mọi con số A/B đơn-tài-xế từ trước tới nay đều là cận trên lạc quan** — chúng đo trong thế
   giới mà chỉ một người nghe lời. UPDATE-047/051/056 và sweep D-SIM-06 đều thuộc diện này. Không
   được trích dẫn như hiệu quả sản phẩm thật.
2. **Guardrail hiện tại không đủ**: nó so served_rate A vs B trong ca *một* tài xế được advice —
   nơi tác động hệ thống gần như bằng 0 theo thiết kế. Guardrail thật phải chạy ở `coverage: all`.
3. **Đề xuất ĐA-08 (mới)**: chỉ tiêu chấp nhận của advisor phải gồm **ràng buộc hệ thống**:
   `served_rate` không giảm và đơn hết hạn không tăng ở `coverage: all`, ≥30 seed — trước khi bất
   kỳ kênh nào được coi là "có giá trị".
4. Kết nối ĐA-07 (từ hồ sơ 06): hai đề xuất này là một cặp — ĐA-07 sửa mức cá nhân (chi phí cơ
   hội), ĐA-08 sửa mức hệ thống (ràng buộc cân bằng).

## 6. Cái CHƯA kiểm (trung thực)

- 10 seed đủ chỉ ra **hướng và cơ chế**, **chưa đủ** cho khoảng tin cậy (chuẩn ≥30 seed).
- Chỉ chạy `coverage: all` với kênh mặc định; **chưa** quét theo tỷ lệ phủ (`share` 10/25/50%) —
  rất có thể tồn tại ngưỡng phủ mà lợi ích cá nhân chưa bị triệt tiêu.
- Chưa tách đóng góp của từng kênh ở chế độ diện rộng (mới làm ablation ở mức 1 tài xế).
- Chưa đo tác động lên **khách**: thời gian chờ xe, tỷ lệ huỷ do chờ lâu — mới đo gián tiếp qua
  đơn hết hạn.
