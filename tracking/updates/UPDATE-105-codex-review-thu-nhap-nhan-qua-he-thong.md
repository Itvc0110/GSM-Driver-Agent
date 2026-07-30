# UPDATE-105 — Codex review: bằng chứng thu nhập, nhân quả từng advice và phản ứng toàn hệ thống

- **Ngày:** 2026-07-30
- **Người thực hiện:** Codex, theo yêu cầu của Cường
- **Loại:** `research / review-evidence / docs-only`
- **TODO / User story liên quan:** UPDATE-087, UPDATE-088, UPDATE-092, UPDATE-098, D-M3-01, D-M3-10, L1-04, E10
- **Snapshot được review:** `origin/main = 0dde7010608b78af0f744e6fb9fb217d6a56c3e1`
- **Trạng thái:** `REVIEW-EVIDENCE / WAITING-VERDICT`

## 1. Mục tiêu và phạm vi

Tài liệu này trả lời ba câu hỏi bằng bằng chứng đang có trong repository:

1. SIM hiện đo được thay đổi tiền nào khi bật Advisor?
2. Các thay đổi gần đây đã đo được **nhân quả của từng advice** chưa?
3. SIM đã mô hình hóa **phản ứng của nhiều tài xế và rủi ro herding** đến mức nào?

Đây là tài liệu review, không phải chứng nhận production và không thay đổi runtime, solver, simulator,
config hay UI. Mọi con số bên dưới là **MOCK SIM**; không phải dữ liệu vận hành GSM thật.

## 2. Executive verdict

| Câu hỏi | Verdict | Bằng chứng chính | Giới hạn quyết định |
| --- | --- | --- | --- |
| Advisor có làm mean payout tăng trong run xác nhận hiện có? | **CÓ trong MOCK SIM** | positioning-only, 100 seed: `+6.016đ/tài xế/ngày`; tổng đội `+541k/ngày` | adoption 100%, một ngày, demand ngoại sinh, Advisor có lợi thế oracle λ |
| Có thể nói mỗi tài xế đều tăng thu nhập? | **KHÔNG** | P4 `−272đ`, không có ý nghĩa; lợi ích phân bổ không đều | `payout_mean_all` là trung bình đội, không phải individual causal effect |
| Đã đo causal effect của từng advice? | **CHƯA** | adherence denominator đã sửa nhưng không có short counterfactual branch | World A/B phân kỳ; follow/ignore chịu selection bias |
| Đã có anti-herding trong SIM? | **CÓ MỘT PHẦN** | capacity allocation, coverage curve, HHI, equilibrium proxy | capacity danh định; chỉ positioning; chưa nối production dispatch; demand chưa nội sinh đầy đủ |
| Đủ để kết luận Advisor tăng thu nhập cá nhân hoặc tổng đội ngoài thực tế? | **CHƯA** | chưa có real-data/shadow/pilot causal evidence | kết quả MOCK không được nâng thành business claim |

## 3. Ledger con số tiền được phép trích

### 3.1 Kết quả xác nhận positioning-only

Artifact nguồn: `research/audit/2026-07-27-current-state/25-confirm-100seed.json`.
Report nguồn: `tracking/updates/UPDATE-087-xac-nhan-100seed-va-de-xuat-cau-hinh.md:6-23`.

Thiết kế run:

- seed `3000–3099`, 100 seed tươi;
- mỗi seed chạy A, B1 và B3w;
- `coverage: all`;
- B3w chỉ bật `positioning_overrides: wait_only`;
- config mặc định vẫn có `advice.enabled: false` (`configs/pilot_dongda.yaml:311-337`); script
  experiment phải override cờ này để tạo arm B;
- 90 tài xế trong config (`configs/pilot_dongda.yaml:206-225`);
- một ngày mô phỏng.

| Metric B3w − A | Giá trị trong repo | Cách đọc đúng |
| --- | ---: | --- |
| `payout_mean_all` | **+6.016đ/tài xế/ngày, SIG** | trung bình payout trên toàn đội trong MOCK SIM |
| `total_payout_vnd` | **+541k/đội/ngày, SIG** | tổng payout của 90 tài xế trong run |
| `served_rate` | **+1,74 điểm phần trăm, SIG** | service-level proxy trong SIM tăng |
| đơn hết hạn | **−23,4 đơn/ngày, SIG** | ít demand mock bị hết hạn hơn |
| `gini_payout` | **giảm 0,0069, SIG** | phân phối payout đều hơn trong run |
| `payout_mean_P4` | **−272đ, ns** | chưa chứng minh P4 được lợi hoặc bị hại |

