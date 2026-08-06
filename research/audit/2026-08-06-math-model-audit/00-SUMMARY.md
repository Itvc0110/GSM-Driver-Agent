# 00-SUMMARY — Audit math-model + vòng phản biện: 5 nợ, verdict, thứ tự sửa

- **Ngày:** 2026-08-07 (bản viết lại — bản 2026-08-06 đã lỗi thời, xem §0) · **Cho:** Cường (đọc để RA
  QUYẾT ĐỊNH thứ tự sửa)
- **Nguồn ĐỌC TRỰC TIẾP cho bản này:** `pb-01` … `pb-07` (7 góc soi phản biện, **nay ĐÃ CÓ trên đĩa**) +
  `mm-04-rest-family.json` + `mm-07-s2.json`. Cite phụ: `UPDATE-142` (bảng acceptance D-M3-04-FIX),
  `UPDATE-087` (+6.016đ n=100), `UPDATE-160`, `UPDATE-163`, `tracking/DEFERRED.md`, `rc-02-numbers.json`.
- **Ranh giới giữ nguyên:** sức khoẻ KHÔNG vào objective (spec §1.2b, chỉ cổng một chiều tier-5) · số tài
  chính do rule/analytics tính · không can thiệp dispatch/matching/pricing/đơn cụ thể · mọi số dưới đây là
  **SIM MOCK** theo `configs/pilot_dongda.yaml` (seed ghi rõ), **không phải số thật GSM**.

## 0. ⚠ ĐỌC TRƯỚC — bản trước đã bị vô hiệu, và 6 số relay phải sửa

Bản 00-SUMMARY ngày 2026-08-06 mở đầu bằng cảnh báo *"6/7 artifact phản biện KHÔNG TỒN TẠI ⇒ CẤM trích số
của pb-01..05/07"*. **Cảnh báo đó nay HẾT hiệu lực:** cả 7 `pb-*` đều có trên đĩa, `mm-04-rest-family.json`
và `mm-07-s2.json` cũng đã có. Hệ quả:

- **Lệnh cấm trích số được GỠ** cho `pb-01..07` (số đọc được từ file, kèm probe script).
- **Ba verdict ĐỔI** so với bản trước: `D-ADV-02` (cách sửa) PLAUSIBLE → **REFUTED**; `D-M3-21`
  PLAUSIBLE → **REFUTED** (ở chuỗi suy ra); `D-ADV-01` CONFIRMED → **PLAUSIBLE** (hạ ở vòng 2).
- **Sáu số đang lưu hành phải đính chính** (mỗi số đều do refuter tự đếm lại, không relay):

| Số đang lưu hành | Ở đâu | Số ĐÚNG (nguồn) |
| --- | --- | --- |
| "đổi đích sang ô cách **3–5 km**" | `DEFERRED.md:122` | ô ranked gần nhất **1,66 km**; Δkm **+0,666/lượt = +67%** (`pb-07` §dinh_chinh) |
| bản W_NOW của D-ADV-02 "giữ **66%**" | `DEFERRED.md` D-ADV-02 (b) | **52,3%** (46/88) — refuter KHÔNG tái lập được 66% (`pb-04`) |
| "**16/77 = 20,8%**" lượt kéo ca chết | `DEFERRED.md` D-ADV-02 (a) | tử số 16 khớp; **mẫu số tranh chấp**: `pb-03` đếm 77 lượt ÁP, `pb-04` đếm 88 lượt NÓI ⇒ **18,2%–20,8%**, phải chốt MỘT định nghĩa |
| "phần lớn quyết định bị **cadence NÉN**" | mô tả D-M3-20 | **chưa từng xảy ra**: `configs:432 cadence.enabled=false` + `advice_bridge.py:334-335` ⇒ đo 0/379 và 0/386 (`pb-01`) |
| "adherence P3/P5 ≈0,30 ⇒ **~70%** lượt bị coin từ chối" | UPDATE-162 | coin từ chối **37–50%** (3/8 và 4/8); nguồn nhiễu áp đảo là `no_alt_action` (`pb-01`, `pb-02`) |
| "**arm ĐỐI CHỨNG** bị bẩn" | mô tả D-M3-20 | **sai chiều**: arm A rút **0 draw ở 20/20 seed** ⇒ arm A SẠCH; arm bị dịch là **B** (`pb-01`, `pb-02`) |

---

## 1. Bảng 5 nợ × verdict phản biện

