# UPDATE-082 — Reconcile current state: data 90 ngày, hai demo, Advisor UX và ĐA-01..06

> **Đổi số 073 → 082 (2026-07-28).** Remote `origin/main` đã chiếm số 073
> (`UPDATE-073-simulator-web-fare-unification.md`, do Cường/session khác đẩy lên trong lúc nhánh
> này còn ở working tree). Theo quy ước tích hợp: **đổi số local, không renumber lịch sử remote**.
> Nội dung bên dưới giữ nguyên ngày tạo **2026-07-27**, nên số thứ tự KHÔNG phản ánh thời gian.

- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent theo yêu cầu trực tiếp của Cường
- **Loại:** docs / research / audit
- **TODO / User story liên quan:** T-040; US-F0-01; US-F1-02; F1–F3; ĐA-01..06

## Tóm tắt

Đọc/reconcile codebase, schema, manifest, UI/backend/sim/advisor và lịch sử audit để trả lời rõ
“mock 90 ngày”, data update, parity simulation↔driver app và năng lực Advisor. Tạo dossier 6 file,
đính chính docs lỗi thời, lưu follow-up prompt. Cường chốt architecture B và ĐA-01..03; ĐA-04..06
đã có hướng chi tiết nhưng vẫn chờ duyệt. Không sửa runtime và không tiếp quản phiên R5.

## Chi tiết cập nhật

1. **Data lineage:** phân biệt 13 bảng L1R có shape GSM với nội dung hoàn toàn MOCK; snapshot 90
   ngày 2026-07-01→2026-09-28, seed 7000, engine commit `d325055`, 150 profile. Làm rõ R2 30 seed
   không artefact-verify trực tiếp snapshot local (`D-SIM-08`).
2. **Data update:** lập ma trận sim RAM/export/static UI/trip demo/Advisor. Kết luận cuốc demo và
   Advisor không cập nhật payout/acceptance/completion; regen + backend restart/cache reset là thủ
   công. Đề xuất event→projection→as-of snapshot, Advisor read-only.
3. **Schema:** inventory 41 JSON Schema; ghi blocker registry một-file/entity chưa thực thi
   backward compatibility cho minor bump.
4. **Hai demo:** ghi decision B — simulation demo cho dispatcher/researcher chạy A/B/C và
   visualize system/fairness; driver app demo + Advisor cho một tài xế. Không cần cùng UI, nhưng
   cùng run/actor/as-of phải reconcile canonical events/ledger.
5. **Advisor:** map 9 solver/input/source/channel; web hiện chỉ S1, core C6 chưa là product path
   thống nhất, Flutter advice hard-code, external context/goal/F3 recap chưa wired.
6. **UX:** thiết kế proposal lifecycle ignore/rest, tách intent khỏi behavior, không repeat rest
   advice trong cùng window/shift, safety flow riêng; personal goal ≠ policy quota ≠ mission;
   shift/week recap fancy nhưng accessible/non-coercive.
7. **ĐA:** ĐA-01..03 chuyển `APPROVED-DESIGN`; ĐA-04..06 có dependency, contracts và acceptance
   gates để Cường duyệt. Không implement.
8. **R5:** ghi `BLOCKER-R5-MUT10` từ HEAD `7739b3c`; source + git diff xác nhận mutation bị commit
   lẫn vào fleet-label fix. Không restore ở cycle này theo yêu cầu không đụng tiến trình R5.
9. **Stale docs:** sửa current README/SCOPE/USER_STORIES/tracking; thêm banner thay vì viết lại
   historical evidence; đính chính UPDATE-061 “DATA THẬT”.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
