#!/usr/bin/env python3
"""Reverse-engineer per-role curriculum-plan manifests from current content.

Walks the structural curriculum manifest (``manifest/curriculum.manifest.json``)
and produces one ``curriculum_plan.<slug>.manifest.json`` per role plus the
slim ``curriculum_plan.index.json``.

Each existing module becomes one Requirement (e.g.,
``REQ-JR-MOD-006-KUBERNETES-INTRO``) with:

- ``label`` — the module's README title
- ``exercises`` — slugs of all the module's exercises
- ``solutions`` — paths to SOLUTION.md files in the matching solutions repo
- ``tests`` — paths to test files under ``tests/`` inside the solutions repo
- ``coverage_status`` — ``covered`` if at least one exercise has tests,
  ``partial`` if exercises exist but tests don't, ``missing`` otherwise

Each existing project becomes one Requirement (``REQ-JR-PROJ-02-...``)
with the same shape.

Every entry is tagged ``provenance: "backfilled"`` and
``requires_confirmation: true`` so human reviewers can find and validate
them. The first real research cycle compares deltas against THIS baseline,
which is what makes the continuity-over-novelty policy enforceable.

Idempotent — re-running against an unchanged workspace produces the same
output (modulo the ``generated_at`` timestamp on the index).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running directly without setting PYTHONPATH.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from aicg.curriculum_plan import (
    CURRICULUM_PLAN_SCHEMA_VERSION,
    INDEX_SCHEMA_VERSION,
    CurriculumPlan,
    CurriculumPlanIndex,
    CurriculumPlanIndexEntry,
    Requirement,
    ResearchWindow,
    write_curriculum_plan,
    write_curriculum_plan_index,
)
from aicg.manifest import (
    CurriculumManifest,
    Exercise,
    Module,
    Project,
    Track,
    load_curriculum_manifest,
)

LOGGER = logging.getLogger(__name__)

# Per-role short codes used in requirement IDs (REQ-<CODE>-...).
# Stable across regenerations.
_ROLE_CODE = {
    "junior-engineer": "JR",
    "engineer": "ENG",
    "senior-engineer": "SR",
    "principal-engineer": "PE",
    "ml-platform": "MLP",
    "mlops": "MLO",
    "performance": "PERF",
    "security": "SEC",
    "architect": "ARCH",
    "senior-architect": "SARCH",
    "principal-architect": "PARCH",
    "team-lead": "TL",
    "chief-ai-officer": "CAO",
}


def _role_code(slug: str) -> str:
    return _ROLE_CODE.get(slug, slug.upper().replace("-", ""))


def _normalize_slug(slug: str) -> str:
    """Uppercase + dash-joined version of a module/project slug."""
    return re.sub(r"[^A-Z0-9]+", "-", slug.upper()).strip("-")


def _requirement_id_for_module(role_slug: str, module: Module) -> str:
    return f"REQ-{_role_code(role_slug)}-{_normalize_slug(module.slug)}"


def _requirement_id_for_project(role_slug: str, project: Project) -> str:
    return f"REQ-{_role_code(role_slug)}-{_normalize_slug(project.slug)}"


def _discover_tests_for_exercise(
    exercise: Exercise, solutions_repo_path: Path | None
) -> list[str]:
    """Find test files under tests/ inside an exercise's solutions dir."""
    if solutions_repo_path is None or exercise.solutions_path is None:
        return []
    solution_dir = solutions_repo_path / exercise.solutions_path
    if not solution_dir.is_dir():
        return []
    tests_dir = solution_dir / "tests"
    if not tests_dir.is_dir():
        return []
    tests = sorted(
        str((exercise.solutions_path + "/tests/" + p.name))
        for p in tests_dir.iterdir()
        if p.is_file() and p.suffix in (".py", ".sh", ".yaml", ".yml")
    )
    return tests


def _discover_solutions_for_exercise(
    exercise: Exercise, solutions_repo_path: Path | None
) -> list[str]:
    """SOLUTION.md / STEP_BY_STEP.md / similar inside the solution dir."""
    if solutions_repo_path is None or exercise.solutions_path is None:
        return []
    solution_dir = solutions_repo_path / exercise.solutions_path
    if not solution_dir.is_dir():
        return []
    docs: list[str] = []
    for candidate in ("SOLUTION.md", "STEP_BY_STEP.md", "README.md"):
        p = solution_dir / candidate
        if p.is_file():
            docs.append(exercise.solutions_path + "/" + candidate)
    return docs


def _discover_tests_for_project(
    project: Project, solutions_repo_path: Path | None
) -> list[str]:
    if solutions_repo_path is None or project.solutions_path is None:
        return []
    solution_dir = solutions_repo_path / project.solutions_path
    if not solution_dir.is_dir():
        return []
    tests_dir = solution_dir / "tests"
    if not tests_dir.is_dir():
        return []
    return sorted(
        str(project.solutions_path + "/tests/" + p.name)
        for p in tests_dir.iterdir()
        if p.is_file() and p.suffix in (".py", ".sh", ".yaml", ".yml")
    )


def _discover_solutions_for_project(
    project: Project, solutions_repo_path: Path | None
) -> list[str]:
    if solutions_repo_path is None or project.solutions_path is None:
        return []
    solution_dir = solutions_repo_path / project.solutions_path
    if not solution_dir.is_dir():
        return []
    docs: list[str] = []
    for candidate in ("SOLUTION.md", "STEP_BY_STEP.md", "README.md"):
        p = solution_dir / candidate
        if p.is_file():
            docs.append(project.solutions_path + "/" + candidate)
    return docs


def _coverage_for(exercises: list[str], tests: list[str]) -> str:
    if exercises and tests:
        return "covered"
    if exercises:
        return "partial"
    return "missing"


