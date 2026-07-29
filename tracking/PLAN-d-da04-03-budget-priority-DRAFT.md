# PLAN (DRAFT — chờ Cường duyệt, KHÔNG implement) — D-ĐA04-03: ngân sách chú ý hết chia theo FIFO

Ngày: 2026-07-29 · Người soạn: AI agent (tổng hợp từ 3 thiết kế độc lập, mỗi thiết kế do một
agent riêng bảo vệ một góc — bản đầy đủ tại `scratchpad/da04_design_proposals.json`; lượt
soi đối kháng + chấm điểm độc lập bị QUOTA-BLOCKED, phần "đánh giá" dưới đây là của agent
chính, tự nhận là MỘT lượt đọc, chưa qua phản biện chéo).

## ⚠ ĐÍNH CHÍNH QUAN TRỌNG (2026-07-29, sau hai vòng soi đối kháng)

**Luận cứ định lượng trung tâm của plan này từng BỊ TREO** (bản đầu ghi "FIFO tốn 1.458đ") —
nay **đã đo lại xong và luận cứ MẠNH LÊN**. Ba confound được tìm ra *sau khi* lưới đó được đo:

1. **DET-01** — arm đối chứng `cadence=off` cũng tắt luôn keyed coin ⇒ adherence hiệu dụng cao
   hơn ~10đp. Đã sửa.
2. **R-01** — một lời khuyên được nghe theo bị **áp tác động 2,0–2,5 lần** ở arm OFF (không có
   cooldown ⇒ hỏi lại ⇒ keyed coin trả cùng "follow" ⇒ áp lại). **Lỗi đúng-sai.** Đã sửa.
3. **R-09** — ba kênh dùng ba định nghĩa "đã nói" ⇒ ngân sách chia không đồng nhất. Đã sửa.

**✅ ĐÃ ĐO LẠI XONG (artifact 37) — và kết quả làm plan này MẠNH LÊN, không yếu đi:**

| Δ payout/tài xế | có `shift_plan` | KHÔNG `shift_plan` | Bỏ `shift_plan` được gì |
| --- | --- | --- | --- |
| cadence **ON** | +5.624đ | +7.173đ | **+1.549đ** |
| cadence **OFF** | +8.488đ | +6.789đ | **−1.700đ** |
| *Giá của nhịp* | −2.865đ | **+384đ** | **tương tác +3.249đ** |

- Con số cũ 1.458đ → **+3.249đ** (gấp hơn hai lần), và ô OFF **đảo dấu** (−25đ → −1.700đ).
- **Không có `shift_plan`, nhịp gần như MIỄN PHÍ (+384đ)** ⇒ **toàn bộ "giá của nhịp" nằm ở
  cách chia ngân sách, không ở bản thân nhịp.** Đây chính xác là điều plan này định giải.
- Giá của nhịp ở n=100 ghép cặp (số duy nhất có CI hợp lệ): **−1.530đ CI[−2.401, −673] SIG**
  — bằng một nửa con số từng báo.
- ⚠ Các hiệu số trong bảng là hiệu của **điểm ước lượng** (không lưu per-seed cho 4 ô ⇒ không
  có CI). Muốn kết luận về độ lớn tương tác phải lưu per-seed rồi bootstrap.

**Hệ quả cho plan:** câu hỏi #6 ("*nếu Δ co về gần 0 thì đóng luôn D-ĐA04-03?*") **đã có câu
trả lời: KHÔNG** — Δ không co về 0, nó **to gấp đôi**. Phần *chẩn đoán cơ chế* vẫn đứng; phần
*định lượng* nay có số thật. ⚠ Vẫn giữ cảnh báo: `D-R08` cho biết con số "2.670 lần bị nén"
phóng đại ~47% vì ba kênh đếm "bị nén" theo quy ước khác `shift_extend`.

## 0. Sự thật làm đảo đề bài (phát hiện khi đối chiếu config — cả 3 thiết kế đều tự khai)

**Ở config ship hiện tại, D-ĐA04-03 tốn ≈ 0đ.** `configs/pilot_dongda.yaml`: 4 kênh chịu
ngân sách đều `false` (ĐA-07), chỉ positioning bật mà positioning nằm NGOÀI ngân sách.
Chi phí FIFO **+3.249đ/tài xế/ngày** (tương tác, artifact 37) chỉ xuất hiện khi bật nhiều kênh —
tức ở **arm nghiên cứu**. Hệ quả:

- Đây là nợ **hạ tầng ĐO**, không phải tiền đang mất: mọi phép đo "kênh X có giá trị không"
  từ nay về sau đều nhiễm artifact tranh-suất nếu không sửa.
