# UPDATE-110 — E10 KẾT QUẢ: mất λ thì +6.016đ còn **57–65%**; trigger chờ-lâu SỤP

Ngày: 2026-07-31 · Trạng thái: `DONE` (visual gate REVIEWED, Cường verdict OK 2026-07-31)

## Câu trả lời cho câu hỏi trung tâm

> **"+6.016đ còn lại bao nhiêu khi advisor mất λ?"** → **còn ~3.100–3.600đ/người/ngày**, tức
> **57–65%** của trần. Giá trị **KHÔNG sụp** khi advisor mất oracle, nhưng **suy giảm SIG**.

Ghép cặp CRN n=100 seed TƯƠI 5000–5099, coverage `all`, kênh positioning `wait_only`,
mọi arm verdict adherence **OK** (cổng D-M3-10 không treo arm nào):

| Arm | Nguồn cầu / trigger | Δ vs A (CI95) | Δ vs oracle (CI95) | Lớp §6.3 |
| --- | --- | --- | --- | --- |
| `B_oracle` | λ config · capacity | **+5.529** [4.578, 6.414] | — | **tái lập trần** (CI chứa +6.016 của UPDATE-087) |
| `B_hist` | 30 ngày pickup lịch sử · capacity | **+3.146** [2.251, 4.046] | −2.383 [−3.458, −1.278] | **KQ-CÒN-MỘT-PHẦN** (R≈57%) |
| `B_real` | λ̂ cửa sổ cuốn k\*=6 · capacity | **+3.604** [2.542, 4.710] | −1.925 [−3.050, −759] | **KQ-CÒN-MỘT-PHẦN** (R≈65%) |
| `B_wait` | λ̂ · **trigger chờ-lâu** T=30 | **+533** [−228, +1.277] | −4.996 [−6.050, −3.922] | 🔴 **KQ-SỤP** (MDE=727) |
| `B_wait_oracle` (n=30) | λ config · trigger chờ-lâu | *chiều: không phân biệt được với 0* | — | chẩn đoán, **cấm trích độ lớn** |

**G-GUARD: 0/9 tầng hệ thống suy giảm SIG ở cả ba arm** (served_rate, orders_completed,
total_payout, expired_n, wait_median, gini, station_hhi, supply_cell_hhi, starved_hours) ⇒
không có nhãn "đạt cá nhân, hại hệ thống".

## Ba kết quả ngoài dự đoán — báo đúng như đo được

1. **Kỳ vọng §6.5#3 ĐẢO DẤU (nhưng không SIG).** Spec đăng ký trước: *"B_hist gần B_oracle;
   B_real thấp hơn rõ"*. Đo được **ngược**: B_real (+3.604) ≥ B_hist (+3.146). Ghép cặp trực
   tiếp real−hist = **+458 [−679, +1.584], MDE 1.120 ⇒ KHÔNG phân biệt được**. Phát biểu đúng
   là *"hai arm ngang nhau ở n=100"*, **không** phải "realized tốt hơn lịch sử". Ý nghĩa: cửa
   sổ trong-ngày k=6 **không hề thua** 30 ngày lịch sử — nhất quán với L1 (thế giới rank tĩnh
   nên lịch sử dài không mang thêm thông tin) và làm nhẹ đi lo ngại "zero-history giết giá trị".
2. **E10b (trigger chờ-lâu) SỤP.** Δ = +533đ CI chứa 0. Cơ chế đọc được từ volume: arm wait chỉ
   sinh **3,6 ứng viên/ngày** (so 248 của B_real) và thi hành **1,6 lần/ngày** — trigger đúng
   nhưng quá hiếm để tạo giá trị. Precision fired-vs-underfed(λ) = 1,00 nhưng recall = 0,03
   (probe). Trả lời trực tiếp câu hỏi Cường 2026-07-30 (*"có nên thêm biến thời-gian-chờ?"*):
   **thay λ bằng chờ-lâu thì mất gần hết giá trị**; nó không phải nguồn tin thay thế được.
3. **Không tìm thấy dấu hiệu herding/censoring (B1).** corr(residual share pickup, share cung)
   ≈ 0 ở CẢ BA thế giới: A +0,019 · oracle −0,004 · real +0,021 (n=4.590 cặp mỗi thế giới);
   `supply_cell_hhi` real 0,01233 vs oracle 0,01237. **G-HERD KHÔNG thoả** ⇒ theo đúng wording
   pre-registered: *"không tìm thấy bằng chứng cho cơ chế censoring ở config này"* — CẤM đọc
   thành "đã bác bỏ herding" (thế giới rank-tĩnh L1 là nơi herding khó xảy ra nhất).

