# SPEC — Môi trường giả lập Twin-World & đánh giá hiệu quả gợi ý (v1.1)

Cập nhật: 2026-07-21 · Trạng thái: **APPROVED** (Cường 2026-07-21: "approve mọi quyết định thiết kế, có thêm arm C") — hiệu chỉnh chi tiết theo research đợt 3+4 trong `research/simulation/`.
Trả lời yêu cầu #1, #2, #5, #6 (Cường, 2026-07-21). Thiết kế giả lập được coi **quan trọng ngang** thiết kế bài toán tối ưu.

**Thu hẹp pilot (Cường 2026-07-21, đợt 2):** phạm vi biểu diễn/visualization đầu tiên = **1 quận Hà Nội, N = 50 actors**; demand/ngày của khu vực lấy từ research hoặc mock theo phân phối vị trí×thời gian; bản đồ pilot gồm trạm đổi pin + POI demand anchors; H3 chia cho cấp quận/phường — chi tiết tại `specs/simulation-pilot-world.md`. Kiến trúc twin-world dưới đây không đổi; N=300–500 toàn thành phố trở thành kịch bản mở rộng sau pilot.

## 0. Mục tiêu

Chứng minh (hoặc bác bỏ) một cách đo được rằng: **gợi ý của agent làm tài xế đạt kết quả tốt hơn**, trong một khu vực giả lập sát thật (Hà Nội, lưới H3), nhiều loại tài xế, đơn được phân bởi một dispatcher tối ưu có sẵn — và **không gây hại hệ thống** (tắc trạm sạc, mất cân bằng cung).

## 1. Kiến trúc Twin-World (trả lời #1)

Chạy **hai thế giới song song, cùng seed** (counterfactual twin):

```text
                    ┌────────────────────────────────────────────┐
  WorldConfig ──────┤  SHARED: demand generator (seeded),        │
  (seed, city, N)   │  H3 grid, station map, weather/events,     │
                    │  dispatcher algorithm, policy bundle        │
                    └───────────────┬────────────────────────────┘
              ┌─────────────────────┴─────────────────────┐
      ARM A (advised)                            ARM B (baseline)
      actors nhận advice từ Advisor               actors y hệt, KHÔNG advice
      (adherence model quyết định nghe/không)     (chỉ heuristic bản năng)
              │                                           │
      event log A (parquet)                       event log B (parquet)
              └───────────────┬───────────────────────────┘
                        Evaluator: paired metrics theo seed
                        + dashboard + spatial replay
```

Nguyên tắc bắt buộc:

1. **Common random numbers**: cùng seed ⇒ cùng chuỗi đơn phát sinh (thời gian, cell đón/trả, giá trị cuốc), cùng thời tiết/sự kiện, cùng tính cách actor. Khác biệt duy nhất giữa 2 arm là **advice và phản ứng với advice**. RNG phải tách stream theo mục đích (demand stream, actor-behavior stream, adherence stream) để 1 quyết định khác đi không làm lệch toàn bộ chuỗi ngẫu nhiên phía sau.
2. **Dispatcher là hộp đen chung** (thuật toán có sẵn — xem §4): advisor KHÔNG can thiệp matching. Advice chỉ đổi *hành vi actor* (online lúc nào, di chuyển nghỉ/sạc lúc nào, theo mốc thưởng nào) → gián tiếp đổi input cho dispatcher. Đúng ranh giới sản phẩm (không can thiệp dispatch).
3. So sánh **paired theo seed**: chạy K seeds (mặc định 20–30), mỗi seed cho 1 cặp (A,B); metric hiệu quả = phân phối của Δ(seed) = metric_A(seed) − metric_B(seed); kiểm định paired (bootstrap CI + sign test). ▸RESEARCH: chốt K và test cụ thể theo variance thực đo được.
4. **Arm C — placebo (ĐÃ CHỐT, Cường approve 2026-07-21)**: arm thứ ba cùng seed với advice ngẫu nhiên/naive (cùng tần suất, cùng loại action space với arm A nhưng nội dung không dùng demand/policy intelligence — vd khuyên sạc tại mốc giờ cố định, khuyên nghỉ ngẫu nhiên trong cooldown hợp lệ). Mục đích: tách "giá trị của việc có lời khuyên bất kỳ" (placebo/Hawthorne) khỏi "giá trị của lời khuyên thông minh". Báo cáo chuẩn: Δ(A−B), Δ(C−B), Δ(A−C) — hiệu quả thật của intelligence là Δ(A−C).

