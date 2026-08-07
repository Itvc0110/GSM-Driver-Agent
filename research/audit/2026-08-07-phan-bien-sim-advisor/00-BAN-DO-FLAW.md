# BẢN ĐỒ FLAW — 6 góc phản biện + 1 phản biện viên độc lập (2026-08-07)

**Nguồn:** `pb1-ket-qua-C9.json` · `pb2-thiet-ke-S4.json` · `pb3-thieu-metric.json` · `pb4-thieu-tinh-nang.json` ·
`pb5-advisor-san-pham.json` · `pb6-phan-phoi-ket-qua.json` · **`pb-refute.json`** (phản biện viên độc lập, bác 13/76).
Số liệu thô: `pb1-do-lai.json`, `pb1b-raw.json.gz`, `pb2-DO-raw.json`, `pb3-do-metric-thieu.json`.

**Người viết bản này là NGƯỜI TỔNG HỢP, không phải người đo.** Mọi con số dưới đây đọc từ artifact được cite.
Tôi đã tự verify lại **26 neo code bằng nội dung** (tên hàm/literal) — kết quả ở §7.

---

## 0. PHÁN QUYẾT TRUNG TÂM — đọc trước khi đọc bất kỳ bảng nào

Phản biện viên độc lập dựng **arm NULL** (advice **tắt hoàn toàn**, chỉ đổi khoá RNG của `_actor_demand_hint`
thêm `+7919` để rút lại nhiễu niềm tin của chính tài xế — **không advisor, không allocation, không adherence coin**)
và đo lại đúng công thức tercile trên **cùng 30 seed CRN**:

| đại lượng (30 seed, ghép cặp cùng actor) | arm B (kênh THẬT) | **arm N (KHÔNG advisor)** |
|---|---|---|
| payout rảnh-ÍT (t0) | −15.290,40đ **SIG** | **−20.756,86đ SIG** |
| payout giữa (t1) | −1.158,32đ ns | **−6.887,23đ SIG** |
| payout rảnh-NHIỀU (t2) | +26.106,39đ **SIG** | **+25.337,78đ SIG** |
| **payout TOÀN ĐỘI** | **+3.219,23đ SIG** | **−768,77đ ns** |
| Δ cuốc theo tercile | −0,586 / −0,233 / +1,394 | −0,846 / −0,478 / +1,358 |
| R²(tercile) trên 2.700 quan sát | 0,0463 | **0,0526** |
| MAD \|Δpayout\|/tài xế (liều xáo trộn) | 57.379đ | **59.983đ** |

**Đọc thẳng:** một thế giới **không có can thiệp nào** tái tạo TOÀN BỘ cấu trúc nhóm với biên độ **bằng hoặc lớn hơn**,
trong khi giá trị ròng nó tạo ra là **−769đ ns**. ⇒ **Biên độ nhóm bị TÁCH RỜI khỏi giá trị tạo ra.**

### Ba hệ quả bắt buộc

1. 🔴 **RÚT** mọi con số chia theo tercile khỏi mọi báo cáo: `−15.290đ`, `+26.106đ`, `+23.566đ`, `−14.602đ`,
   tỷ lệ chuyển giao `58,4%`, `churn 17,82×`, `harmed_share 42,30%`, `delta_p10 −89.264đ`.
   Câu **"lấy của người bận −15.290đ"** là **HIỆN VẬT**, không phải phát hiện.
2. 🟢 **CÁI ĐƯỢC PHÉP CÔNG BỐ hôm nay về kênh positioning** — đúng ba con số, không hơn:
   - **+17,27 chuyến hoàn thành/ngày/đội** CI[+13,03; +21,60] SIG và **−16,27 đơn HẾT HẠN** CI[−20,93; −11,83] SIG (S4-D5);
   - **kèm chi phí 93,69 km chạy rỗng/ngày/đội** CI[+86,36; +101,37] (S4-D7);
   - **kèm trần null của c9d**: thông tin của solver đóng góp **tối đa +414đ = 12,9%** của +3.219đ
     (**28,3%** nếu hiệu chỉnh Bonferroni k=4) — PB6-05/06.
3. 📌 **`D-C9-PHAN-PHOI` đóng được.** Mục đó trong `tracking/DEFERRED.md:140` đã tự ghi *"chưa loại được **can thiệp
   như một BỘ XÁO TRỘN**… biên độ tercile CHƯA được phép trích"* và tự đề nghị đúng phép thử này.
   pb1 **không cite** mục đó ⇒ đây là **ĐÓNG một mục đã có trong hàng đợi**, không phải phát hiện mới.

> ⚠ **Cái KHÔNG được nói:** phản biện viên **không chứng minh hiệu ứng nhóm bằng 0**. Ông ta chứng minh nó
> **KHÔNG ĐO ĐƯỢC và KHÔNG QUY ĐƯỢC cho kênh**. Phép thử duy nhất còn lại (chưa ai chạy) ở §6.

---

## 1. BẢNG FINDING ĐỨNG VỮNG — **58 mục**

Đã trừ 13 mục bị refuter bác (§5b) và trừ trùng lặp (PB1-03/04/11 gộp một dòng; PB6-01/02/10/18 bị bác vì trùng pb1).

**Ký hiệu:** 🅿 = chạm **ĐƯỜNG SẢN PHẨM** (tài xế thật đọc) · 🚢 = chạm **KÊNH ĐANG SHIP** (positioning/S4 và độ tin của số nó).
**Phân bố: 🅿 22 · 🚢 30 · chuẩn đo (cổng ĐA-08) 6.**

### 1A. ĐƯỜNG SẢN PHẨM — thẻ tài xế thật đọc (🅿, 11 mục)

*Phản biện viên tái lập **từng con số** của cả 11 mục này bằng một lượt chạy độc lập (7 ngày `dates[7::12]` × 110 tài xế
bike × 3 mốc = **2.310 lượt**). **Góc pb5 không có finding nào bị bác.***

| Mã | Neo (file + nội dung) | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| 🅿 **PB5-01** | `advisor.py` `_cliff_item` (≈:367) trả `"numbers": []` **vs** `_verify_item` gọi `V.check_bare_numbers` (≈:410) — cùng file; tầng hai: `cards.js` `const it = a.items[0]` (:291,:314,:342) | **Cảnh báo phòng ngừa "tỷ lệ nhận sát ngưỡng" bị CHÍNH verifier của file đó giết 100%.** Note của solver luôn chứa 2 số thập phân ⇒ V1 luôn bắn ⇒ luôn bị loại. **160/246 lần bị vứt là lúc thẻ chính đang giục tài xế chạy thêm để lấy thưởng** — advisor BIẾT mà không nói vài cú từ chối nữa là mất trắng | **246/2.310 (10,65%) sinh · 0/246 sống sau `advice()` · 0/246 được vẽ.** Lỗi V1 nguyên văn: `0.85` 288 lần, `0.87` 99, `0.86` 66, `0.88` 39. Item/payload: TRƯỚC verifier {1:2.063, 2:246, 0:1} → SAU {1:2.309, 0:1} | **CAO** | ĐO ×2 |
| 🅿 **PB5-02** | `advisor.py:281` `("thuong_moc_ke", sol["tier_vnd"], "vnd", "MOCK")` · `policy.py:104` `def bonus_at` và `gsm_sim/policy.py:94` `def day_bonus` — **cả hai GÁN `bonus = tier_vnd`, không cộng dồn** | **Số tiền trên mặt thẻ là TỔNG MỐC, không phải PHẦN KIẾM THÊM.** Thưởng ngày là bậc thang **thay thế** ⇒ phần đổi được bằng công sức = `tier_vnd − bonus_at(points_now)`. Không tầng nào tính. Thẻ đặt số tiền TỔNG cạnh "khoảng X giờ nữa, Y cuốc" ⇒ sai theo chiều **khuyến khích chạy thêm** | 1.129 thẻ `feasible_gap`; **111 (9,83%) sai**: **105 thẻ hiện 60.000đ khi biên là 30.000đ** (2,00×), **6 thẻ hiện 115.000đ khi biên là 55.000đ** (2,09×). Tổng thổi 3.510.000đ | **CAO** | ĐO ×2 |
| 🅿 **PB5-03** | `advice_checkpoint.py:189` `advisor.build_gi(...)` → `bonus_feasibility.solve` **vs** cổng DUY NHẤT `advisor.py:227` `if not driver_id.startswith(("d-","r-"))` → `no_active_channel` | **Đường v2 nhập từ `build_gi` xuống nên ĐI VÒNG cổng đội xe.** Chuỗi `startswith(("d-","r-"))` xuất hiện **đúng 1 lần** trong mã sản phẩm. Ngày `ADVICE_V2_ENABLED` bật, 40/150 tài xế car/premium nhận thẻ tiền tính bằng **policy BIKE** | **120/120 lượt** (40 tài xế × 3 ngày) sinh `tier_vnd ≠ 0`. VD `ce-0`: v2 → `{feasible:true, tier_vnd:60000, hours_needed:2.86}`; v1 → `{is_silent:true, no_active_channel}`. **Bán kính hôm nay = 0** (`advice_v2.py:39` `ADVICE_V2_ENABLED` mặc định `"0"`) — nhưng Flutter của Khánh **chỉ gọi v2**, không có v1 để rơi về | **CAO (tiềm ẩn)** | ĐO ×2 |
| 🅿 **PB5-04** | `advisor.py:177` `"historical_rate_method": rate_method` — docstring `_hist_rate` khai *"trả kèm `method` để card/nhật ký nói được đây là **xấp xỉ**"* | **100% thẻ dựng trên mẫu số XẤP XỈ, và cái nhãn sinh ra để nói điều đó có ĐÚNG 0 consumer hiển thị.** Grep 8–9 hit: producer/upcaster/schema/test — **0 hit ở `ui/web`, 0 ở `ui/driver_app`**. Câu "khoảng 7,7 giờ nữa" đứng trên mẫu số suy từ hình dạng span, tài xế không có cách nào biết | **2.310/2.310 (100%)** là `estimated_span_scaled`, 0 lượt `measured_intervals`. 1.482 thẻ mang số giờ, chỉ 93 (6,3%) có chữ "ước lượng" — **và caveat đó nói chuyện KHÁC** ⇒ **1.389/1.482 = 93,7%** trưng số giờ không một chữ về mẫu số | **CAO** | ĐO + grep |
| 🅿 **PB5-05** | `advisor.py:289` `"source": "SOLVER"` **hardcode**, ngay dưới dòng `gio_can_them` đi qua `_num_source` (:199) | Hai số sinh từ **MỘT** lần `_walk` trên **CÙNG** một `rate` bị dán hai lớp xuất xứ mâu thuẫn. Khi rate là `dp:policy_theoretical` (**tân binh / đầu ca** — đúng lúc câu hỏi quan trọng nhất), số cuốc là ước lượng lý thuyết nhưng cột nguồn in cho tài xế chữ **"SOLVER"**. Contract có sẵn enum `ASSUMPTION` ⇒ không phải hạn chế schema | **1.482/1.482 (100%)** `cuoc_can_them` = "SOLVER"; cùng lúc `gio_can_them` = MOCK 1.389 / ASSUMPTION 93 | TB | ĐO |
| 🅿 **PB5-06** | `cards.js:314` `shortMsg` thay `it.message` bằng cặp `tên: số` · `cards.js:210` `node("div","adv-why **hidden**")` | **Bề mặt `nudge` — bề mặt DUY NHẤT bắn giữa ca — vứt câu bất định của backend.** Backend làm ĐÚNG (2.309/2.309 thẻ có caveat), client thay bằng "diem con thieu: 10 điểm" ⇒ thẻ còn tiêu đề khẳng định + một con số trần; vế bất định lùi sau nút "Vì sao" | **552/770 nudge (71,7%)** không có token bất định nào trên mặt. Đối chiếu: brief 0/770, recap 0/769 | TB | ĐO (tái lập logic bằng Python, **không** chạy trình duyệt) |
| 🅿 **PB5-07** | `ui/contracts/advice.json` khối `numbers.items.properties` chỉ có `name/value/unit/source` — **0 trường `money_kind`** · `cards.js:339-341` ghép `payout_vnd` với "mốc thưởng" trong **một câu** | CLAUDE §5 đòi tách gross/payout/net. Đây là khuyết tật **CẤU TRÚC**: contract không có chỗ khai loại tiền ⇒ không cổng nào kiểm được. Câu recap do **CLIENT** ghép ⇒ **không đi qua `_verify_item`** | 2.309/2.309 (100%) thẻ mang tiền; **1.540/2.309 (66,7%)** mặt thẻ không có token phân loại nào | TB | ĐO (chấm bằng từ khoá) |
| 🅿 **PB5-08** | `advisor.py:26` `DEFAULT_SHIFT_END_MIN = 22*60` với comment tự dán nhãn *"ASSUMPTION — UI cho sửa qua query param"* · `api.js:42-45` **không gửi** `shift_end_min` | Giả định độ dài ca đi thẳng vào câu **khẳng định không điều kiện** "Quỹ giờ còn lại của ca không đủ". Client web (đường advice **sống duy nhất** hôm nay) không gửi tham số sửa lần nào ⇒ mọi tài xế bị áp ca 06:00–22:00 cứng. Không caveat nào nhắc | **827/2.310 (35,80%)** trả thẻ `insufficient_budget_hours` — mã phổ biến thứ hai | TB | ĐO |
| 🅿 **PB5-09** | `advice.py:360` `"event_id": f"ui-shown-{driver_id}-{date}-{topic}-{bucket}"` — **không chứa `advice_id`**, trong khi docstring cùng hàm khai là có | Payload ≥2 item ⇒ item thứ hai bị `INSERT OR IGNORE` nuốt ⇒ vắng khỏi ngân sách ca **và** mẫu số adherence dù đã hiện lên màn hình | **Phơi nhiễm hôm nay = 0** (đo: item sau verifier = {1:2.309}). **NHƯNG bật ngay khi PB5-01 được sửa**: 246/2.310 (10,65%) sẽ đánh rơi event `displayed` | THẤP hôm nay · **TB nếu sửa PB5-01 trước** | ĐO |
| 🅿 **PB5-10** | `advisor.py:264-277` nhánh at-risk có comment *"KHÔNG kèm số tiền: mức thưởng đó chính là thứ đang có nguy cơ KHÔNG được trả"* **vs** :279-282 nhánh cùng nghĩa lại mang `thuong_moc_ke` | Một lan can **đạo đức** chỉ phủ một nửa các nhánh mà nó dùng lý lẽ để phủ. Hai nhánh nói CÙNG sự thật ("tỷ lệ dưới ngưỡng, thưởng sẽ không được trả") nhưng nhánh chưa-đạt-mốc vẫn in số tiền vào bảng "Vì sao" | **353/2.310 (15,28%)** thẻ `acceptance_below_threshold`, **tất cả** mang `thuong_moc_ke` | TB | ĐO |
| 🅿 **PB5-11** | `advisor.py:358` docstring `_policy_thresholds` khai *"**Đi kèm MỌI payload advice**"* — sai ở nhánh `no_active_channel` (:227) và nhánh nhịp chặn của router | Lời khai quản trị không đúng + trường có **0 consumer toàn repo** (0 hit ở `ui/web`, `ui/driver_app`, **không có trong `advice.json`**) ⇒ mục tiêu "UI thôi hardcode" chưa đạt ở đâu cả | Đo trực tiếp `advisor.advice('ce-0',...)` → keys **không có** `policy_thresholds` | THẤP | ĐO + grep |

