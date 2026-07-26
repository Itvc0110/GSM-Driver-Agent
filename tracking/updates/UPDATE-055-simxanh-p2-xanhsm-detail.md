# UPDATE-055 — SIM-XANH Phase 2: chi tiết XanhSM — rating · tân binh (Q-01) · mission

Ngày: 2026-07-26 · Track: **A (SIM-XANH)** · Tiếp nối UPDATE-054 (`fac5e58`)
Chỉ thị Cường: *"làm nó thật chi tiết về state, actors, action, bám đúng những cái mà chúng ta
đã plan"* — ba mảnh này đều là bảng L1R thật đang bị sinh giả ở tầng data hoặc chưa có trong sim.

## 1. Rating TRONG sim (bảng `driver_statistic_daily` cột rating)

- Sau mỗi `dropoff`: khách chấm sao với p=0.75 (`p_rated`, ASSUMPTION); phân phối sao theo
  **chất lượng archetype** (P3 top 5★ 88% · P4 tân binh 68% — ASSUMPTION có lập luận, config).
- Event `trip_rated` + counter trên Actor (reset ngày). **BIKE trong data đọc counter sim**;
  car/rto giữ gauss (không có sim). Trước đây bike cũng gauss — hai tầng kể hai chuyện.
- **RNG stream RIÊNG** (`seed ^ 0x5A7E5`): chèn vào stream hành vi sẽ dịch chuỗi và làm trôi
  TOÀN BỘ hiệu chỉnh SIM-1/P1. Có test chứng minh: tắt rating không đổi bất kỳ metric thị
  trường nào.

## 2. Chương trình TÂN BINH — cấu trúc THẬT (Q-01 fetch, greensm.com)

| lớp | căn cứ | trong sim |
|---|---|---|
| `tenure_days` theo archetype | P4 = tân binh (5-60 ngày), khác 90-720 | sample stream dẫn xuất riêng; **+1 mỗi sáng** (multi-day) |
| Mốc **≥50 cuốc / 7 ngày đầu** | **THẬT** (điều kiện thưởng chuyển nền tảng) | đọc lịch sử ngày-đã-xong qua `DriverMemory` (không rò tương lai), trả **MỘT lần/đời** (`newbie_week1_paid`); tiền 500k **PROXY** |
| **Bảo lãnh doanh thu 90 ngày** | **THẬT** (số image-locked → PROXY sàn 350k/ngày) | settle cuối ngày: bù `(sàn − gross) × driver_share`, chỉ khi **online ≥ 6h** (chống lạm dụng) |
| Combo 810k + clawback <200 cuốc/tháng | **THẬT** | tham số đã vào config; cơ chế clawback theo THÁNG cần chuỗi ≥60 ngày — ghi `D-SIM-17` |

Event `newbie_guarantee_topup` / `newbie_week1_bonus` → payout + journey. **`D-SIM-02` mở khoá
ở mức mock-có-nguồn**; số thật vẫn chờ GSM (D-POL-05).

## 3. MISSION trong sim (nền cho solver S6 có kênh tác động)

- Catalog ngày trong config (3 mission MOCK: khung sáng/khung tối/cả ngày — cấu trúc mô phỏng
  "Nhiệm Vụ Tiếp Theo", research đợt 4).
- Đếm tiến độ deterministic tại `dropoff` (không RNG); chạm mốc → `mission_completed` +
  reward vào payout, **đúng một lần/ngày/mission** (test).
- **Data BIKE từ SỰ KIỆN sim**: `public_mission` (catalog sim), `public_mission_earn_history`
  (từng lần hoàn thành, timestamp thật), `public_user_mission_progress` (tiến độ ngày cuối
  quan sát); car/rto giữ rule-based. Multi-day: `mission_progress` reset ngày (danh sách reset
  tường minh).

## 4. Bảo toàn tiền nâng từ 2 → 4 nguồn

`payout = cuốc + thưởng ngày + mission + tân binh` — journey `income_curve` gom mọi sự kiện
tiền (t, amount) rồi sort-cộng-dồn; metrics tách `trip_payout/day_bonus/mission_reward/newbie`.
Test bảo toàn 4-nguồn trên MỌI actor (mở rộng BUG-SIM2-01).

## 5. Files

`configs/pilot_dongda.yaml` (3 khối mới, nhãn THẬT/PROXY/ASSUMPTION từng số) · `entities.py`
(counters + reset + tenure) · `archetypes.py` (tenure stream riêng) · `world.py` (3 hook:
trip_rated, mission, `_newbie_settle` ở cả 2 nhánh settle) · `multiday.py` (`newbie_week1_paid`)
· `journey.py` (tiền 4 nguồn) · `adapter_sim.py` (`_sim_driver_day` mở rộng + `_sim_missions`)
· `realdata.py` (BIKE rating/mission từ sim; car giữ rule-based) · `tests/test_xanh_detail.py`
(TẠO, 13 test) · `tests/test_journey.py` (contract 4 nguồn).

## 6. Kiểm chứng

- 13 test Phase 2 xanh; data tests + schema gate xanh; journey/multiday xanh.
- Smoke seed 42: **699 rating · 58 mission hoàn thành · 16 topup bảo lãnh** — cơ chế sống thật.
- **Không trôi hiệu chỉnh**: test tắt-rating-không-đổi-thị-trường; mission/newbie chỉ cộng
  payout (không feedback vào hành vi nhận đơn).
- 1 fix trong lúc làm: schema `public_mission_earn_history` đòi `count_order` integer —
  điền target mốc thay vì None.
- Full suite: chạy nền, số ghi ở commit.

## 7. Adversarial self-review / flaws found

1. **RNG discipline giữ nghiêm** — rating stream riêng, tenure stream dẫn xuất, mission/newbie
   deterministic. Có test chứng minh, không chỉ tuyên bố. ✅
2. **Tiền 4 nguồn** — bảo toàn kiểm mọi actor. ✅
3. **Trả-một-lần** — mission (ngày) và mốc tuần-1 (đời) đều có test chống trả kép. ✅

**FLAW ghi nhận:**
- **F-P2-A (TB)** — `newbie_week1_bonus` cộng vào ngày ĐẠT mốc nhưng nếu mốc đạt ở ngày có
  censor cuối ngày, event nằm sau `day_end_settle` log payout → thứ tự log có thể lệch nhẹ
  (không lệch TIỀN — bảo toàn vẫn xanh). Sev thấp, ghi để khỏi ngạc nhiên khi đọc log.
- **D-SIM-17** — clawback combo theo THÁNG chưa kích hoạt được trong chuỗi ngắn (<60 ngày);
  cấu trúc đã có, cần chuỗi dài + định nghĩa "tháng tenure" khi tài xế vào giữa kỳ.
- Số PROXY (500k mốc tuần-1, sàn 350k/ngày) **quyết định độ lớn** của các kết luận advisor về
  tân binh — khi GSM cho số thật phải thay và đo lại (nối vào D-POL-05).

## 8. Visual review

`DEFERRED` — gộp **V-09** (Phase 4 dashboard sẽ hiển thị rating/mission/newbie trên journey).
