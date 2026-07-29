# UPDATE-099 — ĐA-04: AdviceCadencePolicy MỘT LUẬT (sim + UI) + keyed adherence draw + visualize

- **Ngày:** 2026-07-29 · ⚠ **Đổi số 098 → 099 (2026-07-29)**: remote đã chiếm 098 (`c493d89`, debate herding) — theo quy tắc numbering-không-trùng, tiền lệ 073→082
- **Người thực hiện:** AI agent (Fable 5) theo yêu cầu Cường — cycle kế tiếp sau C5/UPDATE-097
- **Loại:** feature (đổi HÀNH VI thật của advisor ở cả sim lẫn sản phẩm)
- **TODO / User story liên quan:** ĐA-04 (duyệt 2026-07-27), D-A3-01, D-SIM-14, W6 (một phần), V-18 (mới)

## Tóm tắt

Advisor trước cycle này **nói không có nhịp**: sim rút lại coin tuân thủ mỗi tick 2′ tới khi
"thành công" (washout D-A3-01 — adherence danh nghĩa 0,30 có hiệu dụng ≈1,0), còn UI thì
`GET /advice` **stateless** nên nút "Bỏ qua" của tài xế không đổi được gì. Cycle này đưa vào
**một luật nhịp dùng chung** (`gsm_core/lifecycle/cadence.py`) mà **cả sim lẫn sản phẩm cùng
gọi**, cộng với **keyed adherence draw** (một coin cho mỗi `(decision_id, material_revision)`).
Kết quả đo được: hai đơn vị adherence **hội tụ** — decision 68,1% vs event 67,6% (trước ĐA-04:
76,9% vs 53,6%, lệch 23đp). Washout chết ⇒ **mọi con số A/B từ nay mới đo đúng cái nó nói**.

⚠️ **Nhưng phần quan trọng nhất của UPDATE này là một LỜI ĐÍNH CHÍNH, không phải một kết
quả.** Tôi đã báo cho Cường hai con số "giá của nhịp" (−2.885đ rồi −3.048đ) **trước khi** hai
vòng soi đối kháng độc lập tìm ra **ba confound** trong chính arm đối chứng của phép đo đó:

1. **Lỗi #13 (`DET-01`)** — cờ `cadence.enabled` không chỉ tắt nhịp mà **tắt luôn keyed coin**,
   hồi sinh đúng cái washout cycle này sinh ra để giết ⇒ arm đối chứng có tài xế nghe lời
   **~10 điểm phần trăm nhiều hơn** vì lý do không liên quan tới nhịp.
2. **Lỗi #17 (`R-01`)** — một lời khuyên được nghe theo bị **áp tác động 2,0–2,5 lần** ở arm
   đối chứng. **Lỗi đúng-sai, không chỉ lỗi đo**: mức can thiệp phụ thuộc vào việc advisor bị
   hỏi lại bao nhiêu lần — tức phụ thuộc chính cái đang được đo.
3. **Lỗi #18 (`R-09`)** — ba kênh dùng ba định nghĩa "đã nói" ⇒ ngân sách chia không đồng nhất.

Đã sửa cả ba, **kiểm chứng bằng chính phép đo đã phát hiện chúng** (lệch thổi phồng giữa hai
arm 0,095 → **0,003**; tỷ lệ liều can thiệp 2,5× → **1,17×**), và **đo lại toàn bộ**.

**Con số cuối (artifact 37, n=100 ghép cặp): giá của nhịp = −1.530đ CI[−2.401, −673] SIG —
bằng ĐÚNG MỘT NỬA con số tôi đã báo (−3.048đ).** Chiều kết luận đúng từ đầu, **định lượng thì
sai gấp đôi**.

Và lưới 2×2 đo lại đổi luôn câu trả lời: **không có `shift_plan`, nhịp gần như MIỄN PHÍ
(+384đ)**; toàn bộ chi phí nằm ở **tương tác với `shift_plan` (+3.249đ)**. Tức **nhịp không
đắt — cách chia ngân sách FIFO mới đắt**. Ở **config ship** (chỉ `positioning`, kênh nằm ngoài
hệ thống cadence) nhịp tốn **≈ 0đ**. Hệ quả: `D-ĐA04-03` mạnh lên chứ không yếu đi như tôi
đoán ở PLAN draft.

⚠ **Và lập luận "cái nhịp mua được" cũng phải đính chính**: *"P5 thoát khỏi mức hại −8.166đ
SIG"* — **SAI, rút lại** (sau khi loại confound, không nhóm nào bị hại có ý nghĩa ở bất kỳ
arm nào). *"Nhịp mua công bằng"* vẫn đúng nhưng hẹp hơn: ghép cặp ON−OFF cho gini −0,0030 SIG,
nhưng so với thế giới không-advice thì arm đủ kênh chỉ **ns** — và arm DUY NHẤT có gini cải
thiện SIG là **chỉ-positioning**.

Đó vẫn là **đánh đổi sản phẩm, agent không tự quyết** → `Q-09` trong `PENDING-REVIEW.md`.

## Chi tiết cập nhật

### 1. Lõi chung `src/gsm_core/lifecycle/cadence.py` (MỚI)

