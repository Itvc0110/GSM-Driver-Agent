# UPDATE-062 — Track UI U3: khu "Mô phỏng" trong web UI (port từ dashboard P4)

Ngày: 2026-07-26 · Track: **UI** · Phase U3/U4 · Sau U2 (`dabc108`).
Chỉ thị gốc (Cường): *"gắn simulation vào 1 phần riêng trong UI"* — chốt mức: **port hẳn**.

## 1. Files bị ảnh hưởng

- `ui/backend/app/routers/sim.py` (TẠO): serialize KẾT QUẢ ENGINE — `/run` (tổng quan ngày sim +
  picker), `/journey` (timeline/offers/income_curve/events/metrics từ `build_journey` —
  `to_dict` sẵn của engine), `/replay` (legs toạ độ từ `result.segments` — client nội suy),
  `/ab` (cặp CRN dùng ĐÚNG máy đo của `parallel`: import `_cfg_with`/`_driver_metrics`/
  `_system_metrics`/`pick_target` — KHÔNG chép logic, tránh lỗi hai-nguồn-sự-thật đã trả giá
  ở SIM-1; refactor giữa chừng: bản đầu chạy 4 run/lượt, bản chốt 2 run + cache), `/sweep`
  (đọc `dsim06_sweep.json` precomputed — không tính lại). `run_once` cache LRU theo seed.
- `ui/backend/app/main.py`: mount router `/api/v1/sim`.
- `ui/web/mo-phong/index.html` (VIẾT LẠI từ placeholder) + `mo-phong/mo-phong.js` (TẠO):
  trang desktop-first tông Stitch light, seed input + 4 tab:
  - **Replay đội xe**: Leaflet + slider phút + nút ▶ chạy; 90 marker màu theo hoạt động
    (palette entity validated), nội suy tuyến tính trong leg; tủ pin amber; đếm tài xế đang chạy.
  - **Hành trình 1 tài xế**: KPI 4 nguồn tiền + Gantt Plotly (bar ngang theo kind) + đường thu
    nhập cộng dồn bậc thang + marker sự kiện (advice cyan · mission amber · thưởng ngày xanh ·
    tân binh tím) + bảng offer CÓ LÝ DO.
  - **Thế giới song song A/B**: nút chạy cặp (30-60s), cards Δ payout / A / B / guardrail hệ
    thống, 2 đường thu nhập chồng (A xám · B cyan); **warning 1-seed in cố định** (contract bắt).
  - **Độ nhạy**: heatmap adherence×lift mỗi archetype từ file sweep, **diverging đỏ↔cyan
    midpoint XÁM tại 0** (đúng dataviz), ô ✳ = CI không chứa 0, chú thích 30 seed/ô.
- `ui/contracts/journey.json`: `online_min` integer→number (engine trả float — schema theo engine).
- `ui/backend/tests/test_contracts.py`: +3 test U3 (journey đúng schema + **bảo toàn 4 nguồn**
  parts==payout==cuối income_curve; replay đúng schema + legs sorted; ab đúng schema + warning
  bắt buộc + delta nhất quán).

## 2. Kiểm chứng (số đọc từ output thật)

- Backend suite: **16 passed** (13 cũ + 3 U3; 1 vòng đỏ thật: `online_min` 723.6 vs integer —
  sửa contract, không sửa engine).
- Suite chính KHÔNG chạy lại: không file nào trong `src/`/`tests/` đổi từ lần 493-green U2
  (diff U3 chỉ nằm trong `ui/` — kiểm bằng git status). Ghi rõ thay vì im lặng.
- `node --check` mo-phong.js sạch. Launch thật `:8010`: mo-phong page + JS + `/sim/run`
  + `/sim/sweep` đều 200; run seed 1000: 90 actors, top d-14 P2 27 cuốc.
- Visual status: **PENDING V-10** (mở chính thức ở U4 — trang đã xem được).

## 3. Adversarial self-review / flaws found

- **F-U3-A (TB)**: replay nội suy TUYẾN TÍNH giữa 2 đầu chặng — xe "bay" qua nhà, không bám
  đường (đúng như TripsLayer của dashboard P4). Vẽ theo tim đường cần geometry OSRM per-chặng
  (matrix offline chỉ có distance/duration, KHÔNG có polyline) → ghi chú ngay trên UI; nếu
  Cường muốn, phương án là fetch geometry 1 lần cho ~200 cặp cell phổ biến (defer — không làm ẩu).
- **F-U3-B (THẤP)**: `/ab` chạy 2 sim run trong request HTTP (30-60s block worker) — đủ cho
  local review 1 người; multi-user cần background job queue (out-of-scope local dev).
- **F-U3-C (THẤP)**: picker Hành trình chỉ hiện top-40 theo offer (90 gây danh sách dài) —
  silent cap ghi tại đây; seed nào cũng đổi được nên không mất khả năng xem ai.
- **F-U3-D (THẤP)**: heatmap texttemplate làm tròn nghìn ("12k") — số đầy đủ trong hover;
  đánh đổi có chủ ý cho ô nhỏ.
- Palette: khu Mô phỏng dùng ĐÚNG bộ light validated; cyan brand chỉ ở chrome (nút/marker
  advice); idle `#9aa4ab` đậm hơn token `#eceff2` vì làm MARKER trên map cần thấy được —
  lệch token có chủ ý, ghi tại đây (idle vẫn không phải series chart).

## 4. Follow-up

U4 (chốt Track UI): test đồng bộ tokens↔theme.css, adversarial review tổng, **V-10** vào
PENDING-REVIEW với kịch bản xem đầy đủ, cập nhật SCREEN-PARITY + spec. Sau đó: **AUDIT**.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · **V-09** (dashboard SIM-XANH) · Q-03 (corpus
Khánh). **V-10** mở ở U4 — xem sớm: `http://localhost:8010/app/` và `/app/mo-phong/`.