def _module_to_requirement(
    role_slug: str,
    module: Module,
    solutions_repo_path: Path | None,
) -> Requirement:
    exercise_slugs: list[str] = []
    all_tests: list[str] = []
    all_solutions: list[str] = []
    for exercise in module.exercises:
        exercise_ref = f"{module.slug}/{exercise.slug}"
        exercise_slugs.append(exercise_ref)
        all_tests.extend(_discover_tests_for_exercise(exercise, solutions_repo_path))
        all_solutions.extend(_discover_solutions_for_exercise(exercise, solutions_repo_path))

    coverage = _coverage_for(exercise_slugs, all_tests)
    return Requirement(
        id=_requirement_id_for_module(role_slug, module),
        label=module.title,
        provenance="backfilled",
        requires_confirmation=True,
        exercises=tuple(exercise_slugs),
        projects=(),
        solutions=tuple(sorted(set(all_solutions))),
        tests=tuple(sorted(set(all_tests))),
        coverage_status=coverage,
        notes=(
            f"Backfilled from existing module `{module.slug}`. "
            "Replace label + add evidence on next research cycle if confirmed."
        ),
    )


def _project_to_requirement(
    role_slug: str,
    project: Project,
    solutions_repo_path: Path | None,
) -> Requirement:
    tests = _discover_tests_for_project(project, solutions_repo_path)
    solutions = _discover_solutions_for_project(project, solutions_repo_path)
    project_ref = project.slug
    coverage = _coverage_for([project_ref], tests)
    return Requirement(
        id=_requirement_id_for_project(role_slug, project),
        label=project.title,
        provenance="backfilled",
        requires_confirmation=True,
        exercises=(),
        projects=(project_ref,),
        solutions=tuple(sorted(solutions)),
        tests=tuple(sorted(tests)),
        coverage_status=coverage,
        notes=(
            f"Backfilled from existing project `{project.slug}`. "
            "Replace label + add evidence on next research cycle if confirmed."
        ),
    )


def _backfill_track(
    track: Track, workspace: Path
) -> CurriculumPlan:
    solutions_repo_path = (
        workspace / track.solutions_repo if track.solutions_repo else None
    )
    requirements: list[Requirement] = []
    for module in track.modules:
        requirements.append(
            _module_to_requirement(track.slug, module, solutions_repo_path)
        )
    for project in track.projects:
        requirements.append(
            _project_to_requirement(track.slug, project, solutions_repo_path)
        )

    return CurriculumPlan(
        schema_version=CURRICULUM_PLAN_SCHEMA_VERSION,
        role=track.slug,
        role_title=track.display_name,
        research=ResearchWindow(
            window_start=None,
            window_end=None,
            postings_sampled=0,
            last_refreshed=None,
            sources=(),
        ),
        requirements=tuple(requirements),
    )


def _index_for_plans(
    plans: dict[str, CurriculumPlan], file_pattern: str
) -> CurriculumPlanIndex:
    entries: list[CurriculumPlanIndexEntry] = []
    for slug, plan in sorted(plans.items()):
        entries.append(
            CurriculumPlanIndexEntry(
                slug=slug,
                file=file_pattern.format(slug=slug),
                requirement_count=plan.requirement_count,
                coverage=plan.coverage_breakdown(),
                role_title=plan.role_title,
            )
        )
    return CurriculumPlanIndex(
        schema_version=INDEX_SCHEMA_VERSION,
        generated_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        roles=tuple(entries),
    )


def backfill_all(
    workspace: Path,
    structural_manifest_path: Path,
    out_dir: Path,
) -> tuple[dict[str, CurriculumPlan], CurriculumPlanIndex]:
    structural = load_curriculum_manifest(structural_manifest_path)
    plans: dict[str, CurriculumPlan] = {}
    for track in structural.tracks:
        plans[track.slug] = _backfill_track(track, workspace)

    out_dir.mkdir(parents=True, exist_ok=True)
    file_pattern = "curriculum_plan.{slug}.manifest.json"
    for slug, plan in plans.items():
        write_curriculum_plan(plan, out_dir / file_pattern.format(slug=slug))

    index = _index_for_plans(plans, file_pattern)
    write_curriculum_plan_index(index, out_dir / "curriculum_plan.index.json")
    return plans, index


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Parent dir holding the curriculum repos. Default: parent of CWD.",
    )
    parser.add_argument(
        "--structural-manifest",
        type=Path,
        default=None,
        help="Path to curriculum.manifest.json. Default: manifest/curriculum.manifest.json next to this script.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output dir for per-role manifests + index. Default: manifest/ next to this script.",
    )
    args = parser.parse_args(argv)

    workspace = (args.workspace or Path.cwd().parent).expanduser().resolve()
    repo_root = Path(__file__).resolve().parent.parent
    structural = (
        args.structural_manifest or repo_root / "manifest" / "curriculum.manifest.json"
    ).expanduser().resolve()
    out_dir = (args.out or repo_root / "manifest").expanduser().resolve()

    if not workspace.is_dir():
        LOGGER.error("workspace not found: %s", workspace)
        return 2
    if not structural.exists():
        LOGGER.error(
            "structural manifest not found at %s — run "
            "scripts/build-curriculum-manifest.py first",
            structural,
        )
        return 2

    plans, index = backfill_all(workspace, structural, out_dir)
    LOGGER.info(
        "Wrote %d role manifests + index to %s",
        len(plans),
        out_dir,
    )
    for slug, plan in sorted(plans.items()):
        breakdown = plan.coverage_breakdown()
        LOGGER.info(
            "  %-25s requirements=%-3d covered=%-3d partial=%-3d missing=%-3d",
            slug,
            plan.requirement_count,
            breakdown["covered"],
            breakdown["partial"],
            breakdown["missing"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
