# UPDATE-086 — Artifact 24: đo lại bằng estimator KHÔNG BIAS — advisor không làm ai nghèo đi; kênh vị trí LẦN ĐẦU dương cá nhân SIG

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** measurement (Cycle E — thi hành Q-11) + evaluator fix
- **TODO liên quan:** **BUG-EVAL-ARGMAX → DONE-CODE** · H4 · nối UPDATE-085
- **Artifact:** `24-unbiased-30seed.json` — 30 seed × 6 thế giới (A·B0·B1·B2·B3w·B3r), 180 run,
  `coverage: all`, CRN

## 1. Evaluator mới (Q-11 duyệt)

`parallel._cohort_metrics`: mean payout trên **MỌI** tài xế (`payout_mean_all`) + tách archetype
(`payout_mean_P1..P7`) — không chọn lọc theo bất kỳ thống kê nào của A hay B ⇒ không còn
regression-to-the-mean. Nằm trong dict `system` ⇒ `PairResult`/`compare()`/mọi consumer giữ
nguyên. `pick_target` GIỮ làm view chẩn đoán, docstring mang nhãn **BIASED-DIAGNOSTIC** (có test
canh nhãn). **Placebo test mới**: advice bật + mọi kênh tắt ⇒ Δ = 0 tuyệt đối từng seed (canh
CRN + estimator không tự chế số; bản thiết kế đo cũ chưa từng có placebo). 4 test; mutation ME1
(bỏ merge cohort) ⇒ 2 đỏ gồm cả placebo — không còn test xanh-rỗng. Suite **633 passed / 5 skipped**.

## 2. Kết quả (Δ/người/ngày trừ khi ghi khác; SIG = CI 95% loại 0)

| | B0 shift_plan | B1 +wait_only | B2 +wait_and_reloc | **B3w CHỈ positioning** | B3r |
|---|---|---|---|---|---|
| **payout_mean_all** | −466 ns | **+3.464 SIG** | **+4.590 SIG** | **+5.027 SIG** | **+3.568 SIG** |
| payout_mean_P4 | −439 ns | +1.628 ns | −1.042 ns | −777 ns | −748 ns |
| [argmax-A, BIAS] | (−35,5k) | (−34,2k) | (−32,6k) | (−33,2k) | (−31,9k) |
| served_rate | ns | +1,54đp SIG | +1,34đp SIG | **+1,72đp SIG** | +1,40đp SIG |
| đơn hết hạn | ns | −20,2 SIG | −18,7 SIG | −20,2 SIG | −19,6 SIG |
| Gini | ns | **GIẢM SIG** | **GIẢM SIG** | −0,0053 ns | **GIẢM SIG** |
| HHI cung/ô | ns | GIẢM SIG | GIẢM SIG | GIẢM SIG | GIẢM SIG |
| tổng payout đội | ns | +312k SIG | +413k SIG | **+452k SIG** | +321k SIG |
| km rỗng | ns | +0,80đp SIG | +0,75đp SIG | +0,80đp SIG | +0,85đp SIG |
| veto(b) km-rỗng-tự-trả | PASS | **PASS** | **PASS** | **PASS** | **PASS** |
| đổi pin [H4] | **+4,7 SIG** | +8,3 SIG | +7,4 SIG | +2,6 SIG | +1,7 SIG |
| chờ đổi pin [H4] | ns | ns | ns | ns (−0,77) | ns |

## 3. Ba kết luận

### 3.1 "Advisor làm tài xế nghèo đi" — CHÍNH THỨC là artifact đo lường

B0 không bias: **−466đ/người, CI trùm 0** — advisor hiện trạng là HOÀ về cá nhân, không phải
−17k…−40k như chuỗi argmax cũ. Toàn bộ narrative tiêu cực hai ngày qua đo *cực trị hồi quy về
trung bình*, đúng như UPDATE-085 §4 chứng minh.

### 3.2 Kênh VỊ TRÍ: lần đầu tiên một kênh advice DƯƠNG cá nhân có ý nghĩa thống kê

`payout_mean_all` **+3,5k…+5,0k/người/ngày SIG** ở cả 4 nhánh có positioning; B3w (chỉ
positioning, shift_plan im lặng — đúng chỉ thị ĐA-07) đẹp nhất: **+5.027đ/người + served
+1,72đp + đơn chết −20/ngày + đội +452k + HHI giảm + veto km-rỗng PASS**.

