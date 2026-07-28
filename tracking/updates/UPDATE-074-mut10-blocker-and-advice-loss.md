# UPDATE-074 — Gỡ BLOCKER-R5-MUT10 + truy nguyên "advisor làm ra ít tiền hơn tự làm"

Ngày: 2026-07-27 · Track: R5 (double-check) + AUDIT · Sau `7739b3c`.

## 1. BLOCKER-R5-MUT10 — mutation lọt vào repo do LỖI CỦA TÔI

**Sự việc**: một reviewer agent chạy mutation-test trên `shift_dp.py` rồi **bị quota giết trước
khi khôi phục file**. Ngay sau đó tôi commit fix fleet-label bằng `git add -A` → mutation bị cuốn
vào commit `7739b3c` và nằm trong HEAD:

```python
def _soc_cost(params):
    bucket_min = int(params.get("bucket_min", 30))
    return int(params["soc_cost_per_bucket"])   # MUT10: bo scale bucket_min   ← MUTATION
```

**Hệ quả**: với `bucket_min=60` (đúng giá trị producer sim/l1r dùng), DP tưởng pin dùng được
**gấp đôi** thực tế ⇒ lịch SWAP sai. Và mutation **SỐNG SÓT toàn bộ suite** — nghĩa là không test
nào phủ `bucket_min ≠ 30`.

**Đã làm**:
- Khôi phục `_soc_cost` về `max(1, round(soc_cost_per_bucket * bucket_min / 30))`, kèm docstring
  ghi lại sự việc để không ai tưởng đó là code cố ý.
- **2 regression test mới** (`tests/test_shift_dp.py`): `test_soc_cost_scales_with_bucket_min`
  (30'→1, 60'→2, 120'→4, không bao giờ 0) và `test_soc_budget_binds_at_60min_buckets` (hệ quả
  hành vi: bucket dài hơn phải cần SWAP không ít hơn).
- **Chứng minh test có giá trị**: re-apply MUT10 → `1 failed` ✓; restore → `19 passed`.

**Bài học quy trình (tự áp)**: KHÔNG `git add -A` khi có agent nền đang chạy mutation-test. Từ
nay stage theo đường dẫn cụ thể, và `git diff` trước mỗi commit trong lúc có agent chạy.

## 2. Trả lời câu hỏi của Cường: "làm theo Advisor ra tiền ÍT hơn tự làm"

**Tái lập được — Cường đúng.** 5 seed CRN: **LỖ 3/5, LỜI 1/5, HOÀ 1/5** (bảng đầy đủ trong
`research/audit/2026-07-27-current-state/06-why-advice-loses-money.md`).

Cơ chế **ngược với giả thuyết trực giác**: advisor KHÔNG làm tài xế nhận cuốc xấu. Số đo seed 1000
cho thấy B nhận cuốc **gần hơn, đắt hơn** — nhưng bị **chào ít đơn hơn (18→12)** và **tốn gấp 2,3
lần thời gian đổi pin (62→144 phút)**.

**Ablation từng kênh (3 seed)** chỉ đích danh thủ phạm:

| kênh | Δ payout | kết luận |
|---|---|---|
| **`accept_lift`** | **−104.895đ** | thủ phạm duy nhất |
| `shift_extend` | +26.953đ | có lợi |
| `rest_window` · `shift_plan` | 0 | INERT ở config này |

**Vì sao gate không chặn**: S1 `bonus_feasibility` ĐÃ được nối (D-SIM-09) và kết luận FEASIBLE lúc
6h16 sáng là **hợp lý theo dữ liệu lúc đó**. Lỗ hổng nằm ở mô hình: S1 coi năng suất (điểm/giờ) là
**hằng số ngoại sinh**, trong khi chính hành động do advice tạo ra lại **làm giảm năng suất tương
lai** (cạn pin, trôi khỏi vùng cầu). Hệ không có vòng phản hồi này ⇒ chi phí cơ hội vô hình.

Đây là **D-SIM-05** ở dạng đã đo lượng hoá, nhưng nguyên nhân sâu hơn ghi chép cũ.

**Khuyến nghị ngay**: **không bật `accept_lift` mặc định trong bất kỳ demo nào cho stakeholder**
cho tới khi có ĐA-07 (đưa chi phí cơ hội / ràng buộc SOC-vị thế vào điều kiện kênh). Đề xuất
ĐA-07 nằm trong hồ sơ §5.

## 3. Kiểm chứng

- `tests/test_shift_dp.py`: **19 passed**; mutation re-apply → đỏ đúng chỗ.
- Full suite: **đang chạy** tại thời điểm viết (`fullsuite_mut10fix.txt`) — số sẽ ghi bổ sung,
  KHÔNG tuyên bố xanh trước khi đọc output.
- Ablation/tái lập: engine trực tiếp (`run_pair` CRN), không qua UI — loại trừ nhiễu tầng web.
- **Giới hạn trung thực**: 5 seed (bảng) và 3 seed (ablation) đủ chỉ ra CƠ CHẾ, **chưa đủ kết luận
  phân phối** (chuẩn ≥30 seed). Chưa kiểm archetype khác P4.

## 4. Trạng thái R5-B (double-check đa-agent)

5 reviewer chạy được 3: adapter (14 finding — F-01 fleet label đã fix ở `7739b3c`), sim-router
(14 finding), cards+playback (23 finding). **2 reviewer chết vì quota tháng**: fix-batches và
tests+docs — chính reviewer tests+docs là nơi sinh ra MUT10. Findings đã persist tại
`research/audit/2026-07-27-r5-selfcheck/`. **Chưa xử lý hết** — không tuyên bố R5 xong.

---
**⏳ PENDING-REVIEW (nhắc lại đầy đủ):** V-01..V-09 · **V-10** (app + cards + khu Mô phỏng) ·
Q-03 (corpus Khánh) · **ĐA-01/02/03 đã duyệt — chờ implement**; **ĐA-04/05/06 chờ Cường duyệt
hướng**; **ĐA-07 (mới) — chi phí cơ hội cho accept_lift, chờ Cường xem hồ sơ 06**.
