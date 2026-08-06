# UPDATE-173 — 🔴 RÚT LẠI một "đính chính" của chính tôi: **65,3% KHÔNG sai**, tôi mới sai

- **Ngày:** 2026-08-07
- **Loại:** đính chính của đính chính (docs) + trả nợ index PROJECT-GRAPH — **0 dòng code thay đổi**
- **Sửa:** `UPDATE-172` §3 · `DEFERRED.md` hàng `D-ADV-03`

## 1. Chuyện gì đã xảy ra

`UPDATE-172` §3 tôi viết: *"**65,3% cuốc trả ngoài lõi** là SAI; đo được **56,1–56,5%**; 65,3% (chính xác
64,65%) là mức ĐƠN SINH"* — dựa vào con số của refuter `pb-07`.

**Tôi đi kiểm nguồn của 65,3% và thấy nó có gốc thật:** `UPDATE-083` — bảng hiệu chỉnh `drop_demand_alpha`,
hàng **α = 0,4**, cột *"trả ngoài lõi"* = **65,3%**; và `drop_demand_alpha` trong config **hiện vẫn là
0,4**. Nghĩa là 65,3% **không** phải số tôi bịa hay lấy sai chỗ — nó là số hiệu chỉnh của repo.

**Nên tôi tự đo** (arm A, 5 seed 1000–1004, `pilot_dongda`):

| đại lượng | tôi đo | n |
| --- | --- | --- |
| **đơn SINH** có drop ngoài lõi | **64,4%** | 3.883/6.029 |
| **cuốc HOÀN THÀNH** (`trip_rated`, log tại `order.drop_cell` — `world.py:776`) có drop ngoài lõi | **64,6%** | 2.329/3.608 |

**Cả hai khớp 65,3%.** ⇒ **`65,3%` KHÔNG SAI**, và **`56,1–56,5%` là số tôi KHÔNG tái tạo được**.

## 2. Kết luận và lệnh

- **RÚT LẠI** đính chính ở `UPDATE-172` §3 (đã thay bằng banner rút-lại, giữ bản gốc để đối chiếu).
- **`56,1–56,5%` CẤM TRÍCH** cho tới khi có ai tái tạo được. Nó nằm trong `pb-07-dadv03-vi-sao-that-bai.json`
  như evidence của refuter, nhưng **tôi không xác nhận**.
- ⚠ **Việc rút lại này KHÔNG lay chuyển kết luận BÁC `D-ADV-03`**: refutation đó đứng trên **giá của
  deadhead** (**+512,6 km/ngày = +95% nền**, +1.290 phút-đội không-được-chào, +821 điểm-SOC), **không**
  đứng trên con số 65,3%. Cycle vẫn HUỶ.

## 3. Nợ index đã trả cùng lúc

`PROJECT-GRAPH.md` thiếu **5 hàng** (`UPDATE-168`…`172`) — vi phạm chính lệnh validation §9 của file đó
(và CLAUDE.md §4 đòi cập nhật graph sau **mỗi** thay đổi). Đã thêm đủ **6 hàng** (168–173).

## Kiểm chứng

- Hai phép đo của tôi chạy trên `run_once` config mặc định (**arm A**); `drop_demand_alpha` kiểm là **0,4**
  ⇒ **cùng điều kiện** với hàng α=0,4 của `UPDATE-083`.
- ⚠ **Chưa kiểm chứng / giới hạn của phép đo của tôi:** `trip_rated` bắn **722 cuốc/ngày** trong khi
  `orders_completed` nền là **~960/ngày** (rc-02) ⇒ **đó là một TẬP CON** (chỉ cuốc được rate), không phải
  toàn bộ cuốc hoàn thành. Vì thế con số **64,6%** là *"trong tập được rate"*; nó **khớp** mức đơn sinh
  64,4% nên không có dấu hiệu thiên lệch, nhưng **tôi không tuyên bố** đây là tỷ lệ trên toàn bộ cuốc.
- Cũng **chưa** thử tái tạo cách đo của `pb-07` (arm B3w, seed 1000/1001) để tìm ra vì sao nó ra 56% —
  ghi thành việc còn lại, **không** đoán.
- Suite: **không chạy** — 0 dòng code thay đổi.

## Visual
`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. **Lỗi gốc của tôi:** tin một con số của agent **hơn** một con số đã hiệu chỉnh của repo, rồi đi "sửa"
   cái đúng. Đúng bài học `verify-favourable-claims-hardest` — và lần này nó thậm chí không phải claim
   *thuận lợi*, chỉ là claim **tiện** cho câu chuyện tôi đang kể. **"Tác tử báo" ≠ "tôi đo".**
2. Điều làm lỗi này nguy hiểm: tôi đã **viết nó vào commit message và DEFERRED** — tức nó đã thành
   "sự thật của repo" trong một vòng. Nếu không tự kiểm lại thì nó sẽ sống. ⇒ **Quy tắc bổ sung: khi
   "sửa" một con số CÓ SẴN của repo, phải mở nguồn gốc của con số đó ra đọc TRƯỚC** (tôi làm ngược:
   sửa trước, tìm nguồn sau — và may là có tìm).
3. Con số `64,6%` của tôi là **tập con được rate** (722/960) — tôi nói rõ giới hạn thay vì làm tròn thành
   "toàn bộ cuốc hoàn thành".
4. Tôi **chưa** truy vì sao `pb-07` ra 56% — có thể nó đo đại lượng khác (vd chỉ cuốc **kích hoạt
   deadhead**). Để mở, không đoán.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13 ·
**amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
