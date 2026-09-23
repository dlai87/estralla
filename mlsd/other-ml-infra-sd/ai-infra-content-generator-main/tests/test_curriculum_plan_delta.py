"""Tests for the curriculum-plan delta schema, validator, and apply logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aicg.curriculum_plan import (
    CurriculumPlan,
    Evidence,
    Requirement,
    ResearchWindow,
)
from aicg.curriculum_plan_delta import (
    ADDITION_FLAG_THRESHOLD,
    DELTA_SCHEMA_VERSION,
    HIGH_FREQUENCY_REMOVAL_THRESHOLD,
    MIN_EVIDENCE_PER_ADDITION,
    MIN_FREQUENCY_PER_ADDITION,
    CurriculumPlanDelta,
    CurriculumPlanDeltaError,
    RequirementAddition,
    RequirementRemoval,
    RequirementUpdate,
    apply_delta,
    dump_delta,
    load_delta,
    validate_delta,
    write_delta,
)


def _baseline(reqs: list[Requirement] | None = None) -> CurriculumPlan:
    return CurriculumPlan(
        schema_version=1,
        role="junior-engineer",
        role_title="Junior",
        research=ResearchWindow(),
        requirements=tuple(reqs or []),
    )


def _req(id: str, *, frequency: float | None = None, **kw) -> Requirement:
    return Requirement(
        id=id,
        label=kw.pop("label", id),
        frequency=frequency,
        provenance=kw.pop("provenance", "backfilled"),
        requires_confirmation=kw.pop("requires_confirmation", True),
        coverage_status=kw.pop("coverage_status", "partial"),
        **kw,
    )


def _evidence(n: int) -> tuple[Evidence, ...]:
    return tuple(
        Evidence(posting_id=f"p{i}", phrase=f"phrase {i}", url=f"https://x/{i}")
        for i in range(n)
    )


def _addition(
    id: str = "REQ-JR-NEW", frequency: float = 0.40, evidence_count: int = 3
) -> RequirementAddition:
    req = Requirement(
        id=id,
        label=f"new {id}",
        frequency=frequency,
        provenance="research",
        requires_confirmation=False,
        evidence=_evidence(evidence_count),
        coverage_status="missing",
    )
    return RequirementAddition(requirement=req, rationale="X is now cited in 35% of postings")


# ---------- schema ----------


def test_load_rejects_wrong_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "d.json"
    path.write_text(
        json.dumps({"schema_version": 999, "role": "x", "month": "2026-06"}),
        encoding="utf-8",
    )
    with pytest.raises(CurriculumPlanDeltaError):
        load_delta(path)


def test_round_trip(tmp_path: Path) -> None:
    delta = CurriculumPlanDelta(
        schema_version=DELTA_SCHEMA_VERSION,
        role="junior-engineer",
        month="2026-06",
        rationale="cycle 1",
        additions=(_addition(),),
        updates=(RequirementUpdate(id="REQ-JR-EXISTING", frequency=0.45),),
        removals=(RequirementRemoval(id="REQ-JR-OLD"),),
    )
    path = tmp_path / "d.json"
    write_delta(delta, path)
    loaded = load_delta(path)
    assert loaded == delta


# ---------- validation: continuity policy ----------


def test_addition_with_insufficient_evidence_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(_addition(evidence_count=MIN_EVIDENCE_PER_ADDITION - 1),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="evidence"):
        validate_delta(delta, baseline)


def test_addition_with_low_frequency_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(_addition(frequency=MIN_FREQUENCY_PER_ADDITION - 0.01),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="frequency"):
        validate_delta(delta, baseline)


def test_addition_colliding_with_existing_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(_addition(id="REQ-JR-EXISTING-1"),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="collides"):
        validate_delta(delta, baseline)


def test_addition_with_wrong_provenance_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    bad_req = Requirement(
        id="REQ-JR-NEW",
        label="x",
        frequency=0.4,
        provenance="manual",  # must be "research"
        evidence=_evidence(3),
        coverage_status="missing",
    )
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(RequirementAddition(requirement=bad_req),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="provenance"):
        validate_delta(delta, baseline)


def test_update_to_unknown_requirement_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        updates=(RequirementUpdate(id="REQ-JR-NONEXISTENT", frequency=0.5),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="unknown"):
        validate_delta(delta, baseline)


def test_removal_of_unknown_requirement_rejected() -> None:
    baseline = _baseline([_req("REQ-JR-EXISTING-1")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        removals=(RequirementRemoval(id="REQ-JR-NONEXISTENT"),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="unknown"):
        validate_delta(delta, baseline)


def test_high_frequency_removal_without_migration_note_rejected() -> None:
    high_freq = HIGH_FREQUENCY_REMOVAL_THRESHOLD + 0.05
    baseline = _baseline([_req("REQ-JR-CRITICAL", frequency=high_freq)])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        removals=(RequirementRemoval(id="REQ-JR-CRITICAL"),),
    )
    with pytest.raises(CurriculumPlanDeltaError, match="migration_note"):
        validate_delta(delta, baseline)


def test_high_frequency_removal_with_migration_note_allowed() -> None:
    high_freq = HIGH_FREQUENCY_REMOVAL_THRESHOLD + 0.05
    baseline = _baseline(
        [_req(f"REQ-JR-OTHER-{i}") for i in range(20)]
        + [_req("REQ-JR-CRITICAL", frequency=high_freq)]
    )
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        removals=(
            RequirementRemoval(
                id="REQ-JR-CRITICAL",
                migration_note="Merged into REQ-JR-EXISTING-2 with broader scope.",
            ),
        ),
    )
    validated = validate_delta(delta, baseline)
    # Only 1 removal of 21 baseline = 4.8% < 10% threshold; should NOT flag.
    assert validated.requires_explicit_approval is False


# ---------- validation: flag thresholds ----------


def test_additions_over_threshold_flag_for_approval() -> None:
    # 10 existing -> ADDITION_FLAG_THRESHOLD=0.20 -> >2 additions flags.
    baseline = _baseline([_req(f"REQ-JR-X-{i}") for i in range(10)])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="huge cycle",
        additions=tuple(
            _addition(id=f"REQ-JR-NEW-{i}") for i in range(3)  # 30%
        ),
    )
    validated = validate_delta(delta, baseline)
    assert validated.requires_explicit_approval is True
    assert any("additions" in note for note in validated.validation_notes)


def test_additions_under_threshold_do_not_flag() -> None:
    baseline = _baseline([_req(f"REQ-JR-X-{i}") for i in range(20)])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(_addition(id="REQ-JR-NEW-1"),),  # 1 of 20 = 5%
    )
    validated = validate_delta(delta, baseline)
    assert validated.requires_explicit_approval is False


def test_removals_over_threshold_flag_for_approval() -> None:
    # 20 existing -> REMOVAL_FLAG_THRESHOLD=0.10 -> >2 removals flags.
    baseline = _baseline(
        [_req(f"REQ-JR-X-{i}", frequency=0.10) for i in range(20)]
    )
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="huge cleanup",
        removals=tuple(
            RequirementRemoval(id=f"REQ-JR-X-{i}", migration_note="archived")
            for i in range(3)
        ),
    )
    validated = validate_delta(delta, baseline)
    assert validated.requires_explicit_approval is True
    assert any("removals" in note for note in validated.validation_notes)


def test_empty_delta_passes_clean() -> None:
    """No additions, no updates, no removals — the expected steady-state output."""
    baseline = _baseline([_req(f"REQ-JR-X-{i}") for i in range(15)])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="market unchanged this cycle",
    )
    validated = validate_delta(delta, baseline)
    assert validated.requires_explicit_approval is False
    assert validated.additions == ()
    assert validated.updates == ()


# ---------- apply ----------


def test_apply_addition() -> None:
    baseline = _baseline([_req("REQ-JR-X")])
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        additions=(_addition(id="REQ-JR-NEW"),),
    )
    validated = validate_delta(delta, baseline)
    new = apply_delta(validated, baseline)
    assert new.requirement_count == 2
    assert new.requirement_by_id("REQ-JR-NEW") is not None


def test_apply_update_merges_evidence_and_lists() -> None:
    baseline = _baseline(
        [
            _req(
                "REQ-JR-K8S",
                frequency=0.4,
                evidence=_evidence(2),
                exercises=("mod-006/exercise-01",),
            )
        ]
    )
    new_evidence = (Evidence(posting_id="p_new", phrase="latest"),)
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="refine k8s",
        updates=(
            RequirementUpdate(
                id="REQ-JR-K8S",
                frequency=0.55,
                evidence_add=new_evidence,
                exercises_add=("mod-006/exercise-02",),
            ),
        ),
    )
    validated = validate_delta(delta, baseline)
    new = apply_delta(validated, baseline)
    k8s = new.requirement_by_id("REQ-JR-K8S")
    assert k8s is not None
    assert k8s.frequency == 0.55
    assert len(k8s.evidence) == 3
    assert "mod-006/exercise-01" in k8s.exercises
    assert "mod-006/exercise-02" in k8s.exercises
    # Idempotent: existing exercise not duplicated.
    assert k8s.exercises.count("mod-006/exercise-01") == 1


def test_apply_removal() -> None:
    baseline = _baseline(
        [_req("REQ-JR-X", frequency=0.30), _req("REQ-JR-OLD", frequency=0.10)]
    )
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="x",
        removals=(RequirementRemoval(id="REQ-JR-OLD", migration_note="archived"),),
    )
    validated = validate_delta(delta, baseline)
    new = apply_delta(validated, baseline)
    assert new.requirement_count == 1
    assert new.requirement_by_id("REQ-JR-OLD") is None


def test_role_mismatch_rejected() -> None:
    baseline = _baseline()
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="engineer",  # mismatch
        month="2026-06",
        rationale="x",
    )
    with pytest.raises(CurriculumPlanDeltaError, match="role"):
        validate_delta(delta, baseline)


# ---------- end-to-end: real backfilled baseline ----------


def test_end_to_end_against_backfilled_junior_engineer() -> None:
    """An empty delta against the real junior-engineer baseline is a no-op."""
    from aicg.curriculum_plan import load_curriculum_plan

    baseline_path = Path("manifest/curriculum_plan.junior-engineer.manifest.json")
    if not baseline_path.exists():
        pytest.skip("backfilled junior-engineer manifest not present in this checkout")
    baseline = load_curriculum_plan(baseline_path)
    delta = CurriculumPlanDelta(
        schema_version=1,
        role="junior-engineer",
        month="2026-06",
        rationale="market unchanged",
    )
    validated = validate_delta(delta, baseline)
    new = apply_delta(validated, baseline)
    assert new.requirement_count == baseline.requirement_count
    assert validated.requires_explicit_approval is False
