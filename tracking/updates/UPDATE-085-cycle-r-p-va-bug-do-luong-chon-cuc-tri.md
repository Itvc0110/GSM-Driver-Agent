# UPDATE-085 — Cycle R (gốc REST) + Cycle P (policy nền) + PHÁT HIỆN BUG ĐO LƯỜNG chọn-cực-trị

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** bugfix (solver + measurement-design) + feature nền (policy validity, cost ledger) + measurement
- **TODO liên quan:** Q-10(c) · T-045b · ① effective dating · **BUG-EVAL-ARGMAX (mới)**
- **Artifacts:** `22-sau-cycle-r-30seed.json` · `23-b3-positioning-only-30seed.json`
- **Verdicts nền:** Q-10 Cường chốt **(c) rồi (b)**; mục V-17/T-045b Cường uỷ quyền agent
  (quyết định ghi `PENDING-REVIEW` §Đã check xong)

## TL;DR — phát hiện quan trọng nhất ở CUỐI, đọc §4 trước nếu vội

1. **Cycle R** sửa gốc REST đúng cơ học (nghỉ thừa giảm 4×, `go_swap→rest` = 0) — nhưng payout
   tài xế đích KHÔNG hồi.
2. **B3** (tắt hẳn shift_plan, chỉ positioning) — tài xế đích **vẫn −33k** ⇒ giả thuyết
   "thủ phạm là shift_plan" **SỤP**.
3. Truy tiếp ⇒ **§4: cách đo đã dùng từ SIM-4 bị bias chọn-cực-trị** — `pick_target` lấy tài xế
   MAX-offers của thế giới A; đo không chọn lọc thì hiệu ứng trung bình P4 là **DƯƠNG nhẹ**.
4. Cycle P: `PolicyBundle.is_valid_at` 3 trạng thái + cảnh báo fail-loud · sổ chi phí riêng
   reconcile được · rename disutility. Mặc định zero-behavior (test bit-identical).

## 1. Cycle R — reproduce cả ba giả thuyết rồi mới sửa

| Giả thuyết | Reproduce | Fix |
|---|---|---|
| **H1** DP mù nghỉ-đã-nghỉ ⇒ tái áp mỗi consult | tổng nghỉ +16–27%; **11–14 lần/seed tái-khuyên REST ≤60′ sau một lần nghỉ** | `spi.rest_taken_min` + `shift_elapsed_min`; tín dụng trong `_required_rest` |
| **H2** hai mô hình sinh lý chồng nhau | (hệ quả H1 — `rest_min` gộp cả nghỉ bản năng) | giải cùng H1 |
| **H3** REST thắng SWAP khi hoà | fixture SOC=22% + demand phẳng ⇒ `ONLINE,REST,REST,SWAP` — nghỉ 2 bucket TRƯỚC đổi pin dưới ngưỡng; 7–12 `go_swap→rest`/seed | đổi thứ tự so sánh: SWAP xét trước REST (tie-break, không thêm số) |

### ⚠ Fix ĐẦU TIÊN của H1 bị số liệu BÁC BỎ (lần 3 trong 2 ngày)

Bản backfill `R = nhu_cầu_CẢ_CA − đã_nghỉ` làm advisory REST **nổ 55–66 → 145–178/seed**
(tổng nghỉ +39–54%): tài xế CHƯA nghỉ — vì đang bận kiếm tiền, điều tốt — bị đòi bù quá khứ.
Công thức chốt: **tín dụng đơn điệu an toàn** — chỉ phần nghỉ VƯỢT nhu cầu ca-đã-qua mới trừ
vào phần còn lại, bảo đảm `R_mới ≤ R_cũ` mọi input (có test quét lưới chống tái phạm).

**Sau fix (3 seed):** advisory 13–21 · tái-khuyên 2–4 · `go_swap→rest` **= 0** · tổng nghỉ
−4%…+14%. 7 test, mutation MR1/MR2/MR3 đều đỏ đúng chỗ, restore xanh. Schema L3 thêm 2 trường
optional (additive, giữ const 1.0.0 — B-02 registry đa phiên bản vẫn defer); whitelist
`test_input_has_no_future_fields` cập nhật có lý do (hai trường đều là QUÁ KHỨ thuần).

## 2. Cycle P — nền policy, zero-behavior mặc định

