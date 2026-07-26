# UPDATE-049 — SIM-5 (phase cuối): bộ metric đầy đủ + regen 13 bảng `l1r` từ engine mới

Ngày: 2026-07-26 · Track: **A (SIM overhaul)** · Phase: **5/5 — KẾT THÚC LỘ TRÌNH**
Tiếp nối: 044 (`9de4074`) · 045 (`aa58998`) · 046 (`4cea652`) · 047 (`a7c2597`) · 048 (`24c1627`)

## 1. Vì sao

Hai món nợ cuối của Track A:

1. **Bộ metric chưa phủ spec §6** — thiếu *thời gian chờ khách* và *mật độ cung/cầu hex × giờ*
   (phép đo đã tìm ra khuyết tật SIM-1 nhưng chỉ tồn tại dạng script dùng một lần).
2. **`data/mock/realdata-v1/` sinh TRƯỚC SIM-1 ⇒ ĐÃ CŨ.** Đây là món nợ nghiêm trọng: Cường chốt
   (`DIRECTIVES` §1) *"bản publish cuối cùng CHẠY TRÊN MOCK DATA"*. Bộ cũ mang hành vi của một thế
   giới **đã bị bác bỏ** (served 61.9%, accept 96.3%, completion 99.6%, không có huỷ-sau-nhận).
   Mọi solver/advisor đang được thử trên nền sai.

## 2. Đã làm gì

- **`src/gsm_sim/sim_metrics.py` (MỚI)** — `customer_wait()` · `supply_demand_density()`
  (hex × giờ, có `starved_hours`) · `driver_metrics()` (gộp **từ `journey`**, không tính lại) ·
  `system_metrics()` (kế thừa `summarize()`, chỉ bổ sung) · `full_report()`.
  Advisor A/B **uỷ quyền** cho `parallel.compare` — không nhân bản.
- **Manifest truy vết engine**: thêm `engine_commit` + `engine_note`. Bộ cũ **không** ghi engine
  nào tạo ra nó — chính vì thế nó lạc hậu suốt SIM-1..4 mà không ai phát hiện.
- **`scripts/regen_mock.py`** — regen + in bảng so sánh CŨ→MỚI.
- **Regen 90 ngày** từ engine `24c1627`.

## 3. Bộ data MỚI vs CŨ (`driver_statistic_daily`, 90 ngày)

| chỉ số | CŨ | **MỚI** | đổi |
|---|---|---|---|
| số driver-day | 9.259 | **11.378** | +2.119 |
| tỷ lệ nhận (median) | 0.8696 | **0.9091** | +0.0395 |
| tỷ lệ nhận p10 | 0.7500 | 0.7647 | +0.0147 |
| tỷ lệ hoàn thành (median) | 0.9444 | 0.9545 | +0.0101 |
| tỷ lệ huỷ (median) | 0.0500 | 0.0417 | −0.0083 |
| cuốc/ngày (median) | 15.0 | 15.0 | 0 |
| trips (tổng bản ghi) | 145.573 | **169.059** | +23.486 |

**Nhất quán sim↔data đạt được:** acceptance median trong data = **0.909**, hành vi sim = **~0.910**.
Trước SIM-1 hai con số này là 0.88 vs 0.96 — hai tầng kể hai câu chuyện khác nhau.

## 4. Phát hiện: driver-day có acceptance = 1.00 tăng 12% → **23%**

Thoạt nhìn giống hồi quy chất lượng. Điều tra:

- **77%** số ca 1.00 có **≥10 request** ⇒ KHÔNG phải mẫu nhỏ.
- Chủ yếu là `bike-electric` (1.893/2.617), tức nhóm **do sim sinh**.
- Nhưng archetype accept cao (P3 .98, P5 .97, P2 .95) nhận trọn 15 offer có xác suất **~0.74** —
  hoàn toàn bình thường.

**Kết luận: KHÔNG phải hồi quy, mà là bản cũ MƯỢT GIẢ TẠO.** Bản cũ tổng hợp acceptance bằng
`rng.gauss(target, 0.04)` nên gần như không bao giờ rơi đúng 1.00. Bản mới là **tỷ số hai số
nguyên thật** (accepted/requested) — dữ liệu thật của GSM cũng vậy, nên cũng dồn ở 1.00.
Đã thêm **lan can** `test_acceptance_ones_are_explainable`: tỷ lệ 1.00 phải < 40% **và** vẫn còn
>15% driver-day dưới ngưỡng thưởng (dư địa advisor). Không siết chặt hơn vì sẽ là ép dữ liệu
thật theo hình dung mượt mà của mình.

