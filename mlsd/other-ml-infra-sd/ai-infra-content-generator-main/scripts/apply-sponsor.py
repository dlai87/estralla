#!/usr/bin/env python3
"""Add sponsor visibility to every repo across all four curriculum orgs.

Two mechanisms, because the org-level Sponsors page alone never shows inside a
repo (the user's exact problem — people live in the repos):

1. An org-level ``.github/FUNDING.yml`` (in each org's ``.github`` repo) → GitHub
   renders the native **Sponsor** button at the top of *every* repo in the org.
2. A marker-delimited sponsor line in each learning/solutions README, inserted
   right after the site banner, so the link is visible in the rendered content
   too. Idempotent: re-running replaces the block in place.

Each org points at its own ``github.com/sponsors/<org>`` page.

Dry-run by default; pass --apply to commit via the GitHub API.
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
from pathlib import Path

OPEN = "<!-- aicg:sponsor -->"
CLOSE = "<!-- /aicg:sponsor -->"
BANNER_CLOSE = "<!-- /aicg:site-banner -->"

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = REPO_ROOT / "config" / "domains"
ORG_MANIFEST = REPO_ROOT / "config" / "aicg-org.yaml"


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))


def org_to_repos() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for mpath in [ORG_MANIFEST] + sorted(DOMAINS_DIR.glob("*.yaml")):
        data = _load(mpath)
        org = data["org"]
        repos = out.setdefault(org, [])
        for role in data.get("roles", []):
            repos.append(role["learning_repo"])
            repos.append(role["solution_repo"])
    return out


def sponsor_block(org: str) -> str:
    url = f"https://github.com/sponsors/{org}"
    body = (
        f"> 💜 **[Sponsor this curriculum]({url})** — sponsorships keep the whole "
        "open-source AI Career Curriculum free and moving."
    )
    return f"{OPEN}\n{body}\n{CLOSE}"


def apply_sponsor_line(body: str, org: str) -> tuple[str, bool]:
    block = sponsor_block(org)
    if OPEN in body and CLOSE in body:
        pre, rest = body.split(OPEN, 1)
        _, post = rest.split(CLOSE, 1)
        new = pre + block + post
        return new, new != body
    # Insert right after the site-banner close marker if present, else after H1.
    if BANNER_CLOSE in body:
        pre, post = body.split(BANNER_CLOSE, 1)
        new = pre + BANNER_CLOSE + "\n\n" + block + post
        return new, new != body
    lines = body.splitlines()
    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            out.append("")
            out.append(block)
            inserted = True
    if not inserted:
        out = [block, ""] + lines
    new = "\n".join(out)
    if body.endswith("\n") and not new.endswith("\n"):
        new += "\n"
    return new, new != body


def _gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)


def put_file(org: str, repo: str, path: str, content: str, message: str, apply: bool) -> str:
    meta = _gh([f"repos/{org}/{repo}/contents/{path}", "--jq", "{sha:.sha,content:.content}"])
    existing_sha = None
    if meta.returncode == 0:
        m = json.loads(meta.stdout)
        existing_sha = m["sha"]
        if base64.b64decode(m["content"]).decode("utf-8") == content:
            return "unchanged"
    if not apply:
        return "would-write"
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    args = [
        "-X", "PUT", f"repos/{org}/{repo}/contents/{path}",
        "-f", f"message={message}", "-f", f"content={b64}", "-f", "branch=main",
    ]
    if existing_sha:
        args += ["-f", f"sha={existing_sha}"]
    res = _gh(args)
    return "ok" if res.returncode == 0 else f"FAIL:{res.stderr[-160:]}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    org_repos = org_to_repos()
    funding = readme = 0
    for org, repos in org_repos.items():
        # 1. Org-level FUNDING.yml → native Sponsor button on every repo.
        funding_yml = f"github: [{org}]\n"
        status = put_file(org, ".github", "FUNDING.yml", funding_yml,
                          "chore: org-level sponsor button (FUNDING.yml)", args.apply)
        print(f"  [{status}] {org}/.github/FUNDING.yml")
        funding += status in ("ok", "would-write")

        # 2. Per-repo README sponsor line.
        for repo in repos:
            meta = _gh([f"repos/{org}/{repo}/contents/README.md", "--jq", ".content"])
            if meta.returncode != 0:
                print(f"  ?? {org}/{repo}: no README")
                continue
            body = base64.b64decode(meta.stdout).decode("utf-8")
            new_body, changed = apply_sponsor_line(body, org)
            if not changed:
                continue
            status = put_file(org, repo, "README.md", new_body,
                              "docs: add sponsor link to README", args.apply)
            print(f"  [{status}] {org}/{repo}/README.md")
            readme += status in ("ok", "would-write")

    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: {funding} FUNDING.yml, {readme} READMEs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
