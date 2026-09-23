# AICG Roadmap

The autonomous curriculum pipeline (design: `autonomous-curriculum-pipeline.md`)
is built and live for the AI-infra curriculum. This roadmap tracks where it goes
next: finishing the staged rollout, generalizing it into a domain-neutral engine,
and putting a control plane in front of it.

> Status legend: ✅ done · 🔄 in progress · 🟡 partial · ⏳ planned

**Status @ 2026-06-25.** The engineering spine is complete: §2.1 ✅, §2.2 ✅
(four live domains), §2.3 🟡 (mechanism done; corpora to author), §2.4 ✅, §3 ✅
(`bootstrap-domain`), §4 🟡 (CLI fleet view done; web UI pending), §1 🟡 (P4
executor built; P2/P3/P5 promotion is operational — see below). What's left is by
design human-gated: promoting write-phases to ACT requires watching a live cycle
(flipping `pipeline.phases.*` is the act step, not a code gap), authoring
per-domain corpora is content, creating a GitHub org needs `admin:org`, and the
web control plane is its own build. 486 tests.

---

## 0. Current state (✅)

All P0–P6 phases are implemented, tested, and live on the runner:

- **P0** eval-gate — flag-only judge, calibrated BAR=76 (ACT)
- **P1** author loop — autonomous authoring quality-gated before merge (ACT)
- **P2–P5** re-audit / research-add / retire / package — deciding on real data in
  OBSERVE (dry-run) mode via `aicg org pipeline-tick`, writing nothing. The P4
  retire *executor* is now built (`retire_executor.py`); promoting any of
  P2–P5 to ACT is a watched flag-flip.
- **P6** fan-out — applies across every role / repo in every domain
- **Fleet** — `aicg fleet status` rolls up all four domains (read-only)

---

## 1. Finish the staged rollout — promote write-phases observe → act (⏳)

Each write-phase is live in observe mode; promotion is a watched flag-flip plus a
little act-mode wiring. Do these one at a time, watching each for a cycle.

- **P2 re-audit auto-fix** — add `refresh_stale` to `HANDLED_WORK_TYPES` + a
  regenerate-by-path handler; flip `pipeline.phases.reaudit_autofix` /
  `quality_judge.flag_only=false`.
- **P3 research auto-promote** — wire `research_cycle` promotion into the research
  job (auto-apply qualifying deltas instead of proposing); flip
  `research_autopromote`.
- **P4 retire** — ✅ **executor built** (`retire_executor.py`: `plan_retirement`
  + `scan_dangling_refs` pure, `execute_plan` through injectable seams,
  `git_fs_seams` for production, `dry_run` honored; 5 tests). Remaining: assemble
  `RetiredNode` details + paths in the tick, validate as a real dry-run to a
  branch, then flip `retire` — the operational watch-a-cycle step.
- **P5 package** — wire `plan_monthly_package` into `monthly-release` (tag changed
  repos + build Release tarballs + `ARCHIVE_INDEX.md`); flip `package`.

---

## 2. Domain-neutral engine — generalize beyond AI (🔄 — 2.1/2.2/2.4 done; 2.3 remaining)

The pipeline core is already domain-agnostic. Four changes turn "AI curriculum
tool" into a curriculum engine that works for any profession. Ordered by leverage.

1. **Domain-configurable freshness rubric** ✅ *(highest leverage — the seam; done 2026-06-25)*
   `quality_judge.freshness_dimensions` is now a list of `{name, description}`
   pairs (defaults to the AI set, so the AI curriculum is unchanged). A non-tech
   domain supplies its own — nursing grades `guideline_currency` /
   `regulation_currency`, law `statute_currency` / `caselaw_currency` — and the
   same pipeline grades it. The engine is now provably domain-neutral. (Also
   fixed a latent bug: the freshness prompt was iterating the *quality* dims.)

2. **Multi-tenant config + git/gh plumbing** ✅ *(done 2026-06-25)*
   `config/domains/<name>.yaml` + `aicg.domains` resolution run N domain
   configs, each its own GitHub org + repos + role ladder. **Four domains
   live:** ai-infra (11 roles), ml-engineering (4), ai-engineering (4),
   ai-governance (2). `--domain` flows through every `aicg org` command;
   `aicg fleet status` rolls them up. "Domain" is the tenancy boundary above
   "role."

3. **Per-domain calibration corpus** 🟡 *(mechanism done; corpora to author)*
   `domains.calibration_corpus_path` resolves `calibration/<domain>/corpus/`
   (legacy `calibration/corpus/` for ai-infra), and `calibrate-judge` defaults
   to it per `--domain` — so each tenant picks its own BAR from its own good/bad
   exemplars, and `quality_judge.thresholds` already carries the per-domain BAR.
   The only remaining work is **authoring** each sibling domain's exemplar
   corpus (content, not engineering) — deferred while those domains are
   observe-only with the judge off.

