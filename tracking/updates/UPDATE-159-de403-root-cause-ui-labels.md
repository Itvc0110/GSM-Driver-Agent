# UPDATE-159 — Chốt D-E4-03 (root cause hai quan sát treo) + UI bản-cuối cho stakeholder + lịch trình

- **Ngày:** 2026-08-06
- **Loại:** research (root cause) + UI (nhãn/giải thích) + docs (lịch trình, bài học)
- **Liên quan:** UPDATE-156/157 (hai quan sát treo) · chỉ thị Cường 2026-08-06 (flaw/root-cause ·
  lịch trình · tên dễ hiểu · "cái nào tốt thì mặc định bật" · UI không mã hiệu nội bộ)

## D-E4-03 — CHỐT bằng hai probe phân biệt (khuôn FIX-PRE)

### (a) "rest +281′" — KHÔNG phải cơ chế ổn định: PHỤ THUỘC CỬA SỔ SEED

Sổ thời gian `station_choice` 30 seed trên cửa sổ **7000-7029** (phép đo gốc dùng 1000-1029):

| khoản | Δ (B−A) | CI95 |
| --- | --- | --- |
| `charge_min` | **−698,0′** | [−842; −554] ✅ hiệu ứng trực tiếp của kênh |
| `idle_min` | **+520,3′** | [+319; +706] ✅ |
| `empty_min` | +98,9′ | [+46; +151] ✅ |
| **`trips_done`** | **+5,5** | **[+1,3; +9,4] ✅ sản xuất THẬT tăng** |
| `points` | +31,0 | [+7,8; +53,3] ✅ |
| `rest_min` | **+19,6** | [−45; +86] — **ns** |

Cùng kênh, cùng n=30: seeds 1000s cho rest **+281 CI chặt**, seeds 7000s cho **+19,6 ns** ⇒ thời
gian giải phóng từ trạm chảy vào đâu (idle/rest) phụ thuộc va chạm meal-hour/fatigue theo cửa sổ
seed. **Bài học mới ghi sổ:** trước khi root-cause một "hiệu ứng", đo lại trên cửa sổ seed KHÁC.

### (b) "span p90 +15,6′" — CƠ CHẾ THẬT, và giả thuyết artifact CỦA TÔI BỊ BÁC

Tôi nghi ngưỡng kế toán `break_min=20′` tạo hiệu ứng giả (hàng đợi trạm dài từng được đếm là
break). Probe sensitivity break 10′/20′/30′ (30 seed, cửa sổ 1000):
Δ = **+20,1′ / +15,6′ / +23,9′** — ổn định mọi ngưỡng ⇒ artifact **BÁC**; kênh thật sự làm chuỗi
làm việc liền mạch dài hơn (bỏ các quãng dừng cưỡng bức ở trạm).

**Đối chiếu chuẩn tầng 5:** +15,6′/444′ = **+3,5% < `SPAN_P90_RISE_TOL` 10%** ⇒ cổng một chiều
**KHÔNG bắn** — trade-off nằm trong dung sai sức khoẻ đã chốt từ D-M3-05, không cần verdict mới.

### Kết luận D-E4-03 → **ĐÓNG**

Cơ chế kênh: trạm bớt chờ (−698′ downtime) → thời gian quay lại vòng làm việc → **trips +5,5,
points +31 (CI sạch)**; chi phí thật = chuỗi liên tục dài thêm ~3,5% p90 (trong dung sai).
Không còn quan sát treo. Điều kiện bật kênh chuyển sang phép đo 100 seed (đang chạy — theo tiền
lệ positioning/ĐA-08); Cường đã uỷ quyền *"cái nào tốt thì mặc định bật"*.

## UI bản-cuối cho stakeholder (chỉ thị trong ngày)

- **`src/gsm_sim/channel_labels.py` (MỚI)** — MỘT nguồn nhãn VN + giải thích một câu cho mọi bề
  mặt; **ID nội bộ không đổi** (registry/contract/event log — bài học QĐ-4).
- Dashboard: sidebar "🤖 Trợ lý tài xế" + tab A/B dùng nhãn thân thiện (VD *"Chọn trạm đổi pin ít
  phải chờ"* thay `station_choice`); **quét sạch mã hiệu nội bộ khỏi chuỗi hiển thị** (ĐA-07,
  D-M3-*, V-28, arm B → chuyển thành comment); bảng Δ theo hồ sơ có chú giải P1..P7 bằng lời.
- Web demo: kiểm tra — mã hiệu chỉ nằm trong comment JS, chuỗi hiển thị sạch sẵn.

## Lịch trình

`tracking/PLAN-2026-08-06-lich-trinh-cai-thien.md` — 4 sóng (1: chốt D-E4-03 + bật kênh + keyed
RNG D-SIM-K3 + oracle-all · 2: độ tin sim T-045c/D-M3-19/D-A3-01b · 3: advisor E-07/B6-PARITY/UX
card · 4: vệ sinh) + mục **"Bài học đã docs"** tích luỹ 7 mục + mục **"KHÔNG LÀM và vì sao"**.

## Kiểm chứng
2 probe scratchpad (`probe_e01_ledger.py`, `span_sensitivity.py`) · dashboard syntax OK + restart
· suite không đổi (labels là chuỗi hiển thị; conftest/e-tests nguyên).

## Visual
Gộp V-31 (đã có nhãn mới — hướng dẫn V-31 vẫn đúng đường bấm).

## Follow-up
- Đọc `e01-station-100.json` khi xong → nếu giữ tín hiệu + tầng 5 pass ⇒ bật `station_choice: true`
  mặc định (UPDATE-160, ghi rõ cơ sở + uỷ quyền + có thể thu hồi).
- D-SIM-K3 keyed RNG = việc lớn kế tiếp theo lịch trình.
