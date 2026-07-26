# UPDATE-053 — D-SIM-13: hoàn thiện nhiều-ngày (B/C/D) + **review đối kháng 28-agent** + 2 bug thật

Ngày: 2026-07-26 · Track: **A** · Tiếp nối UPDATE-052 (`317a268`)
Cường yêu cầu: *"luôn double check lại trong phần lớn này, kiểm tra thật kĩ về test live nếu cần"*
⇒ cycle này có thêm **vòng review đối kháng đa-agent** (4 lăng kính × verify từng finding, 28 agent)
trên diff chưa commit, bên cạnh test + kiểm chạy thật.

## 1. Ba phần đã làm (theo plan B→C→D)

**B — `DriverMemory` nối vào solver S1.** `build_bonus_gap_input` ưu tiên
`memory.points_per_hour_avg` (lịch sử ngày trọn) thay vì ước lượng trong-ngày; ước lượng
acceptance đầu ca ưu tiên `memory.acceptance_avg` (số đo thật của CHÍNH tài xế) hơn
`accept_base` (tham số archetype). `bridge.memory` gán sau khi tạo World, chỉ chứa các ngày
**đã xong** ⇒ không rò tương lai. Không memory ⇒ y hệt đường cũ (baseline 1-ngày giữ nguyên).

**C — tuần reset đúng chu kỳ.** `DriverMemory.close_week()` + `weeks_hist`;
`week_offset` để ranh giới tuần **trùng tuần ISO** của bảng data (`_week_key` dùng Thứ Hai) —
nếu hai định nghĩa "tuần" lệch nhau thì S5 khoán tuần không join được với data.

**D — mockgen chuỗi liên tục.** `generate_day` tách thành `_tables_from_run()`;
`generate_days_continuous()` chạy `run_multiday` MỘT lần; `generate_realdata(continuous=True)`
mặc định. **Regen 90 ngày**: phân phối biên gần như không đổi (acceptance median 0.9091→0.9167,
completion/cancel/cuốc y nguyên) — đúng kỳ vọng, vì tính liên tục không nên đổi marginals.

## 2. Kết quả đo trung thực về "tính liên tục"

- **Danh tính bền qua 90 ngày** (cùng driver_id + khung ca), ID bản ghi không đụng nhau,
  schema 13 bảng pass, **BIKE 6/6 PASS 0 GAP** (verify 30 seed).
- **Autocorr lag-1 cuốc/ngày ≈ −0.04** — kỳ vọng plan là ">0 nhẹ" ⇒ **KHÔNG đạt**, và lý do là
  **cấu trúc, không phải bug wiring**: between-driver sd 3.88 > within 3.22 (danh tính CÓ tách
  tài xế), nhưng không có trạng thái HÀNH VI nào sống qua đêm (SOC hồi, mệt reset, advice tắt
  khi regen) ⇒ hiệu suất ngày-qua-ngày do ngoại sinh chi phối. Tính liên tục hiện tại =
  **danh tính + memory + kế hoạch**, chưa = **persistence hành vi** (ngày nghỉ, thói quen, ốm)
  → `D-SIM-16`.

## 3. REVIEW ĐỐI KHÁNG (workflow 28 agent): 24 finding xác nhận → đã xử lý

Triage: 24 finding gộp còn ~14 vấn đề riêng biệt (nhiều lăng kính bắt trùng). **Đã sửa ngay 11**,
**defer 3** (có mã DEFERRED). Đáng kể nhất:

| # | Finding | Xử lý |
|---|---|---|
| C1/C6 (CAO) | **Vòng lặp tự tham chiếu**: `acceptance_hist` ghi tỷ lệ ĐÃ-ĐƯỢC-LIFT rồi dùng làm ước lượng hành vi GỐC ⇒ advisor tưởng "bệnh khỏi", tự tắt lời khuyên phòng ngừa, dao động khuyên/im qua các ngày | ✅ chỉ ghi ngày **không bị can thiệp** (`accept_lift == 0`) + test |
| C3 | Tuần TRÒN cuối run không bao giờ đóng (days=7 ⇒ `weeks_hist` rỗng — S5 sẽ hụt đúng tuần cuối) | ✅ đóng cuối run khi tuần vừa tròn + test |
| C13 | Tuần memory (theo day_index) ≠ tuần ISO của bảng data ⇒ không join được trừ khi start là Thứ Hai | ✅ `week_offset` từ weekday ngày đầu + test lịch thật |
| C7/C12 | **Manifest nói dối**: `engine_commit: 317a268` nhưng data sinh từ cây CHƯA COMMIT — phá đúng mục đích của trường truy vết | ✅ `_git_commit()` gắn `+dirty`; regen lại SAU commit |
| C8 | Kế hoạch nghỉ CŨ dính mãi khi gặp ngày không idle | ✅ xoá kế hoạch khi ngày không idle + test |
| C5/C11/C14 | ID duy nhất xuyên ngày chỉ là XÁC SUẤT (`day_seed` 31-bit có thể trùng ⇒ trùng cả dòng ngoại sinh = hai ngày y hệt) | ✅ rehash quyết định luận tới khi hết trùng |
| C9 | Truthiness rơi rớt lịch sử 0.0 điểm/giờ (dữ liệu hợp lệ: "lịch sử không kiếm được điểm") | ✅ so `is not None` |
| C10/C20, C17, C18, C21, C22, C23, C24 | 7 lỗi chất lượng TEST: mutate fixture module-scope · test liên tục VACUOUS (driver_id chỉ là chỉ số) · skip-guard im lặng đúng lúc phải đỏ · tuần chỉ kiểm trips · assertion reset xác suất vô nghĩa · test SOC luôn-đúng-vật-lý · giả định DAYS<7 ngầm | ✅ sửa cả 7 — test giờ có răng |
| C4/C16 | `continuous=False` KHÔNG phải baseline A/B paired (lật cờ đổi cả seed lẫn RNG car/premium) | ✅ docstring nói thẳng; pairing thật → defer |
| C2 (defer) | Memory đổi việc CÓ/không rút coin adherence ⇒ reorder dòng `bridge.rng` dùng chung — so sánh memory-on/off lẫn hiệu ứng thông tin với xáo coin | → **D-SIM-14**: RNG adherence theo (actor, ngày, lần hỏi) thay vì stream tuần tự |
| C15 (defer, pre-existing) | Ledger `day_bonus` của actor còn online cuối ngày bị đóng dấu 00:00 NGÀY SAU ⇒ mis-bucket trong dataset liên tục | → **D-SIM-15** |

## 4. BUG-DSIM13-02 — lộ ra khi VIẾT TEST cho finding C19, kèm **đính chính UPDATE-051**

C19 chỉ ra nhánh `memory.acceptance_avg` chưa có test. Viết test thì lộ bug thật:
`_advice_would_help` check "đã đạt ngưỡng" bằng `actor.acceptance_rate` THÔ — property này trả
**1.0 khi chưa có offer nào (0/0)** ⇒ **đầu ca luôn bị chặn nhầm** là "đã đạt ngưỡng", giết đúng
lời khuyên **phòng ngừa đầu ca** (loại giá trị nhất — PHÁT HIỆN SIM-4-B). Fix: dùng cùng ước
lượng đã chọn (lịch sử/base).

**Hệ quả — phải đính chính UPDATE-051:** đo lại 30 seed sau fix, `accept_lift` trở về **đúng
+32.276đ / 16-30 n_pos** (trùng từng đồng với thời D-SIM-05). Tức mức sụt +20.473 và câu chuyện
"advisor im lặng 16/30 ca nhờ S1 lọc" của UPDATE-051 phần lớn là **artifact của chính bug này**,
không phải giá trị của việc nối S1. Giá trị thật của D-SIM-09 là **kiến trúc** (một nguồn sự
thật; ràng buộc completion có kiểm giữa ca) — không phải con số. Đã gắn banner đính chính vào
UPDATE-051 (không xoá bản gốc). Guardrail served_rate sau fix: không đổi có ý nghĩa.

