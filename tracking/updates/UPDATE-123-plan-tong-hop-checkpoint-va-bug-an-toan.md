# UPDATE-123 — Plan tổng hợp AdviceCheckpoint; phát hiện lỗi AN TOÀN `safety` bypass `is_driving`

- **Ngày:** 2026-08-03
- **Người thực hiện:** Khánh (agent), theo yêu cầu Khánh trong hội thoại
- **Loại:** docs (plan) + phát hiện bug an toàn + đính chính
- **TODO liên quan:** `CKPT-A`..`CKPT-F` (GĐ0), `CKPT-P1`..`P6`, `CKPT-MIG`; blocker `B-03`

## Tóm tắt

Hợp nhất plan AdviceCheckpoint của tôi (UPDATE-122) với một plan review độc lập thành **một plan
tổng hợp**, sau khi kiểm chứng **từng luận điểm của cả hai bên bằng code**. Trong quá trình đó:

1. **4/4 phê bình mà bản review nhắm vào plan của tôi đều ĐÚNG** — đã sửa cả trong plan mới lẫn
   trong `findings.md` đã lỡ vào repo.
2. **Phát hiện một lỗi AN TOÀN đang sống, tái lập qua API thật**: `topic=safety` bypass `is_driving`,
   cooldown và ngân sách thẻ.
3. Tìm ra một **ràng buộc thứ tự thi công mà cả hai plan đều bỏ sót**.

**KHÔNG sửa dòng code nào** — Khánh yêu cầu "không code, không refactor ở bước này".

## Chi tiết cập nhật

### 1. 🔴 Lỗi AN TOÀN — `safety` bypass `is_driving` (blocker `B-03`, TODO `CKPT-B`)

