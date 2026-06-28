# Obsidian Vault — AutoQC Repair (human-readable memory layer)

This folder is an Obsidian vault. It's the **readable mirror** of the structured repair history
stored in Supabase. Supabase = source of truth; this vault = for humans (pod leads, writers).

## Open it
In Obsidian: **Open folder as vault** → select this `obsidian-vault/` folder.

## Structure
```
obsidian-vault/
  Dashboards/index.md       ← start here (MOCs + Dataview queries)
  Issues/                   ← one note per AutoQC issue+repair (from the template)
  Templates/issue-template.md
```

## How notes get created
When the repair pipeline finishes an issue, it writes a note into `Issues/` using
`Templates/issue-template.md`, filling the frontmatter from the same record inserted into Supabase.
That keeps the two layers in sync (structured ↔ readable).

## Privacy
Issue notes can reference grader/trap/answer content, so this vault is **gitignored** and must not
be pushed to the public repo.
