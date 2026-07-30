# Hợp đồng dữ liệu phản thực — "nếu chúng ta có data thật"

**Task:** `T-047` · **Ngày:** 2026-07-30 · **Trạng thái:** đề xuất thiết kế (chưa implement, chưa tạo file schema nào)
**Nguồn chỉ thị:** `tracking/QUYET-DINH-2026-07-30-nam-diem.md` §Điểm 3 · `tracking/TODO.md` T-047

---

## §0. Task này là gì, và KHÔNG là gì

Cường chốt 2026-07-30, nguyên văn:

> *"MOCK data, giả sử chúng ta có data thật — chia thành 1 task mới, cần research kĩ càng, bạn tự chốt
> schema hợp lý. Tôi cũng đã nói rõ sẽ không có data thật từ GSM hay được cung cấp gì thêm."*

**KHÔNG phải:** một yêu cầu dữ liệu gửi ai. GSM đã cấp **schema** (tên cột của 9/13 bảng) và sẽ
**không cấp thêm gì**. Mọi dòng *"XIN GSM"* trong `docs/data-catalog/gsm-data-catalog.csv` và mọi
`x-availability: "TBC-với-GSM"` trong `schemas/l1r/*` là **nhánh chết** — §2.6 đóng chúng.

**LÀ:** một đặc tả phản thực gồm bốn phần, và phần thứ ba là phần có giá trị nhất:

1. **Hợp đồng dữ liệu** — nếu có data thật thì hạt, khoá, đơn vị, nguồn của từng trường là gì (§2).
2. **Bản đồ MOCK↔THẬT** — MOCK đang thay từng trường bằng cái gì (§3).
3. 🔴 **Kết luận nào của dự án KHÔNG sống nổi qua khoảng cách MOCK↔THẬT** (§4).
4. **Cơ chế CODE chống tự lừa** — không phải lời hứa, mỗi cái một hàm/test (§5).

Lý do phần 3 là phần đáng nhất: nó là thứ bảo vệ được trước hội đồng, và là thứ ngăn chúng ta tự lừa.
Repo này đã ba lần tuyên bố xong rồi bị soi độc lập bắt lỗi làm sai mọi con số
(`gsm-independent-review-before-reporting-numbers`), và một lần báo số sai gấp đôi cho Cường vì arm
đối chứng không sạch (`DET-01`, UPDATE-099). §4 và §5 tồn tại để chuyện đó không tái diễn.

### 0.1 Spec này tổng hợp từ đâu

Ba thiết kế đối đầu đã được chấm bằng hai lăng kính. Spec này **không** chọn một cái rồi bỏ hai cái:

| Lấy gì | Từ đâu | Vì sao |
| --- | --- | --- |
| **Xương sống hạt `ngày × băng giờ`** cho tiền; quarantine `trips` | `star-warehouse` (76đ) | Nó là hạt GSM **thật sự phát ra** — tôi tự đo lại: `driver_orders_rush_hours` tách `_rush_hour`/`_normal_hour` và invariant băng→tổng đúng **100%** trên cả `total_order`, `total_fee`, `commission` (§1.2). Không phải hạt ta phát minh. |
| **Cổng chứng thư** (`measurement_claim`) là đường ra DUY NHẤT của mọi con số; refusal-as-data; khai tử `TBC-với-GSM`; nhận MDS/TLC ở mức **đặt tên**, không nhận hạt | `event-sourced` (70đ) | Ý tưởng mạnh nhất của cả ba: biến ba luật §5 CLAUDE.md từ quy ước tác giả thành **điều kiện validate**. Không có nó, §5 chỉ là lời hứa. |
| **Tách `source` thành BA TRỤC vuông góc** (`dataset_label` / `grain_tier` / `provenance.kind`) | `hybrid-contract` (58đ) | Insight cấu trúc tốt nhất trong cả ba, dù thiết kế đó điểm thấp nhất. Hợp đồng chỉ-theo-tầng **không bắt được vòng tròn**: 7 tham số đo-từ-sim-nạp-lại-sim nằm ở tầng **cao nhất** về độ mịn. Trục `provenance.kind = SELF_FIT` là thứ duy nhất bắt chúng. |

**Và spec này sửa 9 lỗi mà cả ba thiết kế đều mắc hoặc chỉ mắc một phần.** Mọi lỗi dưới đây do tôi tự
đo lại trong phiên này, không trích từ bản chấm — §1.4 liệt kê đủ.

### 0.2 Nhãn chứng cứ dùng xuyên spec

| Nhãn | Nghĩa |
| --- | --- |
`[ĐO]` | tôi tự chạy trên file gốc trong phiên này; script tái lập ở §9.3 |
`[ĐỌC]` | tôi tự mở file gốc trong repo trong phiên này |
`[KẾ-THỪA]` | từ artifact/UPDATE của repo, tôi **chưa** tự tái lập — luôn ghi rõ nguồn |
`[SUY]` | suy luận của tôi |

---

## §1. Sự thật hiện trạng

### 1.1 13 bảng GSM: cái gì có, ở hạt nào

`[ĐO]` `grep -c "CHƯA CÓ CỘT" docs/data-catalog/gsm-data-catalog.csv` = **4**.

| # | Bảng GSM | Hạt thật | Cột | Vai trò trong hợp đồng |
| --- | --- | --- | --- | --- |
| 1 | `driver_orders_rush_hours` | **driver × ngày × băng giờ** | 14 thật | **XƯƠNG SỐNG TIỀN** (§2.2) |
| 2 | `driver_income_daily` | driver × ngày | 8 thật | tiền cấp ngày; đối soát |
| 3 | `driver_statistic_daily` | driver × ngày | 15 thật | acceptance/cancel — **không cắt được trong ngày** |
| 4 | `driver_online_hours_sap_id` | driver × ngày | 10 thật | `online_time` một vô hướng/ngày |
| 5 | `driver_bike_stoppoints` | driver × ngày | **4 thật** | ⚠ chỉ `total` + `_rush_hour`, **không có `_normal_hour`** |
| 6 | `kpi_driver_platform_calculator_gbq` | driver × tuần | 21 thật | ⚠ **không có cột target/threshold nào** |
| 7 | `public_driver_hex_tracking` | driver × lần-vào-hex | 19 thật | **fact hạt-giờ THẬT duy nhất** |
| 8 | `public_mission` | 1 mission | 28 thật | reference |
| 9 | `public_mission_earn_history` | 1 lần chạm mốc | 21 thật | có `order_time`/`complete_time` |
| 10 | `trips` | 1 cuốc | **0 cột biết** | **QUARANTINE** — nuôi 4 solver |
| 11 | `driver_penalization_ATA` | 1 khoản trừ | **0 cột biết** | QUARANTINE |
| 12 | `public_frauds` | 1 cờ | **0 cột biết** | QUARANTINE |
| 13 | `public_user_mission_progress` | driver × mission × ngày | **0 cột biết** | QUARANTINE |

**Ba sự thật cấu trúc, không phải sự thật về quyền truy cập:**

- 5 bảng hạt **NGÀY**, 2 bảng hạt **TUẦN**, 1 reference. Chỉ **3** bảng vừa có cột thật vừa có
  timestamp; chỉ **1** trong đó nói về hành vi cấp phút (`public_driver_hex_tracking`).
- **Một cuốc bị TỪ CHỐI không sinh dòng ở bất kỳ bảng nào.** Ta chỉ có
  `total_request_calculate_accept − accepted_count` = **số** lần từ chối trong ngày, **không có thời
  điểm**. Không có `go_online`/`go_offline` — chỉ `online_time`. 140 cột đã biết không có cột nào mang
  timestamp của một lời mời hay một lần bật/tắt app.
- **Không bảng GSM nào ghi việc tài xế ĐÃ ĐƯỢC XEM lời khuyên.** ⇒ nửa "advisor nói gì" bắt buộc là
  nguồn thứ 14, **tài sản của ta**, không phải thứ để xin.

### 1.2 Điểm neo phải nói trước mọi thứ khác

`[ĐO]` trên `data/mock/realdata-v1/driver_orders_rush_hours.parquet` (12.805 dòng, 150 driver, 90 ngày):

```
(total_order_rush_hour + total_order_normal_hour == total_order)  →  100,0%
(total_fee_rush_hour   + total_fee_normal_hour   == total_fee)    →  100,0%
(commission_rush_hour  + commission_normal_hour  == commission)   →  100,0%
```

⇒ **Hạt "ngày + băng giờ" không phải tôi phát minh. Nó là hạt GSM thực sự phát ra**, và là **độ mịn
dưới-ngày DUY NHẤT mà cột tiền thật của GSM có.** Toàn bộ §2 đứng trên sự thật này.

⚠ Nhưng `driver_bike_stoppoints` `[ĐO]` chỉ có `total_stoppoints` + `total_stoppoints_rush_hour` —
**không có `_normal_hour`**. Băng `normal` của bảng đó là **DERIVED bằng phép trừ**, không phải cột
GSM. Hợp đồng phải dán nhãn khác nhau cho hai bảng này (§3.2).

### 1.3 Cái gì hôm nay là MOCK

Bộ đang dùng: `data/mock/realdata-v1/` `[ĐỌC]` manifest — `label=MOCK`,
`generator=gsm_core.mockgen.realdata v4`, `engine_commit=d325055`, `days=90`, `seed_base=7000`,
`start_date=2026-07-01`, **thiếu `generated_at`**.

| `[ĐO]` | Số |
| --- | --- |
| `trips` | 167.575 dòng · **51,54%** `pickup_h3` là token bịa `8amock##` |
| `public_driver_hex_tracking` | 1.371.758 dòng · **90/150** driver (40% roster không có byte vị trí nào) · `campaign_id` NULL **95,01%** · trung vị `stay_duration_seconds` **62s** |
| 5 bảng daily | 12.805 dòng mỗi bảng · `online_time` TB **9,675h**, max **21,75h**, **10,30%** ngày >14h |
| `kpi` weekly | 2.090 · `earn_history` 6.837 · `progress` 261 · `penalization` 75 · `frauds` 138 · `mission` 6 |
| Suite hiện hành | `[ĐO]` `pytest --collect-only` = **799 test** (CLAUDE.md ghi ~707 — số cũ) |

⚠ HEAD hiện tại ≠ commit sinh data (`d325055`) ⇒ **bộ parquet có thể đã lạc hậu so với engine**. Mọi
số `[ĐO]` ở trên là số của **bộ mock này**, không phải số của GSM, và phải regen trước khi dùng làm
chứng cứ chính thức.

### 1.4 Chín lỗi tôi sửa so với ba thiết kế đối đầu

Tất cả do tôi tự đo/đọc lại. Đây là danh sách *sửa*, không phải danh sách *phê*.

| # | Cả ba (hoặc phần lớn) nói | `[ĐO]`/`[ĐỌC]` sự thật | Hệ quả lên thiết kế |
| --- | --- | --- | --- |
| 1 | `payout/gross` "chỉ 3 giá trị, **phương sai 0**" | **9.816** giá trị phân biệt (jitter do `round()`); làm tròn 4dp mới ra đúng 3 `{0,25; 0,75; 0,90}`. Var **toàn cục = 0,0246 > 0**; var **trong-tài-xế** max = **1,89e-11 ≠ 0**; số giá trị phân biệt trong một tài xế lên tới **84** | Gate `var > 0` **PASS** (sai); gate `n_distinct ≤ 3` **không fire** (9.816); gate `var == 0` **không fire**. §5.3 định nghĩa lại gate cho đúng |
| 2 | `reached_target` "tự phủ định bằng dữ liệu cùng dòng" | `target_hex` **100%** là token 8 ký tự `8amock##`; `current_hex` **100%** là H3 15 ký tự hợp lệ ⇒ `current==target` = 0% là **lệch KIỂU**, không phải bất đồng ngữ nghĩa | "agree_rate" là gate **FAIL vĩnh viễn không mang tin**. Thay bằng gate *reject-rate*; `reached_target` dán **UNVERIFIABLE** (§3.4) |
| 3 | "`reached_target` True ở 59,9% **dòng**" | 59,9% của **68.493** dòng CÓ target = **3,0%** của 1.371.758 dòng toàn bảng | Mọi tỷ lệ phải mang mẫu số tường minh (§5.1) |
| 4 | fact hạt-giờ: `dwell_seconds_sum` `maximum: 3600` | Rollup theo `(driver, ngày, giờ vào, ô)` = **1.200.943** dòng; **8.000** (0,666%) vượt 3.600s; max **22,88 giờ**; nén chỉ **12,45%** | Trần 3600 **loại dòng của chính fact hạt-giờ duy nhất**. §2.4 sửa bằng cách đặt tên trường theo hạt thật + bỏ trần |
| 5 | ngưỡng "idle" 300s là ổn | Σ dwell≥300s **vượt `online_time`** ở **746/8.022** driver-day (**9,3%**), tệ nhất vượt **19,57 giờ** | `BUG-PI5b-01` còn sống. §5.4 thêm invariant; cấm gọi là "idle" |
| 6 | `public_user_mission_progress` có cột thật; kênh `mission` "✅ đo được" | Nó là **1 trong 4** bảng `CHƯA CÓ CỘT` | Kênh `mission` **không sạch** — tựa một phần lên bảng engineered (§6.2) |
| 7 | `resolve_cost_params` có 5 số hạng chi phí | `[ĐỌC]` `src/gsm_core/policy.py` trả **đúng 2**: `{battery, cash_per_km}`. **Không có** `fixed_daily`, `maintenance` | Gate `estimated_net` phải kiểm **phủ trọn enum**, không chỉ "≥1 term ACTIVE" (§6.3) |
| 8 | kiểu `Money` NamedTuple chặn được trộn tiền | `[ĐO]` tôi chạy: `max([Money("ESTIMATED_NET",999999), Money("GROSS",1)])` → **`GROSS 1`** (tuple so `kind` theo chữ trước). `Money("GROSS",100000) < Money("PAYOUT",75000)` → **True**. `Money(...)==("PAYOUT",75000)` → **True**. `a*2` → `tuple`, guard bốc hơi | Trong repo đã có **`BUG-EVAL-ARGMAX`**, một kiểu tiền mà `max()` sắp theo tên kind **tệ hơn không có kiểu**. §6.4 dùng frozen dataclass `order=False` |
| 9 | adherence "76,9% vs 53,6%" | `[ĐỌC]` UPDATE-099: đó là số **TRƯỚC ĐA-04**. Sau keyed coin: **68,1% vs 67,6%** (lệch 0,5đp, washout đã chết) | Mọi chỗ trích 76,9/53,6 như hiện hành là **số cũ** |

Thêm hai `[ĐỌC]` làm vỡ tuyên bố tuyệt đối của thiết kế `event-sourced`:

- `schemas/l3/session_summary_input.schema.json:45` **đã có `estimated_net_vnd`** ⇒ không được phát
  biểu *"estimated_net không tồn tại ở tầng dữ liệu"*; phải **di trú** (§6.1).
- `schemas/l1/app_event.schema.json` **đã có** `kind ∈ {go_online, go_offline, offer_shown, accept,
  decline, cancel, complete}`, và `schemas/l2i/inferred_activity.schema.json` **đã có**
  `label ∈ {rest_likely, charging_likely, relocating, idle_wait}` ⇒ đề xuất entity `offer_event` /
  `session_event` / `guard/rest_observation` là **nhân bản một sự thật đã có tên** (họ lỗi `T-046`).
  Hợp đồng này **không** tạo chúng.

Và một ràng buộc kỹ thuật `[ĐỌC]`: `src/gsm_core/schema_registry.py:143` dựng
`Draft202012Validator(...)` **không có `format_checker`** ⇒ mọi `"format": "date-time"` chỉ là tài
liệu. Lớp chặn thật là `pattern` + parse tại boundary.

---

## §2. Hợp đồng dữ liệu được chốt

### 2.1 Ba trục thay cho một trường `source`

`[ĐỌC]` hôm nay `source` tồn tại ở **hai enum không khớp nhau**:

- `schemas/README.md:29` → `MOCK | REAL | ESTIMATED | COARSE | INFERRED`
- `schemas/l3/market_state_view.schema.json:43` → `MOCK | REAL | PROXY | ESTIMATED | EXTERNAL`

