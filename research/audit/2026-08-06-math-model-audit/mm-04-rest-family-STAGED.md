# mm-04 — audit math-modelling kênh REST_WINDOW + meal-timing

**Đích dự kiến của artifact:** `research/audit/2026-08-06-math-model-audit/mm-04-rest-family.json`
**Trạng thái:** plan mode đang bật ⇒ tôi KHÔNG được ghi vào repo. Nội dung artifact hoàn chỉnh
nằm trong khối JSON dưới đây (copy nguyên khối vào đúng path trên khi được duyệt).

Probe đã chạy (read-only, không ghi file repo):
`…/scratchpad/probe_mm04_rest.py` + 2 lệnh python inline. 3 seed (7000/7001/7002) × 4 ngày × 2 arm.

```json
{
  "item": "REST_WINDOW (S7 idle_reduction — TẮT theo config; hoãn nghỉ = CAM KẾT dồn vào khung vắng, D-M3-04-FIX) + meal-timing (D-E4-05, chưa xây)",
  "objective_as_implemented": {
    "co_ham_muc_tieu_khong": "KHÔNG. Không có objective function nào trong kênh này — không có đại lượng tiền/cuốc nào được tính, so, hay cực trị hoá. Toàn bộ là một chuỗi cổng boolean. Đây là khác biệt bản chất so với station_choice (có argmin) và shift_extend (có need_min): mm-04 không sai phép tính, nó KHÔNG CÓ phép tính.",
    "S7_idle_reduction": "Chọn `worst_window` = argmax_h(idle_min ĐÃ TÍCH LUỸ tại giờ h) trên tập {h : demand_index(h) ≤ LOW_DEMAND_MAX=0.5}, tie-break theo h nhỏ hơn (idle_reduction.py:74-78). Gate `notable` = total_idle ≥ 45′ OR longest_idle ≥ 25′ (:80). demand_index = chuẩn hoá theo ĐỈNH trong ngày. KHÔNG có vế tiền, KHÔNG có vế cuốc, KHÔNG so demand giữa hai giờ.",
    "bridge_should_defer_rest": "Hàm CỔNG, trả (defer, why, alt). Thứ tự: soc_low → fatigued → committed → commit_broken → defer_cap → target=rest_window_hour → no_window/at_window → window_past → defer_cap(2) → no_alt_action → cadence → coin → CAM KẾT (advice_bridge.py:889-944). Điều kiện đủ để hoãn: (i) tồn tại một giờ đích khác giờ hiện tại, (ii) giờ đó tới được trong ca và trong trần 120′, (iii) `consider_relocate` trả khác WAIT, (iv) qua nhịp + coin. Không điều kiện nào định giá.",
    "action": "`actor.rest_commit_due_min = floor_hour(now) + minutes_to` (:939) + `rest_deferred_min += minutes_to − now%60` (:943). World ép REST ở decision point đầu tiên trong [due, due+60) (`rest_commit_gate`, world.py:49-66, gọi ở :871); bận trọn giờ X ⇒ `broken` + trả quyền nghỉ.",
    "duong_song_duy_nhat": "`planned_rest_hour` từ multiday (memory hôm qua, multiday.py:167 ghi / :233 nạp). Bridge SHORT-CIRCUIT ở advice_bridge.py:848-849 trước cả `notable` và trước `_capture_checkpoint`. Đường nội-ngày ĐO ĐƯỢC là inert: probe day0, 3/3 seed made=0, `window_past` 54/52/58 + `no_window` 19/17/19, Δpayout/Δtrips/Δrest_min = ĐÚNG 0.0 (bit-identical). Cite D-SIM-10 / UPDATE-050 — bổ sung con số.",
    "suy_bien_thuc_te": "Với `rest_defer_max_min=120` (POLICY_LOCKED, policy_locks.py:39-40; config :377) và `minutes_to` lượng tử theo ĐẦU GIỜ (:910), khoảng hoãn khả thi CHỈ còn {60′, 120′} ⇒ kênh chỉ dời được nghỉ 1-2 giờ về phía trước, tối đa ~1-2 lần/tài xế/ngày. Đo: made 0-4/ngày-đội trên ~118-136 lượt nghỉ (≈1-3%); `defer_cap` veto 6-17/ngày."
  },
  "action_space": [
    "S7: trả về MỘT giờ trong ngày (không ô H3 — guardrail D-004b/B1 giữ đúng)",
    "bridge: {hoãn tới đầu giờ X, không hoãn} × {alt = (RELOCATE, cell) do `consider_relocate` chọn}",
    "world thi hành THẬT: `rest_commit_gate` ép `action := REST` (world.py:871-875, `rest_forced=True`); nhánh rơi `action, target = alt` + `reloc_reason='rest_defer'` (world.py:1060-1062)",
    "KHÔNG có action nào cho meal-timing: `meal_hour` là HABIT tĩnh của actor (behavior.py:161), chưa kênh nào đặt lịch nó (D-E4-05)"
  ],
  "variables_observed": [
    "S7 nhận: idle_by_hour (world.py:1143, chỉ giờ ĐÃ QUA), total/longest idle, online_hours, demand_by_hour 24 giờ, active_reposition (luôn None trong sim)",
    "bridge nhận: soc_pct, online_min, fatigue_threshold_min, rest_commit_due_min/broken, rest_deferred_min, shift_end_min, hour, demand_hint_fn, alt_action_fn, soc_threshold",
    "ĐÚNG-SẠCH đã kiểm: `build_idle_reduction_input` gọi `demand_hint_fn` cho CẢ 24 giờ (:820) mà KHÔNG làm bẩn dòng RNG chung — `_actor_demand_hint` dùng `np.random.default_rng((seed,actor,hour,cell))` riêng + cache theo khoá (world.py:1146-1170), 0 draw từ `World.rng`. Nghi vấn CRN ở đây bị BÁC.",
    "ĐÚNG-SẠCH đã kiểm: `due` không bao giờ ở quá khứ (minutes_to ≥ 60 ⇒ due > now); cửa sổ gate đúng [due, due+60); rail sức khoẻ (`fatigued`) đứng TRÊN nhánh `committed` (:892 trước :897) — đúng §1.2b cổng một chiều."
  ],
  "variables_missing": [
    {
      "var": "demand tại GIỜ HIỆN TẠI (vế đối chiếu của cả bài toán)",
      "vi_sao_quan_trong": "Thế giới định giá nghỉ = số cuốc mất ≈ rest_min × λ(giờ đang nghỉ). Giá trị của việc HOÃN = rest_min × [λ(giờ hiện tại) − λ(giờ đích)]. Kênh không tính hiệu đó: nó chỉ kiểm `target != hour` (:907). Trên đường sống, `demand_hint_fn` và `hour` được TRUYỀN VÀO nhưng KHÔNG DÙNG lần nào (short-circuit :848-849 bỏ qua toàn bộ solver) — biến sim biết mà kênh bỏ qua theo nghĩa mạnh nhất.",
      "nguon_co_san_trong_sim": "`world._actor_demand_hint(actor, hour)` đã tính sẵn ở world.py:860 cùng vòng lặp; `_demand_index` hôm qua đã nằm trong memory"
    },
    {
      "var": "khả-thi-tính của giờ đích (reachability) khi S7 chọn khung",
      "vi_sao_quan_trong": "S7 chọn argmax(idle quá khứ) hoàn toàn không biết trần 120′ hay giờ nghỉ theo bản năng. Đo day1 seed 7000: 17/90 tài xế không có kế hoạch, 17/90 (19%) có kế hoạch NẰM TRONG tầm 1-2h so với `meal_hour`, 56/90 (62%) kế hoạch BẤT KHẢ (gap 3,4,5,18,21,22,23 giờ). `planned_rest_hour` thường rơi vào 5h hoặc 9-10h (đầu ca, chờ nhiều, cầu thấp) trong khi `meal_hour` ∈ {11,12,13,18,19}. Đây là nguyên nhân TRỰC TIẾP của tỷ lệ hành động 1-3%.",
      "nguon_co_san_trong_sim": "now, `rest_defer_max_min`, `shift_end_min`, `meal_hour` — tất cả đã có ở call-site; chỉ cần đưa tập giờ ứng viên vào `idle_reduction_input`"
    },
    {
      "var": "GIÁ của hành động thay thế: travel time + SOC + việc RELOCATE làm tài xế RA KHỎI pool điều phối",
      "vi_sao_quan_trong": "Cổng chỉ hỏi `alt != WAIT` — một PROXY tồn-tại, không phải một định giá. Nhưng world: (a) relocate đặt `state = ENROUTE` (world.py:1125) và pool chào đơn CHỈ lấy `ActorState.IDLE` (world.py:628) ⇒ 'việc có ích' cũng là thời gian KHÔNG nhận được đơn; (b) relocate tự nguyện TRỪ PIN thật (world.py:1130) ⇒ hoãn 2 giờ với nhiều lượt relocate có thể kéo mốc đổi pin về sớm, đổi downtime nghỉ thành downtime trạm. Cả hai vế world định giá, objective không có.",
      "nguon_co_san_trong_sim": "`cell_distance_km`, `_travel_min`, `_pct_per_km` đã dùng ngay trong nhánh đó"
    },
    {
      "var": "phương sai / P(giờ X còn rảnh để nghỉ) — cam kết là lời hứa xác suất",
      "vi_sao_quan_trong": "Cam kết coi giờ X là chắc chắn. Thực tế `broken` (bận trọn giờ X) làm nghỉ KHÔNG ĐƯỢC DỜI mà bị XOÁ: `meals_taken` đã +1 tại behavior.py:163 TRƯỚC khi bridge kịp hoãn, nên sau `broken` nhánh nghỉ-ăn không bao giờ bắn lại; chỉ còn `fatigue>1.0 & p=0.3`. Đo: 1 lần `broken` / 12 ngày-đội (hiếm) — nhưng bảo toàn chỉ được khai bằng BẤT ĐẲNG THỨC `made ≥ kept+broken+cleared` (sim_metrics.py:365; test_rest_commit.py:243), không invariant nào đòi nghỉ được DỜI chứ không bị XOÁ.",
      "nguon_co_san_trong_sim": "lịch sử busy-fraction theo giờ của chính actor; hoặc đơn giản là phục hồi `meals_taken` ở nhánh broken"
    },
    {
      "var": "thời lượng nghỉ (REST_MIN..REST_MAX = 20-45′) trong kiểm khả thi cuối ca",
      "vi_sao_quan_trong": "`:911` chỉ kiểm `now + minutes_to > shift_end_min`, không kiểm nghỉ có VỪA trong ca. Ràng buộc đúng là `due + REST_MAX ≤ shift_end`. Cam kết đặt ở due = shift_end − 20′ vẫn qua cổng; world REST rồi `timeout(uniform(20,45))` bất chấp shift_end (world.py:1113) ⇒ nghỉ trườn qua giờ kết ca và tài xế END_SHIFT ngay sau — phần đuôi ca bị đổi thành thời gian ngoài ca một cách im lặng.",
      "nguon_co_san_trong_sim": "`REST_MAX_MINUTES` là hằng module cùng file world.py:46"
    },
    {
      "var": "điểm/mốc thưởng (`policy.trip_points(hour)`) — giờ peak điểm ×2",
      "vi_sao_quan_trong": "point_peak=10 vs point_normal=5 ở giờ [6,7,16,17] (config :252-255). Hoãn nghỉ từ giờ thường sang giờ thường là một chuyện; dời quanh biên giờ peak điểm đổi giá trị GẤP ĐÔI. Kênh không đọc `trip_points` lần nào.",
      "nguon_co_san_trong_sim": "`self.policy.trip_points(hour)` đã dùng ở S2/shift_extend"
    }
  ],
  "math_issues": [
    {
      "title": "KHÔNG có phép so demand giữa giờ hiện tại và giờ đích: khung chọn bằng argmax(idle SUNK) dưới một cổng tuyệt đối ≤0,5 ⇒ 3/15 lượt hoãn ĐÃ QUAN SÁT dời nghỉ vào giờ CẦU CAO HƠN",
      "evidence": "src/gsm_core/solvers/idle_reduction.py:74-78 (sort theo −idle_min, lấy giờ ĐẦU TIÊN có demand ≤ LOW_DEMAND_MAX; :25 LOW_DEMAND_MAX=0.5); src/gsm_sim/advice_bridge.py:907 (chỉ kiểm `target == hour`, không so demand). Probe: (a) cổng ≤0,5 nhận 13-14/24 giờ, gồm giờ 12 ĐÚNG 0,500 = một nửa đỉnh, trong khi giờ 9 = 0,5288 bị loại — dải giờ 'thấp điểm' hợp lệ trải 0,34-0,50 (lệch tương đối 32%) mà solver coi như tương đương; (b) 3/15 lượt hoãn quan sát được (3 seed × ngày 1-3) có demand_index(giờ đích) > demand_index(giờ hiện tại) theo CHÍNH tín hiệu S7 đã dùng: seed 7000 day1 2/4 (11h→12h: 0,375→0,500; 11h→13h: 0,375→0,394), seed 7001 day1 1/1.",
      "detail": "Giá trị của kênh = rest_min × [λ(giờ hiện tại) − λ(giờ đích)]. Code cực-đại-hoá idle ĐÃ TIÊU ở quá khứ — một sunk cost — và chỉ kiểm ngưỡng TUYỆT ĐỐI trên giờ đích, nên DẤU của giá trị không được bảo đảm. Đúng khuôn station_choice/UPDATE-160: objective cực tiểu một đại lượng phụ (chờ ở giờ vắng) và thiếu vế mà world thật sự định giá (cuốc mất ∝ λ tại giờ nghỉ). Khác biệt làm nó nặng hơn station_choice: ở đây không có argmin nào cả, nên không có chỗ để 'thêm một vế' — phải thêm HẲN một phép so. Kênh đang OFF (config :339) nên tác động là tiềm ẩn, nhưng đây là kênh sắp được đo ở ablation kế và mọi số Δ của nó đứng trên phép chọn này.",
      "severity": "CAO",
      "confidence": "CAO",
      "cung_lop_station_choice": true
    },
    {
      "title": "LAN CAN 1 `soc_low` BẤT KHẢ ĐẠT từ call-site của world (rail chết) — nhưng `REST_RAILS` vẫn tính nó là 1/3 lan can sức khoẻ và tầng 5 không thể tố giác việc xoá nó",
      "evidence": "src/gsm_sim/behavior.py:148-152 (`choose_idle_action` bước 1: `soc_pct <= cfg_vehicle['swap_soc_threshold_pct']` ⇒ GO_SWAP/GO_CHARGE, REST không bao giờ được chọn) vs src/gsm_sim/world.py:1037 (chỉ hỏi bridge khi `action == REST`) + :1040 (truyền ĐÚNG cùng khoá `swap_soc_threshold_pct`) ⇒ src/gsm_sim/advice_bridge.py:890 `soc_pct <= soc_threshold` là FALSE theo cấu trúc. Đo: 0 veto `soc_low` trong 12 ngày-đội (3 seed × 4 ngày), tập lý do quan sát được = {fatigued, window_past, no_window, defer_cap, no_alt_action, at_window, not_followed}. src/gsm_sim/sim_metrics.py:329 `REST_RAILS = ('soc_low','fatigued','defer_cap')`, :359 `veto_fired_n` = tổng ba; :537 `if va >= RAIL_ALIVE_MIN_N and vb == 0` với RAIL_ALIVE_MIN_N=20 (:340) ⇒ va=0 luôn ⇒ nhánh 'SỤP VỀ 0' của `soc_low` không bao giờ bắn.",
      "detail": "Chính `D-M3-06` (gỡ hai nhánh hoãn GO_SWAP/GO_CHARGE vì code chết 0/41) đã làm rail này thành trẻ mồ côi: trước đó `soc_low` là lan can THẬT của nhánh hoãn-đổi-pin. Docstring vẫn giữ lý lẽ cũ 'hoãn đổi pin ⇒ battery_stranded' (advice_bridge.py:884) — lý lẽ không còn đường chạy. Hệ quả kép: (a) `veto_fired_n` bị PHA LOÃNG bằng một hằng 0, nên tỷ lệ 'lan can còn sống' đọc ra lạc quan hơn thực tế; (b) cơ chế tầng 5 sinh ra ĐÚNG để bắt đòn xoá-lan-can lại mù với rail này — ai xoá `soc_low` thì không test nào đỏ, không flag nào bắn. Test `tests/test_advice_bridge.py:285-293` gọi `should_defer_rest` TRỰC TIẾP với soc=10/thr=20, tức nó ghim ngữ nghĩa của hàm chứ KHÔNG chứng minh rail có đường chạy trong world — đúng lớp 'test ghim một hành vi không tồn tại ở runtime'. Lưu ý ranh giới: đề xuất KHÔNG phải đưa sức khoẻ vào objective; chỉ là rail phải hoặc sống hoặc bị khai tử tường minh.",
      "severity": "CAO",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "Trần hiệu ứng của kênh thấp hơn NỀN NHIỄU của cặp arm 1-2 bậc độ lớn: một ngày có ĐÚNG 0 can thiệp vẫn lệch −28.928 VND / −7 cuốc",
      "evidence": "Probe 3 seed × 4 ngày: day0 (kênh inert, made=0) Δ = ĐÚNG 0,0 ở cả payout/trips/rest_min — chuẩn CRN sạch. Từ day1: seed 7002 day2 made=0 mà Δpayout=−28.928, Δtrips=−7 (chỉ có veto `no_alt_action`=5, `not_followed`=2 — mỗi lần vẫn GỌI `alt_action_fn` ở advice_bridge.py:916 trước cadence/coin ⇒ rút RNG từ `World.rng` DÙNG CHUNG). |Δpayout| quan sát: 28.928 … 626.869 với made ∈ {0,1,2,4}. |Δrest_min| tới 630,1′ trên nền 3.874,8′ = 16,3%. Giá trị lý thuyết một lượt hoãn: 32,5′ nghỉ ≈ 0,54 giờ-tài-xế × Δλ với |Δdemand_index| đo được 0,02-0,13 của đỉnh; payout/cuốc = 23.841 VND, ~10,4 cuốc/tài xế/ngày (935 cuốc/90 actor) ⇒ ≈1-5k VND/lượt, ≤ ~20k/ngày-đội. SNR ≈ 0,01-0,24.",
      "detail": "Nguyên nhân dòng RNG là `D-M3-20` (chỉ cite). Cái CHƯA ghi ở đâu là HAI hệ quả đo lường: (1) mọi Δ mức-đội của `rest_window` không thể đọc được — kể cả một phiên bản HOÀN HẢO của kênh (dời nghỉ từ 0,50 xuống 0,19 = trần Δdemand 0,31 ⇒ ~5k VND/tài xế/ngày ≈ 2% payout ngày 248k) cũng nằm quanh nền nhiễu nếu đo bằng tổng payout; (2) `REST_TOTAL_DROP_TOL = 0,02` (sim_metrics.py:341) nằm ~8 lần DƯỚI nhiễu đo được của `rest_min_total` ⇒ cổng sức khoẻ tầng 5 bắn/không-bắn gần như ngẫu nhiên trên đường multiday, vừa báo động giả vừa cấp giấy-thông-hành giả. Kết luận thi công: kênh này phải đo bằng estimator PHẠM VI SỰ KIỆN (cửa sổ của chính tài xế được can thiệp), không phải Δ tổng.",
      "severity": "CAO",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "Đường SỐNG DUY NHẤT nạp cho S7 dòng đơn NGOẠI SINH của hôm qua (gồm 20,1% đơn KHÔNG ai phục vụ) — trái nguyên tắc 'tuyệt đối không dựng từ world.orders' và trái chính caveat PROXY của solver",
      "evidence": "src/gsm_sim/multiday.py:162 `\"demand_by_hour\": _demand_index(result)` + :175-186 (`for o in result.orders` — TOÀN BỘ đơn sinh ra, không lọc trạng thái) vs src/gsm_sim/advice_bridge.py:24-31 nguyên tắc #2 ('Tuyệt đối không dựng từ `world.orders`') và src/gsm_core/solvers/idle_reduction.py:12/:29-30 WARN_PROXY ('chỉ đơn ĐÃ phục vụ'). Đo seed 7000: 1.202 đơn sinh / 960 COMPLETED ⇒ censoring 20,1%; tập giờ 'thấp điểm' theo GEN = [0..5,9,10,12,13,14,15,22,23] vs theo SERVED = [0..5,10,12,13,14,23] ⇒ ĐỔI 3/24 giờ (9, 15, 22 lật); lệch chỉ số theo giờ tới ±0,234 (h06 −0,234, h20 +0,147, h09 +0,117).",
      "detail": "KHÔNG phải rò tương lai (ngày đã xong) — nên đừng gọi nó là future leak. Nó là PHÌNH TẬP THÔNG TIN: tài xế/advisor thật chỉ quan sát được cuốc đã phục vụ (censored bởi cung), sim lại cấp cầu ngoại sinh không censored. Vì censoring dồn vào giờ thiếu cung, chuẩn hoá-theo-đỉnh đổi hình và TẬP GIỜ HỢP LỆ đổi thật (3/24) ⇒ mọi giá trị đo được của kênh là CHẶN TRÊN của bản triển khai. Nặng thêm vì test duy nhất ghim tính chất 'chỉ dùng belief' (`tests/test_advice_bridge.py:318-327`) chỉ phủ đường NỘI-NGÀY — đúng đường đã đo là INERT. Cùng lớp lỗi 'test ghim đường chết, đường sống không ai ghim'.",
      "severity": "TB",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "Bản sửa ADV-08 chỉ migrate PHÉP CỘNG, hai CỔNG vẫn dùng thước cũ đã phóng đại — và cổng cuối ca còn thiếu hẳn thời lượng nghỉ",
      "evidence": "src/gsm_sim/advice_bridge.py:910 `minutes_to = ((target − hour) % 24) * 60` (đo giữa hai ĐẦU GIỜ) dùng ở :911 `now_min + minutes_to > shift_end_min` và :913 `rest_deferred_min + minutes_to > rest_defer_max_min`, trong khi :943 cộng đại lượng THẬT `minutes_to − now%60`. Test ghim đúng sự lệch này: `tests/test_rest_commit.py:85-87` (now=9h10, target=11h ⇒ booked 110, còn cổng :913 tính bằng 120). world.py:1113 `rest_min = rng.uniform(REST_MIN_MINUTES, REST_MAX_MINUTES)` chạy bất chấp `shift_end_min`.",
      "detail": "(a) Hai cổng tính THỪA tới 59′ so với sổ ⇒ từ chối oan những lượt hoãn mà ngân sách 120′ thật sự chịu được; đúng lớp lỗi mà repo đã có tiền lệ ('một bản đính chính lại mắc đúng lỗi nó đi sửa') — phần accrual đã sửa, phần gate bị bỏ lại. Chiều tác động là BỚT can thiệp, nên nó cộng dồn vào bài toán liều thấp 1-3% ở dưới, không che bug nào. (b) Nghiêm hơn về ràng buộc: điều kiện khả thi ĐÚNG là `due + REST_MAX_MINUTES ≤ shift_end_min`, còn `now + minutes_to` = `due + now%60` vừa CHẶT quá (thừa now%60) vừa LỎNG quá (thiếu 20-45′ nghỉ) — ràng buộc bind SAI CỬA, đúng lớp (e) của audit. Ca đặt cam kết ở `due = shift_end − 20′` qua được cổng; tới giờ X gate ép REST, nghỉ trườn qua `shift_end` rồi END_SHIFT ⇒ đuôi ca im lặng biến thành ngoài-ca. Tần suất CHƯA ĐO (mẫu kept chỉ 15 lượt).",
      "severity": "TB",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "Bậc `rest_window` của CHANNEL_LADDER không SẠCH quy trách: cả KÍCH HOẠT lẫn HÀNH ĐỘNG đều là positioning, dù bậc đó khai `positioning_overrides: 'off'`",
      "evidence": "src/gsm_sim/parallel.py:42-43 (bậc `rest_window` đặt `positioning_overrides: 'off'`) nhưng điều kiện hoãn là `alt != WAIT` (advice_bridge.py:916-918) mà `alt` = `consider_relocate` — trả RELOCATE chỉ khi `v_adj > best_val × 1,25` (behavior.py:217) và `rng.random() < p_move` (:228); hành động áp vào world là RELOCATE mang `reloc_reason='rest_defer'` (world.py:1060-1062). Test ghim chính điều này: `tests/test_rest_commit.py:244` `assert reloc >= made` — mỗi cam kết sinh một relocate NGAY.",
      "detail": "Kênh vì thế bắn ĐÚNG LÚC tiêu chí dịch-chuyển-có-lợi của bản năng thoả, và thứ nó áp vào world là một cú relocate. Δ đo được ở bậc này trộn (i) giá trị dời thời điểm nghỉ với (ii) giá trị của một lượt relocate thêm — trong khi bậc `positioning` riêng (`= B3w`) mới là chỗ giá trị (ii) đáng được ghi. Thêm nữa RELOCATE đặt `state = ENROUTE` (world.py:1125) và pool chào đơn chỉ lấy IDLE (world.py:628), nên 'việc có ích' cũng là thời gian không nhận được đơn: cổng `alt != WAIT` là PROXY tồn-tại chứ chưa bao giờ là định giá. Đây là hậu duệ trực tiếp của bài học FIX-PRE ('action := WAIT là TOÀN BỘ cơ chế') — đã thay WAIT bằng RELOCATE nhưng vẫn chưa định giá vế nào.",
      "severity": "TB",
      "confidence": "CAO",
      "cung_lop_station_choice": true
    },
    {
      "title": "Bộ guardrail tầng 5 của họ REST được neo trên `run_once` — đúng đường mà kênh INERT; các rail chỉ sống ở multiday thì bị khai là 'trơ'",
      "evidence": "tests/test_rest_rails_guardrail.py:26-36 (cả run_a/run_b đều `run_once`) + :56-62 `test_t3_defer_cap_TRO_o_config_hien_hanh` assert `veto_defer_cap_n == 0`. Probe: trên run 1 ngày (≡ day0) made=0 ⇒ defer_cap/no_alt_action/at_window/commit_* đều 0; trên multiday `defer_cap` bắn 6-17/ngày và `no_alt_action` 5-12/ngày.",
      "detail": "Kết quả: `veto_fired_n` ở fixture tầng 5 thực chất CHỈ là `veto_fatigued_n` (soc_low chết theo cấu trúc, defer_cap trơ theo đường đo) ⇒ bộ tố giác 'lan can sụp về 0' chỉ còn MỘT tín hiệu sống. Đây không phải test sai — T3 nói thẳng 'ĐỎ = TIN TỐT' — nhưng tiền đề của nó ('kênh nói 0 lần') CHỈ đúng trên `run_once`, còn `D-M3-04-FIX` đã làm kênh nói được trên multiday. Neo cổng vào đường không có can thiệp là cùng lớp lỗi 'đo arm đối chứng bẩn': cổng đo đúng thứ nó sinh ra để đo, nhưng ở nơi không có gì để đo.",
      "severity": "TB",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "`notable` và short-circuit `planned_rest_hour` làm hai cổng chống-bịa-vấn-đề + checkpoint trở nên vô hiệu trên đường sống",
      "evidence": "src/gsm_sim/advice_bridge.py:848-849 (return TRƯỚC `build_idle_reduction_input`, TRƯỚC `notable` :853-854, TRƯỚC `_capture_checkpoint` :858-860). idle_reduction.py:80 `notable = total ≥ 45′ OR longest ≥ 25′` — trên multiday hồi cứu, tổng idle/tài xế/ngày luôn vượt xa 45′ nên `notable` cũng gần như không bind ở multiday.py:166.",
      "detail": "Hệ quả: (a) trên đường sống, kênh không bao giờ kiểm lại rằng HÔM NAY có vấn đề chờ đáng lưu ý — nó thi hành kế hoạch hôm qua vô điều kiện; (b) không `advice_checkpoint` nào của S7 được sinh, nên `rest_window_end_min` / validity-hint (checkpoint_trace.py:91, lifecycle/checkpoint.py:252) chưa từng được thực thi ở nơi kênh hành động — hai test phủ nó (`tests/test_checkpoint_enrichment.py:94`, `tests/test_advice_checkpoint.py:118`) đều dựng snapshot tay. Freshness/hạn hiệu lực của lời khuyên nghỉ vì thế không có bằng chứng runtime.",
      "severity": "THẤP",
      "confidence": "CAO",
      "cung_lop_station_choice": false
    },
    {
      "title": "`meals_taken` bị tiêu TRƯỚC khi bridge kịp hoãn ⇒ nhánh `broken` XOÁ nghỉ chứ không DỜI nghỉ; bảo toàn chỉ được khai bằng bất đẳng thức",
      "evidence": "src/gsm_sim/behavior.py:161-164 (`actor.meals_taken += 1` rồi mới `return REST`) — bridge được hỏi SAU (world.py:1037) nên cờ đã tiêu; sau `broken` (world.py:49-66 ⇒ `rest_commit_broken=True`) nhánh nghỉ-ăn không bắn lại được, chỉ còn `fatigue > 1.0 & rng < 0.3` (behavior.py:167). Bảo toàn khai ở sim_metrics.py:365 và assert ở tests/test_rest_commit.py:243 đều là `made ≥ kept+broken+cleared`.",
      "detail": "Đo: 1 `broken` / 12 ngày-đội; `DANGLING = made − kept − broken − cleared` = 0 ở CẢ 12 ngày-đội ⇒ giả thuyết của tôi rằng cam kết treo im lặng tới END_SHIFT (gate không được gọi vì END_SHIFT không nằm trong {WAIT,RELOCATE,REST}) là KHÔNG QUAN SÁT ĐƯỢC ở các seed này — tôi hạ nó xuống 'cấu trúc cho phép, thực nghiệm chưa thấy'. Phần CÒN ĐỨNG: không invariant nào đòi Σrest_min được BẢO TOÀN (dời) thay vì giảm (xoá), nên nếu tần suất `broken` tăng (ví dụ khung đích rơi vào giờ đông hơn — chính issue #1), kênh sẽ mua thu nhập bằng nghỉ bị xoá mà sổ sách vẫn khớp bất đẳng thức. Ranh giới: đây KHÔNG phải đề nghị tối ưu sức khoẻ; là đòi hỏi objective không được ăn gian một vế nó tuyên bố là bảo toàn.",
      "severity": "THẤP",
      "confidence": "TB",
      "cung_lop_station_choice": false
    }
  ],
  "extension_proposals": [
    {
      "title": "Cổng HIỆU CẦU: chỉ hoãn khi demand(giờ đích) ≤ demand(giờ hiện tại) − gap_min",
      "action_executable": "Không đổi action (`rest_commit_due_min` + `rest_commit_gate` đã thi hành thật, đo được `kept > 0`). Chỉ thêm một điều kiện trước :932: `d_now = Σ demand_hint_fn(actor, hour)`, `d_tgt = Σ demand_hint_fn(actor, target)` chuẩn hoá cùng đỉnh; nếu `d_tgt > d_now − gap_min` ⇒ `return False, 'no_demand_gain', None` + log veto",
      "solver_dua_tren": "`world._actor_demand_hint` đã tính ở world.py:860 cùng vòng lặp; `idle_reduction` đã trả `demand_by_hour`. 0 số bịa, không solver mới",
      "chi_phi_uoc": "nhỏ",
      "ky_vong": "Khử ĐÚNG vế thiếu cùng-lớp-station-choice; 3/15 lượt sai dấu về 0. Failing test trước: hoãn 11h→12h với di(11)=0,375 < di(12)=0,500 phải bị chặn"
    },
    {
      "title": "S7 chọn khung theo argmin(demand) trên tập giờ TỚI ĐƯỢC, thay argmax(idle sunk)",
      "action_executable": "Không đổi action. Thêm `candidate_hours` vào `idle_reduction_input` (dẫn xuất từ now, `rest_defer_max_min`, `shift_end_min`, `REST_MAX_MINUTES`); trong `solve` đổi khoá sort từ `-idle_min` sang `(demand_index, -idle_min)` và lọc theo `candidate_hours` nếu có",
      "solver_dua_tren": "Chính `idle_reduction` (vài dòng ở :74-78); mọi biến đã có ở call-site",
      "chi_phi_uoc": "nhỏ",
      "ky_vong": "Sửa gốc tỷ lệ 62% kế hoạch BẤT KHẢ (đo day1: 56/90) ⇒ liều can thiệp từ 1-3% lên mức đo được. Failing test trước: tài xế meal_hour=11, giờ 13 có demand thấp nhất trong tầm ⇒ target phải là 13, không phải 5"
    },
    {
      "title": "Hoàn tất ADV-08 ở hai CỔNG + đưa thời lượng nghỉ vào ràng buộc cuối ca",
      "action_executable": "`:913` → `rest_deferred_min + (minutes_to − now_min % 60) > rest_defer_max_min`; `:911` → `due + REST_MAX_MINUTES > shift_end_min` ⇒ reason MỚI `rest_would_cross_shift_end` (giữ mẫu số adherence theo khuôn `infeasible_world_end` của shift_extend, D-M3-01)",
      "solver_dua_tren": "Không cần solver — hai số đã có trong hàm; `REST_MAX_MINUTES` là hằng module world.py:46 (import hoặc chuyển vào config cùng nguồn sự thật, khuôn D-M3-05)",
      "chi_phi_uoc": "nhỏ",
      "ky_vong": "Ngân sách 120′ nghĩa đúng như ADV-08 đã chốt; hết cảnh nghỉ trườn qua giờ kết ca. Bảng veto tách được 'hết ngân sách' khỏi 'nghỉ không vừa ca'"
    },
    {
      "title": "Invariant BẢO TOÀN NGHỈ + event `advice_rest_deleted`",
      "action_executable": "Ở nhánh `broken` (world.py:49-66 / :877-879): phục hồi quyền nghỉ theo lịch (`actor.meals_taken -= 1`) HOẶC log `advice_rest_deleted` log-only (không decision_id, không mẫu số adherence — khuôn `advice_rest_veto`); thêm khoá `commit_open_eod_n` vào `rest_rails_audit` và đổi bất đẳng thức thành ĐẲNG THỨC `made == kept + broken + cleared + open_eod`",
      "solver_dua_tren": "Không cần solver; sổ cam kết đã có ở sim_metrics.py:360-377",
      "chi_phi_uoc": "nhỏ",
      "ky_vong": "Không thể mua thu nhập bằng nghỉ bị XOÁ mà sổ vẫn khớp. Giữ sức khoẻ NGOÀI objective: đây là kế toán, không phải biến tối ưu"
    },
    {
      "title": "Estimator PHẠM VI SỰ KIỆN thay Δ tổng đội cho kênh này",
      "action_executable": "Không thêm action. Chấm điểm chỉ trên cửa sổ `[t_defer, commit_hour·60 + 60)` của CHÍNH tài xế được can thiệp: offers/accepts/payout trong cửa sổ, đối chiếu cùng cửa sổ ở arm A. Dùng `decision_id` (world.py:1056) + segment `reason='rest_defer'` (world.py:1061) đã tồn tại",
      "solver_dua_tren": "`checkpoint_trace` + `decision_id` + `_seg` đã có; kèm vá vị trí RNG của `D-M3-20` (rút `alt_action_fn` ở CÙNG điểm ở cả hai arm) để CRN sống sót",
      "chi_phi_uoc": "vừa",
      "ky_vong": "Đưa SNR từ 0,01-0,24 lên vùng đo được; đồng thời làm `REST_TOTAL_DROP_TOL=2%` có nghĩa lại (hiện ~8× dưới nhiễu)"
    },
    {
      "title": "MEAL-TIMING (D-E4-05) đặt CHỦ ĐỘNG đầu ca — đúng chỗ cơ chế cam kết đã sẵn sàng",
      "action_executable": "Đầu ca (hoặc lần consult đầu), đặt luôn `rest_commit_due_min` = đầu giờ tốt nhất trong `[meal_hour − 2, meal_hour + 2] ∩ candidate_hours`, thay vì CHỜ bản năng đề xuất REST rồi mới phủ quyết. Cơ chế thi hành (`rest_commit_gate`) đã chứng minh sống (`kept > 0`, 15/15 lượt quan sát)",
      "solver_dua_tren": "`idle_reduction.demand_by_hour` cho vế cầu + `policy.trip_points(hour)` cho vế điểm peak ×2 (config :252-255) — cả hai đã có, agent không tự bịa số",
      "chi_phi_uoc": "vừa",
      "ky_vong": "Xoá bài toán reachability theo CẤU TRÚC (không còn phụ thuộc giờ bản năng đòi nghỉ); biến một phủ-quyết-phản-ứng thành một LỊCH. Đây là mở rộng có giá trị cao nhất còn trống của họ REST"
    },
    {
      "title": "Khai tử hoặc hồi sinh `soc_low` tường minh",
      "action_executable": "Hoặc (a) bỏ `soc_low` khỏi `REST_RAILS` (sim_metrics.py:329) + xoá lý lẽ đã hết đường chạy ở advice_bridge.py:884, thêm test khẳng định nó KHÔNG bao giờ bắn từ world (khuôn `test_go_swap_khong_bi_hoan_du_kenh_bat`); hoặc (b) làm nó CÓ NGHĨA: kiểm `soc_pct − ước_tiêu_pin_relocate_trong_cửa_sổ ≤ threshold` — rail này TỚI ĐƯỢC và đồng thời định giá vế SOC mà alt-relocate đang đốt miễn phí",
      "solver_dua_tren": "`_pct_per_km` / `cell_distance_km` đã dùng ngay nhánh relocate (world.py:1127-1130); `terms_active`/config làm nguồn ngưỡng",
      "chi_phi_uoc": "nhỏ",
      "ky_vong": "`veto_fired_n` hết bị pha loãng bằng hằng 0; tầng 5 lấy lại khả năng tố giác đòn xoá-lan-can trên rail này"
    }
  ],
  "notes_cau_hoi_rieng": {
    "q1_bai_toan_dang_giai": "Như-đã-implement: KHÔNG phải bài toán tối ưu. Objective rỗng; action space = {hoãn nghỉ tới đầu giờ X, không hoãn} với X = argmax(idle quá khứ | demand ≤ 0,5); constraint = 4 lan can (1 chết) + trần 120′ + nhịp + coin + 'alt phải khác WAIT'. Bài toán ĐÚNG lẽ ra là: chọn giờ nghỉ h* cực đại hoá [λ(h_now) − λ(h*)] × rest_min − chi phí alt-action, s.t. h* trong tầm ngân sách và nghỉ vừa trong ca, với sức khoẻ là CỔNG MỘT CHIỀU (§1.2b) chứ không phải vế trong hàm.",
    "q2_bien_sim_biet_ma_kenh_bo_qua": "Nặng nhất: `demand_hint_fn` và `hour` được TRUYỀN VÀO `should_defer_rest` nhưng trên đường sống (planned_rest_hour) KHÔNG DÙNG lần nào — short-circuit ở :848-849 bỏ qua cả solver. Kế: giá của alt-action (travel/SOC/ra khỏi pool IDLE), thời lượng nghỉ 20-45′, `trip_points(hour)`, và tính khả-thi của giờ đích lúc S7 chọn.",
    "q3_math": "Sai (đơn vị/mốc quy chiếu): `minutes_to` đo giữa hai ĐẦU GIỜ dùng cho hai cổng, còn sổ cộng `minutes_to − now%60` — lệch tới 59′. Ràng buộc BIND SAI CỬA: cổng cuối ca thiếu thời lượng nghỉ. Cận thị: chỉ so một giờ đích duy nhất do memory hôm qua áp đặt, không so với giờ hiện tại. Kỳ vọng vs realized: cam kết coi giờ X chắc chắn rảnh; `broken` biến DỜI thành XOÁ. Không có phương sai ở đâu cả — nhưng khác S2/shift_extend, ở đây vấn đề không phải Jensen mà là KHÔNG CÓ hàm giá trị để mà lấy kỳ vọng.",
    "q4_mo_rong_neo_duoc": "Cơ chế thi hành đã SỐNG và là tài sản đáng dùng: `rest_commit_due_min` + `rest_commit_gate` ép được nghỉ thật (kept > 0, 15/15 lượt quan sát giữ được cam kết). Thứ còn thiếu là ĐẦU VÀO quyết định. Ưu tiên: (1) cổng hiệu cầu, (2) S7 chọn theo argmin(demand) trên tập tới-được, (6) meal-timing chủ động — cả ba dùng đúng action đó và đúng hai solver/analytics đã có (`idle_reduction`, `_actor_demand_hint`, `policy.trip_points`).",
    "q5_lop_loi_objective_thieu_ve": "CÓ, ở dạng cực đoan nhất trong 12 item: station_choice còn có argmin để thêm vế, mm-04 không có hàm nào cả. World định giá cuốc mất ∝ λ tại giờ nghỉ; kênh định giá 'giờ tôi đã chờ nhiều nhất, miễn là ≤ 0,5 đỉnh'. Bằng chứng chiều: 3/15 lượt hoãn đi SAI DẤU theo chính tín hiệu của nó. Thêm hai vế world định giá mà objective không có: RELOCATE làm tài xế ra khỏi pool chào đơn (world.py:628) và trừ pin thật (world.py:1130).",
    "no_chi_cite_khong_bao_lai": "D-M3-20 (alt_action_fn rút RNG trước cadence/coin ⇒ arm đối chứng bẩn — tôi chỉ thêm ĐO hệ quả: ngày 0 can thiệp lệch −28.928 VND/−7 cuốc); Q-16 (kênh giữ TẮT vì hại sức khoẻ); D-E4-05 (meal-timing chưa làm); D-M3-04-FIX (cam kết — cơ chế này đo được là sống); D-SIM-10/UPDATE-050 (đường nội-ngày inert — thêm số: 0/3 seed có defer ở day0); D-M3-06 (nhánh swap/charge chết — đây là nguyên nhân làm rail `soc_low` mồ côi); D-M3-19 (mẫu số online_min ngậm phút nghỉ); D-M3-01 (mẫu số adherence).",
    "gia_thuyet_TU_BAC_BO": "(a) `_demand_index` bị CENSOR bởi cung ⇒ vòng lặp tự-củng-cố: SAI — nó đọc `result.orders` = đơn SINH RA, không phải đơn phục vụ; vấn đề thật là chiều NGƯỢC (phình tập thông tin). (b) Gọi `demand_hint_fn` cho 24 giờ làm bẩn dòng RNG chung: SAI — `_actor_demand_hint` dùng `default_rng` riêng theo (seed,actor,hour,cell) + cache. (c) Cam kết treo im lặng tới END_SHIFT rồi xoá nghỉ không dấu vết: cấu trúc CHO PHÉP (gate không được gọi ở nhánh END_SHIFT) nhưng `DANGLING = 0` ở CẢ 12 ngày-đội ⇒ hạ xuống 'chưa quan sát được', không báo như bug. (d) `due` có thể ở quá khứ: SAI — `minutes_to ≥ 60` nên `due > now` luôn.",
    "chua_kiem_chung": "Tần suất nhánh 'nghỉ trườn qua shift_end' (mẫu kept chỉ 15 lượt, chưa instrument riêng). Δλ thật (cuốc/giờ) tương ứng với một đơn vị demand_index — tôi ước bằng tỷ lệ tuyến tính, chưa đo hồi quy. Hàng seed 7001/day3 bị cắt khỏi output nên tổng lượt hoãn quan sát là 15, không phải toàn bộ 3×3 ngày.",
    "evidence_labels": "Mọi con số trong file này là ĐO trên probe read-only (3 seed × 4 ngày × 2 arm, `configs/pilot_dongda.yaml`, MOCK data) hoặc SUY TỪ CODE có file:line. Không số nào lấy từ artifact cũ. Ước lượng giá trị/lượt hoãn (1-5k VND) là TÍNH TAY từ payout/cuốc=23.841 và |Δdemand_index| đo được — nhãn ASSUMPTION, confidence TB."
  }
}
```

## Đề xuất bước tiếp (khi được duyệt)

1. `cp` khối JSON trên vào `research/audit/2026-08-06-math-model-audit/mm-04-rest-family.json`.
2. Không sửa code trong cycle này — 3 finding CAO cần qua `mm-13-refute.json` trước khi vào kết luận
   (luật của README audit dir: chưa phản biện thì không được vào `00-SUMMARY.md`).
3. Ứng viên nợ MỚI để mở trong TODO/DEFERRED nếu phản biện giữ: rail `soc_low` chết,
   thiếu cổng hiệu cầu, hai cổng chưa migrate ADV-08.
