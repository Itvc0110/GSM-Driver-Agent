# Root cause THẬT: soi vào simulation, data, công thức và bản dịch solver→action

Ngày: 2026-07-27 · Trả lời ba chỉ thị của Cường. Seed 1000, `configs/pilot_dongda.yaml`.
**Thay cho hướng "thêm biến giá trị nghỉ"** — Cường bác đúng: không mô hình hoá được chính xác thì
không nên tạo biến.

---

## PHẦN A — Chờ đơn nhiều giờ (chỉ thị #3): KHÔNG phải lỗi data, là **hình học cung–cầu**

### A1. Triệu chứng tái lập được

| Số đo | Giá trị |
|---|---|
| khoảng chờ giữa hai hoạt động | median **0,7′** · p90 **12,5′** · p99 **152′** · **MAX 334′ (5,6 giờ)** |
| khoảng > 60′ / > 120′ / > 180′ | **61 / 30 / 9** |
| ví dụ: actor 33 (P3) | online **849 phút**, chỉ được chào **5 đơn** cả ngày |
| số lần được chào/tài xế | min **3** · median **11** · max 29 |

### A2. Cùng lúc đó, 20–30% đơn giờ cao điểm HẾT HẠN

`supply_demand_density`: 06h expired 29,5% · 07h 30,6% · 08h 20,7% · 22h 27,9%.

**Tài xế rỗi hàng giờ trong khi đơn hết hạn** ⇒ không thể là thiếu cung. Là **ghép đơn hỏng**.

### A3. Truy nguyên — bốn phép đo nối tiếp

**(1) Đơn hết hạn có tài xế ở gần không? → CÓ, rất gần.**

| | |
|---|---|
| đơn hết hạn có tài xế rỗi cách **< 5 km** | **238/238 = 100%** |
| khoảng cách tới người rỗi gần nhất (tốt nhất trong đời đơn) | median **1,29 km** |
| có ứng viên trong `k_max=6` tại thời điểm tốt nhất | **81,9%** |

**(2) Có được chào không? → PHẦN LỚN LÀ KHÔNG.**

| | |
|---|---|
| đơn hết hạn **từng được chào** | 34/238 = **14,3%** |
| **chưa bao giờ được chào** | **204/238 = 85,7%** |
| **chưa bao giờ có assignment** | **191/238** |

**(3) Có phải đơn xấu bị chê không? → KHÔNG.**

| | gross median | km median |
|---|---|---|
| đơn **hết hạn** | **24.151đ** | 3,20 |
| đơn **được phục vụ** | 24.734đ | 3,31 |

Tỷ lệ nhận toàn cục **90,8%** (972 matched / 98 declined). Từ chối **không** phải nguyên nhân.

**(4) Vậy vì sao? → Mật độ tài xế rỗi quá thưa so với bán kính dispatch.**

| Số đo (9.253 tick) | Giá trị |
|---|---|
| vùng pilot | **3,9 km × 5,9 km** (~23 km²) |
| tài xế **rỗi**/tick | median **12** (trong 90 tài xế) |
| đơn đang mở/tick | median **3,0** |
| **assignment/tick** | **0,44** |
| k/c từ đơn tới người rỗi **gần nhất** | median **2,46 km** · p90 **3,90 km** |
| số ô trong `k=6` **có** tài xế | **median 0** |
| **tick mà người gần nhất > 2,1 km (ngoài `k=6`)** | **5.736/9.253 = 62,0%** |

`k=6` ở res 9 = 127 ô ≈ **13 km², bán kính ~2,1 km**. Với **12 người rỗi trải trên 23 km²**,
khoảng cách tới người gần nhất **median 2,46 km > 2,1 km** ⇒ **62% số lượt, shortlist H3 RỖNG**.

⇒ **Đơn chết vì không có ai trong tầm với, chứ không vì bị chê.** Và cùng nguyên nhân đó làm tài
xế ngồi rỗi hàng giờ: họ ở **sai chỗ**, không phải ở "không có việc".

### A4. Một BUG thật kèm theo (nhỏ hơn, nhưng có thật)

`dispatcher.py:77` — chọn tài xế **gần nhất theo haversine**, nếu ETA > `eta_max` thì **bỏ luôn
đơn**, không thử người khác. Docstring biện minh: *"ETA đơn điệu theo distance nên actor gần nhất
fail ETA ⇒ mọi actor khác cũng fail"*.

