# UPDATE-184 — Kiểm ĐỘ THỰC của sim: phép đối chiếu "dữ liệu thật" là VÒNG TRÒN, và đo lại độ bền kết luận advisor

Ngày: 2026-08-08 · Người điều khiển: Cường · Trạng thái: `DONE-CODE` (research/docs; chưa có verdict)

## Tóm tắt

Cường chỉ đạo: *"focus on pushing the efficiency of advisors and the validation of sim world — as
realistic as possible"*, ưu tiên việc **không cần duyệt**.

Việc đầu tiên tôi làm — đối chiếu sim với 13 bảng "dữ liệu thật" — cho một bảng **rất đẹp** (mọi
chỉ số lệch < 10%; `hoàn thành/được chào` lệch **0,8%**, tứ phân vị trùng khít). **Tôi đã không
báo con số đó**, vì kiểm nguồn gốc thì nó là **vòng tròn**: các dòng **xe máy** của
`driver_statistic_daily` do **chính `gsm_sim` sinh ra**.

⇒ Kết luận thật, và nó nặng hơn: **trong repo không tồn tại neo dữ liệu thật nào để kiểm chứng độ
thực của sim.** Mọi câu *"sim giống thực tế X%"* dựa trên các bảng này đều vô căn cứ.

Thay vì đi tìm neo không tồn tại, tôi chuyển sang đo thứ **đo được**: **kết luận advisor có sống
sót khi thế giới khác đi không** — cụ thể theo **độ chặt thị trường** (cỡ đội), vì cỡ đội hiện
hành `n = 90` là **số vặn tay**, không phải số đo được.

## Chi tiết cập nhật

### 1. Phép đối chiếu độ thực — và vì sao nó vô hiệu

Đối chiếu `driver_statistic_daily ⋈ driver_online_hours_sap_id` (join `(driver_id, local_date)`,
12.805 driver-day) với arm A (advisor TẮT) của `pb1b-raw.json.gz`. Đã tránh hai bẫy trước khi
chạy:

- **ghép hai bảng chưa join** — bản nháp `zip()` giờ online của tài xế này với cuốc của tài xế
  khác; đã sửa thành join thật;
- **mẫu số nhiễm loại xe** — sim `pilot_dongda` là xe máy; bảng có 3.137 driver-day ô tô/premium.
  Lọc `driver_type` bắt đầu bằng `bike` ⇒ 9.668 driver-day. (Đúng cơ chế đã làm `mm-03` sai ~2×
  và làm tôi báo sai *"26,7% im lặng"*.)

Kết quả (giữ lại **chỉ để làm bằng chứng cho lỗi**, KHÔNG được trích như kiểm chứng):

| chỉ số | "thật" xe máy | SIM arm A | lệch |
| --- | --- | --- | --- |
| giờ online/ngày | 8,93h | 8,55h | −4,2% |
| cuốc hoàn thành/ngày | 11,00 | 10,00 | −9,1% |
| lượt được chào/ngày | 13,00 | 12,00 | −7,7% |
| **cuốc / giờ online** | 1,38 | 1,26 | −8,5% |
| **hoàn thành / được chào** | 0,86 | 0,86 | **−0,8%** |

**Dòng cuối là dấu hiệu báo động, không phải thành tích.** Hai quá trình độc lập không cho cùng
trung vị *và* cùng tứ phân vị `[0,78–0,93]` tới hai chữ số. Truy nguồn:

- `src/gsm_core/mockgen/adapter_sim.py:17-18` — `from gsm_sim.runner import run_once`
- `src/gsm_core/mockgen/realdata.py:3-5` — *"BIKE simulate qua `adapter_sim.generate_day`…
  Acceptance theo **archetype target** + noise"*
- `src/gsm_core/mockgen/realdata.py:138-141` — `accepted`/`offered` lấy **thẳng** từ `sim_stats`

