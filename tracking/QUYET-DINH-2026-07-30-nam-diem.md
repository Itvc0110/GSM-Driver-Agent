# QUYẾT ĐỊNH — 5 mục V-15, chốt 2026-07-30

Cường trả lời 5 mục giá trị ở §6 của [`PHAN-QUYET-2026-07-29-diem3-met-nghi.md`](PHAN-QUYET-2026-07-29-diem3-met-nghi.md):

> 1. `rest_window` cho bạn quyết định
> 2. okey, chấp nhận câu trả lời
> 3. MOCK data, giả sử chúng ta có data thật — chia thành 1 task mới, cần research kĩ càng, bạn tự
>    chốt schema hợp lý. Tôi cũng đã nói rõ sẽ không có data thật từ GSM hay được cung cấp gì thêm.
> 4. bạn quyết, phán quyết dựa trên thử nghiệm và hiểu biết của bạn với định hướng của bài toán.
> 5. Tự quyết, nhớ tiêu chí là luôn chọn khó làm nhất, đem lại nhiều giá trị nhất.

Bốn trong năm mục là **"bạn quyết"**. Dưới đây là quyết định của tôi kèm lý do, để sau này ai đọc
cũng biết nó dựa trên cái gì và đảo nó cần bằng chứng gì.

---

## Điểm 1 — `rest_window` phân lớp thế nào → **DEMAND-TIMING**

**Quyết định:** `rest_window` là kênh **DEMAND-TIMING**. Nó ở **TRONG** bảng tiền, **chịu cadence**,
và **phải chịu `coin_follows`** (hiện đang thiếu — `D-M3-01`).

**Vì sao không chọn SAFETY** (phương án còn lại, đưa kênh ra ngoài bảng tiền + bypass cadence):

1. **Nhãn SAFETY đảo nghĩa kênh này.** `rest_window` **LẤY NGHỈ ĐI** — nó khuyên *hoãn* nghỉ để dồn
   vào giờ vắng khách. Gọi một kênh lấy-nghỉ-đi là "kênh an toàn" rồi cho nó quyền nói không hạn chế
   là đúng loại lệch nhãn↔hành vi mà cả cycle ĐA-04 sinh ra để diệt.
2. **Nó sẽ tạo một kênh adherence-1,0 được nói vô hạn.** Kênh này hiện là kênh **duy nhất không rút
   coin** ⇒ adherence cắm cứng 1,0. Bypass cadence + adherence 1,0 = một kênh mà mọi lời khuyên đều
   được nói và đều được nghe theo. Không kênh nào trong sản phẩm được có tính chất đó.
3. **Sức khoẻ đã được bảo vệ bằng thứ mạnh hơn nhãn: LAN CAN.** Đo được: `soc_low` chặn 44,1% và
   `fatigued` chặn 26,9% — **71,0% cơ hội bị lan can chặn**. Lan can là ràng buộc cứng trong code;
   nhãn chỉ là chuỗi ký tự. Bảo vệ bằng cái chặn được, không bằng cái đọc hay.
4. **Chọn SAFETY làm sản phẩm mất khả năng định giá lời khuyên nghỉ** — mà `C2′` (§1.2b của
   `specs/advisor-objective-model-v2.md`) là đường duy nhất định giá được nó **mà không** tạo tỷ giá
   sức-khoẻ↔tiền.

**Kèm theo (❌ CHƯA CÓ — phải viết):** `rest_defer_max_min` phải trở thành **hằng số chính sách
khoá-không-sweep** (`POLICY_LOCKED_KEYS`), để không bao giờ xuất hiện một bảng *"hoãn lâu hơn = nhiều
tiền hơn"* tạo áp lực nới trần. Cơ chế này **hiện không tồn tại trong code** — grep toàn repo:
0 kết quả. Nó là **điều kiện tiên quyết của `C2′`**, không phải bảo đảm đang có.

---

## Điểm 2 — câu trả lời chính thức với GSM/hội đồng → **CHẤP NHẬN** (Cường chốt)

