# P3 — MOCK-gen grand plan (chi tiết cho GEN-AGENT + verify harness)

Cập nhật: 2026-07-24 · Part 3/7 · Trạng thái: DESIGN
Mục tiêu: gen mock ĐÚNG shape 13 bảng thật (P2), realistic, nhất quán chéo bảng, để pipeline chạy end-to-end như trên data thật. **Gen-agent đọc file này + `01`/`02` là đủ để gen.** Harness (agent kiểm) re-read TỪNG row/col/table.

## 0. Nguyên tắc gen (BẮT BUỘC)

1. **Sim → events → AGGREGATE**: tái dùng `mockgen/adapter_sim.generate_day` (đã có) sinh event nền (trips, GPS→hex, online, accept/complete/cancel), rồi **aggregate** ra các bảng KPI daily/weekly. ⇒ aggregate LUÔN nhất quán với event nền (không có bảng nào "bịa số" lệch bảng khác).
2. Bảng KHÔNG có event nền (mission catalog, penalization, fraud, user_mission_progress) → **rule-based generator** riêng, phân phối grounded research, seed-deterministic.
3. **Mọi record `source="MOCK"`**; số grounded `research/simulation/realism-benchmarks.md` + `research/community/pain-points.md` (dải thu nhập/giờ) + policy hiện hành.
4. **Deterministic**: seed = seed_base + day/week index; CRN. Regen được từ seed (parquet gitignored).
5. PII fields: gen giá trị **giả rõ ràng** (full_name="MOCK Driver 0007", phone="+8490MOCK…") — để test PII-drop tool P4, KHÔNG dùng số thật.

## 1. Thứ tự gen (dependency)

```
1. L0 config: policy_bundle (weekly-khoan), driver_profile (N driver, track, depot, vehicle), mission_catalog
2. Sim per day → events: trips, hex-track, online, accept/complete/cancel, swap
3. Aggregate daily: driver_statistic_daily, driver_orders_rush_hours, driver_bike_stoppoints,
   driver_income_daily, driver_online_hours
4. Aggregate weekly (mỗi 7 ngày): kpi_weekly_calculator
5. Rule-based: mission_earn_history (từ trips×mission), user_mission_progress, penalization (từ vi phạm), frauds (hiếm)
```

## 2. Field-by-field gen spec (mỗi bảng)

### driver_statistic_daily (per driver × day)
| field | gen rule | ràng buộc |
|---|---|---|
| local_date, driver_id | từ vòng lặp | FK driver_profile |
| accepted_count | = #accept event | ≤ total_request_accept |
| completed_count | = #complete | ≤ accepted_count |
| cancelled_count | = #cancel-by-driver | |
| count_cancel_not_relate_driver | = #cancel-not-driver | tách khỏi cancellation_rate |
| total_request_calculate_{accept,complete,cancel} | mẫu số KPI = #offer liên quan | |
| acceptance_rate | accepted/total_request_accept | **[0,1]**, khớp archetype (P1:0.82, P2:0.93…) |
| fulfillment_rate | completed/accepted | [0,1] |
| cancellation_rate | cancelled/(…) | [0,1]; rate = count/req EXACT |
| total_rating, total_order_rating, count_rating_5_star | rating ~ N(4.7,0.2) clip[1,5]; 5star≈70-85% | count_rating_5_star ≤ total_order_rating ≤ completed |

### driver_online_hours (per driver × day)
`online_time` (giờ) = tổng khoảng go_online→offline sim; grounded 3–4h(PT)…10–11h(top). `schedule_date`≈local_date. `driver_type/depot/hub` từ profile. PII (full_name/phone/sap) = giả nhãn.

### driver_orders_rush_hours (per driver × day)
Split trips theo khung **rush GSM** (6-8h,16-18h — hoặc theo policy_bundle). `total_fee`=Σgross; `commission`=Σ(gross×driver_share); `revenue_not_relate_driver`=total_fee−commission (proxy). **Ràng buộc: normal_hour + rush_hour = total** cho cả 4 metric (order/commission/fee/revenue).

### driver_bike_stoppoints (per driver × day)
`total_stoppoints` = #idle-segment (hex stay > ngưỡng) + #pickup/drop (định nghĩa TBC-GSM → mock cả 2 biến thể, nhãn). rush ⊆ total.

### kpi_weekly_calculator (per driver × week)
`week_key`=ISO week; `week_start/end`; `kpi_month/year`. Rollup 7 daily. `type/status` ∈ {active, at_risk, achieved} suy từ tiến độ vs target (target = policy_bundle weekly_quota — nếu chưa có số thật → MOCK nhãn). Vehicle/depot từ profile. PII drop-ready.

