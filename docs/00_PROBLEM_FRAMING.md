# 00 — Problem Framing

## 1. Reframe

Câu hỏi sai: “Làm sao để tài xế nhận cuốc tốt hơn và kiếm nhiều tiền nhất?” Câu hỏi này đẩy sản phẩm vào vùng xung đột trực tiếp với dispatch và dễ khuyến khích chạy lâu.

Câu hỏi đúng: “Trong những quyết định nằm trong quyền kiểm soát của tài xế, làm sao giúp họ chọn kế hoạch ca có thu nhập ròng/giờ tốt hơn, downside thấp hơn và phù hợp với pin, thời gian, điểm kết thúc, nghỉ, mục tiêu cá nhân — mà không làm giảm service level, fairness hay lợi ích mạng lưới?”

## 2. Pain point → quyết định → giải pháp ngắn → dữ liệu → metric

| Pain point | Quyết định cần hỗ trợ | Brief solution | Data tối thiểu | Metric chính |
| --- | --- | --- | --- | --- |
| Chọn sai giờ chạy | Bắt đầu/kết thúc lúc nào | Shift plan + what-if | availability, forecast theo time bucket, lịch sử cá nhân | causal lift net VND/h; late-end rate |
| Chạy nhiều nhưng rỗng/chờ cao | Tiếp tục hay kết thúc/chuyển mode | efficiency alert; Phase 2 mới có zone guidance | session, empty km, wait, zone forecast | empty-km ratio; productive time |
| Theo thưởng không còn lợi | Theo tier nào hay dừng | Bonus navigator với expected incremental net | policy thưởng, progress, eligible trips, time left | incremental net after bonus; false-pursuit rate |
| Sạc sai thời điểm | Sạc bây giờ/sau, mức nào | charge plan theo opportunity cost | SOC, energy curve, charger ETA/wait, future need | peak-time lost; charge wait; reserve violations |
| Nghỉ sai hoặc chạy quá dài | Nghỉ lúc nào | smart break + hard safety policy | driving/online duration, low-demand window | break compliance; fatigue proxy |
| Chuyến cuối làm xa nhà/depot | Khi nào bật homeward | homeward/return-to-depot plan | blurred end zone, deadline, travel-time forecast | end-zone distance; on-time-end rate |
| Không hiểu vì sao thu nhập thấp | Ngày sau đổi gì | post-shift decomposition, one actionable lesson | earning ledger, time allocation, comparable days | insight usefulness; next-shift change/uplift |
| Không tin gợi ý chung chung | Có nên làm theo | alternative + range + expiry + reason | model calibration, driver preference, outcomes | calibration; accept/ignore reason; trust trend |

## 3. Product boundary

### Phase 0–1: cho phép

- Lập/điều chỉnh ca; so sánh 2–3 kế hoạch.
- Mục tiêu và xác suất đạt mục tiêu.
- Bonus tier: theo/không theo và lý do kinh tế.
- Sạc/nghỉ; homeward/return-to-depot.
- Efficiency alerts và post-shift coaching.
- What-if khi tài xế thay đổi giờ, mục tiêu, risk hoặc end zone.
- Chat/voice chỉ để giải thích và nhập constraint.

### Phase 2: có điều kiện

- `STAY_IN_ZONE` hoặc `REPOSITION_TO_ZONE` ở mức zone, không ở mức cuốc.
- Bắt buộc capacity token, expiry, fleet impact, fairness và service-level gate.
- Không hiển thị hotspot nếu system không biết số recommendation còn hiệu lực.

### Không làm

- Gợi ý nhận/từ chối/hủy một order cụ thể.
- Xếp lại đơn, can thiệp giá, dispatch hoặc passenger matching.
- Hứa chắc mức thu nhập.
- Dạy lách policy/phạt/định vị; tối ưu dựa trên thông tin không được phép dùng.
- Tối ưu thu nhập bằng cách ép tăng giờ hoặc bỏ nghỉ.

## 4. Vì sao không bắt đầu bằng agent

