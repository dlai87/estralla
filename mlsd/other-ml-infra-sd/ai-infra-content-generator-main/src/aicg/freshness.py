"""Content-freshness audits for committed curriculum repos.

Three review passes live here, ordered from cheapest to most expensive:

1. :func:`audit_links` — HEAD-pings every external URL in every committed
   markdown file. Pure HTTP, no LLM. Catches link rot, redirects, and
   404s deterministically.

2. :func:`audit_versions` — greps committed text against a curated
   registry of "current target versions" (PyTorch, CUDA, hardware,
   etc.) and flags stale pins. Pure regex, no LLM.

3. :func:`review_existing_artifacts` — invokes the configured judge in
   "freshness" mode on existing committed artifacts. Catches semantic
   staleness that grep can't (deprecated APIs, superseded best
   practices, outdated cost claims). Heavier — burns judge credits.

All three emit ``WorkItem``-shaped findings that the org runner can
splice into the work-queue alongside structural gaps. Severity flows
out so the priority weighter can promote critical staleness above
new-content gaps when warranted.
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .state import utc_now, write_json

FRESHNESS_LINKS_REPORT = "freshness-links-report.json"
FRESHNESS_VERSIONS_REPORT = "freshness-versions-report.json"
FRESHNESS_REVIEW_REPORT = "freshness-review-report.json"
# Per-repo rotation state. Tracks last-scanned timestamp + score for
# every artifact ever judged so per-night runs can skip files still
# within their cooldown window and prioritize least-recently-scanned
# files first. Without this, max_artifacts always hits the
# alphabetically-first N files and never reaches the tail.
FRESHNESS_SCAN_HISTORY = "freshness-scan-history.json"
FRESHNESS_SCAN_HISTORY_SCHEMA_VERSION = 1

# Files that count as "reviewable artifacts" — module READMEs, lecture
# notes, exercise solutions, project solutions. We deliberately skip
# CHANGELOGs, README at repo root, VERSIONS, etc. — those rot less and
# editing them via freshness review would conflict with the propagate
# step's rules.
_REVIEWABLE_GLOBS = (
    "modules/*/SOLUTION.md",
    "modules/*/README.md",
    "modules/*/exercise-*/SOLUTION.md",
    "lessons/*/README.md",
    "lessons/*/lecture-notes/*.md",
    "lessons/*/exercises/*.md",
    "projects/*/SOLUTION.md",
    "projects/*/STEP_BY_STEP.md",
    "projects/*/README.md",
)

# Markdown link patterns: [text](url), <url>, bare URLs in code.
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*?\]\((https?://[^\s)]+)\)")
_AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
_BARE_URL_RE = re.compile(r"(?<![\(\[\<])(https?://[^\s\)\]\>]+)")

_SKIP_DIRS = {".git", ".aicg", "node_modules", "_archive", ".venv"}
_MD_EXTENSIONS = {".md", ".mdx"}

# Trailing characters that often glom onto URLs in markdown prose but are
# never part of the URL itself. Includes the quote characters that show
# up when a URL is the value of a JSON/YAML string in a code sample —
# the audit was picking up ``http://x/y"`` and flagging it broken.
_URL_TRAILING_STRIP = '.,;:!?"\'}'
# Example / reserved hosts that should never be treated as live external
# links. RFC 2606 (.example/.test/.invalid/.localhost TLDs and the
# example.com/.net/.org domains), the loopback range, link-local, and
# the common ``your-foo`` / ``my-foo`` placeholder prefixes curriculum
# docs use in code samples. Real users of the curriculum should not
# expect any of these to resolve.
_RESERVED_TLDS = (".example", ".test", ".invalid", ".localhost")
_RESERVED_EXAMPLE_HOSTS = frozenset(
    {"example.com", "example.net", "example.org",
     "localhost", "0.0.0.0", "127.0.0.1",
     # Docker desktop & docker-compose default-bridge aliases.
     "host.docker.internal", "gateway.docker.internal",
     # Curriculum-wide placeholder domains used in SRE / runbook /
     # incident-response examples. Not RFC-reserved but treated
     # identically here — code samples constantly cite
     # ``https://wiki.company.com/...``, ``https://runbooks.mycompany.com``.
     "company.com", "mycompany.com", "yourcompany.com",
     "acme.com", "acme.org"}
)
_PLACEHOLDER_HOST_RE = re.compile(
    r"^(your|my|some|sample|placeholder)[-.]", re.IGNORECASE
)
# Kubernetes service DNS — never reachable from a public link checker.
# Covers the canonical fully-qualified form (svc.cluster.local), the
# truncated within-namespace form (.svc), and the search-path-resolved
# form (.cluster.local).
_K8S_DNS_SUFFIXES = (
    ".svc.cluster.local",
    ".cluster.local",
    ".svc",
)
# Template placeholders that survive into URL text — $VAR, ${VAR},
# $(cmd), <PLACEHOLDER>, {{ var }}. Checked across the WHOLE URL, not
# just the host, because curriculum docs often build URLs in code
# samples like ``curl -O https://dl.k8s.io/release/$(curl -s ...)``
# where the shell substitution is in the path.
_PLACEHOLDER_URL_RE = re.compile(
    r"\$\{?[A-Z_]|\$\(|<[A-Za-z_][\w-]*>|\{\{"
)
# Slack webhook stub. Real Slack webhooks look like
# /services/T0123/B0123/abc — the placeholder convention is
# /YOUR/SLACK/WEBHOOK or /WORKSPACE/CHANNEL/TOKEN. We match the
# upper-case stub words anywhere in the path.
_UPPER_PLACEHOLDER_PATH_RE = re.compile(
    r"/(YOUR|YOU|MYORG|MYREPO|MY-ORG|MY-REPO|ORIGINAL-OWNER|YOUR-USERNAME|"
    r"YOUR-ORG|YOUR-REPO|YOUR-TOKEN|TOKEN|SLACK|WEBHOOK|CHANNEL|WORKSPACE)"
    r"(/|$)"
)
# github.com placeholder owners. Singular generic stand-ins used in
# git tutorials: ``github.com/user/repo.git``, ``github.com/myorg/myrepo``.
# Case-insensitive — covers ``YOU`` / ``YOUR-USERNAME`` too.
_GITHUB_PLACEHOLDER_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/"
    r"(user|username|myorg|my-org|myrepo|my-repo|original-owner|your-?username)"
    r"(/|$)",
    re.IGNORECASE,
)

DEFAULT_LINK_TIMEOUT = 8.0
DEFAULT_LINK_WORKERS = 16
DEFAULT_LINK_USER_AGENT = "AICG-link-checker/1.0 (+https://github.com/AI-Infra-Curriculum)"

# Severity thresholds (per file) for link rot.
_SEV_HIGH_BROKEN = 5
_SEV_MEDIUM_BROKEN = 2


class FreshnessError(RuntimeError):
    """Raised when a freshness audit cannot proceed."""


# Substrings that mean "the hostname does not resolve". These are
# almost always template placeholders / k8s service shortnames /
# docker-compose service names that survived into prose URLs — never
# real broken citations. The audit's collection-time _is_example_url
# catches most of them, but the long tail (e.g. ``<svc>.<namespace>``
# k8s shorthand) only fails at fetch time. Treating DNS-failure as
# "not broken" silently drops those.
_DNS_FAILURE_MARKERS = (
    "name or service not known",
    "nodename nor servname",
    "getaddrinfo failed",
    "temporary failure in name resolution",
    "no address associated with hostname",
    "[errno -2]",
    "[errno -3]",
    "[errno 8]",
    "[errno 11001]",
)


@dataclass(frozen=True)
class LinkFinding:
    file_path: str
    url: str
    status: int | None
    reason: str

    def is_broken(self) -> bool:
        if self.status is None:
            # status=None means the fetch never got a response.
            # Distinguish DNS-resolution failures (placeholder URLs)
            # from real network errors (server down / timeout).
            reason_lower = (self.reason or "").lower()
            if any(marker in reason_lower for marker in _DNS_FAILURE_MARKERS):
                return False
            return True
        # 403 / 405 / 429 / 451 / 999 are server-side denials of the
        # audit's HEAD request — they prove the URL is REACHABLE, not
        # broken. (LinkedIn returns 999 for the same reason.) The
        # whole point of audit-links is to find dead citations; a
        # citation a learner can click and read but the bot can't is
        # still valid curriculum content.
        if self.status in {403, 405, 429, 451, 999}:
            return False
        return self.status >= 400 or self.status in {301, 308}


# ---------------------------------------------------------------------------
# Link checker
# ---------------------------------------------------------------------------


def audit_links(
    repo_path: Path,
    *,
    timeout: float = DEFAULT_LINK_TIMEOUT,
    max_workers: int = DEFAULT_LINK_WORKERS,
    write_report: bool = True,
    url_fetcher=None,
) -> dict[str, Any]:
    """HEAD-ping every external URL in every committed .md file.

    Parameters mirror real-world tuning knobs; ``url_fetcher`` exists so
    tests can stub the network call entirely.
    """
    repo_path = Path(repo_path).resolve()
    if not repo_path.exists():
        raise FreshnessError(f"Repo does not exist: {repo_path}")

    fetch = url_fetcher or _default_url_fetcher(timeout)
    urls_by_file = _collect_markdown_urls(repo_path)

    findings: list[LinkFinding] = []
    unique_urls = sorted({url for urls in urls_by_file.values() for url in urls})
    results: dict[str, tuple[int | None, str]] = {}
    if unique_urls:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_url = {pool.submit(fetch, url): url for url in unique_urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    status, reason = future.result()
                except Exception as exc:  # noqa: BLE001
                    status, reason = None, f"fetch-error: {exc}"
                results[url] = (status, reason)

    for file_rel, urls in urls_by_file.items():
        for url in urls:
            status, reason = results.get(url, (None, "unfetched"))
            findings.append(
                LinkFinding(
                    file_path=file_rel,
                    url=url,
                    status=status,
                    reason=reason,
                )
            )

    broken = [f for f in findings if f.is_broken()]
    per_file = _aggregate_per_file(broken)
    work_items = _link_findings_to_work_items(repo_path.name, per_file)

    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "operation": "freshness_links",
        "repo": repo_path.name,
        "files_scanned": len(urls_by_file),
        "urls_unique": len(unique_urls),
        "broken_count": len(broken),
        "broken_findings": [_finding_dict(f) for f in broken],
        "work_items": work_items,
    }
    if write_report:
        (repo_path / ".aicg").mkdir(parents=True, exist_ok=True)
        write_json(repo_path / ".aicg" / FRESHNESS_LINKS_REPORT, report)
    return report


# ---------------------------------------------------------------------------
# Version-pin scanner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VersionTarget:
    """A single curated entry from version-targets.yaml.

    Example::

        - id: pytorch
          name: PyTorch
          current: "3.0"
          deprecated:
            - "2.0"
            - "2.1"
            - "2.2"
          pattern: "(?i)pytorch[\\s=:]*([0-9]+(?:\\.[0-9]+)?)"
    """

    id: str
    name: str
    current: str
    deprecated: tuple[str, ...]
    pattern: re.Pattern[str]
    eol: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "VersionTarget":
        return cls(
            id=str(raw["id"]),
            name=str(raw.get("name", raw["id"])),
            current=str(raw.get("current", "")),
            deprecated=tuple(str(v) for v in raw.get("deprecated", [])),
            pattern=re.compile(str(raw["pattern"])),
            eol=bool(raw.get("eol", False)),
        )


@dataclass(frozen=True)
class VersionFinding:
    file_path: str
    target_id: str
    matched_version: str
    line_number: int
    excerpt: str
    severity: str


def load_version_targets(registry_path: Path) -> list[VersionTarget]:
    """Load curated version targets from a YAML/JSON registry."""
    if not registry_path.exists():
        raise FreshnessError(f"version-targets registry not found: {registry_path}")
    from .config_loader import load_config  # local import to avoid cycle

    raw = load_config(registry_path)
    items = raw.get("targets", []) if isinstance(raw, dict) else raw
    return [VersionTarget.from_dict(item) for item in items if isinstance(item, dict)]


def audit_versions(
    repo_path: Path,
    *,
    targets: list[VersionTarget] | None = None,
    registry_path: Path | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    """Scan committed text for stale version pins per the registry."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.exists():
        raise FreshnessError(f"Repo does not exist: {repo_path}")
    if targets is None:
        if registry_path is None:
            raise FreshnessError("Pass either targets= or registry_path=.")
        targets = load_version_targets(registry_path)

    findings: list[VersionFinding] = []
    for md_path in _iter_markdown_files(repo_path):
        rel = md_path.relative_to(repo_path).as_posix()
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for target in targets:
                for match in target.pattern.finditer(line):
                    raw_version = (match.group(1) if match.groups() else match.group(0)).strip()
                    severity = _classify_version_severity(raw_version, target)
                    if severity is None:
                        continue
                    findings.append(
                        VersionFinding(
                            file_path=rel,
                            target_id=target.id,
                            matched_version=raw_version,
                            line_number=line_no,
                            excerpt=line.strip()[:200],
                            severity=severity,
                        )
                    )

    work_items = _version_findings_to_work_items(repo_path.name, findings, targets)
    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "operation": "freshness_versions",
        "repo": repo_path.name,
        "target_count": len(targets),
        "finding_count": len(findings),
        "findings": [_version_finding_dict(f) for f in findings],
        "work_items": work_items,
    }
    if write_report:
        (repo_path / ".aicg").mkdir(parents=True, exist_ok=True)
        write_json(repo_path / ".aicg" / FRESHNESS_VERSIONS_REPORT, report)
    return report


