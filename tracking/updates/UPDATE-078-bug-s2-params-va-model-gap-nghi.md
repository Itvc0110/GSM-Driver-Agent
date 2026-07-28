# UPDATE-078 — BUG-S2-PARAMS: sim dựng bucket 60′ nhưng S2 tính như 30′; và phát hiện sim không đo được giá trị của nghỉ

> ⚠ **CORRECTED 2026-07-28 — BUG-EVAL-ARGMAX (UPDATE-085 §4, Q-11).** Mọi số payout "tài xế
> đích" trong file này đo bằng `pick_target` argmax-A — phép chọn CỰC TRỊ có bias âm hệ thống
> (regression to the mean; sign-flip đã chứng minh: argmax-A −19,7k vs argmax-B +27,4k vs
> không-chọn-lọc +3,6k trên CÙNG can thiệp). **Các số tầng HỆ THỐNG (served/expired/HHI/Gini/
> tổng payout đội) KHÔNG bị ảnh hưởng.** Số thay thế: artifact `24-unbiased-30seed.json` +
> UPDATE-086. Giữ nguyên phần còn lại của file làm lịch sử.


- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** fix (BUG) + research (MODEL GAP)
- **TODO / User story liên quan:** **T-041 bước 1b + 1c**; hồ sơ
  [`10-*`](../../research/audit/2026-07-27-current-state/10-bug-bucket-min-khong-truyen.md) và
  [`11-*`](../../research/audit/2026-07-27-current-state/11-sim-khong-the-cham-diem-loi-khuyen-nghi.md)

## Tóm tắt

`advice_bridge.consult` gọi `shift_dp.solve(spi, policy)` **không truyền `params`** ⇒ solver dùng
`DEFAULT_PARAMS`, trong đó `bucket_min = 30` — trong khi bridge dựng bucket **60 phút**. DP vì thế
tin **pin bền gấp đôi** và **nghỉ bắt buộc chỉ còn ¼**. Đo: **18/25 tài xế đổi lịch**, chiều
`OOO` → `OOR`.

Đo lại 30 seed: Δ payout đi từ −17.310đ xuống −24.960đ. **Nhưng phép so ghép cặp đúng cách cho
thấy hiệu số của chính fix là −7.650đ với CI95 [−24.390, +9.522] — KHÔNG có ý nghĩa thống kê**
(fix giúp ở 12/30 seed). ⇒ **Chưa kết luận được fix giúp hay hại.**

Phát hiện đứng vững, độc lập với điều đó: **trong sim, không nghỉ KHÔNG mất gì** (`fatigue` chỉ
khiến tài xế tự nghỉ, không ảnh hưởng năng suất) ⇒ chỉ tiêu kép **không thể** thưởng cho lời khuyên
nghỉ đúng. Và `p_accept`/`avg_dist_km`/gate thưởng hoá ra **inert hoàn toàn** — bằng chứng độc lập
cho model gap "REST cộng 0.0".

## Chi tiết cập nhật

### 1. BUG-S2-PARAMS — caller không bao giờ được cập nhật

`shift_dp.solve(spi, policy, params=None)` nhận tham số qua `params`. `grep shift_dp.solve` toàn
repo → **đúng một caller** (`advice_bridge.py:222`), và nó **không truyền gì**.

| Tham số | Trước (mặc định) | Sau (số thật của sim) | Hệ quả của cái sai |
|---|---|---|---|
| `bucket_min` | **30** | `self.bucket_min` = **60** | `_soc_cost` 1 thay vì 2 band/bucket; `_required_rest` **¼**; cap cuốc/bucket ½ |
| `avg_dist_km` | 3.0 | **3.5** (`orders.trip_km_median`) | định giá thấp mỗi cuốc ~14% |
| `p_accept` | 0.9 | ước lượng as-of của actor | tài xế tưởng tượng |
| `acceptance_rate` / `completion_rate` | **không truyền** | truyền thật | `_bonus_eligible` trả *"không có số để xét"* ⇒ S2 **hứa thưởng cho cả người chính sách sẽ không trả** |

