# TODO — Backlog công việc

Cập nhật: 2026-07-21 (đợt 3 — sắp xếp lại theo yêu cầu Cường). Trạng thái: `TODO` / `READY` / `DOING` / `VALIDATING` / `DONE` / `BLOCKED`. Owner theo cơ chế **tự nhận việc (self-claim)** — xem `ASSIGNMENTS.md`. Xong việc phải có UPDATE trong `tracking/updates/`.

## Thứ tự thực thi (theo độ quan trọng + phụ thuộc tuyến tính)

**Track SIM/Advisor (Cường + AI agent) — tuyến tính:**

1. ✅ **T-024 Realism pass + T-021 Calibration vòng 1** (DONE 2026-07-21): đối chiếu benchmark → sửa time-accounting bug, patience 2 tầng, day-bonus, demand-hint. **Kết luận quan trọng**: unserved 34%/util 38% của baseline B là mismatch không gian + swap herding — **ĐÚNG và là dư địa cho advisor**; target 15-20% là cho ARM A không phải B (xem `research/simulation/realism-benchmarks.md` §Kết luận). Tinh chỉnh nhỏ còn lại không blocker.
2. **T-019 Advisor system** (việc trung tâm — TIẾP THEO): DP lớp A + trigger + capacity ledger; **LLM lớp C** (deepseek-v4-flash OK, fallback gpt-4o-mini **cần Cường xin quyền model** — hiện 403) render/personalize; kiến trúc "spec-first, LLM-offline" (`research/simulation/llm-advisor-architecture.md`). Kèm **observability per-layer** (T-026: Langfuse chính / Phoenix thay thế) xây ĐỒNG THỜI.
3. **T-020 Twin-runner 3 arm + evaluator**: chỉ sau khi advisor tồn tại; Δ 3 arm × scope × information × adherence sweep.
4. **T-027 Robustness/shift**: regime sweep trên cùng map (multi-map chỉ khi cần external validity — research kết luận đủ với same-map + domain randomization).

**Track song song (không đụng files nhau):**

- **Khánh: T-009 UI clone** (ưu tiên của Khánh — brief `planning/ui-clone-brief.md`).
- **Người thật (ai rảnh): T-013** join FB group + kiểm changelog app (chặn crawler).
- **AI agent (khi Cường rảnh review): T-004 KB chính sách** (độc lập với sim; cần cho product F0 sau).
- Dashboard sim (xong slice v0) — nâng cấp dần theo nhu cầu xem/control.

**Hoãn cho tới khi track SIM xong:** T-005 (CrewAI — advisor tự viết đang tiến tốt, đánh giá lại sau), T-006/T-007/T-008 (khung F1-F3 product — sẽ tái dùng advisor từ sim), T-011 (contract — chốt sau khi advisor API ổn định), T-015 (community — roadmap).