### 1B. ĐƯỜNG SẢN PHẨM — tính năng/đường dây (🅿, 11 mục)

*Mẫu số đã kiểm đúng bài học M1/M5: **110 tài xế bike in-scope**, không phải 150 — `advisor.py:227` chặn 40 tài xế
`ce-*`/`cp-*` ngay ở cửa. Mọi tỷ lệ chia cho 110 (hoặc 1.100 tài-xế-ngày, hoặc 3.300 lượt). **Góc pb4 không có finding nào bị bác.***

| Mã | Neo (file + nội dung) | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| 🅿 **TN-01** | `main.py:41-46` — 6 `app.include_router(...)`: **không có** router policy/FAQ, goal, recap | **12/14 user story không có đường chạy nào tới tài xế**; 1/14 đủ (US-F1-04); 1/14 cố ý hoãn (US-F2-04). **Cả khối F0 và cả khối F3 của SCOPE §3 có 0 đầu ra sản phẩm** | grep trên `{src,ui,scripts,configs,schemas}`: `goal` = **1 hit** (docstring test), `voucher` = **0**, `rental` = **0**, `policy_diff` = **0** | **CAO** | ĐO (grep+AST); phần "US nào coi là có đường" là **PHÁN ĐOÁN** |
| 🅿 **TN-02** | `advisor.py:235` `bonus_feasibility.solve(gi, policy())` là lời gọi solver **DUY NHẤT** · `cards.js` `KIND_HOURS = {brief:9*60, nudge:14*60, recap:21*60+30}` | **Advisor sản phẩm nói được ĐÚNG 3 dạng câu, 100% từ MỘT solver (S1).** Ba mặt thẻ dùng cùng một hàm, chỉ khác `now_min` ⇒ **"Tổng kết ca" (F3) thực chất là thẻ mốc-thưởng in lúc 21:30**. Contract khai `kind` enum 5 giá trị, **3 giá trị có 0 producer** | 3.300 lượt: nói 3.296 (99,9%). `feasible_gap` 1.687 (51,1%) · `insufficient_budget_hours` 1.181 (35,8%) · `acceptance_below_threshold` 428 (13,0%) · **cliff 0/3.300** | **CAO** | ĐO |
| 🅿 **TN-03** | `advice_v2.py:39` `os.getenv("ADVICE_V2_ENABLED","0")=="1"` · `advice_checkpoint.py:176` `runtime_state_provider or UnavailableRuntimeStateProvider()` | Kênh v2 (S2 `shift_dp`) chết ở **HAI cửa độc lập**. Kể cả bật cờ vẫn `missing_state` — **không chỗ nào trong `ui/backend/app/` truyền provider**. Mọi lời khuyên **THỜI ĐIỂM** (nghỉ/đổi pin/kết ca) không có đường tới tài xế dù dây đã nối xong | Chạy thật `d-0`: `solver_set=['S1']`, `reasons={'S2':'missing_state'}` | **CAO** | ĐO |
| 🅿 **TN-04** | `f3_patterns.py` — **0 lời gọi `.solve(` ngoài test** · `from_l1r.py` docstring *"payout_breakdown ĐỌC THẲNG: gross=total_fee, driver_payout=commission"* | **Tính năng thiếu ĐẮT NHẤT**: S3 chạy được trên 110/110 tài xế, đã tính sẵn gross+payout, nhưng 0 call site ⇒ khối F3 không phát ra một chữ nào. **Ba US F3 bị chặn không phải vì thiếu thuật toán mà vì thiếu ĐÚNG một lời gọi + một endpoint** | 1.100 tài-xế-ngày: S3 ok **100%** · có pattern **767/1.100 = 69,7%** · gross+payout **1.069/1.100 = 97,2%**. ⚠ **`inferred_activities` rỗng 1.100/1.100** ⇒ chỉ **2/4** loại pattern bắn được | **CAO** | ĐO |
| 🅿 **TN-05** | `from_l1r.py:324` `rewards.get("vnd", 0)` **vs** `mockdata.py:157` `json.loads(row["rewards"]) if isinstance(row["rewards"], str)` — **bản vá chỉ ở MỘT consumer** | **S6 `mission_knapsack` VỠ 100% ở ranh giới parquet.** `rewards` là dict trong bộ nhớ, **str sau khi ghi đĩa**. S6 chưa từng chạy một lần nào trên hình dạng dữ liệu mà sản phẩm sẽ đưa cho nó. Suite xanh vì mọi test lấy bảng **in-memory**, không test nào đọc lại file đã ghi ⇒ **fixture suy biến** | in-memory dict 6/6 · parquet **str 6/6** · loader sản phẩm **str 6/6** · **crash 1.100/1.100 = 100%** (`AttributeError: 'str' object has no attribute 'get'`). Dữ liệu dày: 6 mission, 261 dòng progress phủ **110/110** | **CAO** | ĐO (refuter **reproduce lại 100%**) |
| 🅿 **TN-06** | grep case-insensitive `src/gsm_sim/**`: `penal` = **0**, `fraud` = **0**, `khoan` = **0**, `voucher` = **0**; đối chứng dương `mission` = **27** | **S8/S9 KHÔNG THỂ KIỂM bằng ĐA-08 với twin-world hiện có** — world không mô hình hoá phạt lẫn cờ gian lận. Đưa chúng vào hàng đợi "đo hiệu quả" là **hứa một phép đo không tồn tại** | S8: notable 482/1.100 (43,8%) nhưng chỉ 19/1.100 (1,7%) có tiền thật bị trừ. S9: cờ mở 127/1.100 (11,5%); ⚠ **138/138 dòng `public_frauds` là `open`, 0 dòng `cleared`** ⇒ nhánh guardrail "cờ đã cleared → im lặng" **chưa từng có phơi nhiễm nào** | **CAO** | ĐO |
| 🅿 **TN-07** | `weekly_khoan.py` docstring *"**KHÔNG bịa số policy**… quota=None ⇒ `quota_available=False`"* | S5 **KHÔNG phải scaffold nên bỏ** — nó đang từ chối bịa số **đúng như §5 yêu cầu**. Thứ chặn là số khoán của GSM chưa có ⇒ xếp **BỊ CHẶN BỞI DỮ LIỆU NGOÀI**, không phải nợ kỹ thuật. Điều kiện mở lại là **một con số từ GSM**, không phải một commit | `policy().weekly_quota = None` (đo trực tiếp) | TB | ĐO |
| 🅿 **TN-08** | `SCOPE.md:23-24` tự khai *"Router/KB C6 free-text hiện là **legacy** và phải được deprecate khi chạm tới"* · lối vào duy nhất `smoke_advisor_live.py:18` | Cái **thực sự** là scaffold không phải solver nào cả mà là cụm C6: **8 module khép kín 1.184 dòng**, lối ra khỏi cụm chỉ là một script. ⚠ **Cái ĐẮT không phải dòng chết**: 11 file test giữ nó xanh nên mỗi vòng audit lại có người đọc `router.py` (khai đủ S1..S9 trong `_ROUTES`) rồi tin 9 solver đang chạy — **`router.py` là nguồn của ảo giác "có 9 kênh"** | AST: pipeline 1 importer (script) · router/templates/policy_kb/episode_store **1 importer = pipeline** · LOC cụm = 1.184. ⚠ `verifier.py` **THUỘC** đường sản phẩm ⇒ GIỮ | TB | ĐO (AST); câu "nên bỏ" là **ĐỀ XUẤT** |
| 🅿 **TN-09** | `advice.json` item có ĐÚNG 9 trường — **0 trường citation/doc_id/effective_date** · `policy.py` `effective_from: str \| None = None` | **Thẻ sản phẩm không mang trích dẫn chính sách và không có ngày hiệu lực.** "Version" duy nhất tài xế thấy là `policy_v:sim-policy-v0` — **một id CONFIG SIM đóng vai version chính sách**. CLAUDE §5 không thể thoả bằng sửa nội dung, **phải sửa contract**. Corpus policy có thật (7 record) nhưng chỉ `PolicyKB` đọc, mà `PolicyKB` chỉ được `pipeline.py` import (TN-08) ⇒ **corpus không có đường tới tài xế** | `version='sim-policy-v0'`, `effective_from/to = null`, `costs=null`, `track=null`. ⚠ **Ranh giới mock KHÔNG bị vi phạm**: `numbers[].source ∈ {MOCK,SOLVER}` + `is_mock:true` + `data_mode:'mock-realdata'` | **CAO** | ĐO |
| 🅿 **TN-10** | `SCOPE.md:9` *"…hoặc **estimated net income**"* · `from_l1r.py:232` literal `"estimated_net_vnd": None` — **hằng None** | Một trong hai mục tiêu tiền của SCOPE hiện **0% khả dụng**. Không phải lỗi (§5 cấm ước đoán chi phí ⇒ trả None là ĐÚNG) — nhưng nó ràng chặt với US-F0-02: **20 tài xế `r-*` (RTO) được advisor phục vụ mà không có một đồng chi phí thuê nào trong mô hình** | `estimated_net ≠ None`: **0/1.100 = 0,0%** · `policy().costs = null` · `policy().track = null` | TB | ĐO; câu "ai đọc payout RTO như tiền về túi là đọc sai" là **SUY** |
| 🅿🚢 **TN-11** | `demo_session.py:67` `advice["positioning_overrides"] = "off"` + `channels = {shift_plan:T, accept_lift:T, ...}` **vs** ship: 6 kênh false + `positioning_overrides: wait_only` | **Demo Track UI chạy bộ kênh NGƯỢC HẲN bản đang ship**: bật đúng hai kênh **ĐA-07 đã TẮT** (lý do ghi thẳng trong config: *"thu nhập ns, served −0,33đp SIG, đơn chết +4,1 SIG"*) và **tắt kênh duy nhất đang bật**. Thêm `adherence_by_archetype = 0.0` cho cả P1..P7 ⇒ demo cũng không biểu diễn được hiệu ứng lời khuyên lên hành vi | Đọc nguyên văn cả hai file | TB | ĐO cấu hình; hậu quả "người xem thấy advisor khác" là **SUY** (chưa chạy demo e2e) |

### 1C. THIẾT KẾ S4 — kênh đang ship (🚢, 6 mục)

