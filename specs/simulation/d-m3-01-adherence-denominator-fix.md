# Spec thi công — `D-M3-01`: sửa mẫu số adherence (3 tầng, 5 kênh)

Ngày 2026-07-30 · Trạng thái: **`READY` — chờ duyệt plan trước khi code**
Bằng chứng: `tracking/SOI-2026-07-30-mau-so-adherence.md` · `scripts/probe_adherence_truth.py`

Mọi số là **MOCK** (`configs/pilot_dongda.yaml`), 3 seed (1000–1002), `coverage=all`, `ladder=all`.

---

## §1 Vấn đề

`decision_adherence` được tính từ event log. Với hai kênh (`shift_extend`, `rest_window`) event chỉ
được ghi **khi tài xế ĐÃ THEO** ⇒ mẫu số chỉ chứa người đã theo ⇒ con số tính ra là **1,0 theo cấu
trúc**, không thể khác. Đây là họ lỗi `BUG-EVAL-ARGMAX` và là **tái diễn `F-1`** (mẫu số kênh
`positioning` từng hụt đúng như vậy, đã sửa bằng cách emit `decided` cho mọi người được gán).

**Trong scope:** mẫu số/tử số adherence ở sim (3 tầng) + test tautology + `L1-04` (token cháy trước
clamp khả thi).
**NGOÀI scope, phải làm cycle riêng:** mọi thứ ở đường sản phẩm (`L3-03` thứ tự event, `L4-01`
`displayed` vs `decided`, `L4-03` khe nói miễn phí, `L4-07` `SHIFT_START_MIN` cứng, `L4-09` `topic`
default) — chúng là **UI/contract**, chạm vào cùng lúc sẽ làm không thể quy nhân quả cho Δ nào.

## §2 Sự thật hiện trạng — ĐO ĐƯỢC, không suy luận

| Kênh | rút coin? | event khi KHÔNG theo? | `_ALWAYS_FOLLOWED`? | adherence THẬT | adherence BÁO CÁO |
| --- | --- | --- | --- | --- | --- |
| `shift_plan` | ✅ `:505` | ✅ (`advice_given` mang cờ `followed`) | ❌ | **0,534** | 0,534 ✅ |
| `accept_lift` | ✅ `:577` | ✅ (`advice_bonus_gate` mang cờ) | ❌ | **0,434** | 0,434 ✅ |
| `positioning` | ✅ `:527` | ✅ (mẫu số = `standby_alloc.assigned_ids`) | ❌ | **0,498** | — (đã sửa ở `F-1`) |
| **`shift_extend`** | ✅ `:823` | ❌ **KHÔNG** | ✅ **CÓ** | **0,473** (quyết định) · 0,311 (lần hỏi) | **1,000** 🔴 **sai 2,1×** |
| **`rest_window`** | ❌ **KHÔNG** | ❌ **KHÔNG** | ✅ **CÓ** | **không tồn tại** | **1,000** 🔴 |

Đếm thô (3 seed): `shift_extend` — advisor nói **1051**, nghe theo **327**, event ghi **97**.
`rest_window` — coin **0 lần**, event **0**, và bậc thang của nó **bit-identical** với `s2_only`.

## §3 Con số ĐÃ BÁO bị ảnh hưởng

