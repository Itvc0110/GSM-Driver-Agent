# PLAN CHI TIẾT TỪNG CYCLE — cải tiến sim + advisor (Cường yêu cầu 2026-08-06)

> **Chỉ thị Cường (2026-08-06, sau khi chuyển hẳn sang opus):** *"ngay khi kết quả chạy nền về thì cải
> tiến tiếp, phải lên plan rõ ràng trước từng cải tiến, phải docs rõ ràng, có kết quả thật, tìm root
> cause nếu có vấn đề trước khi fix, phải lên plan chi tiết trước từng cycle."*
>
> File này là **plan chi tiết** cho từng cycle. Bản đồ ưu tiên 4 sóng vẫn ở
> `PLAN-2026-08-06-lich-trinh-cai-thien.md`; la bàn quyết định ở `BOOTSTRAP-SESSION.md` §5b.

## 0. LUẬT CHUNG cho mọi cycle dưới đây (không cycle nào được bỏ)

1. **Không sửa trước khi phản biện xong.** 5 nợ mới (`D-M3-20`, `D-M3-21`, `D-ADV-01`, `D-ADV-02`,
   `D-ADV-03`) hiện là *"một mình tôi đồng ý với tôi"*. Workflow phản biện đang chạy (7 refuter, mỗi nợ
   một góc soi, **được lệnh cố BÁC**). **Nợ nào bị REFUTED thì cycle của nó bị HUỶ**, không "sửa cho
   chắc".
2. **Thứ tự bất di dịch:** nợ chạm **ĐỘ TIN của phép đo** xếp trước nợ chạm **giá trị**; nợ chạm giá trị
   xếp trước **tính năng mới**. Lý do: sửa giá trị trên thước bẩn thì không đọc được kết quả.
3. **Mỗi cycle phải có:** (a) root cause **đã chứng minh** (không phải nghi); (b) **test đỏ-trước** thật
   sự đỏ trước khi sửa; (c) **acceptance bằng SỐ** chốt trước khi chạy; (d) danh sách **rủi ro đảo kết
   luận**; (e) UPDATE-### riêng + nhắc PENDING-REVIEW.
4. **Đổi hành vi sim ⇒ vào plan mode xin duyệt trước khi implement** (CLAUDE.md §4b). File này là *plan
   của chương trình*, không thay thế bước duyệt từng cycle.
5. **Kênh ĐANG BẬT (`positioning`) ⇒ mọi thay đổi phải regate n=100 theo ĐA-08 đủ 9 dòng.**
6. **Sức khoẻ KHÔNG vào objective** (spec §1.2b) — không cycle nào được nới điều này.
7. **Số nào định trích thì mở artifact gốc**; hai số khác **cửa sổ seed** không được đứng cùng bảng mà
   không nhãn (bài học UPDATE-164 — lỗi tôi vừa mắc).

---

## CYCLE A — `D-M3-20`: làm SẠCH arm đối chứng của `rest_window`

**Điều kiện khởi động:** phản biện `pb-01` (chuỗi gọi) **và** `pb-02` (hậu quả) đều không REFUTED.
Nếu `pb-02` cho thấy đây chỉ là trường hợp riêng của `D-SIM-K3` ⇒ **gộp vào Cycle E**, không làm riêng.

| Mục | Nội dung |
| --- | --- |
| **Vì sao trước tiên** | Đây là **thước**, không phải giá trị: nó làm bẩn arm đối chứng ⇒ mọi Δ của `rest_window` sau 2026-08-05 không đọc được. Và nó là nợ **tôi tự tạo ra** trong cycle D-M3-04-FIX của chính mình rồi báo "acceptance passed" cho Cường |
| **Root cause (đã chứng minh, tôi tự đọc code)** | `advice_bridge.py:916` gọi `alt_action_fn` **trước** cadence `:922` và coin `:933` → `world.py:1041` truyền `consider_relocate(..., self.rng, ...)` → `behavior.py:228` rút `rng.random()`. Arm A: cổng cờ `:843` ⇒ return `no_window` ở `:907` **trước** dòng 916 ⇒ 0 draw |
| **Test đỏ-trước** | Kênh **BẬT** + ép **mọi coin từ chối** (monkeypatch `coin_follows` → False) ⇒ `fingerprint_actors` phải **IDENTICAL** arm A. Test này phải **ĐỎ** trên code hiện tại. Thêm mũi 2: cadence nén (đặt `min_gap` lớn) ⇒ cũng phải IDENTICAL |
| **Fix hẹp (2 phương án, chọn sau khi đọc `pb-01`)** | (i) **Tách hai pha**: "có ô tốt hơn không" (tất định, 0 draw — dùng cho gate `no_alt_action`) khỏi "có đi không" (`p_move`, rút **sau** coin); (ii) rút `p_move` của đường-advisor bằng **keyed hash** như `adherence_coin`. Ưu tiên (i) vì không thêm nguồn ngẫu nhiên mới |
| **Acceptance (số)** | 1. Hai test đỏ-trước **XANH**. 2. Kênh **TẮT** ⇒ fingerprint IDENTICAL arm A trên **5 seed** (bất biến cũ, không được vỡ). 3. **Đo lại** acceptance D-M3-04-FIX trên **30 seed** cùng cửa sổ seed cũ; báo cả **hai** bộ số (trước/sau) — nếu kết luận D-M3-04-FIX **đổi**, phải ghi CORRECTED lên UPDATE tương ứng. 4. Cả hai suite xanh như baseline (2F của Khánh) |
| **Rủi ro đảo kết luận** | (a) `pb-02` có thể chứng minh mỗi actor có stream riêng ⇒ một draw thêm **không lan** ⇒ nợ sập; (b) fix (i) đổi thứ tự draw ⇒ **arm B cũng đổi** ⇒ không so được trực tiếp với số cũ (phải nói rõ, không lặng lẽ thay số); (c) `no_alt_action` là **mẫu số adherence** — đổi cách tính nó có thể đổi tỷ lệ nghe, phải kiểm cổng `D-M3-10` không bắn oan |
| **Chi phí ước** | Nhỏ-vừa (1 hàm + 2 test + 1 lần đo 30 seed ~10′ máy) |