| Mã | Neo (file + nội dung) | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| 🚢 **S4-D3** | `capacity_alloc.py:53` `rows, cols = linear_sum_assignment(cost)` · :50 `cost[i,j] = pen if tgt == c["target"] else pen + 10.0` | **`linear_sum_assignment` không mua được gì ở điểm vận hành này.** `pen ∈ [0;1]` bị áp đảo bởi hằng `+10` ⇒ hàm mục tiêu **tách được** thành "số lượt lệch target" (trội) + "tổng pen" (thứ) ⇒ bài toán **suy biến**. Ai bỏ công bảo vệ/tối ưu hoá/A-B tầng Hungarian này đang tối ưu một thứ **không có độ phân giải** | **Greedy first-fit đạt ĐÚNG giá trị cost tối ưu ở 472/472 lô (100,0%)**. Đối chứng độ phân giải: cách chọn NAIVE chỉ trùng 177/472 ⇒ ma trận cost **có** phân biệt được một số thứ, chỉ không phân biệt greedy với Hungarian | **CAO** | ĐO (472 lô, 30 seed). ⚠ Phép đo trên **phân bố input thực tế**, KHÔNG phải chứng minh toán học |
| 🚢 **S4-D5** | `pb2-DO-raw.json` khoá `b_he_thong` — đếm `dropoff` và `order_expired` trên toàn event log cả hai arm | **PHẦN SỐNG SÓT DUY NHẤT ở mức giá trị.** Kênh này **không phải trò chơi tổng-bằng-không**: nó biến đơn HẾT HẠN thành đơn được phục vụ. Refuter kiểm chéo bằng arm null: net trips arm N = **+0,011/người (~+1 chuyến toàn đội)** so với arm B **+0,192 (~+17 chuyến)** ⇒ **phần hệ thống này KHÔNG tái tạo được bằng nhiễu, nó là THẬT** | Δ chuyến hoàn thành **+17,27** CI[+13,03;+21,60] SIG · Δ đơn HẾT HẠN **−16,27** CI[−20,93;−11,83] SIG · Δ đơn nhận ở ô NHẬN người **+24,67** SIG · ở ô NGUỒN **+1,50 ns**. Liều: 35,83 lượt relocate/ngày vào 15,27 ô | THÔNG TIN | ĐO (30 seed) |
| 🚢 **S4-D6** | `pb2-DO-raw.json` khoá `b_phoi_nhiem` và `b_phoi_nhiem_SHUF` | **KẾT QUẢ ÂM TÍNH + cảnh báo phương pháp.** Giả thuyết "người bị đẩy vào ô đông chèn lấn người ĐÃ Ở ĐÓ" **không được phép đo này ủng hộ**: ô NHẬN phục vụ THÊM, ô NGUỒN không mất gì, và nhóm "có phơi nhiễm" lại LÃI NHIỀU HƠN. Nhưng đó là **QUAN SÁT chứ không phải NHÂN QUẢ** — arm MÙ SHUF cho đúng mẫu hình ⇒ "phơi nhiễm" chỉ đang đánh dấu người đứng ở ô có `capacity_left > 0` = **biến chọn mẫu** | Không phơi nhiễm +6.363đ SIG vs có phơi nhiễm +22.202đ SIG; **đối chứng MÙ SHUF: +8.409đ vs +20.231đ — cùng mẫu hình** | TB | ĐO; kết luận là **"KHÔNG ĐỦ BẰNG CHỨNG"**, không phải "đã bác" |
| 🚢 **S4-D7** | `capacity_alloc.py:44-50` **không có biến khoảng cách** · `features/allocation.py` candidate dùng ĐÚNG 4 trường `{driver_id, advice_kind, target, priority_soc}` · `pilot_dongda.yaml` `cash_cost_vnd_per_km: 0` | **S4 không mô hình hoá chi phí cơ hội của người bị đẩy đi — không số hạng km, không số hạng thời gian, không ở đâu.** Vế TIỀN hôm nay = 0 thật (đổi pin miễn phí tới 31/03/2029, và bản đồ lớp §4.9 nói vặn config này **INERT**). Vế **THỜI GIAN không bằng 0 và không ai bù** | **93,69 km chạy rỗng standby/ngày/đội** CI[+86,36;+101,37] · 2,596 km/lượt CI[+2,496;+2,687]. Nhóm MOVER (n≈30,3/seed): +13,751 phút rỗng SIG, Δpayout −2.326đ **ns**. **DERIVED: 24,0 phút rỗng/chuyến mới**; **DERIVED: 14.054đ/ngày** nếu quy 150đ/km | **CAO** | ĐỌC CODE + ĐO. ⚠ **Nhóm MOVER là điều kiện hoá HẬU-XỬ-LÝ** — chỉ con số ĐẾM SỰ KIỆN (93,69 km) là miễn nhiễm |
| 🚢 **S4-D9** | `capacity_alloc.py:50` `pen ∈ [0;1]` vs mismatch `+10.0` · `pilot_dongda.yaml` `swap_soc_threshold_pct: 20` | **HẠ severity của B8.** SOC là xếp hạng MỀM, không có sàn, không bao giờ thắng được số hạng mismatch — đúng về CẤU TRÚC. Nhưng bản đồ lớp ghi TB dựa trên *"có lượt gán cho tài xế SOC 8,7%"* = một phép đếm **CỰC TRỊ theo seed**. **Đây chính là kỷ luật mẫu số của M1/M5 được áp đúng** | Mẫu số đúng = **2.234 lượt gán**: 17 lượt gán cho SOC < 20% = **0,76%**. SOC thấp nhất từng được gán 10,3% | **THẤP** (hạ từ TB) | ĐO (2.234 lượt) |
| 🚢 **S4-D10** | `capacity_alloc.py:104-105` `max(1, int(round(v * (1 - pct))))` với `pct = 0.20` | **HẠ B5.** S4 trả khoá `sensitivity` + caveat "capacity là DANH ĐỊNH — ESTIMATED" ⇒ người đọc tin bất định của trần **ĐÃ được đo**. Thật ra: capacity 1 → 1 (không đổi), 2 → 2 (không đổi), chỉ 3 → 2 mới đổi. Kết hợp với `params` **không được đọc lần nào** trong thân `solve` (B9) ⇒ S4 trưng ra **HAI cửa phân tích độ nhạy mà cả hai không thể trả lời khác baseline** | 1.202 bản ghi zone_supply: capacity=1 chiếm **1.058 (88,0%)**, =2 chiếm 135 (11,2%), =3 chiếm 9 (0,75%) ⇒ **99,25% suất bất động dưới −20%** | TB | ĐO (1.202 bản ghi) + đọc code |

### 1D. ĐỘ TIN CỦA PHÉP ĐO — biên độ nhóm (🚢, 10 mục)

| Mã | Neo (file + nội dung) | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| 🚢 **PB1-01** | `pb1-do-lai.py` `class NoisyWorld` + `_cfg_with(cfg, enabled=False,...)`, khoá RNG `(self.seed + 7919, actor_id, hour, int(c,16))` | **Toàn bộ mẫu hình tercile tái lập ở arm KHÔNG CÓ ADVISOR** ⇒ biên độ ±26k **không phải bằng chứng phân phối lại**. 📌 Đây là **đóng `D-C9-PHAN-PHOI`** (mục đã có, pb1 không cite) chứ không phải phát hiện mới | Bảng §0. Liều: MAD arm N **59.983đ > B 57.379đ** ⇒ **không thể chê placebo yếu** | **CRITICAL** | ĐO (refuter tái lập **từng chữ số** từ `pb1b-raw.json.gz`) |
| 🚢 **PB1-02** | `c9c-...py:20` dòng luận *"Nếu arm NULL **bit-identical** với arm A ⇒ không có xáo trộn ⇒ mẫu hình của 9b là **THẬT**"* | **Quy tắc phán xử SAI LOGIC.** Arm null bit-identical ⇒ **không có lần rút khác nào** ⇒ phép thử có **LỰC BẰNG 0** với chính giả thuyết nó định loại (hồi quy về trung bình cần B ≠ A). `ty_le_hien_vat = 0/(−15290) = −0,0` là tỷ số mà **tử số không có support** — cùng họ lỗi mẫu-số/tử-số của M1/M5, đảo chiều. Nếu c9c được trích như "đã loại RTM" thì **mọi kết luận dựng trên nó sụp theo** | c9c json: `n_fingerprint_giong = 30`, `delta_t0=t1=t2 = 0.0` chẵn, **ci95 [0,0]** cả ba tercile (refuter tự mở json xác nhận) | **CRITICAL** | ĐO (đọc nguồn + đo arm N thay thế) |
| 🚢 **PB1-03/04/11** *(gộp 3)* | `pb1-do-lai.py` dict `TIEU_CHI` 8 lát cắt; `pb1b-...json` khối `co_che` | **Tercile KHÔNG phải lát cắt đúng.** Mọi biến **ĐO ĐƯỢC ở A** cho gradient còn LỚN HƠN và arm null tái lập hết; mọi thuộc tính **CỐ ĐỊNH** thì gradient **BIẾN MẤT**. Gradient tỷ lệ thuận với **mức NHIỄU của biến chia nhóm**, không tỷ lệ với "mức kênh nhắm vào nhóm đó". "Câu chuyện cơ chế" đi kèm biên độ tercile phải **RÚT** | `payout_A`: B +31.622/+16.277/−38.242 — **N +30.836/+10.757/−43.899, cả ba SIG**. `shift_len` (CỐ ĐỊNH): B +3.467/+5.357/+834 — **N toàn ns**. `shift_start`: **N toàn ns**. Cơ chế: Δidle t2 = −36,8′ ở B vs **−30,9′ ở arm KHÔNG advisor**. ⚠ Lát cắt **GIẢ theo `actor_id`** vẫn ra một nhóm −4.219đ với 20/30 seed âm | **HIGH** | ĐO |
| 🚢 **PB1-05** | `entities.py:73` `idle_min: float = 0.0  # chờ đơn tại chỗ` · `world.py` — `idle_min +=` xuất hiện **ĐÚNG MỘT LẦN** (nhánh WAIT) · `empty_min # pickup + relocate + deadhead` | **`idle_min` KHÔNG lẫn di-chuyển-rỗng/nghỉ/sạc — về định nghĩa nó SẠCH.** Nhưng **NHÃN DIỄN GIẢI SAI**: nó tương quan **+0,765 với độ dài ca**, chỉ +0,070 với số cuốc, và **+0,227 (DƯƠNG) với payout** ⇒ tercile "rảnh ÍT nhất" phần lớn là người **CA NGẮN, thu nhập nền THẤP NHẤT**, không phải "người đang bận/kiếm nhiều". **Diễn ngôn "lấy của người bận đưa cho người rảnh" sai ngay ở bước đặt tên biến**, độc lập với vấn đề RTM | corr: shift_len +0,765 · online +0,765 · empty +0,367 · rest +0,287 · payout **+0,227** · offered +0,076 · trips +0,070. Payout **NỀN** theo tercile (refuter đo lại 30 seed): **224.540 / 270.525 / 258.998** ⇒ t0 là nhóm nghèo nhất. Idle 74′/172′/253′ ứng ca TB 351′/503′/617′ | **HIGH** | ĐỌC CODE + ĐO |
| 🚢 **PB1-06** | `pb1-do-lai.json` khối `lieu_MAD_payout` | **Sàn nhiễu per-tài-xế cao hơn hiệu ứng đội ~18 lần** ⇒ **mọi phát biểu "ai được ai mất" đều dưới ngưỡng đo được**. Một cú xáo trộn **không mang thông tin nào** cũng dịch payout mỗi người trung bình 59.983đ. **Ràng buộc cứng cho MỌI báo cáo per-driver về sau**, không riêng c9 | MAD \|Δpayout\|/tài xế: B **57.379đ** · N **59.983đ**. Hiệu ứng toàn đội +3.219đ ⇒ tỷ số **≈ 17,8×** | **HIGH** | ĐO |
| 🚢 **PB1-07** | `c9b-...json` trường `ty_le_cham` (sinh từ event `standby_followed` ở arm B) | **Tiền đề LIỀU không tồn tại trong CHÍNH artifact c9b.** Không có quan hệ liều–đáp ứng: liều gần như phẳng và **KHÔNG đơn điệu** (nhóm GIỮA cao nhất) trong khi "đáp ứng" chạy đơn điệu. Một can thiệp thật phải để lại dấu ở liều. **Bằng chứng NỘI TẠI, không cần arm N** | `ty_le_cham` = **27,3% / 37,7% / 35,9%**; Δ tương ứng −15.290 / −1.158 / +26.106. Chênh liều t2−t0 = 8,6 điểm %; chênh Δ = 41.397đ. **Nhóm liều CAO NHẤT (t1) có Δ ns** | MEDIUM | ĐO |
| 🚢 **PB1-08** | `parallel.py:101` docstring `pick_target` chứa nguyên văn **`BUG-EVAL-ARGMAX`** | **Chính repo đã đặt tên cho lỗi này** và c9b là đúng lỗi đó ở dạng tercile. c9b tự bảo vệ bằng "chia theo biến TIỀN-can-thiệp ⇒ không post-treatment conditioning" — **đúng nhưng KHÔNG ĐỦ**: chọn theo thứ hạng của một biến NHIỄU đo ở A là mối đe doạ **thứ hai**, đã có tiền lệ trả giá **với biên độ y hệt**. Bài học cũ chỉ gắn vào `pick_target` nên tercile lách qua | Tiền lệ trong docstring: argmax-A **−19.654đ** · argmax-B **+27.416đ** · mean-P4 không chọn lọc **+3.610đ**. Hôm nay: **−15.290 / +26.106 / +3.219**. **Ba cặp số cùng cấu trúc** | MEDIUM | ĐO (đọc nguồn) + đối chiếu |
| 🚢 **PB1-09** | `pb1b-...json` khối `phan_tan` | Phân tán payout giữa tài xế KHÔNG đổi. ⚠ **TỰ PHẢN BIỆN của chính pb1**: hoán vị danh tính giữ nguyên phân phối biên nên sd/gini không đổi **KHÔNG loại được** "xáo trộn ai giàu ai nghèo" ⇒ xếp **bằng chứng PHỤ** | A: sd 96.776đ, gini 0,2195 · B: Δsd −313đ ns · N: Δsd +1.381đ ns | LOW | ĐO |
| 🚢 **PB1-10** | `pb1-do-lai.json` `toan_doi` vs `c9d-...json` `toan_doi` | **KHÔNG BÁC ĐƯỢC Δ toàn đội +3.219đ** — arm null có liều LỚN HƠN mà vẫn −769đ ns. **NHƯNG hai placebo cho hai câu trả lời khác nhau**: c9d SHUF tái lập gần hết (+4.590đ), arm N không tái lập gì. **Hoà giải (SUY, chưa kiểm)**: SHUF giữ nguyên **TẬP Ô ĐÍCH** và chỉ phá ghép cặp; arm N không có tập ô nào ⇒ giá trị mức đội, nếu có, nằm ở việc **CHỌN Ô**, không ở Hungarian | B **+3.219đ** CI[+1.657;+4.731] SIG, 6/30 seed âm · N **−769đ** ns, 16/30 seed âm · c9d SHUF +4.590đ, **THẬT = B−SHUF = −1.371đ** CI[−3.074;+414] ns | INFO | ĐO số; **cách hoà giải là SUY (DERIVED)** |
| 🚢 **PB6-12** | `c9b-...py:16-18` docstring *"Đây cũng đúng đối tượng mà kênh vị trí nhắm: **người rảnh nhiều**"* | **"Người rảnh nhiều" không phải một NGƯỜI, nó là một LẦN RÚT THĂM.** (1) Về khoa học: đây chính là cơ chế RTM mà c9c không loại được. (2) **Về sản phẩm: KHÔNG thể dùng `idle_min` để chỉ mặt trước ai sẽ bị thiệt** ⇒ mọi đề xuất kiểu "bù trừ cho nhóm bị thiệt" hoặc "chỉ bật kênh cho nhóm hưởng lợi" **KHÔNG THI HÀNH ĐƯỢC** | pb6 (10 seed): 15/90 giữ nguyên tercile, 30/90 trải cả ba. **Refuter đo lại ở n=30 — MẠNH HƠN: chỉ 13/90 actor luôn ở cùng một tercile, 63/90 trải hết cả ba** | **HIGH** | ĐO ×2 |

### 1E. KỶ LUẬT THỐNG KÊ — cái phải kèm khi trích (🚢, 14 mục)

