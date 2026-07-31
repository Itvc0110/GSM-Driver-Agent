# UPDATE-115 — RÒ RỈ THÔNG TIN TƯƠNG LAI: 6 chỗ ở 3 L3 view (D-M3-11)

Ngày: 2026-08-01 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi** (chỉ đạo Cường 2026-07-31)

## Nó bắt đầu từ một test đỏ mà tôi tưởng là chuyện của mock

Full suite sau UPDATE-114 có **1 đỏ**: `test_bug01_idle_never_exceeds_online_time` —
`d-62` `2026-07-03` cho idle **247,48′** trong khi online **246,00′**. Vượt 1,48′.

Hai giả thuyết rẻ tiền tôi đã **loại bằng đo**, không phải bằng suy luận:

| Giả thuyết | Bác bỏ |
| --- | --- |
| Làm tròn `online_time` | `realdata.py:177` là `round(online_h, 2)` ⇒ lệch tối đa **0,3″**, không thể ra 1,48′ |
| Chỉ là lệch hai bảng, nới tolerance là xong | Dump segment thấy **2 segment bắt đầu 23:03 và 23:27** — trong khi view được hỏi lúc **23:00** |

⇒ Không phải lệch đo. Là **rò rỉ thông tin tương lai**.

**Vì sao fix `D-E10-01` hôm qua làm nó lộ ra**: `generate_realdata(continuous=True)` (mặc định)
chạy qua `run_multiday`, nên thêm `idle_streak_min` vào `_DAILY_RESET_FLOAT` đổi realization của
mock ⇒ một bất khớp **có sẵn** rơi đúng vào driver-day vượt ngưỡng. Fix đó ĐÚNG và được giữ
nguyên; công của nó là làm lỗi này lộ ra.

## Root cause — chứng minh được, không phải phỏng đoán

`derive_idle_reduction_input_l1r` lọc record **chỉ theo NGÀY** (`seen[:10] != d`) và **không bao
giờ so với `t_now`**. Phân rã 1,48′ đo được:

| Thành phần | Số |
| --- | --- |
| 2 segment BẮT ĐẦU sau `t_now` (chưa xảy ra) | **37,15′** |
| Phần sau `t_now` của segment ĐANG diễn ra (bị tính trọn) | **2,82′** |
| `total_idle_min` sau khi bỏ cả hai | 247,48 → **207,51′** ≤ 246′ ✅ |

`from_l1r.py:104` (`t["complete_time"] <= t_now`, thêm bởi AUDIT A3 LAYEROUT-4/UPDATE-070)
chứng minh repo **BIẾT** luật này — deriver idle **bỏ sót** nó, không phải chọn khác.

## Rồi probe tổng quát tìm thêm 5 chỗ nữa

Vì đã thấy một chỗ, tôi không đoán các chỗ còn lại mà dựng **phép thử tổng quát**: gọi mỗi
deriver hai lần — trên bảng đầy đủ và trên bảng **đã xoá mọi record có timestamp > `t_now`**.
Khác nhau ⇒ view đã đọc thứ chưa xảy ra. Kết quả (seed 900, `t_now = 2026-07-03T08:00`):

| View | Field | Đầy đủ | Đã cắt tương lai |
| --- | --- | --- | --- |
| `idle_reduction` | `idle_segments` | 247,48′ | 207,51′ |
| `idle_reduction` | `demand_by_hour` | đỉnh giờ 7 = **0,859** | **1,0** (hình dạng cầu khác hẳn) |
| `idle_reduction` | `active_reposition` | `reached: True` | `None` |
| `bonus_gap` | `historical_points_per_hour` | `{peak 3.846, offpeak 5.769}` | **`{}`** |
| `shift_plan` | `points_now` | **35** | **0** |
| `shift_plan` | `demand_forecast` | nuôi bằng cả cuốc chiều | chỉ dữ liệu đã có |
| `weekly_khoan`·`penalty_explain`·`anomaly_alert`·`mission_select` | — | **KHÔNG đổi ⇒ sạch** (đã kiểm, không phải giả định) |

Hai chỗ đáng chú ý nhất, vì chúng không phải "lệch một chút":