---

## CYCLE B — `D-ADV-02`: `shift_extend` phải biết CỬA SỔ ĐIỂM

**Điều kiện khởi động:** `pb-03` (tần suất) cho tần suất **> 0 đáng kể** *và* `pb-04` (cách sửa) không
bác đường S1. Nếu `pb-03` đo ra ~0 lượt ⇒ **hạ severity, chuyển sang chỉ ghi comment cảnh báo**, không
sửa (tránh sửa cái không bao giờ chạy). Nếu `pb-04` phát hiện **S1 cũng dùng rate trung bình** ⇒ phải
**thiết kế lại** cách ước điểm, cycle phình ⇒ tách plan riêng.

| Mục | Nội dung |
| --- | --- |
| **Root cause (đã chứng minh, 3 nguồn)** | `advice_bridge.py:1122-1126` dùng `rate = points/online_h` (trung bình cả ngày, trộn giờ peak 10đ) → `need_min = gap/rate×60`; `policy.py:86-92` trả **0 điểm** ngoài `point_window_hours = [6..21]` (`configs:254`). Hai agent độc lập + tôi kiểm code |
| **Test đỏ-trước** | Dựng actor `shift_end = 21h30`, còn `gap_points > 0`, `rate > 0` ⇒ hàm hiện tại trả `add > 0` (khuyên kéo); test đòi **im lặng** với reason `points_window_closed`. Mũi 2: actor kết ca **19h**, kéo tới 21h30 ⇒ `need_min` phải tính **chỉ phần trong khung**, lớn hơn số cũ |
| **Fix** | Thay `rate` phẳng bằng đường đi từng giờ trên `[shift_end, shift_end + extend_max]`: dùng **`S1 bonus_feasibility`** (đã xử đúng 0-điểm-ngoài-khung từ UPDATE-065). Không nghiệm ⇒ **im lặng** (R-08), reason mới typed |
| **Acceptance (số)** | 1. Hai test đỏ-trước xanh. 2. Kênh TẮT ⇒ fingerprint IDENTICAL (5 seed). 3. Đo kênh BẬT **30 seed**: số lượt nói **giảm** (cắt đúng nhánh vô ích) và **không lượt nào** có cửa sổ kéo hoàn toàn sau 21h — đếm bằng event log. 4. So Δ trước/sau, **không claim tiền** (chưa prereg) |
| **Rủi ro** | (a) Kênh có thể **câm hẳn** — đúng bài học `swap_early` gate chặt thành trơ; nếu câm, ghi trung thực "kênh này chỉ có nghĩa với ca kết trước ~19h" thay vì nới gate; (b) `D-SIM-09` hai nguồn sự thật nếu vừa dùng `next_tier_gap` vừa dùng S1 — phải chọn MỘT nguồn cho gap |
| **Chi phí** | Nhỏ |

---

## CYCLE C — `D-M3-21`: tách `Δgross` khỏi `Δpayout` (KHÔNG đổi hành vi khuyên)

**Điều kiện khởi động:** `pb-05` xác nhận tần suất bind **> 0 đáng kể**. Đây là cycle **đo lường**, an
toàn nhất trong danh sách (không đổi một dòng hành vi nào) ⇒ có thể chạy **song song** Cycle A/B.

