from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from conftest import write_minimal_manifest

from aicg.org_config import load_manifest
from aicg.steward import (
    classify_rollup,
    evaluate_pr_guardrails,
    steward_run,
)


def _success_check(name: str) -> dict:
    return {"name": name, "status": "COMPLETED", "conclusion": "SUCCESS"}


def _failure_check(name: str) -> dict:
    return {"name": name, "status": "COMPLETED", "conclusion": "FAILURE"}


def _pending_check(name: str) -> dict:
    return {"name": name, "status": "IN_PROGRESS", "conclusion": None}


def _commit_status(state: str) -> dict:
    return {"context": "ci/legacy", "state": state.upper()}


# ---------------------------------------------------------------------------
# classify_rollup
# ---------------------------------------------------------------------------


def test_rollup_all_success_is_success() -> None:
    assert classify_rollup([_success_check("ci")]) == "success"


def test_rollup_one_failure_is_failure() -> None:
    rollup = [_success_check("ci"), _failure_check("lint")]
    assert classify_rollup(rollup) == "failure"


def test_rollup_pending_with_success_is_pending() -> None:
    rollup = [_success_check("ci"), _pending_check("e2e")]
    assert classify_rollup(rollup) == "pending"


def test_rollup_skipped_treated_as_success_when_others_pass() -> None:
    rollup = [
        _success_check("ci"),
        {"name": "skip", "status": "COMPLETED", "conclusion": "SKIPPED"},
    ]
    assert classify_rollup(rollup) == "success"


def test_rollup_empty_is_pending() -> None:
    assert classify_rollup([]) == "pending"


def test_rollup_handles_commit_status_shape() -> None:
    assert classify_rollup([_commit_status("success")]) == "success"
    assert classify_rollup([_commit_status("pending")]) == "pending"
    assert classify_rollup([_commit_status("failure")]) == "failure"


# ---------------------------------------------------------------------------
# evaluate_pr_guardrails
# ---------------------------------------------------------------------------


def test_pr_guardrails_block_drafts(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={
            "isDraft": True,
            "headRefName": "aicg/feature",
            "files": [],
            "labels": [],
        },
    )
    assert not decision.allowed
    assert any("draft" in b.lower() for b in decision.blockers)


def test_pr_guardrails_block_do_not_merge_label(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={
            "isDraft": False,
            "headRefName": "aicg/feature",
            "files": [],
            "labels": [{"name": "do-not-merge"}],
        },
    )
    assert not decision.allowed
    assert any("do-not-merge" in b for b in decision.blockers)


def test_pr_guardrails_block_restricted_file(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={
            "isDraft": False,
            "headRefName": "aicg/feature",
            "files": [{"path": ".github/workflows/ci.yml"}],
            "labels": [],
        },
    )
    assert not decision.allowed
    assert any("restricted" in b.lower() for b in decision.blockers)


def test_pr_guardrails_block_main_head_ref(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={"isDraft": False, "headRefName": "main", "files": [], "labels": []},
    )
    assert not decision.allowed


def test_pr_guardrails_block_conflicting_mergeable(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={
            "isDraft": False,
            "headRefName": "aicg/feature",
            "files": [],
            "labels": [],
            "mergeable": "CONFLICTING",
        },
    )
    assert not decision.allowed
    assert any("conflict" in b.lower() for b in decision.blockers)


def test_pr_guardrails_allow_clean_pr(tmp_path: Path) -> None:
    decision = evaluate_pr_guardrails(
        repo_path=tmp_path,
        pr={
            "isDraft": False,
            "headRefName": "aicg/feature",
            "files": [{"path": "modules/mod-001/exercise-01/SOLUTION.md"}],
            "labels": [],
            "mergeable": "MERGEABLE",
        },
    )
    assert decision.allowed
    assert decision.blockers == ()


# ---------------------------------------------------------------------------
# steward_run end-to-end with mocked gh calls
# ---------------------------------------------------------------------------


def _setup_workspace(tmp_path: Path) -> tuple[Path, Path, "OrgManifest"]:
    workspace = tmp_path / "workspace"
    learning = workspace / "ai-infra-security-learning"
    solutions = workspace / "ai-infra-security-solutions"
    learning.mkdir(parents=True)
    solutions.mkdir(parents=True)
    (workspace / ".github").mkdir(parents=True)
    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    return workspace, tmp_path / "state", manifest


def test_steward_dry_run_reports_would_merge(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)

    # ai-infra-security-solutions has an open PR with green CI.
    open_prs = {
        "ai-infra-security-learning": [],
        "ai-infra-security-solutions": [
            {
                "number": 7,
                "title": "Fill mod-001 solutions",
                "headRefName": "aicg/2026-05-27/security-solutions/fill-mod-001",
                "isDraft": False,
                "labels": [],
            }
        ],
        ".github": [],
    }
    pr_views = {
        7: {
            "number": 7,
            "title": "Fill mod-001 solutions",
            "headRefName": "aicg/2026-05-27/security-solutions/fill-mod-001",
            "isDraft": False,
            "labels": [],
            "files": [{"path": "modules/mod-001/exercise-01/SOLUTION.md"}],
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [_success_check("ci")],
        }
    }

    with patch("aicg.steward.list_open_prs") as mock_list, patch(
        "aicg.steward.pr_view"
    ) as mock_view:
        mock_list.side_effect = lambda repo_path: open_prs.get(repo_path.name, [])
        mock_view.side_effect = lambda repo_path, number: pr_views[number]
        report = steward_run(manifest, workspace, state_dir=state_dir, apply=False)

    assert report["status"] == "dry_run"
    solutions_report = next(r for r in report["repos"] if r["repo"].endswith("solutions"))
    assert solutions_report["pr_count"] == 1
    assert solutions_report["prs"][0]["state"] == "would_merge"


