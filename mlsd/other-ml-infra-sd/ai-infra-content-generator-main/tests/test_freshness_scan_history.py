"""Per-repo scan-history + cooldown rotation for freshness review.

These tests prove four contracts that make the per-role nightly review
actually useful (rather than re-judging the alphabetically-first 50
files every cycle):

1. After a review, ``.aicg/freshness-scan-history.json`` exists with one
   entry per judged artifact, carrying timestamp + score + passed flag.
2. Files scanned more recently than ``freshness_cooldown_days`` are
   filtered out before the ``max_artifacts`` slice. When everything is
   in cooldown, the run produces zero work items and (critically) makes
   ZERO judge calls — that's the "free night" for fresh repos.
3. Among eligible artifacts, least-recently-scanned comes first so the
   cap rotates through the corpus over time.
4. History updates land BEFORE a subscription-limit defer breaks the
   loop, so deferred files re-enter the eligible pool on the next run
   instead of being trapped in a "scanned but no verdict" limbo.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from conftest import write_file

from aicg.freshness import (
    FRESHNESS_SCAN_HISTORY,
    review_existing_artifacts,
)
from aicg.judge import JudgeConfig, JudgeVerdict


def _config(cooldown: int = 90) -> JudgeConfig:
    return JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=("api_currency", "version_currency"),
        thresholds={"default": 75, "freshness": 75},
        timeout_seconds=None,
        freshness_cooldown_days=cooldown,
    )


def _passing_verdict(score: int = 90) -> JudgeVerdict:
    return JudgeVerdict(
        score=score,
        dimensions={"api_currency": 25, "version_currency": 20},
        blockers=[],
        summary="Fresh",
        passed=True,
        threshold=75,
        raw="",
    )


def _seed_three_files(repo: Path) -> None:
    write_file(repo / "modules/mod-001/SOLUTION.md", "# a\n")
    write_file(repo / "modules/mod-002/SOLUTION.md", "# b\n")
    write_file(repo / "modules/mod-003/SOLUTION.md", "# c\n")


def test_scan_history_written_after_review(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _seed_three_files(repo)
    calls: list[str] = []

    def fake_judge(**kwargs):
        calls.append(str(kwargs["artifact_path"].name))
        return _passing_verdict()

    report = review_existing_artifacts(
        repo, judge_config=_config(), artifact_judge=fake_judge
    )

    history_path = repo / ".aicg" / FRESHNESS_SCAN_HISTORY
    assert history_path.exists()
    payload = json.loads(history_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert set(payload["files"].keys()) == {
        "modules/mod-001/SOLUTION.md",
        "modules/mod-002/SOLUTION.md",
        "modules/mod-003/SOLUTION.md",
    }
    for entry in payload["files"].values():
        assert "last_scanned" in entry
        assert entry["last_score"] == 90
        assert entry["last_passed"] is True
    assert report["artifacts_reviewed"] == 3
    assert report["skipped_for_cooldown"] == 0


def test_cooldown_skips_recently_scanned_files(tmp_path: Path) -> None:
    """Files scanned 1 day ago must be skipped under a 90-day cooldown."""
    repo = tmp_path / "repo"
    _seed_three_files(repo)

    # Pre-seed history saying we judged everything yesterday.
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    (repo / ".aicg").mkdir(parents=True)
    (repo / ".aicg" / FRESHNESS_SCAN_HISTORY).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "updated_at": yesterday.isoformat(),
                "files": {
                    "modules/mod-001/SOLUTION.md": {
                        "last_scanned": yesterday.isoformat().replace("+00:00", "Z"),
                        "last_score": 80,
                        "last_passed": True,
                    },
                    "modules/mod-002/SOLUTION.md": {
                        "last_scanned": yesterday.isoformat().replace("+00:00", "Z"),
                        "last_score": 80,
                        "last_passed": True,
                    },
                    "modules/mod-003/SOLUTION.md": {
                        "last_scanned": yesterday.isoformat().replace("+00:00", "Z"),
                        "last_score": 80,
                        "last_passed": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    calls: list[str] = []

    def fake_judge(**kwargs):
        calls.append(str(kwargs["artifact_path"]))
        return _passing_verdict()

    report = review_existing_artifacts(
        repo, judge_config=_config(cooldown=90), artifact_judge=fake_judge
    )

    # ZERO judge calls — that's the win. No token cost on a fresh repo.
    assert calls == []
    assert report["artifacts_reviewed"] == 0
    assert report["eligible_count"] == 0
    assert report["skipped_for_cooldown"] == 3
    assert report["work_items"] == []


def test_least_recently_scanned_processed_first(tmp_path: Path) -> None:
    """When max_artifacts caps the run, LRS files win the slot."""
    repo = tmp_path / "repo"
    _seed_three_files(repo)
    write_file(repo / "modules/mod-004/SOLUTION.md", "# d\n")

    # mod-001 and mod-002 scanned 200 days ago; mod-003 scanned yesterday.
    # mod-004 never scanned. Under cooldown=90, eligible = {001, 002, 004}.
    # Sort by LRS: never-scanned first, then 200-days. So order should be
    # mod-004, then mod-001, then mod-002. cap=2 → mod-004 + mod-001.
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=200)).isoformat().replace("+00:00", "Z")
    recent = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    (repo / ".aicg").mkdir(parents=True)
    (repo / ".aicg" / FRESHNESS_SCAN_HISTORY).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "updated_at": now.isoformat(),
                "files": {
                    "modules/mod-001/SOLUTION.md": {
                        "last_scanned": old,
                        "last_score": 80,
                        "last_passed": True,
                    },
                    "modules/mod-002/SOLUTION.md": {
                        "last_scanned": old,
                        "last_score": 80,
                        "last_passed": True,
                    },
                    "modules/mod-003/SOLUTION.md": {
                        "last_scanned": recent,
                        "last_score": 80,
                        "last_passed": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    judged: list[str] = []

    def fake_judge(**kwargs):
        judged.append(str(kwargs["artifact_path"].relative_to(repo).as_posix()))
        return _passing_verdict()

    review_existing_artifacts(
        repo,
        judge_config=_config(cooldown=90),
        artifact_judge=fake_judge,
        max_artifacts=2,
    )
    # mod-003 must NOT have been judged (it's within cooldown).
    assert "modules/mod-003/SOLUTION.md" not in judged
    # mod-004 (never scanned) wins the first slot.
    assert judged[0] == "modules/mod-004/SOLUTION.md"
    # mod-001 (alphabetically before mod-002, same scan time) gets the
    # second slot.
    assert judged[1] == "modules/mod-001/SOLUTION.md"


def test_history_updates_before_subscription_defer(tmp_path: Path) -> None:
    """A mid-batch defer must leave history showing what got judged."""
    repo = tmp_path / "repo"
    _seed_three_files(repo)

    # mod-001 succeeds, mod-002 hits the subscription limit, mod-003
    # never gets judged because the loop breaks.
    def fake_judge(**kwargs):
        rel = kwargs["artifact_path"].relative_to(repo).as_posix()
        if rel == "modules/mod-001/SOLUTION.md":
            return _passing_verdict()
        if rel == "modules/mod-002/SOLUTION.md":
            return JudgeVerdict(
                score=0,
                dimensions={},
                blockers=["Judge subscription limit reached"],
                summary="defer",
                passed=False,
                threshold=75,
                raw="",
            )
        pytest.fail(f"loop should have broken before judging {rel}")

    report = review_existing_artifacts(
        repo, judge_config=_config(), artifact_judge=fake_judge
    )
    assert report["deferred"] is not None
    payload = json.loads(
        (repo / ".aicg" / FRESHNESS_SCAN_HISTORY).read_text(encoding="utf-8")
    )
    # mod-001 was scanned successfully → recorded.
    assert "modules/mod-001/SOLUTION.md" in payload["files"]
    # mod-002 hit the limit; not recorded so it stays eligible for retry.
    assert "modules/mod-002/SOLUTION.md" not in payload["files"]
    assert "modules/mod-003/SOLUTION.md" not in payload["files"]


def test_disabled_judge_does_not_record_history(tmp_path: Path) -> None:
    """When the judge returns None (disabled), don't lock files out."""
    repo = tmp_path / "repo"
    _seed_three_files(repo)

    def fake_judge(**kwargs):
        return None  # judge disabled

    review_existing_artifacts(
        repo, judge_config=_config(), artifact_judge=fake_judge
    )
    # No history written — files must remain eligible the moment the
    # judge is enabled, with no fake 90-day cooldown blocking them.
    assert not (repo / ".aicg" / FRESHNESS_SCAN_HISTORY).exists()