Nghỉ bắt buộc theo `_required_rest = (B·bucket_min // 240)·rest_min_per_4h`:

| Ca còn lại | `bucket_min=30` (bug) | `bucket_min=60` (đúng) |
|---|---|---|
| 10 giờ | 30 phút | **120 phút** |
| 6 giờ | 0 phút | **60 phút** |

**Vì sao lọt:** AUDIT S2-6 (UPDATE-069) đã **thêm** tham số `bucket_min` và ghi rõ *"producer
sim/l1r dùng 60′"* — nhưng **caller duy nhất không được cập nhật**. Đây là **lần thứ ba trong cùng
một phiên** gặp mẫu này (cước 24.000 → `already_maxed` → `bucket_min`).

Và nó giải thích **vì sao mutation MUT10 sống sót** (UPDATE-074): không test nào phủ
`bucket_min ≠ 30` **vì đường chạy thật cũng chưa bao giờ dùng ≠ 30**.

### 2. Đo lại 30 seed — và vì sao KHÔNG được đọc bảng này thành "fix làm tệ hơn"

CRN, `coverage: all`, kênh mặc định, `crn_ok = True` cả hai lần.

| Chỉ số (P4 đại diện) | TRƯỚC (có bug) | SAU (đã sửa) |
|---|---|---|
| **payout/ngày** | −17.310đ  CI [−29.294, −5.820] | **−24.960đ**  CI [−39.951, −10.334] |
| cuốc hoàn thành | −1,6 | **−3,9** (chỉ **2/30** seed có lợi) |
| **phút rỗi** | +25,9 | **+55,3** |
| served_rate | −0,0047 | −0,0071 |
| đơn hết hạn | +4,8 | +8,9 |

**⚠ Bảng trên KHÔNG chứng minh fix làm tệ hơn.** Đó là hai lần chạy khác code; muốn kết luận phải
so **ghép cặp** trên cùng seed và bootstrap **hiệu của hiệu**:

| | giá trị |
|---|---|
| **hiệu số của fix** | **−7.650,10đ** |
| **CI95** | **[−24.390,08 · +9.521,79]** |
| có ý nghĩa? | **KHÔNG** |
| seed mà fix GIÚP | **12/30** |
| spread theo seed | min **−90.651** · max **+96.237** |

SD của hiệu số ~40k trong khi hiệu ứng ~7,6k ⇒ cần **n ≈ 105 seed**, không phải 30.
`MIN_SEEDS_FOR_SIGNIFICANCE = 30` được hiệu chỉnh cho **A/B advice**, không cho
**variant-vs-variant**.

### 2b. Ablation từng tham số (10 seed, ghép cặp) — `bucket_min` là tham số DUY NHẤT có tác dụng

| biến thể | Δ payout |
|---|---|
| `none_bug` | −19.776đ |
| **`bucket`** | **−11.136đ** |
| `pacc_dist` | −19.776đ (**y hệt** `none_bug`) |
| `rates` | −19.776đ (**y hệt**) |
| `all` | −11.136đ |

`p_accept`, `avg_dist_km`, gate thưởng **inert hoàn toàn** — chúng chỉ scale `online_pay`, mà
`REST`/`SWAP` cộng đúng `0.0` nên **argmax không đổi**. Đây là bằng chứng độc lập, mạnh, cho model
gap trung tâm: **khi nhánh không-chạy không có giá trị thì mọi thay đổi về ĐỘ LỚN thu nhập đều vô
nghĩa** — chỉ ràng buộc (nghỉ/SOC) mới đổi được nghiệm.

### 3. MODEL GAP của SIM: không nghỉ thì không mất gì

`+55,3` phút rỗi khớp với nghỉ bắt buộc tăng 4×. Câu hỏi quyết định: **không nghỉ thì mất gì?**

