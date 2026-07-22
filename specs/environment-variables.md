# SPEC — Biến môi trường & luật kết hợp (v1)

Cập nhật: 2026-07-22 · Trạng thái: **IMPLEMENTED CORE / PARTIAL — M2 HARDENING PENDING**.
Nguồn: `research/simulation/environment-variables.md` + `research/simulation/math-audit.md`; implementation core ghi tại UPDATE-012; phasing/gates mới tại `simulation-reliability-upgrade.md` M2.

**Đã có (UPDATE-012):** EnvironmentContext, rain/temp/dow/event demand channels, demand/speed/range factors, config levers, dry no-op tests và scenario UI. **Chưa qua M2 gate:** route-effect/congestion attribution hoàn chỉnh, minute-level smoothed trace, external snapshot adapters/provenance, no-future-leak audit và multi-seed distribution validation. Working diff congestion ngày 2026-07-22 là M0 audit input, chưa phải phần implemented đã chấp nhận.

## 0. Nguyên tắc thiết kế (không thương lượng)

1. **Mọi biến môi trường có thể tắt về "không tác động"** (factor=1, không mưa, không sự kiện) → sim quay về baseline hiện tại.
2. **Tham số ở config, không hard-code** — kể cả các magic number đang có trong code (math-audit A3/A4/A5).
3. **Ba không gian, ba cách kết hợp** (không dùng chung 1 phép nhân): demand=nhân+event-cộng, tốc độ/xác suất=survival-product, vật lý có trần=tuyến tính-có-sàn.
4. **Log giá trị thô + đã chặn** khi có clamp → phát hiện khi nào factor bị bó.
5. **CRN-safe**: biến môi trường của một scenario được **sinh trước thành trace** (weather series, event list) dùng chung mọi arm — không random trong sim loop.

## 1. Kiến trúc: `EnvironmentContext`

Một object bất biến, sinh từ config + seed TRƯỚC khi chạy, cung cấp cho demand generator + world:

```
EnvironmentContext:
  rain_mm_per_hour(t_min) -> float      # chuỗi mưa theo thời gian (scenario)
  temp_c(t_min) -> float                # nhiệt độ theo giờ
  dow_type -> {weekday, friday, weekend}
  events: list[Event(venue_cell, t_start, t_end, attendance)]
  # dẫn xuất (đọc từ config):
  demand_factor(cell, t_min) -> float   # tích các factor level, đã clamp tổng
  event_addend(cell, t_min) -> float    # λ_event cộng thêm
  speed_factor(cell, t_min) -> float    # survival product (rain × congestion)
  offline_prob(actor_arch, t_min) -> float
  range_factor(t_min) -> float          # nhiệt độ → tầm pin
```

Scenario "ngày thường khô" = rain≡0, temp const, dow=weekday, events=[] → mọi factor=1 → baseline. Không phá test hiện có.

## 2. Công thức (chi tiết đầy đủ trong research/environment-variables.md — đây là bản chốt để code)

### 2.1 Demand (nhân + event cộng)
```
M_level(cell,t) = clamp( dow_level(dow) · rain_demand(R(t)) · temp_demand(T(t)), M_min, M_max )
rain_demand(R)  = 1 + Δ_peak·(R/R_peak)·exp(1 − R/R_peak)         # unimodal (SỬA clamp đơn điệu cũ)
λ(cell,t)       = BASE · zone(cell) · hour_dist[dow_type](t) · M_level(cell,t)
λ_total(cell,t) = λ(cell,t) + event_addend(cell,t)
```
- `hour_dist[dow_type]` chuẩn hóa Σ=1 (shape); `dow_level`/`rain_demand`/`temp_demand` là level. Khai báo `mode` mỗi factor trong config.
- clamp tổng `M∈[M_min,M_max]=[0.3,3.0]`; log cả M thô lẫn capped.

### 2.2 Tốc độ (survival product + sàn)
```
speed_factor(cell,t) = (1 − r_rain(R(t))) · (1 − r_congestion(cell,t))
r_rain(R)            = r_max·(1 − exp(−R/R0))
v(cell,t)            = max(v_floor, v_base(hour) · speed_factor(cell,t))
```
Áp vào MỌI di chuyển: pickup, trip, relocate, deadhead, đi trạm. **Kèm sửa math-audit A4**: `v_base` đã gồm `detour_factor` (khoảng cách thực = chim-bay × detour ~1.3).

### 2.3 Supply (survival product xác suất offline)
```
p_offline(arch,t) = 1 − (1 − p_base[arch]) · (1 − p_rain(R(t),arch))
p_rain(R,arch)    = clamp(α[arch]·(1−exp(−R/R_s)), 0, p_cap[arch])
```
Actor mỗi decision-point: nếu online và roll < p_offline → tạm offline (action weather_response). Deterministic theo RNG stream actor.

### 2.4 Nhiệt độ → pin (tuyến tính có sàn)
```
range_factor(T) = clamp(1 − β_hot·relu(T − T_opt_hi), floor, 1.0)
soc tiêu hao thực = pct_per_km / range_factor(T)   # range giảm → tiêu hao/km tăng
```

### 2.5 Sự kiện (cộng, cục bộ)
```
event_addend(cell,t) = Σ_events N·capture · gauss_space(grid_dist(cell,venue), σ) · time_profile(t)
time_profile         = ramp_in[t0−120',t0−15'] + β_out·egress[t_end,t_end+60']
```

## 3. Config schema (thêm vào pilot_dongda.yaml)

```yaml
environment:
  scenario: dry_weekday          # dry_weekday | rain_peak | weekend | event_day | ...
  rain:
    series: []                   # [] = không mưa; hoặc [[t_min, mm/h], ...] nội suy
    demand: {delta_peak: 0.22, r_peak_mmph: 8.0}
    speed:  {r_max: 0.28, r0_mmph: 9.0, v_floor_kmh: 7.0}
    supply: {r_s_mmph: 10.0, alpha: {P1: 0.45, P2: 0.20, P3: 0.10, P4: 0.15, P5: 0.30}, p_cap: 0.5}
  temp:
    series: []                   # [] = const 28C
    demand_factor: 1.0           # off (độ tin thấp)
    range: {t_opt_hi_c: 30.0, beta_hot_per_c: 0.005, floor: 0.85}
  dow:
    type: weekday                # weekday | friday | weekend
    level: {weekday: 1.0, friday: 1.10, weekend: 1.05}
  events: []                     # [{venue_cell, t_start, t_end, attendance, capture_rate}]
  combine:
    demand_total_clamp: [0.3, 3.0]
    log_raw_and_capped: true

# sửa magic numbers (math-audit):
demand:
  detour_factor: 1.3             # A4 — khoảng cách thực / chim bay
  drop_km_per_cell: 0.35         # A3 (nên tính từ h3 edge length)
  drop_softness_km: 0.5          # A3
behavior:
  accept_cost_per_pickup_km_vnd: 3000   # A5
  accept_logit_center_vnd: 6000         # A5
  accept_logit_scale_vnd: 8000          # A5
```

## 4. Sửa kèm từ math-audit (ưu tiên trong lượt implement)

| Issue | Sửa |
| --- | --- |
| A4 detour | `detour_factor` × mọi khoảng cách di chuyển (ưu tiên cao — ETA đang ngắn ~30%) |
| A3 magic | `drop_km_per_cell`, `drop_softness_km` ra config; tính km/cell từ h3 edge |
| A5 magic | 3 tham số accept ra config |
| A2 demand giật giờ | nội suy tuyến tính hour_dist giữa mốc giờ (giảm răng cưa biên giờ) |
| A6 nhiễu hint | đổi `1+N(0,σ)` clamp → `exp(N(0,σ))` lognormal (luôn dương) |
| A1 window | ghi rõ comment "orders_per_day = kỳ vọng trong window" |

## 5. Kịch bản dùng biến (khớp twin-world §9 + robustness T-027)

| Scenario | rain | dow | events | temp |
| --- | --- | --- | --- | --- |
| dry_weekday | [] | weekday | [] | 28 |
| rain_peak | series đỉnh 15mm/h lúc 17-19h | weekday | [] | 26 |
| weekend | [] | weekend | [] | 30 |
| event_day | [] | friday | 1 concert 19-22h | 30 |
| heat | [] | weekday | [] | 40 |
| prolonged_rain | series 8mm/h cả ngày | weekday | [] | 25 |

→ đúng ma trận domain randomization cho robustness (nghiên cứu llm-advisor: same-map + DR đủ).

## 6. Test biên (viết cùng code)

1. Mọi factor=1 (dry_weekday) → metrics khớp baseline hiện tại trong dung sai.
2. rain_demand(0)=1.0; đạt đỉnh đúng R_peak; giảm khi R lớn (kiểm unimodal).
3. speed_factor ∈ (0,1]; v ≥ v_floor luôn.
4. p_offline ∈ [0,1]; tăng theo R; ≤ p_cap.
5. M_level ∈ [M_min, M_max]; log ghi cả thô lẫn capped.
6. event_addend: Σ theo không gian bảo toàn N·capture; =0 ngoài cửa sổ thời gian.
7. Determinism: cùng seed+scenario → weather/event trace identical.

## 7. Chưa qua gate / defer

**M2 — T-034 (đã mở backlog):**

- congestion H3 được spatial smoothing + time interpolation;
- tách attribution base traffic / demand-correlated `[PROXY]` / rain / event route effect;
- `known_at/effective_at`, no-future-leak và no-op equivalence;
- external inputs snapshot/version/provenance trước run, không gọi live trong sim loop;
- multi-seed distribution/sensitivity validation.

**Vẫn defer:**

- tương tác `f_{rain×peak}` riêng — chỉ thêm khi có bằng chứng;
- nhiễu tiêu pin per-km (math-audit A8);
- edge-level traffic — sau road graph/route contract gate.
