# UPDATE-124 — AdviceCheckpoint: sửa F2, safety cadence và nền shadow lifecycle

- **Ngày:** 2026-08-03
- **Người thực hiện:** AI agent theo yêu cầu của người dùng; không thay đổi scope đang claim của Cường tại `ui/backend`
- **Loại:** feature / fix / schema / ui
- **TODO / User story liên quan:** `BUG-F2-NOW`, `CKPT-A`, `CKPT-B`, `CKPT-E`, `CKPT-P1`, `T-039`

## Tóm tắt

Đã sửa F2 để phân biệt hành động hiện tại (`schedule[0]`) với bước tương lai (`next_action`), chặn card text safety khi tài xế đang lái, và gỡ recommendation hard-code khỏi Flutter. Đồng thời bổ sung nền AdviceCheckpoint shadow: schema đóng, projection lifecycle thuần, validity normalizer, fingerprint/dedup và SQLite append-only store riêng, không thay đổi runtime consumer hay overload `decision_id` legacy.

## Chi tiết cập nhật

- F2 render `Bây giờ` từ `schedule[0]`; `next_action` chỉ xuất hiện trong `Sắp tới`. Context pack/prompt cũng pin semantics này. Report legacy không có `schedule` vẫn fallback tương thích.
- Cadence xét `is_driving` trước safety: card text safety khi đang lái trả `QUEUE/unsafe_while_moving`; safety server-created khi đứng yên vẫn được ưu tiên trước dismiss/cooldown/budget. Emergency modality chưa tồn tại nên không tự tạo bypass mới.
- Flutter không còn hiển thị SOC, trạm, zone hoặc uplift hard-code; thay bằng empty state chỉ chờ AdviceCheckpoint có provenance từ backend.
- AdviceCheckpoint dùng event stream/store riêng trong SQLite: artifact content-addressed, checkpoint immutable, event append-only, replay deterministic, terminal state không được regression và `execution_observed` là side-channel độc lập với `accepted`.
- `checkpoint_id`, `display_id`, `segment_id` và `execution_link_id` không thay thế `decision_id`. Chưa có runtime producer/consumer, legacy adapter hoặc agent live.
- API topic enum/server-owned priority và các thay đổi tại `ui/backend` không thực hiện trong cycle này vì path đang thuộc claim Cường; CKPT-B vì vậy chỉ hoàn tất phần cadence core.

## Files bị ảnh hưởng

