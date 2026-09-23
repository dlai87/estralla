"""GitHub Discussions extractor + requirement mapper.

Populates the ``discussion_topics`` field on per-role curriculum-plan
manifests by querying GitHub Discussions in each track's ``-learning``
repo via ``gh api graphql``, then matching threads against requirement
keywords.

Design decisions (locked):

- **Categories:** all except ``Announcements`` (decision noted in
  ``project_curriculum_plan_manifest.md``)
- **Auto-enable:** if a target repo has Discussions disabled, this
  module enables it via ``gh api -X PATCH`` (opt-out with
  ``auto_enable=False``)
- **Caching:** per-repo cache at
  ``manifest/.cache/discussions/<owner>__<repo>.json`` so refreshes are
  incremental. Cache is gitignored.
- **Matching:** substring + simple suffix-strip stemming (lightweight
  Porter approximation). No NLP dependency.
- **Privacy / auth:** uses the host ``gh`` CLI's existing auth. No
  tokens read from this module. If ``gh auth status`` is unauthenticated
  the fetcher returns an empty list with an error in the report.
"""

from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .curriculum_plan import (
    CurriculumPlan,
    DiscussionTopic,
    Requirement,
    write_curriculum_plan,
)

LOGGER = logging.getLogger(__name__)

# Default org (matches the existing curriculum repos).
DEFAULT_OWNER = "ai-infra-curriculum"

# Cache directory (relative to the content-generator repo root). The
# whole ``manifest/.cache/`` tree is gitignored.
DEFAULT_CACHE_RELATIVE = "manifest/.cache/discussions"

# Categories we never map to requirements. Lowercased for comparison.
_EXCLUDED_CATEGORIES: frozenset[str] = frozenset({"announcements"})

# Page size for the GraphQL query. 50 keeps the response under the
# GraphQL node limit while still being efficient.
_PAGE_SIZE = 50

# Stopwords stripped before stemming. Mirrors plan_coverage._STOPWORDS
# so cross-module behavior is consistent.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "into",
        "from",
        "by",
        "at",
        "module",  # high-frequency in backfilled labels; carries no signal
    }
)

# Minimum token length to use for matching — shorter tokens have too
# many false positives (e.g., "ml" matches "html").
_MIN_TOKEN_LEN = 4


@dataclass(frozen=True)
class DiscussionThread:
    repo: str
    number: int
    url: str
    title: str
    body: str
    category: str
    created_at: str
    updated_at: str

    def is_excluded(self) -> bool:
        return self.category.strip().lower() in _EXCLUDED_CATEGORIES


@dataclass
class DiscussionsFetchReport:
    repo: str
    fetched: int = 0
    cached: int = 0
    enabled_now: bool = False
    skipped: bool = False
    error: str = ""
    notes: list[str] = field(default_factory=list)


# Subprocess shim — overridable in tests.
SubprocessRun = Callable[..., subprocess.CompletedProcess]


