# SPEC — SIMULATION OVERHAUL (mảng riêng, Track A) — master

Cập nhật: 2026-07-25 · Trạng thái: **SIM-1..5 + D-SIM-03/05/09/10/13 + SIM-XANH P0-P5 DONE** (UPDATE-044..058). Sim chạy ĐƯỜNG THẬT OSRM, có rating/tân-binh/mission, đo A/B có CI + sweep độ nhạy, dashboard palette-validated · Nguồn yêu cầu: `tracking/DIRECTIVES-2026-07-24.md` §5 (Cường: *"phần này rất quan trọng"*, *"nên tập trung làm thành riêng 1 mảng, có docs và plan riêng"*).

> **Sim là mảng ĐỘC LẬP.** UI app do **Khánh** phát triển; sim **không phụ thuộc UI**, chỉ nối **data output** vào sau (bên cạnh UI). Sim phục vụ: (1) kiểm chứng advisor bằng thế giới song song, (2) sinh/giải thích hành vi tài xế, (3) nguồn dữ liệu hành vi cho mock.

## 1. Yêu cầu Cường (chuẩn nghiệm thu)

1. **Giả lập THỰC SỰ** trên data đang dùng; tương lai thêm data thì **gán vào sim được**.
2. Tài xế **thật sự nhận cuốc, di chuyển, có mật độ** — như hiện tại **và hơn thế**.
3. **Thống kê chung** cho các metric.
4. **Dịch được advice của advisor → ACTION của actor** trong sim.
5. **State phải theo đúng data** (schema `l1r` thật).
6. **ĐẶC BIỆT — theo dõi hành trình 1 tài xế**: mở đầu phiên làm việc; **thế giới song song
   (tự làm vs làm theo chỉ dẫn)**; nhận cuốc thật; tỷ lệ nhận/hoàn thành; **hành vi random**;
   **đo metric trên đúng driver đó**; sim được **tài xế mới thiếu kinh nghiệm** (hành vi
   chưa tối ưu + hồ sơ mới nhiều thưởng) → **baseline tốt**.
7. Sửa các phần **"rất tệ"** — cụ thể tỷ lệ hoàn thành/phục vụ **quá thấp so thực tế** — và
   **làm chi tiết hơn**.

## 2. CHẨN ĐOÁN HIỆN TRẠNG (đo thật, seed 42, `configs/pilot_dongda.yaml`)

> ✅ **SIM-1 ĐÃ SỬA XONG cả 3 dòng dưới đây** (UPDATE-044, gate 30 seed):
> **served 61.9% → 82.3%** · **completion 99.6% → 94.7%** · **accept 96.3% → 91.0% và
> BÁM `accept_base` từng archetype** (P4 tân binh .781 vs P3 top .965). Giờ tệ nhất:
> 05h 94% hết hạn → **06h 33%**. Bảng dưới giữ lại làm **bản ghi khuyết tật gốc**.

| Metric | Sim hiện tại | Thực tế (research) | Kết luận |
|---|---|---|---|
| **served = matched/orders** | **61.9%** (774/1251) | mục tiêu **80–85%** (NYC 2015 ~82%; hệ cung cố định không surge 75–85%) | ❌ **38% cầu không ai nhận** — ĐÂY là "quá thấp" Cường nói |
| completed = dropoff/matched | **99.6%** | ~95% (có huỷ sau nhận, khách bom, sự cố) | ⚠️ **quá sạch** — sim không có huỷ sau khi nhận |
| accept = matched/(matched+declined) | **96.3%** (chỉ 30 decline) | **0.74–0.97 theo archetype** | ⚠️ **quá sạch** — tài xế gần như không từ chối |
| order_expired | 477/1251 (38%) | — | nguyên nhân trực tiếp của served thấp |

**ĐÍNH CHÍNH (SIM-1 đo lại kỹ hơn):** `realdata.py` KHÔNG "override mù" — nó **suy ngược**
accept/cancel từ `profiles.target_acceptance`; trips của BIKE thì vốn đã là sim thật. Và
tài xế **CAR/PREMIUM/RTO không có sim** nên target profile là cách sinh DUY NHẤT cho họ,
không phải "vá". SIM-1 vì vậy chỉ nối BIKE về counter sim, giữ nguyên phần còn lại.

