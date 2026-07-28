# UPDATE-084 — b4: đo kênh VỊ TRÍ 30 seed — kênh ĐẦU TIÊN cứu HỆ THỐNG, nhưng cá nhân vẫn lỗ

> ⚠ **CORRECTED 2026-07-28 — BUG-EVAL-ARGMAX (UPDATE-085 §4, Q-11).** Mọi số payout "tài xế
> đích" trong file này đo bằng `pick_target` argmax-A — phép chọn CỰC TRỊ có bias âm hệ thống
> (regression to the mean; sign-flip đã chứng minh: argmax-A −19,7k vs argmax-B +27,4k vs
> không-chọn-lọc +3,6k trên CÙNG can thiệp). **Các số tầng HỆ THỐNG (served/expired/HHI/Gini/
> tổng payout đội) KHÔNG bị ảnh hưởng.** Số thay thế: artifact `24-unbiased-30seed.json` +
> UPDATE-086. Giữ nguyên phần còn lại của file làm lịch sử.


- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** measurement (quyết định bật/tắt kênh)
- **TODO liên quan:** **T-045a b4** (bước cuối) · nối tiếp UPDATE-083
- **Artifact:** `research/audit/2026-07-27-current-state/21-b4-positioning-30seed.json`
  (30 seed CRN 2000–2029 · `coverage: all` · nền `drop_demand_alpha = 0.4` · 120 lượt sim)

## Thiết kế đo

Bốn thế giới mỗi seed (A chạy một lần, dùng lại — CRN):

| | advisor | positioning |
|---|---|---|
| **A** | tắt | — |
| **B0** | bật (shift_plan như hiện trạng) | off |
| **B1** | bật | `wait_only` |
| **B2** | bật | `wait_and_relocate` |

⚠ So B1 vs B2 là so biến thể ⇒ cần ≥100 seed (`MIN_SEEDS_FOR_VARIANT_COMPARISON`); bảng dưới
CHỈ đọc từng nhánh so với A.

## Kết quả (Δ = B − A, CI 95% bootstrap, SIG = CI không chứa 0)

| Chỉ số | B0 (advisor hiện trạng) | B1 (wait_only) | B2 (wait_and_relocate) |
|---|---|---|---|
| **payout tài xế đích (P4)** | **−32.879đ** SIG · lợi 4/30 | **−40.139đ** SIG · lợi 2/30 | **−28.737đ** SIG · lợi 6/30 |
| served_rate | −0,001 (ns) | **+0,0103 SIG** | **+0,0076 SIG** |
| đơn hết hạn / ngày | −0,2 (ns) | **−13,4 SIG** | **−10,1 SIG** |
| **tổng payout TOÀN ĐỘI** | **−169.522đ SIG** | **+212.216đ SIG** | **+163.212đ SIG** |
| Gini payout [VETO] | ns | ns (−0,004) | ns |
| **HHI cung/ô [VETO]** | ns | **GIẢM −0,0009 SIG** ✅ | **GIẢM −0,0008 SIG** ✅ |
| **km rỗng share [VETO]** | ns | **+0,72đp SIG** ❌ | **+0,70đp SIG** ❌ |
| số lần đổi pin [VETO] | ns | ns | ns |
| khách chờ median | +0,0014′ SIG | ns | ns |
| standby follow / ngày | 0 | 33,0 | 35,1 |

## Đọc kết quả — ba phát hiện

### 1. Đây là kênh ĐẦU TIÊN cải thiện HỆ THỐNG có ý nghĩa thống kê

served **+1,03đp**, đơn hết hạn **−13,4/ngày**, tổng payout đội **+212k/ngày**, và HHI cung
**GIẢM** — tức capacity ledger làm đúng việc: đưa người tới chỗ thiếu **mà không tạo dồn cục**.
Mọi kênh trước đây (hồ sơ `07`, UPDATE-075) đều làm hệ thống đi ngang hoặc xấu đi.

### 2. Nhưng TÀI XẾ ĐÍCH vẫn lỗ — và phần lớn lỗ KHÔNG phải do kênh vị trí

B0 cho thấy advisor hiện trạng trên nền mới đã lỗ **−32.879đ** (tệ hơn −17.497đ ở nền cũ — nền
drop-bám-cầu hiệu quả hơn nên mỗi phút bị advisor kéo khỏi việc càng đắt, đúng mẫu đã thấy khi
sửa dispatcher). Phần biên của positioning quanh mức đó (−7k ở B1, +4k ở B2) **chưa kết luận
được** ở 30 seed. Thủ phạm chính vẫn là cấu trúc REST của shift_plan (hồ sơ `18-*`).

### 3. Mâu thuẫn cá nhân ↔ hệ thống mà ĐA-09 tiên đoán — nay có SỐ

