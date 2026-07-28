# 03 — Advisor: năng lực hiện tại, ignore UX, mục tiêu tuần và recap

## 1. Advisor hiện thực sự làm được gì?

### Core đã có

| Solver | Có thể khuyên/giải thích | Input chính | Nguồn hiện tại | Đã ra driver app? |
|---|---|---|---|---|
| S1 Bonus Feasibility | Khả năng đạt mốc thưởng/ngày, gap điểm/giờ, eligibility | points, tiers, rate lịch sử, giờ còn, acceptance/completion | L1/L1R + policy mock/versioned | **Có, web**; đây là channel thật duy nhất của app. |
| S2 Shift DP | Online/nghỉ/swap/kết ca theo forecast/SOC/points | demand forecast, SOC, points, policy | Sim/config; đường personalization chưa đủ | Có trong sim bridge, chưa ra app. |
| S3 F3 Patterns | Pattern ca và session summary | trip/activity/payout/day state | L1/L2I/L3 | Core có; app recap chưa nối. |
| S4 Capacity Allocation | Phân bổ candidate có capacity guardrail | candidates, station/zone capacity | Sim/coarse | Không ra app; chỉ phù hợp system/sim guardrail. |
| S5 Weekly Khoán | Feasibility gap **khoán policy** | revenue, days/hours remaining, quota, money basis | Policy + aggregates | Pipeline có đường, app chưa nối. Không phải mục tiêu cá nhân. |
| S6 Mission Select | Chọn tập mission theo budget | missions, reward, effort/hours | Mission tables + assumptions | Pipeline có; chưa app; chưa time-window safe. |
| S7 Idle Reduction | Nhận diện chờ lâu/dead hours, reminder có điều kiện | idle segments, demand by hour, online hours | Tracking/demand proxy | Sim bridge có một kênh rest, app chưa nối. |
| S8 Penalty Explain | Giải thích rule/metric và cách tuân thủ | penalties, rates, thresholds | L1R/policy | F3 pipeline; chưa app. |
| S9 Anomaly Alert | Nêu dấu hiệu bất thường trung tính, đề nghị support | flags/confidence/status | fraud/anomaly input | F3 pipeline; chưa app. |

Core C6 còn có router, context pack, template/LLM composer, verifier và safe-degrade. Tuy nhiên:

- web app chỉ nối S1 qua adapter riêng;
- brief/nudge/recap hiện chủ yếu là ba cách trình bày S1, recap chưa phải F3;
- Flutter dùng advice hard-code;
- F0 free-text là legacy; scope đã đổi sang FAQ có cấu trúc + citation;
- WeatherAPI/traffic/event/community chưa đi vào decision runtime;
- SOC/location runtime, estimated net, personal weekly goal và true F3 recap chưa có;
- `POST /advice/action` chỉ ghi JSONL, không làm Advisor nhớ hoặc đổi cadence.

## 2. Data Advisor được phép dùng

| Loại | Ví dụ | Luật |
|---|---|---|
| Observable internal | offer/accept/decline/trip/payout/mission/policy/app state | Ưu tiên; có `as_of`, source, version, quality. |
| Derived internal | acceptance estimator, demand forecast, idle segments, goal feasibility | Có derivation/model version + uncertainty. |
| External | weather, route ETA, public event | Chỉ qua adapter/cache/freshness; không thay policy hay pricing. Hiện chưa wired. |
| User-declared | time budget, personal payout goal, preference nhắc | User kiểm soát/chỉnh/xóa; không suy thành “cam kết”. |
| Prohibited/unsafe | future realized event, PII không cần thiết, dispatch internals để khuyên từng đơn | Không dùng; không khuyên nhận/từ chối/hủy cuốc cụ thể. |

Advisor là **read-only decision layer** với operational metrics. Việc tài xế chạy thật làm data đổi
qua ingestion/projection; không phải qua Advisor write-back.

## 3. Ignore/non-compliance: hiện có gì và thiếu gì?

### Docs đã có

`specs/advice-timing-state-memory.md` đã định hybrid trigger, cooldown tối thiểu 20 phút/topic,
tối đa 6 proactive advice/shift, ưu tiên safety → SLA/bonus → demand, queue khi đang chạy và memory
cho exposures/follow/ignore/goals. `specs/adherence-measurement.md` nói ignore nhiều thì giảm topic,
không tăng áp lực.

### Runtime còn thiếu

- `dismissed` chỉ append JSONL rồi card biến mất;
- lần GET sau không đọc action log để suppress/dedupe;
- card bị auto-evict có thể không có lifecycle event;
- không có `seen`, `snoozed`, `expired`, `superseded`, `withdrawn`;
- “Làm theo” chỉ là **intent**, nhưng UI/analytics dễ hiểu nhầm là behavior đã xảy ra;
- EpisodeStore, UI JSONL và sim event không join được;
- sim có thể rút coin adherence lại ở nhiều tick, tạo washout.

## 4. State machine đề xuất — PROPOSAL

```text
candidate
  ├─ suppressed(reason)
  ├─ queued(until safe transition)
  └─ presented → seen → expanded
                    ├─ intent_follow
                    ├─ dismissed
                    ├─ snoozed(until)
                    └─ no_response

presented/queued → expired | superseded | withdrawn

behavior outcome (đo riêng): matched | coincident | contrary | unobservable | not_applicable
```

Các phân biệt bắt buộc:

- `intent_follow` không chứng minh đã làm theo;
- `dismissed` không đồng nghĩa chống đối;
- `no_response` là unknown, không phải refusal;
- `coincident` nghĩa tài xế làm đúng hành vi nhưng không thể quy cho advice;
- Advisor không dùng từ “tuân lệnh”, không chấm điểm ngoan/không ngoan và không trừng phạt.

## 5. Case cụ thể: nhắc nghỉ nhưng tài xế tiếp tục chạy

### Advice nghỉ tối ưu thông thường

1. Khi đủ điều kiện tại một safe decision point, tạo một `decision_id` và card “nghỉ/đổi pin”.
2. Nếu tài xế dismiss hoặc tiếp tục online, suppress **equivalent advice** trong decision window
   hiện tại/đến hết ca; không nhắc lại mỗi tick.
3. Chỉ re-evaluate khi có `material_revision`: sang ca mới, SOC/fatigue proxy vượt band mới,
   policy/safety state đổi, hoặc window cũ hết hạn.
4. Sau nhiều dismiss ở nhiều ca, hỏi đúng một lần, trung tính: “Bạn muốn giảm nhắc nghỉ không?”;
   không nói “Bạn đã bỏ qua 3 lần”.

### Safety alert

Safety là state machine riêng, không escalation từ advice thu nhập:

- khi xe đang di chuyển: không hiện card visual-manual; queue tới safe transition;
- cảnh báo mới chỉ phát lại nếu risk state thay đổi materially hoặc policy bắt buộc;
- không dùng bonus/thu nhập để ép tài xế bỏ qua mệt mỏi;
- hard safety veto không thể bị “mua” bằng projected payout.

Nền nghiên cứu: Android Automotive khuyến nghị giảm distraction và giản lược interaction trong xe;
NHTSA có guideline riêng cho visual-manual distraction; JITAI coi “provide nothing” là một
intervention option hợp lệ khi người dùng không receptive hoặc việc nhắc là unsafe.

