# research/ — Kết quả nghiên cứu, chia theo loại tài liệu

Cập nhật: 2026-07-29. Mỗi **loại tài liệu** nằm trong một folder tên rõ ràng. Mọi claim trong đây kèm **nguồn + ngày + độ tin cậy** (`official` > `press` > `community` > `research`). Số chưa xác nhận đánh dấu `TBD`/`MOCK`.

## Cấu trúc folder

| Folder | Loại tài liệu | File hiện có |
| --- | --- | --- |
| `policy/` | Chính sách, thưởng/phạt, quy tắc — dữ liệu để trả lời F0 và tính thưởng F1 | `bonus-programs.md`; **T-004 handoff (Khánh):** `T004_POLICY_SOURCE_REGISTER.md` (7 URL official current + guardrail track), `T004_TEXT_CORPUS_USAGE.md`, `t004-current-policy-text-corpus-2026-07-22.json` (evidence snapshot — **KHÔNG phải KB runtime/prompt context**; **⚠ full-text đang lỗi encoding (mojibake) — cần re-fetch/repair trước khi reviewer dùng**, xem UPDATE-022) |
| `economics/` | Cấu trúc thu nhập, chiết khấu theo hình thức hợp tác, chi phí tài xế | `income-structure.md`; `driver-cost-structure-2026.md` (nguồn official cho `swap_fee_vnd: 0` / `cash_cost_vnd_per_km: 0` — miễn phí đổi pin Platform tới 31/03/2029) |
| `community/` | Pain points, kinh nghiệm thực chiến, thu nhập tự khai, group Facebook | `pain-points.md`, `community-insights.md` |
| `market/` | Số liệu thị trường & phân phối đơn (để mock) + tín hiệu điều phối/API ngoài | `order-distribution.md`, `dispatch-signals-and-external-apis.md` |
| `simulation/` | Nghiên cứu cho môi trường giả lập twin-world: công cụ, phương pháp đánh giá, tham số thế giới, timestep, action space, pilot world, biến môi trường, math-audit, realism, kiến trúc LLM advisor | `tooling.md`, `evaluation-methodology.md`, `world-parameters.md`, `timestep-design.md`, `action-space.md`, `pilot-world-dongda.md`, `environment-variables.md`, `math-audit.md`, `realism-benchmarks.md`, `llm-advisor-architecture.md`, `agent-pipeline-patterns.md` (đợt 7 — C6), `multi-agent-equilibrium.md` (ĐA-09 §2.2 — fictitious play, PoA, coverage curve), `data/` (OSM snapshots) |
| `ux/` | Nghiên cứu UX/HCI cho advisor: nudge patterns (Uber/Grab), NHTSA driver-distraction, agent-trace visualization (CrewAI) | `2026-07-27-decision-trace-design-note.md` (prep cho R2/R3) |
| `audit/` | Audit code/data/model + hồ sơ trạng thái đã reconcile | `2026-07-26-full-audit/REPORT.md`; `2026-07-27-r5-selfcheck/adapter-findings.md`; **đọc mới nhất:** [`2026-07-29-cycle-w-review/findings.md`](audit/2026-07-29-cycle-w-review/findings.md) |
| `experiments/` | Kết quả thử nghiệm/sweep có tổ chức riêng (mockgen, sensitivity) | `mockgen/ROUND-1..4-*.md`, `mockgen-realdata/ROUND-2-stats-report.md`, `sensitivity/dsim06_sweep.json` |
| (root) | Tổng hợp toàn bộ | `00_SUMMARY.md` |

## Quy ước

- **File tổng hợp đọc trước:** [`00_SUMMARY.md`](00_SUMMARY.md) — 10 điều quan trọng nhất + mapping research→features.
- Tài liệu **đặc tả kỹ thuật** (spec để code) KHÔNG nằm ở đây mà ở `specs/` (vd `specs/mock-order-distribution.md`).
- Tài liệu **kế hoạch** (scope, personas, user stories) ở `planning/`.
- Khi thêm loại findings mới (vd `research/safety/`, `research/ux/`): tạo folder tên rõ ràng + cập nhật bảng trên.
- Chính sách Xanh SM đổi rất thường xuyên → mọi con số phải ghi **effective date + version**; xem timeline trong `policy/bonus-programs.md`.
