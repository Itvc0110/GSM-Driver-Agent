# UPDATE-114 — 5 lỗ đường ống A/B (vòng thiết kế D-M3-04 bắt) + E10b dải ngưỡng thấp

Ngày: 2026-07-31 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi** (chỉ đạo Cường 2026-07-31)

## Bối cảnh — vòng thiết kế bắt lỗi ở HAI tầng

Chạy workflow thiết kế `run_pair_multiday` cho `D-M3-04` (3 góc độc lập: CRN-first ·
metric-first · minimal-diff, mỗi góc một skeptic). **6/6 agent hoàn thành** — và nó bắt được
hai loại thứ khác nhau: (1) **hai chỗ SAI trong brief của tôi**, cả hai bị bác bằng ĐO;
(2) **năm lỗ trong code HIỆN HÀNH**, ảnh hưởng mọi phép đo A/B chứ không riêng `D-M3-04`.

## Phần A — brief của tôi sai hai chỗ

| Tôi viết | Vòng soi đo được | Phán quyết |
| --- | --- | --- |
| *"CRN phân rã dần theo ngày; phải đo mức phân rã"* | Ngày 0 hai arm **BIT-IDENTICAL** (fingerprint per-actor `a092e1f242905001` ở CẢ A và B). `reset_for_new_day` xoá sạch mọi carrier quỹ đạo: SOC từ dòng dùng chung `default_rng((seed,d,0xDA1))`, `shift_*` từ `base_shift`, `cell` về `home_cell` ⇒ **hỗn loạn KHÔNG tích luỹ xuyên ngày**; thứ duy nhất truyền qua là `DriverMemory` = chính can thiệp | 🔴 **TÔI SAI** — bỏ mục "đo phân rã CRN"; multiday A/B **sạch hơn tôi tưởng** |
| *"trần kênh nghỉ ≤29% vì hai lan can chặn 71,0%"* | 71,0% là số **MỘT NGÀY**. Trong multiday kênh chỉ hiện thực **2–5,7%** cơ hội và chặn chính là `at_window`/`window_past`, không phải lan can sức khoẻ | 🔴 **TRÍCH SAI CHẾ ĐỘ** — đã đính chính trong brief |

Thêm một bẫy nữa vòng soi chỉ ra: **`CHANNEL_LADDER["rest_window"]` bật kèm `shift_plan:
True`** ⇒ đo trên nền đó là đo *`shift_plan` + `rest_window`* vs không-gì, mà `shift_plan` đã
bị **ĐA-07/UPDATE-087 TẮT vì có hại**. Nền đúng: A = positioning `wait_only`, B = A +
`rest_window`.

Và một tin tốt đo được: arm B `rest_window` decided **0/12/11**, followed **0/5/8** theo ngày
0/1/2 ⇒ **kênh thôi INERT từ ngày thứ hai**, đúng acceptance của `D-M3-04`.

## Phần B — 5 lỗ code HIỆN HÀNH, đã sửa

