"""Retirement decision logic for the quarterly research loop (design §4.4, S3/U-M8).

Retirement is the only destructive autonomous operation (`git rm` from `main`),
so it is gated by four guards working together:

1. **Hysteresis** — a node retires only after its support sits below FLOOR for
   ``retire_quarters`` consecutive cycles (~6 months), never on one soft quarter.
   The add-bar and retire-bar are deliberately asymmetric so a requirement
   hovering at threshold can't be added-then-deleted-then-added.
2. **Minimum sample** — if the cycle scraped fewer than ``min_sample`` postings,
   that's "no data", not "zero evidence"; retirement is halted.
3. **Anomaly circuit-breaker** — if more than ``anomaly_fraction`` of active
   nodes drop below FLOOR in one cycle, that's a correlated measurement failure
   (e.g. a broken scraper), not real market movement; halt and flag, execute
   nothing.
4. **Per-cycle cap** — at most ``max_retire_per_cycle`` retirements per role per
   cycle; the rest are flagged and reconsidered next cycle.

Plus the protected set (U-M8): a node the active cohort is teaching is never
retired — deferred until the term ends.

This module is pure: it decides *which* nodes to retire from evidence; the
caller performs the `git rm` + reconciliation + tombstone steps.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class RetireConfig:
    floor: int = 3  # support below this counts as "declining" this cycle
    retire_quarters: int = 2  # consecutive sub-floor cycles before retiring
    min_sample: int = 5  # min absolute postings scraped; below = no-data
    anomaly_fraction: float = 0.15  # >this share dropping at once = measurement failure
    max_retire_per_cycle: int = 1


@dataclass(frozen=True)
class NodeEvidence:
    node_id: str
    current_support: int  # evidence count this cycle
    consecutive_below: int  # consecutive cycles at/below floor, including this one


@dataclass(frozen=True)
class RetireDecision:
    retire: tuple[str, ...]  # node ids to retire this cycle
    flagged: tuple[str, ...]  # eligible-but-deferred (capped / halted / protected)
    halted: bool
    halt_reason: str | None  # "low_sample" | "anomaly" | None


def decide_retirements(
    nodes: list[NodeEvidence],
    *,
    cycle_sample: int,
    config: RetireConfig,
    protected: Iterable[str] = (),
) -> RetireDecision:
    """Decide which active nodes to retire this cycle, honoring all guards."""
    protected_set = set(protected)
    active = list(nodes)
    eligible = [
        n
        for n in active
        if n.consecutive_below >= config.retire_quarters and n.node_id not in protected_set
    ]
    protected_eligible = tuple(
        n.node_id
        for n in active
        if n.consecutive_below >= config.retire_quarters and n.node_id in protected_set
    )

    # Guard 2: thin scrape is no-data, not zero-evidence.
    if cycle_sample < config.min_sample:
        return RetireDecision(
            retire=(),
            flagged=tuple(n.node_id for n in eligible) + protected_eligible,
            halted=True,
            halt_reason="low_sample",
        )

    # Guard 3: correlated mass-drop = measurement failure.
    below_now = [n for n in active if n.current_support < config.floor]
    if active and (len(below_now) / len(active)) > config.anomaly_fraction:
        return RetireDecision(
            retire=(),
            flagged=tuple(n.node_id for n in below_now),
            halted=True,
            halt_reason="anomaly",
        )

    # Guard 4 + hysteresis: retire the worst-declining up to the cap; flag the rest.
    eligible.sort(key=lambda n: (n.current_support, -n.consecutive_below))
    retire = tuple(n.node_id for n in eligible[: config.max_retire_per_cycle])
    flagged = tuple(n.node_id for n in eligible[config.max_retire_per_cycle :]) + protected_eligible
    return RetireDecision(retire=retire, flagged=flagged, halted=False, halt_reason=None)
