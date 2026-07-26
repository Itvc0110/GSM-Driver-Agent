# UPDATE-061 — Track UI U2: web app + backend chạy DATA THẬT + advisor S1 thật

Ngày: 2026-07-26 · Track: **UI** · Phase U2/U4 · Sau U1 (`b51d26f`).

## 1. Files bị ảnh hưởng

**Backend (`ui/backend/`)** — tiến hoá gateway của Khánh, GIỮ routing proxy + trip/step demo:
- `app/adapters/mockdata.py` (TẠO): đọc `data/mock/realdata-v1` (polars, cache module) —
  `driver_state` v1.1 (tiền: gross=`total_fee`, trip payout=`commission`=gross×driver_share theo
  generator; mission cộng từ `public_mission_earn_history.earn` đúng ngày; rating từ counter;
  mission progress join catalog), `driver_history`, `map_context` (demand = SỐ ĐƠN ĐẶT theo
  pickup_h3×giờ từ bảng `trips` — đúng nghĩa demand proxy SCOPE F2), `stations()` (11 tủ pin OSM
  THẬT từ `batt_dd.json`), `catalog` (150 driver × 90 ngày, gắn fleet theo prefix), `default_view`
  (bike-sim nhiều cuốc nhất). **SOC là PROXY deterministic** (không có trong 13 bảng GSM) — docstring
  + ghi chú ngay trên UI.
- `app/adapters/advisor.py` (TẠO): dựng `bonus_gap_input` từ bảng mock (điểm từ trips×policy,
  lịch sử điểm/giờ 7 ngày median theo bucket, tỷ lệ từ statistic) → gọi **solver S1 thật**
  (`gsm_core.solvers.bonus_feasibility`); policy MỘT nguồn qua `SimPolicy.to_core_record()`
  (cùng đường với mockgen — không lệch số). Dịch SolverReport → contract advice: feasible_gap /
  info-infeasible (nói thật lý do) / **im lặng** (already_on_track; đội car → `no_active_channel`
  vì CHƯA có policy car — không áp bừa).
- `app/routers/driver.py`, `app/routers/advice.py` (TẠO); `app/main.py` (SỬA — của ta theo claim):
  v2.0 mount web app tại `/app`, `/` redirect; map-context mặc định mock-realdata,
  `scenario_id="synthetic"` giữ generator Khánh; state-synthetic giữ nhãn deprecated.
- `tests/test_contracts.py` (TẠO — 6 test: schema mọi endpoint, payout==Σbreakdown, est_net phải
  null, im-lặng↔items loại trừ nhau, đội car im lặng đúng mã, determinism byte-identical, history
  bounded); `tests/conftest.py` (TẠO); `tests/test_api.py` (SỬA theo semantics gateway v2 — ghi chú
  trong file). `ui/contracts/map_context.json`: ports/distance nullable (OSM không có số cổng —
  không bịa); enum data_mode +`mock-realdata` (additive).
- `pyproject.toml`: extra `ui` (fastapi/uvicorn/httpx). Lưu ý vận hành: `uv sync` PHẢI kèm đủ
  `--extra viz...` nếu không nó gỡ package của dashboard (đã suýt dính, file lock cứu).

**Web (`ui/web/`)** — TẠO: `theme.css` (CSS vars SINH TỪ design-tokens), `index.html` (5 màn),
`js/api.js` (lớp gọi API duy nhất), `js/app.js`, `mo-phong/index.html` (placeholder U3).
Màn: **Xanh Now** (Leaflet Carto light; demand hex tô sequential-cyan theo intensity; tủ pin amber;
pill payout + nhãn "Thu nhập tài xế (payout)"; badge mock cố định; vòng đời cuốc demo port từ demo
Khánh — polyline 2 lớp brand, cước demo **KHÔNG cộng** vào payout) · **Thu nhập** (card payout
mặc định + breakdown; gross card riêng; **est_net hiển thị "—"** vì chưa đủ known costs; Plotly bar
14 ngày + list từng ngày) · **Chuyến của tôi** (lịch sử demo phiên, nhãn rõ) · **Xe & Pin** (SOC
proxy + tủ pin OSM) · **Cài đặt** (picker 150×90 hồ sơ, rating, mission, provenance data + link khu
Mô phỏng). **Bot Trợ Lý Xanh**: sheet render advice thật — title/message, bảng numbers[] KÈM NGUỒN
từng số, thanh confidence, mã lý do, caveat; trạng thái im lặng hiển thị tử tế.