⇒ Bảng trên so **`gsm_sim` với `gsm_sim`**, dùng **cùng bộ `ARCHETYPES`**. Mức khớp `−0,8%` gần
như là **đồng nhất thức**. Dòng ô tô/premium là rule-based (`realdata.py:144-148`,
`prof["target_acceptance"]` + nhiễu Gauss) — cũng là giả định của ta, chỉ khác bộ sinh.

Điều này **nhất quán** với hồ sơ đối tác: GSM cấp **SCHEMA** 13 bảng, **không** cấp **DỮ LIỆU**.
Tôi đã có ghi chú đó và vẫn chạy phép so — nên đây cũng là lỗi quy trình, không chỉ lỗi phát hiện.

### 2. Ba con số về ĐỘ THỰC vẫn rút ra được (không cần neo ngoài)

- `accept_base` trung bình theo `archetype_mix` = **0,9084**; `acceptance_rate` trong bảng =
  **0,909**. Không phải trùng hợp — cùng một tham số đi vòng.
- **`wait_median_min` = 0,066′ ≈ 4 giây.** Đây là **khách chờ được ghép**
  (`sim_metrics.customer_wait`, chỉ tính đơn ĐƯỢC ghép). ⚠ **Không phải** đại lượng Cường nêu.
- **Chờ của TÀI XẾ** = `idle_min` = **32,0%** thời gian online (trung vị), tức ~164′/ca 8,55h.

