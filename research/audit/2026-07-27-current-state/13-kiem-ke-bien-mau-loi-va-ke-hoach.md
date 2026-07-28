# Kiểm kê biến · Mẫu lỗi lặp lại · Kế hoạch sửa có kiểm thử

Ngày: 2026-07-27 · Trả lời bốn chỉ thị của Cường (tổng hợp root cause, chi phí pin, chờ đơn,
kiểm kê toàn biến). Nối tiếp [`12`](12-root-cause-that-dispatch-pin-cho-don.md).

---

# PHẦN 1 — MẪU LỖI LẶP LẠI: "sửa một tầng, tầng khác không biết"

Trong **một phiên**, đúng một hình dạng lỗi xuất hiện **năm lần**. Đây là phát hiện quan trọng
nhất về mặt quy trình, vì nó dự đoán được chỗ tiếp theo sẽ hỏng.

| # | Sửa/thêm ở đâu | Ai không biết | Hậu quả | Trạng thái |
|---|---|---|---|---|
| 1 | `PolicyBundle.gross_fare` | `routing.py` tự tính `km × 24000` | cước lệch **4,6×**, tài xế nhìn thấy | ✅ UPDATE-075 |
| 2 | S1 trả `feasible=False` (AUDIT A1) | **cả 3 consumer** rẽ nhánh `already_maxed` trước | tài xế mất sạch thưởng, advisor nói *"không có gì cần chỉnh"* | ✅ UPDATE-076 |
| 3 | AUDIT A3 sửa `_gap_sentence` (S1) | `_khoan_sentence` (S5) cùng file, cách 130 dòng | khoán không đạt được vẫn hứa + doạ truy thu | ✅ UPDATE-076 |
| 4 | AUDIT S2-6 thêm `params["bucket_min"]` | **caller duy nhất** không truyền | DP tính bucket 30′ khi sim tiến 60′ | ✅ UPDATE-078 |
| 5 | Hiệu chỉnh `actors.n` 74→90 để đạt `served_rate` | không ai kiểm **thời gian rỗi** | tài xế chờ tới **5,6 giờ** | ⛔ MỞ — T-045d |

**Đặc điểm chung**: bản sửa **đúng**, test của tầng đó **xanh**, nhưng **không có test ở tầng
tiêu thụ**. Và ở #5: tối ưu **một** metric bằng cách chỉnh **một tham số cấu trúc**, không kiểm
metric khác mà tham số đó cũng điều khiển.

### Quy tắc rút ra (áp dụng từ nay)

1. **Fix ở tầng producer PHẢI có test ở tầng consumer/caller.** Test producer xanh không chứng
   minh gì về đường chạy thật.
2. **Thêm tham số mới ⇒ phải có test rằng caller TRUYỀN nó**, không chỉ test solver dùng đúng.
3. **Chỉnh tham số cấu trúc để đạt metric A ⇒ phải in ra metric B, C mà tham số đó điều khiển**,
   ngay trong cùng lần sweep.
4. **Hai tên cho một sự thật = nợ kỹ thuật.** (`bonus_at`/`day_bonus`, `feasible`/`notable`,
   `acceptance_rate` 3 định nghĩa.)

### Chỗ TIẾP THEO có nguy cơ cùng mẫu (chưa kiểm — ứng viên ưu tiên)

| Ứng viên | Vì sao nghi | Cách kiểm |
|---|---|---|
| `bonus_at` (không gate) vs `day_bonus` (có gate) | cùng khái niệm, **khác luật**, không test nào ràng buộc | test parity trên lưới (points × acceptance × completion) |
| `next_tier_gap` chép nguyên văn ở `gsm_core` và `gsm_sim` | đang khớp, **không test nào giữ** | test parity |
| `trip_points` hai bản | như trên | test parity |
| Mọi `DEFAULT_PARAMS` khác của 9 solver | chỉ mới kiểm `shift_dp` | test "caller truyền đủ" cho từng solver được nối |
| `_soc_proxy` (UI) vs `soc_pct=None` (l1r) vs `actor.soc_pct` (sim) | **ba nguồn cho một biến** | xem Phần 3 |

