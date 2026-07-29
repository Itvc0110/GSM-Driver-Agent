# UPDATE-092 — Review đọc-lại `66268cc`: sổ tra hạn chế + bằng chứng cải thiện (docs-only)

> ⚠ **RÀ TẠI `66268cc`, COMMIT SAU `5364395`.** Trong lúc soạn, phiên khác push `5364395` đóng
> Cycle W (36 finding, suite 707/5). Tôi **verify lại từng finding trên code mới** — kết quả ở
> **§H-04-bis**: 4/4 finding của §H-04 **đã được sửa**, chỉ **một** phát hiện của tôi sống sót
> (`format_checker`, và nó rộng hơn ban đầu: 15 schema). §H-04 giữ làm bản ghi lịch sử.

- **Ngày:** 2026-07-29
- **Người thực hiện:** AI agent, dưới claim của **Cường** (yêu cầu: *"review lại repo, ghi lỗi commit
  nào file nào mục nào logic ra sao, config nào, điều nào chưa đạt"*)
- **Loại:** docs (review / audit note) — **KHÔNG đổi một dòng code nào**
- **TODO / User story liên quan:** T-046 (mẫu lỗi lặp) · ĐA-05 (Cycle W còn dở) · ĐA-04 (kế tiếp) ·
  T-045b/c/e · B6-PARITY (mới, xem §Follow-up)

## Tóm tắt

Rà soát toàn repo tại `66268ccb7ae` (local == `origin/main`, tree sạch) để trả lời ba nhận xét cũ
của Cường về đo nhân quả advice và phản ứng toàn hệ thống. Kết luận: **nhận xét #3 (dư cung /
herding) đã bị code vượt qua, có 3 tầng cơ chế thật + ~220 run đo đạc; nhận xét #1 và #2 (nhân quả
từng lượt advice, counterfactual ngắn) vẫn đúng nguyên vẹn** — phần *ghi chép* đã xong ở `66268cc`,
phần *ước lượng* chưa có dòng nào. Rủi ro lớn nhất hiện tại **không nằm ở hai gap đó** mà ở
**B6-PARITY**: sản phẩm đang được A/B đo (5 kênh, 9 solver) khác hẳn sản phẩm đang ship cho tài xế
(1 solver).

File này là **sổ tra khi review lại** — mỗi hạn chế có commit / file / dòng / logic để kiểm chứng
lại mà không phải đọc lại toàn bộ lịch sử.

## Chi tiết cập nhật

Không có quyết định thiết kế nào được đưa ra ở đây. Đây là bản ghi nhận trạng thái, dùng làm đầu
vào cho lần plan tiếp theo. Ba quy ước khi đọc:

1. Mỗi dòng "hạn chế" phải **kiểm chứng lại được** bằng đúng lệnh/đường dẫn ghi kèm.
2. Mục nào tôi **tự chạy lại và xác nhận** thì ghi `tự verify`; mục nào lấy từ hồ sơ cũ thì ghi rõ
   nguồn — không trộn hai loại bằng chứng.
3. Không mục nào ở đây được coi là đã sửa. Sửa phải qua plan mode (chốt của Cường 2026-07-29 ~03:40).

---

# PHẦN 1 — ĐÃ CẢI THIỆN THẬT (có bằng chứng)

## 1.1 Chống dồn cung / herding — 3 tầng code thật

Nhận xét cũ: *"advisor thấy khu A nhiều đơn → khuyên 30 tài xế đến khu A → khu A dư người"*.
**Đã có cơ chế chặn ở cả ba tầng**, không phải một chỗ:

| Tầng | Cơ chế | Bằng chứng |
|---|---|---|
| Dữ liệu | `capacity_left = slots − supply_effective`; `ranked_cells` **chỉ chứa ô còn trần** ⇒ ô đủ người **biến mất khỏi danh sách khuyên** | `src/gsm_core/features/market_state.py:80-103` |
| Cung đang tới | Người **đã được khuyên mà chưa đi** tính là cung của ô đích **ngay lập tức** ⇒ người hỏi sau trong cùng bucket không còn thấy ô đó trống | `src/gsm_sim/market_state.py:37-62` (`pending_targets`) + `src/gsm_sim/world.py:333` |
| Điều phối | Hungarian trên slot đã expand theo capacity; dư candidate → `unassigned` (**bỏ hẳn advice**, không ép); `staggered` khi phải đẩy sang ô khác | `src/gsm_core/solvers/capacity_alloc.py:25-70`; gọi theo **lô** mỗi bucket ở `src/gsm_sim/world.py:263-344` |

## 1.2 Equilibrium — đã đo bằng số, không còn là phỏng đoán

Nguồn: `research/simulation/multi-agent-equilibrium.md` (UPDATE-088, ~220 run).

| Câu hỏi | Kết quả đo |
|---|---|
| Cân bằng tồn tại? | **Có**, hội tụ ~1 vòng khi belief = tổng cầu thực (Δbelief tụt về mức nhiễu 6%/vòng); điểm bất động ≈ chính `λ_config` đang dùng |
| Heatmap thích nghi ngây thơ (γ=0) | **KHÔNG hội tụ** (Δbelief kẹt ~0,5; alloc churn 0,4→1,7) và **tệ vĩnh viễn**: served −2đp, payout −6~8k/người |
| Phủ cao có tự triệt tiêu advice? | **Không** — served tăng đơn điệu, phủ 10%→100% = +0,60đp → +1,74đp |
| Price of anarchy | adherence thật (0,30–0,75) đã lấy **70% served / 51% payout** của mức tập trung hoá |
| Bẫy mới | **free-rider ở phủ 25–50%**: người *không* dùng (+3.986đ) hưởng **nhiều hơn** người dùng (+3.327đ) |

Kết quả giá trị nhất không phải "cân bằng tồn tại" mà là **cảnh báo γ=0**: pipeline *"chỗ nào thiếu
xe thì đẩy xe tới"* nghe hợp lý và **sai kiểu tự phá**.

## 1.3 Tự sửa được lỗi thước đo của chính mình — hai lần

