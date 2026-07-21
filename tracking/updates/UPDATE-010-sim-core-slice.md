# UPDATE-010 — T-018 vertical slice: simulator core chạy được (arm B, Đống Đa, 1 ngày)

- **Ngày:** 2026-07-21
- **Người thực hiện:** AI agent (Claude Code), dưới claim T-018 của Cường
- **Loại:** code (implement)
- **TODO liên quan:** T-018 (DOING — vertical slice DONE)

## Tóm tắt

Dựng `src/gsm_sim/` (uv + Python 3.11): nạp thế giới Đống Đa từ OSM, sinh demand mock deterministic, dispatcher batched-nearest, 50 actors B-arm (behavior model bản năng) chạy 1 ngày trên SimPy, xuất event log parquet + manifest + metrics. **29/29 test xanh**; CLI chạy ra kết quả hợp lý theo archetype.

## Chi tiết (các checkpoint chạy được)

1. **Scaffold**: `pyproject.toml` (uv, hatchling, deps: simpy/h3/numpy/polars/pyarrow/shapely/pyyaml, [dev] pytest), `configs/pilot_dongda.yaml` (mọi số từ specs, nhãn MOCK). Checkpoint 1 đã merge `main` (778875f).
2. **geo.py**: nạp polygon 5 phường (shapely polygonize từ way outer), 11 trạm pin, 59 POI (dùng `center` cho way/relation); polyfill H3 res9. Verify khớp research tuyệt đối: **85 core cells, 11 trạm (9 trong lõi), 26 BV + 13 ĐH, 19 parent res8**.
3. **policy.py**: sim-policy-bundle-v0 (fare 13k+4.3k/km, share 75%, điểm 10/5 theo giờ đặt, mốc ngày, next_tier_gap). demand.py: exogenous trace Poisson theo giờ×cell, OD distance-decay, renormalize trong window. Sanity: 1191 đơn, median 3.48km/19.3k, 2 đỉnh 7h & 17-19h.
4. **entities/archetypes/behavior**: 5 archetype → sample 50 actors có jitter (P2=15, P3=5...); behavior B-arm (accept logistic, idle action: wait/relocate/swap/charge/rest/end, chọn trạm, battery model).
5. **dispatcher/world/runner**: batched-nearest trên tick 5s; SimPy DES cho trip/swap lifecycle + order expiry; deadhead khi trả khách ngoài lõi; forced_auto_accept khi acceptance<50%.
6. **metrics/logging/cli**: summarize 3 tầng sơ bộ, ghi events+actors parquet + manifest.json (nhãn mock/version); CLI `gsm-sim run` in bảng + ascii chart cuốc/giờ.

## Kết quả run (seed 2, DỮ LIỆU MÔ PHỎNG)

| Archetype | Trips TB | Payout median | Acceptance |
| --- | --- | --- | --- |
| P2 full-time RTO | 19.8 | 302k | 0.93 |
| P3 top performer | 17.6 | 289k | 0.97 |
| P4 tân binh | 13.5 | 224k | 0.82 |
| P1 sinh viên PT | 12.5 | 197k | 0.89 |
| P5 lão làng | 8.4 | 162k | 0.99 |

Hành vi khớp thiết kế persona: full-time acceptance cao → nhiều cuốc/payout; tân binh acceptance thấp nhất; lão làng giờ ngắn ít cuốc nhất. Served rate ~66% (unserved cao hơn dải target 15-20% → cần tinh chỉnh ở calibration T-021, chưa phải gate).

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| pyproject.toml, uv.lock, configs/pilot_dongda.yaml | tạo (uv.lock/pyproject đã có từ checkpoint 1) |
| src/gsm_sim/{__init__,config,geo,policy,demand,entities,archetypes,behavior,dispatcher,world,runner,metrics,logging_ev,cli}.py | tạo |
| tests/{test_geo,test_policy_demand,test_actors,test_run_smoke}.py | tạo |
| .gitignore (Python + runs/) | sửa |

## Kiểm chứng

- `uv run --extra dev pytest`: **29 passed**.
- `uv run gsm-sim run --config configs/pilot_dongda.yaml --seed N`: chạy, ghi parquet, đọc lại được.
- Determinism sơ bộ: 2 lần cùng seed → metrics tổng khớp (byte-identical để vòng sau).
- CHƯA làm (vòng sau DoD-core / T-019 / T-020): twin-runner 3 arm, RNG per-(entity,purpose) đầy đủ + determinism byte-identical, sensitivity 5s/2s, calibration gate T-021 (served rate cần chỉnh), Hungarian, advisor A/C, evaluator/dashboard/kepler.
- Behavior model là xấp xỉ utility (chưa full spec §1) — đủ cho slice, tinh chỉnh ở T-021.

## Follow-up

- T-021 calibration: chỉnh để unserved về 15-20% (hiện ~34%) — có thể do dispatcher greedy + relocate hạn chế + acceptance; tune trước khi so sánh arm.
- T-019 advisor arm A/C cắm vào world (đã có chỗ: RNG stream, demand_hint param trong choose_idle_action).
- Push checkpoint này lên main để Khánh/Cường có code nền.
