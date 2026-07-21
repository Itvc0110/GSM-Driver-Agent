# MOCK SPEC — Demand proxy Bike Hà Nội (nháp v1, T-003)

Cập nhật: 2026-07-20 · Căn cứ: `research/market/order-distribution.md`, `research/policy/bonus-programs.md`, `research/community/` · Trạng thái: **SPEC READY / CODE CHƯA CLAIM**. Mọi output gắn `is_mock=true`, provenance và deterministic seed.

## 0. Ranh giới

Generator này mô phỏng **placed-order demand proxy** theo thời gian/khu vực. Nó **không** mô phỏng matching/dispatch, không tạo pool đơn chắc chắn đủ điều kiện cho một tài xế, và không ước tính xác suất một đơn cụ thể được phân cho họ.

Minimum scope F2 chỉ dùng proxy để tư vấn **khi nào chạy/nghỉ/sạc**. Không dùng output để khuyên reposition/chọn khu vực, nhận/từ chối/hủy cuốc.

## 1. Mô hình

```text
raw_demand(zone, hour, dow, weather)
  = BASE_HN
  × zone_share(zone)
  × normalized_hour_weight(hour, dow_type)
  × dow_factor(dow)
  × weather_factor(rain_mm_per_hour)

normalized_hour_weight(h) = raw_hour_weight[h] / Σ(raw_hour_weight[0..23])
```

Khi cần mô phỏng `eligible/available pool`, phải có model/contract riêng với dispatch owner; không suy từ `raw_demand`.

## 2. Mức tuyệt đối `BASE_HN` (MOCK, sai số cao)

- FACT: Xanh SM ~1.000.000 chuyến/ngày toàn quốc, >100.000 xe (8/2025, press/high).
- ASSUMPTION A1: Hà Nội chiếm ~28% số chuyến (`TBD`).
- FACT/market proxy: 2 bánh chiếm 61,36% chuyến ride-hailing VN (Mordor).
- MOCK: `1.000.000 × 0,28 × 0,6 ≈ 170.000` placed-order demand/ngày toàn Hà Nội.

Con số này chỉ là scenario scale. Không được chia cho số tài xế để suy ra đơn/tài xế vì thiếu supply, eligibility, service mix, online hours và dispatch behavior.

Sanity-check tham khảo: nguồn tự khai full-time Bike thường nói 15–30 cuốc/ngày và 300–700k revenue/ngày, nhưng định nghĩa gross/payout/net không đồng nhất; không dùng các số đó làm constraint bắt buộc.

## 3. Relative hour weights — ngày thường

Bảng dưới là **relative raw weights**, tổng hiện tại = **15,45**; generator bắt buộc chuẩn hóa bằng công thức ở §1.

Anchor VN: peak 6–9h và 17–20h (Grab official + giờ giao thông HN). Hình dạng chi tiết dùng [PROXY] Didi/NYC, không phải số GSM.

| Giờ | Weight | Giờ | Weight | Giờ | Weight | Giờ | Weight |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 0.25 | 06 | 0.80 | 12 | 0.65 | 18 | **1.30** |
| 01 | 0.15 | 07 | **1.00** | 13 | 0.55 | 19 | 1.10 |
| 02 | 0.10 | 08 | **1.00** | 14 | 0.55 | 20 | 0.90 |
| 03 | 0.10 | 09 | 0.70 | 15 | 0.65 | 21 | 0.80 |
| 04 | 0.15 | 10 | 0.60 | 16 | 0.90 | 22 | 0.60 |
| 05 | 0.35 | 11 | 0.65 | 17 | **1.20** | 23 | 0.40 |

Rationale: 6–9h commute sáng; 12h nhích nhẹ; 16h bắt đầu leo; 17–19h peak chiều; 20–23h giảm dần; 1–4h đáy. Các policy reward windows chỉ là evidence phụ có version, không quyết định trực tiếp demand.

## 4. `dow_factor` và cuối tuần