| Số đã báo | Ở đâu | Sai thế nào | Cần đo lại? |
| --- | --- | --- | --- |
| `shift_extend 43/43 = 100%` · *"Ground truth 100% ✓"* | `research/audit/2026-07-29-cycle-w-review/findings.md:153` | **thổi 2,1×** (thật 0,473 theo đơn vị QUYẾT ĐỊNH — đơn vị của `decision_adherence`); nhãn "Ground truth" là **vòng tròn** — lấy GT từ chính event hỏng | ✅ sửa số + gỡ nhãn GT |
| Arm `rest_window` trong mọi bậc thang A/B | artifact 31–39 | Arm đó **bit-identical với `s2_only`** ⇒ **không phải can thiệp khác**, là arm dán nhãn sai | ✅ gắn nhãn "arm trùng" vào mọi artifact |
| `decision 68,1% ≈ event 67,6%` (bằng chứng *"washout D-A3-01 CHẾT"*) | UPDATE-099, HANDOFF §2 | Agent `L5-01` nói số này tính **chỉ trên `accept_lift`** ⇒ `D-M3-01` thổi nó lên **0,00đp**. **CHƯA tôi kiểm.** Nếu đúng thì số **không sai**, nhưng câu *"washout đã chết"* phát biểu cho **cả hệ** trong khi bằng chứng phủ **1/5 kênh** | ⚠ phải kiểm phạm vi trước khi giữ câu đó |
| Mọi Δ A/B có `shift_extend` bật | artifact 31–39 | Δ **không** sai vì adherence chỉ là thước; nhưng **28% quyết định mất hẳn** (`L1-04`) nghĩa là liều can thiệp thực tế **thấp hơn** liều danh nghĩa | ⚠ Δ vẫn dùng được, nhưng phải ghi rõ liều |

## §4 Thiết kế sửa — và phân loại ĐỔI HÀNH VI vs KHÔNG

> 🔴 **ĐÍNH CHÍNH 2026-07-30 (UPDATE-107, sau khi thi công D và đo n=100 ghép cặp):** dòng D dưới
> đây SAI khi viết. Cả **BỐN** thay đổi là quan sát thuần — **không có thay đổi nào đổi hành vi**.
> Δ đo được ở n=100, cả 11 chỉ tiêu: **0,00 [0,00, 0,00]** tuyệt đối. Lý do đầy đủ ở cuối mục này.

Đây là mục quan trọng nhất: ban đầu tôi phân loại ba trong bốn thay đổi là quan sát thuần và một
đổi HÀNH VI THẬT — **cách phân loại đó dựa trên một sự hiểu sai đã được đo bác bỏ**, xem dưới.

| # | Thay đổi | Đổi hành vi? | Chứng minh bằng gì |
| --- | --- | --- | --- |
| **A** | Tầng 1: thêm `coin_follows` cho `rest_window` | ❌ **KHÔNG** — kênh nói **0/873** lần nên coin không bao giờ được rút; và `adherence_coin` là sha256, **không tiêu RNG dùng chung** ⇒ không dịch dòng | `fingerprint_actors` IDENTICAL, ≥5 seed |
| **B** | Tầng 2: log event khi KHÔNG theo (`followed=False`) cho `rest_window` + `shift_extend` | ❌ **KHÔNG** ở sim — ngân sách nhịp đọc `cadence_note_spoken`, **không** đọc event | `fingerprint_actors` IDENTICAL; nhưng **`n_advice` của `/ab` đổi nghĩa** ⇒ phải ghi vào UPDATE |
| **C** | Tầng 3: bỏ 2 kind khỏi `_ALWAYS_FOLLOWED`, đưa vào `_FOLLOW_FLAG_KINDS` | ❌ **KHÔNG** — projection thuần | test projection đọc `detail["followed"]` |
| **D** | `L1-04`: dời `_claim_effect` xuống **SAU** clamp khả thi trong `check_shift_extend` | ~~✅ CÓ, ĐỔI THẬT~~ → ❌ **KHÔNG** (đo n=100: Δ=0 tuyệt đối) | `fingerprint_actors` IDENTICAL, n=100 ghép cặp, 11 chỉ tiêu |

### ~~Vì sao D đổi hành vi~~ → Vì sao D KHÔNG đổi hành vi, và tôi đã hiểu sai gì

**Lập luận cũ (sai):** *"lời khuyên bất khả thi tiêu token `_claim_effect` rồi bị clamp về 0 ⇒ mọi
lần hỏi lại trong bucket đó trả False ⇒ quyết định mất hẳn (đo: 38/135 = 28%). Sau khi dời, token
không cháy ⇒ một lần hỏi sau trong cùng bucket có thể áp được ⇒ Δ đổi."*

