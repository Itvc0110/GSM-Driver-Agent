# RC-00 — VERDICT: vì sao thời gian thừa của `station_choice` không chảy vào đơn

> ## ⚠ ĐÍNH CHÍNH 2026-08-06 — đọc TRƯỚC §0 và §2
>
> Phép đo **F1 basin-map** (`f1-basin-map-KETQUA.md`, 0 seed, chính là falsifier mà mục adversarial của
> file này yêu cầu) đã chạy và **làm YẾU hai phát biểu dưới đây**:
>
> 1. **"đúng HAI ô bẫy"** là **quá hẹp**. Ở bậc sốt-ruột cao, luật leo dốc cho **6 attractor** (đều là
>    **chu trình hai ô** — đúng như §2(3) dự đoán ✅), nhưng lưu vực lớn nhất là **`88f`+`8c7` (42,8%)**,
>    **không phải** `953`/`bb3`; cặp `94b`+`953` chỉ **14,7%**, và `bb3` không có trong top-5 khi σ=0.
> 2. **"Bẫy do TÍNH ĐỊA PHƯƠNG, không do nhiễu"** — **SAI**. Với σ thực tế theo archetype (0,10–0,60),
>    attractor **vỡ thành 40–78 cái**, top-3 chỉ còn **30,4% → 13,7%** ⇒ luật leo dốc **một mình không
>    dự đoán được** việc 56,6% phút idle dồn vào đúng hai ô.
>
> **Phát biểu đã hiệu chỉnh:** *luật leo dốc + tầm nhìn 0,74 km tạo ra một **HỌ** điểm hút cục bộ và cung
> rảnh bị giam trong họ đó* — **không** phải *"đúng hai ô, do tính địa phương chứ không do nhiễu"*.
>
> **Phần KHÔNG bị bác, ngược lại còn được củng cố:** cơ chế **là** luật leo-dốc-theo-niềm-tin, không phải
> nhà ở/deadhead — `rc-03` đo nguồn vào hai ô hút: `relocate_demand_seek` **123** vs `deadhead` **2** vs
> `go_online` **4** (**95%** do chính luật đó). Và `give_up` sinh **chu trình hai ô** đã được F1 xác nhận
> độc lập, kể cả tìm ra đúng cặp `94b`+`953`.
>
> **✅ Claim HÌNH HỌC của §0 — nay ĐÃ XÁC NHẬN bằng số đo** (`f2-expired-by-cell.py`, đơn chết theo ô,
> arm A, 5 seed; cổng đối chiếu đạt: top-10 ô chiếm **42,0%** vs rc-03 báo **42,1%**): hai ô hút cách 5 ô
> nhiều-đơn-chết nhất **3,46–3,71 km** (dải tới 5,10 km) — khớp dải 3,40–4,73 km đã nêu, và **cả hai đều
> NGOÀI bán kính chào đơn 2,22 km**. Caveat "proxy" của F1 §2.6 **đã đóng**.
>
> **🔴 Phát hiện MỚI sắc hơn cả kết luận gốc:** cặp mà luật leo dốc **ưu ái nhất** (`88f`+`8c7`, lưu vực
> **42,8%**) nằm **1,34–1,60 km** từ ô nhiều-đơn-chết — tức **TRONG** bán kính 2,22 km — và bản thân nó có
> **4,60 đơn chết/ngày**; cặp `e2b`+`e2f` (12,9%) còn tốt hơn (`e2b` là ô đơn-chết **hạng 4**). ⇒ Vấn đề
> **không phải** *"luật chỉ tạo ra bẫy"* mà là ***"luật tạo ra vài điểm hút, có cả cái TỐT ngay cạnh cầu,
> nhưng đội xe lại dồn vào cái TỆ"***.
>
> **Còn `UNRESOLVED` (phát biểu lại cho sắc):** vì sao đội xe hội tụ về cặp **XA** thay vì cặp **GẦN** mà
> chính luật ưu ái hơn? Ứng viên chưa đo: phân bố `home_cell`/vị trí bắt đầu ca · belief cache theo
> `(actor, giờ, cell)` làm quỹ đạo phụ thuộc lịch sử · trường cầu đổi theo giờ nên lưu vực đổi trong ngày.
> ⚠ **KHÔNG** phải deadhead — rc-03 đã đo: `demand_seek` **123** vs deadhead **2** vs go_online **4**.

Ngày: 2026-08-06 · Vai: RC-04 (phản biện rc-01/rc-02/rc-03 + phán quyết cuối) · Mock: có (sim)
Tiền đề: `rc-01-mechanism.json` (cơ chế, đọc code) · `rc-02-numbers.json` (số nền) · `rc-03-overlap.json` (probe đo trong sim)

---

## 0. Trả lời thẳng câu hỏi của Cường

> *"Đáng ra thời gian thừa phải vào đơn chứ? Đây là do thiết kế sim kém à?"*

**Không, thời gian thừa KHÔNG thể vào đơn — và lý do chính KHÔNG phải "sim kém" chung chung, mà là
một khuyết tật CỤ THỂ ở bản năng đứng-chỗ của tài xế: tài xế rảnh bị KẸT trong hai ô "bẫy niềm tin"
cách MỌI ô có nhiều đơn chết 3,40–4,73 km, tức ngoài CẢ bán kính chào đơn (2,22 km) lẫn bán kính
ETA-khả-thi (3,14 km) — nên rót thêm bao nhiêu phút rảnh vào đó cũng không gặp được đơn nào.**

Ba số đóng đinh (đo trong lần soi này, **không phụ thuộc seed**, thuần hình học + config):

| Sự thật | Số | Nguồn |
| --- | --- | --- |
| Hai ô hút 56,6% toàn bộ phút idle của đội **là cực đại địa phương** của trường cầu kỳ vọng (hạng 5 và 6/85 ô) | `89415cb4953` / `89415cb4bb3`, cầu 31,85 đơn/ngày mỗi ô | `gsm_sim.demand.expected_demand_field` + `world.py:1158` |
| Khoảng cách từ hai ô đó tới **mọi** ô đầu bảng đơn chết | **3,40 – 4,73 km** (ngoài hex k=6 = 2,22 km, ngoài cả ETA-ball 3,14 km) | haversine trên `h3.cell_to_latlng` |
| Tầm nhìn niềm tin của tài xế rảnh | **0,74 km** (`grid_disk(cell, 2)`) trong khi bán kính tìm đường được nới tới **1,11 km** (ring 3) ⇒ **bước sốt-ruột cuối cùng là VÔ HIỆU** | `world.py:1165` vs `behavior.py:205,213` |

Tài xế chỉ di chuyển **lên dốc nghiêm ngặt** (`v_adj > best_val × bar`, bar 1,25→1,05 — `behavior.py:217`)
trên một trường niềm tin **TĨNH lấy từ config, không có vế cạnh tranh** (`world.py:1146-1175`), với
tầm nhìn 0,74 km. Ô đỉnh cầu số 1 (`89415cb4c0b`, 51,69 đơn/ngày — **cũng là ô nhiều đơn chết nhất**)
cách hai ô bẫy 3,86 và 4,63 km, và để đi từ bẫy sang đó phải **đi xuống dốc qua một thung lũng niềm tin**.
Luật đứng-chỗ hiện tại **không cho phép** điều đó. Kết quả: người rảnh vĩnh viễn ở sai chỗ, và
`station_choice` chỉ **làm dày thêm đúng chỗ đã thừa** (50,5% Δidle rơi vào chính hai ô đó — rc-03 §2).

