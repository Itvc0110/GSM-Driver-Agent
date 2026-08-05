# UPDATE-138 — `D-QD4-03`/`V-28`: lan can SỨC KHOẺ cho kênh KÉO CA (`shift_extend`)

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent, theo quyết định Cường (*"chọn b"* — giữ đo, thêm lan can)
- **Loại:** fix (ranh giới sản phẩm) + sim behavior
- **TODO / liên quan:** `D-QD4-03` · `V-28` · nối tiếp UPDATE-137 (QĐ-4)

## Tóm tắt

Kênh **kéo dài ca** đang được đo mức nghe lời và có **0 lan can sức khoẻ**, trong khi kênh **hoãn
nghỉ** — cùng họ theo chính khai báo của repo — có **ba**. Update này thêm ba lan can
(`soc_low` · `fatigued` · `would_exceed_fatigue`) **kèm đường quan sát** để guardrail tầng 5 đếm
được. Kênh vẫn **ở trong bảng đo** (Cường chốt (b), không chuyển sang `SOFT_TOPICS`).

## Chi tiết cập nhật

### Vì sao đây là ranh giới, không phải tinh chỉnh

Lập luận §1.2c — *"một khi `rest_adherence` tồn tại như một con số, nó sẽ được nhìn như thứ cần cải
thiện"* — áp **nguyên văn** cho `shift_extend_adherence`, chỉ đổi dấu: "cải thiện" ở đây nghĩa là
**nhiều tài xế hơn đồng ý làm dài giờ hơn**.

Ba bằng chứng repo tự mâu thuẫn, đều kiểm được:

| # | Bằng chứng |
| --- | --- |
| 1 | `policy_locks.py:40-42` khoá `advice.shift_extend_max_min` **ngang hàng** `rest_defer_max_min`, comment nguyên văn *"cùng họ: **kéo dài thời gian làm việc vì tiền**"*; module tự gọi mình là *"KHOÁ CHÍNH SÁCH SỨC KHOẺ … lan can sức khoẻ (§1.2b)"* |
| 2 | `check_shift_extend` **có** đọc `actor.online_min` — nhưng làm **mẫu số năng suất** (`rate = points/online_h`), không phải cổng mệt ⇒ **tài xế mệt mà năng suất cao vẫn được khuyên kéo ca** |
| 3 | `sim_metrics.SPAN_P90_RISE_TOL = 0.10` — guardrail tầng 5 **tố giác** khi `work_span_p90` tăng >10%; còn `adherence_view` **tính là thành tích** cái tỷ lệ làm nó tăng |

### Ba lan can, và vì sao cần cái thứ ba

| Thứ tự | Điều kiện | reason |
| --- | --- | --- |
| 1 | `soc_pct <= soc_threshold` | `soc_low` |
| 2 | `online_min > fatigue_threshold_min` | `fatigued` |
| 3 | `online_min + need_min > fatigue_threshold_min` | `would_exceed_fatigue` |

Lan can 3 là phần Cường chọn thêm, và **đo được là phần làm gần hết việc**: hoãn nghỉ chỉ **đổi
thời điểm**, còn kéo ca **thêm giờ làm** ⇒ cái hại nằm ở chỗ lời khuyên **ĐẨY** tài xế qua ngưỡng,
không chỉ ở chỗ họ đã qua. Ca lọt nếu chỉ có lan can 2: `online_min` = ngưỡng − 10′, `need_min` =
40′ ⇒ kết thúc ở ngưỡng + 30′.

`soc_threshold` **không bịa số mới** — dùng đúng nguồn world truyền cho `should_defer_rest`:
`float(self.veh["swap_soc_threshold_pct"])`.

**Thứ tự có chủ ý:** lan can 3 đứng **TRƯỚC** `cap_unreachable`. Khi một lời khuyên vừa vượt trần
kinh tế vừa đẩy qua ngưỡng mệt, lý do báo ra phải là lý do **SỨC KHOẺ** — nếu không, bảng veto sẽ
nói *"hết trần"* cho đúng những ca mà lan can sức khoẻ mới là thứ chặn, và người đọc kết luận sai
rằng lan can chưa bao giờ cần tới.

### Đường quan sát — phần suýt bị bỏ sót, và sever bắt được

`should_defer_rest` trả `(bool, reason)` → world log `advice_rest_veto` → `rest_rails_audit` đếm →
**guardrail tầng 5**. `check_shift_extend` trả **`float`**, và `world.py` làm `if added:` ⇒ **trả
0.0 thì không log gì**.

