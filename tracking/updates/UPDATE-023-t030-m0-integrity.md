# UPDATE-023 — T-030 / M0 Simulator Integrity: 12 flaw fixed + regression suite + observable/latent taxonomy

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent (dưới claim **Cường** T-018/T-030)
- **Loại:** fix / feature / test / spec
- **TODO / User story liên quan:** T-030 (M0 integrity — gate mở M1–M4), T-021 (calibration gap ghi nhận)

## Tóm tắt

Đóng 12 flaw M0 đã CONFIRMED trong audit 14-agent + 1 bug C-2, theo đúng root-cause protocol §4b: mỗi fix có regression test **failing-first** (chạy chứng minh đỏ trước khi sửa). 5 commit hẹp: baseline Stage A–C (`71313bf`) → tranche 1 conservation (`db1056e`) → tranche 2 information/behavior (`9d6bd8f`) → tranche 3 spatial/dispatch (`5567c67`) → drop-sampling contract (`97e8cb2`). Test suite 38 → **57 pass** (19 test M0 mới). Thêm taxonomy **Observable/Inferable/Latent** vào master spec theo insight của Cường về `meals_taken`.

## Chi tiết cập nhật

### Flaw đã fix (mã audit → root cause → fix)

| Mã | Root cause đã prove | Fix |
|---|---|---|
| M0-1 | Pin trả trạm append `soc=0` không có process nâng lên ready → tủ chết dần; hết wait-cap vẫn nhận pin 100% "ma" | Đổi pin 1-1 ATOMIC trong wait-loop (pin đầy ra + pin cạn vào sạc cùng lúc, chống race); pin hồi `soc=100, ready_at=sạc xong`; hết cap → `swap_failed`, SOC nguyên |
| M0-2 | Dispatch stateless → cùng (đơn, tài xế) chào lại mỗi 5s sau decline | `offer_history` + `dispatcher.offer_cooldown_min` (config, default 10ph) |
| M0-3 | `demand_field` xây từ TOÀN BỘ orders của run → actor thấy đơn tương lai | `expected_demand_field(config)`: λ = orders/day × hour_share × cell_weight — không đọc realized trace |
| M0-4 | Belief resample mỗi idle-check + duyệt `set` → nhiễu trắng + **cross-process nondeterminism (PYTHONHASHSEED — đã prove: 3 process 3 kết quả)** | Belief cache per (actor, hour, cell-view); nhiễu per-cell RNG `(seed, actor, hour, cell)`; duyệt sorted. 3 process giờ identical |
| M0-5 | Order không có state machine — đơn matched có thể "bốc hơi" | `order_states`: CREATED→OPEN→MATCHED→PICKED_UP→COMPLETED/EXPIRED/CENSORED; terminal bất biến; event `order_matched` |
| M0-6 | `env.run(until)` bỏ rơi actor/đơn in-flight; không censor | `_settle_end_of_run`: censor đơn + label `censored_end_of_run` cho actor bận |
| M0-7 | Meal rest re-fire trong cùng giờ | `meals_taken` flag — 1 lần/ngày |
| M0-8 | GO_CHARGE sạc tại chỗ (teleport), `home_cell` không dùng | Leg di chuyển thật về `home_cell` (thời gian + pin + segment `go_home_charge`) |
| M0-9 | `dist_km` lognormal độc lập endpoints → fare/time/SOC không khớp hình học | `dist_km = haversine(pickup_pt, drop_pt)`; lognormal chỉ CHỌN drop cell. Kèm fix cap `buffer_k+3` (chặn mọi cuốc >2.5km) + OD boundary đúng spec (lõi ∪ buffer quanh lõi) |
| M0-10 | `_set_pos` không sync H3 → 5 chỗ gán cell thủ công, dễ desync | `_set_pos` atomic lat/lon+cell; xóa mọi gán tay |
| M0-11 | Dispatch dừng ở ring đầu có candidate → người gần hơn ring kế bị bỏ | Quét MỘT LẦN toàn disk k_max |
| M0-12 | Tie-break theo thứ tự duyệt | Key `(distance, actor_id)` deterministic |
| M0-4-time | `online_min` mất đoạn bận cuối ngày | `_last_accrual` per-actor + flush lúc settle |
| C-2 | `enabled=false` không gate `route_effect` | `r()` trả 0 toàn bộ khi disabled |

### Taxonomy Observable / Inferable / Latent (spec §3.5 — từ câu hỏi Cường)

