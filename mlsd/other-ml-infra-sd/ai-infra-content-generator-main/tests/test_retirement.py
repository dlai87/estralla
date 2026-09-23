"""Tests for the retirement decision logic (design §4.4 + review S3).

Retirement is the one destructive, autonomous operation, so it is heavily
gated: hysteresis (sustained decline, not a single soft quarter), a minimum
absolute posting sample (a thin scrape is "no data", not "zero evidence"), an
anomaly circuit-breaker (a correlated mass-drop = measurement failure, halt
rather than execute), and a per-cycle cap.
"""

from aicg.retirement import NodeEvidence, RetireConfig, decide_retirements


def _nodes(healthy: int, declining: list[tuple[str, int, int]]) -> list[NodeEvidence]:
    """healthy filler nodes (well above floor) + explicit declining ones."""
    nodes = [NodeEvidence(f"healthy-{i}", current_support=20, consecutive_below=0) for i in range(healthy)]
    nodes += [NodeEvidence(nid, current_support=s, consecutive_below=c) for nid, s, c in declining]
    return nodes


CFG = RetireConfig(floor=3, retire_quarters=2, min_sample=5, anomaly_fraction=0.15, max_retire_per_cycle=1)


def test_retires_after_sustained_decline() -> None:
    nodes = _nodes(9, [("mod-x", 1, 2)])  # 1 node, 2 consecutive sub-floor quarters
    out = decide_retirements(nodes, cycle_sample=30, config=CFG)
    assert out.halted is False
    assert out.retire == ("mod-x",)


def test_single_soft_quarter_does_not_retire() -> None:
    nodes = _nodes(9, [("mod-x", 1, 1)])  # only 1 quarter below floor -> hysteresis holds
    out = decide_retirements(nodes, cycle_sample=30, config=CFG)
    assert out.retire == ()


def test_low_sample_halts_retirement() -> None:
    nodes = _nodes(9, [("mod-x", 0, 5)])  # would retire, but...
    out = decide_retirements(nodes, cycle_sample=3, config=CFG)  # sample < min_sample
    assert out.halted is True
    assert out.halt_reason == "low_sample"
    assert out.retire == ()


def test_anomaly_mass_drop_halts() -> None:
    # 4 of 10 nodes drop below floor this cycle (40% > 15%) -> measurement
    # failure, halt and retire nothing even though some are eligible.
    declining = [(f"mod-{i}", 0, 2) for i in range(4)]
    nodes = _nodes(6, declining)
    out = decide_retirements(nodes, cycle_sample=30, config=CFG)
    assert out.halted is True
    assert out.halt_reason == "anomaly"
    assert out.retire == ()
    assert set(out.flagged) == {n for n, _, _ in declining}


def test_per_cycle_cap_limits_and_flags_rest() -> None:
    # 3 eligible out of 30 nodes (10% < 15%, no anomaly); cap=1 -> retire 1, flag 2.
    declining = [("mod-a", 2, 2), ("mod-b", 0, 3), ("mod-c", 1, 2)]
    nodes = _nodes(27, declining)
    out = decide_retirements(nodes, cycle_sample=40, config=CFG)
    assert out.halted is False
    assert len(out.retire) == 1
    # lowest-support / longest-declining retired first: mod-b (support 0, 3 quarters)
    assert out.retire == ("mod-b",)
    assert set(out.flagged) == {"mod-a", "mod-c"}


def test_protected_nodes_are_never_retired() -> None:
    # A node the active cohort is teaching (protected set, U-M8) is deferred.
    nodes = _nodes(9, [("mod-x", 0, 5)])
    out = decide_retirements(nodes, cycle_sample=30, config=CFG, protected={"mod-x"})
    assert out.retire == ()
    assert "mod-x" in out.flagged
