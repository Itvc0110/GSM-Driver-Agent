# UPDATE-126 — AdviceCheckpoint P2–P5 hoàn tất code, chờ V-25

- **Ngày:** 2026-08-03
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Trạng thái:** `DONE-CODE / V-25 BLOCKED`
- **Loại:** schema / lifecycle / simulator / API / Web / Flutter / agent shadow
- **TODO:** `CKPT-B/C/D`, `CKPT-P1..P5`, `CKPT-MIG`, `T-039`

## Kết quả

Đã hoàn thiện đường AdviceCheckpoint P2–P5 theo kiến trúc UPDATE-124: checkpoint có
event stream riêng, không mở rộng hay dual-write lifecycle legacy, không overload/backfill
`decision_id`. Runtime sản phẩm mặc định template-only và API v2 mặc định tắt. Agent chỉ
chạy shadow nội bộ, output chỉ lưu artifact đánh giá và không thể thay canonical
action/window/numbers hoặc lifecycle tài xế.

`DONE-CODE` không đồng nghĩa production-ready: product S2 mặc định fail-closed vì chưa có
provider SOC/rest thật; live LLM/canary nằm ngoài scope; V-25 còn chờ Flutter SDK + human
review trên emulator/device.

## P0/P1 — contract, policy và store

- V1 chỉ chấp nhận `brief|nudge|recap`, reject `safety` và topic lạ. Driving luôn queue.
  Sim router dùng allowlist driver-facing nên `advice_rest_veto` không thành card. Silent
  response mang đủ `scenario_id`, `seed`, `data_mode`, `is_mock` và closed reason enum.
- `advice_artifact`, `advice_checkpoint`, `advice_checkpoint_event` lên 1.1.0, giữ snapshot
  1.0.0 và pure upcaster. Checkpoint có source decision/run/input/report refs; `expanded`
  và `execution_observed` là side-channel, không đổi presentation state.
- Pure normalizer/policy đóng taxonomy/action, validity S1/S2/S4/S7, fingerprint/dedup,
  material supersede, driving queue, cooldown/budget và deterministic primary selection.
- SQLite `create_checkpoint_bundle()` commit artifact/checkpoint/`created` cùng transaction;
  conflicting retry fail-loud. Simulator dùng RAM journal có cùng validation/projection.
- `CKPT-MIG` là `RESOLVED-BY-DESIGN`: `source_decision_id` chỉ là reference legacy;
  `checkpoint_id` giữ identity riêng. Q-13 và V-21 vẫn mở.

## P2 — simulator traceability

- Capture được gắn sau callsite hiện hữu của S1, S2, S4, S7 và shift-extension; không thêm
  solver invocation, trigger hay RNG draw. Snapshot bỏ raw coordinate/PII và giữ state audit,
  exact solver input/report, source decision ID và refs content-addressed.
- Tick loop chỉ append RAM. `RunResult` mang artifacts/checkpoints/events/pending execution;
  post-run export bốn JSONL với count/digest manifest.
- Segment ID deterministic từ run/actor/content/ordinal. Execution link tách identity và
  mặc định `coincident`; `accepted` không tự sinh execution và execution không tự sinh intent.
- Metrics báo riêng volume/dedup/queue/expiry/supersede, decision/event adherence,
  accept/execution rate và relation/confidence. Không bịa retained impact khi schema hiện
  không có số đó.
- Comparator `checkpoint_shadow.enabled=false|true` trên seed 1000–1004: `IDENTICAL` 5/5
  cho order outcomes, terminal state, payout, SOC, trips và segment kind/time/order.

## P3 — product S1/S2, lease, API và UI

- `ProductDriverRuntimeState` chỉ nhận state `REAL|LIVE` còn fresh và đã observed. Missing,
  stale, malformed hoặc future-observed state đều trả `missing_state` và không gọi S2;
  `_soc_proxy` không được import. Trusted fixture chứng minh ONLINE-now/SWAP-future.
- S1/S2 fail-isolated; `solver_set` chỉ có solver thành công. S4 vẫn simulator-only.
- Lease immutable: insert lease và `offered` trong cùng `BEGIN IMMEDIATE`; concurrent/retry
  GET dùng cùng `display_id` và budget chỉ tiêu một lần. Display chỉ được ghi sau mounted ACK;
  client event retry idempotent; missing 404, stale/transition 409, invalid body/query 422.
- `GET /api/v2/advice` nhận surface + runtime query đóng, tối đa một card. Silent envelope
  không có checkpoint/display/buttons. `ADVICE_V2_ENABLED=0` là mặc định và Web fallback v1.
- Web ACK sau DOM mount; Flutter ACK trong post-frame callback. Hai client đọc canonical
  action/window/numbers/provenance từ server, không tính lại SOC/action/message. Flutter giữ
  provenance-aware empty state và badge MOCK/PROXY.
- Mốc metric: v2 `displayed` là mounted ACK, không so trực tiếp với legacy `displayed`.

## P4/P5 — presenter, verifier và shadow runtime

- Contract đóng `agent_presentation_input/output@1.0.0`; agent output chỉ có reason/why
  template và used fact/number/caveat IDs. Không có action/window/expiry/source/free number.
- `CheckpointPresenter` side-effect-free và không import store/EpisodeStore. Template render
  canonical content; checkpoint orchestration không gọi legacy `AdvisorPipeline._finish()`.
- Verifier veto malformed/extra JSON, checkpoint mismatch, unknown IDs, bare digits,
  conflicting action, trip-specific advice, income promise, urgency drift, CJK, overlength
  và provider error; tối đa một repair rồi deterministic template fallback.
