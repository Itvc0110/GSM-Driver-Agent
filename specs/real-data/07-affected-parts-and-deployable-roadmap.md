# P7 — Affected-parts audit + roadmap deployable (kiểm thử/giả lập)

Cập nhật: 2026-07-24 · Part 7/7 · Trạng thái: DESIGN
Trả lời Cường #5: phần nào bị ảnh hưởng, todo đi sau, plan deployable + kiểm thử/giả lập — **TRỪ hiệu năng AI-Advisor (observation/CI-CD/optimize)**.

## 1. Affected-parts audit (phần → thay đổi → severity)

| Phần | Thay đổi do re-ground/UC5-8 | Severity |
|---|---|---|
| `schemas/` | +13 `l1r/*`; deprecate `gps_ping`; re-ground `driver_day_state`; mở rộng `policy_bundle` (weekly-khoan) | **Cao** |
| `schema_registry.py` | +layer `l1r`; LAYER_OF | TB |
| `mockgen/` | viết lại → gen 13 bảng (sim→aggregate) + rule-based mission/penalty/fraud; 4 vòng verify mới | **Cao** |
| Solver S1–S4 | remap L3 input sang field thật (rate đọc thẳng statistic_daily; rush từ orders_rush_hours) | Cao |
| Solver mới | S5 weekly-khoan, S6 mission-knapsack, idle-reduction | **Cao** (mới) |
| Feature mới | penalty-explain (UC6), anomaly-alert (UC7) — reasoning | TB |
| Advisor C6 | router FEATURE_SOLVERS + intent keywords cho UC5-8; composer feature instruction; **envelope KHÔNG đổi** | TB |
| `datasource/` (mới) | DataSource + MockSource + BigQuerySource skeleton + PII | Cao |
| `ExternalContext` (mới, treo) | chỗ cắm external API (P5) — chưa code tới khi Cường chốt key | Thấp |
| Tests | regen theo schema mới; failing-first mỗi solver mới; PII/datasource test | Cao |
| `configs/` | pilot config + policy config (weekly-khoan) | TB |
| Specs | `policy-weekly-khoan-model` nối S5; `core-data-schema` §1 cập nhật mapping real | TB |
| F0 corpus (Khánh) | D-POL-04 (vẫn treo owner) | — |
| **AI-Advisor perf/observability/CI-CD/optimize** | **LOẠI TRỪ khỏi roadmap này** (Cường) | — |

## 2. Roadmap deployable (mỗi phase = 1 cycle plan riêng + test/sim)

Thứ tự theo phụ thuộc. Mỗi phase: brainstorm→plan→implement→verify→(visual nếu có UI). "Số thật" (khoán/target/5 bảng thiếu cột) chờ **D-POL-05** + GSM trả lời P1§4 → phase dùng MOCK nhãn tới khi có.

| Phase | Nội dung | Phụ thuộc | Kiểm thử / giả lập (deployable) |
|---|---|---|---|
| **PI-1 Schema** | viết 13 `l1r/*` + registry + CHANGELOG (P2) | catalog | validate example/bảng; 162 test cũ giữ nguyên; PII/availability annotation test |
| **PI-2 Mock regen** | `generate_realdata` sim→aggregate + rule-based; 4 vòng verify (P3) | PI-1 | R1 schema+FK; R2 stats ≥30 seeds vs benchmark; R3 cross-table (aggregate↔event); R4 adversarial — **harness re-read từng row/col/table** |
| **PI-3 DataSource tool** | DataSource+MockSource+BQ skeleton+PII (P4) | PI-1 | contract test MockSource; client-mock BQ guard/PII/provenance; **live treo chờ credentials** |
| **PI-4 Solver remap + S5/S6** | S1-S4 → field thật; S5 khoan; S6 mission-knapsack | PI-2 | failing-first per solver; SolverReport schema; determinism; number_traceability=1.0; S6 knapsack đúng tối ưu (test nhỏ brute-force đối chiếu) |
| **PI-5 UC5-8 features** | idle-reduction, penalty-explain, anomaly-alert + router mở rộng | PI-4, C6 | per-feature test; guardrail (không kết tội/không khuyên đơn); reasoning fallback; integration 3 driver × feature mới |
| **PI-6 External (treo)** | ExternalContext + provider (P5) | Cường chốt key/techstack | mock provider deterministic test; PROXY nhãn; cache/fallback |

**Giả lập (simulation) xuyên suốt**: sim twin-world (gsm_sim) tiếp tục là nguồn event nền cho mock (PI-2) + môi trường test adherence sau (M4). Twin A/B/C eval = sau, không trong 6 phase này.

## 3. TODO/DEFERRED update (governance)
- TODO: thêm block "Real-data integration PI-1..PI-6" (mỗi phase READY/ BLOCKED theo phụ thuộc); D-POL-05 nối "GSM trả 5 bảng thiếu cột + target KPI + semantics (P1§4)".
- DEFERRED: D-POL-01/02/03 (weekly-khoan) **hợp nhất** vào PI-1/PI-2/PI-4 (có data thật path). D-004 reposition → mở lại CÓ ĐIỀU KIỆN (UC5, P6). External API → DEFERRED chờ Cường chốt key.
- Câu hỏi GSM (P1§4) + techstack/env (P4§6, P5§4) → 1 mục "cần Cường/GSM chốt".

## 4. Điều kiện "bài toán hoàn thành toàn vẹn" (Cường #5)
Sau **PI-2** (mock chuẩn theo schema mới) → pipeline end-to-end chạy realistic; sau **PI-4/PI-5** → đủ solver/feature phủ UC1-UC8. "Toàn vẹn" = 13 bảng mock verify 4 vòng + solver/feature UC1-8 xanh + advisor tổng hợp được. **Loại trừ**: tinh chỉnh hiệu năng LLM, observability tuning, CI/CD, optimize — theo Cường.

## 5. Acceptance P7
Audit đủ phần ảnh hưởng + severity; roadmap 6 phase có phụ thuộc + kiểm thử/giả lập cụ thể mỗi phase; loại trừ AI-Advisor perf ghi rõ; TODO/DEFERRED cập nhật; điều kiện "toàn vẹn" định nghĩa. Mỗi phase = cycle riêng có plan (không làm gộp).