## 2. Thế giới mô phỏng

### 2.1 Không gian & thời gian

- Lưới **H3 resolution 8** cho nội thành Hà Nội (▸RESEARCH xác nhận res + số cells; res 8 ~0.7 km²/cell). Res 7 cho vành ngoài nếu cần giảm chi phí.
- Thời gian: discrete-event trên timeline liên tục, tick tổng hợp 5 phút cho các field (demand, supply density). Một run mặc định = 1 ngày vận hành 05:00–24:00; kịch bản tuần = 7 ngày nối tiếp có persistent memory của actor.
- Demand generator: dùng `specs/mock-order-distribution.md` (BASE × zone_share × hour_shape × dow × weather) chiếu xuống từng cell H3, sinh đơn Poisson theo cell×tick; mỗi đơn có cell đón, cell trả (ma trận OD đơn giản theo khoảng cách), giá trị cuốc.

### 2.2 Các thực thể

| Thực thể | State chính | Ghi chú |
| --- | --- | --- |
| Actor (tài xế) | cell hiện tại, SOC pin, trạng thái (idle/enroute/on-trip/charging/rest/offline), số cuốc & doanh thu hôm nay, điểm thưởng, giờ online, archetype params, adherence params, memory hành vi | sinh từ archetype (§5) |
| Order | thời điểm đặt, cell đón/trả, giá trị, trạng thái (open/assigned/completed/expired) | expire nếu không ai nhận trong X phút |
| Station (trạm đổi pin/sạc) | cell, số khe, hàng chờ hiện tại, thời gian phục vụ/khe | ▸RESEARCH: số trạm & phân bố HN thực tế |
| Dispatcher | thuật toán gán đơn (§4) | hộp đen chung 2 arm |
| Advisor (chỉ arm A) | policy bundle, demand/supply field nhìn thấy được, capacity ledger (§6) | sinh advice theo trigger (xem `specs/advice-timing-state-memory.md`) |
| World | demand field, supply field (mật độ tài xế theo cell), weather, event, policy version | supply field là biến mới bổ sung theo yêu cầu #5 |

### 2.3 Vòng đời actor & action set (chốt theo research `research/simulation/action-space.md`)

idle → (được gán đơn? → enroute → on-trip → hoàn thành, cập nhật thu nhập/điểm/SOC) → idle; xen kẽ quyết định hành vi bằng **behavior model** (§5.2); ở arm A/C nếu có advice hiệu lực thì adherence model (§7) quyết định.

Action set chốt (căn cứ hành vi thực của tài xế Xanh SM Bike — có nguồn):

- **App events:** `go_online` · `go_offline` · `set_offline_after_trip` (tính năng official cho Bike — cơ chế kết ca "mềm" mà advisor được khuyên) · `accept_order`/`decline_order` (decline vô hiệu khi cờ `forced_auto_accept` — hệ thống ép bật khi acceptance ngày <50%, reset 23h59) · `cancel_trip(reason)` (mọi cancel Bike tính vào rate) · `complete_trip`.
- **Vật lý:** `wait_at_cell` · `relocate_to_cell` (actor tự quyết — advisor KHÔNG khuyên trong product) · `go_to_swap_station → queue → swap_battery` (90s, tủ 6 khe) · `charge_at_home(≈3–4h)` (đội sạc cắm) · `rest` · `start_shift`/`end_shift` · `weather_response` (offline khi mưa với xác suất cao theo archetype — evidence Thanh Niên).
- **Không mô hình hóa:** multi-app (bị cấm với xe Xanh SM — khác giả định sim Grab-like), hành vi vi phạm (chạy ngoài app, cuốc ảo, xí chỗ tủ pin) — trừ scenario noise có nhãn riêng.
- **State kèm actor:** acceptance/completion/cancel rate, điểm thưởng tuần, SOC, vị trí, `forced_auto_accept`, gói tài xế (FT/PT theo archetype).

## 3. Metrics — 3 tầng (trả lời #1 "đo trên nhiều phương diện")

### Tầng tài xế (per-actor, tổng hợp theo archetype)

