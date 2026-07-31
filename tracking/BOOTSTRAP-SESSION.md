# BOOTSTRAP SESSION — prompt để nạp một AI coding agent mới vào dự án này

Cập nhật: **2026-08-01** · local HEAD = **`1d98de6`** (đã đẩy origin/main; Cường đã cho phép đẩy)

**Cách dùng:** mở session mới, paste đoạn trong khung §0 dưới đây. Không cần paste cả file này —
đoạn đó trỏ agent tới đúng các file phải đọc, theo đúng thứ tự.

**Cách bảo trì:** sau mỗi cycle có ý nghĩa, cập nhật **§2 (state)** và **§3 (hàng đợi)** của file này.
Đừng để nó stale — một bootstrap sai còn tệ hơn không có, vì agent sẽ tin nó.

---

## §0. ĐOẠN CẦN PASTE

```text
Bạn là AI coding agent làm việc trong repo GSM-Driver-Agent. Trước khi làm BẤT KỲ việc gì,
đọc theo ĐÚNG thứ tự này — đừng đọc lại toàn bộ lịch sử, hãy đi theo route:

1. CLAUDE.md                                  — harness bắt buộc, thắng mọi tài liệu khác
2. tracking/BOOTSTRAP-SESSION.md              — file này: state hiện tại + hàng đợi + BẪY đã sập
3. tracking/PLAN-2026-07-30-hang-doi-cong-viec.md  — THỨ TỰ THI CÔNG, có acceptance + chi phí
4. tracking/PENDING-REVIEW.md                 — việc Cường đang chờ check; PHẢI nhắc lại sau MỖI update
5. tracking/PROJECT-GRAPH.md                  — chọn route đọc theo task (KHÔNG đọc hết UPDATE)
6. tracking/DEFERRED.md + tracking/TODO.md    — khi task chạm scope/status/claim/policy
7. git log --oneline -8 + git status          — biết mình đang ở đâu; đừng tin ký ức

Sau đó ĐỌC MỤC §3 và §5 của tracking/BOOTSTRAP-SESSION.md rồi báo lại cho tôi:
(a) bạn hiểu state hiện tại là gì, (b) bạn định làm mục nào đầu tiên và vì sao,
(c) có gì trong hàng đợi bạn thấy sai thứ tự.

Đừng bắt đầu code trước khi tôi duyệt. Ngôn ngữ trao đổi: tiếng Việt.
```

---

## §1. Dự án là gì (30 giây)

Hệ thống AI giúp tài xế Xanh SM (GSM) cải thiện thu nhập. Team 2 người: **Cường** + **Khánh**.

Có **hai nửa**, và phân biệt được hai nửa này là điều kiện để hiểu mọi tài liệu:

| | Trả lời câu hỏi gì | Ở đâu |
| --- | --- | --- |
| **SIM** (twin-world A/B, SimPy) | *"Nội dung lời khuyên có giá trị không?"* → đo **TRẦN** giá trị advisor | `src/gsm_sim/` |
| **SẢN PHẨM** (FastAPI + web + Flutter) | *"Advisor nói bao nhiêu là không phiền?"* | `ui/`, `src/gsm_core/` |

⚠ **Nhịp nói (cadence) thuộc SẢN PHẨM, KHÔNG thuộc SIM** — Cường chất vấn 2026-07-29 và agent đã
phải thừa nhận lập luận cũ sai. `advice.cadence.enabled: false` là mặc định **đúng**, không phải bug.

**Ranh giới CỐ ĐỊNH** (đọc `CLAUDE.md` §5, đây chỉ là ba cái bị vi phạm nhiều nhất):
- Agent/LLM **không tự tính** số tài chính/xác suất — mọi số đến từ rule/analytics kiểm chứng được.
- **Sức khoẻ tài xế KHÔNG phải biến để tối ưu.** Đã có phán quyết: **không mô hình hoá hậu quả của
  mệt**, huỷ vĩnh viễn (`specs/advisor-objective-model-v2.md` §1.2b).
- Mock data **phải gắn nhãn mock**. Mọi số trong repo là MOCK; **GSM sẽ không cấp thêm dữ liệu**.

