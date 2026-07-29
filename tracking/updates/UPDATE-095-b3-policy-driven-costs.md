# UPDATE-095 — B3: POLICY quyết định biến chi phí sống/chết theo (track, as_of)

- **Ngày:** 2026-07-29 (chiều)
- **Người thực hiện:** AI agent dưới claim Cường (PLAN-cycle-wx Phần B — đã duyệt)
- **Loại:** schema bump (quy trình Cycle V) + core policy + solver
- **Hiện thân tầm nhìn:** vế A5 TRỌN VẸN (*"hàm tối ưu cập nhật giá trị biến theo thay
  đổi chính sách"*) + phần RULE của ý A1 (*"chính sách free đổi pin hết hạn thì bỏ biến
  đó, hay điền arg −xx đồng thay vì 0"* — OPEN-THREADS §A1). Không LLM, không bịa số:
  mọi giá trị từ `policy_bundle` versioned (§5).

## Cơ chế

| Mảnh | Nội dung |
|---|---|
| Schema | `policy_bundle` 1.0.0→**1.1.0**: +`costs` optional (battery_free_until 2029-03-31 official · swap_fee_vnd 9000 · battery_rent · swap_range_km_per_pack · cash_by_track). Snapshot @1.0.0 từ git HEAD; upcaster stamp-only (KHÔNG bịa costs cho record cũ); LATEST_VERSIONS pin; CHANGELOG |
| `resolve_cost_params(policy, as_of)` | Bảng tra THUẦN → mỗi số hạng {value, state, reason, source}. **Ba trạng thái, CẤM gộp**: ACTIVE / OFF_BY_POLICY ("biết là miễn phí — BỎ biến, kèm hạn") / UNKNOWN ("không biết — dùng 0 + caveat, không bịa"). PolicyBundle thêm `track`+`costs` |
| Solver | `shift_dp.solve` đọc `params["policy_costs_as_of"]` (opt-in qua params — guard chống-future-leak pin chữ ký (spi, policy, params) và as_of là ngữ cảnh "bây giờ", không phải data tương lai). `terms_active[]` trong solution NÓI RA số hạng nào sống/chết + lý do (câu hỏi #2 của Cường); explicit `cash_cost_vnd_per_km` THẮNG policy (đường sim B2); UNKNOWN ⇒ caveat |

## Hành vi chứng minh được (test)

- as_of `2026-07-29` (trước hạn): battery **OFF_BY_POLICY**, reason nêu "2029-03-31";
  cash platform = 0 ACTIVE.
- as_of `2029-04-01` (sau hạn): battery **ACTIVE** 9.000đ/lượt; cash = **150đ/km**
  (9000÷60km/pack) — *cùng tài xế, chi phí khác, KHÔNG ai sửa code* — đây chính là
  "hàm tối ưu cập nhật theo policy" thành sự thật đo được.
- Track charge: cash 80đ/km luôn sống. Bundle 1.0.0 không costs: UNKNOWN ≠ OFF + caveat.
- Không `policy_costs_as_of`: KHÔNG terms_active — mọi caller cũ nguyên vẹn.

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| TDD | 15 test mới đỏ trước (collection error → xanh); guard future-leak BẮT thiết kế đầu (as_of trên chữ ký) → refactor về params opt-in — guard hoạt động đúng vai |
| Bộ test | b3_policy_costs (15) + c1_cost_term + shift_dp + schemas + schema_versioning + advisor_pipeline = **81 passed**; bước 5 quy trình bump: mockgen + l1r + lifecycle = **61 passed** (record persist 1.0.0 vẫn pass) |
| Caller cũ | test_no_as_of_no_terms_backward_compat + tiebreak determinism; sim KHÔNG truyền key mới ⇒ zero delta đường sim |
| Chưa làm | bridge/production truyền `policy_costs_as_of` (đường sim giữ explicit-cash B2 có chủ ý — policy bundle của SIM chưa có costs; nối khi bundle sim mang costs hoặc đường production bật); kịch bản ĐO as_of>2029 trên sim 30 seed (cần bundle sim có costs — cycle sau) |

## Visual verification

`NOT_APPLICABLE` — solver/schema layer; đường sim không đổi (không truyền key mới).

## Adversarial self-review / flaws found

1. Guard future-leak bắt được thiết kế đầu của chính tôi (thêm as_of vào chữ ký) — sửa
   thành params opt-in; ghi nhận guard T-046 làm đúng việc.
2. Quy đổi swap_fee→đ/km dùng `swap_range_km_per_pack` danh định (60km) — cận trên của
   chi phí thực (pack không cạn 100% mới đổi); ghi trong reason, chấp nhận cho v1.
3. `battery_rent_vnd_month` có trong schema nhưng resolve chưa dùng (cần quy tắc phân bổ
   tháng→ngày→km — cần số ngày làm việc, chưa có nguồn chốt) — để UNKNOWN-by-omission,
   KHÔNG bịa; ghi nợ.
4. Sweep B2 (artifact 29) đang chạy nền lúc viết — chưa có số ngưỡng.

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 · Q-03 · Q-04 · Q-07 · BUG-MOCKGEN-CLI · ĐA-05 chờ verdict (UPDATE-091) ·
B6-PARITY chờ xếp ưu tiên · sweep B2 artifact 29 (nền) · format_checker qua plan mode.