Cường chỉ ra `meals_taken` không đo được ở hệ thực Xanh SM — chỉ đo được app events/GPS/swap, còn "nghỉ ăn" phải SUY từ đứng-im-dài-giữa-trưa. Đã ghi vào master spec: latent state (meals, fatigue, belief, patience) là **sim-only ground truth** điều khiển behavior; **advisor/evaluator/F3 chỉ được tiêu thụ observable + inferable projection** — đọc latent = vi phạm cùng lớp future-leak. Follow-up T-031/T-036: xây inferable-projection layer + nhãn `SIM-GROUND-TRUTH` trong UI (hiện `trajectory.py` còn dùng `patience_min` cho customer viz — được phép ở Diagnostic, cần nhãn khi làm M3).

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_sim/world.py` | M0-1/2/3/4/5/6/8/10 + settle end-of-run |
| `src/gsm_sim/demand.py` | `expected_demand_field`, M0-9 contract, drop-disk + OD boundary |
| `src/gsm_sim/dispatcher.py` | M0-11/12 full-scan + tie-break; bỏ import thừa |
| `src/gsm_sim/behavior.py` | meal flag |
| `src/gsm_sim/entities.py` | `meals_taken` |
| `src/gsm_sim/congestion.py` | C-2 toggle |
| `src/gsm_sim/runner.py` | expose `stations`, `order_states` |
| `tests/test_m0_integrity.py` | tạo — 19 tests |
| `specs/simulation-reliability-upgrade.md` | taxonomy observable/inferable/latent |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| 12 flaw tồn tại ở baseline | `OBSERVED-CODE` | Audit 14-agent + 14/19 test đỏ trước fix | Cao | — |
| PYTHONHASHSEED gây cross-process drift | `OBSERVED-CODE` | 3 process khác kết quả trước fix; identical sau | Cao | CRN A/B/C sẽ vỡ nếu còn |
| Median cuốc 3.2km < target 3.5km là giới hạn địa lý pilot (~3-4km ngang) | `ASSUMPTION` → T-021 | Đo phân phối sau fix; Đống Đa 9.95km² | Trung | Nếu sai → cần xem lại drop kernel |
| Swap wait ≈ 0 sau fix là hệ quả pin hồi thật (11 tủ × 5 pin, 105ph/viên đủ cho ~50 swap/ngày) | `OBSERVED-CODE` + throughput arithmetic | swap_events 54; capacity ~55 pin luân chuyển | Trung-cao | Nếu demand swap tăng (T-031 24h) queue sẽ xuất hiện lại |

## Kiểm chứng

### Seeds và scenarios

| Run | Seeds | Scenario | Kết quả |
|---|---|---|---|
| `pytest -q` full suite | fixture seeds | dry + env bounds | **57/57 pass** (từng tranche đều chạy lại) |
| Failing-first proof | seed 3/4 | dry | 14/19 test M0 đỏ trước fix, xanh sau |
| Cross-process determinism | seed 1 × 3 process | dry | identical (trước fix: 3 kết quả khác nhau) |
| Shift table 5 seeds | 1–5 | dry (baseline json vs post json, scratchpad) | bảng dưới |

### Bảng dịch chuyển metrics (mean 5 seeds, dry) — mọi shift có giải thích

| Metric | Baseline | Sau T-030 | Giải thích |
|---|---|---|---|
| served_rate | 0.61 | 0.60 | Cooldown bỏ re-offer ảo; censoring chuyển đơn treo về EXPIRED/CENSORED |
| swap_wait_median/max | 6.1 / 61 | 0 / 0 | Pin HỒI thật → tủ không cạn dần như bug cũ; capacity 11 tủ đủ cho 54 swap |
| swap_events | 66 | 54 | Hết livelock re-swap; meal 1 lần → ít vòng idle-check |
| utilization_ft | 0.53 | 0.39 | `online_min` giờ ĐỦ (đoạn bận cuối ngày + đo đúng) → mẫu số tăng; con số cũ cao ẢO |
| payout_ft | 290k | 243k | dist thực (median 3.2 vs lognormal 3.5) + không còn double-serve từ re-offer |
| pickup_eta_median | 3.53 | 3.95 | Full-scan disk chọn ĐÚNG người gần nhất nhưng cooldown làm pool nhỏ hơn ở peak |
| battery_stranded | 0 | 0 | Không đổi (A8 vẫn defer) |

**CHƯA kiểm chứng:** distribution/calibration ≥30 seeds (thuộc T-021/T-031 gate); rain/event scenario multi-seed (chạy 1 seed smoke trong suite); inferable-projection layer chưa xây (mới ghi spec).

## Visual verification

- **Status:** `REVIEWED` — Cường xem dashboard (port 8501, health 200) 2026-07-22 và duyệt push.
- **Cách launch:** `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` (port 8501).
- **Seed/scenario:** seed 1, dry_weekday + rain_peak.
- **Verdict:** OK push. UI v0 còn lỗi đã biết (tủ pin/H3, trajectory player) — scope T-035–T-037, không thuộc T-030.

## Adversarial self-review / flaws found

1. **Trông tốt nhưng sai?** swap_wait=0 có thể bị đọc là "trạm thừa công suất" — thật ra là 50 actor/11 tủ pilot nhỏ; T-031 (24h, pool lớn) sẽ stress lại. Utilization giảm 0.53→0.39 là số cũ SAI (mẫu số thiếu), không phải sim tệ đi.
2. **Leak/CRN:** future-leak đã đóng (expected field); belief RNG tách stream — không tiêu behavior stream (CRN giữ); cross-process determinism PASS. `patience_min` trong customer viz là latent — nhãn ở M3.
3. **Assumption yếu nhất:** giải thích median 3.2km bằng địa lý pilot — cần T-021 kiểm bằng phân phối thực tế nếu có data.
4. **Baseline so sánh:** t030_baseline_metrics.json (5 seeds) vs post; từng shift giải thích ở trên; không shift nào không giải thích được.
5. **Flaw còn mở → TODO:** dead flag `hour_interp` (M1-3, T-031); dynamic fleet + 0-24h (T-031); OSM endpoints (T-032); UI fixes (T-035–T-037); A8 nhiễu tiêu pin (defer); inferable-projection (T-031/T-036).

## Follow-up / defer phát sinh

- **T-031:** thêm scope inferable-projection layer (observable events → inferred rest/charge/relocate) làm data schema chuẩn cho advisor/evaluator.
- **T-021:** calibration gap median cuốc 3.2km (địa lý pilot) — đối chiếu khi có benchmark.
- Sạc swap_wait stress trở lại khi T-031 mở 24h/pool lớn — theo dõi.
