# UPDATE-121 — tầm pin trên UI khớp engine + cổng UI↔engine đầu tiên (`D-M3-17`, `D-M3-18`)

Ngày: 2026-08-01 · Trạng thái: `DONE-CODE` (chờ visual review) · Hướng: **fix lỗi**

## Bối cảnh

`D-M3-17` là việc #0 Cường đã ghim: smoke end-to-end hôm qua phát hiện UI tự tính tầm pin bằng
công thức riêng. Bốn nguồn cho **một** đại lượng:

| Nguồn | Công thức | Tầm ở SOC 100% |
| --- | --- | --- |
| engine `behavior.soc_range_km` — đội đổi pin | `soc / 1.6` | **62,5 km** |
| engine — đội sạc | `soc / 0.85` | **117,6 km** |
| `adapters/mockdata.py` (UI đang dùng) | `soc * 1.1` | **110 km** cho MỌI tài xế |
| `simulator.py` (endpoint legacy, vẫn phục vụ HTTP) | `soc * 3.2` | **320 km** |

⇒ tài xế đội đổi pin thấy tầm **thổi ~1,76×**; endpoint legacy **5,1×** (320 km với xe máy điện là
vô lý — dải tham chiếu Feliz S 100–130 km).

## Chuyện làm đổi cách sửa: KHÔNG CÓ field đội pin

Nợ ghi *"fix = UI đọc `soc_range_km` và phải biết `fleet` của tài xế"*. Khi làm thì đo được: **cả
bảng mock lẫn 13 bảng GSM đều không có thông tin đội pin.** `driver_type` chỉ nói loại xe
(`bike-electric`, `car`, `car-premium`, `bike-electric-rto`); engine phân đội pin theo *archetype*
(P1 sạc · P2/P4/P6/P7 đổi pin · P3/P5 chia 50/50 bằng RNG).

Nên đây đúng là **thiếu field**, như nợ đã dự đoán — và không được lấy đó làm cớ để bịa hệ số.

**Cách xử lý đã chọn:** dùng hệ số **THẬN TRỌNG** (tầm ngắn hơn), khai **dải** đầy đủ, và khai
**cơ sở** của con số. Lý do chọn thận trọng: hậu quả không đối xứng — báo tầm ngắn hơn thực tế chỉ
gây bất tiện, báo dài hơn có thể làm tài xế **hết pin giữa đường**.

## Và một lỗi lớn hơn lộ ra: `D-M3-18` — 40/150 tài xế là XE HƠI

Test đầu tiên đỏ vì nó lấy `drivers[0]` và trúng `ce-0` — **xe hơi**. Đếm lại catalog:

| Đội | Số tài xế |
| --- | --- |
| `bike-sim` | 90 |
| `bike-rto` | 20 |
| `car-platform` · `car-employee` · `car-premium` | 15 · 15 · 10 = **40** |

Engine và `configs/pilot_dongda.yaml` **chỉ mô hình xe máy điện** (hai loại pin). Với 40 tài xế xe
hơi, hệ số xe máy **không áp dụng được** — dùng nó là sai *loại xe*, tệ hơn cả lỗi 1,76× ban đầu.

**Không thể trả `null`:** `ui/driver_app/lib/models/driver_state.dart:56` ép
`(json['vehicle_range_km'] as num)` ⇒ null làm **app Flutter của Khánh crash**; `models.py:57` khai
`float` nên pydantic cũng reject. Nên giải pháp là **cộng thêm, không phá**: giữ nguyên field và
kiểu, thêm cờ `vehicle_range_km_applicable=False` + `basis` nói *"KHÔNG CÓ CƠ SỞ cho đội car…"*.

## Files

| File | Thay đổi |
| --- | --- |
| `ui/backend/app/adapters/mockdata.py` | `_range_band()` đọc hệ số từ `configs/pilot_dongda.yaml` (nguồn cấu hình duy nhất) · `_range_fields()` trả 5 field kèm cờ + cơ sở |
| `ui/backend/app/simulator.py` | `soc * 3.2` → `_km_per_soc_pct()` đọc từ cùng config |
| `ui/web/js/app.js` | `renderEv()` hiện **dải** thay vì một số; cờ `false` ⇒ *"— chưa có cơ sở"*; `title` mang cơ sở; **điền chú thích + nhãn xe theo đội thật** |
| `ui/web/index.html` | Bỏ câu tĩnh *"giả định ~110 km/100%"* (số cũ đã bị bỏ) và nhãn cứng *"VinFast (bike điện)"* |
| `ui/contracts/driver_state.json` | +4 field (`_low`, `_high`, `_applicable`, `_basis`); `required` +2; mô tả nói rõ vì sao giữ kiểu `number` |
| `ui/backend/tests/test_range_matches_engine.py` | **MỚI — 12 test**, là **cổng UI↔engine đầu tiên** của repo |

## Số trước / sau (đo thật)

Tài xế xe máy, SOC 70%: **77,0 km → 43,8 km** (dải 43,8–82,4 km).
Tài xế xe hơi: vẫn trả số để không phá consumer, nhưng cờ `applicable=false` và UI hiện *"— chưa
có cơ sở"*.

## Kiểm chứng

- **12 test mới: 4 đỏ trước → xanh sau.** Gồm `test_scanner_nay_THUC_SU_bat_duoc` (sever-restore:
  tự chứng minh scanner bắt được `soc * 3.2` và **miễn nhiễm** comment/docstring).
