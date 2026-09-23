"""Per-role curriculum-plan manifests.

The traceability manifest the user used to maintain by hand. One JSON
file per role at ``manifest/curriculum_plan.<slug>.manifest.json``,
plus a slim ``manifest/curriculum_plan.index.json`` that summarizes the
roster.

Each requirement traces the full chain:
- evidence (job postings)
- discussion_topics (GitHub Discussions threads, populated by W2.3)
- exercises (slugs — paths resolved via the structural manifest)
- projects (slugs)
- solutions (paths in the matching solutions repo)
- tests (paths to tests that prove coverage)

Schema and lifecycle decisions are documented in the project memory
``project_curriculum_plan_manifest.md``. Key invariants enforced here:

- ``schema_version: 1`` — bump if the traceability fields change shape
- Provenance is required (``"research" | "backfilled" | "manual"``)
- Items with ``provenance="backfilled"`` must carry ``requires_confirmation: true``
  so human reviewers can find them
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

LOGGER = logging.getLogger(__name__)

CURRICULUM_PLAN_SCHEMA_VERSION = 1
INDEX_SCHEMA_VERSION = 1

Provenance = Literal["research", "backfilled", "manual"]
CoverageStatus = Literal["covered", "partial", "missing"]
_VALID_PROVENANCE: frozenset[str] = frozenset({"research", "backfilled", "manual"})
_VALID_COVERAGE: frozenset[str] = frozenset({"covered", "partial", "missing"})


class CurriculumPlanError(ValueError):
    """Raised when a curriculum-plan manifest is malformed."""


# ---------- per-requirement records ----------


@dataclass(frozen=True)
class Evidence:
    """A single job-posting citation."""

    posting_id: str
    phrase: str
    employer: str = ""
    title: str = ""
    url: str = ""
    date_observed: str = ""


@dataclass(frozen=True)
class DiscussionTopic:
    """A GitHub Discussion thread that touches this requirement."""

    thread_url: str
    category: str = ""
    title: str = ""
    matched_via: str = ""  # e.g., "keyword:kubernetes" or "manual"


@dataclass(frozen=True)
class Requirement:
    id: str
    label: str
    frequency: float | None = None
    provenance: Provenance = "manual"
    requires_confirmation: bool = False
    evidence: tuple[Evidence, ...] = ()
    discussion_topics: tuple[DiscussionTopic, ...] = ()
    exercises: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    solutions: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    coverage_status: CoverageStatus = "missing"
    notes: str = ""

    def has_any_coverage(self) -> bool:
        return bool(self.exercises or self.projects)


# ---------- per-role manifest ----------


@dataclass(frozen=True)
class ResearchWindow:
    """Markers for which research cycle populated this manifest."""

    window_start: str | None = None
    window_end: str | None = None
    postings_sampled: int = 0
    last_refreshed: str | None = None
    sources: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class CurriculumPlan:
    schema_version: int
    role: str
    role_title: str
    research: ResearchWindow
    requirements: tuple[Requirement, ...]

    def requirement_by_id(self, req_id: str) -> Requirement | None:
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None

    def coverage_breakdown(self) -> dict[str, int]:
        counts: dict[str, int] = {"covered": 0, "partial": 0, "missing": 0}
        for req in self.requirements:
            counts[req.coverage_status] = counts.get(req.coverage_status, 0) + 1
        return counts

    @property
    def requirement_count(self) -> int:
        return len(self.requirements)


# ---------- index across roles ----------


@dataclass(frozen=True)
class CurriculumPlanIndexEntry:
    slug: str
    file: str
    requirement_count: int
    coverage: dict[str, int]
    role_title: str = ""


@dataclass(frozen=True)
class CurriculumPlanIndex:
    schema_version: int
    generated_at: str
    roles: tuple[CurriculumPlanIndexEntry, ...]

    def get(self, slug: str) -> CurriculumPlanIndexEntry | None:
        for entry in self.roles:
            if entry.slug == slug:
                return entry
        return None


# ---------- loaders ----------


def load_curriculum_plan(path: Path) -> CurriculumPlan:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise CurriculumPlanError(f"{path}: root must be an object")

    schema = int(raw.get("schema_version", 0))
    if schema != CURRICULUM_PLAN_SCHEMA_VERSION:
        raise CurriculumPlanError(
            f"{path}: schema_version={schema} != expected {CURRICULUM_PLAN_SCHEMA_VERSION}"
        )

    requirements = tuple(_parse_requirement(item, path) for item in raw.get("requirements", []))
    research = _parse_research(raw.get("research") or {})

    return CurriculumPlan(
        schema_version=schema,
        role=_required_str(raw, "role"),
        role_title=_required_str(raw, "role_title"),
        research=research,
        requirements=requirements,
    )


def load_curriculum_plan_index(path: Path) -> CurriculumPlanIndex:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise CurriculumPlanError(f"{path}: root must be an object")

    schema = int(raw.get("schema_version", 0))
    if schema != INDEX_SCHEMA_VERSION:
        raise CurriculumPlanError(
            f"{path}: schema_version={schema} != expected {INDEX_SCHEMA_VERSION}"
        )

    entries = tuple(_parse_index_entry(item, path) for item in raw.get("roles", []))
    return CurriculumPlanIndex(
        schema_version=schema,
        generated_at=str(raw.get("generated_at", "")),
        roles=entries,
    )


# ---------- writers ----------


def dump_curriculum_plan(plan: CurriculumPlan) -> dict[str, Any]:
    """Serialize a CurriculumPlan back to plain JSON-shaped dict."""
    return {
        "schema_version": plan.schema_version,
        "role": plan.role,
        "role_title": plan.role_title,
        "research": {
            "window_start": plan.research.window_start,
            "window_end": plan.research.window_end,
            "postings_sampled": plan.research.postings_sampled,
            "last_refreshed": plan.research.last_refreshed,
            "sources": list(plan.research.sources),
        },
        "requirements": [_dump_requirement(r) for r in plan.requirements],
    }


def dump_curriculum_plan_index(index: CurriculumPlanIndex) -> dict[str, Any]:
    return {
        "schema_version": index.schema_version,
        "generated_at": index.generated_at,
        "roles": [
            {
                "slug": e.slug,
                "file": e.file,
                "role_title": e.role_title,
                "requirement_count": e.requirement_count,
                "coverage": dict(e.coverage),
            }
            for e in index.roles
        ],
    }


def write_curriculum_plan(plan: CurriculumPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dump_curriculum_plan(plan), indent=2) + "\n", encoding="utf-8")


def write_curriculum_plan_index(index: CurriculumPlanIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dump_curriculum_plan_index(index), indent=2) + "\n", encoding="utf-8")


# ---------- parsing helpers ----------


def _parse_research(raw: Any) -> ResearchWindow:
    if not isinstance(raw, dict):
        raise CurriculumPlanError("`research` must be an object")
    return ResearchWindow(
        window_start=raw.get("window_start"),
        window_end=raw.get("window_end"),
        postings_sampled=int(raw.get("postings_sampled", 0)),
        last_refreshed=raw.get("last_refreshed"),
        sources=tuple(
            dict(item)
            for item in raw.get("sources", [])
            if isinstance(item, dict)
        ),
    )


def _parse_requirement(raw: Any, path: Path) -> Requirement:
    if not isinstance(raw, dict):
        raise CurriculumPlanError(f"{path}: each requirement must be an object")

    provenance = str(raw.get("provenance", "manual"))
    if provenance not in _VALID_PROVENANCE:
        raise CurriculumPlanError(
            f"{path}: requirement `{raw.get('id')}` has invalid provenance "
            f"{provenance!r}; must be one of {sorted(_VALID_PROVENANCE)}"
        )

    requires_confirmation = bool(raw.get("requires_confirmation", False))
    if provenance == "backfilled" and not requires_confirmation:
        raise CurriculumPlanError(
            f"{path}: requirement `{raw.get('id')}` is backfilled but "
            "missing requires_confirmation:true"
        )

    coverage_status = str(raw.get("coverage_status", "missing"))
    if coverage_status not in _VALID_COVERAGE:
        raise CurriculumPlanError(
            f"{path}: requirement `{raw.get('id')}` has invalid "
            f"coverage_status {coverage_status!r}; must be one of {sorted(_VALID_COVERAGE)}"
        )

    return Requirement(
        id=_required_str(raw, "id"),
        label=_required_str(raw, "label"),
        frequency=_optional_float(raw.get("frequency")),
        provenance=provenance,  # type: ignore[arg-type]
        requires_confirmation=requires_confirmation,
        evidence=tuple(_parse_evidence(e) for e in raw.get("evidence", [])),
        discussion_topics=tuple(_parse_topic(t) for t in raw.get("discussion_topics", [])),
        exercises=tuple(str(s) for s in raw.get("exercises", [])),
        projects=tuple(str(s) for s in raw.get("projects", [])),
        solutions=tuple(str(s) for s in raw.get("solutions", [])),
        tests=tuple(str(s) for s in raw.get("tests", [])),
        coverage_status=coverage_status,  # type: ignore[arg-type]
        notes=str(raw.get("notes", "")),
    )


def _parse_evidence(raw: Any) -> Evidence:
    if not isinstance(raw, dict):
        raise CurriculumPlanError("evidence entries must be objects")
    return Evidence(
        posting_id=str(raw.get("posting_id", "")),
        phrase=str(raw.get("phrase", "")),
        employer=str(raw.get("employer", "")),
        title=str(raw.get("title", "")),
        url=str(raw.get("url", "")),
        date_observed=str(raw.get("date_observed", "")),
    )


def _parse_topic(raw: Any) -> DiscussionTopic:
    if not isinstance(raw, dict):
        raise CurriculumPlanError("discussion_topics entries must be objects")
    return DiscussionTopic(
        thread_url=_required_str(raw, "thread_url"),
        category=str(raw.get("category", "")),
        title=str(raw.get("title", "")),
        matched_via=str(raw.get("matched_via", "")),
    )


def _parse_index_entry(raw: Any, path: Path) -> CurriculumPlanIndexEntry:
    if not isinstance(raw, dict):
        raise CurriculumPlanError(f"{path}: each index entry must be an object")
    coverage_raw = raw.get("coverage") or {}
    if not isinstance(coverage_raw, dict):
        raise CurriculumPlanError(f"{path}: index entry coverage must be an object")
    coverage = {str(k): int(v) for k, v in coverage_raw.items()}
    return CurriculumPlanIndexEntry(
        slug=_required_str(raw, "slug"),
        file=_required_str(raw, "file"),
        requirement_count=int(raw.get("requirement_count", 0)),
        coverage=coverage,
        role_title=str(raw.get("role_title", "")),
    )


def _dump_requirement(req: Requirement) -> dict[str, Any]:
    return {
        "id": req.id,
        "label": req.label,
        "frequency": req.frequency,
        "provenance": req.provenance,
        "requires_confirmation": req.requires_confirmation,
        "evidence": [
            {
                "posting_id": e.posting_id,
                "phrase": e.phrase,
                "employer": e.employer,
                "title": e.title,
                "url": e.url,
                "date_observed": e.date_observed,
            }
            for e in req.evidence
        ],
        "discussion_topics": [
            {
                "thread_url": t.thread_url,
                "category": t.category,
                "title": t.title,
                "matched_via": t.matched_via,
            }
            for t in req.discussion_topics
        ],
        "exercises": list(req.exercises),
        "projects": list(req.projects),
        "solutions": list(req.solutions),
        "tests": list(req.tests),
        "coverage_status": req.coverage_status,
        "notes": req.notes,
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CurriculumPlanError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CurriculumPlanError(f"invalid JSON in {path}: {exc}") from exc


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CurriculumPlanError(f"missing or invalid string field: {key}")
    return value.strip()


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
