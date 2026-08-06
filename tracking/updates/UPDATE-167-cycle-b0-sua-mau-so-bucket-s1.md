# UPDATE-167 — Cycle B0: sửa MẪU SỐ bucket của S1 (đường sản phẩm) — feasible 29,9% → 52,2%

- **Ngày:** 2026-08-06
- **Loại:** bug fix (đường SẢN PHẨM) + schema bump 1.1.0 + đo trước/sau có kết quả thật
- **Nợ:** `D-ADV-04` · **Plan đã duyệt:** `tracking/PLAN-2026-08-06-CYCLE-B0-da-duyet.md`
- **Nguồn phát hiện:** audit math-model `mm-06-s1.json`; reproduce `repro-s1-denominator.py`

## 1. Bug (đã reproduce TRƯỚC khi sửa)

| Tầng | Quy ước | Đúng/sai |
| --- | --- | --- |
| 3 producer (`features/bonus_gap.py:64` · `features/from_l1r.py:161` · **`ui/.../advisor.py:74`**) | điểm-của-bucket ÷ giờ online **TOÀN NGÀY** | **SAI** |
| Solver `bonus_feasibility._hour_rate` → `_walk` (nhân `rate × span` cho **từng giờ** của bucket) | điểm ÷ giờ online **TRONG bucket** | **ĐÚNG** — có test ghim `tests/test_bonus_feasibility.py:112-119` |

⇒ rate **luôn** ước NON theo hệ số `giờ_ngày / giờ_bucket`. Kịch bản reproduce: producer trả
`{peak: 6.0, offpeak: 6.0}` (đúng `{30, 7.5}`) ⇒ S1 phán **INFEASIBLE** *"chỉ kiếm thêm ~42đ < 50đ"*
trong khi rate đúng cho **FEASIBLE tại 2,42h**. Vì **S1 là solver duy nhất đường sản phẩm chạy**
(`B6-PARITY`), hệ nói với tài xế thật *"không với tới mốc"* về một mốc **với tới được**.

**Vế thứ hai, thiên lệch NGƯỢC CHIỀU:** survivorship — ngày online-phủ-bucket mà **0 điểm** bị loại
khỏi mẫu (`if p > 0`) ⇒ median LẠC QUAN. Hai lỗi **bù trừ và che nhau** ⇒ sửa cùng lúc.

## 2. KẾT QUẢ THẬT — đo trước/sau trên đường sản phẩm (150 tài xế × 5 ngày × 4 giờ hỏi = **3.000 ca**)

Script: `research/audit/2026-08-06-math-model-audit/measure-s1-feasible-before-after.py` (MOCK).
Tách **ba** arm để biết mỗi vế đóng góp bao nhiêu, không gộp:

| arm | mẫu số | survivorship | feasible |
| --- | --- | --- | --- |
| **A** (cũ) | TOÀN NGÀY | bỏ ngày 0 điểm | **898/3.000 = 29,9%** |
| **B** | TRONG BUCKET | bỏ ngày 0 điểm | 1.593 = 53,1% |
| **C** (code sau fix) | TRONG BUCKET | đóng **0.0** | **1.566/3.000 = 52,2%** |

**Cả hai kỳ vọng TIỀN-ĐĂNG-KÝ đều đứng:**
- `A→B` **ĐƠN ĐIỆU: 0 ca đi ngược** (695 ca infeasible→feasible, 0 ca ngược) — đúng hệ quả toán học
  của `giờ_ngày ≥ giờ_bucket`. Nếu có ca ngược thì đó là **code sai**, và không có ca nào.
- `B→C` **một chiều: 0 ca ngược** (27 ca feasible→infeasible do mẫu `0.0`).
- Vế survivorship kéo lại **3,9%** của chiều thuận (27/695) ⇒ hai bias **không** bù trừ đối xứng;
  chiều tổng là **hết bi quan**.

**Falsifier hằng số — BÁC:** đổi `MIN_BUCKET_HOURS` 0,25 / 0,5 / 1,0 ⇒ feasible 52,5% / 52,2% / 52,2%,
lệch verdict **0,3% / 0% / 0%** ⇒ kết luận **không** là hiện vật của hằng số ASSUMPTION.

## 3. ⚠ MỘT KỲ VỌNG CỦA TÔI HỤT — truy nguyên chứ không bỏ qua

