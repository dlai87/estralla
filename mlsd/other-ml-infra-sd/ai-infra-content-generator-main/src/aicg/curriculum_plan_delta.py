"""Schema for curriculum-plan deltas (research output) + validators + apply.

A delta describes the proposed changes to a per-role
``curriculum_plan.<slug>.manifest.json`` for a single research cycle. It
is the structured contract between the research agent and the
human-review PR workflow.

Concrete continuity policy (codified here so validators can enforce it
instead of relying on prompt instructions alone):

- Each addition must carry ≥ 3 distinct evidence items
- Each addition must declare a frequency ≥ 0.30
- A delta proposing > 20% additions to the existing manifest's
  requirement count auto-flags ``requires_explicit_approval: true``
- A delta proposing > 10% removals auto-flags
  ``requires_explicit_approval: true``
- Removals of requirements with frequency > 0.50 require a
  ``migration_note`` field justifying the removal

Validators do NOT reject deltas that hit the percentage thresholds —
they FLAG them. Reviewers can still merge a flagged delta; the flag
exists so we can never silently ship a large change. Validators DO
reject malformed entries, missing evidence, and removals of
high-frequency requirements without a migration note.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .curriculum_plan import (
    CURRICULUM_PLAN_SCHEMA_VERSION,
    CoverageStatus,
    CurriculumPlan,
    Evidence,
    Requirement,
    _VALID_COVERAGE,
    _VALID_PROVENANCE,
    write_curriculum_plan,
)

LOGGER = logging.getLogger(__name__)

DELTA_SCHEMA_VERSION = 1

# Continuity-policy thresholds. Sourcing them as constants makes the
# policy easy to change in one place if it ever needs tuning.
MIN_EVIDENCE_PER_ADDITION = 3
MIN_FREQUENCY_PER_ADDITION = 0.30
ADDITION_FLAG_THRESHOLD = 0.20  # > 20% additions vs current count
REMOVAL_FLAG_THRESHOLD = 0.10  # > 10% removals vs current count
HIGH_FREQUENCY_REMOVAL_THRESHOLD = 0.50  # requires migration_note


class CurriculumPlanDeltaError(ValueError):
    """Raised when a delta is malformed."""


# ---------- delta record types ----------


@dataclass(frozen=True)
class RequirementAddition:
    requirement: Requirement
    rationale: str = ""


@dataclass(frozen=True)
class RequirementUpdate:
    """Patch fields on an existing requirement.

    Any field set to ``None`` is left untouched on apply. ``evidence_add``
    is appended to the existing list, NOT replaced — the research cycle
    grows the evidence; it doesn't curate it. Removing evidence is a
    separate, explicit operation that lives outside the delta API.
    """

    id: str
    label: str | None = None
    frequency: float | None = None
    coverage_status: CoverageStatus | None = None
    evidence_add: tuple[Evidence, ...] = ()
    exercises_add: tuple[str, ...] = ()
    projects_add: tuple[str, ...] = ()
    solutions_add: tuple[str, ...] = ()
    tests_add: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True)
class RequirementRemoval:
    id: str
    migration_note: str = ""


@dataclass(frozen=True)
class CurriculumPlanDelta:
    schema_version: int
    role: str
    month: str  # YYYY-MM
    rationale: str
    research_window: dict[str, Any] = field(default_factory=dict)
    additions: tuple[RequirementAddition, ...] = ()
    updates: tuple[RequirementUpdate, ...] = ()
    removals: tuple[RequirementRemoval, ...] = ()
    # Set by the validator, not by the agent. ``True`` when the delta
    # exceeds an auto-flag threshold; reviewers must explicitly approve.
    requires_explicit_approval: bool = False
    validation_notes: tuple[str, ...] = ()


# ---------- loaders ----------


def load_delta(path: Path) -> CurriculumPlanDelta:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise CurriculumPlanDeltaError(f"{path}: root must be an object")

    schema = int(raw.get("schema_version", 0))
    if schema != DELTA_SCHEMA_VERSION:
        raise CurriculumPlanDeltaError(
            f"{path}: schema_version={schema} != expected {DELTA_SCHEMA_VERSION}"
        )

    return CurriculumPlanDelta(
        schema_version=schema,
        role=_required_str(raw, "role"),
        month=_required_str(raw, "month"),
        rationale=str(raw.get("rationale", "")),
        research_window=dict(raw.get("research_window") or {}),
        additions=tuple(_parse_addition(a) for a in raw.get("additions", [])),
        updates=tuple(_parse_update(u) for u in raw.get("updates", [])),
        removals=tuple(_parse_removal(r) for r in raw.get("removals", [])),
        requires_explicit_approval=bool(raw.get("requires_explicit_approval", False)),
        validation_notes=tuple(str(n) for n in raw.get("validation_notes", [])),
    )


def dump_delta(delta: CurriculumPlanDelta) -> dict[str, Any]:
    return {
        "schema_version": delta.schema_version,
        "role": delta.role,
        "month": delta.month,
        "rationale": delta.rationale,
        "research_window": delta.research_window,
        "requires_explicit_approval": delta.requires_explicit_approval,
        "validation_notes": list(delta.validation_notes),
        "additions": [
            {
                "rationale": a.rationale,
                "requirement": _dump_addition_requirement(a.requirement),
            }
            for a in delta.additions
        ],
        "updates": [
            {
                "id": u.id,
                "label": u.label,
                "frequency": u.frequency,
                "coverage_status": u.coverage_status,
                "notes": u.notes,
                "evidence_add": [_dump_evidence(e) for e in u.evidence_add],
                "exercises_add": list(u.exercises_add),
                "projects_add": list(u.projects_add),
                "solutions_add": list(u.solutions_add),
                "tests_add": list(u.tests_add),
            }
            for u in delta.updates
        ],
        "removals": [
            {"id": r.id, "migration_note": r.migration_note} for r in delta.removals
        ],
    }


def write_delta(delta: CurriculumPlanDelta, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dump_delta(delta), indent=2) + "\n", encoding="utf-8")


# ---------- validation ----------


def validate_delta(
    delta: CurriculumPlanDelta, baseline: CurriculumPlan
) -> CurriculumPlanDelta:
    """Run continuity-policy validation. Returns a delta with notes + flags set.

    Reject conditions (raise):
    - Addition with < MIN_EVIDENCE_PER_ADDITION evidence items
    - Addition with frequency < MIN_FREQUENCY_PER_ADDITION
    - Addition whose ID collides with an existing requirement
    - Update / removal referencing a non-existent requirement ID
    - Removal of a high-frequency requirement (> 0.50) without
      migration_note

    Flag conditions (do NOT reject, but set requires_explicit_approval):
    - Additions count > ADDITION_FLAG_THRESHOLD of baseline.requirement_count
    - Removals count > REMOVAL_FLAG_THRESHOLD of baseline.requirement_count
    """
    if delta.role != baseline.role:
        raise CurriculumPlanDeltaError(
            f"delta.role={delta.role!r} does not match baseline.role={baseline.role!r}"
        )

    baseline_ids = {r.id for r in baseline.requirements}
    baseline_by_id = {r.id: r for r in baseline.requirements}
    notes: list[str] = []
    flag = False

    # Additions: schema validation + collision + evidence/frequency thresholds.
    for addition in delta.additions:
        req = addition.requirement
        if req.id in baseline_ids:
            raise CurriculumPlanDeltaError(
                f"addition `{req.id}` collides with an existing requirement"
            )
        if len(req.evidence) < MIN_EVIDENCE_PER_ADDITION:
            raise CurriculumPlanDeltaError(
                f"addition `{req.id}` carries only {len(req.evidence)} evidence "
                f"item(s); minimum is {MIN_EVIDENCE_PER_ADDITION}"
            )
        if req.frequency is None or req.frequency < MIN_FREQUENCY_PER_ADDITION:
            raise CurriculumPlanDeltaError(
                f"addition `{req.id}` has frequency "
                f"{req.frequency} < {MIN_FREQUENCY_PER_ADDITION}"
            )
        if req.provenance != "research":
            raise CurriculumPlanDeltaError(
                f"addition `{req.id}` must have provenance='research' "
                f"(got {req.provenance!r})"
            )

    # Updates: must target existing IDs.
    for update in delta.updates:
        if update.id not in baseline_ids:
            raise CurriculumPlanDeltaError(
                f"update targets unknown requirement `{update.id}`"
            )
        if update.frequency is not None and not (0.0 <= update.frequency <= 1.0):
            raise CurriculumPlanDeltaError(
                f"update `{update.id}` has out-of-range frequency {update.frequency}"
            )

    # Removals: must target existing IDs + high-frequency removals need
    # an explicit migration note.
    for removal in delta.removals:
        if removal.id not in baseline_ids:
            raise CurriculumPlanDeltaError(
                f"removal targets unknown requirement `{removal.id}`"
            )
        existing = baseline_by_id[removal.id]
        if (
            existing.frequency is not None
            and existing.frequency > HIGH_FREQUENCY_REMOVAL_THRESHOLD
            and not removal.migration_note.strip()
        ):
            raise CurriculumPlanDeltaError(
                f"removal `{removal.id}` (frequency {existing.frequency}) "
                "is above the high-frequency threshold and requires a "
                "migration_note"
            )

    # Flag thresholds.
    baseline_count = max(baseline.requirement_count, 1)
    addition_ratio = len(delta.additions) / baseline_count
    removal_ratio = len(delta.removals) / baseline_count
    if addition_ratio > ADDITION_FLAG_THRESHOLD:
        flag = True
        notes.append(
            f"additions {len(delta.additions)} of baseline {baseline_count} "
            f"= {addition_ratio:.1%} > {ADDITION_FLAG_THRESHOLD:.0%} threshold"
        )
    if removal_ratio > REMOVAL_FLAG_THRESHOLD:
        flag = True
        notes.append(
            f"removals {len(delta.removals)} of baseline {baseline_count} "
            f"= {removal_ratio:.1%} > {REMOVAL_FLAG_THRESHOLD:.0%} threshold"
        )

    if flag:
        notes.insert(
            0,
            "auto-flagged requires_explicit_approval — reviewer must explicitly "
            "confirm scope before merge",
        )

    return replace(
        delta,
        requires_explicit_approval=flag,
        validation_notes=tuple(notes),
    )


# ---------- apply ----------


def apply_delta(delta: CurriculumPlanDelta, baseline: CurriculumPlan) -> CurriculumPlan:
    """Produce a new CurriculumPlan that reflects the validated delta.

    Caller is expected to have run :func:`validate_delta` first (the
    apply function does not re-validate; it trusts validation to have
    been done at delta-load time).
    """
    if delta.role != baseline.role:
        raise CurriculumPlanDeltaError(
            f"apply: delta.role={delta.role!r} != baseline.role={baseline.role!r}"
        )

    by_id = {r.id: r for r in baseline.requirements}

    # Removals.
    for removal in delta.removals:
        by_id.pop(removal.id, None)

    # Updates.
    for update in delta.updates:
        existing = by_id.get(update.id)
        if existing is None:
            continue  # post-removal of same id — silently skip
        merged_evidence = (*existing.evidence, *update.evidence_add)
        merged_exercises = _merge_unique(existing.exercises, update.exercises_add)
        merged_projects = _merge_unique(existing.projects, update.projects_add)
        merged_solutions = _merge_unique(existing.solutions, update.solutions_add)
        merged_tests = _merge_unique(existing.tests, update.tests_add)
        by_id[update.id] = replace(
            existing,
            label=update.label if update.label is not None else existing.label,
            frequency=(
                update.frequency if update.frequency is not None else existing.frequency
            ),
            coverage_status=(
                update.coverage_status
                if update.coverage_status is not None
                else existing.coverage_status
            ),
            evidence=merged_evidence,
            exercises=merged_exercises,
            projects=merged_projects,
            solutions=merged_solutions,
            tests=merged_tests,
            notes=update.notes if update.notes is not None else existing.notes,
        )

    # Additions (after updates, so collisions would already be rejected
    # by validate_delta).
    for addition in delta.additions:
        by_id[addition.requirement.id] = addition.requirement

    new_requirements = tuple(
        by_id[req.id]
        for req in baseline.requirements
        if req.id in by_id
    ) + tuple(
        addition.requirement for addition in delta.additions
    )

    # Research window — pull through from the delta if provided.
    new_research = baseline.research
    if delta.research_window:
        from .curriculum_plan import ResearchWindow

        rw = delta.research_window
        new_research = ResearchWindow(
            window_start=rw.get("window_start") or baseline.research.window_start,
            window_end=rw.get("window_end") or baseline.research.window_end,
            postings_sampled=int(rw.get("postings_sampled") or baseline.research.postings_sampled),
            last_refreshed=rw.get("last_refreshed") or baseline.research.last_refreshed,
            sources=tuple(rw.get("sources") or baseline.research.sources),
        )

    return CurriculumPlan(
        schema_version=baseline.schema_version,
        role=baseline.role,
        role_title=baseline.role_title,
        research=new_research,
        requirements=new_requirements,
    )


def apply_delta_to_file(
    delta: CurriculumPlanDelta, baseline_path: Path, out_path: Path | None = None
) -> CurriculumPlan:
    from .curriculum_plan import load_curriculum_plan

    baseline = load_curriculum_plan(baseline_path)
    validated = validate_delta(delta, baseline)
    if validated.requires_explicit_approval:
        LOGGER.warning(
            "Delta for %s requires explicit approval: %s",
            delta.role,
            "; ".join(validated.validation_notes),
        )
    new_plan = apply_delta(validated, baseline)
    if out_path is not None:
        write_curriculum_plan(new_plan, out_path)
    return new_plan


# ---------- parsing helpers ----------


def _parse_addition(raw: Any) -> RequirementAddition:
    if not isinstance(raw, dict):
        raise CurriculumPlanDeltaError("addition entries must be objects")
    req_raw = raw.get("requirement")
    if not isinstance(req_raw, dict):
        raise CurriculumPlanDeltaError("addition.requirement must be an object")
    return RequirementAddition(
        requirement=_parse_addition_requirement(req_raw),
        rationale=str(raw.get("rationale", "")),
    )


def _parse_addition_requirement(raw: dict[str, Any]) -> Requirement:
    provenance = str(raw.get("provenance", "research"))
    if provenance not in _VALID_PROVENANCE:
        raise CurriculumPlanDeltaError(
            f"addition.requirement.provenance={provenance!r} invalid"
        )
    coverage = str(raw.get("coverage_status", "missing"))
    if coverage not in _VALID_COVERAGE:
        raise CurriculumPlanDeltaError(
            f"addition.requirement.coverage_status={coverage!r} invalid"
        )
    return Requirement(
        id=_required_str(raw, "id"),
        label=_required_str(raw, "label"),
        frequency=_optional_float(raw.get("frequency")),
        provenance=provenance,  # type: ignore[arg-type]
        requires_confirmation=bool(raw.get("requires_confirmation", False)),
        evidence=tuple(_parse_evidence(e) for e in raw.get("evidence", [])),
        exercises=tuple(str(s) for s in raw.get("exercises", [])),
        projects=tuple(str(s) for s in raw.get("projects", [])),
        solutions=tuple(str(s) for s in raw.get("solutions", [])),
        tests=tuple(str(s) for s in raw.get("tests", [])),
        coverage_status=coverage,  # type: ignore[arg-type]
        notes=str(raw.get("notes", "")),
    )


def _parse_update(raw: Any) -> RequirementUpdate:
    if not isinstance(raw, dict):
        raise CurriculumPlanDeltaError("update entries must be objects")
    coverage = raw.get("coverage_status")
    if coverage is not None and coverage not in _VALID_COVERAGE:
        raise CurriculumPlanDeltaError(
            f"update.coverage_status={coverage!r} invalid"
        )
    return RequirementUpdate(
        id=_required_str(raw, "id"),
        label=raw.get("label"),
        frequency=_optional_float(raw.get("frequency")),
        coverage_status=coverage,  # type: ignore[arg-type]
        evidence_add=tuple(_parse_evidence(e) for e in raw.get("evidence_add", [])),
        exercises_add=tuple(str(s) for s in raw.get("exercises_add", [])),
        projects_add=tuple(str(s) for s in raw.get("projects_add", [])),
        solutions_add=tuple(str(s) for s in raw.get("solutions_add", [])),
        tests_add=tuple(str(s) for s in raw.get("tests_add", [])),
        notes=raw.get("notes"),
    )


def _parse_removal(raw: Any) -> RequirementRemoval:
    if not isinstance(raw, dict):
        raise CurriculumPlanDeltaError("removal entries must be objects")
    return RequirementRemoval(
        id=_required_str(raw, "id"),
        migration_note=str(raw.get("migration_note", "")),
    )


def _parse_evidence(raw: Any) -> Evidence:
    if not isinstance(raw, dict):
        raise CurriculumPlanDeltaError("evidence entries must be objects")
    return Evidence(
        posting_id=str(raw.get("posting_id", "")),
        phrase=str(raw.get("phrase", "")),
        employer=str(raw.get("employer", "")),
        title=str(raw.get("title", "")),
        url=str(raw.get("url", "")),
        date_observed=str(raw.get("date_observed", "")),
    )


def _dump_addition_requirement(req: Requirement) -> dict[str, Any]:
    return {
        "id": req.id,
        "label": req.label,
        "frequency": req.frequency,
        "provenance": req.provenance,
        "requires_confirmation": req.requires_confirmation,
        "evidence": [_dump_evidence(e) for e in req.evidence],
        "exercises": list(req.exercises),
        "projects": list(req.projects),
        "solutions": list(req.solutions),
        "tests": list(req.tests),
        "coverage_status": req.coverage_status,
        "notes": req.notes,
    }


def _dump_evidence(e: Evidence) -> dict[str, Any]:
    return {
        "posting_id": e.posting_id,
        "phrase": e.phrase,
        "employer": e.employer,
        "title": e.title,
        "url": e.url,
        "date_observed": e.date_observed,
    }


def _merge_unique(existing: tuple[str, ...], add: tuple[str, ...]) -> tuple[str, ...]:
    seen = set(existing)
    extras = tuple(x for x in add if x not in seen and not seen.add(x))
    return (*existing, *extras)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CurriculumPlanDeltaError(f"delta file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CurriculumPlanDeltaError(f"invalid JSON in {path}: {exc}") from exc


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CurriculumPlanDeltaError(f"missing or invalid string field: {key}")
    return value.strip()


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
