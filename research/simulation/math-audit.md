# Audit công thức toán + độ phủ biến của sim (2026-07-21)

Trạng thái: DRAFT — kiểm tra thủ công code hiện tại (`src/gsm_sim/`), chờ đối chiếu research biến môi trường.
Mục đích: bắt lỗi toán, tìm biến còn thiếu, chuẩn hóa công thức kết hợp nhiều factor trước khi làm giàu.

## A. Lỗi/điểm cần sửa phát hiện khi đọc code

### A1. `_hour_intensity` bỏ mass đêm nhưng orders_per_day KHÔNG đổi nghĩa → nén demand (đã harmonize spec nhưng code chưa khớp)
`demand.py:60-68`: chỉ giữ giờ trong window [5,24), chuẩn hóa tổng=1, rồi `lam = orders_per_day × share`. Nghĩa là 1200 đơn bị **dồn vào 19h** thay vì 24h → cường độ/giờ cao hơn ~7% so với nếu tính cả đêm. Spec §4 nói "1200 = kỳ vọng TRONG window" nên **đúng ý định**, nhưng cần ghi rõ trong config comment (đang mơ hồ). KHÔNG phải bug, là quy ước — xác nhận lại.

### A2. Poisson theo GIỜ, không theo bucket nhỏ → demand giật cục ở biên giờ
`demand.py:99-103`: `n_h ~ Poisson(orders_per_day × hour_share[h])`, rồi rải uniform trong [h*60, h*60+60]. Hệ quả: cường độ **hằng số trong mỗi giờ**, nhảy bậc tại phút 0 mỗi giờ (vd 8h=1.00 tụt xuống 9h=0.70 đột ngột). Thực tế demand mượt. → Nên nội suy tuyến tính giữa các mốc giờ HOẶC sinh theo bucket 15ph. Ảnh hưởng: pattern giờ răng cưa, có thể lệch matching ở biên giờ. Mức trung bình.

### A3. `_sample_drop` — công thức chọn cell trả có 2 magic number chưa versioned
`demand.py:116-127`: `k = min(buffer_k+3, round(dist_km/0.35)+1)` (0.35 = km/cell res9 ước lượng) và `weights = exp(-dists/0.5)` (0.5 = bán kính mềm). Hai số 0.35 và 0.5 **hard-code trong hàm**, không ở config. Cần đưa ra config + ghi nguồn. `0.35km/cell`: res9 edge ~0.174km, đường kính ~0.35km — hợp lý nhưng nên tính từ `h3.average_hexagon_edge_length` thay vì hằng.

### A4. Distance = centroid haversine × (1/speed) — thiếu hệ số đường vòng (detour factor)
`geo.py cell_distance_km` + `dispatcher.py:70`: ETA = khoảng cách chim-bay-centroid / tốc độ. Thực tế đường đi dài hơn đường chim bay ~1.3–1.4× (circuity/detour factor đô thị). → Mọi ETA/pickup/trip đang **ngắn hơn thực ~30%**. Đây là lý do pickup ETA p90 chỉ 6ph. Cần hệ số `detour_factor` (~1.3) trong config, nhân vào mọi quãng đường di chuyển. **Ưu tiên cao** — ảnh hưởng ETA, tiêu pin, thời gian.

### A5. `accept_order` — magic numbers trong logit chưa versioned + đơn vị lẫn lộn
`behavior.py:41-44`: `net = gross − pickup_dist_km×3000`; `x = (net−6000)/8000 + logit(accept_base)`. Các số 3000 (chi phí/km đến đón?), 6000, 8000 (scale) **hard-code**. Cần: đưa ra config, đặt tên (cost_per_pickup_km, logit_center, logit_scale), ghi rõ đơn vị (VND). Toán logit đúng cấu trúc nhưng tham số bịa hoàn toàn.

### A6. `demand_hint` nhiễu có thể ÂM nhưng lại clamp về 0 → mất thông tin ở tail
`world.py _actor_demand_hint`: `base × (1 + N(0,σ))`, clamp max(0,...). Với σ=0.6 (P4), P(1+N<0)=P(N<-1)=16% → 16% số cell bị ép về 0 → tân binh "mù" nhiều cell. Có thể là intended (tân binh sai nhiều) nhưng dùng multiplicative noise gây skew. Cân nhắc: nhiễu lognormal `base × exp(N(0,σ))` (luôn dương, không clamp, đúng bản chất "sai số nhân"). **Mức trung bình.**

