# D-M3-04 BRIEF — bật multiday trong A/B để kênh `rest_window` thôi INERT

Ngày: 2026-07-31 (chốt acceptance 2026-08-01) · Trạng thái: **🟢 PHÉP THỬ CÓ ĐIỀU KIỆN — Cường bật
đèn 2026-08-03, luật quyết định đã KHOÁ trước khi đo** (xem khung ngay dưới). 3 câu hỏi thiết kế đã
được Cường duyệt 2026-07-31; acceptance đã sửa theo 5 lỗ UPDATE-114. Thi công còn lại =
`run_pair_multiday`, thuộc **Cycle B** riêng theo `CLAUDE.md` §4b.

> ## 🟢 CƯỜNG BẬT ĐÈN 2026-08-03 — nhưng nó thành PHÉP THỬ CÓ ĐIỀU KIỆN
>
> Chỉ thị: *"tôi duyệt D-M3-04, việc khuyên nghỉ nên defer thành khuyên mềm, không cho vào để đo
> hiệu quả trong sim"*. Hai vế này chỉ hai hướng ngược nhau, nên agent hỏi lại và Cường chốt:
>
> > *"**thử D-M3-04 trước, nếu có ý nghĩa thì giữ, không thì revert và khuyên mềm**"*
>
> ⇒ Phép đo **VẪN CHẠY**, nhưng kết quả của nó nay **quyết định** kênh `rest_window` ở lại bảng tiền
> hay chuyển thành **khuyên mềm** (nói vì đúng cho tài xế, 0 claim tiền, 0 đo mức nghe lời).
>
> 🔴 **Vì thế "có ý nghĩa" đã được định nghĩa TRƯỚC khi đo**, ở
> `d-m3-04-multiday-prereg-locked.json` → khoá **`luat_quyet_dinh`** (thêm 2026-08-03, chưa có số
> nào). Không làm thế thì đây đúng là họ lỗi `BUG-EVAL-ARGMAX`: đọc số rồi mới chọn cách diễn giải.
>
> | Kết quả | Hành động |
> | --- | --- |
> | Δ ngày 1..2 **dương SIG** + tầng 5 không suy giảm + không STOP nào bắn | **GIỮ** — kênh ở lại `MEASURED_TOPICS` |
> | Δ ≤ 0, hoặc ns, hoặc STOP bắn | **REVERT** — chuyển sang `SOFT_TOPICS`, bỏ mọi claim tiền |
>
> ⚠ Kỳ vọng đã khoá **2026-08-01** là **Δ ≤ 0** (world β=0) ⇒ **nhánh REVERT là nhánh dự đoán
> trước**. Nếu nó xảy ra thì phép đo **thành công** (mô hình dự đoán đúng), không phải kênh thất bại.
>
> Ranh giới **vô điều kiện** đã có hiệu lực ngay (không chờ phép đo này): **UI không có trace đồng
> ý/không đồng ý cho khuyên mềm** — xem `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` và
> `specs/advisor-objective-model-v2.md` §1.2c. Đã thi hành bằng cổng (UPDATE-128).

## Vấn đề — đã xác nhận bằng grep, không phải claim

`grep -n "multiday\|run_multiday" src/gsm_sim/parallel.py scripts/run_parallel.py` = **0 kết
quả**. Toàn bộ đường A/B chạy `run_once` (một ngày). Mà:

- `actor.planned_rest_hour` chỉ được nuôi ở `multiday.py:232` (chép từ `DriverMemory` sang
  actor khi mở ngày mới, d > 0);
- `advice_bridge.rest_window_hour` (:732) short-circuit theo chính `planned_rest_hour`;
- ⇒ trong mọi A/B single-day, `planned_rest_hour = None` ⇒ khung nghỉ phải tự suy từ S7 ⇒
  đo được **0/873 lần nói** (3 seed, coverage all).

**Hệ quả đã trả giá**: mọi câu *"advisor có 5 kênh"* trong artifact A/B thực chất là **4
kênh**; và `rest_window` — kênh duy nhất chạm ranh giới sức khoẻ — chưa từng được đo.

## Thiết kế (bản nháp, cần plan mode duyệt trước khi code)

### Đường chạy
`parallel.run_pair_multiday(cfg, seed, days, channels, coverage)`: chạy `run_multiday` HAI
lần cùng seed — arm A (`advice.enabled=false`) và arm B — rồi so **ngày ≥ 2** (ngày 1 chưa
có memory nên `planned_rest_hour` vẫn None; gộp nó vào là pha loãng chính thứ cần đo).

### Ba câu hỏi thiết kế phải chốt trong plan mode

1. ✅ **CHỐT (Cường duyệt 2026-07-31): (b) trung bình ngày 2..N, bootstrap theo SEED.**
   Bootstrap theo seed (không theo ngày) vì các ngày **không độc lập** — cùng actor mang
   `DriverMemory` sang. Lấy đơn vị resample là seed thì giả định độc lập mới đúng.