**Nói ngắn cho Cường:** đây không phải lỗi của kênh chọn trạm, cũng không phải sim đo sai. Kênh làm
đúng việc của nó (chờ đổi pin −3,6′/lượt SIG). Thời gian nó trả lại rơi vào một **kho idle đã dư 68 lần**
so với nhu cầu, nằm **cách chỗ cần người 3–5 km**. Trong thế giới sim hiện tại, **không một kênh nào chỉ
giải phóng thời gian tài xế có thể thắng cổng tiền của ĐA-08** — và đó là điều Cường cần quyết (xem §6.5).

---

## 1. PHẢN BIỆN rc-03 — năm mũi bắt buộc

### 1.1 Probe có lọc đúng trạng thái eligible không? → **ĐÚNG, không bác được**

- Probe lọc `a.state != ActorState.IDLE: continue` (`probe_idle_overlap.py:141`) — **đúng và chỉ đúng**
  điều kiện dispatcher dùng: `idle = [a for a in self.actors.values() if a.state == ActorState.IDLE]`
  (`world.py:628`), và không có bộ lọc thứ hai nào trước khi gán (`world.py:639` chỉ kiểm lại IDLE).
- Probe **không** đọc `actor.idle_min` và **không** đọc `segments` ⇒ miễn nhiễm với mọi kẽ của hai
  đường đo đó. Đây là điểm mạnh nhất của rc-03.
- Cổng SOC (`world.py:652`) và `decide_accept` (`world.py:665`) xảy ra **SAU** khi đã chào ⇒ `n_both`
  của probe đúng nghĩa "tập Hungarian được phép gán", không phải "tập sẽ nhận".

**Kẽ CÒN LẠI (không bác kết luận nhưng phải ghi):** `n_both ≥ 1` **không** đồng nghĩa "đơn này lẽ ra
được phục vụ" — Hungarian gán mỗi tài xế tối đa 1 đơn/tick (`dispatcher.py:72-76`), nên một ứng viên có
thể đang là ứng viên tốt hơn cho đơn khác. ⇒ nhóm 3 (31,7%) là **cận trên của phần "vớt được"**, và
mọi số tiền suy từ nó (rc-03 §8) là CEILING. rc-03 có ghi cảnh báo này (§8 lý do ii) — giữ nguyên.

### 1.2 Bán kính dùng đúng số dispatcher không? → **ĐÚNG TỪNG SỐ, không bác được**

Đối chiếu công thức dòng-với-dòng:

| | dispatcher thật | probe |
| --- | --- | --- |
| shortlist | `grid_disk(order.pickup_cell, k_max)`, `k_max = disp_cfg["candidate_ring_k_max"]` = 6 — `dispatcher.py:80,111` | `grid_disk(pc, disp["candidate_ring_k_max"])` — dòng 130, 234 |
| ngưỡng | `eta_max = disp_cfg["eta_max_min"]` = 11 — `dispatcher.py:81,114` | dòng 235 |
| tốc độ | `speed_fn(order.pickup_cell, hour)` = `world._eff_speed(hour, pickup_cell)` — `dispatcher.py:101` + `world.py:634` | `world._eff_speed(hour, pc)` — dòng 132 |
| hệ số đường | `factor_fn(a.cell, order.pickup_cell)` = `world._dfac` — `dispatcher.py:104` | `world._dfac(a.cell, pc)` — dòng 145 |
| khoảng cách | `haversine_km(a.lat, a.lon, order.pickup_lat, order.pickup_lon)` — `dispatcher.py:103` | dòng 144 |

**PHÁT HIỆN MỚI khi kiểm mục này (BUG, chưa có hồ sơ):** config có **hai** khoá bán kính —
`candidate_ring_k: 4` và `candidate_ring_k_max: 6` (`configs/pilot_dongda.yaml:120,133`). Dispatcher
**chỉ đọc `_max`** (`dispatcher.py:80`; grep toàn `src/`: không nơi nào đọc `candidate_ring_k`).
Nhưng **dashboard vẫn có slider "Bán kính tìm tài xế (rings res9)" nối vào khoá CHẾT đó**
(`src/gsm_sim/dashboard.py:129-131`, default range `(2,8)` ở `dashboard_defaults.py:20`).
⇒ **một núm điều khiển stakeholder-facing kéo mà KHÔNG đổi gì.** Ai từng thử "nới bán kính" bằng
dashboard sẽ kết luận sai rằng bán kính không quan trọng. Đúng họ lỗi "cơ chế mồ côi" (UPDATE-117).

### 1.3 Năm seed có đủ cho claim CƠ CHẾ không? → **ĐỦ cho cơ chế, KHÔNG đủ cho độ lớn — và rc-03 thiếu một cột**

- rc-03 tự khai đúng: ở n=5, `orders_completed` Δ = −3,2 và `expired` Δ = −1,0 **ngược dấu** n=100
  (+1,69 / −1,86) ⇒ mọi phát biểu về Δ **kết quả** phải lấy từ `e01-station-100.json`. Đây là kỷ luật đúng.
- **Điểm bác được:** rc-03 báo các tỉ lệ cơ chế (53,88% · 14,43% · 31,7% · 69,6%) **không kèm độ tán
  theo seed**. Mẫu số 1.019 bản ghi **không phải 1.019 quan sát độc lập** — đơn trong cùng một seed
  chia nhau đúng một hình học cung. Cỡ mẫu hiệu dụng gần 5 (ngày), không phải 1.019. ⇒ **các tỉ lệ này
  chưa có khoảng tin cậy nào**, không được trích ra ngoài như số chốt.
- **Nhưng kết luận cơ chế vẫn đứng, vì có ba trụ độc lập không cần seed:**
  1. **Hình học tĩnh** (§2 dưới): bẫy cách đơn chết 3,4–4,7 km; tầm nhìn 0,74 km; ring 3 vô hiệu. Đây
     là hàm của config + H3, **không có RNG**.
  2. **Đồng nhất bộ đếm chính xác**: `assign − cooldown_blocked − offers_made = 0` **đúng bằng 0** ở cả
     hai arm (rc-03 §5). Tôi kiểm lại được vì sao nó phải đúng: giữa `match_batch` và vòng chào **không
     có `yield` nào** (`world.py:636-673`), Hungarian cho mỗi tài xế tối đa 1 cặp/tick, nên hai bộ lọc
     đứng trước cổng cooldown (`world.py:639`) **chưa bao giờ chặn cái gì**. ⇒ con số 69,6% là **đếm đúng
     từng lượt**, không phải xấp xỉ.
  3. **Phản thực ĐÃ CÓ SẴN mà rc-03 bỏ sót**: chính comment config đã ghi sweep 12 seed cho bán kính
     shortlist (`configs/pilot_dongda.yaml:126-133`): `k=6 → 233 đơn hết hạn · k=7 → 211 · k=8 → 196 ·
     k=12 → 195`. ⇒ nới shortlist cứu **−37 đơn/ngày** (12 seed), so với probe cho 29,4/ngày (n=5, cận
     trên). **Hai phép đo độc lập hội tụ** — đây là chỗ mạnh nhất của toàn hồ sơ, và rc-03 nói "chưa
     chạy phản thực" là **không chính xác**: phản thực bán kính đã chạy, còn no thì **bão hoà ở k≈8**
     (196 vs 195 ở k=12) — tức nới bán kính chỉ cứu ~16% kho đơn chết rồi hết.

