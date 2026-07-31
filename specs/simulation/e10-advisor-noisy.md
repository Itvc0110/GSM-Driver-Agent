# SPEC THI CÔNG E10 — ADVISOR CŨNG NHIỄU: "+6.016đ còn lại bao nhiêu khi advisor mất λ?"

Ngày: 2026-07-31 · Trạng thái: **SPEC CUỐI — TỔNG HỢP, chưa implement, chưa đo** (chờ duyệt plan mode)
Nguồn: 3 thiết kế độc lập (`e10a-estimator`, `e10b-wait-trigger`, `e10-measurement`) + 6 lượt phản biện
đối kháng theo lăng kính rò-rỉ-oracle. Spec này NHẬN phần đứng vững, VÁ các lỗ phản biện chỉ ra, và
GHI RÕ ở §9 những lỗ **không vá được** — chúng là giới hạn tường minh của phép đo, không được im.

Mọi con số trong tài liệu này là **MOCK** (`configs/pilot_dongda.yaml`) hoặc số kế hoạch.
Đây là **câu hỏi**, không phải mục tiêu phải chứng minh: nếu Δ sụp về ~0 thì đó là kết quả quan trọng
nhất dự án từng đo và **phải báo đúng như vậy** (`tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` §3).

**Ba điểm chờ Cường chốt trong plan mode trước khi code** (spec đề xuất, không tự quyết):
1. Thêm arm `B_hist` (advisor-có-lịch-sử) — mở rộng từ 3 arm của PLAN lên 4 arm chính + 1 arm chẩn
   đoán. Lý do ở §5.1; không thêm code engine (dùng hook `market_demand_override` sẵn có).
2. Nếu cổng tiền-flight §5.5 bắn trên chính arm oracle: sửa THƯỚC adherence positioning (followed =
   coin-outcome tại lúc gán; execution rate tách thành chỉ tiêu riêng) — một mini-cycle riêng, đổi
   nghĩa một con số đã báo.
3. Ngân sách máy ~5–5,5h (nhiều hơn ước ~3–4h của PLAN vì thêm arm + sweep T).

---

## §0. Sự thật code đã tự kiểm (mở file ngày 2026-07-31 — KHÔNG chép lại từ thiết kế nào)

| Điểm | File:line | Nội dung đã xác nhận |
| --- | --- | --- |
| Nguồn λ oracle | `src/gsm_sim/demand.py:76` | `expected_demand_field` = orders_per_day × hour_share × cell_weight, deterministic theo config; gán `world.demand_field` tại `world.py:143` |
| `cell_weight` | `demand.py:38-62` | LÀ luật không gian noise-free của generator ⇒ cấm làm prior mặc định |
| Advisor đọc λ | `src/gsm_sim/market_state.py:94-99` | `_demand(hour)`: `demand_override` (fictitious play, THAY THẾ không merge) thắng, rồi `world.demand_field` |
| Producer chỉ dựng khi cần | `world.py:156-161` | `market = None` trừ khi `advice.enabled` ∧ `positioning_overrides != "off"` ⇒ World A không chạm code mới |
| Consumer duy nhất của `view()` | `world.py:294` | grep toàn `src/`: chỉ `_standby_planner`; tests dựng producer trực tiếp (`tests/test_market_state_sim_producer.py:134-160`, stub cần guard `hasattr(world,"cfg")` ở `market_state.py:79`) |
| Trigger hiện tại | `world.py:307` | ứng viên = IDLE + covered + `cap_left.get(a.cell,0)==0`; cadence check `world.py:313-315`; `pref` = ô còn trần gần nhất `world.py:318` |
| Coin | `advice_bridge.py:401-425, 582-592` | keyed sha256 (`adherence_coin`), rút MỘT lần lúc gán (`world.py:353`) — **0 lần tiêu `world.rng`**. ⚠ docstring :589 nói "cùng dòng RNG" là chữ CŨ, code thật là keyed — sửa docstring khi chạm file |
| Mẫu số positioning | `world.py:335-339` + `projections.py:212-242` | decided = `standby_alloc.assigned_ids` (fail-loud khi thiếu decision_id); followed = event `standby_followed` (`projections.py:186-188`). Comment world.py: 86 gán / coin-true 42 / followed thật 36 (1 seed) |
| Pop im lặng | `world.py:781-785` | `sb_cell == actor.cell` ⇒ pop không log ⇒ coin-true không bao giờ thành followed |
| Cổng wait_only | `world.py:786-787` | plan chỉ áp khi bản năng == WAIT; `standby_plan` không TTL (`world.py:305`) |
| Event kinds | `world.py:470/394/531/584/609` | `order_expired` / `order_censored` (CẤM đọc — unserved); `order_matched` log **`actor.cell` = ô TÀI XẾ** (bẫy); `pickup` log **`order.pickup_cell`** (✅ nguồn duy nhất); `dropoff` log drop_cell |
| `log()` round t | `world.py:173-175` | `round(env.now, 3)` — jitter biên bucket deterministic, vô hại |
| slots/capacity | `src/gsm_core/features/market_state.py:81-82, 99-103` | `slots = int(demand // trips_per_driver_per_bucket)`; `capacity_left = max(0, slots − eff)`; `ranked` chỉ chứa ô cap>0, sort sd_ratio + tie tên ô |
| Hungarian stagger | `src/gsm_core/solvers/capacity_alloc.py:50` | cost zone ≠ target = `pen + 10.0` — **KHÔNG phải LARGE** ⇒ stagger sang bất kỳ zone còn slot là hành vi hợp lệ của S4 |
| Bản năng sốt ruột | `behavior.py:168-197` + `configs/pilot_dongda.yaml:202-204` | step **20′** (config, không phải default 30), max_steps 2 ⇒ give_up từ streak 40′, p_move 0,9/tick 2′ ⇒ phân phối streak **cụt ~40–44′** |
| `idle_streak_min` | `entities.py:53`; ghi tại `world.py:499/881/885` | reset khi được CHÀO (kể cả sau đó decline) / sau relocate; +2,0 mỗi tick WAIT. **Không nằm trong `_DAILY_RESET_*`** (`entities.py:125-132`) — bẫy multiday, ghi DEFERRED |
| Belief tài xế | `world.py:890-919` | λ × lognormal per-(seed, actor, hour, cell) — E10 **không đụng**; đọc `demand_field` tại :902 là đường HỢP LỆ (tiên đề mô hình) |
| Trace tương lai trên `world` | `world.py:119, 143` | `orders_sorted` (toàn bộ đơn cả ngày) và `demand_field` nằm ngay trên object `world` ⇒ estimator KHÔNG được cầm `world` |
| A/B pipeline | `parallel.py:39-52, 73-95, 195-211, 254, 291-325, 328-390` | `CHANNEL_LADDER["positioning"]`; `_cfg_with` mặc định `coverage="single"` (bẫy vận hành); `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100`; `aggregate_adherence` + z Poisson-binomial \|z\|>4 trên TỔNG seed, null từ `nominal_adherence(cfg)` |
| Fingerprint | `scripts/probe_adherence_truth.py:46, 151` | `fingerprint_actors` (segments+payout+trips+rest_min per-actor) + cờ `--fingerprint` có thật |
| Config | `pilot_dongda.yaml:22-29, 311-361` | start 300 / end 1440 / warmup 60; orders_per_day 1200; advice: coverage single, positioning_overrides wait_only, trips_per_hour_est 1.5, bucket_min 60 |
| Artifact numbering | `research/audit/2026-07-27-current-state/` | cao nhất = `40-l104-*` ⇒ E10 dùng prefix **`41-e10-*`** |

### §0b. Bảng tiếp nhận phản biện (traceability — cái gì nhận, vá ở đâu, cái gì không vá được)

| Finding phản biện | Phán quyết | Xử lý |
| --- | --- | --- |
| k\* tuning bằng RMSE-vs-λ = oracle chảy vào hyperparameter | **NHẬN** | §6.2: tiêu chí realized-only (MAE dự báo one-step-ahead), shadow trên World A |
| Estimator cầm `world` (orders_sorted/demand_field trong tầm với) | **NHẬN** | §3.4: narrow reader (`events` + scalars), whitelist test |
| Poison `world.demand_field` bất khả thi (bản năng cũng đọc) | **NHẬN** | §2.3: tách `demand_source` tại construction, poison đúng ref của producer |
| Tự-gán qua Hungarian stagger (không chỉ qua `pref`) — giết E10b | **NHẬN** | §4.4: zone-veto (một luật đóng cả tự-gán lẫn nguồn-đích chồng nhau) |
| Ứng viên gồm cả người streak 0 trong ô fire | **NHẬN** | §4.3: cổng cá nhân streak ≥ T (tái dùng T) |
| T=45/60 chết cấu trúc (impatience cụt streak ~40–44′); neo 27,7′ nhầm CYCLE với WAIT | **NHẬN** | §4.2: neo sửa lại 14–18′, lưới T {15,20,25,30,35}, control-run bắt buộc |
| n_min=1 headline = luật per-driver lách cửa sau (P bắn oan 0,17–0,47) | **NHẬN** | §4.3: headline n_min=2, biến thể 1 và 3 |
| Cổng D-M3-10 gộp n=100 chưa từng chạy trên positioning — sẽ TREO cả oracle vì gap coin-vs-execution | **NHẬN** | §5.5: bước tiền-flight bắt buộc + nhánh sửa THƯỚC (không nới ngưỡng) |
| "Mất λ" trộn với "mất trí nhớ qua đêm" (sim 1 ngày) | **NHẬN** | §5.1: thêm arm `B_hist` qua `market_demand_override` sẵn có |
| `supply_residual_corr` confound cơ học — "corr>0 = herding" sai cấu trúc | **NHẬN** | §3.6-B1: cửa sổ disjoint + null baseline từ A/B_oracle + cấm chữ "xác nhận" |
| Giao thức không pin coverage ⇒ đo cái tắt của chính mình | **NHẬN** | §5.2: `coverage="all"` pre-registered, script assert decided>0 |
| Fingerprint ở default-off là tautology (code mới unreachable) | **NHẬN** | §2.4: fingerprint trên CẢ HAI config (off và B_oracle) |
| `smooth_alpha` tự mâu thuẫn hai chỗ | **NHẬN, mạnh hơn** | BỎ hẳn α khỏi v1 — bớt một tham số; muốn smoothing thì pre-register lại |
| `n_buckets` âm trước giờ mở cửa; % câm thổi bởi bucket cấu trúc | **NHẬN** | §3.2/§3.3: `max(0, …)`, cold tường minh khi `idx ≤ first_op_bucket`, % câm chỉ trên bucket vận hành |
| `min_pickups` gần như trơ ở config này (~15–22 pickup/giờ thấp nhất) | **NHẬN** | §7: đăng ký TRƯỚC dự đoán "trơ"; sweep identical ⇒ báo "tham số trơ", cấm chữ "robust" |
| λ̂ đếm PICKUP nhưng λ là ORDER ⇒ deflation mức ~20–25% vào thẳng `slots` | **NHẬN** | §3.6-B2 + §5.4: decomposition volume (n_candidates/n_assigned/coin/executed) bắt buộc |
| Δ theo k ở n=30 vi phạm chuẩn n=100 variant-vs-variant | **NHẬN** | §6.4-G-SENS: n=30 chỉ đọc CHIỀU, nhãn `n_insufficient`, cấm trích độ lớn |
| Bảng 4 lớp kết luận thiếu caveat bất đối xứng (thế giới rank-tĩnh) | **NHẬN** | §6.3 + §9-L1 |
| Feed pickup TOÀN ĐỘI ngoài đời chưa VỮNG (catalog trips thiếu cột) | **NHẬN một phần** | không giết phép đo (không phải leak) — thành ASSUMPTION §9-L3, sensitivity subsample DEFERRED |
| λ̂ ngửi oracle QUA bản năng tài xế (pickup thấm λ) | **NHẬN — không vá được** | §9-L2 + diagnostic rank-corr bắt buộc kèm mọi KQ-GIỮ |
| Wait-trigger nhắm đúng nhóm mà `wait_only` không override được | **NHẬN — không vá được trong v1** | §9-L4 + bộ diagnostic execution-gate đọc CÙNG Δ (§4.6) |
| Đơn vị bucket lệch (counts theo giờ vs planner theo bucket_min) | **NHẬN, giải khác** | §3.2: counts key theo **bucket planner** (nhất quán mọi b) + assert `bucket_min==60` khi realized (phạm vi đo) |
| Arm 4 "chạy nếu Δ khó giải thích" = cửa hậu-nghiệm | **NHẬN** | §5.1: arm chẩn đoán `B_wait_oracle` chạy LUÔN ở n=30 |
| Percentile threshold cho T | **BÁC** (giữ kết luận thiết kế) | luôn-bắn / mẫu mỏng / không giải thích được — giữ ngưỡng tuyệt đối |
| Prior `cell_weight` cho cold-start | **BÁC** (giữ) | oracle-lite đúng nghĩa — cold = IM LẶNG |

