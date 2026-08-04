# TODO — Backlog công việc

> 📋 **THỨ TỰ THI CÔNG HIỆN HÀNH: `tracking/PLAN-2026-07-30-hang-doi-cong-viec.md`**
> Hàng đợi đã sắp thứ tự + acceptance + chi phí cho từng mục, kèm §8 *"việc KHÔNG làm và vì sao"* để không ai đào lại. Thứ tự: ~~`L1-04`~~ ✅ **XONG (UPDATE-107) — Δ=0 tuyệt đối, giả thuyết ban đầu "28% mất hẳn" BỊ BÁC bởi chính phép đo** → ~~cổng thống kê~~ ✅ **ĐÃ CHỐT (UPDATE-103) VÀ ĐÃ NỐI (UPDATE-107)**: z Poisson-binomial `|z|>4` chạy thật trong `run_ladder` → 🔴 **`E10` advisor-cũng-nhiễu** — nay không còn bị chặn bởi `L1-04` → 3 tiên quyết cổng `rest_window` → cycle đường SẢN PHẨM (13 finding sev CAO) → `E9`.
> ⚠ `E10` đứng trên mọi thí nghiệm kênh khác **không phải vì nó mới** mà vì advisor hiện nhận **đúng λ của generator** trong khi tài xế chỉ nhận `λ×nhiễu` ⇒ `T-047` §4 xếp con số chủ lực **+6.016đ vào cột LUNG LAY**. `E10` quyết định các Δ khác có nghĩa gì.


> **⚠ ĐỌC TRƯỚC: [`PROJECT-GRAPH.md`](PROJECT-GRAPH.md), sau đó [`DIRECTIVES-2026-07-24.md`](DIRECTIVES-2026-07-24.md)** — graph route tài liệu và chỉ thị chương trình
> của Cường (data luôn MOCK + local-only; external API keys; **SIM overhaul là mảng riêng ưu tiên
> cao nhất**; mock UI xem advice; C7 + rà soát định kỳ mô hình tối ưu). File đó THẮNG khi xung đột.

Cập nhật: 2026-07-29 (**Cycle P/R/V/W**; xem `tracking/PLAN-cycle-wx-2026-07-29.md` cho kế hoạch đang thực thi — Phần A đã xong, Phần B đang làm; legacy CORE rows retained for traceability). Trạng thái: `TODO` / `READY` / `DOING` / `VALIDATING` / `DONE-CODE` / `WAITING-VERDICT` / `BLOCKED` / `QUOTA-BLOCKED`. Owner theo cơ chế **tự nhận việc (self-claim)** — xem `ASSIGNMENTS.md`. Xong việc phải có UPDATE trong `tracking/updates/`.

> **⚠ PHIÊN 2026-07-28 — đọc [`OPEN-THREADS-2026-07-28.md`](OPEN-THREADS-2026-07-28.md)**: việc
> dang dở + **ý tưởng kiến trúc của Cường chưa có spec** (agent làm ROUTER trên không gian solver
> có điều kiện theo chính sách · cache theo `problem_digest` · thiết kế lại objective theo policy
> sống/chết). Trong đó có cả trả lời "structured data hay text" và thứ tự phụ thuộc đề nghị.

## REVIEW-092 — sổ tra hạn chế (2026-07-29, docs-only)

> **Đọc [`updates/UPDATE-092-review-doc-lai-han-che-va-cai-thien.md`](updates/UPDATE-092-review-doc-lai-han-che-va-cai-thien.md)**
> — mỗi mục dưới đây có commit/file/dòng/logic để kiểm chứng lại. Không mục nào đã được duyệt
> hướng sửa; sửa phải qua plan mode.

| Mã | Việc | Trạng thái | Mã tra trong UPDATE-092 |
|---|---|---|---|
| **B6-PARITY** | **UI mới chạy 1/9 solver (`ui/backend/app/adapters/advisor.py:190` chỉ gọi `bonus_feasibility`) ⇒ A/B đang đo sản phẩm KHÁC sản phẩm ship** | `TODO` **HIGH** | H-06 |
| `REVIEW-092-1` | Đo nhân quả TỪNG LƯỢT advice — join `decision_id` → tiền. ⚠ **Cấm** so thẳng follow-vs-ignore (adherence lệch theo archetype ⇒ BUG-EVAL-ARGMAX thứ ba) | `TODO` **HIGH** | H-01 |
| `REVIEW-092-2` | Counterfactual branch ngắn tại thời điểm advice (`world.py` chưa có branch/snapshot) | `TODO` **HIGH** | H-02 |
| `REVIEW-092-3` | Chốt định nghĩa adherence: DECISION (76,9%) hay EVENT (53,6%) | `WAITING-VERDICT` | H-05 |
| `REVIEW-092-4` | Cầu co giãn theo thời gian chờ (`demand.py` ngoại sinh hoàn toàn) | → `DEFERRED` | H-03 |
| ~~—~~ | ~~Nợ Cycle W: W-6 · F-6 · W-7 · W-4-regex · 5 test `.pending` · fingerprint~~ | ✅ **ĐÓNG bởi `5364395`** (verify lại từng cái trên code mới) | H-04-bis |
| **`REVIEW-092-5`** | **`src/gsm_core/schema_registry.py:143` dựng `Draft202012Validator` KHÔNG truyền `format_checker` ⇒ từ khoá `"format"` vô hiệu lực trên MỌI schema.** `5364395` sửa triệu chứng (siết regex schema lifecycle) chứ không sửa nguyên nhân — **15 schema khai `date-time` mà không có `pattern` dự phòng** hiện không validate ngày giờ gì cả (`advisor/advice_request` · `composed_advice` · `solver_report` · `l0/policy_bundle` · `l1/app_event` · `gps_ping` · `payout_ledger` · `policy_change_event` · `swap_transaction` · `trip_record` · `l2i/inferred_activity` · `l3/allocation_input` · `bonus_gap_input` · `shift_plan_input` · `shift_plan_input@1.0.0`). **Reproduce:** `bonus_gap_input.t_now = "KHONG-PHAI-NGAY-THANG"` → `validate()` trả `[]` | `TODO` **MED** | H-04-bis |
| — | Nhắc lại nợ cũ có bằng chứng mới: T-045c (đơn bỏ oan chưa đo lại) · T-045e (`soc_pct=None` ⇒ DP giả định pin đầy) · D-SIM-16 (autocorr ngày≈0) · A1 router-theo-policy · A2 cache theo `problem_digest` · nhánh `costs` trong `policy_bundle` schema | `TODO` | H-08..H-12 |
| — | **⚠ ĐÍNH CHÍNH `OPEN-THREADS` §B3 (2 mục đã LÀM RỒI, đừng làm lại):** `effective_from/to` + `is_valid_at` tri-state **ĐÃ CÓ** (`gsm_core/policy.py:29-34,54-55,58-72`) — chỉ còn thiếu `as_of` per-request + fail-closed + `meta.policy_effective_from` trong config pilot. T-045b **ĐÃ CÓ** (`behavior.py:58,86-91` đổi tên `pickup_disutility_vnd_per_km`; sổ `actor.cost_vnd` ở `world.py:97-98,349-352`; config `pilot_dongda.yaml:268-269`) — chỉ còn thiếu **quét độ nhạy với số ≠ 0** | `CORRECTED` | H-08, H-12a |

**Đã sửa ngay trong cycle này:** lệnh validation §9 của `PROJECT-GRAPH.md` đang **FAIL** — 18 UPDATE
(074–091) không có link trong graph. Đã thêm §3.7.

**Đã CẢI THIỆN THẬT (đừng mở lại):** chống dồn cung 3 tầng (`features/market_state.py:80-103` ·
`sim/market_state.py:37-62` · `capacity_alloc.py`) và equilibrium đã đo bằng số (UPDATE-088) —
nhận xét cũ *"solver coi môi trường là ngoại sinh"* **đã bị code vượt qua ở tầng sim**.

## Current-state checkpoint 2026-07-27

- **T-040 — DONE (docs/research):** reconcile toàn codebase về data 90 ngày, schema/update path,
  simulation↔driver-app parity, Advisor capabilities/ignore UX/goals/recap và ĐA-01..06. Dossier:
  `research/audit/2026-07-27-current-state/`; **UPDATE-082** (đổi số từ 073 — remote đã chiếm 073).
- **DECISION architecture B:** simulation demo = dispatcher/researcher evaluation view; driver app
  demo + Advisor = single-driver view; hai projection dùng chung canonical run/snapshot/ledger.
