# PLAN (LƯU TRỮ) — Chương trình NGHỈ-CÓ-GIÁ-TRỊ: mệt → hiệu suất → gợi ý nghỉ đo được

Lưu: 2026-08-01 theo yêu cầu Cường (*"lưu plan cũ lại rồi viết đè sau"*). Đây là plan của cycle
2026-07-31, được bảo toàn nguyên văn khi plan file chuyển sang task khác (Week 2 Report).

**Trạng thái:** **Phase A ĐÃ XONG** (UPDATE-111 + 114 + 116). **Phase B CHƯA LÀM** — Cường
2026-07-31 hạ xuống nhãn **THỬ NGHIỆM, không ưu tiên**: *"việc đảo C2 nên được coi như 1 thử
nghiệm — xem có thể khai thác nếu có ích không, do đã có phán quyết từ trước"* ⇒ `V-20` trong
`tracking/PENDING-REVIEW.md` đang chờ Cường chốt văn bản phán quyết.

Đọc kèm: `specs/simulation/e11-fatigue-world-brief.md` ·
`tracking/PHAN-QUYET-2026-07-31-dao-c2-tang-world.md` ·
`tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` · `specs/advisor-objective-model-v2.md` §1.2b

> **⚠ ĐỌC TRƯỚC — cập nhật 2026-08-03 làm mất một trụ của plan này.** Quyết định Cường
> (`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`) xếp kênh **`rest_nudge`** — đúng kênh
> Phase B sinh ra để đo — vào **`SOFT_TOPICS`**: 0 mẫu số adherence, 0 `followed`, 0 claim tiền.
>
> Cụ thể trong plan này: mục **V1 "bảo toàn thu nhập"** (bảng §GIÁ TRỊ) **mất đường đo**; và Phase B
> §"Đo" viết *"coin adherence riêng thấp hơn"* cho `rest_nudge` — **điều đó nay bị cấm**, vì một
> coin adherence riêng cho kênh nghỉ chính là thước nghe-lời của lời khuyên sức khoẻ.
>
> Phần còn **nguyên giá trị**: **V2** (chỉ tiêu sức khoẻ tầng 5, cột riêng, không quy tiền — đã có
> thật từ UPDATE-116), **V3** (niềm tin — vẫn là ASSUMPTION), **V4** (nền tảng/pháp lý), và toàn bộ
> **Phase A** (đã xong). Phát hiện kỹ thuật về `online_min` **gộp cả thời gian nghỉ** (`world.py:756`)
> cũng còn nguyên giá trị — nó là bẫy thật cho bất kỳ thiết kế liều-mệt nào.
>
> ⇒ Plan này giữ ở dạng **LƯU TRỮ**. Muốn hồi sinh thì phải **thiết kế lại quanh V2**, không nối
> tiếp bản này. Xem thêm khung cập nhật ở `e11-fatigue-world-brief.md`.

---

## Context — và một xung đột phải nói thẳng

Chỉ đạo của Cường (2026-07-31, reject plan cũ hơn): *"thiết kế nghỉ phải đi kèm thiết kế mệt →
giảm hiệu suất → việc khuyên nghỉ phải đem lại giá trị gì đấy (trong sim, và thực tế). Trên thực
tế khi triển khai AI chỉ GỢI Ý (nhẹ hơn khuyên) nghỉ khi thấy tài xế làm quá sức."*

⚠ Chỉ đạo này **đảo một phần phán quyết đã duyệt** (`PHAN-QUYET-2026-07-29-diem3-met-nghi.md`,
Cường chấp nhận 2026-07-30; spec §1.2b ghi C2 "HUỶ VĨNH VIỄN"): phán quyết cũ cấm mọi cơ chế
mệt→hiệu-suất **kể cả viết vào world**, vì nó tạo tỷ giá sức-khoẻ↔tiền (`∂payout/∂F`). Cường là
người ra quyết định gốc nên có quyền mở lại — nhưng phải **mở lại tường minh bằng PHAN-QUYET
mới**, không lách.

**Vì sao phán quyết cũ để lại một lỗ thật:** trong world không có hậu quả mệt, kênh nghỉ **về cấu
trúc không thể có giá trị đo được** — hoãn nghỉ miễn phí, gợi ý nghỉ chỉ tốn thời gian kiếm tiền
⇒ Δ ≤ 0 vĩnh viễn ⇒ sim không bao giờ trả lời được câu hỏi sản phẩm *"gợi ý nghỉ khi quá sức có
đáng không"*. Từ chối mô hình hoá tỷ giá không xoá nó khỏi thực tế — chỉ làm sim mù với nó.

