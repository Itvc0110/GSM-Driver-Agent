# Audit MATH-MODELLING kênh + solver (Cường chỉ thị 2026-08-06)

> *"Kiểm tra tính logic của bài toán, quan sát đủ biến chưa? math modelling chuẩn chưa? có mở
> rộng thêm được không? — kể cả những cái đang bị tắt. Mở rộng phải dựa trên đầu ra là các
> action có thể thực hiện được và solver. Tương tự với solver."*

**Lớp lỗi mẫu (case study UPDATE-160 / D-E4-06):** `station_choice` có objective CẬN THỊ —
argmin(đường+queue+pin) cực tiểu downtime nhưng thiếu VẾ GIÁ TRỊ VỊ TRÍ sau đổi pin ⇒ thời gian
thắng SIG, tiền thua (P1 −3,9k SIG). Audit này tìm cùng lớp lỗi ở 7 kênh + 9 solver:
(a) objective thiếu vế mà world thật sự định giá; (b) biến sim BIẾT nhưng kênh/solver BỎ QUA;
(c) kỳ vọng ≠ realized; (d) sai đơn vị; (e) ràng buộc không bind hoặc bind đôi.

**Artifact:** `mm-01..mm-12.json` (5 kênh · 5 solver · 2 cắt ngang: information-set +
extensibility-map) → `mm-13-refute.json` (phản biện) → `00-SUMMARY.md` (tổng hợp đã lọc).
Finding nào KHÔNG có evidence file:line hoặc chưa phản biện thì không được vào kết luận
(bài học ADV-09). Mọi đề xuất mở rộng phải neo (action executable trong sim × solver có sẵn).

KHÔNG lặp lại nợ đã biết: ADV-01..09 · D-E4-01/02/06 · E10 λ-noise · T-045c · D-M3-19 ·
B6-PARITY · D-M3-01/10. Ranh giới: sức khoẻ KHÔNG vào objective (§1.2b spec v2).

Trạng thái: workflow chạy nền 2026-08-06. Nếu session bị compact: đọc artifact dir này +
`tracking/BOOTSTRAP-SESSION.md` §5b rồi tiếp tục từ 00-SUMMARY.md.
