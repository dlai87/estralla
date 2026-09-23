# SOLUTION — project-02-technology-roadmap

> Read this *after* attempting the capstone deliverables. Like
> `project-01-enterprise-platform`, this is a principal-architect
> track project: the solution is a rubric plus a worked structural
> template, not a runnable system. If you are looking for reference
> platform artifacts, they live in the architect and senior-architect
> tracks.

The paired learner brief for this capstone lives in the sibling
learning repository at
`../../../ai-infra-principal-architect-learning/projects/project-02-technology-roadmap/README.md`.
The scope, deliverable list, and rubric below are the graded
principal-track spine for this capstone — a strategic package
graded on internal coherence, rejected alternatives, reversibility,
and stakeholder legibility. The two artifacts are designed to
compose: the sibling brief supplies the concrete scenario,
deliverable list, and any numeric dimension weights the learner
submits against; this SOLUTION supplies the shape and grading
altitude those specifics instantiate. Neither overrides the
other — a learner submission is expected to satisfy both.

## 1. Solution overview

The `project-02-technology-roadmap` capstone asks the learner to
produce the **multi-year technology roadmap a principal architect
would defend to an executive audience** for an AI-infrastructure
program. It is the roadmap sibling to `project-01-enterprise-platform`:
where `project-01` grades the *strategic package* (thesis, invariants,
investment, coalition, modernization), `project-02` grades the
*roadmap artifact itself* — the horizons, dependencies, decision
points, sunsets, and budget-cycle alignment — as its own object,
at higher resolution.

The capstone pulls in material from every module in the track:

- from `mod-601-org-wide-architecture` — the horizon structure,
  dependency mapping, and roadmap review discipline (see
  [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
  §"The roadmap");
- from `mod-602-industry-standards` — the standards-adoption
  timing rows that belong on the roadmap;
- from `mod-603-multi-year-investment` — the alignment between
  roadmap cadence and the budgeting cycle, and the
  reserved/on-demand mix per horizon (see
  [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md),
  §"Roadmap");
- from `mod-604-stakeholder-coalition` — the sequence of asks
  that must precede each roadmap milestone;
- from `mod-605-tech-debt-modernization` — the modernization
  wave structure and sunset-side of the roadmap (see
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md),
  §"Roadmap").

A passing submission is not one artifact. It is a **roadmap
package** of five short, mutually consistent documents that
together let a peer principal architect (a) understand the bet,
(b) see the dependencies between the pieces, (c) find the
decision points at which the roadmap admits it might be wrong,
and (d) trace every commitment back to a stakeholder ask and a
funding line. Coherence across the package is the primary
grading dimension; depth in any single document is secondary.

### What the deliverable is *not*

- Not a Gantt chart. A month-by-month bar chart across a
  three-year horizon over-fits to today's plan and rots the
  moment the plan is stress-tested.
- Not a vendor purchase order. Concrete vendor selection is out
  of scope at this altitude for the same reason as in
  `project-01` (see `mod-603` SOLUTION.md and
  [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)).
- Not a system design document. The roadmap references
  architectural invariants but does not draw component boxes;
  those live in the architect track.
- Not a wish list. Any item on the roadmap that lacks a stated
  dependency, an owner, and a decision point is decorative and
  should be cut before submission.

### What "roadmap" means for grading

For this project, a "roadmap" is the artifact that would sit on
the wall of the platform team's ops room for the next 18–36
months and be re-reviewed quarterly. The grading assumption is
an org roughly the size of the one `project-01` assumes — 5–10
platform teams, 50–100 product teams, an annual budget with
quarterly true-ups, and at least one regulatory or
industry-standards constraint that anchors the roadmap to the
outside world. Submissions that make an explicit note of what
would change at the 100-engineer or 10,000-engineer scale — and
what would change under a different budgeting cadence (startup
runway model, government fiscal year, multi-year capex block) —
grade above ones that assume a universal answer.

## 2. Worked answer or implementation

The package below is the shape a strong submission takes. Titles
and section counts should match; wording is the learner's.

### 2.1 The roadmap map (one page, one landscape diagram)