Một trường đang gánh **ba câu hỏi khác nhau**: *dữ liệu có thật không · dẫn xuất bằng cách nào · mịn
cỡ nào*. Gộp ba trục vào một enum chính là chỗ ranh giới rò: một view ghi `source: "REAL"` vẫn có thể
mịn hơn nguồn của nó mà không ai phát hiện.

```
dataset_label   : MOCK | REAL                      ← KHÔNG có giá trị "MIXED". Trộn = lỗi cứng.
grain_tier      : E0 | E1w | E1 | E2 | E3 | E4 | E5 ← tầng/độ mịn của bằng chứng
provenance.kind : MEASURED_OUTER | MEASURED_INNER | POLICY_RULE | DERIVED
                | EXTERNAL_PROXY | SELF_FIT | ENGINEERED_GUESS | RNG_NOISE
```

`source` cũ **giữ lại**, `deprecated_since: "2026-07-30"`, dẫn xuất máy móc từ ba trục mới để
consumer cũ không vỡ (`schemas/README.md` quy định giữ ≥1 chu kỳ khi bỏ field).

**Trục thứ ba là trục mà hợp đồng chỉ-theo-tầng KHÔNG bắt được**, và là lý do tôi lấy nó từ thiết kế
điểm thấp nhất: `accept_logit_center_vnd = 21.200` được **đo từ chính sim rồi nạp lại vào sim**
`[KẾ-THỪA` UPDATE-081`]`. Nó nằm ở tầng **cao nhất** về độ mịn nhưng là **vòng tròn**. Chỉ
`provenance.kind = SELF_FIT` gọi được tên nó.

### 2.2 Bậc thang bằng chứng

| Tier | Hạt | Nguồn | Có trong production? |
| --- | --- | --- | --- |
`E0` | không-thời-gian, versioned | `l0/policy_bundle` — **RULE, không phải data** | ✅ ta sở hữu |
`E1w` | driver × tuần | 2 bảng tuần | ✅ (giả định có data thật) |
`E1` | driver × ngày (**× băng giờ** cho tiền) | 5 bảng ngày | ✅ |
`E2` | driver × lần-vào-hex | **chỉ** `public_driver_hex_tracking` | ⚠ có, nhưng rủi ro hạt (§9.1) |
`E3` | `decision_id` (bucket 30′) / event | `advisor/advice_lifecycle_event` — **TA TỰ SINH** | ✅ **luôn có, không cần xin ai** |
`E4` | decision point **có `p_t`** | randomization | ❌ **chưa có cơ chế** (§6.5 / §8.1) |
`E5` | tick 1′, ground truth | `gsm_sim` | ❌ **cấm dùng cho claim production** |

### 2.3 Sơ đồ thực thể

```
┌ TẦNG NGOÀI ─ đúng những gì GSM có ─ ĐÓNG BĂNG, không thêm cột ─────────────────┐
│  schemas/l1r/* (13 entity, ĐÃ TỒN TẠI — không sửa; là mirror bảng GSM)          │
└────────────────────────┬───────────────────────────────────────────────────────┘
                         │ ingest: as_of_cut + H3 validate + reject counting
                         ▼
┌ VÙNG DW (mới) ─ schemas/dw/{fact,dim,meta}/ ───────────────────────────────────┐
│                                                                                 │
│  F1  driver_day_band        (driver × ngày × băng)   ◀ XƯƠNG SỐNG TIỀN  §2.2    │
│  F2  driver_day_ops         (driver × ngày)                                      │
│  F3  driver_day_stop_band   (driver × ngày × băng)   ⚠ normal = DERIVED         │
│  F4  driver_hour_cell       (driver × ngày × giờ × ô) ◀ fact hạt-giờ THẬT duy nhất│
│  F5  driver_week_kpi        (driver × tuần)          ⚠ không có cột target       │
│  F6  advice_exposure        (driver × ngày × băng × kênh) ◀ cầu nối advice↔tiền  │
│  F7  day_net_estimate       (driver × ngày × cost_version) ◀ HÔM NAY 0 DÒNG     │
│  F8  day_wellbeing_observable (driver × ngày)        ◀ GUARDRAIL_ONLY  §7        │
│                                                                                 │
│  D1  driver (SCD2) · D2  date · D3  hour_band (SCD2, ĐỊNH NGHĨA CỦA TA)          │
│  D4  h3_cell · D5  advice_channel · D6  policy_version · D7  cost_model_version  │
│                                                                                 │
│  M1  field_provenance   ◀ bản đồ MOCK↔THẬT dạng DỮ LIỆU  §2.5                   │
│  M2  ingest_reject · M3  data_quality_check · M4  grain_capability               │
└────────────────────────┬───────────────────────────────────────────────────────┘
                         ▼
┌ QUARANTINE ─ schemas/dw/quarantine/ ─ 4 bảng 0-cột-biết ───────────────────────┐
│  Q1 trip_raw · Q2 penalty_event · Q3 anomaly_flag · Q4 mission_progress         │
│  KHÔNG có FK tới dim conformed nào. CẤM chạm đường tiền (test §5.5)             │
└────────────────────────┬───────────────────────────────────────────────────────┘
                         ▼
┌ CỔNG RA DUY NHẤT ─ schemas/advisor/measurement_claim ──────────────────────────┐
│  Mọi con số tới mắt người (tài xế · nội bộ · hội đồng) phải có một chứng thư.   │
│  Không chứng thư ⇒ KHÔNG được render.                             §2.6, §5      │
└─────────────────────────────────────────────────────────────────────────────────┘

  ╔ E5 SIM_ONLY ─ MỘT CHIỀU: chỉ ra claim có audience=internal_sim. Không có đường về ╗
```

**Thay đổi kiến trúc duy nhất:** `src/gsm_core/features/from_l1r.py` thôi đọc trực tiếp 13 bảng; nó
đọc DW. `[ĐỌC]` hôm nay `from_l1r.py` **không có consumer production nào** (grep chỉ ra `tests/`) ⇒
đổi nền bây giờ là rẻ nhất nó sẽ từng rẻ.

### 2.4 JSON Schema — F1 `driver_day_band` (xương sống tiền)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gsm-driver-agent/schemas/dw/fact/driver_day_band",
  "title": "driver_day_band",
  "description": "XƯƠNG SỐNG TIỀN. Hạt: 1 dòng = (tài xế × ngày × băng giờ). Nguồn duy nhất: driver_orders_rush_hours (14/14 cột THẬT). Một dòng GSM sinh ĐÚNG 2 dòng fact (rush, normal); dòng TOTAL của GSM KHÔNG lưu — nó là SUM và dùng làm invariant ingest (ĐO: khớp 100% trên 12.805 driver-day). Chỉ chứa ngày ĐÃ ĐÓNG.",
  "type": "object",
  "x-grain": "driver_key × date_key × hour_band",
  "x-natural-key": ["driver_key", "date_key", "hour_band"],
  "x-gsm-source-table": "gsm-data-prod.M_DRIVER_KPI_REWARD.driver_orders_rush_hours",
  "x-ingest-invariants": [
    { "id": "INV-BAND-SUM-ORDERS", "expr": "SUM(orders_n) OVER (driver_key,date_key) == GSM.total_order", "runner": "dw.invariants.band_sum", "vacuous_on_mock": false },
    { "id": "INV-BAND-SUM-GROSS",  "expr": "SUM(gross_vnd) OVER (driver_key,date_key) == GSM.total_fee",  "runner": "dw.invariants.band_sum", "vacuous_on_mock": false },
    { "id": "INV-BAND-SUM-PAYOUT", "expr": "SUM(payout_vnd) OVER (driver_key,date_key) == GSM.commission","runner": "dw.invariants.band_sum", "vacuous_on_mock": false },
    { "id": "INV-MONEY-ADD",       "expr": "gross_vnd == payout_vnd + platform_vnd", "runner": "dw.invariants.row_identity", "vacuous_on_mock": true,
      "vacuous_reason": "ĐO: mock ĐỊNH NGHĨA revenue_not_relate_driver := gross - commission, khớp 12.805/12.805 dòng. Invariant PASS mà không chứng minh gì. CẤM trích làm bằng chứng chất lượng." },
    { "id": "INV-CLOSED-DAY",      "expr": "date_key <= dim_date.last_closed_date", "runner": "dw.invariants.closed_day", "vacuous_on_mock": false }
  ],
  "properties": {
    "driver_key":     { "type": "string", "pattern": "^[0-9a-f]{32}$",
      "x-unit": "id", "x-provenance": "DERIVED", "x-gsm-source": "driver_orders_rush_hours.driver_id",
      "description": "HMAC-SHA256(pepper, driver_id) rút 32 hex. driver_id THÔ không persist (§7)." },
    "driver_key_era": { "type": "string", "x-unit": "id", "x-provenance": "OURS_PRODUCT",
      "description": "Thế hệ khoá. Rotate pepper ⇒ era mới ⇒ join xuyên era FAIL TƯỜNG MINH, không âm thầm sinh tài xế ma (không có era, rotate biến 150 tài xế thành 300 và mọi phân phối cấp người sai mà không ai biết)." },
    "date_key":       { "type": "string", "format": "date",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$",
      "x-unit": "date", "x-provenance": "MEASURED_OUTER", "x-gsm-source": "driver_orders_rush_hours.local_date",
      "description": "Ngày địa phương UTC+7. pattern BẮT BUỘC vì registry không có format_checker." },
    "hour_band":      { "type": "string", "enum": ["rush", "normal"],
      "x-unit": "enum", "x-provenance": "MEASURED_OUTER",
      "x-gsm-source": "hậu tố cột GSM (_rush_hour / _normal_hour)" },
    "hour_band_def_version": { "type": "string", "pattern": "^band-\\d+\\.\\d+\\.\\d+$",
      "x-unit": "version", "x-provenance": "OURS_PRODUCT",
      "description": "FK dim_hour_band. BẮT BUỘC vì THÀNH VIÊN của băng là ĐỊNH NGHĨA CỦA TA, không phải của GSM." },
    "orders_n":       { "type": "integer", "minimum": 0, "x-unit": "đơn",
      "x-provenance": "MEASURED_OUTER", "x-gsm-source": "total_order_{band}",
      "x-semantics-unknown": true,
      "description": "⚠ 'đơn hoàn thành' hay 'đơn tính tiền'? Không cột nào trong 14 cột nói rõ. GSM sẽ không xác nhận." },
    "gross_vnd":      { "type": "integer", "minimum": 0, "x-unit": "vnd",
      "x-money-kind": "GROSS", "x-provenance": "MEASURED_OUTER", "x-gsm-source": "total_fee_{band}",
      "description": "VND NGUYÊN (không float tiền). TIỀN KHÁCH TRẢ. Định nghĩa: specs/money-definitions/v1.md#gross" },
    "payout_vnd":     { "type": "integer", "minimum": 0, "x-unit": "vnd",
      "x-money-kind": "PAYOUT", "x-provenance": "MEASURED_OUTER", "x-gsm-source": "commission_{band}",
      "description": "TIỀN TÀI XẾ NHẬN (MDS: driver_trip_pay; TLC: net of commission/surcharges/taxes, KHÔNG gồm tolls/tips). ⚠ Tên GSM 'commission' NGƯỢC nghĩa thông thường: nó là phần TÀI XẾ. Căn cứ cách đọc này: sự tồn tại của revenue_not_relate_driver như một cột RIÊNG. Đây là cách đọc CÓ THỂ SAI và không test nào bắt được — xem §9.2." },
    "platform_vnd":   { "type": "integer", "x-unit": "vnd",
      "x-money-kind": "PLATFORM_TAKE", "x-provenance": "MEASURED_OUTER",
      "x-gsm-source": "revenue_not_relate_driver_{band}",
      "description": "KHÔNG có minimum: 0. Trên data thật, trợ giá/incentive có thể làm payout > gross ⇒ take ÂM là chuyện thường trong ride-hailing. Kẹp ≥0 sẽ fail cứng hoặc âm thầm che incentive." },
    "money_definition_version": { "type": "string", "pattern": "^money-\\d+\\.\\d+\\.\\d+$",
      "x-unit": "version", "x-provenance": "OURS_PRODUCT" },
    "dataset_label":  { "type": "string", "enum": ["MOCK", "REAL"], "x-unit": "enum" },
    "ingest_run_id":  { "type": "string", "x-unit": "id",
      "description": "{generator}@{engine_commit}[+dirty]#{generated_at}" },
    "schema_version": { "const": "1.0.0" }
  },
  "x-partition-rule": "Partition theo (dataset_label, date_key). Một partition chứa hai dataset_label = FAIL ingest.",
  "x-forbidden-properties": [
    "acceptance_rate", "cancellation_rate", "fulfillment_rate",
    "payout_ratio", "driver_share",
    "estimated_net_vnd", "net_vnd", "profit_vnd", "revenue_vnd", "income_vnd", "amount_vnd",
    "hour", "hour_local", "online_minutes",
    "fatigue_score", "rest_debt", "health_index"
  ],
  "x-forbidden-rationale": "Tỷ lệ = phụ thuộc hàm của count ⇒ lưu là tạo hai sự thật (T-046). payout_ratio thêm lý do riêng ở §5.3. hour: không nguồn tiền nào có giờ. Tên trung tính (revenue/income/amount) bị cấm ở §6.2. Trường sức khoẻ: §7.",
  "required": ["driver_key","driver_key_era","date_key","hour_band","hour_band_def_version",
               "orders_n","gross_vnd","payout_vnd","platform_vnd","money_definition_version",
               "dataset_label","ingest_run_id","schema_version"],
  "additionalProperties": false,
  "x-pii-columns": ["driver_key"]
}
```

### 2.5 JSON Schema — D3 `hour_band` (dim nhỏ nhất, nguy hiểm nhất)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gsm-driver-agent/schemas/dw/dim/hour_band",
  "title": "hour_band",
  "description": "2 thành viên {rush, normal}. Tồn tại để nói ra một sự thật khó: GSM TÁCH TIỀN theo băng giờ nhưng KHÔNG cấp ĐỊNH NGHĨA băng. Ta đang dùng RUSH_HOURS={6,7,8,16,17,18} (src/gsm_core/mockgen/realdata.py:32) — số CỦA TA. Không cột nào trong 140 cột cho phép kiểm định nghĩa đó.",
  "type": "object",
  "x-grain": "band_key × definition_version (SCD2)",
  "properties": {
    "band_key":           { "type": "string", "enum": ["rush", "normal"], "x-unit": "enum" },
    "definition_version": { "type": "string", "pattern": "^band-\\d+\\.\\d+\\.\\d+$", "x-unit": "version" },
    "definition_owner":   { "type": "string", "enum": ["GSM", "OURS", "UNKNOWN"],
      "description": "Hôm nay = 'OURS'. Chuyển 'GSM' CHỈ khi có văn bản GSM — sẽ không xảy ra." },
    "member_hours_ours":  { "type": "array", "items": { "type": "integer", "minimum": 0, "maximum": 23 },
      "x-unit": "giờ", "x-provenance": "ENGINEERED_GUESS",
      "description": "rush=[6,7,8,16,17,18]; normal = bù." },
    "member_hours_gsm":   { "type": ["array", "null"], "items": { "type": "integer" },
      "description": "null = KHÔNG BIẾT. Luôn null." },
    "is_contiguous":      { "type": "boolean",
      "description": "false cho rush: nó là TẬP HỢP hai khối (sáng 6–9, chiều 16–19), không phải một khoảng. Hệ quả cứng: KHÔNG tách được hiệu ứng sáng khỏi chiều bằng dữ liệu tiền. Ghi ở §4 hàng 10." },
    "hour_attribution_rule": { "type": "string",
      "enum": ["by_request_time", "by_pickup_time", "by_complete_time", "UNKNOWN"],
      "description": "Cuốc được gán vào băng theo mốc nào? Mock chọn by_complete_time (realdata.py:181,219) — LỰA CHỌN TUỲ Ý. GSM: UNKNOWN. Chọn sai mốc DỊCH TIỀN giữa hai băng ở các cuốc vắt qua biên." },
    "falsifiable_from_gsm_tables": { "type": "boolean",
      "description": "false. Không có cột tiền cấp giờ ⇒ không học lại được biên băng từ dữ liệu. Ngoại lệ mở lại duy nhất: nếu cột thật của bảng `trips` (hiện 0 cột biết) chứa cờ rush." },
    "alignment_risk_note": { "type": "string",
      "description": "Nếu băng TA ≠ băng GSM: exposure (ta gửi advice trong giờ TA gọi là rush) và outcome (tiền GSM kế toán vào băng GSM) LỆCH NHAU ⇒ hiệu ứng bị PHA LOÃNG VỀ 0. Bias hướng zero, KHÔNG hướng dương ⇒ rủi ro bất đối xứng, dồn về phía xấu. Giảm thiểu: randomize ở hạt (driver × ngày), KHÔNG ở hạt băng (§6.5)." },
    "effective_from":     { "type": "string", "format": "date" },
    "effective_to":       { "type": ["string", "null"], "format": "date" },
    "dataset_label":      { "type": "string", "enum": ["MOCK", "REAL"] },
    "schema_version":     { "const": "1.0.0" }
  },
  "required": ["band_key","definition_version","definition_owner","member_hours_ours",
               "member_hours_gsm","is_contiguous","hour_attribution_rule",
               "falsifiable_from_gsm_tables","effective_from","dataset_label","schema_version"],
  "additionalProperties": false,
  "x-pii-columns": []
}
```

