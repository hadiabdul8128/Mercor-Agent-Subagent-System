# Project Sanctum AutoQC — Repair Agent/Subagent System: PLAN

## 1. Project Summary

Project Sanctum writers generate clinical **world files** (synthetic patient charts, notes,
medication lists, task assets). An automated quality checker, **AutoQC**, flags issues across
multiple clinical and structural categories.

This project builds an **agent/subagent system** that takes a pasted AutoQC issue, routes it to
the correct specialist, runs a **regression check** before any change, and only then proposes a
fix. The goal is to stop "whack-a-mole" repairs where fixing one flagged issue silently breaks a
different AutoQC category.

This repo is currently in **Phase 0 / Phase 1**: planning layer plus the first agent (the
Intake / Classifier Agent). No application code, no automatic file editing, and no database
connection yet.

## 2. Problem Statement

Current writer workflow:

1. Writer pastes ONE AutoQC issue into Claude.
2. Claude fixes that one issue locally.
3. AutoQC re-runs.
4. **New** issues appear in *other* categories because the fix damaged cross-document
   consistency, trap architecture, chronology, or formatting.

Root causes:

- No routing: every issue is handled by a generalist with full-file context dumped in.
- No regression gate: a fix is applied before checking its blast radius across other categories.
- No folder-scope awareness: edits land on world files when the real issue is in task config or
  pipeline metadata.
- No preservation guarantees: intentional **traps** and intentional inconsistencies get
  "normalized" away.

## 3. Architecture (text diagram)

```
                    ┌─────────────────────────────┐
   pasted AutoQC →  │   Intake / Classifier Agent │  (Phase 1 — built)
                    │  extract + classify + route │
                    └──────────────┬──────────────┘
                                   │ structured JSON
                                   ▼
                    ┌─────────────────────────────┐
                    │   Main Orchestrator Agent   │  (Phase 2)
                    │  holds file map + world      │
                    │  state; routes; decides      │
                    │  fix/override/escalate/human │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
     │ Specialist Sub- │  │ Specialist Sub- │  │  ... one per     │  (Phase 3)
     │ agent (per      │  │ agent           │  │  AutoQC criterion│
     │ AutoQC category)│  │                 │  │                  │
     │ diagnose+propose│  │ diagnose+propose│  │ diagnose+propose │
     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
              └────────────────────┼────────────────────┘
                                   │ proposed patch (NOT applied)
                                   ▼
                    ┌─────────────────────────────┐
                    │      Regression Agent       │  (Phase 4)
                    │ does this fix break another  │
                    │ AutoQC category? approve/deny │
                    └──────────────┬──────────────┘
                                   │ approved patch only
                                   ▼
                    ┌─────────────────────────────┐
                    │        Patch Engine         │  (Phase 5, deterministic code)
                    │ applies approved patch to a  │
                    │ COPY; originals never        │
                    │ overwritten                  │
                    └─────────────────────────────┘

   Memory Layer (Phase 6): Supabase = structured source of truth;
                           Obsidian = human-readable summaries.
```

## 4. Agent Roles

### Main Orchestrator Agent (Phase 2)
- Holds the file map and world state. Does **not** shove every file into context.
- Receives the Classifier's JSON and routes to the correct specialist subagent.
- Decides whether to **fix**, **override**, **escalate**, or **request human review**.
- Owns the sequencing: specialist → regression → patch engine.

### Intake / Classifier Agent (Phase 1 — built here)
- First agent run whenever a user pastes an AutoQC issue.
- Extracts category, subcriterion, severity, flagged path, offending text, recommended routing.
- Classifies flagged path as `filesystem/`, `tasks/`, `.meta/`, or `unknown`.
- Determines whether the issue is likely writer-fixable.
- Outputs structured JSON plus a short human-readable recommendation.
- **Read-only.** Never proposes or applies edits.

### Specialist Subagents (Phase 3)
- One subagent per AutoQC criterion.
- They **diagnose and propose**. They do **not** directly apply patches.
- Each is scoped to its own criterion so it does not "over-fix" neighboring concerns.

### Regression Agent (Phase 4)
- Checks whether one proposed fix breaks another AutoQC category.
- **No patch is applied without regression approval.**

### Patch Engine (Phase 5)
- Deterministic code, not an LLM.
- Subagents propose patches → Regression Agent approves → Patch Engine applies.
- **Original files are never overwritten** (writes to copies / new versions).

## 5. Specialist Agent Criteria

(Full detail in `docs/AUTOQC_CRITERIA.md`.) One specialist per category:

