# SPEC — Mô hình khoán tuần + clawback + điểm-theo-dịch-vụ (design, chưa code)

Cập nhật: 2026-07-24 · Trạng thái: **⚠ 2026-07-29: S5 `WeeklyKhoanFeasibility` + schema `weekly_quota` ĐÃ CODE** (UPDATE-038/040) — D-POL-01/02 = **DONE-CODE**, `D-POL-03` (mock regen) = **PARTIAL**, cả ba vẫn **BLOCKED D-POL-05** (chỉ SỐ target thật từ GSM còn thiếu). Xem đính chính §6 bên dưới; blueprint gốc (spec-first, KHÔNG code trong cycle viết spec) giữ để đối chiếu lịch sử.
Nguồn: `research/policy/policy-refresh-2026-07-24.md` (Vận Doanh 23/02/2026), `core-data-schema-and-advisor-architecture.md` §1/§2 (schema + solver envelope), `src/gsm_core/policy.py` (PolicyBundle hiện hành).

> **Tại sao spec trước, không code ngay:** số khoán/clawback/điểm-theo-dịch-vụ **image-locked** trên trang official → phải pull **data thật GSM** (partnership). Code schema/mock với số giả bây giờ dễ phải làm lại. Spec này chốt STRUCTURE + MATH + field cần query để implement nhanh khi có số.

## 0. Vấn đề

Policy hiện hành (Vận Doanh 23/02/2026) đổi cơ chế kinh tế mà model hiện tại (S1 điểm/ngày) **không** biểu diễn: (i) **khoán tuần theo doanh số VND** + **truy thu (clawback) 20-40%** khi thiếu; (ii) **bỏ phạt ≤70%** (chỉ còn eligibility thưởng); (iii) điểm khác theo **service_type**. Cần tách bạch 3 cơ chế, mở rộng schema additive, và thêm 1 solver thuần-math cho khoán tuần.

## 1. Ba cơ chế tuần — TÁCH BẠCH (tránh trộn)

| Cơ chế | Đơn vị | Kích hoạt | Kết quả | Trạng thái |
|---|---|---|---|---|
| **(A) Thưởng tuần theo ĐIỂM** | điểm/tuần | tích điểm cuốc theo khung giờ×service | đạt tier → **cộng** `week_bonus`, IF eligibility (≥85% nhận & hoàn thành HN, ≥5 ngày) | ĐÃ CÓ (một phần) |
| **(B) Khoán tuần + CLAWBACK** | VND doanh số/tuần | không đạt khoán tuần | **truy thu** `clawback_rate × shortfall` (cấn ví) | **MỚI** |
| **(C) Phạt tỷ lệ nhận ≤70%** | — | — | **ĐÃ BỎ 23/02/2026** — chỉ giữ lịch sử có ngày | REMOVED |

**Lưu ý quan trọng (chống double-count):** (A) và (B) là **hai chiều khác nhau** — (A) *thưởng* theo điểm, (B) *phạt/truy thu* theo doanh số VND. Solver/composer KHÔNG được cộng gộp hay coi eligibility (A) là điều kiện của (B). Diễn giải F3 đổi từ "sát ngưỡng phạt" → "tiến độ khoán tuần + eligibility thưởng".

### 1A. Đính chính semantics tiers (bug tiềm ẩn)
Research (`bonus-programs.md`) nêu các mốc (400-699→200k…) là **điểm TUẦN**. Schema hiện đặt tên `day_bonus_tiers` và S1 xử lý như **ngày** (daily proxy). ⇒ Đây là **simplification có nhãn**, không phải fact. Spec đề xuất làm rõ chu kỳ (mục 2) và, khi implement, quyết định giữ daily-proxy hay chuyển weekly thật (open decision c).

## 2. Schema mở rộng (ADDITIVE / OPTIONAL / VERSIONED — chưa code)

Nguyên tắc: field mới **optional** → mock v1 + 162 test hiện tại **vẫn valid**; số = nhãn `REAL`/`MOCK`/`TBD`. Khi implement: bump `schemas/CHANGELOG.md` minor version.

