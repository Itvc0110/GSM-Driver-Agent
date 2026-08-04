# Spec — Đo "tài xế có làm theo advice không" bằng HAI đường song song (BACKLOG Q6)

Ngày: 2026-07-27 · Trạng thái: spec v0 — **một phần DONE-CODE** (Cycle W UPDATE-091; `D-M3-01` +
`D-M3-10` UPDATE-102).
🔴 **Đọc ĐÍNH CHÍNH 2026-07-30 ngay dưới §Nguyên tắc TRƯỚC khi dùng file này** — nó đảo một kết luận
của spec (*"thiếu hiển thị"* → **thiếu khả năng đối chiếu**). Và đọc **BỔ SUNG 2026-08-03** (ngay
trước §Đường 1): có một lớp lời khuyên — **khuyên mềm** — mà câu trả lời đúng là **không đo**, không
phải đo cho đúng. Xem cả đính chính 2026-07-29 — trả lời câu hỏi Cường *"how are we tracking if the driver follow
instructions, are there multiple ways done in same time?"*. Implement từng phần đã/sẽ theo cycle
riêng; file này là bản đồ chung.

## Nguyên tắc

Một đường đo đơn lẻ nói dối: nút bấm đo Ý ĐỊNH (dễ bấm cho xong), hành vi đo THỰC TẾ (nhưng
nhiễu — hành vi đổi có thể không do advice). Phải chạy CẢ HAI và đối chiếu; lệch giữa hai đường
chính là tín hiệu quý (nói-một-đằng-làm-một-nẻo).

