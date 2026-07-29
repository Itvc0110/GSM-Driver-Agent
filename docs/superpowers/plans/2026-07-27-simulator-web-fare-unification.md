> ✅ **ACTIVE — thuộc UI-FARE-01 (UPDATE-073, chờ verdict V-16); KHÔNG thuộc pack DEFERRED D-001.**

# Simulator/Web Fare Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` and `superpowers:test-driven-development`. Do not touch `ui/driver_app/`.

**Goal:** Đồng nhất cơ chế tính gross fare và trip payout của cuốc demo Web với `gsm_sim.PolicyBundle`, giữ demo tách khỏi ledger.

**Architecture:** Simulator policy/config tiếp tục là nguồn duy nhất. UI backend dùng adapter mỏng để quote theo route distance; Web chỉ render response và không tính tiền.

**Tech stack:** Python 3.11+, FastAPI/Pydantic, pytest, vanilla ES modules.

## Global constraints

- Không hard-code fare/share trong backend hoặc JavaScript.
- `fare_vnd` là gross; `driver_payout_vnd` chưa gồm bonus.
- Mọi output là MOCK/synthetic và có policy version.
- Không sửa Flutter hoặc legacy Stitch HTML.
- V-11 phải được ghi nhận trung thực; user đã trực tiếp cho phép commit/push main dù verdict người dùng còn pending.

### Task 1: Regression contract

**Files:** `ui/backend/tests/test_demo_pricing.py`, `ui/backend/tests/test_routing_api.py`, `ui/backend/tests/test_api.py`.

- [x] Viết test boundary 2 km/3,5 km/distance âm và policy provenance.
- [x] Viết deterministic OSRM fixture và forced-fallback tests.
- [x] Viết test `/trip/step` trả fare null.
- [x] Chạy focused tests và xác nhận RED đúng vì adapter/fields chưa tồn tại.

### Task 2: Canonical pricing backend

**Files:** tạo `ui/backend/app/adapters/sim_pricing.py`; sửa `models.py`, `routers/routing.py`, `simulator.py`.

- [x] Cài adapter gọi `gsm_sim.PolicyBundle` từ config hiện hành.
- [x] Thay cả hai fare branch bằng quote canonical.
- [x] Mở rộng response additive và bỏ fare tĩnh khỏi trip fixtures.
- [x] Chạy focused tests tới GREEN.

### Task 3: Web presentation

**Files:** `ui/web/index.html`, `ui/web/js/app.js`.

- [x] Hiện gross, payout, version và MOCK ở incoming/active.
- [x] Lưu gross/payout/distance/route-source/version trong history.
- [x] Giữ `S.state.money` read-only trong trip lifecycle.
- [x] Chạy `node --check` và manual/static ledger review.

### Task 4: Tracking and verification

**Files:** UPDATE-073, TODO, PROJECT-GRAPH, DEFERRED, PENDING-REVIEW, UI docs.

- [x] Ghi before/after, evidence, assumptions, adversarial review và test output.
- [x] Đăng ký UI-FARE-01, graph node, D-POL-06 và V-11.
- [x] Chạy focused suites, UI suite, root full suite và `git diff --check`.
- [x] Launch Web UI và ghi V-11 technical evidence; user-authorized commit/push main, human verdict tiếp tục pending.
