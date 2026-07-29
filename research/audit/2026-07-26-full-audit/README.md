# AUDIT toàn hệ thống (chỉ thị Cường 2026-07-26 §6) — hồ sơ đang chạy

> **HISTORICAL WORKING SNAPSHOT:** phần mở đầu bên dưới phản ánh thời điểm A1 vừa xong nên có
> trạng thái/số liệu đã lỗi thời. Kết quả reconcile của audit là [`REPORT.md`](REPORT.md); trạng
> thái code/data/UX mới nhất và blocker R5 xem
> [`../2026-07-27-current-state/README.md`](../2026-07-27-current-state/README.md); hiện trạng
> mới nhất (Cycle W) xem thêm [`../2026-07-29-cycle-w-review/findings.md`](../2026-07-29-cycle-w-review/findings.md).
> Không sửa lại nội dung lịch sử phía dưới để giữ evidence trail.

Trạng thái: **A1 MATH AUDIT xong vòng find+verify** (2026-07-27 rạng sáng) · A2 data đã gom bằng
chứng · A3 agent-system chưa chạy · A4 fix đang tiến hành.

## A1 — MATH AUDIT (workflow 87 agent: 14 finder + verify đối kháng từng finding CAO/TB)

Kết quả thô đầy đủ: **`a1_math_findings.json`** (110 finding — đọc file này, README chỉ tóm tắt).

| Nhóm | Số lượng |
|---|---|
| CONFIRMED (đã qua refuter) | **61** |
| PLAUSIBLE | 1 |
| REFUTED | 0 |
| CHƯA VERIFY do session limit (finder xong, refuter chết) | 11 |
| THẤP — ghi nhận, không verify (chính sách scale) | 37 |

**Caveat phương pháp (trung thực):** tỷ lệ 0-refuted bất thường — refuter có thể thiên vị xác
nhận; ngoài ra vài verifier chạy lúc safety-classifier down. Bù lại: **top-3 claim nặng nhất đã
được TÔI tự kiểm lại trực tiếp trên code và xác nhận thật** (BEHAV-2, S1-1, S8S9-1 — xem dưới).
Mọi fix chỉ làm sau khi tự đọc code + có failing regression test — không fix theo lời agent.

### CONFIRMED severity CAO (9)

| ID | Loại | Tóm tắt | Fix |
|---|---|---|---|
| BEHAV-2 | BUG | **Dashboard override `accept_logit_center_vnd`=6000 (slider max 12000)** — mọi run từ dashboard dùng kinh tế TRƯỚC 2 lần recalibration (đúng là 21200). ✔ tự kiểm `dashboard.py:117` | narrow |
| S1-1 | BUG | Nhánh `already_maxed` bỏ qua ràng buộc acceptance/completion — báo "có thưởng" khi tài xế dưới ngưỡng đã MẤT thưởng. ✔ tự kiểm `bonus_feasibility.py:43-51` | narrow |
| S1-2 | MODEL | `hours_needed=gap/rate` coi rate bucket tại t_now không đổi hết ca (đứng giờ peak → lạc quan) | narrow |
| S1-4 | CALIB | `DEFAULT_TRIPS_PER_HOUR=3.0` không nguồn, gấp ~2 lần số ĐO trong repo (1.4-1.5) | narrow |
| S2-1 | BUG | Points-band flooring (`add_pts // PBS`) rơi phần dư điểm mỗi bucket → DP quyết định trên điểm sai | narrow |
| S5-1 | BUG | View weekly_khoan **rò tương lai**: revenue_so_far/days_active gộp cả ngày SAU `t_now` | narrow |
| S6-1 | MODEL | Knapsack không biết cửa sổ giờ mission — chọn mission có khung đã qua | large → đề án |
| S8S9-1 | BUG | Template F3 render số (`total`, `penalty_count`, `threshold`) KHÔNG neo numbers_registry → verifier V1 veto. ✔ tự kiểm `templates.py:110-115` | narrow |
| EST-1 | MODEL | Fallback acceptance/completion=**1.0 khi thiếu mẫu** — lạc quan hệ thống xuyên feature layer (họ hàng BUG-DSIM13-02) | large → đề án EST-8 |

