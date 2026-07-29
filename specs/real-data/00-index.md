# Real GSM data integration — masterplan index

Cập nhật: 2026-07-24 · Trạng thái: **DESIGN blueprint** (chưa code) · Người: AI agent (yêu cầu Cường)
Kích hoạt: Cường cấp **schema thật gsm-data-prod** (13 bảng, 2026-07-24). Quyết định chốt: (1) chưa BQ access → tool = interface+PII, test mock; (2) **re-ground về bảng thật**; (3) **mở rộng UC5-UC8**. Yêu cầu: tách phần nhỏ, chi tiết, **plan từng phần trước khi code**.

> **Cycle này CHỈ sản xuất blueprint** (catalog + 7 part-plan). Implement = các cycle PI-1..PI-6 riêng (P7 roadmap), mỗi cycle có plan+test.
>
> **Trạng thái impl (UPDATE-034, 2026-07-24):** ✅ **PI-1** (13 schema `l1r/*`) + ✅ **PI-2** (`mockgen/realdata.py` sim→aggregate, 13 bảng, R1/R3/R4 verify, suite 201). Còn PI-3 (DataSource tool), PI-4 (solver+S5/S6), PI-5 (UC5-8), PI-6 (external). R2 statistical verify chưa chạy.
>
> **⚠ Đính chính 2026-07-29:** **PI-4** (adapter L1R→L3 + S5/S6, UPDATE-037/038) và **PI-5** (S7/S8/S9
> + router UC5-8, UPDATE-040..043) đều **DONE**. **R2 statistical verify ĐÃ CHẠY** — xem
> `research/experiments/mockgen/ROUND-2-stats-report.md` và
> `research/experiments/mockgen-realdata/ROUND-2-stats-report.md`. Còn lại: **PI-3 DEFERRED chủ ý**
> (`D-GCP-01` — publish chạy trên mock/local, không phải blocker cần unblock) + **PI-6** (External,
> key/config đã có nhưng provider/cadence chưa implement).

## Các phần

| Part | File | Nội dung |
|---|---|---|
| Catalog | [`docs/data-catalog/gsm-data-catalog.csv`](../../docs/data-catalog/gsm-data-catalog.csv) (+`.xlsx`) | 13 bảng × 10 cột kiểm soát; sinh bởi `scripts/build_data_catalog.py` |
| P1 | [`01-data-catalog-and-analysis.md`](01-data-catalog-and-analysis.md) | phân tích sâu từng bảng/trường + glossary + câu hỏi GSM |
| P2 | [`02-schema-reground-plan.md`](02-schema-reground-plan.md) | 13 bảng → L0-L3 mới (`l1r/*`); cũ→giữ/deprecate |
| P3 | [`03-mockgen-grandplan.md`](03-mockgen-grandplan.md) | field-by-field cho gen-agent + 4 vòng verify (re-read từng row/col/table) |
| P4 | [`04-datapull-tool-plan.md`](04-datapull-tool-plan.md) | DataSource, read-only cứng, PII policy, techstack/env cần chốt |
| P5 | [`05-gap-analysis-and-supplements.md`](05-gap-analysis-and-supplements.md) | gap + mock-supplement + **external API brainstorm** + techstack/env |
| P6 | [`06-new-features-and-optimization.md`](06-new-features-and-optimization.md) | S5 khoan, S6 mission-knapsack, idle/penalty/anomaly; map UC↔F |
| P7 | [`07-affected-parts-and-deployable-roadmap.md`](07-affected-parts-and-deployable-roadmap.md) | affected audit + roadmap PI-1..6 + kiểm thử/giả lập |

## Kiểm tra ĐỦ 6 Ý Cường

| Ý | Yêu cầu | Phần đáp ứng |
|---|---|---|
| #1 | plan mock + Excel catalog vào repo (check hàng/cột) + nghiên cứu từng bảng/trường | Catalog (13 hàng verify) + P1 |
| #2 | grand plan để gen-agent gen tốt; harness re-read từng dòng/cột/bảng | P3 (field-by-field + 4 vòng verify) |
| #3 | gap vs scaffold; mock-supplement (future-harvest? external API vd Google Map street≠customer); feature/optimization/feature-from-new-fields | P5 (gap+external) + P6 (feature/opt) |
| #4 | plan tool kéo data (PII, read-only) | P4 |
| #5 | affected parts, todo sau, deployable + kiểm thử/giả lập — TRỪ AI-Advisor perf/observation/CICD/optimize | P7 (loại trừ ghi rõ) |
| #6 | bảng alert/explain/mini-task giống output feature ta | P6 §1/§4 (UC6/7/8 = envelope F3/alert ta) + P1 (usecase) |

## Cần Cường/GSM chốt (gom từ các part)

1. **GSM semantics** (P1§4): định nghĩa `total_core_order`/`stoppoints`/`ATA`/`is_ddi_mission`/`reward_level`; **vị trí số target KPI tuần**; **cột thật 5 bảng thiếu** (trips, penalization, frauds, user_mission_progress); `revenue_not_relate_driver` gồm gì.
2. **BQ access + auth** (P4§6): khi nào cấp credentials; cơ chế auth; ENV (`GSM_GCP_PROJECT`, dataset, `GOOGLE_APPLICATION_CREDENTIALS`, `GSM_PII_SALT`).
3. **External API techstack/key** (P5§4): có dùng Google Maps/Weather/holiday không; cấp key; budget/quota.
4. **weekly-khoan open decision (d)**: khoán trên gross vs driver_payout (`policy-weekly-khoan-model.md`).

→ Không tự quyết/điền env; hỏi trước khi thêm dep hoặc kéo data.
