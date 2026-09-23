"""Tests for the plan-coverage report + text renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from aicg.curriculum_plan import (
    CurriculumPlan,
    Evidence,
    Requirement,
    ResearchWindow,
    load_curriculum_plan,
)
from aicg.plan_coverage import (
    coverage_report,
    render_text,
)


def _r(
    id: str,
    status: str = "missing",
    *,
    frequency: float | None = None,
    exercises: tuple[str, ...] = (),
    projects: tuple[str, ...] = (),
    tests: tuple[str, ...] = (),
    solutions: tuple[str, ...] = (),
    evidence: int = 0,
    discussions: int = 0,
    label: str | None = None,
) -> Requirement:
    return Requirement(
        id=id,
        label=label or id,
        frequency=frequency,
        provenance="manual",
        requires_confirmation=False,
        coverage_status=status,  # type: ignore[arg-type]
        exercises=exercises,
        projects=projects,
        tests=tests,
        solutions=solutions,
        evidence=tuple(
            Evidence(posting_id=f"p{i}", phrase=f"e{i}") for i in range(evidence)
        ),
        discussion_topics=tuple(),  # noqa: shape — count handled in keywords test
    )


def _plan(reqs: list[Requirement]) -> CurriculumPlan:
    return CurriculumPlan(
        schema_version=1,
        role="junior-engineer",
        role_title="Junior",
        research=ResearchWindow(),
        requirements=tuple(reqs),
    )


def test_coverage_groups_by_status() -> None:
    plan = _plan(
        [
            _r("A", "covered", exercises=("x",), tests=("t",)),
            _r("B", "partial", exercises=("x",)),
            _r("C", "missing"),
        ]
    )
    report = coverage_report(plan)
    assert report["summary"] == {"covered": 1, "partial": 1, "missing": 1, "total": 3}
    assert [g["id"] for g in report["groups"]["covered"]] == ["A"]
    assert [g["id"] for g in report["groups"]["partial"]] == ["B"]
    assert [g["id"] for g in report["groups"]["missing"]] == ["C"]


def test_missing_lists_keywords() -> None:
    plan = _plan(
        [_r("REQ-JR-K8S", "missing", label="Kubernetes Intro and Pod Lifecycle")]
    )
    report = coverage_report(plan)
    gap = report["groups"]["missing"][0]
    assert "kubernetes" in gap["keywords"]
    assert "intro" in gap["keywords"]
    assert "pod" in gap["keywords"]
    assert "lifecycle" in gap["keywords"]
    # stopwords filtered
    assert "and" not in gap["keywords"]


def test_partial_lists_what_is_missing() -> None:
    plan = _plan(
        [
            _r("A", "partial", exercises=("ex1",)),  # no tests, no projects, no solutions, no evidence
        ]
    )
    report = coverage_report(plan)
    gap = report["groups"]["partial"][0]
    pieces = gap["missing_pieces"]
    assert "no tests" in pieces
    assert "no project anchor" in pieces
    assert "no solution document" in pieces
    assert "no evidence" in pieces
    # exercise IS present, so it's not listed.
    assert "no exercise anchor" not in pieces


def test_groups_sorted_by_frequency_desc() -> None:
    plan = _plan(
        [
            _r("LOW", "missing", frequency=0.10),
            _r("HIGH", "missing", frequency=0.80),
            _r("MID", "missing", frequency=0.40),
        ]
    )
    report = coverage_report(plan)
    order = [g["id"] for g in report["groups"]["missing"]]
    assert order == ["HIGH", "MID", "LOW"]


def test_render_text_smoke() -> None:
    plan = _plan(
        [
            _r("REQ-1", "missing", label="Kubernetes", frequency=0.6),
            _r("REQ-2", "covered", exercises=("x",), tests=("t",)),
        ]
    )
    report = coverage_report(plan)
    text = render_text(report)
    assert "Coverage" in text
    assert "REQ-1" in text
    assert "Kubernetes" in text
    assert "REQ-2" in text
    assert "MISSING" in text
    assert "COVERED" in text


def test_render_text_omits_empty_groups() -> None:
    plan = _plan([_r("A", "covered", exercises=("x",), tests=("t",))])
    text = render_text(coverage_report(plan))
    # Only the COVERED group should render — no empty PARTIAL/MISSING headings.
    assert "MISSING" not in text
    assert "PARTIAL" not in text


def test_against_committed_junior_manifest() -> None:
    """End-to-end against the backfilled junior baseline."""
    path = Path("manifest/curriculum_plan.junior-engineer.manifest.json")
    if not path.exists():
        pytest.skip("backfilled junior manifest not present in this checkout")
    plan = load_curriculum_plan(path)
    report = coverage_report(plan)
    assert report["summary"]["total"] == plan.requirement_count
    assert (
        report["summary"]["covered"]
        + report["summary"]["partial"]
        + report["summary"]["missing"]
        == plan.requirement_count
    )
    text = render_text(report)
    assert "junior-engineer" in text
