# UPDATE-100 — E5 cho tương tác FIFO một CI hợp lệ, và phán quyết điểm 3 (mệt/nghỉ)

Ngày: 2026-07-29 · Người điều khiển agent: Cường · Trạng thái: `WAITING-VERDICT`
Loại: docs + instrument (**không đổi output sim**, không sửa file `src/gsm_sim/**` nào)

## 1. Vì sao có update này

Hai việc đến cùng lúc:

1. **E5** — thí nghiệm tôi tự ghi ra như lỗ hổng của chính artifact 37 (*"các hiệu số là hiệu
   của điểm ước lượng, không có CI"*) đã chạy xong ở n=100 per-seed.
2. **Điểm 3 của Cường** — *"kiểm tra có thiết kế độ mệt của tài xế chưa? ... kiểm tra xem liệu
   có thực sự đủ khả năng thiết kế môi trường phức tạp đến thế không? phần này phải engineer kĩ,
   brainstorm và debate, kiểm tra lại nhiều lần."* — workflow debate 10 agent xong, rồi tôi tự
   kiểm lại toàn bộ và **bác một chẩn đoán trọng tâm của nó**.

## 2. Files bị ảnh hưởng

| File | Tạo/Sửa | Gì |
| --- | --- | --- |
| `research/audit/2026-07-27-current-state/38-e5-2x2-perseed-n100.json` | **tạo** | Lưới 2×2 per-seed n=100 (seed 4200–4299, 4 world/seed) + bootstrap CI |
| `research/audit/2026-07-27-current-state/README.md` | sửa | Mục artifact 38 + hai đính chính bắt buộc |
| `tracking/updates/UPDATE-099-da04-cadence-mot-luat.md` | sửa | §Ablation: bảng E5 có CI; đánh dấu ô −1.700đ là nhiễu n=30 đã bị bác |
| `tracking/PLAN-2026-07-29-cadence-thuoc-san-pham.md` | sửa | Thêm §4c (E5); gạch mâu thuẫn `D-ĐA07-recheck` ở §4 và §6 |
| `tracking/HANDOFF-2026-07-29-da04.md` | sửa | §3 + §4.1c: E5 ✅, thay cảnh báo "không có CI" bằng số có CI |
| `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` | **tạo** | Phán quyết điểm 3 + 6 claim tự kiểm + đo lại + 5 mục cần Cường |
| `scripts/probe_rest_window_blockers.py` | **tạo** | Instrument đếm phân phối lý do chặn của `should_defer_rest` |
| `research/audit/2026-07-27-current-state/39-da07-recheck-tran-n100.json` | **tạo** | Phép đo ĐỘC LẬP `D-ĐA07-recheck` (n=100, seed khác, nhịp TẮT) |
| `specs/simulation/e1-budget-arbitration-4-mechanisms.md` | **tạo** | Spec E1 (7 agent) + header NULL-0 hạ ưu tiên chính nó |
| `tracking/DEFERRED.md` · `TODO.md` · `PROJECT-GRAPH.md` · `PENDING-REVIEW.md` | sửa | `D-M3-01..07`; T-041 1c → DEFERRED; node UPDATE-100; **V-15 có câu trả lời** |

## 3. E5 — tương tác FIFO lần đầu CÓ CI (artifact 38)

n=100 ghép cặp (4200–4299), 4 world/seed, lưu per-seed cả 4 ô rồi bootstrap:

| Ước lượng (`net_mean_all`) | mean | CI95 | |
| --- | --- | --- | --- |
| **TƯƠNG TÁC ngân sách FIFO** | **+2.207đ** | [+1.077, +3.372] | **SIG** |
| Giá của nhịp **khi CÓ** `shift_plan` | −2.466đ | [−3.420, −1.570] | **SIG** |
| Giá của nhịp **khi KHÔNG có** `shift_plan` | **−259đ** | [−1.111, +589] | **ns** |
| Bỏ `shift_plan` khi nhịp BẬT | +2.259đ | [+1.161, +3.323] | **SIG** |
| Bỏ `shift_plan` ở TRẦN | **+53đ** | [−974, +1.102] | **ns** |

Tương tác cũng SIG trên `gini_payout` +0,0043 · `served_rate` +0,52đp · `orders_completed`
+6,28 · `expired_n` −7,33 · `others_payout` +195.979đ.

**Hai kết luận, cả hai đều là đính chính lời tôi đã báo:**

1. *"Nhịp tự nó gần như miễn phí"* — trước là **điểm ước lượng +384đ**, nay là **−259đ với CI
   trùm 0** ⇒ có bằng chứng thống kê rằng **không phân biệt được với 0**. Chi phí của nhịp
   **không** ở việc advisor nói ít, mà ở **cách chia ngân sách**. Đây là luận cứ mạnh nhất tới
   nay cho `D-ĐA04-03`.
2. **`D-ĐA07-recheck` GIẢI — và nó ỦNG HỘ ĐA-07, không bác.** Tôi đã báo *"ở trần, `shift_plan`
   đáng +1.700đ ⇒ ngược ĐA-07"*. **Con số đó là nhiễu n=30.** Ở n=100: **+53đ ns** ⇒ kênh
   **trung tính khi đứng một mình** (khớp ĐA-07), nhưng **độc hại dưới ngân sách FIFO**
   (+2.259đ SIG) vì chiếm suất của kênh có tác dụng. ĐA-07 giữ TẮT là đúng, **với lý do mạnh
   hơn lý do ban đầu**.

### 3.1 Artifact 39 — phép đo ĐỘC LẬP đóng `D-ĐA07-recheck`

Bộ seed khác, ước lượng ghép cặp riêng, nhịp TẮT, n=100:

| Ước lượng | mean | CI95 | |
| --- | --- | --- | --- |
| **GIÁ TRỊ của `shift_plan`** ở trần | **−451đ** | [−1.499, +608] | **ns** |
| Trần giá trị advisor, đủ kênh | +7.666đ | [+6.615, +8.662] | SIG |
| Trần giá trị advisor, bỏ `shift_plan` | **+8.117đ** | [+7.022, +9.232] | SIG |

Khớp artifact 38 (+53đ ns ↔ −451đ ns — cùng lượng, dấu ngược theo quy ước) ⇒ **hai phép đo độc
lập cùng kết luận `shift_plan` trung tính.** `D-ĐA07-recheck` **ĐÓNG**, ĐA-07 đúng. Ở n=100 bỏ nó
còn hơi TỐT hơn (+8.117 vs +7.666) — ngược thứ tự lưới n=30 (6.789 < 8.488) ⇒ **ô −1.700đ là nhiễu.**

### 3.2 🔴 E1 tự lật ưu tiên của chính nó — **NULL-0**

Workflow sinh spec E1 (7 agent) tự mở artifact 38 và bắt điều tôi bỏ sót. Tôi đã gọi
`D-ĐA04-03`/E1 là *"mục giá trị cao nhất còn lại"*. **Câu đó SAI:**

| Sự thật | Số | |
| --- | --- | --- |
| Tương tác FIFO — toàn bộ giải thưởng một trọng tài khéo hơn có thể giành | +2.207đ | SIG |
| Bỏ `shift_plan` khi nhịp bật — **một dòng YAML của ĐA-07 đã lấy** | +2.259đ | SIG |
| **Giá của nhịp ở CẤU HÌNH SẢN PHẨM** (nhịp ON, `shift_plan` OFF) | **−259đ** | **ns** |

Dòng ba là dòng quyết định: **ở đúng cấu hình sản phẩm, ngân sách chú ý hiện tại không tốn khoản
tiền nào đo được.** Trọng tài khéo hơn nhiều nhất giành lại chi phí của trọng tài hiện tại — mà
chi phí đó là **0 (ns)**. ⇒ **E1 có headroom ≈ 0đ**; ĐA-07 đã ăn xong giải thưởng bằng một dòng
config. Spec lưu ở `specs/simulation/e1-budget-arbitration-4-mechanisms.md`, trạng thái
`DEFERRED-CÓ-ĐIỀU-KIỆN` (`D-M3-07`) — chỉ mở lại khi bật một kênh ÂM.

**Chỗ artifact 38 KHÔNG loại trừ, và đây mới là lever đáng đào:** `shift_plan` trung tính nghĩa là
lời khuyên tốt và tệ của nó **triệt tiêu nhau**. Cả bốn cơ chế trong spec đều *chia suất GIỮA các
kênh*; **không cơ chế nào CHỌN LỌC TRONG một kênh**. ⇒ Đề xuất thí nghiệm kế tiếp là **E9 — chọn
lọc trong kênh** (chỉ nói khi độ tin cậy cao), không phải E1.

Spec cũng chứa **hai lỗi thật ở SẢN PHẨM** đáng sửa bất kể E1 có chạy hay không: `topic` có
default `"bonus"` ở `GET /advice` ⇒ client không gửi `topic` (Flutter, curl, test cũ) rơi vào
nhánh khác web client; và không có guard chặn `budget_mode != fifo` khi cổng FIFO đã tắt.

## 4. Điểm 3 — phán quyết: KHÔNG mô hình hoá hậu quả của mệt

Chi tiết ở `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md`. Rút gọn:

- **(a) Có nên?** KHÔNG. Mọi cơ chế cho mệt hậu quả năng lực đều tạo `∂payout/∂F` — một **tỷ giá
  sức-khoẻ↔tiền**. Viết vào *world* thay vì *objective* không xoá tỷ giá, chỉ xoá **nhãn**. Và nó
  không cứu được kênh nó được viện dẫn để cứu: lời khuyên duy nhất được phép nói là **HOÃN**, mà
  dưới đúng mô hình đó hoãn ⇒ liều cao hơn ⇒ Δ **âm hơn**.
- **(b) Có đủ khả năng?** KHÔNG. 0 dữ liệu mệt, 0 dữ liệu tai nạn. Proxy duy nhất từng được nêu
  (`count_cancel_not_relate_driver`) là **`rng.randint(0, cancelled)`** — nhiễu thuần theo
  construction. Cần căn 5–11 tham số với 0 điểm dữ liệu ⇒ tiêu chí còn lại là **dấu của Δ**, thứ
  §4b cấm. Liều 240′ (Điều 64) áp dụng **ô tô kinh doanh vận tải**, đoàn pilot là **bike 100%**.

### 4.1 🔴 Bằng chứng mạnh nhất — tôi tự đo, không phải agent nói

`scripts/probe_rest_window_blockers.py`, 3 seed, `coverage=all`, `ladder=all`, **873 lần** gọi:

| Chặn ở đâu | lần | % | |
| --- | --- | --- | --- |
| `soc_low` | 385 | **44,1%** | ← LAN CAN SỨC KHOẺ |
| `fatigued` | 235 | **26,9%** | ← LAN CAN SỨC KHOẺ |
| `window_past` | 155 | 17,8% | `D-SIM-10` |
| `no_window` | 90 | 10,3% | idle median **16′** < ngưỡng **45′** — S7 cố ý không bịa vấn đề |
| `at_window` | 8 | 0,9% | đúng, không hoãn |
| **THỰC SỰ NÓI** | **0** | **0,00%** | |

**Hai lan can sức khoẻ một mình chặn 71,0%** ⇒ trần trên của kênh **≤29,0%**, và trần đó do
**chính ranh giới đạo đức Cường đặt** dựng nên, không phải bug. ⇒ Đầu tư mô hình mệt để định giá
lời khuyên nghỉ là **đầu tư vào thứ mà ranh giới đã cấm không cho quan trọng**.

### 4.2 Tôi bác chẩn đoán trọng tâm của agent phán quyết

Nó đề xuất *"Cycle 0 — sửa `window_past`: chặn **53/55 = 96,4%**, rẻ nhất và giá trị cao nhất"*.
Đo thật: `window_past` = **17,8%** số cơ hội (≈61% phần sống sót sau lan can). **Sai 5,4× về độ
lớn** — cùng họ lỗi với `DET-01` (đúng cơ chế, sai độ lớn 5,7×). Sửa nó cho hoàn hảo cũng chỉ mở
được ≤17,8%, không phải phục sinh cả kênh ⇒ **hạ ưu tiên**.

## 5. Kiểm chứng

| Cái gì | Bằng chứng | Nhãn |
| --- | --- | --- |
| Số E5 | Đọc **JSON gốc** `38-e5-*.json`, không trích từ ký ức hay bản tóm tắt (luật đã học sau lần báo sai) | ĐO, n=100 |
| 6 claim code của debate | Tự đọc code từng file:line — **cả 6 ĐÚNG** (bảng §3 của phán quyết) | ĐO |
| 1 claim của debate SAI | *"`rest_deferred_min += 2.0` ⇒ no-op"* — dòng ngay sau đổi `action → WAIT`, REST→WAIT là đổi hành vi thật | ĐO |
| Phân phối blocker | `probe_rest_window_blockers.py`, 3 seed, reproducible | ĐO, **3 seed ⇒ mô tả, KHÔNG nhân quả** |
| Số của phản biện chéo | *"79,7% reset từ khe hở idle"*, *"veto 54/90 → 0/90"* | **CHƯA reproduce — không trích** |

**Chưa kiểm chứng:** tỷ lệ 44,1/26,9/17,8 chỉ ở 3 seed (§4b yêu cầu ≥5 cho stochastic, ≥30 cho
phân phối) — đủ để kết luận *"kênh nói 0 lần"* (0/873 là định tính), **không** đủ để chốt tỷ lệ.
Ca vắt nửa đêm (`D-R11b`) chưa xét trong probe.

## 6. Adversarial self-review / flaws found

### 6.1 🔴 Probe của CHÍNH TÔI tự hỏng HAI lần — bắt được trước khi báo

1. **`coverage="single"` + `actor_id=None` ⇒ `covers()` trả False cho MỌI tài xế** — tôi đã tự
   tắt advisor rồi đo cái tắt của mình. `idle_reduction.solve` chỉ được gọi **1 lần/3 seed** mà
   `no_window` bắn **203 lần** — hai số không thể cùng đúng, đó là chỗ tôi bắt được. Nếu báo
   luôn, tôi đã báo *"kênh bị lan can chặn"* cho một cấu hình không có advisor.
2. **Tự dựng dict kênh "chỉ bật `rest_window`"** — nhưng `CHANNEL_LADDER["rest_window"]` **có
   `shift_plan: True`** ⇒ đo một cấu hình **không tồn tại trong artifact nào**.

Cả hai bẫy đã viết vào docstring của probe để người sau không sập lại.

### 6.2 🔴 FLAW MỚI, nặng: hai kênh có adherence 100% **theo cấu trúc**

Ba tầng cùng chỉ một chỗ:

| Tầng | Hiện trạng | Hệ quả |
| --- | --- | --- |
| `advice_bridge` | `rest_window` là kênh **DUY NHẤT không gọi `coin_follows`** (4 kênh kia: `:505/:527/:577/:823`) | adherence trong WORLD **cắm cứng 1,0** |
| `world.py:800-810` | chỉ log `advice_rest_window` **khi đã hoãn** | không có mẫu số "đã nói bao nhiêu lần" |
| `projections.py:163` | `_ALWAYS_FOLLOWED = {"advice_shift_extend", "advice_rest_window"}` — *"sự tồn tại của event nghĩa là ĐÃ THEO"* | `decision_adherence` của **cả hai** kênh = **100%** không thể khác |

Đây **đúng họ lỗi `BUG-EVAL-ARGMAX`** và đúng họ lỗi `F-1` (mẫu số positioning hụt, đã sửa bằng
cách emit `decided` cho mọi người được gán). `shift_extend` **có** coin nhưng return `0.0` khi
không theo ⇒ cũng không có event ⇒ cùng bệnh.

**Hiện tại chưa làm sai con số nào** vì `rest_window` nói 0/873 lần — nhưng đó là **trùng hợp may
mắn, không phải thiết kế**. `shift_extend` thì có nói, nên adherence 100% của nó **đang** là số
sai trong mọi bảng đã báo.

⇒ Đã ghi thành `D-M3-01` ở §5.2 của phán quyết, ưu tiên **1** (trên cả `window_past`). Chưa sửa —
cần plan riêng vì chạm **3 file + contract đo lường**, không phải one-liner.

### 6.3 Đã kiểm, không phát hiện vấn đề

- Số E5 đọc từ JSON gốc; CI khớp từng chữ số với `estimators.*.ci95`.
- Ước lượng ghép cặp: world A bit-identical giữa arm ⇒ `cost(s) = B_on(s) − B_off(s)` có CI hợp
  lệ (không trừ hai mean).
- Không file `src/**` nào bị sửa trong update này ⇒ **không cần** chứng minh behavior-neutral.
- Bias đã khai báo: sim **không có kênh tác hại nào** của hoãn nghỉ (`D-SIM-16`) ⇒ mọi Δ dương
  của lời khuyên hoãn nghỉ **dương quá mức theo cấu trúc**.

### 6.4 Seed/kịch bản có thể làm kết luận đảo chiều

- Phân phối blocker ở 3 seed: nếu ở 30 seed `soc_low` tụt dưới ~30% thì trần của kênh rộng hơn
  nhiều và §4.1 phải viết lại. **Chưa chạy.**
- Artifact 39 (`D-ĐA07` n=100 độc lập, đang chạy) là phép đo thứ hai cùng câu hỏi trên bộ seed
  khác — nếu nó **không** khớp +53đ ns thì §3.2 phải mở lại.

## 7. Docs đã cập nhật kèm theo

- `tracking/TODO.md`: cần thêm `D-M3-01` (adherence mẫu số 2 kênh) — **chưa làm, ghi ở §8**
- `SCOPE` / `DEFERRED` / `USER_STORIES`: **không đổi** (không thêm/bớt tính năng)
- `PROJECT-GRAPH`: cần node UPDATE-100 + cạnh `099 →(bổ sung CI)→ 100` — **chưa làm, §8**

## 8. Follow-up / defer

| Mã | Việc | Ưu tiên |
| --- | --- | --- |
| **D-M3-01** | `coin_follows` cho `rest_window` + log not-followed + `projections._ALWAYS_FOLLOWED` bỏ 2 kind ⇒ adherence 2 kênh đo được | **1 — cấp thiết** |
| **D-M3-02** | `fingerprint_actors()` thay `assert_crn` ở mọi test "bit-identical" | 2 |
| **D-M3-03** | Comment sai `behavior.py:157` ("xác suất tăng theo fatigue" — code là hằng 0,3) + nhãn ASSUMPTION cho `fatigue_threshold_min` | 3 |
| **D-M3-04** | `planned_rest_hour` chưa từng chạy trong A/B (chỉ có ở `multiday.py`) ⇒ hoặc bật multiday, hoặc ghi rõ `rest_window` inert trong mọi artifact | 4 |
| **D-M3-05** | Guardrail tầng 5: `rest_min_total`, `veto_fired_n`, `max_continuous_drive_min` | 5 |
| ~~D-M3-06~~ | ~~Sửa `window_past`~~ | **hạ** — trần ≤17,8%, và §4(a) nói kênh không đáng định giá |
| — | Đo lại phân phối blocker ở 30 seed | khi rảnh compute |
| — | Node graph + TODO cho UPDATE-100 | ngay sau update này |

## 9. Visual status

**`NOT_APPLICABLE`** — docs + một instrument đọc-only; không đổi dynamics, default parameter,
metric, visual encoding hay cách stakeholder diễn giải kết quả. Không file `src/gsm_sim/**` nào
bị sửa. (Số E5 sẽ cần visual khi nó vào dashboard/báo cáo — chưa vào.)

## 10. ⏳ NHẮC LẠI PENDING-REVIEW (lệ CLAUDE.md §3.1 — hoãn ≠ waive)

**V-15 chính là câu hỏi của update này** và nay đã có câu trả lời có bằng chứng:
*"có đồng ý ưu tiên thêm hậu quả của MỆT vào sim (T-041 1c)?"* → **tôi đề xuất KHÔNG**, xem §4.
Kèm: lập luận *"nghỉ 30′→120′ làm payout −17.310 → −24.960 ⇒ lỗi của thước đo"* là **non-sequitur**
— +90 phút nghỉ đổi −7.650đ ≈ **85đ/phút**, **thấp hơn** mọi giá phút-làm-việc trong sim
(284–910đ/phút, MOCK) ⇒ đó là dấu kỳ vọng của bất kỳ mô hình có chi phí cơ hội.

Còn mở: **V-01…V-15** (15 mục visual/data) · **V-18** (nhịp nói advisor, UPDATE-099) ·
mục ❓ *"quyết định cần Cường chốt"* và ⛔ *"blocker kỹ thuật"* trong `tracking/PENDING-REVIEW.md`.
Thêm 5 mục mới ở §6 của `PHAN-QUYET-2026-07-29-diem3-met-nghi.md`.