**Tiền đề đó SAI**: `ETA = dist × factor(cell_actor → cell_pickup) / speed`, và chính repo đo được
`factor` **median 1,46 · p10 1,24 · p90 1,94** (`configs/pilot_dongda.yaml:278`). Biến thiên 56%
⇒ một người xa hơn nhưng đường tốt hơn có thể ETA **thấp hơn**.

Đo: **3.520** lượt bỏ vì ETA; trong đó **293 (8,3%) BỎ OAN** — còn ứng viên khác đạt ETA
(tiết kiệm được median **3,1 phút**, max 11,7 phút).

**Đánh giá trung thực**: bug thật, cần sửa, nhưng **không phải nguyên nhân chính** (8,3% số lượt bỏ).

### A5. Ý nghĩa cho advisor — đây mới là root cause của "advisor không có ích"

Trong thế giới này, đòn bẩy lớn nhất **không phải** khi nào nghỉ, mà là **đứng ở đâu**:

- 62% số lượt, đơn chết vì không ai trong bán kính 2,1 km;
- tài xế rỗi median 12 người / 23 km²;
- đơn hết hạn không hề xấu về kinh tế.

Nhưng advisor **không có kênh nào khuyên vị trí**, và **không có state về cung**:
`MarketStateView` mới là spec (ĐA-09, chưa code), **S4 `capacity_alloc` là solver đa-tác-nhân
duy nhất và đang CHẾT** (không producer, không caller — hồ sơ `04`).

⇒ Advisor đang **tối ưu sai biến quyết định**. Nó tinh chỉnh ONLINE/REST/SWAP/END trong khi biến
có đòn bẩy là **vị trí**. Đó là lý do mọi thay đổi về ĐỘ LỚN thu nhập đều inert (hồ sơ `11` §5) —
không phải vì thiếu "giá trị nghỉ".

---

## PHẦN B — Chi phí đổi pin (chỉ thị #2): **có thật, và HOÀN TOÀN chưa vào mô hình**

### B1. Thông tin thực tế — repo đã có, ở `research/economics/income-structure.md`

| Khoản | Số | Nguồn / độ tin |
|---|---|---|
| **Đổi pin tại trạm** | **9.000đ/lần, tối đa 20 lần/tháng/xe** (ưu đãi 10/02/2026–30/06/2028, bản thuê pin) | iMotorbike News 05/2026 — **press/medium**; `vinfastauto.com` trả **403**, chưa xác nhận trực tiếp |
| Thuê pin tháng | ~175–300k | như trên |
| **Sạc** | ~1.000đ/chuyến, ~10.000đ/ngày | press 2023 — **press/medium** |
| "Vào Xanh, Tặng Xe" | **miễn phí thuê pin tới 31/3/2029, đổi pin KHÔNG giới hạn** | Vietnamnet 29/03/2026 — **press/high** |
| RTO Evo 2026 | **miễn phí đổi pin 5 lần/ngày tới 06/2028** | community/medium |

**Đính chính nhẹ phát biểu của Cường**: *"sạc free, đổi pin có phí"* — **ngược lại về mặt cấu
trúc**: sạc **có** phí (nhỏ, ~1.000đ/chuyến), đổi pin **có** phí 9.000đ/lần **nhưng nhiều chương
trình đang miễn phí** (RTO 5 lần/ngày; "Tặng Xe" không giới hạn). ⇒ Chi phí pin **phụ thuộc HỢP
ĐỒNG/CHƯƠNG TRÌNH**, không phải một hằng số. Đây là biến **theo cohort**, phải versioned như policy.

### B2. Trong mô hình: **không có đồng nào**

- `grep swap_cost|charge_cost|energy_cost` toàn `src/` + `configs/` → **rỗng**.
- `payout_vnd` **chỉ cộng** (`+=`) ở 7 chỗ, **không trừ** bất kỳ chi phí nào.
- Config chỉ có **thời gian** và **tầm hoạt động**: `swap_time_s_min/max: 60/120`,
  `swap_range_km: 60`, `home_charge_min: 210`. **Không có tiền.**
- `shift_dp`: nhánh `SWAP` cộng đúng `0.0` — không thu, cũng **không chi**.

### B3. Hệ quả đo được — đúng như Cường nhận xét

