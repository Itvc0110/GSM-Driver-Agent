# UPDATE-185 — Cycle 1: mẫu số tỷ lệ nhận thôi tính những lượt tài xế CHƯA TỪNG ĐƯỢC HỎI

Ngày: 2026-08-09 · Người điều khiển: Cường · Trạng thái: `WAITING-VERDICT`
(visual gate + một test cố ý để đỏ chờ Cường quyết)

## Tóm tắt

Cường quyết xử `Q-07` bằng cách **hiệu chỉnh lại `accept_base` của P7**. Tôi chạy **falsifier cho
chính quyết định đó** trước khi vào plan mode — nó **bắn**, và dẫn tới một lỗi lớn hơn Q-07:

> `world.py:647` tăng `orders_offered` **TRƯỚC** cổng pin ở `:654-664`. Pin không đủ ⇒
> `orders_soc_skipped += 1` rồi `continue` — **`decide_accept` KHÔNG BAO GIỜ được gọi**. Lượt đó
> vẫn nằm trong mẫu số tỷ lệ nhận, tức tính vào tài xế một lượt **họ chưa từng được hỏi**.

Và nó **ăn tiền**: `acceptance_rate` đi thẳng vào `policy.day_bonus`, hàm trả **0** khi acceptance
dưới 0,85 **bất kể điểm**. Đo được **46/900 driver-day (5,11%)** bị đẩy xuống dưới ngưỡng CHỈ vì
skip-pin, **33** thực sự mất tiền, **108.000đ/ngày** trên đội 90.

⇒ `accept_base = 0,94` của P7 **KHÔNG SAI**. Thước đo sai. **Q-07 tự tan.**

## Chi tiết cập nhật

### Thiết kế: giữ `orders_offered`, dẫn xuất `orders_decided`

Hai sự thật khác nhau, giữ cả hai thay vì ghi đè một cái:

- `orders_offered` — dispatcher đã định tuyến bao nhiêu đơn tới đây. **Giữ nguyên**, vì
  `advice_bridge.py:974` cần nó để ước lượng **tốc độ đơn tới**, và tốc độ tới **đúng là** phải
  gồm cả lượt bị chặn vì pin.
- `orders_decided = orders_offered − orders_soc_skipped` — số lần tài xế **thật sự quyết định**
  (chính xác là tập `decide_accept` được gọi). **Mẫu số mới của mọi tỷ lệ nhận.**

Sáu chỗ dùng **cùng một** định nghĩa, không nơi nào tự trừ tay.

### Kết quả đo — SIM

| chỉ số | TRƯỚC | SAU |
| --- | --- | --- |
| lệch `realized − accept_base`, trung bình 7 archetype | −0,0241 | **−0,0050** |
| riêng P7 | −0,0416 | **−0,0142** |
| driver-day dưới ngưỡng thưởng 0,85 | 80/270 | **70/270** |
| thưởng ngày (thành phần) | 14.533đ | **15.900đ** (+1.367đ/người = **123.000đ/ngày**) |
| `forced` (nhận bị ép) | 0,338% | 0,311% |
| `served_rate` · `expired_n` | 0,8033 · 179,2 | 0,8055 · 178,9 |

⚠ Tổng payout dịch **+2.099đ/người**, nhưng **chỉ +1.367đ là thưởng trả lại**; phần còn lại
**+732đ** là **trôi quỹ đạo** (SE của trung bình trên 900 driver-day ≈ 1.846đ ⇒ **không phân biệt
được với 0**). Tôi **không** tính nó là lợi ích.

### Kết quả đo — ĐƯỜNG SẢN PHẨM (sau `scripts/regen_mock.py --days 90`)

| chỉ số | TRƯỚC | SAU |
| --- | --- | --- |
| P1a — thẻ trưng TỔNG mốc | 131/426 = 30,75% | **0/509 = 0%** |
| P1b — lượt trong dải sát ngưỡng | 96 | **81** |
| P1b — cảnh báo **tới tay tài xế** | 0/96 | **81/81 = 100%** |
| mock `acceptance_rate` median | 0,9091 | 0,9231 |
| mock `completed_count` median | 12 | 13 |

