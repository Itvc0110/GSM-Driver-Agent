# UPDATE-172 — F5 GIẢI được câu `UNRESOLVED` + số phản biện vòng 2 (mạnh hơn nhiều) + đính chính 65,3%

- **Ngày:** 2026-08-07
- **Loại:** research (đo thật, cổng nhiễu-loạn XANH) + đính chính một con số tôi đã dùng nhiều nơi
- **Artifact:** `f5-visit-vs-holding.py` + `.json` · 7/7 `pb-*.json` (vòng 2)
- **0 dòng code sản phẩm/sim thay đổi**

## 1. ✅ `UNRESOLVED` ĐÃ GIẢI: hai ô hút là **GIẾNG SÂU + ĐÔNG LƯỢT**, và F1 đo **sai đại lượng**

Câu treo từ `UPDATE-169/170`: *vì sao đội xe dồn vào cặp XA (`953`+`bb3`) thay vì cặp mà luật ưu ái?*

Đo (arm A, 5 seed, **cổng nhiễu-loạn XANH**, tổng 15.310′ idle/ngày — khớp rc-03):

| ô | idle ′/ngày | % tổng | lượt vào/ngày | **giữ ′/lượt** |
| --- | --- | --- | --- | --- |
| `bb3` ← ô hút rc-03 | **5.721** | **37,4%** | **191,6** | **29,9** |
| `953` ← ô hút rc-03 | **2.761** | **18,0%** | **120,8** | **22,9** |
| `94b` | 1.647 | 10,8% | 149,6 | 11,0 |
| `88f` ← **F1 "lưu vực rộng nhất"** | **56** | **0,4%** | **9,6** | 5,8 |
| `8c7` ← cùng cặp | **110** | 0,7% | **14,4** | 7,7 |

- Hai ô hút giữ **55,4%** phút idle — rc-03 báo 56,6% ⇒ **khớp**.
- Thời gian giữ **trung vị mọi ô: 6,9′**. Hai ô hút giữ **3,3×–4,3×** trung vị.
- Cặp mà F1 gọi là *"lưu vực rộng nhất (42,8%)"* thực tế nhận **9,6 / 14,4** lượt vào/ngày — **kém 20×**
  so với `bb3` — và giữ **xấp xỉ trung vị** ⇒ tổng chỉ **~1%** phút idle.

**⇒ Kết luận:** phút idle tích lũy = **(lượt vào) × (thời gian giữ)**. F1 chỉ đo **độ RỘNG lưu vực**
(bao nhiêu ô khởi đầu *dẫn tới*) — một đại lượng **không** dự đoán được cả hai vế thật. Hai ô hút thắng
ở **CẢ HAI**: đông lượt vào **và** giữ lâu nhất. Cơ chế "cực đại địa phương ở ring 1 với `bar = 1,25`"
của verdict **đúng** — nó chính là thứ tạo ra **độ SÂU**.

*(Ngoại lai đáng ghi, không ảnh hưởng tổng: `bb7` giữ **1.186′/lượt** với 0,2 lượt/ngày — một tài xế bị
kẹt hẳn; 1,5% idle.)*

## 2. Số phản biện vòng 2 — mạnh hơn bản relay rất nhiều

### `D-M3-20` — nay có **arm NULL thật** và một fix **đã chứng minh khôi phục bit-identity**
`pb-02` dựng arm NULL đúng nghĩa (kênh **BẬT**, coin patch **luôn từ chối** ⇒ **đúng 0 can thiệp**),
**20 seed × 3 ngày × 90 actor**:

| đại lượng | SD nhiễu trôi-stream | so nền | **SD nhiễu / SD tổng quan sát** |
| --- | --- | --- | --- |
| `rest_min_total` | **157,5′** | 4,20% | **1,12** |
| `work_span_p90` | **22,4′** | 5,03% | **1,22** |
| payout đội | **318.718đ** | 1,37% | **1,05** |

⇒ **Nhiễu trôi-stream MỘT MÌNH giải thích (thực tế hơi vượt) TOÀN BỘ độ phân tán của Δ post-FIX**, và cả
ba điểm ước lượng của `UPDATE-142` (+10,9′ · −2,9′ · −35.954đ) nằm **sâu trong một SE của nhiễu**.
Thêm: arm A = **0 draw ở 20/20 seed** · fingerprint **A ≠ B_null ở 38/40** ngày-arm · và
**A == B_fix ở 60/60** ⇒ **fix khôi phục bit-identity**, tức cycle này **đã được de-risk trước khi làm**.
`pb-01` bổ sung độ lớn ở arm thật: coin=NEVER cho **−1.625.279đ / −34 cuốc / +519′ rest** (seed 7000) =
**1,2–2,4% payout đội**, **cùng bậc hoặc lớn hơn** Δ đang được báo là "hiệu ứng".

### `D-ADV-02` — có **phương án sửa THỨ BA**, tốt hơn cả hai phương án của tôi
| bản sửa | còn nói được | tác dụng phụ |
| --- | --- | --- |
| `W_END` (bản **nguyên văn tôi viết**) | 12/88 = **13,6%** | mất ~86% lượt nói, phần lớn **vô căn** |
| `W_NOW` (bản tôi "sửa lại") | 46/88 = 52,3% | 🔴 **tắt một lan can sức khoẻ** đang chặn **36,0%** lượt gọi |
| **`cổng-HẸP`** (dùng `_points_possible` trên cửa sổ kéo làm **cổng một chiều**) | **72/88 nguyên vẹn** | **cắt đúng 18,2%** lượt vô căn |

