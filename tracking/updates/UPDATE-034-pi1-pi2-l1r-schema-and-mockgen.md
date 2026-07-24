# UPDATE-034 — PI-1 (13 schema l1r) + PI-2 (mockgen realdata) IMPLEMENTED

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường: "process to go on; engineer uncertain data yourself; minimize keys")
- **Loại:** feature (schema + mockgen)
- **TODO / User story liên quan:** Real-data PI-1/PI-2 (UPDATE-033); T-038; D-POL-05

## Tóm tắt

Implement 2 phase đầu roadmap real-data: **PI-1** = 13 schema `l1r/*` (mirror bảng thật gsm-data-prod, 5 bảng thiếu cột được ENGINEER, nhãn TBC); **PI-2** = generator `mockgen/realdata.py` sinh 13 bảng bằng **sim→aggregate** (nhất quán event nền). Confirm **plan gen data (P3) done + chạy được**. External API = **0 call** (mock self-contained — minimize keys theo yêu cầu Cường). Full suite **201 pass** (162→+30 l1r +9 realdata).

## Chi tiết cập nhật

- **PI-1**: `scripts/build_l1r_schemas.py` emit 13 JSON schema vào `schemas/l1r/`. 8 bảng theo field thật; **5 bảng ENGINEER** (trips, driver_penalization, fraud_flag, user_mission_progress + hex/mission) — cột tự thiết kế grounded, nhãn `x-availability: TBC-với-GSM`. PII field = **optional** (record sau khi tool scrub bỏ PII vẫn validate); `x-pii-columns` khai để tool P4 drop/hash. Registry `schema_registry.py` +layer `l1r` (+`L1R_ENTITIES`).
- **PI-2**: `mockgen/realdata.py` — `generate_realdata(days, seed_base, out)` chạy `generate_day` (sim event) mỗi ngày → `aggregate_days` (KPI daily/weekly + trips reshape + hex dwell) + `build_weekly_and_missions` (weekly rollup + mission catalog/earn/progress + penalization/fraud rule-based). Aggregate nhất quán event nền: `income.total_fee=Σtrips.gross`, `commission=round(fee×share)`, `normal+rush=total`, `completed=orders=#trips`, `weekly=Σdaily`. Mọi record MOCK/INFERRED, deterministic seed.
- **Smoke**: 14 ngày × 50 driver → 700 daily/bảng, 150 weekly, 10.3k trips, 170k hex, 177 mission-earn, 16 penalization, 9 fraud. 13/13 bảng.
- **Uncertain data engineered creatively** (Cường ủy quyền): trips=dispatch shape từ trip_record; penalization={type,amount,reason,status,ata_code}; fraud={type,severity,confidence,status} nhãn INFERRED không kết tội; user_mission_progress={progress,target,state}.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `scripts/build_l1r_schemas.py` | tạo (emit 13 schema) |
| `schemas/l1r/*.schema.json` (13) | tạo |
| `src/gsm_core/schema_registry.py` | sửa (+layer l1r, L1R_ENTITIES) |
| `src/gsm_core/mockgen/realdata.py` | tạo (generator) |
| `tests/test_l1r_schemas.py` (30) + `tests/test_realdata_gen.py` (9) | tạo |
| `tests/test_schemas.py` | sửa (EXPECTED_L1R) |
| `data/mock/realdata-v1/*.parquet` | tạo (gitignored — regen từ seed) |
| `tracking/{TODO,DEFERRED,updates}` | governance |

## Docs đã cập nhật kèm theo
TODO: PI-1/PI-2 → DONE. `specs/real-data/00-index.md`,`03-mockgen` status→implemented. DEFERRED: 5 bảng engineered → khi GSM cho cột thật thì đối chiếu (D-POL-05). SCOPE/USER_STORIES: không đổi.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| 13 bảng l1r validate + 201 suite pass | `OBSERVED-CODE` | pytest 201 pass | Cao | — |
| Aggregate nhất quán event nền | `OBSERVED-CODE` | R3 test (income↔rush, commission, completed=orders) | Cao | mock lệch |
| Generator deterministic | `OBSERVED-CODE` | seed-based | Cao | — |
| 5 bảng cột ENGINEER | `TBC-với-GSM` | tự thiết kế grounded | TB | đối chiếu khi GSM cho cột thật |
| stoppoints=proxy #trips; cancelled=accepted−completed | `ASSUMPTION` (sim thiếu cancel) | mockgen | TB | KPI cancel/stop lệch định nghĩa GSM |
| share=0.75 | `PROXY` | policy hiện hành | Cao | commission lệch nếu track khác |

