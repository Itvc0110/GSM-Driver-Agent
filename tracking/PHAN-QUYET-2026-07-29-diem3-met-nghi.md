# PHÁN QUYẾT — điểm 3 của Cường: có nên đưa HẬU QUẢ của mệt vào sim để định giá lời khuyên nghỉ?

Trạng thái: `WAITING-VERDICT` (mục giá trị ở §6 cần Cường). Ngày 2026-07-29.
Mọi số là **MOCK** (`configs/pilot_dongda.yaml`), không phải số thật GSM.

Câu hỏi gốc: *"Còn trong sim kiểm tra có thiết kế độ mệt của tài xế chưa? Brainstorm xem nên
giữ thiết kế về mệt, nghỉ của tài xế, lời khuyên advisor ra action nghỉ để làm 1 features để
tính metric tiền không? kiểm tra xem liệu có thực sự đủ khả năng thiết kế môi trường phức tạp
đến thế không? phần này phải engineer kĩ, brainstorm và debate, kiểm tra lại nhiều lần."*

Đã chạy: workflow 10 agent (4 lập trường A/B/C/D + phản biện chéo + phán quyết), 39 phút,
1,19M token. **Rồi tôi tự kiểm lại toàn bộ claim code và tự đo lại con số trọng yếu** — theo
lệ đã học: ~1/4 finding của soi độc lập sai hoặc phóng đại.

---

## 1. Hai câu trả lời

### (a) Có nên mô hình hoá hậu quả của mệt để lời khuyên nghỉ đo được bằng tiền? → **KHÔNG**

Lý do quyết định **không phải** "phức tạp quá" hay "tốn thời gian" — mà là:

**Bất kỳ cơ chế nào cho mệt hậu quả năng lực đều tạo `payout = f(F)`, tức tồn tại
`∂payout/∂F` — một tỷ giá sức-khoẻ↔tiền.** Viết tỷ giá đó vào *world* thay vì vào *objective*
không xoá nó; chỉ xoá **nhãn** của nó. Repo đã kẻ đúng đường này hai chỗ:
`shift_dp.DEFAULT_PARAMS` ("payout THUẦN, không phạt fatigue ảo"; `rest_min_per_4h` là ràng
buộc CỨNG) và `advice_bridge.should_defer_rest` ("sức khoẻ tài xế không phải biến để tối ưu").

Và nó **không cứu được kênh mà nó được viện dẫn để cứu**: lời khuyên nghỉ duy nhất sản phẩm
được phép nói là **HOÃN** (`rest_window` đổi *thời điểm*, không đổi *lượng* nghỉ). Dưới đúng mô
hình đó — tích liều khi lái, hồi phục khi nghỉ — hoãn nghỉ ⇒ lái dài hơn ⇒ liều cao hơn ⇒ Δ của
`rest_window` **âm hơn**, không dương hơn. Thứ mô hình mệt re-sign được là lời khuyên *"nghỉ
THÊM"*, mà không kênh nào phát và chính khung "nghỉ = ràng buộc" cấm định giá.

### (b) Có đủ khả năng làm đúng không? → **KHÔNG**

- **0 dữ liệu mệt, 0 dữ liệu tai nạn tài xế** trong toàn repo. `M_DRIVER_KPI_REWARD.online_time`
  có `mockgen_strategy: "từ go_online/offline sim"` ⇒ vòng tròn.
- Đường nhận dạng duy nhất từng được nêu — `driver_statistic_daily.count_cancel_not_relate_driver`
  — là **`rng.randint(0, cancelled)`** (`src/gsm_core/mockgen/realdata.py:168`): **nhiễu thuần
  theo construction**, tệ hơn vòng tròn. *(Tôi tự kiểm — ĐÚNG.)*
- Cần căn 5–11 tham số với 0 điểm dữ liệu ⇒ tiêu chí lựa chọn duy nhất còn lại là **dấu của Δ**,
  đúng thứ `CLAUDE.md` §4b cấm ("không được chỉnh calibration để che BUG").