```
behavior.py:142   fatigue = actor.online_min / actor.fatigue_threshold_min
behavior.py:144   fatigue > 0.35 → có thể nghỉ ăn
behavior.py:149   fatigue > 1.0  → có thể nghỉ ngắn
```

**Hết.** `fatigue` **chỉ khiến tài xế tự nghỉ**; nó KHÔNG tác động tới xác suất nhận, tốc độ, tỷ
lệ huỷ, rating hay rủi ro. ⇒ **nghỉ = mất tiền; không nghỉ = mất KHÔNG GÌ.**

Do đó:

1. **Chỉ tiêu kép ĐA-08 hiện không có tầng nào** đo được lợi ích của nghỉ ⇒ **không thể** thưởng
   cho lời khuyên nghỉ đúng, dù nó đúng đến đâu ngoài đời.
2. ⇒ Số hạng **C2 "giá trị nghỉ"** của spec **bị chặn**: đưa vào solver bây giờ thì solver khuyên
   nghỉ nhiều hơn và thước đo chấm tệ hơn — tối ưu hoá vào cái thước không có vạch cho thứ cần đo.
3. Kết luận này **độc lập** với §2/§2b: nó là sự thật đọc thẳng từ code, không phải suy từ Δ.

### 4. Cái bẫy đã cố ý KHÔNG bước vào

Cách nhanh nhất để Δ đẹp lên là **giảm `rest_min_per_4h`** hoặc bỏ ràng buộc nghỉ. Đó là **che
MODEL GAP** — `CLAUDE.md §4b` cấm thẳng — và về sản phẩm còn tệ hơn: hệ sẽ khuyên chạy 10 tiếng
liên tục **vì thước đo của chính ta không biết tính chi phí của việc đó**.

Tôi cũng **cố ý chưa chạy** `rest_min_per_4h = 0` để đo cận trên phần-do-nghỉ, vì con số đó rất dễ
bị trích dẫn thành *"bằng chứng nên bỏ ràng buộc nghỉ"*.

