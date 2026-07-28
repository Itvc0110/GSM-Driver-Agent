# 02 — Simulation, driver app và Advisor: parity đúng nghĩa

## 1. Product boundary đã chốt

**DECISION — Cường 2026-07-27:** chọn **B — một canonical run/snapshot, hai projection**.

Hai UI có người dùng và mục tiêu hoàn toàn khác nhau:

| Bề mặt | Người dùng | Câu hỏi cần trả lời | Được hiển thị |
|---|---|---|---|
| **Simulation demo** | Dispatcher/researcher/stakeholder đánh giá | Hệ thống vận hành ra sao? Advice có hiệu quả không? Có làm hại fleet/fairness không? | Toàn fleet, demand/supply, dispatch outcomes, A/B/C, sensitivity, system guardrails, actor drill-down. |
| **Driver app demo + Advisor** | Một tài xế | Trạng thái của tôi là gì? Gợi ý nào liên quan đến tôi, dựa trên dữ liệu nào, tôi có muốn làm theo không? | Chỉ projection của tài xế, brief/nudge/recap, mục tiêu cá nhân, lý do và freshness vừa đủ. |

Parity **không** có nghĩa hai màn hình giống nhau. Driver app không phải dashboard dispatcher thu
nhỏ; simulation demo cũng không mô phỏng giao diện điện thoại. Parity có nghĩa là khi chọn cùng
`run_id + actor_id + as_of`, các sự kiện và số tương ứng phải truy về cùng một nguồn canonical.

## 2. Tình trạng hiện tại: ba “thế giới” chưa nối thành một

### Thế giới 1 — engine run theo seed

`/api/v1/sim/run|journey|replay|ab|sweep` gọi engine hiện tại, cache run theo seed rồi serialize
cho khu Mô phỏng. Đây là đường gần nhất với mục tiêu simulation demo, nhưng router còn đổi/bỏ
ngữ nghĩa của engine và R5 đang audit các mismatch.

### Thế giới 2 — snapshot 90 ngày

Driver app web đọc các Parquet `realdata-v1`, mặc định chọn ngày cuối và một `d-*`. Advisor app
hiện dựng L3 input từ snapshot rồi chỉ chạy S1. Snapshot được tạo bởi engine commit cũ hơn HEAD và
không biết run vừa chạy trong khu Mô phỏng.

### Thế giới 3 — cuốc interaction mẫu cũ

`/api/v1/trip/step` + routing proxy tạo ba cuốc mẫu để diễn hoạt interaction. Đây không phải
“driver app demo” theo nghĩa product đích: nó không đi từ canonical actor/run, không ghi ledger và
không cập nhật hồ sơ. Routing proxy còn tính `fare_vnd = distance_km × 24.000`, tách khỏi policy.
Nên cô lập đường này dưới nhãn `/demo/*` hoặc thay bằng projection canonical; tuyệt đối không dùng
để chứng minh parity tiền/data.

## 3. Những mismatch đã xác nhận

| Chủ đề | Simulation/engine | Driver app hiện tại | Hậu quả |
|---|---|---|---|
| Identity | Actor thuộc một seed/run cụ thể | Chỉ dùng raw `driver_id` + date snapshot | Cùng tên ID chưa chắc cùng thế giới. |
| Clock/as-of | Event time liên tục trong run | Nhiều aggregate whole-day/mission toàn snapshot | Có future-information leak và “time travel”. |
| Demand | Tất cả order request, served/unserved | Completed trip group theo request time/pickup H3, top 12 | Demand app bị dispatch/fulfillment bias, không bằng market demand. |
| Driver state | State machine online/idle/en-route/on-trip/rest/charge + SOC | “Đang chạy” nếu cả ngày có trip; SOC hash; location = demand zone nóng | App không phản ánh state của actor. |
| Journey outcome | `completed`, `cancelled_after_accept`, `censored`, chưa nhận | Router ép về boolean; UI gọi mọi `false` là “huỷ sau nhận” | Gán sai outcome, có thể đổ lỗi sai cho tài xế. |
| Distance | Pickup leg và trip distance tách | Field `dist_km` đang mang pickup distance ở journey payload | Client có thể hiểu sai quãng đường. |
| Money | Ledger: trip share + day bonus + mission + newbie + adjustment | App tự cộng commission + mission; route proxy tự tính giá | Tổng payout không thể reconcile; UI tự tính thay vì project ledger. |
| Mission | Progress theo event/time trong sim | `_missions(driver_id)` không lọc as-of/date | Tài xế có thể thấy tiến độ cuối 90 ngày ở một ngày trước đó. |
| Advice | S2/S1/S7/custom bridge trong sim, adherence coin | App chỉ S1 từ snapshot; Flutter hard-code | A/B đang đo behavior khác product ship. |
| Recap | Có S3/F3 data path trong core | App recap chỉ đóng gói lại S1 + payout | Chưa phải recap hành vi sau ca. |

R5 còn ghi nhận các gap serialization/visualization khác; xem
[`05-verification-and-review.md`](05-verification-and-review.md). Không sửa chúng trong cycle docs này.

## 4. Kiến trúc B đích

