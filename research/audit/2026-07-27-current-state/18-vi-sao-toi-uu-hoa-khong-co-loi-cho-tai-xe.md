# Vì sao các bài tối ưu hoá KHÔNG đem lại lợi ích cho tài xế — phân rã bằng ablation

Ngày: 2026-07-28 · Trả lời câu hỏi của Cường. Đo trên thế giới **đã sửa** (dispatcher tầng 2 +
tài xế biết sốt ruột), 15 seed CRN, `coverage: all`, bootstrap CI.

---

## 1. Kết quả ablation — bằng chứng, không phải suy luận

| biến thể | Δ payout | CI95 | seed có lợi |
|---|---|---|---|
| **hiện tại (đầy đủ)** | **−14.125đ** | [−35.019, +7.617] | 4/15 |
| bỏ hẳn **REST** | −3.490đ | [−19.137, +11.333] | 1/15 |
| bỏ hẳn **SWAP** | −20.792đ | [−41.591, +2.259] | 3/15 |
| **bỏ cả REST và SWAP** | **+0đ** | **[0, 0]** | 0/15 |

### Phân rã

| thành phần | đóng góp |
|---|---|
| **REST** | **−10.635đ** — thủ phạm chính |
| **SWAP** | **+6.667đ** — kênh **duy nhất** có ích |
| **tương tác REST × SWAP** | **−10.157đ** |

## 2. Bốn lý do, xếp theo mức đóng góp

### 2.1 94% lời khuyên KHÔNG có tác dụng gì

Đếm 6 seed: **6.329 ONLINE** · 338 REST · 72 SWAP. Mà `ONLINE → None` (không can thiệp — đúng
theo BUG-SIM3-01 đã sửa từ trước: `ONLINE` nghĩa *"khung này nên đang làm việc"*, không nói đứng
hay đi).

Dòng **"bỏ cả REST và SWAP ⇒ Δ = +0, CI [0,0]"** là **bằng chứng thực nghiệm**: advisor trở thành
**no-op tuyệt đối**. Trước đây điều này chỉ được suy từ đọc code; nay đo được.

⇒ **Advisor đang phát ra 94% nội dung không làm gì cả.** Không phải "khuyên sai" — mà là **khuyên
một thứ không dịch được thành hành động nào**.

### 2.2 REST là thủ phạm chính (−10.635đ), và lý do đã biết từ trước

`_required_rest` là **ràng buộc CỨNG** của DP (nhu cầu sinh lý, `rest_min_per_4h`). Nhưng trong
sim, **nghỉ không có lợi ích nào** — `fatigue` chỉ khiến tài xế tự nghỉ, **không** ảnh hưởng tỷ lệ
nhận / tốc độ / huỷ / rating / rủi ro (hồ sơ [`11`](11-sim-khong-the-cham-diem-loi-khuyen-nghi.md) §1).

⇒ **Mọi phút nghỉ bị ép là lỗ thuần.** Đây không phải "mô hình tồi" — nó là **bất khả thi về cấu
trúc**: kênh `shift_plan` có đúng ba đầu ra khác ONLINE (REST/SWAP/END), mà REST thì thế giới
không trả công.

### 2.3 SWAP là thứ DUY NHẤT hoạt động (+6.667đ)

Đây là tin tốt duy nhất và **đáng giữ**: khuyên đổi pin đúng lúc thật sự sinh tiền. Hợp lý — pin là
ràng buộc vật lý **có hậu quả thật** trong sim (41 lần bỏ đơn vì thiếu pin, 15/133 lượt đổi pin
thất bại, chờ tủ tối đa 50′). Khác hẳn nghỉ.

### 2.4 Tương tác âm (−10.157đ) — lớn hơn cả lợi ích của SWAP

Hai kênh **cùng bật** tệ hơn tổng hai kênh riêng lẻ. Khớp với số đếm: **47 lần `go_swap → rest`** —
advisor bảo nghỉ **đúng lúc tài xế đang đi đổi pin** ⇒ hoãn việc đổi pin sang thời điểm tệ hơn:
pin thấp hơn, giờ đông hơn, và 11% rủi ro tới trạm không có pin sẵn.

