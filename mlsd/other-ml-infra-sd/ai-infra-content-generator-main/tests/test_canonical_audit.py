"""Tests for the canonical-sources staleness audit."""

from __future__ import annotations

from pathlib import Path

from aicg.link_refresh import FetchResult
from aicg.manifest import audit_canonical_sources, load_canonical_sources

CANONICAL_PATH = Path("manifest/canonical_sources.json")


def _fetcher(responses: dict[tuple[str, str], FetchResult]):
    def fetch(url: str, method: str = "HEAD") -> FetchResult:
        return responses.get(
            (url, method),
            FetchResult(status=200, final_url=url),  # default-alive for unmocked URLs
        )

    return fetch


def test_audit_clean_registry_produces_no_stale() -> None:
    """If every successor URL returns 200, no entries are flagged."""
    registry = load_canonical_sources(CANONICAL_PATH)
    stale = audit_canonical_sources(registry, http_fetcher=_fetcher({}))
    assert stale == []


def test_audit_detects_404_successor() -> None:
    """A successor that 404s gets flagged."""
    registry = load_canonical_sources(CANONICAL_PATH)
    dead = "https://wellfound.com/jobs"  # angellist's documented successor
    stale = audit_canonical_sources(
        registry,
        http_fetcher=_fetcher(
            {
                (dead, "HEAD"): FetchResult(status=404, final_url=dead),
                (dead, "GET"): FetchResult(status=404, final_url=dead),
            }
        ),
    )
    # Every entry that points at the dead successor gets flagged
    # (the AngelList source has three old_url variants all mapped to
    # wellfound.com).
    dead_entries = [s for s in stale if s.new_url == dead]
    assert len(dead_entries) >= 1
    assert any(s.old_url == "https://angel.co/jobs" for s in dead_entries)
    assert all(s.status == 404 for s in dead_entries)


def test_audit_ignores_403_rate_limit() -> None:
    """A 403 anti-bot response is NOT stale — the URL is alive, just walled."""
    registry = load_canonical_sources(CANONICAL_PATH)
    walled = "https://wellfound.com/jobs"
    stale = audit_canonical_sources(
        registry,
        http_fetcher=_fetcher(
            {
                (walled, "HEAD"): FetchResult(status=403, final_url=walled),
                (walled, "GET"): FetchResult(status=403, final_url=walled),
            }
        ),
    )
    assert stale == []


def test_audit_detects_network_failure() -> None:
    """A URL with no response (DNS fail, timeout) is treated as stale."""
    registry = load_canonical_sources(CANONICAL_PATH)
    dead = "https://github.com/eza-community/eza"
    stale = audit_canonical_sources(
        registry,
        http_fetcher=_fetcher(
            {
                (dead, "HEAD"): FetchResult(status=None, final_url=dead, error="timeout"),
                (dead, "GET"): FetchResult(status=None, final_url=dead, error="timeout"),
            }
        ),
    )
    assert any(s.new_url == dead for s in stale)


def test_audit_skips_non_http_canonicals() -> None:
    """oci:// canonicals (e.g., Bitnami) are skipped — different probe shape."""
    registry = load_canonical_sources(CANONICAL_PATH)
    # The Bitnami source's successor is oci://. We shouldn't try to HEAD oci:// URLs.
    bitnami = next(s for s in registry.sources if "Bitnami" in s.name)
    assert any(v.startswith("oci://") for v in bitnami.successors.values())
    stale = audit_canonical_sources(registry, http_fetcher=_fetcher({}))
    # No bitnami entries should appear (they have oci:// successors).
    assert all("Bitnami" not in s.source_name for s in stale)


def test_audit_follows_head_then_get() -> None:
    """HEAD 405 followed by GET 200 is alive, not stale."""
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://wellfound.com/jobs"
    stale = audit_canonical_sources(
        registry,
        http_fetcher=_fetcher(
            {
                (url, "HEAD"): FetchResult(status=405, final_url=url),
                (url, "GET"): FetchResult(status=200, final_url=url),
            }
        ),
    )
    assert stale == []
