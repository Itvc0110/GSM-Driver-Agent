# UPDATE-180 — Cycle 3 + Cycle 4 + Cycle 2: **hai cổng thường trực** và **năm bề mặt bằng chứng** được đính chính

- **Ngày:** 2026-08-07
- **Loại:** implementation (2 cổng mới, 3 khoá config, 1 hàm gộp) + docs correction
- **Plan:** `tracking/PLAN-2026-08-07-todo-cycle-lam-het.md` (Cường **duyệt** 2026-08-07) ·
  cycle canonical `research/audit/2026-08-07-root-cause-classes/00-BAN-DO-LOP.md`
- **Phán quyết uỷ quyền:** `tracking/PHAN-QUYET-2026-08-07-bon-quyet-dinh-uy-quyen.md`

---

## 1. CYCLE 3 — cổng khoá config, viết **MỘT LẦN**

### Lỗi (reproduce 1 lệnh)
`Config.get(dotted, default)` trả default **im lặng** khi path vắng. Ba dòng sống nhờ đó:

| chỗ | đọc | khoá THẬT | rơi về |
| --- | --- | --- | --- |
| `advice_bridge.py:202` | `orders.trip_km_median` | `demand.trip_km_median` | 3.5 |
| `advice_bridge.py:209` | `orders.cancel_after_accept_rate` | `behavior.cancel_after_accept_rate` | 0.05 |
| `world.py:172` | `dispatcher.offer_cooldown_min` | **không có trong yaml** | 10.0 |

Cả ba **vô hại tới nay** vì default **tình cờ trùng** giá trị config — đúng dấu hiệu chẩn đoán của
lớp này. Cái giá thật: **ai sweep khoá đúng sẽ thấy Δ = 0 và kết luận SAI** rằng tham số không
ảnh hưởng — một kết luận sai **trông như được dữ liệu hậu thuẫn**.

### ⭐ Vì sao cổng CŨ không bắt được — và đây là phần đáng đọc nhất
`test_config_flags_wired.py:80` khớp theo **TÊN LÁ**: nó tìm token `trip_km_median` trong source.
Chuỗi `"orders.trip_km_median"` **chứa đúng token đó** ⇒ cổng kết luận `demand.trip_km_median`
*"đã có người đọc"*.

> **Chính dòng hỏng đã bảo lãnh cho khoá đúng. Cổng bị con bug nó đi bắt qua mặt.**

### Việc đã làm
- **`tests/test_config_key_ton_tai.py` (MỚI)** — chiều NGƯỢC (code → config), AST-scan mọi
  `<cfg-like>.get("a.b")`, khớp **đường dẫn đầy đủ**. Kèm **đối chứng dương tính** (dựng khoá ma
  trong cây tạm, đòi scanner bắt được) và test *"sửa xong thì config THỰC SỰ CÓ RĂNG"*.
- **`test_config_flags_wired.py`** — `_co_nguoi_doc()` thay khớp-tên-lá bằng khớp-đường-dẫn:
  *lần xuất hiện **hỏng** = tên lá đi ngay sau `<namespace>.` với namespace KHÁC block cha thật*.
  Kèm đối chứng dương tính dựng lại **nguyên văn** dòng hỏng và đòi cổng ĐỎ.
- Sửa 2 khoá; **thêm `dispatcher.offer_cooldown_min: 10`** vào yaml (giá trị = đúng default cũ)
  kèm cảnh báo **đọc `D-SIM-K6` trước khi sweep** (cooldown 10′ ≥ `patience_max_min` 10′ ⇒ nó
  hiện là ràng buộc **CÂM**; sweep mà không biết sẽ đọc ra đường phẳng và tưởng đã đo xong).

### Acceptance — ĐẠT
| tiêu chí | kết quả |
| --- | --- |
| scanner khoá ma | **4 → 0** |
| cổng đỏ-trước | ✅ 3 test đỏ đúng chỗ trước khi sửa |
| **BIT-IDENTICAL** | ✅ **5/5 seed** (1000–1004), fingerprint **trùng từng ký tự** trước/sau (`git stash` để đo arm trước) |
| config có răng | ✅ `demand.trip_km_median=9.0` ⇒ đọc ra 9.0; namespace sai vẫn rơi default |

