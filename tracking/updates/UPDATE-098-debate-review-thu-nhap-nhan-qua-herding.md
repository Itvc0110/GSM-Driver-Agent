# UPDATE-098 — SOL/DEBATE REPORT: thu nhập, nhân quả từng advice và phản ứng toàn hệ thống tại `aae326c`

> **Trạng thái:** `REVIEW-EVIDENCE / DOCS-ONLY` — đây là biên bản tranh luận kỹ thuật có bằng chứng,
> **không phải fix**, không thay đổi runtime, config, schema, task status hay T-004.
>
> **SHA được kiểm tra:** `aae326cdad29abc1e433e8fb0ea046f8aa38f086`
> **Khoảng commit:** `c96dd37412a0e8191587e9963dd789cb3c046281^..aae326cdad29abc1e433e8fb0ea046f8aa38f086`
> (11 commit)
> **Ngày kiểm tra:** 2026-07-29
> **Phạm vi:** simulator, evaluator, advisor bridge, solver S2, policy cost, lifecycle, UI A/B và artifact 29/30.

## 0. Cách dùng tài liệu này

Đây là bản **SOL — State of Limitations** viết theo hình thức debate. Mỗi kết luận phải có đủ:

1. **Mệnh đề** đang được tranh luận.
2. **Luận cứ ủng hộ** — phần đã có code hoặc số đo thật trong simulator.
3. **Phản biện** — điều code/số đo chưa chứng minh được.
4. **Bằng chứng tái kiểm tra** — commit, file, symbol/dòng hoặc lệnh chạy.
5. **Impact note** — tác động tới module, channel, metric hoặc claim nào.
6. **Verdict** — `ĐÃ HOÀN THÀNH / MỘT PHẦN / CHƯA CÓ / CÓ NHƯNG SAI-CHƯA ĐỦ TIN CẬY`.

Quy ước bằng chứng:

- `OBSERVED-CODE`: đọc trực tiếp source tại SHA nêu trên.
- `OBSERVED-RUN`: tự chạy lại trên đúng SHA, có exit code và output.
- `COMMITTED-ARTIFACT`: số đã có trong repo nhưng phải kiểm provenance trước khi dùng.
- `LIMIT`: giới hạn bắt buộc phải đi cùng mọi claim.

Không được dùng tài liệu này để tuyên bố uplift GSM thật. Simulator đang dùng dữ liệu/hành vi MOCK-PROXY,
không phải thử nghiệm production hay quan sát tài xế thực.

---

## 1. Executive verdict

| Câu hỏi | Verdict | Bằng chứng chính | Giới hạn bắt buộc |
|---|---|---|---|
| Advisor hiện tại tăng mean payout toàn đội? | **CÓ trong MOCK sim** | `OBSERVED-RUN`: 30 seed, `coverage=all`, positioning-only: `+3.999,98đ/người/ngày`, CI dương | Không phải GSM thật; không chứng minh từng tài xế |
| Tổng payout và served rate tăng? | **CÓ trong run này** | `+359.997,8đ/đội/ngày`; served `+1,38đp`, đều CI dương | Chỉ cấu hình positioning `wait_only`, một ngày, demand ngoại sinh |
| Mỗi tài xế/cohort đều tăng? | **KHÔNG** | Chỉ P1/P7 dương có ý nghĩa; P3/P5 có point estimate âm | `driver_keys` artifact rỗng; không có individual causal estimate |
| Follow một advice cụ thể lời/lỗ bao nhiêu? | **CHƯA CÓ** | Không có join `decision_id → payout/trips/outcome` | Lifecycle ID mới là hạ tầng ghi chép |
| Có short counterfactual branch tại advice? | **CHƯA CÓ** | `world.py` không có snapshot/fork/branch; `REVIEW-092-2` còn TODO HIGH | World A/B phân kỳ sau action đầu tiên |
| State có đổi khi follow positioning? | **CÓ trong engine, quan sát chỉ MỘT PHẦN** | actor sang `ENROUTE`, đổi cell/SOC/empty km; `pending_targets` đổi market state | Không có state-before/state-after gắn `decision_id`; UI làm mất dữ liệu này |
| Đã chống herding? | **ĐÃ CÓ trong simulator** | supply incoming + capacity + Hungarian batch + HHI | Chưa phải production; demand/equilibrium chưa nội sinh đầy đủ |
| B2/B3/C5 đủ an toàn để gọi production-ready? | **KHÔNG** | Có Bellman defect, policy validity defect và bridge chưa nối B3 runtime | Default `shift_plan=false` đang giảm blast radius, không xoá defect |
| UI A/B đo đúng sản phẩm đang ship? | **KHÔNG** | Web bật `CHANNEL_LADDER["all"]`; product adapter chỉ gọi S1 | Demo/A-B hiện đo cấu hình khác product path |

