# UPDATE-147 — Nền móng AdviceCheckpoint: validity thật, facts trên record, attach an toàn, queued có dấu vết

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent dưới quyền Khánh (yêu cầu trực tiếp trong hội thoại: hoàn thành vòng Verify → Design → Implement → Test → Measure → Self-review từ discovery UPDATE-146)
- **Loại:** code + schema (1.1.0 → 1.2.0) + tests
- **Trạng thái:** `DONE-CODE / WAITING-VERDICT` (visual gate chưa chạy browser — xem §Visual)
- **Không đổi:** cadence baseline (20′/6 ca), kênh ĐA-07, `silent_maintenance`, canonical action, simulator dynamics (comparator IDENTICAL 5/5), LLM flags (vẫn OFF)

## 1. Root-cause đã xác minh (GĐ1 — mọi số tái lập trong session)

| # | Root-cause | Nhãn | Bằng chứng |
|---|---|---|---|
| R1 | `checkpoint_trace.actor_snapshot` bịa `freshness_deadline = now+1′` ⇒ `normalize_validity` min() luôn bị che ⇒ 100% checkpoint sim sống đúng 1 phút ⇒ **34/86 card-lượt seed 1000 chết `expired` tại presentation (~40%)** | FACT | `checkpoint_trace.py:63` cũ + funnel BEFORE `funnel-seed1000.json` |
| R2 | Fingerprint material không chứa future head + `material_revision` luôn `"1"` ⇒ mọi revision plan bị nén thành 1 record (S2 consult ~mỗi 30′ suốt ca → đọng 1 ONLINE/ca) | OBSERVED-CODE + FACT | `checkpoint.py:293-314` cũ; 2.013 lời solver/seed → 176 record |
| R3 | `normalize` chỉ đọc 6 key; `numbers[]`/`caveats[]` bị vứt; `checkpoint_record` strip `fingerprint` ⇒ card nghèo facts + dedup product không bao giờ khớp record đã persist | OBSERVED-CODE | `checkpoint.py:145-231, 74-88` cũ |
| R4 | `action_window = None` trên 100% record (chỉ RULE emit; schedule bucket labels bị bỏ) ⇒ card "trong cửa sổ được đề xuất" không có cửa sổ | FACT | timeline JSON 2 bộ seed |
| R5 | Demo attach gắn mù vào event đầu tiên sau bucket — không xét moving/validity ⇒ 12 card mất vĩnh viễn vì moving-at-attach; moving gate demo trả silent **không event** ⇒ không phân biệt "im vì lái" với "mất" | FACT + OBSERVED-CODE | funnel BEFORE; `demo_trace.py:234-243` cũ; `advice_checkpoint.py:406-407` cũ |
| R6 | Máy trạng thái thiếu `ready→queued`; nhánh resume `queued→ready` phía product có sẵn nhưng không bao giờ chạy vì không ai ghi queued | OBSERVED-CODE | `checkpoint.py:31-32` cũ; `advice_checkpoint.py:322` |
| R7 | (Phát hiện khi bump schema) `_created_event`/`offered` event stamp `checkpoint.get("schema_version")` ⇒ record 1.2.0 sẽ làm event validate FAIL | OBSERVED-CODE | `checkpoint_store.py:45,263` cũ |

**Nhận định cũ đúng/sai:** UPDATE-144/136/137 đúng ở mọi con số đã kiểm (864/413/450/1 tái lập chính xác; ONLINE maintenance là policy đúng — GIỮ im lặng). Điểm 137 nói "attach loss ~1,2% là đuôi nhỏ" — đúng nhưng chưa đủ: lớp mất lớn nhất (expired-tại-presentation ~40%) chỉ lộ ra khi đo funnel; lượt này xác nhận và sửa tận gốc.

## 2. Thiết kế được chọn (GĐ2) và vì sao

So 3 hướng: (a) vá tại presentation (nới revalidation) — bác vì che sự thật validity; (b) sửa policy/cadence để demo nhiều card — bác vì phạm ranh giới (không đổi cadence, không unsuppress); **(c) sửa ĐƯỜNG DỮ LIỆU tận producer/normalize + association + observability** — chọn, vì mọi lớp trên (policy, presentation, product, demo) đều hưởng, không đổi hành vi solver/policy, rollback bằng revert, đo được bằng comparator + funnel.

