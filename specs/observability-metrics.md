# SPEC — Observability metrics per-layer (T-026 phase 1)

Cập nhật: 2026-07-23 · Trạng thái: **DESIGN — thiết kế TRƯỚC khi code (spec core §6)**
Nguồn: `core-data-schema-and-advisor-architecture.md` §3/§6; `advisor-optimization-layer-a.md`; `research/simulation/llm-advisor-architecture.md` (Langfuse/Phoenix).
Phase 1 = thiết kế bảng metric đo được. Phase 2 (C6) = instrument Langfuse. **Cycle này KHÔNG code instrumentation.**

## 0. Nguyên tắc

1. **Metric thiết kế trước code** — mỗi layer biết đo gì trước khi build (không gắn observability sau; yêu cầu T-026).
2. **Mọi metric đọc từ SCHEMA đã có** — SolverReport / ComposedAdvice / DecisionRecord / sim twin output. Không metric "lơ lửng".
3. **Chỉ 2 hard invariant** (spec §5 — agent không tạo số): `solver.number_traceability = 1.0` và `composer.faithfulness = 1.0`. Còn lại **observe-only** — chưa đặt ngưỡng số vì chưa có baseline data (đặt threshold = follow-up khi có dữ liệu, tránh đoán bừa).
4. **Readiness cột `active_from`**: layer đã/đang code = instrument ngay; layer chưa code = `DESIGNED` (thiết kế sẵn, bật khi tới C#).
5. **Langfuse mapping**: mỗi layer = 1 span trong trace của 1 AdviceRequest; mỗi metric = span attribute/score. Ghi sẵn cho C6.

## 1. Bảng metric

Cột: `metric · definition · source (schema field) · unit · active_from · alert_intent (định tính — khi nào bất thường)`.

### 1.1 Router (deterministic, không LLM) — `active_from: C6`

| metric | definition | source | unit | active | alert_intent |
|---|---|---|---|---|---|
| `router.intent_accuracy` | % request phân đúng feature F0–F3 (so nhãn eval set) | AdviceRequest.feature vs gold | ratio | C6 DESIGNED | tụt so eval baseline |
| `router.out_of_taxonomy_rate` | % request rơi vào "ngoài phạm vi" (R5) | routing decision log | ratio | C6 DESIGNED | tăng đột biến = gap taxonomy |
| `router.stage1_fanout` | số solver kích hoạt song song/request | orchestration log | count | C6 DESIGNED | =0 khi lẽ ra có solver |

### 1.2 Solver (thuần math) — `active_from: C2` ✅ đo được ngay

| metric | definition | source | unit | active | alert_intent |
|---|---|---|---|---|---|
| `solver.number_traceability` | **% số trong SolverReport.numbers có `source` hợp lệ (policy_v/ledger/dp)** | SolverReport.numbers[].source | ratio | **C2 — HARD =1.0** | bất kỳ số nào không trace = BLOCK |
| `solver.feasibility_rate` | % bài trả feasible (infeasible_reason=null) | SolverReport.infeasible_reason | ratio | **C2** | quá thấp = input/model sai |
| `solver.solve_latency_ms` | thời gian giải | wall-clock | ms | **C2** | p95 phình = model nặng |
| `solver.input_freshness_sec` | tuổi L3 view lúc giải | SolverReport.inputs_used[].freshness | sec | **C2** | quá cũ = pipeline trễ |
| `solver.confidence` | confidence solver tự báo | SolverReport.confidence | 0–1 | **C2** | phân phối lệch thấp = cần review |

### 1.3 Composer (LLM #1) — `active_from: C6`

| metric | definition | source | unit | active | alert_intent |
|---|---|---|---|---|---|
| `composer.faithfulness` | **% số trong ComposedAdvice.numbers khớp SolverReport (không bịa)** | ComposedAdvice.numbers vs SolverReport | ratio | C6 DESIGNED — **HARD =1.0** | <1.0 = hallucination = veto |
| `composer.citation_coverage` | % claim policy có citation | ComposedAdvice.citations | ratio | C6 DESIGNED | thiếu citation cho claim policy |
| `composer.persona_fit` | phù hợp persona (eval/human sample) | eval | score | C6 DESIGNED | — |
| `composer.token_cost` | token in/out | LLM usage | count | C6 DESIGNED | phình bất thường |
| `composer.fallback_rate` | % dùng template fallback (LLM-off/veto) | ComposedAdvice.fallback_used | ratio | C6 DESIGNED | cao = LLM/verifier hỏng |

### 1.4 Verifier (LLM #2 hoặc rule) — `active_from: C6`

| metric | definition | source | unit | active | alert_intent |
|---|---|---|---|---|---|
| `verifier.veto_rate` | % advice bị veto → template | verifier decision | ratio | C6 DESIGNED | cao = composer kém |
| `verifier.repair_rate` | % advice qua 1 vòng repair | verifier decision | ratio | C6 DESIGNED | cao = prompt cần chỉnh |
| `verifier.guardrail_violations` | đếm vi phạm §5 (số bịa, hứa thu nhập, khuyên đơn cụ thể) | guardrail checklist | count | C6 DESIGNED | >0 = phải điều tra |
| `verifier.false_number_caught` | số sai composer mà verifier bắt được | diff | count | C6 DESIGNED | — (tín hiệu verifier hoạt động) |

### 1.5 Adherence — `active_from: M4`

| metric | definition | source | unit | active | alert_intent |
|---|---|---|---|---|---|
| `adherence.seen_rate` | % advice actor "thấy" (không UNSEEN) | DecisionRecord + sim | ratio | M4 DESIGNED | — |
| `adherence.acted_rate` | % advice actor làm theo (EXPLICIT_FOLLOW) | advice_spec vs behavior | ratio | M4 DESIGNED | — |
| `adherence.coincident_rate` | % làm theo nhưng twin B cũng làm (không tính công advisor) | twin-diff | ratio | M4 DESIGNED | cao = advice trùng bản năng |
| `adherence.divergence_index` | |cell_A−cell_B| + |ΔSOC|/10 + 1{state khác} | DecisionRecord | index | M4 DESIGNED | — |

### 1.6 End-metric (evaluator T-020) — `active_from: M4`

| metric | definition | source | unit | active |
|---|---|---|---|---|
| `end.delta_payout` | Δ(A−B), Δ(C−B), **Δ(A−C)** paired seed | twin evaluator | vnd + CI | M4 DESIGNED |
| `end.delta_utilization` | Δ util FT | twin evaluator | ratio | M4 DESIGNED |
| `end.fairness_gini` | Gini payout; decile thấp nhất | twin evaluator | index | M4 DESIGNED |
| `end.system_guardrail` | queue trạm/unserved không xấu đi do advice | twin evaluator | ratio | M4 DESIGNED |

## 2. Langfuse trace shape (cho C6 — không code bây giờ)

```text
trace: advice_request(request_id, driver_id, feature)
  span: router            → router.* attributes
  span: solver:S1..S4     → solver.* (mỗi solver 1 span; number_traceability score)
  span: composer          → composer.* (faithfulness score)
  span: verifier          → verifier.* (veto/repair)
  → ComposedAdvice (fallback_used, residual_path)
[async, sim] adherence.* + end.* gắn qua DecisionRecord.request_id
```

Fallback observability khi Langfuse tắt/headless (cron): ghi parquet dual-channel (như sim event log) — không chặn deterministic core.

## 3. Follow-up (đặt threshold khi có data)

- Ngưỡng số cho observe-only metrics (latency p95, feasibility_rate floor, veto_rate ceiling...) — chốt sau khi C2+ có baseline; ghi vào doc này (minor update).
- 2 hard invariant (`number_traceability`, `faithfulness` = 1.0) áp dụng NGAY từ khi layer tương ứng code.
- Eval set cho router/composer (gold labels) — xây cùng C6.

## 4. Không làm trong phase 1

Instrument Langfuse SDK (C6); ngưỡng số cụ thể (chờ baseline); eval set (C6); dashboard metric (M3/T-037).
