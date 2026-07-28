# Review đối kháng Cycle W (ĐA-05 lifecycle store) — 16 finding có reproduce thật

- **Ngày:** 2026-07-29 (02:30–03:30)
- **Cách chạy:** 2 agent độc lập, mỗi agent một lăng kính, **bắt buộc chạy repro thật**
  (không suy diễn), cấm sửa file repo. Batch 2 agent theo quota guard §3.5 sau khi
  batch 4-agent đầu tiên chết toàn bộ vì session limit.
- **Trạng thái:** đang sửa dở tại thời điểm Cường yêu cầu pause. Bảng dưới ghi rõ cái nào
  đã sửa, cái nào chưa.

## Vì sao hồ sơ này tồn tại

Review tìm ra **lỗi nghiêm trọng nhất của cycle**: `adherence_view` — chính cái "một luật"
mà ĐA-05 quảng cáo là nguồn sự thật chung — báo adherence **0% / 2% / 100%** trong khi sự
thật là **53,6% / 52,2% / 48,8%**. Đây đúng họ lỗi BUG-EVAL-ARGMAX: thước đo sai được
trình bày như sự thật. Nếu ship, mọi kết luận về "tài xế có nghe advisor không" đều sai.

## Lăng kính 1 — NGỮ NGHĨA & CORRECTNESS (F-1..F-8)

| # | Finding | Sev | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| F-1 | `adherence_view` SAI ở mọi kênh, sai cả hai chiều. `_SIM_KIND_MAP` map theo KIND trong khi `followed` của sim nằm ở `detail["followed"]`; `advice_followed` chỉ log khi advice ĐỔI hành động (BRIDGE-3); `shift_extend`/`rest_window` chỉ log khi ĐÃ theo; positioning không có event `decided` per-actor | **HIGH** | projection 2,0%/0,0%/0,0%/100% vs sự thật 52,2%/53,6%/100%/48,8% (seed 1000, coverage=all). Tự verify độc lập: khớp | **ĐÃ SỬA** — `_sim_steps()` đọc `detail["followed"]`; `standby_alloc` mang `assigned_ids`/`decision_ids` làm mẫu số |
| F-2 | `adherence_view` key `(driver_id, topic)` trộn hai run: sim đặt `driver_id=str(actor_id)` ⇒ actor 0 của run A và run B là một hàng | **HIGH** | 33+37=70 khoá gộp còn 55 ⇒ 15 tài xế trộn chéo vũ trụ | **ĐÃ SỬA** — key `(run_id, driver_id, topic)` |
| F-3 | Idempotency window UI là CẢ NGÀY, không phải "cùng phút": `at_min` là hằng số theo loại card (`cards.js`) ⇒ "Làm theo → Bỏ qua → Làm theo lại" bị nuốt, nhật ký hiện NGƯỢC hành động cuối | **HIGH** | CŨ `[followed, dismissed, followed]` → MỚI `[dismissed, followed]` | **ĐÃ SỬA** — key theo giây quan sát |
| F-4 | `derive_run_id` chỉ đọc block `advice` ⇒ hai run khác hẳn (bucket_min 60 vs 15) cùng ID; kết quả lệch 7 lần | MED | `standby_followed` 38 vs 262, cùng `run_id` | **ĐÃ SỬA** — thêm digest sha256 của toàn config (trừ `meta`) |
| F-5 | `_decision_id` hardcode bucket 30' trong khi planner chạy `advice.bucket_min` | MED | `bucket_min=15` ⇒ 23 decision_id trùng ⇒ 23 event bị nuốt | **ĐÃ SỬA** — bucket theo config cho kênh vị trí |
| F-6 | `count_episodes` đếm distinct decision trên TOÀN BỘ file, không lọc `origin` ⇒ thổi phồng khi UI/sim ghi chung; append trùng `episode_id` mất im lặng (bản cũ nổ IntegrityError); 20k event ⇒ 149 ms | MED | 12 → 13 → 16 → 17 khi thêm event UI/sim | **CHƯA SỬA** |
| F-7 | `sim_events_to_lifecycle` bỏ qua `Event.run_id`, lấy từ tham số ⇒ record TỰ MÂU THUẪN vẫn pass schema (rủi ro thật ở multiday) | MED | cột `run_id='TOI-BIA-RA'` trong khi `decision_id` nhúng run thật | **ĐÃ SỬA** — ưu tiên `Event.run_id`, lệch ⇒ ValueError |
| F-8 | POST /action ghi JSONL TRƯỚC canonical ⇒ validate lỗi làm hai store phân kỳ | MED | `date="29/07/2026"` ⇒ HTTP 500, JSONL đã có dòng | **ĐÃ SỬA** — canonical trước, JSONL sau + validate `date` ở pydantic |

