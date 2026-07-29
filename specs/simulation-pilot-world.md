# SPEC — Pilot World: Đống Đa, 50 actors, 3-arm twin-world (v1)

Cập nhật: 2026-07-22 · Trạng thái: IMPLEMENTED PILOT / COMPATIBILITY PROFILE (05:00–24:00); nâng cấp bị gate bởi `simulation-reliability-upgrade.md` M0–M4.
Nguồn: `research/simulation/pilot-world-dongda.md` + `timestep-design.md` + `action-space.md` + `world-parameters.md` + `evaluation-methodology.md` + `tooling.md`. Spec nền: `simulation-twin-world.md` (kiến trúc 3 arm — không đổi), `advice-timing-state-memory.md` (trigger/memory), `mock-order-distribution.md` (hour-shape).

> **Override 2026-07-22:** các số 50 actors/1.200 orders và run 05:00–24:00 dưới đây mô tả pilot lịch sử. M1 target là `[00:00,24:00)` với `actors.n` = daily actor pool; phasing/gates theo `simulation-reliability-upgrade.md`. Không dùng target service của A-arm làm correctness gate cho B-arm.
Data: `research/simulation/data/` — batt_dd.json (11 tủ pin thật), poi_dd.json, dd_geom.json (polygon 5 phường proxy), battery_nodes.json (144 tủ toàn HN cho bản mở rộng).

## 1. Thế giới pilot

| Thành phần | Giá trị chốt | Nguồn |
| --- | --- | --- |
| Khu vực | **Quận Đống Đa cũ** (proxy 5 phường mới: Đống Đa, Kim Liên, Ô Chợ Dừa, Văn Miếu–QTG, Láng), ~9,95 km² | pilot-world-dongda §1 |
| Lưới | **H3 res 9**: 85 cells lõi (116 kể cả biên) — lưới vận hành; **res 8** (12 cells) cho heatmap/báo cáo qua `cell_to_parent` | §2 |
| Actors | **N = 50**, sample từ 5 archetype (P1 20% · P2 30% · P3 10% · P4 25% · P5 15% — mix config được) với jitter giờ/target/cell nhà/SOC | twin-world §5 |
| Đơn/ngày | `orders_per_day = 1.200` (dải 900–1.800) `[MOCK]`; 15–20% unserved là service objective/scenario target cho A-arm, **không phải integrity target của B-arm** | pilot-world-dongda §3 + reliability-upgrade M0 |
| Demand không gian | `w_cell = a·pop_density + b·Σ(POI_loại×hệ_số)` chuẩn hóa; POI thật (26 BV, 13 ĐH, 3 TTTM, 10 chợ) + office-weight mock dọc trục Láng Hạ/NCT/Thái Hà/Hoàng Cầu | §4 |
| Demand thời gian | hour-shape từ `mock-order-distribution.md` (2 đỉnh 7–9h, 17–19h ~2×TB; weather factor `clamp(1+0.006·mm/h, 1, 1.5)`) chiếu xuống cell | spec mock |
| Trạm pin | **11 tủ thật** (tọa độ OSM), 6 khe (5 pin + 1 trống), đổi 90s (uniform 60–120s), sạc lại trong tủ 1,5–2h/viên → throughput ~2,5–3 pin/giờ/tủ; cụm Đông dày/Tây thưa | world-parameters §1 |
| Xe | Đội **đổi pin** (Evo swap): ~55–70 km/pack, tiêu hao 1,4–1,8%/km/pack, ngưỡng đi đổi SoC 15–25%; biến thể đội sạc cắm (charge_at_home 3–4h) cho một phần archetype P3/P5 | world-parameters §2 |
| Tốc độ | cao điểm 17 · thường 25 · đêm 30 km/h; di chuyển = `grid_distance × tốc_độ(giờ)` | world-parameters §2 |
| Dispatcher | Batched: gom đơn trong tick, candidates = `grid_disk(pickup, k=2)` res 9 (nới k=3 nếu rỗng — chú ý res 9 nên k=2 ≈ 700m, cân nhắc k=4–6 tương đương bán kính cũ ở res 8; calibrate khi build), Hungarian (`scipy.linear_sum_assignment`), ETA_max 8ph, expire 60–90s | world-parameters §3 + hiệu chỉnh res 9 |

