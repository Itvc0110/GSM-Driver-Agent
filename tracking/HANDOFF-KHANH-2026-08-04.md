# HANDOFF → KHÁNH (2026-08-04) — UI toàn phần + phản hồi về SIM

**Cường chốt 2026-08-04:** *"Khánh lo toàn bộ phần còn lại của UI (tôi chỉ làm hết cycle này)"*.
File này là **điểm vào cho agent của Khánh** — nó nói phần việc còn dở, và quan trọng hơn: **cái gì
đang HỎNG mà nhìn không ra**.

---

## §0. ĐOẠN PASTE CHO AGENT MỚI CỦA KHÁNH

```text
Bạn là AI coding agent làm việc trong repo GSM-Driver-Agent, dưới claim của KHÁNH.
Đọc theo ĐÚNG thứ tự, đừng đọc lại toàn bộ lịch sử:

1. CLAUDE.md                                   — harness bắt buộc, thắng mọi tài liệu khác
2. tracking/HANDOFF-KHANH-2026-08-04.md        — file này: việc còn dở + lỗ ĐANG SỐNG
3. tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md §6b — RANH GIỚI SẢN PHẨM,
                                                  đọc TRƯỚC KHI chạm advice_checkpoint/checkpoint/advice_v2.json
4. docs/reports/week2/AUDIT-CHECKLIST-cho-Khanh.md Phần 6 — 4 việc cần Khánh
5. tracking/PENDING-REVIEW.md                  — K-01 là mục CỦA BẠN, không phải của Cường
6. tracking/DEFERRED.md                        — D-QD4-01/02/03, D-M3-02, D-M3-18
7. git log --oneline -8 + git status

Ràng buộc KHÔNG được vi phạm (CLAUDE.md §5):
- Sức khoẻ tài xế KHÔNG phải biến để tối ưu — và KHÔNG đo mức nghe lời của khuyên sức khoẻ.
- Mọi số tài chính đến từ rule/analytics, agent chỉ diễn giải.
- Mock data phải gắn nhãn mock.
Ngôn ngữ: tiếng Việt.
```

---

## §1. 🔴 LỖ ĐANG SỐNG ở v2 — sửa trước, không phải "khi nào có thẻ mềm"

### 1.1 Flutter vẽ nút "Làm theo" VÔ ĐIỀU KIỆN

`ui/driver_app/lib/widgets/advice_checkpoint_card.dart:91-92`:
`onPressed: () => widget.onResponse('accepted')` — không đọc cờ mềm nào. Cộng với
`ui/contracts/advice_v2.json` khai `response_options` là **hằng**
`["accepted","dismissed","expanded"]`, không theo topic.

**Vì sao nó LIVE chứ không phải tương lai:** thẻ `rest` **sinh được hôm nay**. `shift_dp` (S2) trả
action `REST` khi chạm sàn nghỉ tối thiểu (`rest_min_per_4h`), rồi `_topic_for_action`
(`checkpoint.py:134`) route `code == "REST"` → topic `rest`. Backend nay trả **422** cho
`accepted` trên topic mềm ⇒ **tài xế bấm nút và ăn lỗi**.

> Backend chặn được **DỮ LIỆU**, không chặn được **CÂU HỎI**. Cái nút chính là câu hỏi.
> QĐ-1 nói *"UI không nên có trace đồng ý làm theo hay không"* — vế UI ở v2 **chưa** được thi hành.

**Cần làm:** envelope mang cờ `is_soft_advice` (v1 đã có ở `GET /advice/actions`), card chỉ vẽ nút
**Ẩn** khi cờ bật. Tham chiếu bản đã đúng: `ui/web/js/cards.js` chế độ `soft` + cổng
`ui/web/tests/cards_soft_gate.mjs` (node thuần, không cần jsdom/npm — chạy
`node ui/web/tests/cards_soft_gate.mjs`).

### 1.1b 🔧 ĐỀ XUẤT XỬ LÝ 422 — Cường giao phần này cho Khánh (app/UI)

