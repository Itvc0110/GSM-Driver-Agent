# Spec — Đo "tài xế có làm theo advice không" bằng HAI đường song song (BACKLOG Q6)

Ngày: 2026-07-27 · Trạng thái: spec v0 — **một phần DONE-CODE (Cycle W, UPDATE-091)**, xem đính
chính 2026-07-29 dưới đây — trả lời câu hỏi Cường *"how are we tracking if the driver follow
instructions, are there multiple ways done in same time?"*. Implement từng phần đã/sẽ theo cycle
riêng; file này là bản đồ chung.

## Nguyên tắc

Một đường đo đơn lẻ nói dối: nút bấm đo Ý ĐỊNH (dễ bấm cho xong), hành vi đo THỰC TẾ (nhưng
nhiễu — hành vi đổi có thể không do advice). Phải chạy CẢ HAI và đối chiếu; lệch giữa hai đường
chính là tín hiệu quý (nói-một-đằng-làm-một-nẻo).

## Đường 1 — EXPLICIT (ý định, UI) — ✅ ĐÃ CÓ từ UPDATE-067

- Nút **Làm theo / Bỏ qua / Vì sao** trên mỗi card → POST `advice_action` (contract v1.0),
  log jsonl local nhãn mock; đọc lại ở Cài đặt.
- Đơn vị phân tích: (driver, date, advice_id, card_kind, action).
- Giới hạn đã ghi: đo Ý ĐỊNH; không có side-effect (tài xế luôn tự quyết — CLAUDE §5).

> **⚠ Đính chính 2026-07-29 (Cycle W, UPDATE-091):** đường ghi canonical nay là **`AdviceEventLog`**
> (`gsm_core/lifecycle/event_log.py`, append-only, idempotent theo `event_id`) — JSONL local ở trên
> chỉ còn vai trò **debug**, không phải nguồn sự thật. Đơn vị phân tích đổi thành
> **`(driver, run_id, decision_id, …)`** — `decision_id` có 3 namespace, `Event.run_id` deterministic
> kèm config digest. UI POST/GET action nay đi qua store canonical.

## Đường 2 — IMPLICIT (hành vi, sim/A-B) — ✅ NỀN ĐÃ CÓ, thiếu phần ĐỐI CHIẾU

- Sim: coin adherence theo archetype (D-SIM-04 ASSUMPTION) + event `advice_given/followed`
  (world.py) + **thế giới song song CRN** đo hiệu ứng nhân-quả sạch (Δ payout theo cặp seed).
- Data thật (tương lai): so hành vi cửa-sổ-sau-advice vs baseline cá nhân (vd: advice "nâng tỷ
  lệ nhận" lúc 14h → acceptance realized 14h-18h vs cùng khung các ngày không-advice).
  **Chặn bởi**: bảng GSM không có accept/decline event (chỉ daily aggregate — F-U2-A/EST-6);
  cần nguồn event-level hoặc chấp nhận granularity ngày.

## Phần THIẾU — việc cho cycle sau (ưu tiên theo thứ tự)

1. **Join key hai đường**: `advice_id` hiện chỉ sống ở UI; sim events không mang advice_id tương
   thích. Chuẩn hoá: advice_id = hash(driver, date, solver, reason_code, at_min-bucket) sinh Ở
   BACKEND — cả card lẫn (sau này) sim bridge dùng chung → join được explicit ↔ implicit.
   **⚠ DONE Cycle W (UPDATE-091):** đã có `decision_id` 3 namespace + `Event.run_id` deterministic
   trong `gsm_core/lifecycle/` — join key hai đường nay tồn tại ở backend, không còn chỉ-UI.
2. **Bảng đối chiếu**: view (driver, tuần) → tỷ lệ bấm-Làm-theo vs Δ hành vi đo được vs adherence
   coin sim — 3 cột cạnh nhau, lệch = flag. Chỗ hiển thị: khu Mô phỏng (reviewer), KHÔNG áp
   lực lên tài xế. **⚠ Cập nhật 2026-07-29:** một nửa đã có — `adherence_view` (hai tên
   `decision_adherence` + `event_adherence`) tính được từ projections; còn thiếu **hiển thị** view
   này ở khu Mô phỏng (phần UI/dashboard chưa làm).
3. **Cập nhật D-SIM-04**: khi có log explicit đủ dày (dù là mock/demo), dùng phân phối bấm-nút
   làm prior MỚI cho adherence coin thay ASSUMPTION thuần (vẫn nhãn rõ nguồn).
4. **Ethics guard** (bài học nudge Uber): KHÔNG dùng số đo adherence để tăng áp lực nudge
   (không "bạn đã bỏ qua 3 lần!"); chỉ dùng để ĐO chất lượng advice và tôn trọng im lặng
   (bỏ qua nhiều lần một LOẠI advice → advisor giảm loại đó — memory design, xem A3 MEMSTATE).

## Liên kết

`ui/contracts/advice_action.json` · UPDATE-067 · D-SIM-04 · D-SIM-14 (RNG coin theo khoá) ·
BACKLOG Q6/R2 · `research/ux/2026-07-27-decision-trace-design-note.md`.
