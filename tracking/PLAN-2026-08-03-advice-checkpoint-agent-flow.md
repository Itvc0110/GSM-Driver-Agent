# Plan tổng hợp: AdviceCheckpoint + tích hợp Agent

**Nguồn:** hợp nhất plan của tôi (2026-08-03) + plan review, sau khi **kiểm chứng từng luận điểm
bằng code**. Không code ở bước này.

---

## Context

Repo có ba đường gần như độc lập: simulator (gọi S1/S2/S4/S7, mô phỏng tuân thủ), backend sản phẩm
(chỉ S1, tự dựng card), và `AdvisorPipeline` (composer/verifier/fallback nhưng **không caller runtime
nào**). Hệ quả: không truy được lời khuyên về state đã sinh ra nó, không phân biệt được "đã hiển thị"
với "đã mô phỏng làm theo", và **đã có lỗi lọt ra tới tài xế**.

Plan này lấy **kiến trúc của bản review** (mạnh hơn) + **tính cụ thể của bản tôi** (output thật,
bug tái lập được), rồi sửa lỗi của cả hai theo bằng chứng đã kiểm.

### Đã kiểm chứng — sửa lỗi của CẢ HAI plan

| Sai ở đâu | Sự thật đã kiểm | Ảnh hưởng plan |
|---|---|---|
| **Tôi**: `valid_until = 30′` | Ba số khác nhau: `interval_min:30` (polling) · `bucket_min:60` ([config:387](configs/pilot_dongda.yaml#L387), cửa sổ khuyến nghị) · `DECISION_BUCKET_MIN=30` (lưới định danh) | `valid_until` do **normalizer từng solver** cấp từ bucket của nó, KHÔNG hằng số |
| **Tôi**: "cả hai đường gate trước solver" | **Sai với S1/S7**: `bonus_feasibility.solve()` chạy trong `_advice_would_help` (dòng 653) **trước** `cadence_allows` (dòng 666); [:659-665](src/gsm_sim/advice_bridge.py#L659-L665) ghi rõ là **cố ý** (hỏi nhịp sớm ⇒ 63% event nén ma) | Không được "chuẩn hoá" bằng cách ép cadence lên trước — sẽ tái tạo lỗi đã sửa |
| **Tôi**: verifier sau khi nối agent (`findings.md` §10) | Đúng thứ tự là **verifier trước** | GĐ4 trước GĐ5; và phải sửa `findings.md` đã vào repo |
| **Tôi**: agent trả `action_type` rồi verifier kiểm | Loại bằng **cấu trúc** mạnh hơn: agent **không** phát ngôn action | Contract agent: chỉ sinh lý do; action do code render |
| **Review**: `advice_followed 19` cạnh `advice_given 1187` | [world.py:840](src/gsm_sim/world.py#L840) chỉ log `followed` khi `mapped_action != action` — tức **chỉ khi advice ĐỔI hành vi**. Không phải adherence 1,6% | Bảng phải chú thích, nếu không tái tạo đúng lỗi "mẫu số hỏng" của ĐÍNH CHÍNH 2026-07-30 |
| **Review**: "backend TestClient treo" | Ở máy này **66 passed / 10s** | Không phải giới hạn repo; kiểm chứng backend LÀM ĐƯỢC |
| **Cả hai bỏ sót** | [`event_log.append()` validate qua registry TRƯỚC khi ghi](src/gsm_core/lifecycle/event_log.py#L123); `event_type` là **enum đóng 7 giá trị**; schema `additionalProperties:false` | **Schema phải đi trước** mọi event type mới — ràng buộc cứng, không phải lựa chọn |

### Claim của bản review đã xác nhận đúng

264 `advice_rest_veto` dù `advice.enabled=False` (khớp chính xác, tổng 6.391 events) · `sim.py` gom
`advice_*` thành event "advice" cho tài xế · **safety bypass cả `is_driving`**
([cadence.py:156](src/gsm_core/lifecycle/cadence.py#L156) `return PRESENT` đứng trước `if is_driving`) ·
QUEUE vi phạm `ui/contracts/advice.json` đúng 4 lỗi · Flutter hard-code — **và tệ hơn mô tả**:
"Vincom Đồng Khởi"/"Q.1" là **TP.HCM** trong khi pilot là **Đống Đa, Hà Nội**, lại không nhãn mock.

---

## 1. OUTPUT — thứ thay đổi mà người dùng thấy

**Ca thật đã chạy** (`shift_dp`, d-15, 09:00, SOC 46%, 78 điểm): `schedule[0] = ONLINE@09:00`,
`next_action = SWAP@10:00`.

| | Nội dung |
|---|---|
| **TRƯỚC** (đang chạy hôm nay) | *"Gợi ý **lúc này**: anh/chị nên **đi đổi pin** — đổi pin trước khi cạn."* — trong khi solver bảo **chạy tiếp**, và `advice_spec` của chính nó ghi **10:00** |
| **SAU** | **"Bây giờ: cứ chạy tiếp."** · *"Sắp tới **10:00** nên đổi pin."* · ⚠ *"Tỷ lệ nhận dưới ngưỡng nên mốc thưởng hiện **0đ**."* · <sub>hiệu lực tới 10:00 · độ tin 50% · số liệu mô phỏng</sub> |

Nguồn lỗi: [`templates.py:283`](src/gsm_core/advisor/templates.py#L283) đọc `next_action` rồi render
`"Gợi ý lúc này"`, **không bao giờ đọc `schedule[0]`**.

---

## 2. Bất biến (thi hành bằng cấu trúc, không bằng lời hứa)

| # | Bất biến | Cách thi hành |
|---|---|---|
| **I1** | Không tồn tại trường "action" chung chung. Chỉ có `recommendation.action` (bucket hiện tại) và `future_plan` | schema |
| **I2** | `valid_until` do **normalizer của solver** cấp (bucket + freshness + shift end). Không hằng số | normalizer per-solver |
| **I3** | **Agent không phát ngôn action/window/số/nguồn.** Chỉ trả `reason_template`/`why_template` + ID đã dùng | contract agent |
| **I4** | Mọi số là placeholder tham chiếu `numbers_registry` | **đã có** — `V.check_bare_numbers` |
| **I5** | `offered` (backend trả response) ≠ `displayed` (client ACK đã render) | lifecycle v1.1.0 |
| **I6** | Một active checkpoint / driver / topic; một primary card | policy thuần |
| **I7** | `topic` (miền solver) ≠ `surface` (nơi hiển thị). `brief/nudge/recap` là **surface**, không phải topic cooldown | taxonomy |

---

## 3. Kiến trúc

```
AnalysisTrigger → StateSnapshot → SolverReport → RecommendationCandidate
                                                        │
                                                 CheckpointPolicy (thuần)
                              ┌──────────┬──────────────┼──────────┐
                              ▼          ▼              ▼          ▼
                          SUPPRESSED  QUEUED         READY      silent
                                                        │
                                              presentation lease (display_id)
                                                        │
                                              Agent/Template  ← ĐIỂM DUY NHẤT gọi agent
                                                        │
                                              revalidate checkpoint
                                                        │
                                                 offered → client ACK → displayed
                                                        │
                                              followed | dismissed  (= ý định, KHÔNG phải execution)
                                                        │
                                              execution link (record riêng)
```

**Identity:** `snapshot_id` · `solver_run_id` · `checkpoint_id` · `display_id` · `execution_segment_id`.

**Gọi agent — phương án C** (chỉ khi READY + còn hiệu lực + sắp hiển thị) cho sản phẩm;
**phương án D** (precompute + replay) cho sim/eval. **Chung một pipeline**, khác thời điểm gọi.
Probe cho thấy phương án A có thể tạo ~9.400 model call/run mà phần lớn không thành lời khuyên.

⚠ **Không ép cadence lên trước solver ở S1/S7** — thứ tự hiện tại là có chủ đích và đã trả giá để có.
Checkpoint được sinh **sau** khi candidate thành hình, ở cả hai kiểu thứ tự.

---

## 4. Giai đoạn — mỗi giai đoạn dừng được an toàn

### GĐ0 — Việc độc lập, làm được ngay (không chờ kiến trúc)

Không mục nào phụ thuộc checkpoint. Ưu tiên cao vì đang ảnh hưởng thật.

| Việc | File | Vì sao gấp |
|---|---|---|
| **A. BUG-F2-NOW** — template đọc `schedule[0]`, tách `now_line`/`next_line` | `advisor/templates.py` | Lỗi đang tới tay tài xế; test đỏ trước |
| **B. Safety bypass `is_driving`** | `lifecycle/cadence.py` | **An toàn.** Hiện `safety` → PRESENT kể cả đang lái. Sửa tối thiểu: safety **không** bypass `is_driving`; cảnh báo khẩn cần modality riêng — **chưa tồn tại** ⇒ tới khi có, safety phải QUEUE |
| **C. `advice_rest_veto` rò vào luồng tài xế** | `routers/sim.py` | Event lan can bị hiển thị như lời khuyên; 264 lần dù advice TẮT |
| **D. QUEUE vi phạm contract** (3 required thiếu + `reason_code` ngoài enum) | `routers/advice.py`, `ui/contracts/advice.json` | Mọi phản hồi im lặng đang vi phạm contract |
| **E. Flutter hard-code** | `driver_app/lib/screens/home_screen.dart` | Sai thành phố (TP.HCM vs Hà Nội) + không nhãn mock ⇒ vi phạm CLAUDE.md §5 |
| **F. Sửa nợ tài liệu của tôi** | `research/audit/2026-08-03-*/findings.md`, `tracking/PLAN-2026-08-03-*.md` | 2 sai sót + 1 mâu thuẫn thứ tự đã vào repo |

**Dừng được:** có. Mỗi mục là một cycle độc lập, review/commit riêng.
**Kiểm:** test đỏ→xanh cho A/B/D; 5 seed chứng minh C không đổi số A/B; visual gate cho A/E.

---

### GĐ1 — Schema + policy thuần (shadow, KHÔNG đổi hành vi)

**Ràng buộc cứng đã kiểm:** `append()` validate trước khi ghi, `event_type` enum đóng ⇒ **schema
phải xong trước mọi thứ khác**.

- `advice_lifecycle_event@1.1.0`: thêm `queued/ready/generated/offered`; giữ 7 giá trị cũ. Upcaster
  1.0.0→1.1.0 theo đúng lối `upcasters.py` đã dùng 2 lần.
- `driver_state_snapshot@1.0.0`, `advice_checkpoint@1.0.0`, `agent_presentation_input/output@1.0.0`.
- `lifecycle/checkpoint.py` — **hàm thuần**, không import sim/UI (cùng kỷ luật `cadence.py`).
- Normalizer **riêng cho từng solver** (S1/S2/S4/S7/rule): tách `action` (bucket hiện tại) khỏi
  `future_plan`; mỗi normalizer tự cấp `valid_until`.
- Policy thuần: fingerprint · dedup · validity · priority lexicographic · queue · supersede.

**Fingerprint chứa:** topic, canonical action, normalized window, urgency band, reason code,
material revision. **Không chứa:** message, poll timestamp, solver invocation ID.

**Priority (lexicographic, không score tuỳ ý):** `P0` safety/năng lượng nguy cấp → `P1` sắp hết hạn
(SWAP/CHARGE/REST/END/bonus) → `P2` shift-plan/timing → `P3` thông tin (mặc định IM).
Cùng mức: hết hạn sớm hơn → impact lớn hơn (**do solver cấp**) → confidence cao hơn → tạo trước → thứ tự topic.

**Dừng được:** có — chạy shadow, không đường nào đọc kết quả.
**Kiểm:** unit test policy thuần; compat-test upcaster bằng record persist thật (lối B-02).

---

### GĐ2 — Simulator traceability

- Phát checkpoint từ **callsite hiện có**, không thêm trigger mới.
- Persist `snapshot_ref` / `solver_ref` (ref + digest, không nhúng cả state).
- Segment ID deterministic + link checkpoint → segment.
- Đo: candidate volume, duplicate rate, expiry, retained value, quan hệ execution.

**Dừng được:** có — dữ liệu chẩn đoán có giá trị ngay cả khi dừng ở đây.
**Kiểm:** **fingerprint identical 5 seed trước/sau** — lệch ⇒ DỪNG, không "calibrate lại".
Báo cáo `decision_adherence` và `event_adherence` **tách tên** (phán quyết Cường 2026-07-29, cấm khoá trần).

---

### GĐ3 — Backend/UI lifecycle, template-only

- Sản phẩm phát `decided` trước `offered`/`displayed` (đóng khoảng trống mẫu số).
- `GET` chỉ ghi `offered`; thêm **POST display ACK** ghi `displayed`.
- QUEUE lưu là `queued`, không phải `suppressed`.
- Trả contract mới sau feature flag; giữ adapter cho response cũ.
- UI không tự xoá card cạnh tranh — backend phát `superseded`.
- Bỏ `brief/nudge/recap` khỏi vai trò topic (chỉ còn surface).

⚠ **Display ACK đổi nghĩa metric:** `displayed` sẽ under-count khi ACK rớt ⇒ **số trước/sau GĐ3
không so trực tiếp được**. Phải ghi rõ mốc đứt gãy.

**Dừng được:** có — template renderer deterministic, chưa có LLM. **Toàn bộ kiến trúc checkpoint
kiểm thử được độc lập trước khi đụng model.**

---

### GĐ4 — Contract + guardrail agent (TRƯỚC khi nối)

- Contract presentation-only: agent nhận `canonical_action` (label do **code** render),
  `action_window`, `facts`, `numbers_registry`, `confidence`, `caveat_ids`, giới hạn độ dài.
  **Không** gửi toạ độ thô, PII, toàn bộ trajectory, hay future schedule không liên quan.
- Agent trả `reason_template` / `why_template` + `used_fact_ids` / `used_number_ids` / `used_caveat_ids`.
  **Không** trả action/window/expiry/zone.
- Verifier bổ sung: checkpoint ID khớp · chỉ dùng ID có trong input · không digit ngoài placeholder ·
  không hứa thu nhập · không biến forecast thành chắc chắn · giới hạn độ dài theo surface · 1 repair
  rồi fallback template.

**Dừng được:** có. **Điều kiện ra:** verifier action-boundary **hoàn thành** — đây là cổng, không phải bước.

---

### GĐ5 — Nối agent (`llm_mode="off"`)

- Sản phẩm: phương án C — lease `display_id` → cache → gọi → validate → **revalidate checkpoint sau
  model call** → hết hạn/superseded thì bỏ output.
- Sim: phương án D — precompute rồi replay.
- Cache key: fingerprint + locale + prompt/template version + model version + policy version.
  TTL **không vượt** `valid_until`.
- Agent lỗi/timeout **không được** làm sai lifecycle của checkpoint.

**Dừng được:** có — vẫn template, nhưng đã đi qua toàn bộ đường agent thật.

---

### GĐ6 — LLM live + đánh giá

Shadow → canary nội bộ → driver opt-in. Lưu model/provider/prompt/template version. So nhiều agent
trên **cùng trajectory**. Theo dõi: cards/ca, duplicate, queued-expiry, ACK rate, intent vs execution,
fallback rate, latency/chi phí, fairness.

**Không tuyên bố uplift production từ số mô phỏng.**

---

## 5. Kiểm chứng xuyên suốt

| Loại | Cách |
|---|---|
| Bug đã tái lập | Test đỏ trước: `schedule[0]=ONLINE` + `next_action=SWAP@10:00` ⇒ `now_line` phải nói "chạy tiếp", **không** chứa "đổi pin"; `next_line` chứa "10:00" |
| Hồi quy suite | `pytest -q` **VÀ** `pytest -q ui/backend/tests` (CLAUDE.md §2). Baseline: **935+4skip / 66** |
| Bất biến hành vi | fingerprint identical **5 seed** cho GĐ1–GĐ3; lệch ⇒ dừng |
| Phân phối | ≥30 seed nếu đụng phân phối/calibration |
| Visual | GĐ0-A/E và GĐ3 đổi thứ tài xế thấy ⇒ chụp `/app/` trước/sau |

**Kịch bản bắt buộc:** ONLINE hiện tại + SWAP tương lai · trip xong đúng lúc advice hết hạn · SOC qua
ngưỡng khi đang on_trip · nhiều topic cùng READY · cùng candidate qua nhiều lần polling · solver
timeout/infeasible/stale · agent timeout/JSON hỏng/bịa số/quá dài · HTTP rớt trước ACK · checkpoint bị
supersede khi agent đang chạy · tài xế bấm "Làm theo" nhưng segment không xảy ra.

---

## 6. Rủi ro

| Rủi ro | Xử lý |
|---|---|
| **Overload `decision_id` = `checkpoint_id`** trên dữ liệu đang có; `adherence_view` khoá trên nó | **Chưa có kế hoạch migration ở cả hai plan.** Phải quyết trước GĐ2: field mới hay overload + backfill. Nếu overload, so sánh lịch sử phải có mốc đứt gãy |
| GĐ2/GĐ3 vô tình đổi số A/B | fingerprint 5 seed là **điều kiện dừng** |
| Safety modality chưa tồn tại | Tới khi có, safety **QUEUE** chứ không PRESENT khi đang lái |
| Scope phình | Mỗi GĐ có điểm dừng an toàn; không bắt đầu GĐ kế khi GĐ trước chưa đạt exit criteria |
| Ngưỡng đặt bằng trực giác | `20′`/`6 thẻ` là baseline đã duyệt (`D-ĐA04-02`); [cadence.py:70-72](src/gsm_core/lifecycle/cadence.py#L70-L72) cấm chỉnh bằng cảm giác. Ngưỡng mới phải là experiment ARM sau shadow |

## 7. Ngoài phạm vi

Không gỡ B6-PARITY (chỉ làm **nhìn thấy được** qua `solver_set` bắt buộc) · không bật LLM trước GĐ6 ·
không đặt số cho `min_expected_impact` · không đổi `min_gap`/ngân sách · không refactor
`trajectory.py`/`hanoi_graph.py` · không tạo microservice (module domain thuần trong `gsm_core`).

## 8. Câu hỏi cần simulation trả lời

Validity hợp lý cho từng solver/topic · tỉ lệ queued hết hạn trước safe transition · tỉ lệ S2 ONLINE
nên im · tỉ lệ agent xong nhưng checkpoint đã superseded · mức giảm call C so với A/B · một primary
card có làm mất recommendation giá trị · priority có gây starvation · ngưỡng impact/confidence nào
giữ value mà giảm noise · intent vs execution lệch bao nhiêu · fairness/herding có regression ·
`displayed` nên là mounted ACK hay cần dwell.