**Mục "ngoài scope #2" của plan TỰ ĐÓNG.** Trước bản vá, **32,0%** (56/175) tài xế bị cảnh báo có
tỷ lệ **sạch** đã ngoài dải ⇒ lời khuyên *"đừng từ chối nữa"* **chỉ sai việc** (việc đúng là đổi
pin sớm). Nay mẫu số là lượt **được hỏi**, nên ở trong dải nghĩa là **thật sự đã từ chối** ⇒ câu
chữ đúng nguyên nhân, **không cần sửa lời**.

### Hiệu quả advisor đo lại (30 seed, 3 arm, CÙNG cửa sổ seed của `+3.219đ`)

| bộ | nền A | **B − A (advisor)** | N − A (nhiễu thuần) |
| --- | --- | --- | --- |
| mẫu số **CŨ** | 251.354đ | **+3.219đ** SIG | −769đ ns |
| mẫu số **MỚI** | 252.653đ | **+3.106đ** SIG | −2.378đ **SIG** ⚠ |

✅ Bộ CŨ **tái tạo chính xác** số lịch sử (nền `251.354,155đ`, `B−A +3.219,224đ`,
`expired −16,267`) ⇒ dụng cụ đo đang đo đúng thứ trước đây đã đo.

✅ **Hiệu quả advisor không đổi thực chất** (+3.219 → +3.106, nằm trong CI của nhau). Nền dịch
+1.298đ là **tiền thưởng trả lại**, KHÔNG phải advisor tạo ra.

## Files bị ảnh hưởng

**Sửa (6 chỗ, một định nghĩa):**
- `src/gsm_sim/entities.py` — thêm property `orders_decided`; `acceptance_rate` dùng nó; chặn
  chia 0 (`decided == 0` ⇒ 1.0, giữ đúng quy ước `BUG-DSIM13-02`)
- `src/gsm_sim/journey.py` — `n_decided`; thêm khoá `decided` vào metrics (file này vốn đã báo
  cáo riêng `skipped_soc` mà vẫn để nó trong mẫu số)
- `src/gsm_sim/advice_bridge.py:547` — cổng đủ-mẫu đếm trên `orders_decided`
- `src/gsm_core/mockgen/adapter_sim.py` — xuất thêm `soc_skipped` + `decided`
- `src/gsm_core/mockgen/realdata.py` — `req_accept` dùng `decided`, **có fallback** cho snapshot
  sim cũ không có khoá
- `tests/test_sim_realism.py` — mẫu số cổng realism

**Tạo:** `tests/test_mau_so_ty_le_nhan.py` (6 test) · 4 script+artifact trong
`research/audit/2026-08-08-do-thuc-cua-sim/`

**Sửa test bị vỡ do bản vá:** `tests/test_c1_cost_term.py`, `tests/test_c5_swap_cost.py` (stub
`_A` thiếu `orders_decided`) · `ui/backend/tests/test_p1a_card_dung_tang_them.py` (neo cứng ca
`d-13` — nay fixture **tự tìm** ca hợp lệ)

**Dữ liệu:** `data/mock/realdata-v1/*` regen (không track trong git, chỉ `manifest.json`)

## Assumptions và evidence

| nhãn | nội dung | confidence |
| --- | --- | --- |
| **ĐO** | root cause tại `world.py:647` vs `:654-664` | **CAO** — đọc code + đo 7/7 archetype + `% skip pin` xếp hạng đúng thứ tự độ lệch |
| **ĐO** | 108.000đ/ngày thưởng bị tước oan | CAO — 900 driver-day, và đo lại độc lập ra 123.000đ/ngày |
| **GIẢ ĐỊNH** | lượt bị chặn vì pin **không nên** tính vào tỷ lệ nhận | **TRUNG BÌNH** — đúng với mô hình sim (`decide_accept` không được gọi), nhưng **ngữ nghĩa `total_request_calculate_accept` thật của GSM CHƯA BIẾT** |

