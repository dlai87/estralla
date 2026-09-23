"""Tests for the curriculum-plan schema + loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aicg.curriculum_plan import (
    CURRICULUM_PLAN_SCHEMA_VERSION,
    CurriculumPlan,
    CurriculumPlanError,
    CurriculumPlanIndex,
    CurriculumPlanIndexEntry,
    Evidence,
    Requirement,
    ResearchWindow,
    dump_curriculum_plan,
    dump_curriculum_plan_index,
    load_curriculum_plan,
    load_curriculum_plan_index,
    write_curriculum_plan,
    write_curriculum_plan_index,
)


def _minimal_plan(role: str = "junior-engineer") -> CurriculumPlan:
    return CurriculumPlan(
        schema_version=CURRICULUM_PLAN_SCHEMA_VERSION,
        role=role,
        role_title=f"{role} Track",
        research=ResearchWindow(),
        requirements=(),
    )


# ---------- schema ----------


def test_schema_version_mismatch_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 999,
                "role": "junior-engineer",
                "role_title": "junior",
                "research": {},
                "requirements": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CurriculumPlanError):
        load_curriculum_plan(path)


def test_backfilled_requires_confirmation_must_be_true(tmp_path: Path) -> None:
    """Backfilled entries without requires_confirmation:true are rejected."""
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "role": "junior-engineer",
                "role_title": "Junior",
                "research": {},
                "requirements": [
                    {
                        "id": "REQ-JR-X",
                        "label": "X",
                        "provenance": "backfilled",
                        "requires_confirmation": False,
                        "coverage_status": "partial",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CurriculumPlanError):
        load_curriculum_plan(path)


def test_invalid_provenance_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "role": "junior-engineer",
                "role_title": "Junior",
                "research": {},
                "requirements": [
                    {
                        "id": "REQ-JR-X",
                        "label": "X",
                        "provenance": "magic",  # invalid
                        "coverage_status": "covered",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CurriculumPlanError):
        load_curriculum_plan(path)


def test_invalid_coverage_status_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "role": "junior-engineer",
                "role_title": "Junior",
                "research": {},
                "requirements": [
                    {
                        "id": "REQ-JR-X",
                        "label": "X",
                        "provenance": "manual",
                        "coverage_status": "kinda",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CurriculumPlanError):
        load_curriculum_plan(path)


# ---------- round-trip ----------


def test_plan_round_trip(tmp_path: Path) -> None:
    """Write then read produces an equivalent CurriculumPlan."""
    plan = CurriculumPlan(
        schema_version=CURRICULUM_PLAN_SCHEMA_VERSION,
        role="junior-engineer",
        role_title="Junior",
        research=ResearchWindow(
            window_start="2026-04-01",
            window_end="2026-06-30",
            postings_sampled=47,
            last_refreshed="2026-06-04",
            sources=({"name": "linkedin", "count": 22},),
        ),
        requirements=(
            Requirement(
                id="REQ-JR-K8S",
                label="K8s basics",
                frequency=0.72,
                provenance="research",
                evidence=(
                    Evidence(posting_id="p1", phrase="K8s familiarity", url="https://x"),
                ),
                exercises=("mod-006/exercise-01",),
                tests=("modules/mod-006/exercise-01/tests/test_pods.py",),
                coverage_status="covered",
            ),
        ),
    )
    path = tmp_path / "plan.json"
    write_curriculum_plan(plan, path)
    loaded = load_curriculum_plan(path)
    assert loaded == plan


def test_index_round_trip(tmp_path: Path) -> None:
    index = CurriculumPlanIndex(
        schema_version=1,
        generated_at="2026-06-04T00:00:00Z",
        roles=(
            CurriculumPlanIndexEntry(
                slug="junior-engineer",
                file="curriculum_plan.junior-engineer.manifest.json",
                role_title="Junior Engineer",
                requirement_count=15,
                coverage={"covered": 12, "partial": 3, "missing": 0},
            ),
        ),
    )
    path = tmp_path / "index.json"
    write_curriculum_plan_index(index, path)
    loaded = load_curriculum_plan_index(path)
    assert loaded == index
    assert loaded.get("junior-engineer") is not None


# ---------- helpers on Requirement / CurriculumPlan ----------


def test_requirement_has_any_coverage() -> None:
    r = Requirement(id="X", label="x", provenance="manual", exercises=("a",))
    assert r.has_any_coverage() is True
    empty = Requirement(id="X", label="x", provenance="manual")
    assert empty.has_any_coverage() is False


def test_plan_coverage_breakdown() -> None:
    plan = CurriculumPlan(
        schema_version=1,
        role="x",
        role_title="x",
        research=ResearchWindow(),
        requirements=(
            Requirement(id="A", label="A", provenance="manual", coverage_status="covered"),
            Requirement(id="B", label="B", provenance="manual", coverage_status="covered"),
            Requirement(id="C", label="C", provenance="manual", coverage_status="partial"),
            Requirement(id="D", label="D", provenance="manual", coverage_status="missing"),
        ),
    )
    assert plan.coverage_breakdown() == {"covered": 2, "partial": 1, "missing": 1}


# ---------- committed manifest sanity ----------


def test_committed_junior_manifest_loads() -> None:
    """The backfilled junior-engineer manifest loads cleanly."""
    path = Path("manifest/curriculum_plan.junior-engineer.manifest.json")
    if not path.exists():
        pytest.skip("backfilled manifest not present in this checkout")
    plan = load_curriculum_plan(path)
    assert plan.role == "junior-engineer"
    # All backfilled entries must carry requires_confirmation.
    backfilled = [r for r in plan.requirements if r.provenance == "backfilled"]
    assert backfilled
    assert all(r.requires_confirmation for r in backfilled)


def test_committed_index_loads() -> None:
    path = Path("manifest/curriculum_plan.index.json")
    if not path.exists():
        pytest.skip("backfilled index not present in this checkout")
    index = load_curriculum_plan_index(path)
    # The ai-infra org has 11 roles — the IC/architect/lead ladder from
    # junior-engineer to principal-architect. The agentic vertical and the
    # security + chief-ai-officer roles moved to sibling orgs
    # (ai-engineering-curriculum, ai-governance-curriculum) and now live in
    # their own per-domain configs, so they are excluded here. The index
    # stays in sync with the trimmed org config.
    assert len(index.roles) == 11
    # Every slug listed should have a coverage breakdown summing to the count.
    for entry in index.roles:
        assert sum(entry.coverage.values()) == entry.requirement_count