---

# PHẦN 2 — CHI PHÍ PIN: tài liệu + kế hoạch

## 2.1 Sự thật đã kiểm

**Trong mô hình**: `grep swap_cost|charge_cost|energy_cost` toàn `src/` + `configs/` → **rỗng**.
`payout_vnd` chỉ `+=` ở 7 chỗ, **không trừ đồng nào**. Config chỉ có **thời gian**
(`swap_time_s_min/max: 60/120`, `home_charge_min: 210`) và **tầm** (`swap_range_km: 60`).
`shift_dp` nhánh `SWAP` cộng đúng `0.0`.

**Hệ quả đo được** (seed 1000, 90 tài xế):

| nhóm | n | payout median | cuốc median | online median |
|---|---|---|---|---|
| **SWAP** | 69 | **262.502đ** | 11,0 | 535′ |
| SẠC cắm | 3 | 207.962đ | 11,0 | 532′ |
| không nạp | 18 | 120.300đ | 5,0 | 236′ |

**SWAP trội 26% với CÙNG số cuốc và CÙNG giờ online** — vì swap mất 1–2 phút còn sạc mất 210
phút, **và cả hai đều miễn phí trong mô hình**.

## 2.2 Số thực tế (đã có trong `research/economics/income-structure.md`, không phải mới tìm)

| Khoản | Số | Nguồn / độ tin |
|---|---|---|
| Đổi pin tại trạm | **9.000đ/lần, tối đa 20 lần/tháng** (10/02/2026–30/06/2028, bản thuê pin) | iMotorbike 05/2026 — **press/medium**; `vinfastauto.com` **403** |
| Thuê pin tháng | 175–300k | như trên |
| Sạc | ~1.000đ/chuyến, ~10.000đ/ngày | press 2023 — **press/medium** |
| "Vào Xanh, Tặng Xe" | **miễn phí thuê pin tới 31/3/2029, đổi pin KHÔNG giới hạn** | Vietnamnet 29/03/2026 — **press/high** |
| RTO Evo 2026 | **miễn phí đổi pin 5 lần/ngày tới 06/2028** | community/medium |

⚠ **Đính chính phát biểu ban đầu**: không phải *"sạc free, đổi pin có phí"*. Sạc **có** phí nhỏ;
đổi pin **có** giá niêm yết **nhưng nhiều chương trình đang miễn phí có trần**. ⇒ chi phí pin là
biến **theo cohort/hợp đồng**, phải **versioned như policy**, không phải hằng số toàn cục.

## 2.3 Kế hoạch (T-045b)

**Bước 1 — schema & config, mặc định GIỮ NGUYÊN hành vi**

```yaml
vehicle:
  swap_fee_vnd: 0              # 9000 (press/medium) — 0 = cohort đang miễn phí
  swap_free_per_day: 0         # RTO: 5
  charge_cost_vnd_per_trip: 0  # ~1000 (press 2023)
```

Đưa vào `policy_bundle` (versioned, theo cohort), **không** hard-code trong world.

**Bước 2 — ledger riêng, không trộn**: thêm `energy_cost_vnd` là **dòng thứ 5** của ledger, để
`journey` vẫn tách được 4 nguồn thu và 1 dòng chi. `payout_vnd` giữ nguyên nghĩa (thu), thêm
`net_after_energy_vnd`. **Không** đổi nghĩa trường cũ (bài học "hai tên một sự thật").

**Bước 3 — vào solver**: `shift_dp` nhánh `SWAP` trừ `swap_fee` (tính cả trần miễn phí đã dùng
trong ngày ⇒ **cần state mới `swaps_today`**).

**Kiểm thử bắt buộc**

