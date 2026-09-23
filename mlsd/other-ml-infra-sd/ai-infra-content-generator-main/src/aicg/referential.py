"""Referential-integrity checks for autonomous content changes.

Two ways autonomy can produce internally-broken repos:

- **Dangling references on retire (U-H3):** retiring a module `git rm`s its files,
  but sibling content may still link to it ("see Module 6"). A retire must not
  finalize while surviving content still references the retired node — the
  references are rewritten/regenerated first, else the retire defers (C5).
- **Exercise/solution pairing drift (U-M6):** an exercise and its solution are a
  coupled unit. A solution that is missing, or whose recorded exercise hash no
  longer matches the live exercise, is a broken pair the learner would hit.

Both are pure: the caller supplies the file contents / hashes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


def find_dangling_refs(node_id: str, surviving_files: dict[str, str]) -> list[tuple[str, str]]:
    """Find surviving files that still reference ``node_id``.

    Matches the node id/slug as a word or inside a path/link. Returns
    (file_path, matched_line) pairs so the caller can rewrite or regenerate
    them before a retire finalizes.
    """
    pattern = re.compile(re.escape(node_id))
    hits: list[tuple[str, str]] = []
    for path, content in surviving_files.items():
        for line in content.splitlines():
            if pattern.search(line):
                hits.append((path, line.strip()))
    return hits


@dataclass(frozen=True)
class Pair:
    exercise_id: str
    solution_present: bool
    recorded_exercise_hash: str | None  # hash the solution was written against
    current_exercise_hash: str


def find_broken_pairs(pairs: list[Pair]) -> list[tuple[str, str]]:
    """Return (exercise_id, reason) for exercises with a missing/stale solution."""
    broken: list[tuple[str, str]] = []
    for p in pairs:
        if not p.solution_present:
            broken.append((p.exercise_id, "missing_solution"))
        elif p.recorded_exercise_hash != p.current_exercise_hash:
            broken.append((p.exercise_id, "hash_mismatch"))
    return broken
