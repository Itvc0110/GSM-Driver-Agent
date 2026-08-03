# Nguồn số liệu — Week 2 Report

Mọi con số trong báo cáo truy được về một file cụ thể. Bảng này để mentor (hoặc bất kỳ ai) đối
chiếu mà không phải tin lời.

**Ngày đo:** 01/08/2026 · **Chế độ:** MOCK (`configs/pilot_dongda.yaml`) · **Engine commit:**
`d325055`

---

## 1. Kết quả E10 — bốn arm (§11.1)

Nguồn chính: `research/audit/2026-07-27-current-state/41-e10-diff.json`

| Số trong báo cáo | Khoá trong artifact |
| --- | --- |
| `B_oracle` +3.938,9đ · CI [2.854,0; 5.033,1] · MDE 1.080,4 | `stop1_delta_oracle` |
| `B_hist` +3.400,6đ · CI [2.423,0; 4.337,4] · MDE 957,3 | `arms.hist.delta_vs_A` |
| `B_hist` Δ vs oracle −538,3 · MDE_dd 1.012,0 | `arms.hist.delta_vs_oracle` |
| `B_real` +3.126,5đ · CI [2.079,9; 4.167,1] · MDE 1.035,0 | `arms.real.delta_vs_A` |
| `B_real` Δ vs oracle −812,5 · MDE_dd 1.211,7 | `arms.real.delta_vs_oracle` |
| `B_wait` +174,0đ · CI [−602,9; +916,3] · MDE 770,3 | `arms.wait.delta_vs_A` |
| *"không tái lập được +6.016"* | `stop1_delta_oracle.ref_update087` = `6016` |
| HHI cung real 0,01235 vs oracle 0,01214 | `g_herd_hhi` |
| n=100, seed 5000–5099, bootstrap 5000 lần seed 12345 | `prereg.seeds_measure`, `prereg.metric_chinh` |
| Spearman pickup-vs-λ = 0,41 (caveat L2) | `UPDATE-113` §caveat |

Artifact per-arm: `41-e10-arm-{oracle,hist,real,wait}-n100.json` (mỗi file có `verdict`,
`z_pooled_positioning`, `adherence_pooled`, `decided_total`).

## 2. E10b — quét ngưỡng (§11.2)

Nguồn: `research/audit/2026-07-27-current-state/44-e10blow-summary.json`, khoá `ket_qua`

| T | Δ vs A | CI | Can thiệp/ngày | Giữ % | Lớp |
| --- | --- | --- | --- | --- | --- |
| 10 | 2.589,3 | [1.687,5; 3.464,4] | 46,3 | 66% | KQ-CÒN-MỘT-PHẦN |
| 12 | 2.960,8 | [2.057,8; 3.830,4] | 42,1 | 75% | KQ-GIỮ |
| 15 | 2.159,1 | [945,4; 3.313,8] | 36,0 | — | KQ-CÒN-MỘT-PHẦN |
| 18 | 1.777,6 | [788,3; 2.759,1] | 27,4 | — | KQ-CÒN-MỘT-PHẦN |

Tham số khoá trước khi đo: `specs/simulation/e10b-low-threshold-prereg-locked.json`

## 3. Độ ổn định (§11.3)

| Số | Nguồn |
| --- | --- |
| Fingerprint 15/15 IDENTICAL | `UPDATE-102:196` |
| Fingerprint 10/10 IDENTICAL | `UPDATE-109:42` |
| Fingerprint 5/5 IDENTICAL + hash `040c79a862f4b6a4`, `d9671c69e57568c0`, `e3bf368273b8c91c`, `b5068bc7b258812e`, `93de60f8f29ce9d7` | `UPDATE-117` §Kiểm chứng |
| SD ≈ 409đ (3 realization cùng seed) | `research/audit/2026-07-27-current-state/43-coin-realization-probe.json` |
| Cổng z: −2,39 → −4,41 TREO → −0,38/+0,82/−0,95/−0,16 | `UPDATE-113:13-14, 83-86` |
| Bias thước 2,4 điểm phần trăm; z=2,29 (n=30) vs z=4,20 (n=100) | `UPDATE-113` §lỗi phương pháp |