| nhóm | n | payout median | cuốc median | online median |
|---|---|---|---|---|
| **SWAP** | 69 | **262.502đ** | 11,0 | 535′ |
| SẠC cắm | 3 | **207.962đ** | 11,0 | 532′ |
| không nạp | 18 | 120.300đ | 5,0 | 236′ |

**Người đổi pin kiếm nhiều hơn 26%** với **cùng số cuốc và cùng số giờ online** — chênh lệch đến
từ việc swap mất 1–2 phút còn sạc mất 210 phút.

**Trong sim, SWAP là chiến lược trội tuyệt đối: nhanh VÀ miễn phí.** Ngoài đời nó **có giá** (hoặc
miễn phí có trần). ⇒ Mô hình đang **thiên vị swap một cách không có căn cứ**, và advisor học theo
sự thiên vị đó.

### B4. Đề nghị (đúng tinh thần "không bịa số")

Thêm **một** tham số có nhãn nguồn, **mặc định = 0** (giữ nguyên hành vi), bật lên mới có tác dụng:

```yaml
vehicle:
  swap_fee_vnd: 0          # 9000 theo iMotorbike 05/2026 (press/medium) — 0 = chương trình miễn phí
  swap_free_per_day: 0     # RTO: 5 lần/ngày miễn phí tới 06/2028
  charge_cost_vnd_per_trip: 0   # ~1000 (press 2023)
```

và **trừ vào `payout_vnd`** như một dòng ledger riêng (không trộn vào `trip_payout`), để
`journey` vẫn tách được 4 nguồn. Đây chính là số hạng **C1 "chi phí vận hành"** của spec objective
v2 — nhưng ở dạng **đo được, có nguồn**, không phải "giá trị nghỉ" mơ hồ.

---

## PHẦN C — Trả lời chỉ thị #1: root cause thật, không cần biến "giá trị nghỉ"

Ba lỗ hổng, xếp theo đòn bẩy, **đều đo được**, **không cái nào cần biến mơ hồ**:

| # | Lỗ hổng | Bằng chứng | Loại |
|---|---|---|---|
| **1** | **Advisor tối ưu SAI BIẾN**: không có kênh khuyên vị trí, không có state cung; S4 chết | 62% lượt đơn chết vì không ai trong 2,1 km; `MarketStateView` chưa code | **MODEL GAP có thể sửa bằng biến ĐO ĐƯỢC** (mật độ cung theo ô×giờ — `public_driver_hex_tracking` 1,37M dòng đã có) |
| **2** | **Chi phí pin/năng lượng = 0** trong mọi công thức | §B; swap trội 26% vì miễn phí | **BUG mô hình hoá** — số có nguồn, thêm được ngay |
| **3** | **Dispatcher bỏ đơn theo tiền đề sai** (ETA đơn điệu) | 293 lượt bỏ oan (8,3%), factor p10 1,24 vs p90 1,94 | **BUG thường** |

**Điểm chung với chẩn đoán cũ**: hồ sơ `11` §5 đo được `p_accept`/`avg_dist_km`/gate thưởng
**inert hoàn toàn** — mọi thay đổi ĐỘ LỚN thu nhập không đổi nghiệm. Nay hiểu vì sao: **biến quyết
định thật (vị trí) không nằm trong bài toán**. Thêm "giá trị nghỉ" cũng sẽ inert theo cùng lý do.

**Vì vậy bỏ hướng C2 "giá trị nghỉ"** (Cường đúng) và chuyển sang ba mục trên — tất cả đều có
**đơn vị đo được và nguồn**, không cần đặt giá cho một thứ không đo được.

## Chưa kiểm (trung thực)

- Toàn bộ số ở seed **1000**, một config. Chưa lặp đa seed cho phần A3/A4.
- Chưa đo **cận trên lợi ích** của việc sửa dispatcher (bỏ oan 8,3%) lên served_rate.
- `9.000đ/lần` là **press/medium**, `vinfastauto.com` 403 — **chưa xác nhận trực tiếp**; phải hỏi
  GSM (nối vào `D-POL-05`) trước khi dùng làm số mặc định khác 0.
- Chưa kiểm archetype nào hay ở "sai chỗ" nhất, và liệu hành vi `relocate` hiện tại có làm tình
  hình tệ hơn không.
