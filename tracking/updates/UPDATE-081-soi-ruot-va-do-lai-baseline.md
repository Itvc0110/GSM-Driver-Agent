# UPDATE-081 — Tài xế biết SỐT RUỘT (cắt đuôi chờ) + đo lại baseline sau dispatcher tầng 2

> ⚠ **CORRECTED 2026-07-28 — BUG-EVAL-ARGMAX (UPDATE-085 §4, Q-11).** Mọi số payout "tài xế
> đích" trong file này đo bằng `pick_target` argmax-A — phép chọn CỰC TRỊ có bias âm hệ thống
> (regression to the mean; sign-flip đã chứng minh: argmax-A −19,7k vs argmax-B +27,4k vs
> không-chọn-lọc +3,6k trên CÙNG can thiệp). **Các số tầng HỆ THỐNG (served/expired/HHI/Gini/
> tổng payout đội) KHÔNG bị ảnh hưởng.** Số thay thế: artifact `24-unbiased-30seed.json` +
> UPDATE-086. Giữ nguyên phần còn lại của file làm lịch sử.


- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** feature (behavior model) + measurement (đo lại baseline)
- **TODO liên quan:** **T-045d** (theo ranh giới **Q-08** agent chốt); nối tiếp UPDATE-080

## Tóm tắt

**(1)** Đo lại baseline 30 seed trên thế giới có dispatcher tầng 2: **advisor trông TỆ HƠN gấp
đôi** (−17.310đ → **−38.374đ**). Đây là kết quả **quan trọng**, không phải hồi quy — dispatcher cũ
đang thổi phồng giá trị advisor.

**(2)** Cắt đuôi chờ phi thực tế theo ranh giới Q-08: khoảng chờ tối đa **269′ → 59′**, p99
**152′ → 41′**, số khoảng > 90′ **45,3 → 0**.

## 1. Đo lại baseline: dispatcher tốt lên ⇒ advisor tệ đi GẤP ĐÔI

30 seed CRN, `coverage: all`, `crn_ok = True`.

| Chỉ số (P4 đại diện) | TRƯỚC (greedy-haversine) | **SAU (batch Hungarian)** |
|---|---|---|
| **payout/ngày** | −17.310đ [−29.294, −5.820] SIG | **−38.374đ** [−51.219, −24.866] SIG · lợi **5/30** |
| cuốc hoàn thành | −1,6 SIG | **−4,5** SIG · lợi 2/30 |
| phút rỗi | +25,9 SIG | **+50,5** SIG |
| served_rate | −0,0047 | −0,0033 (CI chứa 0) |
| đơn hết hạn | +4,8 | +7,9 (CI [0,97 · 14,33]) |
| tổng payout toàn đội | −168.517đ | +67.649đ (CI chứa 0) |

**Đọc đúng**: khi ghép đơn hiệu quả hơn, mỗi phút advisor kéo tài xế rời trạng thái online trở nên
**đắt hơn** — bỏ lỡ nhiều đơn hơn. ⇒ **Con số −17.310đ cũ là cận trên lạc quan**, được một
dispatcher kém làm đẹp hộ.

Đây đúng điều đã cảnh báo khi cân nhắc Q-07 phương án (a): *"dispatcher thiển cận thổi phồng giá trị
advisor"* — nay có số.

## 2. Tài xế biết SỐT RUỘT (T-045d)

### 2.1 Truy nguyên đầy đủ

- vòng idle poll **mỗi 2 phút** ⇒ chờ 244′ = **122 lần ra quyết định không dịch chuyển**;
- `_actor_demand_hint` là **PRIOR cache theo (actor, giờ)** — **không bao giờ** cập nhật từ trải
  nghiệm;
- `choose_idle_action` xét **ring-1** (6 ô, ~0,35 km), đòi hơn **25%**, rồi tung đồng xu 50%.

⇒ Nếu ô hiện tại là **cực đại địa phương THEO NIỀM TIN** thì `best_cell == actor.cell` suốt cả
giờ — **không có cả cú tung đồng xu**. Tài xế ngồi 4 tiếng, không đơn nào, niềm tin vẫn nguyên.

### 2.2 Điều tôi thử trước và KHÔNG đủ

Nới ring + hạ ngưỡng + tăng xác suất đi: max chờ vẫn **201′** ở mức escalation mạnh nhất.
**Lý do**: không ngưỡng nào làm tài xế rời một ô mà *niềm tin của họ* nói là tốt nhất — phép so
sánh `v_adj > here × bar` luôn thất bại khi `here` là cực đại.

### 2.3 Mảnh còn thiếu: THÔI TIN vào niềm tin

