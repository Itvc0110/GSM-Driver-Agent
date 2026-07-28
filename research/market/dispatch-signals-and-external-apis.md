# Research — Biến điều phối, API bên ngoài, taxonomy sự kiện (đợt 6b)

> **HISTORICAL RESEARCH INPUT — 2026-07-27:** bảng chọn Open-Meteo/TomTom/Nager/Ticketbox dưới
> đây là brainstorm đợt 6b, **không phải stack runtime hiện tại**. Chỉ thị/.env hiện chọn
> WeatherAPI + OSRM + Stadia + Jina; ngoài OSRM routing/cache, external context chưa được nối vào
> Advisor và chưa có refresh cadence. Xem
> [`../audit/2026-07-27-current-state/01-data-lineage-and-update-model.md`](../audit/2026-07-27-current-state/01-data-lineage-and-update-model.md).

Ngày: 2026-07-22 · Nguồn: research đợt 6b · Phục vụ: làm giàu sim + harness advisor (T-019/T-026), mở rộng `specs/environment-variables.md`
Nhãn: **[NGUỒN]** URL kiểm chứng · **[PROXY]** cơ chế quốc tế · **[ƯỚC LƯỢNG]**.

## NHÓM 1 — Biến state hệ điều phối THỰC ghi nhận

**Bối cảnh Xanh SM (quan trọng):** Xanh SM **không surge cấp tiến** kiểu Grab — chỉ xin kê khai giá linh hoạt (giảm tối đa ~8k / tăng tối đa ~22k theo khung giờ) [NGUỒN baodautu]; **Bike giữ giá gần ổn định cả giờ cao điểm** [NGUỒN dttc.sggp]. → **Cung không co giãn theo giá** → khi mưa/sự kiện, hệ dồn về hàng đợi/ETA/hủy thay vì tự cân bằng bằng giá = **dư địa advisor** (khớp realism-benchmarks NYE + environment-variables §7). Xanh SM cấm multi-app → state cung đơn giản (1 nền tảng).

| Biến state | Hệ thực dùng | Sim ta | Advisor ta |
| --- | --- | --- | --- |
| Supply/Demand ratio per hex (tính lại 30–60s) | Uber (H3), Grab, DiDi — lõi surge/reposition | ✅ per-cell | ✅ so sánh vùng |
| Demand intensity (req/cell·phút) | Uber, Grab | ✅ Poisson λ | ✅ |
| Available idle drivers/cell (+SoC/ETA) | Uber dispatch, DiDi | ✅ | ✅ |
| ETA-to-pickup dự đoán | Uber (½tr req/s), Grab traffic-aware | ✅ output dispatcher | ✅ tín hiệu "vùng căng" |
| Unfulfilled/unmatched rate | Uber: 25% khi mất surge | ✅ | ✅ |
| Cancellation rate | Uber/Grab/DiDi | ✅ (2–5% decline + no-show) | ⚠️ chỉ diễn giải |
| Waiting/queue length | Uber, DiDi batch | ✅ (expire patience) | ✅ |
| Driver idle/utilization | Uber (negative signal RL) | ✅ | ✅ (lõi khuyến nghị) |
| Trip distance + journey time (live traffic) | Grab, Uber | ✅ | ✅ |
| Historical pattern (hour×DoW) | Uber, Grab | ✅ | ✅ |
| **Tín hiệu ngoài: thời tiết, event end-time, traffic disruption** | Uber (3 external signals), Grab live-traffic | ✅ (env-vars) | ✅ = cầu nối NHÓM 2/3 |

