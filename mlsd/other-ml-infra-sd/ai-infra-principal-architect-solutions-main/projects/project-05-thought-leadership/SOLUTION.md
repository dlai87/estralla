# SOLUTION — project-05-thought-leadership

> Read this *after* attempting the capstone deliverables. Like
> `project-01-enterprise-platform`,
> `project-02-technology-roadmap`, and
> `project-03-governance-framework`, this is a principal-architect
> track project: the solution is a rubric plus a worked structural
> template, not a runnable system. If you are looking for runnable
> platform artifacts, they live in the architect and
> senior-architect tracks; if you are looking for the standards
> and industry-influence discipline that thought leadership sits
> on top of, the module reference is
> [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md).

The paired learner brief for this capstone lives in the sibling
learning repository at
`../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/README.md`
with the customary supporting `requirements.md`,
`architecture.md`, `rubric.md`, `STEP_BY_STEP.md`, and
`deliverables/README.md`. The specific scenario, deliverable
inventory, requirement IDs, and rubric weights are defined by
that brief and should be treated as authoritative for grading.
<!-- Note: exact filename set, scenario numbers, and deliverable inventory are published in ai-infra-principal-architect-learning/projects/project-05-thought-leadership — this SOLUTION is written to compose with whatever the brief specifies at the same altitude as project-01–03, not to override it. -->

The five-block strategic package below is the **principal-track
spine** — the industry-influence system a peer principal
architect (or a simulated ETLT plus external-communications and
legal panel) would grade before reading any depth artifacts.
Every generic thesis, channel choice, and common mistake in this
SOLUTION maps to at least one deliverable of the paired brief;
§4.4 gives the mapping shape. The two artifacts are designed to
compose: the sibling brief supplies the concrete scenario,
deliverable list, and rubric weights the learner submits
against; this SOLUTION supplies the shape and grading altitude
those specifics instantiate. Neither overrides the other — a
learner submission is expected to satisfy both.

## 1. Solution overview

The `project-05-thought-leadership` capstone asks the learner to
produce the **industry-influence system a principal architect
would defend to their ETLT, external-communications lead,
in-house counsel, and a peer principal architect from a
comparable firm** — not a personal-brand plan, not a marketing
campaign, and not a conference calendar. It is the standards-
and-influence sibling of `project-01` (platform strategy),
`project-02` (technology roadmap), and `project-03` (governance):
where those capstones grade decisions the org makes *inside*
its walls, `project-05` grades the deliberate positions the org
(or the principal architect on behalf of the org) takes
*outside* its walls, and the mechanism that keeps those
positions honest, employer-aligned, and — over a 3-year
horizon — measurably influential.

The capstone pulls in material from every module the principal
track presently exercises:

- from `mod-602-industry-standards` — the "engaging with — and
  shaping — standards bodies, open-source consortia, regulatory
  dialogue" discipline the capstone operationalizes (see
  [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md));
- from `mod-604-stakeholder-coalition` — the coalition mechanics
  that make an external position survive the first sponsor
  rotation and the first internal legal review (see
  [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md));
- from `mod-601-org-wide-architecture` — the altitude of
  standards, invariants, and "conditions under which many teams
  can decide well" that a public position necessarily commits
  the org to for years (see
  [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md));
- from `mod-603-multi-year-investment` — the reasoning discipline
  that a 3-year thought-leadership investment must survive when
  the CFO asks for its return (see
  [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md));
- from `mod-605-tech-debt-modernization` — the sequencing and
  kill-criterion patterns that make the influence plan survive
  contact with a public reversal (see
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)).

A passing submission is not a single artifact. It is an
**influence package** of five short, mutually consistent design
blocks — thesis and point-of-view, publication and channel
portfolio, standards and open-source engagement, community and
advisory practice, and measurement / sequencing / coalition —
that together let a peer principal architect (a) see the
falsifiable claim the influence program is built around, (b)
see the delegation rules that keep the principal architect from
becoming the org's only external voice, (c) see the leading
indicators that would trigger course-correction before a lagging
metric (a lost keynote slot, a public retraction) proves the
program is broken, and (d) trace every commitment to an employer
alignment, a legal / disclosure gate, and a coalition move.
Coherence across the package is the primary grading dimension;
depth in any single block is secondary.

### What the deliverable is *not*

- Not a personal-brand plan. If the submission substitutes
  follower counts, X/LinkedIn engagement, or Substack subscribers
  for a falsifiable industry position, the learner has confused
  reach with leadership.
- Not a marketing campaign. Product-marketing plans belong in a
  different discipline; a principal architect's influence rests
  on published technical positions, not on campaign impressions.
- Not a conference calendar. A list of talks accepted is an
  output, not a program. The program is what determines whether
  the talks accepted are the right talks.
- Not a Wikipedia-style neutral survey. A survey with no thesis
  is a literature review; leadership requires a bet.
- Not runnable software. If the submission contains code beyond
  reference implementations that accompany a published position
  (open-source protocol implementation, benchmark harness for a
  measurement claim, corpus for a reproducibility artifact) the
  learner has mistaken the altitude of the exercise.
- Not detached from the employer. A principal architect
  publishing under an employer's imprint carries the employer's
  reputational risk. A submission that treats disclosures,
  employer review, and legal sign-off as bureaucratic obstacles
  rather than load-bearing artifacts has ignored the coalition
  most likely to kill the program (see §5 common mistake #11).

### What "thought leadership" means for grading

For this project, "thought leadership" is the load-bearing
industry-influence system of an org large enough that its
technical positions have external consequences — competitors
adopting or opposing the position, standards bodies weighting
it, customers deferring purchasing decisions to it, regulators
citing it. The program is graded first on whether it would
produce durable, employer-aligned, ethically defensible
influence at that scale — not on how polished a single keynote
reads. A program that would optimize a single-engineer
consultancy (one voice, one channel, ad-hoc cadence) is
under-designed for a firm at principal-architect scale; a
program that would optimize a global-scale hyperscaler (five
tiers of spokespeople, dedicated PR/AR org, standing analyst
briefing program) is likely over-designed for the learner's
scenario. Submissions that make an explicit note of what would
change at the small-firm, mid-cap-employer, and hyperscaler
scales grade above ones that assume a universal answer.

## 2. Worked answer or implementation

The package below is the shape a strong submission takes. Titles
and section counts should match; wording is the learner's. Each
block anchors to the paired brief's deliverable list (§4.4 maps
them cell-by-cell once the brief's deliverable IDs are
inventoried by the learner).

