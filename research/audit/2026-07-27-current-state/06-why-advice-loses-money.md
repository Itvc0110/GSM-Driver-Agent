# Vì sao "làm theo Advisor" ra ÍT tiền hơn tự làm — truy nguyên bằng ablation

Ngày: 2026-07-27 · Nguồn: **Cường thử nghiệm trên UI và báo lại**. Đây là finding MỚI, chưa nằm
trong hồ sơ `01`–`05` và cũng chưa có trong audit 2026-07-26.
Loại: **MODEL GAP (CAO)** — không phải bug code; solver chạy đúng như thiết kế, nhưng thiết kế
bỏ sót một vòng phản hồi.

## 1. Tái lập (engine, không qua UI)

`run_pair` CRN, kênh `all`, tài xế đích P4, seed 1000-1004:

| seed | A tự làm | B theo advisor | Δ | advice events | thưởng A→B | cuốc A→B |
|---|---|---|---|---|---|---|
| 1000 | 322.501 | 282.501 | **−40.000** | 17 | 0→0 | 12→10 |
| 1001 | 322.501 | 282.499 | **−40.002** | 18 | 0→0 | 13→9 |
| 1002 | 335.198 | 335.198 | 0 | 18 | 30.000→30.000 | 13→13 |
| 1003 | 322.502 | 352.502 | +30.000 | 17 | 0→**30.000** | 12→13 |
| 1004 | 327.393 | 302.500 | **−24.893** | 17 | 0→0 | 16→14 |

**LỖ 3/5 · LỜI 1/5 · HOÀ 1/5.** Quy luật lộ ra ngay: seed nào **chạm được mốc thưởng** thì advice
có lời (1003), seed nào **không chạm** thì advice chỉ gây hại.

## 2. Cơ chế — ngược hẳn giả thuyết ban đầu

Giả thuyết tự nhiên: "advisor bảo nhận thêm cuốc xấu". **Sai.** Số đo seed 1000:

| | A tự làm | B advisor |
|---|---|---|
| được CHÀO | 18 đơn | **12 đơn** (ít hơn 6) |
| nhận | 13 | 12 |
| hoàn thành | 12 | 10 |
| pickup TB | 1,20 km | 1,00 km |
| gross/cuốc TB | 23.079đ | 24.563đ |
| **thời gian sạc** | 62 phút | **144 phút** (×2,3) |
| idle | 93 phút | 168 phút |

B nhận cuốc **gần hơn và đắt hơn** — nhưng vẫn ít tiền hơn, vì **bị chào ít đơn hơn** và **mất
82 phút cho đổi pin**. Nói cách khác: nâng tỷ lệ nhận sớm trong ca đẩy tài xế vào chuỗi cuốc làm
cạn pin và kết thúc ở vùng ít cầu → mất vị thế nhận đơn về sau.

## 3. Ablation — thủ phạm là MỘT kênh

Bật từng kênh riêng lẻ (3 seed):

| kênh | Δ payout tổng | Δ số offer | Δ thời gian sạc |
|---|---|---|---|
| **`accept_lift`** | **−104.895đ** | −6/−6/−2 | +82/+55/0 phút |
| `rest_window` | 0 | 0 | 0 |
| `shift_extend` | +26.953đ | +4 | 0 |
| `shift_plan` | 0 | 0 | 0 |

⇒ Toàn bộ thiệt hại đến từ **`accept_lift`**. Hai kênh khác đang INERT ở config này (đã biết:
D-SIM-03/D-SIM-10), `shift_extend` có lợi.

## 4. Vì sao gate không chặn — MODEL GAP thật sự

`check_bonus_gate` đã gọi S1 `bonus_feasibility` (D-SIM-09, UPDATE-051) nên **không phải** lỗi
"quên kiểm khả thi". Vấn đề nằm ở chỗ khác: gate quyết định tại **phút 376 (≈6h16 sáng)**, khi
quỹ giờ còn nhiều nên S1 kết luận FEASIBLE hoàn toàn hợp lý. Nhưng:

1. S1 tính "cần thêm bao nhiêu giờ" dựa trên **tốc độ điểm/giờ lịch sử**, coi năng suất là
   **hằng số ngoại sinh**;
2. thực tế, hành động do chính advice tạo ra (nhận thêm cuốc) **làm thay đổi năng suất tương lai**
   — cạn pin, dịch chuyển khỏi vùng cầu, ít được chào đơn hơn;
3. mô hình **không có vòng phản hồi này**, nên S1 không bao giờ thấy chi phí cơ hội của việc nhận
   cuốc thêm.

Đây đúng là **D-SIM-05** ("advice nửa vời gây lỗ") ở dạng đã được đo lượng hoá — nhưng nguyên nhân
sâu hơn cái đã ghi: không chỉ "không chạm ngưỡng nên không có thưởng bù", mà **bản thân hành động
làm giảm năng suất**, thứ chưa mô hình nào trong hệ tính tới.

## 5. Hệ quả cho các quyết định đang chờ

- **ĐA-01 (shrinkage estimator — đã APPROVED-DESIGN)**: sẽ làm gate ÍT bắn hơn ở mẫu nhỏ (ước
  lượng ổn định hơn ⇒ ít "báo động giả" đầu ca). Đó là hướng đúng, nhưng **không đủ** — nó chỉ sửa
  *khi nào tin con số*, không sửa *chi phí cơ hội bị bỏ qua*.
- Cần một **ĐA mới** (đề xuất **ĐA-07**): đưa chi phí cơ hội vào điều kiện của `accept_lift` —
  hoặc bằng ràng buộc SOC/vị thế (không khuyên nhận thêm khi pin dưới ngưỡng hoặc khi cuốc kéo ra
  vùng cầu thấp), hoặc bằng cách chỉ bật kênh này khi **xác suất chạm mốc** đủ cao (không chỉ
  "feasible" nhị phân).
- **Trước khi có ĐA-07: kênh `accept_lift` KHÔNG nên bật mặc định** trong bất kỳ demo nào cho
  stakeholder — con số A/B sẽ tự phản bội sản phẩm.

## 6. Cái tôi CHƯA kiểm

- Chỉ 5 seed cho bảng §1 và 3 seed cho ablation §3 — đủ để chỉ ra cơ chế, **chưa đủ để kết luận
  phân phối** (chuẩn ≥30 seed, CLAUDE §4b).
- Chưa kiểm ở archetype khác P4, chưa kiểm với `max_realized_accept` khác.
- Chưa chứng minh chuỗi nhân quả "nhận cuốc → cạn pin → mất vị thế" bằng trace từng cuốc; hiện
  mới có tương quan mạnh (số sạc +82 phút, offer −6) và loại trừ 3 kênh còn lại.
