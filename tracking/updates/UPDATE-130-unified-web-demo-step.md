# UPDATE-130 — Canonical Unified Web Demo step projection

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / VISUAL BLOCKED` (canonical step; Web/Agent chưa nối)
- **TODO:** `WEB-DEMO-UNIFIED`

## Kết quả

`DemoSessionService.advance()` hiện trả một snapshot canonical gồm simulation time,
transition, driver snapshot, state delta, derived trip lifecycle, map markers, route legs,
advice reference, compact timeline và provenance. Trip state chỉ được project từ simulator
event sequence. Route được tách `driver_to_pickup` và `pickup_to_destination`, cache theo
endpoint/leg và loại bỏ fare khỏi route payload để không ghi đè payout canonical của simulator.

OSRM/GraphHopper hiện hữu được gọi qua routing provider trong default path; provider exception
rơi về straight-line geometry với `route_is_real_road=false`, `source=fallback_straight_line`.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `ui/backend/app/services/demo_session.py` | sửa | route cache/fallback + canonical step fields |
| `ui/backend/tests/test_demo_step_contract.py` | tạo | response/route/fallback contract |

## Evidence

| Claim | Nhãn | Evidence | Confidence |
|---|---|---|---|
| Web có thể render cả driver/trip/map/route trong một response | `OBSERVED-CODE` | `test_step_response_contains_canonical_driver_trip_map_and_route` | cao |
| OSRM lỗi không làm step fail | `OBSERVED-CODE` | `test_route_failure_is_a_fallback_and_does_not_fail_step` | cao |
| Route không thay canonical payout/SOC | `FACT` | route projection chỉ đọc transition; simulator values lấy từ trace | cao |
| Default online route latency phù hợp từng click | `UNVERIFIED` | chưa chạy Web live với OSRM trong environment này | thấp |

## Kiểm chứng

- `.venv/bin/python -m pytest -q ui/backend/tests/test_demo_step_contract.py ui/backend/tests/test_demo_session_api.py` ngoài sandbox → **5 passed**, 1 Starlette deprecation warning.
- Không chạy full backend/simulator/solver.

## Visual verification

- **Status:** `BLOCKED` — Web vẫn chưa dùng response canonical; visual gate chờ Task 5.

## Adversarial self-review / flaws found

1. Route payload không trả `fare_vnd`/`driver_payout_vnd`; tránh UI dùng OSRM distance để tính
   lại tiền. Payout chỉ nằm trong trip/driver snapshot từ simulator.
2. `COMPLETED` giữ leg pickup→destination để xem lại lịch sử; không diễn giải đó là route
   đang chạy.
3. Không có trip thì routes rỗng và advice silent nếu không có checkpoint; không tạo ID giả.
4. Route cache hiện ở session process; nhiều worker cần shared cache trước deployment thật.

## Expansion checkpoint (T-039)

1. **Schema:** nên khóa JSON Schema cho step envelope trước khi frontend đổi hẳn flow; chưa
   thêm trong cycle để giữ task nhỏ.
2. **Bài toán tối ưu:** không.
3. **Tính năng:** mở projection hai-leg và fallback route; Agent/presentation vẫn ở Task 4.

## Follow-up

- Task 4 thay `advice` reference bằng AdviceCheckpoint lease/template envelope thật.
- Task 5 chuyển Web render atomic từ response này.
