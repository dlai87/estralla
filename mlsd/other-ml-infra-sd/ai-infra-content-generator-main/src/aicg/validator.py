"""Validation runner for curriculum repositories."""

from __future__ import annotations

import py_compile
from pathlib import Path
from typing import Any

from .audit import audit_repo
from .state import relative_path, utc_now, write_state

VALIDATION_REPORT = "validation-report.json"
SKIP_DIRS = {".git", ".aicg", ".venv", "node_modules", "__pycache__"}


def validate_repo(
    workspace: Path,
    repo_name: str,
    module: str | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    audit = audit_repo(workspace, repo_name, module=module, write_report=True)
    repo_path = Path(audit["repo"]["path"])
    checks = [
        check_markdown_basics(repo_path),
        check_curriculum_file_format(repo_path),
        check_python_syntax(repo_path),
        check_ci_contract(repo_path),
        check_audit_blockers(audit),
    ]
    failed = any(check["status"] == "fail" for check in checks)
    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "repo": audit["repo"],
        "status": "failed" if failed else "passed",
        "audit_summary": audit["summary"],
        "checks": checks,
    }
    if write_report:
        write_state(repo_path, VALIDATION_REPORT, report)
    return report


def check_markdown_basics(repo_path: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for path in repo_path.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        content = path.read_text(encoding="utf-8")
        if content and not content.endswith("\n"):
            findings.append(
                {
                    "severity": "warning",
                    "path": relative_path(path, repo_path),
                    "message": "Markdown file does not end with a newline.",
                }
            )
        if "\t" in content:
            findings.append(
                {
                    "severity": "warning",
                    "path": relative_path(path, repo_path),
                    "message": "Markdown file contains tab characters.",
                }
            )
    return {
        "name": "markdown_basics",
        "status": "pass",
        "finding_count": len(findings),
        "findings": findings,
    }


def check_python_syntax(repo_path: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    checked = 0
    for path in repo_path.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_path(path, repo_path),
                    "message": str(exc),
                }
            )
    return {
        "name": "python_syntax",
        "status": "fail" if findings else "pass",
        "checked_count": checked,
        "finding_count": len(findings),
        "findings": findings,
    }


def check_curriculum_file_format(repo_path: Path) -> dict[str, Any]:
    protected = ("CURRICULUM.md", "CURRICULUM_INDEX.md", "README.md", "VERSIONS.md")
    findings: list[dict[str, Any]] = []
    checked = 0
    for filename in protected:
        path = repo_path / filename
        if not path.exists():
            continue
        checked += 1
        findings.extend(validate_markdown_format(path, repo_path))
    errors = [finding for finding in findings if finding["severity"] == "error"]
    return {
        "name": "curriculum_file_format",
        "status": "fail" if errors else "pass",
        "checked_count": checked,
        "finding_count": len(findings),
        "findings": findings,
    }


def validate_markdown_format(path: Path, repo_path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(line.strip() for line in lines):
        return [
            {
                "severity": "error",
                "path": relative_path(path, repo_path),
                "message": "Protected markdown file is empty.",
            }
        ]

    first_content = next((line.strip() for line in lines if line.strip()), "")
    if not first_content.startswith("# "):
        findings.append(
            {
                "severity": "warning",
                "path": relative_path(path, repo_path),
                "message": "Protected markdown file should start with an H1 heading.",
            }
        )

    previous_heading = 0
    in_code = False
    for line_number, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.startswith("#"):
            continue
        level = len(line) - len(line.lstrip("#"))
        if previous_heading and level > previous_heading + 1:
            findings.append(
                {
                    "severity": "warning",
                    "path": relative_path(path, repo_path),
                    "line": line_number,
                    "message": "Heading level skips a parent level.",
                }
            )
        previous_heading = level

    findings.extend(validate_markdown_tables(path, repo_path, lines))
    return findings


def validate_markdown_tables(path: Path, repo_path: Path, lines: list[str]) -> list[dict[str, Any]]:
    """Validate that every GitHub-flavored markdown table is well-formed.

    Rules enforced:

    - The row after a header must be a separator row of the same column
      count (``|---|---|`` or variations with alignment markers).
    - Every body row must have the same number of columns as the header.
    - A bare separator row without a preceding header is flagged.
    """
    findings: list[dict[str, Any]] = []
    table_width: int | None = None
    in_table = False
    separator_seen = False
    in_code_fence = False
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            table_width = None
            in_table = False
            separator_seen = False
            continue
        if in_code_fence:
            continue
        if not _is_table_row(stripped):
            table_width = None
            in_table = False
            separator_seen = False
            continue
        cells = _split_table_row(stripped)
        if not in_table:
            table_width = len(cells)
            in_table = True
            separator_seen = False
            continue
        if not separator_seen:
            separator_seen = True
            if not _is_separator_cells(cells):
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_path(path, repo_path),
                        "line": line_number,
                        "message": "Markdown table is missing the |---|---| separator row after the header.",
                    }
                )
                # Treat this row as if it were a body row for subsequent
                # column-count checks.
                if table_width is not None and len(cells) != table_width:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_path(path, repo_path),
                            "line": line_number,
                            "message": "Markdown table row has a different column count.",
                        }
                    )
            elif table_width is not None and len(cells) != table_width:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_path(path, repo_path),
                        "line": line_number,
                        "message": "Markdown table separator column count does not match the header.",
                    }
                )
            continue
        if table_width is not None and len(cells) != table_width:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_path(path, repo_path),
                    "line": line_number,
                    "message": "Markdown table row has a different column count.",
                }
            )
    return findings


def _is_table_row(stripped: str) -> bool:
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) >= 2


def _split_table_row(stripped: str) -> list[str]:
    return [cell.strip() for cell in stripped.strip("|").split("|")]


_SEPARATOR_CELL_PATTERN = __import__("re").compile(r"^:?-{2,}:?$")


def _is_separator_cells(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL_PATTERN.match(cell) for cell in cells)


def check_ci_contract(repo_path: Path) -> dict[str, Any]:
    workflows = repo_path / ".github" / "workflows"
    findings: list[dict[str, Any]] = []
    if not workflows.exists():
        findings.append(
            {
                "severity": "warning",
                "path": ".github/workflows",
                "message": "No GitHub Actions workflow directory exists.",
            }
        )
    return {
        "name": "ci_contract",
        "status": "pass",
        "finding_count": len(findings),
        "findings": findings,
    }


def check_audit_blockers(audit: dict[str, Any]) -> dict[str, Any]:
    findings = [
        gap
        for gap in audit.get("gaps", [])
        if gap.get("severity") == "error"
        and gap.get("type") in {"missing_solution_module", "missing_exercise_solution", "needs_research"}
    ]
    return {
        "name": "audit_blockers",
        "status": "fail" if findings else "pass",
        "finding_count": len(findings),
        "findings": findings,
    }
