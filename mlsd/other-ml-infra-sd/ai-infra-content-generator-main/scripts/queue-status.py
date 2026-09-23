#!/usr/bin/env python3
"""Print a quick status table for remaining curriculum work.

Reads:
  - <state>/work-queue.json (org-level promoted queue)
  - <workspace>/<repo>/.aicg/work-plan.json (per-repo, not yet promoted)

Where <state> and <workspace> are resolved from the org manifest, so the
script never needs a hardcoded host path. Run from anywhere:

    python scripts/queue-status.py
    python scripts/queue-status.py --manifest path/to/aicg-org.yaml
    python scripts/queue-status.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aicg.org_config import load_manifest, state_dir_for_manifest  # noqa: E402


IN_FLIGHT = {"pr_open", "pr_opened", "in_progress"}
DONE = {"merged", "closed", "skipped"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to aicg-org.yaml (defaults to config/aicg-org.yaml).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON document instead of an ASCII table.",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    state_dir = state_dir_for_manifest(manifest)
    workspace = manifest.path.parent.parent

    queue_path = state_dir / "work-queue.json"
    queue_items = _load_queue_items(queue_path)
    status_counts = Counter((it.get("status") or "unset") for it in queue_items)
    ready_now, deferred = _split_ready(queue_items)

    per_repo = _aggregate_per_repo(workspace, manifest.repo_names)

    if args.json:
        print(json.dumps(_summary_dict(
            queue_path, queue_items, status_counts, ready_now, deferred, per_repo
        ), indent=2, sort_keys=True))
        return 0

    _print_table(queue_items, status_counts, ready_now, deferred, per_repo)
    return 0


def _load_queue_items(queue_path: Path) -> list[dict]:
    if not queue_path.exists():
        return []
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return list(data.get("work_items") or data.get("items") or [])


def _split_ready(items: list[dict]) -> tuple[int, int]:
    now = datetime.now(timezone.utc).isoformat()
    ready = deferred = 0
    for it in items:
        status = it.get("status") or "unset"
        if status in IN_FLIGHT or status in DONE:
            continue
        retry_after = it.get("retry_after")
        if retry_after and retry_after > now:
            deferred += 1
        else:
            ready += 1
    return ready, deferred


def _aggregate_per_repo(workspace: Path, repos: tuple[str, ...]) -> list[dict]:
    rows: list[dict] = []
    for repo in repos:
        plan = workspace / repo / ".aicg" / "work-plan.json"
        if not plan.exists():
            continue
        try:
            data = json.loads(plan.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        work_items = data.get("work_items") or []
        backlog = data.get("backlog_items") or []
        if not work_items and not backlog:
            continue
        rows.append({
            "repo": repo,
            "work_items": len(work_items),
            "backlog_items": len(backlog),
        })
    rows.sort(key=lambda r: r["work_items"] + r["backlog_items"], reverse=True)
    return rows


def _summary_dict(
    queue_path: Path,
    items: list[dict],
    status_counts: Counter,
    ready_now: int,
    deferred: int,
    per_repo: list[dict],
) -> dict:
    return {
        "queue_file_present": queue_path.exists(),
        "totals": {
            "tracked": len(items),
            "ready_now": ready_now,
            "deferred": deferred,
            "in_flight": sum(status_counts[s] for s in IN_FLIGHT),
            "done": sum(status_counts[s] for s in DONE),
        },
        "by_status": dict(status_counts),
        "per_repo_unpromoted": per_repo,
    }


def _print_table(
    items: list[dict],
    status_counts: Counter,
    ready_now: int,
    deferred: int,
    per_repo: list[dict],
) -> None:
    in_flight = sum(status_counts[s] for s in IN_FLIGHT)
    done = sum(status_counts[s] for s in DONE)
    unpromoted_work = sum(r["work_items"] for r in per_repo)
    unpromoted_backlog = sum(r["backlog_items"] for r in per_repo)

    print("Curriculum queue status")
    print("=" * 48)
    _print_kv_table([
        ("ready now", ready_now),
        ("deferred (retry_after)", deferred),
        ("in flight (PRs open)", in_flight),
        ("done (merged/closed)", done),
        ("total tracked", len(items)),
        ("unpromoted work_items", unpromoted_work),
        ("unpromoted backlog", unpromoted_backlog),
    ])
    remaining = ready_now + deferred + in_flight + unpromoted_work + unpromoted_backlog
    print(f"\nEffective remaining: {remaining}")

    if status_counts:
        print("\nBy status:")
        _print_kv_table(sorted(status_counts.items(), key=lambda kv: -kv[1]))

    if per_repo:
        print("\nPer-repo (unpromoted only):")
        _print_grid(
            ["repo", "work_items", "backlog_items"],
            [[r["repo"], r["work_items"], r["backlog_items"]] for r in per_repo],
        )


def _print_kv_table(pairs: list[tuple]) -> None:
    if not pairs:
        return
    key_width = max(len(str(k)) for k, _ in pairs)
    for k, v in pairs:
        print(f"  {str(k).ljust(key_width)}  {v}")


def _print_grid(headers: list[str], rows: list[list]) -> None:
    if not rows:
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  ".join("-" * w for w in widths)
    print("  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  " + sep)
    for row in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))


if __name__ == "__main__":
    raise SystemExit(main())
