# UPDATE-128 — Observable simulator trace cho Unified Web Demo

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / VISUAL BLOCKED` (trace layer; Web chưa nối)
- **TODO:** Unified Web Demo / CKPT-P6 dependency

## Kết quả

Thêm observer-only snapshots tại `World.log()` và projection thuần
`gsm_sim.demo_trace.build_demo_trace()`. Snapshot lấy state của actor ngay sau event
hiện hữu; không gọi solver mới, không gọi RNG và không mutate dynamics. Projection dựng
transition ID deterministic, driver snapshot, state delta, trip lifecycle từ event, segment
join và checkpoint reference từ `RunResult`.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `src/gsm_sim/world.py` | sửa | thêm `trace_snapshots` và observer trong `World.log()` |
| `src/gsm_sim/runner.py` | sửa | expose snapshots qua `RunResult` |
| `src/gsm_sim/demo_trace.py` | tạo | pure event/segment/checkpoint projection cho Web replay |
| `tests/test_demo_trace.py` | tạo | deterministic transition/trip/delta/unknown actor gates |

## Evidence và assumptions

| Claim | Nhãn | Evidence | Confidence |
|---|---|---|---|
| Observer không thay đổi semantic outcome | `OBSERVED-CODE` | `test_run_once_wires_shadow_trace_without_changing_semantic_outcomes` xanh với semantic fingerprint | cao |
| Transition chỉ project event actor-facing | `OBSERVED-CODE` | `demo_trace._VISIBLE_EVENT_KINDS` + focused tests | cao |
| Demo có thể dùng snapshot thay vì tái dựng từ actor cuối run | `FACT` | `RunResult.trace_snapshots` giữ state sau từng event | cao |
| Trace snapshot có tọa độ để render bản đồ demo | `ASSUMPTION` | Web demo cần canonical driver position; tọa độ không đi vào checkpoint solver artifact | trung bình |

## Kiểm chứng

- `.venv/bin/python -m pytest -q tests/test_demo_trace.py` → **3 passed**.
- `.venv/bin/python -m pytest -q tests/test_checkpoint_trace.py::test_run_once_wires_shadow_trace_without_changing_semantic_outcomes tests/test_checkpoint_trace.py::test_ram_sink_keeps_exact_solver_artifacts_and_links_execution_post_run` → **2 passed**.
- `git diff --check` cho file cycle → PASS.

Không chạy full simulator/backend theo chỉ thị. Flutter/device chưa liên quan ở cycle này.

## Visual verification

- **Status:** `BLOCKED` — Unified Web chưa chuyển sang session/canonical response nên chưa
  có màn hình mới để Cường xem. Phải mở replay/Web sau Task 5 trước khi đóng gate cuối.

## Adversarial self-review / flaws found

1. Snapshot sau event có thể phản ánh state trước một số mutation nếu callsite hiện hữu log
   trước mutation; projection giữ đúng observed state và không tự sửa thứ tự event.
2. `trip` state được dựng từ event sequence, không đọc `order_states` cuối run để tránh
   biến mọi transition thành trạng thái terminal.
3. Segment join là evidence quan sát, không gán quan hệ causal hay `accepted`.
4. Checkpoint xuất hiện cùng phút event mới được attach; checkpoint lẻ được thêm transition
   riêng, không tạo checkpoint giả.

## Expansion checkpoint (T-039)

1. **Schema:** chưa cần field mới trong AdviceCheckpoint; `RunResult.trace_snapshots` là
   runtime projection nội bộ.
2. **Bài toán tối ưu:** không phát sinh solver/objective mới.
3. **Tính năng:** mở đường cho server-owned demo cursor; chưa nối Web/OSRM/Agent.

## Follow-up

- Task 2 phải dùng `build_demo_trace` trong server-owned session và khóa cursor/idempotency.
- Giữ visual gate `BLOCKED` tới khi Unified Web render canonical snapshot thật.