⭐ **Cổng bắt ngay chính test tôi vừa viết** (`cfg.get(dotted)` với biến) ở lần chạy kế — bằng
chứng nó có răng thật, không phải xanh rỗng. Đã khai vào `DOC_BANG_BIEN` kèm lý do.

⚠ **Một thiết kế của tôi bị chính phép đo bác:** bản đầu ghim **0** call site `cfg.get(<biến>)`
theo đề xuất bản đồ. Chạy ra **5**, và cả 5 **chính đáng** (duyệt vòng lặp khoá, helper nhận
`key`). Ghim 0 ⇒ cổng luôn đỏ ⇒ bị tắt ⇒ mất luôn phần có ích. Đổi sang **ghim DANH MỤC**.

---

## 2. CYCLE 4 — cổng một chiều phải **THỰC SỰ SOI**

### Lỗi (lần thứ **BA** cùng một khuôn)
`_ONE_WAY_PREFIXES = ("veto_", "xveto_", "commit_")` đẩy 3 họ khoá **RA KHỎI** bảng significance
hai chiều (đúng — chống Goodhart). Nhưng `aggregate_health_guardrail` có danh sách **chép tay**
chỉ gồm `veto_*`, và `health_guardrail_flags` chỉ lặp `REST_RAILS`.

⇒ **7 khoá** ngoài tầm soi, **9 khoá** không vào `a_mean` — trong khi artifact vẫn in cạnh chúng
`"one_way_gate": "health_guardrail_flags"`, tức **một lời khai quản trị KHÔNG CÓ THẬT**.

`parallel.py:415-419` **tự chép** rằng danh sách tường minh *"đã HỞ hai lần"*. Bản vá lần đó nối
đúng **chiều đi ra**, **quên chiều đi vào**. Sửa nửa đường — nửa còn lại im lặng.

### Việc đã làm
- `aggregate_health_guardrail.keys` **SUY RA từ chính các hằng rail** (`REST_RAILS`,
  `EXTEND_RAILS`, `COMMIT_KEYS`) — thêm rail mới là nó **tự vào**, không cần ai nhớ.
- `health_guardrail_flags` nay soi **cả hai họ** lan can, **cộng ba nhánh mới**:
  (i-b) **rail CHƯA TỪNG BẮN** dù cổng có chạy — nhánh mà cổng cũ **mù** (nó đòi `va ≥ 20`, nên
  rail bất khả đạt không bao giờ làm nó nổ; đo được `veto_soc_low_n = 0,0` cả hai arm/30 seed);
  (i-c) **sổ CAM KẾT** — `commit_kept_n` sụp về 0, và bảo toàn `kept+broken+cleared ≤ made`.
- **`sim_metrics.RAIL_KHAI_TRO`** — rail trơ CÓ CHỦ Ý phải khai kèm **lý do + ĐIỀU KIỆN MỞ LẠI**
  (khuôn `defer_cap` đã dùng). Khai 2: `veto_soc_low_n` (bất khả đạt sau `D-M3-04-FIX`) và
  `veto_defer_cap_n` (đã có test khai trơ).
- **`tests/test_tang5_khong_co_vung_mu.py` (MỚI)** — 11 test, gồm **hai đối chứng ngược**:
  mẫu số/tổng **KHÔNG được** soi riêng (soi chúng = tạo **chiều khen** cho veto cao), và
  **kênh TẮT không được tố giác nhầm** (mẫu số 0 = cổng không chạy, khác *"lan can vô dụng"*).

### Acceptance — ĐẠT
| tiêu chí | trước | sau |
| --- | --- | --- |
| vùng mù của cổng | **7 khoá** | **0** |
| vắng mặt khỏi `a_mean` | **9 khoá** | **0** |
| test tầng 5 liên quan | — | **52 passed** |

⚠ **Harness của chính tôi sập bẫy fixture suy biến (L2):** bản đầu đặt MỌI khoá = 100 ⇒
`kept+broken+cleared = 300 > made = 100` ⇒ cờ *"vỡ bảo toàn"* nổ **trước khi tiêm gì** ⇒ phép đo
vô nghĩa. Đã thêm `test_nen_phai_SACH_CO_truoc_khi_tiem` ghim lại.

---

## 3. CYCLE 2 — năm bề mặt bằng chứng (docs-only)

