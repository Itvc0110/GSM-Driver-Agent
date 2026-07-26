# UPDATE-052 — D-SIM-10: **sim NHIỀU NGÀY** (advice ngày N → hành vi ngày N+1)

Ngày: 2026-07-26 · Track: **A** · Tiếp nối UPDATE-051 (`a45e44d`)
Cường yêu cầu riêng cho cycle này: *"luôn double check lại trong phần lớn này, kiểm tra thật kĩ
về test live nếu cần"* ⇒ có mục **§4 kiểm chứng chạy thật**.

## 1. Vì sao

UPDATE-050 chẩn đoán: **S2 `shift_dp` là solver DUY NHẤT nhìn về phía trước**; S3/S7/S8/S9 hồi
cứu, S5 theo tuần. Với sim MỘT ngày, lời khuyên hồi cứu **không có chỗ tác động** — kênh
`rest_window` (S7) inert hoàn toàn vì khung nó chỉ ra luôn nằm phía sau actor đang chạy.

Sim nhiều ngày mở đúng cơ chế các solver đó được thiết kế cho: **học hôm qua, áp dụng hôm nay.**

## 2. Đã làm gì

- **`src/gsm_sim/multiday.py` (MỚI)** — `run_multiday(cfg, seed, days)`:
  actor **sample MỘT LẦN** rồi `reset_for_new_day()` mỗi ngày. Sample lại mỗi ngày nghĩa là mỗi
  ngày một **nhóm người khác** ⇒ "học từ hôm qua" thành vô nghĩa.
