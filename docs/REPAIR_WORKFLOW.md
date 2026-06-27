# Repair Workflow — End to End

How a writer uses this system, and how the agents chain together. This is the complete pipeline
(Phases 1–5). Real testing happens by dropping a real AutoQC run + world tree into it.

## The writer's loop

```
1. Writer runs their world files through AutoQC.
2. AutoQC returns findings (pass/fail across the 9 categories).
3. Writer reviews the output world files + findings.
4. Writer runs THIS system:  /autoqc-repair  (paste the finding(s))
5. System returns: classification → routed diagnosis → regression verdict →
   patched copy in _repaired/ (only if PASS), or override/escalate/human-review.
6. Writer re-runs AutoQC on the _repaired/ tree to confirm.
```

The system's job is step 5: fix the finding **without** creating a new failure in another
category — and never touch the writer's original files.

## Agent chain (what runs, in order)

```
        paste AutoQC finding
                │
                ▼
      ┌───────────────────┐
      │ intake-classifier │  category, subcriterion, severity, flagged_path,
      │   (read-only)     │  folder_scope, writer_fixable, recommended_action
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │   orchestrator    │  validates scope, consults file map,
      │   (read-only)     │  routes to the right specialist
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │   specialist ×1   │  diagnoses + PROPOSES (one of 9 categories);
      │   (propose-only)  │  emits regression_concerns; never edits
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐     FAIL  ──────► back to specialist (re-propose)
      │  regression-agent │     HUMAN_REVIEW ► stop, escalate to pod lead
      │   (the GATE)      │     PASS_NO_EDIT ► override/escalate, no edit
      └─────────┬─────────┘     PASS ─────────┐
                                              ▼
                                  ┌───────────────────┐
                                  │   patch-engine    │  applies ONLY approved patch,
                                  │ (copy-on-write)   │  to _repaired/, never originals
                                  └─────────┬─────────┘
                                            ▼
                                  re-run AutoQC on _repaired/
```

## The four verdicts (what each means for the writer)

| Verdict | What happened | Writer's next step |
|---|---|---|
| **PASS** | Fix is safe across all 9 categories; patch-engine applied it to `_repaired/` | Re-run AutoQC on `_repaired/` |
| **FAIL** | Proposed fix would break another category; bounced back to the specialist | System re-proposes; review the blocking reasons |
| **HUMAN_REVIEW** | Needs clinical judgment or trap-vs-error intent call | Pod lead decides before anything is applied |
| **PASS_NO_EDIT** | Issue is internal (`tasks/`/`meta/`), a false positive, or should be overridden | Document / override / escalate — do **not** edit world files |

## Safety invariants (always true)

- **Originals are never overwritten.** All edits land in `_repaired/` (copy-on-write).
- **No patch without a regression `PASS`.** The gate is mandatory.
- **Traps are preserved.** Never defused, labeled, or weakened.
- **Intentional inconsistencies stay.** Different-date draws, scope-appropriate omissions,
  documented traps are not "fixed."
- **Scope governs.** `tasks/` and `meta/` findings are not world-file edits.
- **Filesystem governs** filename drift (see `docs/REFERENCE_PIPELINE.md`).

## Output the writer receives

A consolidated **repair report**, one block per finding:

- the classification JSON (from intake-classifier),
- the specialist's proposal + `regression_concerns`,
- the regression verdict JSON (PASS / FAIL / HUMAN_REVIEW / PASS_NO_EDIT),
- what the patch-engine did (or why it refused), and
- a copy-pasteable `epm_note` for the pod workflow.

Plus, on any `PASS`, a `_repaired/` tree with the patched file(s) and a `_repaired/PATCH_LOG.md`.

## Worked reference

A real run of this pipeline on the Task 7 `tasks/T1/task.json` residue (verified: residue in
`tasks/`, all 21 world files clean, golden answer isolated) correctly returns **PASS_NO_EDIT** —
no world files touched, traps preserved, escalate instead. See `docs/REFERENCE_PIPELINE.md`.

## Production note

In Claude Code today, this runs as the subagent chain above (the `/autoqc-repair` command drives
it). For the workplace deployment, the same logic is wrapped as an MCP server on a VPS so the team
invokes it from their own Claude Code — the agent definitions are the source of truth either way.
The `patch-engine` is the component that becomes hardened deterministic code at deploy time.
