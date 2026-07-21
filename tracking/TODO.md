# TODO — Backlog công việc

Cập nhật: 2026-07-21. Trạng thái: `TODO` / `READY` / `DOING` / `VALIDATING` / `DONE` / `BLOCKED`. Owner theo cơ chế **tự nhận việc (self-claim)** đầu session — không ai giao việc (xem `ASSIGNMENTS.md`). Khi làm xong một mục phải có UPDATE tương ứng trong `tracking/updates/`.

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
| T-018 | Build simulator core PILOT: world + actors + dispatcher + twin-runner CRN | DOING (vertical slice DONE) | Cường | 2026-07-21: `src/gsm_sim/` chạy 1 ngày arm B, 29/29 test xanh, output parquet — xem UPDATE-010. Còn: twin-runner 3 arm, determinism byte-identical, sensitivity, calibration gate (unserved ~34% cần về 15-20%) |
| T-019 | Advisor-sim arm A + C: trigger hybrid + DP lớp A + capacity ledger + placebo random-safe | TODO | — | Spec đã đủ để code: `advisor-optimization-layer-a` §2 (DP pseudocode, information model, advice_scope) + §2.5 (arm C định nghĩa lại) |
| T-020 | Evaluator + dashboard + replay + adherence report | TODO | — | DoD-eval: Δ 3 arm × advice_scope × information × adherence sweep; divergence index; proximal 90ph; counterfactual branch = stretch. `MAPBOX_TOKEN` optional |
| T-021 | Calibration sim: đối chiếu output với số tự khai research (15–30 cuốc/ngày, payout/ngày, pattern sạc trưa) | TODO | — | Sau T-018; sanity trước khi tin kết quả so sánh A/B |
| T-022 | Research đợt 4: action space tài xế + pilot world 1 quận/50 actors + timestep phân tầng | DONE | AI agent | 2026-07-21: `research/simulation/{action-space,pilot-world-dongda,timestep-design}.md` + `data/` (OSM: 11 tủ pin Đống Đa, POI, polygon); spec tổng hợp: `specs/simulation-pilot-world.md` |
| T-023 | Chốt action taxonomy cho SIM actor + phạm vi advisor tác động (product vs sim) | DONE | AI agent + Cường | 2026-07-21: verify chuyên sâu → **A13 = UNVERIFIED** (nguồn duy nhất là trang AI-gen; không dấu vết official/báo chí/diễn đàn sau 3,5 tháng); **Xanh KHÔNG có heatmap tài xế** → advice khu vực = BỔ SUNG không chồng đè, Cường mở CÓ ĐIỀU KIỆN (5 điều kiện an toàn trong `action-space.md` §Phạm vi advisor: capacity-aware, cảnh báo tỷ lệ nhận, nhãn mock, không hứa thu nhập, shift-aware flag OFF). Kiểm changelog in-app → T-013 |
