# UPDATE-029 — Solver S4 CapacityAlloc (chống herding) + allocation derivation (C5)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE C5)
- **Loại:** feature / test / data (dep)
- **TODO / User story liên quan:** Track CORE; US-F2-04; pain #1. **Hoàn tất 4/4 solver.**

## Tóm tắt

Solver cuối (4/4): platform-level gán advice nhiều driver (swap/standby) vào slot có capacity → **chống herding**. `scipy.optimize.linear_sum_assignment`. Brainstorm chốt: assignment/min-cost có capacity, cả swap_window + standby_zone, standby kèm **5 safety_flags F2-04**. 12 test + integration over-subscribe (0 vi phạm capacity); full suite 125 pass. **Track CORE solver layer hoàn tất — next C6 agent pipeline.**

## Chi tiết cập nhật

### `gsm_core/solvers/capacity_alloc.py`
- Tách 2 loại capacity: swap_window → (station, bucket) cap = throughput; standby_zone → (zone, bucket) cap = threshold.
- Assignment: expand slots theo capacity → `linear_sum_assignment` trên rectangular cost matrix (priority SOC thấp trước + target-match). Slot đầy → cost LARGE (loại). Dư candidate → `unassigned` (bỏ advice, chống dồn).
- **standby safety_flags** (5 điều kiện F2-04): capacity_aware, warn_acceptance, mock_label, no_income_promise, no_specific_order. swap_window KHÔNG có (timing thuần).
- Output: allocations[] + unassigned[] + `herding_avoided` (staggered + unassigned — giá trị chống herding đo được). numbers[] có source; sensitivity capacity−20%.

### `gsm_core/features/allocation.py`
derive `allocation_input`: candidates từ driver_reports; station_capacity = throughput × 30ph; zone_supply = threshold config.

### `pyproject.toml`
+scipy>=1.12 (chỉ S4 dùng — linear_sum_assignment).

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_core/solvers/capacity_alloc.py` | tạo |
| `src/gsm_core/features/allocation.py` | tạo |
| `tests/test_capacity_alloc.py` | tạo (12 test) |
| `pyproject.toml`, `uv.lock` | +scipy |
| `tracking/TODO.md` | C5 DONE (4/4 solver) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| Không vượt capacity | OBSERVED-CODE | test_alloc_respects_capacity + integration 0 vi phạm | Cao | herding không chống được |
| standby đủ 5 safety_flags | OBSERVED-CODE | test_standby_has_safety_flags + integration | Cao | vi phạm F2-04 |
| Không chỉ đơn cụ thể | OBSERVED-CODE | test_no_specific_order_advice | Cao | vi phạm §5/product boundary |
| SOC thấp swap trước | OBSERVED-CODE | test_low_soc_swap_priority | Cao | ưu tiên sai |

## Kiểm chứng

### Seeds và scenarios

| Run | Kết quả |
|---|---|
| `pytest tests/test_capacity_alloc.py` | **12/12 pass** (failing-first) |
| Full suite | **125/125 pass** |
| Integration over-subscribe (38 advice, 11 trạm + 1 zone) | gán 34, bỏ 4 (chống dồn), **0 vi phạm capacity**, standby 5 flags, sensitivity −20%→unassigned 4→13 |
| Determinism | test_determinism |

## Visual verification

- **Status:** `NOT_APPLICABLE` — solver layer, không UI. allocations visualize ở M3 (capacity heatmap).

## Adversarial self-review / flaws found

1. **Vượt capacity?** Không — slot expand theo capacity, integration 0 vi phạm. Chống herding đo được (herding_avoided).
2. **Product boundary:** standby_zone chỉ gợi ý vùng + 5 safety_flags; không chỉ đơn (test blob check order_id absent).
3. **Số bịa?** numbers[] chỉ capacity (station_registry/zone_supply source) + đếm — không số tài chính; scipy chỉ giải assignment.
4. **Simplification (ghi rõ):** bản đầu 1 bucket (t_now window 30ph), không multi-bucket lookahead → stagger chưa dùng bucket kế (candidate dư = unassigned thay vì dời giờ). zone_supply threshold mock (chưa demand thật). capacity danh định (chưa telemetry → caveat ESTIMATED).
5. **Flaw còn mở → C6/sau:** multi-bucket stagger (dời sang bucket kế thay vì bỏ); zone demand thật; capacity telemetry; candidates adapter S2/S3 → S4 tự động (hiện nhận driver_reports trực tiếp).

## Expansion checkpoint (T-039)

1. **Schema**: `allocation_input` đủ; `allocation` trong solution có `safety_flags`/`staggered` — không cần thêm entity. zone_supply/station_capacity items là object tự do → schema hóa chặt khi ổn.
2. **Bài toán tối ưu mới?** Multi-bucket capacity allocation (dời candidate sang bucket kế thay vì bỏ) = min-cost flow theo thời gian — nâng cấp S4. Ghi cho sau.
3. **Tính năng mới?** herding_avoided + allocations sẵn cho **capacity heatmap M3** và metric hệ thống (twin-world §3 tầng system) — nối M4 evaluator.

(Không tự triển khai — đề xuất để Cường duyệt.)

## Follow-up / defer phát sinh

- **C6 (tiếp theo):** agent pipeline — Router → Composer → Verifier + context pack + memory (LLM VÀO ĐÂY). 4 solver + SolverReport envelope sẵn sàng làm input Composer. Brainstorm+plan riêng.
- multi-bucket stagger; zone demand thật; candidates adapter tự động S2/S3→S4.
