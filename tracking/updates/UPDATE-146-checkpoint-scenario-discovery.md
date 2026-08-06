# UPDATE-146 — AdviceCheckpoint scenario discovery + presentation funnel (read-only)

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent dưới quyền Khánh (không có claim đang hoạt động xung đột; lượt discovery theo yêu cầu trực tiếp trong hội thoại)
- **Loại:** research / evidence-only
- **Trạng thái:** `DONE-CODE` cho artifact phân tích; **KHÔNG** thay đổi runtime, solver, policy, cadence, UI, flag, producer; **KHÔNG** bật LLM
- **Kế thừa:** UPDATE-144 (inventory) + UPDATE-145 (expansion). Lượt này không lặp lại mà xác minh + bổ sung 3 phép đo mới và phần scenario/gap/prioritization sâu hơn.

## Tóm tắt

Trả lời câu hỏi "vì sao replay nghèo checkpoint và nên làm giàu tình huống thế nào" bằng số đo mới:

1. **Baseline tái lập chính xác** trên working tree: 864/413/450/1 (5 seed 1000–1004) — khớp UPDATE-144 từng con số.
2. **10 seed tươi (2000–2009)** xác nhận cấu trúc ổn định, không phải tình cờ seed: 1.766 record/900 driver-run (1,96), READY 0,959/driver-run, ONLINE 100% suppressed, 0 queued/superseded, 3 expired, per-run 164–186.
3. **Phép đo MỚI — presentation funnel qua đường Web thật** (`DemoSessionService.advance` cho toàn bộ 90 actor seed 1000, route factory stub không mạng): 7.100 step, chỉ **40 step có card (0,56%)**; **53/90 actor không thấy card nào**; median 24 click tới card đầu; **34 card chết `expired` tại presentation** vì validity giả 1 phút; **12 card mất vĩnh viễn** vì moving-at-attach không re-offer và không ghi event `queued`.
4. **Taxonomy 0-bit (FACT mới):** 100% record có `surface=nudge`, `trigger_type=solver_update`, `urgency_band=medium`, `reason_code=solver_recommendation`, `material_revision="1"`, `action_window=None`, validity ≈1′ — mọi field điều phối presentation hiện đơn trị ⇒ priority band phẳng, nhánh LLM `complex_*` không bao giờ kích hoạt, dedup nén mọi revision.
5. **Chẩn đoán:** checkpoint "ít" chủ yếu là policy đúng (maintenance silent 52%, kênh tắt theo ĐA-07) + dedup thiếu `material_revision`; **lỗi thật lớn nhất làm demo nghèo là plumbing** — `freshness_deadline = now+1′` hardcode (`src/gsm_sim/checkpoint_trace.py:63`) nuốt ~40% card đáng lẽ hiển thị được; đuôi READY-SWAP không attach ~1,2% (10/863 seed tươi).
6. **Shortlist đề xuất (chưa code):** hạng 0 = sửa nền móng (validity thật, `action_window`, `numbers[]`/`caveats[]` vào record, `material_revision`, dropoff-fix, event `queued` ở demo path) — ăn mọi card hiện có lẫn tương lai; sau đó mới tới producer mới (`SWAP_SOON`, brief/recap, `order_skipped_soc` awareness…).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `research/audit/2026-08-05-checkpoint-scenario-discovery/discovery-report.md` | tạo | Báo cáo đầy đủ: chẩn đoán 5 lớp, thống kê, purpose map, gap map 6 lớp, 8 nhóm scenario, prioritization, demo candidates, open questions |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/measure_presentation_funnel.py` | tạo | Script đo funnel qua `DemoSessionService` thật; read-only, không mutate RNG/policy; route stub |
| `research/audit/2026-08-05-checkpoint-scenario-discovery/funnel-seed1000.json` | tạo | Kết quả funnel 90 actor seed 1000 |
| `tracking/PROJECT-GRAPH.md` | sửa | Thêm §3.11 phủ UPDATE-134/135/136/137 (graph trước đó dừng ở 133 — vá khoảng trống coverage) |
| Runtime/source/config/test | **không đổi** | Không bật kênh, không sửa cadence, không gọi external API/LLM |

## Docs đã cập nhật kèm theo

`SCOPE`, `TODO`, `DEFERRED`, `USER_STORIES`, `PENDING-REVIEW` **không đổi** (không có mục tương ứng đổi trạng thái). `PROJECT-GRAPH` thêm §3.11 như trên.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| 864/413/450/1 baseline tái lập | `FACT` | rerun `analyze_checkpoints.py` trên working tree, exit 0 | Cao (synthetic) | — |
| Cấu trúc ổn định 10 seed tươi | `FACT` | rerun seeds 2000–2009 | Cao trong synthetic | Không đại diện production |
| 40/7.100 step có card; 53/90 actor 0 card; 34 expired; 12 unsafe_while_moving | `FACT` | `funnel-seed1000.json` | Cao cho seed 1000 | Cần lặp nhiều seed trước khi generalize |
| Validity 1′ do hardcode `now_min + 1` | `OBSERVED-CODE` + `FACT` | `checkpoint_trace.py:63` + 100% record validity=1′ | Cao | — |
| Expired-at-presentation là do validity giả (không phải policy) | `INFERENCE` | revalidate tại `advice_checkpoint.py:375-379` với valid_until=created+1′ | Trung-cao | Nếu sai, nguyên nhân khác cần root-cause riêng |
| Moving-at-attach mất card vĩnh viễn (không re-offer, không event queued) | `OBSERVED-CODE` + `FACT` | `advice_checkpoint.py:406-407`, attach 1-transition `demo_trace.py:176-251`, 12 case funnel | Cao | — |
| 7/10 template key không đến được trong demo hiện tại | `INFERENCE` từ policy order + config | `checkpoint.py:286-287`, demo factory flags | Trung-cao | Kiểm bằng test reachability nếu cần |
| Coverage các candidate (SWAP_SOON 84,7%…) | kế thừa `PROXY` UPDATE-145 | 5 seed | Trung bình | Cần 30 seed |

## Kiểm chứng

| Command | Seed/scope | Kết quả | Chưa kiểm chứng |
|---|---|---|---|
| `analyze_checkpoints.py --seeds 1000..1004 --output <scratch>` | 5 seed | exit 0; 864/413/450/1 khớp UPDATE-144 | — |
| `analyze_checkpoints.py --seeds 2000..2009 --output <scratch>` | 10 seed tươi | exit 0; 1.766/863/900/3; 10 READY-SWAP không attach | phân phối ≥30 seed |
| `measure_presentation_funnel.py 1000` | 90 actor, full timeline | exit 0; JSON artifact | funnel các seed khác; funnel có tài xế thật (intent) |
| Full suite | — | **KHÔNG chạy** (audit bounded, không đổi runtime) | root + ui/backend suites |

## Visual verification

- **Status:** `NOT_APPLICABLE` — docs/data-only, không đổi visual encoding, cadence hay runtime. Không mở browser.

## Adversarial self-review / flaws found

1. Funnel dùng route factory stub (raise → fallback thẳng) để tránh gọi mạng — đã kiểm đường advice không phụ thuộc route content (`_advice` chỉ đọc transition driver state); nếu sau này advice đọc route thì phép đo phải làm lại.
2. Funnel là session trình diễn, không phải tài xế thật — accepted/dismissed/expanded KHÔNG đo được và không được suy diễn; báo cáo giữ 4 tầng Displayed/Accepted/Execution/Outcome tách bạch.
3. `expired=34` đếm theo silent reason tại presentation; chưa phân rã record-level (một checkpoint có thể xuất hiện một lần duy nhất nên rủi ro double-count thấp, chưa chứng minh 0).
4. Kết luận "policy đúng chiếm phần lớn" dựa trên decomposition 5 lớp; không loại trừ bug chưa biết ở tầng solver (ngoài scope lượt này).
5. Số coverage candidate lấy từ UPDATE-145, không đo lại — nhãn PROXY giữ nguyên.
6. `checkpoint_id` lặp giữa run là identity chủ ý; mọi join trong phân tích dùng `(run_id, checkpoint_id)`.
7. Không coi funnel seed 1000 là đại diện: seed khác chưa chạy funnel (chi phí); đã ghi rõ trong giới hạn.

## Follow-up / defer phát sinh (đề xuất, chờ owner — chưa mở TODO item)

- **P0 (plumbing, behavior-đổi-record cần comparator + upcaster):** bỏ hardcode freshness 1′; map `action_window` từ schedule/worst_window; đưa `numbers[]`/`caveats[]`/`material_revision` vào record; fix `dropoff` state boundary (đã là P0 của UPDATE-145); ghi event `queued` ở demo moving-gate; cân nhắc re-offer sau moving.
- **P1:** producer `SWAP_SOON` (topic mới — cần owner duyệt schema); surface brief/recap; awareness `order_skipped_soc`.
- **P2:** income pace / plan deviation / long idle (sau dropoff-fix); tân binh & mission (cần multiday); trạm pin (rủi ro herding — cần cơ chế capacity-aware).
- **Open questions** cho owner: xem §8 của discovery-report (counting touchpoint, taxonomy mở rộng, demo navigation, checkpoint_audit lên UI dev-mode, ranh giới S8/D-006, thí nghiệm mưa trong SIM, thứ tự chốt Q-09/Q-10/Q-13/V-21).
