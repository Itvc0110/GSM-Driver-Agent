# UPDATE-176 — Chuỗi hiệu chỉnh: sửa dispatcher là **cải thiện KHÔNG đánh đổi**, còn dư cung chỉ **một phần** là bù

- **Ngày:** 2026-08-07
- **Loại:** research (đo 3 arm, advisor TẮT để cô lập world) — **0 dòng code/config thay đổi**
- **Artifact:** `research/audit/2026-08-06-root-cause-idle/g1-chuoi-hieu-chinh.py` + `.json`
- **Đặt hàng:** Cường 2026-08-07 — *"cuốc được nhận/hoàn thành rất cao, chờ ghép đơn thực tế không cao như
  sim; advisor tối ưu được thời gian thì thời gian đó phải dùng để kiếm tiền — fail này xử lý chưa?"*

## 1. Giả thuyết tôi mang đi kiểm

> Khuyết tật dispatcher (shortlist **2,22 km** < bán kính ETA-khả-thi **3,14 km**) → hụt phục vụ →
> **hiệu chỉnh bơm đội 74→90** để đạt `served_rate` → **dư cung** → giá trị biên phút rỗi ≈ 0 → mọi kênh
> advisor tiết-kiệm-thời-gian trượt cổng tiền.

Nếu đúng: nới shortlist sẽ **tự** nâng served, cho phép **hạ đội** mà vẫn giữ served.

## 2. Kết quả (5 seed, advisor TẮT ở cả ba arm)

| arm | served_rate | hết hạn/ngày | **idle %** online | trips/tài xế | payout/tài xế |
| --- | --- | --- | --- | --- | --- |
| **A0** k=6, n=90 *(nguyên trạng)* | 0,8304 | 204,6 | **33,6%** | 10,57 | 250.552đ |
| **A1** k=8, n=90 *(chỉ nới shortlist)* | **0,8700** | **157,0** | 31,5% | 10,97 | 258.418đ |
| **A2** k=8, n=74 *(nới + hạ đội)* | 0,8036 | 237,2 | **26,4%** | **12,43** | **290.944đ** |

## 3. Ba kết luận

### ✅ (a) Sửa dispatcher là **cải thiện KHÔNG ĐÁNH ĐỔI** — A1 trội hơn A0 trên **mọi** chỉ số tôi đo
`served` **+3,97đp** · hết hạn **−47,6/ngày** · idle −2,1đp · trips +0,40 · payout **+7.866đ/tài xế**.
Không một chỉ số nào xấu đi. Khớp sweep 12-seed sẵn có trong config (`0,761→0,788`, `233→196`).
⇒ **~48 đơn/ngày đang chết vì một vòng lọc hình học**, không vì thiếu người.

### 🔴 (b) Giả thuyết của tôi **BỊ LÀM YẾU**: dư cung **không thuần** là bù cho dispatcher
Hạ đội về 74 (kèm k=8) làm `served` **tụt 2,68đp** so với nền ⇒ phần *"cơ cấu"* mà `D-SIM-01` nói
(**cầu một quận**) là **THẬT ở mức đáng kể**. Tôi **không** được nói *"bơm đội chỉ để che bug"*.

### ⭐ (c) Nhưng lộ ra thứ giá trị hơn: **config đang ngồi trên một BIÊN ĐÁNH ĐỔI, và nó chọn một đầu**
A2 đổi **−2,68đp served (khách)** lấy **+16,1% payout/tài xế · +17,6% trips/tài xế · idle 33,6%→26,4%**.
Nghĩa là **tồn tại một điểm hiệu chỉnh** nơi realism CÁ NHÂN tốt hơn hẳn **và** phút rỗi đủ khan để kênh
tiết-kiệm-thời-gian **có chỗ tạo tiền** — đúng thế giới mà Cường mô tả (chờ ghép đơn không cao).
**Đây là quyết định chính sách của Cường**, không phải của agent: *ưu tiên khách (served) hay tài xế
(thu nhập + realism)?*

⇒ **Câu trả lời cho "fail xử lý chưa": CHƯA — và nó KHÔNG phải fail của advisor.** Advisor trượt cổng tiền
vì **điểm hiệu chỉnh của world**, cộng một khuyết tật dispatcher **~48 đơn/ngày** chưa sửa.

## 4. Q-07 — điều đang chặn cải thiện không-đánh-đổi (tôi tự bắt lỗi phép đo của mình)