### 1.4 Δidle có thể là artifact của cách đếm segment không? → **KHÔNG. Bác được mũi này.**

- Probe **không dùng segment ở bất kỳ đâu**. Nó lấy mẫu `ActorState.IDLE` mỗi 1′ (dòng 200-228).
- Hai đường đo độc lập khớp nhau: lấy mẫu state Δ = **+674,6′** vs bộ đếm `actor.idle_min` Δ = **+688,8′**
  ⇒ lệch **2,1% trên Δ** (rc-03 §4). Hiện tượng không phải ảo giác đo.
- Nhịp lấy mẫu 1′ so với lượng tử tích luỹ 2′ của nhánh WAIT (`world.py:1140,1144`) ⇒ đủ mịn (Nyquist).
- Cổng nhiễu-loạn xanh: fingerprint 7 số (`served_rate, orders_completed, expired, n_events, payout,
  idle_min, charge_min`) **trùng từng số** giữa có-probe/không-probe ở cả hai arm + exact-repeat.

**Kẽ đo THẬT thứ ba mà tôi xác nhận được ở tầng code (rc-03 chỉ nêu, tôi kiểm xong):** chặng đi tới trạm
được cộng vào **CẢ HAI** sổ — `actor.empty_min += travel` (`world.py:1248`) **và** `actor.charge_min +=
travel + wait + swap_s/60` (`world.py:1288`; nhánh thất bại `world.py:1277` cũng `travel + wait`).
⇒ sổ thời gian đội hở **+3,41%**. Kiểm mạch lạc: kẽ `idle_min` cộng-trước-timeout (+563′) cộng chặng
đi-trạm đếm-hai-lần (~194 lượt × ~4′ ≈ 780′) ≈ 1.343′ so với 1.555′ hở thật ⇒ **hai kẽ giải thích ~86%
độ hở**, phần dư ~200′ chưa truy. Đủ để nói: **"−698′ chết ở trạm" KHÔNG thuần là xếp hàng.**

### 1.5 Đối chiếu chéo rc-01 (cơ chế) với số rc-03 — **có MỘT mâu thuẫn thật + hai đính chính**

**(a) MÂU THUẪN THẬT — lời giải thích của rc-03 cho việc vế "cell trạm" của H2 đổ là SAI.**
rc-03 §2 viết: *"Lý do nằm trong code: sau swap actor IDLE tại cell trạm NHƯNG nếu cell đó ngoài lõi thì
vòng actor kế ép deadhead về lõi (`world.py:856-857`)"*. Tôi đo: **9 trong 11 ô trạm NẰM TRONG LÕI**
(chỉ `89415cb49c3` và `89415cb4eb3` ngoài lõi). Vậy với 9/11 trạm **không có deadhead nào bị ép** — cơ chế
mà rc-03 nêu **không hoạt động** cho phần lớn trường hợp.
*Con số 3,05% vẫn đúng; lời giải thích thì sai.* Cơ chế ĐÚNG là: sau swap tài xế IDLE tại ô trạm **trong
lõi**, vòng idle kế tiếp gọi `choose_idle_action` với niềm tin (`world.py:859-861`) và **leo dốc đi khỏi
đó** — thời gian di chuyển vào `empty_min` (`world.py:1131`), chỉ khi WAIT mới cộng `idle_min`
(`world.py:1140`). Tức tài xế **không đứng ở trạm, mà đi thẳng vào bẫy niềm tin**.
**Vì sao mâu thuẫn này QUAN TRỌNG:** nó đổi hẳn hướng sửa. Nếu nguyên nhân là deadhead-ngoài-lõi thì
sửa hình học lõi; nếu nguyên nhân là leo dốc niềm tin thì phải sửa `behavior.consider_relocate` /
`_actor_demand_hint` — và **đó mới là chỗ đúng** (§2).

**(b) Đính chính rc-01:** rc-01 evidence ghi *"offer_history ghi TRƯỚC khi xét, world.py:646"* — **sai
thứ tự**. Code: kiểm cooldown ở **644**, ghi `offer_history` ở **646** (sau). Kết luận của rc-01 (SOC-skip
cũng nạp cooldown) **vẫn đúng** vì dòng 646 chạy trước nhánh SOC ở 654; chỉ mô tả thứ tự là sai.

**(c) Đính chính rc-02:** rc-02 §3.1 dùng `698 ÷ 3,5991 = 193,9 lượt swap` để kết luận *"−698′ về bản
chất là GIẢM XẾP HÀNG, không phải giảm thời gian đổi pin thật"*. Với phát hiện §1.4 (chặng đi trạm nằm
trong `charge_min`), phép phân rã này **không định danh được**: Δcharge trộn Δchờ **và** Δđi-đường. Giữ
kiểm-mạch-lạc, bỏ kết luận.

### 1.6 Một chỗ rc-03 **quy sai địa chỉ** (bác được)

rc-03 §8 gán **38,8 đơn/ngày** và **+9.100…10.600đ/tài xế** cho `bug_2_cooldown_sau_gan`. Nhưng 38,8
là nhóm **3a** ở §1, mà định nghĩa của 3a là *"(≥2 ứng viên đồng thời NHƯNG ≤1 lượt chào cả đời) HOẶC
(có ứng viên NHƯNG 0 lượt chào)"* — **không phân biệt** ba nguyên nhân khác nhau: (i) cổng cooldown nuốt
tick, (ii) Hungarian đã gán tài xế đó cho **đơn khác** (cạnh tranh, không phải bug), (iii) artifact lấy
mẫu 1′. Con số **đặc trưng cho cooldown** là `share_dead_with_cool_blocked_assign = 23,26%` (≈47,4
đơn/ngày **bị chạm**), và thiệt hại mỗi đơn bị chạm chỉ là **30,5 tick × 5s ≈ 2,5′** trong một đời
5–10′ — **không phải mất trắng cả đơn**. ⇒ **ceiling tiền của bug_2 trong rc-03 là KHÔNG CÓ CĂN CỨ như
đã gán nhãn.** Phải đo riêng (§6.2).

### 1.7 Ba chỗ rc-03 tự làm yếu mình mà nên nói rõ hơn

