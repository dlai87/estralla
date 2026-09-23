"""Daily status-issue formatter (design §4.6, review C-B2).

The autonomous pipeline runs unattended, so observability is GitHub-native: a
daily status issue is the operator's dashboard. This module turns a daily-run
summary into an issue title + body. The out-of-band heartbeat (C-B2) is a
separate concern (it must not depend on the same token); this only formats the
in-band summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DailyStatus:
    date: str  # YYYY-MM-DD (passed in)
    merged: int = 0
    quarantined: int = 0
    queue_depth: int = 0
    budget_used: int = 0
    budget_total: int = 0
    auth_skips: int = 0  # ticks that skipped on an auth/API failure
    quarantine_flags: list[str] = field(default_factory=list)


def status_issue_title(s: DailyStatus) -> str:
    health = "⚠️" if (s.quarantined or s.auth_skips) else "✅"
    return f"{health} Pipeline status — {s.date}"


def status_issue_body(s: DailyStatus) -> str:
    budget_pct = f"{(100 * s.budget_used / s.budget_total):.0f}%" if s.budget_total else "n/a"
    lines = [
        f"## Pipeline status — {s.date}",
        "",
        f"- **Merged today:** {s.merged}",
        f"- **Quarantined:** {s.quarantined}",
        f"- **Queue depth:** {s.queue_depth}",
        f"- **Budget used:** {s.budget_used} / {s.budget_total} ({budget_pct})",
        f"- **Auth-skipped ticks:** {s.auth_skips}",
    ]
    if s.auth_skips:
        lines.append("")
        lines.append(
            "> ⚠️ One or more ticks skipped on an auth/API failure. If this persists, "
            "check the runner token (the out-of-band heartbeat should also have alerted)."
        )
    if s.quarantine_flags:
        lines.append("")
        lines.append("### Quarantined artifacts (need attention)")
        lines.append("")
        lines += [f"- {q}" for q in s.quarantine_flags]
    return "\n".join(lines).rstrip() + "\n"
