# UPDATE-121 — Nghiên cứu cơ chế AdviceCheckpoint và vị trí tích hợp Agent

- **Ngày:** 2026-08-03
- **Người thực hiện:** Khánh (agent), theo yêu cầu Khánh trong hội thoại
- **Loại:** research
- **TODO / User story liên quan:** chạm `Q-13`, `Q-14`, `V-21` (đang chờ Cường); liên quan ĐA-04
  (AdviceCadencePolicy), ĐA-05 (lifecycle store), ĐA-06 (AdviceEnvelopeV2)

## Tóm tắt

Audit toàn bộ chuỗi Simulator → Driver State → Solver → Advice → Agent → Backend → UI để trả lời
"kết quả solver nào đáng đưa cho tài xế, và khi nào gọi agent". Kết luận: repo **đã có ~70% cơ chế
này**, nhưng nó **bị chẻ đôi thành hai nửa không nối được** — sim emit `decided` mà không có
`displayed`; sản phẩm emit `displayed` mà không có `decided`. **Không code gì** ở lượt này.

## Chi tiết cập nhật

Tạo hồ sơ audit `research/audit/2026-08-03-advice-checkpoint/findings.md` (11 mục): sơ đồ flow thật,
bảng FACT/PARTIAL/GAP/BUG-RISK có path+line, 3 phương án chuẩn hoá checkpoint, so sánh 4 thời điểm
gọi agent, schema thiết kế, chính sách nhịp, rủi ro, kế hoạch 6 giai đoạn.

**Ba phát hiện chính:**

1. **Hai nửa là ảnh gương lỗi của nhau** — đây là lý do gốc khiến hai đường đo "không join được" như
   `specs/adherence-measurement.md` ĐÍNH CHÍNH 2026-07-30 đã ghi. Checkpoint không cần phát minh,
   cần **hợp nhất**.
2. **`AdvisorPipeline` mồ côi** — tầng agent (Composer + Verifier + `safe_degrade` fail-closed) đã
   xây xong nhưng **không đường sản phẩm nào gọi**; caller duy nhất là 11 file test +
   `scripts/smoke_advisor_live.py`. Cùng họ "cơ chế mồ côi" với `trajectory.py` (V-22) và
   `hanoi_graph.py`. Backend **có** dùng `verifier` rời (`adapters/advisor.py:16`) nhưng bỏ qua pipeline.
3. **`superseded`/`expired` chưa bao giờ được emit cho advice** — nhưng **consumer đã sẵn sàng**:
   `projections.decision_state()` là máy trạng thái đủ 7 state, replay-idempotent. Thiếu **producer**,
   không phải thiếu máy.

