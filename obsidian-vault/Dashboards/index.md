# AutoQC Repair — Dashboard

Human-readable layer for the Sanctum AutoQC repair system. **Supabase is the structured source of
truth; this vault mirrors it for reading and linking.** One note per AutoQC issue lives in
`Issues/`, created from `Templates/issue-template.md`.

## How to use
- Open in Obsidian (point Obsidian at the `obsidian-vault/` folder as a vault).
- Each issue note carries YAML frontmatter (category, scope, verdict, status) so Dataview /
  search can slice by any field.
- Verdicts: **PASS** (patched), **FAIL** (bounced to specialist), **HUMAN_REVIEW** (pod lead),
  **PASS_NO_EDIT** (override/escalate, no edit).

## Maps of Content (one per AutoQC category)
- [[Solution Integrity]]
- [[Clinical Accuracy]]
- [[Medication Reconciliation]]
- [[Cross-Document Consistency]]
- [[Temporal Integrity]]
- [[Trap Architecture]]
- [[Completeness]]
- [[Realism and Authenticity]]
- [[Documentation Standards]]

## Suggested Dataview queries
(If the Dataview plugin is installed.)

````
```dataview
TABLE category, folder_scope, regression_status, final_action, status
FROM "Issues"
SORT created DESC
```
````

Open items needing a human:
````
```dataview
LIST
FROM "Issues"
WHERE regression_status = "HUMAN_REVIEW" AND status != "resolved"
```
````