Câu chính thức: *"Chúng tôi không định giá lời khuyên nghỉ qua đường sức khoẻ — vì không có dữ liệu,
và vì nguyên tắc."*

Đã ghi vào spec source-of-truth: `specs/advisor-objective-model-v2.md` **§1.2b** (mới) + **§5b HUỶ**
+ **§6 bước 2b/3 HUỶ**. Đây là nợ docs của V-15, nay trả xong.

---

## Điểm 3 — data thật → **`T-047`, task mới, đã khởi động**

Cường chốt hai điều đồng thời: (a) **giả sử có data thật thì schema là gì** — cần research kĩ; (b)
**GSM sẽ không cấp thêm gì**. Hai điều đó không mâu thuẫn: deliverable **không phải yêu cầu dữ liệu
gửi ai**, mà là **đặc tả phản thực** — và phần giá trị nhất của nó là mục *"kết luận nào của chúng ta
KHÔNG sống nổi qua khoảng cách MOCK↔THẬT"*.

⇒ Rút lại đề xuất *"gửi GSM xin bảng `trips` cấp đơn"* ở §6.3 của phán quyết. Cường đã trả lời: không.

Đang chạy: workflow research 4 hướng (schema thật GSM · kiểm kê MOCK cạn kiệt · solver cần gì · chuẩn
ngoài) → 3 thiết kế đối đầu theo 3 triết lý → chấm 2 lăng kính → spec chốt tại
`specs/real-data/data-contract-counterfactual.md`.

---

## Điểm 4 — nếu `rest_window` vẫn Δ≈0 thì tắt hay đầu tư? → **CHƯA ĐƯỢC QUYẾT, vì kênh CHƯA HỀ ĐƯỢC ĐO**

Đây là mục tôi phải nói ngược lại đề xuất của chính mình hôm qua. Hôm qua tôi viết *"tôi đề xuất tắt
kênh + ghi DEFERRED, kỳ vọng trung thực là gần 0"*. **Quyết định đó sẽ là quyết định dựa trên một
phép đo không hợp lệ**, vì hai lý do đo được:

| | |
| --- | --- |
| `D-M3-01` | Kênh **không rút coin** ⇒ `decision_adherence` cắm cứng 1,0 ⇒ **cái thước hỏng** |
| `D-M3-04` | `planned_rest_hour` — đường **duy nhất** làm lời khuyên hồi cứu của S7 có tác dụng — chỉ được nuôi ở `multiday.py`, còn `run_parallel.py` **không dùng multiday** ⇒ trong **mọi** artifact A/B đã đo, kênh nói **0/873 lần** ⇒ **cái kênh chưa từng bật** |

Tắt một kênh vì nó Δ≈0 trong khi nó chưa từng nói câu nào là kết luận rỗng. ⇒ **Quyết định của tôi:
cho kênh đúng MỘT phiên xử công bằng, với cổng TIỀN-ĐĂNG-KÝ viết ra TRƯỚC khi đo.**

Viết cổng ra trước khi đo là thiết bị chống tự lừa: nó cắt đường "đo xong rồi mới chọn tiêu chí nào
làm mình thắng".

### 🔒 CỔNG TIỀN-ĐĂNG-KÝ cho `rest_window` (khoá, không sửa sau khi đã đo)

**Điều kiện tiên quyết (làm xong hết mới được đo):**
1. `D-M3-01` — kênh có `coin_follows`, và mẫu số adherence đo được ở cả 3 tầng.
2. `D-M3-04` — `planned_rest_hour` thực sự chạy trong A/B (bật multiday hoặc đường tương đương).
3. `D-M3-05` — guardrail tầng 5 (`rest_min_total`, `veto_fired_n`, `max_continuous_drive_min`) có
   trước khi đo, không thêm sau.

**PASS — cả 4 điều kiện, thiếu một là FAIL:**
- Δ`net_mean_all` **> 0** và **CI95 không trùm 0** ở **n ≥ 100 ghép cặp CRN**;
- guardrail 4 tầng của ĐA-08 **và** `others_payout_vnd` không xấu đi SIG;
- guardrail **tầng 5** không xấu đi (nghỉ không bị bào mòn, veto không bị vô hiệu hoá, chuỗi lái
  liên tục không dài ra);
