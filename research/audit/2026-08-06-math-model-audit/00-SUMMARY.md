# 00-SUMMARY — Audit math-model + vòng phản biện: 5 nợ, verdict, thứ tự sửa

- **Ngày:** 2026-08-06 · **Cho:** Cường (đọc để RA QUYẾT ĐỊNH thứ tự sửa)
- **Nguồn:** `research/audit/2026-08-06-math-model-audit/` (10 artifact `mm-*`, 1 artifact `pb-06`) ·
  `tracking/updates/UPDATE-162`, `UPDATE-163` · `tracking/PLAN-2026-08-06-cycles-chi-tiet.md`
- **Ranh giới giữ nguyên:** sức khoẻ KHÔNG vào objective (spec §1.2b, chỉ cổng một chiều) · số tài chính
  do rule/analytics · không can thiệp dispatch/matching/pricing/đơn cụ thể.

## 0. ⚠ ĐỌC TRƯỚC — trạng thái artifact (ảnh hưởng mức tin của CẢ file này)

| Cái được yêu cầu | Thực tế trên đĩa |
| --- | --- |
| `pb-01 … pb-07` (7 góc soi phản biện) | **CHỈ CÓ `pb-06`** (D-ADV-01). 6 artifact còn lại **KHÔNG TỒN TẠI** |
| `mm-04-rest-family.json` | **KHÔNG TỒN TẠI** — nội dung "họ nghỉ" thực nằm ở **`mm-10-aux-solvers.json`** (S7 `idle_reduction` / kênh `rest_window` / `should_defer_rest`) |
| `mm-07-s2.json` | **KHÔNG TỒN TẠI** — nội dung S2 thực nằm ở **`mm-02-shift-family.json`** (`shift_dp` + `shift_extend` + `sp_end_only`) |

**Hệ quả bắt buộc:** verdict của `pb-01/02/03/04/05/07` dưới đây là **verdict được RELAY bằng chữ**
(trong prompt điều phối), **không có artifact để mở**. Theo đúng luật ADV-09 và
`PLAN-2026-08-06-cycles-chi-tiet.md` §0.7 (*"số nào định trích thì mở artifact gốc"*):

> **CẤM trích bất kỳ SỐ nào được cho là của `pb-01..05/07`.** Chỉ `pb-06` có số đọc được từ file.
> Chỗ nào tôi ghi *"tần suất chưa được trích"* là vì artifact không tồn tại, **không phải** vì refuter
> không đo.

Ngoài ra `mm-03`, `mm-05`, `mm-08`, `mm-09`, `mm-11`, `mm-12` có trên đĩa nhưng phần lớn **chưa qua
phản biện**; UPDATE-162/163 chỉ tiêu thụ `mm-01`, `mm-05`, `mm-11` (+`mm-12` cho D-ADV-03).

---

## 1. Bảng 5 nợ × verdict phản biện

