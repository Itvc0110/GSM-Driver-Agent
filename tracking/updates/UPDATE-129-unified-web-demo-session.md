# UPDATE-129 — Server-owned Unified Web Demo session/cursor

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / VISUAL BLOCKED` (session/API; canonical step projection đang ở Task 3)
- **TODO:** `WEB-DEMO-UNIFIED`

## Kết quả

Thêm `DemoSessionService` và `/api/v1/demo` để Web không còn sở hữu cursor. Session giữ
`run_id/seed`, actor catalog, selected actor, cursor, monotonic `step_version`, lifecycle
status và map idempotency `client_step_id → response`. Mỗi session có lock riêng; retry cùng
client ID trả nguyên response, còn request với version cũ trả conflict.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `ui/backend/app/services/demo_session.py` | tạo | run cache + trace projection + cursor/idempotency |
| `ui/backend/app/routers/demo.py` | tạo | create/select/state/Next Step HTTP contract |
| `ui/backend/app/main.py` | sửa | mount `/api/v1/demo` |
| `ui/backend/tests/test_demo_session_api.py` | tạo | service + HTTP retry/version/error gates |

## Evidence

| Claim | Nhãn | Evidence | Confidence |
|---|---|---|---|
| Hai request cùng `client_step_id` không advance hai lần | `OBSERVED-CODE` | focused test `test_session_requires_actor_and_advance_is_idempotent` | cao |
| Stale `expected_step_version` bị chặn 409 | `OBSERVED-CODE` | HTTP focused test ngoài sandbox | cao |
| Session là observer replay, không live SimPy | `FACT` | service chỉ giữ `RunResult`/trace và đổi cursor | cao |
| Store in-process đủ cho MVP một process | `ASSUMPTION` | chưa có multi-process deployment requirement | trung bình |

## Kiểm chứng

- `.venv/bin/python -m pytest -q ui/backend/tests/test_demo_session_api.py` trong sandbox bị treo ở TestClient/AnyIO portal và đã dừng.
- Cùng lệnh ngoài sandbox → **3 passed**, một Starlette deprecation warning.
- `.venv/bin/python -m pytest -q ui/backend/tests/test_demo_session_api.py` direct service path → **2 passed** trước HTTP wiring.
- Không chạy full backend/simulator/solver.

## Visual verification

- **Status:** `BLOCKED` — API chưa được render vào Web; gate sẽ chạy sau Task 5.

## Adversarial self-review / flaws found

1. Response idempotency được kiểm tra trước version/status để retry cuối cùng vẫn trả đúng
   response; client ID mới với version cũ vẫn bị 409.
2. Actor không thể đổi sau khi cursor đã advance; tránh trộn trajectory giữa hai actor.
3. Khi trace hết, session trả 410 cho request đúng version; response cuối vẫn chứa snapshot
   cuối để Web render được.
4. In-process registry không chịu được nhiều worker process; nếu deployment dùng nhiều worker
   phải đổi sang store phân tán trước khi canary, không âm thầm giả định.

## Expansion checkpoint (T-039)

1. **Schema:** chưa thêm schema public; response đầy đủ sẽ khóa ở Task 3.
2. **Bài toán tối ưu:** không.
3. **Tính năng:** API đã có nền cho actor picker/Next Step; route/trip/advice projection còn thiếu.

## Follow-up

- Task 3 thêm closed canonical step envelope và route cache/fallback.
- Giữ old `/api/v1/trip/step` chỉ vì compatibility; không gọi từ unified flow.
