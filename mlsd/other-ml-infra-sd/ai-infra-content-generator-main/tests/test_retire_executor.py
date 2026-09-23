"""Tests for the P4 retirement executor (roadmap §1) — fakes, no real git."""
from __future__ import annotations

from aicg.retire_executor import (
    RetireSeams,
    execute_plan,
    plan_retirement,
    scan_dangling_refs,
)
from aicg.retirement import RetireDecision
from aicg.tombstone import RetiredNode


def _node(node_id: str) -> RetiredNode:
    return RetiredNode(
        node_id=node_id,
        title=f"Module {node_id}",
        summary="what it covered",
        retired_on="2026-06-25",
        last_version="v2026.05",
        release_url="https://example.com/releases/v2026.05",
    )


def _decision(*retire: str) -> RetireDecision:
    return RetireDecision(retire=tuple(retire), flagged=(), halted=False, halt_reason=None)


def test_plan_skips_nodes_without_path_or_detail() -> None:
    decision = _decision("mod-1", "mod-2", "mod-3")
    nodes = {"mod-1": _node("mod-1"), "mod-2": _node("mod-2")}  # mod-3 has no detail
    paths = {"mod-1": "lessons/mod-1", "mod-3": "lessons/mod-3"}  # mod-2 has no path
    plan = plan_retirement("repo", decision, nodes, paths, version="v2026.06", date="2026-06-25")
    assert [op.node_id for op in plan.ops] == ["mod-1"]
    assert plan.ops[0].tombstone_path == "lessons/mod-1/RETIRED.md"
    assert "Module mod-1" in plan.changelog_entry
    assert "### Retired" in plan.changelog_entry


def test_scan_dangling_refs_excludes_self_finds_others() -> None:
    node_paths = {"mod-1": "lessons/mod-1"}
    files = {
        "lessons/mod-1/README.md": "self ref lessons/mod-1 should be ignored",
        "lessons/mod-2/README.md": "see lessons/mod-1 for prerequisites",
        "CURRICULUM.md": "no mention here",
    }
    refs = scan_dangling_refs(node_paths, files)
    assert refs == (("mod-1", "lessons/mod-2/README.md"),)


def test_dry_run_writes_nothing_but_reports() -> None:
    decision = _decision("mod-1")
    nodes = {"mod-1": _node("mod-1")}
    paths = {"mod-1": "lessons/mod-1"}
    plan = plan_retirement("repo", decision, nodes, paths, version="v2026.06", date="2026-06-25")

    git_calls: list[list[str]] = []
    writes: dict[str, str] = {}
    seams = RetireSeams(
        run_git=lambda a: (git_calls.append(a) or (0, "")),
        write_text=lambda p, c: writes.__setitem__(p, c),
        read_text=lambda p: {"lessons/mod-2/README.md": "links lessons/mod-1"}.get(p),
        list_files=lambda: ["lessons/mod-2/README.md"],
    )
    result = execute_plan(plan, seams, paths, dry_run=True)
    assert result.dry_run is True
    assert git_calls == []  # nothing executed
    assert writes == {}  # nothing written
    assert result.removed == ("lessons/mod-1",)  # but reports what it would do
    assert result.dangling_refs == (("mod-1", "lessons/mod-2/README.md"),)


def test_execute_git_rm_tombstone_changelog() -> None:
    decision = _decision("mod-1")
    nodes = {"mod-1": _node("mod-1")}
    paths = {"mod-1": "lessons/mod-1"}
    plan = plan_retirement("repo", decision, nodes, paths, version="v2026.06", date="2026-06-25")

    store = {"CHANGELOG.md": "## v2026.05 — 2026-05-01\n\nOld entry\n"}
    git_calls: list[list[str]] = []
    seams = RetireSeams(
        run_git=lambda a: (git_calls.append(a) or (0, "")),
        write_text=lambda p, c: store.__setitem__(p, c),
        read_text=lambda p: store.get(p),
        list_files=lambda: list(store),
    )
    result = execute_plan(plan, seams, paths, dry_run=False)
    assert result.dry_run is False
    assert result.removed == ("lessons/mod-1",)
    assert result.tombstoned == ("lessons/mod-1/RETIRED.md",)
    assert result.changelog_written is True
    # git rm happened, tombstone written + re-added
    assert ["rm", "-r", "--quiet", "lessons/mod-1"] in git_calls
    assert "RETIRED.md" in store["lessons/mod-1/RETIRED.md"] or "retired" in store["lessons/mod-1/RETIRED.md"]
    # changelog prepends new entry above the old one
    assert store["CHANGELOG.md"].index("v2026.06") < store["CHANGELOG.md"].index("v2026.05")


def test_execute_records_git_rm_failure() -> None:
    decision = _decision("mod-1")
    nodes = {"mod-1": _node("mod-1")}
    paths = {"mod-1": "lessons/mod-1"}
    plan = plan_retirement("repo", decision, nodes, paths, version="v2026.06", date="2026-06-25")
    seams = RetireSeams(
        run_git=lambda a: (1, "fatal: pathspec did not match"),
        write_text=lambda p, c: None,
        read_text=lambda p: None,
        list_files=lambda: [],
    )
    result = execute_plan(plan, seams, paths, dry_run=False)
    assert result.removed == ()
    assert any("git rm" in e for e in result.errors)
