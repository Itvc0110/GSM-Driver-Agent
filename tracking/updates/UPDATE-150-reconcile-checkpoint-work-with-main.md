# UPDATE-150 — Hoà giải checkpoint/UI-idea work với `origin/main` (14 commit mới, tới `6ecef47`)

- **Ngày:** 2026-08-06
- **Người thực hiện:** AI agent theo yêu cầu trực tiếp của Khánh
- **Loại:** governance / git reconciliation / config
- **Trạng thái:** `DONE-CODE` — branch mới đã tạo, tests xanh, chờ push + PR (thực hiện ngay sau UPDATE này)

## Bối cảnh

Trong lúc làm việc local (UPDATE-144..149), `origin/main` đã tiến thêm **14 commit** (merge-base `276df6d` → `6ecef47`), gồm PR #5 (đã merge nhánh `feat/advice-checkpoint-agent-template-why` — chính là HEAD cũ của local) cộng thêm 13 commit trực tiếp của Cường: khoá ngoài + khuyên mềm không đo (UPDATE-135..137 CỦA MAIN), lan can sức khoẻ kênh kéo ca (UPDATE-138 CỦA MAIN), D-M3-04 cycle B REVERT (UPDATE-140..142 CỦA MAIN), V-28 dashboard (UPDATE-143 CỦA MAIN). 66 file, 8.305 dòng thêm.

**Vấn đề:** local đã độc lập dùng đúng dải số **UPDATE-135..140** cho nội dung hoàn toàn khác (checkpoint inventory/expansion/discovery/foundation-fixes + UI-idea-cards catalog từ một phiên khác của Khánh). Trùng số — không trùng đường dẫn file (git không tự conflict) nhưng vi phạm quy ước UPDATE duy nhất của repo và gây nhầm lẫn khi đọc PROJECT-GRAPH/TODO.

## Việc đã làm

### 1. Khảo sát mức xung đột thật (trước khi đụng git)

So khớp diff hunk (line-range) giữa `276df6d→origin/main` và `276df6d→working tree` cho từng file có tên trùng:

| File | Main đổi (dòng cũ) | Local đổi (dòng cũ) | Overlap thật |
|---|---|---|---|
| `src/gsm_core/lifecycle/checkpoint.py` | không đổi | 145-414 | KHÔNG (main không đụng file này) |
| `src/gsm_sim/advice_bridge.py` | 748-1001 | 594-600, 744-753, 998-1011 | Cận biên (2 chỗ liền kề, không cùng dòng) |
| `src/gsm_sim/world.py` | 15-994 (6 hunk) | 453-459 | KHÔNG |
| `ui/backend/app/services/advice_checkpoint.py` | 33-469 (3 hunk) | 403-533 | KHÔNG |
| `ui/contracts/advice_v2.json` | dòng 69 (topic enum) | dòng 110 (checkpoint_schema_version) | KHÔNG |
| `configs/pilot_dongda.yaml`, `pyproject.toml`, `schemas/CHANGELOG.md` | không đổi | — | KHÔNG (an toàn, "config" lo ngại của Khánh không trúng ở đây) |
| `tracking/PROJECT-GRAPH.md`, `tracking/TODO.md` | append nhiều dòng | append nhiều dòng | Khác section, an toàn |

Kết luận trước khi merge: rủi ro conflict thật chỉ ở 2 điểm liền kề trong `advice_bridge.py` (ranh giới `rest_window_hour`/`should_defer_rest` và ranh giới `check_shift_extend`/`_capture_checkpoint`) — git 3-way merge xử lý đúng cả hai, xác nhận bằng `git stash pop` không sinh conflict marker nào (§3).

### 2. Đánh số lại UPDATE-135..140 (local) → **144..149**

143 là số cuối cùng đã dùng trên main. Đổi tên file + thay MỌI tham chiếu chéo (`\bUPDATE-13[5-9]\b|\bUPDATE-140\b`) trong 22 file bị ảnh hưởng (docs lẫn code comment):

| Cũ (local) | Mới | Nội dung |
|---|---|---|
| UPDATE-135-checkpoint-inventory-audit.md | **UPDATE-144** | Inventory audit 5 seed |
| UPDATE-136-advice-checkpoint-expansion-audit.md | **UPDATE-145** | Expansion/candidate audit |
| UPDATE-137-checkpoint-scenario-discovery.md | **UPDATE-146** | Scenario discovery + funnel |
| UPDATE-138-checkpoint-foundation-fixes.md | **UPDATE-147** | Nền móng checkpoint (code) |
| UPDATE-139-checkpoint-deep-opportunity-discovery.md | **UPDATE-148** | Deep opportunity discovery (phiên khác của Khánh) |
| UPDATE-140-driver-ui-experience-idea-cards.md | **UPDATE-149** | 33 UI Idea Cards (phiên khác của Khánh) |