> ## 🔴 ĐÍNH CHÍNH 2026-07-30 (`D-M3-01` + `D-M3-10`, UPDATE-102) — nguyên tắc trên ĐÚNG nhưng THIẾU
>
> Spec này giả định hai đường đều **hợp lệ nhưng khác nhau**, và việc còn lại chỉ là *đối chiếu*.
> Thực tế đo được: **đường IMPLICIT tự nó có mẫu số HỎNG**, và **hai đường hiện KHÔNG JOIN ĐƯỢC**.
> Đó là hai vấn đề khác hẳn "hai đường lệch nhau" — và cả hai đã sống nhiều tháng mà không ai thấy.
>
> ### (a) Đường IMPLICIT: mẫu số thiếu ⇒ adherence = 1,0 **theo cấu trúc**
>
> Với `shift_extend` và `rest_window`, event **chỉ được ghi khi tài xế ĐÃ THEO** ⇒ tử số = mẫu số ⇒
> `decision_adherence` **không thể khác 1,0**. Đo được: báo **1,000** trong khi sự thật (đo từ coin,
> độc lập với event log) là **0,473** ⇒ **thổi 2,1×**, và số đó đã sống trong **39 artifact**.
>
> ⚠ Đơn vị: **2,1×** là theo đơn vị QUYẾT ĐỊNH. Con số 0,311 hay "3,2×" mà một bản đính chính trước
> đã báo là theo đơn vị **LẦN HỎI** — trộn hai đơn vị là chính lỗi mà bản đính chính đó mắc lại.
>
> **Đã sửa** (3 tầng, `advice_bridge` + `world` + `projections`): `shift_extend` nay báo **0,475** vs
> sự thật **0,473**. Kèm nhánh mà spec cũ không lường: *"tài xế ĐỒNG Ý nhưng thế giới không thi hành
> được"* (kéo ca vượt `time.end_min`) cũng phải log — nó thuộc **cả tử số lẫn mẫu số**.
>
> ### (b) Vì sao không ai thấy: cổng hợp lệ chỉ tồn tại trên giấy
>
> Luật *"mọi arm phải báo `decision_adherence` per archetype so danh nghĩa; lệch ⇒ TREO"* **chưa từng
> được thi hành**: `parallel.py` / `sim_metrics.py` / `run_parallel.py` tham chiếu
> `adherence`/`followed`/`decided` **ĐÚNG 0 LẦN**; artifact **35–39 không có khoá `adherence` nào**.
> ⇒ **Đã nối** (`D-M3-10`): `adherence_audit()` theo (kênh × archetype) · cổng **BẤT KHẢ** ·
> `PairResult` mang adherence **cả hai arm** · `run_ladder` ghi `verdict` TREO/OK.
>
> ### (c) 🔴 HAI ĐƯỜNG KHÔNG JOIN ĐƯỢC — đây là chỗ spec cũ sai nhiều nhất
>
> §Phần THIẾU #2 dưới đây viết *"còn thiếu **hiển thị** view này ở khu Mô phỏng"*. **Không phải thiếu
> hiển thị — thiếu khả năng đối chiếu.** Bốn lý do cấu trúc, mỗi cái tự nó đủ chặn:
>
> | # | Vấn đề | Hệ quả |
> | --- | --- | --- |
> | 1 | Sản phẩm ghi `event_type = "displayed"`, **không bao giờ** ghi `decided`; `adherence_view` chỉ đếm `event_decided` khi `et in ("decided","followed")` | **`event_adherence` ở sản phẩm VĨNH VIỄN `None`** — một nửa bộ đo hai-tên chết im lặng ở đúng nơi có tài xế thật |
> | 2 | Không gian `topic` **rời nhau hoàn toàn**: sản phẩm `{brief, nudge, recap}` + default `bonus`; sim `{shift_plan, positioning, accept_lift, shift_extend, rest_window}`. `adherence_view` khoá theo `(run_id, driver_id, topic)` | **Không có một khoá nào so được** giữa hai đường |
> | 3 | `followed` ở sản phẩm là **CÚ BẤM TỰ KHAI**; `followed` ở sim là **ĐỔI HÀNH VI THẬT** (chỉ log khi `mapped_action != hành động bản năng`) | **Cùng tên, cùng field, cùng projection — hai nghĩa khác nhau.** Đối chiếu hai cột này là so ý định với hành vi rồi gọi kết quả là "lệch" |
> | 4 | Sản phẩm ship **1/5 kênh** (S1 bonus-gap); kênh giá trị nhất của sim (`positioning`) bị **D-004 CẤM** ở sản phẩm | Tập kênh của hai đường **không giao nhau** |
>
> ⇒ **Việc phải làm KHÔNG phải "thêm một view"** mà là **thống nhất taxonomy `topic` và ngữ nghĩa
> `followed` trước đã**. Chi tiết + 13 finding sev CAO khác của đường sản phẩm:
> `tracking/SOI-2026-07-30-mau-so-adherence.md` §1/§4. ⚠ **Chưa cái nào qua phản biện đối kháng**
> (16/16 agent phản biện fail vì session limit, hai lần) — nhưng bốn mục trong bảng trên tôi **tự
> kiểm bằng đọc code**.
>
> ### (d) Bài học đổi cách viết spec này
>
> Nguyên tắc mở đầu vẫn đúng, nhưng phải thêm một tầng **TRƯỚC** nó:
> **mỗi đường đo phải tự chứng minh mẫu số của nó tồn tại, TRƯỚC khi hai đường được đối chiếu.**
> Cổng bắt buộc cho mọi đường đo mới:
> 1. adherence tính ra được có thể **khác 1,0 và khác 0,0** không? (nếu không ⇒ mẫu số hỏng)
> 2. có tồn tại một **ground truth ĐỘC LẬP** để pin nó vào không? (sim: coin. Sản phẩm: **chưa có**)
> 3. cổng nghiệm thu có **chứng minh được là ĐỎ ĐƯỢC** không? (test tautology của `F-1` sống 39
>    artifact vì không ai đòi điều này)