| # | chỗ | đính chính | tôi tự kiểm |
| --- | --- | --- | --- |
| **E1** | `docs/reports/week2/…:161-174` **(BÁO CÁO GỬI MENTOR)** | Thêm **cột Trạng thái**. Tự đếm `.solve()` ngoài package: **5/9 solver có 0 lời gọi** (S3, S5, S6, S8, S9) — **không phải 3/9** như bản đồ ghi. Đường sản phẩm thật chạy **S1** (+S2 khi đủ state). Tách *"quy tắc thiết kế"* khỏi *"trạng thái thi công"* | ✅ đếm bằng lệnh |
| **E2** | `pilot_dongda.yaml:399` + `advice_bridge.py:773` (bản CHÉP) | Khẳng định *"vách đá … mất 34k"* **đã bị RÚT** ở `UPDATE-048` §2 (30 seed: nhóm không chạm ngưỡng Δpayout **+18.207đ DƯƠNG**; −34k là **một seed cá biệt**). Giữ tham số, **bỏ lý lẽ đã rút**, giữ lý lẽ còn đứng | ✅ mở `UPDATE-048` đọc |
| **E3** | `shift_dp.py:16` | `ACTIONS` là **mã hoá chỉ số** của `best_a`, **không phải** tie-break. Thứ tự thật **ONLINE → SWAP → REST → END** (`:228,244,249,254`) | ✅ đọc 4 nhánh |
| **E4** | `UPDATE-097:15` | *"consumer đủ số để tính net"* **SAI dưới config ship**: `swap_fee=0` ⇒ `expected_swap_cost_vnd` **luôn 0.0** và `n_swaps` **không expose** ⇒ lịch 7 SWAP **giống hệt** lịch 0 SWAP | ✅ đọc `solution` dict |
| **E5** | `UPDATE-078:157` | Hai nhãn `OBSERVED-CONFIG` là **SAI** — nhãn đúng là `ASSUMED-DEFAULT`. ⚠ **Cái KHÔNG bị lật:** *giá trị* 3.5 vẫn đúng nên kết luận `~40%` của `mm-07-s2` **vẫn đứng**; sai là **provenance** | ✅ |

**Cộng thêm — chặn hai phép đo NO-OP:**
- `DEFERRED.md` `D-E4-01`: điều kiện mở lại **đã sửa**. `cash_cost` **bất biến TỪNG BIT** trên
  **[0; 4.325]đ/km** (ngưỡng lật = **17–62× giá thật**) ⇒ **⛔ không sweep {0,70,150,250}** —
  Δ=0 rất dễ đọc thành *"chi phí không quan trọng"*.
- `PLAN-cycle-wx-2026-07-29.md:108`: gạch bỏ đúng phép sweep đó kèm lý do cấu trúc.

---

## Kiểm chứng

- **Fingerprint 5 seed BIT-IDENTICAL** trước/sau Cycle 3 (đo bằng `git stash`, không lập luận).
- Cổng mới: `test_config_key_ton_tai.py` **16 passed** (cùng `test_config_flags_wired.py`) ·
  `test_tang5_khong_co_vung_mu.py` **11 passed** · nhóm tầng 5 (`rest_rails`, `shift_extend_rails`,
  `rest_commit`, mới) **52 passed**.
- Probe độc lập: khoá ma **4 → 0** · vùng mù tầng 5 **7 → 0** · vắng `a_mean` **9 → 0**.
- **Suite đầy đủ** (chạy **CẢ HAI** — bẫy `testpaths` chỉ thu `tests/`):
  - `ui/backend/tests`: **205 passed** ✅
  - `tests/`: lần 1 ra **1187 passed / 3 failed / 4 skipped**. Baseline là **2 failed** (của
    Khánh) ⇒ tôi truy ngay 1 lỗi mới.

### ⚠ Bài học vừa trả giá: **sửa file trong lúc suite chạy nền làm HỎNG chính phép đo**

Lỗi mới là `test_e1b_cong_thuc_kenh.py::test_gate_accept_lift_khong_parse_chuoi`. Nó **XANH khi
chạy riêng**. Nguyên nhân: test dùng `inspect.getsource(...)`, mà `inspect` đọc qua `linecache`
theo **số dòng** — và tôi đã **sửa `advice_bridge.py` (đính chính E2) trong lúc suite đang chạy
nền** ⇒ offset dòng dịch ⇒ `getsource` trả về lát cắt sai của file.

