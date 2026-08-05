# UPDATE-140 — Cycle B (`D-M3-04`): phép đo chạy xong → **REVERT** `rest_window` sang khuyên mềm

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent (Cường: *"chốt đề xuất, nghiên cứu lại 1 lần rồi làm ngay khi kết quả về"*)
- **Loại:** research (phép đo) + fix (thi hành luật quyết định đã khoá)
- **Liên quan:** `D-M3-04` · prereg khoá 2026-08-01 · `luat_quyet_dinh` khoá 2026-08-03 · `V-07`

## Tóm tắt

Viết `run_pair_multiday` (phần CÒN LẠI duy nhất của `D-M3-04` — grep trước đó: hàm này **chỉ tồn
tại trong tài liệu**), chạy 100 seed × 3 ngày × 2 arm, và **thi hành luật quyết định đã đăng ký
TRƯỚC khi đo**: kết quả trúng **hai** điều kiện REVERT độc lập ⇒ `rest_window` chuyển từ
`MEASURED_TOPICS` sang `SOFT_TOPICS`.

## Kết quả — `research/audit/2026-07-27-current-state/45-dm304-multiday.json`

| | |
| --- | --- |
| **Δ payout** (`payout_mean_all`, trung bình ngày 1..2) | **−429,3đ** · CI95 **[−1142,3; +289,6]** ⇒ **ns** |
| **STOP-A/B** (adherence + arm đối chứng) | **OK** — 0 flag |
| **STOP-C** (tầng 5) | 🔴 **BẮN** — `rest_min_total` −6,6% (3879′ → 3621′) |
| **STOP-D** (tất định) | **OK** — ngày 0 và ngày 1 identical qua hai lần chạy |
| **Verdict** | **REVERT** — hai đường độc lập: Δ `ns` **VÀ** STOP-C bắn |

### ✅ Prereg dự đoán ĐÚNG

Kỳ vọng khoá 2026-08-01: Δ ∈ **[−1.500, +500]**. Đo được **−429** — **nằm trong khoảng**. Phép đo
**THÀNH CÔNG** (mô hình dự đoán đúng), **không phải** "kênh thất bại". Đúng như prereg ghi trước:
*"nếu REVERT xảy ra thì phép đo THÀNH CÔNG"*.

### 🔴 Phần đáng nói hơn Δ tiền: hại SỨC KHOẺ, và nó KHÔNG mất đi khi kênh thành khuyên mềm

| tầng 5 (cột RIÊNG — **cấm** quy ra VND) | Δ | CI95 |
| --- | ---: | --- |
| `rest_min_total` | **−257,9′** | [−290,7; −226,2] |
| `work_span_p50` | **+14,0′** | [12,1; 15,9] |
| `work_span_p90` | **+42,3′** | [37,5; 47,1] |
| `drive_min_p50` | **+7,6′** | [6,4; 8,9] |
| `drive_min_p90` | **+19,6′** | [15,8; 23,4] |
| `veto_defer_cap_n` | 0 → **8,0** | [7,5; 8,5] |

Kênh nói **2 986** lần, được nghe **1 726** (adherence 0,578) trên 100 seed × 2 ngày.

⇒ Kênh **ăn vào nghỉ** một cách không thể chối cãi (mọi CI không chứa 0). REVERT làm nó thôi có
claim tiền và thôi bị đo mức nghe lời — nhưng **không** sửa cái hại đó. Kênh đang **TẮT** ở config
sản phẩm; đề nghị **giữ TẮT** cho tới khi làm xong đề xuất ở
`specs/simulation/d-m3-04-root-cause-delta-am.md`.

### 🔒 Ranh giới phát biểu (prereg khoá)

- **ĐƯỢC** nói: *"trong world không có hậu quả mệt, kênh nghỉ là chi phí thuần"*.
- **KHÔNG được** nói: *"gợi ý nghỉ vô giá trị ngoài đời"* — khác nhau đúng ở β, thứ ta có **0 dữ
  liệu** để đặt (0 dữ liệu mệt, 0 dữ liệu tai nạn).

