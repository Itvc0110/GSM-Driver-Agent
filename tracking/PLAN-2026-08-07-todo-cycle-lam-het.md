# PLAN 2026-08-07 — todo cycle **làm hết**

> Cường: *"lên plan để vào todo cycle làm hết, phải nghiên cứu, brainstorm, đọc kỹ tài liệu, công thức,
> logic, code tìm root cause thật TRƯỚC KHI trình plan, nhớ phải docs"*.

**Danh sách cycle canonical: [`research/audit/2026-08-07-root-cause-classes/00-BAN-DO-LOP.md`](../research/audit/2026-08-07-root-cause-classes/00-BAN-DO-LOP.md)**
— 10 cycle, mỗi cycle có root-cause · test đo-trước · acceptance bằng số · rủi ro · phụ thuộc, kèm **§4 (19
điều KHÔNG làm)** và **§5 (14 cảnh báo trung thực)**. File này **không chép lại** bản đồ; nó ghi **phán xử
và đính chính của tôi**, và những gì **Cường phải quyết**.

**Nền:** 13 agent (12 xong, **L4 chết giữa chừng**) truy 6 lớp + đọc nốt 5 artifact + 1 refuter được lệnh
**cố BÁC** · [`00-TU-KIEM-cua-toi.md`](../research/audit/2026-08-07-root-cause-classes/00-TU-KIEM-cua-toi.md)
(6 điều **tôi tự kiểm**) · probe [`c4b-do-vung-mu-tang-5.py`](../research/audit/2026-08-07-root-cause-classes/c4b-do-vung-mu-tang-5.py).

---

## 1. ⚠ HAI ĐÍNH CHÍNH cho chính những gì tôi đã báo hôm nay

### (a) *"6/6 kênh advisor TẮT ⇒ bán kính ảnh hưởng = 0"* — **ĐÚNG NHƯNG KHÔNG ĐỦ**

Tôi dùng câu đó để **đảo thứ tự cả kế hoạch**. Bản đồ đo được **hai đường vòng** mà tôi đã bỏ sót:

- `ui/backend/app/services/demo_session.py:68-71` **bật lại** `shift_plan`/`accept_lift` cho Track UI.
- **S2 đã đi dây ĐẦY ĐỦ trên backend sản phẩm** (`advice_checkpoint.py:206-209` → `main.py:44`). Thứ chặn
  nó là **`missing_state`**, **KHÔNG phải ĐA-07**. Và trên **shape sản phẩm thật** (l1r): `eo==0` **0,0%**,
  cap 2,4 **BIND 88,6%** ⇒ **`S2-3` SỐNG NGUYÊN trên đường sản phẩm**, không chỉ trong sim.

⇒ Kết luận **hướng** vẫn đúng (xếp theo bán kính ảnh hưởng, không theo thứ tự tìm ra), nhưng **tiền đề của
tôi sai ở một vế quan trọng**. Nợ kênh ngủ vào `DEFERRED` **kèm điều kiện mở lại**, **không** kèm câu
*"bán kính = 0"* trần trụi.

### (b) *"6 lớp nguyên nhân"* — **bị bác xuống còn BA cơ chế**

Refuter (được lệnh cố bác) kết luận: **"lớp là một CÁCH KỂ CHUYỆN GỌN cho ba cơ chế thật, không phải sáu
cấu trúc"**. Đo: **54 suất thực thể khai → ~36 phân biệt** (thổi ~50%); `advice_bridge.py:202` một mình
được đếm **ba suất**.

| # | Cơ chế **sống sót cả 4 phép thử** | Cổng |
| --- | --- | --- |
| **(1)** | **KHOÁ CONFIG MA + default IM LẶNG** — 3 điểm code | cổng tĩnh: **4 hit, 0 dương tính giả, <1s** ✅ |
| **(2)** | **CHÉP LUẬT / hai công thức cho một khái niệm** trên đường sản phẩm | **TEST VI PHÂN** ✅ |
| **(3)** | **TEST KHÔNG PHÂN BIỆT ĐƯỢC ĐÚNG VỚI SAI** | **CỔNG ĐỘT BIẾN SENTINEL** ✅ (đã chạy thật) |

- **L6 bị BÁC hẳn như một lớp** (không bác các phát hiện bên trong) ⇒ 3 nợ đơn lẻ vào `DEFERRED`.
- **Hai cổng tôi/agent đề xuất bị BÁC BẰNG ĐO**: cổng CANON literal (**165 bắn/50 file**, phải miễn trừ
  **~97,6%** so với ngưỡng huỷ 10% do chính nó đặt) và luật AST *"parametrize trang trí"* (bắn 6/38 nhưng
  **trật mục tiêu**).
- **`LỚP 0` (nợ ngủ đông sau công tắc) tôi nêu ở bản trước: giữ, nhưng yếu hơn** — vì (a) cho thấy công
  tắc **không phải** thứ duy nhất gác cửa. Nó vẫn đúng cho `ADVICE_V2_ENABLED` và cho `C4b`.