| # | Lỗ | Bản chất | Sửa |
| --- | --- | --- | --- |
| (a) | **DET-01 không có cổng** | `PairResult.adherence_a` tồn tại kèm comment *"arm đối chứng cũng phải được ĐO, không giả định sạch"* nhưng `aggregate_adherence` **chỉ đọc `adherence_b`** ⇒ không cổng nào đọc nó. Đúng họ lỗi `D-R12` (cơ chế sống ở comment + field, không có đường chạy) — và DET-01 đã từng làm tôi báo một con số sai cho Cường | arm A (advice off) có quyết định ⇒ **TREO** kèm tên seed |
| (c) | `dismissed`/`suppressed` **bị bỏ sót** khỏi `aggregate_adherence` | Không bao giờ tới artifact ⇒ mất đường phân biệt *"tài xế TỪ CHỐI"* với *"advisor bị NHỊP CHẶN"* — hai kết cục khác nhau của ĐA-04. Vi phạm bằng **bỏ sót**, không bằng tính sai | cộng cả 6 khoá |
| (e) | Tầng 5 vào **bảng significance HAI CHIỀU** | `compare()` gắn `significant` cho chỉ tiêu sức khoẻ và `run_parallel` in *"ĐỘNG TỚI HỆ THỐNG"* ⇒ **"veto tăng" đọc thành "hệ thống tốt lên"**, mà veto tăng nghĩa là tài xế chạm mệt/cạn pin NHIỀU HƠN. Đúng hướng Goodhart mà tầng 5 sinh ra để chặn | `HEALTH_KEYS_ONE_WAY`; tầng 5 in RIÊNG, không có `significant` |
| (b) | Cổng tầng 5 đặt trên **TỔNG cohort** | Phụ thuộc cấu hình: ladder `all` chạm **100%** tài xế nên cổng đủ nhạy (`rest_min_total` +15% ≫ tol 2%); nhưng kênh THƯA như `rest_window` multiday chạm ~10% ⇒ hiệu ứng **pha loãng ~10×** xuống dưới nhiễu seed ⇒ **cổng canh NHIỄU**, verdict tuỳ seed, và người sửa sẽ nới tolerance (mẫu `D-R20`) | `touched_actors(result, channel)` + `health_guardrail(result, actor_ids=…)` |
| (d) | `_sig` kẹp cứng **n≥30** | So **hai biến thể advice** là bài toán khác, cần `MIN_SEEDS_FOR_VARIANT_COMPARISON=100` (hằng đó đã có kèm lý lẽ đo được: SD ~40k/seed ⇒ n≈105). Mọi contrast biến-thể qua `compare()` được gắn `significant` ở n=30 — dưới chuẩn | `_sig(..., min_seeds)` + `compare(..., min_seeds)`; artifact ghi `min_seeds_for_sig` |

## Phần C — E10b dải ngưỡng THẤP (CONFIRMATORY, prereg khoá trước khi đo)

`specs/simulation/e10b-low-threshold-prereg-locked.json` (Cường duyệt) ·
artifact `44-e10blow-summary.json`:

| T | Δ vs A | Can thiệp/ngày | Δ vs oracle | Lớp |
| --- | --- | --- | --- | --- |
| 10′ | +2.589 [1.688, 3.464] | 46,3 | −1.350 | CÒN-MỘT-PHẦN |
| **12′** | **+2.961 [2.058, 3.830]** | 42,1 | −978 (MDE 1.128) | 🟢 **KQ-GIỮ** |
| 15′ | +2.159 [945, 3.314] | 36,0 | −1.780 | CÒN-MỘT-PHẦN |
| 18′ | +1.778 [788, 2.759] | 27,4 | −2.161 | CÒN-MỘT-PHẦN |

**Ba kiểm của prereg đều PASS:**
- **STOP-A** cổng adherence: không bắn (z từ −1,56 tới +0,41, verdict OK cả 4);
- **STOP-B** T=15 **tái lập** dương SIG ⇒ phép đo khám phá hôm trước **không phải type-I**;
- **STOP-C** G-GUARD: **0/12 tầng** suy giảm SIG ở cả 4 T (gồm tầng 5 sức khoẻ);
- **Kỳ vọng QUAY ĐẦU: XÁC NHẬN** — Δ đỉnh ở T=12; T=10 giảm về +2.589 **dù can thiệp NHIỀU
  HƠN** (46,3 vs 42,1/ngày) ⇒ trigger **có tính chọn lọc thật**, không phải mua Δ bằng khối
  lượng. (Nếu chỉ mua bằng khối lượng thì T=10 phải cao nhất.)

**Phát biểu được phép**: trigger chỉ đọc **thứ quan sát được** (thời gian chờ của ô) ở T=12
đạt **75%** giá trị của advisor-biết-λ và lớp **KQ-GIỮ** (CI của Δ vs oracle chứa 0).
**Kèm bắt buộc**: caveat **L1** (thế giới rank-tĩnh) + **L2** (λ̂ ngửi oracle qua hành vi đội
xe) + **`D-E10-07`** (CI hẹp hơn thực tế ~409đ) ⇒ phát biểu **YẾU** về ngoài đời.
**Headline E10 gốc VẪN là T=30** — prereg cũ khoá vậy, không sửa số cũ.

## Files

- **SỬA** `src/gsm_sim/parallel.py` (a, c, d, e) · `src/gsm_sim/sim_metrics.py` (b) ·
  `scripts/run_parallel.py` (e — in tầng 5 riêng) · `scripts/measure_e10.py` (+`e10blow`)
