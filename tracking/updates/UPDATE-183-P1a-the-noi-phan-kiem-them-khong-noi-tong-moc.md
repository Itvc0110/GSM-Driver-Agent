# UPDATE-183 — `P1`: thẻ nói **phần KIẾM THÊM** (`P1a`) + cảnh báo sát ngưỡng **tới được tài xế** (`P1b`)

- **Ngày:** 2026-08-07
- **Loại:** implementation **đường sản phẩm** — **ĐỔI NỘI DUNG CARD** ⇒ visual gate bắt buộc
- **Plan:** `C:\Users\Cuong\.claude\plans\binary-cuddling-twilight.md` (Cường duyệt 2026-08-07)
- **Artifact:** `research/audit/2026-08-07-p1-tien-tren-card/`

## 1. Lỗi

`policy.bonus_at` là thang **THAY THẾ**, không cộng dồn — `bonus = tier_vnd` **ghi đè** chứ không
`+=` (`gsm_core/policy.py:104-110`; docstring nói *"mốc cao nhất đạt được"*). Nhưng thẻ đặt
`tier_vnd` = **TỔNG của mốc** ngay cạnh cụm nỗ lực:

> *"Còn với được mốc thưởng **60.000đ** hôm nay — bạn thiếu 40 điểm (khoảng **3,6 giờ chạy nữa**,
> 6 cuốc). Quỹ giờ còn lại đủ."*

Tài xế **đã chốt** mốc 30.000đ đọc câu đó và hiểu 3,6 giờ ấy đổi được **60.000đ**. Sự thật:
**30.000đ**. Số 60.000 tự nó không sai — nó là **tên của mốc**; sai là **chỗ đặt**.

## 2. ⚠ ĐO LẠI trước khi sửa — và con số đổi hẳn

Plan ghi rõ rủi ro: `Cycle B0` (`UPDATE-167`) vừa sửa mẫu số bucket của S1 ⇒ phân phối `feasible`
đã đổi **SAU** khi agent `pb5` đo. So *"111 → 0"* mà không đo lại là so **hai đại lượng khác nhau**.

| | agent `pb5` | **tôi đo lại** |
| --- | --- | --- |
| tỷ lệ thẻ sai | 111/1.129 = **9,83%** | **131/426 = 30,75%** |
| tiền bị thổi | — | **4.440.000đ** |
| bội số | 2,00× / 2,09× | **2,00×** (114 thẻ) · **2,09×** (17 thẻ) |

**Cao gấp 3.** Fallback *"nếu < 2% thì hạ severity"* **không kích hoạt**.
⚠ Chỉ quét **đội bike** (`d-`/`r-`) — đếm cả `ce-*` là bẫy đã làm `mm-03` sai ~2× và làm tôi
báo sai 26,7% hôm nay.

## 3. Sửa

- `bonus_feasibility.py` — `solution` thêm `bonus_now_vnd` (`policy.bonus_at(points_now)`) và
  **`tier_delta_vnd = tier_vnd − bonus_now_vnd`**; `numbers` khai `tier_delta` **chỉ khi khác
  tổng**. ⚠ **Chỉ nhánh có `next_tiers`** — nhánh `already_maxed` đã đúng, **không đụng**.
- `ui/backend/app/adapters/advisor.py` — `numbers` thêm `thuong_tang_them`; **tiêu đề giữ TÊN
  mốc**, câu nói về **nỗ lực** nay mang phần tăng thêm:
  > *"… (khoảng 3,6 giờ chạy nữa, 6 cuốc), **được thêm 30.000đ so với mức đã chốt**. Quỹ giờ còn lại đủ."*

**Vì sao phép trừ AN TOÀN** (tôi lo nó sai với người không đủ điều kiện — họ nhận **0đ** dù đủ
điểm): `feasible = enough_hours and ok_acc and ok_comp` (`bonus_feasibility.py:178`) ⇒ thẻ
`feasible_gap` **chỉ hiện với người ĐỦ điều kiện** ⇒ `bonus_at` đúng là phần họ **thật sự đã chốt**.

**Không cần bump schema:** `advice_artifact.schema.json` có `additionalProperties: false` ở cấp 1
nhưng `payload` khai `{"type": "object"}` **không ràng buộc**. (Khác Cycle B0 — ở đó tôi sửa
`bonus_gap_input`, là schema **input** có ràng buộc.)

