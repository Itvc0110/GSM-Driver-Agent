# Q-07 — tiền đề SỤP: `accept_base` của P7 không sai, THƯỚC ĐO sai (và nó ăn tiền thật)

Ngày 2026-08-08 · tiền-plan cho Cycle 1 · **kết luận: KHÔNG hiệu chỉnh `accept_base` P7**

## Bối cảnh

Cường quyết xử Q-07 bằng cách **hiệu chỉnh lại `accept_base` của P7** (giả thuyết: `0,94` là prior
cũ sai, realized ~0,889 mới đúng). Trước khi vào plan mode tôi chạy **falsifier cho chính quyết
định đó**, với tiêu chí phán quyết ghi **trước** khi thấy số
(`q07-accept-base-p7-co-sai-khong.py`):

> Riêng P7 lệch ⇒ hiệu chỉnh là **sửa sự thật**.
> **Cả đội** cùng lệch ⇒ hiệu chỉnh riêng P7 là **vặn số cho test xanh** = che khuyết tật ⇒ KHÔNG LÀM.

## Bước 1 — falsifier bắn: 7/7 archetype lệch ÂM

20 seed, advisor TẮT, đo **đúng phép** mà `tests/test_sim_realism.py:68-73` dùng:

| arch | base | realized k=6 | lệch | realized k=8 | lệch |
| --- | --- | --- | --- | --- | --- |
| P1 | 0,85 | 0,8441 | −0,0059 | 0,8344 | −0,0156 |
| P2 | 0,95 | 0,9235 | −0,0265 | 0,9246 | −0,0254 |
| P3 | 0,98 | 0,9560 | −0,0240 | 0,9506 | −0,0294 |
| P4 | 0,80 | 0,7870 | −0,0130 | 0,7818 | −0,0182 |
| P5 | 0,97 | 0,9379 | −0,0321 | 0,9292 | −0,0408 |
| P6 | 0,93 | 0,9031 | −0,0269 | 0,9044 | −0,0256 |
| **P7** | 0,94 | 0,8962 | **−0,0438** | 0,8831 | **−0,0569** |

Trung bình **−0,0246** (k=6) / **−0,0303** (k=8). P7 là cái **lệch nhất**, không phải cái **duy
nhất** lệch.

⚠ Giả thuyết đầu tiên của tôi (**Jensen**: σ lõm ở p>0,5 nên E[σ(·)] < base) **bị chính dữ liệu
bác** — Jensen dự đoán lệch lớn nhất quanh base ≈ 0,79, mà P4 (base 0,80) lại lệch **gần ít nhất**.
Không dùng giả thuyết chưa kiểm để giải thích.

## Bước 2 — root cause: MẪU SỐ NHIỄM lượt tài xế CHƯA TỪNG ĐƯỢC HỎI

`src/gsm_sim/world.py:647` tăng `orders_offered` **TRƯỚC** cổng pin ở `:654-664`:

```python
actor.orders_offered += 1          # :647  ← đếm là "đã chào"
...
enough = actor.soc_pct - total_km * self._pct_per_km(actor) > 8.0
if not enough:
    actor.orders_soc_skipped += 1
    self.log(actor.actor_id, "order_skipped_soc", ...)
    continue                        # ← `decide_accept` KHÔNG BAO GIỜ được gọi
```

⇒ Lượt đó vào **mẫu số** nhưng **không hề là một quyết định của tài xế**. Chính sim đã tự khai
điều này ở nhánh bên cạnh (`SIM-1: KHÔNG còn tính là "cancelled" — tài xế chưa hề nhận đơn`) —
tức ngữ nghĩa đã được nhận ra cho `cancelled`, nhưng **bỏ sót cho `offered`**.

Đây đúng lớp lỗi **"mẫu số nhiễm ca cố ý ngoài phạm vi"** đã làm hai claim của agent sai trong
cùng phiên này (`M1`, `M5`).

### Kiểm: bỏ skip-pin ra khỏi mẫu số thì khoảng lệch SẬP

10 seed, advisor TẮT:

| arch | base | realized **cũ** | lệch | realized **sạch** | lệch | % skip pin |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | 0,85 | 0,8481 | −0,0019 | 0,8504 | **+0,0004** | 0,3% |
| P2 | 0,95 | 0,9253 | −0,0247 | 0,9425 | −0,0075 | 1,8% |
| P3 | 0,98 | 0,9511 | −0,0289 | 0,9794 | **−0,0006** | 2,9% |
| P4 | 0,80 | 0,7877 | −0,0123 | 0,7931 | −0,0069 | 0,7% |
| P5 | 0,97 | 0,9364 | −0,0336 | 0,9621 | −0,0079 | 2,7% |
| P6 | 0,93 | 0,9046 | −0,0254 | 0,9179 | −0,0121 | 1,4% |
| **P7** | 0,94 | 0,8984 | **−0,0416** | **0,9317** | **−0,0083** | **3,6%** |

