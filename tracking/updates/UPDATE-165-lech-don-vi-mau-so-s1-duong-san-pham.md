# UPDATE-165 — 🔴 Lệch ĐƠN VỊ mẫu số S1: advisor phán SAI "không kịp" trên ĐƯỜNG SẢN PHẨM (đã reproduce)

- **Ngày:** 2026-08-06
- **Loại:** research (audit math-model, **có reproduce chạy thật**) — chưa sửa code
- **Liên quan:** `mm-06-s1.json` (agent audit) · UPDATE-162/163 (nợ trước) ·
  `PLAN-2026-08-06-cycles-chi-tiet.md` (thêm **Cycle B0**) · `B6-PARITY` (UI chỉ chạy 1/9 solver)
- **Nợ mới:** `D-ADV-04` (sev **CAO — đường sản phẩm**)

## 1. Phát hiện: producer và solver KHÔNG CÙNG ĐƠN VỊ

| Tầng | Làm gì | File |
| --- | --- | --- |
| **Producer** (cả 3 đường) | chia **điểm-của-bucket** cho **giờ online TOÀN NGÀY** | `features/bonus_gap.py:63-64` · `features/from_l1r.py:161` · **`ui/backend/app/adapters/advisor.py:74`** |
| **Solver S1** | tiêu thụ như **điểm/giờ TRONG bucket** — nhân `rate × span` cho **từng giờ** thuộc bucket | `solvers/bonus_feasibility.py:51-52` + `_walk:72,79` |

Vì `giờ_ngày ≥ giờ_trong_bucket`, rate **luôn** bị ước NON, hệ số `oh_ngày / oh_bucket` (peak thường
2–5×). **Ai sai:** ngữ nghĩa của solver bị **test ghim** (`tests/test_bonus_feasibility.py:113-119`:
`hist offpeak=15 ⇒ hours=gap/15`) ⇒ **solver ĐÚNG, producer SAI**. Sửa producer.

## 2. Reproduce — kết quả THẬT (tôi tự chạy lại, không phải đọc code)

Tài xế online 08–18h (10h/ngày × 4 ngày), 60đ peak trong 2h + 60đ offpeak trong 8h.
Hỏi lúc **15:00**, `points_now = 110`, thiếu **50đ**, quỹ giờ **6h**, acceptance 1.0:

```
hist_rate producer: {'offpeak': 6.0, 'peak': 6.0}        ← đúng phải là {peak: 30, offpeak: 7.5}

--- verdict với hist từ PRODUCER (mẫu số = giờ cả ngày) ---
feasible: False | hours_needed: None
infeasible_reason: từ giờ đến hết khung điểm chỉ kiếm thêm được ~42đ < 50đ còn thiếu

--- verdict với rate THẬT (điểm / giờ TRONG bucket) ---
feasible: True | hours_needed: 2.42
```

⇒ **Advisor nói "không với tới" về một mốc thưởng với tới được trong 2,42 giờ.**

## 3. Vì sao đây là nợ nặng nhất tìm được trong audit

**`S1` là solver DUY NHẤT mà đường sản phẩm chạy** (`B6-PARITY`, `ui/.../advisor.py:193-229`) ⇒ lỗi
này **không nằm trong sim**, nó nằm trong **card cho tài xế thật**. Hướng lỗi là **bi quan có hệ
thống**: hệ im lặng hoặc dập hy vọng **đúng lúc lời khuyên có giá trị nhất**. Đối chiếu: mọi nợ khác
tìm được hôm nay đều ở kênh **đang TẮT** hoặc ở tầng đo.

Họ lỗi: `D-M3-17` / `T-046` — *nhiều bản chép một sự thật* (ba producer cùng chép một quy ước sai).
**Chưa từng được ghi nợ ở đâu** (đã grep tracking).

## 4. ⚠ Ràng buộc thi công: PHẢI sửa HAI VẾ CÙNG LÚC

