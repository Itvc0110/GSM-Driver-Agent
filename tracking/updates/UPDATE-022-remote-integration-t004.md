# UPDATE-022 — Tích hợp remote (T-004 source register + corpus) vào main, bảo toàn Stage A–C

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent (theo yêu cầu **Cường**: kiểm branch, pull/merge vào main, mở visualization, liệt kê việc dang dở)
- **Loại:** docs / integration / merge
- **TODO / User story liên quan:** T-004 (teammate Khánh), T-029/T-030 (reliability program)

## Tóm tắt

Tích hợp `origin/main` (đã tiến tới `b4cd1f9` — owner merge PR #1 source register + PR #2 text corpus) vào local `main`. Local main là ancestor thuần (0 ahead / 4 behind) nên không có commit local nào chọi. Governance M0–M4 (UPDATE-021, đổi số từ 013 do remote đã chiếm 019/020) được commit trước bằng allowlist docs; sau đó merge remote, hợp nhất `tracking/TODO.md` (giữ cả T-004 và M0–M4). **Toàn bộ working diff Stage A–C được bảo toàn nguyên trạng, không stage/commit.**

Phát hiện quan trọng: file corpus `t004-current-policy-text-corpus-2026-07-22.json` (owner đã merge qua PR #2) đang **lỗi encoding — mojibake toàn bộ 7 records tiếng Việt**. Không tự sửa/revert PR của owner; ghi thành việc dang dở cho task T-004 repair.

## Chi tiết cập nhật

### 1. Trạng thái remote khi tích hợp

- `origin/main` = `b4cd1f9` (Merge PR #2). Chuỗi mới so với local `5f85aa8`: `57e1a85` (source register) → `52f2c26` (merge PR #1) → `3221f21` (corpus) → `b4cd1f9` (merge PR #2).
- 7 file đến từ teammate: `research/policy/{T004_POLICY_SOURCE_REGISTER.md, T004_TEXT_CORPUS_USAGE.md, t004-current-policy-text-corpus-2026-07-22.json}`, `tracking/{TODO.md, ASSIGNMENTS.md}`, `tracking/updates/{UPDATE-019, UPDATE-020}`.
- Không file nào chạm `src/gsm_sim/`, `configs/`, `tests/` hay specs sim. Overlap duy nhất với docs local là `tracking/TODO.md` (auto-merge sạch).

### 2. Numbering

Remote đã dùng `UPDATE-019` (footprint compaction) và `UPDATE-020` (text corpus). Do đó reliability program local đổi từ `UPDATE-013` → **`UPDATE-021`**; update tích hợp này là **`UPDATE-022`**. Không backfill 013–018, không renumber lịch sử. Cập nhật tham chiếu tại `tracking/TODO.md` T-029, header/self-ref UPDATE-021, và comment `src/gsm_sim/archetypes.py` (file thuộc Stage A–C, sửa comment cho nhất quán nhưng KHÔNG stage vào commit docs).

### 3. Cấu trúc commit

1. `34dfaa7 docs: reliability-first simulator program M0-M4 + governance` — 11 file allowlist docs, không sim code.
2. `ba94c12 Merge remote-tracking branch 'origin/main'` — 7 file T-004 + TODO hợp nhất; Stage A–C không staged.
3. (update này + research index/summary sync — commit kèm).

### 4. Clarify UPDATE-019 (non-destructive)

`UPDATE-019` viết "xóa UPDATE-010…018". Đọc theo lịch sử canonical toàn repo thì gây hiểu nhầm: canonical `UPDATE-010/011/012` (simulator) vẫn tồn tại trên main và KHÔNG bị xóa; Git history không ghi nhận canonical `UPDATE-013…018` từng tồn tại. Không sửa file lịch sử `UPDATE-019`; ghi làm rõ tại đây: cụm đó chỉ nói về **artifact chuẩn bị T-004 branch-local** (crawler/raw/asset/plan nháp), không phải ledger canonical.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `tracking/updates/UPDATE-013-...` → `UPDATE-021-...` | đổi tên + sửa ref | Reliability program (đổi số vì remote chiếm 019/020) |
| `tracking/TODO.md` | sửa + merge | Ref UPDATE-021; hợp nhất T-004 (Khánh) + M0–M4 |
| `src/gsm_sim/archetypes.py` | sửa comment | UPDATE-013→021 ref; **KHÔNG staged — vẫn là Stage A–C/T-030 input** |
| `research/README.md` | sửa | Index 3 file T-004 + market/simulation; cảnh báo corpus encoding |
| `research/00_SUMMARY.md` | sửa | T-004 follow-up: handoff xong, chưa KB runtime, corpus lỗi encoding |
| `tracking/updates/UPDATE-022-remote-integration-t004.md` | tạo | Update này |
| (từ remote) `research/policy/*`, `tracking/ASSIGNMENTS.md`, `UPDATE-019/020` | merge vào | Nội dung teammate, giữ nguyên |

## Docs đã cập nhật kèm theo

TODO (ref + merge), research README + SUMMARY. SCOPE/DEFERRED: không đổi trong lượt tích hợp. ASSIGNMENTS: lấy bản remote (local sạch), không tự claim.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `origin/main`=`b4cd1f9`, local ancestor thuần (0 ahead/4 behind) | `OBSERVED-CODE` | `git rev-list --left-right --count`, `git branch -av` 2026-07-22 | Cao | Nếu diverge thật, cần reconcile khác |
| 7 file remote không chạm sim code/config/spec | `OBSERVED-CODE` | `git diff --name-status 5f85aa8..origin/main` | Cao | Nếu sai, Stage A–C có thể bị merge chạm |
| Corpus JSON mojibake toàn bộ 7 records | `OBSERVED-CODE` | `git show :...json` → 8586 ký tự `Ã` lỗi | Cao | Corpus không dùng làm evidence review tới khi repair |
| Stage A–C giữ nguyên 219+/44- + 2 untracked qua cả 2 commit | `OBSERVED-CODE` | `git diff --stat -- src/gsm_sim configs` trước/sau | Cao | Nếu đổi, phải điều tra staging |

## Kiểm chứng

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| `uv run --extra dev pytest -q` | N/A | N/A | (điền khi chạy) | — |
| `run_once` sanity | 1–5 | dry_weekday | (điền khi chạy) | Chưa chạy multi-seed distribution ≥30 |

## Visual verification

- **Status:** `REVIEWED` (dashboard launch OK, HTTP 200) — nhưng **các lỗi Cường nêu CHƯA được sửa** trong lượt này.
- **Cách launch / artifact:** `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` (port 8501, health 200).
- **Seed / scenario đã xem:** dry_weekday / rain_peak / event_day (seed 1).
- **Người review + verdict:** Cường 2026-07-22 — xác nhận dashboard **chưa fix** lỗi đã nêu (tủ pin bị H3 đè, chưa có trajectory/actor journey/customer/flaw player, timestep resolution); **cho phép push merge, để chỉnh lượt sau**.
- **Ghi chú:** dashboard hiện là v0 (arm B, 1 seed, aggregate H3). Các fix thuộc M3/T-035–T-037 + Stage A–C audit T-030. Đây là lượt tích hợp docs/merge, KHÔNG phải lượt sửa UI — nên các lỗi UI được chuyển thành việc dang dở có chủ đích (waiver tường minh của Cường).

## Adversarial self-review / flaws found

1. **Trông tốt nhưng sai:** merge sạch có thể tạo cảm giác T-004 hoàn chỉnh; thực tế corpus lỗi encoding → đã gắn cảnh báo ở README/SUMMARY/đây.
2. **Owner PR vs quality gate:** corpus không đạt semantic quality nhưng owner đã merge vào main; agent KHÔNG tự revert/sửa PR của owner — chỉ ghi việc dang dở. Cần Khánh/owner quyết repair.
3. **Stage A–C leak:** kiểm `git diff --cached` ở cả 2 commit → không sim file nào bị stage; comment archetypes sửa nhưng không staged.
4. **Numbering drift:** đã đổi 013→021 và dùng 022, tránh trùng remote 019/020.
5. **Flaw còn mở:** corpus encoding repair, T-030 audit Stage A–C, dashboard trajectory (T-035–T-037).

## Follow-up / defer phát sinh

- **T-004 repair (Khánh/owner):** re-fetch/khôi phục UTF-8 cho corpus, làm rõ 2 field `page_sha256`, semantic validation (reject mojibake/C1); tạo UPDATE riêng. Chưa có ai claim.
- **T-030 (READY):** audit Stage A–C — việc sim tiếp theo, cần self-claim + plan mode.
- Dashboard chưa hiển thị trajectory/customer/flaw (M3/T-035–T-037).