### 2.6 JSON Schema — F4 `driver_hour_cell` (fact hạt-giờ thật duy nhất; **lỗi hạt đã sửa**)

`[ĐO]` cho thấy đặc tả của thiết kế thắng **không nhận nổi dữ liệu trung thực**: rollup ra
1.200.943 dòng, trong đó **8.000 dòng (0,666%) vượt trần 3.600s**, max **22,88 giờ**. Nguyên nhân:
`hour_local` quy theo **mốc VÀO ô** nhưng `dwell` lại bị kẹp theo **thời gian chiếm dụng giờ**. Hai
cách hiểu khác nhau trong cùng một dòng.

**Cách sửa của tôi:** không kẹp, và **đặt tên trường theo đúng hạt của nó**. Một lần đứng dài hơn một
giờ là sự thật, không phải lỗi dữ liệu — và guardrail nghỉ (§7) **cần thấy** nó.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gsm-driver-agent/schemas/dw/fact/driver_hour_cell",
  "title": "driver_hour_cell",
  "description": "Hạt: 1 dòng = (tài xế × ngày × GIỜ BẮT ĐẦU × ô H3). 'Giờ bắt đầu' = giờ của entered_current_hex_at. Rollup từ public_driver_hex_tracking (19/19 cột thật). Đây là fact DUY NHẤT có hạt giờ VÀ cột thật cùng lúc ⇒ nó là toàn bộ khả năng đo hành vi dưới-ngày của hệ. KHÔNG có cột tiền. KHÔNG có cột 'idle'.",
  "type": "object",
  "x-grain": "driver_key × date_key × hour_started × h3_cell_key",
  "x-gsm-source-table": "gsm-data-prod.GSM_MISSION_SERVICE_APPEND.public_driver_hex_tracking",
  "properties": {
    "driver_key":     { "type": "string", "pattern": "^[0-9a-f]{32}$", "x-unit": "id" },
    "driver_key_era": { "type": "string", "x-unit": "id" },
    "date_key":       { "type": "string", "format": "date",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$", "x-unit": "date" },
    "hour_started":   { "type": "integer", "minimum": 0, "maximum": 23, "x-unit": "giờ",
      "x-provenance": "DERIVED", "x-gsm-source": "hour(entered_current_hex_at)",
      "description": "ĐỔI TÊN từ 'hour_local' có chủ ý: nó là giờ VÀO ô, KHÔNG phải giờ chiếm dụng. Tên cũ mời người đọc hiểu là occupancy rồi kẹp dwell ≤3600 ⇒ loại 0,666% dòng (ĐO: 8.000/1.200.943, max 22,88h)." },
    "h3_cell_key":    { "type": "string", "pattern": "^[0-9a-f]{15}$", "x-unit": "h3r9",
      "x-provenance": "MEASURED_OUTER", "x-gsm-source": "current_hex",
      "description": "H3 res9, 15 hex. pattern này LÀ CỔNG CHẶN: token bịa '8amock##' không khớp ⇒ đẩy sang meta_ingest_reject thay vì lọt vào fact. ĐO: current_hex sạch 100% (1.371.758/1.371.758 dòng đúng 15 ký tự) ⇒ cổng này reject 0% cho bảng này. Chính bảng `trips` mới có 51,54% bịa." },
    "dwell_seconds_of_visits_started_in_hour": { "type": "integer", "minimum": 0, "x-unit": "giây",
      "x-provenance": "MEASURED_OUTER",
      "description": "KHÔNG có maximum. Tổng stay_duration_seconds của các lần đứng BẮT ĐẦU trong giờ này — có thể vượt 3600 một cách hợp pháp. Tên dài có chủ ý: nó nói ra hạt của chính nó." },
    "occupancy_seconds_in_hour": { "type": "integer", "minimum": 0, "maximum": 3600, "x-unit": "giây",
      "x-provenance": "DERIVED",
      "description": "TRƯỜNG RIÊNG cho cách hiểu occupancy: phần thời gian thực nằm TRONG biên giờ này, cắt theo giờ. Hai cách hiểu = hai cột, KHÔNG phải một cột hai nghĩa (đây là chỗ đặc tả gốc vỡ)." },
    "visits_n":       { "type": "integer", "minimum": 1, "x-unit": "lần" },
    "max_dwell_seconds": { "type": "integer", "minimum": 0, "x-unit": "giây",
      "description": "KHÔNG kẹp 3600. Nếu kẹp, longest_dwell_minutes của F8 không bao giờ vượt 60 phút ⇒ guardrail nghỉ (§7) MÙ với một lần nghỉ thật. Đây là lý do thứ hai phải bỏ trần." },
    "dwell_ge_300s_seconds": { "type": "integer", "minimum": 0, "x-unit": "giây",
      "x-provenance": "DERIVED",
      "description": "⚠ NGƯỠNG 300 NẰM TRONG TÊN CỘT LÀ CÓ CHỦ Ý: nó là ngưỡng CỦA TA (realdata.py:317-322), không phải 'idle' của GSM. Một cột tên 'idle_seconds' sẽ bị đọc là quan sát ⇒ CẤM. BUG-PI5b-01 sinh ra từ đúng việc gọi dwell là idle. ĐO: Σ trường này vượt online_time ở 746/8.022 driver-day (9,3%), tệ nhất +19,57h ⇒ xem invariant INV-DWELL-LE-ONLINE (§5.4)." },
    "dwell_threshold_rule_version": { "type": "string", "pattern": "^dwell-\\d+\\.\\d+\\.\\d+$" },
    "raw_status_seconds": { "type": "object", "additionalProperties": { "type": "integer", "minimum": 0 },
      "description": "Map giá trị THÔ của tracking_status → giây. Cố tình free-form: enum {moving,idle,offline} trong schemas/l1r/public_driver_hex_tracking.schema.json là do TA đặt; enum thật của GSM chưa biết. Không ép vào enum ta." },
    "campaign_key":   { "type": ["string", "null"], "x-unit": "id",
      "description": "ĐO: NULL 95,01% trong mock. Xem x-grain-risk." },
    "target_h3_cell_key": { "type": ["string", "null"], "pattern": "^[0-9a-f]{15}$", "x-unit": "h3r9",
      "description": "PATTERN GIỐNG h3_cell_key — đây là chỗ đặc tả gốc thiếu. ĐO: target_hex trong mock là token 8 ký tự '8amock##' ở 100% (68.493/68.493) dòng có target ⇒ TOÀN BỘ bị reject ở cổng này, và reject-rate 100% là con số PHẢI hiển thị (§5.3), không phải con số phải né." },
    "reached_target_reported": { "type": ["boolean", "null"],
      "x-provenance": "RNG_NOISE",
      "description": "ĐO: True ở 59,94% của 68.493 dòng CÓ target = 3,0% của 1.371.758 dòng toàn bảng. LUÔN ghi mẫu số. Sinh bởi rng.random()<0.6 (realdata.py:314)." },
    "reached_target_verifiability": { "type": "string",
      "enum": ["VERIFIED_AGREE", "VERIFIED_DISAGREE", "UNVERIFIABLE_TARGET_INVALID"],
      "description": "ĐÍNH CHÍNH đặc tả gốc: nó gọi reached_target là 'tự phủ định bằng dữ liệu cùng dòng'. SAI. current_hex là H3 15 ký tự, target_hex là token 8 ký tự ⇒ hai giá trị KHÔNG SO SÁNH ĐƯỢC. Trạng thái đúng là UNVERIFIABLE_TARGET_INVALID (100% dòng có target trên mock), không phải DISAGREE. Một gate 'agree_rate < 0.9 ⇒ FAIL' sẽ FAIL vĩnh viễn vì lệch KIỂU và không mang tin gì về reposition." },
    "dataset_label":  { "type": "string", "enum": ["MOCK", "REAL"] },
    "ingest_run_id":  { "type": "string" },
    "schema_version": { "const": "1.0.0" }
  },
  "x-forbidden-properties": ["idle_seconds","is_idle","gross_vnd","payout_vnd","estimated_net_vnd","fatigue_score"],
  "x-grain-risk": "RỦI RO ĐƠN LẺ LỚN NHẤT của cả hợp đồng, KHÔNG KIỂM ĐƯỢC mà không có data. Bảng thật ở dataset GSM_MISSION_SERVICE_APPEND và có campaign_id/log_id/schedule_job_id/target_hex/hex_history/updated_at — đọc như DÒNG TRẠNG THÁI theo (driver × campaign), replicate append-only qua CDC. Nếu đúng, bảng thật CHỈ TỒN TẠI KHI CÓ CAMPAIGN reposition ⇒ data thật KHÔNG có vị trí ngoài campaign, NGƯỢC HOÀN TOÀN với mock (ĐO: campaign_id NULL 95,01%). Nếu đúng, F4 sụp và §6.5(b) sụp theo. Bắt buộc khai coverage_mode ∈ {CONTINUOUS, CAMPAIGN_ONLY, UNKNOWN}, mặc định UNKNOWN.",
  "required": ["driver_key","driver_key_era","date_key","hour_started","h3_cell_key",
               "dwell_seconds_of_visits_started_in_hour","occupancy_seconds_in_hour","visits_n",
               "max_dwell_seconds","dwell_ge_300s_seconds","dwell_threshold_rule_version",
               "dataset_label","ingest_run_id","schema_version"],
  "additionalProperties": false,
  "x-pii-columns": ["driver_key","h3_cell_key","hour_started"],
  "x-pii-note": "driver_key + h3_cell_key + hour_started là quasi-identifier MẠNH: chuỗi ô theo giờ tái định danh được kể cả khi driver_id đã hash (nơi ở suy từ ô đầu/cuối ca). §7.3."
}
```

### 2.7 JSON Schema — `measurement_claim` (cổng ra duy nhất; **máy trạng thái đã sửa**)

Đây là entity tôi lấy từ `event-sourced`, nhưng **cả hai** thiết kế có cổng này đều tự khoá chết:
`PLAN_RECOMMENDATION` (output chính của sản phẩm) và `CAUSAL_MRT` bị `REFUSED` **vĩnh viễn** vì hàm
`min()` trộn hai thang không cùng đơn vị. Sửa bằng hai thứ: (a) bảng `TIER → hạt mịn nhất được phép`,
(b) **`role`** trên từng provenance — chỉ entry cấp **outcome/exposure** mới kẹp hạt claim; covariate
và policy không kẹp.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gsm-driver-agent/schemas/advisor/measurement_claim",
  "title": "measurement_claim",
  "description": "MỘT con số + MỘT khán giả. Bất biến. Mọi số hiển thị cho tài xế, cho nội bộ, hay cho hội đồng phải đi qua đây. Không chứng thư ⇒ UI/report KHÔNG được render. Ba luật §5 CLAUDE.md được cài thành điều kiện validate, không phải quy ước.",
  "type": "object",
  "properties": {
    "claim_id": { "type": "string", "minLength": 1 },
    "kind": { "type": "string",
      "enum": ["DESCRIPTIVE_WEEK","DESCRIPTIVE_DAY","DESCRIPTIVE_SUBDAY","FORECAST",
               "PLAN_RECOMMENDATION","ASSOCIATION_DAY","CAUSAL_DAY_HOLDBACK",
               "CAUSAL_SWITCHBACK","CAUSAL_MRT","SIM_COUNTERFACTUAL"] },
    "quantity": { "type": "string" },
    "unit": { "type": "string",
      "enum": ["vnd","vnd_per_driver_day","vnd_per_hour","h","min","km","count","ratio","pp"] },
    "money_kind": { "type": "string",
      "enum": ["GROSS","PAYOUT","PLATFORM_TAKE","ESTIMATED_NET","NOT_MONEY"],
      "description": "BẮT BUỘC. NOT_MONEY cho đại lượng phi tiền. Không có giá trị chung chung ('REVENUE'/'INCOME') — §6.2." },
    "grain": { "type": "string", "enum": ["week","day","subday_minute","decision_point"],
      "description": "Hạt của PHÁT BIỂU." },
    "value": { "type": ["number","null"],
      "description": "null = KHÔNG BIẾT. INV-CLAIM-1: state=REFUSED ⟺ value=null. Không bao giờ dùng 0 thay cho không biết (bài học soc_pct=None ⇒ pin đầy)." },
    "denominator_n": { "type": ["integer","null"], "minimum": 0,
      "description": "BẮT BUỘC (có thể 0) khi unit ∈ {ratio, pp}. denominator_n == 0 ⇒ value PHẢI null. Đây là chốt chặn cho đúng lỗi repo đã mắc: standby_alloc báo 36/36 = 100% vì mẫu số thiếu 86 dòng; D-M3-01 báo adherence 1,0 theo CẤU TRÚC vì kênh không rút coin. §5.1." },
    "n_units": { "type": "integer", "minimum": 1,
      "description": "SỐ ĐƠN VỊ ĐỘC LẬP THẬT (driver-day, hoặc khối switchback) — KHÔNG phải số seed. Precision là hàm của SỐ LẦN GÁN (Bojinov et al.), không của CRN." },
    "as_of": { "type": "string", "format": "date-time",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])T([01]\\d|2[0-3]):[0-5]\\d:[0-5]\\d(\\.\\d+)?(Z|[+-]([01]\\d|2[0-3]):[0-5]\\d)$",
      "description": "Thời điểm TÍNH. INV-CLAIM-4: as_of >= window_end. Đây là chốt cho lớp RÒ TƯƠNG LAI TRONG NGÀY — một claim hạt day dựng từ provenance hạt day KHÔNG vi phạm ceiling, nên chỉ as_of bắt được nó (§3.3, §5.2)." },
    "window_start": { "type": "string", "format": "date-time" },
    "window_end":   { "type": "string", "format": "date-time" },
    "provenance": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "entity":        { "type": "string" },
          "role":          { "type": "string", "enum": ["outcome","exposure","covariate","policy"],
            "description": "CHỖ SỬA QUAN TRỌNG NHẤT của cổng này. Ceiling hạt chỉ tính trên role ∈ {outcome, exposure}. Không có role, một covariate hạt tuần kéo mọi claim về 'week' và PLAN_RECOMMENDATION bị REFUSED vĩnh viễn." },
          "grain_tier":    { "type": "string", "enum": ["E0","E1w","E1","E2","E3","E4","E5"] },
          "dataset_label": { "type": "string", "enum": ["MOCK","REAL"] },
          "provenance_kind": { "type": "string",
            "enum": ["MEASURED_OUTER","MEASURED_INNER","POLICY_RULE","DERIVED",
                     "EXTERNAL_PROXY","SELF_FIT","ENGINEERED_GUESS","RNG_NOISE"] },
          "rule_version":  { "type": ["string","null"] },
          "dataset_ref":   { "type": ["string","null"],
            "description": "BẮT BUỘC khi dataset_label=MOCK: manifest + seed + engine_commit + generated_at (CLAUDE.md §5 đòi seed + nguồn + ngày tạo)." },
          "as_of_cut":     { "type": ["string","null"],
            "description": "Mốc đã CẮT nếu input là aggregate ngày mà đọc trong ngày. null + tier E1 + uncuttable=true ⇒ trường KHÔNG cắt được (acceptance_rate, online_time)." },
          "uncuttable":    { "type": "boolean", "default": false }
        },
        "required": ["entity","role","grain_tier","dataset_label","provenance_kind"],
        "additionalProperties": false
      }
    },
    "randomization": {
      "type": ["object","null"],
      "description": "TRƯỜNG SCHEMA THẬT, không phải khoá ngoài luồng. Cả hai thiết kế có cổng này đều đọc claim['p_t'] trong khi additionalProperties:false khiến p_t KHÔNG THỂ tồn tại ⇒ mọi claim CAUSAL_* bị chặn vì thiếu một TRƯỜNG, không vì thiếu dữ liệu.",
      "properties": {
        "design_id":         { "type": "string", "description": "Bản thiết kế khai TRƯỚC khi chạy (pre-registration nội bộ)." },
        "unit":              { "type": "string", "enum": ["driver_day","driver_day_topic","zone_timeblock","decision_point"] },
        "p_t":               { "type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1 },
        "arm_constant_within_unit": { "type": "boolean",
          "description": "PHẢI true. Không có nó, 14 dòng của cùng một driver-day có thể mang arm khác nhau và validate sạch — test INV-ARM-CONST (§5.6)." },
        "control_arm_effective_adherence": { "type": "number", "minimum": 0, "maximum": 1,
          "description": "BẮT BUỘC: adherence HIỆU DỤNG của arm ĐỐI CHỨNG, ĐO ĐƯỢC chứ không giả định 0. Bài học DET-01 (UPDATE-099): cờ cadence.enabled tắt luôn keyed coin ⇒ arm đối chứng nghe lời ~10đp nhiều hơn vì lý do không liên quan ⇒ đã báo số sai gấp đôi cho Cường." }
      },
      "required": ["design_id","unit","p_t","arm_constant_within_unit","control_arm_effective_adherence"],
      "additionalProperties": false
    },
    "cost_terms": { "type": ["array","null"],
      "description": "BẮT BUỘC khi money_kind=ESTIMATED_NET. Phải PHỦ TRỌN enum term (§6.3) — không phải chỉ ≥1 item.",
      "items": {
        "type": "object",
        "properties": {
          "term":   { "type": "string", "enum": ["battery","cash_per_km","fixed_daily","maintenance","depreciation"] },
          "value":  { "type": "number" },
          "unit":   { "type": "string", "enum": ["vnd","vnd_per_km","vnd_per_swap","vnd_per_day"] },
          "state":  { "type": "string", "enum": ["ACTIVE","OFF_BY_POLICY","UNKNOWN"],
            "description": "Khớp gsm_core.policy.resolve_cost_params. OFF_BY_POLICY (pin miễn phí tới 2029-03-31) KHÔNG chặn; chỉ UNKNOWN chặn." },
          "reason": { "type": "string", "minLength": 10 }
        },
        "required": ["term","value","unit","state","reason"], "additionalProperties": false
      }
    },
    "adherence_denominator": { "type": "string",
      "enum": ["decision","event","self_report","not_applicable"],
      "description": "KHÔNG có giá trị 'adherence' trần. Sau ĐA-04 hai đơn vị hội tụ (ĐO/UPDATE-099: 68,1% vs 67,6%) nhưng chúng vẫn là HAI đại lượng — hội tụ là kết quả, không phải giấy phép gộp tên." },
    "audience": { "type": "string", "enum": ["driver","analyst","stakeholder","internal_sim"] },
    "producer_kind": { "type": "string", "enum": ["rule","solver","analytics"],
      "description": "CỐ Ý KHÔNG CÓ 'llm' (CLAUDE.md §5: agent không tự tính số). Đây là ràng buộc NHÃN + audit trail, KHÔNG phải bất khả — không gì ngăn ai ghi 'rule' cho văn LLM sinh. Cơ chế thật đạt được là khiến việc nói dối trở nên TƯỜNG MINH và audit được. Xem §9.2." },
    "producer_id": { "type": "string" },
    "state": { "type": "string", "enum": ["SUPPORTED","DEGRADED","REFUSED"] },
    "refusals": { "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "reason_code": { "type": "string",
            "enum": ["TIER_ABSENT","GRAIN_CEILING","DENOMINATOR_EMPTY","AS_OF_BEFORE_WINDOW_END",
                     "NO_RANDOMIZATION","CONTROL_ARM_DIRTY","ARM_NOT_CONSTANT","COST_TERM_UNKNOWN",
                     "COST_TERMS_INCOMPLETE","RNG_NOISE_ON_DRIVER_FACING","POLICY_UNKNOWN",
                     "QUARANTINE_ON_MONEY_PATH","MIXED_DATASET_LABEL","K_ANON_FAIL","LABEL_UPGRADED"] },
          "detail":      { "type": ["string","null"] },
          "human_reason":{ "type": "string", "minLength": 10,
            "description": "Câu tiếng Việt hiển thị được. Refusal không nói ra được là refusal vô dụng — và nó là thứ UI render THAY CHO con số." }
        },
        "required": ["reason_code","human_reason"], "additionalProperties": false
      }
    },
    "caveats": { "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 10 },
      "description": "≥1 caveat LUÔN bắt buộc, kể cả khi SUPPORTED (CLAUDE.md §5: không hứa chắc thu nhập)." },
    "dataset_label": { "type": "string", "enum": ["MOCK","REAL"] },
    "schema_version": { "const": "1.0.0" }
  },
  "required": ["claim_id","kind","quantity","unit","money_kind","grain","value","n_units","as_of",
               "window_start","window_end","provenance","audience","producer_kind","producer_id",
               "state","refusals","caveats","dataset_label","schema_version"],
  "additionalProperties": false,
  "allOf": [
    { "if":   { "properties": { "unit": { "enum": ["ratio","pp"] } }, "required": ["unit"] },
      "then": { "required": ["denominator_n"], "properties": { "denominator_n": { "not": { "const": null } } } } },
    { "if":   { "properties": { "money_kind": { "enum": ["GROSS","PAYOUT","PLATFORM_TAKE","ESTIMATED_NET"] } }, "required": ["money_kind"] },
      "then": { "required": ["cost_terms"] } },
    { "if":   { "properties": { "kind": { "enum": ["CAUSAL_DAY_HOLDBACK","CAUSAL_SWITCHBACK","CAUSAL_MRT"] } }, "required": ["kind"] },
      "then": { "required": ["randomization"], "properties": { "randomization": { "not": { "const": null } } } } },
    { "if":   { "properties": { "kind": { "enum": ["SIM_COUNTERFACTUAL","CAUSAL_MRT"] } }, "required": ["kind"] },
      "then": { "properties": { "audience": { "const": "internal_sim" } } } }
  ]
}
```

