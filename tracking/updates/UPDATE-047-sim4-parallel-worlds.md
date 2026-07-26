# UPDATE-047 — SIM-4 "Parallel worlds": máy đo A/B + mở rộng kênh tác động

Ngày: 2026-07-26 · Track: **A (SIM overhaul)** · Phase: **SIM-4 / 5**
Chỉ thị: `DIRECTIVES-2026-07-24.md` §5.6 · Cường chốt 2026-07-26: làm **cả** máy đo lẫn mở rộng kênh
Tiếp nối: UPDATE-044 (`9de4074`) · 045 (`aa58998`) · 046 (`4cea652`)

## 1. Phát hiện dẫn đường (đo trước khi code)

`policy.day_bonus()` trả **0** khi `acceptance < bonus_min_acceptance`, **bất kể tài xế chạy bao
nhiêu điểm**. Config pilot đặt ngưỡng **0.85**, trong khi P4 tân binh có `accept_base = 0.80`
⇒ **tân binh bị loại khỏi toàn bộ thưởng ngày**. Đúng như SIM-2 đo được: P4 và P1 nhận **0đ**,
còn P2/P3/P5/P6/P7 (accept ≥ 0.90) nhận 30-60k.

⇒ Kênh advice giá trị nhất **không phải** xếp lịch nghỉ (S2), mà là cảnh báo *"tỷ lệ nhận của anh
dưới ngưỡng đủ điều kiện thưởng"*. Đây là **sự thật policy**, tác động ở **mức TỶ LỆ** — không phải
"nhận cuốc cụ thể này" (giữ đúng ranh giới CLAUDE.md §5).

## 2. Đã làm gì

- **`src/gsm_sim/parallel.py` (MỚI)** — máy đo: `run_pair` (A/B **chung seed** ⇒ chung đơn hàng/
  thời tiết/tắc đường), `compare` (**hiệu theo cặp** + **CI 95% bootstrap**), `run_ladder`
  (đo **thang bậc** để biết kênh nào tạo giá trị), guardrail hệ thống.
- **3 kênh tách bật/tắt RIÊNG** (`advice.channels`): `shift_plan` (S2, từ SIM-3) ·
  **`accept_lift`** (MỚI) · **`shift_extend`** (MỚI).
- `Actor.accept_lift` + `effective_accept_base` (có **trần 0.98**). Lift chỉ đổi **xác suất**,
  không đổi **số lần rút** ngẫu nhiên ⇒ CRN nguyên vẹn.
- **`scripts/run_parallel.py`** — chạy lại phép đo bất cứ lúc nào, in Δ + CI + `n_pos`.

## 3. KẾT QUẢ (30 seed, tài xế P4, hiệu theo cặp + CI 95% bootstrap)

| Bậc kênh | Δ payout | CI 95% | Δ thưởng | Δ cuốc | Δ accept |
|---|---|---|---|---|---|
| `s2_only` | **+0đ** | [0, 0] | 0 | 0 | 0 |
| `+accept_lift` | **+32.276đ** ✳ | [+8.255, +58.480] | +16.000 ✳ | +1.47 | +0.11 ✳ |
| `+shift_extend` (all) | **+42.471đ** ✳ | [+16.614, +70.662] | +21.000 ✳ | +1.87 ✳ | +0.12 ✳ |

✳ = CI không chứa 0.

**Ba điều phải đọc kèm, nếu không sẽ hiểu sai:**

1. **`s2_only` = ĐÚNG BẰNG 0** trên cả 30 seed, mọi metric. Đây là **xác nhận định lượng** cho
   `F-SIM3-A`: kênh xếp lịch của S2 gần như luôn trả `ONLINE` (= không can thiệp) nên **không đóng
   góp gì**. Giá trị đến **toàn bộ** từ kênh mới.
2. **`shift_extend` mua thêm tiền bằng THÊM GIỜ, không phải bằng hiệu quả.** Online +41 phút
   (có ý nghĩa). Xét **payout/giờ**: `accept_lift` **+21,5%** còn `all` chỉ **+19,3%** — tức là
   hoãn kết ca **làm giảm** hiệu suất giờ. Nếu chỉ nhìn tổng payout sẽ kết luận sai rằng
   "bật thêm kênh thì tốt hơn".