| Lỗi | Trước | Sau | Bằng chứng |
|---|---|---|---|
| BUG-EVAL-ARGMAX | chuỗi "advisor làm tài xế nghèo đi −17k…−40k" (UPDATE-075/078/081/084) | estimator cohort không chọn lọc | `src/gsm_sim/parallel.py:93-108` (nhãn ⛔ BIASED-DIAGNOSTIC) + `:111-126` `_cohort_metrics`. Sign-flip: argmax-A −19.654đ · argmax-B +27.416đ · mean-P4 **+3.610đ** |
| F-1 `adherence_view` | **2,0% / 0,0% / 100%** | **52,2% / 100% / 41,9%** | `research/audit/2026-07-29-cycle-w-review/findings.md:21,56-61`; fix ở `src/gsm_core/lifecycle/projections.py:137-145` |

## 1.4 Hạ tầng đo nhân quả — phần *ghi chép* đã xong (commit `66268cc`)

| Có gì mới | Bằng chứng |
|---|---|
| Mỗi lời khuyên có **ID deterministic** | `src/gsm_sim/world.py:164-177` `_decision_id()`, stamp ở 7 chỗ emit advice |
| Máy trạng thái `decided → displayed → followed/dismissed/expired/superseded/suppressed` | `src/gsm_core/lifecycle/projections.py:51-82` |
| Mẫu số đúng: denominator = **số decision**, không phải số event `followed` | `projections.py:85-105`; `world.py:315-339` ghi `assigned_ids`/`decision_ids` để đếm cả người **không** theo |
| Event log append-only thật (không API update/delete, test canh bằng `hasattr`); validate qua registry **trước** khi chạm DB | `src/gsm_core/lifecycle/event_log.py:62, 103-105` |
| Khoá `(run_id, driver_id, topic)` — actor 0 của run A ≠ actor 0 của run B | `projections.py:99`; đo được: gộp 2 run làm 70 khoá tụt còn 55 ⇒ 15 tài xế bị trộn chéo |

## 1.5 Attribution mức **kênh** (không phải mức lượt)

`CHANNEL_LADDER` (`src/gsm_sim/parallel.py:39-52`) + `run_ladder()` (`:269-300`) trả lời *"giá trị
đến từ kênh nào"*. Chi tiết đáng giữ: ladder **sở hữu cả `positioning_overrides`** như pseudo-channel
— nếu không, bậc `"none"` sẽ âm thầm kế thừa product default và cả thang bậc mất nghĩa.

## 1.6 Guardrail dữ liệu / fail-closed

| Cơ chế | Bằng chứng |
|---|---|
| Chống rò tương lai: chỉ dùng ngày **trước**, shrinkage về pooled prior, **bỏ fallback 1.0** | `ui/backend/app/adapters/advisor.py:117-131` |
| Thiếu cung ⇒ `positioning_allowed = False` ⇒ solver **bỏ hẳn** lời khuyên vị trí | `src/gsm_core/features/market_state.py:54-63` |
| Card không qua verifier ⇒ **im lặng** | `ui/backend/app/adapters/advisor.py:318-338`; `src/gsm_core/advisor/pipeline.py:136-137, 151-164` |
| CRN nghiêm: đơn sinh ngoại sinh trước run, dùng chung mọi arm + `assert_crn` | `src/gsm_sim/demand.py:1-8`, `parallel.py:192-202` |
| <30 seed ⇒ `significant` luôn False + cờ `n_insufficient` | `parallel.py:222, 235-236, 245` |

---

# PHẦN 2 — HẠN CHẾ (sổ tra: commit · file · mục · logic)

## H-01 🔴 Chưa đo được nhân quả của **từng lượt** advice

- **Commit:** không phải lỗi của một commit — là **tính năng chưa từng được xây**.
- **File / mục:**
  - `src/gsm_sim/parallel.py:175-189` `run_pair()` — chạy `run_once(A)` rồi `run_once(B)`, so **cả run**.
  - `src/gsm_core/lifecycle/projections.py:100-101` — `adherence_view` trả đúng 4 số đếm
    `{decided, followed, dismissed, suppressed}`.
- **Logic thiếu:** không có dòng code nào join `decision_id` → kết cục tiền (payout / trips / Δ).
  `grep -ri counterfactual src/` = **0 hit** (tự verify).
- **Hệ quả:** trả lời được *"bật advisor có đổi kết quả chung không"* và *"kênh nào tạo giá trị"*,
  **không** trả lời được *"chính lần follow này lời/lỗ bao nhiêu"*.
- **⚠ Cạm bẫy phải tránh khi sửa:** so trực tiếp *"lần follow"* vs *"lần ignore"* sẽ cho số **sai có
  hệ thống**. `src/gsm_sim/advice_bridge.py:92-95` đặt `DEFAULT_ADHERENCE = {P4: 0.75, P3: 0.30,
  P5: 0.30, …}` ⇒ nhóm "follow" **thừa tân binh, thiếu lão làng**; chênh lệch đo được chủ yếu là
  *chênh lệch giữa người*, không phải tác động của advice. Đúng họ lỗi BUG-EVAL-ARGMAX.
- **💡 Tài sản chưa ai khai thác:** `advice_bridge.py:374` và `:395` cho thấy follow/ignore quyết
  bằng `self.rng.random() < p`, `p` **chỉ phụ thuộc archetype** ⇒ **đây là một phép ngẫu nhiên hoá
  thật đã có sẵn trong sim**. Có điều kiện theo archetype (và theo việc đã được gán), follow-vs-ignore
  **đã là randomized**. Một estimator **phân tầng** (archetype × bucket) rẻ hơn nhiều so với dựng
  nhánh phản thực và đã loại được confounder lớn nhất. Vẫn chưa đủ vì (a) **interference** — người
  này theo làm đổi kết cục người kia; (b) **dynamic confounding** — việc bạn nằm trong pool 12:00
  phụ thuộc chính bạn đã theo hay chưa lúc 10:00.

## H-02 🔴 World A phân kỳ — chưa có counterfactual branch ngắn

- **File:** `src/gsm_sim/world.py` — không có branch / fork / snapshot state ở bất kỳ đâu.
- **Logic:** hai run độc lập từ đầu tới cuối; càng về sau càng phân kỳ (vị trí, đơn được chào, pin,
  mệt, thời điểm sạc/nghỉ).