| Mã | Neo | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| 🚢 **PB6-05** | `c9d-...json` `toan_doi.that.ci95` | ⭐ **ĐẶT TRẦN CHO CHÍNH KẾT LUẬN THUẬN LỢI.** Câu "thông tin của solver đóng góp KHÔNG ĐO ĐƯỢC" **đúng nhưng phải kèm trần**. Báo cáo "Hungarian bị bác" mà không kèm trần này là **over-claim về phạm vi** — đúng loại lỗi đã làm hỏng 2/5 finding hôm nay | **Cận trên CI95 của (B − SHUF)**: toàn đội **+414,49đ = 12,88%** của +3.219đ · t2 +4.372,72 = **16,75%** của +26.106 · t1 +4.167,65 = 359,8%. MDE(80%): 4.938 / 7.075 / 7.280 / **2.560đ** | MEDIUM | ĐO |
| 🚢 **PB6-06** | `c9d-...py:138,:147` — 4 khoảng tin cậy dùng chung α=0,05, không Bonferroni/Holm | **Ở c9d khoảng hẹp là CÓ LỢI cho kết luận của chính mình** (khẳng định một NULL) ⇒ đúng tinh thần *"claim THUẬN LỢI phải verify kỹ hơn"* trong MEMORY | Bonferroni k=4 (α=0,0125, z=2,4977): toàn đội [−3.654; **+912**] ⇒ trần null nới từ **12,9% → 28,3%**; t0 từ 4,2% → 10,5% | MEDIUM | ĐO + tính |
| 🚢 **PB6-04** | `c9b-...json` `tercile_1.sig = "ns"` | **"ns" ở tercile GIỮA là NULL RỖNG, không phải bằng chứng "phẳng".** `c9b:98` in *"Δ phẳng hoặc ĐẢO ⇒ giá trị là lan toả hệ thống"* — đó là **đọc "ns" thành "bằng 0"**, đúng bẫy CLAUDE §4b cảnh | sd 12.440đ, se 2.271đ, \|eff\|/se = 0,51 ⇒ **power = 0,080**, **MDE(80%) = 6.359đ**. (t0/t2 có power ≈ 1,000) | MEDIUM | ĐO + công thức chuẩn |
| 🚢 **PB6-08** | `c9b-...py:44` `SEEDS = list(range(3300, 3330))` | **Định hướng chi phí**: n=30 **THỪA** cho hiệu ứng tercile (power ≈ 1,000, đủ từ **n=15**) nhưng **THIẾU cho mọi kết luận NULL**. Ai đề xuất "chạy thêm 70 seed cho đủ 100" phải nói rõ đó là để **siết các NULL**, không phải xác nhận −15.290/+26.106 | delta_all: sd 4.439, se 810, power 0,978, n tối thiểu 80% = **15**. Ngoại suy n=100 (**DERIVED**): se toàn đội 914→501, MDE 2.560→**1.402đ**, trần Bonferroni +912→**+380đ = 11,8%** | MEDIUM | ĐO; ngoại suy n=100 là **DERIVED** |
| 🚢 **PB6-03** | `c9b-...json` `per_seed[0..29]` | **Kết quả ÂM TÍNH, củng cố c9b**: không bimodal, không phụ thuộc outlier. **Ghi lại để không ai đổ lỗi cho outlier nhằm né đối mặt** | t0 âm **29/30** seed, t2 dương **29/30**, delta_all dương 24/30. Bỏ 3 seed ủng hộ mạnh nhất (adversarial): delta_all +3.219→**+2.507 (vẫn dương)**. Khe hở lớn nhất 1,40 sd < ngưỡng nghi ngờ 1,5 sd | INFO | ĐO |
| 🚢 **PB6-07** | `c9b-...py:49-53` `def _boot(xs, rng)` với `rng.choices(xs, k=len(xs))` | **Một nghi ngờ BỊ BÁC — ghi lại để không ai phí công nghĩ lại.** Bootstrap **đúng cấu trúc**: đơn vị lấy mẫu là SEED (không phải actor — actor cùng thế giới cạnh tranh nhau), giá trị đã là hiệu ghép cặp cùng actor cùng seed | Chạy lại B=20.000: t0 [−17.902;−12.677] vs repo [−17.828;−12.591]. CI percentile **hẹp hơn t-CI 5–9%**; chỉ số percentile lệch **1 rank** | LOW | ĐO (bootstrap lại) |
| 🚢 **PB6-09** | `pilot_dongda.yaml:236` `n: 90` + `archetype_mix` P1..P7 · `advice_bridge.py:305` `if self.coverage == "all": hit = True` | **MẪU SỐ SẠCH** — refuter/pb6 đã tự kiểm đúng điều kiện làm hỏng M1/M5: đội sim là 90 tài xế hai bánh thuộc P1..P7, **tất cả** được advisor phủ khi `coverage='all'`. **Không được dùng lý do "mẫu số nhiễm" để bác c9b** | n=90 (khớp cả 30 dòng `per_seed`); 90 % 3 = 0 ⇒ tercile **30/30/30 chính xác** | INFO | ĐO (chạy sim + đếm), **không suy từ nhãn config** |
| 🚢 **PB6-11** | đo lại: xếp tercile theo `online_min` và theo `idle_min/online_min` | **Khoá một hướng sửa SAI.** KHÔNG được "giải thích" c9b bằng *"tại P1 chạy ca ngắn nên idle thấp"* — chia theo **độ dài ca** thì mẫu hình BIẾN MẤT (không đơn điệu, dấu ngược) | Theo `online_min`: **+4.162 SIG / +6.722 SIG / −1.594 ns** (dấu ngược). Theo `idle/online`: −23.175 SIG / −2.798 ns / +35.264 SIG (**biên độ lớn hơn c9b ~1,4×**) | INFO | ĐO (20 seed) |
| 🚢 **PB6-13** | `c9d-...py:81-85` `if len(allocs) > 1: ... self.n += 1` — **tử số không có mẫu số** | `c9d.json` lưu `n_hoan_vi: 10..17` và header in *"~14 lượt hoán vị/seed"* — người đọc dễ hiểu đó là **cường độ placebo**. Thực ra các lượt solve trả ≤1 allocation bị **bỏ qua hoàn toàn và không ghi ở đâu**. Nếu tỷ lệ bỏ qua cao thì SHUF ≈ B và kết luận "bản mù tái tạo toàn bộ" sẽ là **tầm thường đúng**. **Lỗ hổng TRUY VẾT** | Refuter/pb6 đo lại (5 seed): lượt solve bị bỏ 13/77 = 16,9% nhưng **allocation nằm trong đó chỉ 13/319 = 4,1%**; allocation **THỰC SỰ đổi đích 242/319 = 75,9%**. Theo seed: 66,0 / 66,2 / **83,6** / 78,5 / 81,3% — **tái tạo đúng ba số tác giả báo** | LOW | ĐO (instrument lại) |
| 🚢 **PB6-14** | `capacity_alloc.py:61-63` `"staggered": tgt != c["target"]` — **tính TRƯỚC khi `_Hoanvi` ghi đè `assigned_target`** | Dưới arm SHUF, event `standby_planner` ghi `herding_avoided` của **LỜI GIẢI THẬT** chứ không phải arm đang chạy ⇒ ai so herding/Gini/HHI giữa B và SHUF từ event log sẽ đọc ra "hai arm phân tán như nhau" **một cách giả tạo**. **KẾT LUẬN HIỆN TẠI KHÔNG BỊ ĐẢO** | Đọc code: vòng thi hành ở `world.py` chỉ dùng 3 khoá (`assigned_target`, `driver_id`, `safety_flags`) — **`staggered` và `assigned_bucket` không xuất hiện lần nào** ⇒ payout sạch | LOW | ĐỌC CODE |
| 🚢 **PB6-15** | `capacity_alloc.py:88` `allocations = swap_alloc + standby_alloc` vs `_Hoanvi` hoán vị trên **toàn bộ** `allocs` | **MÌN CHƯA NỔ**: `assigned_target` của swap là **station_id**, của standby là **tên ô**. Hoán vị trộn hai loại sẽ gán station_id làm ô đứng chờ. **Hôm nay sạch chỉ vì station rỗng.** Điều kiện mở lại: bật `station_choice` (đang false, **NO-GO theo UPDATE-160**) hoặc bất kỳ đường nào đưa swap_window vào cùng lời gọi | `world.py` truyền `[]` cho tham số station; mọi candidate là `advice_kind='standby_zone'` ⇒ `swap_alloc` rỗng | LOW | ĐỌC CODE + config |
| 🚢 **PB6-16** | `c9b-...py:69` `sorted(ids, key=lambda i: idle_a[i])` — `ids` đã sorted ⇒ **tie-break là `actor_id`, không khai báo** | Không đảo dấu, nhưng là **nguồn không-xác-định không được khai** và sẽ nặng lên nếu ai chia quintile/decile | **7/20 biên** có `idle_min` bằng nhau tại điểm cắt. Ước lượng tác động **≈ 690đ** ở trường hợp xấu nhất (nhỏ hơn nhiều so với se 1.359–2.250đ) | LOW | ĐO (đếm ties) + **DERIVED** (ước lượng tác động) |
| 🚢 **PB6-17** | `c9b-...py:70-71` `t = len(xep)//3` — dồn phần dư vào **tercile CAO NHẤT** (lặp y hệt ở c9c:84 và c9d:97) | Nếu n không chia hết cho 3, nhóm "rảnh NHIỀU nhất" nhận thêm 1–2 người — **đúng nhóm có biên độ lớn nhất**, sai số vào đúng chỗ đắt nhất. `pilot_dongda.yaml` đã đổi `actors.n` **ba lần (50 → 74 → 90)** và **74 không chia hết cho 3** ⇒ chạy lại trên config cũ/khác thì **lỗi kích hoạt im lặng**. Không có assert nào canh | n=90 hôm nay ⇒ 30/30/30, **không lệch**. Đối chiếu: 74 % 3 = 2 | LOW | ĐO + đọc config |
| 🚢 **PB6-19** | `c9b.json` `per_seed[0]` (seed 3300) và `per_seed[7]` (seed 3307) | **Hai seed đối cực rẻ nhất để đặt breakpoint nếu muốn truy CƠ CHẾ** (PB6-03 đã chứng minh chúng không lái kết luận) | seed **3300** là seed DUY NHẤT cả đội cùng thua (delta_all −9.386,43; khe 1,40 sd) và cũng là seed có SHUF âm nhất ở t0 (−25.191,87 vs B −13.520,07). seed **3307** là seed DUY NHẤT nhóm "rảnh ÍT" có lãi (+2.892,23) | INFO | ĐO |

### 1F. CHUẨN ĐO / cổng ĐA-08 (6 mục — chạm **cái cổng đã cấp phép cho kênh đang ship**)

| Mã | Neo | Hậu quả | Số ĐO ĐƯỢC | Sev | ĐO/SUY |
|---|---|---|---|---|---|
| **PB3-03** | `specs/advisor-objective-model-v2.md:242-244` *"đòi TỪNG archetype dương-SIG thì subgroup không bao giờ đủ power"* | **Lập luận biện minh cho tầng 1b CẮT HAI CHIỀU**: nếu subgroup không đủ lực chứng minh LỢI thì cũng không đủ lực **tố giác HẠI** — mà 1b được viết ở dạng **CHỈ tố giác hại**. ⇒ 1b có xác suất tố giác **tỉ lệ NGHỊCH với độ hiếm của nhóm**, tức bảo vệ kém nhất đúng những nhóm dễ tổn thương nhất | **P3 có điểm ước lượng ÂM LỚN NHẤT trong 7 archetype: −18.757,95đ** nhưng CI[−41.357,76; +4.009,23] trùm 0 ⇒ **1b PASS**. P3 chỉ có **5/90** tài xế | **CAO** | ĐO (số) + trích nguyên văn spec. ⚠ **Chỉ giữ đề xuất (i) báo kèm MDE** — đề xuất (ii) "thêm phân tầng tercile" **BỊ BÁC** (PB3-02) |
| **PB3-04** | `sim_metrics.py` `concentration_metrics` → `system_guardrail` → `parallel.py:208` `"supply_cell_hhi": g["supply_cell_hhi"]` | **BÁC mệnh đề "HHI cung theo ô chưa ai đo"** — nó ĐÃ CÓ, ĐANG được đọc, ĐANG GIẢM SIG; nhãn "metric MỚI cần viết" ở spec §5 là **NHÃN STALE**. ⭐ **Đây là kỷ luật 3 được thi hành đúng** (mở nguồn gốc trước khi nói repo thiếu). ⚠ **NHƯNG cùng phép đo cũng chứng minh HHI KHÔNG BAO GIỜ bắt được tái phân phối**: HHI là đại lượng theo **Ô**, tái phân phối là đại lượng theo **NGƯỜI** | Δ `supply_cell_hhi` **−0,0009** CI[−0,0013;−0,0005] **SIG GIẢM** (cung trải đều hơn) · `station_hhi` −0,0086 ns · `n_supply_cells` −0,17 ns | TB | ĐO + tự mở nguồn gốc |
| **PB3-05** | `scripts/cham_da08_station_choice.py` — 6 phép chấm, **0 dòng đọc `station_hhi` hoặc `supply_cell_hhi`** (tôi verify lại: grep 2 khoá này = **0 hit** trong file) | **Cổng chấm ĐA-08 TỰ ĐỘNG DUY NHẤT của repo BỎ HẲN tầng "Tập trung"** — một trong 5 dòng của bảng §5, mà spec ghi *"Kênh nào vi phạm bất kỳ dòng nào ⇒ không được bật"*. Tên "số 5" bị **tầng-5 sức khoẻ (sinh sau, không thuộc bảng §5)** chiếm chỗ. Dòng này đang được chấm **BẰNG TAY** | 6 phép chấm / 5 dòng bảng §5; **2 khoá CÓ SẴN trong `compare()["system"]` mà script bỏ qua** | TB | ĐO (đọc trọn script + đối chiếu spec) |
| **PB3-06** | `sim_metrics.py:217` `"payout_p10"`, :287 `"wait_p90_min"` **được sinh** vs `parallel.py:176` `_system_metrics` **chọn tay 9 khoá** | **TÍNH RỒI VỨT**: 13 khoá bị bỏ khỏi đường chuyển tiếp ⇒ không bao giờ vào `PairResult`/`compare()`/artifact. **Hai cái đau nhất**: (i) `wait_p90_min` — tiêu chí khách hàng của §5 chỉ được chấm trên **trung vị**, đuôi chờ không ai canh; (ii) `event_repeat_ratio` + `event_adherence_is_lower_bound` chính là **NHÃN mà L3-04 dựng để chặn người ta so event_adherence giữa các kênh** — một nhãn cảnh báo **0 người đọc là nhãn không tồn tại** | 13 khoá bị bỏ; **3 khoá 0 reader tuyệt đối** (kể cả test). ⚠ **PHẢN BIỆN CHÍNH ĐỀ XUẤT**: nối `payout_p10` vào **KHÔNG** chữa được tái phân phối — Δ đo được **+3.469,47đ ns** (p10/Gini là thước **HÌNH DẠNG**; tái phân phối đổi **AI đứng ở đâu**) | TB | ĐO (grep + đo Δ của chính các khoá bị vứt) |
| **PB3-10** | `parallel.py:56-70` `PairResult` · `:463` `diffs = [b - a for a, b in zip(va, vb)]` | **RÀO CẢN THI CÔNG**: mọi metric ghép cặp đều **đã là HIỆU** ⇒ nhét vào `system_b` sẽ **bị `compare()` TRỪ cho `system_a`** — một loại vô nghĩa im lặng đúng họ `net_mean_all` hai công thức (C2/Cycle 7). Phải **THÊM TRƯỜNG MỚI** vào `PairResult` ⇒ **đổi SHAPE của contract A/B**, không phải thêm test. Mọi consumer (`dashboard.py`, `measure_e10.py`, `measure_l104.py`, `cham_da08_*.py`) phải được rà. **KHÔNG được lén nhét vào `system_*`** | `PairResult` có 7 trường, **0 trường mang phân phối per-actor**; `_driver_metrics` trả 12 khoá cho **ĐÚNG 1 actor**; `_rows` áp `b − a` cho MỌI khoá không phân biệt | TB | ĐO (đọc code) |
| **PB3-11** | `sim_metrics.py:307` `out.update(health_guardrail(result))` **rồi** `parallel.py:219` gọi **LẠI** `health_guardrail(result, actor_ids=...)` | **BẪY NGỦ**: tầng-5 sức khoẻ chạy **hai lượt mỗi arm mỗi seed**, một bản (phạm vi TOÀN COHORT) bị vứt. Hôm nay **0 sai số**. **NHƯNG** ngày ai đó thêm một khoá tầng-5 vào danh sách chuyển tiếp từ `g` (việc rất tự nhiên — `g` đang nằm ngay đó và ĐANG chứa khoá đó), họ lấy bản **TOÀN COHORT** thay vì bản **BỊ CHẠM** — đúng cái mà `n_actors_scope` sinh ra để phân biệt — **và không cổng nào kêu vì cả hai đều là số hợp lệ** | 2 lời gọi cho cùng một `result`; 9/9 khoá lấy từ `g` hiện **ngoài** tầng 5 ⇒ độ lệch hôm nay = **0** | THẤP-TB | ĐO (đọc code). **Chưa reproduce bằng một ca sai thật** |

