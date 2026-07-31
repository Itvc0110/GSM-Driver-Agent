# UPDATE-118 — hai CỔNG THƯỜNG TRỰC: rò rỉ tương lai + một bảng màu duy nhất (`D-M3-12`, `D-M3-16a`)

Ngày: 2026-08-01 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi** (chỉ đạo Cường 2026-07-31)

## Vì sao — món nợ hôm nay đều là MỘT món

Ba UPDATE trước (115/116/117) đóng 14 bug thuộc **hai họ**: *"đọc thứ chưa xảy ra"* và *"cơ chế
được khai báo nhưng không có đường chạy"*. Cả hai lần, thứ tìm ra bug là một **script dùng một
lần** — và script làm xong việc thì biến mất, nên người thêm deriver/cờ sau lặp lại y nguyên
được. Nợ thật không phải 14 bug, mà là **thiếu cổng cho những bảo đảm đã phát biểu**.

Hai cổng dưới đây đóng đúng chỗ đó. Cùng với `test_config_flags_wired.py` (UPDATE-117), nay có
**ba cổng thường trực** cho ba bảo đảm mà `CLAUDE.md` §4b đòi nhưng trước đây không ai thi hành.

## Cổng 1 — không L3 view nào được đọc record CHƯA TỒN TẠI (`D-M3-12`)

`tests/test_future_leak_gate.py` (3 test). Gọi **7 deriver** hai lần: trên bảng đầy đủ, và trên
bảng đã xoá mọi record mà **timestamp sớm nhất** của nó còn sau `t_now`. Khác nhau ⇒ đọc tương lai.

**Chọn "timestamp sớm nhất" là bài học trả giá bằng một false positive** ở UPDATE-115: script cũ
cắt theo `complete_time` (khoá đầu danh sách), nên cuốc *đặt* 07:50 *xong* 08:10 bị nó loại — trong
khi `demand_by_hour` **đúng** khi giữ cuốc đó (tại 08:00 ta đã biết có yêu cầu lúc 07:50). Cắt
theo min-timestamp không phụ thuộc deriver dùng khoá nào ⇒ không sinh báo động giả loại đó.

Hai test đi kèm, quan trọng hơn test chính:

- **sever-restore**: tái tạo đúng bug gốc `D-M3-11` (một deriver chỉ lọc theo NGÀY) rồi **đòi
  phép thử phải phát hiện**. Không có test này thì một verdict xanh không phân biệt được
  *"không có rò rỉ"* với *"phép cắt không đo gì"*.
- **đối chứng ngược**: đòi phần giữ lại sau khi cắt phải `> 0` và `< toàn bộ`. Nếu `_truncated`
  xoá gần hết bảng thì test chính xanh **một cách rỗng** (view rỗng == view rỗng).

**Kết quả**: 7/7 deriver sạch. Đây là **bằng chứng độc lập** rằng 6 fix của UPDATE-115 đã đóng
hết họ lỗi này ở tầng "record chưa tồn tại" — không phải chỉ ở 6 chỗ tôi đã sửa.

**Giới hạn đã khai** (đừng đọc cổng như bảo đảm toàn phần): record **đã tồn tại** nhưng có
**field** trỏ tương lai (vd `complete_time` của cuốc đang chạy) vẫn qua được. Chống ca đó cần
luật per-field. `test_future_leak_l1r.py` canh các ca cụ thể; cổng này canh **họ**.

## Cổng 2 — chỉ MỘT bảng màu cho trạng thái hoạt động (`D-M3-16a`)

`tests/test_state_colors_single_source.py` (3 test). Cổng **có điều kiện**, nên nó không cần
Cường quyết trước:

- `trajectory` chưa ai `import` ⇒ chấp nhận lệch màu, nhưng đòi **nhãn cảnh báo còn nguyên**
  trong docstring;
- có ai `import` ⇒ hai bảng **phải khớp** cho mọi trạng thái chung.

