# Driver Income OS — AI Coding Pack

Phiên bản: `0.1.0-discovery`  
Ngày: `2026-07-16`  
Trạng thái: tài liệu khám phá và đặc tả ban đầu; chưa phải đặc tả chính thức của GSM.

## Kết luận thiết kế quan trọng nhất

Driver Income OS là **lớp hỗ trợ quyết định cho tài xế**, không phải hệ thống dispatch thứ hai và không phải chatbot tự quyết định. Forecasting ước lượng tương lai; optimizer tạo các phương án khả thi; policy gate loại phương án vi phạm an toàn, pháp lý, chính sách hoặc lợi ích hệ thống; UI/LLM chỉ trình bày, giải thích và cho phép tài xế thêm ràng buộc.

MVP không khuyên tài xế nhận, từ chối hoặc hủy một cuốc cụ thể; không thay đổi thứ tự phân phối cuốc; không hứa chắc thu nhập. Những gợi ý có thể làm dịch chuyển nguồn cung theo vùng chỉ được mở ở phase sau khi có quota cấp đội xe, fairness, service-level guardrail và đo được tác động thị trường.

## Thứ tự đọc cho AI coding

1. `AGENTS.md` — quy tắc làm việc bắt buộc.
2. `MASTER_PROMPT.md` — prompt đầy đủ để khởi động AI coding.
3. `docs/00_PROBLEM_FRAMING.md` — định nghĩa bài toán và phạm vi lời khuyên.
4. `docs/01_PRD.md` — người dùng, use case, MVP và acceptance criteria.
5. `docs/02_SYSTEM_SPEC.md` — luồng hệ thống, API và failure behavior.
6. `docs/03_DATA_AND_MOCK_SPEC.md` — data contract, provenance và mock strategy.
7. `docs/04_OPTIMIZATION_SPEC.md` — objective, constraints, uncertainty và thuật toán.
8. `docs/05_METRICS_ROI_EXPERIMENTS.md` — đo hiệu quả, causal test và ROI.
9. `docs/06_ARCHITECTURE_REPO_CICD.md` — kiến trúc, tech stack, scaffold và CI/CD.
10. `docs/07_ROADMAP_GOVERNANCE.md` — PHASE*, FIX*, MEMORY và risk register.
11. `docs/08_OPEN_QUESTIONS_AND_DECISIONS.md` — quyết định đã khóa và câu hỏi cần GSM xác nhận.
12. `docs/09_RESEARCH_REFERENCES.md` — nguồn nghiên cứu và mức độ áp dụng.

Các JSON Schema trong `contracts/` là điểm nối giữa hai người phát triển. `templates/` chứa mẫu quản trị thay đổi.

## Giả định nền tảng

- Chưa có schema dữ liệu chính thức; mọi dữ liệu demo phải mang `data_mode=synthetic`, `is_mock=true`, version và provenance.
- Thu nhập ròng được tính theo compensation policy của từng nhóm tài xế/loại xe; không dùng một công thức cố định cho Bike, Car và Premium.
- Các giới hạn lái xe, nghỉ, pin, khu vực hoạt động, thưởng và service-level là policy có version, không hard-code vào optimizer.
- Địa chỉ nhà không cần lưu dạng địa chỉ thô; MVP dùng `home_zone_id`/geofence đã làm mờ và chỉ khi tài xế đồng ý.
- Các con số target trong tài liệu là placeholder/hypothesis nếu chưa có baseline; không được trình bày như cam kết kinh doanh.

## Definition of Ready

Một PHASE chỉ được code khi có: problem statement, in/out of scope, contract bị ảnh hưởng, acceptance criteria, test plan, dữ liệu/mode chạy, guardrail và rollback plan.

## Definition of Done

Code, test, contract, telemetry, tài liệu PHASE/FIX và `templates/MEMORY.md` cùng được cập nhật; không có mock data đi qua live adapter; recommendation có trace ID, expiry, baseline, uncertainty và policy decision.
