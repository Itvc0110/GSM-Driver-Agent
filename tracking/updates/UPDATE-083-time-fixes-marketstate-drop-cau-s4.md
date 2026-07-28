# UPDATE-083 — Sửa 3 lỗi thời gian · MarketState producer · điểm trả bám cầu · hồi sinh S4

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** bugfix (time) + feature (sim positioning stack) + research (chi phí thực)
- **TODO liên quan:** **T-045a** (b0/b0-D/b2/b3) · T-045b (research, chưa code) · T-046 (quy tắc 5)
- **Plan:** `binary-cuddling-twilight.md` đã duyệt + 2 quyết định planning (batch tick; đo cả hai
  mức ghi đè) + Cường chốt giữa phiên: *"sửa drop trước khi đo b4"*, *"nghiên cứu sâu chi phí"*.

## Tóm tắt

Chuỗi 4 khối, mỗi khối theo protocol reproduce → prove → failing test → narrow fix → mutation-proof:

1. **b0 — ba lỗi thời gian** (từ câu hỏi Cường *"có time mismatch ở đâu không"*).
2. **b2 — MarketState producer**: sim biết ai đang RỖI ở đâu và ai ĐANG TỚI đâu.
3. **b0-D — điểm trả khách bám cầu**: corr −0,222 → **+0,418** (α=0.4).
4. **b3 — hồi sinh S4**: kênh vị trí có TRẦN, gán theo lô Hungarian, batch tick 60′.

Kèm: hồ sơ chi phí thực `research/economics/driver-cost-structure-2026.md` (đã commit `e4d98af`)
và bộ nhớ phiên `tracking/OPEN-THREADS-2026-07-28.md`.

## 1. b0 — ba lỗi thời gian (commit `6fe6d48`)

| # | Lỗi | Mức độ | Chứng minh |
|---|---|---|---|
| A | nhãn bucket mất NGÀY (`% 24`) ⇒ `sorted()` của shift_dp đảo thứ tự lịch | **tiềm ẩn** — che bởi demand_field không có giờ 0 | repro tổng hợp: bucket `00:00` nhảy lên vị trí 0 |
| A′ | **bucket MA** sau `time.end_min` thổi phồng `B` ⇒ `_required_rest` | **thật — 48 lần/seed** | instrument 1 seed |
| A″ | `shift_extend` kéo ca quá lúc thế giới dừng (tới 1500′) | **thật — 9 lần/seed** | instrument 1 seed |

**Đính chính công khai**: tôi từng nghi *"số UPDATE-047 nhánh `all` đã nhiễm"* — **SAI**, đo
0/1197 lần hỏi solver bị đảo. Số cũ sạch, nhưng sạch **do tình cờ** (không có cầu ban đêm trong
config), không do thiết kế — vẫn phải sửa vì chỉ cần ai thêm ca đêm là lỗi sống dậy im lặng.

Fix: `_iso()` mang ngày thật + clamp horizon + clamp shift_extend theo `world_end_min`.
6 test (`test_advice_time_encoding.py`), **mutation-proof M1/M2/M3** — lượt chạy đầu còn tự bắt
được 2 test của tôi là lan can yếu (chạy trên pilot config nên "xanh vì không có gì để sai") ⇒
chuyển sang fixture thế giới 26:00.

Kèm b0-C: `derive_allocation_input(bucket_min=…)` — hằng cứng 30′ sẽ **cắt nửa trần trạm** cho
batch tick 60′ của b3; bắt được TRƯỚC khi viết consumer. 4 test, mutation-proof.

## 2. b2 — MarketState producer (commit `cdf9aec`)

`Actor.enroute_cell` (ENROUTE dùng chung 3 việc mà không ai ghi ĐÍCH) + `gsm_sim/market_state.py`
dịch World sống → `build_market_state`. Đường đón khách miễn trừ CÓ NHÃN (`ENROUTE_EXEMPT`) + test
quét source đỏ nếu ai thêm đường di chuyển mới mà quên. 11 test, mutation W1 (quên gán) và W2
(quên xoá khi tới nơi — tệ hơn: actor bị đếm "đang tới" vĩnh viễn) đều bị bắt.

