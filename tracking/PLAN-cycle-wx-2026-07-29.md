# Plan — (A) đóng Cycle W · (B) chi phí C1 do POLICY quyết định, **thước đo đi TRƯỚC**

> **Bản trong repo — Cường ĐÃ DUYỆT 2026-07-29** (bản gốc ở plan file phiên làm việc).
> Trạng thái thực thi: **Phần A HOÀN TẤT** (kèm batch 2 review 20 finding, sửa hết —
> xem `research/audit/2026-07-29-cycle-w-review/findings.md`); **Phần B CHƯA bắt đầu**.

## Context — vì sao plan này tồn tại

Cycle W (ĐA-05 lifecycle store) **PAUSE ở trạng thái dở**: review đối kháng 2 lăng kính trả
**16 finding có reproduce thật** (`research/audit/2026-07-29-cycle-w-review/findings.md`),
13/16 đã sửa và push (`66268cc`). Cường chốt phần còn lại phải qua plan mode.

Nghiêm trọng nhất đã sửa: `adherence_view` báo **0%/2%/100%** trong khi sự thật
**53,6%/52,2%/48,8%** — thước đo sai trình bày như sự thật, cùng họ BUG-EVAL-ARGMAX.

**Verdict Cường phiên này:** adherence báo **CẢ HAI, tách tên** (`decision_adherence` +
`event_adherence`), không bao giờ gọi trống là "adherence". Hướng tiếp theo Cường giao tôi quyết.

## ⚠ Bản plan trước của tôi CÓ LỖI — khảo sát đã bác bỏ

Bản trước định: thêm chi phí C1 vào solver rồi **đo bằng chỉ tiêu ĐA-08 (`payout_mean_all`)**.
Khảo sát chứng minh điều đó vô nghĩa:

- `parallel.py:119-122` — estimator ĐA-08 chỉ đọc `a.payout_vnd`;
- `entities.py:63-65` + `world.py:350-352` — chi phí sống ở sổ RIÊNG `actor.cost_vnd`;
- `sim_metrics.py`/`metrics.py` — grep `cost`: **0 match**. Sổ chi phí là **sổ chết**;
- `tests/test_cost_ledger.py:77-78` **chốt cứng** cost không được chạm payout (đúng §5).

⇒ Solver trừ chi phí sẽ **hy sinh payout để tiết kiệm khoản mà thước không thấy** ⇒ trông
TỆ HƠN. Đúng bẫy spec v2 §5b: *"sửa solver trước khi sửa thước = tối ưu hoá vào thước hỏng"*.
**Sửa thứ tự: thước đo TRƯỚC.**

---

# PHẦN A — đóng Cycle W (làm trước, không mở scope)

## A1. Bốn việc còn lại

| # | Sửa gì | File |
|---|---|---|
| F-6 | `count_episodes` lọc `origin == "pipeline"` (đang đếm mọi origin ⇒ thổi phồng 12→17 khi UI/sim ghi chung) | `advisor/episode_store.py` |
| W-6 | Recorder ghi `passed=True` cho request **chưa chạy verify** (`or {...}` ở `pipeline.py:209`); reset của Cycle W biến lỗi hiếm thành hệ thống ở nhánh R5. Giữ `None` ≠ `False` | `advisor/pipeline.py` |
| W-4b | Regex `occurred_at`: giờ `([01]\d|2[0-3])` thay `\d{2}` — `T24:00:00` lọt schema nhưng giết `fromisoformat` | `schemas/advisor/advice_lifecycle_event.schema.json` |
| W-7 | `AdvisorPipeline.close()` + context manager uỷ quyền `store.close()` (12/13 call site đi qua lớp này) | `advisor/pipeline.py` |

## A2. Adherence hai tên (verdict Cường)

Mỗi khoá `(run_id, driver_id, topic)` trả:
`{decided, followed, dismissed, suppressed, event_decided, event_followed,
decision_adherence, event_adherence}` — **không bao giờ có khoá tên `adherence`**.
Test canh: `assert "adherence" not in row` + so **cả hai** với ground truth
(accept_lift phải ra đúng **76,9%** và **53,6%**).

## A3. Verify (chưa cái nào chạy sau 13 fix)

1. Move `research/audit/.../test_review_fixes.py.pending` → `tests/test_lifecycle_review_fixes.py`.
2. **Fingerprint bit-identical chạy lại** (`run_once` 5 seed × 2 arm + `run_multiday` 3 ngày):
   `summarize` VÀ `kinds` đều phải IDENTICAL. Lệch ⇒ dừng, điều tra (đã thêm
   `assigned_ids`/`decision_ids`, đổi `derive_run_id`, đổi `infer_schema_length`).
