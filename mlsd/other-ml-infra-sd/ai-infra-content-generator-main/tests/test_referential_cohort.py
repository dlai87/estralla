"""Tests for referential integrity (U-H3/U-M6) and cohort protected set (U-H1/U-M8)."""

from aicg.cohort import derive_protected_set
from aicg.referential import Pair, find_broken_pairs, find_dangling_refs


def test_dangling_ref_found_in_surviving_sibling() -> None:
    surviving = {
        "mod-307/README.md": "Cost matters. As covered in mod-309-governance, ...",
        "mod-301/README.md": "Foundations only; no cross-link here.",
    }
    hits = find_dangling_refs("mod-309-governance", surviving)
    assert len(hits) == 1
    assert hits[0][0] == "mod-307/README.md"
    assert "mod-309-governance" in hits[0][1]


def test_no_dangling_refs_when_clean() -> None:
    surviving = {"a.md": "nothing here", "b.md": "nor here"}
    assert find_dangling_refs("mod-309-governance", surviving) == []


def test_pairing_flags_missing_and_stale_solutions() -> None:
    pairs = [
        Pair("ex-01", solution_present=True, recorded_exercise_hash="h1", current_exercise_hash="h1"),
        Pair("ex-02", solution_present=False, recorded_exercise_hash=None, current_exercise_hash="h2"),
        Pair("ex-03", solution_present=True, recorded_exercise_hash="old", current_exercise_hash="new"),
    ]
    broken = dict(find_broken_pairs(pairs))
    assert "ex-01" not in broken
    assert broken["ex-02"] == "missing_solution"
    assert broken["ex-03"] == "hash_mismatch"


def test_protected_set_is_intersection_with_active_plan() -> None:
    taught = {"mod-303", "mod-309", "mod-999-removed"}
    active = {"mod-301", "mod-303", "mod-309"}
    assert derive_protected_set(taught, active) == {"mod-303", "mod-309"}


def test_protected_set_empty_when_no_overlap() -> None:
    assert derive_protected_set({"mod-x"}, {"mod-y"}) == set()