Lệch trung bình **−0,0241 → −0,0061**. Với P7, **80% khoảng lệch là hiện vật đo**. Và `% skip pin`
**xếp hạng đúng** thứ tự độ lệch (P7 3,6% lệch nhiều nhất · P1 0,3% lệch ít nhất) — đó là bằng
chứng cơ chế, không phải trùng hợp.

⇒ **`accept_base = 0,94` của P7 KHÔNG SAI.** Realized sạch **0,9317**, lệch **0,83đp**, nằm sâu
trong dung sai 5đp.

## Bước 3 — nó KHÔNG chỉ là thước đo. Nó ăn TIỀN.

`entities.py:122-123`: `acceptance_rate = orders_accepted / orders_offered` — **cùng mẫu số nhiễm**.
Và `world.py:552` / `:1092`:

```python
bonus = self.policy.day_bonus(a.points, a.acceptance_rate, a.completion_rate)
```

`day_bonus` trả **0** khi `acceptance < bonus_min_acceptance` (0,85) — **bất kể điểm**
(`advice_bridge.py:106` đã ghi rõ tính chất này).

**Đo (10 seed, 900 driver-day, advisor TẮT):**

| | |
| --- | --- |
| bị đẩy xuống dưới 0,85 **chỉ vì** skip-pin | **46/900 = 5,11%** |
| trong đó **thực sự mất tiền** (đủ điểm) | **33** |
| thưởng bị mất | **1.080.000đ / 10 seed = 108.000đ/ngày** |

Đội 90 người ⇒ **108.000đ/ngày** so với **toàn bộ** lợi ích advisor đang đo được
(+3.219đ × 90 = 289.710đ/ngày) ⇒ lỗi này bằng **37%** lợi ích advisor.

### Lan tới đâu

1. **`tests/test_sim_realism.py`** — cổng đang chặn k=8 đo trên đại lượng nhiễm ⇒ **Q-07 xây trên
   tiền đề sai**.
2. **Payout của sim** — mọi số payout đã đo (gồm `+3.219đ`) tính trên một thế giới có 3,67%
   driver-day bị tước thưởng oan.
3. **Mock data → đường sản phẩm** — `mockgen/realdata.py:138-141` lấy **thẳng** `accepted`/`offered`
   từ `sim_stats` ⇒ `acceptance_rate` trong `driver_statistic_daily` **cũng nhiễm** ⇒ advisor thật
   đọc số nhiễm.
4. ⚠ **Cảnh báo `P1b` tôi vừa ship** nhắm đúng dải sát ngưỡng 0,85. Một phần tài xế ở đó là do
   **skip pin**, không do từ chối — mà câu cảnh báo nói *"vài lần từ chối nữa là mất toàn bộ
   thưởng"*. **Quy sai nguyên nhân.** Chưa đo bao nhiêu phần trăm; phải đo trước khi sửa lời.

## Câu hỏi KHÔNG phải của tôi

Lượt bị chặn vì pin **có nên** tính vào tỷ lệ nhận của tài xế không, là **định nghĩa chính sách
của GSM**, không phải lựa chọn kỹ thuật của ta. Sim hiện mô hình hoá nó như **hệ thống bỏ qua**
(`order_skipped_soc`, không gọi `decide_accept`) — nên **đếm nó vào mẫu số là mâu thuẫn với chính
mô hình**. Nhưng nếu GSM thật tính kiểu khác thì phải theo GSM.

## Đề xuất — Cycle 1 nên ĐỔI NỘI DUNG

| | cũ (Cường đã duyệt) | **đề xuất mới** |
| --- | --- | --- |
| làm gì | hiệu chỉnh `accept_base` P7 | **sửa mẫu số tỷ lệ nhận**: loại lượt `order_skipped_soc` |
| vì sao | 0,94 là prior sai | 0,94 **đúng**; thước đo sai, và nó **ăn 108.000đ/ngày** |
| tác dụng phụ | test xanh | có thể **mở k=8 miễn phí** (P7 sạch chỉ lệch 0,83đp) ⇒ **−32,6 đơn chết/ngày** |
| rủi ro | che khuyết tật thật | đổi payout ⇒ **phải đo lại mọi số cũ**, gồm `+3.219đ` |

⚠ Đổi hành vi sim ⇒ **plan mode + duyệt**, không tự làm.
