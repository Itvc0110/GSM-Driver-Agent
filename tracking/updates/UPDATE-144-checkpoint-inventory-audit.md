# UPDATE-144 — AdviceCheckpoint inventory audit (read-only)

- **Ngày:** 2026-08-05
- **Người thực hiện:** AI agent dưới quyền chung Cường + Khánh
- **Loại:** research / evidence-only
- **Trạng thái:** `DONE-CODE` cho artifact audit; không thay đổi runtime, policy, cadence, UI, solver objective hoặc feature flag
- **Tracking scope:** không đóng V-25, không claim production-ready, không thêm checkpoint giả

## Kết quả

Đã chạy lại đúng run factory của Web demo `ui/backend/app/services/demo_session.py:_default_run` trên 5 seed `1000–1004` và dựng pure `gsm_sim.demo_trace.build_demo_trace` cho các actor. Kết quả:

- 864 checkpoint records;
- projected state: 413 `ready`, 450 `suppressed`, 0 `queued`, 1 `expired`, 0 `superseded`;
- 412 checkpoint references được attach đúng một lần, 452 không attach, 0 attach trùng trong từng run;
- 815 `execution_observed` side-channel events/links;
- 0 `offered`, `displayed`, `accepted`, `dismissed`, `expanded` trong RunResult — đây là product presentation stream, không suy ra từ simulator;
- 205 `checkpoint_id` lặp giữa nhiều run, do identity deterministic; artifact join theo `(run_id, checkpoint_id)`.
- Một record S2/SWAP ở seed 1003 kết thúc `expired` với `valid_until < valid_from`; không attach/offer và được giữ làm regression edge case. Không có `superseded`/`queued`/recap trong sample.

## Artifact

Tất cả nằm trong `research/audit/2026-08-05-checkpoint-inventory/`:

- `checkpoint-audit.md` — catalog, trigger/purpose, lifecycle funnel, template/UI boundary, risks và demo candidates;
- `checkpoint-by-actor.csv` — thống kê theo seed/actor và aggregate actor;
- `checkpoint-by-type.csv` — thống kê source/topic/action, READY/suppressed/execution/validity/gap;
- `checkpoint-timeline.json` — checkpoint records, lifecycle, artifact-derived capture state, compact transitions, audit attachments và scenario candidates;
- `analyze_checkpoints.py` — script rerunnable, không ghi telemetry và không gọi lease/product presentation.

Reproduction:

```text
PYTHONPATH=src:ui/backend .venv/bin/python \
  research/audit/2026-08-05-checkpoint-inventory/analyze_checkpoints.py \
  --seeds 1000 1001 1002 1003 1004
```

## Evidence / boundary

- Producer callsites: `src/gsm_sim/advice_bridge.py:597,747,903,950` và S4 `src/gsm_sim/world.py:455`.
- Observer-only capture: `src/gsm_sim/checkpoint_trace.py:128-213`; post-run execution linking `:215-292`.
- READY attachment/primary selection: `src/gsm_sim/demo_trace.py:176-251`.
- Deterministic templates: `src/gsm_core/advisor/checkpoint_templates.py:72-142`.
- Product lease/intent boundary: `ui/backend/app/services/demo_session.py:323-408` và `ui/backend/app/services/advice_checkpoint.py:393-489,791-871`.

Trace `ready` không đồng nghĩa card đã offered/displayed. `execution_observed` mặc định `coincident`/confidence `0.6`, không phải bằng chứng causal/adherence. S4 positioning vẫn simulator-only; recap, queued, superseded và phần lớn expiry không có producer trong sample, nên không tạo fixture để lấp khoảng trống demo.

## Verification

- Analysis script: exit 0 trên cả 5 seed; output summary `checkpoint_count=864`.
- Script syntax: `PYTHONPATH=src:ui/backend .venv/bin/python -m py_compile .../analyze_checkpoints.py` exit 0.
- Không chạy full backend/simulator/solver suite; đây là audit dữ liệu bounded, không phải regression gate.
- Không có visual gate trong cycle này; artifact-only, V-25 vẫn chờ human/browser/device review.

## Adversarial review

1. Không dùng `checkpoint_id` đơn độc khi gộp nhiều run; script đã khóa `(run_id, checkpoint_id)`.
2. Không gọi `accepted/displayed` là adherence; product event counts để `0` khi RunResult không có presentation.
3. Chỉ chọn demo checkpoint `READY`, attach đúng một transition và không ở `enroute/on_trip`; expired/superseded được đánh dấu lifecycle-only.
4. Không coi current/future `ONLINE→SWAP`, queued, recap hoặc actor không checkpoint là có thật khi sample không chứng minh.

## Follow-up mở

- Owner chọn seed/actor từ artifact cho browser demo 3–5 bước.
- Nếu cần test offered/displayed/intent funnel, chạy một Web session riêng và join theo `run_id + checkpoint_id + display_id`.
- Nếu cần demo queued/expired/superseded/recap, owner phải chốt scenario/replay semantics; audit này không thay policy để tạo chúng.