- **`historical_points_per_hour`**: code viết `- {today}` — bỏ đúng *hôm nay* nhưng **không bỏ
  ngày SAU hôm nay**. Với bảng 6 ngày hỏi ở ngày 3, "lịch sử" gồm ngày 4/5/6. Và chính ba ngày
  tương lai đó làm đủ ngưỡng `len(v) >= 3` — nên bỏ chúng đi thì prior **rỗng hoàn toàn**. Đây
  là đầu vào S1 BonusFeasibility dùng để nói *"còn kịp đạt mốc thưởng"* (xem §Phạm vi ảnh hưởng
  bên dưới: solver **nhận** view này nhưng đường l1r **chưa nối** vào production).
- **`shift_plan.points_now` = 35 lúc 8 giờ sáng**: điểm của cuốc chạy buổi chiều. Đây **đúng họ
  lỗi** mà AUDIT A3 LAYEROUT-4 đã sửa cho `bonus_gap` từ UPDATE-070 — `shift_plan` bị bỏ sót.

Một **false positive** tôi đã loại: `demand_by_hour` sau fix lọc theo `request_time`, còn probe
cắt theo `complete_time` (khoá đầu trong danh sách) ⇒ cuốc đặt 07:50 xong 08:10 bị probe loại
nhưng deriver giữ. Deriver ĐÚNG: tại 08:00 ta đã biết có yêu cầu lúc 07:50. Lệch định nghĩa
khoá cắt, không phải rò rỉ.

## Phạm vi ảnh hưởng — kiểm bằng grep, và nó HẠ mức nghiêm trọng

`grep -rn "from_l1r" --include="*.py" src/ ui/ scripts/` (trừ chính file đó) = **0 kết quả**.
Toàn bộ module `features/from_l1r.py` **chưa được import ở bất kỳ đâu ngoài tests** — nó là
đường PI-4a dựng sẵn cho khi có dữ liệu thật, chưa nối vào UI hay pipeline nào.

**Hệ quả trung thực, cả hai chiều:**

- ✅ **Không con số nào đã công bố bị ảnh hưởng.** E10/E10b và mọi artifact A/B đọc `world`/
  `sim_metrics`, không đọc `from_l1r`. Đây là kiểm bằng grep, không phải suy luận như tôi ghi
  ở bản nháp đầu của UPDATE này.
- ⚠ **Mức nghiêm trọng thấp hơn tôi viết ban đầu** (`D-M3-11` sev CAO là do 1 test đỏ trong
  suite, không phải do số sai đã đi ra ngoài). Tôi đã hạ mô tả cho khớp — sáu rò rỉ này là
  **bom hẹn giờ**, không phải đám cháy: chúng sẽ hoạt động đúng vào lúc nối l1r vào production,
  tức đúng lúc bắt đầu tin vào số của nó.
- Test `test_derivation_from_real_tables` gọi `solve(v)` với view l1r và validate
  `solver_report` ⇒ solver **chấp nhận** view này. Nên "chưa nối" là chuyện của đường chạy,
  không phải của tính tương thích.

### Vì sao đường SIM không có họ lỗi này (kiểm, không giả định)

`RealizedDemandEstimator.estimate` (E10a) cắt đúng: `if e.t_min >= t_lim: break` với
`t_lim = idx*b`, cửa sổ `[lo, idx)` **chỉ chứa bucket đã trọn**. Và tổng quát hơn: trong sim,
event chỉ tồn tại **sau khi xảy ra** (append theo tick) nên đọc "cả danh sách" vẫn không thể
thấy tương lai. Đường l1r thì ngược lại — nó đọc **bảng tĩnh đã có trọn ngày**, nên *không cắt*
đồng nghĩa *đọc tương lai*.

⇒ Hai đường có **cấu trúc rủi ro khác nhau**, và đó là lý do cổng `D-M3-12` cần thiết cho l1r
mà không cần cho sim. Ghi lại để lần sau không đi tìm cùng lỗi ở chỗ nó không thể tồn tại.

## Fix

Một helper `_observed_seconds(start, dur_s, t_now)` — trả 0 nếu chưa bắt đầu, cắt về
`t_now - start` nếu đang diễn ra, giữ nguyên nếu đã kết thúc; chuỗi không parse được thì giữ
`dur_s` (thà giữ số cũ hơn im lặng làm rỗng view). Ngưỡng `idle_min_seconds` áp **SAU** khi cắt:
dwell vừa dài 2′ không phải "chờ lâu".