Kiểm tra độc lập trên raw artifact trong phiên review:

```text
mean(B3w.payout_mean_all - A.payout_mean_all), 100 seed
= 6.016,1544đ/tài xế/ngày
```

**Impact note:** `+6.016đ` và `+541k` là hai cách tổng hợp của cùng hiệu ứng fleet/day, không phải
bằng chứng một advice cụ thể đã tạo thêm từng ấy tiền và cũng không chứng minh mọi tài xế đều tăng.

### 3.2 Bằng chứng interference và free-rider đã xuất hiện trong SIM

Nguồn: `research/simulation/multi-agent-equilibrium.md:59-80` và artifact
`28-coverage-curve-30seed.json`.

| Coverage | Δ người dùng | Δ người không dùng | Δ toàn đội bình quân | Δ served |
| ---: | ---: | ---: | ---: | ---: |
| 10% | **+5.876đ** | +1.555đ | +2.131đ | +0,60đp |
| 25% | +3.327đ | **+3.986đ** | +3.796đ | +0,98đp |
| 50% | +3.331đ | **+4.032đ** | +3.674đ | +1,13đp |
| 100% | +4.586đ | — | +4.586đ | +1,74đp |

Ở coverage 25–50%, người không dùng hưởng lợi nhiều hơn người dùng. Đây là **bằng chứng interference
trong simulator**: hành động của nhóm được khuyên làm thay đổi cạnh tranh và outcome của nhóm không
được khuyên. Nó đồng thời chứng minh vì sao không thể coi mỗi driver là một đơn vị độc lập rồi so
follow với ignore một cách thô.

### 3.3 Bằng chứng phản ứng sai có thể làm mất tiền

Trong fictitious-play proxy, belief chỉ dùng demand residual (`γ=0`) không hội tụ và cho payout thấp
hơn khoảng **6.000–8.000đ/tài xế** so với belief giữ cả demand đã phục vụ (`γ=1`). Nguồn:
`research/simulation/multi-agent-equilibrium.md:12-40`.

**Impact note:** repo đã chứng minh trong MOCK SIM rằng một feedback rule nghe hợp lý nhưng sai có thể
tự tạo vòng lặp đuổi theo residual demand và làm outcome xấu đi. Đây là bằng chứng cần system-response
model; chưa phải bằng chứng feedback loop production đã được giải quyết.

### 3.4 Ranh giới bắt buộc khi trích tiền

- `payout_mean_all` là **driver payout**, không tự động là `estimated net income`.
- Trong nhiều artifact, `net_mean_all == payout_mean_all` vì cost term đang bằng 0; không được đổi nhãn
  thành “lợi nhuận ròng thực tế”.
- Không được dùng mean fleet để nói “mỗi tài xế” hoặc “advice này” tạo cùng một mức tiền.
- Không được dùng MOCK/SIG để nói hiệu quả GSM thật; `SIG` chỉ có nghĩa CI trong mô hình run loại 0.

## 4. Hạn chế 1 — chưa đo nhân quả từng advice

### Claim

Các commit D-M3-01/D-M3-10 đã sửa cách đếm follow/ignore và thêm validity metadata, nhưng:

```text
đếm adherence đúng hơn
≠
đo causal effect của từng advice
```

### Evidence đã có

1. `src/gsm_core/lifecycle/projections.py:85-140` tạo `decision_adherence` và `event_adherence` từ
   lifecycle events.
2. `src/gsm_sim/sim_metrics.py:336-372` tổng hợp adherence theo channel và channel × archetype.
3. `src/gsm_sim/parallel.py:300-325` chạy World A không Advisor và World B có Advisor theo cùng seed,
   rồi đo delta fleet/day.
4. UPDATE-102 chứng minh mẫu số `shift_extend` trước đây sai: 1,000 được sửa về 0,475, gần coin truth
   0,473 trên ba seed.