### driver_income_daily (per driver × day)
`total_fee`=Σgross; `commission`=Σpayout; `revenue_not_relate_driver`=fee−commission; `avg_daily_revenue`=total_fee/total_order; `total_order`; `total_core_order` ⊆ total_order (đơn core, ~85-95%). **Nhất quán với orders_rush_hours & statistic_daily cùng ngày.**

### trips (event, shape ~ trip_record; cột TBC)
Tái dùng trip_record: order_id, driver_id, service_type, t_request/assign/pickup/complete, pickup/drop lat-lon+H3, dist_km, gross_vnd. + customer_id (giả). Aggregate → demand density(hex,bucket).

### driver_hex_tracking (event)
Từ chuỗi GPS→H3 sim: init/current/last_hex, entered_current_hex_at, stay_duration_seconds (idle), hex_history (list). `target_hex`/`reached_target` chỉ set khi có reposition mission (campaign_id) — else null. tracking_status ∈ {moving, idle, offline}.

### mission_catalog (public_mission) — reference
Gen ~10-20 mission: mission_type ∈ {trip_count, revenue, rush_hour, reposition, rating}, rewards (VND/point), start/end_time (khung giờ), rule_code, audience (track/depot), is_ddi_mission. Grounded: mini-task thật (vd "250 chuyến/30 ngày=1tr", "2 chuyến khung vàng=30k").

### mission_earn_history (event)
Với mỗi trip thỏa điều kiện mission → earn record: mission_id, order_id, driver_id, service_type, order/complete_time, count_order, count_stoppoint, earn (từ mission.rewards), reward_level. **Σearn per driver-week nhất quán user_mission_progress.**

### user_mission_progress (INFER cột)
per driver × active mission: progress (đếm từ earn_history), target (mission), state ∈ {in_progress, completed, claimed}, updated_at. progress ≤ target.

### driver_penalization (INFER cột)
Hiếm (chỉ khi vi phạm): driver_id, date, penalty_type ∈ {clawback_khoan, conduct, late}, amount_vnd, reason, week_ref. Grounded clawback 20-40% shortfall (weekly-khoan). Nhãn — KHÔNG bịa dày.

### frauds (INFER cột)
Rất hiếm (~<1%): driver_id, t, fraud_type ∈ {route_deviation, gps_anomaly, off_app}, severity, evidence_ref, status. **Nhãn INFERRED, dùng để test anomaly-alert, KHÔNG kết tội.**

## 3. Verify harness (agent kiểm — RE-READ TỪNG row/col/table)

| Vòng | Kiểm | Ngưỡng/acceptance |
|---|---|---|
| **R1 schema+FK** | mọi record validate `l1r/*`; FK driver_id/mission_id/order_id/station_id không orphan; enum/range hợp lệ | 0 fail, 0 orphan |
| **R2 statistical (≥30 seeds)** | phân phối vs benchmark: online_time, trips/ngày (FT 15–30), acceptance per archetype, income dải, rush share, rating | trong tolerance/CI ghi report; gap có nhãn (T-021 style) |
| **R3 cross-table consistency** | **aggregate ↔ event nền**: Σtrips.gross per driver-day = income_daily.total_fee; statistic_daily counts = #events; rush+normal=total; weekly rollup=Σdaily; earn_history Σ=progress; ledger tái tính | 0 lệch (deterministic) |
| **R4 adversarial** | rate ∉[0,1]? completed>accepted? progress>target? penalty khi rate>ngưỡng? mission ngoài khung giờ? time nghịch? | 0 vi phạm |

Report → `research/experiments/mockgen-realdata/ROUND-{1..4}-*.md` (commit). Gen-agent PHẢI đạt cả 4 trước khi coi mock hợp lệ.

## 4. Output & CLI (cycle impl)
`uv run python -m gsm_core.mockgen.generate_realdata --days 30 --drivers 50 --seed-base 100 --out data/mock/realdata-v1` → 13 parquet + manifest(label=MOCK) + 4 report. Reuse pattern `mockgen/generate.py`.

## 5. Acceptance P3
Field-by-field spec đủ 13 bảng; ràng buộc chéo bảng rõ; 4 vòng verify có ngưỡng; deterministic; PII giả có nhãn. Gen-agent đọc là gen được không cần hỏi thêm (trừ 4 câu semantics GSM ở P1§4 → dùng giả định có nhãn tới khi GSM trả lời).
