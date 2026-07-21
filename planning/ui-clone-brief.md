# BRIEF — T-009 UI clone (dành cho Khánh)

Cập nhật: 2026-07-21 · Phân công: **Khánh làm T-009 song song** trong khi Cường làm simulator (T-018) — 2 phần **không đụng file nhau** (UI ở `apps/` hoặc `ui/`, sim ở `src/gsm_sim/`).
Mục đích brief: gom đủ context để bắt đầu mà không phải đọc lại toàn repo. Đọc kèm: `planning/SCOPE.md` §5 (UI/UX), `CLAUDE.md` §6 (mobile-first).

## Việc cần làm

Dựng **UI/UX tạm thời cho app tài xế** (mobile-first) bằng cách clone giao diện tham khảo, để sau này gắn các tính năng F0–F3. Đây là **prototype giao diện**, chưa nối logic thật.

- **Template công cụ:** <https://github.com/JCodesMore/ai-website-cloner-template> (MIT, là GitHub template repo — bấm "Use this template" hoặc clone về).
- **Trang cần clone tham khảo:** <https://rag-xanh-sm-v1.vercel.app/>
- **Yêu cầu:** **mobile-first** (tài xế dùng trên điện thoại); tham khảo cảm giác app Xanh SM ở góc nhìn tài xế.

## Ranh giới (bám scope hiện hành — quan trọng)

- UI này chỉ là **khung trình bày**; **không** tự tính số tài chính/policy — số sẽ do backend (rule/analytics) cấp sau (xem `CLAUDE.md` §5).
- Tiền phải phân biệt rõ 3 lớp khi hiển thị: **gross revenue / driver payout (mặc định) / estimated net** (xem `planning/SCOPE.md` §1) — kể cả bản mock cũng dùng đúng nhãn.
- Có nhãn **"Dữ liệu mô phỏng"** cho mọi số mock trên UI.
- 4 màn hình gợi ý theo F0–F3: hỏi đáp chính sách (F0), trước ca / đặt chỉ tiêu (F1), trong ca / demand + nhắc sạc-nghỉ (F2), sau ca / phân tích (F3). Xem 7 trang flow trong `flow image/GSM_Driver_Income_AI_Agentv2.drawio` để hình dung nội dung từng màn.

## Các bước gợi ý (cho AI coding agent làm cùng)

1. Đọc `CLAUDE.md` (harness) + brief này. Vào **plan mode**, hỏi lại điểm chưa rõ trước khi code (đúng quy trình repo).
2. Claim T-009 trong `tracking/ASSIGNMENTS.md` (thêm dòng của Khánh, phạm vi files = thư mục UI, để không đụng `src/gsm_sim/` của Cường).
3. Khảo sát template repo (stack thực tế: Next.js? Vite? — kiểm tra `package.json`) + trang target (các màn, layout, màu, component).
4. Dựng khung mobile-first + 1–2 màn trước (vd F0 chat policy + F1 chỉ tiêu), dữ liệu mock có nhãn.
5. Ghi `tracking/updates/UPDATE-###-ui-clone.md` sau khi có checkpoint chạy được.

## Chưa được verify (cần Khánh/agent tự kiểm khi bắt đầu)

- Stack thực tế của template (agent trước chỉ lấy được metadata: MIT, is_template, branch master; chưa đọc `package.json`).
- Cấu trúc màn hình của `rag-xanh-sm-v1.vercel.app` (chưa khảo sát sâu — cần agent fetch/mở khi làm).
- Có cần API key/.env cho template không.

## Lưu ý phối hợp

- Cường đang giữ claim T-018 (simulator) — phạm vi `src/gsm_sim/`, `specs/simulation-*`, `configs/`. Khánh tránh các file này.
- Khi cần chung một file (vd `README.md`, `tracking/TODO.md`) thì nhắn nhau trước, sửa nhỏ, commit riêng.