- **dấu của Δ giữ nguyên** trên cả ba biến thể cầu: `hour_weights` **phẳng** (placebo cầu) ·
  peak dịch **+2h** · `meal_hour` dịch **±3h**.

**FAIL ⇒ TẮT kênh + ghi DEFERRED. 🚫 CẤM hiệu chỉnh lại rồi đo lần hai.** Cụ thể cấm: nới
`rest_defer_max_min`, đổi ngưỡng `IDLE_TOTAL_ALERT_MIN`, đổi định nghĩa lan can, hoặc đổi
`LOW_DEMAND_MAX` để có thêm khung. Lý do cấm: với 3 tham số có thể nới, đo lại tới lần thứ ba thì
xác suất tìm được một tổ hợp cho Δ dương do nhiễu là đáng kể — và không ai sẽ ghi lại rằng đã thử
ba lần.

**Kỳ vọng trung thực của tôi trước khi đo: gần 0.** Lý do: trần trên của kênh là **≤29,0%** số cơ hội
(71% bị lan can chặn), và `shift_plan` — phiên bản mạnh hơn của cùng ý tưởng "sắp lại ca" — đã bị tắt
sau khi hai phép đo n=100 độc lập cho **+53đ ns** và **−451đ ns**. Ghi kỳ vọng ra đây trước khi đo,
để nếu kết quả dương thì tôi phải giải thích vì sao, chứ không được lặng lẽ ăn mừng.

---

## Điểm 5 — V-15 và nợ docs → **HUỶ**, kèm phần THAY THẾ

**Quyết định:** V-15 → **HUỶ**. Nhưng theo tiêu chí *"chọn khó làm nhất, giá trị nhất"*, tôi **không**
chỉ gạch C2 — gạch một số hạng khỏi objective mà không thay gì là để lại một lỗ, và lỗ đó sẽ được ai
đó lấp lại bằng đúng ý tưởng vừa bị gạch.

Nên tôi viết **phần thay thế**, đã vào spec:

| Đã làm | Ở đâu |
| --- | --- |
| C2 (giá trị nghỉ) → **HUỶ**, đánh dấu "KHÔNG BAO GIỜ IMPLEMENT" | `specs/advisor-objective-model-v2.md` §1.2 |
| **`C2′` MỚI** — chi phí cơ hội của **THỜI ĐIỂM** nghỉ, 0 tham số nhân quả mới | §1.2 + §1.2b |
| **§1.2b MỚI** — lập luận toán học đầy đủ + bằng chứng đo được + **khung BA LỚP** | §1.2b |
| §5b → **HUỶ toàn bộ**, và chỉ ra lập luận định lượng của nó là **non-sequitur** | §5b |
| §6 bước 2b (cơ chế mệt) + bước 3 (C2) → **HUỶ**; `C2′` thay, chặn bởi `D-M3-01`+`D-M3-04` | §6 |

### Khung BA LỚP — đây là phần thay thế thật sự

| Đại lượng | Vai trò trong objective | Cơ chế enforce | Có thật chưa? |
| --- | --- | --- | --- |
| **LƯỢNG nghỉ** | **RÀNG BUỘC CỨNG**, không phải số hạng | `rest_min_per_4h` trong `shift_dp` | ✅ **CÓ** (`src/gsm_core/solvers/shift_dp.py`) |
| | | `POLICY_LOCKED_KEYS` khoá `rest_defer_max_min` không cho sweep | ❌ **CHƯA CÓ — phải viết** |
| **THỜI ĐIỂM nghỉ** | **BIẾN** — định giá bằng `C2′` | `rest_window` = DEMAND-TIMING, trong bảng tiền, chịu cadence | ✅ CÓ (cadence) |
| | | …và chịu `coin_follows` | ❌ **CHƯA CÓ — `D-M3-01`, sev CAO** |
| **MỆT (`fatigue`)** | **LATENT** — không ai đọc để tính tiền | ba lan can trong `should_defer_rest` (`soc_low`/`fatigued`/`defer_cap`) | ✅ **CÓ** — đo được chặn 71,0% |
| | | grep-test `test_no_fatigue_in_payout_path` | ❌ **CHƯA CÓ — phải viết** |
| | | guardrail tầng 5: `rest_min_total`, `veto_fired_n`, `max_continuous_drive_min` | ❌ **CHƯA CÓ — `D-M3-05`** |

