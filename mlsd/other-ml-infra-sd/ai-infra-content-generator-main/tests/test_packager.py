"""Tests for the monthly packaging plan (P5 / S10)."""

from aicg.packager import (
    RepoChange,
    build_archive_index_rows,
    plan_monthly_package,
    tagged_repos,
)


def test_only_changed_repos_are_tagged() -> None:
    changes = [
        RepoChange("repo-a", changed_since_last_tag=True, added=("mod-new",), retired=("mod-old",)),
        RepoChange("repo-b", changed_since_last_tag=False),
    ]
    plans = plan_monthly_package(changes, version="v2026.06", date="2026-06-01")
    by_repo = {p.repo: p for p in plans}
    assert by_repo["repo-a"].action == "tag"
    assert "mod-new" in by_repo["repo-a"].changelog
    assert "mod-old" in by_repo["repo-a"].changelog
    assert by_repo["repo-b"].action == "skip-unchanged"
    assert by_repo["repo-b"].changelog == ""


def test_tagged_repos_lists_only_tag_actions() -> None:
    changes = [
        RepoChange("a", True, added=("x",)),
        RepoChange("b", False),
        RepoChange("c", True),
    ]
    plans = plan_monthly_package(changes, version="v2026.06", date="2026-06-01")
    assert tagged_repos(plans) == ["a", "c"]


def test_archive_index_rows_distinguish_tagged_and_unchanged() -> None:
    changes = [RepoChange("a", True, added=("x",)), RepoChange("b", False)]
    plans = plan_monthly_package(changes, version="v2026.06", date="2026-06-01")
    rows = build_archive_index_rows(plans)
    assert any("a" in r and "v2026.06" in r for r in rows)
    assert any("b" in r and "unchanged" in r for r in rows)


def test_no_changes_means_no_tags() -> None:
    changes = [RepoChange("a", False), RepoChange("b", False)]
    plans = plan_monthly_package(changes, version="v2026.07", date="2026-07-01")
    assert tagged_repos(plans) == []
