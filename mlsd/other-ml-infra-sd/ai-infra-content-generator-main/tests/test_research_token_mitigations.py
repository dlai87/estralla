"""Regression tests for Bug 4 mitigations.

- Brief-mode prompts: non-canary roles get slug-only summaries
- Canary roles still get the full hierarchy (they consume it)
- _pending_proposal_pr: branch-prefix detection works for both opener formats
- research_apply skips a role when an open proposal PR exists
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from aicg.manifest import (
    CurriculumManifest,
    Module,
    Track,
    summarize_manifest_for_prompt,
    summarize_track_for_prompt,
)
from aicg.org_config import RoleConfig, load_manifest
from aicg.org_runner import build_research_prompt
from aicg.org_runner import generate_research_packets
from aicg.research import (
    CANARY_ROLES_NEW_FORMAT,
    _OPEN_PR_BRANCH_PREFIXES,
    ResearchError,
    _pending_proposal_pr,
    research_apply,
)


def _completed(returncode: int = 0, stdout: str = "[]", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


# ---------- brief-mode summaries ----------


def test_summarize_track_brief_is_much_shorter_than_full() -> None:
    """Brief mode should be at least 50% smaller than full mode."""
    track = Track(
        slug="junior-engineer",
        display_name="Junior",
        level=1,
        learning_repo="x",
        solutions_repo="y",
        learning_repo_url="https://x",
        solutions_repo_url="https://y",
        modules=tuple(
            Module(
                slug=f"mod-{i:03d}-thing",
                number=i,
                title=f"Module {i}: Something Long",
                path=f"lessons/mod-{i:03d}",
                github_url="https://x",
                exercises=tuple(),
                prerequisites=(),
                related=(),
            )
            for i in range(1, 11)
        ),
        projects=tuple(),
        resources=tuple(),
    )
    full = summarize_track_for_prompt(track)
    brief = summarize_track_for_prompt(track, brief=True)
    assert len(brief) < len(full) * 0.6
    # Brief still names every module slug — just compactly.
    for i in range(1, 11):
        assert f"mod-{i:03d}-thing" in brief


def test_summarize_manifest_brief_omits_sibling_index() -> None:
    """Brief mode skips the sibling-tracks index too (pure noise for non-canary)."""
    # Use a minimal synthetic manifest.
    track = Track(
        slug="x",
        display_name="X",
        level=1,
        learning_repo="r",
        solutions_repo="s",
        learning_repo_url="",
        solutions_repo_url="",
        modules=tuple(),
        projects=tuple(),
        resources=tuple(),
    )
    manifest = CurriculumManifest(
        schema_version=1,
        generated_at="now",
        org="ai-infra-curriculum",
        tracks=(track,),
    )
    brief = summarize_manifest_for_prompt(
        manifest, only_track_slug="x", brief=True
    )
    full = summarize_manifest_for_prompt(manifest, only_track_slug="x")
    assert "Sibling tracks" not in brief
    # Full mode would emit a sibling index if there were other tracks,
    # but with only one track it just omits the line. Both forms have
    # the role's header.
    assert "X" in brief and "X" in full


# ---------- routing through build_research_prompt ----------


@pytest.fixture
def org_manifest():
    p = Path("config/aicg-org.yaml")
    if not p.exists():
        pytest.skip("org manifest not in this checkout")
    return load_manifest(p)


def test_non_canary_prompt_uses_brief_existing_curriculum(org_manifest) -> None:
    """A non-canary role's prompt should be SMALLER than the canary's prompt."""
    canary_id = next(iter(CANARY_ROLES_NEW_FORMAT))
    canary_role = next((r for r in org_manifest.roles if r.id == canary_id), None)
    non_canary_role = next(
        (r for r in org_manifest.roles if r.id not in CANARY_ROLES_NEW_FORMAT), None
    )
    if canary_role is None or non_canary_role is None:
        pytest.skip("manifest does not have a canary and non-canary role")

    canary_prompt = build_research_prompt(org_manifest, canary_role, "2026-06")
    non_canary_prompt = build_research_prompt(org_manifest, non_canary_role, "2026-06")
    # Canary prompt embeds the full hierarchy + larger v2 output contract.
    # Non-canary should be smaller.
    assert len(non_canary_prompt) < len(canary_prompt)
    # Non-canary prompt's existing-curriculum section uses the brief
    # intro: "These already exist — do NOT propose duplicates."
    assert "do NOT propose duplicates" in non_canary_prompt
    # Canary's section uses the longer intro:
    assert "Treat every module / exercise / project" in canary_prompt


# ---------- _pending_proposal_pr ----------


def _role(role_id: str = "junior-engineer") -> RoleConfig:
    import dataclasses

    defaults: dict[str, Any] = {
        "id": role_id,
        "title": role_id,
        "level": 1,
        "learning_repo": f"ai-infra-{role_id}-learning",
    }
    for field in dataclasses.fields(RoleConfig):
        if field.name in defaults:
            continue
        if field.default is not dataclasses.MISSING:
            continue
        if field.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            continue
        defaults[field.name] = ""
    return RoleConfig(**defaults)


def test_pending_pr_detects_aicg_research_branch() -> None:
    rows = [
        {
            "url": "https://github.com/ai-infra-curriculum/x/pull/42",
            "headRefName": "aicg/research/2026-06/junior-engineer",
            "updatedAt": "2026-06-01T00:00:00Z",
        }
    ]
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout=json.dumps(rows)),
    ):
        url = _pending_proposal_pr(_role())
    assert url == "https://github.com/ai-infra-curriculum/x/pull/42"


def test_pending_pr_detects_v2_research_branch() -> None:
    rows = [
        {
            "url": "https://github.com/x/y/pull/7",
            "headRefName": "research/2026-06/junior-engineer",
            "updatedAt": "2026-06-02T00:00:00Z",
        }
    ]
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout=json.dumps(rows)),
    ):
        url = _pending_proposal_pr(_role())
    assert url == "https://github.com/x/y/pull/7"


def test_pending_pr_ignores_other_role_branches() -> None:
    """A PR for a different role must not block this role."""
    rows = [
        {
            "url": "https://x/1",
            "headRefName": "aicg/research/2026-06/senior-engineer",
            "updatedAt": "2026-06-01T00:00:00Z",
        }
    ]
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout=json.dumps(rows)),
    ):
        url = _pending_proposal_pr(_role("junior-engineer"))
    assert url is None


def test_pending_pr_ignores_non_research_branches() -> None:
    """Random feature branches must not count as pending review."""
    rows = [
        {
            "url": "https://x/2",
            "headRefName": "feat/some-thing",
            "updatedAt": "2026-06-01T00:00:00Z",
        }
    ]
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout=json.dumps(rows)),
    ):
        url = _pending_proposal_pr(_role())
    assert url is None


def test_pending_pr_picks_most_recently_updated() -> None:
    rows = [
        {
            "url": "https://old",
            "headRefName": "aicg/research/2026-04/junior-engineer",
            "updatedAt": "2026-04-15T00:00:00Z",
        },
        {
            "url": "https://newer",
            "headRefName": "aicg/research/2026-06/junior-engineer",
            "updatedAt": "2026-06-01T00:00:00Z",
        },
    ]
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout=json.dumps(rows)),
    ):
        url = _pending_proposal_pr(_role())
    assert url == "https://newer"


def test_pending_pr_gh_failure_returns_none() -> None:
    """gh failure must not block the cycle — return None and let agent run."""
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(returncode=1, stderr="auth required"),
    ):
        url = _pending_proposal_pr(_role())
    assert url is None


def test_pending_pr_no_open_prs_returns_none() -> None:
    with patch(
        "aicg.research.subprocess.run",
        return_value=_completed(stdout="[]"),
    ):
        url = _pending_proposal_pr(_role())
    assert url is None


# ---------- branch prefixes constant ----------


def test_branch_prefixes_cover_both_openers() -> None:
    """The constant must include both prefix forms used by _open_proposal_pr / _v2."""
    assert "aicg/research/" in _OPEN_PR_BRANCH_PREFIXES
    assert "research/" in _OPEN_PR_BRANCH_PREFIXES


# ---------- per-role filtering (Option A: nightly per-role timers) ----------


def _multi_role_manifest_path(tmp_path: Path) -> Path:
    """A manifest with two roles, used by the role-filter regression tests.

    conftest.write_minimal_manifest only seeds one role, which can't
    distinguish "filter to one role" from "loop touched every role".
    """
    data = {
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
    path = tmp_path / "aicg-org.yaml"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def test_generate_research_packets_role_filter_writes_only_target(tmp_path: Path) -> None:
    """`generate_research_packets(role_id=...)` writes one prompt, not all."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state_dir = tmp_path / "state"
    manifest = load_manifest(_multi_role_manifest_path(tmp_path))

    report = generate_research_packets(
        manifest, workspace, month="2026-06", state_dir=state_dir, role_id="engineer"
    )
    assert len(report["packets"]) == 1
    assert report["packets"][0]["role"] == "engineer"
    # Only engineer.md is on disk; junior-engineer was filtered out.
    month_dir = state_dir / "research" / "2026-06"
    assert (month_dir / "engineer.md").exists()
    assert not (month_dir / "junior-engineer.md").exists()