### 2.1 Thesis and point of view (~2 pages + one falsifiability statement)

One page of prose defining the **industry claim** the program
is built around, one page defending it, and a short
falsifiability statement — the observable outcome that would
retire the thesis.

- **The claim** must be a single sentence, stated as an
  imperative or a prediction, not a topic. "AI infrastructure
  will consolidate around open weights and open telemetry" is a
  claim; "AI infrastructure" is a topic. The claim is the
  load-bearing artifact.
- **The evidence base** must cite three kinds of source in
  balance: (a) published industry data (analyst market shares,
  standards-body membership data, foundation-published
  telemetry — cite the source, do not paraphrase), (b) primary
  observations from the author's own operational experience
  (with employer permission, appropriately abstracted), and
  (c) counter-evidence the author took seriously. A thesis with
  no counter-evidence section is propaganda, not leadership;
  reviewers grade the counter-evidence with the same rigour as
  the evidence (see [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md)
  §"The case study" for the same pattern at module altitude).
- **The scope-of-authority** must be stated: is the claim being
  made by the individual, by the individual on behalf of the
  employer, or by the employer with the individual as author?
  These three cases carry different legal, disclosure, and
  coalition consequences. A program that leaves this ambiguous
  will be resolved — badly — by the first inquiry from a
  reporter or a regulator.
- **The falsifiability statement** names, in advance, the public
  evidence that would convince the author to publicly retire or
  amend the thesis. Example shape: "If [named benchmark] shows
  [named opposite result] at [named horizon], we will publish a
  correction under the same imprint." This is the single item
  most correlated with distinction: it converts a "position"
  into a "bet with an exit."
- **The relationship to competitor theses**. Name the two or
  three strongest existing positions in the space (from named
  peer architects, analysts, or standards documents; cite them)
  and explain, in a paragraph each, where the author agrees,
  where the author diverges, and what the disagreement rests on.
  A thesis with no named neighbors reads as if it were formed
  in a vacuum; graders assume this is because the author has
  not read the literature.

The rest of the package instantiates and defends this thesis.
If §2.2's publication portfolio does not evidence the thesis, if
§2.3's standards engagement does not advance it, and if §2.5's
measurement does not track it, the package is incoherent and
grade drops accordingly.

### 2.2 Publication and channel portfolio (~2 pages + a tiered channel map + one editorial calendar)

Two disciplines braided together: **the artifact set** (the
mix of long, medium, and short-form outputs across a rolling
12–18 month window) and **the mechanism** (the editorial
practice, review chain, and archival strategy that keep the
outputs credible over years rather than weeks).

**Channel tiering** as a table (target: 3–4 tiers). Each tier
names the artifact type, the target audience, the review chain,
and the retention expectation.

| Tier | Artifact type                                                                       | Primary audience                        | Review chain                                                 | Retention                                        |
|------|-------------------------------------------------------------------------------------|-----------------------------------------|--------------------------------------------------------------|--------------------------------------------------|
| 1    | Peer-reviewed paper, standards contribution, or book chapter                        | Peer principal architects, standards bodies | Author → co-author panel → external peer review → publisher | Permanent (DOI-anchored or standard-track)       |
| 2    | Long-form technical piece under employer or independent imprint (IEEE Software, ACM Queue, InfoQ, morning-paper-style deep read) | Senior engineers, architects, analysts   | Author → editor → employer legal/comms review → publisher    | ≥ 5 years, canonical URL, versioned              |
| 3    | Conference talk, podcast episode, working-group presentation                        | Working engineers and architects        | Author → speaker coach → employer comms review → venue      | Recorded and re-hostable; slides checked in     |
| 4    | Blog post, short video, thread                                                      | Broad practitioner community            | Author → single named reviewer → publish                    | ≥ 2 years; explicit archival URL, no silent edits |

- **The tier balance** must be defended. A portfolio dominated
  by Tier 4 (rapid blog posts, threads) may reach a large
  audience but does not durably shift industry positions; a
  portfolio dominated by Tier 1 (peer review) does not scale to
  the cadence needed to stay relevant. The load-bearing move is
  the ratio: state the ratio, defend it in three sentences, and
  attach it to the thesis in §2.1 (Tier 1 is for the load-
  bearing claim; Tier 4 is for the evidence trail leading to
  it).
- **The editorial calendar** covers a rolling 12 months, names
  the artifact, the tier, the intended venue (or set of
  candidate venues), the required lead time, the reviewer, and
  the dependency on any operational milestone (a launch, an
  incident retro that has cleared internal review, a benchmark
  release). Publish this calendar internally, not externally;
  the calendar is a coalition artifact, not a marketing one.
- **Cadence discipline**. Publishing on a *predictable* rhythm
  matters more than publishing on a *high* rhythm. A monthly
  Tier 2 or Tier 3 output plus a quarterly Tier 1 or high-Tier-2
  output over three years produces more durable influence than a
  daily Tier 4 burst that goes silent for a quarter (see
  [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)
  on the same "consistency over amplitude" pattern in
  capital-allocation reasoning).
- **The archival and correction policy**. Every Tier 1 and Tier
  2 output has a canonical, dated URL; every substantive edit
  after publication is either a versioned successor or an
  in-line correction with a change note, never a silent rewrite.
  This is the single most-cited practice in academic and
  standards-track credibility; the same discipline applies to
  employer-hosted long-form. See references §6 for the ACM /
  IEEE ethics-of-publication anchors.
- **The republication and translation posture**. State whether
  the program grants right-of-republication (Creative Commons
  licence — name which one; the CC-BY vs CC-BY-SA vs CC-BY-NC
  choice has downstream coalition consequences and must be a
  decision, not a default) and how translations will be handled
  (community-driven vs commissioned; canonical translation vs
  aggregated versions). See references §6 for Creative Commons.
- **The retraction and correction protocol**. This is the
  distinction bar. Publish, in advance, the process by which the
  program will retract a published position that turns out to be
  wrong. Include the trigger (a falsified claim in §2.1's
  evidence base; a factual error identified by a reader; a
  regulatory finding), the actor (the author, with employer
  comms sign-off), the artifact (a versioned successor plus a
  visible retraction notice on the original URL), and the
  timeline (target ≤ 30 days from identification to retraction
  notice for factual errors; ≤ 90 days for thesis-level
  reversals with employer review). A program that has no
  retraction protocol will improvise its first retraction — and
  the improvisation is where careers end.

