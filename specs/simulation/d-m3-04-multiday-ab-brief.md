# D-M3-04 BRIEF — bật multiday trong A/B để kênh `rest_window` thôi INERT

Ngày: 2026-07-31 · Trạng thái: **BRIEF — chưa implement** (soạn trong lúc hai phép đo chạy;
implement chạm `parallel.py`/config nên phải đợi đo xong). Hướng: *"hoàn thành kế hoạch dang
dở"* (chỉ đạo Cường 2026-07-31).

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

1. **Metric gộp theo ngày nào?** (a) chỉ ngày cuối — sạch nhất về memory nhưng n giảm 7×;
   (b) trung bình ngày 2..N — nhiều dữ liệu hơn nhưng các ngày không độc lập (cùng actor);
   (c) tổng 7 ngày trừ ngày 1. **Nghiêng (b)** + bootstrap theo SEED (không theo ngày) để
   không giả định độc lập sai.
2. **CRN còn giữ được tới đâu?** Multiday có `reset_for_new_day` dùng RNG riêng
   (`np.random.default_rng((seed, d, 0xDA1))`) ⇒ A và B cùng chuỗi reset. Nhưng quỹ đạo ngày
   1 đã khác (advice) ⇒ SOC/vị trí đầu ngày 2 khác ⇒ **CRN phân rã dần theo ngày**. Đây là
   bản chất, không phải bug — nhưng phải **đo mức phân rã** (fingerprint ngày 1 vs ngày 3
   ở arm A giữa hai lần chạy) và khai trong artifact, nếu không ai đó sẽ đọc Δ ngày 7 như
   thể nó cùng độ tin cậy với Δ ngày 2.
3. **Chi phí máy**: 7 ngày × 2 arm × n seed. Với n=30 là 420 run-ngày ≈ 3,5×
   chi phí một arm single-day n=100. Cần chốt n và số ngày (đề xuất: **days=3, n=100** —
   đủ để `planned_rest_hour` sống từ ngày 2, rẻ hơn 7 ngày, và giữ chuẩn n=100).

### Bẫy đã biết (từ chính repo, không phải suy đoán)

- **`D-E10-01`**: `idle_streak_min` KHÔNG nằm trong `_DAILY_RESET_*` (`entities.py`) ⇒ ngày 2
  mở màn với streak tồn dư của cuối ngày 1. Phải sửa **TRƯỚC** khi đo multiday, kèm test,
  nếu không mọi số E10b/rest trong multiday sai từ phút đầu.
- Trần trên của kênh là **≤29%** số cơ hội dù sửa gì (hai lan can sức khoẻ chặn 71,0% —
  `soc_low` 44,1% + `fatigued` 26,9%). Đó là **ranh giới đạo đức**, không phải bug ⇒ kỳ vọng
  ghi trước: Δ của `rest_window` sẽ NHỎ, và Δ nhỏ **không** phải lý do nới lan can.
- `POLICY_LOCKED_KEYS` (UPDATE-111) đã khoá `rest_defer_max_min` ⇒ không ai "cứu" Δ bằng
  cách nới trần hoãn. Guard này chính là điều kiện tiên quyết cho phép đo này chạy an toàn.
- Guardrail **TẦNG 5** (UPDATE-111) phải bật trong artifact: `veto_fired_n` per-rail +
  quá-sức hai định nghĩa. Đây là phép đo đầu tiên mà tầng 5 thực sự có việc để canh.

### Acceptance đề xuất

- Kênh `rest_window` nói **> 0 lần** ở ngày ≥ 2 (nếu vẫn 0 ⇒ chẩn đoán tiếp, KHÔNG kết luận
  "kênh vô dụng" — có thể còn chặn khác);
- cổng adherence D-M3-10 verdict OK cho mọi arm; tầng 5 không flag;
- Δ báo kèm **mức phân rã CRN theo ngày** và trần ≤29% nói ở trên;
- fingerprint ngày 1 arm A giữa hai lần chạy: IDENTICAL (nếu không, multiday không tất định
  và mọi Δ vô nghĩa).

## Việc phải làm TRƯỚC

1. `D-E10-01` — thêm `idle_streak_min` vào `_DAILY_RESET_FLOAT` + test multiday (nhỏ, rẻ).
2. Plan mode: chốt 3 câu hỏi thiết kế trên với Cường.