- Severity đã hạ CAO → TB trong `DEFERRED.md` với căn cứ trên.
- **Thứ tự đúng: chốt Q-09 trước** (nếu Cường chọn "nới ngân sách 6→10" thì tranh chấp giảm
  hẳn và phần lớn giá trị của mọi cơ chế dưới đây bốc hơi).

## 1. Ba phương án (mỗi cái một câu + điểm chết người)

| # | Phương án | Cơ chế một câu | Điểm mạnh nhất | Điểm chết người (tự thú nhận) |
|---|---|---|---|---|
| A | **Thang ưu tiên tĩnh theo lớp khẳng định** + trọng tài PROPOSE/COMMIT | Gom candidate mỗi tick, xếp theo lớp `safety > policy/bonus > demand` (lớp = "input nào làm lời khuyên SAI"), cấp suất từ trên xuống, thua thì QUEUE | Không cần con số nào chưa tồn tại; bám sát chữ ĐA-04 đã duyệt; mọi lần cấp suất giải thích được bằng một dòng bảng | Thứ hạng NGƯỢC giá trị đã đo (positioning — kênh dương duy nhất — hạng chót); độc quyền chỉ đổi chủ (`accept_lift` có thể ăn 6 suất trong 100′ đầu ca "đúng luật") |
| B | **Ngưỡng giá trị theo suất còn lại** (reservation price, họ secretary problem) | Chỉ tiêu suất khi `ev` của lời khuyên vượt ngưỡng τ(suất còn lại, thời gian còn lại); đầu ca kén, cuối ca hạ giá | Đúng bản chất kinh tế của "ngân sách chú ý"; không rò tương lai (τ tính từ phân phối, không từ realization) | **Kênh tự chấm điểm bài của chính nó**: `shift_plan` khai `delta_payout ≥ 0 theo thiết kế` trong khi thực đo âm — kênh yếu nhất khai giá to nhất ⇒ có thể TỆ HƠN FIFO. `rest_window` chưa có ước lượng tiền nào trong repo |
| C | **Ngân sách có làn**: 1 suất bảo lưu/kênh + hồ chung 2 suất (tổng vẫn 6) | Không kênh nào bỏ đói kênh nào vì không ai đụng suất bảo lưu của ai; suất chưa dùng nhả vào hồ chung ở pha cuối ca | Rẻ nhất, không cần số mới, không dự báo (commitment device, không phải ước lượng) | Bảo đảm CÔNG BẰNG GIỮA KÊNH, không bảo đảm TIỀN: nếu 3 kênh được bảo lưu đều trung tính/âm thì âm hơn cả FIFO (`rest_window` nói 0/234 lần — giá trị CHƯA TỪNG đo được) |

## 2. Bảng chấm ĐỘC LẬP (giám khảo riêng, gộp 7 bản thiết kế → 4 họ)

Vòng 2 có một agent giám khảo chạy được (vòng 1 bị quota chém). Nó **đối chiếu file thật, không
nhận số của phương án làm sự thật**, và cho bảng dưới đây — 6 tiêu chí × 0–5:

| Họ | bám ĐA-04 | đo được | **không cần số chưa tồn tại** | sim + sản phẩm | determinism | đơn giản | **Tổng** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C — LÀN** (bản gọn) | 5 | 5 | 5 | 4 | 5 | 4 | **28** |
| **A — THANG TĨNH** | 5 | 5 | 5 | 4 | 5 | 2 | **26** |
| **D — PHẢN ĐỀ (bỏ ngân sách)** | 2 | 5 | 4 | 4 | 5 | 4 | **24** |
| B — stake (measure-first) | 4 | 5 | 3 | 3 | 4 | 2 | 21 |
| B — DP `ev` từ solver | 4 | 5 | **2** | 3 | 4 | 1 | **19** |

**Xếp hạng + khuyến nghị của giám khảo** (trùng kết luận của tôi ở §3, nhưng cụ thể hơn):

1. **C — LÀN, ship ở dạng TỐI THIỂU**: chỉ quota bảo lưu theo kênh, **bỏ hồ chung và bỏ
   `late_release` ở bản đầu** (đúng hai phần không có số đỡ lưng — tách thành arm riêng). Bắt
   buộc gộp hai catch: high-water `max_phase_rank` (nếu sau này bật late_release) và **thống
   nhất đơn vị "một lần nói" theo `decision_bucket` 30′** — không sửa chỗ này thì kết luận sẽ
   **đổ oan cho `rest_window`**.
2. **D — chạy Arm-1 của nó TRƯỚC, như một PHÉP ĐO, không như cơ chế để ship.**
3. **A — hoãn**, nhưng chạy phép chẩn đoán rẻ ngay: *% `shift_budget_exhausted` có đối thủ hạng
   cao cùng bucket*. Nếu <20% thì thang-thuần vô giá trị. A là hạ tầng đúng dài hạn
   (PROPOSE/COMMIT đằng nào cũng phải làm) — mở lại khi có **≥2 kênh production cùng bật**.
