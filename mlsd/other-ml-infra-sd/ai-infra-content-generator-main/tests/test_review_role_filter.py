"""Per-role review filter (Option A nightly review timers).

These tests prove:

1. ``aicg org review --role <slug>`` walks BOTH the learning and
   solution repos for that role (not just solutions) — the legacy
   behavior left learner-facing lecture notes and exercise prompts
   un-judged, which is precisely the content where stale citations
   and deprecated APIs mislead learners most.
2. Other roles' repos are NOT walked when --role is set, so a
   nightly timer running ``review-role <slug>`` consumes one role's
   token budget, not the whole org's.
3. ``--role`` rejects unknown ids fast (a typo in a systemd timer
   name fails immediately instead of silently no-op'ing forever).
4. The legacy unfiltered call walks both learning and solution repos
   for every role (a strict correctness improvement over the prior
   solutions-only behavior).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import write_file

from aicg.cli import main


_MIN_MANIFEST_TWO_ROLES = {
    "org": "AI-Infra-Curriculum",
    "default_remote": "git@github.com:AI-Infra-Curriculum/{repo}.git",
    "release": {"tag_format": "v%Y.%m", "branch": "main"},
    "extra_repos": [],
    "documentation": {
        "format_guard_files": ["README.md"],
        "org_readme_repo": ".github",
        "org_readme_files": ["README.md"],
    },
    "schedules": {},
    "automation": {
        "state_dir": ".aicg/org",
        "agent": {
            "provider": "openai",
            "model": "codex-gpt-5.5",
            "interface": "local_cli_subscription",
            "agent_command": "/bin/true",
        },
    },
    "content_generation": {
        "agent": {
            "provider": "anthropic",
            "model": "claude-opus-4-7",
            "interface": "local_cli_subscription",
            "agent_command": "/bin/true",
        }
    },
    "job_requirements": {
        "ownership_strategy": "lowest_level_role",
        "markdown_file": "JOB_REQUIREMENTS.md",
        "structured_file": ".aicg/job-requirements.json",
        "supplemental_dir": "supplemental",
    },
    "research": {"minimum_postings_per_role": 25, "source_window_days": 45},
    "maintained_by": {
        "name": "VeriSwarm.ai",
        "url": "https://veriswarm.ai",
        "phrasing": "Maintained by VeriSwarm.ai",
        "footer_marker": "<!-- aicg:maintained-by -->",
    },
    # quality_judge intentionally disabled — the filter test doesn't
    # need the judge to do anything; it only needs to verify which
    # repos got walked. Each walked artifact is marked "skipped" with
    # zero token cost, which is enough to assert traversal.
    "quality_judge": {"enabled": False, "thresholds": {"default": 70}},
    "roles": [
        {
            "id": "junior-engineer",
            "title": "Junior",
            "level": 10,
            "learning_repo": "ai-infra-junior-engineer-learning",
            "solution_repo": "ai-infra-junior-engineer-solutions",
        },
        {
            "id": "engineer",
            "title": "Engineer",
            "level": 20,
            "learning_repo": "ai-infra-engineer-learning",
            "solution_repo": "ai-infra-engineer-solutions",
        },
    ],
}


def _seed_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Create both roles' learning + solutions repos, each with one
    reviewable artifact under the freshness globs. Returns (workspace,
    manifest_path)."""
    workspace = tmp_path / "workspace"
    for role in ("junior-engineer", "engineer"):
        write_file(
            workspace / f"ai-infra-{role}-learning" / "lessons" / "mod-001" / "README.md",
            f"# {role} learning\n",
        )
        write_file(
            workspace / f"ai-infra-{role}-solutions" / "modules" / "mod-001" / "SOLUTION.md",
            f"# {role} solution\n",
        )
    manifest = tmp_path / "aicg-org.yaml"
    manifest.write_text(json.dumps(_MIN_MANIFEST_TWO_ROLES, indent=2) + "\n", encoding="utf-8")
    return workspace, manifest


