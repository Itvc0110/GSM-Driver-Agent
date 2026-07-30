# PLAN cấp thiết — NHỊP thuộc SẢN PHẨM, không thuộc SIM

Ngày: 2026-07-29 · Trạng thái: **chờ Cường gật để thi công** (đây là đổi mặc định của sim, không
phải fix nội bộ) · Nguồn: chất vấn của Cường 2026-07-29.

---

## 1. Cường đúng, và tôi đã sai

> *"trong sim đâu cần advisor im sau khi tài xế không tuân theo? sim để so sánh giữa thế giới
> không có advisor và hoàn toàn tuân thủ advisor mà? Nên advisor đâu cần im. Chỉ deploy thật mới
> có tính năng đó! Tôi có đang hiểu sai không?"*

**Không hiểu sai. Tôi đã lập luận sai ở cycle ĐA-04.** Lập luận cũ của tôi là *"cooldown và ngân
sách là thuộc tính của LỜI KHUYÊN nên phải có ở cả hai bên, vì A/B phải đo đúng thứ sẽ ship"*.
Nghe hợp lý nhưng nó **trộn hai câu hỏi khác nhau**:

| Câu hỏi | Ai trả lời | Cần nhịp không? |
| --- | --- | --- |
| *"Nội dung lời khuyên có giá trị không?"* — trần giá trị của advisor | **SIM** | **KHÔNG** |
| *"Sản phẩm như đang thiết kế sẽ giao được bao nhiêu phần của trần đó?"* | SIM (một arm riêng) | Có |
| *"Advisor nói bao nhiêu là không phiền?"* | **SẢN PHẨM** + người thật | Không đo được ở sim |

Sim tồn tại để trả lời câu **thứ nhất**. Đưa cooldown/ngân sách vào mặc định của sim làm nó trả
lời câu thứ hai trong khi mọi người đọc nó như câu thứ nhất.

**Bằng chứng rằng đây không phải chuyện lý thuyết** — chính số liệu tôi đo được:
- Ngân sách FIFO làm `shift_plan` chiếm hết suất ⇒ **tương tác +3.249đ**. Tức nhịp đang **làm
  bẩn phép đo giá trị từng kênh**, đúng cái sim sinh ra để đo.
- Con số headline `−1.530đ CI[−2.401,−673] SIG` mà tôi báo cho Cường là **giá của một ràng buộc
  UX**, không phải một sự thật về advisor. Nó thuộc `Q-09` (câu hỏi sản phẩm), không thuộc sim.
- `rest_window` nói 0 lần — tôi từng đổ cho ngân sách; hoá ra **sai** (100% số nén là ma).

## 2. Ranh giới đúng — sửa lại bảng của UPDATE-099 §2

| Cơ chế | SIM (mặc định) | SẢN PHẨM | Vì sao |
| --- | --- | --- | --- |
| `dismissed_for_window` (nút Bỏ qua) | ❌ không bao giờ | ✅ | Đã chốt 2026-07-29. Phản ứng của người trước UI |
| **`shift_budget_exhausted` (6/ca)** | **❌ TẮT mặc định** ⟵ **ĐỔI** | ✅ | **Ngân sách CHÚ Ý của người nghe** — là ràng buộc UX, không phải thuộc tính của lời khuyên |
| **`topic_cooldown` (20′/chủ đề)** | **❌ TẮT mặc định** ⟵ **ĐỔI** | ✅ | Cùng lý do. Việc "một quyết định chỉ rút một coin" đã do `decision_bucket` 30′ đảm nhiệm — **không cần cooldown để giữ tính đúng đắn của phép đo** |
| `unsafe_while_moving` → QUEUE | (n/a — sim chỉ hỏi lúc idle) | ✅ | An toàn của người thật |
| `decision_bucket` 30′ (một quyết định = một coin) | ✅ **GIỮ** | ✅ | Đây là **hạ tầng ĐO**, không phải nhịp. Bỏ nó thì washout sống lại |
| `_claim_effect` (một quyết định = một lần áp) | ✅ **GIỮ** | (n/a) | Tính đúng đắn, không phải UX |

**Điểm mấu chốt:** cái giữ phép đo khỏi washout là `decision_bucket` + `_claim_effect`, **không
phải** cooldown/ngân sách. Nên tắt nhịp trong sim **không** làm sống lại lỗi cũ — đã chứng minh
bằng `test_coin_is_keyed_even_when_cadence_off` và `test_one_decision_one_effect_application`.

