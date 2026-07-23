# UPDATE-032 — Design spec: mô hình khoán tuần + clawback + điểm-theo-dịch-vụ

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường: "go on with what you think is best")
- **Loại:** docs (design spec, spec-first)
- **TODO / User story liên quan:** D-POL-01/02/03/05; T-039; US-F1, US-F3

## Tóm tắt

Viết design spec `specs/policy-weekly-khoan-model.md` biến các gap policy (D-POL-01..05 từ UPDATE-031) thành blueprint code được: 3 cơ chế tuần tách bạch (thưởng-điểm / khoán-clawback / bỏ-phạt), schema mở rộng additive, solver mới S5 `WeeklyKhoanFeasibility`, ledger mapping (không kind mới), và danh sách field **data thật GSM** cần pull. **Không code sản phẩm** — số khoán/clawback image-locked, code với số giả dễ rework; spec-first là pattern của repo (4 solver đều spec trước).

## Chi tiết cập nhật

Đọc `policy.py`/S1: model hiện = điểm/cuốc→tier→thưởng, đơn vị ĐIỂM, xử lý như NGÀY. Xác định:
- `day_bonus_tiers` đặt tên nhầm (research: tiers là TUẦN) → daily-proxy là simplification có nhãn (open decision c).
- `PayoutLedger.kind` đã có `deduction`+`week_bonus` → clawback/bonus map được, **không cần kind mới**.
- `ServiceCatalog.service_type` đã có → điểm-theo-dịch-vụ nối vào.
- `thresholds.forced_accept_below` (auto-accept <50%) thuộc regime đã bỏ 23/02/2026 → đề xuất deprecate.

Spec đề xuất: `points.by_service` (optional override), `weekly_quota{min_revenue_vnd, min_active_days, clawback_rate, market_scope}` (optional, số TBD/real-data), S5 solver thuần-math cùng SolverReport envelope (gap doanh số tuần, clawback risk, feasibility theo giờ/ngày còn). Chống double-count: (A) thưởng-điểm và (B) khoán-VND là 2 chiều khác, không gộp.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `specs/policy-weekly-khoan-model.md` | tạo | design spec |
| `tracking/TODO.md` | sửa | D-POL-01/02 có blueprint |
| `tracking/updates/UPDATE-032-*.md` | tạo | file này |
| **KHÔNG đụng** `schemas/**`, `src/gsm_core/**`, mock, corpus T-004 | — | implement ở cycle sau |

## Docs đã cập nhật kèm theo
TODO: D-POL-01/02 gắn spec. DEFERRED: không đổi (spec làm rõ, chưa đóng gap). SCOPE/USER_STORIES: không đổi.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| 3 cơ chế tuần (A/B/C) tách đúng | `OBSERVED` | policy-refresh + official | Cao | model trộn cơ chế |
| `deduction`/`week_bonus` đủ map clawback/bonus | `OBSERVED-CODE` | spec §1 PayoutLedger.kind | Cao | thêm kind thừa |
| `by_service`/`weekly_quota` optional ⇒ không phá mock/test | `OBSERVED-CODE` | schema additive | Cao | 162 test fail |
| Số khoán/clawback/điểm×service | `image-locked/TBD` | ảnh official | — | phải pull data thật |
| Khoán tính trên gross vs payout | `UNVERIFIED` (open d) | — | — | đơn vị S5 sai |

## Kiểm chứng

Docs-only → **không chạy test** (full suite giữ 162, không đụng `src/`). Cross-check số cited về `policy-refresh-2026-07-24.md` + URL official; số chưa có = TBD. **Chưa kiểm chứng:** mọi con số khoán/clawback/điểm×service (image-locked); money-definition khoán (open d) — đều để data thật GSM.

### Seeds và scenarios
| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| đọc policy.py/S1/schema | xác định seam schema+solver | số thật |

## Visual verification
- **Status:** `NOT_APPLICABLE` — design spec, không simulator/UI.

## Adversarial self-review / flaws found
1. **Rework risk:** spec đề xuất field/số minh hoạ; nếu data thật khác STRUCTURE (không chỉ số) → sửa spec. Mitigation: field optional + open decisions a-d chốt trước code.
2. **Double-count (A) vs (B):** đã cảnh báo tách bạch trong spec §1.
3. **Daily-proxy tiers:** flag là simplification, không tự "sửa" thành weekly (open c) — tránh phá S1/mock ngoài kế hoạch.
4. **Không over-reach:** chỉ spec; không đụng schema/solver/mock/corpus. Ranh giới §5 giữ (agent không tạo số policy).
5. **Flaw mở → map:** open decisions a-d + D-POL-01..05.

## Expansion checkpoint (T-039)
1. **Schema:** `points.by_service`, `weekly_quota`, deprecate `forced_accept_below` (D-POL-02).
2. **Bài toán tối ưu:** S5 `WeeklyKhoanFeasibility` (doanh số/tuần) — solver mới từ residual, thuần math (D-POL-01).
3. **Tính năng:** F1 kế hoạch tuần "tránh truy thu / đạt khoán"; F3 tiến độ khoán thay cảnh báo phạt.

## Follow-up / defer phát sinh
- Open decisions a-d → cần Cường chốt trước khi mở D-POL-01/02 (implement).
- Thứ tự implement: D-POL-02 (schema) → D-POL-01 (S5) → D-POL-03 (mock regen), mỗi bước cycle riêng có plan.
