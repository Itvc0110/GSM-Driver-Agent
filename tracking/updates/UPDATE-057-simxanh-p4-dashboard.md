# UPDATE-057 — SIM-XANH Phase 4: dashboard theo taste-skill + dataviz (palette VALIDATED)

Ngày: 2026-07-26 · Track: **A (SIM-XANH)** · Sau Phase 2 (`de70ff6`); Phase 3 sweep đang chạy nền
Chỉ thị Cường: *"Làm nó đẹp lên, sử dụng taste-skill, có thể dùng thư viện khác design cho đẹp"*
+ *"viết mọi tính năng có thể để trực quan tốt nhất"*.

## 1. Đọc brief trung thực (theo chính quy tắc taste-skill §13)

Đây là **dashboard dữ liệu** — taste-skill tự khai out-of-scope cho dashboard, chỉ áp phần
nguyên tắc chuyển giao được: **một accent khoá toàn trang · theme khoá dark · không AI-purple ·
một hệ bo góc (8px) · số dùng mono · WCAG contrast**. Công cụ đúng cho phần biểu đồ là skill
**dataviz** — đã theo đủ quy trình 7 bước của nó.

## 2. Palette: TÍNH, không ước bằng mắt

Chạy `validate_palette.js` (dataviz skill). **Bản nháp đầu TRƯỢT 4/5 check** (blue↔violet
ΔE 1.9 protan — va chạm CVD kinh điển; lightness band lệch; gray dưới sàn chroma) — đúng lý do
skill bắt chạy script. Snap về bộ tham chiếu đã validate của skill:

| token | giá trị | job |
|---|---|---|
| surface / elevated | `#12181c` / `#1a2126` | nền |
| **accent (duy nhất)** | `#199e70` — aqua, trùng brand Xanh | CTA, marker, series-1 |
| categorical (thứ tự CỐ ĐỊNH) | chở khách `#199e70` · đi đón `#3987e5` · đổi pin `#c98500` · nghỉ `#9085e9` · dịch chuyển `#d55181` | identity — màu theo entity vĩnh viễn |
| idle | tông nền mờ `#242d33` + nhãn trực tiếp | **KHÔNG phải series** — "vắng hoạt động" |
| sequential (mật độ cầu) | aqua một-hue mờ→sáng | magnitude |
| status | good/warning/critical reserved | state, không tái dụng làm series |

**Kết quả validator: 5/5 PASS** (CVD worst-pair ΔE 16.0 · normal 19.7 · contrast ≥3:1).
Diverging cho heatmap độ nhạy: đỏ↔aqua với **trung tính ở 0** (đúng chuẩn: không hue ở midpoint).

## 3. Tính năng mới

- **Tab Replay** (yêu cầu "trực quan tốt nhất"): time-slider + `TripsLayer` — xem đội xe
  CHUYỂN ĐỘNG theo phút, vệt màu theo loại hoạt động, trạm pin amber; đếm chặng/tài xế đang
  di chuyển tại thời điểm.
- **Tab Thế giới song song** (trả nợ SIM-4): chạy cặp A/B ngay trong dashboard (cached),
  bảng Δ theo cặp + guardrail served; **cảnh báo đọc-số in thẳng UI**: "1 seed = 1 ngày —
  kết luận cần 30 seed + CI". Nếu file sweep D-SIM-06 tồn tại → **heatmap độ nhạy**
  (adherence × lift_max, diverging quanh 0) đọc từ file, không tính lại.
- **Tab Hành trình nâng cấp**: vạch mốc advice/mission/thưởng trên Gantt (từ event thật);
  hàng metric thêm điểm sao ngày · mission · tân binh (thâm niên).
- Gantt/minutes-bar/bản đồ đổi sang palette cố định + nhãn tiếng Việt; hex demand sang
  sequential aqua (bỏ cam-đỏ tuỳ hứng cũ); map style dark; bỏ emoji khỏi tab (taste-skill).
- `.streamlit/config.toml` + `dashboard_theme.py` (token MỘT nguồn) + CSS metric-card/tab/header.

## 4. Nguyên tắc giữ

Mọi số hiển thị đọc từ **nguồn sự thật sim** (`RunResult`/`journey`/`parallel`/file sweep) —
dashboard không tự tính lại (bài học coherence). Replay dùng `segments` có sẵn, A/B dùng máy đo
`parallel.py`.

## 5. Kiểm chứng

- Render-test offline: replay 173 chặng cửa sổ 700±45ph; cặp A/B chạy được (d-41, guardrail in).
- Launch thật `localhost:8505` — headless OK, không lỗi console.
- `dashboard_theme.py` syntax + template đăng ký global.

## 6. Flaws / follow-up

- **F-P4-A (TB)**: trạm pin trong Replay chưa có **queue động theo phút** — `RunResult` không
  lưu chuỗi thời gian hàng chờ; cần world ghi `station_queue_sample` event nếu muốn (không giả số).
- **F-P4-B (THẤP)**: Stadia tiles chưa nhúng (map_style dark mặc định Carto) — cần format URL
  style Stadia + key qua env; Carto đủ đẹp cho V-09, Stadia là nice-to-have.
- Tab Môi trường/Nhịp ngày mới chỉ ăn theme template, chưa redesign sâu.

## 7. Visual review

**V-09 (PENDING-REVIEW)**: `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` —
xem theo thứ tự: **Replay** (kéo slider quanh 07:00 và 18:00 — thấy nhịp cao điểm) →
**Hành trình** (chọn d-41 P4: Gantt màu mới + vạch advice + metric sao/mission/tân binh) →
**Thế giới song song** (bấm "Chạy cặp A/B", đọc guardrail; nếu sweep xong sẽ thấy heatmap).