## 3. Việc phải làm

| # | Việc | Ghi chú |
| --- | --- | --- |
| 3.1 | `configs/pilot_dongda.yaml`: `advice.cadence.enabled: true → false` | **Đổi mặc định của sim.** Cơ chế giữ nguyên, chỉ đổi mặc định |
| 3.2 | Viết lại docstring `cadence.py` §ranh giới + comment config theo bảng §2 | Docstring hiện đang khẳng định điều ngược lại — nó sẽ dạy sai người sửa sau |
| 3.3 | Test khoá chiều mới: mặc định của `pilot_dongda.yaml` phải cho **0 event `advice_suppressed`**; và một test khẳng định **tắt nhịp KHÔNG làm washout sống lại** (hai đơn vị adherence vẫn hội tụ) | Chiều ngược của `test_cadence_config_actually_parsed_from_yaml` hiện tại — test đó đang pin `enabled is True`, phải sửa |
| 3.4 | **Đảo nhãn mọi artifact**: `OFF_*` là arm **CHÍNH** (trần giá trị advisor), `ON_*` là arm **sản phẩm**. Cập nhật `README` audit + `UPDATE-099` + `HANDOFF` | Không cần chạy lại — chỉ đọc lại số đã có theo nhãn đúng |
| 3.5 | Q-09 phát biểu lại: **không phải** *"nhịp có đáng −1.530đ không"* mà *"sản phẩm giao được bao nhiêu phần của trần +8.488đ, và mức nào là không phiền"* | Câu hỏi cũ hỏi sai |

## 4. Số phải đọc lại theo nhãn mới (artifact 37, không chạy lại)

| Arm | Nhãn CŨ | Nhãn ĐÚNG | Δ payout/tài xế |
| --- | --- | --- | --- |
| `OFF_all` | "arm đối chứng" | **TRẦN giá trị advisor (4 kênh + vị trí)** | **+8.488đ** |
| `OFF_nosp` | "ô thứ tư của lưới" | Trần, bỏ `shift_plan` | +6.789đ |
| `ON_all` | "arm chính" | Sản phẩm-như-thiết-kế | +5.624đ |
| `ON_nosp` | — | Sản phẩm, bỏ `shift_plan` | +7.173đ |
| `ON_pos_only` | — | Sản phẩm ở **config ship** hiện tại | +4.469đ |

⇒ **Trần là +8.488đ; sản phẩm-như-thiết-kế giao +5.624đ ⇒ nhịp đang cắt mất ~1/3 trần.** Đó là
cách phát biểu đúng, và nó làm `D-ĐA04-03` (chia ngân sách) thành việc đáng làm nhất — vì phần
lớn chỗ mất đó là do FIFO, không do bản thân việc nói ít.

⚠ ~~`OFF_nosp` < `OFF_all` ⇒ ở trần `shift_plan` có giá trị +1.700đ, ngược ĐA-07~~ —
**ĐÃ GIẢI, con số đó là nhiễu n=30.** E5 ở n=100 cho **+53đ ns** ⇒ `shift_plan` trung tính khi
đứng một mình, KHỚP ĐA-07. Xem §4c.

## 4b. 🔬 BẪY PHẢN CHỨNG ĐÃ SẬP — và nó dạy một LUẬT ĐO mới

Theo đúng §5.1, tôi viết test phản chứng **trước** khi đổi mặc định: *"tắt nhịp thì hai đơn vị
adherence vẫn phải hội tụ"*. Nó **ĐỎ cả 5 seed** — decision 0,674 vs event 0,500.

Tôi đã suýt kết luận *"cooldown đang gánh tính đúng đắn, không được đổi mặc định"*. **Sai.** Đo
tiếp thì nguyên nhân khác hẳn:

| arm | decision adherence | danh nghĩa | **lệch** | event | event/bucket **được nghe theo** | event/bucket **bị bỏ qua** |
| --- | --- | --- | --- | --- | --- | --- |
| nhịp BẬT | 0,658 | 0,603 | **+0,055** | 0,653 | 1,02 | 1,04 |
| nhịp TẮT | 0,674 | 0,617 | **+0,057** | 0,500 | **2,38** | **4,93** |

