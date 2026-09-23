"""Tests for role title aliases (research synonyms)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from aicg.org_config import RoleConfig, default_manifest_path, load_manifest
from aicg.org_runner import build_research_prompt


def _manifest_with(role: RoleConfig):
    """Reuse the real manifest shape, swapping in just the test role.

    Loading the on-disk manifest keeps the test resilient to new
    OrgManifest fields instead of hand-constructing every one.
    """
    base = load_manifest(default_manifest_path())
    return dataclasses.replace(base, roles=(role,))


def test_roleconfig_aliases_default_empty() -> None:
    role = RoleConfig(
        id="x", title="X", level=10, learning_repo="l", solution_repo="s"
    )
    assert role.aliases == ()


def test_research_prompt_lists_aliases_when_present() -> None:
    role = RoleConfig(
        id="agentic-ai-developer",
        title="Agentic AI Developer",
        level=20,
        learning_repo="ai-infra-agentic-ai-developer-learning",
        solution_repo="ai-infra-agentic-ai-developer-solutions",
        aliases=("AI Engineer", "LLM Application Developer"),
    )
    prompt = build_research_prompt(_manifest_with(role), role, "2026-07")
    assert "AI Engineer" in prompt
    assert "LLM Application Developer" in prompt
    assert "count their postings toward the evidence threshold" in prompt


def test_research_prompt_no_alias_line_when_empty() -> None:
    role = RoleConfig(
        id="engineer",
        title="AI Infrastructure Engineer",
        level=20,
        learning_repo="ai-infra-engineer-learning",
        solution_repo="ai-infra-engineer-solutions",
    )
    prompt = build_research_prompt(_manifest_with(role), role, "2026-07")
    assert "count their postings toward the evidence threshold" not in prompt