| Mã nợ | Verdict theo từng GÓC SOI | Độ lớn ĐÃ ĐO ĐƯỢC | Cái còn thiếu |
| --- | --- | --- | --- |
| **D-M3-20** — arm đối chứng `rest_window` bị bẩn (RNG-stream) | **CONFIRMED × 2, hai góc soi ĐỒNG Ý.** (a) *Chuỗi gọi có thật xảy ra không* (`should_defer_rest:916` → lambda `world.py:1041` → `consider_relocate` → `rng.random()` `behavior.py:228`; arm A có rút không) = **CONFIRMED**. (b) *Hậu quả đo lường có nghiêm trọng như claim không*, sau khi **cố bác qua 4 đường** (CRN/stream riêng · trùng `D-SIM-K3` · độ lớn tương đối · acceptance định tính) = **CONFIRMED** ⇒ **KHÔNG** phải trường hợp riêng của `D-SIM-K3` | **Chưa có số nào đọc được.** `pb-02` không có artifact. Con số *"adherence P3/P5 ≈ 0,30 ⇒ ~70% lượt bị coin từ chối"* trong UPDATE-162 là **suy luận từ tham số adherence**, KHÔNG phải phép đo trôi-stream | Độ lớn thật của Δ-do-nhiễu-trôi trên bộ số `D-M3-04-FIX` (phải đo lại 30 seed **sau** khi sửa). Chưa biết fix (i) tách-hai-pha hay (ii) keyed-hash rẻ hơn — `pb-01` lẽ ra chốt việc này |
| **D-ADV-02** — `shift_extend` mù `point_window_hours` (kéo ca sau 21h ⇒ `E[Δthưởng] = 0`) | **BẤT ĐỒNG GIỮA HAI GÓC SOI — và bất đồng này KHÔNG phải về sự tồn tại của bug:** (a) *Tần suất / có bao giờ BIND không* = **CONFIRMED** ⇒ bug **có chạy thật**, không phải nhánh chết. (b) *Cách sửa đề xuất có đúng không* = **PLAUSIBLE**: refuter **cố bác** claim "sửa bằng cách gọi `S1 bonus_feasibility._walk` trên `[shift_end, shift_end+extend]`; solver đã xử đúng 0-điểm-ngoài-khung từ UPDATE-065, kênh chỉ chưa gọi" và **không bác nổi, nhưng cũng không chứng minh được** ⇒ hướng sửa **đúng nhưng chưa đủ**. **Lý do bất đồng:** hai câu hỏi khác nhau — "bug có thật/có chạy" (đã xong) vs "gọi S1 là ĐỦ chưa" (chưa xong) | **Chưa được trích.** `pb-03` không có artifact ⇒ **không được nói "X% lượt kéo ca xảy ra sau 21h"**. Bằng chứng cơ chế thì rắn: `advice_bridge.py:1122-1126` (rate = points/online_h) · `policy.py:86-92` (trip_points = 0 ngoài khung) · `configs:254` (`[6..21]`) — 3 nguồn độc lập trùng nhau | **Chỗ chí tử:** `mm-06` issue #4 chứng minh producer in-sim đổ **day-average vào CẢ HAI bucket** (`advice_bridge.py:990-992`) ⇒ **gọi S1 khi input còn sai mẫu số thì chỉ CHUYỂN CHỖ ĐẶT LỖI**. ⇒ Cycle B **phụ thuộc** B0. Thêm: phải chốt **MỘT** nguồn cho `gap` (`next_tier_gap` **hay** S1), nếu không là `D-SIM-09` hai-nguồn-sự-thật |
| **D-M3-21** — sàn bảo lãnh tân binh hấp thụ TRỌN biên của P4 | **PLAUSIBLE** (một góc soi: *tần suất BIND cho P4 + hệ quả suy ra "payout HẰNG ⇒ guard 1b ĐA-08 zero power ⇒ `payout_mean_all` bị kéo về 0 theo cấu trúc"*). Tức: **đồng nhất thức đại số đứng vững, CHUỖI SUY RA thì chưa** | **Chỉ có phần đại số, kiểm lại được bằng tay:** `payout = 0,75·gross + 0,75·(350.000 − gross) = 0,75 × 350.000 = 262.500đ` — **hằng** ⇒ `∂payout/∂gross = 0` (`world.py:575-578`, `configs:487-494`). Điều kiện bind đủ 3 vế: `tenure ≤ 90` (P4 sample ∈ **[5,60)**, `archetypes.py:113-115` ⇒ **mọi P4**) ∧ `online ≥ 6h` (`guarantee_min_online_h: 6.0`) ∧ `gross < 350k`. Nhân đôi: P4 `accept_base 0,80 < 0,85` ⇒ `day_bonus = 0` | **Tần suất bind (%ngày-P4) CHƯA ĐO** — đây đúng là lý do verdict chỉ PLAUSIBLE. Không được nói *"P4 vô hại/vô lợi trong X% ngày"*. Chưa kiểm `day_bonus`/mission có **nằm ngoài** đồng nhất thức không (nếu có ⇒ P4 vẫn có đường hưởng lợi ⇒ phải sửa **cách phát biểu**, không phải sửa metric) |
| **D-ADV-01** — `positioning` (**kênh ĐANG SHIP**) thiếu vế Δ-giá-trị, stagger mù khoảng cách, không `min_gain`, không TTL ⇒ *"đang thắng DƯỚI trần"* | **CONFIRMED** — góc soi *"đây là BUG hay THIẾT KẾ CÓ CHỦ ĐÍCH"*. Refuter **không bác được vế nào**, nhưng **bác được CÁCH GỌI TÊN và ĐỘ LỚN của một vế**: (1) *objective = feasibility* → phải gọi **DESIGN-GAP có chủ đích**, KHÔNG phải bug (docstring `capacity_alloc.py:1-8` tuyên bố thẳng "chống herding"; `world.py:372-381` "S4 chỉ THI HÀNH"); (2) *stagger mù khoảng cách* → **CONFIRMED + ĐO ĐƯỢC**, và mạnh hơn nợ mô tả: trong CÙNG một hàng, mọi ô lệch preferred có cost **bằng nhau TUYỆT ĐỐI** (`capacity_alloc.py:50`) ⇒ **tie EXACT**, dải `pen` chỉ `[0,1]` = 1/10 mức lệch nên **không bao giờ** phá được; (3) *không `min_gain`* → **CONFIRMED, không có nhánh né**, bất đối xứng thật với `advice_bridge.py:729-730` (`station_choice_min_gain_min: 3`); (4) *không TTL* → **HẠ xuống THẤP về độ lớn** (nợ nói QUÁ); (5) *"đang thắng dưới trần"* → **PLAUSIBLE, chưa có bằng chứng bằng ĐỒNG** | **CÓ SỐ THẬT — probe chạy được, đọc từ `pb-06`** (3 seed 1000/1001/1002, `pilot_dongda.yaml`, coverage=all, wait_only, trigger=capacity; instrument bằng wrapper, KHÔNG sửa file repo): · **255/712** ứng viên được gán (457 unassigned vì hết trần) · **143/255 = 56%** lượt gán là **STAGGERED** ⇒ nhánh này là **ĐA SỐ**, không phải nhánh chết · **126/143 = 88%** bị gán tới ô **XA HƠN** ô-còn-trần-gần-nhất; thêm km median **+1,68**, max **+4,36** (trong khi d(own,pref) median chỉ 0,98 ⇒ **~2,7× km rỗng**); ca tệ nhất 3,40 km khi có ô trần cách 0,74 km · **counterfactual km thuần, GIỮ NGUYÊN 255 người gán: 628,9 km thực tế vs 516,0 km ⇒ thừa 112,8 km (+22%), ≈37,6 km/run, MỘT CHIỀU: 41/48 lô thực tế tệ hơn, 0/48 lô counterfactual tệ hơn** · TTL: lag thi hành n=122, median **1,42′**, p90 25,0′, max 62,0′; vượt biên bucket 60′ **chỉ 1/122 = 0,8%** · **248/255** lượt có `λ` ô nguồn > 0 (median 1,79 đơn/giờ) ⇒ vách `int(λ//1,5)` đang hút cạn ô có cầu THẬT | · **Quy đổi km → ĐỒNG chưa có**: 112,8 km là **slack CƠ CHẾ**, KHÔNG phải Δpayout. Muốn nói "thắng dưới trần" bằng tiền thì phải chạy arm có cost-khoảng-cách + paired **n=100** theo ĐA-08 · counterfactual của refuter minimize **km thuần** nên **BỎ ưu tiên SOC** ⇒ là **thước độ lớn, KHÔNG phải đề xuất triển khai** · "xa hơn ô gần nhất" (126/143) là **chỉ dấu**, không phải chứng minh per-move (ô gần có thể đang được người khác dùng đúng chỗ); bằng chứng CHẮC là **tie EXACT trong cost matrix** · số TTL chỉ đúng cho config Đống Đa (grid nhỏ, bucket 60′, wait_only) — **chưa sweep** · **chưa kiểm `coverage=single`** (mặc định file config): 3 seed cho **0 lượt gán, 0 event** ⇒ mọi số trên **chỉ đúng cho arm `coverage=all`** mà ĐA-08 dùng |
| **D-ADV-03** — kênh mới *"positioning chặng về"* (đổi đích deadhead-to-core theo cầu) | **REFUTED** — góc soi *"VÌ SAO NÓ SẼ THẤT BẠI: phản biện đề xuất TRƯỚC khi bỏ công xây"*. Theo `PLAN-2026-08-06-cycles-chi-tiet.md` §0.1 (*"nợ nào bị REFUTED thì cycle của nó bị HUỶ, không sửa cho chắc"*) ⇒ **Cycle D KHÔNG được bắt đầu** | Chưa có số nào. Hai số trong UPDATE-163 (**65,3%** cuốc trả ngoài lõi; **~539 km** rỗng/ngày) là đọc từ **config `:83-90`** + `world.py:799-829`, KHÔNG phải kết quả sim của đề xuất | ⚠ **`pb-07` không có artifact ⇒ tôi KHÔNG biết refuter đã bác bằng CƠ CHẾ NÀO.** Verdict tôi relay được; **lý do thì không**. Đây là một **ĐỀ XUẤT** (chưa tốn code) nên đóng nó là rẻ — nhưng đóng **vĩnh viễn mà không ghi lý do** thì 3 tháng sau sẽ có người đào lại đúng ý tưởng này. ⇒ xem §2 |

---

## 2. Ba giỏ: sửa ngay / phải đo thêm / bị bác

### 2a. ĐỦ CHÍN ĐỂ SỬA NGAY (CONFIRMED + root cause chứng minh + acceptance đo được)

