# SPEC — Core Data Schema & Advisor Architecture (v1)

Cập nhật: 2026-07-23 · Trạng thái: **DESIGN APPROVED (brainstorm Cường 2026-07-23) — chờ review file để vào plan**
Nguồn: brainstorm Cường 2026-07-23; kế thừa `simulation-reliability-upgrade.md` §3.5 (observable/inferable/latent), `advisor-optimization-layer-a.md` (DP), `advice-timing-state-memory.md` (trigger/memory), `planning/USER_STORIES.md`, `research/community/pain-points.md`, `research/simulation/llm-advisor-architecture.md`.
Bối cảnh mới: **dự án hợp tác chính thức với GSM — có quyền truy cập data thật** (Cường 2026-07-23) → schema **platform-centric**.

## 0. Quyết định nền (đã chốt trong brainstorm)

| # | Quyết định | Lựa chọn |
|---|---|---|
| D1 | Góc nhìn data | **Platform-centric** — gồm supply/demand field, station state thật của GSM |
| D2 | Bài toán modelling lõi | **4 solver**: ShiftDP, BonusFeasibility, F3Patterns, CapacityAlloc — thuần math, KHÔNG agent |
| D3 | Ranh giới math vs agent | **Solver-first, agent-residual**: mặc định mọi bài formalize được đi solver; agent chỉ nhận residual liệt kê ĐÓNG (§4) |
| D4 | Kiến trúc schema | **4 tầng + event backbone** (L0 reference → L1 event log → L2 state fields → L3 feature views) |

Ràng buộc bất biến (CLAUDE.md §5): agent không tự tính số tài chính/xác suất; tách `gross_revenue`/`driver_payout`/`estimated_net_income`; mock có nhãn; không can thiệp matching/dispatch/pricing/routing; không khuyên nhận/từ chối đơn cụ thể.

**Assumption data quality (Cường chốt):** L1 giả định data GSM export **đã clean/normalize** trước ingest — dedup, timestamp chuẩn hóa UTC+7, schema hợp lệ, không late-event/clock-skew chưa xử lý. Data-quality/ingest pipeline **ngoài scope spec này**; nếu export thô thì mở task riêng (ghi `TBC-với-GSM`). Mock generator (T-038 C1) phải gen data ĐÃ ở mức sạch này.

## 1. Schema 4 tầng

### 1.1 Sơ đồ

```text
L0 REFERENCE (slowly-changing, versioned)
  PolicyBundle · DriverProfile · StationRegistry · ZoneMap(H3) · ServiceCatalog
      ↓ FK
L1 EVENT LOG (immutable, append-only — NGUỒN SỰ THẬT)
  AppEvent · TripRecord · GPSPing · SwapTransaction · PayoutLedger · PolicyChangeEvent
      ↓ derivation JOB (code có version — không sửa tay)
L2 STATE FIELDS (bucket 15ph × H3 — platform data thật, ĐO ĐƯỢC)
  SupplyField · DemandField · StationState · DriverDayState
L2i INFERRED VIEWS (rule-versioned — TÁCH RIÊNG, không trộn với measured)
  InferredActivity (+ mọi entity suy diễn tương lai đều vào tầng này)
      ↓ feature view (read-only)
L3 FEATURE VIEWS (input cho solver/agent)
  ShiftPlanInput · BonusGapInput · SessionSummaryInput · AllocationInput
```

### 1.2 L0 — Reference entities

| Entity | Fields chính | Ghi chú |
|---|---|---|
| `PolicyBundle` | bundle_id, version, effective_from/to, track (core_owned/platform/rto), service, fare table, share %, điểm/cuốc theo khung, mốc thưởng ngày/tuần, ngưỡng acceptance/completion, source_url | Nguồn số tài chính DUY NHẤT cùng PayoutLedger. Version hóa — trả lời US-F0-03 |
| `DriverProfile` | driver_id, track, tier, tenure_months, vehicle_type, fleet (swap/charge), home_zone (H3 res8 — coarse cho privacy), thói quen khai báo (shift window, meal window — nếu tài xế tự khai) | Track BẮT BUỘC cho F0 (guardrail T-004: `green_bike_unspecified` không auto-map) |
| `StationRegistry` | station_id, lat/lon, H3, slots, throughput danh định | |
| `ZoneMap` | H3 res9 vận hành + res8 báo cáo, POI weights | Đã có trong sim |
| `ServiceCatalog` | service_type (bike/express/ngon...), thuộc tính đơn | D-009 đa dịch vụ nối vào đây |

