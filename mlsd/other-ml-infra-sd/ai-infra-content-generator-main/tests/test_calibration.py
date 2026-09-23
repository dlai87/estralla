"""Tests for the eval-gate calibration harness (P0).

The harness runs the freshness judge over a hand-labeled corpus of
known-good and known-bad artifacts and reports how well the judge's
score separates the two — so BAR can be chosen empirically rather than
guessed. The real judge is stubbed here; calibration logic is what's
under test, not the LLM.
"""

from pathlib import Path

from aicg.calibration import run_calibration
from aicg.judge import JudgeConfig, JudgeVerdict


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _corpus(tmp_path: Path, good: list[str], bad: list[str]) -> Path:
    corpus = tmp_path / "corpus"
    for i, body in enumerate(good):
        write_file(corpus / "good" / f"good-{i}.md", body)
    for i, body in enumerate(bad):
        write_file(corpus / "bad" / f"bad-{i}.md", body)
    return corpus


def _config(threshold: int = 75) -> JudgeConfig:
    return JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": threshold, "freshness": threshold},
        timeout_seconds=None,
    )


def _scoring_judge(score_by_label):
    """Return a fake judge that scores by the artifact's label dir."""

    def judge(*, repo_path, artifact_path, artifact_id, config, runner_root=None):
        label = "good" if "/good/" in artifact_path.as_posix() else "bad"
        score = score_by_label[label]
        threshold = config.freshness_threshold()
        return JudgeVerdict(
            score=score,
            dimensions={},
            blockers=[],
            summary=f"{label}:{score}",
            passed=score >= threshold,
            threshold=threshold,
            raw="",
        )

    return judge


def test_calibration_reports_clean_separation(tmp_path: Path) -> None:
    corpus = _corpus(tmp_path, good=["a", "b", "c"], bad=["x", "y"])
    report = run_calibration(
        corpus,
        judge_config=_config(threshold=75),
        artifact_judge=_scoring_judge({"good": 90, "bad": 30}),
    )
    assert len(report.rows) == 5
    # good passes, bad fails at threshold 75 → perfect confusion
    assert report.true_pass == 3 and report.false_fail == 0
    assert report.true_fail == 2 and report.false_pass == 0
    assert report.separable is True
    # suggested BAR sits strictly between the two clusters
    assert 30 < report.suggested_bar <= 90


def test_calibration_recommends_higher_bar_when_current_lets_bad_through(tmp_path: Path) -> None:
    # good=95, bad=80, current threshold=75 → bad PASSES (false_pass) even
    # though the clusters are cleanly separable. Calibration's job is to
    # surface that the current BAR is too low and recommend one (80,95].
    corpus = _corpus(tmp_path, good=["a"], bad=["x", "y"])
    report = run_calibration(
        corpus,
        judge_config=_config(threshold=75),
        artifact_judge=_scoring_judge({"good": 95, "bad": 80}),
    )
    assert report.false_pass == 2  # both bad artifacts slipped through at BAR=75
    assert report.separable is True  # min(good)=95 > max(bad)=80
    assert 80 < report.suggested_bar <= 95  # a bar that would have caught them


def test_calibration_non_separable_picks_best_sweep(tmp_path: Path) -> None:
    # overlapping clusters: no threshold separates them perfectly
    corpus = tmp_path / "corpus"
    write_file(corpus / "good" / "g0.md", "a")
    write_file(corpus / "good" / "g1.md", "b")
    write_file(corpus / "bad" / "b0.md", "x")
    write_file(corpus / "bad" / "b1.md", "y")

    def judge(*, repo_path, artifact_path, artifact_id, config, runner_root=None):
        name = artifact_path.name
        score = {"g0.md": 80, "g1.md": 40, "b0.md": 60, "b1.md": 20}[name]
        t = config.freshness_threshold()
        return JudgeVerdict(score, {}, [], name, score >= t, t, "")

    report = run_calibration(corpus, judge_config=_config(), artifact_judge=judge)
    assert report.separable is False
    assert report.suggested_bar is not None  # best-effort sweep value


def test_calibration_raises_on_empty_corpus(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    (corpus / "good").mkdir(parents=True)
    (corpus / "bad").mkdir(parents=True)
    import pytest

    with pytest.raises(ValueError):
        run_calibration(
            corpus, judge_config=_config(), artifact_judge=_scoring_judge({"good": 90, "bad": 10})
        )


def test_calibration_aborts_on_rate_limit(tmp_path: Path) -> None:
    # A rate-limited judge returns a bogus 0 with a limit message in `raw`;
    # calibration must refuse to derive a BAR from it.
    import pytest

    from aicg.calibration import CalibrationLimitError

    corpus = _corpus(tmp_path, good=["a"], bad=["x"])

    def limited_judge(*, repo_path, artifact_path, artifact_id, config, runner_root=None):
        return JudgeVerdict(
            score=0,
            dimensions={},
            blockers=[],
            summary="",
            passed=False,
            threshold=config.freshness_threshold(),
            raw="You've hit your session limit · resets 6:20pm (America/Phoenix)",
        )

    with pytest.raises(CalibrationLimitError):
        run_calibration(corpus, judge_config=_config(), artifact_judge=limited_judge)
