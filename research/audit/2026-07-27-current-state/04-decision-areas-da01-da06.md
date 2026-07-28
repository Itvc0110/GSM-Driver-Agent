# 04 — Decision areas ĐA-01..ĐA-06

## 1. Trạng thái quyết định

| Mã | Trạng thái 2026-07-27 | Phạm vi |
|---|---|---|
| **ĐA-01** | **APPROVED-DESIGN** | Estimator acceptance/completion thống nhất bằng shrinkage; chưa implement. |
| **ĐA-02** | **APPROVED-DESIGN** | B1 mission time-window; B2 shared-trip counting vẫn blocked bởi policy thật. |
| **ĐA-03** | **APPROVED-DESIGN** | Chỉ p_accept + avg_dist personalization theo dòng duyệt hiện hành; chưa tự nhập thêm S2-1/band-flooring. |
| **ĐA-04** | **RESEARCHED — PENDING APPROVAL** | `AdviceCadencePolicy` dùng chung + fix adherence washout. |
| **ĐA-05** | **RESEARCHED — PENDING APPROVAL** | Canonical append-only advice lifecycle store + rebuildable projections. |
| **ĐA-06** | **RESEARCHED — PENDING APPROVAL** | Canonical card envelope v2 + một giọng nói + trace hai mức. |

`APPROVED-DESIGN` không đồng nghĩa đã code/test. Cycle này chỉ đóng tài liệu và dependency.

## 2. ĐA-01 — estimator thống nhất

### Quyết định đã duyệt

Một hàm dùng chung cho core/sim/UI:

```text
shrunk_rate(k, n, p0, m) = (k + m × p0) / (n + m)
```

- `p0` ưu tiên pooled counts lịch sử cá nhân `Σk/Σn`, không mean-of-daily-ratios;
- fallback tiếp theo là cohort/archetype/population, gắn `ASSUMPTION` và provenance;
- không bao giờ fallback 1.0 chỉ vì `n=0`;
- `m` là config, default candidate = 5; phải recalibrate, không hard-code như chân lý;
- advice/forecast dùng estimate; việc chấm policy payout vẫn dùng realized raw rate theo rule;
- response phải mang `k`, `n`, `p0`, `m`, prior source, estimator version và `as_of`.

### Data path cần thống nhất

| Call site hiện rời rạc | Hành vi đích |
|---|---|
| L1 feature `bonus_gap` | Gọi canonical estimator; counts chỉ đến `t_now`. |
| L1R adapter `from_l1r` | Không carry/fallback bí mật; ghi prior source. |
| UI Advisor adapter | Không tự median/whole-day rate khác core. |
| Sim `advice_bridge` | Không cutoff cứng rồi dùng realized thô từ offer thứ 5. |
| DriverMemory | Lưu pooled counts và boundary ngày/ca rõ ràng. |

### Gate kiểm chứng

1. unit/property tests cho `n=0`, small-n, large-n, `p0∈[0,1]`, monotonicity;
2. no-future-leak: counts chỉ đến `as_of`;
3. raw policy eligibility giữ nguyên;
4. 30-seed common-random-number sweep trước/sau, báo shift theo archetype và advice frequency;
5. calibration/Brier hoặc reliability bins nếu estimator dùng như probability;
6. parity: cùng counts/prior thì sim/UI/core ra cùng estimate tuyệt đối.

## 3. ĐA-02 — mission knapsack biết cửa sổ giờ

### B1 đã duyệt

- tách campaign validity (`start_time/end_time`) khỏi service/eligible windows;
- dùng interval half-open `[start, end)` và timezone explicit;
- hỗ trợ nhiều window, overlap, cross-midnight;
- tại `t_now`, chỉ giữ capacity từ phần giao giữa eligible windows và budget còn lại;
- nếu `remaining_count > eligible_capacity`, mission là infeasible, không hứa reward;
- đưa window/capacity/bound reason vào solver numbers/trace;
- UI nói “không còn đủ khung giờ phù hợp”, không chỉ nói “thiếu X giờ” chung chung.

