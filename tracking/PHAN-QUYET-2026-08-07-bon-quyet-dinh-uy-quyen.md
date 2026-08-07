# PHÁN QUYẾT 2026-08-07 — bốn quyết định Cường **uỷ quyền**, có quyền phủ quyết

> Cường 2026-08-07: *"duyệt plan, thi công đi, về việc cần quyết tôi cho bạn quyền phủ quyết,
> reasoning thêm 1 vòng"*.
>
> Tôi ghi lại **lập luận đầy đủ**, không chỉ kết luận — vì uỷ quyền không có nghĩa là khỏi giải
> trình, và vì Cường phải lật lại được bất kỳ mục nào bằng cách bác đúng cái tiền đề tôi dùng.

---

## Q-D — *"thời gian chờ / đổi pin có tính là nghỉ phục hồi?"* → ❌ **KHÔNG. TÔI PHỦ QUYẾT.**

**Lập luận.** Đề nghị này nghe như một tinh chỉnh định nghĩa, nhưng hệ quả kỹ thuật là **làm yếu
một lan can MỘT CHIỀU**:

- `rest_min_total` là đại lượng mà `health_guardrail_flags` dùng để tố giác *"advice đang ăn vào
  nghỉ"* (tolerance 2%). Cho phép đếm thời gian **chờ khách** và **đổi pin** vào đó sẽ **thổi
  mẫu số** — đúng chiều làm cổng **im** khi advisor thật sự ăn vào nghỉ.
- `DRIVE_BREAK_MIN` đã cố ý loại swap 1–2′ khỏi *"hồi phục"* (`sim_metrics.py:336-338`), và lý do
  ghi rõ: *"swap pin thì KHÔNG (không phải hồi phục)"*. Đề nghị này **đảo ngược một quyết định
  đã có lý lẽ**, không phải lấp một chỗ trống.
- Ngồi chờ khách **không phải nghỉ**: tài xế vẫn ở trên xe, vẫn trong trạng thái sẵn sàng. Chính
  `continuous_work` định nghĩa `work_span` = *"nghỉ→nghỉ, GỒM đứng chờ khách"* — tức repo đã
  phán xử điều này một lần rồi.

**Ranh giới:** đây là `POLICY_LOCKED` + `CLAUDE.md §1.2b`. Kể cả có quyền quyết, hướng *"nới lan
can sức khoẻ"* là hướng tôi sẽ luôn từ chối tự làm — nó **mua Δ bằng cách xoá cái đo tác hại**.

**Điều kiện lật:** có dữ liệu sinh lý thật (không phải suy luận) cho thấy thời gian chờ tại chỗ
có giá trị hồi phục đo được. Khi đó vẫn phải qua `policy_locks` + Cường duyệt tường minh.

---

## Q-B — S5 / S6 / S8 + `AdvisorPipeline`: khai tử hay nối stack? → **ba số phận KHÁC NHAU**

Bản đồ gộp ba solver này thành một câu hỏi. Đọc kỹ thì chúng **không cùng loại**:

| solver | phán quyết | vì sao |
| --- | --- | --- |
| **S8** giải trình phạt | ❌ **NGOÀI SCOPE — không nối, không đo** | `CLAUDE.md §1`: *"Luồng giải trình vi phạm thuộc **dự án khác** — file drawio đã xoá khỏi repo theo yêu cầu Cường (D-006)"*. Đây **không phải quyết định mới của tôi**; nó đã được quyết, và việc S8 còn nằm trong repo mới là cái sai |
| **S5** khoán tuần | ⚠ **TUYÊN BỐ KHÔNG THỂ KIỂM** — không nối | Sim **không có** cơ chế khoán tuần/clawback (`grep 'weekly_quota\|khoan\|clawback' src/gsm_sim/` = **0**) ⇒ **ĐA-08 không chạy được** bằng twin-world hiện tại. Theo `specs/real-data/data-contract-counterfactual.md §4`, cách trung thực là **xếp KHÔNG THỂ KIỂM**, không phải *"nối dây rồi tính sau"* |
| **S6** mini-task | ⏸ **HOÃN tới sau khi sửa cost model** | World **đã có** mission ⇒ đo được bằng ĐA-08 **ngay**. Nhưng bật nó trước khi sửa cost model là **lặp lại nguyên văn `station_choice`**: một kênh nghe hợp lý, đo ra FAIL, tốn một vòng đầy đủ để biết |
| `AdvisorPipeline` | 📄 **GIỮ, nhưng DÁN NHÃN** (Cycle 2) | `pipeline.py:59` nhận `solver_reports` **TỪ CALLER** ⇒ thêm tên vào `router.py` **KHÔNG** làm solver chạy. Nguy hiểm nằm ở chỗ người đọc tưởng ngược lại ⇒ sửa bằng **docs**, không bằng code |

**Điều chung — và là lý do tôi không nối cái nào:** nối một solver **không kiểm chứng được** vào
stack advisor vi phạm ranh giới `CLAUDE.md §5` (*mọi số hiển thị cho tài xế đến từ component
**có thể kiểm chứng***). *"Có mặt trong stack"* sẽ được đọc là *"đã được kiểm"*.

