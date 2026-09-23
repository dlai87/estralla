"""Cohort freeze / protected set (design U-H1, U-M8).

A paid cohort teaches from a pinned ``cohort-N`` ref so live autonomy can't
change content mid-term. The retire engine additionally skips any node the
active cohort is currently teaching — the **protected set** — deferring its
retirement until the term ends (retirement is deferred, never cancelled).

Pure derivation: given the cohort's taught node ids and the role's active plan
nodes, the protected set is their intersection (a stale cohort entry pointing at
an already-gone node is simply ignored).
"""

from __future__ import annotations

from collections.abc import Iterable


def derive_protected_set(taught_node_ids: Iterable[str], active_plan_nodes: Iterable[str]) -> set[str]:
    """Nodes the active cohort is teaching that still exist in the plan."""
    active = set(active_plan_nodes)
    return {n for n in taught_node_ids if n in active}
