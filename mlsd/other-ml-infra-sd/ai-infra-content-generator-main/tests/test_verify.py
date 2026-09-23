from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from conftest import make_security_workspace, write_file

from aicg.cli import main as cli_main
from aicg.source_registry import SourceRegistry
from aicg.verify import VerifyError, verify_repo


SOLUTION_TEMPLATE = textwrap.dedent(
    """\
    # Threat model exercise solution

    ## Overview

    Short walkthrough.

    ## Implementation

    Steps to build the model.

    ## Validation

    Run `pytest`.

    ## Rubric

    Graded on completeness.

    ## Common mistakes

    Forgetting threats.

    ## References

    - https://www.nist.gov/itl/ai-risk-management-framework
    """
)


def _plan_with_one_action(solutions: Path) -> dict:
    return {
        "schema_version": 2,
        "repo": {"name": "ai-infra-security-solutions", "path": str(solutions)},
        "work_items": [
            {
                "id": "fill-mod-001-ml-security-foundations-solutions",
                "type": "module_solution_gap",
                "repo": "ai-infra-security-solutions",
                "module": "mod-001-ml-security-foundations",
                "status": "generated",
                "source_policy": {"required_default_sources": ["nist-ai-rmf"]},
                "exercises": [],
                "actions": [
                    {
                        "type": "write_solution",
                        "path": "modules/mod-001-ml-security-foundations/exercise-01-threat-model/SOLUTION.md",
                    }
                ],
            }
        ],
    }


def _write_plan(solutions: Path, plan: dict) -> Path:
    state_dir = solutions / ".aicg"
    state_dir.mkdir(parents=True, exist_ok=True)
    plan_path = state_dir / "work-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan_path


def test_verify_passes_when_artifact_is_complete(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_one_action(solutions))

    report = verify_repo(workspace, "ai-infra-security-solutions")

    assert report["status"] == "verified"
    assert report["work_items"][0]["status"] == "verified"
    assert report["work_items"][0]["actions"][0]["status"] == "ok"


def test_verify_fails_when_file_missing(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    # Plan exists but the agent never wrote the file.
    _write_plan(solutions, _plan_with_one_action(solutions))

    report = verify_repo(workspace, "ai-infra-security-solutions")

    assert report["status"] == "verification_failed"
    actions = report["work_items"][0]["actions"]
    assert any(
        finding["type"] == "file_missing"
        for action in actions
        for finding in action["findings"]
    )


def test_verify_fails_when_required_sections_missing(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        "# Solution\n\nGreat work.\n",
    )
    _write_plan(solutions, _plan_with_one_action(solutions))

    report = verify_repo(workspace, "ai-infra-security-solutions")

    assert report["status"] == "verification_failed"
    findings = report["work_items"][0]["findings"]
    types = {finding["type"] for finding in findings}
    assert "missing_required_sections" in types


def test_verify_flags_needs_research_marker(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    content = SOLUTION_TEMPLATE + "\n<!-- needs-research: verify the citation -->\n"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        content,
    )
    _write_plan(solutions, _plan_with_one_action(solutions))

    report = verify_repo(workspace, "ai-infra-security-solutions")

    types = {
        finding["type"]
        for action in report["work_items"][0]["actions"]
        for finding in action["findings"]
    }
    assert "needs_research_marker" in types
    assert report["status"] == "verification_failed"


def test_verify_raises_when_plan_missing(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    with pytest.raises(VerifyError):
        verify_repo(workspace, "ai-infra-security-solutions")


def test_verify_updates_plan_status(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_one_action(solutions))

    verify_repo(workspace, "ai-infra-security-solutions")

    plan = json.loads((solutions / ".aicg" / "work-plan.json").read_text())
    assert plan["work_items"][0]["status"] == "verified"


def test_cli_verify_returns_nonzero_on_failure(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    _write_plan(solutions, _plan_with_one_action(solutions))

    rc = cli_main(
        [
            "verify",
            "--workspace",
            str(workspace),
            "--repo",
            "ai-infra-security-solutions",
        ]
    )

    assert rc == 1
    assert (solutions / ".aicg" / "verify-report.json").exists()


def test_module_rationale_sections_relax_for_rationale_work_item(tmp_path: Path) -> None:
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    rationale = textwrap.dedent(
        """\
        # SOLUTION — mod-001

        ## What this module is really teaching

        Overview.

        ## Architectural decisions and why

        Reasoning.

        ## Trade-offs we deliberately accepted

        Lists.

        ## Common mistakes graders see

        Listed.

        ## Related curriculum touchpoints

        - foo
        """
    )
    write_file(
        solutions / "modules" / "mod-001-ml-security-foundations" / "SOLUTION.md",
        rationale,
    )
    plan = {
        "schema_version": 2,
        "repo": {"name": "ai-infra-security-solutions", "path": str(solutions)},
        "work_items": [
            {
                "id": "rationale-mod-001-ml-security-foundations",
                "type": "module_rationale_missing",
                "repo": "ai-infra-security-solutions",
                "module": "mod-001-ml-security-foundations",
                "status": "generated",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
                "actions": [
                    {
                        "type": "write_module_rationale",
                        "path": "modules/mod-001-ml-security-foundations/SOLUTION.md",
                    }
                ],
            }
        ],
    }
    _write_plan(solutions, plan)

    report = verify_repo(workspace, "ai-infra-security-solutions")

    assert report["status"] == "verified"
