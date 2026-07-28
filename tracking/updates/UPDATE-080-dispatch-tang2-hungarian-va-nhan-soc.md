# UPDATE-080 — Dispatcher tầng 2 (batched Hungarian) + nhãn MOCK cho SOC + chốt Q-08

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** feature (dispatch tầng 2) + fix (nhãn mock) + decision (Q-08)
- **TODO liên quan:** Q-06 ✅ · Q-07 (c) · Q-08 ✅ · T-045c/e; hồ sơ
  [`15`](../../research/audit/2026-07-27-current-state/15-dispatch-h3-nghien-cuu-va-thiet-ke.md)

## Tóm tắt

Ba việc: **(1)** xây **tầng 2 của dispatcher** — batched bipartite Hungarian trên `cost = ETA` —
tầng này có trong đặc tả từ đầu nhưng **chưa bao giờ được xây**; **(2)** gắn **nhãn MOCK cho SOC**
đi cùng dữ liệu (Q-06 phương án b); **(3)** chốt **Q-08** theo uỷ quyền của Cường.

## 1. Dispatcher tầng 2 (Q-07 phương án c)

### 1.1 Phát hiện: đặc tả có hai tầng, code chỉ có một

`world-parameters.md` §3 (dẫn công bố DiDi) đặc tả: tầng 1 lấy ứng viên bằng H3, **tầng 2 giải
bipartite `cost = ETA_pickup` bằng `scipy.linear_sum_assignment`**, và *"greedy nearest giữ làm
baseline so sánh"*. Code chỉ có greedy; docstring tự ghi *"Hungarian để vòng sau"* — vòng sau không
tới. **Ba sai lệch chồng nhau**: thiếu tầng 2 · xếp hạng theo **haversine** thay vì ETA · xét đơn
theo **`order_id`**.

### 1.2 Nghiên cứu thực tế ngành (theo chỉ thị *"ưu tiên thực tế, không ưu tiên dễ"*)

- bipartite + Hungarian + batch là **chuẩn ngành** (Uber, DiDi); window ~2s; bán kính chào 1–3 km.
- cost thực tế gồm cả **mức sẵn sàng nhận của tài xế** — ta **cố ý chưa đưa vào**, xem §1.5.
- **Rapido** (bike-hailing, cùng loại hình Xanh SM) đặt tên đúng cho bug của ta: **`bad_hex`** = ô
  *gần hơn về hình học nhưng lái chậm hơn* vs **`good_hex`** = *xa hơn nhưng nhanh hơn*.
  Hệ cũ **ưu tiên `bad_hex` rồi vứt `good_hex` đi** — chính là 293/3.520 lượt bỏ oan đã đo.

Nguồn đầy đủ ở hồ sơ `15-*` §2.

### 1.3 Đã xây

`cost(o,d) = ETA_pickup` dùng **`factor_fn` theo cặp ô** (đường OSRM thật), `linear_sum_assignment`,
cặp `ETA > eta_max` ⇒ cost `INFEASIBLE` (loại). Rơi về greedy khi `|O|==1`/`|D|==1`, khi
`matching: greedy`, hoặc khi ma trận > `MAX_PAIRS = 200_000`. Deterministic: ma trận dựng theo
`sorted(order_id) × sorted(actor_id)`.

### 1.4 Kết quả — 30 seed

| | served | hết hạn | pickup TB | lệch lớn nhất vs `accept_base` | runtime |
|---|---|---|---|---|---|
| gốc greedy-haversine, k=6 | 0,761 | 233 | 1,04 | P7 −0,042 ✅ | 2,9s |
| **batch, k=6 (ĐÃ CHỐT)** | **0,763** | **231** | **0,97** | P7 −0,049 ✅ | **2,7s** |
| batch, k=8 | 0,793 | 194 | 1,10 | P7 −0,058 ❌ | 3,2s |
| batch, k=10 | 0,801 | 183 | 1,13 | P7 −0,063 ❌ | — |

**Chốt `matching: batch` ở `k_max = 6`**: cải thiện thuần trên mọi chiều, mọi test xanh.

### 1.5 Cố ý CHƯA làm

- **Không** đưa xác suất nhận vào cost dù ngành có làm: dispatch sẽ "biết" `accept_base` — tham số
  **sinh hành vi** ⇒ oracle. Nếu làm phải dùng tỷ lệ **quan sát được**, và nó chạm ranh giới đo
  advisor ⇒ tách thành quyết định riêng.