Các quyết định kỹ thuật tự chốt (suy được từ code, có giải thích trong comment):
- freshness thật = chu kỳ consult của kênh (`interval_min`; S4 = bucket planner) — đó là chu kỳ dữ liệu được làm tươi thật sự;
- window bucket suy từ CHÍNH nhãn schedule của solver (hiệu 2 nhãn liên tiếp; 1 nhãn thì dùng `bucket_end` hint) — không bịa hằng số;
- fingerprint thêm `future_head` (code+window của hành động kế) — đủ phân biệt revision material, không nổ theo đuôi lịch;
- attach ưu tiên transition AN TOÀN đầu tiên TRONG validity; di chuyển suốt validity thì vẫn gắn vào transition đầu để `queued` có dấu vết; hết validity trước mọi transition ⇒ audit `expired_before_transition`;
- `ready→queued` mở trong transition matrix; demo present ghi `queued` khi đang lái và resume `queued→ready` khi an toàn (mirror đường product).

## 3. Thay đổi đã triển khai

| File | Thay đổi |
|---|---|
| `schemas/advisor/advice_checkpoint.schema.json` | 1.1.0 → **1.2.0**: thêm `numbers[]`, `caveats[]`, `fingerprint` (required) |
| `schemas/advisor/advice_checkpoint@1.1.0.schema.json` | snapshot version cũ (mới tạo) |
| `schemas/CHANGELOG.md` | entry 2026-08-05 |
| `src/gsm_core/upcasters.py` | upcaster `advice_checkpoint` 1.1.0→1.2.0 (numbers/caveats rỗng — không bịa; fingerprint tái lập bằng hàm production) |
| `src/gsm_core/lifecycle/checkpoint.py` | `ready→queued`; record 1.2.0 + 3 field mới; normalize: numbers/caveats passthrough, action_window + future windows từ bucket labels (`_schedule_step_minutes`/`_plan_window`), validity hint fallback từ snapshot; fingerprint + `future_head` |
| `src/gsm_core/lifecycle/checkpoint_store.py` | created/offered event stamp cố định version của EVENT entity (1.1.0) |
| `src/gsm_sim/checkpoint_trace.py` | `actor_snapshot`/`capture` nhận `validity_hints` (freshness/bucket_end/rest_window_end/allocation_bucket_end theo phút sim); fallback +1′ chỉ còn cho fixture cũ |
| `src/gsm_sim/advice_bridge.py` | `_capture_checkpoint` mặc định freshness = `now + interval_min`; S2 truyền `bucket_end_min` (lưới floor theo `bucket_min`); S7 truyền `rest_window_end_min = (hour+1)·60` |
| `src/gsm_sim/world.py` | callsite S4 truyền freshness/allocation_bucket_end = `now + bucket_min` (không đụng dynamics — chỉ tham số capture observer) |
| `src/gsm_sim/demo_trace.py` | attach an toàn trong validity + audit `expired_before_transition` |
| `ui/backend/app/services/advice_checkpoint.py` | moving gate ghi event `queued` + resume `queued→ready`; `_presentation_inputs` ưu tiên numbers/caveats trên record (fallback artifact cho record 1.1.0); template_version đọc từ registry |
| `src/gsm_core/advisor/checkpoint_templates.py` | **v2**: SWAP/REST render "trong khung HH:MM–HH:MM" từ `action_window` thật (không window giữ wording cũ) |
| `ui/contracts/advice_v2.json` | `provenance.checkpoint_schema_version` enum {1.1.0, 1.2.0} |

## 4. Tests

- **Mới:** `tests/test_checkpoint_enrichment.py` (13 test — validity hints, window synthesis, không bịa window khi thiếu label, numbers/caveats/fingerprint trên record, fingerprint future-head đổi/ổn định/khớp-record-persist, ready→queued→ready→offered, schema 1.2.0 + upcaster 1.1→1.2, created-event giữ version event entity) — **viết ĐỎ trước** (9 fail trên code cũ), xanh sau khi sửa.
- **Mới:** `tests/test_demo_checkpoint_alignment.py` +3 test attach-safety (skip moving → safe trong validity; moving-suốt-validity vẫn gắn để queued có vết; expired-before-transition audit).
- **Mới:** `ui/backend/tests/test_demo_moving_queue.py` (2 test — queued event + idempotent + resume ra card; queued quá freshness ⇒ expired trung thực).
- **Cập nhật theo hành vi mới (có ghi lý do trong diff):** `tests/test_schemas.py` (latest 1.2.0), `tests/test_advice_checkpoint.py` (chuỗi upcast tới 1.2.0; created event 1.1.0).

## 5. Before/After (cùng working tree, cùng seed — artifact thật)

