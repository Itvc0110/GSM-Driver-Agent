# AdviceCheckpoint expansion audit — internal-data coverage (read-only)

- Ngày phân tích: **2026-08-05**
- Seed: **1000, 1001, 1002, 1003, 1004**
- Run factory: `ui/backend/app/services/demo_session.py:_default_run`
- Provenance: `data_mode=synthetic`, `is_mock=true`; đây không phải số GSM production.
- Phạm vi: audit và dry-run offline; **không sửa runtime/policy/cadence**, không bật `ONLINE`, không gọi API ngoài, không gọi LLM.
- Script tái lập: [`analyze_advice_expansion.py`](analyze_advice_expansion.py)

## 1. Kết luận điều hành

Không nên mở 450 checkpoint `shift_timing / ONLINE` đang `suppressed` để đạt quota. Trong `normalize_solver_decision`, `ONLINE` được đánh dấu `maintenance` (`src/gsm_core/lifecycle/checkpoint.py:195-224`); `evaluate_checkpoint` trả `silent_maintenance` (`:286-287`). Đây là trạng thái duy trì, không phải một lý do mới để làm phiền tài xế.

Baseline 5 seed là **864 record**, tương đương **1,92 record/tài xế/run** và **0,918 READY/tài xế/run**. Cấu trúc hiện tại có giá trị nhưng hẹp: S1 bonus, S2 SWAP và S2 REST. Mục tiêu 5–10 nên được hiểu là **touchpoint có nội dung khác nhau trong một ca đầy đủ**, không phải 5–10 popup.

Một gói Balanced dùng dữ liệu nội bộ hiện có (brief + recap + candidate in-shift, áp dry-run cooldown và safety) cho **median 5, mean khoảng 4,60 touchpoint/tài xế/run**; nếu thêm long-idle proxy thì khoảng **4,68**, nhưng proxy này đang bị ảnh hưởng bởi boundary state của `dropoff` và chưa đủ điều kiện production. Vì vậy chưa có bằng chứng để tuyên bố đạt trung bình 5–10. Có thể đạt mục tiêu sau khi:

1. sửa/kiểm chứng snapshot boundary sau `dropoff` và bổ sung các field trace còn thiếu;
2. biến pre-shift/recap thành surface chính thức, không coi chúng là nudge;
3. thêm producer cho income pace/plan deviation với facts typed và threshold được owner duyệt;
4. chạy lại phân phối tối thiểu 30 seed trước khi thay cadence production.

## 2. Runtime hiện tại và lý do baseline thấp

### Flow đã xác minh

1. S2 `consult` gọi `shift_dp.solve`, rồi `_capture_checkpoint("S2", ...)` (`src/gsm_sim/advice_bridge.py:580-613`). S1 bonus gọi `_capture_checkpoint("S1", ...)` (`:633-904`). S7 và RULE có producer trong code (`:700-780`, `:908-951`) nhưng bị tắt trong demo factory.
2. Web demo tạo bản sao config và chỉ bật trace S1/S2; `shift_plan=true`, `accept_lift=true`, `shift_extend=false`, `rest_window=false`, `positioning_overrides="off"` (`ui/backend/app/services/demo_session.py:49-79`). Trace không ép actor làm theo advice.
3. Observer lưu snapshot/artifact/checkpoint trong `RunResult`; không gọi solver mới trong click Web.
4. Lifecycle policy kiểm tra validity, state, dedup, supersede, expiry, driving, dismissal, budget, cooldown, maintenance và evidence theo thứ tự (`src/gsm_core/lifecycle/checkpoint.py:234-290`).
5. Các `READY` trong simulator chưa phải `offered/displayed`; lease và ACK thuộc product Web session. `accepted`, `dismissed`, `expanded` là intent, không phải execution.

### Baseline 5 seed

| Chỉ số | Giá trị |
|---|---:|
| Driver-run | 450 |
| Checkpoint created | 864 |
| Created / driver-run | 1,920 |
| READY | 413 |
| READY / driver-run | 0,918 |
| SUPPRESSED | 450 |
| EXPIRED | 1 |
| QUEUED | 0 trong trace capture (moving gate được kiểm lại ở product bridge) |
| SUPERSEDED | 0 |
| Execution links | 815; mặc định `coincident`, không phải causal/adherence |
| Checkpoint không READY | 451 |

