# P2 — Schema re-ground plan (13 bảng thật = source-of-truth → L0–L3 mới)

Cập nhật: 2026-07-24 · Part 2/7 · Trạng thái: **⚠ 2026-07-29: ĐÃ CODE** (PI-1 — 13 schema `l1r/*` + registry, UPDATE-034); blueprint gốc (DESIGN, plan cho cycle impl, CHƯA code) giữ để đối chiếu lịch sử.
Quyết định Cường: **re-ground về bảng thật**. Nguyên tắc: schema thật = canonical L1'; L0 config (rule/không gian) giữ; L2/L3 recompute; versioning additive; PII per field.

## 1. Kiến trúc lớp SAU re-ground

```
L0 REFERENCE / CONFIG (KHÔNG có trong 13 bảng → giữ config/KB/external)
  PolicyBundle (rule số: point/tier/khoán/clawback — versioned)  · ServiceCatalog
  StationRegistry/ZoneMap (OSM VinFast)  · MissionCatalog (= public_mission, nửa-reference)
        ↓ (data thật export)
L1' MEASURED = ĐÚNG SHAPE 13 BẢNG THẬT (canonical, source-of-truth)
  KPI daily:  driver_statistic_daily · driver_online_hours · driver_orders_rush_hours
              · driver_bike_stoppoints · driver_income_daily
  KPI weekly: kpi_driver_platform_calculator
  events:     trips · driver_hex_tracking · mission_earn_history · driver_penalization · frauds · user_mission_progress
        ↓ derivation JOB (versioned)
L2 STATE (recompute từ L1' — nếu L1' đã aggregate thì L2 mỏng đi)
  DriverDayState (≈ driver_statistic_daily) · DriverWeekState (MỚI ≈ kpi_calculator)
  DemandDensity(hex,bucket) (từ trips) · IdleState (từ hex_tracking)
L2i INFERRED (tách riêng): InferredActivity, AnomalyFlag(từ frauds+lệch route), PenaltyRisk
        ↓ feature view
L3 SOLVER INPUTS  (remap sang field thật)
  BonusGapInput · ShiftPlanInput · SessionSummaryInput · AllocationInput
  + WeeklyKhoanInput (S5) · MissionSelectInput (S6) · IdleReductionInput (UC5) · PenaltyExplainInput (UC6)
```

## 2. Bảng đối chiếu: schema CŨ → hành động

| Schema hiện có | Hành động | Lý do |
|---|---|---|
| `l1/trip_record` | **GIỮ + đối chiếu** `trips` (bổ sung cột khi GSM cho) | trips ~ trip_record; nền demand |
| `l1/gps_ping` | **DEPRECATE → thay** `driver_hex_tracking` (H3-agg) | real chỉ có hex-agg, không raw ping |
| `l1/app_event` | **GIỮ (sim-only)** + đánh dấu: real KHÔNG export event thô; rate/counts lấy từ `driver_statistic_daily` | dùng cho sim & derive mock aggregate |
| `l1/payout_ledger` | **GIỮ** + map: kind=trip_payout↔commission, deduction↔penalization, week_bonus↔mission/KPI | real income ở `driver_income_daily` (agg) |
| `l1/swap_transaction` | **GIỮ (mock/external)** — không có bảng thật | pin từ mock+OSM (P5) |
| `l2/demand_field`,`supply_field`,`station_state` | **GIỮ (derive/mock)** — real chỉ suy được demand từ trips | P5 gap |
| `l2/driver_day_state` | **RE-GROUND** = mirror `driver_statistic_daily` (rate đọc thẳng) | thật hơn suy từ event |
| `l0/policy_bundle` | **GIỮ + mở rộng** (weekly-khoan spec: service points, weekly_quota) | rule không có trong 13 bảng |
| `l0/driver_profile` | **GIỮ + map** sap_contract_type→track, depot/hub, vehicle | từ online_hours/kpi_calculator |
| `l0/service_catalog`,`zone_map`,`station_registry` | **GIỮ** | reference |

## 3. Schema JSON MỚI cần viết (cycle impl P-impl-1)

| File | ≈ bảng thật | Ghi chú |
|---|---|---|
| `l1r/driver_statistic_daily.schema.json` | 1:1 (15 cột) | rate + counts + rating |
| `l1r/driver_online_hours.schema.json` | 1:1 (10, drop PII) | online_time |
| `l1r/driver_orders_rush_hours.schema.json` | 1:1 (14) | rush/normal split |
| `l1r/driver_bike_stoppoints.schema.json` | 1:1 (4) | idle proxy |
| `l1r/kpi_weekly_calculator.schema.json` | 1:1 (21, drop PII) | weekly KPI |
| `l1r/driver_income_daily.schema.json` | 1:1 (8) | payout breakdown |
| `l1r/driver_hex_tracking.schema.json` | 1:1 (19) | reposition/idle |
| `l1r/mission_catalog.schema.json` | public_mission (28) | reference mission |
| `l1r/mission_earn_history.schema.json` | 1:1 (21, drop customer_id) | earn history |
| `l1r/user_mission_progress.schema.json` | INFER (thiếu cột) | `TBC-với-GSM` |
| `l1r/driver_penalization.schema.json` | INFER (thiếu cột) | `TBC-với-GSM` |
| `l1r/fraud_flag.schema.json` | INFER (thiếu cột) | `TBC-với-GSM` |
| `l1r/trips.schema.json` | INFER từ trip_record | `TBC-với-GSM` |

(prefix `l1r/` = L1-real; giữ `l1/` cũ cho sim tới khi hợp nhất — tránh phá 162 test một nhịp.)

## 4. Quy ước bắt buộc mỗi schema mới

- `schema_version` semver; thêm field = optional + minor bump; bỏ = `deprecated_since`.
- `source` enum {MOCK, REAL, ESTIMATED, COARSE, INFERRED} — **mọi record gắn nhãn** (CLAUDE.md §5).
- **PII per field**: `x-pii: true` + `x-pii-action: drop|hash|keep` (dùng cho P4 tool). PII = full_name, phone_number, email, tel, sap_id, sap_profile_id, driver_name, vehicle_vin_number, vehicle_license_plate, customer_id.
- `x-availability: CONFIRMED | TBC-với-GSM` per field; 5 bảng infer = TBC toàn bộ.
- `datastream_metadata` → optional object nullable (không dùng logic).

## 5. Registry + validator + changelog
- `SchemaRegistry` (`gsm_core/schema_registry.py`) thêm layer `l1r`; `LAYER_OF` map.
- `schemas/CHANGELOG.md`: entry re-ground (minor→có thể major nếu deprecate gps_ping). Migration note: `l1/` cũ song song `l1r/` mới, hợp nhất ở phase sau.

## 6. Acceptance P2 (cho cycle impl)
- 13 schema `l1r/*` viết + validate example record; registry nhận layer mới.
- PII/availability annotation đủ; 5 bảng infer đánh dấu TBC.
- Test: validate 1 record/bảng (mock nhỏ) pass; 162 test cũ KHÔNG đổi (l1/ giữ nguyên).
- Bảng "cũ→hành động" (§2) thực thi đúng: không xóa thẳng, deprecate có nhãn.

## 7. Rủi ro / cần chốt
- **Major vs minor bump** nếu deprecate gps_ping → hỏi Cường khi impl.
- Hợp nhất `l1/`(sim) vs `l1r/`(real): giữ 2 nhánh hay adapter 1 chiều — quyết ở P7 roadmap.