⇒ Nghi vấn của Cường (*"thời gian chờ ghép đơn của tài xế thực tế không cao đến mức như trong
sim"*) hiện **chưa kiểm được**: không bảng nào có cột chờ-ghép, `trips` bị catalog ghi
**THIẾU CỘT** (không có `t_request → t_assign`). Nhưng hai số trên nói ngược chiều nhau —
**khách** chờ gần như bằng không, còn **tài xế** rảnh 32%. Nếu có nghi ngờ về độ thực thì chỗ
đáng ngờ là **4 giây**, không phải 32%.

### 3. Thay thế: đo ĐỘ BỀN của kết luận thay vì đo độ thực

`+3.219đ SIG` đo tại **đúng một điểm**: `actors.n = 90` — con số **vặn tay từ 74 lên 90** để kéo
`served_rate` lên 0,797. Dư cung đúng là điều kiện kênh **vị trí** ít giá trị nhất.

Thí nghiệm: đội ∈ {60, 75, 90, 105, 120} × 20 seed × **3 arm** (A / B / **NULL**), ghép cặp CRN.
Arm NULL (`NoisyWorld`, `RNG +7919`) chạy ở **mọi** mức đội — vì sàn nhiễu có thể tự đổi theo `n`;
hiệu chuẩn chỉ tại 90 thì các mức khác lại thành số thô. Đây là **nội dung cổng `null_arm_delta`
(Cycle P2) áp ngay tại chỗ**, kèm cổng tự phát hiện `PLACEBO VÔ HIỆU` khi arm NULL trùng khít
arm A (bẫy đã làm hỏng kết luận C9, `UPDATE-182`).

**Kết quả (20 seed ghép cặp CRN mỗi mức · 300 lượt `run_once`):**

| đội | `served_rate` A | Δpayout (B−A) | | Δ nhiễu thuần (N−A) | Δ đơn hết hạn | Δ phút rảnh |
| --- | --- | --- | --- | --- | --- | --- |
| 60 | 0,685 | **+1.572đ** [−1.280; +4.284] | **ns** | −1.119 ns | −6,7 SIG | −4,4′ SIG |
| 75 | 0,744 | **+3.722đ** [+1.594; +5.756] | SIG | +1.337 ns | −10,1 SIG | −6,8′ SIG |
| **90** | 0,795 | **+3.097đ** [+944; +5.157] | SIG | −854 ns | −15,8 SIG | −7,8′ SIG |
| 105 | 0,827 | **+4.170đ** [+1.924; +6.456] | SIG | −465 ns | −19,3 SIG | −8,9′ SIG |
| 120 | 0,844 | **+4.340đ** [+2.445; +6.333] | SIG | +428 ns | −27,9 SIG | −9,2′ SIG |

✅ **Cổng placebo PASS ở mọi mức** — arm NULL có phương sai thật (không mức nào bit-identical),
và `N − A` **ns ở cả 5 mức** ⇒ hiệu ứng không phải hiện vật nhiễu. Đây là lần đầu
`null_arm_delta` (Cycle P2) được áp **trên nhiều điểm thế giới**, không chỉ tại n=90.

✅ **Kết luận `+3.219đ` TÁI LẬP:** đo lại tại n=90 với bộ seed 20 ra **+3.097đ** SIG.

✅ **Nhất quán nội tại (kiểm bảo toàn):** Δ đơn hết hạn / số tài xế ≈ Δ chuyến. n=90:
15,8/90 = 0,176 vs đo 0,187. n=60: 6,7/60 = 0,112 vs đo 0,068. Không có rò rỉ chuyến.

### ⚠ 3b. Kết quả BÁC giả thuyết cấu trúc của chính tôi

Từ phân tích benchmark tôi đã viết: *"thế giới thừa cung ⇒ giải phóng thời gian tài xế ít giá trị
vì không đủ đơn hấp thụ"*, và **ngầm dự đoán** advisor sẽ mạnh hơn ở thị trường chặt.

**Đo được điều ngược lại, đơn điệu:** hiệu ứng **tăng theo cỡ đội** (+1.572 ns → +4.340 SIG), và
`Δ phút rảnh` / `Δ đơn hết hạn` cũng tăng đơn điệu. Đọc đúng:

> **Lời khuyên vị trí là công cụ PHÂN BỔ THẶNG DƯ, không phải công cụ cho khan hiếm.** Khi cung
> khan (đội 60, 31,5% đơn chết), ràng buộc chặt là **thiếu người**, dời người quanh bản đồ không
> tạo thêm năng lực. Khi cung dư, vị trí mới quyết định phần rảnh có rơi đúng chỗ có cầu không.

### ⚠ 3c. Điều khó chịu phải nói thẳng

Mức đội **gần benchmark ngành nhất** cũng là mức advisor **không đo được hiệu quả payout**:
n=60 cho 822/1258 đơn ⇒ **13,7 cuốc/tài xế**, gần dải 18–22 hơn hẳn mức hiện hành (10,0) —
và ở đúng đó `Δpayout` là **ns**.

⚠ **KHÔNG được đọc thành *"advisor vô dụng trong thế giới thực tế"*.** CI ở n=60 rộng
[−1.280; +4.284], điểm ước lượng **dương**; 20 seed có thể **thiếu lực**, không phân biệt được
*"hiệu ứng nhỏ hơn"* với *"chưa đủ mẫu"*. Và `Δ đơn hết hạn` **SIG ở CẢ n=60** (−6,7).

### 3d. ĐÃ GIẢI QUYẾT — chạy thêm 60 seed tại đúng mức đó, câu trả lời là THIẾU LỰC

`tang-luc-tai-muc-thuc-te.py`, seed **3320–3379** (mới, không chồng lấn), tổng **80 seed** tại
đội 60. Tiêu chí đọc đã ghi **trước** khi thấy số:

| chỉ số | 20 seed (cũ) | **60 seed (mới)** | gộp 80 |
| --- | --- | --- | --- |
| `payout` | +1.572đ **ns** [−1.280; +4.284] | **+2.370đ SIG** [+657; +4.114] | **+2.171đ** |
| `expired_n` | −6,7 SIG | −6,5 SIG [−10; −3] | −6,5 |
| `idle` | −4,4′ SIG | −6,5′ SIG [−8; −5] | −6,0′ |

✅ Arm NULL tại mức này: **−988đ ns**, **0/60** trùng khít ⇒ cổng placebo vẫn PASS ở cỡ mẫu lớn.

⇒ **Kết luận: hiệu ứng payout CÓ ở mức đội thực tế nhất.** Cái `ns` ban đầu là **thiếu mẫu**,
không phải hiệu ứng biến mất. Bức tranh sau hiệu chỉnh: advisor **có tác dụng trên toàn dải độ
chặt thị trường đã thử**, và tác dụng **lớn dần khi cung dư**.

⚠ **Hệ quả về độ tin của các mức khác:** ước lượng tại n=60 dịch **+1.572 → +2.370đ (+51%)** khi
tăng từ 20 lên 60 seed. Bốn mức còn lại vẫn ở **20 seed** ⇒ **độ lớn từng mức có sai số thật**;
chỉ được trích **xu hướng đơn điệu**, không được trích con số từng mức như giá trị chính xác.

### 3e. P2b — ô solver CHỌN không hơn ô NGẪU NHIÊN, đo ở mức LƯỢT GÁN

Phép đo trả lời câu Cường đã chọn (*"S4 — chưa đổi hàm mục tiêu, ĐO TRƯỚC ĐÃ"*). Arm `SHUF`
hoán vị đích **giữa chính các allocation** cùng lượt ⇒ giữ đa tập đích, giữ trần ô/zone-veto,
cùng số người được điều, cùng cường độ xáo trộn — **chỉ khác: không biết đi đâu**.

**Cổng 0 (dụng cụ đo phải trung tính):** recorder của arm B chứng minh **bằng vân tay payout
trùng khít**, không bằng lập luận. 61 lượt gán ghi được ở seed 3300.

| | B (solver chọn) | SHUF (mù) |
| --- | --- | --- |
| có đơn ≤20′ sau khi được điều | **57,52%** [55,42; 59,62] | **57,13%** [55,06; 59,24] |
| n lượt gán | 2.234 | 2.223 |
| chờ tới đơn kế (median, censor 45′) | 16,67′ | 16,75′ |

**⭐ Hiệu (B − SHUF) = +0,39đp [−2,48; +3,17] `ns`** ⇒ **HOÀ**, đúng phán quyết đã ghi trước.

**Bốn đường bằng chứng độc lập nay hội tụ:**
1. suy luận ma trận cost (tôi tự dẫn): `cost[i,j] = pen_i (+10)`, `pen_i` **hằng theo hàng** ⇒
   cộng hằng vào cả hàng **không đổi lời giải** bài toán gán ⇒ tương đương **chỉ báo 0/1**;
2. `greedy ≡ Hungarian` **472/472** (agent đo);
3. `B − SHUF` **ns** ở mức **ngày** (`c9d`);
4. `B − SHUF` **ns** ở mức **lượt gán**, n ≈ 2.200 (phép đo này).

#### ⚠ Phạm vi kết luận — hẹp hơn nhiều so với cách dễ đọc nhầm

`SHUF` **giữ nguyên tập ô đích và số người được điều**; nó chỉ hoán vị **ai đi ô nào**.
⇒ Cái được chứng minh là: **phép GÁN (tài xế nào → ô nào) không mang giá trị đo được.**
⇒ Cái **KHÔNG** được chứng minh: rằng kênh vị trí vô giá trị. Việc **điều người rảnh đi đâu đó
có trần còn lại** vẫn tạo ra hiệu ứng hệ thống đã đo (−15,8 đơn hết hạn, +3.097đ). `ranked_cells`
và `slots` (chọn TẬP ô) **không** bị phép đo này chạm tới.

**Giới hạn lực, phải nói ra:** CI hiệu rộng **5,66đp** ⇒ chỉ loại được hiệu ứng **lớn hơn ~3,2đp**
trên nền 57,5%. Và mỗi tài xế được điều **1,42 lần/ngày** ⇒ quan sát **không độc lập**, CI
bootstrap **hẹp hơn sự thật**. ⇒ Câu đúng là *"không phát hiện được lợi ích của phép gán, với
lực đủ bắt ~3đp trở lên"*, **không** phải *"đã chứng minh bằng không"*.

### 4. Phân phối chờ ghép — tôi nêu `D-WAIT-4S` rồi tự bác

Đo đầy đủ (seed 3300): đội 90 → p50 **0,07′** · p75 **0,96′** · p90 **2,87′** · p99 6,48′ ·
max **10,04′**. Phân phối **có đuôi tử tế**, không nhị phân như tôi phỏng đoán; `p75 ≈ 0,96′`
**trùng benchmark MDPI ~1 phút**, `max ≈ 10′` **đúng cap patience** đã thiết kế. Trung vị 4 giây
là **hệ quả của thừa cung** (69,5% đơn có người trong tầm ngay lượt dispatch đầu) và **dịch đúng
hướng** khi siết cung (đội 60: p50 0,17′, p90 4,12′). ⇒ `D-WAIT-4S` **HẠ CẤP, không phải lỗi**.

## Files bị ảnh hưởng

- **Tạo** `research/audit/2026-08-08-do-thuc-cua-sim/sim-vs-du-lieu-that.py` — phép đối chiếu +
  **đính chính vòng tròn ngay trong docstring**; giữ lại làm bằng chứng, không xoá
- **Tạo** `research/audit/2026-08-08-do-thuc-cua-sim/sim-vs-du-lieu-that.json` — artifact
- **Tạo** `research/audit/2026-08-08-do-thuc-cua-sim/do-ben-cua-ket-luan.py` — thí nghiệm độ bền
- **Tạo** `tracking/updates/UPDATE-184-do-thuc-cua-sim-khong-co-neo-that.md` — file này

Không đụng `src/`, `ui/`, `configs/`, `schemas/`.

## Docs đã cập nhật kèm theo

- `tracking/DEFERRED.md` — thêm `D-NEO-THAT` (xem Follow-up)
- SCOPE / USER_STORIES / TODO: **không đổi** (research thuần)

## Assumptions và evidence

| nhãn | nội dung | confidence |
| --- | --- | --- |
| **ĐO** | Xe máy trong `driver_statistic_daily` do `gsm_sim` sinh | **CAO** — đọc trực tiếp 3 vị trí code |
| **ĐO** | `wait_median_min` = 0,066′; `idle` = 32,0% online | CAO — `_system_metrics`, seed 3300 |
| **ĐO** | mean `accept_base` theo mix = 0,9084 | CAO — tính tay từ `ARCHETYPES` + `archetype_mix` |
| **SUY** | Không tồn tại neo dữ liệu thật nào trong repo | **TRUNG BÌNH-CAO** — đã kiểm 13 bảng qua `mockdata`; chưa loại trừ nguồn ngoài `data/mock/realdata-v1` |
| **GIẢ ĐỊNH** | Cỡ đội là trục bất định đáng đo nhất | TRUNG BÌNH — chọn vì có bằng chứng vặn tay 74→90; các trục khác (λ cầu, `ECON_WEIGHT`, `k_max`) chưa đo |

## Kiểm chứng

### Seeds và scenarios

- Đối chiếu: 30 seed (3300–3329) × 90 actor, arm A, từ `pb1b-raw.json.gz`; 9.668 driver-day mock
- Độ bền: 5 mức đội × 20 seed (3300–3319) × 3 arm = **300 lượt `run_once`**
- Smoke test `_do()` trên seed 3300 **trước khi** chạy full

**Chưa kiểm chứng:** wait-to-match của tài xế (không có cột); độ thực tuyệt đối của bất kỳ tham số
nào; các trục bất định ngoài cỡ đội.

## Visual verification

`NOT_APPLICABLE` — research/docs thuần, không đổi code sản phẩm, không đổi output UI.

## Adversarial self-review / flaws found

1. **Suýt báo một claim THUẬN LỢI sai.** Bảng "lệch < 10%" là thứ Cường muốn nghe. Tôi chỉ dừng
   lại vì dòng `−0,8%` *quá* khớp. Nếu nó lệch 6% — đủ đẹp nhưng không đáng ngờ — **tôi đã báo**.
   ⇒ Ngưỡng nghi ngờ của tôi đang neo vào *"số có đáng ngờ không"*, đáng lẽ phải neo vào
   *"nguồn có độc lập không"*, và câu hỏi đó phải hỏi **trước khi chạy**.
2. **Tôi đã có sẵn thông tin để biết trước.** Hồ sơ đối tác ghi rõ GSM cấp schema, không cấp dữ
   liệu. Tôi vẫn chạy phép so rồi mới truy nguồn.
3. **Hai lỗi phương pháp tự bắt được trước khi chạy**: `zip()` hai bảng chưa join; và mẫu số lẫn
   ô tô. Cả hai đều thuộc lớp lỗi đã trả giá trước đây.
4. **`_do()` bản nháp đọc ba thuộc tính không tồn tại** (`orders_served`, `orders_total`,
   `match_waits`) sau `getattr(..., None)` ⇒ sẽ **âm thầm** trả `nan`/đường suy diễn. Bắt được
   bằng smoke test `dir(result)` trước khi chạy 20 phút. Đây đúng mục *"hidden fallback"*.
5. **Chưa loại trừ**: `served_rate` có thể đổi theo `n` **không đơn điệu** (đội to hơn ⇒ tắc
   đường/tranh đơn). Nếu vậy trục *"độ chặt"* không phải một chiều và bảng phải đọc theo
   `served_rate` chứ không theo `n`. Script in **cả hai** cột nên phát hiện được.
6. **Điểm yếu còn lại**: 20 seed cho 5 mức là **ít hơn** 30 seed của `pb1b`. Nếu một mức ra `ns`,
   **không** được đọc là "advisor hết tác dụng ở mức đó" — có thể chỉ là thiếu lực.

## Expansion checkpoint

Phát hiện *"không có neo thật"* **không** mở scope mới: không đề xuất đi xin dữ liệu GSM, không
dựng nguồn ngoài. Nó **thu hẹp** những claim được phép nói, và chuyển công sức sang đo độ bền —
việc đã nằm trong plan đã duyệt (Cycle P2).

## Follow-up / defer phát sinh

- **`D-NEO-THAT`** (sev **CAO**, chưa có chủ): mọi claim dạng *"sim giống thực tế"* bị **CẤM** cho
  tới khi có nguồn độc lập. Điều kiện mở lại: có dữ liệu GSM thật, hoặc có nguồn công bố bên ngoài
  (blog official, báo cáo ngành) đủ để neo ít nhất `cuốc/giờ online` và `% thời gian rảnh`.
- **`D-WAIT-4S`** (sev **TRUNG BÌNH**): `wait_median_min` = 4 giây — nghi vấn dispatcher lý tưởng
  hoá (khách gần như không bao giờ chờ). Cần đo phân phối đầy đủ (p90/max) trước khi kết luận.
- Nghi vấn gốc của Cường về chờ-ghép-đơn của **tài xế**: `UNRESOLVED` — thiếu cột dữ liệu.

---

## ⏰ NHẮC LẠI — PENDING-REVIEW (Cường đang chờ check)

Gom đủ tại `tracking/CAN-CUONG-DUYET-2026-08-06.md`:

- 🔴 **CHẶN — visual gate P1** (`UPDATE-183`): thẻ `d-13 / 2026-09-26 / 14:00` (thưởng **tăng
  thêm**) và `d-3` hoặc `d-9` cùng ngày (cảnh báo **sát ngưỡng**). Kèm câu hỏi tôi **cố ý không tự
  quyết**: `caveat` nay có **ba mệnh đề** nối bằng `·` — có quá tải thị giác không?
- 🔴 **CHẶN — V-32**
- V-31 · K-01(b) ACK · D-QD4-05 · ~27 mục `V-` · Q-03/04/09/10/13 · **amendment ĐA-08**
- 4 quyết định tôi đã dùng quyền uỷ quyền (`PHAN-QUYET-2026-08-07`): `Q-D` phủ quyết · `Q-B` ·
  `Q-A` · `Q-07` — **tiền đề đều bác được**, Cường lật lại lúc nào cũng được
- ⏸ Khánh: 2 test đỏ + Flutter

Hoãn ≠ waive.