> **⚠ Đính chính 2026-07-29 — số cấu hình đã calibrate lại so với bảng gốc trên:**
> - **N actors: 50 → 90** (`configs/pilot_dongda.yaml actors.n`). Với `orders_per_day = 1.200`
>   không đổi ⇒ đơn/actor giảm từ 24,0 xuống **13,3** — chờ THỰC THI **Q-05 bước ②** (khôi phục
>   tỷ lệ đơn/actor — Cường đã chốt thứ tự ①→④, xem `tracking/PENDING-REVIEW.md` dòng Q-05).
> - **Dispatcher**: `candidate_ring_k = 4` (không phải k=2), `candidate_ring_k_max = 6` (đã HOÀN TÁC
>   từ 12 — xem `tracking/TODO.md` T-045a c0/Q-07), `matching: batch` (Hungarian, không còn greedy
>   mặc định) — khớp mô tả "Hungarian" ở trên nhưng k thật khác.
> - **ETA_max**: 8 phút → **11 phút** (`eta_max_min`, hiệu chỉnh theo hệ số đường OSRM thật).
> - **Patience khách**: không còn "expire 60–90s" — mô hình 2 tầng: chờ match ~ lognormal
>   (`patience_median_min = 5.0`, `patience_sigma = 0.5`, cap `patience_max_min = 10.0`); tầng 2 huỷ
>   nếu pickup ETA > `eta_max_min`.

## 2. Kiến trúc thời gian (chốt theo `timestep-design.md`)

| Tầng | Cơ chế | Giá trị |
| --- | --- | --- |
| T0 trip/swap lifecycle | pure DES (SimPy), pin lazily tại biên event | giây |
| T1 dispatch tick | tick thật duy nhất | **5s** (sensitivity 2s/15s) |
| T2 demand/metrics bucket | flush counters | **15 phút**/hex (system metrics 5ph được) |
| T3 advisor anchor | hybrid anchor + event-trigger | **30 phút** + trigger (sau swap, idle>10ph, đầu/cuối ca) — khớp `advice-timing-state-memory.md` |
| T4 viz | log event + nội suy khi render, KHÔNG frame trong sim | frame 1s sim-time |

**Determinism/CRN (bắt buộc, 3 arm):** priority tường minh cùng-timestamp `trip/swap done < đơn nổ < dispatch tick < metrics flush` (đơn nổ đúng biên tick → VÀO batch); sort mọi iteration theo (actor_id, order_id); RNG per `(entity, purpose)` bằng `SeedSequence.spawn()`; **pre-generate exogenous trace** (timestamp/cell đón-trả/base duration/traffic hệ số) dùng chung 3 arm. Test: 2 lần chạy cùng seed → log identical; diff trace giữa arm → identical.

## 3. Ba arm (đã approve)

- **A** — advisor thông minh (trigger hybrid + optimization lớp A + capacity ledger anti-herding).
- **B** — không advice (behavior model bản năng thuần).
- **C** — placebo: cùng tần suất/loại advice như A nhưng nội dung naive (mốc giờ cố định, không dùng demand/policy intelligence).
- Báo cáo: Δ(A−B), Δ(C−B), **Δ(A−C) = giá trị thật của intelligence**; paired theo seed (20–30 seeds, sequential ≤100).

## 4. Actor model (chốt theo `action-space.md`)

- App events: `go_online/go_offline/set_offline_after_trip/accept_order/decline_order/cancel_trip/complete_trip`; cờ `forced_auto_accept` khi acceptance ngày <50% (reset 23h59).
- Vật lý: `wait_at_cell / relocate_to_cell (actor tự quyết) / go_to_swap_station→queue→swap_battery / charge_at_home / rest / start_shift / end_shift / weather_response`.
- Không mô hình hóa: multi-app (bị cấm với xe Xanh SM), hành vi vi phạm (trừ scenario noise có nhãn).
- Advisor product-scope: chỉ timing (online/offline/kết ca qua `set_offline_after_trip`, nghỉ/sạc/đổi pin lệch đỉnh), tiến độ mốc thưởng versioned, cảnh báo ngưỡng hồ sơ, thời tiết. KHÔNG: đơn cụ thể, reposition. Trong sim, advisor-sim thêm capacity ledger (fleet-awareness cho nghiên cứu — SCOPE §5b).

