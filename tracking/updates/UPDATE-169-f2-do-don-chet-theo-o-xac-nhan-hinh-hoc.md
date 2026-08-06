# UPDATE-169 — F2: đo ĐƠN CHẾT THEO Ô ⇒ xác nhận hình học của verdict + phát hiện sắc hơn

- **Ngày:** 2026-08-06
- **Loại:** research (đo thật, arm A 5 seed) + đóng một caveat do chính tôi tạo ra + trả nợ artifact
- **Artifact:** `research/audit/2026-08-06-root-cause-idle/f2-expired-by-cell.py` + `.json`
- **Chạm:** cập nhật `f1-basin-map-KETQUA.md` §2.6→§4 và banner của `rc-00-VERDICT.md`

## 1. Vì sao chạy

`UPDATE-168` (F1) phải tự ghi caveat: cột *"khoảng cách tới ô nhiều đơn chết"* dùng **PROXY = cầu kỳ
vọng** vì `rc-03` chỉ xuất **tổng hợp**, không xuất bảng theo ô ⇒ *"cấm dùng số 0,00–1,34 km của F1 để
bác số 3,40–4,73 km của verdict"*. Caveat đó là do **thiếu dữ liệu**, không phải bản chất ⇒ đo cho xong.

## 2. Cổng đối chiếu ĐẠT trước khi đọc kết luận

Đo: arm A (mọi kênh tắt), 5 seed ⇒ **204,6 đơn chết/ngày**, **82 ô** có đơn chết.
**top-10 ô chiếm 42,0%** kho — `rc-03` báo **42,1%** ⇒ hai đường đo **độc lập khớp**, pipeline của tôi
không lệch. (Chỉ sau khi cổng này đạt tôi mới đọc phần dưới.)

## 3. ✅ Claim hình học của verdict — XÁC NHẬN

| ô | vai trò | cách 5 ô nhiều-đơn-chết nhất | đơn chết của chính ô |
| --- | --- | --- | --- |
| `953` | ô hút idle **đo được** | **3,46** km (dải 3,46–4,27) | 1,80/ngày |
| `bb3` | ô hút idle **đo được** | **3,71** km (dải 3,71–5,10) | 1,40/ngày |

Verdict nói **3,40–4,73 km**; đo được **3,46–3,71 km** tới top-5. **Cả hai NGOÀI bán kính chào đơn
2,22 km** ⇒ phần *"rót thêm phút rảnh vào đó cũng không gặp đơn nào"* **đứng**. Caveat F1 §2.6 **đóng**.

## 4. 🔴 Phát hiện MỚI — sắc hơn cả kết luận gốc của verdict

| ô | vai trò | khoảng cách | đơn chết của chính ô |
| --- | --- | --- | --- |
| `88f` | attractor **lưu vực LỚN NHẤT của F1 (42,8%)** | **1,60** km | **4,60**/ngày |
| `8c7` | cùng cặp | **1,34** km | 2,80/ngày |

Cặp mà **chính luật leo dốc ưu ái nhất** nằm **TRONG** bán kính 2,22 km và **có đơn chết nội tại cao gấp
2–3 lần** hai ô hút thật. Cặp `e2b`+`e2f` (lưu vực 12,9%) còn tốt hơn: `e2b` là ô đơn-chết **hạng 4**
(11,0/ngày).

⇒ **Vấn đề KHÔNG phải *"luật chỉ tạo ra bẫy"*, mà là *"luật tạo ra vài điểm hút — có cả cái TỐT ngay
cạnh cầu — nhưng đội xe lại dồn vào cái TỆ"***. Đây là một phát biểu **khác** và **hữu ích hơn**: nó
nói rằng dư địa không nằm ở "sửa luật cho tài xế đi xa hơn", mà ở **"vì sao họ vào lưu vực tệ"**.

## 5. `UNRESOLVED` được phát biểu lại cho sắc

*Vì sao đội xe hội tụ về cặp **XA** thay vì cặp **GẦN** mà chính luật ưu ái hơn?*
Ứng viên **chưa đo**: phân bố `home_cell`/vị trí bắt đầu ca · belief cache theo `(actor, giờ, cell)` làm
quỹ đạo phụ thuộc lịch sử · trường cầu đổi theo giờ nên lưu vực đổi trong ngày.
⚠ **KHÔNG** phải deadhead — `rc-03` đã đo nguồn vào hai ô hút: `demand_seek` **123** vs deadhead **2** vs
`go_online` **4**.

## 6. Trả nợ artifact (cùng cycle)

- `mm-04-rest-family.json` + `mm-07-s2.json` — **nay là JSON thật, hợp lệ** (trước là bản `-STAGED.md`
  cứu từ plan-file vì tôi lỡ chạy workflow trong plan mode nên agent bị chặn ghi).
- 6/7 artifact `pb-*` (phản biện) **vẫn đang chạy lại** ở workflow nền — tới khi có file, **lệnh CẤM
  trích số của `pb-01/02/03/04/05/07`** trong `UPDATE-166` §3 **vẫn hiệu lực**.

## Kiểm chứng

- F2 đo bằng `run_once` trên **config mặc định = arm A**; `order_expired` **không mang cell**
  (`world.py:619` chỉ log `order_id`) ⇒ phải map qua `result.orders` → `pickup_cell`. **Đây chính là một
  mảnh của VISIBILITY GAP** mà verdict §3-H4 nêu (bộ metric không xuất đủ) — ghi lại để ai cần thì biết.
- **Chưa kiểm chứng:** n=5 seed ⇒ **không có CI** cho từng ô; các số theo ô chỉ dùng để **xếp hạng** và
  tính khoảng cách (khoảng cách là **hình học thuần**, không phụ thuộc seed) ⇒ kết luận khoảng cách vững,
  còn *"ô X có 4,6 đơn chết/ngày"* thì là điểm-ước-lượng không CI.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim thay đổi (chỉ thêm script đo + docs + 2 artifact JSON).

## Visual
`NOT_APPLICABLE` — research.

## Adversarial self-review / flaws found

1. **Tôi đặt cổng đối chiếu TRƯỚC khi đọc kết luận** (top-10 share 42,0% vs 42,1%) — nếu lệch thì phải
   truy pipeline chứ không được đọc tiếp. Lần này khớp; ghi lại vì đây là thói quen đúng cần giữ.
2. F1 và F2 cùng nói *"luật tạo ra ít điểm hút"* nhưng **F1 sai ở việc đoán DANH TÍNH**. Bài học lặp lại
   lần thứ ba trong ngày: **mô hình tĩnh dự đoán được CẤU TRÚC, không dự đoán được KẾT CỤC**; muốn kết cục
   thì phải đo trong run thật.
3. Khoảng cách 1,34 km của cặp `88f`+`8c7` **vẫn < 2,22 km** nhưng **> 0** — không được đọc thành "cặp đó
   phục vụ được mọi đơn chết"; nó chỉ có nghĩa "nằm trong tầm với của một số ô đơn chết".
4. Tôi **chưa** trả lời được §5 và **không** đoán bừa. Ứng viên đã liệt kê là *ứng viên*, không phải
   kết luận.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (card F0/F1 đổi nội dung — blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13 · **amendment ĐA-08 kênh phía-cung** — gom đủ ở
`tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
