# Chi phí THỰC của tài xế Xanh SM Bike — mọi khoản công khai tường minh (2026-07-28)

Cường giao (2026-07-28): *"GSM sẽ không cung cấp thêm thông tin gì, chúng ta phải tự tìm kiếm thật
sâu để hiểu, sau đó mô hình hóa chính sách"* và *"nghiên cứu lại chi tiết chi phí thực sự của mọi
thứ đang được public tường minh"*.

⇒ **`D-POL-05` đổi bản chất**: không còn là "chờ GSM trả lời" mà là "dựng mô hình tốt nhất từ nguồn
công khai, gắn nhãn nguồn + độ tin, versioned như policy".

---

## 0. Phát hiện quan trọng nhất — chi phí km đang được tính MỘT NỬA

`src/gsm_sim/behavior.py:86` khi tài xế cân nhắc nhận đơn:

```python
net = gross_vnd - pickup_dist_km * cost_per_km_vnd     # cost_per_km_vnd = 3000.0
```

Nhưng `payout_vnd` — đại lượng mà **advisor tối ưu** — chỉ có `+=`, **không trừ gì**
(`world.py`: 6 chỗ cộng, 0 chỗ trừ). Nghĩa là:

| | quãng đón | quãng đổi chỗ | quãng chở khách |
|---|---|---|---|
| trong **quyết định** của tài xế | 3.000đ/km | — | — |
| trong **sổ tiền** advisor tối ưu | **0** | **0** | **0** |

⇒ Tài xế *hành xử* như thể mỗi km tốn tiền, nhưng *thước đo* nói mọi km đều miễn phí. Đây chính là
lý do cấu trúc khiến lời khuyên đổi chỗ trông "không mất gì" với optimizer — và là rủi ro trực tiếp
cho T-045a b3 (vòng lặp *đi → cạn pin → đổi*).

⚠ **Chưa kết luận `3000` là sai.** Nó nằm ở nhánh *cảm nhận* (disutility: công sức, thời gian,
rủi ro), không phải nhánh *kế toán*. Nhưng nếu ai đọc nó như tiền thì lệch **10–20×** so với chi phí
tiền mặt tính dưới đây. Hai khái niệm phải được đặt tên khác nhau — đúng nợ "hai tên một sự thật"
của T-046.

---

## 1. Năng lượng

### 1.1 Đội ĐỔI PIN (swap) — hiện tại gần như MIỄN PHÍ, và đó là chính sách có HẠN