| Mã nợ | Verdict theo GÓC SOI | Độ lớn ĐÃ ĐO (probe chạy thật) | Cái còn thiếu |
| --- | --- | --- | --- |
| **D-M3-20** — draw RNG ở `advice_bridge.py:916` phá ghép cặp CRN của `rest_window` | **CONFIRMED × 2, hai góc soi ĐỘC LẬP và ĐỒNG Ý.** (a) *chuỗi gọi có thật xảy ra không* = CONFIRMED. (b) *hậu quả đo lường*, sau khi cố bác qua 4 đường (CRN/stream riêng · trùng `D-SIM-K3` · độ lớn tương đối · acceptance định tính) = CONFIRMED, **cả 4 đường đều thất bại**. Hai artifact **không có điểm nào nghịch nhau**; `pb-02` chỉ bổ sung hai thứ `pb-01` thiếu (tỷ lệ SD vs CI acceptance; arm Bfix) | · arm A: **0 draw ở 20/20 seed** (SẠCH) · arm B multiday: **16–56 lần tới `:916`, 6–24 draw**/run 3 ngày · run **1 ngày = INERT** (A==B từng số: payout 22.908.261, 960 trip, rest 4026,1′) ⇒ lỗi **chỉ sống ở đường MULTIDAY** · **arm NULL** (coin luôn từ chối ⇒ **0 can thiệp**) vẫn lệch fingerprint **38/40 ngày-arm**; seed 7000 Δ **−1.625.279đ / −34 trip / +519,07′ rest** với **0** can thiệp · nền nhiễu n=20: rest_min_total SD **157,5′** (4,20% nền) · work_span_p90 SD **22,4′** (5,03%) · payout đội SD **318.718đ** (1,37%) · **SD nhiễu / SD suy từ CI acceptance UPDATE-142 = 1,12 · 1,22 · 1,05** ⇒ nhiễu MỘT MÌNH giải thích ~100% độ phân tán của Δ post-FIX · **arm Bfix (stream riêng) identical 60/60 ngày-arm** ⇒ draw ở `:916` là nguyên nhân **DUY NHẤT**, và acceptance đề xuất **là ĐẠT ĐƯỢC** | Δ **THẬT** sau fix: chưa ai đo (phải chạy lại `run_dm304.py` n=30, hoặc 100 theo prereg). Lệch **hệ thống** +94,2′ rest (t=+2,67, n=20, 3 phép so sánh ⇒ p~0,015) là **PLAUSIBLE**, cần n≥100 — **cấm trích thành "nhiễu có bias +94 phút"**. Bảng acceptance UPDATE-142 **không có artifact JSON** ⇒ ánh xạ `'rest_min'` → `health_guardrail.rest_min_total` là suy theo tên (dòng ratio 1,12 chưa xác nhận); `'idle_min'` **chưa đo**. Chưa chọn giữa hai đường fix (tách-hai-pha giữ ngữ nghĩa vs keyed-hash đổi ngữ nghĩa `p_move`) |
| **D-ADV-02** — `shift_extend` mù `point_window_hours` | **HAI GÓC SOI BẤT ĐỒNG — và bất đồng là về CÁCH SỬA, không về bug.** (a) *tần suất / có bao giờ BIND* = **CONFIRMED** (bug chạy thật, không phải nhánh chết). (b) *cách sửa đề xuất* = **REFUTED** — claim "gọi `S1 bonus_feasibility._walk` trên `[shift_end, shift_end+extend]`, kênh chỉ CHƯA GỌI" bị bác bằng **ba đoạn độc lập**. **Vì sao bất đồng:** hai câu hỏi khác nhau; (b) KHÔNG bác bug, chỉ bác đường sửa | · vùng chết bắt đầu **22:00**, KHÔNG phải "sau 21h" (`[6..21]` inclusive, `configs:254`) — sửa theo đúng chữ của claim thì **cắt mất 1 giờ có điểm thật** · **16** lượt có cửa sổ kéo **100% ngoài khung điểm** (P7:12, P5:4 theo `pb-03`; P7:9, P5:7 theo `pb-04`), **điểm kiếm được trong 16 cửa sổ đó = 0** (đo trực tiếp) · **128,1′** kéo vô ích / 5 seed ≈ **25,6′/ngày**; 12/16 lượt **<8′** · điểm tính theo **giờ KHÁCH ĐẶT** (`world.py:752`) ⇒ mất điểm vì hết ĐƠN MỚI, không vì cuốc bị cắt · `gap` treo trước 16 lượt: **510.000đ** · Về cách sửa: `_walk` **không có tham số END** (luôn đi tới nửa đêm, `DAY_END_HOUR=24.0`), bản nguyên văn cắt kênh xuống **12/88 = 13,6%** (gần TRƠ), bản W_NOW còn **46/88 = 52,3%** nhưng **TẮT một lan can sức khoẻ đang chặn 15.504/43.009 = 36,0% lượt gọi** (tái lập knife-edge: proj **1245′ → 1024,2′** vs thr 1220) · và **không sửa vế rate**: `need_S1 == need_flat` ở **70/88** lượt trên đường multiday · **bản cổng-HẸP** (không ai đề xuất) cắt đúng **16/88 = 18,2%**, giữ **72/88** nguyên vẹn | Mọi tỷ lệ đều **CÓ ĐIỀU KIỆN trên cổng CŨ** (88 lượt đã nói) ⇒ **không phải tỷ lệ hậu-fix**: 21.276 lượt `reachable_in_shift` + 15.504 lượt `would_exceed_fatigue` có thể **đảo sang nói**. Chưa CHẠY pytest để xác nhận 2 test ghim thật sự đỏ (refuter tái lập bằng số học trên đúng input của test). Chưa đo tác động hệ thống (payout/served) của bất kỳ bản sửa nào. Mẫu số 77 vs 88 chưa chốt. Chỉ 5 seed, 1 ngày, `shift_extend` bật đơn độc |
| **D-M3-21** — sàn bảo lãnh tân binh hấp thụ biên của P4 | **REFUTED** (một góc soi: *tần suất BIND + chuỗi hệ quả suy ra*). **Tiền đề bind thì ĐÚNG và mạnh hơn nợ nói**; **chuỗi suy ra bị bác ở cả 3 mắt** | · bind **96,25%** ngày-P4 arm A, CI [94,38; 98,12]; **97,5%** arm B — vế ràng buộc DUY NHẤT là `gross<350k`; `tenure≤90` và `online≥6h` **không bao giờ chặn** (online median 527′, min 481′) · **mắt 1 "payout HẰNG" BỊ BÁC**: **27 giá trị payout phân biệt** trong 154 ngày bind, dải **262.498…352.500đ**; đồng nhất thức đúng là `262.500 + mission + day_bonus` (residual ∈ [−2,+2] trên **toàn bộ** ngày bind) — mission và day_bonus **nằm NGOÀI** dòng nhất thức, và **46,1%** ngày bind có tiền không bị hấp thụ · **mắt 2 "đạo hàm 0 ⇒ guard 1b zero power" BỊ BÁC**: Δpayout ≠ 0 ở **125/150** ngày-CẶP mà **cả hai arm đều bind**, dải −70.000…+89.998đ; thêm **10/160 = 6,25%** ngày BIND-FLIP; `sd(Δpayout P4 theo seed) = 3.153đ` ⇒ ở n=100 **MDE95 ≈ 620đ** · **mắt 3 "payout_mean_all bị kéo về 0" BỊ BÁC**: **+5.351,8đ CI [+1.881; +8.955] SIG dương** ở n=10, khớp hướng+bậc với **+6.016đ SIG** n=100 (UPDATE-087) · cổng acceptance 0,85 **qua được**: 22,5% → 28,75% ngày (**+6,25 điểm phần trăm do positioning**) | n=**10** seed (ĐA-08 đòi 100) ⇒ "Δpayout P4 = +190,8 CI [−1.559; +2.023] ns" **chưa kết luận được**, chỉ là chưa đo ra ở n=10. **single-day** ⇒ lớp tân binh thứ 2 (50 cuốc/7 ngày) chưa kiểm. `guarantee_gross_floor_vnd = 350.000` là **PROXY có nhãn** (D-POL-05 image-locked) ⇒ tần suất bind 96–98% là **hệ quả của một giả định**, không phải sự thật GSM. Chưa đo với `cash_cost>0` (net của P4 vẫn biến thiên khi bật chi phí) |
| **D-ADV-01** — `positioning` (**kênh ĐANG SHIP**): feasibility, +10 phẳng, không `min_gain`, không TTL ⇒ *"thắng dưới trần"* | **PLAUSIBLE** (hạ từ CONFIRMED của vòng 1). **Không bác được vế cơ chế nào** — nhưng khối 4 chân + 1 kết luận có: 1 chân **sai nhãn** (feasibility = DESIGN-GAP tuyên bố, không phải bug), 1 chân **rỗng về độ lớn** (TTL), 2 chân **CONFIRMED và vật chất** (+10 phẳng · thiếu `min_gain`), **kết luận "thắng DƯỚI trần" chưa chứng minh** ⇒ không được gọi CONFIRMED cho cả khối | · **hai vòng độc lập khớp dấu và bậc**: staggered **143/255 = 56%** (3 seed) và **255/421 = 60,6%** (5 seed) ⇒ nhánh **ĐA SỐ** · root cause CHẮC là **tie EXACT**: mọi ô lệch preferred có cost `pen + 10.0` **bằng nhau tuyệt đối** (`capacity_alloc.py:50`); dải `pen = (100−SOC)/100 ∈ [0,1]` = **1/10** mức lệch ⇒ khoảng cách **không có mặt** trong cost matrix; probe tie: kẻ thua cost **11,0** trên CẢ 'AAA' và 'ZZZ', chọn 'AAA' **kể cả khi đảo input** ⇒ đích quyết bởi **tên ô** · km: counterfactual **628,9 vs 516,0 km = +112,8 km (+22%)**, 41/48 lô tệ hơn, **0/48** ngược chiều · **TTL: 0/179 lượt vượt biên bucket** (vòng 2; vòng 1: 1/122) và `market_state.py:162-167` **cache theo bucket** ⇒ "re-validate lúc thi hành" đọc lại **y nguyên** ảnh cũ ⇒ bản vá TTL **bất động ở 100%** lượt đo được · phạm vi: `coverage=single` (**mặc định file config**) cho **0 lượt gán, 0 event** (vs 81 event khi `all`) | **km → ĐỒNG: KHÔNG có đường nào trong arm đã đo** — `cash_cost_vnd_per_km: 0` (`configs:282`) ⇒ 112,8 km thừa tốn **0đ trực tiếp**; hai đường duy nhất (phút ENROUTE không match được · SOC → đổi pin sớm) **chưa ai phân rã**; D-F098-A đã sweep cash 0 và 250đ/km, **dấu positioning không đảo**. Counterfactual 516,0 km minimize **km thuần** nên **bỏ ưu tiên SOC** ⇒ là **thước độ lớn, không phải target**. Chưa sweep bucket ngắn / travel dài / adherence cao cho vế TTL; chưa tách 6 plan không-follow thành "hoàn thành im lặng" vs "reservation ma". Chưa đo Δpayout nếu THÊM vế khoảng cách |
| **D-ADV-03** — đề xuất kênh mới *"positioning chặng về"* (đổi đích deadhead-to-core theo cầu) | **REFUTED** — và lần này **CÓ CƠ CHẾ** (bản trước chỉ relay được chữ "REFUTED", không ai biết vì sao). Vế **quan sát code** thì ĐÚNG (deadhead mù cầu, `world.py:802-811` lấy ô lõi **đầu tiên gặp** trong `grid_disk`, không phải gần nhất); cái bị bác là **luận cứ kinh tế** ("chi phí biên ≈ 0") và **"đề xuất mở rộng tốt nhất"** | · nền: **0,994 km/lượt**, **541–555 lượt/ngày**, 538–552 km/ngày · **F1 TRẦN ĐÃ CẠN**: tổng trần vị trí cả ngày chỉ **70–95 suất**, đã bị **131–156 ứng viên** từ chối vì hết trần ⇒ đổi đích được **≤12,6–17,6%** lượt deadhead, và **lấy của chính kênh đang +6.016đ SIG** ⇒ zero-sum · **F5 GIÁ PHẢI TRẢ**: không lan can ⇒ **88,0%** lượt bị đổi, **+0,758 km/lượt = +512,6 km/ngày (+95%)**, **≥1.290,1 phút-đội/ngày** không-được-chào (ước thực tế ~2.300′) — so `station_choice` chỉ bơm **+98,9′/ngày** ⇒ **13–23×** nhiều hơn, **không có khoản tiết kiệm đối ứng** · **F3 MÙ**: `slots = ⌊λ/1,5⌋` ⇒ tổng slot toàn lưới **0 lúc 05h và 23h**, **3–4 lúc 10–15h**, tối đa 35 lúc 18h; **61% đơn chết** ở ô kênh **không bao giờ** gửi ai tới · **F4 HÌNH HỌC**: **64,6%** cặp ô lõi đã trong shortlist 2,22 km ⇒ đổi ô chỉ mở thêm **+8,2…+10,9%** cầu nhìn thấy · **F2**: `view()` cache 60′ ⇒ ~29 lượt deadhead/giờ đọc **một ảnh đóng băng** ⇒ đúng fallacy-of-composition mà module được xây để chặn · **trần hiệu ứng dưới độ phân giải**: nửa CI payout n=100 = **1.009đ ⇔ ±3,55–4,00 đơn/ngày** (rc-02 §3.5) · vế "hai chặng rỗng thay vì một" đo lại: xảy ra ở **tối đa 6,1–8,7%** lượt (n_follow 34–47 vs 541–555), **không phải 65%** · tiền đề câu hỏi "đơn chết trong hay ngoài lõi" **bị bác**: pickup_noncore = **0,00%** trên 3.570 đơn | **KHÔNG có arm B** — đề xuất chưa implement ⇒ mọi số "sau khi đổi đích" là **TÍNH TOÁN HÌNH HỌC** trên (giờ, ô-trả) có trọng số lượt thật, **không phải sim A/B**. Trần/ứng viên/n_follow đo **2 seed**; chồng lấn đơn chết **3 seed** (dưới chuẩn 5/30 của repo). Δphút chưa nhân detour ~1,46 và congestion ⇒ **cận dưới**. "Cầu nhìn thấy" là **PROXY** cho eligibility, bỏ qua cạnh tranh Hungarian và `offer_cooldown`. Chưa kiểm ở zone khác (D-SIM-01 treo) — **điều kiện mở lại của `DEFERRED.md:122` vẫn hợp lệ và refuter KHÔNG bác nó** |

