# PB-02 — phản biện `D-M3-20` (hậu quả đo lường)

⚠ Plan mode đang bật ⇒ **KHÔNG được ghi**
`research/audit/2026-08-06-math-model-audit/pb-02-dm320-hau-qua.json`.
Nội dung artifact dự kiến (ghi tạm ở đây để không mất) — chỉ cần copy khối JSON dưới ra đúng path
khi được duyệt.

## Việc cần làm khi hết plan mode
1. Ghi khối JSON dưới ra `research/audit/2026-08-06-math-model-audit/pb-02-dm320-hau-qua.json`.
2. Xoá 2 probe tạm ở scratchpad (không thuộc repo): `probe1_count_draws.py`, `probe2_noise_floor.py`,
   `probe2_out.json`.
3. Sửa `tracking/DEFERRED.md` `D-M3-20`: (a) gỡ mệnh đề *"nhánh cam kết `:898` cũng rút mỗi tick"*
   — đo được **0 lượt**/2 seed × 3 ngày; (b) đổi khung hậu quả từ *"số không tin được"* sang
   **"mất công suất"** (phương sai, không phải thiên lệch); (c) ghi rõ acceptance ĐỊNH TÍNH của
   D-M3-04-FIX là **miễn nhiễm** trôi-stream (FIX-PRE bit-identical 30/30 + sever 7/7 + 16 test).
4. Nợ mới cần mở: **idle_min_total 4/4 seed cùng dấu (+281′, sd 149)** ⇒ chưa loại được khả năng
   trôi-stream có THIÊN LỆCH (không chỉ phương sai). n=4 quá nhỏ; cần n≥30 mới kết luận.

```json
{
  "ma_no": "D-M3-20",
  "goc_soi": "HẬU QUẢ ĐO LƯỜNG có nghiêm trọng như claim không",
  "verdict": "CONFIRMED",
  "do_lon_uoc": "Nền nhiễu trôi-stream THUẦN (2 arm đều TẮT kênh, tiêm ĐÚNG 1 draw phụ/ngày lúc t≥660′, 4 seed × 3 ngày, metric ngày 1-2): rest_min_total per-seed +172,3 / −103,1 / −239,1 / −94,2 (sd 172, |max| 239) · work_span_p90 −17,5 / −9,7 / +41,4 / +40,5 (sd 32, |max| 41) · idle_min_total +485 / +129 / +266 / +245 (mean +281, sd 149) · payout_mean_all sd 3.215đ. So với bảng acceptance UPDATE-142: rest_min +10,9 [−41,2;+59,3] · idle_min −66,8 [−200,6;+68,4] · work_span_p90 −2,9 [−9,6;+3,6]. ⇒ nhiễu 1-draw đã cùng bậc (hoặc lớn hơn) CHÍNH hiệu ứng TRƯỚC FIX từng được gọi là có ý nghĩa (−244′ rest, +42,3′ span). sd suy ra từ CI post-FIX (50×√30/1,96 ≈ 140′) khớp sd trôi-stream đo được (172′) ⇒ phương sai của Δ post-FIX gần như TOÀN BỘ là trôi-stream. Đếm draw phụ (arm B thật, kênh BẬT, 3 ngày): seed 7000 = 12 draw (10 PHÍ / 2 hiệu dụng), seed 7001 = 8 (6/2)."
}
```