- **ĐA-01..03 APPROVED-DESIGN, NOT IMPLEMENTED.**
- **ĐA-04..ĐA-09 + `specs/advisor-objective-model-v2.md` DUYỆT 2026-07-27** (Cường: *"oke duyệt
  hết"*). Chi tiết verdict trong `PENDING-REVIEW.md` §Đã check xong.
  **ĐA-04 → `DONE-CODE` 2026-07-29 (UPDATE-099)**: nhịp nói MỘT LUẬT dùng chung sim+UI +
  keyed adherence draw. Washout D-A3-01/D-SIM-14 CHẾT (decision 68,1% ≈ event 67,6%; trước
  76,9 vs 53,6). Ranh giới sim↔sản phẩm (dismiss là UI-only) khoá bằng 2 test theo chỉ thị
  Cường 2026-07-29. Visual **V-18** chờ Cường. **+ 2 defect P0 từ debate review remote `UPDATE-098` đã reproduce độc lập và FIX**: F-098-01 (gate Bellman bỏ bonus vượt mốc) và F-098-02 (resolver dùng policy ngoài thời hạn) — `tests/test_f098_defects.py`. F-098-03/04/05 → `D-F098-B`. Ba mục mới mở: `D-ĐA04-01` (material_revision
  rỗng không fail-loud), **`D-ĐA04-03` (ngân sách FIFO — kênh ÂM chiếm hết suất, rest_window
  chết đói ⚠ **chân "rest_window chết đói" đã bị chính agent BÁC BỎ** — xem `D-R08`; bằng chứng còn lại là `shift_plan` chiếm suất; cần plan riêng)**, `D-ĐA04-04` (chi phí log suppressed), `D-R08` (**đã fix**: 50% số nén là ma).
  **`D-ĐA04-03` MẠNH LÊN 2026-07-29 (UPDATE-100, artifact 38 n=100 per-seed):** tương tác ngân sách FIFO **+2.207đ CI[+1.077,+3.372] SIG**, còn **giá của nhịp khi KHÔNG có `shift_plan` = −259đ ns** (CI trùm 0) ⇒ nhịp tự nó không tốn tiền có ý nghĩa, **toàn bộ chi phí là chi phí FIFO**. ⚠ **Tôi phải RÚT LẠI câu *"mục giá trị cao nhất còn lại"* ngay trong cùng ngày:** giải thưởng +2.207đ **đã bị ĐA-07 lấy bằng một dòng YAML** (bỏ `shift_plan` khi nhịp bật = +2.259đ SIG), và ở **đúng cấu hình sản phẩm** (nhịp ON, `shift_plan` OFF) giá của nhịp là **−259đ ns** ⇒ ngân sách chú ý hiện tại không tốn khoản tiền nào đo được ⇒ trọng tài khéo hơn có **headroom ≈ 0đ**. ⇒ E1 → **`D-M3-07` DEFERRED-CÓ-ĐIỀU-KIỆN** (mở lại khi bật một kênh ÂM); spec thi công đầy đủ đã lưu ở `specs/simulation/e1-budget-arbitration-4-mechanisms.md`. **Lever thay thế đề xuất: `E9` — chọn lọc TRONG một kênh** (cả 4 cơ chế của E1 đều chia suất GIỮA các kênh; artifact 38 không nói gì về chọn lọc trong kênh).
  `D-ĐA07-recheck` **ĐÓNG 2026-07-29 bằng HAI phép đo n=100 độc lập** và **ủng hộ** ĐA-07: artifact 38 cho bỏ `shift_plan` ở trần = **+53đ ns**, artifact 39 (seed khác, ước lượng riêng) cho giá trị của nó = **−451đ ns** ⇒ kênh **trung tính khi đứng một mình**, **độc hại dưới FIFO**. Ô **−1.700đ** của lưới n=30 là **nhiễu**.
  **ĐA-06 đã CHỐT riêng 2026-07-27** — nghĩa vụ nhắc-duyệt hoàn tất, agent **không nhắc nữa**;
  vẫn xếp POLISH, và mang nhãn **DỄ THAY ĐỔI** ⇒ thi công theo ràng buộc ở **T-044**.
- **T-047 — HỢP ĐỒNG DỮ LIỆU PHẢN THỰC ("nếu có data thật")**, mở 2026-07-30 theo chỉ thị Cường: *"MOCK data, giả sử chúng ta có data thật — chia thành 1 task mới, cần research kĩ càng, bạn tự chốt schema hợp lý"* + *"sẽ không có data thật từ GSM hay được cung cấp gì thêm"*. ⇒ Deliverable **KHÔNG** phải yêu cầu dữ liệu gửi ai; là đặc tả phản thực gồm: hợp đồng dữ liệu (JSON Schema versioned) · **bản đồ MOCK↔THẬT** từng trường · 🔴 **kết luận nào của dự án KHÔNG sống nổi qua khoảng cách đó** (mục giá trị nhất) · cơ chế CODE chống tự lừa. Spec đích: `specs/real-data/data-contract-counterfactual.md` — ✅ **XONG 2026-07-30, 1.262 dòng** (§0–§9 + phụ lục). Trạng thái: **`WAITING-VERDICT`** — 4 mục cần Cường ở phụ lục. 🔴 **§4 phân loại 17 kết luận của dự án thành VỮNG / LUNG LAY / KHÔNG THỂ KIỂM**, và **con số chủ lực +6.016đ nằm ở LUNG LAY**: advisor nhận **λ CHÍNH XÁC** của generator trong khi tài xế chỉ nhận `λ×lognormal` ⇒ không phải "sai 2×" mà **sai về bản chất nguồn tin**; ngoài đời tín hiệu tốt nhất là mật độ cuốc **ĐÃ phục vụ**, thiên lệch về nơi đã có tài xế — đúng hướng làm **herding TỆ HƠN** ⇒ **phải dựng arm "advisor cũng nhiễu" TRƯỚC khi mang ra hội đồng**. Agent chính hạ cấp rủi ro §9.2 #1 (`commission`=payout) bằng **hai neo ĐỘC LẬP ngoài mock**: đọc ngược ngụ ý share **0,30** (ngoài dải có nguồn [0,75–0,91]) và payout **118k/ngày** (**2,7× DƯỚI** sàn ĐBTN 8h=320k, VnExpress 11/2023).
- **T-041 bước 1c (hậu quả của MỆT) → `HUỶ` 2026-07-30** (Cường: *"okey, chấp nhận câu trả lời"*; trước đó `DEFERRED` 2026-07-29 UPDATE-100)** — quyết định NGUYÊN TẮC, không mở lại bằng dữ liệu mới. Nợ docs đã trả trong `specs/advisor-objective-model-v2.md` (§1.2 C2 HUỶ · §1.2b MỚI · §5b HUỶ · §6 bước 2b/3 HUỶ); thay bằng **`C2′`** = chi phí cơ hội của THỜI ĐIỂM nghỉ. Năm quyết định + cổng tiền-đăng-ký: `tracking/QUYET-DINH-2026-07-30-nam-diem.md`.** — phán quyết ở `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` sau debate 10 agent + tự kiểm + đo lại: **KHÔNG mô hình hoá hậu quả của mệt.** (a) mọi cơ chế đều tạo `∂payout/∂F` — tỷ giá sức-khoẻ↔tiền, viết vào *world* thay vì *objective* chỉ xoá NHÃN; (b) 0 dữ liệu mệt/tai nạn, proxy duy nhất là nhiễu thuần theo construction; (c) **đo được: lan can sức khoẻ chặn 71,0% cơ hội của kênh nghỉ** ⇒ trần kênh ≤29,0% do chính ranh giới đạo đức ⇒ mô hình mệt chính xác đến đâu cũng không mở được 71% đó ra mà không phá nguyên tắc. `rest_window` nói **0/873 lần** hiện nay. **Chờ Cường chốt 5 mục giá trị** ở §6 của phán quyết (V-15). Thay vào đó làm `D-M3-01` — ✅ **DONE-CODE 2026-07-30 (UPDATE-102)**: `shift_extend` từ **1,000 → 0,475** (sự thật đo từ coin **0,473**), fingerprint per-actor **15/15 IDENTICAL**. Kèm 🔴 **`D-M3-10` cũng DONE**: cổng hợp lệ *"mọi arm báo adherence, lệch >0,02 ⇒ TREO"* **chưa từng được thi hành** (đường ống A/B tham chiếu `adherence` **0 lần**; artifact 35–39 **không có khoá nào**) — đó là **lý do trực tiếp** `D-M3-01` sống qua 39 artifact. Nay `PairResult` mang adherence **cả hai arm**, `run_ladder` ghi `verdict` TREO/OK, cổng **BẤT KHẢ** + 9 test gồm test **đòi cổng bắn** trên đúng trạng thái `D-M3-01`. ~~**Còn `L1-04`** (dời `_claim_effect` sau clamp) — ĐỔI HÀNH VI, UPDATE riêng, n≥100~~ ✅ **XONG 2026-07-30 (UPDATE-107)**: đo n=100 ghép cặp cho **Δ=0,00 [0,00,0,00] tuyệt đối trên cả 11 chỉ tiêu** — giả thuyết "28% quyết định mất hẳn" là do tôi đọc sai một con số đo (gap LOGGING đã đóng bởi `D-M3-01`, không phải gap QUYẾT ĐỊNH). Fix vẫn giữ (đúng semantic `R-01`, vô hại đo được), chỉ rút lại lý do ưu tiên nó.
- **T-041 — MÔ HÌNH HOÁ LẠI ADVISOR (spec objective v2 §6), ưu tiên cao nhất hiện tại:**
  1. `DONE 2026-07-27 (UPDATE-075)` đo trước sửa sau — Gini/HHI/khách + guardrail 4 tầng +
     bỏ ép `coverage="single"` + baseline 30 seed `coverage: all`.
  1b. `DONE 2026-07-27 (UPDATE-078)` **BUG-S2-PARAMS**: bridge không truyền `params` cho `shift_dp`
     ⇒ DP tính bucket 30′ trong khi sim tiến 60′ (pin tưởng bền gấp đôi, nghỉ bắt buộc giảm 4×).
     Hồ sơ `10-*`. **Tác động lên payout CHƯA đo được**: so ghép cặp 30 seed cho hiệu số −7.650đ
     CI [−24.390, +9.522] — **CI trùm 0**, fix giúp ở 12/30 seed. Cần **n≈105** (SD ~40k/seed).
     Ablation: `bucket_min` là tham số DUY NHẤT có tác dụng; `p_accept`/`avg_dist_km`/gate thưởng
     **inert hoàn toàn** (chỉ scale `online_pay`, argmax không đổi ⇒ thêm bằng chứng cho model gap).
  1b'. `TODO` chạy lại so ghép cặp ở **n≈105 seed** để kết luận dấu của fix (hoặc dùng thiết kế
     giảm phương sai). Hằng `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100` đã ghi vào `parallel.py`.
  1c. ~~thêm "giá trị nghỉ"~~ **HUỶ HƯỚNG 2026-07-27 theo chỉ thị Cường**: *"rất khó mô hình hoá
     giá trị nghỉ tường minh… trừ khi mô hình hoá được chính xác thì không nên tạo biến"*. Thay
     bằng **T-045** (root cause thật, đo được). Sự thật code vẫn giữ để tham chiếu: `fatigue` chỉ
     khiến tài xế tự nghỉ, không ảnh hưởng năng suất (hồ sơ `11-*` §1).
  2. `TODO` C1 chi phí vận hành/km + C5 chi phí SOC phi tuyến → đo lại chỉ tiêu kép.
  3. ~~C2 giá trị nghỉ~~ **HUỶ** (xem 1c). C3 rủi ro (CVaR/phạt phương sai) — `TODO`, nhưng theo
     hồ sơ `11-*` §5 thì mọi số hạng ĐỘ LỚN đều inert khi biến vị trí chưa vào bài toán ⇒ **làm
     T-045a TRƯỚC**, nếu không lại đo một thay đổi không có tác dụng.
  4. `TODO` `MarketStateView` + C4 chi phí cơ hội vị trí (ĐA-09).
  5. `DONE-CODE/RESEARCH 2026-07-28 (UPDATE-083..088)` capacity ledger + S4 + **ĐA-09 §2.2 đủ
     ba câu trả lời bằng số** (hồ sơ `research/simulation/multi-agent-equilibrium.md`): cân bằng
     tồn tại & ≈ λ_config (γ=1 hội tụ 1 vòng) · heatmap-residual (γ=0) KHÔNG hội tụ, tệ vĩnh
     viễn — cảnh báo production · PoA: adherence thật lấy 51–73% mức tập trung · phủ tăng đơn
     điệu không tự-triệt-tiêu, có bẫy free-rider 25–50%. **Đề xuất cấu hình bật (UPDATE-087)
     chờ Cường.**
  - **Ràng buộc Cường**: `accept_lift` giữ TẮT; ~~`shift_plan` giữ BẬT + cảnh báo đỏ trong khu Mô
    phỏng, **đo lại trước bản cuối — không hiệu quả thì TẮT để advisor im lặng**.~~
    **⚠ SAI — đính chính 2026-07-29: `shift_plan` đã TẮT** (`channels.shift_plan: false` từ
    2026-07-28, theo điều-khoản-bản-cuối ĐA-07 — Cường DUYỆT, UPDATE-087/089). Đo lại cho thấy
    không hiệu quả nên đã tắt để advisor im lặng đúng như điều kiện đặt ra ở trên.
- **BUG-EVAL-ARGMAX — `DONE-CODE 2026-07-28 (UPDATE-086, Q-11 duyệt)`.** Estimator cohort
  không bias trong `parallel._cohort_metrics` + placebo test + nhãn BIASED cho argmax + banner
  CORRECTED trên UPDATE-075/078/081/084 + artifact `24-*`. **Kết quả đảo chiều**: B0 hoà (−466đ
  ns) — chuỗi "advisor làm nghèo" là artifact; kênh vị trí **+3,5–5,0k/người SIG** nhưng kẹt
  **veto 9 đổi-pin** (Q-12 chờ Cường). Việc gốc (giữ làm sử): `pick_target` argmax-A bias âm có hệ thống (sign-flip đã chứng minh: −19,7k vs
  +27,4k vs +3,6k không-chọn-lọc). Việc: (1) `parallel` thêm estimator mean-per-archetype trên
  mọi tài xế được phủ; (2) tiêu chí 1 ĐA-08 đọc estimator mới; (3) argmax giữ làm view chẩn đoán
  CÓ NHÃN; (4) đo lại 30 seed toàn bộ cấu hình (artifact 24-*); (5) đính chính bảng số các
  UPDATE-075/078/081/084 bằng banner CORRECTED. H4 (swaps +4,7 sau reorder) đo lại cùng lượt.
- **T-046 — MẪU LỖI LẶP LẠI "sửa một tầng, tầng khác không biết"** (hồ sơ `13-*` Phần 1): xuất
  hiện **5 lần trong một phiên**. 4 quy tắc rút ra (test ở tầng consumer; test caller TRUYỀN tham
  số mới; chỉnh tham số cấu trúc phải in metric coupled; hai-tên-một-sự-thật là nợ). **Ứng viên
  nghi tiếp theo, chưa kiểm**: `bonus_at` vs `day_bonus` · `next_tier_gap`/`trip_points` chép đôi ·
  `DEFAULT_PARAMS` của 8 solver còn lại · viết `test_l3_views_derivable_from_l1r`.
  - **Quy tắc thứ 5, thêm 2026-07-28 — "test có mà không BẮT".** Khi kiểm lại MUT10 theo yêu cầu
    Cường: trong 2 regression test viết ra để canh mutation, **chỉ 1 test giết được mutant**;
    `test_soc_budget_binds_at_60min_buckets` khẳng định `swaps60 >= swaps30` nên **vẫn xanh khi
    mutation quay lại**. ⇒ Test viết cho một bug cụ thể phải được **chứng minh là ĐỎ khi bug quay
    lại** (re-apply → đỏ → restore → xanh), không chỉ xanh sau khi sửa. Bất đẳng thức `>=`/`<=`
    hầu như luôn là lan can yếu. **Chưa kiểm**: các regression test khác trong repo cũng có thể
    thuộc loại này.
