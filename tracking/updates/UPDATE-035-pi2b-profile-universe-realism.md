# UPDATE-035 — PI-2b: profile universe (mọi loại GSM) + realistic acceptance + CSV export

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (refine Cường: realism+random, profile phủ car/bike/prem, defer zone)
- **Loại:** feature (mockgen realism + diversity)
- **TODO / User story liên quan:** Real-data PI-2b; caveat R2 (UPDATE-034)

## Tóm tắt

Nâng cấp generator mock l1r thành **profile-driven**: (1) sửa caveat R2 **acceptance median 1.00→0.88** (theo archetype target + noise, back-out decline); (2) **profile universe phủ mọi loại GSM** (bike-platform/rto, car-platform/employee, car-premium) — sim CHỈ simulate subset bike, còn lại rule-based; (3) thêm randomness (ngày nghỉ, fare/dist variance, reposition target_hex, penalty/fraud đa dạng type). Zone enlargement DEFER (Cường). + tool `parquet_to_csv.py` cho Cường review tay. Full suite **204 pass**.

## Chi tiết cập nhật

- **`mockgen/profiles.py`** (mới): `build_profile_universe(sim_bike_ids, seed, ...)` → roster {driver_id: profile}. 5 archetype (newbie 0.74 … top 0.96) × 5 kind GSM (share/fare/vehicle theo `economics/income-structure`). Bike-sim khớp id sim; car/premium/rto rule-based.
- **`mockgen/realdata.py`** (viết lại v2): `build_tables` profile-driven. Bike trips từ sim; **car/premium/rto trips rule-based** (`rule_based_trips`: fare theo kind, demand shape 2 đỉnh, ~12% ngày nghỉ). `_emit_day` aggregate ĐỒNG NHẤT với **acceptance = clamp(gauss(target, 0.04))** → accepted/declined back-solve; **per-driver `driver_share`** (bike .75/rto .90/car-emp .25/car .75). hex_tracking chỉ bike + ~5% reposition target_hex. penalty/fraud đa dạng type.
- **`scripts/parquet_to_csv.py`** (mới): export mọi parquet → CSV utf-8-sig (Excel review). `data/mock/realdata-v1/csv/`.
- **R2 re-verify** (30 seeds/3083 driver-days): acceptance median **0.88** (p10 0.75), payout median 273k (p90 **954k** — car/premium tail thật), 6/6 in-range. Caveat acceptance-degenerate ĐÃ ĐÓNG.
- Regenerate `data/mock/realdata-v1` (21 ngày, 110 profile: 50 bike + 20 rto + 15 car + 15 car-emp + 10 premium) → 2152 driver-day, 34k trips.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `src/gsm_core/mockgen/profiles.py` | tạo (profile universe) |
| `src/gsm_core/mockgen/realdata.py` | viết lại v2 (profile-driven) |
| `scripts/parquet_to_csv.py` | tạo (CSV export) |
| `tests/test_realdata_gen.py` | sửa (per-driver share + 3 test realism/diversity) |
| `research/experiments/mockgen-realdata/ROUND-2-stats-report.md` | cập nhật (acceptance 0.88) |
| `tracking/{TODO,updates}` | governance |
| `data/mock/realdata-v1/{*.parquet,csv/*}` | regen (gitignored) |

## Docs đã cập nhật kèm theo
TODO: PI-2b refine + đang làm. Không đổi SCOPE/USER_STORIES.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| acceptance 1.00→0.88 realistic | `OBSERVED-CODE` | R2 report + test_acceptance_realistic | Cao | — |
| universe phủ car/bike/prem | `OBSERVED-CODE` | test_profile_universe_diverse | Cao | — |
| per-driver share đúng | `OBSERVED-CODE` | test_r3_commission_per_driver_share | Cao | payout lệch |
| car income (fare/share) | `PROXY/MOCK` | economics/income-structure (car lương+25%, premium fare cao) | TB | car payout lệch định nghĩa GSM |
| car-employee share 0.25 (bỏ base salary) | `ASSUMPTION` | đơn giản hóa (chưa model lương cứng) | TB | employee net sai — cần data thật |

## Kiểm chứng

`pytest tests/test_realdata_gen.py` 12 pass (R1/R3/R4 + acceptance realistic + diversity + car-present); full suite **204 pass**. R2 30-seed: acceptance median 0.88 (fixed), 6/6 in-range. Regenerate + CSV export OK. **CHƯA kiểm chứng:** car/premium income vs định nghĩa GSM thật (base salary employee chưa model — ASSUMPTION); lớp thưởng tuần chưa cộng vào payout (payout vẫn biên dưới cho bike — chờ S5); scale 90+ ngày chưa chạy (smoke 21 ngày).

### Seeds và scenarios
| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| test_realdata_gen (8 ngày, 110 driver) | 12 pass | — |
| R2 30 seeds/3083 dd | acceptance 0.88, 6/6 | car income def |

## Visual verification
- **Status:** `NOT_APPLICABLE` — data tooling. CSV export cho Cường review tay (`data/mock/realdata-v1/csv/`).

## Adversarial self-review / flaws found
1. **car-employee share 0.25 bỏ base salary** → income employee thấp giả tạo; nhãn ASSUMPTION, cần data thật/định nghĩa GSM.
2. **payout bike vẫn biên dưới** (thiếu lớp thưởng tuần) — chưa fix ở PI-2b (thuộc S5/rule); R2 payout median tăng nhờ car tail, không phải bike bonus.
3. **car/premium không có hex_tracking** (bike-only) → UC5 idle chỉ bike; hợp lý (reposition bike).
4. **rule-based car trips hex giả** ("8amock##") — không geo thật; đủ cho KPI review, không cho routing.
5. **acceptance giờ khớp target nhưng độc lập với hành vi decline thật của sim** — là override MOCK có chủ đích (sim under-decline), nhãn rõ.
6. Không đụng l1/ cũ + advisor core → 201 test cũ intact (204 = +3 PI-2b).

## Expansion checkpoint (T-039)
1. **Schema:** không đổi (profile express qua field driver_type/type/vehicle).
2. **Bài toán tối ưu:** car/premium data mở khả năng solver đa dịch vụ; nhưng scope hiện F0-F3 bike-first.
3. **Tính năng:** đa dạng archetype/kind → test personalization F1/F3 theo track thật hơn.

## Follow-up / defer phát sinh
- **Lớp thưởng tuần vào payout** (bike biên dưới) → nối S5 (PI-4), không phải PI-2b.
- **car-employee base salary** model → cần định nghĩa GSM (P1§4 câu hỏi).
- **Scale 90+ ngày** khi cần tập lớn (smoke 21 ngày đủ review).
- Zone enlargement DEFER (Cường) — future.