| Nợ | Vì sao đủ chín |
| --- | --- |
| **D-M3-20** (arm đối chứng `rest_window`) | Hai góc soi **CONFIRMED và đồng ý**; chuỗi gọi đọc thẳng file:line; đã loại được giả thuyết "chỉ là `D-SIM-K3`"; acceptance là **bất biến nhị phân đo được ngay** (fingerprint IDENTICAL khi mọi coin từ chối) ⇒ test đỏ-trước viết được không cần bàn thêm. Đây là **THƯỚC**, không phải giá trị |
| **D-ADV-04** (mẫu số bucket của S1 — **KHÔNG nằm trong 5 nợ nhưng chín NHẤT**) | **Đã REPRODUCE có output thật** (`repro-s1-denominator.py`, chạy đúng đường production `derive_bonus_gap_input → solve`): producer trả `{peak: 6.0, offpeak: 6.0}` thay vì `{30, 7.5}` ⇒ S1 phán **INFEASIBLE** *"chỉ kiếm thêm ~42đ < 50đ"* trong khi rate đúng cho **FEASIBLE tại 2,42h**. Ai đúng ai sai đã phân xử: **solver ĐÚNG, producer SAI** — ngữ nghĩa consumer bị **test ghim** `tests/test_bonus_feasibility.py:113-119`. **Khảo sát ADV-09 đã làm xong** (plan §B0): L1 và UI **không có test ghim** ⇒ bug thuần; sim có `test_multiday.py:172-173` nhưng ý định test là *kiểm nối memory*, không chốt ngữ nghĩa. **S1 là solver DUY NHẤT đường sản phẩm chạy** (B6-PARITY) ⇒ lỗi đập thẳng vào card tài xế thật, và làm advisor **bi quan có hệ thống** |
| **D-ADV-01 — CHỈ vế (2) stagger mù khoảng cách** | Vế duy nhất **CONFIRMED + đã đo độ lớn một chiều** (56% lượt gán, +22% km, 41/48 lô, 0/48 ngược chiều) **và KHÔNG có test bảo vệ** (`pb-06`: không tìm thấy test nào ghim "stagger chọn đích theo alphabet"). ⚠ Nhưng nó nằm trên **kênh ĐANG BẬT** ⇒ **regate n=100 ĐA-08 đủ 9 dòng** là điều kiện, không phải tuỳ chọn ⇒ tôi xếp nó **SAU** hai cái trên (xem §4) |

### 2b. PHẢI ĐO THÊM TRƯỚC KHI SỬA

| Nợ | Phải đo cái gì (rẻ nhất trước) |
| --- | --- |
| **D-M3-21** | **%ngày-P4 có `newbie_guarantee_topup > 0`** trên **artifact `positioning` n=100 ĐÃ CÓ** (không cần chạy sim mới nếu event log còn trường). Đây là phép đếm, ~30′, **không đổi một dòng hành vi** ⇒ rẻ nhất trong cả danh sách và nó **đổi cách đọc `+6.016đ` đã báo cho Cường**. Kèm câu hỏi phân xử: `Δgross(P4) > 0` SIG hay không? |
| **D-ADV-02** | (a) **tần suất** — bao nhiêu % lượt `shift_extend` có cửa sổ kéo rơi (một phần / hoàn toàn) sau 21h. `pb-03` bảo CONFIRMED nhưng **không có artifact ⇒ số phải đo lại**. Nếu ~0 ⇒ **hạ severity, chỉ ghi comment cảnh báo**, không sửa (plan §Cycle B đã ghi luật này); (b) **B0 phải xong trước** — nếu không thì chỉ chuyển chỗ đặt lỗi |
| **D-ADV-01 — vế (1) "objective thiếu Δ-giá-trị" và vế (5) "đang thắng dưới trần"** | Vế (1) là **DESIGN-GAP có chủ đích** ⇒ mở rộng cost matrix là **ĐỀ XUẤT**, cần plan + duyệt Cường, **không phải sửa bug**. Vế (5) **PLAUSIBLE, cấm trích như số đã đo** — muốn nói bằng tiền thì phải quy đổi km→đồng và chạy arm cost-khoảng-cách n=100 |
| **D-ADV-01 — vế (4) không TTL** | **HẠ xuống THẤP** theo `pb-06` (1/122 = 0,8% vượt biên bucket). **Giữ mở** vì đúng lớp lỗi *"hành động trên ảnh cũ"*, nhưng **không** đáng một cycle riêng bây giờ; chưa sweep coverage thấp / bucket ngắn / travel dài, và chưa tách 5 plan không-follow thành *"hoàn thành im lặng"* vs *"reservation ma"* |

### 2c. BỊ BÁC — một dòng để không ai đào lại

- **`D-ADV-03` "positioning chặng về"** — **REFUTED** ở góc soi *"vì sao nó sẽ thất bại"* ⇒ theo plan §0.1,
  **Cycle D HUỶ, không code, không prereg.** ⚠ **Điều kiện duy nhất để đóng vĩnh viễn:** phải viết
  `pb-07` (hoặc một dòng trong `DEFERRED.md`) **ghi CƠ CHẾ đã bác** — hiện artifact không tồn tại nên
  lý do **chưa ai ghi được**. Ứng viên đã ghi sẵn trong `PLAN` §Cycle D (rủi ro a–d: km rỗng tăng · ô
  `capacity_left>0` có thể là ô λ-thấp do `⌊λ/1.5⌋` · herding · đơn chết phần lớn NGOÀI lõi) —
  **nhưng tôi KHÔNG được nói cái nào là cái refuter dùng.**
- **`D-ADV-01` gọi là "BUG"** — **bị bác cách gọi tên.** Nó là **DESIGN-GAP có chủ đích**
  (`capacity_alloc.py:1-8` + `world.py:372-381` tuyên bố thẳng "chống herding", "S4 chỉ THI HÀNH").
  Đừng ai viết "bug positioning" nữa.
- **`D-ADV-01` vế "không TTL" ở mức CAO** — **bị bác về ĐỘ LỚN** (0,8%). Nợ **nói QUÁ**.
- **Giả thuyết *"pref = own cell làm lọc khoảng cách vô dụng"*** — **bị bác bằng code**:
  `market_state.py:99-103` chỉ đưa ô `capacity_left>0` vào `ranked`, nên ô đang đứng của ứng viên
  **không bao giờ** là preferred ở `trigger=capacity`.
- **Sửa cost lệch-target thành `LARGE` (cấm stagger)** — **đã bị chặn trước**: sẽ **ĐẬP**
  `test_t14_zone_veto_dong_ca_stagger` và `test_t15_...`. Sửa **phải là THÊM vế khoảng cách/Δ-giá-trị,
  giữ mismatch hữu hạn**, và **không lật** `test_low_soc_swap_priority` / `test_herding_avoided_count`
  (dải `pen` chỉ 1,0 ⇒ trọng số km phải cùng thang tiền/phút hoặc nhỏ hơn ngưỡng).
- **`D-M3-20` = trường hợp riêng của `D-SIM-K3`** — **bị bác** (`pb-02`, một trong 4 đường cố bác)
  ⇒ Cycle A **không gộp** vào Cycle E.

---

