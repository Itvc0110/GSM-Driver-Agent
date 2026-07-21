# UPDATE-004 — Tái cấu trúc research theo loại + hoàn tất research đợt 2

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo yêu cầu của Cường
- **Loại:** docs / research / refactor
- **TODO / User story liên quan:** T-012 (DONE), sinh T-013

## Tóm tắt

Theo yêu cầu "lưu finding vào folder, tài liệu khác loại vào folder khác nhau có tên rõ ràng": tách `planning/research/` + `planning/mock/` thành 2 cây riêng — `research/` (findings, chia theo loại) và `specs/` (đặc tả kỹ thuật). Đồng thời hoàn tất research đợt 2: trích được **con số thưởng cụ thể** (trước đây nằm trong ảnh) từ text bài official + PDF Q&A + trang vệ tinh.

## Chi tiết cập nhật

### Tái cấu trúc thư mục

| Cũ | Mới |
| --- | --- |
| planning/research/00_SUMMARY.md | research/00_SUMMARY.md |
| planning/research/bonus-programs.md | research/**policy**/bonus-programs.md |
| planning/research/income-structure.md | research/**economics**/income-structure.md |
| planning/research/pain-points.md | research/**community**/pain-points.md |
| planning/research/community-insights.md | research/**community**/community-insights.md |
| planning/research/order-distribution.md | research/**market**/order-distribution.md |
| planning/mock/order-distribution-spec.md | **specs**/mock-order-distribution.md |

- Thêm `research/README.md` mô tả thiết kế folder (loại tài liệu → folder tên rõ ràng: policy/economics/community/market; specs tách riêng; planning tách riêng).
- Sửa mọi cross-reference trong docs đang hoạt động (CLAUDE.md, README.md, planning/SCOPE, PERSONAS, RESEARCH, research/00_SUMMARY, specs/mock, tracking/TODO). UPDATE-001/002/003 giữ nguyên (lịch sử append-only — đường dẫn cũ là ảnh chụp thời điểm đó).

### Research đợt 2 — con số verify được (thay phần "trong ảnh")

Đã tự verify qua WebFetch/WebSearch (agent bảng thưởng bị session limit, tôi hoàn tất thủ công):
- **Timeline tỷ lệ chia** (gỡ mâu thuẫn): 91% (11/2024) → 70% (12/2025) → tới 75% (02/03/2026) — các version nối tiếp, không mâu thuẫn.
- **Bảng điểm thưởng tuần** KV1 (HN...): 400/700/1.100/1.400 → 200k/400k/800k/1,2tr; KV khác: 500/800/1.200/1.500 → 200k/400k/800k/1,2tr.
- Điểm/cuốc: cao điểm 6–8h & 16–18h =10đ, giờ thường =5đ; **điểm tính theo giờ khách ĐẶT chuyến**.
- Điều kiện thưởng tuần: HN ≥5 ngày + ≥85% nhận + ≥85% hoàn thành (HCM 90/90).
- Thưởng "Giờ Vàng" HN (26/03–30/04/2026): 2 chuyến trong khung 6–8h/17–19h → 30k/ngày, cần ≥18 cuốc + ≥90%.
- Thưởng thâm niên: 6–9th 500k, 9–12th 700k, ≥12th 1tr/tháng (⚠️ gốc là chính sách Car — chưa xác nhận cho Bike).
- Kinh nghiệm cộng đồng (agent 2): pattern "trưa về sạc 3–4h"; tủ pin HN quá tải Đống Đa/Từ Liêm; 6 group Facebook (login wall → T-013); điểm đứng HN + dead hours → đã mock reasoning.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| research/ (7 file di chuyển) | move | từ planning/research + planning/mock |
| research/README.md | tạo | thiết kế folder theo loại |
| research/policy/bonus-programs.md | sửa | thêm §"Bảng số verify đợt 2" |
| research/community/community-insights.md | tạo | kết quả agent kinh nghiệm cộng đồng |
| specs/mock-order-distribution.md | move+sửa | từ planning/mock |
| planning/research, planning/mock | xóa | folder rỗng sau move |
| CLAUDE.md, README.md, planning/{SCOPE,PERSONAS,RESEARCH}.md, research/00_SUMMARY.md, tracking/TODO.md | sửa | cross-ref + bản đồ repo + TBD |

## Docs đã cập nhật kèm theo

TODO (T-012 DONE, thêm T-013), CLAUDE/README (bản đồ repo có research/ + specs/), PERSONAS (điền TBD). SCOPE/DEFERRED: không đổi nội dung (chỉ path nếu có).

## Kiểm chứng

- Con số bảng thưởng: verify trực tiếp bằng WebFetch trang "Thưởng Nóng Giờ Vàng" + WebSearch bảng điểm 2 nhóm khu vực + thâm niên. PDF Q&A 12/2025 KHÔNG đọc được text (FlateDecode) — số PDF lấy gián tiếp qua agent, đánh dấu rõ.
- CHƯA kiểm chứng: mức thâm niên áp dụng Bike (mượn số Car); % chia theo từng khung giờ; nội dung trong group FB (T-013).

## Follow-up / defer phát sinh

- T-013: join FB group đọc mẹo + số thành viên.
- Còn lại theo thứ tự Cường: T-009 UI clone (sau research — giờ research xong), T-004 KB chính sách, T-005 đánh giá CrewAI, T-002/T-003 chuyển sang code sau khi có scaffold + claim.
