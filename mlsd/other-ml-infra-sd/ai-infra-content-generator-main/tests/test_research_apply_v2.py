"""W2.2b — research_apply emits + validates the new v2 delta format for canary roles."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aicg.curriculum_plan import write_curriculum_plan
from aicg.org_config import OrgManifest, load_manifest
from aicg.org_runner import build_research_prompt
from aicg.research import (
    CANARY_ROLES_NEW_FORMAT,
    CURRICULUM_PLAN_DELTA_V2_FILE,
    _handle_new_format_role,
)


ORG_MANIFEST_PATH = Path("config/aicg-org.yaml")
JUNIOR_BASELINE_PATH = Path("manifest/curriculum_plan.junior-engineer.manifest.json")


@pytest.fixture
def org_manifest() -> OrgManifest:
    if not ORG_MANIFEST_PATH.exists():
        pytest.skip("org manifest not in this checkout")
    return load_manifest(ORG_MANIFEST_PATH)


@pytest.fixture
def junior_role(org_manifest: OrgManifest):
    role = next((r for r in org_manifest.roles if r.id == "junior-engineer"), None)
    if role is None:
        pytest.skip("junior-engineer role not in org manifest")
    return role


# ---------- prompt routing ----------


def test_canary_set_contains_junior() -> None:
    assert "junior-engineer" in CANARY_ROLES_NEW_FORMAT


def test_junior_prompt_emits_v2_output_contract(org_manifest, junior_role) -> None:
    prompt = build_research_prompt(org_manifest, junior_role, "2026-06")
    assert "curriculum-plan v2" in prompt
    assert ".aicg/curriculum-plan-delta-v2.json" in prompt
    assert "additions" in prompt and "updates" in prompt and "removals" in prompt
    # Legacy schema's required `modules` / `exercises` / `projects` top-level
    # keys should NOT appear in v2 contract (avoid agent confusion).
    assert '"modules":' not in prompt
    assert "Existing curriculum to build on" in prompt
    assert "Continuity bias" in prompt


def test_non_canary_prompt_still_uses_legacy(org_manifest) -> None:
    # Pick any non-canary role.
    role = next(
        (r for r in org_manifest.roles if r.id not in CANARY_ROLES_NEW_FORMAT),
        None,
    )
    if role is None:
        pytest.skip("no non-canary role in org manifest")
    prompt = build_research_prompt(org_manifest, role, "2026-06")
    assert "curriculum-plan v2" not in prompt
    assert ".aicg/curriculum-plan-delta.json" in prompt


# ---------- handler ----------


def _make_canary_workspace(
    tmp_path: Path, role_id: str
) -> tuple[Path, Path, Path]:
    """Build a tmp workspace that mimics the runner_root + learning_path layout."""
    runner_root = tmp_path / "content-generator"
    (runner_root / "manifest").mkdir(parents=True)
    workspace = tmp_path / "workspace"
    learning_path = workspace / f"ai-infra-{role_id}-learning"
    (learning_path / ".aicg").mkdir(parents=True)
    return runner_root, workspace, learning_path


def _write_baseline_with(
    runner_root: Path, role_id: str, requirements: list[dict] | None = None
) -> Path:
    """Create a minimal per-role baseline so the handler can validate against it."""
    path = runner_root / f"manifest/curriculum_plan.{role_id}.manifest.json"
    payload = {
        "schema_version": 1,
        "role": role_id,
        "role_title": role_id,
        "research": {
            "window_start": None,
            "window_end": None,
            "postings_sampled": 0,
            "last_refreshed": None,
            "sources": [],
        },
        "requirements": requirements
        or [
            {
                "id": "REQ-JR-EXISTING-1",
                "label": "Existing 1",
                "frequency": 0.4,
                "provenance": "backfilled",
                "requires_confirmation": True,
                "evidence": [],
                "discussion_topics": [],
                "exercises": [],
                "projects": [],
                "solutions": [],
                "tests": [],
                "coverage_status": "partial",
                "notes": "",
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_v2_delta(learning_path: Path, payload: dict) -> Path:
    path = learning_path / CURRICULUM_PLAN_DELTA_V2_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _fake_role(role_id: str):
    """Minimal duck-typed role for the handler — only .id and .title are touched."""

    class _R:
        id = role_id
        title = role_id

    return _R()


def test_handler_returns_applied_no_delta_when_v2_file_missing(tmp_path: Path) -> None:
    runner_root, _ws, learning_path = _make_canary_workspace(tmp_path, "junior-engineer")
    _write_baseline_with(runner_root, "junior-engineer")
    report = _handle_new_format_role(
        role=_fake_role("junior-engineer"),
        learning_path=learning_path,
        runner_root=runner_root,
        month="2026-06",
        open_pr=False,
        outputs={"delta_present": False},
    )
    assert report["status"] == "applied_no_delta"
    assert report["format"] == "v2"


def test_handler_reports_baseline_missing(tmp_path: Path) -> None:
    runner_root, _ws, learning_path = _make_canary_workspace(tmp_path, "junior-engineer")
    # NO baseline written.
    _write_v2_delta(
        learning_path,
        {
            "schema_version": 1,
            "role": "junior-engineer",
            "month": "2026-06",
            "rationale": "x",
        },
    )
    report = _handle_new_format_role(
        role=_fake_role("junior-engineer"),
        learning_path=learning_path,
        runner_root=runner_root,
        month="2026-06",
        open_pr=False,
        outputs={"delta_present": True},
    )
    assert report["status"] == "baseline_missing"


def test_handler_reports_proposal_ready_for_empty_delta(tmp_path: Path) -> None:
    """Empty delta = steady-state = proposal_ready with no requires_approval."""
    runner_root, _ws, learning_path = _make_canary_workspace(tmp_path, "junior-engineer")
    _write_baseline_with(runner_root, "junior-engineer")
    _write_v2_delta(
        learning_path,
        {
            "schema_version": 1,
            "role": "junior-engineer",
            "month": "2026-06",
            "rationale": "market unchanged this cycle",
        },
    )
    report = _handle_new_format_role(
        role=_fake_role("junior-engineer"),
        learning_path=learning_path,
        runner_root=runner_root,
        month="2026-06",
        open_pr=False,
        outputs={"delta_present": True},
    )
    assert report["status"] == "proposal_ready"
    assert report["validation"]["requires_explicit_approval"] is False
    assert report["validation"]["additions"] == 0
    # Proposal markdown should have been written.
    assert len(report["proposal_files"]) == 1
    md = Path(report["proposal_files"][0]).read_text(encoding="utf-8")
    assert "Research Proposal" in md
    assert "Continuity check" in md


def test_handler_reports_delta_rejected_for_underqualified_addition(
    tmp_path: Path,
) -> None:
    """An addition with < 3 evidence items is rejected by the validator."""
    runner_root, _ws, learning_path = _make_canary_workspace(tmp_path, "junior-engineer")
    _write_baseline_with(runner_root, "junior-engineer")
    _write_v2_delta(
        learning_path,
        {
            "schema_version": 1,
            "role": "junior-engineer",
            "month": "2026-06",
            "rationale": "weak addition",
            "additions": [
                {
                    "rationale": "x",
                    "requirement": {
                        "id": "REQ-JR-NEW",
                        "label": "new",
                        "frequency": 0.45,
                        "provenance": "research",
                        "requires_confirmation": False,
                        "evidence": [{"posting_id": "p1", "phrase": "only one"}],
                        "exercises": [],
                        "projects": [],
                        "solutions": [],
                        "tests": [],
                        "coverage_status": "missing",
                    },
                }
            ],
        },
    )
    report = _handle_new_format_role(
        role=_fake_role("junior-engineer"),
        learning_path=learning_path,
        runner_root=runner_root,
        month="2026-06",
        open_pr=False,
        outputs={"delta_present": True},
    )
    assert report["status"] == "delta_rejected"
    assert "evidence" in report["error"].lower()


def test_handler_flags_explicit_approval_for_oversize_delta(tmp_path: Path) -> None:
    """Additions > 20% of baseline auto-flag requires_explicit_approval."""
    runner_root, _ws, learning_path = _make_canary_workspace(tmp_path, "junior-engineer")
    # Baseline with 10 requirements — adding 3 = 30% > 20% threshold.
    _write_baseline_with(
        runner_root,
        "junior-engineer",
        requirements=[
            {
                "id": f"REQ-JR-X-{i}",
                "label": f"x{i}",
                "frequency": 0.4,
                "provenance": "backfilled",
                "requires_confirmation": True,
                "evidence": [],
                "discussion_topics": [],
                "exercises": [],
                "projects": [],
                "solutions": [],
                "tests": [],
                "coverage_status": "partial",
                "notes": "",
            }
            for i in range(10)
        ],
    )
    additions = [
        {
            "rationale": "ok",
            "requirement": {
                "id": f"REQ-JR-NEW-{i}",
                "label": f"new{i}",
                "frequency": 0.40,
                "provenance": "research",
                "requires_confirmation": False,
                "evidence": [
                    {"posting_id": f"p{j}", "phrase": "e"} for j in range(3)
                ],
                "exercises": [],
                "projects": [],
                "solutions": [],
                "tests": [],
                "coverage_status": "missing",
            },
        }
        for i in range(3)
    ]
    _write_v2_delta(
        learning_path,
        {
            "schema_version": 1,
            "role": "junior-engineer",
            "month": "2026-06",
            "rationale": "burst of new tooling appeared in postings",
            "additions": additions,
        },
    )
    report = _handle_new_format_role(
        role=_fake_role("junior-engineer"),
        learning_path=learning_path,
        runner_root=runner_root,
        month="2026-06",
        open_pr=False,
        outputs={"delta_present": True},
    )
    assert report["status"] == "proposal_ready"
    assert report["validation"]["requires_explicit_approval"] is True
    assert any("additions" in n for n in report["validation"]["notes"])
    md = Path(report["proposal_files"][0]).read_text(encoding="utf-8")
    assert "Requires explicit approval" in md
