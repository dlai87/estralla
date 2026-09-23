from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from conftest import write_minimal_manifest

from aicg.dependabot import (
    MAX_REBASE_REQUESTS,
    _process_dependabot_pr,
    dependabot_run,
)
from aicg.org_config import load_manifest


def _setup_workspace(tmp_path: Path) -> tuple[Path, Path, "OrgManifest"]:
    workspace = tmp_path / "workspace"
    (workspace / "ai-infra-security-learning").mkdir(parents=True)
    (workspace / "ai-infra-security-solutions").mkdir(parents=True)
    (workspace / ".github").mkdir(parents=True)
    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    return workspace, tmp_path / "state", manifest


# ---------------------------------------------------------------------------
# Single-PR classification
# ---------------------------------------------------------------------------


def test_clean_dependabot_pr_routes_to_auto_merge(tmp_path: Path) -> None:
    pr = {
        "number": 13,
        "title": "ci(deps): bump hashicorp/setup-terraform from 3 to 4",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
    }
    with patch("aicg.dependabot._enable_auto_merge") as mock_merge:
        mock_merge.return_value = {"status": "merged"}
        outcome = _process_dependabot_pr(
            repo_path=tmp_path, repo="repo-x", pr=pr, prior={}, apply=True
        )
    assert outcome["action"] == "auto_merge"
    assert outcome["status"] == "merged"
    mock_merge.assert_called_once_with(tmp_path, 13)


def test_unstable_dependabot_pr_still_queues_auto_merge(tmp_path: Path) -> None:
    pr = {
        "number": 12,
        "title": "ci(deps): bump x",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "UNSTABLE",
    }
    with patch("aicg.dependabot._enable_auto_merge") as mock_merge:
        mock_merge.return_value = {"status": "auto_merge_enabled"}
        outcome = _process_dependabot_pr(
            repo_path=tmp_path, repo="repo-x", pr=pr, prior={}, apply=True
        )
    assert outcome["action"] == "auto_merge"
    assert outcome["status"] == "auto_merge_enabled"


def test_conflicting_pr_requests_rebase_first_time(tmp_path: Path) -> None:
    pr = {
        "number": 11,
        "title": "bump",
        "mergeable": "CONFLICTING",
        "mergeStateStatus": "DIRTY",
    }
    with patch("aicg.dependabot._post_rebase_comment") as mock_comment, patch(
        "aicg.dependabot._enable_auto_merge"
    ) as mock_merge:
        mock_comment.return_value = {"returncode": 0, "stdout_tail": "", "stderr_tail": ""}
        mock_merge.return_value = {"status": "auto_merge_enabled"}
        outcome = _process_dependabot_pr(
            repo_path=tmp_path, repo="repo-x", pr=pr, prior={}, apply=True
        )
    assert outcome["action"] == "rebase_requested"
    assert outcome["status"] == "rebase_pending"
    assert outcome["rebase_request_count"] == 1
    mock_comment.assert_called_once()


def test_conflicting_pr_escalates_after_cap(tmp_path: Path) -> None:
    pr = {
        "number": 10,
        "title": "bump",
        "mergeable": "CONFLICTING",
        "mergeStateStatus": "DIRTY",
    }
    prior = {"rebase_request_count": MAX_REBASE_REQUESTS}
    with patch("aicg.dependabot._post_rebase_comment") as mock_comment:
        outcome = _process_dependabot_pr(
            repo_path=tmp_path, repo="repo-x", pr=pr, prior=prior, apply=True
        )
    assert outcome["status"] == "escalated"
    assert outcome["action"] == "no_action"
    mock_comment.assert_not_called()


def test_dry_run_does_not_call_gh(tmp_path: Path) -> None:
    pr = {
        "number": 9,
        "title": "bump",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
    }
    with patch("aicg.dependabot._enable_auto_merge") as mock_merge:
        outcome = _process_dependabot_pr(
            repo_path=tmp_path, repo="repo-x", pr=pr, prior={}, apply=False
        )
    assert outcome["status"] == "would_merge"
    mock_merge.assert_not_called()


# ---------------------------------------------------------------------------
# Full sweep with retry persistence
# ---------------------------------------------------------------------------


def test_dependabot_run_writes_report_and_state(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    state_dir.mkdir(parents=True)
    pr_fixture = [
        {
            "number": 5,
            "title": "ci(deps): bump foo",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        }
    ]
    with patch("aicg.dependabot.list_dependabot_prs") as mock_list, patch(
        "aicg.dependabot._enable_auto_merge"
    ) as mock_merge:
        mock_list.side_effect = lambda p: pr_fixture if "security-solutions" in str(p) else []
        mock_merge.return_value = {"status": "merged"}
        report = dependabot_run(
            manifest, workspace, state_dir=state_dir, apply=True
        )

    assert report["status"] == "applied"
    state_path = state_dir / "dependabot-state.json"
    assert state_path.exists()
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert "ai-infra-security-solutions#5" in persisted["prs"]


def test_dependabot_run_persists_rebase_count_across_runs(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    state_dir.mkdir(parents=True)
    pr_fixture = [
        {
            "number": 7,
            "title": "ci(deps): bump bar",
            "mergeable": "CONFLICTING",
            "mergeStateStatus": "DIRTY",
        }
    ]

    def fake_list(p: Path) -> list:
        return pr_fixture if "security-solutions" in str(p) else []

    with patch("aicg.dependabot.list_dependabot_prs", side_effect=fake_list), patch(
        "aicg.dependabot._post_rebase_comment", return_value={"returncode": 0, "stdout_tail": "", "stderr_tail": ""}
    ), patch("aicg.dependabot._enable_auto_merge", return_value={"status": "auto_merge_enabled"}):
        first = dependabot_run(manifest, workspace, state_dir=state_dir, apply=True)
        second = dependabot_run(manifest, workspace, state_dir=state_dir, apply=True)

    persisted = json.loads(
        (state_dir / "dependabot-state.json").read_text(encoding="utf-8")
    )
    # First run: count went 0 → 1. Second run: 1 → 2.
    assert persisted["prs"]["ai-infra-security-solutions#7"]["rebase_request_count"] == 2