- Liều "có nguồn" **không có nguồn cho quần thể này**: Điều 64 (240 phút lái liên tục) áp dụng
  *ô tô kinh doanh vận tải*; đoàn pilot là **bike 100%** ⇒ 240′ là ASSUMPTION, không phải nguồn.

---

## 2. 🔴 Bằng chứng mạnh nhất — và nó không phải của agent, tôi tự đo

`scripts/probe_rest_window_blockers.py` (mới), 3 seed (4200–4202), `coverage=all`,
`ladder=all`, **873 lần** `should_defer_rest` được gọi:

| Chặn ở đâu | lần | % | |
| --- | --- | --- | --- |
| `soc_low` | 385 | **44,1%** | ← LAN CAN SỨC KHOẺ |
| `fatigued` | 235 | **26,9%** | ← LAN CAN SỨC KHOẺ |
| `window_past` | 155 | 17,8% | khung solver chỉ ra nằm phía sau (`D-SIM-10`) |
| `no_window` | 90 | 10,3% | S7 không thấy vấn đề (idle median **16′** < ngưỡng **45′**) |
| `at_window` | 8 | 0,9% | đang ở đúng khung — đúng, không hoãn |
| **THỰC SỰ NÓI** | **0** | **0,00%** | |

**Hai lan can sức khoẻ một mình chặn 71,0% số cơ hội** ⇒ **trần trên của kênh `rest_window` là
≤29,0%**, và cái trần đó do **chính ranh giới đạo đức Cường đã đặt** dựng nên, không phải do bug.

⇒ Đây là câu trả lời trực tiếp cho *"có đủ khả năng thiết kế môi trường phức tạp đến thế
không"*: **đầu tư mô hình mệt để định giá lời khuyên nghỉ là đầu tư vào thứ mà ranh giới đã cấm
không cho quan trọng.** 71% cơ hội bị chặn bởi đúng nguyên tắc "sức khoẻ không phải biến để tối
ưu"; mô hình mệt chính xác đến đâu cũng không mở được 71% đó ra, vì mở ra chính là phá nguyên tắc.

### Tôi bác chẩn đoán trọng tâm của agent

Agent phán quyết đề xuất **"Cycle 0 — sửa `window_past`: root cause đã chứng minh, chặn
53/55 = 96,4%, rẻ nhất và giá trị cao nhất"**. Đo thật: `window_past` = **17,8%** số cơ hội
(≈61% phần sống sót sau lan can), **không phải 96,4%**. Sai **5,4×** về độ lớn — cùng đúng
họ lỗi với `DET-01` (đúng cơ chế, sai độ lớn 5,7×). Sửa `window_past` cho hoàn hảo cũng chỉ mở
được ≤17,8% cơ hội, không phải phục sinh cả kênh.

`no_window` cũng không phải "solver hỏng": idle tích luỹ median **16 phút** so ngưỡng
`IDLE_TOTAL_ALERT_MIN = 45` — S7 **cố ý không bịa vấn đề** khi tài xế không chờ nhiều. Đúng thiết kế.

---

## 3. Sáu claim code của agent — tôi tự kiểm, **cả sáu ĐÚNG**

