# Schema changelog

## 2026-07-24 (PI-4b, UPDATE-038) — additive, KHÔNG phá contract cũ

- `l0/policy_bundle`: **+`weekly_quota`** optional `{min_revenue_vnd, min_active_days,
  clawback_rate, market_scope}` — khoán tuần Vận Doanh 23/02/2026. Số = **TBC-với-GSM**
  (image-locked); `null` ⇒ solver S5 **KHÔNG được suy đoán mốc** (§5).
- `advisor/solver_report.solver`: enum **+`weekly_khoan`, +`mission_knapsack`** (enum đóng
  → phải khai tường minh khi thêm solver).
- `l3/weekly_khoan_input` (mới): input S5; `money_basis ∈ {gross, driver_payout}`,
  mặc định **gross** (quyết định (d) 2026-07-24, nhãn ASSUMPTION).
- `l3/mission_select_input` (mới): input S6; `reward_vnd` chỉ lấy từ `mission_catalog`.
- Tất cả field mới là **optional/additive** → 13 schema `l1r` + 23 entity cũ không đổi;
  suite cũ vẫn xanh.

## 2026-07-24 (PI-1, UPDATE-034) — layer `l1r`

- **+13 entity `l1r/*`** mirror bảng thật `gsm-data-prod` (KPI daily/weekly, trips,
  hex_tracking, mission×3, penalization, fraud). 5 bảng thiếu cột thật được **ENGINEER**
  với nhãn `x-availability: TBC-với-GSM`; PII khai qua `x-pii-columns` (optional field
  ⇒ record sau khi tool scrub vẫn validate).

## 1.0.0 — 2026-07-23 (T-038 C0, UPDATE-024)

- Initial: 23 entity across l0/l1/l2/l2i/l3/advisor theo spec
  `core-data-schema-and-advisor-architecture.md` v1.1.
- Ghi chú thiết kế:
  - `payout_ledger` tách gross/payout tại nguồn; **net-input entity CHƯA có**
    (chờ known costs — thuê xe/điện per track; thêm khi T-011 policy registry
    hoặc GSM export chi phí; sẽ là minor bump).
  - `policy_bundle.track` có `green_bike_unspecified` (guardrail T-004 — không auto-map).
  - `trip_record.dist_km` theo distance contract M0-9 (= haversine endpoints trong mock).
  - `advice_request.trigger_source` theo advice-timing spec (user_ask/anchor/event_trigger).
- TBC-với-GSM (fallback trong spec §1.6): GPSPing tần suất; swap wait đo trực tiếp;
  SOC telemetry; demand request-log (unserved).
