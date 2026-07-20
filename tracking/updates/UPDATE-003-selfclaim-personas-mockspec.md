# UPDATE-003 — Self-claim ASSIGNMENTS, 5 personas, mock spec phân phối, xóa drawio vi phạm

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo yêu cầu của Cường
- **Loại:** docs / research / defer
- **TODO / User story liên quan:** T-002 (DONE nháp v1), T-003 (DOING — spec xong), T-012 (redefine + DOING)

## Tóm tắt

Theo chỉ đạo mới của Cường: (1) ASSIGNMENTS đổi sang cơ chế **tự nhận việc đầu session, không ai giao việc**; (2) làm giàu personas — 5 hồ sơ (thêm tân binh mới dùng app + lão làng thâm niên); (3) không OCR ảnh chính sách — chạy research đợt 2, không ra thì mock; defer quy trình khiếu nại (D-007); (4) tự xây mock spec phân phối đơn bằng research + reasoning; (5) xóa file drawio luồng vi phạm khỏi repo.

## Chi tiết cập nhật

1. `tracking/ASSIGNMENTS.md` viết lại: bảng claim đang hoạt động + lịch sử; 6 quy tắc (claim đầu session, 1 việc 1 người, không đụng phạm vi claim người kia, cập nhật khi kết thúc, agent làm dưới claim của người điều khiển, claim quá 3 ngày tự release). CLAUDE.md §3.3 và banner AGENTS.md sửa theo.
2. `planning/PERSONAS.md` (mới): P1 sinh viên part-time, P2 full-time RTO, P3 top performer xe riêng, P4 tân binh mới dùng app (hưởng ĐBTN 3 tháng đầu, sát ngưỡng 70%), P5 lão làng ≥24 tháng (thưởng thâm niên/Loyalty, kinh nghiệm lỗi thời khi chính sách đổi). Kèm nháp schema hồ sơ cho T-011. SCOPE §3-F0 cập nhật từ "2–3 hồ sơ" → 5 personas.
3. `planning/mock/order-distribution-spec.md` (mới): mô hình `BASE × zone × hour_shape × dow × weather`; bảng trọng số 24h; hệ số thứ trong tuần + biến thể cuối tuần; hệ số mưa; zone tier HN; giá cuốc lognormal; sanity check 15–30 cuốc/ngày; assumption log A1–A4.
4. Research đợt 2 (T-012 redefine): 2 agent nền — (a) săn bảng thưởng chi tiết từ blog/video/repost, (b) kinh nghiệm cộng đồng FB/TikTok/YouTube (khu đứng chờ HN, dead hours, mẹo tỷ lệ, trạm pin). Không OCR/app theo quyết định Cường.
5. Xóa `flow image/GSM_Income_AI_agent.drawio` (luồng vi phạm — dự án khác; file chưa từng commit git); D-006 cập nhật; thêm D-007 (quy trình khiếu nại — defer).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| tracking/ASSIGNMENTS.md | viết lại | self-claim, không ai giao việc |
| planning/PERSONAS.md | tạo | 5 persona nháp v1 |
| planning/mock/order-distribution-spec.md | tạo | spec mock T-003 |
| flow image/GSM_Income_AI_agent.drawio | **xóa** | theo yêu cầu Cường |
| CLAUDE.md, AGENTS.md, README.md, planning/SCOPE.md, tracking/DEFERRED.md, tracking/TODO.md, planning/research/00_SUMMARY.md | sửa | đồng bộ các quyết định trên |

## Docs đã cập nhật kèm theo

SCOPE (F0 personas, §4 vi phạm), TODO (T-002/T-003/T-012), DEFERRED (D-006, D-007), 00_SUMMARY (gaps). USER_STORIES: chưa đổi — nên bổ sung story cho P4/P5 khi review personas.

## Kiểm chứng

Thay đổi docs, không có code chạy. CHƯA kiểm chứng: các số MOCK trong PERSONAS và mock spec (đã ghi assumption log + TBD); kết quả research đợt 2 (đang chạy).

## Follow-up / defer phát sinh

- Khi research đợt 2 xong: cập nhật bảng thưởng (hoặc mock), file kinh nghiệm cộng đồng, điền TBD trong PERSONAS; sau đó tới T-009 (UI clone) theo thứ tự Cường chọn.
- Đề xuất: thêm user stories cho P4 (onboarding) và P5 (delta chính sách) vào USER_STORIES khi Cường review.
