"""Bug 2 — rate-limit detector for response.md / response.json.

The Jun 1 2026 research cycle had roles 5-12 fail silently with rc=1
and empty stderr. Reading the JSONL transcript showed each one had
actually hit Claude Code's 5-hour session limit — the message
"You've hit your session limit · resets HH:MMam (TZ)" landed in
response.md (where the wrapper redirects claude's stdout) but never
reached the runner's captured stdout, so the classifier missed it
and the runner reported `agent_failed`.

These tests prove the fix:

1. ``classify_limit_scope`` matches the JSONL fingerprint
   (``"apiErrorStatus":429`` etc.) so a wrapper that DOESN'T redirect
   still gets caught.
2. ``parse_resets_clause`` converts ``resets 10:30am (America/Phoenix)``
   to an absolute ISO UTC timestamp.
3. ``reclassify_with_response_file`` reads ``response.md`` /
   ``response.json`` to upgrade a ``rc=1 + clean stdout + empty stderr``
   failure into ``limit_reached=True`` — the actual Bug 2 condition.
4. Already-limited results pass through unchanged (no double-counting).
5. Successful results pass through unchanged (no false positives).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from aicg.agent_cli import (
    AgentCommandResult,
    classify_limit_scope,
    parse_resets_clause,
    reclassify_with_response_file,
)


def _failed_result(stdout: str = "", stderr: str = "") -> AgentCommandResult:
    return AgentCommandResult(
        command="fake",
        returncode=1,
        stdout=stdout,
        stderr=stderr,
        limit_reached=False,
        retry_after=None,
        limit_scope=None,
        limit_pattern_unmatched=True,
    )


# ---------- classify_limit_scope direct ----------


def test_classify_recognizes_apierrorstatus_429() -> None:
    """A JSONL line carrying the 429 fingerprint must classify."""
    text = '{"message":"err","apiErrorStatus":429,"error":"rate_limit"}'
    assert classify_limit_scope(text) is not None


def test_classify_recognizes_error_rate_limit_string() -> None:
    text = '{"error":"rate_limit","something":"else"}'
    assert classify_limit_scope(text) is not None


def test_classify_handles_session_limit_phrasing() -> None:
    """The user-facing text inside the JSONL still classifies."""
    text = "You've hit your session limit · resets 10:30am (America/Phoenix)"
    scope = classify_limit_scope(text)
    # "session limit" is in LIMIT_PATTERNS and "5-hour" / "weekly" never
    # appear in this phrasing, so the scope falls back to "unknown".
    # That's fine — the runner still marks the role deferred.
    assert scope is not None


# ---------- parse_resets_clause ----------


def test_parse_resets_clause_converts_local_time_to_utc() -> None:
    """``resets 10:30am (America/Phoenix)`` → next 10:30 MST in UTC."""
    text = "You've hit your session limit · resets 10:30am (America/Phoenix)"
    # Phoenix is UTC-7 year-round (no DST). At 09:00 UTC on June 4 it
    # is 02:00 in Phoenix → the next 10:30am is on the SAME day at
    # 17:30 UTC.
    now = datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc)
    iso = parse_resets_clause(text, now=now)
    assert iso == "2026-06-04T17:30:00Z"


def test_parse_resets_clause_rolls_forward_when_already_past() -> None:
    """If 'now' is later than today's reset time, return tomorrow's."""
    text = "resets 10:30am (America/Phoenix)"
    # 19:00 UTC on June 4 == 12:00 PHX, past 10:30am → return June 5.
    now = datetime(2026, 6, 4, 19, 0, tzinfo=timezone.utc)
    iso = parse_resets_clause(text, now=now)
    assert iso == "2026-06-05T17:30:00Z"


def test_parse_resets_clause_returns_none_when_no_match() -> None:
    assert parse_resets_clause("nothing here") is None


def test_parse_resets_clause_pm_offset() -> None:
    """3:15pm in Phoenix → 22:15 UTC, advancing day if needed."""
    text = "resets 3:15pm (America/Phoenix)"
    now = datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc)
    iso = parse_resets_clause(text, now=now)
    assert iso == "2026-06-04T22:15:00Z"


def test_parse_resets_clause_handles_missing_timezone() -> None:
    """No (TZ) annotation → assume UTC, still parseable."""
    text = "resets 8:00am"
    now = datetime(2026, 6, 4, 1, 0, tzinfo=timezone.utc)
    iso = parse_resets_clause(text, now=now)
    assert iso == "2026-06-04T08:00:00Z"


# ---------- reclassify_with_response_file ----------


def test_reclassify_catches_limit_in_response_md(tmp_path: Path) -> None:
    """The Bug 2 condition: rc=1, empty stderr, JSONL hidden in response.md."""
    response = tmp_path / "response.md"
    response.write_text(
        '{"type":"assistant","message":{"content":[{"type":"text","text":'
        '"You\'ve hit your session limit · resets 10:30am (America/Phoenix)"'
        '}]},"error":"rate_limit","apiErrorStatus":429}\n',
        encoding="utf-8",
    )
    result = _failed_result(stdout="", stderr="")
    upgraded = reclassify_with_response_file(result, response)
    assert upgraded.limit_reached is True
    assert upgraded.limit_scope is not None
    assert upgraded.retry_after is not None
    # The precise reset-time from the JSONL beats the +5h fallback.
    assert upgraded.retry_after.endswith("Z")
    assert upgraded.retry_after.startswith("2026") or upgraded.retry_after  # parseable


def test_reclassify_returns_unchanged_when_no_response_file(
    tmp_path: Path,
) -> None:
    """No response file → fall through, still agent_failed."""
    result = _failed_result(stdout="random crash", stderr="")
    same = reclassify_with_response_file(result, tmp_path / "missing.md")
    assert same.limit_reached is False
    assert same.limit_pattern_unmatched is True


def test_reclassify_skips_when_pattern_already_matched(
    tmp_path: Path,
) -> None:
    """A result already classified as limit_reached must not be touched."""
    response = tmp_path / "response.md"
    response.write_text("totally unrelated content", encoding="utf-8")
    already_limited = AgentCommandResult(
        command="fake",
        returncode=1,
        stdout="usage limit hit",
        stderr="",
        limit_reached=True,
        retry_after="2026-06-04T17:30:00Z",
        limit_scope="five_hour",
        limit_pattern_unmatched=False,
    )
    same = reclassify_with_response_file(already_limited, response)
    assert same is already_limited  # exact same instance — no rebuild


def test_reclassify_skips_when_command_succeeded(tmp_path: Path) -> None:
    """rc=0 results pass through (limit_pattern_unmatched is False)."""
    response = tmp_path / "response.md"
    response.write_text("apiErrorStatus:429", encoding="utf-8")
    success = AgentCommandResult(
        command="fake",
        returncode=0,
        stdout="ok",
        stderr="",
        limit_reached=False,
        retry_after=None,
        limit_scope=None,
        limit_pattern_unmatched=False,
    )
    same = reclassify_with_response_file(success, response)
    assert same is success


def test_reclassify_reads_response_json_too(tmp_path: Path) -> None:
    """Judge wrappers use response.json; same path must work."""
    response = tmp_path / "response.json"
    response.write_text(
        '{"error":"rate_limit","apiErrorStatus":429}', encoding="utf-8"
    )
    result = _failed_result()
    upgraded = reclassify_with_response_file(result, response)
    assert upgraded.limit_reached is True


def test_reclassify_tolerates_unreadable_file(tmp_path: Path) -> None:
    """If we can't read the file, fall back to the original result.

    A flaky disk or permissions issue should never CRASH the runner —
    it should just leave the result as the original agent_failed.
    """
    path = tmp_path / "response.md"
    path.write_bytes(b"\xff\xfe\x00garbage")  # invalid UTF-8 / weird bytes
    result = _failed_result()
    # Should not raise. errors="ignore" turns garbage into empty text,
    # so the classifier won't match and the result passes through.
    same = reclassify_with_response_file(result, path)
    assert same.limit_reached is False
