# SOI — mẫu số adherence (`D-M3-01`): 48 finding thô · 12 tôi tự kiểm ĐÚNG · 3 độ lớn tự đo · 0 qua phản biện tự động

Ngày 2026-07-30 · Trạng thái: **`PARTIAL`** — vòng phản biện tự động KHÔNG chạy được (§0), nhưng **12 finding đã được tôi tự kiểm** (§1) và **3 độ lớn đã được tôi tự đo** (§2, §2b, §3).

Workflow soi 5 tầng × 5 kênh (`wf_e65b275f-598`). Mục tiêu: tìm cạn kiệt mọi chỗ mẫu số adherence
hỏng, phản biện đối kháng, rồi sinh spec thi công.

---

## 0. 🔴 ĐỌC TRƯỚC — hai thất bại của quy trình, một trong đó là lỗi của tôi

### 0.1 Vòng phản biện KHÔNG chạy: 16/16 agent phản biện fail (session limit)

Kết quả workflow trả về `n_song_sot: 8, n_bi_bac: 0`. **Con số đó là SAI và nó là lỗi trong script
của tôi.** Logic phân loại:

```js
const nBac = j.verdicts.filter((v) => v.bac_bo).length
if (nBac >= 2) killed.push(j); else survived.push(j)
```

Khi cả hai agent phản biện fail, `verdicts` là mảng **rỗng** ⇒ `nBac = 0` ⇒ `0 >= 2` sai ⇒ finding
được xếp vào **`survived`**. Tức script của tôi **đếm "không có phán quyết" thành "đã sống sót qua
phản biện"**.

Đây đúng là họ lỗi `BUG-EVAL-ARGMAX` mà cả cycle này sinh ra để diệt — **mẫu số rỗng cho ra một
kết luận trông như dương tính**. Tôi đã viết chính lỗi đó vào công cụ dùng để tìm chính lỗi đó.

**Sửa cho lần sau:** phải đòi `verdicts.length === LENSES.length` mới được xếp loại; thiếu phán
quyết ⇒ trạng thái thứ ba **`CHƯA_PHẢN_BIỆN`**, không được gộp vào `survived`.

⇒ **Không finding nào dưới đây đã qua phản biện đối kháng.** Nhãn duy nhất đáng tin là "tôi tự kiểm
lại bằng cách đọc code" hoặc "tôi tự đo" — tôi làm việc đó cho 12 finding (§1) và 3 độ lớn (§2/§2b/§3).

### 0.2 Tầng L2 (`world.py`) hoàn toàn KHÔNG được soi

`soi:L2-world` fail vì session limit. Đây là tầng quyết định *"event nào được ghi, khi nào"* — tức
đúng tầng chứa nguyên nhân trực tiếp của mẫu số thiếu. **Kết quả soi hiện tại có một lỗ ở giữa.**

---

## 1. ✅ Finding tôi TỰ KIỂM bằng đọc code — đều ĐÚNG

