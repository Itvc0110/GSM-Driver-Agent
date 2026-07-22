# UPDATE-021 — Chương trình nâng cấp simulator reliability-first M0–M4 + governance mới

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent (theo yêu cầu và thiết kế được **Cường duyệt**)
- **Loại:** docs / spec / governance / defer
- **TODO / User story liên quan:** T-029 (DONE); tạo follow-up T-030–T-037; remap T-018–T-021/T-026–T-028

## Tóm tắt

Chốt chương trình nâng cấp simulator theo thứ tự **M0 integrity → M1 24h dynamic market → M2 spatial/exogenous world → M3 stakeholder visualization → M4 advisor/twin-runner**, thay cho việc tiếp tục advisor/UI trên nền sim chưa qua integrity gate. Bổ sung harness bắt buộc cho brainstorming+plan mode theo coherent cycle, root-cause debugging, multi-seed verification, adversarial self-review và visual review trước commit/push của meaningful sim/UI update.

Lượt này **chỉ thay đổi tài liệu/governance**. Working diff Stage A–C trong `src/gsm_sim/` và config được bảo toàn nguyên trạng, được coi là **M0 audit input**, không phải code đã chấp nhận hoặc hoàn thành.

## Chi tiết cập nhật

### 1. Master spec M0–M4

Tạo `specs/simulation-reliability-upgrade.md` làm source of truth về phasing, contracts và exit gates:

- `actors.n` = daily actor pool; active supply biến động nội sinh.
- Engine = continuous DES; dispatch tick riêng; observation/replay per-event hoặc bins 1/5/15 phút.
- M1 target `[00:00,24:00)`; 05:00–24:00 giữ làm compatibility pilot.
- H3 dùng cho field/index/candidate shortlist; OSM road/POI lat/lon dùng endpoint/movement/ETA/viz.
- Canonical Driver/Customer/Order/Station/Environment/Decision contracts.
- Evidence labels `[FACT]/[OBSERVED-CODE]/[PROXY]/[MOCK]/[ASSUMPTION]/[UNVERIFIED]`.
- M0 flaw inventory: station battery lifecycle, re-offer loop, unused `hour_interp`, future-information leak, unstable belief, incomplete customer terminal states, end-of-day censoring/time conservation, repeated meal break, charge-home travel, endpoint-distance consistency, atomic H3 position sync, dispatch semantics/tie-break và expired-event regression.
- Acceptance mặc định: deterministic exact repeat; behavior ≥5 seeds; distribution/calibration ≥30 seeds; M4 dùng paired CI protocol.
- Story Mode + Diagnostic Mode và visual-review gate.

### 2. Scope/backlog/deferred

- `planning/SCOPE.md`: thêm §5c reliability-first; product boundaries giữ nguyên.
- `tracking/TODO.md`: reorder track SIM theo M0→M4; thêm T-029–T-037; T-021 chuyển VALIDATING; tách T-020 evaluator khỏi dashboard chung.
- `tracking/DEFERRED.md`: D-010 chuyển `PARTIAL REOPEN`; mở regime/distribution shifts qua T-034/T-027, giữ multi-day trust/full counterfactual/res8-N500/ĐBTN deferred.
- Không sửa `ASSIGNMENTS.md`: agent không tự claim task implementation mới.

### 3. Harness và UPDATE template

`CLAUDE.md` §4b mới yêu cầu:

- brainstorm → plan mode trước coherent implementation cycle;
- debug theo reproduce→classify→baseline→instrument→prove root cause→failing regression→narrow fix→multi-seed/boundary/full-suite→self-review;
- không tune calibration che BUG;
- adversarial check conservation/future leak/CRN/double-count/config/no-op/UI source/evidence;
- meaningful sim/UI update phải mở visualization cho Cường review trước commit/push nếu chưa waive;
- docs-only/test-only/no-output refactor có thể `NOT_APPLICABLE` có lý do.

`UPDATE_TEMPLATE.md` thêm Assumptions/evidence, Seeds/scenarios, Visual verification và Adversarial self-review/flaws.