- **`Actor.reset_for_new_day()`** — danh sách **tường minh** cái gì reset (không dùng kiểu "reset
  mọi thứ trừ…"), vì chỗ này sai được theo **cả hai chiều**.
- **`DriverMemory`** — lịch sử cuộn (accept/completion/điểm-mỗi-giờ/payout/cuốc) + tích luỹ TUẦN
  (nền cho S5) + `planned_rest_hour`.
- **S7 xuyên ngày**: cuối ngày N chạy `idle_reduction.solve()` trên idle **cả ngày** →
  `worst_window.hour` → ngày N+1 kênh `rest_window` dùng khung **biết trước** thay vì khung vừa trôi qua.
- `day_seed(seed, d)` — mỗi ngày cầu khác nhau nhưng **tái lập được**; A/B vẫn pair theo seed gốc.

## 3. Bug thật phát hiện trong lúc làm

**BUG-DSIM10-01 — mọi ngày dùng CHUNG một list `actors`.** Bản đầu truyền thẳng `actors` vào
`RunResult` từng ngày. Vì actor bị reset **tại chỗ**, `days[0].actors` sẽ phản ánh trạng thái
**ngày CUỐI** ⇒ mọi journey/metric theo ngày sai **im lặng** (không crash, không test nào đỏ).
Fix: `copy.deepcopy(actors)` làm ảnh chụp từng ngày + test `test_each_day_has_own_actor_snapshot`.

## 4. KIỂM CHỨNG CHẠY THẬT (không chỉ test đơn vị)

### L1 — bảng ngày-qua-ngày, d-30 (P4), 7 ngày

| ngày | cuốc | điểm | accept | payout | idle |
|---|---|---|---|---|---|
| 0 | 18 | 100 | 0.905 | 290.359đ | 135ph |
| 1 | 5 | 30 | 0.556 | 82.596đ | 297ph |
| 2 | 5 | 35 | 0.833 | 87.479đ | 320ph |
| 3 | 16 | 90 | 0.944 | 264.546đ | 38ph |
| 4 | 13 | 75 | 0.812 | 179.165đ | 200ph |
| 5 | 9 | 55 | 0.900 | 150.078đ | 220ph |
| 6 | 11 | 65 | 0.917 | 169.934đ | 233ph |

Điểm từng ngày `[100, 30, 35, 90, 75, 55, 65]` — **không cộng dồn** ⇒ reset đúng. Lịch sử cuộn
sau 7 ngày: accept TB **0.8382**, điểm/giờ TB **7.573**; tích luỹ tuần **1.472.211đ / 77 cuốc**.
Danh tính bền qua cả 7 ngày. **Biến động ngày-qua-ngày lớn (5→18 cuốc) là THẬT** — mỗi ngày một
bộ cầu khác.

### L2 — carry-over có tác dụng thật, không phải vỏ
7 ngày, cùng seed, `rest_window` tắt vs bật: payout **1.224.157đ → 1.248.077đ (Δ +23.920đ)**,
cuốc 77 → 78. **Khác nhau ⇒ cơ chế thật sự chạy.** (Nếu giống hệt thì tính năng chỉ là vỏ.)

### L3 — truy vết S7 xuyên ngày: **kênh HẾT INERT**

| ngày | event `advice_rest_window` |
|---|---|
| 0 | **0** (chưa có lịch sử — đúng thiết kế) |
| 1 | **1** (lý do: `defer_to_13h`) |
| 6 | **1** |

Đây là **xác nhận trực tiếp cho chẩn đoán UPDATE-050**: cùng kênh đó ở sim một ngày cho **0 event
tuyệt đối**; nay có event từ ngày 2 trở đi. Tuy vậy **số lần vẫn ít** (2/7 ngày) — xem F-DSIM10-A.

### L4 — không rò thông tin tương lai
Chạy **3 ngày** và **5 ngày** từ cùng seed: 3 ngày đầu **giống hệt từng metric**. Nếu hành vi
ngày sớm phụ thuộc ngày chưa xảy ra thì phép này sẽ lệch. Đã thành test tự động.

### L5 — chi phí
**16,8 giây cho 7 ngày** (~2,4s/ngày), tuyến tính theo số ngày. Chấp nhận được.

### L6 — đường 1 ngày KHÔNG bị đụng
`summarize()` + counter seed 42/1000 **giống hệt** baseline trước cycle.

## 5. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/multiday.py` | **TẠO** |
| `src/gsm_sim/entities.py` | sửa — `reset_for_new_day()`, `planned_rest_hour` |
| `src/gsm_sim/advice_bridge.py` | sửa — ưu tiên khung nghỉ đã lên kế hoạch từ hôm qua |
| `tests/test_multiday.py` | **TẠO** — 10 test |

## 6. Kiểm chứng

- **Full suite: 463 passed, 5 skipped** (trước 453).
- Reset kiểm **cả hai chiều**: cái phải reset đã reset, cái phải giữ vẫn giữ.
- `test_no_future_leak_across_days` — 3 ngày vs 5 ngày.
- `test_each_day_has_own_actor_snapshot` — chống BUG-DSIM10-01 quay lại.
- Bảo toàn SIM-2 (offer/tiền) kiểm ở **từng ngày**, không chỉ ngày đầu.

## 7. Adversarial self-review / flaws found

1. **Ảnh chụp actor** — BUG-DSIM10-01, loại lỗi im lặng nguy hiểm nhất; đã fix + khoá test. ✅
2. **Reset sai hai chiều** — dùng danh sách tường minh thay vì "reset mọi thứ trừ…". ✅
3. **Rò tương lai xuyên ngày** — rủi ro MỚI; đã có phép thử 3-vs-5 ngày. ✅
4. **Tự nghiệm thu bằng test mình viết** — vì thế làm thêm L1-L6 chạy thật, đọc số bằng mắt
   (Cường yêu cầu). L1 và L3 là hai chỗ test đơn vị dễ bỏ sót nhất. ✅

**FLAW ghi nhận:**

- **F-DSIM10-A (TB) — S7 hết inert nhưng vẫn hiếm (2/7 ngày).** Ba lan can an toàn (SOC/mệt/trần)
  vẫn chặn phần lớn. Cần soi xem còn dư địa hợp lệ nào không, **không được nới lan can**.
- **F-DSIM10-B (TB) — `DriverMemory` chưa nối vào `build_bonus_gap_input`.** Lịch sử cuộn đã có
  nhưng S1 vẫn nhận ước lượng trong-ngày. Nối vào là việc nhỏ, giá trị rõ.
- **F-DSIM10-C (TB) — tích luỹ TUẦN chưa reset theo tuần** (mới cộng dồn tuyến tính) và chưa nối
  S5. Chỉ đúng khi `days ≤ 7`. Phải sửa trước khi chạy chuỗi dài.
- **F-DSIM10-D (TB) — `mockgen` vẫn sinh 90 ngày ĐỘC LẬP**, chưa dùng `run_multiday`. Data hiện
  tại vì thế vẫn không có tính liên tục ngày-qua-ngày.

## 8. Visual review

`DEFERRED` (**V-08**) — cần Cường xem bảng ngày-qua-ngày (§4 L1) và xác nhận biến động
5→18 cuốc/ngày là hợp lý với thực tế.

## 9. Follow-up

- **F-DSIM10-B**: nối `DriverMemory` vào S1 (việc nhỏ, giá trị rõ) — nên làm ngay.
- **F-DSIM10-C**: reset tuần đúng chu kỳ trước khi nối S5 khoán tuần.
- **F-DSIM10-D**: chuyển `mockgen` sang `run_multiday` ⇒ data 90 ngày có tính liên tục thật.