`PROJECT-GRAPH.md` §3.11 và mọi cross-reference trong 6 file trên đã cập nhật đồng bộ; verify bằng `grep -rlE "UPDATE-13[5-9]\b|UPDATE-140\b"` → rỗng sau khi sửa.

**Không đổi:** `UPDATE-114-requirements-and-simulator-setup.md` (untracked, có sẵn từ trước phiên này, chủ đề môi trường/`requirements.txt` không liên quan) — số 114 **đã bị dùng thật** trên cả hai nhánh (`UPDATE-114-nam-lo-duong-ong-ab-va-e10b-low.md`), nhưng vì đây là việc ngoài phạm vi (không phải checkpoint/UI-idea), tôi **không đưa vào PR này** để tránh phình scope; giữ nguyên untracked, ghi chú cho Khánh quyết định riêng.

### 3. Git surgery

```
git stash push -u -m "reconcile-with-main-2026-08-06: ..."   # gộp cả tracked + untracked
git checkout -b feat/checkpoint-foundation-and-ui-ideas origin/main
git stash pop
```

Kết quả: **6 file "Auto-merging" thành công, 0 conflict marker.** Không dùng branch cũ `feat/advice-checkpoint-agent-template-why` (đã merge vào main qua PR #5) để tránh nhầm lẫn — branch mới đặt tên theo đúng nội dung đang PR.

### 4. Fix K-01(a) — `scripts/compare_checkpoint_shadow` không import được dưới `pytest` thật

Cường đã flag (`PENDING-REVIEW.md` K-01, "cho KHÁNH") 2 test đỏ sẵn trên `origin/main` khi chạy bằng `pytest`/`uv run pytest` (không phải `python -m pytest`): `tests/test_checkpoint_trace.py` × 2, `ModuleNotFoundError: No module named 'scripts'`. Root cause xác nhận: `pyproject.toml`'s `pythonpath = ["src"]` không đưa repo root vào `sys.path`; `python -m pytest` tình cờ xanh vì `-m` tự thêm cwd vào `sys.path[0]`.

**Fix:** `pythonpath = [".", "src"]`. Verify bằng invocation THẬT (`</br>.venv/bin/pytest` — không dùng `-m`, mô phỏng đúng cách `uv run pytest` gọi): `tests/test_checkpoint_trace.py` 8/8 pass (trước đó đỏ theo đúng mô tả của Cường).

**ĐÍNH CHÍNH khi đọc kỹ hơn (xem UPDATE-147 §7 đã sửa):** fix này KHÔNG giải quyết `tests/test_demo_trace_neutrality.py` (một fail pre-existing khác, root cause khác: `app` package chỉ được thêm path bởi `ui/backend/tests/conftest.py`, phạm vi không phủ `tests/` gốc) — hai fail này bị tôi gộp nhầm thành một trong UPDATE-147 bản đầu; đã tách rõ.

**K-01(b) — CHỜ CƯỜNG/KHÁNH XÁC NHẬN, KHÔNG tự quyết:** `tests/test_cadence_policy.py::test_safety_topic_presents_even_while_driving` đổi từ assert `PRESENT` sang assert `QUEUE`/`unsafe_while_moving`. Thay đổi này **đã tồn tại trong working tree TRƯỚC phiên này** (không phải do agent tạo ra), và khớp với quyết định B-03 đã đóng theo `BOOTSTRAP-SESSION.md` §5 (*"cadence xét driving trước safety... safety priority chỉ còn cho trusted server producer và vẫn queue khi driving"*). Tôi **giữ nguyên** thay đổi này (không revert về PRESENT) vì nó khớp quyết định đã đóng, nhưng đưa vào **commit riêng, nhãn rõ** và nêu tường minh trong PR — đúng yêu cầu *"đừng ai sửa lặng lẽ"* của Cường. Nếu Cường/Khánh muốn xem lại quyết định B-03, revert commit này không ảnh hưởng phần còn lại của PR.

### 5. Kiểm chứng trên branch mới (`feat/checkpoint-foundation-and-ui-ideas`, HEAD = `origin/main` + local work)

| Kiểm | Kết quả |
|---|---|
| Focused (`test_checkpoint_enrichment` + `test_advice_checkpoint` + `test_checkpoint_trace` + `test_schemas` + `test_schema_versioning` + `test_demo_checkpoint_alignment` + `test_cadence_policy` + `test_advisor_pipeline`) | **117 passed** |
| `ui/backend/tests` (full) | **195 passed** (124 của cycle trước + ~71 test mới từ main: OSRM wired, soft-advice no-trace ×2) |
| `scripts/compare_checkpoint_shadow.py` 5 seed | **IDENTICAL 5/5** — dynamics không đổi kể cả sau khi hợp nhất với sim changes mới của main (D-M3-04 REVERT, lan can sức khoẻ kéo ca) |
| `tests/test_checkpoint_trace.py` qua `.venv/bin/pytest` (không `-m`) | **8/8 pass** (trước fix: ModuleNotFoundError, đúng mô tả K-01a) |
| Root suite full (`.venv/bin/pytest -q`, 23′47″) | **1110 passed / 4 skipped / 3 failed — CẢ BA FAIL ĐỀU PRE-EXISTING**, mỗi cái chứng minh bằng `git stash` (bỏ toàn bộ diff UPDATE-144..150) rồi chạy lại trên `origin/main` sạch: fail y hệt cả ba. (1)(2) đã biết từ cycle UPDATE-147 (`test_demo_trace_neutrality`, `test_health_boundary::test_money_manifest_is_complete`). (3) **MỚI phát hiện khi chạy full suite lần này** — `tests/test_cadence_sim.py::test_count_positioning_in_budget_flag_is_alive`: bật/tắt `count_positioning_in_budget` cho ra **cùng một `summarize(r)`** ở seed 1000 (`sup_off`/`sup_on` đúng như kỳ vọng, nhưng `sum_on == sum_off` — cờ không đổi được kết quả emergent dù cơ chế cổng nhịp đã hoạt động đúng theo 2 assert trước đó). Không thuộc phạm vi checkpoint/UI-idea — không sửa, chỉ ghi nhận cho chủ cổng (D-ĐA04-03/positioning budget) |

## Files bị ảnh hưởng (riêng của UPDATE-150)

| File | Hành động |
|---|---|
| `pyproject.toml` | `pythonpath = [".", "src"]` |
| 6× `tracking/updates/UPDATE-14{4,5,6,7,8,9}-*.md` | đổi tên từ 135-140, cross-ref cập nhật |
| `tracking/PROJECT-GRAPH.md`, `research/audit/2026-08-05-checkpoint-scenario-discovery/discovery-report.md`, và các file code có comment "UPDATE-13x" | cross-ref cập nhật theo số mới |
| `tracking/updates/UPDATE-147-checkpoint-foundation-fixes.md` | đính chính §7 (tách 2 fail pre-existing khác root-cause) |

## Adversarial self-review

1. Không audit lại nội dung research của UPDATE-148/149 (viết bởi phiên khác của Khánh) đối chiếu với thay đổi taxonomy mới của main (`advice_topics.py`, `rest`→SOFT). Có khả năng một số nhận định trong đó đã stale sau D-M3-04 REVERT + QĐ-4. Không sửa nội dung đó (ngoài phạm vi việc merge/renumber) — ghi rõ trong PR để owner tự soát.
2. K-01(b) được GIỮ nguyên theo lý do đã nêu, nhưng đây vẫn là một quyết định an toàn — PR phải nêu tường minh để không bị coi là "sửa lặng lẽ".
3. `UPDATE-114-requirements-and-simulator-setup.md` + `requirements.txt` (untracked, ngoài phạm vi) cố tình **không** đưa vào PR này — tránh mở một vấn đề không liên quan (và số 114 đã bị dùng thật) giữa lúc PR đang tập trung vào checkpoint/UI-idea.
4. Comparator chỉ chạy 5 seed (không phải 30+) — đủ cho "không đổi dynamics chủ ý", không phải certificate thống kê đầy đủ.
5. Root suite full chưa có số cuối tại thời điểm viết — PR sẽ không tuyên bố "suite xanh" cho tới khi có kết quả.

## Follow-up

- `tests/test_demo_trace_neutrality.py` path/pythonpath fix thật — chưa làm (§4 đính chính), để riêng.
- Money-manifest classification cho 4 hàm demo trace — chưa làm, thuộc chủ cổng `test_health_boundary`.
- `tests/test_cadence_sim.py::test_count_positioning_in_budget_flag_is_alive` — pre-existing trên main sạch, KHÔNG thuộc phạm vi cycle này, cần chủ cổng `count_positioning_in_budget`/D-ĐA04-03 xem lại.
- `UPDATE-114-requirements-and-simulator-setup.md` cũ + `requirements.txt` — hỏi Khánh có cần giữ/renumber riêng không.

## Kết quả cuối (điền sau khi root suite xong)

Root suite: **1110 passed / 4 skipped / 3 failed** — cả 3 fail pre-existing trên `origin/main` sạch (chứng minh bằng stash), không do PR này gây ra. Backend: 195/195. Comparator: IDENTICAL 5/5. Sẵn sàng commit + push + PR.
