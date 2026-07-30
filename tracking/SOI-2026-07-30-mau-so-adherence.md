# SOI — mẫu số adherence (`D-M3-01`): 48 finding thô, 7 tự kiểm ĐÚNG, 0 được phản biện

Ngày 2026-07-30 · Trạng thái: **`PARTIAL` — vòng phản biện KHÔNG chạy được**, xem §0.

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
lại bằng cách đọc code" — và tôi làm việc đó cho 7 finding, ghi ở §1.

### 0.2 Tầng L2 (`world.py`) hoàn toàn KHÔNG được soi

`soi:L2-world` fail vì session limit. Đây là tầng quyết định *"event nào được ghi, khi nào"* — tức
đúng tầng chứa nguyên nhân trực tiếp của mẫu số thiếu. **Kết quả soi hiện tại có một lỗ ở giữa.**

---

## 1. ✅ BẢY finding tôi TỰ KIỂM bằng đọc code — đều ĐÚNG

| # | Claim | Bằng chứng tôi tự đọc | Hậu quả |
| --- | --- | --- | --- |
| **L1-01** | `rest_window` là kênh **duy nhất** không rút coin | `advice_bridge.py` `should_defer_rest` không có `coin_follows` ở bất kỳ dòng nào; 4 kênh kia: `:505` `:527` `:577` `:823` | adherence cắm cứng 1,0 |
| **L1-03** | `check_shift_extend` trả `0.0` khi coin=False **không để lại dấu vết** | `advice_bridge.py:823-824` `if not self.coin_follows(...): return 0.0` | mẫu số chỉ gồm người ĐÃ THEO |
| **L3-01** | Sửa tầng 1+2 mà không sửa `_sim_steps` thì **VẪN 100%** | `projections.py` `if kind in _ALWAYS_FOLLOWED or detail.get("followed")` — với 2 kind đó, bước `followed` được thêm **bất kể** `detail["followed"]` | fix một nửa = không fix |
| **L3-03** | 🔴 Ở SẢN PHẨM, `followed` **LUÔN thắng** `dismissed` bất kể tài xế bấm gì sau cùng | `projections.py:43` sort theo `(occurred_at, event_id)`; `advice.py:246` `occurred_at` dựng từ `body.at_min` — **hằng số theo loại card** (`cards.js` `KIND_HOURS`) ⇒ mọi hành động cùng ngày trên cùng card **bằng nhau** về `occurred_at` ⇒ phá thế hoà bằng `event_id` = `ui-{advice_id}-{action}-{giây}` ⇒ `"dismissed" < "followed"` ⇒ `followed` sort SAU ⇒ `decision_state` (`:79` `row["state"] = et`) lấy cái SAU cùng | **sản phẩm không thể ghi nhận tài xế đổi ý** từ "làm theo" sang "bỏ qua" |
| **L4-01** | Sản phẩm ghi `displayed`, sim ghi `decided` ⇒ `event_adherence` ở sản phẩm **vĩnh viễn None** | `advice.py:203` `"event_type": "displayed"`; `projections.py` chỉ đếm `event_decided` khi `et in ("decided","followed")` | một nửa bộ đo im lặng chết ở sản phẩm |
| **L4-03** | Cooldown 20′ nhưng khoá idempotency của `displayed` là bucket **30′** ⇒ có khe advisor **nói miễn phí** | `advice.py:194` `bucket = decision_bucket(float(now_min))` (30′) vs `min_gap_min_per_topic=20` | card tới tay tài xế mà **không có event và không tiêu ngân sách** — họ lỗi F-1 sống lại ở đường sản phẩm |
| **L5-03** + **L5-04** | 🔴 Con số **đã báo** `shift_extend 43/43 = 100%` là **artifact của lỗi**, và **chính test regression của họ lỗi F-1 khắc lỗi đó thành kỳ vọng** | Số đã báo: `research/audit/2026-07-29-cycle-w-review/findings.md:153` ghi *"43/43 = 100% \| Ground truth 100% ✓"*. Test: `tests/test_lifecycle_review_fixes.py:67-70` — `gt_ext` đếm **một** loại event rồi assert **cả** `decided` **và** `followed` bằng nó ⇒ **đồng nhất thức**, adherence = 1,0 luôn, test **không bao giờ đỏ được** | Trong CÙNG một test, `shift_plan` (`:62-65`) và `positioning` (`:73-76`) được pin bằng **hai** đại lượng khác nhau — đúng. Chỉ `shift_extend` bị pin **tautology** |

**L5-04 là finding giá trị nhất của cả lô:** test được viết để chống họ lỗi "mẫu số chỉ chứa người
đã theo" lại **lấy ground truth từ chính event bị hỏng**, cho một kênh khác. Comment ở `:67` gọi
đúng tên lỗi (*"chỉ log KHI đã hoãn ⇒ 100% followed"*) rồi coi nó là hành vi đúng.

---

## 2. ⚠ Độ lớn: agent đưa HAI số ĐÁ NHAU — chưa ai đo

Về adherence thật của `shift_extend`:

| Nguồn | Số |
| --- | --- |
| `L1-03` | *"tỷ lệ nghe theo thật là 0,26–0,38"* |
| `L5-03` | *"sự thật đo được là ~50%"* |
| Danh nghĩa theo archetype (`DEFAULT_ADHERENCE`) | ~0,59–0,68 |

**Ba số, không cái nào trùng cái nào.** Đây đúng bẫy *"cơ chế đúng, độ lớn sai"* đã sập hai lần
trong repo này (`DET-01` sai 5,7× · chẩn đoán `window_past` sai 5,4×). ⇒ **Không trích số nào trong
ba số này** cho tới khi tôi tự đo. Cơ chế thì đã chắc (§1); độ lớn thì chưa.

## 3. ⚠ `L1-02` — cơ chế của nó chỉ giải thích 71%, không phải 100%

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
