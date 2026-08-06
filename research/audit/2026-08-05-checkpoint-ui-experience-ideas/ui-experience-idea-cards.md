# AdviceCheckpoint — từ simulator evidence thành trải nghiệm UI tài xế

- **Ngày:** 2026-08-05
- **Kế thừa:** UPDATE-148 và `research/audit/2026-08-05-checkpoint-scenario-discovery/`
- **Phạm vi:** research/ideation; không sửa runtime, policy, cadence, solver, Web hay LLM
- **Evidence:** Web-demo seeds 1000–1004 (450 actor-run), corpus L1R MOCK 90 ngày và exact
  storylines seed 1000. Mọi số là SIMULATED/MOCK trừ khi ghi khác.

## 1. Executive synthesis

Phát hiện sản phẩm quan trọng nhất không phải “có thể thêm nhiều card”, mà là AdviceCheckpoint
có thể trở thành **bộ nhớ hành trình của ca**:

1. Trước ca, hệ thống ghép kế hoạch, năng lượng và quyền lợi thành một bản đồ có giới hạn rõ.
2. Trong ca, hệ thống không chỉ phản ứng event; nó nhận ra episode: pin xuống nhanh, chờ lặp,
   plan đổi nhiều lần, thực tế lệch plan, hoặc nhiều mục tiêu bắt đầu xung đột.
3. Hệ thống giữ hai trục riêng: **Bây giờ** và **Sắp tới**. Một plan revision được giải thích bằng
   delta của facts, không bằng một thông báo mới thiếu ngữ cảnh.
4. Sau hành động, UI chỉ nói điều đã quan sát: “có swap segment”, “có nghỉ”, “có checkpoint mới”.
   Nó không biến `accepted` hay sự trùng thời gian thành causal effect.
5. Sau ca và qua nhiều ngày, hệ thống so tài xế với chính lịch sử của họ, không ép mọi persona
   vào một nhịp chung.

Đầu ra cụ thể là **33 Idea Cards** bên dưới. Cả 33 đều là composite/rolling-window hoặc journey
synthesis; ít nhất 10 card dùng plan-versus-actual/journey history, 7 card dùng multiday/profile
và hơn 25 card kết hợp từ hai nhóm dữ liệu trở lên. Không card nào khuyên nhận, từ chối hoặc hủy
một cuốc cụ thể.

## 2. Cách đọc Idea Cards

- **COMPOSITE/ROLLING:** hình thành từ nhiều signal hoặc cửa sổ, không phải event acknowledgment.
- **PLAN/JOURNEY:** dùng plan revision, execution segment hoặc before-versus-after.
- **MULTIDAY/PROFILE:** dùng history cá nhân/DriverMemory; không cohort stereotype.
- **MULTI-SOURCE:** ghép ít nhất hai nhóm như plan+SOC, journey+policy hoặc income+mission.
- Coverage là khả năng tạo candidate dưới **research probe**, không phải số card nên hiển thị.
- Các ngưỡng 30′/60′/90′/120′, 15 điểm phần trăm và ±20% baseline đều chưa phải policy.

Portfolio xuyên ca được hình dung như sau:

```text
Brief đầu ca
→ current-plan strip luôn có nhưng không interrupt
→ 2–4 nudge thật sự cần hành động
→ passive/composite insight cập nhật theo episode
→ Why giải thích plan revision
→ recap cuối ca
→ multiday analytics khi tài xế chủ động mở
```

## 3. Idea Cards — trước ca và đầu ca

### IC-01 — La bàn ca hôm nay

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** trước ca không biết nên theo dõi mốc nào, khi nào cần nghỉ/đổi pin và đâu là
  phần chắc chắn so với forecast.
- **Raw evidence:** `Actor.shift_start_min/shift_end_min/soc_pct/points`; first S2 schedule và
  future plan; S1 policy tiers; mission catalog/progress; checkpoint numbers/caveats
  (`entities.py:27`, `shift_dp.solve`, `bonus_feasibility.solve`, `checkpoint.py`).
- **Derived-state logic:** journey synthesis tại đầu ca: lấy state đầu tiên + first valid plans,
  gom các boundary theo thời gian, loại signal thiếu freshness và giữ provenance từng section.
- **Kết luận:** “ca có ba mốc cần chú ý: năng lượng, nghỉ và quyền lợi; chưa có việc cần làm ngay”.
- **UI:** brief một lần, vì đây là orientation chứ không phải interruption.
- **Nội dung mẫu:** “Ca 09:10–20:30. **Bây giờ:** online. **Sắp tới:** dự kiến xem lại pin lúc
  13:00–14:00; khung nghỉ đang được tính lại. Bạn có 55 điểm hướng tới mốc 30.000đ. Các mốc là
  mô phỏng từ lịch sử, không bảo đảm thu nhập.”
- **Giá trị đặc biệt:** một màn hình kể cả ca bằng plan + policy + uncertainty, thay vì ba push rời.
- **Khả thi:** SMALL-WIRING trong simulator; product cần trusted shift/SOC và policy/mission source.
- **Coverage:** đủ input cấu trúc cho 450/450 actor-run; product S2 vẫn fail-closed nếu thiếu SOC.
- **Risk/guard:** information overload và stale plan; tối đa 3 mốc, source badge, update strip thay
  vì phát brief lần hai.

### IC-02 — Khung hoạt động mạnh của riêng bạn

- **Loại:** ROLLING · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** lịch chung “giờ cao điểm” không cho biết khung nào thường hiệu quả với chính họ.
- **Raw evidence:** `driver_orders_rush_hours` normal/rush orders+commission, online-hours history,
  trip timestamps và DriverMemory payout/trips history (`from_l1r.py`, `multiday.py:52`).
- **Derived-state logic:** personalized baseline trên các ngày so sánh được; tính share trip/payout
  theo khung, yêu cầu minimum history và chỉ gọi pattern khi ổn định qua nhiều ngày.
- **Kết luận:** “khung chiều thường đóng góp tốt hơn cho riêng bạn; đây là pattern lịch sử”.
- **UI:** brief chip + expandable analytics; không popup trong lúc chạy.
- **Nội dung mẫu:** “Trong lịch sử mô phỏng gần đây, 16:00–19:00 đóng góp tỷ trọng cuốc cao hơn
  các khung khác của bạn. Đây là quan sát quá khứ, không phải dự báo nhu cầu hôm nay.”
- **Giá trị đặc biệt:** cá nhân hóa theo driver, không gửi mọi người vào cùng một khung.
- **Khả thi:** REAL-DATA-READY về daily table shape; service/freshness và comparable-day contract
  vẫn cần xác nhận.
- **Coverage:** 150/150 profile MOCK có rush-split history; độ ổn định pattern chưa đo.
- **Risk/guard:** herding và selection bias; chỉ analytics, không target zone, không khẳng định causal.

### IC-03 — Nhịp 90 phút đầu

- **Loại:** ROLLING · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** đầu ca chậm nhưng không biết đó là bất thường hay nhịp quen thuộc của mình.
- **Raw evidence:** journey income curve, completed trips, online/idle minutes trong 90′ đầu;
  rolling comparable-day payout/trip/online history (`journey.py:160,201`, daily L1R tables).
- **Derived-state logic:** so pace 90′ đầu với phân phối 7–30 ngày cùng loại ca; chỉ đưa descriptive
  band nếu đủ history, không ngoại suy tổng thu nhập cuối ca.
- **Kết luận:** “đầu ca đang chậm hơn vùng quen thuộc của bạn, nhưng thời gian còn lại vẫn đủ để
  tiếp tục plan hiện hành” hoặc “đang trong vùng thường thấy”.
- **UI:** passive insight dưới plan strip; chỉ nudge nếu solver/rule đưa action mới.
- **Nội dung mẫu:** “90 phút đầu: 2 cuốc, 41.000đ payout — thấp hơn vùng thường thấy của chính
  bạn. **Bây giờ:** giữ kế hoạch hiện tại. Hệ thống sẽ đánh giá lại khi facts thay đổi.”
- **Giá trị đặc biệt:** nhận biết deviation sớm mà không tự phát minh recommendation.
- **Khả thi:** NEW-INTERNAL-CONTRACT cho intraday ledger; daily history shape đã có.
- **Coverage:** UNMEASURED; phép đo cần replay income curve theo mốc 90′ và join comparable days.
- **Risk/guard:** anxiety và promise; không đỏ/khẩn cấp, không forecast payout cuối ca.

### IC-04 — Bản đồ quyền lợi trong ca

- **Loại:** COMPOSITE · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** mission, bonus ngày và chương trình tân binh có thể cùng tồn tại nhưng mỗi nơi
  hiển thị một kiểu, khiến tài xế nhầm điều kiện.
- **Raw evidence:** S1 points/eligibility, mission catalog/progress/completion, newbie tenure/floor/
  topup, policy versions và shift time (`world.py:553,768`; `mission_knapsack.py`).
- **Derived-state logic:** incentive-stack projection; giữ mỗi chương trình là một entity/version,
  sort theo expiry và đánh dấu feasible/at-risk/completed, không cộng phần thưởng chưa chắc chắn.
- **Kết luận:** “mission A đã xong; mốc ngày còn theo dõi; top-up chỉ được xác nhận khi settlement”.
- **UI:** brief + passive progress group, không ba popup cạnh tranh.
- **Nội dung mẫu:** “Quyền lợi hôm nay: ✓ Mission sáng +20.000đ đã ghi nhận; mốc ngày đang ở
  55 điểm; chương trình tân binh sẽ được đối soát cuối ca. Không cộng phần chưa xác nhận vào payout.”