- UI suite: **77 passed** (65 + 12).
- Suite **CẢ HAI lệnh**: `uv run pytest -q` → **935 passed / 4 skipped / 0 failed** ·
  `uv run pytest -q ui/backend/tests` → **77 passed**. Tổng **1.012** (935 + 77), tăng 12 so với
  UPDATE-118 đúng bằng số test mới. **0 đỏ** — đổi 5 field trong contract không vỡ consumer nào.

## Adversarial self-review / flaws found

- **Cổng này lẽ ra phải có từ đầu.** Lỗ hổng thật không phải hệ số sai, mà là **không có test nào
  so UI với engine** — nên cả hai bên đều xanh trong khi lệch 1,76×. Suite 1.000 test không thấy
  gì. Đây là bài học kiến trúc test: *cổng phải đặt ở ĐƯỜNG NỐI giữa hai thành phần, không phải
  bên trong mỗi thành phần.*
- **Tôi tự sập bẫy grep hai lần trong một cycle.** (1) Bản đầu của scanner grep chuỗi `"soc * 3.2"`
  và bắt luôn **comment giải thích lỗi cũ** của chính tôi ⇒ cổng dạy người sau xoá lời giải thích.
  (2) Bản AST tiếp theo quét cả cây con nên bắt oan `soc * _range_band()[0]` — tức bắt đúng đoạn
  **đã sửa đúng** (hằng `0` chỉ là chỉ số mảng). Bản cuối chỉ xét **hai toán hạng trực tiếp**.
- **Số thận trọng vẫn là một lựa chọn, không phải sự thật.** Với đội sạc, ta đang báo thiếu ~47%
  tầm thật. Đúng hướng an toàn nhưng **không đúng số**. Cách sửa thật là có field đội pin — ghi
  vào `D-M3-18`.
- **App Flutter chưa đọc cờ mới** ⇒ tài xế xe hơi trên app vẫn thấy con số không có cơ sở. Backend
  và web đã đúng; phần Flutter thuộc Khánh. Đã ghi thành câu hỏi trong
  `docs/reports/week2/AUDIT-CHECKLIST-cho-Khanh.md`.
- **Chưa kiểm `map_context` và các endpoint khác** có tự tính tầm pin không. Scanner AST phủ toàn
  `ui/backend/app/**` nên nếu có thì đã bắt — nhưng scanner chỉ tìm mẫu `soc * hằng`, không bắt
  được biến thể như `pin_pct / 1.6`. Vùng mù đã khai.
- **Con số 43,8 km trông "tệ hơn" 77 km với người xem demo.** Đây là hệ quả trực tiếp của việc sửa
  đúng; nếu sau này có ai muốn nâng lại thì phải nâng bằng **field đội pin**, không phải bằng cách
  nới hệ số.

## Chụp ảnh xong mới thấy: sửa số nhưng ĐỂ LẠI lời giải thích cũ

Sau khi sửa backend + `app.js`, tôi chụp màn **Xe & Pin** để Cường xem, và ảnh phơi ra hai chỗ
tôi **chưa sửa xong** — cả hai là text tĩnh trong `index.html`:

1. Chú thích dưới ô tầm pin vẫn ghi *"giả định **~110 km/100%**"* — **đúng con số mà cycle này
   vừa bỏ**. Tức số thì đúng, còn lời giải thích bên dưới nó thì sai. Đây chính là mẫu *"sửa một
   tầng, tầng khác không biết"* mà comment trong `mockdata.py` đã cảnh báo từ Q-06.
2. Nhãn xe ghi cứng *"VinFast (bike điện)"* — hiện ra cho cả tài xế **xe hơi** `ce-0`.

Đã sửa: chú thích và nhãn xe nay **do `app.js` điền theo đội thật**, không còn câu tĩnh.

**Ba lần chụp đầu tôi tưởng đã xem được ca xe hơi nhưng không.** `?driver_id=` không được UI dùng;
`select_option` một mình không đủ (app chỉ nạp lại khi bấm **"Áp dụng"** — `#btn-apply-profile`);
và `default-view` trả `d-19` nên cả hai ảnh đầu đều là **cùng một tài xế xe máy**. Thứ phát hiện ra
là `#ev-plate` vẫn ghi `d-19`. Nếu tin lần chụp đầu thì tôi đã báo *"UI hiện đúng cho xe hơi"* mà
chưa hề thấy.

Kết quả cuối, đo trực tiếp trên DOM:

| Tài xế | Nhãn xe | Tầm đi | Chú thích |
| --- | --- | --- | --- |
| `d-19` (xe máy) | VinFast (bike điện) | **36,2–68,2 km** | *"Dải suy từ mức tiêu hao của engine — hiển thị đầu THẤP (thận trọng)"* |
| `ce-0` (xe hơi) | VinFast (ô tô · nhân viên) | **— chưa có cơ sở** | *"Đội xe này chưa có tham số tiêu hao trong hệ thống nên không hiển thị số"* |

## Visual review

**`REVIEWED-SELF` / chờ Cường.** Đã chụp `assets/ui-xe-pin-xemay.png` và
`ui-xe-pin-xehoi.png`, xem trực tiếp cả hai. Đây là đổi **số hiển thị cho tài xế** (77 → 43,8 km và một dòng
"— chưa có cơ sở" với xe hơi), nên theo `CLAUDE.md` §4b phải có verdict trước khi coi là xong.
Ghi thành `V-25`.

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**21 mục đang chờ Cường check** + **V-25 mới** (số tầm pin đổi trên UI) = **22**. Hoãn ≠ waive.
