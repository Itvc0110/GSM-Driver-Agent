# UPDATE-163 — `shift_extend` mù cửa sổ điểm (bug CAO, 3 nguồn) + cơ hội mở rộng số 1: "positioning chặng về"

- **Ngày:** 2026-08-06
- **Loại:** research (audit math-model, phần tôi tự kiểm) — **0 dòng code thực thi thay đổi**
- **Liên quan:** UPDATE-162 (ba nợ đầu) · `HANDOFF-2026-08-06-quota-blocked-audit.md` · chỉ thị Cường
  *"kiểm công thức đã chuẩn chưa… mở rộng các kênh — phải dựa trên action có thể thực hiện được và solver"*

## 1. 🔴 `D-ADV-02` — `shift_extend` mù `point_window_hours` (sev CAO)

**Ba nguồn độc lập trùng nhau:** agent `mm-11` (MI-2) + agent `mm-12` + **tôi tự mở code kiểm**.

| Chỗ | Sự thật đã kiểm |
| --- | --- |
| `advice_bridge.py:1122-1126` | `rate = actor.points / online_h` (**trung bình cả ngày**, trộn giờ peak 10đ) → `need_min = gap_points / rate × 60`. **Không một tham chiếu nào** tới cửa sổ điểm hay hình dạng cầu theo giờ |
| `policy.py:86-92` | `trip_points` trả **0** nếu `order_hour ∉ point_window_hours` |
| `configs:254` | `point_window_hours = [6..21]` |

⇒ **Ca kết 21–24h (P5/P7, P1 ca tối): mọi phút kéo thêm cho `E[Δthưởng] = 0`**, trong khi tài xế trả
work-span thật + pin + km. Đúng lớp lỗi `station_choice`: objective thiếu **vế giá trị theo thời
gian mà world định giá tường minh**. Ngay cả kéo *trong* khung, `rate` trộn peak ⇒ `need_min` ước
**non ~2×** ⇒ kéo không đủ, vẫn trượt mốc (họ "vách đá" D-SIM-05); hai cổng `reachable_in_shift` /
`cap_unreachable` phán sai theo.

✅ **Không nhiễm số nào đã báo**: kênh TẮT mặc định. ⚠ **Không trùng ADV-02/03** (hai cái đó sửa "so
với ca còn lại" và "dự phóng mệt", không chạm cửa sổ điểm).

**Sửa — solver ĐÃ CÓ SẴN:** thay `rate` phẳng bằng **`S1 bonus_feasibility._walk`** đi từng giờ trên
`[shift_end, shift_end + extend]` — solver này **đã** xử đúng "0 điểm ngoài khung" từ UPDATE-065
(fix S1-2/3/5); kênh chỉ **chưa gọi**, trái chính nguyên tắc `D-SIM-09` mà bridge tự tuyên bố. Không
nghiệm ⇒ **im lặng** với reason mới `points_window_closed` (R-08). **Bắt buộc sửa trước** mọi lần bật
đo lại kênh.

## 2. ⭐ `D-ADV-03` — cơ hội mở rộng XẾP HẠNG 1: "positioning chặng về"

`world.py:799-811`: sau cuốc trả ngoài lõi, `_relocate_to_core` chọn `target` = **ô lõi đầu tiên gặp
khi nới vòng** — thuần khoảng cách, **mù cầu**. Đó là relocate THẬT (tốn phút + SOC, `empty_min += t`,
`enroute_cell = target` nên đã tự vào sổ `supply_incoming`). Planner vị trí **không thấy** điểm quyết
định này vì actor đang `ENROUTE` (`world.py:421` chỉ quét IDLE). Kích hoạt: **65,3% cuốc trả ngoài
lõi**, deadhead ~**539 km/ngày** (config `:83-90`).

**Vì sao đây là đề xuất tốt nhất — và khác hẳn `station_choice` vừa NO-GO:**

| | `station_choice` (NO-GO) | `positioning chặng về` (đề xuất) |
| --- | --- | --- |
| Bản chất | **Tạo/đổi chuyến đi** để tiết kiệm phút | **Đổi HƯỚNG** km rỗng *bắt buộc phải chạy* |
| Chi phí biên | Có (đi xa hơn để tiết kiệm chờ) | **≈ 0** (đằng nào cũng chạy về lõi) |
| Vế vị trí | **Thiếu** — chính lý do NO-GO | **Là toàn bộ nội dung** của kênh |
| Họ kênh | pin (chưa từng dương) | **VỊ TRÍ — họ duy nhất dương SIG** (+6.016đ, PASS 9/9) |

Hiện tại tài xế về **nhầm ô rồi mới bị kéo đi tiếp = HAI chặng rỗng thay vì một**.
Neo sẵn: action `RELOCATE(target)` có; solver `S4` + `MarketStateView.capacity_left` **đang chạy**;
ràng buộc thuần math: chỉ chọn ô lõi `capacity_left > 0` với `dist ≤ dist(gần-nhất) + δ`. Kỷ luật CRN:
bản năng vẫn tính target cũ, advice **ghi đè**. Đo như **kênh mới** theo ĐA-08 đủ 9 dòng + **veto km rỗng**.

## Files bị ảnh hưởng

`tracking/DEFERRED.md` (thêm `D-ADV-02`, `D-ADV-03`) · `tracking/updates/UPDATE-163-*.md` ·
`PROJECT-GRAPH.md` · `PENDING-REVIEW.md`. **Không sửa code.**

## Kiểm chứng

- Tôi tự mở và đọc: `advice_bridge.py:1117-1150`, `policy.py:84-93`, `configs:252-255`,
  `world.py:799-829`, `world.py:421`. Mọi khẳng định ở trên đến từ những dòng đó.
- **Chưa kiểm chứng:** độ lớn (chưa chạy sim nào) · `D-ADV-03` chưa có prereg, chưa có số kỳ vọng ·
  vẫn **CHƯA qua phản biện độc lập** (agent phản biện chết vì quota) — trừ `D-ADV-02` có lợi thế
  **hai agent độc lập trùng nhau + tôi kiểm code**, nên độ tin cao hơn ba nợ của UPDATE-162.
- Suite: **không chạy** — không sửa code.

## Visual

`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. `D-ADV-03` là **đề xuất của tôi**, và tôi vừa mới NO-GO một kênh cùng "nghe rất hợp lý" (bài học
   UPDATE-160). Vì vậy: ghi rõ **bảng so sánh cấu trúc** vì sao nó khác, và **không** hứa số nào.
   Rủi ro thật cần prereg đo: km rỗng có thể **tăng** (δ nới) và `veto 8(b)` là cổng sẽ bắt.
2. `D-ADV-02` "đúng" về cơ chế nhưng tôi **chưa đo tần suất**: bao nhiêu % lượt `shift_extend` xảy ra
   sau 21h? Nếu ~0 thì bug vô hại thực tế. Không được nói "kênh vô dụng" trước khi đếm.
3. Cả hai đến từ artifact agent — tôi kiểm được **evidence**, nhưng không kiểm được **cái agent bỏ
   sót**. 7 artifact còn lại chưa đọc; `mm-04`/`mm-07` chưa tồn tại.

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/` — đang sống) · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