### B2 chưa được phép đoán

Nhiều mission lồng nhau có thể cùng đếm một trip hoặc không. Logic này phụ thuộc policy GSM thật
(`D-POL-05`). Cho tới khi có nguồn:

- không giả định cộng effort độc lập là chính xác;
- gắn caveat “upper bound” nếu vẫn cần estimate;
- không implement shared-trip set packing như rule production.

### Gate kiểm chứng

Boundary test đúng tại start/end, DST không áp dụng nhưng timezone +07:00 vẫn explicit, window qua
nửa đêm, two overlapping windows, expired mission, no remaining capacity, và B1 không thay result
của mission không có window restriction.

## 4. ĐA-03 — personalization cho S2

### Scope đã duyệt

Đúng phạm vi hiện ghi trong `PENDING-REVIEW`: **truyền p_accept cá nhân + avg_dist cá nhân** vào
Shift DP. Không tự mở rộng approval sang band-flooring S2-1 hoặc các finding khác.

- `p_accept`: lấy từ ĐA-01, cùng estimator/provenance/as-of;
- `avg_dist`: rolling 28 ngày, winsorized để giảm outlier;
- fallback: driver → cohort/fleet → assumption rõ ràng 3 km;
- `avg_dist` phải nêu nó là pickup/served trip/total route distance nào; không trộn unit;
- mọi input dùng cho E[payout] phải nằm trong `numbers[]`/trace.

### Dependency

ĐA-03 phụ thuộc ĐA-01; không nên implement p_accept riêng trước rồi thay lại. Finding band-flooring
S2-1 cần một bugfix cycle riêng hoặc user mở rộng approval.

### Gate kiểm chứng

- fixture cho driver đủ/thiếu lịch sử, outlier distance, cohort fallback;
- no-future-leak rolling window;
- exact-repeat cùng seed/input;
- 30-seed CRN so trước/sau, report cả advice rate, payout driver, fleet effect và fairness;
- parity sim/app cho cùng driver projection.

## 5. ĐA-04 — AdviceCadencePolicy dùng chung

### Vấn đề

Hiện có ba semantics: sim trigger/tick, app giờ đồng hồ cố định và spec theo pha ca. Sim còn có thể
rút adherence coin lại đến khi “follow”, làm mức adherence hiệu dụng cao hơn config. A/B vì vậy
chưa đo intervention giống product.

### Hướng đề xuất

Một component deterministic, không nằm trong UI:

```text
evaluate(candidate, driver_state, shift_phase, lifecycle_memory, safety_state)
  → PRESENT | QUEUE | SUPPRESS
  + typed reason + next_eligible_at + material_revision
```

Baseline giữ đúng quyết định docs hiện có:

- cooldown ≥20 phút/topic;
- tối đa 6 proactive advice/shift;
- priority safety > policy/bonus > demand;
- anchor theo **pha ca**, không wall-clock 09:00/14:00/21:30;
- while-driving → queue/suppress theo safety class;
- một adherence draw cho `(decision_id, material_revision)`, không re-roll mỗi tick;
- cadence chặt hơn chỉ là experiment arm, không thay baseline âm thầm.

Reason codes ví dụ: `duplicate_window`, `topic_cooldown`, `shift_budget_exhausted`,
`unsafe_while_moving`, `stale_input`, `dismissed_for_window`, `superseded`, `low_value`.

### Cần Cường duyệt

**Recommendation:** duyệt hướng trên và coi 20 phút/6 advice là baseline đầu tiên; mọi tuning sau
dựa trên telemetry/micro-randomized evaluation, không bằng cảm giác.

## 6. ĐA-05 — canonical advice lifecycle store

### Vấn đề

EpisodeStore, UI JSONL và sim events dùng ID/schema khác nhau; không trả lời được một decision đã
được show/dismiss/follow ra sao. Content hash public cũng dễ collision/privacy/linkability và không
đủ biểu diễn cùng content được show nhiều lần.

### Hướng đề xuất

Local-first **append-only SQLite event log** + rebuildable projections; JSONL chỉ là debug/export;
EpisodeStore trở thành legacy adapter trong giai đoạn migration.

