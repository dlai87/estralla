"""Rolling re-audit rotation slice (design §4.4 audit loop, C-B3).

The re-audit loop checks a slice of artifacts per day so every artifact is
re-verified on a ~rotation_days cycle. Nodes scanned within the cooldown are
skipped; the rest are ordered most-overdue-first (never-scanned first) and
capped. With the cap >= daily arrival rate nothing rots past the window; under
backpressure the cap holds and the effective rotation lengthens (freshness is
SOFT — C-B3), which the caller surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

_NEVER = 10**9  # sort key for never-scanned: infinitely overdue


@dataclass(frozen=True)
class ScanNode:
    node_id: str
    last_scan: str | None  # YYYY-MM-DD or None if never scanned


def _days_overdue(last_scan: str | None, today: str) -> int:
    if last_scan is None:
        return _NEVER
    return (date.fromisoformat(today) - date.fromisoformat(last_scan)).days


def select_audit_slice(
    nodes: list[ScanNode], *, today: str, slice_cap: int, rotation_days: int = 90
) -> list[str]:
    """Return the node ids to re-audit today: past-cooldown, most-overdue first, capped."""
    eligible = [
        (n.node_id, _days_overdue(n.last_scan, today))
        for n in nodes
        if _days_overdue(n.last_scan, today) >= rotation_days
    ]
    eligible.sort(key=lambda pair: pair[1], reverse=True)  # most overdue first
    return [nid for nid, _ in eligible[: max(0, slice_cap)]]