- **Giá trị đặc biệt:** giải quyết xung đột ngữ nghĩa giữa nhiều policy/solver bằng provenance.
- **Khả thi:** SMALL-WIRING trong sim; product cần authoritative mission/newbie policy contracts.
- **Coverage:** bonus READY + mission cùng ca ở 130/450 actor-run; newbie event ở 76 actor-run.
- **Risk/guard:** policy stale và double-count money; version/effective date bắt buộc, ledger tách
  confirmed/projected.

### IC-05 — Lộ trình năng lượng của ca

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** SOC hiện tại không cho biết khi nào pin trở thành ràng buộc của kế hoạch.
- **Raw evidence:** SOC snapshots, S2 current/future schedule, shift remaining, trip/empty segments,
  swap/charge events và caveats (`World.log`, `shift_dp.solve`, checkpoint future plan).
- **Derived-state logic:** ghép SOC hiện tại với future action windows và observed consumption;
  tạo state `comfortable / prepare / action-now / recovering`, re-evaluate khi plan revision material.
- **Kết luận:** “chưa cần dừng; kế hoạch hiện dành một cửa sổ đổi pin sau” hoặc “window đã tới”.
- **UI:** current-plan strip cố định, mở rộng thành energy timeline; nudge chỉ ở `action-now`.
- **Nội dung mẫu:** “**Bây giờ:** online, SOC 58%. **Sắp tới:** chuẩn bị đổi pin 13:00–14:00.
  Cửa sổ có thể đổi khi quãng chạy thực tế khác forecast.”
- **Giá trị đặc biệt:** dự báo ràng buộc trước khi thành sự cố và phân biệt current/future.
- **Khả thi:** SMALL-WIRING trong sim; NEW-INTERNAL-CONTRACT cho product SOC/activity.
- **Coverage:** current≠future xuất hiện ở 450/450 actor-run; future-SWAP ở 387/450.
- **Risk/guard:** stale SOC và false precision; REAL/LIVE only, validity visible, moving gate.

## 4. Idea Cards — năng lượng và sự cố

### IC-06 — Chuẩn bị đổi pin trước điểm gãy

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** chỉ biết đổi pin khi SOC đã thấp làm mất cơ hội tiếp tục ca.
- **Raw evidence:** suppressed S2 ONLINE record có future SWAP window, SOC, remaining shift,
  recent energy events; observed `go_swap` (`checkpoint future_plan`, `world.py:635,1102`).
- **Derived-state logic:** không unsuppress ONLINE; chỉ tạo `prepare` khi future SWAP tồn tại ổn định
  qua revision, window đủ mới và có material energy evidence.
- **Kết luận:** “tiếp tục online bây giờ, nhưng chuẩn bị đổi pin trong window đã tính”.
- **UI:** low-interruption nudge một lần cho mỗi material window; sau đó pin vào plan strip.
- **Nội dung mẫu:** “**Bây giờ:** tiếp tục online. **Sắp tới:** đổi pin 15:00–16:00. Pin hiện chưa
  yêu cầu dừng ngay; kế hoạch có thể cập nhật theo quãng chạy.”
- **Giá trị đặc biệt:** biến maintenance revisions thành một lời báo trước có kiểm soát, không spam.
- **Khả thi:** NEW-INTERNAL-CONTRACT/topic trong sim; product cần trusted SOC.
- **Coverage:** 2.637 future-SWAP record/387 actor-run ở UPDATE-148; 349 distinct future windows
  thực sự có swap trong window, phủ 274/450 actor-run theo probe mới.
- **Risk/guard:** lặp theo poll và hiểu nhầm “đổi ngay”; dedup theo semantic window, code-owned
  Bây giờ/Sắp tới, proactive budget giữ nguyên.

### IC-07 — Pin đang hao nhanh hơn kế hoạch

- **Loại:** ROLLING · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** SOC vẫn trên ngưỡng nhưng xu hướng hao đã làm future plan cũ kém phù hợp.
- **Raw evidence:** trace SOC snapshots, occupied/empty/relocate segments, environment range factor,
  old/new S2 plans và shift remaining.
- **Derived-state logic:** so realized SOC delta trên cửa sổ với delta implied bởi plan/baseline;
  yêu cầu nhiều snapshot và material deviation, không chỉ một SOC reading.
- **Kết luận:** “năng lượng đang giảm nhanh hơn plan; window đổi pin đã được kéo sớm” — chỉ khi
  solver revision thật sự đổi window.
- **UI:** composite explanation gắn vào plan revision, không một card threshold riêng.
- **Nội dung mẫu:** “Trong 75 phút gần nhất, SOC giảm nhanh hơn nhịp kế hoạch. Window đổi pin đã
  chuyển từ 16:00–17:00 sang 15:00–16:00. Đây là cập nhật mô phỏng, không phải cảnh báo lỗi pin.”
- **Giá trị đặc biệt:** giải thích *vì sao* plan đổi bằng observed trend + solver output.
- **Khả thi:** SMALL-WIRING trong sim; NEW-INTERNAL-CONTRACT cho product telemetry.
- **Coverage:** UNMEASURED; cần read-only SOC-slope probe giữa consecutive snapshots và revision.
- **Risk/guard:** sensor noise, temperature confounding; smoothing, source/freshness, không chẩn đoán
  sức khỏe pin.

### IC-08 — Vòng lặp bỏ lỡ vì pin

- **Loại:** ROLLING · REPEATED-PATTERN · MULTI-SOURCE.
- **Vấn đề tài xế:** một lần thiếu SOC có thể là ngẫu nhiên; lặp lại cho thấy kế hoạch năng lượng
  đang tạo gián đoạn thực sự.
- **Raw evidence:** nhiều `order_skipped_soc` với `soc_pct/need_km`, S2 plan revisions, swap events
  và shift remaining (`world.py:635`).
- **Derived-state logic:** nhóm SOC-skip trong 60–120′ thành một episode; chỉ insight khi lặp ≥2
  hoặc khi chưa có recovery action, tuyệt đối không hiển thị thông tin đơn cụ thể.
- **Kết luận:** “pin thấp đã làm gián đoạn cơ hội nhiều lần; nên theo action/window energy hiện tại”.
- **UI:** composite nudge nếu safe và solver current SWAP; nếu không, passive awareness.
- **Nội dung mẫu:** “Trong 90 phút gần đây, hệ thống ghi nhận 2 lần SOC không đủ cho hành trình
  được mô phỏng. **Bây giờ:** theo kế hoạch đổi pin hiện tại. Không có lời khuyên nhận cuốc cụ thể.”
- **Giá trị đặc biệt:** phân biệt noise một event và pattern có ý nghĩa.
- **Khả thi:** SMALL-WIRING trong sim; product cần aggregate dispatch/SOC reason contract.
- **Coverage:** 121 event/95 actor-run; repeated ≥2 ở 20 actor-run.
- **Risk/guard:** privacy/dispatch boundary và shame; aggregate only, neutral wording, no order ID.

### IC-09 — Ca đã phục hồi sau đổi pin?

- **Loại:** COMPOSITE · PLAN/JOURNEY · BEFORE-AFTER.
- **Vấn đề tài xế:** sau swap không biết hệ thống đã quan sát được việc đó và plan mới thay đổi ra sao.
- **Raw evidence:** pre-swap SOC/plan, swap segment/wait, post-swap SOC, subsequent S2 plan và
  trip/activity segments.
- **Derived-state logic:** đóng energy episode khi swap hoàn tất; so before/after state và plan,
  không so payout causal; relation chỉ `observed/coincident` trừ explicit intervention.
- **Kết luận:** “swap đã được ghi nhận, SOC phục hồi và plan quay về ONLINE” hoặc “plan vẫn còn
  ràng buộc khác”.
- **UI:** passive success state + expandable timeline; không popup chúc mừng bắt buộc.
- **Nội dung mẫu:** “Đã ghi nhận đổi pin lúc 13:23. SOC sau đổi: 100%. Kế hoạch hiện chuyển về
  online; window tiếp theo sẽ được tính từ trạng thái mới. Đây là hành động quan sát được, không
  phải bằng chứng lời khuyên đã gây ra kết quả.”
- **Giá trị đặc biệt:** theo recommendation tới execution rồi quay lại planning loop.
- **Khả thi:** SMALL-WIRING trong sim; NEW-INTERNAL-CONTRACT cho observed swap/SOC product.
- **Coverage:** 115 recovery episode sau SOC-skip trong 90′, phủ 90 actor-run; 6 episode/5 actor-run
  không có swap trong cửa sổ probe.
- **Risk/guard:** causal overclaim; label observed action, không tính uplift.

### IC-10 — Ma sát đổi pin

- **Loại:** ROLLING · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** kế hoạch nói “đổi pin” nhưng thực tế queue/failure có thể làm ca lệch thêm.
- **Raw evidence:** `go_swap/swap_done/swap_failed`, `wait_min`, station state, subsequent plan
  revisions (`world.py:1102-1154`, `entities.Station`).
- **Derived-state logic:** một episode từ go_swap tới success/fail; so duration với plan window và
  nhận biết repeated friction trong ca.
- **Kết luận:** “việc đổi pin mất lâu hơn dự kiến và plan đã được cập nhật” — không gợi ý trạm khác
  khi thiếu live capacity.
