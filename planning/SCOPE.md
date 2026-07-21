# SCOPE — Phạm vi hiện hành (v2)

Cập nhật: 2026-07-20 · Trạng thái: ACTIVE · Thay thế cách tiếp cận cũ trong `docs/` (đã defer, xem `tracking/DEFERRED.md`).

## 1. Phần CỐ ĐỊNH

**Problem statement:** Tài xế Xanh SM khó tối ưu thu nhập vì không nắm hết chính sách/thưởng phạt áp dụng cho hồ sơ của mình, không biết chạy/nghỉ/sạc lúc nào là hợp lý, và không có phản hồi phân tích sau ca.

**Mục tiêu:** Giúp tài xế đạt mục tiêu **driver payout** (khoản nhận sau phần chia cho nền tảng — mục tiêu mặc định) hoặc **estimated net income** (driver payout trừ các chi phí tài xế chịu đã biết) trong quỹ thời gian của họ, mà **không** can thiệp matching/dispatch/pricing/routing. Ba lớp tiền phải luôn tách rõ: `gross revenue` = doanh thu/cước trước chia nền tảng; `driver payout` = gross sau platform share + bonus/adjustment đủ điều kiện; `estimated net income` = payout trừ chi phí có bằng chứng. Estimated net phải gắn definition/version và chỉ hiển thị khi đủ dữ liệu; thiếu chi phí thì ghi `partial/unknown`, không tự ước đoán.

**Định hướng giải pháp:** Bản chất là bài toán tối ưu đa biến có ràng buộc, nhưng **tiếp cận top-down**, chưa mô hình hóa từ atomic features. Kiến trúc flow-first hybrid (xem `flow image/GSM_Driver_Income_AI_Agentv2.drawio`): orchestrator điều phối → rule/analytics tính baseline, khoảng cách mục tiêu, what-if, xếp hạng (**mọi số tài chính/policy**) → **AI agent tổng hợp, so sánh, giải thích** — và **được đảm nhiệm một vài bước reasoning** khi sub-problem chưa có cách tối ưu hóa hoặc mô hình hóa quá phức tạp so với reasoning thuần (phải log, gắn độ tin cậy, tắt được về rule/template; không tự tạo số tài chính/policy) → guardrail pass/veto/human-review → tài xế quyết định → đo kết quả. *Tinh chỉnh nguyên tắc reasoning được Cường duyệt 2026-07-20 — vẫn thuộc phần định hướng cố định.* Stakeholder có nhắc **CrewAI** như một framework tham khảo cho lớp orchestration/agent (đang đánh giá, chưa chốt — T-005).

## 2. Phần LINH HOẠT

Kiến trúc chi tiết, stack, cách triển khai feature, UI — được đề xuất thay đổi qua plan mode. Luồng data và kế hoạch bên dưới đều là **khung tạm thời**; bài toán còn mơ hồ về features thực tế → phải vừa xây khung vừa nghiên cứu sâu (xem `planning/RESEARCH.md`).

**Tính năng tương lai (roadmap — sau khi hoàn thiện F0–F3; vẽ nét đứt trong drawio v2):** (a) nhận thêm **state pin xe** cho F2 (D-002); (b) **nguồn cộng đồng** (group tài xế / websearch kinh nghiệm) đi qua khối **kiểm chứng & lọc rủi ro** (`specs/community-source-risk-control.md`, D-008) — chỉ bổ sung ngữ cảnh, không thay policy/số tài chính.

## 3. Minimum scope — 4 khối tính năng

### F0 — Hỏi đáp chính sách theo hồ sơ tài xế

Trả lời về chính sách, ưu đãi, thưởng/phạt **hiện hành**, cá nhân hóa theo hồ sơ. Phân loại tài xế cần hỗ trợ (taxonomy):

- Thâm niên: mới làm / làm lâu năm.
- Thời gian: full-time / part-time.
- Chỉ số hồ sơ: tỷ lệ nhận đơn, tỷ lệ hoàn thành đơn (theo các mức).
- Hình thức xe: chạy xe cá nhân lên platform / thuê xe của công ty.
- Tier / loại xe: Bike, Bike Premium, Car, Car Premium, v.v.

