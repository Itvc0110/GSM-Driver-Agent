# UPDATE-050 — D-SIM-03 (phần 1): nối solver S7 + **chẩn đoán vì sao action-space hẹp**

Ngày: 2026-07-26 · Track: **A (sau lộ trình SIM-1..5)** · Tiếp nối UPDATE-049 (`4128cb7`)

## 1. Vì sao

`D-SIM-03` là giới hạn lớn nhất còn lại: **mới 1/9 solver** có kênh tác động vào hành vi actor.
Hệ quả đo được ở SIM-4: bậc `s2_only` cho Δ **đúng bằng 0** trên 30 seed ⇒ kết luận A/B đang
**đánh giá thấp advisor một cách hệ thống**.

Chọn **S7 `idle_reduction`** làm kênh thứ hai vì: (a) idle là bất hiệu quả LỚN NHẤT đã đo được
(148-378 phút/tài xế, util 0.26-0.34); (b) khuyến nghị của nó là *"dồn nghỉ/đổi pin vào khung
vắng khách"* — **không phải reposition**, nên không chạm ranh giới `D-004`.

## 2. Đã làm gì

- **Kênh `rest_window`** (`advice_bridge.py`): dựng `idle_reduction_input` (schema L3) từ idle
  tích luỹ theo giờ, **gọi solver S7 THẬT** (`idle_reduction.solve`) → `worst_window.hour`.
  `demand_by_hour` chuẩn hoá từ **belief cá nhân** ⇒ không rò tương lai (nguyên tắc SIM-3).
- `Actor.idle_by_hour` + `rest_deferred_min`; hook trong `world.py` **chỉ HOÃN, không bao giờ ÉP**
  nghỉ (nếu bản năng chưa muốn nghỉ thì không can thiệp).
- **Ba lan can an toàn**, mỗi cái một test riêng: SOC thấp · mệt thật · trần hoãn.
- Thêm bậc `rest_window` vào `CHANNEL_LADDER`; kênh **mặc định TẮT**.

## 3. KẾT QUẢ: kênh **INERT** — và lý do là phát hiện chính của cycle

Đo 30 seed: Δ **đúng bằng 0** trên mọi metric (idle, util, cuốc, payout), y hệt `s2_only`.
`battery_stranded` không tăng (A=0, B=0).

Truy nguyên trên tài xế đích (P4, seed 2000) — cả **3** lần nghỉ/đổi pin đều bị lan can chặn
**đúng**:

| # | sự kiện | đã online | nguyên nhân | lan can |
|---|---|---|---|---|
| 1 | `go_swap` t=552 | 174ph (0.36× ngưỡng mệt) | **SOC thấp** | hoãn = hết pin giữa đường ⇒ chặn ĐÚNG |
| 2 | `rest` t=676 (giờ 11) | 298ph (0.62×) | **bữa ăn** | S7 chỉ khung **giờ 10** — **ĐÃ QUA** ⇒ không hoãn được |
| 3 | `rest` t=860 | 482ph (1.00×) | **mệt thật** | sức khoẻ không phải biến tối ưu ⇒ chặn ĐÚNG |

**PHÁT HIỆN D-SIM03-A — S7 là solver HỒI CỨU, không phải sinh hành động thời gian thực.**
Nó phân tích idle **đã xảy ra** rồi nói *"anh chờ nhiều ở khung X"*. Với một actor đang chạy,
khung X **luôn nằm phía sau**. Lời khuyên của nó về bản chất là cho **ngày mai**, hoặc cho giai
đoạn **lập kế hoạch trước ca** — không phải cho quyết định lúc này.

**Điều này reframe cả D-SIM-03.** Lý do mới 1/9 solver được nối **không phải** vì lười, mà vì
**phần lớn solver là hồi cứu hoặc thông tin**: S3 (tổng kết ca), S7 (idle đã qua), S8/S9 (giải
thích phạt/bất thường), S5 (khoán TUẦN — sim mới 1 ngày), S6 (mission — sim chưa có khái niệm).
**S2 `shift_dp` là solver DUY NHẤT nhìn về phía trước.**

