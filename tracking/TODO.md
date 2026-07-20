# TODO — Backlog công việc

Cập nhật: 2026-07-20. Trạng thái: `TODO` / `DOING` / `DONE` / `BLOCKED`. Owner theo cơ chế **tự nhận việc (self-claim)** đầu session — không ai giao việc (xem `ASSIGNMENTS.md`). Khi làm xong một mục phải có UPDATE tương ứng trong `tracking/updates/`.

| ID | Việc | Trạng thái | Owner | Ghi chú |
| --- | --- | --- | --- | --- |
| T-001 | Deep research chính sách & thu nhập tài xế Xanh SM (theo `planning/RESEARCH.md`) | DONE (đợt 1) | AI agent (Cường duyệt) | 2026-07-20; output: `research/` (chia theo loại); gaps còn lại → T-012 |
| T-002 | Thiết kế hồ sơ tài xế mock (Bike trước) từ kết quả T-001 | DONE (nháp v1) | AI agent | 2026-07-20: 5 persona tại `planning/PERSONAS.md` (thêm tân binh + lão làng theo yêu cầu Cường); chờ review; số TBD chờ T-012 |
| T-003 | Mock phân phối đơn theo khung giờ × ngày trong tuần × khu vực | DOING | AI agent | Spec nháp v1 xong: `specs/mock-order-distribution.md` (research + reasoning, assumption log); còn code generator — chờ scaffold + claim |
| T-004 | Knowledge base chính sách cho F0 (policy có version + trích dẫn) | TODO | — | Nguồn từ T-001 |
| T-005 | Đánh giá framework agent: CrewAI vs flow tự viết (orchestrator theo drawio v2) | TODO | — | Stakeholder refer CrewAI; cần so sánh control/guardrail/độ phức tạp |
| T-006 | Khung F1 trước ca: chỉ tiêu net mặc định + nhận xét chỉ tiêu theo hồ sơ | TODO | — | Phụ thuộc T-002, T-004 |
| T-007 | Khung F2 trong ca: lời khuyên chạy/nghỉ/sạc từ phân phối mock | TODO | — | Phụ thuộc T-003 |
| T-008 | Khung F3 sau ca: analyzer/advisor + danh mục hành vi chưa tối ưu | TODO | — | Phụ thuộc T-002 |
| T-009 | UI/UX tạm: clone <https://rag-xanh-sm-v1.vercel.app/> bằng [ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template), mobile-first | TODO | — | Tham khảo app tài xế Xanh SM |
| T-010 | Xác nhận scope luồng giải trình vi phạm (drawio file 2) | DONE | Cường | Chốt 2026-07-20: dự án khác, ngoài scope repo này — xem D-006 |
| T-011 | Định nghĩa contract/schema mới cho scope v2 (hồ sơ tài xế, state đơn, output tư vấn) | TODO | — | Contracts cũ trong `contracts/` đã defer, chỉ tham khảo |
| T-012 | Research đợt 2: bảng thưởng chi tiết + kinh nghiệm cộng đồng (FB groups, TikTok/YouTube) | DONE | AI agent | 2026-07-20: KHÔNG OCR/app. Bảng thưởng đã verify: `research/policy/bonus-programs.md`; cộng đồng: `research/community/community-insights.md`. FB groups cần join tay (T-013) |
| T-013 | Join 1–2 group Facebook tài xế + đọc mẹo thực chiến, số thành viên | TODO | — | Cần người thật (login wall chặn crawler); danh sách 6 group ở `research/community/community-insights.md` |
| T-014 | Vẽ lại luồng v2 (drawio 7 trang: L0–L2 + F0–F3, hiện tại + tương lai) | DONE | AI agent (Cường duyệt plan) | 2026-07-20: `flow image/GSM_Driver_Income_AI_Agentv2.drawio`; nới nguyên tắc reasoning trong SCOPE/CLAUDE; spec lọc rủi ro `specs/community-source-risk-control.md` |
| T-015 | (Tương lai) Tích hợp nguồn cộng đồng + khối kiểm chứng/lọc rủi ro vào sản phẩm | TODO | — | Roadmap D-008; theo `specs/community-source-risk-control.md`; cần F0–F3 chạy ổn trước |