- driver payout/giờ online; tổng payout/ngày; estimated net (trừ chi phí đổi pin/thuê xe theo track).
- utilization = thời gian có khách / giờ online; empty time; số cuốc.
- đạt mốc thưởng: % actor đạt mốc điểm tuần/ngày; khoảng cách tới mốc.
- SOC stress: số lần SOC < ngưỡng an toàn; thời gian chờ ở trạm.
- giờ làm: tổng giờ online (kiểm soát "tăng thu nhập nhưng phải cày thêm giờ" — báo cả payout/h lẫn tổng giờ).

### Tầng hệ thống (marketplace không bị hại)

- service level: % đơn được phục vụ; thời gian chờ trung bình của khách; % đơn expire.
- supply-demand mismatch theo cell×tick (chuẩn hóa); heatmap chênh lệch.
- trạm sạc: queue length theo trạm×tick, P95 thời gian chờ đổi pin, **Gini/HHI của tải giữa các trạm** (đo herding — yêu cầu #5).
- phân bố tài xế: entropy/tập trung của supply field so với demand field.

### Tầng công bằng & bền vững

- Gini của payout giữa actors; payout của decile thấp nhất (advice không được chỉ giúp nhóm mạnh).
- chênh lệch hiệu quả giữa archetype (tân binh có hưởng lợi ít nhất bằng lão làng không).
- robustness: Δ metric ổn định qua seeds (CI không vắt qua 0), qua kịch bản (mưa, lễ, demand thấp).

Mỗi metric báo cáo: giá trị A, B, Δ, CI 95% (bootstrap trên seeds), và hướng tốt. ▸RESEARCH: đối chiếu bộ metric với industry/papers rồi chốt danh sách cuối.

## 4. Dispatcher baseline (thuật toán tối ưu "có sẵn")

Yêu cầu: đơn giản, minh bạch, đủ giống thực tế, chạy trên H3:

- **Batched nearest matching**: gom đơn mở trong cửa sổ Δt (2–5s sim-time hoặc theo tick), tìm ứng viên trong `gridDisk(order.cell, r)` (r tăng dần tới r_max), giải bài toán gán chi phí nhỏ nhất (Hungarian/greedy theo khoảng cách H3 + hướng di chuyển), tôn trọng trạng thái actor (idle mới nhận được).
- Từ chối/bỏ lỡ: actor có acceptance behavior (theo archetype) → đơn quay lại pool; ảnh hưởng tỷ lệ nhận của actor (liên kết ngưỡng policy).
- ▸RESEARCH: đối chiếu với tài liệu matching công khai (DiDi/Uber/Grab) và chốt tham số (Δt, r_max, cost function).

Dispatcher giữ nguyên giữa 2 arm và KHÔNG đọc advice — bảo toàn ranh giới "advisor không can thiệp phân đơn".

## 5. Quần thể actor (trả lời #6 — "nhiều và đa dạng hơn 3 persona")

### 5.1 Từ persona → archetype → population

5 persona trong `planning/PERSONAS.md` trở thành **archetype templates**. Mỗi archetype là *phân phối tham số*, không phải 1 actor:

| Archetype (từ persona) | Tỷ trọng mặc định | Tham số biến thiên khi sample |
| --- | --- | --- |
| P1 Sinh viên part-time | 20% | giờ online 2–5h (tối), target thấp, acceptance dao động, adherence trung bình |
| P2 Full-time RTO | 30% | 8–11h, target trung-cao, acceptance cao, adherence cao |
| P3 Top performer | 10% | 10–12h, chiến lược riêng mạnh (ít nghe advice trừ khi giá trị rõ), acceptance rất cao |
| P4 Tân binh | 25% | giờ lệch khung, hiểu biết thấp, acceptance thấp-trung bình, adherence cao nhưng thực thi lỗi |
| P5 Lão làng | 15% | 8–9h, thói quen cố định (adherence thấp với advice trái thói quen), hiệu quả bản năng cao |

- Sample N actors (mặc định **N = 300–500**, ▸RESEARCH chốt theo chi phí chạy) với jitter: giờ bắt đầu, cell nhà (phân bố theo tier khu dân cư), SOC ban đầu, target, hệ số hành vi. Cùng seed ⇒ cùng quần thể ở cả 2 arm.
- Tỷ trọng archetype là config; chạy sensitivity với các mix khác nhau.
- Trong arm A có thể chỉ X% actor "có app advisor" (mặc định 100%, nhưng config để mô phỏng adoption từng phần).

### 5.2 Behavior model (bản năng — dùng ở CẢ 2 arm)

Mỗi actor quyết định theo heuristic có nhiễu: chọn hành động có utility cao nhất trong {tiếp tục chờ, dạt sang cell lân cận có demand quen thuộc, nghỉ, đi đổi pin, kết ca} với utility = f(kỳ vọng đơn theo kinh nghiệm cá nhân, SOC, mệt mỏi, gần target, thói quen archetype) + ε. Kinh nghiệm cá nhân = bảng demand đã học từ các ngày trước của chính actor (khởi tạo từ prior của archetype — lão làng có prior chính xác hơn tân binh). Đây chính là cơ chế tạo ra **coincident compliance** (#2): actor giỏi tự làm đúng điều advisor sẽ khuyên.

## 6. Advisor trong sim + chống herding (trả lời #5)

Advisor arm A nhìn thấy: demand field dự báo, **supply field** (mật độ tài xế theo cell — biến mới), **station state** (queue/khe trống), policy bundle, và state/memory của từng actor được tư vấn. Nguyên tắc:

1. **Capacity-aware advice**: advisor giữ một **capacity ledger** — khi khuyên actor i đi đổi pin tại trạm s trong khung t, ledger trừ 1 suất kỳ vọng của (s,t); khi (s,t) hết suất kỳ vọng, actor tiếp theo được khuyên trạm/khung khác. Tương tự cho "nghỉ bây giờ": không để tỷ lệ actor được khuyên nghỉ trong cùng tick vượt ngưỡng (giữ service level).
2. **Staggering/jitter**: cùng một nhu cầu (vd sạc trưa) được rải trong khoảng thời gian bằng ưu tiên theo SOC (SOC thấp đi trước) + jitter ngẫu nhiên, thay vì một mốc giờ chung.
3. **Marginal value**: giá trị của một advice được tính trên trạng thái *sau khi* các advice trước đó đã phát (không tính trên trạng thái tĩnh) — tránh mọi actor cùng thấy "13h trạm X vắng".
4. **Guardrail hệ thống trong sim**: nếu metrics hệ thống (queue trạm, unserved demand) vượt ngưỡng do advice, advisor phải tự điều tiết (giảm tần suất, đổi nội dung); evaluator ghi nhận vi phạm như một failure mode.

Ghi chú phạm vi: fleet-awareness này nằm **trong simulator/advisor-sim** để nghiên cứu; sản phẩm thật vẫn theo ranh giới hiện hành (D-004 mở lại *cho phạm vi giả lập*, không phải cho product).

## 7. Đo adherence & attribution (trả lời #2)

### 7.1 Taxonomy adherence (per advice)

| Loại | Định nghĩa đo được trong sim |
| --- | --- |
| `EXPLICIT_FOLLOW` | actor đổi hành động sang đúng advice spec trong time window (hành động trước advice ≠ hành động sau) |
| `COINCIDENT` | actor thực hiện hành động khớp advice spec nhưng twin của nó ở arm B (cùng seed, cùng thời điểm) cũng làm vậy ⇒ "đằng nào cũng làm", KHÔNG tính công cho advisor |
| `PARTIAL` | làm theo một phần (đúng hành động, lệch thời gian/địa điểm quá tolerance) |
| `IGNORE_ACTIVE` | thấy advice (đã hiển thị) nhưng hành động khác hẳn |
| `UNSEEN` | advice phát nhưng actor bận (đang on-trip…) — mô phỏng việc tài xế thật không đọc màn hình |

- **Advice spec** phải machine-checkable: `(action_type, target_window, target_cell/station hoặc none, expiry)` → so khớp với event log của actor bằng rule, không cần hỏi actor.
- **Twin-diff attribution**: vì có arm B cùng seed, với mỗi advice ta so hành vi actor i quanh thời điểm t ở A và B: nếu A đổi mà B không → thay đổi *do advice*; nếu cả hai cùng đổi → coincident. Đây là lợi thế chỉ có trong sim, giải đúng nỗi băn khoăn "tài xế có kinh nghiệm tự làm đúng".
- **Adherence model** (input của sim, không phải output): xác suất nghe theo = logistic(giá trị kỳ vọng advice cảm nhận được, độ tin của actor với advisor (tăng/giảm theo lịch sử advice đúng/sai), độ bận, độ trái thói quen). Tham số theo archetype; calibrate sau bằng dữ liệu thật nếu có.
- Với sản phẩm thật sau này: cùng taxonomy nhưng đo bằng `advice_shown/viewed/acted` events + behavioral matching trong window; không có twin nên attribution yếu hơn (ghi rõ hạn chế). ▸RESEARCH: mapping sang ITT/CACE chuẩn.

### 7.2 Report adherence

- adherence rate theo loại × archetype × loại advice; funnel: phát → hiển thị → thấy → theo (một phần/đủ) → outcome.
- hiệu quả có điều kiện: Δ payout của nhóm EXPLICIT_FOLLOW vs IGNORE (cùng archetype, cùng seed) — nhưng luôn kèm twin-diff để khử selection bias (người chăm nghe có thể vốn giỏi hơn).

## 8. Visualization & phân tích (trả lời #1 "dễ theo dõi, dễ phân tích")

Ba lớp (đề xuất sơ bộ — ▸RESEARCH sẽ chốt stack cuối trong `research/simulation/tooling.md`):

1. **Spatial replay**: xuất event log → **kepler.gl** (H3 layer + time playback, export file HTML tự chạy không cần server) để xem phim: demand nổi lên theo cell, tài xế di chuyển, hàng chờ trạm. So sánh A/B bằng 2 panel cùng timeline hoặc layer chênh lệch.
2. **Dashboard chỉ số**: **Streamlit + Plotly**: chọn run/seed/kịch bản, bảng Δ metric + CI, đường tích lũy payout theo giờ, boxplot theo archetype, heatmap mismatch, queue trạm theo thời gian.
3. **Experiment tracking**: mỗi run ghi config + seed + metrics vào **MLflow** (hoặc parquet + DuckDB nếu muốn nhẹ) để so sánh giữa các phiên bản advisor/optimizer.

Alternatives đang cân nhắc: pydeck (nhúng deck.gl trong notebook/Streamlit), Folium (tĩnh, nhẹ), Grafana (nếu muốn theo dõi live khi sim chạy dài). Lưu ý .env: kepler.gl/pydeck có thể cần **Mapbox token** cho basemap đẹp (có fallback không token) — sẽ xin Cường khi build (§10).

## 9. Kịch bản đánh giá tối thiểu

1. Ngày thường khô — sanity + hiệu quả cơ bản.
2. Ngày mưa giờ tan tầm — demand tăng, advice sạc/nghỉ phải né peak.
3. Demand thấp (CN sáng) — advice "nghỉ/kết ca sớm" có bảo vệ tổng payout/h không.
4. Sự kiện lớn 1 khu (concert) — advice có khai thác event mà không dồn cung quá mức.
5. **Stress herding**: 100% adoption + advisor tắt capacity-ledger vs bật — chứng minh cơ chế chống tắc trạm (#5) hoạt động.
6. Mất điện/1 trạm đóng — robustness khi capacity giảm đột ngột.
7. Adoption từng phần (30%/70%) — hiệu quả cho người dùng advisor khi phần lớn thị trường không dùng.

## 10. Biến môi trường / secrets dự kiến (xin Cường khi bắt đầu build)

| Biến | Dùng cho | Bắt buộc? |
| --- | --- | --- |
| `MAPBOX_TOKEN` | basemap kepler.gl/pydeck | không (có fallback) |
| `LLM_API_KEY` (Anthropic/OpenAI) | chỉ khi chạy advisor bản LLM-in-the-loop trong sim; bản đầu dùng advisor rule-based, không cần | chưa |
| `MLFLOW_TRACKING_URI` | nếu dùng MLflow server thay local folder | không |

## 11. Việc mở tiếp (đưa vào TODO)

- T-016 research đợt 3 (3 mảng: tooling, evaluation methodology, world params) — ĐANG CHẠY.
- T-017 chốt spec này v2 sau research + review của Cường/Khánh.
- T-018 build simulator core (world, actors, dispatcher, twin-runner).
- T-019 advisor-sim rule-based + capacity ledger.
- T-020 evaluator + dashboard + replay.
- T-021 calibration: đối chiếu output sim với các số tự khai trong `research/` (15–30 cuốc/ngày full-time, payout ngày…).
