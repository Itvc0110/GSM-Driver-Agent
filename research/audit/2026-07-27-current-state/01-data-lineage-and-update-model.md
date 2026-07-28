# 01 — Data lineage, schema và cơ chế cập nhật

## 1. Câu trả lời ngắn cho “mock 90 ngày là sao?”

**FACT:** repo có một manifest cho artefact `realdata-v1` ghi:

- `label = MOCK`;
- generator `gsm_core.mockgen.realdata v4 (multi-day continuous, D-SIM-13)`;
- `days = 90`, `seed_base = 7000`, `start_date = 2026-07-01`;
- ngày cuối suy ra là **2026-09-28**;
- 13 bảng `l1r`, 167.575 trip hoàn thành và 1.371.758 dòng hex tracking;
- 150 hồ sơ: 90 bike platform, 20 bike RTO, 15 car platform, 15 car employee, 10 car premium;
- engine commit được ghi trong snapshot là `d325055`, khác HEAD lúc audit là `7739b3c`.

Nguồn: [`data/mock/realdata-v1/manifest.json`](../../../data/mock/realdata-v1/manifest.json).

Vì ngày audit là 2026-07-27, snapshot chứa cả ngày quá khứ lẫn **ngày tương lai mô phỏng**. Vì vậy
không được mô tả nó là “90 ngày lịch sử gần nhất”. Tên đúng là: **một scenario synthetic liên tục
90 ngày bắt đầu 2026-07-01**.

### “Schema thật” khác “data thật” như thế nào?

| Thành phần | Trạng thái |
|---|---|
| Tên 13 bảng và tên cột `l1r` | **REAL-SCHEMA:** lấy từ metadata GSM được cung cấp cho dự án. |
| Giá trị trong từng dòng | **MOCK:** do simulator/rule generator tạo; không có record vận hành GSM. |
| Các bảng L0/L1/L2/L3/advisor khác | **PROJECT CONTRACT:** schema do dự án thiết kế, không nên gọi là “schema GSM thật”. |
| Các assumption về demand, fare, hành vi | Trộn `FACT/PROXY/MOCK/ASSUMPTION` theo tài liệu nghiên cứu; không phải calibration từ raw GSM. |

Parquet cục bộ bị gitignore; `git ls-files data/mock/realdata-v1` chỉ thấy manifest. Nghĩa là clone
repo không tự mang theo toàn bộ snapshot nếu không có bước regen/copy artefact.

## 2. Snapshot được sinh từ đâu?

Luồng hiện hành:

```text
config + policy mock + seed 7000
        │
        ├─ bike-platform (d-*) → simulator đa ngày liên tục
        │                        └─ actor/order/ledger/memory trong RAM
        │
        └─ bike-RTO/car-platform/car-employee/car-premium
                                 → generator rule-based
                         │
                         ▼
              aggregate theo 13 bảng l1r
                         │
                         ▼
        scripts/regen_mock.py --days 90 → Parquet + manifest
```

Code liên quan: [`src/gsm_core/mockgen/realdata.py`](../../../src/gsm_core/mockgen/realdata.py),
[`scripts/regen_mock.py`](../../../scripts/regen_mock.py),
[`src/gsm_sim/multiday.py`](../../../src/gsm_sim/multiday.py).

`research/market/order-distribution.md` cung cấp proxy/assumption cho hình dạng thị trường, nhưng
không phải một raw dataset được nạp thẳng vào 90 ngày. `ROUND-2-stats-report.md` kiểm phân phối trên
một ensemble 30 seed riêng; nó không đọc và chứng nhận từng file Parquet đang nằm trên đĩa. Đây là
gap đã biết `D-SIM-08`.

## 3. Schema hiện bao gồm những gì?

Toàn registry hiện có **41 entity**:

| Tầng | Entity | Vai trò |
|---|---|---|
| L0 reference | `driver_profile`, `policy_bundle`, `service_catalog`, `station_registry`, `zone_map` | Hồ sơ, policy/version, dịch vụ, trạm, vùng. |
| L1 event | `app_event`, `gps_ping`, `payout_ledger`, `policy_change_event`, `swap_transaction`, `trip_record` | Event quan sát được, thiết kế immutable. |
| L1R GSM-shaped | 13 bảng liệt kê dưới đây | Hình dạng bảng/cột theo metadata GSM. |
| L2 derived | `demand_field`, `driver_day_state`, `station_state`, `supply_field` | Projection trạng thái có `derivation_version`. |
| L2I inferred | `inferred_activity` | Hoạt động suy luận, bắt buộc confidence/rule version. |
| L3 solver views | `allocation_input`, `anomaly_alert_input`, `bonus_gap_input`, `idle_reduction_input`, `mission_select_input`, `penalty_explain_input`, `session_summary_input`, `shift_plan_input`, `weekly_khoan_input` | Input read-only cho 9 solver. |
| Advisor | `advice_request`, `solver_report`, `composed_advice` | Request, kết quả solver và output đã compose. |