| # | Claim | Bằng chứng tôi tự đọc | Hậu quả |
| --- | --- | --- | --- |
| **L1-01** | `rest_window` là kênh **duy nhất** không rút coin | `advice_bridge.py` `should_defer_rest` không có `coin_follows` ở bất kỳ dòng nào; 4 kênh kia: `:505` `:527` `:577` `:823` | adherence cắm cứng 1,0 |
| **L1-03** | `check_shift_extend` trả `0.0` khi coin=False **không để lại dấu vết** | `advice_bridge.py:823-824` `if not self.coin_follows(...): return 0.0` | mẫu số chỉ gồm người ĐÃ THEO |
| **L3-01** | Sửa tầng 1+2 mà không sửa `_sim_steps` thì **VẪN 100%** | `projections.py` `if kind in _ALWAYS_FOLLOWED or detail.get("followed")` — với 2 kind đó, bước `followed` được thêm **bất kể** `detail["followed"]` | fix một nửa = không fix |
> ## ✅ PHẢN BIỆN 2026-07-31 — bốn finding nặng nhất, tôi TỰ làm (agent phản biện chết quota 3 lần)
>
> Không dùng agent nữa — đọc code + **reproduce qua đường ống thật** (`decision_state`,
> `adherence_view`, `evaluate`). Kết quả: **L3-03 ĐÚNG · L4-01 ĐÚNG (nặng hơn mô tả) ·
> L4-03 ĐÚNG (cần Cường chốt cách sửa) · L4-07 ĐÚNG (nặng nhất)**.
>
> - **L3-03** reproduce: bấm "Làm theo" 14:00 → đổi ý "Bỏ qua" 15:00 ⇒ hệ thống ghi `followed`.
>   Đối chứng `occurred_at` khác nhau ⇒ ghi đúng `dismissed` ⇒ nguyên nhân đúng là **thế hoà**.
>   ✅ **ĐÃ SỬA**: tie-break thêm `observed_at` (thời điểm server nhận) trước `event_id`.
> - **L4-01** nặng hơn mô tả: không chỉ `event_adherence = None` — đo được
>   `event_followed=1 > event_decided=0`, tức **tử số vượt mẫu số**, trạng thái BẤT KHẢ mà
>   không cổng nào bắt. ✅ **ĐÃ SỬA**: `displayed` (sản phẩm) tính vào mẫu số EVENT cùng
>   `decided` (sim) — hai tên của cùng một sự kiện "advisor đã nói".
> - **L4-03** reproduce: `decision_bucket(0)==decision_bucket(25)` nhưng `min_gap=20` ⇒ ở
>   t=25′ cadence trả **PRESENT** (card tới tay tài xế) trong khi `event_id` displayed trùng
>   khoá bucket ⇒ store dedupe ⇒ **không event, không tiêu ngân sách**. ⏳ **CHƯA SỬA** —
>   sửa đúng là làm hai lưới nhất quán (`min_gap` ≥ `DECISION_BUCKET_MIN`), nhưng 20′ là
>   baseline Cường duyệt (`D-ĐA04-02`) và đổi nó là ĐỔI CHÍNH SÁCH ⇒ **cần Cường chốt**
>   (thêm vào PENDING-REVIEW).
> - **L4-07** (nặng nhất) reproduce: `cards.js` dựng `advice_id` BỊA (`brief-{date}`/
>   `recap-{date}`) cho card im lặng, `_render` vẫn vẽ nút ⇒ một cú bấm tạo decision+followed
>   cho lời khuyên **advisor chưa từng đưa** ⇒ `decision_adherence = 100%` cho quyết định MA.
>   ✅ **ĐÃ SỬA hai tầng**: client không vẽ nút trên card im lặng (nút "Đã hiểu" không ghi
>   event); boundary từ chối `advice_id` ngoài namespace advisor (422, không ghi gì).
>
> **Vòng 2 (cùng ngày) — thêm 5 finding phản biện xong:**
> - **L4-04 ĐÚNG** (`GET /advice` trả silent card mà KHÔNG ghi event nào ⇒ mẫu số "advisor
>   ĐỊNH nói nhưng bị nén" mất hẳn ở sản phẩm, `adherence_view["suppressed"]` luôn 0 ⇒ hai
>   đường không so được dù chung projection). ✅ **ĐÃ SỬA**: `_note_suppressed` ghi event
>   `suppressed` với `decision_id` hậu tố `-sup` (đúng tiền lệ sim, KHÔNG vào mẫu số `decided`).
> - **L4-09 ĐÚNG** (`topic` default `"bonus"` — client chỉ gửi brief/nudge/recap ⇒ namespace
>   mồ côi có cooldown/dismiss riêng không ai nuôi). ✅ **ĐÃ SỬA**: `CLIENT_TOPICS` +
>   `DEFAULT_TOPIC="brief"`, test canh default phải nằm trong tập topic client thật.
> - **L4-07(SOI) ĐÚNG** (`SHIFT_START_MIN = 6*60` cứng cho MỌI tài xế trong khi
>   `shift_end_min` đã là query param ⇒ bất đối xứng, pha ca của tài xế ca đêm sai hoàn
>   toàn). ✅ **ĐÃ SỬA**: tham số hoá `shift_start_min`; hằng cũ còn là default demo.
>   ⚠ **LỆCH MÃ đã phát hiện**: `PLAN` §5 gọi `L4-07` là "card im lặng vẽ nút advice_id bịa",
>   `SOI` §4 gọi `L4-07` là "SHIFT_START_MIN cứng" — HAI finding khác nhau cùng mã. Cả hai
>   đều ĐÚNG và cả hai đã sửa; đánh số lại khi có dịp.
> - **L4-08 = TRÙNG `D-R21`** (client gửi `at_min` giả `KIND_HOURS`), không phải finding mới.
>   `D-R21` đã phản biện hạ cấp và cố ý chưa sửa (cần cycle UI bỏ `KIND_HOURS` cả hai phía).
>   Fix `L3-03` hôm nay đã giải quyết PHẦN hệ quả của nó (đổi-ý-không-ghi-nhận).
> - **L4-05 ĐÚNG về ngữ nghĩa, sev hạ xuống TB**: `followed` ở sản phẩm là **cú bấm tự khai**,
>   ở sim là **đổi hành vi thật** — cùng tên/field/projection. NHƯNG khoá `adherence_view` là
>   `(run_id, driver_id, topic)` và UI luôn `run_id=None` ⇒ hai đường **đã tách sẵn**, không
>   trộn số được bằng code. Rủi ro còn lại là **người đọc gộp hai bảng** ⇒ ghi `D-R22`.
>
> **Vòng 3 (cùng ngày) — 3 finding nữa, ĐỀU ĐÚNG, có số:**
> - **L3-04 ĐÚNG — đo được**: `event_adherence` là estimator **LỆCH THEO CẤU TRÚC** ở kênh
>   có HỎI LẠI (tần suất hỏi lại phụ thuộc chính kết cục: người KHÔNG theo bị hỏi lại mỗi
>   tick, người ĐÃ theo thì thôi). Seed 5100 ladder=all: `accept_lift` decision **0,714**
>   (n=63) vs event **0,524** (n=147) ⇒ **lệch −19,0đp**, tỷ lệ hỏi lại **2,33×**; ba kênh
>   không-hỏi-lại lệch đúng **0,0đp** (1,00×). ✅ **ĐÃ GẮN NHÃN** (không "sửa" được vì nó đo
>   thứ khác): `adherence_audit` nay trả `event_repeat_ratio` +
>   `event_adherence_is_lower_bound` — với kênh hỏi lại, `event_adherence` là **chặn DƯỚI**,
>   CẤM so giữa các kênh.
> - **L4-02 ĐÚNG**: không gian topic sản phẩm `{brief, nudge, recap}` ∩ không gian kênh sim
>   `{shift_plan, accept_lift, shift_extend, rest_window, positioning}` = **RỖNG**.
> - **L4-06 ĐÚNG**: `ui/backend/app/adapters/advisor.py` chỉ gọi `bonus_feasibility` (S1) ⇒
>   sản phẩm ship **1/5** kênh của sim.
>
> 🔴 **Kết luận gộp L4-02 + L4-05 + L4-06 — phải nói với hội đồng**: adherence của SẢN PHẨM
> và của SIM **không so sánh được**, ở BA tầng độc lập: (1) đơn vị hành động (cú bấm tự khai
> vs đổi hành vi thật), (2) không gian topic rời rạc hoàn toàn, (3) phạm vi kênh 1/5. Bất kỳ
> câu nào dạng *"adherence hệ thống là X"* gộp hai đường đều SAI. → `D-R22` mở rộng.
>
> Còn lại chưa phản biện: `L5-03/04`, `L1-02`, `L3-02`, `L5-01/02` (sev CAO).

