# SPEC — Kiểm chứng & lọc rủi ro nguồn cộng đồng

Cập nhật: 2026-07-20 · Trạng thái: spec cho **tính năng tương lai** (D-008; nét đứt trong `flow image/GSM_Driver_Income_AI_Agentv2.drawio`, khối FILTER-F1). Chưa build; đây là kế hoạch kiểm soát rủi ro để khi mở tính năng thì có sẵn ranh giới.

## 1. Bối cảnh & mục tiêu

Nguồn cộng đồng = thông tin từ group Facebook tài xế, YouTube/TikTok, diễn đàn (VOZ/otofun), websearch kinh nghiệm (xem `research/community/`). Giá trị: mẹo thực chiến (khu đứng chờ, dead hours, trạm pin quá tải) mà nguồn official không có. Rủi ro: **tin sai, tin lỗi thời, tin bịa, PII, nguồn giả mạo official, lời khuyên lách luật**. Spec này định nghĩa cách để giá trị đi vào hệ thống mà rủi ro bị chặn.

**Nguyên tắc số 1 (bất biến):** thông tin cộng đồng **chỉ bổ sung ngữ cảnh/gợi ý định tính**, **KHÔNG bao giờ** trở thành số tài chính/policy hiển thị cho tài xế. Mọi con số tiền/thưởng/phạt/tỷ lệ vẫn chỉ đến từ Policy KB (official, có version) + rule/analytics.

## 2. Phân hạng nguồn (source tier)

| Tier | Nguồn | Được dùng cho |
| --- | --- | --- |
| T1 official | greensm.com / xanhsm.com, app tài xế, văn bản pháp luật | Số tài chính/policy, câu trả lời F0 có trích dẫn |
| T2 press | báo uy tín (VnExpress, Tuổi Trẻ, CafeF…) | Ngữ cảnh, đối chiếu; số chỉ khi khớp T1 |
| T3 community | group FB, forum, video tài xế, blog tuyển dụng | **Chỉ** gợi ý định tính (khu đứng, dead hours, mẹo pin), gắn nhãn "kinh nghiệm cộng đồng — chưa kiểm chứng" |
| T4 blocked | nguồn giả official (`bike-xanhsm.com`, `xanhsmbike.com`, `taixexanhsm.com`, `xanhsmcar.com`…), nội dung ẩn danh không truy vết | Không dùng làm nguồn; chỉ lead để tìm nguồn T1/T2 |

## 3. Pipeline lọc (khối FILTER-F1)

Mỗi mẩu thông tin cộng đồng đi qua 6 bước, fail bất kỳ bước nào → loại hoặc hạ cấp:

1. **Nhận diện nguồn & tier** — map domain/handle về tier; T4 loại ngay. Cảnh giác domain nhái official.
2. **Chống lỗi thời** — gắn ngày nguồn; chính sách Xanh SM đổi rất nhanh → thông tin >90 ngày về policy phải kiểm lại với T1 hiện hành; quá hạn mà không đối chiếu được → loại khỏi phần policy.
3. **Lọc PII** — bỏ số điện thoại, biển số, tên thật, vị trí nhà, ảnh chứng minh; không lưu raw chat.
4. **Chống tin sai/bịa** — claim định lượng phải khớp ≥1 nguồn T1/T2; claim mâu thuẫn official bị đánh dấu "trái policy", không hiển thị như sự thật.
5. **Chống lời khuyên lách luật** — loại nội dung dạy né phạt/gian lận/chạy ngoài app/thao túng vị trí (đây là guardrail sản phẩm, không được "mua" bằng giá trị thông tin).
6. **Gắn metadata** — mỗi mẩu qua lọc mang: `source_tier`, `source_url`, `source_date`, `confidence` (community tối đa medium), `verified_against` (nguồn T1/T2 nếu có), `is_community=true`.

## 4. Ranh giới sử dụng sau lọc

- Được phép: gợi ý định tính cho **F2** (khu vực/khung giờ tham khảo, trạm pin lệch đỉnh), bổ sung ngữ cảnh cho **F3** (đối chiếu hành vi), làm **lead nghiên cứu** để tìm nguồn official.
- Không được: thay số trong Policy KB; làm căn cứ tính thưởng/phạt/chỉ tiêu; trình bày không kèm nhãn "kinh nghiệm cộng đồng — chưa kiểm chứng".
- Agent khi dùng insight cộng đồng phải **nói rõ đây là kinh nghiệm cộng đồng**, không phải chính sách chính thức, và (nếu có) chỉ ra nguồn official liên quan.

## 5. Con người & kiểm toán

- **Human review** cho batch insight mới trước khi đưa vào knowledge phục vụ tài xế (Ops/Cường-Khánh).
- Log đường đi mỗi insight (nguồn → lọc → dùng ở đâu) để audit & thu hồi khi phát hiện sai.
- Cơ chế thu hồi: một insight bị chứng minh sai → gỡ + đánh dấu nguồn giảm tin cậy.

## 6. Liên kết

- Danh sách group/nguồn cộng đồng đã định danh: `research/community/community-insights.md`.
- Guardrail sản phẩm tổng: `CLAUDE.md` §5. Vị trí trong kiến trúc: khối FILTER-F1 (L1) và nhánh nét đứt F0/L0 trong drawio v2.
- Việc cần người thật: join group đọc nội dung (T-013).