Phân phối actor-run của record hiện tại: min **1**, median **2**, p75 **2**, p90 **3**, max **4**. READY: min **0**, median **1**, p75 **1**, p90 **2**, max **3**. READY interval (chỉ khi có ≥2 READY): median **153 phút**, p75 **254**, p90 **363**, max **513**. Nếu tính cả đầu/cuối ca, gap lớn nhất theo actor-run có median **428 phút**, p75 **506**, p90 **540**, max **712**; đây là lý do Web có actor phải đi qua nhiều transition mới gặp card, không tự động chứng minh trace rơi checkpoint.

Trong 450 actor-run, **148 không có READY nào**. Đây là hệ quả của source/callsite và policy hiện tại, không nên chữa bằng cách bỏ suppression toàn bộ.

## 3. Coverage map hiện tại

| Topic / action | Source và trigger | Số lượng | Lifecycle | Giá trị hiện tại |
|---|---|---:|---|---|
| `bonus_eligibility / PROTECT_ELIGIBILITY` | S1 `check_bonus_gate`: chỉ tạo khi còn khả năng cứu điều kiện thưởng; `:633-904` | 198 | 198 READY | Có gap điểm, mốc thưởng, số cuốc/giờ và caveat; driver-facing tốt |
| `energy / SWAP` | S2 schedule có action hiện tại SWAP; `consult` `:597` | 162 | 161 READY, 1 expired | Có SOC/schedule/forecast; current action rõ |
| `rest / REST` | S2 schedule hiện tại REST; S7 producer có nhưng demo tắt | 54 | 54 READY | Có schedule/caveat; cần safety gate khi đang di chuyển |
| `shift_timing / ONLINE` | S2 current action ONLINE | 450 | 450 `suppressed/silent_maintenance` | Không có giá trị nếu chỉ “tiếp tục online”; chỉ đáng tái sử dụng khi có future SWAP/REST hoặc deviation material |
| `shift_boundary / END, EXTEND` | S2/RULE boundary | 0 | Không quan sát trong 5 seed | `END`/`EXTEND` chưa có facts đủ để mở production card |
| `positioning_sim_only / REPOSITION_SIM_ONLY` | S4 `_standby_planner`, `src/gsm_sim/world.py:350-480` | 0 trong Web trace | Simulator-only | Không được đưa thành chỉ dẫn khu vực thật |
| `policy_info`, `safety_reserved`, recap | Schema/route có boundary, producer không có trong run này | 0 | Không tạo | Không tạo giả để đủ quota |

### Vì sao 450 ONLINE không phải 450 lời khuyên bị mất

`ONLINE` là action duy trì và có thể lặp theo polling. Nếu bật thẳng, hệ thống sẽ biến mỗi lần solver gọi thành card trùng nội dung. Những record ONLINE có future `SWAP` là tín hiệu có thể tái sử dụng, nhưng cần một topic/reason material mới như `battery_planning / SWAP_SOON`; không được đổi `silent_maintenance` thành card chỉ bằng một feature flag.

## 4. Snapshot và chất lượng dữ liệu — blocker trước producer mới

Có một boundary cần sửa/kiểm chứng trước khi dựa vào trip completion, idle hoặc plan deviation:

- `_serve_trip` đã cập nhật SOC, payout, points, location, segment và order state trước khi gọi `log("dropoff")` (`src/gsm_sim/world.py:709-729`), **nhưng chưa chuyển `actor.state` từ `ON_TRIP` về `IDLE` trước log**. Trace thực tế seed 1000 cho thấy snapshot `dropoff` vẫn `driver.state=on_trip`; state chỉ trở về idle ở vòng idle sau đó.
- Vì vậy offline safety gate dựa trên transition state đánh dấu nhiều proxy (đặc biệt long-idle/efficiency/income) là unsafe. Đây là `BUG/RISK` boundary, không được dùng để kết luận tài xế đang lái hay idle trong producer mới.
- `CheckpointTraceSink.capture` gọi policy với `is_driving=False`; moving safety được product bridge kiểm lại sau đó. `READY` ở trace không đồng nghĩa có thể offer ở UI.

