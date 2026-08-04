# UPDATE-134 — AdviceCheckpoint Agent template-first + lazy Why implementation

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Loại:** implementation / evidence hand-off
- **TODO / User story liên quan:** `CKPT-P6`, AdviceCheckpoint presentation; không đổi claim của người khác

## Tóm tắt

Đã triển khai phương án đã duyệt: template-first, deterministic `SILENT|TEMPLATE|LLM`, strict provider adapter không tools và lazy “Vì sao?”. Template-only vẫn là đường mặc định; provider live không được gọi trong cycle này. Canonical/lifecycle focused gates được chạy trước khi thêm adapter/generation path. Trạng thái code là `DONE-CODE`; HTTP TestClient/AnyIO portal và Flutter/device visual vẫn `BLOCKED/WAITING-VERDICT`, nên chưa phải production-ready.

## Chi tiết cập nhật

- Xác minh `.env` có OpenAI-compatible provider, nhưng không ghi API key vào tài liệu/log.
- Xác minh `CheckpointPresenter` hiện chỉ `template|shadow`; `LLMComposerClient` là legacy Composer contract và không được tái sử dụng trực tiếp.
- Chốt provider boundary không tools, allowlisted input, closed reason/why output, deterministic verifier, cache/claim, stale revalidation và immutable lease content.
- Chốt lazy Why endpoint không gọi solver, không tạo checkpoint, không thay accepted/dismissed/execution.
- Thêm registry template có current/future wording, typed numbers và version.
- Thêm provider OpenAI-compatible riêng, timeout/token/call budget/kill-switch; key chỉ đọc từ env và không đi vào artifact/log.
- Thêm proactive generation claim/cache/verifier/stale fallback; lease pin artifact + digest + version metadata.
- Thêm lazy Why service/router/cache/idempotency, historical fallback và `expanded` side-channel.
- Web demo dùng DOM API an toàn, action/current/future/provenance render, Why loading/retry/step guard và ACK retry.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/advisor/checkpoint_templates.py` | tạo | deterministic template registry |
| `src/gsm_core/advisor/presentation_strategy.py` | tạo | pure strategy + reason codes |
| `src/gsm_core/advisor/advice_agent.py` | tạo | strict structured provider, no tools |
| `schemas/advisor/agent_presentation_input@1.0.0.schema.json` | tạo | historical snapshot |
| `schemas/advisor/agent_explanation_{input,output}.schema.json` | tạo | lazy Why closed contract |
| `ui/contracts/advice_why.json` | tạo | response envelope contract |
| `ui/web/js/demo_guards.js` | tạo | monotonic step/ACK guards |
| AdviceCheckpoint, store, simulator trace/session, router, Web files | sửa | canonical prerequisites + orchestration/UI wiring |
| `tests/`, `ui/backend/tests/`, `ui/web/tests/` | sửa/tạo | focused TDD gates |

## Docs đã cập nhật kèm theo

`SCOPE`, `DEFERRED`, `USER_STORIES` không đổi. Không bật feature flag và không chỉnh claim của người khác. `TODO/PROJECT-GRAPH` chưa được đánh dấu production-ready; visual/provider owner gates vẫn mở.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Provider là OpenAI-compatible | `OBSERVED-CODE` | `.env` có `AI_PROVIDER=openai`, `OPENAI_BASE_URL`, `DEFAULT_MODEL`; key redacted | cao | Adapter phải đổi transport |
| Legacy `LLMComposerClient` không phù hợp AdviceCheckpoint output | `OBSERVED-CODE` | `src/gsm_core/advisor/llm_client.py`, `composer.py` trả `advice_spec` | cao | Có thể làm Agent thay canonical fields |
| Canonical prerequisites đã sửa trong code | `FOCUSED-VERIFIED` | trace/session/lease/silent/ACK tests listed below | cao | HTTP contract vẫn bị environment hang |
| Template-only fallback luôn khả dụng | `FOCUSED-VERIFIED` | `CheckpointPresenter(mode="template")`, generation/Why fallback tests | cao | rollback bằng flags |
| Provider credentials không lộ | `FOCUSED-VERIFIED` | fake-provider redaction tests; không gọi network | cao | provider smoke chưa chạy |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `PYTHONPATH=src .venv/bin/python scripts/compare_checkpoint_shadow.py --config configs/pilot_dongda.yaml --seeds 1000 1001 1002 1003 1004` | 1000–1004 | trace on/off comparator | `IDENTICAL` cho cả 5 seed | Không thay thế full sweep |
| Focused Python suite (canonical + Agent + Why, `-k 'not http'`) | fixtures + demo traces | run_id, alignment, post-mutation, isolation, lease pin, strategy, provider, Why | **118 passed, 1 deselected**; HTTP contract được chạy riêng với timeout và exit 124 | Không chạy full backend/simulator/solver |
| `tests/test_advice_agent_provider.py tests/test_presentation_strategy.py ui/backend/tests/test_demo_advice_bridge.py ui/backend/tests/test_advice_generation_flow.py ui/backend/tests/test_demo_advice_why.py` | fixtures | provider budget/kill, status strategy, pinned replay, proactive + Why | **23 passed** | no network |
| Web Node smoke + syntax (`cards-security`, `unified-demo`, guards, advice-v2, pricing) | source/contract | safe DOM, lazy Why, ACK/stale guards | **all pass** | browser/emulator chưa chạy |
| `timeout 20s env PYTHONPATH=ui/backend .venv/bin/python -m pytest -q ui/backend/tests/test_demo_session_api.py::test_http_contract_uses_idempotent_step_and_version_conflict` | — | TestClient HTTP contract | **exit 124 timeout** | FastAPI 0.141.1 / Starlette 1.3.1 / httpx 0.28.1 AnyIO portal hang; cần env debug riêng |
| `.env` inspection | không | provider config | Base URL/model/key presence xác minh, key không xuất | Provider availability/latency chưa kiểm |

## Visual verification

- **Status:** `BLOCKED / WAITING-VERDICT`
- **Cách launch / artifact:** Node source/smoke đã pass; Flutter SDK/device và browser visual chưa có trong environment.
- **Seed / scenario đã xem:** comparator 5/5 seed identical; không claim V-25.
- **Người review + verdict:** Chưa có human visual verdict.
- **Lý do:** Flutter/Dart vắng; HTTP TestClient contract còn treo ở portal boundary.

## Adversarial self-review / flaws found

1. Provider live không được gọi trước focused canonical gates; adapter chỉ được tạo khi allowlist + mode bật.
2. Input future-plan là typed allowlist; raw solver report/PII/coordinates không qua provider boundary.
3. Lease retry đọc artifact đã pin theo digest; replay bridge không rerender.
4. Proactive và Why dùng namespace/cache key khác nhau; Why chỉ gọi sau click.
5. HTTP TestClient timeout vẫn là environment/application boundary chưa được sửa; không tuyên bố HTTP API xanh.
6. `cards.js` legacy renderer đã bỏ raw markup; Web dynamic text dùng DOM APIs.

## Expansion checkpoint (T-039)

1. **Schema:** thêm `agent_presentation_input@1.1.0` với typed future plan; output giữ closed 1.0.0.
2. **Bài toán tối ưu:** không thêm solver/objective/cadence.
3. **Tính năng:** lazy Why và selective presentation; không mở conversational agent.

## Follow-up / defer phát sinh

- `CKPT-P6` code path chuyển sang `DONE-CODE` cho template/lazy Why và strict adapter; không claim production/live.
- Flutter/device V-25, HTTP contract environment, provider smoke/budget owner, production/canary vẫn mở.
- Rollback đã kiểm soát bằng `ADVICE_PRESENTATION_MODE=template`, `ADVICE_WHY_AGENT_ENABLED=0`, `ADVICE_AGENT_ALLOWLIST=0`, `ADVICE_AGENT_KILL_SWITCH=1`, `ADVICE_V2_ENABLED=0`.