⇒ Mở rộng action-space thật sự cần một trong hai:
- **(a) biến thể forward-looking** của các solver (vd S7 dự báo khung vắng SẮP TỚI thay vì khung
  đã qua), hoặc
- **(b) sim NHIỀU NGÀY** — lời khuyên hồi cứu ngày N đổi hành vi ngày N+1. Đây cũng là điều kiện
  cần cho S5 khoán tuần.

**Không "vặn" lan can để kênh có số đẹp.** Cả ba lần chặn đều đúng về an toàn/thực tế; nới ra sẽ
tạo ra tài xế hết pin giữa đường hoặc chạy quá sức — đúng loại "số đẹp giả" spec §7.1 cấm.

## 4. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/advice_bridge.py` | sửa — `build_idle_reduction_input`, `rest_window_hour`, `should_defer_rest` |
| `src/gsm_sim/entities.py` | sửa — `idle_by_hour`, `rest_deferred_min` |
| `src/gsm_sim/world.py` | sửa — ghi idle theo giờ; hook hoãn nghỉ + event `advice_rest_window` |
| `src/gsm_sim/parallel.py` | sửa — bậc `rest_window` trong `CHANNEL_LADDER` |
| `configs/pilot_dongda.yaml` | sửa — `channels.rest_window` (TẮT), `rest_defer_max_min` |
| `tests/test_advice_bridge.py` | sửa — +6 test (3 lan can, không rò tương lai, ngưỡng notable) |

## 5. Kiểm chứng

- **Full suite: 452 passed, 5 skipped** (trước 446).
- **Cổng an toàn**: kênh tắt ⇒ World A giống hệt baseline seed 42/1000 từng con số.
- **Ba lan can có test riêng** (không chỉ là `if` trong code).
- **`battery_stranded` không tăng** khi bật kênh — bằng chứng lan can SOC hoạt động.
- **Guardrail hệ thống**: served_rate và `swap_wait_mean` Δ = 0 (kênh inert nên không thể hại).
- Đo 30 seed qua `run_ladder`, có bậc `rest_window`.

## 6. Adversarial self-review / flaws found

1. **Cám dỗ nới lan can cho kênh "có tác dụng"** — đã từ chối; ba lần chặn đều đúng. ✅
2. **Gọi solver thật thay vì tự cài lại lý lẽ** — kênh này gọi `idle_reduction.solve()`, không
   chép logic. ✅
3. **Kết luận "kênh vô dụng"** — đã truy nguyên từng lần chặn thay vì kết luận vội; hoá ra vấn đề
   nằm ở **bản chất hồi cứu của solver**, không phải ở kênh. ✅

**FLAW ghi nhận:**

- **F-DSIM03-A (CAO) — nợ kỹ thuật đã nêu tên: `check_bonus_gate` tự cài lại lý lẽ advisor**
  (so ngưỡng, tính khả thi) thay vì gọi solver **S1 `bonus_feasibility`**. Đúng lỗi "hai nguồn
  sự thật" mà tôi đang đi sửa ở chỗ khác. → `D-SIM-09`.
- **F-DSIM03-B (TB) — kênh `rest_window` hiện là hạ tầng CHƯA sinh giá trị.** Giữ lại vì đúng
  đắn và có lan can, nhưng **không được tính là thành tựu** cho tới khi có sim nhiều ngày hoặc
  biến thể forward-looking của S7.

## 7. Docs cập nhật kèm theo

`tracking/DEFERRED.md` (D-SIM-09, D-SIM-10) · `tracking/TODO.md` · `tracking/PENDING-REVIEW.md` (V-07).

## 8. Visual review

`NOT_APPLICABLE` — kênh inert, không đổi output nhìn thấy được. V-01..V-06 vẫn đang chờ Cường.

## 9. Follow-up

- **`D-SIM-09`**: nối S1 vào bonus-gate (xoá nợ hai-nguồn-sự-thật) — việc rõ ràng, nên làm sớm.
- **`D-SIM-10`**: sim **nhiều ngày** — mở khoá S3/S5/S7/S8/S9 (advice ngày N → hành vi ngày N+1)
  và là điều kiện cần cho khoán tuần. Đây là đòn bẩy LỚN NHẤT cho action-space.
