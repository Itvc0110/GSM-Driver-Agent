# E11 BRIEF — thế giới có mệt + kênh gợi ý nghỉ (ĐẦU VÀO cho spec, chưa phải spec)

Ngày: 2026-07-31 · Trạng thái: **DRAFT — nhánh THỬ NGHIỆM, KHÔNG ƯU TIÊN** (Cường
2026-07-31: đảo C2 = thử nghiệm, phán quyết cũ giữ mặc định; ưu tiên hoàn thành dang dở +
fix lỗi thay vì mở rộng sim). Không code gì từ file này; chỉ mở khi hàng đợi fix/hoàn-thành
cạn và Cường gọi tên.
File này gom mọi điều đã học để workflow thiết kế spec (kiểu E10: N thiết kế độc lập +
phản biện rò-rỉ + tổng hợp) không phải khai quật lại.

> ## ⚠ CẬP NHẬT 2026-08-03 — kênh của E11 nay là KHUYÊN MỀM, tức KHÔNG ĐO ĐƯỢC như E11 giả định
>
> Quyết định Cường 2026-08-03 (`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`) xếp
> **`rest_nudge`** — đúng cái kênh E11 sinh ra để đo — vào **`SOFT_TOPICS`**: không mẫu số
> adherence, không `followed`, không claim tiền.
>
> **Đây là một mâu thuẫn thật với thiết kế E11, phải nói thẳng chứ không lấp:** E11 đo *"gợi ý nghỉ
> đáng bao nhiêu theo từng mức β"* (bảng V1 "bảo toàn thu nhập"). Nếu kênh không được đo mức nghe
> lời và không được claim tiền thì **V1 mất đường đo**, và phần còn dùng được của E11 là **V2**
> (chỉ tiêu sức khoẻ tầng 5, cột riêng, không quy tiền) + **V4** (nền tảng/pháp lý).
>
> ⇒ Nếu E11 được gọi tên lại thì phải **thiết kế lại quanh V2**, không phải nối tiếp bản này. Và nó
> phụ thuộc kết quả `D-M3-04`: nếu `D-M3-04` REVERT (nhánh prereg dự đoán trước, vì world β=0) thì
> **cả kênh HOÃN nghỉ cũng thành khuyên mềm**, và lý do tồn tại của E11 yếu đi rõ — lúc đó câu hỏi
> đúng không còn là *"nghỉ đáng bao nhiêu tiền"* mà là *"gợi ý nghỉ thế nào cho tài xế thấy được
> tôn trọng"*, một câu hỏi UX, không phải câu hỏi sim.
>
> Trạng thái không đổi: **THỬ NGHIỆM, KHÔNG ƯU TIÊN.** `V-20` vẫn chờ Cường chốt văn bản phán quyết.

## Câu hỏi trung tâm

> **Gợi ý nghỉ khi tài xế làm quá sức có giá trị bao nhiêu — theo từng mức giả định về
> hậu quả của mệt?** (đường cong Δ(β), KHÔNG phải một con số)