# ---------------------------------------------------------------------------
# LLM freshness review
# ---------------------------------------------------------------------------


def review_existing_artifacts(
    repo_path: Path,
    *,
    judge_config,
    max_artifacts: int | None = None,
    write_report: bool = True,
    artifact_judge=None,
    runner_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Invoke the freshness judge on existing committed artifacts.

    ``artifact_judge`` lets tests stub the network call; in production
    it defaults to :func:`aicg.judge.judge_artifact_freshness`.

    Artifact selection now honors a per-repo scan-history file
    (``.aicg/freshness-scan-history.json``):

    * Files scanned within ``judge_config.freshness_cooldown_days`` are
      dropped from the candidate list. The default is 90 days, so each
      file gets re-judged ~quarterly.
    * Remaining candidates are sorted by ``(last_scanned, path)`` —
      least-recently-scanned (and never-scanned) come first.
    * ``max_artifacts`` is applied AFTER the cooldown + sort, so the
      cap rotates fairly across the corpus instead of always re-judging
      the alphabetical front.

    The history is updated after each judge call (mid-batch, before
    a subscription-limit defer would otherwise break us) so deferred
    files become eligible again immediately.
    """
    repo_path = Path(repo_path).resolve()
    if not repo_path.exists():
        raise FreshnessError(f"Repo does not exist: {repo_path}")

    if artifact_judge is None:
        from .judge import judge_artifact_freshness

        artifact_judge = judge_artifact_freshness

    now = now or datetime.now(timezone.utc)
    cooldown_days = getattr(judge_config, "freshness_cooldown_days", 90)
    history = _load_scan_history(repo_path)

    all_artifacts = _collect_reviewable_artifacts(repo_path)
    eligible = _filter_by_cooldown(all_artifacts, history, cooldown_days, now)
    eligible = _sort_by_least_recently_scanned(eligible, history)
    cap = len(eligible) if max_artifacts is None else max_artifacts
    artifacts = eligible[:cap]
    skipped_for_cooldown = len(all_artifacts) - len(eligible)

    role_findings: list[dict[str, Any]] = []
    work_items: list[dict[str, Any]] = []
    deferred: dict[str, Any] | None = None
    history_updated = False

    for artifact_rel in artifacts:
        artifact_id = _slug(artifact_rel)
        artifact_path = repo_path / artifact_rel
        verdict = artifact_judge(
            repo_path=repo_path,
            artifact_path=artifact_path,
            artifact_id=artifact_id,
            config=judge_config,
            runner_root=runner_root,
        )
        entry = {"artifact": artifact_rel, "artifact_id": artifact_id}
        if verdict is None:
            entry["status"] = "skipped"
            entry["reason"] = "judge disabled or unconfigured"
            role_findings.append(entry)
            # Judge-disabled is not a real scan — do NOT update history
            # or we'd lock the file out for 90 days while the judge is
            # off and miss the first real cycle after it's turned on.
            continue
        entry["score"] = verdict.score
        entry["passed"] = verdict.passed
        entry["dimensions"] = dict(verdict.dimensions)
        entry["blockers"] = list(verdict.blockers)
        entry["summary"] = verdict.summary
        # Detect subscription-limit defer.
        if any("subscription limit" in (b or "").lower() for b in verdict.blockers):
            entry["status"] = "deferred"
            deferred = entry
            role_findings.append(entry)
            break
        if not verdict.passed:
            entry["status"] = "stale"
            severity = _review_severity(verdict)
            entry["severity"] = severity
            # Flag-only mode reports the staleness but enqueues no repair —
            # full visibility, zero autonomous action (design doc P0).
            if getattr(judge_config, "flag_only", False):
                entry["flagged_only"] = True
            else:
                work_items.append(
                    {
                        "id": f"refresh-stale-{artifact_id}",
                        "repo": repo_path.name,
                        "type": "refresh_stale",
                        "severity": severity,
                        "path": artifact_rel,
                        "title": f"Refresh stale content in {artifact_rel}",
                        "score": verdict.score,
                        "blockers": list(verdict.blockers),
                        "summary": verdict.summary,
                    }
                )
        else:
            entry["status"] = "ok"
        role_findings.append(entry)
        history[artifact_rel] = {
            "last_scanned": now.isoformat().replace("+00:00", "Z"),
            "last_score": verdict.score,
            "last_passed": bool(verdict.passed),
        }
        history_updated = True

    if history_updated:
        _save_scan_history(repo_path, history, now)

    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "operation": "freshness_review",
        "repo": repo_path.name,
        "artifacts_reviewed": len(role_findings),
        "eligible_count": len(eligible),
        "skipped_for_cooldown": skipped_for_cooldown,
        "stale_count": sum(1 for e in role_findings if e.get("status") == "stale"),
        "deferred": deferred,
        "findings": role_findings,
        "work_items": work_items,
    }
    if write_report:
        (repo_path / ".aicg").mkdir(parents=True, exist_ok=True)
        write_json(repo_path / ".aicg" / FRESHNESS_REVIEW_REPORT, report)
    return report


def _load_scan_history(repo_path: Path) -> dict[str, dict[str, Any]]:
    """Load the per-repo scan history.

    Returns an empty dict if the file is missing, unreadable, or has a
    schema version we don't recognize. We never throw on history-load
    failure — losing rotation state is preferable to skipping a review
    cycle entirely, and the file will be rewritten cleanly on save.
    """
    path = repo_path / ".aicg" / FRESHNESS_SCAN_HISTORY
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("schema_version") != FRESHNESS_SCAN_HISTORY_SCHEMA_VERSION:
        return {}
    files = payload.get("files")
    if not isinstance(files, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, value in files.items():
        if isinstance(key, str) and isinstance(value, dict):
            out[key] = value
    return out


def _save_scan_history(
    repo_path: Path, history: dict[str, dict[str, Any]], now: datetime
) -> None:
    payload = {
        "schema_version": FRESHNESS_SCAN_HISTORY_SCHEMA_VERSION,
        "updated_at": now.isoformat().replace("+00:00", "Z"),
        "files": history,
    }
    (repo_path / ".aicg").mkdir(parents=True, exist_ok=True)
    write_json(repo_path / ".aicg" / FRESHNESS_SCAN_HISTORY, payload)


def _filter_by_cooldown(
    artifacts: list[str],
    history: dict[str, dict[str, Any]],
    cooldown_days: int,
    now: datetime,
) -> list[str]:
    """Drop artifacts scanned more recently than the cooldown window."""
    if cooldown_days <= 0:
        return list(artifacts)
    cutoff = now - timedelta(days=cooldown_days)
    out: list[str] = []
    for rel in artifacts:
        entry = history.get(rel) or {}
        last = _parse_iso_timestamp(entry.get("last_scanned"))
        if last is not None and last > cutoff:
            continue
        out.append(rel)
    return out


def _sort_by_least_recently_scanned(
    artifacts: list[str], history: dict[str, dict[str, Any]]
) -> list[str]:
    """Sort by ``(last_scanned, path)`` ascending — never-scanned first.

    Stable, deterministic, and tie-broken by alphabetical path so the
    ordering is reproducible across nights when many files share the
    same last_scanned timestamp (e.g. first cycle after the judge
    becomes enabled).
    """
    def key(rel: str) -> tuple[int, str, str]:
        entry = history.get(rel) or {}
        raw = entry.get("last_scanned")
        if not isinstance(raw, str):
            return (0, "", rel)  # never-scanned: highest priority
        return (1, raw, rel)
    return sorted(artifacts, key=key)


def _parse_iso_timestamp(raw: Any) -> datetime | None:
    if not isinstance(raw, str):
        return None
    text = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _collect_reviewable_artifacts(repo_path: Path) -> list[str]:
    paths: set[str] = set()
    for pattern in _REVIEWABLE_GLOBS:
        for match in repo_path.glob(pattern):
            if not match.is_file():
                continue
            if any(part in _SKIP_DIRS for part in match.parts):
                continue
            paths.add(match.relative_to(repo_path).as_posix())
    return sorted(paths)


def _review_severity(verdict) -> str:
    if verdict.blockers:
        return "high"
    if verdict.score < 50:
        return "high"
    if verdict.score < 70:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _default_url_fetcher(timeout: float):
    def _fetch(url: str) -> tuple[int | None, str]:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": DEFAULT_LINK_USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.reason or "ok"
        except urllib.error.HTTPError as exc:
            return exc.code, str(exc.reason or exc)
        except urllib.error.URLError as exc:
            return None, f"url-error: {exc.reason}"
        except TimeoutError:
            return None, "timeout"
        except OSError as exc:
            return None, f"os-error: {exc}"

    return _fetch


def _iter_markdown_files(repo_path: Path) -> Iterable[Path]:
    for path in repo_path.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _MD_EXTENSIONS:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _collect_markdown_urls(repo_path: Path) -> dict[str, list[str]]:
    urls_by_file: dict[str, list[str]] = {}
    for md_path in _iter_markdown_files(repo_path):
        rel = md_path.relative_to(repo_path).as_posix()
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        urls: list[str] = []
        for pattern in (_MARKDOWN_LINK_RE, _AUTOLINK_RE, _BARE_URL_RE):
            for match in pattern.finditer(text):
                url = match.group(1).rstrip(_URL_TRAILING_STRIP)
                if not url or _is_example_url(url):
                    continue
                if url not in urls:
                    urls.append(url)
        if urls:
            urls_by_file[rel] = urls
    return urls_by_file


def _is_example_url(url: str) -> bool:
    """True for URLs that are reserved / example / placeholder hosts.

    These show up everywhere in curriculum code samples
    (``http://localhost:8000/api``, ``https://your-api.example.com``,
    ``http://${INGRESS_IP}/health``, ``http://backend-service:8080``)
    and the audit should never flag them as broken external links —
    they're teaching scaffolding, not real citations.

    Coverage:
      * RFC 2606 reserved TLDs (.example, .test, .invalid, .localhost)
        and the example.com/.net/.org domains
      * localhost / 0.0.0.0 / 127.0.0.1 / docker host aliases
      * Private + link-local IPv4 ranges (10/8, 192.168/16, 172.16/12,
        169.254/16)
      * Hosts whose name starts with ``your-``, ``my-``, ``some-``,
        ``sample-``, ``placeholder-``
      * Kubernetes / docker-compose service DNS:
        - any *.svc.cluster.local / *.cluster.local / *.svc
        - any host with no dot (bare service name like ``db`` or
          ``backend-service`` only used inside a compose network)
      * URLs containing un-substituted template tokens: ``$VAR``,
        ``${VAR}``, ``<PLACEHOLDER>``, ``{{ var }}``
      * URLs with empty hostnames (``http://:8000/...``)
    """
    if not url.startswith(("http://", "https://")):
        return False
    # Template tokens anywhere in the URL → never a real fetchable URL.
    if _PLACEHOLDER_URL_RE.search(url):
        return True
    # Slack webhook / GitHub fork stubs use upper-case placeholder words
    # in the path. Curriculum docs use these constantly for "fill in
    # your own ID here" prose; never a real citation.
    if _UPPER_PLACEHOLDER_PATH_RE.search(url):
        return True
    # GitHub-specific placeholder owners (case-insensitive).
    if _GITHUB_PLACEHOLDER_RE.match(url):
        return True
    # Use urllib.parse so userinfo (admin:admin@), ports, and IPv6 are
    # handled correctly. The old split-based parser misread
    # ``http://admin:admin@localhost:3000`` as host=``admin``.
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        # Empty hostname means the URL is unmistakably a stub
        # (``http://:8000/path``). Never reachable.
        return True
    if host in _RESERVED_EXAMPLE_HOSTS:
        return True
    # Suffix match against the example.com/.net/.org family — covers
    # subdomains like ``staging.example.com`` and ``my-svc.example.org``
    # which are routine in cohort exercises (the RFC 2606 reservations
    # apply to the whole subtree, not just the apex).
    for reserved in _RESERVED_EXAMPLE_HOSTS:
        if "." in reserved and host.endswith("." + reserved):
            return True
    if any(host == tld[1:] or host.endswith(tld) for tld in _RESERVED_TLDS):
        return True
    if any(host.endswith(suffix) for suffix in _K8S_DNS_SUFFIXES):
        return True
    if _PLACEHOLDER_HOST_RE.match(host):
        return True
    # Bare hostnames (no dot) can never be reached from a public
    # link checker. Curriculum code samples use them constantly for
    # docker-compose service names (``db``, ``api``,
    # ``backend-service``) and k8s service short names.
    # IPv4 numeric literals always contain dots (10.0.0.1), so this
    # rule never catches a real address.
    if "." not in host:
        return True
    # Private + link-local IPv4 ranges — curriculum code samples often
    # use these as stand-in addresses. Never reachable from the audit
    # runner anyway.
    if re.match(r"^10\.\d+\.\d+\.\d+$", host):
        return True
    if re.match(r"^192\.168\.\d+\.\d+$", host):
        return True
    if re.match(r"^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$", host):
        return True
    if re.match(r"^169\.254\.\d+\.\d+$", host):  # link-local
        return True
    return False


def _aggregate_per_file(broken: list[LinkFinding]) -> dict[str, list[LinkFinding]]:
    out: dict[str, list[LinkFinding]] = {}
    for finding in broken:
        out.setdefault(finding.file_path, []).append(finding)
    return out


def _classify_version_severity(matched: str, target: VersionTarget) -> str | None:
    norm = matched.strip()
    if not norm:
        return None
    if target.eol:
        return "high"
    if norm in target.deprecated:
        # Old enough to be explicitly deprecated.
        return "high"
    if target.current and norm and _is_older_minor(norm, target.current):
        return "medium"
    return None


def _is_older_minor(found: str, current: str) -> bool:
    """True if `found` is strictly older than `current` by major.minor.

    Lenient parser — only checks the first two numeric components.
    """

    def _parts(text: str) -> tuple[int, int]:
        nums = re.findall(r"\d+", text)
        if not nums:
            return (0, 0)
        major = int(nums[0])
        minor = int(nums[1]) if len(nums) > 1 else 0
        return major, minor

    return _parts(found) < _parts(current)


def _link_findings_to_work_items(
    repo: str, per_file: dict[str, list[LinkFinding]]
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for file_rel, findings in sorted(per_file.items()):
        broken_count = len(findings)
        severity = _link_severity(broken_count)
        items.append(
            {
                "id": f"refresh-links-{_slug(file_rel)}",
                "repo": repo,
                "type": "refresh_links",
                "severity": severity,
                "path": file_rel,
                "broken_count": broken_count,
                "title": (
                    f"Fix {broken_count} broken link(s) in {file_rel}"
                ),
                "details": [
                    {"url": f.url, "status": f.status, "reason": f.reason}
                    for f in findings[:20]
                ],
            }
        )
    return items


def _version_findings_to_work_items(
    repo: str,
    findings: list[VersionFinding],
    targets: list[VersionTarget],
) -> list[dict[str, Any]]:
    targets_by_id = {t.id: t for t in targets}
    grouped: dict[tuple[str, str], list[VersionFinding]] = {}
    for finding in findings:
        grouped.setdefault((finding.file_path, finding.target_id), []).append(finding)

    items: list[dict[str, Any]] = []
    for (file_rel, target_id), group in sorted(grouped.items()):
        target = targets_by_id[target_id]
        worst_severity = "high" if any(f.severity == "high" for f in group) else "medium"
        items.append(
            {
                "id": f"refresh-version-{target_id}-{_slug(file_rel)}",
                "repo": repo,
                "type": "refresh_versions",
                "severity": worst_severity,
                "path": file_rel,
                "target": target.id,
                "current_target": target.current,
                "title": (
                    f"Update {target.name} references in {file_rel} "
                    f"(target {target.current})"
                ),
                "matches": [
                    {
                        "line": f.line_number,
                        "matched_version": f.matched_version,
                        "excerpt": f.excerpt,
                        "severity": f.severity,
                    }
                    for f in group[:20]
                ],
            }
        )
    return items


def _link_severity(broken_count: int) -> str:
    if broken_count >= _SEV_HIGH_BROKEN:
        return "high"
    if broken_count >= _SEV_MEDIUM_BROKEN:
        return "medium"
    return "low"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()[:80]


def _finding_dict(finding: LinkFinding) -> dict[str, Any]:
    return {
        "file_path": finding.file_path,
        "url": finding.url,
        "status": finding.status,
        "reason": finding.reason,
    }


def _version_finding_dict(finding: VersionFinding) -> dict[str, Any]:
    return {
        "file_path": finding.file_path,
        "target_id": finding.target_id,
        "matched_version": finding.matched_version,
        "line_number": finding.line_number,
        "excerpt": finding.excerpt,
        "severity": finding.severity,
    }