- **UI:** passive incident explanation + recap section.
- **Nội dung mẫu:** “Lần đổi pin vừa rồi mất 13 phút chờ. Hệ thống đã tính lại phần còn lại của ca.
  Chưa có dữ liệu trạm thời gian thực để đề xuất địa điểm khác.”
- **Giá trị đặc biệt:** đưa operational friction vào planning narrative thay vì coi action là tức thì.
- **Khả thi:** SIMULATOR-SHOWCASE; product cần live station/observation contract.
- **Coverage:** 140 friction episode/110 actor-run; xuất hiện thiên về giữa–cuối ca (p50 67,7%).
- **Risk/guard:** stale inventory/herding; không recommend station, show source limitation.

## 5. Idea Cards — kế hoạch, nghỉ và nhịp hoạt động

### IC-11 — Vì sao kế hoạch vừa đổi

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** thấy action/window mới nhưng không biết phần nào của trạng thái đã làm plan đổi.
- **Raw evidence:** immutable old/new checkpoints, fingerprint/future head, numbers/caveats,
  solver-input refs và intervening trace events/segments.
- **Derived-state logic:** deterministic checkpoint diff; chỉ liệt kê changed allowlisted facts và
  sequence quan sát giữa hai revisions, không để presenter suy lý action mới.
- **Kết luận:** “plan đổi từ ONLINE→REST vì remaining shift/rest state thay đổi” hoặc “future SWAP
  được kéo sớm sau energy evidence”.
- **UI:** Why/timeline explanation gắn vào current-plan strip.
- **Nội dung mẫu:** “Kế hoạch đổi lúc 14:05: **trước đó** online tới 16:00; **hiện tại** nghỉ trong
  14:00–15:00. Thay đổi được tính từ trạng thái nghỉ và thời gian ca còn lại; forecast vẫn có bất định.”
- **Giá trị đặc biệt:** giải thích revision bằng artifact thật, không phải LLM kể một lý do chung.
- **Khả thi:** SMALL-WIRING; checkpoint artifacts/refs đã có.
- **Coverage:** 1.224 semantic revisions, phủ 426/450 actor-run; p50 xuất hiện ở 64,5% ca.
- **Risk/guard:** post-hoc causal story; chỉ changed facts có provenance, dùng “được tính lại sau”
  thay “vì event X gây ra”.

### IC-12 — Kế hoạch đang đổi quá nhiều

- **Loại:** ROLLING · PLAN/JOURNEY · REPEATED-PATTERN.
- **Vấn đề tài xế:** nhiều card trái chiều trong thời gian ngắn làm mất niềm tin và tăng cognitive load.
- **Raw evidence:** semantic signatures của consecutive S2 checkpoints, action/future head/windows,
  timestamps và policy suppression history.
- **Derived-state logic:** rolling 120′; nhận biết ≥3 semantic changes, gom thành một trạng thái
  `plan_unstable` thay vì phát từng revision.
- **Kết luận:** “plan đang biến động; UI giữ một plan strip và chỉ thông báo khi ổn định/material”.
- **UI:** passive banner “đang cập nhật kế hoạch”, không actionable nudge.
- **Nội dung mẫu:** “Kế hoạch đã đổi 3 lần trong 2 giờ gần đây. Hệ thống đang giữ hành động hiện tại
  và sẽ chỉ thông báo lại khi window ổn định hơn.”
- **Giá trị đặc biệt:** dùng chính lịch sử recommendation để chống spam, không chỉ cooldown theo topic.
- **Khả thi:** SMALL-WIRING trong checkpoint projection.
- **Coverage:** 92/450 actor-run theo probe 3 semantic changes/120′; thiên về cuối giữa ca (p50 69,8%).
- **Risk/guard:** che mất action khẩn; safety/current-action change luôn vượt stability suppression.

### IC-13 — Thực tế đang lệch kế hoạch

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** action đã lên plan nhưng window trôi qua mà hành động chưa được quan sát.
- **Raw evidence:** READY SWAP/REST/END checkpoint, validity/action window, execution segments/events,
  current actor state và next checkpoint.
- **Derived-state logic:** match canonical action với observed action trong validity; nếu absent,
  phân loại `not_observed`, `late`, `different_action`, không tự gọi là ignore.
- **Kết luận:** “hành động chưa được quan sát trong window; recommendation có thể không còn hiện hành”.
- **UI:** passive plan status; nudge mới chỉ khi solver re-plans.
- **Nội dung mẫu:** “Kế hoạch nghỉ 14:00–15:00 đã hết window nhưng chưa có segment nghỉ được ghi
  nhận. Hệ thống sẽ dùng trạng thái hiện tại để tính plan mới; đây không phải đánh giá tuân thủ.”
- **Giá trị đặc biệt:** tách intent, adherence inference và observed execution.
- **Khả thi:** SMALL-WIRING trong sim; product cần observed activity contract.
- **Coverage:** 125 action-in-validity/109 actor-run; thêm 21 late-within-60′/21 actor-run.
- **Risk/guard:** missing telemetry bị hiểu là tài xế bỏ qua; wording `không quan sát được`, confidence.

### IC-14 — Kế hoạch phục hồi sau gián đoạn

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** sau SOC-skip, cancellation hoặc swap fail, UI chỉ hiện event mà không cho thấy
  hệ thống đã tiếp nhận hậu quả vào plan.
- **Raw evidence:** disruption event, state snapshot sau mutation, next semantic plan revision,
  remaining shift và execution segment.
- **Derived-state logic:** mở episode tại disruption; tìm revision trong cửa sổ 60′; đóng khi plan
  ổn định hoặc action recovery quan sát được.
- **Kết luận:** “sự cố đã được phản ánh trong kế hoạch mới” hoặc “chưa có revision đủ mới”.
- **UI:** timeline explanation nối incident → plan update.
- **Nội dung mẫu:** “Sau lần đổi pin không thành công lúc 14:12, kế hoạch được tính lại lúc 14:31:
  **Bây giờ:** online; **Sắp tới:** đổi pin trong window mới. Chưa có dữ liệu live về hàng chờ trạm.”
- **Giá trị đặc biệt:** kể một feedback loop hoàn chỉnh thay vì alert rời rạc.
- **Khả thi:** SMALL-WIRING trong sim; product phụ thuộc observed disruption/state.
- **Coverage:** 160 disruption→revision episode, phủ 125 actor-run, p50 ở 64,8% ca.
- **Risk/guard:** correlation narrative; dùng sequence language, không causal effect.

### IC-15 — Cửa sổ nghỉ đang trôi

- **Loại:** ROLLING · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** biết cần nghỉ nhưng không nhận ra window dự kiến đang gần hết hoặc đã dời.
- **Raw evidence:** S2/S7 rest window, current state, continuous online/rest history, remaining shift,
  prior rest revisions.
- **Derived-state logic:** theo dõi distance-to-window và revision history; chỉ nudge khi safe state
  và current REST; nếu future REST thì plan strip/passive.
- **Kết luận:** “nghỉ chưa cần ngay nhưng window đã dời” hoặc “window hiện tại đang mở”.
- **UI:** plan-strip countdown không dùng urgency giả; actionable nudge khi current action REST.
- **Nội dung mẫu:** “**Bây giờ:** online. **Sắp tới:** khung nghỉ đã chuyển sang 15:00–16:00 vì
  kế hoạch ca được cập nhật. Khi đang di chuyển, hệ thống sẽ không mở card dài.”
- **Giá trị đặc biệt:** phân biệt future rest với rest-now và giải thích revision.
- **Khả thi:** SMALL-WIRING sim; product cần trusted activity/rest state.
- **Coverage:** 57 REST READY trong 5 seed; 609 rest events/348 actor-run. Window-drift riêng
  UNMEASURED, cần diff consecutive future REST windows.
- **Risk/guard:** health boundary và driving safety; không tối ưu sức khỏe theo payout, safe-state only.

### IC-16 — Nghỉ chủ động hay chỉ đang chờ?

- **Loại:** COMPOSITE · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** idle không có cuốc và nghỉ chủ động trông giống nhau về “không di chuyển” nhưng
  có ý nghĩa khác cho phục hồi và plan.
- **Raw evidence:** inferred idle gaps, explicit rest events/segments, online minutes, S7 planned-rest
  state, confidence (`journey.py:_timeline_of`, `multiday._update_memory`).
- **Derived-state logic:** phân tách observed rest với inferred idle trong cửa sổ; tổng hợp tỷ trọng
  và nhận biết khi planned rest chưa thực hiện dù đã có nhiều idle.
- **Kết luận:** “bạn đã chờ nhiều nhưng chưa có khoảng nghỉ được ghi nhận” — awareness, không health claim.
- **UI:** passive recovery card hoặc recap, không popup.
- **Nội dung mẫu:** “Ca này có 74 phút chờ suy diễn và 18 phút nghỉ được ghi nhận. Hai loại thời
  gian không được xem là tương đương; kế hoạch nghỉ tiếp theo vẫn dựa trên segment quan sát được.”
- **Giá trị đặc biệt:** hiểu semantics của time, không chỉ cộng phút không hoạt động.
- **Khả thi:** SMALL-WIRING sim; NEW-INTERNAL-CONTRACT cho activity confidence product.
- **Coverage:** idle≥30′ và rest cùng ca ở 296/450 actor-run; 228 idle→rest episode/176 actor-run.
- **Risk/guard:** inference error; badge `suy diễn`, không chấm điểm sức khỏe/tính chăm chỉ.

### IC-17 — Chuỗi chờ lặp lại

