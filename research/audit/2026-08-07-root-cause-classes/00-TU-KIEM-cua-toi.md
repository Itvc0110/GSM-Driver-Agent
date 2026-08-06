# Bốn điều **tôi tự kiểm** trước khi trình plan (2026-08-07)

> Không phải agent báo. Mỗi mục dưới đây tôi mở code/artifact/git ra đọc, và ghi rõ cái gì **đo được**
> vs cái gì **suy ra**. Ba lần trong hai ngày qua tôi suýt trích một con số trả lời sai câu hỏi, nên mục
> nào tôi *chưa* kiểm thì nói thẳng là chưa.

---

## 1. ⭐ NẶNG NHẤT — bản án giết `shift_plan` được tuyên bởi một solver **không nhìn thấy mốc thưởng**

**Đo được (git, không suy luận):**

| việc | commit | ngày |
| --- | --- | --- |
| ĐA-07 tắt `shift_plan` trong config | `5a44cbb` | **2026-07-28** |
| E5 đo lại (`D-ĐA07-recheck`) ⇒ củng cố ĐA-07 | — | 2026-07-29 |
| **Sửa `points_band_size` 15 → 5** (`ADV-01`) | `bec2671` | **2026-08-06** |

Ở band 15, `shift_dp.py:207` là `pb + add_pts // PBS`. Giờ thường `pph = 5`, `exp_trips ≈ 1–2,2`
⇒ `add_pts ≈ 5–11` ⇒ `add_pts // 15 = **0**` ⇒ **points_band ĐÓNG BĂNG suốt DP** ⇒ mốc thưởng ngày
(60/100/160/200) **không bao giờ vào được giá trị Bellman**. Chính comment trong repo nói vậy
(`shift_dp.py:21-25`, do tôi đọc chứ không nhớ): *"lịch S2 tối ưu như thể không có thưởng"*.

⇒ **Cả hai vế bằng chứng của ĐA-07 đều sinh ra từ solver đó**: vế *"không có giá trị"* (payout ns) và
vế *"còn có hại"* (served −0,33đp SIG, đơn chết +4,1 SIG). Một DP mù thưởng thì lịch REST/SWAP/END nó
xếp **không neo vào thứ nó tồn tại để tối ưu**.

**⚠ Tôi KHÔNG kết luận "S2 thật ra có giá trị".** Rất có thể nó vẫn vô dụng — DP còn tối ưu payout
từ cuốc, thưởng chỉ là terminal. Điều tôi khẳng định hẹp hơn và chắc chắn hơn:

> **Chưa ai đo `shift_plan` bằng solver đã sửa.** Bản án hiện hành dựa trên bằng chứng đã hỏng ở đúng
> cơ chế mà kênh này tồn tại để khai thác.

**Đã có ai ghi nghĩa vụ đo lại chưa? — CHƯA.** `D-E4-01` có nói ADV-01 trơ, nhưng quy nguyên nhân cho
**world zero-cost** (`cash_cost=0`), *không* quy cho lỗi band. Hai cách giải thích **cạnh tranh** và
**tách được**: band chạm phía **doanh thu** (thưởng), zero-cost chạm phía **chi phí**. Cả hai có thể
cùng đúng — nhưng hiện chỉ một cái được ghi hồ sơ.

**Chưa kiểm:** giữa 28/07 và 06/08 còn hàng chục fix khác (`D-M3-*`, `ADV-*`) ⇒ đo lại là một phép đo
**MỚI**, không phải so thẳng với số cũ. Phải chạy cả hai arm tươi.

---

## 2. `R-2` — lan can `soc_low` bất khả đạt: **xác nhận, và nặng hơn agent báo**

**Chứng minh cấu trúc (đọc code):**
- `world.py:1037` — chỉ vào nhánh khi `action == IdleAction.REST`
- `behavior.py:151` — bước 1 của `choose_idle_action`: `soc_pct <= swap_threshold` ⇒ trả `GO_SWAP`/`GO_CHARGE`,
  **không bao giờ** tới REST
- `world.py:1040` — truyền vào `should_defer_rest` **đúng cùng** `swap_soc_threshold_pct`
- `advice_bridge.py:890` — `if actor.soc_pct <= soc_threshold: return False, "soc_low"`

⇒ Muốn tới dòng 890 phải có `soc > ngưỡng`; điều kiện dòng 890 là `soc <= ngưỡng`. **Rỗng theo cấu trúc.**

