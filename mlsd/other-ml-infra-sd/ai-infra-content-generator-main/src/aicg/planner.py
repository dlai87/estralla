"""Deterministic work-plan generation from audit reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .state import utc_now, write_state

WORK_PLAN = "work-plan.json"

# Exercise statuses that translate to an open work item.
ACTIONABLE_EXERCISE_STATUSES = {"missing_solution", "source_gap"}

# Statuses that are not blockers but indicate room to grow. Surfaced as
# deferred backlog rather than ready work.
BACKLOG_EXERCISE_STATUSES = {"module_rationale_only"}


def plan_from_audit(audit_report: dict[str, Any], repo_path: Path | None = None) -> dict[str, Any]:
    work_items: list[dict[str, Any]] = []
    backlog_items: list[dict[str, Any]] = []

    for module in audit_report.get("modules", []):
        module_id = module["module_id"]
        actionable = [
            exercise
            for exercise in module.get("exercises", [])
            if exercise.get("status") in ACTIONABLE_EXERCISE_STATUSES
        ]
        backlog = [
            exercise
            for exercise in module.get("exercises", [])
            if exercise.get("status") in BACKLOG_EXERCISE_STATUSES
        ]
        module_status = module.get("status")
        has_module_rationale = bool(module.get("has_module_rationale"))

        if actionable:
            work_items.append(
                build_work_item(
                    audit_report=audit_report,
                    module=module,
                    exercises=actionable,
                    priority=len(work_items) + 1,
                    work_type="module_solution_gap",
                    title=f"Fill {module_id} module exercise solutions",
                    reason=(
                        "Learning exercises exist in the paired learning repo, but the solutions "
                        "repo is missing module-level reference solutions."
                    ),
                )
            )
        elif (
            module_status == "gap"
            and not has_module_rationale
            and not module.get("exercises")
        ):
            # Module exists but has neither rationale nor exercises captured.
            work_items.append(
                build_module_rationale_work_item(
                    audit_report=audit_report,
                    module=module,
                    priority=len(work_items) + 1,
                )
            )

        if backlog:
            backlog_items.append(
                build_work_item(
                    audit_report=audit_report,
                    module=module,
                    exercises=backlog,
                    priority=1000 + len(backlog_items) + 1,
                    work_type="exercise_depth_followup",
                    title=f"Add exercise-level depth for {module_id}",
                    reason=(
                        "Module-level SOLUTION.md exists; per-exercise artifacts could deepen the "
                        "answer for graders comparing approaches."
                    ),
                    severity="warning",
                )
            )

    for project in audit_report.get("projects", []):
        if project.get("status") == "ok":
            continue
        work_items.append(
            build_project_work_item(
                audit_report=audit_report,
                project=project,
                priority=len(work_items) + 1,
            )
        )

    plan = {
        "schema_version": 2,
        "generated_at": utc_now(),
        "repo": audit_report["repo"],
        "audit_summary": audit_report["summary"],
        "work_item_count": len(work_items),
        "work_items": work_items,
        "backlog_item_count": len(backlog_items),
        "backlog_items": backlog_items,
    }
    if repo_path is not None:
        write_state(repo_path, WORK_PLAN, plan)
    return plan


def build_project_work_item(
    audit_report: dict[str, Any],
    project: dict[str, Any],
    priority: int,
) -> dict[str, Any]:
    project_id = project["project_id"]
    solution_dir = project.get("solution_path") or f"projects/{project_id}"
    return {
        "id": f"fill-{project_id}-solution",
        "type": "project_solution_gap",
        "repo": audit_report["repo"]["name"],
        "project": project_id,
        "title": f"Author solution artifact for {project_id}",
        "severity": "error",
        "priority": priority,
        "status": "planned",
        "why": (
            "Learning repo defines a project capstone but the paired solutions "
            "repo is missing the canonical SOLUTION.md / README.md / STEP_BY_STEP.md."
        ),
        "source_policy": {
            "official_first": True,
            "required_default_sources": [],
            "needs_research_blocks_merge": True,
        },
        "exercises": [],
        "actions": [
            {
                "type": "create_directory",
                "path": solution_dir,
            },
            {
                "type": "write_solution",
                "path": f"{solution_dir.rstrip('/')}/SOLUTION.md",
                "project_id": project_id,
                "source_project": project.get("learning_path"),
            },
        ],
    }


def build_work_item(
    audit_report: dict[str, Any],
    module: dict[str, Any],
    exercises: list[dict[str, Any]],
    priority: int,
    work_type: str,
    title: str,
    reason: str,
    severity: str = "error",
) -> dict[str, Any]:
    module_id = module["module_id"]
    work_id = (
        f"fill-{module_id}-solutions"
        if work_type == "module_solution_gap"
        else f"depth-{module_id}-exercises"
    )

    actions: list[dict[str, Any]] = [
        {
            "type": "create_directory",
            "path": module.get("solution_path") or f"modules/{module_id}",
        }
    ]
    for exercise in exercises:
        exercise_id = exercise["exercise_id"]
        slug = exercise.get("slug")
        target_dir = exercise.get("expected_solution_dir") or (
            f"modules/{module_id}/{exercise_id}-{slug}"
            if slug
            else f"modules/{module_id}/{exercise_id}"
        )
        actions.append(
            {
                "type": "write_solution",
                "exercise_id": exercise_id,
                "source_exercise": exercise["learning_path"],
                "path": f"{target_dir.rstrip('/')}/SOLUTION.md",
            }
        )

    return {
        "id": work_id,
        "type": work_type,
        "repo": audit_report["repo"]["name"],
        "module": module_id,
        "title": title,
        "severity": severity,
        "priority": priority,
        "status": "planned",
        "why": reason,
        "source_policy": {
            "official_first": True,
            "required_default_sources": recommended_source_ids(module_id),
            "needs_research_blocks_merge": True,
        },
        "exercises": [
            {
                "exercise_id": exercise["exercise_id"],
                "title": exercise.get("title", exercise["exercise_id"]),
                "slug": exercise.get("slug"),
                "learning_path": exercise["learning_path"],
                "expected_solution_dir": exercise.get("expected_solution_dir"),
                "required_artifacts": exercise.get("required_artifacts", ["SOLUTION.md"]),
                "status": exercise.get("status"),
            }
            for exercise in exercises
        ],
        "actions": actions,
    }


def build_module_rationale_work_item(
    audit_report: dict[str, Any],
    module: dict[str, Any],
    priority: int,
) -> dict[str, Any]:
    module_id = module["module_id"]
    return {
        "id": f"rationale-{module_id}",
        "type": "module_rationale_missing",
        "repo": audit_report["repo"]["name"],
        "module": module_id,
        "title": f"Add module-level SOLUTION.md for {module_id}",
        "severity": "error",
        "priority": priority,
        "status": "planned",
        "why": (
            "The solutions module directory exists but lacks either per-exercise solutions or a "
            "module-level rationale. Authoring a module-level SOLUTION.md unblocks downstream "
            "audit checks while exercise-level depth is iterated."
        ),
        "source_policy": {
            "official_first": True,
            "required_default_sources": recommended_source_ids(module_id),
            "needs_research_blocks_merge": True,
        },
        "exercises": [],
        "actions": [
            {
                "type": "write_module_rationale",
                "path": f"modules/{module_id}/SOLUTION.md",
            }
        ],
    }


def recommended_source_ids(module_id: str) -> list[str]:
    sources = ["owasp-ml-top-10", "mitre-atlas", "nist-ai-rmf"]
    if "zero-trust" in module_id:
        sources.extend(["nist-sp-800-207", "kubernetes-docs"])
    if "supply-chain" in module_id:
        sources.extend(["slsa", "sigstore-docs", "openssf-scorecard"])
    if "compliance" in module_id or "governance" in module_id:
        sources.extend(["nist-ai-600-1", "veriswarm-trust-center"])
    return sources