IDs tách vai trò:

| ID | Vai trò |
|---|---|
| `decision_id` | Một quyết định logic/candidate tại context revision. |
| `display_id` | Một lần card được present. |
| `event_id` | Mỗi lifecycle event, idempotency key. |
| `request_id/trace_id` | Quan sát pipeline; không thay decision identity. |

Envelope event cần `occurred_at` và `observed_at`, actor/source/schema version, reason code và
context revision. Dùng UUID opaque hoặc keyed HMAC cho dedupe nội bộ; không dùng plain hash của
content làm public ID.

SQLite chỉ có một writer tại một thời điểm, nên cần bounded write queue/retry và đo `SQLITE_BUSY`.
Không bật WAL một cách mù quáng trên SQLite cũ: WAL-reset bug ảnh hưởng các bản đến 3.51.2 và được
sửa ở 3.51.3 (có backport 3.44.6/3.50.7).

Nguồn: [SQLite WAL documentation](https://sqlite.org/wal.html).

### Dependency bắt buộc

Sửa `BLOCKER-ARCH-VERSION` trước hoặc cùng cycle. Nếu registry chỉ biết một schema/entity, event log
append-only sẽ không replay được qua migration.

### Cần Cường duyệt

**Recommendation:** SQLite event log canonical + projections, JSONL export, EpisodeStore adapter;
chưa đưa cloud/event bus vào publish mock-local.

## 7. ĐA-06 — canonical card envelope v2 và một giọng nói

### Vấn đề

Pipeline C6 compose một blob nhiều solver; web cards có contract/giọng riêng; Flutter hard-code.
Guardrail và number provenance không bao phủ đồng nhất mọi client.

### Hướng đề xuất

`AdviceEnvelopeV2` chứa `list[card]`; v1 blob chỉ tồn tại qua adapter migration.

Mỗi card tối thiểu có:

- `decision_id`, `card_id/display_policy`, `topic`, `priority`, `phase`;
- `title`, `message`, `primary_action`, `secondary_action`, `why`;
- `valid_from`, `expires_at`, `next_eligible_at`;
- `numbers[]`: name, value, unit, source_ref, `as_of`, evidence kind, data mode;
- `caveats`, confidence/calibration band, freshness, policy reason;
- `lifecycle_policy` và typed suppression/dismiss semantics.

Verify từng card; card hỏng bị loại. Nếu toàn bộ hỏng, trả silent `verification_failed` và trace
nội bộ, không trả text chưa kiểm. Driver mini-trace chỉ nói “dựa trên gì / cập nhật lúc nào / điều
kiện nào”; reviewer trace giữ solver/model/constraint detail.

Giọng tiếng Việt: trung tính, tôn trọng quyền quyết định, ít đại từ, không hứa, không shaming,
không jargon như bucket/E[payout] ở mặt driver.

### Cần Cường duyệt

**Recommendation:** v2 list-of-cards là canonical; web/Flutter/sim preview cùng render adapter;
deprecate v1 blob có thời hạn sau khi parity tests xanh.

## 8. Dependency map và thứ tự khuyến nghị

```text
BLOCKER-R5-MUT10 ──► restore + regression verification

BLOCKER-ARCH-VERSION ──► ĐA-05 lifecycle store ──► ĐA-04 cadence memory
         │                         │
         └─────────────────────────┴──► ĐA-06 card v2

ĐA-01 estimator ──► ĐA-03 S2 personalization

ĐA-02 B1 độc lập; B2 ──► D-POL-05 policy truth

Architecture B projections là integration boundary cho cả ĐA-01..06.
```

Thứ tự implementation nghiên cứu đề xuất:

1. R5 restore/finish và khóa baseline;
2. version-aware registry + SourceEnvelope;
3. ĐA-01 và ĐA-02 B1 ở cycle riêng;
4. ĐA-03 sau ĐA-01;
5. ĐA-05 → ĐA-04 → ĐA-06;
6. parity integration và 30-seed/visual review.

