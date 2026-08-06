# UPDATE-164 — rc-02: BÁC giả thuyết bão hoà, đủ POWER, và ĐÍNH CHÍNH cách tôi trình bày số cho Cường

- **Ngày:** 2026-08-06
- **Loại:** research (số nền — rút từ artifact có sẵn, KHÔNG chạy sim mới) + **đính chính báo cáo**
- **Liên quan:** UPDATE-160 (NO-GO) · UPDATE-161 (rc-01 cơ chế) · câu hỏi Cường *"đáng ra thời gian
  thừa phải vào đơn chứ? đây là do thiết kế sim kém à?"*
- **Artifact:** `research/audit/2026-08-06-root-cause-idle/rc-02-numbers.json`

## 1. ⚠ ĐÍNH CHÍNH — tôi đã trộn HAI cửa sổ seed khi trả lời Cường

Khi giải thích *"thời gian giải phóng chảy vào idle/nghỉ"*, tôi dẫn **−698′ charge / +520′ idle /
+235′ rest** như **một sổ thời gian**. Sai:

| Số | Cửa sổ seed | n | Cấp bằng chứng |
| --- | --- | --- | --- |
| −698′ charge · +520′ idle · +98,9′ empty · +5,5 trips | **7000–7029** | 30 | ⚠ **CHỈ CẤP DOCS** — bảng trong UPDATE-159, sinh bởi probe scratchpad; **output KHÔNG được ghi ra artifact** |
| **+235′ rest SIG** | **1000–1099** | 100 | artifact `e01-station-100.json` |

Cùng kênh, cửa sổ 7000s cho rest chỉ **+19,6′ ns**. ⇒ **Không được cộng chúng vào một sổ.** Đây đúng
bẫy §5 của repo (*"con số nào định trích thì mở artifact gốc"*) — lần này tôi sập ở dạng **trộn đơn
vị cửa sổ seed**, và người bắt được là chính agent đo của tôi.

**Nợ kèm theo (`VISIBILITY GAP` cấp artifact):** bộ metric A/B (`parallel.py:194-215`) **không xuất
sổ thời gian ĐỘI** (idle/charge/empty/occupied/online tổng đội) — chỉ có `rest_min_total`. Vì thế
những số đẹp nhất về "thời gian chảy đi đâu" hiện **không kiểm chứng lại được** mà phải chạy lại probe.

## 2. Ba kết luận số học DÙNG ĐƯỢC

**(1) BÁC giả thuyết bão hoà — trực giác của Cường đúng.** Chuyển đổi *hoàn hảo* 698 phút-đội chỉ
cần **24–52 đơn/ngày**, trong khi nền có **188,31 đơn chết/ngày** ⇒ dùng hết **13–27%** kho. Không hề
"hết đơn để vớt". Củng cố: `positioning` từng vớt thật −23,4 đơn chết, và tỷ lệ đổi là **~0,96 đơn
hoàn thành cho mỗi đơn chết tránh được** (oracle: 0,93) ⇒ **cơ chế "vớt đơn chết → tiền" HOẠT ĐỘNG**
trong sim này. Thước quy đổi ba nguồn độc lập: **252–284đ/tài xế cho mỗi +1 đơn toàn đội**.

**(2) Phép đo CÓ ĐỦ POWER — "không thấy tiền" là hiện tượng THẬT.** Chuyển đổi hoàn hảo đáng
**+6.100…+14.700đ/tài xế** = **1,0–2,4 lần TOÀN BỘ kênh vị trí**, tức **6–13 lần** độ phân giải
(±~4 đơn/ngày) của phép đo tiền n=100. Nó đã không thấy ⇒ không phải nhiễu.
⚠ **Nhưng mặt sau, phải nói cho công bằng:** mức chuyển đổi **đo được** (+1,69 đơn ≈ **3–7%**) lại
**NẰM DƯỚI** độ phân giải đó ⇒ **không được đọc "payout ns" thành "chuyển đổi = 0"**.

**(3) LƯỢNG thời gian không phải biến quyết định.** 698 phút-đội = **7,76′/tài xế/ngày** rót vào kho
idle **sẵn có ~143′/tài xế**. Ở nền, **mỗi đơn chết đã có ~68 phút-đội idle nằm cạnh mà vẫn không gặp
nhau**. Thêm 5,4% vào một kho đã dư 68 lần ⇒ **năng suất biên của phút idle ở nền ≈ 0**.
⇒ **Câu hỏi đúng không phải "thời gian chảy đi đâu" mà là "vì sao idle và đơn chết KHÔNG GẶP NHAU".**

## 3. Bằng chứng định hướng mạnh nhất cho H2 (lệch VỊ TRÍ) — và phản biện đi kèm

- **Thuận H2:** tài xế tiêu điểm **idle +45,45′ SIG** nhưng **được chào ÍT HƠN: offers −5,14 SIG**
  (n=30 cùng chiều). Rảnh nhiều hơn mà ít cơ hội hơn — vì điều kiện được chào = `IDLE` **+ nằm trong
  bán kính**, phần hụt phải đến từ **vị trí** (hoặc cooldown/shortlist). Khớp rc-01 #7 (sau đổi pin
  IDLE ngay nhưng đứng ở **cell trạm**).
