# UPDATE-030 — C6 Agent pipeline (Router → Composer → Verifier) + F0 corpus-based + observability

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (theo yêu cầu Cường — "pull về làm luôn F0")
- **Loại:** feature
- **TODO / User story liên quan:** T-038 C6, T-026 phase 2, T-039; US-F0-01, US-F1-03/04, US-F2/F3

## Tóm tắt

Xây toàn bộ tầng advisor `src/gsm_core/advisor/` — pipeline AdviceRequest → Router (zero-ML) → SolverReport song song (nhận từ caller) → Context Pack (1 renderer) → Composer (LLM #1, **placeholder-first**) → Verifier (3 tầng, tầng 1 CODE có quyền veto) → ComposedAdvice + episode store, kèm observability per-layer (2 HARD invariant). LLM lần đầu vào hệ. Đường LLM-off (template) là guardrail bắt buộc, luôn chạy. F0 dựa **corpus T-004 sạch** với track-guardrail. Phát hiện + fix **3 bug thật** trong lúc build (đều có regression test).

## Chi tiết cập nhật

**Kiến trúc (spec core §3–§5, research đợt 7 `agent-pipeline-patterns.md`):**
- **Router** direct-map feature→solver set, keyword tiếng Việt xác nhận intent, câu lạ → `out_of_taxonomy` (R5).
- **Context Pack** = 1 renderer duy nhất cho cả Composer prompt lẫn Verifier: SolverReport → Markdown-KV trong XML, số canonical `[N-id]`, system prompt STATIC byte-identical (prefix cache), `numbers_registry` là nguồn sự thật.
- **Composer placeholder-first**: LLM chỉ viết `message_template` chứa `{{N-id}}`; CODE thay bằng số format VN (`render_number_vn`). Faithfulness thành **bất biến cấu trúc** — LLM không bao giờ chạm chữ số. Repair ≤1; LLM chết/verify fail → cờ fallback → pipeline hạ template (fail-closed).
- **Verifier 3 tầng**: T1 CODE veto (V1 số trần / V2 blocklist tiếng Việt hứa-thu-nhập & khuyên-đơn & thiếu-disclaimer / V3 CJK / V4 F0-citation); T2 LLM-judge advisory (off default — EXP-001); repair→veto→template.
- **Episode store** SQLite append-only (kiêm DecisionRecord) + exact-key cache TTL 6h (KHÔNG semantic cache).
- **Observability** đọc metric TỪ SCHEMA: 2 HARD invariant `solver.number_traceability=1.0` + `composer.faithfulness=1.0` tính trực tiếp; span parquet dual-channel; Langfuse optional (lazy, bật khi có env key).
- **LLM client** (live) lazy `openai` JSON-mode + fallback 4 tầng (primary deepseek → reask → gpt-4o-mini → template). **Không dùng instructor** (JSON-mode thuần đủ, tối thiểu deps) — lệch nhẹ so plan, ghi rõ.

**3 bug thật phát hiện khi build (root-cause protocol đầy đủ):**
1. **BUG-C6-01 (normalize đ/Đ)** — `_norm` dùng NFD+strip-Mn nhưng đ/Đ (U+0111/U+0110) là **chữ cái riêng**, NFD KHÔNG tách → "đơn"→"đon", "điểm"→"điem", "đổi pin"→"đoi pin". Hệ quả: keyword match tiếng Việt ÂM THẦM hỏng ở **cả 3 module** (F0 KB retrieve, router intent, verifier blocklist). Fix: `_text.normalize_vi()` map tay `đ→d` trước NFD; gom 3 bản `_norm` trùng về 1 nguồn.
2. **BUG-C6-02 (promise pattern báo nhầm tên chính sách)** — pattern nới rộng bắt theo co-occurrence "đảm bảo"+"thu nhập", nhưng chính sách GSM tên chính thức là *"Chính Sách **Đảm Bảo Thu Nhập**"* → mọi câu F0 trích nguồn này bị gán "hứa thu nhập". Fix: promise = HỨA KẾT QUẢ KIẾM TIỀN (động từ "kiếm được/đạt được" hoặc mức tiền cụ thể), KHÔNG phải danh từ chính sách.
3. **BUG-C6-03 (verifier soi text trích dẫn official)** — tiêu đề policy trích verbatim chứa số (ngày "05/06/2026", "2 chiều") hoặc từ hứa hẹn bị V1/V2 gán cho agent. Fix: `cited_texts` — gỡ đoạn trích official + text solver-authored (digest/heuristic_note/reason, deterministic & truy vết được) khỏi phạm vi soi; guardrail chỉ soi CLAIM của agent.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/advisor/_text.py` | tạo | `normalize_vi` — 1 nguồn chuẩn hoá VN (fix BUG-C6-01) |
| `src/gsm_core/advisor/{policy_kb,router}.py` | sửa | dùng `_text.normalize_vi` thay bản `_norm` cục bộ |
| `src/gsm_core/advisor/verifier.py` | sửa | promise patterns (BUG-C6-02), `_strip_spans`/`cited_texts` (BUG-C6-03), dùng `_text` |
| `src/gsm_core/advisor/{policy_kb,router,context_pack,templates,episode_store,pipeline}.py` | tạo (tranche A) | pipeline deterministic |
| `src/gsm_core/advisor/{composer,llm_client,observability}.py` | tạo (tranche B) | placeholder-first + live client + metric |
| `src/gsm_core/advisor/templates.py` | sửa | `_advice_spec` (bỏ `expiry` rỗng — hợp schema), F1 bỏ digest trùng chữ |
| `src/gsm_core/advisor/pipeline.py` | sửa | fallback khi composer bỏ cuộc, `_trusted_spans`, recorder optional |
| `tests/{test_advisor_pipeline,test_composer_verifier,test_advisor_integration}.py` | tạo | 14+18+5 = 37 test |
| `scripts/smoke_advisor_live.py` | tạo | smoke live ngoài suite (in 4 advice mẫu) |
| `pyproject.toml` | sửa | +optional `llm = ["openai>=1.30"]` |

## Docs đã cập nhật kèm theo

- `tracking/TODO.md`: T-038 C6 → DONE (VALIDATING live path); T-026 phase 2 instrument xong.
- `tracking/DEFERRED.md`: +3 follow-up (F0 retrieval relevance, F0 policy-lookup vs bonus-gap tách intent, live LLM smoke thật).
- SCOPE/USER_STORIES: không đổi.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Pipeline deterministic (template/mock-LLM) đúng schema + 2 HARD invariant =1.0 | `OBSERVED-CODE` | 37 test xanh + 162 full suite | Cao | — |
| BUG-C6-01/02/03 fix đúng root cause | `OBSERVED-CODE` | reproduce + regression test đỏ→xanh mỗi bug | Cao | KB/guardrail sai âm thầm |
| Placeholder-first ⇒ faithfulness = bất biến cấu trúc | `OBSERVED-CODE` | `compute_faithfulness`=1.0 ∀ advice; V1 chặn số trần | Cao | Composer bịa số |
| Live LLM composer (deepseek qua ai-box.vn) | `UNVERIFIED` | Chưa cài `openai`, endpoint gpt-4o-mini từng 403 (T-025) | — | Live có thể format/parse lệch; template fallback vẫn an toàn |
| `_trusted_spans` số từ solver digest truy vết được | `ASSUMPTION` | solver là component math verified; nhưng số trong digest CHƯA nằm trong `numbers[]` | TB | Số digest sai → lọt V1 (mитigation: solver nên đăng ký mọi số surfaced) |
| S2/S3/S4 report trong integration test | `MOCK` | fixture gắn nhãn trong docstring test | — | Chỉ test seam pipeline, không phải solver thật trên mock |

## Kiểm chứng

37 test advisor (14 pipeline tranche A + 18 composer/verifier tranche B + 5 integration/observability) xanh; full suite **162 passed**. Từng rule verifier có test đỏ→xanh riêng. Integration 3 driver × 4 feature template-mode → 12/12 advice hợp schema `composed_advice`, faithfulness=1.0, verifier pass, 12 episode ghi, parquet span flush được. Smoke script chạy template-fallback (thiếu `openai`) → in 4 advice mạch lạc, HARD invariant OK.

**CHƯA kiểm chứng:** đường LLM **live thật** (cần `uv sync --extra llm` + `.env` + endpoint sống) — composer/verifier/repair với model thật chưa chạy; T2 LLM-judge (off default) chưa bật.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `pytest tests/test_advisor_*` | deterministic (no RNG) | 4 feature × rule-level | 37 passed | — |
| `pytest -q` (full) | — | toàn repo | 162 passed | — |
| `smoke_advisor_live.py` | — | F0–F3, driver d-1 | 4 advice + HARD OK (template mode) | live LLM path |

## Visual verification

- **Status:** `NOT_APPLICABLE` (JSON pipeline; UI ở M3/T-035–037). Thay bằng **sample text advice** cho Cường xem.
- **Cách launch / artifact:** `uv run python scripts/smoke_advisor_live.py` (in 4 advice F0–F3).
- **Seed / scenario đã xem:** driver d-1, policy sim-policy-v0, track platform; 4 feature.
- **Người review + verdict:** chờ Cường xem 4 advice mẫu (in ở phần hội thoại) — trước commit/push.
- **Nếu NOT_APPLICABLE:** không có dashboard/replay ở C6; text advice thay thế theo CLAUDE.md §4b.

## Adversarial self-review / flaws found

1. **Trông tốt nhưng có thể sai:** faithfulness=1.0 là *cấu trúc* (placeholder-first) — chỉ đúng nếu Composer THẬT tuân "chỉ dùng {{N-id}}". Live model có thể tự viết số → V1 phải bắt. **Đã test** mock trả số trần → veto→template. Live CHƯA test → `UNVERIFIED`.
2. **Hidden fallback:** composer bỏ cuộc trả message rỗng "" có thể lọt V1/V2/V3 (rỗng không vi phạm) nhưng vi phạm schema `minLength:1`. **Đã đóng:** pipeline hạ template khi `fallback_used=True` bất kể verify.
3. **Whitelist loophole (`cited_texts`/`_trusted_spans`):** gỡ đoạn trích khỏi soi số CÓ THỂ cho lọt số bịa nếu trùng text nguồn. Mitigation: LLM không emit số (placeholder-first) nên không chèn được số vào tiêu đề; template chỉ nhúng registry-number + text solver deterministic. Rủi ro thực tế ~0 ở đường hiện tại, nhưng ghi DEFERRED: solver nên đăng ký MỌI số surfaced (kể cả khung giờ) vào `numbers[]` để khỏi tin digest nguyên khối.
4. **Unit/double-count:** `numbers[]` trong ComposedAdvice = TOÀN BỘ registry (superset số thực dùng trong message) — provenance đúng, không double-count tiền; nhưng chưa lọc theo số THỰC xuất hiện. Ghi nhận, chưa phải bug (mọi số đều truy vết).
5. **Baseline loại trừ:** BUG-C6-01 chứng minh bằng in `_norm("đơn")="đon"` + NFD không có Mn cho U+0111 (loại giả thuyết "regex sai"); BUG-C6-02/03 chứng minh bằng chạy blocklist trên đúng 7 title corpus (loại giả thuyết "chỉ test sai").
6. **Flaw mở → map:** F0 retrieval relevance + policy-lookup tách bonus-gap + live smoke → DEFERRED (D-C6-01/02/03).

## Expansion checkpoint (T-039)

1. **Schema:** ComposedAdvice có thể thêm field `numbers_used` (subset số THỰC xuất hiện trong message, tách khỏi `numbers` provenance) — cho UI hiển thị đúng số nào được nêu. SolverReport nên thêm quy ước: mọi số surfaced trong `problem_digest` phải có entry `numbers[]` tương ứng (đóng loophole `_trusted_spans`). **Đề xuất — chờ Cường.**
2. **Bài toán tối ưu:** residual R3 (giải trình infeasibility) và R4 (what-if) chưa formalize — hiện Composer/template chỉ trình bày. R4 what-if ("nếu chạy thêm 1h?") có thể thành **solver nhỏ** re-run S1/S2 với param nhiễu → so sánh, thuần math. Ứng viên solver mới.
3. **Tính năng:** episode store đã bandit-ready (propensity/reward nullable) → EXP bandit chọn template/persona (C7). Observability parquet đủ để dựng dashboard metric advisor (gộp vào T-037).

## Follow-up / defer phát sinh

- **D-C6-01** (DEFERRED, sev thấp): F0 KB retrieval relevance — query "thưởng" hiện cite "Bộ quy tắc ứng xử" thay vì chính sách thu nhập. Mở lại khi F0 lên UI thật / có eval set citation-relevance (C7).
- **D-C6-02** (DEFERRED, sev TB): F0 template luôn nêu bonus-gap dù câu hỏi thuần policy → tách intent "policy-lookup" (chỉ trả trích dẫn) vs "bonus-gap" (có số). Cần khi F0 free-text đa dạng.
- **D-C6-03** (TODO, sev TB): chạy `smoke_advisor_live.py` với LLM thật (`uv sync --extra llm` + `.env` + endpoint) — verify composer/verifier/repair live; bật khi endpoint ổn (gpt-4o-mini từng 403).
- **D-C6-04** (DEFERRED, sev thấp): solver đăng ký mọi số surfaced (kể cả khung giờ) vào `numbers[]` để bỏ phụ thuộc `_trusted_spans` digest.
