"""Tests for tombstone/changelog rendering and the status-issue formatter."""

from aicg.status_report import DailyStatus, status_issue_body, status_issue_title
from aicg.tombstone import RetiredNode, render_changelog_entry, render_tombstone


def test_tombstone_signposts_to_the_release() -> None:
    node = RetiredNode(
        node_id="mod-x",
        title="Legacy Serving Patterns",
        summary="TF1 Session-based model serving",
        retired_on="2026-06-24",
        last_version="v2026.05",
        release_url="https://github.com/org/repo/releases/tag/v2026.05",
    )
    md = render_tombstone(node)
    assert md.count("# ") == 1  # single H1
    assert "retired on **2026-06-24**" in md
    assert "v2026.05" in md and node.release_url in md
    assert "What it covered" in md
    assert md.endswith("\n")


def test_changelog_entry_lists_added_and_retired() -> None:
    entry = render_changelog_entry(
        "v2026.06", "2026-06-01", added=["mod-new: Agentic Eval"], retired=["mod-old: V100 sizing"]
    )
    assert "## v2026.06 — 2026-06-01" in entry
    assert "### Added" in entry and "mod-new: Agentic Eval" in entry
    assert "### Retired" in entry and "mod-old: V100 sizing" in entry


def test_changelog_entry_handles_no_change() -> None:
    entry = render_changelog_entry("v2026.07", "2026-07-01", added=[], retired=[])
    assert "No curriculum changes this period." in entry
    assert "### Added" not in entry


def test_status_title_flags_unhealthy() -> None:
    ok = DailyStatus(date="2026-06-24", merged=3)
    bad = DailyStatus(date="2026-06-24", quarantined=1)
    skip = DailyStatus(date="2026-06-24", auth_skips=2)
    assert status_issue_title(ok).startswith("✅")
    assert status_issue_title(bad).startswith("⚠️")
    assert status_issue_title(skip).startswith("⚠️")


def test_status_body_reports_metrics_and_quarantine() -> None:
    s = DailyStatus(
        date="2026-06-24",
        merged=5,
        quarantined=2,
        queue_depth=11,
        budget_used=18,
        budget_total=20,
        auth_skips=0,
        quarantine_flags=["mod-309/ex-02 (failing rubric)"],
    )
    body = status_issue_body(s)
    assert "**Merged today:** 5" in body
    assert "18 / 20 (90%)" in body
    assert "mod-309/ex-02 (failing rubric)" in body


def test_status_body_warns_on_auth_skips() -> None:
    body = status_issue_body(DailyStatus(date="2026-06-24", auth_skips=3))
    assert "skipped on an auth/API failure" in body
