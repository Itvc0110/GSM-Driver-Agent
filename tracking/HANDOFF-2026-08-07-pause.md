# HANDOFF 2026-08-07 — PAUSE. Điểm vào cho session sau

> Đọc file này **ngay sau `CLAUDE.md`**, trước `BOOTSTRAP-SESSION.md`.
> Commit cuối: `b5bf83f`. Cây sạch, đã push. Không có tiến trình nền nào đang chạy.

---

## 0. ⛔ ĐỌC TRƯỚC KHI TRÍCH BẤT KỲ SỐ NÀO

**Tôi đã báo SAI một kết luận lớn hôm nay và đã rút.** Nếu bạn thấy các số này ở đâu đó
(kể cả trong commit message cũ `4d92ccc`, `d468c1d`), **chúng đã bị loại**:

⛔ `−15.290đ` · `+26.106đ` · `58,4%` · `17,82×` · `42,30%` · `−89.264đ`
⛔ Câu *"kênh positioning PHÂN PHỐI LẠI thu nhập"* / *"lấy của người bận"*

**Vì sao sai:** refuter dựng `NoisyWorld` (cùng seed, cùng đơn, **advisor TẮT HOÀN TOÀN**, chỉ
đổi khoá RNG nhiễu niềm tin `+7919`) và một thế giới **không có can thiệp nào** tái tạo **toàn
bộ** mẫu hình tercile với biên độ **lớn hơn** (−20.757/+25.338, cả ba SIG) trong khi ròng
**−769đ ns**. ⇒ **hồi quy về trung bình** thuần. Hồ sơ: `UPDATE-182`, `D-C9-PHAN-PHOI` = **ĐÃ LOẠI**.

✅ **Cái CÒN ĐỨNG** (arm null KHÔNG tái tạo được): **+17,27 chuyến/ngày · −16,27 đơn hết hạn ·
payout toàn đội +3.219đ SIG** (arm null: ~+1 chuyến, −769đ ns). Kênh positioning **có giá trị
thật ở mức hệ thống**; cái sụp là phân rã *"ai được ai mất"*.
✅ **`9d` vẫn đứng:** `B − SHUF` **ns mọi dòng** ⇒ **Hungarian matching đóng góp KHÔNG ĐO ĐƯỢC**.
Giá trị đến từ *đẩy tài xế rảnh tới ô được chọn*, không từ *chọn ai đi ô nào*.
⚠ `+6.016đ` (UPDATE-087) **không tái tạo được** với code hôm nay — tôi đo `+3.219đ` trên 30 seed
tươi. Trích phải kèm ngày đo + cảnh báo (`D-C9-6016`).

---

## 1. Ba luật tôi phải trả giá mới học được — áp ngay, đừng học lại

1. **Ghi caveat ≠ không đăng số.** Tôi *đã tự viết* *"chưa loại được xáo trộn ⇒ chưa được phép
   trích"* rồi **vẫn** đưa số vào `DEFERRED` sev CAO và báo miệng.
   ⇒ **Nếu vừa viết "chưa loại được X" thì con số đó Ở LẠI trong artifact** — không vào
   `DEFERRED`, không vào `UPDATE`, không vào lời báo, cho tới khi X bị loại.
2. **Placebo phương-sai-0 là placebo VÔ HIỆU.** `9c` bit-identical 30/30 nhìn như bằng chứng
   mạnh; thực ra nó **không thể** phát hiện hồi quy về trung bình. Placebo phải có **cùng loại
   nhiễu** với can thiệp, chỉ thiếu **thông tin**.
3. **Mọi ngưỡng cổng phải neo bằng một arm KHÔNG-CAN-THIỆP CÓ NHIỄU.** Ba metric agent đề xuất
   (`harmed_share`, `churn_ratio`, `delta_p10`) đều sụp vì arm null vượt ngưỡng **mạnh hơn**
   hiện trạng ⇒ chúng sẽ treo một thế giới không làm gì.
4. **Không sửa file khi một suite nền đang chạy** — `inspect.getsource` lệch offset, sinh ra một
   lỗi *trông như thật* (mất một lượt chạy 27 phút).
5. **Trước khi chia, hỏi: mẫu số có gồm ca CỐ Ý ngoài phạm vi không?** Hôm nay **2/5** finding
   định lượng của agent sai vì đúng cơ chế này (`coverage=single`; đếm cả đội car/premium
   40/150 = **đúng 26,7%**).

---

## 2. ĐÃ LÀM HÔM NAY (đã push, suite xanh đúng baseline)

| UPDATE | nội dung | trạng thái |
| --- | --- | --- |
| **178** | ĐA-07 tuyên bởi solver **mù thưởng** (git: tắt kênh 28/07, sửa band 06/08) · `soc_low` mồ côi · 6/6 kênh TẮT | `RESEARCH-DONE` |
| **179** | Audit 13 agent — giả thuyết **6 lớp của tôi bị bác xuống 3 cơ chế**; bắt được **2 cycle NO-OP** | `RESEARCH-DONE` |
| **180** | **Cycle 3** khoá config ma (**4→0**, **bit-identical 5/5 seed**) · **Cycle 4** vùng mù tầng 5 (**7→0**, `a_mean` **9→0**) · **Cycle 2** 5 bề mặt bằng chứng + chặn 2 sweep NO-OP | `DONE-CODE` |
| **181** | **Cycle 1 phần 1/2**: `A2` một công thức pha (cũ lệch **6/12** mốc, mới **0/12**) · `A11` · `M5` R-08 | `DONE-CODE` |
| **182** | ❌ **Rút kết luận C9** + kết quả phản biện 8 agent (**58/76 đứng vững**) | đính chính |