def _gh_json(args: list[str], runner: SubprocessRun = subprocess.run) -> Any:
    """Run ``gh api`` and parse the JSON body. Raises on non-zero exit."""
    completed = runner(
        ["gh", "api", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"gh api failed (rc={completed.returncode}): "
            f"argv={shlex.join(args)} stderr={completed.stderr[-300:]}"
        )
    return json.loads(completed.stdout or "{}")


def repo_has_discussions(
    owner: str, repo: str, *, runner: SubprocessRun = subprocess.run
) -> bool:
    """Check the repo's ``hasDiscussionsEnabled`` flag."""
    query = (
        "query { repository(owner: \"%s\", name: \"%s\") "
        "{ hasDiscussionsEnabled } }" % (owner, repo)
    )
    data = _gh_json(["graphql", "-f", f"query={query}"], runner=runner)
    return bool(
        data.get("data", {}).get("repository", {}).get("hasDiscussionsEnabled")
    )


def enable_discussions(
    owner: str, repo: str, *, runner: SubprocessRun = subprocess.run
) -> None:
    """PATCH the repo to set ``has_discussions: true``."""
    _gh_json(
        [
            "-X", "PATCH",
            f"repos/{owner}/{repo}",
            "-F", "has_discussions=true",
        ],
        runner=runner,
    )


_DISCUSSIONS_QUERY = """
query($owner:String!, $name:String!, $first:Int!, $after:String) {
  repository(owner:$owner, name:$name) {
    discussions(first:$first, after:$after, orderBy:{field:UPDATED_AT, direction:DESC}) {
      pageInfo { endCursor hasNextPage }
      nodes {
        number
        title
        body
        url
        createdAt
        updatedAt
        category { name }
      }
    }
  }
}
""".strip()


def fetch_discussions(
    repo: str,
    *,
    owner: str = DEFAULT_OWNER,
    page_size: int = _PAGE_SIZE,
    max_pages: int = 20,
    runner: SubprocessRun = subprocess.run,
) -> list[DiscussionThread]:
    """Page through all discussions in ``owner/repo``, excluding banned categories."""
    threads: list[DiscussionThread] = []
    cursor: str | None = None
    for _ in range(max_pages):
        args = [
            "graphql",
            "-f", f"query={_DISCUSSIONS_QUERY}",
            "-F", f"owner={owner}",
            "-F", f"name={repo}",
            "-F", f"first={page_size}",
        ]
        if cursor:
            args += ["-F", f"after={cursor}"]
        data = _gh_json(args, runner=runner)
        block = (
            data.get("data", {}).get("repository", {}).get("discussions") or {}
        )
        for node in block.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            category = (node.get("category") or {}).get("name", "")
            thread = DiscussionThread(
                repo=repo,
                number=int(node.get("number", 0)),
                url=str(node.get("url", "")),
                title=str(node.get("title", "")),
                body=str(node.get("body", "") or ""),
                category=category,
                created_at=str(node.get("createdAt", "")),
                updated_at=str(node.get("updatedAt", "")),
            )
            if thread.is_excluded():
                continue
            threads.append(thread)
        page_info = block.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    return threads


# ---------- cache ----------


def _cache_path(cache_dir: Path, owner: str, repo: str) -> Path:
    return cache_dir / f"{owner}__{repo}.json"


def load_cached_threads(
    cache_dir: Path, owner: str, repo: str
) -> list[DiscussionThread]:
    path = _cache_path(cache_dir, owner, repo)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    threads: list[DiscussionThread] = []
    for item in raw.get("threads") or []:
        if not isinstance(item, dict):
            continue
        threads.append(
            DiscussionThread(
                repo=str(item.get("repo", repo)),
                number=int(item.get("number", 0)),
                url=str(item.get("url", "")),
                title=str(item.get("title", "")),
                body=str(item.get("body", "")),
                category=str(item.get("category", "")),
                created_at=str(item.get("created_at", "")),
                updated_at=str(item.get("updated_at", "")),
            )
        )
    return threads


def write_cached_threads(
    cache_dir: Path,
    owner: str,
    repo: str,
    threads: list[DiscussionThread],
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, owner, repo)
    payload = {
        "schema_version": 1,
        "fetched_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "owner": owner,
        "repo": repo,
        "threads": [
            {
                "repo": t.repo,
                "number": t.number,
                "url": t.url,
                "title": t.title,
                "body": t.body,
                "category": t.category,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in threads
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


# ---------- refresh (fetch + cache + auto-enable) ----------


def refresh_repo_discussions(
    repo: str,
    *,
    owner: str = DEFAULT_OWNER,
    cache_dir: Path,
    auto_enable: bool = True,
    runner: SubprocessRun = subprocess.run,
) -> DiscussionsFetchReport:
    """Ensure Discussions are enabled, fetch all threads, write the cache."""
    report = DiscussionsFetchReport(repo=repo)
    try:
        enabled = repo_has_discussions(owner, repo, runner=runner)
        if not enabled:
            if not auto_enable:
                report.skipped = True
                report.notes.append("Discussions disabled (auto_enable=False)")
                return report
            enable_discussions(owner, repo, runner=runner)
            report.enabled_now = True
            report.notes.append("Auto-enabled Discussions on this repo")
        threads = fetch_discussions(repo, owner=owner, runner=runner)
        report.fetched = len(threads)
        write_cached_threads(cache_dir, owner, repo, threads)
        report.cached = len(threads)
    except RuntimeError as exc:
        report.error = str(exc)
    return report


# ---------- requirement matching ----------


def _tokens_from_label(label: str) -> list[str]:
    """Tokenize a requirement label into stemmed comparison tokens."""
    text = re.sub(r"[^a-z0-9]+", " ", label.lower())
    out: list[str] = []
    for raw in text.split():
        if raw in _STOPWORDS:
            continue
        stem = _light_stem(raw)
        if len(stem) < _MIN_TOKEN_LEN:
            continue
        out.append(stem)
    seen: set[str] = set()
    dedup: list[str] = []
    for token in out:
        if token in seen:
            continue
        seen.add(token)
        dedup.append(token)
    return dedup


def _light_stem(token: str) -> str:
    """Lightweight Porter-ish suffix stripping.

    Order matters — strip longer suffixes first. Conservative: only
    trims forms we see commonly in module / requirement labels
    (plurals, gerunds, past tense, common derivations).
    """
    if len(token) < 5:
        return token
    for suffix, replacement in (
        ("ization", "ize"),
        ("ations", "ate"),
        ("ation", "ate"),
        ("ing", ""),
        ("ies", "y"),
        ("es", ""),
        ("ed", ""),
        ("er", ""),
        ("ly", ""),
        ("s", ""),
    ):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)] + replacement
    return token


def _thread_text_for_match(thread: DiscussionThread) -> str:
    return (thread.title + "\n" + thread.body).lower()


def _thread_contains_token(thread_text: str, token: str) -> bool:
    """True if ``token`` (or a 1-char inflection) appears in the text.

    Substring matches on the stem + naive inflections. Avoids regex
    backtracking — the text can be large.
    """
    if token in thread_text:
        return True
    # Try simple inflections.
    for suffix in ("s", "es", "ed", "ing", "y"):
        if (token + suffix) in thread_text:
            return True
    return False


def find_thread_matches(
    requirement: Requirement, threads: list[DiscussionThread]
) -> list[tuple[DiscussionThread, list[str]]]:
    """Return threads matching ≥1 requirement-label token, with the tokens."""
    tokens = _tokens_from_label(requirement.label)
    if not tokens:
        return []
    matches: list[tuple[DiscussionThread, list[str]]] = []
    for thread in threads:
        text = _thread_text_for_match(thread)
        matched = [t for t in tokens if _thread_contains_token(text, t)]
        if matched:
            matches.append((thread, matched))
    return matches


def map_discussions_to_plan(
    plan: CurriculumPlan, threads: list[DiscussionThread]
) -> CurriculumPlan:
    """Return a new CurriculumPlan with ``discussion_topics`` populated."""
    new_requirements: list[Requirement] = []
    for req in plan.requirements:
        matches = find_thread_matches(req, threads)
        topics = tuple(
            DiscussionTopic(
                thread_url=thread.url,
                category=thread.category,
                title=thread.title,
                matched_via="keyword:" + ",".join(sorted(set(matched))[:5]),
            )
            for thread, matched in matches
        )
        # Preserve any existing manual topics (matched_via="manual" /
        # non-keyword) that the agent or a human added.
        manual = tuple(
            t for t in req.discussion_topics if not t.matched_via.startswith("keyword:")
        )
        new_requirements.append(
            type(req)(
                **{
                    **{f: getattr(req, f) for f in req.__dataclass_fields__},
                    "discussion_topics": manual + topics,
                }
            )
        )
    return type(plan)(
        schema_version=plan.schema_version,
        role=plan.role,
        role_title=plan.role_title,
        research=plan.research,
        requirements=tuple(new_requirements),
    )


# ---------- high-level driver ----------


def refresh_role_discussions(
    *,
    role: str,
    learning_repo: str,
    baseline_path: Path,
    cache_dir: Path,
    owner: str = DEFAULT_OWNER,
    auto_enable: bool = True,
    use_cache_only: bool = False,
    write: bool = True,
    runner: SubprocessRun = subprocess.run,
) -> dict[str, Any]:
    """Refresh discussion_topics for one role's curriculum-plan manifest.

    1. Fetch Discussions for the role's ``-learning`` repo
       (unless ``use_cache_only=True``).
    2. Map them to the role's requirements via keyword matching.
    3. Write the updated per-role manifest (unless ``write=False``).
    """
    from .curriculum_plan import load_curriculum_plan

    fetch_report: DiscussionsFetchReport
    if use_cache_only:
        threads = load_cached_threads(cache_dir, owner, learning_repo)
        fetch_report = DiscussionsFetchReport(
            repo=learning_repo,
            cached=len(threads),
            notes=["use_cache_only=True; skipped fetch"],
        )
    else:
        fetch_report = refresh_repo_discussions(
            learning_repo,
            owner=owner,
            cache_dir=cache_dir,
            auto_enable=auto_enable,
            runner=runner,
        )
        threads = load_cached_threads(cache_dir, owner, learning_repo)

    plan = load_curriculum_plan(baseline_path)
    updated = map_discussions_to_plan(plan, threads)

    mapped = sum(len(r.discussion_topics) for r in updated.requirements)
    if write:
        write_curriculum_plan(updated, baseline_path)

    return {
        "role": role,
        "learning_repo": learning_repo,
        "threads_seen": len(threads),
        "mappings_written": mapped,
        "wrote_file": write,
        "fetch": {
            "fetched": fetch_report.fetched,
            "cached": fetch_report.cached,
            "enabled_now": fetch_report.enabled_now,
            "skipped": fetch_report.skipped,
            "error": fetch_report.error,
            "notes": list(fetch_report.notes),
        },
    }