## 4. Kiểm chứng

| tiêu chí | kết quả |
| --- | --- |
| thẻ không nêu phần tăng thêm | **131 → 0** |
| số thẻ `feasible_gap` | **426 → 426** (không mất thẻ nào) |
| `tests/test_p1a_tier_delta.py` | **16 passed** |
| `ui/backend/tests/test_p1a_card_dung_tang_them.py` | **5 passed** |
| `ui/backend/tests` | **224 passed** (baseline 216, +8 test mới) |
| `tests/` | **1205 passed · 2 failed** — đúng **hai lỗi có sẵn của Khánh**, 0 lỗi mới |

**Ba đường render đều đã sửa** (không chỉ đường sống):
`adapters/advisor.py` (v1, ĐANG CHẠY) · `templates.py:273` (qua `pipeline.py` — solver mồ côi;
có **fallback** `_sol1.get("tier_delta_vnd", _sol1.get("tier_vnd"))` cho artifact CŨ chưa có khoá,
không có nó thì câu này **im lặng đổi nghĩa** khi gặp report cũ) · `f3_patterns.py:104` (S3,
**0 caller** — sửa **phòng ngừa**, không phải vá bán kính).

**Bất biến được ghim thêm** (không có trong plan, tôi thêm khi thi công):
- nhóm **chưa chốt mốc nào** (295/426 thẻ — **đông nhất**) phải **không đổi một chữ** và không
  được mang **hai số tiền trùng nhau**;
- nhánh `already_maxed` **không sinh** `tier_delta_vnd` (số vô nghĩa ở đó) và `numbers` giữ
  đúng một phần tử.

---

## 5. `P1b` — cảnh báo "sát ngưỡng" nay TỚI ĐƯỢC tài xế

**Lỗi:** thẻ cliff bị giết **hai lần độc lập** — (a) `_verify_item` đòi mọi số trong text trace
về `numbers`, mà `_cliff_item` **cố ý** để `numbers: []` ⇒ note solver luôn chứa `0.85`/`0.86` ⇒
V1 luôn bắn; (b) `cards.js` chỉ vẽ `items[0]`, cliff luôn `append` thứ hai.
Đo (`pb5`): **246/2.310 sinh · 0/246 sống · 0/246 được vẽ**. Tôi đo lại trên đội bike:
**96/990 lượt (9,70%) ở trong dải · 0/96 tới tay**.

### ⚠ Câu hỏi trong plan của tôi SAI ĐẠI LƯỢNG — sửa khi thi công

Plan ghi *"đo bao nhiêu lượt còn đủ quỹ giờ để KÉO tỷ lệ LÊN"*. Đọc code: cliff bắn khi
**`0,85 ≤ acc < 0,88`** — tài xế **ĐANG TRÊN** ngưỡng; cảnh báo là **PHÒNG NGỪA**.
⇒ Đại lượng đúng: **còn MẤY LẦN TỪ CHỐI nữa thì rơi?**

| còn mấy lần từ chối thì rơi dưới 0,85 | số lượt |
| --- | --- |
| **1 lần** | 66/96 = **68,8%** |
| 2 lần | 27/96 = 28,1% |
| 3 lần | 3/96 = 3,1% |
| **⇒ ≤3 lần** | **96/96 = 100%** |

Quỹ giờ còn lại lúc cảnh báo: **trung vị 5,0 giờ**. ⇒ Một tài xế cách **một cú từ chối** khỏi
việc mất **trọn thưởng ngày**, còn 5 giờ ca phía trước — và hệ thống **không nói gì**.
Fallback *"đừng ship nếu không hành động được"* **KHÔNG kích hoạt**; ngược hẳn.

⚠ **Hai định nghĩa tỷ lệ, cố ý:** dải cảnh báo dùng `acceptance_rate` **đã co** (góc nhìn
advisor), còn `k` tính trên **đếm thô** — và đếm thô mới là thứ **chính sách dùng cuối ngày** để
quyết trả thưởng. Đây là chủ ý, không phải lẫn lộn.

