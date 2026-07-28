# Multi-agent equilibrium của advice diện rộng — ĐA-09 §2.2, đo bằng số

Ngày: 2026-07-28 · Cycle Q · Trả lời ba câu hỏi spec `advisor-objective-model-v2.md` §2.2 đặt ra
từ 2026-07-27 mà tới nay chưa ai đo. Nền: B3w (CHỈ positioning wait_only — cấu hình đề xuất
UPDATE-087), thế giới α=0.4, estimator không bias (Q-11).

**Artifacts:** `26a-ficplay-gamma0.json` · `26b-ficplay-gamma1.json` · `27-poa-30seed.json` ·
`28-coverage-curve-30seed.json` (thư mục audit hiện hành).

---

## 1. Câu hỏi 1 — Điểm cân bằng có tồn tại không? **CÓ — và twist quan trọng hơn chính nó**

**Thiết kế**: fictitious play trên belief-cầu của ADVISOR (hook `advice.market_demand_override`
— chỉ planner đọc, bản năng tài xế bất biến, có test cách ly). `d⁰ = λ_config`; vòng k chạy 5
seed CRN với belief `d^(k-1)`, rồi `d^k` = trường đơn-EXPIRED (+ γ·SERVED) theo (giờ, ô đón)
trung bình trên seed. K=6.

| vòng | γ=0 (thuần residual) served / expired / payout_mean | γ=1 (tổng cầu thực) served / expired / payout_mean |
|---|---|---|
| 0 (λ_config) | 0,8126 / 168,6 / 256.701 | 0,8126 / 168,6 / 256.701 |
| 1 | **0,7890 / 196,4 / 249.040** | 0,8152 / 166,2 / 259.435 |
| 2 | 0,7928 / 195,6 / 251.531 | 0,8080 / 177,8 / 258.559 |
| 3–6 | 0,792–0,799 / 190–195 | 0,802–0,814 / 166–178 |
| Δbelief/vòng | **kẹt ~0,49–0,71** (không hội tụ) | **~0,06–0,07 ngay từ vòng 1** (≈ nhiễu) |
| Δalloc/vòng | nhảy 0,42 → 1,72 (churn) | tụt về 0,16–0,22 |

**Đọc:**

1. **γ=1 hội tụ gần như tức thì** — belief "tổng cầu thực" (chết + được phục vụ) là điểm bất
   động: advice loop TỰ-NHẤT-QUÁN, không dao động. Và điểm cân bằng đó **xấp xỉ chính
   λ_config** ⇒ dùng config demand làm belief advisor (thiết kế hiện tại) đã đứng ở cân bằng.
2. **γ=0 KHÔNG hội tụ và tệ vĩnh viễn**: gửi người tới *nơi đơn chết vòng trước* — chính là
   "heatmap thích nghi" ngây thơ mà ai cũng muốn build đầu tiên — làm served **−2đp**, payout
   −6~8k/người, và phân bố gán CHURN mãi (đuổi theo đuôi mình). Đây là *fallacy of composition*
   ở dạng động, đo được.

**Hệ quả production (§14.1)**: tín hiệu cầu thích nghi cấp cho advisor PHẢI giữ khối cầu
đã-được-phục-vụ (γ>0), không được chỉ nhìn phần hụt. Một pipeline "chỗ nào thiếu xe thì đẩy
xe tới" nghe hợp lý và **sai** — sai kiểu tự phá, không phải sai kiểu nhiễu.

## 2. Câu hỏi 2 — Price of anarchy: adherence thật đã lấy được ~50–73% mức tập trung

30 seed × {A · B3w adherence-THẬT (per-archetype 0,30–0,75) · B3w adherence-1.0}:

| | A | adherence THẬT | adherence 1.0 | **thật lấy được** |
|---|---|---|---|---|
| served | 0,7902 | 0,8073 | 0,8146 | **70%** mức tập trung |
| đơn hết hạn | 197,7 | 173,4 | 164,6 | **73%** |
| payout_mean/người | 247.925 | 252.511 | 256.836 | **51%** |
| HHI cung | 0,0130 | 0,0120 | 0,0112 | — (cả hai đều giảm) |

**Đọc**: cái giá của "tài xế được quyền từ chối" là phần 27–49% còn lại (~+4,3k/người và
+0,7đp served nữa nếu ai cũng nghe). **Cơ chế BỀN với adherence không hoàn hảo** — ở mức nghe
lời thật (0,30–0,75 theo archetype) đã ăn được đa số lợi ích hệ thống ⇒ nâng adherence là
đòn bẩy CÓ nhưng không phải nút thắt sống còn; và không bao giờ được lấy adherence-1.0 làm
kỳ vọng khi nói chuyện với stakeholder.

## 3. Câu hỏi 3 — Ngưỡng phủ: KHÔNG có bi kịch phủ-cao, nhưng có bẫy free-rider ở giữa

Δpayout/người/ngày so A cùng seed (30 seed; covered tách bằng đúng predicate của bridge):

| share | Δ người DÙNG | Δ người KHÔNG dùng | Δ tất cả | Δ served |
|---|---|---|---|---|
| 10% | **+5.876** | +1.555 | +2.131 | +0,60đp |
| 25% | +3.327 | **+3.986** | +3.796 | +0,98đp |
| 50% | +3.331 | **+4.032** | +3.674 | +1,13đp |
| 100% | +4.586 | — | +4.586 | +1,74đp |

**Ba phát hiện:**

1. **Lợi ích KHÔNG sập khi phủ tăng** — trả lời thẳng ĐA-09 #3: không có ngưỡng tự-triệt-tiêu;
   capacity ledger đã chặn đúng kịch bản dồn-cục làm hồ sơ `07` từng đo được served GIẢM.
   Served tăng ĐƠN ĐIỆU theo phủ ⇒ về hệ thống, càng đông càng tốt.
2. **Người vào sớm hưởng đậm nhất** (+5,9k ở phủ 10% — lợi thế khi tín hiệu còn khan hiếm).
3. **Bẫy free-rider ở phủ giữa**: tại 25–50%, người KHÔNG dùng hưởng **hơn** người dùng
   (+4,0k vs +3,3k) — người dùng trả chi phí km-rỗng của reposition, người đứng yên ở ô đông
   hưởng cạnh tranh loãng đi. Hệ quả sản phẩm: động lực cá nhân để *bắt đầu dùng* yếu đi đúng
   ở vùng adoption giữa — rủi ro adoption chững — trong khi lợi ích hệ vẫn đang tăng. Hướng
   xử lý (chưa làm, cần duyệt): ưu tiên phân bổ tốt cho người dùng lâu năm / gamification —
   ghi DEFERRED, không tự triển khai.

## 4. Giới hạn trung thực

- Cầu NGOẠI SINH trong sim (đơn không sinh thêm khi phục vụ tốt) ⇒ equilibrium ở đây là cân
  bằng CUNG-vs-BELIEF, không phải cung-cầu đầy đủ; thế giới thật cầu nội sinh một phần (giá,
  thời gian chờ ảnh hưởng người đặt).
- 5 seed/vòng cho fictitious play — đủ chỉ HƯỚNG hội tụ (Δbelief tách bậc rõ 0,5 vs 0,06);
  giá trị metric từng vòng mang nhiễu ±.
- Toán tử belief là ASSUMPTION v1 (trung bình seed, không smooth thời gian); operator khác
  (EMA, per-hour học riêng) chưa quét.
- Một ngày; chưa có hiệu ứng nhiều-ngày (memory) trong vòng lặp.
