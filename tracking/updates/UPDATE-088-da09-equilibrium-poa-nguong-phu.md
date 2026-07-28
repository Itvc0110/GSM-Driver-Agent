# UPDATE-088 — Cycle Q: ĐA-09 §2.2 có số — cân bằng TỒN TẠI, heatmap-residual tự phá, không có bi kịch phủ-cao

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường** (chỉ thị: *"làm hướng tốn thời gian,
  khó, nhiều giá trị nhất"*)
- **Loại:** research (multi-agent) + 1 hook code nhỏ (advisor-only belief override)
- **Hồ sơ chính:** `research/simulation/multi-agent-equilibrium.md` (file plan C1 gốc đã hứa)
- **Artifacts:** `26a/26b-ficplay-*.json` (5 seed × 7 vòng × 2 toán tử) · `27-poa-30seed.json`
  · `28-coverage-curve-30seed.json` — tổng ~220 run

## Ba câu trả lời (chi tiết + bảng: hồ sơ equilibrium)

1. **Cân bằng TỒN TẠI, hội tụ ~1 vòng** khi belief advisor = tổng cầu thực (γ=1, Δbelief tụt
   về mức nhiễu 6%/vòng) — và điểm bất động ≈ chính `λ_config` ⇒ thiết kế hiện tại đã đứng ở
   cân bằng. **Twist giá trị hơn**: belief thuần-residual (γ=0 — *"chỗ nào đơn chết thì đẩy
   người tới"*, chính là heatmap thích nghi ngây thơ) **không bao giờ hội tụ** (Δbelief kẹt
   ~0,5; alloc churn 0,4→1,7) và **tệ vĩnh viễn** (served −2đp, payout −6~8k). Cảnh báo
   production §14.1 cụ thể: tín hiệu cầu thích nghi PHẢI giữ khối cầu đã-được-phục-vụ.
2. **Price of anarchy khiêm tốn**: adherence thật (0,30–0,75) đã lấy **70% served / 73% đơn
   chết / 51% payout** của mức tập-trung-hoá (adherence 1.0). Quyền từ chối của tài xế đắt
   ~+4,3k/người còn lại — đòn bẩy có, không phải nút thắt.
3. **Không có ngưỡng tự-triệt-tiêu**: served tăng đơn điệu theo phủ (10%→100%: +0,6→+1,74đp);
   người vào sớm hưởng đậm nhất (+5,9k @10%); **bẫy free-rider ở phủ 25–50%** (người không
   dùng +4,0k > người dùng +3,3k) — rủi ro adoption chững, hướng xử lý ghi DEFERRED chờ duyệt.

## Code

Hook duy nhất: `advice.market_demand_override` (UPDATE trong commit trước, `20da231`) — 3 test,
mutation MQ1, test cách ly "planner tắt ⇒ override vô hình từng bit".

## Kiểm chứng

Smoke 2 seed trước khi đốt full · mỗi vòng ghi JSON đầy đủ (field + alloc + metrics) · PoA/
coverage dùng lại A-side artifact 25 đúng seed · suite trước cycle **633 passed / 5 skipped**
(hook đã nằm trong suite này? — hook merge sau suite: đã chạy riêng
`test_market_demand_override + test_market_state_sim_producer` = 14 passed; full suite kế tiếp
sẽ gộp).

## Visual verification

`BLOCKED` — gộp V-17; đề xuất thêm: vẽ đường cong phủ (bảng §3) thành chart trong khu Mô phỏng
khi làm R2 decision-trace.

## Adversarial self-review / flaws found

1. **5 seed/vòng cho fictitious play** — đủ tách bậc hội tụ (0,5 vs 0,06 là một bậc độ lớn),
   không đủ so metric từng vòng; đã ghi rõ trong hồ sơ.
2. **Toán tử belief v1** (mean seed, không EMA/smooth) — kết luận "γ=0 phân kỳ" có thể dịu đi
   với EMA; chưa quét. Nhưng bài học "phải giữ khối served" đứng vững vì cơ chế (mass residual
   co lại → ranked cells co → churn) không phụ thuộc smoothing.
3. **PoA đo trên B3w wait_only** — mức tập trung "thật sự" (solver toàn cục gán mọi hành động,
   không chỉ standby) sẽ cao hơn; PoA ở đây là cận DƯỚI của khoảng cách.
4. **Free-rider gap 25–50% chưa có CI riêng** (điểm ước lượng từ 30 seed) — trước khi dùng nó
   ra quyết định sản phẩm cần bootstrap CI cho hiệu covered−uncovered.
5. Coverage dùng seed 3000–3029 (trùng dải confirmatory) — chấp nhận được vì đây là nghiên cứu
   mô tả, không phải nghiệm thu; ghi để ai đọc sau biết.

## ⏳ Nhắc PENDING-REVIEW

**Đề xuất cấu hình UPDATE-087 vẫn chờ Cường duyệt bật** (B3w wait_only + shift_plan off).
V-01..V-17 · Q-03/Q-04/Q-07 · B-02 treo. Câu phụ Q-12 (tiêu chí per-archetype) chưa chốt.
