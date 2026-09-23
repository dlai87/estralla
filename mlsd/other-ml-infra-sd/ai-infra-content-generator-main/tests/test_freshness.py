from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from conftest import write_file

from aicg.freshness import (
    FreshnessError,
    VersionTarget,
    audit_links,
    audit_versions,
    review_existing_artifacts,
)


# ---------------------------------------------------------------------------
# Link checker
# ---------------------------------------------------------------------------


def _seed_repo_with_links(tmp_path: Path, urls_by_file: dict[str, list[str]]) -> Path:
    repo = tmp_path / "repo"
    for rel, urls in urls_by_file.items():
        body = "\n".join(f"See [link]({url}) for more." for url in urls) + "\n"
        write_file(repo / rel, body)
    return repo


def test_audit_links_flags_404(tmp_path: Path) -> None:
    repo = _seed_repo_with_links(
        tmp_path,
        {"modules/mod-001/README.md": ["https://dead-site.foo/broken"]},
    )

    def fake_fetch(url: str) -> tuple[int, str]:
        return 404, "Not Found"

    report = audit_links(repo, url_fetcher=fake_fetch)
    assert report["broken_count"] == 1
    assert report["work_items"][0]["type"] == "refresh_links"
    assert report["work_items"][0]["severity"] == "low"


def test_audit_links_severity_escalates_with_count(tmp_path: Path) -> None:
    repo = _seed_repo_with_links(
        tmp_path,
        {
            "modules/mod-001/README.md": [
                f"https://dead-site.foo/broken/{i}" for i in range(6)
            ]
        },
    )

    report = audit_links(repo, url_fetcher=lambda url: (404, "Not Found"))
    item = report["work_items"][0]
    assert item["severity"] == "high"
    assert item["broken_count"] == 6


def test_audit_links_ignores_200_ok(tmp_path: Path) -> None:
    repo = _seed_repo_with_links(
        tmp_path,
        {"modules/mod-001/README.md": ["https://dead-site.foo/ok"]},
    )
    report = audit_links(repo, url_fetcher=lambda url: (200, "OK"))
    assert report["broken_count"] == 0
    assert report["work_items"] == []


def test_audit_links_raises_when_repo_missing(tmp_path: Path) -> None:
    with pytest.raises(FreshnessError):
        audit_links(tmp_path / "missing")


