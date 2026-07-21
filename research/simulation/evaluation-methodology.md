# Research — Phương pháp đánh giá hiệu quả advisor & đo adherence (twin-world)

Ngày: 2026-07-21 · Nguồn: T-016 (research đợt 3) · Phục vụ: `specs/simulation-twin-world.md` §1, §7
Thuật ngữ chuẩn để dùng trong docs: *common random numbers / paired-seed design*, *counterfactual simulation*, *ITT vs CACE/LATE*, *principal strata (complier/always-taker/never-taker/defier)*, *proximal vs distal outcome (MRT/JITAI)*, *capacity-aware recommendation*, *envy-free coordination*.

## (a) Protocol đánh giá — từng bước

### Design: counterfactual twin worlds trên Common Random Numbers (CRN)

- Chạy 2 arm cùng seed là **đúng chuẩn phương pháp luận**: CRN là kỹ thuật variance reduction kinh điển khi so sánh 2+ cấu hình ([Variance reduction](https://en.wikipedia.org/wiki/Variance_reduction), [CRN example](https://demonstrations.wolfram.com/TheMethodOfCommonRandomNumbersAnExample/)); trong ABM gọi là **paired-seed/matched evaluation** — CRN giảm số simulation cần thiết **>10×** cho cùng mức standard error, và cho phép phân tích ở mức từng agent ([arXiv:2409.02086](https://arxiv.org/html/2409.02086v1), [arXiv:2512.24145](https://arxiv.org/pdf/2512.24145)).
- Industry dùng đúng cách này: Lyft xây simulator marketplace factual vs counterfactual ([Lyft blog](https://eng.lyft.com/https-medium-com-adamgreenhall-simulating-a-ridesharing-marketplace-36007a8a31f2)); DiDi calibrate simulator tới sai lệch <1.5% để đánh giá policy offline ([arXiv:2408.10479](https://arxiv.org/html/2408.10479v1)).
- **Yêu cầu kỹ thuật then chốt — RNG synchronization**: tách stream theo tiến trình ngoại sinh (demand riêng, mỗi actor riêng, weather riêng) để khi arm A đổi hành vi, phần còn lại của thế giới vẫn nhận đúng chuỗi số như arm B. Chấp nhận divergence dần giữa 2 arm — CRN vẫn giảm variance chừng nào outcome còn tương quan dương theo seed; nên log tương quan seed-level để biết CRN còn tác dụng.

### Số seeds

- Pilot **n₀ = 10–20 seeds** → tính SD của hiệu số theo seed D_i = metric_A(i) − metric_B(i) → chọn n theo half-width CI mong muốn: `CI = D̄ ± t(α/2,n−1)·S_D/√n` ([Goldsman — Comparing Systems](https://www2.isye.gatech.edu/~sman/courses/6644/Module10-ComparingSystems-201128.pdf)).
- Sequential: thêm seed đến khi CI hội tụ (Robinson 2004). Văn liệu dùng 30–100 replication; CRN giảm mạnh nhu cầu. **Đề xuất: bắt đầu 20–30, sequential tối đa 100.**

### Thống kê

1. **Paired t-test/CI trên D_i** — đơn vị phân tích = seed (tài xế trong cùng seed không độc lập).
2. **Bootstrap CI trên seeds** cho metric lệch/non-normal (tỷ lệ, Gini); báo effect size + CI, không chỉ p-value.
3. **1 primary metric** chọn trước (đề xuất: driver payout/giờ online của nhóm được advise); còn lại secondary.
4. Nhiều arm (>2): dùng ranking & selection.
5. Báo cả aggregate lẫn distributional (per archetype, per percentile) — paired design làm nổi khác biệt distributional.

### Vì sao twin-world thay vì A/B/switchback

- Driver-level A/B **sai về nguyên tắc** trong ride-hailing: chung pool cung → treatment hút driver khỏi control, vi phạm SUTVA, thường phóng đại effect ([Lyft experimentation](https://eng.lyft.com/experimentation-in-a-ridesharing-marketplace-b39db027a66e), [arXiv:2104.12222](https://arxiv.org/pdf/2104.12222)). Thực địa phải dùng **switchback** theo thời gian×vùng (Lyft/Uber ~160 phút/khối/DoorDash/Bolt — [Statsig](https://www.statsig.com/blog/switchback-experiments), [Bojinov & Simchi-Levi](https://www.hbs.edu/ris/Publication%20Files/WP21-034_20160b13-a86c-4a0d-b6e9-bbae288486c5_c93009c0-8003-43fd-bb1a-012c02d33b98.pdf)).
- **Twin-world trong sim né được interference hoàn toàn** (2 thế giới không chia sẻ pool) — chính là lý do industry xây simulator.
- Lưu ý: twin-world đo total effect khi 100% arm A có advisor → **phải chạy thêm kịch bản adoption 10%/50%/100%** vì hiệu ứng cân bằng thị trường đổi theo mức phủ.

## (b) Taxonomy adherence + twin-diff attribution

Nền khái niệm: **ITT** (so theo được-gán-advice, unbiased cho "triển khai advisor đáng giá bao nhiêu" nhưng under-estimate khi adherence thấp) vs **CACE/LATE** (hiệu quả trong nhóm compliers, ước lượng IV); **principal strata** Angrist–Imbens–Rubin: complier / always-taker (= "coincident compliance" — đằng nào cũng làm) / never-taker / defier ([PMC3154088](https://pmc.ncbi.nlm.nih.gov/articles/PMC3154088/)). Ngoài đời strata không quan sát được; **trong twin-world quan sát trực tiếp** — nhìn twin ở arm B là biết. Khung **MRT/JITAI** (mobile health) khớp advice theo thời điểm: mỗi decision point đo *proximal outcome* ngắn hạn, tách với *distal outcome* cả ca/tuần ([AJPH MRT](https://ajph.aphapublications.org/doi/full/10.2105/AJPH.2022.307150)). Ride-hailing: adherence modeling trong rebalancing ([arXiv:2412.16632](https://arxiv.org/abs/2412.16632) — tối ưu nhận thức adherence cải thiện 30%); i-Rebalance user study 99 tài xế thật, advice cá nhân hóa tăng acceptance 38% ([arXiv:2401.04429](https://arxiv.org/abs/2401.04429)).

### Bảng taxonomy (mỗi advice episode = advice tại decision point t, spec hành động + window [t, t+w])

| Nhãn | Định nghĩa vận hành | Twin arm B | Strata |
| --- | --- | --- | --- |
| **Explicit adherence** | Hành động arm A khớp advice spec trong window | Twin KHÔNG làm vậy | Complier |
| **Coincident compliance** | Hành động khớp spec | Twin CŨNG làm vậy → không attribute cho advice | Always-taker |
| **Partial** | Khớp loại hành động, lệch thời điểm/thời lượng quá tolerance; chấm 0–1 theo độ khớp | So twin tách phần lệch tự nhiên | Giữa |
| **Non-adherence** | Không có hành động khớp trong window | — | Never-taker |
| **Contrary** | Làm ngược advice | So twin xem có phải hành vi nền | Defier — tín hiệu advice phản cảm |

### Cách đo

1. Log mỗi episode: (actor, seed, t, spec, window, confidence) — khớp yêu cầu log reasoning của CLAUDE.md.
2. Behavioral matching hành động vs spec (ngưỡng dung sai khai báo trước).
3. **Twin-diff attribution**: "thay đổi do lời khuyên" = Explicit (+ phần chênh Partial); Coincident bị loại. `true influence rate = |Explicit| / (|Explicit|+|Coincident|)` — tách ảo giác "advice đúng vì trùng hành vi sẵn có".
4. Hai tầng hiệu quả: **ITT cấp seed** (bật advisor đáng giá bao nhiêu) + **episode-level proximal** (một lời khuyên được nghe tạo ra bao nhiêu), phân theo nhãn adherence.
5. **Hạn chế phải khai báo**: sau episode đầu, 2 thế giới phân kỳ → twin B không còn là counterfactual "sạch" cho episode sau của cùng actor. Giảm thiểu: đánh dấu độ phân kỳ trạng thái tại mỗi episode; với phân tích tinh, re-run "counterfactual branch" ngắn từ trạng thái arm A tại t nhưng không phát advice; kết luận distal luôn dựa trên paired difference cấp seed (không cần twin sạch theo episode).
6. Sản phẩm thật sau này: cùng taxonomy nhưng đo bằng `advice_shown/viewed/acted` + behavioral matching; không có twin nên attribution yếu hơn (ITT + IV) — ghi rõ hạn chế.

## (c) Metrics 3 tầng (đối chiếu văn liệu — bổ sung cho spec §3)

Nguồn đối chiếu: DiDi repositioning DRL đo income/hour ([arXiv:2103.04555](https://arxiv.org/abs/2103.04555)); productivity tách occupied/idle/pickup ([arXiv:1809.10329](https://arxiv.org/pdf/1809.10329)); served demand/wait/adherence ([arXiv:2412.16632](https://arxiv.org/abs/2412.16632)); EV service rate + charging wait ([arXiv:2412.09978](https://arxiv.org/abs/2412.09978)); fairness Gini earnings ~0.4–0.45, top 10% driver chiếm 48% thu nhập Chicago ([Nature Sci Rep](https://www.nature.com/articles/s41598-020-63171-9), [arXiv:2502.08893](https://arxiv.org/pdf/2502.08893)); envy-free từ Learn to Earn ([arXiv:2006.10904](https://arxiv.org/abs/2006.10904)). Metrics bổ sung spec: **biến động thu nhập ngày-qua-ngày (SD)** (giá trị "ổn định" của tư vấn), **tổng payout toàn hệ** (soi zero-sum vs positive-sum), **khoảng cách advised vs non-advised khi adoption <100%**, **envy metric**.

## (d) Anti-herding (đối chiếu văn liệu — xác nhận spec §6)

Văn liệu xác nhận: recommender mù tương tác → supply excess; mô hình biết trước thậm chí chọn KHÔNG khuyên để tránh dồn cung ([arXiv:2412.16632](https://arxiv.org/abs/2412.16632), [mean-field oversupply equilibrium arXiv:2504.02346](https://arxiv.org/pdf/2504.02346)). Cơ chế theo độ phức tạp:

1. **Capacity-aware allocation** (chính — khớp capacity ledger trong spec): Learn to Earn giải min-cost flow cho recommendation giải thích được + envy-free ([arXiv:2006.10904](https://arxiv.org/abs/2006.10904)); anticipatory charging coordination giảm chờ + tăng service rate ([arXiv:2412.09978](https://arxiv.org/abs/2412.09978), [safe RL charging arXiv:2407.20679](https://arxiv.org/pdf/2407.20679)).
2. **Tokens/quota** theo (khung giờ × loại trạm) — bản rời rạc của #1, dễ log/giải thích.
3. **Staggering/sequential**: advice sau nhìn thấy hệ quả advice trước (kiến trúc i-Rebalance).
4. **Power-of-two-choices**: đưa mỗi tài xế 2 lựa chọn sample ngẫu nhiên kèm so sánh — giảm mất cân bằng tải cấp số nhân, tránh herding do thông tin cũ ([Mitzenmacher](https://ieeexplore.ieee.org/document/963420/)); hợp triết lý "tài xế quyết định".
5. **Herding như guardrail metric**: concentration index + queue trạm là điều kiện veto — advice làm queue arm A > arm B nghĩa là advisor tự phá giá trị.

## (e) Giới hạn nguồn

DoorDash switchback blog 403 (dẫn qua tóm tắt; thay bằng Statsig + Bojinov–Simchi-Levi đã kiểm chứng). [arXiv:2512.24145] và [arXiv:2409.02086] mới đọc abstract — đọc full text khi viết spec chi tiết điều kiện phá vỡ CRN. Mọi số sim sinh ra gắn nhãn MOCK theo CLAUDE.md.
