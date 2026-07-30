> ## ⚠ ĐỌC TRƯỚC — spec này TỰ LẬT ƯU TIÊN CỦA CHÍNH NÓ (agent chính xác nhận 2026-07-29)
>
> Spec do 7 agent sinh ra để thi công **E1** (`D-ĐA04-03`), mục tôi đã gọi là *"giá trị cao nhất
> còn lại của ĐA-04"*. **Câu đó nay SAI, và chính spec này chứng minh** — §0.1 của nó tự mở
> artifact 38 và phát hiện cái nó gọi là **NULL-0**.
>
> **Lập luận (tôi đã tự kiểm lại từ `38-e5-2x2-perseed-n100.json`):**
>
> | Sự thật | Số | |
> | --- | --- | --- |
> | Tương tác ngân sách FIFO — toàn bộ "giải thưởng" mà một trọng tài khéo hơn có thể giành | +2.207đ | SIG |
> | Bỏ `shift_plan` khi nhịp BẬT — **một dòng YAML của ĐA-07 đã lấy** | +2.259đ | SIG |
> | **Giá của nhịp ở CẤU HÌNH SẢN PHẨM** (nhịp ON, `shift_plan` OFF) | **−259đ** | **ns** |
>
> Dòng thứ ba là dòng quyết định: **ở đúng cấu hình sản phẩm đang chạy, ngân sách chú ý hiện
> tại không tốn khoản tiền nào đo được.** Một trọng tài khéo hơn nhiều nhất chỉ giành lại được
> chi phí của trọng tài hiện tại — mà chi phí đó là **0 (ns)**. ⇒ **E1 như đặc tả ở đây có
> headroom ≈ 0đ ở cấu hình hiện tại.** ĐA-07 đã ăn xong giải thưởng bằng một dòng config.
>
> **Vì vậy spec này ở trạng thái `DEFERRED-CÓ-ĐIỀU-KIỆN`** (`D-M3-07`). Nó chỉ trở nên đáng thi
> công khi **bật lại một kênh ÂM** — và đó là quyết định của Cường, không phải của phép đo.
>
> **Điều artifact 38 KHÔNG loại trừ, và đây mới là chỗ đáng đào tiếp:** `bo_shiftplan_khi_OFF =
> +53đ ns` nghĩa là `shift_plan` **trung tính** khi đứng một mình — tức lời khuyên tốt và lời
> khuyên tệ của nó **triệt tiêu nhau**. Một cơ chế **CHỌN LỌC TRONG MỘT KÊNH** (chỉ nói khi độ
> tin cậy cao, im phần còn lại) có thể tách hai nửa đó ra — và **artifact 38 không nói gì về
> lever này**. Bốn cơ chế trong spec đều là *chia suất GIỮA các kênh*, không phải *chọn lọc
> TRONG một kênh*. ⇒ Đề xuất: thí nghiệm tiếp theo nên là **E9 — chọn lọc trong kênh**, không
> phải E1.
>
> Phần còn lại của tài liệu giữ nguyên như agent sinh ra: nó vẫn là spec thi công tốt nhất cho
> E1 khi nào E1 được mở lại, và §1.2/§1.4 chứa **hai lỗi thật ở SẢN PHẨM** đáng sửa ngay bất kể
> E1 có chạy hay không (`topic` có default `"bonus"` ⇒ client không gửi `topic` rơi vào nhánh
> khác; và guard chống hồi sinh cổng đã tắt).

# SPEC THI CÔNG E1 — CƠ CHẾ CHIA NGÂN SÁCH CHÚ Ý (A/B/C/D)

Bản gộp 4 spec + soi đối kháng. Đọc cùng `tracking/HANDOFF-2026-07-29-da04.md` §2/§3. Tài liệu này là **nguồn thi công**; nơi nào nó khác 4 spec gốc thì **nó thắng** (mọi khác biệt đều là hệ quả của một finding soi đối kháng, có ghi mã).

---

## §0. SỰ THẬT ĐÃ KIỂM LẠI (đọc trước, vì nó lật baseline của cả 4 spec)

### 0.1 Artifact 38 TỒN TẠI — baseline phải viết lại
`research/audit/2026-07-27-current-state/38-e5-2x2-perseed-n100.json` (n=100, seed **4200–4299**, per-seed). Đã tự mở file, không trích lại từ spec:

| estimator | mean | CI95 | SIG |
|---|---|---|---|
| `TUONG_TAC_ngan_sach_FIFO` (net_mean_all) | **+2 206,6đ** | [1 077,3 · 3 371,7] | ✅ |
| `bo_shiftplan_khi_ON` | +2 259,4đ | [1 161,3 · 3 323,0] | ✅ |
| `bo_shiftplan_khi_OFF` | +52,8đ | [−974,3 · 1 102,4] | ❌ |
| `gia_cua_nhip_co_shiftplan` | −2 466,1đ | [−3 419,6 · −1 569,7] | ✅ |
| `gia_cua_nhip_khong_shiftplan` | −259,4đ | [−1 110,8 · 588,7] | ❌ |
| `served_rate` / `bo_shiftplan_khi_ON` | +0,0068 | [0,0046 · 0,0090] | ✅ |
| `orders_completed` / `bo_shiftplan_khi_ON` | +8,11 | [5,57 · 10,67] | ✅ |

**Ba hệ quả bắt buộc, áp cho cả 4 cơ chế:**
1. Con số "+3.249đ không có CI" **chết**. Dùng **+2 206,6đ CI[1 077 · 3 372]**.
2. **Trần trên của MỌI cơ chế chia ngân sách ≈ 2,2k đ/người/ca.** Arm nào báo Δ > ~2,2k đ phải bị nghi là đang đo *"nói ít/nhiều hơn"*, không phải *"chia khéo hơn"*.
3. **NULL-0 (giả thuyết vô hiệu DÙNG CHUNG cho A, B, C, D):** `bo_shiftplan_khi_ON` = **+2 259đ SIG** — tức **một dòng YAML của ĐA-07 đã lấy gần như toàn bộ giải thưởng**, và còn cho served +0,68đp SIG, +8,11 đơn SIG (không có đánh đổi phải cân). ⇒ Không cơ chế nào được gọi là "đáng ship" nếu nó không **vượt NULL-0**, chứ không phải vượt FIFO-5-kênh. Đây là tổng quát hoá của arm B3 trong spec B, và nó áp cho cả 4.

### 0.2 `event_type: "queued"` bị schema TỪ CHỐI — hết là câu hỏi mở
`schemas/advisor/advice_lifecycle_event.schema.json` → `event_type.enum = {decided, displayed, followed, dismissed, suppressed, superseded, expired}`; `AdviceEventLog.append` validate qua `SchemaRegistry` rồi raise **trước khi chạm DB**. ⇒ hàng đợi của A là **SIM-ONLY, chắc chắn**; UI chạy `queue_enabled=false`; bất đối xứng phải in lên mọi artifact. (`reason_code` là string tự do ⇒ reason mới KHÔNG cần bump schema, chỉ sửa description.)

### 0.3 Config ship tắt ngân sách bằng BA khoá độc lập
`configs/pilot_dongda.yaml`: `advice.enabled: false` (dòng 312) · `advice.cadence.enabled: false` · `advice.cadence.count_positioning_in_budget: false`. `cadence_allows` early-return `True` khi `not cadence_enabled`. ⇒ mọi arm `*-ship-confirm` sẽ **pass rỗng**; artifact phải liệt kê chính xác runner bật cờ nào. Và đây là nguồn của lỗi **A-C1** (§2.5).

### 0.4 `min_gap_min_per_topic` điều khiển HAI thứ (nợ cũ, cả 4 thừa hưởng)
`advice_bridge.py::cadence_allows`: `key = (actor_id, topic, v.reason, int(now_min // min_gap_min_per_topic))`. ⇒ mọi reason MỚI cũng bị dedupe theo lưới **20′** trên tick **2′** ⇒ metric đếm của A (`arbiter_lost`, tỷ lệ đụng độ) và C (`lane_budget_exhausted`) **thiếu tới ~10×**. Sửa ở §1.7, **trước** khi đo bất kỳ metric đếm nào.

### 0.5 Hằng đã tự kiểm (dùng trong tính toán dưới)
`max_proactive_per_shift: 6` · `min_gap_min_per_topic: 20` · `advice.interval_min: 30` · `advice.bucket_min: 60` · `DECISION_BUCKET_MIN = 30.0` · `accept_lift_step: 0.10` / `accept_lift_max: 0.15` (⇒ bão hoà sau **2** liều) · `shift_extend_max_min: 60` · `rest_defer_max_min: 120` · `rest_window` cộng **2,0′/tick** · ca theo archetype (`src/gsm_sim/archetypes.py`): P1 3–4h · P2 10–11h · P3 11–12h · P4 8–9h · P5 8–9h · P6 7–9h · P7 8–9h · `evaluate` thứ tự hôm nay: safety → is_driving → dismissed → **budget** → **cooldown**.

---

## §1. HẠ TẦNG DÙNG CHUNG (E1-CORE) — LÀM TRƯỚC, KHÔNG CƠ CHẾ NÀO ĐƯỢC BẮT ĐẦU TRƯỚC NÓ

Làm sai phần này thì cả 4 arm vô giá trị. Toàn bộ E1-CORE phải **bit-identical ở mặc định**, chứng minh bằng đo (test C-01).

### 1.1 MỘT cờ chế độ, không phải bốn
4 spec đặt 4 tên (`arbiter.mode` / `arbitration.mode` / `budget_mode` / `budget_mode`). Giữ 4 tên là tái diễn Lỗi #18 ở quy mô lớn hơn.

```yaml
advice:
  cadence:
    budget_mode: fifo   # fifo | ladder | reservation | lanes | lanes_shadow | no_global
    charge_unit: call   # call | decision_bucket        ← "một suất là gì", ORTHOGONAL
```
- Enum **loại trừ nhau**: không có tổ hợp hai cơ chế ⇒ không có đường để hai cờ điều khiển cùng một thứ.
- `fifo` ⇒ **không một dòng code E1 nào chạy**: không dựng proposal, không tính bảng, không đọc/ghi trường memory mới, không phát event kind mới, `drain_suppressed` giữ đúng vị trí, `due()`/`_last_consult` giữ nguyên.
- Giá trị ngoài enum ⇒ `raise ValueError` (không im lặng rơi về default — đó là cách một arm chạy sai mà không ai biết).

