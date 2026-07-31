# UPDATE-117 — quét CƠ CHẾ MỒ CÔI: cờ config không ai đọc + module chết mang bảng màu thứ hai (`D-M3-15`)

Ngày: 2026-08-01 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi** (chỉ đạo Cường 2026-07-31)

## Vì sao quét — thay vì chờ lần thứ tư

Mẫu *"thứ được khai báo nhưng không có đường chạy"* đã sập **ba lần**: `D-R12` · UPDATE-114 lỗ
(a) (`adherence_a` sống ở comment + field) · UPDATE-116 `D-M3-13` (tầng 5 có hàm gộp, không có
nguồn). Bài học tôi tự ghi ở UPDATE-115 là: **bắt được một lỗi thuộc một họ thì viết phép thử
cho cả họ rồi quét, đừng soi bằng mắt.** Lần này áp dụng nó trước khi lỗ thứ tư tự xuất hiện.

Quét ba lớp: (1) cờ trong `configs/pilot_dongda.yaml` không xuất hiện trong `src/`; (2) hàm
public không có caller; (3) hai lớp trên giao nhau ở đâu.

## Lớp 1 — 5 cờ config mồ côi, và BA trong đó là tài liệu SAI

| Cờ | yaml khai | Giá trị **hiệu dụng** của sim | Lệch |
| --- | --- | --- | --- |
| `vehicle.swap_range_km` | 60 km | `100 / 1.6` = **62,5 km** | **+4,2%** |
| `vehicle.charge_range_km` | 110 km | `100 / 0.85` = **117,6 km** | **+6,9%** |
| `time.metrics_bucket_min` | 15′ | gộp theo **GIỜ** (`t_min // 60`, 4 chỗ) | **4×** |
| `newbie_program.combo_value_vnd` | 810.000đ | — (combo chưa implement) | cờ trơ |
| `newbie_program.combo_min_trips_per_month` | 200 | — | cờ trơ |

Phạm vi pin thật được suy từ `*_consume_pct_per_km` (`behavior.soc_range_km`), nên hai khoá
`*_range_km` là **số dẫn xuất bị chép cứng rồi lệch dần** — đúng mẫu *"hai nguồn sự thật cho
một sự thật"* của `D-M3-11`, chỉ ở tầng config.

**Cái giá cụ thể của một cờ mồ côi** (lý do tôi không coi đây là chuyện nhỏ): ai sweep nó để đo
sẽ thấy Δ = 0 và kết luận **sai** rằng *"tham số này không ảnh hưởng"* — trong khi thật ra nó
chưa từng được đọc. Một kết luận sai trông như được dữ liệu hậu thuẫn.

**Một bẫy grep tôi tự sập rồi tự bắt**: lần quét đầu báo `swap_range_km` có 3 caller. Kiểm tay
thì cả 3 là `swap_range_km_per_pack` — một khoá **hoàn toàn khác** ở `policy.py`. Cổng nay khớp
theo **token** (`(?<![A-Za-z0-9_])…(?![A-Za-z0-9_])`), không phải substring.

## Lớp 2 — 14 hàm public không caller, trong đó một module chết hẳn

7 hàm là `derive_*_l1r` (đã biết từ UPDATE-115: module PI-4a chưa nối). Còn lại đáng chú ý:

| Hàm | src caller | test |
| --- | --- | --- |
| `trajectory.build_paths` | 0 | **0** |
| `trajectory.build_customer_events` | 0 | **0** |
| `trajectory.detect_flaws` | 0 | 2 |
| `behavior.soc_range_km` | 0 | 0 |
| `sim_metrics.full_report` · `journey.journey_to_json` · `policy_locks.is_locked` | 0 | 3/3/2 |

`dashboard.py` (696 dòng) **không import gì từ `trajectory`**. Nên cả module — kể cả
`detect_flaws`, tức cơ chế *"phát hiện hành vi chưa tối ưu"* — đang không chạy ở đâu.

🔴 **Và đây là phần nguy hiểm**: `trajectory.STATE_COLORS` là **bảng màu THỨ HAI**, xung đột với
bảng dashboard đang dùng:

| Trạng thái | `trajectory.STATE_COLORS` | `dashboard_theme.ACTIVITY_COLORS` |
| --- | --- | --- |
| `enroute` | cam `(255,165,0)` | **xanh dương** `#3987e5` |
| `relocate` | vàng `(255,205,86)` | **hồng** `#d55181` |
| `on_trip` | `(40,167,69)` | `#199e70` (gần nhau) |

Nối module này vào UI mà không thống nhất màu trước sẽ tạo **hai cách đọc cùng một trạng thái**
— đúng loại lỗi `CLAUDE.md` §4b gọi là *"UI tự recompute khác engine"*.

## Fix

- **XOÁ** `vehicle.swap_range_km` / `charge_range_km` / `time.metrics_bucket_min` khỏi config, thay bằng comment ghi
  công thức + giá trị hiệu dụng (62,5 / 117,6 km; metrics gộp theo GIỜ) + dải tham chiếu. Xoá **thay vì sửa số**: giữ
  một giá trị dẫn xuất trong config là mời gọi nó lệch lần nữa.
- **CỔNG THƯỜNG TRỰC** `tests/test_config_flags_wired.py` (4 test): mọi cờ phải có người đọc;
  cờ cố ý khai trước phải nằm trong `CHUA_DUNG` **kèm lý do**; và một test riêng chặn
  `*_range_km` quay lại config. Cộng một **đối chứng hai chiều**: cờ đã nối mà vẫn nằm trong
  `CHUA_DUNG` là **nhãn sai** (dạy người đọc rằng cờ vô hiệu trong khi nó đang điều khiển
  hành vi) ⇒ cũng đỏ.