| Specialist | Subcriteria |
|---|---|
| Solution Integrity | Out-of-World Residue in Document Body and Metadata; Content Leakage; Golden Answer Traceability; World Spec Alignment; Trap Survival Through File Generation |
| Clinical Accuracy | Calculation and Fixture Accuracy; Clinical Values Plausible; Clinical Code Validity |
| Medication Reconciliation | Prescriber Attribution Integrity; Medication List Consistency |
| Cross-Document Consistency | Cross-Document Field Consistency |
| Temporal Integrity | Document Chronology and Sequencing; Task Temporal Anchoring Verified; World Files Dated No Later Than July 2025 |
| Trap Architecture | Traps Logically Resolvable; Trap Documentation and Density |
| Completeness | File Set Complete; Supporting Clinical Data Present |
| Realism and Authenticity | Clinical Cold-Read + AI Tells |
| Documentation Standards | Formatting, Register & Length; Content Completeness (No Gaps) |

## 6. The Repair Loop

```
1. INTAKE      Classifier extracts + classifies + recommends routing.
2. ROUTE       Orchestrator sends issue to the correct specialist subagent.
3. DIAGNOSE    Specialist diagnoses and PROPOSES a patch (does not apply).
4. REGRESS     Regression Agent checks the proposed patch against all other
               AutoQC categories. Approve / deny.
5. APPLY       Only if approved, Patch Engine applies to a copy.
               Originals never overwritten.
6. RECORD      Outcome written to memory (Supabase structured; Obsidian readable).
```

A patch may **never** skip steps 3→4→5 in that order.

## 7. Folder-Scope Routing Rules

| Scope | Meaning | Default stance |
|---|---|---|
| `filesystem/` | World-facing clinical document | Possible **writer-fixable** world-file issue |
| `tasks/` | Task config or task asset | Do **not** assume a world-file edit is needed |
| `.meta/` | Pipeline bookkeeping / metadata | Usually **escalate or document**, not writer-edit |
| `unknown` | Path not recognized | **Ask for files or clarification** |

**Worked example (the canonical case):**

AutoQC says:
> "Solution Integrity failed: `pipeline_output/tasks/T1/task.json` contains a notes field
> reading 'Generated by task_gen_standalone. Trap: ... correct response assigns ...'"

Correct classification:
- category: **Solution Integrity**
- subcriterion: **Out-of-World Residue in Document Body and Metadata**
- flagged path: `pipeline_output/tasks/T1/task.json`
- folder scope: **tasks**
- writer-fixable: **false**
- likely action: **override_or_escalate**
- recommendation: Do **not** edit `filesystem/` world files. The residue is inside internal
  task config, not a world-facing clinical document.

## 8. Memory Plan

Not implemented yet — documented intent only.

**Supabase (structured source of truth):** proposed schema

- `issues` — one row per AutoQC issue: `id`, `created_at`, `category`, `subcriterion`,
  `severity`, `flagged_path`, `folder_scope`, `offending_text`, `issue_summary`,
  `writer_fixable`, `recommended_action`, `specialist_agent`, `status`.
- `proposals` — one row per specialist proposal: `id`, `issue_id`, `specialist_agent`,
  `proposed_patch`, `rationale`, `created_at`.
- `regressions` — `id`, `proposal_id`, `verdict` (approve/deny), `categories_checked`,
  `conflicts_found`, `created_at`.
- `patches` — `id`, `proposal_id`, `applied`, `copy_path`, `applied_at`.
- `world_files` — file map: `path`, `folder_scope`, `last_seen`, `hash`.

**Obsidian (human-readable layer):** one markdown note per issue summarizing classification,
proposal, regression verdict, and final action — for pod leads to read.

## 9. Regression Plan

- Every specialist proposal must pass the Regression Agent before the Patch Engine runs.
- The Regression Agent re-evaluates the proposed change against **all nine** AutoQC categories,
  not just the originating one.
- Verdict is binary (approve / deny) with a list of categories checked and any conflicts found.
- Denials return to the specialist with the conflict, or escalate to human review.

## 10. MVP Phases

- **Phase 0** — Planning/context layer. *(this commit)*
- **Phase 1** — Intake / Classifier Agent. *(this commit)*
- **Phase 2** — Main Orchestrator Agent + file map.
- **Phase 3** — Specialist subagents (one per criterion).
- **Phase 4** — Regression Agent.
- **Phase 5** — Patch Engine (deterministic, copy-on-write).
- **Phase 6** — Memory layer (Supabase + Obsidian).

## 11. Non-Goals (for now)

- No automatic file editing.
- No connection to Supabase yet.
- No specialist subagents beyond documentation yet.
- No overwriting of original files, ever.
- No normalization of intentional inconsistencies or removal of intentional traps.
- No clinical judgment calls made unilaterally — those go to human/pod-lead review.
