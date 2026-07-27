# GSM Driver Income Agent

Hệ thống AI hỗ trợ tài xế Xanh SM (GSM) cải thiện thu nhập: hỏi đáp chính sách/thưởng phạt theo hồ sơ, tư vấn **trước ca – trong ca – sau ca**. Sản phẩm tách rõ `gross revenue`, `driver payout` (mục tiêu mặc định) và `estimated net income` (chỉ khi đủ chi phí). Team 2 người: **Cường** & **Khánh**.

Trạng thái: 2026-07-27 · scope v2 (top-down, flow-first) · core data/9 solver/C6, simulator, SIM-XANH và web UI đã `DONE-CODE`; visual verdicts, policy values và post-audit decisions còn mở — xem `tracking/PROJECT-GRAPH.md`.

## Nguyên tắc cốt lõi

- Bản chất là bài toán tối ưu đa biến có ràng buộc, nhưng tiếp cận **top-down**: rule/analytics tính mọi số tài chính/policy, **AI agent tổng hợp, so sánh, giải thích** — được reasoning có điều kiện cho phần chưa mô hình hóa (log + độ tin cậy + tắt được).
- Không can thiệp matching/dispatch/pricing/routing; không hứa chắc thu nhập; tài xế luôn tự quyết.
- Mock data gắn nhãn mock; câu trả lời chính sách phải có trích dẫn nguồn.

## Đọc theo thứ tự

1. `CLAUDE.md` — harness bắt buộc cho AI coding agent.
2. `tracking/PROJECT-GRAPH.md` — route đọc theo task và trạng thái/correction của 66 UPDATE hiện hành; không đọc toàn bộ lịch sử mặc định.
3. `planning/SCOPE.md` — scope hiện hành (F0 policy Q&A, F1 trước ca, F2 trong ca, F3 sau ca) + câu hỏi mở.
4. `planning/PERSONAS.md` — 5 hồ sơ tài xế mock (Bike).
5. `research/` — kết quả nghiên cứu chia theo loại (`policy/`, `economics/`, `community/`, `market`); đọc trước `research/00_SUMMARY.md` khi route yêu cầu.
6. `specs/` — đặc tả kỹ thuật để code (vd mock phân phối đơn).
7. `planning/USER_STORIES.md` — user stories nháp.
8. `tracking/TODO.md` · `tracking/ASSIGNMENTS.md` (bảng tự nhận việc) · `tracking/DEFERRED.md` · `tracking/PENDING-REVIEW.md` — mở theo route và khi task đổi status/claim.
9. `flow image/` — drawio kiến trúc income advisor: `...v2.drawio` hiện hành (7 trang: L0–L2 + F0–F3), `...v1.drawio` đối chiếu. (File luồng giải trình vi phạm đã xóa — dự án khác, D-006.)

## Pack cũ (DEFERRED)

`docs/00–09`, `contracts/`, `templates/`, `MASTER_PROMPT.md`, `AGENTS.md` là AI-coding pack theo hướng full multi-variable constrained optimization (v0.1, 2026-07-16) — đã **defer** ngày 2026-07-20 (xem `tracking/DEFERRED.md` D-001). Giữ các file đã giải nén làm tài liệu tham khảo; nhiều nguyên tắc ranh giới sản phẩm được kế thừa trong `CLAUDE.md`. Archive ZIP nguồn đã bỏ khỏi Git; lịch sử commit vẫn lưu snapshot trước đó.