Nguồn: [Android Automotive notifications](https://developer.android.com/training/cars/platforms/automotive-os/notifications),
[NHTSA visual-manual guidelines](https://www.nhtsa.gov/document/visual-manual-nhtsa-driver-distraction-guidelines-vehicle-electronic-devices),
[JITAI design principles](https://pmc.ncbi.nlm.nih.gov/articles/PMC5364076/).

## 6. Mục tiêu tuần: phải tách ba khái niệm

| Khái niệm | Chủ sở hữu | Money basis | Có tác động policy/dispatch? |
|---|---|---|---|
| **Personal weekly goal** | Tài xế tự đặt/chỉnh/bỏ | Mặc định `driver_payout`; net chỉ khi đủ cost | Không; là planning/tracking tool. |
| **Policy weekly quota (khoán)** | Policy bundle có effective/version | `gross_revenue` hoặc basis ghi rõ | Có thể ảnh hưởng payout theo policy, nhưng Advisor không tự đặt. |
| **Mission/reward** | Mission contract | Count/value/reward theo rule | Tách riêng; không gọi là “mục tiêu của bạn”. |

S5 hiện xử lý khái niệm thứ hai; không được tái sử dụng nó như personal goal store.

## 7. Flow mục tiêu tuần đề xuất — PROPOSAL

### Thiết lập

1. Tài xế chọn quỹ thời gian tuần và `driver_payout` mong muốn; có thể skip.
2. Analytics đưa ba mức **Nhẹ / Vừa sức / Thử thách** từ lịch sử cá nhân + time budget, kèm số
   giờ dự kiến và range; user vẫn nhập tự do.
3. Advisor phân loại `comfortable | stretch | infeasible | unknown`, nêu 2–3 căn cứ có source.
4. Tài xế xác nhận; goal có version/effective week và chỉnh được giữa tuần.
5. Thay goal không đổi dispatch, acceptance, tier hay pay.

### Theo dõi

- progress tự cập nhật từ payout ledger;
- so với quỹ giờ còn lại và range lịch sử, không hứa “chắc chắn đạt”;
- nếu chậm nhịp, đưa một lựa chọn nhỏ; nếu data stale/thiếu thì nói chưa đủ chắc;
- không gửi countdown gây áp lực, không biến missed goal thành failure.

DoorDash mô tả tracker mục tiêu tuần cá nhân, điều chỉnh được, dựa lịch sử/giờ và nhấn mạnh không
gây áp lực; Uber công khai việc theo dõi daily/weekly earnings goals. Đây là pattern tham khảo, không
phải bằng chứng rằng cùng thiết kế sẽ tạo uplift cho GSM.

Nguồn: [DoorDash earnings goal tracker](https://dasher.doordash.com/en-us/blog/earnings-goal-tracker),
[DoorDash Help Center](https://help.doordash.com/en-ca/dashers/article/dx-earnings-goal-tracker),
[Uber Driver app](https://www.uber.com/au/en/drive/driver-app/).

## 8. Shift recap và weekly recap “fancy” nhưng không coercive

### Shift recap

```text
┌──────────────────────────────────┐
│ Hôm nay · 8h42 online             │
│ 423.000đ payout  · goal +23.000đ │
│ gross 564.000đ · net chưa đủ data│
├──────────────────────────────────┤
│ 14 cuốc  · 2h06 chờ · 36' nghỉ   │
│ payout breakdown [expand]         │
├──────────────────────────────────┤
│ Một pattern có bằng chứng         │
│ “13–14h chờ lâu hơn median 7 ngày”│
│ Thử ngày mai: [một experiment nhỏ]│
└──────────────────────────────────┘
```

### Weekly recap

- personal goal result, policy quota và missions ở ba section khác nhau;
- một pattern mạnh nhất + uncertainty/sample size;
- so sánh với chính tài xế trong lịch sử, không leaderboard;
- “Giữ / điều chỉnh goal tuần sau”, không auto-increase;
- celebrate progress bằng visual nhẹ, không streak/shaming/pressure.

### Fancy có nghĩa gì?

- hierarchy rõ, hero number đúng money basis, progressive disclosure;
- micro-animation ngắn và tôn trọng `prefers-reduced-motion`;
- chart có label/text alternative, không dùng màu là tín hiệu duy nhất;
- target cảm ứng tối thiểu WCAG 2.2 AA, ưu tiên 44×44 CSS px cho control chính;
- focus visible, keyboard order đúng, contrast kiểm được;
- không bury caveat/fees hoặc khiến “Bỏ qua” khó hơn “Làm theo”.

Nguồn: [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[FTC dark patterns report](https://www.ftc.gov/news-events/news/press-releases/2022/09/ftc-report-shows-rise-sophisticated-dark-patterns-designed-trick-trap-consumers).

## 9. Contract tối thiểu còn thiếu

### PersonalGoal

`goal_id`, `driver_id`, `week_key`, `money_basis`, `target_vnd`, `time_budget_min`,
`created_at`, `effective_at`, `supersedes`, `status`, `source=USER_DECLARED`, `schema_version`.

### GoalAssessment

`assessment_id`, `goal_id`, `as_of`, `class`, `expected_range`, `hours_range`, `evidence_refs`,
`uncertainty`, `data_freshness`, `model_version`, `caveats`.

### Recap

`period`, `as_of`, `money_breakdown`, `goal_result`, `policy_quota_status`, `mission_status`,
`activity_breakdown`, `pattern`, `experiment`, `evidence_refs`, `data_completeness`.

### AdviceLifecycleEvent

`event_id`, `decision_id`, `display_id`, `driver_id`, `event_type`, `occurred_at`, `observed_at`,
`reason_code`, `context_revision`, `source`, `schema_version`.

## 10. Acceptance criteria UX

1. Dismiss rest advice không làm card tương đương quay lại trong cùng decision window/shift.
2. Card không xuất hiện khi `isDriving=true`; queued card chỉ hiện ở safe transition.
3. Intent và behavior outcome nằm ở hai event/field khác nhau.
4. Personal goal không thay policy quota, mission, dispatch, acceptance hoặc tier.
5. Mọi progress tiền reconcile với payout ledger; net thiếu cost hiển thị `unknown/partial`.
6. Recap không dùng future event và luôn ghi `as_of`.
7. Missed goal không tạo penalty, streak loss, shame copy hoặc auto-goal increase.
8. UI qua reduced-motion, contrast, keyboard/focus và touch-target checks.

