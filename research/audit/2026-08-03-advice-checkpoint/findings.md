# Audit: cơ chế AdviceCheckpoint và vị trí tích hợp Agent

- **Ngày:** 2026-08-03 · **Người thực hiện:** Khánh (agent) · **Loại:** audit code (research)
- **Trạng thái:** nghiên cứu, **CHƯA code**. Mọi kết luận kiểm bằng code thật (path + line).
- **UPDATE đi kèm:** `UPDATE-121`

> **Câu hỏi gốc:** solver chạy ≠ phải làm phiền tài xế. Cần cơ chế quyết định *kết quả solver nào
> đáng đưa cho tài xế* và *khi nào gọi agent*.

---

## 0. Kết luận một dòng

Repo **đã có ~70% cơ chế này**, nhưng nó **bị chẻ đôi thành hai nửa không nối được**, và hai nửa ấy
là **ảnh gương lỗi của nhau**. Đây không phải bài toán "xây AdviceCheckpoint từ đầu" mà là **hợp
nhất hai nửa đã tồn tại + nối agent vào đúng một chỗ**.

| | SIM (`gsm_sim`) | SẢN PHẨM (`ui/backend` + `ui/web`) |
|---|---|---|
| Solver chạy | S2 `shift_dp`, `idle_reduction`, `capacity_alloc`, `bonus_feasibility` | **chỉ S1** `bonus_feasibility` |
| Emit `decided` | ✅ có | ❌ **không bao giờ** |
| Emit `displayed` | ❌ không (`display_id`=null theo schema) | ✅ có |
| Gọi Agent/LLM | ❌ **không bao giờ** | ❌ **cũng không** |

---

## 1. Flow THỰC TẾ hiện tại

### 1a. Đường SIM (trưởng thành, nhiều lan can)

```
World._idle_loop  (src/gsm_sim/world.py:770-880)
  │  choose_idle_action()   ← bản năng chạy TRƯỚC, CỐ Ý (giữ CRN cho A/B)
  ├─ check_bonus_gate()     → log advice_bonus_gate    [kênh accept_lift]
  ├─ check_shift_extend()   → log advice_shift_extend  [kênh shift_extend]
  └─ AdviceActionBridge.consult()            (advice_bridge.py:575)
       ├─ covers(actor)? ch_shift_plan bật?              → None
       ├─ due(actor)?     ← interval_min polling gate    (advice_bridge.py:457)
       ├─ cadence_allows() → cadence.evaluate()          (cadence.py:146)
       │       PRESENT | QUEUE | SUPPRESS + typed reason
       ├─ build_shift_plan_input()   ← StateSnapshot     (advice_bridge.py:465)
       ├─ shift_dp.solve(spi, policy, solver_params)     (advice_bridge.py:587)
       ├─ solver_action = schedule[0].action   ← BẪY 1 đã tránh
       ├─ coin_follows() → adherence_coin(seed, decision_id, material_revision)
       └─ BridgedAdvice → world log advice_given / advice_followed / advice_suppressed
                          + decision_id = (driver, channel, bucket 30′)
```

### 1b. Đường SẢN PHẨM (mỏng hơn nhiều)

```
cards.js nudge({isDriving})                  (ui/web/js/cards.js:114-135)
  └─ GET /api/v1/advice?...&is_driving        (ui/backend/app/routers/advice.py:148)
       ├─ shift_phase() → phase
       ├─ cadence.evaluate(topic, now, phase, mem, is_driving)   ← CÙNG luật với sim ✅
       │       ≠ PRESENT → _note_suppressed() → emit `suppressed` → trả silent
       └─ PRESENT → advisor.advice()          (adapters/advisor.py:178)
                      └─ bonus_feasibility.solve()   ← CHỈ S1
                    → _note_shown() → emit `displayed`
```

### 1c. Đường AGENT (tồn tại nhưng **mồ côi**)

