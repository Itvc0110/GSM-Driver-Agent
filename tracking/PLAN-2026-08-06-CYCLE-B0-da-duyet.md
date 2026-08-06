# PLAN — Cycle B0: sửa MẪU SỐ của S1 (đường sản phẩm) + persist verdict root-cause

## Context

Cường hỏi: *"đáng ra thời gian thừa phải vào đơn chứ? đây là do thiết kế sim kém à? tìm root cause"*.
Bốn agent đã chạy xong (rc-01→rc-04). **Root cause đã tìm ra** và **không phải "sim kém" chung chung**:

> Cung rảnh bị **giam trong hai ô "bẫy niềm tin"** — cực đại địa phương của trường cầu **tĩnh lấy từ
> config**, giữ **56,6% toàn bộ phút idle của đội**, cách **mọi** ô nhiều đơn chết **3,40–4,73 km** (ngoài
> cả bán kính chào đơn 2,22 km lẫn bán kính ETA-khả-thi 3,14 km). Tài xế rảnh chỉ **nhìn được 0,74 km**
> (`world.py:1165`) và chỉ **đi lên dốc nghiêm ngặt** (`behavior.py:217`), còn bước *"rỗi lâu ⇒ đi xa hơn"*
> **là NO-OP** vì ring 3 = 1,11 km vượt ngoài tầm nhìn niềm tin. Nên phút rảnh thêm phân bổ **y như hình
> học idle sẵn có** (50,5% Δidle rơi đúng hai ô bẫy, nơi chỉ có 1,57% đơn chết) chứ không di cư về phía cầu.

Phân loại: **MODEL GAP (chi phối) + BUG ×4 + VISIBILITY GAP ×3 tầng**; phân bổ định lượng = `UNRESOLVED`.
Trong đó **2 BUG MỚI** chưa từng có hồ sơ: **bước sốt-ruột là no-op** (B3) và **slider dashboard nối vào
khoá config CHẾT** (B5, đang lừa người xem). Kèm một **hệ quả chính sách** cần Cường quyết: trong world
cố ý dư cung (đội 74→90 để kéo `served_rate` lên 0,797), **cổng payout của ĐA-08 là bất khả thắng về cấu
trúc** cho mọi kênh chỉ giải phóng thời gian.

**Song song đó**, audit math-model tìm ra một lỗi **nặng hơn về mức độ ảnh hưởng thật**, vì nó nằm trên
**đường sản phẩm** chứ không trong sim: **lệch đơn vị mẫu số của S1** khiến advisor phán SAI *"không kịp"*
về mốc thưởng **với tới được**. Đã reproduce, có output thật (`UPDATE-165`, `D-ADV-04`).

**Plan này chọn Cycle B0 (mẫu số S1) làm cycle thi công đầu tiên** vì: (a) nó là **bug đường sản phẩm**,
không phải sim; (b) đã **reproduce** + tôi tự kiểm 4/4 chỗ code; (c) **không phụ thuộc** workflow phản
biện đang chạy; (d) **không đổi hành vi sim** ⇒ không cần re-baseline. Các cycle sim (B3/B2/B5) xếp sau,
theo đúng thứ tự verdict đề xuất, và **cần plan riêng** vì chúng đổi dynamics.

## Việc 1 — Persist verdict root-cause vào repo (không đổi code)

Agent rc-04 bị plan mode chặn nên **chưa ghi được** verdict vào repo. Phải:
- Copy toàn văn verdict (9 mục) → `research/audit/2026-08-06-root-cause-idle/rc-00-VERDICT.md`
- Copy `probe_idle_overlap.py` (scratchpad) → `.../rc-03-probe-script.py` — **rc-03 đang trích một
  đường dẫn KHÔNG TỒN TẠI** ⇒ hồ sơ hiện **không tái tạo được**
- Ghi 5 nợ mới vào `DEFERRED.md`: **B3** no-op sốt-ruột · **B5** slider chết · **B4** sổ thời gian đội hở
  +3,41% (chặng đi trạm đếm HAI lần: `world.py:1248` **và** `1288`) · `idle_min` thừa 3,8% (cộng trước
  `timeout`) · **B2** cooldown-sau-khi-gán nuốt im lặng 69,6% slot gán
- Đẩy **7 đính chính** (verdict §8) lên các artifact/UPDATE trước — gồm **đính chính của tôi**: rc-02 suy
  `Δoccupied` bằng phép trừ là SAI (đo thật: Δoccupied **−65,1′**, Δonline **−208,7′**, sổ hở +3,41%)
- UPDATE-166 + cập nhật `PLAN-2026-08-06-cycles-chi-tiet.md` (Cycle F → tách thành F1..F4 theo verdict §6)