| Mục | Nội dung |
| --- | --- |
| **Root cause (đồng nhất thức, đã kiểm)** | `world.py:575-578`: `topup = (sàn − gross) × driver_share` cộng vào payout ⇒ `payout ≡ 0,75 × 350.000 = 262.500đ` **hằng** khi `gross < sàn` ⇒ **∂payout/∂gross = 0**. Mọi P4 (tenure ∈ [5,60)) trong cửa sổ bảo lãnh; điều kiện kèm `online ≥ 6h` |
| **Vì sao phải sửa BÁO CÁO** | Guard **1b ĐA-08** cho P4 hiện **không có power** (không thể hại cũng không thể lợi) ⇒ mọi bảng per-archetype tôi đã báo (kể cả `+6.016đ`) đang đọc P4 sai bản chất |
| **Việc làm** | `sim_metrics`: thêm `gross_mean_{arch}` cạnh `payout_mean_{arch}`; cờ `policy_absorbed` cho ngày-tài-xế có `newbie_guarantee_topup > 0` **hoặc** `day_bonus = 0`-vì-acceptance; dashboard/A-B hiển thị **cả hai cột** với chú giải bằng lời (không mã hiệu — bản cuối cho stakeholder) |
| **Acceptance (số)** | 1. Test: dựng cohort có 1 tài xế bind ⇒ `policy_absorbed` đếm đúng 1; `gross_mean` và `payout_mean` **khác nhau** đúng lượng topup. 2. Chạy lại **artifact positioning n=100 đã có** qua thước mới (không cần chạy sim mới nếu event log còn) và trả lời: **`Δgross(P4) > 0` SIG hay không?** 3. Fingerprint IDENTICAL (chỉ thêm metric, không đổi hành vi) |
| **Rủi ro** | (a) `pb-05` có thể chỉ ra `day_bonus`/mission **nằm ngoài** đồng nhất thức ⇒ P4 vẫn có đường hưởng lợi ⇒ phải sửa cách phát biểu, không phải sửa metric; (b) nếu event log cũ không đủ trường thì phải chạy lại n=100 (~10′) |
| **Chi phí** | Nhỏ-vừa |

---

## CYCLE D — `D-ADV-03`: kênh MỚI "positioning chặng về" (prereg trước, code sau)

**Điều kiện khởi động:** `pb-07` (*"vì sao nó sẽ thất bại"*) **không** tìm ra cơ chế chặn quyết định.
⚠ Cycle này **không được bắt đầu bằng code**. Bắt đầu bằng **prereg**, và chỉ khi Cường duyệt.

| Mục | Nội dung |
| --- | --- |
| **Cơ hội (đã kiểm)** | `world.py:799-811`: sau cuốc trả ngoài lõi, xe về **ô lõi gần nhất, mù cầu**; là relocate THẬT (tốn phút + SOC, vào `empty_min`, `enroute_cell` đã tự vào sổ cung-đang-tới). Planner vị trí **không thấy** vì actor đang `ENROUTE` (`world.py:421` chỉ quét IDLE). Kích hoạt **65,3% cuốc**, ~**539 km rỗng/ngày** |
| **Vì sao khác `station_choice` (vừa NO-GO)** | Không **tạo** chuyến đi để tiết kiệm phút — chỉ **đổi hướng km rỗng bắt buộc** ⇒ chi phí biên ≈ 0; và thuộc **họ vị trí**, họ duy nhất dương SIG |
| **PREREG (chốt TRƯỚC khi chạy)** | Giả thuyết: `Δpayout_mean_all > 0` CI loại 0 ở n=100 **và** 0/7 archetype âm-SIG (ĐA-08 1a+1b). Cơ chế phải thấy: **`empty_min` KHÔNG tăng > δ** (nếu tăng nhiều ⇒ đang mua vị trí bằng km rỗng, veto 8(b) sẽ bắt) và **`expired_n` giảm**. Falsifier: nếu `expired_n` không giảm mà payout tăng ⇒ nghi tái phân phối, phải phân rã trước khi tin |
| **Test đỏ-trước** | 1. Cờ TẮT ⇒ fingerprint IDENTICAL (bất biến "tắt được về baseline"). 2. Cờ BẬT + world dựng tay: ô lõi gần nhất `capacity_left = 0`, ô lõi thứ nhì `capacity_left > 0` trong `δ` ⇒ đích phải là ô **thứ nhì**. 3. Không ô nào còn trần ⇒ **rơi về bản năng** (ô gần nhất) |
| **Acceptance** | ĐA-08 đủ **9 dòng** ở **n=100**, chuẩn y như kênh mới; kèm **guard herding**: nếu `supply_cell_hhi` **tăng** SIG ⇒ phải nối sổ trừ-trần cho đường này trước khi xin bật |
| **Rủi ro (ghi trước, chờ `pb-07` xác nhận)** | (a) đích xa hơn ⇒ **km rỗng tăng**, đúng cái veto 8(b) canh; (b) ô `capacity_left > 0` có thể là ô **λ thấp** (do `slots = ⌊λ/1.5⌋` = 0 ở nơi khác) ⇒ đẩy xe vào ô chết; (c) **herding**: mọi xe trả khách cùng bucket thấy cùng bảng xếp hạng; (d) nếu **đơn chết phần lớn NGOÀI lõi** thì đưa xe về lõi "có cầu" vẫn không gặp đơn chết |
| **Chi phí** | Vừa-lớn (kênh mới + prereg + n=100) |

