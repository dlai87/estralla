"""Curriculum manifest + canonical-source registry.

Two structured indexes that ground every AICG content decision:

- ``curriculum.manifest.json`` — every track, module, exercise, project,
  and resource across the 27 curriculum repos, with paths + GitHub URLs.
  Used by the generator (to cross-reference existing content during
  authoring) and by the moderation bot (for ``/find``).
- ``canonical_sources.json`` — for each external tool/concept the
  curriculum cites, the canonical URL plus known successors. Consulted
  by the link-refresh resolver BEFORE Wayback fallback, so a deprecated
  vendor URL routes to the live successor instead of an archive
  snapshot.

Both files are deterministic JSON, version-pinned via ``schema_version``,
and produced by ``scripts/build-curriculum-manifest.py``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = 1
CANONICAL_SCHEMA_VERSION = 1


class ManifestError(ValueError):
    """Raised when a manifest file is malformed."""


# ---------- curriculum manifest ----------


@dataclass(frozen=True)
class Exercise:
    slug: str
    number: int
    title: str
    learning_path: str | None
    solutions_path: str | None
    learning_url: str | None
    solutions_url: str | None


@dataclass(frozen=True)
class Module:
    slug: str
    number: int
    title: str
    path: str
    github_url: str
    exercises: tuple[Exercise, ...] = ()
    prerequisites: tuple[str, ...] = ()
    related: tuple[str, ...] = ()


@dataclass(frozen=True)
class Project:
    slug: str
    number: int
    title: str
    learning_path: str | None
    solutions_path: str | None
    learning_url: str | None
    solutions_url: str | None
    docs: tuple[str, ...] = ()  # ['requirements.md', 'architecture.md', …]
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class Resource:
    slug: str
    path: str
    github_url: str


@dataclass(frozen=True)
class Track:
    slug: str  # e.g. "junior-engineer"
    display_name: str
    level: int  # 1=junior, 2=engineer, 3=senior, etc.
    learning_repo: str | None
    solutions_repo: str | None
    learning_repo_url: str | None
    solutions_repo_url: str | None
    modules: tuple[Module, ...] = ()
    projects: tuple[Project, ...] = ()
    resources: tuple[Resource, ...] = ()


@dataclass(frozen=True)
class CurriculumManifest:
    schema_version: int
    generated_at: str
    org: str
    tracks: tuple[Track, ...]

    def track(self, slug: str) -> Track | None:
        for t in self.tracks:
            if t.slug == slug:
                return t
        return None

    def find_module(self, track_slug: str, module_slug: str) -> Module | None:
        track = self.track(track_slug)
        if track is None:
            return None
        for module in track.modules:
            if module.slug == module_slug:
                return module
        return None

    def find_project(self, track_slug: str, project_slug: str) -> Project | None:
        track = self.track(track_slug)
        if track is None:
            return None
        for project in track.projects:
            if project.slug == project_slug:
                return project
        return None

    @property
    def total_modules(self) -> int:
        return sum(len(t.modules) for t in self.tracks)

    @property
    def total_exercises(self) -> int:
        return sum(len(m.exercises) for t in self.tracks for m in t.modules)

    @property
    def total_projects(self) -> int:
        return sum(len(t.projects) for t in self.tracks)


def load_curriculum_manifest(path: Path) -> CurriculumManifest:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise ManifestError("Curriculum manifest root must be an object.")

    schema = int(raw.get("schema_version", 0))
    if schema != MANIFEST_SCHEMA_VERSION:
        raise ManifestError(
            f"Curriculum manifest schema_version={schema} "
            f"!= expected {MANIFEST_SCHEMA_VERSION}"
        )

    tracks = tuple(_parse_track(item) for item in raw.get("tracks", []))
    return CurriculumManifest(
        schema_version=schema,
        generated_at=str(raw.get("generated_at", "")),
        org=str(raw.get("org", "ai-infra-curriculum")),
        tracks=tracks,
    )


def _parse_track(raw: Any) -> Track:
    if not isinstance(raw, dict):
        raise ManifestError("Track entries must be objects.")
    return Track(
        slug=_required_str(raw, "slug"),
        display_name=_required_str(raw, "display_name"),
        level=int(raw.get("level", 0)),
        learning_repo=raw.get("learning_repo"),
        solutions_repo=raw.get("solutions_repo"),
        learning_repo_url=raw.get("learning_repo_url"),
        solutions_repo_url=raw.get("solutions_repo_url"),
        modules=tuple(_parse_module(item) for item in raw.get("modules", [])),
        projects=tuple(_parse_project(item) for item in raw.get("projects", [])),
        resources=tuple(_parse_resource(item) for item in raw.get("resources", [])),
    )


def _parse_module(raw: Any) -> Module:
    if not isinstance(raw, dict):
        raise ManifestError("Module entries must be objects.")
    return Module(
        slug=_required_str(raw, "slug"),
        number=int(raw.get("number", 0)),
        title=_required_str(raw, "title"),
        path=_required_str(raw, "path"),
        github_url=_required_str(raw, "github_url"),
        exercises=tuple(_parse_exercise(item) for item in raw.get("exercises", [])),
        prerequisites=tuple(str(item) for item in raw.get("prerequisites", [])),
        related=tuple(str(item) for item in raw.get("related", [])),
    )


def _parse_exercise(raw: Any) -> Exercise:
    if not isinstance(raw, dict):
        raise ManifestError("Exercise entries must be objects.")
    return Exercise(
        slug=_required_str(raw, "slug"),
        number=int(raw.get("number", 0)),
        title=_required_str(raw, "title"),
        learning_path=raw.get("learning_path"),
        solutions_path=raw.get("solutions_path"),
        learning_url=raw.get("learning_url"),
        solutions_url=raw.get("solutions_url"),
    )


def _parse_project(raw: Any) -> Project:
    if not isinstance(raw, dict):
        raise ManifestError("Project entries must be objects.")
    return Project(
        slug=_required_str(raw, "slug"),
        number=int(raw.get("number", 0)),
        title=_required_str(raw, "title"),
        learning_path=raw.get("learning_path"),
        solutions_path=raw.get("solutions_path"),
        learning_url=raw.get("learning_url"),
        solutions_url=raw.get("solutions_url"),
        docs=tuple(str(item) for item in raw.get("docs", [])),
        prerequisites=tuple(str(item) for item in raw.get("prerequisites", [])),
    )


def _parse_resource(raw: Any) -> Resource:
    if not isinstance(raw, dict):
        raise ManifestError("Resource entries must be objects.")
    return Resource(
        slug=_required_str(raw, "slug"),
        path=_required_str(raw, "path"),
        github_url=_required_str(raw, "github_url"),
    )


# ---------- canonical sources ----------


@dataclass(frozen=True)
class CanonicalSource:
    name: str
    canonical: str
    topic: tuple[str, ...]
    rationale: str
    successors: dict[str, str]
    machine_consumed: bool = False


@dataclass(frozen=True)
class CanonicalSourceRegistry:
    schema_version: int
    updated_at: str
    sources: tuple[CanonicalSource, ...] = field(default_factory=tuple)

    def lookup_successor(self, url: str) -> str | None:
        """Return the canonical successor URL for ``url``, or None.

        Strips trailing slashes during comparison so ``https://x.com`` and
        ``https://x.com/`` match the same successor entry.
        """
        candidates = (url, url.rstrip("/"), url + "/")
        for source in self.sources:
            for old, new in source.successors.items():
                if old in candidates or old.rstrip("/") == url.rstrip("/"):
                    return new
        return None

    def is_known_machine_endpoint(self, url: str) -> bool:
        """True if the URL matches a registered machine-consumed endpoint."""
        host = _host_of(url)
        for source in self.sources:
            if not source.machine_consumed:
                continue
            if host == _host_of(source.canonical):
                return True
        return False


def load_canonical_sources(path: Path) -> CanonicalSourceRegistry:
    """Missing file = empty registry (caller may operate without it)."""
    if not path.exists():
        LOGGER.info(
            "Canonical-source registry not present at %s; resolver will "
            "fall through to standard redirect chase / Wayback fallback.",
            path,
        )
        return CanonicalSourceRegistry(
            schema_version=CANONICAL_SCHEMA_VERSION,
            updated_at="",
            sources=(),
        )

    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise ManifestError("Canonical-source registry root must be an object.")
    schema = int(raw.get("schema_version", 0))
    if schema != CANONICAL_SCHEMA_VERSION:
        raise ManifestError(
            f"Canonical-source schema_version={schema} "
            f"!= expected {CANONICAL_SCHEMA_VERSION}"
        )

    sources = tuple(_parse_canonical_source(item) for item in raw.get("sources", []))
    return CanonicalSourceRegistry(
        schema_version=schema,
        updated_at=str(raw.get("updated_at", "")),
        sources=sources,
    )


def _parse_canonical_source(raw: Any) -> CanonicalSource:
    if not isinstance(raw, dict):
        raise ManifestError("Canonical source entries must be objects.")
    successors_raw = raw.get("successors", {})
    if not isinstance(successors_raw, dict):
        raise ManifestError(
            f"Canonical source `{raw.get('name')}` has non-object `successors`."
        )
    return CanonicalSource(
        name=_required_str(raw, "name"),
        canonical=_required_str(raw, "canonical"),
        topic=tuple(str(item) for item in raw.get("topic", [])),
        rationale=str(raw.get("rationale", "")),
        successors={str(k): str(v) for k, v in successors_raw.items()},
        machine_consumed=bool(raw.get("machine_consumed", False)),
    )


# ---------- shared helpers ----------


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"Manifest file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in {path}: {exc}") from exc


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"Missing or invalid string field: {key}")
    return value.strip()


def _host_of(url: str) -> str:
    if not url.startswith(("http://", "https://", "oci://")):
        return url
    rest = url.split("://", 1)[1]
    return rest.split("/", 1)[0].lower()


# ---------- prompt-summary helpers ----------


def summarize_track_for_prompt(
    track: Track, *, max_titles: int = 12, brief: bool = False
) -> str:
    """Compact, prompt-friendly inventory of a single track.

    Designed to be included in a research prompt so the agent grounds
    proposals in what's already covered. Keeps each line short enough
    that even the full 12-track summary fits in a reasonable prompt
    budget.

    ``brief=True`` produces a one-line-per-thing inventory (slugs
    only, no exercise counts, no projects breakdown) for use in
    prompts that don't consume the per-role manifest — the agent just
    needs enough signal to avoid proposing duplicates.
    """
    if brief:
        lines = [f"### {track.display_name} (`{track.slug}`)"]
        if track.modules:
            slugs = ", ".join(
                f"`{m.slug}`" for m in track.modules[:max_titles]
            )
            suffix = (
                f" (+{len(track.modules) - max_titles} more)"
                if len(track.modules) > max_titles
                else ""
            )
            lines.append(f"Modules: {slugs}{suffix}")
        if track.projects:
            slugs = ", ".join(
                f"`{p.slug}`" for p in track.projects[:max_titles]
            )
            suffix = (
                f" (+{len(track.projects) - max_titles} more)"
                if len(track.projects) > max_titles
                else ""
            )
            lines.append(f"Projects: {slugs}{suffix}")
        return "\n".join(lines)

    lines: list[str] = [
        f"## {track.display_name} (level {track.level}, slug `{track.slug}`)"
    ]
    if track.modules:
        lines.append(f"Modules ({len(track.modules)}):")
        for module in track.modules[:max_titles]:
            ex_count = len(module.exercises)
            ex_marker = f" — {ex_count} exercise(s)" if ex_count else ""
            lines.append(f"- {module.slug} · {module.title}{ex_marker}")
        if len(track.modules) > max_titles:
            lines.append(f"- … {len(track.modules) - max_titles} more")
    if track.projects:
        lines.append(f"Projects ({len(track.projects)}):")
        for project in track.projects[:max_titles]:
            lines.append(f"- {project.slug} · {project.title}")
        if len(track.projects) > max_titles:
            lines.append(f"- … {len(track.projects) - max_titles} more")
    return "\n".join(lines)


@dataclass(frozen=True)
class StaleCanonicalEntry:
    """A registered canonical successor whose URL is now broken or gone."""

    source_name: str
    old_url: str
    new_url: str
    status: int | None
    note: str

    def render(self) -> str:
        status = f"HTTP {self.status}" if self.status else "no response"
        return (
            f"- `{self.source_name}`: `{self.old_url}` → `{self.new_url}` "
            f"({status}{': ' + self.note if self.note else ''})"
        )


def audit_canonical_sources(
    registry: CanonicalSourceRegistry,
    *,
    http_fetcher=None,
) -> list[StaleCanonicalEntry]:
    """Probe every registered ``successors[*]`` URL and flag dead ones.

    Uses the same HEAD-then-GET classification as the link-refresh
    resolver — only 404/410/451/no-response count as stale. 401/403/429
    are auth-walled / rate-limited and do NOT trigger a stale flag.

    ``http_fetcher`` is the same fetcher signature used by link-refresh
    (injectable for tests).
    """
    if http_fetcher is None:
        from .link_refresh import default_http_fetcher

        http_fetcher = default_http_fetcher

    from .link_refresh import (
        _UNAMBIGUOUSLY_BROKEN_STATUSES,
        _is_redirect,
        _is_success,
    )

    stale: list[StaleCanonicalEntry] = []
    for source in registry.sources:
        for old_url, new_url in source.successors.items():
            # Skip non-HTTP canonicals (oci://, git://) — probing them
            # would need scheme-specific clients; they don't rot the
            # same way.
            if not new_url.startswith(("http://", "https://")):
                continue

            head = http_fetcher(new_url, "HEAD")
            if _is_success(head.status) or _is_redirect(head.status):
                continue
            # Confirm with GET — some servers reject HEAD.
            get = http_fetcher(new_url, "GET")
            if _is_success(get.status) or _is_redirect(get.status):
                continue

            final_status = get.status if get.status is not None else head.status
            note = get.error or head.error
            if final_status in _UNAMBIGUOUSLY_BROKEN_STATUSES or final_status is None:
                stale.append(
                    StaleCanonicalEntry(
                        source_name=source.name,
                        old_url=old_url,
                        new_url=new_url,
                        status=final_status,
                        note=note,
                    )
                )
    return stale


def summarize_manifest_for_prompt(
    manifest: CurriculumManifest,
    *,
    only_track_slug: str | None = None,
    brief: bool = False,
) -> str:
    """Whole-curriculum summary suitable for embedding in research prompts.

    When ``only_track_slug`` is provided, returns just that track's
    summary plus a one-line index of sibling tracks — the most common
    use case from the research pipeline (per-role prompt).

    ``brief=True`` produces a much smaller summary (slugs only) for
    prompts that don't consume the per-role manifest. Saves ~50-70%
    of the token cost when the agent only needs duplicate-avoidance
    signal, not full hierarchy detail.
    """
    if only_track_slug is not None:
        target = manifest.track(only_track_slug)
        if target is None:
            return f"(no track matched `{only_track_slug}`)"
        if brief:
            # Skip the sibling-tracks index too — pure noise for the
            # brief code path (non-canary roles).
            return (
                f"# Existing curriculum — `{only_track_slug}`\n\n"
                f"{summarize_track_for_prompt(target, brief=True)}\n"
            )
        sibling_index = "Sibling tracks: " + ", ".join(
            f"{t.slug} (L{t.level})" for t in manifest.tracks if t.slug != only_track_slug
        )
        return (
            f"# Existing curriculum — `{only_track_slug}`\n\n"
            f"{summarize_track_for_prompt(target)}\n\n"
            f"{sibling_index}\n"
        )

    parts = [
        f"# Existing curriculum across {len(manifest.tracks)} tracks "
        f"({manifest.total_modules} modules, {manifest.total_exercises} exercises, "
        f"{manifest.total_projects} projects)\n"
    ]
    for track in sorted(manifest.tracks, key=lambda t: (t.level, t.slug)):
        parts.append(summarize_track_for_prompt(track, brief=brief))
    return "\n\n".join(parts)
