# UPDATE-168 — F1 basin-map: falsifier ĐÃ CHẠY và làm YẾU chính claim "bẫy niềm tin" của tôi

- **Ngày:** 2026-08-06
- **Loại:** research (falsifier, **0 seed sim** — thuần hình học + config) + **đính chính artifact trước**
- **Artifact:** `research/audit/2026-08-06-root-cause-idle/f1-basin-map.py` + `...-KETQUA.md`
- **Chạm:** banner ĐÍNH CHÍNH đã thêm vào đầu `rc-00-VERDICT.md`; ghi chú vào `CAN-CUONG-DUYET-2026-08-06.md`

## Vì sao chạy cái này trước mọi việc khác

`rc-04` (verdict root-cause) **tự thừa nhận** trong mục adversarial: nó chưa liệt kê hết attractor, chưa
đo lưu vực, nên *"có thể còn attractor tốt (gần cầu) mà phần lớn tài xế thực ra rơi vào"*. Tôi ghi vào
todo là **phải chạy phép đo này TRƯỚC khi trích claim root-cause ra ngoài**. Nó là falsifier — và nó
**đã bắn một phần**.

## Kết quả (85 ô lõi × 19 giờ = 1.615 ô-giờ)

| bậc sốt-ruột | ring | số attractor | lưu vực lớn nhất |
| --- | --- | --- | --- |
| n=0 | 1 (~0,37 km) | 25 | 9,4% |
| n=1 | 2 (~0,74 km) | 14 | 20,1% |
| **n=2** (rỗi ≥ 40′) | 3 (~1,11 km) | **6** | **42,8%** |

Nhiễu per-actor: σ=0 → 4 attractor (top-3 = 84,6%) · σ=0,10 → 12 (53,3%) · **σ=0,30 → 40 (30,4%)** ·
**σ=0,60 → 78 (13,7%)**.

## ✅ Phần verdict ĐỨNG (F1 xác nhận độc lập)

1. Luật leo dốc **thật sự** dồn cung vào ít điểm hút: 25 → 14 → **6** khi bậc sốt-ruột tăng.
2. `give_up` sinh **CHU TRÌNH HAI Ô** — ở n=2 **100%** attractor là cặp; F1 tìm ra **đúng cặp
   `94b`+`953`** mà verdict dự đoán. Xác nhận không tầm thường.
3. `B3` (bước sốt-ruột no-op) tái tạo được: ô ring-3 luôn `hint = 0.0`.

## ⚠ Phần verdict BỊ LÀM YẾU — tôi đã sửa cách phát biểu

4. **"Đúng HAI ô bẫy" là quá hẹp**: lưu vực lớn nhất là **`88f`+`8c7` (42,8%)**, **không phải**
   `953`/`bb3`; cặp `94b`+`953` chỉ **14,7%** và `bb3` **không có** trong top-5 khi σ=0.
5. **"Bẫy do TÍNH ĐỊA PHƯƠNG, không do nhiễu" — SAI.** Với σ thực tế 0,10–0,60, attractor **vỡ thành
   40–78 cái** ⇒ luật leo dốc **một mình không dự đoán được** việc 56,6% phút idle dồn vào đúng hai ô.

**Phát biểu đã hiệu chỉnh** (đã ghi banner vào `rc-00-VERDICT.md`): *luật leo dốc + tầm nhìn 0,74 km tạo
ra một **HỌ** điểm hút cục bộ, cung rảnh bị giam trong họ đó* — **không** phải *"đúng hai ô, do tính địa
phương chứ không do nhiễu"*.

## 🔴 Nhưng giả thuyết thay thế của CHÍNH TÔI bị bác bởi số đã có trong tay

Tôi định đề xuất *"có thể `home_cell`/hình học deadhead mới là thứ bơm người vào hai ô đó"* (đúng mục còn
treo verdict §7.7). **rc-03 đã đo và bác**: nguồn idle tại hai ô hút (seed 1000, arm A) =
`relocate_demand_seek` **123** vs `relocate_deadhead_to_core` **2** vs `go_online` **4** ⇒ **95%** lượt
vào là do **chính luật leo-dốc-theo-niềm-tin**. Tôi đã có con số này trong artifact mà **chưa đọc tới**
khi hình thành giả thuyết — bài học: **đọc hết artifact trước khi đề xuất cơ chế thay thế**.

## Kiểm chứng

- Script mô phỏng **nguyên văn** luật: niềm tin chỉ trên `grid_disk(cell,2)` với nhiễu lognormal per-cell
  **keyed (seed, actor, hour, cell)** (`world.py:1146-1175`); leo dốc với `ring/bar/give_up` theo đúng
  config (`behavior.py:199-231`). **0 RNG sim**, tái tạo được.
- ⚠ **CHƯA kiểm chứng / KHÔNG so được:** cột *"khoảng cách tới ô nhiều đơn chết"* của F1 dùng **PROXY =
  cầu kỳ vọng** (rc-03 không xuất bảng đơn-chết-theo-ô, chỉ có tổng hợp) ⇒ **cấm** dùng số 0,00–1,34 km
  của F1 để bác số 3,40–4,73 km của verdict. Hai ô hút có cầu *trung bình* nhưng đơn chết **rất thấp**
  (3,2 đơn = 1,57% kho) ⇒ gần-ô-đỉnh-cầu **≠** gần-ô-đỉnh-đơn-chết.
- `p_move` không mô phỏng: nó đổi *tốc độ* tới attractor, không đổi *attractor nào*.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim thay đổi (chỉ thêm script đo + docs).

## Còn UNRESOLVED

Vì sao run thật cho `953`+`bb3` mà không phải cặp có lưu vực lớn nhất? F1 (tĩnh, mọi ô khởi đầu đồng đều)
là **mô hình quá thô** — dynamics thật có belief cache theo `(actor, giờ, cell)`, trường cầu đổi theo giờ,
và tài xế chỉ relocate khi rỗi đủ lâu. Muốn trả lời phải đo **phân bố lượt ghé theo ô** trong run thật.

## Visual
`NOT_APPLICABLE` — research, không đổi code/UI/hành vi sim.

## Adversarial self-review / flaws found

1. **Đây là lần thứ hai trong ngày một kết luận của tôi bị chính phép đo tiếp theo sửa** (lần một:
   `D-ADV-03` bị BÁC). Giá trị của việc chạy falsifier **trước** khi trích số ra ngoài đã tự chứng minh —
   nếu tôi báo "bẫy đúng hai ô, nhiễu vô can" cho Cường rồi mới đo, thì đó là một câu sai đã tới tay anh.
2. F1 **không** bác được phần cơ chế, và tôi phải nói rõ điều đó thay vì thổi phồng mức độ "đã bác" —
   claim còn lại (họ điểm hút cục bộ, 95% do `demand_seek`) vẫn đứng và vẫn đủ để kết luận §5 của verdict
   (cổng payout bất khả thắng cho kênh phía-cung) **không đổi**, vì §5 dựa trên số đo khác.
3. Tôi **chưa** dùng bảng đơn-chết-theo-ô đo được (rc-03 không xuất) ⇒ một cột của F1 là proxy có nhãn.
   Muốn so đúng thì phải xuất bảng đó — ghi vào việc còn lại, không giả vờ đã so.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (card F0/F1 đổi nội dung — blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13 · **amendment ĐA-08 kênh phía-cung** — tất cả đã gom vào
`tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