Đội +212k/ngày nhưng người được đo −40k: kênh vị trí là **positive-sum cho hệ, tái phân phối
bất lợi cho người nghe lời**. Gini không tăng (ns) nên tổn thất không tập trung — nhưng "người
làm theo advisor chịu chi phí, cả làng hưởng served" là đúng câu hỏi fairness Cường đặt, giờ đo
được thay vì đoán.

## Phán quyết theo tiêu chí đã chốt

| # | Tiêu chí | B1 | B2 |
|---|---|---|---|
| 1 | Δpayout cá nhân > 0, CI loại 0 | ❌ | ❌ |
| 2 | served không giảm | ✅ (tăng SIG) | ✅ |
| 3 | hết hạn không tăng | ✅ (giảm SIG) | ✅ |
| 4 | Gini không tăng | ✅ | ✅ |
| 5 | HHI không tăng [VETO] | ✅ (giảm) | ✅ |
| 6 | realism xanh | ✅ 617 passed | ✅ |
| 7 | tắt cờ = cũ | ✅ (test bit-identical) | ✅ |
| 8 | km rỗng không tăng [VETO] | ❌ +0,72đp | ❌ +0,70đp |
| 9 | đổi pin không tăng [VETO] | ✅ | ✅ |

⇒ **KHÔNG BẬT mặc định** (`positioning_overrides` giữ `off`): hỏng tiêu chí 1 và veto 8.

**Nhưng phải nói thẳng phần tinh tế**: veto 8 viết là *"km rỗng không tăng"* trong khi +0,7đp km
rỗng ấy chính là **cơ chế vận hành** của reposition — và nó ĐƯỢC TRẢ CÔNG ở tầng đội (+212k) và
tầng khách (−13 đơn chết/ngày). Tiêu chí như đang viết trừng phạt mọi kênh vị trí về nguyên tắc.
Ba lựa chọn cho Cường (ghi PENDING-REVIEW Q-10):

- **(a)** giữ nguyên veto ⇒ kênh vị trí off vĩnh viễn theo định nghĩa;
- **(b)** đổi veto 8 thành *"km rỗng chỉ được tăng nếu tổng payout đội tăng SIG cùng lúc"*
  (empty-km-phải-tự-trả-tiền);
- **(c)** hoãn quyết định, đánh gốc trước: sửa cấu trúc REST của shift_plan (thủ phạm −33k) rồi
  đo lại — khi cá nhân hết lỗ vì REST, tiêu chí 1 mới có cửa.

Khuyến nghị của agent: **(c) rồi (b)** — không bật gì hôm nay, không vặn tiêu chí giữa trận.

## Kiểm chứng

30 seed CRN · `crn_ok` theo thiết kế (A dùng lại, cùng seed mọi nhánh) · suite trước đo:
**617 passed / 5 skipped** · artifact JSON đầy đủ per-seed để tái kiểm.

## Visual verification

- **Status:** `BLOCKED` — gộp với UPDATE-083: Replay seed 1000, bật `wait_only`, xem
  `standby_alloc`/`standby_followed` + tab Bản đồ H3 (phân bố cung có trải đều hơn không — HHI
  giảm phải NHÌN thấy được).

## Adversarial self-review / flaws found

1. **Tài xế đích là P4 được chào nhiều nhất** (`pick_target`) — không đại diện người ít đơn;
   người rỗi nhiều có thể HƯỞNG positioning thay vì chịu chi phí. Chưa đo per-archetype.
2. **B1 tệ hơn B2 ở payout cá nhân là NGƯỢC trực giác** (wait_only bảo thủ hơn mà lỗ sâu hơn) —
   ở 30 seed khoảng cách B1−B2 chưa kết luận được; KHÔNG xếp hạng.
3. **km rỗng share tăng nhưng tổng km cũng đổi** — share là tỷ lệ, chưa tách "thêm km rỗng" với
   "bớt km có khách"; artifact có đủ số để tách nếu cần.
4. **standby follow ~33/ngày cho cả đội** là thấp (90 tài xế × nhiều bucket) — trần + điều kiện
   candidates (không kéo người đang ở ô còn trần) đang giữ kênh rất tiết chế; đó là thiết kế,
   nhưng cũng có nghĩa hiệu ứng đo được đến từ số lần can thiệp khá nhỏ ⇒ hiệu ứng/lần can thiệp
   lớn — đáng nhìn kỹ hơn.
5. **Chưa chạy ≥100 seed** cho bất kỳ so sánh biến thể nào.

## ⏳ Nhắc PENDING-REVIEW

`V-01..V-16` + **V-17 mới** (visual b3/b4) chưa ai xem. **Q-10 MỚI: chọn (a)/(b)/(c) cho veto km
rỗng** — quyết định sản phẩm, agent không tự chọn. Q-03, Q-04, Q-07, B-02 vẫn treo.
