# SPEC — Advisor Optimization Lớp A + Behavior Model B-arm (v0)

Cập nhật: 2026-07-21 · Trạng thái: READY (vá blocker F8 + G1/G4/G5 từ red-team audit) · Tiền đề: `sim-policy-bundle-v0.md`, `advice-timing-state-memory.md` (trigger/lớp biến), `simulation-pilot-world.md` (thế giới).
Nguyên tắc: deterministic theo input + seed (bắt buộc cho CRN); mọi tie-break có quy tắc cố định.

## 1. Behavior model (B-arm — nền của MỌI so sánh; cũng là "bản năng" của A/C khi không có advice)

### 1.1 Decision points

Actor ra quyết định tại: (i) kết thúc cuốc; (ii) mỗi 10 phút khi idle; (iii) SOC qua ngưỡng; (iv) mốc cá nhân (giờ bắt đầu/kết thúc quen, giờ ăn trưa quen theo archetype).

### 1.2 Action utilities (chọn argmax + noise Gumbel per-actor-stream — deterministic theo seed)

```text
U(wait_here)      = λ_demand · Ê[đơn/10ph tại cell]                    − λ_fatigue·F(t)
U(relocate(c'))   = λ_demand · Ê[đơn/10ph tại c'] − λ_move·τ(c,c')     − λ_fatigue·F(t)   (xét c' ∈ grid_disk k≤6, top-3 theo Ê)
U(swap/charge)    = w_soc(SOC) − λ_queue·Q̂(trạm)                       (w_soc: 0 khi SOC>40%, tăng dốc dưới 25%, ∞ dưới 12%)
U(rest)           = w_meal(giờ) + λ_fatigue·F(t)                       (w_meal đỉnh ở giờ ăn quen archetype)
U(end_shift)      = w_home(t vs giờ về quen) + bonus_lock_in           (bonus_lock_in: đã đạt mốc ngày → thiên về kết ca nếu quá giờ quen)
```

- `Ê[đơn]` = **bảng kinh nghiệm cá nhân** (per-actor demand prior trên cell×hour-bucket): khởi tạo = `true_mean × (1 + ε_a)`, ε_a ~ N(0, σ_arch); **σ_arch: P4 tân binh 0.6 · P1 0.4 · P2 0.3 · P5 0.15 · P3 0.1** (G1: "lão làng chính xác hơn" được định lượng). Cập nhật online: EMA α=0.3 theo quan sát của chính actor. → tạo coincident compliance tự nhiên.
- `F(t)` mệt mỏi = giờ online lũy kế / ngưỡng archetype (P3 12h, P2 10h, P5 9h, P1 5h, P4 8h), quy đổi qua λ_fatigue (VND-equivalent/10ph, default 3k).
- Tham số λ per archetype trong config `behavior-params-v0.yaml` (sinh khi build, review được).
- **Acceptance khi đơn nổ**: p_accept = logistic(η·(gross_ước − c_pickup·τ_pickup)) nhân hệ số archetype (P3 0.98 · P5 0.97 · P2 0.95 · P1 0.85 · P4 0.80); bị ép 1.0 khi `forced_auto_accept`.
- **Chọn trạm (G4)**: trạm quen (persistent memory) với p=0.7, ngược lại nearest theo τ; khi đến nơi thấy queue > 3 → rời sang trạm gần kế (tối đa 1 lần chuyển).
- **`battery_stranded` (G5)**: dispatcher chỉ gán khi SOC dự kiến sau cuốc > 8%; nếu vẫn hụt (variance tiêu hao) → sự kiện `battery_stranded`: cuốc bị hủy hệ thống (không phạt actor trong v0), actor "dắt bộ" tới trạm gần nhất với tốc độ 4 km/h; metric đếm riêng.

### 1.3 Calibration gate (G1 — thứ tự cứng)

**T-021 phải pass trên B-arm TRƯỚC khi chạy so sánh 3 arm**: 15–30 cuốc/actor full-time; pattern nghỉ-trưa/sạc-trưa xuất hiện; unserved trong dải mục tiêu. Lưu ý audit: 3 con số calibration ràng buộc lẫn nhau — chỉ tune 2, con thứ 3 để quan sát.

