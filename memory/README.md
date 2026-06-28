# Memory Layer

Phase 6 — the persistent history for the AutoQC repair pipeline.

- **Supabase** (Postgres) = structured source of truth. Tables: `issues`, `proposals`,
  `regressions`, `patches`, `world_files`, plus the `issue_timeline` view. Schema lives in
  `../supabase/migrations/`.
- **Obsidian** (`../obsidian-vault/`) = human-readable mirror. One note per issue in `Issues/`.

`sanctum_memory.py` writes to both. Stdlib only — no pip installs. Reads credentials from `../.env`
(`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).

## Setup (already done for this project)
1. `cp ../.env.example ../.env` and fill in values.
2. Schema is applied via `supabase db push` from the repo root.

## Usage (the pipeline calls these; ids chain together)
```bash
# 1. classifier output -> issues  (prints issue_id)
IID=$(python3 memory/sanctum_memory.py issue --json '<intake-classifier JSON>')

# 2. specialist output -> proposals  (prints proposal_id)
PID=$(python3 memory/sanctum_memory.py proposal --issue-id "$IID" --json '<specialist JSON>')

# 3. regression verdict -> regressions
RID=$(python3 memory/sanctum_memory.py regression --issue-id "$IID" --proposal-id "$PID" --json '<regression JSON>')

# 4. patch-engine result -> patches
python3 memory/sanctum_memory.py patch --issue-id "$IID" --regression-id "$RID" --json '<patch JSON>'

# file map row (upsert by run_id+path)
python3 memory/sanctum_memory.py world_file --json '<file-map entry JSON>'

# (re)write just the Obsidian note for an issue
python3 memory/sanctum_memory.py note --issue-id "$IID"
```

Each insert reads only the schema's columns from the JSON (extra fields are ignored), so you can
pass an agent's full output object directly. Inserting a proposal/regression/patch also refreshes
the issue's Obsidian note (`--no-note` to skip).

## Notes
- `issues` rows are keyed by a generated UUID; chain ids between steps as shown.
- `world_files` upserts on `(run_id, path)`.
- The Obsidian `Issues/` folder is gitignored (it can contain grader/trap content).