## 3. Finding MỚI từ "mm-04 / mm-07" — chỉ severity CAO/TB · **TẤT CẢ CHƯA QUA PHẢN BIỆN**

> ⚠ `mm-04-rest-family.json` và `mm-07-s2.json` **không tồn tại**. Nội dung tương ứng nằm ở
> **`mm-10-aux-solvers.json`** (họ nghỉ: S7 `idle_reduction` + kênh `rest_window` + `should_defer_rest`)
> và **`mm-02-shift-family.json`** (S2 `shift_dp` + `shift_extend` + `sp_end_only`).
> **Cả hai artifact CHƯA qua vòng phản biện nào** (workflow phản biện chỉ sinh được `pb-06`).
> UPDATE-162 §Kiểm chứng nói rõ: `mm-02/03/06/08/09/10/12` **chưa kiểm ⇒ chưa được trích**.
> ⇒ Danh sách dưới đây là **hàng đợi phản biện**, KHÔNG phải kết luận, và **KHÔNG được đưa vào cycle nào**
> trước khi có refuter.

### 3a. Từ `mm-02` (thay `mm-07` — họ S2 / `shift_extend`)

| # | Finding | Sev | Bằng chứng | Vì sao đáng phản biện trước |
| --- | --- | --- | --- | --- |
| S2-a | **`sp_end_only` CHẾT CẤU TRÚC**: trong world zero-cost, `END` **không bao giờ** thắng trong DP ⇒ bật kênh E4/E-05 lên là **im lặng 100%**, và người đo ablation sẽ đọc nhầm thành *"không có ca nào đáng kết sớm"* | **CAO** | `shift_dp.py:250-254` (`END` chỉ khi **strictly >** `best_v`) + `:245-249` (`REST` luôn khả thi, reward 0) + `:185-189`; `configs:281-282` (`cash=0`, `swap_fee=0`). **Probe của agent: 0/252 case** (B∈{4,12,24} × 7 profile demand kể cả demand=0 × 4 mức điểm × 3 SOC) có `END` trong schedule | Đây là **claim có probe** ⇒ dễ phản biện dứt điểm. Nếu đúng, nó **đổi cách đọc một ablation** (đúng lớp lỗi *"cờ config nói SAI hành vi"* UPDATE-117), và fix rẻ (guard + regression test), **0 đổi hành vi** |
| S2-b | **Lượng tử hoá band-5 VẪN lỗi sau ADV-01**: floor kép `round(exp_trips·pph) // 5` ⇒ với `exp_trips < 0,9` (toàn bộ giờ vắng) **0 band/bucket** ⇒ points band **đóng băng** suốt DP, Bellman **mù mốc thưởng** 60/100/160/200; cộng `pts0` floor tới −4 điểm | **CAO** | `shift_dp.py:204-207` + `:176`. Probe agent: demand/bucket 0,5–0,88 ⇒ `add_pts ∈ {2..4}` ⇒ 0 band/bucket | Claim của fix ADV-01 (*"band 5 khớp point_normal=5 ⇒ mỗi cuốc tiến ≥1 band"*) chỉ đúng **PER-CUỐC**, còn DP chuyển state theo **KỲ VỌNG** — nếu đúng thì đây là **ADV-01 chưa sửa xong**, và là **điều kiện cần** trước bất kỳ lần bật lại `shift_plan` theo điều kiện reopen ĐA-07 |
| S2-c | **Cầu khả dụng cá nhân = TỔNG top-3 cell belief** (không vị trí, không chia cạnh tranh) ⇒ phóng đại tới **3×** ở giờ vắng ⇒ thổi `E[payout]`/`delta` của S2 | TB | `advice_bridge.py:504-509` + `shift_dp.py:147-152` (`grouped[b] += expected_orders` cộng cả 3 cell; cap 1,2 cuốc chỉ cắt khi tổng > cap) | Giải thích **một phần** vì sao ĐA-07 đo `shift_plan` không tạo giá trị dù DP "dự đoán" delta > 0 ⇒ chạm **khoảng cách dự-đoán-vs-đo**, không chỉ chạm giá trị |
| S2-d | **Clamp `world_end` CỤT**: nhánh `0 < add < need_extra` **vẫn ÁP kéo ca** dù mốc đã bất khả thi trong `add` được cấp ⇒ **kéo ca chắc-chắn-không-thưởng**, và A/B đọc event như can thiệp đầy đủ | TB | `advice_bridge.py:1191-1221` — `:1197` clamp; chỉ nhánh `add ≤ 0` trả `infeasible_world_end` (`:1198-1206`); `cap_unreachable` (`:1148`) kiểm **trần extend** nhưng **không** kiểm trần `world_end` ⇒ **ràng buộc bind một cửa, lọt cửa kia** | Cùng họ D-ADV-02, sửa **cực rẻ** (so hai số đã có trong hàm, thêm reason `world_end_unreachable`, giữ mẫu số adherence D-M3-01). Ghi chú của agent: *b0-A từng đo 9/49 lần hoãn rơi vùng `world_end`* ⇒ vùng này **không hiếm** (số này **chưa phản biện**) |
| S2-e | **Certainty-equivalence trên terminal STEP function**: `bonus_at(round(E[points]))` thay vì `E[bonus(points)]` ⇒ Jensen gap **hai chiều** quanh mốc; ngay TRÊN mốc, `E[payout]` báo cáo phồng đúng `tier_vnd × (1−P)` | TB | `shift_dp.py:186-188, 252, 283`; `advice_bridge.py:1126` (`need_min` deterministic, buffer **×1,15 tuỳ tiện không neo thống kê**) | Đây là **gốc toán chung** của D-ADV-02 (không phương sai) **và** của `mm-06` issue #2 (S1 verdict nhị phân trên median) ⇒ nếu phản biện xong, một quyết định thiết kế (`P(đạt mốc)` bằng Poisson tail) đóng **nhiều nợ cùng lúc** |

### 3b. Từ `mm-10` (thay `mm-04` — họ nghỉ)

