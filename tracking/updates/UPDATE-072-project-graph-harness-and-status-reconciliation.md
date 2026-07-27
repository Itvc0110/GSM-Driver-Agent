# UPDATE-072 — Project graph, graph-first harness và reconcile task status

- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent theo yêu cầu của Cường
- **Loại:** docs / governance / harness
- **TODO / User story liên quan:** T-018, T-026, T-030, T-038, UX-CARDS, R1/R4, AUDIT-A1/A2/A3, R5-A/R5-B, T-039

## Tóm tắt

Tạo `tracking/PROJECT-GRAPH.md` làm canonical reading map cho toàn bộ 66 UPDATE hiện hành; mỗi UPDATE có link file thật, topic/status/dependency/correction edge và route đọc theo task. Harness chuyển sang graph-first để agent không đọc lại toàn bộ lịch sử, đồng thời áp quota cap 2 và queue `2 → 2 → 1`.

Audit song song đã reconcile các task code-complete nhưng tracking còn `TODO`/`VALIDATING`/`DOING`, vẫn giữ riêng những mục `WAITING-VERDICT`, `BLOCKED` hoặc `QUOTA-BLOCKED`.

## Chi tiết cập nhật

1. **Graph canonical**
   - 66 linked UPDATE nodes (`001–012`, `019–072`), không tính template; `013–018` không phải canonical files sau numbering integration.
   - Current-state board, route matrix, open/legacy TODO-ID routes, open-work ledger, conflict/staleness ledger và dynamic link validation.
   - Correction edges bắt buộc: 036→035, 048→047, 053→051, 071→audit overclaim.
2. **Harness routing**
   - `CLAUDE.md` và `README.md` đọc graph sau harness, mở source docs/correction chain theo route thay vì đọc lại 65+ UPDATE.
   - Status vocabulary: `HISTORY-COMPLETE`, `DONE-CODE`, `WAITING-VERDICT`, `QUOTA-BLOCKED`, `CORRECTED`.
   - Parallel cap 2; 5 sessions queue `2 → 2 → 1`; quota error persist partial + một retry + hạ cap 1.
3. **Status reconciliation từ evidence**
   - T-026/T-038 → `DONE-CODE`; T-018/T-030 → `WAITING-VERDICT`.
   - Legacy T-018/Track UI claims chuyển xuống history/released; T-009b của Khánh giữ `READY` active scope.
   - Đăng ký UX-CARDS, R1/R4, AUDIT A1/A2/A3, R5-A, R5-B trong TODO.
   - D-POL-01/02 → `DONE-CODE / BLOCKED D-POL-05`; D-POL-03 → `PARTIAL / BLOCKED D-POL-05`.
   - D-SIM-02/D-SIM-06 code-complete; D-SIM-12 superseded; D-EXT-02 closed bởi OSRM+Stadia.
   - V-07 superseded bởi D-SIM-10/UPDATE-052; các visual verdict khác vẫn mở.
   - Audit summary sửa theo UPDATE-071: 179 findings, 21 fix rows; 152 agents/118 confirmed giữ nguyên.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `tracking/PROJECT-GRAPH.md` | tạo | Canonical graph, routes, quota loop, validation |
| `CLAUDE.md` | sửa | Graph-first bootstrap, status vocabulary, quota guard |
| `README.md` | sửa | Reading order mới |
| `tracking/TODO.md` | sửa | Reconcile completed/post-audit tasks |
| `tracking/DEFERRED.md` | sửa | Reconcile completed/superseded/dependency-blocked items |
| `tracking/ASSIGNMENTS.md` | sửa | Release legacy T-018/Track UI claims; giữ T-009b |
| `tracking/PENDING-REVIEW.md` | sửa | V-07 superseded; human visual gates khác giữ nguyên |
| `tracking/DIRECTIVES-2026-07-24.md` | sửa | Audit count/status correction |
| `tracking/updates/UPDATE-072-project-graph-harness-and-status-reconciliation.md` | tạo | Update này |

## Docs đã cập nhật kèm theo

`CLAUDE.md`, `README.md`, `TODO`, `DEFERRED`, `ASSIGNMENTS`, `PENDING-REVIEW`, `DIRECTIVES` và graph đã đồng bộ. `SCOPE`, `USER_STORIES`, specs và runtime contracts không đổi.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| Có 66 canonical UPDATE sau khi tạo UPDATE-072 | `FACT` | filesystem enumeration, exclude template | Cao | validation/link coverage sai |
| T-026/T-038 code-complete | `OBSERVED-CODE/DOC` | UPDATE-024/025/030/034..039 + TODO evidence | Cao | task bị đóng sớm |
| T-018/Track UI không còn active implementation | `OBSERVED-DOC` | successor UPDATE-044..063/067/068; claims cũ | Cao | ownership/edit conflict |
| Cap 2 và queue 2→2→1 giảm quota risk | `DECISION` | user chọn; failures UPDATE-064/071 | Cao | audit chậm hơn nhưng không đổi product behavior |
| Pending visual verdicts chưa đóng | `FACT` | `PENDING-REVIEW.md` ✅ section trống | Cao | overclaim reviewed/complete |

## Kiểm chứng

- Dynamic graph coverage: mỗi UPDATE file phải có exact relative link trong graph.
- Required tracking sources exist; correction edges and quota rule present.
- `git diff --check` phải sạch.
- Docs-only: không chạy runtime suite; không claim code/simulation/UI behavior mới.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
|---|---|---|---|---|
| Graph/link/status validation | N/A | 66 UPDATE docs | `PROJECT_GRAPH_VALIDATION_OK` khi chạy cuối cycle | Runtime/visual unchanged and not rerun |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** docs-only graph/harness update
- **Seed / scenario đã xem:** N/A
- **Người review + verdict:** AI self-review + read-only reviewer; no UI/simulator output changed
- **Lý do:** không thay đổi visual encoding, runtime output hoặc interaction.

## Adversarial self-review / flaws found

1. Hard-code count 65 sẽ hỏng ngay khi tạo UPDATE-072 → validation đổi sang dynamic exact-link coverage; current count cập nhật 66.
2. Graph chỉ ghi `UPDATE-###` không đủ kiểm path → mọi node đổi sang link full filename.
3. `DONE` có thể che visual gate → dùng `DONE-CODE / WAITING-VERDICT`; V-01..V-06, V-08..V-10 giữ mở.
4. Reconcile claim có thể đụng ownership → chỉ release legacy completed scope; T-009b/contract coordination giữ nguyên.
5. Graph có thể drift sau UPDATE mới → `CLAUDE.md` bắt graph update trong cùng coherent cycle và validation kiểm mọi UPDATE file.

## Expansion checkpoint (T-039)

1. **Schema:** không đổi runtime schema; graph status vocabulary chỉ là interface tài liệu.
2. **Bài toán tối ưu:** không phát sinh solver mới; ĐA-01..06 và D-A3-01..06 giữ chờ quyết định.
3. **Tính năng:** graph-first context routing và quota batching là harness capability; không phải feature cho tài xế.

## Follow-up / defer phát sinh

- R5-B vẫn `QUOTA-BLOCKED`; chạy lại khi session/quota cho phép.
- V-01..V-06, V-08..V-10; Q-03; ĐA-01..06 vẫn phải nhắc lại sau UPDATE.
- Mỗi UPDATE mới phải thêm link/node/edge vào graph trong cùng cycle.