## 3. b0-D — điểm trả khách bám cầu

**Vấn đề đo được**: corr(cầu, nơi trả) = **−0,226**; 10 ô cầu cao nhất nhận 30,3% lượt đặt nhưng
2,2% lượt trả; 82,3% trả ngoài lõi ⇒ deadhead 11,8% thời gian; **40,2% km toàn đội là chạy rỗng**.
Root cause: `_sample_drop` thuần khoảng-cách trên vùng 316 ô mà lõi chỉ 85 — MODEL GAP, không
phải bug.

**Fix**: hệ số cầu pha tuyến tính `m(c) = 1 + α·(w/w̄ − 1)` kẹp ≥ 0. **Cố ý khác** công thức luỹ
thừa trong preview đã duyệt: luỹ thừa với w=0 giết sạch ô buffer ở mọi α>0 (100% trả trong lõi —
sửa lố ngược). α=0 ⇒ trace **y hệt từng bit** (test canh).

**Quét 5 mức × 3 seed** (`research/audit/2026-07-27-current-state/20-sweep-drop-alpha.json`):

| α | corr | ngoài lõi | med km | served | km rỗng | deadhead |
|---|---|---|---|---|---|---|
| 0.0 | −0.222 | 80.9% | 3.22 | 0.791 | 40.5% | 636 km |
| **0.4 ←** | **+0.418** | **65.3%** | 3.14 (−2,5%) | 0.790 | 38.9% | 539 |
| 0.8 | +0.777 | 37.9% | 2.94 (−8,7%) | 0.809 | 36.9% | 353 |

Chọn **0.4** — giữa dải mục tiêu Cường duyệt (+0,3..0,5), quãng đường gần như không méo.
⚠ **Mọi baseline cũ lệch** — lần đổi nền thứ 4; b4 đo lại từ đầu.

## 4. b3 — hồi sinh S4 (kênh vị trí có trần)

Kiến trúc Cường chốt: **batch tick** — mỗi 60′, `_standby_planner` dựng MarketStateView → lọc
candidates (IDLE, được phủ, KHÔNG đứng ở ô còn trần — kéo người đã đúng chỗ đi là churn) → S4
Hungarian gán vào ô còn trần (preferred = ô gần nhất, ưu tiên người NHIỀU pin) → adherence rút
**một lần lúc gán** (không re-roll mỗi poll — lỗi D-SIM-14) → vòng idle chỉ ĐỌC `standby_plan`.

Cờ `advice.positioning_overrides`: `off` (mặc định) | `wait_only` | `wait_and_relocate`.
Vòng khép kín: follow ⇒ `pending_targets`/`enroute_cell` trừ ngay trần cho người hỏi sau.