## 2. Advisor optimization lớp A (arm A)

### 2.1 Bài toán

Tại decision point của advisor (trigger theo `advice-timing-state-memory.md` §1), cho actor i:

- **State**: (t, cell, SOC, payout_lũy_kế, điểm_lũy_kế, acceptance/completion_rate, giờ_online, target, cờ forced_auto_accept).
- **Horizon**: các bucket 30ph còn lại của ca (tối đa 20 bucket).
- **Action/bucket**: {ONLINE, REST, SWAP/CHARGE, END} (+ cell gợi ý cho ONLINE nếu advice_scope cho phép khu vực).
- **Giải bằng DP xuôi trên (bucket × SOC-band × trạng_thái)** — SOC rời rạc hóa 10 band; ~20×10×4 states → trivial, deterministic.

```text
V(b, s) = max_a [ r(b, s, a) + V(b+1, s'|a) ]
r(ONLINE tại cell c) = Ê_advisor[đơn/bucket tại c] × p_accept_i × payout_kỳ_vọng/đơn(policy bundle)
                        − λ_fatigue,i · F  − λ_move·τ(nếu đổi cell)
r(REST) = 0 + reset_một_phần F
r(SWAP) = −thời_gian_swap_kỳ_vọng(τ + Q̂_ledger) × cơ_hội  + tránh_stranding
r(END)  = 0; terminal_bonus = giá_trị_mốc_NGÀY_đạt_được(điểm_dự_kiến) [kỳ vọng, không CVaR trong v0]
```

- **Mốc thưởng** (step function): dùng điểm kỳ vọng; advice "chốt mốc" phát khi `điểm_thiếu ≤ Ê[điểm/bucket] × buckets_còn` và ≥ ngưỡng giá trị (mốc_VND ≥ 30k).
- **Ngưỡng hồ sơ**: nếu acceptance_rate sát 85%/70% → DP bị chặn không đề xuất hành vi làm giảm (thực tế: advisor chỉ nhắc cảnh báo — không có action nào trong enum làm giảm tỷ lệ).
- **Tie-break deterministic**: khi bằng giá trị → thứ tự ưu tiên cố định ONLINE > REST > SWAP > END; cell tie-break theo h3-index tăng dần.

### 2.2 Advisor information model (F3 — bắt buộc config)

`advisor_information ∈ {oracle, product_proxy}`:
- `oracle`: Ê_advisor = true Poisson intensity (upper bound).
- `product_proxy` (**headline**): Ê_advisor = intensity × (1+ε_t), ε_t ~ N(0, 0.25) per (cell-cluster, hour) — mô phỏng sai số mock proxy; supply field làm mờ (chỉ đếm theo res-8 parent); station state trễ 5 phút (G2 information model: actor/advisor thấy trạng thái tủ qua snapshot trễ 5ph — nguồn herding từ thông tin cũ).

### 2.3 Advice scope (F4 — ablation bắt buộc)

`advice_scope ∈ {product_only, sim_extended}`:
- `product_only` (**headline cho quyết định sản phẩm**): timing online/rest/swap/end + khu vực đứng chờ theo 5 điều kiện an toàn (được Cường mở 2026-07-21) + nhắc mốc/ngưỡng. KHÔNG chỉ định trạm cụ thể (chỉ "đổi pin khung giờ X, tránh đỉnh").
- `sim_extended`: + station steering qua capacity ledger (trỏ trạm cụ thể), full supply field.
- Báo cáo Δ cho **cả hai scope** — tách phần hiệu quả đến từ đòn bẩy product không có.

### 2.4 Capacity ledger (arm A, chống herding)

Ledger đếm advice-outstanding theo (trạm, bucket 30ph) [sim_extended] hoặc (khung giờ swap, bucket) [product_only]. Sức chứa kỳ vọng = throughput tủ × bucket. Advice thứ N+1 vào slot đầy → DP nhận Q̂_ledger tăng → tự chuyển bucket/hành động khác. Staggering: ưu tiên SOC thấp trước, cộng jitter ±7ph từ actor-stream.

