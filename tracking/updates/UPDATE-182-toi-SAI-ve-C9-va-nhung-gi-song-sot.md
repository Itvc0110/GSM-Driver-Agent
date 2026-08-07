# UPDATE-182 — **Tôi sai về C9**: soi độc lập bác bằng một arm KHÔNG CÓ ADVISOR; và những gì sống sót

- **Ngày:** 2026-08-07
- **Loại:** đính chính (nghiêm trọng) + kết quả phản biện 8 agent · **0 dòng code đổi**
- **Artifact:** `research/audit/2026-08-07-phan-bien-sim-advisor/` — `00-BAN-DO-FLAW.md` ·
  `pb-refute.json` · `pb1..pb6-*.json` (+ `.py` tái tạo được)

---

## 1. ❌ TÔI SAI — và sai ở đúng chỗ tôi đã tự cảnh báo rồi vẫn bước vào

Vài giờ trước tôi báo với Cường, và ghi vào `DEFERRED` **sev CAO**:

> *"Kênh `positioning` **PHÂN PHỐI LẠI** thu nhập: rảnh-ít **−15.290đ SIG**, rảnh-nhiều
> **+26.106đ SIG**, biên độ gấp ~8× giá trị ròng. Vế *lấy của người bận* chưa ai từng báo cáo."*

**Refuter dựng đúng phép thử tôi thiếu.** `NoisyWorld` (`pb1b-co-che-va-lat-cat-co-dinh.py`):
**cùng seed, cùng đơn, cùng actor, advisor TẮT HOÀN TOÀN** — chỉ đổi khoá RNG của **nhiễu niềm
tin cá nhân** (`+7919`). Tức một thế giới **không có can thiệp nào**, chỉ nhiễu.

| đại lượng (tercile theo `idle_min@A`) | arm THẬT (B) | arm **KHÔNG CÓ ADVISOR** |
| --- | --- | --- |
| Δ payout t0 / t1 / t2 | −15.290 / −6.887 / +26.106 | **−20.757 / −6.887 / +25.338** — cả ba **SIG** |
| Δ **ròng** | **+3.219đ SIG** | **−769đ ns** |
| Δ trips t0/t1/t2 | −0,586 / −0,233 / +1,394 | **−0,846 / −0,478 / +1,358** |
| R² của trục tercile | 0,0463 | **0,0526** |
| `harmed_share` | 42,30% | **46,00%** |
| `churn_ratio` | 17,82× | **78,02×** |
| `delta_p10` | −89.264đ | **−98.467đ** |

⇒ **Năm con số cuối đều XẤU HƠN ở thế giới không có advisor.** Mẫu hình tercile của tôi là
**hồi quy về trung bình** thuần: điều kiện hoá trên `idle_min@A` rồi đo `B−A` sinh ra dấu +/−
theo tercile với **bất kỳ** nhiễu nào, kể cả nhiễu không mang thông tin và không do advisor.

### Vì sao placebo của tôi không bắt được — và đây là bài học

`9c` (arm NULL = advisor bật, positioning tắt) ra **bit-identical 30/30 seed**. Tôi đọc đó là
*"placebo sạch"*. Sự thật: nó là placebo **PHƯƠNG SAI 0** — không có nhiễu thì **không thể** đo
được hồi quy về trung bình. Tôi cần một placebo **CÓ nhiễu mà KHÔNG có thông tin**; refuter dựng
đúng cái đó.

**Nặng hơn:** tôi **đã tự viết** trong chính artifact rằng *"chưa loại được giả thuyết can thiệp
như một bộ xáo trộn ⇒ biên độ tercile CHƯA được phép trích"* — rồi **vẫn** đưa số vào `DEFERRED`
sev CAO và **vẫn** báo miệng với Cường. Ghi caveat không thay được việc **không đăng số**.

⛔ **CẤM TRÍCH:** −15.290đ · +26.106đ · 58,4% · 17,82× · 42,30% · −89.264đ.
`D-C9-PHAN-PHOI` đã chuyển **ĐÃ LOẠI** (giữ dòng làm hồ sơ, không xoá).

---

## 2. ✅ Cái SỐNG SÓT — arm null **không** tái tạo được

