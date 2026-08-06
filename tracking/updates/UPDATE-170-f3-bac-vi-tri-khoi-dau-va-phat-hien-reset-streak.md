# UPDATE-170 — F3: BÁC giả thuyết vị trí khởi đầu + phát hiện MỚI: `idle_streak` reset mỗi lần relocate

- **Ngày:** 2026-08-06
- **Loại:** research (falsifier cho giả thuyết của chính tôi) + phát hiện cơ chế mới (đọc code, xác nhận)
- **Artifact:** `research/audit/2026-08-06-root-cause-idle/f3-why-far-basin.py` + `.json`
- **Nợ mới:** `D-SIM-K8`

## 1. Câu hỏi và kết quả — giả thuyết của tôi BỊ BÁC

`UPDATE-169` §5 để mở: *vì sao đội xe hội tụ về cặp XA (`953`+`bb3`, 3,5 km) thay vì cặp GẦN mà chính
luật ưu ái hơn (`88f`+`8c7`, 1,3 km, lưu vực 42,8%)?* Giả thuyết rẻ nhất: **vị trí khởi đầu** — F1 cân
mọi ô như nhau, đội xe thật thì bắt đầu từ `home_cell`.

Đo (450 actor-run, 5 seed, arm A, giờ 18h — chạy đúng luật leo dốc từ `home_cell` thật):

| lưu vực | σ=0 | σ=0,30 |
| --- | --- | --- |
| `88f`+`8c7` — **GẦN cầu** (1,3 km) | **46,2%** | 25,6% |
| `94b`+**`953`** — **ô hút QUAN SÁT ĐƯỢC** (3,5 km) | **15,8%** | 12,2% |

Và chỉ **3,1%** actor có `home_cell` **là chính** hai ô hút.

⇒ **BÁC.** Nếu vị trí khởi đầu quyết định, đội xe phải dồn vào cặp **GẦN** (46,2%), không phải cặp **XA**
(15,8%). Quan sát thật là **56,6% phút idle ở cặp XA** ⇒ giả thuyết không giải thích được.

## 2. 🔴 Phát hiện MỚI khi truy tiếp — và nó đổi cách đọc F1