| Test | Nội dung | Loại |
|---|---|---|
| `test_energy_cost_default_zero_is_noop` | mặc định 0 ⇒ payout **y hệt** bit-for-bit trên 5 seed | regression |
| `test_swap_fee_reduces_net_not_gross` | phí trừ vào `net_after_energy`, **không** đụng `gross`/`trip_payout` | boundary tiền |
| `test_free_swap_cap_respected` | `swap_free_per_day=5` ⇒ 5 lần đầu 0đ, lần 6 mới tính phí | logic trần |
| `test_dp_prefers_charge_when_swap_expensive` | đặt `swap_fee` rất cao ⇒ DP chuyển sang sạc | hành vi solver |
| `test_swap_advantage_shrinks_with_fee` | quét `swap_fee` ∈ {0, 9k, 20k} × 10 seed ⇒ chênh lệch SWAP−SẠC **giảm đơn điệu** | độ nhạy |

**Chưa được làm trước khi có**: xác nhận số từ GSM (`D-POL-05`). Cho tới lúc đó **mặc định phải
là 0** và mọi kết quả bật phí phải mang nhãn **ASSUMPTION**.

---

# PHẦN 3 — KIỂM KÊ BIẾN: nguồn · cách dùng · độ bền

## 3.1 Nguyên tắc phân loại

- **REAL-SCHEMA**: suy được từ 13 bảng L1R (schema GSM cấp).
- **SIM-ONLY**: chỉ tồn tại trong simulator, **13 bảng không có**.
- **FUTURE**: cần GSM cấp thêm (đã liệt kê G1–G6 ở spec objective v2 §4).
- **PROXY/BỊA**: sinh ra bằng heuristic/hash, **không phải đo**.

## 3.2 Biến vào của hai solver ĐANG CHẠY

### S1 `bonus_gap_input` — **lành mạnh**

| Trường | Nguồn | Ghi chú |
|---|---|---|
| `points_now` | **REAL-SCHEMA** | `trips` + policy |
| `next_tiers` | **REAL-SCHEMA** | policy bundle |
| `historical_points_per_hour` | **REAL-SCHEMA** | `trips` + `driver_online_hours_sap_id`, ≤7 ngày trước |
| `hours_budget_remaining` | **PROXY** | UI dùng hằng `DEFAULT_SHIFT_END_MIN = 22*60`; tài xế thật kết ca khác nhau |
| `acceptance_rate` / `completion_rate` | **REAL-SCHEMA** | ✅ đã sửa rò tương lai (UPDATE-077) |

⇒ S1 **chạy được trên data thật**. Điểm yếu duy nhất: giờ kết ca là hằng số.

### S2 `shift_plan_input` — ⛔ **có một biến KHÔNG TỒN TẠI trong data thật**

| Trường | Nguồn | Ghi chú |
|---|---|---|
| `buckets_remaining` | **PROXY** | phụ thuộc giờ kết ca giả định |
| **`soc_pct`** | ⛔ **SIM-ONLY** | **Không bảng nào trong 13 bảng có cột pin** (đã grep toàn schema: `soc/batter/pin` → **KHÔNG CÓ**) |
| `points_now` | REAL-SCHEMA | |
| `demand_forecast` | **PROXY** | sim: belief cá nhân của actor; l1r: mật độ `trips` lịch sử. **Không phải cầu thật tương lai** |

**Ba đường, ba hành vi khác nhau cho `soc_pct`:**

| Đường | Giá trị | Hệ quả |
|---|---|---|
| **sim** (`advice_bridge`) | telemetry thật `actor.soc_pct` | S2 lập lịch SWAP đúng |
| **l1r** (`from_l1r.py:450`) | **`None`** | `shift_dp:125` ⇒ `soc0 = NS-1` = **giả định pin ĐẦY**, im lặng, không hạ confidence |
| **UI** (`mockdata._soc_proxy`) | **sha256(driver\|date) → 30..95** | **số BỊA**, và **hiển thị cho tài xế**: `app.js:99` `⚡ {soc}%`, tô đỏ khi <25% |

⇒ **Ba lỗi trong một biến**: (a) không có nguồn thật; (b) fallback ngầm "pin đầy" — nguy hiểm vì
khuyên tài xế 15% pin như thể 100%; (c) **số bịa hiển thị cho tài xế không có nhãn trên UI**
(nhãn PROXY chỉ nằm trong docstring Python) — vi phạm ranh giới `CLAUDE.md §5` *"mock phải gắn
nhãn mock"*.

