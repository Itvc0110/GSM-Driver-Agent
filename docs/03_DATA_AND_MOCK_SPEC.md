> ⚠️ **DEFERRED — 2026-07-20.** Tài liệu thuộc cách tiếp cận cũ (full multi-variable constrained optimization). Scope hiện hành: `CLAUDE.md` + `planning/SCOPE.md`. Chỉ dùng tham khảo (xem `tracking/DEFERRED.md`, mục D-001). Riêng nguyên tắc mock/provenance vẫn đáng kế thừa.

# 03 — Data and Mock Specification

## 1. Data principles

1. Domain-first contract; source payload được map qua adapter.
2. Event time khác ingestion time; late/out-of-order phải được xử lý rõ.
3. Mọi giá trị dùng để khuyên có provenance, freshness, quality và version.
4. Synthetic, replay, shadow và live là bốn mode tách biệt.
5. Personalization tối thiểu hóa PII và có purpose/consent/retention.
6. Monetary value dùng minor unit integer (`VND` vẫn là integer), không float.
7. Geospatial dùng zone/H3-like cell đã duyệt; exact coordinate chỉ ở operational boundary cần thiết.
8. Compensation/policy effective-dated; không rewrite lịch sử theo policy mới.

## 2. Data modes

| Mode | Purpose | Allowed claims | Forbidden |
| --- | --- | --- | --- |
| `synthetic` | scaffold, demos, edge cases | contract/logic works on scenarios | accuracy/uplift/ROI claim |
| `replay` | historical backtest | behavior on logged data under assumptions | causal claim without counterfactual |
| `shadow` | real-time compare, no exposure | latency/calibration/data quality | driver impact claim |
| `live` | approved pilot/product | causal/operational result under design | mixing synthetic features |

## 3. Common envelope

Mỗi event/snapshot có: `id`, `schema_version`, `event_time`, `ingested_at`, `source_system`, `source_record_id`, `data_mode`, `is_mock`, `quality_status`, `fresh_until`, `market_id`, `service_type`, `trace_id`. PII-bearing records thêm `purpose`, `consent_version`, `retention_class`.

## 4. Entity/data dictionary

### Driver and preference

- `driver_pseudonym`, `driver_profile_version`, `market_id`.
- `engagement_model`: employee/partner/other/unknown.
- `eligible_service_types`, `vehicle_profile_id`, `policy_bundle_id`.
- Explicit: availability windows, target net income, hard end time, blurred end zone, max reposition/time, risk mode, preferred break windows, opt-outs.
- Learned: time/zone preference distribution, recommendation response history, calibration/trust state; always confidence + updated time.
- Không suy đoán family/health/sensitive reason. Lưu constraint, không cần lý do đời tư.

### Vehicle/energy

- profile/type/class/service capability; battery capacity/usable SOC/reserve policy.
- current SOC, range band, telemetry time/quality.
- consumption distribution by distance/time/traffic/weather; charging curve/connector.
- depot/lease/energy cost ownership as policy references, not a universal field assumption.

### Shift/session

- shift ID/status, planned/actual start, hard/soft end, current zone.
- online, occupied, pickup, idle, reposition, charging, break durations.
- continuous-driving/working counters supplied by approved policy computation.
- current plan/recommendation IDs; last meaningful event.

### Earnings/bonus

- immutable ledger entries: trip gross, share/commission, incentive/bonus, energy, fee, approved penalty/adjustment, tax/other if in scope.
- `economic_owner` and inclusion in `net_earnings_definition_version`.
- bonus program/tier, eligibility rules, progress, expiry/effective window, probability estimate provenance.
- Reconciliation status; unfinalized earnings được gắn provisional.

### Trip aggregates

- completed trip timestamps, origin/destination zone, occupied/pickup distance/time, gross/net components, service type, completion/cancel outcome theo approved scope.
- Phase 1 không expose live order candidates cho optimizer.

### Environment/fleet

- zone/time bucket demand distribution; available/committed supply distribution.
- trip duration/fare/destination transition distributions, not only mean.
- traffic/travel-time matrix quantiles; weather/event features with source.
- Phase 2: recommendation exposure/reservation count và opportunity capacity.

### Charging

