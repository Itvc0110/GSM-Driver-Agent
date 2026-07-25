# UPDATE-041 — PI-5b: S7 IdleReduction (UC5) + fix trạng thái bất khả idle > online

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường duyệt plan PI-5b)
- **Loại:** feature + fix
- **TODO / User story liên quan:** Real-data PI-5b; UC5 "Reduce Idle"; US-F2/US-F3; D-004b

## Tóm tắt

Thêm **S7 IdleReduction** — solver đầu tiên khai thác `public_driver_hex_tracking` (bảng LỚN NHẤT: 1.09M dòng/90 ngày, trước đây chưa ai dùng). Nối vào F2 (trong ca) + F3 (sau ca). Tuân đủ **5 điều kiện an toàn D-004b**. Suite **313 pass**. **1 trạng thái BẤT KHẢ lộ khi đọc output** (test vẫn xanh): idle 1300 phút > online 4.8h — đã fix tận gốc + invariant test.

## Guardrail D-004b (reposition mở CÓ ĐIỀU KIỆN) — thực thi ra sao

| Điều kiện | Cách thực thi (có test) |
|---|---|
| 1. B1: khuyên MỨC THỜI GIAN, **không chọn điểm đứng hộ** | Solver KHÔNG sinh/không đề xuất ô H3 nào; `hex` chỉ dùng thống kê. Test: ô H3 không xuất hiện trong solution/digest/message |
| 2. Khu vực chỉ nhắc **nhiệm vụ CHÍNH THỨC của hãng** | Chỉ nói khi data có `campaign_id`; không có → im lặng. Test 2 chiều |
| 3. Cảnh báo tỷ lệ nhận | `WARN_ACCEPTANCE` luôn trong `caveats` (test mọi nhánh) |
| 4. Demand = PROXY có nhãn, không hứa thu nhập | `WARN_PROXY` luôn có; test digest không chứa "đảm bảo/chắc chắn/cam kết" |
| 5. Không khuyên nhận/từ chối đơn | Không có field/câu nào về đơn cụ thể |

## Chi tiết

- `l3/idle_reduction_input` (mới) + `solver_report.solver` enum **+`idle_reduction`** + registry + CHANGELOG.
- `features/from_l1r.derive_idle_reduction_input_l1r`: lọc `tracking_status="idle"` (≥5 phút) theo ngày, demand PROXY theo giờ từ `trips`, `active_reposition` từ `campaign_id`.
- `solvers/idle_reduction.py`: tổng/dài nhất/`idle_share`; tìm **khung vừa chờ nhiều vừa nhu cầu thấp** → gợi ý dồn nghỉ/đổi pin vào đó. **Không bịa vấn đề** khi chờ ít (ngưỡng 45 phút tổng / 25 phút một khoảng).
- Router F2/F3 + intent `idle_wait` ("đứng chờ/chờ lâu/ế khách"); context_pack whitelist; template F2/F3.

**Mẫu output THẬT (verify=True):**
> "Hôm nay anh/chị chờ tổng **304 phút**, nhiều nhất quanh khung **13h** — khung này nhu cầu thường thấp, anh/chị có thể dồn nghỉ/đổi pin vào đó. Ngoài ra, anh/chị đang có nhiệm vụ di chuyển của hãng (chưa hoàn thành)."

Đối chiếu research: idle 304ph/11.24h online = **45%** — khớp dải utilization FT 45-55% (`realism-benchmarks`); khung 13h khớp "dead hours 13-16h" (`community-insights`). Hai tín hiệu độc lập ⇒ tăng tin cậy.

## Adversarial self-review / flaws found