## Kiểm chứng

`pytest tests/test_l1r_schemas.py` 30 pass; `tests/test_realdata_gen.py` 9 pass (gen 8 ngày + R1 schema/FK + R3 cross-table + R4 bounds); full suite **201 pass**. Smoke 14 ngày sinh 13 bảng thật shape. Parquet gitignored (regen từ seed).

**R2 statistical (DONE — `scripts/verify_realdata_stats.py`, 30 seeds/1500 driver-days → `research/experiments/mockgen-realdata/ROUND-2-stats-report.md`):** 6/6 metric median trong dải benchmark. **Caveat trung thực (không claim "realism-proven tuyệt đối"):** (a) payout median ~195k = **biên DƯỚI** (sim thiếu lớp thưởng tuần — cộng ở rule/S5, không phải bug mock); (b) acceptance median **1.00 = biên TRÊN** (sim under-produce decline → tỷ lệ nhận lạc quan hơn thực 0.74-0.97) → cần thêm decline realistic hoặc data thật; (c) cuốc/ngày median 14 ~ biên dưới. Aggregate consistency R1/R3/R4 vẫn chặt.

**CHƯA kiểm chứng:** semantics GSM cho 5 bảng + số target KPI (TBC); DataSource tool (PI-3, chưa làm); solver remap (PI-4); acceptance realism (caveat b).

### Seeds và scenarios
| Run | Seed | Kết quả | Chưa kiểm chứng |
| --- | --- | --- | --- |
| test_realdata_gen (8 ngày) | 100 | 13 bảng R1/R3/R4 pass | R2 30-seed stats |
| smoke 14 ngày | 100 | counts hợp lý | vs benchmark tuyệt đối |

## Visual verification
- **Status:** `NOT_APPLICABLE` — data/schema tooling (không UI). Record counts in ra cho Cường xem.

## Adversarial self-review / flaws found
1. **Cancelled proxy** = accepted−completed (sim không có cancel event thật) → cancellation_rate là ước lượng, nhãn MOCK; đối chiếu khi có data thật.
2. **stoppoints=#trips** proxy (chưa dùng gps dwell cluster đầy đủ) → định nghĩa GSM có thể khác (dừng đón/trả vs chờ) → TBC, mock 1 biến thể.
3. **R2 chưa chạy**: mới R1/R3/R4; statistical vs benchmark (≥30 seeds) để phase verify riêng (P3 §3) — ghi UNVERIFIED, không claim "realistic đã chứng minh".
4. **hex_tracking 170k records/14 ngày** — nặng; per-ping dwell → có thể cần bucket thô hơn (COARSE) khi scale; ghi nhận.
5. **Engineered cột** có thể lệch schema thật GSM → nhãn TBC + build script tái sinh dễ khi GSM cho cột.
6. **share cố định 0.75** — track platform; RTO/khác cần policy bundle đúng track (weekly-khoan spec).
7. Không đụng core cũ (l1/ giữ nguyên) → 162 test cũ intact; l1r song song.

## Expansion checkpoint (T-039)
1. **Schema**: 13 l1r xong; tiếp theo L2 recompute (DriverWeekState) + L3 view mới cho S5/S6 (PI-4).
2. **Bài toán tối ưu**: dữ liệu mission (catalog+progress+earn) sẵn cho **S6 mission-knapsack**; weekly (kpi_calculator) cho **S5** — implement PI-4.
3. **Tính năng**: rating KPI (total_rating/5star) đã sinh → F3 chất lượng; penalization/fraud sinh → UC6/UC7 (PI-5).

## Follow-up / defer phát sinh
- **PI-3** DataSource tool (read-only+PII) — next; **PI-4** solver remap + S5/S6; **PI-5** UC5-8 features.
- **R2 DONE** (6/6 in-range, 2 caveat biên): cải thiện realism khi có data thật; acceptance sim quá cao (thêm decline) — theo dõi.
- **Cần GSM**: cột thật 5 bảng + số target KPI tuần + semantics (P1§4) → đối chiếu engineered.
- Cần Cường chốt (khi tới phase): BQ auth/env (PI-3), external key (PI-6) — chưa đụng.