⚠ **P4 (tân binh) chưa chứng minh được hưởng lợi**: điểm ước lượng ±1–2k, CI trùm 0 — subgroup
~13 người/run thiếu power ở n=30. **Không bị hại có ý nghĩa**, nhưng "tách theo archetype" của
Q-11 chưa cho P4 dấu dương. Cần n≈100 hoặc nhìn nhóm theo tuần.

### 3.3 Veto 9 (đổi pin không tăng) — kẹt ĐÚNG kiểu veto 8 cũ

Đổi pin tăng SIG ở mọi nhánh positioning (+1,7…+8,3/ngày toàn đội ≈ +1,5–7% trên nền ~113) —
**cơ chế tất yếu**: đi nhiều hơn ⇒ tốn pin hơn. Chờ-đổi-pin **không tăng** (ns, B3w còn âm),
tức chưa thấy dồn trạm. Theo LUẬT hiện hành: **veto 9 FAIL ⇒ vẫn KHÔNG bật** — không vặn tiêu
chí giữa trận (đúng nguyên tắc đã giữ ở Q-10). Câu hỏi lên Cường: **Q-12** — sửa veto 9 theo
mẫu (b) (*"đổi pin được tăng nếu chờ-đổi-pin không tăng SIG VÀ tổng payout đội tăng SIG"*)
hay giữ nguyên.

### H4 (swap non sau reorder SWAP-trước-REST): lành tính trên estimator không bias

B0: swaps +4,7 SIG nhưng chờ đổi pin ns và payout cá nhân/đội ns ⇒ chưa thấy thiệt hại đo được.
Giữ theo dõi ở lượt đo sau; không hành động.

## 4. Phán quyết ĐA-08 (tiêu chí 1 mới) — B3w

| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | mean Δpayout mọi tài xế > 0 CI loại 0 | ✅ **+5.027 SIG** (P4 subgroup: ns — không hại, chưa chứng minh lợi) |
| 2–3 | served / hết hạn | ✅ đều CẢI THIỆN SIG |
| 4 | Gini không tăng | ✅ (−0,0053 ns) |
| 5 | HHI [VETO] | ✅ GIẢM SIG |
| 6 | realism | ✅ 633 passed |
| 7 | tắt cờ = cũ | ✅ bit-identical test |
| 8 | km rỗng [veto (b)] | ✅ PASS (+452k đội SIG) |
| 9 | đổi pin [VETO nguyên bản] | ❌ +2,6 SIG ⇒ **chưa được bật** — chờ Q-12 |

## Files

`src/gsm_sim/parallel.py` · `tests/test_evaluator_unbiased.py` (4) · banner CORRECTED trên
UPDATE-075/078/081/084 · artifact `24-*`.

## Kiểm chứng

TDD đỏ trước (2 đỏ thật + 1 xanh-rỗng tự bắt và vá) · mutation ME1 · placebo-zero · suite 633 ·
180 run CRN · view argmax in kèm có nhãn để so bias trực tiếp (−35,5k vs −466đ trên cùng B0).

## Visual verification

`BLOCKED` — gộp V-17; thêm: tab A/B của khu Mô phỏng cần đọc cohort mean thay vì single-driver
(nợ UI, ghi D-UI-03 vào DEFERRED nếu Cường đồng ý).

## Adversarial self-review / flaws found

1. **Veto 9 fail bị phát hiện SAU khi veto 8 đã được sửa** — hai veto cùng mẫu lỗi (trừng phạt
   cơ chế thay vì trừng phạt tác hại). Lẽ ra khi Q-10 mở veto 8 tôi phải rà luôn 9. Ghi nhận.
2. **P4 subgroup thiếu power** — "tách theo archetype" mới ở mức BÁO CÁO, chưa đủ mẫu để làm
   TIÊU CHÍ per-archetype. Cần quyết định: tiêu chí 1 đọc mean_all (như bảng trên) hay đòi từng
   archetype không âm SIG (chặt hơn nhiều, cần n lớn).
3. Placebo test chỉ canh no-op; chưa có test tự động cho BIAS argmax (chỉ có nhãn + diagnostic
   script) — bias là tính chất thống kê, khó unit-test rẻ.
4. `payout_mean_all` gộp mọi archetype kể cả P3/P5 ít nghe lời — hiệu ứng thật trên người NGHE
   có thể lớn hơn con số pha loãng này (adherence-weighted view là việc sau).

## ⏳ Nhắc PENDING-REVIEW

**Q-12 MỚI** (veto đổi pin — xem §3.3). V-01..V-17 chờ. Q-03/Q-04/Q-07/B-02 treo.
