# UPDATE-166 — ROOT CAUSE đã tìm ra + phản biện 5 nợ SỬA LƯNG chính tôi ở 4/5 (PAUSE tại đây)

- **Ngày:** 2026-08-06
- **Loại:** research (2 workflow, 14 agent, có probe chạy thật) — **0 dòng code thay đổi**
- **Trạng thái:** ⏸ **PAUSE theo lệnh Cường** (*"lưu plan lại, save ở đây và pause"*)
- **Plan đã duyệt & lưu:** `tracking/PLAN-2026-08-06-CYCLE-B0-da-duyet.md`

## 1. ROOT CAUSE — trả lời câu hỏi của Cường (verdict đầy đủ: `research/audit/2026-08-06-root-cause-idle/rc-00-VERDICT.md`)

> *"Đáng ra thời gian thừa phải vào đơn chứ? Đây là do thiết kế sim kém à?"*

**Không phải "sim kém" chung chung — là một khuyết tật CỤ THỂ ở bản năng đứng-chỗ:**
cung rảnh bị **giam trong hai ô "bẫy niềm tin"** (cực đại địa phương của trường cầu **tĩnh lấy từ
config**, hạng 5–6/85 ô) giữ **56,6% toàn bộ phút idle của đội**, cách **mọi** ô nhiều đơn chết
**3,40–4,73 km** — ngoài **cả** bán kính chào đơn 2,22 km **lẫn** bán kính ETA-khả-thi 3,14 km. Tài xế
rảnh chỉ **nhìn được 0,74 km** (`world.py:1165`), chỉ **đi lên dốc nghiêm ngặt** (`behavior.py:217`), và
bước *"rỗi lâu ⇒ đi xa hơn"* **là NO-OP** vì ring 3 = 1,11 km vượt ngoài tầm nhìn niềm tin. Nên phút rảnh
thêm phân bổ **y như hình học idle sẵn có** (50,5% Δidle rơi đúng hai ô bẫy — nơi chỉ có **1,57%** đơn
chết) chứ không di cư về phía cầu. Ba số đóng đinh này **không phụ thuộc seed** (hình học + config, 0 RNG).

**Phân loại (cấm gộp thành "sim kém"):** `MODEL GAP` (chi phối) + `BUG ×4` + `VISIBILITY GAP ×3 tầng`.
Phân bổ định lượng từng thành phần = **`UNRESOLVED`**.

| Loại | Nội dung |
| --- | --- |
| **(A) KHÔNG kém — chủ ý, có văn bản** | cầu ngoại sinh không co giãn (`REVIEW-092-4` deferred) · eligibility **chỉ** `IDLE` ⇒ nghỉ không vớt được đơn *theo thiết kế* · đội 74→90 là **đòn bẩy calibration** để đạt `served_rate` 0,797 ⇒ **dư cung là giá phải trả có ý thức** |
| **(B) KÉM THẬT — 4 khuyết tật, 2 MỚI** | `B1` shortlist hex 2,22 km < ETA 3,14 km (**nay có số**: 14,4% ≤29,4 đơn/ngày; **hội tụ** sweep 12-seed sẵn có: −37 đơn/ngày, bão hoà k≈8) · `B2` **cooldown kiểm SAU Hungarian**, chặn thì `continue`, **không chào người kế, không log** (69,6% slot) · 🆕 `B3` **bước sốt-ruột NO-OP** · 🆕 `B5` **slider dashboard nối khoá config CHẾT** (đang lừa người xem) · `B4` sổ thời gian đội **hở +3,41%** (chặng đi trạm đếm HAI lần) |
| **(C) Hệ quả chính sách — Cường quyết** | Trong world cố ý dư cung, **cổng payout của ĐA-08 là bất khả thắng về cấu trúc** cho mọi kênh chỉ giải phóng thời gian. Đề xuất: chấm kênh phía-cung bằng **metric thời gian + cổng không-gây-hại** (đúng điều kiện reopen (c) của `D-E4-06`) |

