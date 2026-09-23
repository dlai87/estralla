"""Tests for the deterministic refresh_links handler."""

from __future__ import annotations

from pathlib import Path

import pytest

from aicg.link_refresh import (
    DISALLOWED_REPLACEMENT_DOMAINS,
    FetchResult,
    LinkResolution,
    apply_replacements,
    handle_refresh_links_item,
    resolve_link,
)


def _fetcher(responses: dict[str, FetchResult]):
    def fetch(url: str, method: str = "HEAD") -> FetchResult:
        if url not in responses:
            return FetchResult(status=None, final_url=url, error="not_mocked")
        return responses[url]
    return fetch


def _wayback(snapshots: dict[str, str | None]):
    def fetch(url: str) -> str | None:
        return snapshots.get(url)
    return fetch


# ---------- resolve_link --------------------------------------------


def test_resolve_link_returns_alive_when_recheck_passes():
    fetcher = _fetcher({"https://example.com/foo": FetchResult(200, "https://example.com/foo")})
    resolution = resolve_link(
        "https://example.com/foo",
        http_fetcher=fetcher,
        wayback_fetcher=_wayback({}),
    )
    assert resolution.source == "alive"
    assert resolution.replacement == "https://example.com/foo"
    assert not resolution.needs_edit


def test_resolve_link_follows_redirect_to_final_200():
    fetcher = _fetcher({
        "https://example.com/old": FetchResult(301, "https://example.com/new"),
        "https://example.com/new": FetchResult(200, "https://example.com/new"),
    })
    resolution = resolve_link(
        "https://example.com/old",
        http_fetcher=fetcher,
        wayback_fetcher=_wayback({}),
    )
    assert resolution.source == "redirect"
    assert resolution.replacement == "https://example.com/new"
    assert resolution.needs_edit


def test_resolve_link_falls_back_to_wayback_when_dead():
    fetcher = _fetcher({"https://gone.example/x": FetchResult(404, "https://gone.example/x")})
    archived = "https://web.archive.org/web/20250101000000/https://gone.example/x"
    resolution = resolve_link(
        "https://gone.example/x",
        http_fetcher=fetcher,
        wayback_fetcher=_wayback({"https://gone.example/x": archived}),
    )
    assert resolution.source == "wayback"
    assert resolution.replacement == archived
    assert resolution.needs_edit


def test_resolve_link_unresolved_when_no_options():
    fetcher = _fetcher({"https://gone.example/x": FetchResult(404, "https://gone.example/x")})
    resolution = resolve_link(
        "https://gone.example/x",
        http_fetcher=fetcher,
        wayback_fetcher=_wayback({}),
    )
    assert resolution.source == "unresolved"
    assert resolution.replacement is None
    assert not resolution.needs_edit


def test_resolve_link_refuses_disallowed_replacement_domain():
    """Wayback or a redirect that lands on a disallowed domain must NOT replace."""
    disallowed = "https://veriswarm.ai/some/path"
    assert "veriswarm.ai" in DISALLOWED_REPLACEMENT_DOMAINS
    fetcher = _fetcher({"https://gone.example/x": FetchResult(404, "https://gone.example/x")})
    resolution = resolve_link(
        "https://gone.example/x",
        http_fetcher=fetcher,
        wayback_fetcher=_wayback({"https://gone.example/x": disallowed}),
    )
    assert resolution.source == "unresolved"
    assert resolution.replacement is None


# ---------- apply_replacements --------------------------------------


def test_apply_replacements_preserves_link_text_in_markdown():
    body = "See the [docs](https://old.example/x) for details."
    resolution = LinkResolution(
        original="https://old.example/x",
        replacement="https://new.example/y",
        source="redirect",
    )
    out = apply_replacements(body, [resolution])
    assert out == "See the [docs](https://new.example/y) for details."


def test_apply_replacements_longest_first_avoids_prefix_collision():
    body = "a=https://x.example/foo b=https://x.example/foobar"
    rs = [
        LinkResolution("https://x.example/foo", "https://X1.example/", "redirect"),
        LinkResolution(
            "https://x.example/foobar", "https://X2.example/", "redirect"
        ),
    ]
    out = apply_replacements(body, rs)
    assert "https://X1.example/" in out
    assert "https://X2.example/" in out
    # Original short URL must have been substituted exactly, not duped.
    assert "https://x.example/foo" not in out
    assert "https://x.example/foobar" not in out


def test_apply_replacements_skips_alive_links():
    body = "Read [here](https://example.com/foo)."
    rs = [
        LinkResolution(
            "https://example.com/foo", "https://example.com/foo", "alive"
        )
    ]
    out = apply_replacements(body, rs)
    assert out == body  # untouched


# ---------- handle_refresh_links_item -------------------------------


def _make_workspace(tmp_path: Path, repo: str, relpath: str, body: str) -> Path:
    workspace = tmp_path / "ws"
    repo_path = workspace / repo
    target = repo_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return workspace


def test_handler_no_replacements_skips_pr(tmp_path):
    body = "[a](https://gone.example/x) [b](https://also-gone.example/y)"
    workspace = _make_workspace(tmp_path, "repo-a", "docs/notes.md", body)
    item = {
        "type": "refresh_links",
        "repo": "repo-a",
        "path": "docs/notes.md",
        "details": [
            {"url": "https://gone.example/x", "status": 404, "reason": "Not Found"},
            {"url": "https://also-gone.example/y", "status": 404, "reason": "Not Found"},
        ],
    }
    result = handle_refresh_links_item(
        workspace=workspace,
        item=item,
        http_fetcher=_fetcher({
            "https://gone.example/x": FetchResult(404, "https://gone.example/x"),
            "https://also-gone.example/y": FetchResult(404, "https://also-gone.example/y"),
        }),
        wayback_fetcher=_wayback({}),
        open_pr=False,
    )
    assert result["status"] == "no_replacements_found"
    assert "pr" not in result
    # Body unchanged.
    assert (workspace / "repo-a" / "docs/notes.md").read_text() == body


