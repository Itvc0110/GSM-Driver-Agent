# SPEC — Chương trình nâng cấp simulator reliability-first M0–M4 (v1)

Cập nhật: 2026-07-22 · Trạng thái: **APPROVED ROADMAP — IMPLEMENTATION GATED BY M0**  
Nguồn: quyết định Cường 2026-07-22; kế thừa `simulation-pilot-world.md`, `simulation-twin-world.md`, `advisor-optimization-layer-a.md`, `environment-variables.md` và `research/simulation/`.

## 0. Thẩm quyền, mục tiêu và non-goals

Spec này là source of truth về **thứ tự milestone, contract xuyên milestone, exit gate và verification protocol** của simulator từ 2026-07-22. Các spec cũ vẫn sở hữu công thức/domain detail, trừ điểm được override tường minh tại đây.

Mục tiêu:

1. Khóa correctness/reproducibility trước khi mở rộng realism hoặc UI.
2. Chuyển pilot thành market 00:00–24:00 với daily actor pool và supply động.
3. Làm không gian hybrid đúng nghĩa: H3 cho index/field, OSM lat/lon cho endpoint/movement.
4. Tạo visualization đủ giải thích cho stakeholder: market → actor journey → advisor.
5. Chỉ đo hiệu quả advisor sau khi baseline/world/evaluator qua gate.

Non-goals của chương trình:

- Không nới ranh giới sản phẩm: advisor không can thiệp matching/dispatch/pricing/routing và không khuyên nhận/từ chối/hủy một đơn cụ thể.
- Không trình bày số MOCK/PROXY như dữ liệu thật GSM.
- Không để LLM tạo số tài chính, xác suất hoặc policy.
- Không mở ngay toàn Hà Nội/N=500, road-routing edge-level, live API trong sim loop, multi-day trust dynamics hoặc full counterfactual branching.

Working diff Stage A–C tồn tại ngày 2026-07-22 (`geo/demand/dispatcher/world/congestion/trajectory...`) là **M0 audit input**, chưa phải implementation đã được chấp nhận. Không commit nguyên khối trước khi có invariant/regression tests.

## 1. Evidence taxonomy và nguyên tắc reliability

| Nhãn | Nghĩa | Cách dùng |
| --- | --- | --- |
| `[FACT]` | Nguồn primary/official hoặc invariant kỹ thuật đã chứng minh | Ghi nguồn/test cụ thể |
| `[OBSERVED-CODE]` | Quan sát trực tiếp từ code, diff, test hoặc output sim | Không đồng nghĩa với thực tế GSM |
| `[PROXY]` | Biến thay thế gián tiếp | Ghi nguồn, giới hạn và confidence |
| `[MOCK]` | Dữ liệu/tham số tổng hợp phục vụ sim | Ghi seed/version/ngày tạo |
| `[ASSUMPTION]` | Giả định thiết kế chưa đủ bằng chứng | Ghi tác động nếu sai + task verify |
| `[UNVERIFIED]` | Claim chưa kiểm chứng | Không dùng làm policy/fact |

Mỗi claim không phải `[FACT]` phải có: nguồn/lý do, confidence, tác động nếu sai, và task verify/calibrate hoặc điều kiện defer.

### 1.1 Phân loại flaw

- **BUG:** vi phạm contract/invariant; cần reproduction + failing regression test trước fix.
- **MODEL GAP:** code đúng như viết nhưng mô hình thiếu cơ chế.
- **CALIBRATION GAP:** công thức hợp lệ nhưng tham số/phân phối chưa đủ bằng chứng.
- **VISIBILITY GAP:** engine có state nhưng không quan sát/giải thích được.
- **DEFER:** có giá trị nhưng chưa cần để qua milestone gate hiện tại.

Không chỉnh calibration để che BUG. Chưa reproduce/prove root cause thì ghi `UNRESOLVED`, không ghi “fixed”.

## 2. Dependency graph và quyền sở hữu