Các cải thiện này làm **exposure/adherence measurement đáng tin hơn**. Chúng không tạo counterfactual
cho từng decision.

### Evidence còn thiếu

- Không có snapshot/fork ngắn ngay trước một `decision_id` để chạy cùng state với hai nhánh
  `follow` và `ignore`.
- World A và B chỉ đồng nhất ban đầu. Sau action đầu tiên, vị trí, pin, mệt, order offer, thời điểm
  nghỉ/sạc và RNG-consumption có thể phân kỳ.
- Không có outcome window/expiry/tolerance chuẩn hóa cho từng loại advice.
- Follow/ignore không ngẫu nhiên: xác suất adherence khác theo archetype
  (`configs/pilot_dongda.yaml:400-407`, từ 0,30 tới 0,75), nên so hai nhóm thô bị selection bias.
- `payout_mean_all` và `total_payout_vnd` là outcome theo driver/day hoặc fleet/day, không được join
  ngược thành causal effect của một lời khuyên.
- Product và SIM vẫn không join được đầy đủ: product không emit `decided`; taxonomy topic khác nhau;
  `followed` ở UI là self-report còn trong SIM là behavior transition
  (`specs/adherence-measurement.md:43-57`).

### Impact

Hệ thống hiện trả lời được:

> Khi bật một cấu hình Advisor trong một scenario MOCK, outcome trung bình của cả run thay đổi thế nào?

Hệ thống chưa trả lời được:

> Chính decision này, với tài xế này và state này, đã làm payout tăng hoặc giảm bao nhiêu?

### Verdict

**CHƯA ĐẠT.** Paired-world là bằng chứng ITT ở fleet/day cho một cấu hình Advisor. Nó không phải
per-advice causal attribution, CATE theo tài xế hay bằng chứng follow tốt hơn ignore.

## 5. Hạn chế 2 — phản ứng toàn hệ thống đã có mô hình một phần nhưng chưa đủ tin cậy

### Những gì đã có thật trong code/SIM

1. `src/gsm_core/solvers/capacity_alloc.py:27-125` expand slot theo capacity, dùng assignment và trả
   `unassigned`, `staggered`, `herding_avoided`.
2. `tests/test_capacity_alloc.py:41-49` kiểm tra bốn driver muốn một trạm capacity 2 thì không gán
   quá hai người; các test khác kiểm `herding_avoided` và sensitivity capacity.
3. `src/gsm_sim/market_state.py:81-99` cho Advisor một demand belief riêng để chạy fictitious-play.
4. Artifact 27/28 đã đo PoA, coverage curve, HHI và free-rider. Coverage cao trong experiment hiện tại
   không làm served collapse.

Vì vậy nhận xét “SIM chưa có bất kỳ phản ứng hệ thống hoặc capacity guardrail nào” là **không đúng**.

### Vì sao vẫn chưa đủ tin cậy

#### 5.1 Advisor có lợi thế oracle

`src/gsm_sim/demand.py:76-91` tạo `expected_demand_field` từ chính λ cấu hình generator;
`src/gsm_sim/world.py:142-143` gắn field này vào world; `src/gsm_sim/market_state.py:99` trả nó cho
Advisor. Driver behavior lại nhận belief có nhiễu theo archetype.

Do đó kết quả positioning hiện đo một Advisor biết cấu trúc sinh demand tốt hơn driver. Source-of-truth
`specs/real-data/data-contract-counterfactual.md:755-758` xếp claim `+6.016đ` là **LUNG LAY** và yêu
cầu E10 “Advisor cũng nhiễu”.

#### 5.2 Capacity là danh định, chưa phải production capacity

`capacity_alloc.py` có caveat rõ: capacity trạm/zone là `ESTIMATED`, chưa có telemetry thật. Unit test
chứng minh solver không vượt input capacity; nó không chứng minh input capacity đúng hoặc allocation
được thi hành end-to-end bởi production dispatch.

#### 5.3 Equilibrium mới là proxy hẹp

`research/simulation/multi-agent-equilibrium.md:83-92` tự ghi các giới hạn:

- demand ngoại sinh; service tốt không làm demand tương lai thay đổi;
- equilibrium là supply-vs-belief, chưa phải supply-demand đầy đủ;
- fictitious play chỉ năm seed mỗi vòng;
- operator belief là assumption v1;
- chỉ một ngày, chưa có multi-day memory effect;
- chỉ kênh positioning `wait_only`.

