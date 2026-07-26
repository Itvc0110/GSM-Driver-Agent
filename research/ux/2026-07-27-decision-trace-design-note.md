# Design note — Decision-trace cho advisor (R2) + agent-trace tối giản kiểu CrewAI (R3)

Ngày: 2026-07-27 · Trạng thái: **NOTE chuẩn bị — chưa phải plan**; cycle R1-R3 sẽ vào plan mode
riêng sau audit (thứ tự trong `tracking/BACKLOG-QUESTIONS-2026-07-27.md`).

## 1. Nguồn tham khảo (đã research)

**CrewAI tracing** ([docs](https://docs.crewai.com/en/observability/tracing)): timeline spans
theo tầng (Crew → agent → task), mỗi bước hiện agent/task/tool + input/output + duration +
trạng thái, click-through từng giai đoạn, export. Yếu tố đáng bắt chước: (1) **mỗi bước 1 dòng
gọn** có icon trạng thái ✓/✗/⏳, (2) expand/collapse chi tiết, (3) trạng thái bằng màu/icon,
(4) panel chi tiết input/output/metadata, (5) metrics nhẹ (duration/confidence).
Kèm quan sát terminal-style của CrewAI: agent "thinking/acting" hiện realtime từng dòng —
cảm giác SỐNG mà không tràn chữ.

## 2. Insight quan trọng: KHÔNG cần engine mới

Mọi dữ liệu cho decision-trace ĐÃ TỒN TẠI trong hệ:
- `SolverReport` có sẵn: `problem_digest`, `inputs_used[]` (view id + freshness), `numbers[]`
  (kèm source), `sensitivity[]`, `confidence`, `caveats`, `infeasible_reason`, `solution.constraints`
  (ràng buộc nào bind!).
- Advice contract UI đã mang confidence/reason_code/numbers.source.
- Verifier flags + fallback_used có trong pipeline C6; episode_store ghi mỗi lượt.
- Sim có event `advice_given/followed` + solver_action + adherence.

⇒ Việc cần làm chỉ là **serialize thành `decision_trace[]`** ở backend + render. Không tính lại
số nào (giữ nguyên tắc một-nguồn-sự-thật).

## 3. Phác thảo (cho plan sau)

**Contract `decision_trace` (nhúng vào advice response, optional):**
```
trace: [
  {step: "view",     name: "bonus_gap_input",     status: "ok", digest: "điểm 140 · nhận 0.91 (NGÀY) · quỹ 3.2h", detail: {...}},
  {step: "solver",   name: "S1 bonus_feasibility", status: "ok", digest: "thiếu 20đ ≈ 1.3h — FEASIBLE", detail: {constraints, numbers, sensitivity}},
  {step: "verify",   name: "guardrails",           status: "ok", digest: "số neo registry · không hứa thu nhập"},
  {step: "compose",  name: "card nudge",           status: "ok", digest: "template · confidence 0.85"},
]
```
**UI 2 mức:**
- **Trong card "Vì sao" (app tài xế)**: trace mini 3-4 dòng icon + digest — tài xế hiểu "vì sao
  trợ lý nói vậy" trong 5 giây, KHÔNG jargon (tên solver ẩn sau nhãn tiếng Việt "tính khả thi mốc thưởng").
- **Khu Mô phỏng (reviewer)**: trace đầy đủ expand được từng step (input/output/constraint bind),
  kiểu CrewAI span list; cộng terminal-style live-feed khi replay (dòng chảy sự kiện advice trong ngày sim).

**R1 ràng buộc thiết kế**: khu Mô phỏng dùng CHUNG shell/tokens/components với app (theme.css
hiện có) — trang mo-phong sẽ được đưa về cùng layout ngôn ngữ (cards, pills, section-label).
**R4**: playback thêm pause/×1/×4/×16 + "nhảy tới sự kiện kế" (dữ liệu events đã có trong journey).

## 4. Việc mở (đưa vào plan R1-R3)

- Nhãn tiếng Việt cho từng solver/step (map S1..S9 → tên người-hiểu-được) — MỘT nguồn trong tokens?
- Trace của advice IM LẶNG (giá trị lớn: "vì sao trợ lý im" — hiện silent.reason_code đã có, trace hoá).
- Ghép với đo adherence: card→action log đã có (UPDATE-067) — trace + action = vòng kín hiểu-và-đo.
