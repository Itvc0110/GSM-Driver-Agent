# UPDATE-102 — `D-M3-01`: sửa mẫu số adherence 3 tầng · `shift_extend` từ **1,000 → 0,475** (sự thật 0,473)

Ngày: 2026-07-30 · Người điều khiển agent: Cường (duyệt plan: *"chốt"*) · Trạng thái: `DONE-CODE`
Loại: **sửa code sim + projection + test** — behavior-neutral, đã chứng minh bằng fingerprint

Spec: `specs/simulation/d-m3-01-adherence-denominator-fix.md` · Soi:
`tracking/SOI-2026-07-30-mau-so-adherence.md`

---

## 1. Lỗi được sửa

`decision_adherence` tính từ event log. Với **hai kênh** (`shift_extend`, `rest_window`), event chỉ
được ghi **khi tài xế ĐÃ THEO** ⇒ mẫu số chỉ chứa người đã theo ⇒ con số ra **1,0 theo cấu trúc**,
không thể khác. Họ lỗi `BUG-EVAL-ARGMAX`, và là **tái diễn `F-1`** (mẫu số `positioning` từng hụt
đúng như vậy).

Ba tầng cùng chỉ một chỗ, **sửa một tầng là không sửa gì**:

| Tầng | Hiện trạng trước | Sửa |
| --- | --- | --- |
| `advice_bridge` | `rest_window` là kênh **duy nhất** không gọi `coin_follows` | thêm coin, `material_revision = f"defer_to_{giờ}h"` (nội dung ĐỊNH TÍNH) |
| `advice_bridge` + `world` | `shift_extend` `return 0.0` khi coin=False, **không dấu vết** | `note_spoken_outcome()` + `drain_spoken_outcomes()` → world log event mang `followed` |
| `projections` | `_ALWAYS_FOLLOWED = {shift_extend, rest_window}` — *"tồn tại nghĩa là ĐÃ THEO"* | `_ALWAYS_FOLLOWED` **rỗng**; hai kind vào `_FOLLOW_FLAG_KINDS` |

## 2. Files bị ảnh hưởng

| File | Gì |
| --- | --- |
| `src/gsm_sim/advice_bridge.py` | `_spoken_outcome_seen/_out` · `note_spoken_outcome()` · `drain_spoken_outcomes()` · coin cho `rest_window` · 2 call site ở `shift_extend` |
| `src/gsm_sim/world.py` | `_SPOKEN_OUTCOME_KIND` · vòng drain sau cả hai chỗ gọi · `followed=True` cho nhánh đã-theo của cả hai kênh |
| `src/gsm_core/lifecycle/projections.py` | `_ALWAYS_FOLLOWED` → rỗng, +2 kind vào `_FOLLOW_FLAG_KINDS` |
| `tests/test_lifecycle_review_fixes.py` | **sửa test TAUTOLOGY** + cổng chống tái phát |
| `scripts/probe_adherence_truth.py` | probe đo adherence từ COIN + so với projection + fingerprint |

## 3. Kết quả — thước đo nay KHỚP ground truth

Đo bằng `scripts/probe_adherence_truth.py`, 3 seed (1000–1002), `coverage=all`, `ladder=all`.
Ground truth = **COIN** (`coin_follows` trả gì), **độc lập hoàn toàn với event log**. So **cùng đơn
vị** decision-level (gộp bucket 30′ + `material_revision`).

| Kênh | coin: QĐ theo/tổng | **THẬT** | projection | **BÁO** | |
| --- | --- | --- | --- | --- | --- |
| `shift_plan` | 971/1820 | 0,534 | 1851/3464 | 0,534 | OK |
| `positioning` | 124/248 | 0,500 | 121/251 | 0,482 | OK |
| `accept_lift` | 121/214 | 0,565 | 154/265 | 0,581 | OK |
| **`shift_extend`** | **121/256** | **0,473** | **135/284** | **0,475** | **OK** *(trước: **1,000**)* |
| `rest_window` | — | kênh **không nói lần nào** (`D-M3-04`) | — | — | coin đã nối |

⇒ `shift_extend` đi từ **1,000 → 0,475**, lệch **0,002** so với sự thật.

### 3.1 Phát hiện mà spec CHƯA lường: nhánh "đồng ý nhưng bất khả thi"

Sau khi log nhánh không-theo, `shift_extend` mới đạt **0,394** — vẫn hụt **24/121**. Nguyên nhân:
coin=True nhưng lời khuyên **bất khả thi** (kéo ca vượt `time.end_min`) ⇒ clamp về 0 ⇒ **vẫn không
có event**. Đó cũng là một quyết định **ĐƯỢC NGHE THEO** (`applied = 0`), thuộc **cả tử số lẫn mẫu
số**.

