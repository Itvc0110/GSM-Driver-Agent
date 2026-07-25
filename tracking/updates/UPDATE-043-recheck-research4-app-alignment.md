# UPDATE-043 — Recheck toàn dự án: research đợt 4 + đồng bộ advisor với TÍNH NĂNG THẬT của app

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường: "recheck toàn bộ, research thêm, check math/pipeline/architecture, viết thêm test, làm việc không cần unblock")
- **Loại:** research + fix + test
- **TODO / User story liên quan:** UC5/UC6/UC7; D-004(b); D-007; T-039

## Tóm tắt

Recheck toàn dự án. **3 subagent audit FAIL ngay lập tức** (hết hạn mức chi tiêu tháng) → **không có kết quả nào từ subagent**; tự audit bằng tool local thay thế. Kết quả: property audit 9 solver **PASS**, codify thành test mới; vòng research đợt 4 phát hiện **3 điều đảo giả định thiết kế**; fix **1 bug guardrail thật** (advice bị verifier VETO). Suite **334 → 378 pass**.

## A. Audit tự làm (thay subagent)

- **Property audit xuyên solver** trên data thật: schema hợp lệ, `number_traceability=1.0`, determinism, không NaN/Inf, confidence ∈ [0,1], digest không rỗng → **6/6 solver chạy được từ data thật đều PASS**.
- Codify thành **`tests/test_solver_properties.py` (37 test)** — bắt hồi quy khi thêm solver mới mà quên guardrail; có test khẳng định **mọi solver đã cài phải nằm trong enum schema** (enum đóng, dễ quên).
- Phát hiện nhỏ (chưa sửa): S1–S4 **không khai hằng `SOLVER`** trong khi S5–S9 có → không nhất quán kiến trúc, ghi follow-up.

## B. Research đợt 4 — 3 phát hiện ĐẢO GIẢ ĐỊNH (`research/policy/app-features-refresh-2026-07-24.md`)

| # | Phát hiện (official) | Trước đây ta tin |
|---|---|---|
| **F-1** | App **CÓ bản đồ nhiệt** + tính năng **"Nhiệm Vụ Tiếp Theo"** (15/04/2026, app v3.6.1); gợi ý khu vực nhiều khách, **không bắt buộc** | `action-space.md`: *"Xanh **không có heatmap** cho tài xế"* → **căn cứ chính của D-004** |
| **F-2** | **"Mức độ cảnh báo gian lận"** in-app từ 10/10/2025 — **4 mức: Không/Thấp/Cao/Rất cao** + khuyến cáo | S9 tự đặt thang `low/medium/high` |
| **F-3** | **"Giải trình trực tuyến"** từ 15/12/2025 — **BẮT BUỘC trong 48 GIỜ**, quá hạn ảnh hưởng tài khoản | Không hề biết/không nhắc |

**F-1 quan trọng nhất:** advice khu vực của ta **không còn là "bổ sung"** mà sẽ **chồng đè** tối ưu của hãng ⇒ **không xây heatmap riêng**; cách đúng là **trỏ về tính năng chính thức**. Đã đính chính `action-space.md` tại chỗ (giữ nội dung cũ làm lịch sử). May mắn: thiết kế S7 (chỉ khuyên MỨC THỜI GIAN, không tự chọn ô H3) **vẫn đúng** — nay có lý do mạnh hơn.

## C. Đồng bộ code với app thật

1. **S9**: dùng **đúng thang 4 mức của app** (`official_level`: Thấp/Cao/Rất cao; không cờ → "Không") để lời tư vấn **khớp cái tài xế đang nhìn thấy**; + **đếm ngược hạn giải trình 48h** (`explain_hours_left`, `explain_overdue`), thiếu `detected_at` → **không đoán**.
2. **S8**: nêu **quyền giải trình trực tuyến + hạn 48h** (chỉ nhắc quyền — **không** xây quy trình khiếu nại, D-007).
3. **S7**: caveat trỏ **"Dẫn đường → Nhiệm vụ tiếp theo"** (tính năng chính thức) thay vì ta tự gợi ý khu.
4. Schema `anomaly_alert_input` +`explain_deadline_hours` (optional, default 48).

## D. Bug thật phát hiện khi ĐỌC OUTPUT (test vẫn xanh)

