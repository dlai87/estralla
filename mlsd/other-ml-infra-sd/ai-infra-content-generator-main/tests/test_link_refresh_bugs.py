"""Regression tests for the three bugs found in production AICG link-refresh PRs.

Bug A — 301/302 / 429 / 403 / HEAD-405 misclassified as broken.
Bug B — Doubled Wayback prefix when the same broken URL appears in N
        resolution slots and Wayback timestamps differ.
Bug C — Wayback substituted into machine-consumed positions (Helm
        repo, OCI, ``pip install -i``, ``git clone``, YAML
        ``repository:``, ``image:``, ``keyless: url:``).

Each test reproduces the failure mode that landed in a real PR
(architect-solutions #5/#6, security-solutions #17/#18, junior-engineer-solutions #7/#8)
so the regression set documents the incident, not just the bug.
"""

from __future__ import annotations

from pathlib import Path

from aicg.link_refresh import (
    FetchResult,
    LinkResolution,
    apply_replacements,
    handle_refresh_links_item,
    resolve_link,
)


# ---------- fetchers ----------


def _http_fetcher(responses: dict[tuple[str, str], FetchResult]):
    """Mock that requires explicit (url, method) match — fails closed."""

    def fetch(url: str, method: str = "HEAD") -> FetchResult:
        key = (url, method)
        if key in responses:
            return responses[key]
        # Fall back to method-agnostic lookup.
        for (u, _m), result in responses.items():
            if u == url:
                return result
        return FetchResult(status=None, final_url=url, error="not_mocked")

    return fetch


def _wayback(snapshots: dict[str, str | None]):
    def fetch(url: str) -> str | None:
        return snapshots.get(url)

    return fetch


# ---------- Bug A: redirects + ambiguous statuses ----------


def test_bug_a_302_redirect_is_followed_not_wayback() -> None:
    """Reproduces architect-solutions #5: charts.bitnami.com -> repo.broadcom.com."""
    url = "https://charts.bitnami.com/bitnami"
    redirect = "https://repo.broadcom.com/bitnami-files/"
    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=302, final_url=redirect),
            (redirect, "HEAD"): FetchResult(status=200, final_url=redirect),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/20220926/https://charts.bitnami.com/bitnami"})

    result = resolve_link(url, http_fetcher=http, wayback_fetcher=wb)

    assert result.source == "redirect"
    assert result.replacement == redirect
    # The Wayback URL must NEVER appear when the redirect resolves cleanly.
    assert "web.archive.org" not in (result.replacement or "")


