# Audit LỚP NGUYÊN NHÂN GỐC — 2026-08-07

> Cường: *"lên plan để vào todo cycle làm hết, phải nghiên cứu, brainstorm, đọc kỹ tài liệu, công thức,
> logic, code tìm root cause thật TRƯỚC KHI trình plan, nhớ phải docs"*.

## Giả thuyết trung tâm của vòng này

Hai ngày qua tôi tìm ra **>20 nợ** rời rạc (`D-ADV-01..06`, `D-SIM-K6/K7/K8`, `D-M3-19/20/21`,
`B1..B5`, 12 finding `mm-04`/`mm-07`…). Nhìn lại, chúng **lặp lại vài khuôn**:

| lớp | mô tả | thực thể đã biết |
| --- | --- | --- |
| **L1 — nhiều quy ước cho một sự thật** | một tầng **tự tính** đại lượng mà engine đã sở hữu, bằng công thức khác | `D-M3-17` (UI tính tầm pin ≠ engine) · `D-ADV-04` (mẫu số bucket S1, **đường sản phẩm**) · `D-ADV-06` (sổ pin solver ước cao 24%) · `S2-6` |
| **L2 — test ghim VÔ HIỆU** | assertion đúng chữ, nhưng **fixture suy biến** làm nó không kiểm được tính chất nào | `S2-1` (`_required_rest(B=6)=0` ⇒ Δ≡0) · `ADV-01` test (fixture `exp_trips=1,000` chằn) · `test_rest_when_zero_demand` (chỉ assert `!= ONLINE`) · `R-2` (rail chết vẫn tính là 1/3 lan can) |
| **L3 — cơ chế MỒ CÔI** | cờ/khoá/hàm/solver **không có consumer sống**, nhưng vẫn hiện diện như thể sống | `B5` (slider dashboard → `candidate_ring_k` chết) · `sp_end_only` (code chết) · `S3`/`S9` (0 caller) · `S4 swap_window` (producer truyền `[]`) |
| **L4 — cổng đặt SAI VỊ TRÍ trong chuỗi** | cổng đúng nội dung nhưng đặt trước/sau bước sai ⇒ tác dụng phụ im lặng | `D-M3-20` (rút RNG **trước** cadence/coin) · `B2` (cooldown kiểm **sau** Hungarian, `continue` không lui ứng viên) · `D-ADV-02` (cổng đọc thước cũ) |
| **L5 — world zero-cost làm cả HỌ kênh trơ** | `cash_cost=0`/`swap_fee=0` ⇒ mọi kênh chi-phí mất phanh | `D-E4-01` · `ADV-01` · `E-05` · `S2-4` (cầu=0 ⇒ kế hoạch TOÀN SWAP) |
| **L6 — hiệu chỉnh BÙ cho khuyết tật** | tham số world bị điều chỉnh để che một defect, thay vì sửa defect | đội **74→90** bù cho shortlist hẹp (`UPDATE-176/177`: k=8 trội **cả 7 chỉ số** ở n=100) |

**Nếu giả thuyết đúng** thì kế hoạch nên **sửa LỚP** (một fix + một cổng chặn tái diễn cho mỗi lớp), thay
vì sửa 20 triệu chứng rời. **Nếu sai** — tức các nợ độc lập thật — thì phải nói ra và xếp theo giá trị đơn lẻ.

## Nhiệm vụ của vòng audit này

1. **Đọc nốt** 5 artifact chưa ai đọc: `mm-02` (họ shift) · `mm-03` (accept_lift) · `mm-08` (S4) ·
   `mm-09` (penalty/khoán/knapsack) · `mm-10` (idle/anomaly/f3).
2. **Truy TỪNG LỚP tới cùng**: liệt kê **mọi** thực thể của lớp đó trong repo (grep-driven, `file:line`),
   không chỉ những cái đã biết.
3. **Phản biện** giả thuyết lớp (nó có thể là **cách kể chuyện gọn**, không phải cấu trúc thật).
4. **Tổng hợp** thành bản đồ lớp → cycle, có acceptance đo được cho từng cycle.

## Kỷ luật bắt buộc (rút từ hai ngày trả giá)

- **Trích SỐ, không trích NHÃN** — verdict một lượt refuter không ổn định (3/7 đổi khi chạy lại).
- **Số suy-từ-config phải ĐO LẠI trên sim** trước khi vào kết luận (2 lần agent sai độ lớn: 36%→24%,
  bind P4).
- **Khi chạm một con số CÓ SẴN của repo, mở NGUỒN GỐC của nó ra đọc TRƯỚC** (quy tắc này đã cứu 3 lần).
- **Mô hình tĩnh nói về CẤU TRÚC, không nói về KẾT CỤC** (F1 lệch 20× khi đoán kết cục).
- **Đề xuất CÁCH SỬA cũng phải qua phản biện như đề xuất PHÁT HIỆN** (3 lần phương án sửa của tôi bị bác).
- Ranh giới: sức khoẻ **không** vào objective (§1.2b) · số tài chính do rule/analytics · không can thiệp
  dispatch/pricing/đơn cụ thể.

## Artifact

`rc-L1..L6-*.json` (một file mỗi lớp) · `mm-02/03/08/09/10-*.json` (đọc nốt) ·
`pb-L*-refute.json` (phản biện lớp) · `00-BAN-DO-LOP.md` (tổng hợp → plan).