## 4. Guardrail sức khoẻ (§11.4)

| Số | Nguồn |
| --- | --- |
| Vòng 1 (5 seed 5100–5104): `rest_min_total` 3.772,6 → 4.774,2 | `42-rest-rails-sabotage-probe.json` |
| Vòng 2 (seed 5011): 3.689,0 → 4.041,8 · `work_span_p90` 388,3 → 370,5 · `drive_min_p90` 314,6 → 301,2 · `veto_fired_n` 175 → 184 · `n_actors_scope` 90/90 | `UPDATE-116` §Kết quả đo trên đường thật |
| G-GUARD 0/9 tầng suy giảm | `41-e10-diff.json` `arms.*.g_guard_sig_worse` (rỗng) |
| `ADHERENCE_Z_MAX = 4.0` · `STAT_GATE_MIN_DENOM = 20` | `src/gsm_sim/sim_metrics.py:631-632` |
| `IMPOSSIBLE_ADHERENCE_MIN_DENOM = 20` | `src/gsm_sim/sim_metrics.py:486` |

## 5. Công bằng (§10.2)

| Số | Nguồn |
| --- | --- |
| Gini payout −0,0069 SIG | `UPDATE-087` |
| 0/7 archetype bị hại; 5/7 dương SIG | `specs/advisor-objective-model-v2.md:217-218` |
| Đường cong phủ: +0,60 → +0,98 → +1,13 → +1,74 điểm phần trăm | `research/simulation/multi-agent-equilibrium.md` |
| Mức nền arm A: served 0,7902 · payout/người 247.925đ (30 seed) | `research/simulation/multi-agent-equilibrium.md` |
| `dispatcher.py` 151 dòng, 0 lần tham chiếu advice | `grep -ci "advice\|advisor\|bridge" src/gsm_sim/dispatcher.py` |

## 6. Bài học estimator (§11.6)

Nguồn: `tracking/updates/UPDATE-085-cycle-r-p-va-bug*.md`

| Cách đo | Δ payout |
| --- | --- |
| argmax arm A | −19.654đ |
| argmax arm B | +27.416đ |
| mean P4 | +3.610đ |
| toàn đội (cohort) | +5.350đ |

## 7. Tham số mô phỏng (§5.5)

Tất cả từ `configs/pilot_dongda.yaml`:

| Tham số | Dòng |
| --- | --- |
| `start_min: 300`, `end_min: 1440`, `warmup_min: 60`, `dispatch_tick_s: 5` | 20–25 |
| `orders_per_day: 1200` | 32 |
| `h3_res: 9` (~85 ô lõi), `h3_res_report: 8` | 16–17 |
| `swap_consume_pct_per_km: 1.6`, `charge_consume_pct_per_km: 0.85` | vehicle |
| `home_charge_min: 210`, `swap_soc_threshold_pct: 20` | vehicle |
| `battery_recharge_min: 105`, `wait_cap_min: 60`, tủ `slots−1 = 5` viên | 157–163 |
| 7 archetype P1–P7 + tỷ trọng | 228–243 |
| `accept_lift_step: 0.10`, `accept_lift_max: 0.15` | 366–368 |
| `advice.enabled: false` (mặc định advisor im) | advice |
| `cadence.enabled: false` ở sim | 416 |

Code: `ActorState` 6 giá trị (`src/gsm_sim/entities.py:12-23`) · `IdleAction` 6 giá trị
(`src/gsm_sim/behavior.py:20-26`) · thứ tự ưu tiên hành động (`behavior.py:134-210`) ·
logit nhận cuốc (`behavior.py:57-101`) · 5 nhịp thời gian (`world.py:546-548,534,970,768-769`) ·
dispatcher 2 tầng (`dispatcher.py:1-27,61-134`) · `MAX_PAIRS = 200.000` (`dispatcher.py:40-42`).

## 8. Thống kê (§4.3)

