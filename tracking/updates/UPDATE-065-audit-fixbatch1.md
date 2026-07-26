# UPDATE-065 — AUDIT fix batch 1: 7 fix hẹp CONFIRMED, mỗi cái regression-test-trước

Ngày: 2026-07-27 · Track: **AUDIT** · Sau UPDATE-064 (`c23aa77`). Chính sách Cường đã chốt:
fix ngay BUG hẹp; MODEL GAP lớn chỉ đề án.

## 1. Fix đã vào (finding id theo `research/audit/2026-07-26-full-audit/a1_math_findings.json`)

| ID | Fix | Files |
|---|---|---|
| **S1-1** | `already_maxed` kiểm ràng buộc acceptance/completion — dưới ngưỡng → `feasible=False` + lý do + caveat (hết "báo có thưởng khi chính sách trả 0") | `src/gsm_core/solvers/bonus_feasibility.py` |
| **S1-2/3/5** | VIẾT LẠI lõi S1: `_walk` đi TỪNG GIỜ còn lại tới nửa đêm — peak/offpeak trộn theo giờ thật, giờ ngoài khung điểm = 0đ/h (22h30 → infeasible "ngoài khung"), trips đếm theo ppt từng giờ; sensitivity/next-tier rewalk; `hours_needed=None` khi không đạt được trong ngày (schema không nhận Infinity) | như trên + `ui/backend/app/adapters/advisor.py` (guard None) |
| **S1-4** | Fallback 3.0 cuốc/giờ (không nguồn) → **1.5** (khớp số ĐO `advice.trips_per_hour_est` nhãn ĐO trong config sim; vẫn confidence 0.5 + caveat) | như trên |
| **BEHAV-2 (mở rộng)** | TOÀN BỘ 9 slider dashboard đọc default TỪ CONFIG qua `dashboard_defaults.py` mới (range chứa giá trị hiệu chỉnh, config vượt range thì NỔ thay vì âm thầm kẹp); slider detour đổi nhãn "FALLBACK (đường thật đã dùng OSRM)" | `src/gsm_sim/dashboard_defaults.py` (TẠO) · `dashboard.py` |
| **S5-1** | View khoán tuần cắt tại `min(today, week_end)` — hết rò doanh thu/giờ-online TƯƠNG LAI vào revenue_so_far/days_active/avg_rate | `src/gsm_core/features/from_l1r.py` |
| **S8S9-1** | S8 đăng ký `penalty_count` (unit count) + threshold nhánh 'near' vào numbers[]; template `_penalty_sentence` neo mọi số qua `_vn()` (bài học BUG-PI5d-01) — verifier V1 hết veto advice F3 có khoản trừ | `src/gsm_core/solvers/penalty_explain.py` · `src/gsm_core/advisor/templates.py` |
| **DEMAND-1** | Gỡ cờ CHẾT `demand.hour_interp` cả 2 phía (code + config comment nói dối); nội suy thật → **D-SIM-19** (cần regate 30 seed) | `src/gsm_sim/demand.py` · `configs/pilot_dongda.yaml` · DEFERRED |
| **STATS-2** | Guardrail `/ab` per-cell THẬT: dropoff events → pickup_cell, `worst_cell_delta_served` = min delta thật, `flagged_cells` nhất quán, có cờ thì KHÔNG được nói "ổn"; ngưỡng −3 đơn/cell ghi rõ là ngưỡng thô demo 1-seed | `ui/backend/app/routers/sim.py` |

## 2. Regression tests (đỏ-trước-xanh-sau)

- `tests/test_bonus_feasibility.py` +4 (already-maxed-below-threshold · after-window · blended-rate
  15h→peak · fallback-1.5) — chạy đỏ trước fix (4 failed), xanh sau.
- `tests/test_dashboard_defaults.py` (TẠO, 3 test — default==config · 21200 trong range · vượt
  range phải raise).
- `tests/test_features_from_l1r.py` +1 (đứng đầu tuần revenue < cuối tuần — đọc-tương-lai thì đỏ);
  `tests/test_weekly_khoan.py::test_view_gross_matches_income_sum` SỬA KỲ VỌNG — bản cũ của test
  này chính là hiện thân bug S5-1 (cộng cả tuần), nó đỏ sau fix là bằng chứng lật đúng chiều.
- `tests/test_penalty_anomaly.py` +1 (câu penalty qua thẳng `check_bare_numbers` — đỏ trước fix).
- `tests/test_policy_demand.py` +1 (vệ sinh config: mọi key `demand.*` phải được code đọc).
- `ui/backend/tests/test_contracts.py` +1 (guardrail per-cell nhất quán).

## 3. Kiểm chứng (số đọc từ output thật)

- **Full suite: 504 passed, 4 skipped** (11m18s) — trước batch 493+5 (net +11 test, 1 skip cũ
  thành test chạy). **UI backend: 21 passed.** Advisor suites chạy riêng lúc fix: 113 passed.
- Visual status: **NOT_APPLICABLE** cho solver/view; riêng dashboard slider là behavior change có
  chủ ý (default = config đã hiệu chỉnh) — nhập vào kịch bản **V-09/V-10** sẵn có, không cần gate mới.

## 4. Adversarial self-review / flaws found

- S1 `_walk` giả định pattern giờ CHỈ trong ngày hiện tại (không vắt sang mai) — đúng ngữ nghĩa
  thưởng NGÀY; ghi chú trong docstring.
- `hours_needed=None` là thay đổi CONTRACT nhỏ của SolverReport (trước luôn số) — schema vốn cho
  phép (validate pass), consumer UI đã guard; bridge sim không đọc trường này (kiểm bằng grep).
- Confidence S1 khi trộn nguồn (hist + fallback) lấy 0.5 bảo thủ — ghi trong code; semantics
  confidence vẫn là mã-hoá-nguồn (S1-7 THẤP còn mở, thuộc đề án estimator).
- STATS-2 ngưỡng −3 vẫn là ngưỡng thô TÔI chọn (Poisson noise 1 ngày) — đã ghi thẳng trong code
  + UI có warning 1-seed; kết luận hệ thống thật ở sweep 30-seed.
- Fix CHƯA làm (còn trong hàng): S2-1 (DP flooring — cần thiết kế expectation-rounding),
  11 finding chưa-verify (quota), cụm MODEL GAP (EST-1/8, S6-1, S2-4...) → đề án ở A4.

## 5. Follow-up

Sau quota reset (2:20am): verify 11 finding treo → A3 agent-system workflow → A4 report tổng +
đề án MODEL GAP. S2-1 fix xen được trước đó.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · V-09 (dashboard SIM-XANH — slider nay bám config)
· **V-10 (Track UI)** · Q-03 (corpus Khánh).
