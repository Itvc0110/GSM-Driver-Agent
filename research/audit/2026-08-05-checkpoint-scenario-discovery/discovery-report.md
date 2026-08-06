# Discovery — làm giàu tình huống AdviceCheckpoint (read-only)

> **ĐÍNH KÈM 2026-08-05 (cùng ngày):** các lỗi nền móng nhóm G4/§5-nhóm-4 của báo cáo này
> (validity 1′ giả, action_window=None, numbers/caveats bị vứt, dedup nuốt revision,
> moving-at-attach mất card, queued không dấu vết) **đã được sửa trong UPDATE-147**.
> Số funnel BEFORE trong báo cáo này giữ nguyên làm baseline; số AFTER:
> `funnel-seed1000-AFTER-U138.json` (card 40→92, actor có card 37→59, expired 34→1).
> **Phase II (§10–§23)** là discovery hiện hành sau UPDATE-147: kiểm kê rộng 35 nhóm signal,
> 33 capability, corpus MOCK 90 ngày và ba storyline liên tục. Các section §0–§9 được giữ nguyên
> làm bằng chứng lịch sử, không dùng số BEFORE để mô tả current worktree.

- Ngày phân tích: **2026-08-05** · branch `feat/advice-checkpoint-agent-template-why` (HEAD `276df6d` + diff test chưa commit, không chạm đường đo)
- Loại: **discovery/brainstorm dựa trên code + run thật** — KHÔNG sửa runtime/policy/cadence, KHÔNG bật LLM, KHÔNG tạo checkpoint giả
- Kế thừa trực tiếp: `research/audit/2026-08-05-checkpoint-inventory/` (UPDATE-144) và `research/audit/2026-08-05-advice-expansion/` (UPDATE-145). Báo cáo này KHÔNG lặp lại hai audit đó; nó xác minh lại baseline, bổ sung 3 phép đo mới (bộ 10 seed tươi, phân bố taxonomy-field, presentation funnel qua Web session thật) và làm phần scenario discovery / gap map / prioritization sâu hơn.
- Provenance: mọi số từ `app.services.demo_session._default_run` (synthetic, `is_mock=true`). Nhãn: `FACT` = đo trực tiếp từ run/code; `OBSERVED-CODE` = đọc code có file:line; `INFERENCE` = suy luận từ FACT; `UNVERIFIED` = chưa kiểm.

## 0. Phương pháp

Lần theo đúng chuỗi dữ liệu thật:

```
Driver state → operational event → solver/rule evaluation → recommendation
→ checkpoint normalization → lifecycle policy → presentation → driver interaction
→ execution observation
```

Ba phép đo đã chạy (script + artifact trong thư mục này và scratchpad):

1. **Verify baseline**: chạy lại `analyze_checkpoints.py` seeds 1000–1004 trên working tree → **864/413/450/1 tái lập chính xác** (FACT).
2. **Ổn định nhiều seed**: chạy seeds **2000–2009** (10 seed tươi, disjoint) → cấu trúc giữ nguyên (§2.1).
3. **Presentation funnel thật**: script `measure_presentation_funnel.py` đi qua **đúng đường Web client dùng** (`DemoSessionService.advance` → `_advice` → `present_existing_checkpoint`) cho toàn bộ 90 actor seed 1000, đếm card/silent per step (§2.3). Route factory được stub (fallback thẳng) để không gọi mạng — không ảnh hưởng đường advice.

## 1. Chẩn đoán hiện trạng — vì sao checkpoint "ít"

"Ít" là hợp lực của **5 lớp**, phần lớn là hành vi policy đúng, kèm một cụm lỗi/nghèo-dữ-liệu có địa chỉ cụ thể:

| Lớp | Cơ chế | Mất bao nhiêu | Policy đúng hay lỗi |
|---|---|---|---|
| L1 Config | Demo factory chỉ bật S1+S2 (`accept_lift`, `shift_plan`); S4 `positioning_overrides="off"`, S7/RULE tắt (`demo_session.py:63-79`) | 3/5 producer sim không chạy | **Chủ ý** (ĐA-07 di sản); nhưng đáng chú ý demo bật 2 kênh mà pilot config TẮT — demo không phản ánh config ship |
| L2 Producer + dedup | `capture` return sớm khi `checkpoint_id` đã tồn tại (`checkpoint_trace.py:195-196`); id = sha(driver+fingerprint), fingerprint gần như chỉ còn topic+action vì `material_revision` luôn `"1"` | S2 consult ~mỗi 30′ suốt ca nhưng chỉ đọng ~1 record ONLINE/driver-run | **Nửa chủ ý**: dedup là đúng, nhưng vì solver không emit `material_revision`, mọi revision nội dung (SOC đổi, schedule đổi) bị nén thành 1 record — lần capture thứ 2 **vô hình hoàn toàn** (không event duplicate) |
| L3 Lifecycle policy | `silent_maintenance` cho ONLINE/NO_ACTION (`checkpoint.py:221,286-287`) | 450/864 = 52% record | **Policy đúng** (UPDATE-145 đã lập luận; không mở lại) |
| L4 Attach/replay | Chỉ READY attach; SWAP tạo sát cuối chuỗi event không còn transition để attach | 1/413 (bộ cũ), **10/863 (bộ tươi, ~1,2%)** READY không bao giờ hiển thị được, toàn bộ là `energy/SWAP` | **Lỗi association có thật nhưng đuôi nhỏ** — không phải nguyên nhân chính |
| L5 Product | Product S2 luôn `missing_state` (Q-14 by design); product chỉ có S1 | Toàn bộ S2 phía product | **Chủ ý** (fail-closed, không SOC proxy) |

**Kết luận chẩn đoán (INFERENCE có số đỡ):** phần "ít" đến từ (a) chỉ 2/9 solver có đường chạy trong demo và 4/9 có producer bất kỳ, (b) dedup-theo-fingerprint nén chuỗi consult thành 1 record vì thiếu `material_revision`, (c) 52% record là maintenance đúng luật phải im. **Không có bằng chứng checkpoint bị rơi hàng loạt do lỗi attach** (0 attach trùng, đuôi mất ~1,2% READY). Cái làm demo "nghèo" hơn nữa không phải số lượng mà là **chất lượng facts trên card** (§4, nhóm G4): card thiếu window, thiếu số, thiếu caveat text.

### Giới hạn của dữ liệu hiện tại

- Một ngày synthetic, scenario `dry_weekday` (mưa/sự kiện/nhiệt tắt hết) — mọi kết luận coverage là trần dưới của thế giới có nhiễu thời tiết.
- `dropoff` snapshot còn `on_trip` (`world.py:709-729`, blocker UPDATE-145) — mọi proxy idle/efficiency chưa tin được.
- `freshness_deadline` sim bịa `now + 1′` (`checkpoint_trace.py:63`) ⇒ **validity mọi checkpoint sim đúng 1 phút** — che toàn bộ window thật của solver (§4-G4).
- 0 event presentation trong RunResult (offered/displayed/accepted/dismissed/expanded) — đúng kiến trúc; funnel §2.3 đo tầng này bằng session thật, nhưng **không có tài xế thật** nên accepted/dismissed/expanded thật sự vẫn = không đo được trong lượt này.

## 2. Thống kê runtime

### 2.1 Trace-level (FACT, hai bộ seed)

| Chỉ số | 5 seed 1000–1004 | 10 seed tươi 2000–2009 |
|---|---:|---:|
| Driver-run | 450 | 900 |
| Checkpoint records | 864 (1,92/driver-run) | 1.766 (1,96/driver-run) |
| READY | 413 (0,918/dr) | 863 (0,959/dr) |
| SUPPRESSED (100% `shift_timing/ONLINE`, `silent_maintenance`) | 450 | 900 |
| EXPIRED (validity đảo, họ `window_past`) | 1 | 3 |
| QUEUED / SUPERSEDED | 0 / 0 | 0 / 0 |
| Attach đúng 1 lần / attach trùng | 412 / 0 | — / 0 |
| READY không attach được (toàn `energy/SWAP` sát cuối timeline) | 1 (0,24%) | 10 (1,16%) |
| Execution links (`coincident`, conf 0.6 — KHÔNG phải adherence) | 815 | 1.680 |
| Tổng theo run | 167–176 | 164–186 |
| Actor 0 checkpoint (gộp seed) | 0 | 0 |
| Driver-run 0 READY | 148 (32,9%) | — |

Theo type (share ổn định giữa 2 bộ): S1 `bonus_eligibility` ~22,7% · S2 `energy/SWAP` ~18–19% · S2 `rest` ~6–8% · S2 `shift_timing/ONLINE` ~51–52%. Giờ tạo bimodal 05–07h và 15–17h (theo ca P6/P7). Per driver-run: record min 1 / median 2 / max 4; READY min 0 / median 1 / max 3; READY interval khi có ≥2 READY: median 153′ (p90 363′).

### 2.2 Taxonomy field — đo mới (FACT, cả 2 bộ seed)