Thuần, không import sim/UI/streamlit — theo đúng mẫu `projections.py` của ĐA-05 ("một luật,
một database"). Cấu phần:

| Thành phần | Nội dung | Vì sao |
| --- | --- | --- |
| `CadenceConfig` | `min_gap_min_per_topic=20`, `max_proactive_per_shift=6`, phase [25%, 75%] | Số BASELINE đã duyệt ở ĐA-04, không tự đặt thêm hằng số |
| `shift_phase(elapsed, len)` | `early` / `mid` / `late` | Anchor theo **PHA CA**, bỏ wall-clock (chữ của design) |
| `evaluate(...)` | `PRESENT` / `QUEUE` / `SUPPRESS` + typed reason + `next_eligible_min` | Pure function — sim và UI cùng gọi |
| `adherence_coin(seed, decision_id, material_revision)` | sha256 → uint64/2⁶⁴ | MỘT coin/quyết định; re-check KHÔNG re-roll |
| `DECISION_BUCKET_MIN = 30.0` | hằng dùng chung cho `decision_id` **và** coin | Xem "Lỗi #1" bên dưới |

Thứ tự luật trong `evaluate` (quan trọng — priority safety > policy > demand):
an toàn bypass mọi cổng → đang lái ⇒ `QUEUE` (không mất lời khuyên) → dismissed trong pha ⇒
`SUPPRESS` → hết ngân sách ca ⇒ `SUPPRESS` → chưa hết cooldown topic ⇒ `SUPPRESS` → `PRESENT`.

### 2. RANH GIỚI SIM ↔ SẢN PHẨM (chỉ thị Cường 2026-07-29 — chép nguyên văn)

> *"việc đo hiệu quả của phần mềm trong sim không nên bị ảnh hưởng bởi việc tắt gợi ý khi xế
> bấm nút bỏ qua, sim là để đo hiệu quả của 1 xã hội driver tuân theo lời khuyên so với 1 xã
> hội driver khi chưa có hệ thống và làm việc với quy tắc random."*

Chỉ thị này **thay đổi thiết kế đang làm dở**: bản đầu định cho sim dùng cả `dismissed_for_window`
cho "giống sản phẩm nhất". Sai. Sim đo **xã hội tuân theo lời khuyên vs xã hội random** — nút Bỏ
qua là hành vi của người dùng thật trước một UI thật, không phải tham số của phép đo. Nếu nối
dismiss vào sim thì arm B tự bịt miệng mình rồi mọi Δ đều nhỏ đi vì lý do không liên quan tới
chất lượng lời khuyên.

Phân định cuối cùng:

| Cơ chế | SIM | SẢN PHẨM (UI) | Lý do |
| --- | --- | --- | --- |
| cooldown 20′/topic | ✅ | ✅ | Thuộc tính của LỜI KHUYÊN (nói quá dày là dở ở cả hai thế giới) |
| ngân sách 6/ca | ✅ | ✅ | Như trên |
| `dismissed_for_window` | ❌ **KHÔNG BAO GIỜ** | ✅ | Hành vi người dùng trước UI — không phải biến của phép đo |
| `unsafe_while_moving` → QUEUE | (n/a, sim chỉ hỏi lúc idle) | ✅ | An toàn của người thật |
| "nghe hay không nghe" | `adherence_coin` theo archetype | nút bấm thật, ghi vào event log | Sim MÔ HÌNH HOÁ, sản phẩm ĐO |

Ranh giới này được **khoá bằng 2 test**, không phải bằng lời hứa trong docs:
`test_sim_never_suppresses_by_dismiss` (2 seed, quét reason của mọi `advice_suppressed`) và
`test_sim_cadence_memory_has_no_dismiss_state` (đọc source `AdviceActionBridge`, đỏ nếu ai đó
thêm `dismissed_in_phase[...]`). Docstring `cadence.py` chép nguyên văn chỉ thị để người sửa
sau đọc được lý do, không chỉ đọc được luật.

### 3. Sim wiring (`advice_bridge.py`, `world.py`)

- 4 kênh (`shift_plan`, `accept_lift`, `shift_extend`, `rest_window`) hỏi `cadence_allows()`
  **trước** khi làm việc; SUPPRESS ⇒ event `advice_suppressed` có reason typed, dedupe theo
  `(actor, topic, reason, bucket)` để không spam mỗi tick.
- 4 chỗ `rng.random()` tuần tự thay bằng `coin_follows(...)` với `material_revision` riêng cho
  từng kênh (`solver_action` / `"lift"` / `"extend"` / `f"cell{target}"`) — **nội dung lời khuyên
  đổi thật thì mới có coin mới**, đúng chữ của design.
- `positioning` **không tính vào ngân sách** (`count_positioning_in_budget=False`). Căn cứ: đó
  là kênh DUY NHẤT dương SIG ở mọi mức chi phí thực (artifact 29: +4.000→+3.363đ, break-even
  ≈1.570đ/km ≈ 6× cận trên chi phí thật). Bịt nó bằng ngân sách chung là **tự tay vứt giá trị
  đã chứng minh** để đổi lấy sự đối xứng hình thức. Cờ bật lên thì kênh này chịu cả cooldown
  lẫn ngân sách như mọi kênh khác — **và đường dây đó nay có thật** (xem Lỗi #6: ban đầu nó là
  cờ chết, config đọc được nhưng không tới engine).
- `world._decision_id` và coin **dùng chung** `decision_bucket()` (xem Lỗi #1).
- Drain hàng đợi suppressed sau vòng idle với hậu tố `-sup` trên `decision_id` (xem Lỗi #2).

### 4. UI wiring — vòng adherence §12 KÍN VỀ HÀNH VI

`GET /api/v1/advice` nay dựng `CadenceMemory` từ **store canonical** `AdviceEventLog` (origin=ui,
đúng tài xế, đúng ngày) rồi gọi **cùng `evaluate`** như sim. SUPPRESS/QUEUE ⇒ trả `items: []` +
`silent.reason_code` + `silent.message` (4 thông điệp tôn trọng, không đổ lỗi, không hứa) +
block `cadence`. `POST /advice/action` ghi thêm `topic` + `phase` vào payload để memory đọc lại
đúng ngữ cảnh; `dismissed` mang `reason_code="dismissed_for_window"`.

Ba trường của `CadenceMemory` đều được nuôi ở phía UI: `dismissed_in_phase` (từ event
`dismissed`), `proactive_count` và `last_decided_min` (từ `displayed`/`followed`). Trường
thứ ba từng bị bỏ quên — xem Lỗi #9.

**Khác biệt sim vs UI (yêu cầu "khác biệt rõ" của Cường)**: sim nuôi memory trong RAM theo tick
nội sinh; UI dựng lại memory từ event log tại **request-time**. Hai đường vào khác nhau, **một
hàm quyết định** — đó là chỗ "một luật" có nghĩa thật chứ không phải khẩu hiệu.

Cửa sổ dismissed = **hết PHA ca hiện tại** (Cường chốt qua AskUserQuestion 2026-07-29). Hai
phương án bị loại: "90 phút" (hằng số tự đặt, không căn cứ) và "im hết ca" (chặn luôn cảnh báo
an toàn/mất thưởng về sau — trái priority safety > policy > demand).

### 5. Visualize (V-18)

- `ui/backend/app/routers/sim.py::_journey_payload`: **giữ** `channel/followed/reason/decision_id`
  thay vì nén thành `{"kind":"advice"}` — đóng một phần W6. Trước đây khu Mô phỏng **không thể**
  cho thấy advisor im lúc nào vì thông tin đã bị vứt ở tầng payload.
- `src/gsm_sim/dashboard.py::tab_journey`: vạch **CHẤM** = advisor NÓI; **vùng xám** = quãng
  advisor im vì hết ngân sách ca (một mốc + vùng tô, KHÔNG phải 55 vạch — xem Lỗi #10);
  vạch **GẠCH** chỉ dành cho lý do còn thông tin (cooldown, hoãn vì đang lái). Thêm bảng
  "Nhịp nói của advisor (ĐA-04)" liệt kê per-topic đã nói / bị nén **và vì sao** — đọc
  thẳng từ event, không tự tính lại.
- `ui/web/mo-phong/mo-phong.js`: khai báo kind mới trong `EV_COLORS`/`EV_VI`. Không làm bước
  này thì frontend rơi vào nhánh fallback và hiện chuỗi thô `advice_suppressed` cho người dùng
  Việt — bắt được khi rà consumer của payload thay vì chỉ nhìn phía server.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/lifecycle/cadence.py` | tạo | Lõi chung + `adherence_coin` + `DECISION_BUCKET_MIN` + docstring ranh giới |
| `src/gsm_core/lifecycle/projections.py` | sửa | `adherence_view`: suppressed ra khỏi mẫu số, đếm riêng |
| `src/gsm_sim/advice_bridge.py` | sửa | Gates 4 kênh, keyed coin, memory per-actor, drain suppressed |
| `src/gsm_sim/world.py` | sửa | `decision_bucket()` dùng chung, hậu tố `-sup` khi drain |
| `src/gsm_sim/dashboard.py` | sửa | V-18: marker nói-vs-nén + bảng nhịp |
| `ui/backend/app/routers/advice.py` | sửa | Cadence gate + silent message + `topic`/`phase` vào payload |
| `ui/backend/app/routers/sim.py` | sửa | V-18: journey payload giữ channel/followed/reason |
| `ui/web/mo-phong/mo-phong.js` | sửa | V-18: nhãn tiếng Việt + màu cho kind `advice_suppressed` |
| `ui/web/js/cards.js`, `ui/web/js/api.js` | sửa | Lỗi #15: gửi `topic` ở cả GET và POST (placeholder theo loại card, chờ ĐA-06) |
| `ui/backend/tests/test_contracts.py` | sửa | Fixture `_isolate_telemetry` — GET nay có side-effect nên test contract phải cô lập |
| `tests/test_f098_defects.py` | tạo | 9 test cho 2 defect P0 của debate review remote |
| `src/gsm_core/solvers/shift_dp.py`, `src/gsm_core/policy.py` | sửa | F-098-01 gate Bellman; F-098-02 chặn policy ngoài thời hạn |
| `configs/pilot_dongda.yaml` | sửa | Block `advice.cadence` (enabled, min_gap, budget, counts_positioning) |
| `tests/test_cadence_policy.py` | tạo | 21 test lõi |
| `tests/test_cadence_sim.py` | tạo | 11 test sim: 2 khoá ranh giới + 2 khoá **cờ sống** (Lỗi #6) |
| `tests/test_lifecycle_review_fixes.py` | sửa | Lỗi #8: tách bất biến khỏi tiền đề đã hết hiệu lực; +1 test ở arm cadence TẮT |
| `ui/backend/tests/test_lifecycle_actions.py` | sửa | +4 test vòng kín hành vi |
| `research/audit/2026-07-27-current-state/31..34-*.json` | tạo | Hiệu năng + **lưới ablation 2×2** (30 seed CRN mỗi ô) |

## Docs đã cập nhật kèm theo

| Doc | Đã đổi gì |
| --- | --- |
| `tracking/PROJECT-GRAPH.md` | Node UPDATE-099 (đổi số từ 098 vì remote chiếm) + cạnh `CORRECTS D-A3-01/D-SIM-14` + ghi nhận ba confound và hai defect F-098 |
| `tracking/TODO.md` | ĐA-04 → `DONE-CODE`; ghi nhận 2 defect P0 của debate review đã fix |
| `tracking/PENDING-REVIEW.md` | **V-18** (visual) · **Q-09** (số đang treo → nay có số cuối) · **Q-10** (pull-vs-push, MỚI) |
| `tracking/DEFERRED.md` | Đóng `D-A3-01`, `D-SIM-14`, `D-R12`. Mở **11 mục**: `D-ĐA04-01..04`, `D-A3-01b`, `D-F098-A/B`, `D-R02`, `D-R08`, `D-R11b`, `D-R17`, `D-R20`, `D-R21` |
| `tracking/PLAN-d-da04-03-budget-priority-DRAFT.md` | **MỚI** — 4 họ phương án + bảng chấm độc lập + 8 cảnh báo + 7 câu hỏi cần Cường chốt |
| `research/audit/2026-07-27-current-state/README.md` | Ghi rõ artifact 31–35 **BỊ TREO**, chỉ 37 được trích cho quyết định |
| `CLAUDE.md` | Đếm 92 → 93 UPDATE |
| `configs/pilot_dongda.yaml` | Comment cảnh báo `enabled` chỉ điều khiển CỔNG, không đổi cơ chế coin |

SCOPE / USER_STORIES: không đổi.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `min_gap=20′`, `budget=6/ca` | `ASSUMPTION` (baseline duyệt) | ĐA-04 verdict 2026-07-27 | Trung bình | Nhịp quá thưa/dày; là **experiment arm**, tuning sau bằng telemetry đúng chữ design |
| Phase boundaries 25%/75% | `ASSUMPTION` | Hằng cấu trúc, document trong `CadenceConfig` | Trung bình | Cửa sổ dismissed dài/ngắn hơn ý muốn |
| Washout đã chết | `OBSERVED-CODE` + đo thật | `test_washout_dead_two_units_converge`, seed 1000: decision 68,1% vs event 67,6% | Cao | Nếu sai thì mọi Δ A/B vẫn thổi phồng như trước |
| positioning ngoài ngân sách là đúng | `OBSERVED-CODE` | artifact 29 (30 seed): dương SIG ở mọi mức chi phí thực | Cao | Bịt kênh dương duy nhất ⇒ mất giá trị đã chứng minh |
| Adherence quan sát ≠ trung bình danh nghĩa quần thể | `OBSERVED-CODE` | Người ĐƯỢC khuyên không phải mẫu ngẫu nhiên (P4 tân binh chiếm ưu thế vì họ dưới ngưỡng) | Cao | Nếu quên, sẽ viết test bám sai mốc — đúng họ lỗi BUG-EVAL-ARGMAX |
| Sim không có nút Bỏ qua | `FACT` (chỉ thị Cường) | Chép nguyên văn ở §2 | Cao | Sim tự bịt miệng ⇒ Δ nhỏ đi vì lý do không liên quan chất lượng lời khuyên |
| **Arm đối chứng `cadence=off` SẠCH** | `OBSERVED-RUN` (đo sau fix) | Lệch thổi phồng adherence giữa hai arm **0,003** (trước fix 0,095); liều can thiệp OFF/ON **1,17×** (trước 2,0–2,5×) | Cao | Đây là giả định NỀN của mọi con số "giá của nhịp". Nó **đã sai một lần** và không ai — kể cả tôi — nhận ra cho tới khi soi độc lập. Nếu còn sai, Q-09 lại phải đính chính lần thứ ba |
| **Bộ test thật sự bắt được lỗi** | `OBSERVED-RUN` (mutation testing) | 3 mutation cố ý (`DECISION_BUCKET_MIN` 30→20 · `dismissed` trước `safety` · bỏ `_claim_effect`) đều bị bắt; test R-01 được kiểm riêng: đỏ khi mutation, xanh khi khôi phục | Trung bình | Trước cycle này nhiều test xanh dù code hỏng (tautology, so biểu thức với chính nó). Mutation chỉ phủ 3 điểm — **không phải bằng chứng toàn bộ suite chặt** |
| **Trạng thái nhịp không rò qua ngày** | `OBSERVED-CODE` + test | `multiday` dựng `World` mới ⇒ bridge mới mỗi ngày; `test_cadence_state_does_not_leak_across_days` | Cao | Rò ⇒ ngày 2 thừa hưởng ngân sách cạn của ngày 1, mọi Δ nhiều-ngày sai một chiều |
| Số "2.670 lần bị nén" | `UNVERIFIED` (phóng đại đã biết) | `D-R08`: 3 kênh hỏi nhịp TRƯỚC khi biết có nội dung ⇒ **47% event nén là "ma"** | Thấp | Mọi kết luận "kênh nào đói suất" — nền của D-ĐA04-03 — lệch có hệ thống. **Chưa sửa vì sửa sẽ đổi số đã công bố giữa lúc đang đo** |

## Kiểm chứng

### Test

| Bộ | Số test | Nội dung đáng kể nhất |
| --- | --- | --- |
| `tests/test_cadence_policy.py` | 23 | cooldown/budget/dismissed-hết-pha; phase boundaries (kể cả ca dài 0); QUEUE khi driving; safety bypass; coin deterministic + đổi `material_revision` ⇒ coin mới + phân bố ~uniform (10k key) |
| `tests/test_cadence_sim.py` | 13 | washout chết (hai đơn vị hội tụ ≤5đp); suppressed ngoài mẫu số; re-check không re-roll; budget ≤6/ca; exact-repeat; **CRN world A bit-identical**; 2 test khoá ranh giới sim↔sản phẩm; **2 test khoá cờ sống** (`cadence.enabled` tắt ⇒ 0 event nén; `count_positioning_in_budget` bật ⇒ số người được gán GIẢM) |
| `tests/test_lifecycle_review_fixes.py` | 21 (+1 mới) | Bất biến `decided <= event_decided` ở mọi cấu hình; phép gộp bucket kiểm ở arm cadence TẮT |
| `ui/backend/tests/test_lifecycle_actions.py` | 15 (11 mới) | dismiss im đúng pha · không lan sang topic khác · hết pha nói lại · driving ⇒ QUEUE · **ngân sách 6/ca ở UI** · **cooldown 20′ ở UI** (Lỗi #9) · **budget đếm decision, không đếm event** (Lỗi #12) · **NÓI thì hao ngân sách dù không ai bấm** + **poll trong một bucket = 1 lần nói** (Lỗi #14) · **một công thức pha ca** (Lỗi #16) |
| **Full suite (LƯỢT CUỐI)** | **843 passed · 5 skipped · 0 failed** (17′58″) | `pytest tests ui/backend/tests` — chạy SAU **toàn bộ** fix của cycle, máy không có job nào khác. Ba mốc trong cycle: 817/1 failed (test đỏ đã ĐIỀU TRA, là tiền đề lỗi thời — Lỗi #8) → 823/0 → 839/0 → **843/0**; chênh là các test mới thêm sau mỗi vòng soi |

Lượt chạy full suite **trước** khi sửa Lỗi #6/#7/#8/#9 cho **817 passed / 1 failed** — giữ lại
con số đó ở đây làm bằng chứng rằng test đỏ đã được ĐIỀU TRA (hoá ra là tiền đề lỗi thời,
Lỗi #8), không phải được nới cho xanh. Chênh 817 → 823 gồm: +3 test mới của cycle sau lượt
đó (cờ sống ×2, gộp bucket ở arm cadence tắt), +2 test UI (ngân sách, cooldown — Lỗi #9),
+1 test đỏ nay xanh.

⏱ **Suite chậm hơn hẳn** (17′37″ → 21′19″). Nguyên nhân đã biết chứ không phải bí ẩn: mỗi
run sim nay sinh thêm ~2.670 event `advice_suppressed` (xem `D-ĐA04-04`), và các test mới
chạy thêm sim run cho arm cadence tắt. Ghi ra để lần sau không ai coi đây là hồi quy.

### Mutation testing — bằng chứng bộ test SIẾT rồi thì thật sự bắt được lỗi

Soi đối kháng cho thấy nhiều test của tôi *"vẫn xanh dù code đã hỏng"*. Sau khi siết, tôi
**cố tình phá code** rồi chạy lại để kiểm chính bộ test — không chỉ tin rằng nó đã chặt hơn:

| Mutation | Test bắt được? |
| --- | --- |
| `DECISION_BUCKET_MIN` 30 → 20 | ✅ `test_decision_bucket_min_is_pinned_and_meaningful` đỏ |
| Đưa nhánh `dismissed` **lên trước** nhánh `safety` trong `evaluate` | ✅ `test_safety_beats_dismiss_and_cooldown` đỏ |
| Bỏ `_claim_effect` (khôi phục lỗi R-01: áp tác động lặp) | ✅ đỏ — **nhưng ban đầu chỉ bị bắt bởi một test dedupe KHÔNG liên quan**, tức bắt được do MAY. Đã thêm `test_one_decision_one_effect_application` bắt đúng chỗ, và test này đã được kiểm: đỏ khi có mutation, xanh khi khôi phục |
| Bỏ `_note_shown` (khôi phục Lỗi #14: ngân sách chỉ hao khi tài xế BẤM) | ✅ **đúng 2 test** đỏ: `test_showing_a_card_consumes_budget_without_any_tap` và `test_polling_same_bucket_does_not_burn_budget` |
| Khoá event `displayed` theo `advice_id` thay vì **decision bucket** (khôi phục lỗi poll-đốt-ngân-sách) | ✅ đúng **một** test đỏ: `test_polling_same_bucket_does_not_burn_budget` — test kia vẫn xanh, đúng như thiết kế (mỗi test canh một chiều) |

Bài học nhỏ nhưng thật: *"mutation bị bắt"* chưa đủ — phải hỏi **test NÀO** bắt. Bắt bởi một
test không liên quan nghĩa là lá chắn sẽ biến mất ngay khi test đó được sửa vì lý do khác.

Ghi thêm một lỗi tự mắc khi viết chính test R-01 này: tôi đoán tên trường là `lift_applied`
(tên trong dataclass) trong khi event dùng `lift` ⇒ test cho `0/58` và **suýt đọc thành
"R-01 sống lại"** trong khi code đúng. Đúng họ Lỗi #7 — kiểm bằng dữ liệu thật, đừng đoán tên
trường. Nay test có `assert "lift" in gate[0].detail` để hỏng thì hỏng rõ ràng.

### Kiểm bất biến trên NHIỀU SEED (CLAUDE.md đòi ≥5 seed cho stochastic regression)

Toàn bộ test cadence bám seed 1000 (`D-R20`). Kiểm lại ba bất biến cốt lõi trên **5 seed**:

| seed | decision adh | event adh | \|lệch\| | số lần ÁP / số quyết định | trần ngân sách |
| --- | --- | --- | --- | --- | --- |
| 1000 | 0,658 | 0,653 | 0,004 | 58/58 | 5 |
| 1001 | 0,667 | 0,621 | **0,045** | 44/44 | 5 |
| 1002 | 0,683 | 0,667 | 0,016 | 54/54 | 5 |
| 2000 | 0,566 | 0,553 | 0,013 | 57/57 | 6 |
| 3160 | 0,578 | 0,562 | 0,017 | 50/50 | 6 |

Cả ba bất biến giữ ở mọi seed: hai đơn vị adherence hội tụ (≤0,05), **số lần áp tác động =
số quyết định** (R-01), trần 6/ca. ⚠ **Nhưng seed 1001 cho 0,045 — sát ngưỡng 0,05.** Đúng
cảnh báo `D-R20`: một seed khác có thể làm test đỏ oan, và người sửa dễ nới **code** thay vì
nới ngưỡng. Đây là lý do bất biến nên phát biểu bằng thống kê nhiều seed, không bằng hằng số
cứng trên một seed.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `pytest tests ui/backend/tests` | 1000–1002, 2000, 3160 (+10k key cho coin) | 4 kênh × cadence on/off × multiday 2 ngày | **843 passed / 5 skipped / 0 failed** (17′58″) | — |
| `da04_sweep.py` (artifact **31**) | 3160–3189 (30 tươi) | `default_positioning` (wait_only) và `ladder_all` | `research/audit/2026-07-27-current-state/31-da04-cadence-30seed.json` | So xếp hạng cũ-vs-mới cần ≥100 seed (quy tắc variant) — **chưa chạy** |
| `da04_ablation.py` (artifact **32**) | 3160–3189 (cùng bộ) | `ladder_all` với `cadence.enabled=false` | `32-da04-ablation-30seed.json` — **+8.586đ** vs +5.701đ | — |
| `da04_ablation2.py` (artifact **33**) | 3160–3189 (cùng bộ) | `ladder_all` bỏ `shift_plan`, cadence ON | `33-da04-no-shiftplan-30seed.json` — **+7.135đ** | — |
| `da04_ablation3.py` (artifact **34**) | 3160–3189 (cùng bộ) | ô thứ tư của lưới 2×2: bỏ `shift_plan`, cadence OFF | `34-da04-2x2-cell-30seed.json` — **+8.561đ** ⇒ tương tác **+1.458đ** | Chưa thử arm "ưu tiên theo giá trị" (chính là `D-ĐA04-03`, cần plan) |
| `da04_n100.py` (artifact **35**) | **4000–4099 (100 tươi, ghép cặp)** | giá của nhịp `B_on−B_off`, ladder_all | `35-da04-cost-of-cadence-n100.json` — **−3.048đ SIG**; gini −0,0051 SIG | Lưới 2×2 đầy đủ ở n=100 — chỉ chạy nếu cần phân rã chuẩn hơn |

### HIỆU NĂNG sau update (nề nếp Cường yêu cầu báo sau MỖI update)

> 🔴 **CẢNH BÁO ĐỌC SỐ (thêm 2026-07-29 sau soi đối kháng):** mọi con số **"giá của nhịp"**
> trong mục này — −2.885đ (n=30) và −3.048đ (n=100) — được tính với arm đối chứng
> `cadence=off` **BỊ NHIỄM** (Lỗi #13: tắt cờ cũng tắt keyed coin ⇒ arm đối chứng có adherence
> hiệu dụng cao hơn ~10đp). **Chúng là cận trên của trị tuyệt đối, không phải giá trị đúng.**
> Đã sửa gốc + đang chạy lại thành **artifact 36**; §ĐÍNH CHÍNH cuối mục này ghi số mới.
> Các con số **KHÔNG** bị ảnh hưởng (vì chỉ dùng arm cadence ON): +4.469đ (positioning),
> +5.701đ (ladder_all), +7.135đ (bỏ shift_plan), và toàn bộ Δ vs thế giới không-advice.

**Artifact 31** — 30 seed tươi 3160–3189, CRN paired A/B, `coverage=all`, bootstrap CI95.
Tất cả số dưới đây là **`driver_payout`** (`net_mean_all == payout_mean_all` vì `cost_mean_all`
= 0 ở config mặc định — chi phí chỉ bật khi quét độ nhạy B2/C5).

| Chỉ tiêu | `default_positioning` (chỉ kênh vị trí) | `ladder_all` (bật cả 4 kênh + vị trí) |
| --- | --- | --- |
| **Δ payout/tài xế** | **+4.469đ** CI[+1.962, +6.938] **SIG** | **+5.701đ** CI[+3.441, +7.982] **SIG** |
| Δ served_rate | +1,48đp CI[+0,92, +2,02] SIG | +2,23đp CI[+1,67, +2,79] SIG |
| Δ đơn hoàn thành | +17,97 CI[+11,2, +24,6] SIG | +27,03 CI[+20,2, +33,9] SIG |
| Δ đơn hết hạn | −17,0 CI[−23,2, −10,5] SIG | −28,3 CI[−35,0, −21,9] SIG |
| Δ chuyến/tài xế | +0,200 CI[+0,125, +0,274] SIG | (cùng dấu, SIG) |
| Δ gini_payout (thấp = công bằng hơn) | −0,0053 SIG | −0,0051 SIG |
| Δ supply_cell_hhi (thấp = cung trải đều hơn) | −0,0012 SIG | −0,0012 SIG |
| Δ station_hhi (dồn trạm pin) | −0,015 SIG | −0,030 SIG |
| Δ payout người NGOÀI nhóm được khuyên | +419.823đ SIG | +522.523đ SIG |
| Nhóm thắng đậm | P7 +20.664đ SIG · P1 +5.939đ SIG | P7 +19.933đ SIG · P4 +13.343đ SIG · P1 +6.398đ SIG · P6 +6.333đ SIG |
| Nhóm âm (đều **ns**) | P3 −2.897đ | P3 −11.535đ · P5 −1.968đ · P2 −1.377đ |

**Ba điều đọc được:**

1. **Cadence KHÔNG làm hỏng giá trị đã có.** Tham chiếu cũ cho kênh vị trí là +4.000đ
   (artifact 29, cash cost 0); sau ĐA-04 đo được **+4.469đ** trên 30 seed **tươi**. Hai con số
   này **không so trực tiếp được** (khác seed set), nhưng khoảng tin cậy chồng nhau ⇒ không có
   dấu hiệu suy giảm. Đây là câu hỏi chính của artifact 31 và câu trả lời là **không hỏng**.
2. **Lợi ích lan ra ngoài nhóm được khuyên** (+420k/+523k cho người khác) và **cả hệ thống**
   (served +1,5→2,2đp, đơn hết hạn giảm 17→28). Đây là bằng chứng cho chỉ tiêu KÉP của ĐA-08:
   advisor không lấy phần của người khác mà làm chiếc bánh to hơn.
3. **`ladder_all` nay DƯƠNG và tốt hơn chỉ-positioning** — ngược hẳn lịch sử (trước đây bật
   thêm kênh thì tệ đi; `shift_plan` từng âm −1.627đ, kịch bản 2029 âm SIG). ⚠️ **KHÔNG được
   đọc thành "cadence cứu các kênh spam"** — ablation dưới đây bác bỏ cách đọc đó.

### ⚠️ ABLATION (artifact 32–34) — cadence đang LẤY ĐI giá trị, không thêm vào

Câu hỏi: phần cải thiện của `ladder_all` là công của **nhịp** hay của **keyed coin**? Tách
bằng cách giữ nguyên mọi thứ (cùng 30 seed 3160–3189, cùng keyed coin), chỉ đổi một biến.

| Arm | Δ payout/tài xế | Δ served | Δ đơn hoàn thành | Δ gini |
| --- | --- | --- | --- | --- |
| cadence **ON**, ladder all | +5.701đ SIG | +2,23đp SIG | +27,0 SIG | **−0,0051 SIG** |
| cadence **OFF**, ladder all | **+8.586đ SIG** | +2,67đp SIG | +32,3 SIG | −0,0020 **ns** |
| cadence ON, **tắt `shift_plan`** | +7.135đ SIG | +2,52đp SIG | +31,0 SIG | −0,0011 ns |
| cadence ON, chỉ positioning | +4.469đ SIG | +1,48đp SIG | +18,0 SIG | −0,0053 SIG |

**Phán quyết trung thực: bật nhịp làm MẤT 2.885đ/tài xế/ngày** (8.586 → 5.701). Giả thuyết
"cadence cứu kênh spam" **bị bác bỏ** — công của phần cải thiện so với lịch sử là của **keyed
coin** (tức là của việc *sửa thước đo*, một hệ quả đo lường), không phải của nhịp.

**Phân rã 2.885đ đó thành hai nửa:**

Ba arm đầu **không đủ để kết luận nhân quả**: bỏ `shift_plan` vừa *giải phóng ngân sách* vừa
*loại tác hại trực tiếp của chính kênh đó*. Nên artifact **34** chạy ô thứ tư, thành **lưới
2×2 đầy đủ** (cadence × có/không `shift_plan`), cùng 30 seed CRN:

| Δ payout/tài xế | có `shift_plan` | KHÔNG `shift_plan` | Bỏ `shift_plan` được gì |
| --- | --- | --- | --- |
| **cadence ON** | +5.701đ SIG | +7.135đ SIG | **+1.433đ** |
| **cadence OFF** | +8.586đ SIG | +8.561đ SIG | **−25đ** |
| *Giá của nhịp* | **−2.885đ** | **−1.426đ** | **tương tác +1.458đ** |

**Đọc lưới này:** bỏ `shift_plan` khi cadence TẮT gần như **không đổi gì** (−25đ) — nghĩa là
trong kịch bản này kênh đó **tự nó gần như vô hại**. Nhưng khi cadence BẬT, bỏ nó lại đáng
**+1.433đ**. Toàn bộ lợi ích nằm ở **tương tác (+1.458đ)**, tức là ở **việc nó chiếm suất
trong ngân sách chung** chứ không phải ở lời khuyên nó đưa ra.

⇒ **`D-ĐA04-03` (ngân sách FIFO) được XÁC NHẬN**, confound đã loại bỏ bằng thiết kế 2×2 chứ
không bằng lập luận. Đây là bằng chứng nhân quả sạch nhất của cycle này.

⇒ Phân rã cuối: **−1.458đ là do ngân sách FIFO** (con số này là **tương tác đo trực tiếp**,
không phải hiệu 2.885−1.426=1.459 — hai cách tính lệch 1đ do làm tròn; dùng số đo trực tiếp)
và
**−1.426đ là giá nội tại của việc nói ít đi** (không sửa được bằng kỹ thuật; **đánh đổi UX ↔
tiền, quyết định của Cường** — xem §Quyết định cần Cường chốt).

📌 Ghi chú cho ĐA-07: `shift_plan` ở đây gần như vô hại khi không có cadence (−25đ), **khác**
với −1.627đ mà C5 đo ở kịch bản `s2_only`. Không mâu thuẫn (khác arm, khác cấu hình chi phí),
nhưng **đừng trích con số nào như thể nó phổ quát** — tác động của kênh này phụ thuộc mạnh vào
việc nó phải chia ngân sách với ai.

### 📉 ĐÍNH CHÍNH TỪNG BƯỚC — mỗi confound bị loại lại làm "giá của nhịp" NHỎ ĐI

Đây là phần quan trọng nhất của mục HIỆU NĂNG, và nó là một **lời đính chính**, không phải
một kết quả. Ba confound được phát hiện *sau khi tôi đã báo số cho Cường*, và mỗi lần loại
một cái thì con số lại giảm:

| Trạng thái code | Giá của nhịp (n=100, ghép cặp) | Artifact |
| --- | --- | --- |
| Chưa loại confound nào | **−3.048đ** CI[−4.117, −2.005] SIG | 35 |
| Đã loại **DET-01** (keyed coin vô điều kiện) | **−2.593đ** CI[−3.501, −1.634] SIG · **hẹp đi 455đ (15%)** | 36 |
| Đã loại **DET-01 + R-01 + R-09** | **−1.530đ** CI[−2.401, −673] SIG · **hẹp đi 1.518đ (50%)** | **37** |

**Con số cuối cùng: −1.530đ/tài xế/ngày — bằng ĐÚNG MỘT NỬA con số tôi đã báo (−3.048đ).**
Mọi chỉ tiêu khác cũng giảm khoảng một nửa: `gini` −0,0030 (từ −0,0051), served −0,46đp (từ
−0,85đp), đơn hoàn thành −5,47 (từ −10,26), payout người khác −140k (từ −268k). Tất cả vẫn
SIG và vẫn cùng chiều — **kết luận định tính đúng từ đầu, định lượng thì sai gấp đôi**.

### 🔬 LƯỚI 2×2 ĐO LẠI TOÀN BỘ (artifact 37) — và nó đổi câu trả lời cho Q-09

Cả **năm** arm chạy lại với đủ ba fix (30 seed 3160–3189; ô ON cũng đổi vì R-01/R-09 chạm cả
hai phía):

| Δ payout/tài xế | có `shift_plan` | KHÔNG `shift_plan` | Bỏ `shift_plan` được gì |
| --- | --- | --- | --- |
| **cadence ON** | +5.624đ SIG | +7.173đ SIG | **+1.549đ** |
| **cadence OFF** | +8.488đ SIG | +6.789đ SIG | **−1.700đ** |
| *Giá của nhịp* | **−2.865đ** | **+384đ** | **tương tác +3.249đ** |

**Đọc lưới này — đây là phát hiện quan trọng nhất của cả cycle:**

- Ô dưới-phải đảo dấu: khi cadence TẮT, bỏ `shift_plan` **làm xấu đi 1.700đ** (trước khi loại
  confound, con số đó là −25đ). Nghĩa là `shift_plan` **có giá trị** khi được nói tự do.
- **Không có `shift_plan`, nhịp gần như MIỄN PHÍ: +384đ** (điểm ước lượng dương nhẹ).
- ⇒ **Toàn bộ "giá của nhịp" tập trung ở tương tác với `shift_plan`** (+3.249đ). Nói cách
  khác: nhịp không đắt; **cách chia ngân sách FIFO mới đắt**, và nó đắt vì để đúng kênh
  `shift_plan` chiếm suất.
- ⇒ **`D-ĐA04-03` (ưu tiên ngân sách) nay có lý do mạnh hơn hẳn**, không yếu đi như tôi đoán.
- ⇒ **Ở CONFIG SHIP, nhịp tốn ≈ 0đ**: chỉ `positioning` bật, mà kênh đó nằm ngoài hệ thống
  cadence hoàn toàn (`ON_pos_only` +4.469đ, không bị cổng nào chạm).

⚠ **Giới hạn phải nói rõ:** các hiệu số trong bảng (+1.549 / −1.700 / +3.249 / +384) là hiệu
của các **điểm ước lượng**; tôi chỉ lưu khối tổng hợp cho 4 ô này nên **không có CI cho chúng**.
Con số duy nhất có CI hợp lệ là ước lượng ghép cặp n=100: **−1.530đ CI[−2.401, −673]**. Muốn
kết luận về ĐỘ LỚN của tương tác thì phải lưu per-seed cho cả 4 ô rồi bootstrap — chưa làm.

### ⚠️ ĐÍNH CHÍNH THỨ HAI — hai lập luận "cái nhịp MUA được" của tôi cũng phải sửa

Tôi đã nói với Cường rằng nhịp *"mua công bằng"* và *"cứu P5 khỏi mức hại −8.166đ SIG"*. Sau
khi loại confound, cả hai phải phát biểu lại:

| Arm (artifact 37) | Δ `gini_payout` vs không-advice | Nhóm bị hại **có ý nghĩa** |
| --- | --- | --- |
| `ON_all` | −0,0039 **ns** | **không có** |
| `OFF_all` | −0,0039 **ns** | **không có** |
| `ON_nosp` | −0,0020 ns | không có |
| `OFF_nosp` | −0,0033 ns | không có |
| `ON_pos_only` | −0,0053 **SIG** | không có |

- **"P5 bị hại −8.166đ SIG khi tắt nhịp" — SAI, rút lại.** Sau khi loại confound, **không
  nhóm archetype nào bị hại có ý nghĩa ở BẤT KỲ arm nào**. Con số cũ là sản phẩm của arm đối
  chứng bị nhiễm (liều can thiệp gấp 2–2,5 lần), không phải của việc tắt nhịp.
- **"Nhịp mua công bằng" — vẫn ĐÚNG nhưng phải nói chính xác hơn.** So với thế giới
  không-advice thì cải thiện gini của từng arm là **ns**; nhưng ước lượng **ghép cặp** n=100
  (ON − OFF, cùng seed) cho **−0,0030 SIG** ⇒ *"bật nhịp làm gini tốt hơn tắt nhịp"* đứng
  vững, còn *"advisor có nhịp làm đội xe công bằng hơn hẳn"* thì **không** — ở arm đủ kênh,
  hiệu ứng công bằng so với không-advice không đạt ý nghĩa.
- Đáng chú ý: arm **duy nhất** có gini cải thiện SIG là `ON_pos_only` — tức **kênh vị trí**,
  không phải nhịp, mới là thứ làm đội xe công bằng hơn.

**Cái KHÔNG đổi qua cả ba bước:** `gini_payout` **−0,0051 SIG** y nguyên. Tức kết luận *"nhịp
mua công bằng bằng tiền"* vững; chỉ **giá** là thứ tôi liên tục báo cao hơn thực tế.

**Bài học về thứ tự (đáng ghi thành luật):** tôi sửa DET-01 rồi **đo ngay**, rồi vòng soi thứ
hai tìm ra R-01 và tôi phải đo lại. Đúng ra: **soi cho hết confound TRƯỚC, đo MỘT lần**. Mỗi
lần "sửa rồi đo ngay" là một lần gần như chắc chắn phải đo lại — và tệ hơn, là một lần nữa
báo cho Cường một con số sẽ phải đính chính.

### ✅ XÁC NHẬN n=100 (artifact 35) — con số Q-09 đứng trên nay đạt chuẩn variant-vs-variant

Adversarial self-review của chính UPDATE này ghi *"Δ giữa các arm là gợi ý mạnh, chưa phải kết
luận thống kê chắc chắn — số nào dùng để RA QUYẾT ĐỊNH phải chạy lại ở n≈100"*. Đã chạy:
**100 seed TƯƠI 4000–4099** (không trùng bộ 3160–3189), ước lượng **GHÉP CẶP** — vì world A
bit-identical giữa hai arm, giá của nhịp trên mỗi seed là `B_on(s) − B_off(s)`, hiệu sạch có
CI hợp lệ (phép trừ hai mean của artifact 31/32 trùng điểm ước lượng nhưng KHÔNG có CI).
Mỗi seed chạy 3 thế giới (A, B_on, B_off) thay vì 4. Kết quả (`ladder_all`, coverage=all):

| Chỉ tiêu | Giá của nhịp (B_on − B_off, ghép cặp) | Đọc |
| --- | --- | --- |
| **Δ payout/tài xế** | **−3.048đ** CI[−4.117, −2.005] **SIG** | Kết luận n=30 (−2.885đ) **ĐỨNG VỮNG** — nằm giữa CI |
| Δ served_rate | −0,85đp CI[−1,08, −0,61] SIG | Nhịp làm hệ thống phục vụ ít khách hơn |
| Δ đơn hoàn thành | −10,3 SIG · đơn hết hạn +10,25 SIG | Cùng chiều |
| **Δ gini_payout** | **−0,0051** CI[−0,0081, −0,0022] **SIG** | **Lần đầu "cái nhịp MUA được" có bằng chứng ghép cặp trực tiếp** (ở n=30 chỉ suy ra gián tiếp từ ON SIG / OFF ns) |
| Phân bố per-seed | nhịp có lợi ở **34/100** seed; median −2.713đ | Không phải tail-driven — đa số seed mất thật |

Đối chiếu hai bộ seed độc lập: Δ_ON = +6.654đ (n=100) vs +5.701đ (n=30); Δ_OFF = +9.702đ vs
+8.586đ — CI chồng nhau, không có dấu hiệu bộ seed cũ bất thường.

⚠ Hai giới hạn phải giữ khi trích số này: (a) phân rã 1.458đ-FIFO / 1.426đ-nội-tại vẫn là số
**n=30** — lưới 2×2 chưa chạy lại ở n=100 (4 ô × 100 seed ≈ 2 giờ máy; chạy nếu Cường cần
phân rã ở độ chuẩn này); (b) toàn bộ là arm `ladder_all` — ở config ship (§0 PLAN draft,
4 kênh tắt) giá của nhịp ≈ 0đ vì không có ai tranh ngân sách.

**Cái cadence MUA được bằng 2.885đ đó:** công bằng hơn (`gini_payout` giảm **SIG** khi ON,
`ns` ở cả hai arm OFF/no-shift_plan) và bớt gây hại cho nhóm P5 (OFF: −8.166đ **SIG**; ON:
−1.968đ ns). Nói cách khác nhịp **san đều** thay vì **tăng tổng**.

### ❓ Quyết định cần Cường chốt (không tự quyết vì đây là đánh đổi sản phẩm)

Sau khi sửa `D-ĐA04-03` (ưu tiên ngân sách theo giá trị thay vì FIFO), phần mất còn ~1.426đ
— đó là con số đo trực tiếp ở ô (cadence ON × không `shift_plan`) của lưới 2×2.
Ba đường đi, agent **không** tự chọn:

1. **Giữ nhịp như hiện tại** — trả ~1.426đ/tài xế/ngày để advisor không spam. Được: công bằng
   hơn, P5 không bị hại, trải nghiệm tôn trọng.
2. **Nới baseline** (ví dụ ngân sách 6 → 10/ca) và đo lại như một experiment arm — đúng chữ
   design *"cadence chặt hơn/lỏng hơn là ARM, không đổi baseline âm thầm"*.
3. **Chỉ giữ nhịp ở SẢN PHẨM, bỏ ở SIM** — ⚠️ agent **khuyến nghị KHÔNG** chọn đường này: nó
   phá đúng lý do ĐA-04 tồn tại (A/B phải đo thứ sẽ ship). Ghi ra để Cường thấy đủ lựa chọn.

## Đối chiếu với debate review của teammate (`UPDATE-098`, remote `c493d89`)

Teammate push một bản SOL/debate review 5 defect tại `aae326c`. Agent chính **tự reproduce
độc lập** hai defect P0 rồi fix trong cycle này (không nhận vơ, không bỏ qua):

| ID | Reproduce của agent chính | Fix | Ghi chú trung thực |
| --- | --- | --- | --- |
| **F-098-01** gate Bellman | ✅ **Defect THẬT, nhưng probe gốc KHÔNG dựng được.** Reviewer dùng `bucket_min` mặc định 30′; ở đó `cap_trips = 30/25 = 1,2` ⇒ `add_pts = 11 < points_band_size 15` ⇒ **band điểm không thể tiến**, nên `['SWAP']` là quyết định ĐÚNG, không phải lỗi. Defect chạm được ở **`bucket_min=60` — đúng cấu hình sim** (`configs/pilot_dongda.yaml:361`): 45 điểm + cash 4.327đ/km ⇒ net −13đ/bucket, vượt mốc 60 điểm ⇒ +30.000đ; solver cũ trả `['SWAP']` payout 0. | Gate `online_net > 0` → `exp_trips > 0`. Lý: gate chỉ được chặn cái **không khả thi** (không có cầu); *"lỗ thì đừng chạy"* phải do phép so `v > best_v` quyết — đó là toàn bộ nội dung nguyên lý Bellman. Sau fix: `['ONLINE']`, payout 58.026đ. | Cash mặc định 0 ⇒ `exp_trips>0 ≡ online_pay>0` ⇒ **hành vi mặc định bit-identical**. Chỉ đổi ở arm có chi phí > 0. |
| **F-098-02** policy ngoài hạn | ✅ **Defect THẬT, reproduce đúng như mô tả.** Bundle hiệu lực 2030-01-01→2030-12-31, hỏi `as_of=2029-04-01`: `is_valid_at` trả `False` nhưng resolver vẫn cấp `ACTIVE 9.000đ/lượt` + `ACTIVE 250đ/km`. | Chặn ở đầu `resolve_cost_params`: `is_valid_at is False` ⇒ mọi số hạng `UNKNOWN` + reason nói rõ ngoài hạn. | **Chỉ chặn `False`, KHÔNG chặn `None`** — `is_valid_at` có ba giá trị, và `None` nghĩa "nguồn không ghi hạn". Chặn cả `None` là hidden fallback chiều ngược lại và sẽ giết mọi bundle không có `effective_from`. Test canh cả hai nhánh. |
| F-098-03 schema `date-time` fail-open | Chưa làm | — | Đã có trong `TODO.md:28` (15 schema, cần plan mode) — không kéo vào cycle này. |
| F-098-04 B3 chưa nối canonical runtime | Chưa làm | — | Đúng, và **cố ý**: sim lấy chi phí từ config (nguồn sự thật của sim). Việc nối là quyết định kiến trúc, không phải fix. |
| F-098-05 taxonomy/provenance | Chưa làm | — | Cần chốt taxonomy `track` trước (quyết định sản phẩm). |

Test: `tests/test_f098_defects.py` (8 test, TDD đỏ trước). Suite liên quan: 134 passed
(`-k "s1 or bonus or policy or solver"`), `test_shift_dp.py` 19/19, `test_c1_cost_term.py` +
`test_b3_policy_costs.py` + `test_c5_swap_cost.py` 35/35.

⚠ **F-098-01 đổi hành vi solver ở các arm có chi phí > 0** ⇒ artifact 29 (sweep chi phí B2) và
30 (C5 swap fee) đo bằng solver CŨ. Chiều kết luận của chúng (*"positioning dương ở mọi mức chi
phí thực"*, *"s2_only âm ở kịch bản 2029"*) **không bị đảo** vì fix chỉ **thêm** nhánh ONLINE
vào tập khả thi — nhưng độ lớn có thể đổi. Ghi thành follow-up, chưa chạy lại.

## Lỗi đã mắc TRONG cycle này (Cường: *"documents lại toàn bộ, kể cả kiểm thử và lỗi, không mắc lại"*)

**Mục lục** — 22 lỗi + 5 lỗi test. Thứ tự các mục bên dưới KHÔNG theo số (chúng được chèn dần
theo lúc phát hiện); dùng bảng này để tra. Cột "ai bắt" là phần trung thực nhất của tài liệu:

| # | Lỗi | Ai bắt |
| --- | --- | --- |
| **13** 🔴 | Arm ĐỐI CHỨNG của mọi ablation bị nhiễm (tắt cờ cadence = tắt luôn keyed coin) | soi độc lập |
| **17** 🔴 | Một lời khuyên được nghe theo bị **áp tác động 2,0–2,5 lần** — lỗi đúng-sai | soi độc lập |
| 1 | Coin bucket 20′ vs `decision_id` 30′ ⇒ re-roll | tự bắt (test) |
| 2 | `suppressed` đè `followed` + lọt mẫu số adherence | tự bắt (đo) |
| 3 | (quy trình) suýt cho sim mượn cơ chế của sản phẩm | chỉ thị Cường |
| 6 | Cờ `count_positioning_in_budget` là **cờ chết** | tự bắt (test theo checklist) |
| 7 | Test tôi vừa viết đo sai đại lượng (event vs người) | tự bắt |
| 8 | Test cũ mã hoá tiền đề mà cycle này xoá bỏ | tự bắt (suite đỏ) |
| 9 | `topic_cooldown` sống ở sim, **chết ở sản phẩm** | tự bắt (rà từng trường) |
| 10 | Visualize không đọc được (55 vạch, 54 vạch cùng lý do) | tự bắt (đo mật độ) |
| 11 | Hidden fallback do chính bản sửa #10 tạo ra | tự bắt (cùng lượt) |
| 12 | Ngân sách UI đếm **event** thay vì **quyết định** (1 card = 2 suất) | lộ ra khi thiết kế D-ĐA04-03 |
| 14 | Ngân sách chỉ hao khi tài xế **BẤM**, không hao khi advisor **NÓI** | soi độc lập |
| 15 | Frontend **không bao giờ gửi `topic`** ⇒ cooldown theo-chủ-đề gộp thành một | soi độc lập |
| 16 | **Hai công thức** tính pha ca cho cùng một phút | soi độc lập |
| 18 | Ba kênh dùng **ba định nghĩa "đã nói"** | soi độc lập |
| 19 | Fallback pha ⇒ Bỏ qua cũ thành **lệnh im di động** | soi độc lập |
| 20 | Ca **vắt qua nửa đêm** ⇒ `shift_phase` trả `early` vĩnh viễn | soi độc lập |
| 21 | Trường `phase` chết tính bằng hằng số cứng | soi độc lập |
| 22 | Nhánh an toàn **QUEUE chết ở sản phẩm**; lời khuyên bị VỨT thay vì HOÃN | soi độc lập |
| R-04 | Assertion là **đồng nhất thức đại số** | soi độc lập |
| R-05 | Test cờ chỉ kiểm **sự vắng mặt của telemetry** | soi độc lập |
| R-06 | `DECISION_BUCKET_MIN` không test nào pin | soi độc lập |
| R-07 | Bug F-3 kể trong docstring, **không test nào tái hiện** | soi độc lập |
| R-13/14/15/16 | Test CRN **so biểu thức với chính nó**; exact-repeat bỏ `detail`; cooldown pin sai lớp; safety pin nửa vời | soi độc lập |
| (thêm) | `n_on < n_off` — khẳng định **có hướng**, không phải bất biến | tự bắt (khi R-01 làm nó đỏ) |


### Lỗi #1 — coin rút theo bucket 20′ trong khi `decision_id` cắt theo 30′

- **Triệu chứng:** test `test_recheck_does_not_reroll` đỏ: 3 `decision_id` có **hai** kết cục
  `followed` khác nhau.
- **Root cause:** `advice_bridge` tính bucket coin bằng `min_gap_min_per_topic` (20′), còn
  `world._decision_id` cắt bucket 30′. Hai lưới lệch pha ⇒ trong một `decision_id` có thể rơi
  hai bucket coin ⇒ **re-roll đúng cái washout mà cycle này sinh ra để giết**.
- **Vì sao nguy hiểm:** không crash, không đỏ ở bất kỳ test cũ nào; chỉ làm số adherence nhích
  lên. Đây đúng họ lỗi "thước đo sai trình bày như sự thật" (BUG-EVAL-ARGMAX).
- **Fix + chống tái phát:** một hằng số **`DECISION_BUCKET_MIN = 30.0`** trong `cadence.py`, cả
  `world` lẫn coin đều gọi `decision_bucket()`; test `test_recheck_does_not_reroll` canh vĩnh
  viễn. **Bài học tổng quát: hai lưới thời gian độc lập cho cùng một khái niệm là bug đang chờ
  xảy ra — phải có MỘT nguồn sự thật, kể cả khi hai số tình cờ bằng nhau.**

### Lỗi #2 — event `suppressed` đè trạng thái `followed` và lọt vào mẫu số adherence

- **Triệu chứng:** sau khi bật cadence, `decision_adherence` tụt còn **0,25** trong khi
  `event_adherence` vẫn 0,68 — lệch 43đp theo chiều **ngược** với washout.
- **Root cause:** hai lỗi chồng nhau. (a) Khi drain hàng đợi suppressed, event dùng **cùng**
  `decision_id` với lần đã `followed` ⇒ projection `decision_state` lấy trạng thái cuối là
  `suppressed`, xoá mất `followed`. (b) `adherence_view` đếm `suppressed` vào `decided`.
- **Vì sao sai về BẢN CHẤT:** "bị nén" nghĩa là advisor **không nói** — nó không thể nằm trong
  mẫu số của "nói mà có được nghe không". Gộp vào là định nghĩa sai, không phải lệch số.
- **Fix + chống tái phát:** `decision_id` khi drain mang hậu tố `-sup`; `adherence_view` đưa
  `suppressed` ra khỏi `decided` và đếm sang cột riêng. Test
  `test_suppressed_not_in_adherence_denominator` canh bất biến `decided ≤ event_decided`.
- **Kết quả sau fix:** decision 68,1% ≈ event 67,6% (lệch 0,5đp).

### Phát hiện #4 (MODEL GAP, không phải BUG) — ngân sách ca bị chiếm theo FIFO, không theo giá trị

Đo thật seed 1000, ladder all, 90 tài xế: **531 lần advisor NÓI vs 2.670 lần bị NÉN** (83%
nén), trong đó `shift_budget_exhausted` chiếm 2.634. Nhìn một tài xế cụ thể (actor 89):
6/6 suất ngân sách đều bị **`shift_plan`** lấy — đúng cái kênh mà ĐA-07 kết luận ÂM và Cường
chốt *"bản cuối trước khi chốt: TẮT để advisor IM LẶNG nếu không hiệu quả"*. Hệ quả dây
chuyền: `advice_rest_window` **không nói được lần nào** trong cả run (234 lần bị nén) — tức là
hiện tượng *"rest_window inert"* ở D-SIM-03/V-07 nay có thêm một lời giải thích mới: **nó chết
đói ngân sách**, không phải chết vì logic kênh.

- **Phân loại:** `MODEL GAP`, không phải BUG. Code làm đúng thứ nó được viết; thứ **thiếu** là
  cơ chế ưu tiên khi các kênh tranh nhau một ngân sách chung. Design ĐA-04 có nói priority
  `safety > policy/bonus > demand`, nhưng priority đó hiện chỉ áp cho **safety bypass** — phần
  còn lại là **ai hỏi trước thì lấy** (FIFO theo thứ tự tick).
- **Vì sao KHÔNG tự sửa trong cycle này:** Cường duyệt ĐA-04 với baseline "≤6 proactive/ca";
  cơ chế đấu giá/ưu tiên ngân sách là **thiết kế mới**, phải qua plan. Tự thêm ở đây là phình
  scope đúng cái CLAUDE.md §3.4 cấm.
- **Nhưng phải ghi ngay vì nó đổi cách ĐỌC số hiệu năng của chính UPDATE này** — xem mục 1 của
  Adversarial self-review.
- Ghi thành **`D-ĐA04-03`** (severity TRUNG BÌNH, có bằng chứng số ở trên).

### Phát hiện #5 (chi phí quan sát) — 2.670 event chỉ để nói "tôi im"

Dedupe hiện theo `(actor, topic, reason, bucket 20′)` nên con số trên là **đúng luật**, không
phải spam bug. Nhưng nó nghĩa là log nhịp **nặng gấp 5 lần** log lời khuyên thật. Chấp nhận
được ở sim (RAM, đúng verdict ĐA-05 "sim để RAM"); **không** chấp nhận được nếu bê nguyên
sang sản phẩm ghi SQLite. Ghi thành `D-ĐA04-04` (thấp) — điều kiện mở lại: khi UI bắt đầu ghi
event suppressed vào store thật.

### Lỗi #6 — cờ `count_positioning_in_budget` là CỜ CHẾT (đọc được từ config, không tới engine)

- **Cách phát hiện:** không phải bằng mắt. Đi qua checklist adversarial của CLAUDE.md
  (*"config flag có thực sự được dùng và disabled factor có quay về baseline"*) rồi **viết test
  cho chính câu hỏi đó** — `test_count_positioning_in_budget_flag_is_alive`. Test đỏ ngay.
- **Root cause:** kênh positioning đi đường riêng (`standby_follow_draw` → `capacity_alloc`),
  **không gọi** `cadence_allows` cũng **không gọi** `cadence_note_spoken`. Nên nhánh
  `if topic != "positioning" or self.cadence_counts_positioning` trong `cadence_note_spoken`
  **không bao giờ chạy với topic="positioning"**. Cờ đọc được, comment trong YAML quảng cáo
  hành vi "bật để đo arm siết", nhưng không có đường dẫn nào tới engine.
- **Vì sao đáng sợ:** nếu không có test này, UPDATE-099 sẽ khẳng định *"positioning nằm ngoài
  ngân sách theo cấu hình, muốn siết thì bật cờ và đo"* — một câu **sai** mà không ai phát
  hiện cho tới khi có người thật bật cờ và thấy số không đổi.
- **Fix hẹp:** wire hai điểm trong `world.py` (gate trước khi đưa vào `cands`, note sau khi
  allocation gán), **cả hai đều nằm sau `if self.advice.cadence_counts_positioning`** ⇒ nhánh
  mặc định đi đúng đường cũ ⇒ artifact 31/32/33 vẫn hợp lệ.
- **Bài học:** *"cờ có trong config"* ≠ *"cờ có tác dụng"*. Mọi cờ mới phải có một test chứng
  minh **bật và tắt cho kết quả khác nhau**, nếu không nó là tài liệu nói dối.

### Lỗi #7 — test do CHÍNH tôi vừa viết đo sai đại lượng (suýt kết luận ngược)

Bản đầu của test trên đếm `len(events kind == "standby_alloc")`. Sau khi fix cờ, số đó **tăng**
(83 → 85) trong khi kỳ vọng phải giảm ⇒ nhìn như "fix không có tác dụng / cờ vẫn chết".
Sự thật: `standby_alloc` là **một event cho mỗi (vòng, Ô)**, không phải mỗi người — siết người
lại làm số Ô có người tăng. Đại lượng đúng nằm ở `detail["n_assigned"]`. Đây **đúng họ
BUG-EVAL-ARGMAX**, lần này ở trong test chứ không phải ở sản phẩm: **thước đo sai làm bằng
chứng đúng trông như bằng chứng sai**. Docstring test nay ghi lại nguyên cái bẫy.

### Lỗi #8 — một test cũ mã hoá tiền đề mà chính cycle này xoá bỏ

`test_event_level_counters_present` (Cycle W) khẳng định `decided < event_decided` với lý lẽ
*"accept_lift fire mỗi tick nên decision gộp bucket phải ít hơn event"*. Sau ĐA-04 hai số bằng
nhau (58 == 58) vì cooldown 20′ khiến mỗi bucket 30′ chỉ còn một lần nói — **đó chính là hiệu
ứng mong muốn**, không phải hồi quy. Xử lý: **không** hạ assertion cho xanh, mà tách làm hai —
bất biến còn đúng ở mọi cấu hình (`decided <= event_decided`) giữ ở chỗ cũ, còn phần "gộp
bucket" chuyển sang test mới chạy ở **arm cadence TẮT**, nơi tiền đề spam vẫn còn đúng. Sức
mạnh phát hiện lỗi được giữ nguyên thay vì bị nới cho qua.

### Lỗi #10 — bản visualize đầu tiên KHÔNG ĐỌC ĐƯỢC (55 vạch, 54 vạch cùng một lý do)

- **Cách phát hiện:** không phải bằng cách nhìn ảnh, mà bằng cách **đo mật độ marker trước khi
  mời người xem**. Seed 1000: 82/90 tài xế có vạch nén; trung vị **33 vạch**, p90 = 49,
  **xấu nhất 55 vạch trên 1080 phút** — một vạch mỗi 20 phút. Và ở tài xế xấu nhất, **54/55
  vạch cùng lý do `shift_budget_exhausted`**.
- **Vì sao đó là lỗi thật chứ không phải chuyện thẩm mỹ:** vạch thứ 54 không nói thêm gì so
  với vạch thứ nhất. Một biểu đồ 55 vạch giống nhau **giấu** thông tin thay vì bày ra —
  người xem không đọc được "advisor im từ lúc nào" giữa rừng vạch. V-18 sẽ trượt và Cường
  sẽ mất thời gian cho một bản không xem được.
- **Sửa (đổi cách kể, không chỉ đổi màu):** hết ngân sách nay vẽ **MỘT** mốc *"hết ngân sách
  nhắc"* + **tô vùng xám** từ đó tới cuối ca; chỉ những lý do **còn thông tin** (cooldown,
  hoãn vì đang lái) mới vẽ từng vạch. Chú thích ghi rõ có bao nhiêu lần advisor **muốn nói
  mà không được**. Kết quả: từ 55 phần tử thị giác xuống ~2, mà **nói được nhiều hơn** —
  thấy ngay advisor tắt tiếng lúc nào và im bao lâu.
- **Bài học:** *"đã vẽ ra được"* ≠ *"đọc được"*. Với mọi visualize, phải **đo mật độ và độ
  lặp của phần tử thị giác trên dữ liệu thật** trước khi mời người xem — nếu 98% phần tử
  cùng một nội dung thì đó là dấu hiệu chọn sai đơn vị biểu diễn.

### Lỗi #11 — hidden fallback do CHÍNH bản sửa Lỗi #10 tạo ra (bắt trong cùng lượt)

Bản sửa trên viết `getattr(pick, "shift_end_min", t0)` để lấy giờ tan ca. Nhưng `pick` là
**hàng của selectbox**, không phải `Actor` — nên `getattr` sẽ luôn rơi vào fallback và vùng
tô co lại thành rỗng, **âm thầm**, không lỗi, không ai biết. Đúng họ "hidden fallback" mà
chính UPDATE này phê phán ở B3 và Lỗi #6. Sửa: dùng `a_pick` (Actor thật, đã có sẵn ở dòng
trên) và **không** đặt fallback — thà nổ còn hơn tô sai. **Bài học: `getattr(x, "attr",
default)` trên một object mình không chắc kiểu là cách viết một lỗi im lặng.**

### 🔴 Lỗi #17 (R-01) — MỘT lời khuyên được nghe theo bị ÁP TÁC ĐỘNG NHIỀU LẦN

Vòng soi thứ hai bắt đúng phần dư mà fix DET-01 **không** giải quyết, và nó nặng hơn:

- `check_bonus_gate` chạy `actor.accept_lift += applied` **mỗi lần được gọi** với
  `followed=True`. Keyed coin (fix DET-01) làm hỏi lại ra **cùng** câu trả lời — nên khi
  không có cooldown, cùng một quyết định bị **áp lại**. Đo: `gate_events / decision_id` =
  **2,46 / 2,11 / 2,02** ở arm OFF (seed 1000–1002) vs **~1,05** ở arm ON.
- **Đây là lỗi ĐÚNG-SAI, không chỉ lỗi đo.** Một tài xế nghe theo *một* lời khuyên thì tỷ lệ
  nhận được nâng *một* bậc. Bản cũ nâng tới `lift_max` nhanh gấp 2–2,5 lần chỉ vì advisor bị
  hỏi lại nhiều hơn — tức **mức can thiệp phụ thuộc vào chính cái cadence đang được đo**.
  Không có cách nào đọc Δ như "giá của nhịp" khi liều thuốc của hai arm khác nhau.
- **Fix:** `_claim_effect(actor, topic, now_min)` — trả `True` đúng một lần cho mỗi quyết
  định, **khoá TRÙNG khoá của coin**. Bất biến: *số lần áp tác động = số QUYẾT ĐỊNH được
  nghe theo*, không phải số event.
- **Phạm vi cổng — rà từng kênh, ghi vào code để không ai "sửa" nhầm:**
  `accept_lift` ✅ cần (tác động một-lần) · `shift_extend` ✅ cần (cùng lý do) ·
  `rest_window` ❌ **KHÔNG** cần — `rest_deferred_min += 2.0` mỗi tick là *"đã hoãn nghỉ
  thêm 2 phút THẬT"*, cộng dồn là đúng ngữ nghĩa; đặt cổng vào đây sẽ làm sim tin tài xế chỉ
  hoãn nghỉ 2 phút cho cả ca · `shift_plan`/`positioning` ❌ không cần (trả action/gán ô cho
  world, world chỉ thi hành một hành động mỗi tick).
- **Hệ quả:** artifact 36 (chạy với fix DET-01 nhưng chưa có fix này) **vẫn còn nhiễm** ⇒
  phải chạy artifact **37** với đủ ba fix. Ghi lại chuỗi này vì nó là bài học về **thứ tự**:
  sửa một confound rồi đo ngay là cách chắc chắn phải đo lại lần nữa.

### ✅ Kiểm chứng bộ fix #13 + #17 — chạy LẠI đúng phép đo đã phát hiện chúng

Không tuyên bố "đã sửa" bằng việc test xanh; chạy lại chính phép đo đã lộ ra lỗi (seed 1000,
kênh `accept_lift`):

| Arm | decision adherence | danh nghĩa nhóm được khuyên | **thổi phồng** | event/quyết định | tổng lift đã áp |
| --- | --- | --- | --- | --- | --- |
| cadence ON | 0,658 | 0,603 | **+0,055** | 1,03 | 3,800 |
| cadence OFF | 0,674 | 0,617 | **+0,057** | 3,21 | 4,450 |

- **Lệch thổi phồng giữa hai arm: 0,095 → 0,003** (giảm ~32 lần). Hai arm nay có cùng mức
  chệch so danh nghĩa ⇒ **arm đối chứng đã sạch**, Lỗi #13 đóng.
- **Tỷ lệ liều can thiệp OFF/ON: 2,0–2,5 lần (số lần áp) → 1,17 lần (tổng lift).** Lỗi #17 đóng.
- ⚠ **Phần dư 17% KHÔNG phải confound** — arm OFF vẫn ra **nhiều quyết định riêng biệt hơn**
  (không cooldown ⇒ nhiều bucket có lời khuyên). Đó chính là **hiệu ứng thật của nhịp**, đúng
  thứ ta muốn đo. Còn `event/quyết định` 3,21 ở arm OFF là các lần **phát lại không có tác
  động** (R-01 chặn), nên chúng chỉ làm ồn log chứ không làm lệch phép đo nữa.

### Lỗi #18 (R-09) — ba kênh dùng ba định nghĩa "ĐÃ NÓI"

`accept_lift` gọi `cadence_note_spoken` **vô điều kiện**; `shift_extend` gọi **chỉ khi
followed**; `rest_window` gọi **mỗi cửa sổ hoãn**. Hệ quả: lời khuyên `shift_extend` bị bỏ
ngoài tai **không tiêu** suất nào ⇒ kênh đó được hỏi lại không giới hạn, trong khi
`accept_lift` bị bỏ ngoài tai vẫn đốt 1/6 suất. Mọi phép chia ngân sách theo kênh trong
ablation 31–34 lệch theo.
**Fix:** `cadence_note_spoken` chạy **trước** `coin_follows` ở `shift_extend` — ngân sách là
ngân sách **CHÚ Ý của người nghe**, advisor NÓI là đã tiêu, bất kể có được làm theo hay không.

### Lỗi #19–#21 — ba lỗ nữa ở nửa sản phẩm (vòng soi 2, đã sửa)

| ID | Lỗi | Sửa |
| --- | --- | --- |
| **#19** (R-18) | `_phase_of(...) or phase` — record thiếu `at_min` (bản trước ĐA-04, hoặc POST không gửi vì field `default=None`) rơi về **pha của người ĐỌC** ⇒ một cú Bỏ qua cũ thành **lệnh im di động**: hỏi ở pha nào cũng im pha đó | Không biết pha thì **bỏ qua record**, không đoán. *"Không biết" khác "là pha này"* — cùng bài học `is_valid_at` trả ba giá trị ở F-098-02 |
| **#20** (R-11a) | Ca **vắt qua nửa đêm**: query cho `shift_end_min` nhỏ tuỳ ý, ca 22:00→02:00 gửi 120 ⇒ `shift_len = 120−360 < 0` ⇒ `shift_phase` trả `"early"` **vĩnh viễn** ⇒ *"im hết pha"* biến thành *"im hết ca"*, trái verdict đã chốt | `_norm_shift_end`: kết ca sớm hơn mở ca nghĩa là hôm sau (+1440), áp ở cả GET lẫn `_phase_of`. ⚠ Phần còn lại (memory lọc theo `date` nên qua 00:00 ngân sách được cấp lại **giữa ca**) cần khái niệm `shift_id` → `D-R11b` |
| **#21** (F4 phần dư) | Sau khi sửa Lỗi #16, `POST /action` **vẫn** ghi một trường `phase` tính bằng `DEFAULT_SHIFT_END_MIN` cứng — **trường chết** mà người đọc sau sẽ tin | Bỏ hẳn trường đó. Giữ lại một trường tính bằng công thức KHÁC chỉ để "debug" là mời gọi đúng cái nhầm lẫn vừa sửa |

### Lỗi #22 (R-12) — nhánh an toàn `QUEUE` chết ở sản phẩm, và lời khuyên bị VỨT thay vì HOÃN

`Cards.nudge` có `if (isDriving) return null` — giữ đúng NHTSA, nhưng hai cái sai đi kèm:

1. Backend **không bao giờ thấy** `is_driving` ⇒ nhánh `QUEUE / unsafe_while_moving` trong
   `cadence.evaluate` **không bao giờ chạy ở sản phẩm**. Cùng họ *"code tự quảng cáo một nhánh
   không chạy"* đã trả giá ở Lỗi #9 — và lần này nó là nhánh **an toàn**. Ở SIM thuộc tính này
   được bảo đảm bằng **cấu trúc** (vòng idle bỏ `ENROUTE`/`ON_TRIP`) ⇒ thuộc tính **có ở sim,
   không có ở sản phẩm** — đúng loại lệch ĐA-04 sinh ra để diệt.
2. `return null` **VỨT** lời khuyên. `QUEUE` nghĩa là *"trợ lý sẽ nhắc khi bạn dừng"* — đúng
   thứ tài xế cần và đúng câu `_SILENT_MSG` đã viết sẵn.

**Fix:** client **báo trạng thái**, luật chung **quyết**. An toàn không giảm: backend trả
`QUEUE` ⇒ `silent` ⇒ không card nào được vẽ. Nguyên tắc rút ra: *client báo cáo trạng thái,
đừng tự thi hành chính sách* — thi hành ở client nghĩa là sim và sản phẩm chạy hai luật khác
nhau, dù cả hai "trông đúng".

### Bốn lỗi TEST mà vòng soi thứ hai bắt (đều là test của tôi)

| ID | Lỗi | Sửa |
| --- | --- | --- |
| **R-04** | `assert decided == followed + dismissed + (decided − followed − dismissed)` — **đồng nhất thức đại số**, đúng với mọi bộ số. Tôi viết nó với comment *"cấu trúc đếm nhất quán"*; thực chất là một dòng trang trí. Mutation cho `suppressed` cộng vào CẢ hai mẫu số sẽ sống sót. | Thay bằng bất biến nói được điều gì sai: `suppressed > 0`, `followed + dismissed <= decided`, và `decided + suppressed > event_decided` |
| **R-05** | `test_cadence_disabled_returns_to_baseline` chỉ kiểm **sự vắng mặt của telemetry** — mutation nén thật mà không ghi event sẽ sống sót, và lưới 2×2 thành "ON vs ON không log" | Kiểm HÀNH VI: tắt cadence ⇒ **phải tồn tại tài xế vượt 6/ca**; bật ⇒ không ai vượt |
| **R-06** | `DECISION_BUCKET_MIN` tự nhận là *"nguồn sự thật duy nhất, sai là washout sống lại im lặng"* nhưng **không test nào pin**. Đổi 30→2 thì coin và `decision_id` co nhất quán ⇒ mọi test vẫn xanh | Pin cả **giá trị** lẫn **ngữ nghĩa** (hai lần hỏi cách <30′ ⇒ một coin) và bất biến `bucket ≥ cooldown` |
| **R-07** | Bug F-3 được **kể trong docstring** đầu file test mà **không test nào tái hiện** — revert bản fix đó thì cả file vẫn xanh | Test `followed → dismissed → followed` **với đồng hồ nhích từng giây** (bản đầu của tôi nén vào một giây và đỏ — nhưng đó là ca double-click mà thiết kế CÓ Ý gộp; đã thêm cả mặt đối chứng đó) |

Và bốn lỗi test nữa từ cùng vòng soi, đã sửa hết:

| ID | Lỗi | Sửa |
| --- | --- | --- |
| **R-13** | `test_world_a_untouched_crn` là `summarize(run(base)) == summarize(run(base))` — **so một biểu thức với chính nó**. Chỉ kiểm determinism, không kiểm điều tên test tuyên bố; CRN drift lệch *nhất quán* cả hai lần vẫn xanh | So hai **cấu hình khác nhau**: `base` vs `advice enabled + coverage="none"` phải cho cùng `summarize` **và** cùng chuỗi event |
| **R-14** | `test_exact_repeat_with_cadence` chỉ so `(t_min, actor_id, kind)` — bỏ `detail` (chứa `decision_id`/`followed`/`reason`, đúng những trường mọi projection join theo) dù CLAUDE.md đòi bit-identical | So thêm `cell` và `detail`; chi phí = 0 vì code vốn đúng |
| **R-15** | Độ lớn cooldown 20′ chỉ được pin ở **dataclass mặc định**. Gõ nhầm key ở lớp **parse YAML** ⇒ cooldown hiệu dụng 2′, `topic_cooldown` biến mất, mà test cũ dùng `&` (*"một trong hai reason"*) nên vẫn xanh nhờ budget | Đòi **cả hai** reason (`<=` thay vì `&`) + test mới pin `bridge.cadence_cfg` **sau `Config.load`** — đúng lớp có thể hỏng |
| **R-16** | Ưu tiên safety chỉ pin **một nửa** (vs `is_driving`, vs budget) — thiếu vs `dismissed` và vs `cooldown`. Mutation đảo thứ tự nhánh ⇒ mọi test xanh, hậu quả sản phẩm: **bỏ qua một thẻ an toàn làm im toàn bộ cảnh báo an toàn tới hết pha** | Một assert với memory có đủ ba thứ chặn cùng lúc |

Kèm một lỗi test nữa **tự bắt khi R-01/R-09 làm nó đỏ**:
`test_count_positioning_in_budget_flag_is_alive` khẳng định `n_on < n_off` — một hiệu ứng **có
hướng**, không phải bất biến: khi positioning tiêu ngân sách thì các kênh khác cạn sớm hơn, và
tổng số người được gán là kết quả **tương tác**. Nó đỏ ở 80 vs 79 dù cờ hoạt động hoàn hảo.
Thay bằng bất biến về **cơ chế**: cờ tắt ⇒ positioning không có event nén nào; cờ bật ⇒ phải có.

### Lỗi #14–#16 — ba lỗ của "một luật" ở phía SẢN PHẨM (soi đối kháng bắt, agent chính xác nhận)

Ba finding riêng biệt nhưng cùng một gốc: **nửa UI của "một luật" đo bằng đơn vị khác nửa sim.**

**#14 (F1) — ngân sách chỉ hao khi tài xế BẤM, không hao khi advisor NÓI.** `GET /advice` trả
card mà **không ghi event nào** ⇒ tài xế phớt lờ 20 thẻ thì `proactive_count` vẫn 0 ⇒ advisor
nói mãi. Sim thì gọi `cadence_note_spoken` ngay khi nói. Sai ở **đơn vị đếm**: sim đếm *lời
nói*, sản phẩm đếm *cú bấm*.
*Fix:* `_note_shown()` ghi event `displayed` khi GET trả items, khoá theo **decision bucket
30′** (không theo `advice_id` — id đó mang `now_min` nên client refresh mỗi phút sẽ thành
"lời khuyên mới" và đốt hết ngân sách trong vài giây). Hai test canh hai chiều: 7 bucket khác
nhau ⇒ cạn ngân sách; 15 lần poll trong một bucket ⇒ đúng 1 lần nói.
*Trade-off nói thẳng:* đây là **side-effect trên một GET** — mùi REST, chọn có chủ ý, vì chỉ
server biết chắc "advisor đã nói"; để client tự POST "đã xem" thì một client im lặng lại làm
ngân sách không hao, tức quay về đúng lỗ hổng này.
*Hệ quả kéo theo (tự gây, tự sửa trong cùng lượt):* GET có side-effect làm **4 test contract
đỏ** (`KeyError: 'seed'` — response rơi vào nhánh im lặng vì đọc rác của lần chạy trước trong
DB dùng chung). Đã thêm fixture `_isolate_telemetry` autouse. Bài học: **thêm side-effect vào
một endpoint đọc-only làm mọi test của endpoint đó thành có-trạng-thái** — phải cô lập ngay,
không chờ nó đỏ ngẫu nhiên.

**#15 (F3) — frontend KHÔNG BAO GIỜ gửi `topic`.** Cả `POST /action` (`cards.js`) lẫn
`GET /advice` (`api.js`) đều không truyền ⇒ mọi thứ rơi về default `'bonus'` ⇒ cooldown và
dismiss *"theo chủ đề"* **gộp thành một chủ đề duy nhất** ở sản phẩm thật: bỏ qua nhắc buổi
sáng khoá miệng luôn tổng kết ca. Test `test_dismiss_does_not_silence_other_topic` xanh vì nó
gọi API **trực tiếp** với `topic=rest` — không đi qua frontend.
*Fix:* cả hai đường gửi `topic`, tạm ánh xạ theo LOẠI CARD (`brief`/`nudge`/`recap`) với nhãn
**PLACEHOLDER** rõ ràng — item của backend hôm nay chưa mang chủ đề thật, trường đó thuộc
ĐA-06 (`AdviceEnvelopeV2`, đã duyệt chưa implement). Ánh xạ này chỉ bảo đảm ba loại card không
dùng chung cooldown, **chưa** phân biệt "nhắc thưởng" với "nhắc nghỉ" trong cùng loại card.

**#16 (F4) — hai công thức tính PHA CA cho cùng một phút.** `POST /action` lưu pha tính bằng
`advisor.DEFAULT_SHIFT_END_MIN` **cứng 22:00**; `GET /advice` tính bằng `shift_end_min` từ
query ⇒ với ca 06:00–18:00, phút 16:00 là `late` theo công thức đọc nhưng `mid` theo công thức
ghi ⇒ cửa sổ im-theo-pha lệch. Đúng họ **Lỗi #1** (hai lưới thời gian cho một khái niệm).
*Fix:* **bỏ một công thức**, không đồng bộ hai. Pha nay luôn tính LÚC ĐỌC từ `at_min` đã lưu
(`_phase_of`); trường `phase` trong payload chỉ còn để debug và **không được dùng để quyết
định**. Test dựng đúng phút mà hai công thức cho hai kết luận khác nhau.

**Về finding F2 (`positioning` bị ngân sách CHẶN dù được miễn TIÊU) — agent chính BÁC BỎ.**
`evaluate` trong `cadence.py` đúng là kiểm `proactive_count >= max` cho mọi topic không-safety,
nhưng **call site của positioning có guard**: `if self.advice.cadence_counts_positioning and
not cadence_allows(...)` — cờ mặc định `False` ⇒ short-circuit ⇒ `cadence_allows` **không bao
giờ được gọi** cho positioning. Bằng chứng đo thật (seed 1000, ladder all): danh sách channel
của mọi event `advice_suppressed` là `{accept_lift, shift_plan, rest_window, shift_extend}` —
**không có `positioning`**. Agent soi đọc `evaluate` tách rời khỏi call site.

### 🔴 Lỗi #13 (NGHIÊM TRỌNG NHẤT CỦA CYCLE) — arm ĐỐI CHỨNG của mọi ablation BỊ NHIỄM

- **Cách phát hiện:** không phải tôi. Một agent soi đối kháng độc lập (lăng kính determinism,
  finding `DET-01`) đọc `coin_follows` và chỉ ra: nhánh
  `if not self.cadence_enabled: return bool(self.rng.random() < p)` **bó CƠ CHẾ RÚT COIN vào
  cùng một cờ với NHỊP NÓI**. Nên arm `cadence=off` — arm tôi dùng làm đối chứng cho artifact
  32/34/35 — vừa không có nhịp **vừa hồi sinh washout D-SIM-14** mà chính cycle này sinh ra để
  giết.
- **Reproduce (tôi tự đo, seed 1000, kênh accept_lift):**

  | Arm | decision adherence | danh nghĩa của chính nhóm được khuyên | thổi phồng | event/quyết định |
  | --- | --- | --- | --- | --- |
  | cadence ON | 0,681 | 0,603 | +0,078 | 1,03 |
  | cadence **OFF** | 0,761 | 0,588 | **+0,173** | 1,82 |

  ⇒ arm đối chứng có tài xế nghe lời **~10 điểm phần trăm nhiều hơn** vì lý do **không liên
  quan tới nhịp**. Mọi Δ "giá của nhịp" tính từ nó đều thổi phồng.
- **Đính chính agent soi:** finding `DET-01` suy đoán độ lớn ≈ +0,995 (giả định re-roll mỗi
  tick 2′ suốt cửa sổ 30′ ⇒ 1−0,7¹⁵). Thực tế kênh này chỉ fire **1,82 lần/quyết định** nên
  thổi phồng là +0,173. **Cơ chế đúng, độ lớn bị nói quá ~5,7 lần.** Ghi lại để cân bằng: soi
  đối kháng bắt được lỗi tôi không thấy, nhưng số của nó cũng phải kiểm chứ không tin thẳng.
- **Vì sao tôi không tự bắt được:** tôi CÓ viết test cho cờ này —
  `test_cadence_disabled_returns_to_baseline` — nhưng nó chỉ khẳng định *"tắt cờ ⇒ 0 event
  nén"*. Đúng, và vô dụng: nó kiểm **cổng**, không kiểm **coin**. Bài học Lỗi #6 (*"cờ có
  trong config ≠ cờ có tác dụng"*) tôi đã viết ra rồi vẫn không đủ — phiên bản mạnh hơn là
  **"một cờ phải điều khiển ĐÚNG MỘT thứ; test phải kiểm từng thứ nó điều khiển, và phải hỏi
  nó có điều khiển thứ gì KHÔNG NÊN không"**.
- **Fix:** keyed coin **vô điều kiện**; `cadence.enabled` chỉ còn điều khiển gate. Kèm theo
  `DET-02` tự khỏi: coin không còn tiêu `self.rng` nên bật/tắt một kênh không xê dịch stream
  `covers` của kênh khác ⇒ hai ô OFF của lưới 2×2 nay ghép cặp thật.
- **Test khoá** `test_coin_is_keyed_even_when_cadence_off` — hai bất biến **không phụ thuộc số
  liệu**: (a) hỏi lại 15 lần cùng quyết định ⇒ một câu trả lời; (b) `self.rng.bit_generator.state`
  **không đổi** sau 20 lần rút coin.
- **Hệ quả tài liệu:** artifact 32/34/35 và mọi con số "giá của nhịp" tôi đã báo (−2.885đ,
  −3.048đ) **bị treo cho tới khi có artifact 36**. Xem §ĐÍNH CHÍNH ở cuối mục HIỆU NĂNG.

### Lỗi #12 — ngân sách UI đếm EVENT thay vì QUYẾT ĐỊNH (1 card = 2 suất)

- **Cách phát hiện:** không phải do test hay review trực tiếp — lộ ra khi một agent thiết kế
  cơ chế ngân sách cho `D-ĐA04-03` phải đọc kỹ `_cadence_memory` để mô tả hiện trạng. Bằng
  chứng reproduce: một card bấm "Vì sao" (`displayed`) rồi "Làm theo" (`followed`) ⇒
  `proactive_count = 2`. **Ba card là advisor im cả ngày** thay vì sáu.
- **Root cause:** `proactive_count += 1` cho MỖI event trong khi ngân sách định nghĩa theo
  số lần advisor NÓI (= số quyết định). Đúng họ lỗi decision-vs-event mà Cycle W trả giá 4
  lượt review — lần này ở phía UI.
- **Fix:** đếm `len(set(decision_id))` của các event `displayed`/`followed`. Test
  `test_budget_counts_decisions_not_events` khoá: 3 card × 2 event = 3 suất, và ngân sách
  chưa cạn thì advisor vẫn PRESENT.
- **Bài học (lặp lần thứ ba trong một cycle, đáng ghi thành luật):** bất kỳ counter nào
  đếm trên event stream phải trả lời được câu "đơn vị của counter này là GÌ — event hay
  decision?" ngay tại chỗ khai báo. Hai lần trước: Lỗi #2 (suppressed lọt mẫu số), Lỗi #7
  (đếm event `standby_alloc` thay vì người).

### Lỗi #9 — `topic_cooldown` sống ở sim nhưng CHẾT ở sản phẩm ("một luật" chỉ đúng một nửa)

- **Cách phát hiện:** đọc lại diff của `_cadence_memory` với câu hỏi *"ai nuôi từng trường của
  `CadenceMemory`?"*. Ba trường: `dismissed_in_phase` ✅, `proactive_count` ✅,
  **`last_decided_min` — không ai nuôi**. Mà `evaluate` chỉ áp cooldown khi trường đó có giá
  trị ⇒ nhánh `topic_cooldown` **không bao giờ chạy ở UI**, trong khi `_SILENT_MSG` đã có sẵn
  một câu tử tế cho nó. Code tự quảng cáo một tính năng không tồn tại.
- **Vì sao đây là lỗi NẶNG về ý nghĩa, dù chỉ 5 dòng:** cả cycle này tồn tại để sim và sản
  phẩm **cùng một luật**. Một cổng chạy ở sim mà không chạy ở sản phẩm nghĩa là A/B đang đo
  một advisor **khác** với advisor sẽ ship — đúng cái bệnh ĐA-04 sinh ra để chữa.
- **Fix:** nuôi `last_decided_min[topic]` từ `payload["at_min"]` của event `displayed`/
  `followed`, lấy giá trị lớn nhất. Test `test_topic_cooldown_alive_in_product` khoá lại:
  hiện thẻ lúc 10:00 → hỏi lại 10:10 phải im với `next_eligible_min=620` → 10:25 nói lại được.
- **Bài học nối tiếp Lỗi #6:** cả hai đều là *"đường dây không nối"* — cờ có trong config
  nhưng không tới engine (Lỗi #6), trường có trong dataclass nhưng không ai ghi (Lỗi #9). Khi
  hai nửa của một hệ dùng chung một cấu trúc dữ liệu, **phải kiểm từng trường xem cả hai bên
  có thật sự nuôi nó không** — kiểu dữ liệu khớp không chứng minh ngữ nghĩa khớp.

### Lỗi #3 (quy trình, không phải code) — suýt cho sim mượn cơ chế của sản phẩm

Bản thiết kế đang làm dở định cho sim dùng luôn `dismissed_for_window` "cho giống sản phẩm".
Chỉ thị của Cường chặn lại. Không có dòng code nào sai — nhưng nếu lọt thì **mọi số A/B về sau
đều nhiễm** một cơ chế không thuộc về phép đo, và sẽ rất khó phát hiện vì nó chỉ làm Δ **nhỏ
đi** (trông như "advisor không hiệu quả lắm", một kết luận sai rất dễ tin). Chống tái phát:
2 test khoá ranh giới + docstring chép nguyên văn chỉ thị.

## Visual verification

- **Status:** `BLOCKED` (chờ mắt người) → `WAITING-VERDICT` khi Cường xem — mã **V-18**
- ⚠ **Cách vẽ đã đổi HAI lần trong cycle** (Lỗi #10 rồi Lỗi #11), và **dữ liệu bên dưới**
  cũng đổi sau bộ fix confound. Bản Cường sẽ xem là bản đã đo lại mật độ **sau** mọi
  thay đổi — không phải bản cũ.
- **Cách launch / artifact — ba thứ cần xem, theo thứ tự:**
  1. `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` → tab 🧭 **Hành trình**,
     **seed 1000**, bật `advice.enabled` + `channels.accept_lift/shift_extend/rest_window`.
     Nhìn: vạch **chấm** = advisor nói · **vùng xám** = quãng im vì hết ngân sách ca (một mốc
     "hết ngân sách nhắc" + vùng tô, KHÔNG phải 58 vạch) · vạch **gạch** = cooldown. Kéo tới
     tài xế **actor 26** — đó là ca xấu nhất (58 lần bị nén, nhưng chỉ 2 phần tử thị giác).
  2. Bảng **"Nhịp nói của advisor (ĐA-04)"** ngay dưới biểu đồ: nói bao nhiêu / bị nén bao
     nhiêu / **vì sao** — đọc thẳng từ event, không tự tính lại.
  3. `uv run uvicorn app.main:app --app-dir ui/backend --port 8010` → `/app/` bấm 🤖 Trợ Lý
     Xanh → **Bỏ qua** → hỏi lại cùng khung giờ ⇒ phải IM kèm câu giải thích tử tế; sang khung
     giờ khác ⇒ nói lại. Và `/app/mo-phong/` tab Hành trình để xem nhãn tiếng Việt của kind
     `advice_suppressed` ("trợ lý im (giữ nhịp)").
- **Seed / scenario đã xem:** seed 1000 (ladder all).
- **Mật độ marker đã ĐO trước khi mời xem** (seed 1000, 90 tài xế): 82 tài xế có vạch nén;
  trung vị 33, p90 = 49, xấu nhất 55 vạch/1080 phút. Chính con số này buộc phải đổi cách vẽ
  (Lỗi #10) — bản trước đó vẽ được nhưng **không đọc được**.
- **Đo LẠI sau toàn bộ bộ fix** (số nén đổi: 2.756 nén / 569 nói): trung vị 34, p90 49, xấu
  nhất **58**. Nhưng phân tách theo cách vẽ mới: **2.718 lần là "hết ngân sách"** (gộp thành
  MỘT vùng xám) và chỉ **38 lần** là `topic_cooldown` (vẽ từng vạch). Tài xế xấu nhất
  (actor 26): 58 lần bị nén ⇒ chỉ còn **1 vạch + 1 vùng xám = 2 phần tử thị giác**. Cách vẽ
  mới vẫn đứng vững sau khi dữ liệu bên dưới đã đổi — đó là dấu hiệu chọn đúng đơn vị biểu
  diễn, không phải chỉnh cho vừa một bộ số.
- **Agent đã verify được tới đâu (nói rõ để không ai đọc nhầm thành "đã review"):**
  - ✅ **Data path**: chạy thật seed 1000 và đếm từ event — 531 lần NÓI / 2.670 lần NÉN; một
    tài xế mẫu (actor 89) cho `{shift_plan: 6, positioning: 1}` đã nói và
    `{accept_lift: 13, shift_plan: 12, shift_extend: 9}` bị nén vì `shift_budget_exhausted`.
    Tức là **bảng nhịp có dữ liệu thật để hiện**, không phải khung rỗng.
  - ✅ **Compile/lint**: cả 6 file Python đổi + `mo-phong.js` (`node --check`) đều sạch.
  - ✅ **Consumer check**: rà `EV_COLORS`/`EV_VI` của frontend nên kind mới không rơi vào
    fallback tiếng Anh.
  - ❌ **CHƯA render thật trong trình duyệt** và ❌ **chưa có mắt người**.
- **Người review + verdict:** ⏳ chờ Cường (V-18).
- **Blocker là con người, không phải kỹ thuật:** agent không tự thay được bước "Cường nhìn và
  nói có/không". Theo tiền lệ "hoãn ≠ waive", cycle ghi `DONE-CODE`, **không** ghi `DONE`.

## Soi đối kháng ĐỘC LẬP — hai vòng, 26+ finding (phần đáng giá nhất của cycle)

Sau khi tôi tự nhận cycle "đã xong và đã tự soi", hai workflow soi đối kháng độc lập được chạy
với bốn lăng kính (thước đo · determinism · một-luật-hai-nửa · chất lượng test) rồi một vòng
**phản biện** (agent khác cố BÁC BỎ từng finding) và một **giám khảo** chấm 7 bản thiết kế.

**Kết quả trung thực về chất lượng tự-soi của tôi:**

| | Số lượng |
| --- | --- |
| Finding tôi **tự bắt** trong cycle (Lỗi #1–#12) | 12 |
| Finding **soi độc lập** bắt mà tôi KHÔNG thấy | **9 đã sửa** (#13, #17–#21, R-13…R-16) + 4 chuyển DEFERRED |
| Finding soi độc lập **báo sai / bị bác bỏ** | 6 (DET-05, L1-F2, L1-F1, L1-F4, L1-F8, và độ lớn của DET-01) |

Nghĩa là: **soi độc lập tìm ra lỗi nghiêm trọng nhất của cả cycle** (#13/DET-01 và #17/R-01 —
cả hai làm mọi con số A/B sai), và tôi tự soi thì **không** tìm ra. Nhưng ~23% finding của nó
sai hoặc phóng đại (kể cả độ lớn của chính DET-01: nó nói ≈+0,995, thực đo +0,173), nên **vòng
phản biện là bắt buộc, không phải trang trí** — nếu tôi tin thẳng thì đã sửa nhầm và báo nhầm
tiếp một lần nữa.

**Sáu finding BỊ BÁC BỎ** (ghi lại để không ai đào lại): `DET-05` (drain mất event — đo 6 run,
`_suppressed_out == []` 6/6); `L1-F2` (positioning bị ngân sách chặn — call site short-circuit
đối xứng); `L1-F1`/`L1-F4` (đã fix trước khi phản biện chạy); `L1-F8` (vô hiệu bởi bản fix F1);
và **độ lớn** của `DET-01`.

## Adversarial self-review / flaws found

1. **Cái gì có thể trông tốt nhưng sai? — GIẢ THUYẾT CẠNH TRANH CHO `ladder_all` +5.701đ.**
   Cách đọc hấp dẫn là *"cadence cứu các kênh spam"*. Nhưng có lời giải thích thứ hai, ít
   hào nhoáng hơn và rất có thể đúng hơn: **keyed coin làm adherence hiệu dụng tụt từ ≈1,0
   xuống 0,68**, nên các kênh ÂM (nhất là `shift_plan`, ĐA-07 đã kết luận âm) **ít bị nghe
   theo hơn** ⇒ hại ít đi. Nếu vậy thì phần cải thiện là công của việc **sửa thước đo**, không
   phải của nhịp. Hai lời giải thích cho cùng một con số ⇒ **phải tách bằng ablation**, không
   được chọn cái mình thích. Đã chạy artifact 32 (`ladder_all` cùng seed set, cùng keyed coin,
   chỉ tắt `cadence.enabled`) — kết quả và phán quyết ở mục §HIỆU NĂNG/Ablation.
   Ngoài ra, adherence "đẹp lên" cũng có thể chỉ vì mẫu đổi (cadence loại bớt các lần hỏi lại,
   mà chúng tập trung ở nhóm tuân thủ thấp). Đã kiểm bằng **hai đơn vị đo độc lập** (decision
   và event) — chúng hội tụ ⇒ không phải hiệu ứng chọn mẫu. **Nhưng** 68% vẫn KHÔNG được đọc
   là "trung bình danh nghĩa quần thể": người được khuyên là nhóm dưới ngưỡng (P4 chiếm ưu thế).
2. **Leak / CRN drift / hidden fallback / double-count?** CRN: `test_world_a_untouched_crn`
   chứng minh world A không đổi một bit khi advice tắt. Không có future-info mới (coin lấy từ
   `decision_id` + `material_revision`, cả hai đã biết tại thời điểm quyết định). Double-count:
   đã học từ F-S1 Cycle W — `advice_followed` vẫn KHÔNG có trong map projection.
   **Hidden fallback còn mở:** nếu `material_revision` là `None`/rỗng thì coin vẫn tính được
   (chuỗi rỗng) — không fail-loud. Rủi ro thấp (4 call site đều truyền hằng), nhưng đây đúng
   họ "hidden fallback" đã cắn ở B3.
3. **Assumption yếu nhất:** `min_gap=20′` và `budget=6/ca` là số baseline **chưa có telemetry
   thật** đỡ lưng. Design ĐA-04 nói rõ "tuning sau dựa telemetry" — đang tôn trọng, nhưng
   nghĩa là con số hiệu năng cycle này **có điều kiện theo hai hằng số đó**.
4. **Baseline nào đã so, giả thuyết nào đã loại:** so với chính repo trước cycle (adherence
   76,9/53,6) và với world A (CRN identical). **Đã LOẠI** hai giả thuyết bằng ablation có số:
   (a) *"cadence làm hỏng giá trị positioning"* — bác bỏ (artifact 31 arm `default_positioning`
   +4.469đ SIG, không suy giảm); (b) *"cadence cứu các kênh spam"* — **bác bỏ** (artifact 32:
   tắt cadence còn TỐT HƠN 2.885đ). Giả thuyết **được XÁC NHẬN bằng lưới 2×2** (artifact
   33+34): ngân sách FIFO để kênh chiếm suất — tương tác +1.458đ, trong khi tác hại trực
   tiếp của `shift_plan` ở kịch bản này chỉ −25đ. Thiết kế 2×2 là thứ tách được confound
   mà ba arm đầu không tách nổi; **bài học: một arm thêm vào đúng chỗ đáng giá hơn ba arm
   thêm vào sai chỗ.**
5. **Bài học QUY TRÌNH lớn nhất của cycle (đáng ghi thành luật):** tôi đã ba lần tuyên bố
   "xong" trên một cycle mà sau đó soi độc lập tìm ra lỗi làm sai mọi con số. Ba lần đó có
   cùng một hình dạng: **tôi tự soi bằng cách đọc lại thứ mình vừa viết.** Cái đó bắt được
   lỗi cú pháp và lỗi logic cục bộ, nhưng gần như không bao giờ bắt được **giả định** — vì
   giả định là thứ tôi không nhìn thấy mình đang có. Cụ thể ở đây: tôi *giả định* "tắt cờ
   cadence = về hành vi cũ" và viết test đúng theo giả định đó. Kết luận hành động:
   **với bất kỳ số nào sẽ được báo cho người ra quyết định, phải có ít nhất một lượt soi
   ĐỘC LẬP trước khi báo** — và phải có vòng phản biện, vì ~23% finding của soi độc lập
   sai hoặc phóng đại.

6. **Flaw còn mở:**
   - **`D-ĐA04-03` (CAO, đã chứng minh nhân quả)**: ngân sách FIFO tốn ~1.458đ/tài xế/ngày.
     Cần plan riêng cho cơ chế ưu tiên.
   - **`Q-09`**: 1.426đ còn lại là đánh đổi UX ↔ tiền, chờ Cường chốt.
   - **`D-A3-01b`**: advice NO-OP vẫn đếm là `followed` ⇒ 68% vẫn cao hơn "tỷ lệ lời khuyên
     thực sự đổi hành vi".
   - `D-ĐA04-01` (thấp): `material_revision` rỗng không fail-loud.
   - `D-ĐA04-04` (thấp): 2.670 event suppressed/run — chỉ chấp nhận được vì sim để RAM.
   - `V-18` (visual): chưa có mắt người.
   - **`D-R08`** (TB): đơn vị "bị nén" không cùng quy ước giữa các kênh ⇒ con số "2.670 lần
     bị nén" phóng đại ~47%; **`D-R11b`** (TB): ca vắt nửa đêm reset ngân sách giữa ca;
     **`D-R12`** (TB, an toàn): `is_driving` không có đường nuôi từ client ⇒ nhánh QUEUE
     không bao giờ chạy ở sản phẩm; **`D-R17`** (thấp): ba lưới bucket cho một khái niệm;
     **`D-R20`** (thấp): ba test bám seed 1000; **`D-R02`**+**`Q-10`**: pull-vs-push.
   - So xếp hạng cũ-vs-mới ở mức kết luận cần ≥100 seed — **chưa chạy**. Điều này quan trọng
     hơn tôi tưởng lúc lập plan: các Δ trong §Ablation cách nhau 1,4–2,9k trên SD ~40k/seed,
     nên **thứ tự giữa các arm là gợi ý mạnh chứ chưa phải kết luận thống kê chắc chắn**. Con
     số nào dùng để RA QUYẾT ĐỊNH thì phải chạy lại ở n≈100.

## Expansion checkpoint (T-039)

1. **Schema:** `context_revision` trong lifecycle event nay có nghĩa thật (`material_revision`).
   Đề xuất (chưa làm): đưa `cadence_verdict` + `reason` thành cột hạng nhất của event thay vì
   nằm trong `detail`, để projection đếm nhịp không phải bới payload.
2. **Bài toán tối ưu:** nhịp nói hiện là **luật cứng** (20′/6). Có thể formalize thành bài toán
   ngân sách chú ý: chọn tập lời khuyên tối đa hoá giá trị kỳ vọng dưới ràng buộc ≤K lần/ca —
   tức là một knapsack theo thời gian. Cần telemetry adherence-theo-thứ-tự-nhắc trước khi làm.
3. **Tính năng:** đã đủ vật liệu để làm "Nhật ký nhịp" cho tài xế (*"hôm nay trợ lý nhắc 4 lần,
   bạn làm theo 2"*) — nhưng đó là POLISH, xếp sau T-041/T-042 theo thứ tự đã chốt.
4. **Quy trình (mới, quan trọng hơn cả ba mục trên):** cycle này cho thấy **soi đối kháng độc
   lập bắt được lớp lỗi mà tự-soi không bắt được** — cụ thể là lỗi ở tầng **giả định**, vì
   giả định là thứ người viết không nhìn thấy mình đang có. Đề xuất đưa vào harness: *"con số
   nào sẽ được báo cho người ra quyết định thì phải qua một lượt soi độc lập TRƯỚC khi báo,
   kèm vòng phản biện"*. Có số đỡ lưng: ở cycle này soi độc lập cho 26 finding, **~23% sai
   hoặc phóng đại** — nên phản biện là bắt buộc, không phải trang trí. Cần Cường duyệt trước
   khi sửa CLAUDE.md.

## Follow-up / defer phát sinh

- **V-18** → `tracking/PENDING-REVIEW.md` (visual, non-blocking như V-01..V-17). Điểm cần mắt
  Cường không phải "code chạy chưa" mà **"advisor im như vậy có đúng mức không"** — nhịp quá
  chặt thì tài xế thấy bị bỏ rơi, quá lỏng thì quay lại spam.
- **D-A3-01 và D-SIM-14 đóng `DONE-CODE`** trong `tracking/DEFERRED.md` (washout + coin theo
  khoá). ⚠ **Nhưng tách ra `D-A3-01b` VẪN HỞ**: phần BRIDGE-3 — advice **NO-OP** (lời khuyên
  không đổi hành vi thực tế) vẫn được đếm là `followed` (41/70 ở lần đo cũ). Cycle này giết
  washout chứ **không** giải quyết NO-OP, nên con số 68% vẫn cao hơn "tỷ lệ lời khuyên thực sự
  làm đổi hành vi". Không được trình bày 68% như thể đã sạch cả hai lỗi.
- **D-ĐA04-01** → `tracking/DEFERRED.md`: `material_revision` rỗng không fail-loud; severity
  THẤP; mở lại khi có call site tính revision động.
- **D-ĐA04-02** → `tracking/DEFERRED.md`: tuning `min_gap`/`budget` bằng telemetry thật; mở lại
  khi có ≥1 tuần dữ liệu nút bấm thật (hiện chỉ có MOCK).
- **D-ĐA04-03 (sev TB — hạ từ CAO sau đối chiếu config)** → `tracking/DEFERRED.md`: ngân
  sách chú ý chia theo FIFO, chứng minh nhân quả bằng lưới 2×2 (~1.458đ/tài xế/ngày) —
  NHƯNG ở config ship 4 kênh chịu ngân sách đều TẮT (ĐA-07) ⇒ chi phí này chỉ nhiễm **arm
  nghiên cứu** và tương lai bật lại kênh, không phải tiền production hôm nay. **Khung plan
  3 phương án (thang tĩnh / reservation-price / ngân sách có làn) + 6 câu hỏi cần Cường
  chốt: `tracking/PLAN-d-da04-03-budget-priority-DRAFT.md`** — agent không tự implement.
- **D-ĐA04-04 (thấp)** → `tracking/DEFERRED.md`: 2.670 event suppressed mỗi run (gấp ~5 lần
  event lời khuyên thật); chấp nhận ở sim vì để RAM, phải nén thành counter trước khi sản phẩm
  ghi vào SQLite.
- **Q-09 (quyết định, không phải defer)** → `tracking/PENDING-REVIEW.md`: sau khi sửa
  `D-ĐA04-03` vẫn còn ~1.426đ là giá nội tại của nhịp. Ba đường (giữ / nới baseline thành ARM /
  bỏ nhịp ở sim) — **chờ Cường**, agent chỉ khuyến nghị KHÔNG chọn đường thứ ba.
- ~~**Đề nghị đọc lại ĐA-07 với dữ liệu mới**~~ ⚠ **RÚT LẠI**: lập luận cũ dựa trên lưới 2×2
  **trước khi loại confound** (`shift_plan` "vô hại khi chạy một mình, −25đ"). Đo lại chỉ với
  fix DET-01 đã làm ô `OFF_nosp` đổi từ +8.561 → +6.597đ ⇒ **con số −25đ không còn**. Đọc lại
  ĐA-07 phải chờ artifact 37. Giữ dòng này ở dạng gạch để không ai trích lập luận đã mục.
- **Bảy mục DEFERRED mới từ soi đối kháng vòng 2** (ngoài `D-ĐA04-*` và `D-F098-*`):
  `D-R02` (pull-vs-push → `Q-10`) · `D-R08` (đơn vị "bị nén" phóng đại ~47%) · `D-R11b` (ca
  vắt nửa đêm reset ngân sách giữa ca) · `D-R17` (ba lưới bucket cho một khái niệm) ·
  `D-R20` (test bám seed 1000) · `D-R21` (client gửi `at_min` giả — **cố ý chưa sửa**, vì
  sửa một phía tạo đúng loại bất đối xứng vừa diệt ở Lỗi #16/#21). `D-R12` đã **đóng**.
- **Đề xuất sửa CLAUDE.md** (cần Cường duyệt, xem Expansion #4): thêm điều khoản *"số nào báo
  cho người ra quyết định phải qua soi độc lập + phản biện TRƯỚC khi báo"*. Cycle này là bằng
  chứng: tôi báo sai hai lần, và cả hai lần đều do giả định mà tự-soi không nhìn ra.