---

## 2. Commit map — commit nào thực sự thay đổi runtime

| Commit | Claim/task | Phân loại sau review | Impact note |
|---|---|---|---|
| `c96dd374` | UPDATE-093 + graph addendum | **Docs-only trong commit này** | Không tạo uplift/runtime mới; B1 code nằm trước range |
| `a329f927` | VISION-ALIGNMENT | **Docs-only** | Chỉ định hướng/đối chiếu |
| `b251d6e3` | Mutation guards cho net metric | **Test-only** | Tăng độ tin cậy B1 metric, không đổi kết quả runtime |
| `370bbecd` | Sửa 7 finding tài liệu | **Docs-only** | Governance/claim correction |
| `d362cf2f` | Final review/gỡ NOT-READY graph | **Docs/governance-only** | Không phải implementation knowledge graph T-004; không đổi advisor/sim |
| `87d616f7` | B2 cash cost vào S2 objective | **Code + test, nhưng có defect F-098-01** | Chỉ tác động khi S2/shift-plan chạy và cost khác 0; default 0 |
| `3d22420c` | B3 policy costs theo track/as-of | **Core API/schema/test, chưa vào canonical sim bridge** | Không được dùng để claim policy đang điều khiển advisor runtime |
| `7c6688c9` | Sweep cost hoàn tất | **Docs-only một dòng** | Artifact 29 đã được thêm ở commit trước; commit này không tự chạy sweep |
| `edfb2e5e` | Vision §0 | **Docs-only** | Không đổi runtime |
| `0b2dd2ba` | B4 rename disutility | **Config/runtime rename một phần** | Repo default bit-identical; config ngoài repo dùng key cũ có thể đổi behavior im lặng |
| `aae326cd` | C5 swap fee tại sự kiện | **Code/test + MOCK artifact** | Default fee 0 và `shift_plan=false`; artifact 30 cho thấy S2-only 2029 âm, không phải uplift |

**Verdict commit range:** uplift positioning đo được ở HEAD không chứng minh 11 commit này đã tạo ra uplift.
Phần lớn commit là docs/tests; B2/B3/B4/C5 chủ yếu mở rộng cách hạch toán/diễn giải objective và còn gap.

---

## 3. Debate D-01 — “Sau thay đổi, tài xế đã tăng thu nhập”

### Luận cứ ủng hộ

`OBSERVED-RUN` mới tại đúng `aae326c`:

- seeds `3100..3129`;
- World A advisor off, World B advisor on;
- `coverage=all`;
- chỉ `CHANNEL_LADDER["positioning"]` = `wait_only`;
- paired seed/CRN;
- 30 seed nên `significant` flag được phép hoạt động;
- command exit code `0`, wall time `210,9s`.

| Metric `B − A` | Delta mean | CI95 | Significant |
|---|---:|---:|---|
| `payout_mean_all` | `+3.999,9757đ` | `[2.130,2220; 5.856,8130]` | `true` |
| `net_mean_all` | `+3.999,9757đ` | `[2.130,2220; 5.856,8130]` | `true` |
| `trips_mean_all` | `+0,1867` | `[0,1308; 0,2481]` | `true` |
| `served_rate` | `+0,0138` = `+1,38đp` | `[0,0096; 0,0184]` | `true` |
| `orders_completed` | `+16,8` | `[11,7667; 22,3333]` | `true` |
| `total_payout_vnd` | `+359.997,8đ` | `[191.719,8917; 527.113,1642]` | `true` |
| `gini_payout` | `−0,0081` | `[−0,0121; −0,0040]` | `true` |
| `supply_cell_hhi` | `−0,0012` | `[−0,0018; −0,0005]` | `true` |

