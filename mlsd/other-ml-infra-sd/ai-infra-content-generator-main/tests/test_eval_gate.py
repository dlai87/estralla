"""Tests for the eval-gate orchestration (design §4.3).

The gate is the evaluator-optimizer loop that replaces the human reviewer:
generate -> panel of judges + adversarial critic -> pass merges, fail
revises (bounded), else quarantine. This tests the orchestration logic with
injected scorer/critic/revise functions — no live LLM.
"""

from aicg.eval_gate import EvalGateConfig, run_eval_gate


def _scorer(scores):
    """A panel scorer that returns the next seeded score per call."""
    it = iter(scores)
    return lambda artifact: next(it)


def _cfg(panel_size=3, bar=75, max_revise=3):
    return EvalGateConfig(panel_size=panel_size, bar=bar, max_revise=max_revise)


def test_passes_first_round_clean() -> None:
    out = run_eval_gate(
        generate=lambda: "draft0",
        score=_scorer([90, 88, 92]),
        critic=lambda a: [],
        revise=lambda a, issues: a + "+",
        config=_cfg(),
    )
    assert out.status == "merged"
    assert out.rounds == 1
    assert out.final_artifact == "draft0"
    assert out.final_score == 90  # median of (90, 88, 92)


def test_median_resists_one_low_outlier() -> None:
    # One judge scores 30; the panel median (88) still clears the bar.
    out = run_eval_gate(
        generate=lambda: "d",
        score=_scorer([90, 30, 88]),
        critic=lambda a: [],
        revise=lambda a, i: a,
        config=_cfg(),
    )
    assert out.status == "merged"
    assert out.final_score == 88


def test_blocker_blocks_pass_even_with_high_scores() -> None:
    # Scores are high every round, but the adversarial critic always finds a
    # blocker -> never merges -> quarantines after max_revise rounds.
    out = run_eval_gate(
        generate=lambda: "d",
        score=_scorer([90] * 9),
        critic=lambda a: ["dead link to vendor docs"],
        revise=lambda a, i: a + "!",
        config=_cfg(),
    )
    assert out.status == "quarantined"
    assert out.rounds == 3
    assert "dead link to vendor docs" in out.blockers


def test_passes_after_revise() -> None:
    # Round 1 median 40 (below bar) -> revise -> round 2 median 85 -> merge.
    out = run_eval_gate(
        generate=lambda: "d0",
        score=_scorer([40, 42, 38, 85, 86, 84]),
        critic=lambda a: [],
        revise=lambda a, i: "d1",
        config=_cfg(),
    )
    assert out.status == "merged"
    assert out.rounds == 2
    assert out.final_artifact == "d1"


def test_revise_receives_blockers_and_below_bar_note() -> None:
    seen = {}

    def revise(a, issues):
        seen["issues"] = list(issues)
        return "d1"

    # Round 1: blocked on "d0"; round 2: clean high on "d1".
    out = run_eval_gate(
        generate=lambda: "d0",
        score=_scorer([90] * 6),
        critic=lambda a: ["fix injection path"] if a == "d0" else [],
        revise=revise,
        config=_cfg(),
    )
    assert out.status == "merged" and out.rounds == 2
    assert "fix injection path" in seen["issues"]


def test_quarantine_does_not_revise_after_final_round() -> None:
    calls = {"revise": 0}

    def revise(a, i):
        calls["revise"] += 1
        return a + "x"

    out = run_eval_gate(
        generate=lambda: "d",
        score=_scorer([10] * 9),
        critic=lambda a: [],
        revise=revise,
        config=_cfg(max_revise=3),
    )
    assert out.status == "quarantined"
    # revise runs only between rounds: after r1 and r2, not after the final r3.
    assert calls["revise"] == 2
    assert len(out.history) == 3