`active_reposition` thêm một quyết định về **vùng mù dữ liệu**: `reached_target_at` rỗng trong
cả mock lẫn 13 bảng thật, nên với segment còn đang diễn ra ta **không biết** đã tới đích chưa ⇒
khai `reached: None` ("chưa chốt") thay vì chép sẵn `True` của tương lai. Schema đã cho phép
`null` nên không cần đổi contract.

## Và một bug thứ BẢY, do chính test của mục nợ tìm ra

Tôi viết test cho *đường parse lỗi* của `_observed_seconds` (nợ `D-M3-12`) chỉ để pin hành vi
fallback. Test **đỏ ngay** — nhưng không vì lý do tôi đoán: view **NỔ `ValueError`**.

`_hour(start)` làm `int(iso[11:13])`, nên timestamp **rác** (không phải rỗng) gây exception —
`start = r.get("entered_current_hex_at") or seen` chỉ đỡ field **RỖNG**, không đỡ field **RÁC**.
Lỗi này **có trước `D-M3-11`**; nó chỉ chưa lộ vì mock luôn sinh timestamp đúng định dạng.

Sửa: `start` rác ⇒ lùi về `last_seen_at`; nếu nó cũng không parse được ⇒ **bỏ record**, vì một
record không định vị được trong thời gian thì mọi con số của nó vô nghĩa. Hai test mới cho hai
nhánh, cộng một test ghi lại **vùng mù còn lại**: với dữ liệu *naive* (không offset), việc cắt
`t_now` **im lặng không có tác dụng** — tức fix này vô hiệu đúng ở loại dữ liệu đó và view không
báo gì. Nếu bảng thật GSM không dùng offset thì phải đóng nốt `D-M3-12` **trước khi tin số**.

## Files

- **SỬA** `src/gsm_core/features/from_l1r.py` — `_observed_seconds` + `_parsable_ts` (mới) +
  5 điểm cắt + đỡ crash timestamp rác
- **TẠO** `specs/simulation/d-m3-04-multiday-prereg-locked.json` — prereg khoá cho phép đo
  kế tiếp (kỳ vọng đăng ký trước: Δ ≤ 0 vì world là β=0; kèm dự đoán CÓ THỂ SAI Δ ∈ [−1.500, +500])
- **SỬA** `specs/simulation/d-m3-04-multiday-ab-brief.md` — chốt 3 câu hỏi thiết kế + acceptance
  mới; ghi rõ việc CÒN LẠI: nối `health_guardrail(actor_ids=…)` vào `aggregate_health_guardrail`
- **TẠO** `tests/test_future_leak_l1r.py` — **18 test** (13 cho 6 rò rỉ + 5 cho đường parse
  lỗi/crash)
- **SỬA** `tests/test_idle_reduction.py::test_derivation_from_real_tables` — nó **pin đúng hành
  vi lỗi** (cộng dwell TOÀN NGÀY rồi so với view hỏi lúc 18:00); sửa mẫu số cho cắt tại `t_now`,
  ghi chú lý do tại chỗ
- **SỬA** `tracking/DEFERRED.md` — `D-M3-11` từ `UNRESOLVED` sang đã fix

## Kiểm chứng

- 13 test: **9 đỏ trước / xanh sau** cho ba chỗ đầu; 4 test cho hai deriver sau viết **sau** khi
  sửa code (tôi làm ngược quy trình ở đó) nên chúng được **mutation-verify** bù lại.
- **Mutation**: đảo từng fix về hành vi cũ, mỗi lần suite `test_future_leak_l1r.py` phải đỏ —
  **6/6 mutation đều bị bắt** (M1 idle bỏ cắt: 4 đỏ; M2 `demand_by_hour`, M3 reposition, M4
  bonus hist, M5 shift `points_now`, M6 shift forecast: mỗi cái 1 đỏ), khôi phục bản thật ⇒ 13
  xanh. **Không có test yếu.**
- `tests/test_features_from_l1r.py` + `test_idle_reduction.py` + file mới: **36 xanh**.
- Full suite **CẢ HAI lệnh**: `uv run pytest -q` → **917 passed / 4 skipped / 0 failed**
  (19:50) · `uv run pytest -q ui/backend/tests` → **65 passed**. Tổng **982**.
  Con số khớp kiểm đếm: suite sau fix đầu là 904 (đã xanh — test đỏ ban đầu hết ngay từ fix cắt
  `t_now`), cộng 13 test thêm vào cùng file ⇒ 917. **0 đỏ, không xfail, không nới ngưỡng nào.**

