# UPDATE-036 — Audit PI-2b: 5 flaw phát hiện & fix (có regression + red-green proof)

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường: "recheck the latest works, find flaws, update/fix")
- **Loại:** fix
- **TODO / User story liên quan:** Real-data PI-2b (UPDATE-035)

## Tóm tắt

Audit thực nghiệm data PI-2b vừa commit (83bdb05) → tìm **5 flaw thật**, trong đó **1 crash phụ thuộc seed** và **1 impossible state** (203 driver-day có cuốc khi online=0), và **1 verdict R2 sai do trộn population** (car thổi median payout, che việc bike vẫn biên dưới). Fix cả 5 + regression test (red-green proof trên data cũ). Suite **208 pass**.

## 5 flaw (reproduce → root cause → fix → test)

| # | Flaw | Root cause | Bằng chứng | Fix |
|---|---|---|---|---|
| **01** | **R2 verdict SAI** — gộp car+bike so benchmark **BIKE** | `realism-benchmarks.md` là bike HN; car fare cao 3-5× → thổi median payout | pooled 270k vs **bike 229k** / car 539k → "PASS" giả | `verify_realdata_stats.py` **tách population**; car = OBSERVE-ONLY |
| **02** | **Impossible state**: có cuốc khi `online_time=0` | `online_hours()` chỉ cộng khi ghép đủ cặp go_online→go_offline; sim có ca không đóng | **203 driver-day** (vd d-0: 13 cuốc, 0h) | sàn `online ≥ trip_hours/0.55` (util ≤55%, realism-benchmarks) |
| **03** | Cuốc tràn nửa đêm (latent, seed-dependent) | `rule_based_trips` cho phép start 22:59 + duration 67ph → complete sang ngày sau → phá bất biến R3 | max complete 23h, max dur 4044s | dịch cuốc sớm lại khi tràn → complete luôn trong ngày |
| **04** | Field **degenerate** (0 thông tin) | `total_core_order = completed`, `total_stoppoints = completed` với MỌI record | `==` 100% | core = 80-100% completed (rng); stoppoints = cuốc + **điểm dừng chờ (idle)** |
| **05** | **CRASH phụ thuộc seed** khi ghi parquet | `pl.DataFrame()` chỉ suy kiểu **100 dòng đầu**; cột thưa (`campaign_id`/`target_hex` ~5%) → Null dtype → ComputeError khi gặp str dòng sau | seed 214 crash: "could not append value 'repo-01'" | `write_table_parquet()` dùng `infer_schema_length=None`; fix cả `mockgen/generate.py` |

**Red-green proof** (chạy invariant mới trên data CŨ trước fix): BUG-02 → **203** vi phạm; BUG-04 → degenerate `True`/`True`; BUG-05 → seed 214 crash. Sau fix: 0 / False / chạy OK.

## ⚠ ĐÍNH CHÍNH số liệu đã báo cáo (UPDATE-035)

UPDATE-035 báo "payout median 273k, p90 954k — cải thiện lớn so 195k". **SAI do BUG-01** (trộn car vào). Số ĐÚNG sau khi tách:

| | trước PI-2b | sau PI-2b (bike thật) |
|---|---|---|
| payout/ngày bike | ~195k | **~221k** (median) |
| (số đã báo nhầm) | — | ~273k = pooled có car |

⇒ Bike payout chỉ cải thiện **nhẹ**; vẫn **biên dưới** so thực 380-480k vì **thiếu lớp thưởng tuần** (thuộc S5/PI-4, không phải generator). Car (median 594k) là observe-only.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `src/gsm_core/mockgen/realdata.py` | sửa (fix 02/03/04/05 + `write_table_parquet`, `_trip_hours`) |
| `src/gsm_core/mockgen/generate.py` | sửa (fix 05 — cùng fragility) |
| `scripts/verify_realdata_stats.py` | sửa (fix 01 — tách bike/car) |
| `tests/test_realdata_gen.py` | sửa (+5 regression test) |
| `research/experiments/mockgen-realdata/ROUND-2-stats-report.md` | regen (segmented) |
| `data/mock/realdata-v1/**` | regen + CSV (gitignored) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| 5 flaw đã fix, có regression | `OBSERVED-CODE` | 17 test file + red-green proof | Cao | — |
| bike payout thật ~221k (biên dưới) | `OBSERVED-CODE` | ROUND-2 segmented | Cao | — |
| sàn online = trip_hours/0.55 | `PROXY` | realism-benchmarks util FT 45-55% | TB | online hơi cao ở đuôi (p90 13.2h > target 12) |
| stoppoints = cuốc + idle stop | `MOCK/ASSUMPTION` | định nghĩa GSM chưa rõ (P1§4) | TB | lệch định nghĩa thật |

## Kiểm chứng

`pytest tests/test_realdata_gen.py` **17 pass**; full suite **208 pass**. Seed 214 (crash cũ) chạy OK. R2 30 seeds segmented: bike 2021 dd / car 1052 dd, **bike 6/6 in-range**. Regen 21 ngày + CSV export OK.

**CHƯA kiểm chứng / caveat còn lại:** (a) **online p90 13.19h > target 12h** — sàn util có thể thổi đuôi (chấp nhận tạm, ghi nhận); (b) bike payout vẫn biên dưới tới khi có lớp thưởng tuần (S5); (c) định nghĩa `stoppoints`/`core_order` thật của GSM chưa xác nhận; (d) car income là PROXY (chưa model lương cứng employee).

### Seeds và scenarios
| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| test_realdata_gen (8 ngày) | 17 pass | — |
| seed 214 (crash cũ) | OK | — |
| R2 30 seeds segmented | bike 6/6, car observe | benchmark car |

## Visual verification
- **Status:** `NOT_APPLICABLE` — data tooling. CSV regen cho Cường review (`data/mock/realdata-v1/csv/`).

## Adversarial self-review / flaws found
1. **Verdict "PASS" từng che lỗi** (BUG-01) — bài học: metric gộp population khác nhau là bẫy; giờ luôn segment.
2. **Test xanh không đảm bảo đúng** — 12 test PI-2b xanh nhưng vẫn có 203 impossible state + crash seed; audit thực nghiệm mới lộ. Đã bổ sung invariant.
3. **Fix BUG-02 có tác dụng phụ**: online p90 tăng lên 13.2h (>12) — trade-off giữa "không có cuốc khi offline" và đuôi online; chọn ưu tiên loại impossible state, ghi nhận đuôi.
4. **BUG-05 tiềm ẩn ở generator cũ** (`generate.py`) cũng đã fix — nếu không, mock v1 có thể crash ngẫu nhiên sau này.
5. Còn mở: định nghĩa GSM cho stoppoints/core_order (P1§4); lớp thưởng tuần (S5).

## Expansion checkpoint (T-039)
1. **Schema:** không đổi.
2. **Bài toán tối ưu:** không đổi (S5 vẫn cần để đóng gap payout).
3. **Tính năng:** stoppoints giờ có tín hiệu idle thật → nuôi được UC5 idle-reduction (trước đây degenerate = vô dụng).

## Follow-up / defer phát sinh
- Lớp thưởng tuần vào payout → **S5 (PI-4)**.
- Online-hour đuôi p90 13.2h → tinh chỉnh khi có data thật online.
- Định nghĩa stoppoints/core_order → câu hỏi GSM (P1§4).