- **Loại:** ROLLING · REPEATED-PATTERN · JOURNEY.
- **Vấn đề tài xế:** nhiều khoảng chờ dài rải rác khó nhận ra khi chỉ nhìn từng transition.
- **Raw evidence:** inferred idle blocks trong `DriverJourney`, session boundaries, recent plan and
  official reposition mission nếu có.
- **Derived-state logic:** gom ≥2 block qua cả ca, so duration/timing; chỉ awareness hoặc rest-planning,
  tuyệt đối không suy ra khu vực tốt hơn nếu thiếu S4/official mission.
- **Kết luận:** “khoảng chờ dài đang lặp; có thể xem lại plan khi an toàn”.
- **UI:** passive composite; expandable timeline hiển thị các block.
- **Nội dung mẫu:** “Ba khoảng chờ dài đã xuất hiện: 10:40–11:20, 12:05–12:43 và 14:10–14:50.
  Hệ thống chưa có signal đủ tin cậy để đề xuất khu vực khác.”
- **Giá trị đặc biệt:** pattern qua cửa sổ thay vì alert “idle 30 phút” đơn giản.
- **Khả thi:** SMALL-WIRING sim; product cần activity/hex feed và confidence.
- **Coverage:** 1.012 block ≥30′/379 actor-run; repeated block ở 289 actor-run.
- **Risk/guard:** spam và blame; một card/episode, neutral wording, no target zone.

### IC-18 — Nhịp hoạt động đang chuyển pha

- **Loại:** ROLLING · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** hiệu suất đầu và cuối ca khác nhau nhưng cumulative total che mất chuyển pha.
- **Raw evidence:** occupied/enroute/relocate/idle timeline blocks, shift midpoint, payout curve và
  current plan.
- **Derived-state logic:** so utilization hai nửa hoặc rolling windows; chỉ gọi `phase shift` khi
  delta material, không kết luận nguyên nhân.
- **Kết luận:** “tỷ trọng thời gian có khách đã đổi đáng kể so với đầu ca”.
- **UI:** passive trend chart + short text, không action nếu không có solver recommendation.
- **Nội dung mẫu:** “Nửa sau ca, tỷ trọng thời gian có khách thấp hơn nửa đầu 18 điểm phần trăm.
  Đây là mô tả hành trình; kế hoạch hiện tại chưa yêu cầu đổi hành động.”
- **Giá trị đặc biệt:** phát hiện thay đổi chế độ trong cùng ca, không chỉ KPI cuối ngày.
- **Khả thi:** SMALL-WIRING sim; NEW-INTERNAL-CONTRACT activity ledger product.
- **Coverage:** probe |delta|≥15 điểm phần trăm bắt 130/450 actor-run.
- **Risk/guard:** arbitrary threshold và confounding ca dài/ngắn; calibrate ≥30 seed, no causal story.

### IC-19 — Quãng chạy rỗng đang tăng

- **Loại:** ROLLING · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** tổng cuốc vẫn tăng nhưng tỷ trọng di chuyển không khách có thể xấu dần.
- **Raw evidence:** enroute/relocate/on-trip segments, distances, energy use and prior personal
  empty-share baseline (`Actor.empty_min`, journey timeline).
- **Derived-state logic:** compare empty share giữa rolling windows/halves; chỉ insight khi tăng
  material và enough movement denominator.
- **Kết luận:** “tỷ trọng di chuyển rỗng tăng; chưa có căn cứ để chỉ định khu vực”.
- **UI:** passive efficiency insight hoặc recap analytics.
- **Nội dung mẫu:** “Tỷ trọng di chuyển không khách ở nửa sau cao hơn nửa đầu 17 điểm phần trăm.
  Hệ thống chưa đưa đề xuất vị trí vì chưa có capacity/live demand đủ tin cậy.”
- **Giá trị đặc biệt:** liên kết operational efficiency với energy, nhưng giữ ranh giới positioning.
- **Khả thi:** SMALL-WIRING sim; NEW-INTERNAL-CONTRACT trip/GPS segments product.
- **Coverage:** rising ≥15 điểm phần trăm ở 99/450 actor-run; overall empty-share≥40% ở 361.
- **Risk/guard:** denominator nhỏ, privacy, herding; minimum active time, aggregate H3, no zone advice.

### IC-20 — Thời gian bị bào mòn bởi cuốc hủy

- **Loại:** ROLLING · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** cuốc hủy sau accept làm mất pickup time/SOC nhưng payout tổng không chỉ ra phần
  thời gian bị mất.
- **Raw evidence:** `order_cancelled_after_accept.wasted_min`, enroute segment, SOC snapshot,
  subsequent plan revision and shift remaining (`world.py:697`).
- **Derived-state logic:** group cancellations trong 120′; sum only observed wasted time, then show
  whether plan was re-evaluated—không gán fault hoặc hypothetical income loss.
- **Kết luận:** “hai lần hủy đã tiêu tốn N phút observed; plan sau đó đã/ chưa đổi”.
- **UI:** passive incident summary + recap.
- **Nội dung mẫu:** “Hai cuốc bị hủy sau khi nhận trong 2 giờ gần đây; ước tính từ event ghi nhận
  19 phút di chuyển đón khách đã dùng. Kế hoạch ca đã được tính lại lúc 14:31.”
- **Giá trị đặc biệt:** nối trip lifecycle tới plan, không chỉ tăng counter cancellation.
- **Khả thi:** SMALL-WIRING sim; production trip lifecycle contract chưa được xác nhận đầy đủ.
- **Coverage:** 224 cancellation/169 actor-run; cluster ≥2 trong 120′ ở 21 actor-run.
- **Risk/guard:** blame và counterfactual money; không nói mất bao nhiêu thu nhập, no order details.

### IC-21 — Nhịp quyết định đơn đang thay đổi

- **Loại:** ROLLING · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** tỷ lệ nhận trong ngày thay đổi theo chuỗi nhưng một daily KPI tới quá muộn và
  một lần decline không có ý nghĩa.
- **Raw evidence:** aggregate matched/declined reasons, acceptance history, bonus eligibility and
  remaining time; không dùng nội dung đơn cụ thể.
- **Derived-state logic:** rolling decision-rate band so với baseline cá nhân; chỉ nối với S1 nếu
  eligibility thật sự material, không khuyên nhận cuốc kế tiếp.
- **Kết luận:** “nhịp nhận đang thấp hơn vùng của bạn và ảnh hưởng điều kiện mốc” hoặc chỉ awareness.
- **UI:** passive progress/Why cho S1, không per-order nudge.
- **Nội dung mẫu:** “Trong cửa sổ gần đây, nhịp nhận thấp hơn vùng lịch sử của bạn. Điều kiện mốc
  hiện có rủi ro; hệ thống không đưa lời khuyên cho bất kỳ cuốc cụ thể nào.”
- **Giá trị đặc biệt:** kết hợp pattern cá nhân + policy consequence, vẫn giữ dispatch boundary.
- **Khả thi:** REAL-DATA-READY daily shape; intraday NEW-INTERNAL-CONTRACT.
- **Coverage:** decline cluster ≥2/120′ ở 101 actor-run; MOCK 90 ngày có 88 driver với ≥2 ngày
  acceptance<0,85 và 130 driver có recovery ngày kế tiếp.
- **Risk/guard:** coercion/fairness; passive wording, no acceptance target unless official policy,
  minimum sample size.

## 6. Idea Cards — tiến độ, thu nhập và cuối ca

### IC-22 — Trạng thái mốc thưởng vừa đổi

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** biết số điểm hiện tại nhưng không biết feasibility đã chuyển từ “đang theo
  kịp” sang “có rủi ro” hay ngược lại.
- **Raw evidence:** S1 reports/checkpoints, points/trips, acceptance/completion, time remaining,
  policy tier/version and personal points/hour history.
- **Derived-state logic:** diff consecutive feasibility states, only material transition; progress
  count alone stays passive, eligibility risk can be actionable.
- **Kết luận:** “mốc vừa chuyển trạng thái do remaining time/rate; không bảo đảm đạt thưởng”.
- **UI:** composite progress card with state-change explanation.
- **Nội dung mẫu:** “Mốc 55 điểm đã chuyển từ ‘đang theo kịp’ sang ‘cần bảo vệ điều kiện’. Bạn còn
  2 giờ 10 phút; payout thưởng chỉ được ghi nhận nếu đủ mọi điều kiện policy.”
- **Giá trị đặc biệt:** giải thích state transition, không phải cứ mỗi cuốc tăng một progress toast.
- **Khả thi:** SMALL-WIRING; S1/policy facts đã có, cần preserve revisions thay vì một snapshot.
- **Coverage:** 198 S1 READY/198 actor-run; transition giữa nhiều S1 states hiện UNMEASURED vì
  current trace chưa giữ đủ material S1 revisions.
- **Risk/guard:** income promise và pressure; source/version, no predicted certainty, one material card.

### IC-23 — Mission, bonus và thời gian đang xung đột

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** hai mục tiêu đều “có lợi” nhưng cùng tranh quỹ thời gian/pin/nghỉ, khiến theo
  từng card riêng có thể mâu thuẫn.
- **Raw evidence:** mission windows/progress/reward, S1 feasibility, S2 schedule/SOC/rest, shift
  remaining and policy caveats.
- **Derived-state logic:** detect overlapping deadlines/resource constraints; solver/rule vẫn sở hữu
  action, composite chỉ trình bày trade-off và canonical primary.
