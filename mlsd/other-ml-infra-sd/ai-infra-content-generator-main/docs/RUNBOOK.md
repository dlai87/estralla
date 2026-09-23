# AICG Runbook

## Pilot Loop

Run the pilot from `ai-infra-content-generator`:

```bash
aicg audit --workspace .. --repo ai-infra-security-solutions
aicg plan --repo ai-infra-security-solutions
aicg generate --repo ai-infra-security-solutions --module mod-001-ml-security-foundations
aicg verify --repo ai-infra-security-solutions
```

Expected first result: audit finds that `ai-infra-security-learning` has module
exercises while `ai-infra-security-solutions/modules/` only has a placeholder
README. Planning creates `fill-mod-001-ml-security-foundations-solutions` as the
first work item. The audit also walks `projects/` and emits a
`fill-project-XXX-solution` work item for any learning project missing a
paired solution artifact.

If no `generator_command` is configured, `generate` writes the prompt packet to
`.aicg/prompts/<work-id>.md` in the target repo and exits before changing
curriculum content.

### Generate multiple items in one pass

```bash
aicg generate --repo ai-infra-security-solutions --all
```

Drains every pending work item in priority order. Stops early if the
configured content agent reports a 5-hour / weekly subscription limit
(the queue item is recorded as `deferred` with a `retry_after`
timestamp and resumes on a later daily run).

### Verify the agent's output

```bash
aicg verify --repo ai-infra-security-solutions
```

Walks each work item's `actions` array and confirms:

- The target file exists, is non-empty, ends with a newline.
- The required section headings are present (Overview / Implementation /
  Validation / Rubric / Common mistakes / References by default; relaxed
  for module-rationale docs).
- Cited URLs are classifiable against `config/source-registry.json` when
  the work item declared `required_default_sources`.
- No `needs-research` or `manual-review` markers remain.

Work items move from `generated` to `verified` (or `verification_failed`
with diagnostics in `.aicg/verify-report.json`). Both `aicg run` and
`aicg org daily` call `verify` automatically after generation.

### Propagate the changelog entry

```bash
aicg propagate --repo ai-infra-security-solutions
```

After verification succeeds, the runner appends a row to
`VERSIONS.md` recording what shipped (date, work id, scope, title).
Idempotent — re-running does not duplicate rows. Both `aicg run`
and `aicg org daily` invoke propagate automatically after a
successful verify. `CURRICULUM.md` edits are deliberately *not*
applied automatically; the propagator emits per-item suggestions in
`<repo>/.aicg/propagate-report.json` for the agent / operator to
apply as part of the same PR.

### Grade artifact quality

```bash
aicg verify --repo ai-infra-security-solutions --with-quality-grade
```

When the manifest enables `quality_judge`, the verify step invokes a
configured judge command per artifact and parses a JSON verdict
(`total` / `dimensions` / `blockers` / `summary`). Items that score
below the work-type threshold or return non-empty blockers move to
`verification_failed`. `aicg org daily` runs the judge automatically
when `quality_judge.enabled` is `true` in the manifest.

### Reconcile tracking issues

```bash
aicg org issues                              # dry-run
aicg org issues --apply                      # open / comment / close
```

Failed-permanently items get an `aicg:failed-permanently` issue.
Stuck-deferred items (older than `--stuck-after` hours, default 24)
get `aicg:stuck-deferred`. Verified items close any matching open
issue automatically.

### Summarize GitHub Discussions

```bash
aicg org discussions                          # always dry-run
```

Read-only sweep across every repo: pulls open Discussions, flags
stale Q&A without answers, Ideas threads with traction, and posts
proposing new modules / exercises / projects. Report at
`.aicg/org/discussions-report.json`. The runner never posts comments
or marks discussions resolved — that's human judgment territory.

### Execute a curriculum plan

```bash
aicg org execute-plan --role data-engineer
```

