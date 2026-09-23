from __future__ import annotations

import json
from pathlib import Path

import pytest

from aicg.steward import (
    _blocker_signature,
    _build_response_queue,
    _owner_repo_from_url,
    classify_review_state,
)


def test_owner_repo_extracts_from_pr_url() -> None:
    owner, repo = _owner_repo_from_url(
        "https://github.com/AI-Infra-Curriculum/ai-infra-security-solutions/pull/42"
    )
    assert owner == "AI-Infra-Curriculum"
    assert repo == "ai-infra-security-solutions"


def test_owner_repo_returns_none_on_garbage() -> None:
    assert _owner_repo_from_url("not a url") == (None, None)
    assert _owner_repo_from_url("") == (None, None)
    assert _owner_repo_from_url("https://gitlab.com/x/y/merge_requests/1") == (None, None)


def test_classify_mergeable_when_no_blockers() -> None:
    state = {"reviews": [], "threads": []}
    assert classify_review_state(state)["verdict"] == "mergeable"


def test_classify_blocks_on_changes_requested() -> None:
    state = {
        "reviews": [
            {
                "state": "CHANGES_REQUESTED",
                "submittedAt": "2026-05-27T15:00:00Z",
                "author": {"login": "reviewer"},
                "body": "Please add tests.",
            }
        ],
        "threads": [],
    }
    result = classify_review_state(state)
    assert result["verdict"] == "blocked"
    assert any(b["kind"] == "changes_requested" for b in result["blockers"])


def test_classify_latest_review_per_author_wins() -> None:
    state = {
        "reviews": [
            {
                "state": "CHANGES_REQUESTED",
                "submittedAt": "2026-05-27T14:00:00Z",
                "author": {"login": "reviewer"},
                "body": "no",
            },
            {
                "state": "APPROVED",
                "submittedAt": "2026-05-27T15:00:00Z",
                "author": {"login": "reviewer"},
                "body": "ok",
            },
        ],
        "threads": [],
    }
    assert classify_review_state(state)["verdict"] == "mergeable"


def test_classify_blocks_on_unresolved_thread() -> None:
    state = {
        "reviews": [],
        "threads": [
            {
                "id": "T_kw1",
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "body": "Line missing handler",
                            "path": "src/x.py",
                            "line": 42,
                            "author": {"login": "human", "__typename": "User"},
                        }
                    ]
                },
            }
        ],
    }
    result = classify_review_state(state)
    assert result["verdict"] == "blocked"
    blocker = result["blockers"][0]
    assert blocker["kind"] == "unresolved_thread"
    assert blocker["is_bot"] is False
    assert blocker["path"] == "src/x.py"


def test_classify_ignores_resolved_and_outdated_threads() -> None:
    state = {
        "reviews": [],
        "threads": [
            {
                "id": "T_resolved",
                "isResolved": True,
                "isOutdated": False,
                "comments": {"nodes": [{"author": {"login": "bot"}}]},
            },
            {
                "id": "T_outdated",
                "isResolved": False,
                "isOutdated": True,
                "comments": {"nodes": [{"author": {"login": "human"}}]},
            },
        ],
    }
    assert classify_review_state(state)["verdict"] == "mergeable"


def test_classify_detects_bot_threads() -> None:
    state = {
        "reviews": [],
        "threads": [
            {
                "id": "T_bot",
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "body": "Coverage dropped 3%",
                            "path": "src/x.py",
                            "line": 1,
                            "author": {"login": "codecov[bot]", "__typename": "Bot"},
                        }
                    ]
                },
            }
        ],
    }
    result = classify_review_state(state)
    blocker = result["blockers"][0]
    assert blocker["is_bot"] is True


# ---------------------------------------------------------------------------
# Response queue + escalation
# ---------------------------------------------------------------------------


def _review_blocked_pr(pr_number: int, thread_ids: list[str]) -> dict:
    return {
        "pr_number": pr_number,
        "title": f"PR {pr_number}",
        "head_ref": f"branch-{pr_number}",
        "state": "review_blocked",
        "review_blockers": [
            {"kind": "unresolved_thread", "thread_id": tid} for tid in thread_ids
        ],
    }


def test_response_queue_resets_count_on_new_blockers(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "pr-response-queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "repo-x:respond-pr-7",
                        "blocker_signature": "t:OLD",
                        "response_count": 2,
                        "status": "ready",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    repo_reports = [
        {
            "repo": "repo-x",
            "prs": [_review_blocked_pr(7, ["NEW"])],
        }
    ]
    queue = _build_response_queue(repo_reports, state_dir)
    item = queue["items"][0]
    # New blocker_signature → count resets to 0, status stays ready.
    assert item["response_count"] == 0
    assert item["status"] == "ready"
    assert item["blocker_signature"] == _blocker_signature(
        [{"kind": "unresolved_thread", "thread_id": "NEW"}]
    )


def test_response_queue_escalates_after_max_attempts(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    sig = _blocker_signature([{"kind": "unresolved_thread", "thread_id": "T_same"}])
    (state_dir / "pr-response-queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "repo-x:respond-pr-7",
                        "blocker_signature": sig,
                        "response_count": 3,  # already at the cap
                        "status": "ready",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    repo_reports = [
        {
            "repo": "repo-x",
            "prs": [_review_blocked_pr(7, ["T_same"])],
        }
    ]
    queue = _build_response_queue(repo_reports, state_dir)
    item = queue["items"][0]
    assert item["status"] == "escalated"
    assert item["response_count"] == 3


def test_response_queue_omits_non_review_blocked_prs(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    repo_reports = [
        {
            "repo": "repo-x",
            "prs": [
                {"pr_number": 1, "state": "merged"},
                {"pr_number": 2, "state": "ci_failed"},
                _review_blocked_pr(3, ["T_x"]),
            ],
        }
    ]
    queue = _build_response_queue(repo_reports, state_dir)
    assert len(queue["items"]) == 1
    assert queue["items"][0]["pr_number"] == 3
