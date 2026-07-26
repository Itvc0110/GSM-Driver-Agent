# UPDATE-058 — SIM-XANH Phase 5: regen + verify + ĐÓNG đợt nâng cấp

Ngày: 2026-07-26 · Track: **A** · Chuỗi commit đợt SIM-XANH: `3b724d7` (P0) · `fac5e58` (P1
OSRM) · `de70ff6` (P2 XanhSM detail) · `c61f8f8` (P4 dashboard) · `2fccdc8` (P3 sweep) · P5 này.

## 1. Regen 90 ngày trên engine mới — so sánh trung thực

| chỉ số (`driver_statistic_daily`) | trước SIM-XANH | **sau** | vì sao |
|---|---|---|---|
| driver-day | 11.376 | **12.805** | n 74→90 (đường thật ngốn năng lực đội — P1 §3) |
| tỷ lệ nhận (median) | 0.9167 | 0.9091 | khớp hành vi sim (~0.906) — coherence giữ |
| hoàn thành (median) | 0.9545 | 0.9600 | trong dải gate [0.92, 0.97] |
| cuốc/ngày (median) | 15 | **12** | pha loãng cơ cấu (D-SIM-01 nặng thêm — đã ghi ở P1, không che) |
| bảng mission (BIKE) | rule-based | **từ SỰ KIỆN sim** (earn_history có timestamp thật, progress 261 dòng) | P2 |
| % 5★ | gauss tầng data | **từ event `trip_rated`** (0.79 khớp thiết kế) | P2 |

**4 vòng verify trên data mới**: schema 13 bảng ✅ · thống kê 30 seed **BIKE 6/6 PASS 0 GAP**
(cuốc/ngày median 10 **chạm biên dưới** target 10-30 — hệ quả n=90, trung thực) · nhất quán
sim↔data ✅ · đối kháng ✅.

## 2. Cờ `+dirty` hoạt động đúng — và quy trình chốt provenance

Regen giữa chừng cho `engine_commit: 2fccdc8+dirty` vì tôi sửa docs trong lúc regen chạy —
**đúng thiết kế REVIEW-C7/C12** (không cho manifest nói dối). Quy trình chốt: commit toàn bộ
docs/UPDATE này → regen lại trên cây sạch → commit manifest riêng.

## 3. SIM-XANH tổng kết (6 chỉ thị Cường 2026-07-26 → trạng thái)

| chỉ thị | trạng thái |
|---|---|
| Sim giống XanhSM thật, chi tiết state/actors/action | ✅ P2: rating/tân-binh/mission là SỰ KIỆN sim, bám l1r; tiền 4 nguồn |
| Q-01 tự fetch | ✅ cấu trúc thật greensm.com; số image-locked gắn PROXY (D-POL-05) |
| Google Maps alternatives | ✅ đóng — OSRM/Stadia/OSM; không cần key |
| OSRM thay detour + D-SIM-06 trước D-SIM-16 | ✅ P1 (factor median 1.46, re-baseline có tài liệu, gate 13/13) + P3 sweep |
| Dashboard đẹp (taste-skill) + mọi tính năng trực quan | ✅ P4: palette VALIDATED 5/5, Replay TripsLayer, tab A/B + heatmap sweep (V-09) |
| Track C sau, rồi audit data/agent/math | ⏭️ kế tiếp ngay sau UPDATE này |

## 4. Nợ mở còn lại của Track A (đầy đủ, không giấu)

`D-SIM-01` (1-quận — nặng thêm) · `D-SIM-11` (S1 trả mã lý do cấu trúc) · `D-SIM-14` (RNG
adherence theo khoá) · `D-SIM-15` (ledger timestamp) · `D-SIM-16` (persistence hành vi — SAU
audit theo thứ tự Cường) · `D-SIM-17` (clawback theo tháng cần chuỗi ≥60 ngày) ·
`D-SIM-18` (**shrinkage estimator — chuyển MATH AUDIT**) · F-P4-A/B (queue động trạm, Stadia
tiles) · số PROXY tân binh chờ GSM (D-POL-05).

## 5. Kiểm chứng
Full suite cuối: chạy nền lúc viết — **số thật ghi ở commit message** (đã bỏ thói quen ghi số
dự đoán sau 2 lần lệch). Visual: **V-09** chờ Cường.
