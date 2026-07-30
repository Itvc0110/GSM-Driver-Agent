# UPDATE-101 — Chốt 5 quyết định V-15: C2 HUỶ, `C2′` thay, khung BA LỚP, và cổng tiền-đăng-ký cho `rest_window`

Ngày: 2026-07-30 · Người điều khiển agent: Cường · Trạng thái: `DONE-CODE` (docs/spec-only)
Loại: **sửa spec source-of-truth** + bản quyết định. Không sửa file `src/**` nào.

## 1. Vì sao có update này

Cường trả lời 5 mục giá trị ở §6 của `PHAN-QUYET-2026-07-29-diem3-met-nghi.md`. **Bốn trong năm mục
là "bạn quyết"** — nên update này ghi lại quyết định của agent **kèm lý do và kèm điều kiện đảo**,
để sau này ai đọc cũng biết nó dựa trên cái gì.

Nguyên văn: *"1. rest_window cho bạn quyết định · 2. okey, chấp nhận câu trả lời · 3. MOCK data, giả
sử chúng ta có data thật - chia thành 1 task mới, cần research kĩ càng, bạn tự chốt schema hợp lý -
tôi cũng đã nói rõ sẽ không có data thật từ GSM hay được cung cấp gì thêm. · 4. bạn quyết, phán quyết
dựa trên thử nghiệm và hiểu biết của bạn với định hướng của bài toán. · 5. Tự quyết, nhớ tiêu chí là
luôn chọn khó làm nhất, đem lại nhiều giá trị nhất."*

## 2. Files bị ảnh hưởng

| File | Tạo/Sửa | Gì |
| --- | --- | --- |
| `specs/advisor-objective-model-v2.md` | **sửa (source-of-truth)** | §1.2: **C2 HUỶ** + **`C2′` MỚI** · **§1.2b MỚI** (lập luận toán học + bằng chứng đo + khung BA LỚP) · **§5b HUỶ toàn bộ** + đầu đề cảnh báo + chỉ ra lập luận cũ là non-sequitur · **§6 bước 2b/3 HUỶ** + dòng trạng thái |
| `tracking/QUYET-DINH-2026-07-30-nam-diem.md` | **tạo** | 5 quyết định + lý do + **cổng TIỀN-ĐĂNG-KÝ** cho `rest_window` |
| `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` | sửa | §6 → "ĐÃ CHỐT" + bảng 5 quyết định; §6b giữ câu hỏi gốc để đối chiếu |
| `tracking/PENDING-REVIEW.md` | sửa | **V-15 → ĐÃ CHECK XONG** (giữ dòng gốc để đối chiếu) |
| `tracking/TODO.md` | sửa | **+T-047** (hợp đồng dữ liệu phản thực, `DOING`) · T-041 1c → **HUỶ** |

## 3. Năm quyết định

| # | Quyết định | Lý do gọn |
| --- | --- | --- |
| 1 | `rest_window` = **DEMAND-TIMING** (trong bảng tiền, chịu cadence **và** coin) | Nhãn SAFETY **đảo nghĩa** kênh này — nó **lấy nghỉ đi**. Và nó sẽ tạo một kênh adherence-1,0 được nói vô hạn. Sức khoẻ đã được bảo vệ bằng thứ mạnh hơn nhãn: **lan can, đo được chặn 71,0%** |
| 2 | Chấp nhận câu trả lời chính thức (Cường chốt) | Nợ docs đã trả — xem §2 |
| 3 | **`T-047`** — hợp đồng dữ liệu **phản thực**; 🚫 **rút lại** đề xuất "gửi GSM xin bảng `trips`" | Cường: GSM **không cấp thêm gì**. Deliverable không phải yêu cầu dữ liệu; là đặc tả + **bản đồ MOCK↔THẬT** + *"kết luận nào không sống nổi qua khoảng cách đó"* |
| 4 | **CHƯA quyết tắt/giữ** `rest_window` — kênh **chưa hề được đo** | Thước hỏng (`D-M3-01`: không rút coin ⇒ adherence cắm 1,0) **và** kênh chưa từng bật (`D-M3-04`: `planned_rest_hour` chỉ có ở `multiday.py`, A/B không dùng ⇒ nói **0/873 lần**). Tắt một kênh chưa nói câu nào là kết luận rỗng ⇒ **một phiên xử công bằng với cổng tiền-đăng-ký** |
| 5 | V-15 **HUỶ** — và viết **phần thay thế**, không chỉ gạch | Gạch một số hạng mà không thay gì là để lại lỗ, và lỗ đó sẽ được lấp lại bằng đúng ý tưởng vừa bị gạch |

