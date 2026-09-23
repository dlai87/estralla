"""Tests for the phase-loop composition (author / re-audit / research)."""

from aicg.budget import BudgetConfig
from aicg.pipeline import author_tick, reaudit_tick, research_cycle
from aicg.promotion import DeltaItem, PromotionConfig
from aicg.retirement import NodeEvidence, RetireConfig
from aicg.rotation import ScanNode

SHARES = {"artifact_needs_regen": 0.5, "module_needs_learning": 0.5}


def test_author_tick_drains_within_budget_and_tallies() -> None:
    seen = {"calls": 0}

    def process_item(work_class):
        seen["calls"] += 1
        # quarantine every 3rd item, merge the rest
        return "quarantined" if seen["calls"] % 3 == 0 else "merged"

    report = author_tick(
        available={"artifact_needs_regen": 100, "module_needs_learning": 100},
        budget=BudgetConfig(total=6, shares=SHARES),
        process_item=process_item,
    )
    assert report.processed == 6  # never exceeds the budget
    assert report.merged + report.quarantined == 6
    assert report.quarantined == 2  # items 3 and 6


def test_author_tick_stops_a_class_when_empty() -> None:
    def process_item(work_class):
        return None  # nothing actually available

    report = author_tick(
        available={"artifact_needs_regen": 5},
        budget=BudgetConfig(total=5, shares={"artifact_needs_regen": 1.0}),
        process_item=process_item,
    )
    assert report.processed == 0


def test_reaudit_enqueues_only_on_defect() -> None:
    enqueued = []
    nodes = [ScanNode("a", None), ScanNode("b", "2026-01-01"), ScanNode("c", "2026-06-20")]

    def audit_one(node_id):
        return "dead link" if node_id == "a" else None  # b clean, c on cooldown

    report = reaudit_tick(
        scan_nodes=nodes,
        today="2026-06-24",
        slice_cap=10,
        audit_one=audit_one,
        enqueue_regen=lambda nid, d: enqueued.append((nid, d)),
    )
    # 'c' is within cooldown -> not in slice; a + b audited; only a had a defect.
    assert report.scanned == 2
    assert report.enqueued == 1
    assert enqueued == [("a", "dead link")]


def test_research_cycle_promotes_and_retires() -> None:
    added, retired = [], []
    deltas = [DeltaItem("new", evidence_count=9, frequency=0.8, covered=False)]
    nodes = [NodeEvidence(f"h{i}", 20, 0) for i in range(9)] + [NodeEvidence("dying", 0, 2)]

    report = research_cycle(
        delta_items=deltas,
        promotion_config=PromotionConfig(max_per_run=1),
        nodes=nodes,
        cycle_sample=30,
        retire_config=RetireConfig(),
        protected=set(),
        enqueue_add=added.append,
        mark_retire=retired.append,
    )
    assert report.promoted == ("new",) and added == ["new"]
    assert report.retired == ("dying",) and retired == ["dying"]
    assert report.retire_halted is False


def test_research_cycle_respects_retire_halt() -> None:
    retired = []
    nodes = [NodeEvidence("dying", 0, 5)]  # eligible, but tiny sample halts it
    report = research_cycle(
        delta_items=[],
        promotion_config=PromotionConfig(),
        nodes=nodes,
        cycle_sample=1,  # below min_sample -> halt
        retire_config=RetireConfig(),
        protected=set(),
        enqueue_add=lambda x: None,
        mark_retire=retired.append,
    )
    assert report.retire_halted is True
    assert report.halt_reason == "low_sample"
    assert report.retired == ()
    assert retired == []  # nothing executed