Kết quả theo cohort:

| Cohort | Payout delta | CI95 | Verdict |
|---|---:|---:|---|
| P1 | `+5.633,9567đ` | `[1.619,1496; 9.501,6474]` | dương có ý nghĩa |
| P2 | `+5.236,4653đ` | `[−1.974,2809; 12.160,2389]` | chưa kết luận |
| P3 | `−3.841,6533đ` | `[−21.430,3193; 14.082,2455]` | point âm, chưa kết luận |
| P4 | `+1.806,5477đ` | `[−987,5967; 4.556,6662]` | chưa kết luận |
| P5 | `−4.864,3297đ` | `[−11.567,1993; 1.733,3923]` | point âm, chưa kết luận |
| P6 | `+2.876,0063đ` | `[−1.588,9270; 7.506,0634]` | chưa kết luận |
| P7 | `+17.299,5490đ` | `[9.462,3977; 25.357,6327]` | dương có ý nghĩa |

### Phản biện

1. `net_mean_all == payout_mean_all` vì `configs/pilot_dongda.yaml:273-274` đang đặt swap/cash cost bằng 0.
   Đây không phải net income production đã đủ mọi cost.
2. Chỉ P1/P7 có CI dương; không được nói “mọi tài xế tăng”.
3. `driver_keys` trong artifact 29 là `{}`: không có evidence cấp individual driver.
4. P3/P5 có point estimate âm; cần điều tra heterogeneity trước khi rollout.
5. Demand vẫn ngoại sinh; hành vi adherence là coin theo archetype; toàn bộ run là MOCK simulation.
6. Artifact 29 lưu `others_payout_vnd = +383.377,33đ`, fresh run cho `+353.997,63đ`, dù headline fleet
   metric khớp. Không có generator/actor-selection provenance để giải thích chắc chắn sai khác này.

### Impact note

- **Tác động được chứng minh:** estimator cohort/system trong `src/gsm_sim/parallel.py:111-173,251-267` và
  positioning path trong simulator.
- **Không tác động/chưa chứng minh:** từng driver, GSM production payout, part-time behavior, real dispatch,
  long-run equilibrium, policy-graph runtime.

### Verdict D-01

**MỘT PHẦN:** có uplift mean fleet trong đúng MOCK scenario; chưa có quyền nâng thành individual hoặc business claim.

---

## 4. Debate D-02 — “Khi tài xế chọn advice, không gian trạng thái đã tạo khác biệt”

### Luận cứ ủng hộ — engine có thay đổi thật

Positioning follow tạo chuỗi thay đổi:

1. `src/gsm_sim/world.py:328-335`: tạo `decision_id`; target được ghi vào
   `market.pending_targets` để trừ capacity ngay cho người được xét sau.
2. `world.py:770-772`: ghi `standby_followed` cùng `decision_id`.
3. `world.py:819-832`: actor sang `ActorState.ENROUTE`, đặt `enroute_cell`, tiêu hao SOC/empty distance/time,
   đến nơi thì đổi cell và xoá `enroute_cell`.
4. `src/gsm_sim/market_state.py:37-62,101-123`: state mới được tính thành `supply_incoming`.
5. `src/gsm_core/features/market_state.py:77-103`: `supply_effective` làm giảm `capacity_left`; cell hết trần
   biến mất khỏi `ranked_cells`.

Đây là khác biệt nội sinh thật: một lựa chọn của tài xế làm thay đổi cả state cá nhân và state thị trường cho
các quyết định kế tiếp.

### Phản biện — observation/visualization chưa đủ

- Không có snapshot `state_before/state_after` gắn cùng `decision_id`.
- Không có market-state snapshot đầy đủ theo bucket.
- Outcome sau đó như `relocate`, `dropoff`, `swap_done`, payout mutation không mang `decision_id`.
- `ui/backend/app/routers/sim.py:54-82` nén journey và bỏ decision/follow/target/state; segment trả
  `from=None`, `to=None` ở `:74-75`.
- Dashboard chỉ vẽ advice markers và income curve (`src/gsm_sim/dashboard.py:484-501`); V-17 vẫn chờ visual gate.

### Impact note