---

## §1. Câu hỏi trung tâm — và vì sao nó đứng trên mọi thí nghiệm kênh khác

Advisor của sim nhận `expected_demand_field` = **đúng λ mà generator dùng để sinh đơn**
(`demand.py:76`), trong khi tài xế chỉ nhận `λ × exp(N(0,σ))` per-actor (`world.py:890`,
σ = 0,10–0,60 theo archetype). Ngoài đời advisor **không bao giờ** có λ — tín hiệu tốt nhất là mật
độ cuốc **ĐÃ phục vụ**, thiên lệch hệ thống về nơi **đã có** tài xế (hướng làm herding TỆ HƠN).

Vì thế `specs/real-data/data-contract-counterfactual.md` §4 hàng 1 xếp con số chủ lực
**+6.016đ/người/ngày** (positioning `wait_only`, coverage all, UPDATE-087, PASS 9/9 ĐA-08) vào cột
**LUNG LAY**: *"không phải sai 2× mà sai về BẢN CHẤT NGUỒN TIN"*.

> **Câu hỏi E10: +6.016đ còn lại bao nhiêu khi advisor mất λ?**

Bốn kết cục đều là câu trả lời hợp lệ (định nghĩa chính xác ở §6.3): GIỮ / CÒN-MỘT-PHẦN / SỤP / ÂM.
**Δ âm là kết quả thật, không phải bug** — tài xế trong sim vẫn giữ belief gần-λ (lão làng σ=0,10),
advisor mất sạch: advisor `wait_only` có thể kéo người đang đứng đúng chỗ tới ô slots-ảo do nhiễu
Poisson. Đăng ký trước cách đọc này để kết quả âm không kích hoạt vòng "đi tìm bug" thiên vị.

**Ràng buộc đo lường** (memory `gsm-sim-measurement-boundary`): chỉ **thuộc tính của lời khuyên**
được đổi (nguồn tin, trigger). Thế giới — belief tài xế, dispatcher, demand generator — giữ nguyên
từng bit ở mọi arm.

---

## §2. Kiến trúc: nguồn cầu là tham số của producer, default `oracle` bit-identical

### §2.1. Config (khối `advice:` của `configs/pilot_dongda.yaml`, + khối `probe:` mới)

```yaml
advice:
  # --- E10 (specs/simulation/e10-advisor-noisy.md). Mặc định GIỮ nguyên đường cũ ---
  market_demand_source: oracle       # oracle | realized. Giá trị lạ ⇒ ValueError (fail-loud).
                                     # realized + market_demand_override ⇒ ValueError: hai belief
                                     # THAY THẾ nhau (tiền lệ comment market_state.py:96-98),
                                     # trộn là vô nghĩa.
  realized_demand:
    window_buckets: 3                # k — GIÁ TRỊ HEADLINE đọc từ e10-prereg-locked.json, đây là
                                     # placeholder; quét {1,2,3,4,6}
    min_pickups: 5                   # min_n TOÀN CỤC (per-ô sẽ tái tạo lỗi mẫu số D-M3-01)
  positioning_trigger: capacity      # capacity (đường cũ, không đổi một ký tự) | wait (E10b)
  positioning_wait:
    threshold_min: 30.0              # T — neo §4.2, quét {15,20,25,30,35}
    min_idle: 2                      # n_min theo Ô — quét {1,2,3}

probe:
  wait_stats: false                  # observer log-only cho control-run E10b (§4.7) — 0 RNG,
                                     # 0 ghi state; fingerprint phải IDENTICAL khi bật
```

Không có tham số `smooth_alpha` — đã bỏ (§0b). Không có DemandSource interface mới:
`MarketStateProducer._demand` đã là điểm rẽ nhánh có tiền lệ.

### §2.2. Bảng wiring (file:line, ít xâm lấn nhất)

| File | Sửa gì |
| --- | --- |
| `src/gsm_sim/demand_estimator.py` | **MỚI** (~100 dòng): `RealizedDemandEstimator` — §3.4 |
| `src/gsm_sim/market_state.py:73-92` (`__init__`) | trong khối guard `hasattr(world, "cfg")` sẵn có (:79): đọc `market_demand_source` (default `"oracle"`, giá trị lạ ⇒ ValueError); nếu `"realized"`: (a) `market_demand_override` khác None ⇒ ValueError, (b) assert `bucket_min == 60` (phạm vi đo — §3.2), (c) dựng estimator từ `world.events` + scalars, gán `self.demand_source` = estimator; nếu `"oracle"`: `self.demand_source = None` (đường cũ). Stub test không có `cfg` ⇒ mọi default giữ nguyên |
| `market_state.py:94-99` (`_demand`) | đổi chữ ký private → `_demand(self, hour, idx)`; nhánh mới `if self.demand_source is not None: return self.demand_source.estimate(idx)` đặt TRƯỚC; hai nhánh cũ (override, oracle) giữ nguyên **từng ký tự** |
| `market_state.py:101-125` (`view`) | truyền `idx` vào `_demand`; khi estimator active (và CHỈ khi đó): log `demand_est` / `demand_est_cold` qua `self.world.log` trong nhánh cache-miss (một lần/bucket) — §3.6. Docstring thêm guard: cache là hợp đồng "một ảnh mỗi bucket"; ai xoá cache giữa bucket sẽ không đổi λ̂ (estimator chốt cửa sổ tại biên bucket — §3.4) nhưng sẽ chụp lại CUNG |
| `src/gsm_sim/world.py` | E10a: **KHÔNG sửa**. E10b: nhánh `wait` trong `_standby_planner` (§4.5) + helper `count_idle_wait` đặt cạnh `count_supply`; probe process khi `probe.wait_stats` (§4.7) |
| `src/gsm_sim/advice_bridge.py` | đọc 3 khoá positioning wait (validate `positioning_trigger ∈ {capacity, wait}`); sửa docstring stale :589 |
| `src/gsm_sim/parallel.py` | **KHÔNG sửa** — script thí nghiệm deep-copy cfg và set khoá advice trước khi chạy; cổng D-M3-10 (`aggregate_adherence`/`nominal_adherence`) tự áp |
| `configs/pilot_dongda.yaml` | thêm các khoá §2.1, default neutral |
| `scripts/measure_e10.py` | **MỚI** — §5.6 |
| `specs/simulation/e10-prereg-locked.json` | **MỚI** — file tiền-đăng-ký, commit TRƯỚC run đo đầu tiên (§6.1) |
| `tests/test_demand_estimator.py`, `tests/test_e10_wiring.py`, `tests/test_e10b_wait_trigger.py` | **MỚI** — §8 |

### §2.3. Chống nhiễm oracle — cơ chế CHỨNG NHẬN được (không chỉ mô tả)

Ba tầng, mỗi tầng một test đỏ-được:

1. **Estimator không thể chạm oracle**: constructor nhận **narrow reader** — tham chiếu list
   `world.events` + scalars (`start_min`, `bucket_min`, k, min_n). KHÔNG nhận `world`
   (`orders_sorted`/`demand_field` nằm ngoài tầm với theo cấu trúc). Property test **whitelist**:
   stub chỉ có `.events` (mọi attr khác raise `AttributeError`), estimator chạy trọn một ngày event
   tổng hợp trên stub đó.
2. **Producer ở realized mode không giữ tham chiếu oracle**: sau init, assert
   `producer.demand_source is not None` và test "poison đúng ref": thay `producer.demand_source`
   bằng estimator thật nhưng monkeypatch một spy trên `_demand` — chạy trọn ngày arm realized,
   assert `_demand` không trả về `world.demand_field[hour]` ở BẤT KỲ bucket nào (so identity + so
   giá trị). **KHÔNG poison `world.demand_field` toàn cục** — bản năng tài xế đọc nó hợp lệ tại
   `world.py:902`, poison toàn cục crash vì bản năng chứ không phải vì advisor (phản biện đã chứng
   minh test kiểu đó không bao giờ xanh được đúng cách).
3. **λ chỉ được làm THƯỚC CHẤM hậu-kiểm**: mọi phép so λ̂-vs-λ (bias §3.6, precision E10b §4.3)
   sống trong `scripts/measure_e10.py`, không import vào `demand_estimator.py` — namespace của
   `estimate()` không nhìn thấy `expected_demand_field`.