---

## 2. THIẾU METRIC — 5 đề xuất

### ⚠ NÓI THẲNG TRƯỚC: ĐA-08 **KHÔNG** bắt được kịch bản phân phối lại. Đó **LÀ** lỗ hổng của chuẩn.

Bảng §5 của `advisor-objective-model-v2.md` có 5 tầng: Cá nhân (1a trung bình + 1b per-archetype) · Hệ thống · Khách hàng ·
Công bằng (Gini) · Tập trung (HHI). **Không tầng nào là đại lượng theo NGƯỜI-GHÉP-CẶP.** Đo được:

- Gini Δ = **−0,0032 ns** · payout_p10 Δ = **+3.469 ns** · `supply_cell_hhi` Δ = **−0,0009 SIG GIẢM** ⇒ **cả ba tầng "công bằng/tập trung" đều PASS**, và **PASS đó không mang thông tin gì về việc ai đổi chỗ cho ai** — vì đó là thước **HÌNH DẠNG phân phối cắt ngang** (PB3-06), còn tái phân phối đổi **AI đứng ở đâu** (PB3-04).
- Tầng 1b thì **chỉ tố giác hại** và **xác suất tố giác tỉ lệ NGHỊCH với độ hiếm của nhóm** (PB3-03: P3 n=5/90, điểm ước lượng **−18.758đ** nhưng CI trùm 0 ⇒ PASS).

**Nhưng cách VÁ không phải là ba metric ghép cặp mà pb3 đề xuất.** Refuter đo cả ba trên arm không-advisor:

| metric pb3 đề xuất | arm B (thật) | **arm N (KHÔNG advisor)** | phán quyết |
|---|---|---|---|
| `harmed_share` (T=1.000đ) | 42,30% CI[40,78;43,81] | **46,00%** CI[44,74;47,37] | 🔴 ngưỡng ≥0,50 sẽ **TREO một thế giới không can thiệp** |
| `churn_ratio` (pooled) | 17,82× | **78,02×** | 🔴 tiến ra vô cùng khi net → 0 ⇒ **phạt càng mạnh khi can thiệp càng VÔ HẠI** |
| `delta_p10` | −89.264đ | **−98.467đ** | 🔴 ngưỡng −50.271đ bị **chính arm null vượt gần gấp đôi** |

⇒ **Ba metric đó đo ĐỘ NHẠY HỖN LOẠN của sim, không đo tác hại của kênh.** Chúng bị bác.

**Sự thật cứng phải nói với Cường:** ở sàn nhiễu hiện tại (**MAD 57.379–59.983đ/người/ngày** so với hiệu ứng toàn đội
**+3.219đ**, tỷ số **≈17,8×** — PB1-06), **sim này KHÔNG CÓ ĐỘ PHÂN GIẢI để đo tái phân phối theo người, dù thêm metric nào.**
Cái vá được hôm nay là **hiệu chuẩn phép đo** (M-1), không phải một metric per-person mới.

---

### M-1 — `null_arm_delta`: **cổng hiệu chuẩn placebo bắt buộc** 🥇

- **Định nghĩa.** Mọi tiêu chí của ĐA-08 phải được đo **hai lần**: trên arm THẬT và trên **arm NULL** (advice tắt hoàn toàn, chỉ đổi khoá RNG niềm tin của tài xế). Đại lượng quyết định là **hiệu (thật − null)**, không phải giá trị thô.
- **Cách tính từ dữ liệu sẵn có.** Code đã tồn tại và đã chạy: `pb1-do-lai.py` `class NoisyWorld` + `_cfg_with(cfg, enabled=False, ...)` + khoá `(self.seed + 7919, actor_id, hour, int(c,16))`. **Không cần dữ liệu mới, không cần đổi contract** (đây là arm thứ ba, không phải trường thứ tám của `PairResult` ⇒ **không đụng PB3-10**).
- **Ngưỡng.** Một tiêu chí chỉ được tính **PASS** nếu **CI95 của (thật − null) loại 0 theo đúng chiều mong muốn**. Nếu chỉ có giá trị thô vượt ngưỡng mà hiệu-với-null không SIG ⇒ **verdict là `KHÔNG QUY ĐƯỢC CHO KÊNH`**, không phải PASS và cũng không phải FAIL.
- **Số hôm nay khi áp ngưỡng này.** Toàn đội: B +3.219đ vs N −769đ ns ⇒ **PASS**. Mọi tercile: **FAIL** (null tái tạo bằng hoặc lớn hơn). `harmed_share`/`churn_ratio`/`delta_p10`: **FAIL** cả ba.
- **Vì sao đây là metric số 1:** nó chạm **ĐỘ TIN CỦA PHÉP ĐO**, và nó là thứ duy nhất trong danh sách đã có **bằng chứng nó bắt được lỗi thật** (nó vừa bắt 6 finding + 3 metric đề xuất).

### M-2 — `tang_tap_trung_auto`: chấm tự động tầng "Tập trung" của bảng §5

- **Định nghĩa.** `station_hhi` và `supply_cell_hhi` **không tăng có ý nghĩa** — đúng dòng thứ 5 của bảng §5 mà spec ghi *"vi phạm bất kỳ dòng nào ⇒ không được bật"*.
- **Cách tính.** **Hai khoá ĐÃ có sẵn** trong `compare()["system"]` (`parallel.py:208` chuyển tiếp cả hai). Việc duy nhất phải làm: thêm **2 dòng đọc** vào `scripts/cham_da08_station_choice.py` (hiện **0 hit** cho cả hai khoá — tôi verify lại). **Không đổi contract, không chạy sim mới.**
- **Ngưỡng.** FAIL nếu CI95 của Δ nằm **hoàn toàn dương**. Hôm nay: `supply_cell_hhi` −0,0009 CI[−0,0013;−0,0005] ⇒ **PASS (giảm SIG)**; `station_hhi` −0,0086 ns ⇒ PASS.
- ⚠ **Bắt buộc kèm nhãn**: *"HHI là đại lượng theo Ô. **Đừng dùng 'HHI giảm' làm bằng chứng công bằng giữa NGƯỜI**"* (PB3-04).

### M-3 — `wait_p90_min` + `payout_p10/median/p90`: nối lại 13 khoá bị vứt

- **Định nghĩa.** Tiêu chí "thời gian chờ khách không tăng" của bảng §5 phải được chấm trên **đuôi p90**, không chỉ trung vị.
- **Cách tính.** `sim_metrics.py` **đã sinh** cả bốn khoá (:217 `payout_p10`, :287 `wait_p90_min`); `parallel.py:176` `_system_metrics` **chọn tay 9 khoá và bỏ lại 13**. Sửa = thêm khoá vào danh sách chuyển tiếp. **Đây là scalar hệ thống ⇒ KHÔNG chạm rào cản PB3-10.**
- **Ngưỡng.** FAIL nếu Δ`wait_p90_min` dương SIG. Hôm nay **+0,0088 ns** (phải tính riêng vì compare không có khoá) ⇒ PASS.
- ⚠ **Không được bán `payout_p10` như metric công bằng** — Δ = +3.469 **ns**, và lý do là **cấu trúc**: nó là thước hình dạng (PB3-06).
- **Kèm theo, chi phí 0đ:** nối luôn `event_repeat_ratio` + `event_adherence_is_lower_bound` — **nhãn cảnh báo 0 người đọc là nhãn không tồn tại**.

### M-4 — `empty_min_per_new_trip` / `standby_empty_km_per_day`: **chi phí kênh, hiện KHÔNG nằm ở đâu**

- **Định nghĩa.** Phút và km chạy rỗng do lệnh relocate-standby sinh ra, chia cho số chuyến mới kênh tạo ra.
- **Cách tính.** Từ event log standby đã có: `empty_min` (`entities.py` — *"pickup + relocate + deadhead"*) và khoảng cách/lượt. **Đã đo xong ở S4-D7**, không cần code mới để có số đầu tiên.
- **Ngưỡng.** ⚠ **BÁO CÁO BẮT BUỘC, KHÔNG phải cổng chặn.** Lý do: đưa sức khoẻ/mỏi vào hàm mục tiêu là **vi phạm `specs/advisor-objective-model-v2.md` §1.2b** (sức khoẻ chỉ cộng một chiều ở tier-5). Đề xuất: mọi công bố của kênh **phải kèm** hai số; ngưỡng chặn thì **để Cường chốt**, không phải agent.
- **Số hôm nay.** **93,69 km/ngày/đội** CI[+86,36;+101,37] · 2,596 km/lượt · **DERIVED 24,0 phút rỗng/chuyến mới**. ⚠ Con số 13,75′/mover là **điều kiện hoá hậu-xử-lý** — trích phải kèm cảnh báo chọn mẫu.

### M-5 — `mde_per_archetype`: mọi PASS của tầng 1b phải in kèm LỰC

- **Định nghĩa.** Với mỗi archetype P1..P7, báo `MDE(80%)` cùng lúc với verdict.
- **Cách tính.** `sd`/`se` per-archetype đã có sẵn trong `per_seed` của mọi artifact ĐA-08; MDE = 2,8 × se (công thức chuẩn, pb6 đã dùng).
- **Ngưỡng — đây là phần đổi ngữ nghĩa.** Nếu `MDE(80%) > |ngưỡng quan tâm|` thì verdict là **`KHÔNG ĐỦ LỰC`**, **không phải PASS**. Hôm nay tầng 1b PASS 0/7 archetype âm-SIG, nhưng **P3 (n=5/90) có điểm ước lượng −18.758đ** — một PASS **không có nghĩa gì**.
- ⚠ **CHỈ giữ phần (i) báo MDE.** Phần (ii) của pb3 — "thêm phân tầng tercile 30/30/30 cho cân mẫu" — **BỊ BÁC**: trục tercile giải thích **NHIỀU HƠN ở thế giới không can thiệp** (R² null **0,0526** > thật 0,0463) ⇒ cổng đó sẽ **báo động mạnh nhất đúng lúc không có gì xảy ra**.

---

## 3. THIẾU TÍNH NĂNG — 3 đề xuất (đều sống sót phản biện)

### DX-01 — Thẻ **TỔNG KẾT CA chỉ-đọc** (F3): nối S3 vào một endpoint, **không xin tài xế làm gì cả**

