# CẦN CƯỜNG DUYỆT — hàng đợi quyết định (2026-08-06)

> Cường: *"doc lại điều cần tôi duyệt nếu nó không ảnh hưởng các kế hoạch khác"*.
> File này gom **mọi thứ đang chờ Cường** vào một chỗ, mỗi mục ghi rõ: **cần gì · vì sao phải là
> Cường · nó CHẶN cái gì · tôi đề xuất gì · nếu Cường nói KHÔNG thì sao**.
> Tôi **vẫn tiếp tục** những việc không phụ thuộc các mục này (ghi ở §5 cuối file).
> Chi tiết visual vẫn ở `PENDING-REVIEW.md`; đây là bản tổng hợp để quyết nhanh.

---

## 1. 🔴 DUYỆT PLAN — Cycle `D-M3-20`: làm sạch arm đối chứng của `rest_window`

| | |
| --- | --- |
| **Cần gì** | Duyệt plan cho một cycle **đổi hành vi sim** (CLAUDE.md §4b bắt buộc xin duyệt trước khi implement) |
| **Vấn đề** | `advice_bridge.py:916` gọi `alt_action_fn` **TRƯỚC** cadence (`:922`) và coin (`:933`); hàm đó rút RNG thật (`behavior.py:228`) trên **stream chung**. Arm A (kênh tắt) return ở `:907` **trước** dòng 916 ⇒ **0 draw**. Hệ quả: mỗi quyết định **bị nén hoặc bị từ chối** — lẽ ra phải **bit-identical** với arm A — vẫn làm lệch chuỗi ngẫu nhiên của **cả 90 tài xế** |
| **Nghiêm trọng tới đâu** | ✅ **Cập nhật 2026-08-07 — vòng 2 có artifact và số MẠNH HƠN NHIỀU.** `pb-02` dựng **arm NULL đúng nghĩa** (kênh BẬT, coin **luôn từ chối** ⇒ **đúng 0 can thiệp**), **20 seed × 3 ngày × 90 actor**: SD nhiễu `rest_min_total` **157,5′** · `work_span_p90` **22,4′** · payout đội **318.718đ**; tỷ số **SD_nhiễu / SD_tổng-quan-sát = 1,12 · 1,22 · 1,05** ⇒ **nhiễu trôi-stream MỘT MÌNH giải thích (hơi vượt) TOÀN BỘ độ phân tán của Δ post-FIX**, và cả ba điểm ước lượng của UPDATE-142 nằm **sâu trong một SE của nhiễu**. Arm A = **0 draw ở 20/20 seed**; fingerprint **A ≠ B_null 38/40** ngày-arm. Độ lớn ở arm thật (`pb-01`, coin=NEVER): **−1.625.279đ / −34 cuốc / +519′ rest** = **1,2–2,4% payout đội** |
| **🟢 ĐÃ ĐƯỢC DE-RISK** | `pb-02` cũng đo: **A == B_fix ở 60/60 ngày-arm** ⇒ **fix khôi phục bit-identity**. Nghĩa là acceptance chính của cycle này **đã được chứng minh đạt được trước khi tôi viết một dòng code** — rủi ro thi hành thấp hơn hẳn lúc tôi soạn plan |
| **Chặn cái gì** | (a) **Mọi Δ mới của `rest_window` không đáng tin**; (b) bộ số acceptance của **D-M3-04-FIX mà chính tôi báo "passed" cho Cường phiên này PHẢI ĐO LẠI** |
| **Tôi đề xuất** | Tách `consider_relocate` hai pha: pha **tất định** (có ô tốt hơn không — 0 draw, dùng cho cổng `no_alt_action`) + pha `p_move` rút bằng **keyed hash** như `adherence_coin` (tiền lệ DET-01/DET-02 của repo), **giữ nguyên vị trí và xác suất** ⇒ chỉ sửa vệ sinh RNG, **không** đổi ngữ nghĩa kênh |
| **Acceptance** | Test đỏ-trước: kênh **BẬT** + ép **mọi coin từ chối** ⇒ `fingerprint_actors` **IDENTICAL** arm A (hiện chắc chắn ĐỎ). Mũi 2: cadence nén ⇒ cũng IDENTICAL. Bất biến cũ: kênh TẮT ⇒ IDENTICAL (5 seed). Rồi **đo lại** acceptance D-M3-04-FIX 30 seed, **báo CẢ HAI bộ số trước/sau** |
| **Nếu KHÔNG duyệt** | Kênh `rest_window` vẫn TẮT nên **không có số ship nào bị nhiễm** — nhưng phải ghi `WAITING-VERDICT` và **cấm** trích bất kỳ Δ nào của kênh này, kể cả số cũ |

## 2. 🔴 VISUAL — hai gate đang BLOCKED