**Hàm phán xử** — `src/gsm_core/audit/claim_gate.py`, thuần hàm, không I/O:

```python
# Hạt MỊN NHẤT mà mỗi tier được phép cấp cho một PHÁT BIỂU.
# E0 KHÔNG có mặt: policy là RULE, không phải data, nên nó không kẹp hạt.
TIER_MAX_GRAIN = {"E1w": "week", "E1": "day", "E2": "subday_minute",
                  "E3": "subday_minute", "E4": "decision_point", "E5": "decision_point"}
GRAIN_RANK = {"week": 0, "day": 1, "subday_minute": 2, "decision_point": 3}
LABEL_RANK = {"REAL": 0, "MOCK": 1}
_SOFT = {"EXTERNAL_PROXY", "SELF_FIT", "ENGINEERED_GUESS", "RNG_NOISE"}
_LOAD_BEARING = {"outcome", "exposure"}   # chỉ hai role này kẹp hạt claim

def adjudicate(claim: dict) -> dict:
    r: list[tuple[str, str | None]] = []

    # (1) GRAIN CEILING — chỉ tính trên provenance CHỊU LỰC, và bỏ hẳn E0.
    load = [p for p in claim["provenance"]
            if p["role"] in _LOAD_BEARING and p["grain_tier"] != "E0"]
    if not load:
        r.append(("TIER_ABSENT", "không có provenance nào cấp outcome/exposure"))
    else:
        ceiling = min(GRAIN_RANK[TIER_MAX_GRAIN[p["grain_tier"]]] for p in load)
        if GRAIN_RANK[claim["grain"]] > ceiling:
            r.append(("GRAIN_CEILING",
                      f"claim hạt '{claim['grain']}' mịn hơn tier chịu lực thô nhất"))

    # (2) MẪU SỐ VẮNG — không bao giờ trả 0%/100% từ một mẫu số rỗng.
    if claim["unit"] in ("ratio", "pp"):
        if claim.get("denominator_n") is None:
            r.append(("DENOMINATOR_EMPTY", "unit là tỷ lệ nhưng không khai mẫu số"))
        elif claim["denominator_n"] == 0 and claim["value"] is not None:
            r.append(("DENOMINATOR_EMPTY", "mẫu số 0 ⇒ value phải null, không phải 0 hay 1"))

    # (3) RÒ TƯƠNG LAI — ceiling không bắt được lớp lỗi này.
    if claim["as_of"] < claim["window_end"]:
        r.append(("AS_OF_BEFORE_WINDOW_END", "tính trước khi cửa sổ đóng"))

    # (4) TRỘN MOCK VỚI THẬT — §5 CLAUDE.md là KHÔNG TRỘN, không phải "trộn thì khai".
    labels = {p["dataset_label"] for p in claim["provenance"]}
    if len(labels) > 1:
        r.append(("MIXED_DATASET_LABEL", f"provenance trộn {sorted(labels)}"))
    elif LABEL_RANK[claim["dataset_label"]] < max(LABEL_RANK[x] for x in labels):
        r.append(("LABEL_UPGRADED", "claim mang nhãn sạch hơn input"))

    # (5) NHÂN QUẢ.
    if claim["kind"].startswith("CAUSAL"):
        rd = claim.get("randomization")
        if not rd:
            r.append(("NO_RANDOMIZATION", "advice tất định theo state ⇒ p_t không tồn tại"))
        else:
            if not rd["arm_constant_within_unit"]:
                r.append(("ARM_NOT_CONSTANT", "arm đổi trong một đơn vị gán"))
            if rd["control_arm_effective_adherence"] is None:
                r.append(("CONTROL_ARM_DIRTY", "chưa đo adherence hiệu dụng của arm đối chứng"))

    # (6) NHIỄU RA MẶT TÀI XẾ.
    kinds = {p["provenance_kind"] for p in claim["provenance"]}
    if claim["audience"] == "driver" and "RNG_NOISE" in kinds:
        r.append(("RNG_NOISE_ON_DRIVER_FACING", "một số rng.* được render cho tài xế đọc"))

    # (7) CHI PHÍ PHỦ TRỌN — thiếu một term là thiếu, không phải "đủ".
    if claim["money_kind"] == "ESTIMATED_NET":
        terms = {t["term"]: t["state"] for t in (claim.get("cost_terms") or [])}
        need = {"battery", "cash_per_km", "fixed_daily", "maintenance", "depreciation"}
        if missing := need - set(terms):
            r.append(("COST_TERMS_INCOMPLETE", f"vắng term: {sorted(missing)}"))
        if any(s == "UNKNOWN" for s in terms.values()):
            r.append(("COST_TERM_UNKNOWN", "có số hạng chi phí UNKNOWN"))

    if r:
        return {**claim, "state": "REFUSED", "value": None,
                "refusals": [{"reason_code": c, "detail": d,
                              "human_reason": _vi(c, d)} for c, d in r]}
    if (_SOFT & kinds) or claim["dataset_label"] == "MOCK":
        # HỆ QUẢ CỐ Ý: chạy trên MOCK thì KHÔNG claim nào đạt SUPPORTED.
        return {**claim, "state": "DEGRADED", "refusals": []}
    return {**claim, "state": "SUPPORTED", "refusals": []}
```

`[ĐO]` kiểm máy trạng thái với input hoàn hảo: `PLAN_RECOMMENDATION` (outcome = E1 tiền, policy = E0)
→ ceiling `day`, claim `day` ⇒ **SUPPORTED**. `CAUSAL_MRT` (outcome = E4) → ceiling `decision_point`
⇒ **SUPPORTED**. Claim *"thẻ lúc 14h làm ra X đồng"* (outcome = **tiền, tier E1**) → ceiling `day`,
claim `decision_point` ⇒ **REFUSED(GRAIN_CEILING)**. Đúng ba kết quả cần có.

### 2.8 M1 `field_provenance` — bản đồ MOCK↔THẬT dạng DỮ LIỆU

Hạt: `(entity, field)`, đúng 1 dòng. Trường **bắt buộc**: `entity`, `field`, `owner ∈
{GSM_REAL_COLUMN, GSM_TABLE_ONLY, DERIVED, OURS_PRODUCT}`, `gsm_source`, `grain_native`, `unit`,
`semantics_unknown`, `mock_substitute` (kèm `file:line`), `mock_mechanism ∈ {SIM_DERIVED, RULE,
RNG_NOISE, CONSTANT, ALL_NULL, IDENTITY, CLAMPED_BY_ASSUMPTION}`, `provenance_kind`, `money_path ∈
{ON_MONEY_PATH, OFF_MONEY_PATH, GUARDRAIL_ONLY}`, `derived_from_quarantine`, `if_wrong_2x` (không
được rỗng), `blast_radius[]`, `unfalsifiable_from_within`, `reopen_condition`.

`reopen_condition` **tường minh loại bỏ** *"GSM cấp thêm data"* — đó không phải điều kiện hợp lệ
(chốt 2026-07-30). Gate: `test_every_dw_field_has_provenance`.

### 2.9 Đóng nhánh chết (đính chính bắt buộc)

| Việc | Chỗ |
| --- | --- |
Khai tử `x-availability: "TBC-với-GSM"` → vocabulary mới `PROVIDED_SCHEMA \| TABLE_NAME_ONLY \| NOT_PROVIDED_CLOSED \| FIRST_PARTY \| DERIVED` | 4 `schemas/l1r/*` + `l1/gps_ping` + `l1/swap_transaction` + `schemas/README.md` |
Đóng mọi dòng "XIN GSM" → `TABLE_NAME_ONLY (ta thiết kế — vĩnh viễn)` | `docs/data-catalog/gsm-data-catalog.csv` |
Sửa "**5** bảng thiếu cột" → **4** `[ĐO]` | `specs/real-data/01-data-catalog-and-analysis.md:63`, `:71`, `:79`; `02-schema-reground-plan.md:69`, `:78` |
Thêm `generated_at` vào manifest `[ĐO]` thiếu | `src/gsm_core/mockgen/realdata.py` (giữ hậu tố `+dirty` — thiết kế chống nói dối đúng chỗ) |
Sửa `mockgen_strategy` của `stoppoints`: catalog ghi "đếm từ hex stay/idle segments sim", code là `randint(0, completed//2)` | `docs/data-catalog/gsm-data-catalog.csv` |

---

## §3. Bản đồ MOCK↔THẬT

### 3.1 Tiền (F1) — chỗ nguy hiểm nhất

| Trường thật | MOCK đang thay bằng | Nhãn |
| --- | --- | --- |
`total_fee_{band}` → `gross_vnd` | bike: công thức policy 13k+4,3k/km. car/rto: `fare = randint(fare_lo, fare_hi)` **độc lập quãng đường** — `[KẾ-THỪA]` corr(km, cước) = **0,002** ở nửa đó vs **0,923** ở nửa bike | `RULE` + `RNG_NOISE` (một nửa) |
`commission_{band}` → `payout_vnd` | `round(gross × driver_share)`, `driver_share` **hằng số theo `kind`** | **`IDENTITY`** — xem §4 hàng 3 |
`revenue_not_relate_driver_{band}` → `platform_vnd` | **ĐỊNH NGHĨA** `:= gross − commission`; `[ĐO]` khớp **12.805/12.805 dòng** | **`IDENTITY`** — 0 bit thông tin mới |
`total_order_{band}` → `orders_n` | split trips theo `RUSH_HOURS={6,7,8,16,17,18}` của TA, theo **giờ hoàn thành** | `RULE`, `unfalsifiable_from_within: true` |
băng giờ (định nghĩa) | không có nguồn GSM | `ENGINEERED_GUESS` |