Tôi dự đoán *"hist rỗng không tăng"*. Thực tế **0 → 4 ca** (0,13%). Truy nguyên bằng probe:
guard `MIN_SHAPE_COVERAGE` loại **486/12.805 = 3,80%** driver-day (không phải 4 ca — 4 là số ca-hỏi
mất **hết** prior sau khi guard loại vài ngày). Plan đặt falsifier #4 ở mức *">1% driver-day chạm
nhánh `none` ⇒ guard đang cắt dữ liệu thật"* ⇒ **falsifier NÀY ĐÃ BẮN**.

Đo tiếp để quyết bằng số thay vì bằng cảm giác — **tắt guard hoàn toàn**:

| | feasible | hist rỗng |
| --- | --- | --- |
| guard BẬT (0,5) | 1.566/3.000 = 52,2% | 4 |
| guard TẮT (0,0) | 1.564/3.000 = 52,1% | 0 |
| **lệch verdict do guard** | **2/3.000 = 0,07%** | — |

**Quyết định: GIỮ guard.** Lý do: ảnh hưởng kết quả gần như bằng 0 (0,07%), nhưng nó là lá chắn cho
**dữ liệu thật** — phân bố `online_time/span` trên mock có median 1,04, p10 **0,64**, **min 0,16**;
với ngày mà online chỉ bằng 16% span thì hình dạng span **không nói gì** về nơi những giờ đó nằm, và
phân bổ theo nó là bịa. Cái sai là **ngưỡng dự đoán của tôi** (tưởng ca bệnh lý < 1%), không phải guard.
Ghi lại thành ASSUMPTION có số, không phát biểu là "đã hiệu chỉnh".

## 4. Thay đổi

