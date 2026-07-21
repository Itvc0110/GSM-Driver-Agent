# Research — Pilot world: quận Đống Đa, 50 actors (đợt 4)

Ngày: 2026-07-21 · Nguồn: T-022 · Phục vụ: `specs/simulation-pilot-world.md`
Trả lời yêu cầu #2 của Cường: thu hẹp visualization về 1 khu vực nhỏ, 50 actors, demand nghiên cứu/mock theo vị trí×thời gian, H3 cho quận/phường, bản đồ đủ yếu tố.
Data files kèm theo (OSM thật, tải 2026-07-21, license ODbL): `data/battery_nodes.json` (144 tủ toàn HN), `data/batt_dd.json` (11 tủ Đống Đa), `data/poi_dd.json` (POI Đống Đa), `data/dd_geom.json` (polygon 5 phường proxy).

## 1. Quận chọn: ĐỐNG ĐA (ranh giới quận cũ)

| Tiêu chí | **Đống Đa** | Cầu Giấy | Thanh Xuân |
| --- | --- | --- | --- |
| Diện tích | **9,95 km²** | 12,44 km² | 9,17 km² |
| Dân số | ~371,6k (2019) – ~410k (2024) | ~292,5k | ~293,3k |
| Mật độ | **~40.000/km² — cao nhất HN** | ~23.500 | ~32.000 |
| Tủ pin VinFast (OSM thật) | **11** | 9 | 7 |
| Đại học + CĐ (OSM) | 13 + 6 | 19 + 12 | 8 + 2 |
| Bệnh viện (OSM) | **26** (Bạch Mai, Nhi TW, ĐH Y…) | 7 | 10 |
| TTTM / chợ | 3 / 10 | 5 / 14 | 6 / 7 |

Lý do: mật độ dân cao nhất trên diện tích gọn; mix demand đại diện nhất (cư dân + cụm bệnh viện lớn nhất nội thành + 13 đại học + văn phòng Láng Hạ/Thái Hà + chợ); nhiều tủ pin nhất trong 3 ứng viên NHƯNG chính là nơi ghi nhận **quá tải giờ cao điểm** [ĐỢT 1-3] → đúng bối cảnh mô phỏng ràng buộc đổi pin.

**Caveat hành chính:** từ 1/7/2025 VN bỏ cấp quận; OSM đã xóa relation quận cũ (query xác nhận 0 relation admin_level=6). Proxy = hợp **5 phường mới**: Đống Đa, Kim Liên, Ô Chợ Dừa, Văn Miếu–Quốc Tử Giám, Láng (relation IDs 19331655/56/58/59, 19332318); lệch nhẹ ở biên với Ba Đình/Cầu Giấy/HBT — chấp nhận cho sim, ghi caveat.

## 2. Chia H3 (tính thật bằng h3-py 4.5.0 trên polygon OSM)

| Res | Cells lõi | Kể cả chớm biên | Nhận xét |
| --- | --- | --- | --- |
| 8 | 12 | 24 | quá thô cho 50 actors (4+ actor/cell) |
| **9** | **85** | 116 | ~0,105 km²/cell (~350m); 11 tủ pin rơi vào **11 cell khác nhau** |

**Chốt: res 9 làm lưới không gian chính** (85 cells lõi; 116 nếu phủ trọn biên); demand-weight per cell theo POI + dân số; **tổng hợp báo cáo/heatmap ở res 8** (12 cells) qua `cell_to_parent`. Với 1.200 đơn/ngày → ~14 đơn/cell/ngày — mỏng theo giờ nhưng đủ vì đơn sinh theo phân phối trọng số.

## 3. Demand: đơn bike/ngày trong quận (2 cách độc lập)

- **(a) Top-down** từ ~170k đơn bike HN/ngày [mock nội bộ]: nội thành ~80% → 136k; Đống Đa 10,5% dân nội thành × hệ số POI 1,2–1,4 → **~15.000–22.000 đơn/ngày** [ƯỚC LƯỢNG].
- **(b) Bottom-up** từ dân số × tần suất khảo sát (TGM 72,6% user ≥1 chuyến/tuần; 77% ≥3 lần/tháng; Q&Me; chiết khấu bias online panel): ~260k người có smartphone → 105–130k user → 0,13–0,23 chuyến/ngày → ×60–70% bike → **~10.000–21.000** [ƯỚC LƯỢNG].
- **Chốt dải: 15.000–22.000, central ~18.000 đơn bike/ngày** (2 cách giao nhau).