⚠ **Kỷ luật trích số:** con số *"cooldown nuốt 69,6% phép gán"* **phải luôn kèm** câu hạ nhiệt của chính
agent: 2.595 slot chỉ là **366,6 CẶP** khác nhau (mỗi cặp lặp ~7 lần), thiệt hại thật ~**2,5′ đời đơn cho
23% đơn chết** — *không* phải "mất 69,6% năng lực ghép đơn". Trích thiếu câu này là **báo sai cho Cường**.

## Việc 2 — Cycle B0: sửa mẫu số bucket của S1

### Lỗi (đã reproduce)
Producer chia **điểm-của-bucket** cho **giờ online TOÀN NGÀY**; solver tiêu thụ như **điểm/giờ TRONG
bucket** (nhân `rate × span` cho từng giờ thuộc bucket). Vì `giờ_ngày ≥ giờ_bucket` ⇒ rate **luôn** ước
NON (peak thường **5,12×** trên mock). Output thật: producer trả `{peak: 6.0, offpeak: 6.0}` (đúng phải
`{30, 7.5}`) ⇒ S1 phán **INFEASIBLE** *"chỉ kiếm thêm ~42đ < 50đ"*, rate đúng cho **FEASIBLE tại 2,42h**.

**Solver ĐÚNG** (ngữ nghĩa có test ghim `tests/test_bonus_feasibility.py:113-119`) ⇒ **sửa producer**.
`S1` là solver **duy nhất** đường sản phẩm chạy (`B6-PARITY`) ⇒ lỗi đập thẳng vào card tài xế thật.

### Vế thứ hai PHẢI sửa cùng lúc
**Survivorship**: ngày online-phủ-bucket mà **0 điểm** bị loại khỏi mẫu thay vì đóng `0.0`
(`bonus_gap.py:59-64` · `from_l1r.py:156-161` · `advisor.py:73` `if p > 0`) ⇒ bias **LẠC QUAN**, ngược
chiều vế mẫu số. Đo trên mock: sửa mẫu số làm **238 ca** lật infeasible→feasible (0 ca ngược); thêm vế
`0.0` kéo lại **25** (~10%) ⇒ **không bù trừ đối xứng**, nhưng sửa một vế thì số đổi hướng khó hiểu.

### Thiết kế
Helper dùng chung đặt ở **`src/gsm_core/rates.py`** (KHÔNG phải `features/_common.py` — module private,
đường sản phẩm không nên import; và `rates.py` đã là đúng tiền lệ: docstring của nó là bản án về chính
lớp lỗi "ba quy ước cho một sự thật", `advisor.py:18` đã import từ đó):

- `bucket_of_hour(policy, hour) -> 'peak'|'offpeak'|None` — `None` = ngoài khung điểm ⇒ **loại khỏi CẢ
  tử số lẫn mẫu số** (phút online 23h không được làm loãng offpeak, vì solver không bao giờ áp rate
  bucket cho giờ `ppt=0`)
- `split_minutes_by_bucket(policy, intervals)` — chồng lấn hình học, dùng lại được cho sim
- `bucket_online_hours_measured(policy, intervals)` — đường **CÓ** mốc thời gian (L1 `app_event`)
- `bucket_online_hours_estimated(policy, online_hours_total, activity_span)` — đường **KHÔNG** có mốc
  (L1R + sản phẩm chỉ có `online_time` **vô hướng**; spec `data-contract-counterfactual.md:83` xác nhận
  bảng thật **không có** `go_online/go_offline`). Phân bổ theo **hình dạng span ∩ bucket**:
  `oh_bucket = overlap(span, giờ-bucket ∩ khung-điểm) / span × online_hours_total`.
  **Bất biến có test:** `Σ oh_bucket ≤ online_hours_total` — không bao giờ bịa thêm giờ online
- `bucket_rate_samples(...)` — một ngày → mẫu; bucket có `oh ≥ MIN_BUCKET_HOURS (0,5h)` mà 0 điểm ⇒ đóng
  **0.0**; không có bằng chứng hiện diện ⇒ **không có khoá** (khác hẳn 0.0)
- `median_bucket_rates(...)` — nhiều ngày → median, `min_days=3` như quy ước cũ
- `features/_common.py`: **THÊM** `online_intervals_on_date` (giữ nguyên `online_minutes_on_date`)

