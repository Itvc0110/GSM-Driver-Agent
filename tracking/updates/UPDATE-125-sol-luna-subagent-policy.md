# UPDATE-125 — Cập nhật AGENTS.md cho flow Sol → Luna và quota guard

- **Ngày:** 2026-08-03
- **Người thực hiện:** AI agent — theo yêu cầu trực tiếp của người dùng
- **Loại:** docs
- **TODO / User story liên quan:** `SOL-LUNA-HARNESS` (docs-only, thêm trong `tracking/TODO.md`)

## Tóm tắt

Cập nhật `AGENTS.md` từ pack cũ thành instruction bổ sung cho Codex. Flow mới bắt buộc đọc `CLAUDE.md` trước, Sol phải lập workflow trước khi delegate, subagent phải dùng runtime override Luna `xhigh`, và phải tuân thủ cap 2 phiên của harness hiện hành.

## Chi tiết cập nhật

- `CLAUDE.md` vẫn là source of truth và thắng khi xung đột.
- Mỗi spawn phải truyền `model = "gpt-5.6-luna"` và `reasoning_effort = "xhigh"` bằng field runtime thật.
- Giữ đúng `CLAUDE.md` §3.5: tối đa 2 phiên đồng thời tổng cộng (primary + reviewer/subagent). Ba việc độc lập được queue `2 → 1`, không tự nâng cap.
- Delegate chỉ cho task bounded, độc lập, không chồng claim/path; Sol giữ critical path, quyết định kiến trúc và final synthesis.
- Quota/session-limit retry tối đa một lần; lặp lại thì ghi `QUOTA-BLOCKED`, hạ cap còn 1 và tiếp tục local an toàn.

## Files bị ảnh hưởng

| File | Hành động (tạo/sửa/xóa) | Ghi chú |
| --- | --- | --- |
| `AGENTS.md` | sửa | Thay toàn bộ pack cũ bằng Codex delegation policy hiện hành |
| `docs/superpowers/specs/2026-08-03-sol-luna-subagent-policy-design.md` | tạo | Design đã chốt; ghi rõ runtime boundary và cap của `CLAUDE.md` |
| `docs/superpowers/plans/2026-08-03-sol-luna-subagent-policy.md` | tạo | Plan docs-only và verification |
| `tracking/TODO.md` | sửa | Thêm dòng `SOL-LUNA-HARNESS` ở post-audit docs |
| `tracking/PROJECT-GRAPH.md` | sửa | Thêm link UPDATE-125 vào route harness/docs |
| `tracking/updates/UPDATE-125-sol-luna-subagent-policy.md` | tạo | Nhật ký evidence cho cycle này |

## Docs đã cập nhật kèm theo

`SCOPE`, `DEFERRED`, `USER_STORIES`, `RESEARCH`: không đổi. `TODO` và `PROJECT-GRAPH` đã cập nhật để index cycle docs-only này.

## Assumptions và evidence

| Claim / tham số | Nhãn (`FACT` / `OBSERVED-CODE` / `PROXY` / `MOCK` / `ASSUMPTION` / `UNVERIFIED`) | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` là harness hiện hành và cap mặc định là 2 phiên tổng cộng | `FACT` | `CLAUDE.md` §1, §3.5; `tracking/PROJECT-GRAPH.md` §6 | cao | AGENTS có thể cho phép quá nhiều worker hoặc sai thứ tự đọc |
| Runtime spawn có field override cho model và reasoning effort; Luna hỗ trợ `xhigh` trong phiên hiện tại | `OBSERVED-CODE` | Current-session `multi_agent_v1__spawn_agent` tool schema; `codex --help` xác nhận model override ở CLI | cao | Không thể ép model bằng văn bản nếu runtime field khác |
| `AGENTS.md` là guidance, không phải scheduler cơ học | `FACT` | Design §Runtime boundary; kiểm tra config hiện tại không có subagent registry | cao | Cần review từng tool call để bảo đảm cap/model |

## Kiểm chứng

- `git diff --check`: PASS (exit 0).
- Required-policy scan trên `AGENTS.md`: PASS; có `CLAUDE.md`, `gpt-5.6-luna`, `reasoning_effort = "xhigh"`, cap 2, queue `2 → 1`, `QUOTA-BLOCKED`, critical path và write scope.
- Stale-policy scan: PASS; không còn banner pack cũ, Dev A/Dev B hoặc optimizer-specific rules trong `AGENTS.md`.
- Plan/spec placeholder scan: PASS; không còn `TBD`, `TODO`, hoặc placeholder implementation.
- Scoped tracking scan: PASS; TODO row `SOL-LUNA-HARNESS` và graph link `UPDATE-125` tồn tại.
- Full historical graph-link scan: **UNVERIFIED / pre-existing gap** — còn thiếu link cho `UPDATE-114`, `UPDATE-120`, `UPDATE-121`, `UPDATE-122`, `UPDATE-123`; không sửa vì ngoài scope cycle này.
- Không chạy subagent thật để verify vì sẽ tiêu quota; runtime behavior thực tế chưa được live-smoke trong cycle này.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| Docs/diff verification | N/A | N/A | `git diff --check` + `rg` policy scans PASS | Live spawn model/cap behavior |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** Không có UI, simulator hoặc output visual thay đổi; docs-only.
- **Seed / scenario đã xem:** N/A.
- **Người review + verdict:** N/A.
- **Nếu WAIVED/BLOCKED/NOT_APPLICABLE:** Không áp dụng visual gate vì cycle chỉ sửa instruction và tracking docs.

## Adversarial self-review / flaws found

1. Rủi ro lớn nhất: model/cap không được enforcement bằng `AGENTS.md`; đã ghi rõ phải truyền field runtime và không tuyên bố đã chạy Luna khi không xác nhận được.
2. Yêu cầu “2–3 subagent song song” có thể xung đột với cap 2 phiên trong `CLAUDE.md`; đã fail-closed theo nguồn mạnh hơn và queue `2 → 1`.
3. Không đổi `~/.codex/config.toml`, nên primary vẫn theo config hiện tại; thay đổi model primary nằm ngoài scope.
4. Không có future-information leak, unit mismatch, solver output hoặc visual aggregation trong docs-only cycle.
5. Follow-up còn mở: nếu muốn 2–3 worker ngoài primary chạy đồng thời, người dùng phải cập nhật/duyệt lại cap trong `CLAUDE.md` trước.

## Expansion checkpoint (T-039 — bắt buộc sau mỗi phần hoàn thành)

1. **Schema:** không có.
2. **Bài toán tối ưu:** không có.
3. **Tính năng:** không có; đây là harness/tracking docs-only.

## Follow-up / defer phát sinh

Không phát sinh TODO triển khai. Live-smoke subagent là việc kiểm chứng riêng, chỉ làm khi có task thực tế cần delegate và không gọi chỉ để thử quota.
