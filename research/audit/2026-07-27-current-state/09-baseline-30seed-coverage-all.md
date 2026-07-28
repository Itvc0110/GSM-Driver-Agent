# BASELINE 30 seed · `coverage: all` · guardrail 4 tầng — số nền trước khi sửa mô hình

Ngày: 2026-07-27 · Bước 1 của `specs/advisor-objective-model-v2.md` §6 (**"đo trước, sửa sau"**).
Artifact thô: [`09-baseline30-coverage-all.json`](09-baseline30-coverage-all.json).

**Không có solver nào bị sửa trong lần đo này.** Mục đích duy nhất: có số nền đúng chuẩn (30 seed,
CRN, advice cho toàn đội, đủ 4 tầng chỉ tiêu) để mọi thay đổi sau này so được vào.

## 0. Thiết kế

| Mục | Giá trị |
|---|---|
| Seeds | 1000–1029 (**30**, đạt `MIN_SEEDS_FOR_SIGNIFICANCE`) |
| Ghép cặp | CRN — A và B cùng seed. **Đã kiểm**: `crn_ok = True` ⇒ hai nhánh cùng danh sách đơn |
| A | `advice.enabled = false` |
| B | `advice.enabled = true`, **`coverage: all`** (cả 90 tài xế) |
| Kênh | **mặc định của `configs/pilot_dongda.yaml`** = `shift_plan` bật; `accept_lift`/`shift_extend`/`rest_window` tắt |
| CI | bootstrap 5000 lần, 95% |

## 1. TẦNG CÁ NHÂN — advisor làm tài xế NGHÈO ĐI, có ý nghĩa thống kê

Tài xế đích: một P4 (tân binh) đại diện, **trong thế giới mà tất cả cùng nghe advice**.

| Chỉ số | A (tự làm) | B (theo advice) | Δ | CI 95% | seed có lợi |
|---|---|---|---|---|---|
| **payout/ngày** | 315.927đ | 298.618đ | **−17.310đ** | **[−29.294, −5.820]** ⛔ | **7/30** |
| **cuốc hoàn thành** | 13,3 | 11,7 | **−1,6** | **[−2,4, −0,83]** ⛔ | 6/30 |
| **phút RỖI** | 127,2 | 153,1 | **+25,9** | **[+11,4, +41,7]** ⛔ | 20/30 |
| phút online | 533,7 | 532,2 | −1,5 | [−18,6, +12,8] | 12/30 |
| acceptance_rate | 0,76 | 0,76 | 0,00 | [−0,03, +0,03] | 11/30 |

⛔ = CI **không chứa 0** ở n=30 ⇒ **kết luận có ý nghĩa thống kê**, không phải nhiễu.

**Đây là lần đầu tiên tác hại lên cá nhân được chứng minh ở mức đủ seed.** Trước đó chỉ có 5 seed
(hồ sơ [`06`](06-why-advice-loses-money.md)) — đủ chỉ cơ chế, chưa đủ kết luận. Cường báo *"làm
theo Advisor ra tiền ít hơn tự làm"* — **số liệu xác nhận, và mạnh hơn báo cáo ban đầu**.

### Cơ chế lộ ra rất rõ

`online_min` **không đổi** (−1,5, không significant) nhưng `idle_min` **+25,9** và cuốc **−1,6**.

⇒ Advice **không** làm tài xế chạy ít giờ hơn. Nó làm họ **dùng cùng số giờ đó tệ hơn**: cùng thời
gian online, nhiều thời gian rỗi hơn, ít cuốc hơn. Khớp chính xác với chẩn đoán toán học của spec —
DP luôn chọn `ONLINE` (98,5% lời khuyên) vì `REST`/`SWAP` cộng đúng `0.0`, nên tài xế bị giữ online
trong lúc pin thấp / ở vùng ít cầu thay vì đi đổi pin hoặc nghỉ đúng lúc.

## 2. TẦNG HỆ THỐNG — hại theo HƯỚNG nhất quán, nhưng KHÔNG đủ ý nghĩa thống kê

