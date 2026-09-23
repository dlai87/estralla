# Autonomous Curriculum Pipeline — Design

**Status:** Design approved (brainstorming complete), pending implementation
**Date:** 2026-06-24
**Author:** Joshua Ferguson (design facilitated)
**Scope:** AICG content-generator + pi-rook systemd timers, all 17 roles × 2 repos

---

## 1. Understanding Summary

- **What:** Evolve AICG into a fully autonomous, self-verifying curriculum pipeline over all 17 roles × 2 repos that (a) authors learning **and** solutions, (b) rolling-audits and regenerates existing content, (c) tracks the job market quarterly to **add new and retire obsolete** content, (d) keeps every README current, and (e) packages a monthly archive — **with no human in the content path.**
- **Why:** The project's purpose *is* the automation — an end-to-end agentic-systems-architecture artifact to demonstrate (autonomy + guardrails), not just a curriculum.
- **Who:** Operator/architect (you); learners as repo consumers. No human reviewers in the loop.
- **Loops & cadences:** continuous/daily authoring; daily rolling re-audit (90-day rotation); quarterly research (add/retire); monthly tag + packaged Release; README refresh on every content change.
- **Guardrail replacing the human:** eval-gate = judge panel + adversarial critic, bounded revise, else quarantine+flag — applied at generation **and** at re-audit.
- **Non-goals:** no human approval step; no separate archive repos; no soft-deprecate-in-place; `main` holds only current content.

## 2. Assumptions (confirmed)

1. **Cost/throughput:** single Claude subscription token (re-secured 2026-06-24). Keep per-run caps, per-role cadence, concurrency 1, daily usage budget that **skips-and-retries** near the limit (fail safe, never stall mid-commit). **Bounded daily throughput is acceptable.**
2. **Reliability:** any auth/API failure → log, skip, retry next cycle; no partial commits; quarantine after N failed revise rounds.
3. **Observability:** GitHub-native only — PRs/issues/Discussions + a daily status-summary issue + quarantine flag issues. No new dashboard.
4. **Orchestration:** keep `systemd --user` timers as scheduler + `aicg org` subcommands as the pipeline; no new long-running orchestrator service.
5. **Evidence gate stays** (≥3 postings incl. aliases) for what research *proposes*; full autonomy governs *merging*, not the evidence bar.

## 3. Decision Log

| # | Decision | Alternatives rejected | Rationale |
|---|----------|----------------------|-----------|
| 1 | **Autonomy boundary = full autonomy.** Research auto-promotes delta → auto-archive → auto-execute → auto-generate. No human merge gate. | Risk-tiered auto-merge; gate-deletions-only; notify-and-timeout | Project purpose is end-to-end agentic automation. |
| 2 | **Quality gate = eval-gate + adversarial verify.** Generate → judge panel (rubric ≥ bar) + adversarial critic (no blockers) → pass merges; fail revises ≤N, else quarantine+flag. | Single judge; canary+rollback; generate-only (trust) | Removing the human means content must self-verify before `main`; mirrors mod-204 evaluator-optimizer. |
| 3 | **Archive model = monthly tags/Releases.** Deprecated content `git rm`'d from `main`; recovery via tag `vYYYY.MM` + Release tarball. | In-place `/archive` dir; separate archive repo; soft-deprecate | Unifies deprecation + monthly packaging into one mechanism; `main` stays lean = "current market." |
| 4 | **Audit loop = rolling re-audit + auto-regenerate.** Daily slice, **90-day target** rotation; failures requeue through eval-gate; passes stamp scan date. | Weekly batch; monthly pre-release; rolling flag-only | Cost-smoothed, reuses existing review cooldown. **Freshness is SOFT** (amended by C-B3): the 90-day rotation lengthens and is surfaced under backpressure or protected-set deferral; the HARD token budget (D5) always wins. |
| 5 | **NFRs:** bounded daily throughput; GitHub-native observability; retire/replace **decoupled** (retire on decline now, replace later only when evidence supports). | Unbounded throughput; dedicated monitoring; coupled replace | Stay within one subscription; avoid curriculum flapping. |
| 6 | **Orchestration = Approach A** (extend timers + `aicg org` subcommands; reuse typed work queue). | B unified state-machine rewrite; C long-running orchestrator agent | Lowest risk, deterministic, observable, matches confirmed assumptions; borrows B's queue without the rewrite. |

## 4. Final Design

### 4.1 System map & loops