2. ~~**CRN còn giữ được tới đâu?**~~ ✅ **ĐÍNH CHÍNH 2026-07-31 — tôi lo SAI, vòng soi đo bác**:
   CRN **KHÔNG phân rã theo ngày**. Đo được: ngày 0 của hai arm **BIT-IDENTICAL** (fingerprint
   per-actor `a092e1f242905001` ở cả A và B), và `reset_for_new_day` **xoá sạch mọi carrier
   quỹ đạo** — SOC lấy từ dòng dùng chung `default_rng((seed, d, 0xDA1))`, `shift_*` khôi phục
   từ `base_shift`, `cell` về `home_cell` ⇒ **hỗn loạn không tích luỹ xuyên ngày**. Thứ duy
   nhất truyền qua là `DriverMemory` — tức **chính can thiệp cần đo**. ⇒ Bỏ mục "đo mức phân
   rã CRN"; multiday A/B sạch hơn tôi tưởng.
3. ✅ **CHỐT (Cường duyệt 2026-07-31): `days=3`, `n=100`.** Đủ để `planned_rest_hour` sống từ
   ngày 2 (đo được: decided 0/12/11 theo ngày 0/1/2), rẻ hơn 7 ngày, và giữ chuẩn n=100 —
   cùng cỡ mẫu với E10/E10b nên Δ so được với nhau.

### Bẫy đã biết (từ chính repo, không phải suy đoán)

- **`D-E10-01`**: `idle_streak_min` KHÔNG nằm trong `_DAILY_RESET_*` (`entities.py`) ⇒ ngày 2
  mở màn với streak tồn dư của cuối ngày 1. Phải sửa **TRƯỚC** khi đo multiday, kèm test,
  nếu không mọi số E10b/rest trong multiday sai từ phút đầu.
- ⚠ **ĐÍNH CHÍNH trần ≤29%**: con số 71,0% lan can là **số MỘT NGÀY**. Trong multiday, vòng
  soi đo được kênh chỉ hiện thực **2–5,7%** cơ hội và chặn chính là `at_window`/`window_past`,
  **không** phải lan can sức khoẻ. Trích 71% cho chế độ multiday là **trích sai chế độ**.
  Kỳ vọng vẫn giữ: Δ của `rest_window` NHỎ, và Δ nhỏ **không** phải lý do nới lan can.
- 🔴 **`CHANNEL_LADDER["rest_window"]` KHÔNG dùng được**: nó bật kèm `shift_plan: True` +
  `positioning_overrides: "off"` ⇒ đo trên nền đó là đo *`shift_plan` + `rest_window`* vs
  không-gì, mà `shift_plan` **đã bị ĐA-07/UPDATE-087 TẮT vì có hại**. Nền ĐÚNG: arm A =
  positioning `wait_only`; arm B = A **+ `rest_window`**.
- ✅ **Cơ chế CÓ CHẠY (vòng soi đo thật)**: arm B `rest_window` decided **0/12/11** và followed
  **0/5/8** theo ngày 0/1/2 ⇒ kênh **thôi INERT từ ngày thứ hai**, đúng acceptance.
- `POLICY_LOCKED_KEYS` (UPDATE-111) đã khoá `rest_defer_max_min` ⇒ không ai "cứu" Δ bằng
  cách nới trần hoãn. Guard này chính là điều kiện tiên quyết cho phép đo này chạy an toàn.
- Guardrail **TẦNG 5** (UPDATE-111) phải bật trong artifact: `veto_fired_n` per-rail +
  quá-sức hai định nghĩa. Đây là phép đo đầu tiên mà tầng 5 thực sự có việc để canh.

### Acceptance — bản CHỐT 2026-08-01 (đã sửa theo 5 lỗ UPDATE-114 tìm ra)

- Kênh `rest_window` nói **> 0 lần** ở ngày ≥ 2 ✅ (đã đo trước: decided 0/12/11) — nếu về 0
  thì chẩn đoán tiếp, **KHÔNG** kết luận "kênh vô dụng";
- **nền A = positioning `wait_only`**, B = A + `rest_window`. 🔴 **KHÔNG dùng
  `CHANNEL_LADDER["rest_window"]`** — nó bật kèm `shift_plan: True` mà `shift_plan` đã bị
  ĐA-07/UPDATE-087 TẮT vì có hại ⇒ đo trên đó là đo hai can thiệp trộn nhau;
- **cổng arm đối chứng (DET-01)**: arm A có quyết định ⇒ TREO. Nay đã có đường chạy thật
  (UPDATE-114 lỗ (a)) — trước đó cổng này chỉ sống ở comment;
- cổng adherence `D-M3-10` verdict OK cho **cả hai** arm;
- **tầng 5 phải chấm trên `touched_actors`, không trên tổng cohort** (UPDATE-114 lỗ (b)):
  kênh này chạm ~10% tài xế ⇒ chấm trên tổng pha loãng ~10× xuống dưới nhiễu seed ⇒ cổng canh
  nhiễu. Việc **nối `health_guardrail(actor_ids=…)` vào `aggregate_health_guardrail`** thuộc
  cycle này — cơ chế đã có nhưng **đường chạy thì chưa** (đúng họ lỗi (a), đừng lặp lại);