Khi sốt ruột kịch (rỗi ≥ `step × max_steps`), tài xế **bỏ hẳn phép so sánh** và đi tới ô tốt nhất
trong bán kính — **kể cả ô mình nghĩ là kém hơn**. Đó là điều người thật làm: ngồi đây 40 phút
không đơn nào thì niềm tin đã bị thực tế bác bỏ.

### 2.4 Kết quả (3 seed, quét tham số)

| step/max | served | max chờ | p99 | >90′ | cuốc/tx | relocate/tx |
|---|---|---|---|---|---|---|
| **TẮT** | 0,764 | **269′** | **152′** | **45,3** | 10,1 | 6,7 |
| 30 / 2 | 0,777 | 76′ | 60′ | 0,3 | 10,3 | 9,0 |
| **20 / 2 ⭐** | **0,787** | **59′** | **41′** | **0,0** | 10,4 | 10,0 |
| 15 / 3 | 0,786 | 79′ | 46′ | 0,0 | 10,4 | 9,9 |
| 20 / 3 | 0,767 | 94′ | 60′ | 1,0 | 10,1 | 8,9 |

Chốt **20′ / 2 bước**: rỗi 20′ → nới ring + bớt kén; rỗi 40′ → thôi tin niềm tin.

### 2.5 Ranh giới Q-08 được giữ bằng TEST, không bằng lời hứa

Đây là **bản năng**, không phải lời khuyên: chỉ nới bán kính và bỏ kén, **không cấp thêm thông tin
nào** về cầu. Giá trị advisor vẫn là positioning **có thông tin** (đúng khu, đúng lúc,
capacity-aware).

`test_idle_impatience.py` canh **cả hai phía**:
- `test_no_implausible_idle_tail` / `test_idle_gap_p99_reasonable` — đuôi phải bị cắt;
- **`test_impatience_does_not_hand_over_the_advisors_job`** — `served_rate` không được nhảy quá
  **+0,05** so với bản tắt cờ (đo được **+0,023**). Nếu bản năng thành "positioning miễn phí" thì
  test ĐỎ;