**Đã kiểm, KHÔNG có lỗi** (agent tự chạy): fallback `standby_decision` không bao giờ chạy
(pop MISS=0); tie-break `advice_suppressed`/`advice_given` cùng tick ổn định (hoán vị ×10
không đổi state); `get_actions` thứ tự + `limit` khớp hành vi JSONL cũ; CHANNEL_LADDER
không bậc nào đụng ID.

## Lăng kính 2 — TƯƠNG THÍCH CONSUMER (W-1..W-8)

| # | Finding | Sev | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| W-1 | = F-4, xác nhận chéo bằng ca khác: đổi `dow=weekend` ⇒ cùng run_id, **128 event_id + 889 decision_id đụng nhau**; store `INSERT OR IGNORE` **nuốt im lặng** run thứ hai | **HIGH** | append run B trả False, payload run A còn lại | **ĐÃ SỬA** (digest) |
| W-2 | `pl.DataFrame(rows)` dùng `infer_schema_length=100` ⇒ key xuất hiện sau dòng 100 bị bỏ IM LẶNG. Ở **đúng cấu hình mặc định đã duyệt** (chỉ positioning bật), event đầu mang `decision_id` ở index 158 ⇒ **cột khoá join biến mất khỏi `events.parquet`** | **MED-HIGH** | columns thiếu `d_decision_id`, `d_channel`, `d_safety_flags`, `d_to_cell`, `d_capacity_left` | **ĐÃ SỬA** — `infer_schema_length=None` |
| W-3 | = F-8 (POST 500 + hai store lệch) | MED | status 500, JSONL đã ghi 1 dòng | **ĐÃ SỬA** |
| W-4 | `at_min=1440` (pydantic cho phép) sinh `T24:00:00` — **lọt regex** `\d{2}` của schema nhưng `fromisoformat` nổ ⇒ MỘT record độc giết toàn bộ `decision_state` của store | MED | POST 200, sau đó `decision_state` ValueError | **ĐÃ SỬA** — `le=1439` (còn nên siết regex giờ 0-23) |
| W-5 | `at_min=None` ⇒ `event_id` trùng ⇒ lần bấm thứ hai bị nuốt (JSONL vẫn 2 dòng). Bản ghi lịch sử duy nhất trong repo đúng dạng `at_min: null` | LOW-MED | 2 POST → 1 event, 2 dòng JSONL | **ĐÃ SỬA** (key theo giây) |
| W-6 | Hai audit trail nói ngược nhau: episode ghi `verify.passed=None` (đúng) nhưng recorder ghi `passed=True` cho request CHƯA verify (`or {...}` ở `pipeline.py:209`). Reset của Cycle W làm lỗi từ hiếm thành hệ thống ở nhánh R5 | MED | `last_verify_result={}` → recorder `verifier_passed=True` | **CHƯA SỬA** |
| W-7 | `close()` không với tới chủ sở hữu thật: `AdvisorPipeline` không có `close()`/context manager, 12/13 call site đi qua nó ⇒ vẫn rò connection (`PermissionError WinError 32`). Không phải regression — là fix chưa đủ | LOW | `rmtree` khi pipeline còn sống ⇒ nổ | **CHƯA SỬA** |
| W-8 | DB legacy: bảng `episodes` cũ vô hình với API mới ⇒ `count_episodes` trên DB cũ = 0. Không có `.db` nào trong repo nên tác động ~0 | LOW | count=0 trên DB có 2 dòng episodes | **CHƯA SỬA** (informational — đã ghi UPDATE) |

**Đã kiểm, KHÔNG có lỗi**: `Event.run_id` không phá positional/equality/asdict (1 call site
src, tests dùng keyword); `adapter_sim` mockgen 0 record fail schema, không rò key advice
sang L0/L1; dashboard/sim_metrics/journey/trajectory/parallel/router sim **giống hệt từng
bit** khi strip key mới; 7 file test advisor 106 passed; `smoke_advisor_live.py` chạy thật
với LLM live, 4 feature faithfulness 1.0.

## Kết quả ĐO LẠI sau khi sửa F-1 (seed 1000, coverage=all, 4 kênh + positioning)

