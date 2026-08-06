# UPDATE-171 — Trả nợ artifact phản biện (7/7) và **BA verdict ĐỔI** khi chạy lại

- **Ngày:** 2026-08-07
- **Loại:** trả nợ tái tạo + đính chính hai nợ theo số mới — **0 dòng code sản phẩm/sim thay đổi**
- **Đóng:** cảnh báo *"6/7 artifact không tồn tại ⇒ CẤM trích số"* của `UPDATE-166` §3

## 1. Nợ đã trả

| Nợ | Trạng thái |
| --- | --- |
| 6/7 artifact `pb-*` không tồn tại (tôi lỡ chạy workflow trong **plan mode** nên agent bị chặn ghi) | ✅ **7/7 có trên đĩa** — kèm cả script probe của refuter (`pb-04-probe-88-luot.py`, `pb-04-verify-doc-lap.py`, `pb-04-raw-88-luot.txt`) ⇒ **tái tạo được** |
| `mm-04`/`mm-07` chỉ có bản `-STAGED.md` | ✅ đã trích thành **JSON hợp lệ** (`UPDATE-169`) |
| Cột khoảng cách của F1 dùng PROXY | ✅ đã đo thật (`UPDATE-169`, F2) |
| Con số streak `~17,2′` là DERIVED | ✅ đã đo thật (`UPDATE-170`, F4: p50 **8,0′**, n=2 chỉ **2,13%**) |

## 2. 🔴 Phát hiện phương pháp: MỘT lượt refuter KHÔNG phải oracle

Chạy lại đúng cùng prompt cho **ba verdict khác** lần đầu:

| nợ · góc soi | lần 1 (relay) | lần 2 (có artifact) |
| --- | --- | --- |
| `D-ADV-02` **cách sửa** | PLAUSIBLE | **REFUTED** |
| `D-M3-21` tần suất bind | PLAUSIBLE | **REFUTED** |
| `D-ADV-01` thiết kế/bug | CONFIRMED | **PLAUSIBLE** |

Bốn verdict còn lại giữ nguyên. ⇒ **Quy tắc mới cho chính tôi:** verdict của một lượt refuter là **bằng
chứng có phương sai**, không phải phán quyết. Cái đáng tin là **con số + evidence file:line trong
artifact**, không phải nhãn CONFIRMED/REFUTED. Vì vậy từ nay: **trích số, không trích nhãn.**

## 3. `D-M3-21` — tiền đề ĐÚNG (mạnh hơn tôi nói), nhưng suy luận của tôi SAI cả ba vế

**Còn đứng, và mạnh hơn:** bind gần như **phổ quát** cho P4 — **96,25%** ngày arm A (CI95 [94,38; 98,12]);
vế ràng buộc là `gross < 350k`, còn **tenure ≤ 90 và online ≥ 6h KHÔNG BAO GIỜ chặn** (100%/100%; online
median **527′ = 8,8h**) ⇒ lo ngại của tôi *"P4 part-time nên online < 6h"* **sai**. Đại số cũng đúng ở
**vế trips-payout** (biên từ một cuốc thêm = chính xác 0).

**Bị bác — cả ba hệ quả tôi suy ra:**
1. *"payout HẰNG"* → **27 giá trị payout phân biệt** trong 154 ngày bind, dải 262.498…352.500đ (+90.002đ).
2. *"⇒ guard 1b zero power"* → Δpayout ≠ 0 ở **125/150** ngày-cặp cùng bind; thêm **6,25%** ngày
   **bind-FLIP**; và công suất: `sd = 3.153đ` (n=10) ⇒ n=100 cho **MDE95 ≈ 620đ**. Đóng đinh:
   **UPDATE-160 đã bắt P1 −3.863đ ÂM-SIG bằng CHÍNH guard này.**
3. *"payout_mean_all bị kéo về 0"* → Δ = **+5.352đ [+1.881; +8.955] SIG DƯƠNG**.

**🔑 Phát biểu đúng (thay hoàn toàn bản cũ):** rủi ro **không** phải *"guard 1b không đo được gì"* mà là
***"guard 1b đo PAYOUT nên khoản THIẾU HỤT GROSS của P4 bị bảo hiểm che đi"*** — `Δgross ≠ 0` ở
**150/150** ngày-cặp nhưng **~2/3 biên độ** bị topup trung hoà ⇒ **guard UNDER-REPORT tác hại lên gross**.
⇒ Cycle tách `Δgross` cạnh `Δpayout` **vẫn đúng hướng**, nhưng **lý do đổi**: không phải "khôi phục power
đã mất" mà là "thôi under-report".

## 4. `D-ADV-01` — hạ xuống `PLAUSIBLE`, và MỘT fix tôi đề xuất là NO-OP

- **Chân 2 (+10 phẳng) + chân 3 (không `min_gain`): CONFIRMED, mạnh hơn** — **255/421 = 60,6%** lượt gán
  bị stagger ở **5 seed** (vòng trước 56% ở 3 seed).
- **Chân 4 (không TTL): đúng chữ nhưng RỖNG** — **0/179** lượt vượt biên bucket, **và** `view()` cache
  theo bucket khiến bản vá *"re-validate"* **không huỷ được plan nào** ⇒ **fix (d) của tôi là NO-OP, bỏ
  khỏi kế hoạch**.
- **Kết luận *"thắng DƯỚI trần"* chưa có bằng chứng bằng đồng**, và đường km→tiền **bị
  `cash_cost_vnd_per_km: 0` chặn ngay trong arm đã đo** ⇒ **112,8 km thừa KHÔNG quy được thành tiền ở
  config hiện tại** (đúng họ `D-E4-01` world zero-cost). ⇒ Muốn nói bằng tiền thì **phải chạy arm có giá**.

## Kiểm chứng

- 7/7 artifact `pb-*.json` trên đĩa + 3 file probe/raw của `pb-04` ⇒ số **tái tạo được**.
- Tôi **đọc trực tiếp** `pb-05` và `pb-06` (hai cái đổi verdict và chạm nợ tôi đã ghi) để sửa DEFERRED
  theo **số**, không theo nhãn.
- **Chưa kiểm chứng:** `pb-01/02/03/04/07` tôi **chưa đọc toàn văn** lần này (chỉ đọc verdict + so với
  lần 1) ⇒ nếu cần trích số của chúng thì phải mở artifact ra đọc trước.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim thay đổi.

## Visual
`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. **Bài học lớn nhất của cả cycle:** trong một ngày, **năm** kết luận của tôi bị chính phép đo tiếp theo
   sửa (`D-ADV-03` bác · claim "hai ô bẫy" yếu · giả thuyết `home_cell` bác · `D-M3-21` suy luận bác ·
   `D-ADV-01` hạ hạng). Điểm chung: tôi phát biểu **cơ chế nghe hợp lý** trước khi có số. Quy tắc đã ghi:
   **trích SỐ, không trích NHÃN; và mô hình tĩnh chỉ nói về CẤU TRÚC, không nói về KẾT CỤC.**
2. Verdict **không ổn định giữa hai lượt** ⇒ mọi chỗ tôi từng viết *"phản biện CONFIRMED"* phải đọc là
   *"một lượt refuter nói CONFIRMED"*. Đã sửa cách viết ở `UPDATE-166` §2b.
3. Tôi vẫn **chưa** trả lời được câu `UNRESOLVED` chính (vì sao đội xe vào lưu vực xa) — đã loại được ba
   ứng viên bằng số, còn lại phải **đo trong run thật**. Không đoán thêm.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (card F0/F1 đổi nội dung — blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13 · **amendment ĐA-08 kênh phía-cung** — gom đủ ở
`tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
