---
issue_id: "{{issue_id}}"
created: "{{created}}"
category: "{{category}}"
subcriterion: "{{subcriterion}}"
severity: "{{severity}}"
flagged_path: "{{flagged_path}}"
folder_scope: "{{folder_scope}}"        # filesystem | tasks | meta | unknown
writer_fixable: {{writer_fixable}}
specialist_agent: "{{specialist_agent}}"
regression_status: "{{regression_status}}"  # PASS | FAIL | HUMAN_REVIEW | PASS_NO_EDIT
final_action: "{{final_action}}"        # fix | override | escalate | human_review | no_edit
status: "{{status}}"                     # open | resolved | escalated
tags: [autoqc, "{{category_tag}}", "{{regression_status}}"]
---

# {{issue_id}} — {{category}} / {{subcriterion}}

> Human-readable mirror of the structured record in Supabase. Supabase is the source of truth;
> this note is for reading/linking. See [[index]].

## Finding
- **Flagged path:** `{{flagged_path}}`  (scope: **{{folder_scope}}**)
- **Severity:** {{severity}}
- **Offending text:** {{offending_text}}

## Classification (intake-classifier)
{{issue_summary}}
- writer_fixable: **{{writer_fixable}}** · recommended_action: **{{recommended_action}}**

## Diagnosis + proposal ({{specialist_agent}})
{{diagnosis}}

**Proposed change:** {{proposed_change}}
**Regression concerns:** {{regression_concerns}}

## Regression verdict ({{regression_status}})
{{regression_rationale}}
- do_not_touch: {{do_not_touch}}

## Outcome
- **Final action:** {{final_action}}
- **Patched copy:** {{patched_path}}
- **EPM note:**
{{epm_note}}

## Links
- Category MOC: [[{{category}}]]
- Related issues: {{related_issue_links}}