One page. Three to five horizons across the top (see
[`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
§"The roadmap"); a small number of swimlanes down the side
(platform, data, model lifecycle, governance, and one row for
external standards and vendor terms). Each cell is a *bet*, not
a task. A common shape:

|                 | Now (0–3 mo) | Next (3–9 mo) | Later (9–24 mo) | Beyond (24–36 mo) |
|---|---|---|---|---|
| Platform core   | Bet: X       | Bet: Y        | Bet: Z          | Placeholder       |
| Data plane      | ...          | ...           | ...             | ...               |
| Model lifecycle | ...          | ...           | ...             | ...               |
| Governance      | ...          | ...           | ...             | ...               |
| Standards / vendor terms | ...  | ...           | ...             | ...               |

Guardrails on the map:

- No horizon uses a specific month or week. Month-precision on
  the out-years is precision the author does not have; it
  crowds out the honest uncertainty band.
- Every cell that is a *bet* has a corresponding kill-criterion
  row in §2.3. If a cell has no kill criterion, it is a task,
  not a bet, and belongs in a team-level plan rather than the
  principal-level roadmap.
- The last column ("Beyond" or "36 mo") is deliberately sparse
  and labeled as such. A roadmap that fills the far horizon
  with confident items is the author telling on themselves.

### 2.2 The dependency ledger (~1 page)

Every roadmap of any complexity fails on dependencies rather
than on individual items. The ledger names them explicitly. For
each cross-cell dependency:

| From (cell in §2.1) | To (cell in §2.1) | Type | Owner of the interface | Fail-open behavior |
|---|---|---|---|---|
| Platform / Now: X | Data / Next: Y | Technical (interface) | Platform lead | Data team runs against Y-1 |
| Governance / Now: A | Model / Later: B | Regulatory (approval) | Compliance lead | Later item slips one horizon |
| Standards / Next: C | Platform / Later: D | External (vendor GA date) | Vendor mgmt | Alternate vendor in dual-source |

The ledger is graded on three things: whether every dependency
has a named owner of the *interface* (not just the endpoints),
whether the fail-open behavior is realistic (a fail-open of
"escalate to leadership" is not fail-open, it is a re-plan), and
whether at least one *external* dependency — regulator, vendor,
standards body, sister business unit — is captured. Roadmaps
that show only internal dependencies have missed the load-bearing
external timelines that most often slip.

### 2.3 The bets and decision points (~2 pages)

The heart of the package. Each material bet on §2.1 gets an
entry with a fixed shape:

- **The bet** (imperative): "We commit to X by end of horizon N."
- **Leading indicator**: a signal available before the deadline
  that predicts whether X will land. If the only indicator is
  the deadline itself, the bet has no early warning and is
  under-instrumented.
- **Kill criterion**: the specific signal that would pause the
  bet and force a replan. See
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  on modernization wave kill criteria; the same discipline
  applies to build items.
- **Reversibility note**: if the bet turns out to be wrong,
  what does the unwind cost, and by when?
- **Rejected alternatives** (at least two): what else could have
  gone in this cell, and why did this bet win? A bet without
  named rejected alternatives is the author hiding the
  trade-off from themselves; see
  [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
  §"The strategy memo".

A distinction-level submission additionally captures the
"escape hatch owner" for any bet that ships a new guardrail
into the platform, mirroring the invariants table in
[`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
§2.2 — because the roadmap is the artifact that ships guardrails
into production over time, and each guardrail without an owned
escape hatch turns into a shadow platform within a year.

### 2.4 The sunset ledger (~1 page)

An architecture team that only *adds* systems is generating
future tech debt at a constant rate (see
[`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
common failure modes). The sunset ledger is the roadmap's
answer:

| Item retired | Horizon | Last user migrated by | Shut-off date | Kill-switch owner |
|---|---|---|---|---|
| Legacy X | Next   | End of Next  | Start of Later  | Platform lead |
| Vendor Y | Later  | End of Later | Start of Beyond | Vendor mgmt   |
| Standard Z (adopted-then-superseded) | Later | End of Later | Start of Beyond | Compliance |

Guardrails on the sunset ledger:

- Every build item in §2.1 that replaces something incumbent
  produces a corresponding sunset row here. A roadmap where
  the build side is longer than the sunset side means the
  author has not accepted that the org can hold only so many
  live systems at once.
- The "shut-off date" is a hard commitment, not a target. See
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  §"Skipping the decommission" — a roadmap that lets the last
  10% of users keep the legacy system running has produced two
  systems, permanently.
- Sunset rows for *standards* the org has adopted-then-superseded
  are the highest-signal maturity marker; most roadmaps miss
  this row entirely.

### 2.5 The investment cadence overlay (~1 page)

The roadmap is graded on whether it aligns to the org's actual
budgeting cadence (see
[`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md),
§"Roadmap"). At minimum, the overlay names:

- The **budget-approval milestones** the roadmap depends on
  (annual budget, mid-year true-up, unplanned capital request
  threshold).
- The **contract-renewal decision points** the roadmap surfaces
  ahead of the vendor's calendar, not after it.
- The **capex vs opex mix** implied by each horizon, and how
  reserved-vs-on-demand shifts across horizons as workload
  certainty grows.
- The **reversibility profile of each horizon**: which
  commitments are one-decision-away from reversal and which
  require a multi-quarter wind-down.

Guardrail: no dollar figure appears in this overlay without an
uncertainty band and a stated assumption, per
[`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md),
§"Common mistakes". A point-estimate multi-year forecast is
wrong with probability approaching one, and a CFO reader will
mark the submission down for it.

## 3. Validation steps

There is no build to run at this altitude. Validation is a
sequence of reviews the package must survive, adapted from the
sequence in [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
§3 and specialized to the roadmap altitude.

1. **Internal consistency check.** Re-read the five documents in
   order. Every bet in §2.3 must appear as a cell in §2.1 and
   must be paired with (a) at least one dependency row in §2.2,
   (b) at least one budget-approval or contract-renewal
   milestone in §2.5, and (c) a matching sunset row in §2.4 if
   the bet replaces something incumbent. Cells that fail any of
   these links are decorative — cut them or add the links.
2. **Rejected-alternatives audit.** For each bet in §2.3, does
   the "rejected alternatives" list name at least two plausible
   alternatives with a reason for rejection that a reasonable
   peer could disagree with? A bet with only strawman
   alternatives is propaganda; see
   [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
   §"The strategy memo".
3. **Peer-principal cold read.** Give the package to a peer
   principal architect (or the closest proxy) with no context.
   The test from
   [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
   the reader should be able to disagree with the roadmap and
   still articulate the reasoning — applies here too. Rewrite
   before submitting if they say "I can't tell what you were
   weighing" for any horizon.
4. **CFO-mode read of §2.5.** Read the investment cadence
   overlay as if you had to defend each figure to a skeptical
   CFO. Every dollar figure has an assumption attached; every
   forecast has an uncertainty band; every commitment has a
   reversibility note.
5. **Dependency stress test.** Pick the three dependencies in
   §2.2 whose external owners the org has the least control
   over (vendor GA dates, regulator approvals, standards-body
   ballots). Slip each by one horizon. Which bets in §2.3
   survive, which slip with them, which fail? A roadmap that
   silently fails under any single external slip is
   over-coupled.
6. **Sunset audit.** For every build row in §2.1, is there a
   matching sunset row in §2.4? If not, the roadmap is
   accumulating live systems on net. This is
   [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
   §"Skipping the decommission" applied to the roadmap layer.
7. **Standards-legibility pass.** For every position on the
   roadmap that touches an external standard the org already
   engages with (for instance, the NIST AI Risk Management
   Framework for AI risk practices, CNCF project maturity
   levels for OSS-adoption decisions, MLCommons benchmarks for
   performance claims), confirm the position is stated in terms
   that standard would recognize. This costs little now and
   avoids retrofits later.
8. **Quarterly-review dry run.** Simulate the first quarterly
   review of the roadmap: pretend one bet from horizon "Now"
   has stalled, one dependency from §2.2 has slipped, and one
   sunset in §2.4 is running late. Does the package still let
   the reader decide what to do, or does it collapse? Roadmaps
   that only work when everything goes right have not been
   stress-tested.

## 4. Rubric or review checklist

The checklist below is the principal-track spine for a roadmap
capstone. Where the paired learning brief specifies numeric
dimension weights or hard-check thresholds, those override the
weightings implied here.

A pass on this capstone requires all of the following. Missing
even one item is grounds for revision, not partial credit — the
roadmap is graded as a package.

- [ ] All five documents present, at roughly the target lengths.
      Longer is not better; a memo that exceeds one page usually
      buried a trade-off.
- [ ] §2.1's roadmap map uses 3–5 horizons, not month-by-month
      timelines, and its far horizon is deliberately sparse and
      labeled as such.
- [ ] Every bet in §2.3 appears as a cell in §2.1 and traces to
      a dependency in §2.2, a milestone in §2.5, and — where the
      bet replaces incumbent tech — a sunset row in §2.4.
- [ ] §2.2's dependency ledger names the *owner of the interface*
      for each dependency, not just the endpoint owners, and
      captures at least one external dependency.
- [ ] Each bet in §2.3 has a leading indicator distinct from the
      deadline, a kill criterion, a reversibility note, and at
      least two rejected alternatives with reasons.
- [ ] The sunset ledger §2.4 has at least one row per build item
      in §2.1 that replaces something incumbent, with a shut-off
      date treated as a hard commitment.
- [ ] §2.5 aligns the roadmap to the org's budgeting cadence and
      surfaces contract-renewal decision points ahead of the
      vendor's calendar.
- [ ] Every forecast in §2.5 has an uncertainty band or a stated
      assumption; no point estimates on multi-year lines.
- [ ] Cross-references between documents are consistent — a
      commitment in one is not silently contradicted by another.
- [ ] The package contains at least one explicit "what would
      make this roadmap wrong" statement and at least one
      explicit "what we are deliberately not putting on this
      roadmap and why" statement.
- [ ] The package would be legible to a peer principal architect
      reading it cold, per the test in
      [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).

A distinction-level submission additionally does the following,
though none are required to pass:

- [ ] Notes what would change at the 100-engineer and
      10,000-engineer scales, and under a different budgeting
      cadence than annual-with-quarterly-true-ups.
- [ ] Explicitly cites at least one external standard the
      roadmap intentionally converges on (for example, an entry
      in the NIST AI Risk Management Framework, a CNCF project
      lifecycle transition, an MLCommons benchmark version) and
      dates that convergence to a specific horizon.
- [ ] Includes a written post-review plan for the roadmap
      itself — how the org will audit whether the horizon-N bets
      were right 12–18 months in, and what evidence would
      trigger a mid-horizon course correction.
- [ ] Uses at least one *guardrail-and-escape-hatch* pairing
      from [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
      §2.2 in a bet that introduces a new platform invariant,
      showing the roadmap is aware it is the vehicle by which
      invariants ship.

### 4.1 Mapping to the strategic-package rubric

`project-02` is the higher-resolution roadmap sibling of
`project-01`. The mapping is intentional so that both artifacts
can be graded against a single principal-track spine:

| This package (§2.x) | `project-01` counterpart | Reused rubric dimension(s) |
|---|---|---|
| 2.1 Roadmap map            | 2.5 Modernization sequence     | Architectural soundness; brownfield realism |
| 2.2 Dependency ledger      | 2.4 Coalition plan (partly)    | Operating model; brownfield realism |
| 2.3 Bets and decision points | 2.1 Platform thesis + 2.2 invariants | Executive communication; architectural soundness |
| 2.4 Sunset ledger          | 2.5 Modernization sequence     | Brownfield realism |
| 2.5 Investment cadence overlay | 2.3 Investment thesis      | FinOps / business-case credibility |

## 5. Common mistakes

Patterns graders reliably see on this capstone. Most are variants
of failure modes named in the module-level `SOLUTION.md` files;
they show up here because a roadmap is where all five converge
on a single artifact.

1. **The Gantt chart masquerading as a roadmap.** Every item
   pinned to a specific week 18 months out. Precision the
   author does not have, that crowds out the honest uncertainty.
   Fix by collapsing to the horizon shape in §2.1.
2. **All build, no sunset.** The build side of §2.1 is
   populated, the sunset ledger §2.4 is empty or nearly so.
   The org is quietly accumulating live systems. See
   [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md),
   common failure modes.
3. **Bets without leading indicators.** The only evidence that
   a bet is going wrong is the deadline. By the time the
   deadline is missed, the surrounding roadmap has already
   assumed the bet's success and starts unraveling.
4. **Kill criteria absent or vague.** A kill criterion of
   "the bet is not going well" is not a criterion. It has to
   name the signal, the threshold, and the actor. See
   [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md),
   §"No exit criteria".
5. **Dependency ledger without interface owners.** Endpoints
   have owners; the interface between them frequently does not.
   The interface is where the slip happens.
6. **Only internal dependencies captured.** No regulator, no
   vendor, no standards body on the ledger. The most common
   real-world roadmap slips originate outside the org.
7. **Point-estimate financial forecasts.** A number without an
   assumption is a hostage to fortune. See
   [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md),
   §"Forecasts with no uncertainty bands".
8. **Roadmap ignores the budget calendar.** The engineering
   cycle and the budgeting cycle are decoupled in the roadmap,
   so the horizon-2 bets need approvals that finance sees for
   the first time in the horizon-1 quarterly review. See
   [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md),
   §"Roadmap".
9. **Vendor-renewal dates absent.** The roadmap does not
   surface any vendor's renewal date, so the org walks into
   negotiations with no leverage timeline. Vendors know their
   renewal dates; the roadmap should too.
10. **Presenting inevitability instead of a bet.** If §2.3
    reads as "this is obviously the right sequence," the author
    has hidden the trade-off — often from themselves. Graders
    will spend the review looking for what was hidden. Mirrors
    [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
    §5, item 10.
11. **Skunkworks modernization threaded into the roadmap.**
    Sunset rows depend on a separate "new team" successfully
    replacing the incumbent team's system. See
    [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md),
    §"Skunkworks modernization".
12. **Coalition asks and roadmap milestones misaligned.** A
    horizon-2 bet requires a stakeholder sign-off that the
    coalition plan sequences for horizon-3. One document is
    fictional; usually it is the roadmap. Cross-check against
    §2.5 and, where the org already has a `project-01`
    coalition plan, against
    [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
    §2.4.

## 6. References

### Local curriculum context

- [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
  design philosophy across the principal-architect track; the
  "strategy survives stakeholder rotation" and peer-principal
  cold-read tests are load-bearing frames for this capstone.
- [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
  — the enterprise-platform capstone this roadmap is the
  higher-resolution sibling of; §2.2's invariants table and
  §2.4's coalition plan are directly referenced above.
- [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md)
  — roadmap horizon structure, dependency mapping, and review
  discipline.
- [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md)
  — the standards-adoption timing rows that belong on the
  roadmap, and the standards-legibility validation step.
- [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)
  — budget-cycle alignment, reserved-vs-on-demand mix per
  horizon, forecast uncertainty guidance, vendor-renewal
  decision points.
- [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  — the sequence of asks that must precede each roadmap
  milestone and the coalition-decay observation that motivates
  the quarterly-review dry run.
- [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  — modernization wave structure, kill criteria, and the
  "skipping the decommission" failure mode that motivates the
  sunset ledger §2.4.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — path parity
  and repo rules the capstone submission is expected to follow.

### Paired learning repository

- `../../../ai-infra-principal-architect-learning/projects/project-02-technology-roadmap/README.md`
  — the paired learner brief. It carries the concrete scenario,
  deliverable list, page-count targets, and any numeric rubric
  weights the learner is graded against for a specific org;
  this SOLUTION carries the principal-track spine those
  specifics instantiate. Together they form the graded package —
  submissions are expected to satisfy both.

### External standards commonly referenced at this altitude

A roadmap does not require any particular external framework,
but a distinction-level submission tends to align its language
with at least one of these widely used references. The URLs are
canonical entry points; the exact clause a bet or sunset row
maps to depends on the regulatory and industry context of the
org the roadmap is written for.

- **NIST AI Risk Management Framework (AI RMF 1.0)** —
  <https://www.nist.gov/itl/ai-risk-management-framework> —
  standard vocabulary for AI risk practices in U.S. regulated
  industries. Useful when the roadmap crosses a governance
  guardrail into production and needs to name the risk
  function in terms compliance already recognizes.
- **CNCF project maturity levels (Sandbox / Incubating /
  Graduated)** —
  <https://www.cncf.io/project-lifecycle-guidelines/> — the
  widely used shorthand for OSS-adoption timing decisions on
  the roadmap. A bet that adopts a Sandbox project in horizon
  "Now" is qualitatively different from one that adopts a
  Graduated project.
- **MLCommons benchmarks** — <https://mlcommons.org/benchmarks/>
  — when a roadmap horizon commits to a performance improvement,
  stating it in MLCommons terms is more defensible than an
  internal benchmark that will not survive vendor rotation.
- **Architecture Decision Records (ADRs)** —
  <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
  and the community template at <https://adr.github.io/> —
  Michael Nygard's original ADR format is the low-friction way
  to make each bet in §2.3 reviewable over time as the roadmap
  moves through its quarterly reviews.

Version pins, page references, and internal-policy mappings
should be added by the learner when defending the submission
inside a specific organization; the URLs above are the canonical
entry points, but the exact clause a roadmap element maps to
depends on the regulatory and industry context.
