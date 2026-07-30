# Spec — Mô hình hoá lại bài toán Advisor (v2): cá nhân + toàn cục

Ngày: 2026-07-27 · Trạng thái: **⚠ ĐÃ DUYỆT 2026-07-27** (Cường: *"oke duyệt hết"*) **+ amendment Q-11/Q-12 (2026-07-28)** — xem §5 AMENDMENT bên dưới.
Thay thế phần objective của `specs/advisor-optimization-layer-a.md` §2.1 (giữ nguyên phần còn lại).

## 0. Vì sao phải viết lại — bằng chứng, không phải cảm tính

| Bằng chứng | Số đo |
|---|---|
| Advisor nói gì với 90 tài xế | **1135/1152 lời khuyên (98,5%) là "ONLINE"** |
| Khi tài xế nghe theo | 414 lần bỏ *chờ* · **28 lần bỏ đi đổi pin** · **19 lần bỏ kết ca** · 6 lần bỏ nghỉ |
| Kết quả cá nhân | lỗ 3/5 seed ([hồ sơ 06](../research/audit/2026-07-27-current-state/06-why-advice-loses-money.md)) |
| Kết quả toàn đội | ~36% percentile tăng · served_rate giảm 6/10 seed · đơn hết hạn +8/ngày ([hồ sơ 07](../research/audit/2026-07-27-current-state/07-fleetwide-advice-equilibrium.md)) |

**Nguyên nhân toán học** (`src/gsm_core/solvers/shift_dp.py`, nhánh Bellman):

```
V(ONLINE) = online_pay + V(next)     # online_pay > 0 LUÔN LUÔN
V(REST)   = 0.0        + V(next)     # KHÔNG có giá trị
V(SWAP)   = 0.0        + V(next)     # KHÔNG có giá trị
```

Chạy **không có chi phí**, nghỉ **không có giá trị** ⇒ nghiệm tối ưu tất yếu là *"chạy hết công
suất"*. Đó không phải lời khuyên — đó là điều tài xế đã tự làm, và họ làm **tốt hơn** vì bản năng
của họ có tính tới pin và mệt (behavior model có `fatigue_threshold_min`, SOC gate; DP thì không).

**Sai tầng bài toán**: hiện đặt là single-agent MDP với môi trường **ngoại sinh cố định**; sim thực
tế là multi-agent với môi trường **nội sinh**. `shift_dp.py` tự thú model gap này ở docstring.

## 1. Objective v2 — cá nhân

Ký hiệu: bucket `b`, hành động `a ∈ {ONLINE, REST, SWAP, END}`, state `s = (b, soc, points, rests_left, cell)`.

```
V(s) = max_a [ R(s,a) − C(s,a) + γ·E[V(s')] ]
```

### 1.1 R — thu nhập (đã có, giữ)
`R(ONLINE) = E[trips]·payout_per_trip`; `R(END) = bonus_at(points)` (đã gate eligibility ở S2-3).

### 1.2 C — CHI PHÍ (mới, 5 số hạng)