| **L3-03** | 🔴 Ở SẢN PHẨM, `followed` **LUÔN thắng** `dismissed` bất kể tài xế bấm gì sau cùng | `projections.py:43` sort theo `(occurred_at, event_id)`; `advice.py:246` `occurred_at` dựng từ `body.at_min` — **hằng số theo loại card** (`cards.js` `KIND_HOURS`) ⇒ mọi hành động cùng ngày trên cùng card **bằng nhau** về `occurred_at` ⇒ phá thế hoà bằng `event_id` = `ui-{advice_id}-{action}-{giây}` ⇒ `"dismissed" < "followed"` ⇒ `followed` sort SAU ⇒ `decision_state` (`:79` `row["state"] = et`) lấy cái SAU cùng | **sản phẩm không thể ghi nhận tài xế đổi ý** từ "làm theo" sang "bỏ qua" |
| **L4-01** | Sản phẩm ghi `displayed`, sim ghi `decided` ⇒ `event_adherence` ở sản phẩm **vĩnh viễn None** | `advice.py:203` `"event_type": "displayed"`; `projections.py` chỉ đếm `event_decided` khi `et in ("decided","followed")` | một nửa bộ đo im lặng chết ở sản phẩm |
| **L4-03** | Cooldown 20′ nhưng khoá idempotency của `displayed` là bucket **30′** ⇒ có khe advisor **nói miễn phí** | `advice.py:194` `bucket = decision_bucket(float(now_min))` (30′) vs `min_gap_min_per_topic=20` | card tới tay tài xế mà **không có event và không tiêu ngân sách** — họ lỗi F-1 sống lại ở đường sản phẩm |
| **L5-03** + **L5-04** | 🔴 Con số **đã báo** `shift_extend 43/43 = 100%` là **artifact của lỗi**, và **chính test regression của họ lỗi F-1 khắc lỗi đó thành kỳ vọng** | Số đã báo: `research/audit/2026-07-29-cycle-w-review/findings.md:153` ghi *"43/43 = 100% \| Ground truth 100% ✓"*. Test: `tests/test_lifecycle_review_fixes.py:67-70` — `gt_ext` đếm **một** loại event rồi assert **cả** `decided` **và** `followed` bằng nó ⇒ **đồng nhất thức**, adherence = 1,0 luôn, test **không bao giờ đỏ được** | Trong CÙNG một test, `shift_plan` (`:62-65`) và `positioning` (`:73-76`) được pin bằng **hai** đại lượng khác nhau — đúng. Chỉ `shift_extend` bị pin **tautology** |

