# UPDATE-156 — E4/E-03 kênh đổi-pin-sớm: code XONG; đo n=30 — payout ns, một quan sát CHƯA GIẢI THÍCH

- **Ngày:** 2026-08-06
- **Loại:** feature (kênh mới, mặc định TẮT) + research (đo quan sát)
- **Liên quan:** UPDATE-151 r03 SWAP-06 · UPDATE-155 (bài học kênh thời-gian) · plan E4

## Đã làm

Kênh `swap_early` (SIM-ONLY, mặc định TẮT): dồn lần đổi pin TẤT YẾU (SOC ∈ (ngưỡng, +15]) vào lúc
RẺ — rảnh liên tục ≥10′ + trạm vắng (queue ≤ 1, có pin sẵn). Mọi điều kiện đọc trạng thái HIỆN
TẠI (không dự báo, không rò).

- Topic `swap_early` vào registry **MEASURED** (cùng lý lẽ `energy`: tác hại pin có kênh mô hình
  hoá — không tạo tỷ giá sức-khoẻ↔tiền) — 34 test registry xanh.
- `advice_bridge.check_swap_early` (6 rail, mọi nhánh có reason) + coin/cadence/drain mẫu số
  (D-M3-01) · world: chỉ đè WAIT, trước positioning, **gate cờ TRƯỚC `choose_station`** (kênh
  tắt = 0 draw RNG — CRN) · config 3 khoá mới có reader (flag-wired xanh).
- 🐛 Bug bắt khi test tích hợp: dùng nhầm `grid.stations` (bản GEO tĩnh, không có queue/pin)
  thay vì `self.stations` (Station sống — đúng danh sách `_do_charge` dùng). Sửa + comment.
- 14 test (`tests/test_e4_e03_swap_early.py`) — **52 passed** cùng cổng.

## Đo 30 seed (coverage=all, cô lập 1 cơ chế) — `research/audit/2026-08-06-e2/e03-swapearly-30.json`

| metric | Δ (B−A) | đọc |
| --- | --- | --- |
| `payout_mean_all` | −614,6 [−2.449; +1.184] | **ns** |
| `swap_wait_mean` | +0,14 [−0,65; +0,90] | ns — **nền chỉ 5,69′**: chi phí kênh định né vốn nhỏ ở world này |
| `charge_min_p90_F_swap` · `served` · `gini` | ns | — |
| `rest_min_total` (một chiều, quan sát) | **+279,1′ [+212; +347]** (3.648 → 3.927, **+7,7%**) | 🔴 **CHƯA GIẢI THÍCH ĐƯỢC** — xem dưới |
| `work_span_p90` | −0,6 ns | — |

### 🔴 Quan sát +7,7% nghỉ — kỷ luật đọc

CI không chứa 0 nhưng tôi **không có cơ chế** giải thích vì sao đổi-pin-sớm làm tài xế NGHỈ nhiều
hơn. Ứng viên: (a) trôi quỹ đạo D-SIM-K3 (mỗi lượt swap sớm dịch mọi draw phía sau — kênh này đổi
hành vi ở nhiều actor nên phân kỳ rộng); (b) cơ chế thật qua `meals/fatigue` reroll ở decision
point mới. Theo đúng bài học UPDATE-140 (*"đọc nhánh `if` trước, khai thác số sau"*): **KHÔNG kể
chuyện** — ghi nợ `D-E4-03`: nếu định bật kênh này thì PHẢI root-cause quan sát này trước
(reproduce → đọc nhánh → phép kiểm phân biệt kiểu FIX-PRE).

## Verdict kênh (n=30 — thăm dò)

**Giữ TẮT.** Không thấy hại rõ, không thấy lợi: giá trị kỳ vọng của kênh là né hàng đợi/stranded,
mà world hiện tải trạm thấp (wait nền 5,7′, `swap_failed` hiếm). Đúng mẫu E-05/ADV-01: **kênh chỉ
có giá trị khi chi phí nó né TỒN TẠI trong world**. Nợ `D-E4-02`: sweep khan-hiếm-trạm (giảm số
trạm / event day) nếu Cường muốn nghiên cứu tiếp — kèm prereg nếu định claim.

## 🔴 Meta-finding của E4 sau 2 kênh (nối UPDATE-155)

Ba điểm dữ liệu (ADV-01-in-sim, E-05, E-03) hội tụ: trong world hiện tại (cầu-chặn, chi phí 0,
trạm rảnh), **giá trị advisor tập trung ở họ VỊ TRÍ** (+4,5k đã đo; mất-vì-không-nghe +3,5k).
⇒ Phần còn lại của E4 nên dồn vào **E-01 station-choice + E-07 zone-rotation** (họ vị trí,
SIM-ONLY như Cường duyệt) thay vì E-02 meal-timing (cùng cơ chế demand-timing với rest_window —
kênh đã đo −429 ns). E-02 tụt xuống cuối danh sách.

## Kiểm chứng
52 passed (E-03+E-05+flag-wired+registry) · OFF bit-identical (test tích hợp) · phép đo 2,8′.

## Visual
`NOT_APPLICABLE` — kênh TẮT mặc định. Gom V-31.

## Follow-up
E-01 station-choice (ưu tiên 1 mới) → E-07 → E5 lọc test → oracle config đầy đủ → V-31.
Nợ mới: `D-E4-02` (sweep khan hiếm trạm) · `D-E4-03` (root-cause +7,7% nghỉ trước khi bật).