3. Mutation mới: bỏ lọc origin ⇒ đỏ · recorder trả `True` khi rỗng ⇒ đỏ · nới regex ⇒ đỏ.
4. **Full suite** (baseline 653/5).
5. Batch 2 review đối kháng — 2 lăng kính còn lại (INPUT THÙ ĐỊCH · KỶ LUẬT schema/docs/T-046),
   2 agent theo quota guard §3.5.
6. Gỡ banner "ĐANG DỞ" ở UPDATE-091, cập nhật `findings.md` + PENDING-REVIEW.

---

# PHẦN B — chi phí C1 do policy quyết định, **ba bước, thước đo đi trước**

## B0. Sự thật khảo sát (mọi claim có file:line trong báo cáo agent)

- **Solver có ĐÚNG 2 số hạng cộng, 0 số hạng trừ**: ONLINE `eo·p_accept·ppo` (`shift_dp.py:181,190`)
  + bonus terminal (`:168,214`); SWAP và REST đều cộng `0.0` (`:204,:209`).
- **Solver mù thời gian**: grep `as_of` toàn `src/` = 3 dòng, tất cả trong `policy.py:58-67`.
  `shift_dp.solve` và `capacity_alloc.solve` không nhận ngày.
- **`is_valid_at` có đúng 1 call site** (`advice_bridge.py:158`) và **chỉ để LOG**
  (`world.py:99-103`). Config pilot không khai `meta.policy_effective_from/to` ⇒ luôn `None`.
- **Policy bundle không có chỗ cho chi phí**: `policy.py:13-35` chỉ doanh thu;
  `schemas/l0/policy_bundle.schema.json` có `additionalProperties: false` (:208).
  Chi phí nằm ở `configs/pilot_dongda.yaml:268-269` (`swap_fee_vnd: 0`,
  `cash_cost_vnd_per_km: 0`) — **không có** `effective_from/to`, `source_url`, `confidence`, `cohort`.
- **Khuôn mẫu "policy làm chết một biến" ĐÃ TỒN TẠI đúng một chỗ**: `shift_dp.py:153-154`
  `bonus_at = ... if eligible else (lambda pts: 0)` — đúng dạng cần, nhưng điều kiện là tỷ lệ
  của tài xế (không phải hiệu lực thời gian), là `if` hardcode, và **không xuất ra `SolverReport`**.
- `configs/pilot_dongda.yaml:263-267` — comment **đã viết sẵn đúng nội dung A1**
  (*"biến THEO COHORT × THỜI ĐIỂM, không phải hằng số"*) nhưng **chưa có code nào đọc `31/03/2029`**.

## B1 — bước 1: THƯỚC ĐO (không sửa solver nào)

Thêm `net_mean_all = payout − cost` **cạnh** `payout_mean_all` trong `_cohort_metrics`
(`parallel.py:111-126`); giữ nguyên estimator cũ và giữ nguyên `test_cost_ledger.py:77-78`
(cost KHÔNG chạm payout). Đồng thời nối `cost_vnd` vào `sim_metrics` để dashboard thấy được.

