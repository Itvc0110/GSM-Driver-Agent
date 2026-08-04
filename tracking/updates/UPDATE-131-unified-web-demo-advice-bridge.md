# UPDATE-131 — AdviceCheckpoint bridge cho Unified Web Demo

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / VISUAL BLOCKED` (bridge/presenter; Web chưa nối)
- **TODO:** `WEB-DEMO-UNIFIED`

## Kết quả

`DemoSessionService` nay dùng cùng checkpoint SQLite path với Advice v2 (hoặc path được
inject trong test), persist exact checkpoint/artifact bundle đã có trong `RunResult`, replay
lifecycle event từ simulator và gọi `AdviceCheckpointService.present_existing_checkpoint()`.
Bridge này không gọi lại solver khi bấm `Next Step`; nó chỉ thực hiện READY/validity/presenter/
lease flow. Checkpoint queued, suppressed, expired hoặc terminal trả silent; khi không có
lifecycle event trong fixture tối thiểu, một record `created` được chuyển READY đúng một lần.

Advice response vì vậy là `AdviceEnvelopeV2` thật với immutable `display_id`, provenance và
template presentation; không còn trả raw checkpoint/reference hoặc fake ID. Store path dùng
chung với ACK endpoints để Web có thể gửi mounted/displayed event sau khi render.

Verifier bổ sung reject markup HTML và control characters trong agent-owned reason/why sau
khi loại placeholders. Template vẫn là fallback và bridge bắt lỗi presentation để replay step
không thất bại.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `ui/backend/app/services/demo_session.py` | sửa | persist trace bundle/events, present existing checkpoint, safe silent fallback |
| `ui/backend/app/services/advice_checkpoint.py` | sửa | reject queued/non-ready replay state before lease |
| `src/gsm_core/advisor/checkpoint_presenter.py` | sửa | verifier markup/control-character guard |
| `tests/test_checkpoint_presenter.py` | sửa | adversarial unsafe markup/control cases |
| `ui/backend/tests/test_demo_advice_bridge.py` | tạo | template envelope, shared store, no-checkpoint silent contract |

## Evidence

| Claim | Nhãn | Evidence | Confidence |
|---|---|---|---|
| Demo replay uses exact trace artifacts and does not invoke product solver on click | `OBSERVED-CODE` | `_advice()` calls `create_checkpoint_bundle()` + `present_existing_checkpoint()`, no `ProductSolverOrchestrator.solve` | cao |
| Simulator policy verdict is preserved | `OBSERVED-CODE` | exported `advice_checkpoint_events` are appended before presentation; non-ready state is silent | cao |
| Lease/display identity is shared with v2 ACK router | `FACT` | default DB path is `data/ui-telemetry/advice_checkpoint.db`; bridge calls existing `acquire_presentation_lease` | cao |
| Model-owned markup cannot reach presenter output | `OBSERVED-CODE` | `verify_agent_output()` guard + focused adversarial tests | cao |

## Kiểm chứng

- `.venv/bin/python -m pytest -q tests/test_checkpoint_presenter.py ui/backend/tests/test_demo_advice_bridge.py ui/backend/tests/test_demo_step_contract.py ui/backend/tests/test_demo_session_api.py` → **22 passed**, 1 Starlette deprecation warning.
- Không chạy full backend/simulator/solver theo chỉ thị.

## Visual verification

- **Status:** `BLOCKED` — Web chưa render canonical step và chưa gửi displayed ACK; sẽ kiểm tra
  sau Task 5.

## Adversarial self-review / flaws found

1. Checkpoint schema cho phép `synthetic|mock-realdata|live`, không phải `sim-engine`; bridge
   giữ vocabulary schema của checkpoint và chỉ dùng `sim-engine` ở envelope/provenance demo.
2. Store mở connection theo từng step để không chia sẻ SQLite connection qua worker thread;
   deployment nhiều process vẫn cần session/shared-store decision trước canary.
3. Bridge catch presentation failure thành silent fallback để giữ cursor/replay usable; lỗi
   phải được telemetry/HTTP observability bổ sung nếu bật live Agent.

## Expansion checkpoint (T-039)

1. **Schema:** chưa cần field mới; AdviceEnvelopeV2 đã có source/provenance và lease IDs.
2. **Bài toán tối ưu:** không phát sinh; không solve lại theo click.
3. **Tính năng:** mở đường cho Web render template/Agent source trên canonical step.

## Follow-up

- Task 5 chuyển `/app/` từ client-owned `tripStep`/hard-coded trip sang `/api/v1/demo`.
- Giữ `ADVICE_PRESENTATION_MODE=template` và `ADVICE_V2_ENABLED=0` mặc định.