- **Bổ sung chưa nêu trong nhận xét cũ:** `world.py:333` ghi `pending_targets[aid] = cell` ⇒ **một
  lần follow làm đổi lời khuyên phát cho mọi người hỏi sau trong cùng bucket** ⇒ phân kỳ **nhanh
  hơn** trực giác.
- **Nền tốt để dựng nhánh:** CRN giữ nghiêm (`demand.py:1-8` sinh trace ngoại sinh trước khi chạy;
  `parallel.py:192-202` `assert_crn` kiểm hai nhánh cùng danh sách đơn) ⇒ phân kỳ hoàn toàn nội sinh.

## H-03 🟠 Giới hạn của kết luận equilibrium — phải nói kèm khi báo cáo ra ngoài

- **Cầu hoàn toàn ngoại sinh, không co giãn theo thời gian chờ** — `src/gsm_sim/demand.py:1-8`
  (*"Trace ngoại sinh = danh sách Order … được sinh TRƯỚC khi chạy sim → dùng chung cho mọi arm"*).
  Khách không bỏ app khi chờ lâu ⇒ kết luận "phủ cao vô hại" có thể đổi nếu mô hình hoá điều đó.
- **Chỉ đúng cho kênh vị trí.** 3 kênh còn lại đang TẮT (xem §Config C-01); chưa ai đo equilibrium
  cho chúng.
