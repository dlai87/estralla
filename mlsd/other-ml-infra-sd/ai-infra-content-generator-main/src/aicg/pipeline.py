"""Phase-loop composition for the autonomous pipeline (design §4).

Composes the pure primitives (budget, rotation, promotion, retirement, eval-gate)
into the three core loops, with all side effects injected so the orchestration is
unit-testable without git, an LLM, or the live runner:

- ``author_tick``  (P1): allocate the budget across work classes, then process
  that many items each through the eval-gate (merge or quarantine).
- ``reaudit_tick`` (P2): pick the day's rotation slice, cheap-check each, and
  enqueue a regen ONLY on a cited defect (the no-op guard, C-B3/S4).
- ``research_cycle`` (P3/P4): auto-promote additive deltas that clear the gate;
  decide retirements behind all guards and mark them (executor does the git rm).

The CLI wires the injected callables to the real generator / judge / git
machinery; these functions own only the control flow.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .budget import BudgetConfig, plan_drain
from .promotion import DeltaItem, PromotionConfig, decide_promotions
from .retirement import NodeEvidence, RetireConfig, decide_retirements
from .rotation import ScanNode, select_audit_slice


@dataclass(frozen=True)
class AuthorTickReport:
    merged: int
    quarantined: int
    processed: int
    allocation: dict[str, int] = field(default_factory=dict)


def author_tick(
    *,
    available: dict[str, int],
    budget: BudgetConfig,
    process_item: Callable[[str], str | None],
) -> AuthorTickReport:
    """Drain the queue within the fair-share budget; tally gate outcomes.

    ``process_item(work_class)`` pulls the next item of that class, generates/
    revises it through the eval-gate, and returns ``"merged"`` / ``"quarantined"``
    — or ``None`` if the class is unexpectedly empty (stop draining it).
    """
    allocation = plan_drain(budget, available)
    merged = quarantined = processed = 0
    for work_class, count in allocation.items():
        for _ in range(count):
            status = process_item(work_class)
            if status is None:
                break
            processed += 1
            if status == "merged":
                merged += 1
            elif status == "quarantined":
                quarantined += 1
    return AuthorTickReport(merged, quarantined, processed, allocation)


@dataclass(frozen=True)
class ReauditTickReport:
    scanned: int
    enqueued: int
    defects: tuple[tuple[str, str], ...]  # (node_id, defect)


def reaudit_tick(
    *,
    scan_nodes: list[ScanNode],
    today: str,
    slice_cap: int,
    audit_one: Callable[[str], str | None],
    enqueue_regen: Callable[[str, str], None],
    rotation_days: int = 90,
) -> ReauditTickReport:
    """Re-audit the day's slice; enqueue a regen only when a defect is cited."""
    slice_ids = select_audit_slice(
        scan_nodes, today=today, slice_cap=slice_cap, rotation_days=rotation_days
    )
    defects: list[tuple[str, str]] = []
    for node_id in slice_ids:
        defect = audit_one(node_id)  # None = clean (no-op guard: do NOT regenerate)
        if defect:
            enqueue_regen(node_id, defect)
            defects.append((node_id, defect))
    return ReauditTickReport(scanned=len(slice_ids), enqueued=len(defects), defects=tuple(defects))


@dataclass(frozen=True)
class ResearchCycleReport:
    promoted: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    retired: tuple[str, ...]
    retire_halted: bool
    halt_reason: str | None


def research_cycle(
    *,
    delta_items: list[DeltaItem],
    promotion_config: PromotionConfig,
    nodes: list[NodeEvidence],
    cycle_sample: int,
    retire_config: RetireConfig,
    protected: set[str],
    enqueue_add: Callable[[str], None],
    mark_retire: Callable[[str], None],
) -> ResearchCycleReport:
    """Auto-promote qualifying additions; decide+mark retirements behind the guards."""
    promo = decide_promotions(delta_items, promotion_config)
    for item_id in promo.promoted:
        enqueue_add(item_id)

    retire = decide_retirements(
        nodes, cycle_sample=cycle_sample, config=retire_config, protected=protected
    )
    if not retire.halted:
        for node_id in retire.retire:
            mark_retire(node_id)

    return ResearchCycleReport(
        promoted=promo.promoted,
        rejected=promo.rejected,
        retired=(() if retire.halted else retire.retire),
        retire_halted=retire.halted,
        halt_reason=retire.halt_reason,
    )