- **Kết luận:** “mission còn cơ hội nhưng energy/rest plan là ràng buộc chính; không cộng reward
  chưa chắc chắn”.
- **UI:** composite progress card; một primary CTA, các mục tiêu khác thành context.
- **Nội dung mẫu:** “Mission còn 2 cuốc trước 18:00; mốc ngày còn 15 điểm. **Bây giờ:** theo kế
  hoạch nghỉ. Hai khoản thưởng chưa được tính vào payout vì điều kiện chưa hoàn tất.”
- **Giá trị đặc biệt:** multi-objective explanation mà không cho LLM tự chọn mục tiêu.
- **Khả thi:** SMALL-WIRING sim; product cần authoritative mission/policy + trusted S2 state.
- **Coverage:** bonus+mission cùng ca ở 130 actor-run; mission gần energy event trong 60′ ở
  196 actor-run.
- **Risk/guard:** over-optimization và unsafe extension; safety/rest dominate, no reward sum until confirmed.

### IC-24 — Thu nhập hôm nay so với chính bạn

- **Loại:** ROLLING · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** payout tuyệt đối không nói hôm nay khác gì so với ca tương tự của chính họ.
- **Raw evidence:** intraday payout curve, daily commission history, online hours, comparable shift/
  weekday, trip count and incentive-source breakdown.
- **Derived-state logic:** prior-only rolling baseline, comparable-day filtering and uncertainty band;
  report deviation, not end-of-day forecast.
- **Kết luận:** “pace hiện thấp/cao hơn vùng quen thuộc của bạn ở cùng thời điểm ca”.
- **UI:** passive insight + expandable trend; never interrupt solely for being below baseline.
- **Nội dung mẫu:** “Sau 4 giờ, payout đã ghi nhận là 128.000đ — thấp hơn vùng giữa của 7 ca tương
  tự gần nhất. Chênh lệch không dự báo tổng cuối ca và có thể do chuỗi cuốc hôm nay.”
- **Giá trị đặc biệt:** personal baseline with future-leak guard, không leaderboard/cohort pressure.
- **Khả thi:** NEW-INTERNAL-CONTRACT intraday ledger; daily history shape REAL-DATA-READY.
- **Coverage:** 150/150 MOCK profiles có ≥7 comparable observations; probe ±20% bắt 4.445/11.771
  eligible days nên threshold này bị coi là quá nhạy, chưa ship.
- **Risk/guard:** regression-to-mean/seasonality/anxiety; comparable-day, confidence band, opt-out.

### IC-25 — Thu nhập hôm nay đến từ đâu

- **Loại:** COMPOSITE · JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** tổng payout trộn tiền cuốc, mission, bonus và newbie, khiến khó hiểu điều gì đã
  thực sự được ghi nhận.
- **Raw evidence:** `DriverJourney` trip/day-bonus/mission/newbie ledger, payout/gross and settlement
  events (`journey.py:160,226`).
- **Derived-state logic:** reconcile sources to canonical payout; separate confirmed from pending;
  no counterfactual attribution.
- **Kết luận:** “payout hiện gồm X từ trip và Y từ incentive đã ghi nhận”.
- **UI:** passive breakdown throughout shift + recap section.
- **Nội dung mẫu:** “Payout 322.500đ: 249.344đ từ cuốc, 20.000đ mission và 53.156đ top-up đã
  settlement. Gross và payout được hiển thị riêng.”
- **Giá trị đặc biệt:** explainable money lineage, một điểm mạnh hơn notification thông thường.
- **Khả thi:** SMALL-WIRING sim; product cần canonical ledger semantics gross/payout/confirmed.
- **Coverage:** ≥2 nguồn income ở 345/450 actor-run; incentive share≥20% ở 210 actor-run.
- **Risk/guard:** double-count/unit semantics; conservation check và policy-source reference.

### IC-26 — Mục tiêu không còn khả thi: bảo toàn ca

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** tiếp tục đuổi một mốc đã không còn khả thi có thể làm plan cuối ca khó hiểu.
- **Raw evidence:** S1 infeasibility reason, time remaining, points/rate, S2 energy/rest constraints,
  policy tier and caveats.
- **Derived-state logic:** solver feasibility is canonical; projection explains which constraints
  bind, then removes incentive pressure from passive portfolio. It does not invent a replacement action.
- **Kết luận:** “mốc không còn feasible theo assumptions hiện tại; chỉ giữ action canonical khác”.
- **UI:** calm composite status, not a red alert; Why shows binding facts.
- **Nội dung mẫu:** “Theo dữ liệu hiện tại, mốc tiếp theo không còn khả thi trong thời gian ca còn
  lại. Hệ thống sẽ không tiếp tục nhắc mốc này. Payout đã ghi nhận không thay đổi.”
- **Giá trị đặc biệt:** biết khi nào nên im lặng, chống gamification spam.
- **Khả thi:** SMALL-WIRING khi S1 emits closed infeasibility reason.
- **Coverage:** UNMEASURED; current checkpoint producer focuses READY recommendation, cần offline
  count of S1 infeasible reports without creating driver-facing records.
- **Risk/guard:** false discouragement; only closed solver verdict with fresh inputs, allow later reactivation.

### IC-27 — Cổng kết ca an toàn

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** gần cuối ca có nhiều áp lực—mốc, mission, pin—nhưng không nên mặc định kéo dài.
- **Raw evidence:** shift boundary, current S2 action, S1 feasibility, SOC/rest state, configured
  extension rails and completed journey.
- **Derived-state logic:** safety/policy gate first; `END`/`EXTEND` only from approved rule/solver;
  UI summarizes constraints and defaults to end when state unavailable.
- **Kết luận:** “kết ca theo kế hoạch” hoặc “extension được solver cho phép tới boundary cụ thể”.
- **UI:** actionable nudge once near boundary; recap begins after terminal event.
- **Nội dung mẫu:** “Ca kết thúc lúc 20:30. **Bây giờ:** kết ca theo kế hoạch. Mốc tiếp theo không
  còn đủ thời gian theo assumptions hiện tại; hệ thống không khuyến khích kéo dài.”
- **Giá trị đặc biệt:** resolves competing objectives under explicit safety rails.
- **Khả thi:** NEW-INTERNAL-CONTRACT/owner policy; shift-extension channel hiện off trong demo.
- **Coverage:** end_shift 357 actor-run + day_end_settle 93 = terminal evidence cho 450; decision
  END/EXTEND candidate UNMEASURED.
- **Risk/guard:** fatigue/earnings pressure; fail-closed, hard extension cap, no LLM action.

### IC-28 — Nhật ký lời khuyên và hành động

- **Loại:** COMPOSITE · PLAN/JOURNEY · LIFECYCLE.
- **Vấn đề tài xế:** sau nhiều card không nhớ hệ thống đã nói gì, mình đã phản hồi gì và hệ thống
  quan sát được hành động nào.
- **Raw evidence:** checkpoint/lease/display identity, displayed/accepted/dismissed/expanded events,
  execution links, segment/event refs and terminal state.
- **Derived-state logic:** chronological join giữ identity riêng; render three lanes:
  `presented`, `intent`, `observed execution`.
- **Kết luận:** “card A đã hiển thị; bạn bấm accepted; swap được quan sát sau đó—không khẳng định causal”.
- **UI:** timeline/detail, pull-only; no popup.
- **Nội dung mẫu:** “13:02 lời khuyên đổi pin được hiển thị · 13:04 bạn chọn ‘Làm theo’ · 13:23
  hệ thống ghi nhận segment đổi pin. Ba mốc này là các sự kiện khác nhau.”
- **Giá trị đặc biệt:** auditability end-to-end hiếm có ở app notification rule-based.
- **Khả thi:** SMALL-WIRING; lifecycle/execution identities đã có.
- **Coverage:** 275/450 actor-run có READY checkpoint với execution link trong trace; presentation
  intent trong simulator là UNMEASURED vì không giả click.
- **Risk/guard:** surveillance/causal overclaim; user-visible history retention, relation label, delete policy.

### IC-29 — Recap hành trình ca

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE.
- **Vấn đề tài xế:** recap KPI đơn thuần không giải thích ca đã thay đổi như thế nào.
- **Raw evidence:** full `DriverJourney`, plan revisions, checkpoint lifecycle, observed execution,
  income sources, energy/rest/idle episodes and policy results.
- **Derived-state logic:** synthesize 3–5 moments material theo time order; separate facts, intentions,
  observations and outcomes; no causal uplift.
- **Kết luận:** “ca có những phase nào, plan đổi ở đâu, hành động nào được quan sát và payout đến từ đâu”.
- **UI:** post-shift recap with expandable chapters.
- **Nội dung mẫu:** “Hôm nay: 15 cuốc, payout 330.636đ. Plan pin đổi hai lần; hai SOC-skip được ghi
  nhận trước lần swap cuối. Bạn xem 2 lời khuyên; 1 hành động tương ứng được quan sát. Không có
  counterfactual để kết luận lời khuyên làm tăng thu nhập.”
- **Giá trị đặc biệt:** giải thích toàn journey thay vì báo tổng cuối ngày.
- **Khả thi:** SMALL-WIRING sim; product cần session/activity/lifecycle retention.
- **Coverage:** recap inputs 450/450; 148 actor-run không READY vẫn có recap hữu ích.
- **Risk/guard:** quá dài/false causality; top moments + expand, explicit evidence labels.

## 7. Idea Cards — nhiều ngày và simulator showcase

