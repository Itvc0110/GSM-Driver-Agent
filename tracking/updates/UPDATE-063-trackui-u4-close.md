# UPDATE-063 — Track UI U4: verify tổng + ĐÓNG Track UI (chờ verdict V-10)

Ngày: 2026-07-26 · Track: **UI** · Phase U4/U4 · Chuỗi commit: `b6fec1c` (U0 import) ·
`b51d26f` (U1 tokens/contracts) · `dabc108` (U2 web+data thật) · `36d6281` (U3 Mô phỏng) · U4 này.

## 1. Files bị ảnh hưởng

- `ui/backend/tests/test_theme_sync.py` (TẠO — 4 test): tokens↔theme.css không được trôi
  (brand colors, categorical light, radius, và ranh giới **accent brand không làm màu series**).
- `tracking/PENDING-REVIEW.md`: mở **V-10** với kịch bản xem đầy đủ (app tài xế + khu Mô phỏng).
- `tracking/DIRECTIVES-2026-07-24.md` §8 + `tracking/TODO.md`: Track UI → U0-U4 XONG, nợ mở ghi đủ.
- `ui/docs/SCREEN-PARITY.md`: 10/10 màn web ✅; cột Flutter là việc T-009b của Khánh.
- Memory agent: cập nhật chỉ thị track (tránh phiên sau đọc bản cũ).

## 2. Kiểm chứng (số đọc từ output thật)

- **Full suite chính: 493 passed, 5 skipped** (11m11s) — bằng đúng baseline trước Track UI:
  cả track KHÔNG đụng engine/advisor cũ (toàn bộ diff nằm trong `ui/` + docs + pyproject extra).
- **UI backend suite: 20 passed** (13 U2 + 3 U3 + 4 theme-sync).
- **Đối chiếu nguồn 2 hồ sơ** (kế hoạch đòi 2×2): d-19/2026-09-28 (439.636đ) và r-3/2026-08-15
  (490.842đ) — khớp bảng nguồn từng đồng, 2 đội khác nhau.
- Server live `:8010`: app + mo-phong + 10 endpoint 200.

## 3. Adversarial self-review tổng Track UI (flaws — đầy đủ, không giấu)

| Mã | Flaw | Trạng thái |
|---|---|---|
| F-U2-A (TB) | payout ngày UI = cuốc + mission, THIẾU day_bonus/newbie vì 13 bảng GSM không có bảng thưởng ngày | ghi chú trên UI; **câu hỏi cho AUDIT** |
| F-U2-B (TB) | tỷ lệ nhận/hoàn thành granularity NGÀY cấp cho advice trong-ngày | caveat in trong advice; thuộc D-SIM-18 (MATH AUDIT) |
| F-U2-C (THẤP) | shift_end mặc định 22h (ASSUMPTION, chưa cho sửa trên UI) | param sẵn ở API |
| F-U3-A (TB) | replay nội suy thẳng — chưa bám tim đường (matrix không có geometry) | ghi trên UI; defer |
| F-U3-B (THẤP) | /ab block worker 30-60s | đủ cho review local 1 người |
| D-UI-01/02 | nghỉ hưu dashboard cũ (sau V-10) · vendor hoá CDN | DEFERRED |
| Kiểm chéo | demo fare không chạm payout (code path + mắt) · UI không tự tính số nào (grep spot: mọi số render từ JSON API) · nhãn mock mọi màn · contracts additive (Flutter v0 Khánh vẫn parse — CHƯA chạy Flutter thật để xác nhận, ghi cho Khánh) | ✔ |

## 4. Chỉ thị Cường (interrupt 2026-07-26) → trạng thái cuối

| Ý | Trạng thái |
|---|---|
| Nghiên cứu `uiuxgsm-main.zip`, biến thành 1 phần project | ✅ U0 — import `ui/`, provenance + ownership rõ |
| Không build UI mock nữa — build thẳng UI thật | ✅ U2 — web app 5 màn chạy data mock 90 ngày + advisor S1 thật |
| Update phần chưa bắt kịp so với Khánh | ✅ 2 chiều: ta có UI thật; backend Khánh có data/advisor thật thay placeholder |
| Gắn simulation vào 1 phần riêng trong UI | ✅ U3 — khu Mô phỏng 4 tab (mức "port hẳn" như Cường chốt) |
| Thiết kế lại theo phong cách/tông màu đó | ✅ U1/U2/U3 — light cyan Stitch toàn bộ, palette dataviz re-validate PASS trên nền sáng |
| (kèm) Khánh làm mobile song song | ✅ cơ chế contract-first + T-009b + SCREEN-PARITY |

## 5. Kịch bản xem V-10 (chờ Cường — hoãn được, không waive)

Server: `uv run uvicorn app.main:app --app-dir ui/backend --port 8010` (đang chạy sẵn).
1. `http://localhost:8010/app/` — **Xanh Now**: pill payout d-19 (data thật) · demand hex cyan 18h ·
   badge mock; bấm **🤖**: đổi 3 chip giờ — 9h *feasible_gap* / 19h *không khả thi (nói thật)* /
   21h30 *im lặng đúng*; **Thu nhập**: payout card + gross tách + est_net "—" + chart 14 ngày;
   **Cài đặt**: đổi sang `cp-0` → bot im lặng "chưa phủ đội car"; thử vòng đời cuốc demo (cước
   demo KHÔNG cộng vào payout).
2. `/app/mo-phong/` — **Replay** ▶ quanh 07:00/18:00 · **Hành trình** (Gantt + income 4 nguồn +
   marker sự kiện + bảng offer) · **A/B** (chạy cặp ~40s, đọc warning 1-seed + guardrail) ·
   **Độ nhạy** (heatmap ✳, midpoint xám tại 0).

## 6. Kế tiếp

**AUDIT toàn bộ** (thứ tự Cường giữ nguyên): data · hệ thống agent · **math modelling (quan trọng
nhất)** — workflow đa-agent; danh mục đầu vào: D-SIM-18, F-U2-A, F-U2-B, F-P3-B, D-SIM-14.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · V-09 (dashboard SIM-XANH) · **V-10 (Track UI —
kịch bản §5)** · Q-03 (corpus Khánh thiếu policy 23/02/2026).