**L5-04 là finding giá trị nhất của cả lô:** test được viết để chống họ lỗi "mẫu số chỉ chứa người
đã theo" lại **lấy ground truth từ chính event bị hỏng**, cho một kênh khác. Comment ở `:67` gọi
đúng tên lỗi (*"chỉ log KHI đã hoãn ⇒ 100% followed"*) rồi coi nó là hành vi đúng.

---

## 2. ✅ ĐỘ LỚN — đã ĐO, và nó giải quyết cả ba số đá nhau

`scripts/probe_adherence_truth.py` (mới): đo adherence từ **COIN**, tức ground truth **độc lập với
event log**. Mỗi lần `coin_follows` được gọi = một lần advisor NÓI; giá trị trả về = tài xế có nghe
theo. 3 seed (1000–1002), `coverage=all`, `ladder=all`.

| Kênh | advisor NÓI | nghe theo | **adherence THẬT** | event ghi | **báo cáo trong artifact** | |
| --- | --- | --- | --- | --- | --- | --- |
| `shift_plan` | 3464 | 1851 | **0,534** | 3464 | 0,534 | ✅ mẫu số ĐÚNG |
| `accept_lift` | 760 | 330 | **0,434** | 760 | 0,434 | ✅ mẫu số ĐÚNG |
| **`shift_extend`** | **1051** | **327** | **0,311** *(đơn vị LẦN HỎI)* | **97** | **1,000** | 🔴 sai — nhưng xem §2d: đơn vị đúng là **0,473**, thổi **2,1×** |
| `rest_window` | — | — | **không rút coin** | 0 | 1,000 | 🔴 không có khái niệm "không theo" |
| `positioning` | 251 | 125 | **0,498** | — | — | (kênh dùng `standby_*`, probe chưa map — **giới hạn của probe**, không phải lỗi) |

**Phân xử ba số đá nhau:**

| Nguồn | Số | Kết quả |
| --- | --- | --- |
| `L1-03` (agent soi) | 0,26–0,38 | ✅ **ĐÚNG** — 0,311 nằm trong khoảng |
| `L5-03` (agent soi) | ~50% | ❌ **SAI** |
| Tôi trích "danh nghĩa 0,59–0,68" | — | ❌ **SAI, lỗi của tôi**: `DEFAULT_ADHERENCE` thật là **0,30–0,75** theo archetype (P3/P5 = 0,30 · P4 = 0,75). Số 0,59–0,68 là adherence **hiệu dụng đã đo** ở artifact cũ, tôi trích lại thành "danh nghĩa" |

⇒ Con số **đã báo** *"`shift_extend` 43/43 = 100% · Ground truth 100% ✓"* thổi lên **2,1×** (xem §2d) so với
sự thật **31,1%**. Và nhãn *"Ground truth ✓"* của nó là vòng tròn — lấy ground truth từ chính event
bị hỏng (`L5-04`).

