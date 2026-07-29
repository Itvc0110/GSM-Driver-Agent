# Research Summary — Đợt 1 + Đợt 2 + Đợt 3 (simulation) + Refresh policy 2026-07-24

> **CURRENT-STATE INDEX — 2026-07-27 (cập nhật 2026-07-29):** summary dưới đây là research/policy
> snapshot theo từng đợt. Để biết code/data/UI/Advisor hiện đang chạy gì, “mock 90 ngày” là gì, và
> quyết định architecture B, đọc [`audit/2026-07-29-cycle-w-review/findings.md`](audit/2026-07-29-cycle-w-review/findings.md)
> + [`tracking/PLAN-cycle-wx-2026-07-29.md`](../tracking/PLAN-cycle-wx-2026-07-29.md).
> Không suy từ benchmark/research rằng snapshot là data thật hoặc external provider đã được wired.

Ngày cập nhật: 2026-07-21 (refresh policy 2026-07-24) · Files chi tiết: [income structure](economics/income-structure.md) · [bonus/policy](policy/bonus-programs.md) · **[⚠ POLICY REFRESH 2026-07-24](policy/policy-refresh-2026-07-24.md)** · [pain points](community/pain-points.md) · [community insights](community/community-insights.md) · [order distribution](market/order-distribution.md) · **simulation:** [tooling](simulation/tooling.md) · [evaluation methodology](simulation/evaluation-methodology.md) · [world parameters](simulation/world-parameters.md) (+ đợt 4 đang chạy: action space, pilot 1 quận, timestep).
Phương pháp: web research song song + đối chiếu chéo; claim trung tâm ĐBTN đã xác minh trực tiếp trên official page. Mỗi file ghi nguồn/ngày/reliability; số community không được nâng thành policy/financial fact.

> **⚠ ĐÍNH CHÍNH 2026-07-24 (đọc trước):** Chính sách **Vận Doanh 23/02/2026** (toàn quốc) đã **BỎ phạt tỷ lệ nhận/hoàn thành ≤70%**, chuyển sang **KHOÁN TUẦN** + **truy thu 20%** (HN/HCM tới 40%) phần doanh số chưa đạt. ⇒ Mọi phần nói "phạt <70%" trong đợt 1/2 là **snapshot lịch sử (15/07/2025), có thể đã bị thay thế**. Bộ QTƯX 05/06/2026 vẫn liệt kê phạt <70% → **mâu thuẫn chưa reconcile**, cần data thật GSM. Chi tiết + timeline version: [policy-refresh-2026-07-24.md](policy/policy-refresh-2026-07-24.md).

## 10 điều quan trọng nhất

1. **Công thức thu nhập Bike được truyền thông official:** revenue share + thưởng tuần + thưởng khác. Hệ thống phải tách `gross revenue`, `driver payout` và `estimated net income`; policy/track quyết định cách tính.
2. **Policy thay đổi theo version:** timeline revenue share đã thấy 91% (11/2024, HCM) → 70% (12/2025) → tới 75% (02/03/2026). Không có một tỷ lệ vĩnh viễn cho mọi track/market.
3. **ĐBTN 3 tháng đầu** (policy từ 30/03/2026): HN/HCM có mức/điều kiện riêng; chỉ áp dụng khi map đúng cohort/track/effective date, không dùng như default universal.
4. **Ngưỡng nhận/hoàn thành và bảng điểm cũng versioned:** có bản HN 12/2025 yêu cầu 85%/85%; các threshold cũ 70%/50% là facts lịch sử có ngày, không hard-code cho hiện tại.
5. **Ba track kinh tế khác nhau:** xe cá nhân Platform, thuê/RTO, employee Car. Không trộn benefit/revenue share/chi phí giữa track.
6. **Thu nhập tự khai tương quan với giờ chạy**, nhưng các nguồn không nhất quán gross/payout/net; chỉ dùng làm calibration range, không làm guarantee.
7. **Pain point lặp lại nhất:** sạc/đổi pin mất thời gian; pattern sáng chạy → trưa sạc/nghỉ → chiều chạy lặp ở nhiều nguồn.
8. **Mock demand proxy:** anchor giờ cao điểm VN + proxy quốc tế cho hình dạng; không đại diện matching/dispatch hoặc số đơn chắc chắn đến từng tài xế.
9. **Nguồn cộng đồng có giá trị định tính** (mẹo pin, dead hours, điểm quá tải) nhưng phải qua source tier/freshness/PII/cross-check/human review; không cấp policy/số tài chính.
10. **Gap còn lại:** policy Bike thâm niên/Loyalty, % chia chi tiết theo khung giờ hiện hành, dữ liệu GSM theo giờ/khu vực, nội dung group FB sau login. Quyết định hiện hành là không OCR/nhập tay ảnh; không tìm được thì mock có assumption rõ.