## Kiểm chứng

- `uv run pytest -q` → **3 failed, 1210 passed, 4 skipped** (24:35)
- `uv run pytest -q ui/backend/tests` → **224 passed, EXIT=0**

**Ba lỗi đỏ, đã tách nguyên nhân bằng `git stash` chứ không đoán:**
1. `test_demo_trace_neutrality` — **của Khánh**, cây sạch cũng đỏ
2. `test_money_manifest_is_complete` — **của Khánh**, cây sạch cũng đỏ
3. `test_count_positioning_in_budget_flag_is_alive` — **của tôi, CỐ Ý để đỏ** (xem dưới)

### Seeds và scenarios

3300–3329 (đo lại advisor, cùng cửa sổ `+3.219đ`) · 3300–3309 (trước/sau trên cùng seed) ·
3400–3459 (60 seed **mới** kiểm arm NULL) · 1000–1002 (cờ cadence) · regen mock 90 ngày,
`seed_base=7000`

**Chưa kiểm chứng:** ngữ nghĩa tỷ lệ nhận của GSM thật; ảnh hưởng tới `driver_app` của Khánh.

## Visual verification

`BLOCKED` — mock đã regen ⇒ **nội dung card đổi**. Cần Cường xem `d-13 / 2026-09-26 / 14:00`
(hoặc ca mà fixture động chọn) **sau** regen. Gộp được với gate **P1** đang chờ.

## Adversarial self-review / flaws found

1. ⚠ **CÁI GIÁ CHƯA AI NÊU — `acceptance = 1,00` thoái hoá tăng 3.363 → 3.893 (+530)**, tức
   **30,4%** đội. Cơ chế: được chào 5, 1 bị chặn vì pin, nhận 4 ⇒ cũ `4/5 = 0,80`, mới
   `4/4 = 1,00`. Đúng ngữ nghĩa nhưng **làm nặng thêm một khuyết tật độ thực đã có hồ sơ**
   (`realdata.py` docstring: *"sửa caveat R2 acceptance≈1.00"*). → `D-ACC-100`.
2. 🔴 **Tôi TỪ CHỐI tự sửa một test đỏ.** `test_count_positioning_in_budget_flag_is_alive` có ba
   khẳng định; **hai cái cơ chế vẫn xanh** (cờ vẫn tới được engine). Cái đỏ là `sum_on != sum_off`
   — **số emergent**, đúng thứ docstring của chính test cảnh báo không được khẳng định. Đo được:
   **lượt gán = 88 ở CẢ BỐN ô** (cờ tắt/bật × mẫu số cũ/mới) ⇒ cờ nén 3–4 lời khuyên nhưng
   **không đổi ai được điều đi đâu**; khẳng định đó xanh trước đây là nhờ **trôi hỗn loạn**.
   Thêm: số event nén phụ thuộc seed (**3** ở 1000, **0** ở 1001, **1** ở 1002) ⇒ trên seed 1001
   cả khẳng định thứ hai cũng đỏ. Plan của tôi ghi *"phải bàn trước, không sửa test cho xanh"*
   ⇒ **để đỏ, chờ Cường**. → `D-CO-NHIP`.
3. **Giả thuyết "cổng thưởng" của tôi SAI.** Arm NULL đi từ `ns` sang `−2.378đ SIG` sau bản vá;
   tôi đoán do mẫu số sạch đẩy nhiều người tới sát cổng 0,85. Đo tách thành phần: dịch nằm ở
   **phần cuốc** (−2.278đ SIG), **không** ở thưởng (−100đ ns) ⇒ bác. Chạy **60 seed mới độc lập**:
   **+130đ ns** ⇒ lần SIG trước là **may rủi đa phép thử** (1 SIG trên 8 phép thử ≈ 34%).
   Đã kiểm `NoisyWorld` là **bản sao trung thực** (cùng bán kính, thứ tự, sigma, khoá cache) nên
   không phải null đặc tả sai — điều này cũng xác nhận arm NULL của `UPDATE-184`.
