# Autonomous Org Automation

This is the target operating model for headless management of the
AI-Infra-Curriculum GitHub org.

## Agent Policy

- **Claude Opus 4.7**: content generation only. This includes curriculum,
  solution, job-requirement, and supplemental content.
- **Codex GPT-5.5**: everything else. This includes repository orchestration,
  audits, validation, work planning, PR/issue/discussion stewardship, release
  tagging, and scheduler control.

The policy is encoded in `config/aicg-org.yaml`. Command strings are intentionally
configurable because headless hosts may use different local wrappers.

The default command path is local CLI only:

- Claude content: `scripts/run-claude-content.sh`
- Codex control: `scripts/run-codex-control.sh`

These wrappers call the `claude` and `codex` commands installed on the headless
host. They do not use Anthropic or OpenAI API tokens.

## Subscription Limits

Claude and Codex subscription sessions can hit 5-hour or weekly limits. AICG
treats those failures as temporary:

- command output is scanned for limit messages
- `.aicg/run-state.json` records `agent_limit_reached`
- org queue items move to `deferred`
- `retry_after` is set to roughly 5 hours, 7 days, or 6 hours for unknown limits
- future daily runs re-enable deferred items after `retry_after`

This keeps cron/systemd jobs healthy while preserving the exact work item that
needs to resume.

## Schedule

Default timers:

- Monthly release: day 1, 02:00.
- Monthly job research: day 1, 05:30.
- Weekly audit: Sunday, 03:00.
- Daily remediation: every day, 04:00.
- Daily stewardship report: every day, 04:30.

Install on a host with:

```bash
scripts/bootstrap-headless-host.sh --workspace /srv/ai-infra-curriculum --scheduler systemd
```

For cron instead:

```bash
scripts/bootstrap-headless-host.sh --workspace /srv/ai-infra-curriculum --scheduler cron
```

Use `--dry-run` first to inspect the generated entries.

## Monthly Release

`aicg org release` plans date-based tags for all learning and solution repos.
The configured format is `v%Y.%m`, producing tags such as `v2026.05`.

The org `.github` repository is included in sync and stewardship operations, but
is not part of the curriculum/solution release tag set by default.

`aicg org release --apply` creates and pushes tags. Per-repo GitHub Actions
should use `templates/github/release-package.yml` to publish `.tar.gz` and `.zip`
assets for each tag.

## Monthly Job Research

`aicg org research` writes one research packet per role under
`.aicg/org/research/<YYYY-MM>/`.

Each packet requires:

- Current job postings and source URLs.
- Normalized requirements in `.aicg/job-requirements.json`.
- Human-readable coverage in `JOB_REQUIREMENTS.md`.
- Links to curriculum paths for covered requirements.
- External learning resources for useful but out-of-scope requirements.

Shared requirements use the lowest-level ownership rule: the lowest-level role
that genuinely needs the skill owns the primary curriculum coverage. Higher
roles link to that owner unless they need different depth or leadership context.

When research changes coverage, generated updates must also keep these files in
sync while preserving their existing format:

- `CURRICULUM.md`
- `CURRICULUM_INDEX.md`
- `README.md`
- `VERSIONS.md`
- org-level README files in the `.github` repo, including `README.md` and
  `profile/README.md` when present

## Weekly Audit

`aicg org audit` runs repo-level audit and planning across all solution repos and
writes `.aicg/org/work-queue.json`.

The work queue is deterministic and sorted by role level, repo, and work item
priority. Daily remediation consumes this queue instead of freely choosing work.

Validation includes format checks for the protected curriculum docs above. The
check is intentionally structural: it catches empty protected files, broken
tables, and suspicious heading hierarchy changes before PRs are considered safe.

## Daily Remediation

`aicg org daily` selects the next ready work item and prepares a content packet
for the configured Claude content agent. If no ready gaps exist, it creates
supplemental content packets for brief, source-backed material under each
learning repo's `supplemental/` directory.

## PR, Issue, And Discussion Stewardship

