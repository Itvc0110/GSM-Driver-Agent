# Đối chiếu HAI CHIỀU sim ⇄ UI — nền cho C2 "một nguồn luật"

Ngày: 2026-07-27 · Nguồn: khảo sát agent + tự kiểm. Trả lời câu hỏi Cường: *"UI và sim phải chung
1 logic, 1 luật, 1 database. Kiểm tra xem chúng có thể học được gì từ nhau."*

## 0. UI hiện có BA đường dữ liệu tách rời (không phải một)

| Đường | Endpoint | Nguồn | Trạng thái |
|---|---|---|---|
| **A** mock 90 ngày | `/driver/*`, `/advice`, `/map-context` | parquet `realdata-v1` | lệch nhiều |
| **B** sim-engine LIVE | `/sim/*` | gọi thẳng `run_once` | ✅ **đã hợp nhất đúng — mẫu để nhân rộng** |
| **C** legacy synthetic/OSRM | `/routing/*`, `/trip/step` | `simulator.py`, `routing.py` | **không nối gì với sim/policy** |

## 1. HAI (BA) NGUỒN SỰ THẬT — xếp theo mức nguy hiểm

| # | Luật | Nguồn 1 (sim) | Nguồn 2/3 (UI) | Hệ quả |
|---|---|---|---|---|
| **1** 🔴🔴🔴 | **Cước một cuốc** | `gsm_sim/policy.py:75` `13.000 + 4.300/km sau 2km` | `routing.py:61,96` **`km × 24.000`** · `simulator.py` cước cứng 116k/85k/145k | Cuốc 5km: sim **25.900đ** vs routing **120.000đ** — **lệch 4,6×**. Số `24000` **không tồn tại ở bất kỳ config/spec nào**. Tài xế nhìn thấy trực tiếp. Không test nào bắt |
| **2** 🔴🔴🔴 | **Payout 1 tài xế 1 ngày** | `world.py` cộng **4 nguồn** vào `payout_vnd` | `mockdata.py:131-134` chỉ `commission + mission` | `/sim/journey` và `/driver/state` trả **hai số khác nhau** cho cùng tài xế cùng ngày |
| **3** 🔴🔴 | **"Mốc thưởng cao nhất đạt được"** | `gsm_sim/policy.py:99` `day_bonus()` — **CÓ gate** acceptance/completion | `gsm_core/policy.py:76` `bonus_at()` — **KHÔNG gate** | Gọi nhầm ⇒ hứa thưởng mà policy không trả. Cùng tên khái niệm, khác luật |
| **4** 🔴🔴 | **Policy đọc từ đâu** | — | advisor UI đọc `configs/*.yaml` **hôm nay**; tiền đọc từ parquet sinh lúc regen; **data không có bảng `policy_bundle`** | Sửa `day_bonus_tiers` → advisor khuyên mốc mới, data mốc cũ, **lệch câm** |
| **5** 🔴 | `trip_points` / `next_tier_gap` | `gsm_sim/policy.py:86,104` | `gsm_core/policy.py:55,66` | Chép nguyên văn, đang khớp, **không test nào ràng buộc phải khớp** |
| **6** 🔴 | **"Demand"** | λ **kỳ vọng** từ config (prior) | đếm cuốc **đã hoàn thành** (posterior, thiên lệch sống sót) | Cùng tên, cùng vẽ lên bản đồ, **ngữ nghĩa ngược nhau** |
| **7** 🟠 | Câu chữ có số cho tài xế | backend qua verifier | **`cards.js:120-122` tự ghép `fmtVnd(...)` ở frontend** | **Lỗ thủng của chính guardrail R5-A** — verifier chỉ soi title+message backend |
| **8** 🟠 | Giờ kết ca | `entities.py:33` theo archetype + nới ca | `advisor.py:24` hằng `22*60` | `hours_budget_remaining` sai với mọi tài xế không kết ca 22h |

## 1b. 🔴🔴🔴 `already_maxed` che mất `feasible` — advisor trấn an tài xế SẮP MẤT TOÀN BỘ THƯỞNG