**Scale cho 50 actors Xanh SM:** 18k × thị phần XSM bike ~25–40% (Q&Me 2024: 19% bike; Mordor 2025: >50% toàn thị trường — bike ước giữa 2 mốc) ≈ 4.500–7.200 đơn XSM/ngày → cần ~200–400 tài xế active → 50 actors ≈ 13–25% fleet → đơn "chảy đến" 50 actors ≈ 900–1.500/ngày. Kiểm tra ngược từ 15–30 cuốc/actor: served 750–1.500 + unserved 10–30% → offered 830–2.150. **Khớp.**

**Tham số sim:** `orders_per_day = 1.200` (mặc định), dải config 900–1.800; target unserved 15–20% → ~19–21 cuốc/actor/ngày. Hour-shape: 2 đỉnh 7–9h & 17–19h cường độ ~2× trung bình [ƯỚC LƯỢNG]; chi tiết dùng `specs/mock-order-distribution.md` chiếu xuống cell.

## 4. Bản đồ pilot

- **11 tủ đổi pin THẬT** (tọa độ trong `data/batt_dd.json`): cụm dày phía Đông (Kim Liên–Phương Mai, gần Bạch Mai), thưa phía Tây (Láng) → tự nhiên tạo ràng buộc di chuyển đổi pin.
- **POI anchors THẬT** (`data/poi_dd.json`): 13 đại học, 26 bệnh viện (cụm Bạch Mai–Việt Pháp–Da liễu–Lão khoa góc Đông Nam = mega-anchor; Nhi TW + Phụ sản góc Tây Bắc), 3 TTTM, 10 chợ, trạm bus Cầu Giấy (biên). Anchor biên nên thêm: Ga Hà Nội, Văn Miếu.
- **Trục đường chính (chỉ hiển thị):** Tây Sơn–Nguyễn Lương Bằng–Tôn Đức Thắng; Lê Duẩn–Giải Phóng; Xã Đàn–Đại Cồ Việt; Trường Chinh + Láng (VĐ2); Nguyễn Chí Thanh; Láng Hạ–Giảng Võ; Thái Hà–Chùa Bộc; Phạm Ngọc Thạch; Khâm Thiên; Hoàng Cầu.
- **Phải MOCK:** demand văn phòng (OSM không có POI office tin cậy) → gán weight "office" cho cells dọc Láng Hạ/Nguyễn Chí Thanh/Thái Hà/Hoàng Cầu; weight dân cư theo dân số 5 phường (có số công bố). Công thức: `w_cell = a·pop_density + b·Σ(POI_loại × hệ_số_loại)`, chuẩn hóa tổng 1, nhãn mock + seed.

## 5. Giới hạn

Đếm tủ theo proxy phường mới → lệch ±1–2 ở biên; 170k đơn/ngày là mock nội bộ nên mục 3 kế thừa sai số; khảo sát tần suất là online panel (bias); Overpass attic lỗi nên không lấy được ranh giới quận cũ nguyên bản.

Sources: [VnExpress mật độ](https://vnexpress.net/trac-nghiem-ve-cac-quan-o-ha-noi-4450054-p4.html) · [Nasaland Đống Đa](https://nasaland.vn/ban-do-quan-dong-da.html) · [Wikipedia Cầu Giấy](https://vi.wikipedia.org/wiki/C%E1%BA%A7u_Gi%E1%BA%A5y_(qu%E1%BA%ADn)) · [MaisonOffice Thanh Xuân](https://maisonoffice.vn/tin-tuc/quan-thanh-xuan-ha-noi/) · [Chinhphu 126 phường mới](https://xaydungchinhsach.chinhphu.vn/sap-xep-dvhc-danh-sach-126-xa-phuong-moi-cua-ha-noi-119250622193659228.htm) · [Hanoimoi 5 phường Đống Đa](https://hanoimoi.vn/dong-da-quy-mo-dan-so-dien-tich-5-phuong-du-kien-sau-sap-xep-699629.html) · [TGM tần suất](https://tgmstatbox.com/stats/ride-hailing-app-usage-frequency-in-vietnam/) · [TGM 2026](https://tgmresearch.com/ride-hailing-insights-2026/vietnam.html) · [Q&Me bike 2024](https://qandme.net/en/report/motorbike-ride-hailing-popularity-2024.html) · [VnExpress Mordor >50%](https://vnexpress.net/mordor-intelligence-xanh-sm-vuot-50-thi-phan-goi-xe-cong-nghe-5015512.html) · Overpass API queries trực tiếp