**Đây là bước bắt buộc trước mọi thay đổi objective** — đúng spec v2 §6 bước 1 ("đo trước,
sửa sau") và đúng bài học Cycle W (thước sai thì mọi kết luận sai).

Verify: bit-identical (chỉ thêm metric mới) · `net_mean_all == payout_mean_all` khi
`cash_cost=0` · khác khi bật · 5 seed.

## B2 — bước 2: C1 vào objective, hệ số mặc định 0

- `shift_dp.DEFAULT_PARAMS` thêm `cash_cost_vnd_per_km: 0.0`; nhánh ONLINE trừ
  `c_km · exp_trips · avg_dist_km` (`shift_dp.py:181,190`). Mặc định 0 ⇒ **bit-identical**.
- Giải xung đột spec §7 ngay tại docstring: `DEFAULT_PARAMS` cấm *"fatigue-as-money"* vì đó là
  **số bịa**; C1 có **nguồn official** (9.000đ/lượt · điện 70–93đ/km) nên không vi phạm §5.
- Sim ledger đọc **cùng một giá trị** với solver ⇒ một nguồn sự thật cho thế giới và người tối ưu.

~~Verify: **sweep `cash_cost ∈ {0, 70, 150, 250}`**~~ (đúng đề nghị hồ sơ chi phí §7.5), 30 seed
CRN, `coverage: all`, đọc **`net_mean_all`** (không phải payout) + chỉ tiêu kép ĐA-08 1a+1b.

> ### ⛔ ĐÍNH CHÍNH 2026-08-07 (Cycle 2) — phép sweep này là **NO-OP**, đừng chạy
>
> **ĐO (36 case × 9 mức):** `cash_cost` **bất biến TỪNG BIT** trên **[0; 4.325]đ/km**. Lý do cấu
> trúc: `cash_km` chỉ nhân vào **nhánh ONLINE** của `shift_dp` ⇒ nó là **phép co giãn đơn điệu
> trên phần thưởng của ONLINE**, nên `argmax` **không thể** đổi cho tới khi `online_net` đổi DẤU.
> Ngưỡng lật = `ppo / avg_dist` = **4.325đ/km**, tức **17–62×** giá thật (70–250đ/km).
>
> ⇒ Cả **4 mức {0, 70, 150, 250} cho kết quả Y HỆT**, sweep trả **Δ = 0**, và Δ=0 ở đây **rất dễ
> đọc thành *"chi phí không quan trọng"*** — một kết luận sai trông như được dữ liệu hậu thuẫn.
> Đây đúng loại tệ nhất, và cùng họ với chính lỗi khoá-config mà `Cycle 3` vừa bịt.
>
> **Thay bằng:** sweep **`swap_fee_vnd`** (phanh THẬT duy nhất), hoặc sửa **CẤU TRÚC** *"chỉ một
> nhánh có tiền"*. Xem `DEFERRED.md` mục `D-E4-01` (điều kiện mở lại đã sửa).

## B3 — bước 3: policy quyết định giá trị (đây mới là A1 phần rule)

- Thêm nhánh `costs` vào `policy_bundle` (schema minor bump theo `schemas/README.md`), mỗi
  trường mang `effective_from/to` + `source_url` + `confidence` + `track/cohort` — tái dùng
  governance đã có, không phát minh mới. Giá trị hôm nay: `battery_free_until: 2029-03-31`,
  `swap_fee_vnd: 9000`, `battery_rent_vnd_month: 175000`, `cash_cost_vnd_per_km` theo track
  (swap-Platform **0** · charge **70–93**).
- `as_of` xuống solver: `solve(spi, policy, params, as_of)`; `advice_bridge.solver_params`
  (`:342-348`) thêm `as_of` + `track`.
- `resolve_cost_params(policy, track, as_of)` — hàm THUẦN, trả mỗi số hạng kèm **ba trạng thái
  ACTIVE / OFF_BY_POLICY / UNKNOWN** (đúng ngữ nghĩa 3 giá trị của `is_valid_at`;
  **cấm gộp UNKNOWN vào OFF** — bài học hidden-fallback đã trả giá 3 lần) + `reason` đọc được.
- `SolverReport` xuất `terms_active[]` (số hạng nào sống/chết + lý do + trích dẫn policy) —
  trả lời câu hỏi thiết kế #2 của Cường ở `OPEN-THREADS:99-101`: output PHẢI nói ra
  *"hiện không tính chi phí pin vì miễn phí tới 31/03/2029"*.

Verify: kịch bản **as_of sau 2029-03-31** ⇒ số hạng pin bật, SOC thành biến kinh tế, lời khuyên
đổi — **đây là bằng chứng "hàm tối ưu cập nhật theo policy"** mà goal đòi. `UNKNOWN` ⇒ giữ 0 +
caveat, không bịa. 30 seed cho mỗi kịch bản as_of.

## B4 — hai nợ nhỏ gộp vào (rẻ, đều có bằng chứng)

- Hoàn tất đổi tên `accept_cost_per_pickup_km_vnd` → `pickup_disutility_*` ở
  `configs/pilot_dongda.yaml:163`, `world.py:68`, `dashboard.py:143-146`,
  `dashboard_defaults.py:23` — hiện **nửa vời** (hàm đã đổi, config/world chưa) ⇒ bẫy đọc nhầm
  **10–20×** (3.000đ cảm nhận vs 30–250đ tiền thật).
- Gắn nhãn dải `[0,75–0,91]` cho `policy.driver_share` (`:243`) — đang là số trần trụi ở cận
  dưới, không dấu vết mâu thuẫn nguồn (`driver-cost-structure-2026.md:116-123`).

## B5 — không làm

Không C2 (giá trị nghỉ — cần cơ chế mệt mỏi §5b trước) · không C3/CVaR · **không để LLM chọn
tham số** (B3 là rule + bảng tra; agent-as-router là cycle sau, khi đã có `CostParams` và
`net_mean_all` để chấm điểm) · không lớp ingest/normalize API thật (**defer có lý do**: GSM cấp
schema nhưng publish chạy mock, chưa có nguồn thật để kiểm chứng — gap Cường đã tự nêu).

## Verification tổng

| Bước | Cổng phải qua |
|---|---|
| A | fingerprint IDENTICAL (run_once + multiday) · full suite · 3 mutation mới · batch 2 review |
| B1 | bit-identical · `net==payout` khi cost=0 · 5 seed |
| B2 | bit-identical khi hệ số 0 · sweep 4 mức · 30 seed CRN · đọc `net_mean_all` |
| B3 | 3 trạng thái ACTIVE/OFF_BY_POLICY/UNKNOWN có test riêng · kịch bản as_of>2029 đổi hành vi · `terms_active` trong SolverReport |

Mỗi bước một UPDATE riêng, review đối kháng trước khi báo hoàn thành.