Cường 2026-08-04: *"phải nghĩ ra cách để xử lý, đề xuất cách xử lý và docs lại để Khánh xử lý,
đây là phạm vi của app, UI"*.

**Nguyên tắc chọn giải pháp:** 422 của ranh giới khuyên mềm **không phải lỗi để hiển thị đẹp hơn** —
nó là dấu hiệu **client đã hỏi một câu không được phép hỏi**. Giải pháp đúng là **đừng để câu hỏi
xuất hiện**, không phải bắt lỗi cho êm.

| Tầng | Việc | Ghi chú |
| --- | --- | --- |
| **1. Chặn ở NGUỒN (chính)** | Envelope v2 mang cờ `is_soft_advice: bool` cho từng card; Flutter/web **chỉ vẽ nút Ẩn + Vì sao** khi cờ bật | Đây là phần 90% giá trị. v1 đã có đúng cờ này ở `GET /advice/actions` — copy hợp đồng, đừng phát minh lại |
| **2. Thu hẹp `response_options`** | `advice_v2.json` đang khai `response_options` là **hằng** `["accepted","dismissed","expanded"]`. Đổi thành **do server tính theo topic**: mềm → `["dismissed","expanded"]` | Client render nút **TỪ** `response_options` thay vì hard-code ⇒ ranh giới tự lan sang mọi client tương lai mà không ai phải nhớ |
| **3. Lan can cuối (vẫn cần)** | Nếu 422 vẫn xảy ra (client cũ, race, `curl`): **KHÔNG hiện message thô** cho tài xế | Message backend là tiếng Việt kỹ thuật có nhắc §1.2c — viết cho **dev**, không cho tài xế |
| **4. Hành vi khi dính 422** | Coi thẻ như đã **Ẩn**: đóng thẻ, **KHÔNG** gửi lại dưới dạng `accepted`, **KHÔNG** retry | Retry là sai bản chất: 422 ≠ 409, đây là *vĩnh viễn không được phép*, thử lại không bao giờ qua |
| **5. Quan sát được** | Log `advice_soft_boundary_rejected` kèm `topic` + `checkpoint_id` vào telemetry dev | Nếu con số này > 0 ở bản ship ⇒ tầng 1/2 đang hở, cần biết ngay chứ không im lặng |

**Vì sao không chọn "hiện toast xin lỗi":** nó biến một lỗi thiết kế thành trải nghiệm cho tài xế
chịu. Tài xế không làm gì sai — hệ thống mới là bên vẽ ra cái nút không nên có.

**Vì sao không chọn "nuốt im lặng":** tài xế bấm mà không có gì xảy ra là tệ nhất — họ sẽ bấm lại.
Nếu đã lọt tới tầng 4 thì phải **đóng thẻ** để cú bấm có kết quả nhìn thấy được.

⚠ **Ràng buộc khi làm tầng 2:** đổi `response_options` từ `const` sang tính-theo-topic là **đổi
contract**. Cổng `test_QD4_ghim_khoang_HO_giua_cac_tu_vung_topic` sẽ ĐỎ — đó là cố ý; sửa bảng ghim
trong test **có chủ ý** kèm ghi lý do, đừng sửa cho test xanh.

### 1.2 `K-01` — 3 test ĐỎ có sẵn trên `main`, tôi KHÔNG tự sửa

Đã chứng minh là đỏ sẵn (stash toàn bộ việc của tôi rồi chạy trên cây sạch `51e877e`):

| Test | Bản chất |
| --- | --- |
| `tests/test_cadence_policy.py::test_safety_topic_presents_even_while_driving` | **BẤT ĐỒNG CHÍNH SÁCH, không phải bug**: code + docstring cố ý QUEUE mọi thẻ chữ khi đang lái (kể cả safety); test đòi PRESENT. Đây là quyết định an toàn của bạn — tôi sửa là quyết hộ |
| `tests/test_checkpoint_trace.py::test_shadow_comparator_ignores_only_diagnostic_metadata` | hạ tầng import (`scripts/` thiếu `__init__.py`) |
| `tests/test_checkpoint_trace.py::test_run_once_wires_shadow_trace_without_changing_semantic_outcomes` | nt |