### 4. Harmonize spec cũ

- `simulation-pilot-world.md`: 05–24 là compatibility profile; M1 target 00–24; 15–20% không phải B-arm integrity target.
- `simulation-twin-world.md`: paired triplet A/B/C; T-018 runner substrate, T-020 evaluator, T-035–T-037 visualization.
- `advisor-optimization-layer-a.md`: M4 sau M0–M3; B-arm gate theo evidence/invariants; no-future-information boundary.
- `environment-variables.md`: status `IMPLEMENTED CORE / PARTIAL`; phần M2 còn thiếu trỏ T-034.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `specs/simulation-reliability-upgrade.md` | tạo | Master spec M0–M4, contracts, flaws, gates |
| `CLAUDE.md` | sửa | §4b workflow/debug/self-review/visual gate |
| `planning/SCOPE.md` | sửa | §5c reliability-first |
| `tracking/TODO.md` | sửa | Reorder + T-029–T-037 + remap tasks |
| `tracking/DEFERRED.md` | sửa | D-010 partial reopen |
| `tracking/updates/UPDATE_TEMPLATE.md` | sửa | Evidence/seeds/visual/adversarial sections |
| `specs/simulation-pilot-world.md` | sửa | Compatibility/full-day + calibration target |
| `specs/simulation-twin-world.md` | sửa | A/B/C ownership/horizon |
| `specs/advisor-optimization-layer-a.md` | sửa | M4/info/calibration boundary |
| `specs/environment-variables.md` | sửa | Implemented core/partial status |
| `tracking/updates/UPDATE-021-simulation-reliability-program.md` | tạo | Update này (đổi số từ 013→021 vì remote đã chiếm UPDATE-019/020 khi tích hợp) |

**Không sửa trong cycle docs:** `configs/pilot_dongda.yaml`, `src/gsm_sim/*.py`, tests/data và `tracking/ASSIGNMENTS.md`.

## Docs đã cập nhật kèm theo

- SCOPE: có (§5c).
- TODO: có (T-029–T-037 và remap).
- DEFERRED: có (D-010).
- USER_STORIES/RESEARCH: không đổi; master spec trỏ research/spec hiện hữu.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Working diff Stage A–C có 9 file tracked + 2 file mới, diffstat 219 insertions/44 deletions tại đầu cycle | `OBSERVED-CODE` | `git status --short`, `git diff --stat -- configs src/gsm_sim tests`, 2026-07-22 | Cao | Nếu diff thay trong cycle, M0 audit snapshot không còn đúng; verification cuối phải phát hiện |
| `actors.n` nên là daily pool, không concurrent active count | `ASSUMPTION` (Cường APPROVED) | Brainstorm 2026-07-22 + persona shift semantics | Cao về design; chưa calibrated | Supply curve/KPI/UI semantics thay đổi ở M1 |
| Full-day target `[00:00,24:00)` tốt hơn pilot 05–24 cho stakeholder market story | `ASSUMPTION` (Cường APPROVED) | Review sim 2026-07-22 | Cao về scope; realism chưa verify | Demand/supply normalization và boundary semantics đổi ở M1 |
| OSM road/POI endpoint đủ cho spatial milestone trước road graph | `ASSUMPTION` (Cường APPROVED) | Brainstorm trade-off 2026-07-22 | Trung bình-cao | Nếu endpoint v1 không đủ, road routing phải mở sớm hơn |
| Demand-correlated congestion là traffic proxy, không phải traffic fact | `PROXY` | `research/market/dispatch-signals-and-external-apis.md` + yêu cầu Cường | Trung bình | Nếu trình bày như fact sẽ overclaim; M2 phải label/attribution/sensitivity |
| 15–20% unserved không phải B-arm integrity invariant | `OBSERVED-CODE` + research conclusion | TODO/T-024 + `research/simulation/realism-benchmarks.md` | Cao | Ép B về target sẽ target-leak và làm sai A/B effect |