- **PoA đo trên B3w `wait_only`** ⇒ là **cận DƯỚI** của khoảng cách, không phải giá trị thật
  (UPDATE-088 §Adversarial #3).
- **Toán tử belief v1** (mean theo seed, không EMA) — kết luận γ=0 phân kỳ có thể dịu đi với
  smoothing, chưa quét (UPDATE-088 §Adversarial #2).
- **Free-rider gap chưa có CI riêng** — mới là điểm ước lượng 30 seed (UPDATE-088 §Adversarial #4).

## H-04-bis ✅ ĐÍNH CHÍNH BẮT BUỘC — `5364395` đã vượt qua §H-04 bên dưới

> **Đọc mục này TRƯỚC §H-04.** §H-04 rà tại `66268cc`. Trong lúc tôi soạn báo cáo, phiên khác đã
> push **`5364395` "đóng Cycle W — 36 finding từ 4 lượt review đối kháng, suite 707/5, fingerprint
> IDENTICAL"**. Tôi **verify lại từng mục trên code mới** (không tin commit message):

| Mã | Trạng thái tại `5364395` | Bằng chứng tôi tự đọc |
|---|---|---|
| **W-6** | ✅ **ĐÃ SỬA** | `pipeline.py:213-214` nay là `or {"passed": None, "errors": []}` — hết bịa `True` |
| **W-7** | ✅ **ĐÃ SỬA** | `pipeline.py:222-228` có `close()` + `__enter__` + `__exit__` |
| **F-6** | ✅ **ĐÃ SỬA** | `episode_store.py:86-91` lọc `e["origin"] == "pipeline"` |
| **W-4 regex** | ✅ **ĐÃ SỬA** | `advice_lifecycle_event.schema.json:59,65` siết `([01]\d\|2[0-3])` + tháng/ngày/offset. **Re-test:** `T24:00:00` nay **BỊ TỪ CHỐI** ✅ |
| 5 test `.pending` | ✅ **ĐÃ VÀO SUITE** | `tests/test_lifecycle_review_fixes.py` (16.340 bytes); file `.pending` đã xoá |
| Full suite + fingerprint | ✅ **ĐÃ CHẠY** | `5364395`: **707 passed / 5 skipped**, fingerprint IDENTICAL |
| positioning thiếu `decided` | ✅ **ĐÃ SỬA** (theo commit) | ghi ở board §2 — tôi chưa tự đo lại |

⇒ **§H-04 bên dưới giữ lại làm bản ghi lịch sử tại `66268cc`, KHÔNG phải trạng thái hiện hành.**

### Nhưng MỘT phát hiện của tôi SỐNG SÓT — và rộng hơn ban đầu

`5364395` sửa **triệu chứng** (siết regex của đúng schema lifecycle) chứ **không sửa nguyên nhân**:

- `src/gsm_core/schema_registry.py:143` vẫn `return Draft202012Validator(self.schema(entity, version))`
  — **không truyền `format_checker`** ⇒ từ khoá `"format"` **không có hiệu lực trên MỌI schema**.
- Quét toàn bộ `schemas/`: **15 schema khai `"format": "date-time"` mà KHÔNG có `pattern` dự phòng**
  ⇒ 15 schema này hiện **không validate ngày giờ gì cả**:
  `advisor/advice_request` · `advisor/composed_advice` · `advisor/solver_report` · `l0/policy_bundle` ·
  `l1/app_event` · `l1/gps_ping` · `l1/payout_ledger` · `l1/policy_change_event` ·
  `l1/swap_transaction` · `l1/trip_record` · `l2i/inferred_activity` · `l3/allocation_input` ·
  `l3/bonus_gap_input` · `l3/shift_plan_input` · `l3/shift_plan_input@1.0.0`.
- **Reproduce (tự chạy):** `bonus_gap_input` với `t_now = "KHONG-PHAI-NGAY-THANG"` →
  `SchemaRegistry.validate()` trả **`[]` = HỢP LỆ**.

**Vì sao đáng sửa:** đây đúng ranh giới mà Cường cảnh báo — *"data từ hệ sinh thái Vingroup/GSM chưa
rõ dtype, output API ngoài phải normalize"*. Hai lựa chọn: (a) truyền `format_checker` một lần ở
`schema_registry.py:143` (sửa cả 15 chỗ); (b) thêm `pattern` cho từng schema (15 chỗ, dễ quên chỗ
thứ 16). **Chưa đề xuất chọn cái nào — cần plan.** Ghi thành mục `REVIEW-092-5`.

## H-04 🟠 (LỊCH SỬ tại `66268cc` — đã bị `5364395` vượt qua, xem §H-04-bis)

| Mã | File · mục | Logic sai | Trạng thái |
|---|---|---|---|
| **W-6** | `src/gsm_core/advisor/pipeline.py:209` | `verify_result=self.last_verify_result or {"passed": True, "errors": []}` — khi dict rỗng, `or` trả nhánh phải ⇒ recorder ghi `passed=True` cho request **chưa verify**. Reset ở `pipeline.py:64` (`self.last_verify_result = {}`) biến lỗi hiếm thành **hệ thống** ở nhánh R5. Episode ghi `passed=None` (đúng) ⇒ **hai audit trail nói ngược nhau về cùng một request** | ❌ chưa sửa |
| **F-6** | `src/gsm_core/advisor/episode_store.py:85-86` | `count_episodes()` = `len(decision_state(self.log.events()))` — đếm distinct decision trên **toàn bộ** log, **không lọc `origin`** ⇒ UI/sim/pipeline ghi chung một file thì số này vô nghĩa. Kèm full-scan mỗi lần gọi (đo cũ: 20k event ⇒ 149 ms) | ❌ chưa sửa |
| **W-7** | `src/gsm_core/advisor/pipeline.py` (toàn file) | `AdvisorPipeline` **không có** `close()` / `__enter__` / `__exit__`. `EpisodeStore` đã có (`episode_store.py:49-56`) nhưng **12/13 call site đi qua pipeline** ⇒ LAYEROUT-16 (`PermissionError WinError 32` khi cleanup TemporaryDirectory trên Windows) **chưa đóng thật** | ❌ chưa sửa |
| **W-4** (phần còn lại) | `schemas/advisor/advice_lifecycle_event.schema.json` — `occurred_at.pattern` **+ nguyên nhân sâu hơn: `src/gsm_core/schema_registry.py:143`** | Regex giờ vẫn `\d{2}`, chưa siết `([01]\d\|2[0-3])`. **Nguyên nhân sâu hơn ghi chép gốc:** `_validator()` dựng `Draft202012Validator(schema)` **KHÔNG truyền `format_checker`** ⇒ `"format": "date-time"` trong schema là **trang trí, không có hiệu lực** — nên regex là lan can DUY NHẤT. Đường UI được `routers/advice.py:62` `le=1439` che, **producer khác ghi thẳng vào store thì không** | ⚠ nửa vời |

**Thêm — nợ của chính cycle W:**

- **5 test reproduce nằm NGOÀI suite**: `research/audit/2026-07-29-cycle-w-review/test_review_fixes.py.pending`
  (5.766 bytes, đuôi `.pending` ⇒ pytest không nhặt). Test không chạy = **lan can chết**, đúng bài
  học T-046 quy tắc 5+6 mà chính repo tự ghi.
- **Full suite + fingerprint chưa chạy lại** sau 13 fix — `tracking/updates/UPDATE-091.md:49-50` để
  trống ô Kiểm chứng. Con số "653 passed / 5 skipped" của commit `32a20c7` là đo **trước** loạt fix.
- **Positioning thiếu event `decided` per-actor phía sim** (`UPDATE-091:81-85` tự thú) ⇒ mẫu số
  under-count. "Một luật" đúng, "một số" chưa.

## H-05 🔴 Định nghĩa "adherence" chưa chốt — BUG-EVAL-ARGMAX thứ ba đang chờ

- **File:** `research/audit/2026-07-29-cycle-w-review/findings.md:61, 83-85`.
- **Logic:** `accept_lift` cho **76,9%** nếu đếm theo DECISION (gộp bucket 30′), **53,6%** nếu đếm
  theo EVENT (gate fire mỗi tick 2′). 112 event → 65 decision.
- **Chưa chốt ⇒ mọi báo cáo adherence về sau đều có thể sai.** Đây là câu hỏi thiết kế cho Cường,
  không phải bug code.

## H-06 🔴 B6-PARITY — cơ chế thông minh chỉ tồn tại trong SIM (nghiêm trọng nhất)

- **Lệnh tự verify:**
  - `grep -rn "market_state\|capacity_alloc\|standby" ui/` → **0 hit**
  - `grep -rn "market_state\|MarketState" src/gsm_core/advisor/` → **0 hit**
- **File / mục:**
  - `ui/backend/app/adapters/advisor.py:190` — `report = bonus_feasibility.solve(gi, policy())`.
    **Chỉ S1.** 8 solver còn lại không có mặt trên đường tài xế thật nhìn thấy.
  - `src/gsm_core/advisor/router.py:14-22` liệt kê 9 solver, nhưng `pipeline.py:59` nhận
    `solver_reports` **từ caller** ⇒ pipeline **không tự chạy solver nào**.
- **Hệ quả:** hồ sơ `research/audit/2026-07-27-current-state/02-*` §3 tự ghi đúng —
  ***"A/B đang đo behavior khác product ship"***. Mọi số Δ của ĐA-08 là số của **sim**, không phải
  của sản phẩm đang chạy.

## H-07 🔴 Không có dữ liệu thật

- **File:** toàn bộ trong `data/mock/` (`data/mock/v1/`, `data/mock/realdata-v1/`).
- **Logic:** `realdata-v1` đúng **shape** bảng GSM (13 bảng L1R) nhưng **số do mockgen sinh**
  (`src/gsm_core/mockgen/realdata.py`, seed_base trong `manifest.json`).
- ⇒ Mọi kết luận hiện tại là kết luận **về thế giới mô phỏng**.

## H-08 🔴 Policy: hai thế giới chưa nối nhau

| Khoản | Structured? | File |
|---|---|---|
| Cước, điểm, mốc thưởng, ngưỡng, khoán tuần, `driver_share` | ✅ có | `schemas/l0/policy_bundle.schema.json` |
| **Giá đổi pin · điện · thuê pin · bảo dưỡng · thuế** | ❌ **không có ở BẤT KỲ schema nào** | mới là văn xuôi ở `research/economics/driver-cost-structure-2026.md` |
| Corpus text | ✅ có nhưng **tách rời** | `research/policy/t004-*.json`; `src/gsm_core/advisor/policy_kb.py:38-48` keyword match 7 record — **trích dẫn không trỏ tới trường số nào** |

- **⚠ ĐÍNH CHÍNH `OPEN-THREADS` §B3 — `effective_from/to` ĐÃ LÀM RỒI, đừng làm lại.**
  `OPEN-THREADS-2026-07-28.md` §B3 ghi *"`policy.py:31-48` vứt cả hai trường"*. **Sai ở thời điểm
  hôm nay**: `src/gsm_core/policy.py:29-34` khai field, `:54-55` đọc từ record, `:58-72`
  `is_valid_at()` với **tri-state đúng** (`None` = KHÔNG BIẾT, tách khỏi "còn hiệu lực" — chính bài
  học `soc_pct=None`). Sim đọc ở `advice_bridge.py:151-158`, world cảnh báo ở `world.py:100-103`.
  Làm ở Cycle P/①.
- **Cái CÒN THIẾU thật (hẹp hơn nhiều):**
  1. `is_valid_at` chỉ được gọi **một lần lúc khởi tạo world** cho `_BASE_DATE`
     (`advice_bridge.py:158`) — **solver không nhận `as_of` theo từng request**;
  2. ngoài hạn �⇒ **chỉ `log`** (`world.py:100-103`), **không fail-closed** — advice vẫn phát;
  3. `configs/pilot_dongda.yaml` **không đặt** `meta.policy_effective_from` ⇒ thực tế
     `policy_valid_today = None` (UNKNOWN) ⇒ lan can chưa bao giờ chạy trong cấu hình đang dùng.
- **Router vẫn không đọc policy**: `src/gsm_core/advisor/router.py` là keyword zero-ML thuần ⇒
  **A1 vẫn chưa có gì** (nhưng điều kiện tiên quyết của nó thì đã xong, khác với ghi chép cũ).

## H-09 ⚠️ Hidden fallback còn sống — lần thứ ba của cùng một mẫu lỗi

- `soc_pct = None` từ L1R ⇒ `shift_dp` **im lặng giả định pin đầy** — khuyên tài xế 15% pin y như
  100% (T-045e, còn mở; ghi ở `OPEN-THREADS` §B4).
- Hai lần trước cùng mẫu: `supply_cell_hhi` đọc field không tồn tại trả **0.0 âm thầm** (UPDATE-075);
  `acceptance_rate` fallback **1.0** ⇒ gate thưởng đi qua nhầm (UPDATE-077, **đã sửa**).

## H-10 🔴 Hành vi tài xế còn quá "ngoan"

- **Lệnh tự verify:** `grep -rin "no_show\|dropout\|sick\|churn" src/` → chỉ có `world.py:295` dùng
  từ "churn" trong comment; **không có cơ chế nào**.
- **File:** `src/gsm_sim/archetypes.py:36-54` — 7 archetype, ca sinh bằng `rng.uniform(*shift_len)`.
- **Thiếu:** không nghỉ đột xuất, không ốm, không bỏ nghề. Ngày-qua-ngày **autocorr ≈ 0** (V-08,
  UPDATE-053 §2) ⇒ chưa có persistence thói quen (D-SIM-16 `DEFERRED`).
- **Lưu ý:** P1 có nhãn *"part-time TỐI"* (`archetypes.py:37`, ca 3–4h) nhưng đó là **ca ngắn tất
  định**, không phải hành vi bất ổn.

## H-11 🔴 17 mục visual chưa ai xem

`V-01 … V-17` trong `tracking/PENDING-REVIEW.md`, tồn từ 2026-07-25. Theo `CLAUDE.md §4b`
*"hoãn ≠ waive"* ⇒ **chưa mục nào được nghiệm thu bằng mắt người.**

## H-12 Nợ kỹ thuật khác

| # | File · mục | Logic |
|---|---|---|
| a | ~~`src/gsm_sim/behavior.py:86`~~ | **⚠ ĐÍNH CHÍNH `OPEN-THREADS` §B3: T-045b ĐÃ LÀM RỒI.** Đã đổi tên thành `pickup_disutility_vnd_per_km` (`behavior.py:58, 86-91, 105, 114`), sổ chi phí tiền mặt tách riêng ở `actor.cost_vnd` (`world.py:97-98, 349-352`), config có `vehicle.swap_fee_vnd: 0` + `cash_cost_vnd_per_km: 0` (`configs/pilot_dongda.yaml:268-269`). **Còn thiếu:** cả hai mặc định **0** ⇒ **chưa ai chạy quét độ nhạy** với số thật (30–250đ/km theo `research/economics/`) |
| b | dispatcher (T-045c) | Bỏ đơn oan 293/3.520 = 8,3%. Đường code đã biến mất khi viết lại Hungarian (`src/gsm_sim/dispatcher.py:121-134`) nhưng **chưa đo lại xác nhận về 0** ⇒ không được ghi DONE |
| c | `src/gsm_core/advisor/episode_store.py:97-102` | `advice_cache` vẫn `INSERT OR REPLACE` **cùng file SQLite** với bảng append-only ⇒ lời hứa append-only là của *bảng* `advice_events`, không phải của *file* |
| d | `SolverReport.problem_digest` | Có sẵn ở mọi solver nhưng **chưa ai dùng làm khoá cache** (ý tưởng A2 của Cường, `OPEN-THREADS` §A2) |
| e | `tracking/PROJECT-GRAPH.md` §9 | **Lệnh validation của chính graph đang FAIL**: 18 UPDATE (074–091) không có link trong graph ⇒ `throw "Missing graph link"`. Đã sửa trong cycle này (thêm §3.7) |

---

# PHẦN 3 — CONFIG: cái gì đang bật, cái gì đang tắt

Nguồn: `configs/pilot_dongda.yaml` khối `advice:`.

| Khoá | Giá trị hiện hành | Ý nghĩa / vì sao |
|---|---|---|
| `advice.enabled` | `false` | mặc định file; `parallel._cfg_with` ghi đè theo arm |
| `advice.coverage` | `single` | ĐA-08 yêu cầu `all` khi đánh giá tác động hệ thống — **phải đổi thủ công khi đo guardrail** |
| **C-01** `channels.shift_plan` | **`false`** | TẮT theo điều khoản BẢN-CUỐI ĐA-07, Cường duyệt (UPDATE-087): n=100 seed cho thu nhập ns, served −0,33đp SIG, đơn chết +4,1 SIG |
| **C-01** `channels.accept_lift` | **`false`** | ĐA-07: giữ TẮT |
| **C-01** `channels.shift_extend` | **`false`** | — |
| **C-01** `channels.rest_window` | **`false`** | — |
| **C-02** `positioning_overrides` | **`wait_only`** | ✅ Kênh DUY NHẤT đang bật. Cường duyệt 2026-07-28, PASS 9/9 ĐA-08 trên n=100 seed (payout_mean_all +6.016đ SIG · served +1,74đp · đơn chết −23,4 · Gini & HHI GIẢM) |
| `interval_min` | `30` | |
| `accept_lift_step` / `_max` | `0.10` / `0.15` | chỉ có nghĩa khi C-01 bật lại |
| `max_realized_accept` | `0.93` | đo được, không bịa |
| `rest_defer_max_min` | `120` | lan can cứng |
| `shift_extend_max_min` | `60` | lan can cứng |
| `advice.market_demand_override` | không đặt | hook fictitious play (ĐA-09); chỉ `MarketStateProducer` đọc — `src/gsm_sim/market_state.py:87-90`. **Bản năng tài xế tuyệt đối không đọc** (test cách ly canh) |

**Hệ quả phải nhớ:** *"advisor"* trong mọi số đo hiện hành = **đúng một kênh vị trí**. Bốn kênh còn
lại đang im lặng theo lệnh. Đừng đọc Δ hiện tại như hiệu quả của "cả advisor".

Config khác đáng nhớ: `dispatch.candidate_ring_k_max = 6` (Q-07 đang mở — phủ 2,22 km trong khi
`eta_max = 11′` cho phép tới 3,14 km ⇒ tài xế thoả ETA ở 2,2–3,1 km bị loại **âm thầm**).

---

# PHẦN 4 — NHỮNG ĐIỀU CHƯA ĐẠT (danh sách gọn để đối chiếu)

| # | Chưa đạt | Mã tra |
|---|---|---|
| 1 | Đo nhân quả **từng lượt** advice (join `decision_id` → tiền) | H-01 |
| 2 | Counterfactual branch ngắn tại thời điểm advice | H-02 |
| 3 | Cầu co giãn / khách bỏ app khi chờ lâu | H-03 |
| 4 | Equilibrium cho 4 kênh còn lại (mới đo kênh vị trí) | H-03 |
| ~~5~~ | ~~3+1 finding Cycle W~~ ✅ **`5364395` đã sửa hết** | H-04-bis |
| **5b** | **CÒN MỞ — `schema_registry.py:143` không truyền `format_checker` ⇒ `"format"` vô hiệu lực trên MỌI schema; 15 schema khai `date-time` mà không có `pattern` dự phòng** (reproduce: `bonus_gap_input.t_now = "KHONG-PHAI-NGAY-THANG"` → hợp lệ) | H-04-bis |
| ~~6~~ | ~~Full suite + fingerprint~~ ✅ **707 passed / 5 skipped, fingerprint IDENTICAL** | H-04-bis |
| ~~7~~ | ~~5 test reproduce vào `tests/`~~ ✅ `tests/test_lifecycle_review_fixes.py` | H-04-bis |
| ~~8~~ | ~~Event `decided` per-actor cho positioning~~ ✅ theo `5364395` (tôi chưa tự đo lại) | H-04-bis |
| 9 | Chốt định nghĩa adherence (DECISION vs EVENT) | H-05 |
| 10 | **Parity SIM ↔ production: UI mới chạy 1/9 solver** | H-06 |
| 11 | Dữ liệu thật của GSM | H-07 |
| 12 | Nhánh `costs` trong `policy_bundle` schema (đổi pin/điện/thuê pin/bảo dưỡng) | H-08 |
| 13 | Solver nhận `as_of` **theo từng request** + **fail-closed** ngoài hạn + `meta.policy_effective_from` trong config pilot (*field & `is_valid_at` đã có — chỉ thiếu 3 điểm này*) | H-08 |
| 14 | Router đọc policy (A1) · cache theo `problem_digest` (A2) | H-08, H-12d |
| 15 | `soc_pct` từ L1R (hết hidden fallback "pin đầy") | H-09 |
| 16 | Hành vi bất ổn: no-show / ốm / bỏ nghề / persistence ngày-qua-ngày | H-10 |
| 17 | 17 mục visual V-01…V-17 | H-11 |
| 18 | Quét độ nhạy chi phí với số thật (*T-045b đã làm, nhưng `swap_fee_vnd`/`cash_cost_vnd_per_km` đều = 0*) · T-045c đo lại đơn bỏ oan | H-12a/b |

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/updates/UPDATE-092-review-doc-lai-han-che-va-cai-thien.md` | tạo | File này |
| `tracking/TODO.md` | sửa | Thêm khối REVIEW-092 (18 mục chưa đạt, có mã tra) |
| `tracking/PROJECT-GRAPH.md` | sửa | Thêm §3.7 (link 074–092 — **sửa luôn lỗi validation FAIL 18 link**) + dòng board |
| `tracking/PENDING-REVIEW.md` | sửa | Thêm **Q-13** (định nghĩa adherence) + **Q-14** (ưu tiên B6-PARITY) |
| `tracking/OPEN-THREADS-2026-07-28.md` | sửa | Banner ⛔ + gạch 2 mục §B3 đã xong ở Cycle P (chống làm lại việc đã làm) |

**Không sửa file code nào.** `git diff --stat` chỉ chạm `tracking/`.

## Docs đã cập nhật kèm theo

TODO ✅ · PROJECT-GRAPH ✅ · PENDING-REVIEW ✅ · SCOPE/DEFERRED/USER_STORIES: **không đổi** (review
không tạo scope mới; các mục H-* đều đã có chỗ trong TODO/DEFERRED hoặc là nhắc lại nợ cũ).

## Assumptions và evidence

| Claim | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| W-6 / F-6 / W-7 / W-4-regex còn nguyên | `OBSERVED-CODE` | Tôi đọc trực tiếp `pipeline.py:209`, `episode_store.py:85-86`, toàn `pipeline.py`, `advice_lifecycle_event.schema.json` | cao | Nếu sai ⇒ đã sửa ở đâu đó tôi không thấy; kiểm lại bằng grep |
| `grep counterfactual src/` = 0 | `OBSERVED-CODE` | tự chạy | cao | — |
| UI chỉ chạy S1 | `OBSERVED-CODE` | `adapters/advisor.py:190` + grep 0 hit | cao | — |
| Số equilibrium (γ, PoA, coverage) | `MOCK` (sim) | UPDATE-088 + `research/simulation/multi-agent-equilibrium.md`, ~220 run | trung bình | Số là của **sim**, không phải thế giới thật; cầu ngoại sinh |
| adherence draw là ngẫu nhiên hoá thật | `OBSERVED-CODE` | `advice_bridge.py:374, 395` — `rng.random() < p`, p chỉ theo archetype | cao | Nếu sai ⇒ đề xuất estimator phân tầng ở H-01 mất nền |
| "653 passed / 5 skipped" | `UNVERIFIED` | commit `32a20c7`; đo **trước** 13 fix Cycle W | thấp | Xem §Kiểm chứng |
| Graph validation đang FAIL 18 link | `OBSERVED-CODE` | tự chạy §9 của PROJECT-GRAPH | cao | — |
| **`OPEN-THREADS` §B3 đã lỗi thời ở 2 mục** | `OBSERVED-CODE` | `gsm_core/policy.py:29-34,54-55,58-72` · `behavior.py:58,86-91` · `world.py:97-98,349-352` · `configs/pilot_dongda.yaml:268-269` | cao | Nếu tin ghi chép cũ ⇒ **làm lại việc đã xong**. Xem §Adversarial #4 |

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| `git fetch` + so HEAD | local == `origin/main` == `66268ccb7ae`, tree sạch |
| `grep -ri counterfactual src/` | **0 hit** ✅ tự chạy |
| `grep -rn "market_state\|capacity_alloc\|standby" ui/` | **0 hit** ✅ tự chạy |
| `grep -rn "market_state\|MarketState" src/gsm_core/advisor/` | **0 hit** ✅ tự chạy |
| `grep -rin "no_show\|dropout\|sick" src/` | 0 cơ chế ✅ tự chạy |
| Graph validation §9 | **FAIL** — 18 link thiếu (074–091) ✅ tự chạy; **đã sửa trong cycle này** |
| Đọc verify 4 finding W-6/F-6/W-7/W-4 | **còn nguyên** cả 4 ✅ |
| **Reproduce W-4 bằng code** (không suy diễn) | ✅ `SchemaRegistry.validate('advice_lifecycle_event', {…'occurred_at':'2026-07-29T24:00:00+07:00'…})` → **`[]` (hợp lệ)**; `datetime.fromisoformat` cùng chuỗi → `ValueError: hour must be in 0..23`. ⇒ record độc **ghi được** vào store append-only rồi giết `decision_state`. **Nguyên nhân sâu:** `schema_registry.py:143` không truyền `format_checker` |
| `pytest tests/test_lifecycle_store.py` (basetemp hợp lệ) | **23 passed** ✅ |
| **Full pytest suite** | xem §Seeds bên dưới |

> ⚠ **BẪY MÔI TRƯỜNG — ghi để người sau không báo động giả.** Lần chạy đầu của tôi ra
> **625 passed / 5 skipped / 62 errors**, mọi error là `PermissionError` — trông **rất giống**
> W-7/LAYEROUT-16 (`WinError 32`, file bị giữ). **KHÔNG PHẢI.** Đọc kỹ: `PermissionError
> [WinError 5] Access is denied: 'C:\Users\…\AppData\Local\Temp\pytest-of-…'` tại
> `_pytest/pathlib.py:175` — **WinError 5 = access denied** (sandbox chặn `tmp_path`), không phải
> **WinError 32 = file in use**. Chạy lại đúng file test với `--basetemp` trỏ vào thư mục ghi được:
> **23 passed, 0 error**. ⇒ Luôn phân biệt hai mã lỗi trước khi quy cho code.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `pytest tests/test_lifecycle_store.py -q -p no:cacheprovider --basetemp=<ghi được>` | — | — | **23 passed** ✅ | — |
| `SchemaRegistry.validate` với `occurred_at='…T24:00:00+07:00'` | — | — | **`[]` = hợp lệ** (reproduce W-4) ✅ | — |
| `validate('bonus_gap_input', t_now='KHONG-PHAI-NGAY-THANG')` | — | — | **`[]` = HỢP LỆ** ⇒ `format` không được thực thi (REVIEW-092-5) ✅ | — |
| `validate` lại `T24:00:00` sau `5364395` | — | — | **BỊ TỪ CHỐI** ✅ (regex mới) | — |
| Full suite | — | — | **707 passed / 5 skipped** — số của `5364395`, **không phải tôi chạy** | Tôi chưa tự chạy xong full suite (xem ghi chú) |
| (không chạy sim) | — | — | — | Cycle này docs-only, không đo lại số sim nào |

> ⚠ **NGUỒN CỦA CON SỐ SUITE — đọc kỹ trước khi trích dẫn.**
> 1. **707 passed / 5 skipped** là số của commit **`5364395`** (phiên khác), tôi **chép lại**, không
>    tự chạy. Nhãn: `UNVERIFIED-BY-ME`.
> 2. Lần chạy full suite của **tôi** chưa kết thúc khi commit ⇒ không có số độc lập.
> 3. **"653 passed"** (commit `32a20c7`) đã **lỗi thời** — đo trước Cycle W.
> 4. **Bắt buộc dùng `--basetemp` trỏ vào thư mục ghi được** — nếu không sẽ gặp bẫy ở §Kiểm chứng
>    và tưởng nhầm là lỗi code.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** docs-only. `git diff --stat` chỉ chạm `tracking/*.md`; không đổi dynamics, tham số mặc
  định, metric, visual encoding, control hay cách stakeholder diễn giải kết quả.
- **Không tự cấp quyền gì:** hàng đợi V-01…V-17 **vẫn nguyên**, cycle này không waive mục nào.

## Adversarial self-review / flaws found

1. **Điều gì có thể làm báo cáo này trông đúng nhưng sai?** Tôi đọc code tĩnh, **không chạy sim** để
   xác nhận hành vi. Ví dụ H-06: tôi kết luận "UI chỉ chạy S1" từ `adapters/advisor.py:190` + grep;
   nếu có đường gọi solver động qua `router.py` mà tôi bỏ sót thì kết luận nhẹ đi. Đã grep 2 hướng,
   nhưng grep không bắt được gọi gián tiếp qua chuỗi tên.
2. **Bằng chứng yếu nhất:** phần equilibrium (§1.2) tôi **lấy nguyên số từ UPDATE-088**, không tự
   chạy lại ~220 run. Nếu artifact đó sai thì §1.2 sai theo. Đã đánh nhãn `MOCK` + confidence trung
   bình. Ngược lại, mọi mục PHẦN 2 đều là `OBSERVED-CODE` tôi tự đọc.
3. **Rủi ro của chính file này:** nó là **bản đồ hạn chế**, dễ bị đọc thành "danh sách việc đã phân
   loại xong". Không mục nào ở đây đã được duyệt hướng sửa. H-01 đặc biệt nguy hiểm: nếu ai đọc lướt
   rồi đi làm "so follow vs ignore" thì tạo ra BUG-EVAL-ARGMAX thứ ba — vì thế cạm bẫy được viết
   **ngay trong mục**, không đẩy xuống cuối.
4. **TÔI ĐÃ MẮC ĐÚNG LỖI MÌNH ĐANG CẢNH BÁO — và tự bắt được trước khi commit.** Bản nháp đầu của
   §H-08 và §H-12a chép thẳng từ `OPEN-THREADS-2026-07-28.md` §B3 (*"`policy.py` vứt
   `effective_from/to`"*, *"T-045b chưa làm"*). **Cả hai đã SAI** — code Cycle P đã làm xong cả hai
   (`gsm_core/policy.py:29-34,54-55,58-72` · `behavior.py:58,86-91` · `world.py:97-98,349-352` ·
   `configs/pilot_dongda.yaml:268-269`). Bắt được vì đọc code chứ không tin ghi chép.
   ⇒ **Quy tắc rút ra: `OPEN-THREADS` là bộ nhớ PHIÊN, không phải trạng thái hiện hành.** Đã ghi
   đính chính vào cả UPDATE này và TODO. Ai đọc `OPEN-THREADS` §B2/B3/B4 về sau phải verify bằng
   code trước khi claim.
5. **Baseline đã so:** `66268cc` vs ba nhận xét cũ của Cường + hồ sơ `02-*` (parity) + `findings.md`
   (Cycle W). Giả thuyết đã loại trừ: *"nhận xét herding vẫn còn nguyên"* — **SAI**, code đã vượt qua
   ở tầng sim (§1.1) và có số đo (§1.2); cái còn nguyên là **parity với production** (H-06), một vấn
   đề khác hẳn.
6. **Flaw còn mở → map ID:** H-01/H-02 → mục mới `REVIEW-092-1/2` trong TODO · H-04 → nợ Cycle W đã
   có trong TODO · H-05 → câu hỏi cho Cường (PENDING-REVIEW) · H-06 → mục mới **`B6-PARITY`** ·
   H-08 → A1/A2 + `OPEN-THREADS` §C · H-09 → T-045e · H-10 → D-SIM-16 · H-11 → V-01..V-17 ·
   H-12a/b → T-045b/c · H-12e → **đã sửa trong cycle này**.

## Expansion checkpoint (T-039)

1. **Schema:** nếu làm H-01, cần một entity mới kiểu `advice_outcome` (khoá `(run_id, decision_id)`,
   mang Δpayout/Δtrips trong cửa sổ đo + nhãn phương pháp). **Chưa đề xuất field cụ thể** — chờ chốt
   phương pháp (nhánh phản thực vs estimator phân tầng). Riêng `policy_bundle` cần nhánh `costs`
   (H-08) — đã ghi ở `OPEN-THREADS` §C, chưa duyệt.
2. **Bài toán tối ưu:** H-01 mở ra một residual formalize được — *"chọn tập lượt advice nào để phát
   sao cho tổng Δ kỳ vọng lớn nhất dưới ràng buộc cadence"*, tức là bài toán chọn tập chứ không phải
   bài toán từng lượt. **Chỉ ghi nhận, không triển khai.**
3. **Tính năng:** `decision_id` + `adherence_view` vừa có đủ để làm ĐA-04 (cadence memory) — đúng
   thứ tự Cường đã nêu. Không đề xuất tính năng mới ngoài đó.

## Follow-up / defer phát sinh

| ID | Nội dung | Severity | Điều kiện đóng |
|---|---|---|---|
| `REVIEW-092-1` | Đo nhân quả từng lượt advice (H-01) — **phải chốt phương pháp trong plan trước khi code** | HIGH | Có estimator + test đối chiếu ground truth độc lập |
| `REVIEW-092-2` | Counterfactual branch ngắn (H-02) | HIGH | Nhánh chạy được + chứng minh không phá CRN |
| **`B6-PARITY`** | **UI mới chạy 1/9 solver ⇒ A/B đo sản phẩm khác sản phẩm ship (H-06)** | **HIGH** | Đường UI gọi cùng `AdviceDecisionService` với sim |
| `REVIEW-092-3` | Chốt định nghĩa adherence: DECISION hay EVENT (H-05) | MED | Cường chốt → ghi vào spec |
| `REVIEW-092-4` | Cầu co giãn theo thời gian chờ (H-03) | MED | → **DEFERRED** (ngoài scope hiện tại), mở lại khi cần kết luận về phủ cao |
| **`REVIEW-092-5`** | **`schema_registry.py:143` không truyền `format_checker` ⇒ `"format"` chết trên 15 schema (H-04-bis)** | MED | Chọn (a) `format_checker` một chỗ hay (b) `pattern` từng schema; có test chứng minh chuỗi rác BỊ TỪ CHỐI |
| ~~—~~ | ~~W-6 / F-6 / W-7 / W-4-regex / 5 test `.pending` / full suite / fingerprint~~ | — | ✅ **ĐÓNG bởi `5364395`** — đã verify lại từng cái trên code mới, xem §H-04-bis |

## ⏳ Nhắc PENDING-REVIEW

**V-01…V-17** visual (Cường: *"hỏi lại sau"*) · **Q-03** corpus Khánh · **Q-04** UX proposal ·
**Q-07** dispatch H3 (đang theo (c)) · **BUG-MOCKGEN-CLI** · nợ UI card `standby_zone` (chặn bởi
Q-04) · **ĐA-05 code chờ verdict** (UPDATE-091, đang WIP) · **MỚI: REVIEW-092 — H-05 (định nghĩa
adherence) cần Cường chốt; B6-PARITY cần Cường xếp ưu tiên.**
