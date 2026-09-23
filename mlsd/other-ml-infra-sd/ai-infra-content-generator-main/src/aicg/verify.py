"""Post-generation artifact verification.

After ``aicg generate`` invokes the configured content agent, this
module checks that the agent actually wrote the artifacts it was
asked for. Verification is deliberately strict — it converts the
generator step from "trust the agent" to "trust but verify."

For each action in a work item it:

1. Confirms the target file exists.
2. Confirms the file is non-empty and ends with a newline.
3. Confirms the file's heading structure matches the prompt's output
   contract (``Solution overview``, ``Validation steps``, ``Rubric``,
   ``References``, etc. — the exact list is configurable per
   work-item type).
4. Confirms cited URLs are classifiable against the source registry
   when the work item required default sources.
5. Confirms the file is free of unresolved ``needs-research`` and
   ``# manual-review`` markers (which would block auto-merge anyway).

The verification report is written to ``.aicg/verify-report.json``
and the work plan's item status is bumped from ``generated`` to
``verified`` (or ``verification_failed`` with diagnostics).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .source_registry import SourceRegistry, extract_urls
from .state import (
    ensure_state_dir,
    read_state,
    relative_path,
    state_path,
    utc_now,
    write_json,
)

VERIFY_REPORT = "verify-report.json"
WORK_PLAN = "work-plan.json"
RUN_STATE = "run-state.json"

# Headings the standard SOLUTION.md prompt contract asks the agent to
# produce. Lookup is case-insensitive and substring-based so minor
# wording variation (e.g. "Solution Overview" vs "Overview of the
# solution") doesn't cause a false failure.
DEFAULT_REQUIRED_SECTIONS: tuple[str, ...] = (
    "overview",
    "implementation",
    "validation",
    "rubric",
    "common mistakes",
    "references",
)

# Required sections relax slightly for module-level rationale docs,
# which prioritise *why* over *how*.
MODULE_RATIONALE_REQUIRED_SECTIONS: tuple[str, ...] = (
    "what this",  # "What this project/module is really teaching"
    "decision",  # "Architectural decisions and why"
    "trade-off",  # "Trade-offs we deliberately accepted"
    "common mistakes",
    "related",  # "Related curriculum touchpoints"
)


_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
_NEEDS_RESEARCH_PATTERN = re.compile(r"needs-research", re.IGNORECASE)
_MANUAL_REVIEW_PATTERN = re.compile(r"#\s*manual-review|manual-review", re.IGNORECASE)


class VerifyError(RuntimeError):
    """Raised when verification cannot run (missing plan, bad repo)."""


@dataclass(frozen=True)
class ActionVerification:
    action: dict[str, Any]
    status: str  # "ok" | "missing" | "empty" | "incomplete" | "blocked"
    path: str
    findings: list[dict[str, Any]]
    quality: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkItemVerification:
    work_id: str
    status: str  # "verified" | "verification_failed"
    actions: list[ActionVerification]
    findings: list[dict[str, Any]]


def verify_repo(
    workspace: Path,
    repo_name: str,
    work_id: str | None = None,
    write_report: bool = True,
    source_registry: SourceRegistry | None = None,
    judge_config: "JudgeConfig | None" = None,
) -> dict[str, Any]:
    """Verify the artifacts produced for ``work_id`` in ``repo_name``."""
    from .inventory import WorkspaceInventory
    from .judge import JudgeConfig

    inventory = WorkspaceInventory(workspace)
    target = inventory.require(repo_name)
    repo_path = target.path
    try:
        plan = read_state(repo_path, WORK_PLAN)
    except FileNotFoundError as exc:
        raise VerifyError(
            f"No work plan at {state_path(repo_path, WORK_PLAN)}; run `aicg plan` first."
        ) from exc

    registry = source_registry or SourceRegistry.load()

    items: list[WorkItemVerification] = []
    # Union work_items + backlog_items — same shape, both carry actions.
    pools = (plan.get("work_items", []), plan.get("backlog_items", []))
    for pool in pools:
        for work_item in pool:
            if work_id is not None and work_item.get("id") != work_id:
                continue
            items.append(
                verify_work_item(repo_path, work_item, registry, judge_config=judge_config)
            )

    summary_status = "verified"
    if any(item.status == "verification_failed" for item in items):
        summary_status = "verification_failed"
    elif not items:
        summary_status = "no_items"

    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "repo": plan["repo"],
        "status": summary_status,
        "work_item_count": len(items),
        "work_items": [
            {
                "work_id": item.work_id,
                "status": item.status,
                "finding_count": len(item.findings),
                "actions": [
                    {
                        "type": action.action.get("type"),
                        "path": action.path,
                        "status": action.status,
                        "findings": action.findings,
                        "quality": action.quality,
                    }
                    for action in item.actions
                ],
                "findings": item.findings,
            }
            for item in items
        ],
    }

    if write_report:
        ensure_state_dir(repo_path)
        write_json(state_path(repo_path, VERIFY_REPORT), report)
        _update_run_state_status(repo_path, summary_status, work_id)
        _update_plan_statuses(repo_path, plan, items)

    return report


def verify_work_item(
    repo_path: Path,
    work_item: dict[str, Any],
    registry: SourceRegistry,
    judge_config: "JudgeConfig | None" = None,
) -> WorkItemVerification:
    actions: list[ActionVerification] = []
    findings: list[dict[str, Any]] = []
    required_sections = _required_sections_for(work_item)
    required_default_sources = (
        work_item.get("source_policy", {}).get("required_default_sources", [])
    )

    for action in work_item.get("actions", []):
        verification = verify_action(
            repo_path,
            action,
            required_sections=required_sections,
            required_default_sources=required_default_sources,
            registry=registry,
            work_item=work_item,
            judge_config=judge_config,
        )
        actions.append(verification)
        findings.extend(verification.findings)

    is_ok = all(action.status == "ok" for action in actions)
    return WorkItemVerification(
        work_id=work_item["id"],
        status="verified" if is_ok and actions else (
            "verification_failed" if actions else "no_actions"
        ),
        actions=actions,
        findings=findings,
    )


def verify_action(
    repo_path: Path,
    action: dict[str, Any],
    required_sections: tuple[str, ...],
    required_default_sources: list[str],
    registry: SourceRegistry,
    work_item: dict[str, Any] | None = None,
    judge_config: "JudgeConfig | None" = None,
) -> ActionVerification:
    action_type = action.get("type")
    target = action.get("path")

    if action_type == "create_directory":
        return _verify_directory_action(repo_path, action)
    if action_type in {"write_solution", "write_module_rationale"}:
        if not target:
            return ActionVerification(
                action=action,
                status="incomplete",
                path="",
                findings=[
                    _finding(
                        "missing_action_target",
                        "error",
                        "Action is missing a 'path' field.",
                    )
                ],
            )
        return _verify_file_action(
            repo_path=repo_path,
            action=action,
            target=target,
            required_sections=required_sections,
            required_default_sources=required_default_sources,
            registry=registry,
            work_item=work_item or {},
            judge_config=judge_config,
        )
    return ActionVerification(
        action=action,
        status="ok",
        path=str(target or ""),
        findings=[
            _finding(
                "unverified_action_type",
                "warning",
                f"No verifier registered for action type {action_type!r}.",
            )
        ],
    )


def _verify_directory_action(
    repo_path: Path, action: dict[str, Any]
) -> ActionVerification:
    target = action.get("path", "")
    full = repo_path / target if target else repo_path
    findings: list[dict[str, Any]] = []
    status = "ok"
    if not full.exists():
        status = "missing"
        findings.append(
            _finding(
                "directory_missing",
                "error",
                f"Expected directory was not created: {target}",
            )
        )
    elif not full.is_dir():
        status = "incomplete"
        findings.append(
            _finding(
                "directory_not_a_directory",
                "error",
                f"Expected a directory at {target}; found a file.",
            )
        )
    return ActionVerification(action=action, status=status, path=target, findings=findings)


def _verify_file_action(
    repo_path: Path,
    action: dict[str, Any],
    target: str,
    required_sections: tuple[str, ...],
    required_default_sources: list[str],
    registry: SourceRegistry,
    work_item: dict[str, Any] | None = None,
    judge_config: "JudgeConfig | None" = None,
) -> ActionVerification:
    full = repo_path / target
    findings: list[dict[str, Any]] = []
    if not full.exists():
        findings.append(
            _finding(
                "file_missing",
                "error",
                f"Expected artifact was not written: {target}",
            )
        )
        return ActionVerification(action=action, status="missing", path=target, findings=findings)

    try:
        content = full.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        findings.append(
            _finding(
                "file_unreadable",
                "error",
                f"Could not read {target}: {exc}",
            )
        )
        return ActionVerification(action=action, status="incomplete", path=target, findings=findings)

    if not content.strip():
        findings.append(
            _finding(
                "file_empty",
                "error",
                f"Artifact is empty: {target}",
            )
        )
        return ActionVerification(action=action, status="empty", path=target, findings=findings)

    if not content.endswith("\n"):
        findings.append(
            _finding(
                "file_missing_trailing_newline",
                "warning",
                f"{target} should end with a trailing newline.",
            )
        )

    headings = _collect_headings(content)
    missing_sections = _missing_sections(headings, required_sections)
    if missing_sections:
        findings.append(
            _finding(
                "missing_required_sections",
                "error",
                f"{target} is missing required heading(s): {', '.join(sorted(missing_sections))}.",
                missing=sorted(missing_sections),
                seen=sorted({heading.lower() for heading in headings}),
            )
        )

    source_findings = _verify_source_policy(
        content, target, required_default_sources, registry
    )
    findings.extend(source_findings)

    marker_findings = _verify_marker_freedom(content, target)
    findings.extend(marker_findings)

    quality_payload: dict[str, Any] | None = None
    if judge_config is not None and judge_config.enabled and work_item is not None:
        try:
            from .judge import judge_action

            verdict = judge_action(
                repo_path=repo_path,
                work_item=work_item,
                action=action,
                artifact_path=full,
                config=judge_config,
            )
        except Exception as exc:  # pragma: no cover - defensive
            verdict = None
            findings.append(
                _finding(
                    "judge_invocation_failed",
                    "warning",
                    f"Quality judge raised {exc.__class__.__name__}: {exc}",
                )
            )
        if verdict is not None:
            quality_payload = verdict.as_dict()
            if not verdict.passed:
                findings.append(
                    _finding(
                        "quality_below_threshold",
                        "error",
                        f"Quality judge: {verdict.score}/100 (threshold "
                        f"{verdict.threshold}); blockers="
                        f"{verdict.blockers or '[]'}.",
                        score=verdict.score,
                        threshold=verdict.threshold,
                        blockers=verdict.blockers,
                        summary=verdict.summary,
                    )
                )

    has_error = any(item["severity"] == "error" for item in findings)
    status = "incomplete" if has_error else "ok"
    return ActionVerification(
        action=action,
        status=status,
        path=target,
        findings=findings,
        quality=quality_payload,
    )


def _required_sections_for(work_item: dict[str, Any]) -> tuple[str, ...]:
    work_type = work_item.get("type", "")
    if work_type == "module_rationale_missing":
        return MODULE_RATIONALE_REQUIRED_SECTIONS
    return DEFAULT_REQUIRED_SECTIONS


def _collect_headings(content: str) -> list[str]:
    headings: list[str] = []
    in_code = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        match = _HEADING_PATTERN.match(line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def _missing_sections(headings: Iterable[str], required: tuple[str, ...]) -> set[str]:
    haystack = " | ".join(heading.lower() for heading in headings)
    return {needle for needle in required if needle.lower() not in haystack}


def _verify_source_policy(
    content: str,
    target: str,
    required_default_sources: list[str],
    registry: SourceRegistry,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    urls = extract_urls(content)
    if not urls and len(content.split()) >= 250:
        findings.append(
            _finding(
                "missing_source_references",
                "warning",
                f"{target} has substantial content but cites no URLs.",
            )
        )
        return findings
    if not urls:
        return findings

    classified = [registry.classify_url(url) for url in urls]
    has_official = any(source and source.is_official for source in classified)
    has_practitioner = any(source and source.is_practitioner_reference for source in classified)
    if has_practitioner and not has_official:
        findings.append(
            _finding(
                "practitioner_reference_without_official_source",
                "warning",
                f"{target} cites practitioner sources without an official one.",
            )
        )
    return findings


def _verify_marker_freedom(content: str, target: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if _NEEDS_RESEARCH_PATTERN.search(content):
        findings.append(
            _finding(
                "needs_research_marker",
                "error",
                f"{target} still contains a `needs-research` marker.",
            )
        )
    if _MANUAL_REVIEW_PATTERN.search(content):
        findings.append(
            _finding(
                "manual_review_marker",
                "error",
                f"{target} still contains a `manual-review` marker.",
            )
        )
    return findings


def _update_run_state_status(
    repo_path: Path, summary_status: str, work_id: str | None
) -> None:
    try:
        run_state = read_state(repo_path, RUN_STATE)
    except FileNotFoundError:
        return
    if work_id and run_state.get("work_id") != work_id:
        return
    new_status = "verified" if summary_status == "verified" else "verification_failed"
    run_state["status"] = new_status
    run_state["verified_at"] = utc_now()
    write_json(state_path(repo_path, RUN_STATE), run_state)


def _update_plan_statuses(
    repo_path: Path,
    plan: dict[str, Any],
    items: list[WorkItemVerification],
) -> None:
    by_id = {item.work_id: item for item in items}
    changed = False
    for pool in (plan.get("work_items", []), plan.get("backlog_items", [])):
        for work_item in pool:
            result = by_id.get(work_item.get("id"))
            if result is None:
                continue
            new_status = (
                "verified" if result.status == "verified" else "verification_failed"
            )
            if work_item.get("status") != new_status:
                work_item["status"] = new_status
                work_item["verified_at"] = utc_now()
                changed = True
    if changed:
        write_json(state_path(repo_path, WORK_PLAN), plan)


def _finding(kind: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    data = {"type": kind, "severity": severity, "message": message}
    data.update({k: v for k, v in extra.items() if v is not None})
    return data