**Sửa (đường rẻ nhất, 0 đổi contract):** gộp câu cảnh báo vào **`caveat` của thẻ đầu** — trường
này đã có và đã render ⇒ tới tay ngay, **không cần `cards.js` vẽ thẻ thứ hai, không cần Khánh**.
Giữ nguyên `_cliff_item` cho consumer nào đọc `items[1]`.
⚠ **Câu cảnh báo KHÔNG mang số** — có số không khai là **đúng cơ chế đã giết thẻ cliff 246/246**;
đã ghim bằng test riêng.

**Kiểm:** `test_p1b_canh_bao_cliff_toi_tay.py` **3 passed**, và **13 tài xế** trong dải trên lát
mock ⇒ test **sống, không xanh rỗng**.

---

## 6. Visual
🔴 **BLOCKED — cần Cường xem.** Hai ca đã ghi:
- `P1a`: **`d-13` / `2026-09-26` / `14:00`** (điểm 60, đã chốt 30.000đ, mốc kế 60.000đ)
- `P1b`: **`d-3`** hoặc **`d-9`** cùng ngày (tỷ lệ 0,873 / 0,858 — trong dải sát ngưỡng)

⚠ **Điều cần Cường để ý:** `caveat` nay có **ba mệnh đề** nối bằng `·` (demand proxy · sát biên ·
sát ngưỡng). Về mặt đo thì đúng, nhưng nếu **quá tải thị giác** thì fallback là **ưu tiên hiển
thị theo mức nghiêm trọng** thay vì nối hết — tôi không tự quyết chuyện này.

## Adversarial self-review / flaws found

1. **Một test của CHÍNH TÔI tự vô hiệu** — ngay trong file có docstring cảnh báo về lớp lỗi đó.
   Tôi cắt câu bằng `re.split(r"[.·]", …)`, mà `_vn(60000,'vnd')` render ra **"60.000đ"** *có dấu
   chấm bên trong* ⇒ phép cắt **xé đôi chuỗi tiền**, câu chứa cụm thời gian không còn chuỗi đầy
   đủ để so ⇒ assert **luôn xanh**. Đã neo lại vào `message` và ghi lý do vào docstring.
2. **Lần đầu 16 test đỏ vì fixture thiếu `next_tiers`**, không phải vì logic. Nếu dừng ở đó tôi
   đã tuyên bố "đỏ-trước xong" trong khi chưa chứng minh gì. Đây là lần thứ **hai** trong hai
   ngày tôi suýt nhận nhầm "đỏ sai lý do" là bằng chứng.
3. **Ba đường render — đã sửa CẢ BA.** Bản nháp plan chỉ nêu một; grep `tier_vnd` toàn repo mới
   lộ `templates.py:273` và `f3_patterns.py:104`. Sửa một chỗ rồi tuyên bố xong chính là lỗi
   `PB5-03` vừa xảy ra hôm nay.
6. **Câu hỏi đo của `P1b` trong plan SAI đại lượng** — tôi viết *"còn đủ quỹ giờ để KÉO tỷ lệ
   lên"* trong khi cliff bắn cho người **ĐANG TRÊN** ngưỡng. Bắt được vì đọc điều kiện sinh
   trước khi viết probe, không phải vì test đỏ.
7. **`caveat` nay ba mệnh đề** — đúng về đo, nhưng có thể quá tải thị giác. Tôi **không tự
   quyết** rút gọn; nêu ra ở visual gate.
4. **Chưa xem mắt thẻ v2.** v2 render `numbers` **tổng quát** (`advice_checkpoint.py:598`,
   `id = f"N{index+1}"`) nên `thuong_tang_them` **sẽ tự hiện** ở đó. `ADVICE_V2_ENABLED=0` nên
   hôm nay bán kính 0, nhưng phải kiểm trước khi bật v2.
5. **Con số 30,75% là của mock hiện tại.** Nó sẽ đổi khi mock đổi — trích phải kèm ngày đo.

## ⏳ Nhắc PENDING-REVIEW

🔴 **MỚI:** visual gate `P1a` — thẻ `d-13 / 2026-09-26 / 14:00`.
**Vẫn chờ:** **V-32** (blocking) · V-31 · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/09/10/13 · amendment ĐA-08 — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`.
⏸ Khánh: 2 test đỏ + Flutter.
