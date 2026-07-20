# SCOPE — Phạm vi hiện hành (v2)

Cập nhật: 2026-07-20 · Trạng thái: ACTIVE · Thay thế cách tiếp cận cũ trong `docs/` (đã defer, xem `tracking/DEFERRED.md`).

## 1. Phần CỐ ĐỊNH

**Problem statement:** Tài xế Xanh SM khó tối ưu thu nhập vì không nắm hết chính sách/thưởng phạt áp dụng cho hồ sơ của mình, không biết chạy/nghỉ/sạc lúc nào là hợp lý, và không có phản hồi phân tích sau ca.

**Mục tiêu:** Giúp tài xế đạt mục tiêu thu nhập (net — tiền thực nhận sau khi trừ phần chia cho app) trong quỹ thời gian của họ, mà **không** can thiệp matching/dispatch/pricing/routing.

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
- Tài xế đặt **chỉ tiêu thu nhập**: mặc định là **tiền thực nhận (net)** — phân biệt rõ với tiền tổng (gross) và phần phải chia lại cho app. Chỉ tiêu mặc định suy từ chính sách Xanh SM + hồ sơ tài xế; tài xế chỉnh được.
- Agent nhận xét chỉ tiêu: quá cao/quá thấp so với hồ sơ (part-time khác full-time) và khuyên điều chỉnh thế nào.
- UI: **defer** chi tiết, nhưng note — sau này phải tối ưu cho dễ dùng.

### F2 — Trong ca

- State chính: số đơn đang được đặt trong khu vực tại thời điểm đó mà có thể được phân phối cho tài xế.
- **Mock** phân phối đơn theo: khung giờ trong ngày × ngày trong tuần × vị trí (tổng số đơn tại một thời điểm ở một khu vực). Yêu cầu: nghiên cứu để con số và phân phối **sát thực tế nhất có thể** (xem RESEARCH).
- Đầu ra: lời khuyên về lộ trình thời gian — khi nào nên chạy, khi nào nên nghỉ/sạc.
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

## 6. Cách mở rộng scope

Tăng dần theo **pain point** và **user story** của tài xế (`planning/USER_STORIES.md`). Mỗi lần mở rộng: xác nhận pain point bằng nghiên cứu thực tế trước, rồi mới thêm feature.

## 7. Câu hỏi mở

1. CrewAI: dùng thật hay chỉ là ý tưởng tham khảo của stakeholder? Cần đánh giá so với flow tự viết (T-005).
2. Nguồn số liệu nào đủ tin cậy để mock phân phối đơn sát thực tế? (đang research — T-001)
3. Ranh giới dữ liệu được phép dùng cho hồ sơ tài xế mock (tỷ lệ nhận/hoàn thành đơn lấy chuẩn nào)?

*Đã chốt 2026-07-20:* luồng giải trình vi phạm là dự án khác (mục 4); research chạy trước, UI clone (T-009) làm sau research.
