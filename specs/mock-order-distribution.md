# MOCK SPEC — Phân phối đơn Bike Hà Nội (nháp v1, T-003)

Cập nhật: 2026-07-20 · Căn cứ: `research/market/order-distribution.md` (+ `research/policy/bonus-programs.md`, `research/community/`) · Trạng thái: spec để code generator; mọi output phải gắn `is_mock=true`, `seed` deterministic.

## Mô hình

```
orders(zone, hour, dow, weather) = BASE_HN × zone_share(zone) × hour_shape(hour, dow_type) × dow_factor(dow) × weather_factor(rain)
```

## 1. Mức tuyệt đối `BASE_HN` (suy luận — đánh dấu rõ từng bước)

- FACT: Xanh SM ~1.000.000 chuyến/ngày toàn quốc, >100.000 xe (8/2025, press/high).
- ASSUMPTION A1: Hà Nội chiếm ~28% số chuyến (`TBD` — không có số công bố; HN & HCM là 2 thị trường chính, HCM lớn hơn).
- FACT: 2 bánh chiếm 61,36% chuyến toàn thị trường VN (Mordor).
- → BASE_HN (bike) ≈ 1.000.000 × 0,28 × 0,6 ≈ **170.000 đơn bike/ngày** cho toàn Hà Nội (MOCK, sai số lớn).
- Sanity check bắt buộc khi code: tài xế full-time mock (online 9–10h, khu tier A/B) phải nhận được **15–30 cuốc/ngày**, doanh thu 300–700k/ngày (khớp số tự khai). Nếu lệch → chỉnh A1, không chỉnh số sanity.

## 2. `hour_shape` — hình dạng 24h, ngày thường (tổng chuẩn hóa = 1)

Anchor VN: 2 khung cao điểm 6–9h & 17–20h (Grab official + quy định HN + khung nhân điểm của chính Xanh SM 6–8h, 16h–19h59). Hình dạng chi tiết: [PROXY] Didi (peak chiều > sáng ~1.3×, trưa không tụt sâu), [PROXY] NYC FHV (tối 20–24h giữ cao).

| Giờ | Trọng số | Giờ | Trọng số | Giờ | Trọng số | Giờ | Trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 0.25 | 06 | 0.80 | 12 | 0.65 | 18 | **1.30** |
| 01 | 0.15 | 07 | **1.00** | 13 | 0.55 | 19 | 1.10 |
| 02 | 0.10 | 08 | **1.00** | 14 | 0.55 | 20 | 0.90 |
| 03 | 0.10 | 09 | 0.70 | 15 | 0.65 | 21 | 0.80 |
| 04 | 0.15 | 10 | 0.60 | 16 | 0.90 | 22 | 0.60 |
| 05 | 0.35 | 11 | 0.65 | 17 | **1.20** | 23 | 0.40 |

Lý do từng đoạn: 6–9h commute sáng (đỉnh 7–8h); 12h nhích nhẹ (ăn trưa + đơn Ngon); 16h bắt đầu leo (trường học tan + đầu khung điểm vàng 16h); 17–19h đỉnh ngày (Didi: chiều > sáng); 20–23h giảm dần nhưng không rơi thẳng (app-hailing lệch tối); 1–4h đáy.

## 3. `dow_factor` và biến thể cuối tuần

| Thứ | Hệ số | Ghi chú |
| --- | --- | --- |
| T2 | 0.95 | đầu tuần trầm |
| T3–T4 | 0.97–1.00 | chuẩn |
| T5 | 1.03 | [PROXY] NYC: Thứ Năm cao |
| T6 | **1.10** | commute + tối mạnh ([PROXY] Chicago/NYC) |
| T7 | 1.05 | tổng ≥ ngày thường ([PROXY] CMAP) |
| CN | 0.90 | sáng rất chậm |