### 1.3 `D-M3-18` — 40/150 tài xế trong catalog là XE HƠI

Backend trả cờ `vehicle_range_km_applicable=false`, **Flutter chưa đọc cờ** ⇒ vẫn hiện số vô căn cứ.
⚠ KHÔNG trả `null` cho `vehicle_range_km`: `driver_state.dart:56` ép `as num` ⇒ app crash.

---

## §2. RANH GIỚI phải giữ khi chạm `topic` (QĐ-4)

Có **bốn cổng** sẽ ĐỎ nếu bạn thêm/đổi một topic v2. Chúng cố ý đỏ — comment thì đọc hay không tuỳ
người, cổng đỏ thì bắt buộc:

| Cổng | Bắn khi |
| --- | --- |
| `tests/test_advice_topic_registry.py::test_QD4_PRODUCER_...` | thêm nhánh `return "<topic mới>"` vào `_topic_for_action` |
| `…::test_QD4_ghim_khoang_HO_...` | enum `topic` của `advice_v2.json` thêm/bớt |
| `…::test_QD4_buoc2_RANH_GIOI_DA_KIN_...` | topic v2 không nằm trong registry |
| `…::test_QD4_ANH_XA_THAT_cua_producer_...` | `_topic_for_action` đổi ánh xạ mà nhãn không đổi theo |
| `ui/backend/tests/test_v2_soft_advice_no_trace.py` | ranh giới ở `record_response`/router bị gỡ |

**Hợp nhất là hợp nhất THẨM QUYỀN, không đổi tên.** `advice_v2.json` và mọi bản ghi giữ nguyên chuỗi.
Nguồn DUY NHẤT quyết định topic nào được đo: `src/gsm_core/lifecycle/advice_topics.py`.

⚠ **Kiểm DB v2 cũ trên máy bạn** (`data/ui-telemetry/advice_checkpoint.db`). Máy Cường **không có**
(kiểm 2026-08-04). Nếu bạn có, bản ghi tạo **trước 2026-08-04** có thể mang `accepted` trên topic
mềm — phải lọc trước khi ai đó tính bất kỳ tỷ lệ nào (`D-QD4-02`).

---

## §3. PHẢN HỒI VỀ SIM CỦA KHÁNH — cái gì MỚI, cái gì repo ĐÃ CÓ

Note của Khánh (`Feedback on sim`) chất lượng cao và **nhiều điểm trùng khớp với thứ repo đã tự đau**.
Bảng dưới tách ba nhóm để không ai làm lại việc đã làm, và không ai bỏ qua việc thật sự mới.

### 3.1 ĐÃ CÓ trong repo — đừng làm lại, hãy đọc ID

| Điểm của Khánh | Repo đã có gì | Ghi chú |
| --- | --- | --- |
| §7 **RNG drift**: cùng seed ≠ cùng realization | **`D-M3-02`** — `assert_crn` chỉ so danh sách đơn `(order_id, t_min, pickup_cell, gross_vnd)`, mà đơn sinh NGOÀI world ⇒ trả `True` dù mọi quỹ đạo actor đã lệch. `world.py:79` dùng MỘT stream `self.rng` chung; `behavior.py:151,157` tiêu draw có short-circuit sau phép so `fatigue` ⇒ đổi định nghĩa liều = **dịch dòng** RNG của cả 90 actor | Khánh **đúng và đi xa hơn**: đề xuất giải pháp (keyed RNG / event tape) mà `D-M3-02` mới chỉ đề xuất *phát hiện* (`fingerprint_actors`) |
| §3 `accepted` ≠ `followed` | **`D-R22`** — `followed` ở sản phẩm là **cú bấm tự khai**, ở sim là **đổi hành vi thật** (chỉ log khi `mapped_action != bản năng`). Cùng tên, cùng field, cùng projection, hai nghĩa | Khánh thêm **chiều thứ ba** (`execution`) — xem 3.2 |
| §6 path dependence một phần | `src/gsm_sim/multiday.py` §"Ranh giới reset / mang sang" — khớp gần như từng dòng với note | Xác nhận độc lập, tốt |
| §11.1 `AdviceEpisode` | **CÓ MỘT PHẦN**: `src/gsm_core/advisor/episode_store.py` + `advice_spec` | Thiếu `state_before`/`state_after`/`next solver input` — xem 3.2 |
| §13 tách metric | `specs/adherence-measurement.md` §(c) đã tách decision vs event adherence; **ĐÍNH CHÍNH 2026-07-30** ghi rõ hai đường **KHÔNG join được** | Khánh tách mịn hơn (8 loại) — hữu ích |
| §5 re-plan là polling tại idle | **XÁC NHẬN** bằng code: `world.py:360` `if a.state != ActorState.IDLE or not self.advice.covers(a): …` | Mô tả của Khánh chính xác |
| §10 chưa model delayed/partial adherence | `D-SIM-*`/`D-M3-19` — và **quan trọng**: `rest_nudge` (gợi ý nghỉ) **không có producer nào** trong repo | |

