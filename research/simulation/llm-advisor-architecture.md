# Research — Kiến trúc LLM-in-the-loop Advisor + Observability (T-025/T-026)

Ngày: 2026-07-21 · Nguồn: research đợt 5 · Phục vụ: `specs/advisor-system-detail.md` (sẽ viết), T-019/T-026
Bối cảnh cố định: lớp A = DP deterministic (không LLM); lớp C = LLM reasoning có guardrail; LLM chính **deepseek-v4-flash** qua endpoint OpenAI-compatible (aggregator ai-box.vn), fallback **gpt-4o-mini**; ~50 actors × ≤6 advice ≈ 300 advice/ngày sim.

## 1. Kiến trúc CHỐT: "Spec-first, LLM-offline, deterministic replay" — (b) mặc định + (c) dạng two-phase batch

**KHÔNG gọi LLM realtime trong sim loop (a)** vì: (1) phá determinism/CRN — tài sản quý nhất của twin-world; (2) sim từ vài giây thành 10–25 phút; (3) **adherence model đọc advice SPEC, không đọc text** → text LLM là presentation layer, render sau sim không đổi kết quả (pattern offline batch inference chuẩn ngành — [Spheron 2026](https://www.spheron.network/blog/batch-llm-inference-gpu-cloud/), [AWS generative ABM](https://aws.amazon.com/blogs/hpc/llms-the-new-frontier-in-generative-agent-based-simulation/)).

```text
SIM PASS 1 (SimPy thuần, nhanh, deterministic)
  Trigger engine → DP solver → ADVICE SPEC (JSON: advice_id, actor, t, action,
      numbers_from_rule[], constraint_binding, value_gap, needs_reasoning?)
      ├→ parquet advice_log        └→ adherence model đọc SPEC → twin-diff outcome
         │ (needs_reasoning=true)          │ (mọi spec)
         ▼                                 ▼
PHASE C: LLM reasoning batch          PHASE B: LLM render batch (async 10–20 song song)
  JSON mode, {choice, rationale,        spec → text tiếng Việt; số CHỈ copy từ numbers_from_rule
  confidence} → decision cache          dedup cache hash(spec+prompt_ver+model)
  (key = state hash)                    validate Pydantic + number-consistency; fail 2 lần → template
         ▼
SIM PASS 2 (chỉ khi lớp C đổi quyết định): replay đọc cache → vẫn deterministic
```

- **Lớp C không cần realtime**: DP flag `needs_reasoning` (value_gap top-2 nhỏ, biến bất định) → pass-1 dùng tie-break deterministic, LLM batch quyết định, ghi **decision cache** (key=state hash), pass-2 replay đọc cache.
- **Chi phí**: ~300 advice × (700 in + 250 out tok) ≈ **$0.05/ngày sim** giá DeepSeek gốc — tiền không phải yếu tố; latency + determinism mới là.
- **Cache 2 tầng**: exact-match dedup (canonicalize spec bỏ actor_id/timestamp — nhiều actor cùng archetype nhận spec giống nhau) bằng diskcache/sqlite; provider-side context caching của DeepSeek (input cache-hit $0.0028/M vs $0.14/M — đặt system prompt cố định lên đầu). ⚠️ Pass-through qua ai-box.vn cần smoke-test.

## 2. Structured output với DeepSeek (đã kiểm docs)

- **JSON mode** có (`response_format={"type":"json_object"}`); bắt buộc chữ "json" trong prompt + kèm ví dụ; docs cảnh báo **thỉnh thoảng content rỗng → phải retry** ([DeepSeek JSON](https://api-docs.deepseek.com/guides/json_mode/)).
- **Function calling strict mode** chỉ qua `base_url .../beta` → **không dùng được qua aggregator**; và không cần (không có tool thật).
- **CHỐT: JSON mode + Pydantic validate phía client (instructor)**.

## 3. Stack code

| Thư viện | Vai trò |
| --- | --- |
| `openai` SDK (base_url ai-box.vn) | client; retry built-in (mặc định 2, exponential backoff 408/429/5xx); timeout httpx |
| `instructor` (Mode.JSON) | Pydantic schema + tự retry khi validation fail (bắt cả lỗi empty content) |
| `pydantic` v2 | `AdviceText`, `ReasoningDecision` |
| `diskcache`/sqlite | dedup cache |
| `langfuse` SDK v3 | observability — drop-in `from langfuse.openai import openai` |

Fallback 4 tầng: (1) SDK retry mạng → (2) instructor retry schema → (3) đổi model `gpt-4o-mini` cùng endpoint → (4) **template rule-based** (bắt buộc theo guardrail "LLM tắt được"). KHÔNG dùng LiteLLM lúc này (dependency lớn, thừa với 2 model/1 endpoint); nâng cấp khi >2 provider.

## 4. Observability — CHỐT: Langfuse chính, Arize Phoenix thay thế

| Tiêu chí | Langfuse | Phoenix | LangSmith | Weave/MLflow/Helicone |
| --- | --- | --- | --- | --- |
| License | MIT, self-host full tính năng | ELv2, OSS | đóng, SaaS | xem research chi tiết |
| Self-host 2 người | Docker Compose NẶNG (PG+ClickHouse+Redis+S3) | **1 container duy nhất** | không free | — |
| Free cloud | Hobby 50k obs/tháng, 2 users | self-host free | giới hạn | — |
| Tích hợp | drop-in openai import + `@observe()` nested | OTel auto-instrument | mạnh với LangChain | — |

**Bắt đầu Langfuse Cloud Hobby** (~30–40k obs/tháng vừa khít 50k); chạm trần hoặc cần offline → self-host; **Phoenix 1-container** nếu muốn 100% local ngay. Cả hai OTel-friendly → chuyển đổi rẻ.

Trace mapping: 1 trace = 1 advice lifecycle: `trigger_eval` span → `dp_solve` span → `generation` (auto) → scores `adherence`/`income_delta`/`numeric_consistency` gắn sau twin-diff. Trace id deterministic từ advice_id để join parquet.

## 5. Metrics per-layer (bảng đầy đủ trong báo cáo — tóm tắt)

- **Trigger**: advice/actor/ngày, cooldown_hit, suppression, phân bố theo loại+giờ.
- **DP**: solve_ms p50/p95, action distribution, **constraint_binding_freq**, value_gap (→ tỷ lệ lớp C), infeasible_rate.
- **LLM**: latency, tokens/cost, json_valid_first_try, fallback_rate theo tầng, dedup hit, provider_cache_hit.
- **LLM guardrail**: **numeric_hallucination_rate** — regex trích mọi số trong text so với `numbers_from_rule[]` (check bằng CODE, không LLM-judge); forbidden_content (khuyên nhận/hủy đơn); confidence calibration.
- **Adherence/Outcome**: taxonomy 5 nhãn twin-diff, income_delta paired, phân rã advice type × archetype.
- **Kênh đôi**: parquet = phân tích chính (join event log, DuckDB); Langfuse = debug từng advice; cùng struct, không tính hai lần.

## 6. Multi-map: CHƯA cần map 2 cho robustness — cần cho external validity

- Chuẩn validation ABM = **sensitivity analysis/parameter sweep trên cùng world** (OFAT, Morris, Sobol) — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0210678), [AI Review 2025](https://link.springer.com/article/10.1007/s10462-025-11412-6).
- **Domain randomization = đa dạng hóa THAM SỐ dynamics trên cùng môi trường** ([ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/56adf9cb91aedfa41ce24398782a012f-Paper-Conference.pdf)) — đúng danh sách sweep của ta (demand regime, weather, adoption, mix, outage).
- Bài học Procgen (cần 500+ levels) áp cho **learned policy**; DP solver không học từ map → không overfit kiểu đó. Thứ CÓ THỂ overfit map 1: threshold chỉnh tay, prompt lớp C, tham số adherence → đó là thứ cần held-out.
- **Cần map 2 khi**: (a) claim ngoài Đống Đa; (b) đã tune tham số trên map 1 (map 2 = test set); (c) claim phụ thuộc topology (mật độ trạm đặc thù). → Ma trận robustness pilot: **1 map × {3 demand × 2 weather × 3 adoption × 3 mix × outage on/off} × ≥5 seeds**; map 2 DEFERRED với điều kiện mở lại rõ.

## 7. Việc verify sớm (trước khi chốt stack)

Smoke-test 10 call qua ai-box.vn: (1) `response_format` pass-through? (2) `usage.prompt_cache_hit_tokens` có trả? (3) latency/model list; (4) fallback gpt-4o-mini cùng endpoint hoạt động?

(Toàn bộ URL nguồn trong transcript research; các claim chính đã dẫn link inline.)