**Suite:** `tests/` **1189 passed / 2 failed** (đúng 2 lỗi có sẵn của Khánh) · `ui/backend/tests`
**216 passed**. Đã xác nhận 2 lỗi kia đỏ sẵn trên baseline bằng `git stash`.

**Bốn quyết định Cường uỷ quyền — đã quyết**, lập luận + **tiền đề có thể bác** ở
`tracking/PHAN-QUYET-2026-08-07-bon-quyet-dinh-uy-quyen.md`:
`Q-D` **phủ quyết** · `Q-B` S8 ngoài scope / S5 không thể kiểm / S6 hoãn · `Q-A` đo lại
`shift_plan` **sau khi xử lý `S2-3`** · `Q-07` giữ `k=6` tới hết Cycle 9, mặc định sau đó **k=8**.

---

## 3. VIỆC KẾ TIẾP — theo thứ tự, kèm ước lượng

### 🔵 Không vướng gate nào (làm được ngay)
| # | việc | ước | ghi chú |
| --- | --- | --- | --- |
| 1 | **Đọc hết 58 finding sống vững** | ~15′ | `research/audit/2026-08-07-phan-bien-sim-advisor/00-BAN-DO-FLAW.md`. Tôi mới đọc **3** cái của `pb5`. Còn **22** mục đường sản phẩm + **30** mục kênh ship |
| 2 | **Cycle 8** — cổng đột biến sentinel | ~45′ | thuần test; agent L2 đã có prototype chạy được (7 plugin, 1 đối chứng dương) |
| 3 | **Cycle 7** — `net_mean_all` một tên một công thức | ~30′ | G1 **đang đỏ ~24.000đ**; chỉ sim/scripts |

### 🔴 Chặn ở visual gate (cần Cường xem card)
| # | việc | ước |
| --- | --- | --- |
| 4 | **`PB5-02`** — thêm `thuong_tang_them = tier_vnd − bonus_at(points_now)`, đặt **nó** cạnh số giờ | ~30′ |
| 5 | **`PB5-01`** — cảnh báo sát ngưỡng bị chính verifier cùng file giết **246/246** | ~30′ |
| 6 | **Cycle 5** — card không được giấu lý do tốn tiền nhất (`A1`/`A7`/`A5`) | ~1h |

### ⏸ Có phụ thuộc
`Cycle 1` phần còn lại (`A3`/`A4`/`D-L4-M3` — đường **v2**, `ADVICE_V2_ENABLED=0` ⇒ tiên quyết
của việc bật v2, không gấp) · `Cycle 9` (còn `D-L4-B2b`/`M4`/`M1`) · `Cycle 10` (**sau** `S2-3`).

---

## 4. Ba phát hiện SẢN PHẨM sống sót — cơ chế tôi đã tự kiểm

- **`PB5-02`** ⭐ `policy.py:104-110` `bonus_at` là thang **THAY THẾ** (`bonus = tier_vnd`, không
  cộng dồn) nhưng `advisor.py:306` trưng `tier_vnd` **TỔNG** cạnh *"khoảng X giờ chạy nữa"*.
  Tài xế đã chốt mốc 30.000đ được nói *"còn với được mốc 60.000đ"* — phần thật sự đổi được là
  **30.000đ**. Agent đo **111/1.129 thẻ (9,83%)**; ⚠ **con số đếm tôi CHƯA đo lại**, cơ chế thì rồi.
- **`PB5-01`** `_cliff_item` để `numbers: []` cố ý, còn `_verify_item` đòi mọi số trong text phải
  trace về `numbers` ⇒ **246/246 bị giết**; **160** trong số đó rơi đúng lúc thẻ kia đang giục
  chạy thêm. Tầng chặn thứ hai: `cards.js` chỉ vẽ `items[0]`.
- **`PB5-03`** đường **v2** gọi thẳng `build_gi` ⇒ **đi vòng qua cổng đội xe DUY NHẤT** của repo
  (`startswith(("d-","r-"))` xuất hiện đúng **một** lần). **120/120** lượt car/premium sinh số
  thưởng bằng chính sách **bike**. Bán kính hôm nay **0** (v2 tắt) ⇒ **instance thứ TƯ** của
  khuôn **"LỚP 0"** (nợ ngủ đông sau công tắc mặc-định-tắt).

---

## 5. ⏳ ĐANG CHỜ CƯỜNG

`V-33` **đã rút** (không client nào gửi ca thật — `D-A2-CLIENT`).
**Còn chờ:** **V-32** (blocking) · **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục `V-` ·
Q-03/04/09/10/13 · **amendment ĐA-08** — gom ở `tracking/CAN-CUONG-DUYET-2026-08-06.md`
(phần **"CẬP NHẬT 2026-08-07"**).
**Mới:** `PB5-02` sửa văn bản thẻ ⇒ cần visual gate.
⏸ **Khánh:** 2 test đỏ + Flutter.
