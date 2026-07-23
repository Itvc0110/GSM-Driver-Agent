# UPDATE-025 — Observability metric table per-layer (T-026 phase 1)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE C2 phase 1)
- **Loại:** docs / spec
- **TODO / User story liên quan:** T-026 (observability), tiền đề cho solver C2 + agent C6

## Tóm tắt

Thiết kế metric table per-layer (`specs/observability-metrics.md`) — 5 layer (router/solver/composer/verifier/adherence) + end-metric, mỗi metric có definition/source/unit/readiness/alert-intent. Đúng nguyên tắc "metric thiết kế TRƯỚC khi code" (spec core §6, yêu cầu T-026 không gắn observability sau). **Cycle docs-only** — chưa code instrumentation (Langfuse để C6). Tách khỏi solver S1 theo quyết định Cường (C2 = metric table riêng trước, S1 cycle sau).

## Chi tiết cập nhật

- Bảng đủ 5 layer + end, mỗi metric readiness `active_from` (solver=C2 đo được ngay; composer/verifier=C6 DESIGNED; adherence/end=M4 DESIGNED).
- **2 hard invariant duy nhất** (spec §5 — agent không tạo số): `solver.number_traceability=1.0`, `composer.faithfulness=1.0`. Còn lại observe-only, chưa đặt threshold số (chờ baseline data — tránh đoán bừa).
- Mọi metric map vào schema field đã có (SolverReport/ComposedAdvice/DecisionRecord/twin output) — self-review xác nhận 8/8 source field tồn tại trong schemas.
- Langfuse trace shape ghi sẵn cho C6 (1 span/layer); fallback parquet dual-channel khi headless.

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `specs/observability-metrics.md` | tạo |
| `tracking/TODO.md` | T-026 phase 1 DONE; C2 tách metric/solver |

## Docs đã cập nhật kèm theo

TODO. SCOPE/DEFERRED/spec core: không đổi.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| Mọi metric trace về schema field có thật | OBSERVED-CODE | self-review grep 8/8 advisor schema | Cao | metric không đo được |
| Chỉ 2 metric nên có ngưỡng cứng | ASSUMPTION | spec §5 (số không bịa) | Cao | đặt threshold sớm → đoán bừa |

## Kiểm chứng

Docs-only: không test/run. Self-review: 0 placeholder; 8/8 metric source field khớp `schemas/advisor/*`.

### Seeds và scenarios

| Run | Kết quả |
|---|---|
| grep placeholder + source cross-check | PASS (0 placeholder, 8/8 field khớp) |

## Visual verification

- **Status:** `NOT_APPLICABLE` — docs-only, không đổi sim/UI/output.

## Adversarial self-review / flaws found

1. **Đoán bừa threshold?** Đã tránh — chỉ 2 hard invariant (có cơ sở §5), phần còn lại observe-only + follow-up đặt threshold khi có data.
2. **Metric lơ lửng?** Không — cross-check 8/8 source field tồn tại trong schema.
3. **Readiness trung thực?** Composer/verifier/adherence đánh `DESIGNED` rõ ràng — không giả vờ đo được khi chưa code.
4. **Flaw còn mở:** threshold số + eval set (router/composer gold labels) → C6; Langfuse SDK → C6.

## Expansion checkpoint (T-039)

1. **Schema**: metric table không thêm entity; nhưng xác nhận SolverReport/ComposedAdvice đủ field cho mọi metric (đã đủ). Nếu C2 phát hiện thiếu → minor bump.
2. **Bài toán tối ưu**: không phát sinh (docs metric).
3. **Tính năng**: metric `end.fairness_gini` nhắc khả năng feature "cảnh báo advice thiên vị nhóm mạnh" — ghi nhận cho M4, chưa làm.

## Follow-up / defer phát sinh

- **C2 tiếp theo (solver S1 BonusFeasibility):** brainstorm + plan riêng; instrument `solver.*` metric bảng này.
- Threshold số + eval set + Langfuse SDK → C6.