### 3.2 Vận hành (F2/F3)

| Trường thật | MOCK | Nhãn |
| --- | --- | --- |
`online_time` | `online_h = max(online_h, trip_hours/0.55)` — 0,55 là **cận trên benchmark utilization 45–55%** ⇒ `[KẾ-THỪA]` **93,2%** driver-day car/rto có util đúng 0,55 | **`CLAMPED_BY_ASSUMPTION`** — ai "xác nhận utilization khớp benchmark" đang xác nhận hằng số ta tự viết |
`acceptance_rate` | `cancelled / total_request_accept`, **KHÔNG trừ** `count_cancel_not_relate_driver` ⇒ chọn cách hiểu **ngược** ghi chú công bằng của spec P1 | `RULE`, lưu **CẢ HAI** (`*_reported` + tự tính) |
`schedule_date` | `[ĐO gián tiếp / KẾ-THỪA]` `== local_date` ở 100% dòng | **`IDENTITY`** — cột **duy nhất** trong 140 cột gợi ý GSM có dữ liệu ĐĂNG KÝ CA, bị bóp thành một cột ⇒ **không đo được lệch ca**, mà lệch ca chính là đối tượng của lời khuyên chọn ca |
`total_stoppoints_rush_hour` | `randint(0, completed//2)` | `RNG_NOISE` |
`total_stoppoints_normal_hour` | **KHÔNG TỒN TẠI** `[ĐO]` — phải trừ | **`DERIVED`**, không phải `GSM_REAL_COLUMN` |

### 3.3 Rò tương lai trong ngày — `[ĐỌC]` code, còn sống

`[ĐỌC]` `src/gsm_core/features/from_l1r.py`: `trips_today` **đã** cắt tại `t_now`
(audit A3/UPDATE-070), nhưng ba chỗ **chưa**:

```python
stat = _stat_row(l1r, driver_id, today)       # dòng CẢ NGÀY
acceptance = float(stat["acceptance_rate"])    # ← số CUỐI NGÀY, đọc lúc 08:00
used = float(onl["online_time"]) if onl else 0.0
hours_budget = max(0.0, min(12.0 - used, ...)) # ← trừ TOÀN BỘ giờ online cả ngày
hist_rate[b] = pts / oh   # pts = điểm CHỈ-CỦA-PEAK, oh = giờ online CẢ NGÀY
```

Ba hệ quả: (a) cảnh báo "sát ngưỡng 85%" trong ca dùng số của tương lai; (b) `hours_budget_remaining`
sai hệ thống; (c) `[KẾ-THỪA]` `historical_points_per_hour['peak']` ra **0,9đ/h** thay vì ~13đ/h ⇒ S1
tuyên một mốc thưởng **đạt được trong ~2h peak** là **KHÔNG khả thi** — sai **~14×**.

Quan trọng: (a) và (b) **không vi phạm grain ceiling** (provenance hạt day, claim hạt day) ⇒ **chỉ
`as_of` bắt được chúng**. Đó là lý do `as_of` là trường bắt buộc ở §2.7 và là điều cả ba thiết kế
thiếu.

### 3.4 🔴 NHIỄU THEO CONSTRUCTION — nhóm riêng, vì chúng **tệ hơn giả định**

Một giả định sai vẫn mang một cơ chế và có thể hiệu chỉnh. **Nhiễu thuần không mang cơ chế nào** —
không hiệu chỉnh được, chỉ bỏ được. Mọi trường dưới đây `mock_mechanism = RNG_NOISE`.

| Trường | Sinh bằng | Solver ĐỌC? | Hệ quả |
| --- | --- | --- | --- |
`public_frauds.confidence` | `round(rng.uniform(0.3, 0.8), 2)` | ✅ **S9 render `"độ tin cậy {x:.0%}"`** | 🔴 **Vi phạm CLAUDE.md §5 nặng nhất trong hệ**: một số uniform-random được in cạnh chữ "độ tin cậy" cho tài xế đọc. Thang `low/medium/high` còn lệch thang chính thức 4 mức của app |
`driver_penalization_ATA.amount_vnd` | `rng.choice([40k,100k,200k])`, chỉ khi `at_risk ∧ rng<0.5` ⇒ `[ĐO]` 75 dòng dồn vào 5 ngày | ✅ S8 cộng thành `total_deducted_vnd` rồi `format_vnd` | Số tiền trừ giải thích cho tài xế là `rng.choice`. S8 docstring nói "đo được" |
`public_driver_hex_tracking.reached_target` | `rng.random() < 0.6` | ✅ S7 / `idle_reduction` | Trường đo hiệu quả reposition. `target_hex` còn `[ĐO]` **100% token 8 ký tự** ⇒ **UNVERIFIABLE**, không so được |
`campaign_id` | `rng.random() < 0.05` | ✅ S7 quyết định có nói "nhiệm vụ reposition CHÍNH THỨC của GSM" | Tính năng chạy trên **hai** lần tung xúc xắc |
`total_stoppoints` | `randint(0, completed//2)` | ✅ S7/UC2 | Proxy idle là nhiễu; catalog **nói dối** về cơ chế |
`count_cancel_not_relate_driver` | `randint(0, cancelled)` | ❌ | Trường quyết định **công bằng** khi xét phạt huỷ |
`total_core_order` | `completed × gauss(0.90, 0.04)` | ❌ | "core" là gì cũng chưa biết |

⇒ **Luật:** `provenance_kind = RNG_NOISE` + `audience = driver` ⇒ `REFUSED` (§2.7 nhánh 6). Bốn
usecase (UC2 idle, UC5 reposition, UC6 giải thích phạt, UC7 cảnh báo bất thường) **mất mặt tài xế**
cho tới khi generator được sửa. Đây là mất mát thật, ghi ở §4 hàng 8–9.

### 3.5 Trường CÓ tên thật mà mock để trống/hằng số

`[KẾ-THỪA]` 30 trường NULL 100%, ~20 trường hằng số. Luật xử lý: `mock_mechanism ∈ {ALL_NULL,
CONSTANT}` ⇒ **không lên fact**, chỉ nằm ở `field_provenance` kèm `reopen_condition`. Đáng nêu tên vì
blast radius: `rule_code` + `qualify_execute_code` (điều kiện đủ điều kiện mission — nền S6),
`hex_history` (đường đi), `ata_code` (trường mà chính **tên bảng** lấy từ đó), và
`trips.status = 'completed'` **100%** ⇒ **cuốc huỷ và cuốc đang giao vô hình** ⇒ **cầu không được
phục vụ không tồn tại trong dữ liệu**.

---

## §4. 🔴 Kết luận nào KHÔNG sống nổi qua khoảng cách MOCK↔THẬT

Ba mức: **VỮNG** (sống qua được, có thể trình bày) · **LUNG LAY** (phụ thuộc một giả định có thể sai,
và biết trước hướng lệch) · **KHÔNG THỂ KIỂM** (không có dữ liệu nào trong tầm với, kể cả data thật,
để xác nhận hay bác bỏ).

Nguồn claim: `[ĐỌC]` `research/audit/2026-07-27-current-state/README.md` · UPDATE-087 · UPDATE-099 ·
UPDATE-100 · UPDATE-101 · `tracking/QUYET-DINH-2026-07-30-nam-diem.md`.

| # | Kết luận đã báo | Phụ thuộc giả định | Mức |
| --- | --- | --- | --- |
| 1 | **`positioning_overrides: wait_only` cho payout +6.016đ/người/ngày SIG, n=100 seed; served +1,74đp; đơn chết −23,4; Gini & HHI giảm; PASS 9/9 ĐA-08** (UPDATE-087) — **con số chủ lực của dự án** | advisor nhận **λ CHÍNH XÁC** của generator (`market_state.py` → `expected_demand_field`) trong khi tài xế chỉ nhận `λ × exp(N(0,σ))`, σ = 0,10–0,60 theo archetype | 🔴 **LUNG LAY** — và không phải "sai 2×" mà **sai về bản chất nguồn tin**. Advisor biết **hàm sinh cầu**; ngoài đời tín hiệu tốt nhất là mật độ cuốc **ĐÃ phục vụ** (không có unserved), tức thiên lệch có hệ thống về nơi **đã có** tài xế — đúng hướng làm **herding TỆ HƠN**. **Phải dựng một arm "advisor cũng nhiễu" TRƯỚC khi mang ra hội đồng.** |
| 2 | Δ đó **phát hiện được** trên panel data thật hạt ngày | `[ĐO]` sd trong-tài-xế của payout = **84.617đ** trên 12.805 driver-day ⇒ **MDE = 4.188đ** (2 arm, power 80%, α=0,05) < 6.016đ. Nếu gán ở hạt **driver** thì MDE = **165.985đ** ⇒ vô vọng | ✅ **VỮNG có điều kiện** — aggregate-ngày **không giết** thực nghiệm, nó chỉ giết **quy gán cho từng lời khuyên**. Điều kiện: gán ở hạt (driver × ngày). Giả định: iid trong tài xế, **không tự tương quan chuỗi ngày** (thực tế sẽ làm MDE xấu hơn); và sd 84.617đ tự nó là **artifact MOCK** (bộ này trộn car + bike một pool) ⇒ dùng làm **bậc độ lớn**, không dùng công bố |
| 3 | **"Chúng tôi tối ưu payout của tài xế, không phải doanh thu nền tảng"** | `payout/gross` biến động theo cuốc/theo giờ | 🔴 **LUNG LAY → gần như CHẾT trên mock.** `[ĐO]` tỷ lệ làm tròn 4dp nhận **đúng 3 giá trị** `{0,25; 0,75; 0,90}`, var **trong-tài-xế** ≤ **1,89e-11** ⇒ trên dữ liệu này **tối ưu payout ĐỒNG NHẤT tối ưu gross** (phép nhân hằng số). Đây là **cam kết thiết kế**, KHÔNG phải kết quả thực nghiệm. Data thật gần chắc chắn có surge/trợ giá/thu hộ làm tỷ lệ biến động — và **chính biến động đó** là chỗ advisor tạo giá trị mà mock đã xoá |
| 4 | **MỨC** thu nhập tài xế (vd "payout FT ~243k/ngày") | `driver_share = 0,75` | 🔴 **LUNG LAY.** 0,75 là **cận dưới** dải official **[0,75–0,91]**. Nếu thật là 0,91 thì payout cao hơn **21,3%** và bảng đối chiếu "payout FT dưới dải thực 270–480k" **tự khớp** mà không cần hiệu chỉnh nào khác ⇒ "CALIBRATION GAP T-021" có thể chỉ là **một tham số policy chọn sai**. ⚠ **Δ bền với share (hệ số nhân chung hai arm); MỨC không bền. Không được trình bày hai thứ đó với cùng độ tin.** |
| 5 | **Giá của nhịp (cadence) = −1.530đ CI[−2.401, −673] SIG** (artifact 37, n=100 ghép cặp) | arm đối chứng **sạch** | ✅ **VỮNG về phương pháp, và đây là hàng đáng tin nhất của bảng.** Con số này là **bản đã sửa** sau khi hai vòng soi độc lập tìm ra **3 confound** (`DET-01`: cờ `cadence.enabled` tắt luôn keyed coin ⇒ arm đối chứng nghe lời +10đp; `R-01`: liều can thiệp 2,0–2,5×; `R-09`: ba định nghĩa "đã nói"). Số **đã báo cho Cường trước đó là −3.048đ** ⇒ **sai gấp đôi**. Đây là tiền lệ vì sao §2.7 bắt buộc `control_arm_effective_adherence` |
| 6 | **Nhịp gần như MIỄN PHÍ khi không có `shift_plan`: −259đ CI[−1.111, +589] ns**; toàn bộ chi phí ở **tương tác FIFO: +2.207đ CI[+1.077, +3.372] SIG** (artifact 38, n=100 per-seed) | — | ✅ **VỮNG trong sim.** Kết luận đúng: **nhịp không đắt, cách chia ngân sách FIFO mới đắt.** Ở config ship (chỉ `positioning`) nhịp tốn ≈0đ |
| 7 | **Adherence hai đơn vị hội tụ: decision 68,1% vs event 67,6%** (washout `D-A3-01` đã chết) | keyed coin theo `(decision_id, material_revision)` | ✅ **VỮNG trong sim** — nhưng ⚠ **mọi tài liệu trích "76,9% vs 53,6%" như số hiện hành là SỐ CŨ** (trước ĐA-04). Cả ba thiết kế đối đầu đều trích số cũ |
| 8 | **`rest_window` Δ ≈ 0 ⇒ nên tắt kênh** | kênh đã được đo | 🔴 **KẾT LUẬN RỖNG — đã bị chính dự án bác 2026-07-30.** `D-M3-01`: kênh **không rút coin** ⇒ adherence **cắm cứng 1,0** ⇒ **thước hỏng**. `D-M3-04`: `planned_rest_hour` chỉ được nuôi ở `multiday.py`, `run_parallel.py` không dùng ⇒ trong **mọi** artifact A/B kênh nói **0/873 lần** ⇒ **kênh chưa từng bật**. Tắt một kênh chưa nói câu nào là kết luận rỗng ⇒ cổng **tiền-đăng-ký** (Quyết định 4) |
| 9 | **"Độ tin cậy X%"** của S9 · **tổng tiền trừ** của S8 · lời khuyên **idle** của S7 · **reposition** hiệu quả | trường tương ứng có mang cơ chế | 🔴 **KHÔNG THỂ KIỂM, và tệ hơn: KHÔNG NÊN NÓI.** `[ĐO]`/`[ĐỌC]` §3.4 — `rng.uniform(0.3,0.8)`, `rng.choice([40k,100k,200k])`, ngưỡng dwell của ta, `rng.random()<0.6`. Bốn bảng nguồn (`public_frauds`, `driver_penalization_ATA`, `trips`, `public_user_mission_progress`) đều **0 cột biết** ⇒ kể cả có data thật, ta **chưa biết một cột nào** để nối vào |
| 10 | Bất kỳ kết luận **"khung giờ sáng hiệu quả hơn chiều"** | băng rush là một khoảng | 🔴 **KHÔNG THỂ KIỂM.** `rush` là **TẬP HỢP** {6,7,8,16,17,18} (`is_contiguous: false`) ⇒ không tách được hiệu ứng sáng khỏi chiều bằng dữ liệu tiền. Không có đường vòng nào |
| 11 | Mọi kết luận **liên quan PIN**: ràng buộc SOC, tie-break SWAP-trước-REST (Cycle R/H3), phí đổi pin C5 | có telemetry SOC | 🔴 **KHÔNG THỂ KIỂM.** 13 bảng **không có** telemetry pin và **không có bảng giao dịch đổi pin nào**. `soc_pct=None` ⇒ `shift_dp.py` đặt `soc0 = NS-1` = **PIN ĐẦY** ⇒ nhánh SWAP và toàn bộ ràng buộc SOC **không bao giờ ràng buộc**. Kênh `swap_window` phải **bỏ hẳn** khỏi production |
| 12 | **Fix tín-dụng-nghỉ (Cycle R/H1)** đã chữa "tổng nghỉ +16–27%" | có `rest_taken_min`/`shift_elapsed_min` cấp phút | 🔴 **KHÔNG SỐNG.** Data thật không có hai trường đó ⇒ `_required_rest` quay về công thức mù-state ⇒ **lỗi tái-áp REST tái sinh nguyên vẹn** trên đường thật |
| 13 | **Kênh vị trí "cứu hệ thống"** (served +1,03đp, đơn chết −13,4/ngày, payout đội +212k/ngày, HHI giảm) qua S4 | có sức chứa trạm/zone | 🔴 **KHÔNG THỂ KIỂM.** Không bảng nào có trạm pin, hàng chờ, hay số tài xế đứng theo ô. `[KẾ-THỪA]` S4 chạy trên **hai hằng số**: throughput **6,0** cuốc/giờ và zone capacity **5** |
| 14 | Số **equilibrium / price-of-anarchy** (adherence thật lấy 51–73% mức tập trung) | `adherence_by_archetype` 0,30–0,75 | 🔴 **LUNG LAY, bất đối xứng về phía xấu.** Config **tự khai** "ASSUMPTION có lập luận, CHƯA có số thật". Sai 2× **xuống** ⇒ Δ tụt về ~+3.000đ, **dưới MDE 4.188đ** ⇒ CI chứa 0. Chiều **lên** bị trần 1,0 kẹp (≤1,33×) ⇒ **rủi ro dồn hết một phía**. Đây là tham số duy nhất trong config hiệu chỉnh được bằng một việc rẻ, làm được ngay, **không cần GSM**: khảo sát tài xế ⇒ **ưu tiên số 1** |
| 15 | Estimator **30–100 seed × CRN twin-world** chứng minh giá trị advisor | thiết kế tái lập được ngoài đời | 🔴 **KHÔNG SỐNG.** Ngoài đời **không có World A và World B cùng ngày cùng đơn**. Phải đổi sang switchback (đơn vị = khối thời gian) hoặc holdback hạt ngày; cả hai cần cỡ mẫu lớn hơn **nhiều bậc**. Precision là hàm của **số lần gán**, không của CRN ⇒ `n_units` ở §2.7 cố ý đếm đơn vị độc lập thật |
| 16 | **`utilization` của sim khớp benchmark 45–55%** | đó là quan sát | 🔴 **VÒNG TRÒN, không phải xác nhận.** `online_h = max(online_h, trip_hours/0.55)` và 0,55 **chính là** cận trên benchmark ⇒ `[KẾ-THỪA]` 93,2% driver-day car/rto nằm trong [0,5449; 0,5551]. Ai "xác nhận" điều này đang xác nhận **hằng số ta tự viết**. (Mốc ngoài **có thật**: định nghĩa `on_trip/online_min` của sim khớp 1:1 định nghĩa pháp lý TLC, và TLC ấn định toàn ngành **58%** — dùng nó, đừng dùng vòng tròn) |
| 17 | Mọi kết luận về **"thu nhập ròng"** / tiết kiệm chi phí | biết chi phí | 🔴 **KHÔNG SỐNG.** `[ĐỌC]` `resolve_cost_params` trả **đúng 2 term** `{battery, cash_per_km}`; `fixed_daily`, `maintenance`, `depreciation` **không có nguồn nào**. Và chi phí cố định **50–67k/ngày** lớn hơn Δ (+6.016đ) **mười lần** ⇒ con số net sẽ do một **giả định chi phí** quyết định, không do advisor. ⚠ Tự bác một nghi ngờ ngược chiều: chi phí **theo km** KHÔNG đảo dấu Δ — cần ~40 km rỗng/người/ngày ở 150đ/km, thực tế deadhead ~6 km/người/ngày ⇒ nó phá **MỨC** và `estimated_net`, **không** phá Δ |