| Khoản | Số | Nguồn | Độ tin |
|---|---|---|---|
| Pack pin | LFP **1,5 kWh** | [Electrive](https://www.electrive.com/2025/08/25/vinfast-to-install-150000-battery-swapping-stations-in-vietnam/) | HIGH |
| Quãng đường/pack khi chạy dịch vụ | **55–70 km** (sim dùng 60) | `world-parameters.md` §2 | MEDIUM |
| Phí đổi tại trạm công cộng | **9.000đ/lượt** | [greensm.com official 26/03/2026](https://www.greensm.com/news/gsm-mien-phi-thue-doi-pin-3-nam-cho-tai-xe-xanh-sm-bike) | **HIGH/official** |
| **Miễn phí đổi KHÔNG GIỚI HẠN** cho tài xế Platform độc quyền | tới **31/03/2029** | như trên | **HIGH/official** |
| Miễn phí thuê pin | **3 năm** kể từ ngày xác nhận đơn, cho khách mua xe đổi pin VinFast tới **30/06/2026** + đăng ký chạy độc quyền Xanh SM Platform | như trên | **HIGH/official** |
| Miễn 20 lượt đổi/tháng (khách thường) | tới **30/06/2028** | [Electrive](https://www.electrive.com/2025/08/25/vinfast-to-install-150000-battery-swapping-stations-in-vietnam/) | MEDIUM |
| Thuê pin **sau** ưu đãi | **175.000đ/tháng** (1 pin) · **300.000đ/tháng** (2 pin) | greensm.com official | HIGH/official |

**Quy ra đ/km:**

```
hôm nay (Platform độc quyền)     :      0 đ/km          ← chính sách, không phải vật lý
sau 01/04/2029                    :  9.000 / 60  = 150 đ/km   + thuê pin 175k/tháng
```

⇒ Chi phí pin **KHÔNG phải hằng số** — nó là **biến theo cohort × thời điểm hợp đồng**. Mô hình hoá
bằng một con số duy nhất là sai về bản chất.

### 1.2 Đội SẠC CẮM (charge)

| Khoản | Số | Nguồn |
|---|---|---|
| Pin Feliz S / Evo200 | **3,5 kWh** LFP | [imotorbike](https://news-vn.imotorbike.com/2026/05/xe-may-dien-vinfast-evo200-chay-duoc-bao-nhieu-km/) |
| Danh định | ~200 km (Evo200 203 km · Feliz S 198 km, tải 65 kg, 30 km/h đều) | nhà sản xuất |
| **Chạy dịch vụ** | **100–130 km** (sim dùng 110) | `world-parameters.md` §2 |
| Giá điện bình quân EVN 2026 | **2.204,07 đ/kWh** (chưa VAT) — QĐ 1279/QĐ-BCT 09/05/2025, 6 bậc | [LuatVietnam](https://luatvietnam.vn/linh-vuc-khac/bang-gia-dien-sinh-hoat-883-96993-article.html) |
| Công tơ thẻ trả trước (nhà trọ) | **2.909 đ/kWh** phẳng, không chia bậc | như trên |

```
sạc nhà, giá bình quân : 3,5 × 2.204 = 7.714đ / 110 km ≈  70 đ/km  (+VAT 8% ≈ 76)
sạc nhà, công tơ thẻ   : 3,5 × 2.909 = 10.182đ / 110 km ≈  93 đ/km
```

⚠ **Bậc thang là bẫy**: tài xế sạc mỗi ngày đẩy hộ lên bậc cao, nên giá biên **cao hơn** giá bình
quân. Dùng giá bình quân là **cận dưới**.

---

## 2. Bảo dưỡng và hao mòn

| Khoản | Số | Nguồn | Độ tin |
|---|---|---|---|
| Kiểm tra định kỳ | 20.000–100.000đ/lần (chưa gồm phụ tùng) | [VinFast](https://vinfastauto.com/vn_vi/nguyen-tac-va-chi-phi-bao-duong-xe-may-dien-vinfast) | MEDIUM |
| Mốc 5.000–10.000 km | 300.000–500.000đ | tổng hợp đại lý | MEDIUM |
| Chu kỳ | 3–6 tháng **hoặc** 3.000–5.000 km | VinFast | MEDIUM |
| Lốp/phanh | tuỳ mẫu, **user tự chịu** | VinFast | LOW (chưa có số) |

```
≈ 400.000đ / 7.500 km  ≈  30–100 đ/km      [MEDIUM]
```

---

## 3. Xe — chi phí CỐ ĐỊNH, không theo km

| Mô hình | Số | Nguồn |
|---|---|---|
| Mua trả góp | cọc **3 triệu** + **1,5–1,7 triệu/tháng** | greensm.com official |
| Thuê xe | **50.000–60.000đ/ngày** (đã gồm pin + đổi pin miễn phí) | tổng hợp đại lý, MEDIUM |
| Kèm theo | hỗ trợ đăng ký, bảo hiểm, bảo dưỡng | greensm.com official |

⚠ Đây là **chi phí theo NGÀY/THÁNG**, không theo km ⇒ **không được** cộng vào `cost_per_km`. Nó đổi
bài toán: tài xế đã trả tiền xe rồi thì mỗi km thêm là *biên rẻ*, nên "chạy thêm" hấp dẫn hơn — và
"nghỉ" đắt hơn — so với mô hình chỉ có chi phí biến đổi.

---

## 4. Nền tảng — SỐ MÂU THUẪN, phải nói rõ

| Nguồn | Con số | Loại |
|---|---|---|
| [greensm.com official 06/11/2024](https://www.greensm.com/news/cap-nhat-chinh-sach-thu-nhap-danh-cho-doi-tac-tai-xe-xanh-sm-bike-tai-tphcm-binh-duong-dong-nai) | *"Tỷ lệ chia sẻ doanh số **lên tới 91%**"* | official nhưng **chi tiết nằm trong ẢNH** |
| greensm.com (bài pin) | chia sẻ doanh thu **tới 90% năm 1**, 85% năm sau | official |
| Nguồn thứ cấp | chiết khấu **15,5%** (⇒ tài xế nhận 84,5%) | MEDIUM |
| Nguồn thứ cấp khác | tài xế nhận **75%** | LOW |

⇒ **Không có một con số duy nhất đúng.** "Lên tới 91%" là mức trần có điều kiện, không phải mức phổ
thông. Sim đang dùng `driver_share` từ config — phải gắn nhãn dải **[0,75 – 0,91]** và ghi rằng
con số chính xác **image-locked**.

---

## 5. Thuế — nhỏ hơn nhiều người tưởng, từ 2026

| Khoản | Nội dung | Nguồn |
|---|---|---|
| TNCN | **1,5%** trên doanh thu chia sẻ, **nền tảng khấu trừ và nộp thay**, theo tháng — từ 01/07/2025 | [Nghị định 117/2025/NĐ-CP](https://www.meinvoice.vn/tin-tuc/35149/nghi-dinh-117-2025-nd-cp-ve-thue-thuong-mai-dien-tu/) |
| VAT dịch vụ vận tải | giảm còn **8%** tới 31/12/2026 | tổng hợp |
| **Ngưỡng miễn thuế** | nâng lên **1 tỷ đồng/năm** từ **01/01/2026** (trước là 200 triệu) | như trên |

⇒ Tài xế bike doanh thu ~120–180 triệu/năm **nằm dưới ngưỡng** ⇒ thuế thực tế ≈ **0**, nhưng vẫn bị
**giữ 1,5% trong năm** rồi làm thủ tục hoàn. Tức là ảnh hưởng **dòng tiền**, không phải lợi nhuận.

---

## 6. Tổng hợp — mô hình đề nghị

```
chi phí BIẾN ĐỔI theo km (đ/km)
  đội swap, Platform độc quyền, tới 31/03/2029 :   0  (năng lượng)  + 30–100 (bảo dưỡng)
  đội swap, sau ưu đãi                         : 150 (năng lượng)  + 30–100
  đội charge, sạc nhà                          :  70–93            + 30–100
                                                 ─────────────────────────────
                                          dải hợp lý:  30 – 250 đ/km

chi phí CỐ ĐỊNH (đ/ngày)
  thuê xe          : 50.000–60.000
  hoặc trả góp     : 1.500.000–1.700.000 /tháng ≈ 50.000–57.000/ngày
  thuê pin sau ưu đãi: 175.000–300.000/tháng ≈ 6.000–10.000/ngày

khấu trừ trên doanh thu
  nền tảng : 9% – 25%  (image-locked, dải [0,75–0,91] tài xế nhận)
  TNCN     : 1,5% khấu trừ tại nguồn, hoàn lại nếu < 1 tỷ/năm
```

### Đối chiếu với sim hiện tại

| Đại lượng | Sim | Thực tế công khai | Nhận xét |
|---|---|---|---|
| chi phí km trong **sổ tiền** | **0** | 30–250 đ/km | **thiếu hoàn toàn** |
| chi phí km trong **quyết định nhận đơn** | 3.000 đ/km | 30–250 đ/km tiền mặt | lệch 10–20× nếu đọc là tiền ⇒ phải đổi tên thành *disutility*, không phải cost |
| phí đổi pin | 0 | 0 hôm nay · 9.000đ sau 2029 | **sim ĐÚNG cho hôm nay** |
| tầm hoạt động swap | 60 km | 55–70 km dịch vụ | ✅ khớp |
| tầm hoạt động charge | 110 km | 100–130 km dịch vụ | ✅ khớp |
| chi phí cố định ngày | 0 | 50–67k/ngày | thiếu — làm "nghỉ" trông rẻ hơn thực tế |

---

## 7. Đề nghị mô hình hoá (chưa implement — chờ Cường duyệt)

1. **Tách hai khái niệm** đang bị gộp: `pickup_disutility_vnd_per_km` (cảm nhận, giữ 3.000) và
   `cash_cost_vnd_per_km` (tiền thật, mặc định theo cohort). Đổi tên là bước đầu.
2. **Ledger chi phí riêng**, mặc định **bật với đội charge** (70–93đ/km có nguồn chắc) và **0 với
   đội swap Platform** (miễn phí có nguồn official) — đây là số ĐÚNG, không phải giả định.
3. **Chi phí cố định/ngày** vào `estimated_net`, **không** vào `payout` — giữ đúng tách bạch
   `gross / payout / estimated_net` của `CLAUDE.md §5`.
4. **Versioned theo cohort × ngày**: `battery_free_until: 2029-03-31` là *policy*, không phải hằng
   số. Sau ngày đó cùng một tài xế có chi phí khác.
5. Quét độ nhạy ở b4: `cash_cost_vnd_per_km ∈ {0, 70, 150, 250}` → lời khuyên vị trí còn dương tới
   mức nào?

## 8. Chưa kiểm / rủi ro

- **Con số nền tảng image-locked** — 91% vs 15,5% vs 75% không hoà giải được bằng nguồn text.
- **Chưa có số lốp/phanh/thay thế** cho xe chạy dịch vụ cường độ cao.
- **Chưa có số bảo hiểm** tách riêng (bài official nói "hỗ trợ" nhưng không nêu giá trị).
- Giá điện dùng **bình quân**; tài xế sạc hằng ngày rơi vào **bậc cao hơn** ⇒ 70đ/km là cận dưới.
- Dải 55–70 km/pack là `[ƯỚC LƯỢNG]` hệ số 0,65–0,8 từ danh định, không phải đo thực địa.