Kế hoạch: **5 hồ sơ persona mock** (nháp v1 tại `planning/PERSONAS.md` — part-time, full-time RTO, top performer xe riêng, tân binh mới dùng app, lão làng thâm niên), tập trung **Bike trước**. Câu trả lời chính sách phải có trích dẫn nguồn (knowledge base policy có version).

### F1 — Trước ca (khi tài xế mở app)

- Chủ động cập nhật/nhắc: hình thức trao thưởng mới, giới hạn mới áp dụng cho tài xế.
- Tư vấn cách tối ưu để đạt mức thưởng.
- Tài xế đặt **chỉ tiêu thu nhập**: mặc định là **driver payout**; UI phải phân biệt với `gross revenue`. Có thể hiển thị **estimated net income** khi biết đủ chi phí tài xế chịu (sạc/thuê xe...), kèm definition/version và trạng thái completeness. Chỉ tiêu mặc định suy từ policy đã version hóa + hồ sơ tài xế; tài xế chỉnh được.
- Agent nhận xét chỉ tiêu: quá cao/quá thấp so với hồ sơ (part-time khác full-time) và khuyên điều chỉnh thế nào.
- UI: **defer** chi tiết, nhưng note — sau này phải tối ưu cho dễ dùng.

### F2 — Trong ca

- State chính: **mock demand proxy** — số đơn được đặt theo khu vực × thời điểm. Đây không phải pool matching/dispatch và không khẳng định đơn nào chắc chắn được phân cho một tài xế.
- **Mock** phân phối demand theo: khung giờ trong ngày × ngày trong tuần × vị trí (tổng số đơn đặt tại một thời điểm ở một khu vực). Yêu cầu: nghiên cứu để hình dạng phân phối sát thực tế nhất có thể, gắn nhãn MOCK/PROXY và assumption log (xem `research/market/` + `specs/mock-order-distribution.md`).
- Đầu ra: lời khuyên **theo thời gian** — khi nào nên chạy, khi nào nên nghỉ/sạc — và (mở 2026-07-21, quyết định Cường sau verify) **gợi ý khu vực đứng chờ theo heatmap demand mock CÓ ĐIỀU KIỆN**: chỉ giữa các cuốc/trước ca, capacity-aware chống dồn cung, kèm cảnh báo tỷ lệ nhận cuốc, nhãn mock + bất định, không hứa thu nhập; căn cứ verify: Xanh không có heatmap tài xế và không ràng buộc khu vực realtime → tính năng bổ sung, không chồng đè tối ưu sẵn có (chi tiết + 5 điều kiện: `research/simulation/action-space.md` §Phạm vi advisor). Vẫn KHÔNG can thiệp dispatch/matching, KHÔNG khuyên nhận/từ chối/hủy đơn cụ thể.
- Cập nhật voucher ngay trong ca.
- **Defer:** nhận thêm state pin xe.

### F3 — Sau ca

Agent đóng vai analyzer + advisor: tổng hợp hành vi/hoạt động trong ca, phân tích explicit cho tài xế:

- Có thể tối ưu hơn như thế nào.
- Chỉ ra hành vi chưa tối ưu, ví dụ: sạc vào giờ cao điểm, chưa chạy đủ để lấy voucher, từ chối nhiều đơn ảnh hưởng đến hồ sơ, v.v.

## 4. Luồng giải trình vi phạm — NGOÀI SCOPE (quyết định 2026-07-20)

Luồng xử lý **hồ sơ vi phạm** (AI hỗ trợ tài xế soạn giải trình, nhân viên kiểm duyệt quyết định) là **một dự án khác, không thuộc repo này** — quyết định của Cường 2026-07-20. File drawio tương ứng đã **xóa khỏi repo** theo yêu cầu (D-006). Quy trình khiếu nại/giải trình khi bị phạt cũng defer theo (D-007).

## 5. UI/UX

- Ưu tiên **mobile-first** (tài xế dùng qua app); tham khảo app Xanh SM ở góc nhìn tài xế.
- Kế hoạch: dùng template <https://github.com/JCodesMore/ai-website-cloner-template> để clone <https://rag-xanh-sm-v1.vercel.app/> làm UI/UX tạm thời (trong TODO).

