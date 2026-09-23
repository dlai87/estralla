"""Staged-rollout configuration for the autonomous pipeline (design §5, P0-P6).

The design mandates phased enablement (P0->P6), each gated by evidence — never
flip the whole system on at once. This reads a ``pipeline`` block from the org
manifest into typed config. **Every autonomous-write phase defaults OFF**, so a
fresh deployment is inert: the loops can run in observe/flag mode but make no
autonomous changes until an operator turns a phase on (after calibration for the
eval-gate, and — for retire — a ToS-clean job-postings source).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .budget import BudgetConfig
from .eval_gate import EvalGateConfig
from .promotion import PromotionConfig
from .retirement import RetireConfig

_DEFAULT_SHARES = {
    "artifact_needs_regen": 0.45,
    "module_needs_learning": 0.30,
    "exercise_needs_solution": 0.20,
    "reserve": 0.05,
}


@dataclass(frozen=True)
class PipelineConfig:
    # --- phase enablement (staged rollout; autonomous-write phases default OFF) ---
    author_enabled: bool = False  # P1: drain queue through the eval-gate to main
    reaudit_autofix: bool = False  # P2: auto-regenerate on a cited defect (else flag-only)
    research_autopromote: bool = False  # P3: apply additive deltas without a PR
    retire_enabled: bool = False  # P4: git rm declined content (also needs a ToS-clean source)
    package_enabled: bool = False  # P5: monthly tag + release
    # --- knobs ---
    daily_budget: int = 8  # HARD per-day item budget
    budget_shares: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_SHARES))
    rotation_days: int = 90
    reaudit_slice: int = 30
    heartbeat_url: str | None = None  # out-of-band dead-man's-switch (C-B2)

    @classmethod
    def from_manifest(cls, manifest: Any) -> PipelineConfig:
        cfg = getattr(manifest, "pipeline", None) or {}
        phases = cfg.get("phases", {}) or {}
        shares = cfg.get("budget_shares") or dict(_DEFAULT_SHARES)
        return cls(
            author_enabled=bool(phases.get("author", False)),
            reaudit_autofix=bool(phases.get("reaudit_autofix", False)),
            research_autopromote=bool(phases.get("research_autopromote", False)),
            retire_enabled=bool(phases.get("retire", False)),
            package_enabled=bool(phases.get("package", False)),
            daily_budget=int(cfg.get("daily_budget", 8)),
            budget_shares={str(k): float(v) for k, v in shares.items()},
            rotation_days=int(cfg.get("rotation_days", 90)),
            reaudit_slice=int(cfg.get("reaudit_slice", 30)),
            heartbeat_url=cfg.get("heartbeat_url"),
        )

    # --- typed sub-configs the loops consume ---
    def budget(self) -> BudgetConfig:
        return BudgetConfig(total=self.daily_budget, shares=self.budget_shares)

    def eval_gate(self, bar: int) -> EvalGateConfig:
        return EvalGateConfig(bar=bar)

    def promotion(self) -> PromotionConfig:
        return PromotionConfig()

    def retire(self) -> RetireConfig:
        return RetireConfig()

    def enabled_phases(self) -> list[str]:
        names = [
            ("author(P1)", self.author_enabled),
            ("reaudit-autofix(P2)", self.reaudit_autofix),
            ("research-autopromote(P3)", self.research_autopromote),
            ("retire(P4)", self.retire_enabled),
            ("package(P5)", self.package_enabled),
        ]
        return [n for n, on in names if on]