**Đính chính phạm vi (trung thực)**: S2 hiện **chưa được nối vào UI** — `adapters/advisor.py` chỉ
gọi S1. Nên (b) là **blocker tương lai**, chưa phải lỗi đang chạy. Nhưng (c) **đang chạy hôm nay**.

## 3.2b PIN: đã có tác động lên sim, và ĐÃ LÀ biến tối ưu — nhưng mô hình hoá lạc quan

Câu hỏi Cường (2026-07-28): *"pin nên có tác động lên sim, phải có giả lập hành vi dựa trên lượng
pin, kiểm tra xem có chưa? nếu muốn đưa vào làm biến tối ưu… thì cũng phải tính kỹ"*.

### (a) Trong SIM: CÓ, và ràng buộc thật — nhưng vừa phải

| Cơ chế | Vị trí | Đo được (seed 1000) |
|---|---|---|
| Bỏ đơn vì **không đủ pin** đi hết cuốc | `world.py:342` `enough = soc − total_km·pct_per_km > 8.0` | **41 lần = 3,5%** lượt chào · **27/90** tài xế dính |
| Tự đi đổi pin khi dưới ngưỡng | `behavior.py:131-134`, `swap_soc_threshold_pct: 20` | **133** lượt |
| Đổi pin **THẤT BẠI** (trạm hết pin sẵn trong `wait_cap` 60′) | `world.py:721-750` | **15/133 = 11%** |
| **Hết pin giữa đường** | `world.py:427` `battery_stranded` | **0** — ngưỡng đang chặn được |
| Hàng chờ tủ pin | `station.queue_len`, tồn kho từng viên + `battery_recharge_min: 105` | chờ median **0′**, **max 50′** |
| Tiêu hao theo quãng đường | `consume_soc` ở 6 chỗ (đón · cuốc · relocate · tới trạm) | SOC cuối ngày min **8%**, median **57%** |

⇒ **Không cần thêm cơ chế hành vi mới** — pin đã gate nhận đơn, sinh chuyến đi đổi pin, có
thất bại và hàng chờ. Đây là khác biệt lớn so với **mệt mỏi** (chỉ khiến tự nghỉ, không hậu quả).

### (b) Trong SOLVER: SOC ĐÃ là một chiều state của DP

`shift_dp` có `soc_bands = 10`, `_soc_cost(params)` trừ SOC mỗi bucket ONLINE, và hành động
`SWAP` nạp về đầy. **Không phải biến mới.**

### (c) NHƯNG mô hình `SWAP` lệch sim ở BỐN điểm — đây là phần "phải tính kỹ"

```python
# shift_dp.py — toàn bộ mô hình SWAP:
v = 0.0 + V[b + 1, NS - 1, pb, rl]     # nạp đầy, tốn đúng 1 bucket, hết
```

| # | DP giả định | Sim/thực tế | Chiều lệch |
|---|---|---|---|
| 1 | SWAP **luôn thành công** | **11% thất bại** (trạm hết pin) | DP **lạc quan** |
| 2 | SWAP tốn **đúng 1 bucket = 60′** | đi + đổi 1–2′ + chờ (median 0′, max 50′) ≈ **10–20′** | DP **bi quan** ⇒ swap **ít hơn** tối ưu |
| 3 | SWAP **không cần đi đâu** | phải di chuyển tới trạm (11 trạm, phân bố lệch Đông/Tây) | DP **lạc quan** |
| 4 | SWAP **miễn phí** | 9.000đ/lần hoặc miễn phí-có-trần (T-045b) | DP **lạc quan** |

Hai chiều lệch **triệt tiêu một phần nhau**, nên không thể đoán dấu tổng — **phải đo**, không suy.

### (d) Và trên DATA THẬT thì cả chiều này **inert**