| Field | Phân bố thực tế |
|---|---|
| `surface` | **100% `nudge`** — brief/recap là enum chết |
| `trigger_type` | **100% `solver_update`** |
| `urgency_band` | **100% `medium`** ⇒ `_priority_band` không bao giờ có high/critical |
| `reason_code` | **100% `solver_recommendation`** |
| `material_revision` | **100% `"1"`** |
| `action_window` | **100% `None`** (chỉ RULE emit, RULE tắt) |
| `validity_minutes` | **~100% = 1,0** (`valid_until = valid_from + 1′`); ngoại lệ là các record ÂM (−9′, −25′) → expired |
| `capture_driver_state` | **100% `idle`** (sim capture hard-code `is_driving=False`) |
| execution link `relation` | lưu `None` (nhãn "coincident" chỉ có trong docs), conf đồng loạt 0.6 |

Diễn giải: **schema taxonomy hiện mang 0 bit thông tin phân biệt** — mọi field điều phối presentation (surface/urgency/trigger/reason) chỉ có 1 giá trị. Hệ quả dây chuyền: priority band phẳng, nhánh LLM `complex_*` của `presentation_strategy` không bao giờ kích hoạt, fingerprint nén mọi revision.

### 2.3 Presentation funnel qua Web session thật (seed 1000, 90 actor)

Đây là phép đo MỚI của lượt này: đi đúng đường `DemoSessionService.advance → _advice → present_existing_checkpoint` (đường Web client dùng) cho **toàn bộ 90 actor**, hết timeline từng actor. (FACT)

| Chỉ số | Giá trị |
|---|---:|
| Tổng step (transition) đã đi | 7.100 (min 24 / median 80,5 / max 176 per actor) |
| Step có card | **40 (0,56%)** |
| Step silent | 7.060 — `no_checkpoint` 7.014 · **`expired` 34** · `unsafe_while_moving` 12 |
| Actor thấy ≥1 card | **37/90 (41%)** |
| Actor 0 card | **53/90 (59%)** — trong đó **20 actor CÓ checkpoint attach nhưng toàn bộ chết `expired` tại presentation** |
| Card/actor | min 0 / median 0 / p90 1 / **max 2** |
| Step tới card đầu (37 actor có card) | median **24** / p75 34 / p90 47 / max 72 — nhưng có ≥8 actor card ngay **step 1** |
| Card theo topic | energy 16 · bonus_eligibility 15 · rest 9 |
| Card theo driver state | idle 100% |
| Transition kind mang card | go_online 16 · relocate 14 · advice_given 5 · advice_bonus_gate 3 · order_declined 1 · swap_failed 1 |

**Ba phát hiện từ funnel (không có trong 2 audit trước):**

1. **Validity 1′ giả nuốt ~40% card đáng lẽ hiển thị được.** Seed 1000 có ~86 lượt checkpoint-attached đi qua presentation: 40 hiện, **34 bị `expired`** (revalidate tại `present_existing_checkpoint` với `valid_until = created+1′`), 12 bị moving. Đây là lỗi plumbing (`checkpoint_trace.py:63`), không phải policy — và là **nguyên nhân lỗi lớn nhất** làm demo nghèo, lớn hơn nhiều đuôi READY-không-attach (~1,2%).
2. **Moving-at-attach = mất vĩnh viễn.** Checkpoint attach vào đúng 1 transition; nếu tại đó tài xế đang `enroute/on_trip` → silent, **không re-offer ở step đứng yên kế tiếp, không event `queued`**. 12 card mất kiểu này ở seed 1000.
3. **Phàn nàn "bấm mãi mới gặp card" có số đỡ:** actor median đi 80 step, 59% không gặp card nào; ai gặp thì median 24 click. Nhưng cũng có ≥8 actor gặp card ngay step 1 — demo không cần fixture, chỉ cần **chọn đúng actor** (hoặc thêm navigation nhảy-tới-checkpoint).

### 2.4 Tách 4 tầng theo yêu cầu đo

```
Displayed   : chỉ đo được qua Web session; RunResult = 0 (đúng kiến trúc)
Accepted    : 0 — không có tài xế thật; intent ≠ execution
Execution   : 815/1680 link `coincident` conf 0.6 — KHÔNG suy nhân quả
Outcome     : KHÔNG đo trong lượt này (Q-13 mở; không claim uplift)
```

## 3. Bản đồ mục đích checkpoint (theo vấn đề tài xế, không theo solver)

| Nhóm vấn đề tài xế | Checkpoint hiện có | Tín hiệu sim có sẵn nhưng chưa dùng | Solver liên quan |
|---|---|---|---|
| **A. Bảo vệ quyền lợi thưởng/mốc** — "tôi sắp mất/kịp mốc nào?" | S1 `PROTECT_ELIGIBILITY` (198) | mốc tân binh (`newbie_week1_bonus`, `tenure_days`), mission (`mission_progress`, catalog config), khoán tuần (S5 input có trong mock), điểm-theo-giờ | S1 ✅ · S5 ❌ · S6 ❌ |
| **B. Năng lượng không gãy ca** — "pin có qua nổi kế hoạch không?" | S2 `SWAP` now (162) | future SWAP trong plan (381/450 dr — `SWAP_SOON`), `order_skipped_soc` (bỏ đơn vì pin), `swap_failed`/queue trạm/tồn pin tủ, `battery_stranded` | S2 ✅ một phần |
| **C. Nhịp ca & thời điểm nghỉ** — "lúc nào nghỉ/kết ca thì ít thiệt nhất?" (chỉ HOÃN, không đổi LƯỢNG — §1.2b) | S2 `REST` (54) | S7 window (kênh tắt; inert 1-ngày vì `planned_rest_hour=None`), END/EXTEND boundary (0 record), `end_shift`/`day_end_settle` mang trips/payout/points/day_bonus | S2 ✅ · S7 ⚠ · RULE ⚠ |
| **D. Vị trí & hiệu quả chờ** — "đứng đây có ổn không?" | 0 trong demo (S4 off; sim-only) | `idle_streak_min` (không vào snapshot), `empty_min/occupied_min`, `sd_ratio`/`capacity_left` của MarketStateView | S4 sim-only ✅ · ràng buộc §8 bẫy #7 |
| **E. Hiểu chuyện gì đang xảy ra** — trước ca/sau ca/khi lệch kế hoạch/khi policy đổi | 0 (surface brief/recap chết; `policy_info` enum chết) | first S2 schedule (brief), settle events (recap), realized-vs-plan (deviation), income pace (payout không vào snapshot), corpus policy versioned, penalty/fraud tables (S8/S9 input) | S3/S8/S9 ❌ producer |

## 4. Gap map 6 lớp

```
(1) Sim BIẾT      ⊃⊃  (2) Solver TÍNH  ⊃  (3) Checkpoint GHI  ⊃  (4) Web HIỂN THỊ
                                                                   ↕ lệch
(5) Tài xế CẦN HIỂU                        (6) Quản lý MUỐN ĐO
```

**G1. Sim biết → solver không nhận** (chọn lọc từ kiểm kê 31 tín hiệu; đầy đủ trong phụ lục kiểm kê):
`idle_streak_min` · queue/tồn pin trạm (S4 nhận station list **luôn rỗng** — `world.py:426`) · `order_skipped_soc`/`orders_soc_skipped` · `order_declined` per-event reason · rating (`trip_rated`) · mission progress · tenure/tân binh · `empty_min/occupied_min/km_driven/cost_vnd` · mưa/nhiệt/tắc đường (`environment.py` đầy đủ nhưng scenario mặc định tắt) · censoring.

**G2. Solver tính → checkpoint không ghi** (`normalize_solver_decision` chỉ đọc 6 key; `checkpoint_record` cắt tiếp):
S1 mất `gap_points/trips_needed/hours_needed/tier_vnd/constraints` · S2 mất delta E[payout], `next_action.reason` · S7 mất `worst_window/idle_share` · report-level mất **`numbers[]`, `caveats[]`, `sensitivity[]`, `infeasible_reason`, `inputs_used[]` freshness** · candidate mất `fingerprint/confidence/solver_status/maintenance` khi persist ⇒ nhánh dedup `duplicate` **không bao giờ khớp record đã persist** (`checkpoint.py:257-259` vs `advice_checkpoint.py:303`).

**G3. Checkpoint ghi → Web không hiển thị:**
- 452/864 không attach (450 đúng luật vì suppressed; đuôi READY-SWAP ~1,2% mất thật);
- `checkpoint_audit` (not_ready/missing_alignment/non_primary_same_time/missing_snapshot — `demo_trace.py:190-251`) **không được UI đọc** ⇒ người xem demo không phân biệt được "im vì policy" với "im vì mất";
- demo moving-gate trả silent `unsafe_while_moving` **không ghi event `queued`** (`advice_checkpoint.py:406-407`) ⇒ mất dấu lifecycle đúng ở chỗ đang cần chứng minh;
- card có `caveat_ids` nhưng **không có text caveat** (template `del facts, caveats` — `checkpoint_templates.py:137`);
- 7/10 template key hiện **không thể đến được** trong demo (ONLINE* bị maintenance-silent, END/EXTEND/S4 tắt, FALLBACK bị not_actionable chặn trước) — chỉ S1_BONUS_PROGRESS ×2, S2_SWAP_NOW, S7_REST_WINDOW sống.