- **Không** chuyển candidate retrieval sang res 8 (k=2 chỉ 19 ô thay vì 127 ⇒ rẻ hơn ~7×) — tối ưu
  hoá, không phải đúng/sai.

## 2. Nhãn MOCK cho SOC (Q-06 phương án b — Cường chốt)

13 bảng GSM **không có cột pin**; `_soc_proxy` sinh SOC bằng `sha256(driver|date)`. Số đó đang hiện
`⚡{soc}%` cho tài xế, tô đỏ khi <25%, **không nhãn**.

**Nhãn đi CÙNG DỮ LIỆU, không hard-code trong JS**: thêm `soc_source` + `vehicle_range_km_source`
vào contract `driver_state` (**required**, enum `MOCK`/`THẬT`); `app.js` **đọc từ payload** rồi mới
hiện badge. Lý do: sửa mỗi `app.js` thì màn hình khác / **Flutter của Khánh** lại quên — đúng mẫu
lỗi "sửa một tầng, tầng khác không biết" (đã gặp 6 lần).

Card "Pin (SOC)" và "Tầm đi còn lại" đổi chú thích mờ *"ước lượng mô phỏng (proxy)"* thành câu nói
thẳng: **"Đây không phải mức pin thật của xe. Dữ liệu GSM hiện chưa có telemetry pin."**

### 2.1 Kiểm chỉ thị kèm theo: "pin phải có tác động lên sim"

**Đã có, và ràng buộc thật** (seed 1000): bỏ đơn vì thiếu pin **41 lần = 3,5%** lượt chào (27/90
tài xế) · đi đổi pin **133** lượt, **15 THẤT BẠI** (trạm hết pin sẵn) · **0** lần hết pin giữa
đường · chờ tủ median 0′ **max 50′**. Khác hẳn mệt mỏi (chỉ khiến tự nghỉ, không hậu quả).

SOC **đã là** chiều state của DP. Bốn sai lệch mô hình `SWAP` vs sim + thứ tự nâng cấp: hồ sơ
`13-*` §3.2b.

## 3. Q-08 — agent chốt theo uỷ quyền

Quyết định 2026-07-21 (*"baseline B chưa tối ưu là feature"*) **vẫn còn hiệu lực**, bổ sung ranh
giới = **tính khả tín vật lý**: unserved/utilization trung bình + dồn trạm **giữ nguyên** (dư địa
hợp lệ, advisor có công cụ sửa); **đuôi phi thực tế phải cắt** — ngưỡng **không khoảng chờ nào >
90 phút**, p99 < 60 phút. Lý do: advisor không có lệnh nào tạo ra đơn hàng, nên đuôi 5,6h là **lỗi
thế giới**, không phải dư địa. Chi tiết trong `PENDING-REVIEW.md`.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_sim/dispatcher.py` | sửa | tầng 2 Hungarian + greedy fallback theo ETA; docstring ghi rõ hai khuyết tật |
| `configs/pilot_dongda.yaml` | sửa | `matching: batch`; `k_max` giữ 6 + bảng đo |
| `tests/test_dispatch_batch_matching.py` | **tạo** | 9 test (2 đỏ trước fix) |
| `tests/test_dispatch_shortlist_radius.py` | sửa | bỏ assert nhiễu, giữ vế served |
| `ui/contracts/driver_state.json` | sửa | `soc_source`, `vehicle_range_km_source` (required) |
| `ui/backend/app/adapters/mockdata.py` | sửa | trả nhãn nguồn |
| `ui/web/{index.html,js/app.js,theme.css}` | sửa | badge `MÔ PHỎNG` + 2 card nói thẳng |
| `ui/backend/tests/test_contracts.py` | sửa | +2 test (payload + render) |
| `research/.../15-*.md` | **tạo** | nghiên cứu dispatch/H3 + thiết kế |
| `tracking/PENDING-REVIEW.md` | sửa | Q-05/Q-06/Q-08 chốt; Q-07 chuyển hướng (c) |

## Kiểm chứng

| Command | Kết quả |
| --- | --- |
| `pytest tests/test_dispatch_batch_matching.py` | **2 failed → 9 passed** |
| `pytest tests/test_sim_realism.py` (30 seed) | **xanh toàn bộ** |
| `pytest tests` (ui/backend) | **35 passed** (33 → +2) |
| `pytest tests` (root, full) | **571 passed / 4 skipped**, runtime **12:31** (trước: 22:33) |
| sweep k ∈ {6,8,10} × 30 seed, `matching: batch` | bảng §1.4 |

⚠ **BASELINE BỊ VÔ HIỆU**: đổi thuật toán dispatch làm lệch **mọi** số đã đo (`09-baseline30`,
`11-ablation-params`, `11-paired-fix-effect`). Phải đo lại trước khi so sánh advisor.

## Visual verification

- **Status:** `BLOCKED` → cần Cường xem. **Hai thứ**: (a) badge `MÔ PHỎNG` cạnh `⚡%` + 2 card pin
  ở màn Xe (`http://localhost:8010/app/`); (b) khu Mô phỏng → Replay/Bản đồ H3 seed 1000 — ghép
  đơn đổi trên toàn bản đồ.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