**BUG-PI5d-01 (guardrail, HIGH)**: template tự format `f"{left:.0f} giờ"` → `"24 giờ"`, **không khớp** chuỗi render từ registry (`"24,0 giờ"`) ⇒ **verifier V1 coi là SỐ TRẦN và VETO cả advice** (`verify=False`). Advice vẫn tới tài xế nhưng ở trạng thái không qua kiểm.
- **Fix 2 lớp**: (a) mọi số hiển thị phải đi qua `_vn()` (neo registry) — truyền `reg` vào `_anomaly_sentence`; (b) `render_number_vn` cho giờ **nguyên** trả `"24 giờ"` thay vì `"24,0 giờ"` (đọc tự nhiên hơn, và nhất quán).
- **Regression test**: e2e pipeline phải `verify=True` khi có số giờ trong message.
- Cùng họ BUG-PI5a-01 (số không neo registry) — đây là **lớp lỗi lặp lại**, nay có test e2e chặn.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `research/policy/app-features-refresh-2026-07-24.md` | tạo (research đợt 4) |
| `research/simulation/action-space.md` | sửa (đính chính heatmap — căn cứ D-004) |
| `src/gsm_core/solvers/{anomaly_alert,penalty_explain,idle_reduction}.py` | sửa |
| `src/gsm_core/advisor/templates.py`, `src/gsm_core/vn_format.py` | sửa (fix BUG-PI5d-01) |
| `schemas/l3/anomaly_alert_input.schema.json` | sửa (additive) |
| `tests/test_solver_properties.py` | **tạo (37 test)** |
| `tests/test_penalty_anomaly.py` | sửa (+7 test: thang 4 mức, 48h, overdue, thiếu mốc, e2e verify) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| App có bản đồ nhiệt + Nhiệm vụ tiếp theo | `FACT` (official) | greensm.com 15/04/2026 | Cao | thiết kế khu vực sai hướng |
| Thang 4 mức Không/Thấp/Cao/Rất cao | `FACT` (press, nhiều nguồn) | CafeF/press 10/2025 | TB | nhãn lệch app (chưa thấy trang official text) |
| Hạn giải trình 48h | `FACT` (official + press) | greensm.com + 24hmoney 15/12/2025 | Cao | nhắc sai hạn = hại tài xế |
| Map severity nội bộ → 4 mức | `ASSUMPTION` | 3 mức ta có vs 4 mức app | TB | mức hiển thị lệch thực tế |
| Heatmap áp dụng cho Bike | `TBC-với-GSM` | bài không tách dịch vụ | TB | trỏ tính năng không tồn tại với Bike |

## Kiểm chứng
`tests/test_solver_properties.py` 37 pass; `test_penalty_anomaly.py` 28 pass; full suite **378 pass** (334 → +44). Đọc output thật: S9 hiển thị "mức cảnh báo trên app: Cao" + "còn khoảng 24 giờ để giải trình", `verify=True`. **CHƯA kiểm chứng:** tiêu chí từng mức trong 4 mức (chỉ có press); heatmap có cho Bike không; LLM live.

## Visual verification
- **Status:** `NOT_APPLICABLE` (chưa UI) — sample text đã đọc và ghi ở mục D.

## Adversarial self-review / flaws found
1. **Subagent audit FAIL** → độ phủ audit thấp hơn dự định; đã bù bằng property test tự viết, nhưng **chưa có cặp mắt độc lập** rà research/architecture. Ghi follow-up.
2. **Map 3→4 mức là ASSUMPTION** (ta chỉ có low/medium/high). Nếu GSM có tiêu chí riêng, nhãn sẽ lệch → cần xác nhận.
3. **Hạn 48h tính từ `detected_at`** — giả định mốc bắt đầu là lúc gắn cờ; thực tế có thể tính từ lúc GSM **thông báo**. Nhãn ASSUMPTION; thiếu mốc → không đoán (có test).
4. **S1–S4 thiếu hằng `SOLVER`** — nhất quán kiến trúc, chưa sửa (follow-up, rủi ro thấp).
5. Chưa rà: `shift_dp`/`capacity_alloc` chưa có view derive từ l1r nên không nằm trong property test data thật (chỉ 6/9 solver được phủ) — follow-up.

## Expansion checkpoint (T-039)
1. **Schema:** `anomaly_alert_input.explain_deadline_hours`; cân nhắc thêm `app_version` (tính năng mới cần v3.6.1) nếu GSM export.
2. **Bài toán tối ưu:** không đổi; F-1 đóng lại hướng "tự làm heatmap" (tránh lãng phí).
3. **Tính năng mới đề xuất** (chưa làm, chờ Cường): (a) nhắc hạn 48h dạng đếm ngược — **đã làm phần lõi**; (b) đối chiếu hành vi ↔ mức cảnh báo (không lộ ngưỡng); (c) nhắc cập nhật app khi thiếu tính năng tối ưu.

## Follow-up / defer phát sinh
- Chạy lại audit độc lập (subagent) khi hạn mức chi tiêu được nâng.
- Xác nhận với GSM: tiêu chí 4 mức; heatmap có cho Bike; mốc bắt đầu tính 48h.
- Thêm `SOLVER` const cho S1–S4; mở rộng property test phủ `shift_dp`/`capacity_alloc`.
