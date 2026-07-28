# Schema changelog

## 2026-07-28 — Cycle V: registry ĐA PHIÊN BẢN (gỡ B-02) + 2 thay đổi

- **CƠ CHẾ**: validate route theo `record["schema_version"]`; lịch sử = `{entity}@{ver}.schema.json`;
  version lạ fail-loud; upcaster `src/gsm_core/upcasters.py`; backward-compat test bằng record
  persist thật. Quy trình bump mới trong README.
- **`shift_plan_input` 1.0.0 → 1.1.0** (minor, additive): +`rest_taken_min`, +`shift_elapsed_min`
  (optional/nullable — Cycle R, UPDATE-085). Snapshot `shift_plan_input@1.0.0.schema.json`;
  upcaster 1.0.0→1.1.0 = stamp (không bịa giá trị nghỉ). Producer bridge emit 1.1.0; producer
  l1r/features giữ 1.0.0 — hai version sống song song hợp lệ.
  ⚠ Đính chính quy trình: đợt Cycle R (2026-07-28 sáng) đã thêm 2 trường này mà KHÔNG bump —
  đúng anti-pattern B-02; entry này trả nợ. 5 đợt additive trước đó (xem các entry dưới) cũng
  không bump — chấp nhận làm lịch sử, không truy bump hồi tố (record cũ vẫn validate vì các đợt
  đó đều additive-optional với chính schema hiện hành 1.0.0 của chúng).
- **`market_state_view` MỚI** (l3, 1.0.0): view T-045a từng emit `schema_version` mà không có
  schema/entity nào trong registry — validate không thể chạm tới. Nay đăng ký + test payload thật.


## 2026-07-24 (PI-5c, UPDATE-042) — additive

- `l3/penalty_explain_input` (mới): input S8 UC6. Số tiền trừ từ `driver_penalization_ATA`;
  ngưỡng từ policy. Guardrail: giải thích QUY TẮC — KHÔNG dạy lách.
- `l3/anomaly_alert_input` (mới): input S9 UC7, `source=INFERRED`. **KHÔNG mang
  `evidence_ref`** sang view (chống lộ cách phát hiện). Guardrail: KHÔNG kết tội.
- `advisor/solver_report.solver`: enum **+`penalty_explain`, +`anomaly_alert`** → đủ 9 solver.

## 2026-07-24 (PI-5b, UPDATE-041) — additive

- `l3/idle_reduction_input` (mới): input S7 IdleReduction (UC5). `hex` CHỈ để thống kê —
  D-004b/B1 cấm dùng để chỉ định chỗ đứng; `active_reposition` chỉ từ campaign CHÍNH THỨC.
- `advisor/solver_report.solver`: enum **+`idle_reduction`**.

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