**G4. Web hiển thị → tài xế cần hiểu (facts nghèo — đây là gap đau nhất):**
- facts truyền cho presentation **chỉ có đúng 1 fact** `F1 = reason_code.replace("_"," ")` = `"solver recommendation"` (`advice_checkpoint.py:505-519`);
- `S2_SWAP_NOW` nói "Đổi pin trong cửa sổ được đề xuất" nhưng `action_window=None` trên 100% record — **card hứa một cửa sổ không tồn tại**;
- validity 1′ do trace bịa ⇒ không thể nói "còn hiệu lực đến HH:MM";
- SOC/points/payout có trong snapshot nhưng không vào candidate ⇒ card năng lượng không nói được "pin đang 18%".

**G5/G6. Tài xế cần / quản lý đo:**
- Tài xế: trước ca không có brief, sau ca không có recap, giữa ca không được báo khi kế hoạch đã lệch — 3 khoảnh khắc định hướng lớn nhất đều trống (450/450 driver-run có dữ liệu cho cả 3).
- Quản lý: `accept_rate`/`execution_rate` trong `checkpoint_metrics` luôn `None` ở sim (không có `offered`); hai đường đo sim/product vẫn KHÔNG join được (đính chính adherence 2026-07-30); Q-13 mở ⇒ mọi số adherence phải báo hai tên.

## 5. Scenario discovery

Phân loại theo 8 nhóm đề bài. Mỗi scenario: problem → evidence → trigger → nội dung/facts → lifecycle → tương tác/đo → rủi ro → hỗ trợ hiện tại → gap → scope ước lượng.

### Nhóm 1 — Đã được hỗ trợ (giữ, làm giàu facts thay vì thêm mới)

| # | Scenario | Trạng thái | Gap còn lại |
|---|---|---|---|
| 1.1 | **Bảo vệ điều kiện thưởng** (S1) | 198 record, 100% READY, template 2 biến thể | Mất `gap_points/trips_needed/tier_vnd/constraints` khi normalize ⇒ card thiếu số dù solver đã tính; caveat không render |
| 1.2 | **Đổi pin ngay** (S2 SWAP) | 162, 99% READY | Không window, không SOC trên card; validity 1′; đuôi ~1,2% READY không attach |
| 1.3 | **Nghỉ trong khung** (S2 REST) | 54, 100% READY | Moving gate đúng; nhưng không nói "khung nào" (window None); S7 bổ trợ đang tắt và inert ở run 1 ngày |

### Nhóm 2 — Dữ liệu có sẵn, chưa tạo checkpoint (ưu tiên khai thác)

**2.1 `SWAP_SOON` — sắp phải đổi pin (future plan)** — candidate mạnh nhất, kế thừa UPDATE-145.
- Problem: tài xế đang chạy tốt nhưng 1–2 bucket nữa phải đổi pin; biết sớm thì chọn trạm/chọn cuốc cuối hợp lý.
- Evidence (FACT): 381/450 driver-run có ONLINE với future SWAP ≤2 bucket; full future_plan đã nằm trong record suppressed.
- Trigger: S2 consult khi `schedule[0]=ONLINE ∧ SWAP ∈ schedule[1..2]` ∧ material change (bucket SWAP đổi hoặc lần đầu).
- Driver state hiển thị: idle/vừa dropoff; moving ⇒ queue. Current action: **tiếp tục online** (giữ nguyên); future: chuẩn bị SWAP — hai field tách bạch (I1), cấm viết thành "đổi ngay".
- Facts cần: bucket SWAP dự kiến, SOC hiện tại, lý do (`next_action.reason` — hiện bị normalize cắt).
- Lifecycle: topic/reason mới (vd `battery_planning`), KHÔNG unsuppress ONLINE hàng loạt; dedup theo (bucket SWAP, SOC band); 1 lần/plan revision.
- Đo: view/expand; execution side-channel `go_swap/swap_done` (đã có matcher); outcome uplift = KHÔNG kết luận (Q-13).
- Rủi ro: lặp mỗi consult nếu thiếu material fingerprint; template `S2_ONLINE_NOW_SWAP_LATER` có sẵn nhưng đang chết — tái dùng được.
- Scope: producer nhỏ trong `advice_bridge` + topic mới trong closed contract (cần owner duyệt schema) + giữ maintenance silent. **Trung bình.**

**2.2 `PRE_SHIFT_PLAN` (brief trước ca)** — 450/450 driver-run có first-S2-schedule; surface `brief` đã có trong enum nhưng chết. Đây là vế F1 của SCOPE và hình thái DIRECTIVES (brief–nudge–recap). Không tiêu budget popup (chờ Q-10/136 §13.1). Scope: producer 1 lần/ca + surface routing. **Trung bình.**

