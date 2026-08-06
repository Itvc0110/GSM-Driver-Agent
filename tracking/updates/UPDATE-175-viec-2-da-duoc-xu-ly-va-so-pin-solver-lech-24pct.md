# UPDATE-175 — Việc 2 hoá ra ĐÃ được xử lý sẵn; việc 3 tìm ra `D-ADV-06`: sổ pin solver lệch **+24%**

- **Ngày:** 2026-08-07
- **Loại:** verification (việc 2) + finding mới có số tự đo (việc 3) — **0 dòng code thay đổi**
- **Nợ mới:** `D-ADV-06`
- **Probe:** `research/audit/2026-08-06-root-cause-idle/f6-drop-outside-core.py` (họ probe cùng thư mục);
  đoạn đo SOC ghi trong UPDATE này (bọc `Actor.consume_soc`, 3 seed arm A)

## 1. Việc 2 (`sp_end_only` chết cấu trúc) — **KHÔNG cần sửa gì, đã được chặn sẵn**

`00-SUMMARY` (S2-5) cảnh báo: `sp_end_only` là **code chết** (`END` bất khả ở bucket 0 trong world
zero-cost; agent đo **0/68** và **0/612** cấu hình) ⇒ *"người đọc ablation E-05 sẽ đọc nhầm im-lặng-cấu-trúc
thành **không có ca nào đáng kết sớm**"*, và nó tự ghi *"chưa kiểm UPDATE-155 đã báo số nào chưa — nếu có
thì phải kiểm lại"*.

**Tôi kiểm: `UPDATE-155` đã diễn giải ĐÚNG ngay từ đầu.** Nó viết `Δ = 0.00, CI (0,0)` trên mọi metric
**kèm lý do cấu trúc**: *"`online_net ≥ 0` bất cứ khi nào còn cầu ⇒ DP không bao giờ chọn END làm hành
động ĐẦU LỊCH"*. ⇒ **Cách đọc sai mà 00-SUMMARY lo đã bị chặn bởi chính UPDATE-155.** Không có gì phải
đính chính; nợ *"kênh chi-phí trơ trong world zero-cost"* đã nằm ở `D-E4-01`.

**Kết quả của việc 2 là: không có việc.** Ghi lại để không ai mở cycle cho nó, và để thấy một lần
**cảnh báo của refuter cũng cần kiểm** — không phải mọi cảnh báo đều là nợ.

## 2. Việc 3 → `D-ADV-06`: solver S2 tin pin cạn nhanh hơn thực tế **~24%**

| tầng | giả định / thực tế |
| --- | --- |
| **Solver S2** | `soc_bands: 10` (1 band = **10 pp**) × `soc_cost_per_bucket: 1` band/30′ ⇒ **20,00 pp SOC / giờ online** |
| **World (tôi ĐO)** | bọc `Actor.consume_soc`, 3 seed arm A: **36.834 pp / 2.281 giờ online = 16,15 pp/giờ** |
| **Tỷ số** | **0,807** ⇒ solver **ước CAO ~24%** |

⇒ DP tin pin cạn nhanh hơn thực tế **~1/4** ⇒ chèn `SWAP` **sớm hơn cần** ⇒ tiêu downtime đổi pin không
đáng. Mọi kênh dựa trên S2 bị thiên lệch **cùng chiều**. **Cùng lớp `D-M3-17` / `D-ADV-04`**: một tầng tự
tính một đại lượng **khác** engine — lần này ở tầng **solver**, không phải UI hay producer.

Test hiện có chỉ ghim **TỶ LỆ** scale theo `bucket_min`, **không ghim MỨC** (pp/giờ) ⇒ lệch mức **sống
sót qua cả suite**.

⚠ **Tôi sửa độ lớn của agent:** `mm-07` (S2-6) báo *"~14,7%/giờ, drift ~36%"*. Chiều **đúng**, độ lớn
**sai**. Số dùng chính thức là **16,15 pp/giờ, +24%** — vì tôi đo **trên sim đang chạy**, còn agent **suy
từ config**.

## Kiểm chứng

- Đo SOC bằng cách bọc `Actor.consume_soc` (cộng `km × pct_per_km`), restore trong `finally`; mẫu số là
  `Σ online_min / 60` trên **mọi** actor của 3 seed.
- **Chưa kiểm chứng / giới hạn:** phép đo **trộn hai đội** (swap `1.6` vs charge `0.85` pp/km) trong khi
  `soc_cost_per_bucket` của solver là **fleet-agnostic** ⇒ so theo **từng đội** có thể ra số khác; ai
  thi hành fix phải tách đội. Tôi **không** đo lại `0/68` và `0/612` của S2-5 (đã có hai nguồn độc lập
  đồng ý: agent + chính UPDATE-155).
- Suite: **không chạy** — 0 dòng code thay đổi.

## Visual
`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. **Việc 2 cho kết quả "không có việc"** — và đó là kết quả có giá trị. Nếu tôi mặc định *"refuter cảnh
   báo thì phải có nợ"* thì đã mở một cycle vô ích. **Cảnh báo cũng phải kiểm như phát hiện.**
2. Lần thứ **hai trong ngày** tôi sửa **độ lớn** của một số agent trong khi giữ **chiều** của nó
   (`D-M3-21` bind 96,25% · nay `D-ADV-06` 24% thay 36%). Mẫu chung: agent **suy từ config**, tôi **đo
   trên sim**. ⇒ Quy tắc: *số suy-từ-config phải được đo lại trước khi vào kết luận.*
3. Giới hạn trộn-hai-đội của phép đo là thật và tôi nói ra thay vì làm tròn — nếu đội charge chiếm phần
   lớn giờ online thì `16,15` bị kéo xuống và độ lệch thật với đội **swap** sẽ **nhỏ hơn** 24%.
4. Tôi **chưa** đọc hết 7 artifact `mm-*` (việc 3 mới làm được một finding) ⇒ việc 3 **còn dở**, không
   phải đã xong.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13 ·
**amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
