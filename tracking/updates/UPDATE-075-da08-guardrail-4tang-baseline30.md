# UPDATE-075 — ĐA-08 bước 1: guardrail 4 tầng + baseline 30 seed `coverage: all` (đo trước, sửa sau)

- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** feature (metric/đo lường) + research + fix
- **TODO / User story liên quan:** **T-041 bước 1**; ĐA-08 (duyệt 2026-07-27); spec
  `advisor-objective-model-v2.md` §5–§6

## Tóm tắt

Cường duyệt spec objective v2 + ĐA-04..ĐA-09 (*"oke duyệt hết"*). Bước 1 của spec §6 là **"đo
trước, sửa sau"**: viết đủ bộ metric 4 tầng, nối vào guardrail A/B, bỏ ép `coverage="single"`, rồi
chạy **baseline 30 seed ở `coverage: all`** — **không sửa solver nào**, để mọi thay đổi sau này có
số nền đúng để so.

Kết quả nền: advisor làm tài xế **nghèo đi −17.310đ/ngày, CI95 [−29.294, −5.820]** — **lần đầu tác
hại được chứng minh có ý nghĩa thống kê**. Tầng hệ thống xấu theo hướng nhất quán nhưng **CI chứa
0** ⇒ phải **đính chính** cách đọc của hồ sơ 07.

## Chi tiết cập nhật

### 1. Bộ metric mới (`src/gsm_sim/sim_metrics.py`)

| Hàm | Đo gì | Vì sao cần |
|---|---|---|
| `gini(values)` | bất bình đẳng payout, bất biến theo thang | so được giữa hai thế giới khác tổng payout |
| `hhi(shares)` | Herfindahl **chuẩn hoá [0,1]** | 0 = trải đều, 1 = dồn một chỗ; so được khi số nhóm khác nhau |
| `fairness_metrics` | Gini + p10/median/p90 + **`total_payout_vnd`** | không có TỔNG thì không phân biệt được *tạo thêm giá trị* với *tái phân phối* |
| `concentration_metrics` | HHI tải trạm, HHI cung theo ô, đỉnh swap/rest theo giờ | guardrail chống herding |
| `customer_impact` | expired/censored/cancelled **tách riêng** + chờ khách | `customer_wait()` cũ cố ý bỏ đơn không ai nhận — chính là phần hại lớn nhất |
| `system_guardrail` | gói đủ **4 tầng** + `starved_hours_n` | dùng trực tiếp cho chỉ tiêu kép ĐA-08 |

`starved_hours_n` **nối `supply_demand_density()` vào guardrail** — hàm này có từ SIM-5, đã test,
nhưng **chưa consumer nào ngoài test** (spec §6.1 chỉ đích danh). Rút thành scalar so được A/B,
**không định nghĩa lại** — gọi thẳng hàm gốc.

### 2. Guardrail A/B (`src/gsm_sim/parallel.py`)

- `_system_metrics` mở từ **5 trường → 12 trường** (đủ 4 tầng). 5 trường cũ giữ nguyên định nghĩa.
- `_cfg_with`/`run_pair`/`run_ladder` nhận tham số **`coverage`**; **bỏ ép `"single"`**.
  Lý do: đo tác hại hệ thống ở chế độ single là vô nghĩa — tác động của MỘT tài xế lên thị trường
  gần bằng 0 **theo thiết kế**. Mặc định vẫn `"single"` ⇒ **backward compatible** (dashboard,
  `sim.py`, `run_sensitivity.py` không đổi hành vi).
- `run_ladder(coverage=...)` trả lời gap hồ sơ 07 §6 tự ghi: *"chưa tách đóng góp từng kênh ở chế
  độ diện rộng"*.

### 3. Baseline 30 seed — hồ sơ [`09`](../../research/audit/2026-07-27-current-state/09-baseline-30seed-coverage-all.md)

CRN đã kiểm (`crn_ok = True`: A và B cùng danh sách đơn ở `coverage: all`).

