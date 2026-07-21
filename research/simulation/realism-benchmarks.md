# Research — Realism benchmarks: đối chiếu sim với thực tế (T-024)

Ngày: 2026-07-21 · Nguồn: research đợt 5 · Phục vụ: chỉnh config sim + calibration T-021

## Phát hiện quan trọng nhất

1. **`order_expire_s: 90` là nguyên nhân chính thổi phồng unserved 34%.** Văn liệu dùng patience khách **~5 phút** trước khi hủy nếu chưa match (nguyên văn arXiv 2503.13200: khách hủy sau 5 phút chưa match, tài xế chờ điểm đón tối đa 10 phút). Sim đang giết đơn nhanh gấp ~3,3 lần thực tế.
2. **Unserved target 15–20% là ĐÚNG cho hệ cung cố định không surge** (natural experiment Uber NYE: khi mất cơ chế giá, completion sụp còn 15–25% — giống điều kiện sim; platform lớn đạt 3–10% là NHỜ surge + cung co giãn, không phải chuẩn cho sim này).
3. **Sim thiếu lớp thưởng trong payout**: thưởng tuần/mốc chiếm ~20–30% thu nhập thực; sim mới tính gross×share.

## Bảng đối chiếu → hành động

| Tham số sim | Benchmark + nguồn | Chỉnh |
| --- | --- | --- |
| expire 90s | patience ~5ph (arXiv 2503.13200); ~1ph match + chịu ETA ~7ph (MDPI 15(6):3243) | **Patience 2 tầng**: chờ match lognormal median 3ph/cap 10ph (per-order, exogenous); sau gán, hủy nếu pickup ETA >8–10ph (eta_max hiện có đã xử lý) |
| unserved 34% | NYC 2014 41%→2015 18%; Bắc Kinh 39,9% không trả lời (PMC5993247); DiDi +0,5–2% fulfillment = thành tựu | Target **15–20% toàn ngày** (peak 25–30%, off-peak <10%); sửa patience trước rồi mới kết luận thiếu cung |
| 15–16 cuốc FT | Sàn ĐBTN ~13–15/ngày; GrabBike FT 20–30 cuốc (danviet); repo 15–30 | Target **median 18–22**, p90 28–30 |
| payout FT 270–300k | Sàn ĐBTN 8h=320k, 10h=400k (VnExpress 11/2023); bike 9,2h→318k (Znews); guarantee 15tr/tháng ≈500–580k/ngày | Target **380–480k**; payout/cuốc ~18k OK (GrabBike 16–20k) → gap = thiếu cuốc + **thiếu lớp thưởng** → cộng day-bonus vào payout cuối ca (rule component) |
| share 75% | xanhsm.com hiện ghi 73%; repo timeline 70%(12/2025)→75%(03/2026) | Giữ 75% + version; ghi chú lệch 73% cần xác minh version |
| utilization chưa đo | ngành 30–60%, ~50% peak (dojobusiness); UberX +30% vs taxi (NBER w22083) | **Bắt buộc đo** occupied/online; target FT **45–55%**; guardrail <35% thừa cung, >65% thiếu cung |
| pickup ETA chưa báo | Lyft mean 3,08ph; Uber 2,6ph, hầu như <5ph; 90% <10ph | Đo; target **mean 3–5ph, p90 ≤8ph** |
| idle giữa cuốc | Austin mean 12,8ph (SD 14,5); Toronto <25ph đa số | Idle 10–15ph là tự nhiên; thêm **nghỉ trưa 45–90ph cho full-time** vào behavior |
| decline 2% | DiDi "seldom decline" khi auto-dispatch | Giữ 2–5%, OK |
| chờ pin max 61ph | thao tác <2ph; peak "chờ cả tiếng" (baoxaydung) | Không phi thực tế nhưng phải là đuôi hiếm: **median <5ph, p90 ≤15ph, p99 45–60ph chỉ giờ đỉnh**; kiểm bug hàng đợi khi cả 6 viên đang sạc |

## Kết luận demand model

1.200 đơn/50 tài xế = 24 đơn/tài xế — đúng trần dải full-time thực → demand khả thi vật lý, không cắt. Thứ tự chỉnh: (a) patience → (b) đo utilization/ETA → (c) nếu unserved vẫn >20% mới giảm demand về ~1.000–1.050 hoặc tăng 55–60 tài xế. Khi đạt 18–22 cuốc, payout tự lên ~350–420k; phần còn thiếu là lớp thưởng (thêm như rule).

(URL nguồn đầy đủ trong transcript research; các nguồn chính: arXiv 2503.13200, Hall-Kendrick-Nosko surge paper, PMC5993247, NBER w22083, Cramer&Krueger, báo VN kienthuc/danviet/genk/Znews/baoxaydung.)