def _review_report_dirs(workspace: Path) -> set[str]:
    """Return the set of repo names that have a freshness-review-report.json
    written into their .aicg/ directory."""
    found: set[str] = set()
    for repo_dir in workspace.iterdir():
        if not repo_dir.is_dir():
            continue
        if (repo_dir / ".aicg" / "freshness-review-report.json").exists():
            found.add(repo_dir.name)
    return found


def test_review_role_walks_both_learning_and_solutions(tmp_path: Path) -> None:
    """--role <slug> hits BOTH that role's learning + solutions repos."""
    workspace, manifest = _seed_workspace(tmp_path)

    rc = main(
        [
            "org",
            "review",
            "--workspace",
            str(workspace),
            "--manifest",
            str(manifest),
            "--state-dir",
            str(tmp_path / "state"),
            "--role",
            "junior-engineer",
        ]
    )
    assert rc == 0
    walked = _review_report_dirs(workspace)
    assert "ai-infra-junior-engineer-learning" in walked
    assert "ai-infra-junior-engineer-solutions" in walked


def test_review_role_does_not_touch_other_roles(tmp_path: Path) -> None:
    """--role junior-engineer must NOT walk engineer's repos."""
    workspace, manifest = _seed_workspace(tmp_path)

    main(
        [
            "org",
            "review",
            "--workspace",
            str(workspace),
            "--manifest",
            str(manifest),
            "--state-dir",
            str(tmp_path / "state"),
            "--role",
            "junior-engineer",
        ]
    )
    walked = _review_report_dirs(workspace)
    assert "ai-infra-engineer-learning" not in walked
    assert "ai-infra-engineer-solutions" not in walked


def test_review_role_unknown_role_fails_fast(tmp_path: Path, capsys) -> None:
    """A typo in the slug must surface as a CLI error, not a silent no-op."""
    workspace, manifest = _seed_workspace(tmp_path)

    rc = main(
        [
            "org",
            "review",
            "--workspace",
            str(workspace),
            "--manifest",
            str(manifest),
            "--state-dir",
            str(tmp_path / "state"),
            "--role",
            "nope",
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "Unknown role 'nope'" in err
    # No reports written for unknown role.
    assert _review_report_dirs(workspace) == set()


def test_review_unfiltered_walks_both_kinds_for_every_role(tmp_path: Path) -> None:
    """Omitting --role covers learning AND solutions for every role.

    The legacy behavior walked solution repos only, leaving learner-
    facing lecture notes / exercise prompts un-judged. Verify the fix.
    """
    workspace, manifest = _seed_workspace(tmp_path)

    rc = main(
        [
            "org",
            "review",
            "--workspace",
            str(workspace),
            "--manifest",
            str(manifest),
            "--state-dir",
            str(tmp_path / "state"),
        ]
    )
    assert rc == 0
    walked = _review_report_dirs(workspace)
    assert walked == {
        "ai-infra-junior-engineer-learning",
        "ai-infra-junior-engineer-solutions",
        "ai-infra-engineer-learning",
        "ai-infra-engineer-solutions",
    }


def test_review_role_writes_role_scoped_report(tmp_path: Path) -> None:
    """Per-role runs land in freshness-review-report.<slug>.json so
    adjacent nightly timers don't clobber each other."""
    workspace, manifest = _seed_workspace(tmp_path)
    state_dir = tmp_path / "state"

    main(
        [
            "org",
            "review",
            "--workspace",
            str(workspace),
            "--manifest",
            str(manifest),
            "--state-dir",
            str(state_dir),
            "--role",
            "junior-engineer",
        ]
    )
    role_scoped = state_dir / "freshness-review-report.junior-engineer.json"
    assert role_scoped.exists()
    payload = json.loads(role_scoped.read_text(encoding="utf-8"))
    assert payload["role"] == "junior-engineer"
    # The unscoped name belongs to the legacy unfiltered path; not
    # written when --role is set.
    assert not (state_dir / "freshness-review-report.json").exists()