| ID | Việc | Trạng thái | Owner | Ghi chú |
| --- | --- | --- | --- | --- |
| T-001 | Deep research chính sách & thu nhập tài xế Xanh SM (theo `planning/RESEARCH.md`) | DONE (đợt 1) | AI agent (Cường duyệt) | 2026-07-20; output: `research/` (chia theo loại); gaps còn lại → T-012 |
| T-002 | Thiết kế hồ sơ tài xế mock (Bike trước) từ kết quả T-001 | DONE (nháp v1) | AI agent | 2026-07-20: 5 persona tại `planning/PERSONAS.md` (thêm tân binh + lão làng theo yêu cầu Cường); chờ review; số TBD chờ T-012 |
| T-003 | Mock demand proxy theo khung giờ × ngày trong tuần × khu vực | READY (spec xong) | — | `specs/mock-order-distribution.md` đã phân biệt demand vs matching, normalized weights, weather formula, money terms; code generator chưa claim |
| T-004 | Knowledge base chính sách cho F0 (policy có version + trích dẫn) | TODO | — | Nguồn từ T-001 |
| T-005 | Đánh giá framework agent: CrewAI vs flow tự viết (orchestrator theo drawio v2) | TODO | — | Stakeholder refer CrewAI; cần so sánh control/guardrail/độ phức tạp |
| T-006 | Khung F1 trước ca: chỉ tiêu net mặc định + nhận xét chỉ tiêu theo hồ sơ | TODO | — | Phụ thuộc T-002, T-004 |
| T-007 | Khung F2 trong ca: lời khuyên chạy/nghỉ/sạc từ phân phối mock | TODO | — | Phụ thuộc T-003 |
| T-008 | Khung F3 sau ca: analyzer/advisor + danh mục hành vi chưa tối ưu | TODO | — | Phụ thuộc T-002 |
| T-009 | UI/UX tạm: clone <https://rag-xanh-sm-v1.vercel.app/> bằng [ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template), mobile-first | TODO (Khánh — ưu tiên) | Khánh | **Brief đầy đủ: `planning/ui-clone-brief.md`**. Làm song song simulator, phạm vi UI riêng không đụng `src/gsm_sim/` |
| T-010 | Xác nhận scope luồng giải trình vi phạm (drawio file 2) | DONE | Cường | Chốt 2026-07-20: dự án khác, ngoài scope repo này — xem D-006 |
| T-011 | Định nghĩa contract/schema mới cho scope v2 (hồ sơ tài xế, demand proxy, output tư vấn) | TODO | — | Contracts cũ deferred; contract mới phải version hóa policy bundle + money definition (`gross_revenue`, `driver_payout`, `estimated_net_income`, cost completeness) |
| T-012 | Research đợt 2: bảng thưởng chi tiết + kinh nghiệm cộng đồng (FB groups, TikTok/YouTube) | DONE | AI agent | 2026-07-20: KHÔNG OCR/app. Bảng thưởng đã verify: `research/policy/bonus-programs.md`; cộng đồng: `research/community/community-insights.md`. FB groups cần join tay (T-013) |
| T-013 | Join 1–2 group Facebook tài xế + đọc mẹo thực chiến, số thành viên | TODO | — | Cần người thật (login wall chặn crawler); danh sách 6 group ở `research/community/community-insights.md` |
| T-014 | Vẽ lại luồng v2 (drawio 7 trang: L0–L2 + F0–F3, hiện tại + tương lai) | DONE | AI agent (Cường duyệt plan + flow) | 2026-07-20: Cường duyệt flow và yêu cầu commit; checkpoint consistency ghi tại UPDATE-006 |
| T-015 | (Tương lai) Tích hợp nguồn cộng đồng + khối kiểm chứng/lọc rủi ro vào sản phẩm | TODO | — | Roadmap D-008; theo `specs/community-source-risk-control.md`; cần F0–F3 chạy ổn trước |
| T-016 | Research đợt 3: tooling sim + evaluation methodology + tham số thế giới HN | DONE | AI agent | 2026-07-21: 3 file tại `research/simulation/` (tooling, evaluation-methodology, world-parameters) |
| T-017 | Review & chốt 2 spec sim | DONE | Cường | 2026-07-21: **APPROVE toàn bộ quyết định thiết kế + thêm arm C placebo**; spec đánh dấu APPROVED |
| T-018 | Build simulator core PILOT: world + actors + dispatcher + twin-runner CRN | DOING (slice + env DONE) | Cường | 2026-07-22 (UPDATE-012): thêm lớp `EnvironmentContext` (mưa/nhiệt/ngày/sự kiện, luật kết hợp 3 không gian), math-audit fixes (detour A4, magic A3/A5/A6), **UI hoàn chỉnh chỉnh tham số + visualize env**, 38/38 test xanh (dry≡baseline, env tác động thật). 2026-07-21 (UPDATE-010): slice arm B 1 ngày, parquet. Còn: twin-runner 3 arm, determinism byte-identical, sensitivity, calibration gate (unserved ~34%→15-20%), nối route_effect vào speed model |
| T-019 | Advisor-sim arm A + C: trigger hybrid + DP lớp A + capacity ledger + placebo random-safe | TODO | — | Spec đã đủ để code: `advisor-optimization-layer-a` §2 (DP pseudocode, information model, advice_scope) + §2.5 (arm C định nghĩa lại) |
| T-020 | Evaluator + dashboard + replay + adherence report | TODO | — | DoD-eval: Δ 3 arm × advice_scope × information × adherence sweep; divergence index; proximal 90ph; counterfactual branch = stretch. `MAPBOX_TOKEN` optional |
| T-021 | Calibration sim: đối chiếu output với số tự khai research (15–30 cuốc/ngày, payout/ngày, pattern sạc trưa) | TODO | — | Sau T-018; sanity trước khi tin kết quả so sánh A/B |
| T-022 | Research đợt 4: action space tài xế + pilot world 1 quận/50 actors + timestep phân tầng | DONE | AI agent | 2026-07-21: `research/simulation/{action-space,pilot-world-dongda,timestep-design}.md` + `data/` (OSM: 11 tủ pin Đống Đa, POI, polygon); spec tổng hợp: `specs/simulation-pilot-world.md` |
| T-023 | Chốt action taxonomy cho SIM actor + phạm vi advisor tác động (product vs sim) | DONE | AI agent + Cường | 2026-07-21: verify chuyên sâu → **A13 = UNVERIFIED** (nguồn duy nhất là trang AI-gen; không dấu vết official/báo chí/diễn đàn sau 3,5 tháng); **Xanh KHÔNG có heatmap tài xế** → advice khu vực = BỔ SUNG không chồng đè, Cường mở CÓ ĐIỀU KIỆN (5 điều kiện an toàn trong `action-space.md` §Phạm vi advisor: capacity-aware, cảnh báo tỷ lệ nhận, nhãn mock, không hứa thu nhập, shift-aware flag OFF). Kiểm changelog in-app → T-013 |
| T-024 | Realism pass: đối chiếu mọi MOCK với benchmark thực tế → chỉnh config | DONE | AI agent (claim Cường) | 2026-07-21: `research/simulation/realism-benchmarks.md`; sửa patience/day-bonus/time-accounting/demand-hint. Kết luận: baseline B unserved 34% là dư địa advisor, target 15-20% cho arm A |
| T-025 | Research kiến trúc AI Advisor LLM-in-the-loop + observability + multi-map | DONE (research) | AI agent (claim Cường) | 2026-07-21: `research/simulation/llm-advisor-architecture.md` — CHỐT "spec-first LLM-offline" + Langfuse/Phoenix + same-map robustness. Spec chi tiết `specs/advisor-system-detail.md` viết khi bắt đầu T-019. Smoke test: deepseek+JSON+cache OK, gpt-4o-mini 403 |
| T-026 | Observability per-layer cho advisor: Langfuse (hoặc alternative từ research) + metric bảng theo layer (trigger/DP/LLM/adherence); xây ĐỒNG THỜI với T-019 | TODO | — | Yêu cầu Cường 2026-07-21: không gắn observability sau; phải đo được shift/robustness |
| T-027 | Robustness/shift measurement: regime sweep (orders 900/1200/1800, mưa, adoption, archetype mix, station outage) trên cùng map; multi-map chỉ khi cần external validity | TODO | — | Sau T-020; căn cứ phương pháp luận từ T-025 |
| T-028 | Dashboard sim v0 (Streamlit + pydeck H3): xem + control (seed/demand/actors/dispatcher levers) | DONE (v0) | AI agent (claim Cường) | 2026-07-21: `src/gsm_sim/dashboard.py`; chạy `uv run --extra viz streamlit run src/gsm_sim/dashboard.py`; healthz OK; nâng cấp dần (replay theo thời gian → T-020) |