**Đo được (artifact của chính repo, `research/audit/2026-08-06-e1b/ladder-truoc.json`, 30 seed):**
`veto_soc_low_n = 0,0` ở **cả hai arm, mọi nấc thang**; `veto_fatigued_n = 55,0 = veto_fired_n`.

**Nguồn gốc:** `world.py:1030` ghi rằng `D-M3-04-FIX` đã **xoá hai nhánh GO_SWAP/GO_CHARGE** vì chúng là
code chết. Trước đó `soc_low` **sống** (nó chặn đúng 41 lượt đó). Xoá hai nhánh làm **chính lan can thành
mồ côi** — và không ai cập nhật `REST_RAILS` hay thêm test khai-trơ.

**Cổng lẽ ra phải bắt — nhưng mù:** `sim_metrics.py:537` là `if va >= RAIL_ALIVE_MIN_N and vb == 0`.
Nó bắt *"rail đang sống ở A thì chết ở B"*. Rail **chưa từng sống** (`va = 0`) ⇒ `va >= 20` sai ⇒
**không bao giờ nổ**. Cổng có thật, nhưng mù đúng ca đang xảy ra.

**⚠ Đính chính cho chính tôi — `defer_cap` KHÔNG phải phát hiện mới.** Tôi thấy `veto_defer_cap_n = 0,0`
và suýt báo là lỗi thứ hai. Mở nguồn ra thì `tests/test_rest_rails_guardrail.py:58-62` **đã khai trơ có
chủ ý**, kèm điều kiện mở lại (*"ĐỎ = TIN TỐT"*). Đây là **cách làm đúng** — và nó cho thấy khuôn sửa
cho `soc_low` đã có sẵn trong repo. (Quy tắc *"mở nguồn gốc con số trước khi nói nó sai"* cứu tôi lần
thứ **tư** trong ba ngày.)

**Mức độ — nói cho chính xác, đừng thổi:** tính chất an toàn *"pin thấp thì không hoãn nghỉ"* **vẫn
đúng**, vì bước 1 của `choose_idle_action` chặn ở thượng nguồn. Cái sai là **báo cáo**: tầng 5 tự trình
bày như cổng **3 lan can**, thực tế chỉ **1** (`fatigued`) có thể bắn. Đây là lỗ hổng **hiển thị**,
không phải lỗ hổng an toàn.

---

## 3. ⭐ Đảo thứ tự ưu tiên: **6/6 kênh advisor đang TẮT**

`configs/pilot_dongda.yaml:330-343` — `shift_plan` · `accept_lift` · `shift_extend` · `rest_window` ·
`swap_early` · `station_choice` = **false**. Kênh duy nhất bật: `positioning_overrides: wait_only`
(PASS 9/9 ĐA-08, Cường duyệt 2026-07-28).

⇒ **Bán kính ảnh hưởng HÔM NAY** của phần lớn nợ tôi đào ra hai ngày qua là **0**:
`S2-1..S2-6`, `R-1..R-7`, `D-E4-01/02`, `D-E4-06 station_choice` đều thuộc kênh đang ngủ.

⇒ Kế hoạch **không được** xếp theo *"nợ nào tôi tìm ra trước"* mà theo **bán kính ảnh hưởng thật**:

1. **Đường sản phẩm** (card tài xế thật) — `B6-PARITY`: sản phẩm chạy **đúng S1/9 solver**
2. **Kênh sim đang sống** — positioning/S4 (`D-ADV-01`)
3. **Độ tin của phép đo** — cổng lan can, dispatcher `k`, adherence, A2/HHI: chúng **gác mọi quyết
   định tương lai**, kể cả quyết định mở lại kênh ngủ
4. **Kênh ngủ** — vào `DEFERRED` kèm điều kiện mở lại, **không** thành cycle

⚠ Sắc thái: `channels: false` là **mặc định ship**; run nghiên cứu bật từng kênh qua override. Nên lỗi
trong kênh ngủ vẫn làm **hỏng phép đo** khi ai đó bật lên nghiên cứu — đó chính là chuyện đã xảy ra ở
mục 1. Vậy nên nó là **nợ đo lường**, không phải nợ sản phẩm.

---

## 4. `S2-2` — sàn điểm: **đã sửa một phần, phần dư vẫn còn, nhưng KHÔNG đáng một cycle**