## 5. Bốn vòng verify trên data MỚI

| vòng | kết quả |
|---|---|
| **1. Schema** | ✅ 13 bảng, tên/số cột khớp CHÍNH XÁC metadata GSM |
| **2. Thống kê ≥30 seed** | ✅ **BIKE 6/6 PASS, 0 GAP** (trước có gap T-021). Đáng chú ý: **giờ online median 8.79h** — trước là gap ~4.5h so thiết kế 8-10h |
| **3. Nhất quán** | ✅ acceptance data 0.909 ≈ sim 0.910; test coherence SIM-1 xanh |
| **4. Đối kháng** | ✅ không idle>online, không cuốc-khi-offline, không tỷ lệ thoái hoá |

## 6. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/sim_metrics.py` | **TẠO** |
| `src/gsm_core/mockgen/realdata.py` | sửa — `_git_commit()` + manifest v3 |
| `scripts/regen_mock.py` | **TẠO** |
| `tests/test_sim_metrics.py` | **TẠO** — 9 test |
| `tests/test_realdata_gen.py` | sửa — +1 lan can tỷ lệ 1.00 |
| `data/mock/realdata-v1/` | **REGEN** (parquet/csv gitignored; commit manifest) |

## 7. Kiểm chứng

- **Full suite: 446 passed, 5 skipped** (trước 437).
- **Không hai nguồn sự thật**: test bắt `system_metrics` giữ nguyên mọi số của `summarize()`;
  `driver_metrics` khớp `journey`; tổng cuốc per-driver = cuốc hệ thống.
- **`starved_hours == []`** — không giờ nào bị bỏ đói (bảo vệ thành quả SIM-1).
- **Thứ tự archetype giữ**: P4 (tân binh) nhận thấp hơn P3 (top) — nếu mất thì mọi kết luận
  advisor vô nghĩa.

## 8. Adversarial self-review / flaws found

1. **Nguồn sự thật thứ hai** — rủi ro chính của module gộp metric; đã chặn bằng 3 test nhất quán. ✅
2. **Kết luận vội "chất lượng data giảm"** khi thấy 1.00 tăng — đã điều tra thay vì đoán, và kết
   luận ngược lại (bản cũ mới là bản giả tạo). ✅
3. **Regen mà không so sánh** — đã chụp số liệu bộ cũ TRƯỚC khi ghi đè; không chụp thì mất vĩnh viễn. ✅
4. **Data không truy vết được engine** — nguyên nhân gốc khiến bộ cũ âm thầm lạc hậu; đã thêm
   `engine_commit`. ✅

**FLAW ghi nhận:**

- **F-SIM5-A (TB) — `verify_realdata_stats.py` sinh data RIÊNG (30 seed × 1 ngày), không đọc bộ
  90 ngày đã ghi.** Nghĩa là vòng 2 kiểm *generator*, không kiểm *artefact đang nằm trên đĩa*.
  Hai thứ hiện trùng nhau vì cùng engine, nhưng sẽ lệch nếu ai regen bằng config khác. Nên thêm
  chế độ đọc thẳng thư mục.
- **F-SIM5-B (TB) — cuốc/tài xế/ngày median 13** (target 10-30 PASS) nhưng vẫn dưới thực tế
  18-22 của tài xế full-time. Nguyên nhân **cơ cấu** đã ghi ở `D-SIM-01` (cầu 1 quận). Không sửa
  bằng cách vặn số.
- Kế thừa chưa giải: `Q-01`/`D-SIM-02` (thưởng tân binh), `D-SIM-03` (1/9 solver nối vào action
  space), `D-SIM-04` (adherence là giả định), `D-SIM-06/07`.

## 9. Visual review

**Status: `DEFERRED` (V-06)** — cần Cường xem: dashboard chạy trên **data mới** + bộ metric mới
(`sim_metrics.full_report`). Tab ⚖️ A/B vẫn **chưa làm** (nợ từ SIM-4).

## 10. Trạng thái Track A sau SIM-5

**Lộ trình SIM-1..SIM-5 đã xong.** Sim hiện: realism đạt dải thực tế · hành trình từng tài xế có
lý do quyết định · advice dịch được thành hành động · đo được A/B có CI · data 13 bảng sinh từ
engine mới, truy vết được commit.

**Việc đáng làm tiếp (ngoài lộ trình):** `D-SIM-03` mở rộng action-space (hiện chỉ 1/9 solver có
kênh tác động — đây là giới hạn lớn nhất của kết quả A/B), rồi Track B/C/D/E.
