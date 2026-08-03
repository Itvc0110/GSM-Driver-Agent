# QUYẾT ĐỊNH 2026-08-03 — KHUYÊN MỀM KHÔNG ĐO

Ngày: **2026-08-03** · Người quyết: **Cường** · Ghi bởi: agent (UPDATE-128) · Trạng thái: **HIỆU LỰC**

## 0. Chỉ thị nguyên văn

> *"tôi duyệt D-M3-04, việc khuyên nghỉ nên defer thành khuyên mềm, không cho vào để đo hiệu quả
> trong sim, trong UI cũng không nên có trace đồng ý làm theo hay không làm theo khi gợi ý — tương
> tự đối với thời tiết, Khánh đang lo phần đó, nhưng làm docs note lại, kiểm tra mọi docs liên quan
> và cập nhật."*

Agent nêu lại **hai điểm không được tự đoán**, Cường chốt cùng ngày:

| Câu hỏi | Cường chốt |
| --- | --- |
| `D-M3-04` **chính là** phép A/B đo Δ tiền của kênh `rest_window`; "duyệt nó" và "không đo khuyên nghỉ trong sim" chỉ hai hướng ngược nhau. Vậy nó thành cái gì? | *"**thử D-M3-04 trước, nếu có ý nghĩa thì giữ, không thì revert và khuyên mềm**"* |
| Bỏ trace đồng ý/không đồng ý thì cơ chế im lặng trong pha (ĐA-04, đã duyệt) xử lý sao? | *"**Giữ nút ẩn, bỏ nút Làm theo**"* |

---

## 1. Ba điều được quyết — và cái nào có điều kiện

| # | Nội dung | Trạng thái |
| --- | --- | --- |
| **QĐ-1** | **UI: khuyên mềm KHÔNG có trace đồng ý/không đồng ý.** Thẻ mềm chỉ có nút **Ẩn** (+ *Vì sao*); **không** có "Làm theo". Không topic mềm nào vào tử số/mẫu số adherence. | **VÔ ĐIỀU KIỆN** — hiệu lực ngay |
| **QĐ-2** | **Thời tiết là khuyên mềm** — cùng ranh giới QĐ-1. Implement thuộc **Khánh**; repo đặt sẵn đường ray + cổng. | **VÔ ĐIỀU KIỆN** — hiệu lực ngay |
| **QĐ-3** | **Khuyên nghỉ → khuyên mềm, bỏ khỏi phép đo hiệu quả.** | **CÓ ĐIỀU KIỆN** vào kết quả `D-M3-04` (§3) |

⚠ **Đọc kỹ QĐ-3**: Cường **không** đóng `D-M3-04` — ông chọn **thử trước**. Nên hôm nay
`rest_window` vẫn ở nhóm ĐƯỢC ĐO (`MEASURED_TOPICS`), và chỉ chuyển sang `SOFT_TOPICS` khi phép đo
cho kết quả theo đúng luật ở §3. Chuyển sớm là tự ý; giữ mãi sau khi có số âm cũng là tự ý.

---

## 2. Vì sao đây là RANH GIỚI, không phải chi tiết UI

Đo *mức nghe lời* của một lời khuyên sức khoẻ **chính là** biến sức khoẻ thành chỉ tiêu để tối ưu.

Cơ chế cụ thể, không phải lo xa: một khi `rest_adherence` tồn tại như **một con số trong bảng**, nó
sẽ được nhìn như thứ cần cải thiện — và *"cải thiện tỷ lệ tài xế chịu nghỉ"* là tối ưu hoá **trên**
sức khoẻ. Đó đúng là thứ `specs/advisor-objective-model-v2.md` §1.2b cấm, bằng đúng lập luận đã dùng
để huỷ `C2`:

> mọi cơ chế cho mệt một hậu quả đều tạo `∂payout/∂F` — một tỷ giá sức-khoẻ↔tiền. Viết tỷ giá đó
> vào world thay vì vào objective **không xoá tỷ giá; nó chỉ xoá NHÃN của tỷ giá.**

Nút "Làm theo" trên thẻ nghỉ là **cùng một tỷ giá, ở tầng thứ ba** — tầng sản phẩm. §1.2b đã bịt
tầng objective và tầng world; văn bản này bịt tầng còn lại.

**Và nó bịt một lỗ thật, không phải giả thuyết.** `PHAN-QUYET-2026-07-29` cấm mô hình hoá hậu quả
của mệt trong sim, nhưng **không** nói gì về việc sản phẩm đếm mức nghe lời. Nên tỷ giá bị chặn ở
sim vẫn có thể mọc lại ở UI — bằng một trường trong event log, im lặng, và **không cổng nào bắt**.

---

## 3. `D-M3-04`: luật quyết định — ĐĂNG KÝ TRƯỚC KHI ĐO

