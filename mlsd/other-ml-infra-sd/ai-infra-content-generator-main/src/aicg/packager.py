"""Monthly packaging plan (design §4.5, review S10/S8/U-H4).

The monthly tag + Release is the archive mechanism (decision D3): retired
content leaves `main` but survives in the dated release. This module decides
*what* to package — only repos changed since their last tag (S10), each with a
changelog entry stating what was added/retired — and the archive-index rows.

It is pure: the caller performs the `git tag`, `gh release create`, and tarball
build (idempotent + resumable per S8). Keeping the decision here makes the
"changed-only" rule and the changelog assembly testable without git.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tombstone import render_changelog_entry


@dataclass(frozen=True)
class RepoChange:
    repo: str
    changed_since_last_tag: bool
    added: tuple[str, ...] = ()
    retired: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepoPackagePlan:
    repo: str
    action: str  # "tag" | "skip-unchanged"
    version: str
    changelog: str  # markdown changelog entry (empty when skipped)


def plan_monthly_package(
    changes: list[RepoChange], *, version: str, date: str
) -> list[RepoPackagePlan]:
    """Decide which repos to tag this month (only those changed since last tag)."""
    plans: list[RepoPackagePlan] = []
    for c in changes:
        if c.changed_since_last_tag:
            changelog = render_changelog_entry(version, date, list(c.added), list(c.retired))
            plans.append(RepoPackagePlan(c.repo, "tag", version, changelog))
        else:
            plans.append(RepoPackagePlan(c.repo, "skip-unchanged", version, ""))
    return plans


def build_archive_index_rows(plans: list[RepoPackagePlan]) -> list[str]:
    """One markdown row per repo for ARCHIVE_INDEX.md."""
    rows: list[str] = []
    for p in plans:
        if p.action == "tag":
            rows.append(f"- **{p.repo}** — [`{p.version}`](releases) (tagged this cycle)")
        else:
            rows.append(f"- **{p.repo}** — unchanged since its last tag")
    return rows


def tagged_repos(plans: list[RepoPackagePlan]) -> list[str]:
    """Repos that actually get a new tag this cycle (for resumable packaging, S8)."""
    return [p.repo for p in plans if p.action == "tag"]
