# UPDATE-142 — `D-M3-04-FIX`: hoãn nghỉ = CAM KẾT, nhánh rơi không được là WAIT (+ `D-M3-06`)

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent (plan duyệt qua plan mode sau khi FIX-PRE chốt verdict 1)
- **Loại:** fix (đổi ngữ nghĩa cơ chế sim) + test + đo chẩn đoán
- **Liên quan:** UPDATE-140 (REVERT) · UPDATE-141 (Q-16 + FIX-PRE) · `D-M3-04-FIX` · `D-M3-06` · `D-E10-01`

## Tóm tắt

Bản cũ: hoãn nghỉ = **phủ quyết bây giờ** — `world.py` cũ đặt `action := WAIT`, biến **86%** phần
nghỉ bị lấy đi thành **chờ rỗng** không sinh thêm đơn nào (UPDATE-140; FIX-PRE: dòng đó là **toàn
bộ** cơ chế, bit-identical 30/30 seed). Bản mới, theo 3 quyết định Cường chốt 2026-08-05:

1. **Hoãn = CAM KẾT** — bridge ghi `rest_commit_due_min` (đầu giờ X, phút tuyệt đối trong ngày);
   world **ép REST ở decision point kế** trong giờ X (`rest_commit_gate`); bận trọn giờ X ⇒ cam
   kết **VỠ** và **quyền nghỉ trả lại** (`rest_commit_broken` — rail mới chặn mọi phủ quyết tới
   khi nghỉ THẬT xảy ra). Nghỉ thật (kể cả nghỉ sớm tự nguyện) xoá cam kết.
2. **Nhánh rơi không được là WAIT** — `consider_relocate` (tách từ bước 5 của cây bản năng,
   extraction thuần) là "cây hành vi với REST bị che"; nếu nó trả WAIT ⇒ **không hoãn**, cho nghỉ
   ngay (`no_alt_action`, kiểm **TRƯỚC** cadence/coin — lời khuyên không tồn tại thì không nén,
   đúng lý lẽ R-08). Relocate-do-hoãn mang `reason="rest_defer"` để truy vết được.
3. **`D-M3-06` gộp** — điều kiện hoãn chỉ còn `REST`; hai nhánh chết `GO_SWAP`/`GO_CHARGE` (0/41,
   `soc_low` chặn trước) đã gỡ, kèm test nguồn + test tích hợp `deferred_from ∈ {rest}`.

Kế toán đổi theo: `rest_deferred_min` cộng **một lần đúng khoảng hoãn** lúc cam kết (bản cũ
+2′/tick) — trần `rest_defer_max_min` (**POLICY_LOCKED, giá trị không đổi**) nay đếm đúng đại
lượng nó canh. Thứ tự rail có chủ ý: **soc_low/fatigued đứng TRÊN cam kết** — đang cam kết mà mệt
thật thì nghỉ ngay (test ghim).

Đường chạy thật (đo trên seed tích hợp): cam kết 13h31 → relocate `rest_defer` → **được đơn 32k**
→ `commit_kept` đúng 14h00 → nghỉ thật. Lời hứa được thi hành, và thời gian chờ thành thời gian
có ích — đúng thứ bản WAIT không bao giờ làm được.

## Sổ CAM KẾT — quan sát được (chống D-R12)

`rest_rails_audit` thêm 4 khoá: `commit_made_n / commit_kept_n / commit_broken_n /
commit_cleared_n`, nối vào `health_guardrail` (tầng 5, cột riêng, không VND). Bảo toàn
`made ≥ kept + broken + cleared` (phần dư = cam kết còn mở cuối ngày) + khúc GIỮA
`relocate(rest_defer) ≥ made` được test tích hợp ghim trên 3 seed.

## 🔴 Bug bắt được TRONG cycle (adversarial, trước khi ai đọc số)