Scheduler (systemd timers) → stateless oneshot jobs (`aicg org` subcommands) → shared state (curriculum-plan files + typed work queue). Every job: `sync` → one bounded unit → commit/push → exit.

| Loop | Cadence | Does | Built from |
|------|---------|------|-----------|
| Sync | start of every job | `git pull --ff-only` all 34 repos | exists |
| Author | daily, bounded | drain queue (new-module learning, solutions, audit re-gen) through eval-gate → merge | extend `daily-remediate` |
| Re-audit | daily slice | audit next artifacts (90-day rotation); failures enqueue regen | repurpose per-role `review` + `quality_judge` ON |
| Research | quarterly/role | market scan → delta; auto-promote additive (evidence ≥3) → enqueue; auto-retire declined → `git rm` + plan update | change `research` cadence + add auto-promote/retire |
| Package | monthly | tag `vYYYY.MM` **changed** repos + build Release tarballs + per-repo changelog (idempotent/resumable) | extend `monthly-release` |
| README-refresh | every content change | deterministic regen from plan + filesystem, **in the same commit** (off LLM budget, not a queue item) | new step |
| Status | daily | post summary issue (merged / quarantined / queue depth / budget) + ping external heartbeat (C-B2) | new, GitHub-native + heartbeat |

Key shift: research drops nightly → **quarterly**; freed cadence funds Author + Re-audit.

### 4.2 Work queue & plan state

Plan node fields:

```text
status: planned | authoring | active | quarantined | retired
last_scan: YYYY-MM-DD        # 90-day re-audit rotation
evidence_count: int          # postings incl. aliases
content_hash: <sha>          # drift / dedupe
```