### 13 bảng L1R và cột chính

| Bảng | Nội dung/cột chính |
|---|---|
| `driver_bike_stoppoints` | driver/ngày, tổng stop point, stop point giờ cao điểm. |
| `driver_income_daily` | commission, số đơn, total fee, revenue ngoài driver, average revenue, core order. |
| `driver_online_hours_sap_id` | ngày lịch, driver/SAP/hub/depot/phone/type, giờ online. Có PII nên không được log/phơi bày tùy tiện. |
| `driver_orders_rush_hours` | order/commission/fee/revenue, tách normal hour và rush hour. |
| `driver_penalization_ATA` | penalty ID/type/amount/reason/metric/code/status/time. |
| `driver_statistic_daily` | accepted/completed/cancelled và denominator; acceptance/fulfillment/cancellation/rating/5-star. |
| `kpi_driver_platform_calculator_gbq` | hồ sơ KPI tuần/tháng, contract/type, depot/vehicle/contacts/status. Có PII. |
| `public_driver_hex_tracking` | init/current/last/target hex, last seen, dwell, reached target, history/status/job metadata. |
| `public_frauds` | loại/severity/confidence/evidence/status của dấu hiệu bất thường. |
| `public_mission` | loại, thời hạn, audience, reward/claim/rule/contract/business/status. |
| `public_mission_earn_history` | mission/order/driver/service/time/status/count/earn/reward level. |
| `public_user_mission_progress` | progress/target theo count và value, state, start/update/claim time. |
| `trips` | driver/customer/service/status, request→complete timestamps, pickup/drop H3, distance/duration, gross/commission, rush/travel mode. |

Định nghĩa đầy đủ nằm trong [`schemas/l1r/`](../../../schemas/l1r/). Những bảng này có cùng shape
với metadata GSM nhưng **current rows đều MOCK**.

### Trường contract quan trọng ngoài L1R

- L0 `policy_bundle`: fare, driver share, points, bonus tiers, weekly quota, thresholds, effective range.
- L1 `payout_ledger`: `kind`, `amount_vnd`, `basis`, `gross_vnd`; đây nên là nguồn duy nhất cho tiền.
- L1 `trip_record`: request/assign/pickup/complete, location, distance và gross.
- L2 `driver_day_state`: points, acceptance, completion, online minutes, SOC với derivation/source.
- L3 `bonus_gap_input`: points, next tiers, rate lịch sử, giờ còn lại, acceptance/completion.
- L3 `shift_plan_input`: SOC/points/demand forecast/policy version.
- L3 `weekly_khoan_input`: doanh thu đến hiện tại, ngày/giờ còn lại, quota và `money_basis`.
- Advisor numbers hiện là traceable records, nhưng chưa có canonical UI card v2.

## 4. Data hiện có cập nhật sau mỗi cuốc không?

### Ma trận sự thật hiện tại

| Ngữ cảnh | Counter/state trong RAM | Ghi vào 13 bảng Parquet | UI lần sau đọc thấy | Advisor làm thay đổi metric? |
|---|---:|---:|---:|---:|
| Một run simulator | **Có**: offers/accepted/completed/cancelled/rating/mission/payout/SOC/state | Không tự động | Chỉ endpoint sim của chính run đó | Không; Advisor chỉ tác động actor qua action bridge trong sim. |
| `run_multiday` rồi export/regen | Có | **Có**, nếu chủ động chạy generator/export | Có sau khi backend reload/cache reset | Không trực tiếp. |
| App web đọc snapshot | Không có runtime actor | Không | Đọc lại cùng snapshot/cache | Không. |
| Cuốc demo `/api/v1/trip/step` | Chỉ đổi UI state của 3 cuốc mẫu | Không | Không cộng payout, không đổi acceptance/completion | Không. |
| GET `/api/v1/advice` | Read-only từ Parquet rồi chạy S1 | Không | Không | **Không** — đúng ranh giới: advisor không được ghi metric vận hành. |
| POST `/api/v1/advice/action` | Append intent `followed/dismissed/expanded` | Chỉ JSONL telemetry riêng | UI có thể đọc action log, nhưng advice lần sau không dùng | Không. |

Vì vậy câu trả lời chính xác là:

- **Trong engine:** có cập nhật ngay khi event xảy ra.
- **Trong UI snapshot:** chưa có streaming/projection update.
- **Sau cuốc demo:** chưa cập nhật payout, acceptance, completion, mission hoặc bảng nào.
- **Khi chạy Advisor:** không cập nhật data tài xế; đây là hành vi đúng. Điều còn thiếu là ingestion/projection của event thực, không phải cho Advisor quyền ghi bảng.

