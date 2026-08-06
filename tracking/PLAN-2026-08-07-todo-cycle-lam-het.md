# PLAN 2026-08-07 — todo cycle **làm hết**, xếp theo **bán kính ảnh hưởng thật**

> Cường: *"lên plan để vào todo cycle làm hết, phải nghiên cứu, brainstorm, đọc kỹ tài liệu, công thức,
> logic, code tìm root cause thật trước khi trình plan, nhớ phải docs"*.
>
> Bản này **thay thế thứ tự** của `PLAN-2026-08-06-cycles-chi-tiet.md` (nội dung kỹ thuật từng cycle ở đó
> vẫn dùng được). Lý do thay: xem §1 — thứ tự cũ xếp theo *"nợ nào tìm ra trước"*, và điều đó **sai**.
>
> Nghiên cứu nền: `research/audit/2026-08-07-root-cause-classes/00-TU-KIEM-cua-toi.md` (5 điều tôi **tự
> kiểm**, có `file:line` + git + artifact) và `00-BAN-DO-LOP.md` (audit 6 lớp nguyên nhân — 12 agent).

---

## 1. ⭐ Điều làm ĐẢO thứ tự — và nó là kết quả nghiên cứu, không phải ý kiến

Tôi mở `configs/pilot_dongda.yaml:330-343` ra đọc (thay vì nhớ):

> **6/6 kênh advisor đang TẮT.** `shift_plan` · `accept_lift` · `shift_extend` · `rest_window` ·
> `swap_early` · `station_choice` = `false`. Kênh **duy nhất** được duyệt bật: `positioning_overrides:
> wait_only`. Và `B6-PARITY`: sản phẩm chạy **đúng 1/9 solver** (S1).

⇒ Phần lớn nợ tôi đào ra hai ngày qua (`S2-1..S2-6`, `R-1..R-7`, `D-E4-01/02/06`) nằm trong **kênh đang
ngủ** ⇒ **bán kính ảnh hưởng hôm nay = 0**. Sửa chúng trước là sửa thứ không ai chạm tới.

Nhưng **không** vứt chúng, vì có một sắc thái quan trọng: `channels: false` là **mặc định ship**, còn
run nghiên cứu **bật từng kênh** qua override. Nên lỗi trong kênh ngủ **vẫn làm hỏng phép đo** khi ai
đó bật lên để nghiên cứu. Đó **chính xác là chuyện đã xảy ra** (§2). Vậy chúng là **nợ đo lường**, không
phải nợ sản phẩm — và xếp theo đúng loại đó.

### Thứ tự thi công (nguyên tắc, áp cho mọi cycle bên dưới)

1. **Đường sản phẩm** — cái tài xế thật nhìn thấy. Sai ở đây là sai với người dùng.
2. **Kênh sim đang SỐNG** — positioning/S4. Cái duy nhất đang tạo ra Δ được trích dẫn.
3. **Độ tin của PHÉP ĐO** — cổng, thước, mẫu số. Chúng **gác mọi quyết định tương lai**, kể cả quyết
   định mở lại kênh ngủ. Nợ đo lường đi **trước** nợ giá trị (luật cũ, giữ nguyên).
4. **Kênh ngủ** — chỉ đụng khi có lý do mở lại, và mở lại thì **đo lại**, không sửa mò.

---

## 2. ⭐ Root cause NẶNG NHẤT tìm được hôm nay: một bản án dựa trên solver hỏng

**Đo được bằng git** (`00-TU-KIEM-cua-toi.md` §1):

| việc | commit | ngày |
| --- | --- | --- |
| ĐA-07 tắt `shift_plan` | `5a44cbb` | **2026-07-28** |
| E5 đo lại, củng cố ĐA-07 | — | 2026-07-29 |
| sửa `points_band_size` 15 → 5 (`ADV-01`) | `bec2671` | **2026-08-06** |

Ở band 15, `add_pts // 15 = 0` với mọi giờ thường ⇒ **mốc thưởng ngày không bao giờ vào giá trị Bellman**
⇒ S2 lập lịch **như thể không có thưởng**. Cả hai vế bằng chứng của ĐA-07 (*"không giá trị"* và
*"còn có hại"*) đều sinh ra từ solver đó.