Queue item: `{ role, target, type, priority, attempts, enqueued_by }`
Types: `module_needs_learning | exercise_needs_solution | artifact_needs_regen`
(README refresh is **not** a queue item — it's a deterministic, off-budget, same-commit step; see S6/U-M7/§11.)

Producers (Research, Re-audit) enqueue; the **Author loop is the sole consumer**. `attempts` bounds eval-gate revise rounds → quarantine. Concurrency guarded by `.aicg/org/aicg-org.lock`; items idempotent. **Exercise and its solution are one coupled unit** (U-M6): regen of either enqueues the pair; the solution records the exercise `content_hash`, a mismatch flags + reprioritizes.

**Retire/replace = plan state, decoupled:** retire sets `status: retired` → Author companion `git rm`s files + refreshes README; the retired stub stays in the plan so it's never re-proposed. Replace is a *separate later* event when a new requirement clears evidence ≥3.

### 4.3 Eval-gate (shared verify core)

```text
eval_gate(node):
  draft = generate(node)
  for round in 1..MAX_REVISE (=3):
     panel  = [judge(draft, rubric) x3]
     critic = adversary(draft)            # find-blockers persona; tool-backed where runnable
     if median(panel) >= BAR and not critic.blockers:
         return MERGE(draft)
     draft = revise(draft, panel.issues + critic.blockers)
  return QUARANTINE(node)
```

- Panel of 3 + 1 adversary; median resists one bad score; adversary defaults to "blocker" when unsure.
- Rubric per-artifact-type, version-pinned in manifest. Runnable artifacts → critic runs pytest/markdownlint (evidence, not opinion).
- Pass = median ≥ BAR **and** zero blockers.
- Bounded revise (3) → quarantine; never infinite, never silent ship.
- On merge: refresh the repo's README **in the same commit** (deterministic, off the LLM budget) → stamp `last_scan` + `content_hash`. No transient README/filesystem disagreement (U-M7).
- Re-audit calls the **same** gate on existing nodes — audit & authoring share one quality bar.

### 4.4 Quarterly research — add & retire

```text
research(role):
  reqs = scrape(title + aliases)
  # ADD
  for r in reqs where freq high and evidence_count >= 3 and not covered:
      add node status=planned; enqueue module_needs_learning
  # RETIRE (hysteresis)
  for node in plan.active:
      node.evidence_count = current support
      if support < FLOOR for RETIRE_QUARTERS (=2) consecutive:
          node.status = retired; enqueue git-rm + readme refresh
```

Asymmetric thresholds (add at ≥3 + high freq; retire only after 2 consecutive sub-FLOOR quarters ≈ 6 months) prevent flapping. Auto-promote applies the validated delta straight to `curriculum-plan.json` (no proposal PR). Per-run caps bound a quarterly burst; overflow drains over days via the bounded Author loop (freshness is soft, D4). Retired content survives only in monthly tags.

**Retire guards (Rounds 1–3):** the S3 circuit breaker (min-sample, >15%-drop anomaly halt, ≤1 retire/role/quarter), the S7 reconciliation gate (`git rm` set == plan `retired` delta, in-commit changelog + `RETIRED.json`), the U-H3 dangling-reference scan (no retire finalizes while surviving content still references the node), and the U-M8 protected set (never retire a node the active `cohort-N` term is teaching) all gate retirement. **Blocked-retire precedence (C5):** a retire blocked by an unresolved dangling-ref or a failed cross-ref regen **defers to the next cycle — it never holds the lock or spin-waits.** Retirement is always *deferred*, never *cancelled*; it resumes when refs are clean and the term boundary passes.

### 4.5 Monthly tag & package (archive)

```text
package():                      # monthly, 1st
  ver = vYYYY.MM
  for repo in all_34:
     git tag -a {ver}; git push origin {ver}
     tar = build_tarball(repo @ {ver})        # role-{ver}.tar.gz
     gh release create {ver} tar --notes=changelog(prev..{ver})
  update org ARCHIVE_INDEX.md
```

Tag = integrity anchor; Release + tarball = human-facing, downloadable, dated archive. Auto-changelog states what was **added/retired** that month (plan-node status diff) — backed per-repo by `CHANGELOG.md` and retire **tombstones** (U-H4), so a learner following an old link hits a signpost, not a 404. `ARCHIVE_INDEX.md` on the org profile lists every version. Packaging is **idempotent and resumable** (per-repo tag state recorded; a re-run resumes only unfinished repos; index built from actually-pushed tags — S8) and snapshots `main` as-is (not release-gated by audit). Lock serializes against in-flight commits and is **yielded within a bounded window** so packaging can't starve daily ticks (C-M3). **Only repos changed since the last tag are tagged/packaged** (S10); the rest are recorded as "unchanged since vX." Version alignment is *eventual*, not atomic.

### 4.6 Failure handling, throughput, observability

```text
every job: acquire lock | exit
  sync; if auth/API 401|429|5xx → log, release, EXIT 0
  do ONE bounded unit: write → verify → commit → push
  on error mid-unit → git reset --hard → exit   # no partial commit
```

- **Fail-safe:** auth failure → skip tick, retry next; idempotent items lose nothing; never half-written `main`.
- **Throughput:** per-day token budget (HARD; D5). Author drains under **fair-share** reserved fractions (e.g. regen 45 / new-learning 30 / solutions 20 / reserve 5 — S6), so new content is never fully starved; README refresh is off-budget (same-commit). Under sustained backpressure the **soft** 90-day rotation lengthens and is surfaced — freshness yields to budget (C-B3), as does protected-set deferral (U-M8).
- **Observability (GitHub-native):** daily Status issue (merged / quarantined / queue depth / budget / skipped-auth ticks); quarantine flag issues (failing rubric + blockers); monthly changelog Releases.

## 5. Testing & Phased Rollout

**Calibrate eval-gate first:** run offline against known-good (hand-authored agentic content) and known-bad (deliberately broken) corpora; tune `BAR` until good passes / bad fails with margin.

**Phased enablement (pilot = `agentic-ai-developer`):**

```text
P0  quality_judge ON, FLAG-ONLY (calibrate on live content, no auto-fix)
P1  schedule Author loop (learning), budget=tiny, pilot only
P2  enable rolling re-audit → auto-regenerate, pilot only
P3  enable quarterly research ADD (auto-promote), pilot only
P4  enable RETIRE (destructive) — dry-run git-rm to a branch first
P5  enable monthly package
P6  fan out to all 17 roles
```

Retire (P4) ships last and proves itself as a no-push dry-run before touching `main`.

**Automated tests:** evidence math + add/retire hysteresis (no flapping); queue idempotency (re-run = no-op); retire removes exactly the right files + updates plan; README refresh matches filesystem; budget bounding stops at cap; fail-safe leaves no partial commit after injected mid-unit error.

**Rollback:** monthly tags + `git revert` recover any bad batch; quarantine prevents most bad content from shipping.

## 6. Risks Acknowledged

- **Autonomous writes to public repos** — mitigated by eval-gate, quarantine, phased rollout, monthly-tag rollback.
- **Destructive retire on `main`** — mitigated by hysteresis, dry-run gate (P4), tag recovery.
- **Single-token cost/limit** — mitigated by bounded budget + skip-and-retry.
- **Quality-bar miscalibration** — mitigated by known-good/known-bad calibration before the gate is trusted.

## 7. Implementation Handoff

High-impact (autonomous public-repo writes). Multi-agent design review **complete** — Skeptic (§8), Constraint Guardian (§9), User Advocate (§10), Arbiter (§11). Disposition: **APPROVED** after P0 reconciliation. Implement per phase P0→P6.

## 8. Review Round 1 — Skeptic (Phase 2)

Ten objections raised. Designer dispositions below; Arbiter ratifies in Phase 3. Accepted items amend the design as stated.

| # | Objection (sev) | Disposition | Design change |
|---|-----------------|-------------|---------------|
| S1 | Eval-gate is the generator judging itself — same model family = one error distribution sampled 4×, not 4 independent observers. Median resists *random* not *correlated* error. (CRITICAL) | **ACCEPT** | **Judge independence is now a hard requirement.** (a) The adversarial critic runs on a **different model family** (non-Claude via API) so the blocker-finder doesn't share the generator's priors. (b) Pedagogical/currency claims must be **grounded against external sources** — the critic fetches current vendor docs (Context7/web) and flags any claim it cannot corroborate; "self-consistent" is not "correct." (c) Runnable artifacts keep the deterministic checks (pytest/markdownlint). The gate is now *cross-check against heterogeneous models + external evidence*, not self-verification. |
| S2 | BAR calibrated once against a fixed corpus while model/rubric/content distribution drift; subscription model silently upgrades. (CRITICAL) | **ACCEPT** | **Recalibration becomes an ongoing control.** A held-out gold/bad set re-runs weekly and **on detected model-version change**; if its pass/fail margin shifts beyond tolerance, the gate **halts new merges and opens a flag issue** until BAR is re-tuned. Calibration is a control loop, not a one-shot P0 step. |
| S3 | Autonomous `git rm` driven by an uncharacterized scraper; a source outage → correlated `evidence_count` collapse → mass-retirement event. Hysteresis guards flapping, not measurement failure. (CRITICAL) | **ACCEPT** | **Retire circuit breaker + scraper characterization.** (a) Scraper source, retry/backoff, and a **minimum absolute posting sample** per cycle are specified; a cycle below min-sample is "no data," not "zero evidence" — it cannot trigger retire. (b) **Anomaly guard:** if >15% of a role's active nodes drop below FLOOR in one cycle, the cycle is treated as measurement failure → **halt retire, flag, execute nothing.** (c) **Per-cycle retire cap** (≤1 node/role/quarter). Retirement is now defended against correlated scrape failure, not just flapping. |
| S4 | Closed 90-day loop (model authors → same model audits → same model regenerates, no external signal) → drift toward judge-pleasing, not correct. `content_hash` detects change, not rot. (HIGH) | **ACCEPT** | Folds into S1. **Re-audit must ground against fresh external sources**, not re-judge in a vacuum. **No-op regen guard:** a node is regenerated only when the audit cites a *concrete external defect* (stale API, dead link, failed check), never on a bare score wobble — this breaks the self-reinforcing loop. Judge-score-vs-time is tracked; a downward trend opens a flag (drift detector, ties to S2). |
| S5 | Bounded single-token consumer fed by unbounded producers (quarterly burst + every re-audit failure + every README) → queue may grow monotonically; "drains over days" asserted, never shown. (HIGH) | **ACCEPT** | **Steady-state invariant + backpressure.** Steady-state production = (re-audit slice × failure-rate f) + rare research bursts; consumption = daily budget. Implementation must assert `consumption ≥ production` at the chosen slice/budget, and a **backpressure rule**: if trailing-7-day queue depth rises, auto-throttle the re-audit slice / lengthen the rotation beyond 90d (and surface it) rather than let the queue grow unbounded. Queue depth is a first-class Status metric with an alert threshold. |
| S6 | Strict priority `regen > solution > new-learning > readme` → under budget pressure, regen starves the system's actual purpose (new content) and README never runs → contradicts "keep READMEs current." (HIGH) | **ACCEPT** | **Fair-share budget, not strict priority:** reserved budget fractions per class (e.g., regen 45% / new-learning 30% / solutions 20% / reserve 5%) so new content can never be fully starved. **README refresh moves OFF the LLM budget entirely** — it's a deterministic regen-from-(plan+filesystem) step run at commit time, so it can't be starved and isn't competing for tokens. |
| S7 | Changelog is the *only* human-readable record of deletions, yet derived and unverified; git-rm could desync from the plan's retired set. (HIGH) | **ACCEPT** | **Reconciliation gate at retire/tag:** assert the `git rm`'d file set == plan's `retired` delta before the commit finalizes; changelog + a machine-readable `RETIRED.json` are written **in the same commit** as the deletion. If reconciliation or changelog generation fails, the retire does not finalize. |
| S8 | `package()` loops tag→push→release across 34 repos with no cross-repo atomicity; a mid-loop failure leaves versions misaligned and `prev..ver` ranges broken. (MEDIUM) | **ACCEPT** | **Idempotent, resumable packaging.** Per-repo tag state is recorded; a re-run resumes only the unfinished repos; `ARCHIVE_INDEX.md` is built from **actually-pushed** tags. The false "atomic alignment" invariant is dropped — alignment is *eventual*, and a repo missing this month's tag is shown as such. |
| S9 | Quarantine has no drain path; for re-audited LIVE content it detects bad content but keeps serving it, and blind re-enqueue burns budget on deterministic failures. (MEDIUM) | **ACCEPT** | **Quarantine policy.** (a) When re-audit quarantines **live** content, the system acts rather than silently serving known-bad: it **reverts that artifact to its last-good tagged version** (or posts an "under revision" stub) so `main` never knowingly serves failing content. (b) Quarantined nodes are **not blindly re-enqueued**; they wait on a change signal (new model version, rubric update, or the cited external defect resolving) with exponential backoff, and carry a GitHub issue — the single sanctioned human touchpoint. |
| S10 | Tagging+packaging all 34 repos monthly even when unchanged = version inflation + storage churn for no-op snapshots (YAGNI). (MEDIUM) | **ACCEPT (modified)** | Only tag/package repos **with changes since last tag**; `ARCHIVE_INDEX.md` records "unchanged since vX" for the rest. Keeps the time-machine value without no-op churn. (Designer note: cross-role version *alignment* was already downgraded to eventual in S8, so per-repo tagging loses nothing real.) |

**Net effect on the safety case:** the three structural weaknesses the Skeptic named — circular verification (S1/S4), static calibration (S2), and destructive action on uncharacterized input (S3) — are now addressed by, respectively, model/evidence heterogeneity, a recalibration control loop, and a retire circuit breaker. The throughput objections (S5/S6) convert "asserted to drain" into a proven invariant + backpressure + fair-share. These are material; the design is stronger for them.

## 9. Review Round 2 — Constraint Guardian (Phase 2)

Three BLOCKERs, four HIGH, three MEDIUM. The Guardian's central, correct point: several Round-1 amendments (S1/S2/S9) added cost, a credential, or a human-gated halt that was never re-costed against the **one-Pi / one-token / no-operator** envelope. Resolutions below; some **amend** Round-1 items.

| # | Objection (sev) | Disposition | Design change |
|---|-----------------|-------------|---------------|
| C-B1 | S1's "different model family" critic = a **second paid API** (key, billing, rate limit), never budgeted; violates the single-subscription assumption. (BLOCKER) | **ACCEPT → amends S1** | **Drop the second-model requirement.** Independence that matters is independence from the *generator's priors*, and **external ground truth supplies that on the same model**: the critic must (a) run deterministic checks first (pytest, markdownlint, link-liveness), and (b) **fetch current vendor docs and corroborate every currency/correctness claim against the fetched text — fail-closed if it cannot cite a source.** A same-family model forced to ground each claim in retrieved evidence is no longer "judging itself." A genuinely independent second model stays an **optional future enhancement** if/when separately funded — **not required**, so the one-token cost model holds. This also dissolves the second-credential parts of C-H2/C-H4/C-M1. |
| C-B2 | Single token already failed silent once; `401 → EXIT 0` with the only alert (Status issue) posted *by the same token* = re-creates the exact silent outage. (BLOCKER) | **ACCEPT** | **Out-of-band dead-man's-switch.** Each successful job pings an external uptime monitor (e.g. healthchecks.io); if pings stop for > T, the external service emails/SMSes the operator — **independent of the Pi and the token.** Additionally, jobs emit a token-age warning when `expiresAt` is within 14 days. Silent EXIT 0 is fine for one tick; terminal silence is not. (NFR upgraded: observability is GitHub-native **plus one external heartbeat** — the minimum needed to not fail silent.) |
| C-B3 | Steady-state invariant (S5) has no arithmetic; worst-case unit is ~13 model passes; on one Pi at concurrency 1, D4 (90-day) and D5 (budget) can't both be assumed true. (BLOCKER) | **ACCEPT** | **Dimension it now + make re-audit cheap + declare which guarantee is soft.** (1) Re-audit is **deterministic-first**: most artifacts get a cheap scan (link/check/diff against fetched docs); the LLM gate fires **only when a defect is suspected**, and full regen (the expensive 13-pass path) **only when a concrete defect is cited** (S4 no-op guard). So steady-state ≈ ~25–35 *cheap* scans/day + a low rate of real regens, not 35 full gates/day. (2) Rough sizing: ~2–3k artifacts / 90 ≈ 25–35/day cheap scans — feasible; full gates reserved for new authoring + cited defects, drained under fair-share budget. (3) **D5 (token budget) is HARD; D4 (90-day freshness) is SOFT.** Under sustained backpressure the rotation lengthens and is surfaced — freshness yields before budget, because blowing the limit is the failure that already bit us. P1 must **measure** real units/day and confirm the inequality; if it fails, rotation relaxes, not the budget. |
| C-H1 | Single Pi: disk-full (34 clones + tarballs), clock skew (drives retire windows + tags), reboot (needs lingering) all unspecified. (HIGH) | **ACCEPT** | **Operational preconditions at job start:** disk-headroom check (skip+flag below threshold); tarballs built in tempdir and deleted after upload (also C-M3); NTP-sync required (retire windows + `vYYYY.MM` depend on a correct clock); `loginctl enable-linger rook` confirmed so timers survive reboot. |
| C-H2 | Credentialed autonomous push + `gh release` to 34 **public** repos from a Pi; blast radius / credential storage undefined (supply-chain surface). (HIGH) | **ACCEPT** | **Least-privilege + locked storage.** GitHub token scoped to exactly the org's repos (not whole account); all credentials outside repo trees, `chmod 600`, service-user only (Claude token already moved to `~/.config/aicg/claude-auth.env` 0600). Rotation runbook documented. Release/tag provenance noted as a future hardening (signing) — not blocking, but recorded. |
| C-H3 | Scraper still unnamed; major boards forbid automated scraping (IP ban → looks like low evidence → drives destructive retire); ToS/legal unaddressed. (HIGH) | **ACCEPT — gates P4** | **RETIRE does not ship until the posting source is a named, ToS-compliant API/dataset** (sanctioned jobs API or licensed feed — not LinkedIn/Indeed scraping). The source's expected baseline volume is recorded so "degraded-but-nonzero" is detectable, not just "zero" (sharpens S3's min-sample). Until then the ADD path may run (additive, non-destructive); RETIRE stays disabled. |
| C-H4 | S2 recalibration adds recurring cost on both creds **and** a silent model upgrade can auto-halt all merges indefinitely — an unbounded human-gated outage in a "no-human" system. (HIGH) | **ACCEPT → amends S2** | Second-cred cost removed by C-B1. **Bound recalibration:** small capped gold/bad corpus, weekly + on-model-change, with a cost cap. **Halt is scoped + alerted + bounded:** a margin-drift halt pauses *new merges only* (audits/reverts still run), fires the C-B2 out-of-band alert, and escalates if unresolved past a max-halt window — never silent, never indefinite. |
| C-M1 | "No human reviewers" ≠ "no operator." S1/S2/S3/S9 created maintained assets (corpus, rubrics, quarantine issues) with no owner or cadence. (MEDIUM) | **ACCEPT** | **Document the operator role explicitly** (you). Maintenance cadence assigned: calibration corpus refresh (quarterly), rubric version bumps (as needed), quarantine-issue response SLA (S9's touchpoint). "No human in the **content path**" stands; "an operator owns the **system**" is now stated, not implied. |
| C-M2 | Lock has no stale-lock/crash recovery; a SIGKILL'd holder wedges all 7 loops silently (second silent-stall path). (MEDIUM) | **ACCEPT** | Lock carries **PID + timestamp**; a lock older than a max-hold TTL whose PID is dead is auto-broken with a flag. Prevents one OOM/power-loss from indefinitely wedging the pipeline (and C-B2's heartbeat catches it if it does). |
| C-M3 | Monthly packaging on a Pi has no storage/bandwidth bound and can hold the lock long, starving daily ticks. (MEDIUM) | **ACCEPT** | Tarballs in tempdir, deleted after successful `gh release`; packaging wall-clock capped and **must not hold the lock longer than a bounded window** (yields to Author/Re-audit ticks). |