```
AdvisorPipeline.handle(req, solver_reports)   (src/gsm_core/advisor/pipeline.py:59)
  → route → PolicyKB → build_context_pack → Composer(LLM|template)
  → Verifier (quyền veto) → safe_degrade nếu fail 2 lần → episode store
```

**Không đường sản phẩm nào gọi nó.** Caller duy nhất: 11 file test + `scripts/smoke_advisor_live.py`.
Đã loại trừ dynamic import (`grep importlib|__import__|getattr` trên `src/gsm_sim/` + `ui/backend/app/`
= **rỗng**). Backend **có** import `gsm_core.advisor.verifier` (`adapters/advisor.py:16`) — tức nó tái
dùng *guardrail* nhưng bỏ qua *composer/agent*.

---

## 2. FACT / PARTIAL / GAP / BUG-RISK

### FACT — đã tồn tại và chạy được

| # | Sự thật | Bằng chứng |
|---|---|---|
| F1 | `AdviceCadencePolicy` hoàn chỉnh: PRESENT/QUEUE/SUPPRESS + typed reason + `next_eligible_min` | `cadence.py:146-169` |
| F2 | Ưu tiên safety > còn lại; safety không bị budget/cooldown/driving chặn | `cadence.py:54,156-157` |
| F3 | Cooldown theo topic + ngân sách ≤6 proactive/ca + dismissed-trong-pha | `cadence.py:160-168` |
| F4 | Pha ca theo **tỉ lệ** thời lượng (không wall-clock cứng) | `cadence.py:129-143` |
| F5 | `decision_id` = (driver, channel, bucket 30′) — deterministic, join được | `world.py:183-199` |
| F6 | `adherence_coin` = hàm THUẦN của (seed, decision_id, material_revision) — diệt washout D-A3-01 | `cadence.py:172-181` |
| F7 | **BẪY 1 đã tránh**: hành động tức thời = `schedule[0]`, `next_action` chỉ để GIẢI THÍCH | `advice_bridge.py:19-22`, `:594` |
| F8 | **BẪY 2 đã tránh**: forecast từ belief cá nhân, không đọc `world.orders` (không rò tương lai) | `advice_bridge.py:24-27` |
| F9 | Schema lifecycle có **7 event_type** + tách 3 tầng ID (`decision_id`/`display_id`/`event_id`) | `schemas/advisor/advice_lifecycle_event.schema.json` |
| **F10** | **Máy trạng thái lifecycle ĐÃ TỒN TẠI và ĐÃ xử lý đủ 7 state** (gồm `superseded`/`expired`), replay-idempotent | `projections.py:64-95`; `_TERMINAL` tại `:21` |
| F11 | Event log append-only, idempotent; projections là MỘT luật dùng chung sim + UI | `lifecycle/event_log.py`, `projections.py` |
| F12 | Verifier có quyền veto + `safe_degrade` fail-closed (thà im hơn nói sai) | `pipeline.py:136-164` |
| F13 | `is_driving` **đã nối thật** client→backend→cadence (không còn chặn ở client) | `cards.js:125` → `advice.py:152` → `:168` |
| ~~F14~~ | 🔴 **ĐÍNH CHÍNH 2026-08-03 (UPDATE-123) — phát biểu cũ SAI:** *"Cả hai đường đều gate TRƯỚC khi chạy solver"*. **Chỉ đúng với S2 `consult` (`advice_bridge.py:578-581`) và đường sản phẩm (`advice.py:166-178`).** SAI với S1 và S7: `check_bonus_gate` gọi `_advice_would_help` (dòng 653) → **`bonus_feasibility.solve()` chạy ở đó**, RỒI mới tới `cadence_allows` (dòng 666); S7 `rest_window_hour` gọi `idle_reduction.solve()` (dòng 735) tương tự. Và đây là **CỐ Ý**: [`advice_bridge.py:659-665`](../../../src/gsm_sim/advice_bridge.py#L659-L665) ghi rõ hỏi nhịp sớm làm **63% lần gọi** sinh event nén MA. ⇒ **Không được "chuẩn hoá" bằng cách ép cadence lên trước** — sẽ tái tạo đúng lỗi đã sửa | `advice_bridge.py:653,666,735` |
| F15 | Ranh giới sim↔sản phẩm có test khoá: sim không dùng `dismissed_for_window` | `cadence.py:30-34` |
| F16 | Backend đã có guardrail riêng: card không qua verifier thì KHÔNG được trả | `adapters/advisor.py:282-320` |

### PARTIAL — có dữ liệu nhưng chưa chuẩn hoá

| # | Vấn đề | Bằng chứng |
|---|---|---|
| P1 | **Taxonomy topic chẻ đôi.** Sim: `shift_plan/accept_lift/shift_extend/rest_window/positioning`; sản phẩm: `brief/nudge/recap` + `KIND_TOPIC` map thủ công | `cards.js:35`; `advice_bridge.py:232-235` |
| P2 | `problem_digest` là **văn xuôi**, không phải state có cấu trúc — không tái dựng được input | `solvers/idle_reduction.py:89` |
| P3 | `expiry` chỉ có trong `composed_advice.advice_spec` (output LLM), **không** ở tầng checkpoint | `schemas/advisor/composed_advice.schema.json:79` |
| P4 | `context_revision` có trong schema, mô tả ghi "ĐA-04 material_revision **sẽ** dùng" ⇒ chưa dùng | schema, dòng mô tả |

### GAP — chưa tồn tại

| # | Thiếu gì | Bằng chứng |
|---|---|---|
| **G1** | **Sim chưa bao giờ gọi Agent.** `grep gsm_core.advisor src/gsm_sim/` = rỗng | đã chạy, 0 kết quả |
| **G2** | **Sản phẩm cũng chưa gọi `AdvisorPipeline`** (chỉ dùng `verifier` rời) | grep toàn repo + `adapters/advisor.py:16` |
| **G3** | **`superseded` / `expired` chưa bao giờ được EMIT cho advice.** ⚠ Không phải "enum chết": **consumer đã sẵn sàng** (F10), chỉ **thiếu producer**. Mọi hit `expired` hiện tại là `order_expired` — khái niệm KHÁC | `world.py:471,536-543` vs `projections.py:21` |
| **G4** | **Không có validity window ở tầng checkpoint** — advice không biết mình hết hạn lúc nào | không có `valid_until`/`ttl` ở tầng advice |
| **G5** | **StateSnapshot không được lưu.** `spi` dựng → truyền solver → **vứt** ⇒ không trả lời được "solver đã thấy state nào" | `advice_bridge.py:584-587` |
| **G6** | **Sản phẩm không emit `decided`** ⇒ `event_adherence` không tồn tại ở sản phẩm | `advice.py:179`; xác nhận bởi ĐÍNH CHÍNH (2b) |
| **G7** | **Sim không emit `displayed`** — schema tự khai `display_id` null cho sim | mô tả `display_id` trong schema |
| **G8** | Không có khái niệm **AdviceCandidate** (thứ bị nén chưa từng thành hình) | — |

### BUG-RISK

| # | Rủi ro | Bằng chứng |
|---|---|---|
| **R1** | **B6-PARITY**: sản phẩm chạy S1, sim chạy S2 ⇒ **A/B đang đo một sản phẩm KHÁC sản phẩm sẽ ship** | `adapters/advisor.py:190`; đang mở là `Q-14` |
| **R2** | **L4-03**: `min_gap=20′` < `bucket=30′`. Đã vá bằng `effective_gap_min=max(...)` nhưng **quyết định chính sách vẫn treo** | `cadence.py:83-104`; `V-21` |
| **R3** | Hai đường đo **hiện không join được** — ĐÍNH CHÍNH 2026-07-30 | `specs/adherence-measurement.md:16-41` |
| **R4** | `expired` trùng tên với `order_expired` ⇒ thêm advice-expiry mà không tách namespace sẽ trộn hai khái niệm trong metric | grep: 4/4 hit hiện là order |
| **R5** | Q-13 chưa chốt: adherence theo DECISION hay EVENT (76,9% vs 53,6%) ⇒ checkpoint kế thừa mơ hồ | `PENDING-REVIEW.md` Q-13 |

---

## 3. Dữ liệu tái sử dụng được (không cần viết lại)

1. `cadence.evaluate()` — trả lời trọn câu hỏi *chọn/ưu tiên/dedup/tần suất/đang-lái/hiệu lực*.
2. `decision_id` (bucket 30′) — khoá join sẵn có, deterministic.
3. `projections.decision_state()` — **máy trạng thái lifecycle đã xong**, nhận đủ 7 state.
4. `advice_lifecycle_event.schema.json` — 7 state đã khai sẵn.
5. `adherence_coin` — mô hình tuân thủ keyed, không re-roll.
6. `AdvisorPipeline` + `Verifier` + `safe_degrade` — tầng agent **đã xây xong**, chỉ chưa ai nối.
7. `build_shift_plan_input()` — StateSnapshot **đã được dựng**, chỉ chưa được lưu.

## 4. Dữ liệu đang bị mất giữa các tầng

| Mất ở đâu | Mất gì | Hệ quả |
|---|---|---|
| `consult()` sau khi solve | toàn bộ `spi` (StateSnapshot) | không tái dựng được quyết định (G5) |
| sim → event log | bước `displayed` | không biết tài xế có thật sự thấy (G7) |
| sản phẩm → event log | bước `decided` | không có mẫu số event (G6) |
| solver → agent | `SolverReport` đầy đủ | agent chưa từng nhận (G1/G2) |
| checkpoint → UI | validity window | UI không biết advice hết hạn (G4) |

---

## 5. Ba phương án chuẩn hoá checkpoint

### PA-A — "Checkpoint = view suy ra từ event log"
Không thêm bảng. Chỉ **bổ sung producer** cho `superseded`/`expired`; consumer đã sẵn (F10).

- ➕ **Rẻ hơn đánh giá ban đầu của tôi** — máy trạng thái không cần xây.
- ➕ Không rủi ro schema; tận dụng `projections.py`.
- ➖ Không giải G5 (state vẫn mất) và G4 (không validity).
- ➖ Không ép được hai đường emit đủ event ⇒ R3 còn nguyên.

### PA-B — "Checkpoint là entity thật, event log là nhật ký của nó" ⭐ **khuyến nghị**
Thêm **một** record `advice_checkpoint@1.0.0` (qua `schema_registry` sẵn có), sinh **một lần tại thời
điểm quyết định**, ở **cả hai** đường.

- ➕ Giải G4, G5, G6, G7, G8 cùng lúc bằng một khái niệm.
- ➕ Ép hai đường hội tụ ⇒ cùng emit `decided` ⇒ join được (gỡ R3).
- ➕ Chỗ neo tự nhiên để nối agent mà **không đụng solver**.
- ➖ Phải thêm schema + upcaster; sửa 2 chỗ ghi (sim + backend).
- ➖ Không tự giải R1 — nhưng làm R1 **nhìn thấy được** (mỗi checkpoint khai rõ solver nào).

### PA-C — "Sinh sẵn toàn bộ khi chạy sim, UI chỉ replay"
- ➕ Reproducible tuyệt đối; 0 latency; đánh giá nhiều agent trên cùng trajectory rất dễ.
- ➖ **Không dùng được cho sản phẩm thật** ⇒ lại tạo đường khác đường ship = B6-PARITY nhân đôi.
- ➖ Chỉ hợp làm **chế độ phụ cho nghiên cứu**.

**Đề xuất: PA-B chính + PA-C làm chế độ replay cho A/B agent (bật/tắt được).**
Nếu ưu tiên rẻ/nhanh trước: **PA-A như bước đệm của PA-B** (không mâu thuẫn — PA-A là tập con).

---

## 6. Thời điểm gọi Agent

| PA | Số lần gọi | Chất lượng | Latency | Reproducible | Rủi ro hết hạn |
|---|---|---|---|---|---|
| A. sau mỗi lần solver chạy | rất cao | thừa | — | kém | cao |
| B. khi tạo AdviceCandidate | cao | thừa (candidate bị nén vẫn tốn) | — | kém | trung bình |
| **C. chỉ khi checkpoint qua policy + còn hiệu lực + sắp hiển thị** ⭐ | **thấp nhất** | đủ | có → cần cache/fallback | tốt | **thấp nhất** |
| D. sinh trước khi sim, UI replay | thấp | đủ | 0 | tuyệt đối | không có |

**Khuyến nghị: C cho sản phẩm, D cho sim/A-B.** Lý do:

- 🔴 **ĐÍNH CHÍNH 2026-08-03:** luận cứ cũ *"repo đã gate trước khi solve ở cả hai đường (F14)"*
  dựng trên tiền đề **SAI** (xem F14 đã đính chính). Kết luận **vẫn giữ**, nhưng lý do đúng là:
  agent được gọi ở **sau khi candidate đã thành hình và qua policy**, bất kể thứ tự
  cadence↔solver của từng kênh. Checkpoint là chỗ neo chung, nên nó dung được **cả hai** kiểu
  thứ tự mà không cần đụng vào thứ tự nào.
- `AdvisorPipeline.handle(req, solver_reports)` đã nhận reports từ caller ⇒ **đúng chữ ký cần**.
- Fallback sẵn có, fail-closed: `llm_mode="off"` → template; verify fail 2 lần → `safe_degrade`.
- Sim dùng D ⇒ A/B **không bị nhiễu bởi latency/lỗi LLM**, vẫn đo đúng nội dung sẽ ship.

⚠ **Ràng buộc bắt buộc:** **một pipeline, hai thời điểm gọi.** Chọn C mà quên sim ⇒ lặp lại đúng
B6-PARITY ở tầng agent.

---

## 7. Schema minh hoạ (mức thiết kế, chưa implement)

```jsonc
// advice_checkpoint@1.0.0 — sinh MỘT LẦN tại thời điểm quyết định
{
  "checkpoint_id": "ckpt-…",
  "decision_id": "…",            // TÁI DÙNG khoá sẵn có (world.py:183)
  "origin": "sim | ui | pipeline",
  "topic": "shift_plan | accept_lift | …",   // taxonomy HỢP NHẤT (giải P1)

  "trigger": { "kind": "poll_due | soc_threshold | trip_completed | shift_late",
               "at_min": 540.0 },

  "state_snapshot_ref": {        // giải G5 — chỉ ref + digest, KHÔNG nhúng cả state
    "schema": "shift_plan_input@1.1.0", "digest": "sha256:…", "stored_at": "…" },

  "solver_decision": {
    "solver": "S2",              // khai rõ ⇒ B6-PARITY nhìn thấy được (R1)
    "action_now": "REST",        // = schedule[0], KHÔNG phải next_action (F7)
    "bucket_now": "2026-07-01T09:00:00+07:00",
    "plan_next_action": "SWAP",  // chỉ để GIẢI THÍCH
    "plan_next_bucket": "…", "confidence": 0.72 },

  "validity": {                  // giải G4
    "valid_from_min": 540.0,
    "valid_until_min": 600.0,    // 🔴 ĐÍNH CHÍNH: bản cũ ghi 570.0 (=30′) là SAI — nhầm
                                 // DECISION_BUCKET_MIN=30 (lưới ĐỊNH DANH) với bucket_min=60
                                 // (cửa sổ KHUYẾN NGHỊ của S2, configs/pilot_dongda.yaml:387).
                                 // Đúng: valid_until do NORMALIZER của từng solver cấp.
    "expiry_reason": null },     // expired | superseded | null

  "policy_verdict": {            // KẾT QUẢ của cadence.evaluate — KHÔNG tính lại
    "verdict": "PRESENT | QUEUE | SUPPRESS",
    "reason_code": "topic_cooldown | …", "next_eligible_min": 560.0 },

  "agent": { "called": false, "advice_id": null,
             "fallback_used": null, "verify_passed": null },

  "material_revision": "…",      // NỘI DUNG khuyên — đổi thì coin mới (F6)
  "source": "MOCK", "schema_version": "1.0.0"
}
```

**Contract agent (input/output tối thiểu):**

- **Input**: `solver_decision` + `validity` + `numbers_registry` (có sẵn ở `context_pack`) + topic.
  **Không** đưa state thô — agent không được tự tính lại.
- **Output**: 🔴 **ĐÍNH CHÍNH 2026-08-03.** Bản cũ cho agent trả `{action_chính, lý_do, thời_hạn}`
  rồi verifier kiểm `action_type` có khớp không. **Cách đó yếu**: nó để lớp lỗi tồn tại rồi mới bắt.
  **Đúng hơn — loại bằng CẤU TRÚC:** agent **không phát ngôn** action/window/expiry/zone/số/nguồn;
  nó chỉ trả `reason_template` + `why_template` + `used_fact_ids`/`used_number_ids`/`used_caveat_ids`.
  **Action label do CODE render** từ checkpoint canonical, UI ghép lại. Không có gì để kiểm nghĩa là
  không có gì hỏng được.
- **Validate**: `verifier.py` đã chặn số bịa + có `safe_degrade`. Bổ sung: checkpoint ID khớp · chỉ
  dùng ID có trong input · giới hạn độ dài theo surface · 1 repair rồi fallback template.
  ⚠ **Verifier phải xong TRƯỚC khi nối agent** (xem §10 đã đính chính), không phải sau.

---

## 8. Chính sách chọn / ưu tiên / dedup / tần suất

Phần lớn đã có (F1–F4). Chỉ cần bổ sung 3 thứ — **cả ba là GIẢ THUYẾT cần sim kiểm chứng**:

| Bổ sung | Giả thuyết ban đầu | Vì sao không chốt cứng |
|---|---|---|
| `min_expected_impact` | ngưỡng theo VND/ca, **chưa có số** | Tiền lệ Q-09: nhịp nói "mua công bằng bằng tiền" — phải đo |
| `valid_until` | 🔴 **ĐÍNH CHÍNH**: bản cũ ghi "= 1 bucket (30′)" — **SAI**, nhầm lưới định danh (30′) với cửa sổ khuyến nghị S2 (**60′**, `configs/pilot_dongda.yaml:387`). Đúng: **normalizer từng solver tự cấp** từ bucket + freshness + shift end | Ba số khác nhau cùng tồn tại: `interval_min:30` (polling) · `bucket_min:60` (cửa sổ) · `DECISION_BUCKET_MIN:30` (định danh) |
| `supersede` khi `material_revision` đổi | thay vì chồng card | Đúng ngữ nghĩa "một quyết định = một lần nói" (F6) |

⚠ **KHÔNG đề xuất con số cooldown mới.** `20′/6 thẻ` là baseline Cường duyệt (`D-ĐA04-02`);
`cadence.py:70-72` ghi rõ *"đừng chỉnh mấy số này bằng trực giác"* ⇒ thay đổi phải là experiment ARM.

---

## 9. Rủi ro & câu hỏi mở cần kiểm chứng bằng simulation

1. **R1/Q-14 (B6-PARITY)** — gỡ **trước hay sau** checkpoint? Checkpoint làm nó *nhìn thấy được*
   nhưng không tự chữa. Câu hỏi thứ tự roadmap → cần Cường.
2. **R5/Q-13** — adherence theo DECISION hay EVENT? Chưa chốt ⇒ checkpoint kế thừa mơ hồ.
3. **R2/V-21** — `min_gap` 20′ vs bucket 30′: vá kỹ thuật đã có, quyết định chính sách còn treo.
4. `valid_until` = 1 bucket có hợp lý? Cần đo tỉ lệ advice hết hạn trước khi hiển thị.
5. Gọi agent ở PA-C có làm tăng tỉ lệ hết hạn? (latency LLM ăn vào validity window)
6. `min_expected_impact` có làm advisor im quá mức? (bài học V-18: "tài xế thấy bị bỏ rơi")

---

## 10. Kế hoạch theo giai đoạn (chưa code)

> 🔴 **PHẦN NÀY ĐÃ BỊ THAY THẾ 2026-08-03 (UPDATE-123).** Kế hoạch hiện hành:
> **[`tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md`](../../../tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md)**
> — bản tổng hợp sau khi đối chiếu với một plan review độc lập và kiểm chứng lại bằng code.
>
> **Hai lỗi của bảng dưới:**
> 1. **Thứ tự GĐ4/GĐ5 SAI** — verifier action-boundary phải xong **TRƯỚC** khi nối agent, không phải
>    sau. Nối agent trước rồi mới dựng lan can là mở đúng cửa mình định khoá.
> 2. **"GĐ0 = chờ Cường chốt Q-13/Q-14/V-21" đã lỗi thời** — UPDATE-122 §3 cho thấy cả ba tự giải;
>    và bản tổng hợp định nghĩa lại GĐ0 thành **6 việc độc lập làm được ngay** (gồm một **lỗi an
>    toàn**: `safety` bypass cả `is_driving`).
>
> Giữ bảng cũ để đối chiếu, KHÔNG dùng để thi công.

| GĐ | Việc | Phụ thuộc |
|---|---|---|
| **GĐ0** | ~~Cường chốt Q-13, Q-14, V-21~~ (đã tự giải — UPDATE-122 §3) | ~~chặn~~ |
| **GĐ1** | Hợp nhất taxonomy topic (P1) | không phụ thuộc GĐ0 |
| **GĐ2** | Sản phẩm emit `decided` (G6) | ĐÍNH CHÍNH (2b) đã chỉ đích danh |
| **GĐ3** | Dựng `advice_checkpoint@1.0.0` (PA-B) | GĐ1 + GĐ2 |
| **GĐ4** | ~~Nối agent~~ ⚠ **đảo thứ tự** — xem cảnh báo trên | GĐ3 |
| **GĐ5** | ~~Luật verifier~~ ⚠ **phải chạy TRƯỚC GĐ4** | — |

Kiểm chứng: ≥5 seed cho hành vi, ≥30 seed nếu đụng phân phối (CLAUDE.md §4b).

---

## 11. Giới hạn của chính báo cáo này

- **Chưa chạy simulation** để kiểm chứng bất kỳ giả thuyết nào ở §8 — mọi số ở đó là `ASSUMPTION`.
- Kết luận "AdvisorPipeline mồ côi" dựa trên grep tĩnh **+ đã loại trừ dynamic import** (kiểm
  `importlib`/`__import__`/`getattr` = rỗng) ⇒ confidence **cao**, nhưng không phải chứng minh hình thức.
- **Đã tự sửa một đánh giá trong quá trình audit:** bản nháp đầu xếp PA-A là "không giải được gì mấy"
  vì tôi chưa đọc `projections.decision_state()`. Sau khi đọc, máy trạng thái lifecycle **đã tồn tại
  và đủ 7 state** ⇒ PA-A rẻ hơn nhiều so với đánh giá ban đầu, và G3 được phát biểu lại chính xác là
  *"consumer sẵn sàng, thiếu producer"*. Ghi lại để người sau không lặp sai lầm đọc thiếu.
- `templates.py` (319 dòng) mới đọc lướt — chi tiết render có thể ảnh hưởng contract agent ở §7.
- Chưa kiểm `episode_store.py` xem có thể tái dùng làm nơi lưu StateSnapshot (G5) hay không.