- **Chiều thiên lệch của phép lấy mẫu 1′ ngược với kết luận:** nhóm 1 (53,9% "không ai ETA-khả-thi cả
  đời") và nhóm 2 (14,4% "chết thuần vì shortlist") đều là **CẬN TRÊN**, nhóm 3 (dispatcher) là **CẬN
  DƯỚI** (rc-03 tự cho đường chéo: ≥34,8%). ⇒ phép đo **thiên vị câu chuyện "vướng bán kính"** và
  **hạ thấp phần dispatcher**. Kết luận nghiêng-về-H2 của rc-03 vì thế **không phải kết luận thận trọng**.
- **Pearson = 0,0005 trên 24 điểm giờ là số MỎNG**, bị hai giờ ngoại lai chi phối (giờ 18 có 31,2 đơn
  chết **mà Δidle vẫn +50,6** — tức không hề "lệch pha" ở đó). Phát biểu **bền** là phát biểu theo tỉ
  trọng: *6 giờ đỉnh chứa 59,1% đơn chết nhận 5,8% thời gian*. Dùng cái đó, bỏ Pearson.
- **Tái tạo:** rc-03 §10 trỏ tới `research/audit/2026-08-06-root-cause-idle/rc-03-probe-script.py` —
  **file KHÔNG TỒN TẠI trong repo** (chỉ có 3 file JSON trong thư mục đó). Bản chạy được nằm ở scratchpad
  của session (`.../2a13ca96-.../scratchpad/probe_idle_overlap.py`), sẽ mất. Artifact thô
  (`rc03-raw.records.json`) cũng không commit. ⇒ **rc-03 hiện KHÔNG tái tạo được từ repo.** Phải sửa trước
  khi trích số ra ngoài.

---

## 2. BẰNG CHỨNG MỚI của lần soi này — hình học tĩnh, **không cần seed**

Đây là phần biến "giả thuyết H2" thành **cơ chế chứng minh được**. Mọi số dưới đây là hàm của
`configs/pilot_dongda.yaml` + lưới H3, chạy được lặp lại, **0 RNG**.

**(1) Thế giới nhỏ hơn ta tưởng, và shortlist KHÔNG phải nút thắt hình học chính.**
Lõi = **85 ô** res 9; đường kính lớn nhất **5,35 km**; trung vị cặp ô 1,70 km. Với một ô lõi bất kỳ:
`grid_disk(k=6)` phủ trung bình **64,6%** số ô lõi (min 18,8% với ô rìa), gần đúng bằng quả cầu 2,22 km
(65,0%). Nới lên bán kính ETA-khả-thi 3,14 km sẽ phủ **88,9%**. ⇒ dư địa của BUG-DISPATCH-SHORTLIST là
**+24 điểm phần trăm diện tích**, khớp với sweep 12-seed đã có (233 → 196 đơn hết hạn).
*Hệ quả:* bán kính 2,22 km trong một quận rộng 3–5 km **không hề chật một cách phi lý** — nên **"vướng
bán kính" là hệ quả, không phải nguyên nhân**. Nguyên nhân là **người rảnh ở đâu**.

**(2) Cung rảnh bị KẸT trong cực đại địa phương của niềm tin, cách cầu 3,4–4,7 km.**
Xếp hạng 85 ô theo `expected_demand_field` gộp ngày:

| ô | hạng | cầu KV/ngày | idle nền A | đơn chết A | là cực đại địa phương (ring 2)? |
| --- | --- | --- | --- | --- | --- |
| `89415cb4c0b` | **1** | 51,69 | 253′ | **13,6** | có |
| `89415cb4c03` | 2 | 44,25 | 254′ | 12,6 | không (leo sang c0b) |
| `89415cb4953` | 5 | 31,85 | **2.691′** | 1,8 | **CÓ** |
| `89415cb4bb3` | 6 | 31,85 | **5.662′** | 1,4 | **CÓ** |

Khoảng cách hai ô bẫy → ô đỉnh cầu/đỉnh đơn-chết: **`953→c0b` 3,86 km · `bb3→c0b` 4,63 km · `953→c33`
3,40 km · `bb3→c03` 4,73 km** — **không ô nào nằm trong `grid_disk(k=6)`**, và **tất cả đều > 3,14 km**
(ngoài cả quả cầu ETA-11′). Hai ô bẫy cách nhau 0,98 km ⇒ chúng là **một vùng bẫy ~1 km** giữ
**56,6% toàn bộ phút idle của đội**.

**(3) Vì sao tài xế không đi ra được — ba mảnh code cùng chặn:**

| mảnh | code | hệ quả |
| --- | --- | --- |
| tầm nhìn niềm tin **cứng 0,74 km** | `world.py:1165` `for c in sorted(grid_disk(actor.cell, 2))` | ô cách >0,74 km **không tồn tại** trong niềm tin |
| bán kính tìm nới tới ring 3 = **1,11 km** | `behavior.py:205,213` (`idle_impatience_max_steps: 2`, config:207) | ô ring 3 trả `demand_hint.get(nb, 0.0) = 0` ⇒ **bước sốt-ruột CUỐI CÙNG là no-op** — cơ chế "rỗi lâu ⇒ đi XA HƠN" (docstring `behavior.py:191-197`) **không thi hành được** |
| chỉ đi **lên dốc nghiêm ngặt** | `behavior.py:217` `if v_adj > best_val * bar` (bar 1,25 → 1,05) | không bao giờ băng qua thung lũng niềm tin |
| nhánh "thôi tin niềm tin" cũng bị giam | `behavior.py:224-227` chọn max trên `_neighbors(ring)` — ring 3 toàn 0 ⇒ vẫn chọn ô ring ≤2 | cho phép **một** bước xuống dốc rồi leo lại ⇒ **chu trình 953 ↔ 94b**; `idle_streak` reset mỗi lần relocate (`world.py:1137`) ⇒ lại 40′ mới sốt ruột lần nữa |
| niềm tin **không có vế cạnh tranh** và **tĩnh cả ngày** | `world.py:1146-1175` (config-prior × nhiễu lognormal σ 0,10–0,60, cache theo (actor, giờ, cell)) | mọi tài xế thấy gần như cùng một bản đồ, **không ai biết ở đó đã đông** ⇒ dồn đàn |

Nhiễu per-actor **không cứu được**: để so 51,69 với 31,85 cần `ln(1,62)=0,48`; nhưng phép so **chưa bao
giờ xảy ra** vì c0b cách 3,86 km — ngoài tầm nhìn 0,74 km. **Bẫy do TÍNH ĐỊA PHƯƠNG, không do nhiễu.**

**(4) Thế giới được CỐ Ý làm dư cung — nên năng suất biên của phút idle ≈ 0 theo thiết kế.**
Sổ thời gian đội (rc-03 §4, arm A): online 45.611′ · idle **15.310′ (33,6%)** · empty 10.883′ (23,9%) ·
occupied 13.683′ (30,0%) ⇒ **utilization 30%**. Config ghi rõ đội xe được **nâng 74 → 90 như một đòn bẩy
để kéo `served_rate` vào dải 80–85%** (`configs/pilot_dongda.yaml:222-228`: `74→0.742 · 78→0.760 ·
84→0.779 · 90→0.797 ✅`), và tự nhận `trips/driver ≈ 10` so với benchmark 18–22 là **giới hạn cơ cấu
một-quận (D-SIM-01, đã DEFER)**. ⇒ **dư cung là lựa chọn calibration có văn bản.** Trong một thế giới
như thế, mỗi đơn chết đã có ~68 phút-đội idle nằm cạnh mà không gặp (rc-02 §3.5); thêm 7,76′/tài xế
(+5,4% kho idle) **không thể có giá trị biên nào**.

---

## 3. Verdict từng giả thuyết SAU phản biện

| | Verdict cuối | Bằng chứng đứng | Bằng chứng đổ |
| --- | --- | --- | --- |
| **H1** CALIBRATION lệch pha giờ | **ĐỨNG ở dạng yếu — nhưng phải ĐỔI TÊN thành PHASE OFFSET CẤU TRÚC, không phải "calibration sai"** | 6 giờ đỉnh (06-08 + 16-18) chứa **59,1%** đơn chết nhận **5,8%** thời gian giải phóng; 10-13 + 20-23 chứa 27,1% nhận **88,6%**; ở 06-08h Δidle = **−16,4′** | (a) dạng mạnh SAI: trung bình vẫn có **9,49** tài xế rảnh toàn thành phố lúc đơn chết, chỉ 5,4% đơn chết lúc không còn ai rảnh. (b) **Không có tham số nào đặt sai**: pin chưa thể cạn trước 8h (Δ = 0,0 **chính xác** ở giờ 5,6,7) ⇒ lệch pha là **hệ quả vật lý** của "phải chạy mới hết pin", không phải calibration lỗi. (c) Pearson 0,0005 là số mỏng — giờ 18 có 31,2 đơn chết mà Δidle **+50,6** |
| **H2** POSITION MISMATCH | **ĐỨNG — và là THÀNH PHẦN CHI PHỐI. Vế "cell trạm" ĐỔ; lời giải thích của rc-03 cho việc đổ đó cũng SAI (§1.5a). Cơ chế đúng đã CHỨNG MINH ở §2** | Bẫy niềm tin cách đơn chết **3,40–4,73 km** (ngoài cả 2,22 và 3,14 km); tầm nhìn 0,74 km; ring 3 no-op; 2 ô giữ 56,6% idle nền và nhận 50,5% Δidle nhưng chỉ có **1,57%** đơn chết; 10 ô nhiều đơn chết nhất (42,1% kho) nhận **−13,0′**; tương quan qua ô ≈ 0 (0,041/0,114); trung vị khoảng cách đơn-chết→người-rảnh-gần-nhất **2,575 km / ETA 13,39′** | Chỉ **3,05%** Δidle vào ô trạm (nền 2,60%) ⇒ tài xế **không đứng ở trạm**. Và 9/11 ô trạm **trong lõi** ⇒ giải thích "bị ép deadhead" của rc-03 sai |
| **H3** DISPATCHER GAP | **ĐỨNG như người ĐẶT TRẦN — KHÔNG giải thích Δ A/B (đối xứng hai arm). Độ lớn của khuyết tật cooldown thì CHƯA ĐO ĐÚNG (§1.6)** | (a) **69,6%** slot gán bị cổng cooldown nuốt **IM LẶNG** (2.595/3.723 mỗi ngày), `continue` không log, không chào người kế (`world.py:644-645`); đồng nhất `assign−blocked−offers = 0` **chính xác** ⇒ đếm đúng từng lượt. (b) 84,2% đơn từng có ≥2 ứng viên đồng thời chỉ được chào ≤1 người. (c) shortlist hex: 14,4% (≤29,4 đơn/ngày) — **hội tụ với sweep 12-seed trong config: −37 đơn/ngày ở k=8, bão hoà ở k≈8** | Hai khuyết tật cùng cường độ ở A và B (0,696 vs 0,702 · 14,4% vs 14,1%) ⇒ **cấm dùng để giải thích Δ**. "Offer một lần rồi chết" và "xếp hạng euclid T-045c" đã bị rc-01 bác đúng (hàng đợi retry mỗi 5s; cost = ETA + Hungarian từ UPDATE-080) |
| **H4** VISIBILITY | **ĐỔ với tư cách lời giải thích — nhưng xác nhận BA kẽ đo thật** | Hai đường đo độc lập khớp: state-sampling +674,6′ vs bộ đếm +688,8′ (lệch 2,1%); probe không dùng segment; cổng nhiễu-loạn trùng 7/7 số | Kẽ thật: (a) `idle_min` thừa **3,8%** (`world.py:1140` cộng 2,0′ **trước** `timeout(2.0)` ở 1144); (b) **sổ đội hở +3,41%** — chặng đi trạm nằm trong **CẢ** `empty_min` (`world.py:1248`) **và** `charge_min` (`world.py:1288,1277`); (c) cấp artifact: bộ metric A/B (`parallel.py:194-220`) không xuất sổ thời gian đội / `orders_total` / `unserved_breakdown` |

---

## 4. PHÂN LOẠI CUỐI theo protocol repo

**`MODEL GAP` (chi phối, ĐÃ CHỨNG MINH — không cần seed) + `BUG` ×4 (hai cái đặt trần & đối xứng hai
arm; hai cái MỚI phát hiện trong lần soi này) + `VISIBILITY GAP` ×3 tầng. `H1` = phase offset cấu trúc,
KHÔNG phải calibration gap. PHÂN BỔ ĐỊNH LƯỢNG cho từng thành phần = `UNRESOLVED`.**

### Tuyên bố root cause (một đoạn)

> Thời gian mà `station_choice` giải phóng không thể thành đơn vì **cung rảnh của sim bị giam trong cực
> đại địa phương của một trường niềm tin TĨNH lấy từ config, cách mọi ô nhiều đơn chết 3,40–4,73 km**,
> trong khi luật đứng-chỗ chỉ cho tài xế **nhìn 0,74 km** (`world.py:1165`) và chỉ **đi lên dốc nghiêm
> ngặt** (`behavior.py:217`), với bước "nới bán kính khi sốt ruột" **vô hiệu vì ring 3 = 1,11 km vượt
> ngoài tầm nhìn niềm tin** (`behavior.py:205,213` vs `world.py:1165`). Vì vậy phút rảnh thêm phân bổ
> **y như hình học idle sẵn có** (50,5% Δidle rơi đúng vào hai ô đã giữ 56,6% idle nền) chứ không di
> cư về phía cầu. Cộng thêm: thời điểm giải phóng bị lệch pha **theo vật lý** với giờ đơn chết (pin
> chưa thể cạn trước 8h ⇒ 06-08h nhận 5,8% thời gian nhưng chứa 59,1% đơn chết), và thế giới **được cố ý
> làm dư cung** (đội 74→90 để kéo `served_rate` lên 0,797 — `configs/pilot_dongda.yaml:222-228`) nên năng
> suất biên của một phút idle ở nền vốn đã ≈ 0. Hai khuyết tật dispatcher (`BUG-DISPATCH-SHORTLIST` và
> `COOLDOWN-SAU-KHI-GAN`) là **thật** và **đặt trần** kho đơn chết ở ~204 đơn/ngày, nhưng **đối xứng
> giữa hai arm** nên **không** sinh ra Δ của kênh — cấm dùng chúng để giải thích payout −33đ.

### "Thiết kế sim có kém không?" — trả lời thẳng, **ba loại khác nhau, cấm gộp**

**(A) KHÔNG kém — thuộc tính world được chọn CHỦ Ý, có văn bản:**
- Cầu **ngoại sinh hoàn toàn**, không co giãn theo cung/chờ (`demand.py:90-171`) ⇒ cung rảnh thêm chỉ có
  **một** đường thành tiền: vớt đơn EXPIRED. Đây là `REVIEW-092-4` **đang DEFERRED** (`TODO.md:36`) — đã
  biết, đã ghi.
- Eligibility = **chỉ** `state == IDLE` (`world.py:628`) ⇒ 152–235′ chảy vào `rest` là **không thể vớt
  đơn theo thiết kế**. Lựa chọn mô hình, không phải bug.
- Đội 90 xe = **đòn bẩy calibration** để đạt `served_rate` 0,797, tự nhận `trips/driver ≈ 10` là giới hạn
  cơ cấu một-quận (D-SIM-01 deferred). Dư cung là **giá phải trả có ý thức**.

**(B) KÉM THẬT — bốn khuyết tật, hai cái MỚI từ lần soi này:**

| # | Khuyết tật | Trạng thái | Số / evidence |
| --- | --- | --- | --- |
| B1 | **`BUG-DISPATCH-SHORTLIST`** — shortlist hex k=6 (2,22 km, phủ 64,6% lõi) hẹp hơn ràng buộc thật ETA-11′ (3,14 km, phủ 88,9%); loại **âm thầm**, không log | Đã ghi hồ sơ, **chưa sửa**; **nay có HAI số hội tụ** | ≤29,4 đơn/ngày (probe n=5, cận trên) ↔ **−37 đơn/ngày** (sweep 12 seed, `configs/pilot_dongda.yaml:126-133`), **bão hoà ở k≈8**. Chặn bởi Q-07: k=7 làm lệch `accept_base` P7 −0,053 > dung sai 5pp |
| B2 | **`COOLDOWN-SAU-KHI-GAN`** — cổng cooldown cặp được kiểm **SAU** phép gán và khi chặn thì `continue`: đơn **mất trọn tick**, không ai khác được chào thay, **không log** | **MỚI** (rc-03) | 2.595/3.723 slot gán/ngày (**69,6%**) bị nuốt; 23,26% đơn chết bị chạm, mỗi đơn mất ~2,5′ đời. **Hai khuyết tật ghép:** thứ tự (lọc sau khi gán, không gán lại) **+** im lặng. Cooldown 10′ ≥ `patience_max` 10′ ⇒ một lần từ chối là **vĩnh viễn** |
| B3 | **Bước sốt-ruột cuối cùng là NO-OP** — `consider_relocate` nới ring lên 3 (1,11 km) nhưng `_actor_demand_hint` chỉ dựng niềm tin trong `grid_disk(cell, 2)` (0,74 km) ⇒ ô ring 3 luôn giá trị 0, **không bao giờ được chọn** | **MỚI (lần soi này)** | `world.py:1165` vs `behavior.py:205,213`, config `idle_impatience_max_steps: 2`. Docstring `behavior.py:191-197` hứa *"rỗi lâu ⇒ đi XA HƠN"* — **cơ chế đó không thi hành được**. Đúng họ lỗi "cờ config không thực sự được dùng" trong checklist CLAUDE.md §4b |
| B4 | **Sổ thời gian đội KHÔNG KÍN (+3,41%)** — chặng đi trạm cộng vào **cả** `empty_min` **và** `charge_min` | **MỚI (rc-03, tôi xác nhận code)** | `world.py:1248` + `world.py:1288`/`1277`. Cộng kẽ `idle_min` thừa 3,8% (`world.py:1140` trước `1144`) giải thích ~86% độ hở. ⇒ **con số tiêu đề "−698′ chết ở trạm" không thuần là xếp hàng** |
| B5 | **Núm dashboard nối vào khoá config CHẾT** — slider *"Bán kính tìm tài xế (rings res9)"* ghi `dispatcher.candidate_ring_k`, nhưng dispatcher **chỉ đọc `candidate_ring_k_max`** | **MỚI (lần soi này)** | `dashboard.py:129-131` + `dashboard_defaults.py:20` vs `dispatcher.py:80` (grep `src/`: không nơi nào đọc khoá không-`_max`). Ai thử "nới bán kính" bằng dashboard sẽ kết luận SAI rằng bán kính không quan trọng |

**(C) OBJECTIVE THIẾU VẾ — `D-E4-06(b)` KHÔNG bị bác, nhưng bị HẠ CẤP xuống đòn bẩy thứ cấp.**
`DEFERRED.md:123` giả thuyết *"objective thiếu vế vị trí: kênh argmin(đường+queue+pin) bỏ qua tài xế
ĐỨNG ĐÂU SAU KHI ĐỔI so với cầu"*. Đo được: Δidle phân bổ **gần y hệt** hình học idle nền (50,5% vs
56,6% vào cùng hai ô bẫy) ⇒ kênh chọn trạm **không quyết định** nơi tài xế kết thúc; **luật leo dốc niềm
tin quyết định**. Nhưng vì leo dốc là **địa phương**, **điểm khởi đầu vẫn quan trọng** — một objective
có vế vị trí có thể đặt tài xế vào lưu vực (basin) của ô đỉnh cầu thay vì lưu vực bẫy. ⇒ giả thuyết
**còn sống, kiểm được**, nhưng phải kiểm **SAU** khi mở bẫy (§6.4d), không thì đo trong nhiễu.
`T-045c` (`TODO.md:39`, "đơn bỏ oan chưa đo lại") **nay đã có số**: xem B1.
`REVIEW-092-4` (cầu ngoại sinh) là gốc của việc "cung rảnh chỉ thành tiền qua đường vớt đơn chết" —
thuộc loại (A), deferred.