**⚠ Tôi KHÔNG nói "S2 thật ra có giá trị".** Rất có thể nó vẫn vô dụng. Khẳng định hẹp và chắc:
**chưa ai đo `shift_plan` bằng solver đã sửa**, và **chưa ai ghi nghĩa vụ đo lại** (`D-E4-01` quy nguyên
nhân cho world zero-cost, không quy cho lỗi band — hai cách giải thích **cạnh tranh và tách được**).

---

## 3. Bảng cycle

Mỗi cycle: **root cause đã chứng minh chưa** · **test đỏ-trước** · **acceptance bằng SỐ** · **rủi ro đảo
kết luận** · **phụ thuộc**. Cycle nào root cause chưa chứng minh thì bước 1 của nó **là chứng minh**,
không phải sửa.

### 🔴 TIER 1 — đường sản phẩm (tài xế thật nhìn thấy)

| # | Cycle | Root cause | Trạng thái |
| --- | --- | --- | --- |
| **C1** | `D-M3-17` — UI **tự tính phạm vi pin** khác engine | ✅ đã chứng minh (smoke e2e, `f38ff25`) | **READY** |
| **C2** | `D-ADV-04b` — vế còn lại của mẫu số S1 trên đường sản phẩm | ✅ B0 đã sửa vế chính, 4b là phần chừa | **READY** (chờ V-32 để không đụng cùng card) |

**C1 — acceptance:** UI **không còn công thức pin riêng**; nó đọc đúng đại lượng engine phát ra. Test
đỏ-trước: một `(driver, soc, fleet)` mà hai công thức lệch ⇒ assert UI == engine. Không đổi engine.
**Rủi ro:** engine có thể mới là cái sai — phải đọc `range_km` ở `behavior.py:129-131` **trước**, và nếu
engine sai thì đây thành cycle sửa engine, không phải sửa UI. **Bắt buộc visual gate** (card F0/F1).

### 🟠 TIER 2 — kênh sim đang SỐNG (positioning/S4)

| # | Cycle | Root cause | Trạng thái |
| --- | --- | --- | --- |
| **C3** | `D-ADV-01` — stagger của S4 | ⏳ **chờ phản biện** (agent mm-08 đang đọc) | **BLOCKED-RESEARCH** |

Đây là kênh **duy nhất** đang tạo ra con số `+6.016đ` được trích khắp nơi. Bất kỳ lỗi nào ở đây làm
**sai con số đang được dùng để biện minh cho cả sản phẩm**. Ưu tiên cao **dù** chưa chứng minh xong —
nhưng bước đầu là **chứng minh**, không sửa.

### 🟡 TIER 3 — độ tin của phép đo (gác mọi quyết định sau)

| # | Cycle | Root cause | Trạng thái |
| --- | --- | --- | --- |
| **C4** | **Lan can `soc_low` mồ côi + cổng aliveness mù** | ✅ **tự kiểm xong** | **READY** |
| **C5** | `A2` ở n=100 + **HHI cung theo ô** | ✅ nợ đo đã biết | **READY** |
| **C6** | `D-M3-20` (rút RNG trước cổng) · `D-M3-21` | ✅ pb-02 đo `A==B_fix` 60/60 | **chờ Cường duyệt plan** |

**C4 — chi tiết (root cause đã chứng minh đầy đủ):**

- **Sự thật:** `soc_low` **bất khả đạt theo cấu trúc**. `world.py:1037` chỉ vào nhánh khi `action==REST`;
  `behavior.py:151` đã trả `GO_SWAP` với **cùng ngưỡng** mà `world.py:1040` truyền xuống; `advice_bridge.py:890`
  kiểm lại đúng ngưỡng đó ⇒ **rỗng**. Đo: `veto_soc_low_n = 0,0` cả hai arm, 30 seed
  (`research/audit/2026-08-06-e1b/ladder-truoc.json`).