Cộng một test canh `dashboard.py` vẫn lấy màu từ **một** nguồn (`ACTIVITY_COLORS`, không phải
`STATE_COLORS`, không tự dựng bảng thứ ba).

Một chi tiết tôi cố ý đặt: nếu hai bảng **về sau khớp nhau**, test sẽ **ĐỎ** kèm yêu cầu xoá
cổng và nhãn. Vì một cảnh báo không còn đúng thì tệ hơn không có cảnh báo — nó dạy người đọc
nghi ngờ sai chỗ.

Cổng **không** tự chọn hướng giải quyết: xoá 300 dòng hay hợp nhất màu vẫn là **`V-22`**, quyết
định của Cường. Nó chỉ đảm bảo không ai nối lại module trong lúc màu còn lệch.

## Files

- **TẠO** `tests/test_future_leak_gate.py` (3) · `tests/test_state_colors_single_source.py` (3)
- **SỬA** `tracking/DEFERRED.md` — `D-M3-12` và `D-M3-16a` đóng; `D-M3-16b/c` còn mở

## Kiểm chứng

- 6 test mới, chạy cùng `test_config_flags_wired`: **10/10 xanh**.
- Cổng 1 **tự chứng minh bắn được** qua test sever-restore (không phải chỉ xanh).
- Full suite **CẢ HAI lệnh**: `uv run pytest -q` → **935 passed / 4 skipped / 0 failed**
  (20:07) · `uv run pytest -q ui/backend/tests` → **65 passed**. Tổng **1.000** chẵn. Khớp kiểm
  đếm: 929 (sau UPDATE-117) + 6 test cổng = 935. **0 đỏ.**

## Adversarial self-review / flaws found

- **Cổng 1 tốn ~20s** vì nó gọi `generate_realdata(days=6)`. Đó là giá phải trả để đo trên dữ
  liệu thật thay vì fixture mỏng — và fixture mỏng là thứ đã làm tôi đỏ SAI lý do ba lượt ở
  UPDATE-116. Chấp nhận, ghi ra để người sau không "tối ưu" nó thành fake rồi mất khả năng đo.
- **Cổng 1 không phủ `derive_session_summary_input_l1r`** vì hàm đó không nhận `t_now` (nó là
  view SAU CA, theo thiết kế). Đúng, nhưng nghĩa là *"7/7 deriver sạch"* phải đọc là **7 deriver
  có `t_now`**, không phải toàn bộ module.
- **Cổng 2 kiểm nhãn bằng chuỗi con trong docstring.** Đổi cách diễn đạt nhãn (mà vẫn cảnh báo
  đúng) sẽ làm test đỏ oan. Tôi chọn vậy có ý thức: nhãn này là thứ **duy nhất** chặn người nối
  lại module, nên tôi muốn mọi lần sửa nó đều phải đi qua một test đỏ. Nếu ai thấy phiền, cách
  đúng là **xoá module hoặc hợp nhất màu** (tức đóng `V-22`), không phải nới cổng.
- **Ba cổng đều dựa trên grep/so-sánh tĩnh**, nên chúng không bắt được đường chạy động
  (`getattr`, dict-dispatch). Đây là vùng mù chung của cả ba, khai một lần ở đây thay vì lặp
  trong từng file.
- **Chưa làm**: `D-M3-16c` (bucket metrics 15′ thật) — là **đổi hành vi**, cần plan + đo lại mọi
  số theo-giờ. Không gộp vào cycle cổng.

## Visual review

`NOT_APPLICABLE` — chỉ thêm test, 0 dòng production đổi.

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**20 mục đang chờ Cường check**: V-01…V-14, V-16, V-17, V-18 (kèm card im lặng), V-20, V-21,
V-22 (xoá 300 dòng `trajectory.py` hay giữ — cổng 2 ở trên đã chặn rủi ro trong lúc chờ, nên
việc này **không còn gấp**). Hoãn ≠ waive. Chi tiết: `tracking/PENDING-REVIEW.md`.