**Net effect:** the single biggest correction is C-B1 — reverting S1 from "second model" to "external-evidence grounding on one model," which keeps the independence guarantee *and* the one-token budget, and collapses the second-credential cost/security/maintenance objections (C-H2/H4/M1) at the same time. C-B2 (out-of-band heartbeat) and C-B3 (D5 hard / D4 soft + deterministic-first re-audit) close the two ways this system could silently die or blow its budget — the failure modes most specific to this hardware. C-H3 correctly holds the destructive RETIRE path hostage to a real, ToS-clean data source.

## 10. Review Round 3 — User Advocate (Phase 2)

Four HIGH, four MEDIUM, two LOW — all on the *consumer's* lived experience (learners, cohort instructors), which Rounds 1–2 didn't touch. All resolvable as UX-level defaults; no architecture change. They converge into three additions: a **committed-user protection** layer, a **referential-integrity** rule, and a **transparency** layer.

| # | Objection (sev) | Disposition | Design change |
|---|-----------------|-------------|---------------|
| U-H1 | Cohort instructor preps a Zoom lesson from a module that regenerates/retires before class; paid students see a repo that contradicts the deck. No content pinning for the teaching window. (HIGH) | **ACCEPT** | **Cohort freeze (committed-user protection).** The cohort teaches from a pinned **`cohort-N` tag/branch**, not live `main`. The autonomous pipeline updates `main` continuously; the cohort ref advances **only by a deliberate operator action between terms**. Instructors get a stable target for the whole term; autonomy is undisturbed on `main`. |
| U-H2 | Self-paced learner mid-journey has modules regenerated/retired under them; `main`="current" serves the drive-by visitor, harms the in-progress studier. (HIGH) | **ACCEPT** | Mitigated by the expectation banner (U-L10) + usable stable anchor (U-H4): learners are told up front to **pin a monthly tag** if they need a stable copy, and the monthly tags are made genuinely usable. Churn on `main` is the autonomy goal (D1) and stays — but the learner is no longer *surprised* by it and has a one-step stable option. |
| U-H3 | Retire `git rm`s a module but surviving sibling modules still cross-reference it ("see Module 6") → guaranteed dangling links in content that *passed* the gate. S7 only reconciles README, not cross-refs. (HIGH) | **ACCEPT** | **Dangling-reference scan extends the S7 retire gate.** Before a retire finalizes, scan all surviving content for links/refs to the retired node; either auto-rewrite/remove them or **enqueue regen of the referencing artifacts**, and **block retire finalization** while unresolved dangling refs remain. Referential integrity is now a retire precondition. |
| U-H4 | "Recoverable via tag/tarball" is technically true but unusable for a non-expert; a mid-quarter retire lands in *last* month's tag, ARCHIVE_INDEX lives on the org profile, learner must diff tarballs. (HIGH) | **ACCEPT** | **Tombstones.** A retired module's path keeps a small `RETIRED.md`: "retired on DATE; covered X; preserved in **[Release vYYYY.MM](direct link)**." A learner following an old link hits a signpost, not a 404. Each repo also gets its own `CHANGELOG.md` (not just the org index). Recovery is now a click from where the learner already is. |
| U-M5 | Learner can't distinguish fresh-passed content from an S9 reverted "under revision" stub or a soon-to-retire module — all render as plain Markdown; the static AI disclaimer doesn't convey per-page state. (MEDIUM) | **ACCEPT** | **Per-artifact status banner** rendered from the plan-node status + `last_scan`: `✅ current — last verified DATE` / `⚠️ under revision` / `⏳ scheduled for retirement`. Surfaces the trust state inline where the learner reads it. |
| U-M6 | Fair-share budget can ship an exercise while its solution is starved or regenerate an exercise without its solution in lockstep → learner finds no/stub/mismatched solution after investing effort. (MEDIUM) | **ACCEPT** | **Exercise↔solution pairing integrity invariant.** An exercise and its solution are a **coupled unit**: regen of one enqueues the other and they merge together; the solution records the exercise `content_hash`, and a mismatch flags + reprioritizes. A live exercise cannot sit without a matching solution beyond a bounded window. |
| U-M7 | For non-retire changes, README-refresh is a *later* queue item, so `main` transiently shows a README that disagrees with the filesystem (7 modules listed, 8 present). (MEDIUM) | **ACCEPT** | **README refresh folds into the same commit as any content change**, not a later queue item — it's deterministic and off the LLM budget (S6), so there's no reason to defer it. Removes the transient inconsistency window for ordinary authoring (retire was already same-commit, S7). |
| U-M8 | Market-chasing retire (quarterly, signal-driven) deletes a topic that's still being actively taught this cohort — optimizes for the drive-by visitor, degrades the paying committed user. (MEDIUM) | **ACCEPT** | **Protected set.** The retire engine skips any node in the **active cohort's taught set** (derived from the `cohort-N` ref, U-H1) and defers its retirement until the term ends. Encodes the committed-user intent the freeze implies. |
| U-L9 | All transparency (Status/quarantine/changelog) is operator-facing; the learner/instructor whose experience breaks gets no signal. (LOW) | **ACCEPT** | Covered by the transparency layer: per-repo `CHANGELOG.md` (U-H4), inline status banners (U-M5), and tombstones (U-H4) put the signal **in the learning repo itself**, where the consumer is — not only in operator issues. |
| U-L10 | No per-repo expectation-setting; a learner cloning a public repo expects stability. Cheapest mitigation for nearly everything above, and absent. (LOW) | **ACCEPT** | **Top-of-README contract** (extends the existing site-banner): "Autonomously generated and continuously updated; modules may be revised or retired as the job market shifts. Pin a monthly tag for a stable copy. Last verified: DATE." Sets the expectation up front. |

