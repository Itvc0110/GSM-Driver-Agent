# P6 — Feature & optimization mới từ data thật (UC5–UC8) + map UC↔F

Cập nhật: 2026-07-24 · Part 6/7 · Trạng thái: DESIGN
Quyết định Cường: **mở rộng UC5-UC8**. Trả lời #6 (UC6/7/8 giống output feature ta). Mỗi mục: nguồn data, bài toán (optimization vs reasoning), I/O contract sketch, guardrail §5.

## 1. Map UC (bảng thật) ↔ Feature ta ↔ Solver

| UC (real) | Bảng nguồn | Feature ta | Loại | Solver/Module |
|---|---|---|---|---|
| UC1 phân tích hiệu suất | statistic_daily, online_hours | F3 (sau ca) + F1 | reasoning+rule | S1/S3 |
| UC2 điểm cần cải thiện | orders_rush_hours, stoppoints | F3 | rule+stat | S3 |
| UC3 tiến độ KPI/thưởng | kpi_weekly_calculator, income_daily, mission_earn | F1/F3 | **optimization** | **S5** weekly-khoan |
| UC4 khả năng đạt KPI | statistic_daily, kpi_calculator | F1 | optimization | S1+S5 |
| UC5 reduce idle / reposition | hex_tracking, trips, stoppoints | F2 (trong ca) | optimization+rule | **Idle-Reduction** (+S4) |
| UC6 giải thích hiệu suất/rủi ro phạt | penalization, statistic_daily | F3 + R3 | **reasoning** (agent) | **Penalty-Explain** |
| UC7 cảnh báo lệch route/bất thường | frauds, hex_tracking, trips | alert MỚI | rule+reasoning | **Anomaly-Alert** |
| UC8 mini task tăng thu nhập | public_mission, progress, earn_history | F2/F3 | **optimization** | **S6** mission-knapsack |

## 2. Solver/feature MỚI — I/O contract sketch

### S5 — WeeklyKhoanFeasibility (UC3/UC4) — optimization, thuần math
Đã có spec `policy-weekly-khoan-model.md`. Nguồn thật: `kpi_weekly_calculator` (week target/status) + `income_daily`/`statistic_daily` (tiến độ). **L3 `weekly_khoan_input`** → SolverReport {gap_revenue, clawback_risk, hours_needed, feasible}. Treo chờ target thật (D-POL-05).

### S6 — MissionKnapsack (UC8) — optimization (knapsack/assignment, scipy)
- **Bài toán**: chọn tập mission (từ `public_mission` còn hiệu lực, đúng audience/khung giờ) để **tối đa Σreward** trong **quỹ giờ/effort còn lại**, xét tiến độ (`user_mission_progress`) + khả thi (rule_code, qualify). Ràng buộc: thời gian, chồng lấn khung giờ, effort (count_order/stoppoint cần).
- **Thuật toán**: 0/1 knapsack (DP) nếu ràng buộc đơn (thời gian); hoặc LP/assignment nếu nhiều ràng buộc → scipy. Thuần math, số từ mission.rewards (có source).
- **I/O**: `mission_select_input` {missions[], progress[], hours_remaining, driver_track} → SolverReport {chosen_missions[], expected_reward_vnd, feasibility, "còn thiếu X để claim mission Y"}.
- Guardrail: reward từ catalog (không bịa); không hứa chắc; advice_spec = mini-task gợi ý, tài xế tự quyết.

### Idle-Reduction (UC5) — optimization+rule
- **Nguồn**: `hex_tracking` (stay_duration, idle streaks, target_hex/reached), `trips`-agg (mật độ cuốc theo hex×giờ), `stoppoints`.
- **Bài toán**: phát hiện **idle bất thường** (stay_duration cao ở hex demand thấp) → gợi ý **thời điểm/di chuyển** theo cơ chế reposition CỦA GSM (target_hex missions). ⚠ **Mở lại D-004 CÓ KIỂM SOÁT**: vì GSM tự có reposition mission → tư vấn theo mission GSM (không tự bịa heatmap), capacity-aware chống dồn cung, cảnh báo "từ chối ảnh hưởng tỷ lệ".
- **I/O**: `idle_input` {hex_seq, stay_durations, demand_density, active_missions} → report {idle_flag, suggested_reposition (theo mission GSM/ demand proxy), expected_gain estimate}.
- Guardrail: KHÔNG khuyên đơn cụ thể; demand = PROXY có nhãn; ưu tiên mission chính thức GSM.