### 3.1 Lập luận cốt lõi của quyết định 2/5 (một dòng)

Mọi cơ chế cho mệt một hậu quả năng lực đều tạo `payout = f(F)`, tức tồn tại **`∂payout/∂F` — một
tỷ giá sức-khoẻ↔tiền**. Viết tỷ giá đó vào *world* (mệt làm chậm tài xế) thay vì vào *objective*
(`−v_rest`) **không xoá tỷ giá; nó chỉ xoá NHÃN.** Ranh giới đã chốt là *"sức khoẻ tài xế KHÔNG phải
biến để tối ưu"* ⇒ **cả hai cách đều bị cấm.**

### 3.2 Phần THAY THẾ — khung BA LỚP (đây là phần "khó nhất, giá trị nhất" của điểm 5)

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

**`C2′`** = `−(payout_kỳ_vọng(giờ_nghỉ) − payout_kỳ_vọng(giờ_vắng_nhất))` — chỉ định giá việc nghỉ
**SAI GIỜ**, không định giá việc nghỉ. Tính từ `demand_by_hour` (belief cá nhân, đã có) ⇒ **0 tham số
nhân quả mới** ⇒ không có gì để hiệu chỉnh sai.

⇒ **Câu hỏi gốc của Cường có câu trả lời CÓ.** *"Lời khuyên advisor ra action nghỉ để làm 1 features
để tính metric tiền không?"* — **làm được**, bằng `C2′`. **Định giá THỜI ĐIỂM nghỉ không cần định giá
SỨC KHOẺ.** Đó là điều spec cũ (§5b) không thấy.

### 3.3 🔒 Cổng TIỀN-ĐĂNG-KÝ cho `rest_window` (quyết định 4)

Viết cổng ra **TRƯỚC** khi đo là thiết bị chống tự lừa: nó cắt đường *"đo xong rồi mới chọn tiêu chí
nào làm mình thắng"*.

**Tiên quyết:** `D-M3-01` (kênh có coin, mẫu số đo được) · `D-M3-04` (`planned_rest_hour` thật sự
chạy trong A/B) · `D-M3-05` (guardrail tầng 5 có **trước** khi đo, không thêm sau).

**PASS — cả 4, thiếu một là FAIL:** Δ`net_mean_all` > 0 và **CI95 không trùm 0** ở **n≥100 ghép cặp
CRN** · guardrail 4 tầng ĐA-08 **và** `others_payout_vnd` không xấu đi SIG · guardrail **tầng 5**
không xấu đi · **dấu của Δ giữ nguyên** trên `hour_weights` phẳng (placebo cầu), peak dịch +2h,
`meal_hour` dịch ±3h.

**FAIL ⇒ tắt kênh + DEFERRED. 🚫 CẤM hiệu chỉnh rồi đo lần hai** — cấm cụ thể: nới
`rest_defer_max_min`, đổi `IDLE_TOTAL_ALERT_MIN`, đổi định nghĩa lan can, đổi `LOW_DEMAND_MAX`.
Lý do: với 3 tham số nới được, đo tới lần thứ ba thì xác suất tìm được tổ hợp cho Δ dương **do nhiễu**
là đáng kể — và không ai sẽ ghi lại rằng đã thử ba lần.

**Kỳ vọng trung thực của agent, ghi TRƯỚC khi đo: gần 0.** Trần kênh ≤29,0%, và `shift_plan` (phiên
bản mạnh hơn của cùng ý tưởng) đã bị tắt sau hai phép đo n=100 độc lập (+53đ ns · −451đ ns). Ghi ra
đây để nếu kết quả dương thì phải giải thích vì sao, không được lặng lẽ ăn mừng.