- **Engine/sim dynamics:** đã bị tác động thật.
- **Debug/audit trail:** chỉ đủ xem immediate action, chưa đủ nối action → outcome.
- **UI/reviewer:** chưa nhìn được state divergence hay counterfactual state.

### Verdict D-02

**RUNTIME ĐÃ CÓ / OBSERVABILITY MỘT PHẦN / VISUAL CAUSAL CHƯA CÓ.**

---

## 5. Debate D-03 — “Đã đo được nhân quả của từng lượt advice”

### Luận cứ ủng hộ

Lifecycle foundation đã có:

- deterministic `decision_id`: `src/gsm_sim/world.py:166-177`;
- advice events mang ID: `world.py:699-787`;
- state/adherence projections: `src/gsm_core/lifecycle/projections.py:51-137`;
- `run_pair()` dùng paired A/B seed: `src/gsm_sim/parallel.py:187-205`.

### Phản biện quyết định verdict

- `run_pair()` chỉ so kết quả **toàn ngày**, không branch tại decision.
- Không có code join `decision_id → payout/trips/net/outcome_window`.
- Các event hậu quả không mang `decision_id`.
- Không có snapshot/fork/branch trong `world.py`.
- Follow-vs-ignore thô bị selection bias vì `DEFAULT_ADHERENCE` khác theo archetype
  (`src/gsm_sim/advice_bridge.py:92-95`).
- Có interference: `pending_targets` của một người thay đổi advice cho người tiếp theo.
- `tracking/TODO.md:23-24` vẫn để `REVIEW-092-1/2` ở `TODO HIGH`.

### Impact note

Gap này tác động trực tiếp tới mọi câu:

- “advice X giúp tài xế Y bao nhiêu tiền?”;
- “follow tốt hơn ignore bao nhiêu?”;
- “advice nào nên giữ/bỏ ở cấp episode?”;
- attribution cho agent/policy/card cụ thể.

Nó **không phủ định** paired fleet uplift ở D-01, nhưng cấm diễn giải fleet uplift thành causal effect cho từng advice.

### Verdict D-03

**CHƯA CÓ.** Lifecycle ID là điều kiện cần, chưa phải estimator nhân quả.

---

## 6. Debate D-04 — “Đã mô hình hóa phản ứng toàn hệ thống và chống herding”

### Luận cứ ủng hộ — anti-herding code thật trong simulator

| Tầng | Cơ chế | Bằng chứng |
|---|---|---|
| Market view | `capacity_left = slots − supply_effective`; cell hết trần bị loại | `src/gsm_core/features/market_state.py:77-103` |
| Incoming supply | actor đang đi + advice pending đều tính vào cung đích | `src/gsm_sim/market_state.py:37-62,101-123` |
| Batch allocation | Hungarian trên capacity slots; dư candidate thành unassigned/staggered | `src/gsm_core/solvers/capacity_alloc.py:53-125` |
| Same-bucket interference control | planner xét theo lô, target pending được trừ ngay | `src/gsm_sim/world.py:263-345` |
| Guardrail | supply-cell HHI, station HHI, Gini, served/starved metrics | `src/gsm_sim/sim_metrics.py:228-268` + `parallel.py:128-173` |

Fresh 30-seed run còn cho supply-cell HHI giảm có ý nghĩa, trong khi served rate và total payout cùng tăng.

### Phản biện

- Demand trace được sinh trước run và hoàn toàn ngoại sinh: `src/gsm_sim/demand.py:1-8`.
- Không có customer abandonment/elasticity theo wait time (`REVIEW-092-4` deferred).
- Equilibrium/fictitious play là research offline, không nằm trong production solver loop.
- `market_demand_override` là hook, nhưng artifact 27/28 không có committed generator đầy đủ.
- Adherence 0,30–0,75 là MOCK archetype probability, không phải observed adherence.
- Product reposition/anti-herding vẫn deferred ở `tracking/DEFERRED.md:10`.
- Chưa mô hình hóa part-time, trust, multi-day adaptation, dispatch policy response hay N lớn production.

### Impact note

- **Simulator positioning:** đã tránh dạng herding ngây thơ “30 người cùng tới một cell”.
- **Production advisor/dispatch:** chưa có bằng chứng được bảo vệ bởi cơ chế này.
- **External claim:** chỉ được nói “anti-herding implemented in simulator”, không được nói “system equilibrium solved”.