## Kiểm tra lại độ chính xác của C2 — PHÁN QUYẾT (Cường giao agent quyết)

**Trụ (b) — "không đủ khả năng làm đúng": VẪN ĐÚNG NGUYÊN VẸN.** 0 dữ liệu mệt, 0 dữ liệu tai
nạn; proxy duy nhất là nhiễu thuần theo construction; 240′ Điều 64 không áp cho bike ⇒ **mọi claim
điểm "gợi ý nghỉ đáng +X đ" là bịa**. Hệ quả sống: chỉ được báo ĐƯỜNG CONG CÓ ĐIỀU KIỆN Δ(β),
lưới β khoá prereg.

**Trụ (a) — "viết vào world chỉ xoá nhãn của tỷ giá, nên cấm cả world": CÓ MỘT LỖ THẬT.** Lập
luận cũ coi "không mô hình hoá" là trung lập. Nó không trung lập — **không mô hình = mô hình với
β=0, và β=0 cũng là một lựa chọn hiệu chuẩn, lại là lựa chọn THIÊN VỊ CHỐNG NGHỈ**:

- world β=0 làm mọi can thiệp TĂNG nghỉ trông như chi phí thuần (Δ ≤ 0 vĩnh viễn) và mọi can
  thiệp HOÃN nghỉ trông miễn phí ⇒ world hiện tại đang **NỊNH kênh hoãn**;
- ngoài đời ∂payout/∂F ≠ 0 là sự thật của lãnh thổ; từ chối vẽ nó lên bản đồ không xoá nó — chỉ
  làm sim mù, và mù **đúng theo hướng có hại cho tài xế**. Thế giới "an toàn đạo đức" hoá ra là
  thế giới thân-vắt-sức. Đây là điểm Cường bắt trúng.
- Nỗi sợ thật của trụ (a) — advisor mặc cả sức khoẻ lấy tiền — nằm ở tầng ADVISOR/BÁO CÁO, không
  phải tầng world. Trong world có mệt, tối ưu tiền và nghỉ-hợp-lý **cùng chiều** (mệt tốn tiền
  thật); chỗ chúng còn lệch đã có ràng buộc CỨNG `rest_min_per_4h` + trần hoãn khoá cứng trám.

**PHÁN QUYẾT: NÊN LÀM — đảo trụ (a) ở TẦNG WORLD, giữ nguyên nó ở tầng advisor/báo cáo, giữ
nguyên toàn bộ trụ (b).** Sáu điều kiện ràng (enforce bằng máy, không bằng lời hứa):

1. Phase A (3 cơ chế) đi TRƯỚC — chặn đúng các cửa lạm dụng mà phán quyết cũ sợ;
2. lưới β khoá prereg TRƯỚC khi đo; β=0 bit-identical (test); **CẤM vĩnh viễn chọn β theo Δ**;
3. advisor MÙ với F — trigger chỉ đọc quan sát được (`work_span`/`online_min`); scanner cơ chế 2
   enforce (manifest class `WORLD_PHYSIOLOGY` riêng: world được mô hình mệt, advisor đọc F là đỏ);
4. báo cáo: cột tiền = "bảo toàn thu nhập, điều kiện theo β"; cột sức khoẻ riêng; **0 quy đổi**;
5. nudge là GỢI Ý: coin adherence riêng thấp hơn, cadence + dismissed-window, không nói khi đang
   chở khách; ba lan can cũ nguyên bit;
6. PHAN-QUYET mới ghi tường minh: đảo cái gì, giữ cái gì, lập luận cũ hở ở đâu — không ghi đè
   im lặng.

⚠ **Phát hiện kỹ thuật quyết định (kiểm 2026-07-31):** biến mệt hiện có (`online_min`) **GỘP CẢ
thời gian nghỉ** (`world.py:756`) — đơn điệu, nghỉ không hồi. Nếu Phase B dùng nó làm liều thì
nghỉ không giảm mệt ⇒ nudge vô giá trị **theo cấu trúc** và ta sẽ đo ra một "số 0 giả" rồi kết
luận nhầm "gợi ý nghỉ vô ích". E11 phải có **liều-có-hồi-phục riêng** (tích khi làm việc, hồi khi
rest/charge ≥ ngưỡng — chính là work_span động); `online_min` của bản năng giữ nguyên từng bit.

## Khung BA RANH GIỚI mới (thay §1.2b nếu Cường duyệt)

Giữ nguyên tinh thần *"sức khoẻ không phải biến để TỐI ƯU"* nhưng đặt lại ranh giới đúng tầng:

1. **World được phép THẬT** — mệt→hiệu-suất tồn tại ngoài đời; sim mô hình nó như **TRỤC QUÉT
   không hiệu chuẩn** β ∈ {0, nhẹ, vừa, mạnh} (β=0 bit-identical, test canh). Không bao giờ claim
   "β thật là X" (0 dữ liệu mệt — điểm (b) vẫn ĐÚNG); mọi kết quả là **đường cong có điều kiện
   Δ(β)**: *"NẾU mệt tốn ~x% hiệu suất THÌ gợi ý nghỉ đáng ~y đ"*. Lưới β khoá trong prereg
   TRƯỚC khi đo — không tồn tại đường "chọn β vì Δ đẹp".
2. **Advisor MÙ với latent** — bài học đắt nhất của E10 áp thẳng: advisor/solver/policy **không
   bao giờ đọc F**. Gợi ý nghỉ trigger trên **QUAN SÁT ĐƯỢC** mà platform thật có: `work_span`
   (nghỉ→nghỉ) và `online_min` — chính chỉ tiêu tầng 5. Advisor không thể mặc cả sức khoẻ vì nó
   không nhìn thấy sức khoẻ — nó thấy giờ công.
3. **Giá trị sức khoẻ KHÔNG quy tiền — kỷ luật BÁO CÁO** — cột tiền và cột sức khoẻ tách vĩnh
   viễn trong mọi artifact: hiệu ứng sức khoẻ báo như trục kết quả riêng (`rest_min_total`↑,
   `work_span p90`↓); hiệu ứng tiền báo là *"chi phí / bảo toàn thu nhập"*. Không câu nào dạng
   "sức khoẻ đáng X đồng".

## GIÁ TRỊ của kênh gợi ý nghỉ — phân rã

| # | Giá trị | Đo ở đâu | Cơ chế |
| --- | --- | --- | --- |
| V1 | **Bảo toàn thu nhập** (tiền, đo trong sim) | Δ(β) n=100, phase B | Mệt→chậm ⇒ ít cuốc/giờ về chiều tối; nghỉ ĐÚNG TRŨNG CẦU (tái dùng logic khung S7) giữ "pin người" cho giờ vàng 17–20h. Đây là luận điểm demand-timing, **không phải định giá sức khoẻ**. Lưu ý phán quyết cũ đã chỉ đúng: cùng world này, kênh HOÃN nghỉ bị phạt (hoãn ⇒ liều cao hơn ⇒ Δ âm hơn) — tức world mới **kỷ luật kênh cũ và thưởng kênh Cường muốn**, hai chiều đều trung thực |
| V2 | **Sức khoẻ** (đo trong sim, KHÔNG quy tiền) | tầng 5, phase A | `rest_min_total`, `work_span p90/max`, `drive_min p90/max`, `veto_fired_n` — nudge phải cải thiện các số này với chi phí tiền chấp nhận được |
| V3 | **Niềm tin/retention** (thực tế, sim không đo được) | ASSUMPTION — trục UX §12 | Advisor chỉ nói tiền = công cụ vắt sức; một gợi ý nghỉ đúng lúc là tín hiệu "app đứng về phía mình" ⇒ adherence các kênh khác tăng. Đúng loại PROACTIVE CARD của F0 §12; "gợi ý" = giọng nhẹ + không lặp sau khi bị Bỏ qua + adherence coin riêng THẤP hơn khuyên (ASSUMPTION, quét) |
| V4 | **Nền tảng/pháp lý** | ghi nhận | Cảm biến quá sức sẵn sàng nếu quy định giờ lái mở rộng sang xe 2 bánh; 240′ Điều 64 vẫn chỉ là mốc tham chiếu ASSUMPTION (ô tô KDVT) |

## PHASE A — 3 cơ chế enforce: từ "hàng rào" thành MÓNG của phép đo giá trị

**Trạng thái: ĐÃ LÀM XONG.** Vai trò trong chương trình giá trị:

1. **`POLICY_LOCKED_KEYS`** (`src/gsm_core/policy_locks.py` + chokepoint
   `advice_bridge.__init__` — KHÔNG ở `run_once` vì multiday dựng World trực tiếp): khoá
   `rest_defer_max_min`=120, `shift_extend_max_min`=60 + 3 hằng `idle_reduction` (gate OR).
   Vắng mặt = hợp lệ. KHÔNG khoá `rest_min_per_4h` (spec đòi sweep được) /
   `fatigue_threshold_min` (hardcode ARCHETYPES) / `swap_soc_threshold_pct` (điều khiển cả
   calibration world). → *Trong phase B nó chặn đúng cửa "nới trần hoãn để Δ đẹp".* 8 test.
