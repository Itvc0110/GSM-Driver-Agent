# UPDATE-048 — D-SIM-05: điều kiện khả thi của lời khuyên **+ ĐÍNH CHÍNH kết luận "vách đá"**

Ngày: 2026-07-26 · Track: **A (SIM overhaul)** · Tiếp nối UPDATE-047 (`a7c2597`)

## 1. Vì sao

`D-SIM-05` (sev CAO) từ UPDATE-047: bridge khuyên nâng tỷ lệ nhận **bất cứ khi nào**
`acceptance < ngưỡng`, kể cả khi tài xế **không thể** với tới — mà UPDATE-047 cho rằng khuyên
nửa vời **gây lỗ 34k**. Mục tiêu: cài điều kiện khả thi trước khi làm SIM-5.

## 2. ĐÍNH CHÍNH — kết luận "vách đá" của UPDATE-047 KHÔNG ĐỨNG VỮNG

Trước khi kết luận điều kiện mới có tác dụng hay không, tôi kiểm lại **chính tiền đề** của
mình. Bảng "vách đá" ở UPDATE-047 §4 dựng trên **seed 1000** — đúng cái bẫy mà chính UPDATE đó
cảnh báo. Đo lại **30 seed** (`accept_lift`, tài xế P4):

| Nhóm | n | Δpayout TB | **median** | thưởng TB | số seed lãi |
|---|---|---|---|---|---|
| **Chạm** ngưỡng 0.85 | **27**/30 | +33.839đ | **+394đ** | 23.333đ | 14/27 |
| **KHÔNG chạm** | 3/30 | **+18.207đ** | +54.193đ | 0đ | 2/3 |

**Ba điều bị lật:**

1. Ngưỡng được chạm **27/30 lần** ngay ở `lift_max = 0.15`. Kịch bản "kẹt dưới ngưỡng" là
   **hiếm**, không phải thường lệ như UPDATE-047 mô tả.
2. Nhóm **không chạm** vẫn có Δpayout **dương** (+18.207đ) ⇒ **không có bằng chứng** tuân thủ
   nửa vời gây hại. Con số −34k là **một seed cá biệt**.
3. Phát hiện thật sự vững hơn: ngay cả khi **chạm** ngưỡng, **median chỉ +394đ** trong khi mean
   +33.839đ ⇒ mean bị **vài ngày thắng lớn kéo lên**; phần lớn ngày gần như **không đổi**.

⇒ Đã gắn cảnh báo đính chính vào UPDATE-047 §4 và sửa `tracking/TODO.md`. **Không xoá** bản gốc
— giữ lại để thấy sai ở đâu.

**Kết luận đúng về advice `accept_lift`:** hiệu ứng **dương và có ý nghĩa ở TRUNG BÌNH**
(+32.276đ, CI [+8.255, +58.480]), nhưng là **phân phối đuôi dày**: đa số ngày ~không đổi, thỉnh
thoảng thắng lớn nhờ chạm mốc thưởng. Đây là **xổ số có kỳ vọng dương**, không phải cải thiện
đều đặn — và phải nói với tài xế đúng như vậy.

## 3. Đã làm gì

`src/gsm_sim/advice_bridge.py` — chỉ khuyên khi **CẢ HAI** điều kiện đúng:

1. **`_acceptance_recoverable()`** — tỷ lệ nhận là **luỹ kế cả ngày**, nên phải hỏi *"còn gỡ kịp
   không?"*: với `o` offer đã nhận, `a` đã chấp nhận, `R` offer kỳ vọng còn lại (từ tốc độ của
   CHÍNH tài xế × thời gian còn lại), `p` = tỷ lệ đạt được khi lift kịch trần →
   `(a + p·R) / (o + R) ≥ ngưỡng`. `o = 0` (đầu ca) ⇒ luôn khả thi.
2. **`_tier_reachable()`** — sửa tỷ lệ mà **không đủ điểm** thì thưởng vẫn **0**; chiếu điểm tới
   cuối ca, chưa đủ lịch sử thì dùng ước lượng lý thuyết (đúng cách S1 làm).

Từ chối khuyên được **ghi lại** (`skipped_advice`) — không im lặng bỏ qua.

