# UPDATE-162 — Ba nợ MỚI từ audit math-model (tôi TỰ KIỂM trên code) + đính chính comment sai

- **Ngày:** 2026-08-06
- **Loại:** research (audit math-modelling, phần tôi tự đọc thay agent tổng hợp đã chết vì quota) +
  fix docs-trong-code (comment sai, 0 đổi hành vi)
- **Liên quan:** UPDATE-160 (NO-GO `station_choice`) · UPDATE-161 (rc-01 cơ chế dispatch) ·
  `HANDOFF-2026-08-06-quota-blocked-audit.md` · chỉ thị Cường: *"kiểm tra tính logic của bài toán,
  quan sát đủ biến chưa, math modelling chuẩn chưa, có mở rộng thêm được không — kể cả cái đang tắt"*

## 0. Vì sao UPDATE này tồn tại

Agent phản biện + agent tổng hợp của workflow audit **chết vì quota**. Thay vì để 10 artifact thô
nằm im (và **cấm trích số** từ chúng theo bài học ADV-09), tôi **tự đọc 3 artifact quan trọng nhất**
(`mm-05` họ pin, `mm-11` information-set, `mm-01` positioning = kênh ĐANG SHIP) và **tự kiểm từng
claim CAO trên code**, không tin agent. Ba nợ dưới đây là những claim **đã qua tay tôi**; phần còn
lại (mm-02/03/06/08/09/10/12) vẫn **chưa kiểm ⇒ chưa được trích**.

## 1. 🔴 `D-M3-20` — ARM ĐỐI CHỨNG BỊ BẨN LẠI ở đường `rest_window` mới (sev CAO)

**Chuỗi bằng chứng tôi tự đọc:**
`advice_bridge.py:916` gọi `alt_action_fn(actor)` **TRƯỚC** cadence (`:922`) và coin (`:933`) →
`world.py:1041` truyền `lambda a: consider_relocate(..., self.rng, ...)` →
`behavior.py:228` `if best_cell != actor.cell and rng.random() < p_move` = **rút RNG thật** trên
stream chung. Nhánh cam kết `:898` cũng rút **mỗi tick**. Arm A: cổng cờ `:843` ⇒ `rest_window_hour`
trả `None` ⇒ return ở `:907-908` **trước** dòng 916 ⇒ **0 draw**.

**Hệ quả:** mọi quyết định **bị cadence nén hoặc coin từ chối** — lẽ ra phải **bit-identical** với
arm A — vẫn làm **lệch chuỗi ngẫu nhiên** của tài xế ở arm B. Với adherence P3/P5 ≈ 0,30 thì ~70%
lượt là loại đó. ⇒ **Δ(B−A) của `rest_window` sau 2026-08-05 trộn nhiễu trôi-stream với hiệu ứng
thật**, và điều đó **chạm chính bộ số acceptance của cycle D-M3-04-FIX mà tôi đã báo cho Cường
trong phiên này**. Đây đúng lớp lỗi `DET-01` từng làm tôi báo số sai một lần.

⚠ Khác `D-SIM-K3` (divergence chung khi hành vi THẬT đổi): đây là lệch stream **khi không có lời
khuyên nào ra**. ✅ **Không có số ship nào bị nhiễm**: kênh TẮT mặc định; `positioning` và verdict
NO-GO `station_choice` không đi qua đường này.

**Sửa (chưa làm — cần plan mode vì đổi hành vi sim):** tách `consider_relocate` hai pha — "có ô tốt
hơn không" (tất định, 0 draw, dùng cho gate `no_alt_action`) khỏi "có đi không" (`p_move`, rút SAU
coin); hoặc rút `p_move` đường-advisor bằng **keyed hash** như `adherence_coin`. **Acceptance:** kênh
BẬT + mọi coin từ chối ⇒ `fingerprint_actors` IDENTICAL arm A (test đỏ-trước), rồi **đo lại**
acceptance D-M3-04-FIX.

## 2. 🔴 `D-M3-21` — Sàn bảo lãnh tân binh hấp thụ TRỌN biên của P4 (sev CAO, đo lường)

**Đồng nhất thức tôi kiểm bằng code + config:** `world.py:575-578` cộng
`topup = (sàn − gross) × driver_share` vào payout. Khi `gross < sàn`:
`payout = 0,75×gross + 0,75×(350.000 − gross) = 0,75 × 350.000 = **262.500đ — HẰNG**`
⇒ **∂payout/∂gross = 0 chính xác**. Điều kiện bind: `tenure ≤ 90` (P4 sample tenure ∈ **[5,60)**,
`archetypes.py:113-115` ⇒ **mọi P4**) **VÀ `online ≥ 6h`** (`guarantee_min_online_h: 6.0`) VÀ
`gross < 350k`. Nhân đôi bởi cổng thưởng: P4 `accept_base 0,80 < 0,85` ⇒ `day_bonus = 0`.

**Hệ quả đổi cách đọc số:** với P4 trong vùng bind, **không kênh nào có thể lợi hay hại qua payout**
⇒ hàng P4 của guard **1b ĐA-08 pass MIỄN PHÍ, zero power**; và `payout_mean_all` bị một archetype
kéo về 0 **theo cấu trúc chính sách**, không phải vì lời khuyên vô dụng. Áp cho cả `+6.016đ` của
positioning: **phần giá trị tạo cho P4 có thể đang bị sàn nuốt và chưa ai tách**.
✅ **KHÔNG lật** NO-GO `station_choice`: nhóm bị hại là **P1**, tenure ∈ [90,720) ⇒ ngoài bảo lãnh.

**Sửa (không đổi hành vi khuyên — đổi BÁO CÁO):** tách `Δgross` vs `Δpayout` per-archetype + cờ
`policy_absorbed`. **CHƯA ĐO** tần suất bind (%ngày-P4).

