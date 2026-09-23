"""Regression tests for the research-proposal PR openers.

Covers the three bugs found on the 2026-06-01 monthly research cycle:

1. ``gh pr create --label foo`` hard-fails when ``foo`` doesn't exist
   in the target repo, losing all expensive agent work
2. Residue from prior agent invocations leaves the tree dirty, which
   blocks ``git checkout -B`` and warns on ``gh pr create``
3. Stderr was empty for ``rc=1`` failures — actually unrelated to the
   PR openers but verified here that stash failures are tolerated.

The fix: stash residue → checkout/add/commit/push/pr_create (no
``--label`` flags) → best-effort ``gh pr edit --add-label`` per label.

These tests use the same subprocess-runner shim as
``test_discussions_index.py`` so they exercise real argv construction
without hitting git/gh.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

from aicg.org_config import RoleConfig
from aicg.research import _open_proposal_pr, _open_proposal_pr_v2


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _record_runner(script: list[subprocess.CompletedProcess]):
    """Subprocess shim. Returns canned responses in order; records calls."""
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(list(argv))
        if not script:
            return _completed()
        return script.pop(0)

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


def _role(**overrides: Any) -> RoleConfig:
    """Build a RoleConfig with the minimal fields the PR openers touch."""
    import dataclasses

    defaults: dict[str, Any] = {
        "id": "junior-engineer",
        "title": "Junior",
        "level": 1,
        "learning_repo": "ai-infra-junior-engineer-learning",
    }
    # Fill in any other required RoleConfig fields with neutral defaults
    # so this helper survives schema additions.
    for field in dataclasses.fields(RoleConfig):
        if field.name in defaults or field.name in overrides:
            continue
        if field.default is not dataclasses.MISSING:
            continue
        if field.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            continue
        # Required field with no default — give it a benign value.
        defaults[field.name] = ""
    defaults.update(overrides)
    return RoleConfig(**defaults)


# ---------- legacy _open_proposal_pr ----------


def test_legacy_pr_create_does_not_pass_label_flags(tmp_path: Path) -> None:
    """The pr_create argv must NOT contain --label (Bug 1)."""
    runner = _record_runner(
        [
            _completed(),  # stash_residue (nothing to stash → returncode 0 here for simplicity)
            _completed(),  # checkout
            _completed(),  # add
            _completed(),  # commit
            _completed(),  # push
            _completed(stdout="https://github.com/.../pull/123\n"),  # pr_create
            _completed(),  # add_label aicg
            _completed(),  # add_label aicg:plan-proposal
            _completed(),  # restore main
        ]
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr(
            tmp_path, _role(), "2026-06", proposal_paths=["RESEARCH_PROPOSAL_2026-06.md"]
        )
    # Find the gh pr create argv.
    pr_create_argv = next(
        c for c in runner.calls if c[:3] == ["gh", "pr", "create"]
    )
    assert "--label" not in pr_create_argv


def test_legacy_pr_add_labels_called_after_create(tmp_path: Path) -> None:
    """`gh pr edit --add-label` runs once per label after a successful PR."""
    runner = _record_runner(
        [_completed() for _ in range(5)]  # stash, checkout, add, commit, push
        + [_completed(stdout="https://github.com/.../pull/1\n")]  # pr_create OK
        + [_completed() for _ in range(3)]  # add_label x2 + restore main
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr(
            tmp_path, _role(), "2026-06", proposal_paths=["x.md"]
        )
    add_label_calls = [c for c in runner.calls if "--add-label" in c]
    assert len(add_label_calls) == 2
    # Each call carries exactly one label.
    flat = [c[c.index("--add-label") + 1] for c in add_label_calls]
    assert sorted(flat) == ["aicg", "aicg:plan-proposal"]


def test_legacy_add_label_failure_does_not_break_flow(tmp_path: Path) -> None:
    """A missing label on the repo logs but does NOT cause the run to fail."""
    runner = _record_runner(
        [_completed() for _ in range(5)]
        + [_completed(stdout="https://github.com/.../pull/1\n")]  # pr_create
        + [
            _completed(returncode=1, stderr="label not found"),  # add_label aicg
            _completed(returncode=1, stderr="label not found"),  # add_label aicg:plan-proposal
            _completed(),  # restore main
        ]
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        report = _open_proposal_pr(
            tmp_path, _role(), "2026-06", proposal_paths=["x.md"]
        )
    # The flow completed (we restored main at the end) and the report
    # includes the failed add_label steps with their non-zero rc.
    step_names = [s["step"] for s in report["steps"]]
    assert "add_label:aicg" in step_names
    assert "add_label:aicg:plan-proposal" in step_names


def test_legacy_stashes_residue_before_checkout(tmp_path: Path) -> None:
    """`git stash push --include-untracked` runs before `git checkout -B`."""
    runner = _record_runner(
        [_completed() for _ in range(9)]  # plenty of slots
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr(tmp_path, _role(), "2026-06", proposal_paths=["x.md"])
    stash_idx = next(
        i for i, c in enumerate(runner.calls) if "stash" in c
    )
    checkout_idx = next(
        i for i, c in enumerate(runner.calls) if "checkout" in c and "-B" in c
    )
    assert stash_idx < checkout_idx
    # The stash command includes --include-untracked.
    assert "--include-untracked" in runner.calls[stash_idx]


def test_legacy_stash_failure_is_not_fatal(tmp_path: Path) -> None:
    """`git stash push` returns non-zero when there's nothing to stash — fine."""
    runner = _record_runner(
        [
            _completed(returncode=1, stderr="No local changes to save"),
            _completed(),  # checkout
            _completed(),  # add
            _completed(),  # commit
            _completed(),  # push
            _completed(stdout="https://...\n"),  # pr_create
            _completed(),  # add_label
            _completed(),  # add_label
            _completed(),  # restore main
        ]
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        report = _open_proposal_pr(
            tmp_path, _role(), "2026-06", proposal_paths=["x.md"]
        )
    # Stash returned non-zero but we proceeded all the way through pr_create.
    pr_create_outcome = next(s for s in report["steps"] if s["step"] == "pr_create")
    assert pr_create_outcome["returncode"] == 0


# ---------- v2 _open_proposal_pr_v2 ----------


def test_v2_pr_create_does_not_pass_label_flags(tmp_path: Path) -> None:
    runner = _record_runner(
        [_completed() for _ in range(5)]  # stash, checkout, add, commit, push
        + [_completed(stdout="https://...\n")]  # pr_create
        + [_completed(), _completed()]  # add_label x2
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr_v2(
            learning_path=tmp_path,
            role=_role(),
            month="2026-06",
            proposal_paths=["RESEARCH_PROPOSAL_2026-06.md"],
            labels=["curriculum-plan-v2", "requires-explicit-approval"],
        )
    pr_create_argv = next(
        c for c in runner.calls if c[:3] == ["gh", "pr", "create"]
    )
    assert "--label" not in pr_create_argv


def test_v2_pr_add_labels_called_after_create(tmp_path: Path) -> None:
    runner = _record_runner(
        [_completed() for _ in range(5)]
        + [_completed(stdout="https://...\n")]  # pr_create
        + [_completed(), _completed()]
    )
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr_v2(
            learning_path=tmp_path,
            role=_role(),
            month="2026-06",
            proposal_paths=["x.md"],
            labels=["curriculum-plan-v2", "requires-explicit-approval"],
        )
    add_label_calls = [c for c in runner.calls if "--add-label" in c]
    flat = [c[c.index("--add-label") + 1] for c in add_label_calls]
    assert sorted(flat) == ["curriculum-plan-v2", "requires-explicit-approval"]


def test_v2_stashes_residue_before_checkout(tmp_path: Path) -> None:
    runner = _record_runner([_completed() for _ in range(9)])
    with patch("aicg.research.subprocess.run", side_effect=runner):
        _open_proposal_pr_v2(
            learning_path=tmp_path,
            role=_role(),
            month="2026-06",
            proposal_paths=["x.md"],
            labels=[],
        )
    stash_idx = next(i for i, c in enumerate(runner.calls) if "stash" in c)
    checkout_idx = next(
        i for i, c in enumerate(runner.calls) if "checkout" in c and "-B" in c
    )
    assert stash_idx < checkout_idx