|---|---|---|
| `research/audit/2026-07-27-current-state/README.md` | Tạo | Index, executive verdict, phương pháp. |
| `research/audit/2026-07-27-current-state/01-data-lineage-and-update-model.md` | Tạo | 90-day mock, 41 schema, update/cadence, version blocker. |
| `research/audit/2026-07-27-current-state/02-simulation-ui-advisor-parity.md` | Tạo | Current gaps, architecture B, acceptance criteria. |
| `research/audit/2026-07-27-current-state/03-advisor-ux-goals-recap.md` | Tạo | 9 solver, ignore/rest, goals, recap UX. |
| `research/audit/2026-07-27-current-state/04-decision-areas-da01-da06.md` | Tạo | Approved/pending DAs và dependency map. |
| `research/audit/2026-07-27-current-state/05-verification-and-review.md` | Tạo | R5 blocker, evidence ledger, user test list. |
| `tracking/FOLLOWUP-PROMPT-2026-07-27.md` | Tạo | Prompt tiếp tục giàu context/no-touch boundary. |
| `README.md` | Sửa | Current implementation/data status + read order + architecture B. |
| `planning/SCOPE.md` | Sửa | F0 structured FAQ, personal weekly goal, proactive cards, architecture B. |
| `planning/USER_STORIES.md` | Sửa | F0 structured FAQ và personal weekly payout goal. |
| `research/00_SUMMARY.md` | Sửa | Current-state banner + F0 mapping. |
| `research/README.md` | Sửa | Thêm audit/current-state vào catalog. |
| `research/market/order-distribution.md` | Sửa | Banner: research proxy, không phải raw snapshot input. |
| `research/market/dispatch-signals-and-external-apis.md` | Sửa | Banner: brainstorm cũ, không phải runtime stack. |
| `research/experiments/mockgen-realdata/ROUND-2-stats-report.md` | Sửa | Caveat ensemble ≠ artefact-specific verification. |
| `research/audit/2026-07-26-full-audit/README.md` | Sửa | Historical snapshot banner. |
| `research/audit/2026-07-26-full-audit/REPORT.md` | Sửa | Decision/R5 status pointer. |
| `schemas/README.md` | Sửa | Runtime compatibility limitation. |
| `tracking/DIRECTIVES-2026-07-24.md` | Sửa | 179/21+R5-A, 150 profiles, §13 decisions/data/R5. |
| `tracking/TODO.md` | Sửa | T-040 DONE, blockers, stale PI/external/C7 corrections. |
| `tracking/DEFERRED.md` | Sửa | Google closed; external no longer key-blocked. |
| `tracking/PENDING-REVIEW.md` | Sửa | ĐA approvals, DA04-06/Q04, V11-12, blockers, stale V05-07. |
| `tracking/BACKLOG-QUESTIONS-2026-07-27.md` | Sửa | Historical/current architecture clarification. |
| `tracking/updates/UPDATE-061-trackui-u2-webapp-realdata.md` | Sửa | Explicit correction: MOCK content, solver thật. |
| `tracking/updates/UPDATE-073-current-state-data-advisor-docs.md` | Tạo | Nhật ký cycle này. |

## Docs đã cập nhật kèm theo

SCOPE, USER_STORIES, TODO, DEFERRED, DIRECTIVES, PENDING-REVIEW, research index/summary và schema
README đều được đồng bộ. Không sửa CLAUDE.md vì không đổi harness/rules.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| 90-day range/seed/150 profile/engine commit | `FACT` | `data/mock/realdata-v1/manifest.json`; generator | Cao | Mô tả artefact và default UI sai. |
| UI snapshot/trip demo/Advisor không write operational metrics | `OBSERVED-CODE` | mockdata cache, trip endpoint, advice router, source search writer | Cao | Update architecture/test plan sai. |
| 41 schema; minor compatibility chưa runtime-safe | `OBSERVED-CODE` | file count; SchemaRegistry; const/additionalProperties | Cao | Migration/event replay có thể fail. |
| Architecture B và ĐA-01..03 approved | `DECISION` | tin nhắn trực tiếp của Cường 2026-07-27 | Cao | Scope implementation/handoff sai. |
| ĐA-04..06, ignore/goals/recap | `PROPOSAL` | code gaps + specs + UX/HCI/official product research | TB–Cao | Chưa được phép implement; Cường có thể đổi product behavior. |
| `MUT10` committed accidentally | `OBSERVED-CODE` / `HYPOTHESIS` về nguyên nhân | source hiện tại + `git show 7739b3c`; R5 transcript | Cao cho mutation; TB cho “accidental” tới khi R5 xác nhận | Solver baseline/test claims không đáng tin. |