### 2.5 Arm C — placebo (F5, định nghĩa lại)

- **Cùng trigger engine + cooldown + budget** như A (không copy lịch của A — tần suất xấp xỉ, log số advice/arm để đối chiếu).
- Content: **random-safe** — uniform trên action hợp lệ tại trạng thái đó, ràng buộc không vi phạm an toàn (không khuyên ONLINE khi SOC<12%, không khuyên bỏ swap khi sắp stranded).
- Chấp nhận Δ(C−B) có thể **âm**; báo hai chiều, diễn giải kèm caveat trust-tĩnh-trong-24h.

## 3. Adherence & đo lường (F6, F7 — bổ sung DoD)

- **Adherence sweep bắt buộc**: {0%, archetype-default, 100%} → báo **Δ expected** (default) và **Δ upper-bound** (100%); frame pilot = "chứng minh năng lực đo", không phải ước lượng hiệu quả tuyệt đối.
- **Divergence index** per (actor, t) trong event log: `div = grid_distance(cell_A, cell_B) + |ΔSOC|/10 + 1{trạng_thái_khác}`; adherence report phân tầng low/high divergence; COINCIDENT chỉ tin ở low-div.
- Counterfactual branch re-run: stretch goal T-020 (ghi rõ, không silent-drop).
- **Proximal outcome** (insight 4): đo Δ payout & Δ điểm trong 90ph sau mỗi advice episode (A vs twin B cùng window) — tín hiệu sạch hơn distal cuối ngày.

## 4. Harmonize các mâu thuẫn docs (F11 — bản chốt)

| Mục | Giá trị CHỐT (spec này override) |
| --- | --- |
| Field aggregation tick | 15 phút (twin-world §2.1 "5 phút" hết hiệu lực) |
| Run window | **05:00–24:00**, warm-up 1h (05:00–06:00 không tính metrics); `orders_per_day = 1.200` = kỳ vọng TRONG window (renormalize hour weights trên 05–24h) |
| Đỉnh demand | sáng ~1,55×TB, chiều ~2,0×TB (theo bảng mock spec — bỏ mô tả "2 đỉnh ~2×") |
| N actors | Pilot = 50 (twin-world §5.1 "300–500" chỉ cho bản mở rộng) |
| UNSEEN | = advice **expire trước khi kịp phát** vì actor bận suốt validity; nếu phát được khi về idle thì không phải UNSEEN |
| Zone weights pilot | `w_cell = a·pop + b·POI` trên res 9 (mock spec §6 Tier A/B/C chỉ cho bản toàn HN; projection res 9 dùng công thức pilot) |
| OD boundary (F10) | **Buffer ring**: demand sinh trong 85 cells lõi; đích sample distance-decay có thể rơi vào vành k≤4 quanh lõi (nhãn `outside`); actor trả khách ngoài → deadhead tự quay về cell lõi gần nhất (chi phí thời gian thực); metrics chỉ tính hoạt động từ lõi |
| DoD tách (F9) | **DoD-core (T-018)**: determinism, sensitivity, calibration B-arm (mục 1.3). **DoD-eval (T-019+T-020)**: ledger proof, Δ 3 arm × advice_scope × information × adherence sweep |
| Runtime (G8) | ~5 kịch bản × 3 arm × 2 scope × 20–30 seeds ≈ 600–900 run + sweep; DES 50 actors ước giây→phút/run → giờ-cấp trên laptop, chạy song song theo seed |

## 5. Defer ghi nhận

- Đa loại đơn (Express/Ngon) trong generator → D-009 (sau pilot).
- Kịch bản tuần + trust dynamics; mất điện 1 trạm; adoption 70%; regime sweep orders∈{900,1200,1800} như trục báo cáo chính → hàng đợi sau pilot (đã ghi twin-world §9 + insight audit).
- CVaR cho mốc thưởng; phụ phí mưa/đêm trong fare → v1.