## 3. 🆕 `D-ADV-01` — `positioning` (kênh ĐANG SHIP) thiếu vế Δ-GIÁ-TRỊ và cổng vật chất (sev TB→CAO)

`capacity_alloc.py:45-53`: cost chỉ có SOC-penalty + **+10 PHẲNG** cho slot lệch preferred ⇒
(a) không có vế *(đơn kỳ vọng ở đích − đơn bỏ lại ở nguồn − phút ENROUTE mất khả năng nhận đơn)* ⇒
**từng lượt gán có thể Δ-âm** dù trung bình thắng; (b) **stagger mù khoảng cách** — ô 0,5 km và
5 km cùng cost, tie vỡ theo **tên ô**; (c) **không có cổng min_gain** đối xứng
`station_choice_min_gain_min: 3` ⇒ "chênh vặt vẫn nói", trái R-08; (d) phân công **không TTL/không
re-validate** (`world.py:994-1012`) ⇒ thi hành trên ảnh cầu bucket cũ.

Kênh **vẫn PASS 9/9 ĐA-08** ⇒ **không lật kết luận**, đây là **dư địa**: nó đang *thắng dưới trần*.
Thứ tự đề xuất: **đo trước** (phân rã Δ-giá-trị per-move + phân phối `bucket_thi_hành − bucket_gán`
từ event log, không đổi hành vi) → rồi mới cân nhắc cost mở rộng. Đổi kênh đang bật ⇒ regate n=100.

## 4. Đính chính comment SAI trong nguồn sự thật (MI-8 — 0 đổi hành vi)

`behavior.choose_station` docstring ghi *"trạm quen p=0.7 (mock = gần nhà)"* và `world.py:971` ghi
*"choose_station RÚT RNG (p=0.7 trạm quen)"* — **tôi mở code: thân hàm 0 lần rút RNG** (chỉ sort
theo khoảng cách + né `queue>3`; `rng` nhận vào **không dùng**). Đã sửa **cả hai** thành mô tả đúng,
kèm hệ quả thật: gọi hàm đó **không** làm lệch dòng RNG ⇒ `swap_early` **an toàn CRN hơn** mức
comment cũ tưởng; thứ tự gate vẫn giữ nhưng **lý do thật là kỷ luật chung**, không phải "bảo toàn
draw". Họ lỗi `D-M3-15`: tài liệu sai nằm trong nguồn sự thật thì người đọc sau suy sai theo.

## Files bị ảnh hưởng

- `src/gsm_sim/behavior.py` · `src/gsm_sim/world.py` — **chỉ comment/docstring** (đính chính MI-8)
- `tracking/DEFERRED.md` — thêm `D-M3-20`, `D-M3-21`, `D-ADV-01` (và `D-SIM-K6` ở UPDATE-161)
- `tracking/updates/UPDATE-162-*.md` (file này) · `PROJECT-GRAPH.md` · `PENDING-REVIEW.md`

## Kiểm chứng

- **Mọi claim CAO ở đây tôi đã tự mở code/config kiểm lại**, không dùng nguyên văn agent: chuỗi
  916→1041→228 + cổng 843 (D-M3-20); đồng nhất thức topup + tenure range + `guarantee_min_online_h`
  (D-M3-21); cost matrix + không có TTL (D-ADV-01); thân `choose_station` (MI-8).
- **CHƯA kiểm chứng:** độ lớn của cả ba (chưa đo) · 7 artifact còn lại chưa đọc ⇒ **chưa được trích** ·
  `mm-04`/`mm-07` chưa tồn tại · **chưa qua vòng phản biện độc lập** (agent phản biện chết vì quota) ⇒
  ba nợ trên là **đã-tự-kiểm nhưng CHƯA-phản-biện**; đúng nghĩa "một mình tôi đồng ý với tôi".
- Suite: **không chạy** — thay đổi code là comment/docstring thuần (0 dòng thực thi). Đã đọc lại vùng
  sửa để chắc không chạm logic.

## Visual

`NOT_APPLICABLE` — không đổi hành vi/UI.

## Adversarial self-review / flaws found

1. **Tôi đang tự kiểm claim của agent bằng chính tôi** — đúng cái memory `soi-doc-lap-truoc-khi-bao-so`
   cảnh báo (3 lần tuyên bố xong đều bị soi độc lập bắt lỗi). Vì vậy ba nợ này ghi trạng thái **TODO
   chưa-phản-biện**, và tôi **không đề xuất sửa ngay** cái nào; ưu tiên phản biện khi có quota.
2. `D-M3-20` là nợ **tôi tự tạo ra** trong cycle D-M3-04-FIX của chính mình (2026-08-05) và đã báo
   "acceptance passed" cho Cường. Không giấu: bộ số đó **phải đo lại** sau khi sửa.
3. `D-M3-21` nghe *thuận lợi* cho advisor ("giá trị bị chính sách nuốt") ⇒ đúng loại claim memory
   `verify-favourable-claims-hardest` dặn kiểm gắt nhất. Đã kiểm đến mức đồng nhất thức đại số + dải
   tenure + ngưỡng online. Cái **chưa** có: **tần suất** bind thực tế ⇒ chưa được nói "P4 vô hại/vô lợi
   trong X% ngày".
4. Rủi ro suy diễn: `D-ADV-01` có thể là **thiết kế có chủ ý** (feasibility/anti-herding thay vì
   maximize) — trong repo đã có tiền lệ "tưởng bug hoá ra thiết kế có test ghim" (ADV-09). Vì vậy ghi
   thứ tự **đo trước, sửa sau**, không sửa cost khi chưa có số.

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/` — **đang sống**) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