## 5b. Mở rộng 2026-07-21 — Đánh giá bằng giả lập & robust optimization (Cường yêu cầu)

Sáu yêu cầu mới được phản ánh vào 2 spec + 3 research:

1. **Đo hiệu quả gợi ý bằng giả lập twin-world** (2 thế giới song song cùng seed: có advice vs không; paired theo seed; metrics 3 tầng driver/system/fairness; visualize replay + dashboard) — `specs/simulation-twin-world.md`; phương pháp luận chuẩn (CRN/paired-seed, ITT/CACE) tại `research/simulation/evaluation-methodology.md`; stack công cụ tại `research/simulation/tooling.md`.
2. **Đo adherence** (tài xế có nghe lời khuyên không, kể cả "kinh nghiệm tự làm đúng" = coincident compliance) — taxonomy 5 nhãn + twin-diff attribution trong 2 file trên.
3. **Robust optimization theo phân lớp biến**: lớp A bền vững → bài toán tối ưu đa biến có ràng buộc; lớp B bán bền vững → feature flag; lớp C bất định → agent reasoning có guardrail; biến thăng/giáng cấp không phá cấu trúc bài toán — `specs/advice-timing-state-memory.md` §2. *Luồng hiện tại tuân thủ nguyên tắc nhưng thiếu phân lớp tường minh — nay đã bổ sung.*
4. **Khung thời gian gợi ý = HYBRID** (event-driven theo cuốc/SOC + fixed anchors đầu ca/khung thưởng + threshold-crossing, có cooldown/budget) và **tách persistent memory vs session state** — `specs/advice-timing-state-memory.md` §1, §3.
5. **Fleet-awareness trong giả lập** (supply field, trạm sạc/pin, chống herding bằng capacity ledger/staggering) — được phép trong **phạm vi simulator/advisor-sim** để nghiên cứu rủi ro "cả làng cùng đi sạc"; ranh giới sản phẩm thật giữ nguyên (D-004 chỉ nới cho sim — xem DEFERRED).
6. **Quần thể giả lập đa dạng**: 5 persona → archetype templates, sample nhiều actors có jitter với dispatcher batched-matching có sẵn; tham số thế giới HN (144 trạm đổi pin từ OSM, tốc độ, pin, demand) tại `research/simulation/world-parameters.md`.

**Pilot thu hẹp (Cường 2026-07-21 đợt 2, APPROVED + arm C):** phạm vi biểu diễn đầu tiên = **quận Đống Đa cũ, H3 res 9 (85 cells), 50 actors, ~1.200 đơn/ngày, 11 tủ đổi pin thật từ OSM**; timestep phân tầng (DES + dispatch tick 5s + bucket 15ph + advisor anchor 30ph); action set actor chốt theo hành vi thực tài xế (nghiên cứu `research/simulation/action-space.md`) — spec: `specs/simulation-pilot-world.md`. Mở rộng toàn nội thành (N=500, res 8) sau pilot, giữ nguyên kiến trúc.

## 6. Cách mở rộng scope

Tăng dần theo **pain point** và **user story** của tài xế (`planning/USER_STORIES.md`). Mỗi lần mở rộng: xác nhận pain point bằng nghiên cứu thực tế trước, rồi mới thêm feature.

## 7. Câu hỏi mở

1. CrewAI: dùng thật hay chỉ là ý tưởng tham khảo của stakeholder? Cần đánh giá so với flow tự viết (T-005).
2. Nguồn số liệu nào đủ tin cậy để hiệu chỉnh mock demand proxy sát thực tế hơn? Research đợt 1+2 đã hoàn tất (T-001, T-012); hiện vẫn thiếu dữ liệu GSM theo giờ/khu vực nên spec dùng FACT + PROXY + MOCK assumptions có version.
3. Ranh giới dữ liệu được phép dùng cho hồ sơ tài xế mock (tỷ lệ nhận/hoàn thành đơn lấy chuẩn nào)?

*Đã chốt 2026-07-20:* luồng giải trình vi phạm là dự án khác (mục 4); research chạy trước, UI clone (T-009) làm sau research.