- **Phản biện ghi sẵn (chưa loại):** `supply_cell_hhi` **−0,0014 SIG** (cung dàn ĐỀU hơn, mạnh bằng
  positioning-oracle) và `station_hhi` −0,0564 SIG. **Dàn đều ≠ bám cầu.** rc-03 phải đo **chồng lấn
  với CẦU**, không đo độ đều.
- Một nhất quán đáng ghi: `others_trips` **+4,83 SIG** trong khi `orders_completed` +1,69 ns — vì tài
  xế tiêu điểm **mất 3,14 cuốc** (4,83 − 3,14 = 1,69). Không mâu thuẫn; là **tái phân phối**, không
  phải sản xuất thêm.

## 4. Tôi tự kiểm hai điều có thể lật kết luận cũ

1. **`coverage`**: `scripts/run_e01_station.py:37` dùng **`coverage="all"`** ⇒ **mọi** tài xế được
   khuyên. ⇒ **"P1 bị hại −3.863đ SIG" KHÔNG phải hiện vật của phép đo một-người** ⇒ **NO-GO của
   UPDATE-160 ĐỨNG**. (Khối "tài xế tiêu điểm" chỉ là cửa sổ chẩn đoán một người — **không được nhân
   lên 90**.)
2. **`starved_hours_n` arm A = 0,4 giờ/ngày** (Δ ns) ⇒ giờ "mọi tài xế đều bận" gần như **không tồn
   tại** ⇒ **đẩy lùi H1 dạng mạnh** ("đơn chết vì mọi người bận"), nhưng **không bác H1 dạng yếu**
   ("thời gian rảnh thêm rơi vào giờ ít đơn"). Cần histogram theo giờ ⇒ rc-03.

## 5. Trả lời câu "thiết kế sim có kém không?" — CHƯA phán, nhưng đã tách được ba loại

rc-02 nói rõ: **gộp ba thứ này thành "sim kém" là SAI**, phải phán riêng ở rc-04.

| Loại | Nội dung |
| --- | --- |
| **Khuyết tật thật (có hồ sơ, chưa sửa)** | shortlist hex **2,22 km < 3,14 km** bán kính ETA-khả-thi + `offer_cooldown 10′ ≥ patience_max 10′`. ⚠ Tồn tại ở **CẢ HAI arm** |
| **Lựa chọn mô hình có chủ đích** | nghỉ/di chuyển **không nhận đơn** (eligible = chỉ `IDLE`); cầu **ngoại sinh** không co giãn |
| **Visibility gap cấp artifact** | bộ metric A/B không xuất sổ thời gian đội (§1) |

**Phân loại cuối: `UNRESOLVED`** — rc-03 (probe chồng lấn idle × đơn chết theo cell/giờ) là phép đo
phân xử, **chưa chạy** (quota).

## Files bị ảnh hưởng

`research/audit/2026-08-06-root-cause-idle/rc-02-numbers.json` (MỚI) ·
`tracking/updates/UPDATE-164-*.md` · `PROJECT-GRAPH.md` · `PENDING-REVIEW.md`. **Không sửa code.**

## Kiểm chứng

- Mọi số trong rc-02 có **đường suy + nhãn** (`DERIVED` / `ESTIMATE` / `UNVERIFIED` / `DOCS-LEVEL`);
  tôi tự kiểm thêm hai điều ở §4 (đọc `run_e01_station.py:37` và artifact metadata).
- **Chưa kiểm chứng:** phân xử H1/H2/H3 (**cần rc-03**) · sổ thời gian đội (thiếu ở artifact) ·
  `Δoccupied/Δonline` cửa sổ 7000s (probe đo nhưng UPDATE-159 không in) · số lượt đổi pin/ngày.
- Suite: không chạy (không sửa code).

## Visual

`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. **Lỗi của tôi, không của agent:** tôi trộn hai cửa sổ seed khi trả lời Cường (§1) — cùng họ bẫy
   "trích số không mở artifact". Bài học bổ sung: **cửa sổ seed là một ĐƠN VỊ**; hai số khác cửa sổ
   không được đứng cùng một bảng mà không nhãn.
2. `−698/+520/+98,9` **không có artifact** ⇒ theo đúng kỷ luật repo, chúng là **bằng chứng cấp docs**.
   Tôi đã dùng chúng như số chắc. Muốn dùng tiếp thì **phải chạy lại probe và ghi artifact**.
3. Kết luận (2) có hai mặt và tôi phải nói cả hai: đủ power để bác *chuyển đổi hoàn hảo*, **không** đủ
   power để bác *chuyển đổi nhỏ*. Nói một mặt là thổi hoặc dập quá.
4. `starved_hours_n` — rc-02 tự cảnh báo **chưa đọc code định nghĩa**; tôi cũng chưa. Không dùng làm
   kết luận, chỉ làm định hướng.

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/` — đang sống) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