4. **B — không làm bây giờ**; nếu về sau thì lấy bản stake-có-nguồn, **tuyệt đối không** lấy
   bản dùng `delta_payout` do chính solver tự khai.

### ⚠ Tám cảnh báo của giám khảo về chính xếp hạng của nó (đọc trước khi tin bảng trên)

Ba cảnh báo nặng nhất:

- **(1) Mọi số tham chiếu trong cả 7 bản có thể đã hết hiệu lực.** Giám khảo tự kiểm mtime và
  phát hiện artifact 31–35 sinh **trước** fix DET-01 — độc lập trùng với đính chính ở đầu file
  này. Hệ quả nó nêu: *"nếu đo lại post-fix mà khoảng cách co lại thì hành động đúng có thể là
  **không làm gì cả**"*.
- **(5) Giá trị của `rest_window`/`shift_extend` CHƯA TỪNG được đo** (0 lần nói / 234 lần nén).
  Nếu chúng ÂM thì phương án C **thể chế hoá "mỗi tài xế nhận ít nhất một lời khuyên hại mỗi
  ca"** và có thể âm hơn cả FIFO. Cả hai bản đề xuất C đều tự khai điều này; giám khảo không có
  số để bác.
- **(7) `D-A3-01b` còn hở** (advice NO-OP vẫn đếm là followed) ⇒ mọi Δ của mọi phương án thừa kế
  sai số này; nếu đóng nó làm đổi kênh nào "trông có giá trị" thì **hạng lớp của A và suất bảo
  lưu của C cùng sai**.

Năm cảnh báo còn lại: Q-09 chưa chốt (nới 6→10 thì C mất phần lớn giá trị); nếu Cường định bật
≥2 kênh production sớm thì **A phải lên hạng 1**; nếu `rest_window` xếp lớp SAFETY thì nó bypass
mọi cổng và C mất lý do tồn tại; **không đủ power để xếp hạng bằng ĐO** (Δ 1,4–2,9k trên SD
~40k/seed — xếp hạng này dựa trên chất lượng thiết kế + chi phí, **không** dựa trên bằng chứng
rằng phương án nào thu lại được tiền); và điểm "đơn giản" của C giả định đã bỏ hồ chung.

## 3. Đánh giá của agent chính (một lượt đọc — chưa qua phản biện chéo)

Câu hỏi thật không phải "cơ chế nào tối ưu" mà là "**ta cần gì NGAY**". Ngay bây giờ mục đích
duy nhất có thật là **đo sạch giá trị từng kênh** (phục vụ quyết định bật lại kênh nào). Cho
mục đích đó:

- **B bị loại ở vòng gửi xe** cho tới khi có ước lượng `ev` không do kênh tự khai — vi phạm
  tinh thần "không bịa số" và có chế độ hỏng tệ hơn hiện trạng.
- **A là hạ tầng đúng dài hạn** (trọng tài một điểm + PROPOSE/COMMIT tách side-effect khỏi
  kiểm tra là việc đằng nào cũng phải làm), nhưng nặng (đụng cả 4 kênh trong `advice_bridge`
  + `world`) và thứ hạng tĩnh chưa có gì đỡ lưng ngoài chữ.
- **C — biến thể TỐI THIỂU của nó — là cái nên làm trước**: khi chạy arm nghiên cứu, mỗi kênh
  có quota riêng (không hồ chung, không nhả pha cuối — bỏ cả hai chi tiết chưa có số đỡ) ⇒
  phép đo "giá trị kênh X" không còn nhiễm bởi kênh khác chiếm suất. ~30 dòng, một cờ config
  `budget_mode: fifo | per_channel`, mặc định `fifo` để bit-identical.

**Khuyến nghị**: (1) chờ Q-09; (2) nếu vẫn cần đo kênh → làm C-tối-thiểu như công cụ đo;
(3) A để dành khi có ≥2 kênh production cùng bật; (4) B chỉ sau khi solver trả được `ev`
kiểm chứng độc lập (thuộc họ ĐA-07 mở rộng).

## 4. Câu hỏi PHẢI Cường chốt (gom từ cả 3 thiết kế, khử trùng lặp)

1. **Q-09** (đã có trong PENDING-REVIEW): giữ nhịp / nới 6→10 làm ARM / bỏ nhịp ở sim.
2. Có ý định **bật lại kênh nào** trong 4 kênh đang tắt không? Nếu KHÔNG trong tầm nhìn gần,
   D-ĐA04-03 nên đứng yên ở TB và không làm cơ chế nào cả.
