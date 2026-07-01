#!/usr/bin/env python3
"""Repository consistency checks for the Sanctum AutoQC agent system."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_AGENT_NAMES = {
    "intake-classifier",
    "orchestrator",
    "solution-integrity",
    "clinical-accuracy",
    "medication-reconciliation",
    "cross-document-consistency",
    "temporal-integrity",
    "trap-architecture",
    "completeness",
    "realism-authenticity",
    "documentation-standards",
    "privacy-compliance",
    "regression-agent",
    "patch-engine",
}

EXPECTED_SPECIALISTS = EXPECTED_AGENT_NAMES - {
    "intake-classifier",
    "orchestrator",
    "regression-agent",
    "patch-engine",
}

STALE_PATTERNS = {
    "one of the 9": "There are 10 AutoQC categories and 10 specialist agents.",
    "all 9 categories": "Regression must check all 10 AutoQC categories.",
    "all nine": "Regression must check all 10 AutoQC categories.",
    "one of the nine": "There are 10 AutoQC categories and 10 specialist agents.",
    "Phase 0/1": "The repo now describes Phases 1-6 as built.",
    "Phase 0 / Phase 1": "The repo now describes Phases 1-6 as built.",
    "No automatic patching until the Regression Agent exists": "The Regression Agent exists; patching is gated by PASS.",
    "Supabase and Obsidian are planned memory layers, not implemented yet": "The memory writer is implemented and credential-gated.",
    "No connection to Supabase yet": "The memory writer supports Supabase when configured.",
    "No specialist subagents beyond documentation yet": "Specialist agent files exist.",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def iter_repo_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel == Path("tools/validate_repo.py"):
            continue
        parts = set(rel.parts)
        if parts & {".git", "_repaired", "__pycache__"}:
            continue
        if path.suffix.lower() in {".md", ".py", ".sql", ".json", ".toml", ".example"}:
            yield path


def check_agents(errors: list[str]) -> None:
    agent_files = sorted((ROOT / ".claude" / "agents").glob("*.md"))
    names = set()
    for path in agent_files:
        text = read(path)
        match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
        if not match:
            fail(errors, f"{path.relative_to(ROOT)} is missing frontmatter name")
            continue
        names.add(match.group(1))

        lowered = text.lower()
        if (
            "diagnoses and proposes only" in lowered
            and "never applies patches" not in lowered
            and "never apply patches" not in lowered
        ):
            fail(errors, f"{path.relative_to(ROOT)} proposes only but does not explicitly forbid applying patches")

    missing = EXPECTED_AGENT_NAMES - names
    extra = names - EXPECTED_AGENT_NAMES
    if missing:
        fail(errors, f"Missing agent definitions: {', '.join(sorted(missing))}")
    if extra:
        fail(errors, f"Unexpected agent definitions: {', '.join(sorted(extra))}")
    if len(agent_files) != len(EXPECTED_AGENT_NAMES):
        fail(errors, f"Expected {len(EXPECTED_AGENT_NAMES)} agent files, found {len(agent_files)}")

    specialist_missing = []
    for specialist in EXPECTED_SPECIALISTS:
        if not (ROOT / ".claude" / "agents" / f"{specialist}.md").exists():
            specialist_missing.append(specialist)
    if specialist_missing:
        fail(errors, f"Missing specialist files: {', '.join(sorted(specialist_missing))}")


def check_stale_text(errors: list[str]) -> None:
    for path in iter_repo_text_files():
        text = read(path)
        for needle, reason in STALE_PATTERNS.items():
            if needle in text:
                fail(errors, f"{path.relative_to(ROOT)} contains stale phrase {needle!r}: {reason}")


def check_core_contracts(errors: list[str]) -> None:
    autoqc = read(ROOT / ".claude" / "commands" / "autoqc-repair.md")
    if "all 10 categories" not in autoqc:
        fail(errors, ".claude/commands/autoqc-repair.md must require all 10 categories in regression")
    if "PASS_NO_EDIT" not in autoqc:
        fail(errors, ".claude/commands/autoqc-repair.md must handle PASS_NO_EDIT")

    regression = read(ROOT / ".claude" / "agents" / "regression-agent.md")
    for status in ("PASS", "FAIL", "HUMAN_REVIEW", "PASS_NO_EDIT"):
        if status not in regression:
            fail(errors, f"regression-agent.md is missing status {status}")
    for category_key in (
        "solution_integrity",
        "clinical_accuracy",
        "medication_reconciliation",
        "cross_document_consistency",
        "temporal_integrity",
        "trap_architecture",
        "completeness",
        "realism_authenticity",
        "documentation_standards",
        "privacy_compliance",
    ):
        if category_key not in regression:
            fail(errors, f"regression-agent.md JSON schema missing {category_key}")

    patch = read(ROOT / ".claude" / "agents" / "patch-engine.md")
    required_patch_guards = [
        'regression_status: "PASS"',
        "safe_to_apply: true",
        "Originals are **never** modified",
        "_repaired/",
        "PASS_NO_EDIT",
    ]
    for guard in required_patch_guards:
        if guard not in patch:
            fail(errors, f"patch-engine.md missing guard: {guard}")


def main() -> int:
    errors: list[str] = []
    check_agents(errors)
    check_stale_text(errors)
    check_core_contracts(errors)

    if errors:
        print("Sanctum validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Sanctum validation passed.")
    print(f"- agents: {len(EXPECTED_AGENT_NAMES)} total, {len(EXPECTED_SPECIALISTS)} specialists")
    print("- core contracts: regression gate, PASS_NO_EDIT, copy-on-write patching")
    return 0


if __name__ == "__main__":
    sys.exit(main())
