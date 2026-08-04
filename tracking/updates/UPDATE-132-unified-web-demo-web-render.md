# UPDATE-132 — Web render canonical replay + displayed ACK

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / VISUAL BLOCKED`
- **TODO:** `WEB-DEMO-UNIFIED`

## Kết quả

`/app/` đã chuyển sang server-owned observer replay:

```text
POST /api/v1/demo/sessions
→ actor picker từ backend
→ PUT .../driver
→ POST .../steps (client_step_id + expected_step_version)
→ render canonical driver/trip/map/routes/advice/timeline
```

Browser không còn gọi `/api/v1/trip/step`, giữ `tripStep`, dựng quote/cuốc hoặc tự tính
SOC/payout. Route geometry và leg (`driver_to_pickup`, `pickup_to_destination`) chỉ được
render từ response của session; fallback geometry được đánh dấu rõ.

Advice card được dựng bằng DOM nodes/textContent cho toàn bộ `title/summary/why/numbers`;
không dùng raw `innerHTML` cho model-owned text. Sau khi card mount, Web gửi mounted ACK qua
demo-scoped endpoint dùng cùng checkpoint lease/event store. Buttons chỉ ghi
`accepted|dismissed|expanded` UI intent; không làm trajectory branch.

Demo session có endpoint ACK riêng vì `ADVICE_V2_ENABLED=0` vẫn phải là rollback an toàn cho
product polling API, trong khi internal replay template có thể chứng minh `displayed` trên
cùng checkpoint stream. `ADVICE_PRESENTATION_MODE=template` vẫn là mặc định.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `ui/web/js/api.js` | sửa | demo session/step/ACK client calls + PUT helper |
| `ui/web/js/app.js` | sửa | canonical replay render, actor picker, Next Step, safe advice DOM/ACK |
| `ui/web/index.html` | sửa | unified replay panel; bỏ hard-coded trip controls khỏi flow |
| `ui/contracts/advice_v2.json` | sửa | cho phép provenance của presentation source (`template|agent`) |
| `ui/backend/app/services/demo_session.py` | sửa | observer-only trace run config/cache và demo ACK/response bridge |
| `ui/backend/app/routers/demo.py` | sửa | demo-scoped display/response endpoints |
| `ui/backend/tests/test_demo_advice_ack.py` | tạo | mounted ACK/response idempotency và shared lease |
| `ui/web/tests/unified-demo.mjs` | tạo | endpoint calls, no client cursor/legacy trip path, DOM IDs |

## Evidence

| Claim | Nhãn | Evidence | Confidence |
|---|---|---|---|
| Client cursor/hard-coded trip path is removed from `/app/` | `OBSERVED-CODE` | `unified-demo.mjs` source guard; `app.js` has no `tripStep`, `demoTrips`, `api.tripStep`, or `innerHTML` | cao |
| Next Step is retry-safe and server-owned | `FACT` | `DemoSessionService.advance()` + API contract tests from UPDATE-129 | cao |
| Agent-owned advice text is not inserted as HTML | `OBSERVED-CODE` | `renderDemoAdvice()` creates nodes and assigns `textContent` | cao |
| Displayed event is recorded when v2 product flag is off | `OBSERVED-CODE` | `/api/v1/demo/.../display` calls shared `AdviceCheckpointService`/`CheckpointStore`; focused ACK test | cao |
| Browser visual parity and live OSRM latency | `UNVERIFIED` | no browser/emulator visual run in this environment | thấp |

## Kiểm chứng

- `node ui/web/tests/unified-demo.mjs` → **PASS**.
- `node ui/web/tests/advice-v2.mjs` → **PASS**.
- `node ui/web/tests/demo-pricing.mjs` → **PASS**.
- `.venv/bin/python -m pytest -q tests/test_checkpoint_presenter.py ui/backend/tests/test_demo_advice_bridge.py ui/backend/tests/test_demo_advice_ack.py ui/backend/tests/test_demo_step_contract.py ui/backend/tests/test_demo_session_api.py` → **23 passed**, 1 Starlette deprecation warning.
- `node --check ui/web/js/app.js ui/web/js/api.js` → **PASS**.
- Không chạy full backend/simulator/solver theo chỉ thị.

## Visual verification

- **Status:** `BLOCKED` — cần mở `/app/` bằng browser và xem replay với OSRM/fallback, actor
  picker, card provenance và ACK event. Đây là human visual gate, không được suy ra từ Node test.

## Adversarial self-review / flaws found

1. Default demo run enables existing S1/S2 capture callsites in a deep-copied config with
   zero adherence and positioning override off. This is an observer fixture, not a production
   advice arm; simulator dynamics must receive a dedicated semantic comparator before rollout.
2. In-process session/route cache is suitable for one-process demo only; multi-worker hosting
   requires shared session/idempotency storage before any canary.
3. The demo ACK endpoint is intentionally internal and not a replacement for `/api/v2/advice`;
   v2 flag/authorization/product rollout remains unchanged.

## Expansion checkpoint (T-039)

1. **Schema:** next cycle should add a closed JSON Schema for the canonical demo step envelope;
   current focused tests assert required fields but do not validate every nested property.
2. **Bài toán tối ưu:** không phát sinh; Next Step never re-solves.
3. **Tính năng:** Web can now compare template versus future shadow artifacts on the same trace;
   no live Agent was enabled.

## Follow-up

- Run human V-25 visual review and a narrow end-to-end smoke with one cached run.
- Add closed demo-step schema/replay evidence only if owner accepts the contract surface.
- Keep v2 disabled/template defaults and rollback by disabling the unified demo route if needed.