```text
M0 — SIM INTEGRITY
  lifecycle + conservation + determinism + audit working diff
          ↓
M1 — 24H DYNAMIC MARKET
  00:00–24:00 + daily actor pool + validated demand/supply
          ↓
M2 — SPATIAL & EXOGENOUS WORLD
  OSM endpoints + H3 dispatch + congestion/weather/events/shifts
          ↓
M3 — STAKEHOLDER VISUALIZATION
  city pulse → actor journey → advisor placeholder + diagnostic mode
          ↓
M4 — ADVISOR & TWIN RUNNER
  advice→actor policy/adherence → paired A/B/C → evaluator/observability
          ↓
T-027 — ROBUSTNESS/SHIFT VALIDATION
```

- T-018 sở hữu deterministic runner/core substrate.
- T-021 là calibration/realism gate xuyên milestone.
- T-019 + T-026 sở hữu advisor + observability.
- T-020 sở hữu A/B/C orchestration, evaluator và attribution; không sở hữu dashboard chung.
- T-027 sở hữu robustness validation sau M2/M4; không xây world engine.

## 3. Contract xuyên milestone

### 3.1 Canonical entities

| Entity | Trách nhiệm |
| --- | --- |
| `DriverActor` | State, location, SOC, shift, actions, earnings counters |
| `CustomerActor` | Created → waiting → matched → picked-up → completed/cancelled |
| `OrderRequest` | Liên kết customer, endpoint, fare/policy, patience và timestamps |
| `Station` | Battery inventory, charging/ready state, reservation và queue |
| `EnvironmentTrace` | Weather/event/traffic/day-type snapshot dùng chung mọi arm |
| `DecisionRecord` | Observation → baseline/advisor action → confidence/reason → adherence → outcome |

Mọi state transition phát **canonical event**. Segment, snapshot, Gantt và chart là derived views; không trở thành source of truth thứ hai.

### 3.2 Canonical state machines

Driver:

```text
OFFLINE → AVAILABLE/IDLE → OFFERED → ENROUTE → ON_TRIP → AVAILABLE
                          ↘ RELOCATING / RESTING / CHARGING / SWAPPING ↗
AVAILABLE → OFF_SHIFT
```

Customer/order:

```text
CREATED → WAITING → MATCHED → PICKED_UP → COMPLETED
                    ↘ CANCELLED_BEFORE_MATCH / CANCELLED_AFTER_MATCH
```

Mỗi order có đúng một terminal state hoặc nhãn `CENSORED_END_OF_RUN` có lý do.

### 3.3 Time semantics

- Engine source of truth: SimPy DES, timestamp liên tục.
- Dispatch tick: mặc định 5 giây, là cơ chế matching riêng.
- Observation/replay bins: per-event hoặc 1/5/15 phút; không thay đổi engine.
- M1 target horizon: `[00:00,24:00)`, tức `t=0` thuộc ngày và `t=1440` không thuộc ngày.

### 3.4 Spatial semantics và dispatch contract

- H3 res 9: demand/supply field, congestion, candidate shortlist và aggregation.
- OSM road/POI lat/lon: endpoint, movement, route/distance và visualization.
- Movement phải cập nhật `lat`, `lon`, `H3 cell` nguyên tử; invariant: `actor.cell == h3(actor.lat, actor.lon)` sau mọi leg.
- Dispatch pipeline:

```text
OSM pickup node → pickup H3
       → H3 k-ring candidate shortlist
       → continuous/road distance + path-time speed
       → ETA gate
       → deterministic tie-break (ETA, distance, actor_id)
```

Không actor ngoài `k_max` được chọn. Fallback Haversine×detour phải có reason/mode trong event và manifest, không trộn silently với road mode.

### 3.5 Money, policy và information boundary

- Gross fare, driver payout, points/bonus chỉ do policy/rule component tính.
- Flaw detector trước paired evaluator chỉ được nêu observed facts hoặc `[HEURISTIC]`; không trình bày số “mất tiền” chắc chắn.
- Baseline actor/advisor không được nhìn realized future orders hoặc future environment state ngoài forecast được phép.
- External inputs phải fetch/snapshot/version **trước run**; không gọi live API trong deterministic sim loop.