4. **Per-domain research source + role titles** ✅ *(done 2026-06-25)*
   Each domain config carries its own `research` block (postings minimum,
   window, caps) and titled roles with `aliases`; the research prompt and the
   promotion add-threshold consume aliases per role. Every sibling-org role now
   has domain-specific titles + aliases. Mechanism is fully per-domain.

---

## 3. Multi-tenancy & provisioning — `bootstrap-domain` (✅ — org creation aside)

A provisioning capability above the existing per-role `bootstrap-role`:

- Create the GitHub org (or target an existing one). — **manual** (needs
  `admin:org`/web UI; org creation isn't in the runner's token scope).
- Seed the domain's role ladder (entry → senior → architect/lead → exec, or the
  domain's equivalent). — ✅ via `config/domains/<name>.yaml`.
- Scaffold the paired `-learning` / `-solutions` repos per role. — ✅
  **`bootstrap-role` is now domain-aware** (`--domain` + `--create-remotes`);
  repo names/branding resolve from the manifest, not a hardcoded `ai-infra-`
  prefix. Proven end-to-end standing up **ml-engineering-curriculum**
  (2026-06-25): 8 role repos + `.github` profile created & pushed.
- Drop in the domain rubric (§2.1) + a starter calibration corpus (§2.3). — ⏳
- Wire the per-role timers + register the domain config. — register ✅; timers
  are manifest-driven (`install-schedules.sh`) but ai-infra-only so far
  (sibling orgs are observe-only, phases off).
- Hand off to the same P0–P6 pipeline. — ⏳ (gated on enabling phases per domain).

**`aicg org bootstrap-domain` now does this end-to-end** (2026-06-25): reads the
domain manifest, scaffolds every role via the domain-aware `bootstrap-role`
(`--create-remotes` creates + pushes), renders the `.github` org-profile README
(role-ladder table + 4-way ecosystem cross-links, via `domain_provision.py`'s
pure `render_org_profile`), and creates the `.github` repo. The only manual step
left is **creating the empty GitHub org** (needs `admin:org`/web UI). Authoring
`CAREER_PROGRESSION.md` + the per-domain calibration corpus (§2.3) are printed as
follow-ups.

Outcome: standing up a new domain is a configuration + provisioning exercise, not
a rewrite — verified by ml-engineering (provisioned by hand, then codified).

---

## 4. Web UI / control plane (🟡 — CLI fleet view done; UI pending)

Today's surfaces are CLI (`fleet status`, `pipeline-status`, `pipeline-tick`,
`calibrate-judge`) and GitHub-native (status issues, PRs, the heartbeat). A
control plane puts a single pane over the multi-domain fleet.

**Observability**

- ✅ **`aicg fleet status`** — read-only roll-up across all domains: mode
  (ACT/OBSERVE/INERT), enabled phases, judge state + BAR, daily budget, and
  best-effort work-queue depth. The CLI form of the fleet dashboard
  (`src/aicg/fleet.py`, pure read model). A web dashboard would render this
  same model.
- Activity feed: recent merges, retirements, promotions, monthly changelogs. ⏳

**Control**

- Promote a phase observe → act per domain (the staged flag-flip, with a
  confirmation + the last observe output shown).
- Trigger a calibration run; view the good/bad separation + suggested BAR; accept.
- Review the quarantine queue: inspect failing artifacts + rubric scores;
  re-queue, override, or leave flagged.
- Pause / resume a domain or the whole fleet (kill switch).

**Provisioning**

- Launch `bootstrap-domain` from the UI: name the domain, pick the role ladder,
  point at a GitHub org, upload/seed the rubric + corpus.

**Architecture notes**

- Read model from the existing state files (`work-queue.json`,
  `daily-run-state.json`, the per-role manifests, calibration reports) + GitHub
  API; the runner stays the source of truth, the UI is a view + a thin control
  layer that writes config flags / enqueues commands.
- Keep the runner authoritative and the UI optional — the pipeline must keep
  running headless if the UI is down (consistent with the no-single-point-of-
  failure stance).

---

## Sequencing

```text
0 (done) ──> 1 promote P2..P5 (near-term)
         └─> 2.1 rubric-config ──> 2.2 multi-org ──> 3 bootstrap-domain ──> 2.3/2.4 per-domain corpus+source
                                                                        └─> 4 control plane (parallel once multi-domain exists)
```

§2.1 (rubric-config) is the cheapest highest-signal step and gates the rest of
the generalization. The control plane (§4) becomes worthwhile once there's more
than one domain to manage.