def test_audit_links_skips_archive_and_aicg(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(
        repo / "modules/mod-001/README.md", "[ok](https://dead-site.foo/in-repo)\n"
    )
    write_file(
        repo / "_archive/old.md", "[old](https://dead-site.foo/in-archive)\n"
    )
    write_file(
        repo / ".aicg/notes.md", "[ai](https://dead-site.foo/in-aicg)\n"
    )

    seen: list[str] = []
    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert "https://dead-site.foo/in-repo" in seen
    assert "https://dead-site.foo/in-archive" not in seen
    assert "https://dead-site.foo/in-aicg" not in seen


def test_audit_links_skips_reserved_example_hosts(tmp_path: Path) -> None:
    """RFC 2606 reserved hosts + localhost must not be flagged broken.

    Regression: the queue had 289 ``refresh_links`` items, many for
    docs full of example/placeholder URLs like ``http://localhost:8000``
    and ``https://your-api.example.com``. Audit should drop those at
    collection time so they never reach the work queue.
    """
    skip_urls = [
        "http://localhost:8000/health",
        "http://localhost/path",
        "https://example.com/api",
        "https://example.org/x",
        "https://example.net/y",
        "https://your-api.example.com/v1",
        "https://my-cluster.local/admin",
        "https://placeholder-service.foo/x",
        "https://api.test/x",
        "https://thing.invalid/x",
        "https://service.localhost/x",
        "http://127.0.0.1:9000",
        "http://0.0.0.0:8080",
        "http://10.0.0.5/admin",
        "http://192.168.1.100:8443",
        "http://172.16.0.1/x",
        "http://169.254.169.254/latest/meta-data/",
    ]
    keep_urls = [
        "https://dead-site.foo/x",  # not reserved
        "https://news.ycombinator.com/y",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls + keep_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)

    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 404, "Not Found"

    report = audit_links(repo, url_fetcher=fake_fetch)
    # Only the non-reserved URLs should have been HEAD-pinged.
    assert set(seen) == set(keep_urls)
    # And only those should appear in broken findings / work items.
    flagged = {f["url"] for f in report["broken_findings"]}
    assert flagged == set(keep_urls)


def test_audit_links_skips_k8s_and_docker_placeholder_urls(
    tmp_path: Path,
) -> None:
    """Regression: junior-engineer's queue had 110 high-sev refresh_links
    items, almost all of them pointing at docker-compose service names,
    k8s service DNS, or un-substituted template variables. Those are
    teaching scaffolding — the audit must drop them at collection time.
    """
    skip_urls = [
        # docker-compose service names (bare hostnames, no dot)
        "http://db:5432",
        "http://container-b:8000/health",
        "http://backend-service-correct",
        "http://failing-readiness-svc",
        # k8s short names with .namespace
        "http://jaeger-collector.monitoring:4318",
        # fully-qualified k8s service DNS
        "http://flask-app-dev-flask-app.dev-namespace.svc.cluster.local",
        "http://inference-gateway-v2.ml-inference.svc.cluster.local/health",
        # docker desktop host alias
        "http://host.docker.internal:8000",
        # template placeholders
        "http://${INGRESS_IP}/api",
        "http://$EXTERNAL_IP/health",
        "http://<INGRESS_IP>/admin",
        "http://<service-ip>/admin",
        "http://{{ gateway }}/v1",
        # empty hostname (port-only URL)
        "http://:8000/health",
        # userinfo-prefixed localhost (regression — old splitter
        # mis-read host as "admin")
        "http://admin:admin@localhost:3000/api/dashboards/uid/slo",
    ]
    keep_urls = [
        # Real public domain — should still be checked.
        "https://www.redhat.com/sysadmin/troubleshooting-network-issues",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls + keep_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)

    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int | None, str]:
        seen.append(url)
        if "redhat.com" in url:
            return 404, "Not Found"
        # Everything that slipped past _is_example_url at collection
        # time fails DNS in real life — return None + the canonical
        # Linux getaddrinfo error.
        return None, "url-error: [Errno -2] Name or service not known"

    report = audit_links(repo, url_fetcher=fake_fetch)
    # Only real public URLs should be HEAD-pinged. If something else
    # made it through, _is_example_url has a gap to plug.
    leaked = set(seen) - set(keep_urls)
    # k8s shorthand like jaeger-collector.monitoring is impractical to
    # catch syntactically (no public TLD test we trust). The DNS-failure
    # downgrade in is_broken() handles it at fetch time instead.
    # So we tolerate fetches happening, but require that NOTHING from
    # skip_urls ends up in the broken_findings list.
    flagged = {f["url"] for f in report["broken_findings"]}
    assert flagged == set(keep_urls), (
        f"expected only {keep_urls} broken, but got {flagged}"
    )
    # And the explicit-skip URLs that bypassed fetch entirely.
    explicit_skips_not_fetched = set(skip_urls) - set(seen)
    assert len(explicit_skips_not_fetched) >= len(skip_urls) - 1, (
        f"too many placeholder URLs reached the fetcher: leaked={leaked}"
    )


def test_audit_links_skips_example_subdomains(tmp_path: Path) -> None:
    """staging.example.com / my-svc.example.org / app.example.net are
    all RFC 2606 reservations even though they're subdomains. The
    audit previously only matched the apex domain exactly and reported
    SSL handshake failures from these as broken citations.
    """
    skip_urls = [
        "https://staging.example.com/health",
        "https://my-svc.example.org/v1",
        "https://api.example.net/users",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)
    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert seen == [], (
        f"example.com / .org / .net subdomains should not be fetched; got {seen}"
    )


def test_audit_links_skips_placeholder_company_domains(tmp_path: Path) -> None:
    """SRE / runbook / incident docs constantly cite
    ``wiki.company.com``, ``runbooks.mycompany.com``, ``api.acme.com``
    as stand-in URLs for "your internal tool here". Treat them like
    example.com.
    """
    skip_urls = [
        "https://wiki.company.com/runbook",
        "https://runbooks.mycompany.com/slo",
        "https://api.acme.com/v1/users",
        "https://app.yourcompany.com/dashboard",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)
    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert seen == [], f"placeholder company domains should not be fetched; got {seen}"


def test_audit_links_skips_shell_substitution_in_path(tmp_path: Path) -> None:
    """``https://dl.k8s.io/release/$(curl -s ...)`` is a download
    command published in installation docs — the ``$(...)`` is meant
    to be evaluated by the user's shell, not by the audit's HEAD
    request. PR #28's _PLACEHOLDER_URL_RE only matched between scheme
    and first /; extend to the whole URL.
    """
    skip_urls = [
        # No nested URL — the whole token is one placeholder.
        "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname",
        "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname",
        "https://api.example-svc.com/configs/${VERSION}/manifest.yaml",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)
    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert seen == [], f"shell-substitution URLs should not be fetched; got {seen}"