1. **BUG-PI5b-01 — TRẠNG THÁI BẤT KHẢ (nghiêm trọng, lộ khi ĐỌC output, test xanh)**: generator gán MỌI dwell >5 phút là `idle` ⇒ khoảng nghỉ/offline dài (đứng yên qua đêm) bị tính "đang chờ khách" → *"chờ tổng **1300 phút** (100% online)"* trong khi online chỉ **4.82h**. Vi phạm bảo toàn thời gian.
   - **Root cause 2 lớp**: (a) data — thiếu phân biệt offline vs idle; (b) solver — `min(1.0, …)` **CHE** mâu thuẫn thay vì nêu.
   - **Fix**: generator gán `tracking_status="offline"` khi dwell > 90 phút (enum đã có sẵn); solver giữ kẹp hiển thị NHƯNG phát `data_warning` khi idle > online.
   - **Invariant test**: Σ idle ≤ online × 60 trên mọi driver-day có idle (chạy trên data thật) + test cờ cảnh báo khi input mâu thuẫn.
2. Ngưỡng "đáng lưu ý" (45/25 phút) là **ASSUMPTION** — tránh cảnh báo nhiễu; cần hiệu chỉnh khi có feedback thật.
3. `demand_by_hour` là PROXY toàn nền tảng (không cá nhân hoá theo khu của tài xế) — chấp nhận ở mức khuyên THỜI GIAN; nếu sau này cá nhân hoá theo khu thì phải xét lại D-004b.
4. Ngưỡng offline 90 phút cũng là ASSUMPTION (tài xế nghỉ trưa 45-90 phút là bình thường theo research) — ghi nhãn.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `schemas/l3/idle_reduction_input.schema.json` | tạo |
| `schemas/advisor/solver_report.schema.json`, `schemas/CHANGELOG.md`, `src/gsm_core/schema_registry.py`, `tests/test_schemas.py` | sửa (additive) |
| `src/gsm_core/features/from_l1r.py` | sửa (+derivation) |
| `src/gsm_core/solvers/idle_reduction.py` | tạo |
| `src/gsm_core/mockgen/realdata.py` | **sửa (BUG-PI5b-01: offline vs idle)** |
| `src/gsm_core/advisor/{router,context_pack,templates}.py` | sửa (wiring F2/F3) |
| `tests/test_idle_reduction.py` | tạo (14 test) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| S7 chạy đúng, guardrail D-004b đủ | `OBSERVED-CODE` | 14 test + đọc output | Cao | — |
| idle ≤ online (bảo toàn) | `OBSERVED-CODE` | invariant test trên data thật | Cao | — |
| idle_share 45% hợp thực tế | `PROXY` | realism-benchmarks util FT 45-55% | TB | ngưỡng cảnh báo lệch |
| ngưỡng 45/25 phút, offline 90 phút | `ASSUMPTION` | tránh nhiễu + pattern nghỉ trưa | TB | cảnh báo quá nhiều/ít |

## Kiểm chứng
`tests/test_idle_reduction.py` **14 pass**; full suite **313 pass**. Chạy thật trên `generate_realdata` → view/report hợp schema, e2e F2 verify pass. **CHƯA kiểm chứng:** ngưỡng với data GSM thật; LLM live; UC6/UC7 chưa làm.

## Visual verification
- **Status:** `NOT_APPLICABLE` (chưa có UI) — sample text ở mục "Mẫu output THẬT".

## Expansion checkpoint (T-039)
1. **Schema:** không đổi ngoài view mới (additive).
2. **Bài toán tối ưu:** S7 xong ⇒ 7 solver; còn UC6/UC7 thiên reasoning (PI-5c).
3. **Tính năng:** `hex_tracking` mở thêm khả năng: đo hiệu quả nhiệm vụ reposition (reached_target rate) theo cohort — ứng viên phân tích cho GSM.

## Follow-up / defer phát sinh
- **PI-5c**: UC6 penalty-explain + UC7 anomaly-alert.
- Hiệu chỉnh ngưỡng idle (45/25) + offline (90 phút) khi có data thật/feedback.
- Cân nhắc đo `reached_target` rate để đánh giá hiệu quả campaign reposition của GSM.
