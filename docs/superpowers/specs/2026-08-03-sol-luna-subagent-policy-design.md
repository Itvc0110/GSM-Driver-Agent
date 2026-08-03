# Sol → Luna Subagent Policy Design

**Date:** 2026-08-03

## Goal

Make the repository’s durable agent guidance tell the primary `gpt-5.6-sol` agent when and how to delegate bounded work to `gpt-5.6-luna` at `xhigh` reasoning, while limiting parallel work to protect quota and avoid conflicting edits.

## Scope

- Update the root `AGENTS.md` from the superseded pack notice to a small repository-specific delegation policy, with the required tracking UPDATE/index entry.
- Keep `CLAUDE.md` as the authority for project scope, claims, planning, evidence, and product boundaries.
- Do not change the primary model, global Codex configuration, source code, tests, or active user changes.

## Design

`AGENTS.md` adds one behavioral layer:

1. Sol first inspects the task, identifies the critical path, and writes a compact workflow before spawning anything.
2. Delegation is reserved for independent, bounded tasks. Shared files, overlapping claims, architecture decisions, and the immediate blocking step remain with Sol.
3. Every delegated run explicitly requests `model = "gpt-5.6-luna"` and `reasoning_effort = "xhigh"` through the runtime spawn call. The file does not pretend to configure an unavailable runtime option.
4. The normal parallel cap follows `CLAUDE.md`: at most 2 concurrent sessions total (primary + reviewer). If a task has 3 independent work items, queue them as `2 → 1`; do not silently override the harness cap.
5. Quota/session-limit failures get at most one retry. A repeated failure stops expansion, records `QUOTA-BLOCKED`, and reduces the cap to one worker for the remainder of the task.
6. Sol reviews each result, closes completed workers, integrates changes locally, and owns the final synthesis and verification.

## Runtime boundary

The policy is durable guidance, not a mechanical scheduler. Actual model selection and concurrency are enforced only when the runtime spawn call carries the requested override and the coordinator follows the cap. The existing global config remains responsible for the primary model.

## Acceptance criteria

- `AGENTS.md` clearly states that `CLAUDE.md` wins on conflict.
- It specifies the exact Luna model slug and `xhigh` reasoning effort for every subagent spawn.
- It specifies the `CLAUDE.md` parallelism cap of 2 concurrent sessions, queueing for a third independent task, disjoint write scopes, and quota fallback.
- It requires pre-delegation planning and post-delegation review/closure.
- It contains no stale Dev A/Dev B ownership or old optimizer requirements that contradict `CLAUDE.md`.
- The patch changes only the intended guidance/tracking files and passes a textual review/diff check. Any pre-existing graph coverage gaps remain explicitly reported rather than being silently repaired.

## Verification plan

- Inspect the resulting `AGENTS.md` for all exact policy terms.
- Run `git diff --check`.
- Inspect `git diff -- AGENTS.md docs/superpowers/specs/2026-08-03-sol-luna-subagent-policy-design.md docs/superpowers/plans/2026-08-03-sol-luna-subagent-policy.md` and confirm unrelated dirty files are untouched.
