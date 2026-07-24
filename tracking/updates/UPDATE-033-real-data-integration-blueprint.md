# UPDATE-033 — Real GSM data integration: catalog + 7 part-plan blueprint

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường cấp schema thật + yêu cầu plan chi tiết từng phần)
- **Loại:** docs (blueprint) + data (catalog)
- **TODO / User story liên quan:** T-038 (schema/mock), T-039 (expansion), D-POL-05 (data thật), UC1-UC8

## Tóm tắt

Cường cấp **schema thật gsm-data-prod (13 bảng)**. Chốt: re-ground về bảng thật; chưa BQ access (tool=interface+PII, test mock); mở rộng UC5-UC8. Sản xuất **blueprint** (data catalog Excel/CSV + 7 part-plan trong `specs/real-data/`) — chưa code schema/solver/mock/tool. Implement = 6 phase PI-1..PI-6 (cycle riêng).

## Chi tiết cập nhật

- **Catalog** `docs/data-catalog/gsm-data-catalog.{csv,xlsx}` (sinh `scripts/build_data_catalog.py`, canonical=Python list-of-dicts, assert 13 bảng). 5 cột gốc Cường + 5 cột ta (layer/PII/availability/consumer/mockgen).
- **7 part-plan** (`specs/real-data/00-index..07`): P1 phân tích sâu 13 bảng/trường; P2 re-ground L0-L3→`l1r/*`; P3 mockgen field-by-field (sim→aggregate) + 4 vòng verify; P4 DataSource read-only+PII; P5 gap + external-API brainstorm (Google Maps/Weather/holiday…); P6 S5/S6/idle/penalty/anomaly + map UC↔F; P7 affected audit + roadmap PI-1..6.
- **Insight**: data thật = pre-aggregated KPI daily/weekly (khác mock event-level) → mock phải aggregate ra đúng shape; weekly-KPI calculator = nền S5 khoán; mission tables = S6 mini-task; hex-tracking = idle/reposition (UC5); penalization/frauds = UC6/UC7 (đúng #6: giống output F3/alert ta).

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `scripts/build_data_catalog.py`, `docs/data-catalog/gsm-data-catalog.{csv,xlsx}` | tạo |
| `specs/real-data/00-index.md` … `07-*.md` (8 file) | tạo |
| `pyproject.toml` | +extra `catalog=[openpyxl]` |
| `tracking/{TODO,DEFERRED}.md`, `UPDATE-033` | sửa/tạo |
| **KHÔNG đụng** `schemas/**`, `src/gsm_core/**` (trừ script), mock, corpus T-004 | implement ở PI-cycle sau |

## Docs đã cập nhật kèm theo
TODO: block Real-data PI-1..6. DEFERRED: D-POL-01/02/03 hợp nhất vào PI; D-004 reposition mở lại có điều kiện; external chờ key. SCOPE/USER_STORIES: không đổi (UC5-8 nối qua feature mở rộng).

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| 13 bảng đúng như ảnh Cường | `FACT` | metadata Cường 2026-07-24 | Cao | catalog lệch |
| Data thật = pre-aggregated KPI | `OBSERVED` | field lists (rate/counts/week) | Cao | mockgen strategy sai |
| 5 bảng thiếu cột → cần xin GSM | `OBSERVED` | "chưa có cột" | Cao | infer sai shape |
| target KPI tuần chưa thấy trong 21 cột kpi_calculator | `OBSERVED` | field list | TB | S5 thiếu target→hỏi GSM |
| Mapping l1r + S5/S6/UC5-8 khả thi | `ASSUMPTION` | phân tích P2/P6 | TB | điều chỉnh khi impl |
| Số khoán/target/5-bảng-cột | `TBC-với-GSM` | image-locked/thiếu | — | dùng MOCK nhãn tới khi GSM trả |

## Kiểm chứng

Catalog sinh được: CSV+XLSX, **assert đúng 13 bảng**, 14 dòng CSV (header+13), verify chạy. Docs-only phần còn lại → **không chạy test code** (full suite giữ 162, không đụng `src/gsm_core` core). **Chưa kiểm chứng:** toàn bộ implement (PI-1..6) chưa làm; semantics GSM (P1§4) chưa xác nhận; số thật chưa có.

### Seeds và scenarios
| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| `build_data_catalog.py --extra catalog` | CSV+XLSX, 13 bảng | — |
| đọc schema/solver/spec | mapping l1r + UC↔F | impl thực tế |

## Visual verification
- **Status:** `NOT_APPLICABLE` — blueprint docs + catalog (không simulator/UI). Catalog Excel mở xem được cho Cường.

## Adversarial self-review / flaws found
1. **Re-ground risk:** viết lại L0-L3 lớn; giảm rủi ro bằng `l1r/` song song `l1/` (không phá 162 test một nhịp), deprecate có nhãn.
2. **Mock aggregate lệch:** nếu aggregate không nhất quán event nền → R3 cross-table verify bắt (P3). Ràng buộc rate=count/req, normal+rush=total, weekly=Σdaily ghi rõ.
3. **5 bảng thiếu cột:** infer có thể sai shape → nhãn TBC + hỏi GSM; mock swap khi có cột thật.
4. **External PROXY nhầm thành demand thật:** nhãn cứng PROXY + disclaimer (P5); không thành số tài chính.
5. **Techstack/env tự ý:** KHÔNG — mọi key/dep/BQ auth hỏi Cường (P4§6, P5§4, index §cần chốt).
6. **D-004 reposition mở lại:** có kiểm soát (theo mission GSM, capacity-aware) — ghi điều kiện, không tự bung heatmap.
7. Flaw mở → map: câu hỏi GSM + techstack/env (index §"cần chốt").

## Expansion checkpoint (T-039)
1. **Schema:** +13 `l1r/*`; DriverWeekState; +weekly_quota/service points (weekly-khoan).
2. **Bài toán tối ưu MỚI:** S5 khoán, **S6 mission-knapsack** (0/1 knapsack/LP scipy) — thuần math; idle-reduction (capacity+demand).
3. **Tính năng MỚI:** UC5 idle, UC6 penalty-explain (reasoning), UC7 anomaly-alert, UC8 mini-task; rating/quality KPI; đa dịch vụ (D-009).

## Follow-up / defer phát sinh
- **PI-1..PI-6** (P7): mỗi phase cycle riêng có plan+test; thứ tự phụ thuộc.
- **Cần Cường/GSM chốt** (index §): semantics 5 field + target KPI + 5 bảng cột; BQ access/auth/env; external key/techstack; khoán gross vs payout.
- D-POL-01/02/03 hợp nhất PI; D-004 reposition mở có điều kiện; corpus D-POL-04 vẫn owner Khánh.