### 2.3 Standards and open-source engagement (~2 pages + a body-selection matrix + a delegation plan)

The load-bearing discipline here is **selection and delegation**,
not participation. Principal architects who attempt to
personally represent their employer at every relevant standards
body burn out and become a bottleneck; principal architects who
skip standards entirely watch competitors write the rules the
employer will later be graded against.

- **Body selection** as a matrix on (a) relevance to §2.1's
  thesis, (b) the employer's strategic surface area,
  (c) the specific-influence realistically achievable at the
  employer's headcount and public track record, and
  (d) the participation cost (staff time, membership fee,
  travel, chair-hours). Score each candidate body across these
  four axes, rank, then draw a line at the resource envelope.
  Bodies below the line are named and explicitly declined, not
  silently ignored — the paper trail matters when a peer
  architect asks "why not IETF for this?"
- **The named universe** the matrix scores against varies with
  the thesis; canonical entries for AI-infrastructure include:
  Linux Foundation projects (CNCF, LF AI & Data, LF Networking,
  PyTorch Foundation), IETF, W3C, IEEE working groups, ISO/IEC
  JTC 1 subcommittees (notably SC 42 for AI), OASIS,
  MLCommons, NIST (specifically the AI RMF and CSF working
  groups), NIST AISI's evaluation efforts, ACM SIGs, and
  discipline-specific standards bodies (e.g., HL7 for
  healthcare, NACS/PCI for payments). Cite each body by its
  primary URL; do not paraphrase its charter (see references
  §6). Regional bodies (ETSI, JISC, GB/T) belong on the matrix
  where the employer's regional exposure warrants; a program
  with no regional entry in a firm with material EU or China
  exposure is under-designed.
- **The engagement tiering** — three levels per selected body:
  1. **Voting or chair-track participation** (the highest-cost,
     highest-leverage engagement; requires named deputy so the
     seat does not lapse under illness or reorganization).
  2. **Working-group contribution** (drafting text, reviewing
     PRs on specifications, publishing implementation reports;
     the level at which most durable influence is exercised).
  3. **Attendance and readership** (subscribing to mailing
     lists, attending public meetings, filing implementation
     experience reports; the level below which "engagement" is
     LinkedIn theatre).
- **Delegation and succession**. For every voting or chair-track
  seat, name the primary, the deputy, and the succession path
  in advance. Standards seats that lapse under reorganization
  are a coalition failure disguised as an administrative one.
  See [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  on the "strategy survives stakeholder rotation" test — the
  same test applies here.
- **Contribution IP and licence stance**. Every standards or
  open-source contribution triggers an IP question: is the
  contribution under the body's own IPR policy (e.g., IETF
  BCP 78/79, W3C Patent Policy, Apache CLA)? Has the employer's
  legal team signed off on the policy in general (so
  individual contributions do not require case-by-case
  review)? A program without a documented answer here will
  either stall its first PR in legal review or (worse) contribute
  under uncertainty and pay for it later.
- **Reference-implementation strategy**. For any specification
  the program contributes to, the deliverable set may include a
  reference implementation. State the licence (Apache 2.0, MIT,
  or BSD are the load-bearing candidates in this space;
  GPL-family licences change downstream coalition dynamics and
  must be an explicit decision), the maintenance owner (an
  engineering team, not the principal architect personally), the
  archival plan (a repository with named org owner, not the
  author's personal account), and the retirement policy
  (when the specification is retired or superseded, how the
  implementation is archived so that references remain
  resolvable). See references §6 for Linux Foundation and OSI
  guidance.
- **Community-code-of-conduct alignment**. Every participation
  in a body brings the body's code of conduct into the
  author's professional life. Cross-reference the employer's
  code of conduct with each body's; where they disagree, decide
  which controls in which situation and record the decision.

**Worked example** (the brief may ask for one or two): pick a
body where the author's employer is *not currently* voting and
where a specific working item advances §2.1's thesis. Write the
paragraph the working-group chair would receive: what the
employer offers (staff time, implementation experience, use
cases), what the employer wants (specific-influence on the item),
and the resource commitment the employer is prepared to make.
This paragraph is the artifact — not the LinkedIn post
announcing the engagement.

### 2.4 Community and advisory practice (~1 page process + a conflicts register + a decline template)

The load-bearing discipline here is **decline discipline**. A
principal architect who accepts every advisory board seat,
podcast invitation, and meetup keynote request becomes an
influence vending machine and stops producing durable
positions; a principal architect who declines everything cannot
build the coalition the thesis needs. The graded artifact is
the framework for *deciding* rather than the roster of accepted
engagements.

- **Engagement categorization**. Four buckets:
  1. **Advisory and board work** — startup technical advisor,
     foundation TAB / TOC seat, standards-body chairing (which
     also lives in §2.3), academic-advisory-board seat,
     regulator working-group participation. Highest coalition
     leverage; highest disclosure surface.
  2. **Speaking and panels** — invited keynote, conference
     tutorial, university guest lecture, podcast interview,
     analyst briefing.
  3. **Community building** — meetup organizing, mentoring
     programs, workshop authoring, open-source maintainership.
  4. **Peer review and citation work** — reviewing for
     journals, conference PCs (e.g., OSDI/SOSP/NSDI/SIGMOD/
     ICML/NeurIPS depending on discipline), standards-track
     documents; letters of support; citations of others'
     positions in the author's own outputs.
- **Time envelope**. Per calendar year, publish (internally)
  the total hours the program will commit across the four
  buckets and the split. A program without a stated envelope
  will overrun; overrun is the leading indicator of the
  author's own §2.1 thesis going stale (no time to think, only
  time to speak).
