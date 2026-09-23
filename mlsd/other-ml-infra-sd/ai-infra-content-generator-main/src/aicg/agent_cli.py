"""Local subscription CLI execution helpers for Claude and Codex."""

from __future__ import annotations

import dataclasses
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

LIMIT_PATTERNS = (
    "usage limit",
    "rate limit",
    "limit reached",
    "quota exceeded",
    "session limit",
    "weekly limit",
    "5-hour",
    "5 hour",
    "try again",
    "too many requests",
    # Claude Code session-limit JSONL fingerprints. The wrappers under
    # scripts/ redirect the CLI's stdout to a response file (response.md
    # / response.json) so the runner's captured stdout is empty when
    # the CLI silently exits on the limit. We pick up the JSONL line
    # via reclassify_with_response_file, which extends the text passed
    # to classify_limit_scope.
    "\"apierrorstatus\":429",
    "\"error\":\"rate_limit\"",
    "isapierrormessage",
)

# Pattern in the user-facing JSONL text:
#   "You've hit your session limit · resets 10:30am (America/Phoenix)"
# Captures the wall-clock retry time + timezone so we can convert it to
# an absolute ISO timestamp instead of falling back to "+5 hours".
_RESETS_RE = re.compile(
    r"resets\s+(\d{1,2}):(\d{2})\s*(am|pm)\s*(?:\(([^)]+)\))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AgentCommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    limit_reached: bool
    retry_after: str | None
    limit_scope: str | None
    limit_pattern_unmatched: bool = False


class AgentLimitReached(RuntimeError):
    def __init__(self, result: AgentCommandResult):
        self.result = result
        super().__init__(
            f"Agent subscription limit reached; retry after {result.retry_after or 'later'}."
        )


def run_agent_command(command: str, cwd: Path) -> AgentCommandResult:
    completed = subprocess.run(
        shlex.split(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    limit_scope = classify_limit_scope(output)
    limit_reached = completed.returncode != 0 and limit_scope is not None
    # When the command failed but no known limit-pattern matched the
    # output, surface that as a separate signal so operators can extend
    # LIMIT_PATTERNS when vendors change their error wording.
    limit_pattern_unmatched = completed.returncode != 0 and limit_scope is None
    return AgentCommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
        limit_reached=limit_reached,
        retry_after=retry_after_for_scope(limit_scope) if limit_scope else None,
        limit_scope=limit_scope,
        limit_pattern_unmatched=limit_pattern_unmatched,
    )


def classify_limit_scope(output: str) -> str | None:
    text = output.lower()
    if not any(pattern in text for pattern in LIMIT_PATTERNS):
        return None
    if "weekly" in text:
        return "weekly"
    if "5-hour" in text or "5 hour" in text or "five hour" in text:
        return "five_hour"
    return "unknown"


def retry_after_for_scope(scope: str) -> str:
    now = datetime.now(timezone.utc)
    if scope == "weekly":
        retry_at = now + timedelta(days=7)
    elif scope == "five_hour":
        retry_at = now + timedelta(hours=5)
    else:
        retry_at = now + timedelta(hours=6)
    return retry_at.isoformat(timespec="seconds").replace("+00:00", "Z")


def retry_after_has_passed(value: str | None) -> bool:
    if not value:
        return True
    try:
        retry_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) >= retry_at


def parse_resets_clause(text: str, *, now: datetime | None = None) -> str | None:
    """Extract a precise retry_after from the JSONL ``resets HH:MMam (TZ)`` clause.

    The Claude Code session-limit message includes the wall-clock time
    when the budget resets, e.g. ``"resets 10:30am (America/Phoenix)"``.
    When present, that beats the ``retry_after_for_scope`` fallback
    (which always rounds to +5/+6/+7 days) because the runner can wake
    up the moment the limit lifts instead of overshooting.

    Returns an ISO-8601 UTC string ending in ``Z``, or ``None`` if no
    parseable ``resets`` clause is found.
    """
    match = _RESETS_RE.search(text)
    if match is None:
        return None
    hour = int(match.group(1)) % 12
    if match.group(3).lower() == "pm":
        hour += 12
    minute = int(match.group(2))
    tz_name = (match.group(4) or "").strip()
    base_tz = _resolve_tz(tz_name)
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone(base_tz)
    candidate = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # If the candidate is already in the past (now is 11am, reset said
    # 10:30am) the message refers to tomorrow's reset.
    if candidate <= local_now:
        candidate = candidate + timedelta(days=1)
    return (
        candidate.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _resolve_tz(name: str):
    if not name:
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except (ImportError, Exception):  # noqa: BLE001 - any tz lookup failure → UTC
        return timezone.utc


def reclassify_with_response_file(
    result: AgentCommandResult, *response_paths: Path
) -> AgentCommandResult:
    """Re-classify a failed result by also reading agent response files.

    The wrappers in ``scripts/run-claude-*.sh`` redirect the CLI's
    stdout to a file (``$OUTPUT_DIR/response.{md,json}``). When the
    CLI hits its session limit, the JSONL line carrying
    ``"apiErrorStatus": 429`` ends up in that file, not in the
    subprocess's stdout. Without this helper the runner sees rc=1 +
    empty stderr + clean stdout and reports ``agent_failed`` (the
    Bug 2 symptom on 2026-06-01).

    Only re-classifies when ``result.limit_pattern_unmatched`` is set
    — i.e., the original classifier already failed to find a pattern.
    Successful runs pass through unchanged.
    """
    if not result.limit_pattern_unmatched:
        return result

    combined = result.stdout + "\n" + result.stderr
    for path in response_paths:
        if not path.exists():
            continue
        try:
            # Cap at 32KB per file — enough to catch the JSONL line at
            # the tail of an interrupted response without OOM'ing if a
            # wrapper happened to log a multi-MB transcript.
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        combined += "\n" + text[-32_000:]

    scope = classify_limit_scope(combined)
    if scope is None:
        return result
    precise_retry = parse_resets_clause(combined)
    return dataclasses.replace(
        result,
        limit_reached=True,
        retry_after=precise_retry or retry_after_for_scope(scope),
        limit_scope=scope,
        limit_pattern_unmatched=False,
    )