### V-32 · UPDATE-167 (MỚI, chặn việc gọi Cycle B0 là hoàn thành)
Card **F0/F1 đổi nội dung THẬT**: sửa lệch đơn vị mẫu số S1 ⇒ đo trên 3.000 ca (MOCK): số ca *"còn với
được mốc"* đi **29,9% → 52,2%**. Nhiều tài xế trước nhận *"không với tới mốc"* nay nhận *"còn với được
mốc thưởng…"*; card sát biên thêm **một câu** *"mốc này sát biên… đừng dồn hết giờ vào nó"*.
**Xem:** `http://127.0.0.1:8000/app/` → 🤖 Trợ Lý Xanh, thử 10h/14h/17h/20h trên 2–3 tài xế.
**Câu hỏi cần Cường trả lời:** *lời khuyên nay có **hứa quá** không? Câu cảnh báo sát biên đọc có tự
nhiên không?* ⚠ **Không gộp vào V-31** — đây là đổi nội dung, không phải đổi nhãn.

### V-31 · UPDATE-151..160 (visual gộp của chương trình E1–E5)
Ba màn ~10′ — chi tiết bước bấm ở `PENDING-REVIEW.md`. Server **đang sống**: dashboard `:8501`, web `:8000/app/`.

## 3. ❓ QUYẾT ĐỊNH CHÍNH SÁCH — ba mục, mục đầu là gốc của nhiều thứ

### 3.1 Amendment **ĐA-08** cho kênh phía-CUNG (⭐ quan trọng nhất, sinh từ root-cause verdict §5)

> ✅ **Cập nhật 2026-08-06 sau khi chạy falsifier F1:** phần *cơ chế* của verdict **đứng** (95% lượt vào
> hai ô hút là do luật leo-dốc-theo-niềm-tin — `demand_seek` 123 vs deadhead 2 vs go_online 4), nhưng
> phát biểu *"đúng hai ô, do tính địa phương chứ không do nhiễu"* **bị làm yếu** (dưới nhiễu thực tế
> attractor vỡ thành 40–78 cái). **Điều này KHÔNG đổi kết luận §5** — cơ sở của §5 là các số đo độc lập
> (33,6% online đã là idle; trung vị khoảng cách đơn-chết→người-rảnh 2,575 km; đội cố ý dư cung), không
> phụ thuộc danh tính hai ô. Chi tiết: `research/audit/2026-08-06-root-cause-idle/f1-basin-map-KETQUA.md`.
**Phát hiện:** trong world hiện tại, **cổng payout của ĐA-08 là BẤT KHẢ THẮNG về cấu trúc** cho mọi kênh
chỉ **giải phóng thời gian** tài xế. Lý do đã đo: 33,6% thời gian online **đã** là idle; trung vị khoảng
cách từ đơn-đang-chết tới người-rảnh-gần-nhất là **2,575 km** (vượt **cả** bán kính chào đơn 2,22 km lẫn
ETA 11′); và world **cố ý dư cung** (đội 74→90 để kéo `served_rate` lên 0,797, có văn bản trong config).
⇒ *"phút rảnh thứ 143 và thứ 151 có cùng giá trị biên: ≈ 0"*.
**Đề xuất:** kênh phía-cung được chấm bằng **metric thời gian/hàng đợi** (đã SIG: `swap_wait −3,6′`,
`charge_p90 −39′`, `station_hhi −0,056`) **+ một cổng "không gây hại tiền"**, thay vì cổng *"phải tăng
tiền"* — cho tới khi world có **cầu co giãn** hoặc **đội xe được calibrate lại**.
**Chặn:** đây đúng là **điều kiện reopen (c)** đã ghi sẵn của `D-E4-06` (`station_choice`), và nó quyết
định mọi kênh phía-cung tương lai có thể được duyệt hay không.
**Nếu KHÔNG duyệt:** giữ nguyên ĐA-08 ⇒ `station_choice` và họ kênh thời-gian **đóng vĩnh viễn**; phải
nói thẳng điều đó thay vì cứ đo lại rồi lại ns.

### 3.2 **Q-07** — ghép đơn ĐÚNG vs trung thành ARCHETYPE
Vòng lọc ứng viên hiện hẹp hơn ràng buộc thật: hex **2,22 km** vs bán kính ETA-khả-thi **3,14 km** ⇒
**14,4% (≤29,4 đơn/ngày)** chết **thuần** vì lọc hình học; sweep 12-seed sẵn có trong config **hội tụ**:
k=6→233, k=7→211, k=8→196, k=12→195 đơn hết hạn ⇒ **−37 đơn/ngày, bão hoà ở k≈8**.
**Nhưng** nới lên k=7 làm `accept_base` của P7 lệch **−0,053 > dung sai 5pp** ⇒ `test_sim_realism` đỏ.
**Cần Cường chọn:** ghép đơn đúng hơn, hay giữ trung thành hồ sơ archetype? **Chặn:** fix `B1`.