- **US THẬT:** US-F3-01 (tách gross / driver payout / estimated net) · US-F3-02 (vài pattern chưa tối ưu) · US-F3-03 (đúng MỘT gợi ý). **Cả ba đang có 0 đường** (TN-01).
- **Chi phí:** thấp nhất trên bảng. S3 chạy **1.100/1.100 = 100%**, đã có pattern cho **767/1.100 = 69,7%**, đã có gross+payout cho **1.069/1.100 = 97,2%**, đã có `top_pattern` + `heuristic_note` tiếng Việt + `severity` + `numbers[].source` truy vết được. **Thiếu đúng một lời gọi + một endpoint.**
- **Đo bằng ĐA-08:** 🔴 **KHÔNG THỂ KIỂM** — nói thẳng. Twin-world không có cơ chế nào biến "đọc một bản tổng kết" thành payout. **Và có lý do thứ hai để không hứa**: pattern chi phối là `bonus_progress_gap` (**739/858 = 86,1%**) mà hành động kế tiếp của nó là *"ca sau chạy thêm ít cuốc"* — tức **KÉO DÀI CA**, đúng chỗ `D-M3-04` đã đo `work_span_p90 +42′` và STOP-C bắn.
- **Đo thay bằng hai thứ ĐO ĐƯỢC ngay:** (1) **test vi phân** — số trên thẻ recap phải TRÙNG TỪNG ĐỒNG với `payout_breakdown` của ledger cùng (tài xế, ngày); (2) tỷ lệ hiển thị/ẩn qua `AdviceEventLog` đã có.
- **§5:** an toàn nhất trong ba — không khuyên nhận/từ chối đơn, không hứa thu nhập (docstring S3 literal `KHÔNG số loss tuyệt đối`), `is_mock:true` giữ nguyên; `estimated_net` phải hiện **`partial/unknown`**, KHÔNG ước đoán (TN-10).
- ⚠ **Phản biện chính đề xuất này:** `inferred_activities` rỗng **1.100/1.100** ⇒ thẻ chỉ nói được **2/4** loại pattern. **Đừng bán nó là "phân tích sau ca đầy đủ".** Và nó **KHÔNG có bằng chứng làm tăng thu nhập** — giá trị là **lấp một khối SCOPE đang trống**, không phải một Δ tiền.

### DX-02 — Sửa **vách parquet của S6** rồi nối kênh `mission_pick`

- **US THẬT:** US-F1-04 mở rộng sang mini-task + ô `UC8 mini-task` mà `router.py` khai từ đầu. Dữ liệu dày: 6 mission active, **261 dòng progress phủ 110/110** tài xế in-scope, 159 `in_progress`.
- **Đo bằng ĐA-08:** 🟢 **ĐO ĐƯỢC** — **đề xuất DUY NHẤT trong ba cái đo được với twin-world HIỆN CÓ**. World đã mô hình hoá mission (grep `mission` trên `src/gsm_sim` = **27 hit**; đối chứng `penal`/`fraud`/`khoan`/`voucher` = **0**). Thêm một nấc `mission_pick` vào `CHANNEL_LADDER` → `run_pair` 30+ seed CRN → chấm 1a + 1b. Hạ tầng đã dùng thật (UPDATE-160 chấm `station_choice` NO-GO bằng đúng đường này).
- **§5:** an toàn — `reward_vnd` LẤY TỪ `public_mission` (docstring literal *"không bịa"*), không khuyên nhận/từ chối đơn, không đụng dispatch.
- ⚠ **Ba phản biện phải mang theo:**
  1. **Sửa 1 dòng KHÔNG đủ.** Test hiện tại **không thể đỏ** vì chạy trên bảng in-memory (TN-05). **Cổng phải là "deriver đọc lại từ parquet ĐÃ GHI"**, nếu không lần sau vẫn thế. Và đặt bản vá ở **MỘT chỗ dùng chung** — `mockdata.py:157` đã là lần vá thứ nhất, **không chép lần thứ ba**.
  2. `tests/test_mission_knapsack.py` còn **cơ chế vô hiệu độc lập**: dung sai `+SLOT_MIN/60 = 0,25h` **bằng đúng độ hạt lưới** ⇒ bất đẳng thức ràng buộc giờ luôn đúng; và oracle brute-force **dùng lại chính công thức cost của solver**. ⇒ **Đừng tin suite xanh của S6 sau khi sửa.**
  3. **Kỳ vọng phải đặt THẤP và prereg TRƯỚC.** Chỉ 6 mission ⇒ trần giá trị nhỏ, mà **MDE của ĐA-08 ở n=30 ≈ 2.560đ/người/ngày** (PB6-08) ⇒ **rất có thể ra ns**. **`ns` là kết quả HỢP LỆ**, không phải thất bại — nhưng **đừng bán DX-02 như "đề xuất đo được giá trị"**.

### DX-03 — `policy_ref` (version + hiệu lực + doc) vào contract thẻ, kèm cổng cấm `sim-policy-*`

- **US THẬT:** US-F0-03 (*"cảnh báo khi chính sách đổi so với lần tôi xem trước"*) **không thể tồn tại** khi `effective_from=None`; đồng thời là điều kiện cần của US-F0-01 và của **CLAUDE §5** (*"trả lời chính sách phải dựa trên nguồn có trích dẫn… có version"*).
- **Hiện trạng đo được:** `version='sim-policy-v0'` — **một id CONFIG SIM đóng vai version chính sách**; `effective_from/to = null`; `advice.json` item có **9 trường, 0 trường citation**; corpus policy t004 có **7 record** nhưng **1 importer duy nhất = `pipeline.py`** (cụm TN-08 đề nghị BỎ) ⇒ **corpus không có đường tới tài xế**.
- **Đo bằng ĐA-08:** 🔴 **KHÔNG THỂ KIỂM** — đây là tính năng **xuất xứ/tuân thủ**, không có cơ chế payout. **Cái ĐO ĐƯỢC là cổng tĩnh**: hôm nay nó **ĐỎ** (đo được: `policy_v:sim-policy-v0`, `effective_from=None`), sau khi sửa thì XANH ⇒ **cổng tự chứng minh đỏ được**.
- ⚠ **Hai phản biện phải mang theo:**
  1. Nó **KHÔNG tự sinh ra dữ liệu**. Nếu GSM chưa cấp policy có ngày hiệu lực thì cổng **đỏ vĩnh viễn**, và áp lực rẻ nhất khi test đỏ là **đặt bừa một `effective_from`** — đúng mẫu lỗi *"vặn config cho khớp phép đo"*. ⇒ **Cổng phải assert NHÃN KHỚP TRẠNG THÁI** (`validity: UNKNOWN` **là hợp lệ và phải hiện ra cho tài xế**), **KHÔNG assert "phải có ngày"**. Đây là khác biệt sống-chết giữa cổng tốt và cổng sẽ bị nới.
  2. **Không được để nó nở thành "nối lại pipeline C6 để có citation"** — corpus chỉ 7 record và cụm C6 là thứ TN-08 đề nghị BỎ. Citation phải đi kèm **từng thẻ** qua `policy_ref`, không qua một tầng KB free-text.

---

## 4. PLAN VÁ — thứ tự

**Nguyên tắc xếp (theo yêu cầu):** ① chạm **ĐỘ TIN CỦA PHÉP ĐO** trước chạm **giá trị** · ② **ĐƯỜNG SẢN PHẨM** trước **sim** ·
③ cái **đang CHỜ CƯỜNG QUYẾT** không xếp (xem §5c).

---

### **B0 — SỬA VĂN BẢN. Không một dòng code.** *(độ tin phép đo · docs-only)*

- **Root cause đã chứng minh?** ✅ **CÓ.** pb1 đo arm null; refuter **tái lập độc lập từng chữ số** từ `pb1b-raw.json.gz`. Hai đường đo độc lập, cùng kết luận.
- **Việc:** (a) rút mọi con số tercile khỏi mọi báo cáo/doc/UPDATE đang lưu hành; (b) cập nhật `DEFERRED.md` `D-C9-PHAN-PHOI` từ *"chưa loại được"* → **"ĐÃ LOẠI"** kèm artifact `pb1b-raw.json.gz` + `pb-refute.json`; (c) ghi lại **ba số được phép công bố** (§0.2) kèm trần null PB6-05/06.
- **Test đo-trước:** đếm hit của các literal `15.290` · `26.106` · `23.566` · `14.602` · `58,4` · `17,82` · `42,30` · `89.264` trên `{tracking,research,docs,specs}` — **hôm nay > 0**.
- **Acceptance BẰNG SỐ:** hit = **0** ngoài các file có nhãn `ĐÍNH CHÍNH`/`BỊ BÁC` tại chỗ.
- **Rủi ro đảo kết luận:** THẤP. Nếu placebo "giữ đúng tập 33% người bị chạm" (§6) sau này cứu được một phần biên độ, việc **rút số** vẫn đúng — số sẽ được **báo lại kèm điều kiện**, không phải khôi phục nguyên trạng.
- **Phụ thuộc:** không. **Làm được ngay hôm nay.**

---

### **B1 — PB5-01 + PB5-09 (cùng cycle, bắt buộc đi kèm).** *(đường sản phẩm · an toàn)*

- **Root cause đã chứng minh?** ✅ **CÓ.** Hai bất biến trong **cùng một file** loại trừ nhau (`_cliff_item` cố ý `numbers: []` vs `_verify_item` đòi mọi số trace về `numbers`); tầng chặn thứ hai độc lập ở `cards.js` (`a.items[0]`, cliff luôn `append` thứ hai). Refuter **reproduce 100%**.
- **Vì sao B1 chứ không B2:** đây là chỗ duy nhất mà **im lặng có thể gây hại vật chất cho tài xế** — **160/246** lần cliff bị vứt là lúc thẻ chính đang giục chạy thêm để lấy thưởng.
- **Test đo-trước (phải ĐỎ trước khi sửa):** một test gọi **`advisor.advice()`** — điểm vào công khai duy nhất — trên fixture `d-0 / 2026-08-25 / 540′ / acc=0,8617`, assert cliff item có mặt trong output. ⚠ **`ui/backend/tests/test_e3_canh_bao_thu_nhap.py` có 4 test và KHÔNG test nào gọi `advice()`**; một test còn assert `it["numbers"] == []` **như một ĐỨC TÍNH** trong khi fixture của chính nó chứa "0.86"/"0.85" — hai điều kiện giết nhau **cách nhau 6 dòng** mà không test nào ghép. Một test khác dùng `inspect.getsource(...)` + `src.count("_cliff_item(") >= 2` ⇒ **kiểm CHỮ TRONG SOURCE, xanh dù đầu ra rỗng**. **Ba test này phải sửa, không phải giữ.**
- **Acceptance BẰNG SỐ:** trên cùng sweep 2.310 lượt — cliff sống **≥ 246** (hôm nay 0); item/payload sau verifier có **{2: 246}** (hôm nay {1: 2.309}); **và** số event `displayed` = số **ITEM**, không phải số **PAYLOAD** (đây là PB5-09 — `advice.py:360` `event_id` không chứa `advice_id`; **không sửa cùng lúc thì 246 lượt sẽ đánh rơi event ngay lập tức**).
- **Rủi ro đảo:** TB. Sửa verifier để "nới" là **sai hướng** — verifier tồn tại để chặn số không trace được. Hướng đúng: hoặc cho `_cliff_item` khai `numbers` (rồi caveat nói rõ đây là **ngưỡng chính sách**, không phải cam kết tiền), hoặc cho V1 bỏ qua số **thuộc ngưỡng policy đã có trong `policy_thresholds`**. **Chọn hướng nào là quyết định sản phẩm ⇒ phải qua brainstorm + plan mode.**
- **Phụ thuộc:** không.

---

### **B2 — PB5-02: số tiền trên mặt thẻ.** *(đường sản phẩm · số tiền sai chiều)*

- **Root cause đã chứng minh?** ✅ **CÓ về cơ chế** — `policy.py:104 bonus_at` và `gsm_sim/policy.py:94 day_bonus` **cả hai GÁN, không cộng dồn** (tôi verify lại cả hai). ⚠ **CHƯA về ngữ nghĩa GSM thật**: pb5 tự khai confidence *"TB cho tầm ảnh hưởng thực — chưa xác nhận với policy GSM THẬT rằng thưởng ngày là bậc thang thay thế"*.
- **⇒ Sửa theo NGỮ NGHĨA CỦA REPO là đúng ngay hôm nay** (hai implementation đều thế), nhưng **nhãn phải nói "theo chính sách đang cấu hình"**, và **câu hỏi cho GSM phải vào `BACKLOG-QUESTIONS`**.
- **Test đo-trước:** fixture tài xế `points_now = 65` (đã chốt 30.000đ), mốc kế 100đ/60.000đ ⇒ thẻ hôm nay hiện **60.000đ**; test assert phải hiện phần kiếm thêm **30.000đ** ⇒ **ĐỎ**.
- **Acceptance BẰNG SỐ:** trên 1.129 thẻ `feasible_gap` — **0 thẻ** hiển thị `tier_vnd` khi `bonus_at(points_now) > 0`; **111 thẻ đổi số**, trong đó **105 thẻ 60.000→30.000** và **6 thẻ 115.000→55.000**; 1.018 thẻ còn lại **không đổi**.
- **Rủi ro đảo:** **CAO nếu GSM cộng dồn** — khi đó số hiện tại đúng và fix sai. ⇒ **Ghi điều kiện đảo tường minh trong UPDATE**; nếu Cường xác nhận được với GSM trước thì làm theo, nếu không thì sửa theo repo + nhãn.
- **Phụ thuộc:** không (nhưng nên cùng đợt review với B1 vì cùng file, cùng mặt thẻ).

---

### **B3 — TN-05 / DX-02 bước 1: vách parquet của S6.** *(đường sản phẩm · crash 100%)*

- **Root cause đã chứng minh?** ✅ **CÓ, reproduce hai lần** (pb4 + refuter): `rewards` là dict in-memory, **str sau khi ghi đĩa**, `from_l1r.py:324` gọi `.get()` trên str ⇒ `AttributeError` **1.100/1.100**.
- **Test đo-trước (đây là phần quan trọng hơn cả bản vá):** test phải **ghi parquet rồi ĐỌC LẠI** bằng loader sản phẩm (`mockdata._table(...).to_dicts()`) rồi mới gọi `derive_mission_select_input_l1r`. **Hôm nay ĐỎ.** Test in-memory hiện có **không thể đỏ**.
- **Acceptance BẰNG SỐ:** crash **1.100/1.100 → 0/1.100**; và `rewards` sau loader là **dict 6/6** ở cả ba tầng (in-memory / parquet / loader).
- **Rủi ro đảo:** THẤP cho bản vá. ⚠ **CAO cho việc tin suite**: `test_mission_knapsack.py` còn dung sai `<= hours + SLOT_MIN/60` **bằng đúng độ hạt lưới** và oracle **dùng lại chính công thức cost của solver** (pb4 **đọc code, chưa đo lại**) ⇒ **suite xanh sau khi sửa KHÔNG phải bằng chứng S6 đúng**.
- **Phụ thuộc:** không. **Dừng ở đây** — bước nối kênh `mission_pick` vào `CHANNEL_LADDER` là **B7**, sau khi có M-1.