## Bias — đo được, giải thích cơ chế của 35–43% bị mất

| # | Đại lượng | Số đo | Đọc |
| --- | --- | --- | --- |
| B2 | `R_b = Σλ̂/Σλ` | **0,85** [p10 0,40 – p90 1,34] | λ̂ thấp hơn λ ~15% (pickup ⊂ order) ⇒ `slots` co ⇒ ít đích hơn |
| B3 | TV(λ̂, λ hiện tại) vs TV(λ̂, λ trễ) | **0,249 vs 0,249** | **BẰNG NHAU** — không có lag đo được; đây là bằng chứng SỐ cho L1 (rank tĩnh ⇒ share quá khứ = share hiện tại) |
| B4 | rank-overlap top10 vs λ | **0,57** (tự ổn định 0,76) | λ̂ chỉ trùng 57% top-10 với λ thật — đây là phần "tin kém hơn" |
| B5 | trễ đón (t_pickup − t_order) | median **5,2′** (p90 10,1′) | smear qua biên bucket nhỏ; hướng bảo thủ |
| L2 | Spearman(share pickup World A, share λ) | **0,41** | đội xe đã "giải mã" λ ở mức trung bình — R bị kéo LÊN so với thế giới cả hai phía đều mù (giới hạn không vá được) |

## G-SENS (§6.4) — độ nhạy, n=30 seeds 5000–5029, **CHỈ đọc CHIỀU**

`artifact 41-e10-sens-summary.json` · nhãn `n_insufficient`: n=30 < 100 ⇒ **cấm trích độ lớn**.

| Trục | Kết quả | Đọc |
| --- | --- | --- |
| `real` theo **k** {1,2,3,4,6} | **5/5 DƯƠNG SIG** | Lớp CÒN-MỘT-PHẦN **giữ chiều toàn lưới** — kết luận "mất λ vẫn còn giá trị" KHÔNG nhạy với k |
| `wait` theo **T** {15,20,25,30,35} + `n_min` {1,2,3} | **0/8 phân biệt được với 0** | **KQ-SỤP giữ toàn lưới** — E10b sụp KHÔNG phải vì chọn T tồi |
| `real` theo **min_pickups** {1,3,10} | **IDENTICAL TỪNG BIT** (mean, CI, decided/seed y hệt) | ✅ **Xác nhận dự đoán §6.5#1**: *"tham số TRƠ tại config hiện hành"* — CẤM đọc thành "robust"; chiều này thực tế **không được kiểm** (L10). Cơ chế: giờ thấp nhất ~14 pickup > max sweep 10 |

**Hai điều phải nói thẳng, không tô:**

- **k=1 (+4.618) và k=2 (+4.828) cho điểm ước lượng CAO HƠN k\*=6 headline (+3.604).** Ở n=30
  không so được độ lớn, nhưng chiều gợi ý: tiêu chí chọn k\* (**MAE dự báo**) tối ưu cho *độ
  chính xác dự báo*, **không nhất thiết** cho *giá trị tiền*. Prereg CẤM đổi k\* sau khi nhìn Δ
  ⇒ ghi làm **giả thuyết cho cycle sau**, giữ nguyên headline. (Nếu đúng, R thật của B_real có
  thể cao hơn 65% — tức kết luận hiện tại là **bảo thủ**.)
- **Δ của `wait` giảm đơn điệu theo T** (T15 +1.612 · T20 +986 · T25 +878 · T30 +533 · T35 +177)
  song song với `decided`/seed (36,8 → 22,1 → 12,5 → 3,1 → 0,8). Nới trigger thì can thiệp nhiều
  hơn và giá trị nhích lên — nhưng **không mức nào vượt nhiễu**. Cơ chế sụp là "quá hiếm", và
  nới ngưỡng không cứu được trong dải đã quét.

## 🔴 Phát hiện mạnh nhất: **thông tin chính xác hơn KHÔNG cho nhiều tiền hơn**

Hai bằng chứng độc lập, cùng chỉ một điều — và nó phản trực giác:

| | Prior lịch sử (`B_hist`) | λ̂ realized (`B_real`) | Ai chính xác hơn? |
| --- | --- | --- | --- |
| TV so λ (sai lệch hình dạng cầu) | **0,102** | 0,249 | **hist chính xác gấp 2,4×** |
| rank-overlap top-10 vs λ | **0,753** | 0,572 | **hist** |
| `R_b` mức (Σλ̂/Σλ) | 0,809 | 0,851 | real |
| **Δ thu nhập** | **+3.146** | **+3.604** | **real (nhưng KHÔNG SIG)** |