def test_generate_research_packets_unknown_role_raises(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state_dir = tmp_path / "state"
    manifest = load_manifest(_multi_role_manifest_path(tmp_path))

    with pytest.raises(ValueError, match="Unknown role 'nope'"):
        generate_research_packets(
            manifest, workspace, month="2026-06", state_dir=state_dir, role_id="nope"
        )


def test_research_apply_role_filter_skips_other_roles(tmp_path: Path) -> None:
    """`research_apply(role_id=...)` only reports on the requested role."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state_dir = tmp_path / "state"
    manifest = load_manifest(_multi_role_manifest_path(tmp_path))

    # Seed prompts for BOTH roles so we know the filter — not the
    # missing-prompt branch — is what's narrowing the report.
    packet_dir = state_dir / "research" / "2026-06"
    packet_dir.mkdir(parents=True)
    (packet_dir / "junior-engineer.md").write_text("# packet\n", encoding="utf-8")
    (packet_dir / "engineer.md").write_text("# packet\n", encoding="utf-8")

    report = research_apply(
        manifest,
        workspace,
        month="2026-06",
        state_dir=state_dir,
        role_id="engineer",
        open_pr=False,
    )
    assert len(report["roles"]) == 1
    assert report["roles"][0]["role"] == "engineer"


def test_research_apply_unknown_role_raises(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state_dir = tmp_path / "state"
    manifest = load_manifest(_multi_role_manifest_path(tmp_path))
    (state_dir / "research" / "2026-06").mkdir(parents=True)

    with pytest.raises(ResearchError, match="Unknown role 'nope'"):
        research_apply(
            manifest,
            workspace,
            month="2026-06",
            state_dir=state_dir,
            role_id="nope",
            open_pr=False,
        )