---

## 2. Ba giỏ: sửa ngay / phải đo thêm / bị bác

### 2a. ĐỦ CHÍN ĐỂ SỬA NGAY (CONFIRMED + root cause chứng minh + acceptance đo được)

| Nợ | Vì sao đủ chín |
| --- | --- |
| **D-M3-20** — cách ly stream RNG ở `advice_bridge.py:916` | Chín NHẤT trong cả file. Hai góc soi CONFIRMED và đồng ý; **arm Bfix đo được identical 60/60 ngày-arm** ⇒ (i) nguyên nhân là **DUY NHẤT** một chỗ, (ii) acceptance là **bất biến nhị phân ĐÃ CHỨNG MINH ĐẠT ĐƯỢC**, không còn gì phải bàn về khả thi. Test đỏ-trước viết được ngay (hiện A==Bnull chỉ **1/20** ở day1 và **1/20** ở day2). **Đây là THƯỚC, không phải giá trị** ⇒ theo nguyên tắc xếp, nó đi trước mọi thứ chạm giá trị |
| **D-ADV-02 (a)** — cổng MỘT CHIỀU `points_window_closed` | Bug CONFIRMED bằng đo (16 cửa sổ chết, **điểm kiếm được = 0**), và **bản sửa đúng đã có sẵn**: cổng hẹp cắt **đúng 18,2%** lượt, **giữ 72/88 nguyên vẹn**, **không đổi `need_min`**, **không hạ lan can mệt**, **không phụ thuộc D-ADV-04b**. ⚠ Bản sửa "gọi S1" thì **REFUTED** — đừng làm |
| **D-ADV-01 — CHỈ vế (2) stagger mù khoảng cách** | Vế duy nhất **CONFIRMED hai vòng độc lập** (56% và 60,6%), root cause **CHẮC** (tie EXACT, tự tính lại được: 1,0 + 10,0 = 11,0 bằng nhau), **không test nào bảo vệ**. ⚠ Nhưng nằm trên **kênh ĐANG BẬT và đang là kênh DUY NHẤT dương SIG** ⇒ **regate ĐA-08 đủ 9 dòng n=100 là điều kiện, không phải tuỳ chọn** ⇒ xếp SAU hai cái trên |

> Ngoài 5 nợ: **D-ADV-04 (mẫu số bucket của S1)** vẫn là nợ chín nhất trên **đường sản phẩm thật** — đã
> REPRODUCE có output (`repro-s1-denominator.py` trên đĩa). **Nguồn của claim đó là phiên tổng hợp TRƯỚC,
> KHÔNG nằm trong 9 artifact của bản này** ⇒ tôi giữ nó trong thứ tự §4 nhưng gắn nhãn xuất xứ.

### 2b. PHẢI ĐO THÊM TRƯỚC KHI SỬA / TRƯỚC KHI TRÍCH

| Nợ | Phải đo cái gì (rẻ nhất trước) |
| --- | --- |
| **D-M3-20 — hai câu hỏi treo** | (i) lệch **hệ thống +94,2′ rest** (t=+2,67, n=20) là THẬT hay nhiễu-của-nhiễu ⇒ cần **n≥100**; nó quan trọng vì **đúng chiều làm cổng STOP-C dễ PASS hơn** và nó **ăn hết biên an toàn** của `REST_TOTAL_DROP_TOL=2%` (SE tỷ lệ ở n=30 chỉ 0,77%). (ii) ánh xạ metric: bảng acceptance UPDATE-142 **không có artifact JSON** ⇒ phải xuất bảng đó ra file trước khi so tiếp; `'idle_min'` **chưa đo** |
| **D-ADV-02 — tần suất HẬU-FIX** | Mọi tỷ lệ (13,6% · 18,2% · 52,3%) là **có điều kiện trên cổng cũ**. Sau khi sửa, dân số nói **đổi** (21.276 `reachable_in_shift` + 15.504 `would_exceed_fatigue` có thể đảo) ⇒ phải chạy lại toàn bộ cổng. Kèm: chốt **MỘT** định nghĩa mẫu số (lượt ÁP=77 hay lượt NÓI=88) |
| **D-M3-21 — PHÁT BIỂU LẠI, không phải sửa metric** | Chuỗi cũ REFUTED. Phát biểu **CÒN ĐÚNG**: *"guard 1b **UNDER-REPORT** tác hại lên **GROSS** của P4"* — `Δgross ≠ 0` ở **150/150** ngày-cặp nhưng ~2/3 biên độ bị topup trung hoà. Việc cần: (i) sửa chữ trong `DEFERRED.md` (đại số "payout HẰNG" là **SAI**), (ii) đo lại ở **n=100** (hiện n=10) và trên **multiday** cho lớp tân binh thứ 2, (iii) chỉ khi đó mới quyết có thêm metric tách `gross`/`payout` hay không |
| **D-ADV-01 — vế (5) "thắng dưới trần"** | **PLAUSIBLE, cấm trích như số.** Muốn nói bằng tiền: phân rã **phút ENROUTE không match được** + **SOC → đổi pin sớm**, hoặc chạy **arm `cash_cost>0`** paired n=100. Lưu ý phản chứng có sẵn: D-F098-A sweep 0 và 250đ/km, **dấu không đảo**; và `station_choice` tiết kiệm phút THẬT mà tiền KHÔNG lên (D-E4-06) |
| **Toàn bộ §3 (mm-04 + mm-07)** | **CHƯA qua phản biện nào.** Không cycle nào được xây trên §3 trước khi có refuter. Riêng một claim của `mm-04` **đã bị `pb-02` đính chính** — xem §3 ghi chú |

### 2c. BỊ BÁC — một dòng để không ai đào lại

- **`D-ADV-03` "positioning chặng về"** — **REFUTED, CÓ CƠ CHẾ ĐÃ GHI** (đây là thứ bản trước không có).
  Lý do gọn: **trần vị trí cả ngày chỉ 70–95 suất và đã bị 131–156 ứng viên tranh hết** (zero-sum với kênh
  đang +6.016đ) · đổi đích làm **km rỗng +67…+95%** = **1.290–2.300 phút-đội/ngày không-được-chào**, không
  có tiết kiệm đối ứng · **61% đơn chết** nằm ở ô mà `⌊λ/1,5⌋` khiến kênh **không bao giờ** tới · chỉ mua
  thêm **~9%** cầu nhìn thấy vì **64,6%** cặp ô lõi đã trong shortlist 2,22 km · trần hiệu ứng **dưới
  ±4 đơn/ngày = dưới độ phân giải phép đo tiền n=100**. ⇒ **Cycle D HUỶ, không code, không prereg.**
  ⚠ Điều kiện mở lại của `DEFERRED.md:122` (zone lớn hơn, D-SIM-01) **vẫn hợp lệ** — refuter không bác nó.
- **Cách sửa D-ADV-02 bằng `S1 _walk` trên `[shift_end, shift_end+extend]`** — **REFUTED.** `_walk` **không
  có tham số END** (luôn đi tới nửa đêm) ⇒ phải chọc vào 2 hàm **private**; phá **2 test ghim**, một trong
  đó là **lan can sức khoẻ** (proj 1245′ → 1024,2′ vs thr 1220 ⇒ rail tắt) — làm yếu cổng một chiều §1.2b
  **như tác dụng phụ là KHÔNG được**; và **không sửa vế rate** (`need_S1 == need_flat` ở **70/88** lượt
  multiday) ⇒ "sửa xong vẫn sai, chỉ đổi chỗ đặt lỗi". Bản nguyên văn còn cắt kênh xuống **13,6%** (gần trơ,
  đúng bài học `swap_early`).
- **Chuỗi "payout HẰNG ⇒ đạo hàm 0 ⇒ guard 1b zero power ⇒ payout_mean_all về 0"** — **REFUTED cả 3 mắt**
  (27 giá trị payout phân biệt · Δ≠0 ở 125/150 ngày-cặp · `payout_mean_all` **+5.352đ SIG dương**).
  Nguyên nhân đại số: **mission và day_bonus cộng SAU `_newbie_settle`** nên **nằm NGOÀI** dòng nhất thức —
  và đó là **THIẾT KẾ có test ghim** (`test_four_source_money_conservation`), không phải tai nạn.
