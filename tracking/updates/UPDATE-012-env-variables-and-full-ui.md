# UPDATE-012 — Biến môi trường (mưa/nhiệt/ngày/sự kiện) + math-audit fixes + UI hoàn chỉnh

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent (theo yêu cầu **Cường**, dưới claim T-018)
- **Loại:** feature / fix / research / ui
- **TODO / User story liên quan:** T-018 (sim core), chuẩn bị T-019 (advisor harness) & T-021 (calibration)

## Tóm tắt

Cường yêu cầu pause update để **audit lại sim đã đủ biến chưa** (mưa→tốc độ, v.v.), công thức toán rõ ràng, **chỉnh được tỷ lệ trong config**, biến tác động lẫn nhau phải có luật kết hợp. Kết quả: (1) audit toán học 8 vấn đề; (2) thêm lớp `EnvironmentContext` với 3 không gian kết hợp đúng luật (demand nhân + event cộng; tốc độ/offline survival; pin tuyến tính có sàn); (3) sửa magic numbers ra config (A3/A4/A5/A6); (4) research đầy đủ biến pricing/API ngoài/taxonomy sự kiện; (5) **UI hoàn chỉnh chỉnh tham số trực tiếp + visualize môi trường**. Mọi factor tắt được về 1 → `dry_weekday` **byte-identical** với baseline (env=None).

## Chi tiết cập nhật

### 1. Audit toán học (`research/simulation/math-audit.md`)
8 vấn đề: A1 quy ước window; A2 demand giật cục biên giờ; A3 magic 0.35/0.5 trong `_sample_drop`; **A4 thiếu detour_factor → ETA ngắn ~30% (ưu tiên cao)**; A5 magic 3000/6000/8000 accept; A6 nhiễu hint clamp→0 (đổi lognormal); A7 tốc độ cố định giữa cuốc; A8 stranded≈0 artifact.

### 2. Luật kết hợp biến (cốt lõi — chống nhân sai)
- **Demand** = tích các factor LEVEL (dow × rain_unimodal × temp), **clamp [0.3, 3.0]** + đếm `clamp_hits`; **sự kiện CỘNG riêng** (`λ_event`), KHÔNG nhân (tránh peak-on-peak).
- **Mưa = 3 kênh tách biệt**: demand ↑ (unimodal chữ U ngược `1+Δ·(R/Rp)·e^{1−R/Rp}`, đỉnh tại Rp), tốc độ ↓ (survival `1−r_rain`, bão hòa ≤ r_max), cung ↓ (offline prob theo archetype, ≤ p_cap — **MOCK, độ tin thấp, chờ hỏi tài xế**).
- **Tốc độ/offline** = survival product `1−Π(1−rᵢ)` (mưa × tắc), luôn ∈ (0,1], có sàn `v_floor`.
- **Nhiệt độ → tầm pin** tuyến tính có sàn (>30°C tăng tiêu hao/km).
- **Sự kiện** = Gauss không gian (H3 distance-decay) × time-profile bất đối xứng (ingress ramp trước, egress spike sắc sau).

### 3. Sửa magic numbers ra config
detour_factor 1.3 (A4), drop_km_per_cell/softness (A3), 3 tham số accept logit (A5), hour_interp (A2), nhiễu hint lognormal (A6). `speed`/`pct_per_km` giờ đi qua helper `_eff_speed`/`_travel_min`/`_pct_per_km` trong world (áp env + detour đồng nhất).

### 4. Research đầy đủ (yêu cầu #4 của Cường)
`research/market/dispatch-signals-and-external-apis.md`: (a) biến state hệ điều phối thực (Uber/Grab/DiDi) — **Xanh SM KHÔNG surge cấp tiến** (giá linh hoạt -8k/+22k, Bike ổn định) → cung không co giãn giá = dư địa advisor; (b) API ngoài free/no-key: **Open-Meteo + TomTom(key free) + Nager.Date + scrape Ticketbox**; (c) **taxonomy sự kiện labeled** (concert/sports/festival_tet/expo/political/accident/weather/exam/countdown) + schema `route_effect` (survival, không double-count với demand).