After `aicg org bootstrap-role` scaffolds the role and the agent
writes `<learning-repo>/.aicg/curriculum-plan.json`, the
`execute-plan` step scaffolds every module and project listed in the
plan as on-disk skeletons (`lessons/mod-XXX/README.md`,
`exercises/`, `labs/`, `quizzes/`; mirrored under `modules/mod-XXX/`
on the solutions side). The audit picks up the resulting gaps and
the daily loop fills them in over subsequent runs.

## Validate

```bash
aicg validate --repo ai-infra-security-solutions
```

Validation fails while required module solutions are missing. That is expected
before generation. Use `--report-only` when a CI or status job should collect the
report without failing the shell step.

## PR Flow

After generated content has been reviewed locally:

```bash
aicg validate --repo ai-infra-security-solutions
aicg pr --repo ai-infra-security-solutions
```

`aicg pr` creates a branch named:

```text
aicg/YYYY-MM-DD/<repo>/<work-id>
```

The PR body includes the work item, audit summary, validation summary, and a
rollback command.

## Auto-Merge Conditions

Auto-merge is blocked unless all of these are true:

- The branch is not `main` or `master`.
- No force-push operation is requested.
- No restricted files are changed.
- No `# manual-review` markers exist.
- No `needs-research` markers exist.
- Target repo CI is green.
- The PR body includes audit, validation, and rollback information.

Restricted files include GitHub workflow files, `CODEOWNERS`, `SECURITY.md`,
`pyproject.toml`, and `aicg.yaml` or `aicg.yml`.

## Source Policy

Prefer official sources in this order:

1. Official standards such as NIST publications.
2. Official project documentation such as OWASP, MITRE ATLAS, Kubernetes,
   Sigstore, SLSA, and OpenSSF.
3. Practitioner implementation references.

VeriSwarm may only be cited as a practitioner reference. It is not a standards
authority. If a fact is not verified, mark it with `<!-- needs-research: ... -->`
and do not auto-merge.

## Troubleshooting

`Repository was not found`: pass `--workspace` explicitly or run from
`ai-infra-content-generator`.

`No generator command configured`: inspect the prompt packet under the target
repo's `.aicg/prompts/` directory or add `aicg.yaml`.

`Validation failed`: inspect `.aicg/validation-report.json`; parity gaps are
expected until generated module solutions exist.

`Guardrails blocked PR creation`: remove unresolved research markers, switch off
`main`, or route restricted-file changes through manual review.

## Org Automation

The org control plane is manifest-driven. The default manifest is
`config/aicg-org.yaml`.

Useful commands:

```bash
aicg org sync --workspace ..
aicg org release --workspace ..          # dry-run
aicg org release --workspace .. --apply  # creates and pushes tags
aicg org research --workspace ..
aicg org audit --workspace ..
aicg org daily --workspace ..
aicg org steward --workspace ..
```

The configured agent policy is:

- Claude Opus 4.7 for curriculum, solution, requirements, and supplemental
  content generation.
- Codex GPT-5.5 for orchestration, validation, PR/issue/discussion stewardship,
  and scheduler control.

The manifest uses local command wrappers by default and does not require API
tokens:

- `scripts/run-claude-content.sh`
- `scripts/run-codex-control.sh`

The manifest stores model intent separately from CLI command strings so the
headless host can use the exact installed wrappers.

When a local agent hits a 5-hour or weekly subscription limit, AICG records the
failure as `agent_limit_reached`, stores a `retry_after` timestamp, and defers the
queue item until a later daily run.

`aicg org sync` also includes the org `.github` repository. Monthly release tags
remain limited to curriculum and solution repos unless the manifest explicitly
marks an extra repo as releasable.

When job research or generated work changes coverage, updates may need to touch
`CURRICULUM.md`, `CURRICULUM_INDEX.md`, `README.md`, `VERSIONS.md`, and the
org-level README files in `.github`. The validator checks these protected files
for basic format preservation, including table column consistency.
