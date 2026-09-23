# SOLUTION — project-03-governance-framework

> Read this *after* attempting the capstone deliverables. Like
> `project-01-enterprise-platform` and `project-02-technology-roadmap`,
> this is a principal-architect track project: the solution is a
> rubric plus a worked structural template, not a runnable system.
> If you are looking for runnable platform artifacts, they live in
> the architect and senior-architect tracks; if you are looking for
> the platform strategy the governance system decides *about*, that
> lives in `project-01`.

The paired learner brief for this capstone lives in the sibling
learning repository at
`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/README.md`,
with supporting `requirements.md`, `architecture.md`, `rubric.md`,
`STEP_BY_STEP.md`, and `deliverables/README.md`. The brief frames
the capstone as the **Northwind Insurance Architecture Governance
Framework**: a Fortune-300 P&C / life carrier (32,000 employees,
$26B GWP, 18 BUs, ~1,100 services across AWS + Azure + regulated
on-prem, 4 architecture chapters, 6 existing ARBs, ~340 unresolved
decisions in backlog) whose CEO and CTO have asked the Chief
Architect to design the decision-making system that turns 94-day
median time-to-decision into ≤ 21 days, 38% reversal into ≤ 15%,
and 184 open exceptions into ≤ 40, all under NY DFS 23 NYCRR 500,
PRA SS1/23, and Solvency II governance obligations.

The learner portfolio is ten graded artifacts (D1 governance
framework through D10 launch comms pack) scored against an
eight-dimension rubric ([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/rubric.md)):
decision-system design clarity (25%), ADR & radar craft (15%),
exception process realism (10%), decision telemetry & KPI fitness
(15%), federation model (10%), rollout plan with abandonment
criteria (10%), cultural & political acuity (10%), and comms
quality (5%). Pass ≥ 70% overall with no dimension below 50%;
distinction ≥ 85% with no dimension below 70%.

The five-block strategic package below is the **principal-track
spine** — the decision-system a peer principal architect (or a
simulated ETLT + audit panel) would grade before reading any of
the D1–D10 depth artifacts. Every generic charter row, KPI, and
common mistake in this SOLUTION maps directly to one or more of
D1–D10; §4.4 gives the mapping. The two artifacts are designed
to compose: the sibling brief supplies the concrete Northwind
numbers, deliverable list, and rubric weights the learner submits
against; this SOLUTION supplies the shape and grading altitude
those specifics instantiate. Neither overrides the other — a
learner submission is expected to satisfy both.

## 1. Solution overview

The `project-03-governance-framework` capstone asks the learner to
produce the **decision-making system a principal architect would
defend to the CEO, CTO, ETLT, chapter leads, BU CIOs, and the
audit function** for an org whose architecture is fragmenting
under its own decision debt. It is the governance sibling of the
platform capstone (`project-01`) and the roadmap capstone
(`project-02`): where `project-01` grades the *strategic package*
for a platform and `project-02` grades the *roadmap artifact*,
`project-03` grades the *decision-making system that produces
both* — the ARBs, ADRs, technology radar, exception process,
decision telemetry, RACI/RAPID matrix, federation model, and
rollout plan — as its own object, at higher resolution.

The capstone pulls in material from every module the principal
track presently exercises:

- from `mod-601-org-wide-architecture` — the altitude of
  standards, invariants, and "conditions under which many teams
  can decide well" that a governance framework operationalizes
  (see [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
  §"What this module is really teaching");
- from `mod-604-stakeholder-coalition` — the coalition mechanics
  that make governance survive a chapter-lead objection or a
  BU-CIO bypass (see
  [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md),
  §"What this module is really teaching");
- from `mod-605-tech-debt-modernization` — the sequencing
  discipline and kill-criterion pattern that make the framework's
  own rollout survive contact with the org (see
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md));
- from `mod-603-multi-year-investment` — the FinOps-credibility
  discipline that a governance-ops budget of ≤ $2M year-1 /
  ≤ $1.5M steady-state must survive when the CFO reads it (see
  [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)).

The brief additionally names two governance-specific learning
modules (`mod-606-architecture-governance`,
`mod-607-decision-systems`) as prerequisites. Where a solutions
counterpart for those modules exists in a peer track, prefer that
reference; where it does not yet exist in this repo, the
five-block spine below encodes the material the capstone actually
grades against.

A passing submission is not one artifact. It is a **governance
package** of five short, mutually consistent design blocks —
decision topology, ADR practice, technology radar, exception
process, and telemetry-and-rollout — that together let a peer
principal architect (a) see how a decision routes from intake to
recorded outcome, (b) see the delegation rules that keep the
Enterprise ARB from becoming the bottleneck it just replaced,
(c) see the leading indicators that would trigger intervention
before a lagging KPI proves the framework is broken, and (d)
trace every commitment to a stakeholder ask, a requirement ID,
and a coalition-durability move. Coherence across the package is
the primary grading dimension; depth in any single block is
secondary.

### What the deliverable is *not*

- Not a platform architecture. Component boxes for the platform
  live in `project-01` (see
  [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md));
  governance decides *about* the platform, does not draw it.
- Not a technology roadmap. Multi-year investment bets live in
  `project-02` (see
  [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md));
  governance is the nervous system that produces the roadmap and
  learns from its outcomes.
