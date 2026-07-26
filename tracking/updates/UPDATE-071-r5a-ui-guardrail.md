# UPDATE-071 — R5-A: vá lỗ GUARDRAIL trên đường UI cards (đường tài xế thực sự nhìn)

Ngày: 2026-07-27 · Track: R5 double-check (DIRECTIVES §12.5) · Phát hiện khi **recheck plan**
theo yêu cầu Cường — không phải do agent tìm ra.

## 1. Lỗ hổng

`grep -rn "verifier|AdvisorPipeline|verify" ui/backend/app/` → **KHÔNG CÓ KẾT QUẢ**.
Nghĩa là: mọi guardrail vá ở batch 3 (V2 negation scope, V1 số trần, fail-closed FAILCLOSED-1)
**chỉ bảo vệ pipeline C6** — trong khi **proactive cards** (DIRECTIVES §12, thứ tài xế THỰC SỰ
nhìn) đi đường `ui/backend/app/adapters/advisor.py` **không qua tầng kiểm nào**. Cards còn tự
format số bằng f-string (`{sol['tier_vnd']:,}đ`, `{hours:.1f}`).

**Test đỏ chứng minh có hại thật**: `test_advice_items_pass_verifier` FAIL trên card THẬT
(số trần không trace được về `numbers[]`) — không phải rủi ro lý thuyết.

## 2. Fix

- `advisor.py`: tách `_advice_raw()` (dựng thô) khỏi **`advice()` = wrapper có guardrail**:
  mỗi item chạy `verifier.check_bare_numbers` + `check_blocklist`; card hỏng bị LOẠI; nếu không
  còn card nào → **im lặng** `reason_code="verify_failed"` + `verify_errors` để truy vết
  (fail-closed, cùng triết lý FAILCLOSED-1).
- Mọi số trong card nay render qua **`gsm_core.vn_format.render_number_vn`** — MỘT nguồn với
  pipeline, hết f-string tự chế.
- Message infeasible: bỏ chuỗi `infeasible_reason` thô (chứa số chưa neo) → diễn giải theo
  `constraints`; đồng thời **sửa lặp title/message** (lỗi giọng văn kiểu A3 LAYEROUT-6 mà chính
  tôi vừa tạo ra ở bản đầu).
- `ui/contracts/advice.json`: enum silent.reason_code +`verify_failed` (additive).

## 3. Kiểm chứng

- `ui/backend/tests`: **25 passed** (+2 test R5-A: card thật phải PASS verifier; **inject card
  độc** "chắc chắn kiếm được 5.000.000đ" → phải bị chặn thành im lặng, không lọt response).
- Đọc card thật 4 mốc giờ sau fix: 9h/14h feasible (số đúng định dạng VN), 19h/21h30 nói thật
  "khó khả thi vì quỹ giờ" — không hứa hẹn, không lặp câu.
- **Full suite chính (batch 3): 531 passed, 4 skipped** — xác nhận 16 fix audit đều xanh.

## 4. R5-B (double-check đa-agent) — BỊ CHẶN, chưa chạy

Workflow 10 finder khởi động lúc ~04:0x nhưng **10/10 chết vì session limit (reset 5:20am)**.
Ghi rõ: phần double-check tự động **CHƯA THỰC HIỆN** — chỉ có R5-A (do tôi tự recheck) và các
spot-check thủ công đã ghi ở UPDATE-070 §4. **Phải chạy lại sau 5:20** trước khi coi R5 là xong.

## 5. Adversarial self-review

- Guardrail có thể chặn NHẦM advice hợp lệ → đã kiểm 4 mốc giờ thật đều qua; test giữ 2 chiều.
- `verify_errors` lộ chi tiết nội bộ ra response — chấp nhận (local review), nhưng nếu publish
  thì phải ẩn: ghi vào DEFERRED khi lên môi trường thật.
- Cards vẫn KHÔNG có V3 (ngôn ngữ lẫn) và V4 (citation F0) — hai check đó gắn với LLM/KB, đường
  cards hiện thuần solver nên bỏ có chủ ý; nếu sau này card có text LLM thì phải bật.

---
**⏳ PENDING-REVIEW:** V-01..V-09 · **V-10** · Q-03 · **ĐA-01..ĐA-06**.

## 6. R5 SOLO double-check (agent bị chặn → tôi tự soi) — kết quả

Agent workflow chết vì session limit, nên tôi tự chạy 2 vùng quan trọng nhất:

### (a) DOCS overclaim — TỰ BẮT ĐƯỢC LỖI CỦA MÌNH
Đếm lại từ chính file JSON thô: REPORT bản đầu ghi **"168 finding · 16 fix"** — SỐ THẬT là
**179 finding** (110 A1 + 69 A3) và **21 hàng fix** (8+8+5 trong ba UPDATE). Số agent 152 và
CONFIRMED 118 thì đúng. Đã sửa REPORT + ghi ĐÍNH CHÍNH ngay trong đó (không sửa lặng).
*Đây đúng loại lỗi "viết vội, nói quá" mà Cường yêu cầu double-check.*

### (b) MUTATION TEST — test mới có thật sự bắt được lỗi không?
Revert TẠM từng fix trong bộ nhớ rồi chạy test tương ứng, khôi phục ngay:

| Fix revert | Test | Kết quả |
|---|---|---|
| `sorted(grouped)` → `list(grouped)` (S2-2) | test_forecast_groups | **PASS ❌ WEAK** → đã sửa fixture (chèn bucket đảo thứ tự 20/18/17/19) → nay **đỏ ✓** |
| `_NEG_RE` → substring cũ (VBYPASS-3) | 4 test negation | đỏ ✓ |
| bỏ `complete_time <= t_now` (LAYEROUT-4) | test_within_day | đỏ ✓ |
| bỏ nhánh fail-closed (R5-A) | test_poisoned | đỏ ✓ |

⇒ 1 test yếu bị phát hiện và vá; 4 test còn lại chứng minh có giá trị thật (không tautology).
Suite sau khi sửa fixture: **54 passed** (shift_dp + a3_fixes + ui backend).

### (c) Còn nợ R5
8 vùng khác (adapter mockdata, sim router, cards lifecycle, playback, batch 1/2 chi tiết, gates,
test quality phần còn lại) **CHƯA soi** — chạy lại workflow sau 5:20am. Không tự nhận là đã xong.