- **Decline template**. A published, reusable paragraph the
  author sends when declining a request that falls outside
  scope. Publishing the template internally does two things: it
  removes the cognitive tax of drafting a decline each time,
  and it makes the "why not this" reasoning legible to the
  coalition. The template names the category the decline falls
  under; over time the pattern of declines is itself an
  informative artifact (see [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  on "disagreement is information").
- **Conflicts register** — a checked-in (internally, not
  publicly, unless the employer's disclosure regime differs)
  register of every advisory relationship, board seat,
  equity holding tied to a technical position, and paid
  engagement. Every entry names the counterparty, the
  compensation form (equity, cash, in-kind, unpaid), the
  disclosure boundary (which venues the relationship must be
  disclosed to), and the recusal condition (what topics the
  author will refuse to opine on because of the relationship).
  For US-domiciled programs, this maps to SEC insider-trading
  and Regulation FD considerations for public-company employers;
  for regulated-industry programs, sector-specific rules apply
  (see references §6 for anchors).
- **Employer sign-off gating**. Every category-1 engagement
  and every category-2 engagement above a stated stakes
  threshold (e.g., audiences > 500, on-the-record media,
  regulator-adjacent panels) requires named sign-off from the
  employer (typically comms + legal + line manager). Below the
  threshold, the program self-authorizes with a filed record.
  The threshold is a decision the submission must *make*;
  reviewers grade "no threshold" as absence of process, not
  freedom.
- **Ethics-of-influence anchors**. The program cites at least
  one external code (ACM Code of Ethics, IEEE Code of Ethics,
  or discipline-specific equivalent — see references §6) as
  the standard the author holds their public positions to.
  Anchoring to an external code is the practice most likely to
  survive an employer change; internal codes rotate faster than
  a principal architect's public track record.

### 2.5 Measurement, sequencing, and coalition (~2 pages + 4 dashboard mocks + a 3-year plan)

This is the "does the influence program work, and will it
survive its first sponsor rotation and its first public
reversal?" block. Three sub-artifacts.

**Telemetry** — 8–12 indicators, each with a target, a
measurement, an owner, a publication cadence, and a **leading /
lagging tag**. Leading indicators drive intervention; lagging
ones prove influence over years. A defensible set (learners
should adapt to the paired brief's specifics):

- **Publication cadence adherence** (Tier 1 / 2 / 3 / 4
  scheduled vs published, per quarter) — **leading**; ≥ 90%
  on-plan; monthly. Intervention: two consecutive quarters
  < 90% triggers a portfolio review — the calendar is either
  too aggressive or the author is over-committed elsewhere
  (see §2.4).
- **Time-to-first-citation** of a Tier 1 or Tier 2 output —
  lagging; median ≤ 6 months to first external citation for
  Tier 1, ≤ 3 months for Tier 2; quarterly.
- **Retraction rate** — lagging; target ≤ 5% of Tier 1 / 2
  outputs retracted within their retention window; annually.
  A rate of zero is *also* a warning: it suggests the program
  is publishing only what is safe rather than what is true (see
  §5 common mistake #7).
- **Standards contribution acceptance rate** (accepted /
  submitted) — lagging; discipline-dependent target; per body
  per quarter.
- **Seat coverage** (voting / chair-track seats held with named
  primary and deputy, out of §2.3-planned) — **leading**;
  target 100%; quarterly. Intervention: any seat without a
  deputy for two consecutive quarters triggers a coalition
  review; a lapsing seat is a coalition failure.
- **Advisory engagement load** (hours committed vs §2.4
  envelope) — **leading**; ≤ 100% of envelope; monthly.
  Intervention: > 110% for two months triggers a decline
  cadence and, if needed, resignations from below-threshold
  engagements.
- **Falsifier watchlist** — the list of concrete external
  outcomes that would falsify §2.1's thesis, reviewed each
  quarter — **leading**; treat any positive on the watchlist as
  a mandatory thesis-review event. This is the single indicator
  most correlated with the "leadership vs pundit" distinction.
- **Retraction-to-first-notice latency** — lagging; ≤ 30 days
  for factual errors, ≤ 90 days for thesis-level; measured on
  each event.
- **Employer alignment audit** — quarterly; qualitative;
  reviewed by the named employer contact (comms lead + legal +
  line manager). Any material misalignment is a leading
  indicator of a coming public retraction or an internal
  program pause.
- **Coalition-durability check** — annually; does a named
  successor exist for the program's public-facing role? This
  is the "does the strategy survive stakeholder rotation" test
  from
  [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md)
  applied to the author personally.
- **Cost-to-employer ledger** (staff time + travel + fees +
  legal review + reference-implementation maintenance) —
  lagging; quarterly; the CFO-visible number.
- **Cost-per-durable-position** — lagging; annually; total
  program cost divided by count of Tier 1 / high-Tier 2
  outputs still canonically cited at 24 months. This is the
  single most defensible ROI number the program produces; see
  [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md).

Each indicator names its instrumentation source (calendar
system, standards-body membership registers, Google Scholar /
Semantic Scholar / OpenReview for citations where discipline
permits, GitHub for reference-implementation activity, internal
conflicts register) and its owner (program ops for the plumbing,
the principal architect for the framing).

**Four dashboard mocks** (the brief may hard-check this):
publication cadence (audience: employer comms lead + line
manager, monthly), standards footprint (audience: employer
technology strategy + peer architects, quarterly), engagement
health (audience: principal architect + line manager, monthly),
and thesis-liveness (audience: principal architect + peer
review panel, quarterly). Each mock is captioned with the
audience and the decision it is meant to inform.

**Three-year rollout** — three phases with per-phase success /
refine / pivot / abandonment criteria. A defensible shape:

| Phase | Months | Content                                                                                              | Success                                                                                              | Refine                        | Pivot                                              | Abandon                                                        |
|-------|--------|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|-------------------------------|----------------------------------------------------|----------------------------------------------------------------|
| 0     | 1–3    | Thesis lock-in with employer comms & legal; conflicts register; channel-tier draft; first Tier 4     | Comms + legal sign-off on §2.1 + §2.4                                                                | One reviewer blocking         | Two reviewers blocking                             | Comms or legal declines to sign at all                        |
| 1     | 4–15   | Editorial calendar in motion; two selected standards bodies engaged at working-group tier; ≥ 1 Tier 1 | ≥ 90% cadence adherence; ≥ 1 accepted standards contribution; ≥ 1 external citation of a Tier 1 output | ≥ 60% cadence adherence       | < 60% cadence adherence for two quarters           | A public retraction that comms judges materially harmful       |
| 2     | 16–24  | Voting-track seats where achieved; reference implementation in production for ≥ 1 spec               | Named succession filed for each seat; reference implementation cited externally                     | Any seat without deputy       | Two seats without deputies                         | Author leaves employer without succession filed                |
| 3     | 25–36  | Steady state; thesis review; portfolio versus falsifier watchlist re-scored                          | Thesis holds or is explicitly amended in Tier 1; portfolio rebalance defensible in ≤ 2 pages         | Thesis softens without notice | Thesis quietly abandoned                          | Falsifier watchlist item confirmed without published response  |

Each phase names ≥ 1 **coalition-risk moment**: e.g., the first
comms-team objection that has to be adjudicated by the CEO's
office, the first standards-body vote where the employer's
position conflicts with a customer's public position, the first
external claim that the author's Tier 1 position advantages the
author's own advisory holdings (see §2.4). Each coalition
moment has a **response plan**, not a hope. The named
coalitions are: comms/AR, legal, the employer's line manager,
the peer principal architects at competitor firms (who may
publicly disagree; disagreement is a coalition-durability
signal, not a failure), the standards-body counterparties
(chairs, working-group leads), and — over the 3-year horizon —
the successor named in the coalition-durability check.

**Meta-governance** — the amend-the-program process. This is
the distinction bar. Named triggers (a falsifier hit, a
retraction of a Tier 1 or high-Tier 2 output, a change of
employer, a change of comms leadership), a named amendment
review body (the author + line manager + comms lead + one
external peer, at minimum), and a stage gate at month 12 and
month 24 to formally re-charter or absorb amendments.

## 3. Validation steps

There is no build to run at this altitude. Validation is a
sequence of reviews the package must survive, adapted from the
sequences in
[`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
§3,
[`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
§3, and
[`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
§3, specialized to the influence altitude.

1. **Requirement-traceability check.** Every requirement ID in
   the paired brief's `requirements.md` traces to at least one
   section of the package above. Requirements with no home are
   gaps; sections with no requirement are decoration.
2. **Internal consistency check.** Re-read the five blocks in
   order. Every claim in the thesis (§2.1) is evidenced by at
   least one Tier 1 or Tier 2 output on the calendar (§2.2), is
   advanced by at least one working-group item (§2.3), and has
   at least one indicator (§2.5) tracking it. Every advisory
   engagement (§2.4) has an entry in the conflicts register and
   a stated disclosure boundary. Cells that fail any of these
   links are decorative — cut them or add the links.
3. **Falsifiability audit.** Read §2.1's falsifiability
   statement out loud. Is it a concrete outcome you could plot
   on a chart, or is it a hedge? If a reasonable peer principal
   would answer "you have not committed to anything," rewrite
   until the sentence names a benchmark, a market share, a
   citation count, or a comparable observable.
4. **Leading-vs-lagging audit.** Count the indicators tagged
   **leading**. A program whose intervention rules all fire on
   lagging indicators is a program that only learns after the
   outcome is unrecoverable. Target: ≥ 4 leading indicators with
   named intervention rules, matching the discipline in
   [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
   §3.4.
5. **Peer-principal cold read.** Give §2.1 and §2.5 to a peer
   principal architect (or a competent surrogate) with no
   context. The
   [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md)
   test — the reader should be able to disagree with the design
   and still articulate the reasoning — applies here. If the
   reader says "I cannot tell what would falsify this thesis"
   or "I cannot tell which venue is Tier 1 and which is Tier 4,"
   the block is not yet legible.
6. **Hostile-reporter read.** Read §2.1 as a business
   reporter who has been briefed on the author's advisory
   holdings (§2.4). Would every paragraph survive the question
   "does this position benefit a company you personally hold
   equity in?" If any Tier 1 or Tier 2 position would not
   survive, the conflicts register is under-scoped or the
   position is under-disclosed.
7. **Employer-comms cold read.** Give §2.5's rollout plan and
   §2.4's conflicts register to the employer's comms lead as
   a real intake. Would they sign off, or would they demand
   changes? A program whose comms lead has not read it before
   the first Tier 1 output is a program that will discover its
   comms constraints in public.
8. **Legal-review dry run.** Read §2.3's standards contribution
   plan against the employer's IP policy and the target bodies'
   IPR policies (IETF BCP 78/79, W3C Patent Policy, Apache CLA,
   etc.). Every "in-scope" contribution has a signed-off
   licence path. Gaps here are the ones that stall a submitted
   PR the day the working-group chair asks for the CLA.
9. **Rollout-abandonment plausibility.** Read the rollout plan's
   Abandon column. Would you actually invoke it under the named
   trigger, or would you argue for one more quarter? A rollout
   whose abandon triggers no one would ever pull is a rollout
   with no kill criteria — see
   [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md).
10. **Anti-vanity stress test.** For each of the four dashboards
    in §2.5, name the decision the dashboard would change *this
    quarter*. If the dashboard's answer is "we would keep an
    eye on the trend," the indicator is a scoreboard, not
    instrumentation. Instrumentation implies an action; if none
    is named, the indicator does not belong in the top 12.
11. **Falsifier replay.** Assume the program has been running
    for four quarters and one item on the falsifier watchlist
    has been observed in public (a competitor benchmark, an
    analyst forecast reversal, a standards outcome). Does the
    meta-governance process (§2.5) route the program into a
    thesis-amendment or a Tier 1 retraction within the stated
    latency? A program whose own amendment process is undesigned
    is a program that cannot learn.
12. **Standards-legibility pass.** For every position that
    touches an area covered by an external standard the author's
    firm already engages with (ThoughtWorks Tech Radar, MADR /
    Nygard for ADR practice references, NIST AI RMF, ISO/IEC
    23894, ISO/IEC 42001, CNCF project maturity model, MLCommons
    benchmark categories), confirm the position is stated in
    terms that standard would recognize. This costs little now
    and avoids costly retro-framing later.
13. **Coalition-durability replay.** Assume the author's line
    manager, comms lead, and CEO have all changed in the last
    12 months. Does §2.5's coalition-durability check produce a
    non-empty successor? If not, the influence program is a
    personal brand in the shape of an institutional program;
    grade drops accordingly.

## 4. Rubric or review checklist

The checklist below is the principal-track spine and is
intended to compose with the paired learning brief's rubric.
Where the brief specifies dimension weights (as with
`project-03-governance-framework`'s eight-dimension rubric),
those weights override any implicit weighting here; the checklist
items below map to those dimensions per §4.4.
<!-- Note: the exact dimension list and weights are published by the paired ai-infra-principal-architect-learning brief for project-05-thought-leadership — this SOLUTION assumes a similar shape to project-01–03 rubrics but does not hard-code weights. -->

A pass on this capstone requires all of the following. Missing
even one item is grounds for revision, not partial credit — the
influence program is graded as a package.

- [ ] All five strategic-package blocks present, at roughly the
      target lengths; longer is not better and usually means the
      thesis was hedged instead of stated.
- [ ] §2.1 states a single-sentence thesis, cites at least three
      kinds of evidence in balance, addresses at least two
      named neighboring positions, and closes with a
      falsifiability statement that names a concrete external
      observable and a horizon.
- [ ] §2.1 makes the scope-of-authority explicit (individual /
      individual-on-behalf-of-employer / employer-authored).
- [ ] §2.2's channel tiering names 3–4 tiers with artifact type,
      audience, review chain, and retention per tier; the
      tier-balance ratio is stated and defended in ≤ 3
      sentences.
- [ ] §2.2's editorial calendar covers 12 rolling months with
      artifact, tier, venue-candidate set, lead time, reviewer,
      and dependency-on-milestone per row.
- [ ] §2.2 documents an archival policy (canonical dated URLs,
      no silent edits) and a retraction protocol (trigger,
      actor, artifact, timeline).
- [ ] §2.3's body-selection matrix scores at least six candidate
      bodies on relevance, surface area, achievable influence,
      and participation cost; the resource line is drawn and
      declined bodies are explicitly named.
- [ ] §2.3 assigns engagement tier (voting / working-group /
      readership) per selected body and names the primary,
      deputy, and succession for each voting or chair-track
      seat.
- [ ] §2.3 documents the IP / CLA path for each selected body
      and names the licence for any reference implementation.
- [ ] §2.4 categorizes engagements into the four buckets, names
      an annual hour envelope, and includes a decline template.
- [ ] §2.4 includes a conflicts register with counterparty,
      compensation form, disclosure boundary, and recusal
      condition per entry; and states the sign-off threshold
      for category-1 and category-2 engagements.
- [ ] §2.4 anchors its ethical framing to at least one external
      code (ACM, IEEE, or discipline-equivalent).
- [ ] §2.5 lists 8–12 indicators, each tagged **leading** or
      **lagging**, with target / measurement / owner / cadence;
      ≥ 3 leading indicators each carry a named intervention
      rule; ≥ 4 dashboard mocks exist with audience and the
      decision each mock informs.
- [ ] §2.5 includes a falsifier watchlist, a retraction-latency
      indicator, and a cost-per-durable-position indicator; the
      thesis-liveness dashboard's owner is the principal
      architect, not comms.
- [ ] §2.5's 3-year rollout has per-phase success / refine /
      pivot / abandon criteria, ≥ 3 named coalition-risk
      moments each with a response plan, and stage gates at
      months 12 and 24.
- [ ] Every requirement ID in the paired brief's
      `requirements.md` traces to a section of the package.
- [ ] Every indicator (§2.5) has an owner and a failure-triggered
      path into meta-governance.
- [ ] The package would be legible to a peer principal architect
      reading it cold, per the test in
      [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).
- [ ] The package contains at least one explicit "what would
      make this thesis wrong" statement (in §2.1) and at least
      one explicit "what we are deliberately not opining on
      publicly and why" statement (in §2.3 or §2.4).

A distinction-level submission additionally does all of the
following:

- [ ] Publishes a **retraction protocol** in §2.2 with a
      concrete example — a paragraph the author would post if a
      named Tier 1 output turned out to be materially wrong.
- [ ] Names a **specific working-group item** in §2.3 the
      author would contribute drafting text to in year 1, with
      the specific-influence being sought stated in a sentence.
- [ ] Includes a **published exception to the program itself** —
      at least one area where §2.1's thesis says "here we
      defer to a competing position and here is why."
- [ ] Includes a **meta-governance design** — the documented
      process by which the program itself is amended, with
      stage gates at month 12 and 24.
- [ ] Notes on what would change at the small-firm,
      mid-cap-employer, and hyperscaler scales, showing the
      author knows the assumed org size is a choice
      (per §1 above).
- [ ] Explicitly cites at least one external standard (ACM /
      IEEE code of ethics, ISO/IEC 42001 or 23894 for AI
      governance, NIST AI RMF, Creative Commons licence family,
      an IPR policy — see §6) as the anchor for a specific
      position rather than inventing terminology internally.

### 4.4 Mapping to the learning-repo deliverable set

The five-block strategic package above is the principal-track
spine; the learner-facing brief will define its own deliverable
inventory (analogous to project-03's D1–D10). Each
strategic-package block maps to one or more graded artifacts.
Because the paired-brief's exact deliverable IDs are not
enumerated in this SOLUTION, the mapping is written by shape;
learners should populate the right-hand column against the
brief they are submitting to.

| Strategic-package block (this SOLUTION)                     | Learning-repo artifact shape                                                                                                       | Likely rubric dimensions exercised                          |
|-------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| 2.1 Thesis & point of view                                  | The "thesis document" or "position paper" deliverable; the falsifiability statement                                                | Thesis clarity; evidence rigor; falsifiability              |
| 2.2 Publication & channel portfolio                         | The "editorial calendar" and "channel tiering" deliverables; sample Tier 1 / 2 / 3 / 4 pieces if the brief asks for them            | Craft; cadence discipline; archival / retraction rigor       |
| 2.3 Standards & open-source engagement                      | The "body-selection matrix" and "engagement plan" deliverables; the reference-implementation licence stance                        | Standards leverage; delegation; IP hygiene                  |
| 2.4 Community & advisory practice                           | The "conflicts register" and "engagement policy" deliverables; the decline template                                                | Ethical rigor; coalition-conflict management                |
| 2.5 Measurement, sequencing, coalition                      | The "measurement plan," "3-year plan," "coalition plan," and "launch comms" deliverables                                           | Telemetry & KPI fitness; rollout; coalition durability; comms |

<!-- Note: learners should replace the middle column with the paired-brief's actual deliverable IDs when submitting against a specific version of the brief's deliverables/README.md. -->

## 5. Common mistakes

Patterns graders reliably see on this capstone. Most are
variants of failure modes named in the module-level
`SOLUTION.md` files; they show up here because the capstone is
where all five modules converge on a single influence system.

1. **Personal brand costumed as institutional program.** The
   submission's dashboards track follower counts, engagement
   rates, and subscriber growth; the thesis is undated and
   unnamed; conflicts and disclosures are absent. The learner
   has written a personal-brand plan and labelled it thought
   leadership. Fix by adding the employer sign-off gate in §2.4
   and the coalition-durability check in §2.5.
2. **Thesis as topic, not claim.** §2.1 reads "the future of AI
   infrastructure" or "open-source and enterprise software" —
   an *area of interest*, not a claim. A topic cannot be
   falsified; a topic cannot be a bet. Fix by writing a single
   imperative sentence and defending it.
3. **No falsifiability.** The thesis is a claim, but nothing
   would retire it. Every hedge has an escape clause; every
   piece of counter-evidence is dismissed as "not yet
   conclusive." The program can be right forever, which means
   it cannot be right meaningfully.
4. **Publication portfolio dominated by Tier 4.** Twenty blog
   posts and threads per month, zero Tier 1 outputs in twelve
   months. The program has volume but not durability. The
   distinction between influence and impressions collapses
   after the first job change: Tier 4 outputs on employer
   platforms do not travel with the author, while Tier 1
   outputs do.
5. **Standards engagement as name-collection.** §2.3 lists
   membership in eight bodies; §2.5 has no indicator for
   working-group contributions accepted. Membership without
   contribution is anti-signal — the employer is paying for
   badges. Fix by picking two bodies to actually contribute to
   and explicitly declining the others (see
   [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md)).
6. **No conflicts register.** §2.4 lists advisory boards and
   speaking honoraria without a disclosure boundary; a
   business-desk reporter would surface the omission in one
   day. This mistake historically ends careers; the register is
   cheap and its absence is expensive.
7. **Zero-retraction target.** The measurement plan targets
   zero retractions. This is either dishonest or safety-first
   to the point of publishing nothing meaningful. Real
   Tier 1 / Tier 2 work occasionally requires correction; the
   right target is a low but non-zero rate paired with a fast
   retraction-latency indicator.
8. **Only-the-author on every seat.** §2.3 assigns the author
   as primary for every standards seat and names no deputy. The
   seat lapses the first time the author is ill, promoted, or
   leaves. This is the coalition failure disguised as an
   administrative one, and it is the single failure mode most
   likely to be discovered too late to correct.
9. **Employer relationship as background noise.** The plan does
   not mention comms review, legal review, or line-manager
   approval; §2.4's threshold for sign-off is unstated. The
   first published position the employer objects to becomes an
   escalation, not a workflow.
10. **Lagging-only indicators.** All 12 indicators measure
    outcomes: citations, retractions, seat counts, cost. All
    are lagging. The program has no way to intervene before an
    outcome is knowable. Cap on rubric-analog dimension for
    telemetry.
11. **Ignoring the employer coalition.** The submission treats
    employer sign-off as a compliance chore rather than a
    coalition move. The comms team, legal team, and line
    manager are the coalitions most likely to kill the program
    (or, in the good case, most likely to be its long-term
    sponsors). A submission that does not run its rollout past
    them before publishing has misjudged its own risk model.
12. **Rollout without coalition-risk moments.** The 3-year plan
    is three phases, each with success criteria, no named
    coalition-risk moments and no response plans. When the
    first standards vote conflicts with a major-customer public
    position, the plan has nothing to say.
13. **Missing meta-governance.** The program designs the
    influence system but no design exists for how the program
    itself is amended. First failed thesis in month 18 finds no
    path back to a corrected position; improvisation follows,
    and the coalition erodes. Mirrors
    [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
    §5 item 9.
14. **Presenting inevitability instead of a bet.** If the
    program reads as "this is obviously the right industry
    position," the author has hidden the trade-off — often from
    themselves. Every graded principal-track deliverable makes
    the bet explicit; this one is no exception. Mirrors
    [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
    §5 item 10 and
    [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
    §5 item 10.
15. **Skipping the "make a call" open questions.** The paired
    brief will list decisions the submission must close (choice
    of tier ratios, choice of licence family for reference
    implementations, choice of code-of-ethics anchor, choice of
    sign-off threshold, choice of successor). A submission that
    leaves those open forfeits the coalition's trust that the
    program will make decisions publicly, since it could not
    make them privately. Close all of the brief-listed
    open questions with a defended position or the program is
    unfinished.

## 6. References

### Local curriculum context

- [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
  design philosophy across the principal-architect track; the
  "strategy survives stakeholder rotation" and peer-principal
  cold-read tests are the load-bearing frames for this
  capstone.
- [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md) —
  the enterprise-platform capstone whose invariants and public
  positions the thought-leadership program takes to standards
  bodies and long-form publication.
- [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md) —
  the roadmap capstone whose bets and decision points the
  influence program instantiates externally; the
  bet-with-kill-criterion shape reappears as the thesis with
  falsifiability statement.
- [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md) —
  the governance capstone whose ADR and radar disciplines
  supply the internal reasoning the external positions cite.
- [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md) —
  the case-study-as-argument and strategy-memo shapes the
  Tier 1 / Tier 2 publication portfolio reuses.
- [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md) —
  the standards-engagement discipline the §2.3 body-selection
  matrix and delegation plan operationalize; this is the module
  most directly reused.
- [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md) —
  the multi-year investment reasoning the 3-year rollout and
  the cost-per-durable-position indicator borrow.
- [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md) —
  the coalition-mechanics module; "disagreement is information"
  and "coalitions decay" motivate this SOLUTION's decline
  template and coalition-durability check.
- [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md) —
  the sequencing and kill-criterion patterns reused in §2.5's
  3-year plan.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — path
  parity and repo rules the capstone submission is expected to
  follow.

### Paired learning repository

- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/README.md`
  — the scenario, deliverable inventory, key questions the
  portfolio must answer, and the duration breakdown for the
  capstone.
- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/requirements.md`
  — the traceable requirement set every deliverable must map
  back to.
- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/architecture.md`
  — the influence-system design doc with the channel tiering,
  standards-engagement plan, and open questions the submission
  must close.
- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/rubric.md`
  — the dimension breakdown and hard-checks used at grading;
  authoritative on weights.
- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/STEP_BY_STEP.md`
  — the phase-level schedule the duration plan expands into.
- `../../../ai-infra-principal-architect-learning/projects/project-05-thought-leadership/deliverables/README.md`
  — the deliverables directory layout, per-deliverable
  checklists, and file-naming conventions the submission is
  expected to follow.

<!-- Note: the six paths above are the customary layout across the principal-architect track (project-01 through project-03 follow the same set); if a future revision of the paired brief renames a file, this section should be updated to match. -->

### External standards and canonical references

The capstone does not require any particular external
framework, but a distinction-level submission tends to anchor
its language to at least one of these widely used references.
The URLs are canonical entry points; the exact clause a
program element maps to depends on the discipline and
jurisdiction of the org the program is written for.

- **ACM Code of Ethics and Professional Conduct** —
  <https://www.acm.org/code-of-ethics> — the anchor most
  commonly cited for public technical positions in computing;
  §2.4's ethical-framing hook.
- **IEEE Code of Ethics** —
  <https://www.ieee.org/about/corporate/governance/p7-8.html>
  — the parallel anchor with emphasis on engineering-wide
  practice; commonly cited alongside the ACM code.
- **NIST AI Risk Management Framework (AI RMF 1.0)** —
  <https://www.nist.gov/itl/ai-risk-management-framework> —
  standard vocabulary for AI risk practices; the load-bearing
  reference where the thesis touches AI-model risk or model
  governance.
- **ISO/IEC 42001:2023 — AI management systems** —
  <https://www.iso.org/standard/81230.html> — the ISO
  management-system standard for AI; a defensible anchor when
  the program's thesis addresses organization-level AI
  governance.
- **ISO/IEC 23894:2023 — AI risk management** —
  <https://www.iso.org/standard/77304.html> — the ISO AI-risk
  guidance; anchor for the risk-management vocabulary in Tier 1
  outputs on AI safety or reliability.
- **ThoughtWorks Technology Radar** —
  <https://www.thoughtworks.com/radar> — the canonical
  Adopt / Trial / Assess / Hold shape and the volume archive
  the §2.1 thesis can cite when disagreeing with a public
  position (the disagreement is a signal, not an
  embarrassment).
- **MLCommons benchmarks** —
  <https://mlcommons.org/benchmarks/> — when a Tier 1 output
  makes a performance claim about ML infrastructure, stating
  it in MLCommons terms is more defensible than an internal
  benchmark.
- **CNCF project lifecycle guidelines (Sandbox / Incubating /
  Graduated)** —
  <https://www.cncf.io/project-lifecycle-guidelines/> — the
  widely used shorthand for OSS-adoption timing on §2.3's
  reference-implementation planning.
- **Linux Foundation project charters** —
  <https://www.linuxfoundation.org/projects> — the umbrella
  entry point for governance charters that §2.3's body-
  selection matrix scores against.
- **Creative Commons licences** —
  <https://creativecommons.org/share-your-work/cclicenses/> —
  the canonical licence family for the §2.2 republication
  posture; the CC-BY vs CC-BY-SA vs CC-BY-NC decision has
  downstream coalition consequences and must be made.
- **Open Source Initiative — approved licences** —
  <https://opensource.org/licenses/> — the canonical registry
  of OSI-approved licences for reference implementations
  produced under §2.3.
- **IETF IPR Policy — BCP 78 / RFC 5378** —
  <https://www.rfc-editor.org/rfc/rfc5378> and
  **BCP 79 / RFC 8179** —
  <https://www.rfc-editor.org/rfc/rfc8179> — the IETF policy
  the standards-contribution plan must be signed off against
  where IETF is on the selected list.
- **W3C Patent Policy** —
  <https://www.w3.org/policies/patent-policy/> — the analogous
  policy at W3C.
- **Apache Contributor License Agreement (ICLA / CCLA)** —
  <https://www.apache.org/licenses/contributor-agreements.html>
  — where reference implementations or contributions land in
  Apache Software Foundation projects, the CLA path §2.3
  documents.
- **ACM SIGSOFT and IEEE Software** —
  <https://www.sigsoft.org/> and
  <https://publications.computer.org/software-magazine/> —
  archetypal Tier 1 / Tier 2 venues for the software
  engineering discipline; anchor for the tier definitions in
  §2.2. Discipline-specific analogues (SIGCOMM, SIGKDD,
  SIGMOD, USENIX ATC / OSDI / NSDI, ICML, NeurIPS) are the
  anchors where the thesis sits in those areas.
- **ACM Digital Library — Author Rights** —
  <https://authors.acm.org/author-services/author-rights> —
  the reference for author-retained rights and republication
  in ACM venues; the analogous IEEE and Springer policies
  should be substituted where the thesis targets those
  publishers.

### Regulatory and disclosure references

Distinction-level submissions from firms with public-market
exposure, regulated-industry exposure, or material advisory-
board activity cite these directly rather than paraphrase them.
The correct set depends on the employer's jurisdictions and
industry; the anchors below are the entry points most commonly
cited for US-domiciled programs.

- **US SEC — Regulation FD (Fair Disclosure)** —
  <https://www.sec.gov/rules/final/33-7881.htm> — governs
  selective disclosure of material information by
  public-company employees; §2.4's conflicts register and
  employer-sign-off threshold anchor here for public-company
  programs.
- **US SEC — Insider Trading rules (Rule 10b-5 and 10b5-1)** —
  <https://www.sec.gov/rules/final/33-8124.htm> — anchor for
  the recusal condition in §2.4 where the author holds equity
  in firms whose valuations may be affected by public
  positions.
- **NIST AI Safety Institute Consortium** —
  <https://www.nist.gov/artificial-intelligence/artificial-intelligence-safety-institute> —
  reference for AI-safety-adjacent public positions in
  US-domiciled programs.

<!-- Note: for programs whose employer domiciles include the EU, UK, or specific regulated jurisdictions (financial services, healthcare, aviation), learners should add the corresponding regulatory anchors — e.g., Solvency II, PRA supervisory statements, HL7, EASA. The exact set depends on the paired brief's scenario. -->

Version pins, article references, and internal-policy mappings
should be added by the learner when defending the submission
inside a specific organization; the URLs above are the
canonical entry points, but the exact clause a program element
maps to depends on the regulatory and industry context.