### 5. UI hoàn chỉnh (yêu cầu "thay tham số thẳng trên UI")
`dashboard.py` viết lại: chỉnh trực tiếp demand/actors/dispatcher/behavior + **kịch bản môi trường** (6 preset + "Tùy chỉnh" với slider mưa/nhiệt/ngày/sự kiện); tab **🌦️ Môi trường** visualize mưa mm/h + demand/speed/range factor + p(offline) theo archetype theo giờ; **so sánh baseline khô** (delta metrics); cảnh báo `clamp_hits`. Sửa bug cũ tham chiếu `order_expire_s` (không còn trong config).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/simulation/math-audit.md` | tạo | 8 vấn đề toán học |
| `research/simulation/environment-variables.md` | tạo | luật kết hợp + nguồn |
| `research/market/dispatch-signals-and-external-apis.md` | tạo | nhóm state/API/event |
| `specs/environment-variables.md` | tạo | spec thiết kế EnvironmentContext + 7 test biên + 6 scenario |
| `src/gsm_sim/environment.py` | tạo | `EnvironmentContext` + `EventSpec` |
| `src/gsm_sim/demand.py` | sửa | `env=` param; event addend; drop config; re-index order_id |
| `src/gsm_sim/behavior.py` | sửa | accept logit params ra config (A5) |
| `src/gsm_sim/dispatcher.py` | sửa | `eff_speed`/`detour` → ETA (A4) |
| `src/gsm_sim/world.py` | sửa | `environment=`; helper `_eff_speed`/`_travel_min`/`_pct_per_km`; hint lognormal (A6) |
| `src/gsm_sim/runner.py` | sửa | `build_environment` + wire vào generate_orders/World; `RunResult.env` |
| `configs/pilot_dongda.yaml` | sửa | block `environment`, `behavior`, detour/drop/hour_interp |
| `src/gsm_sim/dashboard.py` | sửa | UI đầy đủ + tab môi trường + so sánh baseline |
| `tests/test_environment.py` | tạo | 9 test (7 biên + baseline-equiv + env-tác-động) |

## Docs đã cập nhật kèm theo

TODO (T-018 tiến độ + follow-up mới). SCOPE/DEFERRED/USER_STORIES: không đổi (vẫn trong scope sim T-018). RESEARCH: thêm 3 file kết quả.

## Kiểm chứng

- `uv run --extra dev pytest -q` → **38 passed** (29 cũ + 9 env).
- `test_dry_weekday_equals_no_env`: metrics dry_weekday **identical** env=None (env là no-op khi khô, CRN giữ nguyên).
- `test_rain_scenario_changes_metrics`: rain_peak **khác** dry → env thật sự nối vào sim.
- Determinism: cùng seed+scenario → metrics khớp (khô lẫn mưa auto).
- UI: Streamlit AppTest headless 4 kịch bản (dry/rain_peak/event_day/prolonged_rain) + "Tùy chỉnh" bật mưa → **0 exception**, 4 tab + 5 metric render.
- **CHƯA kiểm chứng:** offline-prob do mưa (MOCK, chờ hỏi tài xế — Q3); capture_rate 5–15% & Tết citywide ~0.4 (ước lượng); API ngoài (Open-Meteo/TomTom) chưa gọi thật; route_effect trong schema chưa nối vào speed model (mới ở event demand).

## Follow-up / defer phát sinh

- **T-mới:** nối `route_effect` sự kiện vào speed model (survival cục bộ quanh venue) — hiện chỉ có demand addend.
- **T-mới:** tool layer gọi API ngoài thật (Open-Meteo/TomTom/Nager) cho harness advisor T-019, mỗi tool có nhãn nguồn + confidence + fallback tắt về template.
- **Hỏi tài xế:** hệ số offline do mưa theo archetype (α), capture_rate sự kiện — cập nhật khi có dữ liệu thực.
- **Defer (đã ghi spec §7):** term tương tác rain×peak riêng; nhiễu tiêu pin per-km (A8) để stranded có nghĩa; r_congestion theo cell động.
- A1/A7 (window quy ước, tốc độ cố định giữa cuốc): A1 chỉ cần comment (đã làm); A7 chấp nhận trong slice (tốc độ theo giờ tại thời điểm bắt đầu chặng).