`commit_made_n` bản đầu đếm **mọi** event kind `advice_rest_window` — nhưng kind đó **dùng chung**
với bản ghi không-theo của nhánh drain (thiết kế D-M3-01: cùng kind, khác cờ `followed`, để không
tách mẫu số). Đọc 5 thành cam kết trong khi chỉ có **2** (seed 7000). Sửa: lọc `followed=True`;
test tích hợp ghim cách đếm đúng. Bắt được nhờ **soi timeline từng event** khi thấy
`made=5 ≠ relocate_rest_defer=2` — hai bộ đếm mâu thuẫn lại một lần nữa là thứ cứu số liệu.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/behavior.py` | sửa | tách `consider_relocate` (extraction thuần — RNG order giữ từng draw) |
| `src/gsm_sim/entities.py` | sửa | 2 field cam kết + reset ngày **tường minh** (bẫy `D-E10-01`, có test) |
| `src/gsm_sim/advice_bridge.py` | sửa | `should_defer_rest` → `(defer, why, alt)`; rail `commit_broken`; alt check trước cadence/coin; nhánh `committed` không coin lại/không cộng quota; book cam kết + quota một lần |
| `src/gsm_sim/world.py` | sửa | `rest_commit_gate` (hàm module, unit-test được) + ép ở decision point (chỉ đè WAIT/RELOCATE/REST — không cướp quyền swap/end_shift) + điều kiện hoãn REST-only + nhánh REST xoá cam kết + `reloc_reason="rest_defer"` + 3 event kind mới (log-only, không vào mẫu số adherence) |
| `src/gsm_sim/sim_metrics.py` | sửa | 4 khoá sổ cam kết trong `rest_rails_audit` → `health_guardrail` |
| `tests/test_rest_commit.py` | **tạo** | 16 test, **đỏ-trước** (collection ERROR trước khi code) |
| `tests/test_advice_bridge.py` | sửa | 3 test lan can unpack 3-tuple — sửa **CÓ CHỦ Ý**, ngữ nghĩa lan can không đổi |

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| Test mới (đỏ-trước) | **16 passed** |
| Behavior-neutral config MẶC ĐỊNH (advice OFF) | fingerprint per-actor **15/15 IDENTICAL** vs HEAD (5 seed × {1-day, multiday d0, d1}) — extraction + field mới + nhánh REST đều bất động khi kênh tắt |
| Sever-restore 4 bước, anchor 1 dòng | **7/7 BẮT ĐƯỢC**: gỡ ép ⇒ đỏ · gỡ rail `commit_broken` ⇒ đỏ · nhánh rơi lùi về WAIT ⇒ đỏ (khúc giữa `reloc ≥ made`) · gỡ reset ngày ⇒ đỏ · audit mù (đổi kind) ⇒ đỏ · gỡ alt check ⇒ đỏ · quota lùi +2′/tick ⇒ đỏ |
| `tests/` liền kề (advice_bridge, rest_rails, registry, health_boundary) | 100 passed + đúng 1 F đỏ sẵn `K-03` (4 mục của Khánh, không phình) |
| `uv run pytest -q ui/backend/tests --ignore=…test_demo_advice_ack.py` | **192 passed** |
| A/B chẩn đoán 30 seed | ✅ **ĐẠT CẢ BA acceptance** — bảng dưới |
| `uv run pytest -q` (CẢ suite, SAU FIX) | **1091 passed / 5 failed / 4 skipped** (22′34″) — đúng 5 F **đỏ sẵn** (`K-01`×3 · `K-02` · `K-03` 4 mục của Khánh), **0 hồi quy**; 1091 = 1075 + 16 test mới |

### A/B chẩn đoán 30 seed × 3 ngày (metric ngày 1..2, CI ghép cặp theo seed) — ✅ ĐẠT CẢ BA

| khoản | TRƯỚC FIX (Δ B−A, n=30) | SAU FIX (Δ B_fix−A, n=30) | acceptance |
| --- | --- | --- | --- |
| `rest_min` | **−244,0** [−303,4; −182,8] 🔴 | **+10,9** [−41,2; +59,3] | ✅ CI không dưới 0 |
| `idle_min` | **+209,5** [+109,1; +312,0] 🔴 | **−66,8** [−200,6; +68,4] | ✅ CI chứa 0 |
| `work_span_p90` | +42,3 [37,5; 47,1] (n=100) 🔴 | **−2,9** [−9,6; +3,6] | ✅ CI chứa 0 |
| `occupied_min` | −0,4 ns | −3,2 [−46,7; +40,3] ns | (quan sát) |
| `payout_vnd` (cohort) | −105.972 ns | **−35.954** [−148.641; +68.098] **ns** | (quan sát — KHÔNG claim) |

⇒ **Kênh thôi ăn vào nghỉ**: mọi chỉ tiêu tầng 5 về ~0, tức STOP-C **không còn lý do bắn** ở ngữ
nghĩa mới. Sổ cam kết/ngày: `made` **2,0** [1,7; 2,5] · `kept` **2,0** [1,7; 2,4] — **hầu như mọi
lời hứa được giữ**; `broken` ≈ 0 · `cleared` ≈ 0. `rest_deferred_min` +198′/ngày [162; 235] — nay
đếm đúng khoảng hoãn thật. `veto_fired_n` +8,7 [7,0; 10,4] — lan can vẫn sống.

⚠ Đọc đúng: đây là **chẩn đoán cơ chế**, không phải phép đo giá trị. `made` giảm mạnh so với ngữ
nghĩa cũ (log một lần/cam kết thay vì mỗi tick + `no_alt_action` chặn ~7 lượt/ngày) nên **không so
được** số lần nói giữa hai ngữ nghĩa. Muốn bật lại kênh như lời khuyên kinh tế: prereg MỚI (Q-16a).

## Visual verification

- **Status:** `WAIVED` (2026-08-05) — Cường uỷ quyền lựa chọn (*"V30 bạn tự chọn"*); agent chọn
  **waive bằng bảng timeline** (seed 7000 · ngày 2 · actor 33: cam kết 13h31 → relocate
  `rest_defer` → đơn 32k → `commit_kept` 14h00 → nghỉ; tái tạo bằng `soi_made_vs_reloc.py`).
  Lý do: dashboard chỉ replay một-ngày mà kênh chỉ sống ở multiday; kênh TẮT + MỀM ở sản phẩm nên
  không màn hình nào đang hiển thị sai; xây multiday replay lúc này là phình scope cho kênh chưa
  được bật lại ⇒ ghi `D-VIS-01` (DEFERRED) với điều kiện mở lại: **khi cân nhắc bật lại kênh
  (prereg mới), visual multiday là BẮT BUỘC trước verdict**.
- Kênh **TẮT** ở config sản phẩm (Q-16a) ⇒ màn hình mặc định không đổi (đã chứng minh bằng
  fingerprint 15/15).

## Adversarial self-review / flaws found

1. **Bug đếm `commit_made_n`** — mục riêng ở trên. Đã sửa + ghim test.
2. **Cam kết "mồ côi" cuối ngày**: made − (kept+broken+cleared) > 0 khi giờ X chưa tới mà hết
   ngày/hết decision point idle. Không phải bug — reset ngày xoá — nhưng sổ **không đóng kín
   từng cam kết**; nếu về sau cần, thêm kết cục `commit_expired_day_end`. Khai làm giới hạn.
3. **`consider_relocate` trong nhánh rơi rút RNG từ stream world** ⇒ arm B_fix lệch quỹ đạo so
   với arm B cũ nhiều hơn chính hiệu ứng hành vi — **đúng thiết kế** (arm can thiệp được phép
   khác), nhưng nghĩa là so B_fix với B cũ **không** tách được "hiệu ứng ngữ nghĩa" khỏi "nhiễm
   RNG". Mọi so sánh phải là B_fix vs **A** (CRN pairing theo seed vẫn đúng).
4. **Gate chỉ đè WAIT/RELOCATE/REST** — nếu đúng giờ X tài xế đang được bản năng chọn
   GO_SWAP/END_SHIFT thì nghỉ không bị ép đè lên ràng buộc vật lý/ca; giờ X có thể trôi ⇒ VỠ ⇒
   quyền trả lại. Trung thực hơn là ép nghỉ đè lên đổi pin (hết pin giữa đường tệ hơn mọi lợi ích).
5. **Đã loại trừ**: extraction đổi hành vi (fingerprint 15/15) · gate/log/rail sống trên giấy
   (sever 7/7 + test tích hợp đòi kept > 0 thật) · cam kết sống qua đêm (test reset).
6. **Chưa kiểm**: days > 3 · coverage ≠ "all" · tương tác với kênh khác bật đồng thời (mọi arm
   chẩn đoán đều single-channel).

## Follow-up / defer

| ID | Việc |
| --- | --- |
| `D-M3-04-FIX` | **DONE-CODE** (chờ bảng A/B + suite điền, và `V-30` visual) |
| `D-M3-06` | ✅ **ĐÓNG** — nhánh chết gỡ trong cycle này, có test chặn tái sinh |
| `V-30` (mới) | Visual cam kết giữ/vỡ — BLOCKED vì dashboard chưa replay multiday; chờ Cường waive hoặc đặt việc mới |
