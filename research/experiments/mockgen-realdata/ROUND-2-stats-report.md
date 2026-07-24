# ROUND 2 — Statistical realism (mock l1r vs benchmark)

Seeds: 30 (base 200), driver-days: 3083. Nguồn benchmark: `research/simulation/realism-benchmarks.md`.

> Gap sim đã biết (T-021) được LABEL, không hard-fail — mock kế thừa sim calibration.

| metric | median | p10 | p90 | target | verdict | ghi chú |
|---|---|---|---|---|---|---|
| cuốc/tài xế/ngày | 15.00 | 9.00 | 24.00 | 10–30 | PASS | sim baseline ~16 (biên dưới); thực FT median 18-22 |
| payout(commission)/ngày VND | 273,458 | 131,478 | 954,633 | 150000–550000 | PASS | sim ~300k (thiếu lớp thưởng); thực 380-480k |
| giờ online/ngày | 8.57 | 2.58 | 11.10 | 2–12 | PASS | sim FT median ~4.5h (T-021 gap; thiết kế 8-10h) |
| tỷ lệ nhận | 0.88 | 0.75 | 1.00 | 0.6–1.0 | PASS | eligibility thưởng ≥0.85; archetype 0.74-0.97 |
| % cuốc khung rush | 0.41 | 0.22 | 0.62 | 0.1–0.7 | PASS | 2 đỉnh 6-8h,16-18h |
| % cuốc 5 sao | 0.78 | 0.67 | 0.89 | 0.5–1.0 | PASS | mock N(0.78) |

**Tổng:** 6/6 PASS, 0 GAP-T021 (labeled). GAP = sim baseline biên dưới (cuốc/payout/online) — dư địa advisor + thiếu lớp thưởng tuần, không phải bug mock. Aggregate consistency đã pass R1/R3/R4 (test_realdata_gen).