### Penalty-Explain (UC6) — reasoning (agent, có fallback)
- **Nguồn**: `driver_penalization` (đã/ sắp bị trừ) + `statistic_daily` rates + weekly-khoan tiến độ.
- **Bài toán**: **giải thích** vì sao hiệu suất thấp / rủi ro bị trừ (clawback khoán, conduct) + cách tránh — R3-style reasoning, **log + confidence + fallback template**. Số (mức trừ) từ data/policy, agent chỉ diễn giải.
- **I/O**: `penalty_explain_input` {penalties[], rates, khoan_progress} → advice {message giải thích + citations policy + caveats}. Guardrail: không dạy lách; nêu bất định; số có source.

### Anomaly-Alert (UC7) — rule+reasoning
- **Nguồn**: `public_frauds` (cờ nền tảng) + lệch route (hex_history vs Google route P5) + bất thường (GPS jump, off-app pattern).
- **Bài toán**: **cảnh báo** rủi ro/bất thường — **KHÔNG kết tội**, nhãn INFERRED + confidence, khuyến nghị kiểm tra. Chủ yếu reasoning + rule threshold.
- **I/O**: `anomaly_input` {fraud_flags, route_deviation, patterns} → alert {type, severity, explanation, "kiểm tra lại", non-accusatory}. Guardrail: privacy, không kết luận gian lận (chỉ platform mới phán).

## 3. Feature từ field MỚI chưa dùng
- **Rating/quality KPI** (`total_rating`, `count_rating_5_star`) → F3 "điểm chất lượng" + eligibility (nếu policy có ngưỡng sao) + Premium bonus (research). Solver: rule/stat trong S3.
- **`revenue_not_relate_driver`** → tách gross/payout chuẩn hơn (F3 US-F3-01).
- **`travel_mode`, `service_type`** (mission_earn) → phân tích đa dịch vụ (Bike/Food/Express) — nối D-009.

## 4. Router/advisor mở rộng (C6 pipeline)
- FEATURE_SOLVERS thêm: UC5→[idle_reduction, capacity_alloc], UC6→[penalty_explain]+KB, UC7→[anomaly_alert], UC8→[mission_knapsack]. Intent keywords tiếng Việt mới (mission/nhiệm vụ, idle/đứng chờ, phạt/trừ tiền, bất thường).
- Composer/Verifier KHÔNG đổi bản chất (placeholder-first, veto) — chỉ thêm feature instruction. Số vẫn từ solver.
- **#6 xác nhận**: UC6/UC7/UC8 = output kiểu F3/alert của ta → tái dùng envelope SolverReport + ComposedAdvice, KHÔNG cần pipeline mới.

## 5. Optimization vs reasoning (ranh giới §1 CLAUDE.md)
- **Optimization (solver, số kiểm chứng)**: S5 khoán, S6 mission-knapsack, idle-reduction (phần demand/capacity), S1-S4.
- **Reasoning (agent, log+confidence+fallback)**: penalty-explain (UC6), anomaly-alert (UC7 phần diễn giải), F0 policy Q&A. → đúng chủ trương "agent đảm nhiệm reasoning khi chưa modelling được", tắt về template.

## 6. Acceptance P6
Mỗi UC5-8 có: nguồn data, loại (opt/reasoning), I/O sketch, guardrail. S5/S6 = optimization thuần math; UC6/7 = reasoning có fallback. Map UC↔F↔solver đủ. D-004 reposition mở lại có điều kiện ghi rõ. Không code — blueprint cho P7 roadmap.