---

## Q-A — mở lại ĐA-07 để đo lại `shift_plan`? → ✅ **CÓ, nhưng là ĐO LẠI, KHÔNG phải lật**

**Lập luận.** Bằng chứng của ĐA-07 (28/07) và E5 (29/07) sinh ra khi `points_band_size = 15`, ở
đó `add_pts // 15 = 0` mọi giờ thường ⇒ **mốc thưởng không bao giờ vào giá trị Bellman** ⇒ DP lập
lịch **như thể không có thưởng**. Sửa 06/08. Cả hai vế bằng chứng (*"không giá trị"* và *"có
hại"*) đều đến từ solver đó.

**Nhưng — và đây là vòng reasoning thứ hai mà Cường yêu cầu — CHƯA đo ngay được.**
Bản đồ đo trên **shape sản phẩm thật**: `S2-3` (trần `cap_trips`) **BIND 88,6%**. Nếu trần chi
phối 88,6% quyết định thì đo S2 lúc này trả lời câu *"S2-với-một-cái-trần-đang-siết có giá trị
không"*, **không phải** *"S2 có giá trị không"*.

> ⇒ Đo bây giờ là **lặp lại đúng sai lầm ta đang đi sửa**: ra một bản án mới về một solver **vẫn
> đang bị chặn ở chỗ khác**.

**Phán quyết:** ĐA-07 **giữ nguyên hiệu lực** (kênh vẫn TẮT). Cycle 10 **được duyệt** nhưng
**phụ thuộc cứng**: sau `Cycle 3` ✅, `Cycle 4` ✅, **và** sau khi `S2-3` được xử lý.
**Falsifier ghi trước:** nếu Δ vẫn ns thì ĐA-07 **được củng cố bằng bằng chứng sạch** — đó cũng
là kết quả tốt, và tôi sẽ báo đúng như vậy.

---

## Q-07 — dispatcher `k=6` vs `k=8` → ⏸ **GIỮ k=6 tới khi xong Cycle 9**; mặc định sau đó là **k=8**

**Lập luận.** Ba dữ kiện kéo về hai hướng ngược nhau:

**Kéo về k=8:** n=100 paired CRN — k=8 trội **cả 7 chỉ số, tất cả SIG**, kể cả Gini **giảm** và
veto sức khoẻ **giảm**. Chặn duy nhất là **0,14đp** dung sai trung-thành-hồ-sơ của P7.

**Kéo về khoan đã:**
1. `k` là thuộc tính của **THƯỚC ĐO**, không phải của sản phẩm — nó không tới tay tài xế. Giá trị
   của nó hoàn toàn **công cụ**: làm sim đo đúng hơn.
2. Ta **đang giữa chừng sửa thước** (Cycle 3 ✅, 4 ✅, 8 chưa). Đổi `k` lúc này **dịch mọi baseline**
   trong khi các cổng còn đang thay đổi ⇒ không tách được nguyên nhân nếu số đổi.
3. Thế giới này có một **khuyết tật tiêm vào có chủ ý** (đội 74→90 để bù shortlist hẹp) và
   **tương tác giữa nó với `k` chưa ai đo** (A2 vẫn **n=5**). Sửa `k` mà không hạ đội cùng lúc là
   sửa một nửa của một cặp bù trừ.

**Phán quyết:** giữ `k=6`. **Trigger xét lại:** sau `Cycle 9` (liều/trần kênh đang ship) **và**
khi có `A2` ở n=100 + **HHI cung theo ô**. **Mặc định lúc đó là ADOPT k=8**, trừ khi HHI hoặc
cổng tầng 5 (nay đã hết vùng mù) tố giác tác hại.

⚠ **Cái giá tôi chấp nhận, nói thẳng:** mỗi ngày giữ k=6 là **32,6 đơn chết/ngày** trong mọi phép
đo, và — quan trọng hơn — giá trị advisor đo trong thế giới đó **có thể bị THỔI LÊN**, vì một
phần Δ của advisor là *"cứu lại phần cung bị chính shortlist hẹp lãng phí"*. Tôi chọn trả giá này
**có thời hạn** thay vì đổi thước giữa lúc đang hiệu chỉnh thước.

---

## Nguyên tắc tôi áp cho cả bốn (để Cường soi được cách tôi quyết)

1. **Không mua Δ bằng cách xoá/nới cái đo tác hại** (Q-D).
2. **Không nối thứ không kiểm chứng được vào đường tới tài xế** (Q-B).
3. **Không ra bản án mới khi thước còn hỏng ở chỗ khác** (Q-A) — đây đúng là bài học của chính
   vụ ĐA-07.
4. **Không đổi thước giữa lúc đang sửa thước** (Q-07).

Ba trong bốn phán quyết là **hoãn hoặc từ chối**. Tôi ghi nhận điều đó và tự soi: có phải tôi
đang tránh né không? — Không: mỗi mục có **trigger cụ thể** và **hành động mặc định** đã ghi
trước, nên không mục nào rơi vào im lặng. Mục duy nhất tôi **chủ động đóng** (S8) là mục đã có
quyết định cũ của Cường phủ lên.