Khuyến nghị: PA-B (checkpoint là entity thật) làm chính, agent gọi theo phương án C (chỉ khi
checkpoint đã qua policy + còn hiệu lực + sắp hiển thị) cho sản phẩm và D (precompute) cho sim, với
ràng buộc **một pipeline, hai thời điểm gọi** để không lặp lại B6-PARITY ở tầng agent.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/audit/2026-08-03-advice-checkpoint/findings.md` | tạo | Hồ sơ audit 11 mục |
| `research/README.md` | sửa | Thêm hồ sơ mới vào bảng `audit/` |
| `tracking/PENDING-REVIEW.md` | sửa | Thêm `Q-15` — thứ tự roadmap, GĐ0 bị chặn |
| `tracking/TODO.md` | sửa | Thêm mục nghiên cứu + 6 giai đoạn |
| `tracking/ASSIGNMENTS.md` | sửa | Claim Khánh cho nhánh nghiên cứu này |
| `tracking/updates/UPDATE-121-*.md` | tạo | File này |

**KHÔNG có file code nào bị sửa.**

## Docs đã cập nhật kèm theo

SCOPE/USER_STORIES/DEFERRED: không đổi (nghiên cứu trong scope hiện hành, không mở rộng scope).
TODO + PENDING-REVIEW + ASSIGNMENTS + research/README: có, xem bảng trên.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Sim không bao giờ gọi `AdvisorPipeline` | `OBSERVED-CODE` | `grep gsm_core.advisor src/gsm_sim/` = rỗng; **+ đã loại trừ dynamic import** (`importlib`/`__import__`/`getattr` = rỗng) | Cao | Nếu sai, G1 không tồn tại và GĐ4 đổi phạm vi |
| Sản phẩm chỉ chạy S1 | `OBSERVED-CODE` | `adapters/advisor.py:190` chỉ `bonus_feasibility.solve()` | Cao | Trùng khớp `Q-14` đã mở từ trước ⇒ đối chứng độc lập |
| `superseded`/`expired` chưa được emit cho advice | `OBSERVED-CODE` | grep: 4/4 hit là `order_expired`; `superseded` chỉ trong docstring | Cao | Nếu sai, G3 hẹp hơn |
| `decision_state()` xử lý đủ 7 state | `OBSERVED-CODE` | `projections.py:64-95`, `_TERMINAL:21` | Cao | Đây là căn cứ để hạ chi phí PA-A |
| `valid_until` = 1 bucket (30′) | `ASSUMPTION` | Suy từ `DECISION_BUCKET_MIN` sẵn có; **chưa đo** | **Thấp** | Nếu sai, advice hết hạn sớm/muộn — phải đo bằng sim trước khi chốt |
| `min_expected_impact` cần thiết | `ASSUMPTION` | Suy luận từ tiền lệ Q-09; **chưa có số** | **Thấp** | Có thể làm advisor im quá mức (bài học V-18) |

## Kiểm chứng

- Đọc trực tiếp và trích dẫn có path+line: `cadence.py`, `advice_bridge.py`, `world.py`,
  `projections.py`, `event_log.py`, `pipeline.py`, `advice.py` (router), `adapters/advisor.py`,
  `cards.js`, `advice_lifecycle_event.schema.json`, `composed_advice.schema.json`,
  `specs/adherence-measurement.md`.
- Grep có kiểm chứng ngược: dynamic-import check để không kết luận "mồ côi" chỉ từ grep tĩnh.
- **CHƯA kiểm chứng:** không chạy simulation, không chạy test, **không sửa dòng code nào** ⇒ suite
  không bị ảnh hưởng (không chạy lại; lần chạy gần nhất UPDATE-120: 935 passed/4 skipped + 66 UI).

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| (không chạy) | — | — | — | **Toàn bộ §8** của hồ sơ: `valid_until`, `min_expected_impact` là giả thuyết chưa đo |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** docs-only. Không đổi dòng code nào, không đổi simulator dynamics, UI, metric, visual
  encoding hay cách stakeholder diễn giải kết quả. Không có gì để xem bằng mắt.

## Adversarial self-review / flaws found

1. **Điều gì có thể khiến kết quả trông tốt nhưng sai?** Báo cáo dựa nhiều vào grep. Đã phòng bằng
   dynamic-import check, nhưng grep vẫn không chứng minh được hình thức. Nếu có đường gọi qua
   config/entry-point mà tôi chưa nghĩ tới thì G1/G2 hẹp lại.
2. **Đã tự sửa một đánh giá giữa chừng:** bản nháp đầu xếp PA-A là "không giải được gì mấy" vì chưa
   đọc `projections.decision_state()`. Sau khi đọc, máy trạng thái **đã tồn tại đủ 7 state** ⇒ PA-A
   rẻ hơn nhiều, và G3 được phát biểu lại chính xác là *"consumer sẵn sàng, thiếu producer"*. Đây là
   lỗi đọc thiếu của tôi, đã ghi vào §11 hồ sơ để người sau không lặp lại.
3. **Assumption yếu nhất:** `valid_until` = 1 bucket và `min_expected_impact`. Cả hai **chưa có bất
   kỳ số đo nào** — tôi cố tình KHÔNG đề xuất con số cụ thể, vì `cadence.py:70-72` ghi rõ *"đừng
   chỉnh mấy số này bằng trực giác"*.
4. **Rủi ro mới phát hiện, chưa từng ghi ở đâu:** verifier **không có luật** buộc `action_type` của
   agent phải khớp `solver_decision.action_now` ⇒ agent về lý thuyết **đổi được action của solver**,
   vi phạm ranh giới sản phẩm CLAUDE.md §5. Hiện chưa gây hại vì agent chưa được nối, nhưng phải
   đóng **trước** GĐ4. Đã đưa thành GĐ5.
5. **Rủi ro namespace:** `expired` trùng tên với `order_expired` — thêm advice-expiry mà không tách
   namespace sẽ trộn hai khái niệm trong metric (R4).
6. **Baseline đã so:** đối chiếu với ĐÍNH CHÍNH 2026-07-30 (`adherence-measurement.md`) — kết luận
   của tôi (hai nửa gương nhau) **giải thích được** hiện tượng mà đính chính đó ghi nhận (hai đường
   không join được), tức hai nguồn độc lập khớp nhau.
7. **Flaw còn mở → map vào đâu:** G1..G8 và R1..R5 đã map vào TODO (6 giai đoạn) + `Q-15` mới ở
   PENDING-REVIEW. Không có flaw nào bị bỏ lửng.

## Expansion checkpoint (T-039)

1. **Schema**: đề xuất `advice_checkpoint@1.0.0` (§7 hồ sơ) — **chưa tạo**, chờ GĐ0. Nếu làm thì đi
   qua `schema_registry` + upcaster như B-02 đã dựng.
2. **Bài toán tối ưu**: không có residual mới. Nhưng nếu có `min_expected_impact`, bài toán "chọn
   advice nào để nói trong ngân sách 6 thẻ/ca" trở thành một **knapsack theo ca** — có thể formalize
   sau, hiện chưa cần.
3. **Tính năng**: UI có thể hiện "advice này còn hiệu lực tới HH:MM" khi có `validity` — đề xuất, chưa làm.

(Không tự triển khai — ghi để Cường duyệt.)

## Follow-up / defer phát sinh

- **`Q-15` (MỚI)** → PENDING-REVIEW: thứ tự roadmap — gỡ B6-PARITY (Q-14) trước hay sau checkpoint?
  GĐ0 bị chặn bởi Q-13/Q-14/V-21.
- **GĐ1 làm được ngay** (hợp nhất taxonomy topic) — không phụ thuộc GĐ0. Chưa làm vì Khánh yêu cầu
  "chưa code" ở lượt này.
- **Nợ đọc:** `templates.py` (319 dòng) mới đọc lướt; `episode_store.py` chưa kiểm xem có tái dùng
  làm nơi lưu StateSnapshot (G5) được không.
