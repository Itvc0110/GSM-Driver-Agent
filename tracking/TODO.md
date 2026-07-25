# TODO — Backlog công việc

Cập nhật: 2026-07-23 (**Track CORE ưu tiên** — Cường; sim pause sau T-030). Trạng thái: `TODO` / `READY` / `DOING` / `VALIDATING` / `DONE` / `BLOCKED`. Owner theo cơ chế **tự nhận việc (self-claim)** — xem `ASSIGNMENTS.md`. Xong việc phải có UPDATE trong `tracking/updates/`.

## Thứ tự thực thi (theo độ quan trọng + phụ thuộc tuyến tính)

**Track CORE bài toán (Cường 2026-07-23 — ƯU TIÊN HIỆN TẠI; spec `core-data-schema-and-advisor-architecture.md`):**

1. **T-038 C0**: chốt data schema L0–L3 platform-centric (`schemas/` + validators + changelog).
2. **T-038 C1**: mock data generator + verify 4 vòng (schema/statistical ≥30 seeds/consistency/adversarial — spec §8.1).
3. **C2a** ✅ metric table (UPDATE-025). **C2b** ✅ solver S1 BonusFeasibility + SolverReport DONE 2026-07-23 (`gsm_core/{policy,features/bonus_gap,solvers/bonus_feasibility}`, UPDATE-026; 12 test, integration mock 7/12 feasible).
4. **C3** ✅ S2 ShiftDP (UPDATE-027). **C4** ✅ S3 F3Patterns + L2i (UPDATE-028). **C5** ✅ S4 CapacityAlloc DONE 2026-07-23 (`gsm_core/solvers/capacity_alloc.py`, UPDATE-029; scipy assignment chống herding, 5 safety_flags F2-04, 12 test, over-subscribe 0 vi phạm capacity). **→ 4/4 SOLVER XONG.**
5. **C6** ✅ DONE 2026-07-24 (UPDATE-030): agent pipeline `src/gsm_core/advisor/` (Router zero-ML → Composer placeholder-first LLM#1 → Verifier 3 tầng CODE-veto) + context pack (1 renderer) + episode store (exact-key cache, kiêm DecisionRecord) + observability per-layer (2 HARD invariant =1.0). F0 corpus-based track-guardrail. Template fallback (LLM-off) bắt buộc. 37 test (14+18+5), full suite 162. **3 bug thật fix có regression** (BUG-C6-01 normalize đ/Đ ở cả 3 module; BUG-C6-02 promise pattern báo nhầm tên chính sách "Đảm Bảo Thu Nhập"; BUG-C6-03 verifier soi text trích dẫn official). T-026 phase 2 instrument xong. **Còn: live LLM smoke thật (D-C6-03), visual = sample text.**
6. **Research refresh đợt 3** ✅ DONE 2026-07-24 (UPDATE-031): web research vòng mới phát hiện **Vận Doanh 23/02/2026 BỎ phạt ≤70% + khoán tuần + truy thu 20-40%** (research policy đợt 1/2 lỗi thời). Đồng bộ docs: `research/policy/policy-refresh-2026-07-24.md` + banner ở 00_SUMMARY/bonus-programs/pain-points/income-structure + ghi chú PERSONAS/USER_STORIES/spec §1.7. Flag **D-POL-01..05** (model/schema/mock/corpus/image-locked gaps). **T-004 corpus (Khánh) thiếu policy này → D-POL-04.**
7. **Downstream policy-refresh (D-POL-01..05 — cycle plan riêng, trước/song song C7):** MODEL gap khoán-tuần+clawback (S1/S2), SCHEMA gap points.service_type + weekly_quota/clawback_rate, MOCK regen, CORPUS gap (owner Khánh), image-locked → data thật GSM. **✅ Design spec `specs/policy-weekly-khoan-model.md` (UPDATE-032) = blueprint cho D-POL-01/02/03** (solver S5 WeeklyKhoanFeasibility, schema additive, ledger `deduction`/`week_bonus`). **Decisions Cường 2026-07-24:** (a) ✅ S5 mới; (b) ✅ **CHƯA implement — dừng ở spec, chờ DATA THẬT GSM + Cường mở cycle** (không code với số mock); (c) ✅ giữ daily-proxy (nhãn); (d) ⏳ khoán gross/payout chờ data. ⇒ **D-POL-01/02/03 TREO tới khi có data thật.**
8. **Real-data integration** (Cường cấp schema thật gsm-data-prod 2026-07-24) — **blueprint DONE** (UPDATE-033): catalog `docs/data-catalog/` + 7 part-plan `specs/real-data/`. Chốt: re-ground về 13 bảng thật; chưa BQ access (tool=interface+PII); mở rộng UC5-UC8. **Roadmap 6 phase (mỗi phase cycle riêng có plan+test):**
   - **PI-1 Schema** ✅ DONE 2026-07-24 (UPDATE-034): 13 `l1r/*` + registry + 30 test; 5 bảng thiếu cột ENGINEER (nhãn TBC).
   - **PI-2 Mock regen** ✅ DONE 2026-07-24 (UPDATE-034): `mockgen/realdata.py` sim→aggregate → 13 bảng; R1/R3/R4 verify (9 test) + **R2 statistical 30 seeds/1500 driver-day** (`ROUND-2`, 6/6 in-range). Smoke 14 ngày×50 driver OK.
   - **PI-2b Data review + enlargement (ĐANG LÀM — refine Cường 2026-07-24)**: 
     - **Overall review**: audit từng bảng/cột/phân phối vs catalog+schema+UC coverage; soi caveat R2; kiểm cột ENGINEER; FK/consistency tập lớn.
     - **REALISM + RANDOMNESS (ưu tiên)**: sửa **acceptance median 1.00** (sim thiếu decline) → tỷ lệ nhận theo archetype target (0.74-0.97) + noise per-day, back-out decline; thêm variance/randomness mọi metric; cộng **lớp thưởng tuần** vào payout (nối S5); reposition/penalty/fraud/idle đa dạng hơn.
     - **PROFILE UNIVERSE phủ MỌI loại GSM** (car / bike / premium / platform / rto / employee, archetype PT/FT/top/newbie/veteran, tenure spread): roster LỚN đa dạng; **sim CHỈ sample một subset (bike)** — car/premium/khác sinh KPI **rule-based** grounded `economics/income-structure` (car: lương+commission; premium: fare cao). Quy mô ngày →90+.
     - **DEFER (Cường)**: enlargement zone/station/market (ngoài Đống Đa) — future update.
     - Sau enlarge: chạy lại 4 vòng verify (R1/R2/R3/R4) tập lớn; cập nhật ROUND report. **Gate cho PI-4.**
     - ✅ **DONE 2026-07-24** (UPDATE-035 + **UPDATE-036 audit**): profile universe 110 (bike/rto/car/employee/premium), acceptance 1.00→0.88, CSV export. **Audit tìm & fix 5 flaw**: R2 trộn population (verdict sai), impossible-state 203 driver-day (cuốc khi online=0), tràn nửa đêm, field degenerate (core_order/stoppoints), **crash parquet phụ thuộc seed**. Suite 208. **Đính chính:** bike payout thật ~221k (không phải 273k đã báo — số đó lẫn car), vẫn biên dưới tới khi có **lớp thưởng tuần (S5)**.
   - **PI-3 DataSource tool**: MockSource+BQ skeleton+PII read-only (P4). Sau PI-1. Live treo chờ credentials + Cường chốt BQ auth/env.
   - **PI-4 Solver remap + S5/S6**: S1-4 remap field thật + S5 khoán + S6 mission-knapsack (P6). Sau PI-2.
   - **PI-5 UC5-8 features**: idle-reduction, penalty-explain, anomaly-alert + router (P6). Sau PI-4.
   - **PI-6 External** (treo): ExternalContext + Google Maps/Weather (P5). Chờ Cường chốt key/techstack.
   - **Cần Cường/GSM chốt trước impl:** semantics 5 field + target KPI + cột thật 5 bảng; BQ auth/env; external key. **LOẠI TRỪ**: hiệu năng AI-Advisor/observability/CICD/optimize.
9. **C7**: EXP-001..005 trên instrumentation C6 (episode store đã bandit-ready). **Gated:** eval set F0 phải phản ánh policy hiện hành (post-refresh) + data thật (post PI-2) → chạy sau khi nền policy+data ổn.
7. **T-039** checkpoint mở rộng sau mỗi C#/T# hoàn thành (section bắt buộc trong UPDATE_TEMPLATE).

**Track SIM/Advisor (PAUSE sau T-030 — resume sau khung core; reliability-first):**

1. ✅ **M0 — T-030 Simulator integrity (DONE 2026-07-22, UPDATE-023):** 12 flaw + C-2 fixed, 57/57 test, determinism cross-process PASS.
2. **M1 — T-031 (PAUSED — Track CORE chạy trước, 2026-07-23):** 24h dynamic market + data schema/inferable projection.
3. **M2 — T-032→T-034 (PAUSED):** OSM endpoints → H3 routing contract → exogenous traces.
4. **M3 — T-035→T-037 (PAUSED):** Story/actor/Diagnostic visualization.
5. **M4 — T-019 + T-020 (sau C6/C7):** twin-integration kế thừa artifacts core; T-026 đã nhập vào C2/C6.
6. **Sau M4 — T-027 Robustness/shift.**

Source of truth sim: `specs/simulation-reliability-upgrade.md`. Mỗi milestone/C# có plan mode riêng, multi-seed/boundary/full-suite verification và visual review theo `CLAUDE.md` §4b.

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
| T-004 | Knowledge base chính sách cho F0 (policy có version + trích dẫn) | DONE (text corpus + source register) | Khánh | `research/policy/t004-current-policy-text-corpus-2026-07-22.json` giữ full text + metadata của 7 nguồn T1 current; `T004_TEXT_CORPUS_USAGE.md` nêu guardrail. HTML/ảnh/OCR/crawler không vào repo; T-011/reviewer mới được tạo policy fact runtime. |
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
| T-018 | Simulator core/runner substrate: world + actors + dispatcher + deterministic trace/CRN nền | DOING (slice + env core DONE; integrity chưa đóng) | Cường | UPDATE-010/012: arm B 1 ngày + EnvironmentContext + dashboard v0. Working diff Stage A–C ngày 2026-07-22 là **input T-030**, chưa được chấp nhận/commit nguyên khối. T-018 sở hữu runner substrate; A/B/C orchestration/evaluator thuộc T-020. |
| T-019 | M4 Advisor-sim arm A + C: trigger hybrid + DP lớp A + capacity ledger + placebo random-safe | TODO | — | Chỉ sau M0–M3 gate. Kèm T-026 đồng thời; spec-first/LLM-offline, template fallback. Không nhìn future realized orders, không can thiệp dispatch. |
| T-020 | M4 Twin-runner A/B/C + paired evaluator + adherence/divergence attribution | TODO | — | Sở hữu orchestration/evaluator (`A−B`, `C−B`, `A−C`, ITT/CACE/CI). Dashboard stakeholder chung chuyển T-035–T-037; comparative view đọc canonical evaluator artifacts. |
| T-021 | Calibration/realism gate xuyên M0–M4 theo evidence tiers + invariants + sensitivity | VALIDATING (vòng 1 DONE) | — | Vòng 1 (T-024) xong; milestone gates chưa đóng. B-arm phải plausible/stable/explainable; **15–20% không phải integrity invariant của B-arm**. Distribution/calibration mặc định ≥30 seeds trừ khi plan giải thích khác. |
| T-022 | Research đợt 4: action space tài xế + pilot world 1 quận/50 actors + timestep phân tầng | DONE | AI agent | 2026-07-21: `research/simulation/{action-space,pilot-world-dongda,timestep-design}.md` + `data/` (OSM: 11 tủ pin Đống Đa, POI, polygon); spec tổng hợp: `specs/simulation-pilot-world.md` |
| T-023 | Chốt action taxonomy cho SIM actor + phạm vi advisor tác động (product vs sim) | DONE | AI agent + Cường | 2026-07-21: verify chuyên sâu → **A13 = UNVERIFIED** (nguồn duy nhất là trang AI-gen; không dấu vết official/báo chí/diễn đàn sau 3,5 tháng); **Xanh KHÔNG có heatmap tài xế** → advice khu vực = BỔ SUNG không chồng đè, Cường mở CÓ ĐIỀU KIỆN (5 điều kiện an toàn trong `action-space.md` §Phạm vi advisor: capacity-aware, cảnh báo tỷ lệ nhận, nhãn mock, không hứa thu nhập, shift-aware flag OFF). Kiểm changelog in-app → T-013 |
| T-024 | Realism pass: đối chiếu mọi MOCK với benchmark thực tế → chỉnh config | DONE | AI agent (claim Cường) | 2026-07-21: `research/simulation/realism-benchmarks.md`; sửa patience/day-bonus/time-accounting/demand-hint. Kết luận: baseline B unserved 34% là dư địa advisor, target 15-20% cho arm A |
| T-025 | Research kiến trúc AI Advisor LLM-in-the-loop + observability + multi-map | DONE (research) | AI agent (claim Cường) | 2026-07-21: `research/simulation/llm-advisor-architecture.md` — CHỐT "spec-first LLM-offline" + Langfuse/Phoenix + same-map robustness. Spec chi tiết `specs/advisor-system-detail.md` viết khi bắt đầu T-019. Smoke test: deepseek+JSON+cache OK, gpt-4o-mini 403 |
| T-026 | Observability per-layer cho advisor: Langfuse (hoặc alternative từ research) + metric bảng theo layer (trigger/DP/LLM/adherence); xây ĐỒNG THỜI với T-019 | TODO | — | Yêu cầu Cường 2026-07-21: không gắn observability sau; phải đo được shift/robustness |
| T-027 | Robustness/shift measurement: regime sweep (orders 900/1200/1800, mưa, adoption, archetype mix, station outage) trên cùng map; multi-map chỉ khi cần external validity | TODO | — | Sau T-034 (world shifts) + T-020 (evaluator); task validation, không sở hữu world implementation. |
| T-028 | Dashboard sim v0 (Streamlit + pydeck H3): xem + control (seed/demand/actors/dispatcher levers) | DONE (v0) | AI agent (claim Cường) | 2026-07-21: `src/gsm_sim/dashboard.py`; predecessor của T-035–T-037. Replay/actor journey không còn gộp vào T-020. |
| T-029 | Governance + master spec chương trình simulator reliability-first M0–M4 | DONE (docs) | AI agent (theo yêu cầu Cường) | 2026-07-22: `specs/simulation-reliability-upgrade.md`; cập nhật SCOPE/TODO/DEFERRED/CLAUDE.md/UPDATE template — xem UPDATE-021. Không thay đổi code sim. |
| T-030 | M0: preserve/audit working diff Stage A–C + baseline manifest + canonical lifecycle/conservation/determinism invariants | VALIDATING (fixes DONE, chờ visual verdict) | Cường (AI agent) | 2026-07-22 UPDATE-023: 12 flaw M0 + C-2 fixed failing-first, 57/57 test, cross-process determinism PASS, shift table 5 seeds giải thích đủ. Còn: visual review Cường + push. Taxonomy observable/inferable/latent vào spec §3.5. |
| T-031 | M1: full `[00:00,24:00)` dynamic daily actor pool + NHPP/piecewise-linear demand + bin validation + **data schema/inferable projection** | READY (khi T-030 đóng visual gate) | — | **Ưu tiên Cường 2026-07-22: chốt DATA SCHEMA trước** — observable events (app/GPS/swap) chuẩn hóa sẵn để feed math modelling/context model/actor state; latent chỉ là sim ground truth. Kèm: dead flag `hour_interp` (NHPP), participation funnel, bins 1/5/15ph ≥30 seeds; sim data phải dựa thực tế. |
| T-032 | M2a: OSM road/POI endpoint provider + immutable cache/provenance/offline replay | BLOCKED | — | Phụ thuộc T-030. Pickup/dropoff có `osm_id`, source, H3, bundle hash; không network trong sim loop. Road graph chưa bắt buộc ở endpoint v1. |
| T-033 | M2b: H3 candidate shortlist + continuous/road distance/ETA/trajectory contract | BLOCKED | — | Phụ thuộc T-031 + T-032. Atomic lat/lon/H3 movement, deterministic tie-break, explicit Haversine×detour fallback; dispatch H3 invariants. |
| T-034 | M2c: smoothed congestion + weather/event/route-effect/distribution-shift traces + attribution/no-future-leak | BLOCKED | — | Phụ thuộc T-031 + T-033. Tách base/demand `[PROXY]`/rain/event, survival combine, `known_at/effective_at`, no-op equivalence. Hấp thụ follow-up UPDATE-012. |
| T-035 | M3a: Story Mode city pulse + canonical replay/player (per-event, 1/5/15 phút) | BLOCKED | — | Phụ thuộc T-034; narrative market 24h. H3 mặc định phẳng/bán trong suốt; station layer trên cùng; active fleet/lifecycle/environment đồng bộ playhead. |
| T-036 | M3b: actor journey selector + route/Gantt/SOC/payout/points + flaw labels + advisor placeholder | BLOCKED | — | Phụ thuộc T-035. `OBSERVED` ≠ `HEURISTIC` ≠ `PAIRED_COUNTERFACTUAL`; chưa có M4 thì không hiển thị số “mất tiền” chắc chắn. |
| T-037 | M3c: Diagnostic Mode + audit panels + visual-review harness | BLOCKED | — | Phụ thuộc T-035 + T-036. Demand/supply/lifecycle/spatial/station/evidence diagnostics; launch seed/scenario cho Cường review theo CLAUDE.md §4b. |
| T-038 | **CORE C0+C1: chốt data schema (L0–L3, platform-centric) + MOCK data generator theo schema** | VALIDATING (C0+C1 DONE 2026-07-23, UPDATE-024) | Cường (AI agent) | 23 schema + registry (`gsm_core`); mock 30 ngày × 50 driver (22k trips, 1M GPS pings); **4 vòng verify PASS** (schema/FK, stats 30 seeds, consistency 100%, adversarial 0-bug); 76/76 test. Gap payout/trips có nhãn T-021 (không che). Còn: chạy lại round-4 subagent khi quota ổn; net_input/request-log entity chờ data thật. |
| T-039 | **Recurring: expansion checkpoint — MỞ RỘNG schema / bài toán tối ưu / tính năng?** | RECURRING | — | Yêu cầu Cường 2026-07-23: sau MỖI phần hoàn thành (mỗi C#/T#), UPDATE phải có mục trả lời: (1) schema cần thêm/bớt field gì? (2) có bài toán mới formalize được không (residual→solver)? (3) tính năng mới khả thi từ data hiện có? Không tự triển khai — ghi đề xuất để Cường duyệt. |