### 2.1 `policy_bundle.points` — thêm chiều service
```jsonc
"points": {
  "peak": 10, "normal": 5, "peak_hours": [...], "window_hours": [...],   // giữ = default
  "by_service": {                          // MỚI, optional — nối ServiceCatalog.service_type
    "bike":    {"peak": 10, "normal": 5},
    "express": {"peak": 15, "normal": 10}, // số minh hoạ — THỰC = data thật (5-10-15-20-30)
    "ngon":    {"peak": 20, "normal": 15}
  }
}
```
`trip_points(hour, service_type=None)`: nếu có `by_service[service]` → dùng override; else fallback peak/normal. Backward-compat.

### 2.2 `policy_bundle.weekly_quota` — MỚI, optional
```jsonc
"weekly_quota": {
  "min_revenue_vnd": null,      // TBD — data thật; VND doanh số tối thiểu/tuần theo market+track
  "min_active_days": 5,         // HN 12/2025 (mốc 2: 4)
  "clawback_rate": 0.20,        // 0.20 toàn quốc; HN/HCM tới 0.40 (04/05/2026) — versioned/market
  "market_scope": "toan_quoc"   // vs "hn_hcm"
}
```
Nhãn `source` per số. `null` = chưa có data thật (không đoán).

### 2.3 Làm rõ / dọn
- `day_bonus_tiers`: thêm mô tả chu kỳ trong schema, hoặc thêm `bonus_period: "day"|"week"` (default giữ hành vi hiện tại để không phá test).
- `thresholds.forced_accept_below` (0.5, auto-accept <50%): **review deprecate** — cơ chế auto-accept/penalty thuộc regime đã bỏ 23/02/2026. Giữ field optional nhưng đánh dấu `deprecated` trong mô tả; solver không dùng cho quyết định active.

## 3. Solver mới **S5 `WeeklyKhoanFeasibility`** (thuần math, cùng SolverReport envelope)

Tách khỏi S1 (S1 = điểm/ngày; S5 = doanh số/tuần) — **khuyến nghị solver mới** để mỗi solver một đơn vị/chu kỳ rõ ràng, dễ verify (open decision a).

**L3 view mới `weekly_khoan_input`** (derive từ L1/L2, observable-only):
`driver_id, t_now, week_revenue_so_far_vnd, days_active_so_far, weekly_quota{min_revenue_vnd, min_active_days, clawback_rate}, days_remaining_in_week, hours_budget_remaining, avg_revenue_per_hour_hist (theo khung), policy_bundle_version, source`.

**Output `SolverReport`** (envelope §2 spec core):
- `numbers[]` có source: `gap_revenue_vnd` (khoán − week_so_far), `clawback_if_unmet_vnd` (= clawback_rate × gap, nếu không đạt), `hours_needed` (gap / avg_rev_per_hour), `feasible` (hours_needed ≤ hours_budget_remaining & days_active đủ).
- `sensitivity`: gap theo rate doanh số/giờ (−40%), theo số ngày còn lại.
- `infeasible_reason`: "không đủ giờ còn lại tuần" / "không đủ ngày active" / null.
- `confidence`: cao nếu có avg_rev_per_hour lịch sử; thấp nếu fallback.

**Ràng buộc §5 (bất biến):** mọi số từ policy_bundle + ledger; solver không bịa; deterministic; test failing-first; tách gross/payout (doanh số khoán tính trên **gross** hay **payout**? — **open decision, cần data thật** xác nhận khoán tính trên doanh số gross hay phần tài xế).

**US phục vụ:** US-F1 (kế hoạch tuần: "còn thiếu X doanh số để tránh truy thu / đạt khoán"), US-F3 ("tiến độ khoán tuần", thay cảnh báo phạt cũ). **KHÔNG** hứa thu nhập; nêu bất định.

## 4. Ledger mapping (không cần kind mới)

- Clawback → `PayoutLedger` entry `kind="deduction"`, `amount_vnd` âm/khấu trừ, `basis="{bundle_version}:week:{iso_week}"`.
- Thưởng tuần điểm → `kind="week_bonus"`.
- ⇒ Schema ledger **không đổi**; chỉ generator/model dùng đúng kind (D-POL-03).