**Phát hiện quan trọng (coherence bug xuyên tầng):** vì sim gần như không có `decline`, **data mock sinh ra từ sim từng có acceptance ≈ 1.00**. PI-2b đã vá ở **tầng data** (override theo archetype target 0.74–0.96) → **sim và data hiện KHÔNG NHẤT QUÁN** (data nói 0.88, sim hành xử 0.96). Overhaul phải sửa **tại gốc (sim)** rồi bỏ override ở tầng data.

**Nguyên nhân served thấp (giả thuyết cần chứng minh trong SIM-1):** `order_expire`/patience quá ngắn so với thực tế; số actor online hiệu dụng thấp (research đợt 5: FT chỉ online median ~4.5h dù thiết kế 8–10h); dispatcher chỉ tìm trong `grid_disk k=2`; không có hàng đợi/retry khi chưa có xe.

## 3. NGUYÊN TẮC THIẾT KẾ

- **Data-driven, không hard-code**: mọi tham số hành vi/policy đọc từ config + `l1r` schema thật; thêm data thật sau → chỉ đổi nguồn, không sửa engine.
- **State khớp schema `l1r`**: mọi thứ sim xuất ra phải map 1-1 vào 13 bảng (đã có `mockgen/realdata.py` làm cầu nối) → **sim là nguồn sinh data, không phải thế giới riêng**.
- **Deterministic + CRN**: cùng seed → cùng kết quả; **thế giới song song dùng CHUNG random stream** cho phần ngoại sinh (đơn hàng, thời tiết) để so sánh công bằng (paired-seed).
- **Hành vi random có cấu trúc**: mỗi archetype có phân phối riêng (accept, nghỉ, sạc, tốc độ phản ứng), không phải hằng số.
- **Advisor không được nhìn tương lai**: actor chỉ dùng thông tin có tại thời điểm đó.

## 3b. QUYẾT ĐỊNH ĐÃ CHỐT

- **Thế giới song song dùng ADVISOR PIPELINE DETERMINISTIC** (solver + template, KHÔNG gọi LLM live)
  — Cường chốt 2026-07-24 ("for now your default, update in future"). Lý do: tái lập được,
  miễn phí, và LLM chỉ diễn đạt lại số chứ không đổi số. **Sẽ xem lại sau** khi cần đo ảnh
  hưởng của câu chữ LLM tới adherence.

## 4. KIẾN TRÚC MỤC TIÊU

```
configs/ + l1r data  ─┐
                      ├─►  SIM ENGINE (SimPy)  ──►  events/state  ──►  mockgen → 13 bảng l1r
research benchmarks ──┘         │                                          │
                                │                                          ▼
                    ┌───────────┴────────────┐                    advisor (9 solver + C6)
                    │  WORLD A: tự làm       │                             │
                    │  WORLD B: theo advice  │◄── advice→action bridge ────┘
                    └───────────┬────────────┘
                                ▼
                     paired metrics (A vs B) + driver journey timeline
```

**Thành phần mới cần xây:**
- `AdviceActionBridge`: `ComposedAdvice.advice_spec` → hành động actor (`rest_window`, `swap`, `online`, `mission`, `reposition`…) + **mô hình tuân thủ** (adherence: explicit-follow / partial / ignore / unseen).
- `DriverJourney`: bản ghi chi tiết 1 tài xế theo timeline (phiên, cuốc, quyết định, thu nhập tích luỹ, metric).
- `ParallelWorld`: chạy 2 nhánh cùng seed, chỉ khác "có advisor hay không".
- `SimMetrics`: bộ metric chung + per-driver (served/accept/complete/util/idle/payout/points/khoán).

## 5. LỘ TRÌNH (mỗi phase = 1 cycle có plan + test riêng)

