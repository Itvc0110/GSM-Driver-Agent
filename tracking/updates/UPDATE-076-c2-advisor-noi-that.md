# UPDATE-076 — C2 đợt 1: advisor phải nói thật (S1 `already_maxed` · S5 khoán tuần · seed provenance)

- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** fix (correctness, driver-visible)
- **TODO / User story liên quan:** C2 "một nguồn luật UI↔sim" (ĐA-05 đã duyệt); hồ sơ
  `research/audit/2026-07-27-current-state/08-parity-sim-vs-ui.md` §1b + §1c + §5.2

## Tóm tắt

Ba lỗi làm advisor **nói sai về chính nó**: (1) tài xế đã đủ điểm mốc cao nhất nhưng tỷ lệ dưới
ngưỡng — chính sách sẽ trả **0đ** — được advisor **trấn an** hoặc **im lặng**; (2) khoán tuần
**không thể đạt** vẫn được nói *"còn thiếu Xđ để đạt khoán"* kèm doạ truy thu; (3) response advice
khai `seed: 0` trong khi dataset là `seed_base = 7000`.

Mẫu chung của (1) và (2): **solver đã kết luận đúng, consumer không đọc `feasible`.** (2) tìm được
nhờ **quét theo mẫu lỗi** sau khi sửa (1) — không dừng ở ca đầu tiên.

## Chi tiết cập nhật

### 1b. 🔴🔴🔴 `already_maxed` che mất `feasible` — mất tiền thật, trong im lặng

> Đánh số §1b/§1c/§1d ở đây **cố ý khớp với hồ sơ `08-parity-sim-vs-ui.md`** để tra chéo được;
> không phải lỗi đánh số.

AUDIT A1 (UPDATE-065) đã sửa **solver** cho trung thực: kịch mốc + tỷ lệ dưới ngưỡng ⇒
`feasible: False` + `infeasible_reason` + caveat, **có test**. Nhưng **cả ba consumer** rẽ nhánh
`already_maxed` **TRƯỚC** khi đọc `feasible`, nên sự trung thực đó không bao giờ tới tài xế:

| Nơi | Trước | Sau |
|---|---|---|
| `gsm_core/advisor/templates.py:186` | *"đã đạt mốc thưởng cao nhất hôm nay."* | tách 2 nhánh: an toàn → trấn an; nguy cơ → **nói rõ nghẽn ở tỷ lệ NHẬN hay HOÀN THÀNH** |
| `gsm_sim/advice_bridge.py:453` | `return False, "already_maxed"` (im lặng) | chỉ im khi `already_maxed **AND** feasible`; còn lại rơi xuống `_acceptance_recoverable` quyết định có kịp gỡ không |
| `ui/backend/app/adapters/advisor.py:132` | silent card *"không có gì cần chỉnh. Giữ nhịp hiện tại."* | card cảnh báo `kind=info`, `reason_code=acceptance_below_threshold`/`completion_below_threshold` |

Kèm theo, **solver phải trả `constraints` ở nhánh `already_maxed`** (trước đây không có), vì
consumer đọc `sol["constraints"]` để biết nghẽn ở đâu — không có nó thì dù sửa thứ tự nhánh,
consumer vẫn không nói được điều duy nhất còn cứu được.

**Kịch bản hại**: 210 điểm (kịch mốc 200), `acceptance = 0.80 < 0.85`. Chính sách trả **0đ**.
Solver biết. Advisor nói *"không có gì cần chỉnh"*.

**Cùng dạng lỗi với cước 24.000/km** (UPDATE-075): bản sửa nằm một tầng, consumer không ai biết.
Khác ở chỗ nó **không hiện số sai — nó GIẤU cảnh báo**, nên không nhìn thấy được.

Card cảnh báo **không kèm số tiền thưởng**: chính mức thưởng đó đang có nguy cơ không được trả,
hiện nó ra sẽ thành lời hứa. `numbers: []` và câu chữ không chứa số ⇒ qua verifier V1 sạch.