### 3.2 MỚI và ĐÁNG LÀM — đề xuất thành TODO

| ID đề xuất | Việc | Vì sao đáng |
| --- | --- | --- |
| **`D-SIM-K1`** | **Tách `execution` khỏi `followed`** — metric riêng: accept rate · simulated adherence · execution rate · *accepted nhưng không execute* · *không accepted nhưng vẫn execute* | Repo hiện có HAI nghĩa của `followed` (`D-R22`) và Khánh chỉ ra còn **chiều thứ ba**. Đây là điều kiện để `execution_link` thôi mang tính tương quan |
| **`D-SIM-K2`** | **`caused` vs `consistent_with` vs `deviated_from`** + upper bound của action window; một segment không link nhầm nhiều checkpoint | §9 của note: link hiện chỉ là `coincident` — *"một hành động phù hợp xảy ra sau lời khuyên"* ≠ *"lời khuyên gây ra hành động đó"*. Không có phân loại này thì mọi claim causal đều lỏng |
| **`D-SIM-K3`** 🔴 | **Keyed RNG (`seed + actor_id + purpose + event_id`) hoặc exogenous event tape** | **Giải pháp cho `D-M3-02`.** Đây là mục có đòn bẩy cao nhất trong cả note: nếu RNG drift không khoá được thì **mọi Δ trong repo đều lẫn 4 thành phần** (hệ quả thật · random-stream divergence · solver feedback · policy/adherence divergence) |
| **`D-SIM-K4`** | **Short-horizon evaluation** — đo từ checkpoint tới lần solve kế / hết action window / actor về cùng loại decision point | Khánh nói đúng: bước này phải **TRƯỚC** 90-day. Nó cũng là thứ biến `D-M3-04` từ "đo policy effect" thành "đo được lời khuyên nghỉ làm gì" |
| **`D-SIM-K5`** | **Forced paired branch** (cùng state tại checkpoint → forced FOLLOW / forced IGNORE), **chỉ trong evaluator**, không đưa `forced` vào production actor | Đây là thứ `run_pair()` **không** làm: nó chạy hai full-run advice-on/off, nên đo được *policy effect*, không đo được *causal effect của một checkpoint* |

### 3.3 Điểm cần THẬN TRỌNG — không nhận nguyên văn

- **§15 *"Không dùng full-run difference để claim causal effect từng advice"*** — đúng, và repo
  **đang** ở trạng thái đó. Nhưng `D-M3-04` (prereg đã KHOÁ) đo **policy effect** của kênh
  `rest_window`, **không** claim causal của một checkpoint ⇒ note này **không** làm `D-M3-04` sai.
  Cái nó CÓ chạm: `D-SIM-K3` (RNG drift) ảnh hưởng **độ chắc** của mọi Δ, gồm cả `D-M3-04`.
- **§11.3 "khoá randomness"** đụng vào `world.py`/`behavior.py` — đổi RNG stream sẽ **đổi mọi số đã
  đo**. Phải có prereg + đo lại, không sửa lẻ. Đây là cycle riêng, không phải một PR.
- **§14 câu 5 "có carry SOC/vị trí/fatigue qua ngày không?"** — hiện **KHÔNG** carry ba thứ đó
  (`multiday.py` reset). Đổi là đổi bản chất mô hình; phải hỏi Cường, không tự quyết.

---

## §4. STATE TRONG SIM — trả lời câu Cường hỏi, để agent sau không hiểu sai

**Có HAI thế giới, và chúng KHÔNG chạm nhau:**

| | Mock data (SẢN PHẨM) | Simulator |
| --- | --- | --- |
| Ở đâu | `data/mock/realdata-v1/*.parquet` (13 bảng GSM) | `src/gsm_sim/` — sinh trong RAM |
| Quy mô | **150 tài xế × 90 ngày** (2026-07-01 → 2026-09-28) | **90 actor** (`configs/pilot_dongda.yaml` → `actors.n: 90`), số ngày là tham số |
| Sinh bởi | `scripts/regen_mock.py --days 90` — **ghi MỘT LẦN**, sau đó chỉ đọc | `configs/*.yaml` + `seed` — sinh mới mỗi lần chạy |
| Ai đọc | `ui/backend` → L1R view → solver S1/S2 | không đọc `data/mock/` chút nào; chỉ đọc **file địa lý** (`world.data_dir`: geom/stations/POI/ma trận OSRM) |

⇒ *"90 ngày"* và *"90 tài xế"* là **hai con số khác nhau của hai hệ khác nhau**, trùng số 90 do
tình cờ.

**Sim KHÔNG ghi vào database nào.** Grep toàn `src/gsm_sim/`: 0 lần `sqlite3`/`commit`. Chỉ ghi
**artifact** parquet của một lần chạy (`logging_ev.py` → `events.parquet` + `actors.parquet` trong
thư mục run), và tắt được bằng `--no-write`. Quyết định ĐA-05 của Cường: *"sim để RAM, KHÔNG ghi đè
bảng"*.

**"State" gồm những gì** (`src/gsm_sim/entities.py::Actor` — 40+ trường, chia BA lớp):

| Lớp | Trường | Đổi khi nào |
| --- | --- | --- |
| **DANH TÍNH** (là con người, không phải trạng thái) | `actor_id` · `archetype` (P1–P7) · `fleet` (đội đổi pin / sạc) · `home_cell` · `accept_base` · `demand_prior_sigma` · `fatigue_threshold_min` · `meal_hour` | **KHÔNG BAO GIỜ** đổi. `reset_for_new_day` khai tường minh là không đụng |
| **VẬT LÝ / VỊ TRÍ** | `state` (OFFLINE/IDLE/ENROUTE/ON_TRIP/…) · `cell` · `lat`/`lon` · `soc_pct` · `enroute_cell` | Mỗi **step** của SimPy |
| **TÍCH LUỸ TRONG NGÀY** | `points` · `payout_vnd`/`gross_vnd` · `trips_done` · `orders_offered/accepted/completed/cancelled` · `online_min`/`idle_min`/`rest_min`/`charge_min`/`empty_min`/`occupied_min` · `km_driven`/`cost_vnd` · `idle_streak_min` · `idle_by_hour` · `accept_lift` · `rest_deferred_min` · `shift_extended_min` · `ratings_*` · `mission_progress` | Cộng dồn trong ngày, **reset sáng hôm sau** |

⇒ **CÓ, hồ sơ tài xế nằm trong state** — nhưng ở lớp DANH TÍNH, và nó **bất biến**. `tenure_days` là
ngoại lệ duy nhất: +1 mỗi sáng (*"thời gian trôi là danh tính động duy nhất"*).

**Solver nhận input gì** — không phải cả `Actor`, mà một **lát cắt** do `advice_bridge` dựng. Đếm
thật (số lần đọc): `actor_id` 23× · `shift_end_min` 9× · `points` 8× · `online_min` 6× ·
`shift_extended_min` 5× · `acceptance_rate` 5× · `accept_lift` 5× · `rest_deferred_min` 3× ·
`shift_start_min` 3× · `orders_accepted`/`completion_rate`/`planned_rest_hour`/`soc_pct`/
`orders_offered` 2× · `fatigue_threshold_min`/`fleet`/`archetype`/`accept_base`/`idle_by_hour`/
`rest_min` 1×.

