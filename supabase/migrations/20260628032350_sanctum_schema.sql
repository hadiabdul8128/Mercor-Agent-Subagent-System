-- Sanctum AutoQC repair system — structured memory schema
-- Source of truth for the repair history. Mirrors the agent JSON contracts:
--   intake-classifier -> issues
--   specialist        -> proposals
--   regression-agent  -> regressions
--   patch-engine      -> patches
--   file map          -> world_files
-- Obsidian vault is the human-readable mirror of these rows.

-- ─────────────────────────────────────────────────────────────────────────────
-- issues: one row per AutoQC finding (from intake-classifier)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.issues (
  id                  uuid primary key default gen_random_uuid(),
  created_at          timestamptz not null default now(),
  run_id              text,                       -- pipeline run id (e.g. prun_...)
  task_id             text,                       -- e.g. T1
  category            text not null,              -- one of the 9 AutoQC categories
  subcriterion        text,
  severity            text,
  flagged_path        text,
  folder_scope        text check (folder_scope in ('filesystem','tasks','meta','unknown')),
  offending_text      text,
  issue_summary       text,
  writer_fixable      boolean,
  recommended_action  text,                       -- fix|override|escalate|human_review|needs_files
  specialist_agent    text,                       -- specialist that owns the category
  status              text not null default 'open' -- open|resolved|escalated
);

-- ─────────────────────────────────────────────────────────────────────────────
-- proposals: one row per specialist diagnosis/proposal (propose-only)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.proposals (
  id                  uuid primary key default gen_random_uuid(),
  created_at          timestamptz not null default now(),
  issue_id            uuid not null references public.issues(id) on delete cascade,
  specialist_agent    text not null,
  subcriterion        text,
  diagnosis           text,
  root_cause          text,
  proposed_change     text,
  change_target       text,                       -- world_file|task_config|metadata|none|generation
  writer_fixable      boolean,
  proposed_action     text,                       -- fix|override|escalate|human_review|needs_files|pass|neutral
  regression_concerns jsonb default '[]'::jsonb,
  do_not_touch        jsonb default '[]'::jsonb,
  confidence          text                        -- high|medium|low
);

-- ─────────────────────────────────────────────────────────────────────────────
-- regressions: one row per regression-agent verdict (the gate)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.regressions (
  id                            uuid primary key default gen_random_uuid(),
  created_at                    timestamptz not null default now(),
  proposal_id                   uuid references public.proposals(id) on delete cascade,
  issue_id                      uuid not null references public.issues(id) on delete cascade,
  regression_status             text not null check (regression_status in ('PASS','FAIL','HUMAN_REVIEW','PASS_NO_EDIT')),
  safe_to_apply                 boolean not null default false,
  safe_to_proceed_without_patch boolean not null default false,
  criteria_impact               jsonb default '{}'::jsonb,   -- per-category improved|unchanged|risk|broken|unknown
  blocking_reasons              jsonb default '[]'::jsonb,
  return_to_agent               text,
  requires_human_review         boolean default false,
  requires_pod_lead_review      boolean default false,
  requires_engineering_escalation boolean default false,
  approved_patch_summary        text,
  do_not_touch                  jsonb default '[]'::jsonb,
  final_recommendation          text,
  epm_note                      text
);

-- ─────────────────────────────────────────────────────────────────────────────
-- patches: one row per patch-engine action (apply or refusal)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.patches (
  id                     uuid primary key default gen_random_uuid(),
  created_at             timestamptz not null default now(),
  regression_id          uuid references public.regressions(id) on delete cascade,
  issue_id               uuid not null references public.issues(id) on delete cascade,
  applied                boolean not null default false,
  target_file            text,                    -- e.g. _repaired/filesystem/<file>
  original_file          text,
  approved_patch_summary text,
  diff_summary           text,
  original_hash_before   text,
  original_hash_after    text,
  originals_untouched    boolean,
  in_scope_only          boolean,
  patch_log_entry        text,
  refusal_reason         text
);

-- ─────────────────────────────────────────────────────────────────────────────
-- world_files: the file map / world state (one row per tracked file per run)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.world_files (
  id            uuid primary key default gen_random_uuid(),
  run_id        text,
  path          text not null,
  folder_scope  text check (folder_scope in ('filesystem','tasks','meta','unknown')),
  doc_type      text,
  patient_id    text,
  file_date     date,
  shared_fields jsonb default '[]'::jsonb,
  related_paths jsonb default '[]'::jsonb,
  traps         jsonb default '[]'::jsonb,
  hash          text,
  last_seen     timestamptz not null default now(),
  unique (run_id, path)
);

-- Indexes for the common lookups
create index if not exists idx_issues_run          on public.issues (run_id);
create index if not exists idx_issues_category     on public.issues (category);
create index if not exists idx_issues_status       on public.issues (status);
create index if not exists idx_proposals_issue     on public.proposals (issue_id);
create index if not exists idx_regressions_issue   on public.regressions (issue_id);
create index if not exists idx_regressions_status  on public.regressions (regression_status);
create index if not exists idx_patches_issue       on public.patches (issue_id);
create index if not exists idx_world_files_run     on public.world_files (run_id);

-- Convenience view: latest verdict per issue, with the patch outcome
create or replace view public.issue_timeline as
select
  i.id            as issue_id,
  i.run_id,
  i.task_id,
  i.category,
  i.subcriterion,
  i.folder_scope,
  i.flagged_path,
  i.status,
  r.regression_status,
  r.final_recommendation,
  p.applied       as patch_applied,
  p.target_file,
  i.created_at
from public.issues i
left join public.regressions r on r.issue_id = i.id
left join public.patches     p on p.issue_id = i.id
order by i.created_at desc;
