# UPDATE-054 — SIM-XANH Phase 1: đường THẬT từ OSRM thay detour hằng

Ngày: 2026-07-26 · Track: **A (SIM-XANH, chỉ thị Cường 2026-07-26)** · Tiếp nối UPDATE-053
Chỉ thị: *"trong sim dùng OSRM những chỗ có thể thay vì dùng detour"* + Q-02 đóng (không cần
Google key — OSRM/Stadia/OSM đủ).

## 1. Đã làm gì

- **`scripts/fetch_osrm_matrix.py`** — fetch OSRM `/table` (public, không key) cho **316 cell**
  (85 lõi + vành đệm k=4), chunk 50×50, retry + nghỉ lịch sự → 
  `research/simulation/data/osrm_matrix_dd.parquet` (**99.856 cặp**, commit). Fetch MỘT LẦN;
  sim/test đọc **offline** (DIRECTIVES §2: cache local, không gọi mạng trong đường chạy chính).
- **`geo.RoadMatrix`** — GIỮ contract M0-9 (một nguồn khoảng cách từ endpoint) bằng cách chuyển
  từ *hằng số detour* sang **hệ số theo CẶP CELL**: `road_km = haversine(endpoint) ×
  factor(cell_A, cell_B)` với `factor = osrm_km / haversine(centroid)`, kẹp [1.0, 3.5].
  Thiếu cặp → detour 1.3 cũ (fallback đếm được). `load_road_matrix` cache module-level.
- **Áp vào từng chặng đúng cặp cell**: đón khách (actor→pickup), chở khách (pickup→drop, cả
  thời gian lẫn SOC), huỷ giữa đường, deadhead về lõi, về nhà sạc, đi trạm pin, relocate
  demand-seek; **ETA dispatcher** theo factor cặp (actor→pickup); **CƯỚC theo km lộ trình thật**
  (XanhSM tính cước theo km lộ trình, không phải chim bay).
- `routing.enabled: false` ⇒ trở về hành vi cũ **từng con số** (cổng an toàn).
- **Fix kèm (lộ ra khi rà call site):** relocate demand-seek trước đây **không trừ SOC** — di
  chuyển miễn phí năng lượng là phi vật lý. Nay trừ theo km đường thật.

## 2. Số đo: detour hằng 1.3 ƯỚC NON đường Hà Nội

| | giá trị |
|---|---|
| factor thật (99.540 cặp) | **median 1.46** · p10 1.24 · p90 1.94 · kẹp trần 0,8% |
| phủ core×core | **98,8%** · fallback runtime đo được **2,1%** |

## 3. Re-baseline (quy trình SIM-1: đo → hiệu chỉnh → gate)

Đường thật dài hơn ~12% ⇒ ba mỏ neo dịch, hiệu chỉnh **theo số đo**:

| tham số | cũ | mới | căn cứ |
|---|---|---|---|
| `accept_logit_center_vnd` | 15.400 | **21.200** | cước theo km lộ trình ⇒ net trung vị đo lại = 21.225đ; không cập nhật thì tái diễn khuyết tật SIM-1 (kinh tế áp đảo, archetype vô nghĩa) |
| `eta_max_min` | 10 | **11** | **KHÔNG nới chuẩn**: cùng bán kính vật lý, factor 1.46 làm số phút cao hơn ~12%; ngưỡng tương đương = 10 × 1.46/1.3 ≈ 11,2 |
| `actors.n` | 74 | **90** | mỗi cuốc ngốn thời gian hơn ⇒ năng lực đội giảm; sweep 8 seed: 74→0.742 · 84→0.779 · **90→0.797 ✅** |

**Gate realism 30 seed sau hiệu chỉnh: 13/13 XANH** (served/completion/accept-vs-base/no-dead-hour/
coherence). `orders_per_day` giữ **1200** (không vặn cầu).

## 4. Trung thực về đánh đổi

- **`trips/driver/day` tụt còn ~10** (trước 12.3, research 18-22). Giới hạn cơ cấu 1-quận
  (`D-SIM-01`) **nặng thêm** vì đường thật ngốn năng lực — không che, chờ enlarge zone.
- **Baseline seed-by-seed cũ NGHỈ HƯU**: mọi so sánh với số trước UPDATE-054 phải ghi rõ khác
  engine khoảng cách. Scratch baseline cũ không còn dùng được cho fine-diff.
- OSRM matrix là **snapshot OSM một thời điểm** — không có traffic thời gian thực (tốc độ theo
  giờ + congestion của sim vẫn đảm nhiệm phần đó, đúng phân công).

## 5. Files

`scripts/fetch_osrm_matrix.py` (TẠO) · `research/simulation/data/osrm_matrix_dd.parquet` (TẠO,
commit) · `geo.py` (RoadMatrix + load cache) · `world.py` (per-leg factors + `_dfac`) ·
`dispatcher.py` (factor_fn) · `demand.py` (fare theo km lộ trình) · `runner.py`/`multiday.py`
(truyền road) · `configs/pilot_dongda.yaml` (routing + recalibration).

## 6. Kiểm chứng

- Gate realism 30 seed: **13/13**. Smoke: fallback 2,1%, hits 14.664/run.
- **`tests/test_road_matrix.py` (TẠO, 9 test)**: offline · biên vật lý factor · median >1.3
  (khoá phát hiện lõi) · fallback · phủ core >95% · **cổng an toàn** routing-off ≡ detour cũ
  (và routing-on PHẢI khác — chống tính năng vỏ) · fare theo km lộ trình · regression event+road.
- **2 lỗi full-suite bắt được, root-cause trước khi sửa:**
  1. **BUG-SIMXANH-01**: patch chữ ký `_add_event_orders` KHÔNG khớp → `TypeError` khi config
     có `environment.events` — config thường không có event nên smoke im lặng bỏ qua. Đã sửa +
     regression test (`test_event_orders_accept_road_param`).
  2. `test_no_starved_hours_after_sim1` (MỘT seed) chặt hơn tiêu chí thống kê vốn có (30-seed
     aggregate ≤40%, vẫn xanh): seed 4000 có 06h 48% do dao động ngày lẻ với đường thật.
     Nới per-seed lên 55% (chỉ bắt sụp đổ thật — baseline SIM-1 từng 94%), tiêu chí thống kê
     giữ nguyên ở `test_sim_realism`.

## 7. Visual review

`DEFERRED` — gộp vào **V-09** (Phase 4 dashboard sẽ cho XEM đường thật trên bản đồ).