### IC-30 — Pattern đang lặp qua nhiều ngày

- **Loại:** ROLLING · MULTIDAY/PROFILE · MULTI-SOURCE.
- **Vấn đề tài xế:** một ngày thấp có thể ngẫu nhiên; chuỗi lặp mới đáng để xem.
- **Raw evidence:** DriverMemory acceptance/completion/payout/trips history, daily KPI/income,
  idle/stoppoint and advice history.
- **Derived-state logic:** consecutive-day/repeated-window detection using only prior days; require
  minimum sample and comparable-day grouping.
- **Kết luận:** “hai ngày liên tiếp cùng pattern xuất hiện; đây là trend cần xem, chưa phải nguyên nhân”.
- **UI:** multiday analytics or weekly recap; no interruptive nudge.
- **Nội dung mẫu:** “Hai ca gần nhất, payout nằm dưới vùng 7 ca tương tự và các khoảng chờ dài
  cùng xuất hiện. Hệ thống chưa đủ dữ liệu để quy nguyên nhân cho khu vực hay quyết định cụ thể.”
- **Giá trị đặc biệt:** memory theo người và repeated-pattern reasoning.
- **Khả thi:** MULTIDAY-REQUIRED; daily tables REAL-DATA-READY về shape.
- **Coverage:** MOCK: 125/150 driver có ≥2 ngày income dưới 80% prior-7 median; 88/150 có ≥2 ngày
  acceptance dưới 0,85. Cả hai threshold chỉ là probe.
- **Risk/guard:** shame, future leak, seasonality; prior-only baseline, neutral wording, opt-in.

### IC-31 — Kế hoạch nghỉ cho ca kế tiếp

- **Loại:** COMPOSITE · MULTIDAY/PROFILE · PLAN/JOURNEY.
- **Vấn đề tài xế:** những khung chờ của hôm nay không được tái sử dụng để chuẩn bị ca sau.
- **Raw evidence:** `DriverMemory.planned_rest_hour`, prior-day idle_by_hour, historical demand index,
  next shift window (`multiday.py:_update_memory`).
- **Derived-state logic:** after-day S7 retrospective computes a candidate rest window; next-day
  brief shows it with source day and confidence, then revalidates against fresh state.
- **Kết luận:** “dựa trên các khoảng chờ hôm qua, một window nghỉ có thể ít gián đoạn hơn hôm nay”.
- **UI:** next-shift brief suggestion, not medical advice.
- **Nội dung mẫu:** “Hôm qua, khung 14:00–15:00 có khoảng chờ dài nhất. Ca hôm nay dự kiến dành
  khung đó để xem xét nghỉ; kế hoạch sẽ đổi nếu nhu cầu hoặc trạng thái pin khác.”
- **Giá trị đặc biệt:** closes learning loop day N→N+1 without future leakage.
- **Khả thi:** MULTIDAY-REQUIRED in sim; product needs activity history + user plan memory.
- **Coverage:** UNMEASURED trên five one-day runs; phép đo cần `run_multiday` và count non-null
  `planned_rest_hour` per day/persona.
- **Risk/guard:** historical pattern stale và health boundary; revalidate daily, confidence visible.

### IC-32 — Điều phối vị trí không dồn tài xế

- **Loại:** COMPOSITE · MULTI-SOURCE · SIMULATOR-SHOWCASE.
- **Vấn đề tài xế:** heatmap “điểm nóng” có thể đưa nhiều người tới cùng nơi và tự phá lợi ích.
- **Raw evidence:** S4 expected demand, supply now, `supply_incoming`, capacity_left, allocation and
  observed relocate segment (`market_state.py`).
- **Derived-state logic:** allocation only to cells with capacity; reservations/incoming supply are
  counted before presenting; explain why a seemingly attractive cell is omitted.
- **Kết luận:** “chỉ reposition khi allocation còn capacity; nếu thiếu supply data thì silent”.
- **UI:** simulator showcase composite/map overlay; not production driver card yet.
- **Nội dung mẫu:** “Khu vực A có nhu cầu mô phỏng cao nhưng capacity đã được phân bổ; hệ thống
  không khuyên thêm tài xế tới đó. Actor này được giữ nguyên vị trí.”
- **Giá trị đặc biệt:** demonstrates anti-herding, khác hẳn app chỉ broadcast heatmap.
- **Khả thi:** SIMULATOR-SHOWCASE; live cần demand+supply now/incoming+capacity governance.
- **Coverage:** UNMEASURED trong Web demo vì `positioning_overrides=off`; cần scenario S4 read-only.
- **Risk/guard:** herding/fairness/oracle demand; simulator label, capacity accounting, no live claim.

### IC-33 — Môi trường làm kế hoạch đổi như thế nào

- **Loại:** COMPOSITE · PLAN/JOURNEY · MULTI-SOURCE · SIMULATOR-SHOWCASE.
- **Vấn đề tài xế:** khi travel time/SOC dynamics đổi, app rule-based chỉ báo mưa mà không giải
  thích tác động lên plan.
- **Raw evidence:** deterministic rain/temp/event series, congestion proxy, speed/range factors,
  trip/route segments and old/new S2 plan (`environment.py`, `congestion.py`).
- **Derived-state logic:** compare same scenario before/after environmental regime; explain changed
  plan facts, not weather as live truth and not OSRM geometry as canonical state.
- **Kết luận:** “môi trường mô phỏng làm thời gian/SOC boundary đổi, nên plan window được cập nhật”.
- **UI:** simulator scenario timeline + Why-plan-changed.
- **Nội dung mẫu:** “Trong scenario mưa mô phỏng, tốc độ giảm và consumption thay đổi; window đổi
  pin được kéo sớm 1 bucket. Đây là showcase simulator, không phải dữ liệu thời tiết live.”
- **Giá trị đặc biệt:** multi-source causal mechanism inside simulator with explicit provenance.
- **Khả thi:** SIMULATOR-SHOWCASE; production EXTERNAL-DATA-REQUIRED.
- **Coverage:** current demo dry, events empty: 0 current candidate by design. Cần existing rain/event
  scenario, không fixture UI giả.
- **Risk/guard:** fake-live interpretation/double-count; prominent SIMULATOR badge and factor audit.

## 8. Composite-card catalog

Các card dưới đây không thể tạo từ một event đơn vì giá trị nằm ở episode/delta/baseline:

| Composite | Tín hiệu thành phần | Derived state | Insight tổng hợp | Vì sao một event không đủ |
|---|---|---|---|---|
| La bàn ca | shift + S1 + S2 + mission + confidence | ordered shift constraints | ba mốc cần theo dõi | một solver không thấy toàn incentive/energy map |
| Energy roadmap | SOC + segments + future plan | energy phase | online-now/swap-later | SOC snapshot không chứa trajectory tương lai |
| Energy disruption | repeated SOC-skip + swap/fail + new plan | open/closed energy episode | ca đã/ chưa phục hồi | mỗi skip không cho biết recovery |
| Plan revision explainer | old/new checkpoint + changed facts + intervening events | material diff | vì sao action/window đổi | checkpoint mới không kể state cũ |
| Plan churn guard | ≥3 semantic revisions/120′ | unstable plan | giữ strip, giảm notify | cooldown theo một event không thấy chuỗi revision |
| Plan-versus-actual | canonical window + observed segment | observed/late/not-observed | thực tế đang ở đâu so với plan | action event thiếu planned boundary |
| Recovery narrative | disruption + snapshot-after + next plan | feedback loop recovered | sự cố đã vào plan mới | incident alert không chứng minh re-plan |
| Rest versus idle | explicit rest + inferred idle + planned rest | recovery composition | nghỉ chủ động khác chờ | một “không di chuyển” không có semantics |
| Repeated idle | multiple blocks + session context | repeated waiting pattern | vấn đề lặp trong ca | một block dễ là noise |
| Utilization phase | early/late occupied+empty | phase transition | nhịp ca đổi đáng kể | cumulative utilization che thời điểm đổi |
| Cancellation cost | repeated cancel + wasted time + revision | disruption cluster | observed time erosion | một cancel không tạo pattern |
| Incentive conflict | mission + bonus + time + SOC/rest | binding objective | primary action và context | từng progress bar có thể khuyên mâu thuẫn |
| Personal income pace | intraday curve + prior comparable days | personal deviation band | hôm nay khác nhịp cá nhân | payout hiện tại không có baseline |
| Advice ledger | lease/intent/execution/outcome | three-lane history | đã nói/đã bấm/đã quan sát | một lifecycle event dễ bị diễn giải sai |
| Journey recap | all above + money sources | shift chapters | ca thay đổi thế nào | end_shift counter không kể hành trình |
| Next-day memory | prior idle/demand + next shift | planned rest candidate | ngày N ảnh hưởng brief ngày N+1 | một ngày riêng không có learning loop |

## 9. Product capability clusters

### C1 — Shift Compass

- **Raw groups:** shift/profile, S1/S2 plan, policy/mission, current state.
- **Idea Cards:** IC-01, IC-02, IC-03, IC-04, IC-05.
- **Xuyên ca:** brief → plan strip → early-pace insight; không tạo thêm popup khi plan chưa material.
- **Showcase:** app hiểu giới hạn cả ca và biết phần nào là forecast.
- **Chuyển live:** shift/KPI/policy gần shape thật; SOC/mission authority còn contract gap.

### C2 — Energy Continuity