Code bằng chứng: [`src/gsm_sim/world.py`](../../../src/gsm_sim/world.py),
[`ui/backend/app/adapters/mockdata.py`](../../../ui/backend/app/adapters/mockdata.py),
[`ui/backend/app/main.py`](../../../ui/backend/app/main.py),
[`ui/backend/app/routers/advice.py`](../../../ui/backend/app/routers/advice.py).

## 5. UI đang đọc/cập nhật snapshot như thế nào?

`mockdata.py` dùng `_TABLES` và `@lru_cache`, nên mỗi bảng/manifest/catalog được giữ trong process.
`default_view()` chọn ngày cuối của snapshot, hiện là 2026-09-28, chứ không chọn ngày hệ thống.

Quy trình thay data hiện tại là thủ công:

1. chạy `scripts/regen_mock.py`;
2. xác nhận manifest/Parquet;
3. restart backend hoặc có cơ chế clear cache;
4. reload client.

Không có scheduler, CDC, queue, webhook hay polling production nào trong code hiện tại.

## 6. External data: nguồn nào có và cadence ra sao?

| Nguồn | Config/key | Runtime hiện tại | Cadence hiện tại |
|---|---|---|---|
| OSRM | `OSRM_BASE_URL`, không cần key | Sim dùng ma trận route đã fetch/cache offline; UI route proxy gọi OSRM khi người dùng tính route. | On-demand ở UI; prefetch/offline trong sim. Không có refresh scheduler chung. |
| WeatherAPI | key/base URL có trong `.env(.example)` | Chưa có `ExternalContext` đi vào Advisor/sim product path. | **Chưa implement.** |
| Stadia | key/base URL | Configured cho tiles/geocode; chưa là feature input của Advisor. | **Chưa implement cadence.** |
| Jina Reader | key/URL | Dùng như công cụ nghiên cứu/crawl, chưa có policy ingestion scheduler runtime. | Thủ công. |
| Langfuse | key/host | Observability tùy chọn, không phải source metric tài xế. | Theo trace khi bật; không cập nhật domain data. |
| Google Maps | optional key | Cường đã chốt không cần; OSRM + Stadia + OSM thay thế. | Không áp dụng. |

`research/market/dispatch-signals-and-external-apis.md` là brainstorm lịch sử chọn Open-Meteo,
TomTom, Nager.Date và Ticketbox. Nó không phản ánh stack hiện tại trong `DIRECTIVES`/`.env`, và
không có provider nào trong nhóm đó đã được nối vào advice.

## 7. Mô hình cập nhật đích — PROPOSAL, chưa implement

Kiến trúc B cần tách “event thật” khỏi “Advisor đọc”:

```text
offer/accept/decline/pickup/complete/cancel/payout/policy event
                         │ append, idempotent
                         ▼
                 canonical event log
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
 runtime projection  payout/mission    daily/weekly aggregates
 (near real-time)       ledger          (incremental/batch)
        └────────────────┼─────────────────┘
                         ▼
              immutable as-of snapshot
                         ▼
               Advisor read-only decision
                         ▼
         advice lifecycle/action events riêng
```

Cadence đề xuất theo loại dữ liệu:

| Loại | Cadence đích | Ghi chú |
|---|---|---|
| Offer/accept/decline/pickup/complete/cancel | Event-driven, near real-time | Update projection theo transaction/idempotency key. |
| Payout/bonus/penalty/mission ledger | Event-driven theo posting; reconciliation batch | Không suy ngược tiền từ UI hay routing distance. |
| Acceptance/completion đang trong ca | Projection từ counts đến `as_of`; không lấy whole-day tương lai | Hiển thị sample size và estimator version. |
| Aggregate ngày/tuần GSM-shaped | Incremental hoặc batch sau cut-off | Giữ event time và ingestion time riêng. |
| Policy/mission validity | Versioned change event + polling/webhook tùy nguồn | Không cache vô hạn; `effective_at` khác `observed_at`. |
| Weather/traffic/event ngoài | TTL theo provider/use case | Sim dùng trace đã đóng băng; product có cache/freshness/fallback. |
| Advice/actions | Append-only riêng | Không sửa metric tài xế; join qua decision/display/event ID. |

## 8. Blocker schema versioning

`schemas/README.md` nói additive minor bump tương thích, nhưng `SchemaRegistry` hiện chỉ load một
file cho mỗi entity; schema lại khóa `schema_version.const` và `additionalProperties: false`.
Nếu thay file `1.0.0` bằng `1.1.0`, record cũ không tự được validate song song hoặc upcast.

**BLOCKER-ARCH-VERSION:** trước khi migration cho kiến trúc B/ĐA-05/ĐA-06, cần một trong ba cơ chế:

1. registry đa phiên bản theo `(entity, version)`;
2. upcaster explicit, có test round-trip/backward compatibility;
3. lưu schema versioned thành file riêng và chọn đúng schema theo record.

Không được gọi minor bump “backward compatible” cho tới khi test bằng record cũ thực sự pass.