**(phát hiện 2026-07-27, trong lúc chuẩn bị C2 — nặng hơn mọi mục ở §1)**

AUDIT A1 (UPDATE-065) đã sửa **solver** cho trung thực: đủ điểm mốc cao nhất nhưng tỷ lệ dưới
ngưỡng ⇒ `feasible: False` + `infeasible_reason` + caveat (có test
`test_already_maxed_below_threshold_flags_risk`). **Nhưng cả BA consumer đều rẽ nhánh
`already_maxed` TRƯỚC khi đọc `feasible`**, nên sự trung thực đó không bao giờ tới tài xế:

| # | Nơi | Code | Tài xế thực sự nhận được |
|---|---|---|---|
| a | `gsm_core/advisor/templates.py:186` | `if sol.get("already_maxed"): return "…đã đạt mốc thưởng cao nhất hôm nay."` | câu **trấn an** |
| b | `gsm_sim/advice_bridge.py:453` | `return False, "already_maxed"  # khuyên thêm là thừa` | **im lặng hoàn toàn** |
| c | `ui/backend/app/adapters/advisor.py:132` | silent card `already_on_track`: *"không có gì cần chỉnh. Giữ nhịp hiện tại."* | **"mọi thứ ổn"** |

**Kịch bản hại**: tài xế 210 điểm (kịch mốc), `acceptance = 0.80 < 0.85`. Chính sách sẽ trả **0đ**.
Solver biết và nói `feasible=False`. Advisor nói *"không có gì cần chỉnh"*. Đây là **mất tiền thật,
đúng lúc còn kịp cứu**, và nằm ở **đường im lặng** nên không ai để ý.

Cùng dạng lỗi với #1 (cước): bản sửa nằm một tầng, **các consumer không biết**. Khác ở chỗ nó
không hiện số sai — nó **giấu mất cảnh báo**, nguy hiểm hơn vì không nhìn thấy được.

**Sửa (C2, ưu tiên số 1)**: `already_maxed` **không được là nhánh sớm**. Thứ tự đúng:
`already_maxed AND feasible` → trấn an; `already_maxed AND NOT feasible` → **cảnh báo giữ tỷ lệ**
(cả 3 consumer). Test phải chạy ở **mức consumer**, không chỉ mức solver — test hiện có xanh trong
khi cả 3 consumer đều sai.

### 1c. 🔴🔴 Anh em cùng dạng ở S5 `weekly_khoan` — CHƯA SỬA

Quét theo **mẫu lỗi** của §1b ("consumer rẽ nhánh theo cờ trạng thái mà không đọc cờ đúng-sai")
tìm ra ngay một ca nữa:

- `solvers/weekly_khoan.py:91` tính `feasible = gap == 0 or (enough_hours and days_ok)` và
  `infeasible_reason` (vd *"cần ~40 giờ nhưng quỹ tuần còn 12 giờ"*).
- `advisor/templates.py:48 _khoan_sentence` là **consumer DUY NHẤT** — và nó đọc
  `quota_available`, `gap_revenue_vnd`, `clawback_risk_vnd`, **KHÔNG bao giờ đọc `feasible`**.

⇒ Khi khoán tuần **không thể đạt được**, advisor vẫn nói *"Tuần này còn thiếu Xđ doanh số để đạt
khoán. Nếu không đạt, phần chưa đạt có thể bị truy thu khoảng Yđ."* — vừa **ngụ ý mục tiêu với
tới được**, vừa **treo doạ truy thu**. Đẩy tài xế đuổi theo thứ không thể đạt.

**Chua nhất**: docstring của `_gap_sentence` ngay bên dưới (AUDIT A3 LAYEROUT-2, UPDATE-070) ghi
đúng nguyên tắc — *"câu 'còn thiếu X để đạt mốc Y' CHỈ được nói khi solver bảo KHẢ THI"* — nhưng
bản sửa đó **chỉ áp cho S1**, không áp cho S5 dù câu chữ cùng dạng.

Sửa: `_khoan_sentence` phải đọc `feasible`; infeasible ⇒ nói thật là tuần này khó đạt + lý do theo
nhãn cấu trúc (không chèn `infeasible_reason` thô — nó chứa số chưa neo registry ⇒ V1 veto).