⇒ Thêm lan can mà không đổi cái này thì lan can **chặn đúng nhưng vô hình**: không reason, không
counter, guardrail không thấy. Nên: `check_shift_extend` → `tuple[float, str]`, world log
`advice_extend_veto`, thêm `EXTEND_RAILS` + `extend_rails_audit` nối vào `full_report`.

⚠ `EXTEND_RAILS` **không** chứa `extend_cap`/`cap_unreachable` — đó là ràng buộc **kinh tế**; gộp
vào sẽ thổi `xveto_fired_n` bằng những lần chặn chẳng liên quan sức khoẻ. Tiền tố `xveto_` để không
đè khoá của `rest_rails_audit` (hai bộ đếm sống chung một dict).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/advice_bridge.py` | sửa | `check_shift_extend` → `(float, str)`; 3 lan can; reason cho **mọi** nhánh (mẫu số `xveto_calls_n`) |
| `src/gsm_sim/world.py` | sửa | nhận tuple; log `advice_extend_veto` **chỉ khi** reason ∈ `EXTEND_RAILS`; import `EXTEND_RAILS` (một nguồn) |
| `src/gsm_sim/sim_metrics.py` | sửa | `EXTEND_RAILS` + `extend_rails_audit` + nối `full_report` |
| `tests/test_shift_extend_rails.py` | **tạo** | 13 test, gồm **2 test chạy `run_once` THẬT** |
| `tests/test_advice_time_encoding.py` | sửa | 5 call site theo chữ ký mới + `_SOC_THRESHOLD = 0.0` có giải thích |

## Assumptions và evidence

| Claim | Nhãn | Bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Kênh `shift_extend` TẮT ở config sản phẩm ⇒ hôm nay 0 lời khuyên tới tài xế | `OBSERVED-CODE` | `configs/pilot_dongda.yaml:338` | CAO | nếu sai thì đây là lỗ ĐANG SỐNG, không phải nợ |
| `shift_dp` không sinh `EXTEND` ⇒ đường sản phẩm v2 không có topic này | `OBSERVED-CODE` | `shift_dp.py:16` `ACTIONS = ("ONLINE","REST","SWAP","END")` | CAO | nếu sai thì mức phải nâng lên CAO |
| Config mặc định **bit-identical** trước/sau | `[ĐO]` | fingerprint per-actor + bảng đếm event, **5/5 seed identical** (1000/1001/1002/2000/3160) | CAO | — đã đo, không suy luận |
| Lan can có đường chạy thật | `[ĐO]` | kênh BẬT seed 1000/1001/1002: 3369/4357/3856 lần chặn, **100%** thuộc rail | CAO | — |
| `online_min` là **PROXY** của mệt | `PROXY` | `D-M3-19`: `online_min` **gộp cả thời gian nghỉ** | — | lan can chặn theo một đại lượng không phải phút lái thật |

## Kiểm chứng

### Sever-restore THẬT — 11/11

Bốn bước: tiêm file nguồn thật · `uv run pytest` thật · restore · verify `sha256`.

| Mũi | Kết quả |
| --- | --- |
| j1 gỡ lan can SOC · j2 gỡ `fatigued` · j3 gỡ `would_exceed_fatigue` | **BẮT** |
| j4 đổi `>` → `>=` (sai chiều một ký tự) | **BẮT** |
| j5 trần kinh tế đứng trước lan can sức khoẻ (lý do báo sai) | **BẮT** |
| j6 gộp hai reason mệt thành một | **BẮT** |
| j7 kênh TẮT lại báo là lan can | **BẮT** |
| **j8 bỏ log `advice_extend_veto` ở world** | **BẮT** *(sau khi sửa — xem dưới)* |
| j9 `extend_rails_audit` mất caller · j10 `EXTEND_RAILS` nuốt trần kinh tế · j11 audit lẫn kênh nghỉ | **BẮT** |

🔴 **j8 ban đầu LỌT.** Mọi test khác kiểm `check_shift_extend` (đơn vị) và `extend_rails_audit`
(event tổng hợp) — **không cái nào kiểm khúc GIỮA**: world có thật sự ghi event không. Gỡ dòng
`self.log(...)` ⇒ lan can vẫn chặn đúng nhưng vô hình, cổng vẫn xanh. Đúng định nghĩa **cổng trang
trí** mà cycle này sinh ra để tránh. Đã thêm 2 test chạy `run_once` THẬT (7s).

⚠ j1/j4 lần đầu **ANCHOR-FAIL** — `should_defer_rest` có dòng **y hệt** nên anchor một dòng khớp 2
lần. Script từ chối chạy thay vì tiêm nhầm vào kênh NGHỈ. Nếu nó im lặng thì tôi đã báo "11/11"
trong khi hai mũi chưa hề được thử.

### Seeds và scenarios

| Command | Seed | Kết quả |
| --- | --- | --- |
| `uv run pytest -q` (toàn suite) | n/a | **1058 passed · 5 failed · 4 skipped** (20′09″) — 5 F **đỏ sẵn** (`K-01`/`K-02`/`K-03`), **0 lỗi mới** |
| `uv run pytest -q ui/backend/tests --ignore=…test_demo_advice_ack.py` | n/a | **188 passed** (`--ignore` vì `K-02` gây lỗi collection, đỏ sẵn trên `origin/main`) |
| `uv run pytest -q tests/test_shift_extend_rails.py` | n/a | **13 passed** (7s) |
| `uv run pytest -q tests/test_advice_time_encoding.py` | n/a | **8 passed** — vẫn chạm đúng nhánh (fixture đứng ngoài cả 3 lan can) |
| fingerprint config **mặc định** trước/sau | 1000·1001·1002·2000·3160 | **5/5 IDENTICAL** |
| `run_once` kênh **BẬT** | 1000·1001·1002 | xem bảng dưới |
| sever `scratchpad/sever_extend_rails.py` | n/a | **11/11 BẮT ĐƯỢC** |

### 🔴 Số MỚI khi kênh BẬT — và một điều KHÔNG được đọc sai

| seed | nói TRƯỚC | nói SAU | `xveto_calls` | `fatigued` | `would_exceed` | `soc_low` |
| --- | --- | --- | --- | --- | --- | --- |
| 1000 | 110 | 95 | 3369 | 380 | **2854** | 135 |
| 1001 | 107 | 82 | 4357 | 292 | **3936** | 129 |
| 1002 | 75 | **79** ⚠ | 3856 | 260 | **3469** | 127 |

**(a) ~~Lan can 3 làm ~85% việc~~ — 🔴 ĐÍNH CHÍNH 2026-08-05, câu này ĐẾM SAI ĐẠI LƯỢNG.**

Xem mục *"ĐÍNH CHÍNH số 85%"* ngay dưới. Tóm tắt: 85% là *"lan can được BÁO CÁO bao nhiêu lần"*,
không phải *"lan can THÊM GIÁ TRỊ bao nhiêu"* — vì tôi cố ý đặt nó **trước** trần kinh tế.

**(b) ⚠ seed 1002 số lời khuyên TĂNG (75 → 79).** Một lan can **không thể** thêm lời khuyên. Đây là
**trôi quỹ đạo**: chặn một lần kéo ca làm actor ở trạng thái khác ⇒ cơ hội kéo ca về sau khác ⇒
RNG stream lệch. Đúng thứ `D-SIM-K3` (note của Khánh §7) cảnh báo: *cùng seed ≠ cùng realization*.

⇒ **Không được đọc bảng này thành "lan can làm mất N lời khuyên"**. Con số đó không tách được khỏi
nhiễu quỹ đạo cho tới khi có keyed RNG. Cái đọc được: lan can **có đường chạy thật**, và
`would_exceed_fatigue` là nhánh chi phối.

### 🔴 ĐÍNH CHÍNH số 85% (2026-08-05) — tôi đã đưa con số sai cho Cường

Bản đầu của UPDATE này, của commit `5432486`, của `DEFERRED`/`PENDING-REVIEW`/`PROJECT-GRAPH`, và
câu tôi nói với Cường (*"lựa chọn 'cả hai' của anh có số chống lưng"*) đều dựa trên:

> *"`would_exceed_fatigue` chiếm ~85% số chặn ⇒ nhánh 'đã mệt' một mình chỉ bắt ~11%"*

**Câu đó đếm sai đại lượng.** Tôi **cố ý** đặt `would_exceed_fatigue` **TRƯỚC** `cap_unreachable`
(để lý do báo ra là lý do sức khoẻ — quyết định đó vẫn đúng). Hệ quả: **mọi ca mà trần kinh tế cũng
sẽ chặn đều được tính cho lan can sức khoẻ.** 85% là *"lan can được BÁO CÁO bao nhiêu lần"*, không
phải *"lan can THÊM GIÁ TRỊ bao nhiêu"*.

Đo lại phần **BIÊN** — số ca mà lan can là thứ **DUY NHẤT** chặn (kinh tế cho phép: `need_min ≤` trần):

| lan can | đã bắn | kinh tế **cũng** chặn | 🔴 **BIÊN** | % biên |
| --- | ---: | ---: | ---: | ---: |
| `soc_low` | 391 | 344 | **47** | 12,0% |
| `fatigued` | 932 | 758 | **174** | 18,7% |
| `would_exceed_fatigue` | 10 259 | 10 070 | **189** | **1,8%** |
| **TỔNG** | 11 582 | | **410** | **3,5%** |

⚠ Ước lượng BIÊN dùng trần đầy 60′ làm cận trên của "trần còn lại" ⇒ nó là **cận TRÊN** của giá trị
lan can. Nói quá về giá trị một lan can tệ hơn nói thiếu.

**Bức tranh thật, đảo ngược câu tôi đã nói:**

- `would_exceed_fatigue` **đóng góp biên NHỎ NHẤT** (189 ca, 1,8%) — không phải "làm 85% việc".
  98,2% ca nó báo cáo là ca `need_min` khổng lồ (tài xế năng suất thấp, cần hàng trăm phút để với
  mốc) mà trần 60′ vốn đã chặn.
- `fatigued` — nhánh tôi bảo *"một mình chỉ bắt ~11%"* — thực ra có **biên LỚN NHẤT** (174 ca).
- Cả ba cộng lại chỉ **410/11 582 = 3,5%** là chặn thật sự thêm.

**Lựa chọn (b) của Cường vẫn đúng, nhưng KHÔNG vì lý do tôi đưa.** Giá trị của lan can không nằm ở
số ca — nó nằm ở chỗ **410 ca đó là những ca kinh tế NÓI ĐƯỢC mà sức khoẻ nói không**. Đó chính xác
là những ca ranh giới sinh ra để chặn: lời khuyên *khả thi về tiền* nhưng *đẩy tài xế quá sức*. Một
lan can chặn 3,5% mà đúng 3,5% ấy thì có giá trị; một lan can chặn 85% ca mà 98% trong đó đã bị chặn
sẵn thì chỉ là tiếng ồn trong bảng đếm.

**Vì sao tôi mắc:** tôi đã tự nêu đúng rủi ro này ở phần thiết kế (*"lan can sức khoẻ ưu tiên hơn
trần kinh tế ⇒ bảng veto sẽ nói 'hết trần' cho đúng những ca…"*), thậm chí viết test `j5`/
`test_DOI_CHUNG_lan_can_SUC_KHOE_uu_tien_hon_tran_kinh_te` cho nó — rồi **vẫn đọc bảng đếm như thể
nó là bảng giá trị**. Biết một cái bẫy không đủ; phải đo trước khi trích số.

### `xveto_calls_n` ≠ số lời khuyên bị chặn

3369 là số **lần poll** bị chặn, không phải 3369 lời khuyên biến mất — kênh được hỏi mỗi tick idle,
cùng một actor ở cùng trạng thái bị đếm nhiều lần. Đây đúng lý do `rest_rails_audit` bắt buộc kèm
`veto_calls_n` làm mẫu số.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** không đổi UI nào. Thay đổi nằm ở `advice_bridge` / `world` / `sim_metrics` và test.
  Kênh `shift_extend` TẮT ở config sản phẩm ⇒ không có gì hiện ra màn hình để xem.
- **Cái CẦN xem khi bật kênh:** dashboard tab 🧭 Hành trình — vạch advice của `shift_extend` phải
  **thưa hẳn đi** ở tài xế có `online_min` cao. Ghi vào `PENDING-REVIEW` khi Cycle B chạy.

## 🔴 CỔNG RANH GIỚI SỨC KHOẺ BẮT CHÍNH TÔI — và đó là lỗi QUY TRÌNH

Suite chính báo **2 lỗi MỚI** (ngoài 5 cái đỏ sẵn `K-01`/`K-02`/`K-03`):

```
tests/test_health_boundary.py::test_no_fatigue_in_payout_path
  → src/gsm_sim/world.py:873 [World._actor_proc]
    token cấm 'fatigue_threshold_min' trong scope MONEY
