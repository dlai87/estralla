"""Tests for the observe-mode pipeline tick (P2-P5 dry-run)."""

from types import SimpleNamespace

from aicg.packager import RepoChange
from aicg.pipeline_config import PipelineConfig
from aicg.pipeline_tick import TickInputs, run_pipeline_tick
from aicg.promotion import DeltaItem
from aicg.retirement import NodeEvidence
from aicg.rotation import ScanNode


def _config(**phases):
    return PipelineConfig.from_manifest(SimpleNamespace(pipeline={"phases": phases, "reaudit_slice": 5}))


def test_observe_tick_reports_all_phases_without_writing() -> None:
    inputs = TickInputs(
        scan_nodes=[ScanNode("a", None), ScanNode("b", "2026-01-01")],
        delta_items=[DeltaItem("new", evidence_count=9, frequency=0.8, covered=False)],
        retire_nodes=[NodeEvidence(f"h{i}", 20, 0) for i in range(9)]
        + [NodeEvidence("dying", 0, 2)],
        cycle_sample=30,
        protected=set(),
        repo_changes=[RepoChange("repo-a", True, added=("x",)), RepoChange("repo-b", False)],
        today="2026-06-25",
        version="v2026.06",
    )
    report = run_pipeline_tick(config=_config(), inputs=inputs)
    assert report["mode"] == "observe"
    phases = report["phases"]
    # P2: both nodes overdue -> would scan 2
    assert phases["reaudit(P2)"]["would_scan"] == 2
    # P3: the well-evidenced addition would be promoted
    assert phases["research-add(P3)"]["would_promote"] == ["new"]
    # P4: the sustained-decline node would be retired (guards pass)
    assert phases["retire(P4)"]["would_retire"] == ["dying"]
    assert phases["retire(P4)"]["halted"] is False
    # P5: only the changed repo would be tagged
    assert phases["package(P5)"]["would_tag"] == ["repo-a"]


def test_observe_reports_enabled_flags() -> None:
    report = run_pipeline_tick(
        config=_config(retire=True, package=True), inputs=TickInputs(today="2026-06-25")
    )
    assert report["phases"]["retire(P4)"]["enabled"] is True
    assert report["phases"]["package(P5)"]["enabled"] is True
    assert report["phases"]["reaudit(P2)"]["enabled"] is False


def test_observe_retire_halts_on_low_sample() -> None:
    inputs = TickInputs(
        retire_nodes=[NodeEvidence("dying", 0, 5)], cycle_sample=1, today="2026-06-25"
    )
    report = run_pipeline_tick(config=_config(), inputs=inputs)
    assert report["phases"]["retire(P4)"]["halted"] is True
    assert report["phases"]["retire(P4)"]["would_retire"] == []