- **`min_seeds=100`** cho mọi contrast biến thể qua `compare()` (UPDATE-114 lỗ (d));
- ~~Δ báo kèm mức phân rã CRN~~ — **BỎ**: CRN không phân rã (đo được, xem câu 2);
- trần ≤29% **KHÔNG trích cho chế độ multiday** (số một ngày — xem đính chính bên trên);
- fingerprint ngày 1 arm A giữa hai lần chạy: IDENTICAL (nếu không, multiday không tất định
  và mọi Δ vô nghĩa).

### Prereg đã KHOÁ

`specs/simulation/d-m3-04-multiday-prereg-locked.json` (khoá 2026-08-01, **trước** khi đo).

Điểm quan trọng nhất trong đó — **kỳ vọng đăng ký trước là Δ ≤ 0**, và đó không phải bi quan mà
là kỳ vọng ĐÚNG của mô hình: world hiện tại không có hậu quả mệt, tức **world β=0**, nên mọi can
thiệp tăng nghỉ chỉ tốn thời gian kiếm tiền và không hoàn lại gì. Kèm ranh giới phát biểu: Δ ≤ 0
cho phép nói *"trong world không có hậu quả mệt, kênh nghỉ là chi phí thuần"* và **không** cho
phép nói *"gợi ý nghỉ vô giá trị ngoài đời"* — khác nhau đúng ở β, thứ ta chưa có dữ liệu để đặt.

Prereg cũng khoá một **dự đoán có thể sai**: Δ ∈ [−1.500, +500] đ. Nếu Δ dương SIG > +1.000 thì
dự đoán của tôi sai và phải điều tra — ứng viên đầu tiên là hiệu ứng **THỜI ĐIỂM** (nghỉ đúng
trũng cầu rồi quay lại giờ vàng, tức `C2′`), không phải hiệu ứng sức khoẻ.

## Việc phải làm TRƯỚC

1. ~~`D-E10-01`~~ ✅ **XONG** (UPDATE-113) — và nó đã trả cổ tức ngoài dự tính: vì
   `generate_realdata(continuous=True)` chạy qua `run_multiday`, fix này đổi realization mock và
   **phơi ra 6 rò rỉ thông tin tương lai** ở đường l1r (`D-M3-11`, UPDATE-115).
2. ~~Plan mode: chốt 3 câu hỏi thiết kế~~ ✅ **XONG** — Cường duyệt cả 3 (2026-07-31).
3. ~~Nối `health_guardrail(actor_ids=…)` vào `aggregate_health_guardrail`~~ ✅ **XONG
   2026-08-01 (UPDATE-116)** — và khi mở code ra nối thì phát hiện **vấn đề lớn hơn hẳn**:
   `_system_metrics` (nguồn DUY NHẤT của `system_a/b`) **không mang khoá sức khoẻ nào** ⇒ tầng 5
   trả `TREO — THIẾU DỮ LIỆU` trên mọi pair, tức **chưa từng đo được gì** (`D-M3-13`; `grep` cho
   thấy 0 artifact từng mang khoá này). Nay đã nối nguồn + `touched_actors(rb)` áp cho cả hai arm
   + khai mẫu số `n_actors_scope`. Đo đường thật (seed 5011, `wait_only`, coverage all): nghỉ
   **+352,8′**, `work_span_p90` **−17,8′**, `drive_min_p90` **−13,4′**, verdict OK, scope 90/90.
   ⇒ **Tiên quyết tầng 5 của phép đo này đã sẵn sàng thật, không phải trên giấy.**
4. 🔴 **CÒN LẠI**: `run_pair_multiday` — đường chạy A/B nhiều ngày. Đây là phần **MỞ RỘNG** (viết
   hàm mới), khác với các bước trên là **fix lỗi**; theo chỉ đạo Cường 2026-07-31 (*"ưu tiên fix
   lỗi thay vì mở rộng sim"*) nên nó **chờ Cường bật đèn** dù prereg đã khoá sẵn.
   ✅ **ĐÈN ĐÃ BẬT 2026-08-03** (xem khung đầu file) — nhưng là **Cycle B riêng**: nó đổi hành vi
   sim và thêm một đường đo, nên theo `CLAUDE.md` §4b cần plan riêng, không trộn vào cycle docs
   (UPDATE-128). Ước: ~1,5h người + ~4,2h máy.
5. ✅ **XONG 2026-08-03 (UPDATE-128)**: `luat_quyet_dinh` đã đăng ký vào prereg **trước khi đo**.
   Đây là tiên quyết mới do chỉ thị 2026-08-03 sinh ra — không có nó thì kết quả đo dù đúng vẫn
   không dùng được để quyết định gì, vì tiêu chí sẽ được chọn sau khi thấy số.
