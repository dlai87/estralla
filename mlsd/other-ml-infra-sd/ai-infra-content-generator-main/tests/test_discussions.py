from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from conftest import write_minimal_manifest

from aicg.discussions import DiscussionsConfig, discussions_run
from aicg.org_config import load_manifest


def _setup(tmp_path: Path) -> tuple[Path, Path, "OrgManifest"]:
    workspace = tmp_path / "workspace"
    (workspace / "ai-infra-security-learning").mkdir(parents=True)
    (workspace / "ai-infra-security-solutions").mkdir(parents=True)
    (workspace / ".github").mkdir(parents=True)
    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    return workspace, tmp_path / "state", manifest


def _ts_days_ago(days: float) -> str:
    return (
        (datetime.now(timezone.utc) - timedelta(days=days))
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def test_discussions_flags_stale_qna(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup(tmp_path)
    fetched = {
        "nodes": [
            {
                "number": 12,
                "title": "How do I debug GPU OOM on H100?",
                "url": "https://example.com/12",
                "body": "I keep hitting OOM during training.",
                "createdAt": _ts_days_ago(20),
                "updatedAt": _ts_days_ago(14),
                "locked": False,
                "isAnswered": False,
                "upvoteCount": 1,
                "author": {"login": "engineer"},
                "category": {"name": "Q&A", "slug": "q-a"},
                "comments": {"totalCount": 0},
                "reactions": {"totalCount": 0},
            }
        ]
    }
    with patch(
        "aicg.discussions.fetch_discussions", return_value=fetched
    ):
        report = discussions_run(manifest, workspace, state_dir=state_dir)

    repo_reports = {repo["repo"]: repo for repo in report["repos"]}
    security = repo_reports["ai-infra-security-solutions"]
    assert security["needs_attention_count"] == 1
    flagged = security["needs_attention"][0]
    assert any("Q&A open" in r for r in flagged["reasons"])
    assert report["totals"]["needs_attention_count"] >= 1


def test_discussions_flags_new_module_keywords(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup(tmp_path)
    fetched = {
        "nodes": [
            {
                "number": 7,
                "title": "Propose module on vector DB sharding",
                "url": "https://example.com/7",
                "body": "We should add a new module covering this.",
                "createdAt": _ts_days_ago(2),
                "updatedAt": _ts_days_ago(1),
                "locked": False,
                "isAnswered": False,
                "upvoteCount": 0,
                "author": {"login": "learner"},
                "category": {"name": "Ideas", "slug": "ideas"},
                "comments": {"totalCount": 2},
                "reactions": {"totalCount": 0},
            }
        ]
    }
    with patch(
        "aicg.discussions.fetch_discussions", return_value=fetched
    ):
        report = discussions_run(manifest, workspace, state_dir=state_dir)

    flagged_reasons: list[str] = []
    for repo in report["repos"]:
        for item in repo.get("needs_attention", []):
            flagged_reasons.extend(item["reasons"])
    assert any("curriculum gap" in r for r in flagged_reasons)


def test_discussions_skips_answered_qna(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup(tmp_path)
    fetched = {
        "nodes": [
            {
                "number": 1,
                "title": "Resolved question",
                "url": "https://example.com/1",
                "body": "Answered already.",
                "createdAt": _ts_days_ago(30),
                "updatedAt": _ts_days_ago(28),
                "locked": False,
                "isAnswered": True,
                "upvoteCount": 0,
                "author": {"login": "engineer"},
                "category": {"name": "Q&A", "slug": "q-a"},
                "comments": {"totalCount": 3},
                "reactions": {"totalCount": 0},
            }
        ]
    }
    with patch(
        "aicg.discussions.fetch_discussions", return_value=fetched
    ):
        report = discussions_run(manifest, workspace, state_dir=state_dir)
    assert report["totals"]["needs_attention_count"] == 0


def test_discussions_records_fetch_errors(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup(tmp_path)
    fetched = {"error": "gh: command not found", "nodes": []}
    with patch(
        "aicg.discussions.fetch_discussions", return_value=fetched
    ):
        report = discussions_run(manifest, workspace, state_dir=state_dir)
    assert any(repo.get("fetch_error") for repo in report["repos"])
    assert report["totals"]["repos_with_errors"] >= 1


def test_discussions_report_written(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup(tmp_path)
    with patch(
        "aicg.discussions.fetch_discussions", return_value={"nodes": []}
    ):
        discussions_run(manifest, workspace, state_dir=state_dir)
    assert (state_dir / "discussions-report.json").exists()


def test_discussions_config_defaults(tmp_path: Path) -> None:
    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    config = DiscussionsConfig.from_manifest(manifest)
    assert config.stale_after_days == 7
    assert "Q&A" in config.flag_categories


def test_discussions_skips_missing_repo_directory(tmp_path: Path) -> None:
    _, state_dir, manifest = _setup(tmp_path)
    empty_workspace = tmp_path / "empty"
    empty_workspace.mkdir()
    with patch(
        "aicg.discussions.fetch_discussions", return_value={"nodes": []}
    ) as mock_fetch:
        discussions_run(manifest, empty_workspace, state_dir=state_dir)
    # All repos missing → fetch should never be called.
    mock_fetch.assert_not_called()