## 5. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/multiday.py` | sửa — untreated-only history · close_week cuối run · `week_offset` · chống trùng day_seed |
| `src/gsm_sim/advice_bridge.py` | sửa — memory→S1 · `is not None` · **fix BUG-DSIM13-02** |
| `src/gsm_sim/entities.py` (từ UPDATE-052) · `src/gsm_core/mockgen/adapter_sim.py` | `_tables_from_run` + `generate_days_continuous` + week_offset |
| `src/gsm_core/mockgen/realdata.py` | `continuous=True` mặc định · `_git_commit()+dirty` · docstring A/B trung thực |
| `scripts/regen_mock.py` | đọc manifest từ kết quả trả về |
| `tests/test_multiday.py` | +10 test mới (B/C/D + 6 test giữ fix review) — sửa 7 lỗi chất lượng test |
| `data/mock/realdata-v1/` | REGEN (chỉ commit manifest) |

## 6. Kiểm chứng

- **Baseline 1-ngày giữ nguyên** (seed 42/1000 giống hệt từng con số — memory=None không đổi gì).
- test_multiday + test_advice_bridge + test_parallel_worlds: **58 pass** sau fix.
- Verify thống kê 30 seed trên đường continuous: **BIKE 6/6 PASS, 0 GAP**.
- Regen so sánh cũ/mới: phân phối biên ổn định (bảng ở §1).
- Full suite: xem số cuối trong commit message (chạy nền khi viết UPDATE này).
- Review đối kháng: 28 agent, 24 finding confirmed, **0 finding bị bỏ qua không xử lý/không ghi mã**.

## 7. Adversarial self-review / flaws found

1. **Review đối kháng có giá trị THẬT**: C1/C6 (vòng lặp tự tham chiếu) và C7/C12 (manifest nói
   dối) là lỗi tôi không tự bắt được bằng test của chính mình. ✅
2. **Viết test cho chỗ thiếu coverage lộ ra bug thật** (BUG-DSIM13-02) — lần thứ 3 trong dự án
   pattern này lặp lại (BUG-SIM2-01, mission target_count, nay). ✅
3. **Hai lần đính chính chính mình trong 2 ngày** (UPDATE-047 vách đá, UPDATE-051 im-lặng-16/30)
   — cùng gốc: diễn giải số đo khi cơ chế chưa được test cô lập. Bài học ghi vào §4. ✅
4. **24/24 finding được "confirm"** bởi verifier — tỷ lệ 100% đáng ngờ (verifier có thể thiên về
   xác nhận). Tôi đã tự triage lại từng cái thay vì tin verdict; kết quả: tất cả đều thật nhưng
   mức nghiêm trọng không đều (7 là lỗi test-quality, 2 pre-existing). ✅

**FLAW còn lại (có mã):** `D-SIM-14` (RNG adherence theo khoá — C2) · `D-SIM-15` (ledger
timestamp — C15) · `D-SIM-16` (persistence hành vi — autocorr §2) · kế thừa `D-SIM-11/12`,
`Q-01`.

## 8. Visual review

`DEFERRED` — gộp vào **V-08** (bảng ngày-qua-ngày; nay thêm: xác nhận autocorr ≈ 0 có chấp nhận
được cho bản publish mock hay cần D-SIM-16 trước).

## 9. Follow-up

- Regen data SAU commit để manifest ghi đúng commit sạch (làm ngay trong cycle này).
- `D-SIM-14/15/16` như trên; S5 khoán tuần nay đã đủ nền tuần-ISO, còn chờ số thật (`Q-01`, `D-POL-01/02`).
