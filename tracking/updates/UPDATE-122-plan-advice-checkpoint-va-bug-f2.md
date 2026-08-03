# UPDATE-122 — Plan AdviceCheckpoint + luồng Agent; phát hiện BUG-F2-NOW (khuyên sai thời điểm)

- **Ngày:** 2026-08-03
- **Người thực hiện:** Khánh (agent), theo yêu cầu Khánh trong hội thoại
- **Loại:** docs (plan) + phát hiện bug
- **TODO liên quan:** `BUG-F2-NOW` (MỚI, sev CAO), `CKPT-00`..`CKPT-05`

## Tóm tắt

Dựng plan thi công chi tiết cho AdviceCheckpoint + luồng agent (tiếp nối nghiên cứu UPDATE-121).
Trong lúc dựng plan, chạy solver thật để lấy output thật thay vì bịa ví dụ, và **tái lập được một
BUG đang sống**: template F2 khuyên tài xế làm việc của **một tiếng sau** như thể là việc **lúc này**.

**KHÔNG sửa dòng code nào** — Khánh yêu cầu "không code, không refactor ở bước này".

## Chi tiết cập nhật

### 1. BUG-F2-NOW — lỗi đang sống, đã tái lập

Chạy `shift_dp.solve()` với state thật (d-15, 09:00, SOC 46%, 78 điểm):

```
schedule[0]  = {bucket: 09:00, action: ONLINE}                      ← việc BÂY GIỜ
next_action  = {action: SWAP, bucket: 10:00, reason: "đổi pin trước khi cạn"}   ← MỘT TIẾNG SAU
```

Output template hiện tại (`llm_mode=off`, F2) — thứ tài xế đang thấy:

> *"Gợi ý **lúc này**: anh/chị nên **đi đổi pin** — đổi pin trước khi cạn."*
> `advice_spec.target_window = "2026-07-01T10:00:00+07:00"`

**Ba lỗi cùng lúc:** (1) solver bảo ONLINE, message bảo đi đổi pin — ngược nhau; (2) nói "lúc này"
cho việc của một tiếng sau; (3) message **tự mâu thuẫn với `advice_spec` của chính nó**.

**Root cause:** `templates.py:283` đọc `next_action` rồi render `"Gợi ý lúc này"`, và **không bao giờ
đọc `schedule[0]`**. Theo định nghĩa của chính `shift_dp`, `next_action` là *"action đầu tiên KHÁC
ONLINE trong cả lịch"* — có thể cách hiện tại **vài tiếng**.

Đây đúng là **BẪY 1** mà `advice_bridge.py:19-22` đã ghi thành cảnh báo và sim cẩn thận tránh
(`:594` dùng `schedule[0]`). Sim tránh được, **đường agent/sản phẩm sập thẳng vào**. Cùng họ với
BUG-ADVICE-OVERRIDE — `world.py:820-829` đo được **92/166 = 55%** can thiệp của advisor từng là phá
hoại vì dịch sai ý solver.

### 2. Plan thi công

`tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md` — 8 mục, gồm: output trước/sau tài xế
thấy, checkpoint JSON điền **giá trị thật**, contract input/output agent, 5 bất biến, 3 xung đột +
cách thống nhất, sơ đồ luồng agent, 9 bước thi công B1–B9, kiểm chứng, ngoài phạm vi, rủi ro.

**Ý tưởng cốt lõi:** làm ranh giới "BÂY GIỜ vs SẮP TỚI" thành **bất biến cấu trúc** — checkpoint mang
hai trường tách biệt `action_now`/`plan_next`; agent trả hai dòng riêng `now_line`/`next_line`;
verifier veto nếu `action_type` lệch khỏi `action_now`. Không thể diễn đạt sai kể cả khi thay
template bằng LLM sau này.

### 3. Gỡ chặn GĐ0 — cả ba "blocker" tan khi soi kỹ

| Blocker | Kết luận |
| --- | --- |
| `Q-13` (adherence theo DECISION hay EVENT) | **Đã có phán quyết Cường 2026-07-29**: *"HAI TÊN `decision_adherence`+`event_adherence`, cấm khoá trần"* ⇒ checkpoint chỉ cần **không làm mất thông tin** để tính được cả hai — không phải chọn |
| `V-21` (`min_gap` 20′ vs bucket 30′) | Đã vá kỹ thuật bằng `effective_gap_min = max(...)` (`cadence.py:104`) ⇒ không chặn thi công |
| `Q-14` (B6-PARITY) | Xử lý bằng trường **bắt buộc** `solver_set` — biến lỗi ngầm thành lỗi nhìn thấy được, không cần giải trước |

