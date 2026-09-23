"""Tests for the rotation slice (P2), promotion gate (P3), and stale-lock (C-M2)."""

from aicg.locking import LockMeta, is_stale
from aicg.promotion import DeltaItem, PromotionConfig, decide_promotions
from aicg.rotation import ScanNode, select_audit_slice

# --- rotation (P2) ---


def test_never_scanned_nodes_come_first() -> None:
    nodes = [
        ScanNode("a", "2026-01-01"),  # very overdue
        ScanNode("b", None),  # never scanned -> most overdue
        ScanNode("c", "2026-02-01"),
    ]
    slice_ = select_audit_slice(nodes, today="2026-06-24", slice_cap=2)
    assert slice_[0] == "b"
    assert len(slice_) == 2


def test_cooldown_excludes_recently_scanned() -> None:
    nodes = [
        ScanNode("recent", "2026-06-01"),  # 23 days ago, within 90-day cooldown
        ScanNode("old", "2026-01-01"),
    ]
    slice_ = select_audit_slice(nodes, today="2026-06-24", slice_cap=10)
    assert slice_ == ["old"]


def test_slice_cap_bounds_the_batch() -> None:
    nodes = [ScanNode(f"n{i}", None) for i in range(20)]
    assert len(select_audit_slice(nodes, today="2026-06-24", slice_cap=5)) == 5


# --- promotion (P3) ---

PCFG = PromotionConfig(add_threshold=3, min_frequency=0.30, max_per_run=1)


def test_promotes_well_evidenced_new_requirement() -> None:
    items = [DeltaItem("new", evidence_count=5, frequency=0.5, covered=False)]
    out = decide_promotions(items, PCFG)
    assert out.promoted == ("new",)


def test_rejects_below_gate() -> None:
    items = [
        DeltaItem("thin", evidence_count=2, frequency=0.9, covered=False),
        DeltaItem("rare", evidence_count=9, frequency=0.1, covered=False),
        DeltaItem("dup", evidence_count=9, frequency=0.9, covered=True),
    ]
    out = decide_promotions(items, PCFG)
    assert out.promoted == ()
    reasons = dict(out.rejected)
    assert reasons["thin"] == "low_evidence"
    assert reasons["rare"] == "low_frequency"
    assert reasons["dup"] == "already_covered"


def test_per_run_cap_defers_overflow() -> None:
    items = [
        DeltaItem("a", 9, 0.9, False),
        DeltaItem("b", 8, 0.8, False),
        DeltaItem("c", 7, 0.7, False),
    ]
    out = decide_promotions(items, PCFG)
    assert out.promoted == ("a",)  # strongest evidence first
    assert set(out.deferred) == {"b", "c"}


# --- stale lock (C-M2) ---


def test_fresh_lock_is_not_stale() -> None:
    meta = LockMeta(pid=123, acquired_at="2026-06-24T10:00:00")
    assert not is_stale(meta, now="2026-06-24T10:01:00", ttl_seconds=3600, pid_alive=lambda p: True)


def test_old_lock_with_dead_pid_is_stale() -> None:
    meta = LockMeta(pid=123, acquired_at="2026-06-24T10:00:00")
    assert is_stale(meta, now="2026-06-24T12:00:00", ttl_seconds=3600, pid_alive=lambda p: False)


def test_old_lock_with_live_pid_is_not_broken() -> None:
    # A slow-but-running holder must never be broken.
    meta = LockMeta(pid=123, acquired_at="2026-06-24T10:00:00")
    assert not is_stale(meta, now="2026-06-24T12:00:00", ttl_seconds=3600, pid_alive=lambda p: True)


def test_lock_meta_roundtrips() -> None:
    meta = LockMeta(pid=999, acquired_at="2026-06-24T10:00:00")
    assert LockMeta.parse(meta.serialize()) == meta