## 4. M0 — Simulator integrity gate

### 4.1 Mục tiêu

Audit working diff Stage A–C và baseline hiện tại trước khi thêm behavior. Tách correctness defect, calibration gap, MOCK/PROXY hợp lệ và visualization-only defect.

### 4.2 P0 flaw inventory cần reproduce

| Flaw nghi ngờ | Loại ban đầu | Gate |
| --- | --- | --- |
| Battery trả trạm ở SOC=0 không chuyển đúng charging→ready; actor có thể lấy pin sau wait cap dù không ready | BUG nghiêm trọng | Battery conservation + không phát quá ready inventory |
| Cùng `(order, actor)` bị offer lặp mỗi dispatch tick sau decline/thiếu SOC | BUG/MODEL GAP | Offer history/cooldown invariant |
| `hour_interp` đọc config nhưng chưa tác động generator | BUG | Continuity test theo bins |
| Demand hint dùng toàn bộ realized order trace cùng giờ | Information leak | Allowed-information test |
| Actor belief resample mỗi idle check | MODEL GAP | Stable actor×time-bucket belief |
| Customer thiếu MATCHED/cancel-after-match/terminal conservation | LIFECYCLE GAP | Exactly-one terminal state |
| Run end cắt ENROUTE/ON_TRIP/CHARGE không có censor/carry-over policy | BOUNDARY GAP | End-of-day invariant |
| `online_min`/activity durations có thể không bảo toàn khi actor bận lúc end | BUG cần test | Per-actor time conservation |
| Meal rest có thể lặp nhiều lần trong cùng giờ | MODEL BUG | Max meal-break/window |
| Home charge không có travel về home | SPATIAL BUG | Explicit home-bound leg |
| Sampled endpoint và `dist_km` không cùng distance contract | CONSISTENCY GAP | Route/fare/time contract |
| `_set_pos` không tự sync H3 cell | Fragile contract | Atomic movement API |
| Dispatch dừng ở first non-empty H3 disk | Algorithm semantics | Chốt semantics + test cạnh biên |
| Tie-break actor chưa khóa đầy đủ | Determinism gap | Stable assignment trace |
| `order_expired` từng bọc nested `detail` | BUG đã thấy | Regression test event schema |

Danh sách này không phải kết luận root cause; T-030 phải reproduce/classify từng mục.

### 4.3 Audit artifact

Mỗi run/gate phải xuất hoặc tổng hợp được:

- invariant failures;
- censored entities;
- state overlap/time gaps;
- money, battery và order conservation;
- spatial/H3 mismatches;
- order lifecycle counts;
- distribution goodness-of-fit;
- multi-seed variance;
- sensitivity direction;
- evidence labels/assumptions;
- unresolved/new flaws.

### 4.4 Exit gate M0

- Full suite xanh.
- Cùng seed/config cho canonical trace/log exact repeat; field volatile bị loại phải được định nghĩa rõ.
- Mọi P0 flaw có verdict + regression/invariant hoặc task/defer rõ.
- Không target leakage: B-arm được gate theo plausible/stable/explainable, không ép về target A-arm.
- Working diff Stage A–C chỉ được giữ phần vượt test; phần không đạt sửa/revert trong plan M0 được duyệt.
- Diagnostic visualization tối thiểu mở được cho state/lifecycle review.

## 5. M1 — 24h dynamic market

### 5.1 Supply semantics

`actors.n` = **daily actor pool**, không phải concurrent active count. Mỗi actor có:

- participation decision;
- shift template + start jitter;
- optional split shift/overtime/early offline;
- scheduled/online distinction;
- rest/meal/charge/swap;
- weather-sensitive participation;
- fatigue/max-duty constraints.

UI/metrics luôn tách:

```text
daily pool | participating today | scheduled now | online now
idle | offered/enroute | on-trip | relocating | rest | charging/swap | offline
```

Persona constraints giữ ý nghĩa: P1 part-time tối; P2 phủ hai peak; P3 dài giờ có fatigue; P4 có thể lệch khung; P5 prior tốt nhưng có thể stale khi shift.