⇒ Mở rộng `note_not_followed` → `note_spoken_outcome(followed, reason)`; nhánh đó log với
`followed=True, reason="infeasible_world_end", added_min=0.0`.

**`b0-A` cắt ĐỘ LỚN ở chỗ đó là đúng; nhưng cắt luôn dấu vết ĐO LƯỜNG thì thành một lỗi mẫu số
khác.** Consumer đo độ lớn can thiệp phải dùng `added_min`, **không** dùng số event — đã ghi vào
docstring cả hai nơi.

## 4. Kiểm chứng

### 4.1 Test đỏ TRƯỚC (TDD)

Sửa `tests/test_lifecycle_review_fixes.py:67-70` — bản cũ assert **cả** `decided` **và** `followed`
bằng **CÙNG một biến đếm** ⇒ đồng nhất thức ⇒ adherence = 1,0 luôn ⇒ **test không bao giờ đỏ được**.
Đây là **test regression của họ lỗi `F-1` lại khắc chính lỗi đó thành kỳ vọng** cho kênh khác.

Đỏ đo được trước khi sửa code: **`assert 37 == 0`** — 37 event `advice_shift_extend` được projection
coi là đã-theo, nhưng **0 event nào mang cờ `followed`**.

Sau khi sửa: `21 passed` (file đó), và cổng `ext_adh < 0.99` giữ chỗ chống tái phát.

### 4.2 Behavior-neutral — chứng minh bằng fingerprint PER-ACTOR, **KHÔNG** bằng `assert_crn`

`assert_crn` chỉ so `(order_id, t_min, pickup_cell, gross_vnd)` của đơn, mà đơn sinh **ngoài** world
⇒ trả `True` dù mọi quỹ đạo actor đã lệch (`D-M3-02`). Dùng digest per-actor của
`(segments, payout_vnd, trips_done, rest_min)`:

| | 3 ladder × 5 seed (1000/1001/1002/2000/3160) |
| --- | --- |
| `all` · `rest_window` · `s2_only` | **15/15 IDENTICAL** trước/sau |

Vì sao đúng là phải identical: coin dùng `adherence_coin` (sha256) nên **không tiêu RNG dùng chung**;
`rest_window` nói 0 lần nên coin không được rút lần nào; và event là **output**, không có đường vòng
về hành vi ở sim.