3. **Chỉ 16/30 (và 18/30) seed có Δ dương.** Mean dương nhưng **phân phối lệch**: thắng lớn ở vài
   ngày (chạm mốc thưởng), thua nhỏ ở nhiều ngày. Advice này là **một canh bạc**, không phải
   "ngày nào cũng lợi" — tuyệt đối không được quảng cáo với tài xế như điều chắc chắn.

**Guardrail:** Δ `served_rate` **không có ý nghĩa** ở cả hai bậc ⇒ advice cho 1 tài xế **không làm
xấu hệ thống**. Đạt yêu cầu spec §6.

## 4. Bug/phát hiện mô hình trong cycle

> ⚠️ **ĐÍNH CHÍNH 2026-07-26 (UPDATE-048): mục SIM-4-A dưới đây SAI vì suy rộng từ 1 seed.**
> Đo lại 30 seed: ngưỡng được chạm **27/30 lần** ngay ở `lift_max=0.15`; nhóm KHÔNG chạm
> (3 seed) có Δpayout **+18.207đ**, tức **không có bằng chứng** tuân thủ nửa vời gây hại.
> Bảng dưới là **một seed cá biệt**. Kết luận đúng nằm ở UPDATE-048.

**PHÁT HIỆN SIM-4-A (ĐÃ BỊ BÁC BỎ) — giả thuyết vách đá, chỉ đúng trên seed 1000:**
Quét trần lift trên seed 1000:

| `lift_max` | eff. base | realized accept | ≥0.85? | thưởng | payout |
|---|---|---|---|---|---|
| 0.00 | 0.800 | 0.7895 | không | 0 | **214.400** |
| 0.10-0.15 | 0.90-0.95 | 0.8235 | không | 0 | **180.468** ⚠️ |
| 0.19+ | 0.980 | 0.9333 | **CÓ** | 30.000 | 209.236 |

Nâng tỷ lệ **nhưng không chạm ngưỡng** ⇒ tài xế nhận thêm cuốc rẻ, chiếm chỗ cuốc tốt, **mất 34k
mà không có thưởng bù**. Thưởng theo ngưỡng là **được ăn cả ngã về không**.
⇒ **Quy tắc sản phẩm rút ra:** chỉ khuyên nâng tỷ lệ khi tài xế **thực sự với tới** ngưỡng; khuyên
nửa vời là **có hại**. (Chưa cài thành điều kiện chặn — xem F-SIM4-B.)

**PHÁT HIỆN SIM-4-B — khuyên giữa ngày là quá muộn.** Tỷ lệ nhận là **luỹ kế cả ngày** nên các lần
từ chối đầu ca **không gỡ lại được**. Bản đầu chỉ khuyên sau 5 offer (phản ứng) ⇒ chỉ bò 0.79→0.8235.
Đã đổi sang **phòng ngừa từ đầu ca**, ước lượng bằng `accept_base` (= dữ liệu **lịch sử** của tài xế,
thực tế đọc từ `driver_statistic_daily`) — **không phải** thông tin tương lai.

**Bài học phương pháp:** trên **seed 1000** kênh này cho Δ **−33.932đ**; trên **30 seed** cho
**+32.276đ**. Một seed đã suýt dẫn tới kết luận ngược hoàn toàn — đúng lý do harness bắt buộc ≥30 seed.

## 5. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/parallel.py` | **TẠO** — run_pair/compare/bootstrap CI/run_ladder/guardrail |
| `src/gsm_sim/advice_bridge.py` | sửa — 3 kênh tách biệt + `check_bonus_gate` + `check_shift_extend` |
| `src/gsm_sim/entities.py` | sửa — `accept_lift`, `effective_accept_base`, `shift_extended_min` |
| `src/gsm_sim/behavior.py` | sửa — dùng `effective_accept_base` |
| `src/gsm_sim/world.py` | sửa — gọi 2 kênh mới + 2 event |
| `configs/pilot_dongda.yaml` | sửa — `advice.channels` + tham số lift/extend |
| `scripts/run_parallel.py` | **TẠO** |
| `tests/test_parallel_worlds.py` | **TẠO** — 12 test |

