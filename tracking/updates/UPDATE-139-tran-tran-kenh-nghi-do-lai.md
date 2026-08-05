# UPDATE-139 — "Trần trên kênh nghỉ ≤29% do lan can sức khoẻ" là SAI: đo lại được **~91%**

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent (Cường: *"còn lại dựa trên thứ bạn nghĩ là tốt nhất"*)
- **Loại:** research / đính chính số — **KHÔNG đổi một dòng code sản phẩm**
- **Liên quan:** `D-M3-04` (Cycle B) · `D-M3-06` · nối tiếp đính chính số 85% ở UPDATE-138

> ### 🔴 ĐÍNH CHÍNH 2026-08-05 (cùng ngày, khi mở prereg để thi công Cycle B) — TÔI ĐÃ NÓI QUÁ ĐỘ MỚI
>
> Update này trình bày *"trần ≤29% do lan can sức khoẻ"* như một **phát hiện mới**. **Không phải.**
> `specs/simulation/d-m3-04-multiday-prereg-locked.json` → `vung_mu_khai_truoc`, **khoá 2026-08-01**,
> đã ghi nguyên văn:
>
> > *"Trần 71,0% lan can là số MỘT NGÀY — **KHÔNG trích cho chế độ multiday** (trong multiday kênh
> > chỉ hiện thực 2–5,7% cơ hội, và **chặn chính là `at_window`/`window_past`, không phải lan can
> > sức khoẻ**)"*
>
> Và `d-m3-04-multiday-ab-brief.md:76-78` cũng ghi y hệt. Tức tác giả prereg (chính tôi, 4 ngày
> trước) **đã biết và đã khai** — tôi chỉ quên nó khi viết update này.
>
> **Cái update này thật sự đóng góp, sau khi trừ phần không mới:**
> 1. **Con số** — vùng mù được khai *định tính* (*"chặn chính là at_window/window_past"*); đây là
>    lần đầu nó được **đo**: biên **8,8%**, và `fatigued` = **0,0%** (không bao giờ là thứ chặn duy nhất).
> 2. **`DEFERRED.md` vẫn mang claim cũ KHÔNG có caveat** — prereg khai vùng mù nhưng `DEFERRED` thì
>    không, và `DEFERRED` mới là thứ người ta đọc. Việc sửa nó vẫn cần.
> 3. Hệ quả cho `D-M3-06` (mất một trụ của lý lẽ hạ ưu tiên) — cái này prereg không nói.
>
> **Bài học lặp lại:** đây là lần thứ ba trong hai ngày tôi nói quá về một kết quả (85% → biên 3,5%;
> *"cổng không chặn"* relay từ subagent; và lần này *"phát hiện mới"* vốn đã nằm trong tài liệu tôi
> tự viết). Cả ba đều cùng một hình: **không đọc lại nguồn trước khi tuyên bố.**

## Tóm tắt

Sau khi tự bắt lỗi *"đếm sai đại lượng"* của mình ở UPDATE-138, tôi hỏi câu hiển nhiên tiếp theo:
**lỗi đó có ở chỗ khác không?** Có — và ở đúng con số đang định hình cách đọc **Cycle B**.

`tracking/DEFERRED.md` `D-M3-04` ghi:

> *"Phân rã chặn: `soc_low` 44,1% + `fatigued` 26,9% (**lan can sức khoẻ = 71,0%**) · `window_past`
> 17,8% · `no_window` 10,3%"* … *"**Trần trên của kênh là ≤29,0% dù sửa gì** — do lan can sức khoẻ,
> KHÔNG phải bug"*

Đo lại phần **BIÊN**: lan can sức khoẻ chặn thật **8,8%**, không phải 74%. ⇒ **Trần trên là ~91%,
không phải ≤29%.** Thứ đang chặn kênh là **logic KHUNG của chính S7**, không phải lan can sức khoẻ.

## Chi tiết

### Vì sao con số cũ sai — cùng cơ chế với lỗi 85% của tôi

`should_defer_rest` kiểm theo thứ tự: `soc_low` → `fatigued` → `defer_cap` → `no_window`/`at_window`
→ `window_past` → `defer_cap` → `cadence` → `coin`.

Hai lan can sức khoẻ đứng **TRƯỚC** mọi kiểm khung. Nên **mọi ca mà khung cũng sẽ chặn đều được ghi
cho lan can sức khoẻ**. Bảng phân rã lý do là bảng *"ai BÁO CÁO"*, không phải *"ai CHẶN"*.

### Cách đo — không chép lại logic, không đổi hành vi

Bọc `should_defer_rest`: **gọi hàm THẬT** để lấy quyết định (run không đổi một bit), rồi khi nó trả
lý do sức khoẻ, hỏi tiếp *"nếu bỏ hai lan can đó, các kiểm KHUNG có chặn không?"* — bằng cách gọi
chính `rest_window_hour` của bridge. Không viết lại logic ⇒ không có nguy cơ test bản sao của mình.

⚠ `rest_window_hour` gọi `_capture_checkpoint`, nhưng hàm đó `return None` ngay khi
`checkpoint_trace is None` (mặc định) ⇒ không side effect. Đã kiểm trước khi đo.

### Kết quả — và caveat suýt làm tôi kết luận ngược

| chế độ | 'lan can sức khoẻ' theo cách đếm CŨ | **BIÊN** (khung cho phép, chỉ sức khoẻ chặn) |
| --- | ---: | ---: |
| **một ngày** (`run_once`, 3 seed) | 72,2% (534/740) | **0,0%** (0/740) |
| **nhiều ngày** (`run_multiday`, 2 seed × 3 ngày) | 74,0% (1084/1464) | **8,8%** (129/1464) |