### 1.2 GUARD chống hồi sinh cổng đã tắt (sửa **A-C1**)
`load_cadence()` **raise ValueError** khi:
- `budget_mode != "fifo"` mà `advice.cadence.enabled` là `false`, **hoặc** `advice.enabled` là `false`;
- `charge_unit == "decision_bucket"` mà `budget_mode == "fifo"` và runner không khai tường minh `allow_fifo_charge_arm: true` (đó là một arm đổi hành vi hợp lệ, nhưng phải cố ý).

Lý do: pilot mặc định mang **cả hai** cờ `false` (§0.3). Không có guard này, `budget_mode: ladder` sẽ thi hành ngân sách/quota trong khi đường FIFO đã tắt ⇒ **arm đối chứng `cadence=off` không còn là đối chứng** (Lỗi #13 dạng nghịch). Test: dựng world với `(enabled: false, budget_mode: ladder)` ⇒ assert raise.

### 1.3 Loader DÙNG CHUNG — điều kiện tồn tại của "một luật"
File mới `src/gsm_core/lifecycle/cadence_config.py` (chỗ **duy nhất** được import yaml trong `lifecycle/`):
```python
def load_cadence(path: str | Path | None = None) -> CadenceSettings   # frozen dataclass
def reset_cadence_config_cache() -> None
```
- Cache khoá `(path, st_mtime_ns)` — **không** chỉ theo path (sửa **D-D1**: `lru_cache(path)` làm config rò giữa test ⇒ kết quả phụ thuộc thứ tự test).
- File vắng ⇒ default = **đúng** hằng UI đang khoá cứng (20/6/0,25/0,75) ⇒ hai nửa bit-identical.
- `CadenceSettings` chứa: `CadenceConfig` (4 trường cũ) + `budget_mode` + `charge_unit` + đúng một khối con của cơ chế đang bật.
- **UI phải truyền `cfg` vào CẢ BA chỗ**: `evaluate(...)`, `shift_phase(...)` ở đường GHI (`get_advice`), và `shift_phase(...)` trong `_phase_of` ở đường ĐỌC (`routers/advice.py:85`). Thiếu chỗ thứ ba là pha lệch giữa ghi và đọc **trong cùng một nửa** (sửa **A-P2**, **C-D1**).

### 1.4 `topic` phải BẮT BUỘC ở API (sửa **C-P1** + **D-P1** — lỗ nguy hiểm nhất phía sản phẩm)
Hôm nay `GET /advice` có `topic: str = Query("bonus")` và `AdviceAction.topic` mặc định `"bonus"`, còn `ui/web/js/cards.js::KIND_TOPIC` chỉ gửi `{brief, nudge, recap}`. ⇒ client nào bỏ tham số (Flutter `ui/driver_app/`, curl, test cũ) rơi vào một nhánh khác hẳn web client:
- ở **C**: `"bonus"` không có làn ⇒ chỉ được dùng hồ chung ⇒ 3 suất thay vì 6;
- ở **D**: `"bonus"` → lớp `policy` không có trần ⇒ **advisor KHÔNG GIỚI HẠN**.

Chốt: (a) `topic` bỏ default, thiếu ⇒ 422; (b) bản đồ `TOPIC_CLASS` phủ **cả hai namespace**, `"bonus" → demand`; (c) validate lúc load: khi `budget_mode != fifo`, **mọi** topic mà API có thể nhận phải được phủ bởi ít nhất một luật siết (trần/gap/làn) hoặc được khai `pool_only`/`uncapped` tường minh; (d) test **gọi `GET /advice` KHÔNG truyền topic** 10 lần liên tiếp ⇒ phải im ở đâu đó (hoặc 422).

### 1.5 `CadenceMemory` — hợp nhất, không cộng dồn 4 bộ trường
4 spec đề nghị 3 tên khác nhau cho cùng một đại lượng (`spoken_per_topic` / `slots_by_channel` / `spoken_by_topic`). Chốt **một** tên. Mọi trường default rỗng ⇒ `fifo` không ai đọc, không ai ghi.

| Trường mới | Ai cần | Sim nuôi | UI dẫn xuất từ `AdviceEventLog` |
|---|---|---|---|
| `spoken_by_topic: dict[str,int]` | A (quota) · B (`slot_index_channel`) · C (làn) · D (trần lớp) | `cadence_commit` | đếm `decision_id` **phân biệt** theo `canonical(topic)` |
| `pool_spent_by_topic: dict[str,int]` | C | `cadence_commit` khi nguồn = hồ chung | `payload["lane"]=="pool"` |
| `charged_keys: set[str]` | mọi mode khi `charge_unit=decision_bucket` | `cadence_commit` | `{f"{topic}-{decision_bucket(at_min)}"}` (record thiếu `at_min` **bỏ qua**, luật R-18) |
| `max_phase_rank: int` (high-water) | C (`late_release`) · A (escrow) | `observe_phase` mỗi tick | `max(payload["phase_rank"]…, phase_rank(request hiện tại))` |
| `safety_spoken: int` | A (escrow) | `cadence_commit` | `Σ spoken_by_topic[t]` với `topic_class(t)==safety` |
| `slots_by_opportunity: dict[int,int]` | B (`per_opportunity_cap`) | `cadence_commit` | `+1` tại `decision_bucket(at_min)` mỗi `decision_id` |
| `queued: dict[str, QueuedEntry]` | A | `cadence_update_queue` | **KHÔNG THỂ** (§0.2) ⇒ UI `queue_enabled=false` |
| `ev_spoken_vnd: float` | B (hiệu chuẩn ngược) | `cadence_commit` | `Σ payload["ev_vnd"]`, **sort `(occurred_at, event_id)` trước khi cộng** |

**Hợp nhất quan trọng:** C không có `lane_spent` riêng — `lane_spent[t] = spoken_by_topic[t] − pool_spent_by_topic.get(t,0)`. Nhờ đó bất biến toàn cục **`Σ spoken_by_topic.values() == proactive_count`** đúng ở mọi mode (test C-05), và không có hai bộ đếm nuôi bằng hai điều kiện khác nhau.

`dismissed_in_phase` **giữ UI-only** ở mọi mode (2 test đang khoá). `shift_id` **vẫn không có** — `D-R11b` còn nguyên; ca vắt nửa đêm được cấp lại toàn bộ 8 trường trên; ghi vào UPDATE, không sửa trong cycle này.

### 1.6 Bốn hàm/quy tắc SỬA LỖI CHUNG (mỗi cái sửa một finding của một spec, nhưng áp cho tất cả)

**(a) `_shift_len_planned(actor)` — chặn vòng advisor tự mua ngân sách** (phát hiện của D, áp cho cả B):
```python
return max(0.0, actor.shift_end_min - actor.shift_extended_min - actor.shift_start_min)
```
`check_shift_extend` cộng vào **cả hai** `shift_end_min` và `shift_extended_min`. Mọi đại lượng NGÂN SÁCH/NGƯỠNG dùng độ dài ca (`class_caps_per_hour` của D, `m_after` của B) phải dùng hàm này. Không dùng nó, advisor nới trần của chính mình bằng cách khuyên kéo ca (**B-F1** thừa hưởng lỗi này; D bắt được).
`_phase` **vẫn** dùng `shift_end_min` live — **không sửa** (sửa là đổi pha ⇒ mất bit-identical). Đây là bất đối xứng đã biết, ghi nợ, đừng để ai đọc "đã sửa phase regression" (**C-F1**, **D-F1**).

**(b) `observe_phase` + `max_phase_rank` — high-water cho mọi cổng phụ thuộc pha** (fix của C, áp cho A):
`phase_rank`: early 0 · mid 1 · late 2, **không bao giờ giảm**. Số học kiểm được: ca 600′, `phase_late_frac=0,75` ⇒ late từ 450; elapsed 460 = late; `shift_extend` +60 ⇒ shift_len 660 ⇒ late từ 495 ⇒ **trụt về mid**. Không có high-water thì `late_release` của C **và** escrow của A **nhấp nháy** (nhả tick n, thu tick n+1) ⇒ suất đã cấp không thu lại được ⇒ vượt trần (**A-F1**).
`observe_phase` là **no-op tuyệt đối** khi `budget_mode == fifo` hoặc `not cadence_enabled`, và **không được tạo entry `_cadence_mem`** (hai test đang soi: `test_cadence_state_does_not_leak_across_days`, `test_cadence_disabled_returns_to_baseline` với `_worst(off) > 6`).

**(c) Kế toán safety tách khỏi `proactive_count`** (sửa **A-F2**): topic lớp `safety` bypass mọi cổng **và** chỉ cộng `safety_spoken`, **không** cộng `proactive_count`. Nhờ đó bất biến `proactive_count ≤ max_proactive_per_shift` — thứ mọi dashboard/telemetry và `test_cadence_disabled_returns_to_baseline` đang đọc — **không bị phá** khi có safety thật sau `late_release`. Ở `fifo` và ở ship config không topic nào là safety ⇒ no-op.

**(d) Thứ tự nhánh `evaluate` ĐÓNG BĂNG** (sửa **A-P1**):
`safety → is_driving → dismissed → [TẦNG NGÂN SÁCH theo mode] → topic_cooldown`.
Tầng ngân sách là **chỗ duy nhất** E1 được can thiệp. Cấm đảo cooldown lên trước budget: nó đổi `reason` của các tick vừa-hết-ngân-sách-vừa-trong-cooldown từ `shift_budget_exhausted` sang `topic_cooldown`, mà `dashboard.py:504` tô vùng im-tới-cuối-ca **chỉ** cho reason thứ nhất ⇒ **hình Cường phán V-18 đổi vì lý do không liên quan cơ chế**, và `_suppressed_seen` có `reason` trong khoá nên số event nén cũng đổi.

### 1.7 Hai đường telemetry, không một (sửa §0.4 / **A-C2** / **C-N3**)
- `advice_suppressed`: **giữ nguyên**, kể cả lưới dedupe 20′. Không đụng ⇒ baseline không đổi.
- **MỚI** `advice_gate_trace`: **không dedupe**, chỉ phát khi `budget_mode != fifo`. Mỗi lần một kênh **đạt tới** tầng ngân sách thì ghi một dòng: `(t, actor, topic, topic_class, verdict, reason, k_left, rank, winner, tau_vnd, ev_vnd, lane_source, queue_age)`. **Mọi metric ĐẾM của E1 đọc kênh này**, không đọc `advice_suppressed`.
Không có nó, tỷ lệ đụng độ của A0-oracle và demand-per-lane của C7-shadow **đếm thiếu ~10×** ⇒ dễ ra kết luận sai chiều *"đụng độ hiếm ⇒ dừng E1"* trong khi thực tế đụng độ mỗi tick.

### 1.8 Tách PROPOSE/COMMIT — làm MỘT LẦN, dùng cho A và B
Bốn kênh thành `propose_<topic>` (thuần: chỉ đọc, không đụng memory/RNG/`_last_consult`) + `commit_<topic>`. Bốn hàm cũ (`check_bonus_gate`, `check_shift_extend`, `should_defer_rest`, `consult`) trở thành **wrapper của đường FIFO** giữ đúng thứ tự dòng hôm nay.

**Đây là chế độ hỏng số 1 của cả cycle** (spec A tự chẩn đoán đúng): rò tác dụng phụ khi cắt, không crash, test xanh, payout dịch vài trăm đồng. Bốn chỗ phải canh:
- `propose_accept_lift` gọi `_advice_would_help` → hàm này `self.skipped_advice.append(...)` ⇒ kênh propose-rồi-thua vẫn ghi sổ. **Chốt: `propose_*` nhận `dry: bool`; ở `dry=True` không được append.** Assert list không dài ra trong pass propose.
- `propose_shift_plan` **không được** ghi `self._last_consult`.
- `commit_shift_extend` giữ R-09: `cadence_commit` **vô điều kiện, TRƯỚC `coin_follows`**.
- `commit_accept_lift` giữ `_claim_effect` (R-01) — bỏ là arm đối chứng nhận liều 2,0–2,5×.
Lá chắn duy nhất đáng tin: **test C-01 (golden event stream 5 seed) + C-02 (no-op ở ship config)**. Ai bỏ hai test đó vì *"đường fifo không đổi mà"* thì chế độ hỏng này sống 100%.

### 1.9 Sửa hai lỗi nhỏ đã biết, GÁC THEO MODE
- `World._settle_end_of_run` drain lần cuối (lô cuối đang bị mất khi actor `END_SHIFT`/hết run) — **chỉ khi `budget_mode != fifo`**. Không gác là **thêm** event `advice_suppressed` ở fifo ⇒ vỡ bit-identical, và test "golden 5 seed" với test "final drain loses nothing" **không thể cùng xanh** (sửa **A-B1**).
- `drain_suppressed()` dịch xuống SAU `should_defer_rest` — **chỉ khi `budget_mode != fifo`**.
- `dashboard.py::_het_ns` mở rộng thành `in {"shift_budget_exhausted", "class_budget_exhausted"}`; `lane_budget_exhausted` / `class_cooldown` / `global_cooldown` / `lost_to_higher_priority` vẽ **từng vạch** (còn thông tin, có `next_eligible_min`). Đây là thay đổi **VISUAL-ONLY** áp cho mọi replay cũ ⇒ phải khai trong UPDATE và **xin Cường xác nhận re-baseline hình** (§7.2), vì V-18 được phán trên hình.
- `_SILENT_MSG` phải có câu cho **mọi** reason mà `evaluate` có thể trả (test duyệt tập reason từ module, không hardcode). Câu không được chứa **chữ số** (không tiết lộ ev/tiền — CLAUDE.md §5).

### 1.10 "MỘT SUẤT LÀ GÌ" — chốt một lần cho cả 4 (thay 4 cờ riêng)
**Chốt: một suất = một `(canonical_topic, decision_bucket 30′)` được NÓI.**
- `charge_unit: call` (mặc định) = **hôm nay**: `rest_window` tiêu một suất mỗi 2′ hoãn.
- `charge_unit: decision_bucket`: `cadence_commit` idempotent theo `charged_keys` ⇒ khớp UI (`_note_shown` đã dedupe theo `(topic, bucket 30′)` + `INSERT OR IGNORE`) ⇒ **đây là arm PARITY duy nhất giữa hai nửa**.
- **Cấm so số TUYỆT ĐỐI về volume giữa sim và UI** ở `charge_unit: call`.
- ⚠ Cảnh báo tính toán (sửa tuyên bố của A về `rest_defer_max_min`): với cooldown 20′ còn nguyên, `rest_window` chỉ được grant 1 lần/20′ × 2′ hoãn ⇒ tối đa ~2′ hoãn/20′ ⇒ **`rest_defer_max_min: 120` KHÔNG ràng buộc ở CẢ HAI giá trị `charge_unit`** khi cadence ON (**A-C3**, **D-N2**). Arm đo `charge_unit` phải đo số suất tiêu và `rest_deferred_min`, **không** được quảng cáo là "làm lan can 120′ sống lại".
- `cadence_commit` khi trả `False` (bucket đã tiêu) **vẫn phải ghi `last_decided_min`** ⇒ `charge_unit` không được lén điều khiển đồng hồ cooldown (**A-C3**).

### 1.11 Test cổng an toàn của E1-CORE (viết TRƯỚC mọi cơ chế)
| Mã | Test | Nội dung |
|---|---|---|
| **C-01** | `test_e1_core_default_bit_identical` | golden event stream (kind, actor, t làm tròn 3, detail sort_keys) trên 5 seed **1000/1001/1002/2000/3160**, config mặc định **và** config khai đủ mọi khoá mới ở giá trị vô hiệu ⇒ khớp digest commit kèm test. **Không xanh ⇒ dừng cycle.** |
| **C-02** | `test_e1_is_noop_at_ship_config` | ship config (§0.3) × mọi `budget_mode` ⇒ raise (guard §1.2) hoặc event stream identical. |
| **C-03** | `test_fifo_never_enters_new_code` | monkeypatch mọi entrypoint cơ chế cho raise ⇒ run mặc định vẫn xong. Phải patch **cả** hàm dựng candidate/proposal (sửa **B-B1**: `candidate=` là đối số nên được dựng ở mọi tick nếu viết eager ⇒ **phải dựng LƯỜI**). |
| **C-04** | `test_gate_layer_consumes_no_rng` | `world.rng.bit_generator.state` và `advice.rng...state` không đổi qua 1000 lời gọi tầng ngân sách + pass propose. Bất biến, không bám ngưỡng. |
| **C-05** | `test_slot_accounting_invariant` | mọi actor: `Σ spoken_by_topic == proactive_count`; `Σ pool_spent_by_topic ≤ Σ spoken_by_topic`; `proactive_count ≤ max_proactive_per_shift`; safety không cộng `proactive_count`. Chạy ở mọi mode × `count_positioning_in_budget ∈ {false,true}`. |
| **C-06** | `test_guard_rejects_mode_without_cadence` | §1.2, 4 tổ hợp. |
| **C-07** | `test_ui_reads_shared_config` | vặn `max_proactive_per_shift` trong YAML ⇒ **cả hai** nửa đổi hành vi. Test này **phải ĐỎ trước khi implement** (hôm nay UI đọc 0/4 cờ). |
| **C-08** | `test_topic_is_required` | `GET /advice` không truyền `topic` ⇒ 422; `AdviceAction` thiếu topic ⇒ 422. |
| **C-09** | `test_high_water_survives_extension` | dựng late→mid bằng +60′; `max_phase_rank` giữ 2; kèm biến thể **không** high-water để chứng minh test thực sự bắt (mutation-check tại chỗ). |
| **C-10** | `test_per_hour_and_threshold_use_planned_shift_len` | sau `check_shift_extend` +60′, `_shift_len_planned` KHÔNG đổi. |
| **C-11** | `test_gate_trace_is_not_deduped` | `advice_gate_trace` phát mỗi tick; `advice_suppressed` vẫn dedupe 20′. |
| **C-12** | `test_propose_has_no_side_effects` | pass propose không đổi: `skipped_advice` len, `_last_consult`, `_cadence_mem` nội dung, `_effect_applied`, hai RNG state. |
| **C-13** | `test_silent_msg_covers_every_reason` | duyệt tập reason từ module; và không câu nào chứa chữ số. |

---

## §2. CƠ CHẾ A — THANG ƯU TIÊN TĨNH + TRỌNG TÀI PROPOSE/COMMIT (`budget_mode: ladder`)

### 2.1 Interface (thêm vào `src/gsm_core/lifecycle/cadence.py`, module KHÔNG import sim/UI)
```python
CLASS_SAFETY="safety"; CLASS_POLICY="policy_bonus"; CLASS_POSITION="position"; CLASS_DEMAND="demand"
CLASS_RANK = {CLASS_SAFETY:0, CLASS_POLICY:1, CLASS_POSITION:2, CLASS_DEMAND:3}
# reason mới: lost_to_higher_priority · topic_quota_exhausted · safety_reserve_held
#             queue_expired · queue_promoted        (schema chấp nhận: reason_code string tự do)

@dataclass(frozen=True)
class LadderConfig:
    topic_class: Mapping[str,str]; default_class: str = CLASS_DEMAND
    tiebreak: str = "irreversibility"          # | "topic_order"
    topic_tiebreak_order: tuple[str,...] = ()
    queue_enabled: bool = False
    queue_ttl_min: float = 60.0
    queue_aging: str = "within_class"          # off | within_class | cross_class
    queue_promote_after_min: float = 20.0
    queue_max_class_promote: int = 1
    allow_promote_into_safety: bool = False    # BẤT BIẾN AN TOÀN
    max_per_topic_per_shift: Mapping[str,int] = {}; default_max_per_topic: int = 0
    reserve_for_safety: int = 0
    escrow_release_phase: str | None = None    # "late" ⇒ nhả khi max_phase_rank >= 2
    shift_plan_interval_min: float | None = 30.0   # ⚠ MẶC ĐỊNH GIỮ due(), xem 2.5/A-W1

@dataclass(frozen=True)
class Proposal:
    topic: str; remaining_window_min: float; urgency_per_min: float
    content_key: str; is_driving: bool = False
@dataclass(frozen=True)
class QueuedEntry: enqueued_min: float; content_key: str; last_seen_min: float
@dataclass(frozen=True)
class Grant:
    topic: str; verdict: str; reason: str|None=None; next_eligible_min: float|None=None
    rank: int = -1; cls: str = CLASS_DEMAND; queue_age_min: float = 0.0

def arbitrate(proposals, now_min, phase, memory, cfg, lcfg) -> dict[str, Grant]   # THUẦN
def cadence_update_queue(grants, proposals, now_min, memory, lcfg) -> list[tuple[str,str]]
def cadence_commit(topic, now_min, memory, cfg, *, charge_unit, counts_in_budget) -> bool
```

### 2.2 Bản đồ topic → lớp
`safety→safety` · `accept_lift, shift_extend, brief, bonus→policy_bonus` · `positioning→position` (**tách riêng**, không gộp demand: đây là kênh duy nhất dương SIG) · `shift_plan, rest_window, nudge, recap, advice→demand`. Topic ngoài bảng ⇒ `default_class` **+ tăng biến đếm `topic_class_unknown` + log một lần** (fail-loud). `rest_window` là **dữ liệu cấu hình**, mặc định `demand` — xem §7.1.

### 2.3 Một tick (chỉ khi `ladder`)
```
choose_idle_action(...)      # NGUYÊN VẸN, tiêu world.rng y như World A (giữ CRN)
observe_phase(actor, now)    # high-water
PROPOSE    collect_proposals(...)  # PROPOSE_ORDER tuple hằng, assert 1 proposal/topic
ARBITRATE  arbitrate(...)          # THUẦN
QUEUE      cadence_update_queue(...)
COMMIT     commit_* theo THỨ TỰ HẠNG
DRAIN      drain_suppressed() + advice_gate_trace
```
**Xếp hạng** — khoá sort toàn phần, lượng tử hoá về int, kết bằng `topic` (⇒ tính ổn định của Timsort thành vô nghĩa; hoán vị đầu vào không đổi kết quả):
`(class_rank, −age_bucket, −int(round(urgency*1000)), int(round(max(0,window))), topic_order_rank, topic)`
`class_rank` là thành phần **đầu** ⇒ không có đường nào để một số `demand` lớn vượt `policy_bonus`.
**Ngân sách + escrow:** `reserve = reserve_for_safety`; nhả về 0 khi `escrow_release_phase is not None and max_phase_rank >= phase_rank(escrow_release_phase) and safety_spoken == 0`; `slots0 = max(0, max − reserve − proactive_count)`. Loser: `shift_budget_exhausted` nếu `slots0 <= 0`, ngược lại **`lost_to_higher_priority`** — phân biệt này là **bắt buộc**, nó là con số duy nhất đo được chi phí của trọng tài, và hôm nay nó không tồn tại ở bất kỳ đâu trong repo.
**Hàng đợi chứa TUỔI, không chứa nội dung:** entry chỉ sống nếu topic tự re-propose trong chính tick này với `content_key` y hệt; khác ⇒ xoá, vào lại như mới. Hết TTL ⇒ `queue_expired` — **đây là metric trả lời "kênh nào bị bỏ đói"**, thay con số ma đã bị bác bỏ.
**COMMIT:** topic không GRANT ⇒ **không có tác động nào**; đặc biệt `rest_window` thua thì `action/target` giữ nguyên (KHÔNG ghi `IdleAction.WAIT`) — nếu không sinh trạng thái bất khả "nghỉ bị chặn mà không có lời khuyên nào".

### 2.4 `urgency_per_min` — công thức đã SỬA
| topic | urgency | window |
|---|---|---|
| `accept_lift` | **`gap_to_thr / max(1, phút còn lại tới shift_end)` × dư địa `lift_max − accept_lift`** (đơn vị riêng của kênh) | `shift_end − now` |
| `shift_extend` | `1 / max(1, slack)` với `slack = (extend_max − extended) − need_min` | `shift_end − now` |
| `rest_window` | `1 / max(1, minutes_to_window)` | `minutes_to_window` |
| `shift_plan` | `0.0` (ASSUMPTION: mất suất = HOÃN, bucket sau có lịch mới) | `min(horizon, world_end) − now` |

Sửa **A-N1**: công thức gốc `orders_offered / online_min` **phản lại** chính lý lẽ tie-break — đầu ca `orders_offered = 0` ⇒ urgency 0 ⇒ đúng ca mà PHÁT HIỆN SIM-4-B gọi là giá trị nhất (*lời khuyên PHÒNG NGỪA đầu ca*) thì xếp **cuối** trong lớp. Test: `accept_lift(orders_offered=0, gap_to_thr>0)` vs `shift_extend(slack=5)` cùng lớp ⇒ `accept_lift` phải **thắng**.

### 2.5 Điểm chèn (tên symbol — số dòng `advice_bridge.py` lệch liên tục)
`AdviceActionBridge.__init__` (parse `LadderConfig`, `self._plan_cache`) · 4 cặp `propose_*`/`commit_*` (§1.8) · `collect_proposals` · `arbitrate_tick` · `cadence_allows`/`cadence_note_spoken` giữ chữ ký cho đường FIFO · `_claim_effect`/`coin_follows`/`standby_follow_draw`/`adherence_coin` **KHÔNG ĐỔI MỘT CHỮ** · `World._actor_proc` thêm nhánh sau `choose_idle_action` · `World._standby_planner` không đổi (positioning commit trực tiếp) · `World.log` thêm `arbiter_proposal`/`arbiter_lost`/`queue_expired`/`queue_promoted` **chỉ ở ladder**.

**`_plan_cache` — khoá phải chứng minh bằng CẤU TRÚC (sửa A-D1, chế độ hỏng #2 mà spec A tự cảnh báo rồi tự viết vào):** khoá đề xuất ban đầu thiếu `actor.cell`, `shift_end_min` (→`buckets_remaining`), `shift_start_min`, `orders_offered/accepted` (→`_acc_estimate`). Kịch bản: bucket 30′ = 15 tick; t=600 ở cell X → cache; t=602 RELOCATE sang Y (hoặc `accept_lift` vừa nâng, hoặc `shift_end_min` vừa +45′) ⇒ cache trả plan của trạng thái CŨ ⇒ `schedule[0]` khác ⇒ `material_revision` khác ⇒ **coin khác ⇒ follow khác**. Deterministic, test xanh, payout dịch.
Test **A-16** không dùng 200 mẫu ngẫu nhiên (có thể không bao giờ trúng tick đổi cell trong cùng bucket) mà: bọc `Actor` bằng proxy ghi lại **mọi attribute được đọc** trong `build_shift_plan_input` + `solver_params`, assert `attrs_read ⊆ cache_key_fields`.
Kèm **A-D2**: `plan_t_now_snap="bucket"` snap trường dẫn xuất thời gian tới 29′ trong khi trường trạng thái đọc live ⇒ assert **`rest_taken_min <= shift_elapsed_min`** trong `propose_shift_plan`, không chỉ `t_snap <= now`.

**`shift_plan_interval_min` mặc định **GIỮ 30**, không khai tử `due()`** (sửa **A-W1**): khai tử ⇒ `shift_plan` propose mỗi 2′, chỉ còn cooldown 20′ ⇒ trần grant từ 24 lên 36 trên ca 12h. Mà artifact 38 nói `shift_plan` là kênh trị giá **−2 259đ SIG** (bỏ nó đi thì lãi thêm), served −0,68đp, +8 đơn hết hạn. ⇒ tồn tại vùng cấu hình mà ladder chỉ đơn thuần **cho kênh tệ nhất nói TO hơn**. Khai tử `due()` trở thành **arm riêng A10**, không phải mặc định, và có stop rule ở §8.

### 2.6 Xử lý finding soi (A)
| Mã | Xử lý |
|---|---|
| **A-D1** | SỬA — khoá cache + test cấu trúc (proxy attribute). |
| **A-D2** | SỬA — assert `rest_taken ≤ elapsed`. |
| **A-C1** | SỬA ở §1.2 (guard raise). |
| **A-C2** | SỬA ở §1.7 (`advice_gate_trace` không dedupe). |
| **A-C3** | SỬA ở §1.10 (`cadence_commit` vẫn ghi `last_decided_min`); **và ĐÍNH CHÍNH**: arm `charge_unit` không được quảng cáo là làm `rest_defer_max_min` sống lại. |
| **A-F1** | SỬA ở §1.6(b) (high-water). |
| **A-F2** | SỬA ở §1.6(c) (safety không cộng `proactive_count`). |
| **A-P1** | SỬA ở §1.6(d) (thứ tự nhánh đóng băng). |
| **A-P2** | SỬA ở §1.3 (cfg cho `shift_phase` cả 3 chỗ). |
| **A-B1** | SỬA ở §1.9 (final drain gác theo mode). |
| **A-N1** | SỬA — công thức urgency §2.4. |
| **A-W1** | SỬA — `shift_plan_interval_min` mặc định 30 + stop rule §8. |
| **A-N2** | CHẤP NHẬN có ý thức — không tự chặn: fit trên **seed tươi** (§6.2) là lối ra đã có; §4.2 câu 5 chỉ chặn fit-trên-seed-đã-báo-cáo. |
| §0.2 (queue) | CHẤP NHẬN — `queue_enabled=false` ở UI, in bất đối xứng lên mọi artifact. |

### 2.7 Test riêng của A
`A-01` arbitrate thuần (deepcopy memory bằng chính nó; gọi 2 lần identical) · `A-02` order-independent (200 hoán vị seeded) · `A-03` safety outranks + không rò chéo lớp · `A-04` escrow giữ suất, reason `safety_reserve_held` ≠ `shift_budget_exhausted` · `A-05` nhả **chỉ** ở late **và chỉ khi** `safety_spoken==0`, dùng `max_phase_rank` (không nhấp nháy) · `A-06` quota chống độc quyền · `A-07` queue re-validate `content_key` · `A-08` TTL + `queue_expired` · `A-09` aging không vượt lớp (và `cross_class` + `allow_promote_into_safety=false` **không bao giờ** đạt rank 0) · `A-10` không grant ⇒ không ghi WAIT · `A-11` urgency accept_lift đầu ca thắng · `A-16` cache trong suốt (proxy) · `A-17` `shift_plan` bỏ khỏi tập loại trừ của `test_suppressed_events_are_not_phantom` (`ma = nen − said − {"positioning","shift_plan"}` hôm nay đang loại trừ tường minh) · `A-18` exact-repeat ladder 5 seed · `A-19` một proposal/topic/tick ⇒ RAISE.

---

## §3. CƠ CHẾ B — RESERVATION PRICE (`budget_mode: reservation`)

### 3.1 Interface
```python
@dataclass(frozen=True)
class ReservationConfig:
    plan_clock: str                      # "gate" | "consult"  — KHÔNG CÓ DEFAULT, phải khai
    per_opportunity_cap: int = 1          # ⚠ MẶC ĐỊNH 1, xem B-D2
    opportunity_grid_min: float = DECISION_BUCKET_MIN   # __post_init__ ép ==30
    value_grid_vnd: float = 50.0          # ⚠ đổi từ 250, xem B-N1
    value_cap_vnd: float = 5_000.0        # ⚠ đổi từ 20.000, xem B-N1
    ev_floor_vnd: float = 0.0; tau_scale: float = 1.0
    min_obs_per_bin: int = 30; objective: str = "net_vnd"; algo_version: str = "resv-2"
@dataclass(frozen=True)
class ValueBook:   # artifact JSON, fit NGOÀI vòng chạy, commit được, review được
    book_version: str; objective: str; fitted_on: str; seed_block: tuple[int,int]
    cost_config_hash: str; channels: tuple[ChannelValue,...]
@dataclass(frozen=True)
class ChannelCandidate:   # CỐ Ý KHÔNG CÓ trường value/ev/delta_payout/benefit
    channel: str; features: tuple[tuple[str,float],...]     # SORT theo tên
@dataclass(frozen=True)
class ReservationTable: fingerprint: str; k_max: int; m_max: int; value: ...; tau: ...
```
`ALLOWED_FEATURES` là **danh sách ĐÓNG**; feature lạ ⇒ `ValueError` (đây là lan can chống rò tương lai mạnh nhất trong 4 spec — giữ nguyên).

### 3.2 DP
`V[0][m]=V[k][0]=0`; `V[k][m] = Σ_j f'_j · max(v_j + V[k−1][m−1], V[k][m−1])`; `tau[k][m] = V[k][m] − V[k−1][m]`; `tau[0][*] = +inf`.
Tính chất phải test: `tau` không tăng theo `k`, không giảm theo `m`, `tau[k][0] = 0` (cơ hội cuối nhận mọi `v > 0` — "cuối ca ngưỡng tự hạ" là **hệ quả công thức**, không phải heuristic gắn thêm). Cộng bằng `math.fsum` theo `j` tăng; cache theo fingerprint chứa **mọi** field của config + `book.fingerprint()` nội dung + `cost_config_hash` + `k_max/m_max/DECISION_BUCKET_MIN/algo_version`, float đưa vào bằng `float.hex()`; bảng trên đĩa lưu `float.hex()` (round-trip chính xác).

### 3.3 Luật quyết định
`… → (4) budget k_left ≤ 0 → (5) topic_cooldown → (6) per_opportunity_cap → (7) ev ≤ floor → (8) ev < tau_scale·tau(k_left, m_after) → PRESENT`.
Giữ **budget trước cooldown** đúng như hôm nay ⇒ B **không** mắc A-P1. Bất biến: reservation là **phép SIẾT thuần** của FIFO **ở mức per-decision** (docstring test phải ghi rõ: KHÔNG suy ra ở mức per-run, quỹ đạo phân kỳ).
`m_after = clip(ceil((shift_end_planned − now)/g) − 1, 0, m_max)` với `shift_end_planned` từ **`_shift_len_planned`** (§1.6a) ⇒ advisor không tự nới τ bằng cách khuyên kéo ca (**B-F1**).

### 3.4 Ba lỗi phải sửa trước khi bảng có nghĩa
- **B-D1 — xác suất ÂM, im lặng:** `f'_0 = 1 − Σ_c q_c`. `shift_plan` được hỏi mỗi `interval_min = 30′` = **đúng một cơ hội** ⇒ `q ≈ 1` một mình; thêm `positioning`/`accept_lift`/`rest_window` ⇒ `Σq > 1` gần như chắc chắn ⇒ DP chạy trên xác suất âm ⇒ τ âm hoặc mất đơn điệu, fingerprint khớp, cache khớp, không crash. **SỬA:** `ValueBook.load` raise khi `q ∉ [0,1]` hoặc `Σq > 1`; test dựng sách `Σq = 1,4` kỳ vọng ValueError (test property-based dùng cùng helper sinh pmf **sẽ không bắt được**).
- **B-D2 — DP mis-specified (MODEL GAP, không phải bug):** DP giả định ≤1 candidate/cơ hội, nhưng cơ chế tồn tại chính vì ≥2 kênh cùng muốn nói ⇒ `k` giảm >1 mỗi cơ hội ⇒ τ lệch có hệ thống (quá dễ ở cuối, quá chặt ở đầu). Không sửa được bằng thêm seed. **SỬA:** `per_opportunity_cap` mặc định **1** (ràng buộc mô hình khớp DP), và **phải đo TRƯỚC** phân phối grant-per-bucket-30′ ở arm A0-oracle; nếu `P(≥2) > 0` đáng kể mà muốn `cap=null` thì phải đổi DP sang mô hình nhiều-offer-mỗi-bước — **cycle riêng**.
- **B-N1 — lưới làm DP suy biến, tính từ số THẬT:** artifact 38 nói toàn bộ dư địa cơ chế ngân sách di chuyển được là **+2 207đ trên ≤6 suất** ⇒ ev cận biên/suất cỡ **vài trăm đồng**. Với grid 250đ / cap 20.000đ, toàn bộ phân phối rơi vào **2–3 ô trong 81** ⇒ τ chỉ nhận 2–3 giá trị ⇒ `V[k][m]` là trang trí. (Lý lẽ cũ "cap 20.000 vì Δ arm lớn nhất +8.488đ" so một **mức** với một **giá trị cận biên** — hai đại lượng khác nhau.) **SỬA:** grid **50đ**, cap **5.000đ** (ASSUMPTION dẫn từ +2 207đ/≤6 suất); và **cổng cứng**: sau E-B0a in `J_effective = #ô có khối lượng > 0`; `J_effective ≤ 3` ⇒ **DỪNG B**, báo là cơ chế không có dư địa phân biệt.
- **B-C1 — cờ có default là hàm của cờ khác:** `plan_clock` **bỏ default**; `mode=reservation` mà không khai ⇒ raise. Nếu không, đặt `reservation` **đồng thời** đổi ngữ nghĩa `interval_min`/`_last_consult` — đúng cái B dựng arm B0/B1′ để tách rồi lại nướng vào default.

### 3.5 Điểm chèn
`__init__` nạp sách (fail loud: `value_book` null · kênh lạ · `objective` lệch · `cost_config_hash` lệch · **`world.seed ∈ book.seed_block`**) · `cadence_allows` thêm keyword `candidate` **dựng LƯỜI** (sửa **B-B1**) và trả `CadenceVerdict` (không dùng state ẩn giữa hai lời gọi) · `cadence_note_spoken` → `cadence_commit` + `slots_by_opportunity`/`spoken_by_topic`/`ev_spoken_vnd` · `consult` hai nhánh tường minh theo `plan_clock` (nhánh `gate` copy **y nguyên** thứ tự cũ — bit-identical quan trọng hơn DRY) · `World._actor_proc` thêm `ev/tau/slots_left/opportunities_left/ev_n_obs` vào detail **chỉ ở reservation** · `drain_suppressed` nới tuple 4→5 (đã kiểm: **một** call site, `world.py:788`) · script mới `scripts/fit_value_book.py` (ngoài đường chạy sim).
UI: `get_advice` chuyển **content-first** (gọi advisor trước, gate sau). **Kiểm bắt buộc (B-P1):** lời khuyên đã tính nhưng bị nén **không được** ghi `displayed` — test FastAPI: response `silent` ⇒ `AdviceEventLog` tăng **0** record. Không có test này, ngân sách sản phẩm hao mà tài xế không thấy thẻ.

### 3.6 Đo TRƯỚC (không có thì B không chạy được, và τ gõ tay là bịa số)
- **E-B0a** (ev cấp kênh, scalar): LOO ablation 5 kênh trên nền nghiên cứu, **n=100 seed 4500–4599**, per-seed, `ev̂_c = Δnet / #decision_id của c`, bootstrap ghép cặp. Ghi thẳng hạn chế "đây là ev TRUNG BÌNH, không cận biên" vào `fitted_on`.
- **E-B0b** (ev theo bin, MRT): hold-out **keyed** `sha256(f"{seed}|{decision_id}|{salt}")` (không tiêu RNG, hỏi lại cùng quyết định ra cùng kết quả — cùng họ `adherence_coin`), rate 0,5, **n=300 seed 4600–4899**, hồi quy trên driver-day, cluster bootstrap theo seed; **bắt buộc thêm số hạng TRỄ** và báo nó có ý nghĩa hay không (giả định no-carry-over đổ ⇒ rơi về sách E-B0a).
- `slot_index_channel` là bin **BẮT BUỘC** cho `accept_lift`/`shift_extend` (bão hoà `lift_max` sau 2 liều ⇒ ev suất thứ 3 phải đo được ≈0). Sách thiếu bin đó cho hai kênh ⇒ `load` từ chối.

### 3.7 Xử lý finding soi (B)
| Mã | Xử lý |
|---|---|
| **B-D1** | SỬA — validate `Σq ≤ 1` + test dựng sách vi phạm. |
| **B-D2** | SỬA phần ràng buộc (`cap=1` mặc định) + **ĐO TRƯỚC** grant-per-bucket; mô hình nhiều-offer là cycle riêng. |
| **B-N1** | SỬA — grid 50 / cap 5.000 + cổng `J_effective ≥ 4`. |
| **B-C1** | SỬA — `plan_clock` không default. |
| **B-B1** | SỬA — candidate dựng lười + test C-03 patch cả `_candidate`. |
| **B-F1** | SỬA — `_shift_len_planned` (§1.6a). |
| **B-P1** | SỬA — test "silent ⇒ 0 record". |
| **B-D3** | SỬA — `_cadence_memory` sort `(occurred_at, event_id)` trước khi cộng float (`AdviceEventLog` docstring: *thứ tự không đảm bảo*). |
| **B-N2** | SỬA cùng lúc — bỏ `shift_plan` khỏi tập loại trừ của `test_suppressed_events_are_not_phantom`. |
| **B-W1** | SỬA bằng veto (§8): arm nào có `#nói(positioning) < baseline` ⇒ **vô hiệu**. Số: +6.016đ/người trên ~19 lượt gán/ca ⇒ ~300đ/suất; τ đầu ca dễ vượt 300đ ⇒ B câm đúng kênh dương SIG duy nhất. |
| Vòng tròn hiệu chuẩn | CHẤP NHẬN có lan can (đây là chế độ hỏng #1 của B, spec gốc xếp đúng): `seed_block` fail-loud · `slot_index_channel` bắt buộc · arm B6 hiệu chuẩn ngược (`ev_spoken_vnd` vs Δnet ghép cặp; residual âm tăng theo số suất = chữ ký lỗi) · arm B3 = NULL-0. |

---

## §4. CƠ CHẾ C — NGÂN SÁCH CÓ LÀN (`budget_mode: lanes` / `lanes_shadow`)

### 4.1 Interface & thuật toán (giữ gần nguyên spec gốc — đây là spec sạch nhất về determinism)
`LaneBudgetConfig(lane_topics, ui_lane_topics, lane_priority, reserve_per_lane=1, late_release=True, release_at_phase="late", lane_draw_order="reserve_first", oversubscribe="cap_lanes", lane_set_change="reconcile")`.
- `canonical_lane_order` = `lane_priority` theo thứ tự khai báo + `sorted(còn lại)` ⇒ không phụ thuộc thứ tự dict.
- `allocate_reserves`: `cap_lanes` ⇒ `reserved_total ≤ B` luôn đúng; `shrink_pool` ⇒ arm nghiên cứu, cap toàn cục vẫn chặn.
- `reconcile_lane_set`: suất **đã chi không thể hủy**, chỉ **tái phân loại** sang hồ chung; idempotent.
- `lane_state`: nhả ⇒ `released = Σ max(0, res[t] − lane_spent[t])` **và `lane_free[t] = 0` cho MỌI t** (**NHẢ LÀ CHUYỂN, KHÔNG NHÂN BẢN**). Chứng minh đơn điệu: sau `released > 0` thì `lane_free ≡ 0` ⇒ mọi chi đi qua pool ⇒ `lane_spent` đóng băng ⇒ `released` đóng băng ⇒ `pool_total` đóng băng. (Lập luận sắc nhất trong 4 spec — giữ, và assert.)
- `budget_verdict`: **cap toàn cục LUÔN THẮNG** (`cap_free ≤ 0 ⇒ shift_budget_exhausted`), rồi làn/hồ (`lane_budget_exhausted`).
- Nhả dùng **`max_phase_rank`** (§1.6b), không dùng `phase` live.
- Kế toán: `lane_spent[t] = spoken_by_topic[t] − pool_spent_by_topic[t]` (§1.5).

### 4.2 `lanes_shadow` ghi vào object RIÊNG (sửa **C-C1**)
Shadow tính quyết định của làn để lấy demand per-lane nhưng **thi hành FIFO**. Không được ghi vào `CadenceMemory` (bit-identical duy trì bằng *kỷ luật* là mời người sau phá) — ghi vào `LaneShadowTally` riêng ⇒ bất biến do **cấu trúc**. Số shadow chảy qua `advice_gate_trace` (§1.7), **không** qua `_suppressed_out` (nếu không thì bị dedupe 20′ — **C-N3**).

### 4.3 Sổ đồ (số tính từ config)
Arm nghiên cứu 4 kênh ON ⇒ `lane_topics = {shift_plan, accept_lift, shift_extend, rest_window}` ⇒ `reserved_total = 4`, `pool_base = 6 − 4 = 2`.
Ship config ⇒ `lane_topics` **rỗng** ⇒ `pool_base = 6` ⇒ C **đồng nhất FIFO**. Đừng dùng điều đó làm bằng chứng "C vô hại": nó chỉ nghĩa là C **chưa được kiểm** ở ship path.

### 4.4 Xử lý finding soi (C)
| Mã | Xử lý |
|---|---|
| **C-N1** | SỬA null hypothesis: `C0b` **không** đặt trần = `pool_base` (2). Ở C1 mỗi làn vẫn tiêu được suất ⇒ tổng thực tế tới 6 ⇒ C0b-với-trần-2 **khắc nghiệt hơn** C1 và C1 sẽ thắng vì lý do tầm thường. **Chốt:** đo `slots_spent_per_driver` **thực tế** ở C1 rồi chạy C0b ở đúng con số đó (làm tròn), và **báo cả hai** (pool_base và realised). |
| **C-C1** | SỬA — `LaneShadowTally`. |
| **C-P1** | SỬA ở §1.4 (`topic` bắt buộc). |
| **C-D1** | SỬA ở §1.3 (cfg cho `shift_phase` cả đường ghi và đường đọc `_phase_of`). |
| **C-N3** | SỬA ở §1.7. |
| **C-B1** | CHẤP NHẬN — sửa `dashboard.py::_het_ns` là **VISUAL-ONLY**, đổi hình mọi replay cũ ⇒ khai trong UPDATE + xin xác nhận re-baseline (§7.2). |
| **C-F1** | CHẤP NHẬN — high-water chỉ chữa **quyết định nhả**; `_phase` vẫn trụt lùi ⇒ nhãn pha trong telemetry và `dismissed_in_phase` (UI) vẫn nhấp nháy. Ghi nợ. |
| **C-N2** | SỬA — dùng artifact 38 (§0.1). |
| **C-W1** | SỬA bằng stop rule (§8): số cụ thể — `rest_window` nói **0 lần** kể cả khi tắt hẳn cadence; `accept_lift` bão hoà sau **2** liều; `shift_extend` bị `shift_extend_max_min: 60` chặn ⇒ ở C1 có ~2 suất bảo lưu **chết**, và `late_release` chỉ nhả sau `phase_late_frac = 0,75` ⇒ **75% đầu mọi ca chạy với ngân sách hiệu dụng 4, không phải 6** ⇒ C1 là "hạ trần giữa ca" khoác áo trọng tài. |
| Lệch đơn vị UI/sim | SỬA ở §1.10; **cấm so số tuyệt đối hai nửa** trước arm `charge_unit=decision_bucket`. |

### 4.5 Test riêng của C
`C-c1` mặc định = biểu thức FIFO (bảng 0/5/6/7 suất) và không ghi trường mới · `C-c2` `lanes_shadow` bit-identical với fifo trên 5 seed **nhưng** `LaneShadowTally` khác rỗng · `C-c3` nhả CHUYỂN không NHÂN BẢN (4 làn chưa dùng + pool 2, vào pha cuối một topic nói tối đa **6** lần rồi `shift_budget_exhausted`, KHÔNG phải 10) · `C-c4` reconcile không "hoàn suất", idempotent 3 lần = 1 lần · `C-c5` cap toàn cục luôn thắng (`shrink_pool` 2×5=10 > 6 ⇒ lần thứ 7 là `shift_budget_exhausted`) · `C-c6` không phụ thuộc thứ tự dict (hai thứ tự chèn ngược nhau ⇒ cùng chuỗi quyết định) · `C-c7` `lane_exhausted` KHÔNG vẽ như terminal · `C-c8` UI roundtrip: event thiếu `payload["lane"]` đếm như **pool** + WARN (KHÔNG suy "lane" — suy sai chiều làm ngân sách nổi lên, đúng lỗi R-18).

---

## §5. CƠ CHẾ D — BỎ NGÂN SÁCH CHUNG (`budget_mode: no_global`)

### 5.1 Bốn công cụ độc lập
`class_caps` (trần ĐẾM theo lớp) · `class_caps_per_hour` (trần đếm CHUẨN HOÁ theo `_shift_len_planned`) · `min_gap_min_per_class` (trần TỐC ĐỘ theo lớp) · `min_gap_min_global` (trần TỐC ĐỘ toàn cục). Cộng `adherence_volume_decay` / `adherence_volume_free` (chi phí chú ý — arm bắt buộc, không phải phụ).
**Phân loại khái niệm phải giữ tách trong mọi báo cáo:** trần ĐẾM (a/b) **vẫn tạo im lặng vĩnh viễn**, chỉ hẹp hơn FIFO; trần TỐC ĐỘ (c/d) **triệt tiêu im lặng vĩnh viễn** (không tick nào là "hết suất", chỉ "chưa tới lượt"). Chỉ (c/d) là phản đề đúng của "ngân sách đếm". Cấm gộp thành "phương án D".

`effective_class_cap`: `class_caps` thắng; rồi `floor(r × len/60 + CAP_FLOOR_EPS)` với `max(1, ·)`. `max(1,·)` là bắt buộc: P1 ca **3–4h** (đã kiểm `archetypes.py`), r=0,25 ⇒ floor = 0 ⇒ tài xế part-time im HOÀN TOÀN — chế độ hỏng thầm lặng. Muốn im hẳn phải khai `class_caps: {demand: 0}` tường minh.
`effective_adherence(p) = p × (1 − decay)^max(0, Σspoken − free)`, dùng ở `coin_follows`; **coin (hash) KHÔNG đổi**, chỉ ngưỡng đổi ⇒ không thêm nguồn ngẫu nhiên, washout vẫn chết.
Trần ĐẾM cạn ⇒ **không** trả `next_eligible_min` (nó cạn là cạn tới hết ca; hứa "sẽ quay lại" là nói dối). Trần TỐC ĐỘ ⇒ **luôn** trả `next_eligible_min` và UI **luôn** hiển thị — đây là tính năng UX cốt lõi của D; thiếu nó thì D-c/D-d mất phần lớn giá trị.

### 5.2 Xử lý finding soi (D)
| Mã | Xử lý |
|---|---|
| **D-P1** | SỬA ở §1.4 — đây là lỗ nguy hiểm nhất phía sản phẩm: `topic="bonus"` → lớp `policy` không có trần + `max_proactive_per_shift` bị bỏ qua ⇒ **client quên một query param nhận advisor KHÔNG GIỚI HẠN**; test #16 của D (lái topic demand tường minh) **không bắt được**. Thêm test C-08. |
| **D-D1** | SỬA ở §1.3 — cache khoá `(path, mtime_ns)`. |
| **D-B1** | **CHỐT CỨNG** (không để ngỏ): `topic_class` chỉ ghi vào `detail` khi `budget_mode != fifo`. Để implementer chọn nghĩa là chọn cái tiện, mà test C-01 là cổng an toàn của artifact 31–38. |
| **D-C1** | SỬA bằng ràng buộc arm: `last_decided_min` ghi **vô điều kiện** (kể cả `positioning`), và `positioning` commit từ `_standby_planner` — process SimPy **riêng** chạy trước `_actor_proc` tại mốc trùng timestamp chỉ vì thứ tự `env.process(...)`. ⇒ ở D-d **kết quả** (không chỉ telemetry) phụ thuộc thứ tự process. Arm D-d chỉ chạy với `count_positioning_in_budget` **cố định**, và phải báo độ nhạy theo thứ tự planner (dịch `bucket_min`). |
| **D-C2** | SỬA — `count_positioning_in_budget` thành **cờ chết** ở `no_global` nếu lớp `position` không có trần (`test_count_positioning_in_budget_flag_is_alive` tồn tại đúng để chống cờ chết). Arm D8 **phải** khai `class_caps.position` tường minh. |
| **D-N2** | ĐÍNH CHÍNH — `rest_window` 36 grant × **2′/grant** ⇒ ~72′ ⇒ `rest_defer_max_min: 120` **không ràng buộc** ngay cả ở `no_global`. Câu "D bỏ đúng cái duy nhất đang chặn liều" chỉ đúng cho `accept_lift`/`shift_plan`. Con số "≈70 thẻ/ca" giữ nhãn ASSUMPTION, **phải đo ở D1** trước khi diễn giải. |
| **D-N3** | KHAI RÕ — `UNKNOWN_TOPIC_CLASS = demand` là fail-safe **rỗng** khi `class_caps: {}`; chỉ D2/D3 làm nó thật. |
| **D-F1** | CHẤP NHẬN — như C-F1. |
| **D-B2** | ĐÍNH CHÍNH lo ngại của D: đã grep `tests/` + `ui/backend/tests/` — **không** test nào construct hay so-nguyên-object `CadenceVerdict`; mọi test đọc `.verdict`/`.reason`. Giữ bước grep pre-flight, đừng đặt budget cho nó. |
| **D-W1/W2** | SỬA bằng stop rule + nhãn (§8). |
| Product honesty | SỬA — `_SILENT_MSG["shift_budget_exhausted"]` (*"Hôm nay trợ lý đã nhắc đủ rồi"*) trở thành **lời nói dối** ở `no_global`; sửa copy **cùng lúc**, không để sau. |
| Không sửa `_note_shown` | GIỮ quyết định của D (lập luận đúng: `event_id` theo `(topic, bucket)` **khớp** đơn vị §1.10). |

### 5.3 Test riêng của D
`D-01` bảng verdict mặc định khớp từng ô snapshot cứng · `D-02` `no_global` bỏ qua `max_proactive` (`proactive_count=999` ⇒ PRESENT) · `D-03` trần lớp chỉ ràng buộc lớp mình · `D-04` trần cộng gộp mọi topic trong lớp · `D-05` topic lạ chịu trần demand · `D-06` bảng công thức `effective_class_cap` chốt cứng (r=1,0/L=540→9 · 0,5/540→4 · 0,5/239→**1** · 0,0/540→0 · 0,5/None→None · 1,0/59,999999999→1) · `D-07` reason + `next_eligible_min` (`class_cooldown` 140,0 · `global_cooldown` 125,0 · trần đếm ⇒ None) · `D-08` safety vẫn bypass mọi thứ ở `no_global` · `D-09` `class_overrides={'rest_window':'safety'}` bypass · `D-10` **không im lặng vĩnh viễn**: full run `no_global` + chỉ `min_gap_min_global=40` ⇒ số event reason ∈ {`shift_budget_exhausted`,`class_budget_exhausted`} = **0** · `D-11` decay: off ⇒ digest trùng; 0,10 ⇒ `followed` giảm đơn điệu theo `free` 5→3→0; coin **không** đổi giữa các mức decay · `D-12` ranh giới dismiss không rò qua cửa mới (chạy 2 test hiện có ở `no_global`) · `D-13` UI trần lớp thật sự nén (FastAPI, không unit test `evaluate`).

---

## §6. KẾ HOẠCH ĐO

### 6.1 Điều kiện HỢP LỆ của mọi arm (không đủ ⇒ kết quả bị TREO như artifact 31–35)
1. **Ghi PER-SEED** (lỗ hổng của artifact 37; artifact 38 đã làm đúng — theo nó).
2. Artifact JSON số thứ tự tiếp **39+** trong `research/audit/2026-07-27-current-state/`.
3. Cùng bộ kênh ON ở mọi arm trong một so sánh; **chỉ** đổi khối `cadence`.
4. Báo kèm `decision_adherence` per archetype so danh nghĩa — lệch > 0,02 ⇒ washout/double-dose sống lại ⇒ **treo kết quả**.
5. Báo `%phantom` của `advice_suppressed`: 3 kênh đã sửa R-08 = 0%; **`shift_plan` khai là "CHƯA KIỂM"**, không được khai 0% (bảng R-08 ghi "0% ma" là **hệ quả của việc không sửa code**, không phải phép đo).
6. Header artifact ghi: `budget_mode`, `charge_unit`, `advice.enabled`, `cadence.enabled`, `count_positioning_in_budget`, lưới dedupe telemetry, và **nguồn số baseline = artifact 38** (sửa **D-W2**: `no_global` phá bất biến "cadence ON ⇒ ≤6/ca" **theo thiết kế** ⇒ không ai được đọc một run `no_global` như một run "cadence ON").
7. Mọi Δ thừa kế `D-A3-01b` (advice NO-OP vẫn đếm `followed`) — ghi ở đầu artifact.

### 6.2 Khối seed (rời nhau, chống fit-trên-seed-đánh-giá)
| Dùng cho | Seed | n |
|---|---|---|
| Đã dùng: E5/artifact 38 | 4200–4299 | 100 |
| **E1 baseline + mọi arm so tiền** | **4400–4499** | 100 |
| B: fit ev cấp kênh (E-B0a) | 4500–4599 | 100 |
| B: fit ev theo bin (E-B0b, MRT) | 4600–4899 | 300 |
| Bit-identical / exact-repeat | 1000, 1001, 1002, 2000, 3160 | 5 |
`ValueBook.seed_block` ghi khối fit; bridge **fail loud** nếu `world.seed` nằm trong đó.

### 6.3 Arm — thứ tự chạy
**Giai đoạn 0 — ĐO TRƯỚC, KHÔNG so tiền (chạy xong mới được chạy gì khác):**
- **M1 `ladder-oracle`**: `budget_mode: ladder`, `max_proactive_per_shift = ∞`, quota/escrow/queue off, log **mọi** `advice_gate_trace`. Ba output bắt buộc: (a) **tỷ lệ ĐỤNG ĐỘ** = share tick có ≥2 proposal đủ điều kiện + ma trận đụng độ theo cặp topic; (b) **phân phối grant-per-bucket-30′** (đầu vào cho quyết định `per_opportunity_cap` của B — **B-D2**); (c) **tỷ lệ nén-MA của `shift_plan`** (đo được miễn phí vì `propose_shift_plan` gọi solver trước gate) ⇒ **đính chính `D-ĐA04-03`**.
  **Cổng:** tỷ lệ đụng độ thấp ⇒ toàn bộ cơ chế A bị **chặn trên ở ≈0đ** ⇒ báo đúng như vậy và **không chạy A1–A10**.
- **M2 `lanes_shadow`**: demand per-lane không dedupe. **Cổng:** ≥2 làn có demand ~0 ⇒ C1 chắc chắn chỉ là hạ trần ⇒ chỉ chạy C với `reserve_per_lane` đã hiệu chỉnh theo demand đo được.
- **M3 volume baseline**: thêm vào `src/gsm_sim/sim_metrics.py`: `cards_per_driver_shift` p50/p90/max, `cards_per_hour` p90, `share_of_shift_silenced`, `slots_spent_per_driver`, `reserved_slots_wasted`, `released_used`. **Không có bộ này thì đo được lợi mà không đo được cái mất** — lặp lại BUG-EVAL-ARGMAX tầng diễn giải.

**Giai đoạn 1 — đối chứng (n=100, 4400–4499, per-seed, ghép cặp theo SEED):**
- **NULL-0** = ĐA-07 (`shift_plan` OFF, cadence ON) — **đối chứng chính** cho cả 4.
- **BASE** = FIFO, 5 kênh nghiên cứu ON.
- **BASE-trim** = FIFO với `max_proactive_per_shift` = `slots_spent_per_driver` **thực đo** của arm cơ chế tương ứng (tổng quát hoá C0b đã sửa — **C-N1**) ⇒ tách "chia khéo hơn" khỏi "nói ít hơn".

**Giai đoạn 2 — cơ chế** (mỗi arm so **cả** BASE, BASE-trim **và** NULL-0):
A: `A1` ladder tối giản · `A2` +queue · `A3` +quota · `A4` queue+quota (**ô tương tác bắt buộc** — bài học 2×2) · `A5` reserve+rest_window→safety · `A6` escrow off · `A7` tiebreak=topic_order · `A9` aging grid · `A10` `shift_plan_interval_min ∈ {30, null}`.
B: `B0` τ≡0 + `plan_clock=consult` (tách "đổi đồng hồ" khỏi "đặt ngưỡng") · `B1` đầy đủ · `B1′` `plan_clock=gate` · `B2` `tau_scale ∈ {0; 0,5; 1; 1,5; 2; ∞}` · **`B3` = NULL-0 nội bộ** (chỉ câm kênh ev ≤ 0) · `B4` `per_opportunity_cap ∈ {1, null}` · `B6` hiệu chuẩn ngược.
C: `C1` mặc định · `C2` `late_release=false` · `C3` `pool_first` · `C5` `reserve=2` · `C6` `lane_priority` khác.
D: `D1` phản đề thuần (chỉ cooldown) · `D2` `class_caps.demand ∈ {1,2,4,6,∞}` · `D3` `min_gap_min_per_class.demand ∈ {0,10,20,40}` · `D4` `min_gap_min_global ∈ {0,20,40,60,100}` (**ô G=100 quan trọng nhất cả grid**: volume ≈ 6 thẻ/ca 600′ = **bằng** trần hôm nay nhưng **không** có im lặng vĩnh viễn ⇒ tách "cơ chế" khỏi "liều") · `D5` `class_caps_per_hour ∈ {0,25; 0,5; 1,0}` tách theo archetype (P1 3–4h vs P3 11–12h) · **`D6` break-even decay** × **`D7` đối chứng `fifo` cùng mức decay** (thiếu D7 ⇒ decay lẫn với mode ⇒ D6 vô nghĩa) · `D8` `count_positioning_in_budget` × `class_caps.position` tường minh.
Chung: **`X-charge`** = lưới 2×2 `charge_unit {call, decision_bucket}` × `{fifo, cơ chế thắng}` (câu "một suất là gì", và là arm PARITY duy nhất với UI).
**`SHIP-CONFIRM`**: `budget_mode` ≠ fifo trên ship config ⇒ phải **raise** (guard §1.2). Không raise ⇒ cổng an toàn hỏng ⇒ **dừng tất cả**.

### 6.4 PASS/FAIL nói TRƯỚC khi đo (chống HARKing)
Metric quyết định: **`net_mean_all`** Δ ghép cặp per-seed, bootstrap CI, n=100.
Một cơ chế được gọi là **đáng ship** chỉ khi **tất cả**:
1. Δ vs **BASE** có CI không chứa 0;
2. Δ vs **BASE-trim** có CI không chứa 0 (không phải chỉ hạ/nới liều);
3. Δ vs **NULL-0** có CI không chứa 0 (**vượt được một dòng YAML của ĐA-07**);
4. Δ **không** vượt vô lý trần ≈2,2k đ (§0.1) — vượt ⇒ điều tra là đang đo cái khác;
5. Không guardrail nào xấu SIG.
**Guardrail VETO (một cái đỏ ⇒ arm bị loại bất kể payout), báo TRƯỚC payout:** `served_rate` · `expired_n`/`dead_orders` · `orders_completed` · `gini_payout` · `HHI` · `battery_stranded` · station queue p95 · `rest_deferred_min` p95 · `net_mean_P1..P7` (không nhóm nào hại SIG, đặc biệt newbie p10) · **`#nói(positioning)` không được nhỏ hơn BASE** (**B-W1**) · `cards_per_driver_shift` p90 không vượt mức Cường tuyên bố chịu được (§7.1).

---

## §7. THỨ TỰ THI CÔNG + CHỖ PHẢI DỪNG XIN CHỦ DỰ ÁN

### 7.1 Ba phán quyết GIÁ TRỊ — dừng, hỏi, không đo thay
1. **`rest_window` là lớp `safety` hay `demand`?** Đặt nó `safety` là cấp quyền bypass mọi cổng — phán quyết đạo đức (liên quan nguyên tắc *"sức khoẻ tài xế không phải biến để tối ưu"*). Spec để nó là **cấu hình**, mặc định `demand`, và arm A5/D9 **định giá** phán quyết bằng đồng. **Cấm** chọn "cái nhiều tiền hơn".
2. **`cards_per_driver_shift` p90 chịu được là bao nhiêu?** Đây là Q-09. Sim cho **đường cong** (arm D4/B2/A12); **điểm** trên đường cong là phán quyết người. Phải hỏi **trước** khi chạy, không sau.
3. **Có ý định bật lại kênh nào ở production không?** (§4.2-4). Nếu KHÔNG, thì cả 4 cơ chế là **hạ tầng ĐO**, không phải tiền đang mất: ship config tắt bằng 3 khoá (§0.3) ⇒ FIFO tốn ≈0đ ⇒ giá trị production của E1 = 0đ. Điều này phải nói thẳng ở đầu mọi artifact.
Phụ: **xác nhận re-baseline hình** cho thay đổi `dashboard.py::_het_ns` (§1.9) — Cường phán V-18 trên hình.

### 7.2 Thứ tự
1. **E1-CORE** (§1) + test C-01…C-13. **C-01 đỏ ⇒ dừng cycle**, không đi tiếp.
2. Telemetry `advice_gate_trace` + metric volume (M3). *(Không có bước này thì mọi metric đếm sai ~10× và không đo được cái mất.)*
3. **M1 ladder-oracle** + **M2 lanes_shadow** ⇒ đính chính `D-ĐA04-03`, chốt `per_opportunity_cap`, và **quyết định có chạy A/C tiếp hay không**.
4. **D** trước (rẻ nhất, không cần `ev`, và phát hiện trung tâm của nó — sim không có chi phí chú ý — quyết định ý nghĩa của cả 3 cơ chế còn lại). Chạy D1 + **D6/D7 break-even decay**.
5. **C** (cũng không cần `ev`), với `reserve_per_lane` hiệu chỉnh theo M2.
6. **A** (cần lớp + tie-break, không cần tiền), chỉ nếu M1 cho tỷ lệ đụng độ đáng kể.
7. **B** cuối (cần E-B0a/E-B0b, tốn nhất, và chịu vòng tròn hiệu chuẩn). Chỉ chạy nếu `J_effective ≥ 4`.
8. Visual gate: launch dashboard cho Cường ít nhất **seed 1000** + seed có actor tệ nhất, chờ verdict trước commit/push.

---

## §8. RỦI RO "TỆ HƠN FIFO" — STOP RULE PRE-REGISTER

Đăng ký trước, không chọn sau khi thấy số.

| Cơ chế | Đường tệ hơn cụ thể | STOP RULE |
|---|---|---|
| **A** | Khai tử `due()` ⇒ `shift_plan` (kênh **−2 259đ SIG**, served −0,68đp, +8 đơn hết hạn) đi từ 24 lên 36 grant/ca 12h ⇒ ladder chỉ cho kênh tệ nhất nói to hơn. | Arm nào có `#grant(shift_plan) > BASE` ⇒ **loại trước khi xem payout**. |
| **A** | Tỷ lệ đụng độ ≈0 ⇒ thang ưu tiên đáng ≈0đ. | M1 cho đụng độ dưới mức đáng kể ⇒ **dừng A**, báo đúng như vậy. |
| **B** | τ câm `positioning` — kênh dương SIG duy nhất (+6.016đ trên ~19 lượt/ca ⇒ ~300đ/suất, τ đầu ca dễ vượt). | `#nói(positioning) < BASE` ⇒ arm **vô hiệu**. |
| **B** | Vòng tròn hiệu chuẩn: `ev̂` là trung bình trên tập suất FIFO, không phải cận biên; `accept_lift` bão hoà sau 2 liều ⇒ ev̂ dương CI hẹp **sai chiều cận biên** ⇒ B tự tin chi suất 3–4 cho kênh đã hết tác dụng. **Không test nào đỏ.** | `seed_block` fail-loud + `slot_index_channel` bắt buộc + **B6**: residual (`Δnet_thực − ev_spoken`) âm và tăng theo số suất ⇒ sách sai ⇒ **dừng B**. |
| **B** | `J_effective ≤ 3` ⇒ bảng DP là trang trí. | **dừng B**. |
| **B** | `B3 ≈ B1` (CI chồng) ⇒ toàn bộ giá trị của B là "tắt shift_plan" = NULL-0. | báo **B không đáng ship**, dù đã dựng đầy đủ. |
| **C** | 4 làn × 1 với `rest_window` 0 lần + `accept_lift` bão hoà 2 liều ⇒ ~2 suất bảo lưu chết; `late_release` chỉ nhả sau 75% ca ⇒ **75% đầu ca chạy ngân sách hiệu dụng 4**. C1 "thắng" vì hạ trần, không vì chia khéo. | `reserved_slots_wasted ≥ 1,5/người` **hoặc** `released_used ≈ 0` ⇒ **loại C bất kể payout**. Và bắt buộc so **BASE-trim ở slots thực đo**. |
| **D** | Tautology mô hình: `DEFAULT_ADHERENCE` là **hằng số theo archetype**, không suy giảm theo số thẻ ⇒ sim **không có khả năng sinh ra cái hại mà ngân sách tồn tại để ngăn** ⇒ "cho nhiều thuốc hơn" buộc phải ra tốt hơn. Đường cụ thể: `accept_lift` chạm `accept_lift_max 0.15` sớm ⇒ vượt `bonus_min_acceptance` ⇒ `day_bonus` nhảy từ 0 lên bậc thưởng ⇒ hiệu ứng vách đá áp đảo bảng. Hỏng ở **mặc định**, lần chạy đầu tiên. | **Break-even decay ≤ 0,05/thẻ ⇒ KHÔNG SHIP D**, bất kể Δ ở D1 to bao nhiêu. |
| **D** | D1 không siết `shift_plan` ⇒ payout dương to **đồng thời** served −0,68đp và expired +7,7 SIG (đúng dấu artifact 38). | served/expired là **STOP CỨNG**, per-seed cùng n, **báo trước payout**. |
| **D** | Ô D4 G=100 (cùng volume, không im lặng vĩnh viễn) không khác BASE SIG ⇒ cái D thu về là **nhiều thẻ hơn**, không phải cơ chế tốt hơn ⇒ câu hỏi thật là Q-09, không phải D. | báo đúng như vậy. |
| **Cả 4** | `spoken_by_topic` (hoặc trường tương đương) không được nuôi ở nửa UI ⇒ sản phẩm chạy không trần trong khi sim báo "trần hoạt động tốt". Xác suất cao vì UI **dựng lại** memory từ `AdviceEventLog` bằng hàm khác hẳn sim (cùng họ Lỗi #12 và F1). | test C-07 + C-08 + C-05 phải là **test FastAPI thật**, không unit test `evaluate`. |
| **Cả 4** | Rò tác dụng phụ khi tách propose/commit — không crash, test xanh, payout dịch vài trăm đồng, adherence lệch vài đp. | test **C-01 + C-02 + C-12** là bất khả xâm phạm; ai bỏ chúng thì chế độ hỏng này sống 100%. |

**Câu phải in lên mọi artifact E1:** *Trần trên của mọi cơ chế chia ngân sách ≈ 2,2k đ/người/ca (artifact 38, CI[1 077 · 3 372]), và +2 259đ trong đó đã được ĐA-07 lấy bằng một dòng YAML. E1 đo xem có gì còn lại ngoài phần đó — và ở config ship hôm nay giá trị production của cả bốn cơ chế là 0đ.*