### 1.3 L1 — Event log (observable-only)

Mọi field L1 là thứ **GSM đo được thật** (taxonomy §3.5). Không field nào là suy diễn.

| Entity | Fields chính | Availability |
|---|---|---|
| `AppEvent` | driver_id, t, kind ∈ {go_online, go_offline, set_offline_after_trip, offer_shown, accept, decline, cancel(reason), complete, forced_auto_accept_on/off}, order_ref | CONFIRMED (action-space research) |
| `TripRecord` | order_id, driver_id, service_type, t_request/assign/pickup/complete, pickup+drop lat-lon+H3, dist_km, gross_vnd | CONFIRMED |
| `GPSPing` | driver_id, t, lat/lon → H3, speed | **TBC-với-GSM: tần suất, độ trễ export** |
| `SwapTransaction` | driver_id, station_id, t, battery_out/in id | **TBC-với-GSM: queue/wait có đo không** |
| `PayoutLedger` | driver_id, t, kind ∈ {trip_payout, day_bonus, week_bonus, adjustment, deduction}, amount_vnd, basis (trip_id/bundle_version), gross_vnd tương ứng | CONFIRMED. **Tách gross/payout tại nguồn**; net-input (chi phí thuê/điện) là entity riêng khi có |
| `PolicyChangeEvent` | bundle_id, from_version → to_version, effective_at, changed_fields | Từ policy KB pipeline (T-004 → T-011) |

### 1.4 L2 — State fields (derivation có version)

| Entity | Derivation | Ghi chú |
|---|---|---|
| `SupplyField(bucket, cell)` | count driver online/idle từ AppEvent+GPSPing | data thật GSM |
| `DemandField(bucket, cell)` | count request/served/unserved từ TripRecord + request log | **thay mock bằng thật** — mock chỉ còn cho sim/dev, có nhãn |
| `StationState(bucket, station)` | pin ready/charging từ SwapTransaction + telemetry (TBC) | |
| `DriverDayState(driver, bucket)` | điểm lũy kế, acceptance/completion rate, giờ online, SOC (TBC per-ping hay per-swap) | nuôi cảnh báo ngưỡng |
**L2i — Inferred views (tầng RIÊNG, tách khỏi measured):**

| Entity | Derivation | Ghi chú |
|---|---|---|
| `InferredActivity(driver, segment)` | **INFERRED** label ∈ {rest_likely, charging_likely, relocating, idle_wait} từ GPS+event gaps, kèm `inference_rule_version` + confidence | KHÔNG BAO GIỜ trình bày như đo được; nuôi F3. Quy ước: mọi entity suy diễn tương lai vào L2i, cấm thêm vào bảng measured phía trên |

### 1.5 L3 — Feature views (hợp đồng input solver)

`ShiftPlanInput` (buckets còn lại, SOC, demand forecast per cell-cluster, điểm/mốc, ngưỡng hồ sơ) · `BonusGapInput` (điểm hiện tại, mốc kế, tốc độ điểm lịch sử theo khung giờ, quỹ giờ) · `SessionSummaryInput` (trip timeline + InferredActivity + payout breakdown) · `AllocationInput` (candidate advice nhiều driver + StationState + SupplyField).

### 1.6 Versioning & extensibility (yêu cầu Cường: dư địa update)

- Mỗi entity: `schema_version` semver. **Thêm** = optional field + minor bump. **Bỏ** = `deprecated_since` + ≥1 chu kỳ chuyển tiếp, không xóa thẳng.
- Field chưa chắc GSM export được: nhãn **`AVAILABILITY: TBC-với-GSM`** — bảng fallback GHI SẴN đầy đủ:

| TBC field | Fallback nếu GSM không export | Nhãn output |
|---|---|---|
| GPSPing tần suất cao/độ trễ thấp | Ping thưa → `InferredActivity` hạ confidence + bucket to hơn (30ph thay 15ph); SupplyField độ phân giải res8 thay res9 | `COARSE` |
| Station queue/wait đo trực tiếp | Ước lượng wait từ mật độ SwapTransaction liên tiếp cùng trạm + throughput danh định StationRegistry | `ESTIMATED` + confidence |
| SOC telemetry per-ping | SOC chỉ biết tại mốc swap (100%) + ước lượng tiêu hao theo km từ GPS; `DriverDayState.SOC` nhãn coarse | `ESTIMATED` |
| StationState pin ready/charging telemetry | Suy từ SwapTransaction in/outflow + battery_recharge throughput; field không suy được để rỗng (không bịa) | `ESTIMATED` + confidence |
| Request-log (đơn không được serve) | DemandField chỉ có served; unserved = ước lượng từ mismatch supply/demand có nhãn | `ESTIMATED` |
- `sensitivity` per field (PII: lat/lon thô, driver_id) → cơ chế thu hẹp/anonymize khi cần.
- **Sim map cùng schema**: sim runner xuất L1 events đúng format này (adapter từ `world.events`/`segments`) → twin-world eval và product dùng chung pipeline; dữ liệu sim phải bám phân phối thực tế (benchmark research + data thật khi có).
- Registry `schemas/` trong repo: JSON Schema per entity + validator + changelog.

### 1.7 Traceability biến → feature → pain point (chiều xuất phát từ BIẾN)

Pain # theo `research/community/pain-points.md`: **#1** sạc/đổi pin giờ đỉnh · **#2** quỹ giờ 10–13h/ngày quá tải · **#3** áp lực tỷ lệ nhận (ngưỡng 50% forced-accept, 85% bonus) · **#4** chính sách khó hiểu/đổi liên tục.