### 4.1 Ba trụ còn lại sau khi trừ hết — và một trụ KHÔNG tồn tại

Trước hội đồng phải nói cả ba, đúng thứ tự này:

1. **Sim chứng minh CƠ CHẾ có thể sinh tiền** — kèm nhãn trung thực rằng advisor được cấp λ chính xác
   của generator (hàng 1). Không phải bằng chứng về độ lớn.
2. **Data thật (nếu có) chứng minh HIỆU ỨNG TỔNG ở hạt ngày** — bằng holdback hạt (driver × ngày),
   công suất đã tính: MDE 4.188đ (hàng 2).
3. **Một kênh (positioning) chứng minh CHUỖI NHÂN QUẢ** — vì `public_driver_hex_tracking` đủ mịn; với
   điều kiện `coverage_mode` không phải `CAMPAIGN_ONLY` (§9.1).

**Trụ KHÔNG tồn tại:** quy gán cho **từng lời khuyên** ở 6/7 kênh. Nếu ai cần trụ đó, câu trả lời
trung thực là *"hợp đồng này không cấp nó, và không có nguồn nào trong tầm với cấp nó"* — **không
phải** *"chúng tôi sẽ xin GSM"*.

---

## §5. Cơ chế CODE chống tự lừa

Luật: **lời hứa không có test thì tính 0 điểm.** Mỗi mục dưới đây là một hàm/test + assert cụ thể.

### 5.1 (a) Từ chối tính số khi mẫu số vắng

```python
# tests/test_claim_gate.py
def test_ratio_claim_without_denominator_is_refused():
    c = _claim(unit="ratio", value=1.0, denominator_n=None)
    assert adjudicate(c)["state"] == "REFUSED"
    assert "DENOMINATOR_EMPTY" in {r["reason_code"] for r in adjudicate(c)["refusals"]}

def test_zero_denominator_forces_null_not_zero_and_not_one():
    for v in (0.0, 1.0):
        out = adjudicate(_claim(unit="ratio", value=v, denominator_n=0))
        assert out["state"] == "REFUSED" and out["value"] is None

def test_regression_standby_alloc_100pct_would_be_refused():
    """Lỗi THẬT của repo: standby_alloc báo 36/36 = 100% vì mẫu số thiếu 86 dòng.
    Và D-M3-01: rest_window báo adherence 1,0 theo CẤU TRÚC vì kênh không rút coin."""
    out = adjudicate(_claim(unit="ratio", value=1.0, denominator_n=36,
                            quantity="decision_adherence", adherence_denominator="decision"))
    assert out["state"] != "SUPPORTED"   # dataset MOCK ⇒ tối đa DEGRADED
```

Điểm then chốt: `denominator_n` là **`required`** khi `unit ∈ {ratio, pp}` (§2.7 `allOf` nhánh 1).
Cả hai thiết kế có cổng claim đều để `n` nằm trong một object `uncertainty` **nullable và không
required** ⇒ đúng lỗi repo đã mắc vẫn validate sạch.

### 5.2 (b) Không thể trộn MOCK với THẬT trong cùng một phép so sánh

Ba lớp, vì một lớp không đủ:

```python
def test_mixed_dataset_label_in_provenance_is_refused():
    c = _claim(provenance=[_p(dataset_label="REAL"), _p(dataset_label="MOCK")])
    assert "MIXED_DATASET_LABEL" in _codes(adjudicate(c))

def test_label_cannot_be_upgraded():
    c = _claim(dataset_label="REAL", provenance=[_p(dataset_label="MOCK")])
    assert "LABEL_UPGRADED" in _codes(adjudicate(c))

def test_partition_rule_rejects_two_labels_in_one_partition():
    with pytest.raises(IngestError, match="dataset_label"):
        ingest(rows=[{"dataset_label": "MOCK", ...}, {"dataset_label": "REAL", ...}])

def test_join_across_mock_and_real_is_blocked():
    """Cầu nối advice↔tiền là F6(của TA, MOCK) JOIN F1(REAL). Lớp partition KHÔNG bắt
    được join — nó chỉ gác TRONG một partition. Đây là lỗ mà thiết kế thắng để trống."""
    with pytest.raises(JoinLabelMismatch):
        dw.join(F6_mock, F1_real, on=["driver_key", "date_key"])
```

⚠ **Tôi đổi luật của thiết kế `hybrid`:** nó cho phép trộn miễn khai nhãn thô nhất. CLAUDE.md §5 viết
*"không trộn mock với dữ liệu thật"* — là **KHÔNG TRỘN**, không phải *"trộn thì khai"*. Nên
`MIXED_DATASET_LABEL` là `REFUSED`, không phải `DEGRADED`.

### 5.3 (c) Một giả định không thể lặng lẽ mất nhãn khi được trích lại

```python
def test_every_dw_field_has_provenance():
    """M1 phủ TRỌN: mỗi property của mỗi schema dw/ có ĐÚNG 1 dòng field_provenance,
    if_wrong_2x không rỗng, reopen_condition không được là 'GSM cấp thêm data'."""

def test_self_fit_params_are_labeled():
    """7 tham số đo-từ-sim-nạp-lại-sim PHẢI mang provenance_kind=SELF_FIT.
    Đây là trục mà hợp đồng chỉ-theo-tầng KHÔNG bắt được: chúng ở tier CAO NHẤT."""
    for k in ("accept_logit_center_vnd", "max_realized_accept", "trips_per_hour_est",
              "actors.n", "drop_demand_alpha", "cancel_after_accept_rate",
              "idle_impatience_step_min"):
        assert provenance_of(k).kind == "SELF_FIT"

def test_degenerate_payout_ratio_detector_fires_on_realdata_v1():
    """GATE ĐÃ SỬA — cả ba thiết kế đặc tả sai gate này.
    ĐO: ratio thô có 9.816 giá trị phân biệt (jitter do round()); var toàn cục 0,0246 > 0;
    var trong-tài-xế max 1,89e-11 ≠ 0; n_distinct trong một tài xế lên tới 84.
    ⇒ gate 'var > 0' PASS (sai). gate 'n_distinct <= 3' KHÔNG FIRE. gate 'var == 0' KHÔNG FIRE.
    Gate ĐÚNG: làm tròn ĐỦ để triệt jitter, rồi đếm TRONG từng driver_type."""
    r = (df["commission"] / df["total_fee"]).round(4)
    per_kind = df.with_columns(r.alias("r")).group_by("driver_type").agg(
        pl.col("r").n_unique().alias("nu"))
    assert (per_kind["nu"] <= 1).all()          # fire trên mock hiện hành
    report(DEGENERATE_PAYOUT_RATIO, blocks_claim="CLAIM-PAYOUT-NOT-GROSS")
```

Và cơ chế quan trọng nhất của trục này: **`M3 data_quality_check` là DỮ LIỆU có runner, không phải
prose.** `x-ingest-invariants` ở §2.4 là **mảng object có `id` + `runner` + `vacuous_on_mock`**, không
phải mảng chuỗi tự do. Lý do: một runner đếm "5/5 PASS" trên một tập gồm một đồng nhất thức sẽ tạo
đúng cảm giác an toàn giả mà cảnh báo prose định chống.

```python
def test_vacuous_invariants_are_excluded_from_pass_count():
    """INV-MONEY-ADD (gross == payout + platform) PASS 100% trên mock vì mock ĐỊNH NGHĨA
    platform := gross - commission (ĐO: 12.805/12.805). Nó KHÔNG được tính vào tử số của
    bất kỳ báo cáo 'n/n invariant PASS' nào."""
    rep = run_invariants(F1, dataset_label="MOCK")
    assert rep.counted_total == len([i for i in F1_INV if not i["vacuous_on_mock"]])
    assert "INV-MONEY-ADD" in rep.excluded_vacuous
```

### 5.4 (d) Trường sức khoẻ không thể xuất hiện trên đường tính tiền

Xem §7 — cơ chế ở đó, vì nó cần một ranh giới tinh hơn "cấm".

Cộng invariant cho lỗi `[ĐO]` ở §1.4 hàng 5:

```python
def test_dwell_ge_300s_never_exceeds_online_time():
    """ĐO: vi phạm ở 746/8.022 driver-day (9,3%), tệ nhất +19,57 giờ.
    Một trạng thái BẤT KHẢ (đứng yên nhiều hơn thời gian online) phải fail-loud,
    không được đi vào fact rồi trở thành 'idle_share' của một lời khuyên."""
    v = joined.filter(pl.col("dwell_ge_300s_seconds") / 3600 > pl.col("online_time"))
    assert v.height == 0, f"{v.height} driver-day bất khả — BUG-PI5b-01 tái sinh"
```

### 5.5 Quarantine không chạm đường tiền

```python
def test_no_quarantine_measure_on_money_path():
    """4 bảng 0-cột-biết: trips, driver_penalization_ATA, public_frauds,
    public_user_mission_progress. `trips` nghiêm trọng nhất — nó nuôi 4 solver."""
    bad = [r for r in field_provenance
           if r.derived_from_quarantine and r.money_path == "ON_MONEY_PATH"]
    assert not bad

def test_h3_reject_rate_is_reported_not_silent():
    """ĐO: 51,54% pickup_h3 của trips là token '8amock##' ⇒ reject-rate PHẢI ra 51,54%.
    Nếu ra 0% thì cổng pattern hỏng. Và target_hex reject 100% (68.493/68.493) —
    con số đó phải HIỂN THỊ, vì nó là lý do reached_target là UNVERIFIABLE."""
    assert abs(reject_rate("trips.pickup_h3") - 0.5154) < 0.001
    assert reject_rate("hex_tracking.target_hex") == 1.0
```

### 5.6 Arm đối chứng phải SẠCH (tiền lệ `DET-01`)

```python
def test_arm_constant_within_randomization_unit():
    """Không có ràng buộc này, 14 dòng (băng × kênh) của cùng một driver-day mang arm
    khác nhau và validate sạch."""
    g = F6.group_by(["driver_key", "date_key"]).agg(pl.col("assigned_arm").n_unique().alias("n"))
    assert (g["n"] == 1).all()

def test_causal_claim_requires_measured_control_adherence():
    """DET-01: cờ cadence.enabled tắt luôn keyed coin ⇒ arm đối chứng nghe lời +10đp
    vì lý do không liên quan ⇒ đã báo −3.048đ, sự thật −1.530đ (sai gấp đôi)."""
    assert "CONTROL_ARM_DIRTY" in _codes(adjudicate(
        _claim(kind="CAUSAL_DAY_HOLDBACK", randomization={..., "control_arm_effective_adherence": None})))
```

### 5.7 Rò tương lai — lớp lỗi, không phải một ca

```python
def test_as_of_never_before_window_end():
    """Chốt cho lớp lỗi §3.3. Ceiling KHÔNG bắt được nó (provenance day, claim day)."""
    assert "AS_OF_BEFORE_WINDOW_END" in _codes(adjudicate(
        _claim(as_of="2026-07-15T08:00:00+07:00", window_end="2026-07-15T23:59:59+07:00")))

def test_uncuttable_field_forces_degrade():
    """acceptance_rate và online_time KHÔNG cắt được tại t_now — GSM không có timestamp.
    Chúng phải mang uncuttable=true, và claim dùng chúng không được nói 'đang'."""
    assert provenance_of("driver_statistic_daily.acceptance_rate").uncuttable is True
```

---

## §6. Tách tiền

### 6.1 Ba loại sống ở đâu

| Loại | Trường canonical | Bảng | Nguồn GSM | Điều kiện tồn tại |
| --- | --- | --- | --- | --- |
**GROSS** | `gross_vnd` | F1 | `total_fee_{band}` (cột **thật**) | luôn có |
**PAYOUT** | `payout_vnd` | F1 (cùng dòng) | `commission_{band}` (cột **thật**) | luôn có — **mục tiêu mặc định** |
**PLATFORM_TAKE** | `platform_vnd` | F1 | `revenue_not_relate_driver_{band}` | luôn có, nhưng `IDENTITY` trên mock |
**ESTIMATED_NET** | `estimated_net_vnd` | **F7 — BẢNG KHÁC** | không bảng nào | **chỉ khi có `cost_model_version` được duyệt. Hôm nay: 0 dòng** |

**Việc di trú bắt buộc:** `[ĐỌC]` `schemas/l3/session_summary_input.schema.json:45` **đã có**
`estimated_net_vnd` như một field dữ liệu; `weekly_khoan_input`, `penalty_explain_input`,
`mission_select_input`, `l1/trip_record`, `l1/payout_ledger` cũng có trường `_vnd`. Không được phát
biểu *"net không tồn tại ở tầng dữ liệu"* rồi bỏ qua chúng. `[ĐỌC]` điểm tốt cần giữ:
`from_l1r.py` hiện **đã** để `estimated_net_vnd: None` + `net_definition_version: None` — đúng §5.

### 6.2 Sáu cơ chế cấm trộn