- **"P4 part-time nên online < 6h"** và **"P4 thường vượt 350k"** — **cả hai SAI**: `online ≥ 6h` đạt
  **100%**, `gross < 350k` đạt **96,2–97,5%**. (Tức tiền đề bind **mạnh hơn** nợ nói, chỉ chuỗi suy ra sai.)
- **`D-ADV-01` vế "không TTL" ở mức CAO + bản vá "re-validate lúc thi hành"** — **bác về độ lớn VÀ về
  tác dụng**: **0/179** lượt vượt biên bucket, và `view()` **cache theo bucket** ⇒ bản vá **không huỷ được
  plan nào ở 100%** lượt đo được. ⇒ `extension_proposal #3` của `mm-01` xếp **sau cùng hoặc bỏ**.
- **`D-ADV-01` gọi vế feasibility là "BUG"** — **bác cách gọi tên**: `capacity_alloc.py:1-8` và
  `world.py:372-381` **tuyên bố thẳng** đây là bộ THI HÀNH TRẦN chống-herding ⇒ **DESIGN-GAP có chủ đích**;
  mở rộng cost là **ĐỀ XUẤT cần plan + duyệt Cường**, không phải root-cause fix.
- **Sửa cost lệch-target thành `LARGE` (cấm stagger)** — **đã bị chặn trước**: đập `test_t14_zone_veto_...`
  và `test_t15_...`. Sửa **phải THÊM vế khoảng cách, giữ mismatch HỮU HẠN**, và không lật
  `test_low_soc_swap_priority` / `test_herding_avoided_count` (dải `pen` chỉ 1,0 ⇒ trọng số km phải cùng thang).
- **`D-M3-20` = trường hợp riêng của `D-SIM-K3`** — **BÁC**: cơ chế K3 đòi **hành vi PHẢI KHÁC**, còn arm
  NULL ở đây có **đúng 0** hành vi khác mà vẫn lệch 38/40; và hai fix khác hẳn **về hệ quả** (K3 làm **mất
  hiệu lực mọi số cũ**; fix D-M3-20 để arm A **bit-identical** ⇒ không làm mất hiệu lực phép đo nào)
  ⇒ **Cycle 1 đứng RIÊNG, không gộp vào Cycle E**.
- **"Nhánh cam kết `:898` cũng rút RNG mỗi tick"** — **BÁC bằng đo**: **0/28** và **0/63** call đến từ nhánh
  commit.
- **Giả thuyết "`demand_hint` có thể là None nên bug không chạy"** — **BÁC**: `_actor_demand_hint` luôn trả
  dict (`{}` khi rỗng), và `{}` vẫn vào khối rút.

---

## 3. Finding MỚI từ `mm-04` (họ NGHỈ) và `mm-07` (S2 `shift_dp`) — **TẤT CẢ CHƯA QUA PHẢN BIỆN**

> ⚠ Hai artifact này **đã có trên đĩa** (khác bản trước) nhưng **chưa refuter nào soi**. Tiền lệ repo: một
> "bug hai sổ" hoá ra **thiết kế có test ghim** (ADV-09), và một bản "đính chính" **mắc đúng lỗi nó đi sửa**
> ⇒ đây là **HÀNG ĐỢI PHẢN BIỆN**, không phải kết luận. **Cả hai kênh đang TẮT** (`rest_window: false`;
> `shift_plan: false`, `sp_end_only: false`) ⇒ **không có tác hại đang chạy**; mọi severity là **severity
> CHO VIỆC MỞ LẠI**.
>
> ⚠ **Một claim của `mm-04` ĐÃ BỊ `pb-02` ĐÍNH CHÍNH:** `mm-04` viết *"`REST_TOTAL_DROP_TOL=2%` nằm ~8 lần
> DƯỚI nhiễu ⇒ cổng tầng 5 bắn/không-bắn gần như ngẫu nhiên"*. **QUÁ MẠNH:** `aggregate_health_guardrail`
> chạy flag trên **MEAN qua các seed**, không per-seed ⇒ SE co theo √n (ở n=30: rest **0,77%** vs tolerance
> **2%** ≈ 2,6σ biên an; span **0,92%** vs 10% ≈ 11σ). Cái **đúng đáng lo** là **lệch hệ thống +2,5%** ăn
> biên an của cổng rest, **không phải phương sai**. (Per-seed thì mm-04 không sai: 2/20 seed rớt >2% và
> 1/20 seed tăng >10% **chỉ do nhiễu**.)

### 3a. `mm-07` — solver `shift_dp` (S2), severity CAO/TB

| # | Finding | Sev | Bằng chứng đã đo | Vì sao đáng phản biện trước |
| --- | --- | --- | --- | --- |
| S2-1 | **Hai HÀM MỤC TIÊU khác nhau**: DP tối ưu trên **điểm ĐÃ FLOOR theo band** (`:188`, `:252`) nhưng được **BÁO CÁO/CHẤM trên điểm CHÍNH XÁC** (`:283`, baseline `:314`) ⇒ `delta_payout` **ÂM tới −55.000đ** dù test ghim `test_delta_nonnegative_vs_baseline` xanh | **CAO** | Repro tối giản deterministic: DP 161.746,2 vs baseline 191.746,2 ⇒ **Δ = −30.000,0đ** (đúng một mốc tier-60); điểm DP 56 vs baseline 72. **CAN THIỆP CHỨNG MINH NHÂN QUẢ**: `points_band_size` 5→1 ⇒ Δ **−30.000 → 0,0**. Tần số trên shape thật: **383/9.504 = 4,0%** cấu hình Δ<0, tệ nhất **−55.000đ**. **Test ghim VÔ HIỆU**: fixture cho **R=0** ⇒ không có bucket nghỉ nào để đặt ⇒ Δ ≡ 0 bất kể tính chất | Có repro + can thiệp nhân quả ⇒ **phản biện được dứt điểm**. Auditor **TỰ BÁC** giả thuyết mạnh hơn của chính mình ("DP hệ thống nghỉ vào giờ peak": đo 17.424 bucket REST, chỉ **12,7%** rơi vào peak, **THẤP hơn** nền ~25%) ⇒ dấu hiệu tự soi tốt, nhưng vẫn cần refuter độc lập |
| S2-2 | **ADV-01 CHƯA HẾT**: floor `add_pts // PBS` **per-bucket** bốc hơi **37,5%** tiến trình điểm mỗi bucket giờ thường | **CAO** | `add_pts` giờ thường = round(1,584×5) = 8, `8//5 = 1` band = 5 điểm ⇒ mất **3/8**. Ca 14 bucket: điểm chính xác **144** vs band **110** ⇒ **mất 34 điểm**. Với `points_now=40`: 184 (tier 115.000đ) vs 150 (tier 60.000đ) ⇒ DP lập kế hoạch như thể **mất 55.000đ** thưởng. **Test ADV-01 mù**: fixture cho `exp_trips = 1,000` chằn ⇒ `add_pts = 5 ≡ 0 (mod 5)` ở **cả 4 bucket** | Đây là **gốc** của S2-1 và là **điều kiện cần** trước bất kỳ lần bật lại `shift_plan`. Chi phí fix nhỏ (một dòng `DEFAULT_PARAMS`) nhưng **ô DP ×5** ⇒ **phải đo runtime trước khi chốt** |
| S2-3 | **cap `service_min_per_trip=25′` BIND ở 96,0% bucket** ⇒ eo **phẳng tuyệt đối 2,4** ⇒ vế payout của S2 **hết tín hiệu**; và **`sensitivity −20%/−40%` là ROBUST GIẢ** vì cap áp **SAU** `demand_scale` | **CAO** | **77.064/80.256 = 96,0%** bucket có `eo == 2,4` đúng chằn. λ đo: h=7 med 5,488 · h=18 med 7,135 ⇒ **85/85 cell vượt cap** ở h=7/18/21. Khi `grouped ≥ 4,0` thì `min(2,4; g×0,8) = min(2,4; g×0,6) = 2,4` ⇒ hai dòng sensitivity **bằng ĐÚNG base về mặt số học, không thể khác**. Ở dải thấp thì **NHẢY VÁCH và không đơn điệu**: 0 → **+37.948,7** → **+26.647,7** | ⚠ **Đây là claim THUẬN LỢI đang được relay ra output** (*"Δ bền với cầu −40%"*) — đúng loại phải kiểm gắt nhất (memory `verify-favourable-claims-hardest`). Và nó giải thích **bằng số** vì sao `delta == 0` ở 64,5% cấu hình |
| S2-4 | **Cầu = 0 ⇒ kế hoạch TOÀN SWAP** (9 SWAP / 12 bucket), `next_action = SWAP` **khi pin đầy**; `test_rest_when_zero_demand` **PASS trên đúng kế hoạch phi lý đó** (chỉ assert `!= 'ONLINE'`) | TB-CAO | `swap_fee=0` (D-E4-01) ⇒ phanh duy nhất chết; tie-break SWAP-trước-REST (CÓ CHỦ Ý cho SOC thấp) chiếm mọi thế hoà. Reachability trong sim: actor ở vành đệm có thể nhận hint **toàn 0 cả ca** ⇒ **PLAUSIBLE, chưa đo tần suất** | Hành vi solver **CONFIRMED**; reachability **PLAUSIBLE** ⇒ đúng chỗ refuter cần đo (đếm actor vành đệm) |
| S2-5 | **`sp_end_only` là CODE CHẾT**: `END` **bất khả** ở bucket 0 trong world zero-cost (chứng minh dominance + đo **0/68** và **0/612** cấu hình) ⇒ bật kênh E4/E-05 là đo một kênh **không bao giờ phát ra lời khuyên** | TB | `END` không có continuation; `ONLINE ≥ online_net + bonus_at(pb·PBS) > END` khi `online_net > 0`. Ngay cả `eo=0` cũng ra SWAP, không ra END | Đổi **cách đọc một ablation** (đúng lớp "cờ config nói SAI hành vi", UPDATE-117). Chưa kiểm UPDATE-155 đã báo số nào cho kênh này chưa — **nếu có thì số đó phải kiểm lại** |
| S2-6 | **Sổ pin solver và sổ pin world KHÔNG chia sẻ một tham số nào**: `20%/giờ` cứng của solver vs **~14,7%/giờ** tính từ config world ⇒ drift **~36%** ⇒ DP xếp SWAP **sớm hơn cần** | TB | `soc_cost_per_bucket=1 band/30′` + `soc_bands=10`; `solver_params()` **không truyền** `swap_consume_pct_per_km`. Test hiện có chỉ ghim **tỷ lệ** scale, **không ghim MỨC** | **Cùng lớp D-M3-17** (UI tự tính phạm vi pin khác engine), lần này ở tầng solver. `confidence` của auditor là **TB** (tính từ config, **chưa đo ΔSOC/giờ từ trace**) ⇒ refuter dễ có việc |