**Hiệu ứng chọn lọc: số lần HỎI phụ thuộc CÂU TRẢ LỜI.** Không cooldown thì bucket **bị bỏ qua
bị hỏi lại 4,93 lần** (hỏi mãi tới hết ca), còn bucket **được nghe theo chỉ 2,38 lần** (được
nghe ⇒ `acc` tăng ⇒ kênh thôi hỏi). Nên event-level **đếm thiếu** các bucket followed.

**Washout KHÔNG sống lại:** washout thổi phồng **decision**-level, mà decision-level ở đây ổn
định — lệch danh nghĩa **+0,057 khi tắt vs +0,055 khi bật**, như nhau. ⇒ **Quyết định của Cường
đứng vững; tiền đề test của tôi mới là cái sai.**

### ⚠ LUẬT ĐO MỚI (phải vào harness)

> **Ở arm KHÔNG NHỊP, không được dùng `event_adherence` — chỉ dùng `decision_adherence`.**
> Sai luật này là đọc sai **17 điểm phần trăm**.

Đây là hệ quả trực tiếp của verdict "hai tên" mà Cường chốt ở Cycle W (`decision_adherence` +
`event_adherence`, cấm khoá `adherence` trần): nay đã biết **khi nào cột nào dùng được**. Trước
cycle này ta có hai cái tên mà không có luật chọn.

Test khoá: `test_tat_nhip_khong_lam_washout_song_lai` — 5 seed, assert decision-level sát danh
nghĩa ở **cả hai** arm (bất biến đúng), không assert hội tụ (bất biến sai).

## 4c. ✅ E5 / artifact 38 — tương tác lần đầu CÓ CI, và nó ĐỔI HAI kết luận

n=100 ghép cặp (seed 4200–4299), 4 world/seed, ghi per-seed rồi bootstrap:

| Ước lượng | mean | CI95 | |
| --- | --- | --- | --- |
| **Tương tác ngân sách FIFO** | **+2.207đ** | [+1.077, +3.372] | **SIG** |
| Giá của nhịp **khi CÓ** `shift_plan` | −2.466đ | [−3.420, −1.570] | **SIG** |
| Giá của nhịp **khi KHÔNG có** `shift_plan` | **−259đ** | [−1.111, +589] | **ns** |
| Bỏ `shift_plan` khi nhịp BẬT | +2.259đ | [+1.161, +3.323] | **SIG** |
| Bỏ `shift_plan` ở TRẦN (nhịp tắt) | **+53đ** | [−974, +1.102] | **ns** |
| Tương tác trên `gini_payout` · `served_rate` · `others_payout` | +0,0043 · +0,52đp · +196k | — | đều **SIG** |

**Kết luận 1 — NHỊP TỰ NÓ GẦN NHƯ MIỄN PHÍ, và nay có bằng chứng thống kê.** Artifact 37 chỉ
cho điểm ước lượng +384đ; n=100 cho **−259đ với CI trùm 0** ⇒ *không phân biệt được với 0*.
Nói cách khác: **cái đắt không phải việc advisor nói ít — mà là cách chia ngân sách.**

**Kết luận 2 — `D-ĐA07-recheck` được GIẢI, và nó ỦNG HỘ ĐA-07 chứ không bác.** Tôi vừa báo với
Cường rằng *"ở trần, `shift_plan` đáng +1.700đ ⇒ ngược ĐA-07"*. **Con số đó là nhiễu n=30.**
Ở n=100, bỏ `shift_plan` ở trần chỉ **+53đ, ns** ⇒ kênh này **trung tính khi chạy một mình**,
khớp đúng kết luận ĐA-07 (*"không hiệu quả thì TẮT"*).

Nhưng E5 cho ĐA-07 một lý do **mạnh hơn** lý do ban đầu: `shift_plan` không chỉ trung tính —
**dưới ngân sách FIFO nó ĐỘC HẠI, gây hại +2.259đ SIG** vì chiếm suất của kênh có tác dụng.
Tức: *kênh trung tính khi đứng một mình, nhưng đắt khi phải chia ngân sách chung.*

⇒ Đây là **bằng chứng mạnh nhất tới nay cho `D-ĐA04-03`**: toàn bộ chi phí của nhịp là chi phí
của FIFO, và nó SIG với CI không chứa 0.

