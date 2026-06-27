# File Map — World State

The Orchestrator consults this map to reason about **where** a flagged file lives and **what
else** a fix might affect — **without** loading every file into context. It holds *state about*
files, not the files themselves.

This is a Phase 2 scaffold. The structure below is the intended shape; the concrete file
inventory gets populated when a real Project Sanctum world is loaded (and, in Phase 6, mirrored
into Supabase's `world_files` table).

## Scopes

| Scope prefix | Meaning | Edit stance |
|---|---|---|
| `filesystem/` | World-facing clinical documents | Possible writer-fixable world-file issue |
| `tasks/` | Task config and task assets (e.g. `task.json`) | Not a world-file edit by default |
| `.meta/` | Pipeline bookkeeping / metadata | Escalate or document |
| *(unrecognized)* | Unknown | Ask for files / clarification |

## File-map entry shape

Each tracked file is one entry. The Orchestrator reads these fields; it does **not** read file
bodies unless a specialist later requires it.

```yaml
- path: filesystem/patient/notes/progress_note_2025-06-14.md
  folder_scope: filesystem
  doc_type: progress_note          # note | discharge | med_list | lab | task_config | meta
  patient_id: P001                 # for grouping cross-document siblings
  date: 2025-06-14                 # for temporal reasoning (<= July 2025)
  shared_fields: [name, dob, mrn]  # fields that must agree across documents
  related_paths:                   # cross-document siblings a fix could ripple into
    - filesystem/patient/notes/discharge_summary_2025-06-16.md
    - filesystem/patient/meds/medication_list.md
  traps: []                        # ids/notes of intentional traps living in this file
  notes: ""
```

## How the Orchestrator uses it

1. **Confirm scope** — match `flagged_path` to a scope; reconcile with the classifier's
   `folder_scope`.
2. **Find siblings** — pull `related_paths` and `shared_fields` so a proposed fix's blast radius
   is known *before* anything is proposed. (This is what the Regression Agent will later check
   against.)
3. **Flag traps** — if the flagged file (or a sibling) carries a `traps` entry, mark it
   `do_not_touch` and lean toward human review.
4. **Stay light** — never load the bodies of `related_paths`; track them by reference only.

## Cross-document groups

Files that share a `patient_id` form a consistency group. Cross-Document Consistency, Medication
Reconciliation, and Temporal Integrity issues are evaluated **across the whole group**, which is
exactly why a single-file fix can break a sibling. The map exists to make those groups visible.

## Status

Empty inventory for now (no live world loaded). Populate by listing a real
`filesystem/` + `tasks/` + `.meta/` tree, or generate it programmatically in a later phase.
