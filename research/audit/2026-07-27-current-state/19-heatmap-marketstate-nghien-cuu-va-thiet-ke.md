# Heatmap + MarketStateView: nghiên cứu và thiết kế

Ngày: 2026-07-28 · Cường mở ranh giới (2026-07-28): *"GSM có heatmap, mình có thể bắt chước họ,
MOCK data để xây heatmap thời gian thực — hoặc trong sim, UI y hệt — nếu không crawl được heatmap
thật — biết rằng họ có marketstate thật là tốt"*.

Phục vụ **T-045a**. Nối tiếp [`18`](18-vi-sao-toi-uu-hoa-khong-co-loi-cho-tai-xe.md) §4.5: vị trí là
**đòn bẩy duy nhất còn lại** chưa có trong không gian bài toán.

---

## 1. GSM đang có gì — nguồn official

[greensm.com, 15/04/2026](https://www.greensm.com/vn-vi/news/cap-nhat-tinh-nang-nhiem-vu-tiep-theo-toi-uu-nhan-cuoc)
(**official/high**), app **v3.6.1+**:

| | |
|---|---|
| Gợi ý | **MỘT khu vực duy nhất** — *"đi thẳng đến khu vực có nhu cầu chuyến đi cao nhất gần nhất"* |
| Căn cứ | *"khu vực có nhu cầu cao **gần vị trí hiện tại**"* + *"gợi ý phù hợp **theo thời điểm**"* |
| Quan hệ với heatmap | **KHÔNG thay thế** bản đồ nhiệt — bổ trợ; tài xế *"kết hợp với bản đồ nhiệt"* |
| Ràng buộc | **không bắt buộc**, tài xế có thể bỏ qua; dùng qua nút **"Dẫn đường"** |
| **Capacity / cảnh báo dồn cục / tần suất cập nhật** | **KHÔNG được nhắc tới** |

⇒ **Khoảng trống rõ ràng**: GSM cấp **tín hiệu cầu**, nhưng tài liệu không nói gì về việc **bao
nhiêu tài xế đã hướng tới cùng khu đó**.

## 2. Thực tế ngành — heatmap hiện đại là SUPPLY-AWARE

| Điểm | Nội dung | Nguồn |
|---|---|---|
| Grab **đã cập nhật** heatmap để *"khuyến khích tài xế **rời khỏi khu THỪA CUNG**"* sang khu cầu cao hơn | heatmap không chỉ vẽ cầu — nó vẽ **mất cân đối** | [Grab Engineering](https://medium.com/grab/understanding-supply-demand-in-ride-hailing-through-the-lens-of-grab-data-37ccde1a2e2c) |
| Heatmap tốt tính theo **cầu kỳ vọng + phân bố đội xe HIỆN TẠI và TƯƠNG LAI + vị trí riêng của tài xế** | ⇒ phải trừ cả **cung đang trên đường tới** | [Transportation Science / INFORMS](https://pubsonline.informs.org/doi/10.1287/trsc.2023.1202) |
| Đo được: heatmap cải thiện tỷ lệ hoàn thành **tới +25%** so với chỉ matching | có kỳ vọng định lượng để đối chiếu | như trên |
| **Herding vẫn là vấn đề nền tảng** vì tài xế không bị điều khiển tập trung | ⇒ tín hiệu thôi **không đủ**, cần phân bổ có trần | [ResearchGate — Heatmap Design for Probabilistic Driver Repositioning](https://www.researchgate.net/publication/383527199_Heatmap_Design_for_Probabilistic_Driver_Repositioning_in_Crowdsourced_Delivery) |

## 3. Vị trí của ta — KHÔNG cạnh tranh, mà bổ sung đúng chỗ thiếu

Tài liệu nội bộ `app-features-refresh-2026-07-24.md` §1 kết luận **"KHÔNG xây heatmap riêng"** vì sợ
*chồng đè và mâu thuẫn* với tối ưu của hãng. Kết luận đó **vẫn đúng cho phần TÍN HIỆU CẦU** — ta
không nên vẽ một bản đồ cầu khác với hãng.

Nhưng §2 cho thấy phần **cân đối cung** mới là chỗ tạo giá trị, và tài liệu official của GSM
**không đề cập**. Vậy ranh giới đúng:

| Thành phần | Ai làm | Ta làm gì |
|---|---|---|
| Tín hiệu **cầu** theo ô × giờ | **GSM** (heatmap + "Nhiệm Vụ Tiếp Theo") | **KHÔNG dựng bản đồ cầu cạnh tranh**. Trong sim/UI: **MOCK y hệt**, gắn nhãn |
| **Cung hiện tại** theo ô | — | suy được: sim = `World.actors`; thật = `public_driver_hex_tracking.current_hex` (**1,37M dòng, chưa khai thác**) |
| **Cung ĐANG TỚI** (đã được khuyên đi khu đó) | **không ai** | ⭐ **chỗ ta tạo giá trị** — đây là thứ chống dồn cục |
| **Phân bổ có trần** (capacity ledger) | **không ai** | ⭐ S4 `capacity_alloc` đã có sẵn kênh `standby_zone`, đang chết |

⇒ Sản phẩm không nói *"đi khu X"* (trùng hãng), mà nói được thứ hãng không nói:
***"khu X đang đông khách NHƯNG đã có nhiều tài xế hướng tới — khu Y cân bằng hơn"***, hoặc trỏ về
chính tính năng của hãng khi không có gì tốt hơn để nói.

## 4. Thiết kế `MarketStateView`

Theo `specs/advisor-objective-model-v2.md` §3, mỗi trường mang nhãn `available/degraded/absent`,
solver chạy được ở **cả ba mức**.

| Trường | Sim | Data thật | Khi absent |
|---|---|---|---|
| `expected_demand[cell, bucket]` | `demand_field` (λ config) | mật độ `trips` lịch sử theo hex×giờ | dùng λ config + hạ confidence |
| `supply_now[cell]` | đếm actor IDLE theo ô | `public_driver_hex_tracking.current_hex` + `last_seen_at` | `None` ⇒ **bỏ hẳn lời khuyên vị trí** |
| `supply_incoming[cell]` | actor đang `relocate` tới ô + **advice đã phát** | `target_hex` + `reached_target` (GSM đã có!) | 0 + nhãn degraded |
| `sd_ratio[cell]` | `demand ÷ (supply_now + supply_incoming)` | như trên | `None` |
| `station_queue[station]` | `Station.queue_len` | ❌ không có | `None` ⇒ không khuyên trạm cụ thể |

**Điểm mấu chốt** — `supply_incoming` phải đếm **cả lời khuyên VỪA PHÁT RA nhưng chưa thực hiện**.
Nếu không, 90 tài xế hỏi cùng một lúc sẽ nhận cùng một câu trả lời. Đây chính là *fallacy of
composition* mà hồ sơ [`07`](07-fleetwide-advice-equilibrium.md) đo được.

## 5. Vì sao S4 PHẢI bật cùng lúc, không được để sau

`capacity_alloc` gán candidate vào slot có trần, dư thì **unassigned ⇒ bỏ advice** (im lặng thay vì
đẩy thêm người vào chỗ đã đủ). Không có nó, heatmap là **cỗ máy tạo dồn cục**:

- §2 (nguồn ngoài): *"herding vẫn là vấn đề nền tảng"* dù đã có heatmap;
- hồ sơ [`07`](07-fleetwide-advice-equilibrium.md): khuyên diện rộng đã từng làm served giảm;
- câu hỏi của Cường (2026-07-28) về fairness: **đo thì có, cưỡng chế thì chưa**.

Hiện HHI dồn cục ≈ 0 **chỉ vì advisor chưa khuyên vị trí**. Bật heatmap mà không bật S4 là tự tạo
ra đúng vấn đề mình vừa xây thước để đo.

**Trần mỗi ô** = `max(0, expected_demand/bucket ÷ số_cuốc_một_tài_xế_phục_vụ_được − supply_now − supply_incoming)`.

## 6. Điều kiện chấp nhận (phải xanh CÙNG LÚC, ≥30 seed, `coverage: all`)

| # | Tiêu chí | Vì sao |
|---|---|---|
| 1 | Δ payout cá nhân **> 0**, CI không chứa 0 | mục tiêu; hiện −14.125đ |
| 2 | `served_rate` **không giảm** | ĐA-08 |
| 3 | đơn hết hạn **không tăng** | ĐA-08 |
| 4 | **Gini không tăng** | fairness — câu hỏi 2 của Cường |
| 5 | **HHI cung theo ô không tăng** | chống dồn cục — đây là rủi ro chính của heatmap |
| 6 | `test_sim_realism.py` xanh | không vặn thực tế |
| 7 | Tắt cờ ⇒ hành vi cũ y hệt | so A/B được |

**Nếu (1) đạt mà (5) hỏng ⇒ KHÔNG được bật.** Đó chính là kịch bản "advisor tự phá giá trị của
mình" mà `research/00_SUMMARY.md` #15 gọi là veto metric.

## 7. Ranh giới sản phẩm phải giữ

1. **Không hiển thị bản đồ cầu cạnh tranh với hãng** — trong UI của ta, heatmap là **MOCK có nhãn**,
   phục vụ demo/nghiên cứu; lời khuyên thật thì **trỏ về "Dẫn đường"** của app GSM.
2. Không bao giờ khuyên nhận/từ chối/huỷ **một đơn cụ thể** (`CLAUDE §5`).
3. Giữ 5 `STANDBY_SAFETY_FLAGS` sẵn có của S4: `capacity_aware`, `warn_acceptance`, `mock_label`,
   `no_income_promise`, `no_specific_order`.
4. Số hiển thị phải qua verifier như mọi card khác.

## 8. Chưa kiểm / rủi ro

- **Chưa biết tần suất cập nhật heatmap của GSM** — tài liệu không nói. Ta chọn bucket 30–60′,
  ghi nhãn ASSUMPTION.
- Con số **+25% fulfillment** là từ paper học thuật trên hệ khác — **không phải kỳ vọng cam kết**.
- `supply_incoming` ở data thật dựa vào `target_hex`/`reached_target`; **chưa kiểm** hai cột đó có
  dày dữ liệu không.
- Đổi hành vi vị trí **làm lệch mọi baseline** — phải đo lại lần nữa.