### Cụm finding TB đáng chú ý (chi tiết trong JSON)

- **S3**: duration ÂM vắt nửa đêm (S3-1); nhánh `threshold_forced` dựa cơ chế forced-accept **đã bỏ
  từ policy 23/02/2026** (S3-2); vùng chết acceptance [0.5,0.85) im lặng (S3-3).
- **S5-4** off-by-one ngày (hôm nay chưa có đơn → mất khỏi cả days_active lẫn days_remaining).
- **S6-4** mission sim reset NGÀY nhưng L1R trình bày như mission dài → remaining_count sai.
- **DEMAND-4/5/6**: event orders — rejection sampling nhận draw cuối vô điều kiện (11% cuốc rơi
  ngoài event), pickup uniform-disk thay vì Gaussian, event addend sai đơn vị khi trộn vào weight.
- **PHYS-1**: `station.ready_soc_pct` là knob CHẾT (pin trong tủ luôn 100%).
- **BEHAV-3**: gate advice không throttle — rút coin adherence mỗi ~2 phút idle (adherence hiệu
  dụng ≫ danh nghĩa; chạm D-SIM-14).
- **XANH-2**: mốc 50 cuốc/7 ngày gần như không thể quan sát trong sim (tenure sampling + horizon).
- **STATS-2** (tự-audit U3): `/ab` guardrail — `worst_cell_delta_served` không phải worst-cell,
  `flagged_cells` hardcode `[]`.

### 11 finding CHƯA VERIFY (quota) — ưu tiên verify lại đầu đợt sau

`EST-8` (đề án shrinkage — nền cho D-SIM-18) · `S2-2` (forecast map theo index — nghi lệch cell/bucket)
· `S2-3` (terminal bonus không xét eligibility) · `S2-6/7` · `STATS-1` (guardrail 1-seed ngưỡng bịa
−2/−50k — TỰ THÚ: tôi viết ở U3) · `STATS-3/4/5/7` · `BEHAV-4`.

### Coverage — cái audit KHÔNG phủ (khai báo của từng finder trong JSON `coverage`)

## A2 — DATA AUDIT (bằng chứng đã gom, verdict sơ bộ)

- **F-U2-A ĐÓNG**: 13 bảng GSM thật (`gsm_spec.py`) KHÔNG có bảng thưởng ngày/tân binh —
  ghi chú trên UI là cách trình bày đúng; `PayoutLedger.day_bonus` là thiết kế L0 pack cũ của ta.
- **Lỗ gate schema**: gate kiểm tên bảng/cột+thứ tự, KHÔNG kiểm dtype/nullability/enum/FK;
  4 bảng `spec_cols=None` bị skip hoàn toàn (trips, penalization_ATA, public_frauds,
  user_mission_progress). → ứng viên fix hẹp: mở rộng gate.
- `day_bonus_tiers` thực chất là mốc TUẦN theo research (`specs/policy-weekly-khoan-model.md:23`)
  — simplification có nhãn, đã ghi nhận; giữ daily-proxy là quyết định mở.
- D-SIM-08 còn nguyên (verify script sinh data riêng, không đọc artefact trên đĩa).

## Đề án MODEL GAP (CHỜ CƯỜNG DUYỆT — không cài trước khi chốt)

### ĐA-01 — Estimator thống nhất cho acceptance/completion (D-SIM-18 · EST-1/2/6/8 · BEHAV-7)

