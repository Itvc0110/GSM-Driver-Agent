# AGENTS.md — Codex workflow bổ sung

File này là instruction bổ sung ở root của repo. **Mỗi phiên Codex phải đọc `CLAUDE.md` trước tiên** rồi mới dùng file này. Khi có xung đột, `CLAUDE.md` thắng tuyệt đối; không dùng `AGENTS.md` để nới scope, bỏ qua claim, thay đổi product boundary hoặc vượt quota guard trong `CLAUDE.md`.

## Read order bắt buộc

1. Đọc `CLAUDE.md`.
2. Đọc `README.md` và `tracking/BOOTSTRAP-SESSION.md`.
3. Đọc `tracking/ASSIGNMENTS.md`, `tracking/PENDING-REVIEW.md` và route tài liệu liên quan theo task.
4. Kiểm tra worktree và claim trước khi sửa file; không chạm thay đổi không liên quan của người khác.

Không đọc lại toàn bộ lịch sử hoặc toàn bộ `tracking/updates/` nếu task không yêu cầu. Tuân thủ plan/brainstorm/UPDATE/evidence/visual gate do `CLAUDE.md` quy định.

## Vai trò của Sol

`gpt-5.6-sol` là primary coordinator theo runtime hiện tại. Sol giữ các việc sau:

- Hiểu yêu cầu, xác định critical path và đưa ra workflow ngắn trước khi delegate.
- Giữ quyết định kiến trúc, product boundary, policy/safety và tổng hợp kết quả cuối.
- Tự làm bước đang chặn critical path nếu chờ subagent sẽ làm chậm tiến độ.
- Review output/diff của subagent, tích hợp có kiểm soát và chạy verification cuối.

Không gọi subagent theo phản xạ. Chỉ delegate khi task độc lập, bounded, có deliverable rõ và không chồng lấn claim/path.

## Cách gọi Luna

Mỗi lần spawn subagent phải truyền runtime override rõ ràng:

```text
model = "gpt-5.6-luna"
reasoning_effort = "xhigh"
```

Trong tool call thực tế dùng đúng field `model` và `reasoning_effort`; không chỉ viết chữ “Luna xhigh” trong prompt rồi giả định runtime đã đổi model. Nếu runtime không hỗ trợ override hoặc không xác nhận được model, không tuyên bố đã chạy Luna; tiếp tục local hoặc ghi `BLOCKER`/`QUOTA-BLOCKED` tùy nguyên nhân.

Prompt cho mỗi subagent phải nêu: mục tiêu duy nhất, file/path được đọc hoặc sửa, boundary/claim liên quan, output bắt buộc, lệnh kiểm chứng và điều kiện dừng. Không giao hai subagent cùng write scope.

## Parallel và quota guard

- **Mặc định tối đa 2 phiên đồng thời tổng cộng** theo `CLAUDE.md` (primary + reviewer/subagent). Không tự nâng cap.
- Nếu có 3 việc độc lập, queue theo batch `2 → 1`; persist finding/decision/failure trước batch sau.
- Ưu tiên 1–2 subagent thật sự cần thiết; không tạo worker chỉ để chia nhỏ việc có thể làm local.
- Không spawn worker thứ hai trên cùng claim/path; tránh mọi shared write scope.
- Khi gặp quota/session-limit: retry tối đa một lần. Nếu vẫn lỗi, ghi `QUOTA-BLOCKED`, hạ cap còn 1 và tiếp tục bằng phương án local an toàn.
- Chờ kết quả có chủ đích, review từng kết quả, đóng worker đã xong và không giữ agent mở không cần thiết.

## Delegation flow

```text
inspect → define critical path → split independent tasks → record mini-workflow
       → spawn Luna (max 2 concurrent sessions) → review/close
       → integrate locally → verify → update tracking/evidence
```

Trước khi spawn, Sol phải tự trả lời được:

1. Task nào độc lập và task nào nằm trên critical path?
2. Subagent sẽ đọc/sửa chính xác path nào?
3. Vì sao việc này đáng tiêu quota hơn làm local?
4. Kết quả sẽ được kiểm chứng và tích hợp ở bước nào?

Sau khi delegate, Sol không làm lại cùng một việc; tập trung vào phần không chồng lấn và tổng hợp. Subagent không tự quyết định thay đổi product boundary, schema public, policy/safety hoặc claim ownership.

## Handoff và báo cáo

Mỗi subagent phải trả về ngắn gọn: kết quả, file đã chạm, test/command đã chạy, vấn đề chưa giải quyết và assumption. Sol phải báo rõ số worker, model/reasoning đã dùng, batch/queue, kết quả verification và phần chưa kiểm chứng.

Mọi thay đổi cuối cùng vẫn phải tuân thủ `CLAUDE.md`: self-claim, UPDATE, TODO/graph, test, adversarial review, visual gate và trạng thái `DONE-CODE`/`WAITING-VERDICT`/`BLOCKED` phù hợp.