**Root cause thật, chứng minh bằng đọc code + microbenchmark trực tiếp (2026-07-30):**

1. `self.world_end_min` (`advice_bridge.py:165`) là **hằng số đọc từ config một lần lúc khởi
   tạo bridge** — không đổi trong suốt một run.
2. Mọi nhánh `return 0.0` **trước** dòng `actor.shift_extended_min += add` (rate≤0, need_min quá
   lớn, cadence chặn, coin=False, add≤0) **không mutate bất kỳ state nào** của actor.
3. ⇒ Trong **cùng một bucket 30′**, coin cho cùng kết quả (khoá theo bucket), và mọi state ảnh
   hưởng tới `add` (`actor.shift_end_min`, `actor.shift_extended_min`, `need_min`, `world_end_min`)
   **không đổi** giữa các lần gọi liên tiếp ⇒ **`add` là deterministic trong bucket**: nếu lần đầu
   bất khả thi thì **mọi lần sau trong cùng bucket cũng bất khả thi**, bất kể token có cháy hay không.
4. Microbenchmark xác nhận: actor có `shift_end_min = world_end_min` (bất khả thi tuyệt đối), gọi
   `check_shift_extend` **15 lần liên tiếp trong cùng bucket** ⇒ **`add = 0.0` cả 15 lần**, dù token
   (`_effect_applied`) không hề cháy ở code mới. Kết quả quan sát được **giống hệt** code cũ.

**Vậy con số 38/135 nghĩa là gì?** Nó đo **gap LOGGING**: `_claim_effect` trả `True` (claim thành
công) nhưng world.py **cũ** chỉ log event `advice_shift_extend` khi `add > 0` — nên 38 quyết định
bất khả thi có claim mà **không có event**. Đó là thiếu **dấu vết đo lường**, không phải thiếu
**tác động thật** (tác động thật — `add` — đằng nào cũng bằng 0, có claim hay không). Gap logging
đó **đã được đóng bởi chính `D-M3-01`** (nhánh `note_spoken_outcome(..., reason="infeasible_world_end")`
ở §5 bước 2 dưới) — **không phải bởi `L1-04`**. Tôi đã gộp hai cơ chế khác nhau thành một khi viết
motivation ban đầu.

`L1-04` vẫn **đúng về semantic** (`R-01`: "một quyết định = một lần **áp tác động**" — token nên
cháy khi tác động được áp, không phải khi lời khuyên chỉ được *hỏi*) và **giữ lại vì đúng, rẻ, vô
hại** — nhưng nó không sửa một bug quan sát được, và **không cần "UPDATE riêng + n≥100"** như phân
loại ban đầu đòi. Việc đo n=100 vẫn đã làm — và nó chính là thứ **bác bỏ** giả thuyết ban đầu.

Ràng buộc bất di dịch (đã là luật, đừng phá):
- `cadence_note_spoken` chạy **VÔ ĐIỀU KIỆN** — advisor NÓI là đã tiêu ngân sách chú ý, bất kể tài xế
  có làm theo hay không (`R-09`).
- MỘT quyết định = MỘT lần áp tác động (`_claim_effect`), khoá **TRÙNG** khoá `coin_follows` (`R-01`).
- `rest_window` là **DEMAND-TIMING**: trong bảng tiền, chịu cadence **và** chịu coin (chốt 2026-07-30).

## §5 Thứ tự thi công đỏ-trước

### Bước 0 — sửa test TAUTOLOGY trước tiên (bắt buộc)

`tests/test_lifecycle_review_fixes.py:67-70` hiện là:

```python
gt_ext = sum(1 for e in ev if e.kind == "advice_shift_extend")
assert agg["shift_extend"]["decided"] == gt_ext
assert agg["shift_extend"]["followed"] == gt_ext      # ⇒ adherence = 1,0 ĐỒNG NHẤT THỨC
```

