# Dispatch + H3: hệ đang vận hành thế nào, thực tế vận hành thế nào, và thiết kế lại

Ngày: 2026-07-28 · Phục vụ **Q-07 phương án (c)** — Cường: *"phải nghiên cứu kỹ cách H3 và hệ
thống dispatch đang vận hành và giả lập thực tế nhất. **không ưu tiên dễ, nhẹ mà ưu tiên thực tế**"*.

---

## 1. Phát hiện gốc: TẦNG 2 CỦA DISPATCHER CHƯA BAO GIỜ ĐƯỢC XÂY

`research/simulation/world-parameters.md` §3 đặc tả dispatcher **hai tầng**, dẫn công bố của DiDi:

```text
mỗi TICK (batch window 2–5s):
  # Tầng 1 — bán kính H3
  candidates(o) = drivers trong grid_disk(h3(o.pickup), k=2) tại res 8   # ≈2–2.5 km
  # Tầng 2 — matching
  |O|==1 hoặc |D|==1 → greedy nearest (ETA min)
  ngược lại → bipartite cost(o,d)=ETA_pickup, giải scipy linear_sum_assignment
              chỉ nhận cặp ETA ≤ ETA_max
```

> *"Greedy nearest giữ làm **baseline so sánh** với batched-Hungarian."*

**Thực tế trong code**: chỉ có greedy. `dispatcher.py` docstring tự ghi *"Hungarian để vòng sau"* —
**vòng sau không bao giờ tới**. Và greedy hiện tại còn lệch so với chính docstring của nó:

| | Đặc tả (`world-parameters` §3) | Docstring `dispatcher.py` | **Code thật** |
|---|---|---|---|
| Tầng 2 | bipartite Hungarian | "Hungarian để vòng sau" | **không có** |
| Xếp hạng | `cost = ETA_pickup` | *"greedy theo **ETA** tăng dần"* | **haversine** (`dispatcher.py:65-68`) |
| Thứ tự xét | — | — | **`sorted(open_orders, key=order_id)`** |

⇒ **Ba sai lệch chồng nhau**, không phải một.

## 2. Thực tế ngành làm thế nào (nguồn ngoài)

