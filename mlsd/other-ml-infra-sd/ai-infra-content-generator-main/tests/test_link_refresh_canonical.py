"""Tests that the canonical-source registry is consulted before Wayback.

These tests cement Bug A's class fix: when the curriculum has ground
truth for a vendor rebrand or project successor, the resolver should
emit the *successor* URL, not a Wayback snapshot of the dead one.
"""

from __future__ import annotations

from pathlib import Path

from aicg.link_refresh import FetchResult, resolve_link
from aicg.manifest import load_canonical_sources


def _fetcher(responses: dict[tuple[str, str], FetchResult]):
    def fetch(url: str, method: str = "HEAD") -> FetchResult:
        return responses.get(
            (url, method),
            FetchResult(status=None, final_url=url, error="not_mocked"),
        )

    return fetch


def _wayback(snapshots: dict[str, str | None]):
    def fetch(url: str) -> str | None:
        return snapshots.get(url)

    return fetch


CANONICAL_PATH = Path("manifest/canonical_sources.json")


def test_bitnami_canonical_routes_to_oci_not_wayback() -> None:
    """Bitnami chart URL routes to the OCI registry from canonical_sources.json."""
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://charts.bitnami.com/bitnami"
    archived = "http://web.archive.org/web/X/" + url
    result = resolve_link(
        url,
        http_fetcher=_fetcher({}),  # never reached
        wayback_fetcher=_wayback({url: archived}),
        canonical_sources=registry,
    )
    assert result.source == "canonical"
    assert result.replacement == "oci://registry-1.docker.io/bitnamicharts"
    assert "web.archive.org" not in result.replacement


def test_exa_canonical_routes_to_eza() -> None:
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://the.exa.website/"
    result = resolve_link(
        url,
        http_fetcher=_fetcher({}),
        wayback_fetcher=_wayback({url: "http://web.archive.org/web/X/" + url}),
        canonical_sources=registry,
    )
    assert result.source == "canonical"
    assert result.replacement == "https://github.com/eza-community/eza"


def test_angellist_canonical_routes_to_wellfound() -> None:
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://angel.co/jobs"
    result = resolve_link(
        url,
        http_fetcher=_fetcher({}),
        wayback_fetcher=_wayback({}),
        canonical_sources=registry,
    )
    assert result.source == "canonical"
    assert result.replacement == "https://wellfound.com/jobs"


def test_fulcio_machine_endpoint_protected_even_without_yaml_context() -> None:
    """Fulcio is registered as machine_consumed=true — Wayback is suppressed.

    This is the registry-driven version of the YAML-context protection
    from Bug C: even when the surrounding line doesn't trigger the regex,
    a registered machine_endpoint URL still gets protected.
    """
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://fulcio.sigstore.dev"
    result = resolve_link(
        url,
        http_fetcher=_fetcher(
            {
                (url, "HEAD"): FetchResult(status=404, final_url=url),
                (url, "GET"): FetchResult(status=404, final_url=url),
            }
        ),
        wayback_fetcher=_wayback({url: "http://web.archive.org/web/X/" + url}),
        canonical_sources=registry,
        machine_consumed=False,  # NOT set by context — registry promotes it
    )
    assert result.source == "machine_endpoint"
    assert result.replacement is None


def test_unknown_url_falls_through_to_normal_resolution() -> None:
    """An unregistered URL still uses the standard HEAD/GET/redirect/Wayback path."""
    registry = load_canonical_sources(CANONICAL_PATH)
    url = "https://genuinely-broken.example.com/post"
    archived = "http://web.archive.org/web/X/" + url
    result = resolve_link(
        url,
        http_fetcher=_fetcher(
            {
                (url, "HEAD"): FetchResult(status=404, final_url=url),
                (url, "GET"): FetchResult(status=404, final_url=url),
            }
        ),
        wayback_fetcher=_wayback({url: archived}),
        canonical_sources=registry,
    )
    assert result.source == "wayback"
    assert result.replacement == archived


def test_resolve_link_without_registry_still_works() -> None:
    """canonical_sources is optional — None keeps old behavior."""
    url = "https://charts.bitnami.com/bitnami"
    redirect = "https://repo.broadcom.com/bitnami-files/"
    result = resolve_link(
        url,
        http_fetcher=_fetcher(
            {
                (url, "HEAD"): FetchResult(status=302, final_url=redirect),
                (redirect, "HEAD"): FetchResult(status=200, final_url=redirect),
            }
        ),
        wayback_fetcher=_wayback({}),
        canonical_sources=None,
    )
    # No registry — falls through to redirect chase (Bug A fix).
    assert result.source == "redirect"
    assert result.replacement == redirect