- **NHÃN** `trajectory.py`: khai tường minh module không có đường chạy, ba hàm nào 0 test, và
  bảng màu xung đột — kèm điều kiện phải làm trước khi nối lại. **Không xoá** 300 dòng: quyết
  định giữ/xoá thuộc Cường.
- **NHÃN** `behavior.soc_range_km`: nay là **nguồn công thức duy nhất** cho quan hệ SOC↔km, có
  comment config trỏ về.

## Kiểm chứng

- 4 test cổng: **2 đỏ trước** (đúng hai khoá `*_range_km`), xanh sau.
- **Behavior-neutral ĐO ĐƯỢC**, không chỉ lập luận "0 caller": dựng lại bản config có **cả ba**
  khoá rồi so fingerprint per-actor (payout, trips, rest, soc, online) trên **5 seed** —
  `5011: 040c79a862f4b6a4` · `5013: d9671c69e57568c0` · `5017: e3bf368273b8c91c` ·
  `5019: b5068bc7b258812e` · `5023: 93de60f8f29ce9d7`, **IDENTICAL cả 5**.
  (Vòng đo đầu chỉ có 2 khoá range; tôi chạy lại với cả 3 thay vì suy rằng khoá thứ ba *"cùng
  lập luận 0-caller nên chắc cũng vô hại"* — đúng loại suy luận đã làm tôi sai nhiều lần.)
- Scanner ranh giới fatigue↔tiền vẫn xanh sau khi sửa docstring: `test_health_boundary` 12/12.
- Full suite **CẢ HAI lệnh**: `uv run pytest -q` → **929 passed / 4 skipped / 0 failed**
  (19:50) · `uv run pytest -q ui/backend/tests` → **65 passed**. Tổng **994**. Khớp kiểm đếm:
  925 (sau UPDATE-116) + 4 test cổng = 929. **0 đỏ.**

## Adversarial self-review / flaws found

- **Cổng này có thể thành cổng phiền.** Nó khớp theo tên khoá, nên một cờ đọc **động** (qua
  `cfg.get(name)` với `name` là biến) sẽ bị báo mồ côi oan. Chưa gặp ca nào trong repo hiện tại,
  nhưng nếu gặp thì cách đúng là thêm vào `CHUA_DUNG` với lý do *"đọc động ở <file>"*, **không
  phải** nới regex — nới regex là tự phá cổng (mẫu `D-R20`).
- **Tôi đã dùng grep substring và nó cho 1 false positive ngay lượt đầu** (`swap_range_km` khớp
  nhờ `swap_range_km_per_pack`). Nếu tin nó, tôi sẽ kết luận cờ đó *có* người đọc và bỏ qua đúng
  con lệch 4,2%. Bài học rất cụ thể: **grep tên khoá phải neo biên token**.
- **Chưa quyết**: xoá hay giữ `trajectory.py`. Tôi chọn gắn nhãn vì xoá 300 dòng là quyết định
  sản phẩm, không phải quyết định fix bug. Nhưng nhãn **không** ngăn được người sau `import` nó
  rồi thừa hưởng bảng màu sai — chỉ ngăn được nếu họ đọc docstring. Cổng thật sẽ là một test
  *"STATE_COLORS phải khớp ACTIVITY_COLORS hoặc module phải bị xoá"*; chưa làm, ghi `D-M3-16`.
- ✅ **Đã truy `metrics_bucket_min` thay vì defer** — và nó **tệ hơn "cờ dư"**: `sim_metrics`
  gộp theo **giờ cứng** ở 4 chỗ (`int(t_min // 60)`, dòng 66/77/258/259), tức cờ 15′ **nói sai
  hành vi** với người đọc config, lệch **4×**. Đã xoá + test canh không cho khai lại khi 4 chỗ
  hardcode còn nguyên. Việc *đổi* sang bucket 15′ thật là **đổi hành vi** (mọi số theo-giờ phải
  đo lại) ⇒ cần plan riêng, giữ ở `D-M3-16`.
- Ba mã nợ mở hôm nay (`D-M3-12`, `D-M3-14` → đã đóng trong UPDATE-116, `D-M3-16`) đều thuộc
  **một họ duy nhất**: thiếu cổng thường trực cho các bảo đảm đã phát biểu. Đây là món nợ kiến
  trúc, không phải chuỗi tai nạn rời rạc.

## Visual review

`NOT_APPLICABLE` — config đổi đã chứng minh behavior-neutral bằng fingerprint 3 seed; hai file
còn lại chỉ đổi docstring/comment. Không có output nào đổi để xem.

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**20 mục đang chờ Cường check**: V-01…V-14, V-16, V-17, V-18 (kèm card im lặng), V-20, V-21, và
**V-22 mới mở trong chính UPDATE này**. Hoãn ≠ waive. Chi tiết: `tracking/PENDING-REVIEW.md`.

**V-22** (không chặn việc khác): `trajectory.py` — **xoá 300 dòng hay giữ để dùng cho lớp visual
sau?** Nếu giữ thì phải thống nhất `STATE_COLORS` với `dashboard_theme` trước khi ai đó nối lại,
nếu không UI sẽ có hai cách đọc cùng một trạng thái.