> `mm-07` còn 4 issue **THẤP hoặc TRƠ hôm nay** (`avg_dist_km` dùng cho cả doanh thu và chi phí ⇒ chi phí ước
> non ~40% **nếu bật C1**; `delta` là GROSS−GROSS trong khi DP tối ưu NET; SWAP không được tín dụng nghỉ
> (**MODEL GAP**, auditor **TỰ BÁC** giả thuyết "producer cộng lệch"); bucket mất dòng forecast = **LATENT,
> không đến được hôm nay**). **Một câu hỏi CHÍNH SÁCH cho Cường, không tự quyết:** *thời gian chờ/đổi pin có
> tính là nghỉ phục hồi?* — nới cổng nghỉ là **làm YẾU lan can một chiều §1.2b** ⇒ phải qua `policy_locks` + duyệt.
>
> ⚠ **`mm-07` tự ghi giới hạn quan trọng:** sửa S2-2 + S2-3 là **ĐIỀU KIỆN CẦN** để tái đo `shift_plan` có
> nghĩa, **KHÔNG phải bằng chứng ĐA-07 sẽ lật** (ĐA-07 bác ở n=100 bằng `served −0,33đp SIG`, đơn chết
> `+4,1 SIG`, Gini/HHI xấu SIG — **không chỉ bằng Δ**).

### 3b. `mm-04` — họ NGHỈ (S7 `idle_reduction` + `should_defer_rest`), severity CAO/TB

| # | Finding | Sev | Bằng chứng đã đo | Ghi chú phản biện |
| --- | --- | --- | --- | --- |
| R-1 | **Kênh KHÔNG CÓ hàm mục tiêu nào** — toàn bộ là chuỗi cổng boolean; nó **không so demand giữa giờ hiện tại và giờ đích**, chỉ kiểm `target != hour` ⇒ **3/15 lượt hoãn quan sát được dời nghỉ vào giờ CẦU CAO HƠN** theo chính tín hiệu S7 đã dùng | **CAO** | seed 7000 day1 **2/4** (11h→12h: 0,375→0,500; 11h→13h: 0,375→0,394), seed 7001 day1 1/1. Cổng `demand ≤ 0,5` nhận 13–14/24 giờ, gồm giờ 12 **đúng 0,500** trong khi giờ 9 = 0,5288 bị loại; dải "thấp điểm" hợp lệ trải **0,34–0,50** (lệch tương đối 32%) | **Cùng lớp `station_choice`** ở dạng cực đoan: station_choice còn có `argmin` để thêm vế, đây **không có phép tính nào**. Giá trị đúng = `rest_min × [λ(now) − λ(target)]`. Refuter nên tấn công: 15 lượt là **mẫu quá nhỏ**, và `demand_index` là chuẩn-hoá-theo-đỉnh nên "cao hơn" có thể không đổi dấu tiền |
| R-2 | **Lan can `soc_low` BẤT KHẢ ĐẠT theo cấu trúc** (rail chết) nhưng `REST_RAILS` vẫn tính nó là **1/3** lan can sức khoẻ ⇒ **ai xoá nó thì không test nào đỏ, không flag nào bắn** | **CAO** | `choose_idle_action` bước 1 đã đưa SOC thấp sang GO_SWAP/GO_CHARGE ⇒ world **chỉ hỏi bridge khi `action == REST`** ⇒ điều kiện `soc_pct ≤ soc_threshold` **FALSE theo cấu trúc**. Đo **0 veto `soc_low`** trong 12 ngày-đội. `RAIL_ALIVE_MIN_N=20` ⇒ nhánh "SỤP VỀ 0" **không bao giờ bắn**. Test hiện có gọi hàm **TRỰC TIẾP** ⇒ ghim ngữ nghĩa hàm, **không** chứng minh rail có đường chạy | Đây là **cơ chế tầng 5 mù với chính rail của nó** ⇒ chạm ĐỘ TIN của cổng an toàn. **Ranh giới:** đề xuất KHÔNG phải đưa sức khoẻ vào objective — chỉ đòi rail **hoặc sống hoặc bị khai tử tường minh** |
| R-3 | **Đường SỐNG DUY NHẤT nạp cho S7 dòng đơn NGOẠI SINH của hôm qua**, gồm **20,1% đơn KHÔNG ai phục vụ** ⇒ trái nguyên tắc "tuyệt đối không dựng từ `world.orders`" và trái caveat PROXY của chính solver | TB | seed 7000: **1.202 đơn sinh / 960 COMPLETED** ⇒ censoring 20,1%. Tập giờ "thấp điểm" theo GEN vs theo SERVED **đổi 3/24 giờ** (9, 15, 22 lật); lệch chỉ số tới **±0,234** | **KHÔNG phải rò tương lai** (ngày đã xong) — auditor nói rõ, đừng gọi sai tên. Là **PHÌNH TẬP THÔNG TIN** ⇒ mọi giá trị đo được của kênh là **CHẶN TRÊN**. Test duy nhất ghim "chỉ dùng belief" **chỉ phủ đường NỘI-NGÀY** — đúng đường đã đo là **INERT** |
| R-4 | **Bản sửa ADV-08 chỉ migrate PHÉP CỘNG, hai CỔNG vẫn dùng thước cũ** (lệch tới **59′**); và **cổng cuối ca thiếu hẳn thời lượng nghỉ** ⇒ nghỉ **trườn qua giờ kết ca** rồi END_SHIFT im lặng | TB | `minutes_to` đo giữa hai **ĐẦU GIỜ** dùng cho 2 cổng, còn sổ cộng `minutes_to − now%60`. Test ghim chính sự lệch này (now=9h10, target=11h ⇒ booked **110** còn cổng tính **120**). `rest_min = uniform(20,45)` chạy **bất chấp** `shift_end_min` ⇒ ràng buộc đúng là `due + REST_MAX ≤ shift_end` | Đúng tiền lệ *"một bản đính chính lại mắc đúng lỗi nó đi sửa"*. Chiều tác động của (a) là **BỚT can thiệp** ⇒ không che bug nào. **Tần suất nhánh "trườn qua shift_end" CHƯA ĐO** (mẫu `kept` chỉ 15 lượt) |
| R-5 | **Bậc `rest_window` của CHANNEL_LADDER không SẠCH quy trách**: cả KÍCH HOẠT (`alt != WAIT`) lẫn HÀNH ĐỘNG (RELOCATE `reloc_reason='rest_defer'`) **đều là positioning**, dù bậc đó khai `positioning_overrides: 'off'` | TB | Test **ghim chính điều này**: `assert reloc >= made` — mỗi cam kết sinh một relocate NGAY. RELOCATE đặt `ENROUTE` và pool chào đơn chỉ lấy IDLE ⇒ "việc có ích" cũng là **thời gian không nhận được đơn** | ⇒ Δ ở bậc này **TRỘN** (i) giá trị dời thời điểm nghỉ với (ii) giá trị một lượt relocate thêm. Cổng `alt != WAIT` là **PROXY tồn-tại, chưa bao giờ là định giá**. **Nằm ĐÚNG trên hàm mà Cycle 1 sẽ mổ** ⇒ cân nhắc gộp (nhưng **chưa phản biện** ⇒ gộp thì phải phản biện trong plan cycle) |
| R-6 | **Guardrail tầng 5 của họ REST neo trên `run_once`** — đúng đường mà kênh **INERT** ⇒ các rail chỉ sống ở multiday bị khai là "trơ" | TB | Trên run 1 ngày: `made=0` ⇒ `defer_cap`/`no_alt_action`/`at_window`/`commit_*` đều 0; trên multiday **`defer_cap` bắn 6–17/ngày** và `no_alt_action` **5–12/ngày**. ⇒ `veto_fired_n` ở fixture tầng 5 thực chất **chỉ còn `veto_fatigued_n`** (soc_low chết theo cấu trúc, defer_cap trơ theo đường đo) | Không phải test sai (T3 nói thẳng "ĐỎ = TIN TỐT") — nhưng **tiền đề của nó chỉ đúng trên `run_once`**, còn `D-M3-04-FIX` đã làm kênh nói được trên multiday. **Cùng lớp "đo arm đối chứng ở nơi không có gì để đo"** |
| R-7 | **`meals_taken` bị tiêu TRƯỚC khi bridge kịp hoãn** ⇒ nhánh `broken` **XOÁ** nghỉ chứ không **DỜI** nghỉ; bảo toàn chỉ được khai bằng **BẤT ĐẲNG THỨC** `made ≥ kept+broken+cleared` | THẤP | Đo **1 `broken` / 12 ngày-đội** (hiếm). Auditor **TỰ HẠ** giả thuyết mạnh hơn: `DANGLING = 0` ở **cả 12** ngày-đội ⇒ "cam kết treo im lặng tới END_SHIFT" là **cấu trúc cho phép, thực nghiệm chưa thấy** | Phần **CÒN ĐỨNG**: không invariant nào đòi Σrest_min được **BẢO TOÀN**. Nếu tần suất `broken` tăng (ví dụ do chính R-1) thì kênh **mua thu nhập bằng nghỉ bị XOÁ** mà sổ vẫn khớp. Là **kế toán**, không phải đưa sức khoẻ vào objective |