| # | Finding | Sev | Bằng chứng | Ghi chú phản biện |
| --- | --- | --- | --- | --- |
| R-a | **S3 `bonus_progress_gap` hứa "chốt được mốc" mà KHÔNG kiểm eligibility** mà world thật dùng để zero-out bonus ⇒ tài xế **đã tự loại mình khỏi thưởng** vẫn nhận **lời hứa sai**, đúng lúc họ cần SỰ THẬT nhất | **CAO** | `f3_patterns.py:94-108` (không đọc `dse['acceptance_rate']/['completion_rate']` **dù đã có ở dòng 40-41**); `src/gsm_sim/policy.py:94-97` (`day_bonus` = **0** nếu acceptance<0.85 **HOẶC** completion<0.85, **bất kể points**). `test_f3_patterns.py` **không có** case "gap nhỏ NHƯNG acceptance<0.85" | Đúng khuôn `station_choice` (thiếu vế world định giá). Fix nhỏ + 1 regression đỏ-trước. ⚠ Nhưng xem R-d: **S3 hiện mồ côi** ⇒ chưa hại ai thật |
| R-b | **`session_summary` là deriver L3 DUY NHẤT trong `features/` KHÔNG nhận `t_now`** — cắt theo NGÀY tuyệt đối, **không có tự vệ chống đọc-tương-lai**, và **bị LOẠI khỏi cổng thường trực D-M3-12** | **CAO** | `from_l1r.py:179-213` (chữ ký thiếu `t_now`, khác **MỌI** `derive_*_input_l1r` khác: S5/S6/S7/S8/S9 đều có); `session_summary.py:14-49`; `tests/test_future_leak_gate.py:82-92` (`_cases()` liệt 7 deriver, **không có** `session_summary`); `test_future_leak_l1r.py` cũng không | An toàn hiện **phụ thuộc hoàn toàn kỷ luật caller**, mà `router.py:29-30` khai `session_review` khớp free-text **giữa ca** (*"thu nhap hom nay"*). ⇒ **cổng dựng ra để bắt lớp lỗi này lại bỏ sót đúng file này**. Fix thuần phòng thủ, không đổi hành vi hiện tại |
| R-c | **S7 (đường L1R/production) `demand_by_hour` bị SUPPLY-CENSOR**: đếm `trips` (**chỉ đơn ĐÃ phục vụ**) làm proxy cho cầu ⇒ **giờ thiếu tài xế trông y hệt giờ ít khách** ⇒ có thể khuyên nghỉ **đúng giờ thị trường đói cung nhất**; vòng lặp tự khoá: càng ít người ở lại → càng ít trip → proxy càng thấp | **CAO** | `from_l1r.py:376-386`; `idle_reduction.py:12` (docstring tự nhận *"Demand là PROXY"*) | **Nợ CŨ S7-2, CONFIRMED từ audit 2026-07-26, VẪN CÒN NGUYÊN** ⇒ không phải finding mới, nhưng là finding **chưa ai sửa**. Agent đã tự kiểm để không đổ oan: **đường SIM dùng ORACLE `demand_field`** (`world.py:1142-1168`) nên **KHÔNG mắc** ⇒ bug bị giới hạn ở đường L1R, **chưa có hại thật đo được**, nhưng nổ ngay khi ai nối dây |
| R-d | **Solver MỒ CÔI**: `f3_patterns` (S3) và `anomaly_alert` (S9) **không có caller sống nào** ngoài test/fixture viết tay; `idle_reduction` (S7) chỉ có **đúng MỘT** caller sống — **bên trong simulator**, kênh `rest_window` **mặc định TẮT**. **Không solver nào trong ba cái nối tới UI backend thật** | TB | `ui/backend/app/adapters/advisor.py:1-19` (import **DUY NHẤT** `bonus_feasibility`); `routers/advice.py:343` khai `_REAL_ADVICE_ID_PREFIXES` gồm **`'s7-'`** nhưng **không route/adapter nào sinh advice_id đó**; `scripts/smoke_advisor_live.py:58-65` (`_s3()` **viết tay**, không gọi `f3_patterns.solve()`); grep `f3_patterns.solve(` / `anomaly_alert.solve(` ngoài `tests/`: **0** | ⚠ **Đây là finding QUAN TRỌNG NHẤT của mm-10 cho việc XẾP ƯU TIÊN**: `router.py:18,20-21` là **bản đồ Ý ĐỊNH, không phải bản đồ THI HÀNH** ⇒ R-a/R-b/R-c hiện **KHÔNG gây hại thật cho ai** ⇒ **không cái nào được chen lên trước D-ADV-04** (bug trên đường sản phẩm THẬT). Cũng là ngữ cảnh của **B6-PARITY** (UI chạy 1/9 solver) |
| R-e | **`rest_window` (S7, OFF) × `positioning` (S4, ON) có thể kéo CÙNG một actor theo HAI hướng ở hai tick liền kề** — không có cơ chế chia sẻ trạng thái ⇒ hai lần ENROUTE + SOC thật cho hai đích khác nhau, không actor action nào lợi thêm | TB | `world.py:990-1012` (positioning chỉ ghi đè khi `action==WAIT`, **không chạm khi `REST`** ⇒ `standby_plan` ở lại **treo**); `world.py:1033-1038` (`should_defer_rest` dùng `alt=consider_relocate` — **bản năng CỤC BỘ ring 1-3**, KHÔNG đọc `self.standby_plan`); `behavior.py:175-220` | Lỗi **"ngủ"** (kênh OFF) ⇒ **sửa phòng ngừa, không phải sửa hại đã đo**. Fix rẻ nhất: truyền `self.standby_plan.get(actor.actor_id)` vào `should_defer_rest`, **0 solver mới**. ⚠ **Nằm đúng trên hàm mà Cycle A sẽ mổ** (`should_defer_rest`) ⇒ **cân nhắc gộp vào Cycle A** để không mổ hai lần cùng một hàm |
| R-f | **S9 `confidence` hiển thị cho tài xế dạng `%` như xác suất đã hiệu chỉnh, nhưng KHÔNG có nguồn calibration/closed-loop nào trong repo**; trong mock nó là `rng.uniform(0.3,0.8)` thuần; **false-positive rate KHÔNG đo được ở bất kỳ đâu** | TB | `anomaly_alert.py:96,119-120` (in `.0%`); `mockgen/realdata.py:477-482` (`round(rng.uniform(0.3,0.8),2)`, `status:'open'` **luôn luôn**) | Chạm **ranh giới sản phẩm CLAUDE.md §5** (*không hứa chắc; mock phải gắn nhãn*). Không có field nào trong **13 bảng** ghi kết quả giải trình ⇒ **GAP DỮ LIỆU thật**, không phải lỗi solver. Fix = **đổi CÁCH NÓI**, không đổi model |
| R-g | **Hai nợ CŨ chưa sửa, xác nhận lại trên code 2026-08-06** | TB | (i) `f3_patterns.py:21-27` `_dur_min` bỏ phần NGÀY của timestamp ⇒ hoạt động **vắt qua nửa đêm** cho duration **ÂM** ⇒ sai severity `charge_rest_peak`; P7 *"ca TỐI-ĐÊM 15-16h → 23-24h"* (`configs:242`) là ca có thật vắt gần nửa đêm (nợ **S3-1**). (ii) `anomaly_alert.py:37-45` `_hours_since` **chỉ bắt `ValueError`** ⇒ lệch aware/naive giữa `t_now` và `detected_at` ném **`TypeError` không bị bắt** ⇒ `solve()` **CRASH toàn bộ** thay vì degrade (nợ **S8S9-2**) | Không phải finding mới; ghi để không ai tưởng đã sửa. (ii) sẽ nổ **ngay** khi có input thật trộn tz — rất thường gặp khi trộn CSV/DB |

---

## 4. Thứ tự cycle đề xuất

