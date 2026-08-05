# `D-M3-04` — root cause của Δ ÂM, và vì sao nó đổi cách đọc kết quả

Ngày: 2026-08-05 · Trạng thái: **ba vòng. Vòng 3 (n=30, CI ghép cặp + đọc code) BÁC kết luận vòng 2.**
Số hiện hành: **100 seed** (A/B chính) + **30 seed ghép cặp** (sổ thời gian). Mọi số 3–5 seed đã **gỡ bỏ**.

---

## 0. Kết luận — bản THỨ BA, có bằng chứng ở CẢ HAI mức

> **Hoãn nghỉ biến NGHỈ thành CHỜ RỖNG.** Không thành sạc, không thành chạy rỗng, không thành đơn.
> Tài xế vẫn online, không được phục hồi, và **không kiếm thêm một đồng nào**.

Khác với hai vòng trước, kết luận này đứng trên hai chân độc lập:

**(a) Cơ chế — đọc thẳng trong code, không suy luận** — [`world.py:963-970`](../../src/gsm_sim/world.py#L963-L970):

```python
if defer:
    actor.rest_deferred_min += 2.0
    self.log(...)
    action, target = IdleAction.WAIT, None      # ⬅ NGHỈ → CHỜ. Một dòng.
```

Mà `WAIT` chính là nhánh duy nhất cộng `idle_min` ([`world.py:1042`](../../src/gsm_sim/world.py#L1042)), còn `REST`
là nhánh duy nhất cộng `rest_min` ([`world.py:1016`](../../src/gsm_sim/world.py#L1016)). Hai nhánh **loại trừ nhau**
trong cùng một `if/elif/else` ⇒ dịch chuyển rest→idle là **đổi hành vi thật**, không phải đổi cách phân loại.

**(b) Hệ quả — đo 30 seed × 2 ngày, CI95 bootstrap GHÉP CẶP theo seed:**

| khoản | arm A | arm B | Δ | CI95 | |
| --- | ---: | ---: | ---: | --- | --- |
| `rest_min` | 3 864,7 | 3 620,7 | **−244,0** | [−301,8; −181,7] | ✅ nghỉ bị lấy đi (−6,3%) |
| `idle_min` | 14 440,4 | 14 650,0 | **+209,5** | [+107,3; +309,8] | ✅ ⬅ **chảy vào CHỜ RỖNG** |
| `rest_deferred_min` | 0,0 | 18,0 | **+18,0** | [+16,2; +19,8] | ✅ kênh có chạy |
| `occupied_min` | 14 026,8 | 14 026,3 | −0,4 | [−44,8; +41,7] | ns — **giờ có khách không đổi** |
| `empty_min` | 11 476,5 | 11 499,8 | +23,3 | [−20,9; +64,7] | ns |
| `charge_min` | 3 315,0 | 3 289,9 | −25,1 | [−105,2; +61,2] | ns |
| `orders_offered` | 1 160,3 | 1 161,2 | +0,8 | [−3,5; +5,2] | ns |
| `orders_completed` | 977,3 | 975,8 | −1,5 | [−4,7; +1,7] | ns |
| `payout_vnd` (cohort) | 23 143 603 | 23 037 631 | −105 972 | [−225 394; +15 049] | ns |

**209,5 / 244,0 = 86%** phần nghỉ mất đi hiện lại nguyên vẹn ở cột chờ rỗng. Phần dư nằm trong nhiễu.
Và **không một chỉ tiêu sinh tiền nào nhúc nhích**: chào đơn, nhận đơn, hoàn thành, giờ có khách — ns cả bốn.

⚠ Sổ **không kín** ~3,4% (`online_min` 45 545 vs tổng phần 47 123): `online_min` gộp toàn bộ thời gian đã
trôi (`D-M3-19`, `D-QD4-05`) nên chồng lấn. **Không ảnh hưởng kết luận** — `rest`/`idle` là hai nhánh
loại trừ nhau, và lệch này như nhau ở cả hai arm.

---

## 1. 🔴 Vòng 3 BÁC kết luận trung tâm của vòng 2 — lần thứ ba trong một phiên

Vòng 2 kết luận (in đậm, ở đầu tài liệu này): *"Nó biến thành SẠC và CHẠY RỖNG"*, dựng cả một bảng
so sánh nghỉ-vs-sạc, và đặt **"đưa chi phí PIN vào quyết định hoãn"** làm đề xuất ⭐ số 1.

Đo lại ở 30 seed:

| claim vòng 2 (n=3) | n=30 ghép cặp | |
| --- | --- | --- |
| `charge_min` **+80,5′** ⇒ *"khoản phình to nhất"* | **−25,1** [−105,2; +61,2] | 🔴 **ns, và ĐỔI DẤU** |
| `empty_min` **+76,2′** | **+23,3** [−20,9; +64,7] | 🔴 **ns** |
| `occupied_min` **−14,2′** ⇒ *"khoản duy nhất sinh tiền giảm"* | **−0,4** [−44,8; +41,7] | 🔴 **ns** |
| `orders_cancelled` **+9,2%** | +0,6 [−1,5; +2,5] | 🔴 **ns** |

**Cả bốn số neo của vòng 2 đều là nhiễu.** Đề xuất ⭐ số 1 mất sạch chỗ dựa.

### Điều đáng nói hơn: cơ chế thật nằm ở một dòng code tôi chưa từng mở

`action, target = IdleAction.WAIT, None` — dòng này quyết định *toàn bộ* chuyện gì xảy ra sau khi hoãn.
Nó nói thẳng "nghỉ → chờ". Không có đường nào từ đây tới trạm sạc. Nếu tôi đọc nó **trước**, tôi đã biết
ngay giả thuyết "chảy vào sạc" là bất khả thi về mặt cơ chế, và đã không cần tới 3 seed lẫn 30 seed để bác.

⇒ **Bài học: khi hỏi "thời gian đi đâu", đọc nhánh điều khiển TRƯỚC, khai thác số liệu tổng hợp SAU.**
Số tổng hợp cho tương quan; nhánh `if` cho nhân quả. Tôi đã làm ngược thứ tự, hai vòng liền.

### Ba lần trong một phiên, cùng một lỗi

| # | Claim | n | Kết cục |
| --- | --- | --- | --- |
| 1 | `swap_wait_mean` / `orders_completed` / `served_rate` — 3 CI không chứa 0 ⇒ *"hàng đợi trạm"* | 5 | n=100: **cả ba chứa 0** |
| 2 | `charge_min` +80,5′ / `empty_min` +76,2′ ⇒ *"nghỉ đổi thành sạc"* | 3 | n=30: **ns, charge đổi dấu** |
| 3 | *"85% lượt kéo ca bị lan can chặn"* | — | đếm nhầm lượng: marginal thật **3,5%** |

Mẫu số chung không phải "thiếu seed" — mà là **hành động như thể cảnh báo mình vừa viết không tồn tại**.
Vòng 2 có ghi rõ *"⚠ 3 seed"* ngay trong bảng, rồi vẫn viết kết luận in đậm và xếp hạng đề xuất trên đó.

---

## 2. Chuỗi nhân quả — bản đã sửa (vòng 3)

```
S7 chọn "khung vắng khách" ──► dồn cục: 3 khung ôm 64,4% lượt giao   [H-a ✅ giữ]
        ▼
should_defer_rest phủ quyết bản năng NGHỈ  (chỉ REST — swap/charge bị soc_low chặn trước) [H-b]
        ▼
world.py:970   action := WAIT          ◄── CƠ CHẾ, đọc thẳng trong code
        ▼
tài xế ĐỨNG CHỜ, 2 phút một nhịp, tái thẩm định mỗi nhịp, tối đa 120′ (rest_defer_max_min)
        ├──► idle_min  +209,5′   ✅ CI không chứa 0
        ├──► rest_min  −244,0′   ✅ CI không chứa 0   ⇒ STOP-C BẮN
        └──► orders_offered/accepted/completed/occupied_min:  ns — CHỜ KHÔNG SINH RA ĐƠN NÀO
        ▼
Δ payout ÂM nhưng ns:  −429đ/tài xế [−1 142; +290]  ·  cohort −38 635đ [−102 808; +26 067]
```

**Hai lý do độc lập khiến kênh này chỉ có thể lỗ** — và đây là điểm mới của vòng 3:

1. **β=0** (prereg đã khai trước): world không mô hình hoá hậu quả mệt ⇒ *nghỉ* không mang lại lợi ích.
2. **Thế giới bị chặn bởi CẦU, không bởi cung tài xế** (đo được: `orders_offered` Δ = +0,8 ns): ⇒
   *không nghỉ* cũng **không** mang lại lợi ích. Giải phóng thời gian tài xế không tạo thêm đơn.

Lý do 1 nói "nghỉ vô ích". Lý do 2 nói "không nghỉ cũng vô ích". Cộng lại: kênh **chỉ còn đường lỗ** —
nó chỉ có thể chuyển thời gian từ ô có ích sang ô vô ích. Prereg dự đoán Δ ≤ 0 bằng lý do 1; đo được lý do 2.

---

## 3. Khuyết tật cấu trúc — bản đã sửa

### 3.1 🔴 Hoãn nghỉ là "PHỦ QUYẾT BÂY GIỜ", không phải "DỜI SANG X" — *bằng chứng ở code + số*

Không có cam kết nào rằng nghỉ sẽ diễn ra ở khung đích. `rest_deferred_min += 2.0` mỗi tick, bản năng
nghỉ bị bỏ qua, `action := WAIT`. Khung trôi qua / chạm trần 120′ / hết ca ⇒ **nghỉ biến mất hẳn**.
Đo: `rest_min` −244,0 ✅ · `rest_deferred_min` 0 → 18,0 ✅ · `veto_defer_cap_n` 0 → 8,0 (trần CÓ bị chạm).

Đây giờ là khuyết tật **duy nhất** có bằng chứng trực tiếp, và là khuyết tật **quan trọng nhất**.

### 3.2 🔴 Nhánh rơi của phủ quyết là `WAIT` — lựa chọn tệ nhất có thể

Khi từ chối cho nghỉ, kênh không bảo tài xế làm gì khác: không đổi ô, không sạc, không kết ca. Chỉ **đứng yên**.
Vì tái thẩm định mỗi 2 phút và điều kiện hoãn thường vẫn đúng, tài xế có thể đứng tới **2 tiếng**.

So sánh cho thấy mức độ: khoản nghỉ mất đi **86% hiện lại ở cột chờ rỗng**, và cột sinh tiền **không nhúc nhích**.
Tức kênh này không đánh đổi *sức khoẻ lấy tiền* — nó **đốt sức khoẻ mà không đổi lấy gì**.

### 3.3 ~~Kênh coi NGHỈ và SẠC là hai khoản downtime thay thế được~~ — **RÚT LẠI**

Vòng 2 gọi đây là *"khuyết tật quan trọng nhất"*. Nó dựa trên `charge_min` +80,5′ ở n=3, mà n=30 cho
**−25,1 ns**. Thêm nữa, code không có đường nào từ hoãn-nghỉ sang sạc (§0a). **Mục này sai ở cả số lẫn cơ chế.**

### 3.4 Dồn cục khung nghỉ — có thật, nhưng CHƯA nối được với tiền (giữ nguyên từ vòng 2)

64,4% lượt giao rơi vào ba khung (`H-a` ✅). Kênh vị trí có `supply_incoming` (`market_state.py:13`) và
`herding_avoided` (`world.py:482`); kênh nghỉ **không có gì tương đương**. Nhưng `H-c` cho thấy dồn cục này
chưa biến thành hàng đợi trạm ⇒ **không được bán nó như cách chữa Δ âm**. Nợ về tính bền vững, không phải
nguyên nhân mất tiền.

### 3.5 Nhánh hoãn SWAP/CHARGE là **CODE CHẾT** (giữ nguyên — đây là phát hiện về code, không phải về số)

`if action in (REST, GO_SWAP, GO_CHARGE)` nhưng đo được **0/41** lượt hoãn đến từ swap/charge: khi bản năng
chọn `GO_SWAP` thì SOC thường đã ≤ `swap_soc_threshold_pct`, mà đó chính là lan can `soc_low` ⇒ chặn trước.
Hai phần ba điều kiện **không có đường chạy** — họ `D-R12`, ở dạng ngược: code trông như điều khiển ba cơ
chế, thực tế chỉ điều khiển một.

---

## 4. Đề xuất — xếp lại sau vòng 3

| # | Việc | Bằng chứng | Kiểm bằng |
| --- | --- | --- | --- |
| **1** ⭐ | **Hoãn phải là CAM KẾT, không phải phủ quyết**: ghi "nghỉ ở giờ X"; tới X thì **ép diễn ra**; khung trôi qua thì **trả lại quyền nghỉ ngay** | §3.1 — `rest_min` −244 ✅, `defer_cap` 0→8 | `rest_min_total` Δ ≥ 0 ⇒ STOP-C thôi bắn |
| **2** ⭐ | **Nhánh rơi không được là `WAIT`.** Từ chối nghỉ thì phải kèm một hành động có ích (đổi ô / sạc / kết ca), nếu không thì **đừng từ chối** | §3.2 — 86% nghỉ mất đi thành chờ rỗng | `idle_min` Δ ≈ 0 khi `rest_min` giảm |
| **3** | Sổ chống dồn cục + stagger cho khung nghỉ — dùng lại khuôn `supply_incoming` | §3.4 (64,4%) | phân bố khung phẳng hơn; **không** hứa Δ tiền |
| **4** | Gỡ nhánh CHẾT `GO_SWAP`/`GO_CHARGE`, **hoặc** làm nó chạy được có chủ ý | §3.5 — 0/41 | test đòi nhánh có đường chạy, hoặc nó biến mất |
| ~~5~~ | ~~**Đưa CHI PHÍ PIN vào quyết định hoãn**~~ | 🔴 **RÚT** — `charge_min` ns và đổi dấu ở n=30 | — |
| ~~6~~ | ~~tách kênh swap~~ · ~~sức chứa trạm~~ | 🔴 **RÚT** ở vòng 2 (`H-b`/`H-c`) | — |

⚠ **Đề xuất 1 và 2 vẫn CHƯA được kiểm bằng can thiệp.** Chúng có cơ chế trong code + số khớp, đó là
nhiều hơn hẳn vòng 1/vòng 2 từng có — nhưng **vẫn chưa phải bằng chứng nhân quả**. Xem §5.

---

## 5. Phép kiểm PHÂN BIỆT phải chạy TRƯỚC khi thi công 1 & 2

> Arm B″ = arm B, nhưng khi `should_defer_rest` trả True thì **không** đặt `action := WAIT` — trả về
> `action` gốc (tức cho nghỉ). Tương đương "tắt phủ quyết, giữ nguyên mọi thứ khác".

- Nếu `idle_min` Δ về ~0 **và** `rest_min` Δ về ~0 ⇒ xác nhận dòng `:970` là **toàn bộ** cơ chế
  ⇒ thi công 1 & 2 là đúng chỗ.
- Nếu `rest_min` vẫn giảm ⇒ còn đường khác lấy mất nghỉ ⇒ phải tìm trước khi xây.

🔒 **Chạy ở 30 seed trở lên, kèm CI ghép cặp.** Ba lần bị nhiễu lừa trong một phiên là đủ để coi
"n nhỏ cho nhanh" là một **cái bẫy đã biết**, không phải một lựa chọn hợp lệ.

Chi phí: một nhánh `if` + một lượt 30 seed (~25′). Rẻ hơn hẳn việc thi công rồi mới biết.

---

## 6. Cấm — giữ nguyên từ prereg

- **KHÔNG** nới `rest_defer_max_min` (`POLICY_LOCKED_KEYS`). `veto_defer_cap_n` 0→8,0 cho thấy trần đang
  **làm đúng việc** — nó là thứ duy nhất chặn tài xế đứng chờ quá 2 tiếng.
- **KHÔNG** nới `REST_TOTAL_DROP_TOL`/`SPAN_P90_RISE_TOL` để STOP-C thôi bắn. Nó bắn vì có thật.
- **KHÔNG** quy bất kỳ chỉ tiêu sức khoẻ nào ra VND.
- **KHÔNG** sửa `luat_quyet_dinh` (đã thi hành: REVERT).
- Câu diễn giải mà `luat_quyet_dinh` cho phép — *"trong world không có hậu quả mệt, kênh nghỉ là chi phí
  thuần"* — **vẫn đúng, và giờ đã đủ**: §2 cho thấy thời gian nghỉ bị đổi sang **chờ rỗng**, tức đúng nghĩa
  chi phí thuần, không đổi lấy gì. (Vòng 2 từng đòi sửa câu này vì tưởng nghỉ bị đổi thành *sạc*; đòi hỏi đó
  **rút lại**.)
- **KHÔNG trích trần 71%/≤29%** cho chế độ multiday (prereg `vung_mu_khai_truoc`; biên thật ~8,8%).
