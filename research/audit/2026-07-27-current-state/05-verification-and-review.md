# 05 — Verification ledger và danh sách Cường cần kiểm tra

## 1. Baseline và phạm vi verify

- HEAD đã đọc: `7739b3c`.
- Worktree sạch trước khi tạo dossier.
- Cycle này chỉ thay Markdown; không sửa `src/`, `ui/`, `tests/`, config, schema JSON hoặc data.
- `http://localhost:60217/` là visual companion cho lựa chọn kiến trúc: Cường đã đổi verdict cuối
  sang **B**. Các click A/C trước đó là exploration, không còn là decision.
- Batch subagent fact-check bổ sung bị quota; không overclaim là đã hoàn thành batch đó.

## 2. BLOCKER-R5-MUT10 — cần xử lý trước khi tin full-suite claim mới

**OBSERVED-CODE:** [`src/gsm_core/solvers/shift_dp.py`](../../../src/gsm_core/solvers/shift_dp.py)
hiện có:

```python
return int(params["soc_cost_per_bucket"])   # MUT10: bo scale bucket_min
```

trong khi docstring và config yêu cầu scale theo `bucket_min`. `git show 7739b3c --
src/gsm_core/solvers/shift_dp.py` chứng minh commit fleet-label đã đổi từ implementation đúng:

```python
max(1, round(soc_cost_per_bucket * bucket_min / 30.0))
```

sang mutation trên. Commit message không khai báo thay đổi solver. UPDATE-071 lại nói mutation tạm
đã được khôi phục và suite xanh, nên claim lịch sử đó không còn đúng với HEAD hiện tại.

**Không sửa trong phiên này** vì R5/Fable đang dở và Cường yêu cầu không đụng tiến trình đó.

### Cường/R5 cần làm

1. xác nhận mutation có phải artefact mutation-test bị commit nhầm;
2. restore đúng implementation trong chính cycle R5;
3. thêm/kiểm test phải đỏ khi `bucket_min != 30`;
4. chạy targeted S2 tests rồi full suite;
5. lập UPDATE R5, ghi rõ commit 7739 đã chứa mutation và claim nào được đính chính.

## 3. Finding R5 đang dở — không coi là đã fix

Attachment/session R5 còn ghi các finding có repro nhưng chưa hoàn tất fix/verify, gồm:

- sim journey bỏ event `end_shift` day bonus;
- censored trip bị map thành cancelled;
- system guardrail có payload nhưng UI không hiển thị;
- journey field fare/distance mislabel;
- replay thiếu idle/trip-rated/advice event hoặc time bị truncate;
- cache/duplicate run/thundering herd;
- sweep metadata/30-seed overclaim;
- UI cards lifecycle: auto-evict, double tap, telemetry failure, profile drift, TOCTOU driving;
- S1 `already_maxed` display path có thể im lặng sai khi eligibility fail;
- adapter R5 note: fake H3 zones, payout>gross, date-blind missions, unread penalty table.

Một số patch được soạn trong scratchpad nhưng command write bị classifier/quota chặn. Worktree trước
dossier sạch, nên **không được suy rằng patch đó đã vào repo**. Resume R5 phải đọc source hiện tại,
không copy trạng thái từ transcript.

## 4. Verify ba vòng cho các kết luận data

| Claim | Vòng 1 | Vòng 2 | Vòng 3 | Verdict |
|---|---|---|---|---|
| Snapshot là MOCK 90 ngày | manifest | generator/script | adapter + git tracking | Confirmed. |
| 150 profile, không phải 110 | cộng manifest profile universe | catalog adapter | docs stale scan | Confirmed. |
| UI không tự cập nhật sau trip/advice | trip endpoint/action router | mockdata cache/read-only | không có writer/scheduler | Confirmed. |
| Sim actor cập nhật state trong RAM | world event handlers | multiday memory/export | L1R generator | Confirmed. |
| R2 không verify artefact local | đọc report command/scope | audit D-SIM-08 | manifest không chứa R2 artefact hash | Confirmed gap. |
| External cadence chưa có | `.env.example`/DIRECTIVES | source search provider | Advisor inputs | Confirmed. |
| Schema minor compatibility overclaim | README | registry one-file/entity | const + additionalProperties false | Confirmed blocker. |

## 5. Cường có thể kiểm ngay — trạng thái hiện tại

### Ưu tiên 0: R5 integrity