- station/connector compatibility, zone, travel-time distribution.
- observed/forecast queue, available capacity, freshness, outage.
- charge duration/energy/cost distribution; approved booking/reservation capability.

### Policy

- policy bundle, version, effective_from/to, market/service/profile scope.
- action allowlist, safety/driver-time constraints, battery reserve, bonus rules, platform floors, feature flags, fairness budgets.
- legal/compliance owner và approval status.

### Recommendation/outcome

- exposure channel/time, expiry, options shown/order, chosen/ignored/adjusted.
- optional ignore reason taxonomy, never punitive.
- actual subsequent state/outcome window; attribution eligibility; model/policy versions.

## 5. Freshness and quality

Freshness SLA trong code là config theo source/use case, không dùng một con số toàn hệ thống. Mẫu quality state: `OK`, `LATE`, `STALE`, `MISSING`, `OUTLIER`, `SCHEMA_MISMATCH`, `UNTRUSTED`, `MOCK_LEAK`. Candidate declares required/optional features và fallback. Một feature stale có thể làm giảm confidence; safety/policy/critical battery stale phải veto.

Validation layers:

- schema/type/range/unit/timezone;
- referential and temporal consistency;
- monotonic counters/ledger reconciliation;
- cross-source consistency (SOC/range, trip/earnings);
- distribution drift/missingness/outlier;
- leakage check: không dùng future events trong forecast/evaluation;
- privacy and purpose checks.

## 6. Synthetic generator

Generator nhận `scenario_id`, `seed`, `start_time`, `market_config`, `driver_profile`, `vehicle_profile`, `policy_bundle`, duration và perturbations. Output gồm immutable events + oracle/correct invariants, không chỉ một JSON snapshot.

Scenario bắt buộc:

1. `NORMAL_WEEKDAY_BALANCED`.
2. `RAIN_PEAK_HIGH_DEMAND_HIGH_TRAFFIC`.
3. `LOW_DEMAND_LONG_IDLE`.
4. `CHARGER_CONGESTION_AND_OUTAGE`.
5. `STALE_TRAFFIC_OR_DEMAND_FEED`.
6. `BONUS_NEAR_TIER_BUT_NEGATIVE_INCREMENTAL_NET`.
7. `LOW_SOC_NEAR_RESERVE`.
8. `HARD_HOME_DEADLINE`.
9. `CONFLICTING_CONSTRAINTS_INFEASIBLE`.
10. `FLEET_OVERSUPPLY_FROM_RECOMMENDATIONS`.
11. `NEW_DRIVER_NO_HISTORY`.
12. `PREMIUM_ELIGIBILITY_POLICY_CHANGE`.

Mỗi scenario có expected invariants, ví dụ low SOC không bao giờ phát `CHARGE_LATER` vượt reserve; stale charger feed không nêu exact wait; infeasible không relax safety.

## 7. Mock-to-real migration

1. Freeze canonical schemas và example fixtures.
2. Viết source adapter + mapping tests; không đổi domain để khớp source.
3. Chạy dual-read/shadow và field-level comparison.
4. Lập data availability/quality report; đánh dấu feature unavailable.
5. Recalibrate forecast/economic definitions trên real data.
6. Privacy/security/compliance review và retention config.
7. Bật cohort shadow; synthetic adapter bị build/runtime guard chặn ở live.
8. Chỉ pilot sau causal design và operational rollback.

## 8. Privacy decisions

- Dùng blurred home/end zone; exact home address out of scope mặc định.
- Tọa độ operational có retention ngắn; analytics aggregate/coarsen.
- Personalization opt-in granular; driver xem/sửa/xóa preference.
- Không dùng chat free text trực tiếp làm feature; extract typed constraint, confirm, discard/redact raw theo policy.
- Recommendation data không tự động trở thành performance/discipline score.
- Privacy impact assessment và legal review bắt buộc trước live; Luật Bảo vệ dữ liệu cá nhân hiện hành phải được mapping bởi counsel/owner, không hard-code diễn giải pháp lý trong model.

## 9. Ownership cần xác nhận

Data owner cho dispatch aggregates, earnings, bonus, telemetry, charger, driver profile, external traffic/weather, policy và analytics. Mỗi dataset có owner, steward, SLA, permitted purposes, retention, incident contact và schema change process.