---

## §2. STATE hiện tại (2026-07-30)

```
local HEAD  = 844988f+  (UPDATE-114/115 đã đẩy); UPDATE-116 commit ngay sau
suite       = 1000 passed / 4 skipped / 0 failed  (2026-08-01: 935 + 65 UI)
              uv run pytest -q                  -> xem số trên
              uv run pytest -q ui/backend/tests -> 65
UPDATE       = 112 file, mới nhất UPDATE-118 (104 UIUX + 105 codex review là của remote)
PENDING      = 20 mục V- đang chờ Cường (V-15/V-19 đã ĐÓNG; V-22 mới 2026-08-01):
              V-01..V-14 (visual/data SIM + Track UI) · V-16 (fare parity gate)
              V-17 (kênh VỊ TRÍ b3/b4) · V-18 (nhịp nói advisor + card im lặng)
              V-20 (PHAN-QUYET đảo C2 — Cường đã hạ xuống THỬ NGHIỆM, chờ chốt văn bản)
              V-21 (L4-03 khe advisor nói MIỄN PHÍ — 3 lựa chọn, (a)/(b) đổi CHÍNH SÁCH)
              V-22 (xoá 300 dòng `trajectory.py` hay giữ? — module chết, bảng màu xung đột)
              ⚠ V-16/V-17 dễ bị đọc thiếu — agent đã nhiều lần chỉ đọc V-01..V-14 + V-18
```

🔴 **BẮT BUỘC: luôn chạy CẢ HAI lệnh khi nói "suite xanh".** `pyproject.toml` có
`testpaths = ["tests"]` nên `pytest -q` từ root **BỎ 56 test ở `ui/backend/tests/`** — tức bỏ đúng
test của **đường sản phẩm** (`D-M3-09`).

### Cấu hình đang chạy (đọc kỹ, dễ hiểu sai)

| Cờ | Giá trị | Nghĩa |
| --- | --- | --- |
| `advice.enabled` | **false** | Ở config mặc định **advisor im hoàn toàn**. A/B bật cờ này qua `_cfg_with` để đo |
| 4/5 kênh (`shift_plan`, `accept_lift`, `shift_extend`, `rest_window`) | **false** | Tắt theo ĐA-07 — *"không hiệu quả thì TẮT để advisor IM LẶNG"* |
| `positioning_overrides` | **`wait_only`** | Kênh **duy nhất** được duyệt bật. Chỉ ghi đè khi bản năng là ĐỨNG CHỜ |
| `advice.cadence.enabled` | **false** | Nhịp thuộc SẢN PHẨM (xem §1) |

### Vừa xong (3 cycle cuối)

- **UPDATE-118** — **BA cổng thường trực** nay canh ba bảo đảm mà `CLAUDE.md` §4b đòi nhưng
  trước đây không ai thi hành: cờ config phải có người đọc · không L3 view nào đọc record chưa
  tồn tại (7/7 deriver sạch, **có test sever-restore tự chứng minh cổng bắn được**) · chỉ MỘT
  bảng màu trạng thái. Nhận ra 14 bug của 115/116/117 đều thuộc **hai họ**, và nợ thật là
  **thiếu cổng**, không phải 14 bug rời.
- **UPDATE-117 `D-M3-15`** — **quét cơ chế mồ côi** thay vì chờ lỗ thứ tư. 5 cờ config không ai
  đọc (3 cờ **mô tả SAI hành vi**: phạm vi pin 60/110 vs thật 62,5/117,6 km; bucket metrics 15′
  vs thật 60′) + 14 hàm public không caller, gồm `trajectory.py` module CHẾT mang **bảng màu thứ
  hai xung đột** với dashboard. Nay có **cổng thường trực** `test_config_flags_wired.py`.