### 5.2 Demand semantics

- `orders_per_day` là kỳ vọng toàn `[00:00,24:00)`.
- Dùng non-homogeneous Poisson process hoặc piecewise-linear intensity; weather/event factor tại event time, không chỉ midpoint giờ.
- Không fail một seed vì count không bằng kỳ vọng; gate trên ensemble và tolerance thống kê.
- Validation: total mean/variance, share theo hour và bins 1/5/15 phút, boundary continuity, H3 spatial share, OD distance và event residual additive exactly once.

### 5.3 Exit gate M1

- Tests cho `t=0`, `00:01`, `23:59`, `t=1440`.
- Demand ensemble mặc định ≥30 seeds khớp configured shape trong tolerance được ghi.
- Active supply curve giải thích được theo persona/shift; không actor online ngoài shift policy.
- Không còn chuỗi nhiều giờ 0% served chỉ do shift artifact, trừ labeled supply-shock scenario.
- Visual review dry weekday + weekend; thêm rain nếu participation channel bị tác động.

## 6. M2 — Spatial và exogenous world

### 6.1 OSM endpoint provider

- Pickup/dropoff snap vào OSM road node hoặc POI entrance, lưu `osm_id`, source, category, timestamp/bundle hash và H3.
- Fetch/cache/normalize trước run; sim chỉ đọc immutable versioned bundle.
- Offline replay không gọi network; thiếu cache phải error rõ.
- Endpoint v1 có thể dùng Haversine×detour với nhãn `route=approximated`; road graph chỉ mở sau endpoint gate.

### 6.2 Congestion và environment

Tách attribution:

- base traffic profile;
- demand-correlated traffic `[PROXY]`;
- weather slowdown;
- event route effect/closure.

Kết hợp reduction bằng survival product có cap và log raw/capped. Density field cần spatial smoothing H3 + time interpolation. Không dùng realized arm outcome để tạo exogenous congestion cho chính arm; physical trace có thể dùng latent field nhưng observation chỉ nhận forecast/past được phép.

### 6.3 Distribution shifts

Registry tối thiểu:

- weather;
- weekday/weekend/holiday;
- concert/sports/exam;
- road closure/incident;
- policy/bonus-window change;
- geographic hotspot migration;
- supply participation shock;
- demand regime 900/1200/1800.

Mỗi shift có `known_at`, `effective_at`, source/confidence và channels tác động.

### 6.4 Exit gate M2

- OSM bundle hash + seed/config cho exact replay.
- 100% trip ghi `road` hoặc explicit fallback mode.
- H3 dispatch invariants, deterministic tie-break và location continuity xanh.
- Environment/congestion trace giống nhau giữa arms.
- Tắt từng factor quay về baseline theo tolerance đã khai báo.
- Visual review dry/rain/event và candidate-ring/spatial diagnostic.

## 7. M3 — Stakeholder và diagnostic visualization

### 7.1 Story Mode

Narrative 60–90 giây:

1. **City pulse:** market 24h, demand/supply/congestion/weather/station queue và lifecycle.
2. **Actor journey:** chọn actor, xem route, state Gantt, SOC, payout/points, cuốc, idle/relocate/rest/charge và flaw callouts.
3. **Advisor:** trước M4 chỉ hiện placeholder `ADVISOR CHƯA ĐƯỢC BẬT`; sau M4 mới so paired A/B/C.

Player hỗ trợ per-event hoặc bins 1/5/15 phút; play speed 1×/4×/16×/60×; cùng playhead cho mọi chart/layer và paired arms.

Map z-order:

1. basemap;
2. H3 fill bán trong suốt (mặc định không extrude trong Story Mode);
3. weather/event/congestion outline;
4. customers/orders;
5. driver paths;
6. actor markers;
7. station markers trên cùng với halo và toggle.

Flaw labels:

- `OBSERVED`: state/event thật trong sim;
- `HEURISTIC`: cơ hội nghi ngờ, không khẳng định tiền mất;
- `PAIRED_COUNTERFACTUAL`: chỉ sau M4 evaluator.

