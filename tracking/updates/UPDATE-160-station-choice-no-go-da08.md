# UPDATE-160 — `station_choice` NO-GO bật mặc định: FAIL ĐA-08 ở n=100 (P1 bị hại SIG)

- **Ngày:** 2026-08-06
- **Loại:** measurement (confirmatory n=100) + quyết định theo văn bản + docs (la bàn quyết định)
- **Liên quan:** UPDATE-157 (kênh E-01, thăm dò n=30) · UPDATE-159 (D-E4-03 đóng) ·
  UPDATE-087/089 (chuẩn ĐA-08 + tiền lệ positioning) · chỉ thị Cường 2026-08-06:
  *"đọc tài liệu quan trọng trước khi ra quyết định, dựa vào research chứ không dựa trên ký ức"*

## 1. Quyết định: KHÔNG bật mặc định — `channels.station_choice` giữ `false`

Cường đã uỷ quyền *"cái nào tốt thì mặc định bật"* — nhưng "tốt" được định nghĩa bằng văn bản
đã chốt: **spec `advisor-objective-model-v2.md` §5 (ĐA-08) + AMENDMENT 2026-07-28 (UPDATE-089 §2)**.
Chấm bằng máy (`scripts/cham_da08_station_choice.py`) trên artifact
`research/audit/2026-08-06-e2/e01-station-100.json` (100 paired seed CRN, coverage all):

| Tiêu chí | Kết quả | Verdict |
| --- | --- | --- |
| **1a** `payout_mean_all` > 0, CI95 loại 0 | **−32,6đ** CI [−1.043; +975] ns | ❌ FAIL |
| **1b** no-harm P1..P7 (không âm-SIG) | **P1 −3.863đ** CI [−6.278; −1.564] hoàn toàn < 0 | ❌ **FAIL** |
| 2 served không giảm | +0,14đp ns | ✅ |
| 3 khách (expired/wait) | −1,9 ns / −0,0004 ns | ✅ |
| 4 Gini không tăng | +0,0025 CI chạm 0 (ns) | ✅ |
| 5 tầng 5 (rest/span một chiều) | rest **+235′ SIG (tăng)** · span +16,5′ = 3,8% < 10% | ✅ |
| ref mục tiêu kênh | swap_wait **−3,6′ SIG** — cơ chế vẫn hoạt động | (tham chiếu) |

**Kênh làm đúng việc thời gian (chờ trạm giảm SIG, nghỉ tăng SIG) nhưng KHÔNG chuyển thành tiền,
và làm nhóm P1 mất tiền có ý nghĩa thống kê.** Theo văn bản, vế 1b tồn tại đúng để chặn trường
hợp này. NO-GO.

## 2. Vì sao đây là bài học đắt (ghi để không tái phạm)

- **Ký ức của tôi đã HẠ CHUẨN**: trước khi đọc lại UPDATE-089/spec §5, tôi định duyệt bằng bar
  "cơ chế thật + không hại tầng 5" — tức là đã quên vế (1a) *tiền CI-loại-0* và (1b) *no-harm
  per-archetype*. Nếu quyết theo ký ức thì đã bật một kênh đang làm hại P1 −3,9k/ngày.
- **Bài học 2 (n nhỏ lừa) tái xác nhận lần thứ 4**: n=30 cửa sổ 7000s cho trips +5,5 và points
  +31 "CI sạch" — không sống sót ở n=100 trên lớp tiền; và P1-harm **vô hình** ở n=30.
- Caveat trung thực: 7 phép kiểm per-archetype không hiệu chỉnh đa kiểm định — một âm-SIG/7 có
  thể là noise (xác suất giả ~30% nếu tất cả null). Nhưng (a) chuẩn văn bản không có điều khoản
  FDR, (b) tiền lệ positioning PASS 0/7, (c) 1a cũng FAIL độc lập. Nới chuẩn là quyết định của
  Cường, không của agent. Nếu Cường muốn xem xét lại: cần điều khoản FDR chính thức trong spec
  trước, không phải xé lẻ từng case.

## 3. Reopen condition (DEFERRED `D-E4-06`)

Mở lại xem xét bật khi **một trong**: (a) sau D-SIM-K3 keyed RNG đo lại 100 seed mà 1a/1b đổi
verdict (Δ hiện tại còn lẫn random-stream divergence — nghi phạm chính của P1-harm); (b) root
cause P1-harm chứng minh được là artifact đo (không phải cơ chế); (c) spec ĐA-08 có amendment
mới được Cường duyệt. Kênh vẫn dùng được ở chế độ nghiên cứu (checkbox dashboard).

## 4. La bàn quyết định (trả lời câu hỏi Cường — docs hoá)

Thêm §6 "La bàn quyết định" vào `tracking/BOOTSTRAP-SESSION.md`: quyết định loại nào → đọc file
nào (nghiên cứu thêm hay làm ngay · duyệt cải tiến · no-go/recheck sai lầm cũ). Case study chính
là update này.

## Files bị ảnh hưởng

- `scripts/cham_da08_station_choice.py` (MỚI) — chấm ĐA-08 bằng máy trên artifact, tái chạy được
- `research/audit/2026-08-06-e2/e01-station-100.json` (MỚI) — artifact n=100 (MOCK, seeds 1000–1099)
- `configs/pilot_dongda.yaml` — chỉ comment (giá trị `false` không đổi)
- `tracking/DEFERRED.md` — thêm D-E4-06 · `tracking/PLAN-2026-08-06-lich-trinh-cai-thien.md` —
  1.1 chốt NO-GO, bài học 8 · `tracking/BOOTSTRAP-SESSION.md` — §6 la bàn ·
  `tracking/PROJECT-GRAPH.md` · `tracking/TODO.md` · `tracking/PENDING-REVIEW.md`

## Kiểm chứng

- Đo: `scripts/run_e01_station.py --seeds 100` (background 9,6′, exit 0); chấm: script trên,
  output nguyên văn trong transcript. Số đều MOCK.
- Suite: không đụng code sim/UI (config giá trị không đổi, chỉ comment + docs) — không chạy lại.
- **Chưa kiểm chứng:** root cause P1-harm (chưa root-cause — để D-E4-06, đúng thứ tự "đo lại
  trên nền keyed RNG trước khi root-cause hiệu ứng có thể là divergence").

## Visual

`NOT_APPLICABLE` — không đổi hành vi/UI (kênh vốn đang tắt, vẫn tắt). V-31 vẫn treo như cũ.

## Adversarial self-review / flaws found

1. Script chấm đọc `significant` do bootstrap CI 95% quyết — đúng chuẩn văn bản "CI loại 0";
   không có p-value đa kiểm định (caveat §2 đã ghi, không giấu).
2. `rest +235′ SIG` ở n=100 ngược với "ns @7000s n=30" (UPDATE-159) — KHÔNG mâu thuẫn: n=100
   dùng cửa sổ 1000–1099; xác nhận thêm "quan sát phụ-thuộc-cửa-sổ-seed", một chiều nên không
   chặn.
3. Kịch bản đảo chiều kết luận: keyed RNG (D-SIM-K3) có thể xoá P1-harm (divergence) — đã thành
   reopen condition (a), không phải lý do trì hoãn quyết định hôm nay.

## ⏳ Nhắc PENDING-REVIEW

**V-31** (3 màn hình: dashboard :8501 · web :8000/app/ · bảng Δ per-archetype) · K-01(b) ACK ·
D-QD4-05 · 25 V-items · Q-03/04/07/09/10/13.