Câu *"nếu có ý nghĩa thì giữ, không thì revert"* phải được dịch thành thứ máy chấm được **trước khi
thấy số**. Nếu không, đây đúng là mẫu lỗi tệ nhất của repo: đọc số rồi mới chọn cách diễn giải —
họ lỗi `BUG-EVAL-ARGMAX` (bẫy #1 của `BOOTSTRAP-SESSION.md` §5).

Luật đã ghi vào `specs/simulation/d-m3-04-multiday-prereg-locked.json` → khoá `luat_quyet_dinh`.

> ### ✅ CƯỜNG XÁC NHẬN BẢN DỊCH — 2026-08-03, TRƯỚC khi đo
>
> Agent nêu tường minh **bốn chỗ bản dịch tự quyết** và hỏi lại; Cường: ***"giữ nguyên bản dịch"***
> ⇒ giữ cả bốn:
>
> 1. *"có ý nghĩa"* = có ý nghĩa **THỐNG KÊ**, không phải một ngưỡng tiền tuyệt đối;
> 2. hai điều kiện **AND** mà chỉ thị gốc không nói (tầng 5 không suy giảm · 0 STOP bắn) — chúng làm
>    nhánh **GIỮ khó hơn** câu nói gốc;
> 3. **`ns` xếp vào REVERT**, không xếp vào *"thiếu power, chạy thêm seed"*;
> 4. chấp nhận **MDE ~1.000đ** ở n=100 ⇒ một Δ thật khoảng **+400đ** sẽ ra `ns` ⇒ REVERT, dù hiệu
>    ứng thật là dương.
>
> Và Cường chốt **sau khi được báo trước** rằng theo luật này **REVERT là nhánh gần như chắc chắn**
> (world β=0 không thể sinh Δ dương cho can thiệp tăng nghỉ), nên giá trị thật của việc chạy là ba
> thứ khác: xác nhận dự đoán bằng **đo** thay vì bằng giả định (repo đã 3 lần sai độ lớn khi tin lập
> luận — bẫy #7) · **số sức khoẻ tầng 5** cho kênh nghỉ, thứ chưa ai từng đo · không đóng một kênh
> bằng suy luận.
>
> 🔒 **Từ đây `luat_quyet_dinh` ĐÓNG.** Mọi sửa đổi sau khi đo là vi phạm prereg — **kể cả sửa "cho
> đúng ý ban đầu"**. Nếu số về mà tiêu chí trông sai, thứ được phép làm là **ghi nhận tiêu chí đã
> chọn sai**, không phải đổi tiêu chí.

| Kết quả đo | Hành động |
| --- | --- |
| Δ payout ngày 1..2 **dương và SIG** (CI95 không chứa 0) **VÀ** tầng 5 không suy giảm **VÀ** không STOP-A..D nào bắn | **GIỮ** — `rest_window` ở lại bảng tiền, tiếp tục là kênh được đo |
| Δ ≤ 0, **hoặc** ns, **hoặc** bất kỳ STOP-A..D bắn | **REVERT** — chuyển `rest_window` sang `SOFT_TOPICS`, bỏ mọi claim tiền |

🔴 **Điều phải nói trước, không nói sau:** prereg đã khoá từ **2026-08-01** kỳ vọng **Δ ≤ 0**, vì
world hiện tại không mô hình hoá hậu quả của mệt (world **β=0**) nên mọi can thiệp tăng nghỉ chỉ tốn
thời gian kiếm tiền và không hoàn lại gì. ⇒ **Nhánh REVERT là nhánh được DỰ ĐOÁN TRƯỚC.** Nếu nó
xảy ra thì đó là phép đo **thành công** (mô hình dự đoán đúng), không phải kênh thất bại — và câu
được phép nói là:

> *"trong world không có hậu quả mệt, kênh nghỉ là chi phí thuần"*

**KHÔNG** được nói *"gợi ý nghỉ vô giá trị ngoài đời"*. Hai câu khác nhau đúng ở β, thứ ta không có
dữ liệu để đặt (0 dữ liệu mệt, 0 dữ liệu tai nạn — §1.2b trụ (b)).

---

## 4. Hai VAI của `dismissed` — lẫn hai vai này là làm sai

Đây là chỗ dễ hỏng nhất của quyết định này, nên viết tách:

| Vai | Nghĩa | Ai đọc | Khuyên mềm |
| --- | --- | --- | --- |
| **Nhịp nói** (ĐA-04) | *"đừng nhắc nữa trong pha này"* | `cadence.evaluate` → advisor im | ✅ **GIỮ** |
| **Thước adherence** | *"tài xế KHÔNG đồng ý với lời khuyên"* | `adherence_view` → tử/mẫu số | 🚫 **CẤM** |

Cùng một cú bấm, hai nghĩa. Cường chốt *"giữ nút ẩn"* ⇒ **vai 1 sống** (tài xế vẫn tắt được thẻ
phiền — nếu bỏ luôn thì tài xế mất cách tắt, tệ hơn), **vai 2 chết** (hệ thống không bao giờ suy ra
sự đồng thuận từ đó).

`followed` thì bị cấm thẳng: nó **chỉ có một nghĩa**, và nghĩa đó là vai 2.

---

## 5. Đã thi hành bằng MÁY ở đâu (không phải bằng lời hứa)

Bài học `D-M3-08`/`D-M3-13`: cơ chế chỉ sống trên giấy thì không sống. Nên:

| Bảo đảm | Ở đâu | Chứng minh bắn được |
| --- | --- | --- |
| Registry một nguồn: `MEASURED_TOPICS` / `SOFT_TOPICS` | `src/gsm_core/lifecycle/advice_topics.py` | `assert` hai tập không giao nhau, chạy lúc import |
| Topic mềm **vắng khoá** khỏi `adherence_view` (không phải trả `None`) | `projections.adherence_view` — lọc ở **CẢ HAI** vòng (decision + event) | sever mũi 1 + mũi 2 → **ĐỎ** |
| `POST /advice/action` từ chối `followed` cho topic mềm (**422**) | `advice.AdviceAction._khuyen_mem_khong_nhan_followed` | 9 test parametrize theo `SOFT_TOPICS` |
| **Fail-closed**: topic lạ ⇒ `"unknown"` ⇒ test ĐỎ | `tests/test_advice_topic_registry.py` | sever mũi 3 → **ĐỎ** |
| **Server TRẢ LỜI** thẻ nào là mềm (`GET /advice` → `is_soft_advice`); client **không tự tra danh sách** | `advice.get_advice` đọc `is_soft()`; `cards.js` chỉ đọc cờ | 4 test so **hai bên** (cờ endpoint ↔ registry) + cổng chặn `cards.js` chép lại danh sách |
| Client không vẽ nút "Làm theo" cho thẻ mềm | `ui/web/js/cards.js` chế độ `soft` | kiểm bằng đọc nguồn (repo không có test runner JS — nói rõ là yếu hơn test hành vi) |

⚠ **Một sai lầm đã sửa trong cùng cycle, ghi lại vì lý lẽ của nó rất dễ tái phát:** bản đầu cho
`cards.js` **chép** danh sách `SOFT_TOPICS` sang JS, biện luận *"không có build step chia sẻ hằng
giữa Python và JS thuần"*. Đó đúng là lý lẽ đã dẫn tới `D-M3-17` (UI tự tính tầm pin, lệch engine
1,76×, 1.000 test không thấy vì không test nào so hai bên) — và ở đây thứ bị nhân đôi là một **ranh
giới đạo đức**, không phải một con số. Đường ra không phải build step, mà là **để một bên TRẢ LỜI
thay vì cả hai cùng suy**.

**Vì sao *vắng khoá* chứ không phải `None`:** `None` là tín hiệu *"mẫu số 0 — có thể có bug"*, đúng
thứ `D-M3-01`/`L4-01` đã dùng để tìm ra thước hỏng. Nếu khuyên mềm trả `None` thì nó lẫn vào tín
hiệu báo lỗi, và người sau sẽ đi "sửa" một ranh giới đang chạy đúng.

---

## 6. Hôm nay việc này chặn cái gì — nói thật

Sản phẩm **chưa có** thẻ nghỉ hay thẻ thời tiết nào (`cards.js` chỉ có `brief`/`nudge`/`recap`) ⇒
**không có gì phải tháo**, và cổng hôm nay **không đổi hành vi nào đang chạy**.

Nhưng mặc định thì sai: `_render(...)` mặc định `actionable = true` và `AdviceAction.topic` nhận
**chuỗi tuỳ ý**. Thẻ mềm đầu tiên ai thêm vào sẽ **tự động** có nút "Làm theo" và **tự động** vào
mẫu số — im lặng, và im lặng đúng hướng có hại. Cổng này biến "phải nhớ" thành "không thể quên".

Đó là lý do deliverable là **đường ray + cổng**, không phải sửa một UI chưa tồn tại.

---

## 7. Nợ mở còn lại

| Mã | Nội dung | Ai |
| --- | --- | --- |
| `D-M3-04` | Chạy phép đo (viết `run_pair_multiday`), rồi áp luật §3 | Cường (agent) — **Cycle B, chờ bật đèn** |
| — | Thẻ thời tiết thật: dùng chế độ `soft` của `cards.js`, topic `"weather"` | **Khánh** |
| — | Flutter (`ui/driver_app/`) cũng phải theo QĐ-1 khi có thẻ mềm — chưa kiểm | **Khánh** |
| `V-20` | `PHAN-QUYET` đảo C2 tầng world (E11) — nhánh THỬ NGHIỆM. Văn bản này **không** đóng nó, nhưng nếu `D-M3-04` REVERT thì lý do tồn tại của E11 yếu đi rõ | Cường chốt |

## 8. Nguồn

- `specs/advisor-objective-model-v2.md` §1.2b — ranh giới sức khoẻ, C2 huỷ, `C2′` thay
- `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` — phán quyết gốc
- `specs/simulation/d-m3-04-multiday-prereg-locked.json` — prereg + `luat_quyet_dinh`
- `specs/adherence-measurement.md` — bản đồ hai đường đo
- `tracking/updates/UPDATE-128-*.md` — bằng chứng thi công + sever-restore
