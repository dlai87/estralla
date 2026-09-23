# Curriculum manifest + canonical-source registry + per-role plans

Three structured indexes that ground every AICG content decision.

## Files

| File | Purpose | Updated by |
|---|---|---|
| `curriculum.manifest.json` | Every track, module, exercise, project, and resource across the 27 curriculum repos, with paths + GitHub URLs | `scripts/build-curriculum-manifest.py` (run after any structural curriculum change) |
| `canonical_sources.json` | For each external tool/concept the curriculum cites: canonical URL + known successors (vendor rebrand, deprecation, OCI migration, etc.) | **human-curated** — committed by hand when you learn about a vendor change |
| `curriculum_plan.<role-slug>.manifest.json` (×12) | Per-role traceability: requirement → evidence → GitHub Discussions topics → exercises → projects → solutions → tests | Research cycle proposes deltas; humans approve PRs; `scripts/backfill-curriculum-plans.py` reverse-engineered the initial baseline |
| `curriculum_plan.index.json` | Slim summary across all 12 roles: requirement count + coverage breakdown | Regenerated whenever any per-role file changes |

## Who reads them

| Consumer | File | Why |
|---|---|---|
| `aicg/link_refresh.py` resolver | `canonical_sources.json` | Routes a deprecated vendor URL to the live successor BEFORE falling back to Wayback. Also enforces "always machine-consumed" protection for endpoints like `fulcio.sigstore.dev` |
| `aicg/research.py` agent prompt builder | `curriculum.manifest.json` (via `summarize_manifest_for_prompt`) | Gives the research agent ground truth about what's already covered, so it proposes net-new content instead of duplicating |
| Moderation bot (`/find`, `/ask`) | `curriculum.manifest.json` | Cross-reference lookups by track / module / exercise slug |
| Steward / weekly-audit jobs | both | Detects manifest drift (modules referenced in cross-references that no longer exist; canonical entries whose `successors` are themselves now broken) |

## Rebuilding the curriculum manifest

```sh
python scripts/build-curriculum-manifest.py --workspace ~/path/to/parent-of-repos
# defaults to workspace=parent-of-CWD, output=manifest/curriculum.manifest.json
```

Idempotent — re-run anytime. Reproduces the same output for an unchanged workspace.

Run it after any of these events to keep the manifest in sync:

- A new module / exercise / project lands in a `-learning` or `-solutions` repo
- A research proposal is merged
- A reorganization touches `lessons/` ↔ `modules/` ↔ `projects/` paths

It's cheap (~1 second for the whole workspace) so a wrapper like `scripts/refresh-curriculum-manifest.sh` can be safely called from any pipeline step that mutates curriculum structure.

## Editing canonical_sources.json

Add a new entry when you discover that the curriculum is citing a URL whose canonical form is somewhere else now. Shape:

```json
{
  "name": "Short human label (vendor + topic)",
  "canonical": "https://canonical-url-or-oci://...",
  "topic": ["tag1", "tag2"],
  "rationale": "One sentence: what happened to the original, what's authoritative now.",
  "machine_consumed": false,   // true if the URL is consumed by tooling (helm/oci/cosign), so Wayback must NEVER substitute even if 404
  "successors": {
    "https://old-url-that-was-cited": "https://or-oci-canonical-url",
    "https://another-old-cited-variant": "https://same-canonical"
  }
}
```

The resolver matches both `url` and `url.rstrip("/")` against `successors`, so you don't need separate entries for trailing-slash variants.

## Curriculum plans (per role)

Each `curriculum_plan.<role-slug>.manifest.json` traces the full chain *job title → requirements → exercises/projects/solutions/tests* for one role, with GitHub Discussion topics joined in (W2.3, in progress).

### Shape (excerpt)