`artifact 41-e10-bias-histprior.json` + `41-e10-bias-real.json`. Ghép cặp real−hist =
**+458 [−679, +1.584]** ⇒ **không phân biệt được**. Phát biểu đúng: *"prior lịch sử chính xác
hơn hẳn về thông tin nhưng KHÔNG cho giá trị cao hơn"*.

Bằng chứng thứ hai cùng hướng, từ G-SENS: **k=1/k=2 có MAE dự báo TỆ NHẤT nhưng Δ cao nhất**
(+4.618/+4.828 vs +3.604 của k\*=6 chọn theo MAE).

⇒ **Trong thế giới này, độ chính xác dự báo và giá trị tiền không đồng biến.** Hệ quả thiết kế
thật: tiêu chí chọn k\* (§6.2, MAE realized-only) tối ưu **sai đại lượng**. Prereg CẤM đổi k\*
sau khi nhìn Δ ⇒ **giữ nguyên headline**, ghi thành giả thuyết cho cycle sau (`D-E10-05`). Nếu
đúng, R thật của B_real **cao hơn 65%** ⇒ kết luận hiện tại là **bảo thủ**.

## Visual gate

✅ **REVIEWED — Cường verdict OK 2026-07-31**. Bản đồ cung 3 arm + hiệu, seed 5000:
**https://claude.ai/code/artifact/d8c58414-81fd-4257-a8df-aafb99f6cda8**
(nguồn tái sinh: `scripts/e10_visual.py` + `scripts/e10_visual_render.py`, artifact HTML
`41-e10-visual-map.html`). Số nổi bật trên bản đồ: **HHI cung oracle 0,1696 → real 0,1451** —
mất λ làm cung **phân tán hơn**, không dồn cục; 2.550 tài xế-phút dịch chỗ.

## Vòng soi độc lập — 9 finding SỬA trước khi tin số

Workflow 4 lăng kính × phản biện chéo (25 finding thô, 20 sau dedupe; 9 agent phản biện chết vì
session limit ⇒ phần đó tôi **tự kiểm bằng code**, không nhận nguyên si):

| # | Lỗi | Sửa |
| --- | --- | --- |
| 1 | 🔴 `_volume` so `standby_alloc` với `fired_cells` của tick TRƯỚC (planner log alloc TRƯỚC planner trong cùng tick) ⇒ **SystemExit oan "zone-veto thủng" giết arm wait ở seed 5019** | buffer alloc, ghép đúng tick. Chứng minh: ghép đúng = 0 vi phạm, ghép lệch = 1 false positive |
| 2 | 🔴 STOP-1 bắn nhưng `cmd_diff` **vẫn phân lớp** §6.3 + tính R trên trần đã sụp | `return` thật, ghi `arms_raw_no_classification` |
| 3 | Hiệu-của-hiệu ghép theo **INDEX** + `min(len)` truncate im lặng | ghép theo **SEED** (`common`), ghi `n_paired_seeds` |
| 4 | Thiếu `MDE` cho hiệu-của-hiệu ⇒ KQ-GIỮ không tách "không suy giảm" khỏi "underpowered" | thêm `mde` vào `delta_vs_oracle` |
| 5 | Bảng §6.3 **không vét cạn**: arm THẮNG oracle SIG rơi xuyên, nhãn `None` | thêm lớp **KQ-VƯỢT-ORACLE** (soi thước/L2 trước khi báo) |
| 6 | Thiếu assert env-neutral (spec §5.2) — đổi scenario giữa các lệnh CLI ⇒ trộn hai thế giới câm lặng | `_assert_env_neutral` ở 4 đường dựng cfg |
| 7 | `waitoracle` n=30 ghi mean/CI/MDE + vào G-GUARD ⇒ mời trích độ lớn | chỉ ghi `direction_only_n30` |
| 8 | arm wait `decided=0` pooled chỉ print ⇒ diff phân lớp "KQ-SỤP (MDE=0)" thay vì "trigger câm" | fail-loud `SystemExit` |
| 9 | `firing_rate` pha loãng **21%** (mẫu số gồm 5 tick trước giờ mở cửa) · `arm_verdict` gắn index thay seed · bucket-5 cold không báo riêng · UPDATE-109 khai 35 test (thật **34**) | sửa cả 4 |

**Đính chính prereg minh bạch** (ghi `corrections_after_lock` trong `e10-prereg-locked.json`):
`firing_rate_T30_nmin2` 0,057 → **0,072**. Đây là số **mô tả**, KHÔNG phải tham số quyết định;
`T_headline`/`k*`/`n_min`/`min_pickups` **giữ nguyên**, verdict STOP-3 vẫn SỐNG. Không sửa lén.

