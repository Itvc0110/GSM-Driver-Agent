# UPDATE-039 — Mock khớp CHÍNH XÁC schema GSM (tên bảng thật) + mở rộng 90 ngày

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường: "check lại schema có đúng như tôi cung cấp không? số cột, bảng? chất lượng? extend data")
- **Loại:** fix + data
- **TODO / User story liên quan:** Real-data PI-2b/PI-1; gate cho PI-5

## Tóm tắt

Audit mock vs metadata GSM Cường cung cấp → phát hiện **2 sai lệch thật**: (1) **8/13 bảng bị tôi đổi tên** (rút gọn) so tên thật; (2) `public_mission_earn_history` **thiếu 3 cột** audit (`created_at/updated_at/deleted_at`, 18/21) + sai thứ tự. Đã sửa cả hai, thêm **test GATE** chống trôi schema, và **mở rộng data 21→90 ngày** (1.29M record). Audit lại: **13/13 bảng, 0 vấn đề cột**. Suite **285 pass**.

## Kết quả audit (trước → sau)

| Hạng mục | Trước | Sau |
|---|---|---|
| Bảng có đúng tên thật | 5/13 | **13/13** |
| Cột khớp spec (tên+số+thứ tự) | 12/13 (1 thiếu 3 cột) | **13/13 KHỚP HOÀN TOÀN** |
| Quy mô data | 21 ngày, 302k record | **90 ngày, 1.29M record** |
| File rác tên cũ | — | dọn 16 file (8 parquet + 8 csv) |

**Đổi tên (8):** `mission_catalog`→`public_mission`, `mission_earn_history`→`public_mission_earn_history`, `user_mission_progress`→`public_user_mission_progress`, `driver_hex_tracking`→`public_driver_hex_tracking`, `driver_online_hours`→`driver_online_hours_sap_id`, `kpi_weekly_calculator`→`kpi_driver_platform_calculator_gbq`, `driver_penalization`→`driver_penalization_ATA`, `fraud_flag`→`public_frauds`.

**4 bảng ENGINEER** (spec chưa có cột — giữ nguyên, nhãn TBC): `trips` (19), `driver_penalization_ATA` (11), `public_frauds` (10), `public_user_mission_progress` (12).

**2 cột META của ta** (`schema_version`, `source`) là **chủ ý** — CLAUDE.md §5 bắt buộc gắn nhãn nguồn mock; audit tách riêng, không tính là sai spec. Khi swap sang BigQuery thật, DataSource (PI-3) sẽ thêm/bỏ 2 cột này.

## Chi tiết cập nhật

- `src/gsm_core/mockgen/gsm_spec.py` (**mới**): SPEC metadata GSM = **MỘT nguồn sự thật**, dùng chung bởi script audit + test gate. Sửa ở đây khi GSM cập nhật.
- `scripts/audit_schema_vs_spec.py` (**mới**): in bảng đối chiếu tên/số cột/thứ tự.
- `tests/test_schema_matches_gsm_spec.py` (**mới, GATE**): 11 test — entity đúng tên thật, cột khớp **đúng thứ tự**, nhãn nguồn hợp lệ. Từ nay schema không thể trôi âm thầm.
- Rename 8 entity xuyên suốt: schema JSON (regen), registry, generator, adapter `from_l1r`, solver `mission_knapsack` (source label), tests, script R2.
- Fix `public_mission_earn_history`: thêm `created_at/updated_at/deleted_at` + xếp **đúng thứ tự spec**.
- Mở rộng data: **90 ngày × 110 profile** (50 bike + 20 rto + 15 car + 15 car-emp + 10 premium) → 9.259 driver-day, 145k trips, 1.09M hex, 2.612 mission-earn, 1.532 tuần KPI.
- Dọn 16 file rác tên cũ trong `data/mock/realdata-v1{,/csv}`.

## Adversarial self-review / flaws found

1. **Tự ý rút gọn tên bảng** — tôi đặt tên "đẹp" thay vì tên thật; khi swap BigQuery sẽ lệch mapping. Đã sửa + gate test khoá lại.
2. **Rename sót file**: `mission_knapsack.py` không nằm trong danh sách rename → `source="mission_catalog"` cũ vẫn tồn tại; **full suite bắt được** (test đỏ), đã fix cả `verify_realdata_stats.py`.
3. **File rác**: parquet/CSV tên cũ còn lại sau rename → dễ gây nhầm khi Cường review; đã dọn, xác nhận đúng 13+13.
4. **Cột meta**: chấp nhận lệch 2 cột so bảng thật (có chủ ý §5) — ghi rõ để PI-3 xử lý khi swap.
5. Chưa kiểm: chất lượng thống kê trên tập 90 ngày (R2 chạy trên seed riêng, chưa chạy lại sau extend) — follow-up.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `src/gsm_core/mockgen/gsm_spec.py`, `scripts/audit_schema_vs_spec.py`, `tests/test_schema_matches_gsm_spec.py` | tạo |
| `schemas/l1r/*.schema.json` (13) | regen với tên thật |
| `scripts/build_l1r_schemas.py`, `src/gsm_core/schema_registry.py`, `src/gsm_core/mockgen/realdata.py`, `src/gsm_core/features/from_l1r.py`, `src/gsm_core/solvers/mission_knapsack.py`, `scripts/verify_realdata_stats.py` | sửa (rename + fix cột) |
| `tests/{test_l1r_schemas,test_realdata_gen,test_mission_knapsack,test_schemas}.py` | sửa (tên mới) |
| `data/mock/realdata-v1/**` | regen 90 ngày + dọn rác (gitignored) |

## Kiểm chứng

`scripts/audit_schema_vs_spec.py`: **13/13 bảng, 0 vấn đề cột**. `tests/test_schema_matches_gsm_spec.py` 11 pass (4 skip = 4 bảng ENGINEER không có spec cột). Full suite **285 pass**. CSV export 13/13 cho Cường review tay.

**CHƯA kiểm chứng:** R2 statistical chưa chạy lại trên tập 90 ngày (số liệu R2 hiện từ seed 30×1 ngày — vẫn hợp lệ về phương pháp); chất lượng nội dung 4 bảng ENGINEER vẫn chờ GSM cấp cột thật.

## Visual verification
- **Status:** `NOT_APPLICABLE` — data/schema. CSV tại `data/mock/realdata-v1/csv/` (13 file) cho Cường review.

## Expansion checkpoint (T-039)
1. **Schema:** khớp 100% spec hiện có; còn 4 bảng chờ GSM cấp cột thật (D-POL-05).
2. **Bài toán tối ưu:** không đổi (S1-S6 chạy trên tên mới).
3. **Tính năng:** data 90 ngày đủ dài cho phân tích tuần/tháng (KPI tuần 1.532 dòng) → nuôi S5 + F3 pattern tốt hơn.

## Follow-up / defer phát sinh
- Chạy lại R2 trên tập 90 ngày (xác nhận phân phối không đổi khi scale).
- PI-3 DataSource: xử lý 2 cột meta khi swap BigQuery ↔ mock.
- Xin GSM cột thật cho 4 bảng ENGINEER (D-POL-05).