1. **Bảng khác + FK NOT NULL.** `estimated_net_vnd` **không phải một cột của F1**. Muốn có net phải
   `JOIN F7 ON (driver_key, date_key)`, và F7 có `cost_model_version` **required + FK NOT NULL** ⇒
   không có version ⇒ **JOIN trả rỗng** ⇒ net **KHÔNG TỒN TẠI**, không phải bằng 0.
   Đối chiếu: `configs/pilot_dongda.yaml` đặt `cash_cost_vnd_per_km: 0` — **bảng rỗng không nói dối,
   số 0 thì có.** (Công bằng với artifact hiện có: comment tại chỗ **có** nêu 0 là đúng chính sách cho
   tài xế Platform, **kèm** dải sweep 70–93đ/150đ và ghi "biến THEO COHORT × THỜI ĐIỂM". Nó có nhãn,
   có nguồn, có dải — cơ chế F7 mạnh hơn, không phải vì artifact cũ tệ.)
2. **Cấm tên trung tính.** Không schema DW nào được có trường `revenue`, `income`, `amount_vnd`,
   `money`, `earnings`. Test `test_no_neutral_money_field_names` quét `schemas/dw/**`.
   Trường cũ trong `l1r/*` là **mirror bảng GSM** ⇒ whitelist tường minh, **nhưng** solver không được
   đọc trực tiếp: phải qua F1.
3. **`x-forbidden-properties` + test đọc chính nó** (không dựa vào tác giả nhớ).
4. **Kiểu tiền — `[ĐO]` bản của thiết kế `event-sourced` BỊ HỎNG.** Tôi chạy: `max([Money("ESTIMATED_NET",999_999), Money("GROSS",1)])` → **`GROSS 1`**;
   `Money("GROSS",100_000) < Money("PAYOUT",75_000)` → **True**; `Money(...) == ("PAYOUT",75_000)` →
   **True**; `a*2` → `tuple` (guard bốc hơi). Trong một repo đã có **`BUG-EVAL-ARGMAX`** và solver
   argmax trên tiền (`shift_dp`), một kiểu mà `max()` sắp theo **tên kind** tệ hơn không có kiểu.
   Bản đúng:
   ```python
   @dataclass(frozen=True, order=False, eq=True)   # order=False: KHÔNG có <, >, max()
   class Money:
       kind: Literal["GROSS","PAYOUT","PLATFORM_TAKE","ESTIMATED_NET"]
       vnd: int                                     # VND NGUYÊN, không float tiền
       def __post_init__(self):
           if not isinstance(self.vnd, int): raise MoneyTypeError("tiền phải là int")
       def _same(self, o): 
           if not isinstance(o, Money) or o.kind != self.kind:
               raise MoneyKindError(f"cấm trộn {self.kind} với {getattr(o,'kind',type(o))}")
       def __add__(self, o): self._same(o); return Money(self.kind, self.vnd + o.vnd)
       def __sub__(self, o): self._same(o); return Money(self.kind, self.vnd - o.vnd)
       __radd__ = __add__
   def money_max(xs: list[Money]) -> Money:         # so sánh TƯỜNG MINH, cùng kind
       kinds = {x.kind for x in xs}
       if len(kinds) != 1: raise MoneyKindError(f"money_max trên nhiều kind: {kinds}")
       return max(xs, key=lambda m: m.vnd)
   ```
   ```python
   def test_money_has_no_implicit_ordering():
       with pytest.raises(TypeError): Money("GROSS",1) < Money("PAYOUT",2)
       with pytest.raises(TypeError): max([Money("GROSS",1), Money("PAYOUT",2)])
   def test_money_not_equal_to_plain_tuple():
       assert Money("PAYOUT",75_000) != ("PAYOUT",75_000)
   ```
5. **Gate suy biến** — §5.3, gate đã sửa cho đúng `[ĐO]`.
6. **Bất đối xứng bền/không-bền phải nói ra.** Claim `money_kind = PAYOUT` với `kind` bắt đầu
   `CAUSAL_` **bắt buộc** có caveat khớp `share_sensitivity`: *"Δ bền với `driver_share` (hệ số nhân
   chung hai arm); MỨC tuyệt đối KHÔNG bền — dải official [0,75–0,91], lệch tới 21,3%."*

### 6.3 `estimated_net` — cổng phủ trọn, không phải cổng ≥1

`[ĐỌC]` `resolve_cost_params` trả **đúng 2** term. Nếu cổng chỉ đòi "≥1 item và không có UNKNOWN",
producer chỉ cần **bỏ hẳn** term không biết ra khỏi array ⇒ 1 term ACTIVE là pass, và
*"biết hết chi phí"* đúng khi liệt kê **0** chi phí. Vì vậy §2.7 đòi **phủ trọn enum 5 term** và
`adjudicate` raise `COST_TERMS_INCOMPLETE` khi vắng. Hôm nay `fixed_daily` (**50–67k/ngày**, lớn hơn
Δ mười lần), `maintenance`, `depreciation` **không có nguồn** ⇒ F7 rỗng là **phát biểu trung thực duy
nhất**.

---

## §7. PII và ranh giới chia sẻ · sức khoẻ ngoài đường tiền

### 7.1 PII

| Trường | Lớp | Xử lý |
| --- | --- | --- |
`full_name`, `phone_number`, `sap_profile_id`, `driver_name`, `sap_id`, `email`, `tel`, `engname`, `vehicle_vin_number`, `vehicle_license_plate`, `customer_id` | **direct-ID** | **DROP tại ingest boundary** — không persist. Test `test_dropped_pii_absent_from_all_dw_schemas` |
`driver_id` | ID | `driver_key = HMAC-SHA256(pepper, id)[:32]` (HMAC không hash trần: không gian driver_id nhỏ ⇒ brute-force được). pepper ngoài repo; `driver_key_era` bắt buộc |
`lat`/`lon` thô | **PII cao nhất** | không persist; chuyển h3 res9 tại boundary, buffer thô ≤24h rồi xoá |
`hex_history`, chuỗi visit của một người | **QUASI-ID-trajectory** | §7.2 — nguy hiểm hơn `driver_id` |
tiền cấp cá nhân | sensitive | `audience=stakeholder` ⇒ làm tròn 1.000đ + k≥5 |

### 7.2 Trajectory — pseudonymize `driver_id` KHÔNG đủ

Nơi ở suy ra được từ ô đầu ca và ô cuối ca. Bốn luật, nhận nguyên precedent Chicago TNP (làm tròn
thời gian 15′, cước $2,50, tip $1,00, suppress census tract vùng thưa, chỉ centroid) với một nguyên
tắc: **độ phân giải là PHẦN CỦA SCHEMA (`x-max-resolution`), không phải chi tiết cài đặt.**

- **L-PII-1:** `hex_history` **không tồn tại như một trường** ở bất kỳ entity DW nào.
- **L-PII-2:** view CÔNG BỐ hạ res9 → **res8**; res9 chỉ trong vùng phân tích có row-level access.
- **L-PII-3:** aggregate không-gian công bố cần **k ≥ 5 driver** trong `(giờ × ô)`; dưới k thì
  **suppress**, không làm tròn. ⚠ **Phải khai mức mất mát này ở hạt thật sự cần**, vì nó lớn:
  `[ĐO]` F4 chỉ phủ **90/150** driver và `[KẾ-THỪA]` ở hạt `(ngày × giờ × ô)` — hạt mà mọi phân tích
  không-gian-theo-thời-gian cần — **~73%** ô bị suppress. Không được nói nhẹ thành "một số ô sẽ có k=1".
- **L-PII-4:** cấm truy vấn "ô đầu/cuối của tài xế trong ngày" ở mọi view công bố — đó **chính là**
  truy vấn suy ra nơi ở. Bổ sung: **suppress 15′ đầu và 15′ cuối mỗi session** khỏi mọi export.

### 7.3 Ai thấy gì

| Vai | Thấy | Không thấy |
| --- | --- | --- |
tài xế | dữ liệu **của chính mình**, đầy đủ res9, kèm `caveats`; claim `REFUSED` hiện `human_reason` **thay cho** con số | của người khác; mọi `meta_*` |
advisor runtime | `driver_key`, ô res9 hiện tại, aggregate ngày đã đóng, Ring `E3` | lat/lon thô; lịch sử res9 >7 ngày; PII-direct |
analyst | pseudonym, res8, bucket 15′, k≥5, tiền làm tròn 1.000đ | trajectory đầy độ phân giải; 15′ đầu/cuối ca; bảng liên kết |
engineer_dev | dòng pseudonymized trên partition `MOCK` | **partition `REAL` cấp dòng** (chỉ aggregate) — đây là "không trộn" ở tầng quyền |
auditor | toàn bộ `M1`–`M4`, `ingest_run_id`, số dòng | measure cấp tài xế |
hội đồng (`external`) | **chỉ** `measurement_claim` k≥5 + `M4 grain_capability` (bậc thang claim) + toàn bộ §3/§4 dưới dạng truy vấn | mọi thứ cấp dòng |

### 7.4 Sức khoẻ: ranh giới TINH, theo Quyết định 2026-07-30

⚠ **Đây là mục tôi sửa nặng nhất so với cả ba thiết kế**, vì cả ba viết trước hoặc bỏ qua
`tracking/QUYET-DINH-2026-07-30-nam-diem.md`, và hai trong ba đề xuất luật **trái** quyết định đó.

`[ĐỌC]` Quyết định 1 (2026-07-30): **`rest_window` là kênh DEMAND-TIMING** — nó **ở TRONG bảng tiền**,
**chịu cadence**, và **phải chịu `coin_follows`**. Lý do từ chối nhãn SAFETY: nhãn đó **đảo nghĩa**
kênh (nó **LẤY NGHỈ ĐI**), và bypass cadence + adherence 1,0 sẽ tạo một kênh được nói vô hạn và luôn
được nghe theo.

⇒ Luật *"card `rest_window` không được chứa key `.*_vnd$`"* mà một thiết kế đề xuất **vi phạm quyết
định đã chốt**. Không nhận.

Ranh giới đúng là **`[ĐỌC]` §1.2b của `specs/advisor-objective-model-v2.md`**:

| Đại lượng | Trạng thái | Vì sao |
| --- | --- | --- |
**LƯỢNG nghỉ** | **RÀNG BUỘC CỨNG** (`rest_min_per_4h`) — bất biến, không phải biến | Nghỉ là ràng buộc, không phải số hạng của objective |
**THỜI ĐIỂM nghỉ** | **BIẾN**, định giá bằng **`C2′`** = `−(payout_kỳ_vọng(giờ_nghỉ) − payout_kỳ_vọng(giờ_vắng_nhất))` | Đường **DUY NHẤT** làm lời khuyên nghỉ có Δ tiền đo được **mà KHÔNG tạo tỷ giá sức-khoẻ↔tiền**: lượng nghỉ **giữ nguyên**, chỉ thời điểm là biến |
**MỆT (`fatigue`)** | **LATENT** — không ai đọc để tính tiền | Mọi cơ chế cho mệt một hậu quả năng lực tạo `payout = f(F)`, tức `∂payout/∂F`. Viết vào *world* thay vì *objective* **không xoá tỷ giá, chỉ xoá NHÃN** |

**Vì sao điều này quan trọng cho test:** `[ĐỌC]` `src/gsm_core/solvers/shift_dp.py` — `rests_left` **là
một chiều của state space** (`:156`), `_required_rest(B, params, rest_taken_min, shift_elapsed_min)`
(`:54`), và `rests_left > 0` tại `B` ⇒ `NEG` (`:182`). Tức **nghỉ ĐÃ ở trong DP tối đa hoá tiền của
S2 hôm nay** — và điều đó **hợp đạo đức**, vì nó là **ràng buộc khả thi**, không phải số hạng có hệ số.

⇒ Một test kiểu *"objective bất biến khi perturb dữ liệu nghỉ"* sẽ **hoặc xanh vô nghĩa** (nếu canh
một namespace chưa ai dùng — `[ĐỌC]` `f3_patterns.py:49,55` đang đọc `rest_likely` từ
`l2i/inferred_activity`, entity **đã tồn tại**), **hoặc đỏ đúng trên S2 rồi dẫn tới bản "sửa" bắt S2
thôi tôn trọng nghỉ sinh lý** — tệ hơn hiện trạng. Cặp test đúng:

```python
def test_objective_invariant_under_guardrail_WEIGHT_perturbation():
    """Perturb TRỌNG SỐ của mọi đại lượng sức khoẻ. Objective PHẢI bất biến chính xác —
    vì không tồn tại trọng số nào (không có ∂payout/∂F)."""
    for f in (0.5, 2.0):
        assert solve(spi, w_health=f) == solve(spi, w_health=1.0)

def test_objective_DOES_change_under_feasible_set_perturbation():
    """Perturb RÀNG BUỘC (rest_min_per_4h). Objective PHẢI ĐỔI — nếu không, ràng buộc
    nghỉ đang không có tác dụng. Đây là test mà phiên bản 'cấm hết' làm ngược."""
    assert solve(spi, rest_min_per_4h=1) != solve(spi, rest_min_per_4h=3)

def test_no_fatigue_in_payout_path():
    """CHƯA TỒN TẠI (spec §1.2b tự khai). Grep: fatigue/F/mệt không xuất hiện trên
    đường từ state tới một số VND. l2i/inferred_activity + features/infer_activity.py
    + l3/shift_plan_input.{rest_taken_min,shift_elapsed_min} ĐỀU trong phạm vi quét."""

def test_rest_defer_max_min_is_policy_locked():
    """CHƯA TỒN TẠI — grep POLICY_LOCKED toàn repo = 0 kết quả (ĐO).
    Điều kiện TIÊN QUYẾT của C2′: nếu rest_defer_max_min sweep được, sẽ xuất hiện một
    bảng 'hoãn lâu hơn = nhiều tiền hơn' tạo áp lực nới trần."""
    assert "rest_defer_max_min" in POLICY_LOCKED_KEYS
```

F8 `day_wellbeing_observable` là bảng riêng, `x-money-path: "GUARDRAIL_ONLY"`, chứa `online_minutes`,
`longest_dwell_minutes` (INFERRED, dwell ≠ nghỉ), `consecutive_active_days`,
`days_since_zero_order_day`. Không tồn tại và không được thêm: `fatigue_score`, `rest_debt`,
`health_index`, `fatigue_cost_vnd`. `[ĐỌC]` repo đã có tiền lệ đúng —
`tests/test_schemas.py::test_latent_fields_absent_from_l1` chặn `fatigue`/`belief`/`patience` khỏi L1
⇒ **mở rộng** test đó sang `schemas/dw/**` thay vì viết mới.

**Guardrail chỉ VETO, không trả số:** `-> GuardVerdict(allow: bool, reason: str,
next_eligible_min: int | None)`, không field float. Không có số ⇒ không có gì để nhân với tiền.
`[KẾ-THỪA]` lan can hiện chặn **71,0%** cơ hội của kênh nghỉ (`soc_low` 44,1% + `fatigued` 26,9%).

**Bias phải khai trong mọi báo cáo dùng `C2′`** `[ĐỌC]` spec §1.2b: sim **không có kênh tác hại nào**
của việc hoãn nghỉ (không tai nạn, không giảm chất lượng, không mệt qua đêm — `D-SIM-16`) ⇒ **mọi Δ
dương của lời khuyên hoãn nghỉ đều dương quá mức theo cấu trúc.**

**Bẫy income-targeting → DEFERRED, không sửa code ngay.** Uber đã làm đúng loại can thiệp này
(earnings-goal nudge khi tài xế định logout) và data nội bộ cho thấy nhiều tài xế mới thực hành
*"extreme form of income targeting"* — ca rất dài ngày vắng khách, về sớm ngày đông khách, tức nudge
đẩy họ làm điều **trái lợi ích của chính họ**. **Mục tiêu thu nhập theo NGÀY chính là phản pattern
đó.** Cộng với việc **không mô hình hoá hậu quả của mệt**, sẽ **không đại lượng nào trong mô hình
phản đối lại** ⇒ đây là lý do "guardrail trả enum" là ràng buộc bắt buộc, không phải trang trí.