- **T-045 — LỖ HỔNG ĐO ĐƯỢC (hồ sơ `12-*` + `13-*`), thay cho hướng "giá trị nghỉ":**
  a. **`DONE-CODE` (⚠ 2026-07-29, nợ còn: kênh km-rỗng veto/C4 — xem Q-10/Q-12) ⭐ ĐÒN BẨY LỚN
     NHẤT — advisor tối ưu SAI BIẾN.** 62% lượt, đơn chết vì **không ai
     trong bán kính 2,1 km**; tài xế rỗi median 12 người/23 km²; đơn hết hạn **không xấu về kinh
     tế** (gross 24.151đ vs 24.734đ). Biến có đòn bẩy là **VỊ TRÍ**, mà advisor không có kênh nào
     khuyên vị trí và không có state cung. ⇒ nối **ĐA-09 `MarketStateView`** + **hồi sinh S4
     `capacity_alloc`** (đang chết). Nguồn dữ liệu đã có: `public_driver_hex_tracking` (1,37M dòng).
     **Đây mới là lý do các số hạng ĐỘ LỚN đều inert** (hồ sơ `11-*` §5).
     - **b1 `DONE 2026-07-28`** — `gsm_core/features/market_state.py` + 9 test. Nghiên cứu +
       thiết kế ở hồ sơ `19-*`: **KHÔNG** dựng bản đồ cầu cạnh tranh với GSM (hãng đã có heatmap
       + "Nhiệm Vụ Tiếp Theo", official 15/04/2026); ta cấp hai thứ hãng **không** cấp — **cung
       ĐANG TỚI** (chống dồn cục do chính lời khuyên tạo ra) và **trần theo ô**. Thiếu dữ liệu ⇒
       nhãn `absent` ⇒ **bỏ hẳn** lời khuyên vị trí, không im lặng giả định.
     - **b2 `DONE 2026-07-28`** producer trong sim — `Actor.enroute_cell` + `gsm_sim/market_state.py`,
       **11 test**. `ActorState.ENROUTE` dùng chung cho 3 việc và không ai ghi ĐÍCH ĐẾN ⇒ phải thêm
       trường riêng. Đường **đón khách** cố ý miễn trừ (`ENROUTE_EXEMPT`, có nhãn + test quét source
       để ai thêm đường di chuyển mới mà quên sẽ bị ĐỎ). Mutation-proof cả chiều gán (W1) lẫn chiều
       **xoá khi tới nơi** (W2 — quên xoá còn tệ hơn quên gán: actor bị đếm "đang tới" vĩnh viễn).
     - **b0 `DONE 2026-07-28`** (phát sinh từ câu hỏi *"có time mismatch ở đâu không"*): nhãn bucket
       mất NGÀY (`% 24`) ⇒ `sorted()` của `shift_dp` đảo thứ tự — **tiềm ẩn**, che bởi `demand_field`
       không có giờ 0; **bucket MA** sau 24:00 thổi phồng `B` ⇒ `_required_rest` — **thật, 48
       lần/seed**; `shift_extend` kéo ca quá lúc thế giới dừng — **thật, 9 lần/seed**. 6 test.
       **Đính chính**: nghi ngờ UPDATE-047 bị nhiễm là SAI (đo 0/1197).
     - **b0-D `DONE 2026-07-28 (UPDATE-083)`** `_sample_drop` cân theo cầu — pha tuyến tính
       `m = 1 + α·(w/w̄ − 1)`, **α = 0.4** (quét 5 mức × 3 seed, hồ sơ `20-*`): corr −0,222 →
       **+0,418**, trả ngoài lõi 80,9% → 65,3%, deadhead 636 → 539 km, med dist chỉ −2,5%.
       α=0 tái lập trace cũ **từng bit** (test canh). ⚠ đổi nền lần 4 ⇒ mọi baseline cũ lệch.
     - **b3 `DONE 2026-07-28 (UPDATE-083)`** `_standby_planner` batch tick (Hungarian, đúng chốt
       của Cường) + cờ `positioning_overrides` (off/wait_only/wait_and_relocate) + adherence rút
       MỘT lần lúc gán (chống D-SIM-14). 8 test, mutation S1 (bỏ trần) → 2 đỏ, S3 (ghi đè quá
       tay) → 1 đỏ. Suite **617 passed / 5 skipped**.
     - **b3 `DONE-CODE` (⚠ 2026-07-29, thay TODO)** hồi sinh S4 `capacity_alloc` + kênh
       `standby_zone` vào bridge đã xong cùng lúc với b2 như yêu cầu ở trên (UPDATE-083): heatmap
       nay có capacity ledger (không còn là **cỗ máy tạo dồn cục**, hồ sơ `19-*` §5). Câu hỏi
       fairness của Cường — nay **đo có, cưỡng chế cũng có**.
     - **b4 `DONE 2026-07-28 (UPDATE-084)`** — 30 seed × 4 thế giới (A/B0/B1/B2), artifact `21-*`.
       **Kênh vị trí là kênh ĐẦU TIÊN cứu HỆ THỐNG SIG**: served +1,03đp · đơn chết −13,4/ngày ·
       tổng payout đội **+212k/ngày** · **HHI GIẢM** (capacity ledger chống dồn cục thành công).
       NHƯNG tài xế đích −40k (B0 riêng −33k ⇒ thủ phạm chính vẫn là REST/shift_plan trên nền
       mới) và **veto km rỗng hỏng** (+0,7đp SIG — chính là cơ chế reposition, được trả công ở
       tầng đội). ~~**Phán quyết: giữ `off`** theo tiêu chí đã chốt; câu hỏi veto → **Q-10** chờ
       Cường chọn (a)/(b)/(c).~~ **⚠ Thay bằng verdict Cường 2026-07-28: bật `positioning_overrides:
       wait_only` MẶC ĐỊNH** (`configs/pilot_dongda.yaml`, UPDATE-089) — không còn giữ `off`; câu
       hỏi veto km-rỗng vẫn treo (Q-10/Q-12). ⚠ B1 vs B2 chưa xếp hạng được (cần ≥100 seed).
  b'. **`DONE-CODE 2026-07-28 (Cycle R, UPDATE-085)` — GỐC REST của shift_plan (Q-10c).**
     Reproduce cả 3 giả thuyết: DP mù nghỉ-đã-nghỉ ⇒ tái áp mỗi consult (tổng nghỉ +16–27%,
     11–14 lần/seed tái-khuyên ngay sau nghỉ); REST thắng SWAP khi hoà (fixture SOC 22% cho
     `ONLINE,REST,REST,SWAP`; 7–12 `go_swap→rest`/seed). Fix: `spi.rest_taken_min` +
     `_required_rest` **tín dụng ĐƠN ĐIỆU AN TOÀN** (R_mới ≤ R_cũ luôn — bản backfill đầu tiên
     BỊ SỐ BÁC BỎ: advisory nổ 55–66→145–178, ghi lại trong docstring) + SWAP xét trước REST.
     Sau fix: advisory 13–21, tái-khuyên 2–4, `go_swap→rest` **= 0**. 7 test, MR1-3 mutation-proof.
  b. **`DONE-CODE một nửa 2026-07-28 (Cycle P)` chi phí pin/năng lượng.** Sổ riêng
     `actor.cost_vnd` (km qua chốt chặn `consume_soc` + phí đổi pin), **mặc định 0 = đúng chính
     sách hiện hành** (miễn phí official tới 31/03/2029); reconcile test + test cost-không-rò-
     vào-payout. Còn lại của mục cũ: giá trị THẬT theo cohort khi hết ưu đãi → `grep swap_cost|charge_cost|
     energy_cost` = rỗng; `payout_vnd` chỉ `+=`, không trừ gì. Hệ quả đo được: nhóm **SWAP kiếm
     hơn 26%** (262.502đ vs 207.962đ) với **cùng số cuốc, cùng giờ online** — vì swap nhanh VÀ
     miễn phí. Thêm `swap_fee_vnd`/`swap_free_per_day`/`charge_cost_vnd_per_trip` **mặc định 0**,
     trừ vào ledger riêng. ⚠ Số 9.000đ/lần là **press/medium** (vinfastauto.com trả 403) ⇒ **phải
     hỏi GSM (`D-POL-05`)** trước khi đặt mặc định khác 0. Lưu ý: nhiều chương trình **miễn phí**
     đổi pin (RTO 5 lần/ngày tới 06/2028; "Tặng Xe" không giới hạn tới 31/3/2029) ⇒ chi phí pin là
     biến **theo cohort/hợp đồng**, phải versioned như policy.
  c0. `UNRESOLVED / BLOCKED-Q-07` **⚠ ĐÍNH CHÍNH 2026-07-29 — dòng cũ ghi "DONE 6→12" là SAI
     SỰ THẬT**: nâng k_max 6→12 **ĐÃ HOÀN TÁC** vì phá dung sai `accept_base` của baseline;
     config hiện hành vẫn `candidate_ring_k_max: 6` (comment trong `configs/pilot_dongda.yaml`
     ghi rõ *"ĐÃ TÌM RA, CHƯA SỬA ĐƯỢC"*; test pin `== 6`; UPDATE-079 ghi hoàn tác). Chờ
     **Q-07** — Cường đã chọn hướng (c): nghiên cứu dispatch thật trước khi đụng shortlist.
     Số đo 3-seed của lần thử (served 0,750→0,789, hết hạn −18%, k=16/20 bão hoà, cấm nâng
     `eta_max`) giữ làm evidence cho Q-07. Baseline 30 seed của UPDATE-075/078 **VẪN HIỆU LỰC**
     (đo ở k=6 — đúng config đang chạy).
  c. **`TODO` BUG dispatcher (còn lại)**: `dispatcher.py:77` bỏ đơn khi người **gần nhất theo haversine** fail
     ETA, viện lý do *"ETA đơn điệu theo distance"* — **tiền đề SAI** vì `factor` theo cặp ô biến
     thiên p10 1,24 → p90 1,94 (số của chính repo). Đo: **293/3.520 lượt bỏ OAN (8,3%)**, tiết kiệm
     được median 3,1′. Sửa: xếp hạng theo **ETA thật**, thử tiếp ứng viên kế (có trần). 4 test bắt
     buộc ở hồ sơ `13-*` §4.3. **Không** kỳ vọng giải quyết chờ-hàng-giờ (chỉ 8,3%).
  d. **`TODO` ⛔ GỐC của chờ-hàng-giờ — ĐÃ ĐO XONG BIÊN GIỚI (hồ sơ `14-*`), CHỜ Q-05 xác nhận
     thứ tự mới.** Ba sự thật đã chứng minh: **(i)** sai lệch thiết kế — `orders_per_day = 1200`
     gắn với **50 actors** nhưng `actors.n` đã lên **90** ⇒ đơn/actor 24,0 → **13,3**, tài xế
     **rỗi 32%**; **(ii)** BUG `candidate_ring_k_max = 6` phủ **~2,22 km** (số theo comment
     config; hồ sơ `14-*` từng ghi 1,81 km — số cũ, mâu thuẫn đã ghi nhận) trong khi
     `eta_max = 11′` cho phép xa hơn hẳn ⇒ shortlist loại chính người thoả ETA; nới k=12 làm
     **cả hai metric cùng lên** (served 0,750→0,789, hết hạn −18%) nhưng **ĐÃ HOÀN TÁC —
     xem c0, chờ Q-07** — ⚠ **cấm nâng `eta_max`** (realism);
     **(iii)** quét lưới 16 tổ hợp × 3 seed: **0/16 PASS** cả bốn tiêu chí — `served` và
     `trips/tx` **đối nghịch**, không có điểm giao. Trần năng lực **17,7 cuốc/tx khi bão hoà**
     (biên dưới research 18–22) ⇒ **vật lý ĐÚNG**; mất mát nằm ở **`relocate` 14% + phân bố đơn
     không đều** ⇒ đòn bẩy thật là **T-045a**, không phải mở rộng zone.
     **Bắt buộc**: chọn một điểm trên biên giới **có chủ ý** và **ghi bảng biên giới vào config**
     để người sau không tưởng đã tối ưu.
  e. **`TODO` `soc_pct` — BA nguồn cho MỘT biến, và 13 bảng thật KHÔNG CÓ cột pin** (hồ sơ `13-*`
     §3.2): sim = telemetry thật · l1r = `None` ⇒ `shift_dp` **im lặng giả định pin ĐẦY** (nguy
     hiểm: khuyên tài xế 15% pin như 100%, không hạ confidence) · UI = **sha256 → 30..95**, và
     **số bịa đó HIỂN THỊ cho tài xế** (`app.js:99` `⚡{soc}%`, tô đỏ <25%) mà **không có nhãn
     trên UI** — vi phạm `CLAUDE.md §5` "mock phải gắn nhãn mock". **(c-UI) đang chạy hôm nay;
     (l1r) là blocker tương lai vì S2 chưa nối vào UI.** Sửa UI trước (rẻ, đúng ranh giới).
