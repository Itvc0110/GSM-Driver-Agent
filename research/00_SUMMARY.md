# Research Summary — Đợt 1 + Đợt 2 + Đợt 3 (simulation)

Ngày cập nhật: 2026-07-21 · Files chi tiết: [income structure](economics/income-structure.md) · [bonus/policy](policy/bonus-programs.md) · [pain points](community/pain-points.md) · [community insights](community/community-insights.md) · [order distribution](market/order-distribution.md) · **simulation:** [tooling](simulation/tooling.md) · [evaluation methodology](simulation/evaluation-methodology.md) · [world parameters](simulation/world-parameters.md) (+ đợt 4 đang chạy: action space, pilot 1 quận, timestep).
Phương pháp: web research song song + đối chiếu chéo; claim trung tâm ĐBTN đã xác minh trực tiếp trên official page. Mỗi file ghi nguồn/ngày/reliability; số community không được nâng thành policy/financial fact.

## 10 điều quan trọng nhất

1. **Công thức thu nhập Bike được truyền thông official:** revenue share + thưởng tuần + thưởng khác. Hệ thống phải tách `gross revenue`, `driver payout` và `estimated net income`; policy/track quyết định cách tính.
2. **Policy thay đổi theo version:** timeline revenue share đã thấy 91% (11/2024, HCM) → 70% (12/2025) → tới 75% (02/03/2026). Không có một tỷ lệ vĩnh viễn cho mọi track/market.
3. **ĐBTN 3 tháng đầu** (policy từ 30/03/2026): HN/HCM có mức/điều kiện riêng; chỉ áp dụng khi map đúng cohort/track/effective date, không dùng như default universal.
4. **Ngưỡng nhận/hoàn thành và bảng điểm cũng versioned:** có bản HN 12/2025 yêu cầu 85%/85%; các threshold cũ 70%/50% là facts lịch sử có ngày, không hard-code cho hiện tại.
5. **Ba track kinh tế khác nhau:** xe cá nhân Platform, thuê/RTO, employee Car. Không trộn benefit/revenue share/chi phí giữa track.
6. **Thu nhập tự khai tương quan với giờ chạy**, nhưng các nguồn không nhất quán gross/payout/net; chỉ dùng làm calibration range, không làm guarantee.
7. **Pain point lặp lại nhất:** sạc/đổi pin mất thời gian; pattern sáng chạy → trưa sạc/nghỉ → chiều chạy lặp ở nhiều nguồn.
8. **Mock demand proxy:** anchor giờ cao điểm VN + proxy quốc tế cho hình dạng; không đại diện matching/dispatch hoặc số đơn chắc chắn đến từng tài xế.
9. **Nguồn cộng đồng có giá trị định tính** (mẹo pin, dead hours, điểm quá tải) nhưng phải qua source tier/freshness/PII/cross-check/human review; không cấp policy/số tài chính.
10. **Gap còn lại:** policy Bike thâm niên/Loyalty, % chia chi tiết theo khung giờ hiện hành, dữ liệu GSM theo giờ/khu vực, nội dung group FB sau login. Quyết định hiện hành là không OCR/nhập tay ảnh; không tìm được thì mock có assumption rõ.

## Đợt 3 (2026-07-21) — Simulation & evaluation (tóm tắt)

11. **Twin-world cùng seed là phương pháp chuẩn** (Common Random Numbers/paired-seed, giảm >10× số run; Lyft/DiDi cũng dùng simulator counterfactual); driver-level A/B thực địa sai vì interference — sim né được. Có **arm C placebo** (Cường approve) để tách giá trị "lời khuyên bất kỳ" khỏi "lời khuyên thông minh": hiệu quả thật = Δ(A−C).
12. **Adherence đo bằng twin-diff**: 5 nhãn Explicit/Coincident/Partial/Ignore/Unseen; nhìn twin ở arm B để loại "đằng nào cũng làm" (coincident) khỏi công của advisor — giải đúng bài toán "tài xế giàu kinh nghiệm tự làm đúng".
13. **Stack sim đã chốt**: SimPy + h3-py (res 8, pilot có thể res 9) + parquet/DuckDB + Streamlit/Plotly + kepler.gl replay; không cần API key bắt buộc (Mapbox optional).
14. **Thế giới HN có số thật**: 144 tủ đổi pin VinFast từ OSM (capacity=6, đổi ~90s, sạc lại 1.5–2h/viên); tốc độ bike 17/25/30 km/h theo giờ; cuốc lognormal ~3.5km; pin swap ~55–70km/pack; dispatcher baseline batched-Hungarian trong grid_disk k=2.
15. **Anti-herding có văn liệu**: capacity ledger (min-cost flow/Learn to Earn), tokens/quota, staggering, power-of-two-choices; herding (queue trạm, concentration) là guardrail metric — advice làm queue arm A > arm B nghĩa là advisor tự phá giá trị.
16. **Phân lớp biến A/B/C** cho robust optimization (bền vững → bài toán ràng buộc; bán bền vững → feature flag; bất định → reasoning guardrail) + hybrid trigger (event + fixed anchors + threshold) + persistent-vs-session memory — spec đã APPROVED.

## Mapping research → feature

| Feature | Research dùng trực tiếp |
| --- | --- |
| F0 policy Q&A | `policy/bonus-programs.md`, `economics/income-structure.md`; bắt buộc Policy KB có version/citation |
| F1 trước ca | policy track/cohort + persona + money definitions; không hard-code mốc cũ |
| F2 trong ca | `market/order-distribution.md`, `community/pain-points.md`; chỉ tư vấn theo thời gian, không reposition |
| F3 sau ca | hành vi sạc/nghỉ, tiến độ mốc versioned, so với chính tài xế |
| 5 persona mock | part-time, full-time RTO, top performer, tân binh, lão làng; mọi số gắn MOCK/TBD |
| Simulator twin-world (T-018+) | `simulation/*`; specs: `simulation-twin-world`, `advice-timing-state-memory`, `simulation-pilot-world` (pilot 1 quận, 50 actors) |

## Follow-up

- T-013: người thật join 1–2 group Facebook nếu cần bổ sung insight.
- T-004: research handoff xong (source register 7 URL official + text corpus evidence tại `policy/`). **Chưa phải KB runtime**: T-011/reviewer riêng mới chuyển evidence → `PolicyFact` versioned. ⚠ Corpus JSON đang lỗi encoding (mojibake) — cần re-fetch/repair (UPDATE-022).
- T-011: contract mới phải version hóa policy bundle và money definition; contracts cũ vẫn deferred.
- D-007: quy trình khiếu nại/giải trình là dự án khác.
