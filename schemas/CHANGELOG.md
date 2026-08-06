# Schema changelog

## 2026-08-05 — AdviceCheckpoint facts nền móng (1.2.0, UPDATE-147)

- **`advisor/advice_checkpoint` 1.1.0 → 1.2.0**: thêm `numbers[]` ({value, unit, source}
  của solver report — typed, có provenance), `caveats[]` (string) và `fingerprint`
  (material digest) vào record. Trước đây cả ba bị strip khi persist ⇒ card nghèo facts
  và dedup product không bao giờ khớp record đã lưu. Snapshot `advice_checkpoint@1.1.0`
  giữ nguyên; upcaster 1.1→1.2 điền `numbers=[]`/`caveats=[]` (record cũ không lưu —
  không bịa) và TÁI LẬP `fingerprint` từ chính material fields đã persist.
- Fingerprint material bổ sung `future_head` (code + window của hành động kế tiếp):
  plan đổi bucket SWAP là một lời khuyên KHÁC, không được dedup nhầm với revision cũ.
- Lifecycle transition mở thêm `ready → queued` (tài xế bắt đầu di chuyển sau khi
  checkpoint ready — moving gate ghi dấu vết thay vì silent trắng).

## 2026-08-03 — AdviceCheckpoint runtime contract (1.1.0)

- **`advisor/advice_checkpoint` 1.0.0 → 1.1.0**: thêm identity/reference tách bạch
  `source_decision_id`, `run_id`, `solver_input_refs[]`, `solver_report_refs[]` để replay
  tới exact solver artifacts mà không overload/backfill `decision_id` legacy.
- **`advisor/advice_checkpoint_event` 1.0.0 → 1.1.0**: thêm event `expanded` dạng
  side-channel; event này và `execution_observed` không đổi presentation state.
- **`advisor/advice_artifact` 1.0.0 → 1.1.0**: thêm kind `agent_shadow_output` cho
  evaluation artifact không được phép đi vào response/lifecycle tài xế.
- Ba schema giữ snapshot 1.0.0 và pure upcaster 1.0→1.1; runtime producer luôn điền refs,
  còn record cũ được upcast với refs nullable/rỗng đúng lịch sử.
- Thêm contract đóng `agent_presentation_input@1.0.0` và
  `agent_presentation_output@1.0.0`; output agent chỉ được tham chiếu fact/number/caveat ID
  và enrich phần lý do, không sở hữu action/window/expiry/source/số tự do.

## 2026-08-03 — AdviceCheckpoint shadow contract (1.0.0)

- **`advisor/advice_artifact`**, **`advisor/advice_checkpoint`** và
  **`advisor/advice_checkpoint_event`** là contract mới cho presentation lifecycle shadow.
  Checkpoint không overload `decision_id` legacy; event stream có các trạng thái
  `created/queued/ready/offered/displayed/...` và `execution_observed` là liên kết độc lập.
- Store tương ứng là SQLite append-only, content-addressed artifacts và idempotent theo
  `checkpoint_id`/`event_id`. Đây là snapshot lịch sử trước runtime v2; không dual-write
  legacy lifecycle.

## 2026-07-29 (chiều) — B3: `policy_bundle` 1.0.0 → 1.1.0 (+`costs` optional)

- **`l0/policy_bundle` 1.1.0** (minor, additive): +khối `costs` optional —
  `battery_free_until` (Platform độc quyền: 2029-03-31, official greensm 26/03/2026),
  `swap_fee_vnd` (9.000đ/lượt sau ưu đãi), `battery_rent_vnd_month`,
  `swap_range_km_per_pack`, `cash_cost_vnd_per_km_by_track`. Snapshot
  `policy_bundle@1.0.0.schema.json` dựng từ git HEAD (đúng quy trình); upcaster
  1.0.0→1.1.0 = stamp-only (KHÔNG bịa costs cho record cũ — vắng mặt ⇒
  `resolve_cost_params` trả UNKNOWN). Consumer: `gsm_core/policy.py::resolve_cost_params`
  (3 trạng thái ACTIVE/OFF_BY_POLICY/UNKNOWN) + `shift_dp.solve` qua
  `params["policy_costs_as_of"]` (opt-in — caller cũ nguyên vẹn). Tương thích: record
  1.0.0 persist vẫn validate pass (test_mockgen + test_schema_versioning xanh).

## 2026-07-29 (muộn) — Cycle W đóng: siết `occurred_at`/`observed_at` TẠI CHỖ (1.0.0)

- **`advisor/advice_lifecycle_event`**: pattern hai trường timestamp siết dần qua 2 đợt
  review đối kháng — (đợt 1, W-4b) giờ `([01]\d|2[0-3])`; (đợt 2, F-S4) tháng `01-12`,
  ngày `01-31`, offset giờ `00-23`. **Không bump version — lý do ghi tường minh** (README
  bước 2 yêu cầu khai): đây là bugfix NARROWING chặn record độc (`T24:00:00`, tháng 13…
  từng lọt regex rồi giết toàn bộ projection — store append-only không gỡ được), và
  **không record persist nào từng mang giá trị bị siết** (store mới ra đời trong chính
  cycle này, chỉ có ở tmp/test). Lớp chặn THẬT là `datetime.fromisoformat` tại
  `event_log.append` (X-1 — regex không kiểm được lịch: `2026-02-31` khớp mọi pattern);
  regex chỉ là tài liệu + lớp phòng đầu. Description `run_id` sửa theo format thật của
  `runner.derive_run_id` (thêm `-c{digest8}`, bỏ `-d{day}` không tồn tại — F-S3).

## 2026-07-29 — Cycle W (ĐA-05): advice lifecycle event log

- **`advisor/advice_lifecycle_event` MỚI (1.0.0)**: envelope một event vòng đời advice —
  append-only, idempotent theo `event_id`; IDs tách vai trò `decision_id`/`display_id`/
  `event_id`; `occurred_at`+`observed_at` ISO; `actor`/`origin`/`source`; `reason_code`;
  `context_revision` (chỗ cho ĐA-04 material_revision). Store: `gsm_core/lifecycle/event_log.py`
  (validate qua registry TRƯỚC khi ghi); projections MỘT LUẬT (UI + sim):
  `gsm_core/lifecycle/projections.py`. Ba namespace decision_id hợp pháp ghi trong
  description: `adv-*` (pipeline) / `s1-*` (UI) / `slth-*` (sim, deterministic).

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