> ## 🚫 BỔ SUNG 2026-08-03 — có một lớp lời khuyên KHÔNG ĐƯỢC ĐO chút nào
>
> Quyết định Cường 2026-08-03 (`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`): *"trong UI
> cũng không nên có trace đồng ý làm theo hay không làm theo khi gợi ý — tương tự đối với thời tiết"*.
>
> Cả spec này và bốn đính chính trên đều mặc định **mọi** lời khuyên đều nên đo được, và vấn đề duy
> nhất là đo cho đúng. Bổ sung này nói: với **KHUYÊN MỀM** (thời tiết · `rest_nudge` gợi ý nghỉ ·
> giao thông), câu trả lời đúng là **không đo**, và đó không phải nợ kỹ thuật.
>
> **Lý do:** đo *mức nghe lời* của lời khuyên sức khoẻ chính là biến sức khoẻ thành chỉ tiêu để tối
> ưu. Một khi `rest_adherence` tồn tại như một con số trong bảng, nó sẽ bị nhìn như thứ cần cải thiện
> — và *"cải thiện tỷ lệ tài xế chịu nghỉ"* là tối ưu hoá **trên** sức khoẻ, trái
> `advisor-objective-model-v2.md` §1.2b. Đây là **tầng thứ ba** của cùng tỷ giá mà §1.2b đã bịt ở
> tầng objective (`C2` huỷ) và tầng world (không mô hình hoá hậu quả mệt) — xem §1.2c mới của spec đó.
>
> | | Khuyên mềm |
> | --- | --- |
> | `decision_adherence` / `event_adherence` | 🚫 **KHÔNG TỒN TẠI** — topic mềm **vắng khoá** khỏi `adherence_view` |
> | `followed` | 🚫 **422 tại boundary** (`POST /advice/action`) |
> | `dismissed` | ✅ **CÓ** — nhưng chỉ mang nghĩa *"đừng nhắc nữa trong pha này"* (nhịp nói ĐA-04), **không** nghĩa *"tài xế không đồng ý"* |
> | Nút UI | **Ẩn** + *Vì sao*. **Không** có "Làm theo" (`cards.js` chế độ `soft`) |
>
> ⚠ **Đây là chỗ dễ đọc sai nhất của bổ sung này:** *vắng khoá* ≠ `None`. Đính chính (a)/(d) ở trên
> dạy rằng mẫu số 0 ⇒ `None` là **tín hiệu thước hỏng** — nếu khuyên mềm cũng trả `None` thì nó lẫn
> vào đúng tín hiệu báo lỗi, và người sau sẽ đi "sửa" một ranh giới đang chạy đúng. Nên topic mềm
> phải **không xuất hiện** trong view.
>
> **Đã thi hành bằng máy** (UPDATE-135, sever-restore 4/4 mũi bắn): registry
> `src/gsm_core/lifecycle/advice_topics.py` · lọc ở **CẢ HAI** vòng của `adherence_view` (lọc một
> vòng để hở vòng kia là đúng họ lỗi (c)#1) · cổng **fail-closed** `tests/test_advice_topic_registry.py`
> — topic chưa phân loại ⇒ ĐỎ, không im lặng rơi vào bảng đo.
>
> ⚠ **`rest_window` KHÔNG nằm trong nhóm này (hiện tại).** Nó là HOÃN nghỉ = đổi *thời điểm* = `C2′`,
> một kênh kinh tế. Cường chọn *"thử `D-M3-04` trước, nếu có ý nghĩa thì giữ, không thì revert và
> khuyên mềm"*; luật quyết định đã đăng ký **trước khi đo** ở
> `specs/simulation/d-m3-04-multiday-prereg-locked.json` → `luat_quyet_dinh`. Cái thuộc nhóm mềm là
> `rest_nudge` (GỢI Ý nghỉ khi quá sức) — một kênh **khác**, chưa implement.
>
> **Hệ quả cho đính chính (c)#2** (*"không gian `topic` rời nhau"*): taxonomy nay có **hai lớp**, và
> việc thống nhất `topic` giữa sim và sản phẩm phải tôn trọng lớp — không được gộp một topic mềm vào
> một topic được đo để "cho join được".

> ## 🔴 BỔ SUNG 2026-08-04 — (c)#2 nay có LÝ DO THỨ HAI, và nó nặng hơn lý do đầu
>
> §(c)#2 nêu việc thống nhất `topic` là **điều kiện để hai đường đo JOIN được** — một lý do về **phép
> đo**. Sau khi rebase PR #4 (AdviceCheckpoint v2) thì lộ ra lý do thứ hai, thuộc về **ranh giới đạo
> đức**:
>
> **Một ranh giới không thể phủ hai từ vựng rời nhau.**
>
> Nay có **BA** không gian `topic` cho cùng một khái niệm:
>
> | Nguồn | Từ vựng |
> | --- | --- |
> | sản phẩm v1 | `brief · nudge · recap` (+ `bonus` lịch sử) |
> | registry / sim / pipeline | `positioning · shift_plan · accept_lift · shift_extend · rest_window · online` + **mềm**: `weather · rest_nudge · traffic` |
> | **AdviceCheckpoint v2** | `bonus_eligibility · energy · **rest** · shift_boundary · shift_timing · positioning_sim_only · policy_info · **safety_reserved**` |
>
> Cột ba **giao với hai cột kia = RỖNG**. Nên ranh giới *"khuyên mềm không đo"* — enforce bằng
> `classify()` trên registry — **không chạm được** một event nào của v2. Đo được: một checkpoint
> `rest` (sinh bởi S7) nhận `response: accepted`, tức **trace đồng ý cho lời khuyên nghỉ đang được
> ghi**. Chưa sinh số sai (store v2 riêng, `adherence_view` không thấy), nhưng dữ liệu **tích luỹ**.
>
> ⇒ **Cường chốt 2026-08-04: hợp nhất (phương án (b))**, không chọn cách rẻ hơn là ánh xạ-rồi-chặn —
> vì ánh xạ để lại hai từ vựng, tức để nguyên nguồn gốc của lỗ. Chi tiết + thứ tự thi công:
> `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b.
>
> ⚠ Ràng buộc mới cho việc hợp nhất, ngoài ràng buộc "tôn trọng lớp" ở trên: **`rest` và
> `safety_reserved` của v2 thuộc lớp MỀM**. Gộp chúng vào một topic được đo để "cho join được" là
> đúng cái sai mà đoạn trên vừa cấm — và lần này hậu quả không phải một con số lệch mà là một thước
> nghe-lời cho lời khuyên sức khoẻ.
>
> ### ✅ Trạng thái 2026-08-04 (UPDATE-137) — đọc trước khi lập kế hoạch join
>
> Bảng ba cột ở trên là **ảnh chụp lúc phát hiện**; thực tế còn **từ vựng thứ TƯ** —
> `cadence.SAFETY_TOPICS = {"safety"}`, cùng khái niệm với `safety_reserved` nhưng khác tên, ở khác
> file. Cả bốn nay **đã nhập registry**: mỗi topic có đúng MỘT nơi quyết định nó được đo hay không.
>
> **Nhưng đó là hợp nhất THẨM QUYỀN, không phải hợp nhất TÊN.** Các chuỗi giữ nguyên, và **hai đường
> đo vẫn CHƯA join được** — §(c)#2 vẫn mở, cùng với ĐÍNH CHÍNH 2026-07-30 và `D-R22` (adherence sản
> phẩm = *cú bấm tự khai*; adherence sim = *đổi hành vi thật* — cùng tên, cùng field, khác nghĩa).
>
> ⇒ Ai định làm bước join: mở `D-QD4-02` trong `DEFERRED.md` trước. Nó ghi hai điều kiện bắt buộc,
> trong đó có việc **kiểm DB v2 cũ** — bản ghi tạo trước 2026-08-04 có thể mang `accepted` trên topic
> mềm, và một phép join tin rằng store sạch sẽ hồi sinh đúng con số mà ranh giới này cấm.

## Đường 1 — EXPLICIT (ý định, UI) — ✅ ĐÃ CÓ từ UPDATE-067

- Nút **Làm theo / Bỏ qua / Vì sao** trên mỗi card → POST `advice_action` (contract v1.0),
  log jsonl local nhãn mock; đọc lại ở Cài đặt.
- Đơn vị phân tích: (driver, date, advice_id, card_kind, action).
- Giới hạn đã ghi: đo Ý ĐỊNH; không có side-effect (tài xế luôn tự quyết — CLAUDE §5).

> **⚠ Đính chính 2026-07-29 (Cycle W, UPDATE-091):** đường ghi canonical nay là **`AdviceEventLog`**
> (`gsm_core/lifecycle/event_log.py`, append-only, idempotent theo `event_id`) — JSONL local ở trên
> chỉ còn vai trò **debug**, không phải nguồn sự thật. Đơn vị phân tích đổi thành
> **`(driver, run_id, decision_id, …)`** — `decision_id` có 3 namespace, `Event.run_id` deterministic
> kèm config digest. UI POST/GET action nay đi qua store canonical.

## Đường 2 — IMPLICIT (hành vi, sim/A-B) — ✅ NỀN ĐÃ CÓ, thiếu phần ĐỐI CHIẾU

- Sim: coin adherence theo archetype (D-SIM-04 ASSUMPTION) + event `advice_given/followed`
  (world.py) + **thế giới song song CRN** đo hiệu ứng nhân-quả sạch (Δ payout theo cặp seed).
  **⚠ 2026-07-30:** coin là **ground truth ĐỘC LẬP với event log** — đó là thứ duy nhất phát hiện được
  mẫu số hỏng (xem đính chính (a)). Mọi kênh nay đều rút coin; `rest_window` là kênh cuối cùng được
  nối (`D-M3-01`). Adherence THẬT đo được theo đơn vị QUYẾT ĐỊNH: `shift_plan` 0,534 · `accept_lift`
  0,565 · `positioning` 0,500 · `shift_extend` 0,473 · `rest_window` **kênh chưa nói lần nào**
  (`D-M3-04`: bậc thang của nó **bit-identical với `s2_only`** trên 5 seed).
- Data thật (tương lai): so hành vi cửa-sổ-sau-advice vs baseline cá nhân (vd: advice "nâng tỷ
  lệ nhận" lúc 14h → acceptance realized 14h-18h vs cùng khung các ngày không-advice).
  **Chặn bởi**: bảng GSM không có accept/decline event (chỉ daily aggregate — F-U2-A/EST-6);
  cần nguồn event-level hoặc chấp nhận granularity ngày.

## Phần THIẾU — việc cho cycle sau (ưu tiên theo thứ tự)

1. **Join key hai đường**: `advice_id` hiện chỉ sống ở UI; sim events không mang advice_id tương
   thích. Chuẩn hoá: advice_id = hash(driver, date, solver, reason_code, at_min-bucket) sinh Ở
   BACKEND — cả card lẫn (sau này) sim bridge dùng chung → join được explicit ↔ implicit.
   **⚠ DONE Cycle W (UPDATE-091):** đã có `decision_id` 3 namespace + `Event.run_id` deterministic
   trong `gsm_core/lifecycle/` — join key hai đường nay tồn tại ở backend, không còn chỉ-UI.
2. **Bảng đối chiếu**: view (driver, tuần) → tỷ lệ bấm-Làm-theo vs Δ hành vi đo được vs adherence
   coin sim — 3 cột cạnh nhau, lệch = flag. Chỗ hiển thị: khu Mô phỏng (reviewer), KHÔNG áp
   lực lên tài xế. ~~**⚠ Cập nhật 2026-07-29:** một nửa đã có … còn thiếu **hiển thị**.~~
   🔴 **ĐÍNH CHÍNH 2026-07-30: KHÔNG phải thiếu hiển thị — thiếu khả năng ĐỐI CHIẾU.** Bốn chặn cấu
   trúc ở đính chính (c). Việc thật phải làm, theo thứ tự:
   **(2a)** thống nhất taxonomy `topic` giữa sim và sản phẩm;
   **(2b)** sản phẩm phải emit `decided` (nay chỉ có `displayed`) ⇒ `event_adherence` mới tồn tại;
   **(2c)** tách tên: `followed_selfreport` (bấm nút) vs `followed_behavior` (đổi hành vi thật) —
   dùng chung một field cho hai nghĩa là mời người đọc so ý định với hành vi rồi gọi là "lệch";
   **(2d)** CHỈ khi đó mới dựng view 3 cột.
   ✅ Phần đã xong 2026-07-30: `adherence_view` có hai tên, **và** adherence nay được ghi vào mọi
   artifact A/B kèm `verdict` TREO/OK (`D-M3-10`) — trước đó không artifact nào mang nó.
3. **Cập nhật D-SIM-04**: khi có log explicit đủ dày (dù là mock/demo), dùng phân phối bấm-nút
   làm prior MỚI cho adherence coin thay ASSUMPTION thuần (vẫn nhãn rõ nguồn).
4. **Ethics guard** (bài học nudge Uber): KHÔNG dùng số đo adherence để tăng áp lực nudge
   (không "bạn đã bỏ qua 3 lần!"); chỉ dùng để ĐO chất lượng advice và tôn trọng im lặng
   (bỏ qua nhiều lần một LOẠI advice → advisor giảm loại đó — memory design, xem A3 MEMSTATE).

## Liên kết

`ui/contracts/advice_action.json` · UPDATE-067 · D-SIM-04 · D-SIM-14 (RNG coin theo khoá) ·
BACKLOG Q6/R2 · `research/ux/2026-07-27-decision-trace-design-note.md`.