> ⚠ **Đọc cột cuối trước khi tin bảng này.** Trong 6 cơ chế enforce, **chỉ 2 tồn tại hôm nay**
> (`rest_min_per_4h`, ba lan can). Bốn cái còn lại là **việc phải làm**, không phải bảo đảm đang có.
> Bảng này được viết với cột trạng thái tường minh vì repo đã trả giá cho đúng họ lỗi *"code/spec tự
> quảng cáo một cơ chế không chạy"* (`D-R12`: nhánh `unsafe_while_moving` được quảng cáo trong khi
> `is_driving` không có đường nuôi từ client; và `topic_cooldown` chết ở UI vì `last_decided_min`
> không ai nuôi). ⇒ **`C2′` KHÔNG được đo trước khi 4 cơ chế còn lại có thật** — nếu đo trước, con
> số Δ sẽ được sinh ra trong một hệ không có chốt chặn nào ngăn nó bị đọc thành *"hoãn nghỉ có lợi"*.

Điểm mấu chốt: khung này cho phép **định giá lời khuyên nghỉ bằng tiền** (điều Cường hỏi ở điểm 3 hôm
qua: *"làm 1 feature để tính metric tiền"*) — **và nó không cần mô hình mệt.** Câu trả lời cho câu hỏi
đó là **CÓ làm được**, chỉ là bằng đường khác đường mà spec cũ đề nghị.

Và tôi cũng ghi lại **lập luận sai của chính §5b cũ**, không chỉ gạch nó: *"nghỉ 30′→120′ làm payout
−17.310 → −24.960 ⇒ thước đo hỏng"* — +90 phút đổi −7.650đ ≈ **85đ/phút**, **thấp hơn** mọi giá
phút-làm-việc trong sim (284–910đ/phút, MOCK) ⇒ đó là dấu kỳ vọng của **bất kỳ** mô hình có chi phí cơ
hội, không phân biệt được giả thuyết nào. Ghi lại lỗi lập luận, không chỉ ghi kết luận mới — vì cùng
một lỗi sẽ quay lại dưới tên khác nếu không ai đặt tên cho nó.

---

## Việc phát sinh từ 5 quyết định này

| Mã | Việc | Trạng thái |
| --- | --- | --- |
| `D-M3-01` | Mẫu số adherence 3 tầng (sev CAO) — **chặn mọi phép đo kênh nghỉ và kéo ca** | workflow soi + sinh spec đang chạy |
| `D-M3-04` | `planned_rest_hour` chưa từng chạy trong A/B | điều kiện tiên quyết của cổng điểm 4 |
| `D-M3-05` | Guardrail tầng 5 | điều kiện tiên quyết của cổng điểm 4 |
| `T-047` | Hợp đồng dữ liệu phản thực (điểm 3) | workflow research đang chạy |
| `C2′` | Số hạng mới trong objective | spec xong, chờ `D-M3-01`+`D-M3-04` |
| `E9` | **Chọn lọc TRONG một kênh** — lever thay E1 | chưa thiết kế; xem `D-M3-07` |

**Nhắc theo lệ (CLAUDE.md §3.1):** `tracking/PENDING-REVIEW.md` — **V-15 nay ĐÓNG** bằng tài liệu này.
Còn mở: **V-01…V-14** (14 mục visual/data) · **V-18** (nhịp nói advisor, UPDATE-099) · mục ❓ và ⛔
trong `PENDING-REVIEW.md`. Hoãn ≠ waive.