### Trace-level, 5 seed 1000–1004 (`analyze_checkpoints.py`)

| Chỉ số | BEFORE | AFTER | Diễn giải |
|---|---:|---:|---|
| Records | 864 | 4.705 | dedup không còn nuốt revision; ONLINE 4.242 (90,2%) **vẫn 100% suppressed maintenance** — volume quan sát, không phải card |
| READY | 413 | 462 | +49 = revision SWAP/REST thật trước đây bị nén |
| S1 / SWAP / REST | 198 / 162 / 54 | 198 / 208 / 57 | S1 không đổi (không window trong material — đúng thiết kế chống spam) |
| Validity mean | 1,0′ (giả) | S1 30′ · SWAP 23,3′ · REST 25,7′ | boundary thật (min của bucket/shift/freshness) |
| Expired | 1 | 117 (116 ONLINE cuối ca + 1 SWAP; 115 inverted) | họ `window_past` LỘ RA trung thực thay vì bị freshness 1′ che — đều đúng luật không hiển thị |
| READY không attach | 1 (SWAP) | **2 (S1, sát cuối timeline)** | lớp mất SWAP đã đóng |
| Attach trùng | 0 | 0 | |
| QUEUED trace | 0 | 0 (sim capture vẫn is_driving=False — đúng thiết kế; queued sống ở demo/product store) | |
| Driver-run 0 READY | 148/450 | 148/450 | đúng policy (S1 không trigger + cả ca ONLINE) — không "chữa" bằng nới ngưỡng |
| Comparator dynamics (shadow on/off) | — | **IDENTICAL 5/5 seed** | `scripts/compare_checkpoint_shadow.py --config configs/pilot_dongda.yaml` |

### Presentation funnel Web thật, seed 1000, 90 actor (`measure_presentation_funnel.py`)

Cùng 90 actor, cùng 7.100 transition, cùng route stub — chỉ khác code nền móng:

| Chỉ số | BEFORE | AFTER |
|---|---:|---:|
| Step có card | 40 (0,56%) | **92 (1,30%)** |
| Actor thấy ≥1 card | 37/90 (41%) | **59/90 (66%)** |
| Actor 0 card | 53 (trong đó 20 mất OAN vì expired giả) | **31 (0 actor mất vì expired — 31 này thật sự không có READY, đúng policy)** |
| Silent `expired` tại presentation | 34 | **1** |
| Silent `unsafe_while_moving` | 12 | **6** (còn lại = di chuyển suốt validity, nay có vết `queued`) |
| Số click tới card đầu | median 24 / p90 47 | **median 10 / p90 39** (≥6 actor card ngay step 1) |
| Card/actor | median 0 / max 2 | **median 1 / p90 3 / max 3** |
| Card theo topic | energy 16 · bonus 15 · rest 9 | energy 45 · bonus 33 · rest 14 |
| Card khi driver state | idle 100% | idle 100% (không card khi đang lái — ranh giới giữ nguyên) |

Card density tăng do **card từng bị nuốt oan nay hiển thị được** (validity thật + attach an toàn + revision không bị dedup), KHÔNG do đổi cadence/budget/suppression — `silent_maintenance`, budget 6, cooldown 20′ nguyên vẹn; max 3 card/ca.

### Ổn định 10 seed tươi 2000–2009

| Chỉ số (10 seed 2000–2009) | BEFORE | AFTER |
|---|---:|---:|
| Records | 1.766 | 9.410 (ONLINE 8.450 vẫn 100% suppressed) |
| READY | 863 (0,959/dr) | **954 (1,06/dr)** |
| S1 / SWAP / REST | 400 / 321 / 145 | 400 / **414** / 146 |
| Validity mean | ~1′ | SWAP 23,0′ · REST 25,2′ · S1 30′ |
| Expired | 3 | 212 (họ `window_past` lộ trung thực) |

Cấu trúc after nhất quán giữa hai bộ seed disjoint — không phải hiệu ứng một seed.

## 6. Demo flow sau thay đổi

Không đổi UI/cadence: card vẫn chỉ hiện ở transition an toàn, một primary, mounted ACK như cũ. Khác biệt người xem thấy: (1) card SWAP/REST có khung giờ thật "trong khung HH:MM–HH:MM"; (2) nhiều actor có card hơn và card đến sớm hơn (không còn chết oan vì validity giả); (3) bước đang-lái có dấu vết `queued` trong store thay vì im trắng — dev/audit phân biệt được "im vì lái" với "mất card".

