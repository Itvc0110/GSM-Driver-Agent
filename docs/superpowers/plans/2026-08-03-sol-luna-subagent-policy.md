# Sol → Luna Subagent Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stale root `AGENTS.md` pack notice with durable Codex workflow guidance that makes Sol read `CLAUDE.md`, delegates bounded work to Luna at `xhigh`, and respects the repository’s two-session quota guard.

**Architecture:** `CLAUDE.md` remains the authoritative harness. `AGENTS.md` is a supplemental repository instruction that documents the delegation decision gate, explicit runtime model override, queueing, disjoint write scopes, and result review. A required docs-only UPDATE/TODO/graph entry records the change; no runtime configuration or application code changes are needed.

**Tech Stack:** Markdown, Codex multi-agent runtime, shell-based diff checks.

## Global Constraints

- Read `CLAUDE.md` first; it wins over `AGENTS.md` on conflict.
- Keep the current `CLAUDE.md` cap of 2 concurrent sessions total (primary + reviewer).
- Use `gpt-5.6-luna` with `reasoning_effort: "xhigh"` for every delegated subagent when the runtime supports overrides.
- Do not alter unrelated dirty files or commit without an explicit request.

---

### Task 1: Replace stale delegation guidance

**Files:**
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: `CLAUDE.md` as the authoritative project harness.
- Produces: a root-level supplemental instruction for future Codex sessions.

- [x] **Step 1: Replace the superseded pack text**

Write the current read order, Sol pre-delegation gate, Luna runtime override, two-session cap, queueing rule, quota fallback, disjoint write-scope rule, and post-spawn review steps. Remove stale Dev A/Dev B ownership and old pack-specific architecture rules.

- [x] **Step 2: Run textual verification**

Run:

```bash
git diff --check
rg -n "CLAUDE\.md|gpt-5\.6-luna|xhigh|2 phiên|2 → 1|QUOTA-BLOCKED|không đọc lại" AGENTS.md
```

Expected: no whitespace errors; every required policy term is present.

- [x] **Step 3: Inspect the scoped diff**

Run:

```bash
git diff -- AGENTS.md docs/superpowers/specs/2026-08-03-sol-luna-subagent-policy-design.md docs/superpowers/plans/2026-08-03-sol-luna-subagent-policy.md
```

Expected: only the intended guidance and planning files are changed; unrelated pre-existing worktree changes are absent from this scoped diff.

### Task 2: Record the harness change in tracking

**Files:**
- Create: `tracking/updates/UPDATE-125-sol-luna-subagent-policy.md`
- Modify: `tracking/TODO.md`
- Modify: `tracking/PROJECT-GRAPH.md`

**Interfaces:**
- Consumes: the final `AGENTS.md` policy and the existing UPDATE template.
- Produces: a traceable docs-only UPDATE, TODO row, and graph link.

- [x] **Step 1: Add the evidence record**

Record the exact model/reasoning override, the `CLAUDE.md` two-session cap, the `2 → 1` queue, the verification commands, `NOT_APPLICABLE` visual status, and any pre-existing graph-validation gaps.

- [x] **Step 2: Verify the scoped tracking links**

Run:

```bash
rg -n "SOL-LUNA-HARNESS|UPDATE-125-sol-luna-subagent-policy" tracking/TODO.md tracking/PROJECT-GRAPH.md tracking/updates/UPDATE-125-sol-luna-subagent-policy.md
```

Expected: the TODO row, graph row, and UPDATE references all exist. A full historical graph scan may still report pre-existing missing links; do not repair those unrelated rows in this cycle.
