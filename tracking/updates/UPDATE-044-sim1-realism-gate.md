# UPDATE-044 — SIM-1 "Realism gate": sửa 3 tỷ lệ nền của simulation tại GỐC

Ngày: 2026-07-25 · Track: **A (SIM overhaul)** · Phase: **SIM-1 / 5** · Người điều khiển agent: Cường
Spec: `specs/simulation/00-sim-overhaul-master.md` §2, §5 · Chỉ thị: `tracking/DIRECTIVES-2026-07-24.md` §5.7

## 1. Vì sao

Cường (§5.7): *"sim hiện còn nhiều phần rất tệ — ví dụ **tỷ lệ hoàn thành chuyến tổng đang
quá thấp so với thực tế** — và chưa đủ chi tiết."*

Đo thật (seed 42) tìm ra **3 khuyết tật ĐỘC LẬP**, tất cả đều chứng minh bằng số trước khi sửa:

| # | Khuyết tật | Đo được | Thực tế (research) |
|---|---|---|---|
| 1 | **Cung lệch cầu theo giờ** | 05-06h có **0 tài xế** cho 93 đơn (94%/75% hết hạn); 21-23h chỉ 8-10 tài xế cho 168 đơn ⇒ **served 61.9%** | 80-85% |
| 2 | **Logit accept sai hiệu chỉnh** | accept 96.3%; P4 (base 0.80) thực tế nhận **94.1%**, P3 (0.98) nhận 99.5% ⇒ **archetype vô nghĩa** | 0.74-0.97 theo archetype |
| 3 | **Không có huỷ sau khi nhận** | completion **99.6%** ("quá sạch") | ~95% |

**Root cause khuyết tật 2 (đã chứng minh, không phỏng đoán):** `x = (net − 6000)/8000 +
logit(accept_base)`. Cuốc trung bình (gross 20k, pickup 1km → net 17k) cho số hạng kinh tế
**+1.375**, áp đảo `logit(accept_base)` (P4 = −1.39). Sai ở chỗ đặt `logit_center_vnd` =
mốc *hoà vốn* (6000) thay vì *net trung vị thị trường* (đo thật: **15.417đ**) ⇒ z dương với
MỌI cuốc.

## 2. Đã làm gì

### A. Phủ ca theo đường cầu — `src/gsm_sim/archetypes.py`, `configs/pilot_dongda.yaml`
- Thêm **P6 "ca sáng sớm"** (4:40-5:50 → 7-9h ca) và **P7 "ca tối-đêm"** (15-16h → 23-24h).
  Căn cứ: khung vàng sáng 6-8h (10 điểm/cuốc, `research/policy/bonus-programs`) + blog
  official *"kinh nghiệm chạy ca đêm"* (khung 22h-2h **& 4h-6h**).
- Mix: P1 .14 · P2 .20 · P3 .06 · P4 .18 · P5 .12 · **P6 .18** · **P7 .12**.
  Vòng 2 chuyển cung từ **khung trưa DƯ** (1.1-1.5 đơn/tài xế, hết hạn 4-19%) sang **06h ĐÓI**
  (4.9 đơn/tài xế, hết hạn 43%).
- `actors.n` 50 → **74** (sweep thật: 65→77.7% · 70→78.8% · 74→80.4% · 78→81.2%).
- `dispatcher.patience_median_min` 3.0 → **5.0** — *sửa lệch so NGUỒN GỐC*: arXiv 2503.13200
  nói khách huỷ sau **~5 phút**, calibration cũ đặt chặt hơn nguồn.
- `dispatcher.eta_max_min` 8 → **10** (research cho dải 8-10ph).
- **GIỮ P4 tân binh lệch khung** = dư địa advisor theo cá nhân (nguyên tắc spec §7.1).

### B. Hiệu chỉnh lại quyết định nhận đơn — `src/gsm_sim/behavior.py`
Đổi ngữ nghĩa mô hình: **`accept_base` LÀ mức nhận trung bình của archetype**, kinh tế chỉ
**điều biến quanh** nó — `x = logit(accept_base) + w·z`, `z` **kẹp [−2, 2]**, `w = 0.7`.
`accept_logit_center_vnd` 6000 → **15400** (net trung vị đo thật).

### C. Huỷ sau khi nhận — `src/gsm_sim/world.py`
- `behavior.cancel_after_accept_rate = 0.05`. Huỷ xảy ra **giữa đường đi đón** (30-100%
  quãng đón) ⇒ tài xế mất **thời gian + pin thật, doanh thu 0đ** (không phải huỷ "miễn phí").
