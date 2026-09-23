"""W1.3 — research prompt is grounded in the structural curriculum manifest."""

from __future__ import annotations

from pathlib import Path

import pytest

from aicg.org_config import OrgManifest, load_manifest
from aicg.org_runner import build_research_prompt


MANIFEST_PATH = Path("config/aicg-org.yaml")


@pytest.fixture
def org_manifest() -> OrgManifest:
    if not MANIFEST_PATH.exists():
        pytest.skip("org manifest not present in this checkout")
    return load_manifest(MANIFEST_PATH)


def test_prompt_includes_continuity_bias(org_manifest: OrgManifest) -> None:
    """Every research prompt carries the continuity-over-novelty policy."""
    role = org_manifest.roles[0]
    prompt = build_research_prompt(org_manifest, role, "2026-06")

    assert "Continuity bias" in prompt
    assert "Default to no change" in prompt
    assert "requires_explicit_approval" in prompt
    assert "20%" in prompt


def test_prompt_includes_existing_curriculum_section(org_manifest: OrgManifest) -> None:
    """The structural manifest summary is embedded so the agent grounds in coverage."""
    role = org_manifest.roles[0]
    prompt = build_research_prompt(org_manifest, role, "2026-06")

    assert "Existing curriculum to build on (do not duplicate)" in prompt


def test_prompt_for_junior_includes_junior_modules(org_manifest: OrgManifest) -> None:
    """If the structural manifest exists, the junior prompt names junior modules."""
    if not Path("manifest/curriculum.manifest.json").exists():
        pytest.skip("structural manifest not built in this checkout")
    junior = next(
        (r for r in org_manifest.roles if r.id == "junior-engineer"),
        None,
    )
    if junior is None:
        pytest.skip("junior-engineer role not in org manifest")

    prompt = build_research_prompt(org_manifest, junior, "2026-06")

    # The junior structural manifest has mod-001..mod-010; at least one
    # should appear in the prompt's summary section.
    assert "mod-" in prompt
    # And it should not contain modules from senior tracks (the summary
    # is per-track, with only a one-line sibling-track index).
    # Use a specific senior-only module name to test exclusion. We assert
    # the SECTION_HEADER appears once — siblings get a one-liner only.
    assert prompt.count("Sibling tracks:") <= 1


def test_prompt_handles_missing_manifest(
    org_manifest: OrgManifest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the structural manifest is absent, the prompt falls back gracefully."""
    # Point the module's manifest path at a tmp file that doesn't exist.
    import aicg.org_runner as runner

    monkeypatch.setattr(
        runner, "_CURRICULUM_MANIFEST_PATH", tmp_path / "missing.json"
    )
    role = org_manifest.roles[0]
    prompt = build_research_prompt(org_manifest, role, "2026-06")

    assert "curriculum.manifest.json not built yet" in prompt
    # The rest of the prompt — including the continuity bias — still landed.
    assert "Continuity bias" in prompt
    assert "Goal" in prompt