| Điểm | Thực tế | Nguồn |
|---|---|---|
| Thuật toán | **bipartite graph + Hungarian + batch matching** là chuẩn ngành (Uber, DiDi) | [Frugal Testing – Uber ride-matching](https://www.frugaltesting.com/blog/how-uber-prepares-its-ride-matching-app-for-high-demand) · [DiDi INFORMS 2020](https://tonyzqin.wordpress.com/wp-content/uploads/2020/11/inte.2020.1047.pdf) |
| Batch window | **~2 giây** (DiDi) tới 1–2 phút tuỳ nền tảng; dài hơn = ghép tốt hơn nhưng khách chờ lâu hơn | [Springer 2025 – batch-delay matching](https://link.springer.com/article/10.1007/s11518-025-5710-8) |
| Cost function | `Score = w₁·(1/ETA) + w₂·độ tin cậy tài xế + w₃·**mức sẵn sàng nhận** − w₄·detour` | [Appicial – trip accept algorithms](https://www.appicial.com/blog/the-secret-behind-faster-trip-accept-algorithms-in-taxi-dispatch-systems.html) |
| Bán kính chào | **1–3 km** | như trên |
| Xử lý từ chối | dispatch **tính cả tỷ lệ nhận lịch sử** của tài xế vào điểm số | như trên |
| H3 | **hex8** cho candidate retrieval / tham chiếu điểm đón (Rapido — **bike-hailing**, cùng loại hình Xanh SM) | [Rapido Labs](https://medium.com/rapido-labs/improving-dispatch-with-data-6a307dab7ecc) |

### 2.1 Rapido đặt tên đúng cho bug của chúng ta

Rapido phân biệt tường minh:

- **`bad_hex`** — ô **gần hơn về hình học** nhưng **lái chậm hơn**;
- **`good_hex`** — ô **xa hơn** nhưng **nhanh hơn**.

Đây **chính xác** là khuyết tật đã đo ở [`12`](12-root-cause-that-dispatch-pin-cho-don.md) §A4:
`dispatcher.py:77` chọn tài xế **gần nhất theo haversine**, nếu ETA của người đó fail thì **bỏ luôn
đơn**, viện lý do *"ETA đơn điệu theo distance"*. Với `factor` OSRM biến thiên **1,00 → 3,50**,
tiền đề đó sai; đo được **293/3.520 lượt bỏ OAN (8,3%)**.

⇒ Nói cách khác: **hệ đang ưu tiên `bad_hex` và vứt `good_hex` đi.**

## 3. H3 đang được dùng thế nào ở đây

| | Hiện tại | Đặc tả | Ngành |
|---|---|---|---|
| Res vận hành | **9** (~0,105 km²/ô, cạnh ~0,20 km) | 9 (85 ô lõi) | Rapido dùng **8** cho retrieval |
| Res báo cáo | 8 | 8 | — |
| `k_max` | **6** → phủ **2,22 km** | k=2 tại res 8 → ~2–2,5 km | chào 1–3 km |

⇒ Bán kính **tương đương ngành**, không phải chỗ sai chính. Sai chính là **tầng 2**.

**Lưu ý về `grid_disk` ở res 9**: k=6 sinh **127 ô**, k=8 → 217, k=12 → 469. Chi phí quét tuyến
tính theo số ô × số đơn mở × số tick. Ở res 8 thì k=2 chỉ 19 ô cho cùng bán kính — **rẻ hơn ~7 lần**.
Đây là lý do ngành dùng res thô hơn cho retrieval và res mịn cho phân tích. **Ứng viên tối ưu hoá**,
chưa làm.

## 4. Vì sao thiết kế đúng GỠ ĐƯỢC thế lưỡng nan Q-07

Đo ở [`14`](14-bien-gioi-cung-cau-va-tran-nang-luc.md): nới `k_max` làm served ↑ nhưng tỷ lệ nhận
thực tế trôi khỏi `accept_base` quá dung sai (k6 −0,042 → k8 −0,057). **Cơ chế**: greedy gán đơn
mới cho tài xế **xa**, tài xế từ chối nhiều hơn.

Hungarian gỡ được vì **ba lý do độc lập**:

1. **Tối ưu TỔNG thay vì từng đơn.** Greedy xét đơn theo `order_id` tăng dần: đơn cũ chiếm tài xế
   gần, đơn mới nhận phần thừa ở xa. Hungarian phân bổ toàn cục ⇒ **pickup trung bình GIẢM** khi
   nới shortlist, thay vì tăng. Đây là điều đảo chiều đánh đổi.
2. **Cost = ETA thật, không phải haversine** ⇒ hết cảnh chọn `bad_hex` rồi vứt đơn (8,3%).
3. **Không cần "thử tiếp ứng viên"** — bài toán gán đã xét toàn bộ cặp khả thi cùng lúc.

**Đây là giả thuyết có cơ chế rõ, PHẢI ĐO chứ không được tin**: điều kiện chấp nhận ở §6.

## 5. Thiết kế đề xuất (ưu tiên thực tế, không ưu tiên rẻ)

**Tầng 1 — candidate retrieval (giữ H3, sửa cách chọn bán kính)**
- Giữ `grid_disk` nhưng bán kính **suy từ ETA** thay vì hằng số ma thuật; cắt trần theo đường kính vùng.
- Vẫn giữ `candidate_ring_k` (bắt đầu) → nới dần tới `k_max` khi rỗng, như đặc tả.

**Tầng 2 — batched bipartite matching (XÂY MỚI, đúng đặc tả)**
- `cost(o,d) = ETA_pickup(d→o)` dùng **`factor_fn` theo cặp ô** (đường thật), **không** haversine.
- Cặp có `ETA > eta_max` ⇒ cost `LARGE` (loại), như `capacity_alloc` đã làm.
- `scipy.linear_sum_assignment` (đã là dependency, S4 đang dùng).
- Rơi về greedy khi `|O|==1` hoặc `|D|==1` (đặc tả) — và giữ greedy sau cờ config để **so sánh
  A/B thuật toán**, đúng ý *"greedy giữ làm baseline"*.
- **Deterministic**: cost matrix xây theo thứ tự `sorted(order_id)` × `sorted(actor_id)`;
  `linear_sum_assignment` deterministic với ma trận cố định. Tie-break vẫn `(eta, actor_id)`.

**CHƯA làm ở vòng này (ghi để không tự ý mở rộng)**
- Đưa **xác suất nhận** vào cost (ngành có làm). Rủi ro: dispatch sẽ "biết" `accept_base` —
  tham số **sinh hành vi** ⇒ oracle. Nếu làm thì phải dùng **tỷ lệ nhận lịch sử quan sát được**,
  và nó chạm tới ranh giới đo advisor ⇒ tách thành quyết định riêng.
- Chuyển retrieval sang res 8 (rẻ hơn ~7×) — tối ưu hoá, không phải đúng/sai.

## 6. Điều kiện chấp nhận (phải xanh CÙNG LÚC, ≥12 seed)

| # | Tiêu chí | Vì sao |
|---|---|---|
| 1 | `served_rate` **tăng** so với greedy hiện tại | mục tiêu chính |
| 2 | **`test_accept_matches_archetype_base` XANH** (lệch ≤ 5pp) | chính là ràng buộc đã chặn Q-07 |
| 3 | `test_no_dead_hour` xanh (không giờ nào > 40% hết hạn) | không hy sinh giờ cao điểm |
| 4 | **pickup trung bình KHÔNG tăng** | kiểm trực tiếp cơ chế §4.1 |
| 5 | Số đơn "bỏ oan" (còn ứng viên đạt ETA mà vẫn bỏ) **= 0** | kiểm cơ chế §4.2 |
| 6 | Determinism: cùng seed ⇒ cùng kết quả | CRN là nền của mọi phép đo A/B |
| 7 | `eta_max_min` **không đổi** | realism, không được vặn |
| 8 | Full suite xanh | — |

**Nếu (1) và (2) không cùng đạt** ⇒ giả thuyết §4 sai ⇒ **báo lại, không vặn tham số cho vừa**.

## 7. Chưa kiểm / rủi ro

- Hungarian trên `|O|×|D|` mỗi tick: hiện TB 3 đơn × 13 tài xế ⇒ rẻ. Giờ cao điểm có thể lớn hơn;
  **phải đo runtime**, có trần kích thước rồi mới rơi về greedy.
- Đổi thuật toán dispatch **làm lệch MỌI baseline** (30 seed, ablation, paired-fix). Phải đo lại.
- Kết quả ngành lấy từ blog kỹ thuật + paper, **không phải tài liệu nội bộ Xanh SM** — nhãn
  **press/medium**. Con số cụ thể (window 2s, bán kính 1–3 km) chỉ dùng để **định hướng**, không
  hard-code như sự thật.