**Net effect:** three small layers, all UX-level. **Committed-user protection** (U-H1 cohort freeze + U-M8 protected set) makes the paid cohort and active learners safe from churn without touching `main`'s autonomy. **Referential integrity** (U-H3 dangling-ref scan + U-M6 pairing + U-M7 same-commit README) stops autonomy from producing internally-broken repos. **Transparency** (U-H4 tombstones + per-repo changelog, U-M5 status banners, U-L10 expectation contract) turns "technically recoverable" into "the consumer can actually see what happened and get the version they want." None expands the architecture; they're defaults the loops already have the data to honor.

## 11. Phase 3 — Arbiter Disposition & P0 Reconciliation

The Integrator/Arbiter reviewed all three rounds: safety case **sound**, but the doc was **not internally coherent** after 30 amendments → disposition **REVISE** with five doc-only must-fix items (no redesign; no locked decision reopened). All five are now applied:

1. **README off the LLM queue** — §4.1, §4.2, §4.3, §4.6 updated: README refresh is deterministic, off-budget, same-commit; removed from queue types and the priority ladder. *(Resolves C4.)*
2. **D4 freshness re-worded** — §3 (D4) and §4.4/§4.6 now state the 90-day rotation is a **SOFT target** that yields to the HARD token budget (D5) under backpressure, with protected-set deferral (U-M8) named as a sanctioned, surfaced relaxation. *(Resolves C3 + C1.)*
3. **Blocked-retire precedence** — §4.4 now specifies a retire blocked by an unresolved dangling-ref or failed cross-ref regen **defers to the next cycle without holding the lock or spin-waiting**; retirement is deferred, never cancelled. *(Resolves C5.)*
4. **Operator cadence re-budgeted** — Assumption #3/C-M1's operator role gains two named recurring manual tasks: **maintain/advance the `cohort-N` ref**, and **derive the protected "taught set"** each term (U-H1/U-M8). The one-operator envelope names them rather than implying them. (Compute additions from Round 3 — dangling-ref scan, tombstones, status banners — are deterministic, off-budget, bounded; **no new credential or paid API** was introduced, so the one-token envelope holds.)
5. **P1 throughput unit corrected** — the C-B3-mandated P1 `consumption ≥ production` measurement is scoped to the real work-unit: the **exercise+solution coupled pair** (U-M6), not a lone artifact.

**Contradictions reconciled (Arbiter §2):** C1 (protected-set vs. 90-day) and C3 (D4 text) collapse into soft-freshness; C2 (protected-set vs. retire-cap) is deferral-not-cancellation; C4 (README) and C5 (blocked-retire) fixed above; C6 (heartbeat vs. GitHub-native) is an accepted, costed NFR exception (one free-tier dead-man's-switch). No contradiction reopened D1, the cadences, or the archive model.

### FINAL DISPOSITION: **APPROVED** for phased P0→P6 rollout

All five P0 items landed; exit criteria met (Understanding Lock confirmed, three reviewers invoked, 30 objections resolved, Decision Log complete, design coherent, no locked decision reopened). The design proceeds to implementation **gated by P0 (calibrate eval-gate offline) and P1 (measure real units/day on the exercise+solution pair)** before any autonomous merge; RETIRE (P4) additionally blocked until a named ToS-compliant posting source exists (C-H3).