- Event mới `order_cancelled_after_accept` + terminal state `CANCELLED_AFTER_ACCEPT`.
- **Sửa nghĩa counter**: `orders_cancelled` từ nay CHỈ đếm huỷ-sau-nhận (khớp cột
  `cancelled_count` của `driver_statistic_daily`). Nhánh pin-không-đủ chuyển sang counter
  riêng `orders_soc_skipped` — tài xế **chưa hề nhận đơn** nên không được tính là huỷ.

### D. Khôi phục coherence sim↔data — `adapter_sim.py`, `mockgen/realdata.py`
Chẩn đoán lại **chính xác hơn spec**: `realdata.py` không "override" mù — nó **suy ngược**
accept/cancel từ `profiles.target_acceptance` vì sim cũ nhận ~100%. Trips của tài xế BIKE thì
đã là sim thật.
- `generate_day` xuất thêm kênh nội bộ `_sim_driver_day` (offered/accepted/completed/cancelled).
- `_emit_day(..., sim_stats=)`: **BIKE lấy thẳng counter sim**; **CAR/PREMIUM/RTO giữ target
  profile** vì *không có sim cho họ* — đó là cách sinh duy nhất, không phải "vá".
- Thêm `adapter_sim.entity_tables()` tách bảng L1R thật khỏi kênh nội bộ (`_` prefix) —
  kênh nội bộ **không bao giờ** ghi parquet / vào context pack của advisor.

## 3. Kết quả (gate 30 seed)

| Metric | Trước | **Sau** | Dải mục tiêu | |
|---|---|---|---|---|
| served | 61.9% | **82.3%** (min 78.7 · max 88.6) | 78-88% | ✅ |
| completion | 99.6% | **94.7%** (min 93.1 · max 96.5) | 92-97% | ✅ |
| accept | 96.3% | **91.0%** | bám accept_base | ✅ |
| cancel sau nhận | 0% | **4.8%** | 2-9% | ✅ |
| Giờ hết hạn cao nhất | 05h **94%** | **06h 33%** | ≤40% | ✅ |

**Accept realized vs `accept_base` (khuyết tật 2 đã chết):**

| | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|
| base | .85 | .95 | .98 | **.80** | .97 | .93 | .94 |
| realized | .848 | .932 | .965 | **.781** | .947 | .915 | .897 |
| lệch | −.002 | −.018 | −.015 | −.019 | −.023 | −.015 | −.043 |

P4 tân binh giờ kén hơn P3 top **18.4đ%** (trước: chênh chỉ 5đ% → advisor không có dư địa đo được).

**Coherence sim↔data:** `driver_statistic_daily` của BIKE giờ có acceptance median **0.917**
(sim: 0.910) — cùng một sự thật. CAR/RTO 0.882 (target profile, có nhãn rõ).

## 4. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/archetypes.py` | sửa — thêm P6/P7, thu hẹp khung P6 về 4:40-5:50 |
| `src/gsm_sim/behavior.py` | sửa — mô hình accept mới (`ECON_WEIGHT`, kẹp z) |
| `src/gsm_sim/world.py` | sửa — huỷ sau nhận, terminal state mới, tách counter SOC |
| `src/gsm_sim/entities.py` | sửa — `orders_soc_skipped` + làm rõ nghĩa `orders_cancelled` |
| `configs/pilot_dongda.yaml` | sửa — n/mix/patience/eta/center/cancel-rate (có comment căn cứ) |
| `src/gsm_core/mockgen/adapter_sim.py` | sửa — `_sim_driver_day` + `entity_tables()` |
| `src/gsm_core/mockgen/realdata.py` | sửa — BIKE đọc counter sim |
| `tests/test_sim_realism.py` | **TẠO** — 13 gate test (10 realism + 3 coherence), 30 seed |
| `src/gsm_sim/dashboard.py` | sửa — **fix visual: cột H3 3D đè lên tủ pin** |
| `.gitignore` | sửa — chặn `data/mock/**/*.csv` (279 MB suýt lọt vào git) |
| `tests/test_actors.py`, `tests/test_run_smoke.py` | sửa — bỏ hard-code 50/15/5, đọc config |
| `tests/test_mockgen.py` | sửa — duyệt bảng qua `entity_tables()` |
| `tests/test_m0_integrity.py` | sửa — nhận terminal state mới |

## 5. Kiểm chứng

- **Full suite: 391 passed, 5 skipped** (trước 378) — `uv run pytest -q`, 6ph49.
- Gate SIM-1: **30 seed**, 10/10 xanh (73s). Stochastic ⇒ ngưỡng median + biên per-seed
  rộng hơn (mỗi seed = MỘT NGÀY; ngày tốt/xấu là dao động thật, không phải lỗi).
- **KHÔNG vặn cầu**: `orders_per_day` giữ **1200** — có test riêng khoá lại
  (`test_demand_not_tuned_down`), vì served đẹp nhờ giảm cầu là số đẹp GIẢ.