Thay bằng **hai đại lượng KHÁC NHAU**, đúng như `shift_plan` (`:62-65`) và `positioning` (`:73-76`)
trong cùng test đã làm:

```python
gt_ext_decided = sum(1 for e in ev if e.kind == "advice_shift_extend")
gt_ext_followed = sum(1 for e in ev if e.kind == "advice_shift_extend"
                      and e.detail.get("followed"))
assert agg["shift_extend"]["decided"] == gt_ext_decided
assert agg["shift_extend"]["followed"] == gt_ext_followed
assert agg["shift_extend"]["decision_adherence"] < 0.99, (
    "adherence 1,0 nghĩa là mẫu số chỉ chứa người đã theo — D-M3-01")
```

**ĐỎ như thế nào trước khi sửa:** dòng cuối đỏ ngay (adherence = 1,0); hai dòng trên vẫn xanh cho tới
khi bước 2 thêm cờ `followed`, lúc đó `gt_ext_followed < gt_ext_decided` và assert bắt được.

⚠ **Không được nới assert cuối thành `<= 1.0`.** Nếu nó đỏ sau khi sửa xong thì mẫu số vẫn hỏng.

### Bước 1 — tầng 1: coin cho `rest_window` (thay đổi A)

Trong `should_defer_rest`, **SAU** `cadence_note_spoken` (giữ đúng thứ tự của `shift_extend`, `R-09`):

```python
self.cadence_note_spoken(actor, "rest_window", now_min)
if not self.coin_follows(actor, "rest_window", now_min, f"defer_to_{target:02d}h"):
    return False, "not_followed"
return True, f"defer_to_{target:02d}h"
```

`material_revision` = `f"defer_to_{target:02d}h"` — **nội dung định tính** (hoãn tới giờ nào), không
phải số nhích từng tick. Đổi giờ đích ⇒ coin mới; cùng giờ đích ⇒ cùng coin.

**KHÔNG thêm `_claim_effect` cho kênh này** — `rest_deferred_min += 2.0` mỗi tick là **hoãn THẬT tích
luỹ**, không phải áp lại một tác động.

Test đỏ trước: `test_rest_window_draws_coin` — set `actor.planned_rest_hour` tới giờ tương lai, ba lan
can đều pass, `bridge.adherence = {archetype: 0.0}` ⇒ phải trả `(False, "not_followed")`;
`= {archetype: 1.0}` ⇒ `(True, "defer_to_..h")`. Thêm `test_rest_window_coin_not_rerolled_in_bucket`:
gọi 10 lần trong cùng bucket 30′ ⇒ 10 kết quả **giống nhau**.

### Bước 2 — tầng 2: log khi KHÔNG theo (thay đổi B)

`world.py`, khối `rest_window`:

```python
if defer or why == "not_followed":
    if defer:
        actor.rest_deferred_min += 2.0
    self.log(actor.actor_id, "advice_rest_window", actor.cell,
             deferred_from=action.value, reason=why, followed=defer,
             deferred_total_min=round(actor.rest_deferred_min, 1),
             decision_id=self._decision_id(actor.actor_id, "rest_window", now),
             channel="rest_window")
    if defer:
        action, target = IdleAction.WAIT, None
```

`check_shift_extend`: đổi `return 0.0` sau coin thành đường có **để lại dấu vết** — trả về một giá trị
mang cờ (hoặc ghi vào một danh sách `drain`-được như `drain_suppressed` đã làm), rồi `world.py` log
`advice_shift_extend` với `followed=False`. **Không** đổi giá trị trả về thành `None` (nhiều consumer
đang so `> 0.0`).

### Bước 3 — tầng 3: projection (thay đổi C)

```python
_ALWAYS_FOLLOWED: set[str] = set()          # rỗng — không kind nào "tồn tại nghĩa là đã theo"
_FOLLOW_FLAG_KINDS = {"advice_given", "advice_bonus_gate",
                      "advice_shift_extend", "advice_rest_window"}
```