## 7. Scenario được hỗ trợ tốt hơn / còn defer

- **Tốt hơn ngay:** 1.1 S1 bonus (numbers trên record), 1.2 SWAP-now (window + revision theo bucket), 1.3 REST (window); goal #1–#12 của đề bài — xem §9.
- **Mở khoá nhưng CHƯA làm (chờ owner):** `SWAP_SOON` (dữ liệu future-head + window đã sẵn trên record; cần quyết định topic/policy vì ONLINE maintenance vẫn im đúng luật); brief/recap (Q-10/counting); `order_skipped_soc` awareness; income pace (cần payout vào snapshot).
- **Defer có chủ đích:** sửa `dropoff` state boundary (`world.py:709-729`) — đụng dynamics, cần cycle riêng có fingerprint per-actor chứng minh behavior-neutral (blocker của idle/efficiency producer, KHÔNG blocker của lượt này); caveat text lên card driver-facing (UX — owner); trim 6 numbers S2 trên card (UX pre-existing).
- **Follow-up P1 (pre-existing, lộ ra khi chạy full suite):** (a) **ĐÍNH CHÍNH 2026-08-06** — `tests/test_demo_trace_neutrality.py::test_real_demo_order_boundaries_capture_post_mutation_state` KHÔNG cùng root-cause với K-01(a) (`scripts/compare_checkpoint_shadow`, đã sửa bằng `pythonpath=[".", "src"]` — xem UPDATE-150). Test này import `app.services.demo_session`, mà `app` chỉ được thêm vào `sys.path` bởi `ui/backend/tests/conftest.py`, có phạm vi CHỈ cây `ui/backend/tests/` — file test nằm ở `tests/` (root) không nằm trong phạm vi đó nên vẫn đỏ sau fix K-01(a). Sửa thật cần: dời test sang `ui/backend/tests/`, hoặc thêm `ui/backend` vào `pythonpath` gốc (ảnh hưởng mọi test root, cần cân nhắc rộng hơn scope cycle này); (b) phân loại 4 hàm demo trace (`_driver_snapshot`, `_trip`, `build_demo_trace`, `World.log`) trong money manifest — chúng là projection thuần của giá trị engine, nhưng phân loại thuộc chủ cổng `test_health_boundary`.

## 8. Open decisions thật sự cần owner

1. **`SWAP_SOON`**: cho phép một candidate maintenance-ONLINE có future SWAP material trở thành card chủ động (đổi suppression policy / thêm topic mới trong contract đóng)? Đây là quyết định CHÍNH SÁCH nói-nhiều-hơn (đúng vùng V-18/ĐA-04), dữ liệu đã sẵn 84,7% driver-run.
2. **Volume record ONLINE ×~9 (suppressed)**: giữ mọi revision (audit đầy đủ) hay nén maintenance-only revisions ở tầng capture để RunResult nhẹ? Kỹ thuật làm được cả hai — chọn theo nhu cầu audit/telemetry.
3. Brief/recap/counting (Q-10) và các quyết định cũ Q-09/Q-13/V-21 — như UPDATE-146 §8.

## 9. Hệ thống trả lời 12 câu hỏi mục tiêu thế nào (kiểm được bằng test/artifact)

1. Checkpoint nào được tạo → record 1.2.0 + trace refs. 2. Vì sao → solver_set/reason_code + artifact + numbers/caveats ngay trên record. 3. Hiệu lực → validity thật (bucket/shift/freshness). 4. Facts/numbers → `numbers[]`/`caveats[]` trên record. 5. Vì sao hiện/không → lifecycle event + silent reason + `checkpoint_audit` (thêm `expired_before_transition`). 6. Đang di chuyển → `queued` event, không card chữ. 7. An toàn trở lại → resume `queued→ready` (test chứng minh); quá hạn ⇒ `expired` trung thực. 8. Revision mới có bị dedup nhầm → không (future_head + window trong fingerprint; test đỏ-được). 9. Tài xế thấy gì → template v2, window thật. 10. Bây giờ ≠ Sắp tới → giữ nguyên tách current/future (test F2 hiện hữu + template). 11. Intent/execution/outcome → không đổi ranh giới (accepted ≠ execution ≠ outcome; funnel không gửi intent giả). 12. Web demo tìm checkpoint có ý nghĩa mà không đổi cadence → attach-an-toàn + validity thật (funnel after), không đổi nhịp.

## 10. Rollback