| # | Số hạng | Công thức đề xuất | Nguồn/nhãn | Vì sao cần |
|---|---|---|---|---|
| **C1** | Chi phí vận hành | `c_km · km_kỳ_vọng(b)` — điện + hao mòn | **ASSUMPTION** (chờ GSM: chi phí điện/km, khấu hao). Fallback: suy từ `vehicle.pct_per_km` + giá điện công bố | Không có nó thì mọi km đều "miễn phí" ⇒ luôn chạy |
| ~~**C2**~~ | ~~Giá trị nghỉ~~ **HUỶ 2026-07-30** | ~~`−v_rest(fatigue)`~~ | 🚫 **KHÔNG BAO GIỜ IMPLEMENT** | Xem §1.2b. Số hạng này định giá sức khoẻ bằng tiền — trái ranh giới đã chốt. **Nghỉ là RÀNG BUỘC, không phải số hạng của objective.** Thay thế: `C2′` |
| **C2′** | Chi phí cơ hội của **THỜI ĐIỂM** nghỉ | `−(payout_kỳ_vọng(giờ_nghỉ) − payout_kỳ_vọng(giờ_vắng_nhất))` — chỉ định giá việc nghỉ **SAI GIỜ**, không định giá việc nghỉ | Tính từ `demand_by_hour` (belief cá nhân, đã có) — **0 tham số nhân quả mới** | Đây là đường DUY NHẤT làm lời khuyên nghỉ có Δ tiền đo được **mà không tạo tỷ giá sức-khoẻ↔tiền**: lượng nghỉ giữ nguyên (ràng buộc cứng `rest_min_per_4h`), chỉ thời điểm là biến |
| **C3** | Rủi ro | Thay `E[payout]` bằng **CVaR_α** (α=0.2) hoặc `E − λ·σ` | Thiết kế; λ calibrate bằng sweep | Tài xế thật **ngại rủi ro**: thà chắc 300k hơn 50% cơ hội 500k. E[·] thuần bỏ qua điều này |
| **C4** | Chi phí cơ hội vị trí | `−(V_pos(cell_sau) − V_pos(cell_trước))` — giá trị vị thế | Tính từ `demand_field` + supply (xem §2) | Đây là cơ chế đã đo được ở hồ sơ 06: nhận cuốc → trôi khỏi vùng cầu → mất vị thế |
| **C5** | Chi phí SOC phi tuyến | phạt tăng nhanh khi `soc < soc_reserve` | Sim đã có `swap_soc_threshold_pct` | Giải thích trực tiếp "28 lần bỏ đi đổi pin" |

### 1.2b 🚫 Vì sao C2 bị HUỶ, và C2′ thay nó (chốt 2026-07-30)

Quyết định của Cường: *"okey, chấp nhận câu trả lời"* trên phán quyết
[`tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md`](../tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md).
Đây là **quyết định cuối**, không mở lại bằng dữ liệu mới — nó là quyết định nguyên tắc, không phải
quyết định thực nghiệm.

**Lập luận toán học, một dòng:** mọi cơ chế cho mệt một hậu quả năng lực đều tạo `payout = f(F)`,
tức tồn tại `∂payout/∂F` — **một tỷ giá sức-khoẻ↔tiền**. Viết tỷ giá đó vào *world* (mệt làm chậm
tài xế) thay vì vào *objective* (`−v_rest`) **không xoá tỷ giá; nó chỉ xoá NHÃN của tỷ giá.** Ranh
giới đã chốt của dự án là *"sức khoẻ tài xế KHÔNG phải biến để tối ưu"* ⇒ cả hai cách đều bị cấm.

**C2 cũng không cứu được thứ nó được viện dẫn để cứu.** Lời khuyên nghỉ duy nhất sản phẩm được phép
nói là **HOÃN** (`rest_window` đổi *thời điểm*, không đổi *lượng*). Dưới đúng mô hình mệt-có-hậu-quả,
hoãn nghỉ ⇒ lái dài hơn trước khi hồi phục ⇒ liều cao hơn ⇒ Δ của `rest_window` **âm hơn**, không
dương hơn. Thứ C2 re-sign được là lời khuyên *"nghỉ THÊM"* — mà không kênh nào phát, và chính khung
"nghỉ = ràng buộc" cấm định giá.

**Không đủ khả năng làm đúng, kể cả nếu muốn:** 0 dữ liệu mệt, 0 dữ liệu tai nạn tài xế trong toàn
repo. Proxy nhận dạng duy nhất từng được nêu — `driver_statistic_daily.count_cancel_not_relate_driver`
— là `rng.randint(0, cancelled)` (`src/gsm_core/mockgen/realdata.py:168`): **nhiễu thuần theo
construction**. Cần căn 5–11 tham số với 0 điểm dữ liệu ⇒ tiêu chí lựa chọn duy nhất còn lại là **dấu
của Δ**, đúng thứ `CLAUDE.md` §4b cấm. Liều "có nguồn" 240′ (Điều 64) áp dụng **ô tô kinh doanh vận
tải**; đoàn pilot là **bike 100%** ⇒ 240′ là ASSUMPTION, không phải nguồn.

