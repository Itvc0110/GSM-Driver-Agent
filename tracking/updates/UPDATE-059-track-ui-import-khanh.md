# UPDATE-059 — Track UI U0: import UI của Khánh vào `ui/` + governance

Ngày: 2026-07-26 · Track: **UI** (MỚI — thay Track C mock-UI theo chỉ thị Cường) · Phase U0/U4.

## 1. Chỉ thị + quyết định

Cường (2026-07-26): nghiên cứu `uiuxgsm-main.zip` (kết quả T-009 của Khánh, làm ở repo riêng
`Quockhanh0712/uiuxgsm`), biến thành 1 phần của project, **bỏ mock-UI → build thẳng UI thật**,
**sim thành khu riêng trong UI**, **restyle toàn bộ theo phong cách/tông màu đó**.

Chốt qua AskUserQuestion: (1) **web app** là nền chính + cơ chế cho Khánh làm **Flutter song song**
(contract-first: 1 backend chung, contracts versioned, design tokens chung, bảng SCREEN-PARITY);
(2) sim **port hẳn** vào web UI; (3) tông màu **theo Khánh 100%** (light + cyan `#00AFB9`,
palette dataviz sẽ re-validate trên nền sáng ở U1).

## 2. Files bị ảnh hưởng

- **TẠO `ui/`** (34 file, import NGUYÊN TRẠNG từ zip): `backend/` (FastAPI gateway + OSRM proxy +
  synthetic generators + 3 test), `driver_app/` (Flutter — **của Khánh, không sửa**),
  `demo_stitch_app.html` (web demo Stitch hoàn thiện nhất), `simulator_ui/` (Streamlit leafmap),
  `contracts/` (2 JSON Schema có `is_mock`/`seed`), `docs/`, `.env.example`, `.gitignore`, `.mcp.json`.
  Sửa nội dung DUY NHẤT: `ui/README.md` **thêm** mục Provenance (tác giả Khánh, upstream, ranh giới
  ownership) — phần trên giữ nguyên bản.
- **XÓA** `uiuxgsm-main.zip`. **Đính chính trong lúc làm**: zip KHÔNG untracked như tôi tưởng —
  nó bị cuốn nhầm vào commit errata `0308a12` (git add ẩu của tôi). Gỡ bằng commit riêng ngay sau
  commit U0; nội dung đã sống dưới `ui/` dạng file thường nên không mất gì.
- `tracking/DIRECTIVES-2026-07-24.md`: §6 đánh dấu THAY THẾ; bảng track thêm dòng **Track UI**,
  Track C ❌; **§11 mới** ghi nguyên văn chỉ thị + 3 quyết định đã chốt.
- `tracking/TODO.md`: khối Track UI mới; T-009 → DONE (bàn giao vượt brief); **T-009b** mới cho Khánh.
- `tracking/ASSIGNMENTS.md`: claim mới của Cường (Track UI — `ui/backend|web|contracts|docs`,
  design-tokens); dòng READY **T-009b** cho Khánh (`ui/driver_app/` — không ai khác đụng);
  T-009 chuyển Lịch sử.
- `tracking/DEFERRED.md`: **D-UI-01** (nghỉ hưu dashboard Streamlit — chờ V-10), **D-UI-02** (CDN → vendor hoá).

## 3. Khảo sát (tóm tắt — chi tiết trong plan đã duyệt)

Design system Khánh: cyan `#00AFB9` · ink `#1C1C1E` · nền sáng `#E8F1FA` · Be Vietnam Pro ·
bo góc 16–24px · CartoDB positron/dark · polyline 2 lớp · waypoint A/B/C/D 4 màu. Backend hiện
là **placeholder** (3 cuốc hardcode, state random theo seed, bot advice text cứng) — đúng phần
"chưa bắt kịp": sẽ nối data mock 90 ngày + advisor + sim engine của ta ở U2–U3. Điểm cộng lớn:
Khánh tự đặt nền contracts có `is_mock`/`data_mode: synthetic` — đúng ranh giới CLAUDE §5.

## 4. Kiểm chứng

- Import: 34/34 file khớp danh sách zip; `git status` sạch ngoài `ui/` + docs tracking.
- Nested `.gitignore` của Khánh đã đọc — chuẩn (không che file cần commit); `.env` đã bị ignore
  sẵn ở root. **Chưa chạy** test backend Khánh (cần cài fastapi vào env — làm ở U2 khi tiếp quản).
- Đường dẫn dài nhất trong `ui/` ~175 ký tự < MAX_PATH (đã gặp lỗi này khi giải nén ra scratchpad).
- Visual status: **NOT_APPLICABLE** (U0 import + docs; không đổi behavior gì của hệ hiện có).

## 5. Adversarial self-review / flaws found

- **Ownership**: import quyết định bởi Cường (coordinator) nhưng file của Khánh giữ nguyên trạng,
  provenance ghi rõ trong README + ASSIGNMENTS — Khánh vào đọc là hiểu ngay ranh giới.
- **Rủi ro nhầm nguồn sự thật**: backend Khánh đang trả số RANDOM (ví 202k, SOC random) — nếu ai
  chạy demo bây giờ sẽ thấy số không nhãn đầy đủ trên UI. Chấp nhận ở U0 (nguyên trạng có chủ ý);
  U2 thay adapter + badge "Dữ liệu mô phỏng" là mục tiêu chính.
- `ui/backend` và `src/` có 2 hệ Python khác nhau (Khánh dùng `requirements.txt`, ta dùng `uv`)
  — U2 sẽ hợp nhất vào `pyproject.toml` (extra `ui`), ghi rõ khi làm.
- Trùng tên khái niệm: `ui/simulator_ui` (leafmap của Khánh) ≠ dashboard sim của ta ≠ khu Mô phỏng
  web sắp làm — đã ghi D-UI-01 để dọn sau V-10, tránh 3 công cụ song song lâu dài.

## 6. Follow-up

U1 (tokens + palette light re-validate + contracts + SCREEN-PARITY) → U2 → U3 → U4 (V-10).
Sau Track UI: **AUDIT** data · agent · math modelling (thứ tự Cường giữ nguyên).

---
**⏳ PENDING-REVIEW (nhắc lại theo quy tắc):** V-01..V-08 (sim/dashboard cũ) · **V-09** (dashboard
SIM-XANH: Replay/Hành trình d-41/A-B heatmap — `uv run --extra viz streamlit run src/gsm_sim/dashboard.py`)
· Q-03 (corpus Khánh thiếu policy 23/02/2026). Track UI sẽ thêm **V-10** ở U4.
