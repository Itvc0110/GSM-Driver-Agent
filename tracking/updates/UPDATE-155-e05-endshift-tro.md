# UPDATE-155 — E4/E-05 kênh kết-ca-sớm: code XONG, đo ra TRƠ — và vì sao đó là bài học cấp chương trình

- **Ngày:** 2026-08-06
- **Loại:** feature (kênh con) + research (đo quan sát) — kết quả ÂM có giá trị định hướng
- **Liên quan:** UPDATE-151 r05 (E-05) · UPDATE-153 (ADV-01 in-sim ≈ 0 vì cash=0) · plan E4

## Đã làm

Kênh con `advice.shift_plan_end_only` (mặc định **TẮT**): chỉ nói khi lịch DP S2 bảo **KẾT CA**
(`schedule[0] == END`); nén TRƯỚC coin/note_spoken (họ R-08 — lời khuyên không tồn tại thì không
rút coin, không tiêu suất); đường thi hành END→END_SHIFT tận dụng `_ACTION_MAP` đã nối sẵn.

- `advice_bridge.py`: cờ `sp_end_only` + cổng trong `consult`
- `configs/pilot_dongda.yaml`: khoá mới có reader (cổng `test_config_flags_wired` xanh)
- `tests/test_e4_e05_endshift.py`: 4 test (mặc định TẮT · nén không rút coin · END đi qua ·
  đối chứng cờ tắt) — 35 passed cùng consumer
- `scripts/run_e05_endshift.py` + artifact `research/audit/2026-08-06-e2/e05-endshift-30.json`

## Kết quả đo: TRƠ TUYỆT ĐỐI

30 seed, coverage=all, positioning off (cô lập một cơ chế): **Δ = 0.00, CI (0,0) trên MỌI metric**
— kênh không nói lần nào. Lý do cấu trúc: thế giới hiện chạy `cash_cost_vnd_per_km = 0` ⇒
`online_net ≥ 0` bất cứ khi nào còn cầu ⇒ DP không bao giờ chọn END làm hành động ĐẦU LỊCH tại
điểm consult (dừng sớm chỉ tối ưu khi chạy CÓ GIÁ).

## 🔴 Bài học cấp chương trình (nối UPDATE-153)

Hai điểm dữ liệu độc lập cùng một mẫu: ADV-01 (mốc thưởng vào Bellman) đổi lịch S2 **0 lần**
in-sim; E-05 (kết ca sớm) nói **0 lần** in-sim — đều vì **chi phí vận hành = 0**.

> **Kênh mà giá trị dựa trên CHI PHÍ đều trơ trong sim zero-cost. Giá trị đo được của advisor
> trong sim hiện tại nằm ở các kênh THỜI GIAN/VỊ TRÍ** (positioning +4,5k đã đo; swap-early —
> tránh hàng đợi; meal/rest-timing — dồn downtime vào khung vắng).

Hệ quả cho thứ tự E4: **E-03 (đổi pin sớm tránh giờ đỉnh) và E-02 (meal-timing) lên đầu**;
E-05 giữ cờ (đường sản phẩm dùng `policy_costs_as_of` với phí thật 2029 sẽ khác) nhưng KHÔNG
đo thêm ở config zero-cost. Nếu muốn kênh chi-phí sống trong sim: cần sweep `cash_cost/swap_fee`
theo cohort — việc CÓ CHỦ ĐÍCH riêng, không gài mặc định.

## Kiểm chứng

Test 35 passed · flag-wired xanh · phép đo 12,2′/30 seed · behavior mặc định không đổi (cờ TẮT,
consult nguyên vẹn — test đối chứng).

## Visual
`NOT_APPLICABLE` — kênh trơ + TẮT mặc định; không có gì trên màn hình.

## Follow-up
- E-03 swap-early (ưu tiên 1 mới của E4) · E-02 meal-timing (ưu tiên 2).
- Nợ ghi: `D-E4-01` — sweep chi phí ≠ 0 để đánh thức họ kênh chi-phí (S2-schedule, end-shift)
  nếu Cường muốn nghiên cứu nhánh này; kèm prereg nếu định claim.