---

## 2. Phát hiện của tôi **đứng vững** sau phản biện

1. **⭐ Bản án ĐA-07 tuyên bởi một solver mù thưởng.** Git: ĐA-07 tắt `shift_plan` **28/07** (`5a44cbb`);
   sửa `points_band_size` 15→5 **06/08** (`bec2671`). Ở band 15, `add_pts // 15 = 0` mọi giờ thường ⇒ mốc
   thưởng **không bao giờ vào giá trị Bellman**. ⇒ **Cycle 10** của bản đồ. **Cần Cường quyết mở lại.**
2. **Vùng mù tầng 5** — probe của tôi đo **7 khoá** cổng không soi / **9 khoá** vắng khỏi `a_mean`, và
   bản đồ ghi nhận probe đó **cứu khỏi một số thổi** (đếm thô ra 11). ⇒ **Cycle 4**, **BLOCKS Cycle 10**.
3. **`R-2` `soc_low` mồ côi** — bản đồ chép lại **nguyên văn mức độ tôi đặt**: *"lỗ hổng HIỂN THỊ, không
   phải lỗ hổng AN TOÀN"*.
4. **`B3` sốt ruột** — chỉ **1/4** hiệu ứng no-op, không phải cả bước.

---

## 3. Thứ tự thi công tôi đề nghị (khác bản đồ ở đúng một chỗ)

| # | Cycle | Vì sao ở đây |
| --- | --- | --- |
| 1 | **Cycle 3** — cổng khoá config, viết **MỘT LẦN** | Cơ chế **(1)**, ba lớp cùng nhận ⇒ rẻ nhất, chặn được nhiều nhất. Reproduce **1 lệnh**. Prereq của Cycle 10 |
| 2 | **Cycle 4** — cổng một chiều phải **thực sự soi** | **BLOCKS** mọi phép đo kênh ngủ. 0 thay đổi số hôm nay ⇒ rủi ro thấp nhất |
| 3 | **Cycle 2** — đính chính 5 bề mặt bằng chứng | docs-only, ~nửa ngày, và **lan truyền đã đo được 2 lần**. Càng để lâu càng nhiễm |
| 4 | **Cycle 1** — một ký ức, một nhịp (v2) | Đường sản phẩm, root cause chứng minh xong. ⚠ **đổi HÀNH VI** ⇒ phải công bố Δ số thẻ |
| 5 | **Cycle 5** — card không được giấu lý do tốn tiền nhất | Đường sản phẩm S1 — solver ghép đủ lý do, tầng UI dựng lại **mất thông tin** |
| 6 | **Cycle 8** — cổng đột biến sentinel | Cơ chế **(3)**; làm suite phân biệt được đúng/sai |
| 7 | **Cycle 9** — liều và trần của kênh **ĐANG SHIP** | Kênh duy nhất đã duyệt bật; `+6.016đ` đang được trích khắp nơi |
| 8 | **Cycle 7** — một tên một công thức cho `net_mean_all` | Nhãn sai trên mọi kết luận cũ (payout gộp ≠ thu nhập ròng) |
| 9 | **Cycle 6** — primitive biết điều kiện thưởng | |
| 10 | **Cycle 10** — đo lại `shift_plan` | **Chờ Cường duyệt**; và phải **sau** Cycle 3 + Cycle 4 |

**Chỗ tôi khác bản đồ:** bản đồ đặt **Cycle 1 là điểm vào**; tôi đặt **Cycle 3 + Cycle 4 trước**, vì cả hai
là **cổng** (0 hoặc gần-0 thay đổi hành vi) trong khi Cycle 1 **đổi hành vi sản phẩm** và làm **mọi số
adherence v2 đo trước đó không so được với sau**. Nợ đo lường đi trước nợ giá trị — và Cycle 1 chính là
một nợ giá trị đội lốt refactor.

---

## 4. ⚠ Khoảng trống LỚN NHẤT: lớp **L4 chưa từng được truy**

`rc-L4.json` **không tồn tại** — agent chết vì lỗi API giữa chừng, và refuter cũng không ra verdict.
Mọi thực thể L4 trong bản đồ (`B2`, `D14`, `D20`, `A7`) đến từ người **đọc-nốt**, không từ một vòng truy
có hệ thống.

**Và nó nằm ĐÚNG trên kênh đang ship:** `B2` = `world.py:475-477` tiêu slot **trước** `:495` rút coin
adherence ⇒ đo 3 seed: **đốt 51,3% / 43,4% / 46,8%** slot gán. Ghép với `cap_left = 1` ở **96%+** ô: một
lượt đốt = **xoá trắng** ngân sách lời khuyên của ô đó trong bucket đó.

⇒ **Đề nghị: chạy lại riêng agent L4** trước khi chốt hàng đợi. Rẻ (1 agent) và nó phủ đúng chỗ đắt nhất.

---

## 5. Bản đồ bắt được **hai cycle NO-OP** suýt lọt vào hàng đợi của tôi