## Phát hiện khi áp realism pass vào sim (chẩn đoán 2026-07-21)

Sau khi đổi patience 90s → 2 tầng (3–10ph) + cộng day-bonus, chạy lại: **unserved vẫn ~35% (không giảm)** → patience KHÔNG phải bottleneck như dự đoán. Chẩn đoán sâu lộ ra:

1. **Tài xế "full-time" chỉ online median 4.5h** (thiết kế 8–10h) → thiếu cung hiệu quả là nguyên nhân thật của unserved, không phải patience.
2. **Swap tắc nghiêm trọng**: 18/52 lần đổi pin chờ **cap 61 phút** (p90=61, median=0). Trạm 6 khe, 5 pin đầy ban đầu, sạc lại 105ph/viên; khi nhiều actor dồn → hết pin đầy → chờ. Actor mất 1h/lần swap → mất cung giờ cao điểm.
3. **Sạc cắm `home_charge_min: 210` (3.5h)** ăn hết nửa ca của đội sạc cắm (P1 + phần P3/P5). Thực tế: tài xế sạc cắm chỉ sạc 1 lần/ngày vào **trưa kết hợp nghỉ**, không phải mỗi lần SOC thấp giữa giờ cao điểm.
4. **`online_min` đo sai**: cộng `(now-last)` ở đầu vòng idle → lẫn cả thời gian đang serve trip/charge → utilization 72% là artifact (mẫu số thiếu). Cần tách `occupied/empty/idle/charge/rest` để utilization đúng.

**Hành động (áp trong lượt này):** (a) đo online/utilization đúng bằng tách các loại thời gian; (b) sạc cắm chỉ 1 lần/ngày quanh trưa (không sạc giữa peak); (c) swap: chọn trạm ít tắc + cap chờ hợp lý + đo p50/p90/p99. **Hạ unserved về 15–20% là gate calibration nhiều vòng (T-021)** — ghi lại phần chưa đạt, không ép trong 1 lượt.

## KẾT LUẬN CALIBRATION VÒNG 1 (2026-07-21) — quan trọng cho thiết kế advisor

Sau khi sửa bug accounting (time breakdown đúng) + bật demand-hint (actor có kinh nghiệm cá nhân), baseline B ổn định ở: **served ~66%, util FT ~38%, 16 cuốc/FT, payout ~300k, pickup ETA p90 ~6ph**.

**Chẩn đoán bằng sweep** (đã chạy, ghi lại để không lặp):
1. Mở bán kính dispatcher (ring 4→10, ETA 8→12): served **không đổi** (~65%) → KHÔNG phải thiếu tầm với dispatcher.
2. Giảm demand (1200→1000) hoặc tăng tài xế (50→60): served chỉ 68→73% nhưng **cuốc/util GIẢM mạnh** (16→11, 38→27%) → KHÔNG phải thiếu cung tổng.
3. Idle FT ~3.9h/ca **đồng thời** unserved 34% → **mismatch không gian–thời gian**: tài xế bản năng (home random + relocate yếu) đứng sai chỗ so với demand tập trung (bệnh viện/đại học/văn phòng).
4. Swap: 35% lần đổi pin chờ cap 60ph dù throughput tổng 11 trạm dư (~31 pin/h vs nhu cầu ~2.6/h) → **herding trạm**: actor chọn trạm gần nhất → dồn vài trạm.

**Quyết định thiết kế (đề xuất Cường xác nhận):** unserved ~34% + util ~38% + swap herding của **baseline B là ĐÚNG và cần thiết** — đây chính là **dư địa để advisor chứng minh giá trị**:
- Advisor timing/relocate (capacity-aware) → kéo tài xế tới demand cao đúng lúc → giảm unserved, tăng util.
- Advisor capacity-ledger đổi pin → phân tán trạm → giảm chờ herding.
→ **Target 15–20% unserved là mục tiêu cho ARM A (có advisor), KHÔNG phải arm B.** Nếu ép baseline B về 15–20% bằng vặn tham số thì triệt tiêu chính hiệu ứng cần đo (Δ A−B). Baseline B "chưa tối ưu" là feature, không phải bug.
- 16 cuốc/300k của B ở biên dưới dải thực (18–22/380–480k) — advisor kỳ vọng nâng lên giữa dải. Payout đã cộng day-bonus (rule component).

**Còn tinh chỉnh vòng sau (không blocker):** swap wait cap 60ph → cho actor rời trạm theo pin-availability (không chỉ queue_len); calibrate σ nhiễu demand-hint; nghỉ trưa cho full-time.
