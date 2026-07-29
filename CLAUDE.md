# CLAUDE.md — Harness cho AI coding agent (GSM Driver Income Agent)

Cập nhật: 2026-07-29. Đây là file điều khiển hành vi bắt buộc cho mọi AI coding agent làm việc trong repo này. Khi có xung đột giữa file này và tài liệu khác, **file này thắng** (trừ khi Cường/Khánh nói khác trực tiếp trong hội thoại).

## 1. Dự án là gì

Hệ thống AI hỗ trợ tài xế Xanh SM (GSM) cải thiện thu nhập: trả lời chính sách/thưởng phạt theo hồ sơ tài xế, tư vấn trước ca – trong ca – sau ca. Team 2 người: **Cường** và **Khánh**.

**CỐ ĐỊNH (không được tự thay đổi):** problem statement, mục tiêu, và định hướng giải pháp — bản chất là bài toán tối ưu đa biến có ràng buộc, nhưng tiếp cận **top-down** (flow-first): mọi số tài chính/policy do rule/analytics tính (agent không tự bịa số), **agent chủ yếu tổng hợp, so sánh, giải thích**; agent **có thể đảm nhiệm một vài bước reasoning** khi sub-problem chưa có cách tối ưu hóa hoặc mô hình hóa quá phức tạp so với reasoning thuần — nhưng phải log, gắn độ tin cậy, tắt được về rule/template (tinh chỉnh được Cường duyệt 2026-07-20). Chưa mô hình hóa từ atomic features.
**LINH HOẠT (được đề xuất thay đổi qua plan mode):** kiến trúc, stack, chi tiết feature, UI.

Scope hiện hành: đọc `planning/SCOPE.md`. Luồng dự kiến: `flow image/GSM_Driver_Income_AI_Agentv2.drawio` (bản hiện hành — 7 trang: L0–L2 tổng quan/thành phần/luồng + F0–F3 chi tiết; nét đứt = tính năng tương lai); `...v1.drawio` giữ để đối chiếu. Luồng giải trình vi phạm thuộc **dự án khác** — file drawio đã xóa khỏi repo theo yêu cầu Cường (D-006).

## 2. Bản đồ repo

