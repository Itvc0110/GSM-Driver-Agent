# UPDATE-143 — V-28 lượt chạy riêng: expander Advisor + vạch lan can trên dashboard

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent (Cường: *"V28 chạy riêng đi bật kênh đi"*)
- **Loại:** dashboard (UI sim) + visual run
- **Liên quan:** `V-28` · UPDATE-138 (lan can kéo ca) · `D-QD4-05`

## Vì sao cần sửa dashboard

Tab Hành trình vẽ vạch advice từ `result` của **run chính**, mà sidebar **không có đường nào bật
advisor** ⇒ vạch `advice_shift_extend` không bao giờ hiện, V-28 không thể xem. (Tab Thế giới song
song có checkbox kênh nhưng chỉ ra bảng Δ, không ra timeline.)

## Đổi gì (`src/gsm_sim/dashboard.py`)

1. **Expander `🤖 Advisor (SIM-3/4 — nghiên cứu)`** ở sidebar — mặc định **TẮT** (giữ nguyên hành
   vi cũ, đúng ĐA-07); bật mới merge `advice.*` vào overrides; `shift_plan` ghi rõ *"ĐA-07 đã bác
   — CÓ HẠI"*; caption cảnh báo đây là cấu hình nghiên cứu.
2. **Vạch/vùng ĐỎ lan can sức khoẻ** trên timeline Hành trình: lọc `advice_extend_veto` +
   `advice_rest_veto` theo đúng `EXTEND_RAILS`/`REST_RAILS` (không vẽ `no_window`/`cadence`… —
   tránh rừng vạch vô nghĩa). Lan can bắn mỗi tick 2′ ⇒ tài xế mệt có hàng trăm lượt: **≤20 vẽ
   từng vạch, dày hơn tô VÙNG đỏ nhạt + mốc "lan can sức khoẻ chặn ×N"** (tái dùng đúng bài học
   vùng-ngân-sách của ĐA-04/V-18). Caption ghi rõ *"lượt đếm theo tick 2′"*.

## Bằng chứng chọn seed/actor (headless, 4 seed, config = đúng expander: chỉ `shift_extend`)

| seed | tổng NÓI | tổng lan can chặn | cặp tương phản |
| --- | --- | --- | --- |
| 1000 ⭐ | 50 | 3 369 | **d-81** online 512′ < ngưỡng 540′ ⇒ nói **5** · **d-30** online 667′ > ngưỡng 600′ ⇒ nói **0**, chặn **143** |
| 1 | 36 | 3 695 | d-74 (nói 2) vs d-38 (chặn 173, nói 0) |
| 1001 | 34 | 4 357 | d-44 (nói 2) vs d-28 (chặn 189, nói 0) |
| 1002 | 33 | 3 856 | d-88 (nói 3) vs d-29 (chặn 204, nói 0) |

Mẫu hình nhất quán cả 4 seed: **tài xế vượt ngưỡng mệt nhận 0 lời khuyên kéo ca** — vạch "thưa
hẳn" thực tế là **tắt hẳn**, đúng hơn cả yêu cầu V-28.

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| `ast.parse(dashboard.py)` | syntax OK |
| Mặc định expander TẮT ⇒ overrides không có khoá `advice` | giữ nguyên run chính (hành vi cũ) |
| Launch thật | `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` — sống ở `http://localhost:8501` |
| Suite | KHÔNG chạy lại — dashboard nằm ngoài mọi test (`tests/` không import nó); suite 1091/5F đo ở UPDATE-142 vẫn là số hiện hành |

- **Evidence:** MOCK; seeds 1/1000/1001/1002; script `scratchpad/tim_seed_v28.py`.
- **Visual:** **WAITING-VERDICT** — dashboard đã launch cho Cường, kịch bản xem ghi ở
  `PENDING-REVIEW.md` V-28 (Seed 1000 → Advisor ON → Hành trình → d-81 rồi d-30).

## Adversarial self-review / flaws found

1. **Suýt tạo rừng vạch**: bản đầu vẽ mỗi lượt lan can một vạch — d-30 có 143 lượt. Đã gộp thành
   vùng khi >20, đúng bài học vùng-ngân-sách có sẵn ngay bên dưới đoạn code đó.
2. **"Lượt" ≠ "quyết định"**: lan can bắn theo tick 2′ nên con số ×143 KHÔNG so sánh được với
   marginal 3,5% của UPDATE-138 — caption và PENDING đều ghi chú tường minh để không ai trích nhầm.
3. **Chưa kiểm:** giao diện render thực tế của vùng đỏ (annotation chồng chữ khi vùng hẹp) — Cường
   sẽ thấy ngay khi mở; nếu xấu thì chỉnh vị trí annotation, không đổi dữ liệu.

## Follow-up

| ID | Việc |
| --- | --- |
| `V-28` | **WAITING-VERDICT** — chờ Cường mở `http://localhost:8501` theo kịch bản |
| `D-QD4-05` | vẫn mở — ngưỡng mệt đang so trên `online_min` GỘP CẢ NGHỈ (proxy); đổi đại lượng ở cùng ngưỡng là tắt rail im lặng |