### 2b. 🔴 Phát hiện MỚI khi tách dedup vs mất: 28% quyết định của `shift_extend` biến mất

| Kênh | nghe theo | claim lần đầu | claim bị chặn | event ghi | **HỤT** |
| --- | --- | --- | --- | --- | --- |
| `accept_lift` | 330 | 154 | 176 | 760 | — (kênh log VÔ ĐIỀU KIỆN nên không so được) |
| **`shift_extend`** | **327** | **135** | **192** | **97** | **38 = 28% của 135** |

`claim bị chặn` (192) là **đúng** — hỏi lại cùng quyết định trong cùng bucket phải bị chặn (`R-01`).
Nhưng **HỤT = 135 − 97 = 38** là quyết định **đã tiêu token `_claim_effect`, đã tiêu suất ngân sách
nhịp, đã rút coin — rồi bị clamp bất khả thi và biến mất không event, không tác động**. Đây là
`L1-04` với độ lớn đo được: **28% lời khuyên `shift_extend` "được nghe theo" mất hẳn.** Và vì token
đã cháy, mọi lần hỏi lại trong bucket đó cũng trả False ⇒ quyết định không có đường quay lại.

⚠ Cột HỤT **chỉ có nghĩa cho kênh log-khi-đã-theo**. `accept_lift` log vô điều kiện (760 event = mọi
lần hỏi, mang cờ `followed`) nên −606 là so lệch đơn vị, **không phải finding**.

### 2d. 🔴 Vòng soi thứ hai bắt lỗi trong CHÍNH BẢN ĐÍNH CHÍNH của tôi — và nó đúng

Workflow resume (2026-07-30, chạy được tầng L2, 63 finding) trả về hai finding nhắm vào bản sửa của
tôi. **Cả hai đúng.**

**`L5-05` — tôi mắc lại đúng lỗi ĐƠN VỊ mà tôi đang đi sửa.** Con số *"sự thật 0,311 ⇒ sai 3,2×"* trộn
hai đơn vị: 0,311 = 327/1051 là tỷ lệ theo **LẦN HỎI**, còn `decision_adherence` đếm theo **QUYẾT
ĐỊNH**. Cùng đơn vị thì sự thật là **0,473** ⇒ mức thổi là **2,1×**, không phải 3,2×.

| | |
| --- | --- |
| 1,000 / 0,311 *(lần hỏi)* | 3,22× ← **số tôi đã báo, SAI ĐƠN VỊ** |
| 1,000 / 0,473 *(quyết định)* | **2,11× ← đúng** |

Tôi đã sửa ở **8 chỗ** (`findings.md`, spec `d-m3-01`, `projections.py`, `advice_bridge.py`,
test, và 2 chỗ trong tài liệu này). ⚠ **Commit `c46a379` đã đẩy lên `origin/main` với con số 3,2×
trong message** — không sửa được message, nên đính chính nằm ở đây và trong `findings.md`.

Đây là lần thứ **tư** trong cycle này một lỗi đơn vị/định dạng ở tầng ĐO cho ra một con số sai
(28,67 · "LỆCH" oan cho `accept_lift` · 15/15 KHÁC do CRLF · và giờ là 3,2×). **Công cụ đo phải bị
soi như code sản phẩm** — đó là bài học vận hành lớn nhất của cycle.

**`L5-06` — cổng nghiệm thu của tôi là MỘT PHÍA.** `assert ext_adh < 0.99` sẽ **xanh** trên một con số
sai theo chiều THẤP. Và điều đó đã xảy ra thật: bản vá giữa kỳ cho **0,394** trong khi sự thật 0,473
(**−7,9đp**) mà cổng vẫn xanh. *(Nửa còn lại của finding — "bản vá để tử số hụt" — đúng ở thời điểm
agent đọc file, nhưng tôi đã tự bắt và sửa trước khi nó báo, bằng nhánh `infeasible_world_end`.)*

⇒ Đã thêm cổng **HAI PHÍA** `test_shift_extend_adherence_matches_coin_truth`: pin
`decision_adherence` vào ground truth **độc lập** (coin, gộp theo quyết định), tolerance 0,03.

