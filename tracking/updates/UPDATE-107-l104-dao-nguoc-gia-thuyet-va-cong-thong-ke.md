# UPDATE-107 — `L1-04`: đo bác bỏ chính giả thuyết của tôi (Δ=0 tuyệt đối); và cổng THỐNG KÊ `D-M3-10` được nối vào `run_ladder`

Ngày: 2026-07-30 · Người điều khiển agent: Cường (`continue` sau khi `L1-04` được duyệt trong hàng đợi)
Trạng thái: `DONE-CODE`. Loại: sim (behavior-neutral, đã chứng minh bằng đo) + tooling.

## 1. Vì sao có update này

`L1-04` nằm ở vị trí #1 trong hàng đợi (`PLAN-2026-07-30-hang-doi-cong-viec.md`), được mô tả là
*"thay đổi ĐỔI HÀNH VI THẬT"* sửa một defect *"28% quyết định `shift_extend` mất hẳn"*. Theo đúng
kỷ luật đã khoá cho thay đổi đổi-hành-vi: đo baseline TRƯỚC-fix n=100 ⇒ áp fix ⇒ đo SAU-fix cùng
100 seed ⇒ diff ghép cặp có CI.

**Kết quả đo đảo ngược chính giả thuyết đưa `L1-04` vào hàng đợi.** Update này ghi lại toàn bộ diễn
biến theo đúng root-cause protocol của `CLAUDE.md` §4b — vì đây chính xác là tình huống nó viết ra
để chặn: *"metric shift không giải thích được — không sửa ngay theo phỏng đoán"*.

## 2. Files bị ảnh hưởng

| File | Gì |
| --- | --- |
| `src/gsm_sim/advice_bridge.py` | `check_shift_extend`: dời `_claim_effect` xuống **sau** clamp khả thi (`add ≤ 0.0`) |
| `tests/test_advice_time_encoding.py` | +`test_infeasible_extend_does_not_burn_claim` (đỏ → xanh) |
| `src/gsm_sim/parallel.py` | `aggregate_adherence`: gộp thêm `by_channel_archetype`, nối `adherence_stat_flags` (cổng THỐNG KÊ `D-M3-10`, chốt UPDATE-103) |
| `tests/test_adherence_gate.py` | +`test_ladder_stat_gate_wired_and_can_fire` — cổng chạy thật trong `run_ladder`, không chỉ đơn vị |
| `scripts/measure_l104.py` | **tạo** — đo TRƯỚC/SAU ghép cặp n=100, bootstrap CI |
| `specs/simulation/d-m3-01-adherence-denominator-fix.md` | 🔴 **đính chính §4** — dòng D (`L1-04`) đổi từ "ĐỔI HÀNH VI THẬT" thành "KHÔNG, đo n=100 xác nhận" + giải thích root cause đầy đủ |
| `tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` | 🔴 **đính chính mục #1** — rút lại "38/135 = 28% mất hẳn" làm động lực |
| `research/audit/2026-07-27-current-state/40-l104-{truoc,sau}-n100.json` | **tạo** — artifact per-seed ghép cặp |

## 3. Diễn biến, theo root-cause protocol

### 3.1 Reproduce

Test đỏ trước fix: `test_infeasible_extend_does_not_burn_claim` — actor `shift_end_min =
world_end_min` (bất khả thi tuyệt đối); gọi lần 1 (bất khả thi, không có gì xảy ra); nới
`world_end_min` để "thế giới trở nên khả thi"; gọi lần 2 **cùng bucket 30′**. Trước fix: lần 2 vẫn
trả `0.0` vì token đã cháy ở lần 1. `assert 0.0 > 0.0` — đỏ đúng cơ chế đã chẩn đoán.

### 3.2 Classify

Ban đầu phân loại: **BUG** (token cháy sai lúc, mất quyết định thật). *(Sẽ đảo lại ở §3.5.)*

### 3.3 Compare baseline

Baseline TRƯỚC-fix, n=100 seed tươi (4300–4399), arm `all` `coverage=all`:
`40-l104-truoc-n100.json` — 0/100 seed có adherence flag (thước đo sạch).

### 3.4 Áp fix, đo SAU-fix cùng 100 seed