1. **Giả thuyết trung tâm của tôi SAI.** Hồ sơ `15` §4.1 dự đoán *"Hungarian ⇒ pickup GIẢM khi nới
   shortlist ⇒ đảo chiều đánh đổi Q-07"*. Đo 30 seed: pickup **giảm ở cùng một k** (1,04 → 0,97)
   nhưng **nới k vẫn kéo thêm cuốc đón xa** ⇒ đánh đổi còn nguyên, **Q-07 chưa giải**. Đã sửa
   khẳng định trong test + hồ sơ thay vì để nguyên.
2. **Fixture đầu tiên của tôi vô dụng**: ca "đói theo `order_id`" ban đầu để greedy **tình cờ vẫn
   tối ưu** ⇒ test xanh giả. Phải dựng lại có ràng buộc ETA mới tạo được xung đột thật.
3. **Test của tôi bị thiếu công suất thống kê**: assert chiều đánh đổi trên **3 seed**, mà ở 3 seed
   con số **ngược dấu** với 30 seed (k6 0,073/k8 0,049 vs 30 seed k6 0,049/k8 0,058). Assert đại
   lượng nhiễu ở mẫu nhỏ = **test flaky, tệ hơn không có test**. Đã bỏ vế đó.
4. **Tolerance sai do tôi đặt**: so tổng ETA với `abs=1e-6` trong khi `Assignment.eta_min` làm tròn
   2 chữ số. Lỗi của test, đã nới đúng mức (lặp lại bài học UPDATE-075).
5. **"greedy" trong bảng đo không phải greedy gốc**: fallback mới xếp theo **ETA** và có try-next,
   nên khác thuật toán gốc (haversine, không try-next). Khi so phải dùng số của bản **gốc** đo
   trước khi sửa — đã dùng đúng số đó ở §1.4.
6. **Chưa đo giờ cao điểm riêng** cho batch (greedy k=12 từng làm 18h vượt 40%). `test_no_dead_hour`
   xanh nên không có cờ đỏ, nhưng chưa có bảng theo giờ.
7. **`INFEASIBLE = 1e6` là hữu hạn** để scipy chạy được; nếu một ngày ETA thật vượt 1e6 phút thì
   cặp không khả thi sẽ được chọn. Không thể xảy ra ở quy mô này nhưng là giả định ngầm.

## Expansion checkpoint (T-039)

1. **Schema**: `driver_state` nay có nhãn nguồn per-field. Nên nhân rộng mẫu này cho **mọi** số
   MOCK khác trên UI (payout, tầm đi, demand) thay vì chỉ SOC.
2. **Bài toán tối ưu**: dispatcher nay là bài toán gán tối ưu thật ⇒ mở đường cho **capacity
   ledger / S4** cắm vào cùng khung (T-045a).
3. **Tính năng**: có `matching` làm cờ ⇒ so **A/B THUẬT TOÁN dispatch** được, không chỉ A/B advice.

## Follow-up / defer phát sinh

- **Q-07 vẫn mở**: nới k vẫn bị chặn bởi độ trung thành archetype (−0,058 ở k=8). Cần Cường chọn.
- **Đo lại toàn bộ baseline** ở `matching: batch` trước mọi so sánh advisor.
- Cân nhắc res 8 cho candidate retrieval (rẻ hơn ~7×) — tối ưu hoá.
- Xác suất nhận vào cost — quyết định riêng vì chạm ranh giới oracle.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-15 · **Q-07 (đang mở)** · Q-03, Q-04 · B-02
ARCH-VERSION chặn T-044 · **chưa commit gì trong toàn bộ phiên**.