| đại lượng | arm THẬT | arm không-advisor |
| --- | --- | --- |
| **chuyến/ngày** | **+17,27** | ~**+1** |
| **đơn hết hạn/ngày** | **−16,27** | — |
| payout **toàn đội** | **+3.219đ SIG** | **−769đ ns** |

⇒ **Kênh positioning tạo giá trị THẬT ở mức HỆ THỐNG.** Cái sụp là **phân rã "ai được ai mất"**,
không phải giá trị của kênh.

**Và `9d` vẫn đứng, nay còn vững hơn:** arm `SHUF` (hoán vị ngẫu nhiên đích giữa các allocation —
đã kiểm lực: đổi đích **66,0–83,6%** allocation, 3,2–5,0 ô khác nhau/bucket) cho `B − SHUF` **ns
ở mọi dòng**, toàn đội **−1.371đ ns**. Kết hợp với §2: **giá trị hệ thống là thật, nhưng phần
Hungarian matching (`linear_sum_assignment` — "chống dồn cục") đóng góp KHÔNG ĐO ĐƯỢC.**
Giá trị đến từ *việc đẩy tài xế rảnh tới ô được chọn*, không từ *việc chọn ai đi ô nào*.

**Phản biện:** 13/76 finding bị bác, **58 đứng vững** (22 chạm đường sản phẩm, 30 chạm kênh đang
ship). Ba metric mà `pb3` đề xuất làm cổng (**harmed_share**, **churn_ratio**, **delta_p10**) đều
**bị bác cùng cơ chế**: arm null vượt ngưỡng **mạnh hơn** hiện trạng ⇒ chúng sẽ **treo một thế
giới không có can thiệp nào**.

---

## 3. Ba phát hiện ĐƯỜNG SẢN PHẨM sống sót — tôi tự kiểm cơ chế của cái nặng nhất

### ⭐ `PB5-02` — **số tiền trên mặt thẻ là TỔNG MỐC, không phải phần kiếm thêm**

**Tôi tự kiểm hai vế then chốt:**
- `policy.py:104-110` `bonus_at` — docstring nói *"mốc **cao nhất đạt được**"* và vòng lặp
  **ghi đè** `bonus = tier_vnd` (**không cộng dồn**) ⇒ thang thưởng là **THAY THẾ**.
- `advisor.py:306` — tiêu đề thẻ là `f"Còn với được mốc thưởng {tier_vnd} hôm nay"`, đặt ngay
  cạnh *"khoảng X giờ chạy nữa, Y cuốc"*. `numbers` chỉ đăng ký `thuong_moc_ke = tier_vnd`.

⇒ Tài xế **đã chốt** mốc 30.000đ được nói *"còn với được mốc 60.000đ — khoảng 2 giờ nữa"*.
Phần **thật sự** đổi được bằng 2 giờ đó là **30.000đ**, không phải 60.000đ.
**Không tầng nào** (solver / adapter / contract / client) tính hay hiển thị `tier_vnd −
bonus_at(points_now)`.

Agent đo: **111/1.129 thẻ `feasible_gap` (9,83%)** rơi vào ca này — **105 thẻ trưng 60.000đ khi
biên là 30.000đ** (2,00×), **6 thẻ trưng 115.000đ khi biên là 55.000đ** (2,09×). ⚠ Con số đếm
này **tôi chưa đo lại**; **cơ chế** thì tôi đã xác nhận bằng code.