⇒ `CKPT-00` chuyển `BLOCKED` → `RESOLVED`. Khánh waive gate review trong hội thoại 2026-08-03.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md` | tạo | Plan thi công 8 mục |
| `tracking/TODO.md` | sửa | Thêm `BUG-F2-NOW`; `CKPT-00` → RESOLVED |
| `tracking/updates/UPDATE-122-*.md` | tạo | File này |

**KHÔNG có file code nào bị sửa** (xác minh: `git status` không có `.py`/`.js` nào của tôi).

## Docs đã cập nhật kèm theo

SCOPE/DEFERRED/USER_STORIES: không đổi. TODO: có. PENDING-REVIEW: **không thêm mục mới** — `Q-15` mở
ở UPDATE-121 nay đã tự giải bằng §3, không còn cần Cường chốt để thi công.

## Assumptions và evidence

| Claim | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Template F2 khuyên sai thời điểm | `OBSERVED-CODE` (**đã tái lập, chạy thật**) | `templates.py:283` + output thật in ra ở §1 | **Rất cao** | — |
| `next_action` có thể cách hiện tại nhiều giờ | `OBSERVED-CODE` | Định nghĩa của `shift_dp`; `advice_bridge.py:19-22` | Cao | Nếu sai, mức nghiêm trọng giảm nhưng lỗi vẫn còn |
| Q-13 đã có phán quyết | `FACT` | `PENDING-REVIEW.md` dòng ĐA-05, verdict Cường 2026-07-29 | Cao | Nếu diễn giải sai, `CKPT-00` phải mở lại |
| `valid_until` = 1 bucket (30′) | `ASSUMPTION` | Suy từ `DECISION_BUCKET_MIN`; **chưa đo** | **Thấp** | Advice hết hạn sớm/muộn — phải đo sau GĐ này |
| Bug này gây hại kinh tế thật | `UNVERIFIED` cho đường sản phẩm | `world.py:820-829` đo 55% ở **sim**, chưa đo ở sản phẩm | Trung bình | Mức ưu tiên có thể hạ nếu đo ra khác |

## Kiểm chứng

- Chạy `shift_dp.solve()` thật với `configs/pilot_dongda.yaml` + `PolicyBundle` thật → in ra
  `schedule[0]`, `next_action`, `numbers`, và `render_template('F2', …)`. **Bug tái lập 1/1 lần.**
- Đọc và trích dẫn: `templates.py`, `context_pack.py`, `composer.py`, `verifier.py`, `advice_bridge.py`,
  `world.py`, `projections.py`, `cadence.py`.
- **CHƯA kiểm chứng:** chưa chạy pytest (không sửa code ⇒ không cần; baseline gần nhất UPDATE-121:
  935+4skip / 66). Chưa đo bug này ảnh hưởng bao nhiêu ca trên đường sản phẩm thật. Chưa kiểm
  `valid_until` = 30′ có hợp lý không.

### Seeds và scenarios

| Command / run | Seed | Scenario | Kết quả | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `shift_dp.solve()` in-memory | — (deterministic) | d-15, 09:00, SOC 46%, 78đ, 9 bucket | Bug tái lập; `ONLINE` now vs `SWAP@10:00` | Chưa quét xem bao nhiêu % ca rơi vào tình huống `action_now ≠ next_action` |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** docs-only, không sửa code ⇒ chưa có gì đổi trên màn hình. Bảng trước/sau ở §1.1 của plan
  là **thiết kế mục tiêu**, chưa phải ảnh chụp. Khi thi công B5/B9 sẽ có visual gate thật.

## Adversarial self-review / flaws found

1. **Bug có thể là cố ý không?** Đã cân nhắc: không. `advice_spec` mang đúng bucket 10:00 trong khi
   message nói "lúc này" ⇒ hai phần của cùng một output nói ngược nhau — không thiết kế nào cố ý như vậy.
2. **Ví dụ có bị dựng để ra bug không?** State tôi dựng (SOC 46%, 78 điểm, 09:00) là tham số hợp lý,
   không cực đoan. Nhưng **tôi chưa quét** bao nhiêu % ca thật rơi vào `action_now ≠ next_action` ⇒
   **chưa biết tần suất**, chỉ biết chắc là xảy ra được. Đã ghi là chưa kiểm chứng.
3. **Assumption yếu nhất:** `valid_until` = 1 bucket — thuần suy diễn từ hằng số sẵn có, chưa đo.
   Cố tình KHÔNG đặt số cho `min_expected_impact` vì `cadence.py:70-72` cấm chỉnh baseline bằng trực giác.
4. **Suy luận "gây hại 55%" là của SIM, không phải sản phẩm** — tôi trích để chỉ ra *họ lỗi*, không
   phải để tuyên bố sản phẩm đang mất 55%. Đã gắn nhãn `UNVERIFIED` cho đường sản phẩm.
5. **Rủi ro của chính plan:** B3/B4 (nối checkpoint vào sim) có thể vô tình đổi số A/B. Đã đưa
   fingerprint 5 seed thành điều kiện dừng, không phải bước kiểm tra cho có.
6. **Gỡ chặn GĐ0 có vội không?** Ba blocker được gỡ bằng **lập luận có dẫn chứng** (phán quyết đã có,
   vá đã có, hoặc chuyển thành trường bắt buộc), không phải bằng cách bỏ qua. Nhưng đây vẫn là diễn
   giải của tôi về phán quyết của Cường — nếu Cường đọc và thấy diễn giải sai thì `CKPT-00` mở lại.
7. **Flaw còn mở → map:** `BUG-F2-NOW` (TODO, sev CAO), tần suất bug chưa đo (ghi ở §Kiểm chứng),
   `valid_until` chưa đo (rủi ro §8 của plan).

## Expansion checkpoint (T-039)

1. **Schema**: `advice_checkpoint@1.0.0` đã thiết kế ở plan §1.2, **chưa tạo**.
2. **Bài toán tối ưu**: nếu thêm `min_expected_impact`, "chọn advice nào trong ngân sách 6 thẻ/ca"
   thành **knapsack theo ca** — ghi để sau, chưa cần.
3. **Tính năng**: UI hiện "còn hiệu lực tới HH:MM" khi có `validity` — đã đưa vào plan B9.

## Follow-up / defer phát sinh

- **Đo tần suất `BUG-F2-NOW`**: quét xem bao nhiêu % ca có `schedule[0].action ≠ next_action.action`.
  Rẻ, nên làm cùng lúc với B5 để biết mức nghiêm trọng thật.
- **Nợ đọc từ UPDATE-121 còn nguyên**: `templates.py` các nhánh F0/F1/F3 chưa soi kỹ như F2 — **có
  thể có cùng lỗi**; `episode_store.py` chưa kiểm xem tái dùng làm nơi lưu StateSnapshot được không.
