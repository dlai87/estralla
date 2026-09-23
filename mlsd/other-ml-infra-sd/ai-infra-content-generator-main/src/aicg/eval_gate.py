"""The eval-gate: the self-verifying loop that replaces the human reviewer.

Design §4.3 (autonomous-curriculum-pipeline.md). With the human approval gate
removed (decision D1), content must verify itself before reaching ``main``. The
gate is the evaluator-optimizer pattern the curriculum itself teaches (mod-204):

    generate -> [panel of N judges] + adversarial critic
        pass (median >= BAR and no blockers) -> MERGE
        fail -> revise with the issues -> repeat (bounded)
        still failing after MAX_REVISE -> QUARANTINE (flagged best-effort)

This module is pure orchestration: the scorer, critic, generate, and revise
steps are injected. Production wires them to the real judge (panel = N
independent judge calls; critic = deterministic checks + external-evidence
grounding per review item C-B1). Keeping the loop injectable makes the control
flow — median, bounded revise, quarantine — unit-testable without an LLM.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Injected step signatures.
GenerateFn = Callable[[], str]
ScoreFn = Callable[[str], int]  # one judge's score for an artifact (0-100)
CriticFn = Callable[[str], list[str]]  # adversarial critic -> blocker strings
ReviseFn = Callable[[str, list[str]], str]  # (artifact, issues) -> revised artifact

MERGED = "merged"
QUARANTINED = "quarantined"


@dataclass(frozen=True)
class EvalGateConfig:
    panel_size: int = 3  # independent judges sampled per round
    bar: int = 75  # pass threshold for the panel median (set by calibration, P0)
    max_revise: int = 3  # rounds before quarantine


_DEFAULT_CONFIG = EvalGateConfig()


@dataclass(frozen=True)
class RoundRecord:
    round: int
    scores: tuple[int, ...]
    median: int
    blockers: tuple[str, ...]
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "scores": list(self.scores),
            "median": self.median,
            "blockers": list(self.blockers),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class EvalGateOutcome:
    status: str  # MERGED | QUARANTINED
    final_artifact: str
    rounds: int
    final_score: int
    blockers: tuple[str, ...]
    history: tuple[RoundRecord, ...]

    @property
    def merged(self) -> bool:
        return self.status == MERGED

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rounds": self.rounds,
            "final_score": self.final_score,
            "blockers": list(self.blockers),
            "history": [r.as_dict() for r in self.history],
        }


def run_eval_gate(
    *,
    generate: GenerateFn,
    score: ScoreFn,
    critic: CriticFn,
    revise: ReviseFn,
    config: EvalGateConfig = _DEFAULT_CONFIG,
) -> EvalGateOutcome:
    """Run the generate -> judge/critic -> revise loop to a pass or quarantine.

    Pass condition: panel median >= ``bar`` AND the adversarial critic finds no
    blockers. Both must hold — a high score with one security/accuracy blocker
    still fails. Revise runs only *between* rounds (never after the final round),
    so the quarantined artifact is the last one actually scored.
    """
    draft = generate()
    history: list[RoundRecord] = []

    for r in range(1, config.max_revise + 1):
        scores = tuple(int(score(draft)) for _ in range(config.panel_size))
        median = int(statistics.median(scores))
        blockers = tuple(critic(draft))
        passed = median >= config.bar and not blockers
        history.append(RoundRecord(r, scores, median, blockers, passed))

        if passed:
            return EvalGateOutcome(MERGED, draft, r, median, (), tuple(history))

        if r < config.max_revise:
            issues = list(blockers)
            if median < config.bar:
                issues.append(f"panel median {median} below bar {config.bar}")
            draft = revise(draft, issues)

    last = history[-1]
    return EvalGateOutcome(
        QUARANTINED, draft, config.max_revise, last.median, last.blockers, tuple(history)
    )
