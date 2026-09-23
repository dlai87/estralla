"""Fair-share budget allocation for the author loop (design §4.6, review S6/C-B3).

The daily token/item budget is HARD (decision D5). Strict priority would let the
regen stream starve the new-content the pipeline exists to produce (review S6),
so the budget is split into reserved shares per work class. Each class gets a
floor it can't drop below; any surplus — a class with little backlog, or the
low-priority ``reserve`` share — is redistributed to the highest-priority class
that still has backlog, so the budget is fully used and nothing is wasted.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetConfig:
    total: int  # HARD per-run item budget
    shares: dict[str, float]  # work class -> reserved fraction (~sums to 1.0)


def plan_drain(config: BudgetConfig, available: dict[str, int]) -> dict[str, int]:
    """Decide how many items of each class to drain this run.

    Returns a per-class count (keys = those in ``available``). Guarantees:
    each class gets at least its floor (capped by availability), no class
    exceeds its available backlog, the total never exceeds the budget, and
    surplus is redistributed by descending share so the budget is fully used
    when backlog allows.
    """
    drained: dict[str, int] = {cls: 0 for cls in available}
    total = config.total
    if total <= 0:
        return drained

    # Reserved floor per share-class, capped by what's actually queued.
    pool = total
    for cls, share in config.shares.items():
        floor = int(share * total)
        take = min(floor, available.get(cls, 0))
        if cls in drained:
            drained[cls] = take
        pool -= take

    # Redistribute the remaining pool (empty classes' floors + the reserve
    # share) to the highest-priority classes that still have backlog.
    order = sorted(available, key=lambda c: config.shares.get(c, 0.0), reverse=True)
    while pool > 0:
        progressed = False
        for cls in order:
            backlog = available.get(cls, 0) - drained[cls]
            if backlog > 0:
                give = min(backlog, pool)
                drained[cls] += give
                pool -= give
                progressed = True
                if pool == 0:
                    break
        if not progressed:
            break

    return drained