## Adversarial self-review / flaws found

- **Tôi định đóng cái này thành "lệch hai bảng, ghi nợ rồi đi tiếp".** Nếu dừng ở đó, 6 rò rỉ
  vẫn nằm nguyên trong đường sản phẩm và mã nợ `D-M3-11` sẽ mô tả sai bản chất. Thứ cứu tình
  huống là **dump segment ra xem**, thấy `23:03 > 23:00` — một câu lệnh, không phải suy luận.
- **Bốn trong sáu chỗ tôi tìm được bằng probe, không bằng đọc code.** Tôi đã đọc chính hàm
  `derive_idle_reduction_input_l1r` khi sửa chỗ đầu và **vẫn không thấy** `demand_by_hour` với
  `active_reposition` — mắt tôi neo vào `idle_segments`. Bài học có thể tái dùng: khi đã bắt được
  một lỗi *thuộc họ nào đó*, viết **phép thử cho cả họ** rồi quét, đừng tự soi bằng mắt.
- **`from_l1r.py:104` đã có luật đúng từ UPDATE-070 mà 5 chỗ khác vẫn thiếu** — cùng mẫu
  `D-R12`/`D-M3-08`: một bảo đảm được sửa ở MỘT điểm gọi rồi coi như xong toàn hệ. Đề nghị nợ
  mới `D-M3-12`: biến probe này thành **test thường trực** cho mọi deriver nhận `t_now`, để
  deriver thêm sau không lặp lại. Chưa làm trong cycle này (cần chốt khoá cắt cho từng entity,
  và chính false positive ở trên cho thấy khoá sai sẽ tạo báo động giả).
- **Tôi đã suýt báo sai mức nghiêm trọng theo chiều PHÓNG ĐẠI.** Bản nháp đầu của UPDATE này
  viết *"S1 dùng đúng số này"* và để `D-M3-11` ở sev CAO như thể số sai đã đi ra ngoài. Grep
  cho thấy `from_l1r` **chưa được import ở đâu cả** ⇒ không số nào đã công bố bị ảnh hưởng. Đã
  sửa lại cả hai chỗ. Ghi ra đây vì đây là **cùng loại lỗi** với những lần tôi báo số sai cho
  Cường trước đó — chỉ khác chiều: lần này là thổi lên, không phải bỏ sót.
- `_observed_seconds` giữ nguyên `dur_s` khi parse lỗi hoặc naive/aware lệch nhau — **fallback
  im lặng**, đúng loại thứ repo đã trả giá vì nó. Nay đã có 5 test pin cả ba nhánh, và chính
  chúng tìm ra bug crash thứ bảy. Phần CÒN LẠI của `D-M3-12`: **khai cờ ra output** thay vì im
  lặng (cần sửa schema `additionalProperties: false` nên nằm ngoài cycle này). Với dữ liệu naive,
  fix `D-M3-11` **vô hiệu và không báo gì** — đó là vùng mù đã khai, không phải đã đóng.
- **Tôi viết test cho một mục NỢ và nó tìm ra bug mới.** Đáng ghi lại vì nó ngược với trực giác:
  test viết để *pin hành vi đã biết* lại phơi ra một crash chưa ai gặp. Rẻ hơn nhiều so với gặp
  nó lúc nối bảng thật vào.

## Visual review

`NOT_APPLICABLE` — không đổi dashboard/replay; đổi giá trị L3 view (đường sản phẩm, chưa có UI
nào render `historical_points_per_hour`/`demand_forecast` trong Track UI hiện tại).

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**19 mục đang chờ Cường check**: V-01…V-14, V-16, V-17, V-18 (kèm card im lặng), V-20, V-21.
Hoãn ≠ waive. Chi tiết: `tracking/PENDING-REVIEW.md`.

⚠ **Đính chính con số**: UPDATE-114 và bản nháp của UPDATE này ghi *"20 mục"* — đếm lại theo
mục `## ⏳ CHỜ CHECK` của `PENDING-REVIEW.md` thì đúng là **19** (V-15 và V-19 đã ĐÓNG, nằm ở
mục `✅ ĐÃ CHECK XONG`). Tôi đã cộng nhầm một mục đã đóng.
