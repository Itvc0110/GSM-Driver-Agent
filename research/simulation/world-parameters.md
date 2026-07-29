# Research — Tham số thế giới giả lập Hà Nội (bike điện, trạm đổi pin, dispatcher)

Ngày: 2026-07-21 · Nguồn: T-016 (research đợt 3) · Phục vụ: `specs/simulation-twin-world.md` §2, §4
Quy ước: **[NGUỒN]** = có URL kiểm chứng; **[ƯỚC LƯỢNG]** = suy luận kèm căn cứ; **[ĐỢT 1]** = research nội bộ trước đó. Mọi tham số vào config sim phải kèm nhãn assumption (seed, nguồn, ngày) — không trình bày như số thật GSM/VinFast.

## 1. Trạm đổi pin VinFast tại Hà Nội

### Facts có nguồn

| Mục | Giá trị | Nguồn |
| --- | --- | --- |
| Quy mô toàn quốc | ~4.500 tủ đầu 2026; mục tiêu 45.000 tủ/34 tỉnh Q1/2026; 150.000 đến 2028 | [VinFast IR](https://vinfastauto.us/investor-relations/news/vinfast-launches-four-new-electric-scooter-models-completes-installation-of), [Electrek](https://electrek.co/2026/03/31/vinfast-is-going-all-in-on-electric-scooters-with-massive-battery-swapping-rollout-in-vietnam/), [Dân trí](https://dantri.com.vn/o-to-xe-may/vinfast-phu-dau-honda-bang-3-dong-xe-may-dien-doi-pin-lap-4500-tram-20260115131932404.htm) |
| Khe/tủ | **6 slot (5 pin + 1 trống nhận pin cũ)** | [Phụ Kiện VinFast](https://phukienvinfast.vn/san-pham/tu-doi-pin-xe-may-dien-vinfast/), khớp tag OSM `capacity=6` |
| Pin đổi | Pack LFP **1,5 kWh** | [Electrive](https://www.electrive.com/2025/08/25/vinfast-to-install-150000-battery-swapping-stations-in-vietnam/) |
| Thời gian đổi | ~1–2 phút/lần, tự phục vụ qua app | [zauto.vn](https://zauto.vn/tram-doi-pin-xe-may-dien-vinfast-tai-ha-noi-danh-sach-dia-chi-chi-tiet/) |
| Phí | 9.000đ/lượt; **⚠ SỬA SAI SỰ THẬT (29-07):** Xanh SM Platform miễn phí đổi pin **KHÔNG GIỚI HẠN** vì độc quyền, hiệu lực tới **31/03/2029** (greensm official 26/03/2026). Mốc 30/6/2028 KHÔNG áp dụng cho Platform — đó là mốc "miễn 20 lượt/tháng cho khách thường". Chi tiết: `research/economics/driver-cost-structure-2026.md`. | [Electrive](https://www.electrive.com/2025/08/25/vinfast-to-install-150000-battery-swapping-stations-in-vietnam/), [Tiền Phong](https://tienphong.vn/vinfast-evo-doi-pin-sieu-toc-co-hoi-de-tai-xe-cong-nghe-toi-uu-thu-nhap-post1816460.tpo), `research/economics/driver-cost-structure-2026.md` |
| Giờ hoạt động | Đa số 24/7 | zauto.vn |
| Quá tải ghi nhận | Cục bộ giờ cao điểm khu trung tâm; "xí chỗ" bằng mũ bảo hiểm; app báo còn pin nhưng tủ hết pin đầy; VinFast dự kiến thêm **đặt chỗ đổi pin** trong app | [Báo Xây Dựng 23/6/2026](https://xe.baoxaydung.vn/tu-doi-pin-xe-may-dien-qua-tai-cuc-bo-tai-xe-cong-nghe-dung-chieu-xi-cho-192260616224440811.htm), khớp [ĐỢT 1] |

### Dữ liệu OSM thực (query Overpass trực tiếp 2026-07-21)

- Bbox nội thành (20.9–21.15, 105.73–105.95): **144 node** "Tủ đổi pin VinFast", tag chuẩn `amenity=vending_machine` + `battery_swap=yes` + `brand=VinFast` + `capacity=6` + `charge=9000 VND/battery`. → **Sim dùng được tọa độ trạm THẬT từ OSM.**
- Phân bố theo góc phần tư: Tây Nam 56 (Thanh Xuân–Hà Đông–Nam Từ Liêm), Đông Nam 49 (Đống Đa–HBT–Hoàng Mai), Đông Bắc 13 (Tây Hồ–Long Biên), Tây Bắc ~26. Dày ở vành Thanh Xuân–Hà Đông–Từ Liêm + trung tâm nam; thưa bắc/đông sông Hồng.
- 144 là số **đã map trên OSM** — chắc chắn undercount. [ƯỚC LƯỢNG] thực tế nội thành giữa 2026: 500–1.500 tủ.
- Đừng trộn với 202 node `amenity=charging_station` (trạm sạc ô tô V-Green). Overpass endpoint hay 429/504 → retry/backoff; lưu snapshot JSON vào repo kèm ngày + nguồn OSM (ODbL).

### Tham số trạm cho sim

| Tham số | Đề xuất | Căn cứ |
| --- | --- | --- |
| N trạm | 144 (tọa độ OSM thật); scenario "dày" ×3 nhân bản quanh POI | OSM + [ƯỚC LƯỢNG] |
| Khe/tủ | 6 (5 pin buffer + 1 trống) | [NGUỒN] |
| Thời gian đổi | 90s/pack (uniform 60–120s) | [NGUỒN] 1–2 phút |
| Sạc lại pin trong tủ | ~1,5–2h/viên → throughput bền vững ~2,5–3 pin đầy/giờ/tủ | [ƯỚC LƯỢNG] từ pack 1,5 kWh, sạc ~0,8–1 kW |
| Hàng đợi | FIFO; mô phỏng "app báo còn pin nhưng hết pin đầy" bằng SoC từng viên trong tủ | hành vi Báo Xây Dựng |

## 2. Vận hành bike Hà Nội

| Tham số | Đề xuất | Căn cứ |
| --- | --- | --- |
| Tốc độ cao điểm (config hiện hành `peak_hours: [6,7,8,16,17,18]`) | 15–20 km/h (chọn 17) | [NGUỒN] [thienthanhlimousine](https://thienthanhlimousine.com/10km-di-xe-may-bao-nhieu-phut/), [fxbike](https://fxbike.vn/10km-di-xe-may-bao-nhieu-phut/) |
| Tốc độ ngoài cao điểm | 22–28 (chọn 25) | [ƯỚC LƯỢNG] phần trên dải 15–30 |
| Tốc độ đêm 21h–6h | 28–35 | [ƯỚC LƯỢNG]; trần pháp lý 50–60 ([baochinhphu](https://baochinhphu.vn/quy-dinh-ve-toc-do-toi-da-cua-xe-co-gioi-ap-dung-tu-01-01-2025-102241127101044466.pdf)) |
| Quãng đường cuốc | lognormal median ~3,5 km (3–5, đuôi 10–12) | [ƯỚC LƯỢNG] từ giá cuốc 15–30k [ĐỢT 1] + [daytripsvietnam](https://daytripsvietnam.com/guides/vietnam-grab-prices-2026/) |
| Thời gian cuốc | 10–15 ph cao điểm, 8–12 thấp điểm | = distance/speed |
| Pickup | 0,5–1,5 km (~2–6 ph) — là OUTPUT của dispatcher, không hard-code | [ƯỚC LƯỢNG] |
| Pin Feliz S/Evo200 (sạc cắm) | 3,5 kWh; danh định ~200 km; thực 140–180; **chạy dịch vụ 100–130 km** | [imotorbike](https://news-vn.imotorbike.com/2026/05/xe-may-dien-vinfast-evo200-chay-duoc-bao-nhieu-km/), khớp [ĐỢT 1] 100–120 |
| Xe đổi pin (Evo swap/Evo Lite) | pack 1,5 kWh ~85 km danh định; **dịch vụ ~55–70 km/pack** | [minhlongmoto](https://muaxe.minhlongmoto.com/vinfast/evo-lite/), hệ số 0,65–0,8 [ƯỚC LƯỢNG] |
| Tiêu hao | Feliz/Evo200: 0,85 %/km (~27 Wh/km thực); xe swap: 1,4–1,8 %/km/pack | [ƯỚC LƯỢNG] = 100/tầm thực |
| Ngưỡng đi đổi pin | SoC 15–25% (hoặc pack còn <20 km) | [ƯỚC LƯỢNG] hành vi + pattern [ĐỢT 1] |

**Cập nhật config hiện hành (29-07):**

(a) Km lộ trình nay là **THẬT** từ ma trận OSRM offline (`routing.enabled: true`, factor median
**1,46**) + tầng congestion (cap 0,35, normalize theo `global_peak`); `detour_factor: 1.3` cũ chỉ
còn dùng làm **fallback** khi OSRM không trả được route.

(b) `drop_demand_alpha: 0.4` — điểm trả cuốc bám theo cầu: `m(c) = 1 + α·(w/w̄ − 1)` (w = cầu tại
cell điểm trả, w̄ = cầu trung bình); α=0 cho corr −0,22 (điểm trả LỆCH khỏi cầu), α=0,4 → +0,418
(điểm trả bám cầu thật hơn).

**Khuyến nghị**: sim v1 mô phỏng **đội xe đổi pin** (khớp cơ chế trạm 6-slot); đội Feliz S sạc cắm 4–10h là biến thể sau (tài xế nghỉ trưa sạc thay vì ghé trạm).

## 3. Dispatcher baseline

Industry công khai: DiDi giải **bipartite matching theo batch bằng Hungarian** trên đồ thị driver–order trong window ([DiDi INFORMS 2020](https://tonyzqin.wordpress.com/wp-content/uploads/2020/11/inte.2020.1047.pdf), [arXiv:2408.10479](https://arxiv.org/html/2408.10479v1)); batch-delay được nghiên cứu riêng ([Springer 2025](https://link.springer.com/article/10.1007/s11518-025-5710-8)).

```text
mỗi TICK (dispatch_tick_s = 5s):
  O = orders chưa gán (patience 2 tầng: lognormal median 5', sigma 0.5, cap 10' rồi expire)
  D = drivers idle, SoC đủ (SoC sau cuốc dự kiến > ngưỡng đổi pin)
  # Tầng 1 — bán kính H3
  candidates(o) = drivers trong grid_disk(h3(o.pickup), k=candidate_ring_k=4) tại res 9
  rỗng → nới dần tới candidate_ring_k_max=6; vẫn rỗng → giữ sang tick sau
  # Tầng 2 — matching
  matching: batch (Hungarian) — bipartite cost(o,d)=ETA_pickup, giải scipy linear_sum_assignment
              chỉ nhận cặp ETA ≤ eta_max_min=11 phút; cặp loại → tồn sang tick sau
  greedy nearest (ETA min) = baseline/đường lui khi cần so sánh, không còn là default
```

**Config hiện hành (29-07, đã ship):** H3 **res 9**, `candidate_ring_k: 4` (nới dần tới
`candidate_ring_k_max: 6`), `eta_max_min: 11`, `dispatch_tick_s: 5`, patience 2 tầng lognormal
median 5', sigma 0.5, cap 10'. `matching: batch` (Hungarian) là **mặc định đã ship** (UPDATE-080);
greedy chỉ còn là baseline/đường lui.

## 4. Quy mô đề xuất

**⚠ Nhãn (29-07):** bảng dưới đây là quy mô **THÀNH PHỐ** — **chưa triển khai** (D-SIM-01 defer).
Pilot hiện hành khác hẳn quy mô này: **1 quận, H3 res 9, 90 tài xế, 1.200 đơn/ngày**
(`research/simulation/pilot-world-dongda.md`).

| Tham số | Đề xuất | Căn cứ |
| --- | --- | --- |
| Khu vực | 12 quận nội thành cũ ~300 km², bbox (20.95–21.12, 105.75–105.92) | chuẩn hành chính trước 7/2025 |
| H3 res | **8** → ~400–420 cells | 300/0,737 ≈ 407 |
| N tài xế | **500** (dải 200–1.000) | ~1,2 driver/cell; Hungarian 500×500/tick vẫn ms [ƯỚC LƯỢNG]; tham chiếu [HRSim](https://arxiv.org/abs/2505.17758), [FleetPy](https://arxiv.org/pdf/2207.14246) |
| N đơn/ngày | 8.000–12.000 (≈16–25 cuốc/tài xế) | [ĐỢT 1] 15–30 cuốc/ngày + hour-shape `specs/mock-order-distribution.md` |
| Thời lượng | 24h/run, warm-up 1h, tick dispatch 2–5s, event-driven trip; 20–30 seeds | thông lệ + evaluation-methodology.md |

## 5. OSM/bản đồ

- Trạm: query chuẩn `node["amenity"="vending_machine"]["battery_swap"="yes"]["brand"="VinFast"]` — đã kiểm chứng hoạt động.
- Ranh giới quận: relation `admin_level=6` trong Hà Nội — **CẢNH BÁO**: từ 1/7/2025 VN bỏ cấp quận/huyện, OSM có thể đã chuyển sang phường (`admin_level=8`); nếu mất relation cũ → dùng bbox + H3 làm khung chính, ranh giới chỉ để hiển thị. [KIỂM TRA LÚC CODE]
- Sinh trạm giả cho scenario dày: đặt tại POI `shop=supermarket|mall`, `amenity=fuel|parking`, khu Vinhomes (khớp pattern thực), mật độ ∝ đơn/cell, nhãn MOCK.
