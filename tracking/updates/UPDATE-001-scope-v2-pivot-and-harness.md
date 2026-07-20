# UPDATE-001 — Pivot sang scope v2 top-down + dựng harness/tracking

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo yêu cầu của Cường
- **Loại:** docs / refactor / defer
- **TODO / User story liên quan:** khởi tạo T-001…T-011

## Tóm tắt

Chuyển hướng tiếp cận từ full multi-variable constrained optimization (pack cũ) sang top-down flow-first: rule/analytics tính số, agent tổng hợp–so sánh–giải thích. Dựng harness `CLAUDE.md`, hệ thống `planning/` + `tracking/`, đánh dấu DEFER toàn bộ pack cũ.

## Chi tiết cập nhật

1. Giải nén `driver-income-os-ai-pack.zip` vào gốc repo (turn trước): `docs/00–09`, `contracts/`, `templates/`, `AGENTS.md`, `MASTER_PROMPT.md`, `README.md`; xóa `REAME.md` rỗng (gõ sai tên).
2. Audit chéo pack cũ phát hiện mâu thuẫn đánh số phase MASTER_PROMPT §13 vs docs/07 → ghi vào DEFERRED (D-005).
3. Đọc 2 file drawio trong `flow image/`: v1 = kiến trúc income advisor flow-first hybrid (L0–L2); file 2 = luồng giải trình vi phạm (L0–L4, cần xác nhận scope — T-010).
4. Tạo mới: `CLAUDE.md` (harness bắt buộc: đọc docs trước, plan mode + hỏi lại, UPDATE sau thay đổi, defer policy, phân công chỉ do Cường), `planning/SCOPE.md` (scope v2: F0 policy Q&A, F1 trước ca, F2 trong ca, F3 sau ca; taxonomy hồ sơ; mock plan; UI clone), `planning/RESEARCH.md`, `planning/USER_STORIES.md`, `tracking/TODO.md`, `tracking/ASSIGNMENTS.md` (bảng trống — Cường tự tách), `tracking/DEFERRED.md`, `tracking/updates/UPDATE_TEMPLATE.md`.
5. Đánh dấu DEFER pack cũ: banner đầu file docs/00–09 + MASTER_PROMPT.md + AGENTS.md; ghi chú DEFERRED trong contracts/ và templates/; viết lại README.md.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| CLAUDE.md | tạo | Harness |
| planning/SCOPE.md, RESEARCH.md, USER_STORIES.md | tạo | Scope v2 |
| tracking/TODO.md, ASSIGNMENTS.md, DEFERRED.md, updates/UPDATE_TEMPLATE.md, updates/UPDATE-001-… | tạo | Hệ thống tiến độ |
| docs/00–09 (10 file), MASTER_PROMPT.md, AGENTS.md | sửa | Thêm banner DEFERRED |
| contracts/DEFERRED-NOTE.md, templates/DEFERRED-NOTE.md | tạo | Ghi chú defer cho folder schema/template |
| README.md | sửa | Viết lại theo hướng mới |
| REAME.md | xóa | File rỗng gõ sai tên |

## Docs đã cập nhật kèm theo

Toàn bộ SCOPE/TODO/DEFERRED/USER_STORIES/RESEARCH là bản khởi tạo trong update này.

## Kiểm chứng

Chỉ là thay đổi docs/cấu trúc, không có code chạy. CHƯA kiểm chứng: tính sát thực của mọi giả định về chính sách/số liệu Xanh SM (chờ T-001); scope luồng giải trình vi phạm (chờ T-010).

## Follow-up / defer phát sinh

- T-001…T-011 trong `tracking/TODO.md`.
- D-001…D-006 trong `tracking/DEFERRED.md`.
- Câu hỏi mở cho Cường: SCOPE §7 (CrewAI, nguồn số liệu mock).

## Quyết định của Cường (cùng ngày, sau khởi tạo)

1. T-001 deep research: chạy ngay (AI agent thực hiện, output vào `planning/research/`).
2. Luồng giải trình vi phạm = **dự án khác**, ngoài scope repo này → D-006, T-010 DONE.
3. T-009 UI clone: làm sau khi có kết quả research.
