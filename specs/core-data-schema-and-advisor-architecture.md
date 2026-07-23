# SPEC — Core Data Schema & Advisor Architecture (v1)

Cập nhật: 2026-07-23 · Trạng thái: **DESIGN APPROVED (brainstorm Cường 2026-07-23) — chờ review file để vào plan**
Nguồn: brainstorm Cường 2026-07-23; kế thừa `simulation-reliability-upgrade.md` §3.5 (observable/inferable/latent), `advisor-optimization-layer-a.md` (DP), `advice-timing-state-memory.md` (trigger/memory), `planning/USER_STORIES.md`, `research/community/pain-points.md`, `research/simulation/llm-advisor-architecture.md`.
Bối cảnh mới: **dự án hợp tác chính thức với GSM — có quyền truy cập data thật** (Cường 2026-07-23) → schema **platform-centric**.

## 0. Quyết định nền (đã chốt trong brainstorm)

| # | Quyết định | Lựa chọn |
|---|---|---|
| D1 | Góc nhìn data | **Platform-centric** — gồm supply/demand field, station state thật của GSM |
| D2 | Bài toán modelling lõi | **4 solver**: ShiftDP, BonusFeasibility, F3Patterns, CapacityAlloc — thuần math, KHÔNG agent |
| D3 | Ranh giới math vs agent | **Solver-first, agent-residual**: mặc định mọi bài formalize được đi solver; agent chỉ nhận residual liệt kê ĐÓNG (§5) |
| D4 | Kiến trúc schema | **4 tầng + event backbone** (L0 reference → L1 event log → L2 state fields → L3 feature views) |

Ràng buộc bất biến (CLAUDE.md §5): agent không tự tính số tài chính/xác suất; tách `gross_revenue`/`driver_payout`/`estimated_net_income`; mock có nhãn; không can thiệp matching/dispatch/pricing/routing; không khuyên nhận/từ chối đơn cụ thể.

## 1. Schema 4 tầng

### 1.1 Sơ đồ

