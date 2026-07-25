# UPDATE-046 — SIM-3 "Advice → Action": cầu nối gợi ý advisor thành hành động actor

Ngày: 2026-07-26 · Track: **A (SIM overhaul)** · Phase: **SIM-3 / 5**
Spec: `specs/simulation/00-sim-overhaul-master.md` §5 · Chỉ thị: `DIRECTIVES-2026-07-24.md` §5.4
Tiếp nối: UPDATE-044 (`9de4074`), UPDATE-045 (`aa58998`)

## 1. Vì sao

Cường §5.4: ***"Dịch được kết quả gợi ý của advisor → action của actor trong simulation."***
Không có cầu nối này thì "làm theo chỉ dẫn" ở SIM-4 chỉ là chữ.

Khảo sát cho thấy vốn liếng đã sẵn: solver **S2 `shift_dp`** ra từ vựng **ĐÓNG** (`ONLINE` /
`REST` / `SWAP` / `END`), actor nhận từ vựng đóng (`IdleAction`). ⇒ cầu nối là **ánh xạ từ vựng
sang từ vựng**, không phải hiểu ngôn ngữ tự nhiên.

## 2. Đã làm gì

- **`src/gsm_sim/advice_bridge.py` (MỚI)** — `AdviceActionBridge.consult()`: dựng
  `shift_plan_input` (schema L3) từ trạng thái HIỆN TẠI của actor → gọi `shift_dp.solve()` →
  ánh xạ hành động → **mô hình tuân thủ** theo archetype.
- **`world.py`** — hook hỏi advice khi actor IDLE, đặt **SAU** `choose_idle_action` có chủ ý:
  bản năng vẫn chạy và vẫn tiêu RNG y như World A ⇒ bật advice **không dịch dòng ngẫu nhiên**
  (điều kiện để paired-seed/CRN của SIM-4 có nghĩa). Event mới `advice_given` / `advice_followed`.
- **`configs/pilot_dongda.yaml`** — khối `advice:` **mặc định TẮT**; `coverage: single` (Cường
  chốt 2026-07-26: mặc định 1 tài xế để SIM-4 đo được ảnh hưởng RIÊNG, không lẫn hiệu ứng cả
  thị trường cùng đổi hành vi).
- **`gsm_sim/policy.py`** — thêm `to_core_record()`: **nguồn chuyển đổi DUY NHẤT** giữa
  `PolicyBundle` của sim và của `gsm_core` (hai lớp khác nhau: sim có `day_bonus`, core có
  `bonus_at`). `mockgen/adapter_sim.py` đổi sang dùng chung hàm này ⇒ tầng data và tầng advisor
  không thể nói hai con số policy khác nhau (đúng bài học coherence của SIM-1).

## 3. Hai cái bẫy đã tránh (ghi lại để đừng ai mở lại)

1. **`next_action` KHÔNG phải hành động tức thời.** `shift_dp` định nghĩa nó là *"action đầu
   tiên KHÁC ONLINE trong CẢ lịch"* — có thể nằm cách hiện tại vài **tiếng**. Dùng ngay sẽ bắt
   tài xế nghỉ sớm 2-3h. ⇒ hành động tức thời lấy từ **`schedule[0]`**; `next_action` chỉ để
   giải thích.
2. **Rò rỉ thông tin tương lai.** `demand_forecast` dựng từ `World._actor_demand_hint()` —
   trường kỳ vọng từ CONFIG × nhiễu cá nhân, đã chứng minh không đọc realized trace từ M0-3.
   **Không** dùng `world.orders` của phần còn lại trong ngày.

## 4. Bug thật phát hiện & sửa

**BUG-SIM3-01 — ánh xạ `ONLINE → WAIT` sai ngữ nghĩa, gây HẠI đo được.**
`ONLINE` của solver nghĩa là *"khung này nên ở trạng thái làm việc"* — nó **không** nói đứng yên
hay dịch chuyển. Nhưng trong sim `WAIT` = **đứng im chờ đơn**, còn `RELOCATE` = sang ô đông khách
hơn; **cả hai đều là đang-online**. Ánh xạ cũ biến lời khuyên "cứ chạy tiếp" thành mệnh lệnh
"đứng im", **ghi đè cả RELOCATE**.

Đo trên d-42 (P4, seed 1000): **14 → 11 cuốc · payout 214.400 → 155.376đ · util 0.34 → 0.26 ·
idle 148 → 215ph**. Tức là advice làm tài xế **nghèo đi vì lỗi DỊCH**, không phải vì advisor kém —
đúng loại lỗi sẽ khiến SIM-4 kết luận "advisor có hại" một cách sai.

**Fix:** `ONLINE` = **không can thiệp** (`None`), để bản năng chọn giữa WAIT/RELOCATE. Cũng khớp
ranh giới sản phẩm `D-004` (advisor không chỉ định ô/reposition). Có test khoá riêng.

## 5. Kết quả đo (5 seed, advice bật cho 1 tài xế P4)

| | cuốc | payout TB | util TB |
|---|---|---|---|
| World A (tự làm) | 78 | 243.090đ | 0.373 |
| World B (theo chỉ dẫn) | 77 | 239.917đ | 0.370 |

**Δ(B−A) ≈ −3.173đ/ngày, −1 cuốc** — trong khoảng nhiễu.

