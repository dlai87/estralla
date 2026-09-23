"""Coverage report for a per-role curriculum-plan manifest.

Powers ``aicg org plan-coverage --role <slug>``. Reads the per-role
manifest, groups requirements by ``coverage_status``, and reports gaps
in a form that's useful for the next research cycle.

For ``missing`` rows: surfaces the requirement label, frequency (if any
evidence is attached), and a short keyword summary distilled from the
label so the operator can decide whether to feed it into next-cycle
research targeting.

For ``partial`` rows: surfaces *what's* partial — no test? no project
anchor? — so the gap can be closed by a small content PR instead of a
research cycle.

The function is library-shaped (returns a dict) so the CLI can render
either text or JSON without rerunning the analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .curriculum_plan import CurriculumPlan, Requirement


# Tokens we strip from labels when distilling a keyword summary —
# they're high-frequency in module titles and don't help research
# targeting.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "into",
        "from",
        "by",
        "at",
    }
)


@dataclass(frozen=True)
class CoverageGap:
    id: str
    label: str
    coverage_status: str
    frequency: float | None
    evidence_count: int
    exercises_count: int
    projects_count: int
    solutions_count: int
    tests_count: int
    discussion_topics_count: int
    keywords: tuple[str, ...]
    missing_pieces: tuple[str, ...]


def _keywords_from_label(label: str) -> tuple[str, ...]:
    tokens = (
        ch if ch.isalnum() else " "
        for ch in label.lower()
    )
    text = "".join(tokens)
    parts = [t for t in text.split() if t and t not in _STOPWORDS and len(t) > 2]
    seen: set[str] = set()
    unique: list[str] = []
    for token in parts:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
    return tuple(unique)


def _missing_pieces(req: Requirement) -> tuple[str, ...]:
    missing: list[str] = []
    if not req.exercises:
        missing.append("no exercise anchor")
    if not req.projects:
        missing.append("no project anchor")
    if not req.tests:
        missing.append("no tests")
    if not req.solutions:
        missing.append("no solution document")
    if not req.evidence:
        missing.append("no evidence")
    return tuple(missing)


def _gap_for(req: Requirement) -> CoverageGap:
    return CoverageGap(
        id=req.id,
        label=req.label,
        coverage_status=req.coverage_status,
        frequency=req.frequency,
        evidence_count=len(req.evidence),
        exercises_count=len(req.exercises),
        projects_count=len(req.projects),
        solutions_count=len(req.solutions),
        tests_count=len(req.tests),
        discussion_topics_count=len(req.discussion_topics),
        keywords=_keywords_from_label(req.label),
        missing_pieces=_missing_pieces(req),
    )


def coverage_report(plan: CurriculumPlan) -> dict[str, Any]:
    """Build a structured coverage report for one role's manifest."""
    grouped: dict[str, list[CoverageGap]] = {
        "covered": [],
        "partial": [],
        "missing": [],
    }
    for req in plan.requirements:
        grouped.setdefault(req.coverage_status, []).append(_gap_for(req))

    # Stable sort within each group: highest frequency first (research
    # targeting prefers most-cited gaps), then by ID.
    for group in grouped.values():
        group.sort(
            key=lambda gap: (-(gap.frequency or 0), gap.id),
        )

    summary = plan.coverage_breakdown()
    summary["total"] = plan.requirement_count

    return {
        "role": plan.role,
        "role_title": plan.role_title,
        "research": {
            "window_start": plan.research.window_start,
            "window_end": plan.research.window_end,
            "postings_sampled": plan.research.postings_sampled,
            "last_refreshed": plan.research.last_refreshed,
        },
        "summary": summary,
        "groups": {
            status: [asdict(gap) for gap in gaps]
            for status, gaps in grouped.items()
        },
    }


def render_text(report: dict[str, Any]) -> str:
    """Render the coverage report as a human-readable text block."""
    summary = report["summary"]
    lines = [
        f"# Coverage — {report['role_title']} (`{report['role']}`)",
        "",
        f"Total requirements: {summary['total']}",
        f"  covered: {summary.get('covered', 0)}",
        f"  partial: {summary.get('partial', 0)}",
        f"  missing: {summary.get('missing', 0)}",
        "",
    ]

    research = report.get("research") or {}
    if research.get("last_refreshed"):
        lines += [
            f"Last refreshed: {research['last_refreshed']} "
            f"(window {research.get('window_start')} → {research.get('window_end')}, "
            f"{research.get('postings_sampled', 0)} postings)",
            "",
        ]

    for status in ("missing", "partial", "covered"):
        gaps = report["groups"].get(status, [])
        if not gaps:
            continue
        lines.append(f"## {status.upper()} ({len(gaps)})")
        lines.append("")
        for gap in gaps:
            freq = (
                f" · freq {gap['frequency']:.0%}"
                if gap.get("frequency") is not None
                else ""
            )
            extras: list[str] = []
            if status == "missing" and gap.get("keywords"):
                extras.append("keywords: " + ", ".join(gap["keywords"][:6]))
            if status in ("missing", "partial") and gap.get("missing_pieces"):
                extras.append("missing: " + ", ".join(gap["missing_pieces"]))
            if status == "covered":
                extras.append(
                    f"{gap['exercises_count']} ex · {gap['tests_count']} tests "
                    f"· {gap['discussion_topics_count']} discussion thread(s)"
                )
            extras_str = (" — " + " · ".join(extras)) if extras else ""
            lines.append(f"- `{gap['id']}` — **{gap['label']}**{freq}{extras_str}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
