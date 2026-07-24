# P1 — Data catalog + phân tích sâu 13 bảng thật gsm-data-prod

Cập nhật: 2026-07-24 · Part 1/7 của real-data integration (index: `00-index.md`) · Trạng thái: DESIGN
Nguồn: metadata Cường gửi 2026-07-24 (ảnh + text). Catalog kiểm soát: [`docs/data-catalog/gsm-data-catalog.csv`](../../docs/data-catalog/gsm-data-catalog.csv) (+ `.xlsx`), sinh bởi `scripts/build_data_catalog.py` (13 bảng, canonical = Python list-of-dicts).

## 0. Tổng quan — 2 cụm dataset

| Cụm BigQuery | Bảng | Bản chất |
|---|---|---|
| `M_DRIVER_KPI_REWARD` | driver_statistic_daily, driver_online_hours_sap_id, driver_orders_rush_hours, driver_bike_stoppoints, kpi_driver_platform_calculator_gbq, driver_income_daily, driver_penalization_ATA | **KPI aggregate** daily/weekly (đã tổng hợp — KHÁC mock event-level của ta) |
| `GSM_ORDER_DISPATCH_SERVICE_APPEND` / `GSM_MISSION_SERVICE_APPEND` / `M_BROADCASTING_SERVICE_APPEND` | trips, public_driver_hex_tracking, public_mission, public_user_mission_progress, public_mission_earn_history, public_frauds | **event/append streams** (CDC qua Datastream — field `datastream_metadata`) |

**Insight chính:** phần lớn data thật là **pre-aggregated daily/weekly KPI**, không phải raw event. ⇒ re-ground schema (P2) + mock aggregate (P3) phải sinh đúng shape tổng hợp này. `_APPEND` = replicated CDC (append-only).

## 1. Glossary field kỹ thuật (giải nghĩa để gen/consume đúng)

- `datastream_metadata` — metadata CDC của Google Datastream (source_timestamp, change_type…). **Không phải business field**; mock để null/stub, không dùng cho logic.
- `sap_id` / `sap_profile_id` / `sap_contract_type` — khóa/loại hợp đồng từ hệ SAP (ERP nhân sự). PII/định danh → **drop/hash**. `sap_contract_type` gợi ý track (employee/platform/rto) — hữu ích map track nhưng phải anonymize.
- `week_key`, `week_start`, `week_end`, `kpi_month`, `kpi_year` — khóa chu kỳ **TUẦN/tháng** của KPI calculator → nền cho **khoán tuần** (weekly-khoan spec).
- `init_hex`/`current_hex`/`last_hex`/`target_hex`, `stay_duration_seconds`, `reached_target` — H3 cell + reposition mission. `target_hex` = GSM **chủ động** hướng tài xế tới ô → GSM đã có cơ chế reposition (liên quan mở lại D-004 có kiểm soát).
- `rewards`, `point_id`, `mission_claim`, `rule_code`, `qualify_execute_code`, `is_ddi_mission` — cơ chế mission/mini-task (điều kiện + phần thưởng). `is_ddi_mission` = mission dạng DDI (data-driven incentive?) — cần GSM xác nhận nghĩa.
- `revenue_not_relate_driver` — phần doanh thu **KHÔNG thuộc tài xế** (phần nền tảng/thu hộ) → khóa để **tách gross vs driver_payout** (§5 CLAUDE.md).
- `total_core_order` — đơn "core" (dịch vụ chính, phân biệt mini-task/khuyến mãi?) — cần GSM xác nhận định nghĩa.
- `count_cancel_not_relate_driver` — hủy KHÔNG do lỗi tài xế → không tính vào cancellation_rate phạt.
- `ATA` (driver_penalization_ATA) — nghĩa chưa rõ (Actual Time of Arrival? Acceptance/Time/…) → **HỎI GSM**.

## 2. Phân tích sâu từng bảng (contribute gì → feature/UC)

### Cụm KPI (aggregate — nguồn số chính)

**`driver_statistic_daily` (15 cột) — cột sống của KPI daily.**
- `completed/accepted/cancelled_count` + `total_request_calculate_*` → tử/mẫu của rate. `acceptance_rate = accepted/total_request_accept`, `fulfillment_rate = completed/accepted`, `cancellation_rate`. ⇒ **eligibility thưởng tuần (≥85%)** đọc trực tiếp, KHÔNG cần suy từ event.
- `total_rating`, `total_order_rating`, `count_rating_5_star` → **KPI chất lượng/sao** (biến MỚI ta chưa có). Nuôi F3 (điểm cải thiện chất lượng), penalty-explain.
- `count_cancel_not_relate_driver` → loại hủy-không-lỗi khỏi phân tích phạt (fairness).
- **Feeds:** S1 (eligibility), S3 (pattern), penalty-explain (UC6). UC1/UC4.

**`driver_online_hours_sap_id` (10)** — `online_time` = **quỹ giờ thật** (thay ước lượng từ event). `schedule_date` vs `local_date` → ca đăng ký vs thực. `driver_type`, `depot_id`/`hub_id` → phân nhóm. **Feeds:** S2 (quỹ giờ), S5 (giờ/tuần). PII: full_name/phone/sap → drop.

**`driver_orders_rush_hours` (14)** — tách **rush vs normal hour** cho `total_order/commission/total_fee/revenue_not_relate_driver`. ⇒ trả lời trực tiếp "khung giờ nào hiệu quả" (UC2) **mà không cần định nghĩa khung của ta** — dùng định nghĩa rush của GSM. `commission` = phần tài xế; `total_fee` = tổng cước; `revenue_not_relate_driver` = phần không thuộc tài xế. **Feeds:** S2, S3.