```text
                 Canonical SourceEnvelope
 dataset_id · engine_commit · run_id · seed · policy_version · clock
                               │
                canonical events + payout ledger
                               │
           ┌───────────────────┴───────────────────┐
           ▼                                       ▼
 Dispatcher/System Projection              Driver Projection(actor_id)
 demand · supply · matching outcomes        state · history · money · goals
 fleet/system/fairness metrics              freshness · eligible policy
           │                                       │
           ▼                                       ▼
   SIMULATION DEMO                         AdviceDecisionService
 run · replay · A/B/C · sensitivity                 │
 system guardrails · actor drill-down                ▼
                                           DRIVER APP DEMO
                                      brief · nudge · recap · feedback
```

### Canonical identity

Không join bằng `driver_id` trần. Tối thiểu cần:

```text
(dataset_id, engine_commit, run_id, seed, local_date, actor_id)
```

Product-live có thể thay `engine_commit/seed` bằng `source_snapshot_id/ingestion_cutoff`, nhưng
nguyên tắc không đổi: mỗi projection phải khai báo **nó đang nhìn vào thế giới nào và đến thời điểm
nào**.

### Canonical SourceEnvelope tối thiểu

| Field | Ý nghĩa |
|---|---|
| `dataset_id`, `data_mode`, `is_mock` | Không trộn synthetic/live và luôn hiển thị nhãn. |
| `run_id`, `seed`, `scenario_id`, `engine_commit` | Reproduce simulation. |
| `actor_id`, `fleet`, `policy_version` | Scope driver và luật áp dụng. |
| `event_time`, `observed_at`, `as_of` | Chặn future leak và phân biệt độ trễ ingestion. |
| `projection_version`, `schema_version` | Rebuild/migrate được. |
| `source_refs`, `quality`, `freshness` | Truy nguồn và safe-degrade. |

## 5. Luật parity cho tiền, giá và số liệu

1. **Routing chỉ trả route/distance/ETA; không tính fare.**
2. Fare/gross do versioned policy/pricing component tạo, không do UI hay LLM.
3. `driver_payout` phải là tổng các entry trong canonical `payout_ledger` đến `as_of`.
4. Bonus/mission/newbie/penalty/adjustment là line item riêng, không gộp mơ hồ vào commission.
5. `estimated_net_income` chỉ xuất hiện khi cost coverage đủ và có definition/version.
6. Simulation demo có thể aggregate toàn fleet; driver app chỉ lọc actor, nhưng tổng actor phải
   reconcile với cùng ledger.
7. Mọi number Advisor nêu phải tham chiếu number/source record; LLM chỉ diễn giải.

## 6. Advice parity

Một advice quyết định nên được tạo từ cùng `AdviceDecisionService`:

```text
DriverProjection(as_of) + PolicyProjection(as_of) + ExternalContext(as_of)
    → candidates/solvers → cadence/policy gate → verified card envelope
```

- Simulation dùng output đó để mô hình hóa **intervention** và outcome giả lập.
- Driver app dùng cùng output đó để **present** cho tài xế và thu intent/feedback.
- Simulation có thể thêm counterfactual labels/A-B metadata, nhưng không đổi nội dung decision.
- App có thể rút gọn trace, nhưng không tự recompute feasibility, fare hay payout.

## 7. Kế hoạch migration nghiên cứu — chưa cấp quyền implement

### B0 — Provenance và versioning gate

- sửa `BLOCKER-ARCH-VERSION`;
- định nghĩa `SourceEnvelope` và identity tuple;
- gắn `as_of`/freshness cho mọi projection;
- cô lập `/demo/trip` khỏi canonical endpoints.

### B1 — Canonical projections

- viết `DemandProjection`, `JourneyProjection`, `PayoutLedgerProjection`,
  `DriverRuntimeProjection`, `DriverDailyAggregateProjection`;
- engine run và snapshot provider đều implement cùng interface;
- UI không đọc bảng/engine trực tiếp ngoài provider.

### B2 — Driver-scoped Advisor

- nối 9 solver theo feature/cadence đã được duyệt;
- card v2 có source/as-of/number provenance;
- app demo chọn một actor của canonical run/snapshot.

### B3 — Evaluation

- simulation demo chạy paired A/B/C bằng cùng decision semantics;
- visual dispatcher hiển thị driver/system/fairness cùng uncertainty;
- actor drill-down link sang đúng driver projection, không clone dữ liệu.

## 8. Acceptance criteria cho quyết định B

1. Chọn seed/run/actor/time trong simulation và mở driver projection: trip count, state, points,
   payout line items và mission progress khớp theo cùng `as_of`.
2. Tổng payout các actor bằng fleet payout trong simulation (cho cùng filter/time), sai số 0 VND.
3. Driver app không nhận field dispatcher-only và không hiển thị system control.
4. Simulation demo không dùng snapshot/date mặc định ngầm khi đang hiển thị run engine.
5. Censored trip không bị gọi là cancelled; pickup distance không bị gọi là trip distance.
6. Thay `policy_version` làm cả simulator và driver projection đổi qua cùng ledger rules.
7. Advice decision ID/card content của simulation arm và app preview khớp khi input projection
   giống nhau; khác biệt presentation được phép, khác biệt số/feasibility không được phép.
8. Mỗi endpoint hiển thị `data_mode/is_mock`, `run_or_snapshot_id`, `as_of` và freshness.