- `presentation_mode=template|shadow`, default `template`. Shadow card gửi tài xế vẫn là
  template; model result chỉ lưu `agent_shadow_output`. Revalidate sau model; terminal/expired
  ghi `discarded_stale`, không lease/cache.
- Cache key gồm checkpoint fingerprint, facts digest, locale, prompt/model/policy version;
  TTL không vượt validity. SQLite transient claim giữ một owner/key. Simulator method D chạy
  presenter post-run trên trajectory cố định và cho phép nhiều presenter dùng cùng artifacts.
- SQLite telemetry append-only ghi cache hit, avoided call, stale discard, fallback, latency,
  input/output tokens và cost USD; token/cost để `null` khi provider không cung cấp, không bịa.
  Chưa có provider live; live/canary/kill-switch là P6.

## Verification tươi

| Gate | Kết quả |
| --- | --- |
| `.venv/bin/python -m pytest -q` | **978 passed, 4 skipped**, 1137.52s (full completion run trước hardening `window_conflict` cô lập cuối) |
| `.venv/bin/python -m pytest -q ui/backend/tests` (ngoài sandbox do AnyIO portal) | **84 passed**, 1 Starlette deprecation warning, 11.80s |
| Focused checkpoint/schema/presenter | **70 passed**, 6.51s |
| Focused product/service sau future-state fix | **21 passed**, 0.50s |
| Health money boundary | **12 passed**, 2.74s |
| Final focused presenter/health/checkpoint/trace/schema/product service | **92 passed**, 9.85s (sau hardening + telemetry cuối) |
| Web `demo-pricing.mjs` + `advice-v2.mjs` | PASS |
| Python compile + `git diff --check` | PASS |
| Comparator seed 1000–1004 | **IDENTICAL 5/5** |
| `flutter analyze`, `flutter test` | **BLOCKED — không có Flutter/Dart SDK** |

`uv` không có trong environment. Bootstrap từ `uv.lock` đã thử nhưng mạng bị proxy/SSL
chặn, nên verification dùng interpreter hiện hữu `.venv/bin/python`. Backend TestClient
được chạy ngoài sandbox vì AnyIO portal treo dưới sandbox; lần này suite hoàn tất, không chỉ
collect.

## Adversarial review

1. **Lifecycle:** lease/offered atomic; HTTP rớt trước ACK không sinh `displayed`; expanded
   và execution side-channel không đổi state; terminal transition và conflicting idempotency
   retry đều fail-loud.
2. **Time/future leak:** validity/freshness fail-closed; review cuối tái tạo state có
   `observed_at` tương lai nhưng deadline hợp lệ, thêm regression đỏ rồi chặn trước S2.
3. **Money/SOC/order:** presenter chỉ format số đã registry; health scanner phân loại verifier
   là `NOT_MONEY`; comparator pin payout/SOC/trips/order/segments identical 5/5.
4. **CRN/RNG:** trace sink và segment annotation không draw RNG, presenter chỉ post-run.
5. **Fallback:** S2 không dùng proxy; template luôn driver-facing; model timeout/error/stale
   không đổi response. Feature flag và presentation mode giữ rollback rõ.
6. **Canonical UI:** Web/Flutter không chọn giữa candidates và không suy ra action/SOC;
   silent không có fake ID/nút. Shadow marker có test chứng minh không xuất hiện trong body.
7. **Identity/measurement:** decision/checkpoint/display/segment/execution IDs không trộn;
   decision/event adherence, accept/execution rate báo riêng. Q-13 không tự đóng.

## Visual verification — V-25

- **Status:** `BLOCKED`, chưa `REVIEWED`.
- Backend/Web automation đã bao phủ đủ tám semantics: empty, S1 mock card, S2 missing state,
  driving queue, refresh lease reuse, mounted ACK once, accepted≠execution, shadow absent UI.
- Chưa launch Flutter emulator/device vì cả `flutter` và `dart` đều vắng. Cần human review
  canonical action/window/numbers/provenance, badge và empty/silent states trước rollout.
- Repo vẫn giữ `ADVICE_V2_ENABLED=0`; deployment chỉ được bật ở demo đã duyệt.

## T-039 expansion checkpoint

1. **Schema:** 1.1 đã đủ trace/checkpoint/shadow hiện tại. Không thêm field retained impact
   khi chưa có định nghĩa/source; nếu owner duyệt metric này sẽ cần field typed + unit/source,
   không nhúng số tự do vào checkpoint.
2. **Bài toán tối ưu:** không phát sinh solver mới. Residual hiện tại là true-state provider
   cho S2, thuộc ingestion/runtime integration chứ không phải bài toán tối ưu mới.
3. **Tính năng khả thi:** có thể dựng audit UI checkpoint→lease→intent→execution từ data hiện
   có, nhưng chưa tự triển khai; live agent/canary chỉ mở qua P6 với budget/provider/kill-switch.

## Handoff

- `DONE-CODE`: P0–P5 và automated gates nêu trên.
- `WAITING-VERDICT/BLOCKED`: V-25 Flutter/device; không production-ready.
- `OPEN`: Q-13, V-21, P6/live provider/canary. Cadence vẫn 20 phút/topic và 6 proactive/ca.
- Đã tách thành các commit local theo từng lớp thay đổi; push lên remote và mở PR vào `main`
  là bước bàn giao tiếp theo. Worktree vốn bẩn; thay đổi không liên quan được bảo toàn.
- Subagent: **0**. Runtime không cung cấp `gpt-5.6-luna`, nên cap hạ còn 1 và triển khai local.
