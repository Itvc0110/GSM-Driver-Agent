# research/ — Kết quả nghiên cứu, chia theo loại tài liệu

Cập nhật: 2026-07-20. Mỗi **loại tài liệu** nằm trong một folder tên rõ ràng. Mọi claim trong đây kèm **nguồn + ngày + độ tin cậy** (`official` > `press` > `community` > `research`). Số chưa xác nhận đánh dấu `TBD`/`MOCK`.

## Cấu trúc folder

| Folder | Loại tài liệu | File hiện có |
| --- | --- | --- |
| `policy/` | Chính sách, thưởng/phạt, quy tắc — dữ liệu để trả lời F0 và tính thưởng F1 | `bonus-programs.md` |
| `economics/` | Cấu trúc thu nhập, chiết khấu theo hình thức hợp tác, chi phí tài xế | `income-structure.md` |
| `community/` | Pain points, kinh nghiệm thực chiến, thu nhập tự khai, group Facebook | `pain-points.md`, `community-insights.md` |
| `market/` | Số liệu thị trường & phân phối đơn (để mock) | `order-distribution.md` |
| (root) | Tổng hợp toàn bộ | `00_SUMMARY.md` |

## Quy ước

- **File tổng hợp đọc trước:** [`00_SUMMARY.md`](00_SUMMARY.md) — 10 điều quan trọng nhất + mapping research→features.
- Tài liệu **đặc tả kỹ thuật** (spec để code) KHÔNG nằm ở đây mà ở `specs/` (vd `specs/mock-order-distribution.md`).
- Tài liệu **kế hoạch** (scope, personas, user stories) ở `planning/`.
- Khi thêm loại findings mới (vd `research/safety/`, `research/ux/`): tạo folder tên rõ ràng + cập nhật bảng trên.
- Chính sách Xanh SM đổi rất thường xuyên → mọi con số phải ghi **effective date + version**; xem timeline trong `policy/bonus-programs.md`.
