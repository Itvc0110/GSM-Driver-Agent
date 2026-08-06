# UPDATE-157 — E4/E-01 kênh gợi TRẠM đổi pin: tín hiệu cơ chế THẬT đầu tiên của E4

- **Ngày:** 2026-08-06
- **Loại:** feature (kênh mới, mặc định TẮT) + research (đo quan sát 30 seed)
- **Liên quan:** UPDATE-151 r05 E-01 (Cường duyệt SIM-ONLY) · UPDATE-156 (meta-finding họ VỊ TRÍ)

## Đã làm

Kênh `station_choice` (mặc định TẮT): khi tài xế đi đổi pin, advisor quét TẤT CẢ trạm bằng
`station_eta_min` = **đường đi + queue×swap + chờ-pin-chín** (mọi số đọc từ trạng thái SỐNG —
`queue_len`/`batteries.ready_at`, không dự báo) và chỉ NÓI khi tiết kiệm ≥ 3′ (R-08). Bản năng
hiện tại mù pin-sẵn và đường đi thật (chỉ "gần nhất + né queue>3 một lần").

- Topic `station_choice` → registry **MEASURED** (họ vị trí — kinh tế thuần thời gian).
- `advice_bridge.pick_station` (deterministic argmin, 0 draw RNG; coin hash quyết định nghe;
  drain mẫu số D-M3-01) · world nối SAU bản năng tại `_do_charge` (kỷ luật CRN — bản năng vẫn
  rút RNG y World A, advisor chỉ ghi đè; kênh tắt = 0 draw thêm).
- Config: `channels.station_choice: false` + `station_choice_min_gain_min: 3` (có reader).
- 9 test (`tests/test_e4_e01_station_choice.py`) — **46 passed** cùng cổng flag-wired/registry.

## Đo 30 seed (coverage=all, cô lập 1 cơ chế) — `research/audit/2026-08-06-e2/e01-station-30.json`

| metric | Δ (B−A) | đọc |
| --- | --- | --- |
| `swap_wait_mean` | **−3,77′ [−4,45; −3,11]** | ✅ CI không chứa 0 — chờ trạm giảm **~66%** (nền 5,69′) |
| `charge_min_p90_F_swap` | **−38,9′ [−44,9; −33,1]** | ✅ đuôi downtime pin của đội swap co mạnh |
| `payout_mean_all` | +1.152 [−502; +2.804] | ns — hướng dương, chưa đủ n |
| `trips` · `served` · `gini` | ns | không đánh đổi hệ thống |
| `rest_min_total` (một chiều) | +281 [+209; +352] | 🔴 CÙNG MẪU với E-03 (+279) — chưa giải thích, xem dưới |
| `work_span_p90` (một chiều) | **+15,6 [+2,5; +28,6]** | 🔴 span ĐUÔI TĂNG — phải root-cause trước khi nói kênh "sạch" |

### 🔴 Hai quan sát một-chiều — kỷ luật D-E4-03 mở rộng

CẢ HAI kênh chạm đường pin (E-03, E-01) đều cho `rest_min_total` **+~280′** — trùng lặp đáng ngờ
(cơ chế chung quanh `_do_charge`/decision-point, hoặc cùng một kiểu trôi D-SIM-K3). E-01 thêm
`work_span_p90` +15,6′ CI không chứa 0 — với ranh giới §1.2b thì đây là thứ cổng một chiều sinh
ra để TỐ GIÁC. **Không kể chuyện**: `D-E4-03` nay phủ cả hai kênh — reproduce → đọc nhánh →
phép kiểm phân biệt (khuôn FIX-PRE) là điều kiện TIÊN QUYẾT trước khi cân nhắc bật kênh nào.

## Verdict kênh (n=30 — thăm dò)

Cơ chế hoạt động ĐÚNG mục tiêu thiết kế (wait/queue giảm mạnh, CI sạch) — kênh VỊ TRÍ đầu tiên
của E4 có tín hiệu thật, khớp meta-finding UPDATE-156. Nhưng **giữ TẮT**: (1) payout ns ở n=30;
(2) quan sát span p90 tăng chưa giải thích được — sức khoẻ đứng trên (§1.2b). Muốn tiến thêm:
`D-E4-03` trước, rồi 100 seed + prereg nếu định claim.

## Kiểm chứng
46 passed · OFF bit-identical (test tích hợp fingerprint) · phép đo 3,0′/30 seed · suite đầy đủ
đang chạy (điền ở UPDATE-158).

## Visual
Gom V-31 (replay kênh ON: vạch advice_station_choice + instinct_station trong event detail).

## Follow-up
`D-E4-03` (mở rộng: cả E-03 lẫn E-01, hai quan sát) · E-07 zone-rotation DEFER (`D-E4-04`: planner
feed slots theo bucket — cycle riêng) · E-02 meal-timing DEFER (`D-E4-05`: cùng cơ chế demand-timing
với rest_window đã đo ns — chỉ làm nếu Cường muốn) · E5 wave-1 + suite chốt → UPDATE-158.