## 5. Kịch bản pilot (rút gọn từ twin-world §9)

1. Ngày thường khô (baseline).
2. Mưa giờ tan tầm (weather_response + demand tăng).
3. CN sáng vắng.
4. **Stress herding trạm pin**: 11 tủ × 6 khe cho 50 actor swap-fleet; advisor bật/tắt capacity ledger — chứng minh chống tắc.
5. Adoption 30%/100% arm A.

## 6. Output & viz

- Event log parquet (schema: ts, arm, seed, actor, event_type, cell, order_id, payload) + manifest (config, seed, git hash, spec_version, nhãn mock).
- Metrics: 3 tầng theo twin-world §3 tổng hợp T2 bucket; adherence report theo taxonomy 5 nhãn.
- Replay kepler.gl (basemap CARTO/OSM — không cần token; `MAPBOX_TOKEN` optional): layer H3 demand + trip paths + điểm trạm với queue size theo thời gian; so A/B/C bằng filter arm.
- Dashboard Streamlit: Δ metric + CI theo seed, boxplot theo archetype, queue trạm, funnel adherence.

## 7. Definition of Done (TÁCH 2 TẦNG — theo red-team audit F9; chi tiết harmonize tại `advisor-optimization-layer-a.md` §4)

**DoD-core (T-018 — world/dispatcher/actors/twin-runner):**
1. 2 lần chạy cùng seed → identical log (determinism test pass); diff exogenous trace giữa arm → identical.
2. Sensitivity T1 5s vs 2s: |Δ| < 2% hoặc < ½ SD seeds trên metric nhạy (wait, expire, queue, payout).
3. Calibration B-arm (T-021, **gate trước khi so sánh arm**): output plausible/stable/explainable theo evidence tiers; actor full-time 15–30 cuốc/ngày và pattern nghỉ/sạc là benchmark `[PROXY]`, không invariant cứng. Unserved phải giải thích được theo supply/demand/lifecycle; không tune B-arm về 15–20% để làm A-arm trông tốt.

**DoD-eval (T-019 advisor + T-020 evaluator):**
4. Kịch bản 4: capacity ledger giảm P95 queue vs ledger-off, không giảm service level.
5. Báo cáo Δ(A−B), Δ(C−B), Δ(A−C) với CI ≥20 seeds cho kịch bản 1–2, **phân theo `advice_scope` (product_only vs sim_extended) × `advisor_information` (product_proxy vs oracle) × adherence sweep {0%, default, 100%}** — headline = product_only × product_proxy × default; upper-bound báo riêng.
6. Adherence report phân tầng theo divergence index; proximal outcome (90ph quanh episode) báo cùng distal.

**Tiền đề kinh tế:** mọi payout dùng `specs/sim-policy-bundle-v0.md` (fare 13k+4.3k/km, share 75%, điểm 10/5, mốc thưởng NGÀY mock, chi phí theo track); manifest ghi `policy_bundle_version`.
**OD boundary (compatibility pilot):** buffer ring k≤4 (demand chỉ sinh trong 85 cells lõi; trả khách ngoài phải có movement/deadhead rõ, không teleport); run 05:00–24:00 + warm-up 1h là profile lịch sử. M1 chuyển target sang `[00:00,24:00)` và không renormalize 24h demand vào window cũ.

## 8. Mở rộng sau pilot

Scale toàn nội thành (~400 cells res 8, N=500, 144 trạm) giữ nguyên kiến trúc — chỉ đổi config world. Các số [ƯỚC LƯỢNG]/mock gắn nhãn trong manifest theo ranh giới CLAUDE.md §5.