```

Bản đầu của event `advice_extend_veto` log kèm `fatigue_threshold_min=…` **cho tiện đọc**.
`World._actor_proc` nằm trong **scope MONEY**, nơi spec §7.4 cấm token `fatigue*`. **Cổng đúng,
tôi sai** — `reason` đã đủ cho `xveto_*`; con số ngưỡng chỉ là tiện nghi, và nó đổi lấy một vi phạm
ranh giới. Đã bỏ; danh sách `money_manifest` **vẫn đúng 4 mục** như trên `origin/main` (tôi không
làm nó dài thêm).

### Lỗi thật nằm ở chỗ khác — tôi RELAY một claim chưa verify

Trước khi Cường chốt, tôi viết trong ô lựa chọn của `AskUserQuestion`:

> *"đã kiểm: cổng `test_health_boundary` **KHÔNG chặn** việc này"*

Câu đó lấy từ **báo cáo của một tác tử soi**, và **tôi không tự kiểm**. Tác tử kiểm
`check_shift_extend` (`advice_bridge`, đúng là ngoài scope quét) nhưng **không kiểm chỗ tôi sẽ
LOG** (`world`, trong scope). Nên câu tôi đưa cho Cường để ra quyết định là **đúng một nửa**.

Bộ nhớ của tôi có sẵn dòng *"~1/4 finding của soi độc lập là sai"* và *"luôn kèm vòng phản biện"*.
Tôi đã áp nó cho **những claim bất lợi** (bốn lỗi soi tố tôi — tôi kiểm lại từng cái bằng code)
nhưng **không áp cho claim THUẬN LỢI** — cái nói rằng đường tôi định đi không bị chặn. Đó là thiên
lệch xác nhận, và nó nguy hiểm hơn vì không ai thấy khó chịu khi nghe tin tốt.

**Luật rút ra:** claim làm cho việc DỄ HƠN phải bị verify **kỹ hơn** claim làm cho việc khó hơn.

## Adversarial self-review / flaws found

1. **Cái gì trông tốt nhưng sai?** — "11/11 sever" có thể là 11 mũi dễ. Ba mũi (j5, j7, j10) canh
   **hướng ngược**: lan can đóng quá tay, báo sai lý do, hoặc nuốt cả ràng buộc kinh tế. Và j8 —
   mũi khó nhất — **đã LỌT ở vòng đầu**, tức bộ mũi này không phải bộ dễ.
2. **Điểm yếu nhất: `online_min` là PROXY.** Nó gộp cả thời gian nghỉ (`D-M3-19`) ⇒ một tài xế nghỉ
   nhiều vẫn có `online_min` cao và bị lan can chặn oan. `should_defer_rest` dùng **cùng** proxy nên
   giữ đối xứng là đúng — nhưng cả hai kênh đang chặn theo một đại lượng không phải phút lái thật.
   → nợ `D-QD4-05`: tách `drive_min` cho **cả hai** kênh cùng lúc; sửa một bên là tạo bất đối xứng mới.
3. **Behavior-neutral: đã ĐO, không suy luận.** Cycle trước tôi tuyên bố behavior-neutral bằng suy
   luận cấu trúc và bị phép đo bác (V-29). Lần này fingerprint 5/5 seed identical **trước khi** viết
   câu đó.
4. **Số `shift_extend` cũ nay STALE** — `advice_bridge.py:385,392` (0,394 vs sự thật 0,473; 1,000 vs
   0,311). Chúng đo trên kênh **không có lan can**. Không được trích lại như số hiện hành.
5. **Chưa kiểm:** tác động lên `work_span_p90` và tầng 5 khi kênh bật — cần A/B đủ seed, không phải
   3 run đơn. Ghi là CHƯA ĐO.
6. **Đã loại trừ:** *"lan can chặn oan cả kênh"* — bác bằng `test_DOI_CHUNG_tai_xe_khoe_van_duoc_khuyen`
   và bằng số: kênh vẫn nói 95/82/79 lần.
7. **Flaw còn mở → ID:** `D-QD4-05` (proxy `online_min`) · `D-SIM-K3` (trôi quỹ đạo làm mọi Δ của
   kênh này chưa tách được nhiễu).

## Expansion checkpoint (T-039)

1. **Schema:** không đổi. Event `advice_extend_veto` là log-only, không vào contract UI.
2. **Bài toán tối ưu:** không có residual mới. Ngược lại, cycle này **thu hẹp** không gian lời
   khuyên có chủ ý — đúng ranh giới §1.2b/§1.2c.
3. **Tính năng:** `xveto_*` mở đường cho một cột *"advisor đã im vì sức khoẻ bao nhiêu lần"* trong
   guardrail tầng 5 — nhưng chỉ có nghĩa sau khi `D-SIM-K3` khoá được RNG.

## Follow-up / defer phát sinh

| ID | Việc | Severity | Điều kiện mở lại |
| --- | --- | --- | --- |
| `D-QD4-05` | `online_min` là proxy của mệt (gộp cả nghỉ) — tách `drive_min` cho **cả hai** kênh | TB | làm cùng `D-M3-19`; sửa một kênh là tạo bất đối xứng mới |
| — | Ràng buộc khoá của `D-QD4-03` (**không bật `shift_extend` để đo trước khi có lan can**) nay **ĐÃ GỠ** | — | lan can có thật + sever 11/11 |
| — | `work_span_p90` / tầng 5 khi kênh bật: **CHƯA ĐO** | — | Cycle B hoặc A/B đủ seed |