**Và tôi chứng minh cổng đó ĐỎ ĐƯỢC** — theo đúng bài học `L5-04` (cổng không đỏ được thì vô giá trị).
Tạm bỏ nhánh `infeasible_world_end` ⇒ cổng đỏ với thông điệp chỉ đúng chiều:

```
adherence BÁO 0.430 vs COIN 0.515 (lệch -0.085) — thước đo lệch ground truth độc lập.
Chiều DƯƠNG = mẫu số hụt (D-M3-01); chiều ÂM = tử số hụt. 52/101 quyết định theo coin.
```

Phục hồi ⇒ `22 passed`.

### 2e. `L2-01` — cơ chế ĐÚNG của việc `rest_window` bất động (tầng L2, lần đầu được soi)

Tầng L2 (`world.py`) fail hai lần vì session limit; lần này chạy được và cho **cơ chế đúng hơn cả
`L1-02` và cả suy luận của tôi**:

> World **chỉ hỏi** kênh `rest_window` đúng vào lúc lan can số 1 của nó **cấm** hoãn: `GO_SWAP` sinh
> ra **VÌ** pin thấp, mà lan can đầu tiên là *"pin thấp ⇒ không hoãn"* ⇒ **vị từ kích hoạt và lan can
> loại trừ nhau**.

Khớp đúng số đo của tôi: `soc_low` là blocker lớn nhất (**44,1%**). ⇒ Không phải "kênh yếu" cũng không
phải "lan can trùng khít mọi đường" (`L1-02` nói quá) — mà là **một trong ba đường kích hoạt tự loại
trừ với lan can của chính nó**. Hai đường còn lại (`REST`, `GO_CHARGE`) chết ở `window_past`/`no_window`.

### 2f. `L5-07` — cổng hợp lệ bắt buộc của mọi arm A/B **CHƯA TỪNG được thi hành**

> Không một artifact A/B nào ghi adherence: `parallel`/`sim_metrics`/`run_parallel` **không tham chiếu**
> `adherence`·`followed`·`decided` một lần nào.

Nghĩa là luật *"mọi arm phải báo kèm `decision_adherence` per archetype so với danh nghĩa; lệch > 0,02
⇒ TREO kết quả"* là **một luật chỉ tồn tại trong tài liệu**. **CHƯA tôi kiểm** — nhưng nếu đúng thì nó
giải thích vì sao `shift_extend` báo 1,000 suốt 39 artifact mà không cổng nào bắn.

## 2c. (lịch sử) Ba số đá nhau trước khi đo

Về adherence thật của `shift_extend`:

| Nguồn | Số |
| --- | --- |
| `L1-03` | *"tỷ lệ nghe theo thật là 0,26–0,38"* |
| `L5-03` | *"sự thật đo được là ~50%"* |
| Danh nghĩa theo archetype (`DEFAULT_ADHERENCE`) | ~0,59–0,68 |

**Ba số, không cái nào trùng cái nào.** Đây đúng bẫy *"cơ chế đúng, độ lớn sai"* đã sập hai lần
trong repo này (`DET-01` sai 5,7× · chẩn đoán `window_past` sai 5,4×). ⇒ **Không trích số nào trong
ba số này** cho tới khi tôi tự đo. Cơ chế thì đã chắc (§1); độ lớn thì chưa.

## 3. ✅ `L1-02` — ĐÃ CHỨNG MINH: bậc thang `rest_window` **BIT-IDENTICAL** với `s2_only`

Đo bằng **fingerprint PER-ACTOR** (segments + payout + trips + rest_min), **KHÔNG** dùng
`assert_crn` (nó chỉ so danh sách đơn sinh NGOÀI world ⇒ trả True dù actor lệch hết — `D-M3-02`):

| seed | `s2_only` | `rest_window` | |
| --- | --- | --- | --- |
| 1000 | `e5561414ce8e748b` | `e5561414ce8e748b` | **IDENTICAL** |
| 1001 | `6fe71f42eaba8052` | `6fe71f42eaba8052` | **IDENTICAL** |
| 1002 | `06ad64bbe69f46d1` | `06ad64bbe69f46d1` | **IDENTICAL** |

⇒ Trong **mọi artifact A/B**, arm mang nhãn `rest_window` đã đo **chính xác cùng một thế giới** với
`s2_only`. Không phải "kênh yếu" — là **arm bị dán nhãn sai như một can thiệp khác**. Đây là bằng
chứng cứng nhất cho `D-M3-04` (kênh chưa từng chạy), mạnh hơn con số 0/873 lần nói.