## 4. Kiểm chứng

| Cái gì | Bằng chứng | Nhãn |
| --- | --- | --- |
| Lan can chặn 71,0% | `scripts/probe_rest_window_blockers.py`, 3 seed, `coverage=all`, `ladder=all`, 873 lần gọi | ĐO — **3 seed ⇒ mô tả, KHÔNG nhân quả** |
| Kênh nói 0 lần | 0/873 — định tính, không cần CI | ĐO |
| `shift_plan` trung tính | artifact 38 (+53đ ns) + artifact 39 (−451đ ns), **hai bộ seed độc lập** | ĐO, n=100 mỗi cái |
| 85đ/phút vs 284–910đ/phút | tính từ số của hồ sơ 11 (−7.650đ / 90 phút) | SUY LUẬN từ số MOCK đã có |
| `D-M3-04` (`planned_rest_hour` chỉ ở multiday) | grep toàn repo: chỉ `multiday.py:166/232` nuôi nó; `run_parallel.py` không import multiday | ĐO (đọc code) |

**Chưa kiểm chứng:** tỷ lệ 44,1/26,9/17,8 chỉ ở **3 seed** — đủ để kết luận *"kênh nói 0 lần"*, không
đủ để chốt tỷ lệ là hằng số. `C2′` **chưa implement, chưa đo lần nào** — nó là thiết kế, không phải
kết quả. Ca vắt nửa đêm (`D-R11b`) chưa xét.

## 5. Adversarial self-review / flaws found

### 5.1 Điểm yếu của chính quyết định 1 (DEMAND-TIMING)

Đặt `rest_window` **trong** bảng tiền nghĩa là nó sẽ được **so bằng tiền** với các kênh khác. Nếu
`C2′` đo ra Δ dương, có nguy cơ ai đó đọc thành *"hoãn nghỉ có lợi"* rồi muốn nới trần. Ba chốt chặn:
`POLICY_LOCKED_KEYS` · guardrail tầng 5 · và **bias phải khai báo** trong mọi báo cáo (sim không có
kênh tác hại nào của hoãn nghỉ ⇒ **mọi Δ dương đều dương quá mức theo cấu trúc**). Đã ghi vào §1.2b.

Rủi ro còn lại, chưa chặn được bằng code: một người đọc chỉ đọc bảng Δ mà không đọc dòng bias.
Đây là lý do dòng bias được đặt **trong spec source-of-truth**, không phải trong một UPDATE.

### 5.2 Điểm yếu của `C2′`

`C2′` dựa vào `demand_by_hour` — là **belief cá nhân của actor** (`_actor_demand_hint`), không phải
cầu thật. Nếu belief sai lệch hệ thống thì `C2′` định giá sai theo. ⇒ Đúng lý do cổng tiền-đăng-ký
đòi **placebo cầu** (`hour_weights` phẳng) và **cầu dịch +2h**: nếu dấu của Δ đổi theo biến thể cầu
thì kết luận là kết luận **về PROXY cầu**, không phải về lời khuyên. Chưa chạy.

### 5.3 Tôi đã đảo ngược đề xuất của chính mình trong 1 ngày

Hôm qua tôi viết *"tôi đề xuất tắt kênh + DEFERRED, kỳ vọng gần 0"*. Hôm nay tôi nói **chưa được
quyết**. Không phải đổi ý về kỳ vọng — kỳ vọng vẫn gần 0 — mà là nhận ra **đề xuất hôm qua sẽ là
quyết định dựa trên phép đo không hợp lệ**: kênh nói 0/873 lần vì mitigation của nó chưa từng được
wire vào A/B (`D-M3-04`), và thước đo nó thì hỏng (`D-M3-01`). "Δ≈0" của một kênh chưa từng bật không
mang thông tin. Ghi lại vì đây là loại lỗi dễ lặp: **kết luận đúng hướng, dựa trên bằng chứng rỗng.**