### Verdict D-04

**ANTI-HERDING ĐÃ IMPLEMENT TRONG SIM; SYSTEM EQUILIBRIUM CHỈ MỘT PHẦN/RESEARCH-PROXY.**

---

## 7. Debate D-05 — “B2/B3/C5 đã làm objective robust theo policy”

### Phần đã có

- B2 thêm cash cost/km vào S2 objective; hệ số mặc định 0.
- B3 thêm policy bundle 1.1.0, costs theo track/as-of và ba trạng thái
  `ACTIVE/OFF_BY_POLICY/UNKNOWN`.
- C5 tính swap fee tại event, tránh đếm kép khấu hao pin/km.
- Unit tests bảo vệ default compatibility và một số boundary.

### Phản biện bằng counterexample

#### F-098-01 — P0: Bellman gate loại sai ONLINE có tổng value dương

- **Root cause:** `src/gsm_core/solvers/shift_dp.py:196-212` kiểm `online_net > 0` trước khi cộng
  `V[b+1,...]`. Immediate net âm không đồng nghĩa tổng Bellman value âm nếu ONLINE mở bonus cuối ca.
- **Probe tự chạy:** một bucket, 45 điểm, forecast 3 cuốc, cash `4.327đ/km`, distance 3km.
  Immediate online net = `−18đ`; đạt tier 60 mở bonus `30.000đ`; tổng lý thuyết = `+29.982đ`.
  Solver vẫn trả `schedule=['SWAP']`, `expected_payout=0`.
- **Test gap:** `tests/test_c1_cost_term.py:76-84` đang đóng đinh giả định “net mỗi cuốc âm ⇒ cấm ONLINE”
  nhưng không có case vượt bonus threshold.
- **Impact hiện tại:** tác động solver S2/shift-plan khi cost đủ lớn và tài xế gần mốc thưởng.
  Default `shift_plan=false` giảm blast radius trong config hiện hành; bật lại channel có thể khuyên SWAP/REST/END sai.

#### F-098-02 — P0: resolver dùng policy ngoài thời hạn hiệu lực

- `PolicyBundle.is_valid_at()` tồn tại ở `src/gsm_core/policy.py:65-79`.
- `resolve_cost_params()` ở `:130-190` không gọi method này.
- **Probe tự chạy:** bundle chỉ hiệu lực `2030-01-01..2030-12-31`; tại `2029-04-01`,
  `is_valid_at=False` nhưng resolver trả battery `ACTIVE 9000` và cash `ACTIVE 0`.
- **Impact hiện tại:** core policy-cost opt-in path có thể đưa phí chưa hiệu lực/hết hiệu lực vào solver.
  Canonical sim bridge hiện chưa dùng path này, nhưng production integration sẽ chịu lỗi ngay khi nối.

#### F-098-03 — P0: schema ngày tháng fail-open

- `schemas/l0/policy_bundle.schema.json:200-206` chỉ dùng regex cho `battery_free_until`.
- `src/gsm_core/schema_registry.py:143` dựng `Draft202012Validator` không có `format_checker`.
- **Probe tự chạy:** `battery_free_until="2029-02-31"` trả validation errors `[]`.
- `tracking/TODO.md:28` xác nhận ảnh hưởng rộng hơn: 15 schema có `date-time` nhưng format không được enforce.
- **Impact:** policy/version/as-of, API normalization và các L0/L1/L2i/L3 event có thể nhận timestamp không hợp lệ.

#### F-098-04 — P1: B3 chưa nối canonical runtime

- `src/gsm_sim/policy.py:29-52` không đưa `track/costs` vào core record.
- `src/gsm_sim/advice_bridge.py:346-358` không truyền `policy_costs_as_of`; luôn truyền explicit
  `cash_cost_vnd_per_km` và `swap_fee_vnd` từ config, mặc định 0.
- `src/gsm_core/solvers/shift_dp.py:320-332`: explicit params thắng policy.
- **Impact:** UPDATE-095 chứng minh core API/schema/unit behavior, không chứng minh policy đang điều khiển
  simulator advisor hay production path.