🔴 **Caveat suýt làm tôi báo sai:** bản đo đầu chỉ chạy `run_once` và cho **0,0%** — tôi suýt kết
luận *"lan can sức khoẻ hoàn toàn không chặn gì"*. Nhưng `run_once` là **một ngày**, nơi
`planned_rest_hour` luôn `None` ⇒ `rest_window_hour` phải giải S7 tại chỗ và trả `None` với tài xế
không chờ nhiều ⇒ `no_window` nuốt hết. `D-M3-04` là phép đo **NHIỀU NGÀY**, nơi `multiday.py:166`
nuôi `planned_rest_hour` từ hôm qua — và `DEFERRED` ghi rõ đó là *"đường DUY NHẤT làm lời khuyên hồi
cứu của S7 có tác dụng"*. Ở chế độ đúng, con số là **8,8%**, không phải 0%.

⇒ **Đo ở chế độ nào thì chỉ được phát biểu cho chế độ đó.** Đây là lần thứ hai trong hai ngày tôi
suýt phát biểu cho một chế độ mình không đo.

### Phân rã multiday (chế độ của `D-M3-04`)

| lan can | đã bắn | khung **cũng** chặn | **BIÊN** | % biên |
| --- | ---: | ---: | ---: | ---: |
| `soc_low` | 755 (51,6%) | 626 | **129** | 17,1% |
| `fatigued` | 329 (22,5%) | 329 | **0** | **0,0%** |

**`fatigued` KHÔNG BAO GIỜ là thứ chặn duy nhất** — mọi ca nó bắn đều trùng một ca khung cũng chặn.
Toàn bộ 8,8% đến từ `soc_low` (pin), tức **ràng buộc vật lý**, không phải ràng buộc mệt.

⚠ Con số BIÊN là **cận TRÊN**: một ca qua được kiểm khung vẫn có thể bị `cadence`/`coin` chặn sau
đó, mà tôi không trừ. Nên lan can sức khoẻ chặn thật **≤ 8,8%**.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/DEFERRED.md` | sửa | `D-M3-04`: đính chính "trần ≤29%" → **~91%**; `D-M3-06` được nâng ý nghĩa |
| — | — | **KHÔNG đổi code sản phẩm.** Phép đo ở `scratchpad/do_bien_rest_rails.py` |

## Kiểm chứng

| Command | Seed/scenario | Kết quả |
| --- | --- | --- |
| `scratchpad/do_bien_rest_rails.py` (single) | 1000·1001·1002, 1 ngày | 72,2% báo cáo · **0,0%** biên |
| `scratchpad/do_bien_rest_rails.py multi` | 1000·1001, 3 ngày | 74,0% báo cáo · **8,8%** biên |

**Tái lập được bảng cũ**: 72–74% khớp con số tài liệu 71,0% (khác seed) ⇒ phương pháp đúng, chỉ cách
**đọc** là sai.

**Chưa kiểm:** n nhỏ (2 seed × 3 ngày cho multi). Muốn trích số này vào một kết luận thì phải chạy
≥5 seed và ≥7 ngày. Ở mức hiện tại nó đủ để **bác** một claim tuyệt đối (*"≤29% dù sửa gì"*), chưa
đủ để **khẳng định** một con số thay thế chính xác.

## Visual verification

- **Status:** `NOT_APPLICABLE` — không đổi code, không đổi UI. Đây là phép đo trên code hiện hành.

## Adversarial self-review / flaws found

1. **Bug trong chính script đo (tự bắt).** Bản đầu viết `why or 'SPOKEN' if ok else 'cadence'`;
   Python phân tích thành `(why or 'SPOKEN') if ok else 'cadence'` ⇒ **mọi** lần chặn bị ghi là
   `cadence`, bảng lý do đầu tiên in ra hoàn toàn vô nghĩa. Bắt được vì bảng cho *một* dòng
   `cadence 100%` trong khi bộ đếm thứ hai lại thấy 534 ca sức khoẻ — **hai bộ đếm mâu thuẫn nhau**.
   Nếu chỉ có một bộ đếm thì tôi đã tin bảng sai.
2. **Suýt kết luận từ sai chế độ** — xem caveat multiday ở trên.
3. **Điểm yếu nhất:** n nhỏ, và BIÊN là cận trên (chưa trừ `cadence`/`coin`).
4. **Đã loại trừ:** *"phương pháp sai"* — bác bằng việc tái lập được bảng phân rã cũ (72–74% vs
   71,0%).
5. **Hệ quả cho `D-M3-06`** (*"sửa `window_past` chỉ mở ≤17,8%"*): con số đó vẫn đúng, nhưng lý lẽ
   *"trần đã bị lan can sức khoẻ khoá ở 29%"* thì không còn — nên giá trị của việc sửa khung **cao
   hơn** những gì `D-M3-06` ghi khi hạ ưu tiên nó.

## Follow-up / defer phát sinh

| ID | Việc | Điều kiện |
| --- | --- | --- |
| `D-M3-04` | Đọc kết quả Cycle B **không** được dựa vào trần ≤29% | ngay lập tức |
| `D-M3-06` | Xem lại việc hạ ưu tiên `window_past` — lý lẽ cũ đã mất một trụ | khi Cường xét lại hàng đợi |
| — | Chạy lại phép đo với ≥5 seed × ≥7 ngày nếu cần **trích số** thay cho việc **bác claim** | trước khi số 8,8% được dùng trong một kết luận |
