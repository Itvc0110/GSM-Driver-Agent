# UPDATE-137 — QĐ-4: hợp nhất taxonomy `topic`, bịt đường ghi THỨ TƯ (AdviceCheckpoint v2)

- **Ngày:** 2026-08-04
- **Người thực hiện:** AI agent, theo yêu cầu Cường (*"(b), viết docs lại cẩn thận để khi Khánh chạm code thì phải đọc qua"* → *"làm tiếp luôn đi"*)
- **Loại:** fix (ranh giới sản phẩm) + docs
- **TODO / User story liên quan:** QĐ-1/QĐ-4 (`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b) · `D-QD4-01` · `D-QD4-02` · nối tiếp UPDATE-135/129

## Tóm tắt

Ranh giới *"khuyên mềm KHÔNG đo mức nghe lời"* được UPDATE-135/129 bịt ở **ba** đường ghi (UI v1 ·
sim · pipeline). Đọc lại logic sau khi rebase lên PR #4 thì lộ ra **đường thứ TƯ** — AdviceCheckpoint
v2 — nằm hoàn toàn ngoài: store riêng, từ vựng `topic` riêng **giao với registry = RỖNG**, và `rest`
được sinh thật. Hệ quả: một checkpoint `rest` nhận được `response: accepted`, tức **trace đồng ý cho
lời khuyên NGHỈ đang được ghi**. Update này thi hành phương án **(b) — hợp nhất** mà Cường chốt:
8 topic v2 + `cadence.SAFETY_TOPICS` nhập registry, `record_response` từ chối `accepted` cho topic
mềm (422), và **bốn cổng** để không ai chạm được vùng này mà không đọc quyết định.

## Chi tiết cập nhật

### Lỗ: cái gì thật sự hỏng, và ở mức nào

Ba sự thật độc lập, mỗi cái tự nó đủ để `classify()` không chạm tới một event nào của v2:

1. **Store riêng** — `advice_checkpoint.py` ghi nguyên văn *"independent from the legacy v1 lifecycle
   store"*; v2 → `CheckpointStore`, còn ranh giới sống ở `AdviceEventLog` → `adherence_view`.
2. **Từ vựng topic riêng** — v2 dùng `bonus_eligibility · energy · rest · shift_boundary ·
   shift_timing · positioning_sim_only · policy_info · safety_reserved`; registry dùng
   `brief · nudge · recap · … · weather · rest_nudge · traffic`. **Giao = ∅.**
3. **`rest` được sinh THẬT** — `checkpoint.py:134`: `if solver == "S7" or code == "REST": return "rest"`.

**Nói cho chính xác về mức độ: hôm nay CHƯA có con số nào sai.** `adherence_view` không bao giờ thấy
event v2 nên không tồn tại tỷ lệ nghe lời nào cho `rest`. **Nhưng cái trace thì đang được ghi.** Dạng
này nguy hiểm hơn một con số sai vì nó **tích luỹ và im lặng**: ngày ai đó viết một hàm adherence
trên `CheckpointStore`, tỷ lệ hiện ra ngay với lịch sử đầy đủ — **không ai phải làm gì sai thêm**.

### Hợp nhất THẨM QUYỀN, không hợp nhất TÊN

Cái phải là MỘT là *nơi quyết định topic nào được đo mức nghe lời*, không phải chuỗi. **Không đổi một
tên nào**: `advice_v2.json` và mọi bản ghi đã lưu giữ nguyên. Đổi tên sẽ phá contract của Khánh và
toàn bộ dữ liệu lịch sử — đắt hơn nhiều so với thứ nó giải quyết.

Phân loại 8 topic v2: **6 kinh tế** (`bonus_eligibility` mốc thưởng · `energy` SWAP/sạc — pin là điều
kiện chạy, không phải sức khoẻ người · `shift_boundary` · `shift_timing` · `positioning_sim_only` ·
`policy_info` trích chính sách, không phải khuyên hành vi) → `MEASURED_TOPICS`; **2 mềm** (`rest` ·
`safety_reserved`) → `SOFT_TOPICS`. Cộng thêm từ vựng **thứ tư** `cadence.SAFETY_TOPICS = {"safety"}`
— cùng khái niệm với `safety_reserved`, hai tên ở hai file, trước nay không ai nối.

### `rest` nhập nhằng — và tôi chọn MỀM có chủ ý, không phải vì chắc chắn

`_topic_for_action` gộp hai khái niệm mà registry vốn tách: `rest_window` (HOÃN nghỉ = đổi **thời
điểm**, không đổi lượng = `C2′`, kinh tế, **được đo**) và `rest_nudge` (GỢI Ý nghỉ, mềm). Từ tên
không phân giải được.

Chọn MỀM vì hai sai **không cùng hạng**: xếp nhầm một lời khuyên kinh tế vào mềm thì **mất một mẫu
số** (mất độ chính xác); xếp nhầm một lời khuyên sức khoẻ vào được-đo thì **phá một ranh giới đã
chốt** (§1.2c). → nợ tách đôi: `D-QD4-01`.

### `dismissed` vẫn nhận — và vì sao đó không phải nửa vời

Chỉ `accepted` bị cấm. `dismissed` mang **hai vai** (§4 văn bản quyết định): *"đừng nhắc nữa"* (nhịp
nói — GIỮ) và *"tôi không đồng ý"* (thước adherence — CẤM). Cường chốt *"giữ nút ẩn, bỏ nút Làm
theo"*: tài xế vẫn tắt được thẻ phiền, nhưng hệ thống không bao giờ suy ra sự đồng thuận từ đó.
`expanded` = *"cho tôi xem vì sao"*, cũng không phải đồng thuận.

### 422 chứ không phải 409 — lớp lỗi RIÊNG

`409 conflict` nghĩa *"trạng thái không cho phép LÚC NÀY"*, hàm ý thử lại có thể được. Đây là ranh
giới **vĩnh viễn không được phép** ⇒ `CheckpointSoftAdviceError` là lớp riêng, map **422**, và
`except` của nó phải đặt **TRƯỚC** `except CheckpointConflictError` vì cả hai cùng kế thừa
`ValueError`. Đặt sai thứ tự thì lỗi ranh giới bị nuốt thành 409 — mũi sever (b) chính là ca đó.

### Fail-closed cả ở tầng GHI — bất nhất tự tìm ra khi tự soi

Bản đầu của cổng dùng `is_soft(topic)`, tức chỉ chặn topic **đã khai là mềm**. Topic **chưa khai**
(`classify() == "unknown"`) đi lọt. Nhưng tầng ĐỌC (`adherence_view`, UPDATE-136) thì **loại** topic
chưa khai — Cường chốt 2026-08-03 *"TREO kết quả, như D-M3-10"*.

⇒ Ranh giới có **hai tiêu chuẩn cho cùng một tình huống**, và cái lỏng hơn luôn là cái quyết định.
Đã sửa: `record_response` nay dùng `classify()` và từ chối **cả** `soft` lẫn `unknown`, với **hai
thông điệp khác nhau** (lẫn chúng sẽ khiến người sửa đi phân loại lại một topic đã đúng thay vì khai
topic mới).

**Đánh đổi đã cân, không phải chọn cho gọn.** Chặn ở đây là lỗi **thấy được** (một cú bấm nhận 422);
cho qua là lỗi **im lặng** — và nếu topic lạ đó hoá ra là lời khuyên sức khoẻ (`fatigue`,
`hydration`…) thì cái im lặng ấy chính là trace đồng thuận QĐ-1 cấm. Hai sai không cùng hạng.

Hai lan can quanh lựa chọn này, để nó không thành hình phạt oan:
- **`dismissed` không bị chặn** cho topic chưa khai — tài xế vẫn tắt được thẻ; hình phạt không rơi
  vào người không gây ra lỗi.
- **`topic is None` (checkpoint không tồn tại) vẫn ra 404**, không bị nuốt thành 422. Lỗi *"không
  tìm thấy"* và lỗi *"không được phép"* phải giữ hai thông điệp, nếu không thì đọc log sẽ tưởng ranh
  giới bắn trong khi thật ra chỉ là gõ nhầm ID.

Cả ba đều có test + sever riêng (mũi h1–h3).

### Bốn cổng, xếp theo thứ tự người sửa code sẽ đụng cái nào trước

| Cổng | Bắn khi |
| --- | --- |
| `test_QD4_PRODUCER_that_cua_v2_khong_sinh_duoc_topic_ngoai_registry` | thêm nhánh `return "<topic mới>"` vào `_topic_for_action` |
| `test_QD4_ghim_khoang_HO_giua_cac_tu_vung_topic` | enum `topic` của `advice_v2.json` thêm/bớt phần tử |
| `test_QD4_buoc2_RANH_GIOI_DA_KIN_tren_ca_bon_tu_vung` | một topic v2/`cadence` không nằm trong registry |
| `ui/backend/tests/test_v2_soft_advice_no_trace.py` | ranh giới ở `record_response`/router bị gỡ hoặc map sai mã |

**Cổng producer tồn tại riêng vì scanner AST có vùng mù thật:** `_scan_topics` bắt `topic="x"`
(kwarg), `{"topic": "x"}` (dict) và `X_TOPICS = (...)` — nó **không nhìn `return "x"`**, mà đó chính
là nơi mọi topic v2 ra đời. Ba cổng kia chỉ đóng vòng khi người thêm topic **cũng** sửa
`advice_v2.json`; ai thêm `return "fatigue"` mà chưa động contract thì lọt cả ba. Cổng producer neo
thẳng vào hàm nên không phụ thuộc thứ tự người ta sửa file.

Cổng `test_QD4_ghim_khoang_HO_…` **đổi vai** trong update này: từ *"ghim khoảng hở đang có"* thành
*"chứng minh ranh giới đã kín"* — vì bước 2 đã xong nên đòi hỏi mạnh hơn là hợp lệ.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/lifecycle/advice_topics.py` | sửa | +8 topic v2 (6 measured, 2 soft) + `safety` của `cadence`; comment giải thích vì sao `rest` là mềm |
| `ui/backend/app/services/advice_checkpoint.py` | sửa | `CheckpointSoftAdviceError` + guard `classify()` trong `record_response` (chặn **cả** `soft` lẫn `unknown`, hai thông điệp khác nhau) |
| `ui/backend/app/routers/advice_v2.py` | sửa | map `CheckpointSoftAdviceError` → 422, đặt TRƯỚC `CheckpointConflictError`, ở **cả hai** endpoint |
| `ui/backend/tests/test_v2_soft_advice_no_trace.py` | **tạo** | 19 test: phân loại · service · fail-closed + hai lan can · HTTP đầu-cuối (thẻ `rest` sinh thật qua `_normalize_with_artifacts`) |
| `tests/test_advice_topic_registry.py` | sửa | +cổng PRODUCER `_topic_for_action`; cổng "đã kín"; `SOFT_MONG_DOI` mở rộng |
| `ui/backend/tests/test_advice_v2_api.py` | sửa | `read_text(encoding="utf-8")` — xem "Adversarial self-review" #4 |
| `ui/contracts/advice_v2.json` | sửa | cảnh báo ranh giới trong `topic.description` |
| `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` | sửa | §6b + tiểu mục "Kết quả thi công" (bảng đổi gì/không đổi gì, 4 cổng, sever 8/8, defer bước 3) |
| `tracking/DEFERRED.md` | sửa | +`D-QD4-01` (tách `rest`), +`D-QD4-02` (bước 3) |
| `specs/adherence-measurement.md` | sửa | §(c)#2 nay có **lý do thứ hai** (ranh giới đạo đức, không chỉ join được) + trạng thái 2026-08-04 |
| `docs/reports/week2/AUDIT-CHECKLIST-cho-Khanh.md` | sửa | **Phần 6** — báo tường minh cho Khánh: mình sửa gì trong PR #4 của bạn, và **3 việc cần bạn** (Flutter không vẽ nút "Làm theo" cho thẻ mềm · kiểm DB v2 cũ · xác nhận `rest` mềm hay kinh tế) |
| `ui/web/tests/cards_soft_gate.mjs` | **tạo** | **`Nợ 7`** — cổng khuyên mềm ở tầng CLIENT, node thuần, **zero dependency** (12 phép kiểm) |
| `tests/test_cards_js_soft_gate.py` | **tạo** | bọc cổng JS vào suite pytest (3 test, gồm test chống rút ruột) |
| `tracking/TODO.md`, `PROJECT-GRAPH.md`, `PENDING-REVIEW.md`, `BOOTSTRAP-SESSION.md` | sửa | `SOFT-ADVICE-03` · node UPDATE-136 (**thiếu**, bổ sung) + node UPDATE-137 · `V-27` · state |

## Docs đã cập nhật kèm theo

- `QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b — thêm mục kết quả thi công + cảnh báo DB cũ.
- `DEFERRED.md` — hai nợ mới với **điều kiện mở lại cụ thể**.
- `TODO.md`, `PROJECT-GRAPH.md`, `PENDING-REVIEW.md` — cập nhật kèm (xem cuối file).
- SCOPE / USER_STORIES / RESEARCH: **không đổi** (ranh giới đã có từ QĐ-1, đây là mở rộng phạm vi
  thi hành sang một đường ghi mới, không phải scope mới).

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| v2 và registry giao nhau = ∅ trước update này | `OBSERVED-CODE` | enum `advice_v2.json` vs `advice_topics.py` bản trước | CAO | nếu sai thì lỗ hẹp hơn báo cáo |
| `rest` được sinh thật, không phải nhánh chết | `OBSERVED-CODE` | `checkpoint.py:134` + test HTTP dựng được thẻ `topic="rest"` qua đường thật | CAO | nếu sai thì đây là lỗ lý thuyết, không phải lỗ đang chạy |
| Chưa có con số adherence nào sai vì lỗ này | `OBSERVED-CODE` | `adherence_view` chỉ đọc `AdviceEventLog`; `CheckpointStore` không có consumer adherence nào | CAO | nếu sai thì có số đã công bố bị nhiễm — phải rà artifact |
| Máy Cường không có DB v2 cũ ⇒ chưa bản ghi nào bị nhiễm | `OBSERVED-CODE` | `Get-ChildItem -Recurse -Filter *.db data` → chỉ `advice_lifecycle.db` | CAO | **chỉ đúng cho máy Cường** — máy Khánh CHƯA KIỂM, ghi trong `D-QD4-02` |
| `rest` của v2 nên là MỀM | `ASSUMPTION` | không phân giải được từ tên; chọn fail-closed | **TRUNG BÌNH** | mất mẫu số của kênh HOÃN nghỉ ở đường v2 → `D-QD4-01` |
| 6 topic v2 còn lại là kinh tế | `ASSUMPTION` | ngữ nghĩa solver (S1 mốc thưởng, SWAP/sạc, END/EXTEND ca) | CAO | nếu `energy` bị coi là sức khoẻ thì phải chuyển sang mềm |

## Kiểm chứng

### Sever-restore THẬT — 13/13 mũi bị bắt

Bốn bước đủ: tiêm vào **file nguồn thật** · chạy `uv run pytest` thật (đúng lệnh đã dùng làm nền —
**không** `python -m pytest`, nó thêm CWD vào `sys.path` và cho kết quả khác) · restore · verify
`sha256`. Script: `scratchpad/sever_qd4_{v2,producer,failclosed}.py`.

| Mũi | Tiêm gì | Kết quả |
| --- | --- | --- |
| a | gỡ nhánh `lop == "soft"` trong `record_response` | **BẮT ĐƯỢC** |
| b | 422 → 409 (ranh giới lẫn vào conflict) | **BẮT ĐƯỢC** |
| b2 | đặt `except CheckpointSoftAdviceError` **sau** `CheckpointConflictError` ⇒ bị nuốt | **BẮT ĐƯỢC** |
| c | rút `rest` khỏi `SOFT_TOPICS` | **BẮT ĐƯỢC** |
| d | rút `safety_reserved` khỏi `SOFT_TOPICS` | **BẮT ĐƯỢC** |
| e | đẩy `energy` khỏi bảng ĐƯỢC ĐO (phá phép đo thay vì ranh giới) | **BẮT ĐƯỢC** |
| f | `is_soft` luôn `False` | **BẮT ĐƯỢC** |
| f2 | `classify` luôn trả `"measured"` — **hàm mà đường v2 thật sự gọi** | **BẮT ĐƯỢC** |
| g1 | thêm `return "fatigue_chua_khai"` ở producer | **BẮT ĐƯỢC** |
| g2 | đổi tên `_topic_for_action` | **BẮT ĐƯỢC** |
| h1 | gỡ nhánh fail-closed (topic chưa khai lại ghi được `accepted`) | **BẮT ĐƯỢC** |
| h2 | fail-closed nuốt luôn `dismissed` (đóng quá tay) | **BẮT ĐƯỢC** |
| h3 | checkpoint không tồn tại bị nuốt thành lỗi ranh giới (404 → 422) | **BẮT ĐƯỢC** |

Ba ghi chú về **cách chọn mũi**, vì chọn sai mũi là cách dễ nhất để có một bảng 13/13 vô nghĩa:

- **e · h2 · h3 canh hướng NGƯỢC.** Một cổng ranh giới cũng hỏng khi nó đóng quá tay: xếp mọi thứ
  vào mềm (phá phép đo), chặn cả `dismissed` (tài xế kẹt với thẻ không tắt được), hoặc nuốt mọi lỗi
  thành 422 (đọc log tưởng ranh giới bắn trong khi chỉ là gõ nhầm ID). Cổng chỉ bắt một hướng là
  cổng nửa vời.
- **f2 tồn tại vì f không đủ.** `record_response` gọi `classify`, **không** gọi `is_soft` — nên mũi f
  một mình chỉ chứng minh registry bị ghim, không chứng minh đường v2 đọc nó. Mũi tiêm phải nhắm
  đúng hàm mà đường đang xét thật sự gọi.
- **Mũi a từng ANCHOR-FAIL và script BÁO RA thay vì tính là "qua".** Sau khi đổi guard từ
  `is_soft(topic)` sang `classify()`, anchor cũ không còn khớp. Script in `✗ ANCHOR KHỚP 0 LẦN` và
  **không** cộng vào điểm — nếu nó im lặng thì tôi đã báo 12/12 trong khi một cổng chưa hề được thử.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `uv run pytest -q` | n/a (deterministic) | toàn `tests/` | **1022 passed · 3 failed · 4 skipped** (22′05″) — 3 F là **có sẵn**, xem dưới | — |
| `uv run pytest -q ui/backend/tests` | n/a | toàn `ui/backend/tests/` | **162 passed** | — |
| `node ui/web/tests/cards_soft_gate.mjs` | n/a | cổng khuyên mềm tầng client | **12/12 xanh** | — |
| `uv run python scratchpad/sever_cards_js.py` | n/a | 6 mũi tiêm vào `cards.js` | 6/6 BẮT ĐƯỢC | — |
| `uv run python scratchpad/sever_qd4_v2.py` | n/a | 8 mũi tiêm | 8/8 BẮT ĐƯỢC | — |
| `uv run python scratchpad/sever_qd4_producer.py` | n/a | 2 mũi tiêm | 2/2 BẮT ĐƯỢC | — |
| `uv run python scratchpad/sever_qd4_failclosed.py` | n/a | 3 mũi tiêm | 3/3 BẮT ĐƯỢC | — |

**Không chạy sim/A-B trong update này** — thay đổi không chạm `world.py`, `parallel.py` hay bất kỳ
động lực nào. `advice_topics.py` chỉ **thêm** khoá, không bớt, nên `classify()` của 5 kênh sim không
đổi ⇒ mọi số A/B đã đo giữ nguyên. (Đây là suy luận từ cấu trúc; nếu muốn bằng chứng đo thì phải
chạy fingerprint per-actor — đã ghi là **chưa làm**.)

### 🔴 Ba test ĐỎ — chứng minh CÓ SẴN, không phải suy đoán

`uv run pytest -q` trả 3 failed. Ba test này nằm trong danh sách `K-01` (đỏ có sẵn sau PR #4), nhưng
**trùng tên không phải bằng chứng** — cycle này có chạm `advice_topics.py` và `projections.py`, hai
file mà cadence/checkpoint đều có thể phụ thuộc. Đã kiểm dứt điểm:

```
git stash push -u                       # cắt toàn bộ 17 file của cycle này
uv run pytest -q <đúng 3 test đó>       # → 3 failed  ⇒ ĐỎ SẴN trên 51e877e
git stash pop                           # khôi phục (đã verify lại 17 file)
```

| Test | Loại |
| --- | --- |
| `tests/test_cadence_policy.py::test_safety_topic_presents_even_while_driving` | **bất đồng CHÍNH SÁCH an toàn**, không phải bug: code + docstring cố ý QUEUE mọi thẻ chữ khi đang lái (kể cả safety), test lại đòi PRESENT. Không tự sửa — đây là quyết định sản phẩm của Khánh |
| `tests/test_checkpoint_trace.py::test_shadow_comparator_ignores_only_diagnostic_metadata` | hạ tầng import (`scripts/` thiếu `__init__.py`) |
| `tests/test_checkpoint_trace.py::test_run_once_wires_shadow_trace_without_changing_semantic_outcomes` | nt |

⇒ **Suite của cycle này KHÔNG thêm một test đỏ nào.** Không tự sửa ba cái đó: chúng thuộc claim của
Khánh, và cái đầu là bất đồng chính sách chứ không phải lỗi — "sửa" nó là âm thầm quyết hộ.

### Số test — dùng LỆNH, không chép số vào prose

Số test đã stale **3 lần** trong các cycle trước vì viết tay. Muốn số hiện tại:

```powershell
uv run pytest -q --collect-only 2>&1 | Select-String "tests collected|tests? collected"
uv run pytest -q ui/backend/tests --collect-only 2>&1 | Select-String "tests? collected"
```

⚠ **Phải chạy CẢ HAI** — `pyproject.toml` có `testpaths = ["tests"]` nên lệnh trần **bỏ** cây
`ui/backend/tests` (`D-M3-09`).

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Lý do:** không đổi UI nào. `cards.js`, `web/`, `driver_app/` không bị chạm; thay đổi nằm ở
  service/router/registry và test. Một thẻ mềm bị bấm "Làm theo" nay nhận 422 thay vì 200 — nhưng
  **hôm nay chưa có client nào vẽ nút đó cho thẻ `rest`**, nên không có gì để xem trên màn hình.
- **Cái CẦN xem khi có client thật:** khi Khánh nối thẻ `rest`/`safety_reserved` vào Flutter, thẻ đó
  **không được có nút "Làm theo"** — nếu có, người dùng sẽ bấm và nhận 422, tức lỗi hiện ra ở sai
  chỗ. Đã ghi vào §7 văn bản quyết định (phần việc của Khánh).

## 🔴 SOI ĐỘC LẬP 2026-08-04 — bốn lỗi trong chính cycle này, tôi đã tự kiểm lại toàn bộ

Tự soi (mục dưới) **không bắt được cái nào trong bốn cái này**. Đúng như đã ghi: *tự soi bắt được
lỗi thi công, không bắt được GIẢ ĐỊNH*. Mọi claim dưới đây tôi **kiểm lại bằng code của mình** trước
khi nhận — không nhận nguyên văn báo cáo của agent.

### (1) ⚠ NẶNG NHẤT — cổng đầu-cuối của tôi canh một kịch bản BẤT KHẢ

Test dùng orchestrator giả trả `solver_set=["S7"]`. Hai sự thật độc lập bác bỏ nó:

| | Bằng chứng |
| --- | --- |
| **S7 không chạy ở sản phẩm** | `ProductSolverOrchestrator` chỉ gọi `bonus_feasibility` (`:176`) và `shift_dp` (`:210`). S7 = `solvers/idle_reduction.py`, chỉ sống ở sim |
| **Contract CẤM tổ hợp đó** | `advice_v2.json` → `solver_set.items.enum = ["S1","S2"]`. Thẻ tôi dựng **vi phạm schema**, test không bắt vì tôi không validate |

⇒ Cổng chứng minh ranh giới trên nhánh **không tồn tại được**, còn đường THẬT
(`S2 → code "REST" → "rest"`, `checkpoint.py:134`) **không test nào phủ**. Đây đúng họ lỗi cả cycle
này dựng lên để chống — *cơ chế bảo vệ canh một nhánh không có đường chạy* (`D-R12`, Lỗi #9). **Lần
này tôi là người mắc, ngay trong cycle chống nó.**

**Đã sửa:** `_S2RestOrchestrator` đi đúng đường sản phẩm, **cộng `jsonschema.validate`** trên envelope
— nay một kịch bản giả vi phạm contract sẽ ĐỎ ngay thay vì âm thầm chứng minh thứ vô nghĩa.

### (2) `rest` không "nhập nhằng" như tôi viết — nó RỖNG NGHĨA

Tôi viết *"`rest` gộp `rest_window` (kinh tế) với `rest_nudge` (mềm)"*. Đo lại: **không producer nào
sinh `rest_nudge`**. S7 = *"dời nghỉ/sạc vào khung nhu cầu thấp"*, input không có trường mệt nào nên
**không thể** biết tài xế quá sức; S2's REST là **sàn nghỉ tối thiểu** đặt vào bucket demand thấp.
Cả hai đều là lời khuyên **THỜI ĐIỂM**. `rest` không gộp hai thứ — nó **đặt chỗ trước cho một thứ
chưa tồn tại**.

Kết luận SOFT **giữ nguyên nhưng lý do đổi, và lý do mới mạnh hơn**: `_topic_for_action` route theo
`code == "REST"`, nên **bất kỳ** solver nào mai sau trả `REST` — kể cả producer mệt-mỏi thật — đều
rơi vào khoá này. MEASURED là mở một cửa **vĩnh viễn**, đổi lấy mẫu số một lát cắt S2 hôm nay.

### (3) 🔴 EXTEND — đối xứng ngược của chính QĐ-1, và nhãn SAI của tôi làm nó lọt

`advice_topics.py` cũ khai `shift_timing` = *"EXTEND/đổi giờ"*, `shift_boundary` = *"END ca. Kinh
tế."*. Thực tế `checkpoint.py:138-141` route **CẢ END LẪN EXTEND** → `shift_boundary`; `shift_timing`
là nhánh mặc định cuối, **không bao giờ** nhận EXTEND. ⇒ **nửa EXTEND rơi qua khe giữa hai dòng
comment và chưa từng được xét** — trong khi "khuyên tài xế chạy thêm" là thứ cần xét kỹ nhất.

Ba sự thật đã kiểm bằng code:

1. `check_shift_extend` (`advice_bridge.py:914-931`) có **0 lan can mệt/SOC**, trong khi
   `should_defer_rest` có **ba** (`soc_low` · `fatigued` · `defer_cap`). Nó *có* đọc `online_min`
   nhưng làm **mẫu số năng suất** ⇒ **tài xế mệt mà năng suất cao vẫn được khuyên kéo ca**.
2. `policy_locks.py:40-42` khoá `advice.shift_extend_max_min` **ngang hàng** `rest_defer_max_min`,
   comment nguyên văn *"cùng họ: **kéo dài thời gian làm việc vì tiền**"*, và module tự gọi mình là
   *"KHOÁ CHÍNH SÁCH SỨC KHOẺ … lan can sức khoẻ (§1.2b)"*. **Repo tự xếp nó là đòn bẩy sức khoẻ.**
3. Repo đang tự mâu thuẫn: guardrail tầng 5 **báo động** khi `work_span_p90` tăng >10%, còn
   `adherence_view` **tính là thành tích** cái tỷ lệ làm nó tăng.

Lập luận §1.2c áp nguyên văn, chỉ đổi dấu: *cải thiện `shift_extend_adherence`* = **nhiều tài xế hơn
đồng ý kéo dài giờ làm**.

**Tôi KHÔNG tự đổi phân loại** — đổi phạm vi đo là quyết định sản phẩm, và kênh này đã có số thật mà
`D-M3-01` bỏ công sửa. Đã sửa **nhãn** (lỗi sự kiện), giữ **nguyên trạng** phạm vi đo, và mở
`D-QD4-03` + `V-28` cho Cường. Kèm cổng mới `test_QD4_ANH_XA_THAT_cua_producer_khop_voi_nhan` neo
nhãn vào hành vi thật của producer để nhãn không trôi khỏi code lần nữa.

### (4) `policy_info` — tôi phân loại một topic KHÔNG CÓ producer

Grep toàn repo: đúng 2 hit — dòng khai trong registry và bảng ghim trong test. Nó tới từ **enum
contract**, không từ code sinh thẻ. Không sai kết quả, nhưng lộ ra cách làm: tôi phân loại theo
*danh sách trong contract* chứ không theo *cái gì thật sự sinh ra thẻ*. Đã ghi nhãn tại chỗ.

### Cái soi độc lập KHÔNG bác được (giả định đứng vững)

- *"Store v2 chưa vào `adherence_view` nên chưa sinh số sai"* — **ĐÚNG**: consumer duy nhất của
  `adherence_view` là `checkpoint_trace.py` và `sim_metrics.py`, cả hai đọc `sim_events_to_lifecycle`,
  không đọc `CheckpointStore`.
- `positioning_sim_only` chỉ sim, `bonus_eligibility` kinh tế thuần (0 hit rest/fatigue/soc/safety
  trong `bonus_feasibility.py`) — **ĐÚNG**.
- `energy` xếp MEASURED **vẫn đứng**, nhưng **lý do tôi viết thì sai**: `soc_low` được chính repo gọi
  là lan can sức khoẻ (§1.2b, `sim_metrics.REST_RAILS`). Lý do đúng: pin có **kênh tác hại được mô
  hình hoá** (`battery_stranded`), mệt thì không (`D-SIM-16`). Đã sửa comment.

⚠ **Hai trong bốn tác tử soi chết vì session limit** (`behavior-neutral`, `hau-qua-fail-closed`) ⇒
hai hướng **chưa ai soi**: (a) thêm 6 topic vào bảng ĐO có đổi output `adherence_view` trên dữ liệu
thật không; (b) nhánh fail-closed 422 hiện ra thế nào ở client. Ghi là **CHƯA KIỂM**, không phải
đã qua.

## Adversarial self-review / flaws found

1. **Cái gì có thể trông tốt nhưng sai?** — Cổng có thể xanh vì kịch bản không dựng nổi thẻ mềm chứ
   không phải vì ranh giới kín. Đã chặn: `_the_rest()` **assert `card["topic"] == "rest"`** trước khi
   ba test dưới chạy; nếu ánh xạ S7→rest đổi thì test đỏ với thông điệp nói đúng lý do, thay vì xanh
   rỗng.
2. **Ranh giới đóng quá tay?** — Đúng là rủi ro thật, và có hai đối chứng: `test_topic_KINH_TE_…`
   (kênh kinh tế phải giữ `measured`) và `test_HTTP_the_MEM_van_nhan` (`dismissed`/`expanded` vẫn
   200). Mũi sever **e** kiểm hướng này bằng cách tiêm thật.
3. **Test service dùng `__new__` bỏ `__init__`** — không dựng DB thật. Đánh đổi: nhanh + tất định,
   nhưng nó **không** chứng minh đường ghi thật. Vì thế mới có thêm ba test HTTP đi qua
   `_open_service()` thật. Một mình lớp service là chưa đủ; tôi đã không dừng ở đó.
4. **Lỗi tôi tự gây rồi tự bắt trong cycle này:** thêm cảnh báo tiếng Việt vào `advice_v2.json` làm
   `test_advice_v2_api.py` **đỏ** — `read_text()` không khai encoding dùng cp1252 trên Windows. Đây
   **không phải hồi quy do tôi**: 7 contract khác trong `ui/contracts/` đều đã có tiếng Việt, riêng
   `advice_v2.json` từng là file ASCII thuần nên dòng đó xanh **nhờ may**. Đã sửa bằng
   `encoding="utf-8"` + ghi lý do ngay tại chỗ, không sửa lặng.
5. **Lỗi thứ hai tôi tự gây rồi tự bắt — quan trọng hơn cái trên:** để thêm câu cảnh báo vào
   `advice_v2.json` tôi đã ghi lại cả file bằng `json.dumps(indent=2)` ⇒ **reformat toàn bộ contract
   của Khánh: 310 dòng thêm / 55 dòng xoá cho một câu**. Suite vẫn xanh (JSON tương đương về ngữ
   nghĩa) nên **không cổng nào bắt được** — chỉ đọc `git diff --stat` mới thấy. Đó đúng thứ quy ước
   *"không tự sửa code PR owner"* sinh ra để chặn: một diff như thế làm review bất khả thi và biến
   một câu cảnh báo thành một cuộc xung đột merge. Đã `git checkout` khôi phục rồi sửa đúng một
   dòng bằng edit văn bản. **Diff cuối: 1 dòng.** Bài học vận hành: *suite xanh không chứng minh
   diff sạch* — phải đọc `--stat` trước khi commit vào file người khác sở hữu.
6. **Assumption yếu nhất:** `rest` → mềm (confidence TRUNG BÌNH). Nó có thể đang **giấu một mẫu số
   hợp lệ** của kênh HOÃN nghỉ. Đã ghi `D-QD4-01` kèm điều kiện: nợ này **tự tiêu** nếu `D-M3-04`
   REVERT (khi đó `rest_window` cũng thành mềm).
7. **Đã loại trừ:** (a) *"lỗ này đã sinh số sai"* — bác bằng việc `adherence_view` chỉ đọc
   `AdviceEventLog`; (b) *"DB v2 cũ đang mang bản ghi nhiễm"* — bác **cho máy Cường** bằng
   `Get-ChildItem` (không có file); **không bác được cho máy Khánh** ⇒ ghi thành điều kiện của
   `D-QD4-02` chứ không tuyên bố sạch.
8. **Chưa kiểm:** Flutter (`ui/driver_app/`) — claim của Khánh, không đụng. Nếu app đang gửi
   `accepted` cho thẻ mềm thì nó sẽ bắt đầu nhận 422; đó là hành vi ĐÚNG nhưng cần Khánh xử lý phía
   client, không để lỗi rơi ra màn hình tài xế.
9. **Flaw còn mở → ID:** `D-QD4-01` (tách `rest`) · `D-QD4-02` (bước 3 + kiểm DB máy Khánh) ·
   `K-01` (3 test đỏ có sẵn trên `main`, chưa báo Khánh).

## Expansion checkpoint (T-039)

1. **Schema:** không thêm field. Cân nhắc (chưa làm): thêm `is_soft_advice` vào envelope v2 giống
   `GET /advice/actions` của v1, để client **biết** mà không vẽ nút "Làm theo" — hiện client phải tự
   biết. Đó là cách đóng lỗ ở tầng UI thay vì để 422 làm hàng rào cuối.
2. **Bài toán tối ưu:** không có residual mới. Ngược lại, update này **thu hẹp** không gian đo một
   cách có chủ ý (2 topic ra khỏi bảng đo) — đúng ranh giới §1.2b/§1.2c.
3. **Tính năng:** registry hợp nhất mở đường cho `D-QD4-02` (một bảng adherence cho cả đường sản
   phẩm) — nhưng phải giải `D-R22` trước, vì adherence sản phẩm (cú bấm tự khai) và adherence sim
   (đổi hành vi thật) hiện **không so được**.

## Follow-up / defer phát sinh

| ID | Việc | Severity | Điều kiện mở lại |
| --- | --- | --- | --- |
| `D-QD4-01` | tách `rest` của v2 thành hai topic rõ nghĩa | THẤP | cùng lúc với `D-M3-04`; tự tiêu nếu D-M3-04 REVERT |
| `D-QD4-02` | `CheckpointStore` vào đường đo chung (bước 3) | THẤP | khi cần một con số adherence cho đường v2; phải giải `D-R22` + kiểm DB máy Khánh trước |
| — | Khánh: thẻ mềm trên Flutter **không** được có nút "Làm theo" | — | khi nối thẻ `rest`/`safety_reserved` vào app |
| `K-01` | 3 test đỏ có sẵn trên `main` (không do cycle này) | — | báo Khánh |