`ADV-01` hạ band 15 → 5 (`bec2671`). Nhưng `shift_dp.py:207` vẫn `add_pts // PBS` ⇒ **phần dư
`add_pts % 5` bị vứt MỖI bucket**, không mang sang bucket sau. Đây là cắt cụt **tích luỹ**, không phải
làm tròn một lần: kỳ vọng mất `(PBS−1)/2 = 2` điểm/bucket.

**Nhãn: DERIVED, chưa đo.** Tôi đã viết probe để đo trên input thật rồi **xoá đi** — vì kênh đang tắt
(mục 3) nên con số đó không đổi được quyết định nào hôm nay. Nó chỉ có ý nghĩa **bên trong** việc đo lại
ở mục 1, và sẽ đo ở đó.

⇒ Xếp: **đi kèm cycle đo lại `shift_plan`**, không phải cycle riêng.

---

## 5. `B3` — **đã kiểm xong, và phải nói CHÍNH XÁC HƠN hồ sơ cũ**

Sốt ruột có **bốn** hiệu ứng, không phải một (`behavior.py:200-227`). Tôi kiểm từng cái:

| hiệu ứng | trạng thái | bằng chứng |
| --- | --- | --- |
| nới vành 1 → 3 | ❌ **NO-OP** | `_neighbors` dùng `grid_disk` (**đĩa**, `behavior.py:238`), nhưng niềm tin chỉ phủ `grid_disk(actor.cell, **2**)` (`world.py:1165`) ⇒ ô vành 3 đọc ra `0.0` ⇒ không bao giờ thắng phép so |
| hạ ngưỡng kén `bar` 1,25 → 1,05 | ✅ **sống** | áp thẳng vào `v_adj > best_val * bar` |
| tăng `p_move` 0,5 → 0,9 | ✅ **sống** | cổng cuối `rng.random() < p_move` |
| `give_up` bỏ hẳn phép so | ✅ **sống** | `behavior.py:224-227` chọn `max` theo niềm tin thô ⇒ **đi xuống dốc một bước** |

⇒ Hồ sơ cũ ghi *"bước sốt-ruột là NO-OP"* — **quá rộng**. Đúng phải là: **1 trong 4 hiệu ứng là no-op**
(cái nới vành). Ba cái kia hoạt động. Cách phát biểu cũ làm người đọc tưởng cơ chế chết hoàn toàn, và
sẽ dẫn tới một fix sai chỗ. Sửa vành mà không sửa **bán kính niềm tin** thì vẫn no-op — hai thứ phải đi
cùng nhau, đó mới là root cause.

⚠ Kèm theo: `D-SIM-K8` (`idle_streak_min` reset mỗi lần relocate) làm `give_up` chỉ đi **một bước** rồi
về lại chế độ kén. Tức khám phá bền vững **không** xảy ra. Chưa đo, mới đọc code.

---

## 6. ⭐ LỖI MỚI — 7 khoá gắn nhãn *"cổng một chiều canh"* mà **cổng đó không hề soi chúng**

Tìm ra khi tôi **phản biện chính đề xuất sửa của mình** ở mục 2 (*cổng mới có ồn không?*). Ba tầng:

| tầng | code | khoá |
| --- | --- | --- |
| **định tuyến** `parallel.py:420` | `_ONE_WAY_PREFIXES = ("veto_", "xveto_", "commit_")` — đẩy các khoá này **RA KHỎI** bảng significance hai chiều | `veto_*` · `xveto_*` · `commit_*` |
| **gộp** `parallel.py:557-564` | `keys = (...)` **chép cứng** — chỉ `veto_*` | ❌ **thiếu** `xveto_*`, `commit_*` |
| **cổng** `sim_metrics.py:535` | `for r in REST_RAILS` | ❌ **không lặp** `EXTEND_RAILS`, không đụng `commit_*` |

**ĐO THẬT** (không dừng ở đọc code — tiêm *"rail SỤP VỀ 0"* vào `health_guardrail_flags` cho **từng**
khoá, và đọc `keys` của `aggregate_health_guardrail` bằng `inspect`):

```
=> KHÔNG vào a_mean : 9 khoá  [commit_broken_n, commit_cleared_n, commit_kept_n, commit_made_n,
                               xveto_calls_n, xveto_fatigued_n, xveto_fired_n, xveto_soc_low_n,
                               xveto_would_exceed_fatigue_n]
=> CỔNG KHÔNG soi   : 11 khoá  (9 khoá trên + veto_calls_n + veto_fired_n)
```