**Bằng chứng đóng đinh, đo được:** lời khuyên nghỉ bị chặn ở đâu, `scripts/probe_rest_window_blockers.py`
(3 seed, `coverage=all`, `ladder=all`, 873 lần gọi):

| Chặn ở đâu | % | |
| --- | --- | --- |
| `soc_low` | 44,1% | ← LAN CAN SỨC KHOẺ |
| `fatigued` | 26,9% | ← LAN CAN SỨC KHOẺ |
| `window_past` | 17,8% | `D-SIM-10` |
| `no_window` | 10,3% | S7 cố ý không bịa vấn đề (idle median 16′ < ngưỡng 45′) |
| **NÓI** | **0,00%** | |

**Hai lan can sức khoẻ một mình chặn 71,0%** ⇒ trần trên của giá trị tiền mà kênh nghỉ có thể mang
lại là **≤29,0% số cơ hội** — và trần đó do **chính ranh giới đạo đức** dựng nên, không phải do bug.
Mô hình mệt chính xác đến đâu cũng không mở được 71% đó ra **mà không phá nguyên tắc**.

### Thay thế: khung ba lớp (chốt, thay §5b)

| Đại lượng | Vai trò trong objective | Cơ chế enforce | Có thật chưa? |
| --- | --- | --- | --- |
| **LƯỢNG nghỉ** | **RÀNG BUỘC CỨNG**, không phải số hạng | `rest_min_per_4h` trong `shift_dp` | ✅ **CÓ** (`src/gsm_core/solvers/shift_dp.py`) |
| | | `POLICY_LOCKED_KEYS` khoá `rest_defer_max_min` không cho sweep | ❌ **CHƯA CÓ — phải viết** |
| **THỜI ĐIỂM nghỉ** | **BIẾN** — định giá bằng `C2′` | `rest_window` = DEMAND-TIMING, trong bảng tiền, chịu cadence | ✅ CÓ (cadence) |
| | | …và chịu `coin_follows` | ✅ **CÓ từ 2026-07-30** (UPDATE-102, `D-M3-01` DONE-CODE — coin nối ở `should_defer_rest`, behavior-neutral 15/15 fingerprint IDENTICAL) |
| **MỆT (`fatigue`)** | **LATENT** — không ai đọc để tính tiền | ba lan can trong `should_defer_rest` (`soc_low`/`fatigued`/`defer_cap`) | ✅ **CÓ** — đo được chặn 71,0% |
| | | grep-test `test_no_fatigue_in_payout_path` | ❌ **CHƯA CÓ — phải viết** |
| | | guardrail tầng 5: `rest_min_total`, `veto_fired_n`, `max_continuous_drive_min` | ❌ **CHƯA CÓ — `D-M3-05`** |

> ⚠ **Đọc cột cuối trước khi tin bảng này.** Cập nhật 2026-07-30 (UPDATE-102): **3 tồn tại**
> (`rest_min_per_4h`, ba lan can, và nay **coin cho `rest_window`**). **Ba** cái còn lại
> (`POLICY_LOCKED_KEYS` · grep-test · guardrail tầng 5) là **việc phải làm**, không phải bảo đảm đang có.
> Bảng này được viết với cột trạng thái tường minh vì repo đã trả giá cho đúng họ lỗi *"code/spec tự
> quảng cáo một cơ chế không chạy"* (`D-R12`: nhánh `unsafe_while_moving` được quảng cáo trong khi
> `is_driving` không có đường nuôi từ client; và `topic_cooldown` chết ở UI vì `last_decided_min`
> không ai nuôi). ⇒ **`C2′` KHÔNG được đo trước khi 4 cơ chế còn lại có thật** — nếu đo trước, con
> số Δ sẽ được sinh ra trong một hệ không có chốt chặn nào ngăn nó bị đọc thành *"hoãn nghỉ có lợi"*.

**Bias phải khai báo trong mọi báo cáo dùng `C2′`:** sim **không có kênh tác hại nào** của việc hoãn
nghỉ (không tai nạn, không giảm chất lượng, không mệt qua đêm — `D-SIM-16`) ⇒ **mọi Δ dương của lời
khuyên hoãn nghỉ đều dương quá mức theo cấu trúc.** Lan can + guardrail, không con số, mới được quyết
định việc có hoãn hay không.