- Not an M&A playbook. Integration of acquisitions belongs to
  [`../project-04-ma-integration/SOLUTION.md`](../project-04-ma-integration/SOLUTION.md)
  (see the brief's §11 distinction table); this framework
  leaves *hooks* for that work but does not do it.
- Not a Jira project. If the submission substitutes ticket
  templates for a state machine, a decision tree, or a KPI with
  a named intervention rule, the learner has mistaken tooling
  for governance.
- Not runnable software. If the submission contains Terraform,
  Helm, or application code, the learner has mistaken the
  altitude of the exercise. The one exception is the CI hooks
  in D3 and the state-machine and telemetry-pipeline
  *specifications* in D5 and D6 — those are statically-valid
  design artifacts (state diagram, event schema, checked-in
  policy fragments) and are in scope precisely because they
  demonstrate the automation the framework depends on.

### What "governance" means for grading

For this project, "governance" is the load-bearing decision-making
system of an org the size the brief describes (32,000 employees,
18 BUs, 4 chapters, ~1,100 services). The framework is graded
first on whether it would produce faster, better, more traceable,
more learned-from decisions at that scale — not on how thorough
the ARB charters read in isolation. A framework that would
optimize a 200-engineer org (single ARB, single ADR repo, one
weekly meeting) is under-designed for Northwind; a framework
that would optimize a 200,000-engineer org (five tiers, regional
ARBs, standing arbitration council) is over-designed. Submissions
that make an explicit note of what would change at the
5,000-engineer, 32,000-engineer (target), and 100,000-engineer
scales grade above ones that assume a universal answer.

## 2. Worked answer or implementation

The package below is the shape a strong submission takes. Titles
and section counts should match; wording is the learner's. Each
block anchors to the paired brief's D1–D10 artifact list (§4.4
maps them cell-by-cell).

### 2.1 The decision topology (~2 pages + one diagram)

One page of prose plus one flowchart. The flowchart must be a
routing decision (an intake queue plus routing rules that decide
which tier owns which decision), not an org chart of committees.
The prose must define:

- **The intake**: a single form or bot capturing decision type,
  stakes (financial / risk / reversibility), proposed tier,
  requestor, and target date. Every decision enters *one* queue;
  side-channels ("just Slack the ARB chair") are named as an
  anti-pattern in the framework.
- **The tiers** (target: 3–4, with a fast-track lane). A common
  shape:

  | Tier | Body                       | Owns                                                        | Quorum                  | Cadence                             | SLA (median TTD)             |
  |------|----------------------------|-------------------------------------------------------------|-------------------------|-------------------------------------|-------------------------------|
  | 1    | Enterprise ARB             | Cross-BU / cross-chapter; one-way doors; standards-level    | Rule of the room stated | Biweekly sync + continuous async    | ≤ 21 days                     |
  | 2    | BU ARB                     | Within-BU standards, BU-scoped vendor / exception decisions | Rule of the room stated | Weekly sync + async                 | ≤ 14 days                     |
  | 3    | Chapter ARB                | Within-chapter (Solution / Data / Security / Integration)   | Rule of the room stated | Monthly sync + async                | ≤ 5 days (in-chapter)         |
  | 4    | Fast-track named delegate  | Time-sensitive low-stakes, in-scope                         | Single delegate + veto  | n/a                                 | ≤ 3 days (with 48h ARB veto)  |

