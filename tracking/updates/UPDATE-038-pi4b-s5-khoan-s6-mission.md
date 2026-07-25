# UPDATE-038 — PI-4b: S5 WeeklyKhoanFeasibility + S6 MissionKnapsack

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường duyệt plan PI-4b)
- **Loại:** feature (2 solver mới)
- **TODO / User story liên quan:** Real-data PI-4b; UC3/UC4 (khoán tuần), UC8 (mini-task); T-039

## Tóm tắt

Thêm 2 solver **thuần math** dùng data thật chưa ai khai thác: **S5 WeeklyKhoanFeasibility** (`kpi_weekly_calculator` + `income_daily` → khoảng thiếu khoán tuần + rủi ro truy thu) và **S6 MissionKnapsack** (3 bảng mission → chọn mini-task tối đa thưởng trong quỹ giờ, **0/1 knapsack DP chứng minh tối ưu vs brute-force**). Suite **274 pass** (221 → +53).

## Chi tiết cập nhật

**Schema (additive, không phá contract cũ — CHANGELOG ghi):**
- `policy_bundle` + `weekly_quota` optional; `solver_report.solver` enum **+2** (enum ĐÓNG nên bắt buộc khai); 2 view mới `l3/weekly_khoan_input`, `l3/mission_select_input`; registry + `PolicyBundle.weekly_quota`/`has_weekly_quota()`.

**S5** (`solvers/weekly_khoan.py`): `gap = quota − revenue_tuần(GROSS)`; `clawback = gap × rate`; `hours_needed = gap / avg_revenue_per_hour`; feasible = đủ giờ ∧ đủ ngày hoạt động. `money_basis=gross` ghi vào `source` mỗi số. Sensitivity rate −20/−40% + ràng buộc ngày.

**S6** (`solvers/mission_knapsack.py`): DP 0/1 knapsack trên lưới 15 phút; cost = `remaining_count / trips_per_hour` (ASSUMPTION tuyến tính), value = `reward_vnd` **chỉ từ `mission_catalog`**; trả `chosen_missions`, `skipped` + lý do, sensitivity "+1h/+2h mở thêm gì".

**Derivation** (`features/from_l1r.py`): `derive_weekly_khoan_input_l1r` (tuần từ `kpi_weekly_calculator` đo được, fallback ISO week), `derive_mission_select_input_l1r` (join catalog × progress, lọc hết hạn/đã claim, `trips_per_hour` đo từ lịch sử).

**Mẫu output thật:**
- S5: *"tuần 2026-W27: doanh số 860,882đ/2,000,000đ khoán, thiếu 1,139,118đ (≈34.9 giờ); rủi ro truy thu 227,824đ; 5 ngày hoạt động, còn 4 ngày."*
- S6: *"chọn 1 nhiệm vụ — 2 chuyến khung vàng (còn 2 cuốc); tổng thưởng 30,000đ, ước 0.8/8.0 giờ."*

## ⚠ Đính chính khung "S5 đóng payout gap"

Kiểm tra lại: **không bảng thật nào có field thưởng tuần** (`driver_income_daily` chỉ commission/total_fee/revenue_not_relate_driver). ⇒ **KHÔNG bịa field bonus vào mock** (§5). S5 **tính** thưởng/khoán **từ policy** (số có source `policy_v:*`). Hệ quả: gap payout R2 (bike ~221k vs benchmark 380-480k) **một phần là khác ĐỊNH NGHĨA** — R2 đo *trip commission*, benchmark là *tổng thu nhập gồm thưởng tuần*. Ghi nhận, không "sửa" số cho đẹp.

## Adversarial self-review / flaws found