### 1.3 Mục tiêu phi tuyến cho tân binh
`tenure_days ≤ 90` có **bảo lãnh doanh thu sàn** (PROXY 350k/ngày). Hàm mục tiêu là **bậc thang**:
dưới sàn thì mọi đồng thêm bị bảo lãnh bù ⇒ giá trị biên ≈ 0; trên sàn mới có giá trị thật.
Solver hiện **không biết** điều này ⇒ khuyên tân binh y hệt tài xế lâu năm. Phải đưa `tenure_days`
và `guarantee_floor` vào view.

## 2. Objective toàn cục — multi-agent equilibrium

### 2.1 Vấn đề
Advisor tính λ(cell, hour) **ngoại sinh** từ config. Khi 90 tài xế cùng nghe, cung thay đổi nhưng
λ không đổi ⇒ advisor không bao giờ biết mình đang khuyên trùng nhau. Đây là *fallacy of composition*.

### 2.2 Đề xuất: best-response iteration (fictitious play) trên sim
```
λ⁰ = λ_config                                   # vòng 0: như hiện tại
lặp k = 1..K:
    advice_k = solve(λ^(k-1))                   # mọi tài xế
    supply_k = đo cung thực tế phát sinh        # từ traj/segments của run
    λ^k = λ_config ⊘ f(supply_k)                # cầu CÓ ĐIỀU KIỆN trên cung
tới khi ‖λ^k − λ^(k-1)‖ < ε  (hoặc dao động ⇒ báo KHÔNG hội tụ)
```
Câu hỏi nghiên cứu phải trả lời bằng số:
1. **Có điểm cân bằng không** — hội tụ hay dao động (nếu dao động: đó cũng là kết quả, và nó nói
   rằng advice đồng loạt vốn không ổn định).
2. **Price of anarchy**: so nghiệm phi tập trung với phân bổ tập trung (min-cost flow trên
   (cell, hour) — đây chính là chỗ **S4 `capacity_alloc`** đang chết được hồi sinh).
3. **Ngưỡng phủ**: quét `coverage.share` ∈ {10%, 25%, 50%, 100%} — rất có thể tồn tại ngưỡng mà
   lợi ích cá nhân chưa bị triệt tiêu.

> **⚠ Đính chính 2026-07-29 (ĐA-09, UPDATE-088):** cả ba câu hỏi trên **ĐÃ TRẢ LỜI BẰNG SỐ** —
> xem `research/simulation/multi-agent-equilibrium.md`: (1) cân bằng tồn tại & ≈ λ_config (γ=1 hội
> tụ 1 vòng); heatmap-residual (γ=0) KHÔNG hội tụ, tệ vĩnh viễn; (2) Price of anarchy: adherence
> thật lấy 51–73% mức tập trung; (3) phủ tăng đơn điệu không tự-triệt-tiêu, có bẫy free-rider
> 25–50%.

### 2.3 Cơ chế chống trùng lặp (đã có thiết kế, chưa code)
`specs/advisor-optimization-layer-a.md` §2.4 đã mô tả **capacity ledger**: đếm advice-outstanding
theo (trạm, bucket), advice thứ N+1 vào slot đầy thì DP tự chuyển; staggering ưu tiên SOC thấp +
jitter ±7 phút. **Chưa bao giờ được code.** Đây là điều kiện tiên quyết của §2.2.

> **⚠ Đính chính 2026-07-29 (UPDATE-083/084):** capacity ledger + **S4 `capacity_alloc`** (hồi
> sinh, `_standby_planner` batch Hungarian) **ĐÃ CODE**. Đo 30 seed × 4 thế giới (artifact `21-*`):
> kênh vị trí cứu hệ thống SIG (served +1,03đp, đơn chết −13,4/ngày, payout đội +212k/ngày) và
> **HHI GIẢM** (chống dồn cục thành công). Câu hỏi còn treo: veto km-rỗng (Q-10/Q-12, xem
> `tracking/DEFERRED.md` D-SIM-14 và `tracking/TODO.md` T-045a).

