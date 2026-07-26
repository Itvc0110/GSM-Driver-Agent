# ROUND 2 — Statistical realism (mock l1r vs benchmark)

Seeds: 30 (base 200). driver-days: bike=3232, car=1059. Nguồn benchmark: `research/simulation/realism-benchmarks.md`.

> **TÁCH POPULATION (fix BUG-PI2b-01):** benchmark là của **BIKE Hà Nội**. Gộp car/premium (fare cao 3-5×) sẽ thổi median payout → verdict sai. **Car = OBSERVE-ONLY** (chưa có benchmark VN cho car trong research).

> Gap sim đã biết (T-021) được LABEL, không hard-fail — mock kế thừa sim calibration.


## BIKE (vs benchmark)

| metric | median | p10 | p90 | target | verdict | ghi chú |
|---|---|---|---|---|---|---|
| cuốc/tài xế/ngày | 10.00 | 5.00 | 18.00 | 10–30 | PASS | sim baseline ~16 (biên dưới); thực FT median 18-22 |
| payout(commission)/ngày VND | 192,039 | 105,943 | 332,518 | 150000–550000 | PASS | sim ~300k (thiếu lớp thưởng); thực 380-480k |
| giờ online/ngày | 8.73 | 5.01 | 11.93 | 2–12 | PASS | sim FT median ~4.5h (T-021 gap; thiết kế 8-10h) |
| tỷ lệ nhận | 0.90 | 0.74 | 1.00 | 0.6–1.0 | PASS | eligibility thưởng ≥0.85; archetype 0.74-0.97 |
| % cuốc khung rush | 0.38 | 0.14 | 0.67 | 0.1–0.7 | PASS | 2 đỉnh 6-8h,16-18h |
| % cuốc 5 sao | 0.79 | 0.56 | 1.00 | 0.5–1.0 | PASS | mock N(0.78) |

## CAR (OBSERVE-ONLY)

| metric | median | p10 | p90 | target | verdict | ghi chú |
|---|---|---|---|---|---|---|
| cuốc/tài xế/ngày | 16.00 | 9.00 | 25.00 | — | OBSERVE | car — không dùng benchmark bike |
| payout(commission)/ngày VND | 576,922 | 199,961 | 1,558,992 | — | OBSERVE | car — không dùng benchmark bike |
| giờ online/ngày | 10.43 | 6.21 | 16.00 | — | OBSERVE | car — không dùng benchmark bike |
| tỷ lệ nhận | 0.88 | 0.75 | 1.00 | — | OBSERVE | car — không dùng benchmark bike |
| % cuốc khung rush | 0.47 | 0.31 | 0.65 | — | OBSERVE | car — không dùng benchmark bike |
| % cuốc 5 sao | 0.78 | 0.67 | 0.89 | — | OBSERVE | car — không dùng benchmark bike |

**Tổng (BIKE, có benchmark):** 6/6 PASS, 0 GAP-T021 (labeled). GAP = sim baseline biên dưới (cuốc/payout/online) — dư địa advisor + **thiếu lớp thưởng tuần** (sẽ cộng ở S5/rule), không phải bug mock. Aggregate consistency pass R1/R3/R4 (`test_realdata_gen`).