- Coherence đo trên 3 ngày sinh thật (221 driver-day BIKE).

## 6. Bug thật phát hiện & sửa trong cycle này

**BUG-SIM1-01 — gate test làm OOM cả suite.** Bản đầu của `test_sim_realism.py` giữ **30
`RunResult` đầy đủ** trong fixture module-scope (events + orders + segments + gps ping).
Triệu chứng: `test_weekly_khoan.py::test_view_gross_matches_income_sum` đỏ với
`polars.exceptions.ComputeError: not enough memory` — **ở file khác**, chỉ khi chạy full suite.
- Phân loại: **BUG (của tôi)**, không phải lỗi data/parquet.
- Chứng minh root cause: file đó **xanh khi chạy riêng** ⇒ không phải lỗi nội dung parquet;
  thủ phạm là bộ nhớ do fixture của tôi giữ.
- Fix: `_digest()` rút gọn mỗi run thành aggregate nhỏ NGAY, world được GC. Full suite xanh lại.
- Bài học: đây đúng kiểu "external/infra failure" mà harness §4b cảnh báo — **không được
  sửa domain logic để che**. Ở đây nguồn thật là test mới, không phải parquet.

## 6b. Rà soát lại lần 2 (Cường yêu cầu) — 3 phát hiện MỚI

1. **`.gitignore` hở: 279 MB CSV suýt vào git.** `data/mock/realdata-v1/csv/` (13 file, bản CSV
   để review tay) KHÔNG bị chặn — policy cũ chỉ chặn `*.parquet`. Cùng dữ liệu, khác định dạng,
   tái gen được từ seed ⇒ đã thêm `data/mock/**/*.csv`. **Không commit bộ data này** (nó còn
   sinh TRƯỚC SIM-1 nên đã cũ — xem §10).
2. **Hidden fallback ở fix D.** `_emit_day` nhận `sim_stats=sim_stats.get((drv, d))`; tra HỤT sẽ
   **âm thầm** rơi về target profile — đúng loại harness §4b cấm. Đo thật: **222/222 driver-day
   BIKE tra được, 0 hụt**. Đã khoá bằng `test_no_silent_fallback_to_target_profile` (đỏ ngay nếu
   đổi định dạng ngày/driver_id) + 2 test coherence khác.
3. **FIX VISUAL — cột H3 3D đè lên tủ pin** (Cường chỉ ra). Root cause: `H3HexagonLayer`
   `extruded=True` cao `count × 8` mét, còn `ScatterplotLayer` trạm ở **z = 0**; deck.gl dùng
   **depth buffer** nên cột che trạm **bất kể thứ tự layer** — đổi thứ tự KHÔNG sửa được, đó là
   lý do bug tồn tại. Sửa thuần hình học (không phụ thuộc phiên bản deck.gl): checkbox
   **"Xem phẳng (2D)"** (tắt extrude + pitch 0) và khi ở 3D thì **nhấc trạm lên trên đỉnh cột
   cao nhất +40m**, `billboard=True`, viền trắng + `radius_min_pixels` để nổi trên nền cam.
   Tiện thể sửa tooltip hiện `{name}` rỗng trên hex.

**Đã rà và XÁC NHẬN ĐÚNG (không phải đoán):**
- Tắt cờ `cancel_after_accept_rate=0` → completion **0.9932**, 0 event huỷ ⇒ factor tắt được,
  quay về baseline.
- Mọi lần huỷ đều **tốn thời gian thật** (43 huỷ, 0.11–7.98 phút, tổng 108 phút) — không có
  huỷ "miễn phí" làm advisor học sai rằng huỷ không có giá.
- `orders_soc_skipped` (20) tách sạch khỏi `orders_cancelled` (43 = đúng số event huỷ).

## 7. Adversarial self-review / flaws found

Đã soi theo checklist harness §4b:

1. **Bảo toàn vòng đời đơn** ✅ có test: `matched == dropoff + cancel + censored` (30 seed).
   Terminal `CANCELLED_AFTER_ACCEPT` đã thêm vào tập bất biến (không bị ghi đè).
2. **Bảo toàn thời gian/pin khi huỷ** ✅ huỷ vẫn cộng `empty_min` + `consume_soc` theo đúng
   phần đường đã đi. Nếu huỷ mà "miễn phí" thì advisor sẽ học sai (huỷ không có giá).
3. **Không nhìn tương lai** ✅ quyết định huỷ rút TRƯỚC `timeout`, chỉ dùng `rng`, không dùng
   kết quả cuốc.