⚠ **Nhưng cơ chế mà `L1-02` đưa ra thì chưa đúng.** Nó nói lan can trùng khít vị từ kích hoạt nên
kênh *"KHÔNG THỂ"* bắn. Probe của tôi đo được **253/873 lời gọi ĐI QUA cả ba lan can** rồi mới chết ở
`window_past` (17,8%) / `no_window` (10,3%) / `at_window` (0,9%). Lan can chặn **71,0%**, không phải
100%. ⇒ **Kết cục đúng, cơ chế sai** — đúng bẫy mà chính lăng kính "độ lớn" được dựng ra để bắt.

## 3b. (lịch sử) Nhận định trước khi đo

`L1-02` nói `rest_window` **KHÔNG THỂ** bắn vì lan can trùng khít với vị từ kích hoạt, và bậc thang
`rest_window` **bit-identical** với `s2_only`.

**Kết cục thì khớp đo của tôi** (0/873 lần nói). **Nhưng cơ chế thì không đủ:** probe của tôi đo được
**253/873 lời gọi ĐI QUA được cả ba lan can** rồi mới chết ở `window_past` (17,8%) / `no_window`
(10,3%) / `at_window` (0,9%). Lan can chặn **71,0%**, không phải 100%. ⇒ Claim bit-identical là
**kiểm được và đáng kiểm**, nhưng lời giải thích kèm theo nó chưa đúng.

---

## 4. Chưa phản biện, chưa kiểm (danh sách để không ai tưởng là đã xong)

**Sev CAO, chưa tôi kiểm:** `L1-02` (bit-identical — cần đo) · `L3-02` (multiday: kênh NÓI THẬT và
báo 100% cứng) · `L3-04` (`event_adherence` là estimator **lệch theo cấu trúc** vì tần suất hỏi lại
phụ thuộc kết cục) · `L4-02` (không gian `topic` sản phẩm rời rạc hoàn toàn với không gian kênh sim)
· `L4-04` (sản phẩm không bao giờ ghi `suppressed`) · `L4-05` (`followed` ở sản phẩm là **cú bấm tự
khai**, ở sim là **đổi hành vi thật** — cùng tên, cùng field, cùng projection) · `L4-06` (sản phẩm
chỉ ship 1/5 kênh) · `L4-07` (pha ca sản phẩm dùng hằng `SHIFT_START_MIN = 6*60` cho MỌI tài xế) ·
`L4-08` (`cards.js` đóng băng đồng hồ) · `L4-09` (`topic` default `"bonus"` là namespace mồ côi) ·
`L5-01` (*"decision 68,1% ≈ event 67,6%"* tính trên **một** kênh `accept_lift` ⇒ `D-M3-01` thổi nó
lên **0,00đp**, nhưng nó **stale 2,3đp** so với HEAD) · `L5-02` (claim *"washout đã CHẾT"* phát biểu
cho cả hệ nhưng bằng chứng chỉ phủ 1/5 kênh).

**Sev TB, chưa kiểm:** `L1-04` … `L1-09` (token `_claim_effect` cháy trước clamp khả thi · hai đường
`return None` của `consult` mất dấu · `skipped_advice` không có consumer · `advice.bucket_min` mang
BA nghĩa · một "quyết định" được định danh bằng BA độ rộng bucket 60/30/20′ · tử số `positioning`
hụt ⇒ adherence bị báo THẤP).

**Tầng L2 (`world.py`): 0 finding vì agent fail** — lỗ ở giữa.

---

## 5. Việc tiếp theo, theo thứ tự

1. **Chạy lại workflow (resume)** cho: tầng L2 + 16 agent phản biện + sinh spec. Script phải sửa
   logic `survived` trước khi resume (§0.1).
2. **Tự đo độ lớn** adherence thật của `shift_extend` (§2) và claim bit-identical của `L1-02` (§3).
3. **Sửa `L5-04` trước tiên** — một test tautology còn sống thì mọi fix sau đó không được kiểm chứng.
4. Chỉ khi 1–3 xong mới viết spec `D-M3-01` và implement.

⏳ **PENDING-REVIEW:** V-15 đã đóng (UPDATE-101). Còn mở **V-01…V-14**, **V-18**.
