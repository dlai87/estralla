"""``aicg diff`` — surface what the agent changed since the work plan ran.

The diff inspector reads ``.aicg/work-plan.json`` and ``.aicg/run-state.json``,
combines them with ``git status``/``git diff`` output, and prints a focused
view of:

- Files the plan asked the agent to create or modify.
- Files the agent touched outside the plan ("unexpected" changes).
- Line counts for each new file plus the first / last few lines.
- The full unified diff when ``--full`` is passed.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .state import read_state, relative_path


@dataclass(frozen=True)
class DiffEntry:
    status: str  # "added" | "modified" | "deleted" | "renamed" | "untracked"
    path: str
    line_count: int
    expected: bool
    preview_head: list[str]
    preview_tail: list[str]


def diff_repo(
    repo_path: Path,
    work_id: str | None = None,
    head_lines: int = 12,
    tail_lines: int = 6,
    show_full: bool = False,
) -> dict[str, Any]:
    """Inspect the agent's changes for the most-recent (or specified) work item."""
    try:
        plan = read_state(repo_path, "work-plan.json")
    except FileNotFoundError:
        plan = {"work_items": []}

    expected_paths = _expected_paths_for(plan, work_id)
    porcelain = _git_status_porcelain(repo_path)
    entries = _build_entries(
        repo_path,
        porcelain,
        expected_paths,
        head_lines=head_lines,
        tail_lines=tail_lines,
    )

    summary = {
        "added": sum(1 for e in entries if e.status == "added"),
        "modified": sum(1 for e in entries if e.status == "modified"),
        "deleted": sum(1 for e in entries if e.status == "deleted"),
        "renamed": sum(1 for e in entries if e.status == "renamed"),
        "untracked": sum(1 for e in entries if e.status == "untracked"),
        "unexpected": sum(1 for e in entries if not e.expected),
    }

    report = {
        "schema_version": 1,
        "repo": str(repo_path),
        "work_id": work_id,
        "expected_path_count": len(expected_paths),
        "summary": summary,
        "entries": [
            {
                "status": e.status,
                "path": e.path,
                "line_count": e.line_count,
                "expected": e.expected,
                "preview_head": e.preview_head,
                "preview_tail": e.preview_tail,
            }
            for e in entries
        ],
        "full_diff": _git_diff(repo_path) if show_full else None,
    }
    return report


def _expected_paths_for(
    plan: dict[str, Any], work_id: str | None
) -> set[str]:
    paths: set[str] = set()
    for pool in (plan.get("work_items", []), plan.get("backlog_items", [])):
        for item in pool:
            if work_id and item.get("id") != work_id:
                continue
            for action in item.get("actions", []):
                target = action.get("path")
                if not target:
                    continue
                # ``create_directory`` actions list the dir; include that
                # plus its contents as expected.
                paths.add(target.rstrip("/"))
    return paths


def _git_status_porcelain(repo_path: Path) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    rows: list[tuple[str, str]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        rows.append((status, path))
    return rows


def _git_diff(repo_path: Path) -> str:
    completed = subprocess.run(
        ["git", "diff", "--no-color"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def _build_entries(
    repo_path: Path,
    porcelain: list[tuple[str, str]],
    expected_paths: set[str],
    head_lines: int,
    tail_lines: int,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    for status_code, path in porcelain:
        # Ignore runner state files; they are tracked in .gitignore in
        # any well-configured repo but defensive double-skip helps.
        if path.startswith(".aicg/") or path == ".aicg":
            continue
        status = _classify_status(status_code)
        full = repo_path / path
        line_count = 0
        preview_head: list[str] = []
        preview_tail: list[str] = []
        if status != "deleted" and full.is_file():
            try:
                lines = full.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                lines = []
            line_count = len(lines)
            preview_head = lines[:head_lines]
            preview_tail = lines[-tail_lines:] if line_count > head_lines + tail_lines else []
        is_expected = _matches_expected(path, expected_paths)
        entries.append(
            DiffEntry(
                status=status,
                path=relative_path(full, repo_path),
                line_count=line_count,
                expected=is_expected,
                preview_head=preview_head,
                preview_tail=preview_tail,
            )
        )
    return entries


def _matches_expected(path: str, expected: set[str]) -> bool:
    if path in expected:
        return True
    # Allow create_directory targets to match nested files inside them.
    for candidate in expected:
        if not candidate:
            continue
        if path.startswith(candidate + "/"):
            return True
    return False


def _classify_status(code: str) -> str:
    if code.startswith("??"):
        return "untracked"
    primary = code[0] if code[0] != " " else code[1]
    return {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "U": "modified",
        "T": "modified",
    }.get(primary, "modified")
