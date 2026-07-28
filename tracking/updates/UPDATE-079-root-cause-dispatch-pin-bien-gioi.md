# UPDATE-079 — Root cause thật: dispatch · chi phí pin · biên giới cung–cầu (RESEARCH; fix đã hoàn tác)

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** research (3 hồ sơ). Fix thử nghiệm **đã hoàn tác** — xem §2.
- **TODO liên quan:** **T-045 a/b/c/d/e**, **T-046**; hồ sơ
  [`12`](../../research/audit/2026-07-27-current-state/12-root-cause-that-dispatch-pin-cho-don.md) ·
  [`13`](../../research/audit/2026-07-27-current-state/13-kiem-ke-bien-mau-loi-va-ke-hoach.md) ·
  [`14`](../../research/audit/2026-07-27-current-state/14-bien-gioi-cung-cau-va-tran-nang-luc.md)

## Tóm tắt

Cường bác hướng "thêm biến giá trị nghỉ" (*"không mô hình hoá được chính xác thì không nên tạo
biến"*) và yêu cầu truy root cause thật. Kết quả: **ba lỗ hổng đo được**, **một mẫu lỗi lặp 6 lần**,
và **hai câu hỏi** phải đưa lên Cường (Q-07, Q-08).

**⚠ UPDATE này KHÔNG còn chứa fix nào** — bản đầu đặt `candidate_ring_k_max` 6 → 12, **đã hoàn
tác** vì 2 test realism đỏ (xem §7). Fix thật cho dispatch nằm ở **UPDATE-080** (tầng 2 Hungarian).
UPDATE-079 vì vậy là **research thuần**: ba hồ sơ + hai câu hỏi chờ Cường.

## Chi tiết

### 1. MẪU LỖI LẶP LẠI — 6 lần trong hai phiên (hồ sơ `13` Phần 1)

*Sửa/thêm ở một tầng, tầng tiêu thụ không biết.* Cước 24.000 → `already_maxed` → `_khoan_sentence`
→ `bucket_min` → `actors.n` 74→90 → **`candidate_ring_k_max` vs `eta_max_min`**.

Đặc điểm chung: bản sửa **đúng**, test tầng đó **xanh**, **không có test ở tầng tiêu thụ**.
4 quy tắc + danh sách ứng viên nghi tiếp theo đã ghi vào **T-046**.

### 2. BUG-DISPATCH-SHORTLIST — TÌM RA, thử sửa, ĐÃ HOÀN TÁC

`match_batch` lấy ứng viên bằng `grid_disk(pickup, k_max)` **rồi mới** kiểm ETA. Đĩa hẹp hơn bán
kính ETA-khả-thi ⇒ loại âm thầm.

| | |
|---|---|
| bán kính khả thi xấu nhất | `11/60 × 30 (đêm) / 1,00 (factor OSRM min)` = **5,50 km** |
| đường kính vùng pilot | **4,47 km** ⇒ cần phủ `min(5,50; 4,47)` |
| `k_max = 6` (cũ) | phủ **2,22 km** ❌ |
| `k_max = 12` (mới) | phủ **4,45 km** ✅ — k=16/20 cho kết quả **y hệt** ⇒ 12 đã bão hoà |

**Đo, 3 seed**: served 0,750 → 0,789 · đơn hết hạn 238 → 195 · runtime ×1,8.

⛔ **NHƯNG ĐÃ HOÀN TÁC**: full suite cho **2 test realism đỏ** —
`test_accept_matches_archetype_base` (P7 realized 0,870 vs base 0,94) và `test_no_dead_hour`
(18h: 41% hết hạn). Đo kỹ 12 seed: **không có k nào** vừa cải thiện ghép đơn vừa giữ realism
(k6 −0,042 ✅ · k7 −0,053 ❌ · k8 −0,057 ❌). Cơ chế: đơn **mới được phục vụ** chính là đơn
**pickup xa** ⇒ tài xế từ chối nhiều hơn — hành vi ĐÚNG.

Giả thuyết chữa cháy đã **LOẠI**: nghĩ `accept_logit_center` cũ nên mới lệch ⇒ đo lại net trung vị
thị trường **20.760đ** vs config 21.200đ ⇒ chỉ ~+0,3pp, **không đủ** bù 5,7pp. Không đụng vào nó.

⇒ Hoàn tác về `k_max = 6`, **không nới dung sai test** (đó là che khuyết tật), ghi khuyết tật đầy
đủ vào config + một test **khoá cả hai vế** của đánh đổi. Chuyển thành **Q-07** cho Cường quyết.

⚠ **KHÔNG nâng `eta_max_min`** dù nó cho số đẹp hơn nữa (k=10/eta=18 → served 0,856): 11 phút là
ràng buộc **realism** (khách không chờ đón 18 phút), có căn cứ research 8–10′. Nâng nó là vặn thực
tế cho vừa kết quả — `CLAUDE §4b` cấm. Đã khoá bằng `test_eta_max_unchanged_realism_guard`.

### 3. Biên giới cung–cầu: `served_rate` và `trips/driver` KHÔNG thể cùng đạt (hồ sơ `14`)

Quét **16 tổ hợp (n × orders) × 3 seed**: **0/16 PASS** cả bốn tiêu chí. `served` tăng theo N/O,
`cuốc/tx` tăng theo O/N — **đối nghịch, không có điểm giao**.

**Trần năng lực**: khi bão hoà (rỗi 5%) tài xế làm **17,7 cuốc/ngày** — chạm **biên dưới** dải
research 18–22 ⇒ **vật lý của sim ĐÚNG**. Cấu hình hiện tại để tài xế **rỗi 32%** vì thừa cung.
Phân bổ khi bão hoà: `on_trip` 49% · `enroute` 24% · **`relocate` 14% (chạy rỗng)** · charge 8% ·
rest 5%.

⇒ Đòn bẩy **duy nhất** đẩy được cả hai metric là **phân bổ không gian** = **T-045a**
(`MarketStateView` + hồi sinh S4) — cũng chính là giá trị sản phẩm thật của advisor.

### 4. Sai lệch thiết kế: `orders_per_day` gắn với 50 actors, `actors.n` đã lên 90

`research/simulation/pilot-world-dongda.md` §3: *"Scale cho **50 actors**… `orders_per_day = 1.200`
→ ~19–21 cuốc/actor"*. `git log -S` xác nhận `orders_per_day` **chưa từng được scale lại**.
Đơn/actor: thiết kế **24,0** → hiện **13,3**. **Chưa sửa** — chờ Q-05.

### 5. Chi phí pin: có thật, chưa vào mô hình một đồng nào (hồ sơ `12` Phần B)

`grep swap_cost|charge_cost|energy_cost` = **rỗng**; `payout_vnd` chỉ `+=`. Hệ quả: nhóm **SWAP
kiếm hơn 26%** (262.502đ vs 207.962đ) với **cùng số cuốc, cùng giờ online**.
Số thật: đổi pin **9.000đ/lần** (press/medium) nhưng **nhiều chương trình miễn phí có trần** ⇒
biến **theo cohort/hợp đồng**, phải versioned. Kế hoạch 3 bước + **5 test** ở hồ sơ `13` §2.3.
**Chưa implement** — mặc định phải là 0 cho tới khi GSM xác nhận (`D-POL-05`).

### 6. Kiểm kê biến (hồ sơ `13` Phần 3)

- **S1 lành mạnh**: mọi input suy được từ 13 bảng thật (sau khi UPDATE-077 gỡ rò tương lai).
- **S2 có `soc_pct` — 13 bảng thật KHÔNG CÓ cột pin nào** (grep toàn schema). Ba đường ba hành vi:
  sim = telemetry thật · l1r = `None` ⇒ **im lặng giả định pin ĐẦY** · UI = **sha256 → 30..95**,
  và **số bịa đó hiển thị cho tài xế** (`⚡{soc}%`, tô đỏ <25%) **không có nhãn trên UI**.
- **Robustness: KHÔNG bền** — `soc_pct` thiếu thì fallback ngầm; `demand_forecast` rỗng thì điền 0;
  thêm biến mới thì vướng **B-02**. Nhưng repo **đã có mẫu đúng**
  (`historical_points_per_hour` → fallback + `source="dp:fallback"` + confidence 0,5) — vấn đề là
  **không áp dụng nhất quán**.
- **Bản dịch công thức → action**: đã trace toàn đường — **LLM/agent không tham gia chỗ nào**,
  thuần rule/math, đúng `CLAUDE §5`. Hai chỗ dịch dễ sai; chỗ thứ hai (`adapters/advisor`) đã sinh
  2/6 lỗi ở §1.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `configs/pilot_dongda.yaml` | sửa | ghi khuyết tật shortlist + bảng đánh đổi (giá trị **giữ 6**) |
| `tests/test_dispatch_shortlist_radius.py` | **tạo** | 4 test khoá đánh đổi + guard `eta_max` |
| `research/.../12-*.md` | **tạo** | root cause: dispatch · chi phí pin · chờ đơn |
| `research/.../13-*.md` | **tạo** | kiểm kê biến · mẫu lỗi · kế hoạch có test |
| `research/.../14-*.md` | **tạo** | biên giới cung–cầu · trần năng lực · đính chính 2 khuyến nghị |
| `research/.../14-joint-sweep-actors-orders.json` | **tạo** | artifact quét 16 tổ hợp |
| `tracking/TODO.md` | sửa | T-045 a/b/c/d/e + **T-046**; huỷ hướng "giá trị nghỉ" |
| `tracking/PENDING-REVIEW.md` | sửa | **Q-05**/**Q-06** (đã chốt) · **Q-07** (đánh đổi ghép đơn vs archetype) · **Q-08** (quyết định 2026-07-21 chưa xác nhận) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| shortlist hẹp hơn bán kính ETA | **OBSERVED-CODE+MEASURED** | `dispatcher.py:63` + đo bán kính đĩa | cao | — |
| served 0,750 → 0,789 khi nới k | **OBSERVED-SIM** | 3 seed | trung bình | **đã hoàn tác** vì 2 test realism đỏ |
| trần 17,7 cuốc/tx khi bão hoà | **OBSERVED-SIM** | 1 cấu hình, seed 1000 | trung bình | nếu sai thì kết luận "vật lý đúng" yếu đi |
| 0/16 tổ hợp PASS | **OBSERVED-SIM** | 16 × 3 seed | cao (hướng rõ) | — |
| 13 bảng không có cột pin | **OBSERVED-SCHEMA** | grep toàn `schemas/l1r/` | cao | — |
| đổi pin 9.000đ/lần | **press/medium** | iMotorbike 05/2026; vinfastauto 403 | thấp–TB | **phải hỏi GSM trước khi dùng** |

## Kiểm chứng

| Command / run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| `pytest tests/test_dispatch_shortlist_radius.py` | **2 failed → 4 passed** (sau hoàn tác) | — |
| quét `k_max` ∈ {6,12,16,20} × 3 seed | 12/16/20 **y hệt** ⇒ 12 bão hoà | chỉ 3 seed |
| quét lưới 16 tổ hợp × 3 seed | 0/16 PASS | 3 seed |
| đo trần năng lực | rỗi 32%/13%/5% theo tải | 1 seed |
| `pytest tests` (root, full) | **2 failed, 561 passed** ⇒ HOÀN TÁC | — |

**Full suite:** `k_max=12` cho **2 failed / 561 passed** ⇒ hoàn tác. Sau khi về `k_max=6`:
`test_dispatch_shortlist_radius.py` + `test_sim_realism.py` = **17 passed**. Trạng thái xanh cuối
cùng của cây nằm ở **UPDATE-080** (571 passed).

**Baseline**: vì đã hoàn tác, UPDATE này **không** làm lệch baseline. (UPDATE-080 thì CÓ — đổi
thuật toán dispatch.)

## Visual verification

- **Status:** `BLOCKED` → cần Cường xem
- **Vì sao:** đổi `k_max` làm **ghép đơn khác đi trên toàn bản đồ** — replay/heatmap sẽ khác.
- **Xem:** khu Mô phỏng → tab Replay quanh 07:00/18:00 (mật độ đơn chưa gán giảm) và tab Bản đồ H3.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

0. **Fix của chính UPDATE này đã bị hoàn tác** — tôi tuyên bố "fix thuần, không mất gì" rồi
   full suite chứng minh ngược lại. Bài học: **claim "không mất gì" phải chờ full suite**, không
   được rút ra từ 3 seed và 2 metric mình chọn.
1. **Tôi đã khuyến nghị SAI HAI LẦN ở cùng một câu hỏi** — và Cường đã duyệt trên cơ sở đó:
   - lần 1: gọi "tăng `orders_per_day`" là **bịa cầu** — sai, vì chưa đọc `pilot-world-dongda` §3;
   - lần 2: khuyến nghị **mở rộng zone** — sai, vì mở rộng **giữ nguyên mật độ** nên không đổi
     kinh tế mỗi tài xế, thế lưỡng nan vẫn y nguyên.
   Cả hai chỉ lộ ra khi **đọc lại docs + đo**, đúng như Cường yêu cầu. Đã ghi đính chính vào Q-05
   và hồ sơ `14` §5 thay vì sửa lặng lẽ.
2. **Test quan trọng nhất KHÔNG phải "k == 12"** mà là **bất biến phủ sóng** — nó sẽ đỏ lại nếu ai
   đổi `eta_max_min`, tốc độ hay res H3 mà quên k. Nếu chỉ assert hằng số thì đã tái tạo đúng mẫu
   lỗi đang sửa.
3. **Cám dỗ đã từ chối**: nâng `eta_max` lên 15–18 cho served 0,833–0,856. Đó là vặn realism. Đã
   khoá bằng test.
4. **`factor` min thực = 1,000**, không phải 1,24 như doc ghi (doc nói p10). Dùng **min thật** làm
   biên bảo thủ; nếu dùng p10 thì tính ra k nhỏ hơn và vẫn thiếu.
5. **3 seed là ít**: mọi số ở UPDATE này là **hướng**, chưa phải CI. Kết luận chỉ vững ở chỗ 12/16/20
   cho kết quả **trùng khít** (bão hoà) — cái đó không phụ thuộc số seed.
6. **Chưa đo lại chỉ tiêu kép ĐA-08** sau khi đổi `k_max` — bắt buộc trước khi so advisor tiếp.
7. **`relocate` 14%** mới được **chỉ ra**, chưa chứng minh giảm được. Không hứa.

## Expansion checkpoint (T-039)

1. **Schema**: đề nghị đưa `candidate_ring_k_max` thành **dẫn xuất** (từ `eta_max`, `speed_kmh`,
   res, đường kính vùng) thay vì số cứng — hiện mới khoá bằng test. Chưa làm.
2. **Bài toán tối ưu**: `relocate` 14% + phân bố đơn không đều = bài toán **positioning** chưa ai
   giải; đó là T-045a và là giá trị sản phẩm thật của advisor.
3. **Tính năng**: khi có `MarketStateView`, card *"khu X đang thiếu tài xế"* trở nên khả thi **và
   đo được** — khác hẳn lời khuyên nghỉ vốn không đo được.

## Follow-up / defer phát sinh

- **Q-05** (chờ Cường): xác nhận thứ tự mới ① k_max ✅ → ② tỷ lệ đơn/actor → ③ T-045a → ④ zone.
- **Q-06** (chờ Cường): SOC bịa hiển thị cho tài xế — ẩn / gắn nhãn / chờ GSM.
- **Đo lại baseline 30 seed** ở `k_max = 12` trước mọi so sánh advisor.
- **T-046**: viết test parity cho `bonus_at`/`day_bonus`, `next_tier_gap`, `trip_points`, và
  "caller truyền đủ params" cho 8 solver còn lại.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-15 · **Q-05 (đính chính, cần xác nhận)** · **Q-06 (SOC
bịa)** · Q-03, Q-04 · B-02 ARCH-VERSION chặn T-044 · **chưa commit gì trong toàn bộ phiên**.
