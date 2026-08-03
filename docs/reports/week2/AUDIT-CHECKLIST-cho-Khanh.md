# Checklist audit cho Khánh — Week 2 Report

Chào Khánh, đây là tài liệu để bạn soi lại bản báo cáo gửi mentor trước khi chốt. Mình đã đối
chiếu toàn bộ repo (24 subagent, 494 phát hiện có nguồn) và verify từng con số trong
`SPRINT-1-MENTOR-SUBMISSION.md` của bạn. Kết quả chia làm bốn phần dưới đây.

**Cách dùng:** tick ✅ nếu đồng ý, ❌ nếu bạn thấy mình sai (kèm lý do — rất có thể mình sai, mình
đã tự bắt được 2 lần trong ngày hôm nay).

---

## Phần 1 — 🔴 Ba điểm trong doc của bạn mình đề nghị SỬA

### 1.1 `+6.016đ` — con số này KHÔNG tái lập được nữa

| | |
| --- | --- |
| **Doc của bạn viết** | *"Snapshot `wait_only`, 100 seed: Payout **+6.016đ/người/ngày**; served +1,74 điểm phần trăm; đơn chết −23,4"* |
| **Bằng chứng phản đối** | `tracking/updates/UPDATE-113-sua-thuoc-adherence-positioning.md:109` ghi nguyên văn: *"CI [2.854, 5.033] **không chứa +6.016** của UPDATE-087 ⇒ **không tái lập được trần điểm cũ**"* |
| **Chuyện gì đã xảy ra** | Thước đo tỷ lệ nghe lời bị sai (trộn *"tài xế đồng ý"* với *"hệ thống thực thi được"*). Sau khi sửa thước, **mọi số E10 phải đo lại** và giảm xuống |
| **Số hiện hành** | `B_oracle` **+3.939đ** [2.854; 5.033] · `B_hist` **+3.401đ** · `B_real` **+3.126đ** |
| **Đề nghị** | Dùng **+3.126đ** (arm `B_real`, sát thực tế nhất) hoặc **+3.939đ** (trần). Nếu vẫn muốn nêu +6.016 thì **phải** kèm câu "vòng đo trước, không tái lập được sau khi sửa thước" |

⚠ Đây là điểm mình lo nhất: mentor mà mở artifact ra đối chiếu thì con số +6.016 sẽ không khớp
với `41-e10-diff.json`, và file đó còn **tự ghi** `"ref_update087": 6016` để đánh dấu là số cũ.

- [ ] Khánh đồng ý sửa
- [ ] Khánh không đồng ý, vì: ................................

### 1.2 `−17.310đ` — đúng số, nhưng thiếu ngữ cảnh quan trọng

| | |
| --- | --- |
| **Doc của bạn viết** | *"Snapshot cấu hình cũ, 30 seed: Payout −17.310đ/ngày, CI95 [−29.294; −5.820]"* dùng làm counterexample |
| **Vấn đề** | Số đúng, nhưng nó là của cấu hình có **`shift_plan`** — kênh **đã bị ĐA-07 TẮT vì đo ra có hại**. Đọc không kỹ sẽ tưởng đây là kết quả của sản phẩm hiện tại |
| **Đề nghị** | Giữ nguyên số, thêm một câu: *"cấu hình này đã bị loại bỏ; kênh `shift_plan` hiện TẮT"* |

- [ ] Đồng ý  - [ ] Không, vì: ................................

### 1.3 `ui/README.md` — ba chỗ đã lỗi thời

| Chỗ | Vấn đề |
| --- | --- |
| Mô tả cấu trúc `UIUXgsm/` | Không còn đúng — chính README dòng 215 đã tự đính chính *"gốc thật của UI trong repo này là `ui/`"* |
| *"100% Green Coverage"* (dòng 42) | Đây là câu marketing, không phải số đo. Mentor có thể hỏi "đo bằng gì?" |
| Danh sách 5 tab (dòng 90) | README ghi *"Xanh Now, Điều hướng, Thu nhập, Xe & Pin VinFast EV, Cài đặt"*; code Flutter thật là *"Xanh Now, Chọn điểm đến, Chuyến của tôi, Mua xe VinFast, Cài đặt"*. Ảnh bạn gửi cũng cho thấy nav thứ hai |

Ghi chú thêm: Track UI web có nav **khác** app Flutter (web: *Xanh Now · Thu nhập · Chuyến của tôi
· Xe & Pin · Cài đặt*). Hai mặt đang lệch nhau — mình đã đưa việc đồng bộ vào mục tiêu tuần 3.

