# Schema changelog

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
