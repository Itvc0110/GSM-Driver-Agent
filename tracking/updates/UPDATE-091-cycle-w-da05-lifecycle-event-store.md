# UPDATE-091 — Cycle W: ĐA-05 — advice lifecycle store (event log append-only + projections một-luật)

> ⏸ **TRẠNG THÁI: ĐANG DỞ — PAUSE theo yêu cầu Cường (2026-07-29 ~03:40).** KHÔNG đọc
> update này như một cycle đã hoàn tất. Review đối kháng 2 lăng kính tìm ra **16 finding
> có reproduce thật** (hồ sơ đầy đủ: `research/audit/2026-07-29-cycle-w-review/findings.md`),
> trong đó nghiêm trọng nhất: **`adherence_view` báo 0%/2%/100% trong khi sự thật
> 53,6%/52,2%/48,8%** — thước đo sai nằm ngay trong "một luật" mà cycle này quảng cáo.
> 13/16 finding đã sửa; **3 finding còn lại + full suite + fingerprint chưa chạy lại**.
> Cường chốt: phần còn lại phải **qua plan mode** trước khi sửa tiếp.

- **Ngày:** 2026-07-29
- **Người thực hiện:** AI agent, dưới claim của **Cường** (mạch *"hướng tốn thời gian, khó,
  nhiều giá trị nhất"*; plan duyệt trong phiên)
- **Loại:** architecture (store/audit layer) — **KHÔNG đổi hành vi sim/solver** (có bằng chứng)
- **Đóng:** ĐA-05 (design Cường duyệt 27/07) · D-A3-04 (3 store không join được) ·
  FAILCLOSED-3 · MEMSTATE-2/3/4/6 · FAILCLOSED-7 (một phần: digest vẫn values-only, xem §flaws) ·
  LAYEROUT-16 · **Mở khoá:** ĐA-04 cadence memory (adherence_view + decision_id đã có vật mang)

## Vấn đề (audit `04-*` §6, xác nhận lại bằng 2 Explore agents)

Ba store advice rời rạc, ba namespace ID, không join được: SQLite `episodes` (`adv-uuid`,
write-only — không ai đọc), UI JSONL (`s1-…`), sim events (không có ID — content+t_min+actor).
Hệ quả sống: nút "Bỏ qua" trên UI không bao giờ đổi được hành vi advisor (vòng adherence §12 HỞ);
"followed" của sim không có mẫu số tin được (BRIDGE-3).

## Cơ chế mới (đúng verdict Cường: *"sim để RAM chỉ thêm run_id; UI và sim cùng đọc MỘT projection — một luật, một database"*)

| Mảnh | Nội dung |
|---|---|
| W1 `gsm_core/lifecycle/event_log.py` | SQLite **append-only** (`INSERT OR IGNORE` theo `event_id` — không API update/delete, test canh bằng hasattr); validate qua registry TRƯỚC khi ghi; busy_timeout + bounded retry + đếm `sqlite_busy_count`; KHÔNG bật WAL (bug ≤3.51.2); `close()`/context manager (đóng LAYEROUT-16) |
| W2 schema | `advisor/advice_lifecycle_event` 1.0.0 qua registry đa phiên bản Cycle V ⇒ replay-qua-migration sẵn từ ngày đầu; IDs tách `decision_id`/`display_id`/`event_id`; `occurred_at`+`observed_at`; `actor`/`origin`/`source`; `reason_code`; `context_revision` |
| W3 `projections.py` | **MỘT LUẬT pure-function trên iterable**: `decision_state` (máy trạng thái decided→displayed→followed/dismissed/expired/superseded; suppressed nhánh hệ thống), `adherence_view` (**denominator = decided** — khắc BRIDGE-3 vào luật), `sim_events_to_lifecycle` (RAM→envelope, deterministic, không uuid). Sort theo **thời gian thật** (xem §flaws #1) |
| W4 sim | `Event.run_id` (field DUY NHẤT thêm — đúng chốt); `derive_run_id(cfg,seed)` deterministic `{seed}-{arm}-{kênh}-{coverage}[-pos.mode]` (A/B cùng seed phân biệt được; A cache xuyên ladder giữ MỘT id); `_decision_id` bucket 30' stamp vào 7 chỗ emit advice; standby: decision sinh lúc GÁN, follow dùng lại (`standby_decision` dict); manifest thêm `run_id_deterministic` (folder `runs/` giữ tên wall-clock — không phá) |
| W4 pipeline | reset `last_verify_result` mỗi request (R5 hết mang verdict stale); episode mang `verify` verdict (FAILCLOSED-3) + `solver_report_refs` = problem_digest THẬT (MEMSTATE-4) |
| W4 UI | POST /advice/action ghi event vào store canonical (idempotent — double-click cùng phút = 1 event); GET /actions đọc từ event log, GIỮ nguyên hình dạng contract; JSONL giữ làm debug export song song (đúng quyết định duyệt) |
| W5 adapter | EpisodeStore giữ 4 chữ ký cũ: `append_episode`→event `decided` (một đường ghi, không double-write), `count_episodes`→projection, cache giữ nguyên bảng cùng file |

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| TDD | test đỏ trước ở mọi bước (18 test store/projections + 9 wiring + 2 UI lifecycle) |
| **Bit-identical 5 seeds × 2 arm** | fingerprint (summarize + đếm kind) code HEAD (worktree riêng) vs code mới: **IDENTICAL 10/10** — thêm nhãn không đổi hành vi, không dịch RNG. Chạy LẠI sau toàn bộ hardening: vẫn IDENTICAL 10/10 |
| **Bit-identical multiday** | `run_multiday(seed=1000, days=3)`, 4 kênh + positioning: **IDENTICAL 3/3 ngày** vs HEAD (đường này tôi vừa sửa nên phải chứng minh riêng, không suy diễn từ `run_once`) |
| Mutation | MW1 IGNORE→REPLACE ⇒ đỏ idempotency · MW2 bỏ dismissed ⇒ đỏ denominator · MW3 adapter quên run_id ⇒ đỏ · MW4 derive_run_id lờ arm ⇒ đỏ · restore xanh |
| Exact-repeat | 2 lần cùng cfg+seed ⇒ event stream + run_id + decision_id y hệt (test) |
| Test cũ | test_advisor_pipeline 22/22 xanh KHÔNG SỬA (12 call site EpisodeStore nguyên vẹn); UI backend 43/43 |
| Windows lock | close() + test unlink sau close (LAYEROUT-16) |
| Full suite | (điền khi suite nền `bilqav794` xong — kỳ vọng 653+28 mới) |
| Review đối kháng | (điền khi workflow `w7dlwkqb5` xong) |

## Visual verification

`NOT_APPLICABLE` — tầng store/audit: bằng chứng KHÔNG đổi payload UI/sim = fingerprint
IDENTICAL 10/10 + GET /actions giữ nguyên hình dạng contract (43 test UI xanh, trong đó
roundtrip contract cũ không sửa). W6 (khu Mô phỏng web đọc projection thay vì nén advice
event — `sim.py:60-62`) là bước ĐỔI payload UI ⇒ tách cycle sau, có visual gate riêng.

## Root cause / phân loại 4 phát hiện — ĐỌC KỸ TRƯỚC KHI TIN

Cường chỉ đạo kiểm lại: *"kiểm tra xem phải lỗi thật không"*. Đã đo trên run thật
(seed 1000, coverage=all, 4 kênh bật) — **kết luận trung thực: cả 4 là LAN CAN BOUNDARY,
KHÔNG phải bug đang gây sai số hôm nay.**

| # | Phát hiện | Reproduce | Có đang xảy ra không? |
|---|---|---|---|
| 1 | sort theo CHUỖI ISO sai khi trộn múi giờ | ✅ failing test | **CHƯA** — hôm nay mỗi store chỉ chứa MỘT origin (pipeline toàn UTC, UI/sim toàn +07:00). Kích hoạt đúng lúc hợp nhất "một database" (W6/ĐA-04) — tức nợ này sinh ra CÙNG mục tiêu của ĐA-05 |
| 2 | naive timestamp làm chết toàn bộ projection (`TypeError`) | ✅ repro | **CHƯA** — đo: 0/N event sim naive; pipeline `fromtimestamp(tz=utc)`, UI `now(timezone.utc)` đều aware |
| 3 | numpy scalar trong payload nổ `json.dumps` | ✅ repro | **CHƯA** — quét MỌI kind của run thật: 0 giá trị non-builtin (bridge đã `round()`/`float()`) |
| 4 | chuỗi rác qua `minLength` vào được log | ✅ repro | **CHƯA** — chưa producer nào ghi rác |
| **5** | **`run_multiday` KHÔNG stamp `run_id`** — tạo `World(...)` trực tiếp, không qua `run_once` | ✅ failing test | **CÓ — LỖI THẬT của chính cycle này.** Toàn bộ event của đường chạy nhiều ngày (nền của D-SIM-10/13 và của ĐA-04 sắp tới) mang `run_id=""` ⇒ mất identity, không join/export được. Tự bắt khi soát diff, fix + test canh (`test_multiday_events_also_stamped`, kiểm cả 2 ngày phân biệt được) |

Vì sao vẫn giữ 4 lan can (thay vì gỡ theo YAGNI): đây đúng boundary mà goal của Cường
cảnh báo — *"data đến từ hệ sinh thái Vingroup/GSM chưa rõ dtype, output API ngoài phải
normalize về đúng dạng ta muốn"*. Store append-only là nơi **không sửa lại được**: record
rác lọt vào là vĩnh viễn. Chi phí lan can ~30 dòng, giá phải trả nếu thiếu là hỏng lịch sử.
**Không được đọc mục này thành "đã sửa 4 bug"** — chưa bug nào trong số đó từng xảy ra.

## Adversarial self-review / flaws found

1. **Positioning thiếu event `decided` phía sim**: quyết định standby sinh lúc GÁN nhưng
   không có per-actor event tại đó (chỉ system `standby_alloc` tổng hợp) — vì cycle này
   KHÔNG thêm event kind mới (giữ `/ab` n_advice và dashboard nguyên số, điều kiện của
   fingerprint IDENTICAL). Denominator positioning trong sim vì thế under-count (chỉ thấy
   follow). Ghi TODO làm cùng ĐA-04/W6 khi được phép đổi event stream.
2. `advice_bonus_gate`/`advice_rest_window` fire mỗi tick → decision_id gộp theo bucket 30'
   là ĐỊNH NGHĨA (spec adherence §advice_id), không phải đo đếm sự kiện vật lý — consumer
   phải hiểu 1 decision = 1 bucket, không phải 1 tick. Đã ghi trong docstring `_decision_id`.
3. FAILCLOSED-7 (state_digest values-only) CHƯA sửa trong cycle — digest này giờ chỉ còn vai
   phụ (refs thật đã có problem_digest); sửa digest là việc riêng, sev thấp.
4. Hàng JSONL UI ghi TRƯỚC Cycle W không tự chuyển vào event log (mock-only, gitignored) —
   GET /actions sau cycle chỉ thấy hàng mới. Chấp nhận, không viết importer.
5. `advice_cache` (dead code có chủ) vẫn INSERT OR REPLACE trong CÙNG FILE sqlite — lời hứa
   append-only là của BẢNG `advice_events`, không phải của file. Đã ghi rõ ở docstring adapter.
6. Sim `driver_id` trong lifecycle = `str(actor_id)` — chỉ có nghĩa trong phạm vi `run_id`;
   join xuyên run phải dùng cặp (run_id, driver_id). Ghi trong schema description.

## Files

MỚI: `src/gsm_core/lifecycle/{__init__,event_log,projections}.py` ·
`schemas/advisor/advice_lifecycle_event.schema.json` · `tests/test_lifecycle_store.py` (19) ·
`tests/test_lifecycle_wiring.py` (9) · `ui/backend/tests/test_lifecycle_actions.py` (2).
SỬA: `schema_registry.py` (entity) · `episode_store.py` (viết lại thành adapter) ·
`pipeline.py` (reset verdict + enrich episode) · `world.py` (Event.run_id, `_decision_id`,
7 emit sites, standby_decision) · `runner.py` (derive_run_id) · `logging_ev.py` (manifest) ·
`ui/backend/app/routers/advice.py` · `tests/test_schemas.py` (EXPECTED +1) ·
`schemas/{README,CHANGELOG}.md`.

## Docs cập nhật kèm

TODO (ĐA-05 → DONE-CODE; flaw #1 thành mục mới) · PENDING-REVIEW (ĐA-05 chờ verdict code) ·
DEFERRED (D-A3-04 → DONE-CODE; thêm D-ARCH-A2 problem_digest cache) · PROJECT-GRAPH (node 091).

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 (Cường: "hỏi lại sau") · Q-03 corpus Khánh · Q-04 UX proposal · Q-07 dispatch H3 ·
BUG-MOCKGEN-CLI · nợ UI card standby_zone (chặn bởi Q-04) · **MỚI: ĐA-05 code chờ verdict
(UPDATE-091)** · đề xuất kế tiếp: ĐA-04 cadence memory (Cường yêu cầu "khó nhất, phải visualize").
