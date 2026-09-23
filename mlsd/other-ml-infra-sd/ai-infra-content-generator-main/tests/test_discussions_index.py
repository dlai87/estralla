"""Tests for the Discussions extractor + requirement mapper."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aicg.curriculum_plan import (
    CurriculumPlan,
    DiscussionTopic,
    Requirement,
    ResearchWindow,
    load_curriculum_plan,
)
from aicg.discussions_index import (
    DiscussionThread,
    _light_stem,
    _tokens_from_label,
    enable_discussions,
    fetch_discussions,
    find_thread_matches,
    load_cached_threads,
    map_discussions_to_plan,
    refresh_repo_discussions,
    repo_has_discussions,
    write_cached_threads,
)


def _completed(stdout: str = "{}", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _fake_runner(script: list[subprocess.CompletedProcess]):
    """Return a runner that pops one canned response per call."""
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(list(argv))
        if not script:
            return _completed("{}")
        return script.pop(0)

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


# ---------- stemming ----------


def test_light_stem_handles_common_suffixes() -> None:
    assert _light_stem("kubernetes") == "kubernet"  # -es stripped
    assert _light_stem("deployment") == "deployment"  # no rule applied
    assert _light_stem("running") == "runn"  # -ing
    assert _light_stem("policies") == "policy"  # -ies -> -y
    assert _light_stem("orchestrating") == "orchestrat"
    assert _light_stem("k8s") == "k8s"  # too short to strip


def test_tokens_from_label_filters_stopwords_and_short_tokens() -> None:
    tokens = _tokens_from_label("Module 04 — Network Security for ML Systems")
    assert "modul" not in tokens  # 'module' is a stopword
    assert "and" not in tokens
    assert any(t.startswith("network") or t.startswith("networ") for t in tokens)
    assert any(t.startswith("security") or t.startswith("securit") for t in tokens)
    assert "ml" not in tokens  # below MIN_TOKEN_LEN
    assert any(t.startswith("system") or t.startswith("syste") for t in tokens)


# ---------- repo discussions check + enable ----------


def test_repo_has_discussions_uses_graphql() -> None:
    runner = _fake_runner(
        [
            _completed(
                json.dumps(
                    {"data": {"repository": {"hasDiscussionsEnabled": True}}}
                )
            )
        ]
    )
    assert repo_has_discussions("org", "repo", runner=runner) is True
    # The first call should be a `gh api graphql ...`.
    assert runner.calls[0][:3] == ["gh", "api", "graphql"]


def test_repo_has_discussions_handles_false() -> None:
    runner = _fake_runner(
        [
            _completed(
                json.dumps(
                    {"data": {"repository": {"hasDiscussionsEnabled": False}}}
                )
            )
        ]
    )
    assert repo_has_discussions("org", "repo", runner=runner) is False


def test_enable_discussions_patches_repo() -> None:
    runner = _fake_runner([_completed("{}")])
    enable_discussions("org", "repo", runner=runner)
    # Confirm the PATCH argv contains the repo path and the flag.
    argv = runner.calls[0]
    assert "PATCH" in argv
    assert any("repos/org/repo" in a for a in argv)
    assert any("has_discussions=true" in a for a in argv)


def test_gh_failure_raises_runtime_error() -> None:
    runner = _fake_runner([_completed("", returncode=1, stderr="boom")])
    with pytest.raises(RuntimeError, match="boom"):
        repo_has_discussions("org", "repo", runner=runner)


# ---------- fetch ----------


def test_fetch_discussions_paginates() -> None:
    page_1 = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"endCursor": "C1", "hasNextPage": True},
                    "nodes": [
                        {
                            "number": 1,
                            "title": "Helm chart broken",
                            "body": "kubernetes pod is failing",
                            "url": "https://example/1",
                            "createdAt": "2026-06-01T00:00:00Z",
                            "updatedAt": "2026-06-02T00:00:00Z",
                            "category": {"name": "Q&A"},
                        },
                        {
                            "number": 2,
                            "title": "Announcement",
                            "body": "ignore me",
                            "url": "https://example/2",
                            "createdAt": "",
                            "updatedAt": "",
                            "category": {"name": "Announcements"},
                        },
                    ],
                }
            }
        }
    }
    page_2 = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                    "nodes": [
                        {
                            "number": 3,
                            "title": "Pytest tips",
                            "body": "running tests fast",
                            "url": "https://example/3",
                            "createdAt": "",
                            "updatedAt": "",
                            "category": {"name": "Show and tell"},
                        }
                    ],
                }
            }
        }
    }
    runner = _fake_runner([_completed(json.dumps(page_1)), _completed(json.dumps(page_2))])

    threads = fetch_discussions("repo", owner="org", runner=runner)

    assert [t.number for t in threads] == [1, 3]
    # Announcement was filtered out.
    assert all(t.category != "Announcements" for t in threads)
    # Second call carried the cursor.
    second_call = runner.calls[1]
    assert any("after=C1" in a for a in second_call)


# ---------- cache round-trip ----------


def test_cache_round_trip(tmp_path: Path) -> None:
    threads = [
        DiscussionThread(
            repo="r",
            number=1,
            url="u",
            title="t",
            body="b",
            category="Q&A",
            created_at="c",
            updated_at="u2",
        ),
        DiscussionThread(
            repo="r",
            number=2,
            url="u2",
            title="t2",
            body="b2",
            category="Show and tell",
            created_at="c",
            updated_at="u",
        ),
    ]
    write_cached_threads(tmp_path, "org", "r", threads)
    loaded = load_cached_threads(tmp_path, "org", "r")
    assert len(loaded) == 2
    assert loaded[0].number == 1 and loaded[1].number == 2
    assert loaded[0].category == "Q&A"


def test_load_cached_threads_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_cached_threads(tmp_path, "org", "missing") == []


# ---------- refresh ----------


def test_refresh_auto_enables_when_disabled(tmp_path: Path) -> None:
    # 1: check disabled, 2: PATCH enable, 3: fetch page (no threads, hasNextPage=false)
    runner = _fake_runner(
        [
            _completed(
                json.dumps({"data": {"repository": {"hasDiscussionsEnabled": False}}})
            ),
            _completed("{}"),
            _completed(
                json.dumps(
                    {
                        "data": {
                            "repository": {
                                "discussions": {
                                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                                    "nodes": [],
                                }
                            }
                        }
                    }
                )
            ),
        ]
    )
    report = refresh_repo_discussions(
        "repo", owner="org", cache_dir=tmp_path, auto_enable=True, runner=runner
    )
    assert report.enabled_now is True
    assert report.cached == 0
    assert report.error == ""


def test_refresh_skips_when_disabled_and_auto_enable_false(tmp_path: Path) -> None:
    runner = _fake_runner(
        [
            _completed(
                json.dumps({"data": {"repository": {"hasDiscussionsEnabled": False}}})
            )
        ]
    )
    report = refresh_repo_discussions(
        "repo",
        owner="org",
        cache_dir=tmp_path,
        auto_enable=False,
        runner=runner,
    )
    assert report.skipped is True
    assert report.enabled_now is False


# ---------- matching ----------


def _req(label: str) -> Requirement:
    return Requirement(
        id="REQ-X",
        label=label,
        provenance="backfilled",
        requires_confirmation=True,
    )


def _thread(title: str, body: str = "", category: str = "Q&A", number: int = 1) -> DiscussionThread:
    return DiscussionThread(
        repo="r",
        number=number,
        url=f"https://example/{number}",
        title=title,
        body=body,
        category=category,
        created_at="",
        updated_at="",
    )


def test_find_thread_matches_substring_with_stem() -> None:
    req = _req("Kubernetes Intro")
    threads = [
        _thread("kubernetes pod crashing"),
        _thread("unrelated linux kernel question"),
    ]
    matches = find_thread_matches(req, threads)
    assert len(matches) == 1
    # "kubernet" or "intro" should appear in matched tokens.
    matched_tokens = matches[0][1]
    assert any(t.startswith("kubernet") for t in matched_tokens)


def test_find_thread_matches_handles_inflection() -> None:
    # Label stem "deploy" should match body word "deployed"/"deploying"/"deployments".
    req = _req("Application Deploy")
    threads = [_thread("My deployment is stuck")]
    matches = find_thread_matches(req, threads)
    assert len(matches) == 1


def test_find_thread_matches_returns_empty_when_no_tokens() -> None:
    # Label that produces ONLY stopwords + short tokens.
    req = _req("a to of")
    threads = [_thread("kubernetes anything")]
    assert find_thread_matches(req, threads) == []


def test_map_discussions_to_plan_writes_topics() -> None:
    plan = CurriculumPlan(
        schema_version=1,
        role="junior-engineer",
        role_title="Junior",
        research=ResearchWindow(),
        requirements=(_req("Kubernetes Intro"), _req("Python Fundamentals")),
    )
    threads = [
        _thread("kubernetes 101 question", number=1),
        _thread("python list comprehensions", number=2),
    ]
    new_plan = map_discussions_to_plan(plan, threads)
    by_label = {r.label: r for r in new_plan.requirements}
    assert len(by_label["Kubernetes Intro"].discussion_topics) == 1
    assert "kubernet" in by_label["Kubernetes Intro"].discussion_topics[0].matched_via
    assert len(by_label["Python Fundamentals"].discussion_topics) == 1


def test_map_preserves_existing_manual_topics() -> None:
    manual = DiscussionTopic(thread_url="https://example/manual", matched_via="manual")
    req = Requirement(
        id="REQ-X",
        label="Kubernetes Intro",
        provenance="backfilled",
        requires_confirmation=True,
        discussion_topics=(manual,),
    )
    plan = CurriculumPlan(
        schema_version=1,
        role="junior-engineer",
        role_title="Junior",
        research=ResearchWindow(),
        requirements=(req,),
    )
    threads = [_thread("kubernetes etcd")]
    new = map_discussions_to_plan(plan, threads)
    topics = new.requirements[0].discussion_topics
    assert any(t.matched_via == "manual" for t in topics)
    assert any(t.matched_via.startswith("keyword:") for t in topics)