- **Raw groups:** SOC, trip/empty segments, S2 plan, swap/charge/station events.
- **Idea Cards:** IC-05–IC-10.
- **Xuyên ca:** roadmap → prepare → action-now → observed recovery → friction recap.
- **Showcase:** theo energy constraint xuyên nhiều event thay vì báo “pin thấp”.
- **Chuyển live:** cần trusted SOC + observed swap/charge; station guidance chưa live-ready.

### C3 — Adaptive Plan Narrative

- **Raw groups:** checkpoint revisions, solver artifacts, state snapshots, execution links.
- **Idea Cards:** IC-11–IC-15, IC-28.
- **Xuyên ca:** plan strip cập nhật → Why delta → late/not-observed state → new plan.
- **Showcase:** giải thích chính xác plan changed và chống spam bằng plan history.
- **Chuyển live:** checkpoint layer đã có; state/execution feed là gap chính.

### C4 — Recovery & Operational Rhythm

- **Raw groups:** idle/rest/empty/occupied segments, cancellations, decision aggregates.
- **Idea Cards:** IC-16–IC-21.
- **Xuyên ca:** passive recovery/efficiency insights, chỉ nâng thành nudge khi canonical action có sẵn.
- **Showcase:** nhận ra pattern qua cửa sổ và phân biệt observed với inferred.
- **Chuyển live:** online/daily KPI có shape; intraday activity/trip contract cần mới.

### C5 — Incentive & Income Navigator

- **Raw groups:** S1, missions, newbie, policy, payout ledger, personal history.
- **Idea Cards:** IC-04, IC-22–IC-27.
- **Xuyên ca:** rights map → material progress change → conflict explanation → safe end-shift gate.
- **Showcase:** multi-objective nhưng action vẫn code/solver-owned.
- **Chuyển live:** daily tables gần sẵn; policy authority và intraday ledger quyết định độ sâu.

### C6 — Advice Accountability

- **Raw groups:** checkpoint/lease/lifecycle, client intent, execution segments, outcome metrics.
- **Idea Cards:** IC-13, IC-28, IC-29.
- **Xuyên ca:** show → intent → observation → recap, không nhập identity vào nhau.
- **Showcase:** traceability đầy đủ hơn notification system.
- **Chuyển live:** lifecycle đã có; retention/privacy và observed execution contract còn thiếu.

### C7 — Personal Driver Memory

- **Raw groups:** DriverMemory, daily KPI/income/rush, journey/advice histories.
- **Idea Cards:** IC-02, IC-03, IC-21, IC-24, IC-30, IC-31.
- **Xuyên ca/ngày:** baseline cá nhân → current deviation → repeated pattern → next-shift preparation.
- **Showcase:** học từ chính tài xế mà không future leak/cohort stereotype.
- **Chuyển live:** daily shapes tốt; comparable-day, minimum-history và memory service cần thiết kế.

### C8 — System-aware Simulator Showcase

- **Raw groups:** market demand/supply/capacity, environment/congestion, route/travel dynamics.
- **Idea Cards:** IC-32, IC-33.
- **Xuyên ca:** scenario state changes → solver plan changes → anti-herding allocation → recap.
- **Showcase:** chứng minh simulator hiểu tương tác hệ thống, không chỉ một driver cô lập.
- **Chuyển live:** chưa; giữ nhãn SIMULATOR-SHOWCASE tới khi có authoritative external contracts.

## 10. UI portfolio xuyên suốt ca

| Khoảnh khắc | UI layer | Idea Cards | Hành vi |
|---|---|---|---|
| Trước ca | brief + plan strip | 01, 02, 04, 05 | một lần; facts/provenance; no lease spam |
| 60–90′ đầu | passive insight | 03, 21, 24 | update-in-place; không action nếu solver im |
| Giữa ca an toàn | actionable nudge | 06, 08, 15, 22, 26 | chỉ canonical action + validity; one primary |
| Sau episode | composite/timeline | 09–14, 16–20, 23 | nối sequence; không phá Next Step |
| Gần cuối ca | boundary nudge | 27 | một lần; safety/policy first |
| Sau ca | recap | 25, 28, 29 | chapters + evidence labels |
| Nhiều ngày | expandable analytics/next brief | 02, 24, 30, 31 | pull-first; minimum history |
| Simulator showcase | scenario view | 32, 33 | separate badge/surface; không giả live |

Portfolio này tăng meaningful touchpoints qua **surface diversity**, không bằng cách tăng cadence
của proactive card. Suppressed ONLINE revisions có thể nuôi plan strip/churn detection nhưng không
tự trở thành popup.

## 11. Real-data feasibility matrix

| Phân loại | Idea Cards | Nguồn thật tối thiểu | Điều kiện fail-closed |
|---|---|---|---|
| REAL-DATA-READY về shape | 02, 21 phần daily, 22, 24 phần history, 30 | daily KPI/income/online/rush + policy version | không gọi là intraday nếu chỉ có daily batch |
| SMALL-WIRING | 01 sim, 04 sim, 06 sim, 09 sim, 11–14, 16–20 sim, 25, 28, 29 | projection từ RunResult/checkpoint/journey hiện có | section thiếu facts phải biến mất, không bịa |
| NEW-INTERNAL-CONTRACT | 03, 05–10 product, 15 product, 18–21 product, 23–27 | trusted SOC, activity segments, intraday ledger, observed swap/rest, policy authority | source stale/unavailable ⇒ template/passive/silent |
| MULTIDAY-REQUIRED | 02, 03, 21, 24, 30, 31 | prior-only driver memory + comparable-day service | thiếu minimum history ⇒ không comparison |
| EXTERNAL-DATA-REQUIRED | 33 live | weather/traffic/event feed + version/freshness | tắt hoàn toàn; không dùng congestion proxy làm live |
| SIMULATOR-SHOWCASE | 10 station-depth, 32, 33 | machinery đã có trong simulator | badge SIMULATOR/MOCK; không driver-live rollout |
| REJECT | per-order advice, raw ONLINE, fraud nudge, causal income claim | — | không tạo capability |

## 12. Coverage evidence dùng trong Idea Cards

Probe mới đo episode/derived state thay vì raw inventory:

| Derived state | Occurrence | Actor-run | Persona note / timing |
|---|---:|---:|---|
| Semantic plan revision | 1.224 | 426 | mọi P1/P2/P4/P6/P7 actor; p50 64,5% ca |
| Plan churn ≥3/120′ | 92 | 92 | P2 34, P4 17, P6/P7 14 mỗi nhóm |
| Disruption→revision ≤60′ | 160 | 125 | phủ mọi archetype; p50 64,8% ca |
| Future SWAP thực thi trong window | 349 | 274 | không có P1; p50 53,6% ca |
| READY action observed trong validity | 125 | 109 | late thêm 21 actor-run |
| SOC disruption→swap ≤90′ | 115 | 90 | unrecovered: 6 episode/5 actor-run |
| Long idle≥30′ / repeated | 1.012/— | 379/289 | inferred; không phải health fact |
| Long idle→rest ≤60′ | 228 | 176 | p50 69,5% ca |
| Utilization phase shift ≥15pp | 130 | 130 | tất cả persona |
| Empty share tăng ≥15pp | 99 | 99 | P4/P6 chiếm nhiều trong sample |
| Cancel cluster ≥2/120′ | 21 | 21 | low-frequency, recap/passive |
| Decline cluster ≥2/120′ | 101 | 101 | no per-order recommendation |
| Bonus+mission / mission+energy | 130/196 | 130/196 | multi-objective opportunity |
| ≥2 income sources | 345 | 345 | recap value rộng |
| Zero READY nhưng có recap | 148 | 148 | chứng minh recap không phụ thuộc advice volume |

Chi tiết reproducible nằm trong `experience-coverage.json`. Threshold là probe, không phải trigger.

## 13. End-to-end demo storylines

### Storyline A — Actor 35: một ca năng lượng được hiểu xuyên suốt

1. **Persona/state đầu ca:** seed 1000, P3 swap fleet, shift 550–1232; brief IC-01 cho biết
   online-now và future energy/rest plan.
2. **Raw events:** bonus READY 572; SWAP READY 781; swap 781–803 với wait 13′; SOC-skip 1117
   (20,4%, need 8,35 km) và 1148 (9,6%, need 6,79 km); swap 1152–1158; mission events.
3. **Derived state:** IC-06 mở prepare window; IC-10 ghi station friction; hai SOC-skip mở
   repeated-energy episode IC-08; swap thứ hai đóng episode IC-09; new plans tạo IC-11.
4. **UI:** plan strip trước, nudge SWAP khi READY/safe, timeline “plan đã đổi” sau sự cố; không
   hiển thị card lúc moving.
5. **Plan update:** current/future windows luôn từ S2 records; UI không tự suy SOC/action.
6. **Execution observed:** swap events/segments được link `coincident`, không tự tạo accepted.
7. **Recap:** IC-29: 15 trip, payout 330.636đ, 90 points, 2 SOC-skip, 2 swap episode,
   mission reward 70.000đ; không nói swap làm tăng payout.
8. **Tài xế hiểu:** hệ thống thấy pin là một chuỗi constraint→recovery, không chỉ threshold alert.

### Storyline B — Actor 70: nghỉ, cancellation và energy cùng tranh quỹ ca

1. **Persona/state:** seed 1000, P6; REST READY 300 mở một plan nghỉ có boundary.
2. **Raw events:** bonus READY 361; cancellation 398; mission 471; SOC-skip cùng thời điểm với
   SOC 10,1%; SWAP READY/execution 476; bốn rest events về sau.