## 🔴 Bài học phương pháp lớn nhất của cycle này: **ba CI không chứa 0 ở n=5 đều là NHIỄU**

Smoke 5 seed cho ba chỉ tiêu vận hành có CI **không chứa 0**, và tôi đã nói với Cường rằng *"hướng
khá chắc"*. Ở n=100 **cả ba chứa 0**:

| | n=5 | n=100 | |
| --- | --- | --- | --- |
| `swap_wait_mean` | +1,19 [0,32; 2,23] | **−0,03** [−0,30; +0,24] | ⚠ nhiễu |
| `orders_completed` | −5,8 [−9,0; −2,6] | **−1,3** [−3,14; +0,46] | ⚠ nhiễu |
| `served_rate` | −0,0048 [−0,0076; −0,0020] | **−0,0011** [−0,0026; +0,0003] | ⚠ nhiễu |
| `rest_min_total` | −152,8 | **−257,9** | ✅ thật |
| `work_span_p90` | +37,6 | **+42,3** | ✅ thật |

Trên ba con số nhiễu đó tôi đã dựng cả một giả thuyết *"advisor tạo hàng đợi ở trạm đổi pin"* và
viết hai đề xuất thi công. **Cả hai vô ích.** `min_seeds=100` của prereg không phải thủ tục — nó là
thứ chặn đúng loại sai này.

## Nghiên cứu lại (theo yêu cầu Cường) — vòng hai BÁC hai phần ba vòng một

| Giả thuyết vòng 1 | Phép đo trực tiếp | Kết quả |
| --- | --- | --- |
| dồn cục khung nghỉ | phân bố `planned_rest_hour`, 225 lượt | ✅ **thật** — 3 khung ôm **64,4%**, chỉ 10 giờ khác nhau |
| kênh hoãn **ĐỔI PIN** | `deferred_from` của `advice_rest_window` | 🔴 **BÁC** — **100% là `rest`**, **0/41** lượt swap |
| tụ ở trạm ⇒ hàng đợi | Δ chờ theo giờ | 🔴 **BÁC** — khung đông nhất Δ **0,00**; và n=100 xác nhận `swap_wait` là nhiễu |

**Phát hiện phụ — nhánh CODE CHẾT:** `world.py` viết
`if action in (IdleAction.REST, IdleAction.GO_SWAP, IdleAction.GO_CHARGE)`, nhưng **0/41** lượt hoãn
đến từ swap/charge: khi bản năng chọn `GO_SWAP` thì SOC thường đã ≤ ngưỡng, và đó chính là lan can
`soc_low` chặn trước. Hai phần ba điều kiện **không có đường chạy** — họ `D-R12` ở dạng ngược.

## 🔴 Vòng BA (n=30 ghép cặp) BÁC kết luận trung tâm của vòng hai

Nợ #2 dưới đây (*"sổ thời gian đo ở 3 seed ⇒ chưa đáng tin"*) đã trả xong. Kết quả **bác** chính
kết luận mà vòng hai in đậm:

| claim vòng 2 (n=3) | n=30, CI95 ghép cặp theo seed | |
| --- | --- | --- |
| `charge_min` **+80,5′** ⇒ *"nghỉ chảy vào SẠC"* | **−25,1** [−105,2; +61,2] | 🔴 **ns, và ĐỔI DẤU** |
| `empty_min` **+76,2′** | **+23,3** [−20,9; +64,7] | 🔴 **ns** |
| `occupied_min` **−14,2′** ⇒ *"khoản duy nhất sinh tiền giảm"* | **−0,4** [−44,8; +41,7] | 🔴 **ns** |
| `orders_cancelled` **+9,2%** | **+0,6** [−1,5; +2,5] | 🔴 **ns** |

