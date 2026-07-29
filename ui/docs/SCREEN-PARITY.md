# SCREEN-PARITY — bảng đồng bộ Web (Cường/agent) × Flutter (Khánh)

Cập nhật: 2026-07-27 (U1 + UI-FARE-01) · 2026-07-29 (ĐA-05). **Cơ chế chia việc contract-first** (chốt với Cường):
cả hai UI cùng gọi MỘT backend FastAPI (`ui/backend/`, port 8000) — logic/số chỉ sống ở backend;
style chung lấy từ `ui/design-tokens.json`; response shape chuẩn ở `ui/contracts/*.json`.
Đổi contract = ghi UPDATE-### + báo nhau (xem ASSIGNMENTS). Web làm trước để chốt design + contract,
Flutter bám bảng này để bắt kịp — không ai sửa file của người kia.

## Trạng thái màn hình

| Màn | Contract dùng | Endpoint | Web | Flutter (Khánh) | Ghi chú |
|---|---|---|---|---|---|
| **Xanh Now** (map + pills + CTA) | `driver_state` v1.1 · `map_context` v1.0 | `/api/v1/driver/state` · `/api/v1/map-context` | ✅ U2 | ✅ v0 (data synthetic) | v1.1 additive — Flutter v0 vẫn parse được; nâng cấp cần làm: money tách gross/payout + badge "Dữ liệu mô phỏng"; demand zones giờ là SỐ ĐƠN THẬT từ bảng trips (hex×giờ) |
| **Trợ Lý Xanh = PROACTIVE CARDS** (DIRECTIVES §12 — KHÔNG chat) | `advice` v1.0 + `advice_action` v1.0 | `/api/v1/advice` · POST `/api/v1/advice/action` · GET `/actions` | ✅ UX-CARDS (UPDATE-067) | ❌ Flutter còn bot-sheet text cứng — cần chuyển sang cards | 3 loại thẻ brief/nudge/recap; nudge CHỈ khi không chở khách (NHTSA); nút Làm theo/Bỏ qua/Vì sao → log adherence; im lặng = KHÔNG thẻ; hub sheet thay chat. ⚠ Cập nhật 29-07 (ĐA-05): canonical nay là `AdviceEventLog` (append-only, **validate qua registry trước khi ghi**, idempotent theo `event_id` khoá theo **GIÂY quan sát**); `advice_actions.jsonl` chỉ còn **debug export**; `GET /actions` đọc từ event log. Adherence tính **MỘT LUẬT** (`gsm_core/lifecycle/projections.py`) cho cả UI và sim, ra **hai tên** `decision_adherence`/`event_adherence`. |
| **Thu nhập** (thống kê ca/ngày) | `driver_state.money` + history | `/api/v1/driver/history` | ✅ U2 | ❌ chưa có | Payout mặc định (card cyan); gross card riêng nhãn rõ; est_net hiển thị "—" (không đủ known costs); chart Plotly 14 ngày |
| **Chuyến của tôi** (vòng đời cuốc demo) | `trip_step` + route quote | `/api/v1/trip/step` + `/api/v1/routing/calculate` | ✅ U2 | ❌ chưa có | `trip_step.fare_vnd=null`; Web hiển thị gross/payout từ `sim-policy-v0` (`synthetic`/MOCK), không cộng vào payout ledger |
| **Xe & Pin** | `driver_state` (soc, range) | `/api/v1/driver/state` | ✅ U2 | ❌ khung | SOC là PROXY deterministic (không có trong 13 bảng GSM) — ghi chú ngay trên màn |
| **Cài đặt** (kèm picker hồ sơ) | catalog | `/api/v1/driver/catalog` | ✅ U2 | ❌ khung | Picker 150 driver × 90 ngày; rating + mission từ data; link khu Mô phỏng |
| **Mô phỏng · Replay** | `replay` v1.0 | `/api/v1/sim/replay?seed=` | ✅ U3 | ⬜ để sau (desktop-first) | Nội suy tuyến tính giữa đầu chặng (chưa bám tim đường — F-U3-A); nút ▶ chạy |
| **Mô phỏng · Hành trình** | `journey` v1.0 | `/api/v1/sim/journey?seed=&actor_id=` | ✅ U3 | ⬜ để sau | Gantt + income curve 4 nguồn + marker sự kiện + bảng offer có lý do |
| **Mô phỏng · A/B** | `ab_result` v1.0 | `/api/v1/sim/ab?seed=` | ✅ U3 | ⬜ để sau | Warning 1-seed IN CỐ ĐỊNH (contract bắt); ~30-60s/lượt |
| **Mô phỏng · Độ nhạy** | (file precomputed) | `/api/v1/sim/sweep` | ✅ U3 | ⬜ để sau | Heatmap diverging đỏ↔cyan midpoint xám tại 0; ✳ = CI không chứa 0 |

Ký hiệu: ✅ xong · 🔨 đang làm (phase ghi kèm) · ❌ cần làm để parity · ⬜ chưa cần.

## Quy tắc cho mọi màn (cả hai UI)

1. **Badge "Dữ liệu mô phỏng"** ở mọi màn có số (token `labels.mock_badge`).
2. **Tiền**: payout là số mặc định; gross chỉ hiện kèm nhãn "Doanh thu gộp"; không hứa chắc thu nhập.
   Route fare MOCK dùng cùng `gsm_sim.PolicyBundle` với Simulator: `gross = base + max(0, km-base_km)*per_km`, payout = `round(gross*driver_share)`.
3. **Màu series** theo `design-tokens.json → dataviz.categorical_*` (màu theo entity, không theo thứ tự);
   accent cyan `#00AFB9` CHỈ cho chrome (nút/badge/brand), không làm màu series.
4. Advice render từ `items[]` + `confidence` + `numbers[].source` — UI không thêm số nào tự nghĩ ra;
   trạng thái `silent` hiển thị tử tế ("Bạn đang đúng nhịp — không có gì cần chỉnh").
5. Ba màu sáng (aqua/yellow/magenta) dưới 3:1 trên nền trắng → chart dùng chúng phải có direct label
   hoặc table view (đã ghi trong tokens.provenance).
