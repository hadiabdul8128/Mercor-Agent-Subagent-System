#!/usr/bin/env python3
"""
Sanctum AutoQC — memory writer.

Records the repair pipeline's agent outputs into Supabase (structured source of truth)
and writes a human-readable mirror note into the Obsidian vault.

Stdlib only — no pip installs required. Reads credentials from ../.env:
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Usage (from the pipeline, via Bash):
  python3 memory/sanctum_memory.py issue       --json '<intake-classifier JSON>'
  python3 memory/sanctum_memory.py proposal     --issue-id <uuid> --json '<specialist JSON>'
  python3 memory/sanctum_memory.py regression   --issue-id <uuid> [--proposal-id <uuid>] --json '<regression JSON>'
  python3 memory/sanctum_memory.py patch        --issue-id <uuid> [--regression-id <uuid>] --json '<patch-engine JSON>'
  python3 memory/sanctum_memory.py world_file   --json '<file-map entry JSON>'
  python3 memory/sanctum_memory.py note         --issue-id <uuid>      # (re)write the Obsidian note

Each insert prints the created row's id to stdout so the caller can chain ids.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
VAULT_ISSUES = ROOT / "obsidian-vault" / "Issues"


def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # allow real environment to override
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    if not env.get("SUPABASE_URL") or not env.get("SUPABASE_SERVICE_ROLE_KEY"):
        sys.exit("ERROR: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing from .env")
    return env


def _request(method: str, url: str, key: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "return=representation")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR {e.code} on {method} {url}: {e.read().decode()[:400]}")


def insert(env: dict, table: str, record: dict) -> dict:
    url = f"{env['SUPABASE_URL']}/rest/v1/{table}"
    rows = _request("POST", url, env["SUPABASE_SERVICE_ROLE_KEY"], record)
    return rows[0] if isinstance(rows, list) and rows else (rows or {})


def upsert(env: dict, table: str, record: dict, on_conflict: str) -> dict:
    url = f"{env['SUPABASE_URL']}/rest/v1/{table}?on_conflict={on_conflict}"
    data = json.dumps(record).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("apikey", env["SUPABASE_SERVICE_ROLE_KEY"])
    req.add_header("Authorization", f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "resolution=merge-duplicates,return=representation")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            rows = json.loads(raw) if raw else []
            return rows[0] if rows else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR {e.code} upsert {table}: {e.read().decode()[:400]}")


def fetch(env: dict, table: str, query: str) -> list:
    url = f"{env['SUPABASE_URL']}/rest/v1/{table}?{query}"
    return _request("GET", url, env["SUPABASE_SERVICE_ROLE_KEY"]) or []


# ── column whitelists (keep inserts aligned to the schema) ────────────────────
COLS = {
    "issues": ["run_id", "task_id", "category", "subcriterion", "severity", "flagged_path",
               "folder_scope", "offending_text", "issue_summary", "writer_fixable",
               "recommended_action", "specialist_agent", "status"],
    "proposals": ["issue_id", "specialist_agent", "subcriterion", "diagnosis", "root_cause",
                  "proposed_change", "change_target", "writer_fixable", "proposed_action",
                  "regression_concerns", "do_not_touch", "confidence"],
    "regressions": ["proposal_id", "issue_id", "regression_status", "safe_to_apply",
                    "safe_to_proceed_without_patch", "criteria_impact", "blocking_reasons",
                    "return_to_agent", "requires_human_review", "requires_pod_lead_review",
                    "requires_engineering_escalation", "approved_patch_summary", "do_not_touch",
                    "final_recommendation", "epm_note"],
    "patches": ["regression_id", "issue_id", "applied", "target_file", "original_file",
                "approved_patch_summary", "diff_summary", "original_hash_before",
                "original_hash_after", "originals_untouched", "in_scope_only",
                "patch_log_entry", "refusal_reason"],
    "world_files": ["run_id", "path", "folder_scope", "doc_type", "patient_id", "file_date",
                    "shared_fields", "related_paths", "traps", "hash"],
}


def pick(payload: dict, table: str, **extra) -> dict:
    rec = {k: payload[k] for k in COLS[table] if k in payload}
    rec.update({k: v for k, v in extra.items() if v is not None})
    return rec


# ── Obsidian mirror note ──────────────────────────────────────────────────────
def write_note(env: dict, issue_id: str) -> Path:
    issue = (fetch(env, "issues", f"id=eq.{issue_id}") or [{}])[0]
    prop = (fetch(env, "proposals", f"issue_id=eq.{issue_id}&order=created_at.desc&limit=1") or [{}])[0]
    reg = (fetch(env, "regressions", f"issue_id=eq.{issue_id}&order=created_at.desc&limit=1") or [{}])[0]
    patch = (fetch(env, "patches", f"issue_id=eq.{issue_id}&order=created_at.desc&limit=1") or [{}])[0]

    VAULT_ISSUES.mkdir(parents=True, exist_ok=True)
    cat = issue.get("category", "Uncategorized")
    slug = f"{(issue.get('task_id') or 'T')}-{issue_id[:8]}"
    fm = {
        "issue_id": issue_id, "category": cat, "subcriterion": issue.get("subcriterion", ""),
        "severity": issue.get("severity", ""), "flagged_path": issue.get("flagged_path", ""),
        "folder_scope": issue.get("folder_scope", ""), "writer_fixable": issue.get("writer_fixable"),
        "specialist_agent": issue.get("specialist_agent", ""),
        "regression_status": reg.get("regression_status", "pending"),
        "status": issue.get("status", "open"),
    }
    body = []
    body.append("---")
    for k, v in fm.items():
        body.append(f'{k}: "{v}"' if isinstance(v, str) else f"{k}: {json.dumps(v)}")
    body.append(f'tags: [autoqc, "{reg.get("regression_status","pending")}"]')
    body.append("---\n")
    body.append(f"# {slug} — {cat} / {issue.get('subcriterion','')}\n")
    body.append(f"> Mirror of Supabase row `{issue_id}`. See [[index]].\n")
    body.append("## Finding")
    body.append(f"- **Path:** `{issue.get('flagged_path','')}`  (scope: **{issue.get('folder_scope','')}**)")
    body.append(f"- **Severity:** {issue.get('severity','')}")
    body.append(f"- **Offending text:** {issue.get('offending_text','')}\n")
    body.append("## Classification")
    body.append(f"{issue.get('issue_summary','')}")
    body.append(f"- writer_fixable: **{issue.get('writer_fixable')}** · action: **{issue.get('recommended_action','')}**\n")
    if prop:
        body.append(f"## Diagnosis + proposal ({prop.get('specialist_agent','')})")
        body.append(f"{prop.get('diagnosis','')}\n")
        body.append(f"**Proposed change:** {prop.get('proposed_change','')}")
        body.append(f"**Regression concerns:** {prop.get('regression_concerns','')}\n")
    if reg:
        body.append(f"## Regression verdict — {reg.get('regression_status','')}")
        body.append(f"{reg.get('final_recommendation','')}")
        body.append(f"- do_not_touch: {reg.get('do_not_touch','')}\n")
    if patch:
        body.append("## Patch outcome")
        body.append(f"- applied: **{patch.get('applied')}** → `{patch.get('target_file','')}`")
        if patch.get("refusal_reason"):
            body.append(f"- refusal: {patch.get('refusal_reason')}")
        body.append("")
    if reg.get("epm_note"):
        body.append("## EPM note")
        body.append(reg["epm_note"] + "\n")
    body.append(f"## Links\n- Category MOC: [[{cat}]]")

    path = VAULT_ISSUES / f"{slug}.md"
    path.write_text("\n".join(body))
    return path


def main():
    ap = argparse.ArgumentParser(description="Sanctum AutoQC memory writer")
    ap.add_argument("kind", choices=["issue", "proposal", "regression", "patch", "world_file", "note"])
    ap.add_argument("--json", help="agent output JSON (string)")
    ap.add_argument("--issue-id")
    ap.add_argument("--proposal-id")
    ap.add_argument("--regression-id")
    ap.add_argument("--no-note", action="store_true", help="skip writing the Obsidian note")
    args = ap.parse_args()

    env = load_env()

    if args.kind == "note":
        if not args.issue_id:
            sys.exit("note requires --issue-id")
        print(write_note(env, args.issue_id))
        return

    payload = json.loads(args.json) if args.json else {}

    if args.kind == "issue":
        row = insert(env, "issues", pick(payload, "issues"))
        print(row["id"])
    elif args.kind == "proposal":
        row = insert(env, "proposals", pick(payload, "proposals", issue_id=args.issue_id))
        print(row["id"])
        if not args.no_note and args.issue_id:
            write_note(env, args.issue_id)
    elif args.kind == "regression":
        row = insert(env, "regressions",
                     pick(payload, "regressions", issue_id=args.issue_id, proposal_id=args.proposal_id))
        print(row["id"])
        if not args.no_note and args.issue_id:
            write_note(env, args.issue_id)
    elif args.kind == "patch":
        row = insert(env, "patches",
                     pick(payload, "patches", issue_id=args.issue_id, regression_id=args.regression_id))
        print(row["id"])
        if not args.no_note and args.issue_id:
            write_note(env, args.issue_id)
    elif args.kind == "world_file":
        row = upsert(env, "world_files", pick(payload, "world_files"), on_conflict="run_id,path")
        print(row.get("id", ""))


if __name__ == "__main__":
    main()