`aicg org steward` is the autonomous PR auto-merger. By default it runs in
dry-run mode — listing every open PR with its CI rollup, guardrail decision,
and the would-merge verdict — without touching anything. Add `--apply` to
make it real.

```bash
aicg org steward                  # dry-run
aicg org steward --apply          # auto-merge eligible PRs
aicg org steward --apply \
  --ci-timeout 1200 \
  --ci-poll 45 \
  --merge-method squash
```

For each open PR the steward walks the lifecycle:

1. **ci_pending** — `gh pr view --json statusCheckRollup` is polled at
   `--ci-poll` seconds (default 30) up to `--ci-timeout` seconds
   (default 600). A check is pending while its `status` or `state` is
   `IN_PROGRESS`/`QUEUED`/`PENDING`/`WAITING`/`EXPECTED`. Skipped /
   neutral conclusions pass.
2. **ci_passed** (rollup `SUCCESS`) or **ci_failed**/**ci_timeout**.
3. **guardrails_ok** or **guardrails_blocked** — the full PR view is
   fetched and the steward blocks drafts, `do-not-merge`/`wip` labels,
   head ref `main`/`master`, restricted-file changes
   (`.github/workflows/*`, `CODEOWNERS`, `SECURITY.md`,
   `pyproject.toml`, `aicg.yaml`/`yml`), `needs-research` /
   `manual-review` markers in changed files, and `CONFLICTING`
   mergeable state.
4. **would_merge** (dry-run) or **merge_requested** (`--apply`) —
   `gh pr merge --auto --<method> --delete-branch` is invoked so
   GitHub completes the merge once required status checks settle.
5. **merged** when the follow-up `gh pr view` reports `MERGED`.

Every transition is recorded in `<state-dir>/steward-report.json` with
per-PR `history` (timestamp + state). Re-running the steward is safe:
already-merged PRs no longer show up in `gh pr list --state open`, and
dry-run runs make no mutations regardless.

## Bootstrapping A New Role

`aicg org bootstrap-role` scaffolds a paired learning + solutions repo
set for a new role so the autonomous loop has somewhere to land.

```bash
aicg org bootstrap-role \
  --role data-engineer \
  --title "Data Engineer" \
  --level 25 \
  --description "Build ML-grade data pipelines."
```

This:

1. Creates `ai-infra-data-engineer-learning/` and
   `ai-infra-data-engineer-solutions/` with READMEs, LICENSE,
   `.gitignore` (with `.aicg/` excluded), `CURRICULUM.md` placeholder,
   per-side CI workflow, and empty `lessons/` + `projects/` (or
   `modules/` + `projects/`) directories.
2. Appends the role to the org manifest if it is JSON. For YAML
   manifests it prints a snippet for the operator to paste.
3. Writes a curriculum-bootstrap prompt packet at
   `<state-dir>/bootstrap/<role>.md` instructing the content agent to
   (a) research at least 25 current job postings and (b) author
   `<learning-repo>/.aicg/curriculum-plan.json` describing modules,
   exercises, labs, quizzes, and projects.
4. Optionally creates the remote GitHub repos via
   `gh repo create --push` when `--create-remotes` is passed.

After bootstrap, the autonomous loop picks up from there:

- `aicg org research` adds the role to the monthly job-requirements
  research cycle.
- Once the agent lands `<learning-repo>/.aicg/curriculum-plan.json`,
  `aicg org execute-plan --role <id>` (Phase B) scaffolds every
  module + project as on-disk skeletons: `lessons/mod-XXX/README.md`,
  `exercises/`, `labs/`, `quizzes/`, mirrored in
  `modules/mod-XXX/` on the solutions side and
  `projects/project-XXX/README.md` on both sides.
- `aicg org audit` then reports the unfilled exercises and projects
  as work items in the org queue.
- Each subsequent `aicg org daily` picks the highest-priority item,
  runs generate → verify → propagate, and surfaces the PR for the
  steward to merge.

## Content Propagation

When an item passes `aicg verify`, the runner also calls
`aicg propagate` automatically to append a row to the target repo's
`VERSIONS.md` so the changelog records what shipped:

```
| 2026-05-27 | `fill-mod-001-…-solutions` | `mod-001-…` | Fill mod-001 solutions |
```

The row lands inside the table block for the current month (one is
created if it doesn't exist yet). Propagation is idempotent — running
it twice does not duplicate rows.

`CURRICULUM.md` edits are *not* applied automatically because the
schema varies per repo. The propagator emits a suggestion entry per
work item (visible in `<repo>/.aicg/propagate-report.json`); the
agent or operator can apply those edits as part of the same PR.

## Quality Grading

When the manifest enables `quality_judge`, every artifact that passes
the structural verify step gets graded by a configured judge command:

```json
"quality_judge": {
  "enabled": true,
  "agent_command": "{runner}/scripts/run-claude-judge.sh --prompt {prompt} --output-dir {output_dir} --repo {repo} --work-id {work_id} --artifact {artifact}",
  "thresholds": {"default": 70, "module_rationale_missing": 65},
  "dimensions": ["correctness", "clarity", "source_quality", "depth"]
}
```

The judge writes `response.json` to its output directory with the
contract:

```json
{
  "total": 82,
  "dimensions": {"correctness": 22, "clarity": 20, "source_quality": 20, "depth": 20},
  "blockers": [],
  "summary": "Brief rationale."
}
```

Work items move to `verification_failed` when the score sits below
the work-type threshold *or* the judge returned any `blockers`
(fabricated citations, unresolved markers, etc.). The verdict lands
inside each action under `.aicg/verify-report.json` → `actions[].quality`.

`aicg verify --with-quality-grade` opts into judging in dry-run /
operator-driven mode. `aicg org daily` invokes the judge automatically
whenever the manifest's `quality_judge.enabled` is `true`.

## Issue Stewardship

`aicg org issues` reconciles GitHub issues with the work queue:

- `failed_permanently` items get an issue opened (or refreshed via a
  comment when one already exists).
- `deferred` items older than `--stuck-after` hours (default 24) get
  an issue opened — or commented on — so the queue doesn't stall
  silently.
- `verified` items that have an open tracking issue get the issue
  closed automatically with a comment.

```bash
aicg org issues                              # dry-run
aicg org issues --apply                      # open / comment / close
aicg org issues --apply --stuck-after 12     # tighter freshness
```

Tracking issues are labelled `aicg` plus an `aicg:<state>` sub-label
(`aicg:failed-permanently`, `aicg:verification-failed`,
`aicg:stuck-deferred`) so they're queryable via `gh issue list
--label aicg`. Each issue's body carries the `work_id` so subsequent
runs can find and update the existing issue rather than opening
duplicates.

## Discussion Stewardship

`aicg org discussions` is the read-only third leg of the stewardship
triad. It fetches open Discussions via `gh api graphql` for every repo
in the manifest, computes staleness and signal metrics, and flags
items that need human judgment — stale Q&A without an accepted
answer, Ideas threads with traction, posts proposing new
modules/exercises/projects. It never posts comments or marks
anything resolved.

```bash
aicg org discussions                         # always dry-run
```

Output is written to `.aicg/org/discussions-report.json` for human
review. Tunable via the manifest's `automation.discussions` block
(`stale_after_days`, `max_per_repo`, `flag_categories`,
`new_module_keywords`).

## CURRICULUM.md shipped-items append

When `aicg propagate` records a verified work item in `VERSIONS.md`,
it also extends `CURRICULUM.md` if (and only if) the file already
exists. The runner appends a `## Shipped (autonomous)` section at
the bottom of the document with one row per shipped work item:

```markdown
## Shipped (autonomous)

| Date | Work ID | Scope | Title |
|---|---|---|---|
| 2026-05-27 | `fill-mod-001-solutions` | `mod-001` | … |
```

The section is idempotent (rows dedup by `work_id`) and additive
only — the runner never edits the rest of the document. If
`CURRICULUM.md` does not exist, no file is created.

### Future work

- Promoting flagged discussions into the work queue automatically.
- Cross-repo dependency tracking (e.g. learning↔solutions sync).