`from_l1r.py:450` trả `soc_pct = None` ⇒ `shift_dp.py:125` `soc0 = NS − 1` = **giả định pin đầy**,
im lặng, không hạ confidence. ⇒ Mọi cải tiến mô hình SOC **chỉ có tác dụng trong sim** cho tới khi
GSM cấp telemetry (`D-POL-05`).

### (e) Kết luận: thứ tự đúng nếu muốn nâng cấp SOC thành biến tối ưu tử tế

1. **Trước hết đo xem SOC có phải ràng buộc BINDING không** — hiện 3,5% lượt chào. Nếu sau khi
   sửa cung–cầu (T-045d) tỷ lệ này vẫn nhỏ thì **đừng đầu tư** vào mô hình SOC tinh vi.
2. Nếu binding: sửa **#2 trước** (chi phí thời gian SWAP thực tế thay vì cứng 1 bucket) — đây là
   sai lệch **lớn nhất về độ lớn** và không cần dữ liệu mới.
3. Rồi **#1 + #3** (xác suất thất bại + khoảng cách trạm) — cần `station_queue` trong
   `MarketStateView` (**T-045a**), nên **phụ thuộc T-045a**.
4. **#4 (chi phí tiền) = T-045b**, mặc định 0, chờ `D-POL-05`.
5. **Không** đưa SOC vào **agent reasoning** — nó là ràng buộc vật lý, mô hình hoá được chính xác,
   nên thuộc về solver. (Đúng tiêu chí Cường: chỉ tạo biến khi mô hình hoá được chính xác.)

**Điều kiện chấp nhận cho mỗi bước**: đo lại chỉ tiêu kép + `order_skipped_soc`, `swap_failed`,
`battery_stranded` **không được xấu đi**.

## 3.3 Biến sim-only khác mà advisor đang dựa vào

| Biến | Nguồn | Có ở data thật? |
|---|---|---|
| `soc_pct` | sim telemetry | ❌ |
| `actor.cell` realtime | sim | ⚠ có gián tiếp: `public_driver_hex_tracking.current_hex` (**1,37M dòng, chưa khai thác**) |
| `open_orders` (đơn chưa gán) | sim | ❌ — 13 bảng chỉ có đơn đã hoàn thành |
| `Station.queue_len` | sim | ❌ |
| `congestion.r(cell,hour)` | sim | ⚠ thay được bằng OSRM |
| `accept_base` (tham số sinh hành vi) | sim | ❌ — **dùng nó trong advisor là oracle nhẹ** (UPDATE-078 §5) |

## 3.4 Robustness: mô hình có bền khi biến đổi/thiếu/thêm không?

**Kiểm bằng cách đọc code, chưa chạy test** (đó là việc phải làm — xem Phần 4):