**Chọn phương án span-scaled, không phải theo số cuốc** — đã **đo** trên 1.800 driver-day với tham chiếu
có timestamp: MAE tỷ trọng peak **0,141** (span-scaled) vs **0,513** (trip-count) ⇒ tốt hơn **3,5×**;
median bias 1,009 vs 1,219. Phương án đọc `public_driver_hex_tracking` bị loại: 40% roster không có byte
vị trí, và Σ dwell **vượt** `online_time` ở 9,3% driver-day ⇒ dựng nguồn sự thật thứ hai về "online".

### Nhãn xấp xỉ — bump schema
`bonus_gap_input` **1.0.0 → 1.1.0**, additive-optional (đúng 6 bước `schemas/README.md`):
`historical_rate_method` (enum `measured_intervals | estimated_span_scaled | day_average_mixed | none`)
+ `historical_rate_days`. **Không** overload trường `source` (sẽ xoá nhãn MOCK mà CLAUDE §5 bắt buộc),
**không** nhét metadata vào `historical_points_per_hour` (bẫy cho consumer iterate). Kèm snapshot
`@1.0.0`, upcaster stamp-only, `LATEST_VERSIONS`, `CHANGELOG.md`. **Sim giữ 1.0.0** ⇒
`tests/test_advice_bridge.py:237` không phải sửa.

### Files sẽ sửa
- `src/gsm_core/rates.py` (THÊM 6 hàm + 3 hằng; giữ `shrunk_rate`)
- `src/gsm_core/features/_common.py` (THÊM 1 hàm)
- `src/gsm_core/features/bonus_gap.py:51-73` · `src/gsm_core/features/from_l1r.py:143-174`
- **`ui/backend/app/adapters/advisor.py:58-79`** (`_hist_rate` → thuần, bỏ `if p > 0`), `:134-154`,
  và `:261-277` (**hedge sát biên**, xem dưới)
- `schemas/l3/bonus_gap_input.schema.json` + snapshot `@1.0.0` + `src/gsm_core/upcasters.py` +
  `tests/test_schemas.py:64` + `schemas/CHANGELOG.md`
- Test mới: `tests/_bucket_rate_fixture.py` · `tests/test_dadv04_bucket_rate.py` ·
  `ui/backend/tests/test_dadv04_hist_rate.py`
- **KHÔNG đụng:** `solvers/bonus_feasibility.py` · `src/gsm_sim/*` · `tests/test_bonus_feasibility.py` ·
  `tests/test_multiday.py` (đường sim tách sang **B0b**)

### Hedge rủi ro lạc quan — làm NGAY trong cycle này
Đo được: trong 219 ca mới-feasible, **84 (38%)** bị `rate −20%` lật lại infeasible (nhóm vốn feasible chỉ
**1%**) ⇒ fix này **tập trung rủi ro vào đúng dải mới mở**. Ship mà không hedge = biến bi-quan-hệ-thống
thành **hứa hẹn ở dải 50-50**. Adapter **đang vứt** `report["sensitivity"]` mà solver đã tính sẵn
(`bonus_feasibility.py:193-201`) ⇒ khi `flips_feasible` bật, thêm **một câu caveat** *"mốc này sát biên…"*.
**Không** số mới (verifier V1 không có gì để bắn), **không** đổi solver.

### Thứ tự thi công (red → green, mỗi bước dừng được)
1. Fixture + 7 test ⇒ chạy, **xác nhận đỏ đúng chỗ** (không phải đỏ vì import)
2. `rates.py` + `_common.py` + test bất biến `Σ ≤ online_time`
3. `bonus_gap.py` (measured) ⇒ xanh test 1,2,3,4,7
4. `from_l1r.py` (estimated) ⇒ chạy `test_future_leak_l1r` + `test_future_leak_gate` + `test_features_from_l1r`
5. Schema bump + snapshot + upcaster + CHANGELOG ⇒ `test_schema_versioning` + `test_schemas` + `test_mockgen`
6. `advisor.py` (rate thuần + bỏ `if p > 0`) ⇒ `uv run pytest -q ui/backend/tests`
7. Hedge sát biên + test hedge
8. Script đo trước/sau → điền bảng
9. Fingerprint sim 5 seed (kỳ vọng IDENTICAL) + **CẢ HAI** suite
10. UPDATE-167 + PENDING-REVIEW + visual gate

## Verification

**Test đỏ-trước (phải ĐỎ trước khi sửa):**