**Chỗ trống này là thật:** S1 `bonus_feasibility` đã có khung feasibility nhưng chỉ kiểm **TĨNH**
(`acceptance ≥ ngưỡng`). Nó nói *"không khả thi vì tỷ lệ đang thấp"* chứ không trả lời *"tỷ lệ này
còn gỡ được không?"* — hai câu hỏi khác hẳn với một tỷ lệ luỹ kế.

## 4. Kết quả: điều kiện mới **INERT** ở config hiện tại

Đo lại thang bậc 30 seed: **Δpayout, CI, n_positive, Δthưởng giống HỆT** trước khi thêm
(+32.276đ / [+8.255,+58.480] / 16-30 / +16.000). Điều kiện **không chặn lần nào**, vì:
- advice phát ở **đầu ca** (`o = 0`) ⇒ luôn "còn gỡ được";
- điểm chiếu cả ca luôn vượt mốc đầu (60 điểm).

**Báo đúng như đo được, không tô vẽ**: đây **không** phải nguồn cải thiện. Giá trị của nó là
**lan can** cho các trường hợp biên (ca ngắn, vào ca muộn, ngày đã hỏng) mà bộ 30 seed hiện tại
chưa chạm tới. Giữ lại vì đúng về nguyên tắc và chi phí gần bằng 0; **không** tính là thành tựu.

## 5. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/advice_bridge.py` | sửa — 2 điều kiện khả thi + `skipped_advice` |
| `configs/pilot_dongda.yaml` | sửa — `max_realized_accept` (0.93, **đo được**), `min_online_min_for_rate`, `trips_per_hour_est` |
| `tests/test_advice_bridge.py` | sửa — +5 test (đầu ca khả thi · quá muộn không khả thi · không chạm mốc · ghi lý do từ chối) |
| `tracking/updates/UPDATE-047-*.md`, `tracking/TODO.md` | **đính chính** kết luận vách đá |

## 6. Kiểm chứng

- `test_advice_bridge.py` + `test_parallel_worlds.py`: **32 passed**.
- Đo lại 30 seed → xác nhận điều kiện inert (số liệu §4).
- Phân tích 30 seed tách nhóm chạm/không-chạm ngưỡng → cơ sở cho đính chính §2.
- Cổng an toàn cũ giữ nguyên: tắt kênh ⇒ B ≡ A · CRN · không rò tương lai.

## 7. Adversarial self-review / flaws found

1. **Tự kiểm tiền đề của chính mình** — điều quan trọng nhất cycle này. Kết luận UPDATE-047 dựa
   trên 1 seed đã bị bác bỏ bằng 30 seed. ✅
2. **Không tuyên bố thành công giả** — điều kiện mới inert, đã ghi rõ thay vì gói vào "đã cài
   guardrail". ✅
3. **`max_realized_accept = 0.93`** là số **đo được** ở lift kịch trần, không phải ước đoán —
   nhưng nó **phụ thuộc config** (`accept_lift_max`). Đổi trần lift mà quên đổi số này thì điều
   kiện sẽ sai lệch ⇒ ghi thành `F-DSIM05-A`.

**FLAW ghi nhận:**

- **F-DSIM05-A (TB) — `max_realized_accept` và `accept_lift_max` phải NHẤT QUÁN.** Hiện là hai
  tham số độc lập; lệch nhau thì điều kiện khả thi đánh giá sai năng lực thật. Nên suy ra từ đo
  hoặc thêm kiểm tra nhất quán.
- **F-DSIM05-B (TB) — điều kiện chưa được kiểm ở vùng nó THỰC SỰ bind** (vào ca muộn, ngày đã
  hỏng). Có test đơn vị nhưng chưa có kịch bản end-to-end. Cần khi mở rộng sang archetype khác.
- Kế thừa: `F-SIM4-A` (mới 1 tài xế/1 config), `D-SIM-04` (adherence là giả định),
  `Q-01`/`D-SIM-02` (thưởng tân binh) vẫn chưa giải.

## 8. Visual review

`NOT_APPLICABLE` — không đổi giao diện; thay đổi hành vi đã đo bằng bộ 30 seed. V-05 (UPDATE-047)
vẫn đang chờ Cường.

## 9. Follow-up

- **SIM-5** — bộ metric chung + regen 13 bảng `l1r` từ sim mới (kế tiếp).
- F-DSIM05-A: ràng buộc nhất quán 2 tham số lift.
- Đưa `_acceptance_recoverable` ngược vào solver S1 (`gsm_core`) để advisor THẬT cũng có lý lẽ này.