```jsonc
{
  "schema_version": 1,
  "role": "junior-engineer",
  "role_title": "Junior AI Infrastructure Engineer",
  "research": { "window_start": "...", "window_end": "...", "postings_sampled": 47, ... },
  "requirements": [
    {
      "id": "REQ-JR-MOD-006-KUBERNETES-INTRO",
      "label": "Kubernetes Intro",
      "frequency": 0.72,
      "provenance": "backfilled",      // research | backfilled | manual
      "requires_confirmation": true,    // backfilled entries MUST set this true
      "evidence": [...],
      "discussion_topics": [...],
      "exercises": ["mod-006-kubernetes-intro/exercise-01-pods-and-deployments"],
      "projects": [],
      "solutions": ["modules/.../SOLUTION.md"],
      "tests": ["modules/.../tests/test_pods.py"],
      "coverage_status": "covered"     // covered | partial | missing
    }
  ]
}
```

### Provenance

- `research` — produced by a research cycle with evidence from job postings
- `backfilled` — reverse-engineered from existing content by `scripts/backfill-curriculum-plans.py`; **must** carry `requires_confirmation: true`
- `manual` — added directly by a human via PR

### Coverage states

- `covered` — has exercises **and** has tests
- `partial` — exercises but no tests, or tests but no exercise/project anchor
- `missing` — no exercise / no anchor at all (next-cycle research target)

### Backfilling from current content

The initial baseline was reverse-engineered from `curriculum.manifest.json` so the agent has continuity to defend against rather than starting empty:

```sh
python scripts/backfill-curriculum-plans.py --workspace ~/path/to/parent-of-repos
```

Each existing module becomes one Requirement (ID format `REQ-<ROLE-CODE>-<MODULE-SLUG>`), each project becomes one Requirement, and tests/solutions are discovered by walking the matching solutions repo.

**Re-run safely:** the backfill produces the same output for an unchanged workspace, *except* that the `generated_at` field on the index updates. To avoid noisy diffs, only re-run when curriculum structure has actually changed.

### Continuity policy

Research proposals are expected to be **mostly empty** — the curriculum is mature and the cohort is mid-flight. The research prompt (in `aicg/org_runner.py:_continuity_bias_section`) requires:

- ≥3 distinct job postings citing a gap in the last 90 days
- requirement frequency ≥0.30
- no existing module that could be incrementally extended

Deltas proposing **>20% additions** or **>10% removals** auto-flag `requires_explicit_approval: true` and route to human review.

### Delta format + apply CLI

Research output and human-authored proposals share a single delta schema (see `src/aicg/curriculum_plan_delta.py`):

```jsonc
{
  "schema_version": 1,
  "role": "junior-engineer",
  "month": "2026-06",
  "rationale": "One paragraph: what market shift drives this delta",
  "research_window": { ... },
  "additions": [
    { "rationale": "...", "requirement": { "id": "REQ-JR-NEW", "label": "...", "frequency": 0.34, "provenance": "research", "evidence": [{...}, {...}, {...}] } }
  ],
  "updates": [
    { "id": "REQ-JR-EXISTING", "frequency": 0.78, "evidence_add": [...], "exercises_add": [...] }
  ],
  "removals": [
    { "id": "REQ-JR-OBSOLETE", "migration_note": "Merged into REQ-JR-X." }
  ]
}
```

**Validator rejects:** additions with <3 evidence items, frequency <0.30, provenance≠"research", ID collisions, updates/removals referencing unknown IDs, high-frequency (>0.50) removals without `migration_note`.

**Validator flags (does NOT reject):** additions >20% of baseline count, removals >10%. Sets `requires_explicit_approval: true` so reviewers must confirm scope.

**Apply via CLI:**

```sh
# Dry-run: validate + show diff, do not write
aicg org plan-delta-apply --role junior-engineer --delta /path/to/delta.json --dry-run

# Apply: writes the updated per-role manifest
aicg org plan-delta-apply --role junior-engineer --delta /path/to/delta.json
```

Updates merge evidence and add to exercise/project/solution/test lists idempotently (existing entries are not duplicated).

## Schema versions

All four file types carry `schema_version: 1`. Bump it (and the matching constants in `src/aicg/manifest.py` / `src/aicg/curriculum_plan.py`) when you make a backwards-incompatible change to the structure. The loader rejects mismatched versions to prevent silent drift.