```text
L0 REFERENCE (slowly-changing, versioned)
  PolicyBundle · DriverProfile · StationRegistry · ZoneMap(H3) · ServiceCatalog
      ↓ FK
L1 EVENT LOG (immutable, append-only — NGUỒN SỰ THẬT)
  AppEvent · TripRecord · GPSPing · SwapTransaction · PayoutLedger · PolicyChangeEvent
      ↓ derivation JOB (code có version — không sửa tay)
L2 STATE FIELDS (bucket 15ph × H3 — platform data thật)
  SupplyField · DemandField · StationState · DriverDayState
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
| `InferredActivity(driver, segment)` | **INFERRED** label ∈ {rest_likely, charging_likely, relocating, idle_wait} từ GPS+event gaps, kèm `inference_rule_version` + confidence | Inferable tầng — KHÔNG BAO GIỜ trình bày như đo được; nuôi F3 |

### 1.5 L3 — Feature views (hợp đồng input solver)

`ShiftPlanInput` (buckets còn lại, SOC, demand forecast per cell-cluster, điểm/mốc, ngưỡng hồ sơ) · `BonusGapInput` (điểm hiện tại, mốc kế, tốc độ điểm lịch sử theo khung giờ, quỹ giờ) · `SessionSummaryInput` (trip timeline + InferredActivity + payout breakdown) · `AllocationInput` (candidate advice nhiều driver + StationState + SupplyField).

### 1.6 Versioning & extensibility (yêu cầu Cường: dư địa update)

- Mỗi entity: `schema_version` semver. **Thêm** = optional field + minor bump. **Bỏ** = `deprecated_since` + ≥1 chu kỳ chuyển tiếp, không xóa thẳng.
- Field chưa chắc GSM export được: nhãn **`AVAILABILITY: TBC-với-GSM`** (GPSPing tần suất, queue đo được, SOC telemetry, request-log unserved). Mỗi TBC có fallback ghi sẵn (vd không có request-log → DemandField chỉ có served, unserved là ước lượng có nhãn).
- `sensitivity` per field (PII: lat/lon thô, driver_id) → cơ chế thu hẹp/anonymize khi cần.
- **Sim map cùng schema**: sim runner xuất L1 events đúng format này (adapter từ `world.events`/`segments`) → twin-world eval và product dùng chung pipeline; dữ liệu sim phải bám phân phối thực tế (benchmark research + data thật khi có).
- Registry `schemas/` trong repo: JSON Schema per entity + validator + changelog.

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

- **Không multi-agent swarm** — 1 pipeline deterministic + đúng 2 vai LLM (Composer, Verifier). Model: deepseek-v4-flash chính; fallback gpt-4o-mini (403 — chờ Cường xin quyền); template fallback luôn chạy được (LLM-off mode).
- **Loop bounds**: solver single-pass; Composer↔Verifier ≤1 repair; F0 clarify ≤2 lượt; what-if residual có token budget. Không open-ended loop.
- **State**: agent stateless per-request; state ở L2/L3 + AdvisorStateStore (advice history, cooldown, adherence stats). Cập nhật state = ghi DecisionRecord sau mỗi episode — cơ chế duy nhất.
- **Context pack builder**: code deterministic versioned, budget cứng per section (policy excerpt đúng track+version; K episodes gần nhất; SolverReports; guardrail checklist); mọi mục có provenance + freshness.
- **Memory**: durable (DB — profile/adherence/episode) · session (TTL hết ca) · semantic cache (state-digest → advice). KHÔNG vector-memory hội thoại v1; RAG duy nhất = policy KB.
- **I/O format đóng băng**: `AdviceRequest` / `SolverReport` / `ComposedAdvice` (message, citations, numbers-with-source, confidence, `advice_spec` machine-checkable — dùng lại advisor-layer-a §7.1 cho adherence).

## 4. Agent-residual — danh sách ĐÓNG (chỗ modelling không với tới)

Ghi nhận Cường: "chưa thấy bài toán nào dùng agent — thuần modelling" là ĐÚNG THIẾT KẾ (D3). Agent có đúng 5 việc:

| R# | Residual | Vì sao không formalize được | Guardrail |
|---|---|---|---|
| R1 | F0 free-text policy Q&A | intent tự nhiên + tra policy đúng track/version + gọi S1 lấy số + diễn giải có trích dẫn | số từ solver; citation bắt buộc; thiếu track → hỏi lại (≤2) |
| R2 | Composer: hợp nhất nhiều SolverReport thành MỘT lời khuyên theo persona | chọn-và-diễn-giải là judgment | chỉ dùng numbers[] có source; Verifier đối chiếu |
| R3 | Infeasibility explanation | biến `infeasible_reason` cứng thành lời trung thực + phương án thay thế | không hứa thu nhập; nêu bất định |
| R4 | What-if định tính ngoài model (mưa/sự kiện chưa có model) | chưa có model production | confidence thấp bắt buộc + log + fallback template |
| R5 | Out-of-taxonomy router | câu hỏi lạ → trả lời được/không | không bịa; route hoặc từ chối lịch sự |

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

```text
C0 (T-038a): schemas/ JSON Schema + validators + changelog        ← chốt schema
C1 (T-038b): MOCK DATA GENERATOR theo schema — GEN CHI TIẾT,
     VERIFY NHIỀU VÒNG: (a) schema validation
                        (b) statistical realism vs research benchmarks
                        (c) cross-entity consistency (ledger↔trips↔policy↔events)
                        (d) adversarial review — mỗi vòng có report riêng
     nguồn gen: sim T-030 (adapter) + sampler độc lập; nhãn MOCK + seed + ngày
C2: S1 BonusFeasibility + SolverReport envelope (verify dễ nhất)
C3: S2 ShiftDP        C4: S3 F3Patterns       C5: S4 CapacityAlloc
C6: Router + Composer + Verifier + context pack builder (LLM vào đây)
C7: EXP-001..005 + Langfuse (T-026)
Sau MỖI C#: checkpoint T-039 — "MỞ RỘNG? (schema / bài toán tối ưu / tính năng)"
```

Backlog mới: **T-038** (C0+C1 — chốt schema + mock gen multi-round verify) · **T-039 recurring** (expansion checkpoint sau mỗi phần hoàn thành — nhắc trong UPDATE mỗi cycle).

## 9. Không làm trong spec này

Realtime API ngoài (Open-Meteo/TomTom — chờ offline snapshot schema); vector memory hội thoại; multi-agent swarm; can thiệp dispatch; OCR policy (task riêng); weather-demand model production (R4 residual tới khi đủ data).