Nguồn: [Uber marketplace RL](https://www.uber.com/us/en/blog/reinforcement-learning-for-modeling-marketplace-balance/), [Uber surge-outage 25% unfulfilled](https://www.uber.com/blog/research/the-effects-of-ubers-surge-pricing-a-case-study), [Uber surge = S/D+lịch sử+external](https://akshayghalme.com/blogs/how-uber-surge-pricing-actually-works/), [Grab dynamic pricing](https://www.grab.com/inside-grab/stories/surge-dynamic-pricing-explained/), [Xanh SM giá baodautu](https://baodautu.vn/xanh-sm-xin-ap-dung-linh-hoat-ke-khai-gia-doi-voi-dich-vu-van-tai-bang-taxi-d223870.html), [dttc.sggp Bike giữ giá](https://dttc.sggp.org.vn/dich-vu-xe-om-5-sao-xanh-sm-bike-giup-gia-tang-niem-tin-khach-hang-post108980.html).

## NHÓM 2 — API bên ngoài cho reasoning advisor (Layer C tool-calls)

| Nguồn | Data | Free | Key/.env | Forecast giờ | HN | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Open-Meteo** | mưa/nhiệt/gió hourly | miễn phí không giới hạn (non-commercial) | **KHÔNG** | ✅ tới 16 ngày + past | ✅ | **CHỌN thời tiết** |
| OpenWeatherMap | thời tiết | 60/min free nhưng chỉ 3-hourly | ✅ | ⚠️ hourly cần One Call 3.0 (thẻ) | ✅ | kém Open-Meteo |
| WeatherAPI.com | thời tiết | 1M call/tháng | ✅ | ✅ hourly ~3 ngày | ✅ | dự phòng |
| NCHMF | dự báo VN official | web | — | hạn chế | ✅ | **không API → scrape** [cần kiểm] |
| **TomTom Traffic** | flow tốc độ + incidents | freemium 2.5k+50k/ngày **không thẻ** | ✅ key free | realtime | ✅ [Traffic Index HN] | **CHỌN traffic** |
| Google Maps Routes | ETA traffic-aware | per-SKU, bỏ $200 credit từ 3/2025 | ✅ + billing thẻ | realtime | ✅ tốt nhất | ETA chuẩn nhưng không flow thô + cần thẻ |
| HERE / Mapbox | traffic + routing | 250k/200k tx/tháng | ✅ + thẻ | realtime | ✅ | dự phòng |
| **Ticketbox.vn** | concert VN | web | — | lịch tương lai | ✅ | **không API → scrape**; nguồn concert #1 |
| Google Events (SerpApi/Apify) | sự kiện tổng hợp | SerpApi ~100 free | ✅ | sắp diễn ra | ✅ | structured JSON khi cần gom |
| Facebook Graph Events | — | — | — | — | — | **KHÔNG khả dụng** (deprecated) |
| **Nager.Date** | lễ VN | miễn phí OSS + Docker offline | **KHÔNG** | cả năm | ✅ (VN) | **CHỌN holidays** |
| Điện/pin (EVN/VinFast) | chi phí NL | công bố, không API | — | — | ✅ | đổi pin 9k, Xanh SM miễn phí tới ~2028; **giá xăng không liên quan (fleet điện)** → không cần tool realtime |

**Stack tối thiểu (free/no-key ưu tiên):** Open-Meteo + TomTom (key free) + Nager.Date + scraper Ticketbox. `.env`: `TOMTOM_KEY`, (optional) `SERPAPI_KEY`/`OWM_KEY`.

## NHÓM 3 — Taxonomy sự kiện (labeled) + schema

Nguyên tắc (kế thừa environment-variables §5): sự kiện = **residual CỘNG cục bộ** (`λ_event`), KHÔNG nhân; tham số hóa bằng (a) attendance/intensity, (b) distance-decay Gauss H3, (c) time-profile **bất đối xứng** (ingress ramp trước, egress spike sắc sau). Cơ sở STAR/ST-MGCN + event-aware demand papers.

| Loại HN | Lượng đơn | Tuyến | Time profile | Không gian |
| --- | --- | --- | --- | --- |
| Concert (Mỹ Đình) | spike cục bộ lớn, **egress>ingress** | rào trước venue → ùn | ingress 3–4h trước, egress spike 22–23h | ~2–3km |
| Thể thao (SVĐ Mỹ Đình) | spike, ingress dồn sát giờ | cấm quanh sân | ingress dốc 1–2h, egress spike | ~2–3km |
| Lễ/Tết (phố cổ, Hồ Gươm) | giao thừa spike đêm; **Mùng 1–3 GIẢM MẠNH toàn thành** | phố đi bộ cấm xe | đa ngày, đỉnh 0h | countdown local; Tết **citywide** |
| Hội chợ | spike vừa kéo dài | ùn nhẹ cổng | nhiều đỉnh nhỏ | ~1–2km |
| Chính trị/diễu binh (Ba Đình 2/9) | vùng cấm ~0, **vòng ngoài tăng** | **cấm đường diện rộng** (route trội) | cấm sáng sớm nhiều giờ | lõi cấm + lan |
| Tắc/tai nạn/ngập | cục bộ, hủy tăng | tốc độ đoạn ↓ mạnh | đột ngột, tan 30–120' | rất cục bộ |
| Thời tiết cực đoan | chữ U ngược + cung↓ | tốc độ↓ vùng mưa | theo cửa sổ mưa | toàn thành/ổ mưa (env-vars §1-3) |
| Khai giảng/thi | spike sáng quanh trường | ùn cổng trường | ramp sáng, đỉnh giờ vào | nhiều điểm phân tán |
| Countdown/pháo hoa (Hồ Gươm) | spike đêm cao, egress đồng loạt | cấm quanh hồ | ingress tối muộn, egress spike sau 0h | ~1–2km lõi + lan |

### Schema labeled event (mở rộng λ_event có sẵn — thêm `route_effect` + `type`)

```yaml
event:
  type: concert         # concert|sports|festival_tet|expo|political|accident|weather|exam|countdown
  label: REAL           # REAL | MOCK (mock kèm seed+nguồn+ngày — CLAUDE.md §5)
  source_url: "..."; confidence: 0.8
  venue: {lat, lon, h3_cell}
  space: {kernel: gaussian, sigma_cells: 2.0, scope: local}   # local|citywide (Tết/thời tiết=citywide)
  time_profile:
    ingress: {start, peak, shape: ramp}
    egress:  {start, end, shape: spike, beta_out: 2.0}         # egress sắc hơn (1.5-2.5)
  demand_effect:
    mode: additive       # additive(λ_event) | multiplicative(level) cho citywide (Tết)
    attendance, capture_rate: 0.10   # 5-15% [ƯỚC LƯỢNG] → N_event
    citywide_factor: null            # Mùng 1 Tết: ~0.4 (giảm toàn thành)
  route_effect:
    closed_edges: [...]; speed_multiplier: 0.6   # → r_congestion cục bộ (survival, KHÔNG nhân demand)
    affected_cells: [...]
```

**Không double-count**: `demand_effect` → λ (cộng); `route_effect` → speed model (survival `1−r`). Hai không gian tách biệt.

Ví dụ thật: BlackPink Mỹ Đình (~31–36k/đêm, chờ ~4h, egress ùn — [vnexpress](https://vnexpress.net/hang-chuc-nghin-nguoi-do-ve-san-my-dinh-truoc-concert-2-blackpink-4635792.html), [phunuvietnam](https://phunuvietnam.vn/sau-concert-blackpink-khu-vuc-san-van-dong-my-dinh-un-tac-xe-om-cong-nghe-xep-hang-2023073023224808.htm)); Tết/2/9 [vietnam-briefing](https://www.vietnam-briefing.com/news/2026-vietnam-public-holiday-schedule-tet-national-day-holidays.html/), [Nager.Date VN](https://date.nager.at/publicholiday/vietnam/2026).

## Móc nối harness/advisor

- NHÓM 1 → sim state + advisor diễn giải (bổ sung track unfulfilled rate + idle utilization làm tín hiệu "vùng căng"; advisor KHÔNG tự tính surge — Xanh SM không surge).
- NHÓM 2 → mỗi tín hiệu ngoài = 1 tool có nhãn nguồn + confidence + fallback tắt về template (reasoning-log CLAUDE.md §5).
- NHÓM 3 → labeled events mở rộng λ_event bằng route_effect; giữ luật demand-cộng/speed-survival.

## Cần kiểm khi code (chưa xác nhận)
NCHMF API (khả năng scrape); capture_rate 5–15% + Tết citywide ~0.4 là ƯỚC LƯỢNG (nhãn mock); TomTom/Google đổi giá 2026 (kiểm quota trước khi phụ thuộc).
