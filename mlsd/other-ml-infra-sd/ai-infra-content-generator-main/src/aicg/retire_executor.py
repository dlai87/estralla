"""Retirement executor (roadmap §1 P4) — the destructive step, behind seams.

`decide_retirements` (retirement.py) decides *which* nodes retire; this module
performs the *execution* the decision's docstring defers to the caller: for each
retired node, `git rm` its content and leave a `RETIRED.md` tombstone at the
path (decision D3 — the only record after removal is what we leave behind),
prepend a `CHANGELOG.md` entry, and scan the repo for now-dangling references so
they can be fixed rather than 404.

The split mirrors the rest of the pipeline: ``plan_retirement`` and
``scan_dangling_refs`` are pure (no IO, trivially testable); ``execute_plan``
does the filesystem/git work through injectable seams, so it runs against fakes
in tests and real git in production, and honors ``dry_run`` (P4 is explicitly
"dry-run to a branch first" before the flag flips to act).
"""
from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .retirement import RetireDecision
from .tombstone import RetiredNode, render_changelog_entry, render_tombstone


@dataclass(frozen=True)
class RetireOp:
    node_id: str
    content_path: str  # repo-relative dir whose content is git-rm'd
    tombstone_path: str  # where RETIRED.md is written (content_path/RETIRED.md)
    tombstone_body: str


@dataclass(frozen=True)
class RetirePlan:
    repo: str
    version: str
    date: str
    ops: tuple[RetireOp, ...]
    changelog_path: str
    changelog_entry: str

    @property
    def is_empty(self) -> bool:
        return not self.ops


def plan_retirement(
    repo: str,
    decision: RetireDecision,
    nodes: Mapping[str, RetiredNode],
    paths: Mapping[str, str],
    *,
    version: str,
    date: str,
    changelog_path: str = "CHANGELOG.md",
) -> RetirePlan:
    """Compute the retirement ops for a decision. Pure — no IO.

    Only nodes in ``decision.retire`` that have both a ``RetiredNode`` detail
    and a repo path are executed; anything missing is skipped (it can't be
    safely removed without knowing where it lives).
    """
    ops: list[RetireOp] = []
    retired_titles: list[str] = []
    for node_id in decision.retire:
        node = nodes.get(node_id)
        path = paths.get(node_id)
        if node is None or not path:
            continue
        path = path.rstrip("/")
        ops.append(
            RetireOp(
                node_id=node_id,
                content_path=path,
                tombstone_path=f"{path}/RETIRED.md",
                tombstone_body=render_tombstone(node),
            )
        )
        retired_titles.append(node.title)
    entry = render_changelog_entry(version, date, added=[], retired=retired_titles)
    return RetirePlan(
        repo=repo,
        version=version,
        date=date,
        ops=tuple(ops),
        changelog_path=changelog_path,
        changelog_entry=entry,
    )


def scan_dangling_refs(
    node_paths: Mapping[str, str], files: Mapping[str, str]
) -> tuple[tuple[str, str], ...]:
    """Find files that still reference a retired node's path. Pure.

    Returns (node_id, referencing_file) pairs. The retired node's own files
    (under its content_path) are excluded — they're being removed/tombstoned.
    """
    refs: list[tuple[str, str]] = []
    for node_id, path in node_paths.items():
        needle = path.rstrip("/")
        for fpath, body in files.items():
            if fpath.startswith(needle + "/") or fpath == f"{needle}/RETIRED.md":
                continue  # the node's own (being removed) files
            if needle in body:
                refs.append((node_id, fpath))
    return tuple(refs)


@dataclass
class RetireResult:
    removed: tuple[str, ...] = ()  # content paths git-rm'd
    tombstoned: tuple[str, ...] = ()  # tombstone paths written
    changelog_written: bool = False
    dangling_refs: tuple[tuple[str, str], ...] = ()
    dry_run: bool = False
    errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetireSeams:
    """Injectable IO. In tests these are fakes; in production they wrap git + fs."""

    run_git: Callable[[list[str]], tuple[int, str]]
    write_text: Callable[[str, str], None]
    read_text: Callable[[str], str | None]
    list_files: Callable[[], list[str]]


def git_fs_seams(repo_root: Path) -> RetireSeams:
    """Production seams: real ``git`` (run in ``repo_root``) + filesystem.

    ``list_files`` enumerates tracked + untracked-but-not-ignored markdown via
    ``git ls-files`` so the dangling-ref scan sees the working tree.
    """
    repo_root = repo_root.resolve()

    def run_git(args: list[str]) -> tuple[int, str]:
        proc = subprocess.run(
            ["git", *args], cwd=str(repo_root), capture_output=True, text=True, check=False
        )
        return proc.returncode, (proc.stdout + proc.stderr)

    def write_text(rel: str, content: str) -> None:
        target = repo_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def read_text(rel: str) -> str | None:
        target = repo_root / rel
        if not target.is_file():
            return None
        return target.read_text(encoding="utf-8", errors="ignore")

    def list_files() -> list[str]:
        rc, out = run_git(["ls-files", "*.md"])
        if rc != 0:
            return []
        return [ln for ln in out.splitlines() if ln.strip()]

    return RetireSeams(
        run_git=run_git, write_text=write_text, read_text=read_text, list_files=list_files
    )


def execute_plan(
    plan: RetirePlan,
    seams: RetireSeams,
    node_paths: Mapping[str, str],
    *,
    dry_run: bool = True,
) -> RetireResult:
    """Execute a retirement plan through the seams.

    Steps per op: ``git rm -r`` the content, write the tombstone, then re-add
    the tombstone (so the path survives as a signpost). Then prepend the
    changelog entry and scan for dangling refs. With ``dry_run`` nothing is
    written or git-touched — the result reports what *would* happen plus the
    dangling-ref scan (which is read-only either way).
    """
    removed: list[str] = []
    tombstoned: list[str] = []
    errors: list[str] = []

    # Dangling-ref scan is read-only — always run it.
    files = {p: (seams.read_text(p) or "") for p in seams.list_files()}
    dangling = scan_dangling_refs(node_paths, files)

    if dry_run:
        return RetireResult(
            removed=tuple(op.content_path for op in plan.ops),
            tombstoned=tuple(op.tombstone_path for op in plan.ops),
            changelog_written=not plan.is_empty,
            dangling_refs=dangling,
            dry_run=True,
        )

    for op in plan.ops:
        rc, out = seams.run_git(["rm", "-r", "--quiet", op.content_path])
        if rc != 0:
            errors.append(f"git rm {op.content_path}: {out.strip()}")
            continue
        removed.append(op.content_path)
        seams.write_text(op.tombstone_path, op.tombstone_body)
        seams.run_git(["add", op.tombstone_path])
        tombstoned.append(op.tombstone_path)

    changelog_written = False
    if not plan.is_empty:
        existing = seams.read_text(plan.changelog_path) or ""
        body = (
            plan.changelog_entry
            if not existing.strip()
            else plan.changelog_entry.rstrip("\n") + "\n\n" + existing.lstrip("\n")
        )
        seams.write_text(plan.changelog_path, body)
        seams.run_git(["add", plan.changelog_path])
        changelog_written = True

    return RetireResult(
        removed=tuple(removed),
        tombstoned=tuple(tombstoned),
        changelog_written=changelog_written,
        dangling_refs=dangling,
        dry_run=False,
        errors=tuple(errors),
    )
