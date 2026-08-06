# UPDATE-177 — Q-07 ở **n=100**: k=8 trội **cả 7 chỉ số** (kể cả Gini & sức khoẻ), chặn bởi **0,14đp**; và S2-1 test ghim **vô hiệu**

- **Ngày:** 2026-08-07
- **Loại:** research quyết-định-được (n=100 paired CRN, bootstrap CI) + verification S2-1 — **0 dòng code đổi**
- **Artifact:** `g3-q07-n100.py` + `.json` · probe S2-1 trong UPDATE này

## 1. Giá trị của việc sửa dispatcher — **n=100, có CI, SIG trên MỌI chỉ số**

A0 = `k=6` (nguyên trạng) vs A1 = `k=8`, **100 seed ghép cặp** (cửa sổ 3000–3099, chưa dùng), advisor **TẮT**:

| chỉ số | A0 | A1 | Δ (CI 95%) |
| --- | --- | --- | --- |
| `served_rate` | 0,8365 | **0,8635** | **+2,71đp** [+2,41; +3,00] **SIG** |
| đơn hết hạn/ngày | 196,6 | **164,1** | **−32,6** [−36,2; −29,4] **SIG** |
| idle % online | 33,23% | 31,28% | −1,95đp [−2,20; −1,69] **SIG** |
| trips/tài xế | 10,54 | 10,87 | +0,32 [+0,28; +0,36] **SIG** |
| payout/tài xế | 248.063đ | **254.818đ** | **+6.755đ** [+5.582; +7.959] **SIG** |
| **Gini payout** | 0,2227 | **0,2182** | **−0,0046** [−0,0073; −0,0018] **SIG** ⇒ **bất bình đẳng GIẢM** |
| **veto sức khoẻ** | 121,4 | 118,9 | **−2,5** [−3,9; −1,2] **SIG** ⇒ **chạm lan can ÍT hơn** |

⇒ **k=8 trội hơn k=6 trên cả 7 chỉ số, tất cả SIG ở n=100** — bao gồm **đúng hai thứ tôi đã ghi là chưa
đo** (`Gini` và `veto sức khoẻ`), và cả hai đều **tốt lên**, không phải đánh đổi.

## 2. Q-07 — chặn thật, nhưng **chỉ bởi 0,14đp**

Đại lượng của test (`tests/test_sim_realism.py`): `|realized_accept(archetype) − accept_base(config)|`
**gộp mọi seed**, dung sai **5,00đp**. Đo n=100:

| archetype | `accept_base` | lệch A0 (k=6) | lệch A1 (k=8) |
| --- | --- | --- | --- |
| P1 | 0,85 | +0,44 | −0,89 |
| P2 | 0,95 | −2,06 | −2,36 |
| P3 | 0,98 | −2,41 | −2,03 |
| P4 | 0,80 | −0,98 | −1,06 |
| P5 | 0,97 | −2,33 | −3,20 |
| P6 | 0,93 | −2,35 | −2,80 |
| **P7** | **0,94** | **−4,02 ✅** | **−5,14 ❌** ← **vế ràng duy nhất** |

⇒ **Q-07 chặn thật**, và số của tôi **xác nhận bảng 12-seed trong config** (−4,2 → −5,7 vs tôi −4,02 →
−5,14: cùng chiều, cùng bậc, cùng kết luận). **Nhưng khoảng cách là 0,14đp** — tức đánh đổi thật là:

> **vượt một dung sai trung-thành-hồ-sơ 0,14đp** ⇐⇒ **+2,71đp served · −32,6 đơn chết/ngày ·
> +6.755đ/tài xế · Gini giảm · veto sức khoẻ giảm** (tất cả SIG).

### ⭐ Một phương án THỨ BA chưa ai nêu
Ở k=6, P7 đã lệch **−4,02đp** — tức **80%** đường tới dung sai. Câu chưa ai hỏi: **`accept_base` của P7 =
0,94 có được hiệu chỉnh đúng không?** Nếu realized ≈ 0,889 mới là con số trung thực của một tài xế ca
tối-đêm, thì *"drift"* là **hiện vật của một prior cũ**, không phải suy thoái realism. ⇒ Ngoài hai lựa chọn
(*ghép đơn đúng* vs *trung thành archetype*), còn lựa chọn **hiệu chỉnh lại `accept_base` P7 từ dữ liệu**.
⚠ Đây **không** phải nới dung sai test (điều config gọi là che khuyết tật) — mà là sửa **giá trị tham
chiếu** nếu nó sai. Cần Cường quyết vì nó chạm định nghĩa realism.

## 3. ⚠ Tôi lại suýt báo một con số trả lời SAI câu hỏi (lần thứ ba)