## 3. `MarketStateView` — mở kênh thông tin cung

> **⚠ Đính chính 2026-07-29 (T-045a b1/b2):** `MarketStateView` **ĐÃ IMPLEMENT** —
> `gsm_core/features/market_state.py` (b1, 9 test) + producer trong sim `Actor.enroute_cell` +
> `gsm_sim/market_state.py` (b2, 11 test) = **20 test**. Thiết kế dưới đây không còn là "chưa code".

Solver hiện **mù hoàn toàn về cung**. Thiết kế view mới, cấp cho S2/S4/S7:

| Trường | Nguồn trong sim | Nguồn ở data thật | Fallback khi absent |
|---|---|---|---|
| `supply_by_cell_hour` | `World.actors` (state=IDLE) | `public_driver_hex_tracking` (1,37M dòng — **bảng lớn nhất, đang dùng ít nhất**) | dùng λ ngoại sinh như hiện tại + hạ confidence |
| `sd_ratio` | supply ÷ `demand_field` | như trên | `None` → solver bỏ số hạng C4 |
| `open_orders_by_cell` | `World.open_orders` | KHÔNG có (13 bảng chỉ có đơn đã hoàn thành) | dùng `demand_field` + nhãn PROXY |
| `station_queue` | `Station.queue_len` + `batteries[]` | KHÔNG có | `None` → không khuyên SWAP tới trạm cụ thể |
| `congestion_r` | `congestion.r(cell,hour)` | ETA từ routing provider | 0 (không tắc) + nhãn |
| `env_forecast` | `EnvironmentContext` (mưa/nhiệt/sự kiện) | WeatherAPI (key đã có) | bỏ qua |

**Ràng buộc robust bắt buộc**: mỗi trường mang nhãn `available / degraded / absent`; solver phải
chạy được ở CẢ BA mức, và `confidence` của advice phải giảm theo mức degrade. Không có trường nào
được phép làm solver crash hay bịa số.

## 4. Thông tin GSM có thể cấp ở diện toàn cục (đề nghị tích hợp)

| # | Thông tin | Dùng để | Fallback nếu GSM không cấp | Rủi ro nếu sai |
|---|---|---|---|---|
| G1 | Mật độ tài xế online theo (hex, giờ) | mẫu số của mọi bài toán cân bằng; C4 | suy từ `public_driver_hex_tracking` (có sẵn, chưa khai thác) | khuyên dồn vào ô đã bão hoà |
| G2 | Hàng chờ trạm pin realtime | C5, chống dồn sạc | `None` → không khuyên trạm cụ thể | tài xế tới trạm rồi xếp hàng 40 phút |
| G3 | Đơn chưa được gán (open orders) | tín hiệu S/D thật thay vì λ ngoại sinh | `demand_field` PROXY | advice dựa trên cầu tưởng tượng |
| G4 | ETA/tốc độ trung bình theo khu | congestion thật | OSRM offline matrix (đã có) | ước sai thời gian ⇒ sai quỹ giờ |
| G5 | Surge/pricing state | biết khi nào cuốc đáng giá hơn | không có → dùng fare cơ bản | bỏ lỡ tín hiệu giá quan trọng nhất |
| G6 | Chính sách thưởng đang hiệu lực + version | S1/S5 tính đúng mốc | policy bundle mock versioned | khuyên theo chính sách đã hết hạn |

**Nguyên tắc**: hệ phải **hữu ích ngay cả khi CHỈ có 13 bảng hiện tại**. Mọi trường G1-G6 là
*nâng cấp*, không phải điều kiện sống.

## 5. Chỉ tiêu chấp nhận KÉP (ĐA-08) — thay tiêu chí hiện tại