Xác định vế nào là của ai bằng cách **stash rồi chạy lại** đúng 3 test đó trên baseline:
`test_demo_trace_neutrality` và `test_health_boundary::test_money_manifest_is_complete` **đỏ sẵn**
(2 lỗi của Khánh), `test_gate_accept_lift_khong_parse_chuoi` **xanh** ⇒ lỗi mới là hiện vật của
tôi, không phải của code.

⇒ Chạy lại toàn bộ trên cây ĐÃ ỔN ĐỊNH. **Quy tắc mới cho chính tôi:** không sửa file trong lúc
một suite nền đang chạy — kết quả của nó không dùng được, và tệ hơn là nó **tạo ra một lỗi trông
như thật**.

### ✅ Suite CUỐI CÙNG (cây ổn định, chạy CẢ HAI đường)

| suite | kết quả | so baseline |
| --- | --- | --- |
| `uv run pytest -q` (`tests/`) | **1189 passed · 2 failed · 4 skipped** (25:01) | baseline **2 failed** — **đúng hai lỗi của Khánh**, 0 lỗi mới |
| `uv run pytest -q ui/backend/tests` | **205 passed** | không đổi |

Hai lỗi đỏ là `test_demo_trace_neutrality::test_real_demo_order_boundaries_capture_post_mutation_state`
và `test_health_boundary::test_money_manifest_is_complete` — **đã xác nhận đỏ sẵn trên baseline**
bằng `git stash`, và tôi **không đụng vào**.

---

## 4. ⚠ CỔNG CYCLE 4 CỦA TÔI CÓ MỘT **NHÁNH CHẾT** — tìm ra vài giờ sau khi ship

Vòng audit `L4` (chạy lại riêng agent đã chết ở vòng trước) bắt được: nhánh *"rail CHƯA TỪNG
BẮN"* tôi thêm sáng nay đòi `calls_a > 0 **AND** calls_b > 0`. **Điều kiện đó không bao giờ đúng
cho họ `xveto_`**:

`check_shift_extend` trả `channel_off` **ngay** (`advice_bridge.py:1119-1120`) khi kênh tắt, mà
`channel_off` ∉ `EXTEND_RAILS` ⇒ `world.py:905` không log ⇒ **arm A (đối chứng) LUÔN có
`xveto_calls_n = 0`**. Agent đo: `flags = []` trên 2 seed.

> **Cổng sinh ra để bắt "cơ chế khai mà không có đường chạy" lại tự đẻ ra một nhánh y hệt — và
> chết đúng cho họ khoá mà nó vừa được mở rộng tới.**

**Tôi tự kiểm** bằng cách đọc `advice_bridge.py:1119-1120` và `world.py:905`, không relay agent.
**Đã sửa:** điều kiện neo vào **arm B** (nơi cổng thực sự chạy); arm A chỉ tham gia khi nó cũng
chạy (nếu nó chạy mà rail CÓ bắn thì đó là ca SỤP VỀ 0, nhánh (i) đã xử).
**Đã ghim:** `test_nhanh_chua_tung_ban_phai_SONG_cho_ho_xveto_arm_A_luon_0_calls`, và chứng minh
nó **ĐỎ với điều kiện cũ / XANH với điều kiện mới** bằng phép chạy, không bằng lập luận.

### Ba phát hiện `L4` khác — **chưa tôi tự kiểm**, ghi để không mất
| | chỗ | agent đo |
| --- | --- | --- |
| **M1** | sổ lan can nghỉ không mang thông tin về kênh | arm `enabled=False` **vẫn** sinh **125/107/118** `advice_rest_veto`; bật kênh cũng ra **đúng 125** (seed 5000) ⇒ nếu đứng thì nhánh *"sụp về 0"* của tầng 5 **chưa từng đo được cái nó tưởng** |
| **M3** ⚠ **SẢN PHẨM** | `advice_checkpoint.py:357-365` ghi checkpoint **trước** khi biết cú nén là tạm thời; `_ALLOWED_TRANSITIONS["suppressed"]` **rỗng** | cooldown 20′ lúc 09:10 **giết vĩnh viễn** lời khuyên còn hạn tới 20:00; lý do báo ra là `"duplicate"` (sai nghĩa) |
| **M5** ⚠ **SẢN PHẨM** | `routers/advice.py:197` — `_note_shown` có cổng `if not items`, `_note_suppressed` **không** | **660/660 = 100%** event `suppressed` ghi vào store canonical là **MA** |

