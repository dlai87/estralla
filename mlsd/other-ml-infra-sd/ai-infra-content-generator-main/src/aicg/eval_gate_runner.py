"""Production adapter: wire the real judge into the eval-gate (design §4.3, C-B1).

`eval_gate.run_eval_gate` is pure orchestration over injected score/critic/
generate/revise steps. This module supplies the production versions:

- **panel** — call the real freshness judge ``panel_size`` times; the gate takes
  the median, so one bad sample can't sink (or save) an artifact.
- **critic** — the judge already returns ``blockers`` grounded in evidence (dead
  links, stale APIs/versions); the adversarial critic surfaces those as the
  no-merge condition. (Same model, but blockers are grounded in the artifact's
  actual content, not self-consistency — the C-B1 independence stance.)

For a re-audited (existing) artifact, ``generate`` reads the current file and
``revise`` calls the supplied regenerator to rewrite it; the judge always grades
the file on disk. The judge call is the expensive step, so callers pass a small
``panel_size``.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable
from pathlib import Path

from .eval_gate import EvalGateConfig, EvalGateOutcome, run_eval_gate
from .judge import JudgeConfig, JudgeVerdict

JudgeCall = Callable[..., JudgeVerdict | None]


def _verdict(
    judge: JudgeCall,
    repo_path: Path,
    artifact_path: Path,
    artifact_id: str,
    config: JudgeConfig,
    runner_root: Path | None,
) -> JudgeVerdict | None:
    return judge(
        repo_path=repo_path,
        artifact_path=artifact_path,
        artifact_id=artifact_id,
        config=config,
        runner_root=runner_root,
    )


def panel_median(
    *,
    judge: JudgeCall,
    repo_path: Path,
    artifact_path: Path,
    artifact_id: str,
    config: JudgeConfig,
    panel_size: int = 3,
    runner_root: Path | None = None,
) -> int:
    """Median score from ``panel_size`` independent judge calls on the artifact."""
    scores: list[int] = []
    for _ in range(panel_size):
        v = _verdict(judge, repo_path, artifact_path, artifact_id, config, runner_root)
        scores.append(v.score if v else 0)
    return int(statistics.median(scores)) if scores else 0


def gate_existing_artifact(
    *,
    repo_path: Path,
    artifact_path: Path,
    artifact_id: str,
    judge_config: JudgeConfig,
    gate_config: EvalGateConfig,
    regenerate: Callable[[list[str]], None],
    judge: JudgeCall,
    runner_root: Path | None = None,
) -> EvalGateOutcome:
    """Run the full eval-gate on an existing artifact (re-audit / regen path).

    ``regenerate(issues)`` rewrites the artifact file in place from the judge's
    issues. The gate scores the file (panel), and on failure regenerates and
    re-scores, up to the configured bound, else quarantines.
    """

    def generate() -> str:
        return artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""

    def score(_artifact: str) -> int:
        v = _verdict(judge, repo_path, artifact_path, artifact_id, judge_config, runner_root)
        return v.score if v else 0

    def critic(_artifact: str) -> list[str]:
        v = _verdict(judge, repo_path, artifact_path, artifact_id, judge_config, runner_root)
        return list(v.blockers) if v else ["judge returned no verdict"]

    def revise(_artifact: str, issues: list[str]) -> str:
        regenerate(issues)
        return artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""

    return run_eval_gate(
        generate=generate, score=score, critic=critic, revise=revise, config=gate_config
    )
