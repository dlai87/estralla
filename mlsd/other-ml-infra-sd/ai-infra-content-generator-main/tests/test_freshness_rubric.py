"""Tests for the domain-configurable freshness rubric (roadmap §2.1).

The freshness judge's dimensions are AI/tech-shaped by default (api/version/
hardware currency). Making them configurable is the seam that turns the AI
curriculum judge into a domain-neutral one — a nursing track grades
guideline/regulation currency instead, same pipeline.
"""

from pathlib import Path
from types import SimpleNamespace

from aicg.judge import DEFAULT_FRESHNESS_DIMENSIONS, JudgeConfig, _write_freshness_prompt


def test_default_freshness_dimensions_are_the_ai_set() -> None:
    cfg = JudgeConfig.from_manifest(SimpleNamespace(quality_judge={"enabled": True}))
    names = [name for name, _ in cfg.freshness_dimensions]
    assert names == ["api_currency", "version_currency", "citation_validity", "hardware_currency"]
    assert cfg.freshness_dimensions == DEFAULT_FRESHNESS_DIMENSIONS


def test_custom_freshness_dimensions_from_manifest() -> None:
    cfg = JudgeConfig.from_manifest(
        SimpleNamespace(
            quality_judge={
                "enabled": True,
                "freshness_dimensions": [
                    {"name": "guideline_currency", "description": "outdated clinical guidelines"},
                    {"name": "regulation_currency", "description": "superseded regulations"},
                ],
            }
        )
    )
    assert cfg.freshness_dimensions == (
        ("guideline_currency", "outdated clinical guidelines"),
        ("regulation_currency", "superseded regulations"),
    )


def test_freshness_prompt_uses_configured_dimensions(tmp_path: Path) -> None:
    artifact = tmp_path / "lesson.md"
    artifact.write_text("content", encoding="utf-8")
    cfg = JudgeConfig(
        enabled=True,
        agent_command="x",
        dimensions=(),
        thresholds={"freshness": 75},
        timeout_seconds=None,
        freshness_dimensions=(
            ("guideline_currency", "outdated clinical guidelines"),
            ("regulation_currency", "superseded regulations"),
            ("citation_validity", "dead links"),
        ),
    )
    prompt_path = _write_freshness_prompt(tmp_path, artifact, "lesson", cfg)
    text = prompt_path.read_text(encoding="utf-8")
    # configured domain dimensions + their descriptions appear
    assert "guideline_currency" in text and "outdated clinical guidelines" in text
    assert "regulation_currency" in text
    # AI-specific defaults are NOT present for this domain
    assert "api_currency" not in text and "hardware_currency" not in text
    # per-dimension max scales with the count (3 dims -> 33 each, still /100 total)
    assert "0-33" in text