**Phạm vi ảnh hưởng — nhỏ hơn §1b, phải nói rõ:** `weekly_khoan` chỉ được gọi từ **pipeline C6**
(router F1/F3 → templates), **không** có trong đường `ui/backend/app/adapters/advisor.py` mà app
tài xế đang dùng. Vì F0 free-chat đang bị bỏ theo hướng cards, bán kính nổ hiện tại hẹp. Nhưng khi
khoán tuần lên card (S5 nằm trong scope F1/F3) thì nó thành lỗi driver-visible ⇒ **sửa trước khi
đưa S5 lên cards**, không để lặp lại đúng vết xe của §1b.

## 2. RÒ TƯƠNG LAI mới phát hiện trong UI advisor

`advisor.py:94-96` lấy `acceptance_rate`/`completion_rate` từ `driver_statistic_daily` của **chính
ngày đó** — aggregate CẢ NGÀY. Ở `now_min = 9:00`, S1 **đã biết tỷ lệ cuối ngày**. Đây là **leak**,
không chỉ là "granularity thô" như comment hiện ghi. Đúng loại lỗi mà `advice_bridge.py:24-27` viết
hẳn một đoạn docstring để cảnh báo. Ba chỗ khác trong cùng file thì cắt đúng (`_points_until`,
`hours_budget`, `_hist_rate` chỉ dùng ngày trước).

## 3. Học hai chiều

**SIM có → UI nên học**: công thức cước versioned · tách 4 nguồn tiền + `bonus_share` · kỷ luật
as-of không rò tương lai · nhiều kênh advice có attribution + adherence + RNG stream riêng ·
state ngày tường minh (`_DAILY_RESET_*`) · `skipped_advice` (đo cả lời khuyên đã TỪ CHỐI đưa).

**UI có → SIM nên học**: **verifier fail-closed** (sim thi hành thẳng output solver, không kiểm) ·
`numbers[].source` + `render_number_vn` một nguồn format · guard "chưa đủ policy thì IM LẶNG" ·
**đo adherence THẬT bằng nút bấm** (chính là dữ liệu `advice_bridge.py:59-63` đang thiếu để hiệu
chỉnh `DEFAULT_ADHERENCE`) · contract JSON-Schema + test hợp đồng · `est_net_vnd=None` +
`definition_version`.

## 4. Mẫu hợp nhất ĐÃ ĐÚNG (nhân rộng cho C2)

1. `gsm_sim/policy.py:29 to_core_record()` — **một cầu nối duy nhất**, 3 nơi dùng chung.
2. `ui/backend/app/routers/sim.py:18` — import thẳng `_cfg_with`/`_driver_metrics`/`_system_metrics`
   từ `gsm_sim.parallel` thay vì chép logic. **Đây là khuôn mẫu chuẩn.**

## 5. Thứ tự fix đề nghị (C2)

0. **`already_maxed` che `feasible`** (§1b) — **ưu tiên cao nhất**, mất tiền thật, cả 3 consumer.
1. ✅ **Cước** (#1) — **XONG 2026-07-27 (UPDATE-075)**: `routing.py` gọi `_gross_fare()` → cùng
   `PolicyBundle` với sim; test `test_ui_fare_equals_sim_policy` + test chặn hằng số `24000` quay lại.
2. **Seed/định danh** — `advice` đang khai `"seed": 0` trong khi data là seed 7000 (mâu thuẫn ngay
   trong một response) → `SourceEnvelope` chung.
3. **Leak acceptance** (#2 §2) — cần event-level accept/decline; 13 bảng không có ⇒ dùng prior
   pooled ngày trước (đúng hướng ĐA-01 đã duyệt).
4. **Payout 4 nguồn** (#2 §1) — project từ ledger.
5. **`bonus_at` vs `day_bonus`** (#3) — hợp nhất một hàm có gate, hoặc đổi tên cho hết mơ hồ.
6. **`cards.js` recap** (#7) — số phải lấy từ payload đã verify, không tự ghép.