| Kênh | Trước sửa | Sau sửa | Ground truth | Nhận xét |
|---|---|---|---|---|
| `shift_plan` | 2,0% | **52,2%** (631/1208) | 52,2% (631/1208) | **khớp chính xác** |
| `shift_extend` | 0,0% | **100%** (43/43) | 100% | **khớp chính xác** |
| `positioning` | 100% (36/**36**) | 41,9% (36/**86**) | 48,8% (42/86) | **mẫu số đã đúng** (86 = số người được gán). Tử số 36 = số người THỰC SỰ dịch chuyển; 42 = số người *nhận* lời khuyên (draw thành công) — 6 người nhận nhưng chưa kịp đi (tới ô đúng trước / hết ca). Hai đại lượng khác nhau, projection đo cái thứ hai — **đúng ý nghĩa "đã làm theo"** |
| `accept_lift` | 0,0% | 76,9% (50/65) | 53,6% (60/112) | **khác ĐƠN VỊ, không phải sai**: GT đếm theo EVENT (gate fire mỗi tick 2′), projection đếm theo DECISION (gộp bucket 30′ theo spec adherence). 112 event → 65 decision; decision được tính followed nếu có ít nhất một lần theo trong bucket. Cần chốt định nghĩa nào là "adherence" chính thức trước khi báo cáo số này ra ngoài |

## ⏸ TRẠNG THÁI KHI PAUSE (Cường yêu cầu 2026-07-29 ~03:40)

**Đã commit ở trạng thái này. Cường chốt: phần còn lại PHẢI qua plan mode trước khi sửa.**

Xanh tại thời điểm commit: `test_lifecycle_store` + `test_lifecycle_wiring` +
`ui/backend/tests` = **77 passed**. Hai test phải sửa index vì fix F-2 đổi khoá
`adherence_view` thành `(run_id, driver_id, topic)` — thay đổi cơ học, không phải lỗi mới.

**CHƯA làm — không được coi cycle là xong:**

1. **Full suite CHƯA chạy** sau loạt fix này (lần cuối xanh là trước khi sửa 16 finding).
2. **Fingerprint bit-identical CHƯA chạy lại** — `standby_alloc` nay mang thêm
   `assigned_ids`/`decision_ids`, `derive_run_id` đổi dạng (thêm `-c{digest8}`),
   `logging_ev` đổi `infer_schema_length`. Phải chứng minh lại hành vi sim KHÔNG đổi.
   ⚠ Dự kiến: `summarize` phải IDENTICAL; `kinds` cũng phải IDENTICAL (không thêm kind
   mới, chỉ thêm field trong detail) — nếu lệch là dấu hiệu sửa đã chạm hành vi.
3. **Ba finding chưa sửa**: F-6 (count lọc `origin`), W-6 (recorder bịa `passed=True`),
   W-7 (`AdvisorPipeline.close()`), + phần còn lại của W-4 (siết regex giờ `([01]\d|2[0-3])`).
4. `scratchpad/test_review_fixes.py` (5 test reproduce F-1/F-2/F-5/F-7) **chưa move vào
   `tests/`** — hiện chỉ chạy được thủ công bằng đường dẫn tuyệt đối.
5. **Câu hỏi thiết kế chưa chốt** (phải hỏi Cường trong plan): "adherence" chính thức đo
   theo DECISION (bucket 30′) hay theo EVENT? Hai cách cho 76,9% vs 53,6% ở `accept_lift`.
   Không chốt thì mọi báo cáo adherence về sau lại là một BUG-EVAL-ARGMAX thứ hai.
6. **Batch 2 review chưa chạy**: 2 lăng kính còn lại (INPUT THÙ ĐỊCH, KỶ LUẬT
   schema/docs/T-046) — batch 4-agent đầu chết vì session limit, mới chạy được 2/4 lăng kính.

## Bài học rút ra (ghi cho T-046)

- **Test của tôi xanh trong khi số thì sai.** Test W3 cũ chỉ kiểm "state machine chạy
  đúng" và "sim adapter map được", không ai đối chiếu adherence với GROUND TRUTH của sim.
  Bài học: với mọi thước đo, phải có ít nhất một test so **số cuối cùng** với sự thật độc
  lập, không chỉ test cơ chế.
- **Review đối kháng bắt được thứ TDD không bắt — lần thứ hai liên tiếp** (Cycle V: 7
  finding; Cycle W: 16). Hai lăng kính khác nhau bắt hai họ lỗi khác nhau, và cả hai đều
  ngoài vùng mà tác giả tự nghi ngờ.
- **Xác nhận chéo có giá trị**: F-4 và W-1 là cùng một lỗi được hai agent tìm ra bằng hai
  ca khác nhau (`bucket_min` vs `dow`) ⇒ độ tin cậy cao hơn hẳn một báo cáo đơn lẻ.
