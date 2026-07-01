---
description: Run the full AutoQC repair pipeline on a pasted AutoQC issue (classify → route → diagnose → regression gate → patch). The writer's main entry point.
---

# /autoqc-repair

The **main entry point** for a writer. Paste an AutoQC issue (and make sure the world tree —
`filesystem/`, `tasks/`, `meta/` — is available in the working directory). This command drives the
entire repair pipeline end to end and never touches original files.

## Usage

```
/autoqc-repair
<paste the AutoQC finding(s) here — the category line, flagged path, and offending text>
```

Input text: `$ARGUMENTS`. If empty, ask the writer to paste the AutoQC finding and confirm where
the world tree lives.

## Pipeline to run (in order — never skip a step)

For **each** AutoQC finding:

**1. Classify** — run the `intake-classifier` agent. Get category, subcriterion, severity,
flagged path, folder scope, offending text, writer-fixability, recommended action.

**2. Route** — run the `orchestrator` agent on the classifier JSON. It validates scope, consults
`docs/FILE_MAP.md` / the world tree, and decides the next agent.

**3. Diagnose + propose** — run the specialist named by the orchestrator (one of the 10). It
**proposes only**, with `regression_concerns`. It never edits.

**4. Regression gate** — run the `regression-agent` on the proposal. It checks all 10 categories
and returns `PASS`, `FAIL`, `HUMAN_REVIEW`, or `PASS_NO_EDIT`.

**5. Act on the verdict:**
   - `PASS` → run the `patch-engine`. It applies the approved change **copy-on-write to
     `_repaired/`**, never to originals, then logs it.
   - `FAIL` → return to the specialist (step 3) with the blocking reasons; re-propose.
   - `HUMAN_REVIEW` → STOP. Surface the issue for a human / pod lead. Apply nothing.
   - `PASS_NO_EDIT` → no edit (override/escalate). Record the recommendation.

**6. Report** — produce the consolidated repair report (see `docs/REPAIR_WORKFLOW.md`): per
finding, the classification, verdict, and what was (or was not) done, plus the final action.

## Hard rules (from CLAUDE.md)

- Originals are **never** overwritten. Patches land in `_repaired/` only.
- No patch is applied without a `regression-agent` `PASS`.
- Preserve intentional traps; never normalize intentional inconsistencies.
- `tasks/` and `meta/` issues are **not** world-file edits — expect override/escalate.
- Clinical judgment → `HUMAN_REVIEW`.
- Respect "filesystem governs" filename drift (see `docs/REFERENCE_PIPELINE.md`).

## After the run

Tell the writer to **re-run AutoQC on the `_repaired/` tree** to confirm the fix landed and no new
category regressed — the loop that closes the workflow.