### 4.3 Full suite — **CẢ HAI lệnh** (theo `D-M3-09`)

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest -q` | **794 passed · 5 skipped** (23′30″) |
| `uv run pytest -q ui/backend/tests` | **56 passed** |
| **Tổng** | **850 passed / 5 skipped / 0 failed** |

⚠ **Trung thực về phạm vi run này:** nó khởi động **TRƯỚC** khi tôi thêm
`test_shift_extend_adherence_matches_coin_truth` ⇒ 794, không phải 795. Số thu thập hiện tại là
**800** (799 + 1 test mới). Test mới đã được kiểm **riêng**: file đó `22 passed`, và cổng của nó
**đã được chứng minh ĐỎ ĐƯỢC** (§5.5). Mọi thay đổi **hành vi** đều nằm trong run 794 ở trên; phần
thêm sau chỉ là comment + test mới.

### 4.5 Cổng HAI PHÍA, và chứng minh nó ĐỎ ĐƯỢC

Soi vòng hai (`L5-06`) chỉ ra cổng `assert ext_adh < 0.99` là **MỘT PHÍA** — nó xanh trên một con số
sai theo chiều THẤP. Đúng như vậy: bản vá giữa kỳ cho **0,394** vs sự thật 0,473 (**−7,9đp**) mà cổng
vẫn xanh.

⇒ Thêm `test_shift_extend_adherence_matches_coin_truth`: pin `decision_adherence` vào ground truth
**độc lập** (coin, gộp theo QUYẾT ĐỊNH), tolerance 0,03.

**Chứng minh nó đỏ được** (bài học `L5-04`: cổng không đỏ được thì vô giá trị) — tạm bỏ nhánh
`infeasible_world_end`:

```
adherence BÁO 0.430 vs COIN 0.515 (lệch -0.085) — thước đo lệch ground truth độc lập.
Chiều DƯƠNG = mẫu số hụt (D-M3-01); chiều ÂM = tử số hụt. 52/101 quyết định theo coin.
```

Phục hồi ⇒ `22 passed`.

### 4.4 Bonus: `rest_window` bit-identical với `s2_only` — nay ở **5 seed**

Cả 5 seed IDENTICAL ⇒ trong **mọi** artifact A/B, arm mang nhãn `rest_window` đã đo **chính xác cùng
một thế giới** với `s2_only`. Không phải "kênh yếu" — là **arm bị dán nhãn sai như một can thiệp
khác**. Bằng chứng cứng nhất cho `D-M3-04`.

## 5. Adversarial self-review / flaws found

### 5.1 🔴 BỐN lỗi ĐO của chính tôi (ba tự bắt, một do vòng soi thứ hai bắt)

| # | Lỗi | Nếu tin luôn thì sao |
| --- | --- | --- |
| 1 | Assert đầu tiên đọc `agg["decision_adherence"]` — nhưng `_agg` **cộng dồn mọi trường số**, nên trường đó là **tổng tỷ lệ của ~86 tài xế** (ra **28,67**) | Tôi đã đi tìm một bug "followed > decided" không tồn tại |
| 2 | Probe so **event-level** (coin) với **decision-level** (projection) ⇒ báo "LỆCH" **oan** cho `accept_lift`: 330/760 = 0,434 và 154/265 = 0,581 là **hai số đều đúng**, khác đơn vị | Tôi đã "sửa" một kênh đang đúng |
| 3 | So fingerprint bằng `awk` trên file **CRLF** ⇒ báo **15/15 KHÁC** trong khi hash hiện rõ là giống | Tôi đã báo "nhiễm RNG stream" và đi tìm root cause của một hiện tượng không có |
| 4 | 🔴 **Trộn đơn vị khi báo mức thổi**: *"sự thật 0,311 ⇒ sai 3,2×"* — 0,311 là tỷ lệ theo **LẦN HỎI**, còn `decision_adherence` đếm theo **QUYẾT ĐỊNH**. Cùng đơn vị thì sự thật **0,473** ⇒ **2,1×**. Vòng soi thứ hai (`L5-05`) bắt được | Tôi đã báo mức thổi sai **1,5×**, và **commit `c46a379` đã đẩy lên `origin/main` với con số 3,2× trong message** — đã sửa ở 8 chỗ trong docs/code, message không sửa được |

**Cả BỐN đều là lỗi đơn vị/định dạng ở tầng ĐO**, không phải lỗi ở code sản phẩm — và lỗi thứ tư là chính lỗi mà cycle này đi sửa, mắc lại trong bản đính chính của nó. Đây đúng là họ lỗi
mà cả cycle này tồn tại để diệt — và nó cho thấy công cụ đo cũng phải bị soi như code.

### 5.2 Đã kiểm, không phát hiện vấn đề

- `cadence_note_spoken` vẫn chạy **VÔ ĐIỀU KIỆN** (`R-09` giữ nguyên): advisor NÓI là đã tiêu ngân
  sách chú ý, bất kể tài xế có làm theo.
- `note_spoken_outcome` dedupe theo **ĐÚNG khoá của `coin_follows`** (bucket + `material_revision`)
  ⇒ hỏi lại cùng quyết định không sinh event mỗi tick 2′ (bài học Lỗi #2/`R-08`).
- `decision_id` của nhánh drain tính từ `t_nf` (**lúc NÓI**), không từ lúc drain ⇒ trùng đúng quyết
  định của nhánh đã-theo. Và **không** có hậu tố `-sup`: đây không phải bị nén.
- `_SPOKEN_OUTCOME_KIND` dùng **CÙNG kind** với nhánh đã-theo — tách kind ra là tách mẫu số khỏi tử số.

### 5.3 Chưa làm, và vì sao

- **`L1-04` (bước 4 của spec) CHƯA làm** — dời `_claim_effect` xuống sau clamp khả thi. Đó là thay
  đổi **ĐỔI HÀNH VI THẬT** (token không còn cháy ⇒ một lần hỏi sau trong cùng bucket có thể áp được
  ⇒ liều can thiệp tăng) ⇒ **phải UPDATE riêng + đo n≥100 ghép cặp**. Gộp vào đây là không quy được
  nhân quả cho Δ nào.
- **Tầng L2 (`world.py`) chưa được soi độc lập** (agent fail 2 lần vì session limit) ⇒ có thể còn chỗ
  ghi event tôi không biết. Tôi đã grep `self.log(` quanh vùng advice trước khi sửa, nhưng đó không
  thay được một lượt soi độc lập.
- **13 finding sev CAO + 6 sev TB chưa qua phản biện** — `SOI-2026-07-30` §4. Phần lớn thuộc **đường
  sản phẩm** (`L3-03` thứ tự event, `L4-01` `displayed` vs `decided`, `L4-03` khe nói miễn phí) và là
  cycle riêng.

### 5.4 Seed/kịch bản có thể làm kết luận đảo chiều

Con số **0,473 / 0,475** đo trên **3 seed**. Đủ để kết luận *"mẫu số đã đúng"* (định tính: hai đơn vị
độc lập khớp trong 0,002); **chưa** đủ để chốt 0,47 là hằng số của kênh. Trước khi đưa số này vào
artifact công bố phải chạy ≥30 seed.

## 6. Docs cập nhật kèm

- `research/audit/2026-07-29-cycle-w-review/findings.md:153` — con số `shift_extend 43/43 = 100% ·
  Ground truth 100% ✓` là **artifact của lỗi**; cần gắn nhãn đính chính. **CHƯA LÀM** → §7.
- `tracking/DEFERRED.md` — `D-M3-01` chuyển `DONE-CODE`; `D-M3-02` (fingerprint thay `assert_crn`)
  nay có bản tham chiếu chạy được trong `scripts/probe_adherence_truth.py`.

## 7. Follow-up

| Mã | Việc | Ưu tiên |
| --- | --- | --- |
| `L1-04` | Dời `_claim_effect` sau clamp — **ĐỔI HÀNH VI**, UPDATE riêng, n≥100 | 1 |
| — | Gắn nhãn đính chính vào `findings.md:153` (số 100% là artifact của lỗi) | 1 |
| `D-M3-02` | Đưa `fingerprint_actors` vào `src/gsm_sim/sim_metrics.py`, thay `assert_crn` ở mọi test "bit-identical" | 2 |
| 🔴 **`D-M3-10`** | **Cổng hợp lệ của mọi arm A/B CHƯA TỪNG được thi hành** — `parallel.py`/`sim_metrics.py`/`run_parallel.py` **0 lần** tham chiếu `adherence`; artifact 35–39 **không có khoá `adherence`**. Đây là **lý do trực tiếp** `D-M3-01` sống được qua 39 artifact. Phải nối TRƯỚC mọi phép đo A/B mới | **1 (ngang `L1-04`)** |
| `D-M3-04` | `planned_rest_hour` chưa từng chạy trong A/B — điều kiện tiên quyết của cổng `rest_window` | 3 |
| — | Đo lại adherence ở **30 seed** trước khi công bố số 0,47 | 4 |
| — | Soi độc lập tầng L2 (`world.py`) | 5 |

## 8. Visual status

**`NOT_APPLICABLE`** — thay đổi là **quan sát thuần**, đã chứng minh fingerprint per-actor 15/15
IDENTICAL ⇒ không đổi dynamics, không đổi output số nào của sim, không đổi visual encoding. Cái đổi
là **thước đo adherence**, và nó đổi theo hướng ĐÚNG (khớp ground truth độc lập).
⚠ Khi `L1-04` được làm thì visual gate **CÓ** áp dụng — đó là thay đổi hành vi.

## 10. 🔴 `D-M3-10` — LÀM LUÔN trong cùng cycle, vì nó là NGUYÊN NHÂN GỐC

Sửa `D-M3-01` mà không nối cổng thì lần sau lỗi cùng loại lại sống 39 artifact nữa. Nên tôi làm
luôn, và nó là phần **giá trị lâu dài nhất** của cycle này.

### 10.1 Vấn đề: một cổng chỉ tồn tại trên giấy

Luật đã viết từ lâu: *"mọi arm phải báo kèm `decision_adherence` per archetype so với danh nghĩa;
lệch > 0,02 ⇒ **TREO** kết quả"*. Đo được:

| Kiểm | Kết quả |
| --- | --- |
| `parallel.py` · `sim_metrics.py` · `scripts/run_parallel.py` tham chiếu `adherence`/`followed`/`decided` | **0 lần** |
| Artifact 35–39 có khoá `adherence` | **không có khoá nào** |

⇒ **Đây là lý do trực tiếp `D-M3-01` sống được qua 39 artifact.** Cổng được thiết kế để bắt đúng
loại lỗi đó, nhưng không có một dòng code nào.

### 10.2 Đã nối

| Chỗ | Gì |
| --- | --- |
| `sim_metrics.adherence_audit()` | `decided/followed/adherence` theo **kênh** và theo **(kênh × archetype)** — đọc `projections.adherence_view`, **không** tự cài lại phép đếm (chống lỗi "hai nguồn sự thật" của `D-SIM-09`) |
| `sim_metrics.adherence_flags()` | Cổng **BẤT KHẢ**: adherence đúng 1,0 / 0,0 trên mẫu số ≥20 · `decided=0` · `event_decided=0` trong khi `decided>0` |
| `PairResult.adherence_a/_b` | adherence của **CẢ HAI** arm — bài học `DET-01`: arm đối chứng phải được **đo**, không **giả định** sạch |
| `run_ladder` → `out[step]["adherence"]` | `by_channel` + `flags_per_seed` + **`verdict`** (`"TREO — thước đo hỏng"` / `"OK"`) ⇒ artifact tự mang phán quyết |
| `tests/test_adherence_gate.py` | **9 test** |

### 10.3 Hai loại cổng — và vì sao KHÔNG được gộp

| | Loại | Áp ở đâu | Lý do |
| --- | --- | --- | --- |
| (1) | **BẤT KHẢ** (hard) | **per-seed** | Không phải phép kiểm thống kê. adherence đúng 1,0 trên 101 quyết định là **bất khả với coin ngẫu nhiên** |
| (2) | **THỐNG KÊ** (soft) | **TỔNG nhiều seed** | ⚠ Ngưỡng **0,02 của luật gốc KHÔNG áp per-seed được**: với ~250 quyết định, SE lấy mẫu ≈ **0,03** ⇒ cổng 0,02 mỗi seed **bắn liên tục vì NHIỄU**, và người sửa sẽ **nới ngưỡng thay vì sửa lỗi** — đúng mẫu `D-R20` |

Đã ghi lý do đó **vào code**, không chỉ vào UPDATE — vì người nới ngưỡng trong tương lai sẽ đọc code
chứ không đọc UPDATE này.

### 10.4 Chứng minh cổng ĐỎ ĐƯỢC (bài học `L5-04`)

Tạm hoàn nguyên `_ALWAYS_FOLLOWED` về trạng thái lỗi cũ ⇒ cổng bắn ngay:

```
🔴 shift_extend: decision_adherence = 1,000 trên 101 quyết định — BẤT KHẢ với coin ngẫu nhiên;
   dấu hiệu mẫu số chỉ chứa người ĐÃ THEO (D-M3-01)
```

Và `test_gate_catches_d_m3_01_denominator_bug` dựng lại đúng trạng thái đó trong test, nên nó
**không thể mục lặng lẽ**. Kèm `test_gate_does_not_cry_wolf_on_small_denominator`: mẫu số < 20 thì
1,0 **có thể là may mắn thật** ⇒ không được bắn, nếu không cổng sẽ bị tắt vì nhiễu.

### 10.5 Behavior-neutral + suite

Fingerprint per-actor 3 ladder × 5 seed: **15/15 IDENTICAL** so với trạng thái ngay trước khi thêm
`D-M3-10`. Đúng như phải vậy — `adherence_audit` chỉ **đọc** `result.events`.

Full suite **CẢ HAI lệnh** (`D-M3-09`), sau khi đã có mọi thay đổi của cycle:

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest -q` | **804 passed · 5 skipped** (24′54″) — khớp 809 thu thập |
| `uv run pytest -q ui/backend/tests` | **56 passed** |
| **Tổng** | **860 passed / 5 skipped / 0 failed** |

Suite đi từ 850 → **860**: +1 cổng hai phía (`D-M3-01`) + 9 test cổng adherence (`D-M3-10`).

### 10.6 Điều `D-M3-10` KHÔNG giải quyết

- Cổng **thống kê** (so danh nghĩa, tolerance) **chưa nối** — chỉ có cổng BẤT KHẢ. Cần một quyết định
  về tolerance đúng cho từng cỡ mẫu; nối một ngưỡng sai còn tệ hơn không nối (nó sẽ bị tắt).
- `control_arm_effective_adherence` mà `T-047` §2.7 đòi: `adherence_a` **có** trong `PairResult` nhưng
  arm A tắt advice nên nó rỗng. Trường hợp `DET-01` thật (arm `cadence=off` **có** advice) là arm B
  variant ⇒ đã được `adherence_b` phủ. Ghi ra đây để không ai tưởng `adherence_a` rỗng là bug.
- Artifact **31–39 cũ không có** adherence và **không hồi tố được** — chúng phải giữ nhãn "đo bằng
  thước chưa được kiểm".

## 9. ⏳ NHẮC LẠI PENDING-REVIEW (lệ CLAUDE.md §3.1 — hoãn ≠ waive)

Còn mở: **V-01…V-14** (14 mục visual/data) · **V-18** (nhịp nói advisor, UPDATE-099) · mục ❓ và ⛔
trong `tracking/PENDING-REVIEW.md`. V-15 đã đóng (UPDATE-101).