- **TẠO** `tests/test_control_arm_gate.py` (4) · `tests/test_health_gate_touched.py` (3) ·
  `specs/simulation/e10b-low-threshold-prereg-locked.json` ·
  `research/audit/.../41-e10-e10blow-T{10,12,15,18}-n100.json` + `44-e10blow-summary.json`
- **SỬA** `specs/simulation/d-m3-04-multiday-ab-brief.md` (đính chính 2 chỗ tôi sai + 2 bẫy mới)

## Kiểm chứng

- 7 test mới: **3 đỏ + 1 xanh** rồi **3 đỏ nữa** TRƯỚC fix → 7 xanh sau.
- Regression: cổng adherence + parallel + tầng 5 + fairness **38/38** và **24/24**.
- Full suite CẢ HAI lệnh: **898 passed + 4 skipped + 1 FAILED** (`pytest -q`) **+ 65 UI**.
  🔴 **1 test ĐỎ, ghi `UNRESOLVED`, KHÔNG che** — `test_bug01_idle_never_exceeds_online_time`:
  `d-62` `2026-07-03` idle **247,48′** > online **246,00′**. Nguyên nhân đã truy được một
  phần: `generate_realdata(continuous=True)` dùng `run_multiday`, nên fix `D-E10-01` (reset
  `idle_streak_min`) đổi realization mock ⇒ **phơi ra** một bất khớp CÓ SẴN giữa hai nguồn
  ("online_time" từ sim `online_min` vs "total_idle" từ dwell hex). Làm tròn `round(...,2)`
  chỉ gây ≤0,3″ nên KHÔNG giải thích được 1,48′ ⇒ root cause CHƯA chứng minh xong ⇒ mã nợ
  **`D-M3-11` sev CAO**. **Không nới tolerance, không `xfail`** — cả hai là che (mẫu `D-R20`).
  Fix `D-E10-01` giữ nguyên: nó ĐÚNG, và chính nó làm lỗi lộ ra.
- E10b-low: 4 arm × n=100, cổng OK cả 4, G-GUARD 0/12.

## Adversarial self-review / flaws found

- Lỗ (a) là **cùng họ với lỗi tôi vừa sửa hôm nay** ở D-M3-08 (cơ chế chỉ sống trên giấy).
  Ba lần trong một ngày ⇒ mẫu này là **hệ thống**, không phải tai nạn: repo có xu hướng viết
  comment/field mô tả một bảo đảm rồi không nối đường chạy. Đối trọng duy nhất đã chứng minh
  hiệu quả: **test sever-restore** (ngắt cơ chế ⇒ phải đỏ).
- Lỗ (b) tôi **tự tạo ra hôm qua** (tầng 5, UPDATE-111) và không tự thấy — vòng soi thấy. Bài
  học: cổng đặt trên mẫu số nào phải kiểm bằng **đúng cấu hình sẽ dùng nó**, không phải bằng
  cấu hình dễ nhất (ladder `all` chạm 100% nên trông ổn).
- `touched_actors` đọc `detail["channel"]` — kênh nào không ghi `channel` sẽ không được lọc
  đúng. Đã kiểm: 5 kênh advice hiện có đều ghi. Kênh mới quên ghi ⇒ lọt vào tập "toàn bộ".
- Chưa nối `health_guardrail(actor_ids=...)` vào `aggregate_health_guardrail` — cơ chế có
  nhưng đường chạy cho `D-M3-04` sẽ nối trong cycle đó (⚠ chính họ lỗi (a); ghi vào plan
  `D-M3-04` như acceptance bắt buộc, kèm test T10-kiểu "có mặt trong artifact").

## Follow-up

- Plan mode `D-M3-04` (3 điểm Cường đã chốt: TB ngày 2..N bootstrap theo seed · days=3 n=100)
  — acceptance phải gồm: nối `touched_actors` vào cổng tầng 5, dùng nền A=wait_only thay
  ladder, `min_seeds=100` cho contrast biến thể.
- ⏳ **PENDING-REVIEW 19 mục chờ Cường**: V-01..V-14, V-16, V-17, V-18 (kèm card im lặng mới),
  V-20, V-21.