---

## 5. HỆ QUẢ CHÍNH SÁCH ĐO LƯỜNG — điều quan trọng nhất cho Cường

Trong world hiện tại, **cổng 1a của ĐA-08 (payout) là bất khả thắng về mặt cấu trúc cho bất kỳ kênh nào
chỉ giải phóng thời gian tài xế**:

- Chuyển đổi **hoàn hảo** 698′ đáng 24–52 đơn/ngày = **+6.100…14.700đ/tài xế** (rc-02 §3.3, §3.5) — tức
  bằng **1,0–2,4 lần TOÀN BỘ** kênh vị trí. Nghĩa là n=100 **có đủ power** để thấy nếu nó xảy ra.
- Nhưng chuyển đổi **thực tế đo được** là **3–7%** (+1,69 đơn), **nằm DƯỚI** độ phân giải ±3,55–4,00
  đơn/ngày của phép đo tiền ở n=100 ⇒ *"payout −33đ ns"* **không** chứng minh "chuyển đổi = 0", nó chỉ
  chứng minh "chuyển đổi nhỏ hơn ~4 đơn/ngày".
- Lý do cấu trúc: 33,6% thời gian online đã là idle; trung vị khoảng cách đơn-chết → người rảnh gần nhất
  **2,575 km** (vượt cả 2,22 km và ETA 11′). **Phút rảnh thứ 143 và thứ 151 có cùng giá trị biên: ~0.**