#### 5.4 Chưa chứng minh service-level trade-off ngoài scenario đã chạy

Artifact 25 cho served rate tốt hơn trong scenario hiện tại, nhưng chưa có stress matrix chứng minh
customer wait/service-level không đảo dấu khi:

- forecast/advisor cùng nhiễu;
- demand regime thay đổi;
- capacity sai hoặc stale;
- nhiều tài xế sạc/reposition đồng thời qua nhiều ngày;
- production dispatch tiếp tục tối ưu theo objective riêng.

#### 5.5 Chưa nối production

Product boundary hiện không cho Advisor can thiệp dispatch/matching/routing và không ship positioning
ngoài SIM. Anti-herding simulator vì thế chưa phải protection layer của hệ thống GSM thật.

### Verdict

**HOÀN THÀNH MỘT PHẦN TRONG MOCK SIM; CHƯA ĐỦ TIN CẬY CHO PRODUCTION CLAIM.**

SIM đã vượt qua mô hình “một tài xế độc lập”: có capacity, interference, coverage và equilibrium proxy.
Nhưng chưa chứng minh robustness khi tín hiệu cũng nhiễu như ngoài đời, capacity từ telemetry thật,
demand nội sinh hoặc cùng tồn tại với production dispatch.

## 6. Kết luận được phép và không được phép

### Được phép

> Trong MOCK SIM positioning-only, 100 seed và coverage 100%, mean driver payout tăng khoảng
> 6.016đ/tài xế/ngày và tổng payout đội tăng khoảng 541k/ngày. SIM cũng cho thấy interference,
> free-rider và capacity-aware allocation. Tuy nhiên kết quả còn phụ thuộc oracle demand, một ngày
> mô phỏng và các assumption danh định.

### Không được phép

- “Mỗi tài xế đều tăng thu nhập.”
- “Một advice cụ thể làm tài xế tăng 6.016đ.”
- “Follow advice tốt hơn ignore đúng bằng fleet delta.”
- “Herding và equilibrium đã được giải quyết cho production.”
- “Advisor đã chứng minh làm tăng net income GSM thật.”

## 7. Acceptance gates trước khi nâng claim

### Gate A — per-advice causal

- canonical `decision_id` xuyên solver → presentation → intent → behavior → outcome;
- short branch từ cùng state với `follow`/`ignore` và horizon giới hạn;
- action tolerance, expiry và outcome window theo advice type;
- logging đủ state trước/sau và divergence;
- estimator xử lý archetype selection và fleet interference;
- không dùng World A dài hạn làm counterfactual cho advice cũ nhiều giờ.

### Gate B — system response

- E10 Advisor-noisy chạy trước mọi external income claim;
- sweep coverage × forecast noise × demand regime × capacity error;
- demand/service feedback hoặc giới hạn rõ khi vẫn ngoại sinh;
- customer wait, served rate, expired orders, payout, fairness và empty-km cùng vào veto;
- multi-day scenario;
- shadow với production dispatch, Advisor không ghi dispatch/state;
- capacity/freshness từ telemetry versioned, có fail-safe khi stale.

## 8. Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/updates/UPDATE-105-codex-review-thu-nhap-nhan-qua-he-thong.md` | tạo | báo cáo review evidence-led này |
| `tracking/PROJECT-GRAPH.md` | sửa | đăng ký route UPDATE-105 |

## 9. Docs đã cập nhật kèm theo

- `SCOPE`, `TODO`, `DEFERRED`, `USER_STORIES`: **không đổi**; tài liệu không thay scope hoặc mở
  implementation mới.
- `PROJECT-GRAPH`: thêm node review và correction/evidence edges.
- Không sửa UPDATE lịch sử; UPDATE-105 chỉ định rõ file nào là evidence và file nào là limitation.