def test_audit_links_skips_placeholder_slack_and_github_paths(tmp_path: Path) -> None:
    """Slack webhook stubs (``/services/YOUR/SLACK/WEBHOOK``) and
    GitHub placeholder owners (``github.com/user/repo.git``,
    ``github.com/myorg/myrepo``) are documentation conventions, not
    citations.
    """
    skip_urls = [
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "https://hooks.slack.com/services/WORKSPACE/CHANNEL/TOKEN",
        "https://github.com/user/repo.git",
        "https://github.com/YOU/ml-toolkit.git",
        "https://github.com/ORIGINAL-OWNER/ml-toolkit.git",
        "https://github.com/myorg/myrepo",
    ]
    body = "\n".join(f"See [link]({u})." for u in skip_urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)
    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert seen == [], f"placeholder Slack/GitHub URLs should not be fetched; got {seen}"


def test_audit_links_treats_bot_blocking_as_not_broken(tmp_path: Path) -> None:
    """403 / 405 / 429 / 451 mean the URL is reachable but the bot is
    denied. Junior's queue had Udemy 403s and HashiCorp 429s that
    learners can absolutely click and read — flagging them as broken
    citations is a false positive."""
    urls = {
        "https://www.udemy.com/course/docker/": (403, "Forbidden"),
        "https://www.hashicorp.com/resources/x": (429, "Too Many Requests"),
        "https://labs.play-with-docker.com/": (405, "Method Not Allowed"),
        "https://www.linkedin.com/in/example": (999, "Request denied"),
        "https://reddit.com/r/devops": (451, "Unavailable for legal reasons"),
        # Real broken link — still flagged.
        "https://example.tld-does-not-exist/foo": (404, "Not Found"),
    }
    body = "\n".join(f"See [link]({u})." for u in urls) + "\n"
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)

    def fake_fetch(url: str) -> tuple[int, str]:
        return urls[url]

    report = audit_links(repo, url_fetcher=fake_fetch)
    flagged = {f["url"] for f in report["broken_findings"]}
    assert flagged == {"https://example.tld-does-not-exist/foo"}, (
        f"only the 404 should be flagged; got {flagged}"
    )


def test_audit_links_strips_trailing_quote(tmp_path: Path) -> None:
    """Regression: bare-URL extraction left a trailing ``"`` on URLs
    that were the value of a JSON/YAML string in a code sample."""
    body = (
        '```json\n'
        '{"endpoint": "https://dead-site.foo/v1"}\n'
        '```\n'
    )
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", body)

    seen: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str]:
        seen.append(url)
        return 200, "OK"

    audit_links(repo, url_fetcher=fake_fetch)
    assert seen == ["https://dead-site.foo/v1"]
    # The trailing quote MUST have been stripped — otherwise we'd see
    # the URL with the trailing '"' character.
    assert all(not u.endswith('"') for u in seen)


# ---------------------------------------------------------------------------
# Version-pin scanner
# ---------------------------------------------------------------------------


def _registry_with(*targets) -> list[VersionTarget]:
    return list(targets)


def _make_target(**kwargs) -> VersionTarget:
    raw = {
        "id": kwargs.get("id", "pytorch"),
        "name": kwargs.get("name", "PyTorch"),
        "current": kwargs.get("current", "2.5"),
        "deprecated": kwargs.get("deprecated", ["2.0", "2.1"]),
        "pattern": kwargs.get(
            "pattern", r"(?i)pytorch[\s=:@v]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)"
        ),
        "eol": kwargs.get("eol", False),
    }
    return VersionTarget.from_dict(raw)