| Tham số | Nguồn |
| --- | --- |
| bootstrap `n_boot=5000`, `alpha=0.05`, `seed=12345` | `src/gsm_sim/parallel.py:241-253` |
| `MIN_SEEDS_FOR_SIGNIFICANCE = 30` | `src/gsm_sim/parallel.py:258` |
| `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100` | `src/gsm_sim/parallel.py:268` |
| z Poisson-binomial | `src/gsm_sim/sim_metrics.py:670-684` |
| Adherence danh nghĩa P1 0,55 · P2 0,50 · P3 0,30 · P4 0,75 · P5 0,30 · P6 0,50 | `src/gsm_sim/advice_bridge.py:95-98` |

## 9. Kiểm thử và quy trình (§11.5, §12.6)

| Số | Nguồn |
| --- | --- |
| Suite 850 → … → 1.000 passed | `UPDATE-102:99,263` · `UPDATE-110:130` · `UPDATE-113` · `UPDATE-114:76` · `UPDATE-115` · `UPDATE-116` · `UPDATE-117` · `UPDATE-118:68-70` |
| 935 + 65 = 1.000 passed; 1.004 collected; 4 skipped | đo lại 01/08/2026 (`uv run pytest -q` và `uv run pytest -q ui/backend/tests`) |
| 4 bảng skip (`trips`, `driver_penalization_ATA`, `public_frauds`, `public_user_mission_progress`) | `tests/test_schema_matches_gsm_spec.py:41` |
| `ci.yml` 61 dòng, 3 job, tự khai CHƯA ACTIVE nhưng đã trên `origin/main` (blob `5318b81`) | `.github/workflows/ci.yml:1-4` |
| 112 file `UPDATE-*.md` | `ls tracking/updates/UPDATE-*.md \| wc -l` |
| Sổ nợ 90 mục: 21 đóng, 69 mở | `tracking/DEFERRED.md` |
| 20 mục chờ review | `tracking/PENDING-REVIEW.md` mục `## ⏳ CHỜ CHECK` |

## 10. Số của UI (§9)

| Số | Nguồn |
| --- | --- |
| Δ = −10.819đ (seed 1000, kênh `all`) | chụp trực tiếp từ UI 01/08 — `assets/ui-track-08-ab-ketqua.png` |
| Card: mốc 30.000đ, thiếu 55 điểm, 9,5 giờ, 11 cuốc | chụp trực tiếp — `assets/ui-track-01-landing.png`; số do solver S1 sinh |
| Dashboard 7 tab | chụp trực tiếp — `assets/dashboard-01-tong-quan.png` |
| 29/90 tài xế trên đường lúc 15:06 | ảnh Khánh — `assets/ui-track-mo-phong.png` |
| OSRM 284 điểm, 8,7 km, cước 208.800đ | ảnh Khánh — `assets/ui-driver-app-cuoc-osrm.png` |
| Solver trả ONLINE 6.329 / REST 338 / SWAP 72 | `research/audit/2026-07-27-current-state/18-*.json` |
| `Q-14`: UI chỉ chạy 1/9 solver | `tracking/PENDING-REVIEW.md:52` |
| `D-M3-17`: UI `soc*1.1`; legacy `soc*3.2` | `ui/backend/app/adapters/mockdata.py:147` · `ui/backend/app/simulator.py:157` |

## 11. API ngoài (§8)

| Số | Nguồn |
| --- | --- |
| 1 lời gọi API ngoài runtime: OSRM qua `urllib.request.urlopen` | `ui/backend/app/routers/routing.py` |
| Ma trận hệ số đường OSRM offline, `factor = osrm_km / haversine`, kẹp [1,0; 3,5] | `src/gsm_sim/geo.py:226-234` |
| Hệ số OSRM thật biến thiên 1,00 → 3,50; hệ số phẳng từng làm 293/3.520 lượt bỏ oan | `src/gsm_sim/dispatcher.py:17` |

---

## Cách tái tạo

```bash
# 4 biểu đồ (đọc số từ artifact, không nhập tay)
uv run python docs/reports/week2/make_figures.py

# PDF
uv run python docs/reports/week2/build_pdf.py

# Suite (phải chạy CẢ HAI lệnh mới gọi là "suite xanh")
uv run pytest -q
uv run pytest -q ui/backend/tests
```
