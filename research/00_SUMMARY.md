# Research Summary — Đợt 1 + Đợt 2

Ngày: 2026-07-20 · Files chi tiết: [income structure](economics/income-structure.md) · [bonus/policy](policy/bonus-programs.md) · [pain points](community/pain-points.md) · [community insights](community/community-insights.md) · [order distribution](market/order-distribution.md).
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

## Mapping research → feature

| Feature | Research dùng trực tiếp |
| --- | --- |
| F0 policy Q&A | `policy/bonus-programs.md`, `economics/income-structure.md`; bắt buộc Policy KB có version/citation |
| F1 trước ca | policy track/cohort + persona + money definitions; không hard-code mốc cũ |
| F2 trong ca | `market/order-distribution.md`, `community/pain-points.md`; chỉ tư vấn theo thời gian, không reposition |
| F3 sau ca | hành vi sạc/nghỉ, tiến độ mốc versioned, so với chính tài xế |
| 5 persona mock | part-time, full-time RTO, top performer, tân binh, lão làng; mọi số gắn MOCK/TBD |

## Follow-up

- T-013: người thật join 1–2 group Facebook nếu cần bổ sung insight.
- T-004: policy KB versioned cho F0.
- T-011: contract mới phải version hóa policy bundle và money definition; contracts cũ vẫn deferred.
- D-007: quy trình khiếu nại/giải trình là dự án khác.