⇒ **Khuyến nghị chấm điểm:** kênh phía-cung phải được chấm bằng **metric thời gian/hàng đợi** (đã SIG:
`swap_wait −3,6′`, `charge_p90 −39′`, `station_hhi −0,056`) **cộng** một cổng "không gây hại tiền", chứ
không phải cổng "phải tăng tiền" — cho tới khi world có **cầu co giãn** (`REVIEW-092-4`) hoặc **đội xe
được calibrate lại**. Đây đúng là điều kiện reopen **(c)** đã ghi trong `DEFERRED.md:123` (*"spec ĐA-08
có amendment Cường duyệt"*) — và **§4/§5 ở đây là căn cứ để mở nó**.

---

## 6. Đề xuất phép đo / fix — **CÓ THỨ TỰ**, ghi rõ *cái nào PHÂN BIỆT thêm* vs *cái nào SỬA được gì*

### 6.1 — TRƯỚC MỌI THỨ: làm rc-03 tái tạo được (VISIBILITY; không đổi hành vi; ~1 cycle)
*Sửa được:* độ tin cậy của toàn hồ sơ. *Phân biệt:* không.
- Commit `probe_idle_overlap.py` → `research/audit/2026-08-06-root-cause-idle/rc-03-probe-script.py`
  (đường dẫn rc-03 **đã trích nhưng không tồn tại**) + artifact thô hoặc lệnh tái tạo.
- Thêm **độ tán theo seed** cho mọi tỉ lệ cơ chế; chạy lại **n=30** để đặt CI cho 53,9 / 14,4 / 31,7 / 69,6%.
- Sửa **B4** (chặng đi trạm hết đếm hai lần) + **kẽ `idle_min` cộng-trước-timeout**, rồi **đo lại −698/−872′**.
  ⚠ Bắt buộc: đây là sửa **thước đo**, phải chứng minh **không đổi hành vi** (fingerprint exact-repeat).
- Xuất sổ thời gian đội + `orders_total` + `unserved_breakdown` ra bộ metric A/B (`parallel.py:194-220`).

### 6.2 — PHÂN BIỆT #1 (rẻ nhất, giải quyết đúng chỗ rc-03 quy sai): cooldown có thật làm mất đơn không?
*Phân biệt:* tách "cổng cooldown nuốt một cơ hội THẬT" khỏi "dù sao cũng không có ai khác".
Đo: tại mỗi tick bị cooldown chặn, **có ứng viên hợp pháp KHÁC đang rảnh và chưa bị gán đơn nào trong
tick đó không?** Nếu tỉ lệ đó thấp ⇒ **ceiling +9.100…10.600đ của rc-03 §8 phải xoá**. Nếu cao ⇒ B2 là
fix rẻ nhất toàn repo (không nới bán kính ⇒ **không phá `accept_base`**, không chạm Q-07).

### 6.3 — PHÂN BIỆT #2 (0 seed, chạy trong phút): bản đồ LƯU VỰC niềm tin
*Phân biệt:* chứng minh/giết dứt điểm claim "bẫy" mà **không cần sim**.
Với 85 ô lõi × 19 giờ: xây đồ thị "leo dốc" (từ ô X, ô nào được chọn theo đúng luật `behavior.py:210-229`
với bar 1,25 và 1,05), tìm **các điểm hút (attractor)** và **kích thước lưu vực** của từng cái; in bảng
`(attractor, cầu kỳ vọng, khoảng cách tới 5 ô nhiều đơn chết nhất, % ô lõi thuộc lưu vực)`. Đây là bằng
chứng **tất định**, không seed, cho toàn bộ §2 — và nó cũng nói ngay **fix nào sẽ đủ**.

### 6.4 — FIX, **một cờ một lần**, n≥30, đo lại `expired` + `payout` + `accept_base`
Thứ tự theo *(rẻ & sạch) → (đắt & vướng spec)*:

| | Fix | Vì sao đứng ở vị trí này | Rủi ro |
| --- | --- | --- | --- |
| **a** | **B3**: nới cửa sổ niềm tin `_actor_demand_hint` từ `grid_disk(cell, 2)` lên đúng ring mà `consider_relocate` dùng (3) | Sửa một **no-op đã chứng minh**; cơ chế "rỗi lâu ⇒ đi xa hơn" mới thật sự bật. **Không** đụng dispatcher, **không** đụng bán kính ⇒ không chạm Q-07 | Có thể **tăng dồn đàn** (đi xa hơn nhưng vẫn lên dốc, vẫn không có vế cạnh tranh) ⇒ phải đo `supply_cell_hhi` và idle của hai ô bẫy, **không chỉ** payout |
| **b** | **B2**: lọc cặp trong cooldown **RA KHỎI ma trận cost TRƯỚC** `linear_sum_assignment` (hoặc gán lại sau khi loại) **+ log event** cho mỗi lượt bị chặn | Fix đúng chỗ, không nới bán kính ⇒ **không phá realism**. Chấm dứt "cú loại im lặng" (họ lỗi N5 repo đã trả giá) | Cost matrix động theo `offer_history` ⇒ phải kiểm CRN/exact-repeat cẩn thận |
| **c** | **B5**: nối slider dashboard vào `candidate_ring_k_max` **hoặc** xoá slider | Núm đang **lừa người xem**. Sửa 1 dòng | — |
| **d** | **B1**: shortlist = quả cầu ETA thật thay vì hex k. **Chỉ chạy chế độ nghiên cứu, KHÔNG bật default** | Bị chặn bởi **Q-07** (k=7 → `accept_base` P7 −0,053 > dung sai 5pp, `test_sim_realism.py`). Sweep 12-seed đã có: cứu −37 đơn/ngày, **bão hoà ở k≈8** ⇒ biết trước ceiling, biết trước giá | Cần Cường quyết Q-07: *ghép đơn đúng* hay *trung thành archetype* |
| **e** | **D-E4-06(b)**: điểm trạm = thời gian **+ giá trị vị trí sau đổi**, nối S4/positioning | Chỉ có nghĩa **SAU** (a)/(b): với bẫy còn nguyên, "giá trị vị trí" bị bẫy chi phối. Vì leo dốc là địa phương, **điểm khởi đầu có đòn bẩy** ⇒ giả thuyết còn sống | Đo lại như **kênh mới** (nguyên văn điều kiện reopen (b)) |

### 6.5 — QUYẾT ĐỊNH CỦA CƯỜNG (không phải việc của agent)
1. **Amendment ĐA-08** cho kênh phía-cung: chấm bằng metric thời gian + cổng không-gây-hại, thay vì cổng
   payout (căn cứ §5; đúng điều kiện reopen (c) của `D-E4-06`).
2. **Q-07**: ghép đơn đúng vs trung thành archetype (chặn B1).
3. **`REVIEW-092-4`** (cầu co giãn) / **D-SIM-01** (mở rộng zone) / cỡ đội: chừng nào world còn cố ý dư
   cung để đạt `served_rate`, mọi kênh giải phóng thời gian sẽ **luôn** cho payout ns. Đây là gốc, không
   phải kênh nào cả.

---

## 7. CÒN `UNRESOLVED` — nói rõ thiếu gì

1. **Phân bổ định lượng cho từng thành phần.** Ba nhóm phân hoạch kho đơn chết (53,9 / 14,4 / 31,7%) là
   **cận trên / cận trên / cận dưới** vì lấy mẫu 1′ trong khi tick là 5s, và **chưa có CI theo seed**.
   "Sửa X thì vớt được bao nhiêu" là **phản thực chưa chạy** (trừ bán kính — đã có sweep 12 seed).
2. **Ceiling tiền của B2 (cooldown)**: **BỊ RÚT** khỏi hồ sơ cho tới khi §6.2 đo xong (§1.6).
3. **Δ kết quả (payout/đơn) của kênh**: nguồn có hiệu lực **duy nhất** vẫn là `e01-station-100.json`
   (n=100, cửa sổ 1000s). n=5 của rc-03 cho **dấu ngược** ⇒ cấm trích.
4. **Δonline = −208,7′ (n=5)** — tài xế online **ít hơn** ở arm B, nhưng `work_span_p50` ở n=100 lại
   **+7,99′**. Hai dấu **không khớp**; chưa truy. Nếu Δonline thật là âm thì một phần thời gian giải
   phóng **biến mất khỏi thị trường** thay vì chảy vào idle — chưa loại trừ.
5. **~200′ độ hở sổ còn lại** sau khi trừ hai kẽ đã biết (§1.4).
6. **Trộn ba cửa sổ seed vẫn còn hiệu lực**: −698′/+520′ là **n=30 cửa sổ 7000s, cấp DOCS** (không có
   artifact, `UPDATE-159:16-21`); +235′ rest là **n=100 cửa sổ 1000s**; rc-03 là **n=5 cửa sổ 1000s**
   (−871,9 / +688,8 / +152,5). **Cùng chiều, khác độ lớn — không được cộng vào một sổ.**
7. **Chưa kiểm:** vai trò của `home_cell` và của hình học `_relocate_to_core` (`world.py:805-811,856-857`)
   trong việc bơm người vào lưu vực bẫy — §6.3 sẽ trả lời.

---

## 8. ĐÍNH CHÍNH phải đẩy về các artifact trước

| Artifact | Chỗ sai | Đính chính |
| --- | --- | --- |
| `rc-03` §2 + §6 H2 | *"cell trạm ngoài lõi ⇒ bị ép deadhead về lõi"* làm cơ chế cho việc vế cell-trạm đổ | **9/11 ô trạm TRONG LÕI** ⇒ cơ chế đó không chạy cho phần lớn trường hợp. Cơ chế đúng: sau swap tài xế IDLE **trong lõi** rồi **leo dốc niềm tin đi khỏi trạm**; thời gian di chuyển vào `empty_min` (`world.py:1131`) nên không hiện ra ở ô trạm |
| `rc-03` §8 | gán 38,8 đơn/ngày + 9.100–10.600đ cho `bug_2_cooldown` | 38,8 là nhóm 3a — **không phân biệt** cooldown / cạnh tranh Hungarian / artifact lấy mẫu. Số riêng cho cooldown là 23,26% đơn **bị chạm**, mất ~2,5′/đơn. **Rút ceiling** tới khi §6.2 đo |
| `rc-03` §7 `cai_gi_van_UNRESOLVED` | *"muốn số thật phải chạy run đối chứng có sửa … chưa chạy"* | Phản thực **bán kính đã chạy**: `configs/pilot_dongda.yaml:126-133`, 12 seed, `233 → 211 → 196 → 195` (k = 6/7/8/12) ⇒ **−37 đơn/ngày, bão hoà ở k≈8** |
| `rc-03` §10 | trỏ tới `rc-03-probe-script.py` trong repo | **File không tồn tại** ⇒ hồ sơ hiện **không tái tạo được**. Xem §6.1 |
| `rc-03` §3 | dùng Pearson 0,0005 làm luận điểm chính | Số mỏng (24 điểm, hai giờ ngoại lai; giờ 18 có 31,2 đơn chết mà Δidle **+50,6**). Dùng phát biểu tỉ trọng 5,8% vs 59,1% |
| `rc-01` evidence #4 | *"offer_history ghi TRƯỚC khi xét, world.py:646"* | Kiểm ở **644**, ghi ở **646** (sau). Kết luận (SOC-skip cũng nạp cooldown) **vẫn đúng** vì 646 chạy trước nhánh SOC ở 654 |
| `rc-02` §3.1 | *"−698′ về bản chất là GIẢM XẾP HÀNG"* | Không định danh được: `charge_min` **bao gồm chặng đi trạm** (`world.py:1288`), nên Δcharge trộn Δchờ và Δđi-đường. Giữ kiểm-mạch-lạc, bỏ kết luận |
| `rc-02` §3.2.B | suy `Δoccupied = 59,2′` bằng phép trừ (giả định sổ kín, Δonline≈0) | **SAI ở cửa sổ 1000s**: đo được Δoccupied **−65,1′**, Δonline **−208,7′**, sổ hở **+3,41%**. Không dùng lại phép trừ này |

---

## 9. Nguồn · tái tạo · nhãn

**Bằng chứng CẤP CODE** (đọc trực tiếp, lần soi này): `world.py:628,636-646,856-857,1131,1140,1144,
1146-1175,1248,1277,1288` · `dispatcher.py:80,94-134` · `behavior.py:191-197,199-229,234-238` ·
`demand.py:90-171` · `dashboard.py:129-131` · `dashboard_defaults.py:20` ·
`configs/pilot_dongda.yaml:25,120,126-133,142,147,153-155,205-207,222-228`.

**Bằng chứng HÌNH HỌC TĨNH** (đo lần này, **0 RNG, không seed**, tái tạo bằng `build_grid` +
`expected_demand_field` + `h3.cell_to_latlng` + `haversine_km`): lõi 85 ô · span tối đa 5,35 km · trung
vị cặp 1,70 km · `grid_disk(k=6)` phủ 64,6% lõi (min 18,8%) · 2,22 km phủ 65,0% · 3,14 km phủ 88,9% ·
ring 1/2/3 = 0,37 / 0,74 / 1,11 km · 9/11 ô trạm trong lõi · hạng cầu và tính cực-đại-địa-phương của
`953`/`bb3`/`c0b`/`c03` · khoảng cách bẫy→đơn chết 3,40–4,73 km · `953↔bb3` 0,98 km.

**Bằng chứng CẤP SIM**: `rc-03` (**n=5**, seeds 1000–1004, cổng nhiễu-loạn xanh — **CƠ CHẾ, không phải
thống kê**) · `e01-station-100.json` (**n=100**, cửa sổ 1000s — **nguồn duy nhất có hiệu lực cho Δ kết
quả**) · `oracle-100.json` (thước quy đổi 252–284đ/tài xế cho mỗi +1 đơn đội, 3 nguồn độc lập) ·
`UPDATE-159:16-21` (**cấp DOCS**, n=30 cửa sổ 7000s, **không có artifact**).

**Nhãn:** toàn bộ số là **MOCK/SIM**, không phải dữ liệu GSM thật. Mọi ceiling tiền là **ESTIMATE/CEILING**,
không phải dự báo. Cỡ mẫu và cửa sổ seed ghi kèm từng số; **cấm cộng ba cửa sổ**.

**Visual review gate:** `NOT_APPLICABLE` — đây là audit chỉ-đọc, không đổi code/sim/UI, không sinh output
mới cho stakeholder ngoài văn bản này. (Nếu thi hành §6.4 thì gate **bắt buộc** vì đổi dynamics.)

**Adversarial self-review của chính RC-04 — cái tôi CHƯA loại trừ:**
- Tôi **chưa chạy** sim lần nào. Toàn bộ đóng góp mới của tôi là **hình học tĩnh + đọc code**; nó chứng
  minh *tài xế rảnh KHÔNG THỂ tới chỗ đơn chết*, nhưng **không** chứng minh *nếu tới được thì sẽ vớt được
  bao nhiêu*. Ràng buộc thứ hai (cạnh tranh Hungarian, `decide_accept`, SOC) chưa được cân.
- Tôi kết luận "bẫy" từ **cực đại địa phương + tầm nhìn 0,74 km + đi lên dốc**. Tôi **chưa liệt kê hết
  attractor** và chưa đo **kích thước lưu vực** ⇒ có thể còn attractor tốt (gần cầu) mà phần lớn tài xế
  thực ra rơi vào. §6.3 là phép đo giết được claim của tôi — **phải chạy trước khi trích §2 ra ngoài**.
- Ba tỉ lệ cơ chế của rc-03 tôi **giữ lại mà không có CI**. Tôi đã đánh dấu chúng là cận trên/cận dưới,
  nhưng nếu §6.1 (n=30) cho tán lớn thì phần "14,4% chết thuần vì shortlist" có thể trôi đáng kể — dù
  sweep 12-seed trong config **độc lập chống lưng** cho khoảng 30–37 đơn/ngày.
- Claim **THUẬN LỢI** tôi tự soi kỹ nhất: *"cổng cooldown nuốt 69,6% phép gán"* nghe như đại thảm hoạ.
  Tôi **hạ nhiệt** nó: 2.595 slot chỉ là **366,6 CẶP khác nhau**, mỗi cặp lặp ~7 lần, và thiệt hại thật
  là **~2,5′ đời đơn cho 23% đơn chết** — không phải "mất 69,6% năng lực ghép đơn". Ai trích số 69,6%
  mà không kèm câu này là **đang báo sai cho Cường**.