- **UPDATE-116 `D-M3-13`** — **tầng 5 chưa từng đo được gì**: có hàm gộp, có
  `health_guardrail`, nhưng `_system_metrics` không mang khoá sức khoẻ nào ⇒ `TREO — THIẾU DỮ
  LIỆU` trên mọi pair. Lần thứ BA cùng mẫu `D-R12` trong hai ngày, và cả ba lần UPDATE của chính
  tôi đã tuyên bố cơ chế hoạt động. Sau khi nối, đo đường thật: nghỉ **+352,8′**,
  `work_span_p90` **−17,8′**, verdict OK, scope **90/90**.
- **UPDATE-115 `D-M3-11`** — **6 rò rỉ thông tin tương lai** ở L3 view l1r. Vào từ MỘT test đỏ
  (idle 247,48′ > online 246′); hai giả thuyết rẻ (làm tròn · lệch hai bảng) bị **loại bằng đo**.
  Bài học tái dùng được: khi bắt được một lỗi *thuộc một họ*, **viết phép thử cho cả họ rồi quét**
  — 4/6 chỗ tìm ra bằng probe, không bằng đọc code (tôi đã đọc chính hàm đó mà vẫn không thấy).
- **UPDATE-114** — 5 lỗ đường ống A/B do vòng thiết kế `D-M3-04` bắt, trong đó **lỗ (b) là do
  chính tôi tạo ra hôm trước** (cổng tầng 5 trên TỔNG cohort ⇒ kênh thưa pha loãng ~10× ⇒ cổng
  canh nhiễu). Vòng soi cũng **bác 2 chỗ sai trong brief của tôi** bằng đo.


- **`D-M3-01`** — mẫu số adherence hỏng ở 3 tầng. `shift_extend` báo **1,000** trong khi sự thật
  **0,473** (thổi **2,1×**). Đã sửa → **0,475**. Behavior-neutral: fingerprint per-actor 15/15 IDENTICAL.
- **`D-M3-10`** — luật *"mọi arm báo adherence, lệch ⇒ TREO"* **chưa từng được thi hành** (đường ống
  A/B tham chiếu `adherence` **0 lần**; artifact 35–39 **không có khoá nào**). Đó là **lý do trực tiếp**
  `D-M3-01` sống qua 39 artifact. Đã nối cổng **BẤT KHẢ** + 9 test.
- **`T-047`** — spec hợp đồng dữ liệu phản thực, 1.280 dòng, `WAITING-VERDICT`.

---

## §3. HÀNG ĐỢI — đọc `tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` để có acceptance đầy đủ

| # | Việc | Chi phí | Trạng thái |
| --- | --- | --- | --- |
| 1 | ~~**`L1-04`**~~ | — | ✅ **XONG (UPDATE-107)** — n=100 BÁC giả thuyết "28% mất hẳn": Δ=0 tuyệt đối; đó là gap LOGGING đã đóng bởi `D-M3-01`. Fix giữ (đúng `R-01`). ⚠ Kèm flaw #6 SUITE bắt: event MA sau khi áp — đã sửa (`mark_outcome_logged`) |
| 2 | ~~**Cổng THỐNG KÊ**~~ | — | ✅ **XONG (UPDATE-107)** — z Poisson-binomial `\|z\| > 4` NỐI vào `run_ladder` thật; null đọc từ **nominal của run** (không hardcode); không treo oan arm tuân-thủ-tuyệt-đối |
| 3 | 🔴 **`E10` advisor-cũng-nhiễu** — **quan trọng nhất còn lại** | ~1–1,5 ngày | ✅ **XONG (UPDATE-110)** — **mất λ thì +6.016đ còn 57–65%**; trigger chờ-lâu SỤP; không thấy herding; 9 lỗi script đo bị vòng soi bắt đã sửa. Chờ Cường: visual gate (artifact d8c58414) + phán quyết |
| 4 | **`D-M3-04`** multiday A/B cho `rest_window` | ~4–6 giờ | 🟢 **READY** — 3 câu hỏi thiết kế Cường đã duyệt (TB ngày 2..N bootstrap theo SEED · days=3 n=100 · prereg mới cho dải T thấp); acceptance đã sửa theo 5 lỗ UPDATE-114. ⚠ Trong cycle phải **nối `health_guardrail(actor_ids=…)` vào `aggregate_health_guardrail`** — cơ chế có, đường chạy chưa (đúng họ lỗi (a), đừng lặp) |
| 5 | Cycle **đường SẢN PHẨM** — 13 finding sev CAO | ~1–2 ngày | chưa phản biện |
| 6 | **`E9`** chọn lọc TRONG kênh | ~1 ngày | chờ |