> **AMENDMENT 2026-07-28** (Q-11 duyệt · Q-12 chốt (b) · định nghĩa per-archetype Cường uỷ
> quyền agent — *"tự quyết theo phương án tốt nhất cho 1 dự án tầm cỡ"*):
>
> **Tầng cá nhân đo bằng estimator KHÔNG BIAS** (`payout_mean_*` — BUG-EVAL-ARGMAX,
> UPDATE-085 §4; argmax chỉ là view chẩn đoán có nhãn), gồm HAI vế đồng thời:
> - **(1a) hiệu quả**: `payout_mean_all` (mọi tài xế được phủ) > 0, CI 95% loại 0, n≥30;
> - **(1b) no-harm guard công bằng**: KHÔNG archetype nào có Δ `payout_mean_{arch}` ÂM có ý
>   nghĩa (CI 95% hoàn toàn < 0) — báo cáo đủ P1..P7.
>
> Lý do chọn dạng này thay hai cực đoan: đòi TỪNG archetype dương-SIG thì subgroup không bao
> giờ đủ power (chặn mọi thứ một cách giả tạo); chỉ nhìn mean_all thì bỏ equity. Chuẩn
> efficiency-with-non-inferiority-per-subgroup là thông lệ thử nghiệm nghiêm túc. Kiểm chứng
> trên artifact 25 (n=100): B3w đạt cả 1a (+6.016 SIG) lẫn 1b (0/7 archetype bị hại; 5/7
> dương SIG). Veto 8/9 dùng bản (b): cơ chế được phép tốn km-rỗng/đổi-pin **nếu** chờ-đổi-pin
> không tăng SIG và tổng payout đội tăng SIG cùng lúc.
>
> **Cross-ref 2026-07-29:** estimator cohort không bias + placebo test + banner CORRECTED trên
> UPDATE-075/078/081/084 là nội dung của **UPDATE-086** (artifact 24), không chỉ UPDATE-085.

Một kênh advice chỉ được coi là "có giá trị" khi **đồng thời**:

| Tầng | Điều kiện | Đo thế nào |
|---|---|---|
| **Cá nhân** | (1a) `payout_mean_all` > 0 CI loại 0 **và** (1b) không archetype nào bị hại SIG — xem AMENDMENT | 30+ paired seed CRN, estimator cohort |
| **Hệ thống** | `served_rate` không giảm | `coverage: all`, 30 seed |
| **Khách hàng** | đơn hết hạn không tăng; thời gian chờ khách không tăng | `sim_metrics.customer_wait()` (**đã viết, chưa ai gọi**) |
| **Công bằng** | Gini payout không tăng | metric MỚI cần viết |
| **Tập trung** | HHI tải trạm và concentration cung theo ô không tăng | metric MỚI cần viết |

> **⚠ Đính chính 2026-07-29 (UPDATE-075):** ba dòng Khách hàng/Công bằng/Tập trung ở trên **đã
> viết VÀ được gọi** — bước 1 của §6 (đo trước, sửa sau) đã nối `customer_wait`, viết Gini/HHI,
> và bỏ ép `coverage="single"` trong `parallel.run_pair`.

Kênh nào vi phạm bất kỳ dòng nào ⇒ **không được bật**, kể cả khi số cá nhân đẹp.
CI chạy bộ chỉ tiêu này ở job nightly (khung đã có trong `.github/workflows/ci.yml`).

## 5b. 🚫 ~~CHẶN TRƯỚC BƯỚC 2–3: thước đo hiện KHÔNG đo được giá trị của nghỉ~~ — **HUỶ 2026-07-30**

> **ĐỌC TRƯỚC KHI HÀNH ĐỘNG THEO MỤC NÀY:** §5b **không còn chặn bước nào**. Điều kiện tiên quyết nó
> đặt ra (*"sim phải có hậu quả của việc không nghỉ"*) là **KHÔNG BAO GIỜ được thực hiện** — quyết
> định nguyên tắc, chốt 2026-07-30 (V-15). Phần mô tả bên dưới giữ lại vì **mô tả** vẫn đúng; phần
> **kết luận** của nó bị đảo. Lý do đầy đủ: §1.2b. Thay thế: `C2′` + khung BA LỚP.
> Quyết định gốc: `tracking/QUYET-DINH-2026-07-30-nam-diem.md`.

