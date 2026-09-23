"""Eval-gate calibration harness (P0 of the autonomous pipeline).

Runs the freshness judge over a hand-labeled corpus of known-good and
known-bad artifacts and reports how cleanly the judge's score separates
the two clusters. The point is to choose ``BAR`` (the pass threshold)
from evidence — the safety case of the autonomous pipeline rests on this
number being measured, not guessed (design doc §4.3, §5; review item C-B3).

No autonomous writes happen here: calibration only reads the corpus and
scores it. The real judge is injected via ``artifact_judge`` so the
harness is unit-testable without an LLM call.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .judge import JudgeConfig, JudgeVerdict

# A judge callable: keyword-only, matching aicg.judge.judge_artifact_freshness.
JudgeFn = Callable[..., JudgeVerdict | None]

_LABELS = ("good", "bad")


class CalibrationLimitError(RuntimeError):
    """Raised when a judge call is rate-limited during calibration.

    A rate-limited call returns a bogus 0 score; deriving BAR from that would
    produce a dangerously wrong threshold, so calibration aborts and asks for a
    retry after the limit resets.
    """


@dataclass(frozen=True)
class CalibrationRow:
    """One scored corpus artifact."""

    artifact: str  # POSIX path relative to the corpus root
    label: str  # "good" | "bad" (ground truth, from the subdir)
    score: int
    passed: bool  # judge's pass/fail at the config threshold

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "label": self.label,
            "score": self.score,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class CalibrationReport:
    """Confusion of the judge against ground-truth labels + a suggested BAR."""

    rows: tuple[CalibrationRow, ...]
    threshold: int  # the BAR used to compute the confusion below
    # Confusion: "good should pass, bad should fail."
    true_pass: int  # good & passed   (correct)
    false_fail: int  # good & failed  (over-eager: would regenerate good content)
    true_fail: int  # bad & failed    (correct: caught)
    false_pass: int  # bad & passed   (DANGEROUS: bad content slips to main)
    good_scores: tuple[int, ...]
    bad_scores: tuple[int, ...]
    separable: bool  # min(good) > max(bad): a clean threshold exists
    suggested_bar: int | None  # midpoint if separable, else best-sweep threshold

    @property
    def accuracy(self) -> float:
        total = len(self.rows)
        return (self.true_pass + self.true_fail) / total if total else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "counts": {
                "true_pass": self.true_pass,
                "false_fail": self.false_fail,
                "true_fail": self.true_fail,
                "false_pass": self.false_pass,
            },
            "accuracy": round(self.accuracy, 4),
            "good_scores": list(self.good_scores),
            "bad_scores": list(self.bad_scores),
            "separable": self.separable,
            "suggested_bar": self.suggested_bar,
            "rows": [row.as_dict() for row in self.rows],
        }


def _slug(rel: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", rel).strip("-").lower()


def _collect_labeled(corpus_dir: Path) -> list[tuple[str, Path]]:
    labeled: list[tuple[str, Path]] = []
    for label in _LABELS:
        sub = corpus_dir / label
        if not sub.is_dir():
            continue
        for path in sorted(sub.rglob("*.md")):
            labeled.append((label, path))
    return labeled


def _suggest_bar(
    good_scores: tuple[int, ...], bad_scores: tuple[int, ...], separable: bool
) -> int | None:
    if not good_scores or not bad_scores:
        return None
    if separable:
        # Clean gap: put BAR in the middle of it.
        return (max(bad_scores) + min(good_scores)) // 2
    # Overlapping clusters: sweep for the threshold that classifies the most
    # artifacts correctly (good >= t pass, bad < t fail).
    best_t, best_correct = 1, -1
    for t in range(1, 101):
        correct = sum(1 for s in good_scores if s >= t) + sum(1 for s in bad_scores if s < t)
        if correct > best_correct:
            best_correct, best_t = correct, t
    return best_t


def run_calibration(
    corpus_dir: Path | str,
    *,
    judge_config: JudgeConfig,
    artifact_judge: JudgeFn | None = None,
    runner_root: Path | None = None,
) -> CalibrationReport:
    """Score every artifact in ``corpus_dir`` and report the confusion.

    The corpus is a directory with ``good/`` and ``bad/`` subdirectories of
    ``*.md`` artifacts (nesting allowed). Each is scored by ``artifact_judge``
    (defaulting to the production freshness judge) and compared to its
    ground-truth label.

    Raises ``ValueError`` if the corpus is empty or the judge is disabled
    (returns ``None``) — calibration is meaningless without real scores.
    """
    corpus_dir = Path(corpus_dir).resolve()
    if artifact_judge is None:
        from .judge import judge_artifact_freshness

        artifact_judge = judge_artifact_freshness

    labeled = _collect_labeled(corpus_dir)
    if not labeled:
        raise ValueError(
            f"calibration corpus is empty (need good/ and bad/ *.md files): {corpus_dir}"
        )

    threshold = judge_config.freshness_threshold()
    rows: list[CalibrationRow] = []
    for label, path in labeled:
        rel = path.relative_to(corpus_dir).as_posix()
        verdict = artifact_judge(
            repo_path=corpus_dir,
            artifact_path=path,
            artifact_id=_slug(rel),
            config=judge_config,
            runner_root=runner_root,
        )
        if verdict is None:
            raise ValueError(
                "judge returned None during calibration — enable quality_judge "
                "before calibrating (a disabled judge has nothing to measure)"
            )
        # A rate-limited judge call returns a bogus 0 — refuse to derive a BAR
        # from it. A bad BAR is worse than no BAR.
        from .agent_cli import classify_limit_scope

        limit_text = f"{verdict.raw or ''}\n" + "\n".join(verdict.blockers or [])
        if classify_limit_scope(limit_text) is not None:
            raise CalibrationLimitError(
                f"judge hit a subscription/rate limit while scoring {rel}; "
                "scores are invalid — retry calibration after the limit resets"
            )
        rows.append(CalibrationRow(rel, label, verdict.score, verdict.passed))

    good_scores = tuple(r.score for r in rows if r.label == "good")
    bad_scores = tuple(r.score for r in rows if r.label == "bad")
    separable = bool(good_scores) and bool(bad_scores) and min(good_scores) > max(bad_scores)
    return CalibrationReport(
        rows=tuple(rows),
        threshold=threshold,
        true_pass=sum(1 for r in rows if r.label == "good" and r.passed),
        false_fail=sum(1 for r in rows if r.label == "good" and not r.passed),
        true_fail=sum(1 for r in rows if r.label == "bad" and not r.passed),
        false_pass=sum(1 for r in rows if r.label == "bad" and r.passed),
        good_scores=good_scores,
        bad_scores=bad_scores,
        separable=separable,
        suggested_bar=_suggest_bar(good_scores, bad_scores, separable),
    )
