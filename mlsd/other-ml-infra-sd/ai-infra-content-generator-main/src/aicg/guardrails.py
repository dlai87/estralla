"""Guardrail decisions for PR creation and auto-merge."""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .audit import PlaceholderCache, scan_placeholders

RESTRICTED_AUTO_MERGE_PATTERNS = (
    ".github/workflows/*",
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "SECURITY.md",
    "pyproject.toml",
    "aicg.yaml",
    "aicg.yml",
)


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def evaluate_guardrails(
    repo_path: Path,
    branch: str | None = None,
    changed_files: list[str] | None = None,
    ci_status: str = "unknown",
    auto_merge: bool = False,
    force_push: bool = False,
) -> GuardrailDecision:
    blockers: list[str] = []
    warnings: list[str] = []
    branch = branch or current_branch(repo_path)
    changed_files = changed_files if changed_files is not None else git_changed_files(repo_path)

    if branch in {"main", "master"}:
        blockers.append("Refusing to create or merge curriculum changes directly on main/master.")
    if force_push:
        blockers.append("Force-push is not allowed by AICG guardrails.")

    cache = PlaceholderCache(repo_path)
    marker_findings = scan_placeholders(repo_path, cache=cache)
    cache.save()
    if any(item["type"] == "manual_review" for item in marker_findings):
        blockers.append("Manual-review markers are present.")
    if any(item["type"] == "needs_research" for item in marker_findings):
        blockers.append("needs-research markers are present.")

    restricted = [
        path for path in changed_files if matches_any(path, RESTRICTED_AUTO_MERGE_PATTERNS)
    ]
    if restricted:
        message = "Restricted files changed: " + ", ".join(sorted(restricted))
        if auto_merge:
            blockers.append(message)
        else:
            warnings.append(message)

    if auto_merge and ci_status != "success":
        blockers.append(f"Auto-merge requires green CI; current status is '{ci_status}'.")

    return GuardrailDecision(
        allowed=not blockers,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def current_branch(repo_path: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def git_changed_files(repo_path: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return parse_status_paths(completed.stdout)


def parse_status_paths(output: str) -> list[str]:
    paths: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths
