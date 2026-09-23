"""Tests for the fair-share budget allocator (design §4.6 / review S6, C-B3).

The author loop drains a typed work queue under a HARD daily item budget. Strict
priority would starve new content (review S6), so each class gets a reserved
floor; surplus (a class with little backlog, or the low-priority reserve share)
is redistributed by priority so the budget is fully used without any class
dropping below its floor.
"""

from aicg.budget import BudgetConfig, plan_drain

REGEN = "artifact_needs_regen"
LEARN = "module_needs_learning"
SOLN = "exercise_needs_solution"

SHARES = {REGEN: 0.45, LEARN: 0.30, SOLN: 0.20, "reserve": 0.05}


def test_floors_preserved_and_budget_fully_used() -> None:
    cfg = BudgetConfig(total=20, shares=SHARES)
    plan = plan_drain(cfg, {REGEN: 50, LEARN: 50, SOLN: 50})
    assert plan[REGEN] >= 9  # floor(0.45*20)
    assert plan[LEARN] >= 6  # floor(0.30*20)
    assert plan[SOLN] >= 4  # floor(0.20*20)
    assert sum(plan.values()) == 20  # ample backlog -> full budget used


def test_new_learning_floor_preserved_under_regen_pressure() -> None:
    cfg = BudgetConfig(total=20, shares=SHARES)
    plan = plan_drain(cfg, {REGEN: 9999, LEARN: 50})
    assert plan[LEARN] >= 6  # never starved below its floor by regen backlog
    assert sum(plan.values()) <= 20


def test_empty_class_share_redistributes() -> None:
    cfg = BudgetConfig(total=20, shares=SHARES)
    plan = plan_drain(cfg, {REGEN: 0, LEARN: 50, SOLN: 50})
    assert plan[REGEN] == 0
    assert sum(plan.values()) == 20  # regen's + reserve's share flow to others


def test_never_exceeds_available_per_class() -> None:
    cfg = BudgetConfig(total=20, shares=SHARES)
    plan = plan_drain(cfg, {REGEN: 2, LEARN: 3})
    assert plan[REGEN] <= 2
    assert plan[LEARN] <= 3
    assert sum(plan.values()) <= 5  # can't drain more than exists


def test_zero_budget_drains_nothing() -> None:
    cfg = BudgetConfig(total=0, shares=SHARES)
    assert sum(plan_drain(cfg, {REGEN: 10}).values()) == 0


def test_surplus_goes_to_highest_priority_class() -> None:
    # regen (0.45) outranks learning (0.30): the redistributed reserve lands
    # on regen first.
    cfg = BudgetConfig(total=20, shares=SHARES)
    plan = plan_drain(cfg, {REGEN: 50, LEARN: 50})
    # floors 9 + 6 = 15; remaining 5 (sol share + reserve) -> regen by priority
    assert plan[REGEN] == 14
    assert plan[LEARN] == 6