#### F-098-05 — P1: taxonomy và provenance chưa an toàn

- `schemas/l0/policy_bundle.schema.json:24-32` dùng `track = core_owned/platform/rto/green_bike_unspecified`.
- `costs.cash_cost_vnd_per_km_by_track` ở `:222-232` lại chứa `charge`; test còn dựng `track="charge"` dù
  canonical schema không chấp nhận. Policy/employment track đang bị trộn với energy/fleet type.
- `PolicyBundle.from_record()` ở `src/gsm_core/policy.py:43-63` bỏ `source/source_url`; resolver tự sinh
  `source=policy_v:<version>` và reason chứa chữ `official` ở `:139,160-163`.
- **Impact:** có thể resolve sai cost cho driver, hoặc trình bày MOCK record như policy official.
  Mọi giá trị tiền/thưởng phải exact-track, city/service, effective date/version và giữ first-party provenance.

### Artifact C5 không chứng minh uplift

`research/audit/2026-07-27-current-state/30-c5-swapfee-30seed.json` đo `s2_only`, không phải product default:

- `today_fee0`: net `−1.626,94đ`, CI chứa 0;
- `scen2029_fee9000`: net `−1.981,44đ`, CI âm có ý nghĩa;
- P6 âm có ý nghĩa.

Artifact này hỗ trợ quyết định **giữ shift-plan tắt**, không hỗ trợ claim “C5 tăng thu nhập”.

### Verdict D-05

**CÓ NỀN CODE NHƯNG SAI/CHƯA ĐỦ TIN CẬY CHO PRODUCTION.**

---

## 8. Debate D-06 — “UI A/B đang hiển thị đúng advisor hiện hành”

### Bằng chứng phản bác

- Config hiện hành `configs/pilot_dongda.yaml:311-337`: advisor default off; khi bật, `coverage=single`,
  `shift_plan/accept_lift/shift_extend/rest_window=false`, positioning `wait_only`.
- Web A/B ở `ui/backend/app/routers/sim.py:43-51` lại dùng `CHANNEL_LADDER["all"]` và không truyền
  `coverage=all`; response label ở `:160-163` còn bỏ positioning khỏi tên channel.
- Streamlit ở `src/gsm_sim/dashboard.py:582-589` ép `shift_plan=True` và thừa hưởng positioning, nhưng UI
  không có control/label rõ cho positioning.
- Label “World B (theo chỉ dẫn)” ở `dashboard.py:570-609` không đúng semantics: B bật advisor,
  còn follow vẫn là coin theo archetype.
- Product adapter chỉ gọi S1 `bonus_feasibility` tại `ui/backend/app/adapters/advisor.py:180-190`;
  `B6-PARITY` vẫn `TODO HIGH` ở `tracking/TODO.md:22`.

### Impact note

- **Không làm sai engine A/B core**, nhưng làm người xem hiểu sai sản phẩm/config/channel đang được đo.
- Screenshot/demo UI không được dùng làm evidence product uplift hoặc system-level safety.

### Verdict D-06

**CÓ UI NHƯNG SAI PARITY/CHƯA ĐỦ TIN CẬY.**

---

## 9. Evidence quality và reproducibility

### Tests có exit code 0 trong review

```powershell
$env:PYTHONPATH='src'
& '.\.venv\Scripts\python.exe' -m pytest `
  tests\test_c1_cost_term.py tests\test_b3_policy_costs.py `
  tests\test_b4_rename_disutility.py tests\test_c5_swap_cost.py `
  tests\test_net_metric.py -q
# 32 passed

& '.\.venv\Scripts\python.exe' -m pytest `
  tests\test_market_state.py tests\test_market_state_sim_producer.py `
  tests\test_capacity_alloc.py tests\test_standby_capacity.py -q
# 28 passed

& '.\.venv\Scripts\python.exe' -m pytest `
  tests\test_parallel_worlds.py -q
# 14 passed
```

Tổng: **74 targeted tests pass với exit code 0**.

### Lệnh tái lập fresh 30-seed positioning run

Chạy từ repo root tại `aae326c`:

```powershell
$env:PYTHONPATH='src'
@'
import json
from gsm_sim.config import Config
from gsm_sim.parallel import run_ladder

cfg = Config.load('configs/pilot_dongda.yaml')
result = run_ladder(
    cfg,
    list(range(3100, 3130)),
    steps=('positioning',),
    coverage='all',
)['positioning']
print(json.dumps(result, ensure_ascii=False, indent=2))
'@ | & '.\.venv\Scripts\python.exe' -
```

Acceptance check: `n_seeds=30`, `n_insufficient=false`; các headline delta/CI phải khớp §3. Nếu không khớp,
không được dùng artifact 29 thay thế cho việc điều tra code/config/actor-selection drift.

### Lệnh tái lập hai defect P0

Bellman gate:

```powershell
$env:PYTHONPATH='src'
& '.\.venv\Scripts\python.exe' -c "import runpy; n=runpy.run_path('tests/test_c1_cost_term.py'); p=n['PolicyBundle'].from_record(n['POLICY_REC']); spi=n['_spi'](buckets=1,points=45,soc=80.0,forecast=[3.0]); r=n['solve'](spi,p,{'cash_cost_vnd_per_km':4327.0,'avg_dist_km':3.0}); print(n['_acts'](r),r['solution']['expected_payout'],3*(12975-4327*3)+30000)"
# ['SWAP'] 0.0 29982
```

