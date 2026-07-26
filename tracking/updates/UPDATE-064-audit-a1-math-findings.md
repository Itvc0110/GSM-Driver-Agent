# UPDATE-064 — AUDIT A1: math audit đa-agent — 110 finding, persist trước khi fix

Ngày: 2026-07-27 (rạng sáng) · Track: **AUDIT** (chỉ thị Cường §6 — "math modelling quan trọng
nhất") · Plan đã duyệt + Cường chốt: workflow LỚN ~30 agent, fix ngay BUG hẹp.

## 1. Đã chạy

Workflow `math-audit-a1` (**87 agent thực tế**: 14 finder theo đơn vị — 9 solver, cụm estimator,
behavior, demand, physics, rating/newbie/mission, statistics — + refuter riêng cho từng finding
CAO/TB; 1.594s, ~5.75M token subagent). Workflow **fail ở bước gộp** vì 2 lỗi: (a) session limit
giết 10 refuter + 1 connection error; (b) bug script của tôi — không guard `verdict=null`.
**Khắc phục không tốn agent**: đọc `journal.jsonl` (76 result đã ghi) và gộp bằng Python local.

## 2. Kết quả (persist tại `research/audit/2026-07-26-full-audit/`)

- `a1_math_findings.json` — **110 finding đầy đủ** (61 CONFIRMED / 1 PLAUSIBLE / 0 REFUTED /
  11 chưa-verify-vì-quota / 37 THẤP không verify theo chính sách scale).
- `README.md` — tóm tắt 9 CONFIRMED severity CAO + cụm TB đáng chú ý + A2 verdict sơ bộ
  (**F-U2-A ĐÓNG**: 13 bảng GSM thật không có bảng thưởng ngày/tân binh).

**3 claim nặng nhất đã TỰ KIỂM trên code (không tin agent suông), đều THẬT:**
1. `BEHAV-2` — `dashboard.py:117` slider override `accept_logit_center_vnd` mặc định **6000, max
   12000** trong khi config đã recalibrate **21200** → mọi run chỉnh-tham-số từ dashboard dùng kinh
   tế học cũ. Đây cũng là lời giải cho một phần bí ẩn V-01..V-09: reviewer xem dashboard có thể
   thấy hành vi khác CLI.
2. `S1-1` — `bonus_feasibility.py:43-51` nhánh already_maxed trả `feasible=True` + số thưởng mà
   không kiểm acceptance/completion (dưới ngưỡng = mất sạch thưởng theo chính chính sách S1 áp).
3. `S8S9-1` — `templates.py:110-115` render số trần không neo registry (V1 sẽ veto).

## 3. Kiểm chứng & trung thực

- 0-REFUTED là bất thường thống kê → refuter có thể thiên vị xác nhận; đã ghi caveat vào README;
  quy trình fix: TỰ đọc code từng finding + failing regression test TRƯỚC khi sửa.
- Vài verifier chạy lúc safety-classifier down (hệ thống báo) — cùng chính sách trên xử lý.
- 11 finding chưa verify (trong đó 4 CAO: EST-8 đề án shrinkage, S2-2, S2-3, STATS-1) — verify lại
  đầu đợt sau khi quota reset.
- Chưa fix gì trong update này — persist trước để không mất 5.75M token kết quả nếu phiên chết.
- Visual: NOT_APPLICABLE (chỉ thêm hồ sơ audit + docs).

## 4. Follow-up (đợt kế — UPDATE-065+)

Fix hẹp có test theo thứ tự: S1-1 → BEHAV-2 → S8S9-1 → S1-4 → S5-1 → S2-1 → S1-3 → DEMAND-1 →
STATS-2 (guardrail /ab tôi viết) → lỗ gate schema A2. MODEL GAP lớn (EST-1/EST-8 shrinkage, S6-1
window-aware knapsack, S2-4 p_accept cá nhân hoá) → đề án trình Cường. Rồi A3 agent-system audit.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · V-09 (dashboard SIM-XANH) · **V-10 (Track UI —
web app + khu Mô phỏng, kịch bản trong UPDATE-063 §5)** · Q-03 (corpus Khánh).