def test_audit_versions_flags_deprecated(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(
        repo / "modules/mod-001/README.md",
        "Set up PyTorch 2.0 with CUDA 11.8.\n",
    )
    report = audit_versions(repo, targets=_registry_with(_make_target()))
    assert report["finding_count"] == 1
    finding = report["findings"][0]
    assert finding["matched_version"] == "2.0"
    assert finding["severity"] == "high"
    assert report["work_items"][0]["severity"] == "high"


def test_audit_versions_flags_minor_older_as_medium(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(
        repo / "modules/mod-001/README.md",
        "We use PyTorch 2.3 for training.\n",
    )
    report = audit_versions(
        repo,
        targets=_registry_with(
            _make_target(deprecated=["1.10", "1.11", "2.0", "2.1"])
        ),
    )
    finding = report["findings"][0]
    assert finding["severity"] == "medium"


def test_audit_versions_no_flags_when_current(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", "PyTorch 2.5 is recommended.\n")
    report = audit_versions(
        repo, targets=_registry_with(_make_target(current="2.5"))
    )
    assert report["finding_count"] == 0
    assert report["work_items"] == []


def test_audit_versions_eol_always_high(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/README.md", "Use Theano 1.0 for ...\n")
    target = _make_target(
        id="theano",
        name="Theano",
        current="(none)",
        deprecated=[],
        pattern=r"(?i)theano[\s=:v]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)",
        eol=True,
    )
    report = audit_versions(repo, targets=[target])
    assert report["findings"][0]["severity"] == "high"


def test_audit_versions_from_registry_file(tmp_path: Path) -> None:
    registry = tmp_path / "version-targets.yaml"
    registry.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "id": "pytorch",
                        "name": "PyTorch",
                        "current": "2.5",
                        "deprecated": ["2.0"],
                        "pattern": r"(?i)pytorch[\s=:@v]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    repo = tmp_path / "repo"
    write_file(repo / "README.md", "PyTorch 2.0 here.\n")
    report = audit_versions(repo, registry_path=registry)
    assert report["finding_count"] == 1


# ---------------------------------------------------------------------------
# Freshness review
# ---------------------------------------------------------------------------


def test_review_skips_when_judge_disabled(tmp_path: Path) -> None:
    from aicg.judge import JudgeConfig

    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/SOLUTION.md", "# stale\n")
    judge_config = JudgeConfig(
        enabled=False,
        agent_command=None,
        dimensions=(),
        thresholds={"default": 75},
        timeout_seconds=None,
    )

    def fake_judge(**kwargs):
        return None  # judge disabled → skipped

    report = review_existing_artifacts(
        repo, judge_config=judge_config, artifact_judge=fake_judge
    )
    assert report["stale_count"] == 0
    assert report["work_items"] == []
    assert report["findings"][0]["status"] == "skipped"


def test_review_emits_work_item_when_stale(tmp_path: Path) -> None:
    from aicg.judge import JudgeConfig, JudgeVerdict

    repo = tmp_path / "repo"
    write_file(repo / "modules/mod-001/SOLUTION.md", "Use PyTorch 1.10\n")
    judge_config = JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": 75, "freshness": 75},
        timeout_seconds=None,
    )

    def fake_judge(**kwargs):
        return JudgeVerdict(
            score=40,
            dimensions={"api_currency": 10, "version_currency": 5},
            blockers=["References PyTorch 1.10"],
            summary="Stale",
            passed=False,
            threshold=75,
            raw="",
        )

    report = review_existing_artifacts(
        repo, judge_config=judge_config, artifact_judge=fake_judge
    )
    assert report["stale_count"] == 1
    item = report["work_items"][0]
    assert item["type"] == "refresh_stale"
    assert item["severity"] == "high"  # blockers escalate to high


def test_review_defers_on_subscription_limit(tmp_path: Path) -> None:
    from aicg.judge import JudgeConfig, JudgeVerdict

    repo = tmp_path / "repo"
    # Two artifacts: the first triggers the defer, the second should be skipped.
    write_file(repo / "modules/mod-001/SOLUTION.md", "")
    write_file(repo / "modules/mod-002/SOLUTION.md", "")
    judge_config = JudgeConfig(
        enabled=True,
        agent_command="fake",
        dimensions=(),
        thresholds={"default": 75, "freshness": 75},
        timeout_seconds=None,
    )

    def fake_judge(**kwargs):
        return JudgeVerdict(
            score=0,
            dimensions={},
            blockers=["Judge subscription limit reached (five_hour); retry after 2026-05-27T20:00:00Z."],
            summary="",
            passed=False,
            threshold=75,
            raw="",
        )

    report = review_existing_artifacts(
        repo, judge_config=judge_config, artifact_judge=fake_judge
    )
    # Loop breaks on defer; only one artifact recorded.
    assert report["deferred"] is not None
    assert len(report["findings"]) == 1


# ---------------------------------------------------------------------------
# queue_priority severity bias
# ---------------------------------------------------------------------------


def test_severity_bias_promotes_high_refresh_above_structural(tmp_path: Path) -> None:
    from conftest import write_minimal_manifest
    from aicg.org_config import load_manifest
    from aicg.org_runner import queue_priority

    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    repo = "ai-infra-security-solutions"

    structural = {"id": "mod-001", "type": "module_solution_gap", "priority": 100}
    refresh_high = {
        "id": "refresh-stale-mod-001",
        "type": "refresh_stale",
        "severity": "high",
        "priority": 100,
    }
    refresh_low = {
        "id": "refresh-links-mod-001",
        "type": "refresh_links",
        "severity": "low",
        "priority": 100,
    }

    p_structural = queue_priority(manifest, repo, structural)
    p_high = queue_priority(manifest, repo, refresh_high)
    p_low = queue_priority(manifest, repo, refresh_low)

    # Lower priority number = higher priority. High-severity refresh
    # MUST jump structural gaps; low-severity refresh MUST sit after.
    assert p_high < p_structural
    assert p_structural < p_low
