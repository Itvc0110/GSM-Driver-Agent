# F1 — BASIN MAP: kết quả + phán quyết về claim "bẫy niềm tin" của `rc-00-VERDICT`

Chạy: `uv run python research/audit/2026-08-06-root-cause-idle/f1-basin-map.py` · **0 seed sim**,
thuần hình học + config (tái tạo được). Nguồn luật: `behavior.py:199-231` + `world.py:1146-1175`.

## 0. Vì sao chạy: đây là FALSIFIER cho chính kết luận của tôi

`rc-04` tự thừa nhận trong mục adversarial: nó **chưa liệt kê hết attractor**, **chưa đo lưu vực** ⇒
*"có thể còn attractor tốt (gần cầu) mà phần lớn tài xế thực ra rơi vào"*. F1 trả lời đúng câu đó.

## 1. Số đo

**Số attractor giảm mạnh khi tài xế sốt ruột** (85 ô lõi × 19 giờ = 1.615 ô-giờ):

| bậc sốt-ruột | ring | bar | give_up | số attractor | lưu vực lớn nhất |
| --- | --- | --- | --- | --- | --- |
| n=0 (rỗi ≥ 0′) | 1 (~0,37 km) | 1,25 | không | **25** | 9,4% |
| n=1 (rỗi ≥ 20′) | 2 (~0,74 km) | 1,15 | không | **14** | 20,1% |
| **n=2 (rỗi ≥ 40′)** | 3 (~1,11 km) | 1,05 | **có** | **6** | **42,8%** |

Ở bậc n=2 (bậc quyết định — tài xế rỗi lâu), **MỌI attractor đều là CHU TRÌNH HAI Ô**:

| attractor | lưu vực | cầu TB/ngày |
| --- | --- | --- |
| `88f` + `8c7` | **42,8%** | 29,37 |
| `c03` + `c0b` | 22,4% | **47,97** ← ô đỉnh cầu |
| `94b` + **`953`** | 14,7% | 28,13 |
| `e2b` + `e2f` | 12,9% | 33,09 |
| `843` + `847` | 5,4% | 24,41 |

**Nhiễu per-actor phá vỡ cấu trúc attractor:**

| σ | số attractor | top-3 chiếm |
| --- | --- | --- |
| 0,00 | 4 | 84,6% |
| 0,10 | 12 | 53,3% |
| 0,30 | **40** | **30,4%** |
| 0,60 | **78** | **13,7%** |

## 2. Phán quyết — F1 XÁC NHẬN phần cơ chế, LÀM YẾU phần "hai ô cụ thể"

### ✅ XÁC NHẬN (độc lập, không cần seed)
1. **Luật leo dốc THẬT SỰ dồn cung vào ít điểm hút**: 25 → 14 → **6** attractor khi bậc sốt-ruột tăng.
2. **`give_up` sinh CHU TRÌNH HAI Ô** — ở n=2, **100%** attractor là cặp. Khớp đúng dự đoán *"chu trình
   `953 ↔ 94b`"* của verdict §2(3), và F1 tìm ra **đúng cặp đó** (`94b`+`953`, lưu vực 14,7%). Đây là
   xác nhận độc lập không tầm thường.
3. **`B3` (bước sốt-ruột là no-op) được tái tạo**: ô ring-3 luôn `hint = 0.0` nên không bao giờ được chọn
   theo nhánh so-sánh; ring 3 chỉ có tác dụng qua nhánh `give_up`.

### ⚠ LÀM YẾU (phải sửa cách phát biểu của verdict)
4. **Claim "hai ô bẫy" là QUÁ HẸP.** Ở n=2 không nhiễu, lưu vực lớn nhất là **`88f`+`8c7` (42,8%)** —
   **không phải** cặp `953`/`bb3` mà verdict nêu; `bb3` **không xuất hiện** trong top-5 khi σ=0.
5. **Nhiễu KHÔNG vô can — trái với verdict.** Verdict §2 viết *"Bẫy do TÍNH ĐỊA PHƯƠNG, không do nhiễu"*.
   Đo được: với σ thực tế theo archetype (0,10–0,60), attractor **vỡ thành 40–78 cái**, top-3 chỉ còn
   **30,4% → 13,7%**. ⇒ **luật leo dốc MỘT MÌNH không dự đoán được** việc 56,6% phút idle dồn vào đúng
   hai ô. Verdict đã nói quá ở chỗ này.
6. ⚠ **Cột "khoảng cách tới ô nhiều đơn chết" của F1 KHÔNG so được với verdict**: F1 dùng **PROXY = cầu
   kỳ vọng**, còn verdict dùng **đơn chết ĐO ĐƯỢC**. Hai ô hút có cầu *trung bình* nhưng đơn chết **rất
   thấp** (3,2 đơn = **1,57%** kho, rc-03) ⇒ *gần ô đỉnh-cầu* **không** đồng nghĩa *gần ô đỉnh-đơn-chết*.
   **Không được dùng con số 0,00–1,34 km của F1 để bác con số 3,40–4,73 km của verdict.**

### 🔴 NHƯNG giả thuyết thay thế của tôi BỊ BÁC bởi số đã có trong tay
Tôi định đề xuất *"có thể `home_cell`/hình học `_relocate_to_core` mới là thứ bơm người vào hai ô đó"*
(chính là mục còn treo ở verdict §7.7). **rc-03 đã đo và bác nó**: nguồn của idle tại hai ô hút
(seed 1000, arm A) = **`relocate_demand_seek` 123** vs `relocate_deadhead_to_core` **2** vs `go_online` **4**
⇒ **95% lượt vào là do chính luật leo-dốc-theo-niềm-tin**, không phải nhà ở hay deadhead.

## 3. Kết luận đã hiệu chỉnh (thay cho §2 của verdict)

> Luật đứng-chỗ **thật sự** dồn cung rảnh vào một số ít **chu trình hai ô** (6 attractor ở bậc sốt ruột
> cao), và **95% lượt vào hai ô hút quan sát được là do chính luật đó** (`demand_seek`), không phải nhà
> ở/deadhead. Nhưng **danh tính** của hai ô đó **không** suy được từ luật leo dốc một mình: dưới nhiễu
> per-actor thực tế, attractor vỡ thành 40–78 cái. ⇒ Phát biểu đúng là *"luật leo dốc + tầm nhìn 0,74 km
> tạo ra một HỌ điểm hút cục bộ, và cung rảnh bị giam trong họ đó"*, **không** phải *"đúng hai ô, do
> tính địa phương chứ không do nhiễu"*.

**Còn `UNRESOLVED`:** vì sao trong run thật lại là **`953`+`bb3`** mà không phải cặp có lưu vực lớn nhất
(`88f`+`8c7`)? F1 (tĩnh, mọi ô khởi đầu đồng đều) là **mô hình quá thô** cho câu đó — dynamics thật có
belief cache theo `(actor, giờ, cell)`, trường cầu đổi theo giờ, và tài xế chỉ relocate khi rỗi đủ lâu.
Muốn trả lời phải đo **phân bố lượt ghé** theo ô trong run thật, không phải fixpoint của bản đồ tĩnh.
