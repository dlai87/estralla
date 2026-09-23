"""Stale-lock detection for the org lock dir (design review C-M2).

The pipeline serializes on a single lock dir. Today the lock is a bare `mkdir`
mutex with no owner metadata, so a job killed mid-run (OOM, power loss) while
holding it wedges every subsequent tick silently. This stamps the lock with
PID + acquire time and detects a stale lock: held past a TTL *and* whose owner
PID is no longer alive. A slow-but-live holder is never broken — only a crashed
one, and only after the TTL grace.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LockMeta:
    pid: int
    acquired_at: str  # ISO timestamp

    def serialize(self) -> str:
        return f"{self.pid}\n{self.acquired_at}\n"

    @classmethod
    def parse(cls, text: str) -> LockMeta:
        lines = text.strip().splitlines()
        return cls(pid=int(lines[0]), acquired_at=lines[1])


def is_stale(
    meta: LockMeta,
    *,
    now: str,
    ttl_seconds: int,
    pid_alive: Callable[[int], bool],
) -> bool:
    """A lock is stale only if held past the TTL AND its owner PID is dead."""
    held = (datetime.fromisoformat(now) - datetime.fromisoformat(meta.acquired_at)).total_seconds()
    if held <= ttl_seconds:
        return False  # within grace — give a slow holder room
    return not pid_alive(meta.pid)