## Kiểm chứng

- Suite: **851 passed + 5 skipped** (`pytest -q`) **+ 56** (`ui/backend/tests`) = **907 / 0 fail**.
- Fingerprint per-actor IDENTICAL trước/sau merge (5 seed × 2 config, lặp lại sau mỗi bước).
- Mọi arm chạy `coverage="all"` + assert `decided > 0` per seed (arm capacity) · zone-veto assert
  runtime + cột artifact (`n_assigned_into_fired_cells` = **0** trên toàn bộ 100 seed arm wait).
- Seeds: đo 5000–5099 · tuning/probe/preflight 5100–5129 (disjoint) · bias 5000–5002.
- Artifact: `research/audit/2026-07-27-current-state/41-e10-*.json` (preflight, probe, tune,
  hist-prior, worldA, 5 arm, diff, bias-real).
- Sensitivity 13 biến thể × 30 seed: XONG (bảng G-SENS trên) · `bias` chạy cho CẢ BA arm
  (real/hist/wait) + prior lịch sử so λ trực tiếp.
- **CHƯA kiểm chứng**: `B_wait_oracle` chỉ n=30 (chiều, cấm trích độ lớn); chưa đo arm
  nonstationarity (`D-E10-03`) nên L1 vẫn là giới hạn mở; giả thuyết `D-E10-05` (tiêu chí chọn
  k sai đại lượng) chưa kiểm bằng cycle riêng.

## Nhãn evidence

Toàn bộ **MOCK** (`configs/pilot_dongda.yaml`). Δ là `[ĐO]` n=100 ghép cặp CRN, bootstrap 5000
resample seed 12345. `ruler_fix_applied = false` (thước giữ nguyên, z tiền-flight = −2,39).
ASSUMPTION §9-L3 giữ nguyên: Δ **điều kiện trên** advisor có trip feed toàn đội (cell, phút) —
catalog trips thật đang THIẾU CỘT, GSM không cấp thêm.

## Giới hạn KHÔNG vá được (nguyên văn — phải đi kèm mọi lần trích số)

- **L1 thế giới rank-tĩnh**: `λ = ngày × giờ × ô` ⇒ thứ hạng ô không đổi cả ngày. B3 đo được
  TV_now = TV_lag chính là dấu vân tay của nó. Ngoài đời pattern không dừng ⇒ **R 57–65% là
  chặn TRÊN**, thực tế sẽ thấp hơn. Đây là caveat quan trọng nhất của UPDATE này.
- **L2** λ̂ ngửi được oracle qua bản năng tài xế (Spearman 0,41) ⇒ R bị kéo lên.
- **L3** feed pickup toàn đội chưa VỮNG · **L4** E10b đo trigger × execution-gate, không tách
  trọn · **L6** lịch sử B_hist là 30 ngày cùng-phân-phối · **L7** k\* tuning shadow ≠
  equilibrium · **L10** `min_pickups` nhiều khả năng trơ (đang kiểm ở sens).
- **k\* = 6 nằm ở BIÊN lưới** (MAE giảm đơn điệu 59,7→54,1) — hệ quả của L1; ai đọc "k=6 tối ưu"
  mà bỏ caveat là đọc sai.

## Adversarial self-review / flaws found

- Lỗi #1 của vòng soi (`_volume` off-by-one) **đã suýt giết arm wait bằng false positive** —
  nếu tôi tin SystemExit đó, kết luận sẽ là "zone-veto hỏng" thay vì "trigger sụp". Bài học lặp
  lại: kill-switch cũng cần test cho chính nó.
- `B_wait` có 24/100 seed `decided=0` — fire thưa; đã báo số, không giấu trong trung bình.
- Bảng §6.3 của **chính spec** không vét cạn (lỗi #5) — spec cũng sai được, không chỉ code.
- Kỳ vọng §6.5#3 sai dấu (mục 1) — in lại cạnh kết quả thật theo đúng cam kết.
- Chưa chạy `bias` cho hist/wait ⇒ chưa loại trừ được cơ chế khác nhau giữa hai arm.

## Follow-up

- `D-E10-05` (tiêu chí chọn k tối ưu sai đại lượng) — cycle riêng, prereg mới, n≥100.
- **Visual gate ĐÃ chạy** — artifact d8c58414 (bản đồ 3 arm + hiệu, seed 5000). Chờ verdict Cường.
- ⏳ **PENDING-REVIEW còn 17 mục chờ Cường**: V-01..V-14, V-16, **V-17 (kênh VỊ TRÍ — chính là
  kênh UPDATE này đo)**, V-18.
