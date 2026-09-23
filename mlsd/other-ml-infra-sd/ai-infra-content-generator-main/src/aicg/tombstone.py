"""Tombstones + changelog rendering for retirement (design U-H4, S7).

When content is retired it is `git rm`'d from `main` (decision D3), so the only
record a learner can find is what we leave behind. Two artifacts make
"technically recoverable" actually usable:

- a **tombstone** (`RETIRED.md`) left at the retired path, so a learner
  following an old link hits a signpost — what it covered, when it was retired,
  and a direct link to the release that still contains it — not a 404.
- a per-repo **changelog entry** stating what was added/retired, since the
  monthly tags are otherwise the only history.

Pure rendering; the caller does the `git rm` + commit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetiredNode:
    node_id: str
    title: str
    summary: str  # one line: what it covered
    retired_on: str  # YYYY-MM-DD (passed in; no clock in this module)
    last_version: str  # tag that still contains it, e.g. v2026.05
    release_url: str  # direct link to that release


def render_tombstone(node: RetiredNode) -> str:
    """Render the `RETIRED.md` left at a retired node's path."""
    return (
        f"# {node.title} — retired\n\n"
        f"> This module was retired on **{node.retired_on}** because it fell out of "
        f"the average job-market requirements for this role.\n\n"
        f"**What it covered:** {node.summary}\n\n"
        f"It is preserved in the last release that still contained it: "
        f"**[{node.last_version}]({node.release_url})**. Download that release if you "
        f"need the original material.\n\n"
        f"See this repository's `CHANGELOG.md` for the full evolution history.\n"
    )


def render_changelog_entry(
    version: str, date: str, added: list[str], retired: list[str]
) -> str:
    """Render one monthly changelog section (newest goes on top in the file)."""
    lines = [f"## {version} — {date}", ""]
    if added:
        lines.append("### Added")
        lines.append("")
        lines += [f"- {a}" for a in added]
        lines.append("")
    if retired:
        lines.append("### Retired")
        lines.append("")
        lines += [f"- {r}" for r in retired]
        lines.append("")
    if not added and not retired:
        lines.append("No curriculum changes this period.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
