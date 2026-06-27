---
description: Classify a pasted AutoQC issue using the Intake / Classifier Agent.
---

# /classify-autoqc

Manually classify a pasted AutoQC issue. This command runs the **Intake / Classifier Agent**
behavior over whatever AutoQC text follows.

## Usage

```
/classify-autoqc
<paste the full AutoQC issue text here>
```

You can paste the AutoQC text on the lines after the command, or run the command and paste when
prompted.

## What Claude should do

1. Use the `intake-classifier` agent (`.claude/agents/intake-classifier.md`). Follow its
   instructions exactly. Stay **read-only** — classify and route only; do not propose or apply
   any fix.

2. Take the pasted AutoQC text as input: `$ARGUMENTS` (if the user pasted text on the command
   line). If no text was provided, ask the user to paste the AutoQC issue.

3. Extract: category, subcriterion, severity, flagged path, offending text, issue summary.

4. Classify **folder scope** from the flagged path before recommending anything:
   `filesystem` (possible writer-fixable world-file issue), `tasks` (task config/asset — do not
   assume a world-file edit), `meta` (pipeline bookkeeping — usually escalate), or `unknown`
   (ask for files/clarification).

5. Judge **writer_fixable** and set **recommended_action** to one of
   `fix | override | escalate | human_review | needs_files`.

6. Preserve intentional traps and intentional inconsistencies — list anything that must be
   protected in `do_not_touch`. Never normalize or defuse.

7. Output **both**:
   - the structured JSON block defined in the agent spec, and
   - a short human-readable recommendation.

## Reminders

- Folder scope governs writer-fixability more than the category does.
- If clinical judgment is required, recommend `human_review`.
- This command never edits files. It only classifies and routes.
