# UPDATE-141 — Q-16 chốt + FIX-PRE: `world.py:970` là TOÀN BỘ cơ chế (verdict 1, tuyệt đối)

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent (Cường: *"Với Q-16 đi theo hướng bạn đề xuất. Tiếp tục làm"*)
- **Loại:** quyết định + research (phép kiểm phân biệt) — **0 dòng code sản phẩm**
- **Liên quan:** `D-M3-04-FIX` · `D-M3-04-FIX-PRE` · `D-M3-06` · UPDATE-140 · Q-16

## 1. Q-16 chốt — cả hai theo đề xuất

| | Verdict |
| --- | --- |
| **(a)** | **Giữ `rest_window` TẮT** ở config sản phẩm — kênh vẫn hại sức khoẻ sau REVERT |
| **(b)** | **Duyệt HƯỚNG `D-M3-04-FIX`**: (1) hoãn = CAM KẾT; (2) nhánh rơi không được là `WAIT` |

Kèm ba quyết định thiết kế (AskUserQuestion, cả ba theo phương án đề xuất):

1. **Nhánh rơi**: chạy tiếp cây hành vi với REST bị che; nếu vẫn ra WAIT ⇒ **không hoãn**, cho
   nghỉ ngay (*"không có việc ≠ không hoãn"*).
2. **Ép cam kết**: tới giờ X ép REST **ở decision point kế** (không ngắt cuốc đang chạy); bận trọn
   giờ X ⇒ **trả quyền nghỉ ngay** — lần bản năng muốn nghỉ kế tiếp không bị phủ quyết.
3. **Gộp `D-M3-06`** (gỡ nhánh chết `GO_SWAP`/`GO_CHARGE`, 0/41 lượt) vào cùng cycle FIX.

⚠ Duyệt **hướng** ≠ duyệt **plan**: plan thi công đã trình và được duyệt riêng (plan mode,
2026-08-05, sau khi FIX-PRE chốt).

## 2. FIX-PRE — phép kiểm phân biệt (spec root-cause §5), chạy TRƯỚC khi thi công

**Thiết kế**: arm B″ = arm B nhưng phủ quyết bị CẮT — wrap `should_defer_rest` **thật**, giữ nguyên
mọi tác dụng phụ (coin/RNG/token/cadence), chỉ ép `defer=False` ⇒ dòng
[`world.py:970`](../../src/gsm_sim/world.py#L970) (`action := WAIT`) không bao giờ chạy, mọi thứ
khác y hệt B. Ba ô đọc kết quả **khai TRƯỚC khi chạy** (ghi trong docstring probe).

**Kết quả (30 seed × 3 ngày, metric ngày 1..2):**

| | |
| --- | --- |
| fingerprint B″ ≡ A | **30/30 seed, cả ngày 0 lẫn ngày 1** — bit-identical |
| Δ(B″−A) mọi khoản | **đúng 0.0** (13/13 khoản) |
| Đối chứng nội tại Δ(B−A) | tái lập đúng UPDATE-140: `rest_min` **−244,0** [−303,4; −182,8] · `idle_min` **+209,5** [+109,1; +312,0] ⇒ probe không hỏng |
| **VERDICT** | **1 — `:970` là TOÀN BỘ cơ chế (tuyệt đối)** |

Hai hệ quả quan trọng hơn con số:

- **Máy trong `should_defer_rest` (coin/cadence/token) KHÔNG nhiễm RNG world** — nếu nhiễm thì B″
  đã lệch A dù phủ quyết bị cắt (họ `D-SIM-K3`). Bit-identical 30/30 loại hẳn nghi ngờ đó.
- **Không còn "đường khác lấy mất nghỉ"** — điều kiện DỪNG (verdict 3) không xảy ra ⇒ thi công
  FIX đúng chỗ, không phải đoán.

## 3. Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/PENDING-REVIEW.md` | sửa | Q-16 → ✅ đóng, ghi verdict + ngày |
| `tracking/DEFERRED.md` | sửa | `D-M3-04-FIX`: ghi Cường duyệt hướng · `D-M3-04-FIX-PRE`: TODO → **DONE** (kết quả ở đây) |
| `scratchpad/fixpre_dm304.py` | tạo (scratchpad) | probe 3 arm, wrapper cắt phủ quyết, 3 ô đọc khai trước |

## 4. Kiểm chứng

| Command | Kết quả |
| --- | --- |
| `fixpre_dm304.py 2` (smoke) | đường ống chạy; fingerprint 2/2 identical. ⚠ Cột Δ(B−A) ở n=2 cho `idle_min` **đổi dấu** so với n=30 và `payout` "SIG" dương — đúng bẫy n nhỏ, **không đọc**; smoke chỉ kiểm đường ống |
| `fixpre_dm304.py 30` (~40′) | bảng ở §2 |

- **Evidence:** MOCK (`configs/pilot_dongda.yaml`), seeds 7000–7029, days=3, metric ngày [1,2],
  CI95 bootstrap 5000 lần ghép cặp theo seed. Confidence: CAO cho cơ chế (bit-identical là bằng
  chứng cấu trúc, không phải thống kê).
- **Visual:** `NOT_APPLICABLE` — research probe, 0 dòng code sản phẩm, kênh TẮT ở mặc định.

## 5. Adversarial self-review / flaws found

1. **Wrapper ≠ xoá dòng code**: B″ cắt phủ quyết bằng cách ép `defer=False` ở TẦNG BRIDGE, nên
   nhánh else của world vẫn log `advice_rest_veto` (khác arm B thật về event stream). Điều này
   **không ảnh hưởng** kết luận hành vi (log-only, 0 RNG, 0 state) — nhưng ai tái dùng probe để so
   **event stream** (không phải hành vi) sẽ đọc sai.
2. **`rest_deferred_min` trong B″ luôn 0** ⇒ rail `defer_cap` trong hàm thật không bao giờ bắn ở
   B″ ⇒ hàm gốc có thể trả `True` NHIỀU HƠN arm B. Vô hại vì mọi `True` đều bị ép `False`, nhưng
   nghĩa là **số lần "muốn hoãn" của B″ không so được** với B.
3. **Đã loại trừ:** "probe hỏng/không nhạy" — cột đối chứng Δ(B−A) tái lập đúng số đã công bố;
   "RNG world nhiễm từ bridge" — bit-identical 30/30 bác trực tiếp.
4. **Chưa kiểm:** hành vi ở `days>3` (FIX-PRE thừa kế thiết kế 3 ngày của `D-M3-04`); coverage
   khác `"all"`.

## 6. Follow-up

| ID | Việc |
| --- | --- |
| `D-M3-04-FIX-PRE` | ✅ **DONE** — verdict 1 |
| `D-M3-04-FIX` | **DOING** — plan duyệt 2026-08-05, cycle bắt đầu ngay sau update này (UPDATE-142) |
