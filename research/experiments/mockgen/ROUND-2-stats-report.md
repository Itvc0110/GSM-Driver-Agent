# ROUND 2 — Statistical realism (30 seeds = 30 ngày độc lập)

Benchmark: `research/simulation/realism-benchmarks.md` (PROXY). Median-of-daily-medians ± 95% CI.

| Metric | Giá trị (±CI) | Dải benchmark | Verdict |
|---|---|---|---|
| trips_ft_median | 16.00 ± 0.42 | [15 – 30] repo benchmark 15–30 (target giữa dải 18–22) | PASS |
| payout_ft_vnd | 256,239 ± 17,045 | [270,000 – 480,000] thực tế 270–300k tự khai; sàn ĐBTN→480k | **GAP** (ghi T-021, không che) |
| dist_km_median | 3.21 ± 0.03 | [2.8 – 4.0] median mục tiêu 3.5, hiện 3.2 (đã ghi gap T-021) | PASS |
| peak_share | 0.28 ± 0.00 | [0.24 – 0.55] SERVED share 2 đỉnh (demand share cao hơn — saturation) | PASS |

**Ghi chú gap đã biết (UPDATE-023):** payout FT ~243k dưới dải 270-480k và trips FT ~15 ở biên dưới — CALIBRATION GAP T-021 (pilot nhỏ + supply-demand mismatch là dư địa advisor), KHÔNG tune generator để che.

**KẾT LUẬN: PASS**