Biến thể `hour_shape` cuối tuần (T7/CN): đỉnh sáng 6–9h giảm còn ~60% giá trị bảng; khung 10–16h tăng +15% (mua sắm/chơi — Rakuten: social/dining/shopping là use case lớn); khung 20h–01h tăng +30% (T6/T7). Tối T6 cũng áp boost 20h–01h dù là ngày thường.

## 4. `weather_factor`

- Không mưa: 1.0. Mưa: **1.2** cơ bản ([PROXY] Chicago: Uber +22%).
- Scale cường độ: `1 + 0.006 × mm_per_hour`, trần 1.5 ([PROXY] Hải Khẩu +0,59%/mm·h; mưa to HN 20–50mm/h → +12–30%).
- Lưu ý chiều nghịch cho tài xế bike: mưa tăng đơn nhưng giảm cung bike (nguy hiểm, tài nghỉ) — generator v1 chỉ mô phỏng demand; supply để v2.

## 5. `zone_share` — chia khu vực Hà Nội (MOCK hoàn toàn, chờ dữ liệu thật)

| Tier | Khu vực | Share tổng | Ghi chú |
| --- | --- | --- | --- |
| A | Hoàn Kiếm, Ba Đình, Đống Đa, Cầu Giấy | 40% | văn phòng + du lịch + trường |
| B | Hai Bà Trưng, Thanh Xuân, Tây Hồ, Nam/Bắc Từ Liêm, Long Biên, Hà Đông | 45% | dân cư dày |
| C | Ngoại thành còn lại | 15% | thưa, cuốc dài |

Node đặc biệt (cộng thêm theo sự kiện/giờ): sân bay Nội Bài (đều 24h, cuốc dài), bến xe Mỹ Đình/Giáp Bát/Nước Ngầm (đỉnh cuối tuần + lễ), phố đi bộ Hồ Gươm (tối T6–CN), cổng bệnh viện lớn (sáng sớm), làng đại học (theo lịch học). Event boost kiểu K-PULSE: ×1.5–2 tại zone sự kiện trong khung giờ sự kiện.

## 6. Giá cuốc & doanh thu (để tính thu nhập mock)

- Giá trị cuốc bike: lognormal, median ~25k, P10 ~15k, P90 ~55k (`TBD` — hiệu chỉnh từ bảng giá công khai; sanity: 15–30 cuốc/ngày × giá này ≈ 300–700k doanh thu/ngày ✓).
- Net tài xế = doanh thu × (1 − chiết khấu theo track trong `planning/PERSONAS.md`) + thưởng (bảng thưởng theo research/bonus-programs) − chi phí (sạc ~10k/ngày hoặc đổi pin 9k/lần; thuê xe 60k/ngày nếu RTO).

## 7. Yêu cầu generator (khi code)

1. Deterministic theo `seed` + `scenario_id`; output gắn `is_mock=true`, `generated_at`, `spec_version: mock-dist-v1`.
2. Tham số trên là config (JSON/YAML), không hard-code — chờ research đợt 2/dữ liệu thật để hiệu chỉnh.
3. Scenario tối thiểu: ngày thường nắng, T6 mưa giờ tan tầm, CN sáng vắng, ngày có sự kiện lớn, tuần mưa dài.
4. Không bao giờ trình bày số mock như số thật — UI phải hiển thị nhãn dữ liệu mô phỏng.

## Assumption log

| ID | Giả định | Căn cứ | Rủi ro |
| --- | --- | --- | --- |
| A1 | HN = 28% chuyến toàn quốc | suy luận (không có số công bố) | cao — chỉ ảnh hưởng mức tuyệt đối, không ảnh hưởng hình dạng |
| A2 | Hình dạng giờ Didi áp được cho HN | cùng châu Á, app-hailing | trung bình |
| A3 | Bike share HN ≈ bike share toàn quốc (61%) | Mordor toàn quốc | trung bình |
| A4 | zone_share 40/45/15 | thuần suy luận từ mật độ đô thị | cao — cần dữ liệu thật/khảo sát |