## 5. DATA THẬT GSM cần pull (partnership — thay web/OCR; đóng D-POL-05)

| Field | Dùng cho | Ghi chú |
|---|---|---|
| `weekly_quota.min_revenue_vnd` theo market×track | S5, schema 2.2 | khoán tuần tối thiểu; image-locked |
| `clawback_rate` active theo market | S5 | 20% vs tới 40% |
| Khoán tính trên **gross** hay **payout** | S5 (đơn vị) | quyết định money definition |
| Bảng **điểm × service_type** | schema 2.1 | 5-10-15-20-30 chính xác |
| `min_active_days` chính thức + định nghĩa "ngày active" | (A)/(B) | ≥5 HN |
| Bảng tier điểm tuần mới nhất (sau 01/12/2025) | (A) | thay số research |
| Phạt ≤70% còn active không (reconcile mâu thuẫn 23/02 vs 05/06) | (C)/F0 | bản policy active của driver |

## 6. Decisions (Cường chốt 2026-07-24)

- **(a) ✅ CHỐT: Solver S5 MỚI** `WeeklyKhoanFeasibility` (tách khỏi S1). L3 view mới `weekly_khoan_input`.
- **(b) ✅ CHỐT: CHƯA implement — DỪNG Ở SPEC.** Không đụng schema/solver/mock cho tới khi có **data thật GSM** + Cường mở cycle. KHÔNG code với số MOCK ở giai đoạn này (ưu tiên realism, tránh rework số). **⚠ Đính chính 2026-07-29:** cycle ĐÃ được mở sau đó — schema + S5 **ĐÃ CODE** (UPDATE-038/040); chỉ SỐ target thật (min_revenue_vnd, clawback_rate active) vẫn thiếu (D-POL-05).
- **(c) ✅ CHỐT: GIỮ daily-proxy** cho tier điểm (gắn nhãn rõ là simplification); chỉ chuyển weekly thật sau, khi model tuần (S5) ổn.
- **(d) ✅ CHỐT 2026-07-24 (Cường): khoán tính trên GROSS (doanh số = `total_fee`).**
  - *Căn cứ:* văn bản Vận Doanh 23/02/2026 ghi "truy thu 20% phần **doanh số** chưa đạt" — "doanh số" = turnover; bảng thật tách bạch `total_fee` (gross) vs `commission` (driver payout).
  - *Nhãn:* **ASSUMPTION** (chưa có GSM xác nhận bằng văn bản định nghĩa) → S5 phải expose tham số `money_basis ∈ {gross, driver_payout}` mặc định `gross`, đổi được khi GSM xác nhận. Ghi rõ basis trong `SolverReport.numbers[].source`.

**Trạng thái:** spec = blueprint đóng băng; implement D-POL-01/02/03 **treo tới khi có data thật + Cường mở**. (b)/(d) chờ data; (a)/(c) đã chốt sẵn cho lúc implement.

> **⚠ Đính chính 2026-07-29:** cycle implement đã mở — **D-POL-01/02 = DONE-CODE** (S5 + schema
> additive, UPDATE-038/040); **D-POL-03 = PARTIAL** (mock re-ground xong shape, số chính xác GSM
> chưa có); cả ba **vẫn BLOCKED D-POL-05** cho tới khi có active quota/clawback numbers thật.

## 7. Migration & không phá

Field mới optional → `data/mock/v1` + toàn bộ test hiện tại (162) không đổi. Implement theo thứ tự: schema+validator+CHANGELOG (D-POL-02) → S5+L3 view+test failing-first (D-POL-01) → mock regen+verify (D-POL-03). Mỗi bước = coherent cycle riêng có plan. **⚠ Đính chính 2026-07-29: "162" là baseline TẠI THỜI ĐIỂM viết spec; suite hiện hành là ~707 test.**

## 8. Không thuộc spec này
Không code (schema/solver/mock). Không OCR ảnh. Không sửa corpus T-004 (Khánh — D-POL-04). Không quyết money-definition khoán khi chưa có data thật (để open decision d).
