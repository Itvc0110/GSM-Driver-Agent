# UPDATE-### — <Tiêu đề ngắn, nói rõ thay đổi gì>

- **Ngày:**
- **Người thực hiện:** (Cường / Khánh / AI agent — ghi rõ agent làm theo yêu cầu của ai)
- **Loại:** feature / docs / fix / research / refactor / defer / data / ui
- **TODO / User story liên quan:** (T-###, US-…)

## Tóm tắt

(1–3 câu: thay đổi gì, vì sao.)

## Chi tiết cập nhật

(Mô tả đầy đủ: cái gì đổi, quyết định nào được đưa ra, giả định nào đặt ra.)

## Files bị ảnh hưởng

| File | Hành động (tạo/sửa/xóa) | Ghi chú |
| --- | --- | --- |
| | | |

## Docs đã cập nhật kèm theo

(SCOPE / TODO / DEFERRED / USER_STORIES / RESEARCH có đổi không? Nếu không đổi, ghi "không".)

## Assumptions và evidence

| Claim / tham số | Nhãn (`FACT` / `OBSERVED-CODE` / `PROXY` / `MOCK` / `ASSUMPTION` / `UNVERIFIED`) | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| | | | | |

## Kiểm chứng

(Đã test/chạy thử gì, kết quả; cái gì CHƯA kiểm chứng phải ghi rõ.)

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| | | | | |

## Visual verification

- **Status:** `REVIEWED` / `WAIVED` / `NOT_APPLICABLE` / `BLOCKED`
- **Cách launch / artifact:**
- **Seed / scenario đã xem:**
- **Người review + verdict:**
- **Nếu WAIVED/BLOCKED/NOT_APPLICABLE:** ghi yêu cầu waive, blocker hoặc lý do cụ thể.

## Adversarial self-review / flaws found

1. Điều gì có thể khiến kết quả trông tốt nhưng sai?
2. Có future-information leak, CRN drift, hidden fallback/clipping, unit mismatch, factor double-count hoặc visual aggregation bias không?
3. Assumption/evidence nào yếu nhất?
4. Đã so với baseline nào và giả thuyết nào đã loại trừ?
5. Flaw còn mở map vào TODO/DEFERRED ID nào?

## Expansion checkpoint (T-039 — bắt buộc sau mỗi phần hoàn thành)

1. **Schema**: cần thêm/bớt/sửa field/entity nào? (biến mới phải điền được bảng traceability §1.7 spec core)
2. **Bài toán tối ưu**: có residual nào formalize được thành solver mới không? Có bài toán mới từ data hiện có?
3. **Tính năng**: tính năng mới khả thi từ những gì vừa xây?

(Không tự triển khai — ghi đề xuất để Cường duyệt. Không có gì thì ghi "không".)

## Follow-up / defer phát sinh

(Việc mới sinh ra → thêm vào TODO; ý tưởng ngoài scope → thêm vào DEFERRED; ghi ID, severity/evidence và điều kiện mở lại.)