⇒ **Cả hai phương án của tôi đều thua.** Ghi vào kế hoạch: dùng **`cổng-HẸP`**.
Thêm một lỗi mới: **rò nửa đêm** — `shift_end = 1440 → start_h = 0.0` ⇒ walk báo 8,41h/207,2 điểm **của
NGÀY MAI**; quyết định nói/im **không đảo** (điểm giờ đầu = 0) ⇒ **rò SỐ/LÝ DO, không rò quyết định**.

### `D-ADV-03` — refutation nay có **giá bằng số**
Đổi đích deadhead theo cầu: **88,0%** lượt bị đổi · **+512,6 km/ngày (+95% nền)** · **+1.290 phút-đội
không-được-chào** (cận dưới; ước thực ~2.300′) · **+821 điểm-SOC ≈ +8 lượt đổi pin**. Đối chiếu:
`station_choice` chỉ thêm **+98,9** empty-min/ngày **và đã FAIL** ⇒ kênh này bơm **13–23× nhiều hơn**,
trong khi "cầu nhìn thấy" chỉ tăng **+8,2–10,9%**. **Đóng vĩnh viễn** là quyết định đúng.

## 3. 🔴 ~~ĐÍNH CHÍNH~~ → **RÚT LẠI ĐÍNH CHÍNH NÀY** (chi tiết ở `UPDATE-173`)

> **Bản gốc (SAI, giữ để đối chiếu):** *"Tôi viết **65,3% cuốc trả ngoài lõi**… Đo lại: **56,1–56,5%**
> lượt TRẢ KHÁCH ra ngoài lõi. 65,3% (chính xác 64,65%) là mức ĐƠN SINH — hai đại lượng khác nhau."*
>
> **🔴 RÚT LẠI 2026-08-07.** Tôi đã **tin số 56,1–56,5% của agent** rồi đi "sửa" một con số **ĐÚNG** của
> repo. **Tôi tự đo (5 seed, arm A):** đơn sinh drop ngoài lõi **64,4%** (3.883/6.029) · cuốc hoàn thành
> (`trip_rated`, log tại `order.drop_cell`) **64,6%** (2.329/3.608). **Cả hai khớp** `UPDATE-083`
> (**65,3%**, α=0,4 — `drop_demand_alpha` hiện vẫn 0,4) ⇒ **65,3% KHÔNG SAI**. Số **56,1–56,5%** của
> `pb-07` là số tôi **KHÔNG tái tạo được** ⇒ **không được trích** cho tới khi ai đó tái tạo.
> Đây đúng bài học `verify-favourable-claims-hardest`: **"tác tử báo" ≠ "tôi đo"**.
>
> ⚠ Việc rút lại này **KHÔNG lay chuyển** kết luận BÁC `D-ADV-03` — refutation đó đứng trên **giá của
> deadhead** (+512,6 km/ngày = +95% nền), không đứng trên con số 65,3%.

## Kiểm chứng

- F5: instrument `behavior.consider_relocate` (⚠ namespace `behavior` — bẫy F4), **cổng nhiễu-loạn XANH**;
  tổng idle 15.310′/ngày **khớp** sổ của rc-03 ⇒ pipeline không lệch.
- Số vòng 2 đọc từ **artifact trên đĩa** (7/7), không phải relay.
- **Chưa kiểm chứng:** tôi **chưa tự chạy lại** arm NULL của `pb-02` (tin artifact + evidence của nó);
  nếu dùng số đó để ra quyết định lớn thì nên tự dựng lại. `pb-04` "cổng-HẸP" tôi **chưa tự kiểm** —
  phải kiểm khi thi hành Cycle B.
- Suite: **không chạy** — 0 dòng code sản phẩm/sim đổi.

## Visual
`NOT_APPLICABLE`.

## Adversarial self-review / flaws found

1. **F1 của tôi đo sai đại lượng** — "độ rộng lưu vực" nghe đúng nhưng không phải thứ sinh ra phút idle.
   F5 cho thấy lệch **20×** ở số lượt vào. Bài học bổ sung: **trước khi tin một metric, hỏi nó có phải
   là đại lượng SINH RA hiện tượng không.**
2. **Ba lần liên tiếp phương án sửa của tôi bị bác** (`D-ADV-02` W_END → W_NOW → cả hai thua `cổng-HẸP`;
   `D-ADV-01` fix TTL là no-op; `D-ADV-03` bị đóng). ⇒ Từ nay: **đề xuất cách sửa cũng phải qua phản
   biện như đề xuất phát hiện**, không được coi "biết bug thì biết fix".
3. Con số **65,3%** tôi lấy từ comment config mà **không kiểm nó đo gì** — đúng họ lỗi *"tài liệu sai nằm
   trong nguồn sự thật"* mà tôi vừa tự sửa ở `choose_station` hôm qua. Đã đính chính.
4. Câu `UNRESOLVED` **đã giải**, nhưng phần *"vì sao lượt vào chênh 20× so với dự đoán tĩnh"* thì tôi
   **không** truy tiếp — nó không cần cho quyết định nào đang chờ. Ghi rõ là **chủ động dừng**, không
   phải bỏ sót.

## ⏳ Nhắc PENDING-REVIEW

**V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13 ·
**amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