4. **Random stream** ✅ dùng `self.rng` (stream hành vi actor) — không chạm stream ngoại sinh
   (đơn/thời tiết) ⇒ **CRN cho SIM-4 vẫn còn nguyên**. ⚠️ Nhưng thêm một lần `rng.random()`
   mỗi lần match ⇒ **chuỗi số đổi so trước cycle**: kết quả seed-by-seed KHÔNG so sánh được
   với UPDATE cũ (determinism trong cùng phiên bản vẫn giữ — `test_determinism_same_seed` xanh).
5. **Double-count / clipping ẩn** ✅ `z` bị kẹp [−2,2] là **CHỦ Ý và có comment**, không phải
   clipping ẩn. `min(1.0, …)` từng che BUG-PI5b-01 — đã soi lại, không có ở đường mới.
6. **Config flag có thực dùng?** ✅ `cancel_after_accept_rate` đọc từ config; đặt 0 → về
   baseline completion ~99.6% (đường huỷ tắt hẳn). Có test chống hồi quy im lặng nếu ai tắt.
7. **Nghĩa counter** ✅ đã sửa `orders_cancelled` khỏi bị pha loãng bởi nhánh SOC.

**FLAW CÒN LẠI (ghi nhận, không che):**

- **F-SIM1-A (MEDIUM) — `trips/driver/day ≈ 12.3` thấp hơn research 18-22.** Nguyên nhân **CƠ
  CẤU, không phải bug**: cầu 1 quận = 1200 đơn/ngày ⇒ trần tuyệt đối 1200/74 ≈ 16 cuốc/tài xế
  kể cả phục vụ 100%. Thực tế tài xế chạy **liên quận**. `served` (realism hệ thống) và
  `trips/driver` (realism cá nhân) **không thể cùng đạt** với cầu 1 quận. Đã ưu tiên `served`
  vì đó là khuyết tật Cường chỉ ra. **Điều kiện mở lại:** khi enlarge zone (Cường đã DEFER).
- **F-SIM1-B (LOW) — P7 lệch base −4.3đ%** (lớn nhất trong 7 archetype, vẫn trong tolerance 5đ%).
  Giả thuyết chưa chứng minh: ca đêm gặp nhiều cuốc net thấp hơn ⇒ z âm. Chưa đo → **không
  kết luận**. Nếu tolerance bị siết xuống 3đ% thì phải điều tra trước.
- **F-SIM1-C (LOW) — 59/221 driver-day BIKE có acceptance = 1.00.** Không thoái hoá: đó là
  tài xế được chào RẤT ÍT đơn (mẫu nhỏ ⇒ 1.00 hợp lý thật). Test PI-2b chống thoái hoá vẫn xanh.
- **F-SIM1-D (LOW) — 11h-13h hết hạn 15-19% dù chỉ 1.1-1.2 đơn/tài xế.** Nghi do dồn cụm
  giờ ăn (`meal_hour` P4=11, P2=12, P3=13). Dưới ngưỡng gate 40% nên **không sửa trong cycle
  này**; ghi lại vì nếu sau này siết ngưỡng thì đây là chỗ vỡ đầu tiên.

## 8. Docs đã cập nhật kèm theo

- `specs/simulation/00-sim-overhaul-master.md` — bảng chẩn đoán §2 ghi kết quả SAU, SIM-1 → DONE.
- `tracking/TODO.md` — SIM-1 DONE, SIM-2 READY.
- `tracking/DIRECTIVES-2026-07-24.md` §8 — trạng thái Track A.
- `tracking/DEFERRED.md` — F-SIM1-A (điều kiện mở lại: enlarge zone).
- SCOPE/USER_STORIES: **không đổi** (không thêm/bớt tính năng).

## 9. Visual review

**Status: `REVIEWED` — Cường xem dashboard 2026-07-25, báo lỗi *cột H3 đè lên trạm sạc*;
đã fix (§6b.3) và yêu cầu commit.** Đây là *meaningful simulator update* (dynamics + default
parameters + metric mới) ⇒ theo harness §4b phải launch dashboard thật và chờ verdict
**trước commit**. Seed/scenario đề nghị xem: **seed 1000** (`configs/pilot_dongda.yaml`) —
kiểm tra bằng mắt: mật độ tài xế lúc 05-07h (trước đây trống trơn), đuôi đêm 21-23h, và
các cuốc bị huỷ giữa đường đi đón.

## 10. Follow-up

- **SIM-2** (`DriverJourney`) — sẵn sàng bắt đầu.
- F-SIM1-A → `DEFERRED` (mở lại khi enlarge zone).
- F-SIM1-B/D → soi lại ở SIM-5 khi có bộ metric đầy đủ theo giờ.
- Chưa kiểm chứng: chưa chạy lại **4 vòng verify** của bộ mock 90 ngày với counter mới
  (bộ data trong `data/mock/realdata-v1/` sinh TRƯỚC cycle này) ⇒ cần regenerate ở SIM-5.