- Toàn bộ là commit-revert được; không migration phá huỷ: store cũ (record 1.1.0) vẫn đọc/validate theo version của chính nó, upcaster là pure function.
- Kill-switch sẵn có: `checkpoint_shadow.enabled=false` tắt toàn bộ trace; `ADVICE_V2_ENABLED=0` giữ nguyên product path tắt.
- Session store demo là per-session (digest) — không có state cũ cần dọn.

## Kiểm chứng

| Lệnh | Kết quả |
|---|---|
| `pytest -q tests/test_checkpoint_enrichment.py` (+alignment, +moving_queue) | 13+5(3 mới)+7(2 mới) pass; 9 test ĐỎ trước khi sửa |
| `pytest -q` (root, full, 22′13″) | **1018 passed / 4 skipped / 2 failed — CẢ HAI FAIL LÀ PRE-EXISTING**, chứng minh bằng `git stash` toàn bộ diff U-138 rồi chạy lại: vẫn fail y hệt. (1) `test_demo_trace_neutrality.py` — `ModuleNotFoundError: No module named 'app'`: test của commit `e778a77` import `app.*` nhưng `pyproject pythonpath=["src"]` — test này CHƯA TỪNG chạy được trong root suite; (2) `test_health_boundary.py::test_money_manifest_is_complete` — cổng money-scope đỏ từ khi demo trace commits thêm `demo_trace._driver_snapshot/_trip/build_demo_trace` + `World.log` chạm token tiền mà chưa phân loại manifest. Các cycle UPDATE-128..134 chỉ chạy focused suite nên không thấy |
| `pytest -q ui/backend/tests` (full) | **124 passed** (1 fix contract enum trong cycle) |
| `compare_checkpoint_shadow.py --seeds 1000..1004` | **IDENTICAL 5/5** |
| Inventory/funnel before-after | bảng §5, artifact scratchpad + `research/audit/2026-08-05-checkpoint-scenario-discovery/` |

## Visual verification

- **Status:** `WAITING-VERDICT` — thay đổi nội dung card (window text) + mật độ card demo là meaningful UI change; funnel automation đã đo nhưng **mắt Cường chưa xem**. Cách xem: `/app/` tạo session seed 1000, actor 77/39/70, Next Step tới card đầu (≤3 click), kiểm text "trong khung HH:MM–HH:MM" + provenance MOCK; một transition đang lái phải silent. Chưa commit/push — chờ verdict theo gate.

## Adversarial self-review / flaws found

1. **Volume ONLINE ×9** (suppressed) — đo và khai §8.2, không giấu; không ảnh hưởng tài xế (vẫn im) nhưng làm RunResult/payload demo nặng hơn; cần owner chọn hướng nén nếu thành vấn đề.
2. **115 expired inverted validity** — họ `window_past` lộ ra do bỏ mặt nạ freshness; đúng luật không hiển thị, nhưng con số này giờ PHẢI được đọc là "khuyến nghị cho khung đã qua", không phải bug mới.
3. Fallback `+1′` còn tồn tại cho caller không truyền hints — chấp nhận cho fixture cũ, đã comment; mọi callsite production truyền hints (grep xác nhận 5/5).
4. Funnel AFTER dùng route stub như BEFORE — so sánh cùng điều kiện; đường advice không đọc route (đã kiểm `_advice`).
5. `rest_window_end = (hour+1)·60` chỉ đúng run 1 ngày — S7 đang tắt ở demo/pilot; ghi chú tại chỗ, phải sửa khi bật multiday S7.
6. Queued event id chứa timestamp — idempotent theo transition; hai transition khác nhau cùng trạng thái lái tạo 2 queued event: hợp lệ (ready→queued chỉ legal một lần, lần hai ValueError bị nuốt có chủ ý — đã test không nhân đôi).
7. Chưa chạy Flutter (SDK vắng — V-25 cũ vẫn treo); Web funnel là automation, không thay mắt người.
8. **2 fail pre-existing của branch lộ ra khi chạy full suite** (điều các cycle trước bỏ qua): (a) `test_demo_trace_neutrality` không import được `app` trong root config — test dropoff-boundary của chính branch này chưa từng chạy; (b) money-manifest gate đỏ vì 4 hàm demo trace chạm token tiền chưa phân loại. KHÔNG sửa trong cycle này (ngoài scope, money gate cần phân loại ngữ nghĩa cẩn thận) — ghi thành follow-up P1 bên dưới. Môi trường còn 3 process pytest zombie 0% CPU từ session Codex cũ (bẫy vận hành BOOTSTRAP §5) — không kill vì không thuộc session này.