## 10. Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| B3w mean payout +6.016đ/người/ngày | `MOCK / OBSERVED-RUN` | artifact 25 + UPDATE-087; tái tính raw 100 seed | Cao cho artifact, thấp cho production | overclaim income uplift |
| Tổng payout đội +541k/ngày | `MOCK / OBSERVED-RUN` | UPDATE-087:21 | Cao cho artifact | nhầm fleet effect thành individual effect |
| Coverage 25–50% có free-rider | `MOCK / OBSERVED-RUN` | artifact 28 + multi-agent-equilibrium:63-79 | Trung bình | sai thiết kế adoption/incentive |
| Capacity allocator không vượt capacity input | `OBSERVED-CODE / TEST` | capacity_alloc + test_capacity_alloc | Cao cho solver | herding guard hỏng ở unit boundary |
| Capacity phản ánh production | `UNVERIFIED` | caveat solver: capacity danh định | Thấp | lời khuyên dồn cung ngoài thực tế |
| Per-advice causal effect chưa có | `OBSERVED-CODE` | parallel A/B fleet; không có snapshot/fork; UPDATE-098 | Cao | gán nhầm fleet delta cho từng advice |
| Advisor dùng oracle λ | `OBSERVED-CODE` | demand.py, world.py, market_state.py, T-047 §4 | Cao | uplift không sống qua product proxy |

## 11. Kiểm chứng

### Commands và kết quả

| Kiểm tra | Kết quả |
| --- | --- |
| `git pull --ff-only origin main` | `Already up to date` tại `0dde7010` trước khi viết |
| `git ls-remote origin refs/heads/main` | remote `main = 0dde7010` trước cycle docs |
| Tái tính artifact 25 từ 100 seed | `6.016,1544đ/tài xế/ngày` |
| Đối chiếu source oracle | demand λ: `demand.py` → `world.demand_field` → `market_state` |
| Đối chiếu capacity | solver + unit tests có; caveat capacity danh định có |
| Runtime tests | không chạy lại vì docs-only; runtime không đổi |

### Chưa kiểm chứng

- Không chạy E10 Advisor-noisy.
- Không tạo short counterfactual branch.
- Không chạy production/shadow/real-data experiment.
- Không chứng minh causal uplift hoặc net income thật.

## 12. Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** docs-only; không đổi simulator behavior, metric computation, UI hay visual encoding.

## 13. Adversarial self-review / flaws found

1. Điều dễ làm kết quả trông tốt nhưng sai nhất là nâng `payout_mean_all` thành “mọi tài xế” hoặc
   “net income thật”. Tài liệu đã cấm hai phép nâng claim này.
2. Future-information leak chính là oracle λ; được ghi cạnh con số tiền, không giấu ở cuối tài liệu.
3. Bằng chứng yếu nhất là generalization từ positioning một ngày sang production multi-channel.
4. Baseline được dùng là paired World A theo seed; baseline này hợp lệ cho ITT fleet/day nhưng không
   hợp lệ làm counterfactual dài hạn cho từng advice sau khi trajectory phân kỳ.
5. Không phủ nhận code anti-herding hiện có; verdict phân biệt rõ `DONE-CODE in SIM` với
   `UNVERIFIED in production`.
6. Artifact 25 được tạo trước D-M3-10 và không mang adherence verdict; vì thế tiền được giữ nhãn
   MOCK/observed-run, không nâng thành causal claim.

## 14. Expansion checkpoint

1. **Schema:** tương lai cần decision-level state snapshot/reference, action window, outcome window và
   explicit `followed_selfreport`/`followed_behavior`; chưa thay schema trong cycle này.
2. **Bài toán tối ưu:** cần robust allocation với noisy belief và capacity uncertainty; chưa thiết kế
   solver mới trong report.
3. **Tính năng:** research dashboard có thể hiển thị advice → state divergence → personal/fleet outcome;
   chỉ đề xuất, không implement.

## 15. Follow-up / defer

Thứ tự evidence gate đề xuất, không tự triển khai:

1. hoàn thiện validity gate adherence theo arm × channel × archetype;
2. chạy E10 Advisor-noisy;
3. thiết kế short counterfactual branch theo advice type;
4. stress matrix system response;
5. sau đó mới cân nhắc shadow/production evaluation.

## 16. Nhắc PENDING-REVIEW

Tài liệu này không đóng các verdict người dùng đang chờ trong `tracking/PENDING-REVIEW.md`.
V-01..V-14, V-16, V-17 và V-18 vẫn cần review theo board hiện hành.