Tối thiểu cần một focused regression trước khi mở rộng: snapshot sau `dropoff` phải có state canonical sau mutation; comparator phải chứng minh observer không đổi dynamics/RNG.

## 5. Candidate advice từ dữ liệu nội bộ

Nguyên tắc chung: `value threshold → safety → freshness → cooldown → dedup → presentation budget`. Các threshold trong bảng là **dry-run proposal**, không phải production rule.

| Advice type | Mục đích / trigger | Dữ liệu hiện có | Current / future | Facts & message | Presentation / priority | Dry-run estimate | Quyết định sơ bộ |
|---|---|---|---|---|---|---|---|
| `PRE_SHIFT_PLAN` | Một lần trước `go_online`/shift start | actor shift start/end, SOC, điểm hiện tại, first S2 report | Current: bắt đầu ca; Future: nghỉ/SWAP/END theo schedule | “Kế hoạch ca hôm nay”; mốc điểm, cửa sổ pin/nghỉ; không hứa payout | Brief/passive; P0 | 450/450, 1,00 mỗi driver-run; không overlap checkpoint | **Implement now**, nên là brief artifact/surface, không nudge |
| `BONUS_PROGRESS` | S1 gap/tier/feasibility material change; không chỉ “sắp mất” | S1 input/report: gap points, tier, trips/hours, accept/completion, caveat | Current: bảo vệ eligibility; Future: theo dõi mốc tiếp | “Còn X điểm/~Y cuốc; không đảm bảo đạt mốc” | Template nudge hoặc dashboard; P0 | 198 records, 0,44/driver-run; 100% overlap S1 | **Implement now** bằng S1 hiện tại + material dedup |
| `SWAP_SOON` | S2 current ONLINE nhưng future SWAP trong ≤2 bucket; chỉ một signal/plan revision | S2 future plan, SOC snapshot, freshness, caveats | Current: tiếp tục online; Future: chuẩn bị SWAP | Tách rõ “Bây giờ” và “Sắp tới”; không nói “đổi ngay” | Template; P0/P1; stationary only | 381 raw/381 giữ sau dry-run; coverage 84,7%; overlap 381 ONLINE silent | **Implement now** dưới topic/reason mới; không unsuppress ONLINE hàng loạt |
| `SWAP_NOW` | S2 current action SWAP, validity còn hiệu lực | SOC, action/window, S2 report | Current: SWAP; Future: ONLINE/REST | “Đổi pin trong cửa sổ”; numbers typed | Template nudge; P0 | 162, 0,36/driver-run; 100% overlap energy | **Implement now**, giữ lease/cooldown |
| `REST_WINDOW` | S2/S7 REST và window material; không queue text khi moving | rest window, online/rest, shift boundary, caveat | Current: REST; Future: resume ONLINE | “Nghỉ trong cửa sổ…”; không ép nếu safety veto | Template/passive; P0 | 54, 0,12/driver-run; 100% overlap rest | **Implement now**, S7 chỉ mở sau khi có run evidence |
| `INCOME_PACE` | Ở giữa ca, actual payout pace lệch forecast material | snapshot payout/online, first S2 expected payout, shift time | Current: giữ/điều chỉnh nhịp; Future: theo dõi mốc | “Đang thấp/cao hơn kế hoạch”; không hứa thu nhập | Dashboard/nudge; P1 | Proxy 284 raw; 157 giữ sau safety (~0,35/driver-run), 127 safety-blocked; threshold 0,80/1,20 chỉ là proposal | **Needs additional internal data**: pace adapter, freshness và wording owner |
| `PLAN_DEVIATION` | Realized state khác S2 plan sau material bucket/state change | S2 schedule + event/transition state | Current: state thực tế; Future: plan còn phù hợp hay không | “Kế hoạch đã lệch”; không tự đổi action | Passive/nudge; P1 | Proxy 61, 0,14/driver-run; chưa có canonical deviation field | **Needs additional internal data** và snapshot fix |
| `LONG_IDLE` | Idle liên tục vượt ngưỡng; chỉ nói khi đứng yên | Actor có `idle_streak_min` trong runtime nhưng trace snapshot không lưu | Current: đánh giá lại; Future: không tự chọn zone | “Đã chờ lâu”; không tự phát minh khu vực | Passive/nudge; P1 | Event-gap proxy 880 raw; 36 giữ sau safety+120′ cooldown; 844 safety-blocked; không dùng làm production estimate | **Needs additional internal data**: trace field + boundary regression |
| `EMPTY_EFFICIENCY` | Empty/relocate share cao sau đủ số cuốc | segments có `relocate/enroute/on_trip`, payout/trips | Current: xem lại hiệu quả; Future: chỉ positioning nếu S4 có signal | Không đưa zone mới; chỉ số deadhead/occupied có provenance | Dashboard; P1/P2 | Proxy 279 raw; 156 giữ sau safety+180′, 123 safety-blocked | **Needs additional internal data**; không phải popup mặc định |
| `END_SHIFT` | S2/RULE có boundary END thật, policy cho phép | shift end, points, remaining plan, safety/policy | Current: END; Future: none | “Kết ca theo boundary”; không ép kéo dài | Nudge/brief; P0 nếu có evidence | 0 checkpoint trong sample | **Defer** tới khi producer/validity/policy có evidence |
| `EXTEND_SHIFT` | Chỉ khi gap mốc nằm trong cap extension và policy cho phép | RULE `check_shift_extend` có code, nhưng channel demo tắt | Current: EXTEND; Future: boundary mới | Không khuyến khích chạy thêm khi thiếu guard | Nudge; P1 | 0 trong sample | **Do not implement now**; cần owner/policy gate |
| `POST_SHIFT_RECAP` | Sau `end_shift`/censor, một lần | final actor snapshot, payout, trips, online/rest, checkpoint/intent/execution counters | Current: đã kết ca; Future: điểm lưu ý ca sau | Recap chỉ mô tả; không nói advice gây ra uplift | Recap/passive; P0 | 450/450, 1,00 mỗi driver-run | **Implement now** như recap artifact, không popup |
| `POSITIONING_PRODUCTION` | Chỉ khi S4 có production-safe target | S4 hiện sim-only, demo factory tắt | Không được map `REPOSITION_SIM_ONLY` thành dispatch | Không có message production hợp lệ | Internal-only | 0 | **Do not implement now** |