Phần giá trị cốt lõi cần forecast, optimization, policy và evaluation có cấu trúc. LLM phù hợp với giải thích, hỏi đáp, chuyển lời nói thành constraint có xác nhận và tóm tắt. Card, timeline, map, notification và voice briefing mới là interaction chính; chat là lối vào bổ sung. Cách này giảm hallucination, latency/cost và tạo audit trail rõ.

## 5. Driver/service model

| Dimension | Bike | Car | Premium |
| --- | --- | --- | --- |
| Service eligibility | passenger, parcel/food tùy policy | passenger và các service được cấp | premium service theo eligibility |
| Vehicle/energy | battery/charging model xe máy | battery, depot/charging model ô tô | như Car nhưng policy/service standard riêng |
| Economics | partner/compensation config | employee/partner config theo thị trường | fare/share/quality bonus config riêng |
| Key constraint | range, weather, parcel capacity | continuous driving, charging/depot | service eligibility, customer experience |
| Không giả định | cùng commission với Car | tài xế tự chịu mọi energy cost | Premium luôn có thu nhập/giờ cao hơn |

Không tạo ba code path độc lập. Dùng `DriverCapabilityProfile` + versioned policies.

## 6. Xung đột driver–platform và cách giải

Tối ưu cục bộ từng tài xế có thể làm dồn cung, giảm thu nhập của tất cả và tăng passenger wait ở nơi khác. Hệ thống dùng constrained hierarchy:

1. Safety/legal/policy: veto.
2. Platform/fleet: service-level floor, zone/charger capacity, margin/non-inferiority, fairness.
3. Driver: net earnings, risk, empty/wait, goal.
4. Personal preference: end zone, stability, familiar area, friction.

Kết quả không phải “tối ưu tài xế bất chấp tập đoàn” mà là tối ưu lợi ích tài xế trong feasible set doanh nghiệp đã phê duyệt. Trade-off phải đo được và được Product/Operations sở hữu, không ẩn trong weight của model.

## 7. Những câu hỏi phản biện đã tự trả lời

**Có nên xếp hạng khu vực?** Chưa ở MVP. Khi chưa biết dispatch/supply impact, chỉ nên lập lịch, sạc, nghỉ, thưởng, homeward và phân tích. Zone ranking vào Phase 2 với fleet guard.

**Tại sao cần optimizer nếu UI chỉ gợi ý vài hành động?** Vì lựa chọn hiện tại ảnh hưởng pin, thưởng, giờ kết thúc và cơ hội tương lai; rule đơn lẻ dễ mâu thuẫn. Tuy nhiên heuristic là baseline bắt buộc để kiểm chứng solver.

**Có cần RL?** Chưa. Mock data không tạo policy đáng tin. Rolling-horizon scenario optimization minh bạch, dễ test và phù hợp cold start; RL chỉ là hypothesis sau khi có simulator/logged policy tốt.

**Cá nhân hóa từ thói quen có đủ không?** Không. Explicit constraints luôn ưu tiên; learned preference cần consent, confidence và cơ chế sửa/xóa.

**Tối ưu net earnings/hour có làm tài xế kết thúc quá sớm?** Có thể. Vì vậy luôn hiển thị đồng thời total net earnings, goal probability và hours; objective dùng profile/mode và minimum-goal constraints thay vì chỉ một ratio.

**Mock có ích gì?** Mock giúp khóa contract, test failure/edge cases và demo flow; không chứng minh forecast accuracy, causal uplift hay ROI thật.

## 8. Product hypothesis ưu tiên

1. Shift/charge/bonus/homeward có thể tạo giá trị mà không chạm dispatch.
2. Range + baseline + trade-off làm recommendation đáng tin hơn single-point promise.
3. Một recommendation ít nhưng đúng thời điểm tốt hơn feed nhiều card.
4. Causal lift phải được đo cùng platform guardrails; adoption cao không đồng nghĩa hiệu quả.
5. Homeward và charge-break combination có thể tăng retention/trust dù lift thu nhập nhỏ.