### 1c. Cùng mẫu lỗi, tìm thêm được một ca ở S5 `weekly_khoan` — đã sửa luôn

Sau khi sửa §1b, tôi **quét theo MẪU LỖI** ("consumer rẽ nhánh theo cờ trạng thái mà không đọc cờ
đúng-sai") thay vì coi như đã xong. Ra ngay một ca nữa:

- `solvers/weekly_khoan.py:91` tính `feasible = gap == 0 or (enough_hours and days_ok)`.
- `advisor/templates.py:48 _khoan_sentence` là **consumer DUY NHẤT** — đọc `quota_available`,
  `gap_revenue_vnd`, `clawback_risk_vnd`, **không bao giờ đọc `feasible`**.

Câu thật sự sinh ra khi khoán **không thể đạt** (test in ra nguyên văn):

> *" Tuần này còn thiếu 1.200.000đ doanh số để đạt khoán. Nếu không đạt, phần chưa đạt có thể bị
> truy thu khoảng 240.000đ."*

Vừa **ngụ ý mục tiêu với tới được**, vừa **treo doạ truy thu** — đẩy tài xế đuổi theo thứ solver đã
biết là bất khả thi. Sau sửa: nói thẳng *"khó đạt vì quỹ giờ còn lại trong tuần không đủ"*, giữ
thông tin truy thu, và kết bằng câu không ép.

**Chua nhất**: docstring của `_gap_sentence` ngay bên dưới (AUDIT A3 LAYEROUT-2, UPDATE-070) ghi
đúng nguyên tắc — *"câu 'còn thiếu X để đạt mốc Y' CHỈ được nói khi solver bảo KHẢ THI"* — nhưng
bản sửa đó **chỉ áp cho S1**, không áp cho S5 dù câu chữ cùng dạng, cùng file, cách nhau 130 dòng.

**Phạm vi hẹp hơn §1b, nói rõ:** `weekly_khoan` chỉ chạy trong pipeline C6, **không** nằm trên
đường `adapters/advisor.py` mà app tài xế đang dùng. Nhưng S5 thuộc scope F1/F3 nên khi khoán tuần
lên card thì nó thành driver-visible ⇒ sửa trước, không lặp lại vết xe cũ.

### 1d. Quét CẠN mẫu lỗi — kết luận có biên, để không ai audit lại

Sau khi có 2 ca, tôi quét **toàn bộ** solver emit `feasible` và đối chiếu với consumer:

| Solver | Có `feasible` | Consumer đọc? | Kết luận |
|---|---|---|---|
| `bonus_feasibility` (S1) | ✅ | **trước: KHÔNG** ở nhánh `already_maxed` | 🔴 defect — **đã sửa** (§1b) |
| `weekly_khoan` (S5) | ✅ | **trước: KHÔNG** | 🔴 defect — **đã sửa** (§1c) |
| `idle_reduction` | ✅ | không, nhưng đọc `notable` | ✅ **không phải defect**: `feasible` luôn 1:1 với `notable` (cùng False/cùng True) — trường thừa cùng nghĩa |
| `mission_knapsack` | ✅ | không, nhưng đọc `chosen_missions` | ✅ **không phải defect**: `feasible = bool(chosen)` — cùng nghĩa với thứ consumer đã kiểm |

⇒ **Mẫu lỗi này đã quét cạn: đúng 2 ca, cả 2 đã sửa.** Ghi rõ ở đây để lần sau không phải audit
lại từ đầu. Đề xuất dọn: `idle_reduction`/`mission_knapsack` nên **bỏ** trường `feasible` thừa —
hai tên cho một sự thật chính là thứ sinh ra §1b/§1c ngay từ đầu. Chưa làm (ngoài scope đợt này).

### 2. `seed: 0` — response tự mâu thuẫn về nguồn gốc của mình

`ui/backend/app/adapters/advisor.py` khai cứng `seed: 0` (2 chỗ, gồm cả đường im lặng), trong khi
`mockdata.py` đọc `manifest()["seed_base"] = 7000`. Cùng một dataset, hai định danh. Thêm
`_dataset_seed()` đọc **cùng nguồn** với các envelope khác. Đây là mảnh đầu tiên của
`SourceEnvelope` (C2 §5.2).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/solvers/bonus_feasibility.py` | sửa | nhánh `already_maxed` trả thêm `constraints` |
| `src/gsm_core/advisor/templates.py` | sửa | `_gap_sentence`: `already_maxed` không còn là nhánh sớm · `_khoan_sentence`: đọc `feasible` (S5) |
| `src/gsm_sim/advice_bridge.py` | sửa | chỉ suppress khi `already_maxed AND feasible` |
| `ui/backend/app/adapters/advisor.py` | sửa | card cảnh báo thay silent; `_dataset_seed()` |
| `tests/test_already_maxed_at_risk.py` | **tạo** | 7 test mức **consumer** (4 đỏ trước khi sửa: 3 của S1 + 1 của S5) |
| `ui/backend/tests/test_contracts.py` | sửa | +3 test: card cảnh báo, đối chứng im lặng đúng, seed provenance |
| `research/.../08-parity-sim-vs-ui.md` | sửa | thêm §1b (S1) + §1c (S5); đánh dấu cước ✅ xong |
| `tracking/TODO.md` | sửa | T-042 (7 việc C2, đánh dấu xong 0/1/2) + T-043 |
| `tracking/PENDING-REVIEW.md` | sửa | V-13 (visual gate của UPDATE này) |
| `research/00_SUMMARY.md` | sửa | mục 17–20: kết quả đo 2026-07-27 |
| `specs/advisor-objective-model-v2.md` | sửa | sửa lỗi đánh số §6 (C1 vs C2) + ghi xung đột với quyết định "không bịa số" cũ |

## Docs đã cập nhật kèm theo

Hồ sơ 08 (§1b/§1c) ✅ · TODO (T-042, T-043) ✅ · PENDING-REVIEW (V-13) ✅ · `research/00_SUMMARY.md` (mục 17–20) ✅ · spec objective v2 (sửa đánh số + ghi xung đột) ✅.
SCOPE/USER_STORIES/DEFERRED: **không đổi** — không thêm/bớt tính năng, chỉ sửa cho đúng.

## Assumptions và evidence

| Claim | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Kịch mốc + tỷ lệ dưới ngưỡng ⇒ thưởng = 0 | **OBSERVED-CODE** | `gsm_sim/policy.py:94 day_bonus()` gate; `bonus_feasibility` §S1-1 | cao | nếu policy thật không gate thì cảnh báo là thừa (nhưng vẫn không gây hại) |
| Cả 3 consumer đều rẽ nhánh sớm | **OBSERVED-CODE** | grep `already_maxed` toàn repo; 3 test đỏ trước sửa | cao | — |
| `_khoan_sentence` là consumer DUY NHẤT của S5 | **OBSERVED-CODE** | grep `weekly_khoan` toàn repo (chỉ router/features/templates) | cao | nếu có consumer khác thì còn chỗ chưa sửa |
| Ngưỡng 0.85/0.85 | **MOCK** | `configs/pilot_dongda.yaml` / policy bundle mock | trung bình | số ngưỡng thật chờ GSM (D-POL-05) |
| `seed_base = 7000` | **OBSERVED-DATA** | `data/mock/realdata-v1/manifest.json` | cao | — |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Kết quả | Chưa kiểm chứng |
| --- | --- | --- | --- |
| `pytest tests/test_already_maxed_at_risk.py` (S1) | 1000 | **3 failed → 5 passed** sau fix | — |
| `pytest -k khoan` (S5) | — | **1 failed → 2 passed** sau fix; test in ra nguyên văn câu hại | — |
| `pytest tests/test_already_maxed_at_risk.py tests/test_composer_verifier.py` | 1000 | **25 passed** | — |
| `pytest tests/test_bonus_feasibility.py test_composer_verifier.py test_advice_bridge.py test_already_maxed_at_risk.py` | 1000 | **66 passed** | — |
| `pytest tests` (ui/backend) | — | **31 passed** (28 → +3) | — |
| `pytest tests` (root, full) | mọi | **548 passed, 4 skipped** (14:26) | — |
| **Kiểm baseline không lệch** | 1000, 1001 | **KHỚP tuyệt đối** với `09-baseline30.json` | chỉ 2/30 seed |

**Baseline có bị fix bridge làm lệch không?** Đã **kiểm chứ không giả định**: chạy lại seed
1000/1001 ở `coverage: all` → `d_served_rate`/`d_expired`/`d_total_payout` **trùng khít** số đã ghi
trong UPDATE-075. Lý do: `_advice_would_help` chỉ phục vụ kênh `accept_lift`, mà kênh đó **tắt**
trong config mặc định. ⇒ **Số nền 30 seed của UPDATE-075 vẫn có hiệu lực.**

**Full suite:** **548 passed / 4 skipped** trên code CUỐI (541 của UPDATE-075 → +5 test S1
consumer → **546** ở lần chạy trung gian, không hồi quy → +2 test S5 → **548**). Hai lần chạy đều
đọc output trước khi ghi số; **không tuyên bố xanh trước**.

## Visual verification

- **Status:** `BLOCKED` — **không dựng được kịch bản thật từ snapshot hiện tại** (đã quét, có số).
- **Vì sao KHÔNG phải NOT_APPLICABLE:** thay đổi này **đổi cái tài xế nhìn thấy** — một trạng thái
  trước đây im lặng nay hiện card cảnh báo. Đúng diện phải qua visual gate theo CLAUDE §4b.
- **Cách launch:** `uv run uvicorn app.main:app --app-dir ui/backend --port 8010` →
  `http://localhost:8010/app/`
- **Đã quét toàn bộ snapshot 90 ngày (12.805 driver-day)** tìm ca thật:

  | Số đo | Giá trị |
  |---|---|
  | ca **kịch mốc cao nhất** (≥200 điểm) | **86** |
  | trong đó tỷ lệ dưới ngưỡng ⇒ trạng thái cần demo | **0** |
  | acceptance **thấp nhất** trong 86 ca kịch mốc | **0,857** (ngưỡng 0,850) |
  | điểm **cao nhất** trong nhóm acceptance < 0,85 | **190** (mốc 200) |
  | driver-day có acceptance < 0,85 nói chung | 3.486 / 12.805 = **27,2%** |
  | tương quan points ~ acceptance | **0,227** (yếu) |

  ⇒ Trạng thái này **hụt đúng một sợi tóc**: 190 vs 200 điểm và 0,857 vs 0,850. Không phải bất khả
  thi về mặt cấu trúc (tương quan chỉ 0,23) — chỉ là biên hẹp trong đúng bộ số MOCK này. **Với số
  policy THẬT của GSM (D-POL-05) thì mốc/ngưỡng đổi và trạng thái này có thể thành phổ biến.**
  Vì vậy fix là **phòng thủ đúng chỗ**, không phải sửa lỗi giả tưởng.
- **Người review + verdict:** chưa có. Đề nghị Cường chọn: (a) chấp nhận bằng chứng test + số quét
  trên, hoặc (b) yêu cầu dựng một fixture demo có nhãn MOCK rõ để xem tận mắt.

## Adversarial self-review / flaws found

0. **Điểm chưa hoàn hảo, tự nêu:** `_khoan_sentence` dùng `not sol.get("feasible", True)`, nên
   `feasible = None` (nghĩa "**chưa biết**", solver trả ở nhánh thiếu số khoán) sẽ bị coi là
   *không khả thi*. **Hôm nay không tới được** — nhánh đó đã return sớm ở `quota_available=False`.
   Ngữ nghĩa chặt hơn là `sol.get("feasible") is False` (chỉ nói "khó đạt" khi solver **kết luận
   tường minh**). Chưa đổi vì đường đó bất khả đạt và đổi thì phải chạy lại full suite 15 phút cho
   một khác biệt không quan sát được. **Ghi ra để không ai tưởng là đã cân nhắc rồi bỏ qua.**
1. **Test có thật sự bắt được bug không?** Có — chạy trước khi sửa: **3 failed** đúng 3 consumer,
   2 test đối chứng (trường hợp an toàn) **xanh ngay từ đầu** ⇒ test không phải loại "luôn đỏ".
2. **Test mức solver đã tồn tại và vẫn xanh trong lúc cả 3 consumer sai** — đó chính là lý do bug
   sống sót qua AUDIT A1. Bài học: **fix ở tầng producer phải có test ở tầng consumer**.
3. **Bản nháp test #3 ban đầu là source-inspection** (`assert "feasible" in source`) — loại test
   yếu, sẽ xanh giả nếu chữ "feasible" xuất hiện vì lý do khác. **Đã thay bằng test hành vi**
   (dựng actor thật + monkeypatch solver + gọi `_advice_would_help`).
4. **Card mới có lọt số trần không?** Không: `numbers: []` và câu chữ không chứa chữ số; test chạy
   đúng `check_bare_numbers` + `check_blocklist` như mọi card.
5. **Có làm advisor nói nhiều hơn mức cần?** Test đối chứng `test_maxed_and_safe_stays_silent`
   ràng buộc: kịch mốc + tỷ lệ đủ ⇒ **vẫn im lặng**. Không đánh đổi im-lặng-đúng lấy cảnh báo thừa.
6. **Fall-through của bridge có compose đúng không?** Đã đọc lại toàn hàm: khi
   `already_maxed AND NOT feasible`, luồng rơi xuống nhánh `blocked_elsewhere` — nếu nghẽn ở quỹ
   GIỜ hoặc tỷ lệ HOÀN THÀNH thì **vẫn im lặng** (đúng: kênh `accept_lift` không sửa được hai thứ
   đó); chỉ khi nghẽn ở **tỷ lệ NHẬN** mới đi tiếp tới `_acceptance_recoverable`. Chuỗi lý lẽ cũ
   không bị phá. Đã đối chiếu chuỗi `infeasible_reason` thật của solver ("tỷ lệ nhận …" /
   "tỷ lệ hoàn thành …") khớp với điều kiện `in reason`.
   **Điểm yếu của test**: dùng monkeypatch solver để cô lập nhánh. Test end-to-end với solver
   THẬT (dựng actor 210 điểm + acceptance thấp) sẽ mạnh hơn — ghi làm việc cần làm, chưa làm.
7. **Rủi ro còn lại**: `advice_bridge` nay rơi xuống `_acceptance_recoverable` ở trạng thái mới —
   nếu kênh `accept_lift` được bật lại trong tương lai, số advice sẽ tăng. **Chưa đo** tác động đó
   ở 30 seed vì kênh đang tắt theo quyết định của Cường. Ghi vào follow-up.
8. **Bug KHÔNG tái hiện được bằng data mock hiện tại** (0/86 ca kịch mốc có tỷ lệ dưới ngưỡng —
   xem bảng quét ở §Visual). Đây là phát hiện phải nói thẳng: fix **đúng về code** nhưng **chưa
   chứng minh được tác hại trên data thật đang có**. Không vì thế mà bỏ fix — biên chỉ cách nhau
   10 điểm và 0,007 tỷ lệ, và số policy thật (D-POL-05) sẽ dịch biên đó.
9. **Giả thuyết đầu tiên của tôi về nguyên nhân là SAI — đã điều tra và tự bác bỏ.**
   Nghi ban đầu: *"generator ràng buộc ngầm points với acceptance"* (vì tương quan chỉ 0,227 mà
   biên lại khít). **Điều tra cho thấy không phải**: `corr(n_trips, offers) = 0,967` — số cuốc gần
   như hoàn toàn do **số đơn được chào** quyết định. Đạt 200 điểm cần **~29 cuốc**, trong khi
   offers/ngày median 15 · p95 27 · **max 37**. Nhận dưới 85% thì cần ≥35 offers, nằm ở đuôi cực
   hạn ⇒ đây là **trần số học**, không phải ràng buộc nhân tạo.
   Kết luận đổi hẳn hướng: không phải "mock có lỗi" mà là **"mốc 200 điểm gần như không với tới
   được"** — chỉ **0,67%** driver-day chạm tới. Đó là câu hỏi **calibration policy**, ghi vào
   **T-043**. Giữ lại cả giả thuyết sai ở đây để không ai đi lại đường cũ.

## Expansion checkpoint (T-039)

1. **Schema**: không cần đổi. `SolverReport.solution.constraints` nay xuất hiện ở cả hai nhánh —
   nên cân nhắc đưa `constraints` thành trường **bắt buộc** của schema để không nhánh nào quên nữa.
2. **Bài toán tối ưu**: lộ ra bài toán chưa ai giải — *"tỷ lệ nhận luỹ kế còn gỡ kịp không, và gỡ
   bằng cách nào rẻ nhất"*. `_acceptance_recoverable` mới trả lời có/không, chưa trả lời chi phí.
3. **Tính năng**: cảnh báo "thưởng đang có nguy cơ mất" là ứng viên tốt cho **proactive card** của
   F0 (ĐA-06) — đúng loại nhắc có giá trị, không phải nhắc cho có.

## Follow-up / defer phát sinh

- **C2 còn lại**: rò tương lai `acceptance_rate` (advisor.py §build_gi — dùng aggregate CẢ NGÀY ở
  9h sáng) · payout project từ ledger 4 nguồn · `bonus_at` vs `day_bonus` · `cards.js:120-122` tự
  ghép chuỗi tiền ngoài verifier.
- **Rò tương lai tách thành cycle riêng**: dữ liệu ĐÃ ĐỦ để làm đúng (`accepted_count` +
  `total_request_calculate_accept` có trong `driver_statistic_daily`) ⇒ implement được ĐA-01
  (shrinkage `(k + m·p0)/(n + m)`, prior pooled ngày TRƯỚC). Việc này **đổi nội dung advice** ⇒
  phải có visual gate riêng, không gộp vào đợt này.
- **Chưa đo**: tác động của thay đổi `advice_bridge` khi `accept_lift` được bật lại.
- **MỚI — `T-043` (đã điều tra xong nguyên nhân, còn chờ Cường/GSM quyết)**: mốc thưởng cao nhất
  (200 điểm) chỉ được chạm ở **0,67%** driver-day, vì cần ~29 cuốc trong khi offers/ngày max 37.
  **Không phải lỗi generator** (xem §Adversarial #9). Câu hỏi thật: mốc đó có hợp lý không, và số
  policy THẬT (D-POL-05) có làm đổi kết luận không. Severity: trung bình — không sai số nào hiện
  có, nhưng làm hẹp không gian trạng thái dùng để nghiệm thu advice.

---
**⏳ PENDING-REVIEW (nhắc lại):**
- **Visual:** V-01..V-09 · V-10 (app + cards + khu Mô phỏng) · V-11 · V-12 · **MỚI: visual gate của
  chính UPDATE này đang `BLOCKED`** (cần ca thật trong snapshot).
- **Chờ chốt:** Q-03 (corpus Khánh) · Q-04 (UX proposal — không nằm trong "duyệt hết").
- **Đã duyệt, chờ implement:** ĐA-01 (làm tiếp ở cycle rò-tương-lai) · ĐA-02/03 · ĐA-04 (C3) ·
  ĐA-05 · ĐA-07 · ĐA-09.
- **⚠ ĐA-06 (polish): Cường yêu cầu NHẮC DUYỆT LẠI trước khi implement — nhắc lần 2.**
- **Blocker:** B-02 / ARCH-VERSION (registry một-schema) — trước migration ĐA-05/06.
- **Chưa commit gì** trong toàn phiên (kể cả fix MUT10) — chờ Cường yêu cầu.