def test_bug_a_429_rate_limit_is_not_treated_as_broken() -> None:
    """Reproduces junior #7 line 89: hashicorp.com 429 -> Wayback was wrong."""
    url = "https://www.hashicorp.com/resources/what-is-infrastructure-as-code"
    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=429, final_url=url),
            (url, "GET"): FetchResult(status=429, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    result = resolve_link(url, http_fetcher=http, wayback_fetcher=wb)

    assert result.source == "ambiguous"
    assert result.replacement is None  # leave original in place


def test_bug_a_403_anti_bot_is_not_treated_as_broken() -> None:
    """Reproduces junior #8: medium / leetcode / hackerrank live sites, 403 to curl."""
    url = "https://leetcode.com/"
    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=403, final_url=url),
            (url, "GET"): FetchResult(status=403, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    result = resolve_link(url, http_fetcher=http, wayback_fetcher=wb)

    assert result.source == "ambiguous"
    assert result.replacement is None


def test_bug_a_head_method_not_allowed_falls_through_to_get() -> None:
    """play-with-k8s returns HEAD=405, GET=200; bot must use GET result."""
    url = "https://labs.play-with-k8s.com/"
    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=405, final_url=url),
            (url, "GET"): FetchResult(status=200, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    result = resolve_link(url, http_fetcher=http, wayback_fetcher=wb)

    assert result.source == "alive"
    assert result.replacement == url


def test_bug_a_genuine_404_still_falls_back_to_wayback() -> None:
    """Don't over-correct: real 404s in human-read context should still get Wayback."""
    url = "https://gone-forever.example.com/page"
    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    archived = "http://web.archive.org/web/X/https://gone-forever.example.com/page"
    wb = _wayback({url: archived})

    result = resolve_link(url, http_fetcher=http, wayback_fetcher=wb)

    assert result.source == "wayback"
    assert result.replacement == archived


# ---------- Bug B: doubled Wayback prefix ----------


def test_bug_b_duplicate_originals_deduped_in_apply() -> None:
    """Reproduces security-solutions #18: same broken URL appears twice in doc.

    Without dedupe, the second body.replace() finds the original embedded
    inside the first replacement's Wayback wrapper and rewrites it,
    producing ``web.archive.org/X/http://web.archive.org/Y/original``.
    """
    original = "https://atlas.mitre.org/techniques/AML.T0024/"
    archived_a = "http://web.archive.org/web/20231221220723/" + original
    archived_b = "http://web.archive.org/web/20231227104237/" + original

    body = (
        "See the [primary AML.T0024 technique](" + original + ").\n"
        "Also referenced in the playbook: " + original + " — review."
    )
    resolutions = [
        LinkResolution(original=original, replacement=archived_a, source="wayback"),
        LinkResolution(original=original, replacement=archived_b, source="wayback"),
    ]

    new_body = apply_replacements(body, resolutions)

    # First resolution wins, second is dropped — both occurrences of the
    # original URL get the same replacement.
    assert archived_a in new_body
    assert archived_b not in new_body
    expected = body.replace(original, archived_a)
    assert new_body == expected
    # Crucially: no doubled Wayback prefix anywhere in the document.
    assert "web.archive.org/web/20231221220723/http://web.archive.org" not in new_body


def test_bug_b_handler_dedupes_urls_from_audit_details() -> None:
    """The audit can emit the same URL once per occurrence; handler must dedupe."""
    target_dir = Path("/tmp/aicg_bug_b_test")
    target_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = target_dir / "repo"
    (repo_dir / "docs").mkdir(parents=True, exist_ok=True)
    md = repo_dir / "docs" / "x.md"
    original = "https://gone.example.com/a"
    md.write_text(f"[a]({original})\n\n[same a]({original})\n", encoding="utf-8")

    http = _http_fetcher(
        {
            (original, "HEAD"): FetchResult(status=404, final_url=original),
            (original, "GET"): FetchResult(status=404, final_url=original),
        }
    )
    archived = "http://web.archive.org/web/T/" + original
    wb = _wayback({original: archived})

    item = {
        "repo": "repo",
        "path": "docs/x.md",
        "details": [
            {"url": original},
            {"url": original},
            {"url": original},  # duplicate emissions from the audit
        ],
    }

    result = handle_refresh_links_item(
        workspace=target_dir,
        item=item,
        http_fetcher=http,
        wayback_fetcher=wb,
        open_pr=False,
    )

    # All resolutions get logged, but exactly one unique URL is resolved
    # and substituted — no doubled prefix in the file body.
    new_body = md.read_text(encoding="utf-8")
    assert archived in new_body
    assert "web.archive.org/web/T/http://web.archive.org" not in new_body
    assert result["summary"]["edited"] == 1


# ---------- Bug C: machine-consumed contexts ----------


def test_bug_c_helm_repo_add_refuses_wayback(tmp_path: Path) -> None:
    """Reproduces architect-solutions #5 / junior #6: helm chart URL must not become Wayback."""
    repo_dir = tmp_path / "repo"
    (repo_dir / "docs").mkdir(parents=True)
    url = "https://charts.bitnami.com/bitnami"
    md = repo_dir / "docs" / "tutorial.md"
    md.write_text(
        "Install the chart:\n\n"
        "```sh\n"
        f"helm repo add bitnami {url}\n"
        "helm install feast-redis bitnami/redis\n"
        "```\n",
        encoding="utf-8",
    )

    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    item = {"repo": "repo", "path": "docs/tutorial.md", "details": [{"url": url}]}
    result = handle_refresh_links_item(
        workspace=tmp_path, item=item, http_fetcher=http, wayback_fetcher=wb, open_pr=False
    )

    # File body unchanged — Wayback was suppressed because of the helm context.
    assert md.read_text(encoding="utf-8").find("web.archive.org") == -1
    assert result["summary"]["edited"] == 0
    # The resolution must flag this as a machine endpoint for the PR body
    # to surface (so a human can pick a canonical successor like OCI).
    sources = {r["source"] for r in result["resolutions"]}
    assert "machine_endpoint" in sources


def test_bug_c_yaml_repository_field_refuses_wayback(tmp_path: Path) -> None:
    """A YAML ``repository:`` field is machine-consumed even outside a code fence."""
    repo_dir = tmp_path / "repo"
    (repo_dir / "examples").mkdir(parents=True)
    url = "https://kubernetes-charts.example/old"
    md = repo_dir / "examples" / "chart.md"
    md.write_text(
        "Chart.yaml dependencies:\n\n"
        "```yaml\n"
        "dependencies:\n"
        "  - name: redis\n"
        f"    repository: {url}\n"
        "    version: \"17.x.x\"\n"
        "```\n",
        encoding="utf-8",
    )

    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    item = {"repo": "repo", "path": "examples/chart.md", "details": [{"url": url}]}
    result = handle_refresh_links_item(
        workspace=tmp_path, item=item, http_fetcher=http, wayback_fetcher=wb, open_pr=False
    )

    assert "web.archive.org" not in md.read_text(encoding="utf-8")
    assert result["summary"]["edited"] == 0


def test_bug_c_keyless_url_in_clusterimagepolicy_refuses_wayback(tmp_path: Path) -> None:
    """Reproduces security-solutions #17: Sigstore Fulcio URL must not become Wayback."""
    repo_dir = tmp_path / "repo"
    (repo_dir / "modules").mkdir(parents=True)
    url = "https://fulcio.sigstore.dev"
    md = repo_dir / "modules" / "verify.md"
    md.write_text(
        "Apply the policy:\n\n"
        "```yaml\n"
        "apiVersion: policy.sigstore.dev/v1beta1\n"
        "kind: ClusterImagePolicy\n"
        "spec:\n"
        "  authorities:\n"
        "    - keyless:\n"
        f"        url: {url}\n"
        "```\n",
        encoding="utf-8",
    )

    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    item = {"repo": "repo", "path": "modules/verify.md", "details": [{"url": url}]}
    result = handle_refresh_links_item(
        workspace=tmp_path, item=item, http_fetcher=http, wayback_fetcher=wb, open_pr=False
    )

    body = md.read_text(encoding="utf-8")
    assert "web.archive.org" not in body
    assert url in body
    assert result["summary"]["edited"] == 0


def test_bug_c_pip_install_index_url_refuses_wayback(tmp_path: Path) -> None:
    """pip's ``-i`` flag is machine-consumed; Wayback breaks ``pip install``."""
    repo_dir = tmp_path / "repo"
    (repo_dir / "exercises").mkdir(parents=True)
    url = "https://pypi.example.com/simple/"
    md = repo_dir / "exercises" / "setup.md"
    md.write_text(
        "Install the internal mirror:\n\n"
        "```sh\n"
        f"pip install -i {url} my-package\n"
        "```\n",
        encoding="utf-8",
    )

    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    wb = _wayback({url: "http://web.archive.org/web/X/" + url})

    item = {"repo": "repo", "path": "exercises/setup.md", "details": [{"url": url}]}
    result = handle_refresh_links_item(
        workspace=tmp_path, item=item, http_fetcher=http, wayback_fetcher=wb, open_pr=False
    )

    assert "web.archive.org" not in md.read_text(encoding="utf-8")
    assert result["summary"]["edited"] == 0


def test_bug_c_prose_link_still_gets_wayback(tmp_path: Path) -> None:
    """The control case: in a regular markdown link in prose, Wayback is allowed."""
    repo_dir = tmp_path / "repo"
    (repo_dir / "resources").mkdir(parents=True)
    url = "https://gone-blog.example.com/article"
    md = repo_dir / "resources" / "reading.md"
    md.write_text(f"See [this article]({url}) for background.\n", encoding="utf-8")

    http = _http_fetcher(
        {
            (url, "HEAD"): FetchResult(status=404, final_url=url),
            (url, "GET"): FetchResult(status=404, final_url=url),
        }
    )
    archived = "http://web.archive.org/web/T/" + url
    wb = _wayback({url: archived})

    item = {"repo": "repo", "path": "resources/reading.md", "details": [{"url": url}]}
    result = handle_refresh_links_item(
        workspace=tmp_path, item=item, http_fetcher=http, wayback_fetcher=wb, open_pr=False
    )

    assert archived in md.read_text(encoding="utf-8")
    assert result["summary"]["edited"] == 1