| # | Claim | Kiểm |
| --- | --- | --- |
| 1 | 🔴 **`rest_window` là kênh DUY NHẤT không có `coin_follows`** ⇒ adherence **cắm cứng 1,0** | ĐÚNG — coin gọi ở `shift_plan:505`, `positioning:527`, `accept_lift:577`, `shift_extend:823`; **không** cho `rest_window` |
| 2 | `assert_crn` chỉ so **danh sách đơn**, không so quỹ đạo actor ⇒ không phải bằng chứng "bit-identical" | ĐÚNG (`parallel.py:204-214`) |
| 3 | `world.py:79` một stream `self.rng` **dùng chung** (huỷ-sau-nhận, `rest_min`, thời gian swap…) | ĐÚNG; chỉ rating (`:82`) và demand-hint tách riêng |
| 4 | `behavior.py:151,157` tiêu draw **có short-circuit** sau phép so `fatigue` ⇒ đổi định nghĩa liều = **dịch dòng RNG** của cả 90 tài xế, không phải "dịch mức" | ĐÚNG. Kèm: comment `:157` ghi "xác suất tăng theo fatigue" — code là **hằng 0,3** ⇒ comment SAI |
| 5 | `count_cancel_not_relate_driver = rng.randint(0, cancelled)` ⇒ nhiễu thuần | ĐÚNG (`realdata.py:168`) |
| 6 | `planned_rest_hour` (giảm nhẹ `D-SIM-10`) **chỉ** được nuôi ở `multiday.py`; `run_parallel` không dùng multiday | ĐÚNG ⇒ **trong MỌI A/B đã đo, giảm nhẹ D-SIM-10 chưa từng hoạt động** |

**Một claim của agent SAI:** *"`rest_deferred_min += 2.0` rồi WAIT ⇒ trần tác động ≈0,06%"* hàm ý
kênh là no-op. Dòng ngay sau đổi `action, target = IdleAction.WAIT, None` — **REST→WAIT là đổi
hành vi thật**. Cơ chế yếu, nhưng không phải no-op.

---

## 4. Hai lần probe của CHÍNH TÔI tự hỏng (ghi lại để không lặp)

1. **`coverage="single"` + `actor_id=None` ⇒ `covers()` trả False cho MỌI tài xế** — advisor tắt
   sạch. `idle_reduction.solve` chỉ được gọi **1 lần/3 seed**, và 203 `no_window` chỉ có nghĩa
   *"không được phủ"*. Nếu báo luôn, tôi đã báo *"kênh bị lan can chặn"* trong khi thật ra **tôi
   tự tắt advisor rồi đo cái tắt của mình.** Dấu hiệu bắt được lỗi: `solve` gọi 1 lần mà
   `no_window` bắn 203 lần — số không thể cùng đúng.
2. Tự dựng dict kênh "chỉ bật `rest_window`" — nhưng `CHANNEL_LADDER["rest_window"]` **có
   `shift_plan: True`** ⇒ tôi đã đo một cấu hình **không tồn tại trong artifact nào**.

Cả hai bẫy đã viết vào docstring của `scripts/probe_rest_window_blockers.py`.

---

## 5. Quyết định (phần đo được, tôi tự quyết theo chỉ thị điểm 5)

1. **KHÔNG** mô hình hoá hậu quả của mệt. `fatigue` giữ nguyên là **latent** — không ai đọc nó
   để tính tiền. Bảo vệ sức khoẻ bằng **lan can + guardrail**, không bằng nhãn, không bằng số.
2. **`rest_window` = DEMAND-TIMING** — ở *trong* bảng tiền, chịu cadence, **và phải có
   `coin_follows`** (đang thiếu ⇒ BUG, xem §5.1). Bác đề xuất dán nhãn SAFETY + bypass cadence:
   nhãn đó đảo nghĩa (kênh này **lấy nghỉ đi**), và nó sẽ cho một kênh adherence-1,0 được nói
   không hạn chế.
3. **Bác** mọi đề xuất đổi mẫu số `fatigue` của biến quyết định (phá CRN toàn cục **và** nới lan
   can một chiều — hai lỗi cùng lúc) và **bác** đề xuất xoá veto `fatigued`.
4. `rest_defer_max_min` là **hằng số chính sách khoá-không-sweep** — để không bao giờ xuất hiện
   bảng *"hoãn lâu hơn = nhiều tiền hơn"*.
5. **Bias phải khai báo trong mọi báo cáo:** sim **không có kênh tác hại nào** của việc hoãn nghỉ
   (không tai nạn, không giảm chất lượng, không mệt qua đêm — `D-SIM-16`) ⇒ **mọi Δ dương của
   lời khuyên hoãn nghỉ đều dương quá mức theo cấu trúc**. Không được báo Δ đó như giá trị thật.

