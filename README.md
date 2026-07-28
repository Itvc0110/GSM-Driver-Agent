# GSM Driver Income Agent

Hệ thống AI hỗ trợ tài xế Xanh SM (GSM) cải thiện thu nhập: hỏi đáp chính sách/thưởng phạt theo hồ sơ, tư vấn **trước ca – trong ca – sau ca**. Sản phẩm tách rõ `gross revenue`, `driver payout` (mục tiêu mặc định) và `estimated net income` (chỉ khi đủ chi phí). Team 2 người: **Cường** & **Khánh**.

Trạng thái: **2026-07-27** · core/simulator/web UI đã có implementation và audit nhiều vòng;
**chưa production-ready**. Dữ liệu publish hiện là **MOCK content** theo 13 bảng L1R có shape từ
metadata GSM. Đọc snapshot trạng thái mới nhất tại
[`research/audit/2026-07-27-current-state/`](research/audit/2026-07-27-current-state/README.md).

**Quyết định kiến trúc hiện hành:** một canonical run/snapshot, hai projection — simulation demo là
góc nhìn dispatcher để chạy/đo/visualize hiệu quả toàn hệ thống; driver app demo + Advisor là góc
nhìn của một tài xế. Hai UI khác mục đích nhưng phải reconcile cùng event, payout ledger và `as_of`.

## Nguyên tắc cốt lõi

- Bản chất là bài toán tối ưu đa biến có ràng buộc, nhưng tiếp cận **top-down**: rule/analytics tính mọi số tài chính/policy, **AI agent tổng hợp, so sánh, giải thích** — được reasoning có điều kiện cho phần chưa mô hình hóa (log + độ tin cậy + tắt được).
- Không can thiệp matching/dispatch/pricing/routing; không hứa chắc thu nhập; tài xế luôn tự quyết.
- Mock data gắn nhãn mock; câu trả lời chính sách phải có trích dẫn nguồn.

## Đọc theo thứ tự

1. `CLAUDE.md` — harness bắt buộc cho AI coding agent (quy trình đọc docs → plan mode → hỏi → làm → ghi UPDATE).
2. `tracking/DIRECTIVES-2026-07-24.md` + `tracking/PENDING-REVIEW.md` — quyết định bền và việc Cường cần check.
3. `research/audit/2026-07-27-current-state/` — data lineage, parity, Advisor UX, ĐA-01..06 và verification ledger hiện tại.
4. `planning/SCOPE.md` — scope hiện hành (F0 FAQ có cấu trúc, F1 trước ca, F2 trong ca, F3 sau ca).
5. `planning/PERSONAS.md` — persona mock; không đồng nhất với roster synthetic 150 profile.
6. `research/` — kết quả nghiên cứu chia theo loại; đọc trước `research/00_SUMMARY.md` và banner current-state của từng file cũ.
7. `specs/` + `schemas/` — đặc tả kỹ thuật và contract dữ liệu.
8. `tracking/TODO.md` · `tracking/ASSIGNMENTS.md` · `tracking/DEFERRED.md` · `tracking/updates/` — backlog, claim, deferred và nhật ký.
9. `flow image/` — drawio kiến trúc income advisor; dùng cùng current-state dossier khi đối chiếu vì một số flow lịch sử chưa phản ánh code hiện tại.

## Pack cũ (DEFERRED)

`docs/00–09`, `contracts/`, `templates/`, `MASTER_PROMPT.md`, `AGENTS.md` là AI-coding pack theo hướng full multi-variable constrained optimization (v0.1, 2026-07-16) — đã **defer** ngày 2026-07-20 (xem `tracking/DEFERRED.md` D-001). Giữ các file đã giải nén làm tài liệu tham khảo; nhiều nguyên tắc ranh giới sản phẩm được kế thừa trong `CLAUDE.md`. Archive ZIP nguồn đã bỏ khỏi Git; lịch sử commit vẫn lưu snapshot trước đó.
