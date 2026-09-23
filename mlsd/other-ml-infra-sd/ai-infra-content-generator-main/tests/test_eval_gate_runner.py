"""Tests for the eval-gate production adapter (panel + critic over the real judge)."""

from pathlib import Path

from aicg.eval_gate import EvalGateConfig
from aicg.eval_gate_runner import gate_existing_artifact, panel_median
from aicg.judge import JudgeConfig, JudgeVerdict


def _cfg() -> JudgeConfig:
    return JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": 76, "freshness": 76},
        timeout_seconds=None,
    )


def _verdict(score: int, blockers=()) -> JudgeVerdict:
    return JudgeVerdict(
        score=score, dimensions={}, blockers=list(blockers), summary="", passed=score >= 76,
        threshold=76, raw="",
    )


def test_panel_median_of_three_calls(tmp_path: Path) -> None:
    art = tmp_path / "a.md"
    art.write_text("x", encoding="utf-8")
    scores = iter([90, 30, 88])  # one outlier

    def judge(**kw):
        return _verdict(next(scores))

    med = panel_median(
        judge=judge, repo_path=tmp_path, artifact_path=art, artifact_id="a",
        config=_cfg(), panel_size=3,
    )
    assert med == 88  # outlier 30 ignored


def test_gate_passes_fresh_artifact_without_regen(tmp_path: Path) -> None:
    art = tmp_path / "a.md"
    art.write_text("current content", encoding="utf-8")
    regen_calls = {"n": 0}

    def judge(**kw):
        return _verdict(95)  # well above BAR=76

    out = gate_existing_artifact(
        repo_path=tmp_path, artifact_path=art, artifact_id="a",
        judge_config=_cfg(), gate_config=EvalGateConfig(panel_size=3, bar=76, max_revise=3),
        regenerate=lambda issues: regen_calls.__setitem__("n", regen_calls["n"] + 1),
        judge=judge,
    )
    assert out.status == "merged"
    assert out.rounds == 1
    assert regen_calls["n"] == 0  # fresh content needs no regeneration


def test_gate_regenerates_then_passes(tmp_path: Path) -> None:
    art = tmp_path / "a.md"
    art.write_text("stale content", encoding="utf-8")
    state = {"fixed": False}

    def regenerate(issues):
        art.write_text("fixed content", encoding="utf-8")
        state["fixed"] = True

    def judge(**kw):
        return _verdict(95 if state["fixed"] else 40)  # low until regenerated

    out = gate_existing_artifact(
        repo_path=tmp_path, artifact_path=art, artifact_id="a",
        judge_config=_cfg(), gate_config=EvalGateConfig(panel_size=1, bar=76, max_revise=3),
        regenerate=regenerate, judge=judge,
    )
    assert out.status == "merged"
    assert out.rounds == 2
    assert art.read_text() == "fixed content"


def test_gate_quarantines_persistent_blocker(tmp_path: Path) -> None:
    art = tmp_path / "a.md"
    art.write_text("broken", encoding="utf-8")

    def judge(**kw):
        return _verdict(95, blockers=["dead link"])  # high score but a hard blocker

    out = gate_existing_artifact(
        repo_path=tmp_path, artifact_path=art, artifact_id="a",
        judge_config=_cfg(), gate_config=EvalGateConfig(panel_size=1, bar=76, max_revise=2),
        regenerate=lambda issues: None, judge=judge,
    )
    assert out.status == "quarantined"
    assert "dead link" in out.blockers