Lý do rõ ràng khi nhìn phân bố lời khuyên: **solver nói `ONLINE` 61/64 lần**, chỉ 3 lần khuyên
khác (2 SWAP, 1 REST). Tuân thủ: 39 follow / 25 ignore (khớp `P4 = 0.75` sau khi trừ các lần
ONLINE không can thiệp).

**Kết luận trung thực: cầu nối CHẠY ĐÚNG, nhưng S2 gần như không có gì để khuyên tài xế này.**
Không "vặn" tham số để Δ đẹp lên — xem F-SIM3-A.

## 6. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/advice_bridge.py` | **TẠO** |
| `src/gsm_sim/world.py` | sửa — hook advice khi IDLE + 2 event |
| `src/gsm_sim/policy.py` | sửa — `to_core_record()` (nguồn chuyển đổi duy nhất) |
| `src/gsm_core/mockgen/adapter_sim.py` | sửa — dùng chung `to_core_record()` |
| `configs/pilot_dongda.yaml` | sửa — khối `advice:` (mặc định TẮT) |
| `tests/test_advice_bridge.py` | **TẠO** — 15 test |

## 7. Kiểm chứng

- **Full suite: 420 passed, 5 skipped** (trước 405).
- **World A KHÔNG đổi khi advice tắt**: so `summarize()` + counter seed 42/1000 với baseline
  ghi trước cycle → **giống hệt từng con số**.
- **Không rò tương lai**: test bơm `demand_hint_fn` giả trả giá trị nhận dạng được — forecast
  phải chứa đúng giá trị đó (nếu lấy từ nguồn khác sẽ lệch). Thêm test chặn khoá lạ trong input.
- **Ánh xạ đúng ngữ nghĩa**: `ONLINE→None`, `SWAP→GO_SWAP|GO_CHARGE theo fleet`, `REST/END` trực tiếp.
- **Bảo toàn SIM-2 vẫn giữ khi advice bật** (offer/tiền/thời gian).
- **Chi phí**: 1.11× thời gian chạy khi bật cho 1 tài xế (ngưỡng plan: ≤1.3×). ✅

## 8. Adversarial self-review / flaws found

1. **Trôi RNG** — đã chặn: bridge dùng dòng riêng `seed ^ 0xADD1CE`, và hook đặt SAU
   `choose_idle_action` nên bản năng vẫn tiêu RNG như cũ. ✅
2. **Rò tương lai** — đã có test chuyên biệt (rủi ro số 1 của SIM-4). ✅
3. **Hai nguồn policy** — đã hợp nhất qua `to_core_record()`. ✅
4. **Ngữ nghĩa ánh xạ** — BUG-SIM3-01, đã sửa + khoá test. ✅

**FLAW ghi nhận (không che):**

- **F-SIM3-A (TRUNG BÌNH) — cầu nối mới chỉ dùng 1/9 solver.** Chỉ **S2 `shift_dp`** sinh ra
  hành động thuộc action-space của actor. 8 solver còn lại (S1 bonus, S6 mission, S7 idle…) ra
  lời khuyên **thông tin** hoặc về **hành vi nhận đơn**, mà actor hiện không có kênh nào để thực
  thi. Đây là lý do Δ(B−A) ≈ 0: **không phải advisor vô dụng, mà là kênh tác động còn hẹp**.
  ⇒ SIM-4 nếu chỉ đo với S2 sẽ **đánh giá THẤP advisor một cách hệ thống**. Cần mở action-space
  (vd: advice ảnh hưởng `accept_base` tạm thời, hoặc chọn mission) — cycle riêng.
- **F-SIM3-B (TRUNG BÌNH) — `adherence_by_archetype` là ASSUMPTION, chưa có số thật.** Đặt tân
  binh 0.75 / lão làng 0.30 theo lập luận, **không theo dữ liệu**. Mọi kết luận SIM-4 dạng
  "advisor giúp tân binh nhiều nhất" sẽ **thừa hưởng giả định này**. Cần khảo sát tài xế hoặc
  A/B thật để hiệu chỉnh. Có test khoá chiều so sánh để ai đổi tham số thì biết mình đang đổi gì.
- **F-SIM3-C (THẤP) — bật advice cho 1 tài xế vẫn làm đổi kết quả 73/73 tài xế khác.** Đây
  **KHÔNG phải bug RNG** mà là **khớp nối thị trường thật**: đơn người này không nhận sẽ sang
  người khác. Cần nhớ khi diễn giải SIM-4: Δ trên tài xế đích đã bao gồm phản ứng của thị trường.

## 9. Docs cập nhật kèm theo

`specs/simulation/00-sim-overhaul-master.md` (SIM-3 DONE) · `tracking/TODO.md` ·
`tracking/DEFERRED.md` (F-SIM3-A/B) · `tracking/PENDING-REVIEW.md` (V-04).

## 10. Visual review

**Status: `DEFERRED` (V-04)** — Cường đang hoãn check, cho phép chạy tiếp. Cần xem khi rảnh:
tab 🧭 với `advice.enabled=true`, `single_actor_id` = tài xế P4 — kiểm các mốc advice trên
timeline và cột "theo/không theo".

## 11. Follow-up

- **SIM-4 parallel worlds** — sẵn sàng, NHƯNG đọc kỹ F-SIM3-A trước khi diễn giải kết quả.
- `D-SIM-02` (thưởng tân binh) vẫn chờ Cường chốt (Q-01) — **chặn** baseline tân binh của SIM-4.