---

### **B4 — M-1: cổng hiệu chuẩn placebo vào ĐA-08.** *(độ tin phép đo · sim)*

- **Root cause đã chứng minh?** ✅ **CÓ.** ĐA-08 hôm nay **PASS TOÀN BỘ 5 TẦNG** cho positioning trong khi arm null cho `harmed_share` **cao hơn**, `churn_ratio` **cao hơn**, `delta_p10` **âm hơn** ⇒ chuẩn **không phân biệt được kênh với nhiễu** ở mọi tầng trừ 1a.
- **Test đo-trước:** chạy đúng bộ chấm ĐA-08 trên **arm N** (advice tắt). Hôm nay nó **PASS** ⇒ **cổng đang cấp giấy thông hành cho một thế giới không có can thiệp nào**. Đó là bằng chứng đỏ.
- **Acceptance BẰNG SỐ:** sau khi thêm M-1, arm N phải cho verdict **`KHÔNG QUY ĐƯỢC CHO KÊNH`** ở **cả 5 tầng**; arm B giữ **PASS ở 1a** (hiệu B−N = +3.219 − (−769) và CI loại 0) và chuyển sang **`KHÔNG QUY ĐƯỢC`** ở mọi lát cắt tercile.
- **Rủi ro đảo:** **TB — và phải nói thẳng:** M-1 **có thể làm kênh đang ship mất verdict PASS ở một số tầng**. Đó là **kết quả hợp lệ**, không phải sự cố. Nhưng nó **đổi chuẩn ship** ⇒ **bắt buộc plan mode + Cường duyệt**.
- **Phụ thuộc:** B0 (văn bản phải sạch trước khi đổi chuẩn, nếu không sẽ có hai bộ số cùng lưu hành).

---

### **B5 — M-2 + M-3 + PB3-11: nối khoá bị vứt, chấm tầng Tập trung, gỡ double-call.** *(chuẩn đo · rẻ)*

- **Root cause đã chứng minh?** ✅ **CÓ, bằng đọc code + grep** (tôi verify: `cham_da08_station_choice.py` có **0 hit** cho `station_hhi`/`supply_cell_hhi`; `sim_metrics.py:307` gọi `health_guardrail(result)` rồi `parallel.py:219` gọi lại với `actor_ids` khác).
- **Test đo-trước:** (a) chạy bộ chấm trên một artifact có `supply_cell_hhi` **tăng SIG** giả lập ⇒ hôm nay **PASS sai**; (b) đếm số lời gọi `health_guardrail` cho một `result` ⇒ hôm nay **2**.
- **Acceptance BẰNG SỐ:** bộ chấm đi từ **6 → 8 phép** phủ đủ **5/5 dòng** bảng §5; `wait_p90_min` + `payout_p10/median/p90` + `event_repeat_ratio` + `event_adherence_is_lower_bound` có mặt trong `compare()`; `health_guardrail` được gọi **1 lần**/result.
- ⚠ **RÀNG BUỘC CỨNG (PB3-10):** chỉ thêm **scalar hệ thống** vào `_system_metrics`. **KHÔNG được nhét đại lượng ghép cặp vào `system_*`** — `_rows` áp `b − a` cho MỌI khoá ⇒ sẽ ra vô nghĩa **im lặng**, đúng họ `net_mean_all` hai công thức. Metric ghép cặp cần **trường mới trong `PairResult`** = **đổi contract**, và phải rà `dashboard.py`, `measure_e10.py`, `measure_l104.py`, `cham_da08_*.py`.
- **Rủi ro đảo:** THẤP cho M-2/M-3. **TB cho PB3-11**: gỡ double-call đổi **chi phí tính**, không đổi số (9/9 khoá lấy từ `g` hiện ngoài tầng 5 ⇒ độ lệch hôm nay = 0) — nhưng **chưa reproduce bằng một ca sai thật**, nên phải verify fingerprint bất biến.
- **Phụ thuộc:** không (làm song song B4 được, khác file).

---

### **B6 — M-4 + M-5: công bố chi phí chạy rỗng và MDE per-archetype.** *(chuẩn đo · báo cáo)*

- **Root cause đã chứng minh?** ✅ **CÓ.** S4-D7: candidate dùng **đúng 4 trường**, cost **không có số hạng km/thời gian nào** — nhưng chi phí **đo được**. PB3-03: 1b chỉ tố giác hại và P3 n=5/90.
- **Test đo-trước:** in verdict ĐA-08 hôm nay — **không có** dòng nào về km/phút rỗng, **không có** MDE nào.
- **Acceptance BẰNG SỐ:** mọi công bố kênh positioning kèm **93,69 km/ngày/đội** (CI) + **24,0′/chuyến mới (nhãn DERIVED)**; mọi verdict 1b in kèm MDE — và **P3 chuyển từ `PASS` sang `KHÔNG ĐỦ LỰC`** (MDE hiện tại nuốt trọn điểm ước lượng −18.758đ).
- **Rủi ro đảo:** THẤP (thêm chỉ số báo cáo, không đổi hành vi). ⚠ **KHÔNG đưa sức khoẻ/mỏi vào hàm mục tiêu** — vi phạm spec §1.2b.
- **Phụ thuộc:** B4 (để MDE và chi phí nằm cùng một bản verdict đã hiệu chuẩn).

---

### **B7 — DX-02 bước 2: nối kênh `mission_pick`.** *(giá trị · sim, ĐO ĐƯỢC)*

- **Root cause:** không phải bug — đây là **tính năng**. Điều kiện tiên quyết là B3 (vách parquet) **đã xong và có cổng đọc-lại-từ-đĩa**.
- **Test đo-trước:** prereg **TRƯỚC KHI CHẠY** — tiêu chí 1a (`payout_mean_all` CI95 loại 0) + 1b (0/7 archetype âm SIG) + **M-1** (hiệu với arm null SIG) + **M-2/M-3/M-4**.
- **Acceptance BẰNG SỐ:** ⚠ **prereg rằng `ns` là PASS của quy trình, không phải thất bại.** **MDE ở n=30 ≈ 2.560đ/người/ngày**; chỉ có 6 mission ⇒ **trần giá trị nhỏ hơn MDE là kịch bản có thật**. Nếu muốn kết luận NULL cho `mission_pick` thì phải **n=100** (MDE → ~1.402đ, **DERIVED** từ PB6-08).
- **Rủi ro đảo:** TB. **Đừng bán DX-02 như "đề xuất đo được giá trị"** — nó là "đề xuất **đo được**", khác nhau.
- **Phụ thuộc:** B3, B4.

---

### **B8 — DX-01 (thẻ tổng kết ca) và B9 — DX-03 (policy_ref).** *(giá trị · đường sản phẩm)*

Xếp **sau** vì cả hai là **KHÔNG THỂ KIỂM bằng ĐA-08** ⇒ chúng lấp SCOPE chứ không chứng minh giá trị.
Acceptance của chúng là **cổng tĩnh tự chứng minh đỏ được** (DX-01: test vi phân recap vs ledger, trùng **từng đồng**;
DX-03: cổng assert **NHÃN KHỚP TRẠNG THÁI**, `validity: UNKNOWN` là hợp lệ). Phụ thuộc: B1/B2 (cùng đụng mặt thẻ và contract).

---

## 5. KHÔNG LÀM — và vì sao

### 5a. Không làm vì **đã bị bác bằng số**

1. **KHÔNG dựng `harmed_share` / `churn_ratio` / `delta_p10` làm cổng.** Cả ba báo động **MẠNH HƠN ở arm không-advisor** (46,00% vs 42,30% · 78,02× vs 17,82× · −98.467 vs −89.264). Ngưỡng đề xuất sẽ **TREO một thế giới không có can thiệp nào**. `churn_ratio` còn **phạt càng mạnh khi can thiệp càng VÔ HẠI** (tiến ra vô cùng khi net → 0).
2. **KHÔNG thêm phân tầng tercile vào tầng 1b.** Trục đó giải thích **NHIỀU HƠN ở arm null** (R² 0,0526 > 0,0463) ⇒ cổng sẽ báo động mạnh nhất **đúng lúc không có gì xảy ra**. Tỷ số 4,90× của pb3 là **thật nhưng ý nghĩa bị đảo**.
3. **KHÔNG làm bất kỳ chính sách bù trừ / bật-kênh-theo-nhóm nào theo tercile.** Nhóm đó **không tồn tại ổn định**: **13/90** actor giữ nguyên tercile qua 30 seed, **63/90** trải hết cả ba. "Người rảnh nhiều" là **một lần rút thăm**, không phải một người.
4. **KHÔNG "giải thích" c9b bằng độ dài ca.** Chia theo `online_min` thì mẫu hình **biến mất và đảo dấu** (+4.162 SIG / +6.722 SIG / −1.594 ns) — PB6-11.
5. **KHÔNG chạy thêm 70 seed để "xác nhận" −15.290đ / +26.106đ.** Hai số đó đã có power ≈ 1,000 và đủ từ **n=15**. Thêm seed **chỉ siết các NULL**, không làm biên độ chắc hơn.
6. **KHÔNG trích c9c như "đã loại hồi quy về trung bình".** Nó là placebo **phương sai = 0** (30/30 bit-identical, CI [0,0]) ⇒ **lực bằng 0**.

### 5b. Không làm vì **đã có trong hàng đợi / trùng thực thể** *(13 mục refuter bác)*

| Bị bác | Lý do (rút gọn) |
|---|---|
| **S4-D1** | Đã có trong `DEFERRED.md` `D-ADV-01` từ trước, sev CAO, TODO — nội dung code **đúng** nhưng **đúng với cái đã nằm trong hàng đợi**. Phần mới (472/472) là **bằng chứng bổ trợ** = S4-D3, không phải finding riêng |
| **S4-D2** | Trùng thực thể với `D-ADV-01(b)`, vốn **đã có cả con số** (56% ở 3 seed → **đính chính 60,6% ở 5 seed**). pb2 đo 58,2% ở 30 seed — **số TỐT HƠN nên THAY THẾ số cũ trong DEFERRED**, nhưng là **cập nhật một mục đã có** |
| **S4-D4** | **LÁT CẮT NHIỄM** — arm null cho gradient cuốc **LỚN HƠN** (−0,846/−0,478/+1,358 vs −0,586/−0,233/+1,394) trong khi net +0,011 cuốc/người ⇒ quy ra "tỷ lệ chuyển giao" của **thế giới không can thiệp ≈ 97% > 58,4%**. **Con số 0,584 đúng nhưng nó là hàm của ĐỘ XÁO TRỘN, không phải HƯỚNG CHUYỂN GIAO** |
| **S4-D8** | Mô tả **nửa đúng nửa sai**. Đúng: S4 không có biến nào cho thu nhập luỹ kế / số lần đã gán / người ĐANG Ở đích; tiêu chí duy nhất là `priority_soc`; 88,0% suất có trần = 1. **Sai ở vế làm nên severity**: "một phần ba **nhận diện được TRƯỚC KHI CHẠY** bị mất tiền có hệ thống" dựa vào −15.290đ và bị PB6-12 bác. Câu *"ai đảm bảo nó không làm giàu người rảnh bằng tiền người bận — KHÔNG AI"* **còn đúng về THIẾT KẾ**, nhưng phải phát biểu thuần tuý như **mô tả thiết kế, KHÔNG kèm bằng chứng tercile** |
| **PB3-01** | Cả hai trụ chống đều đo ở arm null và **xấu hơn**. "DA-08 cấp giấy thông hành cho một can thiệp có biên độ phân phối lại" — **sai dấu**: cái được đo là **SÀN NHIỄU**, không phải lỗ hổng. (Phần CÒN ĐÚNG về cổng DA-08 nằm ở PB3-05, đã giữ) |
| **PB3-07/08/09** | Neo null sai (dựa vào c9c phương sai-0) + ngưỡng bị chính arm null vượt — xem §5a.1 |
| **PB6-01** | Trùng PB1-06 (cùng đại lượng: 18,3× / 17,8× / 17,82×) **và quy kết nhân quả** mà pb1 không quy. MAD arm null **59.983đ > 57.379đ** ⇒ thế giới **không có kênh nào** cũng xáo trộn nhiều hơn. **Giữ PB1-06, bỏ PB6-01** |
| **PB6-02** | Thống kê đúng và đo thật (mean/median t2 = 5,3×; 33,7% trong nhóm "thắng" vẫn âm) nhưng **mô tả phân phối của một nhóm không tồn tại ổn định** (PB6-12) ⇒ không thể là finding HIGH; vế cảnh báo đã nằm trong PB1-06/PB1-11 ở cấp mạnh hơn |
| **PB6-10** | Sự thật về **MỨC NỀN** đúng và tái lập được — nhưng đó **là nội dung của PB1-05**, tính MỘT lần. Phần pb6 THÊM vào ("kênh chuyển tiền từ nhóm NGHÈO NHẤT sang nhóm khá hơn", −6,6% đổi +9,9%) là **phép chia hai số mà cả tử số đã bị arm null tái tạo** ⇒ **"tái phân phối là NGHỊCH TIẾN" phải RÚT** |
| **PB6-18** | Trùng PB1-02, và bản pb1 **mạnh hơn** (chỉ ra hậu quả + thay bằng placebo có nhiễu thật). Phần pb6 thêm vào là **ghi chú vận hành đúng** — nên giữ **trong chính file c9c**, không phải một finding |

### 5c. Không xếp vào plan vì **đang CHỜ CƯỜNG QUYẾT**