- **Vì sao thành ra thế:** `D-M3-04-FIX` xoá hai nhánh `GO_SWAP/GO_CHARGE` (đúng — chúng là code chết),
  và **hệ quả không ai ghi** là lan can đi kèm chúng thành mồ côi.
- **Vì sao cổng không bắt:** `sim_metrics.py:537` đòi `va >= RAIL_ALIVE_MIN_N and vb == 0` — nó bắt
  *"rail sống ở A, chết ở B"*, **mù** với rail **chưa từng sống** (`va = 0`).
- **Mức độ — nói cho đúng:** tính chất an toàn *"pin thấp thì không hoãn nghỉ"* **vẫn đúng** (chặn ở
  thượng nguồn). Sai là **báo cáo**: tầng 5 tự trình bày như **3 lan can**, thực tế **1** bắn được.
- **Khuôn sửa đã có sẵn trong repo:** `defer_cap` cũng trơ, nhưng **có chủ ý** và có test khai-trơ kèm
  điều kiện mở lại (`tests/test_rest_rails_guardrail.py:58-62`, *"ĐỎ = TIN TỐT"*). Làm y hệt cho `soc_low`.

**C4 — việc:**
1. Test **đỏ-trước**: `test_soc_low_TRO_theo_cau_truc` — assert `veto_soc_low_n == 0` **kèm** lý do cấu
   trúc, và một test thứ hai chứng minh **vì sao** (dựng actor `soc <= ngưỡng` ⇒ `choose_idle_action`
   **không** trả REST).
2. **Cổng chặn tái diễn** (đây mới là giá trị thật): mở rộng `health_guardrail_flags` để tố giác rail
   **chết ở CẢ HAI arm** — nhưng **không** làm nó ồn: rail đã khai-trơ tường minh (allowlist có lý do)
   thì im, rail **chưa khai** mà `va == vb == 0` thì **bắn**. Không có cổng này thì lớp mồ côi tái sinh.
3. Ghi `veto_fired_n` là tổng của **những rail sống** + kèm số rail đang trơ, để không ai đọc `55` mà
   tưởng ba lan can cùng canh.

**C4 — acceptance:** cổng mới **ĐỎ** trên `soc_low` trước khi khai trơ, **XANH** sau khi khai; và **ĐỎ**
nếu ai đó xoá `fatigued`. Sim **fingerprint IDENTICAL 5 seed** (chỉ thêm test + hàm cổng, 0 đổi dynamics).

**C5 — acceptance:** `A2` (đội 74) ở **n=100 paired CRN** + **HHI cung theo ô** cho **cả** Q-07 A0/A1.
Chỉ khi có hai số này thì *"biên đánh đổi"* của `UPDATE-176` §3(c) mới được gọi là **số chốt** thay vì
**hướng**. ⚠ **Cấm** nói *"equity tốt lên toàn diện"* cho tới khi có HHI — hiện chỉ có Gini payout.

### 🟢 TIER 4 — kênh ngủ: **đo lại**, không sửa mò

| # | Cycle | Nội dung | Trạng thái |
| --- | --- | --- | --- |
| **C7** | ⭐ **Đo lại `shift_plan` bằng solver đã sửa** | §2 — bản án ĐA-07 dựa trên DP mù thưởng | **cần Cường duyệt: có mở lại ĐA-07 không** |
| — | `S2-2` sàn điểm còn dư `add_pts % 5` | DERIVED, chưa đo | **đi kèm C7**, không cycle riêng |
| — | `R-1`, `R-3..R-7`, `D-ADV-06`, `D-E4-01/02/06` | kênh ngủ | **DEFERRED** + điều kiện mở lại |

**C7 — vì sao cần Cường duyệt trước:** mở lại một quyết định **đã duyệt** là việc của Cường, không phải
của tôi. Tôi chỉ trình bằng chứng rằng **bằng chứng cũ đã hỏng**. Nếu Cường đồng ý, C7 chạy:
`shift_plan on/off` × n=100 seed **tươi** (không dùng lại cửa sổ 1000s/3000s), advisor các kênh khác giữ
nguyên, chấm bằng **ĐA-08 nguyên văn** (như `cham_da08_station_choice.py` đã làm cho E-01).
**Falsifier:** nếu Δ vẫn ns thì ĐA-07 **được củng cố bằng bằng chứng sạch** — đó cũng là kết quả tốt.

