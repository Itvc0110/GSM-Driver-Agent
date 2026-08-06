# UPDATE-158 — Merge PR #6 của Khánh + hoà giải số UPDATE + suite chốt sau merge

- **Ngày:** 2026-08-06
- **Loại:** integration (theo lệnh Cường: *"đọc và tìm hiểu rồi merge, xử lý conflict nếu có, kiểm tra kỹ nếu có conflict ngầm"*)
- **Liên quan:** PR #6 `feat/checkpoint-foundation-and-ui-ideas` (8 commit, tới `9c29bba`) · memory git-integration-workflow

## PR #6 của Khánh mang gì

Checkpoint foundation (validity THẬT qua `validity_hints` do callsite khai — S2 bucket-end, S7
window-end, freshness = `interval_min` thay hằng bịa; facts-on-record; safe attach; queued
lifecycle; schema `advice_checkpoint@1.2.0` + upcaster; contract v2 nới enum version) + 6 audit
UPDATE (144–149 CỦA KHÁNH) + **2 fix K-01**: (a) `pythonpath=[".", "src"]` chữa 2 test
`checkpoint_trace` (verify 8/8); (b) `test_safety_topic_presents_even_while_driving` đổi theo
quyết định B-03 đã đóng — commit **có nhãn** *"FLAGGING FOR CUONG/KHANH CONFIRMATION"*, không
sửa lặng lẽ (đúng quy trình).

## Xung đột & cách xử lý

1. **🔴 Đụng số UPDATE-144..150** — Khánh đánh số đúng theo remote (143 là số cuối đã push); 7
   update CHƯA COMMIT của tôi (E-program) phải dời: **144..150 → 151..157** (+ ref "151" tương
   lai → 158). Máy làm: 86 refs / 29 file + đổi tên 7 file, verify bằng chính lượt replace.
   Lỗi thuộc phía tôi (giữ local quá lâu); bài học cũ lặp lại lần hai — từ giờ **push UPDATE
   ngay khi Cường đã cho phép commit** thay vì gom.
2. **Git-level: 0 conflict** — nhưng đó chính là vùng conflict NGẦM (advice_bridge/world/
   checkpoint bị CẢ HAI bên sửa, git tự đan). Quét ngầm:
   - `_capture_checkpoint` của Khánh thêm param `validity_hints` + 2 callsite (S2/S7) — TRỰC
     GIAO với sửa của tôi (should_defer_rest/sp_end_only/pick_station không capture checkpoint);
   - contract v2 chỉ nới `checkpoint_schema_version` enum — không đụng taxonomy QĐ-4; registry
     gates xanh với topic mới của tôi (`swap_early`/`station_choice`);
   - battery cổng nhanh sau merge: **162 passed / 1 F = K-03 nguyên trạng** (không phình mục).
3. **ASSIGNMENTS/GRAPH/TODO của Khánh** merge nguyên vẹn — không sửa dòng nào của anh ấy.

## Suite CHỐT sau merge

| Suite | Kết quả | So với trước |
| --- | --- | --- |
| `uv run pytest -q` | **1155 passed / 2 failed / 4 skipped** (53′) | 5 F → **2 F**: K-01×3 ✅ hết (pythonpath + B-03); còn `test_demo_trace_neutrality` (import `app` — vẫn của Khánh) + K-03 (4 hàm manifest — của Khánh, không phình) |
| `uv run pytest -q ui/backend/tests` **KHÔNG cần `--ignore`** | **201 passed** | 🎉 **K-02 ĐƯỢC CHỮA** bởi pythonpath — collection error biến mất, suite backend nay chạy trọn một lệnh |

⚠ Thời gian suite 53′ (lượt trước 26′) **KHÔNG so được**: dân số test tăng (checkpoint_enrichment
258 dòng + moving_queue + 40 test E-program) + tải máy khác. Số tiết kiệm của E5 wave-1 đo riêng
ở `D-E5-01` khi làm tiếp danh sách r13 — không claim ở đây.

## Commit/push

6 commit E-program (bb52c46..) + merge commit; đẩy `origin/main` sau khi suite chốt xanh.

## Adversarial self-review
1. Renumber bằng replace toàn cục "UPDATE-1xx" TRƯỚC merge — an toàn vì cây lúc đó chỉ có ref
   của tôi; sau merge KHÔNG chạy lại lệnh đó (sẽ phá số của Khánh). Đã kiểm: 0 ref lệch còn lại.
2. Chưa đọc SÂU 6 audit UPDATE của Khánh (144–149 của anh ấy) — chỉ đọc đủ để merge an toàn;
   các UI-idea cards (UPDATE-149 của Khánh) có thể giao với E3/V-31 — ghi việc đọc kỹ vào lượt
   V-31 chuẩn bị.
3. `pythonpath=["."]` là thay đổi TOÀN CỤC của Khánh — có thể che lỗi import kiểu K-01 trong
   tương lai (mọi module ở root importable). Chấp nhận (quyết định của owner), ghi nhận rủi ro.

## Follow-up
Push → V-31 visual gộp (điểm dừng chờ Cường) · cập nhật BOOTSTRAP §2 (suite mới, K-01/K-02 đã giải).
