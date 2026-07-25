# UPDATE-040 — PI-5a: nối S5/S6 vào pipeline advisor (khoán tuần + mini-task ĐẾN được tài xế)

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường duyệt plan PI-5a)
- **Loại:** feature
- **TODO / User story liên quan:** Real-data PI-5a; UC3 (khoán), UC8 (mini-task); US-F1, US-F2, US-F3

## Tóm tắt

S5/S6 (PI-4b) đã build nhưng **sản phẩm không gọi tới** — code chết với tài xế. Cycle này nối vào C6: router map F1/F2/F3 → solver mới, `context_pack` render key mới, `templates` (đường LLM-off bắt buộc) sinh câu khoán tuần + mini-task. Suite **299 pass**. **2 bug ngữ nghĩa lộ ra khi ĐỌC output thật** (test vẫn xanh) — đã fix + test riêng.

## Map UC → feature (advice_request.feature là enum ĐÓNG F0-F3, không tạo feature mới)

| Feature | Solver sau PI-5a |
|---|---|
| F1 trước ca | bonus_feasibility, shift_dp, **weekly_khoan** (UC3), **mission_knapsack** (UC8) |
| F2 trong ca | shift_dp, capacity_alloc, **mission_knapsack** |
| F3 sau ca | f3_patterns, **weekly_khoan** |
| F0 | giữ nguyên (policy Q&A + KB) |

Router thêm intent tiếng Việt: `mission_task` ("nhiệm vụ/mini task"), `weekly_target` ("khoán/doanh số tuần/truy thu"). Câu ngoài phạm vi vẫn → `out_of_taxonomy` (R5).

## Mẫu output THẬT (template mode, verify=True)

> **F1:** "Anh/chị còn thiếu **30 điểm** để chạm mốc thưởng **170.000đ**. Tuần này còn thiếu **852.474đ** doanh số để đạt khoán. **Nếu không đạt**, phần chưa đạt **có thể** bị truy thu khoảng **170.495đ**. Nhiệm vụ nên làm: 2 chuyến khung vàng (thưởng tối đa **30.000đ** nếu hoàn thành đủ điều kiện). Lưu ý: …không phải cam kết thu nhập."

## Adversarial self-review / flaws found (2 bug — test xanh nhưng CÂU SAI)

1. **BUG-PI5a-01 — số bị gán nhầm nhãn (nghiêm trọng)**: `n1/n2` lấy theo **VỊ TRÍ** trong `numbers_registry`. Thêm S5/S6 làm đổi thứ tự ⇒ render *"mốc thưởng **35585.2 vnd_per_hour**"* (tốc độ doanh số bị gọi là mốc thưởng) — vô nghĩa và sai lệch với tài xế. **Fix**: neo theo **GIÁ TRỊ** `bonus_feasibility.solution` (`gap_points`/`tier_vnd`); không có solver đó ⇒ **bỏ câu**, KHÔNG lấy bừa số khác (thà thiếu còn hơn sai).
2. **BUG-PI5a-02 — nói sai khi đã đạt khoán**: kiểm tra CHUỖI đã render (`"0đ"` là truthy) ⇒ tài xế đạt khoán vẫn bị nói *"còn thiếu 0đ … có thể bị truy thu 0đ"*. **Fix**: xét **giá trị số**; gap ≤ 0 → "đã đạt khoán doanh số"; clawback chỉ nói khi > 0.
3. **Verifier V1 bắt số trần `2`** từ TÊN nhiệm vụ "2 chuyến khung vàng" → thêm tên mission vào `_trusted_spans` (cùng trust-class tiêu đề policy, BUG-C6-03). **Giá trị thưởng vẫn bắt buộc từ `numbers_registry`** — không nới guardrail.
4. **Fixture test thiếu trung thực**: `_report_s1()` trong test C6 không có `tier_vnd` trong khi solver THẬT luôn có → sửa fixture cho khớp thật (không sửa code để chiều fixture).
5. Ngôn ngữ cảnh báo truy thu giữ **điều kiện** ("nếu không đạt… có thể"), không doạ/không hứa — có test.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `src/gsm_core/advisor/router.py` | sửa (FEATURE_SOLVERS + 2 intent) |
| `src/gsm_core/advisor/context_pack.py` | sửa (whitelist key S5/S6) |
| `src/gsm_core/advisor/templates.py` | sửa (`_khoan_sentence`, `_mission_sentence`, `_vn` neo giá trị) |
| `src/gsm_core/advisor/pipeline.py` | sửa (`_trusted_spans` += tên mission) |
| `tests/test_advisor_pi5.py` | tạo (15 test: router, ngữ nghĩa, e2e, guardrail) |
| `tests/test_advisor_pipeline.py` | sửa (fixture trung thực + router set mới) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| S5/S6 đến được tài xế qua F1/F2/F3 | `OBSERVED-CODE` | e2e test + output thật | Cao | — |
| Số hiển thị trace registry (faithfulness=1.0) | `OBSERVED-CODE` | test regex + compute_faithfulness | Cao | vi phạm §5 |
| Tên mission là data tin được | `ASSUMPTION` | catalog nền tảng (như tiêu đề policy) | TB | tên chứa số sai lệch lọt V1 |
| Map UC3→F1/F3, UC8→F1/F2 | `ASSUMPTION` | thiết kế sản phẩm | TB | vị trí advice chưa tối ưu UX |

## Kiểm chứng

`tests/test_advisor_pi5.py` 15 test (1 skip khi driver không có rủi ro truy thu); full suite **299 pass**. Chạy thật: 3 feature × pipeline template-mode → ComposedAdvice hợp schema, verifier pass, faithfulness=1.0, câu tiếng Việt đúng ngữ nghĩa (đã đọc kiểm). **CHƯA kiểm chứng:** đường LLM live (vẫn template-mode); UX thứ tự câu chưa qua người dùng thật; UC5/6/7 chưa làm.

## Visual verification
- **Status:** `NOT_APPLICABLE` (chưa có UI) — thay bằng **sample text advice** in ở mục "Mẫu output THẬT" cho Cường đọc.

## Expansion checkpoint (T-039)
1. **Schema:** không đổi (giữ enum F0-F3 đóng).
2. **Bài toán tối ưu:** còn UC5 idle-reduction là ứng viên optimization kế.
3. **Tính năng:** F1 giờ gộp 3 lớp (mốc ngày + khoán tuần + mini-task) → cân nhắc rút gọn/ưu tiên câu khi lên UI (tránh quá dài).

## Follow-up / defer phát sinh
- **PI-5b**: UC5 idle-reduction (hex_tracking), UC6 penalty-explain, UC7 anomaly-alert.
- Độ dài message F1 (3 lớp thông tin) — cân nhắc ưu tiên hoá khi có UI.
- Composer LLM chưa được kiểm với solver mới (chỉ template) — chạy khi bật live (D-C6-03).