**Cá nhân** (P4, trong thế giới ai cũng nghe): payout **−17.310đ** CI [−29.294, −5.820] ⛔ ·
cuốc **−1,6** CI [−2,4, −0,83] ⛔ · **rỗi +25,9′** CI [+11,4, +41,7] ⛔ · online_min ≈ 0 (ns).

⇒ Cơ chế rõ: advice **không** làm tài xế chạy ít giờ hơn, nó làm họ **dùng cùng số giờ đó tệ hơn**.
Khớp chẩn đoán toán học của spec (DP chọn `ONLINE` 98,5% vì `REST`/`SWAP` cộng `0.0`).

**Hệ thống**: served_rate −0,0047 · expired +4,8/ngày · tổng payout −168.517đ · Gini −0,003 ·
station HHI +0,0007 · supply HHI +0,0001 — **tất cả CI đều chứa 0**.

### 4. Đính chính hồ sơ 07 (10 seed → 30 seed)

07 đọc theo hướng *"khách hàng bị ảnh hưởng thật"*. Ở 30 seed: served_rate giảm **16/30 (53%)** —
gần tung đồng xu; expired **+4,8** với CI chứa 0. **Hướng giữ nguyên, độ mạnh yếu đi.** Đã chèn
cảnh báo vào đầu hồ sơ 07 và sửa dòng kết luận trong README dossier. 07 vốn đã tự ghi ở §6 rằng 10
seed chưa đủ CI — đây là thực hiện đúng điều đã tự cảnh báo.

**Ngược lại, kết luận về tầng cá nhân MẠNH LÊN** và đó mới là chỗ phải sửa trước.

### 5. Fix kèm