def test_steward_apply_invokes_gh_pr_merge(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    pr_views = {
        7: {
            "number": 7,
            "title": "Fill mod-001",
            "headRefName": "aicg/2026-05-27/security/fill-mod-001",
            "isDraft": False,
            "labels": [],
            "files": [{"path": "modules/mod-001/exercise-01/SOLUTION.md"}],
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [_success_check("ci")],
        }
    }

    with patch("aicg.steward.list_open_prs") as mock_list, patch(
        "aicg.steward.pr_view"
    ) as mock_view, patch("aicg.steward.enable_auto_merge") as mock_merge, patch(
        "aicg.steward.pr_state", return_value="MERGED"
    ):
        mock_list.side_effect = lambda repo_path: (
            [
                {
                    "number": 7,
                    "title": "Fill mod-001",
                    "headRefName": "aicg/feature",
                    "isDraft": False,
                    "labels": [],
                }
            ]
            if repo_path.name == "ai-infra-security-solutions"
            else []
        )
        mock_view.side_effect = lambda repo_path, number: pr_views[number]
        mock_merge.return_value = {
            "command": "gh pr merge 7 --auto --squash --delete-branch",
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }
        report = steward_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_merge.assert_called_once()
    solutions_report = next(r for r in report["repos"] if r["repo"].endswith("solutions"))
    assert solutions_report["merged_count"] == 1
    assert solutions_report["prs"][0]["state"] == "merged"


def test_steward_blocks_when_ci_fails(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    pr_view_data = {
        "number": 7,
        "headRefName": "aicg/feature",
        "isDraft": False,
        "labels": [],
        "files": [],
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [_failure_check("lint")],
    }

    with patch("aicg.steward.list_open_prs") as mock_list, patch(
        "aicg.steward.pr_view", return_value=pr_view_data
    ), patch("aicg.steward.enable_auto_merge") as mock_merge:
        mock_list.side_effect = lambda repo_path: (
            [{"number": 7, "headRefName": "aicg/feature", "isDraft": False, "labels": []}]
            if repo_path.name == "ai-infra-security-solutions"
            else []
        )
        report = steward_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_merge.assert_not_called()
    solutions_report = next(r for r in report["repos"] if r["repo"].endswith("solutions"))
    assert solutions_report["ci_failed_count"] == 1
    assert solutions_report["prs"][0]["state"] == "ci_failed"


def test_steward_blocks_restricted_file_changes(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    pr_view_data = {
        "number": 7,
        "headRefName": "aicg/feature",
        "isDraft": False,
        "labels": [],
        "files": [{"path": ".github/workflows/ci.yml"}],
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [_success_check("ci")],
    }

    with patch("aicg.steward.list_open_prs") as mock_list, patch(
        "aicg.steward.pr_view", return_value=pr_view_data
    ), patch("aicg.steward.enable_auto_merge") as mock_merge:
        mock_list.side_effect = lambda repo_path: (
            [{"number": 7, "headRefName": "aicg/feature", "isDraft": False, "labels": []}]
            if repo_path.name == "ai-infra-security-solutions"
            else []
        )
        report = steward_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_merge.assert_not_called()
    solutions_report = next(r for r in report["repos"] if r["repo"].endswith("solutions"))
    assert solutions_report["blocked_count"] == 1


def test_steward_state_file_written(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    with patch("aicg.steward.list_open_prs", return_value=[]):
        steward_run(manifest, workspace, state_dir=state_dir, apply=False)
    report_path = state_dir / "steward-report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text())
    assert payload["operation"] == "steward"
    assert payload["status"] == "dry_run"


# ---------------------------------------------------------------------------
# CI-absent short-circuit (wait_for_ci)
# ---------------------------------------------------------------------------


def test_wait_for_ci_short_circuits_when_no_rollup_after_grace(tmp_path: Path) -> None:
    from aicg.steward import wait_for_ci

    # pr_view returns empty rollup forever — simulates a repo with no CI.
    with patch("aicg.steward.pr_view", return_value={"statusCheckRollup": []}):
        result = wait_for_ci(
            repo_path=tmp_path,
            pr_number=1,
            timeout_seconds=120,
            poll_seconds=0,           # don't sleep in the test
            ci_absent_grace_seconds=0,  # short-circuit immediately
        )
    assert result["status"] == "no_ci_present"


def test_wait_for_ci_returns_success_when_rollup_passes(tmp_path: Path) -> None:
    from aicg.steward import wait_for_ci

    rollup = [{"status": "COMPLETED", "conclusion": "SUCCESS"}]
    with patch(
        "aicg.steward.pr_view", return_value={"statusCheckRollup": rollup}
    ):
        result = wait_for_ci(
            repo_path=tmp_path,
            pr_number=1,
            timeout_seconds=10,
            poll_seconds=0,
        )
    assert result["status"] == "success"


def test_wait_for_ci_returns_failure_on_failed_check(tmp_path: Path) -> None:
    from aicg.steward import wait_for_ci

    rollup = [{"status": "COMPLETED", "conclusion": "FAILURE"}]
    with patch(
        "aicg.steward.pr_view", return_value={"statusCheckRollup": rollup}
    ):
        result = wait_for_ci(
            repo_path=tmp_path,
            pr_number=1,
            timeout_seconds=10,
            poll_seconds=0,
        )
    assert result["status"] == "failure"