- [ ] Mở `shift_dp.py::_soc_cost`, xác nhận `MUT10`.
- [ ] Resume đúng phiên R5/Fable; không để một session khác sửa chồng.
- [ ] Sau restore, chạy targeted mutation/regression rồi full suite; đọc output cuối, không dựa vào
  con số test trong UPDATE cũ.

### Ưu tiên 1: hiểu data 90 ngày

- [ ] Mở `data/mock/realdata-v1/manifest.json`: kiểm label, range, engine commit, 150 profile.
- [ ] So `default_view()` với ngày cuối 2026-09-28; xác nhận app đang mở ngày tương lai mock.
- [ ] Thử một driver/date, bấm cuốc demo và gọi lại `/driver/state`: xác nhận payout/rate không đổi.
- [ ] Restart backend sau regen để thấy cache behavior.
- [ ] Đọc banner mới trên ba tab research đang mở: research/benchmark không phải runtime/provider.

### Ưu tiên 2: hiểu hai demo

- [ ] Simulation demo: đánh giá toàn hệ thống, A/B/C, fairness và system guardrail.
- [ ] Driver app demo: đứng ở một actor, chỉ xem state/advice/interaction của actor đó.
- [ ] Xác nhận kỳ vọng: hai UI khác nhau, nhưng khi cùng run/actor/time thì money/state reconcile.

### Ưu tiên 3: UX direction

- [ ] Duyệt state machine ignore/rest ở `03-advisor-ux-goals-recap.md`.
- [ ] Duyệt việc tách personal goal / policy quota / mission.
- [ ] Duyệt nội dung shift/weekly recap và nguyên tắc “fancy nhưng không coercive”.

### Ưu tiên 4: quyết định còn mở

- [ ] ĐA-04: duyệt cadence common + baseline 20 phút/topic, 6 advice/shift, one coin/decision revision.
- [ ] ĐA-05: duyệt SQLite append-only canonical store + projections + JSONL export.
- [ ] ĐA-06: duyệt card envelope v2 list-of-cards + v1 adapter/deprecation.

Danh sách visual cũ V-01..V-10 vẫn nằm tại
[`tracking/PENDING-REVIEW.md`](../../../tracking/PENDING-REVIEW.md); dossier không tự đóng các mục đó.

## 6. Test plan sau khi architecture B được implement

### Canonical parity fixture

1. chạy một seed cố định, chọn actor và ba mốc `as_of`;
2. lấy dispatcher projection và driver projection;
3. reconcile counts/state/money/mission/event outcomes;
4. render simulation demo và app demo từ hai projection;
5. snapshot/golden test chỉ presentation; assertion domain nằm ở projection/ledger.

### Money conservation

- tổng driver ledger = fleet payout;
- gross, platform share, payout, bonus, penalty và net không lẫn unit/basis;
- route distance thay đổi không tự đổi fare nếu policy input không đổi;
- no future ledger entry ở `as_of` sớm.

### Advice lifecycle

- dismiss rest → không re-present trong window;
- no-response ≠ dismiss;
- one adherence draw per decision revision;
- expired/superseded/outbox retry/dedupe;
- telemetry write fail không giả thành action thành công;
- moving state blocks visual card.

### Goal/recap

- đổi/skip goal không đổi dispatch/pay/rate/tier;
- progress chỉ từ ledger đến `as_of`;
- policy quota và mission render ở section riêng;
- partial net; timezone/week boundary; goal revision mid-week;
- accessibility: reduced-motion, contrast, focus, keyboard, touch targets.

### Statistical/evaluation

- exact-repeat deterministic fixtures;
- stochastic behavior ≥5 seeds;
- calibration/distribution/A-B conclusion ≥30 paired seeds hoặc plan nêu power khác;
- report driver/system/fairness, CI, negative seeds và assumption sensitivity;
- không dùng synthetic uplift để claim hiệu quả thật.

## 7. Điều chưa kiểm chứng trong cycle docs này

- Không chạy full test suite vì source HEAD đang chứa mutation R5 và cycle không được tiếp quản fix.
- Không launch/modify UI: docs-only, visual gate `NOT_APPLICABLE`.
- Không verify live API/provider cadence vì hiện không có integration runtime.
- Không khẳng định nội dung 90-day Parquet trên máy khác giống máy này; Parquet không được Git track.
- Không đánh giá visual Flutter, vì thư mục đó thuộc claim Khánh và audit cũ cũng khai không phủ.

