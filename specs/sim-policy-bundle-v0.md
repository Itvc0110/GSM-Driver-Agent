# SPEC — Sim Policy Bundle v0 (MOCK, frozen snapshot)

Cập nhật: 2026-07-21 (rà lại 2026-07-29 — xem `research/economics/driver-cost-structure-2026.md`)
· Trạng thái: READY (vá blocker F1/F2/G3/G6 từ red-team audit) · Version: `sim-policy-v0`
**Toàn bộ là MOCK** — đóng băng từ các policy snapshot đã verify trong `research/policy/bonus-programs.md` + `research/economics/income-structure.md`, KHÔNG phải số hiện hành của GSM; chỉ dùng trong simulator, không bao giờ hiển thị cho tài xế thật như fact. Mỗi giá trị có provenance hoặc [MOCK-DERIVED].

## 1. Fare model (gross revenue mỗi cuốc)

```text
gross(d_km) = BASE_FARE + max(0, d_km − BASE_KM) × PER_KM
BASE_FARE = 13.000 VND (2 km đầu)   [MOCK — hiệu chỉnh từ dải giá cuốc 15–30k, research đợt 1]
PER_KM    = 4.300 VND/km            [MOCK-DERIVED]
Phụ phí (mưa/đêm/cao điểm) = 0 trong v0  [đơn giản hóa; ghi nhận defer]
```

Sanity: cuốc median 3,5 km → gross ≈ 19,5k; 20 cuốc/ngày → ~400–460k gross/ngày — khớp dải tự khai 300–700k.
⚠ Cập nhật 29-07: km nay là lộ trình THẬT (OSRM, ×~1,46 so với đường chim bay) ⇒ gross trung vị
cao hơn sanity trên — đây là lý do `accept_logit_center_vnd` chuyển từ 15.400 → **21.200**.

## 2. Revenue share & payout

- `driver_share = 75%` flat — đóng băng theo trần "lên tới 75%" của snapshot 02/03/2026 (HN). [MOCK: policy thật phân theo khung giờ dưới trần, chi tiết không công bố]
- `driver_payout(ngày) = Σ gross×0.75 + bonus_đạt_được`
- `estimated_net = payout − cost_theo_track` (mục 5).

## 3. Điểm thưởng & mốc NGÀY (giải quyết F2 — pilot chạy 1 ngày)

- Điểm/cuốc theo **giờ khách đặt** (đúng cơ chế verify đợt 2): khung 06–08h & 16–18h = **10 điểm**, các giờ khác trong khung tính điểm (06–21h) = **5 điểm**, ngoài khung = 0. [Snapshot 07/2025; bản 12/2025 đổi 5-10-15-20-30 theo dịch vụ — v0 dùng bản đơn giản đã verify]
- **Mốc thưởng NGÀY [MOCK-DERIVED = mốc tuần HN ÷ 7, làm tròn]**: 60đ→30k · 100đ→60k · 160đ→115k · 200đ→170k (nhận mốc cao nhất đạt được, không cộng dồn).
- Điều kiện nhận thưởng ngày: `acceptance_rate ≥ 85%` VÀ `completion_rate ≥ 85%` (snapshot HN 12/2025).
- Kịch bản tuần (sau pilot): quay lại mốc tuần thật 400/700/1.100/1.400 → 200k/400k/800k/1,2tr + khởi tạo `week_points_so_far` theo archetype.

## 4. Kỷ luật (trong sim = cờ/hệ quả hành vi, không trừ tiền trong run 1 ngày)

- `acceptance_rate (ngày) < 50%` → bật `forced_auto_accept` tới 23h59 (decline vô hiệu).
  ⚠ Đính chính: cơ chế forced-accept đã **BỎ** theo policy Vận Doanh 23/02/2026 (audit A1 S3-2);
  còn dư `threshold_forced` trong `f3_patterns.py:75` — nợ dọn.
- `acceptance/completion < 70%` → cờ `at_risk` (phạt 100–200k/TUẦN ngoài đời — trong run 1 ngày chỉ log cảnh báo + advisor được nhắc).
  ⚠ Đính chính: hình phạt 100–200k/tuần đã bị thay bằng **KHOÁN TUẦN + truy thu 20%** (HN/HCM
  tới 40%) phần doanh số chưa đạt (policy Vận Doanh 23/02/2026).
- Advisor không bao giờ khuyên hành vi làm rơi tỷ lệ (đã có trong điều kiện an toàn advice khu vực).

## 5. Chi phí theo archetype/track (cho estimated_net)

| Archetype | Track | Chi phí/ngày trong sim |
| --- | --- | --- |
| P1, P3, P5 | Xe cá nhân | Điện: sạc nhà ~10k/lần đầy (~120km) [research đợt 1]; đổi pin tại trạm 9k/lượt nếu dùng |
| P2, P4 | RTO/thuê xe công ty | Thuê 60k/ngày + đổi pin **0đ** (Platform miễn phí tới **31/03/2029** — đính chính 29-07, không phải 2028; xem `research/economics/driver-cost-structure-2026.md`) |
| Tất cả | — | ĐBTN (đảm bảo thu nhập cohort mới) KHÔNG mô hình hóa trong v0 — defer, ghi nhãn |

⚠ Đính chính 29-07 (dòng 41): (a) sim **KHÔNG** mô hình hoá tiền thuê xe trong payout; chi phí
tiền mặt là **sổ riêng** `actor.cost_vnd` (T-045b), mặc định `swap_fee_vnd: 0` + `cash_cost_vnd_per_km: 0`,
**KHÔNG đụng payout**. (b) Mốc miễn phí đổi pin đúng là **31/03/2029**, không phải 2028.

⚠ Ghi chú config hiện hành (29-07): số archetype nay là **7** (thêm P6 0.18, P7 0.12 — SIM-1);
P6/P7 **thiếu track/đội xe** trong bundle này — nợ chưa gán. Tên cờ thật trong config là
`charge_fleet_ratio_p3p5` (không phải `charge_fleet_ratio` trơn).

## 6. Đội xe (giải quyết G3)

- P2, P4: 100% xe đổi pin (Evo swap, ~60 km/pack, ngưỡng đi đổi SoC 20%).
- P1: 100% xe cá nhân sạc cắm (Feliz S ~110 km, sạc nhà 3–4h).
- P3, P5: **50% swap / 50% sạc cắm** (config `charge_fleet_ratio_p3p5`, default 0.5).
- P6, P7 (SIM-1, tỷ trọng 0.18/0.12): **chưa gán track/đội xe** trong bundle v0 — nợ, ghi nhận.

## 7. Assumption log

| ID | Giả định | Rủi ro |
| --- | --- | --- |
| PB1 | Fare 13k+4.3k/km, không phụ phí | trung bình — chỉ ảnh hưởng mức tuyệt đối payout, không ảnh hưởng Δ giữa các arm |
| PB2 | Share 75% flat (thật: theo khung giờ dưới trần) | thấp cho so sánh arm; cao nếu diễn giải mức tuyệt đối |
| PB3 | Điểm 10/5 bản 07/2025 (không phải 12/2025 per-service) | thấp — pilot 1 loại đơn |
| PB4 | Mốc ngày = tuần÷7 | trung bình — làm advice "chốt mốc" khả thi trong 1 ngày; kịch bản tuần dùng số thật |
| PB5 | Kỷ luật = cờ, không trừ tiền trong ngày | thấp |

Mọi run manifest phải ghi `policy_bundle_version: sim-policy-v0`.
