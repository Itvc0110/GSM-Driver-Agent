# SCREEN-PARITY — bảng đồng bộ Web (Cường/agent) × Flutter (Khánh)

Cập nhật: 2026-07-26 (U1). **Cơ chế chia việc contract-first** (chốt với Cường):
cả hai UI cùng gọi MỘT backend FastAPI (`ui/backend/`, port 8000) — logic/số chỉ sống ở backend;
style chung lấy từ `ui/design-tokens.json`; response shape chuẩn ở `ui/contracts/*.json`.
Đổi contract = ghi UPDATE-### + báo nhau (xem ASSIGNMENTS). Web làm trước để chốt design + contract,
Flutter bám bảng này để bắt kịp — không ai sửa file của người kia.

## Trạng thái màn hình

| Màn | Contract dùng | Endpoint | Web | Flutter (Khánh) | Ghi chú |
|---|---|---|---|---|---|
| **Xanh Now** (map + pills + CTA) | `driver_state` v1.1 · `map_context` v1.0 | `/api/v1/driver/state` · `/api/v1/map-context` | 🔨 U2 | ✅ v0 (data synthetic) | v1.1 additive — Flutter v0 vẫn parse được; nâng cấp: money tách gross/payout + badge "Dữ liệu mô phỏng" |
| **Bot Trợ Lý Xanh** (bottom sheet) | `advice` v1.0 | `/api/v1/advice` | 🔨 U2 | ✅ v0 (text CỨNG) | Flutter cần thay text cứng bằng render items[] + confidence + trạng thái im lặng |
| **Thu nhập** (thống kê ca/ngày) | `driver_state.money` + history | `/api/v1/driver/history` (U2) | 🔨 U2 | ❌ chưa có | Payout mặc định; gross ghi nhãn rõ; nguồn: mock 90 ngày |
| **Chuyến của tôi** (vòng đời cuốc demo) | `trip_step` (giữ của Khánh) | `/api/v1/trip/step` | 🔨 U2 (port từ demo) | ❌ chưa có | Giữ interaction demo (skip/auto/reset); KHÔNG gắn advice vào cuốc cụ thể (ranh giới CLAUDE §5) |
| **Xe & Pin** | `driver_state` (soc, range) | `/api/v1/driver/state` | 🔨 U2 (khung) | ❌ khung | |
| **Cài đặt** | — | — | 🔨 U2 (khung) | ❌ khung | |
| **Mô phỏng · Replay** | `replay` v1.0 | `/api/v1/sim/replay?seed=` | 🔨 U3 | ⬜ để sau (desktop-first) | Khu riêng theo chỉ thị Cường; Leaflet nội suy client |
| **Mô phỏng · Hành trình** | `journey` v1.0 | `/api/v1/sim/journey?seed=&actor=` | 🔨 U3 | ⬜ để sau | Gantt + income curve 4 nguồn + mốc advice |
| **Mô phỏng · A/B** | `ab_result` v1.0 | `/api/v1/sim/ab?seed=` | 🔨 U3 | ⬜ để sau | BẮT BUỘC hiện warning 1-seed |
| **Mô phỏng · Độ nhạy** | (file precomputed) | `/api/v1/sim/sweep` | 🔨 U3 | ⬜ để sau | Đọc `research/experiments/sensitivity/dsim06_sweep.json`, không tính lại |

Ký hiệu: ✅ xong · 🔨 đang làm (phase ghi kèm) · ❌ cần làm để parity · ⬜ chưa cần.

## Quy tắc cho mọi màn (cả hai UI)

1. **Badge "Dữ liệu mô phỏng"** ở mọi màn có số (token `labels.mock_badge`).
2. **Tiền**: payout là số mặc định; gross chỉ hiện kèm nhãn "Doanh thu gộp"; không hứa chắc thu nhập.
3. **Màu series** theo `design-tokens.json → dataviz.categorical_*` (màu theo entity, không theo thứ tự);
   accent cyan `#00AFB9` CHỈ cho chrome (nút/badge/brand), không làm màu series.
4. Advice render từ `items[]` + `confidence` + `numbers[].source` — UI không thêm số nào tự nghĩ ra;
   trạng thái `silent` hiển thị tử tế ("Bạn đang đúng nhịp — không có gì cần chỉnh").
5. Ba màu sáng (aqua/yellow/magenta) dưới 3:1 trên nền trắng → chart dùng chúng phải có direct label
   hoặc table view (đã ghi trong tokens.provenance).