### 3.3 `REVIEW-092-4` (cầu co giãn) / `D-SIM-01` (mở rộng zone) / cỡ đội
Đây là **gốc** của 3.1: chừng nào world còn cố ý dư cung để đạt `served_rate`, **mọi** kênh giải phóng
thời gian sẽ **luôn** cho payout ns. Không phải lỗi của kênh nào cả. Cần Cường quyết có mở nhánh này.

## 4. Đề xuất cần duyệt trước khi làm (không gấp)

| Mã | Nội dung | Vì sao cần duyệt |
| --- | --- | --- |
| `D-ADV-01` vế **stagger** | Thêm vế khoảng cách vào cost matrix S4 — đo được: **56%** lượt gán bị stagger, **88%** đi **xa hơn** ô-còn-trần-gần-nhất (median **+1,68 km**), thừa **112,8 km (+22%)** | Là **DESIGN-GAP có chủ đích** (docstring tuyên bố *"chống herding"*), **không phải bug** ⇒ mở rộng cost là **đề xuất**. Và nó nằm trên **kênh ĐANG SHIP** ⇒ **bắt buộc regate n=100 ĐA-08 đủ 9 dòng**. ⚠ 112,8 km là **slack cơ chế**, KHÔNG phải Δtiền — repo chưa có phép quy đổi km→đồng |
| `D-ADV-04b` | Đường **SIM** vẫn dùng quy ước mẫu số CŨ (day-average vào **cả hai** bucket) | Sửa phải đổi **schema `DriverMemory`** ⇒ đổi hành vi sim ⇒ regate ≥5 seed. **`Cycle B`/`shift_extend` PHỤ THUỘC nó** |
| `D-ADV-05` | Verdict `feasible` là **nhị phân trên median**, không CI ⇒ khi sát biên thì P(đạt) ≈ 50% mà report nói *"kịp"* | **Đổi ngữ nghĩa solver** + đụng test ghim ⇒ plan riêng. Liên quan trực tiếp câu hỏi V-32 (*"có hứa quá không?"*) |
| `D-ADV-02` | `shift_extend` mù cửa sổ điểm — **18,2%** lượt NÓI có cửa sổ kéo **hoàn toàn** ngoài khung điểm (toàn **P7:9 + P5:7**), điểm thực kiếm = **0**; thưởng "treo trước mắt" **510.000đ** cho những lượt có `E[Δthưởng] = 0` | Phụ thuộc `D-ADV-04b`. 🔴 **CẢ HAI phương án sửa của tôi đều THUA** (vòng 2 đo cả ba): `W_END` (bản tôi viết) còn **13,6%** — mất ~86% lượt nói, phần lớn vô căn · `W_NOW` (bản tôi "sửa lại") còn 52,3% **nhưng TẮT một lan can sức khoẻ** đang chặn **36,0%** lượt gọi · ✅ **`cổng-HẸP`** (dùng `_points_possible` trên cửa sổ kéo làm **cổng một chiều**) **cắt đúng 18,2% và giữ 72/88 nguyên vẹn** ⇒ **dùng bản này**. Thêm lỗi mới: **rò nửa đêm** (`shift_end=1440 → start_h=0.0` ⇒ walk báo điểm của NGÀY MAI; rò SỐ/LÝ DO, không rò quyết định) |

## 5. Việc tôi TIẾP TỤC ngay — không phụ thuộc mục nào ở trên

1. **`F1` basin-map niềm tin** (0 seed, chỉ đọc, phút): dựng đồ thị "leo dốc" trên 85 ô × 19 giờ theo
   đúng luật `behavior.py:210-229`, tìm **điểm hút + kích thước lưu vực**. ⚠ Đây là **FALSIFIER cho
   chính claim "bẫy niềm tin"** của verdict root-cause — **phải chạy TRƯỚC khi trích claim đó ra ngoài**,
   và nó có thể **giết** kết luận của tôi.
2. **Trả nợ tái tạo của hồ sơ phản biện**: 6/7 artifact `pb-*` **không tồn tại** (tôi lỡ chạy workflow
   trong plan mode nên agent bị chặn ghi) ⇒ hiện **cấm trích số** của chúng. Chạy lại + ghi artifact.
3. Ghi `mm-04`/`mm-07` thành JSON đúng khuôn (đang là bản `-STAGED.md` cứu từ plan-file).

Ba việc này **chỉ đọc/đo**, không đổi hành vi, không cần duyệt — và việc (1) có thể **đổi hẳn** nội dung
mục 3.1 nên làm trước là đúng thứ tự.