- **The delegation patterns**. This is the load-bearing
  innovation and the single most-graded item in dimension 1.
  Three patterns:
  1. **Standing delegation by scope** — decisions wholly inside
     Chapter X do not visit the Enterprise ARB.
  2. **Standing delegation by precedent** — once the ARB has
     decided a class ("Postgres deployments default to Aurora
     unless a tier-3 exception applies"), it becomes a standard;
     future instances do not return to the ARB.
  3. **Time-bounded delegation by SLA** — emergency decisions
     go to a named delegate with a short ARB veto window.
- **The routing rules**. Publish as a decision tree or a table,
  not prose. A prose routing rule loses argument-by-attrition to
  the strongest advocate in the room; the point of the framework
  is that routing does not require an argument.
- **The failure-mode of centralization**. State explicitly what
  the framework will *not* pull up to the Enterprise ARB and why
  — this is what turns a governance rewrite from a bottleneck
  refactor into an actual delegation move.

### 2.2 The ADR practice (~2 pages + one template + one lifecycle diagram + three worked examples)

Two disciplines braided together: **the artifact** (an ADR
template that captures what a decision was and why) and **the
mechanism** (the lifecycle and automation hooks that keep ADRs
from becoming a graveyard of well-formatted decisions no one
reads).

**Template shape** (MADR-derived; see references §6 for the
canonical MADR and Nygard sources): status, date, owner, tier,
ARB, supersedes/superseded-by, context, decision (imperative),
consequences (positive/negative/neutral), alternatives considered
(with rejection reasons), reversibility (Low/Medium/High/One-way
door + exit plan when not Low), dissent (captured names +
positions, empty acceptable), links (requirement IDs, related
ADRs, PRs). Any field absent means the ADR cannot pass CI.

**Lifecycle** as a state machine (target shape:
Proposed → InReview → Accepted / Rejected / Deferred →
Superseded / Deprecated / [closed]). Every transition has an
explicit criterion; Accepted requires *recorded* decision +
dissent capture (empty allowed, absent-of-capture not) +
telemetry emission.

**Automation hooks** — this is where a passable submission
becomes a distinction one. At minimum:

1. **Scaffolder**: `npx adr new` (or the org's Backstage
   Template) produces a numbered, properly-formatted draft in
   the right repo with required fields. Prevents the "blank ADR
   as barrier to entry" failure.
2. **Code-review surfacing**: when a PR modifies files under a
   component covered by an ADR (tracked in a checked-in
   coverage manifest such as `.adr-coverage.yaml`), the PR
   description auto-includes the ADR link and the reviewer must
   acknowledge it (checkbox) before approval — enforced as a
   CODEOWNERS-style requirement.
3. **Architecturally significant change detection**: heuristic
   CI rules (new top-level service, new datastore, new external
   dependency in `package.json` / `go.mod` / `pom.xml`, new
   public API) label the PR "ADR-required"; merge is blocked
   until an ADR is linked or a chapter lead comments
   "no ADR justified" (with cause). The heuristic is deliberately
   noisy on the false-positive side; the "no ADR justified"
   exit is designed to be low-friction.
4. **Search + graph**: full-text + tag + status search
   org-wide, plus a cross-link graph (`consumes` / `extends` /
   `contradicts` / `supersedes`) queryable from the software
   catalog.

**Worked examples** (the brief asks for three): pick decisions
non-trivial enough that the "alternatives considered" section
does the work — good candidates from the Northwind scenario are
"default relational store for new services" (Aurora vs.
self-managed Postgres vs. RDS-Postgres), "internal developer
platform" (Backstage self-host vs. Roadie vs. custom), and
"async event backbone" (Confluent Cloud vs. AWS MSK vs.
in-house Kafka). Each worked ADR names the dissent that would
have been captured in reality (not a scrubbed one), because
dissent-with-name is the highest-signal artifact the ADR
produces.

### 2.3 The technology radar (~1 page process spec + a radar with 40–60 entries)

ThoughtWorks-style: 4 rings (Adopt / Trial / Assess / Hold) ×
4 quadrants (Languages & Frameworks / Tools / Platforms /
Techniques). Rings mean what they mean in the ThoughtWorks
convention (see references §6): *Adopt* is the default for new
work, *Trial* is a committed non-trivial evaluation, *Assess* is
a small learning bet, *Hold* is "do not start new, phase out
where present."

The graded object is not the entries themselves; it is the
**governance around movement**. Each entry requires:

- A named sponsor (an architect or chapter lead; not a team).
- Evidence: ≥ 1 production use case in the org OR ≥ 3 peer-firm
  references with public detail (not conference-marketing).
- Justification (≥ 3 sentences anchored in a specific need at
  the org).
- Risk assessment: dependencies and exit cost, stated.
- Where a public radar already positions the entry (ThoughtWorks
  volumes 28+, AWS Well-Architected, CNCF Landscape,
  MLCommons — see references §6), cite it. Where the org
  disagrees, say so; disagreement with a public radar is a
  signal, not an embarrassment.

Movement rules (published, not negotiated):

- **Assess → Trial** requires evidence-of-fit + sponsor
  commitment + radar-editor approval.
- **Trial → Adopt** requires ≥ 2 production deployments with
  ≥ 6 months uptime + endorsement from the relevant chapter
  lead.
- **Adopt → Hold** requires evidence of obsolescence + a
  replacement entry already at Adopt + a 12-month phase-out
  plan (with an owner).
- **Hold → retired** is automatic after 18 months in Hold with
  no reversal.

Cadence: quarterly publication with rolling proposal intake;
editor may promote between publications when evidence is
overwhelming, with backfill at the next publication. Named
editor role (target: 0.5–1.0 FTE; the choice is one of the
brief's "make a call" open questions and must be *made*).

**Adoption instrumentation**: a radar with no citation
mechanism is decoration. The framework mandates radar-entry
citation in new-project design docs (target ≥ 60%, per the
brief's TR-9). This shows up in D6 telemetry.

### 2.4 The exception process (~1 page spec + a state machine + a tooling defence)

The load-bearing exception discipline is not the state machine —
it is **auto-expiry as the default**. Northwind's starting state
is 184 open exceptions, 76% still active from prior years; the
framework's job is to bring that to ≤ 40 active with a median
lifespan ≤ 60 days without an exception amnesty.

**State machine** (published as a Mermaid or equivalent
diagram): Requested → InReview → Approved → Active →
NearExpiry (T-14 alert) → RenewalRequested → InReview [loop]
OR → Closing → Closed; Rejected and Closed terminal. Every
transition has an SLA and an owner.

**Field requirements** (every exception): requestor (named
role), approver (per routing tier), the standard or ADR being
deviated from (linked), scope (components / projects / time),
justification (≥ 1 paragraph), compensating control if
applicable (e.g., "two-senior-reviewer PR gate as compensating
control for waived automated scan"), expiry (max 90 days,
default 60), and a documented "what happens at expiry" (revert
/ escalate / re-review).

**Anti-overflow mechanisms** (this is the rubric's dimension 3
core):

- **Auto-expiry is default** — no exception persists silently.
  T-14 alert forces the requestor to *decide* to renew, not
  drift into permanence.
- **Re-approval rate KPI** (paired-brief TR-7): if > 20% of
  expiring exceptions are renewed, the standard is wrong. The
  KPI is instrumented to trigger an ADR review, not just be
  reported.
- **3-renewal rule** (paired-brief GR-22): an exception renewed
  three times triggers a standard review; either the standard
  changes or the renewal pattern is broken by the ARB. Encoded
  as a hard trigger in the process, not a suggestion.
- **Quarterly triage** by governance ops: all active exceptions
  reviewed; recommended closures produced.

**Tooling choice** — defended, not deferred. Options are
ServiceNow (audit-first, already in org), Backstage extension
(dev-first, integrates with ADR tooling), or Jira project
(lowest-friction). The brief lists this as an open question and
demands a call; the SOLUTION grade drops one full band for a
non-decision. A defensible defence lists the two rejected
options with named reasons, not strawmen.

**Audit export format** — CSV / JSON / PDF per exception with
decision record, approver identity, time bounds, compensating
control evidence, closure cause. For NY DFS 23 NYCRR 500 §500.09
(risk assessment record-keeping) and PRA SS1/23 model-risk
audit trail, this is the "documented risk acceptances" evidence.

### 2.5 The telemetry, rollout, and coalition block (~2 pages + 4 dashboard mocks + a 12-month plan)

This is the "does the framework work, and will it survive
launch?" block. Three sub-artifacts:

**Telemetry** — 8–12 KPIs, each with a target, a measurement,
an owner, a publication cadence, and a **leading / lagging
tag**. Leading indicators drive intervention; lagging ones prove
outcomes over time. The brief's TR-1 through TR-12 are the
target set; a strong submission adds intervention rules for
each leading indicator:

- Median TTD by tier (TR-1) — lagging; target ≤ 21 / 14 / 5
  days; weekly.
- Reversal rate (TR-2) — lagging; target ≤ 15%; monthly.
- ARB throughput (TR-3) — lagging (but early warning if
  collapsing); monthly.
- ARB queue depth (TR-4) — **leading**; target ≤ 20 at
  enterprise tier; weekly. Intervention: > 25 for two weeks
  triggers a triage session; > 30 triggers a temporary
  fast-track expansion.
- Active exception count (TR-5) — **leading**; target ≤ 40;
  weekly.
- Median exception lifespan (TR-6) — lagging; ≤ 60 days;
  monthly.
- Exception re-approval rate (TR-7) — **leading**; ≤ 20%;
  quarterly. Intervention: > 20% on a standard triggers ADR
  review of that standard within one ARB cycle.
- Radar entries by ring + delta (TR-8) — descriptive; quarterly.
- Radar adoption rate (TR-9) — **leading**; target ≥ 60%;
  quarterly.
- Dissent frequency by topic (TR-10) — **leading**; aggregated
  above individual; quarterly. Intervention: repeated dissent
  on a topic from the same source triggers a topic-level review.
- Decision-to-implementation latency (TR-11) — lagging;
  monthly.
- ARB participant NPS (TR-12) — cultural leading indicator;
  quarterly.

Each KPI names its instrumentation source (Backstage event
stream, exception registry, radar CMS, ARB minutes parser) and
its owner (governance ops for the plumbing, Chief Architect for
the framing).

**Four dashboard mocks** (the brief hard-checks this): ARB
performance (audience: ETLT, weekly), exception health (audience:
ARB chairs + Audit, weekly), radar adoption (audience: chapter
leads + radar editor, monthly), cultural health (audience: Chief
Architect, quarterly). Each mock is captioned with the audience
and the decision the mock is meant to inform.

**12-month rollout** — four phases with per-phase success /
refine / pivot / abandonment criteria. A shape that grades well:

| Phase | Months | Content                                                                       | Success                          | Refine                        | Pivot                                | Abandon                                    |
|-------|--------|-------------------------------------------------------------------------------|----------------------------------|-------------------------------|--------------------------------------|--------------------------------------------|
| 0     | 1–2    | Coalition (chapter leads co-design; audit walkthrough), tooling, first ADRs   | 4/4 chapter lead endorsements    | 3/4                           | 2/4                                  | ≤ 1/4 or CTO / CISO churn                  |
| 1     | 3–5    | Pilot in 2 BUs (one supportive, one bypass-history)                           | Both pilots hit tier-2 SLA       | One pilot slipping            | Both pilots slipping                 | Public revocation of participation         |
| 2     | 6–9    | Expansion to 6 more BUs; enterprise-ARB steady operation                     | TTD trending ≤ 30 days at tier-1 | Trending 30–45 days           | Trending > 45 days two months        | Reversal rate rising, not falling         |
| 3     | 10–12  | Steady state (all 18 BUs, all 4 chapters, telemetry public)                  | TTD ≤ 21 tier-1 at Q4 close      | Missed by ≤ 20%               | Missed by ≤ 40%                      | Any dimension of §9 success unachieved     |

Each phase names ≥ 1 **cultural-risk moment** (the brief's
distinction bar): e.g., the first time the Enterprise ARB
overrides a chapter lead in public, the first bypassing BU CIO's
project blocked by the framework, the first audit walkthrough
finding. Each cultural moment has a **response plan**, not a
hope.

**Coalition moments** — mapped per stakeholder group, not left
generic:

- Chapter leads: co-design sign-off in Phase 0; standing seat on
  Enterprise ARB; a public "chapter-lead position" on any
  cross-chapter ADR they dissented on.
- Bypassing BU CIOs: fast-track tier as their explicit value
  prop; pilot in their BU with their lead architect as
  co-designer; dashboarded TTD as the promise-kept receipt.
- Audit: quarterly governance health review (health *review*,
  not audit *of*); export endpoints in D5's spec; pre-rollout
  walkthrough as a hard gate, not optional; endorsement in the
  launch comms.
- ETLT (CTO + CISO co-sponsors): monthly readout; framework
  amendment authority reserved to ETLT; the CTO / CISO churn
  clause of the rollout's Abandon column names them by role.
- BU CIOs at large: quarterly reporting protocol per §2.4 of the
  brief's `architecture.md`; the framework does not centralize
  decisions inside their existing rights without their explicit
  consent (paired-brief CR-2).

**Meta-governance** — the amend-the-framework process. This is
the distinction bar. Named triggers (a fitness-function failure
per §3.6 below, a stakeholder-rotation event per ASM-1, an
audit finding), a named amendment ARB (default: Enterprise
ARB + ETLT), a stage gate at month 12 to formally re-charter
or absorb amendments.

## 3. Validation steps

There is no build to run at this altitude. Validation is a
sequence of reviews the package must survive, adapted from the
sequences in
[`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
§3 and
[`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
§3, specialized to the governance altitude.

1. **Requirement-traceability check.** Every requirement ID in
   the paired brief's `requirements.md` (GR-*, PR-*, TR-*, CR-*,
   CON-*, ASM-*) traces to at least one section of the package
   above. Requirements with no home are gaps; sections with no
   requirement are decoration.
2. **Internal consistency check.** Re-read the five blocks in
   order. Every commitment in the topology (§2.1) — a tier, an
   SLA, a delegation pattern — appears in the ARB charters
   (D2), the RACI (D7), and the KPIs (§2.5 / D6). Every ADR
   lifecycle transition (§2.2) has a telemetry event. Every
   exception state (§2.4) has a KPI or a compensating control.
   Cells that fail any of these links are decorative — cut them
   or add the links.
3. **Delegation audit.** For each of the top 20 decision types
   in D7, is the assignment to the *lowest competent tier*, or
   has centralization crept in? A framework that routes 15 of
   20 to Enterprise ARB has redesigned the bottleneck; force at
   least half to chapter or fast-track and defend the split.
4. **Leading-vs-lagging audit.** Count the KPIs tagged
   **leading**. A framework whose intervention rules all fire
   on lagging indicators is a framework that only learns after
   the outcome is unrecoverable. Target: ≥ 4 leading indicators
   with named intervention rules.
5. **Peer-principal cold read.** Give the D1 framework document
   and the D10 launch deck to a peer principal architect with
   no context. The
   [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md)
   test — the reader should be able to disagree with the design
   and still articulate the reasoning — applies here too. If
   they say "I cannot tell where a decision would go under this
   framework," rewrite the routing rule as a decision tree
   before submitting.
6. **Hostile-BU-CIO read.** Read D10 as the BU CIO whose pet
   project was blocked by the framework last week. Every FAQ
   entry (≥ 25 per rubric dimension 8) should include at least
   one hostile question you would prefer not to answer; if the
   answer is "trust the process," the framework has not
   internalized that the bypassing CIO's information cost is
   the price of adoption.
7. **Chapter-lead-quorum read.** Read D2's charters as each of
   the four chapter leads. Can each of them predict which
   decisions they can make unilaterally, which need
   consultation, and which require ARB, from the charter text
   alone? If any of them cannot, the charter is prose about
   authority, not a delegation rule.
8. **Audit walkthrough dry run.** Read D5 (exception process),
   D6 (telemetry), and D2 (ARB charters) as if you were an
   internal auditor with NY DFS 23 NYCRR 500 §500.09 and PRA
   SS1/23 in hand. Every "documented risk acceptance" surfaces
   in an audit export? Every model-relevant decision (Solvency
   II) surfaces in an ADR whose retention is ≥ 7 years per
   paired-brief CON-4? Gaps here are audit findings by month
   12.
9. **Rollout-abandonment plausibility.** Read the rollout plan's
   Abandon column. Would you actually invoke it under the named
   trigger, or would you argue for one more quarter? A rollout
   whose abandon triggers no one would ever pull is a rollout
   with no kill criteria — see
   [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md),
   §"No exit criteria".
10. **Anti-bureaucracy stress test.** For each of the four
    dashboards in §2.5, name the decision the dashboard would
    change *this week*. If the dashboard's answer is "we would
    look at the trend," the KPI is a report, not
    instrumentation. Instrumentation implies an action; if none
    is named, the KPI does not belong in the top 12.
11. **Fitness-function replay.** Assume the framework has been
    running for four quarters and each fitness function in
    §2.5's telemetry has failed exactly once. Does the
    meta-governance process (§2.5's amendment block) let the
    framework revise, and does the revision leave the org
    better off than the pre-framework baseline? A framework
    whose own amendment process is undesigned is a framework
    that cannot learn.
12. **Standards-legibility pass.** For every position that
    touches an area covered by an external standard the org
    already engages with (ThoughtWorks Tech Radar for radar
    conventions, MADR / Nygard for ADR format, NIST AI RMF for
    any model-governance rows, NY DFS 23 NYCRR 500, PRA SS1/23,
    Solvency II), confirm the position is stated in terms that
    standard would recognize. This costs little now and avoids
    audit-cycle retrofits later.

## 4. Rubric or review checklist

The checklist below is the principal-track spine and is
consistent with the learning brief's eight-dimension, 100-point
rubric ([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/rubric.md)) —
decision-system design clarity (25%), ADR & radar craft (15%),
exception process realism (10%), decision telemetry & KPI
fitness (15%), federation model (10%), rollout plan with
abandonment criteria (10%), cultural & political acuity (10%),
comms quality (5%). §4.4 shows how each checklist item and each
strategic-package block maps onto the D1–D10 artifact set the
brief actually grades. The checklist here is the live grading
rubric used to score submissions.

A pass on this capstone requires all of the following. Missing
even one item is grounds for revision, not partial credit — the
governance framework is graded as a package.

- [ ] All five strategic-package blocks present (D1 references
      each in its outline), at roughly the target lengths;
      longer is not better and usually means a routing rule was
      described in prose instead of drawn.
- [ ] §2.1 defines ≥ 3 ARB tiers with an explicit fourth
      fast-track lane, and ≥ 3 delegation patterns (by scope,
      by precedent, by SLA) each with named authority and
      recall condition.
- [ ] Routing rules for the top 20 decision types are a decision
      tree or a table, not prose (rubric dimension 1 hard
      check).
- [ ] The RACI / RAPID register (D7) covers ≥ 30 inventoried
      decision types with full assignment for the top 20 and
      maps each to a tier.
- [ ] §2.2's ADR template contains every required field and its
      lifecycle is a state machine with per-transition criteria;
      ≥ 2 automation hooks (scaffolder + CI surfacing at
      minimum) are specced to ticket level, not narrated.
- [ ] Three worked ADR examples exist on non-trivial topics,
      each with a real (not scrubbed) dissent capture.
- [ ] §2.3's radar has 40–60 entries across 4 rings × 4
      quadrants; each entry has sponsor, evidence, justification
      (≥ 3 sentences), and a radar-editor date; ring-transition
      criteria are documented per movement direction.
- [ ] §2.4's exception process is a full state machine
      (Requested → Closed with all transitions), defaults to
      auto-expire, has a T-14 alert, encodes the 3-renewal
      rule, and defends its tooling choice (ServiceNow /
      Backstage / Jira) with two rejected alternatives.
- [ ] §2.5's telemetry lists 8–12 KPIs, each tagged **leading**
      or **lagging**, with target / measurement / owner /
      cadence; ≥ 3 leading indicators each carry a named
      intervention rule; ≥ 4 dashboard mocks exist with audience
      and the decision each mock informs.
- [ ] §2.5's federation model (D8) has a reusable BU ARB charter
      template, cross-BU routing as a decision tree, a quarterly
      reporting protocol, and a 5-business-day disagreement
      escalation SLA.
- [ ] §2.5's rollout (D9) is 4 phases over 12 months, with
      per-phase success / refine / pivot / abandonment criteria,
      ≥ 3 named cultural-risk moments each with a response plan,
      and at least one phase carrying a "pause" trigger.
- [ ] The launch comms pack (D10) is ≤ 25 slides with an
      explicit "what would make us stop" slide, 5
      audience-specific 1-pagers (engineer, BU architect,
      BU CIO, chapter lead, audit), a ≥ 25-entry FAQ that
      includes hostile questions, and a CTO+CISO co-signed
      launch email template.
- [ ] Every requirement ID (GR-*, PR-*, TR-*, CR-*, CON-*) in
      the paired brief's `requirements.md` traces to a section
      of D1 or to a named deliverable D2–D10.
- [ ] Every fitness function (§2.5, §3.11) has an owner and a
      failure-triggered path into meta-governance.
- [ ] The package would be legible to a peer principal architect
      reading it cold, per the test in
      [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).
- [ ] The package contains at least one explicit "what would
      make this framework wrong" statement and at least one
      explicit "what we are deliberately not governing here and
      why" statement.

A distinction-level submission additionally does all of the
following (per the paired-brief §rubric distinction bar):

- [ ] A **chapter lead's specific objection** is anticipated
      and addressed in the framework, with the chapter lead's
      quoted concern in the design rationale.
- [ ] A **KPI with an intervention rule you would actually
      invoke** at the named threshold, and a peer reviewer
      agrees you would (not that you should).
- [ ] A **published exception** to your own framework — at
      least one place where the framework says "this part will
      not work for case Y; here is the override" and names the
      override owner.
- [ ] A **meta-governance design** — the documented process by
      which the framework itself is amended, with a stage gate
      at year 1.
- [ ] Notes on what would change at the 5,000-engineer,
      32,000-engineer (target), and 100,000-engineer scales,
      showing the author knows the assumed org size is a choice
      (per §1 above).
- [ ] Explicitly cites at least one external standard (an ADR
      convention such as MADR or Nygard, a public tech-radar
      shape, NY DFS 23 NYCRR 500, PRA SS1/23, or NIST AI RMF)
      as the anchor for a specific position rather than
      inventing terminology internally.

### 4.4 Mapping to the learning-repo deliverable set

The five-block strategic package above is the principal-track
spine; the learner-facing brief expects a wider ten-artifact
portfolio (D1–D10). Each strategic-package block maps to one or
more graded artifacts and to specific rubric dimensions:

| Strategic-package block (this SOLUTION) | Learning-repo artifacts | Rubric dimensions primarily exercised |
|---|---|---|
| 2.1 Decision topology (tiers, delegation, routing) | D1 framework, D2 ARB charters, D7 RACI (top 20) | Decision-system design clarity (25%), Cultural & political acuity (10%) |
| 2.2 ADR practice (template + lifecycle + automation) | D3 ADR handbook (template, automation spec, 3 examples) | ADR & radar craft (15%) |
| 2.3 Technology radar (structure, movement, adoption) | D4 radar (40–60 entries + process) | ADR & radar craft (15%) |
| 2.4 Exception process (state machine, anti-overflow, audit) | D5 exception process (spec, state machine, tooling, audit export) | Exception process realism (10%) |
| 2.5 Telemetry / rollout / coalition block | D6 telemetry (KPIs + dashboards + interventions), D8 federation, D9 rollout, D10 launch comms | Decision telemetry & KPI fitness (15%), Federation model (10%), Rollout plan (10%), Comms quality (5%) |

The eight key questions the learning brief asks (ARB tiering,
ADR practice, tech radar, exception process, decision telemetry,
cross-chapter coordination, federation, decision learning — see
[`README.md §4`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/README.md))
are stress-tests against §2.1's delegation table, §2.4's
anti-overflow mechanisms, and §2.5's telemetry-driven meta-
governance. A submission that answers all eight without touching
every row of §2.1's tier table or every entry in §2.5's KPI list
has misjudged the altitude and needs to push back up.

## 5. Common mistakes

Patterns graders reliably see on this capstone. Most are
variants of failure modes named in the module-level
`SOLUTION.md` files or in the paired brief's "Common failure
modes" section; they show up here because the capstone is where
all five modules converge on a single decision-making system.

1. **The centralizing ARB in a delegation costume.** The
   framework has three tiers on paper but the RACI (D7) routes
   17 of 20 decision types to Enterprise ARB. The learner has
   redesigned the bottleneck. Fix by mapping the top 20 to the
   *lowest competent tier* and defending each escalation
   individually. See paired-brief rubric dimension 1's
   "centralizing ARB" failure mode.
2. **ADR craft without automation.** Template, lifecycle, and
   three worked examples are perfect. The automation spec is a
   paragraph that says "we will use Backstage Templates." No
   ticket-level plan; no CI surfacing; no significant-change
   detection heuristic. Rubric hard-check missed.
3. **Radar-as-decoration.** 40 entries chosen well, movement
   criteria written well, but no adoption mechanism and no TR-9
   citation KPI plumbed into D6. Within one year the radar is a
   stale wiki page. The rubric's adoption mechanism (target
   ≥ 60% citation) is graded on plumbing, not on aspiration.
4. **Exception process without auto-expire.** The state machine
   is beautiful; Closed is only reachable via explicit-close.
   Northwind's 184-active starting state proves humans do not
   remember to close exceptions. Rubric dimension 3 caps at
   half without auto-expire.
5. **Lagging-only KPIs.** All 12 KPIs measure outcomes: TTD,
   reversal rate, lifespan. All are lagging. The framework has
   no way to intervene before an outcome is knowable. Rubric
   dimension 4 caps at half.
6. **KPI with no intervention rule.** Each KPI has a target and
   a dashboard; none has a named rule of what changes if the
   KPI breaches the target. A KPI without an intervention is a
   report, not instrumentation. See validation step §3.10.
7. **Federation-as-prose.** Cross-BU routing is three
   paragraphs of "when two BUs disagree, the ARB chairs meet
   and try to resolve." Rubric hard-check requires a decision
   tree. Prose loses to the strongest advocate; a tree does not.
8. **Rollout without cultural moments.** The 12-month plan is
   four phases, each with success criteria, no named
   cultural-risk moments and no response plans. When the first
   chapter lead publicly dissents from an Enterprise ARB
   decision, the plan has nothing to say. See paired-brief
   §rubric dimension 6.
9. **Missing meta-governance.** The framework designs the
   decision-making system but no design exists for how the
   framework itself is amended. First failed fitness function
   in month 8 finds no path back to a corrected framework;
   improvisation follows, and the coalition erodes.
10. **Silent contradictions between D1, D7, and D9.** D1 says
    "aggressive delegation"; D7's RACI centralizes; D9's rollout
    plans Phase 2 as the moment aggressive delegation begins
    but its success criterion is Enterprise ARB throughput. Any
    one of these might be true; not all three. Validation step
    §3.2 exists to catch this; most authors skip it and pay
    for the skip in review.
11. **Bypassing BU CIO addressed as a compliance problem.**
    The framework treats the bypassing BU CIO as an
    enforcement question. That CIO's bypass is *information* —
    the incumbent ARB was slow, and the BU CIO was rationally
    routing around it. A framework that answers with
    enforcement rather than with a fast-track lane and a
    dashboarded TTD promise has not read the coalition. See
    [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md).
12. **Audit as an afterthought.** D5 has no audit-export
    format; D6 has no audit-visible dashboard; D9 has no
    pre-rollout audit walkthrough. Cycle 1 audit produces
    findings; the framework is now on the defensive at the
    moment its coalition most needs a clean receipt.
    Paired-brief acceptance criterion (§2.3) requires *zero*
    process findings in cycle 1.
13. **Presenting inevitability instead of a bet.** If the
    framework reads as "this is obviously the right governance
    system," the author has hidden the trade-off — often from
    themselves. Every graded principal-track deliverable makes
    the bet explicit; this one is no exception. Mirrors
    [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
    §5 item 10 and
    [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
    §5 item 10.
14. **Skipping the "make a call" open questions.** The paired
    brief's `architecture.md` §14 lists seven decisions the
    submission must close (exception tooling, ADR storage,
    telemetry pipeline owner, radar editor FTE, tier-1 quorum,
    fast-track veto window, ARB compensation model). A
    submission that leaves any open forfeits the coalition's
    trust that the framework will decide anything, since it
    could not decide about itself. Close ≥ 6 of 7 with a
    defended position or the framework is unfinished.

## 6. References

### Local curriculum context

- [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
  design philosophy across the principal-architect track; the
  "strategy survives stakeholder rotation" and peer-principal
  cold-read tests are the load-bearing frames for this
  capstone.
- [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
  — the enterprise-platform capstone whose invariants and
  guardrails the governance framework decides *about*; §2.2's
  guardrail-and-escape-hatch pairing motivates §2.4's exception
  design here.
- [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
  — the roadmap capstone whose bets and decision points the
  governance framework produces and learns from; the
  bet-with-kill-criterion shape reappears here as the ADR with
  reversibility note plus the rollout with abandonment
  criteria.
- [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md)
  — the "design the conditions under which many teams decide
  well" framing that a governance system operationalizes; the
  strategy-memo rubric shape reappears as the ADR template.
- [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  — the coalition-mechanics module; §"disagreement is
  information" and §"coalitions decay" motivate this SOLUTION's
  cultural-moments and quarterly-dissent-retrospective design.
- [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  — the "sequence by blast radius" and "kill criteria" patterns
  reused in §2.5's rollout plan.
- [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)
  — the FinOps-credibility discipline that a governance-ops
  budget of ≤ $2M year-1 (paired-brief CON-5) must survive when
  the CFO reads it.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — path parity
  and repo rules the capstone submission is expected to follow.

### Paired learning repository

- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/README.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/README.md)
  — the Northwind Insurance scenario, ten deliverables (D1–D10),
  the eight key questions the portfolio must answer, and the
  60-hour duration breakdown.
- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/requirements.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/requirements.md)
  — the traceable requirement set (GR-*, PR-*, TR-*, CR-*,
  CON-*, ASM-*) every deliverable must map back to; §8
  acceptance criteria per D1–D10.
- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/architecture.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/architecture.md)
  — the governance-system design doc with the routing topology,
  ADR lifecycle state machine, exception state machine,
  telemetry event schema, and the seven "make a call" open
  questions the submission must close.
- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/rubric.md)
  — the eight-dimension, 100-point rubric with per-dimension
  hard checks, the six most common failure modes, and the
  distinction-grade bar (chapter-lead objection addressed, KPI
  with actionable intervention, published exception to the
  framework, meta-governance design).
- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/STEP_BY_STEP.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/STEP_BY_STEP.md)
  — the phase-level schedule the 60-hour plan expands into.
- [`../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/deliverables/README.md`](../../../ai-infra-principal-architect-learning/projects/project-03-governance-framework/deliverables/README.md)
  — the D1–D10 directory layout, per-deliverable checklists,
  and file-naming conventions the submission is expected to
  follow.

### External standards and canonical references

The capstone does not require any particular external framework,
but a distinction-level submission tends to anchor its language
to at least one of these widely used references. The URLs are
canonical entry points; the exact clause a governance element
maps to depends on the regulatory and industry context of the
org the framework is written for.

- **Architecture Decision Records (ADRs) — Nygard's 2011
  original post** —
  <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
  — the low-friction ADR format the community has built on
  since; the template shape in §2.2 above is a superset.
- **MADR (Markdown Any Decision Records)** —
  <https://adr.github.io/madr/> and
  <https://github.com/adr/madr> — the community-maintained
  MADR template and its ADR-community index at
  <https://adr.github.io/> — the recommended anchor for the
  D3 ADR template's required-field set.
- **ThoughtWorks Technology Radar** —
  <https://www.thoughtworks.com/radar> — the canonical
  Adopt / Trial / Assess / Hold shape and the volumes 28+
  archive the D4 radar's ring-transition criteria and quadrant
  conventions can cite directly.
- **CNCF project maturity levels (Sandbox / Incubating /
  Graduated)** —
  <https://www.cncf.io/project-lifecycle-guidelines/> — the
  widely used shorthand for OSS-adoption timing on the D4
  radar's Tools and Platforms quadrants.
- **NIST AI Risk Management Framework (AI RMF 1.0)** —
  <https://www.nist.gov/itl/ai-risk-management-framework> —
  standard vocabulary for AI risk practices when a governance
  decision touches AI-model risk (relevant to Solvency II
  model-driven decisions and to any AI-radar rows in D4).
- **MLCommons benchmarks** — <https://mlcommons.org/benchmarks/>
  — when a radar entry or an ADR makes a performance claim
  about ML infrastructure, stating it in MLCommons terms is
  more defensible than an internal benchmark.

### Regulatory references cited in the learning-repo brief

The paired brief scopes the capstone to Northwind Insurance, a
regulated multi-jurisdiction insurer. Distinction-level
submissions cite these authoritative sources directly rather
than paraphrasing them:

- **NY DFS Cybersecurity Regulation — 23 NYCRR 500** —
  <https://www.dfs.ny.gov/industry_guidance/cybersecurity> —
  the New York State Department of Financial Services
  cybersecurity regulation whose §500.09 (risk assessment)
  requires documented, time-bounded risk decisions — the audit
  hook D5's exception export format satisfies.
- **PRA SS1/23 — Model Risk Management principles for banks**
  — <https://www.bankofengland.co.uk/prudential-regulation/publication/2023/may/model-risk-management-principles-for-banks-ss>
  — the Bank of England / Prudential Regulation Authority
  supervisory statement whose model-governance principles are
  the audit-trail anchor for cited model-relevant decisions in
  D3 ADRs and D6 telemetry.
- **Solvency II Directive (Directive 2009/138/EC)** —
  <https://eur-lex.europa.eu/eli/dir/2009/138/oj> — the EU
  insurance-solvency directive whose governance-system
  requirements for model-driven decisions anchor the ≥ 7-year
  retention constraint in paired-brief CON-4.

Version pins, article references, and internal-policy mappings
should be added by the learner when defending the submission
inside a specific organization; the URLs above are the canonical
entry points, but the exact clause a governance element maps to
depends on the regulatory and industry context.