- **T-042 — C2 "một nguồn luật UI↔sim"** (ĐA-05 đã duyệt; hồ sơ `08-parity-sim-vs-ui.md` §5):
  0. `DONE 2026-07-27 (UPDATE-076)` `already_maxed` che `feasible` — 3 consumer + solver constraints.
  0b. `DONE 2026-07-27 (UPDATE-076)` **S5 `weekly_khoan`** cùng mẫu lỗi: `_khoan_sentence` không
     đọc `feasible` ⇒ khoán không thể đạt vẫn nói *"còn thiếu Xđ… có thể bị truy thu Yđ"*. Đã sửa
     + 2 test. Quét mẫu lỗi CẠN (UPDATE-076 §1d): chỉ S1/S5 có defect thật.
  1. `DONE 2026-07-27 (UPDATE-075)` cước UI = `PolicyBundle.gross_fare` (bỏ hằng `24000`).
  2. `DONE 2026-07-27 (UPDATE-076)` `seed` advice đọc từ manifest (hết `seed: 0` giả).
  3a. `DONE 2026-07-27 (UPDATE-077)` **UI hết rò tương lai** — `gsm_core/rates.shrunk_rate` +
     `_rate_asof`/`_pooled_prior` (7 ngày TRƯỚC, `p0 = 0,8971`, `m = 20`, **bỏ fallback 1.0**).
     Tác động: **16/60 tài xế đổi phía ngưỡng 0,85**. Sim KHÔNG đổi ⇒ baseline 30 seed còn hiệu lực.
  3b. `TODO` **nối `shrunk_rate` vào SIM** để hết hai-estimator (yêu cầu "một luật" của Cường mới
     xong một nửa) + diệt gốc 0/0→1.0 thay vì vá bằng `acc_est`. ⚠ **SẼ lệch baseline ⇒ đo lại 30 seed.**
  3c. `DONE 2026-07-27 (UPDATE-077)` quét độ nhạy `m`: kết luận **robust** với `m ∈ [5,50]` (đổi
     1,1–4,1%), vì `m ≪ n` (20 vs 81). Chỉ sập ở `m=200` (đổi 20%). Ràng buộc giữ: `m ≪ n`.
  4. `TODO` payout project từ **ledger 4 nguồn** (UI đang tự cộng `commission + mission`).
  5. `TODO` hợp nhất `bonus_at` (không gate) vs `day_bonus` (có gate) — cùng khái niệm, khác luật.
  6. `TODO` `cards.js:120-122` tự ghép chuỗi tiền **ngoài verifier** — lỗ thủng của guardrail R5-A.
  7. `TODO` `SourceEnvelope` đầy đủ (`dataset_id, run_id, as_of, policy_version, data_mode`).
  8. `TODO` dọn: bỏ trường `feasible` **thừa** ở `idle_reduction` (luôn 1:1 với `notable`) và
     `mission_knapsack` (`= bool(chosen)`). Không phải bug hôm nay, nhưng **hai tên cho một sự
     thật** chính là thứ đẻ ra defect §1b/§1c. Quét mẫu lỗi đã CẠN (UPDATE-076 §1d) — chỉ S1/S5
     có defect thật, cả hai đã sửa; đừng audit lại từ đầu.
- **T-043 — mốc thưởng cao nhất gần như KHÔNG với tới được trong thế giới mock** (câu hỏi
  calibration, không phải bug generator):
  - Số đo: 86/12.805 driver-day (**0,67%**) chạm mốc 200 điểm; **0** trong số đó có tỷ lệ dưới
    ngưỡng. Ban đầu tôi nghi generator ràng buộc ngầm — **ĐIỀU TRA CHO THẤY KHÔNG PHẢI**.
  - Cơ chế thật: `corr(n_trips, offers) = 0,967` — số cuốc gần như hoàn toàn do **số đơn được
    chào** quyết định. Cần **~29 cuốc** để đạt 200 điểm, trong khi offers/ngày có median 15,
    p95 27, **max 37**. Ai nhận dưới 85% thì cần ≥35 offers — nằm ở đúng đuôi cực hạn. Đó là
    **trần số học**, không phải ràng buộc nhân tạo.
  - Câu hỏi thật cần Cường/GSM trả lời: **mốc 200 điểm có hợp lý không** khi chỉ 0,67% ngày-công
    chạm tới? Nếu số policy thật (D-POL-05) khác thì kết luận này đổi.
  - **Điều kiện: làm rõ trước khi dùng mock nghiệm thu bất kỳ kênh advice nào liên quan mốc thưởng.**
- **T-044 — ĐA-06 AdviceEnvelopeV2 (CHỐT 2026-07-27, xếp POLISH → làm sau T-041 b2 + T-042).
  ⚠ 2026-07-29: hai điều kiện chặn (B-02 registry đa phiên bản · ĐA-05 projection chung) ĐÃ
  XONG ⇒ về mặt phụ thuộc là `READY`; vẫn giữ thứ tự POLISH theo chốt của Cường.**
  Cường chốt kèm cảnh báo: *"có thể sửa nhiều trong tương lai vì còn đang phân vân"*.
  ⇒ **"Còn phân vân" là RÀNG BUỘC THI CÔNG, không phải ghi chú suông.** Thi công phải giả định
  hình dạng envelope **sẽ đổi**:
  1. **Một chỗ duy nhất biết hình dạng card** — mọi consumer (web cards, Flutter, C6, sim viewer)
     đọc qua **một adapter**; cấm rải `item["title"]`/`item["numbers"][0]` khắp nơi. Bài học đắt
     nhất phiên này: cùng một sự thật nằm ở nhiều chỗ ⇒ sửa một tầng, ba consumer không biết
     (UPDATE-076 §1b/§1c).
  2. **Schema versioned + upcaster** ngay từ v2.0.0 — không dùng `schema_version.const` một giá
     trị (đó chính là **B-02/ARCH-VERSION** đang mở; **phải gỡ B-02 TRƯỚC**, nếu không mỗi lần
     Cường đổi ý là một lần migration đau).
  3. **Adapter v1 giữ sống** để Flutter v0 của Khánh không gãy khi v2 đổi.
  4. **Không** đưa quyết định sản phẩm còn phân vân (số card/ca, thứ tự, mức chi tiết trace) vào
     code cứng — để config, đổi được không cần deploy.
  5. Verify per-card **fail-closed** (đã có tiền lệ R5-A ở `adapters/advisor.advice()`).
  - **Phụ thuộc**: B-02 (registry đa phiên bản) · ĐA-05 (một projection chung) nên xong trước.
- ~~**BLOCKER-R5-MUT10**~~ **ĐÓNG 2026-07-28 — đã commit `6ccd8fc`** (UPDATE-074). Kiểm lại theo
  yêu cầu Cường: re-apply mutation ⇒ `test_soc_cost_scales_with_bucket_min` **ĐỎ** (`1 == 2`),
  restore ⇒ **xanh**. **Đính chính:** mutation **chưa từng lên remote** — `7739b3c` là commit
  local chưa push, `origin/main` luôn sạch. ⚠ `test_soc_budget_binds_at_60min_buckets` dùng `>=`
  nên **KHÔNG giết được mutant** (vẫn xanh khi có mutation) — lan can thật chỉ là test unit; ghi
  vào **T-046** như một ca "test có mà không bắt".
- ~~**BLOCKER-ARCH-VERSION**~~ **GỠ 2026-07-29 (Cycle V, UPDATE-090).** Registry đa phiên bản
  (`{entity}@{ver}.schema.json`, validate route theo record, fail-loud version lạ/null) +
  upcaster từng-bậc có chặn-treo + backward-compat TEST bằng record persist thật + bump thật
  đầu tiên `shift_plan_input` 1.1.0 + vá lỗ `market_state_view` không được validate. Review
  đối kháng 28-agent: 7 finding confirmed-by-reproduce, đã sửa hết (guard file rác/const lệch
  tên/manifest hardcode/upcast treo). **ĐA-05 và T-044 hết bị chặn.**
- **ĐA-05 lifecycle store — `DONE-CODE` 2026-07-29 (Cycle W, UPDATE-091), chờ verdict Cường.**
  Event log append-only (`gsm_core/lifecycle/event_log.py`, idempotent theo `event_id`, validate
  qua registry + parse lịch thật trước khi ghi, không WAL, có `close()`) + **projections MỘT
  LUẬT** dùng chung UI/sim (`decision_state`/`adherence_view` — **HAI TÊN** theo verdict Cường:
  `decision_adherence` + `event_adherence`, cấm khoá `adherence` trần) + `Event.run_id`
  deterministic (kèm config digest) + `decision_id` cho 7 điểm emit advice + UI POST/GET action
  qua store canonical + EpisodeStore thành legacy adapter. **4 lượt review đối kháng trả 36
  finding có reproduce, đã sửa hết** (hồ sơ `research/audit/2026-07-29-cycle-w-review/`);
  nặng nhất: adherence_view từng báo 0%/2%/100% vs sự thật 53,6%/52,2%/48,8%, bản sửa đầu lại
  double-count 54,2% — nay pin theo ground truth. **Bằng chứng không đổi hành vi**: fingerprint
  IDENTICAL vs TRƯỚC-toàn-bộ-Cycle-W (run_once 5 seed × 2 arm + multiday 3 ngày, chạy lại SAU
  mọi fix). Đóng kèm: D-A3-04, FAILCLOSED-3, MEMSTATE-2/3/4/6, LAYEROUT-16; ~~nợ positioning
  thiếu decided~~ **ĐÃ ĐÓNG trong cycle** (F-1: `standby_alloc` mang `assigned_ids`/
  `decision_ids`, adapter sinh `decided` per-actor — mẫu số 86, không còn 36).
- **BUG-MOCKGEN-CLI — `TODO` (PRE-EXISTING, reviewer reproduce 2026-07-29):** entrypoint
  `python -m gsm_core.mockgen.generate` crash `AttributeError: 'str' object has no attribute
  'items'` tại `generate.py:50` TRƯỚC khi tới verify_round1 — đường CLI không được test nào
  phủ (test gọi thẳng hàm). Không do Cycle V (diff không đụng file này trước điểm crash).
  Cần: reproduce → root cause (nghi `adapter_sim._tables_from_run` trả str ở một nhánh) →
  test CLI smoke → fix.

Các section cũ bên dưới là timeline/backlog tích lũy; khi mâu thuẫn, dùng checkpoint này +
`DIRECTIVES` §13 + dossier current-state.

## Thứ tự thực thi (theo độ quan trọng + phụ thuộc tuyến tính)

**Legacy Track CORE sequence (foundation đã code-complete; giữ để tra dependency; spec `core-data-schema-and-advisor-architecture.md`):**