| File | Hành động (tạo/sửa/xóa) | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/advisor/templates.py` | sửa | F2 current/future action rendering |
| `src/gsm_core/advisor/context_pack.py` | sửa | prompt/context semantics cho F2 |
| `src/gsm_core/lifecycle/cadence.py` | sửa | driving queue trước safety priority |
| `tests/test_advisor_pipeline.py` | sửa | regression ONLINE-now/SWAP-future |
| `tests/test_cadence_policy.py` | sửa | safety khi driving phải queue |
| `ui/driver_app/lib/screens/home_screen.dart` | sửa | bỏ fake recommendation, provenance-aware empty state |
| `src/gsm_core/lifecycle/checkpoint.py` | tạo | pure lifecycle, normalizer, fingerprint, policy helpers |
| `src/gsm_core/lifecycle/checkpoint_store.py` | tạo | SQLite append-only shadow store |
| `schemas/advisor/advice_artifact.schema.json` | tạo | immutable artifact contract 1.0.0 |
| `schemas/advisor/advice_checkpoint.schema.json` | tạo | checkpoint contract 1.0.0 |
| `schemas/advisor/advice_checkpoint_event.schema.json` | tạo | lifecycle event contract 1.0.0 |
| `src/gsm_core/schema_registry.py` | sửa | đăng ký ba advisor entities |
| `tests/test_advice_checkpoint.py` | tạo | replay, transition, validity, dedup, store/idempotency tests |
| `tests/test_schemas.py` | sửa | registry coverage |
| `schemas/README.md`, `schemas/CHANGELOG.md` | sửa | ghi rõ shadow contract, không dual-write legacy |
| `tracking/TODO.md` | sửa | cập nhật CKPT-A/B/E/P1 và BUG-F2-NOW |
| `tracking/PROJECT-GRAPH.md`, `tracking/PENDING-REVIEW.md` | sửa | nối UPDATE-124 và đăng ký visual gate V-25 |

## Docs đã cập nhật kèm theo

Đã cập nhật `tracking/TODO.md`, `tracking/PROJECT-GRAPH.md`, `tracking/PENDING-REVIEW.md`, `schemas/README.md`, `schemas/CHANGELOG.md`. `SCOPE.md` không đổi; `CKPT-C`, `CKPT-D`, backend API v2, simulator traceability và visual verdict được giữ làm follow-up.

## Assumptions và evidence

| Claim / tham số | Nhãn (`FACT` / `OBSERVED-CODE` / `PROXY` / `MOCK` / `ASSUMPTION` / `UNVERIFIED`) | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| F2 có thể có `schedule[0]` khác `next_action` | `OBSERVED-CODE` | solver/template/context hiện hữu và regression test mới | cao | UI nói nhầm hành động hiện tại |
| Text card safety khi đang lái phải queue | `DECISION` | plan AdviceCheckpoint; cadence chưa có emergency modality | cao | nếu sai sẽ ảnh hưởng safety presentation |
| Checkpoint lifecycle tách khỏi adherence lifecycle legacy | `DECISION` | kiến trúc đã chọn trong plan, schema/store riêng | cao | tránh migration/backfill sai `decision_id` |
| Artifact/checkpoint data trong test | `MOCK` | fixtures `data_mode=synthetic`, `is_mock=true` | cao | không được dùng để claim production uplift |
| API topic do server sở hữu | `ASSUMPTION / UNVERIFIED` | plan và B-03; backend chưa sửa trong cycle | trung bình | CKPT-B còn partial, client vẫn cần backend gate |
| Flutter empty state đã qua visual review | `UNVERIFIED` | Flutter/Dart SDK không có trong environment; chỉ static inspection | thấp | cần visual gate trước khi đóng UI |

## Kiểm chứng

- `.venv/bin/python -m pytest -q`: **948 passed, 4 skipped** (1141.18s).
- `.venv/bin/python -m pytest -q tests/test_advice_checkpoint.py`: **12 passed** sau khi thêm guard cho conflicting idempotency retry và fallback sau `generation_failed`.
- Root suite ở trên bao phủ focused advisor/cadence/lifecycle/schema/checkpoint regression cuối cùng.
- `git diff --check`: không có whitespace error.
- `rg` xác nhận Flutter không còn các chuỗi fake `Vincom`, `Đồng Khởi`, `Q.1`, `H3 zone đỏ`, `SOC hiện tại`, `35%`, `22%`.
- `--collect-only -q ui/backend/tests`: **66 tests collected**. Full backend suite và cả TestClient smoke bị treo trong anyio portal trước khi vào handler trong environment hiện tại; chưa coi backend suite là pass. `uv` cũng không có trong environment nên dùng `.venv/bin/python` tương đương để chạy pytest.
- Chưa chạy visual review vì không có `flutter`/`dart`; không claim mobile UI parity.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| root pytest | không áp dụng | unit/integration fixtures hiện hữu | 946 pass, 4 skip | backend runtime suite |
| checkpoint tests | không áp dụng | F2-like shift plan, S1/S2/S4/S7 validity, lifecycle happy/invalid paths | deterministic replay và append/idempotency pass | simulator shadow chưa nối |
| Flutter static scan | không áp dụng | source scan | fake card constants không còn | visual rendering |

## Visual verification

- **Status:** `BLOCKED`
- **Cách launch / artifact:** không thể launch; `flutter` và `dart` không được cài trong environment.
- **Seed / scenario đã xem:** không áp dụng; đã static-inspect empty state.
- **Người review + verdict:** chưa có human visual verdict.
- **Lý do:** cần một environment có Flutter SDK và claim owner `ui/driver_app` review mobile-first trước khi chuyển CKPT-E từ `DONE-CODE / visual WAITING-VERDICT`.

## Adversarial self-review / flaws found

1. F2 regression được kiểm tra với ONLINE hiện tại và SWAP tương lai; `next_action` không còn được dùng để nói “bây giờ”.
2. Projection reject event sau terminal, yêu cầu `created` trước, dedup event ID cùng payload và reject conflicting retry; execution không tự biến thành accepted.
3. Fingerprint bỏ poll message, solver invocation ID và presentation metadata; không dùng model output để làm identity.
4. Không có trigger/solver call mới, không trộn synthetic/live và không có số uplift production trong cycle.
5. Rủi ro còn mở: backend vẫn phải sở hữu topic/priority, sim vẫn chưa có `segment_id` link, và UI chưa visual-reviewed. Các ranh giới này map vào CKPT-C/D/P2/P3 và B-03.

## Expansion checkpoint (T-039 — bắt buộc sau mỗi phần hoàn thành)

1. **Schema:** ba entity shadow mới đã được đăng ký; khi nối runtime cần bổ sung traceability cho snapshot/solver report thật và compatibility test với legacy projection.
2. **Bài toán tối ưu:** không phát sinh solver mới; normalizer chỉ chuẩn hóa output solver hiện hữu.
3. **Tính năng:** sau P2/P3 có thể dựng trace UI `checkpoint → display → intent → execution`, nhưng chưa được bật từ cycle này.

## Follow-up / defer phát sinh

| ID | Việc mới | Điều kiện mở |
| --- | --- | --- |
| `CKPT-C` / `CKPT-D` | sim event allowlist và response contract | claim/backend owner Cường |
| `CKPT-P2` | capture snapshot/solver artifact, deterministic segment/execution link | checkpoint shadow contract ổn định |
| `CKPT-P3` | backend v2 lease, offered/displayed ACK, template-only UI | backend TestClient/runtime environment xanh |
| `CKPT-P4` | structured agent I/O + verifier trước khi nối agent | P1 contract được review |
| `V-25` | visual verdict cho Flutter empty state | Flutter SDK + human review |