[`cadence.py:156`](../../src/gsm_core/lifecycle/cadence.py#L156):

```python
if topic in SAFETY_TOPICS:
    return CadenceVerdict(PRESENT)      # ← đứng TRƯỚC mọi kiểm tra
if is_driving:
    return CadenceVerdict(QUEUE, "unsafe_while_moving")
```

**Không phải mìn ngủ — gọi được ngay.** `topic` là query param chuỗi **tự do, không validate enum**
(`advice.py:153`). Đo thật bằng TestClient trên app thật:

| Gọi | verdict | im lặng | số card |
| --- | --- | --- | --- |
| `topic=brief` + `is_driving=true` | `QUEUE` | có | **0** ✓ đúng |
| `topic=safety` + `is_driving=true` | `PRESENT` | không | **1** 🔴 |
| `topic=safety` + `is_driving=false` | `PRESENT` | không | 1 |

Vì nhánh safety đứng trước MỌI kiểm tra, nó bypass luôn **cooldown** và **ngân sách 6 thẻ/ca** ⇒
`topic=safety` hiện là **cửa sau card không giới hạn khi tài xế đang chạy xe**.

Docstring khai đây là chủ ý ("không bị budget/cooldown/driving chặn") — nhưng chủ ý đó giả định có
**modality khẩn cấp riêng** (âm thanh/haptic) đã duyệt, mà repo **chưa hề có**. Đường duy nhất hiện
có để "cảnh báo an toàn" là card chữ đọc khi đang lái.

**Chưa có hại đã xảy ra** (nội bộ chưa producer nào emit `safety` — đã grep xác nhận), nhưng bề mặt
lỗi client/gọi ngoài đang mở. **Luật tạm đề xuất:** safety **QUEUE** như mọi topic, **kèm validate
`topic` theo enum đóng**. Cần Cường xác nhận — đây là đánh đổi an toàn/kịp thời.

### 2. Plan tổng hợp

`tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md` (ghi đè bản cũ). Lấy **kiến trúc của bản
review** (checkpoint bất biến, 5 identity, `offered` vs `displayed` bằng client ACK, ưu tiên
lexicographic, tách `topic` khỏi `surface`, normalizer per-solver) + **tính cụ thể của bản tôi**
(output trước/sau thật, bug tái lập, bất biến cấu trúc).

**Phân kỳ đổi lớn nhất:** tách **GĐ0 = 6 việc độc lập làm được ngay**, không phụ thuộc kiến trúc
checkpoint (`CKPT-A`..`F`). Cả hai plan cũ đều chôn những việc này sau nhiều tầng, trong khi chúng
đang ảnh hưởng thật. Mỗi giai đoạn có **điểm dừng an toàn**.

### 3. Đính chính plan của TÔI — 4/4 phê bình đều đúng

| Sai | Sự thật đã kiểm |
| --- | --- |
| `valid_until = 30′` | **Ba** số khác nhau bị tôi gộp: `interval_min:30` (polling) · `bucket_min:60` (cửa sổ khuyến nghị S2, `configs/pilot_dongda.yaml:387`) · `DECISION_BUCKET_MIN:30` (lưới định danh). Đúng: **normalizer từng solver tự cấp** |
| "cả hai đường gate TRƯỚC solver" | **Sai với S1/S7.** `check_bonus_gate` → `_advice_would_help` (653) → `bonus_feasibility.solve()` chạy ở đó, **rồi mới** `cadence_allows` (666). Và [:659-665](../../src/gsm_sim/advice_bridge.py#L659-L665) ghi rõ là **cố ý** (hỏi nhịp sớm ⇒ **63%** lần gọi sinh event nén MA) ⇒ **không được ép cadence lên trước** |
| verifier sau khi nối agent (`findings.md` §10) | Thứ tự đúng là **verifier trước** — nối agent rồi mới dựng lan can là mở đúng cửa mình định khoá |
| agent trả `action_type` rồi verifier kiểm | Yếu: để lớp lỗi tồn tại rồi mới bắt. Đúng hơn: **loại bằng cấu trúc** — agent không phát ngôn action/window/số/nguồn; action do **code** render |

Cả bốn đã đính chính **tại chỗ** trong `findings.md` (không xoá bản cũ, gắn banner 🔴 + lý do).

### 4. Ràng buộc thứ tự cả hai plan bỏ sót

[`event_log.append()` validate qua `SchemaRegistry` **trước khi ghi**](../../src/gsm_core/lifecycle/event_log.py#L123),
và `event_type` là **enum đóng 7 giá trị**, schema `additionalProperties:false`.

⇒ Mọi event type mới (`queued/ready/generated/offered`) **bị từ chối lúc ghi** cho tới khi schema lên
phiên bản. **Schema phải đi trước — ràng buộc cứng, không phải lựa chọn thứ tự.**

### 5. Đính chính plan REVIEW — 2 điểm

- **`advice_followed 19` cạnh `advice_given 1187` gây hiểu nhầm thành adherence 1,6%.**
  [`world.py:840`](../../src/gsm_sim/world.py#L840) chỉ log `followed` khi `mapped_action != action`
  — tức **chỉ khi advice ĐỔI được hành vi**. Nghe theo mà trùng bản năng thì không có event. Đây
  đúng họ "mẫu số hỏng" mà ĐÍNH CHÍNH 2026-07-30 cảnh báo.
- **"backend TestClient bị treo"** — ở máy này **66 passed / 10s**. Giới hạn môi trường của họ, không
  phải repo.

### 6. Claim của bản review đã xác nhận ĐÚNG

264 `advice_rest_veto` dù `advice.enabled=False` (**khớp chính xác**, tổng 6.391 events, seed 1000) ·
`sim.py` gom `advice_*` thành event "advice" cho tài xế · safety bypass (§1) · QUEUE vi phạm contract
**đúng 4 lỗi** · Flutter hard-code — **và tệ hơn mô tả**: "Vincom Đồng Khởi"/"Q.1" là **TP.HCM**
trong khi pilot là **Đống Đa, Hà Nội**, lại không nhãn mock (vi phạm CLAUDE.md §5).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/PLAN-2026-08-03-advice-checkpoint-agent-flow.md` | ghi đè | Plan tổng hợp thay bản cũ |
| `research/audit/2026-08-03-advice-checkpoint/findings.md` | sửa | 4 đính chính tại chỗ (F14, §6 luận cứ, §7 schema+contract, §8 bảng, §10 kế hoạch → SUPERSEDED) |
| `tracking/TODO.md` | sửa | `CKPT-00..05` → SUPERSEDED; thêm `CKPT-A..F`, `P1..P6`, `MIG` |
| `tracking/PENDING-REVIEW.md` | sửa | Thêm blocker **`B-03 / SAFETY-DRIVING`** |
| `tracking/updates/UPDATE-123-*.md` | tạo | File này |

**KHÔNG có file code nào bị sửa.**

## Docs đã cập nhật kèm theo

SCOPE/DEFERRED/USER_STORIES: không đổi. TODO / PENDING-REVIEW / PLAN / findings: có (bảng trên).

## Assumptions và evidence

| Claim | Nhãn | Bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `topic=safety`+driving trả card | `OBSERVED-CODE` (**tái lập qua API thật**) | TestClient trên `app.main:app`, bảng §1 | **Rất cao** | — |
| `topic` không validate enum | `OBSERVED-CODE` | `advice.py:153` `topic: str = Query(...)` | Rất cao | — |
| Nội bộ chưa producer nào emit `safety` | `OBSERVED-CODE` | grep `"safety"` toàn `src/`+`ui/` = rỗng | Cao | Nếu sai ⇒ lỗi đã gây hại thật, mức độ tăng |
| S1/S7 solve trước cadence | `OBSERVED-CODE` | `advice_bridge.py:653,666,735` | Cao | — |
| `append()` validate trước khi ghi | `OBSERVED-CODE` | `event_log.py:123` | Cao | Nếu sai, GĐ1 không cần đi trước |
| 264 `advice_rest_veto` khi advice tắt | `OBSERVED-CODE` (chạy thật) | `run_once(seed=1000)`, khớp số của plan review | Cao | — |
| `valid_until` per-solver là đúng | `ASSUMPTION` | Suy từ `bucket_min:60`; **chưa đo** advice sống bao lâu thật | **Thấp** | Advice hết hạn sớm/muộn — phải đo ở GĐ2 |

## Kiểm chứng

- **Chạy thật:** `run_once(cfg, seed=1000)` → 6.391 events / 264 `advice_rest_veto` với
  `advice.enabled=False`. TestClient 3 tổ hợp `topic`×`is_driving` (bảng §1).
  `pytest -q ui/backend/tests` → **66 passed / 10s**.
- **Đọc + trích dẫn có path:line:** `cadence.py`, `advice_bridge.py`, `world.py`, `templates.py`,
  `context_pack.py`, `composer.py`, `verifier.py`, `event_log.py`, `projections.py`,
  `schema_registry.py`, `upcasters.py`, `advice.py`, `sim.py`, `cards.js`, `home_screen.dart`,
  `ui/contracts/advice.json`, `configs/pilot_dongda.yaml`.
- **CHƯA kiểm chứng:** không chạy suite chính (`pytest -q`) vì không sửa code — baseline gần nhất
  UPDATE-121: 935+4skip. Chưa đo tần suất `BUG-F2-NOW` trên toàn bộ ca. Chưa đo `valid_until` hợp lý.

### Seeds và scenarios

| Run | Seed | Kết quả | Chưa kiểm chứng |
| --- | --- | --- | --- |
| `run_once` | 1000 | 6.391 events, 264 rest_veto (advice OFF) | mới 1 seed — chưa quét nhiều seed |
| TestClient advice API | — (deterministic) | safety bypass tái lập 1/1 | chưa thử qua HTTP server thật (mới TestClient) |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** docs-only, không sửa code ⇒ chưa có gì đổi trên màn hình. Bảng trước/sau ở PLAN §1 là
  **thiết kế mục tiêu**. Khi thi công `CKPT-A`/`CKPT-E`/GĐ3 sẽ có visual gate thật.

## Adversarial self-review / flaws found

1. **Tôi đã suýt ghi một câu quá nhẹ vào repo.** Bản đầu của mục `B-03` viết *"chưa gây hại thực tế
   vì chưa có producer — nhưng nó là mìn"*. Kiểm tiếp thì thấy `topic` **không validate enum** và
   API trả card thật ⇒ nó **gọi được ngay**, không phải mìn ngủ. Đã sửa trước khi để nguyên. Bài
   học: "chưa có producer nội bộ" ≠ "không tới được".
2. **Tôi có đang tự tâng bốc khi nói 4/4 phê bình đều đúng không?** Đã kiểm từng cái bằng code chứ
   không gật: phê bình 1 (3 con số), 2 (`:653` vs `:666`), 3 (thứ tự trong `findings.md`), 4 (lập
   luận cấu trúc). Ngược lại tôi cũng tìm được **2 lỗi của họ** (§5) — không phải nhận hết về mình.
3. **Assumption yếu nhất:** `valid_until` per-solver. Đã bỏ hằng số 30′ sai, nhưng cái thay thế vẫn
   **chưa được đo**. Cố tình không đặt số mới.
4. **Rủi ro chưa ai giải, đã ghi thành `CKPT-MIG`:** overload `decision_id` = `checkpoint_id` trên
   dữ liệu đang có; `adherence_view` khoá trên field này. **Chặn `CKPT-P2`.**
5. **Display ACK làm đứt gãy metric:** `displayed` under-count khi ACK rớt ⇒ số trước/sau GĐ3 **không
   so trực tiếp được**. Đã ghi vào PLAN §GĐ3 như mốc đứt gãy, không phải chú thích nhỏ.
6. **Baseline đã so:** kết luận "hai nửa gương nhau" (UPDATE-121) và kết luận của plan review độc lập
   khớp nhau ở phần lớn phát hiện dù hai đường điều tra khác nhau — tăng độ tin.
7. **Rủi ro quy mô:** GĐ1–GĐ6 là công trình lớn. Đã đặt **điểm dừng an toàn** mỗi giai đoạn + điều
   kiện ra rõ ràng, nhưng **chưa có ước lượng công sức** — nếu Cường/Khánh cần, phải bổ sung.

## Expansion checkpoint (T-039)

1. **Schema**: 5 schema mới thiết kế ở PLAN §GĐ1 (`advice_lifecycle_event@1.1.0`,
   `driver_state_snapshot`, `advice_checkpoint`, `agent_presentation_input/output`) — **chưa tạo**.
2. **Bài toán tối ưu**: "chọn advice nào trong ngân sách 6 thẻ/ca" là **knapsack theo ca** nếu thêm
   `min_expected_impact` — ghi để sau.
3. **Tính năng**: nhãn "còn hiệu lực tới HH:MM" (PLAN §1); execution link mở đường đo intent vs thực tế.

## Follow-up / defer phát sinh

- **`CKPT-MIG`** (MỚI) — migration `decision_id`→`checkpoint_id`, **chặn `CKPT-P2`**.
- **`B-03`** cần Cường xác nhận luật tạm cho safety (đánh đổi an toàn, không phải kỹ thuật thuần).
- **Đo tần suất `BUG-F2-NOW`** — quét % ca có `schedule[0].action ≠ next_action.action`; làm cùng `CKPT-A`.
- **Nợ đọc còn nguyên từ UPDATE-121:** `templates.py` nhánh F0/F1/F3 chưa soi kỹ như F2 — **có thể
  cùng lỗi**; `episode_store.py` (có cache 6h nhưng pipeline không dùng) chưa kiểm.