⇒ Đây là **lỗi TRÌNH TỰ**, không phải lỗi từng lời khuyên: DP xếp REST và SWAP vào các bucket độc
lập, không biết rằng **hoãn SWAP làm SWAP đắt lên**.

## 3. Giả thuyết tôi đã thử và BỊ SỐ LIỆU BÁC BỎ

**Giả thuyết**: `REST` của DP nghĩa *"đừng ONLINE kiếm tiền"*, mà `go_swap`/`relocate` vốn đã không
phải ONLINE ⇒ ghi đè chúng là thừa + phá hoại. Số đếm ủng hộ mạnh: **92/166 = 55%** can thiệp là
loại này.

**Đo 15 seed**: chặn ghi đè làm advisor **TỆ ĐI** — −14.125đ → **−32.383đ**.

**Vì sao sai**: `go_swap` tốn chuyến đi trạm + chờ (11% thất bại); `relocate` là **chạy rỗng** (14%
thời gian ở trạng thái bão hoà). Chính các lần ghi đè đó đang **CỨU** tài xế khỏi hành động đắt.

Cờ `advice.rest_only_overrides_wait` giữ lại, **mặc định `False`**, kèm số liệu bác bỏ ngay trong
code — để không ai đi lại đường này.

## 4. Trả lời trực tiếp: vì sao tối ưu hoá không có lợi cho tài xế

1. **Không gian hành động của solver thô hơn của tài xế.** Solver có ONLINE/REST/SWAP/END; tài xế
   có WAIT/RELOCATE/REST/GO_SWAP/GO_CHARGE/END. Mọi thứ "không phải ONLINE" bị nén thành REST.
2. **94% đầu ra là ONLINE — không dịch được thành hành động nào.** Advisor về thực chất chỉ có
   **hai** đòn bẩy.
3. **Một trong hai đòn bẩy (REST) bị thế giới định giá bằng 0.** Ép nghỉ = lỗ thuần, không thể
   khác.
4. **Hai đòn bẩy phá nhau** vì DP không mô hình hoá trình tự (hoãn nghỉ làm swap đắt lên).
5. **Đòn bẩy thật (vị trí) không nằm trong bài toán** — 62% lượt đơn chết vì không ai trong tầm,
   `relocate` chiếm 14% thời gian, nhưng solver không có action nào cho nó.

⇒ Kết luận: **không phải "mô hình hoá chưa đủ tốt" theo nghĩa tham số**. Bài toán đang **đặt trên
một không gian hành động sai**: nó tối ưu *khi nào nghỉ* trong một thế giới mà nghỉ không có giá,
và bỏ trống *đứng ở đâu* — biến có đòn bẩy thật.

## 5. Hệ quả cho hướng đi

| Việc | Căn cứ |
|---|---|
| **Giữ và mở rộng kênh SWAP** | kênh duy nhất dương (+6.667đ); pin có hậu quả thật |
| **Sửa lỗi trình tự REST×SWAP** | tương tác −10.157đ; DP phải biết hoãn swap làm swap đắt lên |
| **KHÔNG thêm "giá trị nghỉ" vào solver** | Cường đã bác; và §2.2 cho thấy vấn đề ở **thước đo**, không ở tham số |
| **Thêm action VỊ TRÍ vào không gian bài toán** | §4.5 — đây mới là đòn bẩy; cần heatmap (Cường mở 2026-07-28) |

## 6. Chưa kiểm (trung thực)

- 15 seed cho ablation — đủ chỉ **hướng và thứ hạng**, CI vẫn rộng (chuẩn ≥30, và so biến thể cần
  ≥100 theo `MIN_SEEDS_FOR_VARIANT_COMPARISON`).
- Phân rã "REST −10.635 / SWAP +6.667 / tương tác −10.157" là **hiệu số trung bình**, chưa có CI
  riêng cho từng thành phần.
- Chỉ archetype P4, một config, kênh mặc định (`accept_lift`/`shift_extend`/`rest_window` đều tắt).
- Chưa kiểm liệu sửa lỗi trình tự có thu hồi được đúng −10.157đ hay không.
