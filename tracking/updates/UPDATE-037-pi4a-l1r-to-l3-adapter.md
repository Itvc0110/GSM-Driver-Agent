# UPDATE-037 — PI-4a: adapter L1R → L3 views (solver đọc field ĐO ĐƯỢC)

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường duyệt plan PI-4a; chốt (d)=GROSS)
- **Loại:** feature
- **TODO / User story liên quan:** Real-data PI-4a; US-F1-03/04, US-F3-01; T-039

## Tóm tắt

`src/gsm_core/features/from_l1r.py`: derive 3 L3 view (S1 `bonus_gap_input`, S2 `shift_plan_input`, S3 `session_summary_input`) **từ 13 bảng thật** thay vì recompute từ event sim. Nguyên tắc: field GSM **đo được** (`acceptance_rate`, `fulfillment_rate`, `online_time`, `total_fee`/`commission`) **ĐỌC THẲNG**; chỉ tính thứ bảng thật không có (`points_now` = trips × PolicyBundle). Chain end-to-end verified: bảng thật → view → **S1 solve** → SolverReport hợp schema, traceability=1.0. Suite **221 pass**.

## Chi tiết cập nhật

| View | Đọc thẳng (measured) | Vẫn phải tính | Ghi chú |
|---|---|---|---|
| `bonus_gap_input` (S1) | acceptance ← `statistic_daily.acceptance_rate`; completion ← `fulfillment_rate`; quỹ giờ ← `online_hours.online_time` | `points_now`, `historical_points_per_hour` | điểm KHÔNG có trong bảng thật |
| `session_summary_input` (S3) | `gross_vnd` ← `total_fee`; `driver_payout_vnd` ← `commission` (tách sẵn tại nguồn) | `day_state_end` | `estimated_net=None` (chưa đủ known cost — §5) |
| `shift_plan_input` (S2) | `demand_forecast` ← mật độ `trips` thật theo (giờ × H3) | `points_now` | `soc_pct=None` — 13 bảng KHÔNG có telemetry pin (TBC) |

- **Contract conformance**: phát hiện giả định sai khi test — `buckets_remaining` là **int** (số bucket), `demand_forecast` là `[{bucket, cell_cluster, expected_orders}]`; đã sửa đúng schema thay vì sửa schema.
- **S4 `allocation_input` KHÔNG remap** (có chủ đích): 13 bảng thật thiếu station/battery capacity → S4 giữ mock/sim (gap P5).
- **Đường L1 sim giữ nguyên** (`bonus_gap.py`…) → twin-world không gãy; 2 đường song song, hợp nhất sau.
- **(d) CHỐT GROSS**: ghi vào `policy-weekly-khoan-model.md` — khoán = doanh số (`total_fee`), nhãn ASSUMPTION, S5 phải expose `money_basis` param.

## Adversarial self-review / flaws found

1. **FIXED trong cycle — bịa số lạc quan**: khi không có dòng đo cho ngày hỏi (vd sáng sớm chưa có cuốc), adapter ban đầu trả `acceptance_rate = 1.0` **như thể đo được** → S1 có thể kết luận "đủ eligibility" sai. **Fix**: carry-forward giá trị ĐO gần nhất + hạ `source = ESTIMATED` (không giả vờ measured). Có test riêng.
2. **ASSUMPTION trần ca 12h** khi thiếu declared window (bảng thật không có) — đã ghi nhãn trong code.
3. **demand_forecast chỉ đếm đơn ĐÃ phục vụ** (không có unserved trong `trips`) → thiên thấp; ghi rõ docstring, nhãn ESTIMATED-from-REAL.
4. **Hiệu năng**: `_stat_row`/`_income_row` quét tuyến tính mỗi lần gọi — chấp nhận ở quy mô hiện tại (test 18s), cần index khi PI-3/PI-5 scale. Follow-up.
5. Không đụng đường sim → 208 test cũ intact (221 = +12 mới +1 đã có).

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `src/gsm_core/features/from_l1r.py` | tạo (3 derivation + provenance) |
| `tests/test_features_from_l1r.py` | tạo (12 test end-to-end) |
| `specs/policy-weekly-khoan-model.md` | sửa (chốt (d)=GROSS + `money_basis` param) |
| `tracking/{TODO, updates/UPDATE-037}` | governance |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| View hợp schema + chain S1 OK | `OBSERVED-CODE` | 12 test, suite 221 | Cao | — |
| acceptance/payout đọc thẳng đúng field | `OBSERVED-CODE` | test đối chiếu bằng giá trị gốc | Cao | — |
| khoán = GROSS | `ASSUMPTION` (Cường chốt) | văn bản "truy thu 20% phần doanh số" | TB | S5 numbers lệch ~25% → có `money_basis` param |
| trần ca 12h | `ASSUMPTION` | không có declared window | TB | hours_budget lệch |
| demand_forecast (served-only) | `ESTIMATED` | trips thật | TB | thiên thấp giờ cao điểm |

## Kiểm chứng

`pytest tests/test_features_from_l1r.py` **12 pass** (schema-valid 3 view; measured-vs-source đối chiếu; chain S1→SolverReport traceability=1.0; unknown driver không crash; ESTIMATED labeling). Full suite **221 pass**. **CHƯA kiểm chứng:** chain S2/S3 solver (chỉ chain S1 trong cycle này); S4 chưa remap (thiếu data trạm); chưa chạy trên data thật (chưa có BQ access).

### Seeds và scenarios
| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| generate_realdata(8 ngày, seed 300) → 3 view → S1 | 12 pass | S2/S3 chain, data thật |

## Visual verification
- **Status:** `NOT_APPLICABLE` — feature/adapter layer, không UI.

## Expansion checkpoint (T-039)
1. **Schema:** không đổi (dùng đúng L3 contract sẵn có).
2. **Bài toán tối ưu:** đường vào S5 (weekly khoán, đã chốt GROSS) + S6 mission-knapsack giờ rõ — cycle kế.
3. **Tính năng:** `session_summary_input.inferred_activities` còn rỗng → PI-5 điền idle từ `hex_tracking` (UC5).

## Follow-up / defer phát sinh
- **PI-4b**: S5 WeeklyKhoanFeasibility (`money_basis=gross`) + S6 MissionKnapsack.
- **PI-5**: `inferred_activities` từ hex_tracking (UC5), penalty-explain (UC6), anomaly-alert (UC7).
- Index hoá lookup trong `from_l1r` khi scale (perf).
- Chain test S2/S3 với solver tương ứng.
