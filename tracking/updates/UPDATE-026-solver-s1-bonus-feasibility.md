# UPDATE-026 — Solver S1 BonusFeasibility + L3 derivation + PolicyBundle loader (C2b)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE C2b)
- **Loại:** feature / test
- **TODO / User story liên quan:** T-038 track CORE; US-F0-01, US-F1-03/04; pain #2/#3/#4

## Tóm tắt

Solver đầu tiên (thuần math, dễ verify nhất trong 4): cho `bonus_gap_input` (L3, derive từ mock data T-038) → tính trips/hours cần đạt mốc thưởng kế + **feasibility đa ràng buộc** (điểm ∧ acceptance ∧ completion) → trả `SolverReport` envelope. Mọi số có `source` (number_traceability=1.0 — metric solver §1.2). 3 unit tách bạch trong `gsm_core`, độc lập gsm_sim runtime. TDD failing-first, 12 test + integration mock data thật. LLM CHƯA vào (S1 chỉ trả SolverReport; Composer diễn giải ở C6).

## Chi tiết cập nhật

### `gsm_core/policy.py` — PolicyBundle từ L0 record
Đọc từ `policy_bundle` schema record (không phải sim config) → `trip_points`, `next_tier_gap`, `points_per_trip_estimate`, `bonus_at`, `is_peak`. Logic khớp `gsm_sim/policy.py` nhưng gsm_core không phụ thuộc simulator.

### `gsm_core/features/bonus_gap.py` — derive L3
- `points_now` = Σ `trip_points(hour)` các trip trong ngày (điểm không lưu ledger — suy từ trip observable + policy).
- `historical_points_per_hour` = median điểm/giờ-online theo khung {peak, offpeak} từ ngày lịch sử; **<3 ngày data → rỗng → solver fallback**.
- acceptance = accept/(accept+decline); completion = complete/accept (từ app_event).
- hours_budget = declared_window − đã online.

### `gsm_core/solvers/bonus_feasibility.py` — solver
- Đại số thuần deterministic (không scipy). gap_pts → rate (historical cá nhân `source: historical:self`, else `dp:policy_theoretical`) → hours/trips needed.
- **Feasibility đa ràng buộc**; `infeasible_reason` liệt kê ĐỦ ràng buộc thiếu (giờ + tỷ lệ nhận/hoàn thành). Ví dụ thật: "cần ~2.8 giờ nhưng quỹ chỉ còn 2.8 giờ".
- **3 sensitivity**: rate −20%/−40% (+`flips_feasible`), next_higher_tier (chi phí biên), acceptance_cliff (sát ngưỡng → cảnh báo mất toàn bộ thưởng).
- confidence 0.85 (historical) / 0.5 (fallback); caveats nêu bất định demand proxy.
- `problem_digest` tiếng Việt sinh deterministic.

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_core/policy.py` | tạo |
| `src/gsm_core/features/{__init__,bonus_gap}.py` | tạo |
| `src/gsm_core/solvers/{__init__,bonus_feasibility}.py` | tạo |
| `tests/test_bonus_feasibility.py` | tạo (12 test) |
| `tracking/TODO.md` | C2b DONE |

## Docs đã cập nhật kèm theo

TODO. SCOPE/DEFERRED/spec: không đổi (spec core §2 đã định nghĩa envelope).

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| Mọi số solver có source hợp lệ | OBSERVED-CODE | test_number_traceability | Cao | vi phạm §5 |
| points_now suy đúng từ trip+policy | OBSERVED-CODE | test_derive (=50 thủ công) | Cao | gap sai |
| Feasibility đa ràng buộc đúng | OBSERVED-CODE | test_infeasible_acceptance (đủ điểm/acc thấp→infeasible) | Cao | bỏ sót lý do mất thưởng |
| Feasibility rate hợp lý | OBSERVED-CODE | integration 7/12 feasible ngày giữa | Trung | — |

## Kiểm chứng

### Seeds và scenarios

| Run | Kết quả |
|---|---|
| `pytest tests/test_bonus_feasibility.py` | **12/12 pass** (failing-first: viết test trước) |
| Full suite | **88/88 pass** (76 + 12) |
| Integration `data/mock/v1` 12 driver | 7 feasible / 5 infeasible; digest + số + source đúng |
| Determinism | test_determinism (cùng input → cùng report) |

## Visual verification

- **Status:** `NOT_APPLICABLE` — solver layer, không UI/sim output. Report là JSON envelope, không visual.

## Adversarial self-review / flaws found

1. **Số bịa?** Không — test_number_traceability enforce mọi số có source; solver chỉ dùng policy record + input, không hằng số tài chính ẩn.
2. **Biên float:** `hours_needed ≤ budget` thêm tolerance 1e-6 (integration lộ case 2.8=2.8) — tránh flip ngẫu nhiên.
3. **Đa ràng buộc:** acceptance/completion vào feasibility (không chỉ điểm) — đúng thực tế pain #3.
4. **Fallback trung thực:** thiếu lịch sử → source `dp:policy_theoretical` + confidence 0.5 + caveat, không giả vờ chắc chắn.
5. **Chưa xét:** completion_rate mock luôn ~1.0 (sim ít cancel) → ràng buộc completion hiếm active; sẽ thực tế hơn khi có data GSM. `expected_trips_per_hour` fallback = 3.0 hằng số (nên đưa vào policy/config sau).
6. **Flaw còn mở → C3+:** DEFAULT_TRIPS_PER_HOUR nên config-driven; historical rate chưa xét demand forecast tương lai (chỉ lịch sử) — S2 ShiftDP sẽ dùng forecast.

## Expansion checkpoint (T-039)

1. **Schema**: `bonus_gap_input`/`solver_report` đủ field cho S1 — không cần thêm. Đề xuất minor: thêm `expected_trips_per_hour` optional vào bonus_gap_input để bỏ hằng số 3.0 (chờ duyệt).
2. **Bài toán tối ưu mới?** S1 lộ ra: "so sánh giá trị biên giữa các mốc thưởng" (sensitivity next_higher_tier) có thể thành mini-optimizer chọn mốc tối ưu theo chi phí giờ — hiện chỉ report, chưa optimize. Ghi cho C3+.
3. **Tính năng mới?** Từ S1: cảnh báo cliff acceptance (F3-02) khả thi ngay — đã có trong sensitivity, chờ Composer C6 render.

(Không tự triển khai — đề xuất để Cường duyệt.)

## Follow-up / defer phát sinh

- **C3 (tiếp theo):** S2 ShiftDP (dùng demand forecast, DP numpy) — brainstorm+plan riêng.
- DEFAULT_TRIPS_PER_HOUR → config; completion ràng buộc cần data thật để active.