Nguồn: chỉ đạo Cường 2026-07-31 (*"AI chỉ GỢI Ý — nhẹ hơn khuyên — nghỉ khi thấy tài xế làm
quá sức"*) + phán quyết đảo C2 tầng world.

## Khung ràng buộc đã chốt (từ PHAN-QUYET — không thương lượng lại trong spec)

1. β là TRỤC QUÉT không hiệu chuẩn {0, 0.05, 0.10, 0.15}, khoá prereg TRƯỚC khi đo;
   β=0 **bit-identical** (test canh); CẤM chọn β theo Δ; CẤM claim điểm.
2. Advisor MÙ latent: trigger chỉ đọc `work_span`/`online_min` (tầng 5 — ĐÃ CÓ, UPDATE-111).
   Cơ chế mệt của world khai vào manifest class `WORLD_PHYSIOLOGY` (scanner cơ chế 2 —
   advisor/solver đọc F vẫn ĐỎ).
3. Báo cáo hai cột vĩnh viễn: tiền = "bảo toàn thu nhập (điều kiện theo β)"; sức khoẻ
   (rest_min_total, work_span/drive_min p90) không quy tiền.
4. Nudge là GỢI Ý: coin adherence riêng THẤP hơn khuyên (ASSUMPTION, quét), chịu cadence +
   dismissed-window, không nói khi chở khách; ba lan can `should_defer_rest` nguyên bit;
   `POLICY_LOCKED_KEYS` chặn nới trần.

## Sự thật code đã kiểm (2026-07-31 — thiết kế viên PHẢI kiểm lại, không chép)

- 🔴 **`online_min` GỘP cả thời gian nghỉ** (`world.py:756` — "chờ + serve + charge"),
  đơn điệu, nghỉ không hồi ⇒ **CẤM dùng làm liều**. Cần **liều-có-hồi-phục D riêng**:
  tích khi segment DRIVE (enroute/on_trip/relocate), hồi khi rest/charge ≥ `DRIVE_BREAK_MIN`
  (=20, dẫn xuất từ `REST_MIN_MINUTES` — cả hai hằng ĐÃ CÓ). Nếu dùng online_min ⇒ nudge vô
  giá trị cấu trúc ⇒ "số 0 giả".
- Bản năng hiện đọc `online_min/fatigue_threshold_min` (behavior.py:149-156) để RA QUYẾT
  ĐỊNH nghỉ — biến này GIỮ NGUYÊN BIT (đổi = phá behavior-neutral ở β=0).
- Cơ chế hậu quả v1: MỘT cơ chế duy nhất — `speed_multiplier = 1 − β·g(D)` áp vào
  `_travel_min` (điểm áp cần trace: tốc độ đã qua congestion + env factor — xem `_dfac`,
  `speed_kmh`). g(D) cần bão hoà (vd min(D/D_ref, 1)) — thiết kế viên chốt D_ref từ phân
  phối work_span ĐÃ ĐO: p50=295′, p90=431′ (World A seed 5100, artifact 42-*).
- Trigger nudge đọc tầng 5 runtime: cần cách tính work_span ĐANG CHẠY của actor (world chưa
  track — `continuous_work` là hậu-kiểm trên segments; cần counter online tương tự
  `idle_streak_min` nhưng cho chuỗi làm việc, reset khi rest/charge ≥ ngưỡng; counter MỚI
  không đụng counter cũ).
- Baseline lan can/veto: A ≈ B về rails (artifact 42-rest-rails-sabotage-probe.json);
  kênh rest_window nói 0 lần (D-M3-04) — nudge là kênh MỚI, không sửa kênh cũ.
- Coin/cadence pattern có sẵn: `adherence_coin(seed, key, revision)` keyed sha256;
  dismissed-window theo pha ca (cadence.py). Kênh mới PHẢI theo cùng pattern (bài học
  D-SIM-14 re-roll).
- Đo lường: khuôn E10 tái dùng nguyên (prereg locked file · arm ghép cặp CRN n=100 ·
  cổng adherence D-M3-10 · guardrail NĂM tầng · STOP chain · G-SENS n=30 chỉ CHIỀU).

## Kỳ vọng đăng ký trước (nháp — spec chốt)

- Δ(β=0) ≈ −chi phí nhỏ (nudge tốn thời gian kiếm tiền, không có lợi ích trong world β=0);
- Δ tăng theo β; kênh HOÃN (`rest_window` cũ) ÂM dần theo β (world mới kỷ luật kênh cũ);
- tầng 5: rest_min_total ↑, work_span p90 ↓ ở arm nudge (mọi β kể cả 0);
- STOP nếu Δ<0 ở MỌI β kể cả mạnh — báo "gợi ý nghỉ không có giá trị tiền trong dải giả
  định đã quét" + giá trị chỉ còn ở cột sức khoẻ/niềm tin (V2/V3).

## Bẫy đã biết cho phản biện (mỗi cái một lăng kính)

1. Oracle-leak: trigger/nudge đọc D latent hay g(D)? — CẤM; chỉ đọc counter quan sát được.
2. CRN: counter mới/speed multiplier có tiêu RNG không; β=0 phải qua fingerprint ≥5 seed.
3. Double-count: mệt→chậm đã làm giảm trips; đừng thêm cơ chế thứ hai (accept-quality) ở v1.
4. Confound khối lượng: nudge làm actor nghỉ ⇒ ít giờ online ⇒ so sánh phải tách "ít giờ"
   với "giờ chất lượng hơn" (decomposition per-hour như E10 §5.4).
5. Goodhart tầng 5: nudge được TỐI ƯU để làm đẹp work_span? — cổng một chiều đã chặn chiều
   khen; spec phải giữ.
6. `defer_cap` trơ + D-M3-04: nudge KHÔNG phụ thuộc multiday — nhưng nếu bật multiday sau,
   `idle_streak`/counter mới không nằm trong `_DAILY_RESET_*` là bẫy nạp sẵn (D-E10-01).

## Chi phí ước

Spec+prereg ~0,5 ngày (workflow thiết kế + phản biện) · code ~1 ngày · đo ~3–4h máy
(A/B_nudge × 4β × n=100 ghép cặp; World A cache dùng lại được cho mọi β vì β chỉ chạm arm?
— KHÔNG: β đổi WORLD ⇒ World A cũng đổi theo β ⇒ cần A(β) riêng từng mức. Thiết kế viên
tính lại budget máy: ~8 batch × 100 run).