> `mm-04` cũng chỉ ra **tài sản đáng dùng**: cơ chế thi hành `rest_commit_due_min` + `rest_commit_gate`
> **đo được là SỐNG** (`kept > 0`, 15/15 lượt quan sát giữ cam kết) ⇒ ba mở rộng rẻ nhất (cổng hiệu cầu ·
> S7 chọn theo `argmin(demand)` trên tập TỚI-ĐƯỢC · meal-timing chủ động D-E4-05) **dùng đúng action đó và
> đúng hai analytics đã có**. Con số làm rõ vì sao liều can thiệp chỉ 1–3%: đo day1 seed 7000 có **56/90
> (62%) kế hoạch BẤT KHẢ** (gap 3–23 giờ so với `meal_hour`). **Tất cả CHƯA phản biện.**

---

## 4. Thứ tự cycle đề xuất

**Nguyên tắc xếp:** (1) nợ chạm **ĐỘ TIN của phép đo** trước nợ chạm **giá trị**, trước **tính năng mới** —
*sửa giá trị trên thước bẩn thì không đọc được kết quả*; (2) nợ chạm kênh **ĐANG SHIP** cần **regate n=100**
⇒ đắt hơn, xếp sau; (3) nợ trên **đường sản phẩm thật** trước nợ trên solver/kênh đang TẮT.

### CYCLE 1 — `D-M3-20`: cách ly draw RNG ở `advice_bridge.py:916`

- **Mục tiêu:** kênh **BẬT** mà **mọi quyết định bị từ chối** ⇒ fingerprint **bit-identical** arm A. Đây là
  **THƯỚC**, không phải giá trị: không sửa nó thì mọi Δ multiday của `rest_window` **không đọc được**.
- **Root cause đã chứng minh?** **CÓ — mức mạnh nhất trong file.** `:916 alt = alt_action_fn(actor)` chạy
  **TRƯỚC** cadence `:922` và coin `:933` → `world.py:1041` truyền `self.rng` (stream **DÙNG CHUNG** cho cả
  90 actor) → `behavior.py:228` rút `rng.random()` **có điều kiện** (33–39% call). Arm A **không tới `:916`**
  (return `no_window` ở `:907`) ⇒ **0 draw ở 20/20 seed**. **Arm Bfix (stream riêng) identical 60/60 ngày-arm**
  ⇒ đây là nguyên nhân **DUY NHẤT**; mọi thứ khác kênh bật làm là **behavior-neutral**.
- **Test đỏ-trước:** (1) kênh **BẬT** + `coin_follows → False` ⇒ `fingerprint_actors` phải **IDENTICAL** arm A
  trên **≥5 seed × 3 ngày** — hiện **ĐỎ** (đo: A==Bnull chỉ **1/20** day1, **1/20** day2, 20/20 day0).
  (2) `tests/test_rest_commit.py::test_alt_wait_thi_khong_hoan` **PHẢI GIỮ XANH** — thứ tự "alt TRƯỚC cadence"
  là **THIẾT KẾ có test ghim** ⇒ fix kiểu "chuyển `:916` xuống sau coin" sẽ làm test này **ĐỎ** ⇒ **không được**.
- **Acceptance (SỐ):** 1. hai test trên đạt trạng thái đúng. 2. bất biến CŨ không vỡ: kênh **TẮT** ⇒ identical
  arm A (`test_placebo_intervention_measures_exactly_zero`, `test_disabled_advice_does_not_shift_rng` giữ xanh),
  ≥5 seed. 3. **arm NULL sau fix phải cho Δ = 0,0 tuyệt đối** ở rest_min_total / work_span_p90 / payout đội —
  đối chiếu nền nhiễu **trước fix**: SD **157,5′ / 22,4′ / 318.718đ**. 4. **đo lại acceptance `D-M3-04-FIX`
  n=30 cùng cửa sổ seed cũ**, báo **CẢ HAI** bộ số; nếu kết luận đổi ⇒ banner **CORRECTED** lên UPDATE-142.
  5. **cả hai** suite xanh như baseline (`uv run pytest -q` **và** `uv run pytest -q ui/backend/tests` = 809+56).
- **Rủi ro làm đảo kết luận:** (a) **hai đường fix khác NGHĨA**: tách-hai-pha (gate tất định, rút `p_move` SAU
  coin) **giữ** ngữ nghĩa; keyed-hash **đổi** ngữ nghĩa (`p_move` không còn đồng bộ với bản năng) ⇒ **quyết định
  THIẾT KẾ, phải qua plan mode**; probe chỉ mô phỏng đường keyed-hash. (b) **KHÔNG được hứa "sửa rồi đo lại là
  sạch"**: ngay khi coin nghe (**~2 cam kết/ngày**) thì `D-SIM-K3` lại vào; fix này chỉ trả lại khả năng có
  **MỘT PHÉP KIỂM NULL**. (c) `no_alt_action` là **mẫu số adherence** và **KHÔNG nằm trong `REST_RAILS`** ⇒ đổi
  cách tính nó có thể đổi tỷ lệ nghe, phải kiểm cổng `D-M3-10` không bắn oan. (d) fix đổi thứ tự draw ⇒ **arm B
  CŨNG đổi** ⇒ không so trực tiếp với số cũ, phải nói rõ, **không lặng lẽ thay số**.

### CYCLE 2 — `D-ADV-02 (a)`: cổng MỘT CHIỀU `points_window_closed` cho `shift_extend`

- **Mục tiêu:** kênh **im** đúng ở những ca mà mốc **bất khả thi trong ngày theo cấu trúc** (cửa sổ kéo 100%
  ngoài khung điểm), **không đổi gì khác**.
- **Root cause đã chứng minh?** **CÓ, ba nguồn độc lập trùng nhau + đo trực tiếp:** rate phẳng theo ngày
  (`advice_bridge.py:1064-1224`, grep cả hàm: **không có** `point_window_hours`/`trip_points`) · `trip_points`
  trả **0** ngoài khung (`policy.py:86-92`) · `configs:254 = [6..21]` inclusive ⇒ vùng chết từ **22:00** ·
  và **điểm kiếm được trong 16 cửa sổ chết = 0** (đo, không suy). Chiều sai số **cùng một chiều, khuếch đại**:
  mẫu số `online_min` gộp cả giờ 0-điểm ⇒ rate ước NON ⇒ `need_min` ước CAO ⇒ **DỄ khuyên kéo hơn**.
- **Test đỏ-trước:** (1) actor P7 kết ca **23:20**, gap còn 10 điểm, rate 7đ/h ⇒ phải trả
  `(0.0, 'points_window_closed')`, hiện trả `add > 0` ⇒ **ĐỎ**. (2) **test biên NGƯỢC**: kết ca **21:40**
  (giờ 21 **CÒN** điểm) ⇒ **vẫn được kéo** — cổng này ghim đúng chi tiết lệch-1-giờ mà claim gốc viết sai.
  (3) `shift_end_min ≥ 1440` phải map về **24.0**, KHÔNG về 0.0 (đo: `_hour(1440) = 0` ⇒ walk đọc khung điểm
  **NGÀY MAI**, `hours_to_gap = 8,41h`, `checkpoints[-1] = 207,2` điểm).
