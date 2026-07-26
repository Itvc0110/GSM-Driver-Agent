# UPDATE-069 — AUDIT fix batch 2: gói S2 (shift_dp) + cụm STATS, sau khi verify 11/11

Ngày: 2026-07-27 · Track: AUDIT · Sau UPDATE-065/066 · Verdict nguồn:
`research/audit/2026-07-26-full-audit/a1_verify11_verdicts.json` (**11/11 CONFIRMED**, 4 CAO).

## 1. Verify 11 finding treo — kết quả

Workflow 11 refuter (749k token): **CONFIRMED 11/11**, 0 refuted. Nặng nhất:
- **S2-2 (CAO)**: `_forecast_arrays` đọc forecast theo INDEX trong khi producer (bridge sim +
  l1r) sinh **nhiều dòng/bucket** (1 dòng/cell) ⇒ demand lệch giờ, mất bucket cuối, **E[payout]
  sai ~×2** (repro: 76.205 vs 146.362).
- **S2-3 (CAO)**: terminal bonus cộng vào E[payout] không xét eligibility (cùng lỗi S1-1).
- **STATS-1 (CAO)**: `/ab` phán "✅ ổn" trên 1 seed với ngưỡng bịa (−50k).
- **EST-8 (CAO)**: đề án shrinkage được refuter kiểm toán học + repro → **đáng trình Cường**
  (kèm 2 lưu ý: prior mean-of-ratios cần đổi sang pooled counts; m là knob ảnh hưởng advice
  "cứu ngày xui" — phải calibrate 30 seed).

## 2. Fix đã vào (7)

| ID | Fix | File |
|---|---|---|
| **S2-2** | `_forecast_arrays` GỘP theo timestamp bucket + sort thời gian + trả `bucket_labels` (schedule/next_action dùng nhãn đã gộp) | `shift_dp.py` |
| **S2-3** | `_bonus_eligible(params)` — dưới ngưỡng tỷ lệ thì MỌI nhánh `bonus_at`=0 (terminal, END, reconstruct, baseline) + caveat; thiếu số ⇒ giữ bonus + caveat rõ | `shift_dp.py` |
| **S2-6** | `bucket_min` thành tham số thật: `_required_rest` theo phút thật, `_soc_cost` scale theo bucket | `shift_dp.py` |
| **S2-7** | Cap sức chứa `bucket_min/service_min_per_trip` cho expected_orders (demand CẢ CELL không dồn hết vào 1 tài xế) — mitigation hẹp, model gap thật vẫn ở đề án | `shift_dp.py` |
| **STATS-5** | `compare()` chỉ bật `significant` khi **n ≥ 30** (`MIN_SEEDS_FOR_SIGNIFICANCE`) + cờ `n_insufficient` | `parallel.py` |
| **STATS-3/BEHAV-4** | `realized_cap(archetype, lift) = min(0.98, base + lift − 0.02)` bám ANCHOR ĐO 0.93, theo base từng archetype (bỏ hardcode 0.80 + cộng lạc quan) | `run_sensitivity.py` |
| **STATS-1** | `/ab` guardrail: `ok=null` trên 1 seed (bỏ ngưỡng bịa), thêm `others_payout_delta_vnd`; contract v1.1 nullable; UI hiện "— (1 seed)" + trỏ tab Độ nhạy | `sim.py` · `ab_result.json` · `mo-phong.js` |
| **STATS-4/7** | sweep: ô P2 đổi tên `P2_dip_rescue_check` (nhãn "silence" bị data bác), mỗi ô ghi `n_advice_events`/`n_offers`/`n_seeds`/`max_realized_accept_used`; `_meta` giải thích; artifact cũ **đánh dấu STALE** + UI hiện cảnh báo | `run_sensitivity.py` · `dsim06_sweep.json` · `mo-phong.js` |

## 3. Regression tests (đỏ-trước)

`tests/test_shift_dp.py` +5 (gộp bucket · schedule phủ đủ bucket · gate bonus theo tỷ lệ ·
required_rest theo bucket_min · cap sức chứa) — chạy đỏ 5/5 trước fix.
`tests/test_parallel_worlds.py` +2 (n=1 không được significant · n=30 thì được).
`tests/test_sweep_helpers.py` (TẠO, 3 test: cap khớp anchor đo · dùng base archetype · không
lạc quan hơn nominal). `ui/backend/tests` sửa test guardrail → đòi `ok is None`.

## 4. Kiểm chứng

- `pytest tests/test_shift_dp.py tests/test_solver_properties.py tests/test_advice_bridge.py`:
  **81 passed**. `test_parallel_worlds.py + test_sweep_helpers.py`: **17 passed**.
  `ui/backend/tests`: **23 passed**. Full suite chạy ở bước kế (ghi số sau khi đọc).
- Artifact sweep cũ giữ nguyên số nhưng gắn STALE — **không xoá**, để đối chiếu khi chạy lại.
- Visual: mo-phong A/B card + cảnh báo STALE → nhập **V-10**.

## 5. Còn nợ (đã ghi hồ sơ audit)

S2-4 (p_accept cá nhân hoá) và S2-5 (avg_dist từ data) mở **đường tham số** rồi nhưng call site
chưa truyền — thuộc **ĐA-03**, cần chốt cùng đề án. Chạy lại sweep 30-seed sau khi chốt ĐA-01.

---
**⏳ PENDING-REVIEW:** V-01..V-09 · **V-10** · Q-03 · **ĐA-01/02/03 chờ Cường duyệt**.