### 7.2 Diagnostic Mode

- demand configured vs realized + confidence bands/residual/boundary continuity;
- pool→participating→scheduled→online→state funnel;
- lifecycle/conservation/censoring;
- H3 boundaries, OSM endpoints, candidate rings, winner/loser và spatial mismatch;
- station inventory/queue;
- seed/config/spec/git/data hashes, fallback modes và audit panel.

### 7.3 Exit gate M3

- Stakeholder hiểu market → actor → advisor slot trong 60–90 giây.
- Map/charts/entity states đồng bộ playhead.
- Station không bị H3 che; chart có unit/provenance/mock label.
- AppTest + browser review nhiều scenario; Cường xem UI đang chạy và ghi verdict trước commit/push, trừ explicit waiver.

## 8. M4 — Advisor và twin-runner

Thứ tự:

1. deterministic advice spec/rule layer;
2. trigger + capacity ledger;
3. placebo C random-safe;
4. adherence model;
5. paired A/B/C runner cùng exogenous bundle;
6. evaluator/attribution;
7. LLM offline render/personalize;
8. observability per layer.

`DecisionRecord` phải ghi observation time, allowed information, action, confidence, reason, TTL, adherence và outcome. Advisor chỉ tác động policy/action constraints hợp lệ; actor vẫn quyết định. LLM-off/template fallback là supported mode.

Exit gate:

- Exogenous demand/weather/event/initial actor state giống nhau giữa A/B/C.
- Báo `A−B`, `C−B`, `A−C`; tách ITT/CACE và upper-bound adherence.
- Không kết luận từ một seed; dùng paired CI protocol được duyệt.
- Không future leak; capacity/adherence/fallback/observability có log.
- Paired visualization dùng chung playhead; diagnostic hiển thị divergence.

## 9. Verification protocol mặc định

| Loại thay đổi | Mặc định | Mục đích |
| --- | --- | --- |
| Deterministic invariant/bug | Exact repeat + minimal reproduction | Chứng minh contract |
| Stochastic behavior regression | ≥5 seeds + boundary scenarios | Tránh seed-specific fix |
| Distribution/calibration | ≥30 seeds + tolerance/CI | Kiểm shape/variance |
| M4 paired evaluation | Protocol CI riêng, không một seed | Đo effect hợp lệ |

Plan có thể thay số seed khi giải thích rõ statistical power/cost. UPDATE phải ghi seed/scenario thực chạy.

## 10. Quy trình visual review sau update

Sau meaningful sim/UI update:

1. launch dashboard/replay thật;
2. mở seed/scenario cố định cho Cường;
3. ghi rõ điều cần kiểm;
4. chờ verdict trước commit/push, trừ explicit waiver trong hội thoại hiện tại;
5. launch lỗi → `BLOCKED`, không gọi complete;
6. docs-only/test-only/refactor chứng minh không đổi output → `NOT_APPLICABLE` có lý do.

Visual gate không tự cấp quyền commit/push.

## 11. Deferred và điều kiện mở lại

- Road graph/OSRM: sau OSM endpoint v1 + distance contract gate.
- Edge-level traffic: sau route graph hoặc traffic source phù hợp.
- Multi-district/multi-map, res8/N=500: sau Đống Đa 24h ổn định.
- Live external APIs: sau offline snapshot schema/versioning; không gọi trong sim loop.
- Multi-day trust dynamics và full counterfactual branch: sau M4 eval gate.
- GPU/large-scale optimization: chỉ khi profiling chứng minh bottleneck.

## 12. Mapping backlog

- T-029: governance + master spec (lượt docs này).
- T-030: M0 integrity/audit Stage A–C.
- T-031: M1 24h dynamic market.
- T-032–T-034: M2 endpoint, dispatch/routing contract, exogenous traces.
- T-035–T-037: M3 Story Mode, actor journey, Diagnostic Mode/visual harness.
- T-019/T-026/T-020: M4 advisor/observability/twin evaluator.
- T-027: post-M4 robustness validation.