3. `rest_window` thuộc lớp **demand** (theo input làm nó sai) hay **safety** (theo đối tượng
   nó bảo vệ)? Ảnh hưởng trực tiếp mọi cơ chế ưu tiên VÀ liên quan T-041 (hậu quả MỆT).
4. Khi bật `count_positioning_in_budget` để đo: positioning xuống hạng chót theo lớp, hay giữ
   1 suất dự trữ? (trung thành với chữ ĐA-04 vs bảo vệ kênh dương duy nhất).
5. Có được dùng số Δ đã đo (artifact 31–34) để fit hệ số hiệu chỉnh per-channel không? (fit
   trên chính bộ seed đã báo cáo — agent coi là ranh giới cần cho phép tường minh.)
6. **Kết cục rẻ nhất, phải cân nhắc nghiêm túc: sau artifact 37, nếu Δ co về gần 0 thì có
   ĐÓNG LUÔN `D-ĐA04-03` không?** Hai vòng soi đã cho thấy phần lớn "thiệt hại của FIFO" là
   confound đo lường chứ không phải thiệt hại thật; nếu số cuối gần 0 thì **không xây cơ chế
   nào** là hành động đúng. Cả giám khảo lẫn bản tổng hợp đều đặt khả năng này lên bàn.
7. Nếu cơ chế ưu tiên thu lại tiền nhưng làm `gini_payout` xấu đi SIG — bán lại đúng thứ
   cadence đã mua — thì có chấp nhận không? (họ hàng Q-09.)

## 5. Việc agent tự làm được (không cần chốt gì)

**Đã làm xong trong ngày 2026-07-29** (xem UPDATE-099): siết toàn bộ bộ test (R-04..R-07,
R-13..R-16, R-19); nối dây client (`topic`, `is_driving` — R-03/R-12); ca vắt nửa đêm phần (a)
+ bỏ fallback pha (R-11a/R-18); một-quyết-định-một-lần-áp (R-01); đồng nhất đơn vị "đã nói"
(R-09); và **chạy lại toàn bộ artifact** (36, 37).

**Còn lại:**

- Đóng `D-A3-01b` (advice NO-OP đếm là followed) TRƯỚC mọi cơ chế ưu tiên — mọi phương án
  đều thừa kế lỗi này nếu không đóng (thiết kế B nói rõ: lời khuyên ev cao nhưng không đổi
  hành vi vẫn thắng đấu giá).
- ~~Sửa bug đếm đôi ở app~~ → **ĐÃ FIX** (Lỗi #12 trong UPDATE-099): `_cadence_memory` nay
  đếm `len(set(decision_id))` thay vì cộng mỗi event. Giám khảo bắt được rằng §6 của bản draft
  đầu vẫn ghi nó là "nợ phải trả" — đúng, và đây là bản sửa. **Bài học nhỏ: một plan draft viết
  trước khi fix sẽ nói dối ngay sau khi fix; phải rà lại plan mỗi lần code đổi.**

## 6. Phát hiện kèm theo — ĐÃ XỬ LÝ

`ui/backend/app/routers/advice.py::_cadence_memory` từng đếm `proactive_count += 1` cho CẢ
`displayed` LẪN `followed` ⇒ một card được xem kỹ rồi làm theo tiêu **2 suất** ⇒ 3 card là
advisor im cả ngày. **Đã reproduce, đã fix, đã có test** (`test_budget_counts_decisions_not_events`)
— xem UPDATE-099 §Lỗi #12. Mục này giữ lại để không ai đọc bản draft cũ rồi đi sửa lần hai.

## 7. Sai sự thật trong các bản thiết kế (dùng khi viết plan chính thức)

Giám khảo đối chiếu file và tìm ra ba nhóm sai — ghi lại để plan chính thức không kế thừa:

1. **Cả 7 bản trích sai số UPDATE**: các phát hiện cadence (531/2.670, actor 89 lấy 6/6 suất,
   `rest_window` 234 lần nén) nằm ở **UPDATE-099**, không phải UPDATE-098 (098 là debate/herding
   của teammate). Bản thân các con số thì đúng.
2. **Hai bản mô tả sai code hiện hành**: nói `coin_follows` còn nhánh
   `cadence_enabled=False → self.rng.random()`. Nhánh đó **đã bị xoá** (fix DET-01); dòng đó nay
   là comment mô tả việc xoá. Một bản còn dựng *ràng buộc thiết kế* trên sự thật đã mục.
3. **Số dòng `advice_bridge.py` lệch ~10** so với file hiện tại (file đã sửa nhiều lần trong
   ngày) — dùng tên symbol, đừng dùng số dòng.
