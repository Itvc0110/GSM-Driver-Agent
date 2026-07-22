# Research — Biến môi trường & luật kết hợp multiplier (đợt 6)

Ngày: 2026-07-21 · Nguồn: research đợt 6 · Phục vụ: `specs/environment-variables.md`, sửa `math-audit.md` A + `mock-order-distribution.md` §5
Nhãn: **[NGUỒN]** URL kiểm chứng · **[PROXY]** số quốc tế cho hình dạng/hệ số · **[ƯỚC LƯỢNG]** suy luận.

## 0. TL;DR — luật kết hợp tổng (quan trọng nhất)

Ba "không gian" khác nhau, ba cách kết hợp khác nhau — **KHÔNG dùng chung một phép nhân cho tất cả**:

| Đại lượng | Không gian | Công thức | Lý do |
| --- | --- | --- | --- |
| **Demand (Poisson λ)** | log-space (nhân) | `λ = BASE · Π fᵢ` cho hiệu ứng tỷ lệ; **sự kiện cộng riêng**: `λ_total = BASE·Πfᵢ + λ_event` | Hiệu ứng tỷ lệ độc lập ⇒ nhân (= Poisson GLM log-link). Sự kiện là cuốc *tăng thêm* → cộng |
| **Tốc độ / slowdown** | survival | `v = v_base · Π(1−rᵢ)` ⟺ `r_total = 1 − Π(1−rᵢ)` | Nhiều nguyên nhân chậm độc lập ⇒ ghép xác suất sống sót, **không bao giờ >1 hay <0**; cộng thẳng rᵢ thì tràn |
| **Supply (P offline)** | xác suất | `p = 1 − (1−p_base)·Π(1−pᵢ)` | Cùng lý do — tự chặn [0,1] |

3 nguyên tắc chống lỗi: **(1) factor trực giao** (mỗi factor một chiều); **(2) tương tác → term riêng có tên** (đừng thổi phồng main effect); **(3) chặn mềm ở TỔNG, không chỉ từng cái + log cả thô lẫn đã chặn**.

## 1. Mưa → tốc độ

Định lượng: FHWA arterial mặt ướt **−10…−25%** (gần bike đô thị nhất); freeway mưa to −3…−17%; xe máy giảm nhiều hơn cả mức lý học (~−10…−15 km/h) [NGUỒN FHWA, MDPI su14094985].

```text
speed_rain_factor(R) = 1 − r_rain(R);   r_rain(R) = r_max·(1 − exp(−R/R0))   # bão hòa, ∈[0,r_max]
```
Bike default: `r_max=0.28` (0.20–0.35), `R0=9 mm/h` (8–12). Kiểm: r(2.5)=7%, r(5)=12%, r(10)=19%, r(25)=26%, r(50)=28% — khớp bảng.
Ghép với tốc-theo-giờ + sàn: `v = max(v_floor, v_base(h)·(1−r_rain)·(1−r_congestion))`, `v_floor≈6–8 km/h`.

## 2. Mưa → demand (SỬA: đơn điệu tăng → chữ U ngược)

Định lượng: Chicago Uber **+22%**/Lyft +19%/taxi +5% [PROXY]; NYC +20–25%; Haikou **+0.59%/mm·h** [PROXY]. **Phi tuyến (model hiện tại THIẾU)**: demand tăng rồi GIẢM khi mưa nặng (chữ U ngược — mưa to quá người ở nhà); rõ nhất cuối tuần [NGUỒN WCAS-D-23-0142]. Model `clamp(1+0.006R,…,1.5)` đơn điệu → thổi phồng mưa cực to.

```text
demand_rain_factor(R) = 1 + Δ_peak·(R/R_peak)·exp(1 − R/R_peak)   # unimodal, đỉnh 1+Δ_peak tại R=R_peak
```
Default: `Δ_peak=0.22` (Chicago), `R_peak=8 mm/h`. Kiểm: f(2)=1.12, f(8)=1.22, f(20)=1.12, f(40)=1.02 — lên rồi xuống. Dải: Δ 0.15–0.30, R_peak 5–30.

## 3. Mưa → supply (tài xế nghỉ)

Văn liệu đồng thuận tài xế tắt app khi mưa nhưng **không nguồn nào cho % cụ thể** (gap cả ngành). VN [NGUỒN Thanh Niên 26/7/2025]: hai chiều (nghỉ vì rủi ro / cần tiền nên ở lại), net giảm cung. → **% offline là [ƯỚC LƯỢNG]**: cung giảm −15…−25% lúc mưa to, phân hóa archetype.

```text
p_offline_rain(R, arch) = clamp(p_base[arch] + α[arch]·(1−exp(−R/R_s)), 0, p_cap[arch])
```
`R_s=10`; α: P1 0.45, P4 0.15, P2 0.20, P3 0.10, P5 0.30; p_cap 0.2–0.6. = action `weather_response` đã có trong twin-world §2.3.

