"""Tests for plan-driven learning content generation."""

from __future__ import annotations

import pytest

from aicg.learning_content import build_module_content_prompt


@pytest.fixture
def module() -> dict:
    return {
        "id": "mod-101-llm-fundamentals",
        "title": "LLM Fundamentals for Application Developers",
        "objectives": [
            "Call LLM APIs and reason about tokens and context windows",
            "Handle API errors, rate limits, and retries robustly",
        ],
        "exercises": [
            {"id": "exercise-01", "slug": "first-llm-api-calls"},
            {"id": "exercise-02", "slug": "tokens-context-cost"},
        ],
    }


def test_prompt_includes_objectives_and_module(module: dict) -> None:
    prompt = build_module_content_prompt(
        role_id="agentic-ai-developer",
        role_title="Agentic AI Developer",
        level=20,
        module=module,
        sibling_module_ids=["mod-101-llm-fundamentals", "mod-102-prompt-engineering"],
    )
    assert "mod-101-llm-fundamentals" in prompt
    assert "Agentic AI Developer" in prompt
    assert "Call LLM APIs and reason about tokens" in prompt


def test_prompt_lists_exercise_files_and_targets_lessons_dir(module: dict) -> None:
    prompt = build_module_content_prompt(
        role_id="agentic-ai-developer",
        role_title="Agentic AI Developer",
        level=20,
        module=module,
        sibling_module_ids=["mod-101-llm-fundamentals"],
    )
    # Targets the learning repo's lessons/<module>/ tree, not solutions.
    assert "lessons/mod-101-llm-fundamentals/" in prompt
    assert "first-llm-api-calls" in prompt
    assert "tokens-context-cost" in prompt
    # Must not author solutions.
    assert "solutions" in prompt.lower()  # mentioned only as an exclusion


def test_prompt_enforces_source_policy(module: dict) -> None:
    prompt = build_module_content_prompt(
        role_id="agentic-ai-developer",
        role_title="Agentic AI Developer",
        level=20,
        module=module,
        sibling_module_ids=["mod-101-llm-fundamentals"],
    )
    assert "needs-research" in prompt
    assert "Do NOT invent facts" in prompt


def test_prompt_excludes_sibling_modules(module: dict) -> None:
    prompt = build_module_content_prompt(
        role_id="agentic-ai-developer",
        role_title="Agentic AI Developer",
        level=20,
        module=module,
        sibling_module_ids=["mod-101-llm-fundamentals", "mod-102-prompt-engineering"],
    )
    assert "mod-102-prompt-engineering" in prompt  # named as a do-not-touch sibling