**Nguyên tắc xếp (từ plan §0.2, giữ nguyên):** nợ chạm **ĐỘ TIN của phép đo** → nợ chạm **GIÁ TRỊ** →
**tính năng mới**. Lý do: *sửa giá trị trên thước bẩn thì không đọc được kết quả.* Thêm một nguyên tắc
từ `mm-10` R-d: **nợ trên đường SẢN PHẨM THẬT xếp trước nợ trên solver mồ côi.**

### CYCLE 1 — `D-M3-20`: làm SẠCH arm đối chứng của `rest_window` (= Cycle A của plan)

- **Mục tiêu:** mọi quyết định **bị cadence nén hoặc coin từ chối** phải **bit-identical** với arm A.
- **Root cause đã chứng minh?** **CÓ, và đã qua 2 góc soi phản biện, cả hai CONFIRMED.**
  `advice_bridge.py:916` gọi `alt_action_fn` **trước** cadence `:922` và coin `:933` → `world.py:1041`
  truyền `consider_relocate(..., self.rng, ...)` → `behavior.py:228` rút `rng.random()`. Arm A: cổng cờ
  `:843` ⇒ return `no_window` ở `:907` **trước** dòng 916 ⇒ **0 draw**. Nhánh cam kết `:898` cũng rút
  **mỗi tick**.
- **Test đỏ-trước:** (1) kênh **BẬT** + monkeypatch `coin_follows → False` ⇒ `fingerprint_actors` phải
  **IDENTICAL** arm A — **phải ĐỎ trên code hiện tại**; (2) cadence nén (`min_gap` lớn) ⇒ cũng **IDENTICAL**.
- **Acceptance (SỐ):** 1. hai test trên **XANH**. 2. kênh **TẮT** ⇒ fingerprint IDENTICAL arm A trên
  **5 seed** (bất biến cũ **không được vỡ**). 3. **đo lại** acceptance `D-M3-04-FIX` trên **30 seed**
  **cùng cửa sổ seed cũ**, báo **CẢ HAI** bộ số trước/sau; nếu kết luận đổi ⇒ banner **CORRECTED** lên
  UPDATE tương ứng. 4. **cả hai** suite xanh như baseline (`uv run pytest -q` **và**
  `uv run pytest -q ui/backend/tests` — 809 + 56).
- **Rủi ro làm đảo kết luận:** (a) fix tách-hai-pha **đổi thứ tự draw ⇒ arm B CŨNG đổi** ⇒ **không so
  trực tiếp** được với số cũ (phải nói rõ, **không lặng lẽ thay số**); (b) `no_alt_action` là **mẫu số
  adherence** ⇒ đổi cách tính nó có thể đổi tỷ lệ nghe, phải kiểm cổng `D-M3-10` **không bắn oan**;
  (c) `pb-01` (chọn giữa tách-hai-pha vs keyed-hash) **không có artifact** ⇒ quyết định này chưa được
  phản biện, phải tự lập luận trong plan cycle.
- **Cơ hội gộp:** `mm-10` R-e nằm **đúng trên `should_defer_rest`** ⇒ cân nhắc gộp *"đọc `standby_plan`
  trước khi gọi `consider_relocate` cục bộ"* vào đây để **không mổ hai lần cùng một hàm**. ⚠ Nhưng R-e
  **chưa qua phản biện** ⇒ nếu gộp thì phải phản biện nó trong plan cycle, không gộp mù.

### CYCLE 2 — probe ĐẾM (không sửa code): tần suất bind của `D-M3-21`

- **Mục tiêu:** trả lời **%ngày-P4 có `newbie_guarantee_topup > 0`** và **`Δgross(P4) > 0` SIG hay không**,
  trên **artifact `positioning` n=100 ĐÃ CÓ** (chỉ chạy lại sim nếu event log thiếu trường).
- **Root cause đã chứng minh?** **Đại số CÓ** (`payout ≡ 262.500đ` hằng khi `gross < 350k`), **tần suất
  CHƯA** — đúng lý do `pb-05` chỉ **PLAUSIBLE**.
- **Test đỏ-trước:** không áp dụng (đây là **phép đếm read-only**, 0 dòng hành vi).
- **Acceptance (SỐ):** ra được **một con số %** kèm CI, và một verdict nhị phân *"guard 1b ĐA-08 hàng P4
  có power hay không"*.
- **Vì sao xếp thứ 2 dù không phải "sửa":** nó **rẻ nhất** (~30′), **an toàn nhất** (không đổi hành vi),
  và nó **đổi cách đọc con số `+6.016đ` mà tôi ĐÃ BÁO cho Cường**. Nếu %bind lớn ⇒ Cycle 4 (báo cáo) chạy;
  nếu ≈0 ⇒ **`D-M3-21` hạ severity và Cycle 4 HUỶ**, tiết kiệm hẳn một cycle.
- **Rủi ro đảo kết luận:** `day_bonus`/mission có thể **nằm ngoài** đồng nhất thức ⇒ P4 vẫn có đường
  hưởng lợi ⇒ khi đó phải sửa **cách phát biểu nợ**, không phải sửa metric.

### CYCLE 3 — `D-ADV-04`: sửa MẪU SỐ bucket của S1 (⚠ ĐƯỜNG SẢN PHẨM) (= Cycle B0 của plan)

- **Mục tiêu:** hết **false-infeasible có hệ thống** trên card F0/F1 cho tài xế thật.
- **Root cause đã chứng minh?** **CÓ — mức mạnh nhất trong cả file này: ĐÃ REPRODUCE có output thật.**
  Producer chia **điểm-của-bucket** cho **giờ online TOÀN NGÀY** (`bonus_gap.py:63-64` ·
  `from_l1r.py:161` · `ui/backend/app/adapters/advisor.py:74`); solver tiêu thụ như **điểm/giờ TRONG
  bucket** (`bonus_feasibility.py:51-53` + `_walk:72,79`). **Solver ĐÚNG, producer SAI** (ngữ nghĩa
  consumer bị test ghim `test_bonus_feasibility.py:113-119`). Khảo sát ADV-09 **đã làm xong** (plan §B0).
- **Test đỏ-trước (3 mũi):** (1) producer: online 08–18h, 60đ peak/2h + 60đ offpeak/8h ⇒ đòi
  `{peak: 30.0, offpeak: 7.5}` (hiện `{6.0, 6.0}` ⇒ **ĐỎ**); (2) end-to-end đúng đường production
  `derive_bonus_gap_input → solve` ⇒ đòi `feasible=True, hours_needed ≈ 2.42` (hiện `False` ⇒ **ĐỎ**);
  (3) survivorship: ngày online-phủ-bucket mà **0 điểm** phải đóng **0.0** vào mẫu (hiện biến mất ⇒ **ĐỎ**).
- **Acceptance (SỐ):** 1. ba test trên xanh. 2. **cả hai** suite xanh như baseline; **test ghim ngữ nghĩa
  solver KHÔNG được đổi**. 3. đo lại tỷ lệ `feasible` trên **5 persona × các giờ hỏi**, báo **trước/sau**;
  kỳ vọng số lượt *"không kịp"* **giảm** và **0 lượt** chuyển từ đúng-infeasible sang feasible-sai.
  4. `accept_lift` đang TẮT ⇒ fingerprint **5 seed IDENTICAL**.