`40-l104-sau-n100.json` — cũng 0/100 seed có flag. **Diff ghép cặp, bootstrap 5000, trên 11 chỉ
tiêu** (`net_mean_all`, guardrail 4 tầng ĐA-08, `others_payout_vnd`, `ext_decided`, `ext_followed`):

```
metric                  mean Δ (sau−trước)                        CI95  SIG
net_mean_all                         +0.00                [0.00, 0.00]   ns
served_rate                          +0.00                [0.00, 0.00]   ns
orders_completed                     +0.00                [0.00, 0.00]   ns
total_payout_vnd                     +0.00                [0.00, 0.00]   ns
expired_n                            +0.00                [0.00, 0.00]   ns
wait_median_min                      +0.00                [0.00, 0.00]   ns
gini_payout                          +0.00                [0.00, 0.00]   ns
station_hhi                          +0.00                [0.00, 0.00]   ns
supply_cell_hhi                      +0.00                [0.00, 0.00]   ns
ext_decided                          +0.00                [0.00, 0.00]   ns
ext_followed                         +0.00                [0.00, 0.00]   ns
```

**Δ = 0,00 [0,00, 0,00] tuyệt đối trên cả 11 chỉ tiêu**, kể cả `ext_followed` — đúng chỉ tiêu mà giả
thuyết ban đầu dự đoán sẽ tăng nếu fix đúng như chẩn đoán.

### 3.5 🔴 Instrument + prove root cause — giả thuyết ban đầu bị bác

Δ=0 tuyệt đối (không phải "ns vì yếu", mà CI hai đầu **bằng 0**, tức behavior-neutral thật) buộc
phải dừng lại hỏi *vì sao*, không phải báo "fix vô hại, ship". Instrument trực tiếp:

1. `self.world_end_min` (`advice_bridge.py:165`) là **hằng số đọc từ config một lần lúc khởi tạo
   bridge** — không đổi trong suốt một run.
2. Mọi nhánh `return 0.0` **trước** dòng `actor.shift_extended_min += add` (rate≤0, need_min quá
   lớn, cadence chặn, coin=False, add≤0) **không mutate bất kỳ state actor nào**.
3. ⇒ Trong **cùng một bucket 30′**, coin cho cùng kết quả (khoá theo bucket + `material_revision`),
   và mọi state ảnh hưởng `add` không đổi giữa các lần gọi liên tiếp ⇒ **`add` deterministic trong
   bucket**: bất khả thi ở lần đầu ⇒ bất khả thi ở **mọi lần sau trong cùng bucket**, bất kể token
   cháy hay không.
4. **Microbenchmark trực tiếp xác nhận** (không suy luận suông): actor `shift_end_min =
   world_end_min`, gọi `check_shift_extend` **15 lần liên tiếp cùng bucket** ⇒ `add = 0.0` cả 15
   lần, dù `_effect_applied` (token) **không hề cháy** ở code mới. Kết quả quan sát được giống hệt
   code cũ.

**Vậy con số 38/135 = 28% nghĩa là gì?** Đó đo **gap LOGGING**: `_claim_effect` trả `True` (claim
thành công) nhưng world.py **cũ** chỉ ghi event `advice_shift_extend` khi `add > 0` ⇒ 38 quyết định
bất khả thi có claim mà **không có event**. Đó là thiếu **dấu vết đo lường**, không phải thiếu
**tác động thật** (tác động thật — `add` — đằng nào cũng bằng 0). Gap logging đó **đã được đóng bởi
chính `D-M3-01`** (nhánh `note_spoken_outcome(reason="infeasible_world_end")`, UPDATE-102) —
**không phải bởi `L1-04`**. Tôi đã gộp hai cơ chế khác nhau thành một khi viết motivation ban đầu
cho `L1-04` trong `PLAN-2026-07-30-hang-doi-cong-viec.md`.

### 3.6 Classify lại

