# GSM Driver Income Agent

Hệ thống AI hỗ trợ tài xế Xanh SM (GSM) cải thiện thu nhập thực nhận: hỏi đáp chính sách/thưởng phạt theo hồ sơ, tư vấn **trước ca – trong ca – sau ca**. Team 2 người: **Cường** & **Khánh**.

Trạng thái: 2026-07-20 · scope v2 (top-down, flow-first) · chưa có code — đang ở giai đoạn xây khung + nghiên cứu thực tế.

## Nguyên tắc cốt lõi

- Bản chất là bài toán tối ưu đa biến có ràng buộc, nhưng tiếp cận **top-down**: rule/analytics tính mọi số tài chính/policy, **AI agent tổng hợp, so sánh, giải thích** — được reasoning có điều kiện cho phần chưa mô hình hóa (log + độ tin cậy + tắt được).
- Không can thiệp matching/dispatch/pricing/routing; không hứa chắc thu nhập; tài xế luôn tự quyết.
- Mock data gắn nhãn mock; câu trả lời chính sách phải có trích dẫn nguồn.

## Đọc theo thứ tự

1. `CLAUDE.md` — harness bắt buộc cho AI coding agent (quy trình đọc docs → plan mode → hỏi → làm → ghi UPDATE).
2. `planning/SCOPE.md` — scope hiện hành (F0 policy Q&A, F1 trước ca, F2 trong ca, F3 sau ca) + câu hỏi mở.
3. `planning/PERSONAS.md` — 5 hồ sơ tài xế mock (Bike).
4. `research/` — kết quả nghiên cứu chia theo loại (`policy/`, `economics/`, `community/`, `market/`); đọc trước `research/00_SUMMARY.md`.
5. `specs/` — đặc tả kỹ thuật để code (vd mock phân phối đơn).
6. `planning/USER_STORIES.md` — user stories nháp.
7. `tracking/TODO.md` · `tracking/ASSIGNMENTS.md` (bảng tự nhận việc) · `tracking/DEFERRED.md` · `tracking/updates/` — backlog, phân công, mục đã hoãn, nhật ký thay đổi.
8. `flow image/` — drawio kiến trúc income advisor: `...v2.drawio` hiện hành (7 trang: L0–L2 + F0–F3), `...v1.drawio` đối chiếu. (File luồng giải trình vi phạm đã xóa — dự án khác, D-006.)

## Pack cũ (DEFERRED)

`docs/00–09`, `contracts/`, `templates/`, `MASTER_PROMPT.md`, `AGENTS.md` là AI-coding pack theo hướng full multi-variable constrained optimization (v0.1, 2026-07-16) — đã **defer** ngày 2026-07-20 (xem `tracking/DEFERRED.md` D-001). Giữ làm tài liệu tham khảo; nhiều nguyên tắc ranh giới sản phẩm được kế thừa trong `CLAUDE.md`. File nguồn: `driver-income-os-ai-pack.zip`.