### Response, expiry và external dependency theo candidate

| Type | Expected response | Execution mapping | Expiry / dedup / safety | External dependency |
|---|---|---|---|---|
| `PRE_SHIFT_PLAN` | Xem/expand; không cần accept | Không có execution trực tiếp | Hết hiệu lực khi `go_online` hoặc shift đổi; một lần/ca; chỉ brief | Không |
| `BONUS_PROGRESS` | View/Why; accept chỉ là intent | Có thể đối chiếu trip/points về sau, không causal | Hết khi tier/shift đổi; dedup theo gap/tier/revision; stationary | Không |
| `SWAP_SOON` | View/Why; accept không ép swap | `go_swap/swap_done` là execution quan sát riêng | Hết khi plan/SOC/window đổi hoặc SWAP xảy ra; 120′ proposal; stationary | Không |
| `SWAP_NOW` | View/accept intent | `go_swap/swap_done` | Hết khi window đóng/SWAP done; no card moving | Không |
| `REST_WINDOW` | View/accept intent | `rest` segment nếu xảy ra | Hết khi window đóng/shift end; một lần/window; safety veto | Không |
| `INCOME_PACE` | View/Why; không promise payout | Không có action bắt buộc; chỉ so outcome sau ca | Hết tại snapshot/plan revision mới; 120′ proposal; passive ưu tiên | Không |
| `PLAN_DEVIATION` | View/Why; không tự đổi plan | Quan sát event/segment lệch plan | Hết khi solver revision mới; một lần/revision; stationary | Không |
| `LONG_IDLE` | View/Why; không tự chọn zone | `order_matched/relocate` sau đó chỉ là observation | Hết khi có order/di chuyển/shift end; cooldown + idle streak; stationary | Không |
| `EMPTY_EFFICIENCY` | Dashboard/Why; không điều phối | Segment `relocate/enroute/on_trip` | Hết khi ratio/revision đổi; passive, không popup mặc định | Không |
| `END_SHIFT` / `EXTEND_SHIFT` | View/accept intent; EXTEND không mặc định | `end_shift`/extended event nếu policy cho phép | Hết tại boundary; một lần/ca; policy/safety gate | Không |
| `POST_SHIFT_RECAP` | View/expand; không accept action | Không có execution mới; chỉ báo cáo lịch sử | Immutable sau end/censor; một lần/ca | Không |
| `POSITIONING_PRODUCTION` | Không có response driver-facing ở phase này | S4 allocation chỉ là sim observation | Không re-offer; internal-only | Không; cần product-safe signal trước |

