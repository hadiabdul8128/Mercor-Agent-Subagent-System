# CLAUDE.md — Project Sanctum AutoQC Repair System

Persistent project instructions for Claude Code working in this repository.

## What this project is

An agent/subagent system that takes a pasted **AutoQC** issue, routes it to the correct
specialist, regression-checks any proposed fix, and only then applies it — so that repairing one
flagged issue does not silently break a different AutoQC category. See `PLAN.md` for the full
architecture and `docs/PROJECT_CONTEXT.md` for domain background.

Current status: **Phases 1-6 built.** The full Claude Code prompt pipeline exists:
Intake/Classifier, Orchestrator, 10 specialist subagents, Regression Agent, Patch Engine, and the
Supabase/Obsidian memory writer. The MCP server wrapper for deployment is still future work.

## Global Rules

1. **Original files must never be overwritten.** All future changes write to copies / new
   versions. The Patch Engine (when built) is copy-on-write.

2. **Subagents diagnose and propose only.** Specialist subagents do not apply patches. They emit
   a proposal and a rationale. Application is a separate, later, deterministic step.

3. **No patching without a Regression Agent PASS.** Specialist agents stop at "proposed fix."
   The Patch Engine may write only after `regression_status: "PASS"` and `safe_to_apply: true`.

4. **Classify folder scope before recommending any fix.** Always determine whether the flagged
   path is in `filesystem/`, `tasks/`, or `.meta/` first:
   - `filesystem/` → possible writer-fixable world-file issue.
   - `tasks/` → task config or task asset; do **not** assume a world-file edit.
   - `.meta/` → pipeline bookkeeping/metadata; usually escalate or document.
   - `unknown` → ask for files or clarification.

5. **Preserve intentional traps.** Traps are deliberate. Never remove, defuse, or "clean up" a
   trap while fixing something else. If a fix would alter a trap, escalate.

6. **Do not normalize all inconsistencies.** Some inconsistencies are intentional (trap
   architecture, realism). Do not globally standardize fields, dates, or wording just because
   they differ. Only address the specific flagged issue.

7. **If clinical judgment is required, request human/pod-lead review.** Do not invent clinical
   values, codes, dosages, or chronology. Route to `human_review`.

8. **Memory writes are optional and credential-gated.** Supabase and Obsidian support are built
   through `memory/sanctum_memory.py`, but only run them when `.env` credentials are present and
   the pipeline has a concrete repair event to record. Do not invent memory rows.

## Operating sequence (once later phases exist)

```
Intake/Classifier → Orchestrator routes → Specialist proposes →
Regression approves → Patch Engine applies to a copy → record to memory
```

No step may be skipped. A proposal may never become an applied patch without regression approval.

## Working norms

- Keep agents narrowly scoped; do not dump every file into context.
- Prefer Read/Grep/Glob over shell file manipulation.
- When in doubt about scope or clinical correctness, **escalate** rather than edit.
- Before pushing instruction changes, run `python3 tools/validate_repo.py`.