**Phát hiện 2026-07-27** ([hồ sơ 11](../research/audit/2026-07-27-current-state/11-sim-khong-the-cham-diem-loi-khuyen-nghi.md)):
trong sim, `fatigue` **chỉ khiến tài xế tự nghỉ** — nó **không** ảnh hưởng tới xác suất nhận, tốc
độ, huỷ, rating hay rủi ro. ⇒ **nghỉ mất tiền, không nghỉ không mất gì**.

Hệ quả trực tiếp cho spec này:

- Số hạng **C2 "giá trị nghỉ"** nếu đưa vào solver bây giờ sẽ làm solver khuyên nghỉ nhiều hơn, và
  chỉ tiêu kép §5 sẽ chấm **tệ hơn** — vì không tầng nào trong 5 tầng biết tính lợi ích của nghỉ.
- Bằng chứng định lượng: sửa đúng `bucket_min` (nghỉ bắt buộc 30′ → 120′ cho ca 10h) làm
  payout đi từ **−17.310đ xuống −24.960đ**.
- ⇒ **Sửa solver trước khi sửa sim = tối ưu hoá vào một cái thước hỏng.**

~~**Điều kiện tiên quyết mới**: sim phải có **hậu quả của việc không nghỉ**...~~

## 🚫 §5b BỊ HUỶ TOÀN BỘ — chốt 2026-07-30 (V-15)

Điều kiện tiên quyết ở trên **KHÔNG BAO GIỜ được thực hiện**. Lý do đầy đủ ở **§1.2b**; rút gọn:
mọi cơ chế "mệt có hậu quả" đều tạo `∂payout/∂F` — một tỷ giá sức-khoẻ↔tiền — và viết nó vào *world*
thay vì *objective* chỉ xoá **nhãn**, không xoá tỷ giá.

**Và lập luận định lượng của §5b ở trên là NON-SEQUITUR.** Bằng chứng nó viện dẫn — *"nghỉ bắt buộc
30′→120′ làm payout đi từ −17.310đ xuống −24.960đ ⇒ thước đo hỏng"* — không phân biệt được giả
thuyết nào: +90 phút nghỉ đổi −7.650đ ≈ **85đ/phút**, **thấp hơn** mọi giá phút-làm-việc đo được
trong sim (284–910đ/phút, MOCK). Đó là **dấu kỳ vọng của bất kỳ mô hình có chi phí cơ hội**, không
phải bằng chứng thước đo hỏng.

Câu *"nghỉ mất tiền, không nghỉ không mất gì"* ở đầu §5b **đúng về mô tả** và **vẫn giữ** — nhưng
kết luận rút ra từ nó phải đảo: đó **không** phải lỗi cần sửa bằng cách cho mệt hậu quả; đó là **hệ
quả tất yếu** của việc từ chối định giá sức khoẻ. Cái phải sửa là **phạm vi của lời khuyên nghỉ**
(chỉ hoãn *thời điểm*, không đổi *lượng*) và **cách định giá** (`C2′` = chi phí cơ hội của giờ), chứ
không phải mô hình mệt.

Thay thế chính thức: **khung ba lớp** ở §1.2b (LƯỢNG = ràng buộc · THỜI ĐIỂM = biến · MỆT = latent).

## 6. Thứ tự thực hiện đề nghị (sau khi duyệt)

1. **Đo trước, sửa sau**: nối `sim_metrics.customer_wait`/`supply_demand_density` vào guardrail +
   viết Gini/HHI/concentration + bỏ ép `coverage="single"` trong `parallel.run_pair`. Không sửa
   solver nào ở bước này — để có **baseline đo đúng**.
2. **C1 (chi phí vận hành/km) + C5 (SOC phi tuyến)** — hai số hạng dễ biện minh nhất, đo lại.
   *(Bản đầu của dòng này ghi nhầm "C2 (chi phí vận hành)"; theo bảng §1.2 thì **C1** mới là chi
   phí vận hành, **C2** là giá trị nghỉ. Sửa 2026-07-27 để không implement nhầm số hạng.)*
~~2b. [MỚI, CHẶN] Cơ chế mệt mỏi trong SIM~~ → 🚫 **HUỶ 2026-07-30** (§5b, §1.2b). Không còn là
   điều kiện chặn của bất cứ bước nào.