| Nhóm biến | Feature/US nuôi | Pain # | Solver tiêu thụ |
|---|---|---|---|
| `PolicyBundle` + `PolicyChangeEvent` | US-F0-01/02/**03**, US-F1-01 | #4 | S1; R1 RAG |
| `DriverProfile` (track!) | US-F0-02 (đúng track RTO/platform), mọi F cá nhân hóa | #4 | tất cả |
| `PayoutLedger` | US-F1-02, US-F3-01 (tách gross/payout/net) | #2, #4 | S1, S3 |
| `AppEvent` (accept/decline/forced flag) | US-F3-02, cảnh báo ngưỡng F0 | **#3** | S3, DriverDayState |
| `TripRecord` | US-F3-01/02 (timeline ca), input mọi solver | #2 | S1–S3 |
| `GPSPing` → `InferredActivity` | US-F3-02 (pattern chưa tối ưu, INFERRED có nhãn) | #1, #2 | S3 |
| `SwapTransaction` + `StationState` | US-F2-02 (sạc thấp điểm), F2-04 | **#1** | S2 (SOC constraint), S4 |
| `DemandField` + `SupplyField` | US-F2-01 (demand proxy), F2-04 heatmap có điều kiện | #1, #2 | S2, S4 |
| `DriverDayState` | US-F1-04 (tiến độ mốc), US-F3-02 (sát ngưỡng) | #2, #3 | S1, S3 |
| `StationRegistry`/`ZoneMap`/`ServiceCatalog` | hạ tầng bắt buộc (FK/không gian/dịch vụ) — không nuôi US trực tiếp, giữ vì mọi entity khác tham chiếu | — | tất cả |
| L3 views (4) | đúng 1-1 với S1–S4 → US tương ứng ở §2 | #1–#4 | S1–S4 |

Biến nào sau này thêm vào schema PHẢI điền được hàng trong bảng này (feature + pain hoặc lý-do-hạ-tầng) — điều kiện của T-039 checkpoint.

## 2. Bốn bài toán modelling (thuần math — không agent)

| # | Solver | Bài toán | Công cụ | Feature/US | Trạng thái |
|---|---|---|---|---|---|
| S1 | `BonusFeasibility` | gap điểm→mốc; trips/hours cần; feasible vs quỹ giờ | đại số + scipy khi có ràng buộc | F0-01, F1-03/04 | làm TRƯỚC (dễ verify) |
| S2 | `ShiftDP` | lịch online/nghỉ/sạc theo bucket 30ph max E[payout] | DP numpy 20×10×4 (spec §2 advisor-layer-a) | F1-04, F2-01/02 | spec sẵn |
| S3 | `F3Patterns` | pattern chưa tối ưu từ SessionSummary | rules + so sánh phân phối | F3-01/02/03 | detect_flaws sim là prototype |
| S4 | `CapacityAlloc` | phân bổ advice chống herding | linear_sum_assignment / min-cost | F2-04 có điều kiện | cần S2 candidates |

**SolverReport envelope** (hợp đồng output thống nhất — cách agent "hiểu" solver):

```yaml
SolverReport:
  solver, schema_version
  problem_digest: str        # bài toán bằng lời, sinh deterministic từ input
  inputs_used: [view_id + version + freshness]
  solution: {structured theo solver}
  numbers: [{value, unit, source: policy_vX | ledger | dp_expectation}]
  sensitivity: [{param, delta, kết_luận_đảo_chiều?}]
  confidence: float + caveats: [str]
  infeasible_reason: str | null
```

## 3. Advisor pipeline (agent core)

```text
AdviceRequest → Router (deterministic, không LLM)
  ├─ STAGE 1 song song (independent): S1 · S2 · S3 · PolicyRetrieval(RAG)
  ├─ STAGE 2 (platform-level): S4 nhận candidates nhiều driver
  → Composer (LLM #1): briefing pack → ComposedAdvice
  → Verifier (LLM #2 hoặc rule): số-khớp-nguồn + guardrail §5 → pass / repair ≤1 / veto→template
  → AdviceEpisode → AdvisorStateStore (DecisionRecord append-only)
```

- **Hiện trạng trung thực:** repo CHƯA có agent harness/multi-agent nào được implement (chỉ có spec DP, research llm-advisor-architecture, smoke script LLM; T-005 CrewAI đang hoãn — thiết kế này thay thế đánh giá đó). Pipeline dưới đây là bản build đầu tiên; LLM chỉ xuất hiện từ C6.
- **Không multi-agent swarm** — 1 pipeline deterministic + đúng 2 vai LLM (Composer, Verifier). Model: deepseek-v4-flash chính; fallback gpt-4o-mini (403 — chờ Cường xin quyền); template fallback luôn chạy được (LLM-off mode).
- **Loop bounds**: solver single-pass; Composer↔Verifier ≤1 repair; F0 clarify ≤2 lượt; what-if residual có token budget. Không open-ended loop.
- **State**: agent stateless per-request; state ở L2/L3 + AdvisorStateStore (advice history, cooldown, adherence stats). Cập nhật state = ghi DecisionRecord sau mỗi episode — cơ chế duy nhất.
- **Context pack builder**: code deterministic versioned, budget cứng per section (policy excerpt đúng track+version; K episodes gần nhất; SolverReports; guardrail checklist); mọi mục có provenance + freshness.
- **Memory**: durable (DB — profile/adherence/episode) · session (TTL hết ca) · semantic cache (state-digest → advice). KHÔNG vector-memory hội thoại v1; RAG duy nhất = policy KB.
- **I/O format đóng băng** (3 schema versioned trong `schemas/`):
  - `AdviceRequest`: driver_id, feature ∈ {F0,F1,F2,F3}, free_text_query (nullable), l3_view_refs[], session_id, t_request, trigger_source (user_ask | anchor | event_trigger).
  - `SolverReport`: như §2.
  - `ComposedAdvice`: message, citations[], numbers[] (mỗi số kèm source), confidence, caveats[], `advice_spec` machine-checkable {action_type, target_window, target_zone/station|none, expiry} — theo taxonomy adherence `simulation-twin-world.md` §7.1, dùng cho T-020 đo adherence.

## 4. Agent-residual — danh sách ĐÓNG (chỗ modelling không với tới)

Ghi nhận Cường: "chưa thấy bài toán nào dùng agent — thuần modelling" là ĐÚNG THIẾT KẾ (D3). Agent có đúng 5 việc.

**Guardrail chung mọi R#** (kế thừa, không lặp từng ô): log `DecisionRecord` mỗi episode + `confidence` bắt buộc trong ComposedAdvice + fallback template khi Verifier veto / LLM-off (CLAUDE.md §5).

| R# | Residual | Vì sao KHÔNG formalize được | Guardrail riêng |
|---|---|---|---|
| R1 | F0 free-text policy Q&A | Không gian câu hỏi tự nhiên là mở — không enumerate được intent trước; hiểu ngôn ngữ + chọn đúng đoạn policy theo ngữ cảnh là năng lực NLU, không phải bài tối ưu | số từ S1; citation bắt buộc; thiếu track → hỏi lại (≤2) |
| R2 | Composer: hợp nhất nhiều SolverReport thành MỘT lời khuyên theo persona | "Chọn 1 trong 3 lời khuyên hợp lệ + nói sao cho P4 hiểu" không có objective function đo được — là judgment về ngôn ngữ/ưu tiên người dùng | chỉ dùng numbers[] có source; Verifier đối chiếu từng số |
| R3 | Infeasibility explanation | `infeasible_reason` là mệnh đề logic; biến nó thành lời khuyên trung thực + phương án thay thế phù hợp hoàn cảnh cần sinh ngôn ngữ có empathy — không có công thức | không hứa thu nhập; nêu bất định |
| R4 | What-if định tính ngoài model (mưa/sự kiện chưa có model) | Thiếu data/model production để formalize — reasoning tạm thời TRONG KHI CHỜ formalize | confidence thấp BẮT BUỘC |
| R5 | Out-of-taxonomy router | Nhận diện "câu này ngoài phạm vi" trên input mở là bài phân loại open-set — taxonomy đóng không phủ được | không bịa; route hoặc từ chối lịch sự |

**Residual shrinks over time**: khi R4 formalize được (vd có weather-demand model) → chuyển sang solver, cập nhật spec + minor version. Checkpoint mở rộng (T-039) nhắc việc này.

## 5. Thử nghiệm — mọi nhánh rẽ phải có EXP doc

`research/experiments/EXP-###-<slug>.md`: hypothesis / setup / metric / decision rule / kết luận.

| EXP | Nhánh rẽ | Metric quyết định |
|---|---|---|
| EXP-001 | Verifier: LLM #2 vs rule-only | faithfulness (100% số trace về nguồn) vs latency/cost |
| EXP-002 | Composer: 1 prompt chung vs per-feature | quality per F, token cost |
| EXP-003 | Demand forecast cho S2: historical mean vs model | schedule regret trên sim twin |
| EXP-004 | Briefing pack: full 4 reports vs relevant-only | hallucination rate, độ dài |
| EXP-005 | Model chính/fallback khi 403 giải quyết | như EXP-001 |

## 6. Metrics & observability (thiết kế TRƯỚC khi code — T-026 đồng thời)

Per-layer (Langfuse chính): router accuracy · solver feasibility-rate/latency/input-freshness · composer faithfulness (100% số trace nguồn) · guardrail violation count · verifier veto/repair rate · adherence proxy (advice_spec vs behavior sau đó) · end-metric = Δ payout twin-world (T-020). Bảng chi tiết chốt trong plan T-026, EXP nào cũng đọc từ đây.

## 7. Map advisor → sim actor (khung — chi tiết khi M4/T-019)

`ComposedAdvice.advice_spec` → sim `AdviceEvent` → adherence model (5 nhãn, twin-world §7) → actor override behavior. Placeholder tên field đặt sẵn trong schema để không sửa contract sau. Cường cho phép tính chi tiết sau khi khung agent bản đầu xong.

## 8. Thứ tự implement + backlog

**Track CORE chạy TRƯỚC; sim pause sau T-030 — M1–M4 (T-031..T-037) resume sau khung core.** Một ordering duy nhất cho observability: T-026 phase 1 (metric table) tại C2, phase 2 (Langfuse instrumentation) đồng thời C6 — không gắn sau; T-019 twin-integration kế thừa artifacts C6/C7.

```text
C0 (T-038a): schemas/ JSON Schema + validators + changelog        ← chốt schema
C1 (T-038b): MOCK DATA GENERATOR theo schema (chi tiết §8.1)
C2: metric table per-layer CHỐT (T-026 phase 1 — TRƯỚC khi code solver)
    + S1 BonusFeasibility + SolverReport envelope (verify dễ nhất)
C3: S2 ShiftDP        C4: S3 F3Patterns       C5: S4 CapacityAlloc
C6: Router + Composer + Verifier + context pack builder (LLM vào đây)
    + Langfuse instrumentation ĐỒNG THỜI (T-026 phase 2)
C7: EXP-001..005 chạy trên instrumentation của C6
Sau mỗi C#/T# hoàn thành: checkpoint T-039 — "MỞ RỘNG? (schema / bài toán tối ưu / tính năng)"
```

### 8.1 Chi tiết C1 — mock data generator (Cường: gen sạch, phản ánh thực tế, verify nhiều vòng)

- **Phương pháp gen per-entity:** L0 từ policy research thật (`bonus-programs.md` — bundle có effective date/version); L1 hai nguồn: (i) **adapter từ sim T-030** (world.events/segments → AppEvent/TripRecord/SwapTransaction/PayoutLedger — sim đã qua M0 integrity gate), (ii) sampler độc lập cho entity sim chưa có (GPSPing nội suy dọc segment 30s/ping, PolicyChangeEvent theo kịch bản). Tương quan BẮT BUỘC giữ: ledger amount tái tính được từ (policy_version, trip); event ordering hợp lệ per driver; GPS liên tục theo segment; SOC timeline khớp swap.
- **"Data sạch" acceptance:** 100% pass JSON Schema; 0 orphan FK; 0 event nghịch thời gian per driver; ledger↔trip↔policy khớp 100%; phân phối trong tolerance benchmark.
- **4 vòng verify — mỗi vòng 1 report `research/experiments/mockgen/`:**
  1. **Schema validation**: 100% record mọi entity.
  2. **Statistical realism** vs `research/simulation/realism-benchmarks.md`: trips FT 15–30/ngày, payout dải benchmark, hour-shape 2 đỉnh, dist median ~3.2–3.5km (calibration gap T-021 ghi chú), acceptance per archetype — **≥30 seeds**, tolerance/CI trong report (CLAUDE.md §4b).
  3. **Cross-entity consistency**: tái tính payout từ policy+trips so với ledger; SOC↔swap; GPS↔trip endpoints.
  4. **Adversarial review**: tìm pattern phi thực tế (driver 24h không nghỉ, trip 0 phút, thu nhập âm, GPS teleport) — flaw → sửa generator → chạy lại TỪ VÒNG 1.
- **Volume:** ≥30 ngày × 50 driver (scale theo nhu cầu solver); mọi record nhãn `MOCK` + seed + generated_at.
- Data thật GSM thay dần từng entity khi có export — cùng schema, chỉ đổi nguồn.

Backlog: **T-038** (C0+C1) · **T-039 recurring** (checkpoint sau mỗi phần — section bắt buộc trong `UPDATE_TEMPLATE.md`).

## 9. Không làm trong spec này

Realtime API ngoài (Open-Meteo/TomTom — chờ offline snapshot schema); vector memory hội thoại; multi-agent swarm; can thiệp dispatch; OCR policy (task riêng); weather-demand model production (R4 residual tới khi đủ data).