1. **FIXED trong cycle — S6 vô nghĩa dù test xanh**: `mission_catalog.rewards` thiếu `target_count` (rơi mất ở bản rewrite PI-2b) → `remaining=0` → S6 loại sạch mission ("đã đủ tiến độ"). Phát hiện khi **chạy thật** (không phải qua test). Fix + **regression test** `test_mock_missions_are_actionable`.
2. **§5 giữ chặt**: quota=None → S5 báo `quota_available=False`, **không đoán mốc**; test khẳng định không số nào mang nhãn `policy_v` trong nhánh đó.
3. **Tối ưu có chứng minh**: DP == brute-force trên 30 case seed (không tin "trông đúng").
4. **ASSUMPTION có nhãn**: effort tuyến tính (`remaining/trips_per_hour`); `money_basis=gross`; quỹ giờ tuần = `hours_per_day×ngày còn`.
5. **Chưa nối router C6** (S5/S6 chưa vào pipeline advisor) → thuộc PI-5; hiện chỉ solver-level.
6. Enum `solver_report.solver` đóng — bài học: thêm solver phải bump schema, đã ghi CHANGELOG.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `schemas/l0/policy_bundle.schema.json`, `schemas/advisor/solver_report.schema.json` | sửa (additive) |
| `schemas/l3/{weekly_khoan_input,mission_select_input}.schema.json` | tạo |
| `schemas/CHANGELOG.md`, `src/gsm_core/schema_registry.py` | sửa |
| `src/gsm_core/policy.py` | sửa (weekly_quota + has_weekly_quota) |
| `src/gsm_core/features/from_l1r.py` | sửa (+2 derivation) |
| `src/gsm_core/solvers/{weekly_khoan,mission_knapsack}.py` | tạo |
| `src/gsm_core/mockgen/realdata.py` | sửa (mission target_count) |
| `tests/{test_weekly_khoan,test_mission_knapsack,test_schemas}.py` | tạo/sửa |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| S6 DP tối ưu | `OBSERVED-CODE` | DP == brute-force 30 case | Cao | — |
| S5 số học gap/clawback | `OBSERVED-CODE` | test số học + determinism | Cao | — |
| khoán = GROSS | `ASSUMPTION` (Cường chốt) | "truy thu 20% phần doanh số" | TB | số lệch ~25% → có `money_basis` |
| quota 2tr/tuần trong test | `MOCK` | fixture, KHÔNG phải policy thật | — | chỉ test; runtime phải nạp số thật |
| effort = remaining/trips_per_hour | `ASSUMPTION` | tuyến tính hoá | TB | ước giờ lệch |

## Kiểm chứng

`test_weekly_khoan.py` **13 pass**, `test_mission_knapsack.py` **40 pass** (gồm 30 case DP-vs-brute-force), full suite **274 pass**. Chạy thật trên `generate_realdata` → 2 view hợp schema → 2 SolverReport hợp schema, traceability=1.0. **CHƯA kiểm chứng:** số khoán THẬT của GSM (test dùng MOCK 2tr); S5/S6 chưa nối router C6 (PI-5); chưa có eval so sánh chất lượng advice.

## Visual verification
- **Status:** `NOT_APPLICABLE` — solver layer. Digest text in ra cho Cường xem (mục "Mẫu output thật").

## Expansion checkpoint (T-039)
1. **Schema:** `weekly_quota` cần số thật (D-POL-05); có thể thêm `bonus_tiers_weekly` khi GSM xác nhận.
2. **Bài toán tối ưu:** S5/S6 xong → còn idle-reduction (UC5) là ứng viên optimization kế.
3. **Tính năng:** F1 "kế hoạch tuần đạt khoán", F2/F3 "mini-task nên làm" đã có solver hậu thuẫn — cần nối router (PI-5).

## Follow-up / defer phát sinh
- **PI-5**: nối S5/S6 vào router C6 + UC5 idle-reduction + UC6 penalty-explain + UC7 anomaly-alert.
- Số khoán tuần thật → D-POL-05 (hỏi GSM).
- `inferred_activities` (L2i) từ `hex_tracking` cho S3.