| test | assertion |
| --- | --- |
| `test_l1_rate_la_diem_tren_gio_TRONG_bucket` | `hist == {"peak": 30.0, "offpeak": 7.5}` (hiện `{6.0, 6.0}`) |
| `test_l1_end_to_end_moc_thuong_voi_toi_duoc` | qua `derive_bonus_gap_input → solve`: `feasible is True`, `hours_needed ≈ 2.42` (hiện `False`) |
| `test_ngay_online_ma_trang_diem_dong_0_vao_mau` | `hist["offpeak"] == 0.0` (hiện khoá biến mất ⇒ fallback DƯƠNG) |
| `test_khong_bang_chung_thi_khong_co_khoa` | span không phủ peak ⇒ `"peak" not in hist` |
| `test_l1r_rate_cung_QUY_UOC_voi_l1` | `hist["peak"] ∈ [24, 45]` (dải, neo vào MAE 0,141 đã đo) |
| `test_bat_bien_tong_gio_bucket_khong_vuot_online_do_duoc` | `Σ ≤ online_time + 1e-9` trên 4 span |
| ⭐ `test_quy_uoc_MOT_chieu_producer_va_solver` | cửa sổ thuần một bucket ⇒ `hours_needed ≈ gap / hist["offpeak"]` — **ai đổi mẫu số MỘT bên thì đỏ** |
| `ui/.../test_card_feasible_co_hedge_khi_sat_bien` | `flips_feasible` ⇒ caveat có cảnh báo, **`numbers` không thêm số nào** |

**Acceptance số** (script `measure-s1-feasible-before-after.py`, 90 tài xế × 5 ngày × 4 giờ hỏi = 1.800 ca,
phân tầng bằng **strata ĐO ĐƯỢC** — tercile `online_time`, tercile tỷ trọng cuốc peak):
- `flip inf→fea` do **riêng** mẫu số phải **ĐƠN ĐIỆU** (0 ca đi ngược — hệ quả toán học). **Có ca ngược ⇒ code sai**
- `flip fea→inf` **chỉ** đến từ vế `0.0`, ≈ **10%** của chiều ngược (đo: 25 vs 238). Lệch xa ⇒ điều tra trước khi tin
- `hist` rỗng **không** tăng > 5% ở bất kỳ stratum (fix không được làm mất prior cá nhân: đo 195→187 / 200→200)
- 3 cột `MIN_BUCKET_HOURS ∈ {0,25 · 0,5 · 1,0}` — chứng minh kết luận **không** là hiện vật của hằng số
- `% ca fragile` (rate −20% lật) ở **cả** nhóm mới-feasible và cũ-feasible
- Fingerprint sim **IDENTICAL** 5 seed · **cả hai** suite xanh như baseline (2F của Khánh)

**Falsifier:** (1) ca `fea→inf` không giải thích được bằng một mẫu `0.0` cụ thể ⇒ mẫu số sai chiều đâu đó;
(2) `Σ oh_bucket > online_time` ở bất kỳ driver-day ⇒ đang bịa giờ, DỪNG; (3) verdict đảo > 5% khi đổi
`MIN_BUCKET_HOURS` ⇒ kết luận là hiện vật của hằng số; (4) tỷ số peak sau/trước **không** ≈ `oh_ngày/oh_peak`
của chính tài xế đó (kiểm tay 3 ca) ⇒ helper không làm đúng thứ nó khai.

**Visual gate:** đường sản phẩm là card F0/F1 ⇒ **BẮT BUỘC** — status `BLOCKED` cho tới khi Cường xem card
trước/sau ở một `(driver, date, now_min)` đã ghi, hoặc waive tường minh. **Không** gộp im lặng vào V-31.

## Cấm claim (ghi trước để không tự lừa)
- **Không** nói *"producer nay chính xác"* — chỉ được nói *"hết lệch ĐƠN VỊ; sai số xấp xỉ có nhãn và có số"*
  (đường estimated MAE 0,141; kịch bản audit peak lệch +40%)
- **Không** nói *"advisor tốt hơn"* chỉ vì bớt im lặng — chưa có phép đo kết cục cho tài xế
- `MIN_BUCKET_HOURS = 0,5` là **ASSUMPTION có lập luận**, chưa hiệu chỉnh bằng dữ liệu thật

## Sau B0 (mỗi cái CẦN PLAN RIÊNG)
`B0b` sim memory theo bucket (đổi hành vi ⇒ regate) → `Cycle B` shift_extend (phụ thuộc B0b) →
`F1` basin-map niềm tin (0 seed, **falsifier cho chính claim bẫy** — phải chạy TRƯỚC khi trích §2 ra
ngoài) → `F2` đo cooldown có thật mất đơn (rút ceiling đang vô căn cứ) → `F3` sửa **B3** no-op + **B5**
slider → `F4` **B2** cooldown lọc trước gán + log. **Quyết định của Cường:** amendment ĐA-08 cho kênh
phía-cung · Q-07 (ghép đơn đúng vs trung thành archetype, đang chặn B1) · `REVIEW-092-4` cầu co giãn.
