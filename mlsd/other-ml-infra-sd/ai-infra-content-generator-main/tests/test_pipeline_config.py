"""Tests for the staged-rollout pipeline config (defaults OFF / inert)."""

from types import SimpleNamespace

from aicg.pipeline_config import PipelineConfig


def test_defaults_are_all_off_inert() -> None:
    cfg = PipelineConfig.from_manifest(SimpleNamespace())  # no pipeline block
    assert cfg.author_enabled is False
    assert cfg.reaudit_autofix is False
    assert cfg.research_autopromote is False
    assert cfg.retire_enabled is False
    assert cfg.package_enabled is False
    assert cfg.enabled_phases() == []


def test_phases_read_from_manifest() -> None:
    manifest = SimpleNamespace(
        pipeline={
            "phases": {"author": True, "reaudit_autofix": True},
            "daily_budget": 12,
            "rotation_days": 60,
        }
    )
    cfg = PipelineConfig.from_manifest(manifest)
    assert cfg.author_enabled is True
    assert cfg.reaudit_autofix is True
    assert cfg.retire_enabled is False  # not enabled -> stays off
    assert cfg.daily_budget == 12
    assert cfg.rotation_days == 60
    assert "author(P1)" in cfg.enabled_phases()
    assert "retire(P4)" not in cfg.enabled_phases()


def test_typed_subconfigs() -> None:
    cfg = PipelineConfig.from_manifest(SimpleNamespace(pipeline={"daily_budget": 10}))
    assert cfg.budget().total == 10
    assert cfg.eval_gate(bar=80).bar == 80
    assert cfg.promotion().add_threshold == 3
    assert cfg.retire().retire_quarters == 2
