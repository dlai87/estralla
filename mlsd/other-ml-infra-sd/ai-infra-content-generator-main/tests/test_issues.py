from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import write_minimal_manifest

from aicg.issues import IssuesError, issues_run
from aicg.org_config import load_manifest


def _setup_workspace(tmp_path: Path) -> tuple[Path, Path, "OrgManifest"]:
    workspace = tmp_path / "workspace"
    (workspace / "ai-infra-security-learning").mkdir(parents=True)
    (workspace / "ai-infra-security-solutions").mkdir(parents=True)
    (workspace / ".github").mkdir(parents=True)
    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    return workspace, tmp_path / "state", manifest


def _write_queue(
    state_dir: Path,
    items: list[dict],
    workspace: Path | None = None,
) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": "2026-05-27T00:00:00Z",
        "operation": "weekly_audit",
        "workspace": str(workspace or state_dir.parent),
        "work_item_count": len(items),
        "repo_reports": [],
        "work_items": items,
    }
    queue_path = state_dir / "work-queue.json"
    queue_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return queue_path


def test_issues_dry_run_decides_to_open_for_failed_permanently(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:fill-mod-001",
                "repo": "ai-infra-security-solutions",
                "work_id": "fill-mod-001",
                "status": "failed_permanently",
                "module": "mod-001",
                "type": "module_solution_gap",
                "retry_count": 3,
                "last_failure": "broken",
                "updated_at": "2026-05-27T00:00:00Z",
            }
        ],
    )
    with patch("aicg.issues.list_aicg_open_issues", return_value=[]), patch(
        "aicg.issues.open_issue"
    ) as mock_open:
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=False)

    mock_open.assert_not_called()
    repo_report = report["repos"][0]
    assert repo_report["decision_count"] == 1
    assert repo_report["decisions"][0]["action"] == "open"
    assert report["status"] == "dry_run"


def test_issues_apply_opens_issue_for_failed_permanently(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:fill-mod-001",
                "repo": "ai-infra-security-solutions",
                "work_id": "fill-mod-001",
                "status": "failed_permanently",
                "module": "mod-001",
                "type": "module_solution_gap",
                "retry_count": 3,
                "last_failure": "broken",
                "updated_at": "2026-05-27T00:00:00Z",
            }
        ],
    )
    with patch("aicg.issues.list_aicg_open_issues", return_value=[]), patch(
        "aicg.issues.open_issue"
    ) as mock_open, patch("aicg.issues.comment_issue") as mock_comment, patch(
        "aicg.issues.close_issue"
    ) as mock_close:
        mock_open.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_open.assert_called_once()
    mock_comment.assert_not_called()
    mock_close.assert_not_called()
    assert report["repos"][0]["opened"] == 1


def test_issues_apply_closes_existing_issue_on_verified(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:fill-mod-001",
                "repo": "ai-infra-security-solutions",
                "work_id": "fill-mod-001",
                "status": "verified",
                "module": "mod-001",
                "type": "module_solution_gap",
            }
        ],
    )
    existing_issue = {
        "number": 42,
        "title": "[aicg] failed: mod-001 (fill-mod-001)",
        "body": "Auto-tracked by the AICG runner.\n\n- `work_id`: `fill-mod-001`\n",
        "labels": [{"name": "aicg"}],
        "updatedAt": "2026-05-26T00:00:00Z",
    }
    with patch("aicg.issues.list_aicg_open_issues", return_value=[existing_issue]), patch(
        "aicg.issues.open_issue"
    ) as mock_open, patch("aicg.issues.close_issue") as mock_close, patch(
        "aicg.issues.comment_issue"
    ) as mock_comment:
        mock_close.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_open.assert_not_called()
    mock_comment.assert_not_called()
    mock_close.assert_called_once()
    args, kwargs = mock_close.call_args
    assert args[1] == 42
    assert report["repos"][0]["closed"] == 1


def test_issues_comments_on_existing_issue_for_failed_permanently(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:fill-mod-001",
                "repo": "ai-infra-security-solutions",
                "work_id": "fill-mod-001",
                "status": "failed_permanently",
                "module": "mod-001",
                "type": "module_solution_gap",
                "retry_count": 4,
                "updated_at": "2026-05-27T00:00:00Z",
            }
        ],
    )
    existing_issue = {
        "number": 17,
        "title": "[aicg] failed: mod-001 (fill-mod-001)",
        "body": "Auto-tracked.\n\n- `work_id`: `fill-mod-001`\n",
        "labels": [{"name": "aicg"}],
        "updatedAt": "2026-05-26T00:00:00Z",
    }
    with patch("aicg.issues.list_aicg_open_issues", return_value=[existing_issue]), patch(
        "aicg.issues.comment_issue"
    ) as mock_comment, patch("aicg.issues.open_issue") as mock_open:
        mock_comment.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=True)

    mock_comment.assert_called_once()
    args, kwargs = mock_comment.call_args
    assert args[1] == 17
    mock_open.assert_not_called()
    assert report["repos"][0]["commented"] == 1


def test_issues_opens_for_long_deferred_items(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    stuck_timestamp = (
        datetime.now(timezone.utc) - timedelta(hours=48)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:stuck-item",
                "repo": "ai-infra-security-solutions",
                "work_id": "stuck-item",
                "status": "deferred",
                "module": "mod-001",
                "type": "module_solution_gap",
                "defer_reason": "opaque_generator_failure",
                "updated_at": stuck_timestamp,
            }
        ],
    )
    with patch("aicg.issues.list_aicg_open_issues", return_value=[]):
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=False)
    decisions = report["repos"][0]["decisions"]
    assert decisions[0]["action"] == "open"
    assert "Deferred for over" in decisions[0]["reason"]


def test_issues_skips_recently_deferred_items(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    recent_timestamp = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")
    _write_queue(
        state_dir,
        [
            {
                "id": "ai-infra-security-solutions:recent-item",
                "repo": "ai-infra-security-solutions",
                "work_id": "recent-item",
                "status": "deferred",
                "module": "mod-001",
                "defer_reason": "opaque_generator_failure",
                "updated_at": recent_timestamp,
            }
        ],
    )
    with patch("aicg.issues.list_aicg_open_issues", return_value=[]):
        report = issues_run(manifest, workspace, state_dir=state_dir, apply=False)
    decisions = report["repos"][0]["decisions"]
    assert decisions[0]["action"] == "skip"


def test_issues_raises_when_queue_missing(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    with pytest.raises(IssuesError):
        issues_run(manifest, workspace, state_dir=state_dir, apply=False)


def test_issues_report_written_to_state_dir(tmp_path: Path) -> None:
    workspace, state_dir, manifest = _setup_workspace(tmp_path)
    _write_queue(state_dir, [])
    with patch("aicg.issues.list_aicg_open_issues", return_value=[]):
        issues_run(manifest, workspace, state_dir=state_dir, apply=False)
    assert (state_dir / "issues-report.json").exists()
