# UPDATE-002 — Hoàn thành research đợt 1 (T-001)

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo yêu cầu của Cường
- **Loại:** research
- **TODO / User story liên quan:** T-001 (DONE đợt 1), sinh T-012

## Tóm tắt

Chạy 4 agent nghiên cứu web song song về (1) cấu trúc thu nhập, (2) chương trình thưởng/kỷ luật, (3) pain points, (4) phân phối đơn để mock. Kết quả lưu `planning/research/` (5 file, mỗi claim kèm nguồn + ngày + độ tin cậy). Claim trung tâm (chính sách ĐBTN Green Bike Platform — URL seed của Cường) được xác minh trực tiếp lần 2 trên trang official: khớp.

## Chi tiết cập nhật

- Skill deep-research và tool Workflow không khả dụng trong phiên → dùng 4 background agent + tự kiểm chứng chéo (các con số quan trọng xuất hiện độc lập ở ≥2 agent/nguồn: ngưỡng 70% acceptance, chiết khấu 21%/31%, ĐBTN 600k/ngày, chia sẻ 75%).
- Phát hiện then chốt: công thức thu nhập Bike official; điểm thưởng nhân đôi khung 6–8h & 16–18h; ngưỡng kỷ luật 70%/50%/90%; 3 track hợp tác kinh tế khác nhau; pain point #1 là sạc/đổi pin; bảng thưởng chi tiết chỉ có dạng ảnh/in-app (gap lớn nhất → T-012).
- Số tự khai cộng đồng gắn confidence tối đa medium; nguồn proxy quốc tế gắn nhãn [PROXY], chỉ dùng cho hình dạng phân phối.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| planning/research/00_SUMMARY.md | tạo | 10 điều quan trọng nhất + mapping research→features |
| planning/research/income-structure.md | tạo | 3 track hợp tác, chi phí pin/thuê xe |
| planning/research/bonus-programs.md | tạo | Thưởng/ĐBTN/kỷ luật, tham số cho F0/F1 |
| planning/research/pain-points.md | tạo | Pain points xác nhận + thu nhập tự khai + 3 persona mock đề xuất |
| planning/research/order-distribution.md | tạo | Tham số mock phân phối đơn (T-003) |
| tracking/TODO.md | sửa | T-001 → DONE (đợt 1); thêm T-012 |

## Docs đã cập nhật kèm theo

TODO (như trên). SCOPE/USER_STORIES/DEFERRED: không đổi (mapping research→features nằm trong 00_SUMMARY.md; cập nhật story sẽ làm khi Cường review).

## Kiểm chứng

- Xác minh trực tiếp lần 2 trang ĐBTN official (600k/360k, ≥15 cuốc, phát tới 17 cuốc, bù 36k/cuốc, khung 6h–8h59/16h–18h59, từ 30/03/2026): **khớp**.
- CHƯA kiểm chứng: từng URL còn lại (agent tự mở nhưng chưa verify độc lập toàn bộ); bảng thưởng trong ảnh; con số tự khai cộng đồng. Mâu thuẫn tồn đọng ghi rõ trong từng file (chiết khấu 75%/91%/73%, ngày hiệu lực quy tắc ứng xử).

## Follow-up / defer phát sinh

- **T-012**: xác minh bảng thưởng hiện hành trong app tài xế + OCR ảnh chính sách (cần người có app).
- Đề xuất cho Cường: T-002 (3 persona mock đã có khung từ pain-points.md), T-003 (tham số generator đã có từ order-distribution.md) — sẵn sàng bắt đầu sau khi review.