8 test (`test_standby_capacity.py`): off = y hệt không-có-cờ (payout + số event) · trần là trần
(event tự mang bằng chứng `n_assigned ≤ capacity_left`) · dư ⇒ unassigned · mù cung ⇒ 0 lời khuyên ·
wait_only không đụng go_swap/rest/end (bài học REST) · safety flags đủ 5 tới tận event ·
deterministic. **Mutation S1 (bỏ trần) → 2 đỏ · S3 (ghi đè tất cả) → 1 đỏ · restore → 8 xanh.**

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `src/gsm_sim/advice_bridge.py` | sửa — `_iso`, clamp, cờ positioning, `standby_follow_draw` |
| `src/gsm_sim/{entities,world}.py` | sửa — `enroute_cell`, `_standby_planner`, hook idle, reloc_reason |
| `src/gsm_sim/market_state.py` | **tạo** — producer + `count_supply` |
| `src/gsm_sim/demand.py` | sửa — `_sample_drop` demand-blend, nối 2 call site |
| `src/gsm_core/features/allocation.py` | sửa — `bucket_min` tường minh |
| `configs/pilot_dongda.yaml` | sửa — `drop_demand_alpha: 0.4` + bảng quét; đính chính comment bucket_min |
| `tests/test_{advice_time_encoding,allocation_bucket_scaling,market_state_sim_producer,drop_follows_demand,standby_capacity}.py` | **tạo** — 6+4+11+4+8 = 33 test mới |
| `research/economics/driver-cost-structure-2026.md` · `tracking/OPEN-THREADS-2026-07-28.md` · DIRECTIVES §14 | **tạo/sửa** (commit `e4d98af`) |

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| từng khối TDD | đỏ trước → xanh sau; mutation M1-3/W1-2/S1,S3 đều bị bắt, restore xanh |
| suite giữa phiên (sau b0+b2) | **605 passed / 5 skipped** |
| suite sau b0-D+b3 | ⏳ đang chạy — suite trước đó 611 passed + 6 fail: **5 do tôi chạy mutation song song với suite nền (lỗi quy trình, đã ghi nhận: hai việc phải tuần tự)**, 1 là bug fixture thật của test alpha-zero khi 0.4 thành mặc định — đã sửa |
| quét alpha | 15 run, artifact `20-sweep-drop-alpha.json` |
| b4 (9 tiêu chí × 3 nhánh × 30 seed) | **CHƯA CHẠY** — bước kế tiếp; chưa được phép kết luận kênh vị trí có ích hay không |

## Visual verification

- **Status:** `BLOCKED` → cần Cường xem trước khi coi cycle là reviewed. Khu Mô phỏng →
  Replay seed 1000: (1) phân bố điểm TRẢ khách nay bám khu đông (tab Bản đồ H3); (2) bật
  `positioning_overrides: wait_only` xem event `standby_alloc`/`standby_followed` trên timeline.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

1. **Lỗi quy trình tự gây**: chạy full suite nền SONG SONG với mutation testing trên cùng file ⇒
   5 fail giả. Quy tắc mới: suite và mutation tuần tự, không chồng.
2. **Test alpha-zero của tôi gãy khi đổi mặc định config** — fixture "config không có khoá" phải
   DỰNG bằng cách xoá khoá, không dùng pilot config trực tiếp. Đã sửa + ghi lý do trong test.
3. **Công thức khác preview đã duyệt** (pha tuyến tính vs luỹ thừa) — có lý do (ô w=0 chết sạch),
   ghi rõ trong docstring + test canh ô buffer còn sống. Nếu Cường muốn đúng công thức cũ: một
   dòng đổi, nhưng phải chấp nhận 100% trả trong lõi.
4. **Adherence standby chưa có test riêng** (draw đúng một lần/lượt gán — mới chỉ đúng theo cấu
   trúc code, chưa có test chống re-roll). Ghi nợ vào T-046 ứng viên.
5. **Candidates loại người đứng ở ô còn trần** — quyết định thiết kế của tôi (chống churn/veto km
   rỗng), chưa được duyệt riêng. Hệ quả: kênh bảo thủ hơn, có thể bỏ lỡ gán "tốt hơn hẳn ở xa".
6. **`test_excess_candidates` phụ thuộc config hiện tại** (đòi PHẢI có lúc dư candidate) — đúng ở
   pilot 90 actor, có thể gãy oan ở config thưa. Chấp nhận, vì "không bao giờ dư" ở pilot là
   tín hiệu trần không ràng buộc.
7. **b4 chưa chạy** — mọi kết luận về giá trị kênh vị trí đều CHƯA CÓ. HHI/Gini/km rỗng/đổi pin
   là veto; payout dương mà veto hỏng thì KHÔNG bật.

## ⏳ Nhắc PENDING-REVIEW (quy ước sau mỗi UPDATE)

`V-01..V-16` chưa ai xem (mới nhất: V-15 BUG-S2-PARAMS, V-16 fare parity gate — đổi số từ V-11
remote). Quyết định treo: Q-03 corpus Khánh · Q-04 UX proposal · Q-07 dispatch H3 (đang làm theo
(c)). B-02 ARCH-VERSION vẫn mở — chặn ĐA-05/06.