- **Acceptance (SỐ):** 1. ba test trên xanh. 2. **ba test ghim công thức kênh giữ XANH**
  (`tests/test_e1b_cong_thuc_kenh.py:110-155`) — đây là điểm phân biệt với bản sửa bằng S1 (bản đó **phá 2/3**).
  3. lan can `would_exceed_fatigue` **vẫn chặn ~15.504/43.009 = 36,0%** lượt gọi (nếu tỷ lệ này TỤT ⇒ `need_min`
  đã bị đổi ⇒ **ngoài scope, dừng**). 4. đếm lại event trên **cùng 5 seed (1000–1004)**: lượt có cửa sổ kéo
  **hoàn toàn** ngoài khung điểm **16 → 0**; **72/88 lượt còn lại KHÔNG ĐỔI** (`add` từng lượt bằng số cũ).
  5. kênh TẮT ⇒ fingerprint IDENTICAL ≥5 seed. 6. reason mới **XUẤT HIỆN trong bảng veto** (không trả 0.0
  trắng — bài học D-QD4-03/N5).
- **Rủi ro làm đảo kết luận:** (a) **KHÔNG được kèm bản sửa `need_min`/rate** — nó **REFUTED** và nó **tắt một
  lan can sức khoẻ**; vế rate thuộc **D-ADV-04b, cycle riêng**. (b) tỷ lệ 18,2% là **có điều kiện trên cổng cũ**
  ⇒ **không được claim tỷ lệ hậu-fix** mà không chạy lại toàn bộ cổng. (c) mẫu số 77 vs 88: nếu chọn sai định
  nghĩa thì cùng một fix sẽ được báo là 18,2% hoặc 20,8% ⇒ **chốt định nghĩa TRƯỚC khi báo số**. (d) độ lớn nhỏ
  (**25,6′/ngày**, 12/16 lượt <8′) ⇒ **cấm claim tiền**; giá trị của cycle này là **ĐÚNG-LÝ-DO** + hết hai sổ
  points-per-hour (`src/gsm_core/rates.py` vừa CHỐT quy ước loại giờ 0-điểm khỏi **cả tử và mẫu**).

### CYCLE 3 — `D-ADV-01` **chỉ vế stagger-khoảng-cách** (⚠ **KÊNH ĐANG SHIP** ⇒ regate n=100)

- **Mục tiêu:** thêm vế khoảng cách vào cost matrix S4, **giữ mismatch HỮU HẠN**. **KHÔNG** làm vế feasibility
  (DESIGN-GAP, cần Cường duyệt riêng), **KHÔNG** làm TTL (bác cả độ lớn 0/179 lẫn tác dụng do cache bucket).
- **Root cause đã chứng minh?** **CÓ về CƠ CHẾ, tự tính lại được:** `cost[i,j] = pen` nếu đúng target, **`pen +
  10.0` nếu lệch** ⇒ mọi ô lệch **bằng nhau tuyệt đối**; probe: kẻ thua cost **11,0** trên cả 'AAA' và 'ZZZ',
  chọn **'AAA'** kể cả khi đảo input ⇒ **đích quyết bởi tên ô**. Tần suất **56%** (3 seed) và **60,6%** (5 seed),
  **hai vòng độc lập**. **Không test nào bảo vệ** hành vi chọn-đích-theo-alphabet.
- **Test đỏ-trước:** lô có ô preferred hết slot + hai ô thay thế **rõ ràng khác khoảng cách** ⇒ đòi Hungarian
  chọn ô **GẦN HƠN** (hiện tie ⇒ vỡ theo tên ⇒ **ĐỎ**).
- **Acceptance (SỐ):** 1. test trên xanh. 2. **KHÔNG lật** `test_t14_hungarian_stagger_ve_own_cell_...`,
  `test_t14_zone_veto_dong_ca_stagger`, `test_t15_...` (⇒ **cấm `LARGE`**), **và không lật**
  `test_low_soc_swap_priority` / `test_herding_avoided_count` ⇒ trọng số km phải **cùng thang** hoặc nhỏ hơn
  dải `pen` (span **1,0**). 3. km rỗng **giảm** về phía counterfactual **516,0 km** (từ **628,9**) trên **cùng
  3 seed (1000–1002)** + mở rộng 5 seed (5100–5104) — **516,0 là TRẦN DƯỚI KHÔNG ĐẠT ĐƯỢC** (counterfactual bỏ
  ưu tiên SOC), **đừng lấy làm target**. 4. **REGATE ĐA-08 đủ 9 dòng n=100**: `Δpayout_mean_all` **không âm
  SIG**, **0/7** archetype âm-SIG (tiền lệ: `station_choice` **FAIL** đúng dòng 1b với P1 −3.863đ AM-SIG).
- **Rủi ro làm đảo kết luận:** (a) **`cash_cost_vnd_per_km: 0`** trong đúng arm đã đo **+6.016đ** ⇒ km tiết kiệm
  **có thể không thành tiền theo cấu trúc** ⇒ cycle này rất dễ ra "km tốt hơn, tiền không đổi" (đúng khuôn
  D-E4-06); phải **nói trước** rằng acceptance là **km + không-xấu-đi về tiền**, không phải "tăng tiền".
  (b) mọi số chỉ đúng ở **`coverage=all`**; `coverage=single` (**mặc định file config**) cho **0 lượt gán** ⇒
  fix **không đo được** ở arm mặc định. (c) đây là **kênh duy nhất đang dương SIG** ⇒ rủi ro **làm hỏng cái đang
  thắng** là thật. (d) `slots = ⌊λ/1,5⌋` biến ô có cầu thật thành "nguồn bị hút cạn" ⇒ thêm vế khoảng cách mà
  **không chạm vách floor** có thể **chỉ dịch chỗ thiệt hại**.

### CYCLE 4 — `D-ADV-04` (mẫu số bucket của S1, **ĐƯỜNG SẢN PHẨM THẬT**)

Giữ nguyên như bản trước (đã REPRODUCE có output: `repro-s1-denominator.py`). ⚠ **Xuất xứ claim này là phiên
tổng hợp TRƯỚC, không nằm trong 9 artifact của bản này** ⇒ trước khi bắt đầu phải mở lại repro và xác nhận.
Lý do giữ nó ở đây thay vì cao hơn: nó **không chạm thước A/B** (Cycle 1–3 chạm), nhưng nó **chạm card tài xế
thật** ⇒ nếu Cường ưu tiên tác động người dùng hơn độ tin phép đo thì **đổi nó lên Cycle 2**. Ràng buộc cứng:
**`D-ADV-04b`** (bridge bơm day-average vào **CẢ HAI** bucket ⇒ `need_S1 == need_flat` ở **70/88** lượt) phải
xong **trước** bất kỳ ý định thay `need_min` phẳng bằng S1.

### CYCLE 5 — probe ĐẾM read-only: phát biểu lại `D-M3-21` ở n=100

- **Mục tiêu:** **không sửa hành vi**. Trả lời hai câu: (i) `Δgross(P4)` có SIG dương ở **n=100** không;
  (ii) tần suất bind ở **multiday** (lớp tân binh thứ 2, mốc 50 cuốc/7 ngày) — hiện chỉ có single-day n=10.
- **Root cause đã chứng minh?** **Tiền đề bind CÓ và mạnh** (96,25% CI [94,38; 98,12]); **chuỗi hệ quả cũ
  REFUTED** ⇒ việc cần là **sửa CHỮ trong `DEFERRED.md`** (đại số "payout HẰNG" là **SAI**: 27 giá trị phân biệt)
  và giữ phát biểu đúng: *guard 1b **UNDER-REPORT** tác hại lên GROSS của P4* (`Δgross ≠ 0` ở **150/150** ngày-cặp).
- **Test đỏ-trước:** không áp dụng (phép đếm read-only, 0 dòng hành vi). Nếu sau đó quyết thêm metric tách
  `gross`/`payout` thì test đỏ-trước là: cohort có **đúng 1** tài xế bind ⇒ `policy_absorbed` đếm **đúng 1**;
  `gross_mean` và `payout_mean` khác nhau **đúng lượng topup**; **fingerprint IDENTICAL** (chỉ thêm metric).
- **Acceptance (SỐ):** một verdict nhị phân về `Δgross(P4)` kèm CI ở n=100 (power đã biết: `sd(Δpayout P4)`
  = 3.153đ ⇒ **MDE95 ≈ 620đ**) + một con số %bind ở multiday.
- **Rủi ro làm đảo kết luận:** `guarantee_gross_floor_vnd = 350.000` là **PROXY có nhãn** (D-POL-05) ⇒ nếu sàn
  thật thấp hơn (vd 250k) thì bind **tụt mạnh** và toàn bộ nợ **đổi độ lớn**. **Đây mới là đòn bẩy đáng lo,
  không phải đại số.** Thêm: `cash_cost=0` nên `net == payout`; bật cost-km thì topup **không bù chi phí** ⇒
  net của P4 vẫn biến thiên.