### Safety, expiry, response, execution mapping dùng chung

- Không card text khi `enroute/on_trip`; queued/silent khi đang lái. Brief/recap có thể là passive surface sau khi state an toàn.
- Mỗi candidate phải có validity từ state/solver boundary; không có boundary thì `suppressed: missing_validity`.
- Current action và future plan là hai field; không dùng future SWAP viết thành “đổi ngay”.
- Accept/dismiss/view là intent. Execution chỉ được tạo từ segment/event quan sát sau đó; không suy nhân quả từ `accepted` hoặc thời gian gần nhau.
- Template dùng typed facts/numbers. LLM (nếu sau này cần) chỉ viết `reason/why`, không trigger/action/window/number.

## 6. Offline frequency estimate

Script đã chạy trên cùng 5 seed. `raw_candidates` là số tín hiệu; `dedup_kept_touchpoints` áp cooldown dry-run và safety proxy. `overlap_existing_records` nghĩa là dữ liệu đã có trong checkpoint/ONLINE silent, không phải producer mới.

| Candidate | Raw | Giữ sau gate | Coverage | Mean / driver-run | P50/P75/P90 trên driver có candidate | Safety blocked | Cooldown blocked | Overlap existing |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| `PRE_SHIFT_PLAN` | 450 | 450 | 100,0% | 1,000 | 1/1/1 | 0 | 0 | 0 |
| `BONUS_PROGRESS` | 198 | 198 | 44,0% | 0,440 | 1/1/1 | 0 | 0 | 198 |
| `SWAP_SOON` | 381 | 381 | 84,7% | 0,847 | 1/1/1 | 0 | 0 | 381 |
| `SWAP_NOW` | 162 | 162 | 36,0% | 0,360 | 1/1/1 | 0 | 0 | 162 |
| `REST_WINDOW` | 54 | 54 | 12,0% | 0,120 | 1/1/1 | 0 | 0 | 54 |
| `INCOME_PACE` (proxy) | 284 | 157 | 63,1% raw / 34,9% giữ | 0,349 | 1/1/1 | 127 | 0 | 0 |
| `PLAN_DEVIATION` (proxy) | 61 | 61 | 13,6% | 0,136 | 1/1/1 | 0 | 0 | 0 |
| `LONG_IDLE` (proxy) | 880 | 36 | 89,3% raw / 8,0% giữ | 0,080 | 2/3/4 raw count; 1 sau gate | 844 | 0 | 0 |
| `EMPTY_EFFICIENCY` (proxy) | 279 | 156 | 62,0% raw / 34,7% giữ | 0,347 | 1/1/1 | 123 | 0 | 0 |
| `POST_SHIFT_RECAP` | 450 | 450 | 100,0% | 1,000 | 1/1/1 | 0 | 0 | 0 |

Các số trên là **ước lượng coverage**, không phải lời hứa cadence. Long-idle và efficiency bị giới hạn mạnh bởi state boundary và không được đưa vào headline product metric.

### Gói Balanced tham khảo