| Chỉ số | Δ trung bình | CI 95% | Xấu đi ở |
|---|---|---|---|
| served_rate | −0,0047 | [−0,0106, +0,0012] | 16/30 seed |
| đơn hết hạn | **+4,8 đơn/ngày** | [−1,0, +10,9] | 16/30 seed |
| **TỔNG payout toàn đội** | **−168.517đ/ngày** | [−358.681, +34.267] | 15/30 seed |
| Gini | −0,0030 | [−0,0090, +0,0026] | 15/30 seed |
| station HHI | +0,0007 | [−0,0099, +0,0113] | 14/30 seed |
| supply-cell HHI | +0,0001 | [−0,0003, +0,0005] | 16/30 seed |
| trung vị chờ khách | −0,0003′ | [−0,0014, +0,0009] | 9/30 seed |
| giờ "đói cung" (`starved_hours_n`) | +0,067 giờ | [−0,20, +0,33] | — |

**Mọi CI đều chứa 0.** Ở 30 seed, không tầng hệ thống nào đạt ngưỡng ý nghĩa.

**Tái lập:** chạy độc lập hai lần → `per_seed` và mọi trường hệ thống **trùng khít tuyệt đối**
(`crn_ok = True` cả hai lần). Số trong hồ sơ này sinh lại được từ code trong repo.

### ⚠ ĐÍNH CHÍNH hồ sơ [`07`](07-fleetwide-advice-equilibrium.md)

Hồ sơ 07 (10 seed) đọc kết quả theo hướng *"khách hàng bị ảnh hưởng thật"*. Ở 30 seed:

- `served_rate` giảm **16/30 = 53%** số seed (10 seed cho 6/10 = 60%) — gần với **tung đồng xu**;
- đơn hết hạn **+4,8/ngày** (10 seed cho +7,9), **CI chứa 0**.

⇒ **Hướng vẫn xấu và nhất quán, nhưng không được tuyên bố là đã chứng minh.** Câu đúng phải là:
*"chưa có bằng chứng advice cải thiện hệ thống; tín hiệu hiện có nghiêng về phía làm xấu, chưa đủ
mạnh để kết luận"*. Hồ sơ 07 đã ghi rõ ở §6 rằng 10 seed *"chưa đủ cho khoảng tin cậy"* — đính
chính này là thực hiện đúng điều đã tự cảnh báo, không phải phát hiện mâu thuẫn mới.

### Điều KHÔNG đổi so với hồ sơ 07

Lo ngại **"dồn sạc/nghỉ cùng lúc"** tiếp tục **KHÔNG xảy ra**: station HHI +0,0007 và supply-cell
HHI +0,0001 — hai số gần như bằng 0 tuyệt đối. Herding kiểu dồn về một điểm **không phải** cơ chế
gây hại ở config này.

## 3. Kết luận dùng được ngay

1. **Tác hại nằm ở tầng CÁ NHÂN, không phải tầng hệ thống.** Advisor hiện tại làm mỗi tài xế nghèo
   đi ~17.310đ/ngày (significant); tổng thiệt hại toàn đội chỉ là phép cộng của việc đó, chứ không
   phải hiệu ứng cân bằng thị trường mới.
2. ⇒ **Thứ tự sửa của spec §6 là đúng**: sửa objective cá nhân (C1/C2/C5 → CVaR) TRƯỚC, multi-agent
   equilibrium (ĐA-09) sau. Nếu làm ngược, sẽ đi tối ưu cân bằng cho một hàm mục tiêu vốn đã sai.
3. **Chỉ tiêu kép (ĐA-08) đã có số nền để so.** Mọi thay đổi solver từ nay phải chạy lại đúng bộ
   này và **cả 5 tầng đều không được xấu đi**.
4. `shift_plan` — kênh **đang bật mặc định trong mọi demo** — là kênh sinh ra toàn bộ Δ âm trên.
   Theo quyết định của Cường: **giữ bật + cảnh báo đỏ**, đo lại sau mỗi bước; **bản cuối trước khi
   chốt, nếu vẫn không hiệu quả thì TẮT để advisor im lặng**.

## 4. Chưa kiểm (trung thực)

- Chỉ **một archetype** (P4 tân binh) ở tầng cá nhân. P1/P2/P3/P5/P6/P7 chưa đo ở `coverage: all`.
- Chỉ **một kênh** (`shift_plan`, mặc định). Thang bậc kênh ở diện rộng chưa chạy — `run_ladder`
  nay đã nhận tham số `coverage`, nhưng lần chạy 30 seed cho từng bậc chưa thực hiện.
- Chỉ **một config** (`pilot_dongda`), một ngày/seed. Chưa quét `coverage.share` 10/25/50%.
- Chưa đo tác động tới khách ở mức **huỷ do chờ lâu**; mới có đơn hết hạn + trung vị chờ.