3. **Derived state:** cancellation recovery IC-20 + mission/energy overlap IC-23 + energy recovery
   IC-09 + rest-vs-idle IC-16.
4. **UI:** một composite progress card nói rest là action primary; mission/bonus chỉ context, không
   phát ba nudge cạnh tranh.
5. **Plan update:** after cancellation/SOC change, IC-14 chỉ ra revision mới; không suy sự cố gây
   plan nếu artifact không chứng minh changed fact.
6. **Execution:** swap/rest observations tách khỏi UI intent.
7. **Recap:** 7 trip, payout 152.384đ, 45 points; timeline giải thích recovery và các rest windows.
8. **Tài xế hiểu:** hệ thống ưu tiên constraint hiện hành thay vì đuổi mọi incentive cùng lúc.

### Storyline C — Actor 37: một ca tân binh với nhiều nguồn quyền lợi

1. **Persona/state:** seed 1000, P4/new driver; brief IC-04 liệt kê chương trình bằng policy MOCK.
2. **Raw events:** bonus READY 407; mission 498; SWAP READY/execution 624; rest; mission 879;
   swap 885; newbie topup 926 (gross 279.126, floor 350.000, topup 53.156).
3. **Derived state:** incentive stack IC-04; energy roadmap IC-05; mission/bonus conflict IC-23;
   income-source reconciliation IC-25.
4. **UI:** progress group cập nhật mission completion thụ động; SWAP nudge vẫn là primary khi đến
   window; topup không xuất hiện trước settlement.
5. **Plan update/execution:** plan revisions và two swap segments được giải thích trong timeline.
6. **Recap:** 12 trip, payout 322.500đ, 75 points; tách trip/mission/newbie, không double-count.
7. **Tài xế hiểu:** nhiều chương trình được reconcile thành một money/policy story có provenance.

### Storyline D — Actor 10: nhiều plan revision nhưng không spam

1. **Persona/state:** seed 1000, P1 charge fleet, ca ngắn 1063–1285; không có READY checkpoint.
2. **Raw sequence:** sáu S2 ONLINE records suppressed; future head lần lượt REST→ONLINE→SWAP→ONLINE;
   một idle block 32,2′; chỉ có go_online/end_shift key events.
3. **Derived state:** plan churn IC-12 kích hoạt tại minute 1224; current-plan strip IC-05 update,
   nhưng không biến maintenance thành six cards.
4. **UI:** plan strip hiển thị future boundary hiện hành; một passive “kế hoạch đang biến động” nếu
   cần; zero actionable button vì canonical policy vẫn silent.
5. **Plan/execution:** không có action observation để gán followed/deviated; ledger để trống đúng nghĩa.
6. **Recap:** 7 trip, payout 147.230đ, 40 points, idle 49,7′; kể plan changed nhưng không nói tài xế
   bỏ qua lời khuyên.
7. **Tài xế hiểu:** hệ thống biết nhiều nhưng chủ động im khi không có action có giá trị.

### Storyline E — Actor 1: không có advice vẫn có journey value

1. **Persona/state:** seed 1000, P1 charge fleet, zero READY; five ONLINE records đều suppressed.
2. **Raw events:** hai cancellation-after-accept tại 1116/1202; 11 offers, 10 accepted, 8 completed;
   no SOC-skip, no long-idle block.
3. **Derived state:** cancellation cluster IC-20 (hai lần trong 120′); quiet-shift recap IC-29.
4. **UI:** không bịa advice ID/card; chỉ passive incident summary sau event và recap cuối ca.
5. **Plan:** suppressed plan có thể nuôi strip, nhưng không có canonical new action nên UI không CTA.
6. **Execution/outcome:** two cancellations là observed trip outcomes; không đổ lỗi hoặc ước tính
   hypothetical missed income.
7. **Recap:** 8 trip, payout 164.698đ, 45 points, completion 0,8; giải thích observed wasted minutes.
8. **Tài xế hiểu:** giá trị UI không phụ thuộc việc phải có proactive recommendation.

### Storyline F — Lịch sử hôm nay chuẩn bị ca ngày mai

- **Nhãn:** `SIMULATOR-SCENARIO`, dùng machinery `run_multiday`; chưa chạy/đo trong lượt five-seed.
1. Ngày N có nhiều idle blocks được `DriverJourney` tổng hợp; cuối ngày `_update_memory()` chạy S7
   retrospective và ghi `planned_rest_hour` sau khi ngày đã kết thúc.
2. Brief ngày N+1 (IC-31) nói rõ window đến từ hôm qua, không phải demand live.
3. Trong ngày N+1, state/plan mới revalidate; nếu khác, IC-11 giải thích revision thay vì giữ plan cũ.
4. Rest execution nếu quan sát được đi vào ledger IC-28; recap IC-29 tách plan/intent/execution.
5. Story chứng minh memory qua ngày và no-future-leak; chưa chứng minh health/outcome improvement.

## 14. Lựa chọn mạnh nhất của Agent

### Top 5 triển khai nhanh nhất

1. **IC-29 Recap hành trình ca:** input 450/450, pure projection, tăng value cả cho 148 quiet shifts.
2. **IC-11 Vì sao kế hoạch vừa đổi:** artifacts/fingerprint đã có; 426 actor-run có semantic revision.
3. **IC-25 Thu nhập đến từ đâu:** `DriverJourney` đã tách four sources; dễ kiểm conservation.
4. **IC-01 La bàn ca hôm nay:** dùng current inputs và không tăng interruption budget.
5. **IC-05 Lộ trình năng lượng:** plan/future windows đã có trong sim; phù hợp plan strip trước khi
   thêm SWAP_SOON producer.

### Top 5 thể hiện sự độc đáo mạnh nhất

1. **IC-09 Energy before/after recovery:** theo constraint tới observed execution rồi re-plan.
2. **IC-11 Plan revision explainer:** giải thích delta bằng immutable artifacts.
3. **IC-23 Incentive conflict:** multi-objective context nhưng canonical action không bị Agent đổi.
4. **IC-28 Advice ledger:** presented ≠ intent ≠ execution ≠ outcome hiển thị trực quan.
5. **IC-32 Capacity-aware positioning:** showcase anti-herding thay vì broadcast heatmap.

### Top 5 chuyển sang dữ liệu thật tốt nhất

1. **IC-22 Bonus status transition:** daily KPI/policy path rõ nhất; cần intraday freshness để nudge.
2. **IC-02 Personal strong windows:** rush/online daily shapes đã có; giữ ở analytics để tránh herding.
3. **IC-24 Personal income pace:** daily history sẵn; cần thêm intraday payout ledger.
4. **IC-25 Income-source breakdown:** cần ledger semantics rõ nhưng không phụ thuộc external API.
5. **IC-29 Journey recap:** chuyển dần theo từng section khi trip/activity/lifecycle feeds sẵn sàng.

### Top 3 composite card nên làm trước

1. **IC-11 Plan-change card** — dependency nhỏ, giá trị giải thích lớn, coverage cao.
2. **IC-09 Energy-continuity card** — câu chuyện current/future/execution rõ nhất trong trace.
3. **IC-29 Journey recap** — biến toàn bộ hệ thống thành một trải nghiệm có đầu/cuối.

### Top 3 storyline demo với cấp trên

1. **Actor 35 / Energy continuity:** nhiều event, two swap, SOC-skip, mission và recap trong một ca.
2. **Actor 37 / Incentive stack:** chứng minh money lineage + policy provenance + energy constraint.
3. **Actor 10 / Plan churn without spam:** chứng minh hệ thống biết im, dùng passive strip thay vì
   mass-unsuppress ONLINE.

## 15. Ý tưởng bị loại

| Ý tưởng | Lý do loại |
|---|---|
| “Nên nhận/từ chối/hủy cuốc này” | vượt dispatch boundary; event economics không cấp quyền action |
| Mỗi S2 ONLINE record thành card | 4.126 suppressed record/5 seed; spam, không material value |
| “Đi khu vực nóng nhất” từ demand | herding; thiếu supply incoming/capacity/live authority |
| Dùng OSRM distance/duration làm canonical plan | OSRM demo chỉ display; không được overwrite simulator state |
| Fraud/anomaly warning trực tiếp | false accusation/privacy/gaming; internal governance only |
| Rating giảm thì popup | surveillance/emotional cost cao; chỉ opt-in recap nếu có |
| Gợi ý trạm pin từ wait mô phỏng | chưa có live inventory/queue; dễ dồn tài xế |
| “Advice giúp bạn kiếm thêm X” | không có counterfactual; execution/outcome không phải causal effect |
| Dùng idle gap như fact nghỉ ngơi | idle là inferred, khác explicit rest; phải giữ confidence |
| LLM tự tổng hợp raw history rồi chọn action | LLM không sở hữu trigger/action/window/number/provenance |

## 16. Artifact và tái lập

```text
research/audit/2026-08-05-checkpoint-ui-experience-ideas/
├── ui-experience-idea-cards.md
├── analyze_experience_candidates.py
├── experience-coverage.json
└── ui-experience-storylines.json
```

```bash
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-ui-experience-ideas/analyze_experience_candidates.py \
  --seeds 1000 1001 1002 1003 1004
```

Giới hạn bằng chứng: thresholds là probes; current five-seed là một ngày dry; multiday values là
MOCK; IC-32/33 không có candidate trong Web demo hiện hành; human usefulness và visual layout chưa
được review; không có claim causal hoặc production-readiness.