`world.py:1137`: **`actor.idle_streak_min = 0.0` sau MỖI lần relocate** (*"đã dịch chuyển ⇒ đếm lại từ
đầu"*). Nghĩa là bậc sốt-ruột **reset về 0 mỗi khi tài xế nhích một ô**.

Hệ quả: để lên bậc n=2 (ring 3) tài xế phải rỗi **40 phút LIÊN TỤC mà KHÔNG relocate**. Nhưng ở bậc n=0,
mỗi tick WAIT 2′ đã có `p_move = 0,5` để nhích nếu có ô ring-1 tốt hơn. Quy đổi từ hai số **đã đo**:
`15.310` phút idle đội/ngày ÷ `892` lượt `demand_seek`/ngày (rc-03) ≈ **17,2 phút idle mỗi lần relocate**
⇒ streak trung bình **~17′**, dưới cả ngưỡng bậc n=1 (20′) và **rất xa** 40′. `[DERIVED — từ hai số đo
của rc-03, không phải phép đo trực tiếp phân bố streak]`

⇒ **Cơ chế *"rỗi lâu thì đi xa hơn"* CHẾT vì HAI lý do độc lập:**
1. **`B3`** — ring 3 = 1,11 km vượt ngoài tầm nhìn niềm tin 0,74 km ⇒ ô ring-3 luôn `hint = 0.0` (đã ghi).
2. **`D-SIM-K8` (MỚI)** — bậc sốt-ruột **reset mỗi lần nhích** ⇒ hầu như **không bao giờ tới** bậc đó.

Sửa riêng `B3` (nới cửa sổ niềm tin) sẽ **không** làm cơ chế sống lại, vì lý do (2) vẫn chặn. **Đây là
điều mà `verdict §6.4a` chưa biết khi xếp `B3` là fix rẻ nhất — phải sửa CẢ HAI hoặc không sửa gì.**

## 3. Hệ quả cho cách đọc F1 (đính chính chính tôi lần thứ hai)

F1 nhấn mạnh bậc **n=2** (6 attractor, lưu vực lớn nhất 42,8%) — nhưng đó là **chế độ mà đội xe hầu như
không bao giờ vào**. Chế độ hiệu dụng là **n=0** (ring 1 ~0,37 km, bar 1,25), nơi F1 đo được **25
attractor** với lưu vực lớn nhất chỉ **9,4%** — và `953` là một trong số đó (**7,1%**).

⚠ Nhưng **n=0 cũng KHÔNG dự đoán được** 56,6% dồn vào hai ô. ⇒ Kết luận phương pháp: **bản đồ lưu vực
tĩnh dự đoán được CẤU TRÚC (luật tạo ra ít điểm hút cục bộ) nhưng KHÔNG dự đoán được KẾT CỤC (điểm hút
nào thắng)**. Đây là lần thứ ba trong ngày cùng một bài học; ghi thành nguyên tắc thay vì lặp lại.

## 4. `UNRESOLVED` — còn gì, và đã loại được gì

**Còn mở:** vì sao đội xe hội tụ về cặp XA?
**Đã LOẠI (có số):** ❌ deadhead/`_relocate_to_core` (rc-03: `demand_seek` **123** vs deadhead **2**) ·
❌ phân bố `home_cell` (F3: 15,8% vs 46,2%) · ❌ bản đồ lưu vực tĩnh ở mọi bậc (không khớp kết cục).
**Ứng viên còn lại (chưa đo):** quỹ đạo **phụ thuộc lịch sử** qua belief cache theo `(actor, giờ, cell)` ·
trường cầu **đổi theo giờ** nên lưu vực đổi trong ngày ⇒ tài xế bị "quét" dần về một chỗ · tương tác với
dispatcher (ai được chào thì reset streak — `world.py:1141` ghi *"reset khi được chào"*) ⇒ **ô ít được
chào giữ người lâu hơn**, một cơ chế tự-củng-cố mà bản đồ tĩnh không có.

⚠ **Phép đo đúng cho câu này là ĐO TRONG RUN THẬT** (phân bố lượt ghé + streak theo ô theo giờ), không
phải mô hình tĩnh. Ghi vào việc còn lại chứ **không** đoán tiếp.

## Kiểm chứng

- F3 dùng **lại nguyên hàm leo dốc của F1** (import trực tiếp) ⇒ không có nguy cơ hai bản luật lệch nhau.
- `home_cell` lấy từ **actor thật** của `run_once` (5 seed × 90 actor = 450 actor-run).
- `idle_streak` reset: **tôi tự đọc `world.py:1137`** (không tin trung gian).
- **Chưa kiểm chứng:** con số ~17,2 phút/lần relocate là **DERIVED** từ hai số của rc-03, **không** phải
  đo phân bố streak trực tiếp ⇒ đừng trích như số đo. Phân bố streak thật là việc còn lại.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim thay đổi.

## Visual
`NOT_APPLICABLE` — research.

## Adversarial self-review / flaws found

1. **Tôi tự bác giả thuyết của chính mình lần thứ ba trong ngày** (sau `D-ADV-03` và claim "hai ô bẫy").
   Điểm chung của cả ba: tôi đưa ra cơ chế **nghe hợp lý** rồi mới đo. Nguyên tắc rút ra và đã ghi:
   **mô hình tĩnh chỉ được dùng để nói về CẤU TRÚC, không được dùng để nói về KẾT CỤC.**
2. Phát hiện `D-SIM-K8` làm **xói** giá trị của fix `B3` mà verdict xếp *"rẻ nhất, sạch nhất"* — nếu ai
   sửa `B3` một mình rồi đo Δ≈0 thì sẽ kết luận sai rằng "cơ chế đi-xa-hơn vô dụng". Đã ghi vào DEFERRED
   để không xảy ra.
3. Giờ khảo sát F3 là **18h** (giờ cầu cao nhất) — chưa quét mọi giờ; lưu vực **đổi theo giờ** nên tỷ lệ
   46,2%/15,8% là của một giờ, không phải cả ngày. Không đủ để đảo kết luận (chênh lệch quá lớn) nhưng
   phải nói ra.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13 ·
**amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