1. **T-038 C0**: chốt data schema L0–L3 platform-centric (`schemas/` + validators + changelog).
2. **T-038 C1**: mock data generator + verify 4 vòng (schema/statistical ≥30 seeds/consistency/adversarial — spec §8.1).
3. **C2a** ✅ metric table (UPDATE-025). **C2b** ✅ solver S1 BonusFeasibility + SolverReport DONE 2026-07-23 (`gsm_core/{policy,features/bonus_gap,solvers/bonus_feasibility}`, UPDATE-026; 12 test, integration mock 7/12 feasible).
4. **C3** ✅ S2 ShiftDP (UPDATE-027). **C4** ✅ S3 F3Patterns + L2i (UPDATE-028). **C5** ✅ S4 CapacityAlloc DONE 2026-07-23 (`gsm_core/solvers/capacity_alloc.py`, UPDATE-029; scipy assignment chống herding, 5 safety_flags F2-04, 12 test, over-subscribe 0 vi phạm capacity). **→ 4/4 SOLVER XONG.**
5. **C6** ✅ DONE 2026-07-24 (UPDATE-030): agent pipeline `src/gsm_core/advisor/` (Router zero-ML → Composer placeholder-first LLM#1 → Verifier 3 tầng CODE-veto) + context pack (1 renderer) + episode store (exact-key cache, kiêm DecisionRecord) + observability per-layer (2 HARD invariant =1.0). F0 corpus-based track-guardrail. Template fallback (LLM-off) bắt buộc. 37 test (14+18+5), full suite 162. **3 bug thật fix có regression** (BUG-C6-01 normalize đ/Đ ở cả 3 module; BUG-C6-02 promise pattern báo nhầm tên chính sách "Đảm Bảo Thu Nhập"; BUG-C6-03 verifier soi text trích dẫn official). T-026 phase 2 instrument xong. **Còn: live LLM smoke thật (D-C6-03), visual = sample text.**
6. **Research refresh đợt 3** ✅ DONE 2026-07-24 (UPDATE-031): web research vòng mới phát hiện **Vận Doanh 23/02/2026 BỎ phạt ≤70% + khoán tuần + truy thu 20-40%** (research policy đợt 1/2 lỗi thời). Đồng bộ docs: `research/policy/policy-refresh-2026-07-24.md` + banner ở 00_SUMMARY/bonus-programs/pain-points/income-structure + ghi chú PERSONAS/USER_STORIES/spec §1.7. Flag **D-POL-01..05** (model/schema/mock/corpus/image-locked gaps). **T-004 corpus (Khánh) thiếu policy này → D-POL-04.**
7. **Downstream policy-refresh (reconciled 2026-07-27):** `D-POL-01/02` **DONE-CODE** qua UPDATE-032/038/040 (S5, additive schema, pipeline); `D-POL-03` **PARTIAL** vì mock shape đã re-ground nhưng exact values chưa có; `D-POL-04` vẫn chờ Khánh/Q-03; `D-POL-05` tiếp tục chặn active GSM quota/clawback/service-point values. Không gọi proxy/model shape là policy thật.
8. **Real-data integration** (Cường cấp schema thật gsm-data-prod 2026-07-24) — **blueprint DONE** (UPDATE-033): catalog `docs/data-catalog/` + 7 part-plan `specs/real-data/`. Chốt: re-ground về 13 bảng thật; chưa BQ access (tool=interface+PII); mở rộng UC5-UC8. **Roadmap 6 phase (mỗi phase cycle riêng có plan+test):**
   - **PI-1 Schema** ✅ DONE 2026-07-24 (UPDATE-034): 13 `l1r/*` + registry + 30 test; 5 bảng thiếu cột ENGINEER (nhãn TBC).
   - **PI-2 Mock regen** ✅ DONE 2026-07-24 (UPDATE-034): `mockgen/realdata.py` sim→aggregate → 13 bảng; R1/R3/R4 verify (9 test) + **R2 statistical 30 seeds/1500 driver-day** (`ROUND-2`, 6/6 in-range). Smoke 14 ngày×50 driver OK.
   - **PI-2b Data review + enlargement (DONE-CODE — UPDATE-035/036; kết luận ở dòng cuối mục này)**:
     - **Overall review**: audit từng bảng/cột/phân phối vs catalog+schema+UC coverage; soi caveat R2; kiểm cột ENGINEER; FK/consistency tập lớn.
     - **REALISM + RANDOMNESS (ưu tiên)**: sửa **acceptance median 1.00** (sim thiếu decline) → tỷ lệ nhận theo archetype target (0.74-0.97) + noise per-day, back-out decline; thêm variance/randomness mọi metric; cộng **lớp thưởng tuần** vào payout (nối S5); reposition/penalty/fraud/idle đa dạng hơn.
     - **PROFILE UNIVERSE phủ MỌI loại GSM** (car / bike / premium / platform / rto / employee, archetype PT/FT/top/newbie/veteran, tenure spread): roster LỚN đa dạng; **sim CHỈ sample một subset (bike)** — car/premium/khác sinh KPI **rule-based** grounded `economics/income-structure` (car: lương+commission; premium: fare cao). Quy mô ngày →90+.
     - **DEFER (Cường)**: enlargement zone/station/market (ngoài Đống Đa) — future update.
     - Sau enlarge: chạy lại 4 vòng verify (R1/R2/R3/R4) tập lớn; cập nhật ROUND report. **Gate cho PI-4.**
     - ✅ **DONE 2026-07-24** (UPDATE-035 + **UPDATE-036 audit**): thời điểm đó profile universe 110; manifest hiện tại sau các vòng SIM-XANH/D-SIM-13 là **150** (xem current-state dossier). Acceptance 1.00→0.88, CSV export. **Audit tìm & fix 5 flaw**: R2 trộn population (verdict sai), impossible-state 203 driver-day (cuốc khi online=0), tràn nửa đêm, field degenerate (core_order/stoppoints), **crash parquet phụ thuộc seed**. Suite 208. **Đính chính:** bike payout mock ~221k ở vòng đó (không phải 273k đã báo — số đó lẫn car); không gọi là payout thật GSM.
   - **PI-3 DataSource tool**: MockSource+BQ skeleton+PII read-only (P4). MockSource/local là scope publish; live BQ chủ ý DEFERRED tới khi ghép data GSM thật, không phải task cần unblock trong cycle hiện tại.
   - **PI-4a Adapter L1R→L3** ✅ DONE 2026-07-24 (UPDATE-037) · 🔴 **6 RÒ RỈ TƯƠNG LAI đã fix
     2026-08-01 (UPDATE-115, `D-M3-11`)** — deriver lọc *chỉ theo NGÀY*, không so `t_now`:
     `idle_segments` (view hỏi 23:00 thấy dwell 23:03), `demand_by_hour`, `active_reposition`,
     `bonus_gap.historical_points_per_hour` (gộp cả ngày SAU hôm nay), `shift_plan.points_now`
     (=35 lúc 8h sáng), `shift_plan.demand_forecast`. 13 test + mutation 6/6. `from_l1r` chưa
     được import ngoài tests ⇒ không số công bố nào bị ảnh hưởng. Cổng thường trực = `D-M3-12`: `features/from_l1r.py` — S1/S2/S3 view đọc field ĐO ĐƯỢC (acceptance/fulfillment/online/payout) thay vì recompute; `points_now` vẫn tính từ policy; chain S1→SolverReport traceability=1.0; 12 test, suite 221. **Fix self-review**: không bịa acceptance=1.0 khi thiếu dòng đo → carry-forward + nhãn ESTIMATED. **S4 KHÔNG remap** (bảng thật thiếu station capacity). **(d) CHỐT: khoán = GROSS** (doanh số), nhãn ASSUMPTION + `money_basis` param.
   - **PI-4b** ✅ DONE 2026-07-24 (UPDATE-038): **S5 WeeklyKhoanFeasibility** (gap khoán + rủi ro truy thu, money_basis=gross; quota=None → KHÔNG bịa số) + **S6 MissionKnapsack** (0/1 knapsack DP, **chứng minh tối ưu vs brute-force 30 case**). Schema additive: `policy_bundle.weekly_quota`, `solver_report` enum +2, 2 view L3 mới. 53 test, suite 274. **Fix**: mock mission thiếu `target_count` → S6 vô nghĩa (regression test). **Đính chính**: thưởng tuần KHÔNG có field trong bảng thật → S5 tính từ policy; gap payout R2 một phần là khác ĐỊNH NGHĨA (commission vs tổng thu nhập).
   - **PI-5a** ✅ DONE 2026-07-24 (UPDATE-040): nối **S5/S6 vào pipeline C6** — router F1/F2/F3 + intent `mission_task`/`weekly_target`, context_pack render key mới, template sinh câu khoán tuần + mini-task. 15 test, suite 299. **2 bug ngữ nghĩa lộ khi ĐỌC output** (test vẫn xanh): số bị gán nhầm nhãn ("mốc thưởng 35585.2 vnd_per_hour") do lấy theo VỊ TRÍ registry; nói "còn thiếu 0đ/truy thu 0đ" khi đã đạt khoán (so CHUỖI thay vì SỐ) — đã fix + test.
   - **PI-5b** ✅ DONE 2026-07-24 (UPDATE-041): **S7 IdleReduction (UC5)** — solver đầu tiên dùng `public_driver_hex_tracking` (1.09M dòng); nối F2/F3 + intent `idle_wait`; **đủ 5 điều kiện D-004b** (không chọn điểm đứng hộ, khu vực chỉ nhắc nhiệm vụ chính thức, cảnh báo tỷ lệ nhận, nhãn PROXY, không khuyên đơn). 14 test, suite 313. **Fix trạng thái BẤT KHẢ** (lộ khi đọc output): dwell offline bị gán `idle` ⇒ chờ 1300 phút > online 4.8h; nay dwell >90ph = `offline` + `data_warning` + invariant Σidle ≤ online. Output khớp research (idle 45% ~ util FT 45-55%; khung 13h ~ dead hours).
   - **PI-5c** ✅ DONE 2026-07-24 (UPDATE-042): **S8 PenaltyExplain (UC6)** + **S9 AnomalyAlert (UC7)** → **UC1–UC8 PHỦ HẾT bằng 9 solver**. Guardrail là thiết kế chính: UC6 chỉ nêu quy tắc + cách TUÂN THỦ (test chặn từ khoá dạy lách); UC7 **KHÔNG kết tội** — chỉ 'ghi nhận dấu hiệu' + confidence + khuyến nghị liên hệ hỗ trợ, cờ đã cleared thì im lặng, không lộ evidence/ngưỡng. **Chỉ hiện ở F3, không bắn giữa ca.** 21 test, suite 334. **Fix BUG-PI5c-01**: đồng âm tiếng Việt — 'bất thường'→'bat thuong' chứa 'thuong' (=thưởng) làm route sai → router nay lấy **keyword DÀI NHẤT**. + tách `vn_format.py` (1 nguồn định dạng tiền).
   - **PI-5d** ✅ DONE 2026-07-24 (UPDATE-043): **recheck toàn dự án** — 3 subagent audit FAIL (hết hạn mức chi tiêu) → tự audit; **property test xuyên solver** (`test_solver_properties.py`, 37 test). **Research đợt 4** đảo 3 giả định: app **CÓ bản đồ nhiệt + "Nhiệm vụ tiếp theo"** (đính chính căn cứ D-004), **4 mức cảnh báo gian lận** chính thức, **hạn giải trình 48 GIỜ**. Đồng bộ S7/S8/S9 + pain-point P-5..P-7. **Fix BUG-PI5d-01**: số giờ không neo registry ⇒ verifier VETO advice. Suite 334→378.
   - **Còn lại:** PI-3 live DataSource **DEFERRED chủ ý** vì publish dùng mock/local; PI-6 External có key/config nhưng provider/cadence chưa implement; C7 EXP (LLM live) chưa bắt đầu.
   - **Follow-up không cần unblock**: audit độc lập lại khi có quota; `SOLVER` const cho S1-S4; property test phủ shift_dp/capacity_alloc; xác nhận GSM (tiêu chí 4 mức, heatmap cho Bike, mốc tính 48h).
   - **PI-5 UC5-8 features**: idle-reduction, penalty-explain, anomaly-alert + router (P6). Sau PI-4.
   - **PI-6 External** (treo): ExternalContext theo stack hiện hành WeatherAPI + OSRM + Stadia + Jina. Google Maps không cần (Q-02 closed). Cần cycle provider/cache/freshness riêng, không còn blocked chỉ vì key.
   - **Cần Cường/GSM chốt trước live integration:** semantics 5 field + target KPI + cột thật 5 bảng; BQ auth/env. External key/config đã có, nhưng provider/cache/freshness là cycle riêng. **LOẠI TRỪ**: hiệu năng AI-Advisor/observability/CICD/optimize.
9. **C7**: EXP-001..005 trên instrumentation C6 (episode store đã bandit-ready). **Gated:** eval set F0 phải phản ánh policy hiện hành (post-refresh) + snapshot MOCK được regen/verify đúng schema và provenance; không gọi PI-2 là data thật.
10. **T-039** checkpoint mở rộng sau mỗi C#/T# hoàn thành (section bắt buộc trong UPDATE_TEMPLATE).

**Track A — SIM OVERHAUL (ưu tiên cao nhất, Cường 2026-07-24; spec `specs/simulation/00-sim-overhaul-master.md`):**

1. ✅ **SIM-1 Realism gate — DONE 2026-07-25 (UPDATE-044).** Sửa 3 khuyết tật tại GỐC:
   served **61.9% → 82.3%** (phủ ca P6 sáng sớm/P7 tối-đêm, n=74, patience 5ph đúng nguồn),
   completion **99.6% → 94.7%** (huỷ-sau-nhận 5%, mất thời gian+pin thật),
   accept **96.3% → 91.0% và BÁM `accept_base` từng archetype** (P4 tân binh .781 vs P3 .965
   — trước đây chênh 5đ%, archetype gần như vô nghĩa). Data BIKE đọc counter sim (coherence).
   Gate 30 seed: `tests/test_sim_realism.py` (10 test). Suite **388** xanh.
   Flaw còn lại: F-SIM1-A (trips/driver 12.3 < 18-22 — cơ cấu 1 quận, đã defer), F-SIM1-B/D (LOW).
2. ✅ **SIM-2 Driver journey — DONE 2026-07-25 (UPDATE-045).** `src/gsm_sim/journey.py` +
   tab dashboard 🧭 + export JSON. Từng offer có **LÝ DO** (`economics` = chê xa/rẻ ⇒ dư địa
   advisor; `base_behavior` = mệt/kén ⇒ khuyên tiền vô ích). Bug thật: `income_curve` từng bỏ
   sót **thưởng ngày** (thiếu 60.000đ) — thưởng là thứ advisor tối ưu nên đây là lỗi nặng.
   14 test, suite **405** xanh, RNG không trôi.
   **F-SIM2-A (D-SIM-02) đã được mở khoá code ở UPDATE-055** bằng newbie/rating/mission mechanism;
   active GSM reward values vẫn `BLOCKED D-POL-05`, nên baseline là PROXY và V-03/V-09 còn phải review.
3. ✅ **SIM-3 Advice→Action — DONE 2026-07-26 (UPDATE-046).** `src/gsm_sim/advice_bridge.py`
   (S2 → `IdleAction` + tuân thủ theo archetype, mặc định TẮT). Bug thật **BUG-SIM3-01**:
   `ONLINE→WAIT` sai ngữ nghĩa (ONLINE = 'cứ làm việc', KHÔNG phải 'đứng im') ⇒ ghi đè cả
   RELOCATE, đo được d-42 tụt 14→11 cuốc, 214k→155k. Nay ONLINE = không can thiệp.
   15 test, suite **420**.
   ⚠️ **F-SIM3-A**: cầu nối mới dùng **1/9 solver** ⇒ Δ(B−A)≈0 (−3.173đ, trong nhiễu).
   KHÔNG phải advisor vô dụng — kênh tác động còn hẹp. **SIM-4 phải đọc mục này trước khi
   diễn giải kết quả**, nếu không sẽ kết luận sai là advisor không có giá trị.
4. ✅ **SIM-4 Parallel worlds — DONE 2026-07-26 (UPDATE-047).** `src/gsm_sim/parallel.py`
   (A/B chung seed, hiệu theo cặp + CI bootstrap, thang bậc kênh, guardrail) +
   `scripts/run_parallel.py`. **Kết quả 30 seed (tài xế P4):** `s2_only` Δ=**đúng 0** ⇒ xác nhận
   định lượng F-SIM3-A; `+accept_lift` **+32.276đ** CI[+8.255,+58.480]; `all` +42.471đ.
   Guardrail: served_rate KHÔNG đổi ⇒ không hại hệ thống.
   ⚠️ Ba điều phải đọc kèm: (a) `shift_extend` tăng tiền bằng THÊM GIỜ — payout/giờ +19,3% <
   accept_lift +21,5%; (b) chỉ **16/30 seed** Δ dương ⇒ đây là CANH BẠC, không phải chắc thắng;
   (c) ~~vách đá: tuân thủ nửa vời LỖ 34k~~ **ĐÃ BÁC BỎ (UPDATE-048)** — chỉ đúng trên 1 seed;
   30 seed cho thấy ngưỡng được chạm 27/30 lần và nhóm không-chạm vẫn Δ dương.
   Kết luận ĐÚNG: **median Δ ≈ +394đ** dù mean +33.839đ ⇒ mean bị vài ngày thắng lớn kéo lên;
   advice là **xổ số**, phần lớn ngày gần như không đổi.
   ✅ **D-SIM-05 DONE 2026-07-26 (UPDATE-048)**: đã cài điều kiện khả thi (tỷ lệ còn gỡ được +
   có chạm nổi mốc điểm). Đo lại: **INERT** ở config hiện tại (không chặn lần nào) — giữ lại làm
   lan can cho ca ngắn/ngày xấu, nhưng KHÔNG phải nguồn cải thiện.

5. ✅ **SIM-5 Metrics + xuất data — DONE 2026-07-26 (UPDATE-049). LỘ TRÌNH TRACK A HOÀN TẤT.**
   `src/gsm_sim/sim_metrics.py` + `scripts/regen_mock.py` + manifest ghi `engine_commit`.
   **Regen 90 ngày** từ engine mới: acceptance data **0.909** ≈ sim **0.910** (trước 0.88 vs 0.96).
   4 vòng verify xanh, **BIKE 6/6 PASS 0 GAP** (giờ online median 8.79h — trước là gap ~4.5h).
   Phát hiện: acceptance=1.00 tăng 12%→23% **KHÔNG phải hồi quy** — bản cũ mượt GIẢ TẠO do sinh
   bằng `gauss`; bản mới là tỷ số 2 số nguyên thật, giống dữ liệu thật. Suite **446**.

**SIM-XANH (chỉ thị Cường 2026-07-26) — ✅ XONG 2026-07-26 (UPDATE-054..058, 5 commit):**
P1 OSRM đường thật (fetch 1 lần, offline; factor median 1.46 > detour 1.3; re-baseline có tài liệu:
center 21.2k, eta 11, n=90; gate 13/13) · P2 rating/tân-binh-Q01/mission trong sim (tiền 4 nguồn,
13 test) · P3 sweep D-SIM-06 (P4 dương-mỏng chỉ SIG ở lift 0.19; P1 zero CẤU TRÚC; P2 lật kỳ vọng —
thưởng chấm REALIZED nên dip-alert cứu thưởng thật) · P4 dashboard palette-VALIDATED 5/5 + Replay
TripsLayer + tab A/B + heatmap sweep (V-09) · P5 regen 90 ngày engine mới.
→ **D-SIM-18** (shrinkage estimator) chuyển MATH AUDIT. Thứ tự tiếp: ~~Track C~~ **Track UI → AUDIT toàn bộ**.

**Track UI (chỉ thị Cường 2026-07-26 — DIRECTIVES §11, THAY Track C mock-UI) — ✅ U0-U4 XONG
2026-07-26 (UPDATE-059..063, chờ verdict V-10):**
Import UI Khánh (`uiuxgsm` → `ui/`) làm nền UI THẬT; web app 5 màn + khu Mô phỏng chạy trên
backend FastAPI chung đọc mock 90 ngày + solver S1 thật + engine sim (Replay/Hành trình/A/B/
heatmap sweep). Palette light VALIDATED (giữ hue theo entity; cyan brand = chrome accent).
Contract-first cho Khánh làm Flutter song song (**T-009b READY** — `ui/contracts/` + tokens +
SCREEN-PARITY). `F-U2-A` đã **CLOSED như data fact** ở UPDATE-066 (13 bảng GSM không có bảng bonus riêng; UI caveat giữ nguyên). Nợ mở Track UI: F-U2-B (tỷ lệ granularity ngày → D-SIM-18/AUDIT), F-U3-A (replay chưa bám tim đường),
D-UI-01 (nghỉ hưu dashboard sau V-10), D-UI-02 (vendor hoá CDN).

**Việc đáng làm tiếp sau Track A** (cập nhật 2026-07-26, UPDATE-050): đã nối solver thứ 2 (S7
`idle_reduction`, kênh `rest_window`) và **chẩn đoán ra nguyên nhân gốc**: S2 là solver DUY NHẤT
nhìn về phía trước; phần còn lại HỒI CỨU/thông tin nên không có kênh tác động thời gian thực.
⇒ Ưu tiên: **`D-SIM-10` sim nhiều ngày** (mở khoá S3/S5/S7/S8/S9 cùng lúc — đòn bẩy lớn nhất),
✅ **`D-SIM-09` DONE 2026-07-26 (UPDATE-051)**: đã nối S1. Phát hiện quan trọng về cách ĐỌC SỐ —
Δ mean giảm (+32.276→+20.473) nhưng đó là **cải thiện**: advisor nay **im lặng ở 16/30 ca**
không giúp được, lỗ chỉ còn **4 seed**, lợi/hại ≈ **5,7:1**. Bản cũ luôn khuyên nên phần lớn
seed không-lãi là lỗ thật. Bản cũ còn **bỏ sót hoàn toàn ràng buộc `completion`** ⇒ khuyên nâng
tỷ lệ NHẬN trong khi chỗ nghẽn là tỷ lệ HOÀN THÀNH (sai địa chỉ).
✅ **`D-SIM-10` DONE 2026-07-26 (UPDATE-052)**: `run_multiday` + `DriverMemory` + `reset_for_new_day`.
**Chẩn đoán UPDATE-050 được XÁC NHẬN**: cùng kênh S7 ở sim 1 ngày cho 0 event tuyệt đối, nay có
event từ ngày 2 (lý do `defer_to_13h`). Carry-over có tác dụng thật (Δ +23.920đ/7 ngày).
Bug thật: mọi ngày dùng CHUNG list actors ⇒ `days[0]` phản ánh ngày CUỐI (im lặng, không crash).
Kiểm chứng CHẠY THẬT L1-L6 theo yêu cầu Cường. Suite **463**.
✅ **`D-SIM-13` DONE 2026-07-26 (UPDATE-053)**: B (memory→S1) + C (tuần ISO-aligned, đóng tuần cuối)
+ D (mockgen chuỗi liên tục, regen 90 ngày, BIKE 6/6 PASS). **Review đối kháng 28-agent trên diff**:
24 finding confirmed → 11 fix ngay (nặng nhất: vòng lặp tự tham chiếu C1/C6 — lịch sử ghi ngày
đã-lift làm advisor tự tắt; manifest nói dối commit C7/C12) + 3 defer (D-SIM-14/15/16).
**BUG-DSIM13-02** lộ khi viết test thiếu: 0/0→acceptance_rate=1.0 chặn nhầm advice đầu ca ⇒
**đính chính UPDATE-051** (câu chuyện im-lặng-16/30 phần lớn là artifact của bug này; sau fix
accept_lift về đúng +32.276đ/16-30).
⇒ Còn lại: `D-SIM-11` (S1 trả mã lý do có cấu
trúc thay vì để sim parse tiếng Việt), `D-SIM-12` (4 seed còn lỗ).
~~`D-SIM-03` mở rộng action-space (mới 1/9 solver có kênh tác
động — giới hạn LỚN NHẤT của kết quả A/B), rồi Track B (external data) / C (mock UI) / D (C7) / E.

**Track SIM/Advisor (PAUSE sau T-030 — resume sau khung core; reliability-first):**

1. ✅ **M0 — T-030 Simulator integrity (DONE 2026-07-22, UPDATE-023):** 12 flaw + C-2 fixed, 57/57 test, determinism cross-process PASS.
2. **M1 — T-031 (PAUSED — Track CORE chạy trước, 2026-07-23):** 24h dynamic market + data schema/inferable projection.
3. **M2 — T-032→T-034 (PAUSED):** OSM endpoints → H3 routing contract → exogenous traces.
4. **M3 — T-035→T-037 (PAUSED):** Story/actor/Diagnostic visualization.
5. **M4 — T-019 + T-020 (sau C6/C7):** twin-integration kế thừa artifacts core; T-026 đã nhập vào C2/C6.
6. **Sau M4 — T-027 Robustness/shift.**

Source of truth sim: `specs/simulation-reliability-upgrade.md`. Mỗi milestone/C# có plan mode riêng, multi-seed/boundary/full-suite verification và visual review theo `CLAUDE.md` §4b.

**Track song song (không đụng files nhau):**

- **Khánh: T-009 UI clone** — ✅ **DONE 2026-07-26**: bàn giao `uiuxgsm-main.zip` (Stitch web demo +
  Flutter + FastAPI), import vào `ui/` (UPDATE-059). Tiếp nối: **T-009b Flutter mobile song song**
  (phạm vi `ui/driver_app/`, bắt kịp qua contracts — xem ASSIGNMENTS).
- **Người thật (ai rảnh): T-013** join FB group + kiểm changelog app (chặn crawler).
- **AI agent (khi Cường rảnh review): T-004 KB chính sách** (độc lập với sim; cần cho product F0 sau).
- Dashboard sim (xong slice v0) — nâng cấp dần theo nhu cầu xem/control.

**Hoãn cho tới khi track SIM xong:** T-005 (CrewAI — advisor tự viết đang tiến tốt, đánh giá lại sau), T-006/T-007/T-008 (khung F1-F3 product — sẽ tái dùng advisor từ sim), T-011 (contract — chốt sau khi advisor API ổn định), T-015 (community — roadmap).

| ID | Việc | Trạng thái | Owner | Ghi chú |
| --- | --- | --- | --- | --- |
| T-001 | Deep research chính sách & thu nhập tài xế Xanh SM (theo `planning/RESEARCH.md`) | DONE (đợt 1) | AI agent (Cường duyệt) | 2026-07-20; output: `research/` (chia theo loại); gaps còn lại → T-012 |
| T-002 | Thiết kế hồ sơ tài xế mock (Bike trước) từ kết quả T-001 | DONE (nháp v1) | AI agent | 2026-07-20: 5 persona tại `planning/PERSONAS.md` (thêm tân binh + lão làng theo yêu cầu Cường); chờ review; số TBD chờ T-012 |
| T-003 | Mock demand proxy theo khung giờ × ngày trong tuần × khu vực | READY (spec xong) | — | `specs/mock-order-distribution.md` đã phân biệt demand vs matching, normalized weights, weather formula, money terms; code generator chưa claim |
| T-004 | Knowledge base chính sách cho F0 (policy có version + trích dẫn) | DONE (text corpus + source register) | Khánh | `research/policy/t004-current-policy-text-corpus-2026-07-22.json` giữ full text + metadata của 7 nguồn T1 current; `T004_TEXT_CORPUS_USAGE.md` nêu guardrail. HTML/ảnh/OCR/crawler không vào repo; T-011/reviewer mới được tạo policy fact runtime. |
| T-005 | Đánh giá framework agent: CrewAI vs flow tự viết (orchestrator theo drawio v2) | TODO | — | Stakeholder refer CrewAI; cần so sánh control/guardrail/độ phức tạp |
| T-006 | Khung F1 trước ca: chỉ tiêu net mặc định + nhận xét chỉ tiêu theo hồ sơ | TODO | — | Phụ thuộc T-002, T-004 |
| T-007 | Khung F2 trong ca: lời khuyên chạy/nghỉ/sạc từ phân phối mock | TODO | — | Phụ thuộc T-003 |
| T-008 | Khung F3 sau ca: analyzer/advisor + danh mục hành vi chưa tối ưu | TODO | — | Phụ thuộc T-002 |
| T-009 | UI/UX tạm: clone tham khảo, mobile-first | **DONE 2026-07-26** | Khánh | Kết quả vượt brief: Stitch web demo + Flutter + FastAPI (repo riêng `uiuxgsm`) → import `ui/` (UPDATE-059). Kế nhiệm: T-009b |
| T-009b | Flutter mobile song song web (contract-first) | READY | Khánh | Phạm vi `ui/driver_app/`; đồng bộ qua `ui/contracts/` + `ui/design-tokens.json` + `ui/docs/SCREEN-PARITY.md` |
| T-010 | Xác nhận scope luồng giải trình vi phạm (drawio file 2) | DONE | Cường | Chốt 2026-07-20: dự án khác, ngoài scope repo này — xem D-006 |
| T-011 | Định nghĩa contract/schema mới cho scope v2 (hồ sơ tài xế, demand proxy, output tư vấn) | TODO | — | Contracts cũ deferred; contract mới phải version hóa policy bundle + money definition (`gross_revenue`, `driver_payout`, `estimated_net_income`, cost completeness) |
| T-012 | Research đợt 2: bảng thưởng chi tiết + kinh nghiệm cộng đồng (FB groups, TikTok/YouTube) | DONE | AI agent | 2026-07-20: KHÔNG OCR/app. Bảng thưởng đã verify: `research/policy/bonus-programs.md`; cộng đồng: `research/community/community-insights.md`. FB groups cần join tay (T-013) |
| T-013 | Join 1–2 group Facebook tài xế + đọc mẹo thực chiến, số thành viên | BLOCKED (human login) | — | Cần người thật (login wall chặn crawler); danh sách 6 group ở `research/community/community-insights.md` |
| T-014 | Vẽ lại luồng v2 (drawio 7 trang: L0–L2 + F0–F3, hiện tại + tương lai) | DONE | AI agent (Cường duyệt plan + flow) | 2026-07-20: Cường duyệt flow và yêu cầu commit; checkpoint consistency ghi tại UPDATE-006 |
| T-015 | (Tương lai) Tích hợp nguồn cộng đồng + khối kiểm chứng/lọc rủi ro vào sản phẩm | DEFERRED / ROADMAP | — | Roadmap D-008; theo `specs/community-source-risk-control.md`; cần F0–F3 chạy ổn trước |
| T-016 | Research đợt 3: tooling sim + evaluation methodology + tham số thế giới HN | DONE | AI agent | 2026-07-21: 3 file tại `research/simulation/` (tooling, evaluation-methodology, world-parameters) |
| T-017 | Review & chốt 2 spec sim | DONE | Cường | 2026-07-21: **APPROVE toàn bộ quyết định thiết kế + thêm arm C placebo**; spec đánh dấu APPROVED |
| T-018 | Simulator core/runner substrate: world + actors + dispatcher + deterministic trace/CRN nền | WAITING-VERDICT (successor SIM-1..5 complete) | Cường | UPDATE-010/012 là legacy slice; UPDATE-023 và UPDATE-044..058 chứa successor evidence. Không còn coi claim DOING cũ là active implementation; visual/pending verdicts vẫn ở V-01..V-09. |
| T-019 | M4 Advisor-sim arm A + C: trigger hybrid + DP lớp A + capacity ledger + placebo random-safe | TODO | — | Chỉ sau M0–M3 gate. Kèm T-026 đồng thời; spec-first/LLM-offline, template fallback. Không nhìn future realized orders, không can thiệp dispatch. |
| T-020 | M4 Twin-runner A/B/C + paired evaluator + adherence/divergence attribution | TODO | — | Sở hữu orchestration/evaluator (`A−B`, `C−B`, `A−C`, ITT/CACE/CI). Dashboard stakeholder chung chuyển T-035–T-037; comparative view đọc canonical evaluator artifacts. |
| T-021 | Calibration/realism gate xuyên M0–M4 theo evidence tiers + invariants + sensitivity | WAITING-VERDICT | — | UPDATE-044..058 cung cấp calibration/sensitivity code evidence; V-01..V-06, V-08/V-09 chưa có human verdict. Distribution/calibration mặc định ≥30 seeds trừ khi plan giải thích khác. |
| T-022 | Research đợt 4: action space tài xế + pilot world 1 quận/50 actors + timestep phân tầng | DONE | AI agent | 2026-07-21: `research/simulation/{action-space,pilot-world-dongda,timestep-design}.md` + `data/` (OSM: 11 tủ pin Đống Đa, POI, polygon); spec tổng hợp: `specs/simulation-pilot-world.md` |
| T-023 | Chốt action taxonomy cho SIM actor + phạm vi advisor tác động (product vs sim) | DONE | AI agent + Cường | 2026-07-21: verify chuyên sâu → **A13 = UNVERIFIED** (nguồn duy nhất là trang AI-gen; không dấu vết official/báo chí/diễn đàn sau 3,5 tháng); **Xanh KHÔNG có heatmap tài xế** → advice khu vực = BỔ SUNG không chồng đè, Cường mở CÓ ĐIỀU KIỆN (5 điều kiện an toàn trong `action-space.md` §Phạm vi advisor: capacity-aware, cảnh báo tỷ lệ nhận, nhãn mock, không hứa thu nhập, shift-aware flag OFF). Kiểm changelog in-app → T-013 |
| T-024 | Realism pass: đối chiếu mọi MOCK với benchmark thực tế → chỉnh config | DONE | AI agent (claim Cường) | 2026-07-21: `research/simulation/realism-benchmarks.md`; sửa patience/day-bonus/time-accounting/demand-hint. Kết luận: baseline B unserved 34% là dư địa advisor, target 15-20% cho arm A |
| T-025 | Research kiến trúc AI Advisor LLM-in-the-loop + observability + multi-map | DONE (research) | AI agent (claim Cường) | 2026-07-21: `research/simulation/llm-advisor-architecture.md` — CHỐT "spec-first LLM-offline" + Langfuse/Phoenix + same-map robustness. Spec chi tiết `specs/advisor-system-detail.md` viết khi bắt đầu T-019. Smoke test: deepseek+JSON+cache OK, gpt-4o-mini 403 |
| T-026 | Observability per-layer cho advisor: Langfuse (hoặc alternative từ research) + metric bảng theo layer (trigger/DP/LLM/adherence); xây ĐỒNG THỜI với T-019 | DONE-CODE | Cường (AI agent) | UPDATE-025 metric table + UPDATE-030 C6 phase-2 instrumentation hoàn tất. Live LLM smoke là D-C6-03 riêng; không giữ T-026 ở TODO vì thiếu live endpoint. |
| T-027 | Robustness/shift measurement: regime sweep (orders 900/1200/1800, mưa, adoption, archetype mix, station outage) trên cùng map; multi-map chỉ khi cần external validity | TODO | — | Sau T-034 (world shifts) + T-020 (evaluator); task validation, không sở hữu world implementation. |
| T-028 | Dashboard sim v0 (Streamlit + pydeck H3): xem + control (seed/demand/actors/dispatcher levers) | DONE (v0) | AI agent (claim Cường) | 2026-07-21: `src/gsm_sim/dashboard.py`; predecessor của T-035–T-037. Replay/actor journey không còn gộp vào T-020. |
| T-029 | Governance + master spec chương trình simulator reliability-first M0–M4 | DONE (docs) | AI agent (theo yêu cầu Cường) | 2026-07-22: `specs/simulation-reliability-upgrade.md`; cập nhật SCOPE/TODO/DEFERRED/CLAUDE.md/UPDATE template — xem UPDATE-021. Không thay đổi code sim. |
| T-030 | M0: preserve/audit working diff Stage A–C + baseline manifest + canonical lifecycle/conservation/determinism invariants | WAITING-VERDICT | Cường (AI agent) | UPDATE-023: 12 flaw M0 + C-2 fixed failing-first, 57/57 test, cross-process determinism PASS. Code gate xong; human visual verdict còn nằm ở V-01..V-02, không gọi là fully complete. |
| T-031 | M1: full `[00:00,24:00)` dynamic daily actor pool + NHPP/piecewise-linear demand + bin validation + **data schema/inferable projection** | READY (khi T-030 đóng visual gate) | — | **Ưu tiên Cường 2026-07-22: chốt DATA SCHEMA trước** — observable events (app/GPS/swap) chuẩn hóa sẵn để feed math modelling/context model/actor state; latent chỉ là sim ground truth. Kèm: dead flag `hour_interp` (NHPP), participation funnel, bins 1/5/15ph ≥30 seeds; sim data phải dựa thực tế. |
| T-032 | M2a: OSM road/POI endpoint provider + immutable cache/provenance/offline replay | BLOCKED | — | Phụ thuộc T-030. Pickup/dropoff có `osm_id`, source, H3, bundle hash; không network trong sim loop. Road graph chưa bắt buộc ở endpoint v1. |
| T-033 | M2b: H3 candidate shortlist + continuous/road distance/ETA/trajectory contract | BLOCKED | — | Phụ thuộc T-031 + T-032. Atomic lat/lon/H3 movement, deterministic tie-break, explicit Haversine×detour fallback; dispatch H3 invariants. |
| T-034 | M2c: smoothed congestion + weather/event/route-effect/distribution-shift traces + attribution/no-future-leak | BLOCKED | — | Phụ thuộc T-031 + T-033. Tách base/demand `[PROXY]`/rain/event, survival combine, `known_at/effective_at`, no-op equivalence. Hấp thụ follow-up UPDATE-012. |
| T-035 | M3a: Story Mode city pulse + canonical replay/player (per-event, 1/5/15 phút) | BLOCKED | — | Phụ thuộc T-034; narrative market 24h. H3 mặc định phẳng/bán trong suốt; station layer trên cùng; active fleet/lifecycle/environment đồng bộ playhead. |
| T-036 | M3b: actor journey selector + route/Gantt/SOC/payout/points + flaw labels + advisor placeholder | BLOCKED | — | Phụ thuộc T-035. `OBSERVED` ≠ `HEURISTIC` ≠ `PAIRED_COUNTERFACTUAL`; chưa có M4 thì không hiển thị số “mất tiền” chắc chắn. |
| T-037 | M3c: Diagnostic Mode + audit panels + visual-review harness | BLOCKED | — | Phụ thuộc T-035 + T-036. Demand/supply/lifecycle/spatial/station/evidence diagnostics; launch seed/scenario cho Cường review theo CLAUDE.md §4b. |
| T-038 | **CORE C0+C1: chốt data schema (L0–L3, platform-centric) + MOCK data generator theo schema** | DONE-CODE | Cường (AI agent) | UPDATE-024 và UPDATE-034..039: schemas, registry, mockgen, exact GSM names, 90-day data, integrity/audit gates hoàn tất. Entity/data thật còn thiếu là dependency riêng, không giữ T-038 ở VALIDATING. |
| T-039 | **Recurring: expansion checkpoint — MỞ RỘNG schema / bài toán tối ưu / tính năng?** | RECURRING | — | Yêu cầu Cường 2026-07-23: sau MỖI phần hoàn thành (mỗi C#/T#), UPDATE phải có mục trả lời: (1) schema cần thêm/bớt field gì? (2) có bài toán mới formalize được không (residual→solver)? (3) tính năng mới khả thi từ data hiện có? Không tự triển khai — ghi đề xuất để Cường duyệt. |

## Post-audit work registered from UPDATEs

Các mục dưới đây đã có UPDATE/evidence nhưng trước đây chưa có dòng TODO riêng. Chúng không tự mở quyền implementation ngoài claim và pending gate.

| ID | Việc | Trạng thái | Evidence / gate |
|---|---|---|---|
| UI-FARE-01 | Unify Simulator and Web Driver demo fare through `PolicyBundle` | DONE-CODE / WAITING-VERDICT | UPDATE-073; **V-16** (đánh số lại từ V-11 — xem PENDING-REVIEW); do not touch Flutter `ui/driver_app/` |
| **SOL-LUNA-HARNESS** | Codex delegation policy: đọc `CLAUDE.md` trước, Sol lập workflow, Luna `xhigh`, quota queue | DONE-CODE (docs-only) | UPDATE-125; `AGENTS.md`; không đổi runtime config |
| UX-CARDS | Proactive cards + explicit adherence contract | DONE-CODE / WAITING-VERDICT | UPDATE-067; V-10 |
| R1/R4 | App-language simulation shell + playback/feed | DONE-CODE / WAITING-VERDICT | UPDATE-068; V-10 |
| AUDIT-A1/A2/A3 | Math, integrity, agent-system audit + narrow fix batches | DONE-CODE | UPDATE-064..066, 069..070; ĐA-01..06 and D-A3-01..06 remain open |
| R5-A | UI cards guardrail/fail-closed path | DONE-CODE / WAITING-VERDICT | UPDATE-071; V-10 |
| R5-B | Remaining double-check workflow | QUOTA-BLOCKED | UPDATE-071 §4/§6; rerun after quota/session availability |
| F-U2-A | No dedicated daily/newbie bonus table in 13 GSM tables | CLOSED (data fact) | UPDATE-066; retain UI caveat, not an active blocker |
| D-M3-11 | Future-information leak in 6 L3-view fields (l1r derivers) | FIXED | UPDATE-115; 13 tests + 6/6 mutation; no published number affected (module unimported) |
| D-M3-12 | Make the future-leak probe a standing gate for every `t_now` deriver + test the parse-failure path of `_observed_seconds` | TODO (sev TRUNG) | UPDATE-115; needs per-entity cut-key decision first (a false positive already occurred) |
| D-M3-04 | Multiday A/B so `rest_window` stops being INERT — now a **CONDITIONAL TRIAL**: Cuong 2026-08-03 said *"try D-M3-04 first; keep it if meaningful, otherwise revert to soft advice"* | READY — green-lit, **Cycle B** (own plan per CLAUDE.md §4b: it changes sim behaviour and adds a measurement path). Decision rule pre-registered **before** measuring in `d-m3-04-multiday-prereg-locked.json` → `luat_quyet_dinh`; REVERT is the branch the prereg **predicted** (world β=0) | `specs/simulation/d-m3-04-multiday-ab-brief.md`; wire `touched_actors` into the tier-5 gate as part of the cycle |
| D-M3-13 | Tier-5 guardrail had an aggregator but no data source in the A/B path | FIXED | UPDATE-116; measured: `TREO — THIẾU DỮ LIỆU` on every real pair; 0 stored artifacts carried the key |
| D-M3-15 | Orphan-mechanism sweep: 5 unread config flags (3 of them documenting WRONG behaviour) + 14 uncalled public functions incl. a dead module with a conflicting colour table | FIXED | UPDATE-117; standing gate `test_config_flags_wired.py`; behaviour-neutral verified 5/5 seeds |
| **BUG-F2-NOW** | 🔴 **Template F2 đã sửa trong cycle này** — dùng `schedule[0]` cho action hiện tại, tách `next_action` thành bước tương lai; legacy report thiếu `schedule` vẫn fallback tương thích. | **DONE-CODE / visual WAITING-VERDICT** | UPDATE-124; regression `test_f2_uses_action_now_not_next_action` |
| **CKPT-00..05** | ⚠ **ĐÁNH SỐ LẠI 2026-08-03 (UPDATE-123)** → thay bằng `CKPT-A..F` + `CKPT-P1..P6` dưới đây. Kế hoạch hiện hành: `tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md` (bản tổng hợp, đã đối chiếu plan review độc lập). Lý do đổi: thứ tự verifier↔agent bị SAI ở bản cũ, và GĐ0 nay là 6 việc làm được ngay chứ không phải hàng chờ | SUPERSEDED | UPDATE-123 |
| **CKPT-A** | 🔴 **BUG-F2-NOW** — `templates.py` dùng `schedule[0]` cho hiện tại, `next_action` chỉ cho bước tương lai; prompt/context F2 đã nói rõ hai semantics | **DONE-CODE / visual WAITING-VERDICT** | UPDATE-124; PLAN §GĐ0-A; test đỏ trước |
| **CKPT-B** | Safety text-card khi đang lái luôn queue; v1 chỉ nhận surface đóng `brief/nudge/recap`, v2 topic/priority hoàn toàn server-owned | **DONE-CODE** | UPDATE-126; backend contract/API regression |
| **CKPT-C** | Sim journey chỉ project allowlist event tài xế; `advice_rest_veto` và event kỹ thuật không còn thành card | **DONE-CODE** | UPDATE-126; sim router regression |
| **CKPT-D** | Mọi silent response v1 mang scenario/seed/data_mode/is_mock; enum reason đóng đã đủ queue/cooldown/budget/dismiss | **DONE-CODE** | UPDATE-126; contract validation mọi verdict |
| **CKPT-E** | Flutter đã bỏ card recommendation hard-code SOC/trạm/nhu cầu; thay bằng empty state và chỉ hiển thị AdviceCheckpoint có provenance khi backend cung cấp | **DONE-CODE / visual WAITING-VERDICT** | UPDATE-124; PLAN §GĐ0-E; claim `ui/driver_app/` của Khánh |
| **CKPT-F** | Trả nợ tài liệu: `findings.md` có 2 sai sót + 1 mâu thuẫn thứ tự đã vào repo | **DONE** 2026-08-03 | UPDATE-123; đã đính chính tại chỗ |
| **CKPT-P1** | Contract 1.1, pure normalizer/policy/projection, atomic SQLite bundle và RAM journal; legacy lifecycle tách biệt | **DONE-CODE** | UPDATE-126; backward upcast + sever/restore tests |
| **CKPT-P2** | Sim capture exact snapshot/input/report tại callsite hiện hữu, RAM journal, JSONL/manifest, deterministic segment/execution link và metrics tách biệt | **DONE-CODE** | UPDATE-126; comparator `IDENTICAL` 5/5 seed |
| **CKPT-P3** | S1/S2 orchestration fail-isolated; S2 true-state fail-closed; atomic lease; API v2 + Web/Flutter template flow | **DONE-CODE / visual WAITING-VERDICT** | UPDATE-126; ACK là mounted ACK, metric break đã ghi |
| **CKPT-P4** | Closed structured presenter/verifier; agent không sở hữu action/window/numbers; tối đa một repair rồi template fallback | **DONE-CODE** | UPDATE-126; golden/adversarial suite |
| **CKPT-P5** | Runtime mặc định template, shadow artifact-only + stale discard/cache claim; simulator method D post-run | **DONE-CODE / shadow-only** | UPDATE-126; live/canary ngoài scope |
| **CKPT-P6** | GĐ6 — LLM live + đánh giá; shadow→canary→opt-in | TODO | PLAN §GĐ6 |
| **WEB-DEMO-UNIFIED** | **DONE-CODE / WAITING-VERDICT** — trace, server session, canonical step, AdviceCheckpoint bridge, Web render và demo displayed ACK đã có; chưa có human visual V-25 hoặc narrow live smoke. Không đổi SimPy thành live engine, không gọi solver theo click | UPDATE-128..133 + `docs/superpowers/plans/2026-08-04-unified-web-demo-implementation.md` | chờ visual V-25; live Agent vẫn ngoài scope |
| **CKPT-MIG** | Không migration/backfill: `source_decision_id` là legacy solver/adherence reference; `checkpoint_id` là identity riêng của checkpoint stream | **RESOLVED-BY-DESIGN** | UPDATE-124/126; separate-stream architecture |
| D-M3-16 | Gate for `STATE_COLORS` vs `ACTIVITY_COLORS`; decide delete-or-keep `trajectory.py` (V-22); real 15-min metrics bucket needs behaviour change + fresh measurement | TODO (sev TRUNG) | UPDATE-117; same family as D-M3-12 — architectural debt, not isolated accidents |
| D-M3-12 | Future-leak probe promoted to a standing gate (7 derivers, sever-restore + empty-green counter-check) | FIXED | UPDATE-118; 7/7 clean = independent evidence UPDATE-115 closed the family |
| D-M3-16a | Single-source gate for activity-state colours (conditional on whether `trajectory` is imported) | FIXED | UPDATE-118; de-risks V-22 so the delete-or-keep call is no longer urgent |
| D-M3-17 | UI computed battery range with its own formula (`soc*1.1`, one formula for both fleets) — 1.76x inflated for swap drivers; legacy endpoint used `soc*3.2` = 5.1x | FIXED | UPDATE-121; UI now reads the engine-derived range band and keeps visual verdict `V-25 · UPDATE-121` pending |
| WEEK2-REPORT | Mentor-facing Week 2 report: folder + 24-page PDF + audit checklist for Khanh + source-of-numbers table | WAITING-VERDICT (V-23) | UPDATE-119; 24 subagents cross-checked the repo first; caught Khanh's doc quoting a figure that no longer reproduces |
| D-M3-18 | No battery-fleet field in the data, and 40/150 catalog drivers are CARS — bike consumption factors do not apply to them | TODO (sev CAO) | UPDATE-121; backend+web flag it, Flutter does not read the flag yet |
| SOFT-ADVICE-01 | **Soft advice must not be measured**: no adherence denominator, no `followed`, only a neutral Hide button (Cuong 2026-08-03). Third tier of the health↔money exchange rate that spec §1.2b blocked at the objective and world tiers — this one lives in the PRODUCT | DONE-CODE / WAITING-VERDICT (V-26) | UPDATE-128; `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`; registry `advice_topics.py` + fail-closed gate (**63 tests** across 4 new files (measured 2026-08-03: 15 registry + 29 soft-advice + 8 OSRM + 11 env-loader — recount with `pytest --collect-only`, do NOT trust this number blind); sever-restore 4/4 then 6/6 fired). **Nothing running changes today** — no soft card exists yet; this is rails + a gate so the first one cannot silently land in the measured table |
| SOFT-ADVICE-02 | Weather card using the `soft` render mode (topic `"weather"`), and Flutter (`ui/driver_app/`) honouring the same boundary | TODO — **Khanh** | UPDATE-128; backend/web rails ready; Flutter not checked (Khanh's active claim) |
| D-ENV-01 | `OSRM_BASE_URL` was documented as tier 1 of driver-app routing but **no runtime code read it**; the second OSRM mirror had a **typo'd hostname** (`router.project.osrm.org` — TLS hostname mismatch) so it never worked; `GRAPHHOPPER_API_KEY` was absent from Cuong's `.env` (gitignored, so Khanh's edit never propagated) making tier 2 fail silently | FIXED | UPDATE-128; found by **calling every key for real**, not by reading code. Gate `ui/backend/tests/test_osrm_endpoints_wired.py` (8 tests; sever-restore with REAL pytest 8/8 fired — the earlier "2/2" scripts never ran pytest, see UPDATE-128 §5c). ⚠ Both live OSRM hosts resolve to the SAME IP (5.148.170.168) — swapping mirrors gives **no** extra rate-limit headroom |
| SOFT-ADVICE-03 | **Same boundary, FOURTH write path**: AdviceCheckpoint v2 sat entirely outside it — own store (`CheckpointStore` ≠ `AdviceEventLog`), own `topic` vocabulary **intersecting the registry in ZERO elements**, and `rest` genuinely produced (`checkpoint.py:134`, S7) ⇒ a `rest` checkpoint accepted `response: accepted`, i.e. **a consent trace for a REST recommendation was being written**. No number was wrong yet (`adherence_view` never sees the v2 store) but the data **accumulates** | DONE-CODE / WAITING-VERDICT (V-27) | UPDATE-130; QĐ-4 = option **(b) unify**. Unifies **authority, not names** — `advice_v2.json` strings and stored records unchanged. `record_response` raises `CheckpointSoftAdviceError` → **422** (own class, not 409: 409 implies *retry may work*, this is permanently forbidden); `dismissed`/`expanded` still accepted. 4 gates incl. a **producer** gate anchored on `_topic_for_action`, because the AST scanner is blind to `return "x"` — which is exactly where v2 topics are born. sever-restore **8/8** |
| D-QD4-01 | `rest` in v2 conflates `rest_window` (deferring rest = `C2′`, economic, **measured**) with `rest_nudge` (soft). Classified **soft on purpose, not from certainty** — fail-closed: misfiling economic→soft loses a denominator, misfiling health→measured breaks a settled boundary (§1.2c) | DEFERRED (sev THAP) | UPDATE-130; reopen together with `D-M3-04` — self-cancels if D-M3-04 REVERTs |
| D-QD4-02 | QĐ-4 step 3 — bring `CheckpointStore` into the shared measurement path | DEFERRED (sev THAP) | UPDATE-130; **not needed for the boundary** (post-fix data is clean at source); it is a MEASUREMENT feature dragging in the two-path join (`adherence-measurement.md` §(c)#2). ⚠ Before trusting that store: Cuong's machine has **no** `advice_checkpoint.db` (checked 2026-08-04) but **Khanh's was not checked** — pre-fix records may carry `accepted` on soft topics |
| D-ENV-02 | `GOOGLE_MAPS_API_KEY` is dead: returns `REQUEST_DENIED "API key is invalid"`, wrong format (64 hex, not `AIza…`), and **no code reads it** | LABELLED (not deleted) | UPDATE-128; labelled in `.env` + `.env.example` so nobody assumes Google Maps works. Decide later whether to obtain a real key or drop the variable |