## 2. Kiểm chứng (số đọc từ output thật)

- Backend tests: **13 passed** (`uv run pytest ui/backend/tests -q`).
- Full suite chính: **493 passed, 5 skipped** (11m36s) — KHÔNG hỏng gì của sim/advisor cũ.
- **Đối chiếu nguồn từng đồng** (d-19, 2026-09-28): UI payout 439.636đ = `commission` 399.636 +
  mission `earn` 40.000; gross 532.848 = `total_fee` ✓.
- Advisor hành vi theo giờ (d-19): 9h/14h → `feasible_gap` conf 0.85 (historical:self); 19h →
  `insufficient_budget_hours` nói thật; 21h30 → im lặng `already_on_track`; cp-0 → `no_active_channel`.
- Launch thật: `uvicorn --app-dir ui/backend --port 8010` — `/app/`, theme.css, app.js, mo-phong,
  6 endpoint đều 200. `node --check` 2 file JS sạch.
- Visual status: **PENDING V-10** (mở chính thức ở U4 sau khi có khu Mô phỏng; xem sớm:
  `http://localhost:8010/app/` — đang chạy).

## 3. Adversarial self-review / flaws found

- **F-U2-A (TB)**: `day_bonus`/`newbie` KHÔNG có trong 13 bảng GSM ⇒ payout ngày trên UI là
  cuốc+mission, THIẾU 2 nguồn còn lại so với engine. UI ghi chú thẳng ("thưởng ngày/tân binh: xem
  khu Mô phỏng"). Câu hỏi cho AUDIT: bảng nào của GSM chứa thưởng ngày? (schema thật không thấy —
  có thể nằm ngoài 13 bảng được cấp.)
- **F-U2-B (TB)**: tỷ lệ nhận/hoàn thành cấp NGÀY (statistic daily) dùng cho advice trong-ngày
  tại now_min — granularity thô hơn realized-tại-thời-điểm của sim. Caveat đã in trong advice;
  ước lượng chuẩn thuộc D-SIM-18 (MATH AUDIT).
- **F-U2-C (THẤP)**: `shift_end_min` mặc định 22h là ASSUMPTION (tài xế chưa khai ca) — param
  chỉnh được, ghi trong docstring; UI chưa cho sửa (thêm ở U4 nếu Cường muốn).
- **F-U2-D (THẤP)**: demand zones lấy top-12 hex một giờ — silent cap; popup ghi rõ "không đảm
  bảo đơn về tay bạn". Slider giờ chưa có trên UI (map cố định 18h) — U3 replay sẽ phủ nhu cầu này.
- Con số demo (cước cuốc demo, fare OSRM ×24k/km của Khánh) TÁCH khỏi mọi số data — đã kiểm bằng
  mắt code path: `S.demoTrips` không chạm `S.state.money`.

## 4. Follow-up

U3: khu Mô phỏng (Replay/Hành trình/A/B/heatmap từ engine qua API). U4: verify tổng + đồng bộ
tokens↔theme.css test + V-10. Sau Track UI: AUDIT (F-U2-A/B nhập vào danh mục audit).

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · **V-09** (dashboard SIM-XANH) · Q-03 (corpus Khánh
thiếu policy 23/02/2026). **V-10** mở ở U4 — xem sớm: `http://localhost:8010/app/`.