- `test_relocation_stays_local_knowledge_only` — relocate tìm khách ≤ 2 km (không nhảy cóc);
- `test_impatience_can_be_switched_off` — tắt cờ ⇒ đuôi dài trở lại (cờ thật sự điều khiển).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/entities.py` | sửa | `Actor.idle_streak_min` |
| `src/gsm_sim/behavior.py` | sửa | escalation ring/ngưỡng/xác suất + "thôi tin niềm tin"; `_neighbors(ring)` |
| `src/gsm_sim/world.py` | sửa | cộng dồn `idle_streak_min` ở WAIT; reset khi được CHÀO và khi relocate; truyền `cfg_behavior` |
| `configs/pilot_dongda.yaml` | sửa | 3 tham số + bảng quét trong comment |
| `tests/test_idle_impatience.py` | **tạo** | 5 test (4 đỏ trước fix) |
| `research/.../16-baseline30-sau-dispatch-tang2.json` | **tạo** | baseline sau tầng 2 |
| `research/.../17-baseline30-sau-soi-ruot.json` | **tạo** | baseline sau sốt ruột |

## Kiểm chứng

| Command | Kết quả |
| --- | --- |
| `pytest tests/test_idle_impatience.py` | **4 failed → 5 passed** |
| `pytest tests` (root, full) | **575 passed / 5 skipped** (12:54) |
| baseline 30 seed sau tầng 2 | `crn_ok=True`; bảng §1 |
| baseline 30 seed sau sốt ruột | artifact `17-*`; bảng ba thế giới dưới đây |

### Ba thế giới, cùng 30 seed CRN (`crn_ok = True`)

| | A: gốc | B: +dispatcher tầng 2 | **C: +sốt ruột (hiện tại)** |
|---|---|---|---|
| **payout** | −17.310đ | −38.374đ | **−17.497đ** CI [−31.205, −3.209] **SIG** |
| cuốc | −1,6 | −4,5 | −2,5 |
| phút rỗi | +25,9 | +50,5 | +30,7 |
| served_rate | −0,0047 | −0,0033 | −0,0043 |
| đơn hết hạn | +4,8 | +7,9 | +5,8 |
| seed tài xế có lợi | 7/30 | 5/30 | **7/30** |

**Kết luận quan trọng nhất của cả chuỗi**: sau khi sửa dispatcher cho đúng đặc tả **và** cho tài xế
hành xử khả tín, kết luận **KHÔNG đổi** — advisor vẫn làm tài xế đại diện **nghèo đi có ý nghĩa
thống kê**. Nghĩa là phát hiện ban đầu **không phải artefact của một thế giới kém**; nó bền qua hai
lần nâng cấp lớn về chất lượng mô phỏng.

⚠ **Chưa giải thích được** vì sao B (−38k) tệ hơn hẳn A và C. Giả thuyết: sốt ruột làm cả hai
nhánh A/B cùng dịch chuyển nên triệt tiêu một phần chênh lệch. **Chưa kiểm** — không kết luận.

## Visual verification

- **Status:** `BLOCKED` → cần Cường xem. Khu Mô phỏng → **Replay seed 1000**: tài xế nay **dịch
  chuyển nhiều hơn hẳn** (relocate 6,7 → 10,0 lượt/tài xế), không còn ai đứng im hàng giờ.
  Cũng nên xem tab Bản đồ H3 để thấy phân bố cung đổi.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

1. **Giải pháp đầu tiên của tôi KHÔNG đủ và tôi đã suýt dừng ở đó.** Nới ring + hạ ngưỡng nghe
   hợp lý, nhưng đo ra max vẫn 201′. Chỉ khi hỏi *"vì sao hạ ngưỡng mãi vẫn không đi?"* mới thấy
   phép so sánh với chính niềm tin là chỗ kẹt. **Bài học: sửa tham số của một cơ chế không cứu
   được khi cơ chế đó sai về cấu trúc.**
2. **Test của tôi có một lỗi**: kiểm mọi `relocate` ≤ 2 km, quên rằng `deadhead_to_core` (về lõi
   sau khi trả khách ngoài vùng) **được phép** đi xa. Đã lọc theo `reason == "demand_seek"`.
3. **Rủi ro ăn mất dư địa advisor** — đã lượng hoá và khoá bằng test (+0,023 vs trần 0,05). Nhưng
   trần 0,05 là **tôi tự đặt**, không có nguồn. Nếu Cường thấy quá lỏng/chặt thì sửa được.
4. **served tăng 0,023 vẫn là baseline tốt lên** — về lý thì trái tinh thần "baseline chưa tối ưu
   là feature". Tôi cho là chấp nhận được vì phần tăng đến từ việc **bỏ hành vi phi thực tế**, và
   Q-08 (agent chốt theo uỷ quyền) đã đặt ranh giới đó. Nếu Cường không đồng ý thì hạ escalation.
5. **Chưa đo lại chỉ tiêu kép ĐA-08 đầy đủ** sau sốt ruột — artifact `17-*` đang chạy.
6. **`give_up` dùng `max(nbs, key=(hint, cell))`** — tie-break theo tên ô, deterministic nhưng
   **thiên vị ô có id nhỏ** khi nhiều ô cùng hint. Ở đây hint là số thực nên trùng hiếm; ghi nhận.
7. **Chưa kiểm tương tác với advisor**: sốt ruột có thể **cạnh tranh** với `shift_plan` (advisor
   bảo ONLINE, bản năng bảo đi chỗ khác). `_map_action` không có RELOCATE nên advisor không ghi đè
   được — nhưng chưa đo xem tần suất xung đột.

## Expansion checkpoint (T-039)

1. **Schema**: `idle_streak_min` là state runtime, không cần vào schema. Nhưng nó là **tín hiệu
   tốt cho `MarketStateView`**: "tài xế đã rỗi bao lâu" là thứ hệ thật đo được từ
   `public_driver_hex_tracking.stay_duration_seconds`.
2. **Bài toán tối ưu**: nay có baseline biết tự dịch chuyển ⇒ advisor phải chứng minh
   **positioning CÓ THÔNG TIN hơn bản năng**, không còn ăn điểm nhờ baseline đứng im. Đây là
   phép đo **công bằng hơn hẳn**.
3. **Tính năng**: `idle_streak_min` cho phép card *"anh đã chờ 25 phút — khu X đang có cầu cao hơn"*
   — đúng loại lời khuyên đo được, và khác hẳn bản năng vì có dữ liệu cầu thật.

## Follow-up / defer phát sinh

- **Đo lại chỉ tiêu kép** sau sốt ruột (artifact `17-*`), rồi mới so advisor tiếp.
- **Q-07 vẫn mở** — nay còn đáng làm hơn vì dispatcher đã đúng.
- Kiểm tần suất xung đột bản năng ⇄ advisor (§7).

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-15 + **visual của UPDATE-080/081** · **Q-07 đang mở** ·
Q-03, Q-04 · B-02 ARCH-VERSION chặn T-044 · **chưa commit gì trong toàn bộ phiên**.