| Kịch bản | Hành vi hiện tại | Đánh giá |
|---|---|---|
| `soc_pct` **thiếu** | im lặng giả định **pin đầy**; confidence **không đổi** | ⛔ **hidden fallback** — đúng mẫu `supply_cell_hhi` trả 0.0 im lặng |
| `acceptance_rate` thiếu | `_bonus_eligible` trả `(True, False)` = "giữ bonus + caveat" | ✅ có chủ ý, có caveat |
| `historical_points_per_hour` thiếu | rơi về `points_per_trip_estimate` lý thuyết, `source="dp:fallback"`, confidence 0.5 | ✅ **mẫu TỐT — nên nhân rộng** |
| `demand_forecast` rỗng | `_forecast_arrays` điền demand 0 | ⚠ im lặng; nên hạ confidence |
| **thêm** biến mới | schema `additionalProperties` + `schema_version.const` một giá trị | ⛔ **B-02 ARCH-VERSION** — registry chỉ load một phiên bản |
| giá trị biến **đổi thang** (vd policy đổi mốc) | policy versioned ✅ nhưng data parquet sinh lúc regen | ⚠ lệch câm (hồ sơ `08` #4) |

**Kết luận**: mô hình **KHÔNG robust** theo nghĩa Cường hỏi. Chỗ tốt (`historical_points_per_hour`)
chứng minh **mẫu đúng đã tồn tại trong repo** — vấn đề là **không áp dụng nhất quán**.

## 3.5 "Mô hình hoá hay agent suy luận?" — bản dịch công thức → action

Đường đi hiện tại, đã đọc code:

```
L1R (13 bảng thật) ──derive──► L3 view ──► SOLVER (thuần toán, deterministic)
        │                                        │
        └─ PROXY/SIM-ONLY chen vào đây           ▼
                                          SolverReport{solution, numbers[], confidence}
                                                 │
                        ┌────────────────────────┴───────────────────┐
                        ▼                                            ▼
        sim: `_map_action(solver_action, actor)`      UI: `adapters/advisor` → card
                        │                                            │
                   adherence draw (RNG)                        verifier V1..V4
                        ▼                                            ▼
                   actor action                              JSON contract
```

**Agent/LLM KHÔNG tham gia** ở bất kỳ đâu trong đường này — toàn bộ là rule/math. Đúng ranh giới
`CLAUDE.md §5`. Nhưng có **hai chỗ dịch** dễ sai và **chỉ một chỗ có test**:

1. `_map_action(solver_action, actor)` — dịch `ONLINE/REST/SWAP/END` sang hành vi actor.
   **Bẫy đã ghi trong docstring**: `next_action` **không** phải hành động tức thời; phải lấy
   `schedule[0]`. Có test.
2. `adapters/advisor` — dịch SolverReport sang card. **Đây là chỗ đã sinh ra 2/5 lỗi** ở Phần 1.

⇒ Đề nghị: **mọi bản dịch solver→action/card phải có test ở tầng dịch**, không chỉ ở solver.

---

# PHẦN 4 — KẾ HOẠCH: chờ đơn / dispatch (T-045c + T-045d)

## 4.1 Chuỗi nhân quả đã chứng minh

```
world = 1 quận, demand.orders_per_day = 1200          (trần cấu trúc, D-SIM-01 đã ghi)
        │
        ├─ hiệu chỉnh actors.n 74→90 để kéo served_rate lên 0.797 ✅
        │        └─ hệ quả KHÔNG ai kiểm: 13,4 đơn/tài xế/ngày · 1,19 cuốc/giờ-online
        │                                   ⇒ tài xế rỗi ~75% thời gian
        ▼
12 tài xế RỖI trải trên 23 km²  ⇒  k/c tới người gần nhất median 2,46 km
        │                            > bán kính dispatch k=6 (~2,1 km)
        ▼
62% lượt: shortlist H3 RỖNG  ⇒  đơn chết mà CHƯA BAO GIỜ được chào (85,7%)
        │                        (đơn hết hạn KHÔNG xấu: gross 24.151đ vs 24.734đ)
        ▼
TRIỆU CHỨNG: khoảng chờ MAX 334 phút; đơn hết hạn 20–30% giờ cao điểm
        + BUG dispatcher cộng thêm 8,3% lượt bỏ oan
```

## 4.2 Ba giả thuyết, và cái nào đã bị loại

| Giả thuyết | Trạng thái |
|---|---|
| Đơn xấu nên bị chê | ❌ **LOẠI** — gross/km gần như bằng đơn được phục vụ; tỷ lệ nhận 90,8% |
| Không có tài xế nào ở gần | ❌ **LOẠI** — 100% đơn hết hạn có người rỗi <5 km |
| **Mật độ cung quá thưa so với bán kính dispatch** | ✅ **XÁC NHẬN** — 62% lượt shortlist rỗng |
| Thuật toán dispatch có bug | ✅ **XÁC NHẬN nhưng THỨ CẤP** — 8,3% lượt bỏ |

## 4.3 Phương án — theo thứ tự, mỗi bước có test

### T-045c — sửa BUG dispatcher (hẹp, làm được ngay)

`dispatcher.py:77`: bỏ đơn khi người **gần nhất theo haversine** fail ETA, viện lý do *"ETA đơn
điệu theo distance"*. Tiền đề sai vì `factor` theo cặp ô p10 **1,24** → p90 **1,94**.

**Sửa**: xếp hạng ứng viên theo **ETA thật** (`dist × factor / speed`), không theo haversine; và
**thử tiếp** ứng viên kế nếu người đầu fail ETA (có trần số lần thử để giữ O(1) mỗi đơn).

| Test | Nội dung |
|---|---|
| `test_eta_not_monotonic_in_distance` | fixture 2 tài xế: gần+đường xấu vs xa+đường tốt ⇒ **phải chọn người xa hơn** |
| `test_order_not_dropped_when_another_candidate_passes_eta` | tái lập đúng 293 ca bỏ oan ⇒ phải gán được |
| `test_determinism_unchanged` | cùng seed ⇒ cùng kết quả (tie-break vẫn `(eta, actor_id)`) |
| `test_no_regression_served_rate` | 10 seed: served_rate **không giảm** |

**Kỳ vọng**: served_rate tăng nhẹ. **Không** kỳ vọng giải quyết được chờ-hàng-giờ (chỉ 8,3%).

### T-045d — sửa gốc: cân đối cung–cầu–không gian (cần Cường quyết)

Ba lựa chọn, **loại trừ nhau**, tôi khuyến nghị **(B)**:

| | Phương án | Ưu | Nhược |
|---|---|---|---|
| **A** | Giảm `actors.n` về ~70 | rẻ, 1 dòng | `served_rate` tụt về 0,74 — chính cái đã bị Cường chỉ ra là khuyết tật |
| **B** ⭐ | **Mở rộng zone (liên quận)** — đúng như D-SIM-01 đã đề xuất và bị defer | phản ánh **thực tế** (tài xế chạy liên quận); giải cả served_rate lẫn trips/driver | tốn công: cần lại demand/POI/OSRM matrix cho vùng lớn hơn |
| **C** | Tăng `demand.orders_per_day` giữ nguyên 1 quận | rẻ | **bịa cầu** — 1200 là con số của 1 quận; nâng lên là bỏ căn cứ |

**Vì sao (B)**: cả `served_rate` và `trips/driver` **không thể cùng đạt** khi cầu bị chặn ở 1 quận
(D-SIM-01 nói đúng). Chỉ mở rộng không gian mới gỡ được ràng buộc, và nó **đúng thực tế** — đây
chính là điều Cường vừa nhắc: *"thực tế tài xế không phải đợi hàng tiếng"*.

| Test cho T-045d |
|---|
| `test_trips_per_driver_in_research_range` — 10 seed: trips/driver ∈ **[15, 22]** (research 18–22, chấp nhận biên dưới) |
| `test_idle_gap_p99_under_threshold` — p99 khoảng chờ **< 60 phút**; **không** khoảng nào > 180 phút |
| `test_served_rate_still_realistic` — served ∈ [0,78; 0,88] |
| `test_orders_per_driver_hour` — ≥ 2,0 đơn được chào/giờ-online |
| **Cả bốn phải xanh CÙNG LÚC** — đó chính là bài học #5 ở Phần 1 |

⚠ **Ràng buộc**: T-045d **làm lệch toàn bộ baseline** ⇒ phải đo lại 30 seed + chỉ tiêu kép, và
**mọi kết luận A/B trước đó phải gắn nhãn "đo trong thế giới 1 quận"**.

---

# PHẦN 5 — Chưa kiểm (trung thực)

- Toàn bộ số Phần 4 ở **seed 1000**, một config. Chưa lặp đa seed cho phân phối khoảng chờ.
- Chưa đo **cận trên** lợi ích của T-045c lên served_rate.
- Kiểm kê Phần 3 làm bằng **đọc code + grep schema**, **chưa có test tự động** ràng buộc
  "biến X phải suy được từ 13 bảng". Đó là test nên viết (`test_l3_views_derivable_from_l1r`).
- Chưa kiểm 7 solver còn lại (S3, S5–S9) theo cùng cách; mới soi S1/S2.
- Số chi phí pin là **press/medium**, chưa xác nhận trực tiếp từ GSM.
