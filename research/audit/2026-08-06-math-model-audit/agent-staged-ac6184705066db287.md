# PB-04 — Phản biện D-ADV-02 (góc: cách sửa đề xuất có đúng không)

⚠ **Plan mode đang bật** ⇒ tôi KHÔNG ghi được
`research/audit/2026-08-06-math-model-audit/pb-04-dadv02-cach-sua.json` như orchestrator yêu cầu
(chỉ file plan này được sửa). Toàn bộ payload trả qua `StructuredOutput`. Nếu muốn có file JSON,
thoát plan mode rồi nói "ghi file" — nội dung đã có sẵn, không cần chạy lại probe.

## Kết luận: PLAUSIBLE (cơ chế đúng, ĐƠN THUỐC sai ở 3 chỗ đo được)

### Đúng
- `bonus_feasibility._hour_rate` (`src/gsm_core/solvers/bonus_feasibility.py:43-45`) trả `(0,0,None)`
  khi `policy.trip_points(hour) <= 0` ⇒ solver THẬT SỰ xử đúng "0 điểm ngoài khung".
- Bridge có đủ input (`build_bonus_gap_input` `:973-1008`, đã gọi `solve()` ở `:1025` cho accept_lift)
  ⇒ "kênh chỉ chưa gọi" đúng về mặt cơ học.
- `[ĐO]` 16/88 lượt NÓI có cửa sổ kéo 100% ngoài khung điểm (toàn P5/P7) ⇒ lỗi có thật, 18,2%.

### Sai (đã bác bằng số)
1. **Cửa sổ sai gốc.** `_walk` từ `shift_end` bỏ mất điểm kiếm được trong `[now, shift_end]`
   ⇒ 71/88 lượt thành vô nghiệm, chỉ 12/88 còn nói được (13,6%) — chính là bài học `swap_early`.
   Bản đúng phải walk từ **now**, budget = `remaining + extend_remaining` ⇒ còn 58/88 (66%).
2. **S1 KHÔNG có mô hình cầu theo giờ.** `hist` do bridge dựng là **cùng một** rate ngày
   (`advice_bridge.py:990-996`): đường multiday điền `peak == offpeak == points_per_hour_avg`.
   `[ĐO]` need_S1 ≡ need_flat ở 45/88 (1 bucket) và **70/88** (đường multiday). Vế "rate trộn peak
   ⇒ ước non ~2×" của D-ADV-02 **không được sửa**; và lệch thì lệch về phía LẠC QUAN (13/14 lượt
   thấp hơn, min 0,37×) do fallback cứng `DEFAULT_TRIPS_PER_HOUR = 1.5` (`:18-20`).
3. **Nới lan can sức khoẻ.** `need_min` là input của `would_exceed_fatigue`
   (`advice_bridge.py:1145-1147`, rail hoạt động nhiều nhất: 15.504/43.009 lượt). Tính lại kịch bản
   test ADV-03: proj 1245′ → **1024,2′** ⇒ rail TẮT; `added` 345,0′ → 124,2′ ⇒ đỏ 2 test ghim.

### Việc phải làm nếu vẫn sửa
- Gọi `solve()` (public) chứ không `_walk`/`_points_possible` (private, không có tham số chặn cuối).
- **Override** `hours_budget_remaining` (bridge `:1003` hardcode ca-còn-lại) — nếu không S1 trả
  `enough_hours=False` cho đúng mọi ca kênh này tồn tại để phục vụ.
- Quyết định tường minh có đọc `solution.feasible` không: nó AND cả acceptance/completion ⇒ `[ĐO]`
  cấm thêm 27/88 lượt, chồng lấn phân công với `accept_lift` (`_advice_would_help:1033-1047`).
- Viết lại 2 test ghim + regate ĐA-08 (đổi hành vi + nới rail sức khoẻ, không phải "sửa thuần math").