### 5.4 🔴 Tôi tự bắt được lỗi trong chính update này: bảng "enforce bằng" quảng cáo cơ chế KHÔNG TỒN TẠI

Bản đầu của bảng khung BA LỚP liệt kê 6 cơ chế enforce **như thể chúng đã có**. Grep toàn repo:

| Cơ chế | Thực tế |
| --- | --- |
| `rest_min_per_4h` | ✅ có (`shift_dp.py`) |
| ba lan can `should_defer_rest` | ✅ có |
| `POLICY_LOCKED_KEYS` | ❌ **không tồn tại** |
| `test_no_fatigue_in_payout_path` | ❌ **không tồn tại** |
| `rest_min_total` · `veto_fired_n` · `max_continuous_drive_min` | ❌ **không tồn tại** |

**4/6 là việc phải làm, không phải bảo đảm đang có.** Đây đúng là họ lỗi mà repo đã trả giá hai lần
(`D-R12`: nhánh `unsafe_while_moving` được quảng cáo trong khi `is_driving` không có đường nuôi từ
client; Lỗi #9: `topic_cooldown` chết ở UI vì `last_decided_min` không ai nuôi). Nguy hiểm hơn bình
thường ở đây vì bảng nằm trong **spec source-of-truth** về một **ranh giới đạo đức** — một chốt chặn
sức khoẻ không tồn tại nhưng được ghi là tồn tại là loại sai tệ nhất có thể ở tài liệu này.

**Đã sửa:** bảng nay có cột **"Có thật chưa?"** ở cả ba nơi (spec §1.2b, QUYET-DINH, update này), kèm
cảnh báo: **`C2′` KHÔNG được đo trước khi 4 cơ chế còn lại có thật.**

### 5.5 Đã kiểm, không phát hiện vấn đề

- §5b: **giữ phần mô tả** (*"nghỉ mất tiền, không nghỉ không mất gì"* — vẫn đúng), **đảo phần kết
  luận**. Không xoá lịch sử; đầu đề có cảnh báo để người đọc nhanh không hành động theo mục đã huỷ.
- Không file `src/**` nào bị sửa ⇒ không cần chứng minh behavior-neutral, không cần chạy suite.
- `C2′` không tạo tham số nhân quả mới ⇒ không có gì để hiệu chỉnh sai (khác hẳn C2, cần 5–11 tham số
  với 0 điểm dữ liệu).

## 6. Follow-up

| Mã | Việc | Trạng thái |
| --- | --- | --- |
| `D-M3-01` | Mẫu số adherence 3 tầng — **chặn mọi phép đo kênh nghỉ và kéo ca** | workflow soi 5 tầng + phản biện 2 lăng kính + sinh spec **đang chạy** |
| `T-047` | Hợp đồng dữ liệu phản thực | workflow research 4 hướng + 3 thiết kế đối đầu **đang chạy** |
| `D-M3-04` · `D-M3-05` | Tiên quyết của cổng tiền-đăng-ký | chờ, sau `D-M3-01` |
| `C2′` | Implement + đo theo cổng | chờ 3 tiên quyết |
| `E9` | **Chọn lọc TRONG một kênh** — lever thay E1 (headroom E1 ≈ 0đ) | chưa thiết kế |

## 7. Visual status

**`NOT_APPLICABLE`** — spec + docs, không đổi dynamics, default parameter, metric, visual encoding
hay output. Không file `src/**` nào bị sửa. (`C2′` sẽ cần visual gate khi implement — chưa implement.)

## 8. ⏳ NHẮC LẠI PENDING-REVIEW (lệ CLAUDE.md §3.1 — hoãn ≠ waive)

**V-15 nay ĐÓNG** bằng update này. Còn mở: **V-01…V-14** (14 mục visual/data — SIM-1/2/3/4/5, dashboard
SIM-XANH, Track UI, data semantics, ĐA-01 gỡ rò tương lai, card cảnh báo thưởng sắp mất) · **V-18**
(nhịp nói advisor, UPDATE-099) · mục ❓ *"quyết định cần Cường chốt"* và ⛔ *"blocker kỹ thuật"* trong
`tracking/PENDING-REVIEW.md`.