⚠ Ba điều đáng chú ý trong danh sách đó:
- `fatigue_threshold_min` được đọc **đúng 1 lần** — ở `should_defer_rest` (lan can nghỉ). **Không**
  chỗ nào khác, kể cả `check_shift_extend` ⇒ đó chính là `D-QD4-03`.
- `archetype`/`fleet`/`accept_base` (danh tính) **có** vào solver ⇒ lời khuyên cá nhân hoá theo hồ
  sơ, không phải một luật chung.
- Không có trường nào về **lịch sử nghe lời** — Khánh §2 nói đúng: solver không biết xác suất tài xế
  làm theo. Đó là **có chủ ý** ở giai đoạn này.

**Cập nhật bằng cách nào:** không có "database step". `Actor` là một `@dataclass` **mutable trong
RAM**; các process SimPy ghi thẳng vào trường (`consume_soc` là chốt chặn DUY NHẤT của mọi km/pin).
Solver **đọc** lát cắt tại decision point khi actor IDLE (`world.py:360`
`if a.state != ActorState.IDLE …`) — **không** phải mỗi lần state đổi. Đó đúng là điều Khánh §5 nói:
*re-planning tại decision point khi actor idle*, không phải event-driven.

**State đi qua ngày thế nào** (`multiday.py`):

| RESET mỗi ngày (`Actor.reset_for_new_day()`) | MANG SANG (`DriverMemory`) |
| --- | --- |
| điểm · mọi counter · payout · SOC · mệt · cờ bữa ăn · `accept_lift` · vị trí · shift extension · idle streak | **danh tính** tài xế · lịch sử cuộn (acceptance/completion/points-per-hour) · `planned_rest_hour` · tổng tuần · newbie status |

⚠ Hai bẫy đã ghi trong chính file đó: (1) `DriverMemory` chỉ được cập nhật **SAU** khi ngày chạy
xong — ngày N chỉ đọc dữ liệu ngày ≤ N (chống rò rỉ tương lai); (2) tổng tuần **không bao giờ reset**
⇒ chỉ đúng khi `days ≤ 7`, chạy dài hơn là "tuần" phình vô hạn.

**Khi actor nghe lời ở thế giới song song:** `run_pair` chạy **hai full-run độc lập**, mỗi run có
tập `Actor` riêng trong RAM. Không có chuyện "cập nhật ngược" vào dữ liệu nào. Đó cũng chính là chỗ
`D-SIM-K3` quan trọng: hai run **cùng seed** nhưng một khi hành vi lệch, chúng **tiêu thụ random
theo thứ tự khác nhau** ⇒ Δ cuối cùng lẫn cả hệ quả thật lẫn nhiễu ngẫu nhiên.

---

## §5. Bẫy vận hành (đã trả giá thật)

1. **"Suite xanh" = HAI lệnh**: `uv run pytest -q` **và** `uv run pytest -q ui/backend/tests`.
   `pyproject.toml` có `testpaths = ["tests"]` nên lệnh trần **bỏ** cây `ui/backend` (`D-M3-09`).
2. **Chỉ khởi động suite khi ĐÃ NGỪNG sửa file nó thu** — pytest import lúc collection. Đã sập bẫy
   này hai lần, lần gần nhất mất ~25′ máy.
3. **Đừng đếm số bằng ký ức** — đếm bằng lệnh. Số UPDATE đã sai hai lần vì đoán.
4. **`read_text()` không khai encoding** dùng cp1252 trên Windows ⇒ nổ ngay khi file có tiếng Việt.
   Luôn `read_text(encoding="utf-8")`.
5. **Cổng nào không tự chứng minh bắn được thì là cổng trang trí** — sever-restore đủ bốn bước:
   tiêm vào file nguồn thật · chạy pytest thật · restore · verify `sha256`.
