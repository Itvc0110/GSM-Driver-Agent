# AUDIT toàn hệ thống (chỉ thị Cường 2026-07-26 §6) — hồ sơ đang chạy

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

## A3 — AGENT SYSTEM AUDIT: chưa chạy (kế tiếp sau đợt fix A1).