## Kiểm chứng

Cycle docs không chạy simulator/test suite vì không thay code/output. Kiểm chứng được thực hiện bằng:

- kiểm tra Markdown/diff whitespace;
- cross-doc grep cho M0–M4, T-029–T-037, B-arm 15–20%, environment status và M3 ownership;
- so sánh trước/sau path list + diffstat của `configs/src/gsm_sim/tests`;
- xác nhận index Git rỗng, không staged file.

Kết quả:

- `git diff --check` → **PASS** (chỉ có cảnh báo LF→CRLF của Git trên Windows, không có whitespace error).
- Consistency scan → **PASS**: không còn wording stale “2 arm/hai thế giới”, T-020 không còn sở hữu dashboard chung, environment không còn status “chưa code”, master spec không có placeholder.
- Backlog scan → **PASS**: đúng 9 task rows T-029–T-037, owner implementation để trống theo self-claim.
- Working-diff preservation → **PASS**: trước/sau đều đúng 9 tracked simulator files, `219 insertions / 44 deletions`, cộng 2 untracked `congestion.py`/`trajectory.py`; Git index rỗng.
- External reviewer subagent → **BLOCKED bởi permission classifier của harness** trước khi chạy (retry 2 lần). Không coi là review pass; inline adversarial self-review đã phát hiện và sửa 5 tham chiếu stale “2 arm” trong `simulation-twin-world.md`.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| Markdown + cross-doc consistency + working-diff preservation | N/A | N/A | PASS; xem bullet phía trên | M0 code/test/visualization chưa chạy trong cycle docs; external subagent review bị harness chặn |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** không launch dashboard vì cycle docs-only, không đổi sim/UI/output.
- **Seed / scenario đã xem:** N/A.
- **Người review + verdict:** Cường sẽ review written spec/backlog/harness; đây không phải UI visual gate.
- **Lý do:** `CLAUDE.md` §4b cho phép docs-only ghi `NOT_APPLICABLE` có lý do. M0/T-030 phải mở diagnostic visualization trước khi hoàn tất.

## Adversarial self-review / flaws found

1. **Có thể trông tốt nhưng sai:** master spec đầy đủ có thể tạo cảm giác sim đã được sửa; thực tế Stage A–C chưa qua M0 gate. Vì vậy spec/TODO/UPDATE đều ghi rõ “audit input, chưa accepted”.
2. **Future leak/CRN/fallback/unit/double-count:** chưa kiểm code trong cycle này; đã đưa thành P0/M2 gates. Congestion từ orders bắt buộc gắn `[PROXY]`, không gọi traffic fact.
3. **Assumption yếu nhất:** OSM endpoint + Haversine×detour có đủ thuyết phục trước road graph hay không (T-032/T-033 gate).
4. **Baseline đã so:** docs lịch sử pilot 05–24 và conclusion T-024; loại trừ phương án tiếp tục T-019 trước integrity vì risk target leakage/future leak.
5. **Flaw còn mở:** toàn bộ P0 → T-030; 24h/dynamic fleet → T-031; OSM/H3/congestion/shifts → T-032–T-034; visualization → T-035–T-037; advisor/twin → T-019/T-026/T-020; robustness → T-027.
6. **Rủi ro operational:** vô tình stage/commit working diff Stage A–C cùng docs. Cycle này không stage/commit; nếu Cường yêu cầu commit sau, chỉ stage allowlist docs bằng path cụ thể.

## Follow-up / defer phát sinh

- **T-030 (READY):** M0 audit/prove root cause/invariants cho Stage A–C; phải self-claim và vào plan mode mới trước implement.
- **T-031–T-037 (BLOCKED):** M1–M3 theo dependencies trong TODO/master spec.
- **M4:** T-019/T-026/T-020 sau M0–M3 gates.
- **D-010:** partial reopen như DEFERRED; phần multi-day/scale/counterfactual vẫn hoãn.
- Dừng sau user review written spec/backlog/harness; không tự bắt đầu T-030.