- **`E-S4-3` (TTL cho assignment)** — **đã bị bác 2026-08-07**: **0/179** lượt vượt biên bucket, và
  `market_state.py:162-167` **cache theo bucket** ⇒ re-validate đọc lại **y nguyên ảnh cũ** ⇒ bản vá
  **bất động ở 100% lượt**. `mm-08` viết **trước** đính chính nên tái phát nguyên văn.
- **`E-S4-2` (ngân sách outflow)** — **gần-NO-OP**: ca `eff==slots` chỉ **7,7–12,9%**; ca thống trị là
  `slots==0` (**34–42%**), ở đó ngân sách **không ràng buộc gì**. Nguyên nhân thật là `B1`.

⇒ Đây là lý do vòng phản biện đáng giá: **hai cycle đã có thể vào hàng đợi và tiêu công sức cho Δ = 0**.

---

## 6. CẦN CƯỜNG QUYẾT (không xếp vào cycle — nguyên tắc iv)

| # | Câu hỏi | Dữ kiện để quyết |
| --- | --- | --- |
| **Q-A** | **Mở lại ĐA-07** để đo `shift_plan` bằng solver đã sửa? | Bằng chứng cũ sinh từ DP **không nhìn thấy mốc thưởng** (§2.1). Đo lại có thể **củng cố** ĐA-07 bằng bằng chứng sạch — đó cũng là kết quả tốt |
| **Q-B** | **S5/S6/S8 + `AdvisorPipeline`**: khai tử hay nối vào stack? | S5/S8: sim **không có** cơ chế khoán tuần/clawback ⇒ **ĐA-08 KHÔNG chạy được** ⇒ phải tuyên bố **KHÔNG THỂ KIỂM**. S6: world **đã có** mission ⇒ đo được **ngay**, nhưng phải sửa cost model trước |
| **Q-C** | **Cycle 3 dịch baseline**: đo lại arm E hay ghi nợ có nhãn? | Nối đúng `demand.trip_km_median` làm lệch định giá **20,2%** (cận dưới) ⇒ mọi baseline E-series đo với `shift_plan` bật bị dịch |
| **Q-D** | *"Thời gian chờ/đổi pin có tính là nghỉ phục hồi?"* | **CHÍNH SÁCH, không tự quyết** — nới cổng nghỉ là **làm YẾU lan can một chiều** ⇒ phải qua `policy_locks` + duyệt |
| **Q-E** | **Q-07** (đã có số n=100) · **V-32** blocking · V-31 · ĐA-08 amendment · ~27 mục V- | Gom ở [`CAN-CUONG-DUYET-2026-08-06.md`](CAN-CUONG-DUYET-2026-08-06.md) |

---

## 7. Cảnh báo trung thực về chính bản plan này

1. **Mọi con số SIM trong bản đồ là agent đo, không phải tôi đo.** Tôi tự kiểm 6 vùng
   (`00-TU-KIEM-cua-toi.md`); người vẽ bản đồ tự kiểm 12 vùng. Phần còn lại là **AG** — chưa kiểm chéo.
2. **`file:line` phân rã rất nhanh** — `mm-09` bắt `from_l1r.py` lệch **~+20 dòng** do một commit **cùng
   ngày audit**. ⇒ Khi thi công phải **neo lại bằng nội dung** (tên hàm / literal), không neo bằng số dòng.
3. **Nhiều số then chốt mới có 3 seed** (87,6–88,2% `slots=0`; 43–51% đốt slot; 32,2–44,4% mover) ⇒
   **đủ để quyết ĐO TIẾP, không đủ để quyết SHIP.**
4. **Chưa ai quét `ui/web` (JS) và `ui/driver_app` (Dart)** bằng AST ⇒ bức tranh đường sản phẩm **còn
   thiếu một mảng**, và nếu có thực thể ở đó thì nó **làm MẠNH LÊN** cơ chế (2), không làm yếu đi.
5. **Chưa ai chạy full suite** trong vòng này ⇒ **không phát biểu nào ở đây dựa trên trạng thái suite**.
   ⚠ `ui/backend/tests` đếm **205** trong khi `CLAUDE.md` ghi **201** — **stale lần nữa**, chênh 4 test
   **chưa ai điều tra**.
6. **Con số `549 ca / 17,58 triệu đ` (A1) đã sập bẫy ngay trong vòng đó** (lượt quét đầu ra 1.079 ca /
   36,3 triệu, **sai ~2×**) ⇒ **phải đo lại trong Cycle 5**, không trích thẳng.
7. **"Lớp thứ 7" (PROXY SAI ĐẠI LƯỢNG)** — **ba artifact độc lập** cùng đề nghị, phủ 4/6, 4/9, 3/8 phần
   *"không thuộc lớp nào"*. Nếu đúng thì bảng 6 lớp **đang bỏ sót khuôn lớn nhất**. **Chưa ai truy nó
   grep-driven** ⇒ ghi là **giả thuyết**, không vào kế hoạch.