4. **Hai lỗi quy trình của tôi trong phiên:** (a) `cmd | tail` làm mã thoát của pipeline là của
   `tail` ⇒ một script **crash** vẫn được báo `exit code 0` (regen lần 1 chết vì cp1252 mà tôi
   suýt tin là xong); (b) test P1a của tôi neo cứng ca `d-13`, vỡ ngay lần regen đầu tiên — nay
   fixture tự tìm ca, và **fail lớn tiếng** thay vì `skip` im lặng nếu không còn ca nào.
5. **Chưa loại trừ:** `min_offers_before_lift` nay chặt hơn (đếm trên `decided ≤ offered`) ⇒ kênh
   `accept_lift` có thể **quiet hơn**; đo được driver-day dưới ngưỡng giảm 80→70 (−12,5%), nhưng
   **chưa đo** số lời khuyên `accept_lift` thực giao. Trong kịch bản test cadence, `advice_given`
   là **rỗng hoàn toàn** — mọi lời khuyên đều bị nén, nên không đo được ở đó.
6. **Bất đối xứng còn treo:** `completed_count` median mock nhảy 12 → 13. Bản vá không chạm số
   chuyến; nhiều khả năng là median nguyên-trị nhảy một bậc do dịch phân phối nhỏ, nhưng
   **tôi chưa chứng minh**.

## Expansion checkpoint

Không mở scope: không đụng `accept_base`, không đổi `candidate_ring_k_max`, không sửa lời khuyên
P1b (tự đóng), không đụng `world.py:647`.

## Follow-up / defer phát sinh

- **`D-ACC-100`** (sev **TB**): acceptance = 1,00 thoái hoá 30,4% đội. Điều kiện xử: cùng lúc với
  bất kỳ việc nào chạm mô hình `decide_accept`, hoặc khi có neo ngoài cho phân phối tỷ lệ nhận.
- **`D-CO-NHIP`** (sev **TB**): cờ `count_positioning_in_budget` nén 3–4 lời khuyên nhưng **0**
  thay đổi allocation ⇒ tác dụng kết cục của nó là **trôi**, không phải nhân quả. Cần Cường quyết
  cách xử test.
- **`Q-07` ĐÃ TAN**: k=8 với mẫu số sạch **QUA cổng realism ở cả 7 archetype** (lệch lớn nhất
  −0,0148 so với dung sai 0,05) ⇒ k=8 nay là lựa chọn **miễn phí**, đổi lấy **−32,6 đơn chết/ngày**.
  Là đổi tham số dispatcher ⇒ **cần Cường quyết riêng**.
- **Hỏi GSM**: `total_request_calculate_accept` thật có đếm lượt hệ thống bỏ qua không? Đây là
  **định nghĩa chính sách của họ**, không phải lựa chọn kỹ thuật của ta.

---

## ⏰ NHẮC LẠI — PENDING-REVIEW (Cường đang chờ check)

- 🔴 **CHẶN — visual gate P1** (nay gồm cả card **sau regen**)
- 🔴 **CHẶN — V-32**
- 🔴 **MỚI — test `test_count_positioning_in_budget_flag_is_alive` đang ĐỎ**, tôi cố ý không tự sửa
- V-31 · K-01(b) ACK · D-QD4-05 · ~27 mục `V-` · Q-03/04/09/10/13
- **amendment ĐA-08** — nên hoãn tới sau cycle 4 (tiền đề *"phút rảnh có giá trị biên ≈ 0"* đã bị
  chính kênh vị trí bác, `UPDATE-184`)
- ⏸ Khánh: 2 test đỏ + Flutter

Hoãn ≠ waive.