⚠ **Kỷ luật trích số:** *"cooldown nuốt 69,6% phép gán"* **phải luôn kèm**: 2.595 slot chỉ là **366,6
CẶP** (mỗi cặp lặp ~7 lần), thiệt hại thật **~2,5′ đời đơn cho 23,26% đơn chết** — **không** phải "mất
69,6% năng lực ghép đơn". Ceiling tiền của rc-03 §8 **ĐÃ BỊ RÚT** (quy sai địa chỉ).

## 2. Phản biện 5 nợ — **SỬA LƯNG TÔI Ở 4/5**

| Nợ | Verdict | Điều phản biện sửa của tôi |
| --- | --- | --- |
| **`D-M3-20`** arm đối chứng bẩn | ✅ **CONFIRMED ×2 góc soi** | Không sửa — **nặng hơn** tôi nghĩ: nhiễm THUẦN (kênh bật, 0 can thiệp) làm **fingerprint khác 5/5 seed**, payout ±0,7–3,0%, rest ±391′. Nền nhiễu **cùng bậc hoặc lớn hơn** hiệu ứng cần đo ⇒ **phương sai của Δ post-FIX gần như TOÀN BỘ là trôi-stream**. Đã **loại** giả thuyết "chỉ là D-SIM-K3" ⇒ cycle **riêng** |
| **`D-ADV-02`** shift_extend | ⚠ **bug CONFIRMED, nhưng CÁCH SỬA của tôi SAI** | Bản sửa **nguyên văn** tôi viết làm kênh **gần như TRƠ** (còn 13,6%); bản đúng là walk **từ `now`** (giữ 66%). Và claim *"need_min ước NON ~2×"* của tôi bị **đo NGƯỢC DẤU** (p50 = 1,000) |
| **`D-M3-21`** sàn bảo lãnh P4 | ⚠ **PLAUSIBLE — tôi NÓI QUÁ** | Tần suất bind 99,4% ✅, nhưng payout hằng chỉ ở **56–58,5%** ngày (bonus/mission **nằm ngoài** đồng nhất thức). Phản thực: sàn hấp thụ **~54%, KHÔNG 100%** ⇒ nói *"guard 1b yếu đi đáng kể"*, **không** phải "zero power" |
| **`D-ADV-01`** positioning | ⚠ **đổi tên + đo được** | **CẤM gọi "BUG"** — docstring tuyên bố thẳng *"chống herding"* ⇒ **DESIGN-GAP có chủ đích**. Vế stagger **CONFIRMED + đo**: 56% lượt gán bị stagger, 88% đi **xa hơn** cần thiết (+1,68 km median), thừa **112,8 km (+22%)**. Vế "không TTL" **bị hạ**: chỉ 0,8% vượt biên bucket |
| **`D-ADV-03`** đề xuất mở rộng #1 của tôi | ❌ **REFUTED — CYCLE HUỶ** | Đo thật: deadhead nền chỉ **0,99–1,06 km / 5,63′** mỗi lượt ⇒ luận điểm *"km rỗng đằng nào cũng chạy, chi phí biên ≈ 0"* **sai một bậc độ lớn**. Đổi đích sang ô cầu cách 3–5 km là **nhân km rỗng lên**, không miễn phí |

**Nợ chín nhất để sửa (theo tổng hợp): `D-M3-20` → `D-ADV-04` (mẫu số S1) → `D-ADV-01` vế stagger.**
⚠ Lưu ý tổng hợp viên: `D-ADV-04` *"KHÔNG nằm trong 5 nợ nhưng CHÍN NHẤT"* (đã reproduce, đã phân xử
solver-đúng/producer-sai, đã khảo sát test ghim).

## 3. ⚠ Cảnh báo TRUNG THỰC về chính hồ sơ này

**6/7 artifact phản biện KHÔNG TỒN TẠI trên đĩa** — plan mode chặn agent ghi vào repo. Chỉ có
`pb-06-dadv01-thiet-ke-hay-bug.json`. Các verdict khác là **relay bằng chữ** qua return value ⇒ theo
luật ADV-09, **CẤM trích bất kỳ SỐ nào được cho là của `pb-01/02/03/04/05/07` như số đã đo có nguồn**
cho tới khi chạy lại và ghi artifact. Tương tự: `mm-04`/`mm-07` chưa từng được ghi dạng JSON — tôi đã
**cứu nội dung** ra `mm-04-rest-family-STAGED.md` / `mm-07-s2-STAGED.md`.