Gói gồm `PRE_SHIFT_PLAN + BONUS_PROGRESS + SWAP_SOON + SWAP_NOW + REST_WINDOW + INCOME_PACE + PLAN_DEVIATION + EMPTY_EFFICIENCY + POST_SHIFT_RECAP` có:

- **2.069 touchpoint giữ sau dry-run gate / 450 = 4,598 mean**;
- median actor-run **5**, p75 **6**, p90 **6**, max **9**;
- nếu cộng `LONG_IDLE` proxy đã lọc thì mean khoảng **4,678**, nhưng không đủ chất lượng để dùng làm acceptance.

Diễn giải đúng: bộ dữ liệu nội bộ hiện đã đủ để tiến gần 5 touchpoint theo median, nhưng chưa chứng minh **trung bình 5–10 trong một ca đầy đủ**. Không tăng quota để lấp phần thiếu; cần thêm surface/producer có giá trị và đo lại trên ca/horizon phù hợp.

## 7. Cadence Balanced đề xuất (chưa áp production)

### Budget và surface

- `1 pre-shift brief` một lần/ca.
- `3–6 proactive interruptive` tối đa/ca; giữ giới hạn proactive hiện hữu 6 (`evaluate_checkpoint:278`) làm trần an toàn cho nudge.
- `1–2 passive dashboard insights` (income pace/efficiency/plan deviation), không tiêu cùng budget popup nếu owner chấp thuận.
- `1 post-shift recap`.
- `Why` là on-demand, không quota trước; không tính là autonomous recommendation.
- Không quá **1 proactive card/60 phút/topic group**; safety/energy critical chỉ bypass khi actor đứng yên và trusted policy cho phép. Đây là proposal cần experiment, không thay `20 phút/topic` hiện tại trong lượt này.

### Cooldown/material change proposal

| Nhóm | Cooldown đề xuất để dry-run | Chỉ lặp khi |
|---|---:|---|
| Bonus | 60–90 phút | gap/tier/feasibility đổi material |
| SWAP_SOON | 120 phút | future bucket/SOC/urgency đổi material |
| SWAP_NOW | 60 phút | validity/window hoặc action đổi; khi SWAP đã xong thì không lặp |
| REST | Một lần/window | window hoặc safety reason đổi |
| Income pace | 120 phút | ratio/plan state vượt band mới |
| Plan deviation | Một lần/revision | solver plan mới hoặc deviation đã được xử lý |
| Long idle | 120 phút | idle streak mới và đứng yên; không dùng event-gap proxy lâu dài |
| Recap | Một lần/ca | kết thúc/censor mới |

### Primary selection và grouping

1. Safety/energy-now và validity sắp hết.
2. Shift boundary/REST.
3. Bonus eligibility.
4. Income pace/plan deviation.
5. Efficiency/long idle.

Nếu `SWAP_SOON` và `INCOME_PACE` cùng timestamp, giữ một card: current/future code-owned, hai fact IDs trong cùng explanation. Không phát hai popup cạnh nhau. `ONLINE` maintenance không vào primary set.

## 8. MVP 5–7 advice type

| Ưu tiên | Type | Phân loại | Điều kiện mở |
|---|---|---|---|
| P0 | `PRE_SHIFT_PLAN` | **Implement now** | brief artifact từ actor + first S2; không cần đổi solver |
| P0 | `BONUS_PROGRESS` | **Implement now** | tái sử dụng S1; typed gap/tier/trips; template |
| P0 | `SWAP_SOON` + `SWAP_NOW` | **Implement now** | tách reason/topic khỏi ONLINE maintenance; current/future rõ |
| P0 | `REST_WINDOW` | **Implement now** | reuse S2 REST; mở S7 sau run evidence; moving gate bắt buộc |
| P1 | `POST_SHIFT_RECAP` | **Implement now** | final snapshot/event; recap không causal claim |
| P1 | `INCOME_PACE` | **Needs additional internal data** | pace adapter, as-of/freshness, threshold và wording owner |
| P1 | `PLAN_DEVIATION` hoặc `LONG_IDLE` | **Needs additional internal data** | post-dropoff snapshot fix; idle_streak/plan revision fields; 30-seed dry-run |

