"""Research add-path: auto-promote additive curriculum changes (design §4.4, P3).

The quarterly research delta proposes additions; under full autonomy (D1) they
are applied straight to the plan (no human PR), but only the ones that clear the
evidence gate: support >= add_threshold AND frequency >= min_frequency AND not
already covered. Per-run caps bound a quarterly burst; the overflow waits for
the bounded author loop. Below-gate items are rejected with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionConfig:
    add_threshold: int = 3  # min supporting postings (incl. aliases)
    min_frequency: float = 0.30  # min relative frequency
    max_per_run: int = 1  # cap additions per cycle


@dataclass(frozen=True)
class DeltaItem:
    item_id: str
    evidence_count: int
    frequency: float
    covered: bool  # already in the plan?


@dataclass(frozen=True)
class PromotionResult:
    promoted: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]  # (item_id, reason)
    deferred: tuple[str, ...]  # cleared the gate but over the per-run cap


def decide_promotions(items: list[DeltaItem], config: PromotionConfig) -> PromotionResult:
    """Decide which proposed additions to promote into the plan this cycle."""
    rejected: list[tuple[str, str]] = []
    qualified: list[DeltaItem] = []
    for it in items:
        if it.covered:
            rejected.append((it.item_id, "already_covered"))
        elif it.evidence_count < config.add_threshold:
            rejected.append((it.item_id, "low_evidence"))
        elif it.frequency < config.min_frequency:
            rejected.append((it.item_id, "low_frequency"))
        else:
            qualified.append(it)

    # Strongest evidence first when capping.
    qualified.sort(key=lambda i: (i.evidence_count, i.frequency), reverse=True)
    promoted = tuple(i.item_id for i in qualified[: config.max_per_run])
    deferred = tuple(i.item_id for i in qualified[config.max_per_run :])
    return PromotionResult(promoted=promoted, rejected=tuple(rejected), deferred=deferred)
