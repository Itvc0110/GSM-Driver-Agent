# UPDATE-006 — Đồng bộ checkpoint scope v2 + hoàn thiện flow trước merge

- **Ngày:** 2026-07-20
- **Người thực hiện:** AI agent (Claude Code), theo yêu cầu trực tiếp và plan được Cường duyệt
- **Loại:** docs / diagram / refactor / fix
- **TODO / User story liên quan:** T-003 (READY), T-009 (chưa mở), T-011 (follow-up), T-014 (VALIDATING)

## Tóm tắt

Audit lại toàn bộ repo sau khi branch `feat/scope-v2-scaffold` được push nhưng chưa merge. Giữ working diff drawio có chủ ý, sửa layout/wording/style; đồng bộ docs active sau research/reorg; chuẩn hóa money terms; dọn tracked ZIP. **Cường đã duyệt flow và yêu cầu commit ngày 2026-07-20; T-014 chuyển DONE.**

## Chi tiết cập nhật

1. Chuẩn hóa 3 lớp tiền:
   - `gross revenue`: doanh thu trước chia nền tảng;
   - `driver payout`: sau platform share + eligible bonus/adjustment, là mục tiêu mặc định;
   - `estimated net income`: payout trừ known driver-borne costs, chỉ hiển thị khi đủ dữ liệu + definition/version/completeness.
2. Drawio v2:
   - đưa L0 về canvas;
   - F0 không còn cho phép agent suy policy khi KB thiếu;
   - threshold/mốc thưởng lấy từ Policy KB/config versioned, không hard-code universal;
   - tách style future/fallback/out-of-scope;
   - F2 dùng mock demand proxy để tư vấn theo thời gian, không mô hình hóa matching/reposition;
   - community filter bổ sung human review/audit/revoke.
3. Research/specs:
   - cập nhật trạng thái research hoàn tất đợt 1+2;
   - sửa links/reorg/no-OCR contradictions;
   - T4 source chỉ là blocked lead;
   - `Hủy chuyến hợp lệ` không coi là Bike policy fact;
   - mock demand weights được normalize; weather formula thống nhất; Nội Bài bỏ khỏi Bike; demand tách matching/availability.
4. Tracking:
   - T-003 → READY (spec xong, code chưa claim);
   - T-014 → VALIDATING;
   - T-009 giữ TODO cho vòng hỏi/plan riêng sau merge;
   - T-011 bổ sung money definition/versioning.
5. Git hygiene:
   - ignore `.claude/worktrees/`;
   - xóa tracked source archive `driver-income-os-ai-pack.zip`; history vẫn giữ snapshot;
   - không chạm backup drawio/tool worktrees.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `.gitignore` | sửa | ignore Claude worktrees |
| `driver-income-os-ai-pack.zip` | xóa | theo quyết định Cường; pack đã giải nén |
| `flow image/GSM_Driver_Income_AI_Agentv2.drawio` | sửa | giữ user working diff + hoàn thiện 7 trang |
| `CLAUDE.md`, `README.md` | sửa | money terminology / archive note |
| `planning/SCOPE.md` | sửa | money definitions, demand proxy boundary, research status |
| `planning/PERSONAS.md` | sửa | payout/net convention; policy/track/TBD fixes |
| `planning/RESEARCH.md` | viết lại | trạng thái hoàn tất + nơi lưu |
| `planning/USER_STORIES.md` | sửa | money terms, demand proxy, no-reposition, post-shift pattern wording |
| `research/00_SUMMARY.md` | viết lại | links + đợt 2 + no-OCR |
| `research/policy/bonus-programs.md` | sửa | gaps/version/T4/no-OCR |
| `research/economics/income-structure.md` | sửa | bỏ OCR follow-up |
| `research/community/pain-points.md` | sửa | Hủy hợp lệ không phải Bike fact |
| `research/community/community-insights.md` | sửa | T4 lead; simulation-only zone; không mock Bike policy |
| `specs/mock-order-distribution.md` | viết lại | demand proxy, normalize, weather, money layers |
| `specs/community-source-risk-control.md` | sửa | T4 block + no-reposition boundary |
| `tracking/TODO.md` | sửa | READY/VALIDATING/T-009/T-011 |
| `tracking/updates/UPDATE-006-...md` | tạo | log checkpoint này |

## Docs đã cập nhật kèm theo

- SCOPE: có.
- TODO: có.
- RESEARCH: có.
- PERSONAS: có.
- USER_STORIES: có (money definitions + demand proxy/no-reposition).
- DEFERRED: không đổi; ranh giới D-004/D-007/D-008 giữ nguyên.
- UPDATE-001…005: không sửa (append-only history).

## Kiểm chứng

- Drawio: parser đã parse XML thành công sau vòng sửa mục tiêu đầu; đúng 7 page và graph refs sạch. Sau các exact XML replacements cuối, kiểm tra read/search xác nhận vẫn đúng 7 `<diagram>` theo thứ tự L0/L1/L2/F0/F1/F2/F3; không xóa/đổi ID; edge mới chỉ trỏ `input → flow` (ID tồn tại).
- Geometry: audit trước sửa chỉ báo 4 root vertex L0 ngoài canvas; đã đưa tất cả vào page 1600×900. Search sau sửa không còn root vertex có x/y âm hoặc vượt page; giá trị âm còn lại là edge label offset tương đối, không phải vertex.
- Style/semantic: `dashed=1` chỉ còn ở Community/Filter/State pin và các edge tương lai; fallback/veto/out-of-scope/feedback đã dùng style riêng. Không còn wording `reasoning nếu KB chưa phủ`, threshold `≥70%`, mốc `10đ/1.400` trong drawio.
- Active-doc scan: không còn stale path `planning/research`/`research/bonus-programs`; OCR chỉ còn ở quyết định `không OCR`; Nội Bài được loại khỏi Bike spec; `Hủy chuyến hợp lệ` ghi rõ chưa xác nhận cho Bike; T4 domain chỉ là blocked lead.
- Artifact scan: không còn ZIP trong workspace; backup drawio vẫn tồn tại nhưng khớp ignore `*.bkp`; `.claude/worktrees/` được ignore.
- Các lần chạy Workflow/Agent/shell verifier cuối bị chặn **trước execution** do model safety classifier của harness tạm unavailable; không ghi nhận chúng như test pass/fail của repo. Sẽ rerun parser + Git status trước commit khi harness phục hồi.

**Visual approval:** Cường xác nhận và yêu cầu commit ngày 2026-07-20; T-014 = DONE.

**Hạn chế kiểm chứng:** parser/Git shell preflight cuối đã được gọi nhiều lần nhưng bị safety classifier của harness tạm unavailable và chặn trước execution. Parser trước vòng exact replacements cuối đã pass XML; sau đó Read/Grep xác nhận 7 page tags, refs không bị đổi/xóa, root geometry đã vào canvas và semantic checks sạch. Sẽ tiếp tục retry Git/preflight trước commit; không ghi tool call bị chặn như một PASS.

## Follow-up / defer phát sinh

- T-011: contract v2 phải định nghĩa money fields + policy bundle version + completeness.
- T-009: vòng thông báo/hỏi/plan riêng sau khi checkpoint merge.
- Không mở lại contracts/optimizer cũ; không implement reposition/community product trong checkpoint này.