def test_handler_now_alive_does_not_edit(tmp_path):
    body = "Doc: [link](https://example.com/foo)"
    workspace = _make_workspace(tmp_path, "repo-a", "docs/notes.md", body)
    item = {
        "type": "refresh_links",
        "repo": "repo-a",
        "path": "docs/notes.md",
        "details": [{"url": "https://example.com/foo", "status": 503, "reason": "stale"}],
    }
    result = handle_refresh_links_item(
        workspace=workspace,
        item=item,
        http_fetcher=_fetcher({
            "https://example.com/foo": FetchResult(200, "https://example.com/foo"),
        }),
        wayback_fetcher=_wayback({}),
        open_pr=False,
    )
    assert result["status"] == "no_action_now_alive"
    assert result["summary"]["now_alive"] == 1
    assert (workspace / "repo-a" / "docs/notes.md").read_text() == body


def test_handler_applies_redirect_and_wayback_replacements(tmp_path):
    body = (
        "Old: [a](https://old.example/x)\n"
        "Dead: [b](https://dead.example/y)\n"
        "Alive: [c](https://live.example/z)\n"
    )
    workspace = _make_workspace(tmp_path, "repo-a", "docs/notes.md", body)
    item = {
        "type": "refresh_links",
        "repo": "repo-a",
        "path": "docs/notes.md",
        "details": [
            {"url": "https://old.example/x"},
            {"url": "https://dead.example/y"},
            {"url": "https://live.example/z"},
        ],
    }
    archived = "https://web.archive.org/web/20250101/https://dead.example/y"
    result = handle_refresh_links_item(
        workspace=workspace,
        item=item,
        http_fetcher=_fetcher({
            "https://old.example/x": FetchResult(301, "https://moved.example/x"),
            "https://moved.example/x": FetchResult(200, "https://moved.example/x"),
            "https://dead.example/y": FetchResult(404, "https://dead.example/y"),
            "https://live.example/z": FetchResult(200, "https://live.example/z"),
        }),
        wayback_fetcher=_wayback({"https://dead.example/y": archived}),
        open_pr=False,  # don't invoke git from the test
    )
    assert result["status"] == "edited"
    assert result["summary"] == {"edited": 2, "now_alive": 1, "unresolved": 0}
    new_body = (workspace / "repo-a" / "docs/notes.md").read_text()
    assert "https://old.example/x" not in new_body
    assert "https://moved.example/x" in new_body
    # The Wayback URL embeds the original URL, so search for the
    # markdown link form to confirm the bare reference is gone.
    assert "(https://dead.example/y)" not in new_body
    assert archived in new_body
    # Alive link untouched.
    assert "https://live.example/z" in new_body


def test_handler_skips_missing_file(tmp_path):
    workspace = tmp_path / "ws"
    (workspace / "repo-a").mkdir(parents=True)
    item = {
        "type": "refresh_links",
        "repo": "repo-a",
        "path": "docs/nope.md",
        "details": [{"url": "https://x.example/"}],
    }
    result = handle_refresh_links_item(
        workspace=workspace,
        item=item,
        http_fetcher=_fetcher({}),
        wayback_fetcher=_wayback({}),
        open_pr=False,
    )
    assert result["status"] == "skipped"
    assert result["reason"] == "file_not_found"


# ---------- regression: scheme-less URL (2026-06-01 incident) ---------


def test_default_http_fetcher_handles_schemeless_url_gracefully():
    """A relative URL must not crash urllib with ValueError.

    Regression for the 2026-06-01 incident: a server-side relative
    Location header leaked a scheme-less URL into the queue; urllib's
    `unknown url type` ValueError crashed the entire remediate tick
    for 15 consecutive hourly runs until the bug was fixed.
    """
    from aicg.link_refresh import default_http_fetcher

    result = default_http_fetcher("/en/blog/troubleshooting-network-issues")
    assert result.status is None
    assert "unsupported url scheme" in result.error
    # Critical: no exception escapes the fetcher.


def test_resolve_link_returns_unresolved_for_schemeless_url():
    """End-to-end: scheme-less URL flows through resolve_link cleanly."""
    resolution = resolve_link(
        "/en/blog/troubleshooting-network-issues",
        # Use real default_http_fetcher to exercise the scheme guard;
        # wayback won't be reached because we don't get past HEAD.
    )
    assert resolution.source == "unresolved"
    assert resolution.replacement is None


def test_default_http_fetcher_resolves_relative_location_header():
    """Relative redirect Location headers must be absolutized.

    Without this, the redirect chase in resolve_link would feed the
    relative URL back into the fetcher and produce the scheme-less
    crash inside the chase loop instead of at the entry point.
    """
    from email.message import Message
    from unittest.mock import patch
    from urllib.error import HTTPError

    from aicg.link_refresh import default_http_fetcher

    hdrs = Message()
    hdrs["Location"] = "/en/blog/new-path"

    def _raise(*_a, **_kw):
        raise HTTPError("https://example.com/old", 301, "Moved", hdrs, None)

    with patch("aicg.link_refresh.urllib.request.build_opener") as m:
        m.return_value.open = _raise
        result = default_http_fetcher("https://example.com/old")

    assert result.status == 301
    assert result.final_url == "https://example.com/en/blog/new-path"