---

## §8. Thi công từng bước

### 8.1 Làm được NGAY với mock hôm nay, và ĐÁNG làm

Xếp theo (giá trị ÷ chi phí). Mỗi bước có gate.

| # | Việc | Vì sao đáng | Gate |
| --- | --- | --- | --- |
| B0 | Đính chính §2.9 (đóng `TBC`/`XIN GSM`, sửa "5 bảng"→4, thêm `generated_at`, sửa catalog `stoppoints`) | Rẻ nhất, và đang **nói sai sự thật** trong docs source-of-truth | `test_no_TBC_availability_remains`, `manifest_has_generated_at` |
| B1 | **Khảo sát adherence tài xế thật** (n nhỏ cũng được) | `[§4 hàng 14]` Tham số **duy nhất** trong config hiệu chỉnh được **không cần GSM**, và là tham số nhân trực tiếp vào **mọi** Δ A/B, với rủi ro **bất đối xứng dồn về phía xấu** | thay `ENGINEERED_GUESS` → `MEASURED_*` ở `field_provenance` |
| B2 | `measurement_claim` + `claim_gate.py` + 7 test §5 | Biến ba luật §5 CLAUDE.md thành điều kiện validate. **Không phụ thuộc GSM một byte** | máy trạng thái §2.7: `PLAN_RECOMMENDATION` và `CAUSAL_MRT` phải **SUPPORTED** với input hoàn hảo; claim "thẻ 14h ra X đồng" phải **REFUSED** |
| B3 | Sửa `Money` (frozen dataclass `order=False` + `money_max`) | `[ĐO]` bản NamedTuple cho `max()` **sai đáp án** trong repo đã có `BUG-EVAL-ARGMAX` | `test_money_has_no_implicit_ordering` |
| B4 | Sửa 3 rò tương lai ở `from_l1r.py` (§3.3) + mẫu số `points_per_hour` theo băng | Lỗi **đang sống**, và F1 (hạt băng) **chữa lành** mẫu số — đây là một trong ít lỗi mà hợp đồng này **sửa được**, không chỉ từ bỏ | regression từ 2 probe: `acceptance` ≠ số cuối ngày lúc 08:00; `peak` ≈13đ/h không phải 0,9 |
| B5 | Sửa generator: `8amock##` → H3 thật (cả `pickup_h3` và **`target_hex`**); nối `reached_target` với hình học; `stoppoints` theo cơ chế thật | `[ĐO]` 51,54% + 100% token bịa. Không sửa thì §4 hàng 9 vĩnh viễn KHÔNG THỂ KIỂM | `test_all_h3_tokens_are_valid_h3`, `test_reached_target_implies_geometry` |
| B6 | Chặn `RNG_NOISE` ra mặt tài xế (S9 "độ tin cậy X%", S8 tiền trừ) | Vi phạm §5 **nặng nhất trong hệ**, và fix là một nhánh `if` | `test_rng_noise_never_driver_facing` |
| B7 | `field_provenance` (M1) đủ cho F1–F8 + `test_every_dw_field_has_provenance` | Biến §3 thành **dữ liệu truy vấn được**, và là chỗ duy nhất `SELF_FIT` bị buộc tự khai | `if_wrong_2x` không rỗng; `reopen_condition` ≠ "GSM cấp thêm data" |
| B8 | Dựng F1–F5 + M2/M3 từ 13 bảng; quarantine 4 bảng | Xương sống. `[ĐỌC]` rẻ nhất **bây giờ** vì `from_l1r` chưa có consumer production | invariant §2.4 (loại vacuous); reject-rate `trips.pickup_h3` = **51,54%** |
| B9 | **Bật E4**: thêm `randomization {design_id, unit, p_t, arm_constant_within_unit, control_arm_effective_adherence}` vào `advice_lifecycle_event` (bump 1.0.0→1.1.0 + upcaster **không bịa** trường cho record cũ) | Đường **DUY NHẤT** để một ngày nói được "lời khuyên có tác dụng" bằng thiết kế giới học thuật chấp nhận — **trên chính sản phẩm ta, 0 byte mới từ GSM**. Chi phí: một cờ + một trường | `test_persisted_old_records_still_validate`; `availability=false ⇒ arm=holdback` |
| B10 | F8 + `wellbeing_gate` + 4 test §7.4 (gồm 2 test **chưa tồn tại** mà spec tự khai: `test_no_fatigue_in_payout_path`, `POLICY_LOCKED_KEYS`) | `[ĐỌC]` spec §1.2b: trong 6 cơ chế enforce, **chỉ 2 tồn tại**. `C2′` **không được đo trước khi 4 cái còn lại có thật** | `test_objective_invariant_under_guardrail_WEIGHT_perturbation` **và** `test_objective_DOES_change_under_feasible_set_perturbation` |
| B11 | Chuyển `from_l1r.py` đọc DW | Không rẻ: là viết lại tầng feature của 9 solver, và `[ĐỌC]` mỗi `derive_*` đang tự đặt lại giả định (bucket 30 vs 60, `p_accept=0.9`, `avg_dist_km=3.0`). **Cần plan riêng, không phải một dòng bảng** | output solver không đổi ở đâu phải **chứng minh**; đổi ở đâu phải **giải thích bằng §3** |

### 8.2 Chỉ là ĐẶC TẢ, chờ dữ liệu **không bao giờ tới**

Viết ra để biết ranh giới, **không** mở task, **không** ước lượng, **không** đưa vào roadmap.

| Đặc tả | Chờ gì | Trạng thái vĩnh viễn |
| --- | --- | --- |
`offer_event` (offer_shown/accept/decline cấp giây) | GSM cấp event lời mời | `NOT_PROVIDED_CLOSED`. ⚠ **KHÔNG tạo entity mới** — `[ĐỌC]` `schemas/l1/app_event.schema.json` **đã có** đủ `kind`. Chỉ đổi `x-availability` |
`session_event` (go_online/go_offline) | GSM cấp event bật/tắt app | như trên, cùng entity `app_event` |
`swap_event` + `soc_pct` | GSM cấp telemetry pin + bảng đổi pin | `NOT_PROVIDED_CLOSED` ⇒ **bỏ hẳn kênh `swap_window`** khỏi production (§4 hàng 11) |
`station_capacity` / `zone_supply` (S4) | GSM cấp sức chứa trạm/zone | `NOT_PROVIDED_CLOSED` ⇒ claim "cứu hệ thống" (§4 hàng 13) không tái lập được |
`rest_taken_min` / `shift_elapsed_min` cấp phút | GSM cấp mốc nghỉ | ⇒ fix Cycle R/H1 **tái sinh lỗi** trên đường thật (§4 hàng 12) |
cầu **KHÔNG được phục vụ** | GSM cấp đơn chưa gán | ⇒ `demand_forecast` lệch **xuống có hệ thống** đúng nơi/giờ cung không đủ — lệch **đúng hướng làm herding tệ hơn** |
`trips` cột thật · `driver_penalization_ATA` · `public_frauds` · `public_user_mission_progress` | GSM cấp schema 4 bảng | `TABLE_NAME_ONLY` **vĩnh viễn**. 52 trường nghiệp vụ là phần ta **THIẾT KẾ**, không phải phần ta **CÓ** |
MDS 2.0 làm **hạt** dữ liệu | — | **Không nhận.** Nhận **TÊN** (`commission ↔ driver_trip_pay`, `trip_type: empty` = deadhead, `shift_id`, `dispatch_time`) và định nghĩa payout kiểu TLC. Một fact hạt-cuốc ta không thể điền là một **hư cấu** |

---

## §9. Rủi ro và cái tôi có thể sai

### 9.1 Rủi ro đơn lẻ lớn nhất — không kiểm được mà không có data

**`public_driver_hex_tracking` có thể là bảng trạng thái theo campaign, không phải dấu vết vị trí.**
`[SUF]` Bảng thật ở dataset `GSM_MISSION_SERVICE_APPEND` và có `campaign_id`, `log_id`,
`schedule_job_id`, `target_hex`, `hex_history`, `updated_at` — đọc như một **dòng trạng thái theo
(driver × campaign)** replicate append-only qua CDC, không như ~169 dòng/driver-ngày mà mock sinh.
Nếu đúng: **data thật KHÔNG có vị trí ngoài campaign** (mock `[ĐO]` `campaign_id` NULL **95,01%** —
ngược hoàn toàn) ⇒ **F4 sụp**, và cùng với nó sụp: trụ 3 của §4.1, kênh adherence **duy nhất** đo
được, và mọi phân tích idle/reposition. **Không có cách kiểm.** ⇒ `coverage_mode` mặc định
`UNKNOWN`, và mọi claim positioning phải mang caveat này.

### 9.2 Chỗ tôi có thể sai

1. ~~**`commission → driver_payout`** — *"không test nào bắt được nếu tôi đọc ngược"*~~
   ⚠ **RỦI RO NÀY ĐÃ ĐƯỢC HẠ CẤP** — agent chính tìm được một phép kiểm độc lập mà mục này bỏ sót
   (2026-07-30, `[ĐO]` + `[ĐỌC]` nguồn ngoài):

   | Cách đọc | driver payout/ngày (median, mock) | share ngụ ý | So dải CÓ NGUỒN |
   | --- | --- | --- | --- |
   | **A — `commission` = phần TÀI XẾ** (cách đang dùng) | **272.388đ** | **0,698** | ✅ **trong dải** `[0,75–0,91]`, sát cận dưới |
   | **B — `commission` = phần NỀN TẢNG** (đọc ngược) | **117.883đ** | **0,302** | 🔴 **ngoài mọi giá trị có nguồn** |

   Hai neo độc lập, **không** đến từ mock:
   - `configs/pilot_dongda.yaml:246` — `driver_share: 0.75` với chú thích dải mâu thuẫn nguồn
     **[0,75–0,91]** (`driver-cost-structure-2026 §5`: 91% official image-locked / 90→85% / 84,5% /
     75%). Cách đọc B ngụ ý share ≈ **0,30** — **không nguồn nào** trong dải đó.
   - `research/simulation/realism-benchmarks.md:18` — payout thật **318–480k/ngày** (VnExpress
     11/2023: sàn ĐBTN 8h=320k, 10h=400k; Znews: bike 9,2h→318k). Cách đọc B cho **118k/ngày**, tức
     **~2,7× DƯỚI** sàn 8 giờ — bất khả với tài xế toàn thời gian. Cách đọc A cho 272k, dưới dải
     nhưng **cùng bậc**, và độ lệch đó đã có tên: `CALIBRATION GAP T-021`.

   ⇒ **Phép kiểm tồn tại, và nó là phép kiểm bên ngoài mock** (dải share có nguồn + mức thu nhập có
   nguồn báo chí). Rủi ro còn lại: cả hai neo là **PROXY/ASSUMPTION có nhãn**, không phải tài liệu
   GSM ⇒ vẫn nên xin GSM xác nhận **nếu** có kênh liên hệ; nhưng không còn là *"không cách nào kiểm"*.
   Việc nên làm: viết `test_commission_is_driver_share` — assert `commission/total_fee` nằm trong
   `[0,70; 0,95]` trên mock, để nếu ai đảo nghĩa thì test ĐỎ.
2. **`producer_kind` không có `'llm'` là ràng buộc NHÃN, không phải bất khả.** Không gì ngăn ai ghi
   `"rule"` cho văn LLM sinh. Cơ chế thật đạt được là khiến việc nói dối **tường minh và audit
   được** — tôi ghi điều này vào schema description để không ai đọc nó thành một bảo đảm.
3. **MDE 4.188đ là số tôi tự tính trên MOCK**, giả định iid trong tài xế và **không tự tương quan
   chuỗi ngày**. Tự tương quan thực tế làm MDE **xấu hơn**. sd 84.617đ là artifact mock (trộn car +
   bike một pool) ⇒ **bậc độ lớn, không phải số công bố**.
4. **Tôi không chạy sim/A-B nào.** Mọi Δ (+6.016đ, −1.530đ, +2.207đ, served +1,74đp) là `[KẾ-THỪA]`
   từ UPDATE; tôi **chưa mở artifact JSON gốc**, và MEMORY cảnh báo *"nhiều artifact đã BỊ TREO"*.
5. **Tôi không tạo file schema nào.** §2 là đặc tả để code, **chưa** qua `SchemaRegistry`, **chưa**
   validate. Các khối `allOf/if/then` của `measurement_claim` **chưa được test bằng validator thật**
   — và đó chính là chỗ hai thiết kế đối đầu vỡ. `adjudicate()` tôi có kiểm tay ba ca (§2.7) nhưng
   không kiểm bằng jsonschema.
6. **Tôi không kiểm `ui/`** xem UI đọc canonical hay tự recompute — nên không biết chi phí thật của
   luật "không chứng thư ⇒ không render".
7. **Tôi không đối chiếu từng trường MDS với `schemas/l1r/*`**, và chưa biết MDS 2.x có JSON Schema
   chính thức để `$ref` hay phải viết lại ⇒ chi phí "nhận tên" chưa lượng hoá.
8. **Con số "140 cột / 9 bảng"** tôi `[KẾ-THỪA]`; tôi tự `[ĐO]` xác nhận phần "**4** bảng CHƯA CÓ
   CỘT" nhưng **không đếm tay lại 140**.
9. **M2/M4 (`ingest_reject`, `grain_capability`)** tôi chỉ mô tả bằng prose + gate, **chưa viết JSON
   Schema** — trong khi B8 và cổng "claim IMPOSSIBLE không lọt tài liệu đối ngoại" phụ thuộc chúng.
   Cần một cycle riêng.
10. **Rủi ro của chính hợp đồng này:** nó gác **tầng dữ liệu**, nó **không gác vòng tròn**. `[KẾ-THỪA]`
    7 tham số đo-từ-sim-nạp-lại-sim nằm ở tier **cao**. Trục `SELF_FIT` **không sửa** vòng tròn — nó
    chỉ khiến vòng tròn **không thể ẩn**. Ai đọc spec này mà tưởng vấn đề hiệu chuẩn đã được giải
    quyết thì đã đọc sai.

### 9.3 Tái lập mọi số `[ĐO]`

Bốn script trong scratchpad phiên này, chạy trên `data/mock/realdata-v1/`:
`m1.py` (tỷ lệ payout), `m2.py` (distinctness + token H3 + mẫu số), `m3.py` (invariant băng + MDE +
online), `m4.py` (rollup hạt-giờ + dwell vs online). Cộng một snippet Python thuần cho lỗi `Money`.
⚠ HEAD ≠ `engine_commit=d325055` ⇒ **regen trước khi dùng làm chứng cứ chính thức**; con số có thể
đổi, và nếu đổi thì §4 phải được dựng lại chứ không sửa tại chỗ.

---

## Phụ lục — trạng thái và việc phải làm kèm

**Trạng thái spec:** `WAITING-VERDICT`. Đây là docs-only ⇒ visual review gate = `NOT_APPLICABLE`.
Không mục nào ở §8 được gọi `DONE` khi `tracking/PENDING-REVIEW.md` còn mở; dùng `DONE-CODE` /
`WAITING-VERDICT`.

**Nhắc lại theo CLAUDE.md §3.1 — `tracking/PENDING-REVIEW.md` còn mở, Cường đang chờ check.**
Việc hoãn check ≠ waive.

**Cần Cường quyết trước khi implement:**

1. **§8.1 B1 (khảo sát adherence)** — việc rẻ nhất, giá trị cao nhất, nhưng cần người thật. Có làm?
2. **§5.2** — tôi đổi luật trộn nhãn từ *"trộn thì khai"* thành **`REFUSED`**, chặt hơn cả ba thiết
   kế. Nếu quá chặt cho giai đoạn pilot thì phải nói bây giờ.
3. **§8.1 B11** (`from_l1r` → DW) là một cycle riêng có plan, không phải một dòng bảng. Xác nhận tách?
4. **§9.2 mục 1** (`commission` = phần tài xế) — giả định blast-radius lớn nhất mà tôi không kiểm
   được. Nếu Cường có bất kỳ nguồn nào về nghĩa cột này, nó đáng hơn cả §2 gộp lại.