- [ ] Đồng ý  - [ ] Không, vì: ................................

---

## Phần 2 — ✅ Những gì bạn trích ĐÚNG (đừng sửa oan)

Mình kiểm từng cái và chúng chính xác:

| Nội dung trong doc của bạn | Kiểm chứng |
| --- | --- |
| **H3 resolution 9, ~85 cells lõi**; res 8 để tổng hợp | ✅ `configs/pilot_dongda.yaml:16-17` — comment ghi đúng *"lưới vận hành ~85 cells lõi"* |
| **1.200 đơn/ngày** | ✅ `configs/pilot_dongda.yaml:32` |
| **9 solver** | ✅ đếm thật: 9 file trong `src/gsm_core/solvers/` |
| **50 actors → 90 actors** | ✅ `specs/simulation-pilot-world.md:1` là spec lịch sử (50), có override 2026-07-22; hiện hành 90 |
| **Dispatch: served 0,761 → 0,764 · đơn hết hạn 233 → 228 · pickup 1,04 → 0,98 km · runtime 2,9 → 2,7s (12 seed)** | ✅ `UPDATE-080-dispatch-tang2-hungarian-va-nhan-soc.md` |
| **OSRM là thật** | ✅ và còn hơn bạn viết: có **1 lời gọi API runtime** (`POST /api/v1/routing/calculate`) **cộng** ma trận cache offline cho hệ số đường |
| **Batch matching Hungarian, greedy giữ làm baseline/fallback** | ✅ `src/gsm_sim/dispatcher.py` — fallback khi `n_orders × n_drivers > 200.000` |
| **Ranh giới sản phẩm** (không tự nhận/từ chối cuốc, không thay dispatch) | ✅ và có bằng chứng mạnh: `dispatcher.py` 151 dòng, **0 lần** tham chiếu `advice/advisor/bridge` |

Phần **kiến trúc và cách phân vai** (§4 doc của bạn: data → optimization → agent → safety → UI →
driver) mình thấy đúng và đã giữ nguyên tinh thần đó trong báo cáo mới.

---

## Phần 3 — ❓ Hai câu hỏi mình cần bạn trả lời

### Q1. Text trong ảnh chat "Trợ Lý Xanh AI" đến từ đâu?

Ảnh bạn gửi có bot trả lời: *"Hôm nay anh mới chạy 5 cuốc, thu nhập 350k, còn thiếu 60 điểm nữa –
tầm 4 cuốc nữa là tới mốc thưởng 30k đó."*

Mình đã verify được rằng **đường chạy chính thống** là đúng ranh giới: `ui/backend/app/adapters/
advisor.py` dựng input rồi gọi **solver S1 thật** (`bonus_feasibility.solve()`), mỗi số mang field
`source`. Nhưng `home_screen.dart:75` ghi `'Trợ Lý Xanh AI (Stitch)'` — nên mình **không chắc** text
trong ảnh là từ solver hay còn là bản dựng giao diện từ Stitch.

**Câu hỏi:** ảnh đó là số thật từ solver, hay là mockup? Mình cần biết để viết đúng — hiện trong
báo cáo mình đã ghi trung thực là *"cần Khánh xác nhận"*.

**Trả lời:** ................................................................

### Q2. Flutter gửi `scenario_id` và `seed` mà backend bỏ qua — chủ ý hay drift?

`ui/driver_app/lib/services/api_service.dart:10,24` gửi `scenario_id='default_hcm'` + `seed` tới
`/api/v1/map-context` và `/api/v1/driver/state`. Nhưng router `/driver/state` hiện nhận
`driver_id`/`date` và **bỏ qua** hai tham số đó (`driver.py:27-35`). `ui/simulator_ui/app.py` cũng
gửi tương tự và cũng bị bỏ qua.

**Câu hỏi:** đây là contract cũ chưa dọn, hay bạn đang giữ có mục đích? Nếu là cái đầu thì mình đưa
vào tuần 3 để dọn.

**Trả lời:** ................................................................

---

## Phần 4 — ⚠ Danh sách "dễ báo sai" khi viết cho mentor

Đây là 14 cái quan trọng nhất, lọc từ 309 cảnh báo mà vòng đối chiếu sinh ra. Mình đã áp hết vào
báo cáo mới, nhưng liệt kê ra để bạn kiểm và để lần sau cả hai đều biết:

| # | Đừng viết | Viết đúng là |
| --- | --- | --- |
| 1 | "Dự án có 809 test / suite 865" | **Số đo hôm nay: 1.000 test passed (935 + 65)**, collected 1.004. `CLAUDE.md:32` đang stale |
| 2 | "Dự án có 1.000 test" | *1.000 test **passed*** — còn 4 test skip (GSM chưa cấp cột cho 4 bảng) |
| 3 | "CI đã chạy" hoặc "chưa có CI" | `ci.yml` **có thật** (61 dòng, 3 job) và **đã ở trên `origin/main`**, nhưng header tự khai *"CHƯA ACTIVE"* ⇒ nói: **đã viết và đã push, chưa xác nhận chạy** |
| 4 | "Tầm pin 60 km / 110 km" | Hai số đó **đã bị xoá khỏi config** hôm 01/08 vì lệch với công thức. Đúng là **62,5 km** (swap) và **117,6 km** (charge) |
| 5 | "Sim gộp metrics theo bucket 15 phút" | Sim gộp theo **GIỜ** (`t_min // 60`, 4 chỗ). Cờ 15′ đã bị xoá vì nói sai hành vi |
| 6 | "Guardrail 5 tầng đã hoạt động từ trước" | Tầng 5 **chưa từng đo được gì** cho tới 01/08 — có hàm nhưng chưa nối nguồn (`D-M3-13`) |
| 7 | "3 cổng mới bảo đảm không còn lỗi loại đó" | Cả 3 cổng là **phân tích tĩnh** ⇒ không thấy đường chạy động (`getattr`, dict-dispatch). Phải khai vùng mù |
| 8 | "7/7 deriver sạch" | Đọc là **7 deriver *có* `t_now`** — cổng không phủ `derive_session_summary_input_l1r` |
| 9 | "6 lỗi rò rỉ đã gây sai số cho tài xế" | `from_l1r` **chưa được import ngoài tests** ⇒ chưa số nào đã công bố bị ảnh hưởng. Là **bom hẹn giờ**, không phải đám cháy |
| 10 | "UI và sim dùng cùng một phép đo adherence" | Hai đường **hiện chưa join được**; phải dùng hai tên: `decision_adherence` và `event_adherence` |
| 11 | "Đã bỏ neo giờ cố định cho card" | Server tính theo **pha ca**, nhưng `ui/web/js/cards.js:9` **vẫn hard-code** 09:00/14:00/21:30 |
| 12 | "A/B đo đúng sản phẩm sẽ ship" | **`Q-14` còn mở**: UI chỉ chạy **1/9 solver** ⇒ A/B đang đo một sản phẩm khác |
| 13 | Gọi Track UI / dashboard là "DONE" | `DONE-CODE` / `WAITING-VERDICT` — 20 mục review còn mở, gồm 5 gate visual |
| 14 | Trích cước demo như bảng giá GSM | Cước là `sim-policy-v0` **MOCK**; công thức cũ `km × 24000` từng lệch **~4,6×** policy thật và đã được sửa |

---

## Phần 5 — thứ mình tìm được vào đúng hôm nay, bạn nên biết

Khi smoke end-to-end để chụp ảnh, mình phát hiện **`D-M3-17`**: UI tự tính tầm pin bằng
`soc × 1,1` cho **mọi** tài xế, trong khi engine cho **62,5 km** (đội đổi pin) và **117,6 km**
(đội sạc). ⇒ tài xế đội đổi pin đang thấy số **thổi 1,76 lần**. Endpoint legacy
`/api/v1/driver/state-synthetic` còn dùng `soc × 3,2` = **5,1 lần**.

Suite 1.000 test không bắt được, vì **không có test nào so UI với engine**. Đã ghi mã, xếp việc
đầu tiên của tuần 3. Mình nêu ra đây vì phần `vehicle_range_km` thuộc mảng UI của bạn — nếu bạn
biết lý do chọn hệ số 1,1 thì cho mình biết trước khi sửa.

---

## Ký tắt

| Phần | Người kiểm | Trạng thái |
| --- | --- | --- |
| Phần 1 (3 điểm cần sửa) | Khánh | ⬜ |
| Phần 2 (đúng, không sửa) | Khánh | ⬜ |
| Phần 3 (2 câu hỏi) | Khánh | ⬜ |
| Phần 4 (danh sách dễ báo sai) | Khánh | ⬜ |
| Phần 5 (`D-M3-17`) | Khánh | ⬜ |
| Bản PDF cuối | Cường | ⬜ |