⇒ Đã chèn **§5b CHẶN** vào `specs/advisor-objective-model-v2.md`: số hạng **C2 "giá trị nghỉ"**
KHÔNG được implement trước khi sim có hậu quả của mệt.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/advice_bridge.py` | sửa | `solver_params()` + `_acc_estimate()`/`_comp_estimate()`; `consult` truyền params; `check_bonus_gate` dùng chung `_acc_estimate` (một nguồn) |
| `tests/test_bridge_passes_solver_params.py` | **tạo** | 3 test mức **caller** (3 đỏ trước khi sửa) |
| `research/.../10-bug-bucket-min-khong-truyen.md` | **tạo** | truy nguyên bug |
| `research/.../11-sim-khong-the-cham-diem-loi-khuyen-nghi.md` | **tạo** | model gap của sim |
| `research/.../11-ablation-params.json` | **tạo** | ablation từng tham số (10 seed) |
| `specs/advisor-objective-model-v2.md` | sửa | **§5b CHẶN** + bước 2b vào thứ tự thực hiện |
| `tracking/TODO.md` | sửa | T-041 bước 1b (DONE) + **1c (CHẶN)** |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| bridge dựng bucket 60′, DP tính 30′ | **OBSERVED-CODE** | `advice_bridge.py:123,187,222` vs `DEFAULT_PARAMS` | cao | — |
| 18/25 tài xế đổi lịch | **OBSERVED-SIM** | cùng `spi`, chỉ đổi `params`, seed 1000 | cao | — |
| payout −24.960đ CI [−39.951, −10.334] | **OBSERVED-SIM** | 30 seed CRN, `coverage: all` | cao (trong sim) | — |
| fatigue không ảnh hưởng năng suất | **OBSERVED-CODE** | grep `fatigue` toàn `src/` → chỉ `behavior.py:142/144/149` | cao | nếu có đường khác thì kết luận §3 yếu đi |
| `avg_dist_km = 3.5` | **OBSERVED-CONFIG** | `orders.trip_km_median` | cao | — |
| `completion_prior = 0.95` | **OBSERVED-CONFIG** | `1 − cancel_after_accept_rate (0,05)` | trung bình | chỉ dùng khi actor chưa nhận cuốc nào |

## Kiểm chứng

| Command / run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| `pytest tests/test_bridge_passes_solver_params.py` | **3 failed → 3 passed** | — |
| `pytest tests/test_bridge_passes_solver_params.py tests/test_advice_bridge.py` | **30 passed** | — |
| baseline 30 seed `coverage: all` sau fix | `crn_ok=True`; bảng §2 | 1 archetype, 1 config, 1 kênh |
| ablation từng tham số | §2b — `bucket_min` là tham số DUY NHẤT có tác dụng | 10 seed ⇒ chỉ HƯỚNG |
| **so ghép cặp 30 seed (trước/sau fix)** | hiệu số **−7.650đ CI [−24.390, +9.522] KHÔNG có ý nghĩa**; fix giúp 12/30 | cần **n≈105** mới kết luận được |
| `pytest tests` (root, full) | **558 passed, 4 skipped** | — |

**Full suite:** **558 passed / 4 skipped** (555 của UPDATE-077 → +3 test caller-params).

**Bổ sung sau khi suite chạy:** `parallel.py` thêm hằng `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100`
+ docstring. **Chỉ là hằng số chưa consumer nào đọc + comment ⇒ không đổi hành vi**; đã chạy lại
`tests/test_parallel_worlds.py` để chắc.

**Ghi chú tính hợp lệ:** `_comp_estimate` được đổi fallback từ `bonus_min_completion` (0,85) sang
`completion_prior` (0,95) **sau khi** ablation và full suite đã khởi động. Thay đổi này **không đổi
hành vi**: `completion_rate` chỉ được đọc ở `_bonus_eligible` (`shift_dp.py:63`) và **cả 0,85 lẫn
0,95 đều qua ngưỡng `>= 0,85`**. Nên hai phép đo vẫn có hiệu lực. (Chỉ khác nếu policy nâng ngưỡng
lên > 0,95.)

## Visual verification

- **Status:** `BLOCKED` → cần Cường xem
- **Vì sao:** đây là thay đổi **lớn nhất về hành vi advisor** trong phiên — lịch khuyên đổi ở
  72% tài xế, và tài xế sẽ thấy nhiều lời khuyên NGHỈ hơn hẳn.
- **Launch:** khu Mô phỏng → tab Hành trình, seed **1000**, so Gantt trước/sau (vạch advice
  `OOO` → `OOR`); và tab Thế giới song song.
- **Cảnh báo phải hiển thị kèm:** khu Mô phỏng đang thiếu **cảnh báo đỏ** cho `shift_plan` mà Cường
  đã yêu cầu — nay càng cần, vì Δ âm đã to hơn. Chưa làm; ghi follow-up.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

0. **⛔ LỖI SUY LUẬN CỦA CHÍNH TÔI — nghiêm trọng nhất trong UPDATE này.** Tôi đã kết luận (và
   **báo cáo cho Cường**) rằng *"sửa bug làm advisor tệ hơn, vì nghỉ bắt buộc tăng 4×"*. Câu
   chuyện khớp hoàn hảo với cả hai sự thật (§1 nghỉ tăng 4×, §3 nghỉ vô ích trong sim) — **và vẫn
   sai**, vì tôi so **hai lần chạy khác code** thay vì **ghép cặp cùng seed + CI của hiệu số**.
   Rồi khi ablation 10 seed cho hướng ngược lại, tôi lại suýt kết luận ngược — cũng vội. Phép đo
   đúng (§2) cho: **CI trùm 0, không kết luận được**.
   **Bài học ghi vào `parallel.py`**: `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100`.
1. **Có phải tôi sửa sai không?** Không: `_required_rest` với `bucket_min=60` cho 120 phút/ca-10h,
   đúng ý nghĩa `rest_min_per_4h = 1 bucket/4h`. Cái sai là bản cũ. Fix vẫn đúng — chỉ là **tác
   động của nó lên payout chưa đo được**.
2. **Phần xấu đi có đến từ gate thưởng không?** Ablation trả lời: **không** — `rates` và
   `pacc_dist` cho kết quả **y hệt** `none_bug`. Chỉ `bucket_min` có tác dụng.
3. **Đã cố ý không đo `rest_min_per_4h = 0`** — nêu ở §4, để tránh tạo ra một con số dễ bị dùng
   sai. Đây là lựa chọn có chủ ý, không phải bỏ sót.
4. **Test ở mức caller, không phải solver** — test solver đã xanh sẵn suốt (nó nhận đúng cái được
   truyền). Cùng bài học của UPDATE-076: **fix ở tầng producer phải có test ở tầng consumer/caller**.
5. **`p_accept` dùng `_acc_estimate` = `accept_base` khi ít mẫu** — `accept_base` là **tham số sinh
   ra hành vi**, nên về lý là oracle nhẹ. Tôi giữ vì code sẵn có đã dùng đúng cách đó với ghi chú
   *"thực tế đọc từ `driver_statistic_daily`"*; nhưng đây là **điểm yếu thật**, ghi vào follow-up
   (nên thay bằng `shrunk_rate` như UI — chính là T-042 việc 3b).
6. **Đã tách xong bằng ablation** (§2b): `bucket_min` là tham số duy nhất có tác dụng; ba tham số
   còn lại inert. Nhưng **không** vì thế mà kết luận được dấu của tác động — xem §0.
7. **Kết luận cũ phải sửa, không được im lặng**: hồ sơ `09` §1 và spec §0 quy toàn bộ −17.310đ cho
   model gap *"REST cộng 0.0"*. Nay biết: **một phần là BUG tham số**, và **thước đo cũng hỏng**.
   Đã ghi đính chính trong `10-*` §7 và `11-*`.

## Expansion checkpoint (T-039)

1. **Schema**: không cần đổi. Nhưng `shift_plan_input` **nên** mang luôn `bucket_min` (hiện nằm ở
   `params`, tách khỏi `spi`) — chính sự tách đó làm caller quên truyền. Đề xuất, chưa làm.
2. **Bài toán tối ưu**: mở ra bài toán chưa ai đặt — **"nghỉ bao nhiêu, khi nào, để tối đa thu
   nhập CÓ tính hậu quả của mệt"**. Không giải được cho tới khi sim có hậu quả của mệt (bước 1c).
3. **Tính năng**: khi sim có fatigue→năng suất, có thể làm card *"nghỉ 30 phút bây giờ đổi lại
   ~X cuốc chất lượng hơn buổi tối"* — loại lời khuyên có căn cứ đo được.

## Follow-up / defer phát sinh

- **T-041 bước 1c (CHẶN)**: thêm hậu quả của mệt vào sim. Không làm được bước 2–3 của spec trước đó.
- **T-042 việc 3b**: thay `_acc_estimate` bằng `shrunk_rate` (bỏ nốt oracle `accept_base`).
- **Cảnh báo đỏ `shift_plan` trong khu Mô phỏng** — Cường đã yêu cầu từ trước, chưa làm, nay cấp
  thiết hơn vì Δ âm to hơn.
- **Ablation 30 seed** (hiện mới 10) cho kết luận có CI.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-12 · V-13 (card "thưởng sắp mất") · V-14 (ĐA-01, có ca
thật `d-37`/`d-2`) · **V-15 MỚI** (UPDATE-078 — lịch khuyên đổi 72%) · Q-03, Q-04 chưa duyệt ·
**ĐA-06 đã CHỐT, không nhắc nữa** · B-02 ARCH-VERSION vẫn mở và chặn T-044 · **chưa commit gì**.