### A7. Trip duration/pin dùng tốc độ TẠI THỜI ĐIỂM BẮT ĐẦU cuốc, không đổi giữa cuốc dài
`world.py:162-177`: `_serve_trip` lấy `hour` 1 lần đầu, cuốc 15-30ph có thể vắt qua ranh giới giờ (peak→offpeak) mà tốc độ giữ nguyên. Sai số nhỏ với cuốc ngắn, đáng kể với cuốc dài qua biên giờ. Mức thấp.

### A8. `battery_stranded` check `soc<=0` SAU khi trừ cả cuốc — nhưng dispatcher đã lọc `soc-total>8`
`world.py:180-183`: dispatcher chỉ gán khi `soc − total_km×pct > 8` (world.py:~145), nên stranded gần như không xảy ra (đang 0). Variance thực tế (tiêu pin dao động, tắc đường) chưa mô hình → stranded=0 là artifact. Nếu muốn stranded có ý nghĩa cần thêm nhiễu tiêu pin. Mức thấp (chờ realism research).

## B. Biến CÒN THIẾU (so với ride-hailing thực) — chờ research định lượng

| Biến | Hiện trạng | Ảnh hưởng lên | Cần công thức |
| --- | --- | --- | --- |
| **Mưa** | KHÔNG có | tốc độ ↓, demand ↑ (rồi bão hòa?), supply ↓ (tài xế nghỉ) | research |
| **Ngày trong tuần** | KHÔNG (chỉ 1 ngày, dow_factor có trong mock spec nhưng code chưa dùng) | demand shape | dow_factor × hour |
| **Sự kiện** (concert/lễ) | KHÔNG | demand spike cục bộ theo cell×giờ | research |
| **Detour factor** | KHÔNG (A4) | mọi ETA/quãng đường | ×1.3 |
| **Nhiễu tiêu pin** | KHÔNG (A8) | stranded, biến động SOC | research |
| **Nhiệt độ → tầm pin** | KHÔNG | range xe điện mùa hè HN | research |
| **Tắc đường theo cell** | KHÔNG (chỉ theo giờ toàn cục) | tốc độ không đồng nhất không gian | research |
| **No-show / hủy khách** | có patience (hủy vì chờ) nhưng KHÔNG có no-show sau khi match | completion rate | research |
| **Surge pricing** | KHÔNG (cố ý — xác nhận với research) | — | bỏ qua? |

## C. Vấn đề TRUNG TÂM — kết hợp nhiều multiplier (yêu cầu Cường)

Hiện tại demand chỉ có `orders_per_day × hour_share × cell_weight`. Khi thêm mưa/ngày/sự kiện sẽ thành `base × f_hour × f_dow × f_weather × f_event × f_cell`. Rủi ro **nhân chồng phi lý**: mưa to (×1.3) × sự kiện (×2) × peak (×1.3) = ×3.4 có thể vượt xa thực tế.

Nguyên tắc cần chốt (chờ research mục 8 xác nhận):
- Rate Poisson = `base × Π factors` là chuẩn thống kê (independent multiplicative effects trên intensity) NHƯNG cần **cap tổng** hoặc **diminishing** khi nhiều factor cùng dương.
- Cân nhắc: factor trong **log-space** cộng lại rồi cap, hoặc mỗi factor có trần riêng.
- Tốc độ (khác demand): mưa giảm tốc + peak giảm tốc — KHÔNG nên nhân 2 lần giảm mạnh; nên lấy `min` hoặc kết hợp có sàn.
- Supply-side (tài xế nghỉ khi mưa) và demand-side (khách gọi nhiều khi mưa) tác động NGƯỢC lên fulfillment — phải mô hình cả hai, không chỉ demand.

→ Sau research: viết `specs/environment-variables.md` định nghĩa từng factor + công thức kết hợp CHUẨN, tất cả tham số trong config, có test cho biên (mọi factor=1 → baseline; factor cực đại không vượt trần).

## D. Điểm TỐT (không cần sửa)
- Zone weight, hour intensity chuẩn hóa tổng=1 đúng.
- Patience lognormal, trip lognormal — đúng phân phối.
- Poisson cho demand đếm — đúng.
- RNG tách seed cho demand/actor — nền CRN đúng.
- Logistic accept — đúng cấu trúc (chỉ tham số cần calibrate).