- `ui/backend/tests/test_contracts.py::test_ui_fare_equals_sim_policy` dùng **relative path** →
  chỉ xanh khi chạy từ repo root, đỏ khi chạy từ `ui/backend`. Sửa thành đường dẫn tuyệt đối theo
  vị trí file test. Lỗi của test, không phải của code.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/sim_metrics.py` | sửa | +6 hàm ĐA-08; `system_guardrail` gói 4 tầng |
| `src/gsm_sim/parallel.py` | sửa | guardrail 12 trường; `coverage` cho `_cfg_with`/`run_pair`/`run_ladder` |
| `tests/test_fairness_metrics.py` | **tạo** | 8 test (gồm 2 regression cho flaw tự phát hiện) |
| `ui/backend/tests/test_contracts.py` | sửa | fix path phụ thuộc CWD |
| `research/.../09-baseline-30seed-coverage-all.md` | **tạo** | hồ sơ số nền |
| `research/.../09-baseline30-coverage-all.json` | **tạo** | artifact thô 30 seed |
| `research/.../07-fleetwide-advice-equilibrium.md` | sửa | cảnh báo đính chính 10→30 seed |
| `research/.../README.md` | sửa | mục 8/9 + verdict ĐA-04..09 + dòng kết luận mới |
| `tracking/PENDING-REVIEW.md` | sửa | ĐA-04..09 + SPEC-OBJ-V2 → ✅ ĐÃ CHECK; B-01 → gỡ; ghi rõ Q-03/Q-04 **không** nằm trong "duyệt hết" |
| `tracking/TODO.md` | sửa | T-041 (5 bước spec §6); checkpoint |

## Docs đã cập nhật kèm theo

TODO ✅ · PENDING-REVIEW ✅ · research dossier ✅. SCOPE/USER_STORIES/DEFERRED: **không đổi**
(bước này không thêm/bớt tính năng cho tài xế).

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| payout cá nhân giảm khi theo advice | **OBSERVED-SIM** | 30 seed CRN, CI95 loại 0, `09-baseline30.json` | **cao** (trong sim) | nếu sim sai thì hướng sửa objective vẫn đúng về mặt toán (DP thiếu chi phí) |
| tầng hệ thống **chưa** kết luận được | **OBSERVED-SIM** | mọi CI chứa 0 ở n=30 | cao | nếu tăng seed mà xấu đi rõ ⇒ phải nâng ưu tiên ĐA-09 |
| `supply_cell_hhi` = phút hiện diện quy về ô **ĐIỂM ĐẾN** | **PROXY** (có chủ ý) | `world._seg` chỉ có toạ độ; quy ô bằng h3 tại `to_lat/to_lon` | trung bình | với segment di chuyển dài, cung bị quy hết về đích ⇒ HHI hơi cao hơn thực tế |
| kênh đo = `shift_plan` | **OBSERVED-CODE** | `configs/pilot_dongda.yaml` | cao | — |
| số tiền là **MOCK** | **MOCK** | policy bundle mock versioned | — | không được trình bày như số thật GSM |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Scenario | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `pytest tests/test_fairness_metrics.py tests/test_sim_metrics.py tests/test_parallel_worlds.py` | 1000 | pilot_dongda | **30 passed** | — |
| `pytest tests` (root, full) | mọi | — | **541 passed, 4 skipped** (15:14) | — |
| `pytest tests` (ui/backend) | — | — | **28 passed** | — |
| baseline `coverage: all` | **1000–1029 (30)** | pilot_dongda, kênh mặc định | `09-baseline30-coverage-all.json`; `crn_ok=True` | chỉ 1 archetype, 1 kênh, 1 config |
| red-test chứng minh | 1000 | — | `n_supply_cells` KeyError → sửa → xanh | — |

**Full suite:** **541 passed / 4 skipped** trên code CUỐI (baseline trước phiên: 533 + 8 test mới
của UPDATE này). Lần chạy giữa chừng (539 passed) đã bị **loại bỏ, không dùng để claim** vì nó
chạy trên code chưa có fix `supply_cell_hhi` và `starved_hours_n` — chỉ số của lần chạy cuối mới
được ghi.

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** bước này **không đổi dynamics, không đổi default parameter, không đổi UI**. Chỉ thêm
  hàm đo mới (chưa hiển thị ở đâu) và một tham số `coverage` **mặc định giữ nguyên hành vi cũ**.
  Dashboard/khu Mô phỏng chạy y hệt trước.
- **Sẽ cần visual gate ở bước sau:** khi số hạng chi phí đầu tiên (C1/C5) vào solver — lúc đó
  advice hiển thị cho tài xế sẽ đổi, và cảnh báo đỏ cho `shift_plan` phải lên khu Mô phỏng.

## Adversarial self-review / flaws found

1. **FLAW TỰ PHÁT HIỆN (đã sửa, có regression test)** — bản nháp `concentration_metrics` đọc
   `segment["cell"]`, **field đó không tồn tại** (`world._seg` chỉ ghi `from_lat/from_lon/to_lat/
   to_lon`). Hệ quả: `supply_cell_hhi` **luôn = 0.0** mà test cũ `0 ≤ hhi ≤ 1` vẫn XANH — đúng
   loại "hidden fallback trả 0 im lặng". Sửa bằng quy ô H3 thật; thêm
   `test_supply_cell_hhi_is_not_silently_zero` ràng buộc `n_supply_cells ≥ 2` và `hhi > 0`.
   Sau fix: **306 ô, 30.162 phút hiện diện** — không còn số 0 giả.
2. **Đã soi tên event trước khi tin số**: `order_expired` · `order_censored` ·
   `order_cancelled_after_accept` · `go_swap` · `rest` · `swap_done/failed` + `detail["station"]`
   — **tất cả khớp** với `world.py`. (Nếu sai tên thì mọi metric trả 0 và test vẫn xanh.)
3. **CRN drift**: đã kiểm trực tiếp ở `coverage: all` — `crn_ok = True`. Không kiểm thì mọi Δ là rác.
4. **Future leak**: không có — toàn bộ metric tính **sau khi run kết thúc**, không đưa vào solver.
5. **Double-count**: `system_guardrail` gộp 3 dict; `served_rate`/`orders_completed` chỉ lấy từ
   `summarize()`, `expired` chỉ từ `customer_impact` ⇒ không trùng khoá.
6. **Overclaim đã tự chặn**: kết quả hệ thống **KHÔNG** được viết là "chứng minh có hại" —
   CI chứa 0. Và đã **đính chính ngược hồ sơ 07 của chính mình** thay vì im lặng.
7. **Điểm yếu nhất còn lại**: (a) `supply_cell_hhi` dùng PROXY điểm-đến; (b) tầng cá nhân mới đo
   **một** archetype — P4 tân binh là nhóm nhạy cảm nhất với lịch ca, có thể là **cận trên** của
   tác hại; (c) baseline chạy **một** config.
8. **Baseline artifact vs code**: lần chạy đầu (scratchpad) thiếu `starved_hours_n` vì trường này
   thêm sau khi job đã khởi động ⇒ đã **chạy lại** để artifact trong repo sinh được từ đúng code
   hiện tại. Không giữ lại số của lần chạy cũ.

## Expansion checkpoint (T-039)

1. **Schema**: chưa cần đổi. Nhưng để làm `MarketStateView` (ĐA-09) thì cần khai thác
   `public_driver_hex_tracking` (1,37M dòng, **bảng lớn nhất đang dùng ít nhất**) — đề xuất thêm
   view L3 `supply_by_hex_hour`. Chờ Cường duyệt trước khi làm.
2. **Bài toán tối ưu**: baseline chỉ ra **residual formalize được ngay** — "cùng giờ online nhưng
   nhiều rỗi hơn" chính là bài toán **positioning/idle-time**, hiện không solver nào giải. Đây là
   ứng viên cho số hạng C4 (chi phí cơ hội vị trí) và có thể là solver riêng.
3. **Tính năng**: bộ 4 tầng đủ để dựng **bảng điểm hệ thống** trong khu Mô phỏng (dispatcher xem
   advice ảnh hưởng toàn đội thế nào) — hợp với ARCH-B. Ghi làm đề xuất, chưa triển khai.

## Follow-up / defer phát sinh

- **T-041 bước 2** (kế tiếp): số hạng C1 chi phí vận hành/km + C5 chi phí SOC phi tuyến → đo lại
  đúng bộ này. Điều kiện chấp nhận: **cả 5 tầng không xấu đi**.
- **Mở**: baseline mới có 1 archetype / 1 kênh / 1 config. Ghi vào TODO T-041 làm điều kiện trước
  khi tuyên bố bất kỳ kênh nào "có giá trị".
- **Mở**: `run_ladder(coverage="all")` đã sẵn sàng nhưng **chưa chạy** 30 seed cho từng bậc kênh.
- **Nhắc lại**: `accept_lift` giữ TẮT; `shift_plan` giữ BẬT + **cảnh báo đỏ chưa lên UI** (thuộc
  bước có visual gate).

---
**⏳ PENDING-REVIEW (nhắc lại theo yêu cầu Cường):**
- **Visual chờ check:** V-01..V-09 · **V-10** (app tài xế + cards + khu Mô phỏng) · V-11 (semantics
  data mặc định 2026-09-28) · V-12 (hai demo đúng vai trò).
- **Quyết định chờ chốt:** **Q-03** (corpus Khánh thiếu policy 23/02/2026 — file thuộc claim Khánh)
  · **Q-04** (UX proposal dismiss/goal/recap — **không** nằm trong lần "duyệt hết").
- **Đã duyệt, chờ implement:** ĐA-01/02/03 · ĐA-04 (cadence, cycle C3) · ĐA-05 (một projection
  chung, cycle C2) · ĐA-07/ĐA-09.
- **⚠ ĐA-06 (polish envelope/trace): Cường yêu cầu AGENT NHẮC DUYỆT LẠI trước khi implement — đây
  là lời nhắc đó.**
- **Blocker còn mở:** **B-02 / ARCH-VERSION** (registry một-schema, chưa backward compatible) —
  phải giải trước migration ĐA-05/06.
- **Chưa commit gì trong phiên này** (kể cả fix MUT10) — chờ Cường yêu cầu.