| Đường dẫn | Vai trò |
| --- | --- |
| `CLAUDE.md` | Harness này — đọc đầu tiên |
| `planning/` | SCOPE (scope hiện hành), USER_STORIES, PERSONAS (5 hồ sơ mock), RESEARCH (kế hoạch nghiên cứu) |
| `research/` | Kết quả nghiên cứu, **chia theo loại** (`policy/`, `economics/`, `community/`, `market/`, `simulation/`, `audit/`, `experiments/`, `ux/`) — xem `research/README.md`; đọc trước `research/00_SUMMARY.md` |
| `specs/` | Đặc tả kỹ thuật để code — **14 spec cấp 1 + `real-data/` + `simulation/`**; spec source-of-truth chính hiện hành: `advisor-objective-model-v2.md`, `core-data-schema-and-advisor-architecture.md`, `adherence-measurement.md`, `simulation/00-sim-overhaul-master.md` |
| `tracking/` | TODO (backlog), ASSIGNMENTS (bảng tự nhận việc — không ai giao việc), DEFERRED (mục đã hoãn), `updates/` (nhật ký thay đổi UPDATE-###), `PENDING-REVIEW.md`, `OPEN-THREADS-*.md`, `PLAN-cycle-*.md`, `DIRECTIVES-*`, `BACKLOG-QUESTIONS-*` |
| `tracking/PROJECT-GRAPH.md` | Bản đồ canonical của UPDATE hiện hành: route đọc theo task, dependency/correction edges, trạng thái hiện hành, pending gates và quota loop. **90 file `UPDATE-*.md` tính tới UPDATE-096 (2026-07-29); §3.7 phủ 074–093, route đọc theo task ở `PROJECT-GRAPH-2026-07-29-addendum.md`** |
| `flow image/` | drawio luồng dự kiến — `...v2.drawio` hiện hành (7 trang), `...v1.drawio` đối chiếu (source of truth về flow) |
| `docs/00–09`, `contracts/`, `templates/`, `MASTER_PROMPT.md`, `AGENTS.md` | **DEFERRED** — pack cũ theo hướng full optimization scaffold; chỉ dùng tham khảo, không phải scope hiện hành |
| `docs/data-catalog/` | **ACTIVE** — catalog 13 bảng GSM thật (`gsm-data-catalog.csv/.xlsx`), sinh bởi `scripts/build_data_catalog.py`; `specs/real-data/*` phụ thuộc trực tiếp, KHÔNG deferred |
| `docs/superpowers/` | **ACTIVE** — artifact plan/spec của UI-FARE-01 (UPDATE-073, chờ V-16), không thuộc pack DEFERRED D-001 |
| `src/gsm_core/` | Core solvers (S1–S9), advisor pipeline C6, `lifecycle/` (event log + projections), `schema_registry.py` + `upcasters.py`, `mockgen/` |
| `src/gsm_sim/` | Simulator/twin-world engine (world, dispatcher, actors, parallel A/B/C, dashboard) |
| `schemas/` | JSON Schema đa phiên bản (`{entity}@{ver}.schema.json`) + `CHANGELOG.md` |
| `configs/pilot_dongda.yaml` | Config pilot hiện hành (actors, dispatcher, positioning, policy costs) — nguồn sự thật cho mọi số cấu hình sim |
| `tests/` | ~707 test (suite hiện hành sau Cycle W) |
| `ui/` | `backend/` FastAPI chung, `web/` (Track UI), `driver_app/` (Flutter của Khánh), `contracts/` (JSON Schema versioned + design tokens) |
| `scripts/` | Script vận hành/regen/verify (vd `regen_mock.py`, `run_parallel.py`, `build_data_catalog.py`) |
| `data/` | Mock data (gitignored telemetry/parquet); không commit data thật |

## 3. Quy trình BẮT BUỘC trước khi làm bất kỳ việc gì

1. **Bootstrap theo graph, không đọc lại toàn bộ lịch sử** — đọc `tracking/PROJECT-GRAPH.md` sau file này; chọn route theo task, mở các source docs và correction chain mà graph chỉ ra. `DIRECTIVES-2026-07-24.md` vẫn là nguồn chỉ thị chương trình; `SCOPE`, `TODO`, `DEFERRED`, `ASSIGNMENTS`, **`PENDING-REVIEW.md` (việc Cường đang chờ check — phải NHẮC LẠI sau mỗi update)** được mở đầy đủ khi task chạm scope, status, claim, policy, UI/sim output hoặc architecture. Không mặc định đọc lại toàn bộ UPDATE.
2. **Vào plan mode trước** (EnterPlanMode) với mọi thay đổi code, cấu trúc, contract hoặc docs quan trọng. Trong plan mode, **phải hỏi lại** (AskUserQuestion) những điểm chưa rõ hoặc quan trọng (ảnh hưởng scope, dữ liệu, ranh giới sản phẩm, phân công) trước khi chốt plan. Không tự đoán rồi làm.
3. **Tôn trọng bảng tự nhận việc** `tracking/ASSIGNMENTS.md`: không có ai là người giao việc — Cường/Khánh **tự claim** việc đầu mỗi session. Agent làm việc **dưới claim của người đang điều khiển nó**: kiểm tra bảng claim trước khi sửa file, không tự claim, không làm ngoài phạm vi claim, không đụng files trong claim đang hoạt động của người kia.
4. **Defer thay vì phình scope**: ý tưởng/việc ngoài minimum scope → ghi vào `tracking/DEFERRED.md` (kèm lý do + điều kiện mở lại), không tự triển khai.
5. **Parallel/quota guard**: tối đa 2 phiên đồng thời (primary + reviewer). Nếu cần 5 phiên, queue `2 → 2 → 1`; persist findings/decision/failure trước batch kế tiếp. Quota/session-limit lỗi: retry tối đa một lần, sau đó ghi `QUOTA-BLOCKED` và hạ cap xuống 1. Không mở worker thứ hai trên cùng claim/path.

## 4. Quy trình BẮT BUỘC sau khi thay đổi

Sau mỗi thay đổi có ý nghĩa (code, docs, data, cấu trúc), tạo file `tracking/updates/UPDATE-###-<slug>.md` theo `tracking/updates/UPDATE_TEMPLATE.md`. Các trường bắt buộc phải điền đủ, đặc biệt:

- **Files bị ảnh hưởng** (đường dẫn cụ thể, tạo/sửa/xóa);
- **Chi tiết cập nhật** (cái gì đổi, vì sao);
- **Docs đã cập nhật kèm theo** (SCOPE/TODO/DEFERRED/USER_STORIES có đổi không);
- **Kiểm chứng** (đã test/chạy thử gì, cái gì chưa kiểm chứng);
- **Follow-up/defer** phát sinh.

Đồng thời cập nhật trạng thái mục tương ứng trong `tracking/TODO.md` và node/cạnh liên quan trong `tracking/PROJECT-GRAPH.md`. Thay đổi không có UPDATE đi kèm được coi là chưa hoàn thành. Graph là index, không thay thế evidence trong UPDATE hoặc source docs.

Trạng thái routing chuẩn: `HISTORY-COMPLETE`, `DONE-CODE`, `WAITING-VERDICT`, `READY`, `DOING`, `BLOCKED`, `QUOTA-BLOCKED`, `DEFERRED`, `CORRECTED`. Không gọi một mục là `DONE`/`reviewed` khi `PENDING-REVIEW` còn mở; dùng `DONE-CODE` hoặc `WAITING-VERDICT`.

## 4b. Quy trình implementation, debug, self-review và visual verification BẮT BUỘC

### Coherent implementation cycle

- Trước mỗi **coherent implementation cycle** có thay đổi code, simulation behavior, UI, data contract, architecture hoặc docs quan trọng, agent phải **brainstorm để xác nhận mục tiêu/assumption/ranh giới/acceptance**, sau đó mới vào **plan mode** và xin duyệt plan trước khi implement. Một cycle là một deliverable nhất quán, test/review/commit độc lập được; không cần brainstorm/plan riêng cho từng dòng, từng red-green step, typo hoặc chỉnh câu không đổi nghĩa.
- Phải brainstorm/plan lại nếu scope vượt milestone đã duyệt, assumption chính thay đổi, root cause thực tế khác plan, hoặc cycle đã phình đến mức không còn review được như một khối độc lập.

### Root-cause protocol cho bug/output bất thường

Khi thấy crash, nondeterminism, impossible state, metric shift không giải thích được, visual inconsistency hoặc seed-specific anomaly, **không sửa ngay theo phỏng đoán**. Bắt buộc theo chuỗi:

`reproduce → classify (BUG / MODEL GAP / CALIBRATION GAP / VISIBILITY GAP) → compare baseline → instrument → prove root cause → thêm failing regression test → narrow fix → verify multi-seed + boundary + full suite → adversarial self-review`.

- Chưa reproduce hoặc chưa chứng minh root cause thì ghi `UNRESOLVED`, không ghi “fixed”.
- Không được chỉnh calibration để che BUG. External-data/infrastructure failure phải có deterministic fixture/reproduction ở đúng boundary, không sửa domain logic để che lỗi.
- Mặc định: deterministic invariant/bug phải exact-repeat; stochastic behavior regression chạy **ít nhất 5 seeds**; distribution/calibration chạy **ít nhất 30 seeds** với tolerance/CI. Plan có thể chọn số khác nếu giải thích statistical power/cost.

### Adversarial self-review trước khi báo hoàn thành

Phải double-check tối thiểu:

- lifecycle/terminal state và time/money/battery/order conservation;
- future-information leak, CRN drift, random stream contamination;
- factor double-count, hidden clipping/fallback, unit mismatch;
- config flag có thực sự được dùng và disabled factor có quay về baseline;
- UI có đọc canonical source-of-truth hay tự recompute khác engine/evaluator;
- MOCK/PROXY/ASSUMPTION có nhãn, nguồn và confidence;
- seed/scenario nào có thể làm kết luận đảo chiều;
- flaw mới đã map vào TODO/DEFERRED với severity/evidence/reopen condition.

UPDATE phải có mục `Adversarial self-review / flaws found`; không được bỏ qua vì test xanh.

### Visual review gate

- Sau mọi **meaningful simulator hoặc UI update** (dynamics, default parameter/assumption, metric/output, visual encoding, control, interaction hoặc cách stakeholder diễn giải kết quả), agent phải launch dashboard/replay thật, mở seed/scenario đã ghi cho Cường xem và chờ verdict **trước commit/push**, trừ khi Cường waive tường minh trong hội thoại hiện tại.
- Docs-only, test-only hoặc refactor đã chứng minh không đổi output có thể ghi `NOT_APPLICABLE` kèm lý do. Launch lỗi thì status là `BLOCKED`; không được gọi update là complete/reviewed cho tới khi fix hoặc được waive.
- Gate này không tự cấp quyền commit/push: vẫn chỉ commit/push khi người dùng yêu cầu.

### Evidence và UPDATE tối thiểu

Mỗi UPDATE phải ghi: nhãn evidence/assumption + confidence, seed/scenario thực chạy, cái chưa kiểm chứng, visual status (`REVIEWED / WAIVED / NOT_APPLICABLE / BLOCKED`), root cause/giả thuyết đã loại trừ nếu là bug, và adversarial flaw review. Template tại `tracking/updates/UPDATE_TEMPLATE.md` là bắt buộc.

## 5. Ranh giới sản phẩm (giữ nguyên từ pack cũ — vẫn có hiệu lực)

- Agent/LLM **không tự tính** số liệu tài chính/xác suất — mọi con số hiển thị cho tài xế đến từ rule/analytics component có thể kiểm chứng; agent chỉ diễn giải. Tiền phải tách `gross revenue` / `driver payout` / `estimated net income`; payout là mục tiêu mặc định, estimated net chỉ khi đủ known costs + definition/version.
- **Không** khuyên nhận/từ chối/hủy một đơn cụ thể; không can thiệp matching, dispatch, pricing, routing.
- **Không hứa chắc** mức thu nhập; luôn nêu bất định/điều kiện. Không dạy lách chính sách/phạt.
- Trả lời chính sách phải dựa trên **nguồn có trích dẫn** (policy đã lưu trong knowledge base, có version); không bịa chính sách.
- **Mock data phải gắn nhãn mock** (seed, nguồn, ngày tạo); không trình bày số mock như số thật của GSM; không trộn mock với dữ liệu thật.
- Hệ thống **không tự thực thi** thay tài xế; tài xế luôn là người quyết định.
- **Reasoning của agent** (khi được phép) phải để lại log + mức tin cậy và có đường **fallback về rule/template** khi tắt; không để reasoning tạo ra số tài chính/policy.
- **Nguồn cộng đồng** (group tài xế, websearch kinh nghiệm — tính năng tương lai) phải qua bước **kiểm chứng & lọc rủi ro** (`specs/community-source-risk-control.md`): ưu tiên nguồn official, chống tin sai/lỗi thời/PII/nguồn giả; không dùng cho số tài chính/policy.

## 6. Quy ước làm việc

- Ngôn ngữ tài liệu và giao tiếp: **tiếng Việt** (thuật ngữ kỹ thuật giữ tiếng Anh).
- Tên file/folder: tiếng Anh, kebab-case hoặc như cấu trúc sẵn có.
- Commit khi được yêu cầu; message tiếng Anh ngắn gọn, thân tiếng Việt nếu cần.
- Ưu tiên mobile-first cho mọi UI (tài xế dùng app trên điện thoại).