### 5.1 🔴 BUG mới, cần sửa trước mọi thứ khác: `rest_window` thiếu `coin_follows`

Bốn kênh có coin, một kênh không ⇒ trong mọi phép đo đã chạy, `rest_window` có **adherence
hiệu dụng = 1,0** trong khi bốn kênh kia ~0,59–0,68 theo archetype. Đây là **bất đối xứng đo
lường**: nếu kênh có bao giờ nói được, Δ của nó bị thổi lên theo cấu trúc.

Hiện tại **chưa gây hại số nào** vì kênh nói 0/873 lần — nhưng đó là sự trùng hợp may mắn, không
phải thiết kế. Sửa: thêm `coin_follows(actor, "rest_window", now_min, f"defer_to_{target:02d}h")`
+ failing test trước.

### 5.2 Việc đáng làm, theo đúng thứ tự giá trị (KHÔNG phải thứ tự agent đề xuất)

| # | Việc | Vì sao ở đây |
| --- | --- | --- |
| 1 | `coin_follows` cho `rest_window` + failing test | Lỗi đúng-sai, chặn mọi phép đo sau |
| 2 | `fingerprint_actors()` thay `assert_crn` ở mọi test "kênh tắt ⇒ bit-identical" | `assert_crn` không phát hiện nhiễm stream ⇒ mọi bằng chứng bit-identical hiện tại là bằng chứng yếu hơn ta tưởng |
| 3 | Sửa comment sai `behavior.py:157` + gắn nhãn ASSUMPTION cho `fatigue_threshold_min` | Comment sai dẫn người đọc sau đi sai; nhãn là bắt buộc theo §5 CLAUDE.md |
| 4 | Bật `planned_rest_hour` trong A/B (dùng multiday) **hoặc** ghi rõ `rest_window` inert trong mọi artifact | Giảm nhẹ D-SIM-10 chưa từng chạy ⇒ mọi kết luận "advisor có 5 kênh" thực ra là 4 kênh |
| 5 | `rest_min_total`, `veto_fired_n`, `max_continuous_drive_min` thành **guardrail tầng 5** | Chặn kịch bản "mua Δ bằng cách xoá lan can" |
| ~~6~~ | ~~Sửa `window_past`~~ | **Hạ ưu tiên**: trần ≤17,8%, và §1(a) nói kênh này về bản chất không đáng định giá |

---

## 6. ✅ ĐÃ CHỐT 2026-07-30 — xem `tracking/QUYET-DINH-2026-07-30-nam-diem.md`

Cường trả lời cả 5: mục 2 *"okey, chấp nhận"*; **bốn mục còn lại "bạn quyết"**. Tóm tắt quyết định:

| # | Câu hỏi | Quyết định |
| --- | --- | --- |
| 1 | `rest_window` = DEMAND-TIMING hay SAFETY? | **DEMAND-TIMING** — trong bảng tiền, chịu cadence **và** coin. Sức khoẻ bảo vệ bằng **lan can** (đo được: chặn 71,0%), không bằng nhãn |
| 2 | Câu trả lời chính thức với GSM/hội đồng | **CHẤP NHẬN** — nợ docs đã trả ở `specs/advisor-objective-model-v2.md` §1.2/§1.2b/§5b/§6 |
| 3 | ~~Gửi GSM xin bảng `trips` cấp đơn~~ | 🚫 **RÚT LẠI** — Cường nói rõ GSM **không cấp thêm gì**. Thay bằng **`T-047`**: hợp đồng dữ liệu **phản thực** + bản đồ MOCK↔THẬT + *"kết luận nào không sống nổi qua khoảng cách đó"* |
| 4 | Nếu `rest_window` Δ≈0 thì tắt hay đầu tư? | **CHƯA ĐƯỢC QUYẾT** — kênh **chưa hề được đo**: ~~thước hỏng (`D-M3-01`)~~ *(✅ thước ĐÃ SỬA 2026-07-30, UPDATE-102 — tiên quyết 1/3 xong)* + kênh chưa từng bật (`D-M3-04`, nói 0/873 lần — **còn**). ⇒ Một phiên xử công bằng với **cổng TIỀN-ĐĂNG-KÝ** viết trước khi đo. FAIL ⇒ tắt + DEFERRED, **cấm hiệu chỉnh rồi đo lại** |
| 5 | V-15 | **HUỶ** — và không chỉ gạch C2 mà viết **phần thay thế**: `C2′` (chi phí cơ hội của THỜI ĐIỂM nghỉ) + **khung BA LỚP** (LƯỢNG = ràng buộc · THỜI ĐIỂM = biến · MỆT = latent) |