- **Rủi ro đảo kết luận:** (a) **PHẢI sửa hai vế CÙNG LÚC** — mẫu số (bi quan) và survivorship (lạc quan)
  đang **bù trừ nhau theo tỷ lệ không kiểm soát**; sửa một cái làm số **đổi hướng khó hiểu**;
  (b) sửa xong advisor **lạc quan hơn** ⇒ nếu forecast vẫn là **median point-estimate** thì rủi ro
  *"khuyên bám mốc rồi không tới"* **TĂNG** (`mm-06` issue #2) ⇒ **không được claim "advisor tốt hơn"**
  chỉ vì bớt im lặng, phải ghi nợ kèm; (c) L1R **không có timestamp đủ mịn** ⇒ `oh_bucket` chỉ **xấp xỉ**,
  phải gắn nhãn xấp xỉ; (d) ba producer sửa ba chỗ ⇒ phải có **MỘT test dùng chung** ghim quy ước.

### CYCLE 4 — `D-M3-21`: tách `Δgross` khỏi `Δpayout` (KHÔNG đổi hành vi khuyên) (= Cycle C)

- **Điều kiện:** Cycle 2 cho **%bind > 0 đáng kể**. Nếu ≈0 ⇒ **HUỶ**.
- **Test đỏ-trước:** dựng cohort có **đúng 1** tài xế bind ⇒ `policy_absorbed` đếm **đúng 1**;
  `gross_mean` và `payout_mean` **khác nhau đúng lượng topup**.
- **Acceptance (SỐ):** 1. test trên xanh. 2. chạy lại **artifact n=100 đã có** qua thước mới và trả lời
  **`Δgross(P4) > 0` SIG hay không**. 3. **fingerprint IDENTICAL** (chỉ thêm metric).
- **Rủi ro:** event log cũ có thể **thiếu trường** ⇒ phải chạy lại n=100 (~10′).

### CYCLE 5 — `D-ADV-02`: `shift_extend` phải biết CỬA SỔ ĐIỂM (= Cycle B)

- **Điều kiện (hai cái, đều bắt buộc):** (i) **Cycle 3 xong** — `mm-06` issue #4 cho thấy producer in-sim
  đổ **day-average vào CẢ HAI bucket** (`advice_bridge.py:990-992`) ⇒ gọi S1 khi input còn sai thì **chỉ
  chuyển chỗ đặt lỗi**; (ii) **đo lại tần suất** (vì `pb-03` không có artifact) — nếu ~0 lượt kéo ca rơi
  sau 21h ⇒ **hạ severity, chỉ ghi comment cảnh báo, KHÔNG sửa** (tránh sửa cái không bao giờ chạy).
- **Root cause đã chứng minh?** **CƠ CHẾ: CÓ, 3 nguồn độc lập** (`advice_bridge.py:1122-1126` ·
  `policy.py:86-92` · `configs:254` = `[6..21]`). **CÁCH SỬA: chỉ PLAUSIBLE** — refuter không bác nổi
  đường S1 nhưng cũng không chứng minh được.
- **Test đỏ-trước:** (1) actor `shift_end = 21h30`, `gap_points > 0`, `rate > 0` ⇒ hàm hiện tại trả
  `add > 0`; test đòi **im lặng** với reason typed mới `points_window_closed` ⇒ **ĐỎ**; (2) actor kết ca
  **19h**, kéo tới 21h30 ⇒ `need_min` phải tính **chỉ phần trong khung**, **lớn hơn** số cũ.
- **Acceptance (SỐ):** 1. hai test xanh. 2. kênh TẮT ⇒ fingerprint IDENTICAL **5 seed**. 3. kênh BẬT
  **30 seed**: số lượt nói **giảm**, và **0 lượt** có cửa sổ kéo **hoàn toàn** sau 21h (đếm bằng event log).
  4. so Δ trước/sau, **KHÔNG claim tiền** (chưa prereg).
- **Rủi ro đảo kết luận:** (a) kênh có thể **câm hẳn** — đúng bài học `swap_early` gate chặt thành trơ;
  nếu câm thì **ghi trung thực** *"kênh này chỉ có nghĩa với ca kết trước ~19h"*, **không nới gate**;
  (b) `D-SIM-09` **hai nguồn sự thật** nếu vừa dùng `next_tier_gap` vừa dùng S1 ⇒ **phải chọn MỘT** nguồn
  cho `gap`; (c) **rẻ mà nên gộp**: `mm-02` S2-d (clamp `world_end` cụt) nằm **cùng hàm**, fix là so hai số
  đã có — nhưng **chưa phản biện**, gộp thì phải phản biện trong plan cycle.

### CYCLE 6 — `D-ADV-01` vế stagger-khoảng-cách (⚠ **KÊNH ĐANG SHIP** ⇒ regate n=100)

- **Mục tiêu:** **chỉ** thêm vế khoảng cách/Δ-giá-trị vào cost matrix S4, **giữ mismatch hữu hạn**.
  **KHÔNG** làm vế "objective thiếu Δ-giá-trị" (là DESIGN-GAP, cần Cường duyệt riêng) và **KHÔNG** làm
  TTL (đã hạ THẤP: 0,8%).
- **Root cause đã chứng minh?** **CÓ, mạnh nhất về ĐỘ LỚN trong cả file:** tie **EXACT** trong cost matrix
  (`capacity_alloc.py:50` — mọi ô lệch preferred cùng `pen+10.0`; dải `pen` chỉ `[0,1]` = 1/10 mức lệch ⇒
  **không bao giờ** phá được), cộng probe một chiều: **56%** lượt gán là staggered, **88%** trong đó đi
  **xa hơn** ô-còn-trần-gần-nhất, **+22% km** (628,9 vs 516,0 trên 3 seed; **41/48 lô tệ hơn, 0/48 ngược**).
  Và **không có test nào bảo vệ** hành vi chọn-đích-theo-alphabet.
- **Test đỏ-trước:** dựng lô có ô preferred hết slot, hai ô thay thế **rõ ràng khác khoảng cách** ⇒ đòi
  Hungarian chọn ô **GẦN HƠN** (hiện tie ⇒ vỡ theo **tên ô** ⇒ **ĐỎ**).
- **Acceptance (SỐ):** 1. test trên xanh. 2. **KHÔNG lật** `test_t14_hungarian_stagger_ve_own_cell_...`,
  `test_t14_zone_veto_dong_ca_stagger`, `test_t15_...` (⇒ **cấm** dùng `LARGE`), **và không lật**
  `test_capacity_alloc.py::test_low_soc_swap_priority` / `::test_herding_avoided_count` ⇒ trọng số km
  phải **cùng thang tiền/phút** hoặc nhỏ hơn ngưỡng `pen` (span 1,0). 3. **km rỗng giảm** về phía
  counterfactual 516,0 km, đo lại trên **cùng 3 seed** (1000/1001/1002) + mở rộng. 4. **REGATE ĐA-08 đủ
  9 dòng ở n=100** — `Δpayout_mean_all` **không âm SIG**, 0/7 archetype âm-SIG.
- **Rủi ro làm đảo kết luận:** (a) counterfactual của refuter minimize **km thuần** nên **BỎ ưu tiên SOC**
  ⇒ 516,0 km là **trần dưới không đạt được**, đừng lấy làm target; (b) mọi số probe **chỉ đúng cho
  `coverage=all`** — `coverage=single` (mặc định file config) cho **0 lượt gán, 0 event** ⇒ fix có thể
  **không đo được** ở arm mặc định; (c) đây là **kênh duy nhất đang dương SIG (+6.016đ, PASS 9/9)** ⇒ rủi
  ro **làm hỏng cái đang thắng** là thật; (d) `mm-01` math_issue #4 cảnh báo `slots = ⌊λ/1,5⌋` biến ô có
  cầu thật thành *"nguồn bị hút cạn"* (**248/255** lượt có `λ_own > 0`, median 1,79) ⇒ **thêm vế khoảng
  cách mà không chạm vách floor có thể chỉ dịch chỗ thiệt hại**.

### CYCLE 7 — `D-SIM-K3`: keyed RNG (= Cycle E) — **đòn bẩy cao nhất, chi phí LỚN**

Giữ nguyên như plan §Cycle E. Ghi nhận: `pb-02` **CONFIRMED** rằng `D-M3-20` **KHÔNG** phải trường hợp
riêng của K3 ⇒ **Cycle 1 đứng riêng, không gộp**. Cycle 7 vẫn là **điều kiện reopen (a) của `D-E4-06`**.
Cần **plan chi tiết riêng** trước khi động (đổi nền ngẫu nhiên ⇒ **mọi số cũ không so trực tiếp được**).

### KHÔNG LÀM — `D-ADV-03` "positioning chặng về" (= Cycle D)

**REFUTED ⇒ HUỶ** theo plan §0.1. Việc duy nhất còn phải làm: **ghi LÝ DO bác vào `DEFERRED.md`**
(hiện `pb-07` không tồn tại nên lý do chưa ai ghi được) — nếu không, ý tưởng này **sẽ bị đào lại**.

---

## 5. ⚠ CẢNH BÁO TRUNG THỰC — cái gì trong file này vẫn là SUY LUẬN CHƯA ĐO

1. **6/7 verdict phản biện không có artifact.** Chỉ `pb-06` (D-ADV-01) đọc được từ đĩa. Verdict của
   `D-M3-20` (×2), `D-ADV-02` (×2), `D-M3-21`, `D-ADV-03` là **chữ được relay**, tôi **không mở được** lý
   do, phương pháp, hay số của refuter. *"Tác tử báo"* ≠ *"tôi đo"*.
2. **`D-ADV-03` bị bác mà KHÔNG AI BIẾT VÌ SAO.** Tôi relay được REFUTED; **cơ chế bác thì không**. Đây là
   loại kết luận **thuận lợi cho việc "khỏi phải xây"** ⇒ đúng loại claim phải kiểm gắt nhất. **Không
   được đóng vĩnh viễn** trước khi lý do được viết ra.
3. **`D-ADV-02`: cả "tần suất CONFIRMED" lẫn "hướng sửa PLAUSIBLE" đều KHÔNG có số.** Đặc biệt
   **không ai được nói "X% lượt kéo ca sau 21h"** — con số đó, nếu refuter có đo, đã chết cùng artifact.
   Cycle 5 vì vậy **phải tự đo lại tần suất**, không được tin verdict chữ.
4. **`D-M3-21` là claim THUẬN LỢI cho advisor** (*"giá trị bị chính sách nuốt, không phải lời khuyên vô
   dụng"*) ⇒ đúng loại memory `verify-favourable-claims-hardest` dặn kiểm gắt nhất. Đã kiểm tới **đồng
   nhất thức đại số + dải tenure + ngưỡng online**; **tần suất bind thì CHƯA**. Cấm nói *"P4 vô hại/vô lợi
   trong X% ngày"*.
5. **Toàn bộ §3 (mm-02 + mm-10) CHƯA QUA PHẢN BIỆN NÀO.** Đó là hàng đợi, không phải kết luận. Trong repo
   này đã có tiền lệ: *"bug hai sổ"* hoá ra **thiết kế có test ghim** (ADV-09), và một bản *"đính chính"*
   lại **mắc đúng lỗi nó đi sửa**. **Không cycle nào được xây trên §3 trước khi có refuter.**
6. **Số của `pb-06` là 3 seed, arm `coverage=all`, config Đống Đa.** Không phải n=100, không phải arm mặc
   định. **112,8 km là slack CƠ CHẾ, KHÔNG phải Δpayout** — chưa có phép quy đổi km → đồng nào trong repo.
7. **`+6.016đ SIG (PASS 9/9)` của `positioning` chưa được đọc lại** dưới ánh sáng `D-M3-21`: nếu %bind của
   P4 lớn, phần giá trị tạo cho P4 **có thể đang bị sàn nuốt và chưa ai tách**. Con số vẫn đứng, nhưng
   **cách diễn giải per-archetype của nó thì đang treo** cho tới Cycle 2.
8. **Con số "~70% lượt bị coin từ chối"** (UPDATE-162, cho `D-M3-20`) là **suy ra từ tham số adherence
   P3/P5 ≈ 0,30**, KHÔNG phải phép đo trôi-stream. Đừng trích như số đo.
9. **`D-M3-20` là nợ do chính phiên trước tự tạo ra** trong cycle `D-M3-04-FIX` (2026-08-05) rồi báo
   *"acceptance passed"* cho Cường. Bộ số đó **phải đo lại**; đó là acceptance #3 của Cycle 1, không phải
   việc tuỳ chọn.
10. **Thứ tự cycle ở §4 là ĐỀ XUẤT của tôi**, dựa trên plan §0.2 + `mm-10` R-d. Ba chỗ tôi **chủ động lệch
    khỏi plan**, cần Cường xác nhận: (a) chèn **Cycle 2 = probe đếm read-only** lên trước Cycle B0 vì nó rẻ
    nhất và **đổi cách đọc số đã báo**; (b) thu hẹp Cycle D-ADV-01 xuống **chỉ vế stagger** (bỏ TTL, tách
    DESIGN-GAP ra); (c) gợi ý **gộp** `mm-10` R-e vào Cycle 1 và `mm-02` S2-d vào Cycle 5 để không mổ hai
    lần cùng một hàm — **cả hai đều chưa phản biện**, nên là gợi ý, không phải kế hoạch.

---

## 6. ⏳ Nhắc PENDING-REVIEW (bắt buộc sau mỗi update)

**V-31** (dashboard `:8501` · web `:8000/app/`) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