**Vấn đề đo được**: cùng MỘT đại lượng đang có ≥5 estimator khác nhau rải rác — fallback **1.0
bịa** (bonus_gap.py:44-45, from_l1r.py:100, ui advisor), carry-forward, mean-of-daily-ratios
(memory), realized thô k/n từ offer thứ 5 (advice_bridge) — và verdict advice lật theo việc rơi
vào estimator NÀO chứ không theo dữ liệu. Định lượng: P2 base 0.95 vẫn có ~23% ca bị coi "dưới
ngưỡng 0.85" ngay offer thứ 5 (1−0.95⁵) — advice theo nhiễu lượng tử hoá.

**Đề xuất**: MỘT hàm `gsm_core/estimators.py::shrunk_rate(k, n, p0, m) = (k + m·p0)/(n + m)`
(Beta posterior mean) dùng chung core/sim/UI. Prior p0 theo bậc: (1) **pooled** lịch sử cá nhân
Σk/Σn (KHÔNG mean-of-ratios) từ DriverMemory / statistic_daily ngày trước; (2) accept_base
archetype / median quần thể — nhãn ASSUMPTION; **tuyệt đối không 1.0**. m = pseudo-count, mặc
định 5 (= min_offers hiện tại → chuyển tiếp LIÊN TỤC, bỏ được cutoff cứng), expose config
`advice.rate_prior_pseudo_count`. **Giữ nguyên realized thô ở chỗ CHẤM THƯỞNG** (điều kiện
thưởng là con số realized — chỉ ước lượng cho GATE advice là đổi).
Kèm fix EST-2: k,n của view đếm TRONG NGÀY (điểm và tỷ lệ cùng granularity).

**Chi phí/kiểm chứng**: chạm 5 call site; là thay đổi CALIBRATION-CLASS → sweep D-SIM-06 chạy
lại (30 seed/ô) + so bảng trước/sau; kết luận UPDATE-056 sẽ được đo lại (kỳ vọng: bớt advice-theo-
nhiễu ở P2, giữ hiệu ứng P4).

### ĐA-02 — Mission knapsack biết CỬA SỔ GIỜ (S6-1/2/3)

**Vấn đề đo được** (repro trong findings): 14:00 vẫn chọn mission khung 6-9h và hứa "thưởng tối
đa 20.000đ" không thể đạt; combo bị tính cost CỘNG trong khi sim đếm 1 cuốc cho NHIỀU mission
lồng nhau → từ chối combo tốt hơn (60k khả thi 6h bị bỏ, chọn 50k đòi 2 cửa sổ rời).

**Đề xuất 2 bước**: (B1 — hẹp, làm được ngay sau duyệt) view mang `window_start/end` thật
(fix S6-3 data path), solver LOẠI mission có window ∩ [t_now, t_now+budget] = ∅ và cap
cost theo |window ∩ phần còn lại|; caveat "cuốc có thể đếm cho nhiều nhiệm vụ — ước giờ là chặn
trên". (B2 — cần policy) effort theo TẬP CUỐC CHIA SẺ (window lồng nhau đếm chung) — **chặn bởi
D-POL-05**: chính sách đếm THẬT của GSM chưa kiểm chứng được, không đoán.

### ĐA-03 — Gói shift_dp S2 (S2-1/4/5 + chờ verdict S2-2/3/6/7)

**Đã confirmed**: p_accept=0.9 hằng (spec đòi p_accept_i, call site không truyền params dù hàm
nhận — fix hẹp: truyền acceptance thật của tài xế + avg_dist từ data, ghi numbers[]); band
flooring rơi phần dư điểm (fix: expectation-mix giữa 2 band kế cận — giữ Markov). **Chưa verify
(quota)**: forecast map theo index (S2-2 — nghi lệch cell/bucket nghiêm trọng), terminal bonus
không xét eligibility (S2-3), bucket 30' ngầm (S2-6), demand cả cell làm expected của 1 tài xế
(S2-7). → làm MỘT gói sau khi verify xong để không sửa shift_dp hai lần.

## A3 — AGENT SYSTEM AUDIT: chưa chạy (chờ quota reset — kế tiếp).