**2.3 `POST_SHIFT_RECAP`** — `end_shift`/`day_end_settle` mang trips/payout/points/day_bonus (FACT, event #30/#8); cộng lịch sử checkpoint trong ca (đã có trong store) ⇒ recap "hôm nay hệ thống đã khuyên gì, bạn làm gì" mà KHÔNG claim uplift. Đây là chỗ trả lời "recap chưa phản ánh lịch sử advice". Scope: **trung bình**, thuần projection + template, không solver mới.

**2.4 Bỏ lỡ đơn vì pin (`order_skipped_soc`)** — scenario tự phát hiện từ event #11.
- Problem: tài xế bị dispatcher bỏ qua đơn vì SOC không đủ mà **không hề biết**; cơ hội mất là thật (41 lần/run từng đo ở Q-06).
- Evidence: event `order_skipped_soc{soc_pct, need_km}` + counter `orders_soc_skipped` (không vào snapshot).
- Trigger đề xuất: lần bỏ đơn-vì-pin ĐẦU TIÊN trong ca (hoặc ngưỡng N=2) ∧ đứng yên.
- Nội dung: "Bạn vừa không được chào 1 đơn vì pin thấp. Bây giờ: [giữ theo plan] · Sắp tới: đổi pin ở bucket X" — số từ event, action từ S2 (KHÔNG tự phát minh action; nếu S2 chưa có SWAP trong plan thì chỉ là awareness/passive, không nudge hành động).
- Rủi ro: trùng nội dung với SWAP_SOON/SWAP_NOW ⇒ phải cùng topic group cooldown năng lượng; không được nói "nhận đơn đi" (cấm can thiệp per-order).
- Hỗ trợ hiện tại: 0. Gap: field vào snapshot + producer event-triggered (loại trigger `state_change` — hiện chưa producer nào dùng loại này). Scope: **trung bình**.

**2.5 Mốc tân binh (P4)** — `tenure_days`, `newbie_week1_bonus` (≥50 cuốc/7 ngày), `newbie_guarantee_topup` + config `newbie` — persona P4 là persona sản phẩm lõi và SCOPE F1 nói thẳng use case này. Hiện 0 producer. Dạng S1-mở-rộng (gap-to-milestone), template hoá tốt, số typed từ policy config. Scope: **trung bình** — nhưng chỉ có nghĩa ở run multiday/tenure — demo 1 ngày khó dựng; đánh dấu cần multiday hoặc mock tenure.

**2.6 Mission trong ngày (S6)** — solver S6 + `mission_select_input` + catalog config + event `mission_completed` đều tồn tại; producer 0. Ràng buộc Q-04: mission ≠ mục tiêu cá nhân ≠ khoán. Scope: **trung bình-lớn** (S6 chưa từng chạy trên đường sống; normalize chặn cấu trúc — cần action/validity mapping mới).

### Nhóm 3 — Có checkpoint nhưng policy ẩn (đúng luật, đừng "chữa")

| Scenario | Vì sao ẩn | Kết luận |
|---|---|---|
| ONLINE maintenance ×450 | `silent_maintenance` | **Đúng.** Giá trị nằm ở future_plan bên trong nó (→ 2.1), không phải ở việc hiện card |
| Card khi đang lái | demo `unsafe_while_moving` | Đúng luật; nhưng **thiếu event `queued`** phía demo ⇒ không chứng minh được "hệ thống có biết mà đang hoãn" — sửa observability, không sửa policy |
| 148/450 driver-run 0 READY | S1 không trigger (không recoverable/đã đạt) + cả ca ONLINE | Phần lớn đúng; brief/recap (2.2/2.3) là câu trả lời cho "tài xế không có gì để xem", không phải nới ngưỡng S1 |

### Nhóm 4 — Chỉ thiếu nội dung/facts/template (đòn bẩy rẻ nhất, sửa MỘT lần ăn MỌI card)

| # | Thiếu gì | Nguồn đã có | Sửa ở đâu (khi được duyệt) |
|---|---|---|---|
| 4.1 | `action_window` = None toàn bộ | S2 có bucket; S7 có worst_window; RULE có window | normalize đọc từ schedule/next_action thay vì chỉ `solution.action_window` |
| 4.2 | validity 1′ giả | solver boundary thật (bucket end, shift end, rest window end) | bỏ hardcode `now+1` (`checkpoint_trace.py:63`) — đây cũng là gốc họ expired-đảo |
| 4.3 | Card không số | `numbers[]` của report (traceability=1.0) đang bị normalize vứt | mang `numbers` (đã typed + source) vào candidate/record |
| 4.4 | Caveat không text | `caveats[]` report | card contract thêm caveat text hoặc registry id→text |
| 4.5 | Facts = 1 fact | S1/S2/S7 solution keys (§4-G2) | `_presentation_inputs` lấy từ artifact report như `evaluate_presenters_post_run` đã làm |
| 4.6 | urgency/material_revision/reason mặc định | solver biết (vd S1 gap nhỏ dần = urgency tăng; schedule đổi = revision mới) | solver emit 3 field optional; mở lại priority band + dedup-theo-revision |

**INFERENCE quan trọng:** nhóm 4 chính là điều kiện tiên quyết của mọi nhóm khác — không có 4.2/4.1 thì queue/expire/re-offer vô nghĩa; không có 4.6 thì mọi producer mới sẽ lại bị nén thành 1 record như ONLINE.

### Nhóm 5 — Cần solver/rule/producer mới

`INCOME_PACE` (cần payout vào snapshot + pace adapter; threshold owner) · `PLAN_DEVIATION` (cần plan revision + as-of; sau dropoff-fix) · `LONG_IDLE` (cần `idle_streak_min` vào snapshot + dropoff-fix; **không** làm input positioning — §8 bẫy #7; chỉ là awareness đứng-yên) · trạm pin (queue/tồn tủ — cần S4 nhận station state thật; rủi ro herding cao, để sau) · khoán tuần S5 (multiday, D-POL-01) · policy-delta cho P5 (F0, cần corpus versioned — không phải sim).

### Nhóm 6 — KHÔNG nên thành checkpoint

- Khuyên nhận/từ chối/hủy **một đơn cụ thể** (`order_declined`, `order_matched`) — cấm ranh giới sản phẩm, dù data có đủ.
- `REPOSITION_SIM_ONLY` → card sản phẩm — cấm (S4 sim-only, Q-14).
- Hậu quả của mệt / "chạy thêm đi kẻo phí" — §1.2b, C2 huỷ vĩnh viễn.
- `battery_stranded` lúc đang xảy ra — đang lái, không modality an toàn; thuộc recap + phòng ngừa từ 2.4.
- Sự kiện kỹ thuật: `censored_end_of_run`, `order_censored`, `demand_est*`, `probe_wait_stats`, herding internals của S4.
- Rating từng cuốc — giám sát cảm giác "bị chấm điểm"; nếu có thì chỉ recap tổng, opt-in.

### Nhóm 7 — Chỉ hợp analytics/recap (không popup)

`EMPTY_EFFICIENCY` (deadhead share) · income summary/pace history · adherence history cá nhân · S3 patterns hậu-ca · penalty summary (S8 — chú ý ranh giới dự án giải trình D-006) · rating trend · "advisor đã nói gì hôm nay" (bảng, thuộc recap 2.3).

### Nhóm 8 — Rủi ro spam/an toàn/điều phối lệch/hiểu nhầm (guard bắt buộc kèm mọi đề xuất trên)

| Rủi ro | Kịch bản cụ thể | Guard |
|---|---|---|
| Spam lặp | SWAP_SOON re-fire mỗi consult 30′ | material fingerprint theo (bucket, SOC band, revision) + cooldown nhóm topic năng lượng |
| Herding | Trạm pin "vắng" được khuyên cho nhiều tài xế cùng lúc | chỉ từ S4 capacity-aware; không bao giờ từ template tĩnh; giữ sim-only tới khi có cơ chế chia slot |
| Safety | Card chữ khi đang lái | moving gate hiện có + **thêm event queued ở demo path** để chứng minh được |
| Hiểu nhầm nhân quả | recap "nhờ nghe advice bạn kiếm thêm X" | recap chỉ mô tả; cấm uplift claim (Q-13 mở) |
| Đánh đồng intent/execution | nút "Làm theo" bị đọc thành execution | giữ tách intent (client) / execution (observer side-channel) như hiện tại |
| Demo ≠ vận hành | tăng cadence để demo đẹp | demo navigation là công cụ quan sát (jump-to-checkpoint), KHÔNG đổi policy/cadence |

## 6. Prioritization

Tiêu chí (đề xuất): (a) giá trị tài xế (tiền/rủi ro được bảo vệ), (b) độ tin dữ liệu (typed, từ run, không proxy), (c) giải thích được bằng template + numbers provenance, (d) tần suất/coverage, (e) an toàn (moving/herding/health boundary), (f) chi phí (producer sẵn? normalize chặn?), (g) kiểm thử được (deterministic replay, ≥30 seed), (h) trình bày được cho cấp trên (steps-to-card, câu chuyện rõ).

**Shortlist (không code trong lượt này):**

| Hạng | Việc | Loại | Lý do |
|---|---|---|---|
| 0 | **Nền móng nhóm 4** (validity thật, action_window, numbers/caveats vào record, material_revision, dropoff-fix, queued-event demo) | sửa plumbing | Rẻ, ăn mọi card hiện có lẫn tương lai; không đổi cadence/policy; đo được behavior-neutral |
| 1 | `SWAP_SOON` (2.1) | producer + topic mới | 84,7% coverage, dữ liệu đã nằm trong record, template sẵn, tách bạch Bây giờ/Sắp tới đúng I1 |
| 2 | Brief + Recap (2.2/2.3) | surface mới | 100% coverage, trả lời trực tiếp "tài xế không có gì xem"; không popup; phải chờ Q-10/counting |
| 3 | `order_skipped_soc` awareness (2.4) | producer event-triggered đầu tiên | Giá trị nhận thức cao, số typed, mở loại trigger `state_change` |
| 4 | `INCOME_PACE` / `PLAN_DEVIATION` | cần data nội bộ thêm | Sau khi snapshot có payout/revision; threshold owner duyệt |
| 5 | Tân binh (2.5), Mission (2.6), S5/S8/S9, trạm pin | cần multiday/policy quyết | Giá trị persona rõ nhưng chi phí + rủi ro cao hơn |

## 7. Demo candidates từ trace thật (seed hiện hành, không fixture)

Từ funnel seed 1000 (90 actor, đường Web thật) + inventory UPDATE-144:

| Candidate | Seed | Actor | Bắt đầu | Card đầu tại step | Thao tác | UI chứng minh | Giới hạn kết luận |
|---|---:|---:|---|---:|---:|---|---|
| Đổi pin (energy/SWAP) | 1000 | 77 | `go_online` | 1 | 2–3 click | Card "Chuẩn bị đổi pin" + provenance MOCK; sau đó thấy `go_swap/swap_done` trên timeline (execution side-channel) | coincident ≠ causal; card không có window/SOC (gap G4) |
| Bảo vệ thưởng (S1) | 1000 | 39 | `go_online` | 1 | 2–3 click | Card bonus + typed number nếu có; nút phản hồi intent | accepted = intent trình diễn, không phải tài xế thật |
| Nghỉ trong khung (rest) | 1000 | 70 | `go_online` | 1 | 2–3 click | Card rest + moving gate (bấm tiếp khi enroute → silent đúng luật) | window không hiển thị (None) |
| Actor nhiều card trong ca | 1000 | 40 (funnel: 2 card, card đầu step 1) hoặc 63 (inventory: nhiều topic) | — | 1 | ~5 click | Nhiều hơn một card trên một hành trình | max 2 card/ca ở seed này — mật độ thật, đừng hứa hơn |
| Silent đúng luật khi đang lái | 1000 | bất kỳ trong 12 actor có `unsafe_while_moving` | transition enroute | — | vài click | Response silent có `reason_code` — chứng minh "im có chủ đích" | hiện KHÔNG có event queued để chỉ vào; chỉ có reason trong response |

Giới hạn chung của mọi demo candidate: card đến từ trace thật nhưng **người bấm không phải tài xế** — accepted/dismissed trong demo là thao tác trình diễn; không được đọc thành hành vi. Không dựng được từ trace hiện tại: queued (sim không capture moving), superseded, recap, ONLINE→SWAP card (maintenance silent — đúng luật), actor-không-checkpoint.

## 8. Open questions cho owner

1. **Counting/quota:** brief, passive insight, Why, recap có tính vào mục tiêu "5–10 touchpoint/ca" không? (kế thừa 136 §13.1, thêm: nếu không tính, budget nudge giữ 6 hay hạ?)
2. **Taxonomy mở rộng:** duyệt topic/reason mới cho `SWAP_SOON` (contract đóng — thêm enum là đổi schema version) và 3 field optional `urgency_band/material_revision/reason_code` từ solver?
3. **Nền móng trước producer:** đồng ý thứ tự "nhóm 4 trước, producer mới sau"? (validity/action_window/dropoff là behavior-neutral nhưng đổi nội dung record — cần comparator + upcaster)
4. **Demo navigation:** thêm "Nhảy tới checkpoint kế" / bộ chọn scenario như công cụ quan sát dữ liệu (không đổi cadence)? Điều này giải quyết trực tiếp "bấm nhiều transition mới gặp card" mà không phạm nguyên tắc.
5. **`checkpoint_audit` lên UI dev-mode?** để reviewer phân biệt "im vì policy" vs "im vì mất association".
6. **Ranh giới S8 (penalty):** phần nào thuộc F3 in-scope, phần nào rơi vào dự án giải trình vi phạm (D-006) đã tách?
7. **Thí nghiệm mưa trong SIM:** có đáng chạy scenario `rain` (máy móc có sẵn, đang tắt) để đo trần giá trị advice thời tiết trước khi bàn external weather thật?
8. **Q-10 (PUSH/PULL budget), Q-09 (giá nhịp), V-21 (lưới 20′/30′), Q-13 (định nghĩa adherence)** — các quyết định cũ này chặn phần lớn thiết kế cadence/đo lường ở trên; thứ tự chốt?

## 9. Nguyên tắc đã tôn trọng & giới hạn

Không sửa code/cadence · không checkpoint giả · không bật LLM (provider=None toàn bộ phép đo) · không biến event kỹ thuật thành advice · không claim thu nhập (Q-13 mở) · accepted ≠ execution ở mọi bảng · mọi số từ run/artifact thật, nhãn FACT/OBSERVED/INFERENCE/UNVERIFIED · Bây giờ/Sắp tới tách bạch trong mọi scenario · không card chữ khi đang di chuyển (mọi candidate đều khai moving gate).

Giới hạn: funnel chỉ chạy seed 1000 (demo seed hiện hành); coverage estimate của candidate lấy từ UPDATE-145 (5 seed) — mọi con số coverage cần 30 seed trước khi chốt cadence; run 1 ngày nên tân binh/khoán tuần/S7 planned-rest chưa đo được.

## Phụ lục — nguồn số & tái lập

```
# Baseline verify (đã chạy, exit 0):
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-inventory/analyze_checkpoints.py \
  --seeds 1000 1001 1002 1003 1004 --output <scratch>/inv-5seed

# Ổn định 10 seed tươi:
  ... --seeds 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 --output <scratch>/inv-10seed-fresh

# Presentation funnel (script kèm thư mục này):
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-scenario-discovery/measure_presentation_funnel.py 1000
```

Code evidence chính: producer `advice_bridge.py:597,747,903,950` + `world.py:455` · policy order `checkpoint.py:234-290` · normalize cắt field `checkpoint.py:145-231,74-88` · facts 1-fact `advice_checkpoint.py:505-519` · template bỏ facts/caveats `checkpoint_templates.py:137` · freshness bịa `checkpoint_trace.py:63` · demo moving-gate không queued `advice_checkpoint.py:406-407` · S4 station rỗng `world.py:426` · dropoff boundary `world.py:709-729` · environment cô lập `environment.py` toàn bộ.

---

# Phase II — Deep opportunity discovery sau UPDATE-147

> **Phạm vi:** research/read-only đối với runtime. Phase này bổ sung hai script quan sát và
> các artifact phân tích; không sửa simulator, solver, checkpoint policy, cadence, Web hay LLM.
> Mọi threshold `30 phút idle`, `40% empty share`, `80–120% rolling median` bên dưới chỉ là
> **research probe**, không phải production rule.
>
> Nhãn Phase II: **FACT** = đọc/đo trực tiếp; **INFERENCE** = kết luận từ nhiều FACT;
> **IDEA** = hypothesis cần thử; **OWNER DECISION** = code/evidence không tự chốt được;
> **SIMULATOR-ONLY** = chưa có quyền/data live; **REAL-DATA-READY** = shape đã có đường map,
> không đồng nghĩa service live đang tồn tại.

## 10. Executive conclusion

**FACT — hệ thống không thiếu raw signal; nó thiếu lớp chuyển raw signal thành hành trình thông
tin.** Sau UPDATE-147, năm run seed 1000–1004 có **40.009 event, 18.699 segment, 4.705
checkpoint record**, nhưng chỉ **462 READY = 1,027 READY/driver-run**. Trong 4.705 record,
4.126 là `S2/shift_timing/ONLINE` suppressed và 116 ONLINE expired. Mở chúng thành card sẽ làm
tăng noise chứ không làm tăng giá trị.

**FACT — ba kho dữ liệu giàu nhất đang ít hoặc chưa đi tới UI:** 

1. `DriverJourney` đã ghép sessions, segments, idle suy diễn, offers, income curve và breakdown
   payout (`src/gsm_sim/journey.py:64,109,160,201`), nhưng Web chỉ render snapshot/transition
   hiện hành.
2. `DriverMemory` đã giữ acceptance/completion, points/hour, payout/trips, planned rest và weekly
   totals qua ngày (`src/gsm_sim/multiday.py:52-79,110-179`), nhưng chưa có checkpoint producer
   cho baseline cá nhân hoặc repeated pattern.
3. `World.log()` giữ event detail về SOC-skip, cancel-after-accept, mission, newbie, rating và
   swap friction (`src/gsm_sim/world.py:190-221,635,697,750,768,1102,1154`), trong khi snapshot
   checkpoint chỉ dùng một phần nhỏ.

**INFERENCE — derived state có đòn bẩy cao nhất không phải thêm một rule/event-card, mà là:**
`plan revision`, `energy continuity episode`, `plan-versus-actual`, `rolling personal baseline`,
`repeated idle/friction pattern`, `incentive stack` và `end-of-shift synthesis`. Chúng kết hợp
current state + recent history + future plan + provenance, đúng chỗ dự án khác một notification
engine đơn giản.

**Khuyến nghị portfolio:** một ca nên có **1 brief + 2–4 actionable nudges + 1–3 passive/composite
insights + 1 recap**, cộng Why theo yêu cầu. Đây là mục tiêu 5–10 touchpoint nhưng chỉ 2–4 lần
gây gián đoạn; không đổi budget/cadence hiện hành cho tới khi owner duyệt và 30-seed calibration.

## 11. Evidence và giới hạn

### 11.1 Năm seed sau foundation fixes

| Chỉ số | Kết quả | Nhãn |
|---|---:|---|
| Run / driver-run | 5 / 450 | FACT |
| Event / segment | 40.009 / 18.699 | FACT |
| Checkpoint record / READY | 4.705 / 462 | FACT |
| Driver-run có ≥1 READY | 302/450 (67,1%) | FACT |
| READY/driver-run p50 / p75 / p90 / max | 1 / 2 / 2 / 4 | FACT |
| S1 bonus READY | 198 | FACT |
| S2 SWAP READY / expired | 207 / 1 | FACT |
| S2 REST READY | 57 | FACT |
| S2 ONLINE suppressed / expired | 4.126 / 116 | FACT |

Nguồn: `deep-opportunity-evidence.json`, tạo bởi
`analyze_deep_opportunities.py` qua đúng `_default_run(seed)` của Web demo. Khác số baseline ở
§2 vì đây là code **sau UPDATE-147**: revision không còn bị dedup nhầm, validity thật đã thay
freshness 1 phút giả.

### 11.2 Probe coverage — chứng minh data availability, không phải trigger đã duyệt

| Derived opportunity probe | Actor-run có tín hiệu | Diễn giải đúng |
|---|---:|---|
| Brief inputs / recap inputs | 450 / 450 | Có đủ khung ca và kết quả cuối ca để project, chưa có producer/UI |
| Current action khác future plan | 450 | Nằm trong record S2, phần lớn vẫn maintenance-silent |
| ONLINE-now + future SWAP | 387 | Candidate `SWAP_SOON`, không có nghĩa 387 card nên hiện |
| Có `order_skipped_soc` / lặp ≥2 lần | 95 / 20 | Awareness/episode candidate, không được khuyên nhận cuốc cụ thể |
| Swap failure hoặc wait >5 phút | 110 | Station-friction chỉ đáng dùng ở simulator khi chưa có live inventory |
| Có idle block suy diễn ≥30 phút | 379 | Chứng minh coverage; threshold và inference chưa đủ làm nudge |
| Empty share ≥40% | 361 | Phù hợp analytics/recap; không tự suy ra target zone |
| Cancel sau accept | 169 | Có thể recap chi phí thời gian, không đổ lỗi tài xế |
| Mission completed | 282 | Passive acknowledgment/recap, không cần popup |
| Newbie settlement event | 76 | Persona-specific, policy đang MOCK |

Phân bố probe: longest inferred idle p50/p75/p90 = **40/42/44 phút**, max 208,162; empty
share p50/p75/p90 = **44,2%/48,5%/51,8%**; SOC skip p90 = 1, max 4. Các con số này không
phải ngưỡng khuyến nghị.

### 11.3 Corpus 90 ngày MOCK

`data/mock/realdata-v1/manifest.json` khai `MOCK`, 90 ngày, 150 profile. Probe đọc trực tiếp:

- 12.821 row cho mỗi bảng income/stat/online/rush/stoppoint; 11.771 driver-day đủ 7 quan sát
  trước đó để tính rolling median.
- Probe ±20% so với median 7 ngày bắt 2.154 ngày thấp và 2.291 ngày cao; **cả 150 driver đều
  bị bắt ít nhất một lần**. FACT này chứng minh baseline tính được nhưng đồng thời chứng minh
  threshold quá rộng/noisy, chưa xử lý weekday/shift/persona và không thể ship.
- 88/150 driver có ít nhất hai ngày liên tiếp acceptance <0,85; đây là repeated-pattern input,
  không phải bằng chứng cần nudge.
- Mission: 6 catalog, 261 progress row/150 driver, 7.658 earn row/134 driver.
- Hex tracking: 1.420.051 row/90 driver; 67.562 row idle có stay ≥300 giây; 70.941 row có
  campaign/target/reached labels. Dữ liệu có thể audit official reposition outcome nhưng không
  chứng minh live freshness hay quyền đưa target mới.
- Trips MOCK: 172.079 row/150 driver có distance/duration/pickup/drop. Data catalog hiện chưa
  xác nhận đầy đủ các cột production tương ứng.

## 12. Raw-data coverage map

Bảng đầy đủ 35 signal group nằm ở `raw-signal-coverage.csv`. Bản đồ rút gọn theo mức sử dụng:

| Tình trạng | Raw source và signal | Consumer hiện tại | Opportunity | Nhãn/điều kiện |
|---|---|---|---|---|
| Đang dùng tốt | S1 points/acceptance/completion/policy; S2 SOC/rest/shift; canonical checkpoint validity/action/future | S1/S2 → normalize/policy/template | Bonus, SWAP-now, REST | FACT; SIMULATED/MOCK |
| Có nhưng chưa đến checkpoint | Actor time ledger; World event detail; journey income/offer/timeline; mission/newbie/rating; station wait/fail | metrics/settlement/research | passive insight, composite, recap | FACT; cần projection/producer |
| Có thể tổng hợp | checkpoint revisions + segments; income curve + personal history; repeated SOC/idle/cancel; plan + actual | chưa có consumer driver-facing | plan deviation, energy episode, baseline, pattern | INFERENCE; cần derived-state contract |
| Có logic nhưng cần internal/live contract | SOC, intraday payout ledger, activity/segment feed, station capacity, authoritative mission/policy | sim solvers | chuyển capability sim sang product | GAP; không dùng proxy làm live |
| Schema gần dữ liệu thật | daily KPI, income, online hours, rush split; một phần hex/mission | L1R feature derivation | daily/weekly brief, personal trend | REAL-DATA-READY **về shape**, current values vẫn MOCK; cần source/freshness/PII contract |
| Simulator showcase only | market supply+demand/capacity, rain/temp/event, congestion-from-order-density | S4/world dynamics | capacity-aware positioning, environment plan-change story | SIMULATOR-ONLY; không claim live |
| Không nên driver-facing | raw anomaly/fraud flag, per-order accept/decline, raw ONLINE maintenance, OSRM geometry | internal/display | analytics/governance hoặc reject | risk false accusation, dispatch boundary, spam, source mismatch |

### Tín hiệu đang bị cô lập đáng chú ý

- **Actor time ledger:** `empty_min`, `occupied_min`, `idle_min` tồn tại trên actor
  (`entities.py:71`) nhưng `World.log()` snapshot hiện không capture chúng. `DriverJourney`
  có thể project từ segments mà không đổi dynamics, song confidence phải là `INFERRED`.
- **Income sources:** journey tách trip/day-bonus/mission/newbie (`journey.py:226-250`), trong khi
  card hiện không kể được “thu nhập đến từ đâu” hoặc pace theo thời gian.
- **Offer friction:** decline reason, SOC skip và cancellation có event detail, nhưng ranh giới
  cấm per-order advice vẫn giữ; chỉ tổng hợp window/recap.
- **Lịch cá nhân:** memory cập nhật sau khi ngày kết thúc, tránh future leak
  (`multiday.py:_update_memory`); đây là nền an toàn hơn baseline cohort.
- **Capacity anti-herding:** `market_state.py` đã tính `supply_incoming` và `capacity_left`, nhưng
  nếu thiếu supply thì positioning không đủ căn cứ. Đây là feature showcase, không shortcut bằng
  demand heatmap đơn.
- **Môi trường/congestion:** rain/temp/event và slowdown có model deterministic
  (`environment.py`, `congestion.py`), nhưng demo mặc định dry và congestion là proxy từ mật độ
  order, không phải traffic telemetry.

## 13. Opportunity space

Bảng 33 capability đầy đủ nằm ở `opportunity-catalog.csv`. Phân nhóm sản phẩm:

### 13.1 Brief và plan awareness

| Capability | Thành phần | Trạng thái | Giá trị / guard |
|---|---|---|---|
| Shift brief | shift window + initial plan + bonus/mission state + confidence | **small wiring** | một lần/ca; không đốt proactive budget |
| Current plan strip | current action + future plan + validity | **ready now** cho checkpoint hiện có | passive; không mass-unsuppress ONLINE |
| New-driver program brief | tenure + guarantee/mốc + policy version | **new policy-backed producer** | MOCK policy hiện tại; không nói như chương trình GSM thật |
| Rush-window personal pattern | rush split + online history | **small wiring** | lịch sử không bảo đảm demand tương lai |
| Weekly pace | history + quota authority | **new policy contract** | S5 có solver nhưng quota/basis còn TBC |

### 13.2 Actionable in-shift nudge

| Capability | Thành phần | Trạng thái | Giá trị / guard |
|---|---|---|---|
| Bonus feasibility | S1 + typed policy numbers | **ready now** | chỉ khi eligibility/action material; không hứa bonus |
| SWAP now | S2 current SWAP + SOC + window | **ready now in sim** | product fail-closed tới REAL/LIVE SOC |
| Rest window | S2/S7 + continuous activity + remaining shift | **small wiring** | health không phải objective thu nhập; moving gate |
| Swap soon | ONLINE now + future SWAP + SOC trend | **new producer/policy decision** | không mở toàn bộ maintenance; one energy-group card |
| End/extend shift | boundary + plan + safety + incentive | **owner policy decision** | không khuyến khích kéo dài thiếu safety policy |
| Plan deviation requiring action | prior plan + material state delta + fresh solve | **new derived trigger** | action vẫn chỉ từ solver/rule, không từ projection/LLM |

### 13.3 Passive insight và composite

| Capability | Thành phần | Trạng thái | Giá trị / guard |
|---|---|---|---|
| Bonus/mission progress | current points + next tier/window + mission progress | **small wiring** | merge cùng incentive group, không popup mỗi trip |
| Income pace | intrashift curve + personal historical baseline | **new projection/contract** | descriptive band; không forecast chắc chắn |
| Repeated long idle | inferred idle windows + personal baseline | **new projection** | không tự target zone; confidence visible |
| Empty-time efficiency | empty/occupied segments + baseline | **analytics/recap** | không đồng nghĩa tài xế chọn sai vị trí |
| Energy disruption chain | plan + SOC skips + swap wait/fail + SOC after | **new composite projection** | observed sequence; relation `coincident`, không causal |
| Cancellation recovery | wasted pickup time/SOC + subsequent plan | **new projection** | neutral wording; no blame/no income-causality claim |
| Mission completion | event + policy reward source | **ready for passive UI** | once per mission; not interruptive |
| Why plan changed | immutable old/new checkpoint diff | **new derived artifact** | explanation-only; không đổi action/window |
| Policy change | version diff + effective time + source | **new authoritative producer** | only when source contract exists |

### 13.4 Recap, analytics và internal-only

- **Shift recap — small wiring:** journey metrics + income sources + checkpoint lifecycle +
  execution links. Tách `displayed/accepted/execution_observed/outcome`; cấm uplift claim.
- **Rolling baseline — new internal contract:** 7–30 ngày theo chính tài xế; cần minimum history,
  seasonality và treatment-contamination guard.
- **Repeated risk — research:** consecutive KPI/idle/energy patterns; phải tránh shame/surveillance.
- **Penalty explanation — on-demand/defer:** S8 có logic, nhưng formal violation explanation là
  project boundary riêng và cần authority/appeal path.
- **Anomaly/fraud — internal only:** false-positive/privacy/gaming quá cao để làm driver nudge.
- **Rating trend — opt-in recap:** giá trị thấp, interruption cost cao; không popup.
- **Specific-order acceptance/cancellation — reject:** vi phạm dispatch boundary.

## 14. Composite opportunities — nơi simulator tạo khác biệt

| Derived state | Cửa sổ | Inputs | Trải nghiệm | Vì sao không thể là một event-card |
|---|---|---|---|---|
| Plan revision | từ checkpoint trước tới checkpoint mới | old/new action, future head, window, changed facts/caveats | “Kế hoạch vừa đổi vì…” | một record mới không giải thích delta |
| Energy continuity episode | từ cảnh báo đầu tới swap/charge hoặc end shift | SOC curve, skip events, future SWAP, wait/fail, segment | composite + recap | từng event riêng không cho thấy chuỗi gián đoạn |
| Plan-versus-actual | từ plan validity tới execution window | planned steps + observed segments/events | passive status / recap | cần phân biệt consistent/coincident/deviated, không causal |
| Personal pace | elapsed shift + 7–30 prior comparable days | payout/points/trips curve + personal baseline | passive insight | một payout snapshot không có baseline |
| Repeated friction | rolling 30–90 phút hoặc nhiều ngày | idle/cancel/SOC skip/station wait counts | low-interruption pattern card | single occurrence dễ là noise |
| Incentive stack | shift/day/week | bonus eligibility + mission + guarantee + policy versions | brief/progress/recap | một solver chỉ thấy một chương trình |
| Recovery balance | continuous online + rest + remaining shift | activity timeline + planned rest + state | rest planning | cần lịch sử gần đây và future window |
| End-of-shift synthesis | toàn ca | journey + money sources + lifecycle + execution links | recap | giá trị nằm ở chuỗi, không ở end_shift event |

**INFERENCE:** `Plan revision` và `energy continuity episode` là hai capability độc đáo nhất cho
demo vì chúng dùng identity/lifecycle/checkpoint artifacts hiện có, cho thấy “hiểu quá khứ—hiện
tại—tương lai” mà không trao quyền quyết định cho LLM.

## 15. Portfolio UI — tăng touchpoint, không tăng interruption tuyến tính

| Surface | Mục tiêu/ca | Nội dung phù hợp | Presentation budget |
|---|---:|---|---|
| Pre-shift brief | 1 | plan, bonus/mission state, caveats dữ liệu | ngoài proactive budget; một lần |
| Actionable nudge | 2–4 thường gặp; giữ trần hiện hành tới khi duyệt | bonus-at-risk, SWAP now, rest, material plan change | chỉ ở safe state; cadence/dedup hiện hành |
| Passive insight | 1–3 | pace, mission progress, idle/empty pattern, plan strip | không toast; update-in-place theo material version |
| Composite card | 0–2 | energy episode, why-plan-changed, recovery | chỉ khi nhiều signal thật sự bổ sung nghĩa |
| On-demand Why | theo click | explain immutable checkpoint/context | không proactive; không gọi solver |
| Post-shift recap | 1 | journey, money sources, advice intent/execution/outcome | một lần; không causal claim |
| Analytics/detail | không quota | history/baseline/rating/weekly | pull-only, opt-in |

**IDEA cần kiểm chứng:** dùng một “plan strip” passive bền trong ca thay vì biến mọi S2 ONLINE
revision thành notification. Khi plan thay đổi material, strip update version; chỉ phát nudge nếu
current action cần làm hoặc future boundary gần và đủ dữ liệu. Cách này tận dụng 4.242 ONLINE
record quan sát được mà không biến chúng thành 4.242 popup.

## 16. Real-data feasibility matrix

| Capability | Feasibility | Minimal real contract | Thiếu data xử lý thế nào |
|---|---|---|---|
| S1 bonus + progress | **REAL-DATA-READY về shape / small wiring** | daily KPI + policy version + fresh intraday points nếu nudge | daily-only ⇒ brief/recap hoặc low-freshness badge; không giả current |
| Shift brief/recap | **small wiring in sim** | shift/session service + ledger/activity source | thiếu source ⇒ chỉ các section có data, không bịa |
| Current/future plan | **ready in sim; product blocked S2** | REAL/LIVE SOC/rest/elapsed state + freshness | fail-closed S2 như hiện tại |
| Mission progress | **small wiring after authority** | catalog/progress/earn + policy effective time | source stale ⇒ passive awareness, không action |
| Income pace/baseline | **new internal contract** | intraday payout ledger + comparable-day history | daily-only ⇒ historical analytics, không intrashift nudge |
| Idle/empty efficiency | **new internal contract** | activity/segment feed or GPS-derived activity + confidence | thiếu confidence ⇒ analytics-only/silent |
| Energy episode | **new internal contract** | trusted SOC events + charge/swap observations + station outcomes | không SOC ⇒ silent; không dùng proxy |
| Station friction | **simulator showcase now** | live inventory/queue/reservation timestamps | thiếu ⇒ chỉ recap observed wait, không suggest station |
| Capacity positioning | **SIMULATOR-ONLY** | demand + supply now/incoming + capacity + governance | thiếu bất kỳ capacity input ⇒ no recommendation |
| Environment/traffic | **SIMULATOR-ONLY / external required** | versioned weather/traffic feed + freshness/reliability | tắt feature; OSRM geometry không thay thế traffic |
| Weekly pace | **new policy contract** | authoritative quota/basis + weekly ledger | policy TBC ⇒ no card |
| Penalty/anomaly | **defer/reject ordinary nudge** | authoritative record + explanation/appeal governance | internal-only hoặc no display |

`REAL-DATA-READY` ở đây chỉ nói **shape đã xuất hiện trong catalog/deriver**
(`from_l1r.py:102,179,218,275,323`), không nói repository đang nối service live. Corpus đo là MOCK;
S2 product vẫn đúng khi trả `missing_state` vì `derive_shift_plan_input_l1r()` đặt `soc_pct=None`
(`from_l1r.py:477-527`).

## 17. Prioritization và candidate arbitration

### 17.1 Ưu tiên theo dependency và giá trị

| Tier | Capability | Lý do |
|---|---|---|
| P0 | Shift recap, shift brief, current plan strip | coverage 100%, tận dụng projection hiện có, không tăng interruption |
| P0 | Bonus facts/progress, mission completion passive | producer/event đã có, dễ giải thích, data typed |
| P1 | Energy continuity + `SWAP_SOON` material | coverage cao, câu chuyện mạnh; cần producer/topic/policy và product SOC contract |
| P1 | Why plan changed / plan-versus-actual | độc đáo nhất; cần immutable checkpoint diff + relation taxonomy |
| P1 | Rest/recovery composite | giá trị cao; cần activity confidence và safety/product owner |
| P2 | Income pace + rolling baseline | giá trị/cá nhân hóa cao nhưng cần intraday ledger, seasonality và threshold calibration |
| P2 | Repeated idle/empty/cancellation | useful passive/recap; không đủ căn cứ để positioning action |
| Showcase | Capacity-aware positioning, weather/event plan change | thể hiện simulator, không chuyển thành live claim |
| Reject/defer | raw ONLINE, per-order advice, anomaly nudge, rating popup | spam/boundary/fairness/interruption cost |

### 17.2 Thứ tự chọn khi nhiều candidate cùng lúc

Không đặt trọng số chưa được duyệt. Đề xuất pipeline deterministic:

```text
safe-to-read state
→ complete + fresh + provenance-qualified
→ canonical action/window exists (nếu actionable)
→ material change from last presented version
→ personal relevance
→ topic novelty/diversity
→ interruption cost
→ existing policy priority
→ stable ID tie-break
```

Gom theo semantic group trước khi chọn primary:

- **Energy:** SWAP_SOON + SOC-skip + station friction → một energy-continuity presentation;
- **Progress:** bonus + mission + income pace → một progress composite, nhưng action chỉ từ S1/rule;
- **Recovery:** planned rest + continuous online + idle pattern → một rest/recovery card;
- **Plan:** revision + plan-versus-actual → update plan strip, chỉ interrupt nếu action material;
- **Recap:** tổng hợp mọi group nhưng giữ intent/execution/outcome thành ba dòng riêng.

## 18. Demo storylines từ trajectory thật

Artifact `deep-demo-storylines.json` chứa toàn bộ checkpoint, key event, journey metric và links
của ba actor; không có fixture tạo riêng.

### Story A — Energy continuity và plan revision

- **Seed/run/actor:** 1000 / `1000-B-sp+al-all-c9beb6ef2` / actor 35 (P3).
- **Chuỗi thật:** bonus READY lúc 572 → SWAP READY lúc 781 → swap 781–803 (wait 13′) →
  SOC-skip lúc 1117 (SOC 20,4%, need 8,35 km) và 1148 (SOC 9,6%, need 6,79 km) → SWAP
  READY + thực thi lúc 1152–1158 → mission events → end shift 15 trip, payout 330.636,
  90 points.
- **UI journey đề xuất:** brief → bonus nudge → energy card → passive “plan đã đổi” → recap
  chuỗi energy + mission. Execution links là `coincident` confidence 0,6; **không** nói advice
  gây ra swap hoặc thu nhập.
- **Giá trị demo:** current/future, state change, safe presentation, observed execution và recap
  cùng một story.

### Story B — Rest, cancellation và energy recovery

- **Seed/actor:** 1000 / actor 70 (P6).
- **Chuỗi thật:** REST READY 300 → bonus READY 361 → cancel-after-accept 398 → mission 471 →
  SOC-skip 471 (SOC 10,1%) → SWAP READY/execution 476 → bốn rest events sau đó → end shift
  7 trip, payout 152.384, 45 points.
- **UI journey đề xuất:** rest nudge → neutral cancellation insight → energy recovery → recap.
- **Guard:** cancellation không được dùng để trách tài xế; không claim rest/swap làm tăng payout.

### Story C — New-driver incentive stack

- **Seed/actor:** 1000 / actor 37 (P4).
- **Chuỗi thật:** bonus READY 407 → mission 498 → SWAP READY 624 → rest → mission 879 →
  swap 885 → newbie topup 926 (gross 279.126; floor 350.000; topup 53.156) → end shift
  12 trip, payout 322.500, 75 points.
- **UI journey đề xuất:** policy-labelled brief → bonus/mission progress → energy nudge → recap
  tách trip payout/mission/newbie.
- **Guard:** các policy là MOCK; demo phải hiển thị provenance, không nói đây là chính sách live.

## 19. Safety, spam, herding, fairness và misunderstanding

| Risk | Failure mode | Guard bắt buộc |
|---|---|---|
| Spam | event hoặc S2 consult nào cũng thành card | semantic grouping + material fingerprint + topic cooldown + passive update |
| Interruption | 5–10 touchpoint bị hiểu thành 10 popup | tách budget proactive khỏi brief/passive/Why/recap |
| Safety | text dài lúc ENROUTE/ON_TRIP | queue/silent theo current state; revalidate trước present |
| Herding | nhiều driver nhận cùng target | chỉ S4 capacity-aware với supply incoming/capacity; sim-only tới governance/live data |
| Fairness | baseline cohort/phân loại persona làm thiệt nhóm | ưu tiên baseline chính tài xế; audit coverage theo archetype/fleet/history availability |
| Misunderstanding | current ONLINE nhưng future SWAP bị viết thành “đổi ngay” | code-owned current/future sections + regression template |
| Causality | execution gần checkpoint bị gọi là advice effect | `coincident/consistent/deviated/causal` tách; causal chỉ explicit intervention |
| Income promise | pace/forecast thành chắc chắn | descriptive band + caveat/provenance; không uplift claim |
| Privacy | coordinates/trip history/raw IDs vào card/LLM | derived allowlist, H3/aggregate khi cần, no raw PII |
| Surveillance | rating/fraud/penalty thành nudge | rating opt-in recap; anomaly internal; penalty project boundary riêng |

Coverage theo archetype trong 450 actor-run không đồng đều: P1 chỉ 14/65 có READY, trong khi P4
80/80 và P6 74/80; future-SWAP signal lại phủ hầu hết P2–P7 nhưng chỉ 2/65 P1. **INFERENCE:**
portfolio bắt buộc fallback theo data/state của từng persona; không nên đặt quota card đồng nhất.

| Archetype | Actor-run | Có READY | Future-SWAP | SOC-skip | Idle probe | Mission | Newbie event |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 65 | 14 | 2 | 0 | 21 | 13 | 0 |
| P2 | 90 | 64 | 90 | 27 | 85 | 65 | 0 |
| P3 | 25 | 14 | 25 | 9 | 25 | 19 | 0 |
| P4 | 80 | 80 | 80 | 10 | 75 | 37 | 76 |
| P5 | 55 | 19 | 55 | 17 | 49 | 28 | 0 |
| P6 | 80 | 74 | 80 | 14 | 74 | 73 | 0 |
| P7 | 55 | 37 | 55 | 18 | 50 | 47 | 0 |

## 20. Measurement plan

### 20.1 Unit đo riêng

- **Candidate:** derived signal đủ input trước policy.
- **Checkpoint:** canonical recommendation/information record.
- **Presentation:** brief/nudge/passive/composite/recap được offer/render.
- **Intent:** displayed/accepted/dismissed/expanded.
- **Execution:** observed segment/event link.
- **Outcome:** payout/trip/SOC/rest sau đó.
- **Effect:** chỉ causal/policy effect khi có paired design phù hợp; không suy từ outcome.

### 20.2 Dashboard discovery → rollout

| Nhóm | Metric |
|---|---|
| Useful coverage | meaningful touchpoint/driver-shift; driver có ≥1 brief/nudge/recap; coverage theo archetype/fleet |
| Interruption | proactive nudge/shift/hour; safe-state offer; queued/silent; interruption-free hours |
| Diversity | distinct semantic groups; single vs composite share; scenario entropy; repeated wording/key rate |
| Timing | time-to-first useful touchpoint; inter-touchpoint interval; validity remaining at display |
| Data quality | missing input; stale; MOCK/REAL/LIVE/PROXY share; confidence/caveat coverage |
| Lifecycle | offered/displayed/accepted/dismissed/expanded riêng; execution relation/confidence riêng |
| Portfolio | brief/nudge/passive/composite/recap mix; primary conflicts; merged vs suppressed candidates |
| Portability | capability ready-now/small-wiring/new-contract/live-required; source contract coverage |

Trước production-rule proposal: chạy ≥30 seed, report median/p75/p90/max theo driver và persona;
human review usefulness/repetition; sau đó mới chốt threshold/cooldown. Không dùng một average
fleet để ép driver ít tín hiệu nhận card rỗng.

## 21. Roadmap theo dependency thực tế

1. **R0 — Foundation closeout:** xử lý/định nghĩa rõ `dropoff` state boundary còn mở trong
   UPDATE-147; tạo pure `DriverJourneyView/DerivedSignal` contract có source, observed/inferred,
   freshness, window và confidence. Không tạo producer trước khi projection đáng tin.
2. **R1 — Zero/new-interruption portfolio:** shift brief, current plan strip, mission-completion
   passive, shift recap. Tái sử dụng data hiện tại, không đổi proactive cadence.
3. **R2 — Event-window composites:** energy continuity, Why plan changed, bonus/mission progress,
   recovery summary. Thêm producer/checkpoint chỉ khi có material change và execution relation rõ.
4. **R3 — Personal history:** rolling baseline, income pace, repeated pattern dùng DriverMemory và
   90-day L1R; thiết kế minimum-history, comparable-day và future-leak/treatment guards.
5. **R4 — Simulator showcase:** capacity-aware positioning và environment-driven plan change trên
   scenario có thật; nhãn SIMULATOR-ONLY, không nhập vào live taxonomy.
6. **R5 — Product data contracts:** trusted SOC/activity/intraday ledger/station/policy sources;
   per-source freshness, kill-switch và fail-closed. Chỉ lúc đó promote capability tương ứng.

## 22. Owner decisions

Các mục dưới đây đều mang nhãn **OWNER DECISION**:

1. Định nghĩa chính thức “touchpoint hữu ích” và brief/passive/Why/recap có tính vào mục tiêu
   5–10 hay không; proactive budget hiện hành có giữ nguyên tuyệt đối trong phase portfolio?
2. Chọn P0 product slice: brief+recap trước hay energy/plan composite trước.
3. Duyệt taxonomy/surface mới (`passive`, `composite`, `SWAP_SOON`, `plan_revision`) và schema
   versioning; không overload topic cũ chỉ để tránh migration.
4. Plan revision nên supersede checkpoint cũ, update một passive plan artifact, hay làm cả hai với
   identity riêng?
5. Threshold/baseline: comparable-day definition, minimum history, material delta và confidence;
   probe 30′/40%/±20% không được dùng làm mặc định.
6. Nguồn authority/freshness nào được chấp nhận cho intraday payout, SOC, activity, station và
   mission/policy trước khi gắn REAL/LIVE?
7. Có giữ capacity positioning hoàn toàn sim-only cho tới khi có allocation governance và
   anti-herding telemetry? Khuyến nghị: có.
8. Phân tách UI driver/manager/developer cho checkpoint audit, anomaly, station và causal metrics.
9. Các quyết định cũ Q-13 (measurement), V-21 (cadence), V-25 (visual) vẫn mở; research này không
   tự đóng hoặc thay đổi chúng.

## 23. Artifact và tái lập Phase II

```text
research/audit/2026-08-05-checkpoint-scenario-discovery/
├── analyze_deep_opportunities.py      # five-seed + 90-day MOCK observer
├── deep-opportunity-evidence.json     # aggregate evidence/provenance/threshold warning
├── deep-opportunity-by-actor.csv      # 450 actor-run rows
├── deep-event-inventory.csv           # event count + detail-key inventory
├── extract_deep_storylines.py         # exact selected-trajectory extractor
├── deep-demo-storylines.json          # actors 35, 70, 37; seed 1000
├── raw-signal-coverage.csv             # 35 signal groups
└── opportunity-catalog.csv            # 33 capabilities
```

Tái lập:

```bash
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-scenario-discovery/analyze_deep_opportunities.py \
  --seeds 1000 1001 1002 1003 1004

PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-scenario-discovery/extract_deep_storylines.py \
  --seed 1000 --actors 35 70 37
```

**Adversarial self-review:** (a) journey idle là inferred từ khoảng trống, không observed;
(b) mock L1R shape không chứng minh production service/freshness; (c) thresholds cố ý nhạy để tìm
opportunity, không đo precision/usefulness; (d) actor được chọn sau khi xem CSV nên là demo
selection, không out-of-sample evidence; (e) execution link `coincident` không phải causal;
(f) report không đo UI human preference; (g) foundation diff UPDATE-147 còn uncommitted trong
worktree nên Phase II evidence phản ánh current worktree, không chỉ HEAD `276df6d`.
