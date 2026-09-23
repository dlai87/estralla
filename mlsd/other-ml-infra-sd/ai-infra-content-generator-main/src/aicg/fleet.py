"""Fleet status — a read-only roll-up across every curriculum domain.

Roadmap §4 (control plane) starts here: now that the harness runs four
domains (ai-infra + ml-engineering + ai-engineering + ai-governance), an
operator needs one pane that answers "how live is each domain?" without
opening four manifests. This module is the read model; it makes no writes
and no network calls. The pure functions below take already-loaded
manifests so they're trivially testable; the CLI layer does the IO.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .judge import JudgeConfig
from .pipeline_config import PipelineConfig


@dataclass(frozen=True)
class DomainStatus:
    domain: str
    org: str
    role_count: int
    enabled_phases: tuple[str, ...]
    daily_budget: int
    judge_enabled: bool
    judge_flag_only: bool
    freshness_bar: int | None
    queue_depth: int | None  # None = no work-queue state file found

    @property
    def mode(self) -> str:
        """At-a-glance liveness: ACT (writing), OBSERVE (judging, flag-only),
        or INERT (judge off, no write-phases)."""
        if self.enabled_phases:
            return "ACT"
        if self.judge_enabled:
            return "OBSERVE"
        return "INERT"


def build_domain_status(
    domain: str, manifest: Any, queue_depth: int | None = None
) -> DomainStatus:
    """Derive a DomainStatus from a loaded manifest. Pure — no IO."""
    pc = PipelineConfig.from_manifest(manifest)
    jc = JudgeConfig.from_manifest(manifest)
    bar = None
    if jc.thresholds:
        bar = jc.thresholds.get("freshness", jc.thresholds.get("default"))
    return DomainStatus(
        domain=domain,
        org=manifest.org,
        role_count=len(manifest.roles),
        enabled_phases=tuple(pc.enabled_phases()),
        daily_budget=pc.daily_budget,
        judge_enabled=jc.enabled,
        judge_flag_only=jc.flag_only,
        freshness_bar=bar,
        queue_depth=queue_depth,
    )


def read_queue_depth(state_dir: Path) -> int | None:
    """Best-effort: count open items in ``<state_dir>/work-queue.json``.

    Returns None when the file is absent (a domain that hasn't run yet) or
    unreadable, so the fleet view degrades gracefully rather than erroring.
    """
    qpath = state_dir / "work-queue.json"
    if not qpath.is_file():
        return None
    try:
        data = json.loads(qpath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return None
    open_states = {"queued", "pending", "open", "in_progress", "ready"}
    counted = [
        it for it in items
        if not isinstance(it, dict) or it.get("status", "queued") in open_states
    ]
    return len(counted)


def render_fleet_table(statuses: list[DomainStatus]) -> str:
    """Render a fixed-width table of the fleet. Pure formatting."""
    header = (
        f"{'DOMAIN':<16} {'ORG':<26} {'ROLES':>5} {'MODE':<8} "
        f"{'PHASES':<22} {'JUDGE':<14} {'BAR':>4} {'BUDGET':>6} {'QUEUE':>6}"
    )
    lines = ["Fleet status — AI Career Curriculum ecosystem", "", header, "-" * len(header)]
    for s in sorted(statuses, key=lambda d: d.domain):
        phases = ",".join(s.enabled_phases) if s.enabled_phases else "—"
        judge = (
            f"{'on' if s.judge_enabled else 'off'}"
            + (" (flag)" if s.judge_enabled and s.judge_flag_only else "")
        )
        bar = str(s.freshness_bar) if s.freshness_bar is not None else "—"
        queue = "—" if s.queue_depth is None else str(s.queue_depth)
        lines.append(
            f"{s.domain:<16} {s.org:<26} {s.role_count:>5} {s.mode:<8} "
            f"{phases:<22} {judge:<14} {bar:>4} {s.daily_budget:>6} {queue:>6}"
        )
    total_roles = sum(s.role_count for s in statuses)
    act = sum(1 for s in statuses if s.mode == "ACT")
    observe = sum(1 for s in statuses if s.mode == "OBSERVE")
    inert = sum(1 for s in statuses if s.mode == "INERT")
    lines.append("")
    lines.append(
        f"{len(statuses)} domains · {total_roles} roles · "
        f"{act} ACT / {observe} OBSERVE / {inert} INERT"
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class DigestRow:
    domain: str
    mode: str
    bar: int | None
    filled: int  # roles with authored modules
    total: int


def render_fleet_digest(rows: list[DigestRow], *, date: str = "") -> str:
    """One compact daily summary line per domain + a fleet total. Pure.

    Built for an ntfy push — short, scannable: filled/total roles, mode, BAR.
    """
    head = f"AICG fleet{(' — ' + date) if date else ''}"
    lines = [head]
    tf = tt = 0
    for r in sorted(rows, key=lambda x: x.domain):
        tf += r.filled
        tt += r.total
        bar = f" · BAR {r.bar}" if r.bar is not None else ""
        lines.append(f"{r.domain}: {r.filled}/{r.total} filled · {r.mode}{bar}")
    pct = round(100 * tf / tt) if tt else 0
    lines.append(f"Total: {tf}/{tt} roles ({pct}%) authored")
    return "\n".join(lines)


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def render_fleet_html(statuses: list[DomainStatus], *, generated_at: str = "") -> str:
    """Render the fleet status as a self-contained static HTML dashboard.

    The web form of the §4 control plane's read model — same data as
    ``render_fleet_table``, no external assets, no network. Read-only: it
    surfaces state; promotion/control writes stay in the CLI behind the
    operator. ``generated_at`` is passed in (no clock here).
    """
    mode_color = {"ACT": "#7ee787", "OBSERVE": "#f0883e", "INERT": "#8b949e"}
    rows = []
    for s in sorted(statuses, key=lambda d: d.domain):
        phases = ", ".join(s.enabled_phases) if s.enabled_phases else "—"
        judge = ("on" if s.judge_enabled else "off") + (
            " · flag-only" if s.judge_enabled and s.judge_flag_only else ""
        )
        bar = str(s.freshness_bar) if s.freshness_bar is not None else "—"
        queue = "—" if s.queue_depth is None else str(s.queue_depth)
        color = mode_color.get(s.mode, "#8b949e")
        rows.append(
            "<tr>"
            f'<td class="dom">{_esc(s.domain)}</td>'
            f'<td class="org">{_esc(s.org)}</td>'
            f'<td class="num">{s.role_count}</td>'
            f'<td><span class="badge" style="--c:{color}">{s.mode}</span></td>'
            f"<td>{_esc(phases)}</td><td>{_esc(judge)}</td>"
            f'<td class="num">{bar}</td><td class="num">{s.daily_budget}</td>'
            f'<td class="num">{queue}</td>'
            "</tr>"
        )
    total_roles = sum(s.role_count for s in statuses)
    act = sum(1 for s in statuses if s.mode == "ACT")
    observe = sum(1 for s in statuses if s.mode == "OBSERVE")
    inert = sum(1 for s in statuses if s.mode == "INERT")
    stamp = f"<p class='stamp'>Generated {_esc(generated_at)}</p>" if generated_at else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AICG Fleet Status</title>
<style>
  :root {{ --bg:#0f1419; --surface:#161b22; --ink:#e6edf3; --dim:#8b949e; --rule:#1f2630; --accent:#79c0ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.5 ui-monospace,'JetBrains Mono',Menlo,monospace; padding:32px; }}
  h1 {{ font-size:1.4rem; color:var(--accent); margin:0 0 4px; }}
  .summary {{ color:var(--dim); margin:0 0 24px; }}
  .stamp {{ color:var(--dim); font-size:12px; margin:0 0 24px; }}
  table {{ border-collapse:collapse; width:100%; background:var(--surface);
    border:1px solid var(--rule); border-radius:8px; overflow:hidden; }}
  th,td {{ text-align:left; padding:10px 14px; border-bottom:1px solid var(--rule); }}
  th {{ color:var(--dim); text-transform:uppercase; letter-spacing:.08em; font-size:11px; }}
  tr:last-child td {{ border-bottom:none; }}
  td.num {{ text-align:right; }}
  td.dom {{ color:var(--accent); }}
  td.org {{ color:var(--dim); }}
  .badge {{ display:inline-block; padding:2px 10px; border-radius:999px;
    color:var(--c); border:1px solid var(--c); font-size:12px; }}
</style></head>
<body>
  <h1>AICG Fleet Status</h1>
  <p class="summary">{len(statuses)} domains · {total_roles} roles · {act} ACT / {observe} OBSERVE / {inert} INERT</p>
  {stamp}
  <table>
    <thead><tr>
      <th>Domain</th><th>Org</th><th>Roles</th><th>Mode</th>
      <th>Phases</th><th>Judge</th><th>BAR</th><th>Budget</th><th>Queue</th>
    </tr></thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body></html>
"""