### §2.4. Chứng minh default bit-identical — HAI phạm vi, không phải một

Fingerprint per-actor (`scripts/probe_adherence_truth.py --fingerprint`, exact-repeat, ≥5 seed/cấu
hình) trên **cả hai** config, trước và sau merge:

- **(a) default-off** (`advice.enabled: false`) — bảo vệ arm A. Ở config này producer không được
  dựng (`world.py:156-161`) nên IDENTICAL gần như tautology — vẫn chạy vì rẻ, nhưng **không được
  trích làm bằng chứng chính**.
- **(b) advice ON + `positioning_overrides: wait_only` + `market_demand_source: oracle` +
  `positioning_trigger: capacity`** — bảo vệ **mẫu số Δ_oracle**. Đây là bằng chứng có giá trị duy
  nhất cho claim "đường cũ không đổi": nếu B_oracle trôi âm thầm thì "tỷ lệ sống sót" sai từ mẫu số
  (đúng mẫu DET-01/bẫy §5#5 BOOTSTRAP).

Ghi CẢ HAI vào UPDATE. Lưu ý: fingerprint là actor-based (segments+payout+trips+rest_min) — event
log mới (diag) không phá nó, nhưng ở mode oracle **không được log event mới nào** (test đếm kind).

---

## §3. E10a — `RealizedDemandEstimator`: nguồn cầu realized thay λ

### §3.1. Nguồn sự kiện — chốt cứng

Chỉ event **`pickup`** (`world.py:584`, cell = `order.pickup_cell` — đúng nơi phát sinh cầu, đã
kiểm). CẤM: `order_matched` (cell = ô tài xế — đo phân bố CUNG), `dropoff` (sai vị trí),
`order_expired`/`order_censored` (đơn không phục vụ — future leak + ngoài đời không có, bẫy PLAN #1).
Không join `order_id` → `world.orders` (không chạm cấu trúc chứa tương lai). Cuốc huỷ sau nhận
không bao giờ log `pickup` ⇒ tự loại. Pickup cells ⊆ core cells theo cách sinh.

### §3.2. Công thức (đơn vị đã pin: **pickups / bucket planner**)

Ký hiệu: `b = advice.bucket_min` (60 trong phạm vi đo — assert khi realized), bucket index
`idx = int(now // b)`, `N(c, i)` = số event `pickup` có `int(t_min // b) == i` ∧ `cell == c`,
`first_op_bucket = time.start_min // b` (= 5 với config hiện hành).

```
lo        = max(idx − k, first_op_bucket)
n_buckets = max(0, idx − lo)                      # số bucket VẬN HÀNH đã hoàn tất trong cửa sổ
total     = Σ_{i∈[lo,idx)} Σ_c N(c, i)

COLD  ⇔  idx ≤ first_op_bucket  ∨  n_buckets == 0  ∨  total < min_pickups
COLD  ⇒  λ̂ = {}                                   # advisor IM LẶNG — §3.3, KHÔNG fallback oracle
ngược lại:  λ̂(c) = Σ_{i∈[lo,idx)} N(c, i) / n_buckets   với mọi c có Σ N > 0
```

Vì sao từng vế:

- **Chia `n_buckets`, không chia `k`**: `build_market_state` hiểu `demand_by_cell` là cầu **trong
  một bucket** (`slots = demand // trips_per_driver_per_bucket`, `gsm_core/features/
  market_state.py:81`). Chia cứng k khi cửa sổ dính bucket trước giờ mở cửa sẽ kéo λ̂ xuống bằng
  các số 0 **cấu trúc**. Giờ mở cửa là tri thức sản phẩm công khai, không phải λ — clip về
  `first_op_bucket` hợp lệ, không phải oracle-lite (phản biện đã đồng ý).
- **`max(0, …)`**: planner tick từ `env.now = 0` (SimPy mặc định; `world.py:292` không delay đầu) ⇒
  idx 0..4 gọi estimator; không có nó thì `n_buckets` âm — bug ngủ được min_n che tình cờ.
- **Biên bucket**: event `t_min == idx·b` thuộc bucket `idx` ⇒ ngoài `[lo, idx)` ⇒ không rò
  cùng-thời-điểm. `log()` round 3 chữ số — jitter deterministic, giống mọi arm, vô hại (ghi nhãn).
- **Đơn vị nhất quán với mọi `bucket_min`** vì counts key theo bucket planner, nhưng diag so λ
  per-HOUR và mọi số đã đo đều ở b=60 ⇒ **assert `bucket_min == 60` khi `source=realized`** —
  fail-loud, gỡ khi có người re-derive cho b khác.
- **Độ lớn dự kiến** (ESTIMATE — in phân phối đếm thật 1 seed trước khi chốt dải min_n, §8 bước 5):
  1200 đơn/ngày trên ~85 ô lõi × 19h ⇒ ~0,6–1,2 pickup/ô/bucket, ô đỉnh 3–5. Với
  `trips_per_driver_per_bucket = 1.5`, ô cần λ̂ ≥ 1,5 mới có slot ⇒ đuôi dài ô lèo tèo tự rơi khỏi
  `ranked_cells`. **Hành vi dự kiến, không phải bug** — sparsity Poisson là cái giá của mất λ, đúng
  thứ E10 tồn tại để đo.

### §3.3. Cold-start — TƯỜNG MINH: advisor im lặng, có log, có mẫu số đúng

COLD ⇒ `estimate` trả `{}` ⇒ `build_market_state` cho `cells = {}` / `ranked_cells = []` ⇒
`_standby_planner` tự skip (`world.py:295` — mạch có sẵn, không code mới ở world). Mỗi lần như vậy
`view()` log `demand_est_cold` (actor_id=-1; detail: `idx`, `total`, `n_buckets`).

- **% bucket câm** — mẫu số định nghĩa TRƯỚC: chỉ tính trên bucket vận hành `idx > first_op_bucket`
  (bucket 0–4 đóng cửa cấu trúc ở CẢ HAI arm; bucket 5 cold cấu trúc vì `n_buckets=0` — báo riêng,
  không tính vào %). Không có định nghĩa này số bị thổi ~5×.
- **Vì sao im lặng thắng prior**: (a) prior `cell_weight` = chiều không gian noise-free của λ =
  oracle-lite (BÁC làm mặc định); (b) uniform prior ⇒ sd_ratio chỉ còn phân biệt bằng cung ⇒ khuyên
  "đi chỗ vắng tài xế" bất kể có khách; (c) im lặng khớp ĐA-07, sai số đẩy Δ **xuống** — hướng bảo
  thủ đúng cho kiểm một claim dương; (d) bucket câm hoàn toàn đầu tiên trùng `warmup_min` không
  tính metrics. NHƯNG các bucket **nghèo dữ liệu** 06–09h (ramp sáng: cửa sổ chứa giờ thấp hơn hẳn)
  KHÔNG trùng warmup — đây là một phần của bias B3 và của chính câu trả lời, KHÔNG được gọi là "giá
  cold-start nhỏ" (phản biện đã bác câu đó; xem thêm §5.4 decomposition theo giờ).
- Test chống fallback phải **đỏ được**: cold trả `{}` và assert **khác** `world.demand_field[hour]`
  — chứng minh đỏ bằng cách tạm nối fallback oracle chạy thử (bẫy §5#2).

### §3.4. Cấu trúc dữ liệu + determinism

```python
class RealizedDemandEstimator:
    """E10a — λ̂ từ cuốc ĐÃ ĐÓN (event kind='pickup'), cửa sổ cuốn k bucket planner.

    Narrow reader: CHỈ nhận tham chiếu list events (append-only, t không giảm theo SimPy)
    + scalars. KHÔNG nhận world (orders_sorted/demand_field là trace tương lai/λ).
    0 lần chạm RNG nào — deterministic từ realized data (bẫy PLAN #5 thoả không cần keyed hash).
    """
    def __init__(self, events: list, *, start_min: int, bucket_min: int,
                 window_buckets: int, min_pickups: int): ...
    def estimate(self, idx: int) -> dict[str, float]: ...
    # nội bộ: _ptr (con trỏ tăng dần vào events — O(1) amortized), _counts: {idx: {cell: n}}
```

`estimate(idx)` ingest tới `t_min < idx·b` rồi dừng (con trỏ nằm lại, lần sau tiếp) ⇒ λ̂ **không
phụ thuộc thời điểm gọi trong bucket** — cửa sổ `[lo, idx)` chỉ chứa bucket đã trọn, mọi event của
chúng đã log trước khi bucket `idx` bắt đầu (SimPy xử lý theo thời gian).

### §3.5. Vòng phản hồi nội sinh — chủ ý, có phanh

Arm bật ⇒ tài xế dịch chỗ ⇒ pickup dịch chỗ ⇒ λ̂ bucket sau đổi. Đây là **chủ ý** (chính rủi ro
herding cần đo). Phanh giữ nguyên (bẫy PLAN #4): `supply_incoming`/`pending_targets` trong
`sd_ratio`/`capacity_left` không đụng gì (`count_supply`, `world.py:357`).

### §3.6. Bias — khai đủ 5 loại, mỗi loại một phép đo hậu-kiểm ĐÃ ĐÓNG CÔNG THỨC

⚠ Toàn bộ diag dưới đây dùng λ làm **thước chấm hậu-kiểm** — đặc quyền của sim, ngoài đời không
tái lập được. Nó phục vụ *diễn giải* Δ, không phải tính năng. Nó sống trong `measure_e10.py bias`,
gọi ĐÚNG class estimator (một nguồn sự thật — chống recompute lệch T-046) trên event log của run.

| # | Bias | Cơ chế | Hướng | Đo bằng gì (công thức đóng) |
| --- | --- | --- | --- | --- |
| B1 | **Censoring không gian** (mầm herding-tệ-hơn) | λ̂(c) ≈ λ(c)·P(match\|c) — ô thiếu tài xế có đơn expire vô hình ⇒ under-count đúng nơi đáng khuyên tới; tự củng cố | kéo lời khuyên VỀ nơi đã có cung | per bucket idx: residual `e_c = share(N(c, idx)) − p(c)` (một-bucket, **disjoint** với cửa sổ `[idx−k, idx)` đã nuôi quyết định cung); `s_c` = share `(supply_now+incoming)(c)` tại idx; báo Pearson **và Spearman** corr(e, s) trên ô lõi. **Null baseline**: cùng đại lượng tính ở arm A và B_oracle (nơi cung không do λ̂ điều khiển). Wording bắt buộc: *"nhất quán với censoring"* — **CẤM chữ "xác nhận herding"** (corr đồng-cửa-sổ dương cả khi không censoring — confound cơ học đã bị phản biện chứng minh) |
| B2 | **Mức (level)** | pickup ⊂ order (served ~0,8; unserved+expired vô hình) ⇒ Σλ̂ < Σλ | `slots` co ⇒ ÍT đích, NHIỀU ứng viên (mọi ô λ̂ bé đều cap=0) — Δ trộn "tin kém" với "khối lượng khác" | `R_b = Σλ̂_b / Σλ(hour_b)` per bucket + **decomposition volume §5.4 bắt buộc** |
| B3 | **Trễ (lag)** | trailing window lag theo ramp giờ — sáng under, tối over | khuyên theo hình dạng cầu của k giờ trước | `TV(p̂_b, p(hour_b))` vs `TV(p̂_b, p̄(hour_b−k..hour_b−1))` per bucket (TV = ½Σ\|·\|
 trên share ô lõi) |
| B4 | **Nhiễu Poisson thưa** | 0–5 đếm/ô/bucket ⇒ jitter thứ hạng | `ranked_cells` nhảy giữa bucket | `rank_overlap10 = \|top10(λ̂_b) ∩ top10(λ)\| / 10` per bucket, tie-break DETERMINISTIC theo tên ô (đếm nguyên tie thường xuyên); thêm overlap(λ̂_b, λ̂_{b−1}) đo tự-ổn-định |
| B5 | **Attribution thời điểm ĐÓN** | pickup xảy ra tại `t_order + chờ-match + đường đón` (~3–12′) ⇒ khối lượng smear qua biên bucket; ngoài đời đơn đã phục vụ CÓ request timestamp ⇒ sim NGHÈO thông tin hơn thực tế | bảo thủ (đẩy Δ xuống) | ước lượng độ dịch trên 1 seed: phân phối `t_pickup − order.t_min` từ trace (script, không vào engine) |

**Nguồn dữ liệu cho B1 (supply per bucket)**: khi estimator active, event `demand_est` (log
một lần/bucket ở cache-miss của `view()`) mang detail
`{idx, total, n_buckets, n_cells, cells: {c: [supply_eff, lam_hat]}}`. Arm A / B_oracle **không có
event mới** (neutrality) ⇒ supply của chúng tái dựng hậu-kiểm từ segments; **test đối chiếu bắt
buộc**: ở arm realized, tái dựng hậu-kiểm == số đã log per bucket, exact — chứng minh đường tái dựng
đúng trước khi dùng nó cho A/B_oracle.

**Diagnostic nền cho §9-L2** (báo kèm mọi KQ-GIỮ): Spearman(share pickup World A per hour, share λ
per hour) — mức độ đội xe đã "giải mã" λ qua hành vi.

---

## §4. E10b — trigger positioning bằng THỜI GIAN CHỜ theo Ô

### §4.1. Dữ liệu — đính chính PLAN + ranh giới

PLAN §3b nói dùng `actor.idle_by_hour` — **sai nguồn**: nó keyed theo GIỜ, không có chiều Ô, tích
lũy cả ngày. Nguồn đúng và có sẵn: **`idle_streak_min`** (`entities.py:53`) — +2,0 mỗi tick WAIT
(`world.py:885`), reset khi **được CHÀO** kể cả sau đó decline (`world.py:499`), reset sau relocate
(`world.py:881`).

- **READ-ONLY tuyệt đối**: biến này đang nuôi bản năng sốt ruột (`behavior.py:171`). Mọi ý "sửa
  semantics streak cho sạch" đổi `choose_idle_action` ⇒ phá behavior-neutral ⇒ CẤM trong cycle này.
- **Ranh giới realized của E10b RỘNG HƠN E10a, có nhãn**: streak reset bởi OFFER ⇒ W-statistic nhúng
  thông tin cầu *offered-nhưng-không-phục-vụ*. Hợp lệ (platform tự phát offer nên quan sát được
  ngoài đời — không phải oracle leak, không phải future leak) nhưng **khác** biên "chỉ pickup" của
  E10a — ghi rõ để người đọc T-047 không đánh đồng hai biên.
- ASSUMPTION có nhãn: streak KHÔNG reset khi quay lại từ REST/CHARGING — returner mang streak cũ
  (bằng chứng stale) có thể đẩy median qua T. Không sửa được (ràng buộc trên). `idle_streak_min`
  cũng không nằm trong `_DAILY_RESET_*` — vô hại cho E10 một-ngày, là bẫy nạp sẵn cho `D-M3-04`
  (multiday) ⇒ ghi `tracking/DEFERRED.md` ngay trong cycle này.

### §4.2. Định nghĩa W(c) và ngưỡng T — neo ĐÃ SỬA theo phản biện

Tại thời điểm planner thức (`world.py:292-294`, chu kỳ b=60′), CHỈ khi `positioning_trigger == "wait"`:

```
W(c)      = median_interpolated({a.idle_streak_min : a IDLE, a.cell == c})   # numpy, deterministic
n_idle(c) = |tập trên|
fired     = {c : n_idle(c) ≥ n_min ∧ W(c) > T}
```

Mẫu = **MỌI** actor IDLE trong ô (platform quan sát mọi tài xế; coverage chỉ quyết định ai được
NHẬN lời khuyên — giữ `advice.covers(a)` ở tầng ứng viên như cũ, `world.py:303`).

**Ngưỡng tuyệt đối, không percentile** (giữ nguyên ba lý do của thiết kế: percentile luôn-bắn kể cả
khi cả bản đồ khoẻ — ngược ĐA-07; mẫu vài chục ô có idle ⇒ nhiễu chồng nhiễu; không giải thích được
cho tài xế). **Neo dẫn xuất — bản ĐÃ SỬA hai lỗi phản biện bắt**:

- Hoà vốn `trips_per_hour_est = 1.5` ⇒ chu kỳ 40′/cuốc **gồm cả phục vụ** (~15–20′). Streak chỉ
  tích trong tick WAIT ⇒ median streak hoà-vốn ≈ (40 − service)·ln2 ≈ **14–18′** (không phải 27,7′
  — bản gốc nhầm CYCLE với WAIT).
- Đồng hồ thứ hai đang censor chính biến đo: config pilot `idle_impatience_step_min: 20` ×
  `max_steps: 2` (`pilot_dongda.yaml:203-204`) ⇒ give_up từ streak 40′, p_move 0,9/tick 2′
  (`behavior.py:168-197`) ⇒ phân phối streak **cụt ~40–44′**.

⇒ **T = 30′ headline, khoá a-priori**: ≈ 2× median hoà-vốn, dưới trần cụt. Lưới sweep
**{15, 20, 25, 30, 35}**; **45 và 60 bị LOẠI TRƯỚC vì chết cấu trúc** — đăng ký tường minh để không
ai đọc "Δ(T=60)=0" thành "robust với T". Control-run §4.7 xác nhận firing-rate từng T trước khi
chạy arm; T nào firing ≈ 0 bị loại kèm lý do.

### §4.3. Kỷ luật mẫu số + cổng cá nhân

- **n_min = 2 headline** (đổi so với thiết kế gốc n_min=1, theo hai phản biện định lượng: với n=1,
  "median theo Ô" LÀ chờ của đúng một người — luật per-driver mà PLAN §3b cấm, chiếm đa số lần bắn;
  P(bắn oan mỗi wake | ô hoà vốn, n=1) ≈ e^(−30/15..20) ≈ 0,14–0,22, ~12 wake/ngày ⇒ 1–2 phát kéo
  oan/ngày/người). Biến thể n_min ∈ {1, 3} báo kèm; nếu kết luận đổi dấu giữa 1↔2 thì đó là
  **finding phải báo**, không phải knob.
- **Fallback khối (pre-registered)**: nếu control-run cho thấy < 20% idle-phút nằm trong ô có ≥2
  IDLE ⇒ gộp theo khối `grid_disk(c, 1)` thay ô đơn (vẫn "gộp theo Ô/khối", không per-driver).
  Hằng 20% và bán kính 1 là quy ước khai trước.
- **Cổng cá nhân — vá lỗ "kéo người vừa tới"**: ứng viên = (ô ∈ fired) **∧ streak cá nhân ≥ T**
  (tái dùng T, không tham số mới). Không có nó, ô fire {50′, 40′, 5′} kéo cả người 5′ vừa tới —
  mâu thuẫn chính lời giải thích "anh đã không được nuôi 30′", và tự phá cơ chế hãm (người mới đến
  là mẫu kéo median XUỐNG).
- **Đo bắn-oan trực tiếp (λ chấm điểm hậu-kiểm — hợp lệ)**: tỷ lệ ô fire có pickup trong bucket kế;
  precision/recall của `fired` so với tập "ô thật sự dưới hoà vốn theo λ" trên control-run.

### §4.4. THAY `capacity_left` ở tầng nguồn + ZONE-VETO ở tầng đích (định nghĩa arm, không phải tuỳ chọn)

**THAY** (không AND): trong thế giới không-oracle, chờ realized là tín hiệu tốt nhất hiện có về cân
bằng S/D tại chỗ; AND với `capacity_left` tính từ ước lượng E10a trailing là trói tín hiệu tốt vào
tín hiệu kém hơn — và chặn đúng cú sửa sai chủ lực (ô ước-lượng-stale-cao nhưng đã chết: chờ leo ⇒
kéo đi là ĐÚNG, cap_left>0 sẽ cấm).

**Nhưng THAY mở hai lỗ mà `pref`-guard KHÔNG đóng được** (phản biện chứng minh từ
`capacity_alloc.py:50`: cost zone ≠ target = `pen + 10.0`, không phải LARGE ⇒ Hungarian **stagger**
ứng viên sang bất kỳ zone còn slot, kể cả ô đang đứng):

1. **Tự-gán qua stagger**: own cell ∈ zones (ước lượng stale giữ cap>0) ⇒ khi pref đầy, overflow rơi
   về own cell ⇒ coin rút (`world.py:353`), `decided` phình, rồi pop im lặng (`world.py:781-785`) ⇒
   adherence đo hụt hệ thống ⇒ cổng D-M3-10 TREO arm vì lý do cấu trúc. Test kiểu "pref ≠ own" sẽ
   XANH trong khi lỗi sống — đúng bẫy §5#2.
2. **Nguồn-đích chồng nhau trong cùng batch**: ô X vừa fire (rút người ra) vừa nằm trong ranked
   (đưa người khác vào) ⇒ churn chéo hai actor mà `pingpong_rate` per-actor mù.

**Vá bằng MỘT luật — zone-veto, thuộc ĐỊNH NGHĨA trigger (pre-registered)**:

> Ô ∈ `fired` bị loại khỏi tập đích của batch đó: `ranked_eff = [c for c in ranked if c not in fired]`;
> zones dựng từ `ranked_eff`.

Hệ quả: ứng viên chỉ sinh từ ô fired ⇒ own cell ∉ zones ⇒ Hungarian **không thể** gán về chỗ đứng
(đóng lỗ 1); ô fired không nhận người vào (đóng lỗ 2). Deterministic, tái dùng `wait_stats`, không
tham số mới. **Cái giá khai thật**: arm wait vs arm capacity không còn "chỉ khác đúng MỘT thứ" —
wait-stat chạm cả tầng đích. Chấp nhận như một phần định nghĩa arm; diagnostic
`n_assigned_into_fired_cells` (kỳ vọng = 0, assert runtime + test) và arm chẩn đoán
`B_wait_oracle` (§5.1) gánh phần attribution.

Nếu `ranked_eff` rỗng hoặc ứng viên không còn đích: **không làm ứng viên — không rút coin, không
đếm decided** (test riêng: `decided` không tăng, coin không cháy).

### §4.5. Sketch nhánh planner (giữ cadence check ở CẢ HAI nhánh — phản biện bắt sketch cũ làm rơi)

```python
# _standby_planner, sau khi có view/ranked/cap_left:
wait_mode = (self.advice.positioning_trigger == "wait")
if wait_mode:
    wait_stats = count_idle_wait(acts)          # {cell: (n_idle, median_min)} — tính MỘT lần/bucket
    fired = {c for c, (n, med) in wait_stats.items()
             if n >= self.advice.positioning_wait_min_idle
             and med > self.advice.positioning_wait_threshold_min}
    ranked_eff = [c for c in ranked if c not in fired]      # zone-veto §4.4
else:
    fired, ranked_eff = set(), ranked
if not ranked_eff:
    yield self.env.timeout(b); continue

for a in self.actors.values():
    if a.state != ActorState.IDLE or not self.advice.covers(a):  continue
    if a.actor_id in self.standby_plan:                          continue
    if wait_mode:
        if a.cell not in fired:                                  continue
        if a.idle_streak_min < wait_T:                           continue   # cổng cá nhân §4.3
    else:
        if cap_left.get(a.cell, 0) > 0:                          continue   # đường cũ, nguyên văn
    if (self.advice.cadence_counts_positioning                              # giữ ở CẢ HAI nhánh
            and not self.advice.cadence_allows(a, "positioning", now)):     continue
    pref = min(ranked_eff, key=lambda c: (cell_distance_km(self.grid, a.cell, c), c))
    ...
zones = [{"zone": c, "capacity": cap_left[c]} for c in ranked_eff]
# sau solve: assert all(al["assigned_target"] not in fired for al in sol["allocations"])
```

`count_idle_wait(actors) -> dict[cell, (n, median)]` — helper thuần cạnh `count_supply` trong
`market_state.py`, unit-test độc lập. **KHÔNG** đưa wait-stat vào `build_market_state` của
`gsm_core` ở v1 (schema versioned 1.0.0; positioning bị D-004 cấm ở SẢN PHẨM — đây là công cụ thí
nghiệm SIM-only; E10b thắng thì mở cycle riêng bump 1.1.0).

### §4.6. Vòng phản hồi + execution-gate — cơ chế hãm, luật hành động, và confound khai thật

Bốn cơ chế hãm dao động THEO THỜI GIAN có thật trong code (kiểm từng dòng): (1) trần đích +
`supply_incoming` trừ ngay lúc gán (`world.py:357`, `count_supply:59-61`); (2) người vừa tới reset
streak = 0 ⇒ kéo median ô đích XUỐNG (`world.py:881`); (3) ngưỡng-là-tích-phân: median > 30′ đòi nửa
số người chờ 30′ liên tục, cadence 60′ ⇒ không tồn tại dao động nhanh hơn chu kỳ tích phân; (4) cạnh
quay-về tự tắt bởi chính E10a (A bị rút người ⇒ ít pickup tại A ⇒ ước lượng A suy giảm cấu trúc ⇒ A
rơi khỏi ranked). Chiều KHÔNG GIAN cùng-batch do zone-veto §4.4 đóng.

**Luật hành động tiền-đăng-ký (không phải knob chỉnh sau khi nhìn Δ):**
`pingpong_rate` = tỷ lệ chuỗi A→B→A của cùng actor trong ≤ 2 bucket, đếm trên **MỌI** relocate của
actor đã được standby-gán trong ngày (event `relocate` mang TARGET tại vị trí cell —
`world.py:882`; ô NGUỒN tái dựng từ event liền trước của cùng actor — cách dựng này là một phần của
tiền-đăng-ký). Ngưỡng 10% và cửa sổ 2-bucket là **quy ước khai trước**; vượt ⇒ thêm cooldown 1
bucket theo ô-nguồn và đo lại. Km-rỗng standby (đã có) là thước liên tục đọc kèm.

**Confound execution-gate — khai thật, không vá trong v1** (§9-L4): quần thể `W > 30′` chính là
quần thể impatience bậc ≥1 của bản năng; `wait_only` chỉ áp khi bản năng ra WAIT
(`world.py:786-787`), `standby_plan` không TTL ⇒ ca "coin-true nhưng actor tự relocate theo bản
năng rồi mãi sau mới thực thi plan cũ hai chặng, pending_targets treo (phantom incoming)" xảy ra
theo cấu trúc, tần suất arm wait > arm capacity. Mọi TTL/cleanup đều đổi hành vi cần đo riêng ⇒ v1
không đổi cơ chế, mà **pre-register bộ diagnostic đọc CÙNG Δ cho cả arm capacity lẫn wait**: lag
gán→follow, số relocate bản năng xen giữa, plan chưa áp lúc cuối ngày, km hai-chặng.

### §4.7. Control-run (probe) — bắt buộc TRƯỚC khi khoá sweep, chạy trên World A

Cờ `probe.wait_stats: true` đăng ký một observer process (log-only, chu kỳ 60′): per-cell
`(n_idle, median_streak)` + histogram streak per-actor + tỷ lệ tick instinct==WAIT trong nhóm
ô-sẽ-fire. **0 RNG, 0 ghi state**; fingerprint per-actor bật/tắt cờ phải IDENTICAL (test).
Chạy trên seeds tuning 5100–5129 (World A). Đầu ra quyết định (đều là quyết định TRƯỚC-Δ, hợp lệ):

- phân phối W(c), firing-rate theo từng T của lưới ⇒ loại T chết, xác nhận T=30 sống;
- % idle-phút trong ô ≥2 IDLE ⇒ kích hoạt fallback khối hay không (§4.3);
- WAIT-share trong ô fire ⇒ nếu quá thấp, E10b "câm theo cấu trúc" ⇒ STOP-3 wording;
- precision/recall trigger vs λ (thước chấm hậu-kiểm).

Vì sao cần instrumentation mới: `idle_streak_min` không nằm trong bất kỳ event nào (grep xác nhận)
— "tái dựng từ timeline" sẽ là đường recompute thứ hai dễ sai (streak chỉ tích trong nhánh WAIT).

---

## §5. Phép đo: các arm, seeds, ước lượng ghép cặp, chỉ tiêu, cổng adherence

### §5.1. Các arm (mọi arm B: `channels = CHANNEL_LADDER["positioning"]`, `coverage="all"`, `actor_id=None`)

| Arm | Nguồn cầu cho ranked/capacity | Trigger | Trả lời gì | n |
| --- | --- | --- | --- | --- |
| `A` | — (advice off) | — | baseline ghép cặp | 100 |
| `B_oracle` | λ config (hiện hành) | capacity | tái lập trần +6.016đ (STOP-1) | 100 |
| `B_hist` | `market_demand_override` = trung bình pickups per (hour, cell) của **30 run World A seeds tuning** (5100–5129) | capacity | **điều kiện triển khai thật**: advisor có lịch sử realized nhiều-ngày, không λ — vẫn mang B1/B2, không mang B3/B4 | 100 |
| `B_real` | λ̂ cửa sổ cuốn k\* (E10a) | capacity | **cận dưới zero-history**: mất λ VÀ thức dậy mù mỗi sáng | 100 |
| `B_wait` | λ̂ cửa sổ cuốn k\* (= B_real) | wait (T=30, n_min=2, veto) | E10b: trigger đo-chờ có cứu lại phần nào không | 100 |
| `B_wait_oracle` (chẩn đoán) | λ config | wait | tách đóng góp trigger khỏi nguồn cầu — **chạy LUÔN**, không chờ "Δ khó giải thích" (cửa hậu-nghiệm đã bị phản biện cấm) | 30 |

**Vì sao phải có `B_hist`** (vá lỗ GIẾT-CHẾT của phản biện phép đo): sim một ngày, estimator reset
mỗi run ⇒ arm `B_real` trả lời câu *"mất λ VÀ mất trí nhớ qua đêm"* — khắc nghiệt hơn câu E10 hỏi.
Ngoài đời platform có hàng tháng realized trips. Nếu chỉ có B_real và nó sụp, artifact không phân
biệt được "giá trị đến từ oracle" với "giá trị chết vì zero-history — thứ ngoài đời không xảy ra";
báo "sụp khi mất λ" khi thật ra là "sụp khi mất lịch sử" là báo sai con số quan trọng nhất, theo cả
hai chiều. `B_hist` dùng đúng hook `market_demand_override` sẵn có (docstring của chính nó:
*"aggregate của RUN KHÁC — cross-run learning, không phải future-leak"*, `market_state.py:86`) —
**không code engine mới**. Prior hist deterministic, tính một lần, lưu `41-e10-hist-prior.json`.
⚠ Cấm tuyệt đối dùng World A **cùng seed** làm lịch sử — cùng trace = biết trước đơn hôm nay =
future leak xuyên thế giới. Blend hist + cửa sổ trong-ngày: DEFERRED (thêm trục thiết kế).

### §5.2. Vận hành — các bẫy đã ghi tên

- **Coverage pin cứng**: `_cfg_with` mặc định `coverage="single"` (`parallel.py:74`); truyền
  `actor_id=None` cùng nó ⇒ không ai được phủ ⇒ đo cái tắt của chính mình (BOOTSTRAP §5 bẫy vận
  hành). Script set `coverage="all"` cho MỌI arm B và **assert fail-loud**: arm capacity —
  `by_channel.positioning.decided > 0` từng seed; arm wait — decided pooled > 0 và báo số seed
  decided=0 (wait fire thưa là hành vi dự kiến).
- **World A chạy MỘT lần/seed**, cache dùng chung mọi arm (mẫu `run_ladder`, `parallel.py:301-315`).
- **World A cũng bị audit adherence** (DET-01: arm đối chứng phải ĐO, không giả định sạch):
  `adherence_audit(rA)` + assert `by_channel` rỗng.
- Env phải neutral: assert scenario `dry_weekday` / factor 1.0 (nếu chạy E10 trên mưa/event thì
  `expected_demand_field` không nhân `env.demand_factor` (`demand.py:86` vs `:135-137`) — "oracle"
  hết là oracle, mọi diag đổi nghĩa).
- 4 kênh còn lại khoá `false` tường minh trong config arm (nếu ai bật `shift_plan`/`rest_window`,
  advisor nhận `demand_hint` = λ×nhiễu của tài xế qua `consult`/`should_defer_rest` —
  `world.py:737, 811` — một đường λ gián tiếp vào solver).

### §5.3. Seeds + thống kê

- **Đo chính: 5000–5099** (100, tươi; đã dùng tới nay: 1000–1002, 2000, 3160–3189, 4000–4099,
  4200–4299, 4300–4399). **Tuning/probe/preflight: 5100–5129** (30, disjoint). Sensitivity Δ-chiều:
  5000–5029 (World A cache lại).
- **Ước lượng ghép cặp**: metric chính `net_mean_all`; `Δ_X(s) = B_X(s) − A(s)`;
  arm-vs-arm `D(s) = B_X(s) − B_Y(s)` cùng seed (A triệt tiêu); bootstrap CI 5000 resample seed
  12345 (`bootstrap_ci` hiện có); **hiệu-của-hiệu** per seed (bài học UPDATE-078); n=100 theo
  `MIN_SEEDS_FOR_VARIANT_COMPARISON` (`parallel.py:254`).
- **Retention** `R = mean(Δ_X)/mean(Δ_oracle)` là **mô tả phụ** (bootstrap tỷ số nổ đuôi khi mẫu số
  resample gần 0); căn cứ phân lớp là CI của HIỆU (§6.3). Mọi CI chứa 0 phải kèm `MDE = 1,96×SE` để
  tách "không phát hiện được" khỏi "bằng 0".
- **Decomposition theo GIỜ tiền-đăng-ký** (vá lỗ cold-start trộn vào Δ): báo Δ per-hour-of-day cho
  từng arm — tách "ít giờ hoạt động đầu ngày" khỏi "thông tin kém hơn".

### §5.4. Decomposition VOLUME (bắt buộc — B2 làm arm realized ít đích/nhiều ứng viên một cách cơ học)

Per arm per seed, từ event `standby_planner`/`standby_alloc` + coin: `n_candidates`, `n_assigned`,
`n_coin_true`, `n_executed` (event `standby_followed`), % bucket câm (định nghĩa §3.3), và với arm
wait: `n_fired_cells`, `n_assigned_into_fired_cells` (kỳ vọng 0). Không có bảng này, mechanism
report sẽ kể "tin kém hơn" và "khối lượng can thiệp khác" thành một chuyện.

### §5.5. Cổng adherence D-M3-10 — bước TIỀN-FLIGHT bắt buộc (trước MỌI run E10)

Cổng thống kê z Poisson-binomial (\|z\|>4, null từ `nominal_adherence` của chính run —
`parallel.py:328-390`) **chưa từng chạy trên kênh positioning ở n gộp lớn**. Vấn đề cấu trúc đã
nhìn thấy trong code: mẫu số = người ĐƯỢC GÁN, tử số = event `standby_followed` = coin-true **∧ thi
hành được**; các ca coin-true-không-thành-followed là code path thật (pop im lặng `world.py:781-785`;
bận tới hết ca; instinct ≠ WAIT). Số 1-seed trong comment `world.py:335-338`: 86 gán / coin 42 /
followed 36 ⇒ gap ~7đp dưới null coin. Per-seed z ≈ 1,3 (test hiện tại xanh); **gộp 100 seed
(n≈8.600) z ước ≈ 13 ⇒ TREO cả ba arm, kể cả oracle** — E10 về tay trắng, hoặc tệ hơn: cổng bị nới
giữa trận (mẫu D-R20).

**Giao thức tiền-flight (pre-registered cả hai nhánh):**

1. Chạy `aggregate_adherence` gộp trên arm B_oracle hiện hành, 30 seed (5100–5129). Đo z positioning
   thật (độ lớn 7đp là số 1-seed — cơ chế chắc, độ lớn PHẢI tự đo, bẫy §5#7).
2. **Nếu \|z\| ≤ 4**: giữ nguyên thước, ghi số vào prereg, đi tiếp.
3. **Nếu \|z\| > 4 (dự đoán đăng ký trước: SẼ bắn)**: **sửa THƯỚC, không nới ngưỡng** — mini-cycle
   riêng (điểm chờ Cường duyệt #2):
   - `_standby_planner` ghi thêm `coin_follow_ids` vào detail `standby_alloc` (kết quả
     `standby_follow_draw` đã có sẵn tại đúng dòng gán);
   - `projections.py::_offer_events` sinh thêm event `followed` cho coin-true ids (cùng
     decision_id, reason `"coin"`); gỡ mapping `standby_followed → followed` khỏi `_TERMINAL_ONLY`
     (:186-188) — `standby_followed` trở thành marker THI HÀNH thuần;
   - `execution_rate = executed / coin_true` thành chỉ tiêu RIÊNG trong `adherence_audit` — bản
     thân nó là một finding đáng báo (≈0,86 theo comment 1-seed — đo lại);
   - test đỏ-được: run mà coin-true không bao giờ thi hành ⇒ thước cũ cho adherence 0, thước mới
     cho ≈ nominal; và test bơm adherence lệch 0,10 ở n=500 qua ĐÚNG wrapper của `measure_e10.py`
     ⇒ TREO (chống lỗi adapter quên truyền `by_channel_archetype` — cổng im lặng vĩnh viễn là
     nguyên văn bẫy §5#4);
   - sau vá, cổng D-M3-10 positioning trở thành cổng **toàn vẹn phép đo** (coin/logging), đúng vai
     D-M3-10; nó không còn đo execution — execution nằm ở chỉ tiêu riêng. Composition shift của arm
     wait (chọn người sốt ruột) không làm lệch cổng vì null dùng `p_i` per-archetype của đúng tập
     decided.
4. UPDATE riêng cho mini-cycle; mọi artifact E10 ghi `ruler_fix_applied: true/false`.

### §5.6. `scripts/measure_e10.py` — khung lệnh và thứ tự STOP (đã sửa các lỗi skeleton phản biện bắt)

```
uv run python scripts/measure_e10.py probe        # §4.7 + phân phối đếm pickup (chốt dải min_n)
uv run python scripts/measure_e10.py preflight    # §5.5 — cổng gộp trên B_oracle 30 seed
uv run python scripts/measure_e10.py tune         # §6.2 — k* shadow trên World A tuning seeds
uv run python scripts/measure_e10.py histprior    # dựng 41-e10-hist-prior.json từ World A tuning
uv run python scripts/measure_e10.py worldA       # A ×100, cache
uv run python scripts/measure_e10.py arm <oracle|hist|real|wait|waitoracle>
uv run python scripts/measure_e10.py diff         # STOP theo thứ tự + phân lớp §6.3
uv run python scripts/measure_e10.py bias <arm>   # §3.6
```

Quy tắc thi công script (mỗi cái là một lỗi skeleton đã bị phản biện bắt): PREREG **lazy-load**
theo lệnh (không đọc ở import — gà–trứng với `probe`/`tune`); guardrail truy cập **cứng** `g[k]`
(KeyError nổ — `if k in g` là hidden fallback, vết `supply_cell_hhi` 0.0 âm thầm UPDATE-075);
`GUARD_KEYS` gồm ĐỦ 4 tầng ĐA-08 **kể cả `starved_hours_n`**; JSON seed key là string — normalize;
`worldA` không có `verdict` (scope test cho đúng); thứ tự STOP trong `diff`:

1. verdict(B_oracle) TREO ⇒ **dừng tất cả** — thước hỏng, không có mẫu số nào đáng tin;
2. STOP-1 tái lập (§6.4);
3. verdict từng arm còn lại — TREO ⇒ arm đó chỉ báo verdict + flags, không báo Δ (không KeyError
   dây chuyền: arm bị loại khỏi dict trước khi tính diff);
4. phân lớp §6.3 cho từng arm sống.

Artifact: `research/audit/2026-07-27-current-state/41-e10-*.json` — mỗi arm mang `overrides`,
`seeds`, `verdict`, per-seed rows, volume §5.4, % câm, `ruler_fix_applied`.

---

## §6. 🔒 CỔNG TIỀN-ĐĂNG-KÝ — khoá TRƯỚC khi đo; commit file này + `e10-prereg-locked.json` trước run đầu tiên

### §6.1. File khoá

`specs/simulation/e10-prereg-locked.json`, sinh sau `probe`/`preflight`/`tune`, commit TRƯỚC
`worldA`:

```json
{
  "k_star": null,               "k_criterion": "mae_one_step_realized_v1",
  "k_grid": [1, 2, 3, 4, 6],
  "T_headline": 30.0,           "T_grid": [15, 20, 25, 30, 35],
  "T_excluded_structural": [45, 60],
  "n_min_headline": 2,          "n_min_grid": [1, 2, 3],
  "min_pickups": 5,             "min_pickups_grid": [1, 3, 5, 10],
  "block_fallback": {"active": null, "rule": "idle_share_ge2 < 0.20 => grid_disk r=1"},
  "seeds_measure": "5000-5099", "seeds_tuning": "5100-5129",
  "preflight_z_positioning": null, "ruler_fix_applied": null,
  "expected_registered": "§6.5"
}
```

**CẤM sau khi commit**: đổi k/T/n_min/min_pickups sau khi nhìn bất kỳ Δ nào; nới ngưỡng z sau khi
thấy verdict; đổi metric chính; dời T headline hậu-nghiệm.

### §6.2. Luật chọn k\* — realized-only, đóng công thức, shadow (vá NẶNG-1: 0 oracle trong hyperparameter)

**PROCEDURE là thứ được đăng ký, không phải giá trị** (headline = k\* từ procedure; `3` trong config
chỉ là placeholder — xoá mâu thuẫn "default 3 vs chọn k\*" của thiết kế gốc):

- Trên MỖI World A run của seeds tuning (5100–5129) — **shadow mode**: estimator dựng offline từ
  event log của run (không advice ⇒ không feedback loop; cùng class = một nguồn sự thật);
- với mỗi k ∈ {1,2,3,4,6}, mỗi bucket vận hành `idx > first_op_bucket` có `n_buckets ≥ 1`
  (đánh giá cửa sổ per se ⇒ dùng `min_pickups=1` khi tuning):
  `MAE_s(k, idx) = Σ_{c ∈ core_cells} | λ̂_k(c, idx) − N(c, idx) |` (λ̂ = 0 cho ô không quan sát);
- `score(k) = mean_{s, idx} MAE_s(k, idx)`; **k\* = argmin**, tie ⇒ k nhỏ hơn.
- MAE trên COUNTS là tiêu chí nhạy MỨC (thứ `slots` tiêu thụ) — trả lời luôn phản biện "tv/rank mù
  level". Poisson deviance báo kèm mô tả (không quyết định). **Tuyệt đối chưa nhìn Δ nào ở bước
  này; λ không xuất hiện trong tiêu chí.** Ngoài đời phép chọn này tái lập được nguyên văn trên
  held-out realized data — đúng nghĩa deployable.
- Diag λ-based (TV/rank-overlap vs λ) của từng k: báo hậu-kiểm mô tả. Giới hạn khai thật §9-L7:
  tuning ở shadow-A ≠ equilibrium dưới treatment.

### §6.3. Phát biểu kết luận — 4 lớp loại trừ nhau, null tự nhiên, không mốc % tự đặt

Cho mỗi arm X ∈ {hist, real, wait} (CI95 bootstrap ghép cặp, n=100):

| Lớp | Điều kiện | Câu ĐƯỢC PHÉP nói |
| --- | --- | --- |
| **KQ-GIỮ** | CI(Δ_X) > 0 ∧ CI(Δ_X − Δ_oracle) ∋ 0 | "Mất λ không gây suy giảm phát hiện được (MDE=…)" — **bắt buộc kèm caveat L1+L2 nguyên văn**: thế giới rank-tĩnh + đội xe đã mang λ ⇒ phát biểu YẾU về ngoài đời |
| **KQ-CÒN-MỘT-PHẦN** | CI(Δ_X) > 0 ∧ CI(Δ_X − Δ_oracle) < 0 | "Còn R=…% [CI mô tả] của +6.016đ" |
| **KQ-SỤP** | CI(Δ_X) ∋ 0 | "Không còn bằng chứng giá trị khi advisor mất λ (MDE=…)" — nếu xảy ra ở B_hist thì đây là **kết quả quan trọng nhất dự án từng đo, báo nguyên văn**; phát biểu MẠNH (sụp cả trong thế giới rank-tĩnh dễ hơn đời thực ⇒ ngoài đời chỉ tệ hơn) |
| **KQ-ÂM** | CI(Δ_X) < 0 | "Advisor thiếu λ gây HẠI — positioning giữ OFF ở chế độ realized" — kết quả hợp lệ, không phải bug (§1) |

Đọc theo cặp: `B_hist` trả lời câu E10 ở **điều kiện triển khai thật**; `B_real` là **cận dưới
zero-history**; `B_wait − B_real` (cùng seed) đọc giá trị trigger **× execution-gate** (không phải
trigger thuần — §9-L4); `B_wait_oracle` (n=30, chỉ CHIỀU) tách trigger khỏi nguồn cầu.

### §6.4. STOP rules + cổng phụ (kiểm theo thứ tự, dừng là dừng)

- **STOP-0a — neutrality**: fingerprint §2.4 không IDENTICAL ⇒ BLOCKED, không đo gì.
- **STOP-0b — tiền-flight thước** (§5.5): \|z\|>4 trên B_oracle ⇒ mini-cycle sửa thước trước.
- **STOP-1 — tái lập trần**: CI(Δ_oracle, n=100, seeds 5000–5099) ∋ 0 ⇒ dừng E10. **Kèm hai bước
  chống kết-luận-nhầm đã pre-register**: (a) tính power TRƯỚC từ per-seed rows của artifact
  UPDATE-087 (mở artifact gốc — nhiều artifact khác TREO, memory đã dặn); nếu CI ∋ 0 nhưng CI ∋
  +6.016 và MDE > 6.016 ⇒ báo *"tái lập underpowered"*, không phải *"không tái lập"*; (b) chạy lại
  đúng bộ seed của UPDATE-087 trên code hiện tại để tách "seed tươi" khỏi "code/config drift".
  CI(Δ_oracle) < 0 là **kết quả đảo chiều** — báo đúng tên, không gộp vào "không tái lập".
- **STOP-2 — verdict per-arm** (thứ tự trong `diff` ở §5.6).
- **STOP-3 — E10b câm cấu trúc**: probe §4.7 cho firing-rate ≈ 0 ở T=30 (kể cả sau fallback khối)
  hoặc WAIT-share quá thấp ⇒ B_wait báo "câm theo cấu trúc", không báo Δ.

**Cổng phụ (báo kèm, không đổi lớp):**

- **G-GUARD**: tầng hệ thống ĐA-08 nào suy giảm SIG (expired_n↑, wait_median↑, total_payout↓,
  gini↑, station/supply hhi↑, starved_hours↑) ⇒ arm gắn nhãn "đạt cá nhân, hại hệ thống".
- **G-HERD** (giả thuyết đăng ký trước): kỳ vọng `supply_cell_hhi(B_real) ≥ B_oracle` và B1-corr
  của B_real vượt null baseline. Thoả cả hai + expired_n xấu đi ⇒ ghi *"nhất quán với cơ chế
  censoring/herding"* (cấm chữ "xác nhận" — §3.6).
- **G-SENS**: lớp kết luận giữ CHIỀU ở ≥ 2/3 giá trị k (và T cho B_wait) trên n=30 seeds 5000–5029,
  nhãn `n_insufficient` to, **cấm trích độ lớn** (Δ variant-vs-variant cần n≈105 —
  `parallel.py:246-254`; ở n=30 sign-flip là nhiễu dự kiến). Đảo chiều theo k ⇒ báo "kết luận nhạy
  với k", cấm chọn k đẹp.

### §6.5. Kỳ vọng trung thực — ghi TRƯỚC khi đo (để không ai kể lại chuyện cho khớp số)

1. `min_pickups` **trơ** tại config này (giờ thấp nhất ~15–22 pickup realized > max sweep 10; cổng
   chỉ cắn đúng bucket 5 — đằng nào cũng cold vì n_buckets=0). Sweep identical từng bit ⇒ báo
   *"tham số trơ tại config hiện hành"*, KHÔNG báo "robust".
2. G-SENS theo k **phẳng** — hệ quả thế giới rank-tĩnh (§9-L1), không phải bằng chứng robust.
3. `B_hist` gần `B_oracle` (rank tĩnh ⇒ 30 ngày lịch sử học gần trọn bản đồ, chỉ thiếu phần
   censoring B1/B2); `B_real` thấp hơn rõ (level deflation + sparsity + lag); `B_wait − B_real`
   nhỏ hoặc âm (execution-gate ăn trước — PLAN §8 đã cảnh báo họ cơ chế này).
4. Tiền-flight §5.5 **sẽ bắn** trên B_oracle (gap coin-vs-execution).
5. Kết quả ÂM ở bất kỳ arm realized nào là kịch bản thật (asymmetry belief §1).

Kỳ vọng sai cũng là finding — bảng này in lại trong UPDATE cạnh kết quả thật.

---

## §7. Tham số mới — liệt kê HẾT, mỗi cái một quyết định quét

| Tham số | Nghĩa | Headline (đăng ký trước) | Dải quét | Ghi chú |
| --- | --- | --- | --- | --- |
| `market_demand_source` | nguồn cầu producer | `oracle` (default config) | — (định nghĩa arm) | giá trị lạ / trộn override ⇒ ValueError |
| `realized_demand.window_buckets` (k) | cửa sổ cuốn | **k\* từ procedure §6.2** | {1, 2, 3, 4, 6} | CẤM chọn vì Δ đẹp (bẫy PLAN #2) |
| `realized_demand.min_pickups` (min_n) | cổng nói toàn cục | 5 | {1, 3, 5, 10} | dự đoán TRƠ (§6.5#1); dải chốt sau khi in phân phối đếm 1 seed (probe) |
| ~~smooth_alpha~~ | — | **ĐÃ BỎ** | — | hai thiết kế mô tả hai semantics khác nhau ⇒ bỏ để bớt một knob; smoothing nếu cần = pre-register mới |
| `positioning_trigger` | luật ứng viên | `capacity` (default) | — (định nghĩa arm) | |
| `positioning_wait.threshold_min` (T) | ngưỡng chờ | **30** | {15, 20, 25, 30, 35} | 45/60 loại cấu trúc (§4.2); control-run xác nhận firing |
| `positioning_wait.min_idle` (n_min) | mẫu số theo Ô | **2** | {1, 2, 3} | đổi dấu 1↔2 = finding |
| fallback khối | gộp `grid_disk(c,1)` khi idle mỏng | rule 20% khai trước | — | hằng 20%/bán kính 1 = quy ước khai trước |
| pingpong rule | ngưỡng 10% / cửa sổ 2 bucket | quy ước hành động | — | không phải phép kiểm; kèm km-rỗng liên tục |
| hist prior | 30 ngày World A tuning | N=30 ngày | — | N không quét — giới hạn khai §9-L6 |
| `probe.wait_stats` | instrumentation | false | — | log-only, fingerprint-checked |

Tham số ngầm được KHAI (không quét, ghi nhận tương tác mới): `trips_per_hour_est = 1.5` đổi vai
thành bộ khử-nhiễu-slots khi λ̂ nhiễu (lượng tử hoá `// 1.5` nuốt dao động < 1,5).

---

## §8. Thứ tự thi công — đỏ trước, xanh sau (mỗi cổng phải CHỨNG MINH đỏ được)

Chi phí ước: implement + test ~4–5h · đo ~5–5,5h máy (chia batch, persist từng artifact trước batch
sau — quota guard CLAUDE §3.5) · phân tích + UPDATE ~2h.

**Bước 0 — plan mode**: trình 3 điểm chờ Cường (đầu spec) + spec này. Không code trước khi duyệt.

**Bước 1 — tiền-flight thước (§5.5)** *(trước mọi code E10 — nó quyết định thước của tất cả)*:
- T1 (đỏ-được): bơm adherence lệch 0,10 @ n=500 qua wrapper verdict của script ⇒ TREO; lệch 0,01 ⇒
  OK. Chứng minh đỏ: tạm ngắt truyền `by_channel_archetype`.
- Chạy preflight 30 seed → z thật → nhánh 2/3 của §5.5. Nếu sửa thước: T2 run coin-true-không-thi-
  hành ⇒ thước cũ 0 / thước mới ≈ nominal (đỏ trên code cũ); cả hai suite xanh; UPDATE riêng.

**Bước 2 — estimator E10a (TDD)**:
- T3: công thức — bơm `pickup` tổng hợp vào stub → λ̂ đúng từng số; event `t == idx·b` bị loại;
  clip `first_op_bucket`; `n_buckets = max(0,…)` với idx < 5 (đỏ trên công thức không-max).
- T4: cold ⇒ `{}` và **≠** `demand_field[hour]` — chứng minh đỏ bằng fallback oracle tạm.
- T5: whitelist — stub chỉ có `.events`, mọi attr khác raise; estimator chạy trọn ngày. (Giết cả
  đường `orders`/`orders_sorted`/`demand_field`.)
- T6: xác định-theo-thời-điểm-gọi — `estimate(idx)` giữa bucket == tại biên bucket, exact.
- T7: 0 RNG — grep module không có `rng`/`random`; `world.rng` state bất biến qua một lượt planner
  realized-mode.

**Bước 3 — wiring producer**:
- T8: `realized` + `market_demand_override` ⇒ ValueError; source lạ ⇒ ValueError; `bucket_min≠60`
  + realized ⇒ ValueError (mỗi cái một test đỏ hiển nhiên).
- T9: oracle mode — `_demand(hour, idx)` trả dict bằng **từng bit** bản cũ; không event kind mới
  (đếm kind); stub-không-cfg của test cũ vẫn dựng được producer.
- T10: poison đúng ref §2.3 — arm realized trọn ngày, `_demand` không bao giờ trả oracle field.
- T11 (fingerprint §2.4): hai config × ≥5 seed, exact-repeat, trước/sau merge.

**Bước 4 — E10b**:
- T12: `count_idle_wait` — lọc IDLE, gộp ô, median chẵn/lẻ nội suy, ô rỗng.
- T13: trigger — median > T ∧ n ≥ n_min ⇒ ứng viên (nếu streak cá nhân ≥ T); ≤ T ⇒ không; n_min
  chặn ô 1 người; người streak 5′ trong ô fire KHÔNG bị kéo.
- T14 (**đỏ bắt buộc trước khi vá**): dựng đúng ca STAGGER-về-own-cell (pref đầy bởi ứng viên SOC
  cao hơn, own cell còn slot trong zones) ⇒ chứng minh Hungarian gán về own cell khi CHƯA có veto
  (đỏ), veto vào ⇒ `assigned_target ∉ fired` (xanh). Test "pref ≠ own" đơn thuần bị CẤM làm bằng
  chứng (nó xanh khi lỗi còn sống).
- T15: `ranked_eff` rỗng / không đích ⇒ không ứng viên, **không rút coin**, `decided` không tăng.
- T16: cadence check sống ở nhánh wait (bật `count_positioning_in_budget` ⇒ bị chặn như nhánh cũ).
- T17: cold hai tầng (estimator câm ⇒ planner ngủ; đầu ca mọi streak 0 ⇒ không ô fire).
- T18: probe `wait_stats` — fingerprint bật/tắt IDENTICAL; event probe không lọt vào lifecycle
  projections (kind không decision_id bị skip).

**Bước 5 — probe + tuning + prereg**: `probe` (phân phối W, firing per T, WAIT-share, phân phối đếm
pickup — chốt dải min_n), `tune` (k\*), `histprior`; điền `e10-prereg-locked.json`, **commit**.

**Bước 6 — đo** (theo thứ tự, persist từng file): `worldA` → `arm oracle` (STOP-1 check ngay) →
`arm hist` → `arm real` → `arm wait` → `arm waitoracle` (n=30) → sensitivity (k, T, n_min, min_n ở
n=30, World A cache) → `diff` → `bias`.

**Bước 7 — nghiệm thu**: cả HAI suite (`uv run pytest -q` **và** `uv run pytest -q
ui/backend/tests`); UPDATE-### theo template (đủ mục Adversarial self-review, bảng kỳ vọng §6.5 vs
thực tế, nhãn evidence/ASSUMPTION, seeds); **visual gate**: dashboard/replay 1 seed ghi sẵn cho
Cường xem bản đồ herding (B_real vs B_oracle) trước commit; nhắc lại `PENDING-REVIEW.md`.

---

## §9. Giới hạn KHÔNG VÁ ĐƯỢC + rủi ro của chính spec này

Mỗi mục dưới đây là một lỗ phản biện chỉ ra mà spec **không vá** — chúng phải xuất hiện nguyên văn
trong artifact và UPDATE, không được rơi rụng dọc đường.

- **L1 — Thế giới TÁCH BIẾN, rank tĩnh cả ngày.** `λ = orders_per_day × hour_share × cell_weight`
  ⇒ hour_share nhân đều mọi ô ⇒ thứ hạng ô không đổi suốt ngày; bài toán khó nhất ngoài đời
  (pattern không dừng sáng/tối) không tồn tại trong thế giới đo. Hệ quả bất đối xứng đã nhúng vào
  §6.3: KQ-SỤP nói mạnh, KQ-GIỮ nói yếu; G-SENS phẳng theo k là hệ quả, không phải robust. Arm
  nonstationarity (bật event addend) → DEFERRED kèm điều kiện mở lại.
- **L2 — λ̂ ngửi được oracle QUA bản năng tài xế.** Pickup chỉ xảy ra nơi có tài xế; tài xế đứng
  theo λ×nhiễu ⇒ đội xe là "máy giải mã λ", phân bố pickup đã thấm λ. Không vi phạm ranh giới đo
  (mọi arm cùng thế giới) nhưng R bị kéo LÊN so với thế giới cả hai phía đều mù. Không gỡ được mà
  không đổi thế giới (ngoài scope). Diagnostic bắt buộc: Spearman(pickup share World A, λ share)
  per-hour, kèm mọi KQ-GIỮ.
- **L3 — Feed pickup TOÀN ĐỘI (cell, phút) ngoài đời chưa VỮNG.** Catalog bảng trips fleet-wide
  đang "THIẾU CỘT" (`docs/data-catalog/gsm-data-catalog.csv`, dòng trips) và GSM không cấp thêm dữ
  liệu. ASSUMPTION có nhãn trong artifact: *"Δ điều kiện trên advisor có trip feed toàn đội độ phân
  giải (cell, phút)"*; đối chiếu cột xếp hạng của `data-contract-counterfactual.md` §4 khi viết
  UPDATE. Sensitivity subsample feed (đếm pickup của x% actor, keyed theo actor_id) → DEFERRED kèm
  điều kiện mở lại. Nếu ngoài đời advisor chỉ thấy trip của chính người được tư vấn, mật độ giảm
  ~86× và min_n=5 câm gần cả ngày — Δ đo được KHÔNG phải trần của kịch bản đó.
- **L4 — E10b đo trigger × execution-gate, không phải giá trị thông tin trigger thuần.** `wait_only`
  chỉ áp khi bản năng WAIT; quần thể W>T ≈ quần thể impatience; plan không TTL. Diagnostic §4.6 tách
  được một phần nhưng không deconfound trọn trong v1. `B_wait_oracle` n=30 chỉ đọc CHIỀU.
- **L5 — Attribution thời điểm ĐÓN (B5).** Ngoài đời đơn đã phục vụ có request timestamp — sim
  nghèo thông tin hơn thực tế. Hướng bảo thủ, đã khai trong bảng bias.
- **L6 — "Lịch sử" của B_hist là 30 ngày cùng-phân-phối.** Cùng λ, không cấu trúc thứ/ngày lễ,
  không drift — dễ hơn lịch sử thật; N=30 không quét. Kết hợp L1 ⇒ B_hist gần như chắc chắn đẹp hơn
  ngoài đời. Blend hist + trong-ngày chưa mô hình hoá.
- **L7 — k\* tuning ở shadow World A ≠ equilibrium dưới treatment.** Tiêu chí đã sạch oracle nhưng
  chất lượng ước lượng của cùng một k khác nhau giữa nền A và nền có advice (feedback). Khai trong
  prereg; sensitivity k gánh một phần.
- **L8 — T bị trói vào config bản năng hiện hành.** Neo T đọc cả hai đồng hồ (hoà vốn 1,5 cuốc/h VÀ
  impatience 20′×2 của `pilot_dongda.yaml`); đổi config behavior là đổi nghĩa của T và của cả sweep.
- **L9 — "Kinh nghiệm tài xế" trong sim cũng là oracle-derived.** Sim chỉ đo được phía advisor;
  phát biểu "advisor kém hơn belief tài xế" là phát biểu trong-sim, không phải đo lường về tài xế
  thật.
- **L10 — min_pickups nhiều khả năng trơ** ⇒ chiều "cổng nói tối thiểu" thực tế KHÔNG được kiểm ở
  config này; ai cần cổng đó ở config thưa hơn phải đo lại.

**Rủi ro của chính spec:**

- Spec dài — rủi ro lớn nhất là **thi công chọn lọc** (làm phần dễ, rơi phần cổng). Đối trọng: §8
  đánh số cổng T1–T18, artifact phải mang đủ khoá; thiếu khoá nào `diff` fail-loud.
- Ước độ lớn (0,6–1,2 pickup/ô/bucket; z≈13; SE tái lập) là **tính tay/1-seed** — họ bẫy §5#7 "cơ
  chế đúng độ lớn sai" đã sập 3 lần; mọi con số này PHẢI tự đo lại ở probe/preflight trước khi trích.
- Zone-veto là luật mới chưa từng chạy — có thể tạo dynamics không lường (vd fired cells nhiều ⇒
  ranked_eff cạn ⇒ arm wait im hơn dự kiến). Được phép: báo như hành vi đo được. Không được phép:
  chỉnh veto sau khi nhìn Δ.
- Nếu Cường bác arm `B_hist` (điểm chờ #1): B_real headline phải re-scope claim thành *"cận dưới
  dưới điều kiện zero-history — KHÔNG phải câu trả lời đầy đủ cho E10"*, và E10 ghi nhận còn nợ câu
  trả lời ở điều kiện triển khai thật.

---

*Spec này thay thế các bản nháp `e10a-realized-demand-source.md` / thiết kế E10b rời — không tạo
thêm file spec con; mọi chỉnh sửa sau này sửa TẠI ĐÂY kèm đính chính có ngày.*