Không đưa vào MVP: production positioning, weather/traffic, event/demand external, `EXTEND_SHIFT` khi policy chưa mở, và maintenance ONLINE lặp lại.

## 9. Template catalog

Giữ template-first; không dùng một template chung.

| Template key đề xuất | Bây giờ | Sắp tới | Vì sao/facts |
|---|---|---|---|
| `PRE_SHIFT_PLAN_V1` | Bắt đầu ca theo thời điểm hiện tại | Nghỉ/SWAP/END theo schedule | shift window, SOC, planned actions |
| `BONUS_PROGRESS_V1` | Giữ điều kiện thưởng | Theo dõi mốc còn thiếu | gap points, tier, trips needed, caveat |
| `S2_ONLINE_SWAP_LATER_V2` | Tiếp tục online | Chuẩn bị SWAP trong bucket sau | current/future actions, SOC, validity |
| `S2_SWAP_NOW_V1` | Đổi pin trong window | Quay lại ONLINE theo plan | SOC/action window, freshness |
| `REST_WINDOW_V1` | Nghỉ trong window | Tiếp tục theo plan sau nghỉ | rest window, shift boundary, safety |
| `INCOME_PACE_V1` | Đang thấp/cao hơn nhịp kế hoạch | Theo dõi lại ở checkpoint sau | payout/online, forecast caveat; không promise |
| `PLAN_DEVIATION_V1` | Trạng thái thực tế đã lệch plan | Chờ plan revision tiếp theo | observed vs planned state, no new action |
| `POST_SHIFT_RECAP_V1` | Ca đã kết thúc | Điểm cần xem lại ca sau | payout/trips/online/rest/advice counts; no causal uplift |

Các template lặp lại, số liệu đơn giản không gọi model. LLM chỉ có thể là lazy Why hoặc complex multi-signal explanation sau khi facts/verifier/lease đã sẵn sàng.

## 10. Phase 2 external backlog (chưa tích hợp)

| Nhóm | Mục đích | Nguồn/freshness cần có | Fallback/risk |
|---|---|---|---|
| Weather | Cảnh báo mưa/nóng ảnh hưởng safety/pin | provider có timestamp + reliability | silent khi stale; không mock weather |
| Traffic | ETA/safety route | routing/traffic feed versioned | OSRM geometry không đủ traffic |
| Events | demand spike/road closure | event feed + geofence | không tự suy từ forecast |
| External demand | positioning/demand heatmap | provider + calibration | không map thành `REPOSITION_SIM_ONLY` |
| Live station | availability/queue pin | ecosystem feed | stale thì không khuyên SWAP station cụ thể |

Không gọi API hoặc tạo mock external trong phase hiện tại.

## 11. Test plan trước khi sửa runtime

### Canonical/lifecycle

- `dropoff` snapshot sau mutation: state IDLE, payout/points/SOC/location/order/segment cùng boundary.
- `run_id` join `(run_id, checkpoint_id)`; READY attach exactly once; no duplicate.
- ONLINE maintenance vẫn silent; future SWAP candidate có topic/reason material riêng.
- validity expired/inverted không lease; moving candidate queue/silent; accepted không tạo execution.

### Candidate analyzers

- pure functions cho pre-shift, bonus, SWAP_SOON/NOW, rest, income pace, plan deviation, recap;
- typed facts/numbers/caveats; current/future không trộn;
- material fingerprint/cooldown/dedup; một primary khi cùng timestamp;
- no external provider, no solver call trong Web click, no RNG mutation.

### Distribution/replay

- exact repeat 5 seed cho deterministic invariant;
- tối thiểu 30 seed cho coverage/cadence distribution và confidence interval;
- compare trace on/off về order outcomes, terminal actor state, payout, SOC, trips, segments;
- sensitivity của mọi threshold proposal; không điều chỉnh threshold để đạt 5–10.

### UI/lifecycle sau khi được duyệt

- brief/passive/recap không tiêu proactive popup budget ngoài contract;
- card current/future và silent schema; DOM safe; displayed ACK sau mount;
- Why lazy, không gọi trước click, response cũ không mount sang step mới;
- intent/execution metrics tách riêng.

