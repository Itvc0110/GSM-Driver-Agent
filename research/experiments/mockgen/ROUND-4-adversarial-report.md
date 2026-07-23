# ROUND 4 — Adversarial review (mock dataset v1)

Ngày: 2026-07-23 · Dataset: `data/mock/v1` (30 ngày × 50 driver; 22,075 trips, 47,716 events, 1,004,273 GPS pings).
Phương pháp: query polars độc lập trên 4 chiều hiện thực (subagent workflow bị chặn spend-limit 2 lần → làm inline, số liệu chính xác từ data thật). Mỗi claim có số cụ thể.

## Kết quả — KHÔNG có generator bug

| Chiều | Kiểm | Kết quả | Verdict |
|---|---|---|---|
| **Money** | payout > gross | 0 | PASS |
| | thu nhập âm (non-adjustment) | 0 | PASS |
| | gross khớp fare formula | max lệch **3 VND** (rounding do `dist_km` lưu 3 số lẻ, gross tính full-precision) | PASS — artifact, không phải bug |
| **Space-time** | trip duration ≤ 0 | 0 | PASS |
| | effective speed > 50 km/h | 0 (max 23.2, median 17.3 km/h) | PASS — hợp lý bike đô thị |
| | GPS teleport > 2km trong < 60s | 0 | PASS |
| | GPS implied speed p99 | 23.3 km/h | PASS |
| **Behavior** | trips/driver/ngày | max 32, p99 27 | PASS — không phi lý (FT chăm) |
| **Coverage** | event giờ 0–4h (window 05–24 → phải 0) | 0 | PASS |
| | driver trong profile không có event | 0 | PASS |
| | observed accept-rate | 0.966 (bench archetype 0.80–0.98) | PASS |

## Giới hạn đã biết (EXPECTED-SIM-LIMIT — không sửa generator)

- payout FT ~256k dưới dải thực 270–480k; trips FT median 16 ở biên dưới 15–30 → **CALIBRATION GAP T-021** (pilot Đống Đa nhỏ + supply-demand mismatch = dư địa advisor; UPDATE-023). Đã ghi nhãn trong ROUND-2, KHÔNG tune generator để che.
- dist median 3.21km (mục tiêu 3.5) — giới hạn địa lý pilot, ghi T-021.
- Data mới có L0/L1 (+ GPS). L2/L2i/L3 derivation là bước sau (solver C2+); schema đã sẵn.

## Kết luận

**ROUND 4 PASS** — không phát hiện flaw phải sửa generator. 4/4 vòng verify đạt; dataset dùng được làm nền solver C2–C5. Fare rounding ≤3 VND là artifact chấp nhận (có thể siết bằng cách lưu dist_km nhiều số lẻ hơn nếu solver cần — defer, không blocker).

Subagent adversarial (workflow `wf_3a5e8e56-38c`) bị chặn bởi monthly spend-limit cả 2 lần chạy — thay bằng inline polars review; ghi nhận để chạy lại bằng subagent khi quota ổn định (không blocker vì inline đã phủ đủ 4 chiều với số liệu thật).