**Vì sao `E10` đứng trên mọi thí nghiệm kênh khác** — và đây là điều một agent mới dễ bỏ sót:

Advisor nhận `expected_demand_field` = **đúng λ mà generator dùng** (`src/gsm_sim/demand.py:76`),
trong khi tài xế chỉ nhận `λ × nhiễu per-actor`. Ngoài đời advisor **không bao giờ** có λ. Vì thế
`T-047` §4 hàng 1 xếp con số chủ lực **+6.016đ/người/ngày vào cột LUNG LAY** — *"không phải sai 2× mà
sai về bản chất nguồn tin"*. `E10` phải trả lời:

> **+6.016đ còn lại bao nhiêu khi advisor mất λ?**

Nếu nó sụp về gần 0 thì đó là kết quả quan trọng nhất dự án từng đo, và **phải báo đúng như vậy** —
không được im lặng chọn arm oracle để trình bày.

### Việc KHÔNG làm (đọc `PLAN-...-hang-doi` §8 trước khi đề xuất bất cứ gì)

Mô hình hoá **hậu quả của mệt** (huỷ vĩnh viễn) · **`E1`** 4 cơ chế trọng tài ngân sách (headroom ≈0đ,
`D-M3-07`) · sửa **`window_past`** · **xin GSM thêm dữ liệu** · thêm "chờ lâu" làm **input thứ hai**
cho luật positioning (sẽ đo ra ≈0 — xem §5 bẫy #7).

---

## §4. Tài liệu source-of-truth (đọc khi task chạm tới)

| File | Khi nào đọc |
| --- | --- |
| `specs/advisor-objective-model-v2.md` | Bất cứ gì chạm hàm mục tiêu. **§1.2b** = ranh giới sức khoẻ, C2 huỷ, `C2′` thay |
| `specs/real-data/data-contract-counterfactual.md` | Bất cứ gì chạm dữ liệu. **§4 (dòng 746)** = 17 kết luận xếp VỮNG/LUNG LAY/KHÔNG THỂ KIỂM |
| `specs/simulation/d-m3-01-adherence-denominator-fix.md` | Chạm adherence / mẫu số / thước đo |
| `specs/adherence-measurement.md` | Bản đồ chung hai đường đo. ⚠ **ĐỌC ĐÍNH CHÍNH 2026-07-30** — nó đảo một kết luận của spec: **hai đường hiện KHÔNG JOIN ĐƯỢC** (topic rời nhau · sản phẩm không emit `decided` · `followed` mang hai nghĩa · kênh không giao nhau) |
| `research/audit/2026-07-27-current-state/README.md` | **TRƯỚC KHI TRÍCH BẤT KỲ SỐ NÀO.** Có cảnh báo chung: artifact 31–39 đo bằng thước chưa được kiểm, và 31–35 **BỊ TREO** |
| `tracking/QUYET-DINH-2026-07-30-nam-diem.md` | 5 quyết định V-15 + **cổng TIỀN-ĐĂNG-KÝ** của `rest_window` (khoá, không sửa sau khi đo) |
| `tracking/VISION-ALIGNMENT-2026-07-29.md` | **NEO của mọi plan mới** — đối chiếu từng vế tầm nhìn Cường ↔ cái đã có ↔ gap ↔ route. *Plan nào không trỏ được về một vế ở đây thì phải tự hỏi vì sao tồn tại.* ⚠ Doc-graph 2026-07-30 phát hiện file này MỒ CÔI (0 inbound link) dù tự tuyên bố là NEO — đã nối lại tại đây |

---

## §5. 🔴 MƯỜI BẪY ĐÃ SẬP THẬT — đọc trước khi tin bất kỳ con số nào

Đây là phần giá trị nhất của file này. Mỗi bẫy dưới đây **đã làm một con số bị báo sai cho Cường**.

**1. Đo bằng thước chưa được kiểm.** `shift_extend` báo adherence **1,000** suốt **39 artifact** vì
event chỉ được ghi khi tài xế ĐÃ THEO ⇒ mẫu số chỉ chứa người đã theo ⇒ 1,0 **theo cấu trúc**.
Họ lỗi này có tên: **`BUG-EVAL-ARGMAX`**. ⇒ **Trước khi tin một Δ, kiểm cổng `verdict` của arm đó.**

**2. Test không thể ĐỎ.** Test regression của họ lỗi `F-1` lại **khắc chính lỗi đó thành kỳ vọng**:
assert cả `decided` và `followed` bằng **CÙNG một biến đếm** ⇒ đồng nhất thức. ⇒ **Mọi cổng mới phải
được CHỨNG MINH là đỏ được**, không chỉ mô tả.

**3. Trộn ĐƠN VỊ.** `decision_adherence` đếm theo **QUYẾT ĐỊNH** (gộp bucket 30′); coin đếm theo
**LẦN HỎI**. Trộn hai cái cho ra "sai 3,2×" thay vì **2,1×** — và cho ra "LỆCH" **oan** cho một kênh
đang đúng. ⇒ **Luôn nói rõ đơn vị. Cấm khoá `adherence` trần.**

**4. Cơ chế bảo vệ chỉ sống trên giấy.** Hai lần: `D-M3-08` (4/6 cơ chế enforce của khung BA LỚP
không tồn tại) và `D-M3-10` (cổng hợp lệ A/B tham chiếu `adherence` 0 lần). ⇒ **`grep` xem cơ chế
mình vừa viết trong tài liệu có tồn tại trong code không.**

**5. Arm đối chứng KHÔNG sạch.** `DET-01`: tắt cờ `cadence.enabled` cũng tắt luôn keyed coin ⇒ arm
đối chứng có adherence cao hơn ~10đp vì lý do không liên quan. Con số đã báo **−3.048đ**, sự thật
**−1.530đ**. ⇒ **Đo adherence hiệu dụng của arm đối chứng TRƯỚC khi tin Δ.**

**6. `assert_crn` KHÔNG phải bằng chứng bit-identical.** Nó chỉ so danh sách đơn, mà đơn sinh **ngoài**
world ⇒ trả `True` dù mọi quỹ đạo actor đã lệch. ⇒ **Dùng fingerprint PER-ACTOR** (bản chạy được ở
`scripts/probe_adherence_truth.py`).

**7. "Cơ chế đúng, ĐỘ LỚN sai" — sập 3 lần.** `DET-01` sai 5,7× · chẩn đoán `window_past` sai 5,4× ·
mức thổi 3,2× vs 2,1×. ⇒ **Soi độc lập bắt được cơ chế nhưng thường sai độ lớn. Tự đo lại độ lớn
trước khi trích.** (~1/4 finding của soi độc lập là sai hoặc phóng đại.)

**8. "Test đỏ lệch tí xíu ⇒ chắc là lệch ĐO."** `test_bug01_idle_never_exceeds_online_time` đỏ với
idle **247,48′** vs online **246,00′** — vượt **1,48′**. Phản xạ đầu tiên của tôi: lệch hai bảng, ghi
nợ, đi tiếp. Thực tế là **rò rỉ thông tin tương lai**: view hỏi lúc 23:00 nhận dwell bắt đầu **23:03
và 23:27**, và probe sau đó tìm thêm **5 chỗ nữa** ở 3 deriver (UPDATE-115). ⇒ **Vượt một bất biến
VẬT LÝ thì độ lớn không nói gì về mức nghiêm trọng** — 1,48′ và 1.054′ cùng nghĩa là "sai cơ chế".
Việc cứu tình huống chỉ là **dump dữ liệu ra xem**, một câu lệnh. Và: **4/6 chỗ tìm ra bằng probe,
không bằng đọc code** — tôi đã đọc chính hàm đó khi sửa chỗ đầu mà vẫn không thấy hai field kia.
⇒ **Bắt được một lỗi thuộc một họ thì viết phép thử cho CẢ HỌ rồi quét, đừng soi bằng mắt.**

**9. "Cơ chế TỰ QUẢNG CÁO trong docstring nhưng không ai nối nguồn" — sập 3 LẦN trong 2 ngày.**
`D-R12` · UPDATE-114 lỗ (a) (`adherence_a` có field + comment *"arm đối chứng cũng phải được ĐO"*
nhưng không cổng nào đọc) · UPDATE-116 `D-M3-13` (tầng 5 có hàm gộp + `health_guardrail` đầy đủ,
nhưng `_system_metrics` **không mang khoá sức khoẻ nào** ⇒ verdict `TREO — THIẾU DỮ LIỆU` trên
mọi pair, và `grep` cho thấy **0 artifact** từng mang tầng 5). Cả ba lần, **UPDATE của chính tôi
đã tuyên bố cơ chế hoạt động**. ⇒ **Trước khi tin một cổng, ĐO đầu ra của nó trên một pair
THẬT** — đừng đọc docstring, đừng tin UPDATE cũ, kể cả UPDATE của mình. Đối trọng duy nhất đã
chứng minh hiệu quả: **test sever-restore** (ngắt cơ chế ⇒ phải đỏ) và `grep` artifact đã lưu.

**10. Một giá trị `None` KHÔNG phải bằng chứng cơ chế mù.** Sau khi nối tầng 5, tôi đọc
`a_mean['n_actors_scope']` ra `None` và kết luận *"`touched_actors` trả rỗng ⇒ cổng vẫn chấm toàn
cohort"* — sắp ghi thành lỗi thứ tư. Thực tế: `_mean` chỉ gộp 12 khoá liệt kê nên khoá đó **vắng
khỏi dict**, còn `touched_actors(rb)` trả đúng **90/90**. ⇒ Với `.get()` trả `None`, phân biệt
*"giá trị là None"* với *"khoá không tồn tại"* trước khi kết luận. (Phát hiện sai vẫn dẫn tới một
fix thật: mẫu số **phải** hiện trong artifact — `OK` trên 90/90 và trên 9/90 nghĩa khác hẳn.)

### Bẫy vận hành

- `pytest -q` từ root **bỏ 56 test** đường sản phẩm (§2).
- `_cfg_with(..., coverage=...)` mặc định `"single"`; truyền `actor_id=None` cùng nó ⇒ **không ai được
  advisor phủ** ⇒ bạn đang đo cái tắt của chính mình.
- `_agg()` trong test **cộng dồn mọi trường số**, kể cả `decision_adherence` ⇒ trường đó là **tổng tỷ
  lệ** của ~86 tài xế, không phải một tỷ lệ.
- So hash bằng `awk` trên file **CRLF** cho kết quả "KHÁC" sai.
- `TaskStop` để lại child python chiếm CPU (suite 18′ → 90′).
- Con số nào định trích thì **mở artifact JSON gốc** ra đọc — nhiều artifact (31–35) **BỊ TREO**.

---

## §6. Quy trình bắt buộc (rút gọn — bản đầy đủ ở `CLAUDE.md` §3/§4/§4b)

1. **Plan mode trước** mọi thay đổi code/contract/docs quan trọng. Hỏi lại điều chưa rõ, đừng đoán.
2. **UPDATE-### sau mỗi thay đổi** có ý nghĩa, theo `tracking/updates/UPDATE_TEMPLATE.md`. Phải có mục
   **`Adversarial self-review / flaws found`** — không được bỏ vì test xanh.
3. **Nhắc lại `PENDING-REVIEW` sau MỖI update.** Hoãn ≠ waive.
4. **Chỉ commit/push khi Cường yêu cầu.**
5. Bất biến deterministic: **exact-repeat**. Regression stochastic: **≥5 seed**. Phân phối/hiệu chỉnh:
   **≥30 seed**. So biến thể-vs-biến thể: **≥100 seed** ghép cặp.
6. Chưa reproduce hoặc chưa chứng minh root cause ⇒ ghi **`UNRESOLVED`**, không ghi "fixed".