**⚠ Rủi ro phải nói trước:** giữa 28/07 và 06/08 có hàng chục fix khác ⇒ C7 là phép đo **MỚI**, không
phải so thẳng với số cũ. Phải chạy **cả hai arm tươi**.

### ⬛ TIER 5 — chưa chứng minh root cause, bước đầu là CHỨNG MINH

`B1` shortlist (⇐ Q-07) · `B2` cooldown-sau-gán · `B3` **1/4 hiệu ứng sốt ruột là no-op** (đã sửa cách
phát biểu — xem dưới) · `B4` sổ thời gian đội hở +3,41% · `B5` slider chết · `D-SIM-K3` keyed RNG ·
`D-SIM-K6/K8` · `REVIEW-092-4` cầu co giãn · `D-SIM-01` mở vùng.

**⚠ Đính chính hồ sơ `B3`** (tôi tự kiểm, `00-TU-KIEM-cua-toi.md` §5): hồ sơ cũ ghi *"bước sốt-ruột là
NO-OP"* — **quá rộng**. Đúng là **1 trong 4** hiệu ứng no-op (nới vành 1→3, vì `_neighbors` dùng đĩa
`grid_disk` còn niềm tin chỉ phủ `grid_disk(cell, 2)` ⇒ ô vành 3 đọc `0.0`). Ba hiệu ứng kia (`bar`
1,25→1,05 · `p_move` 0,5→0,9 · `give_up` bỏ hẳn phép so) **hoạt động**. ⇒ **Fix chỉ nới vành sẽ vẫn
no-op**; phải sửa **bán kính niềm tin** cùng lúc. Đây là ví dụ đúng của việc *"cách phát biểu sai dẫn
tới fix sai chỗ"*.

---

## 4. Cái **KHÔNG** làm (ghi để không ai đào lại)

- **Không** sửa nợ trong kênh ngủ theo kiểu từng cái một — chúng vào `DEFERRED` kèm điều kiện mở lại.
  Ngoại lệ duy nhất: khi chúng làm **hỏng một phép đo** ta sắp chạy (đó là C7).
- **Không** đổi `accept_base` P7, **không** đổi `candidate_ring_k_max`, **không** đổi đội 90→74 — cả ba
  là **quyết định của Cường** (Q-07), không phải việc thi công.
- **Không** nới dung sai test để qua cổng — chính config gọi đó là che khuyết tật.
- **Không** đưa sức khoẻ vào hàm mục tiêu (spec §1.2b) kể cả khi nó làm Δ đẹp hơn.

## 5. Cảnh báo trung thực về chính bản plan này

- **Tier 2 (C3) chưa có root cause** — nó ở tier cao vì **hậu quả** cao, không vì bằng chứng chắc. Bước
  đầu của nó là chứng minh, và nếu phản biện bác thì cycle **huỷ**, không "sửa cho có".
- **§2 là phát hiện thuận lợi cho luận điểm của tôi** (rằng còn việc thật phải làm) ⇒ đúng loại phải
  soi kỹ nhất (`verify-favourable-claims-hardest`). Tôi đã hạ nó xuống mức khẳng định hẹp nhất mà bằng
  chứng đỡ được: *"chưa ai đo lại"*, **không phải** *"S2 có giá trị"*.
- **6 lớp nguyên nhân** đang được 12 agent truy và **1 agent được lệnh cố BÁC**. Nếu một lớp bị bác thì
  phần "cổng chặn tái diễn" của lớp đó **rút khỏi plan** — cổng cho một lớp không tồn tại là chi phí
  không có lợi ích.
- Bản này **chưa** xếp lịch cho ~27 mục `V-` và `Q-03/04/09/10/13` đang chờ Cường — chúng ở
  `tracking/CAN-CUONG-DUYET-2026-08-06.md`, không phải việc thi công.
