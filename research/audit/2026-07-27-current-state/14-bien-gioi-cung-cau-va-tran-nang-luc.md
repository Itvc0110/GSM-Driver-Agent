# Biên giới cung–cầu: vì sao `served_rate` và `trips/driver` không thể cùng đạt — và đòn bẩy thật

Ngày: 2026-07-28 · Quét lưới 16 tổ hợp × 3 seed. Artifact: [`14-joint-sweep-actors-orders.json`](14-joint-sweep-actors-orders.json).
Nối tiếp [`12`](12-root-cause-that-dispatch-pin-cho-don.md) và [`13`](13-kiem-ke-bien-mau-loi-va-ke-hoach.md).

> **Hồ sơ này đính chính HAI khuyến nghị trước của chính tôi.** Xem §5.

---

## 1. Sai lệch thiết kế: hai tham số coupled, chỉ một cái được đổi

`research/simulation/pilot-world-dongda.md` §3 (đọc lại theo yêu cầu Cường):

> *"Scale cho **50 actors** Xanh SM… đơn 'chảy đến' 50 actors ≈ **900–1.500/ngày**… Tham số sim:
> `orders_per_day = 1.200` (mặc định) → **~19–21 cuốc/actor/ngày**"*

`specs/simulation-pilot-world.md` tiêu đề: *"Pilot World: Đống Đa, **50 actors**"*.

| | thiết kế gốc | hiện tại |
|---|---|---|
| `actors.n` | **50** | **90** (đi qua 74) |
| `demand.orders_per_day` | **1.200** | **1.200** (không đổi) |
| đơn/actor | **24,0** | **13,3** (−45%) |
| cuốc/actor kỳ vọng | 19–21 | **10,2** |

`git log -S` xác nhận `orders_per_day` **chưa từng được scale lại** kể từ commit scaffold.

⇒ **Đúng mẫu lỗi #5** (hồ sơ `13` Phần 1): `actors.n` bị nâng để kéo `served_rate`, tham số
coupled không ai đụng tới.

**Lưu ý về phạm vi**: tổng cầu XSM Đống Đa mà research ước là **4.500–7.200 đơn/ngày**, nên nâng
`orders_per_day` lên ~2.000 **nằm trong dải đã nghiên cứu** — KHÔNG phải bịa cầu (đính chính §5.1).

## 2. BUG: shortlist H3 nhỏ hơn bán kính mà ETA cho phép

| | |
|---|---|
| `eta_max_min = 11` (có căn cứ research 8–10′ + hiệu chỉnh factor) | bán kính khả thi **1,61 km** (17 km/h, factor 1,94) … **3,14 km** (25 km/h, 1,46) … **4,44 km** (30 km/h, 1,24) |
| `candidate_ring_k_max = 6` ở res 9 | phủ **1,81 km** |

⇒ Tài xế cách 1,81–4,44 km **thoả ETA nhưng không bao giờ vào shortlist**. Lại là *hai tham số
phải khớp nhau nhưng được đặt độc lập*.

**Đo (3 seed, giữ nguyên `eta_max = 11`)**:

| `k_max` | phủ | served | cuốc/tx | đơn hết hạn |
|---|---|---|---|---|
| **6** (hiện tại) | 1,81 km | 0,750 | 9,9 | 238 |
| 10 | 3,01 km | 0,784 | 10,4 | 199 |
| 14 | 4,22 km | 0,789 | 10,4 | 195 (bão hoà) |

**Cả hai metric cùng lên** — khác hẳn việc chỉnh tỷ lệ cung/cầu (luôn đánh đổi). Đây là **fix thuần
tuý không mất gì**.

⚠ **Không được nâng `eta_max`** để số đẹp hơn: 11 phút là ràng buộc **realism** (khách không chờ
đón 18 phút). Nâng nó là vặn thực tế cho vừa kết quả — `CLAUDE §4b` cấm.

## 3. Quét lưới: KHÔNG tổ hợp nào đạt cả bốn tiêu chí

`k_max = 12`, 3 seed/ô. Tiêu chí: served ∈ [0,78; 0,88] · cuốc/tx ≥ 15 · chờ p99 < 60′ · không
khoảng nào > 180′.

| n \ O | 1400 | 1600 | 1800 | 2000 |
|---|---|---|---|---|
| **60** | 0,655 / 15,3 | 0,612 / 16,0 | 0,569 / 17,0 | 0,542 / 17,8 |
| **70** | 0,708 / 14,2 | 0,660 / 14,8 | 0,625 / 16,0 | 0,596 / 16,8 |
| **80** | 0,744 / 13,1 | 0,705 / 13,9 | 0,684 / 15,3 | 0,658 / 16,2 |
| **90** | **0,780** / 12,2 | 0,734 / 12,8 | 0,715 / 14,2 | 0,694 / 15,2 |

(mỗi ô: `served` / `cuốc/tx`) — **0/16 PASS**. Biên giới rất rõ: `served` tăng theo N/O,
`cuốc/tx` tăng theo O/N. **Hai chiều đối nghịch, không có điểm giao thoả cả hai.**

Điều tốt: **mọi tổ hợp đã diệt được triệu chứng chờ hàng giờ** — `>180′` = 0 ở 13/16 ô.