- **①** `PolicyBundle.effective_from/to` + `is_valid_at(as_of)` trả **True/False/None** —
  None = KHÔNG BIẾT, tách khỏi "còn hiệu lực" (bài học hidden-fallback soc_pct). World phát
  `policy_outside_validity` khi config meta khai hạn đã qua (wire-site test). Nền cho A1
  router-theo-policy.
- **T-045b** sổ chi phí riêng: `km_driven` accrue tại chốt chặn duy nhất `consume_soc`;
  `cost_vnd = km×cash + swaps×fee`, **mặc định 0 = đúng chính sách hiện hành** (miễn phí
  official tới 31/03/2029). Test reconcile từng actor + test **cost-không-rò-vào-payout** (§5).
- **Rename**: `cost_per_km_vnd` → `pickup_disutility_vnd_per_km` (3.000đ/km là CẢM NHẬN,
  không phải tiền mặt 30–250đ/km — hai khái niệm hai tên, nợ T-046).
- Sự cố nhỏ tự bắt: regex chèn code **vào trong docstring** `_settle_end_of_run` — sửa tay,
  ghi lại như lời nhắc không patch code bằng regex thiếu anchor.

## 3. Đo 30 seed (artifact 22 + 23) — hệ thống MẠNH LÊN, cá nhân "vẫn lỗ"

| Δ vs A | B0 chỉ shift_plan | B1 +wait_only | B2 +wait_and_relocate | **B3w CHỈ positioning** |
|---|---|---|---|---|
| payout tài xế đích | −35,5k SIG | −34,2k SIG | −32,6k SIG | **−33,2k SIG** |
| served_rate | ns | **+1,54đp SIG** | +1,34đp SIG | **+1,72đp SIG** |
| đơn hết hạn | ns | **−20,2 SIG** | −18,7 SIG | **−20,2 SIG** |
| Gini | ns | **GIẢM SIG** | GIẢM SIG | ns/giảm |
| HHI cung | ns | **GIẢM SIG** | GIẢM SIG | **GIẢM SIG** |
| tổng payout đội | ns | **+312k SIG** | **+413k SIG** | **+452k SIG** |
| veto(b) km-rỗng-tự-trả-tiền | PASS | **PASS** | **PASS** | **PASS** |

- Kênh vị trí sau Cycle R còn mạnh hơn b4 cũ; **B3w là cấu hình đẹp nhất về hệ thống**
  (đội +452k/ngày ≈ +5k/người, served +1,7đp) và **giờ cả Gini cũng cải thiện**.
- Sweep cash hậu kỳ (0/70/150đ/km — không cần chạy lại sim vì cost không đổi hành vi, có test):
  kết luận không đổi dấu ở mọi mức.
- **Nhưng "tài xế đích" lỗ ~33k Ở MỌI cấu hình, kể cả khi shift_plan TẮT** — bốn cơ chế khác
  hẳn nhau, cùng một con số. Đó không phải dáng của một hiệu ứng nhân quả. Truy tiếp ⇒ §4.

## 4. ⛔ BUG-EVAL-ARGMAX — cách đo "tài xế đích" bias âm CÓ HỆ THỐNG từ SIM-4

**Cơ chế**: `parallel.pick_target` chọn tài xế **MAX-offers của thế giới A** — chọn CỰC TRỊ.
Bất kỳ nhiễu loạn nào (bật advice làm event dịch chuyển) kéo cực trị về trung bình ⇒ Δ(B−A)
trên người đó **âm bất kể nội dung can thiệp**. Manh mối đã nằm sẵn trong số liệu: B1 đội
+312k mà "tài xế đích" −34k ⇒ 89 người còn lại +346k — người thua duy nhất là đúng người
được chọn theo cực trị.

**Chứng minh bằng sign-flip** (5 seed, cùng can thiệp B1):

| Cách chọn tài xế đo | mean Δpayout |
|---|---|
| argmax-A (cách hiện tại) | **−19.654đ** |
| argmax-B (cực trị phía kia) | **+27.416đ** ← dấu ĐẢO |
| **tất cả P4, không chọn lọc** | **+3.610đ** |
| toàn đội | +5.350đ/người |

**Hệ quả — các kết luận phải gắn nhãn CORRECTED-PENDING-REMEASURE:**
chuỗi số "advisor làm tài xế đại diện nghèo đi −17,3k/−24,9k/−38,4k/−17,5k/−32,9k/−40k"
(UPDATE-075/078/081/084 + artifact 09/16/17/21/22/23, đều dùng `pick_target` argmax-A) đo
**cực trị + hồi quy về trung bình**, không phải tác động nhân quả lên một tài xế đại diện.
**Các tầng HỆ THỐNG (served/expired/HHI/Gini/tổng payout) không bị bias này** — chúng là
aggregate không chọn lọc, mọi kết luận hệ thống giữ nguyên.

