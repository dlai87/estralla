"""Flag-only review mode (P0).

Flag-only is the safe first activation of the quality judge: it scores
live content and reports what is stale, but enqueues NO repair work item
(no autonomous regeneration). It is how the judge earns trust before any
auto-fix is enabled (design doc P0; review item S9/U-M5).
"""

from pathlib import Path
from types import SimpleNamespace

from aicg.freshness import review_existing_artifacts
from aicg.judge import JudgeConfig, JudgeVerdict


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _stale_judge(**kwargs):
    return JudgeVerdict(
        score=40,
        dimensions={"api_currency": 10},
        blockers=["References PyTorch 1.10"],
        summary="Stale",
        passed=False,
        threshold=75,
        raw="",
    )


def test_judgeconfig_reads_flag_only_from_manifest() -> None:
    on = JudgeConfig.from_manifest(
        SimpleNamespace(quality_judge={"enabled": True, "flag_only": True})
    )
    off = JudgeConfig.from_manifest(SimpleNamespace(quality_judge={"enabled": True}))
    assert on.flag_only is True
    assert off.flag_only is False  # defaults off — acting is opt-in's opposite


def test_flag_only_records_stale_but_emits_no_work_item(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/SOLUTION.md", "Use PyTorch 1.10\n")
    config = JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": 75, "freshness": 75},
        timeout_seconds=None,
        flag_only=True,
    )
    report = review_existing_artifacts(repo, judge_config=config, artifact_judge=_stale_judge)
    # Detected and reported as stale ...
    assert report["stale_count"] == 1
    assert report["findings"][0]["status"] == "stale"
    assert report["findings"][0]["score"] == 40
    # ... but NO repair action enqueued.
    assert report["work_items"] == []


def test_non_flag_only_still_emits_work_item(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/SOLUTION.md", "Use PyTorch 1.10\n")
    config = JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": 75, "freshness": 75},
        timeout_seconds=None,
        flag_only=False,
    )
    report = review_existing_artifacts(repo, judge_config=config, artifact_judge=_stale_judge)
    assert report["stale_count"] == 1
    assert len(report["work_items"]) == 1
    assert report["work_items"][0]["type"] == "refresh_stale"