| Phase | Nội dung | Tiêu chí xong |
|---|---|---|
| **SIM-1 Realism gate** ✅ **DONE** 2026-07-25 (UPDATE-044) | Đã sửa cả 3 tại GỐC: phủ ca (P6 sáng sớm/P7 tối-đêm, n=74, patience 5ph theo nguồn), logit accept (`accept_base` = mức trung bình, kinh tế chỉ điều biến), huỷ-sau-nhận 5% (mất thời gian+pin thật), data BIKE đọc counter sim | ✅ served 82.3% · completion 94.7% · accept bám base ±4.3đ% · **30 seed** · 10 gate test `tests/test_sim_realism.py` · suite 388 xanh |
| **SIM-2 Driver journey** ✅ **DONE** 2026-07-25 (UPDATE-045) | `journey.py`: sessions · timeline (segment + idle suy ra) · từng offer kèm **LÝ DO** (`economics` vs `base_behavior`) + kết cục · thu nhập tích luỹ (cuốc **+ thưởng ngày**) · metric per-driver. Tab dashboard 🧭 + export JSON | ✅ 14 test bảo toàn trên **cả 7 archetype** (offer/thời gian/tiền/không chồng lấn/cộng ra hệ thống); **RNG không trôi** (so baseline seed 42+1000); suite 405 |
| **SIM-3 Advice→Action** ✅ **DONE** 2026-07-26 (UPDATE-046) | `advice_bridge.py`: S2 `shift_dp` → `IdleAction` + mô hình tuân thủ theo archetype; hook khi IDLE, mặc định TẮT; policy hợp nhất qua `to_core_record()` | ✅ 15 test: World A không đổi khi tắt · **không rò tương lai** · ánh xạ đúng ngữ nghĩa (BUG-SIM3-01) · bảo toàn SIM-2 giữ nguyên. Suite 420. ⚠️ **F-SIM3-A**: mới dùng 1/9 solver ⇒ Δ(B−A)≈0, SIM-4 sẽ ĐÁNH GIÁ THẤP advisor nếu chỉ đo với S2 |
| **SIM-4 Parallel worlds** ✅ **DONE** 2026-07-26 (UPDATE-047) | `parallel.py`: A/B chung seed (CRN), **hiệu theo cặp + CI bootstrap**, đo **thang bậc kênh** (attribution), guardrail hệ thống. Mở 2 kênh mới: `accept_lift` (cảnh báo tỷ lệ dưới ngưỡng thưởng) + `shift_extend` | ✅ 30 seed: `s2_only` Δ=**0** (xác nhận F-SIM3-A) · `+accept_lift` **+32.276đ** CI[+8.255,+58.480] · `all` **+42.471đ**. Guardrail served_rate không đổi. **Vách đá**: tuân thủ nửa vời LỖ 34k. 12 test, suite 432 |
| **SIM-5 Metrics + xuất data** ✅ **DONE** 2026-07-26 (UPDATE-049) | `sim_metrics.py` (chờ khách, mật độ hex×giờ, gộp per-driver TỪ journey) + manifest ghi `engine_commit` + `scripts/regen_mock.py`; **regen 90 ngày** từ engine mới | ✅ 4 vòng verify xanh; **BIKE 6/6 PASS, 0 GAP** (giờ online median 8.79h, trước gap ~4.5h); nhất quán sim↔data: acceptance data **0.909** ≈ sim **0.910**; suite 446 |

## 6. METRIC BẮT BUỘC (đo ở mọi phase)

- **Hệ thống**: served rate, expired rate, thời gian chờ khách, mật độ cung/cầu theo hex×giờ.
- **Tài xế**: accept rate, completion rate, cancel rate, util (occupied/online), idle phút, số cuốc, payout gross/net, điểm, tiến độ khoán tuần.
- **Advisor (A vs B)**: Δ payout, Δ util, Δ idle, adherence rate, và **guardrail**: advice KHÔNG làm xấu queue trạm/served của hệ thống.

## 7. RỦI RO / BẪY ĐÃ BIẾT

1. **Đừng "vặn tham số" để đẹp số** — research T-021 từng chốt *baseline chưa tối ưu là dư địa advisor*. Nay Cường yêu cầu realism ⇒ **phân biệt rõ**: `served` phải thực tế (80–85%), còn **dư địa advisor** nằm ở **hiệu quả tài xế** (util/idle/timing), không phải ở việc bỏ đói cầu.
2. **Không để advisor nhìn tương lai** (leak) khi so A/B.
3. **Coherence**: sim → data → solver phải cùng một sự thật; sửa ở gốc, không vá ở ngọn.
4. Sim chi tiết hơn = chậm hơn → cần giữ thời gian chạy chấp nhận được (đo, không đoán).

## 8. Không thuộc spec này
UI (Khánh). Ghép data thật GSM (D-GCP-01). Twin-world evaluator đầy đủ T-020 (kế thừa sau SIM-4).