**Chưa kết luận chiều ngược lại**: +3,6k mean-P4 mới đo ở **5 seed** — chỉ đủ chỉ HƯỚNG
(chuẩn ≥30). Không được tuyên "advisor có lợi cá nhân" cho tới khi đo lại đúng chuẩn.

**Việc kế tiếp (cycle riêng, cần plan)**: sửa evaluator — tiêu chí 1 của ĐA-08 đổi từ
"Δpayout tài xế argmax-A" sang **mean Δpayout trên mọi tài xế được phủ (per-archetype)**,
giữ argmax như view chẩn đoán CÓ NHÃN BIAS; đo lại 30 seed; đính chính bảng số trong các
UPDATE bị ảnh hưởng. Ghi vào TODO **BUG-EVAL-ARGMAX**.

## Files bị ảnh hưởng

`src/gsm_core/solvers/shift_dp.py` (H1+H3) · `src/gsm_core/policy.py` (①) ·
`src/gsm_sim/{advice_bridge,world,entities,behavior}.py` · `schemas/l3/shift_plan_input.schema.json` ·
`configs/pilot_dongda.yaml` (cost keys) · tests: `test_rest_state_visibility.py` (7) ·
`test_cost_ledger.py` (5) · `test_advice_bridge.py` (whitelist) · artifacts `22-*`, `23-*`.

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| reproduce H1/H2/H3 | 3 seed instrument + fixture đơn vị — số trong §1 |
| TDD + mutation | MR1/MR2/MR3 + cost/validity tests; đỏ đúng chỗ, restore xanh |
| full suite | **629 passed / 5 skipped** (628+1 whitelist fix, chạy lại targeted 27 passed) |
| đo 30 seed × 5 cấu hình | artifact 22 (120 run) + 23 (60 run), CRN, A dùng lại |
| chẩn đoán bias | 5 seed × per-driver toàn đội — sign-flip bảng §4 |

## Visual verification

- **Status:** `BLOCKED` — gộp V-17. Thêm hạng mục: Gantt seed 1000 xem REST advisory thưa hẳn
  (13–21/ngày toàn đội) và không còn `go_swap → rest`.

## Adversarial self-review / flaws found

1. **Fix đầu tiên của chính tôi bị đo bác bỏ** (backfill) — giữ đúng kỷ luật đo-trước-tin,
   docstring ghi số để không ai đi lại.
2. **Swaps +4,7 SIG ở B0** sau reorder SWAP-trước-REST — nghi khuyên đổi pin non (H4).
   **CHƯA reproduce, CHƯA kết luận** — nhưng lưu ý nó có thể là hiệu ứng thật đang bị argmax
   che: sau khi sửa evaluator phải đo lại swaps theo estimator không bias.
3. **BUG-EVAL-ARGMAX do tôi phát hiện muộn** — nó nằm trong code từ SIM-4 (UPDATE-047) và tôi
   đã dùng nó suốt 10+ lượt đo trong 2 ngày mà không nghi ngờ, vì mỗi lượt "âm" đều có một
   câu chuyện nghe hợp lý. Cái lộ nó không phải review code mà là **một kết quả không thể
   giải thích được** (B3 tắt shift_plan vẫn −33k). Bài học: con số lặp lại kỳ lạ qua các can
   thiệp KHÁC NHAU là red flag của artifact đo lường, không phải của hiệu ứng bền.
4. Diagnostic 5 seed dùng B1; chưa lặp cho B0/B2/B3 (kỳ vọng cùng cơ chế — sẽ rõ khi đo lại
   30 seed bằng estimator mới).
5. `medianA_P4` trong diagnostic cũng nhiễu (một seed −70k) — trung vị của A vẫn là một dạng
   chọn theo A; estimator đúng là mean-không-chọn-lọc theo archetype.

## ⏳ Nhắc PENDING-REVIEW

`V-01..V-17` chờ; **Q-11 MỚI** (xem PENDING-REVIEW): duyệt đổi tiêu chí 1 ĐA-08 sang estimator
không bias. Q-03/Q-04/Q-07/B-02 vẫn treo.