⚠ Sửa lại §4 và §6 của chính plan này theo E5 — bảng §4 dùng số n=30, đã lỗi thời về ĐỘ LỚN.

## 4d. Artifact 39 + NULL-0 — hai điều đóng lại trong cùng ngày

**Artifact 39** (`39-da07-recheck-tran-n100.json`, seed khác, ước lượng ghép cặp riêng, nhịp TẮT,
n=100): giá trị của `shift_plan` = **−451đ CI[−1.499, +608] ns**. Khớp artifact 38 (+53đ ns khi bỏ
nó) ⇒ **hai phép đo độc lập cùng kết luận `shift_plan` trung tính** ⇒ `D-ĐA07-recheck` **ĐÓNG**,
ĐA-07 đúng. Trần giá trị advisor ở n=100: **+7.666đ** đủ kênh · **+8.117đ** bỏ `shift_plan`.

**NULL-0 — tôi phải rút lại một câu của chính mình.** Tôi viết ở §4c rằng đây là *"bằng chứng mạnh
nhất tới nay cho `D-ĐA04-03`"*. Đúng về **cơ chế**, nhưng tôi đã bỏ sót hệ quả **giá trị**:

- giải thưởng mà một trọng tài khéo hơn có thể giành = tương tác = **+2.207đ SIG**;
- nhưng **bỏ `shift_plan` khi nhịp bật = +2.259đ SIG** — ĐA-07 đã lấy gần hết bằng **một dòng YAML**;
- và ở **đúng cấu hình sản phẩm** (nhịp ON, `shift_plan` OFF) giá của nhịp = **−259đ ns**.

⇒ **Ngân sách chú ý hiện tại không tốn khoản tiền nào đo được ⇒ E1 có headroom ≈ 0đ.** E1 →
`D-M3-07` `DEFERRED-CÓ-ĐIỀU-KIỆN`; spec thi công đầy đủ (7 agent) vẫn lưu ở
`specs/simulation/e1-budget-arbitration-4-mechanisms.md` để mở lại khi bật một kênh ÂM.

**Lever đáng đào thay vào đó — `E9`:** `shift_plan` trung tính nghĩa là lời khuyên tốt và tệ của nó
**triệt tiêu nhau**. Cả bốn cơ chế của E1 đều *chia suất GIỮA các kênh*; **không** cơ chế nào **chọn
lọc TRONG một kênh**. Artifact 38 và 39 đều không nói gì về lever này.

## 5. Rủi ro của chính plan này

1. ✅ **Phản chứng ĐÃ CHẠY và đã sập — xem §4b.** Nó không bác bỏ plan (decision-level ổn
   định ⇒ washout không sống lại) nhưng dạy ra một **luật đo mới** mà không ai biết trước:
   ở arm không-nhịp, `event_adherence` bị hiệu ứng chọn lọc làm lệch 17đp. Bài học: **viết
   phản chứng trước khi đổi mặc định là đúng** — nó đã bắt được một thứ tôi không hình dung ra,
   và nếu tôi đổi trước rồi mới test thì sẽ đọc số sai mà không biết.
2. **Mất khả năng dự báo sản phẩm nếu bỏ hẳn cơ chế.** Nên **không xoá** cadence — chỉ đổi mặc
   định. Arm sản phẩm vẫn chạy được bằng một cờ.
3. **Artifact cũ dễ bị đọc sai nhãn.** Phải sửa README audit trong cùng commit, không để sau.

## 6. Sinh ra từ plan này

- ✅ **`D-ĐA07-recheck` — ĐÃ GIẢI ngay trong phiên bằng E5 (artifact 38).** Kết luận: ĐA-07
  **đúng**, và có lý do mạnh hơn lý do ban đầu. `shift_plan` ở trần: **+53đ ns** (trung tính khi
  đứng một mình); nhưng **dưới ngân sách FIFO nó gây hại +2.259đ SIG**. ⇒ Giữ TẮT là đúng, và
  nếu bao giờ bật lại thì **phải sửa cách chia ngân sách trước**. Artifact 39 (đang chạy) là
  phép đo độc lập cùng câu hỏi trên bộ seed khác — dùng để đối chứng, không phải để thay thế.
- `Q-09` viết lại theo §3.5.