## 12. Files/data cần bổ sung khi owner duyệt

1. `src/gsm_sim/world.py`: sửa boundary `dropoff` và snapshot field `idle_streak_min`/planned state; phải chứng minh behavior-neutral.
2. `src/gsm_sim/checkpoint_trace.py`/`src/gsm_sim/demo_trace.py`: lưu producer reason/material revision, attachment reason và as-of state cho candidate mới.
3. `src/gsm_sim/advice_bridge.py`: producer S1 progress revision, S2 `SWAP_SOON`, và adapter pure cho income pace/plan deviation; không bật ONLINE maintenance.
4. `src/gsm_core/lifecycle/checkpoint.py`: taxonomy/surface mới chỉ sau owner chốt, giữ closed contract và validity/dedup.
5. `ui/backend/app/services/advice_checkpoint.py` và `demo_session.py`: brief/recap/passive projection, không dual-write legacy.
6. `src/gsm_core/advisor/checkpoint_templates.py`: registry versioned cho các template trên.
7. `tests/`: unit policy, trace neutrality, multi-seed distribution, Web contract/lifecycle.

## 13. Open decisions cần owner chốt

1. **Counting:** pre-shift brief, passive insight, Why và recap có tính vào 5–10 touchpoint không? Chúng không nên được biến thành popup để đạt số.
2. **Cadence:** có chấp thuận trần 4–6 proactive/ca và 1 card/60 phút trong một experiment riêng, hay giữ nguyên V-21 hiện tại?
3. **Income pace:** định nghĩa forecast baseline, band material và wording “thấp/cao hơn kế hoạch” trên dữ liệu MOCK.
4. **Trace blocker:** sửa `dropoff` boundary trước hay tạm defer mọi long-idle/plan-deviation producer?
5. **S7/END/EXTEND:** khi nào mở channel; policy/safety guard nào là authority cho `EXTEND`?
6. **S4:** giữ simulator-only hay mở một producer production-safe có canonical target; không tự dùng `REPOSITION_SIM_ONLY` trên UI.
7. **Adherence/causality:** tiếp tục báo riêng intent, execution và outcome; không dùng accepted/displayed làm evidence uplift (Q-13 vẫn mở).

## 14. Evidence và giới hạn

Reproduction:

```text
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-advice-expansion/analyze_advice_expansion.py \
  --seeds 1000 1001 1002 1003 1004
```

Artifacts:

- [`advice-expansion-summary.json`](advice-expansion-summary.json)
- [`candidate-frequency.csv`](candidate-frequency.csv)
- [`candidate-by-actor.csv`](candidate-by-actor.csv)
- baseline checkpoint inventory: [`checkpoint-audit.md`](../2026-08-05-checkpoint-inventory/checkpoint-audit.md)

Verification đã chạy:

- analysis command: exit 0, 5 seed, 450 driver-run, 864 checkpoint, 413 READY;
- `PYTHONPATH=src:ui/backend .venv/bin/python -m py_compile .../analyze_advice_expansion.py`: pass;
- `git diff --check`: pass;
- không chạy full simulator/solver/backend suite theo scope audit;
- không mở browser/visual gate; đây là docs/data audit (`NOT_APPLICABLE` cho visual).

Giới hạn: mọi số là synthetic/mock; 5 seed chỉ là exploratory. Các proxy income/idle/efficiency/plan deviation không phải producer đã được chấp thuận, và snapshot `dropoff` boundary làm chúng chưa đủ để tuyên bố driver-facing readiness.

## Verdict

**Thiết kế mở rộng được đề xuất, nhưng chưa triển khai cadence production.** Bắt đầu bằng pre-shift brief, S1 bonus, S2 SWAP_SOON/NOW, S2 REST và post-shift recap; sau đó sửa trace boundary và bổ sung income/plan facts. Giữ `ONLINE` maintenance silent, giữ S4 simulator-only, không thêm weather/traffic và không bật LLM. Chỉ sau focused canonical fixes + 30-seed dry-run mới chốt có đạt mục tiêu 5–10 touchpoint hay không.