### CYCLE 6+ — hàng đợi PHẢN BIỆN cho `mm-04` / `mm-07` (chưa phải cycle sửa)

Xếp theo "rẻ để phản biện dứt điểm × đổi cách đọc một số đã báo": **S2-3** (claim THUẬN LỢI *"Δ bền với cầu
−40%"* đang ra output) → **S2-1/S2-2** (có repro + can thiệp nhân quả; là **điều kiện cần** cho mọi lần bật lại
`shift_plan`, **không phải** bằng chứng ĐA-07 sẽ lật) → **R-2** (rail chết làm tầng 5 mù) → **R-1** (kênh không
có hàm mục tiêu) → **S2-5/S2-4** (code chết / kế hoạch phi lý) → **R-4/R-6** (thước và cổng) → còn lại.
**Cơ hội gộp:** **R-5** nằm **đúng trên `should_defer_rest`** (hàm Cycle 1 sẽ mổ) ⇒ cân nhắc gộp để không mổ
hai lần **nhưng phải phản biện R-5 trong plan cycle, không gộp mù**.

### KHÔNG LÀM — `D-ADV-03` "positioning chặng về" (= Cycle D)

**REFUTED có cơ chế ⇒ HUỶ.** Việc còn lại **rẻ và bắt buộc**: chép 5 cơ chế F1–F5 (§2c) vào `DEFERRED.md:122`
**thay cho câu "3–5 km" đang SAI**, kèm 5 điều kiện tối thiểu nếu ai muốn đào lại (bỏ sàn `⌊λ/1,5⌋` · giải
quyết cache 60′ mà không đổi view của planner · **nguồn trần RIÊNG** · thêm test veto km rỗng cho đường
`deadhead_to_core` — hiện được **MIỄN TRỪ TƯỜNG MINH** khỏi pin ≤2,0 km · prereg ĐA-08 đủ 9 dòng gồm 1b/P1).

---

## 5. ⚠ CẢNH BÁO TRUNG THỰC — cái gì trong file này vẫn là SUY LUẬN CHƯA ĐO

1. **Không một Δ "hiệu ứng thật" nào của `rest_window` trong repo hiện đọc được.** Nền nhiễu (0 can thiệp)
   **bằng hoặc lớn hơn** hiệu ứng đang báo: nhiễu seed 7000 **−1.625.279đ** vs Δ "hiệu ứng" quan sát
   **+450.736…−695.209đ**. Ba cổng được gọi là acceptance của `D-M3-04-FIX` (*"rest_min CI không dưới 0"*,
   *"idle_min CI chứa 0"*, *"work_span_p90 CI chứa 0"*) **đều là CI của nhiễu** — và **nhiễu làm chúng DỄ PASS
   hơn** ⇒ đó là phép kiểm **thiếu công suất**, không phải bằng chứng an toàn. Phần **ĐỊNH TÍNH** của cycle đó
   **KHÔNG bị lật** (cam kết made 2,0 [1,7;2,5] ~ kept 2,0 [1,7;2,4] là **ĐẾM TRONG ARM B**, không cần CRN;
   tác hại bản WAIT cũ **−244,0′** [−303,4; −182,8] = **1,55×** SD nhiễu **và** có cơ chế độc lập FIX-PRE
   bit-identical 30/30).
2. **Lệch hệ thống +94,2′ rest (t=+2,67, n=20, 3 phép so sánh) là PLAUSIBLE, KHÔNG phải "bias đã chứng minh".**
   Cấm trích thành *"nhiễu có bias +94 phút"*. Cần **n≥100**.
3. **Ánh xạ metric của `pb-02` chưa chắc:** bảng acceptance UPDATE-142 **không có artifact JSON trong repo** ⇒
   `'rest_min'` được ánh xạ sang `health_guardrail.rest_min_total` **theo tên + bậc độ lớn**; nếu là đại lượng
   khác thì **dòng ratio 1,12 chưa xác nhận** (hai dòng `work_span_p90` và payout đội vững hơn). `'idle_min'`
   **không được đo**.
4. **Hai probe của `D-ADV-02` cho hai mẫu số khác nhau trên CÙNG 5 seed** (77 lượt ÁP vs 88 lượt NÓI) — **tử số
   16 khớp**. Chưa ai hoà giải hai định nghĩa. Và **chưa ai chạy pytest** để xác nhận 2 test ghim thật sự đỏ
   dưới bản sửa S1 (refuter tái lập bằng số học trên đúng input của test).
5. **Một con số nền chưa đối chiếu:** `pb-03` báo *"thế giới 74 tài xế"* (370 actor-day / 5 seed) trong khi
   `pb-01`/`pb-02` chạy **90 actor**. Chưa ai giải thích chênh này ⇒ **mọi tỷ lệ "trên đầu tài xế" của `pb-03`
   (vd 25,6′/ngày/74 tài xế) phải được đọc như xấp xỉ**, không phải số đã đối soát.
6. **`D-M3-21`: tần suất bind 96–98% là HỆ QUẢ CỦA MỘT GIẢ ĐỊNH có nhãn**, không phải sự thật GSM
   (`guarantee_gross_floor_vnd` = PROXY, D-POL-05 image-locked). Và nó là **n=10, single-day, một config**.
   ⚠ Đây là claim **THUẬN LỢI** cho advisor ở vòng trước (*"giá trị bị chính sách nuốt, không phải lời khuyên vô
   dụng"*) và nó **ĐÃ BỊ BÁC** — đúng cảnh báo memory `verify-favourable-claims-hardest`.
7. **`D-ADV-01`: "đang thắng DƯỚI trần" là GIẢ THUYẾT CƠ CHẾ, cấm trích như số.** 112,8 km là **slack CƠ CHẾ**;
   `cash_cost_vnd_per_km = 0` **chặn** đường km→tiền **trong đúng arm đã đo +6.016đ**. Và **mọi số của nợ này
   chỉ tồn tại ở `coverage=all`** — ở mặc định file config, cơ chế +10 phẳng **không hề chạy** ⇒ **không ai
   được suy ra "sản phẩm mặc định đang chịu thiệt"**.
8. **`D-ADV-03` bị bác bằng TÍNH TOÁN HÌNH HỌC, không bằng sim A/B** (đề xuất chưa implement nên **không có
   arm B**). Trần/ứng viên đo **2 seed**, chồng lấn đơn chết **3 seed** — **dưới chuẩn 5/30 của repo**. Hai sai
   số của refuter **cùng nghiêng về phía đề xuất** (dùng `eff=0` ⇒ Δkm và Δphút là **cận dưới** của cái giá,
   39% chồng lấn là **cận trên** của cái lợi) ⇒ kết luận **bảo thủ**, nhưng **điều kiện mở lại vẫn hợp lệ**.
9. **Toàn bộ §3 (`mm-04` + `mm-07`) CHƯA QUA PHẢN BIỆN NÀO** — hàng đợi, không phải kết luận. Và trong đó **đã
   có một claim bị đính chính bởi `pb-02`** (tolerance 2% "8 lần dưới nhiễu" ⇒ sai vì cổng chạy trên MEAN) —
   bằng chứng sống rằng §3 **chưa được tin**.
10. **`D-M3-20` là nợ do chính chương trình tự tạo ra** trong cycle `D-M3-04-FIX` (2026-08-05) rồi báo
    *"acceptance passed"* cho Cường. Đáng chú ý: mục adversarial self-review của UPDATE-142 **đã tự ghi** rằng
    `consider_relocate` rút RNG từ stream world — nhưng **kết luận sai**: nó chỉ cảnh "so B_fix với B cũ", trong
    khi **chính B_fix vs A** mới là cái bị nhiễm. Bộ số đó **phải đo lại** — là acceptance #4 của Cycle 1.
11. **Thứ tự §4 là ĐỀ XUẤT của tôi, cần Cường xác nhận 3 chỗ:** (a) đặt `D-ADV-04` (đường sản phẩm thật) ở
    **Cycle 4** thay vì cao hơn — nếu Cường ưu tiên tác động người dùng hơn độ tin phép đo thì **đổi lên
    Cycle 2**; (b) thu hẹp `D-ADV-01` xuống **chỉ vế stagger** (bỏ TTL, tách DESIGN-GAP ra); (c) hạ `D-M3-21`
    từ "cycle sửa metric" xuống **probe đếm read-only** vì chuỗi suy ra đã bị bác.

---

## 6. ⏳ Nhắc PENDING-REVIEW (bắt buộc sau mỗi update)

**V-31** (dashboard `:8501` · web `:8000/app/`) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
**Mới phát sinh cần Cường quyết:** (i) `D-M3-20` chọn **tách-hai-pha** hay **keyed-hash** (đổi ngữ nghĩa
`p_move`); (ii) `mm-07` — *thời gian chờ/đổi pin có tính là nghỉ phục hồi?* (nới cổng nghỉ = làm YẾU lan can
một chiều §1.2b ⇒ **không tự quyết**); (iii) xác nhận 3 chỗ lệch thứ tự ở §5 mục 11.