## 4. Trần năng lực: VẬT LÝ ĐÚNG, mất mát nằm ở phân bổ

| cấu hình | thời gian **rỗi** | cuốc/tx | trần lý thuyết |
|---|---|---|---|
| n=90 O=1200 (**hiện tại**) | **32%** | 10,6 | 25,4 |
| n=90 O=2000 | 13% | 15,4 | 25,6 |
| n=60 O=2000 (**bão hoà**) | **5%** | **17,7** | 25,4 |

Phân bổ thời gian khi bão hoà (n=60, O=2000): `on_trip` 49% · `enroute` 24% · **`relocate` 14%**
· `charge` 8% · `rest` 5%.

**Đọc đúng ba điều:**

1. **Năng lực mỗi tài xế ≈ 17,7 cuốc/ngày khi bão hoà** — chạm **biên dưới** dải research 18–22.
   ⇒ **Vật lý của sim không sai.** Không cần chỉnh tốc độ/quãng đường.
2. Cấu hình hiện tại để tài xế **rỗi 32%** — đó là hệ quả trực tiếp của §1 (thừa cung).
3. Kể cả khi bão hoà, **14% thời gian là `relocate` (deadhead)** — chạy rỗng. Cộng với việc ở tải
   trung bình (n=90, O=2000) vẫn còn **13% rỗi** dù có 22 đơn/tài xế: **đơn phân bố không đều
   trong không gian**, người thì ngập đơn, người thì đói.

⇒ **Đòn bẩy duy nhất đẩy được CẢ HAI metric là phân bổ không gian**: giảm deadhead và ghép đúng
người gần. Đó chính là **T-045a** (`MarketStateView` + hồi sinh S4) — và cũng chính là **giá trị
sản phẩm thật của advisor**: khuyên **đứng ở đâu**.

## 5. ĐÍNH CHÍNH hai khuyến nghị trước của tôi

### 5.1 Tôi gọi "tăng `orders_per_day`" là **bịa cầu** — SAI

Lúc viết hồ sơ `12` §4.3 tôi **chưa đọc** `pilot-world-dongda.md` §3. 1.200 là con số gắn với
**50 actors**, không phải hằng số của quận; tổng cầu quận ước **4.500–7.200/ngày**. Nâng lên
~2.000 cho 90 actors là **khôi phục tỷ lệ thiết kế**, có căn cứ research.

### 5.2 Tôi khuyến nghị (B) **mở rộng zone** — và Cường đã duyệt. Nhưng nó KHÔNG giải được bài toán này

Mở rộng zone giữ nguyên **mật độ** (đơn/km²) ⇒ khoảng cách tới đơn kế tiếp **không đổi** ⇒ kinh tế
mỗi tài xế **không đổi** ⇒ **thế lưỡng nan served/trips vẫn y nguyên**, chỉ là ở quy mô lớn hơn.

Mở rộng zone vẫn **đáng làm** vì lý do **realism** (tài xế thật chạy liên quận — `D-SIM-01`), nhưng
nó **không phải** cách sửa "chờ đơn hàng giờ", và **không nên** làm trước vì rất tốn công (dựng
lại demand/POI/OSRM matrix cho vùng lớn).

**Tôi đề nghị Cường cho phép đổi thứ tự** — chi tiết §6.

## 6. Đề nghị thứ tự (thay cho kế hoạch cũ)

| Bước | Việc | Vì sao trước | Chi phí |
|---|---|---|---|
| **1** | **`k_max` 6 → 12** (giữ `eta_max=11`) | fix thuần, **cả hai metric cùng lên**, không mất gì | 1 dòng + 4 test |
| **2** | **Khôi phục tỷ lệ đơn/actor** về dải thiết kế; **ghi rõ biên giới §3 vào config** và chọn một điểm có chủ ý | sửa sai lệch thiết kế §1; diệt chờ-hàng-giờ | 1 dòng + 4 test + đo lại baseline |
| **3** | **T-045a `MarketStateView` + S4** | **đòn bẩy DUY NHẤT** đẩy được cả hai (§4) — và đúng giá trị sản phẩm của advisor | lớn |
| **4** | Mở rộng zone liên quận | realism, không phải fix; làm sau khi 1–3 xong | rất lớn |

**Về bước 2 — phải trung thực trong config**: không thể đạt cả hai, nên phải **chọn** và **ghi rõ
đang đứng ở đâu trên biên giới**, thay vì để người sau tưởng đã tối ưu. Đề nghị ghi bảng §3 thẳng
vào `configs/pilot_dongda.yaml` cạnh hai tham số.

## 7. Chưa kiểm (trung thực)

- Quét dùng **3 seed/ô** — đủ so sánh tương đối, **chưa đủ CI** (chuẩn ≥30; và so biến thể cần
  ≥100 theo `MIN_SEEDS_FOR_VARIANT_COMPARISON`).
- `k_max=12` chọn theo bán kính ETA trung bình; **chưa quét chi phí tính toán** khi k lớn.
- Trần 17,7 cuốc đo ở **một** cấu hình bão hoà, seed 1000.
- Chưa kiểm liệu giảm `relocate` (14%) có khả thi không — mới chỉ ra nó tồn tại.
- Chưa đo tác động của bước 1+2 lên **chỉ tiêu kép ĐA-08** (phải làm trước khi chốt).