- **P2/P3 của pb2** (sửa hàm mục tiêu S4 để có số hạng khoảng cách; chạy arm ORACLE): `D-ADV-01` ghi thẳng đây là **"ĐỀ XUẤT cần Cường duyệt, không phải sửa bug"**; đổi kênh **ĐANG BẬT** ⇒ **bắt buộc regate ĐA-08 n=100**. **Và có lý do kỹ thuật để chưa làm** (xem §5d.1).
- **TN-08** (xoá cụm C6 free-text 1.184 dòng): **quyết định sản phẩm**, không phải quyết định kỹ thuật. Cái nên làm ngay mà **không cần quyết định**: gắn nhãn `router.py` để không ai đọc `_ROUTES` (khai đủ S1..S9) rồi tin 9 solver đang chạy.
- **Q-09 / Q-10 / V-31 / V-32** trong `PENDING-REVIEW.md` — không đụng.

### 5d. Không làm vì **lý do kỹ thuật**

1. **KHÔNG sửa hàm mục tiêu S4 trước khi biết có bài toán gán nào để giải.** c9d đo được **bản MÙ tái tạo toàn bộ hiệu ứng**; nếu thông tin hiện tại đóng góp **không đo được** thì **không có bằng chứng nào nói một thông tin TỐT HƠN sẽ đóng góp > 0**. Và S4-D3 cho thấy **greedy trùng Hungarian 472/472** ⇒ **sửa cost mà không sửa trần (B1 của bản đồ lớp) là tốn công không đổi được gì.**
2. **KHÔNG vặn `cash_cost_vnd_per_km` để "quy km ra tiền".** Bản đồ lớp §4.9: van này **INERT** (bất biến từng bit trên [0; 4.325]đ/km) — và làm thế là **vặn config cho khớp phép đo**.
3. **KHÔNG mở cycle cho B8 (SOC không có sàn)**: mẫu số đúng cho **0,76%** (17/2.234 lượt), không phải 8,7% cực trị theo seed.
4. **KHÔNG mở cycle cho B5 (sensitivity capacity −20%)**: **99,25% suất bất động** vì `max(1, int(round(...)))` — đây là **hệ quả số học**, không phải một lựa chọn.
5. **KHÔNG đưa sức khoẻ/km rỗng vào hàm mục tiêu** — vi phạm `advisor-objective-model-v2.md` §1.2b. M-4 là **chỉ số BÁO CÁO**.
6. **KHÔNG hứa ĐA-08 đo được DX-01 và DX-03** — tuyên **KHÔNG THỂ KIỂM** theo `specs/real-data/data-contract-counterfactual.md §4`. Tương tự **S8/S9** (TN-06): world có **0 hit** `penal`/`fraud` ⇒ đưa vào hàng đợi "đo hiệu quả" là hứa một phép đo không tồn tại.
7. **KHÔNG phát biểu gì dựa trên trạng thái test suite.** Refuter tự khai **không chạy** `uv run pytest -q` lẫn `uv run pytest -q ui/backend/tests`.

---

## 6. CẢNH BÁO TRUNG THỰC — cái vẫn là **SUY LUẬN CHƯA ĐO**

### 6.1 — Phép thử duy nhất còn lại chưa ai chạy 🔴

Refuter nói thẳng: *"Tôi **KHÔNG chứng minh** hiệu ứng nhóm bằng 0. Tôi chứng minh nó **KHÔNG ĐO ĐƯỢC và KHÔNG QUY ĐƯỢC** cho kênh."*
**Placebo hoàn hảo — giữ nguyên ĐÚNG tập ~33% người bị chạm, chỉ đổi nội dung lời khuyên — chưa ai chạy.**
Đó là phép thử duy nhất có thể cứu bất kỳ con số tercile nào. Phản biện có thể nêu: *"arm N xáo trộn niềm tin của cả 90 tài xế,
arm B chỉ chạm ~33% ⇒ N là cú sốc mạnh hơn nên gradient lớn hơn là đương nhiên."* **Ba điểm chống lại:** (i) liều per-driver
gần bằng nhau (MAD 59.983 vs 57.379); (ii) N cho gradient **≥** trong khi net = −769đ **ns**; (iii) tercile 2 của N (+25.338)
và của B (+26.106) **không phân biệt được về thống kê**. Nhưng **ba điểm này không thay thế phép thử.**

### 6.2 — Trần của kết luận thuận lợi "Hungarian bị bác"

**Bất kỳ báo cáo nào nói "thông tin của solver đóng góp 0" đều là OVER-CLAIM.** Cận trên CI95 của (B − SHUF):
toàn đội **+414đ = 12,9%** của +3.219đ; **28,3%** nếu hiệu chỉnh Bonferroni k=4; ở tercile lỏng tới **16,7%**.
Muốn đủ chặt để ship thì cần **n=100** (MDE 2.560 → ~1.402đ, trần → ~11,8% — **DERIVED**, chưa chạy).

### 6.3 — Phạm vi chính xác của kết luận c9d

SHUF **phá GHÉP CẶP nhưng GIỮ NGUYÊN tập ô được chọn** ⇒ **cái bị bác là HUNGARIAN MATCHING (`linear_sum_assignment`),
KHÔNG phải việc CHỌN Ô.** Arm còn thiếu (điều kiện để bác nốt, PB1-10): **giữ nguyên liều + giữ nguyên số suất mỗi ô
nhưng CHỌN TẬP Ô NGẪU NHIÊN trong zones hợp lệ**. Nếu arm đó cũng cho ≈ +3.2k thì **phần giá trị cuối cùng của kênh cũng sụp**.

### 6.4 — Giả thuyết cơ chế được giao cho pb2: **BỊ BÁC NGAY Ở TIỀN ĐỀ** ⚠

Giả thuyết đặt ra: *"Hungarian tối thiểu hoá TỔNG ETA/quãng đường, mà `cash_cost_vnd_per_km = 0` ⇒ nó tối ưu một đại lượng MIỄN PHÍ."*

**Đọc code (S4-D3 + S4-D7): cost matrix KHÔNG CÓ số hạng ETA/khoảng cách nào cả.** `cost[i,j] = pen` nếu trùng target,
ngược lại `pen + 10.0`; `pen` **không phụ thuộc cột**; candidate mang **đúng 4 trường** `{driver_id, advice_kind, target, priority_soc}`
— **không có trường khoảng cách**. ⇒ **Nó không tối ưu một đại lượng miễn phí; nó tối ưu "số lượt lệch target", một đại lượng
NHỊ PHÂN suy biến** (`10` áp đảo `pen ∈ [0;1]`). Đó là lý do greedy trùng Hungarian **472/472** — và là lời giải thích cơ chế
**tốt hơn** cho kết quả c9d so với giả thuyết ban đầu. **Nhưng đây là ĐỌC CODE + ĐO trên phân bố input, KHÔNG phải chứng minh
toán học rằng greedy luôn tối ưu.**

### 6.5 — Phạm vi hẹp của mọi số sim

**Một kịch bản, một ngày:** `configs/pilot_dongda.yaml`, `coverage=all`, seed **3300–3329**. **Không multi-day, không kịch bản
mưa/sự kiện, không coverage khác.** Bản đồ lớp §5.6 cảnh: kênh đường hiện chạy ở **điểm vận hành ĐỘI TRẦN**, **tăng liều CÓ THỂ ĐẢO DẤU**.
Thêm nữa: `pilot_dongda.yaml` đã đổi `actors.n` **ba lần (50 → 74 → 90)**, và **74 không chia hết cho 3** ⇒ chạy lại bộ script
tercile trên config cũ sẽ **kích hoạt lỗi im lặng** (PB6-17), không assert nào canh.

### 6.6 — **KHÔNG được trộn số của pb4 và pb5**

Hai góc dùng **hai cửa sổ khác nhau**: pb5 + refuter dùng **7 ngày `dates[7::12]` × 110 tài xế × 3 mốc = 2.310 lượt**;
pb4 dùng **10 ngày × 110 × 3 = 3.300 lượt**. Vì thế `feasible_gap` là **1.129** ở pb5 và **1.687** ở pb4 — **cùng một sự thật,
hai mẫu số**. Trích số nào phải kèm cửa sổ đó.

### 6.7 — Những chỗ **chưa chạy thật**

- **PB5-06/07** tái lập logic `cards.js` bằng **Python**, **không chạy trình duyệt thật** ⇒ tỷ lệ 71,7% là TB-confidence. Tỷ lệ 1/3-1/3-1/3 giữa ba bề mặt là do **THIẾT KẾ SWEEP**, không phải tần suất thật tài xế mở từng bề mặt.
- **TN-11**: đọc nguyên văn cả hai file config, **chưa chạy demo end-to-end** ⇒ "người xem thấy advisor khác" là **SUY**.
- **TN-01**: phần "US nào coi là có đường" là **PHÁN ĐOÁN** trên tiêu chí "tài xế có nhận được nội dung đó không", không phải phép đo. Refuter chỉ verify được các grep neo (`voucher` 0, `rental` 0, `f3_patterns` 0 call site sản phẩm, `penal`/`fraud` 0 trong `gsm_sim`), **không đối chiếu lại 14 user story**.
- **PB3-11**: hậu quả là **CẤU TRÚC**, **chưa reproduce bằng một ca sai thật**.
- **S4-D7**: nhóm MOVER là **điều kiện hoá hậu-xử-lý**; chỉ **93,69 km/ngày/đội** (đếm sự kiện) là miễn nhiễm. **24,0′/chuyến** và **14.054đ/ngày** là **DERIVED**.
- **PB6-08 ngoại suy n=100** là **DERIVED** (chia `√(100/30)`), chưa chạy.
- Refuter **không đo lại arm SHUF của c9d bằng một lần chạy độc lập** — mọi số B−SHUF đọc từ `per_seed` của c9d json.
- Refuter **không mở `pb2-DO-raw.json`** để tái tính 472 lô và 2.171 hàng cost; ông kiểm **CẤU TRÚC** cost bằng đọc code và **chấp nhận các phép đếm của pb2**.

### 6.8 — `+6.016đ` **không phải phát hiện mới**

Việc `+6.016đ` không tái tạo được **đã được ghi từ trước**: `tracking/updates/UPDATE-113.md:109` — *"CI [2.854, 5.033] **không chứa +6.016**"*.
Và `PENDING-REVIEW.md` **V-23** đã liệt kê nó như *"1 lỗi nghiêm trọng trong doc Khánh: trích +6.016đ mà UPDATE-113:109 nói không tái lập được"*.
Đo hôm nay (**+3.219đ** trên 30 seed tươi) là **xác nhận lần thứ hai bằng một đường đo khác**, không phải phát hiện mới.
⚠ Refuter **không mở UPDATE-087, không điều tra vì sao** — **nguyên nhân gốc của chênh lệch vẫn là `UNRESOLVED`.**

### 6.9 — Cái tôi (người tổng hợp) **không tự đo**

Tôi **không chạy lại một phép đo nào**. Tôi verify **26 neo code bằng nội dung** (§7) và đọc 7 artifact.
**Mọi con số trong bản này là số của pb1–pb6 và của phản biện viên**, không phải số tôi đo.

---

## 7. NEO CODE TÔI TỰ VERIFY LẠI (26/26 khớp)

`advisor.py`: `_cliff_item` **295/315/339/367** · `check_bare_numbers` **296/410** · `startswith(("d-","r-"))` **227 (đúng 1 lần)** ·
`thuong_moc_ke` **281** · `historical_rate_method` **177** · `DEFAULT_SHIFT_END_MIN` **26** · `_policy_thresholds` **243/358** ·
`"source": "SOLVER"` **289** — `policy.py` `def bonus_at` **104** · `gsm_sim/policy.py` `def day_bonus` **94** —
`capacity_alloc.py` `linear_sum_assignment(cost)` **53** · `pen + 10.0` **50** · `max(1, int(round(` **104/105** —
`parallel.py` `BUG-EVAL-ARGMAX` **101** · `def _system_metrics` **176** · `supply_cell_hhi` **208** · `health_guardrail` **188/211/212/214/219** —
`sim_metrics.py` `payout_p10` **217/222** · `wait_p90_min` **45/49/287** · `health_guardrail(result)` **307** —
`cham_da08_station_choice.py` `station_hhi` **0 hit** · `supply_cell_hhi` **0 hit** ✅ (xác nhận PB3-05) —
`from_l1r.py` `rewards.get("vnd"` **324** · `estimated_net_vnd` **232** — `mockdata.py` `json.loads(row["rewards"]` **157** —
`advice_checkpoint.py` `advisor.build_gi` **189** · `UnavailableRuntimeStateProvider` **57/176** —
`advice_v2.py` `ADVICE_V2_ENABLED` **39** — `cards.js` `a.items[0]` **291/314/338/342** · `adv-why hidden` **140/210** —
`advice.py` `ui-shown-` **360** — `demo_session.py` `positioning_overrides` **67** —
`DEFERRED.md` `D-ADV-01` **126** · `D-C9-PHAN-PHOI` **140** — `UPDATE-113.md` **109**.

⚠ **file:line phân rã nhanh** — mọi khẳng định trên đã neo kèm **tên hàm hoặc literal**; khi số dòng lệch, tìm theo nội dung.

---

## 8. BƯỚC 1 — MỘT CÂU

> **Sửa VĂN BẢN trước, không sửa code: rút mọi con số tercile (−15.290đ / +26.106đ / 58,4% / 17,82× / 42,30% / −89.264đ) khỏi mọi báo cáo và đóng `D-C9-PHAN-PHOI` thành "ĐÃ LOẠI", vì arm không-advisor tái tạo toàn bộ mẫu hình đó với biên độ lớn hơn trong khi giá trị ròng nó tạo ra là −769đ ns.**

*Ngay sau đó, cùng ngày: **PB5-01** (246 cảnh báo phòng ngừa bị chính verifier của file đó giết 100%, 160 lần rơi đúng lúc advisor đang giục tài xế chạy thêm) và **PB5-02** (105 thẻ trưng 60.000đ khi phần đổi được bằng công sức chỉ là 30.000đ) — hai cái này nằm trên **đường sản phẩm thật**, không dính gì tới tranh cãi sim, và đã được tái lập từng con số bởi hai người đo độc lập.*