**Mức độ — nói cho đúng:** đây **không phải số bịa** (60.000đ đúng là tên của mốc), mà là
**khung diễn giải sai + thiếu một đại lượng**. Nhưng nó chạm `CLAUDE.md §5` (*"không hứa chắc mức
thu nhập"*) vì câu ghép lại dựng đúng kỳ vọng sai. **Sửa nhỏ:** thêm `thuong_tang_them =
tier_vnd − bonus_at(points_now)` và đặt **nó** cạnh số giờ.

### `PB5-01` — cảnh báo "sát ngưỡng" bị **chính verifier cùng file** giết 100%
`_cliff_item` cố ý để `numbers: []` (*"KHÔNG số tiền, KHÔNG hứa hẹn"*), còn `_verify_item` đòi
**mọi** chuỗi số trong text phải trace về `numbers` ⇒ note của solver luôn chứa hai số thập phân
⇒ V1 luôn bắn ⇒ thẻ **luôn** bị loại. Tầng chặn thứ hai độc lập: `cards.js` chỉ vẽ `items[0]`,
mà cliff luôn `append` thứ hai. Đo: **246/2.310 lượt sinh cliff · 0/246 sống sót · 0/246 được vẽ**;
**160** trong số đó rơi đúng lúc thẻ kia đang **giục chạy thêm**.

### `PB5-03` — đường **v2** đi vòng qua **cổng đội xe duy nhất** của repo
`advice_checkpoint.py` gọi thẳng `advisor.build_gi`, mà cổng `startswith(("d-","r-"))` nằm trong
`_advice_raw` — **xuất hiện đúng MỘT lần** trong mã sản phẩm. Đo: **120/120 lượt car/premium**
sinh `tier_vnd ≠ 0` bằng chính sách **BIKE**. ⚠ **Bán kính hôm nay = 0** (`ADVICE_V2_ENABLED=0`)
⇒ **instance thứ TƯ** của khuôn "LỚP 0".

---

## Kiểm chứng

- Tôi tự mở `pb1b-co-che-va-lat-cat-co-dinh.py` đọc **cách dựng arm null** trước khi chấp nhận
  phép bác: cùng seed, cùng cấu hình, `enabled=False`, chỉ đổi khoá RNG nhiễu niềm tin ⇒ **hợp lệ**.
- Tôi tự đọc `policy.bonus_at` và `advisor.py:306` cho `PB5-02` ⇒ **cơ chế xác nhận**.
- **Chưa kiểm chứng:** các con số ĐẾM của agent (111/1.129 · 246/2.310 · 120/120) · 58 finding
  còn lại chưa ai đọc hết · **suite chưa chạy** (0 dòng code đổi).

## Visual
`NOT_APPLICABLE` — 0 thay đổi code.

## Adversarial self-review / flaws found

1. **Lỗi tệ nhất của tôi hôm nay, và nó không phải lỗi kỹ thuật.** Tôi **đã viết** *"chưa loại
   được xáo trộn ⇒ biên độ tercile chưa được phép trích"* rồi **vẫn** đăng số vào `DEFERRED` sev
   CAO và báo miệng. **Ghi caveat không phải là không đăng số.** Luật mới cho chính tôi:
   *nếu tôi vừa viết "chưa loại được X" thì con số đó KHÔNG được vào DEFERRED/UPDATE/lời báo —
   nó ở lại trong artifact cho tới khi X bị loại.*
2. **Placebo phương-sai-0 là placebo VÔ HIỆU.** `9c` bit-identical 30/30 nhìn như bằng chứng mạnh;
   thực ra nó **không thể** phát hiện thứ tôi cần phát hiện. Một placebo phải có **cùng loại nhiễu**
   với can thiệp, chỉ thiếu **thông tin**.
3. **Tôi đã đúng khi nghi ngờ, sai khi công bố.** Trình tự đúng là: nghi ngờ ⇒ **dựng null có
   nhiễu** ⇒ rồi mới nói. Tôi làm bước 1 và bước 3, bỏ bước 2.
4. **Ba metric đề xuất làm cổng đều sụp cùng một cơ chế** — chúng đo **sàn nhiễu** chứ không đo
   tác hại. Bài học: **mọi ngưỡng cổng phải được neo bằng một arm KHÔNG CAN THIỆP có nhiễu**,
   nếu không nó sẽ treo cả thế giới không làm gì.
5. **Refuter cũng là agent** — nhưng phép bác này (a) bất lợi cho chính batch của nó, (b) khớp
   với caveat tôi tự viết, (c) tôi đã mở code dựng arm null ra kiểm. Ba điều đó mới đủ để tôi tin.

## ⏳ Nhắc PENDING-REVIEW

🔴 **Cường bỏ qua mọi con số tercile tôi báo trong hai lượt trước** — đã rút.
**Cần Cường quyết:** `PB5-02` sửa **văn bản thẻ** (thêm `thuong_tang_them`) là đổi **nội dung
card** ⇒ cần visual gate. **Vẫn chờ:** **V-32** (blocking) · V-31 · K-01(b) ACK · D-QD4-05 ·
~27 mục V- · Q-03/04/09/10/13 · amendment ĐA-08 — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`.
⏸ Khánh: 2 test đỏ + Flutter.