2. **`test_no_fatigue_in_payout_path`** (scanner AST 2 lớp + MANIFEST money-scope; 4 mũi tiêm
   mutation vào file thật đã chứng minh bắn; comment/docstring miễn nhiễm; veto-scope được đọc
   fatigue hợp lệ; phủ cả `ui/backend`): scope = **đường tiền của ADVISOR/solver/policy/features**.
   Phase B thêm manifest-class `WORLD_PHYSIOLOGY` riêng (hôm nay RỖNG) — world được mô hình mệt
   có kiểm soát, advisor đọc F thì scanner vẫn bắn. → *Đây chính là cái làm ranh giới 2 enforce
   được bằng máy, không phải bằng lời hứa.* 0 dòng production đổi.
3. **Guardrail TẦNG 5** (`D-M3-05`; event `advice_rest_veto` log-only, hằng `REST_MIN/MAX_MINUTES`
   thay literal — bit-identical; `sim_metrics.health_guardrail` + promote vào `parallel`):
   `rest_min_total` · `veto_fired_n` (KHÔNG trơ — đo 174–212 lần/run, kèm `veto_calls_n` vì mẫu
   số đổi theo arm; `defer_cap` TRƠ 0/15 — khai như min_pickups) · **CẢ HAI định nghĩa quá sức
   (Cường chốt)**: `work_span p90/max` (62/90 vượt 240′) VÀ `drive_min p90/max` (25/90). Cổng MỘT
   CHIỀU trên p90 (max nhiễu ±36% ⇒ bắn oan ⇒ mẫu `D-R20`). → **Vai trò kép: tầng 5 là CẢM BIẾN
   QUÁ SỨC — trigger của kênh gợi ý nghỉ phase B đọc đúng chỉ tiêu này.** 10 test.

⚠ **Bổ sung 2026-08-01 (UPDATE-116):** khi đi nối `health_guardrail(actor_ids=…)` thì phát hiện
tầng 5 **chưa từng có nguồn dữ liệu** trong đường A/B (`_system_metrics` không mang khoá sức khoẻ
nào ⇒ verdict `TREO — THIẾU DỮ LIỆU` trên mọi pair). Đã nối nguồn + `touched_actors(rb)` áp cho cả
hai arm + khai mẫu số `n_actors_scope`. Đo đường thật (seed 5011): nghỉ **+352,8′**,
`work_span_p90` **−17,8′**, verdict OK, scope 90/90. ⇒ **Tiên quyết tầng 5 của Phase B nay sẵn
sàng THẬT, không phải trên giấy.**

## PHASE B (CHƯA LÀM — chờ PHAN-QUYET mới, không code trước) — E11

- **Trục mệt**: MỘT cơ chế duy nhất ở v1 để attribution sạch — `speed_multiplier = 1 − β·g(D)`
  với **D = liều-có-hồi-phục MỚI** (tích khi làm việc, hồi khi rest/charge ≥ ngưỡng — KHÔNG dùng
  `online_min` vì nó gộp cả nghỉ, đơn điệu ⇒ nudge sẽ vô giá trị cấu trúc, "số 0 giả");
  `online_min` của bản năng giữ nguyên từng bit. β quét {0, 0.05, 0.10, 0.15} khoá prereg;
  β=0 bit-identical (test).
- **Kênh `rest_nudge`** (MỚI, tách khỏi `rest_window`-hoãn): trigger `work_span` vượt ngưỡng
  (quan sát được — tầng 5), gợi ý nghỉ tại trũng cầu gần nhất (tái dùng S7); giọng GỢI Ý =
  adherence coin riêng thấp hơn (quét), chịu cadence + dismissed-window, **không bao giờ nói khi
  đang chở khách**; ba lan can cũ giữ nguyên từng bit.
- **Đo**: Δ(β) tiền + tầng 5 sức khoẻ, n=100 ghép cặp, prereg kiểu E10 (kỳ vọng ghi trước:
  Δ(0) ≈ −chi phí nhỏ; Δ tăng theo β; kênh HOÃN âm hơn khi β tăng); STOP nếu Δ<0 ở mọi β.
- Chi phí ước: spec+prereg ~0,5 ngày · code ~1 ngày · đo ~3–4h máy.

## Không làm

Code phase B trước PHAN-QUYET · sửa lan can/behavior hiện có · đo C2′ · **calibrate β theo Δ
(cấm vĩnh viễn — lưới khoá trước)** · quy đổi bất kỳ chỉ tiêu sức khoẻ nào ra VND.