Tôi đo `|accept(k=8) − accept(k=6)|` → max **2,36đp** và **định** kết luận *"Q-07 không chặn k=8"*.
**Sai đại lượng:** Q-07 so `realized accept` với **`accept_base` trong config**, không so hai giá trị k.
Bảng **12 seed** trong chính config mới là nguồn đúng:

| k | served | hết hạn | lệch lớn nhất vs `accept_base` |
| --- | --- | --- | --- |
| 6 | 0,761 | 233 | **P7 −0,042 ✅** (đã **sát** ngưỡng) |
| 7 | 0,778 | 211 | P7 −0,053 ❌ |
| **8** | 0,788 | **196** | **P7 −0,057 ❌** |
| 12 | 0,789 | 195 | P7 −0,067 ❌ |

Số của tôi **khớp** bảng đó: P7 đổi **−1,66đp** khi k=6→8, tương ứng −4,2 → −5,7. ⇒ **Q-07 CHẶN THẬT.**
Nhưng có một chi tiết đáng để Cường biết: ở **k=6, P7 ĐÃ ở −4,2đp** — tức điểm hiện tại **đang sát mép**
dung sai, nên dung sai này **không** đang bảo vệ nhiều dư địa; câu hỏi thật là *`accept_base` của P7 có
được hiệu chỉnh đúng không*. ⚠ Và **không được nới dung sai test để đi tiếp** — chính comment config gọi
đó là **che khuyết tật**.

## Kiểm chứng

- 3 arm × 5 seed, **advisor TẮT ở cả ba** ⇒ cô lập hiệu chỉnh world, không lẫn advisor.
- Chỉ đổi hai khoá qua `deepcopy` in-memory (`candidate_ring_k_max`, `actors.n`) — **không sửa file config**.
- **Chưa kiểm chứng:** n=5 seed ⇒ **không có CI**; các Δ ở đây là **hướng + bậc**, không phải số chốt.
  Muốn quyết bằng nó thì phải chạy **n≥30** (và ≥100 nếu so biến thể-vs-biến thể). · Chưa đo **Gini/HHI/đơn
  chết theo giờ** ở A2 (A2 hạ đội ⇒ có thể xấu equity mà bảng này không thấy). · Chưa đo tác động lên
  **veto sức khoẻ** khi trips/tài xế tăng 17,6%.
- Suite: **không chạy** — 0 dòng code thay đổi.

## Visual
`NOT_APPLICABLE` (research). ⚠ Nếu Cường chọn đổi điểm hiệu chỉnh thì đó là **meaningful sim update** ⇒
visual gate bắt buộc.

## Adversarial self-review / flaws found

1. **Giả thuyết của tôi bị làm yếu bởi chính phép đo của tôi** — lần thứ sáu trong hai ngày. Nhưng lần này
   nó **đổi ra một kết luận TỐT HƠN**: không phải *"bơm đội che bug"* mà *"tồn tại một biên đánh đổi và
   config chọn đầu ưu-tiên-khách"*. Đó là câu Cường quyết được; câu cũ thì không.
2. **Tôi lại suýt trích một con số trả lời SAI câu hỏi** (2,36đp) — bắt được nhờ đi tìm định nghĩa của
   Q-07 trước khi viết. Đúng quy tắc vừa rút ra ở `UPDATE-173`: *khi chạm một con số CÓ SẴN của repo,
   mở nguồn của nó ra đọc TRƯỚC.* Quy tắc đó vừa cứu tôi một lần.
3. A2 (hạ đội) **chưa** được kiểm equity/sức khoẻ ⇒ tôi **không** đề xuất nó, chỉ trình bày như một điểm
   trên biên. Trình bày một điểm chưa kiểm đủ như "phương án tốt hơn" sẽ là lặp lại lỗi `D-ADV-03`.
4. Tôi **không** đề xuất nới dung sai Q-07 — chính config đã gọi đó là che khuyết tật, và tôi đồng ý.

## ⏳ Nhắc PENDING-REVIEW

**Q-07 nay là quyết định có ĐÒN BẨY CAO NHẤT** của cả chương trình: nó chặn một cải thiện
**không-đánh-đổi ~48 đơn/ngày**. · **V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/09/10/13 · **amendment ĐA-08** (nay có phương án thứ hai: **đổi điểm hiệu chỉnh** thay vì nới cổng)
— gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