## 6. Kiểm chứng

- **Full suite: 432 passed, 5 skipped** (trước 420).
- **CRN đúng**: cùng seed ⇒ **cùng danh sách đơn** hai nhánh (test riêng). Không có cái này thì
  mọi Δ là rác.
- **Cổng an toàn**: tắt hết kênh ⇒ B ≡ A **từng con số**, cả tài xế lẫn hệ thống.
- **Thống kê**: test bootstrap phát hiện đúng cả trường hợp **có** và **không có** hiệu ứng
  (chống máy đo bịa ra hiệu ứng).
- **Advice không rò sang tài xế khác** (`coverage=single`).
- **Trần lift** được tôn trọng; không khuyên người đã đạt ngưỡng.

## 7. Adversarial self-review / flaws found

1. **Đọc mean mà bỏ qua phân phối** — đã chặn: báo `n_positive` và nói rõ "canh bạc". ✅
2. **Nhầm 'thêm tiền' với 'hiệu quả hơn'** — đã tách `payout/giờ` và chỉ ra `shift_extend` làm
   *giảm* hiệu suất giờ. ✅
3. **Kết luận từ 1 seed** — đã chứng minh bằng ví dụ thật (seed 1000 cho dấu NGƯỢC). ✅
4. **Guardrail chỉ giả định** — đã ĐO (served/others_payout/swap_wait). ✅
5. **Ranh giới sản phẩm** — advice ở mức TỶ LỆ, không nhắm đơn cụ thể; ngưỡng lấy từ
   `PolicyBundle`, không bịa số. ✅

**FLAW ghi nhận (không che):**

- **F-SIM4-A (CAO → chặn kết luận rộng) — mới đo trên MỘT tài xế P4 của MỘT config.** Chưa quét
  các archetype khác, chưa quét độ nhạy theo `adherence` (`D-SIM-04`) hay theo ngưỡng
  `bonus_min_acceptance`. **Không được suy rộng** "advisor giúp +32k" cho mọi tài xế.
- **F-SIM4-B (CAO) — chưa cài điều kiện chặn lời khuyên có hại.** Đã CHỨNG MINH tuân thủ nửa vời
  gây lỗ, nhưng bridge vẫn khuyên bất cứ khi nào acceptance < ngưỡng, **kể cả khi không thể với
  tới**. Cần điều kiện khả thi (kiểu S1 `bonus_feasibility`) trước khi đưa kênh này ra thật.
- **F-SIM4-C (TB) — `accept_lift_step/max` là ASSUMPTION.** Trần 0.15 khiến tài xế **không** chạm
  ngưỡng (thấy ở bảng vách đá); 0.19 thì chạm. Con số này quyết định dấu của kết luận nên **phải**
  hiệu chỉnh bằng dữ liệu thật, không để mặc định quyết hộ.
- **F-SIM4-D (TB) — baseline "tân binh nhiều thưởng" vẫn CHẶN** bởi `Q-01`/`D-SIM-02`. P4 ở đây là
  tân binh **theo mô hình hiện có**, chưa phải hồ sơ tân binh thật của GSM.

## 8. Docs cập nhật kèm theo

`specs/simulation/00-sim-overhaul-master.md` (SIM-4 DONE) · `tracking/TODO.md` ·
`tracking/DEFERRED.md` (F-SIM4-A/B/C) · `tracking/PENDING-REVIEW.md` (V-05).

## 9. Visual review

**Status: `DEFERRED` (V-05)** — Cường đang hoãn check. Xem bằng CLI:
`uv run python scripts/run_parallel.py --seeds 30`. Tab dashboard cho A/B **chưa làm** trong cycle
này (ưu tiên máy đo + tính đúng đắn thống kê); ghi vào follow-up.

## 10. Follow-up

- **F-SIM4-B**: cài điều kiện khả thi trước khi khuyên nâng tỷ lệ — **nên làm trước SIM-5**.
- Quét độ nhạy: archetype khác, mức adherence khác, ngưỡng policy khác.
- Tab dashboard ⚖️ cho A/B (chưa làm).
- **SIM-5**: bộ metric chung + regen 13 bảng `l1r` từ sim mới.