~~3. C2 (giá trị nghỉ)~~ → 🚫 **HUỶ 2026-07-30**. Thay bằng **`C2′` — chi phí cơ hội của THỜI ĐIỂM
   nghỉ** (§1.2b): 0 tham số nhân quả mới, không phụ thuộc bước nào, dùng `demand_by_hour` đã có.
   ⚠ Trước khi đo `C2′` phải xong **`D-M3-01`** (mẫu số adherence của `rest_window` hỏng —
   `decision_adherence` cắm cứng 1,0 theo cấu trúc) và **`D-M3-04`** (`planned_rest_hour` chưa
   TỪNG chạy trong A/B ⇒ kênh nói **0/873 lần** ⇒ chưa hề được đo lần nào). Đo `C2′` trước hai mục
   đó là đo một kênh chết bằng một cái thước hỏng.
4. C3 (rủi ro/CVaR) — đổi cách tổng hợp, đo lại.
5. `MarketStateView` + C4 (chi phí cơ hội vị trí) — cần state cung.
6. Capacity ledger + hồi sinh S4 → multi-agent equilibrium §2.2 (ĐA-09).

> **⚠ Trạng thái từng bước 2026-07-29:** **1 ✅ DONE** (UPDATE-075) · 2 = **KẾ TIẾP**, theo
> `tracking/PLAN-cycle-wx-2026-07-29.md` Phần B (C1 chi phí vận hành/km, thước đo đi TRƯỚC solver)
> · 2b **🚫 HUỶ 2026-07-30** · 3 (C2 giá trị nghỉ) **🚫 HUỶ**, thay bằng `C2′` chờ `D-M3-01`+`D-M3-04` · 4 (C3 rủi ro/CVaR) **chưa làm** · 5 ✅
> **DONE** (`MarketStateView` b1/b2) · 6 ✅ **DONE phần equilibrium** (capacity ledger + S4 hồi
> sinh + ĐA-09 §2.2, UPDATE-083/084/088); veto km-rỗng vẫn treo (Q-10/Q-12).

Mỗi bước: 30 seed CRN, `coverage: all`, chỉ tiêu kép §5, một UPDATE riêng.

## 7. Cái spec này CHƯA giải quyết (trung thực)

- **⚠ XUNG ĐỘT với quyết định cũ trong code (phát hiện 2026-07-27, phải xử lý ở bước 2–3):**
  `shift_dp.DEFAULT_PARAMS` có ghi rõ *"Objective = payout THUẦN (không phạt fatigue ảo) …
  **Fatigue-as-money bị bỏ (không bịa số §5)**"*. Tức việc thêm C1/C2 **mâu thuẫn trực tiếp** với
  một quyết định đã ghi trong code — quyết định đó đúng ở chỗ **không được bịa số**.

  **Cách hoà giải đề nghị** (không phá nguyên tắc cũ): mỗi số hạng chi phí vào code dưới dạng
  **tham số config mặc định = 0**, tức **hành vi mặc định KHÔNG đổi**; giá trị khác 0 phải mang
  nhãn `ASSUMPTION` + nguồn, và chỉ được bật sau khi **quét độ nhạy** cho thấy kết luận không đảo
  chiều trong dải hợp lý. Như vậy code có **dạng hàm đúng** (điều đang thiếu và gây ra −17.310đ)
  mà vẫn **không tuyên bố mức nào là thật**. Đây chính là ranh giới §7 dòng dưới.
- Tham số của C1/C2/C3 đều là **ASSUMPTION** cho tới khi GSM cấp số thật (chi phí điện/km, giá trị
  thời gian nghỉ, mức ngại rủi ro). Spec chỉ đảm bảo **dạng hàm** đúng, không đảm bảo **mức** đúng.
- Không giải bài toán "khách hàng công bằng" (ai được phục vụ trước) — ngoài scope advisor.
- Chưa bàn tới việc advisor có nên **khác nhau theo archetype** hay không (tân binh vs lão làng
  cần objective khác) — ghi nhận là câu hỏi mở.
