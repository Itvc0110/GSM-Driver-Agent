# UPDATE-152 — E1a: sửa THƯỚC ĐO trước khi sửa kênh (đợt 1/5 chương trình tối ưu advisor)

- **Ngày:** 2026-08-06
- **Loại:** fix (đo lường/CLI/schema/UI-parity) — **KHÔNG đổi hành vi sim** (engine không chạm)
- **Liên quan:** UPDATE-151 (review 21 agent) · plan E1–E5 duyệt 2026-08-06 · r03/r06/r07/r08

## Đã sửa (9 mũi, test đỏ-trước `tests/test_e1a_thuoc_do.py` — 6 đỏ → 7 xanh)

| # | Việc | File |
| --- | --- | --- |
| 1 | CLI ladder **CRASH** (KeyError `significant` trên hàng `n_actors_scope`) — per-archetype chưa bao giờ in ra được. Lọc theo *"có significant"* thay vì né `one_way_gate` | `scripts/run_parallel.py` |
| 2 | `n_insufficient` so **ngưỡng hiệu lực** (`min_seeds` truyền vào) thay vì hằng 30 — hết cảnh hai cờ tự mâu thuẫn ở n=50/min=100 | `parallel.py compare` |
| 3 | **Lỗ Goodhart r07-F6**: `xveto_*`/`commit_*` (nối tầng 5 SAU khi frozenset chốt) lọt significance HAI CHIỀU → `_is_one_way()` match theo **tiền tố** `veto_/xveto_/commit_` + set cũ; khoá tầng-5 tương lai không lặp lại lỗ | `parallel.py` |
| 4 | Hàng system thêm `mean_a/mean_b/n_positive`; keys = **UNION** qua mọi pair (hết rơi im lặng/KeyError khi archetype vắng ở một seed) + `n_pairs` khai tường minh; keys sort để artifact diff được | `parallel.py compare` |
| 5 | **Metric pin THEO FLEET** (r03 SWAP-07): `payout/net_mean_F_{swap,charge}` + `charge_min_p50/p90_F_*` (percentile vì lưỡng đỉnh 1-2′ vs 210′ — mean gộp vô nghĩa; fleet confound 100% với archetype) | `parallel.py _cohort_metrics` |
| 6 | Probe spy `_claim_effect` sai chữ ký (TypeError ngay lượt đầu) | `scripts/probe_adherence_truth.py` |
| 7 | `format: date-time` **có răng**: validator nhận `_FORMAT_CHECKER` tự viết bằng `datetime.fromisoformat`. ⚠ KHÔNG dùng `FORMAT_CHECKER` mặc định của jsonschema — thiếu `rfc3339-validator` nên nó **không kiểm date-time** (đã đo: `'date-time' not in checkers`) ⇒ truyền suông là placebo D-R12. Test: `2029-02-31` bị chặn, bản hợp lệ đi qua | `schema_registry.py` |
| 8 | Ngưỡng SOC "thấp" của web đọc từ payload (`soc_low_threshold_pct` ← `vehicle.swap_soc_threshold_pct`) thay vì hardcode 25 ≠ engine 20 (họ D-M3-17); thiếu ngưỡng ⇒ không tô, không bịa. Nhãn MÔ PHỎNG cho SOC proxy **đã có sẵn** từ Q-06 — phần đó của T-045e là stale. +2 test parity vào cổng UI↔engine | `mockdata.py` · `app.js` · `test_range_matches_engine.py` |
| 9 | 3 hàng TODO stale (FIX/FIX-PRE/D-M3-06 đã DONE từ 141/142) | `tracking/TODO.md` |

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| `tests/test_e1a_thuoc_do.py` (đỏ-trước) | 6 đỏ → **7 passed** |
| Consumer của `compare()` (parallel_worlds · health_source_wired · control_arm_gate · evaluator_unbiased · dm304) | **51 passed**, 0 hồi quy |
| Sweep `-k "schema or checkpoint"` | 151 passed (2 F = K-01 đỏ sẵn của Khánh) |
| `ui/backend/tests/test_range_matches_engine.py` | **14 passed** (12 cũ + 2 parity mới) |
| CLI `run_parallel.py --seeds 2` | **exit 0**, in đủ per-archetype (`net_mean_P*`) + per-fleet (`charge_min_p*_F_*`); `xveto_*` nằm đúng mục tầng 5 một chiều |
| Behavior-neutral | engine (world/behavior/bridge/solvers) **không chạm** — fingerprint bất biến theo cấu trúc |

## Quan sát đáng giá cho E1b

CLI smoke 2 seed: **Δ = 0 TUYỆT ĐỐI** ở `s2_only` — arm B không ghi đè hành vi nào của target trên
cả hai seed. Khớp chẩn đoán **ADV-01** (DP floor điểm mỗi bucket ⇒ mốc thưởng không lái được lịch
⇒ schedule DP ≈ bản năng ⇒ kênh gần như câm). E1b sẽ reproduce có kiểm soát trước khi sửa.

## Visual

`NOT_APPLICABLE` — thước đo/CLI/schema; màn hình chỉ đổi hành vi tô "pin thấp" khi SOC ∈ [20,25)
(trước tô sai theo ngưỡng bịa 25). Gom vào V-31 cuối chương trình theo chỉ thị Cường.

## Follow-up

E1b (công thức kênh, 8 mũi) — bắt đầu ngay; mỗi mũi reproduce trước theo root-cause protocol.