**`driver_bike_stoppoints` (4)** — `total_stoppoints` (+rush) = số điểm dừng → **proxy idle/thói quen dừng** (UC2/UC5). **Feeds:** S3, idle-reduction. (Cần GSM định nghĩa "stoppoint": dừng đón/trả hay dừng chờ?)

**`kpi_driver_platform_calculator_gbq` (21)** — bảng **tính KPI tuần + thưởng**: `week_key/start/end`, `kpi_month/year`, `type`, `status`, + hồ sơ xe/depot. ⇒ **NỀN weekly-khoan (S5)**. ⚠ số **target/threshold cụ thể** không thấy trong 21 cột đã biết → có thể ở bảng khác/meta → **HỎI GSM** (D-POL-05). PII nặng (name/sap/email/tel/vin/plate) → drop/hash. **Feeds:** S5.

**`driver_income_daily` (8)** — `commission`, `total_fee`, `revenue_not_relate_driver`, `avg_daily_revenue`, `total_order`, `total_core_order`. ⇒ **payout breakdown thật** (gross=total_fee, driver_payout=commission, phần nền=revenue_not_relate_driver). **Feeds:** S1, S5, F3 (US-F3-01 tách gross/payout).

**`driver_penalization_ATA` (THIẾU CỘT)** — sự kiện phạt/trừ tiền. Infer tối thiểu `{driver_id, date, penalty_type, amount_vnd, reason, week_ref}`. ⇒ nền **penalty-explain (UC6)** + F3 rủi ro. **HỎI GSM cột thật.**

### Cụm event/mission/append

**`trips` (THIẾU CỘT)** — trip-level dispatch. ~ `TripRecord` của ta (order_id, driver_id, service_type, timestamps, pickup/drop hex, gross). ⇒ **mật độ cuốc theo vùng** (UC5 demand density) + nền tính lại aggregate KPI. **HỎI GSM cột** (dùng shape trip_record ta làm giả định).

**`public_driver_hex_tracking` (19)** — chuyển động H3 + reposition: `init/current/last/target_hex`, `stay_duration_seconds`, `reached_target(_at)`, `hex_history`, `tracking_status`, `campaign_id`. ⇒ **idle-reduction (UC5)**: đo idle (stay_duration), đo reposition (target vs reached). `campaign_id` gắn mission reposition. **Feeds:** idle-reduction, S4.

**`public_mission` (28)** — **catalog mini-task**: `mission_type`, `rewards`, `point_id`, `start/end_time` (khung giờ), `rule_code`, `qualify_execute_code`, `audience`, `contract_type`, `is_ddi_mission`. ⇒ **NỀN S6 mission-knapsack (UC8)**: tập nhiệm vụ + phần thưởng + điều kiện + thời gian. **Feeds:** S6.

**`public_user_mission_progress` (THIẾU CỘT)** — tiến độ mission per driver. Infer `{id, driver_id, mission_id, progress, target, state, updated_at}`. ⇒ "còn thiếu gì để claim mission". **Feeds:** S6 (UC8). **HỎI GSM cột.**

**`public_mission_earn_history` (21)** — lịch sử nhận thưởng mission: `mission_id, order_id, driver_id, service_type, order/complete_time, count_order, count_stoppoint, earn, reward_level`. ⇒ thu nhập từ mission (tách khỏi cước) + hiệu quả mission lịch sử. **Feeds:** S6, income breakdown.

**`public_frauds` (THIẾU CỘT)** — cờ gian lận/bất thường. Infer `{driver_id, t, fraud_type, severity, evidence_ref, status}`. ⇒ **anomaly-alert (UC7)** — cảnh báo lệch route/bất thường, **nhãn INFERRED, KHÔNG kết tội**. **HỎI GSM cột.**

## 3. Bảng thiếu cột → cần XIN GSM (5 bảng)

`trips`, `driver_penalization_ATA`, `public_frauds`, `public_user_mission_progress` (+ ghi rõ trong catalog). Chiến lược: (a) tạm infer field tối thiểu (ghi ở P2, nhãn `TBC-với-GSM`); (b) **liệt kê thành câu hỏi cho GSM** trong P5/§data-ask; (c) mock theo field infer, đánh dấu để thay khi có cột thật.

## 4. Câu hỏi cần GSM xác nhận (semantics)

1. Định nghĩa `total_core_order`, `total_stoppoints`, `ATA`, `is_ddi_mission`, `type`/`status` (kpi_calculator), `reward_level`.
2. Số **target/threshold KPI tuần** nằm ở đâu (bảng/cột nào) — quan trọng cho S5.
3. Cột thật của 5 bảng thiếu.
4. `revenue_not_relate_driver` chính xác gồm gì (thu hộ? phí nền tảng?) — cho money-definition khoán (open decision d, weekly-khoan spec).

→ Các câu hỏi này gom vào P5 §"cần hỏi GSP/GSM" + DEFERRED D-POL-05.

## 5. Acceptance P1
- Catalog `.csv`+`.xlsx` sinh được, **đúng 13 hàng** (assert trong script), cột đủ 10 (5 gốc Cường + 5 thêm), PII đánh dấu mọi bảng.
- Mỗi bảng có: mapping layer, consumer (solver/feature), mockgen strategy, usecase.
- 5 bảng thiếu cột được đánh dấu + đưa vào danh sách hỏi GSM.