**12 finding MỚI** (5 từ họ S2, 7 từ họ nghỉ) trong `00-SUMMARY.md` **CHƯA qua phản biện nào** — là
**hàng đợi**, không phải kết luận. Đáng chú ý nhất: `sp_end_only` **chết cấu trúc** (probe 0/252 ca có
END) ⇒ ai đọc ablation E-05 sẽ nhầm "im lặng cấu trúc" thành "không có ca nào đáng kết sớm".

## Files bị ảnh hưởng

- `research/audit/2026-08-06-root-cause-idle/`: **`rc-00-VERDICT.md`** (MỚI, 44KB) + **`rc-03-probe-script.py`** (MỚI — rc-03 từng trích đường dẫn **không tồn tại** ⇒ hồ sơ **không tái tạo được**, nay sửa)
- `research/audit/2026-08-06-math-model-audit/`: `00-SUMMARY.md` · `pb-06-*.json` · `mm-04`/`mm-07` STAGED + 4 file agent-staged cứu từ plan-file
- `tracking/DEFERRED.md`: `D-SIM-K7` (gộp B1–B5 + 3 tầng mù) · **3 đính chính** (`D-ADV-01`, `D-ADV-02`, `D-M3-21`) · **`D-ADV-03` BÁC** kèm lý do (bắt buộc, nếu không ý tưởng sẽ bị đào lại)
- `tracking/PLAN-2026-08-06-CYCLE-B0-da-duyet.md` (MỚI — plan Cường đã duyệt, lưu vào repo)

## Kiểm chứng

- rc-01/02/03/04 + 10 agent phản biện, **có probe chạy thật** (rc-03 có **cổng nhiễu-loạn XANH**:
  fingerprint 7 số trùng từng số giữa có-probe/không-probe ở cả hai arm + exact-repeat).
- **Chưa kiểm chứng:** phân bổ định lượng từng thành phần (`UNRESOLVED`) · 6/7 artifact phản biện thiếu
  (§3) · 12 finding mới chưa phản biện · basin-map (F1) **là falsifier cho chính claim bẫy** — **chưa chạy**.
- **Suite: không chạy** (0 dòng code đổi).

## Visual
`NOT_APPLICABLE` — research + docs. (Cycle B0 khi thi hành sẽ **BẮT BUỘC** visual gate vì card F0/F1 đổi.)

## Adversarial self-review / flaws found

1. **Bài học lớn nhất phiên này:** 4/5 nợ tôi tự tin đưa ra đều bị phản biện sửa — **hai lần** tôi đề
   xuất *"tối ưu một đại lượng có sẵn"* mà không đo cái giá (`station_choice` NO-GO, rồi `D-ADV-03` bị
   BÁC). Đây đúng là điều memory `soi-doc-lap-truoc-khi-bao-so` cảnh báo. Vòng phản biện **phải là bước
   bắt buộc**, không phải tuỳ chọn.
2. Tôi đã chạy 2 workflow **trong plan mode** ⇒ agent không ghi được artifact. Lần sau: **không** khởi
   động workflow ghi-file khi đang ở plan mode.
3. Verdict root-cause tự soi: rc-04 **chưa chạy sim lần nào** (đóng góp mới của nó là hình học tĩnh +
   đọc code) ⇒ chứng minh *tài xế rảnh KHÔNG THỂ tới chỗ đơn chết*, **không** chứng minh *nếu tới được
   thì vớt được bao nhiêu*. **F1 basin-map là phép đo giết được chính claim đó — phải chạy trước khi
   trích §1 ra ngoài.**

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/`) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13 — **Q-07 nay đang CHẶN B1** (ghép đơn đúng vs trung thành archetype) ·
**MỚI: amendment ĐA-08 cho kênh phía-cung** (§1C). ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