Script của tôi in *"max|lệch| theo từng seed: A0 = 5,98đp, **67/100 seed vượt 5đp**"* và tôi **định** kết
luận *"config hiện tại đã vi phạm dung sai"*. **Sai đại lượng:** `_arch_realized` **gộp mọi seed** thành
một giá trị mỗi archetype ⇒ test dùng **trung bình gộp**, không dùng max-theo-seed. Max của **7** biến
nhiễu là thống kê **thiên lệch lên** ⇒ 5,98đp là hiện vật của phép lấy max, **không** phải vi phạm.
Bắt được nhờ **mở test ra đọc trước khi viết** — đúng quy tắc rút ra ở `UPDATE-173`, và nó đã cứu tôi
**ba lần** trong hai ngày.

## 4. S2-1 — test ghim **VÔ HIỆU: xác nhận**; nhưng `Δ<0` tôi **không tái tạo được**

**✅ Vô hiệu — CONFIRMED:** `test_delta_nonnegative_vs_baseline` (`tests/test_shift_dp.py:69`) dùng fixture
`buckets=6`, và `_required_rest(B=6, DEFAULT_PARAMS) = **0**` ⇒ **không có bucket nghỉ nào để đặt** ⇒ DP và
baseline **đều toàn ONLINE** ⇒ `delta = +0,0` **theo cấu trúc**. Assertion `delta >= -1e-6` **không kiểm
được tính chất nào**. Tôi mở rộng B=8/12/14/16/20 (R=1–2, có REST thật) ⇒ delta vẫn **+0,0**.

**❌ `Δ<0` tới −55.000đ — KHÔNG tái tạo được:** quét **1.890 cấu hình** (B ∈ {6,10,12,14,16,20} × points ∈
{0,40,55,95,140,155,195} × soc ∈ {30,60,95} × **5 hình dạng forecast** × 3 giờ `t_now`) ⇒ **0 cấu hình**
có `delta_payout < 0`. Agent báo **4,0%** trên lưới của nó. ⇒ Hai khả năng: lưới của tôi **không phủ** góc
đó, hoặc claim sai. **Tôi không kết luận** — chỉ ghi: `Δ<0` **CẤM TRÍCH** tới khi có ai tái tạo, còn phần
**test vô hiệu** thì **đứng và nên sửa** (fixture phải có `R ≥ 1` mới kiểm được điều nó khai).

## Kiểm chứng

- n=100 ghép cặp **cùng seed** (CRN), bootstrap **2.000** lần trên **hiệu theo cặp**; cửa sổ seed
  3000–3099 **chưa dùng** cho A0/A1 (tránh trùng 1000s đã dùng ở G1).
- Chỉ đổi `dispatcher.candidate_ring_k_max` qua `deepcopy` in-memory — **không sửa file config**.
- **Chưa kiểm chứng:** HHI cung theo ô (chỉ đo Gini payout) · A2 (hạ đội) **vẫn ở n=5**, chưa nâng lên
  n=100 ⇒ mọi số về "biên đánh đổi" của `UPDATE-176` §3(c) vẫn là **hướng, không phải số chốt** ·
  `Δ<0` của S2-1 (§4).
- Suite: **không chạy** — 0 dòng code đổi.

## Visual
`NOT_APPLICABLE` (research). Nếu Cường duyệt k=8 thì đó là **meaningful sim update** ⇒ visual gate bắt buộc.

## Adversalrial self-review / flaws found

1. **Lần thứ ba trong hai ngày tôi suýt trích số trả lời sai câu hỏi** (§3). Ba lần đều cùng dạng: một
   thống kê **trông giống** đại lượng cần, nhưng định nghĩa khác. Quy tắc đang có tác dụng thật; giữ nó.
2. Kết quả n=100 **mạnh hơn** n=5 của tôi ở G1 (Δserved +2,71đp vs +3,97đp — n=5 **thổi lên** ~1,3đp).
   ⇒ Bằng chứng cụ thể cho việc **cấm quyết trên n nhỏ**, kể cả khi hướng đúng.
3. **Gini và veto sức khoẻ tốt lên** là kết quả **thuận lợi** cho phương án tôi đang trình bày ⇒ đúng loại
   phải soi kỹ nhất (`verify-favourable-claims-hardest`). Chúng SIG ở n=100 với CI loại 0, nhưng tôi
   **chưa** đo HHI cung — nên **không** được nói *"equity tốt lên toàn diện"*, chỉ *"Gini payout giảm SIG"*.
4. Phương án thứ ba (hiệu chỉnh `accept_base` P7) là **đề xuất của tôi và chưa được phản biện** — sau ba
   lần phương án sửa của tôi bị bác trong hai ngày, tôi ghi nó là **lựa chọn để Cường cân nhắc**, không
   phải khuyến nghị.

## ⏳ Nhắc PENDING-REVIEW

**Q-07 — quyết định đòn bẩy cao nhất, nay có số n=100**: đánh đổi là **0,14đp** dung sai ⇐⇒ **32,6 đơn
chết/ngày + 6.755đ/tài xế + Gini & sức khoẻ tốt lên**; kèm **phương án thứ ba** (hiệu chỉnh lại
`accept_base` P7). · **V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/09/10/13
· **amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