Test đỏ trước: dựng event log tay với `advice_shift_extend` mang `followed=False` ⇒ `adherence_view`
phải cho `followed=0, decided=1`. Hôm nay nó cho `followed=1`.

### Bước 4 — `L1-04` (thay đổi D) — **UPDATE RIÊNG, KHÔNG gộp**

Dời `_claim_effect` xuống sau `if add <= 0.0: return 0.0`. Test đỏ trước:
`test_infeasible_extend_does_not_burn_claim` — actor có `shift_end_min` sát `world_end_min`, hỏi lần 1
(bất khả thi ⇒ không có gì xảy ra), rồi nới `world_end_min` và hỏi lại **trong cùng bucket** ⇒ phải áp
được. Hôm nay lần 2 trả 0.0 vì token đã cháy.

## §6 Chứng minh behavior-neutral — KHÔNG dùng `assert_crn`

`assert_crn` (`parallel.py`) **chỉ** so `(order_id, t_min, pickup_cell, gross_vnd)` của đơn, mà đơn
sinh **ngoài** world (`runner.generate_orders`) ⇒ nó trả `True` dù mọi quỹ đạo actor đã lệch. Nó
không phải bằng chứng bit-identical (`D-M3-02`).

Dùng `fingerprint_actors(result)` — đã viết và **đã dùng thật** trong
`scripts/probe_adherence_truth.py`, digest:

```
sha256( [ (actor_id, sorted[(seg_kind, round(t0,3), round(t1,3))],
           round(payout_vnd,6), trips_done, round(rest_min,6)) ... ] )
```

**Cổng cho từng thay đổi:**
- **A + B + C**: `fingerprint_actors` **IDENTICAL** trước/sau, ≥**5 seed**, ở cả `ladder=all` và
  `ladder=rest_window`. Nếu KHÁC ⇒ có nhiễm stream, dừng lại tìm root cause, **không** sửa test.
- **D**: fingerprint **SẼ KHÁC** — đó là đúng. Cổng là Δ`net_mean_all` n≥100 ghép cặp + guardrail 4
  tầng + `others_payout_vnd`, một UPDATE riêng.

⇒ Nên đưa `fingerprint_actors` vào `src/gsm_sim/sim_metrics.py` để test dùng được (`D-M3-02`), thay
`assert_crn` ở mọi test "kênh tắt ⇒ bit-identical".

## §7 Rủi ro của chính spec này

1. **Chỗ tôi có thể sai:** giả định *"ngân sách nhịp không đọc event nên B là quan sát thuần"* — đúng
   ở **sim** (`cadence_note_spoken` nuôi memory trong RAM), nhưng ở **sản phẩm** ngân sách **dựng từ
   event log** (`_cadence_memory` → `_spoken_ids`). Nếu sau này sản phẩm cũng ghi `followed=False`
   thì suất ngân sách đổi. ⇒ Bước 2 **chỉ áp cho sim**; đường sản phẩm là cycle riêng.
2. **Số ở §2/§3 đo trên 3 seed.** Đủ để kết luận định tính (mẫu số hỏng / bit-identical / 0 coin);
   **chưa** đủ để chốt 0,311 là hằng số. Trước khi ghi 0,311 vào artifact công bố phải chạy ≥30 seed.
3. **`L5-01` chưa được tôi kiểm** — nếu *"decision 68,1% ≈ event 67,6%"* thật sự chỉ tính trên
   `accept_lift` thì số không sai nhưng **phạm vi của kết luận** sai. Phải kiểm trước khi giữ câu
   *"washout đã chết"*.
4. **Tầng L2 (`world.py`) chưa được soi độc lập lần nào** (agent fail) ⇒ có thể còn chỗ ghi event mà
   tôi không biết. Bước 2 phải grep lại toàn bộ `self.log(` liên quan advice trước khi sửa.
5. **13 finding sev CAO và 6 finding sev TB chưa qua phản biện** — danh sách ở
   `tracking/SOI-2026-07-30-mau-so-adherence.md` §4. Spec này **không** phủ chúng.