## Đợt 3 (2026-07-21) — Simulation & evaluation (tóm tắt)

11. **Twin-world cùng seed là phương pháp chuẩn** (Common Random Numbers/paired-seed, giảm >10× số run; Lyft/DiDi cũng dùng simulator counterfactual); driver-level A/B thực địa sai vì interference — sim né được. Có **arm C placebo** (Cường approve) để tách giá trị "lời khuyên bất kỳ" khỏi "lời khuyên thông minh": hiệu quả thật = Δ(A−C).
12. **Adherence đo bằng twin-diff**: 5 nhãn Explicit/Coincident/Partial/Ignore/Unseen; nhìn twin ở arm B để loại "đằng nào cũng làm" (coincident) khỏi công của advisor — giải đúng bài toán "tài xế giàu kinh nghiệm tự làm đúng". **Cập nhật 2026-07-29 (Cycle W):** nay adherence do `gsm_core/lifecycle/projections.py` tính MỘT LUẬT từ event log (ĐA-05), ra HAI TÊN — `decision_adherence` (followed/decided theo bucket) và `event_adherence` (theo lần nói); **cấm khoá `adherence` trần** (phải chỉ rõ tên nào).
13. **Stack sim đã chốt**: SimPy + h3-py (res 8, pilot có thể res 9) + parquet/DuckDB + Streamlit/Plotly + kepler.gl replay; không cần API key bắt buộc (Mapbox optional).
14. **Thế giới HN có số thật**: 144 tủ đổi pin VinFast từ OSM (capacity=6, đổi ~90s, sạc lại 1.5–2h/viên); tốc độ bike 17/25/30 km/h theo giờ; cuốc lognormal ~3.5km; pin swap ~55–70km/pack; dispatcher baseline batched-Hungarian trong grid_disk k=2.
15. **Anti-herding có văn liệu**: capacity ledger (min-cost flow/Learn to Earn), tokens/quota, staggering, power-of-two-choices; herding (queue trạm, concentration) là guardrail metric — advice làm queue arm A > arm B nghĩa là advisor tự phá giá trị.
16. **Phân lớp biến A/B/C** cho robust optimization (bền vững → bài toán ràng buộc; bán bền vững → feature flag; bất định → reasoning guardrail) + hybrid trigger (event + fixed anchors + threshold) + persistent-vs-session memory — spec đã APPROVED.

## Đợt 5 (2026-07-27) — ĐO THẬT, không còn là giả thuyết

17. **Advisor hiện tại làm tài xế NGHÈO ĐI — có ý nghĩa thống kê.** 30 seed CRN, advice cho toàn
    đội (`coverage: all`): payout **−17.310đ/ngày, CI95 [−29.294, −5.820]**, chỉ **7/30** seed có
    lợi. Cơ chế: **cùng số giờ online** nhưng **+25,9 phút rỗi, −1,6 cuốc** — advice không làm tài
    xế chạy ít hơn, nó làm họ dùng cùng số giờ đó **tệ hơn**. Gốc rễ toán học: trong DP của S2,
    `ONLINE` cộng tiền còn `REST`/`SWAP` cộng đúng `0.0` ⇒ nghiệm tất yếu là "chạy hết công suất".
    Chi tiết: [`audit/2026-07-27-current-state/09-*`](audit/2026-07-27-current-state/09-baseline-30seed-coverage-all.md).
    ⚠ Đính chính 2026-07-28/29: số đó là của cấu hình 4-kênh CŨ (đã TẮT theo ĐA-07). Cấu hình
    duyệt hiện hành (chỉ `positioning_overrides: wait_only`): **+6.016đ/người/ngày SIG (n=100
    seed)**, served +1,74đp, đơn chết −23,4, Gini & HHI giảm — PASS 9/9 ĐA-08 (UPDATE-087).
    Về gốc rễ toán học ONLINE cộng tiền / REST-SWAP cộng 0: REST visibility đã sửa một phần
    (UPDATE-085, `shift_plan_input` 1.1.0 với `rest_taken_min`/`shift_elapsed_min`); kênh
    shift_plan vẫn TẮT theo điều khoản ĐA-07.