Vế thứ hai là **survivorship**: `bonus_gap.py:56-64` chỉ ghi bucket **CÓ cuốc** (ngày online-mà-trắng-
điểm **biến mất** khỏi mẫu thay vì đóng `0.0`), và `advisor.py:73` có `if p > 0`. Đây là bias **LẠC
QUAN** — **ngược chiều** với vế mẫu số (bi quan). Hai lỗi đang **bù trừ nhau theo tỷ lệ không kiểm
soát** ⇒ **sửa một cái làm số đổi hướng khó hiểu**. Nghịch lý đáng ghi: solver đã học đúng bài
*"lịch sử 0.0 là dữ liệu hợp lệ"* (ADV-05, comment ở `bonus_feasibility.py:47-52`) nhưng **không
producer nào từng sản xuất ra 0.0** — bài học được học ở tầng sai.

## 5. Hệ quả cho kế hoạch

- Thêm **Cycle B0** vào `PLAN-2026-08-06-cycles-chi-tiet.md` với 3 test đỏ-trước + acceptance số.
- **Cycle B (`shift_extend` mù cửa sổ điểm) nay PHỤ THUỘC B0**: `mm-06` issue #4 cho thấy producer
  in-sim đổ **day-average vào CẢ HAI bucket** (`advice_bridge.py:990-992`) ⇒ gọi S1 khi input còn sai
  thì chỉ **chuyển chỗ đặt lỗi**, đúng cái Cường cấm.
- Nợ kèm chưa mở cycle (từ `mm-06`, **chưa phản biện**): verdict `feasible` **nhị phân trên median**
  (không phương sai/CI ⇒ khi `hours_needed ≈ budget` thì P(đạt) ≈ 50% mà report nói "kịp") · ràng buộc
  acceptance kiểm **tĩnh** trong khi policy chấm **luỹ kế cuối ngày** · fallback **1,5 cuốc/giờ phẳng**
  bỏ hour-shape cầu · quỹ giờ coi 100% là giờ kiếm điểm (bỏ downtime đổi pin tất yếu).

## Files bị ảnh hưởng

`tracking/DEFERRED.md` (thêm `D-ADV-04`) · `tracking/PLAN-2026-08-06-cycles-chi-tiet.md` (thêm Cycle B0,
sửa điều kiện Cycle B) · `tracking/updates/UPDATE-165-*.md` · `PROJECT-GRAPH.md`. **Chưa sửa code.**

## Kiểm chứng

- **Chạy thật:** `uv run python <scratchpad>/repro_s1_denominator.py` → output nguyên văn ở §2.
- **Tôi tự đọc cả bốn chỗ:** `bonus_feasibility.py:40-85` (solver `_hour_rate` + `_walk`),
  `bonus_gap.py:50-71` (producer L1), `ui/backend/app/adapters/advisor.py:60-79` (producer sản phẩm).
- **Chưa kiểm chứng:** `from_l1r.py:161` tôi **chưa mở** (tin agent cho chỗ này — cần kiểm khi sửa) ·
  tần suất thực tế lỗi bind trên dữ liệu mock hiện hành (chưa đo bảng feasible trước/sau) · 5 nợ kèm
  ở §5 **chưa phản biện**.

## Visual

`NOT_APPLICABLE` (chưa sửa code). ⚠ Khi sửa B0 thì **card F0/F1 của web demo sẽ đổi nội dung** ⇒ lúc đó
là **meaningful UI update** ⇒ phải vào visual gate (V-mới), không được gộp im lặng vào V-31.

## Adversarial self-review / flaws found

1. **Reproduce là của agent, tôi chạy lại — nhưng script cũng do agent viết.** Nó gọi đúng hàm
   production (`derive_bonus_gap_input → solve`), tôi đã đọc solver và producer để xác nhận cơ chế.
   Vẫn cần một refuter soi: *"có test nào ghim quy ước PRODUCER (không phải solver) không?"* — nếu có
   thì đây là hai-quy-ước-có-chủ-đích, không phải bug một phía.
2. Sửa xong advisor **lạc quan hơn** ⇒ rủi ro mới: khuyên bám mốc rồi **không tới** (vì forecast vẫn là
   median). Không được báo "advisor tốt hơn" chỉ vì bớt im lặng — phải đo cả chiều đó.
3. Con số `{peak: 30, offpeak: 7.5}` là **của ví dụ trong script**, không phải hằng của hệ. Đừng trích
   như tham số hệ thống.
4. Tôi chưa đo **tần suất**: bao nhiêu % lượt hỏi thật bị flip verdict? Chưa có số này thì **không**
   được nói "advisor đang sai với X% tài xế".

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/` — đang sống) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