⇒ Vào `DEFERRED` chờ tôi tự kiểm. **M1 là mục phải kiểm trước** vì nếu đúng, nó hạ giá trị của
chính Cycle 4 (cổng đúng, nhưng dữ liệu nuôi cổng bị ô nhiễm).
- **Chưa kiểm chứng:** Cycle 4 **không đổi số nào hôm nay** vì `shift_extend`/`rest_window` đang
  TẮT ⇒ 9 khoá đều 0; giá trị của nó là **điều kiện tiên quyết** cho mọi phép đo kênh ngủ, chưa
  phải một cải thiện đo được.

## Visual
`NOT_APPLICABLE` — 0 thay đổi hành vi sim (fingerprint bit-identical), 0 thay đổi UI. Cycle 1 và
Cycle 5 (đường sản phẩm, **có** đổi hành vi) sẽ cần visual gate.

## Adversarial self-review / flaws found

1. **Hai thiết kế của tôi bị chính phép đo bác trong cùng session** — ghim 0 call site (thực tế 5
   ca chính đáng) và harness nền-không-sạch. Cả hai đều được phát hiện **vì tôi chạy thử**, không
   vì tôi đọc lại. Nguyên tắc *"đề xuất cách sửa phải qua phản biện như đề xuất phát hiện"* nay
   đúng **lần thứ 6**.
2. **Bản đồ ghi "3 ô 0 caller", tôi đếm ra 5.** Tôi sửa theo phép đếm của mình và ghi rõ — nhưng
   điều này nghĩa là **acceptance của bản đồ có một con số sai**, và ai đọc bản đồ mà không đếm
   lại sẽ chép sai vào báo cáo gửi mentor.
3. **Cycle 4 không cải thiện con số nào hôm nay.** Tôi cố ý làm nó sớm vì nó **chặn** Cycle 10.
   Rủi ro thành thật: nếu Cường ưu tiên kết quả nhìn thấy được, đây là cycle "không thấy gì".
4. **`E1` sửa một báo cáo gửi ra ngoài.** Tôi đã tự đếm bằng lệnh thay vì tin bản đồ — đúng loại
   claim phải verify kỹ nhất, vì sai ở đây là sai với người ngoài team.
5. **Chưa làm:** `A5`/`A7` (Cycle 5), `A2`/`A3`/`A4` (Cycle 1) — cả hai **đổi hành vi sản phẩm**
   nên cần đo trước/sau và visual gate, không gộp vào update này.
6. **Tôi tự làm hỏng một lần chạy suite 27 phút** bằng cách sửa file trong lúc nó chạy nền, và
   suýt báo một lỗi không có thật. Bắt được vì **stash rồi so với baseline** thay vì tin con số
   đầu tiên — cùng kỷ luật *"mở nguồn gốc ra đọc trước khi nói nó sai"*, nay đúng **lần thứ 7**.
7. **Hai lỗi đỏ sẵn của Khánh vẫn đỏ** và tôi **không đụng vào** (`test_demo_trace_neutrality`,
   `test_health_boundary::test_money_manifest_is_complete`) — đúng ranh giới claim.

## ⏳ Nhắc PENDING-REVIEW

**Tôi đã dùng quyền Cường uỷ:** `Q-D` **PHỦ QUYẾT** (không tính chờ/đổi pin là nghỉ — nó làm yếu
lan can một chiều) · `Q-B` **S8 ngoài scope / S5 KHÔNG THỂ KIỂM / S6 hoãn tới sau cost model** ·
`Q-A` **CÓ đo lại `shift_plan`, nhưng sau khi xử lý `S2-3`** (cap BIND 88,6% ⇒ đo bây giờ là lặp
lại đúng sai lầm đang sửa) · `Q-07` **giữ k=6 tới hết Cycle 9**, mặc định sau đó là **k=8**.
Lập luận đầy đủ ở `PHAN-QUYET-2026-08-07-bon-quyet-dinh-uy-quyen.md` — Cường lật được bất kỳ mục
nào bằng cách bác đúng tiền đề tôi dùng.

**Vẫn chờ Cường:** **V-32** (blocking) · V-31 · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/09/10/13 · amendment ĐA-08 — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`.
⏸ Khánh: 2 test đỏ + Flutter.