Policy validity + invalid calendar date:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
& '.\.venv\Scripts\python.exe' -c "import runpy; from pathlib import Path; from gsm_core.policy import PolicyBundle,resolve_cost_params; from gsm_core.schema_registry import SchemaRegistry; n=runpy.run_path('tests/test_b3_policy_costs.py'); rec=n['_rec'](costs=n['COSTS']); rec['effective_from']='2030-01-01T00:00:00+07:00'; rec['effective_to']='2030-12-31T23:59:59+07:00'; p=PolicyBundle.from_record(rec); cp=resolve_cost_params(p,'2029-04-01'); print(p.is_valid_at('2029-04-01'),cp['battery']['state'],cp['battery']['value']); bad=n['_rec'](costs={**n['COSTS'],'battery_free_until':'2029-02-31'}); print(SchemaRegistry(Path('schemas')).validate('policy_bundle',bad))"
# False ACTIVE 9000.0
# []
```

### Lifecycle test caveat

- Một lifecycle E2E test chạy riêng pass, exit code 0.
- Cả file `tests/test_lifecycle_wiring.py` in đủ 11 dấu `.` và `[100%]` nhưng pytest không thoát trong
  300 giây, exit 124; tắt plugin auto-load vẫn lặp lại.
- Vì không có exit code 0, **không** ghi “lifecycle suite pass”. Đây là harness/teardown issue cần điều tra riêng.

### Artifact provenance gap

Artifact 29/30 chỉ chứa aggregate và `n_seeds`; thiếu:

- seed IDs;
- code SHA;
- command/generator;
- config snapshot/digest;
- coverage/channel manifest;
- raw paired deltas;
- explicit `data_mode=MOCK`.

Không tìm thấy committed script tái tạo chính xác hai artifact. Vì vậy artifact là
`COMMITTED-ARTIFACT`, không tự chứng minh run provenance hay GSM impact.

---

## 10. Gap SIM → production

| Thành phần | Trạng thái | Evidence/impact |
|---|---|---|
| Paired world + CRN + cohort CI | **Đã hoàn thành trong sim** | `parallel.py`; dùng được cho fleet/channel estimate |
| Per-advice outcome/causal branch | **Chưa có** | chặn individual attribution và advice-level learning |
| Anti-herding supply/capacity | **Đã có trong sim** | chưa bảo vệ production dispatch/advisor |
| Demand/system equilibrium | **Một phần/research proxy** | demand ngoại sinh, chưa dynamic/multi-day |
| Structured normalized inputs | **Có fixture/sim, chưa chứng minh live API** | production dtype/freshness/data mode chưa được xác minh |
| Continuous driver state/database | **Sim chủ yếu RAM; production path một phần** | chưa có canonical live state update evidence |
| Part-time/unstable behavior | **Chưa đủ** | simulator vẫn thiên full-time/archetype |
| Dispatch integration | **Chưa có shadow E2E proof** | không được claim không ảnh hưởng dispatch |
| Policy plain text/T-004 graph | **Đang làm riêng, không thuộc commit range** | corpus là reviewer evidence, chưa phải approved runtime fact |
| Policy as-of/track/provenance | **Có nhưng sai/chưa đủ** | F-098-02/03/04/05 |
| Agent orchestration parity | **Chưa có** | product S1 khác simulator multi-solver |
| State/causal visualization | **Chưa có đầy đủ** | reviewer không thấy advice → state → outcome |

---

## 11. Thứ tự xử lý đề xuất — không tự động coi là đã duyệt implementation

### P0 — correctness và financial safety

1. Sửa Bellman recurrence: xét tổng Q-value; thêm regression case immediate net âm nhưng bonus threshold dương.
2. `resolve_cost_params()` fail-closed theo `effective_from/effective_to/as_of` trước khi đọc costs.
3. Bật JSON Schema format validation; test ngày không tồn tại và 15 schema `date-time`.
4. Tách `policy_track` khỏi `vehicle_energy_type/fleet_model`; không dùng `charge` như policy track.
5. Bảo toàn `source/source_url/data_mode/reviewer status`; cấm hard-code chữ `official`.
6. Nối policy costs vào canonical bridge, có compatibility test chống explicit-zero override.
7. Tạo `advice_outcome` keyed bởi `run_id + decision_id`, state snapshots và short branch horizon.
8. Commit reproducible runner + manifest + raw paired deltas cho mọi artifact dùng ra quyết định.

### P1 — simulation reliability và reviewability

1. Quét adoption 10/25/50/75/100% với heterogeneous/part-time behavior.
2. Thêm demand elasticity, customer abandonment và multi-day/trust dynamics.
3. Đo covered/uncovered/free-rider với CI riêng; không chỉ point estimates.
4. UI hiển thị state before/after, market diff, branch outcome và giữ `decision_id`.
5. Sửa A/B UI dùng đúng product config; system claims bắt buộc `coverage=all`.
6. Shadow dispatch interface, safety invariants và rollback criteria.

### P2 — production path

1. Live adapters có schema version, event time, ingested time, source, freshness, data mode và normalization errors.
2. Policy graph chỉ xuất approved exact-track/time-valid facts; không biến corpus evidence thành runtime authority im lặng.
3. Agent chỉ orchestration/explanation; solver/policy gate vẫn deterministic, traced và fail-closed.
4. Shadow → canary → controlled rollout; không dùng MOCK uplift làm business guarantee.

---

## 12. Checklist cho reviewer/agent kế tiếp

Trước khi nói một finding đã được sửa, phải trả lời đủ:

- [ ] Có failing regression tái hiện đúng root cause không?
- [ ] Fix tác động file/symbol/channel nào? Default channel có bật không?
- [ ] Có thay đổi gross payout, driver payout hay estimated net? Không trộn ba khái niệm.
- [ ] Policy có exact track, service/city, as-of, version và first-party provenance không?
- [ ] Artifact có seed list, code SHA, config digest, coverage/channels và raw paired deltas không?
- [ ] Claim là individual, cohort, fleet hay system? Estimator có đúng cấp đó không?
- [ ] Nếu nói causal: có shared decision state, branch/window và xử lý interference không?
- [ ] Nếu nói anti-herding: đó là sim hay production; demand có còn ngoại sinh không?
- [ ] UI chạy cùng config/solver path với product không?
- [ ] Full command có exit code 0 không? Không biến dấu `.` hoặc artifact có sẵn thành test-pass claim.

## 13. Chốt tranh luận

1. **Advisor positioning đang tạo khác biệt thật trong state và cho uplift mean fleet trong MOCK sim.**
2. **Không có bằng chứng từng tài xế đều tăng; chưa đo được causal effect của từng advice.**
3. **Anti-herding đã chuyển từ ý tưởng thành code simulator, nhưng full system equilibrium/production vẫn chưa có.**
4. **B2/B3/C5 chưa production-ready vì defect objective/policy validity và runtime integration gap.**
5. **UI và artifact hiện chưa đủ để một reviewer độc lập tái lập và hiểu đúng product đang được đo.**
6. Mọi fix tiếp theo phải vào plan/test riêng; UPDATE-098 chỉ đóng vai trò evidence/debate ledger.