⇒ **Hai con số, hai thứ khác nhau — phải nói tách ra:**

| đại lượng | số | khoá |
| --- | --- | --- |
| **vùng mù của CỔNG** (lan can + sổ cam kết mà cổng không soi) | **7** | `xveto_soc_low_n` · `xveto_fatigued_n` · `xveto_would_exceed_fatigue_n` · `commit_made_n` · `commit_kept_n` · `commit_broken_n` · `commit_cleared_n` |
| **vắng mặt khỏi `a_mean`** (bảng tổng tầng 5 không in ra) | **9** | 7 khoá trên **+** `xveto_calls_n` · `xveto_fired_n` |

Artifact vẫn in cạnh chúng `"one_way_gate": "sim_metrics.health_guardrail_flags (D-M3-05)"` — **một lời
khai quản trị KHÔNG có thật**.

⚠ **Hai khoá phụ có ý nghĩa riêng:** `xveto_calls_n` là **MẪU SỐ** của kênh kéo ca. Chính
`parallel.py:561-564` lập luận rằng *"MẪU SỐ phải hiện trong artifact"* — vì cùng một verdict OK có
nghĩa khác hẳn khi chấm trên 90/90 so với 9/90. ⇒ Việc `xveto_calls_n` vắng mặt **vi phạm đúng nguyên
tắc mà file đó tự phát biểu**, dù nó không thuộc vùng mù của cổng.

⚠ **Vì sao phải ĐO chứ không chỉ ĐỌC:** cổng cũng không soi `veto_calls_n`/`veto_fired_n` — nhưng đó là
**mẫu số** và **tổng**, cổng soi từng rail riêng, nên **không soi là ĐÚNG THIẾT KẾ**. Nếu chỉ đếm thô
"khoá cổng không soi" thì ra **11** và tôi đã báo thổi lên. Probe tái tạo được:
`c4b-do-vung-mu-tang-5.py` (+ `.json`).

**Đây là lỗi TÁI DIỄN.** `parallel.py:415-419` tự chép rằng danh sách tường minh *"đã HỞ hai lần"* —
đúng `xveto_*` và `commit_*` — và `_ONE_WAY_PREFIXES` sinh ra để chặn. Bản vá chặn đúng **chiều đi ra**
(khỏi bảng hai chiều) nhưng **không nối chiều đi vào** (tới cổng). Sửa xong nửa đường, nửa còn lại im lặng.

**Hậu quả — nói đúng mức:** `shift_extend` và `rest_window` đang **TẮT** (mục 3) ⇒ hôm nay 9 khoá đó đều
0 và **chưa che giấu gì**. Nó cắn **đúng lúc** ai đó bật hai kênh này lên để đo — tức **đúng việc đo lại
ở mục 1 sắp làm**. ⇒ Đây là **điều kiện tiên quyết** của mọi cycle đo kênh ngủ.

**Cách sửa (và vì sao không phải "nhớ cẩn thận hơn"):** danh sách khoá của `aggregate_health_guardrail`
và vòng lặp của `health_guardrail_flags` phải **suy ra từ CÙNG nguồn** với `_ONE_WAY_PREFIXES`, cộng một
test bất biến: *"mọi khoá định tuyến một chiều thì HOẶC được cổng soi, HOẶC được khai trơ tường minh có
lý do"*. Có test đó thì rail/ledger tương lai **không thể** lọt lần thứ ba.

---

## Cái tôi **chưa** kiểm (nói trước để không ai tưởng đã kiểm)

- `R-1` (kênh nghỉ **không có hàm mục tiêu**; 3/15 lượt hoãn đẩy nghỉ vào giờ **đông** hơn) — mới đọc
  `should_defer_rest`, **chưa** đo phân phối giờ đích.
- `D-ADV-06` (sổ pin solver ước cao 24%) — số 16,15 pp/giờ của tôi là **blended** cả hai đội
  (swap 1,6 và charge 0,85 pp/km), mà `soc_cost_per_bucket` lại **không phân biệt đội**. Phải tách đội
  rồi đo lại mới trích được.
- `A2` (hạ đội) vẫn **n=5** ⇒ biên đánh đổi của `UPDATE-176` §3(c) là **hướng**, không phải số chốt.
- **HHI cung theo ô** chưa đo lần nào (mới chỉ Gini payout) ⇒ **không được** nói *"equity tốt lên toàn diện"*.
