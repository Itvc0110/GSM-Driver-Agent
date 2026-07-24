# P5 — Gap analysis + mock-supplement + external data (brainstorm sâu)

Cập nhật: 2026-07-24 · Part 5/7 · Trạng thái: DESIGN
Trả lời Cường #3 + yêu cầu "brainstorm thật kỹ data thu thập qua công cụ bên ngoài giúp/xây feature". **Mọi techstack/API-key/env → HỎI Cường, không tự điền** (§4).

## 1. 13 bảng thật THIẾU gì (đều driver-centric)

| Thiếu | Có suy được không | Nguồn thay |
|---|---|---|
| **Demand/mật độ KHÁCH theo hex×giờ** | 1 phần: aggregate `trips` (nơi có cuốc) — nhưng chỉ nơi ĐÃ serve, không có unserved/nhu cầu tiềm ẩn | trips-agg (served) + **external POI/traffic PROXY** + mock unserved (nhãn ESTIMATED) |
| **RULE số policy** (điểm/tier/khoán/clawback/target KPI) | KHÔNG (bảng chỉ có kết quả, không có rule) | `policy_bundle` versioned (weekly-khoan spec) + F0 corpus + `kpi_calculator` target (nếu GSM chỉ chỗ) |
| **Station/pin telemetry** (queue, pin ready) | KHÔNG | OSM 144 trạm VinFast (có sẵn) + mock queue (ESTIMATED) |
| **Raw GPS/tốc độ** | KHÔNG (chỉ hex-agg) | `driver_hex_tracking` (coarse) + sim cho fine-grain |
| **Thời tiết / sự kiện / lễ** | KHÔNG | **external API** (§3) |
| **Chi phí net** (điện, thuê, khấu hao) | 1 phần (`revenue_not_relate_driver`) | known-cost config + external giá điện |
| **Customer wait / matching** | KHÔNG | không mô hình (ngoài scope) |

## 2. Mock-supplement: future-harvestable vs external vĩnh viễn

- **(a) Future-harvestable** — mock GIỜ, thay data thật GSM SAU (nhãn MOCK→REAL khi có): demand density (từ trips thật), station telemetry, cột 5 bảng thiếu (penalization/fraud/progress/trips), target KPI tuần. ⇒ mock có nhãn, cấu trúc khớp để swap.
- **(b) External vĩnh viễn** — KHÔNG bao giờ là GSM data, luôn từ API ngoài (nhãn PROXY/EXTERNAL): thời tiết, đường xá/POI, lễ/sự kiện, giá điện. **Không fake thành fact GSM.**
- **Cấm**: fake số tài chính/policy (§5 CLAUDE.md); external chỉ làm context/PROXY, không thành số payout/policy.

## 3. External data BRAINSTORM (giúp feature nào / xây feature gì)

| Nguồn | Data | Giúp/Xây feature | Nhãn | Cần key/techstack |
|---|---|---|---|---|
| **Google Maps — Directions/Distance Matrix** | route thật, ETA, khoảng cách đường | ETA/route thật cho sim & **route-deviation** (UC7 anomaly: lệch route thật vs đi thực); idle/reposition (UC5) chính xác hơn haversine×detour | REAL(route) | Google Cloud API key |
| **Google Maps — Places/POI** | bệnh viện/TTTM/bến xe/trường/văn phòng + độ phổ biến | **PROXY điểm nóng nhu cầu** (F2 gợi ý thời điểm; KHÔNG khẳng định = mật độ khách) | **PROXY** (≠ demand khách) | Google key |
| **Google Maps — Roads/Traffic** | mật độ đường, kẹt xe theo giờ | congestion cho shift/idle timing; travel_mode | PROXY | Google key |
| **Weather API** (OpenWeather / VN) | mưa/nhiệt/gió theo giờ×vùng | **weather-aware F1/F2** (mưa→demand↑ nhưng risk↑); demand-shift scenario; giải thích hiệu suất (UC6) | EXTERNAL | API key |
| **Lịch lễ/sự kiện VN** (holiday API + event feeds) | lễ, concert, phố đi bộ | **event-aware demand spike** (F1 kế hoạch tuần; K-PULSE research) | EXTERNAL | có thể free/static |
| **OSM** (đã dùng) | road graph, POI, ranh giới, 144 trạm pin | pilot world, station layer, zone_map | REAL(geo) | không key (đã có) |
| **GTFS giao thông công cộng** | bến bus/metro | PROXY last-mile demand quanh bến | PROXY | dữ liệu mở |
| **Giá điện EVN** | biểu giá điện | estimated_net (chi phí sạc) | EXTERNAL | tra cứu tĩnh |

**Ưu tiên (ROI cao, ít phụ thuộc):** (1) Google Directions cho route-deviation+ETA (mở UC7 mạnh); (2) Weather; (3) POI proxy; (4) holiday/event. GTFS/giá điện = nice-to-have.

**Rủi ro external:** quota/cost API (Google tính tiền → cần cache + budget); PROXY bị hiểu nhầm thành demand thật → **nhãn cứng + disclaimer**; phụ thuộc mạng → cache offline + fallback.

## 4. TECHSTACK & ENV cần Cường chốt (KHÔNG tự điền)
> Hỏi trước khi thêm dep hoặc điền `.env`:
1. **Có dùng Google Maps Platform không?** Nếu có: cấp `GOOGLE_MAPS_API_KEY`, chốt các API (Directions/Places/Distance) + budget/quota. Lib: `googlemaps` hay REST thuần?
2. **Weather provider?** OpenWeatherMap (key) vs nguồn VN vs bỏ. `WEATHER_API_KEY`.
3. **Holiday/event**: dùng lib tĩnh (`holidays`) hay feed ngoài?
4. Có cần **cache layer** external (parquet/sqlite) + TTL — chốt cách.
5. Tất cả external = optional extra riêng (`extern`), không vào core deps.

→ Mặc định: KHÔNG tích hợp external nào tới khi Cường chốt key/techstack. Plan này chỉ liệt kê + thiết kế chỗ cắm (adapter `ExternalContext` song song `DataSource`).

## 5. Chỗ cắm external trong kiến trúc
`ExternalContext` provider (giống `DataSource`): `weather(hex,t)`, `poi_density(hex)`, `route(a,b)`, `is_event(t,zone)` → trả **có nhãn PROXY/EXTERNAL + confidence**; solver/agent chỉ dùng làm **context/feature phụ**, KHÔNG thành số tài chính/policy. Cache + fallback offline. Mock provider cho test (deterministic).

## 6. Acceptance P5
Bảng gap đủ; phân loại future-harvestable vs external rõ; brainstorm external ≥7 nguồn có nhãn + ROI; mục techstack/env liệt kê câu hỏi cho Cường; chỗ cắm `ExternalContext` thiết kế (chưa code). Không tự thêm dep/key.