**Cả bốn số neo của vòng hai đều là nhiễu**, nên đề xuất ⭐ số 1 của vòng hai (*"đưa chi phí PIN vào
quyết định hoãn"*) **mất sạch chỗ dựa và đã bị RÚT**.

### Cơ chế thật — nằm ở MỘT DÒNG code, không cần seed nào

[`world.py:970`](../../src/gsm_sim/world.py#L970): khi hoãn nghỉ, `action, target = IdleAction.WAIT, None`.
Mà `WAIT` là nhánh **duy nhất** cộng `idle_min` (`:1042`), `REST` là nhánh **duy nhất** cộng `rest_min`
(`:1016`), và hai nhánh **loại trừ nhau** trong cùng `if/elif/else`. Tức: **hoãn nghỉ = đứng chờ**, theo
định nghĩa, không có đường nào tới trạm sạc.

Số n=30 khớp đúng cơ chế đó: `rest_min` **−244,0** [−301,8; −181,7] ✅ · `idle_min` **+209,5**
[+107,3; +309,8] ✅ ⇒ **86%** phần nghỉ mất đi hiện lại ở cột chờ rỗng. Và **không** chỉ tiêu sinh tiền
nào nhúc nhích: `orders_offered` +0,8 ns · `orders_accepted` −1,0 ns · `orders_completed` −1,5 ns ·
`occupied_min` −0,4 ns.

⇒ Kênh **không** đánh đổi sức khoẻ lấy tiền. Nó **đốt sức khoẻ mà không đổi lấy gì**.

### Điểm mới: HAI lý do độc lập khiến kênh chỉ có thể lỗ

1. **β=0** (prereg khai trước): world không có hậu quả mệt ⇒ *nghỉ* không sinh lợi.
2. **Thế giới bị chặn bởi CẦU** (đo được: `orders_offered` Δ = +0,8 **ns**) ⇒ *không nghỉ* cũng không
   sinh lợi. Giải phóng thời gian tài xế **không tạo thêm đơn**.

Prereg dự đoán Δ ≤ 0 bằng lý do 1. Lý do 2 là thứ **đo được** lần này, và nó độc lập.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `specs/simulation/d-m3-04-multiday-prereg-locked.json` | sửa | (commit `371c9b9`, **trước khi đo**) 3 đính chính: DET-01 thu hẹp · fingerprint cả 2 ngày · metric = trung bình cohort |
| `src/gsm_sim/parallel.py` | sửa | `run_pair_multiday` + `_mean_dicts` + `_merge_adherence`; STOP-A soi cả hai arm; DET-01 tham số hoá |
| `src/gsm_sim/sim_metrics.py` | sửa | `fingerprint_actors` chuyển từ `scripts/` lên — MỘT nguồn cho STOP-D |
| `scripts/probe_adherence_truth.py` | sửa | import lại, bỏ bản sao |
| `scripts/run_dm304.py` | **tạo** | CLI + artifact; in LÝ DO khi cổng bắn |
| `tests/test_dm304_multiday_ab.py` | **tạo** | 16 test |
| `src/gsm_core/lifecycle/advice_topics.py` | sửa | **REVERT**: `rest_window` MEASURED → SOFT |
| `tests/test_advice_topic_registry.py` | sửa | 4 cổng ghim trạng thái cũ — sửa **có chủ ý**, đúng như chúng được thiết kế để bắt |
| `specs/simulation/d-m3-04-root-cause-delta-am.md` | **tạo** | root cause + đề xuất (viết lại LẦN BA sau khi n=30 bác vòng 2) |
| `tests/_health_boundary_manifest.py` | sửa | phân loại `fingerprint_actors` (MONEY, kèm chú thích) — chuyển hàm từ `scripts/` vào `src/` làm nó **lọt tầm quét** money-manifest ⇒ K-03 phình 4→5 mục; sửa xong về đúng 4 mục của Khánh |

## Kiểm chứng

| Command | Kết quả |
| --- | --- |
| `uv run python scripts/run_dm304.py --seeds 100 --json …` | 100 seed, ~40′, artifact `45-dm304-multiday.json` |
| `uv run pytest -q tests/test_dm304_multiday_ab.py` | **16 passed** |
| `uv run pytest -q tests/test_advice_topic_registry.py + dm304` | **50 passed** |
| `scratchpad/sever_dm304.py` | **12/12 BẮT ĐƯỢC** |
| `uv run pytest -q` (CẢ suite, SAU REVERT) | **1075 passed / 5 failed / 4 skipped** (55′38″) — 5 F đúng là 5 F **đỏ sẵn** `K-01`×3 · `K-02` · `K-03`, **0 hồi quy mới**. ⚠ K-03 từng phình 4→5 mục vì `fingerprint_actors` lọt tầm quét khi chuyển vào `src/` — đã phân loại, chạy lại `test_health_boundary.py`: **1 failed (đúng 4 mục của Khánh) / 11 passed** |
| `uv run pytest -q ui/backend/tests --ignore=…test_demo_advice_ack.py` | **192 passed** |
| probe sổ thời gian 30 seed × 2 ngày, CI ghép cặp theo seed | xong — kết quả BÁC vòng 2, xem mục "Vòng BA" |

### Sever 12/12 — mũi nào và vì sao

gộp ngày 0 vào metric · TỔNG thay vì TRUNG BÌNH khi nén ngày · TRUNG BÌNH thay vì CỘNG khi gộp
adherence (cổng |z|>4 mất công suất) · DET-01 nới thành không kiểm gì · DET-01 quay lại bắt mọi kênh
(TREO 100% seed) · STOP-A thôi soi arm A · `min_seeds` 100→30 · arm A bỏ khai
`positioning_overrides` (thừa kế im lặng) · hai arm khác nhau ở HAI kênh · STOP-D chỉ kiểm ngày 0 ·
`fingerprint_actors` có bản sao thứ hai · dùng `CHANNEL_LADDER` (prereg cấm).

## Visual verification

- **Status:** `NOT_APPLICABLE` — verdict là REVERT, kênh vẫn TẮT ở config sản phẩm, không có gì đổi
  trên màn hình. Nếu verdict là GIỮ thì đã phải mở visual gate.

## Adversarial self-review / flaws found

1. **Sai lớn nhất: tin CI ở n nhỏ — BA LẦN trong một phiên.**

   | # | Claim | n | Kết cục |
   | --- | --- | --- | --- |
   | 1 | `swap_wait_mean`/`orders_completed`/`served_rate` ⇒ *"hàng đợi trạm"* | 5 | n=100: **cả ba chứa 0** |
   | 2 | `charge_min` +80,5′ ⇒ *"nghỉ đổi thành sạc"* | 3 | n=30: **ns, đổi dấu** |
   | 3 | *"85% lượt kéo ca bị lan can chặn"* | — | marginal thật **3,5%**, thứ hạng đảo |

   Mẫu số chung **không phải** "thiếu seed" mà là **hành động như thể cảnh báo mình vừa viết không
   tồn tại**: cả hai lần tôi *đã* ghi *"⚠ n nhỏ"* ngay cạnh bảng, rồi vẫn viết kết luận in đậm và
   xếp hạng đề xuất thi công lên nó. ⇒ Quy tắc từ nay: **n < 30 + CI ghép cặp thì KHÔNG được xuất
   hiện trong câu kết luận**, chỉ được dùng để chọn phép đo tiếp theo.

2. ✅ **Nợ #2 của bản đầu đã TRẢ** (*"sổ thời gian đo ở 3 seed ⇒ chưa đáng tin"*) — đo lại 30 seed
   ghép cặp, và nó **bác** chính kết luận vòng hai. Xem mục "Vòng BA" ở trên.
3. 🔴 **Lỗi PHƯƠNG PHÁP nghiêm trọng hơn cả lỗi thống kê: khai thác số tổng hợp TRƯỚC khi đọc nhánh
   điều khiển.** Cơ chế thật (`action := WAIT`) nằm ở **một dòng** `world.py:970`. Đọc nó mất 30
   giây và nó **loại thẳng** giả thuyết "chảy vào sạc" về mặt cơ chế — không cần seed nào. Tôi thay
   vào đó chạy 3 seed, suy ra một cơ chế sai, rồi chạy 30 seed để bác nó.
   ⇒ **Số tổng hợp cho TƯƠNG QUAN; nhánh `if` cho NHÂN QUẢ. Đọc code trước.**
4. **Sổ thời gian không kín ~3,4%** (`online_min` 45 545 vs tổng phần 47 123) — chồng lấn do
   `online_min` gộp toàn bộ thời gian đã trôi (`D-QD4-05`). **Không ảnh hưởng kết luận**: `rest`/
   `idle` là hai nhánh loại trừ nhau trong cùng `if/elif/else`, và lệch này như nhau ở cả hai arm.
4. **`compare()` có bug sẵn**: `n_insufficient` tính theo hằng 30 chứ không theo `min_seeds` truyền
   vào. Không sửa trong cycle này (ngoài phạm vi), nhưng artifact ghi **n thật cạnh min_seeds** để
   không ai đọc nhầm cờ đó.
5. **Đã loại trừ:** *"arm đối chứng không sạch"* (STOP-B OK, 0 flag) · *"multiday không tất định"*
   (STOP-D OK cả hai ngày) · *"thước adherence hỏng"* (STOP-A OK cả hai arm).
6. **Chưa kiểm:** cơ chế nghỉ→sạc (đang chạy) · `days=3` là ngắn; kênh có thể khác ở 7/30 ngày ·
   `n=100` cho MDE ~1.000đ nên một Δ thật cỡ −400đ **không phân biệt được với 0** — đó là đánh đổi
   Cường đã chấp nhận tường minh khi khoá prereg.

## Follow-up / defer phát sinh

| ID | Việc |
| --- | --- |
| `D-M3-04` | ✅ **ĐÓNG** — REVERT thi hành xong |
| `D-QD4-01` | ✅ **TỰ TIÊU** — đúng điều kiện đã ghi (*"tự tiêu nếu D-M3-04 REVERT"*): nay `rest`/`rest_nudge`/`rest_window` cùng lớp MỀM nên sự nhập nhằng của `rest` không còn hậu quả phân loại |
| **`D-M3-04-FIX`** (mới) | Kênh **vẫn hại sức khoẻ** dù đã thành khuyên mềm. Giữ **TẮT** tới khi làm xong **cả hai**: (1) **hoãn = CAM KẾT** — ghi "nghỉ ở giờ X", tới X thì ép diễn ra, khung trôi qua thì trả lại quyền nghỉ ngay; (2) **nhánh rơi không được là `WAIT`** — từ chối nghỉ phải kèm hành động có ích, nếu không thì đừng từ chối. ⚠ Điều kiện *"đưa chi phí PIN vào quyết định hoãn"* của bản đầu đã **RÚT** (`charge_min` ns + đổi dấu ở n=30). Xem `d-m3-04-root-cause-delta-am.md` §4 |
| `D-M3-04-FIX-PRE` | 🔒 **Phép kiểm phân biệt phải chạy TRƯỚC khi thi công FIX**: arm B″ = arm B nhưng bỏ `action := WAIT`. Nếu `idle_min` **và** `rest_min` cùng về ~0 ⇒ `:970` là toàn bộ cơ chế. **≥30 seed + CI ghép cặp** — n nhỏ đã lừa ba lần |
| `D-M3-06` | Nhánh CHẾT `GO_SWAP`/`GO_CHARGE` trong điều kiện hoãn — gỡ, hoặc làm nó chạy được có chủ ý |