**Điều quan trọng nhất rút ra:** câu hỏi gốc của Cường — *"lời khuyên advisor ra action nghỉ để làm
1 features để tính metric tiền không?"* — có câu trả lời **CÓ LÀM ĐƯỢC**, chỉ là bằng `C2′` chứ không
bằng mô hình mệt. Định giá **thời điểm** nghỉ không cần định giá **sức khoẻ**.

## 6b. (lịch sử) Câu hỏi gốc trước khi được chốt

1. **`rest_window` = DEMAND-TIMING (trong bảng tiền, chịu cadence + coin)** — đồng ý không?
   Lựa chọn kia (SAFETY, ra khỏi bảng tiền) làm kênh lấy-nghỉ-đi được nói không hạn chế.
2. **Chấp nhận câu trả lời chính thức với GSM/nhà đầu tư:** *"chúng tôi không định giá lời khuyên
   nghỉ qua đường sức khoẻ — vì không có dữ liệu, và vì nguyên tắc"* — được không?
3. **Có gửi GSM yêu cầu dữ liệu** bảng `trips` cấp đơn (`driver_id`, mốc assign/pickup/dropoff/
   cancel, **chủ thể huỷ**) để join `online_time` + `public_driver_hex_tracking`? Đây là **điều
   kiện duy nhất đảo chiều câu (b)**, và nó không tốn compute.
4. **`V-15` chốt lại là HUỶ?** Kèm nợ docs: gạch **C2** ở `specs/advisor-objective-model-v2.md`
   §1.2 và §5b/§6-bước-2b (hiện ghi "chưa làm", mâu thuẫn `TODO.md` T-041 1c đã HUỶ).
5. **Nếu `rest_window` sau khi sửa coin + D-SIM-10 vẫn Δ≈0:** tắt kênh + ghi DEFERRED (tôi đề
   xuất), hay đầu tư thêm? Kỳ vọng trung thực là **gần 0** — `shift_plan`, phiên bản mạnh hơn của
   cùng ý tưởng, đã bị tắt sau n=100.

---

## 7. Chưa kiểm chứng

- Con số của phản biện chéo **chưa reproduce**: "79,7% lần reset đến từ khe hở idle", "veto
  `fatigued` 54/90 → 0/90 khi sửa liều". Không trích vào UPDATE trước khi tự đo.
- Probe của tôi: **3 seed** ⇒ mô tả, **không** phải kết luận nhân quả (§4b yêu cầu ≥5 seed cho
  stochastic regression, ≥30 cho phân phối). Đủ để kết luận *"kênh nói 0 lần"* (0/873 là định
  tính, không cần CI); **không** đủ để chốt tỷ lệ 44,1/26,9/17,8 là hằng số.
- Ca vắt qua nửa đêm (`D-R11b`) chưa xét trong probe.

**Nhắc theo lệ (CLAUDE.md §3.1):** `tracking/PENDING-REVIEW.md` còn mở — **V-15** (chính là §6.4
ở trên) và **V-18**. Toàn bộ tài liệu này là `WAITING-VERDICT`, không phải `DONE`.
Visual gate: `NOT_APPLICABLE` (docs + probe, không đổi output sim).
