"""Observe-mode pipeline tick — run every phase's decision loop, write nothing.

This activates P2-P5 in their *first safe form*: the design's staged rollout
brings each write-phase up as a dry-run first (P4 is explicitly "dry-run the
git-rm first"). ``run_pipeline_tick`` composes the phase loops with
recording-only seams, so each phase's decision logic runs on real data and
reports *what it would do* — re-audit slice, additions it would promote,
retirements it would execute (behind all guards), repos it would tag — without
any autonomous write. It reuses the same `pipeline.py` composition the live
loops use, so observe-mode and act-mode share one code path.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .packager import RepoChange, plan_monthly_package, tagged_repos
from .pipeline import reaudit_tick, research_cycle
from .pipeline_config import PipelineConfig
from .promotion import DeltaItem
from .retirement import NodeEvidence
from .rotation import ScanNode


@dataclass(frozen=True)
class TickInputs:
    scan_nodes: list[ScanNode] = field(default_factory=list)
    delta_items: list[DeltaItem] = field(default_factory=list)
    retire_nodes: list[NodeEvidence] = field(default_factory=list)
    cycle_sample: int = 0
    protected: set[str] = field(default_factory=set)
    repo_changes: list[RepoChange] = field(default_factory=list)
    today: str = ""
    version: str = ""


def run_pipeline_tick(
    *,
    config: PipelineConfig,
    inputs: TickInputs,
    audit_one: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    """Run every phase's decision in observe mode; return a report of intents.

    Writes nothing. ``audit_one`` (optional) returns a defect string or None for
    a node; if omitted, P2 reports the slice it would re-audit without scoring
    (so observe mode needs no LLM calls).
    """
    report: dict[str, Any] = {"mode": "observe", "phases": {}}

    # P2 — re-audit: which artifacts would be re-checked this tick.
    auditor = audit_one or (lambda _node_id: None)
    enqueued: list[tuple[str, str]] = []
    r2 = reaudit_tick(
        scan_nodes=inputs.scan_nodes,
        today=inputs.today,
        slice_cap=config.reaudit_slice,
        audit_one=auditor,
        enqueue_regen=lambda nid, d: enqueued.append((nid, d)),
    )
    report["phases"]["reaudit(P2)"] = {
        "enabled": config.reaudit_autofix,
        "would_scan": r2.scanned,
        "would_regenerate": [nid for nid, _ in r2.defects],
    }

    # P3/P4 — research add + retire (guards run; nothing executed).
    promoted: list[str] = []
    retired: list[str] = []
    rc = research_cycle(
        delta_items=inputs.delta_items,
        promotion_config=config.promotion(),
        nodes=inputs.retire_nodes,
        cycle_sample=inputs.cycle_sample,
        retire_config=config.retire(),
        protected=inputs.protected,
        enqueue_add=promoted.append,
        mark_retire=retired.append,
    )
    report["phases"]["research-add(P3)"] = {
        "enabled": config.research_autopromote,
        "would_promote": list(rc.promoted),
        "rejected": [list(x) for x in rc.rejected],
    }
    report["phases"]["retire(P4)"] = {
        "enabled": config.retire_enabled,
        "would_retire": list(rc.retired),
        "halted": rc.retire_halted,
        "halt_reason": rc.halt_reason,
    }

    # P5 — monthly package: which repos would be tagged.
    plans = plan_monthly_package(inputs.repo_changes, version=inputs.version, date=inputs.today)
    report["phases"]["package(P5)"] = {
        "enabled": config.package_enabled,
        "would_tag": tagged_repos(plans),
    }
    return report