**KHÔNG PHẢI BUG.** `L1-04` vẫn đúng về **semantic** (`R-01`: "một quyết định = một lần **áp** tác
động" — token nên cháy khi tác động được áp, không phải khi lời khuyên chỉ được *hỏi*), và giữ lại
vì đúng, rẻ, và **đo chứng minh vô hại tuyệt đối**. Nhưng nó không sửa một bug quan sát được, và
mức ưu tiên #1 trong hàng đợi (dựa trên "defect đang gây hại 28%") là sai.

## 4. Cổng THỐNG KÊ `D-M3-10` — nối vào `run_ladder`

Cơ chế đã chốt ở UPDATE-103 §3 (Cường duyệt nguyên tắc, agent sửa cơ chế thành công thức đóng
Poisson-binomial) và thi công ở `sim_metrics.py` (commit `6c44f31`) nhưng **chưa nối vào đường ống
A/B thật** — cố ý, để không đụng module `parallel.py` trong lúc job đo `L1-04` đang chạy.

Nay nối: `aggregate_adherence` gộp thêm `by_channel_archetype` qua các seed, gọi
`adherence_stat_flags(tot_arche, DEFAULT_ADHERENCE)`, TREO khi `|z| > 4` (per-ô hoặc gộp theo kênh).
Test tích hợp `test_ladder_stat_gate_wired_and_can_fire` dựng 500 quyết định lệch 0,10 qua
`aggregate_adherence` thật (không chỉ gọi hàm đơn vị) — xác nhận nó **bắn trong đường ống thật**.

## 5. Kiểm chứng

| Cái gì | Bằng chứng |
| --- | --- |
| Test đỏ→xanh | `test_infeasible_extend_does_not_burn_claim`: đỏ trước fix, xanh sau |
| Δ hành vi | `scripts/measure_l104.py diff` — bootstrap 5000, n=100 ghép cặp, 11 chỉ tiêu, **0,00 [0,00,0,00]** tuyệt đối |
| Root cause | đọc code (`world_end_min` hằng số, không mutate trước early-return) + microbenchmark 15 lần gọi cùng bucket |
| Stat gate chạy thật | `test_ladder_stat_gate_wired_and_can_fire` qua `aggregate_adherence`, không phải test đơn vị |
| Suite | *(điền sau khi job nền xong — `uv run pytest -q` + `uv run pytest -q ui/backend/tests`, theo `D-M3-09`)* |

## 6. Adversarial self-review / flaws found

### 6.1 🔴 Tôi đưa một mục vào hàng đợi dựa trên một sự hiểu sai của chính mình

`L1-04` được xếp **#1** trong `PLAN-2026-07-30-hang-doi-cong-viec.md` với lý do *"rẻ, đã có spec, và
là defect ĐANG MỞ"* — dựa trên con số 38/135 mà tôi đọc thành *"quyết định mất hẳn"* khi nó thực ra
đo *"event không được ghi cho quyết định bất khả thi"*, một gap **khác** đã đóng bởi `D-M3-01` cùng
ngày. Đây đúng loại lỗi mà `D-M3-01`/`D-M3-10` sinh ra để chặn ở tầng đo adherence — nhưng lần này
xảy ra ở tầng **lập luận** của chính tôi khi thiết kế hàng đợi việc, không phải ở code.

**Điều làm tôi tự tin sai:** tôi có một con số đo được (38/135), một cơ chế nghe hợp lý (token cháy
trước khi biết khả thi), và một dòng code khớp với cơ chế đó — nhưng chưa bao giờ hỏi *"con số đó
có thực sự đo cái tôi nghĩ nó đo không"*, cho tới khi n=100 buộc phải hỏi.

### 6.2 Đã kiểm, không phát hiện vấn đề

- `note_spoken_outcome` (nhánh `infeasible_world_end`, `D-M3-01`) vẫn hoạt động đúng — không bị đụng
  bởi thay đổi thứ tự claim/clamp lần này (đứng trước cả claim và clamp trong luồng mới).
- `R-01` (một quyết định = một lần áp tác động) **giữ nguyên nghĩa** — chỉ đổi *khi nào* được coi là
  "đã áp".
- `aggregate_adherence` cũ (trước khi thêm stat gate) không bị phá — test cũ (`test_pair_result_
  carries_both_arms`, `test_ladder_artifact_carries_verdict`) vẫn xanh.

### 6.3 Chưa làm, và vì sao

- **Chưa đo lại `L1-04` ở nhiều bộ seed khác** — Δ=0 tuyệt đối trên 100 seed đã đủ để kết luận
  behavior-neutral (không phải "chưa đủ mạnh để thấy hiệu ứng nhỏ" — CI hai đầu bằng 0 chính xác).
  Không cần seed thêm cho một kết luận null tuyệt đối.
- **Cổng thống kê chưa được thử trên artifact THẬT có lệch thật** (mọi test dùng dữ liệu dựng tay).
  Lần đầu nó chạy trên dữ liệu thật là chính lần đo `L1-04` này — và nó cho `verdict: OK` đúng như
  kỳ vọng (không có lệch thật trong dữ liệu mock hiện tại).

## 6b. 🔍 LƯỢT RÀ ĐỐI KHÁNG theo lệnh Cường (*"kiểm tra lại toàn bộ code và thử nghiệm trong đợt này, tìm ra flaw, sửa lại"*)

Rà 6 nghi vấn có chủ đích trên toàn bộ code + thử nghiệm của đợt (D-M3-01/10, cổng thống kê, L1-04,
doc-graph, các script đo). Kết quả: **4 flaw thật (đã sửa) · 1 không phải flaw · 1 ghi nhận**.

| # | Nghi vấn | Kết quả |
| --- | --- | --- |
| 1 | Drain outcome có mất event cuối ngày? | ✅ **KHÔNG phải flaw** — drain nằm cùng tick với cả hai chỗ sinh outcome, chạy **trước** nhánh `END_SHIFT` break |
| 2 | Cờ `--fingerprint` trong `probe_adherence_truth.py` | 🔴 **FLAW — SỬA**: arg khai báo mà **không có handler** (họ `D-R12` "code tự quảng cáo tính năng không chạy"; bằng chứng: chạy `--fingerprint` vẫn in probe thường). Nay có handler thật, xác nhận chạy, hash khớp mọi bản đo trước (`e5561414ce8e748b`) |
| 3 | Cổng thống kê dùng `DEFAULT_ADHERENCE` **cứng** | 🔴 **FLAW — SỬA**: bridge merge `advice.adherence_by_archetype` từ config (`advice_bridge.py:148`), và config pilot **ĐANG CÓ** khoá đó (dòng 400) — hai nguồn sự thật, hôm nay **tình cờ trùng giá trị**. Khoá đó tồn tại để được đổi (quét độ nhạy, calibrate E10); khi đổi, cổng so với null **cũ** ⇒ bắn oan hàng loạt ⇒ bị tắt (mẫu `D-R20`). Sửa: `nominal_adherence(cfg)` mới, `run_ladder` truyền nominal của **run**; +2 test (một test đỏ-được nếu ai hardcode lại) |
| 4 | `DEFERRED_PREFIXES` trong `build_doc_graph.py` | 🔴 **FLAW (nhỏ) — SỬA**: hằng khai báo kèm comment hứa hành vi *"không tính docs cũ là mồ côi"* nhưng **không được dùng** — xoá + sửa comment khớp hành vi thật |
| 5 | **Edge case của chính cổng BẤT KHẢ** (tự soi thêm, ngoài danh sách) | 🔴 **FLAW NẶNG NHẤT — SỬA**: cổng coi adherence=1,0 là bất khả **vô điều kiện**. Với arm **tuân-thủ-tuyệt-đối** (`adherence_by_archetype: 1.0` — chính khái niệm *"so thế giới không advisor vs HOÀN TOÀN tuân thủ"* Cường từng nêu), adherence 1,0 là **ĐÚNG** ⇒ cổng TREO oan mọi kênh mọi seed ⇒ arm hợp lệ nhất bị chặn vĩnh viễn ⇒ cổng bị tắt. Sửa: `adherence_audit` tính bounds nominal per-kênh từ config của run, `adherence_flags` chỉ coi 1,0 bất khả khi `max_p < 1.0` (và 0,0 khi `min_p > 0.0`); +2 test: arm 1.0 chạy sim thật **không** TREO, còn caller không bounds giữ nguyên hành vi cũ. **20/20 test file xanh** |
| 6 | `measure_l104.py` thiếu `others_payout_vnd` so acceptance PLAN mục 1 | ⚠ **GHI NHẬN, không sửa**: `coverage=all` không có actor đích nên "others" không có nghĩa; `total_payout_vnd` phủ thay. Không đổi kết luận — Δ=0 tuyệt đối trên mọi metric đã đo |

Tính chất chung của flaw #2 và #5: **cổng đúng với config hôm nay, sai âm thầm khi config đổi** —
null của một phép kiểm phải là **tham số của chính run được kiểm**, không phải hằng số của người
viết cổng. Cả hai chỗ nay đọc từ `result.config`/`cfg` của run.

Behavior-neutral của cả lượt rà: các sửa chỉ chạm tầng ĐO (`sim_metrics`, `parallel` aggregate,
script, doc-graph) — fingerprint per-actor seed 1000 khớp mọi bản đo trước.

### 6c. 🔴 Flaw #6 — SUITE bắt, KHÔNG phải lượt rà của tôi: event MA sau `L1-04`

Full suite đỏ 1 test (`test_decision_level_matches_ground_truth`: decided **101** vs event **104**
— **3 event MA**). Root cause: quyết định **đã ÁP** làm `shift_end_min` chạm `world_end_min` ⇒ các
lần hỏi lại cùng bucket rơi vào nhánh `add ≤ 0` (mới đứng TRƯỚC claim sau `L1-04`) ⇒ sinh outcome
`infeasible` cho quyết định **đã áp xong**. Trước `L1-04`, `_claim_effect` chặn trước nên im.

**Hai điều phải nói thẳng:**

1. **Khẳng định "behavior-neutral" của §3.4 phải thu hẹp**: `L1-04` neutral về **HÀNH VI**
   (Δ=0 [0,0] n=100 — đúng và giữ nguyên) nhưng **KHÔNG neutral về EVENT LOG**. Phép đo n=100
   **mù** với lỗi này vì cả 11 chỉ tiêu đều là decision-level/hành vi; lỗi nằm ở tầng event.
   Suite bắt được vì có test pin **event-count vs decision-count** — đúng loại cổng hai-đơn-vị
   mà cycle này dựng lên, bắt lại chính người dựng nó.
2. **Lượt rà đối kháng §6b của tôi CŨNG miss** — tôi rà 6 nghi vấn nhưng không nghĩ tới ca
   "hỏi lại sau khi đã áp trong cùng bucket". Người bắt là **bộ test**, không phải người rà.

**Fix:** `mark_outcome_logged()` — khi quyết định được áp thành công (world sẽ log event thật),
đánh dấu outcome-key để các lần hỏi lại cùng bucket không sinh event MA. Regression test mới
`test_applied_decision_does_not_spawn_ghost_infeasible_event` pin đúng tầng event; test suite cũ
(101==104) nay xanh. 50/50 các file liên quan xanh.

## 7. Docs đã cập nhật kèm theo

`specs/simulation/d-m3-01-adherence-denominator-fix.md` §4 (đính chính) ·
`tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` mục #1 (đính chính) · `tracking/DEFERRED.md`,
`tracking/PROJECT-GRAPH.md` (node UPDATE-107, follow-up dưới).

## 8. Follow-up

| Việc | Ưu tiên |
| --- | --- |
| Nối cổng thống kê vào `scripts/run_parallel.py` (hiện chỉ `run_ladder`) | TB |
| Không còn lý do chặn để đo `E10` (mục #3 hàng đợi) — `L1-04` không phải tiên quyết nữa | — |

## 9. Visual status

**`NOT_APPLICABLE`** — behavior-neutral chứng minh bằng đo (Δ=0 tuyệt đối n=100); không đổi
dynamics/output/metric nào của sim đang chạy trong sản phẩm (`shift_extend` vẫn tắt theo ĐA-07).

## 10. ⏳ NHẮC LẠI PENDING-REVIEW (lệ CLAUDE.md §3.1 — hoãn ≠ waive)

**17 mục** chờ Cường: **V-01…V-14** · **V-16** (fare parity) · **V-17** (kênh VỊ TRÍ — kênh duy nhất
đang bật) · **V-18** (nhịp nói). Cộng mục ❓/⛔ trong `tracking/PENDING-REVIEW.md`.