18. **Herding kiểu "dồn sạc/nghỉ cùng lúc" KHÔNG xảy ra** ở config này — đính chính kỳ vọng của
    #15: station HHI +0,0007 và supply-cell HHI +0,0001 (≈ 0). Tác hại đến từ chỗ khác: 90 tài xế
    cùng nhận **một logic lập lịch** làm phân bố cung lệch khỏi thế cân bằng tự nhiên. Guardrail
    chống herding vẫn cần, nhưng **không phải** cơ chế hại chính hiện nay.
19. **Tác hại ở tầng HỆ THỐNG chưa đủ bằng chứng.** served_rate −0,0047 · đơn hết hạn +4,8/ngày ·
    Gini −0,003 — **mọi CI đều chứa 0** ở n=30. Hướng nhất quán là xấu, nhưng **không được tuyên
    bố là đã chứng minh**. (Đính chính cách đọc bản 10 seed của hồ sơ 07.)
20. **⇒ Thứ tự sửa: objective CÁ NHÂN trước, multi-agent equilibrium sau.** Tối ưu cân bằng cho một
    hàm mục tiêu vốn đã sai là làm ngược. **Cập nhật:** Cycle Q đã đo (~220 run,
    [`simulation/multi-agent-equilibrium.md`](simulation/multi-agent-equilibrium.md)): cân bằng
    tồn tại ≈ λ_config với belief γ=1, heatmap residual naive (γ=0) phân kỳ vĩnh viễn, PoA
    51–73%, không có coverage tragedy.
21. **Kỷ luật đo lường — họ lỗi BUG-EVAL-ARGMAX lặp lại.** Lỗi dạng "thước đo sai trình bày như sự
    thật" đã tái diễn nhiều lần; ca mới nhất là **F-1 Cycle W**: `adherence_view` báo
    **0%/2%/100%** trong khi sự thật là **53,6%/52,2%/48,8%**. Nguyên tắc rút ra: **mọi thước đo
    phải có test pin bằng ground truth độc lập** trước khi được tin.

## Mapping research → feature

| Feature | Research dùng trực tiếp |
| --- | --- |
| F0 structured policy FAQ | `policy/bonus-programs.md`, `economics/income-structure.md`; câu hỏi định sẵn + template, bắt buộc policy source có version/citation; free-text C6 là legacy |
| F1 trước ca | policy track/cohort + persona + money definitions; không hard-code mốc cũ |
| F2 trong ca | `market/order-distribution.md`, `community/pain-points.md`; positioning (`wait_only`) là kênh mặc định **BẬT** (Cường duyệt 2026-07-28) — không còn đúng là "chỉ tư vấn theo thời gian, không reposition" |
| F3 sau ca | hành vi sạc/nghỉ, tiến độ mốc versioned, so với chính tài xế |
| 5 persona mock | part-time, full-time RTO, top performer, tân binh, lão làng; mọi số gắn MOCK/TBD |
| Simulator twin-world (T-018+) | `simulation/*`; specs: `simulation-twin-world`, `advice-timing-state-memory`, `simulation-pilot-world` (pilot 1 quận, 50 actors) |

## Follow-up

- T-013: người thật join 1–2 group Facebook nếu cần bổ sung insight.
- T-004: research handoff xong (source register 7 URL official + text corpus evidence tại `policy/`). **Chưa phải KB runtime**: T-011/reviewer riêng mới chuyển evidence → `PolicyFact` versioned. ⚠ Corpus JSON đang lỗi encoding (mojibake) — cần re-fetch/repair (UPDATE-022).
- T-011: contract mới phải version hóa policy bundle và money definition; contracts cũ vẫn deferred.
- D-007: quy trình khiếu nại/giải trình là dự án khác.