**Net effect mưa = 3 kênh cùng lúc**: demand ×1.15–1.22 + supply ×0.75–0.85 + speed ×~0.8 → ETA/unserved tăng vọt. Không surge → hệ dồn về chờ/hủy → **dư địa advisor**.

## 4. Ngày trong tuần (tránh double-count với hour_shape)

Cuối tuần +~20%/ngày; T6 cao nhất về tối; T7 tài xế kiếm nhiều nhất [PROXY]. Repo có dow 0.90–1.10 hợp lý.

**Tách vai chống double-count**: `dow` chỉ chỉnh MỨC ngày (`dow_level`); `hour_shape` là HÌNH DẠNG chuẩn hóa Σ=1 theo `dow_type ∈ {weekday, friday, weekend}`. Tương tác dow×hour xử lý bằng **bảng hour_shape riêng theo dow_type**, không phải 2 multiplier nhân nhau.

## 5. Sự kiện (concert/lễ) — CỘNG không nhân

Văn liệu coi sự kiện là **residual cộng thêm cục bộ** trên nền mùa vụ [NGUỒN arXiv 1711.10090 STAR, ST-MGCN]; đặc trưng inbound ramp trước + egress spike sau (spike ra sắc hơn).

```text
λ_event(cell,t) = N_event · g_space(cell) · g_time(t)
g_space = Gauss theo grid-distance H3 tới venue, σ_s≈1–3 cell, Σ=1
g_time  = ramp_in(t; [t0−120', t0−15']) + β_out·egress(t; [t_end, t_end+60'])   β_out≈1.5–2.5
N_event = attendance · capture_rate     capture_rate ≈ 5–15% [ƯỚC LƯỢNG]
λ_total(cell,t) = [BASE·zone·hour·dow·rain] + λ_event    # CỘNG ngoài phép nhân
```
Nhân sẽ khuếch đại sự kiện phi lý (đỉnh chồng đỉnh).

## 6. Nhiệt độ (ưu tiên thấp — chủ yếu pin)

Demand: bằng chứng yếu (T>25°C → congestion −6% cuối tuần) → **mặc định tắt (factor=1.0)**. Pin: range đỉnh ~21.5°C, giữ ≥100% trong 10–31°C [NGUỒN Geotab]; xe máy điện không AC nên nóng chỉ **−5% quanh 38–40°C** [ƯỚC LƯỢNG].

```text
range_factor(T) = clamp(1 − β_hot·relu(T − T_opt_hi), 0.85, 1.0)   # T_opt_hi=30, β_hot=0.005/°C
```
Nhân vào tầm xe → SoC chạm ngưỡng đổi pin sớm hơn ngày nắng.

## 7. Biến khác

- **Surge**: xác nhận BỎ QUA hợp lý, nhưng phải mô hình hệ quả (cung không co giãn → không tự cân bằng khi mưa/sự kiện — đã ghi realism-benchmarks NYE natural experiment).
- Tắc đường theo cell: đã trong speed model + `r_congestion` cục bộ quanh venue.
- Hủy/no-show: giữ decline 2–5%, no-show gộp vào patience 2 tầng đã có.
- Cạnh tranh hãng: ngoài scope (Xanh SM cấm multi-app). Gió/bão/nồm: gộp vào "mưa to".

## 8. Chi tiết luật kết hợp (đối chiếu math-audit §C)

- **Nhân đúng cho demand** vì `log λ = log BASE + Σ log fᵢ` (Poisson GLM log-link, mỗi fᵢ là incidence-rate-ratio) [NGUỒN StatsDirect, Roback ch.4]. Repo đang làm đúng — giữ.
- **Lỗi double-count**: mỗi factor một chiều; khai báo `mode: shape|level` trong config (shape Σ=1 phân phối lại, level đổi tổng).
- **Lỗi bỏ tương tác**: thêm term có tên `f_{rain×peak}` khi cần (mặc định=1, tắt được), không thổi phồng main effect.
- **Lỗi tràn biên**: clamp từng factor + **clamp TỔNG** `M∈[0.3,3.0]` trong log-space + log cả M thô lẫn M capped.
- **KHÔNG phải cái gì cũng nhân**: tốc độ/xác suất → survival product; đại lượng vật lý có trần (pin) → tuyến tính có sàn.

## 9. Config schema đề xuất (mọi tham số ra ngoài, tắt được về 1)

Xem `specs/environment-variables.md` §config (khối `weather/dow/event/combine`).

## Nguồn chính
FHWA rain/flooding · MDPI su14094985 · Chicago ScienceDirect S2590198225004919 · Haikou S2214367X21000302 · WCAS-D-23-0142 (chữ U ngược + temp) · Geotab EV range · Findings day-of-week · arXiv 1711.10090 STAR · StatsDirect/Roback Poisson · Thanh Niên 26/7/2025 tài xế mưa. (URL đầy đủ trong transcript research.)

## Độ tin thấp (đánh dấu mock rõ khi dùng)
% tài xế offline khi mưa (không nguồn ngành); temp→demand; capture_rate sự kiện.