| Thứ | Hệ số | Ghi chú |
| --- | --- | --- |
| T2 | 0.95 | MOCK |
| T3–T4 | 0.97–1.00 | baseline |
| T5 | 1.03 | [PROXY] NYC |
| T6 | 1.10 | commute + tối ([PROXY]) |
| T7 | 1.05 | [PROXY] CMAP |
| CN | 0.90 | sáng chậm ([PROXY]) |

Cuối tuần: giảm 6–9h còn ~60%, tăng 10–16h +15%, tăng 20h–01h +30%. Các multiplier được áp vào raw weights rồi **chuẩn hóa lại theo ngày** nếu muốn giữ daily total cố định; hoặc không chuẩn hóa lại nếu scenario muốn thay total demand — config phải ghi rõ mode.

## 5. Weather factor

Dùng một công thức duy nhất, không nhân chồng với “1.2”:

```text
weather_factor = clamp(1 + 0.006 × rain_mm_per_hour, 1.0, 1.5)
```

- Nguồn proxy: Haikou ~+0,59%/mm·h; Chicago app-hailing +19–22% trong mưa.
- Scenario default `RAIN_MODERATE` có thể đặt `rain_mm_per_hour≈33`, cho factor≈1.20.
- Mưa có thể tăng passenger demand nhưng giảm supply Bike; spec v1 chỉ mô phỏng demand, không suy availability/safety.

## 6. Zone shares — MOCK distribution only

| Tier | Khu vực | Share | Ghi chú |
| --- | --- | --- | --- |
| A | Hoàn Kiếm, Ba Đình, Đống Đa, Cầu Giấy | 40% | MOCK |
| B | Hai Bà Trưng, Thanh Xuân, Tây Hồ, Nam/Bắc Từ Liêm, Long Biên, Hà Đông | 45% | MOCK |
| C | Ngoại thành còn lại | 15% | MOCK |

POI/event inputs có thể điều chỉnh **distribution trong simulator**, không biến thành recommendation: bến xe, phố đi bộ, bệnh viện, trường/đại học, TTTM. **Nội Bài loại khỏi Bike scenario**; nếu cần Car/taxi scenario phải tách service config.

## 7. Money outputs (optional simulation layer)

- `gross_revenue`: giá trị cuốc trước platform share; distribution hiện `TBD`.
- `driver_payout`: gross sau platform share + eligible bonus/adjustment theo **policy bundle versioned đúng track**.
- `estimated_net_income`: payout trừ known driver-borne costs; kèm `money_definition_version`, `cost_completeness`, `unknown_costs`. Thiếu chi phí → `partial/unknown`, không tự bịa.

Không dùng T4/blocked source (`bike-xanhsm.com`, domain nhái) làm policy/financial config. Xem `research/policy/bonus-programs.md` và `specs/community-source-risk-control.md`.

## 8. Yêu cầu generator khi code

1. Deterministic theo `seed` + `scenario_id`; output: `is_mock=true`, `generated_at`, `source_refs`, `assumption_ids`, `spec_version=mock-demand-v1`.
2. Tất cả tham số ở config JSON/YAML; không hard-code trong domain logic.
3. Scenario tối thiểu: weekday dry, Friday rain peak, Sunday low morning, event day, prolonged rain.
4. Invariants: normalized hourly probabilities sum≈1 trong mode normalized; zone shares sum=1; all counts non-negative; same seed/config → same output.
5. UI luôn hiển thị “Dữ liệu mô phỏng”; không trình bày scale 170k như fact GSM.

## 9. Assumption log

| ID | Giả định | Căn cứ | Rủi ro |
| --- | --- | --- | --- |
| A1 | HN = 28% chuyến toàn quốc | suy luận | cao |
| A2 | Didi/NYC hour shape áp được cho HN | proxy quốc tế | trung bình |
| A3 | Bike share HN ≈ 61% toàn quốc | market proxy | trung bình |
| A4 | zone shares 40/45/15 | suy luận mật độ đô thị | cao |
| A5 | weather response áp được cho Bike HN | proxy app-hailing, chưa có supply | cao |