## Kiểm chứng

- `git diff --check` — PASS sau khi sửa một trailing whitespace.
- Local Markdown link checker trên **25 docs gồm UPDATE-073** — PASS.
- Markdown table-shape checker — phát hiện dòng lịch sử `D-SIM-12` thiếu cột; đã bổ sung điều kiện
  mở lại và rerun PASS trên 10 file có bảng trọng yếu.
- `rg --files schemas -g '*.schema.json'` — **41**; vòng đầu ghi nhầm 39 đã bị kiểm chứng bắt và sửa.
- Stale-claim scan cho `chưa có code`, F0 Q&A, 110/150 profile, 168/16, Google blocked,
  “DATA THẬT”; current docs sửa, historical updates giữ kèm banner/đính chính.
- Scope check `git status --short` — chỉ Markdown; không `src/`, `ui/`, `tests/`, config, JSON schema
  hay data.
- R5 mutation verify: source hiện tại + `git show 7739b3c -- src/gsm_core/solvers/shift_dp.py`.
- Không chạy pytest/full suite: docs-only và baseline source đang chứa R5 mutation chưa được phép sửa.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
|---|---|---|---|---|
| Không chạy simulation trong cycle docs | — | — | Dùng manifest/code/audit artefacts hiện có | Không tái tạo 90-day Parquet hoặc A/B. |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** docs-only; không thay đổi UI/sim output.
- **Seed / scenario đã xem:** không có run mới.
- **Người review + verdict:** Cường đã chốt option B qua hội thoại/visual companion context.
- **Lý do:** cycle chỉ sửa Markdown; V-01..V-12 vẫn ở PENDING-REVIEW.

## Adversarial self-review / flaws found

1. Schema count ban đầu bị ghi 39; mechanical recount ra 41 và đã sửa trước handoff.
2. Không dùng “schema thật” để gọi toàn bộ 41 schema là GSM; chỉ 13 L1R có shape metadata GSM.
3. Không dùng R2 30-seed để certify snapshot local; ghi rõ `D-SIM-08`.
4. Không sửa lặng audit/UPDATE lịch sử; thêm banner và correction trail.
5. Không coi subagent batch bị quota là verification hoàn tất.
6. Không chạy full suite trên mutation rồi báo xanh; để blocker cho đúng R5 owner/cycle.
7. External cadence đề xuất là PROPOSAL, không mô tả như runtime đã có.
8. Architecture B giữ hai audience/UI khác nhau; “same projection source” không bị diễn giải thành
   app tài xế phải hiển thị dashboard dispatcher.

## Expansion checkpoint (T-039)

1. **Schema:** cần `SourceEnvelope`, version-aware registry/upcaster, `PersonalGoal`,
   `GoalAssessment`, `Recap`, `AdviceLifecycleEvent`, và card envelope v2 — tất cả mới là proposal.
2. **Bài toán tối ưu:** ĐA-01..03 đã duyệt design; ĐA-04 cadence policy, ĐA-05 lifecycle store,
   ĐA-06 card contract chờ duyệt. ĐA-02 B2 chờ policy truth.
3. **Tính năng:** architecture B mở actor-link từ dispatcher sim sang driver projection; personal
   goal/recap và ignore-aware Advisor khả thi sau canonical projections/lifecycle.

## Follow-up / defer phát sinh

- `B-01 / BLOCKER-R5-MUT10`: R5 restore + regression/full verification.
- `B-02 / BLOCKER-ARCH-VERSION`: version-aware registry/upcaster trước ĐA-05/06.
- Cường duyệt/điều chỉnh Q-04 và ĐA-04..06.
- Sau implementation architecture B: canonical parity fixture, money conservation, lifecycle,
  accessibility và ≥30 paired-seed evaluation.
- Nhắc lại mọi mục Cường cần check: `tracking/PENDING-REVIEW.md` V-01..V-12, Q-03/Q-04,
  ĐA-04..06 và B-01/B-02.