---

## CYCLE E — `D-SIM-K3`: keyed RNG (việc lớn, nền của mọi phép đo)

**Điều kiện khởi động:** sau Cycle A (hoặc **gộp** Cycle A vào đây nếu `pb-02` cho thấy A chỉ là trường
hợp riêng). Đây là **đòn bẩy cao nhất toàn repo** và là **điều kiện reopen (a) của `D-E4-06`**.

| Mục | Nội dung |
| --- | --- |
| **Vấn đề** | Mọi Δ A/B hiện lẫn **random-stream divergence**: đổi một hành vi ⇒ dịch dòng ngẫu nhiên của **cả 90 tài xế**, nên Δ = hiệu ứng thật **+** nhiễu trôi. Đây là lý do "quan sát phụ thuộc cửa sổ seed" (rest +281 @1000s vs +19,6 ns @7000s) |
| **Hướng** | `rng(seed, actor_id, purpose)` — mỗi (tài xế × mục đích) một dòng độc lập, hoặc **event tape** phát trước. Phải quyết định trong plan riêng: keyed-hash rẻ hơn, tape trung thực hơn |
| **Test đỏ-trước** | Đổi **một** quyết định của **một** tài xế ⇒ mọi tài xế **khác** phải giữ fingerprint **IDENTICAL** (hiện tại chắc chắn ĐỎ) |
| **Acceptance** | 1. Test trên xanh. 2. **Đo lại** hai quan sát phụ-thuộc-cửa-sổ-seed (rest của `station_choice` ở 1000s và 7000s) — kỳ vọng: hai cửa sổ **hội tụ**. 3. Đo lại `D-E4-06` (`station_choice` n=100) — nếu 1a/1b **đổi verdict** thì reopen theo điều kiện đã ghi |
| **Rủi ro** | Đổi nền ngẫu nhiên ⇒ **mọi số cũ không so trực tiếp được**; phải giữ đường cũ sau cờ để đối chiếu, và **không lặng lẽ** thay số trong tài liệu cũ (dùng banner CORRECTED) |
| **Chi phí** | **Lớn** — cycle riêng, cần plan chi tiết riêng trước khi động |

---

## CYCLE F — nợ từ rc-03/rc-04 (chưa biết nội dung — điền khi verdict về)

Đang chạy: probe chồng lấn **idle × đơn chết** theo cell/giờ ⇒ phân xử H1 (lệch pha giờ) / H2 (lệch vị
trí) / H3 (defect dispatcher). Hai ứng viên đã có hồ sơ, **chưa đo độ lớn**:

- **`BUG-DISPATCH-SHORTLIST`** — vòng lọc ứng viên **2,22 km** hẹp hơn bán kính ETA khả thi **3,14 km** ⇒
  loại **âm thầm** tài xế ở dải giữa. Tồn tại ở **cả hai arm** ⇒ sửa nó là **đổi nền**, phải re-baseline.
- **`D-SIM-K6`** — cooldown chào lại **10′ ≥ tuổi thọ đơn 10′** ⇒ một lần từ chối giết cặp vĩnh viễn.

⚠ Cả hai **chỉ được sửa sau khi rc-03 đo được độ lớn**; sửa nền mà chưa biết độ lớn là đúng cái Cường
cấm ("tìm root cause trước khi fix").

---

## Việc KHÔNG làm trong đợt này (để không ai đào lại)

- Bật lại `shift_plan` / `rest_window` / `station_choice` **mà không có prereg mới** — luật cũ còn hiệu lực
  (ĐA-07, Q-16, `D-E4-06`).
- Nới `SPAN_P90_RISE_TOL`, `POLICY_LOCKED`, hay đưa sức khoẻ vào objective.
- Đổi **ID nội bộ** của topic/kênh cho "dễ hiểu" — nhãn hiển thị đã có nguồn riêng (`channel_labels.py`).
- Sửa `count_supply` hai-sổ hoặc veto-khi-kênh-tắt — **thiết kế có test ghim** (ADV-09/ADV-06 đã soi).
- Sửa `BUG-DISPATCH-SHORTLIST` **trước** khi rc-03 đo độ lớn.
