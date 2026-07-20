# UPDATE-005 — Luồng v2 (drawio 7 trang) + nới nguyên tắc reasoning + spec lọc rủi ro nguồn cộng đồng

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo plan đã Cường duyệt
- **Loại:** docs / diagram / scope-refinement
- **TODO / User story liên quan:** T-014 (DONE), T-015 (mới), T-005 (CrewAI — nhắc lại), D-008 (mới)

## Tóm tắt

Theo yêu cầu Cường: vẽ lại luồng (giống v1) bám scope F0–F3 + tính năng tương lai, có cả kế hoạch kiểm soát rủi ro lọc thông tin nguồn cộng đồng; đồng thời review/nới nguyên tắc "AI agent chỉ tổng hợp/so sánh/giải thích". 4 quyết định thiết kế đã hỏi-duyệt qua plan mode; plan được duyệt (có bổ sung phần cập nhật docs liên quan).

## Chi tiết cập nhật

### Nới nguyên tắc reasoning (phần định hướng cố định — Cường duyệt)
"AI agent chỉ tổng hợp/so sánh/giải thích" → agent **chủ yếu** tổng hợp/so sánh/giải thích, **được đảm nhiệm một vài bước reasoning** khi sub-problem chưa có cách tối ưu hóa/mô hình hóa quá phức tạp. Guardrail giữ: số tài chính/policy vẫn từ rule/analytics; reasoning phải log + gắn độ tin cậy + tắt được về rule/template. Sửa ở `CLAUDE.md` §1+§5, `planning/SCOPE.md` §1, `README.md`.

### Drawio v2 (7 trang)
`flow image/GSM_Driver_Income_AI_Agentv2.drawio`: L0 tổng quan · L1 kiến trúc thành phần · L2 luồng hoạt động · F0 hỏi đáp chính sách · F1 trước ca · F2 trong ca · F3 sau ca. Giữ bảng màu v1; **nét đứt = tính năng tương lai**; khối AI Agent ghi "reasoning có điều kiện"; khối **FILTER-F1 "Kiểm chứng & lọc rủi ro"** cho nguồn cộng đồng; state pin (F2) và community source vẽ nét đứt; dispatch/pricing/reposition = ngoài scope (đỏ). v1 giữ để đối chiếu (không xóa).

### Spec lọc rủi ro nguồn cộng đồng
`specs/community-source-risk-control.md` (mới): phân hạng nguồn T1–T4 (chặn domain giả official), pipeline 6 bước (nhận diện tier → chống lỗi thời → lọc PII → chống tin sai → chống lời khuyên lách luật → gắn metadata), ranh giới sử dụng (chỉ định tính, không thành số tài chính/policy), human review + audit + thu hồi. Khối trong drawio trỏ tới file này.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| flow image/GSM_Driver_Income_AI_Agentv2.drawio | tạo | 7 trang, XML validate OK (parse [xml], đủ 7 diagram) |
| specs/community-source-risk-control.md | tạo | kế hoạch kiểm soát rủi ro lọc thông tin |
| CLAUDE.md | sửa | §1 nguyên tắc reasoning + flow ref v2 + bản đồ repo; §5 thêm 2 ranh giới (reasoning log/fallback, nguồn cộng đồng qua lọc) |
| planning/SCOPE.md | sửa | §1 nguyên tắc reasoning + flow ref v2; §2 thêm mục tính năng tương lai |
| README.md | sửa | bullet nguyên tắc + mục flow image v2 |
| tracking/DEFERRED.md | sửa | thêm D-008 (community insights = roadmap) |
| tracking/TODO.md | sửa | fix header (self-claim); thêm T-014 (DONE), T-015 (tương lai) |

## Docs đã cập nhật kèm theo

CLAUDE/SCOPE/README (nguyên tắc + flow ref), DEFERRED (D-008), TODO (T-014/T-015 + header). PERSONAS/USER_STORIES: không đổi trong update này.

## Kiểm chứng

- `flow image/GSM_Driver_Income_AI_Agentv2.drawio`: parse `[xml]` OK, đúng **7 trang**; đã sửa 1 typo `vertex="bd"` → `vertex="1"` (cell RULE ở L0). Chưa mở bằng draw.io GUI để soi layout pixel — đề nghị Cường mở app.diagrams.net để review trực quan.
- Không có code chạy. Chưa kiểm chứng: bố cục hình trực quan (chờ Cường xem), nội dung spec lọc rủi ro (chờ review).

## Follow-up / defer phát sinh

- **Chờ Cường duyệt bản vẽ v2** trước khi sang T-009 (UI clone) — theo đúng plan Phần D.
- T-015 + D-008: tích hợp nguồn cộng đồng (tương lai) theo spec vừa tạo.
- Gợi ý: nếu Cường muốn, xuất PNG từng trang v2 để đưa vào docs/README.