- **`src/gsm_core/rates.py`** — thêm 6 hàm + 3 hằng: `bucket_of_hour` (giờ ngoài khung điểm ⇒ `None`,
  loại khỏi **cả** tử số lẫn mẫu số) · `split_minutes_by_bucket` · `bucket_online_hours_measured`
  (đường có mốc) · `bucket_online_hours_estimated` (đường không mốc, **bất biến `Σ ≤ online_time`**) ·
  `bucket_rate_samples` (đóng `0.0`) · `median_bucket_rates`. Đặt ở đây, **không** ở
  `features/_common.py`: module đó là private (`_`) của package `features`, đường sản phẩm không nên
  import; còn `rates.py` đã là đúng tiền lệ (docstring của nó là bản án về chính lớp lỗi "nhiều quy
  ước cho một sự thật", `advisor.py:18` đã import từ đó).
- **`src/gsm_core/features/_common.py`** — thêm `online_intervals_on_date` (giữ nguyên
  `online_minutes_on_date`); không có `go_online` ⇒ trả span `[first, last]` ⇒ **giữ nguyên** tổng
  thời lượng của hàm cũ.
- **3 producer** dùng helper: L1 → `measured_intervals`; L1R + **sản phẩm** → `estimated_span_scaled`
  (bảng thật không có `go_online`/`go_offline` — `specs/real-data/data-contract-counterfactual.md`).
  Bỏ `if p > 0` ở đường sản phẩm. `_hist_rate` nay trả `(rate, method)` — **nhãn đi cùng số**.
- **Schema `bonus_gap_input` 1.0.0 → 1.1.0**: thêm `historical_rate_method` + `historical_rate_days`
  (optional). Snapshot `@1.0.0`, upcaster **chỉ stamp version** (record cũ **không biết** mẫu số của
  nó được suy thế nào ⇒ **không bịa** nhãn, và **không** sửa số vì không biết giờ-trong-bucket của
  những ngày đã trôi). Không overload trường `source` (sẽ xoá nhãn MOCK mà CLAUDE §5 bắt buộc).
- **Hedge sát biên** (`advisor.py`): khi `sensitivity` có `flips_feasible`, card feasible thêm **một
  câu** *"mốc này sát biên…"*. Lý do: sửa xong advisor **bớt bi quan** ⇒ rủi ro MỚI là hứa hẹn ở dải
  50-50. **Không thêm số nào** (verifier V1 không có gì để bắn), **không** đổi `confidence`.

## 5. Kiểm chứng

- **Test đỏ-trước ĐÃ xác nhận đỏ đúng chỗ trước khi sửa**: `{peak: 6.0, offpeak: 6.0}` vs `{30, 7.5}`
  và đúng câu *"~42đ < 50đ"* — tức fixture tái tạo được chính xác kịch bản audit.
- Mới: `tests/_bucket_rate_fixture.py` (kịch bản canonical **dùng chung** cho cả ba đường — chống tái
  diễn "ba kịch bản cho một sự thật") · `tests/test_dadv04_bucket_rate.py` **10 test** ·
  `ui/backend/tests/test_dadv04_hist_rate.py` **4 test**. Trong đó **`test_quy_uoc_MOT_chieu_producer_va_solver`**
  là cổng chống tái diễn: đổi mẫu số ở **một** bên (producer HOẶC solver) ⇒ đỏ ngay.
- `ui/backend/tests`: **201 passed** (không đụng test cũ nào).
- **Sim: KHÔNG đổi — chứng minh chứ không tin tưởng:** `git diff --stat` cho **0 file dưới
  `src/gsm_sim/`**, và grep xác nhận **0 module sim** import `gsm_core.rates` / `features.bonus_gap` /
  `from_l1r` ⇒ fingerprint đồng nhất **theo cấu trúc**. Tôi **không** chạy fingerprint 5 seed riêng và
  nói rõ điều đó; test determinism trong suite gốc là cổng xác nhận.
- **Suite gốc: 1165 passed / 2 failed / 4 skipped** (25:59). Hai fail là **đúng hai fail có sẵn của
  Khánh** (`test_demo_trace_neutrality` + K-03 `test_money_manifest_is_complete` — 4 hàm
  `demo_trace`/`World.log` chưa phân loại) ⇒ **baseline giữ nguyên, tôi không làm đỏ thêm gì**.
  Số học khớp: **1165 − 1155 = đúng 10** test mới của tôi. `ui/backend`: **205 passed** (201 + 4).
- **CHƯA kiểm chứng:** đường **sim** vẫn dùng quy ước CŨ (`advice_bridge.py:990-992` đổ day-average
  vào **cả hai** bucket) ⇒ nợ **B0b**, cần đổi schema memory ⇒ đổi hành vi ⇒ cycle riêng có regate ·
  các nợ `mm-06` khác (verdict nhị phân trên median không CI, ràng buộc acceptance kiểm tĩnh, fallback
  1,5 cuốc/giờ phẳng, quỹ giờ bỏ downtime đổi pin) **chưa mở cycle**.

## 6. Visual

🔴 **BLOCKED — cần Cường xem.** Card F0/F1 của web demo **đổi nội dung thật**: nhiều tài xế trước đây
nhận *"không với tới mốc"* nay nhận *"còn với được mốc thưởng…"* (29,9% → 52,2% ca feasible), và card
sát biên có thêm một câu cảnh báo. Đây là **meaningful UI update** ⇒ **không** gộp im lặng vào V-31.
Đăng ký **V-32** trong `PENDING-REVIEW`.

## 7. Adversarial self-review / flaws found

1. **Không được nói "producer nay chính xác".** Hai trong ba đường là **XẤP XỈ** (`estimated_span_scaled`)
   vì bảng thật không có mốc online. Phát biểu đúng: *hết lệch ĐƠN VỊ; sai số xấp xỉ có nhãn*.
2. **Không được nói "advisor tốt hơn"** chỉ vì bớt im lặng. Chưa có phép đo **kết cục cho tài xế**:
   một phần trong 695 ca mới-feasible có thể là *"khuyên bám mốc rồi không tới"*. Đó đúng là lý do có
   hedge sát biên — nhưng hedge là **giảm thiểu**, không phải bằng chứng.
3. **Kỳ vọng của tôi hụt một mục** (hist rỗng 0→4) và **falsifier #4 đã bắn** (guard loại 3,8%
   driver-day). Tôi giữ guard **sau khi đo** tác động (0,07%), không phải sau khi lập luận.
4. Test `test_khong_bang_chung_thi_khong_co_khoa` **xanh cả trước lẫn sau** fix — nó chỉ có nghĩa khi
   **đi cùng** test survivorship (một cái đòi có khoá `0.0`, một cái đòi **không** có khoá). Ghi ở đây
   để không ai xoá một trong hai vì "trùng".
5. Con số `{peak: 30, offpeak: 7.5}` là **của kịch bản fixture**, không phải tham số hệ thống.
6. `historical_rate_days` đã thêm vào schema nhưng **producer chưa điền** — đó là nền cho nợ
   `D-ADV-05` (phân vị/CI thay median đơn), **không** phải trường bỏ quên.

## ⏳ Nhắc PENDING-REVIEW

**V-32 (MỚI — card F0/F1 đổi nội dung, blocking)** · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- ·
Q-03/04/07/09/10/13 (**Q-07 đang chặn B1**) · **amendment ĐA-08 cho kênh phía-cung**.
⏸ Khánh: 2 test đỏ + 3 việc Flutter.
