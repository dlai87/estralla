# SOLUTION — project-04-ma-integration

> Read this *after* attempting the capstone deliverables. Like
> `project-01-enterprise-platform`, `project-02-technology-roadmap`,
> and `project-03-governance-framework`, this is a principal-architect
> track project: the solution is a rubric plus a worked structural
> template, not a runnable system. If you are looking for runnable
> platform artifacts, they live in the architect and senior-architect
> tracks; if you are looking for the governance framework the
> integration *uses* rather than redesigns, that lives in
> `project-03`.

The paired learner brief for this capstone lives in the sibling
learning repository at
[`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/README.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/README.md),
with supporting
[`requirements.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/requirements.md),
[`architecture.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/architecture.md),
[`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/rubric.md),
[`STEP_BY_STEP.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/STEP_BY_STEP.md),
and
[`deliverables/README.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/deliverables/README.md).
The brief frames the capstone as the **Argent Health ← Lumen Bio
Intelligence** integration: a publicly traded ~$9.8B revenue
health-tech acquirer buying a 240-employee, ~$140M ARR clinical
decision-support AI company for $620M (cash + earn-out), where
the Group CEO has publicly committed that Lumen's products will
be integrated into Argent's healthcare cloud within 18 months,
with **no revenue interruption, no regulatory excursion (HIPAA,
FDA SaMD, HITRUST), and ≥ 75% of Lumen's senior ML talent
retained at 12 months**, and where the board has been told the
integration will produce **$42M/yr run-rate cost synergy by
month 24** and unlock a **$180M/yr revenue synergy** thesis.

The learner portfolio is ten graded artifacts
([D1 integration architecture vision](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/deliverables/README.md)
through D10 board Audit Committee pack) scored against a
nine-dimension rubric
([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/rubric.md)):
integration architecture vision and pattern fitness (20%), DD
rigor (15%), 90-day plan executability (10%), 18-month roadmap
with abandonment criteria (15%), system-of-record decisions
defensibility (10%), regulatory continuity (10%), cultural
integration and talent retention (10%), synergy realization
credibility (5%), and board / Audit Committee communication
(5%). Pass ≥ 70% overall with no dimension below 50%;
distinction ≥ 85% with no dimension below 70%.

The five-block strategic package below is the **principal-track
spine** — the integration-architecture object a peer principal
integration architect (or a simulated IMO steering + board
Audit Committee panel) would grade before reading any of the
D1–D10 depth artifacts. Every generic gate, KPI, pattern
selection, and common mistake in this SOLUTION maps directly to
one or more of D1–D10; §4.4 gives the mapping. The two artifacts
are designed to compose: the sibling brief supplies the concrete
Argent / Lumen numbers, deliverable list, and rubric weights the
learner submits against; this SOLUTION supplies the shape and
grading altitude those specifics instantiate. Neither overrides
the other — a learner submission is expected to satisfy both.

## 1. Solution overview

The `project-04-ma-integration` capstone asks the learner to
produce the **integration-architecture object a principal
integration architect would defend to the CTO, CFO, CISO, CMO,
Lumen founder, IMO steering, and board Audit Committee** for
an acquisition whose deal thesis rests on retaining a small
cohort of world-class ML talent inside a regulated (HIPAA / FDA
SaMD / HITRUST) health-tech acquirer, on hitting a public
18-month integration deadline set by an earnings call, and on
delivering a specific run-rate cost synergy that the CFO can
re-derive from a lever model. It is the **brownfield sibling**
of the other three capstones in the track: where `project-01`
grades the *strategic package* for the platform Argent already
has, `project-02` grades the *roadmap artifact* that would
otherwise plan the next three years, and `project-03` grades
the *decision-making system* that produces both, `project-04`
grades the *integration itself* — the pre-close due-diligence
memo, the Day-1 readiness gate, the 90-day plan, the 18-month
wave roadmap, the system-of-record register, the pattern
playbook, and the cultural-and-regulatory continuity design —
as its own object, at the altitude a board Audit Committee
grades before the next acquisition is signed.

The capstone pulls in material from every module the principal
track presently exercises and two integration-specific modules
that the brief names as prerequisites:

- from `mod-605-tech-debt-modernization` — the pattern
  landscape (strangler fig, anti-corruption layer,
  branch-by-abstraction, parallel-run, dark launch) and the
  *sequencing-by-blast-radius* discipline that make an 18-month
  wave plan survive contact with a regulated business (see
  [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md));
- from `mod-604-stakeholder-coalition` — the coalition
  mechanics under acquisition stress (five internal
  stakeholder groups plus one external counter-stakeholder,
  Lumen), which are the conditions under which the retention
  design in §2.4 either works or does not;
- from `mod-601-org-wide-architecture` — the altitude at which
  standards, invariants, and system-of-record decisions land;
- from `mod-603-multi-year-investment` — the FinOps and
  capital-allocation discipline that turns the synergy claim
  in §2.5 into a lever model the CFO will not embarrass in
  Q3;
- from `mod-608-ma-integration` and `mod-609-due-diligence`
  (both prerequisites in the brief) — the M&A IT integration
  playbook and the tech / security / architecture DD
  frameworks respectively. Where a solutions counterpart for
  those modules does not yet exist in this repo, the five
  blocks below encode the material the capstone actually
  grades against; the block layout matches the standard IMO
  workstream taxonomy.

A passing submission is not one artifact. It is an **integration
package** of five short, mutually consistent design blocks —
pre-close due diligence, 90-day operational plan, system-of-
record decisions with pattern selection, regulatory-and-cultural
continuity, and 18-month roadmap with synergy and board comms —
that together let a peer principal integration architect (a) see
that the pre-close memo actually distinguishes blockers from
material findings from monitors, (b) trace every commitment back
to a requirement ID in the paired brief's `requirements.md`
and to a named workstream owner, (c) see the reversibility
window on every cutover and the abandonment criterion on every
wave, (d) find the "Lumen wins" system-of-record decision that
prevents the plan from reading as colonization, and (e) confirm
that the $42M synergy claim reconciles lever-by-lever to
something a CFO could defend in the Q4 board meeting.
Coherence across the package is the primary grading dimension;
depth in any single block is secondary.

### What the deliverable is *not*

- Not a redesign of Argent's enterprise AI platform. Argent's
  EAIP-equivalent is the object of
  [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md);
  the integration *consumes* what Argent already has and
  decides how Lumen fits, it does not draw the platform.
- Not a technology roadmap of Argent's next three years.
  Argent's forward roadmap is `project-02`'s object; the
  integration produces the 18-month wave plan whose inputs
  are Lumen's stack and whose outputs feed the forward
  roadmap. Any position on capabilities Argent would build
  regardless of the acquisition is out of scope.
- Not a governance-framework redesign. Argent's ARBs, ADR
  process, exception process, and technology radar are the
  object of
  [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md);
  the integration *uses* Argent's governance — hooking Lumen
  workloads into existing ARBs, filing integration ADRs
  against Argent's template — it does not redesign it.
- Not a commercial or legal integration. Sales-territory
  realignment, product-roadmap merger, HR comp / equity
  restructuring, and Lumen customer contract renegotiation
  belong to their own workstreams; the integration architect
  *inputs* to them and does not own them. See paired-brief
  `requirements.md` §7 for the explicit non-requirements list.
- Not runnable software. If the submission contains
  Terraform, Helm, application code, or migration scripts,
  the learner has mistaken the altitude. The one exception is
  the pattern playbook in D6 and the state-machine and
  process specifications in D3, D5, D8 — those are
  statically-valid design artifacts (state diagrams, decision
  trees, cutover sequence diagrams, DFCR / SaMD change-control
  workflow definitions) and are in scope precisely because
  they demonstrate the automation the integration depends on.
- Not an M&A playbook in general. The playbook is graded on
  fit to *this* acquisition — HIPAA-scoped, FDA-SaMD-scoped,
  GCP-native seller into an AWS-native acquirer, small ML
  talent cohort as the deal-value lever, 18-month public
  deadline. A generic Bain / McKinsey M&A IT integration deck
  copied over without instantiation grades in the
  half-credit band on dimensions 1, 4, and 5.

### What "M&A integration" means for grading

For this project, "integration" is the load-bearing
architectural work of merging a smaller, technically-mature
acquiree into a larger, regulated acquirer without breaking
what makes the acquiree valuable. The framework is graded first
on whether it would keep the FDA SaMD clearance intact, keep
the 8 named ML scientists at their desks, and produce something
close to the promised synergy — not on how thorough the DD
memo reads in isolation. A plan that would work at a scale where
seller and acquirer are the same size (merger of equals) is
under-designed for Argent–Lumen; a plan that would work at
$50B-plus mega-deal scale (dedicated IMO of 200+, dozens of
workstreams, multi-year integration budget in the hundreds of
millions) is over-designed. Submissions that make an explicit
note of what would change at the smaller-acqui-hire (say,
20-employee tuck-in) and at the mega-deal scales grade above
ones that assume a universal answer.

The single principle that reorders everything else in this
capstone is **reversibility**: the paired brief's
`architecture.md` §1 ranks regulatory continuity, customer
continuity, and talent retention above architectural
coherence; §6 prohibits big-bang cutovers on cross-cloud,
customer-facing, and SaMD-touching services; §11 gates every
wave on rollback drills within 30 days. A submission that
optimizes for architectural elegance at the cost of a rollback
window has misjudged the altitude and is likely to grade in
the failing band on dimensions 1 and 4.

## 2. Worked answer or implementation

The package below is the shape a strong submission takes.
Titles and section counts should match; wording is the
learner's. Each block anchors to the paired brief's D1–D10
artifact list (§4.4 maps them cell-by-cell). All Argent /
Lumen numbers below are taken from the paired brief and are
clearly-labeled local exercise context; the *shape* of each
block is what the reader is expected to reuse for a future
acquisition.

### 2.1 The pre-close due-diligence memo (~4 pages + a findings log + a cost-of-rebuild worksheet)

Two disciplines braided together: **the artifact** (a DD memo
whose executive summary a CTO can act on in one read) and
**the mechanism** (a findings log with per-item
categorization + a Day-30 confirmation plan for every
unknown that could re-baseline the integration).

**Memo shape** (matches paired brief `architecture.md` §3;
see `deliverables/d02-due-diligence/`): a one-page executive
summary that opens with a deal recommendation
(**Proceed / Proceed-with-conditions / Escalate**), then the
top-5 material findings in one sentence each, then the top-5
architectural risks in one sentence each. Everything past
page 2 is evidence.

**Findings log** as a checked-in CSV. Every finding lands in
exactly one of four buckets (paired-brief `architecture.md`
§3.2):

| Bucket | Definition | Default action | Named owner role |
|---|---|---|---|
| Blocker | If true at close, deal should not proceed at agreed terms | Escalate to CTO + M&A lead; price renegotiation conversation | CTO |
| Material | Significant integration cost or risk; deal proceeds but plan must account | Quantify cost; reflect in D4 roadmap; named in steering | IMO Technology co-chair (you) |
| Monitor | Worth knowing; small impact; may become material later | Log; track through Day-30 confirmation | Regulatory Affairs Liaison / SRE lead |
| Resolved | Initial concern proved unfounded on further evidence | Document for future DD pattern improvement | DD analyst |

Rubric hard check: ≥ 15 findings, categorized, each with an
action owner. A memo with ten findings, or with fifteen
findings but no owners, caps dimension 2 at half.

**Unknowns bounded by Day-30 confirmation activities.** The
paired brief `architecture.md` §3.3 names five categories of
question the seller cannot answer pre-close: real code
quality vs. the diagrams, real bus-factor, real cloud spend
vs. disclosed, the 8 ML scientists' actual stay / leave
intent, and hidden internal-tooling dependencies. For each,
name the Day-30 activity, the evidence type, the owner, and
the trigger that would re-baseline the plan. A distinction-
level memo carries at least one Day-30 activity whose
negative outcome would credibly pause Wave 1; a memo whose
Day-30 activities can only ratify what is already assumed is
performing DD as ceremony.

**Cost-of-rebuild estimate.** For the top ten Lumen
capabilities on which the deal thesis depends (biomedical
LLM training pipeline, RAG over curated medical literature,
FDA-SaMD-cleared clinical decision modules, EHR integration
front door, Vertex-AI-based serving stack, etc.), estimate
what Argent would spend and how many months it would take to
rebuild from scratch (engineer-years × loaded cost + FDA
submission cycle time for SaMD components). If total
rebuild is under, say, $400M and 24 months, the deal has a
speed-and-optionality thesis, not a synergy one; the memo
must name this explicitly. Rubric hard check: the CFO can
re-derive the estimate.

**Executive summary — deal recommendation.** Three
paragraphs (thesis-supporting findings; material risks;
recommendation). The recommendation is a **position**, not
"further study required." A DD memo whose recommendation is
"we recommend continued analysis" has produced no
architectural signal and grades in the lower band regardless
of the finding count.

### 2.2 The 90-day operational plan (~2 pages + the Day-1 checklist + the Day-30 stabilization report template + the Day-90 ratification gate)

Three artifacts, one nervous system.

**Day-1 readiness checklist.** ≥ 25 items, each with a named
owner role and a pass / fail criterion, grouped by workstream
(paired brief `architecture.md` §4). The load-bearing
discipline is that **no item on the Day-1 checklist is an
architectural change**. The following are Day-1 items;
anything else is a Day-30 item or later:

- Identity: Lumen employees can authenticate to Argent Okta
  (owner: Argent IT; pass = successful test login from ≥ 5
  Lumen employees pre-arranged for Day 0). Lumen's own IdP
  continues to serve Lumen-system access unchanged.
- Communications: joint CEO + founder all-hands within 4h of
  close (owner: Corporate Comms); joint customer message
  within 4h (owner: Marketing + Lumen CS lead); joint partner
  message within 24h (owner: BD).
- BAAs (HIPAA): Lumen → Argent BAA in effect per closing
  conditions; all subcontractor BAAs confirmed valid through
  Day 1 (owner: Argent Privacy Office + Lumen General
  Counsel; pass = signed BAA chain in the record system).
- Financial controls: Lumen spending authorities remapped to
  Argent's signoff thresholds (owner: Argent Finance); Argent
  CFO has read-only access to Lumen financial systems (owner:
  Argent Finance; pass = confirmed logins).
- On-call paging: Lumen on-call unchanged and tested (owner:
  Lumen SRE lead; pass = successful test page Day 0). Argent
  SRE remains responsible for Argent-side incidents; **cross-
  paging is deliberately not enabled Day 1** — cross-paging is
  a month-6 gate under IR-16.
- Customer-facing systems: **zero change**. All Lumen
  production models continue to serve from Lumen's existing
  GCP infrastructure (owner: Lumen SRE; pass = SLO monitors
  unchanged).
- IMO governance: charter signed; Technology workstream
  co-chairs (you + Lumen CTO) named; bi-weekly steering
  cadence booked through Day 90 (owner: IMO chief; pass =
  calendar invites accepted).
- Regulatory-affairs liaison: named individual embedded in
  the IMO Technology workstream Day 1 (owner: CCO; pass =
  RAL on the workstream roster).
- Risk register opened with Day-1 risks logged; owner per
  risk named (owner: IMO PMO).

Rubric hard checks (paired brief §rubric dimension 3): ≥ 25
items; no architectural change items; every item has an
owner and a pass criterion.

**Day-1 must-not-haves** are as load-bearing as the must-haves
(paired brief `architecture.md` §4.2). Name them explicitly:
no architectural change, no service migration, no cloud
migration, no identity unification of the customer-facing
IdP, no comp / equity adjustment communicated to Lumen
employees (that is HR-led on a separate cadence), no public
Argent commitment to a specific integration outcome that the
plan has not confirmed. A Day-1 plan that has must-haves but
does not enumerate must-not-haves has not internalized that
Day 1 is a calendar event with checklist precision.

**Day-30 stabilization.** The rule for Day 1 → Day 30 is
**no architectural change** — the 30-day window is for post-
close DD confirmation activities from §2.1's memo, for
identity provisioning (Lumen employees receive Argent Okta
identities within 30 days per IR-5), and for surfacing the
reality of Lumen's stack against the data-room version. Named
milestones:

- All Day-30 DD confirmation activities from §2.1 complete
  or explicitly escalated; findings log updated.
- Lumen employees provisioned on Argent Okta (IR-5); Lumen
  IdP unchanged for system access.
- Post-close baseline architecture diagrams updated against
  observed reality; deltas from data-room version logged as
  ADR-eligible items.
- Regulatory Affairs Liaison embedded and holding weekly
  cadence with Lumen SaMD lead.
- First integration retrospective with Lumen team held;
  outcomes surfaced to IMO (TR-5).
- Quick-win synergy scan complete; ≥ $4M run-rate identified
  and drafted into D9's model (SR-2).

A Day-30 stabilization report that names "migrated identity,
consolidated observability, decommissioned Lumen Vault" has
mistaken Day 30 for Day 180 and grades in the failing band
on rubric dimension 3.

**Day-90 plan ratification gate.** A **gate**, not a
formality. Enter with D3 (the 90-day report), D4 (draft
18-month roadmap), D5 (draft SoR register), D6 (draft
patterns playbook), D9 (draft synergy model), and D7 (draft
retention design). Ratification requires unanimous signoff
from IMO Technology + Steering + board Audit Committee
chair. Named ratification criteria:

- All 15 SoR decisions from D5 with a defended position
  (not "provisional") — per IR-9.
- 8–12 cutovers with pattern + reversibility window +
  abandonment criterion (D6) — per IR-11.
- Cross-cloud decision (D6's Option A / B / C / D analysis)
  with the chosen option defended.
- Synergy lever model (D9) reconciling to $42M ±15% per SR-1.
- Retention design (D7) for the 8 named ML scientists —
  per-person, not "competitive comp."
- Signoff from CTO, CFO, CISO, CMO, and the Lumen founder or
  her designated deputy — the last of these is the
  distinction-bar signal.

A ratification gate that would pass on documents alone —
without the Lumen founder's signal — is a gate the coalition
does not believe in.

### 2.3 The system-of-record decisions and the integration patterns playbook (~4 pages + a 15-row SoR register + an 8-to-12-cutover playbook + the cross-cloud analysis)

Two artifacts, one architectural spine.

**The SoR register** (paired brief `architecture.md` §5;
`deliverables/d05-sor-decisions/`). One row per shared concern
(15 rows target). Every row carries: Argent's current system,
Lumen's current system, chosen system-of-record, migration
plan, reversibility (Low / Medium / High), regulatory
implications, owner role, and a one-line rationale. The
five-dimension framework (paired brief `architecture.md` §5.2)
— capability fit, regulatory weight, migration cost, talent
signal, reversibility — is applied per row, not per section.

The single load-bearing feature of this register is the
existence of **at least one "Lumen wins" row** — a system on
which Argent's approach is deliberately displaced by Lumen's
(IR-10). The paired brief pre-identifies three candidates
(vector retrieval → Pinecone; MRM for SaMD workloads →
Lumen's custom module; internal LLM hosting → Lumen's
Triton-based pattern). A submission that files every row
against Argent's system has produced a *colonization* plan;
the Lumen team detects it inside Day 60, retention drops
below TR-1's floor, and the deal thesis unwinds. Rubric hard
check: ≥ 1 "Lumen wins" row with technical, strategic, and
cultural rationale.

**The patterns playbook** (paired brief `architecture.md` §6;
`deliverables/d06-patterns-playbook/`). 8–12 concrete
cutovers, one file per cutover under
`d06-patterns-playbook/cutovers/`. Every cutover carries a
pattern, a reversibility window, an abandonment criterion,
and a regulatory implication. The pattern landscape:

| Pattern | Use when | Do not use when | Reversibility window | Reference |
|---|---|---|---|---|
| Strangler fig | Traffic can be routed at a request boundary; new system can be built independently | The abstraction boundary is inside a hot loop or a data-plane critical section | ≥ 30 days for customer-facing; ≥ 90 days for SaMD-touching | [Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html) |
| Anti-corruption layer | Two systems must interoperate but their domain models are irreconcilable in the near term | Both systems are already speaking a shared canonical vocabulary; the ACL becomes an accidental system-of-record | Persistent (the ACL is designed to outlive the migration) | Evans, *Domain-Driven Design* |
| Parallel-run | You need to prove the new system produces the same output as the old, especially for regulated workloads | You cannot compare outputs deterministically; comparison would leak PHI | ≥ 90 days for FDA-SaMD-cleared; ≥ 30 days for HIPAA-touching | Newman, *Monolith to Microservices* — "parallel run" pattern |
| Branch-by-abstraction | A shared abstraction can be introduced behind which implementations are swapped | The systems have no natural shared abstraction; adding one increases complexity for no gain | Bounded by the ≤ 12-month window before abstraction rot | Humble & Farley, *Continuous Delivery* |
| Dark launch | You want to observe a new code path in production without user impact | Observed behavior is not comparable to real behavior (bot traffic, replay data) | ≤ 30 days before commitment decision | Newman, *Building Microservices* 2nd ed |
| Big-bang with reversibility window | Clean cutover is cheaper and lower-risk *and* rollback is testable in under 24h | The cutover touches a cross-cloud, customer-facing, or SaMD-touching surface | ≥ 24h for low-risk, ≥ 30 days for anything touching a validated system | Feathers, *Working Effectively with Legacy Code* (safe-refactor patterns) |

Rubric hard check (dimension 1 and dimension 4): **no big-bang
on cross-cloud, customer-facing, or SaMD-touching cutovers**.
A submission that files the SaMD serving cutover as big-bang
scores zero on that row and caps dimension 1 at 13/20 (the
"vision as feature list" band).

Sample cutover coverage (matching paired brief `deliverables/README.md` §D6):

- Identity cutover (Lumen → Okta) — dark launch + parallel
  auth for 30 days → cutover.
- Secrets cutover (Lumen Vault → Argent Vault federated) —
  ACL + strangler; single-source by month 9.
- Observability cutover for non-LLM metrics (Grafana → Datadog)
  — strangler fig; LangSmith retained for LLM eval.
- Model registry ACL (Lumen registry ↔ Argent MLflow surface)
  — 18-month persistent ACL.
- SaMD model serving parallel-run (Triton ↔ KServe) —
  90-day parallel-run gated on ≤ 0.1% output divergence on a
  named eval suite.
- Training orchestration (Kubeflow Pipelines → Argo) —
  branch-by-abstraction over 12 months.
- Backstage merge (Argent + Lumen fork) — big-bang with 30-day
  reversibility.
- CMDB integration (Lumen assets into ServiceNow) — big-bang
  with 24h reversibility.
- FinOps extension (Vantage extended to GCP) — strangler;
  low-risk.
- Cross-cloud egress optimization for ongoing dual-run —
  ongoing, not a cutover.
- Customer-facing EHR API strangler fig — 12-month traffic
  shift with per-endpoint rollback.
- Internal LLM hosting unification (Argent → Lumen's pattern)
  — dark launch of Argent-side gateway; adopt Lumen's Triton
  pattern; migrate Argent workloads over 12 months.

**The cross-cloud analysis** (paired brief `architecture.md` §7;
`deliverables/d06-patterns-playbook/cross-cloud-analysis.md`).
Four options (A: migrate GCP → AWS; B: keep dual permanently;
C: strangler fig 24–36 months; D: migrate non-SaMD only, SaMD
stays GCP indefinitely with re-evaluation at month 24). Every
option scored on five dimensions (18-month TCO, reversibility,
talent risk, regulatory risk, coalition risk). The **provisional
recommendation is Option D** (paired brief §7.2). Rationale:
SaMD disruption is the highest regulatory risk under RR-2 and
CON-5; cross-cloud migration of cleared modules triggers 510(k)
supplement determination and burns FDA-review time the deal
thesis does not have; non-SaMD workloads are cleaner to
migrate; retention of the SaMD engineers on GCP tooling
through the founder earn-out window (M24) protects TR-3. The
re-evaluation gate at month 24 preserves the option to revisit
after the earn-out completes. **A submission that avoids the
cross-cloud position** — that leaves it "TBD" or "to be
decided by IMO" — has left the largest single decision on the
table and grades in the failing band on rubric dimension 1.

**The cutover file template** (used per cutover under `d06-patterns-playbook/cutovers/NN-name.md`) contains: pattern
choice + rationale (≥ 1 paragraph); scope in / out;
reversibility window with the specific rollback mechanism
(traffic reroute, snapshot restore, feature-flag flip);
abandonment criterion tied to a named leading indicator;
regulatory implications with owner (RAL for anything SaMD-
touching; Privacy Office for anything HIPAA-touching);
dependencies on other cutovers (SoR-decision dependency);
estimated effort in FTE-quarter; and a signoff line for
Argent + Lumen co-leads. A cutover file whose reversibility
line reads "we would roll back" without the mechanism is not
a plan; it is a wish.

### 2.4 The regulatory-continuity and cultural-integration block (~3 pages + the DFCR process + the SaMD change-control decision tree + the HITRUST recertification path + the 8 named scientist profiles + the founder retention design)

Two disciplines that fail together and must be designed
together: regulatory continuity (which fails as a public
incident) and cultural integration (which fails as a
resignation letter).

**HIPAA scope management** (paired brief `architecture.md` §9.1;
`deliverables/d08-regulatory/hipaa-dfcr-process.md`). The
load-bearing artifact is a **Data Flow Change Request (DFCR)
process** — a lightweight 1-page form that fires every time a
new data flow between Lumen and Argent systems is proposed.
Routing: Privacy Office (Argent CCO function) + CISO Designate.
Decision SLA: **5 business days**. Outcome: documented in the
BAA chain as an amendment if scope expands, or logged as
in-scope with no amendment required. The intent is not to
slow integration; it is to make every scope change visible to
the auditor at month 12. Named cadence for the BAA chain
audit itself: Day 30, Month 6, Month 12 (paired brief IR-7).

**FDA SaMD lifecycle** (paired brief `architecture.md` §9.2;
`deliverables/d08-regulatory/fda-samd-decision-tree.md`).
Two Lumen modules are FDA-cleared as Class II SaMD; two more
are in submission. The load-bearing artifact is a **substantial-
change decision tree** — a flowchart whose leaves are one of
{no submission required; letter-to-file; 510(k) supplement
submission; new 510(k) submission}. Every integration action
that touches a validated system routes through the tree with
the Regulatory Affairs Liaison as decision owner; every leaf
is a documented decision retained in the SaMD record for ≥ 7
years per validation practice. The tree is anchored on FDA's
"Deciding When to Submit a 510(k) for a Software Change to an
Existing Device" guidance (see §6 references) — a submission
that reconstructs a decision tree from first principles
without citing the guidance risks landing on a shape a
regulator would not recognize.

**HITRUST recertification** (paired brief `architecture.md` §9.3;
`deliverables/d08-regulatory/hitrust-recertification.md`).
Two positions to defend, both are legitimate:

- Option 1: Lumen recertifies under new ownership at the
  next scheduled cycle (target: month 9–11). Cleanest
  continuity; minimal scope reassessment; retains Lumen's
  existing assessor and evidence trail.
- Option 2: Argent extends its existing HITRUST scope to
  Lumen workloads. Requires reassessment of scope; risk of
  surfacing new gaps; forces early consolidation.

The paired brief recommends Option 1 for the first cycle and
Option 2 at the next renewal (month 24), when the integration
is mature. The distinction bar is a submission that names
the trigger under which the recommendation flips (e.g., "if
BAA chain audit at Month 6 surfaces material gaps against
Argent's HITRUST scope, flip to Option 2 for the next
cycle") rather than treating the recommendation as
irrevocable.

**SOC 2 Type II continuity** (paired brief `architecture.md` §9.4).
Lumen's SOC 2 reports continue at the next renewal cycle
without scope reduction (paired brief RR-4). Argent's SOC 2
scope extends to Lumen workloads by month 12 (target). Six-to-
twelve months of overlapping reports is an accepted cost of
integration and named in D9's synergy sensitivity.

**Regulatory Affairs Liaison role.** A full-time named
individual embedded in the IMO Technology workstream for the
first 12 months (paired brief `architecture.md` §9.2). This
role is the single point of accountability for every SaMD
change-control decision, every DFCR routing, and every
HITRUST evidence request during the recertification cycle. A
regulatory continuity plan that treats regulatory as a matrix
of cross-functional responsibilities without a single named
role fails silently the first time a substantial change
determination is disputed.

**Cultural integration — the 8 named ML scientists** (paired
brief `architecture.md` §8.1;
`deliverables/d07-cultural-talent/8-scientists-profiles.md`).
The retention design is *architecture-side*, not comp-side.
For each of the 8 named scientists (invent role-consistent
initials or names; the discipline is in the profiling), name:

- Role and unique contribution to model performance (which
  models, which capabilities). Not "senior ML engineer" —
  "owns the biomedical-literature RAG retrieval quality
  pipeline; a departure would degrade the two cleared
  modules' retrieval quality by a materially measurable
  margin on the internal eval suite (the specific
  percentage is a Day-30 confirmation activity from §2.1,
  not a pre-close estimate)."
- Stage of career (early / mid / senior / staff) and
  inferred motivation (research scientist vs. founding
  engineer vs. product engineer vs. entrepreneur-in-
  training).
- Earn-out / equity exposure (categorical, not a specific
  dollar figure — the specific number is HR / M&A legal's
  domain).
- Retention design across four architecture-side levers:
  - **Toolchain continuity** — do not force this person off
    HuggingFace / PyTorch / GCP / their preferred serving
    stack within month 12. See paired brief §5.1 row 7 and
    row 13 — the "Lumen wins" SoR decisions on vector
    retrieval and LLM hosting are simultaneously *retention
    moves*.
  - **Decision authority** — a named seat on the relevant
    Argent ARB (from `project-03`'s framework) so their
    architectural opinions still count.
  - **Identity** — integration into Argent's chapter / guild
    structure that avoids the "acquired team" ghetto.
  - **Visible respect** — a "Lumen wins" SoR decision with
    their name on the ADR captures the retention effect that
    HR comp cannot buy.

Rubric hard check (dimension 7): 8 distinct designs, not a
template applied 8 times. A submission whose 8 profiles look
identical has produced a comp memo, not a retention design.

**Cultural integration — broader cohort** (paired brief
`architecture.md` §8.2). For the ~105 broader ML / AI /
platform engineers, name four architecture-side mechanisms:
joint working groups per workstream from month 3 (Argent
co-lead + Lumen co-lead, paired brief TR-4); monthly
retrospectives for the first 6 months, quarterly thereafter
(TR-5); internal-mobility opportunities (Lumen engineers can
join Argent platform team and vice versa without formal
requalification); promotion-path visibility (leveling
exercise transparent, both sides mapped). Board-level
commitment: no mass layoff in the first 12 months.

**Lumen founder retention design** (paired brief §7 SR-3 and
§8; `deliverables/d07-cultural-talent/founder-retention-design.md`).
The founder is Chief Scientific Officer post-close with a
24-month earn-out. The architecture-side retention design is
role definition (what she decides, what she recommends, what
she does not decide), earn-out alignment with technical
milestones (specifically, alignment with retention thresholds
under TR-1 and TR-2), a visible ARB seat, and a career
runway past month 24. **A founder retention design whose
only lever is the earn-out has misjudged the retention
mechanism** — founders leave when the work stops being
theirs, not when the equity vests.

**Cultural anti-patterns** (paired brief `architecture.md`
§8.3). Name four with a design response to each:

1. HuggingFace vs. enterprise platform — Lumen engineers
   default to HF Transformers + PyTorch + custom serving;
   Argent's standards are KServe + MLflow. Response: the
   "Lumen wins" SoR decisions on LLM hosting and MRM;
   toolchain continuity through month 12; the
   branch-by-abstraction migration path over 12 months for
   workloads that must consolidate.
2. GCP vs. AWS familiarity — the multi-month learning curve
   frustrates senior people. Response: Option D on the cross-
   cloud question (SaMD workloads stay GCP indefinitely); a
   voluntary AWS enablement program funded from the
   integration budget, not a mandate.
3. Acquisition fatigue — 240 employees just went through a
   major life event; a 20–30% productivity drop in the first
   6 months is expected. Response: named in D4's capacity
   plan (30 FTE Lumen × 0.7–0.8 utilization for months 1–6);
   surfaced in retrospectives; explicitly not treated as
   underperformance.
4. Argent-team NIH — Argent's platform team sees Lumen's
   tooling as "not invented here." Response: joint working
   groups with real technical engagement (not "you'll absorb
   them"); the "Lumen wins" SoR decisions publicly visible
   to Argent staff; a named Argent-side architect assigned to
   understand and adopt the "Lumen wins" systems.

### 2.5 The 18-month roadmap, the synergy model, and the board comms (~4 pages + a 6-wave roadmap + a lever model + the board Audit Committee deck)

The "does the integration work, and will it survive the
next four board meetings?" block.

**6-wave 18-month roadmap** (paired brief `architecture.md`
§2, §11; `deliverables/d04-18-month-roadmap/`). Six quarters,
one wave per quarter (with overlap). Every wave carries:
theme, scope (which SoR decisions land, which cutovers
execute), dependencies, capacity in FTE-quarter (total ≤ 90
FTE-quarter under CON-2's ≈ 38 FTE cap), and the four-
outcome gate:

| Outcome | Trigger | Action |
|---|---|---|
| Success | All named criteria met on time and on budget | Continue to next wave |
| Refine | ≤ 20% variance on time / budget / criteria | Continue with named adjustments; log to IMO |
| Pivot | 20–40% variance; a specific mid-wave input has invalidated a specific decision | Rewrite the next wave scope; steering signoff |
| Abandon | > 40% variance, or a leading indicator has fired (talent retention below TR-1 floor, SaMD substantial-change trigger, HIPAA scope excursion) | Pause the wave; steering re-baseline |

Rubric hard check (dimension 4): every wave has all four
outcomes named, and at least one wave carries an
**abandonment trigger the author would actually pull**. A
plan whose abandonment triggers no one on the IMO would
ever pull is not a plan with kill criteria; see paired brief
§5 common failure mode and
[`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
on "no exit criteria."

Sample wave shape (matching paired brief `architecture.md`
§2's W1–W6):

| Wave | Months | Theme | Cutovers landed | Regulatory milestone | Abandonment trigger |
|---|---|---|---|---|---|
| W1 | M1–M3 | Identity + secrets + observability foundation | Identity cutover; secrets ACL; observability strangler start | Day-30 DFCR process live; RAL embedded | < 6/8 named scientists retained OR HIPAA finding at Day 30 audit |
| W2 | M4–M6 | Model registry ACL + LLM gateway + FinOps extension | Model registry ACL live; LLM gateway dark launch; Vantage extended to GCP | HITRUST recert cycle initiated | Wave 1 abandonment trigger persists |
| W3 | M6–M9 | Training orchestration + GPU fleet + parallel-run start | Kubeflow → Argo branch-by-abstraction underway; SaMD parallel-run start | HITRUST recert underway | SaMD parallel-run divergence > 1% on eval suite |
| W4 | M9–M12 | Vector retrieval + Backstage merge + first SaMD parallel-run decision | Pinecone as Argent standard; Backstage merged; SaMD parallel-run decision recorded | HITRUST recert closes | > 3 of 8 named scientists departed OR founder departure |
| W5 | M12–M15 | Legacy Lumen-side decommissioning + reversibility drills | Decommission Lumen Backstage; consolidate observability | 12-month Board Audit review passes | Synergy run-rate < $22M annualized at M12 |
| W6 | M15–M18 | Cross-cloud question resolved for non-SaMD; open-question closure | Non-SaMD workloads migrated to AWS per Option D; SaMD workloads stay GCP | Argent SOC 2 scope extends to Lumen workloads | Cost-of-migration > 50% over budget |

**Capacity check.** Total capacity ≈ 38 FTE (8 Argent
platform + 30 Lumen platform per CON-2). Per-wave FTE-quarter
demand must fit; the roadmap is graded on the *sum being
buildable*, not on the elegance of the wave titles.

**Critical path.** Marked on a Mermaid Gantt
(`deliverables/d04-18-month-roadmap/gantt.mmd`): FDA SaMD
continuity is the constraint (nothing affecting cleared
modules can slip without 510(k) implication); HITRUST
recertification (month 9–11) is on critical path; Day-90
ratification is on critical path (synergy depends on it).
Regulatory events must be marked as **non-negotiable dates**,
not as workstream milestones.

**Synergy realization** (paired brief `architecture.md` §10;
`deliverables/d09-synergy/`). $42M / yr run-rate by month 24
per SR-1, lever-by-lever. Nine levers (paired brief §10 table):
GCP commitment renegotiation, AWS reservation extension,
SaaS consolidation, vendor renegotiation, headcount overlap
(G&A only under CON-2), internal vendor consolidation,
internal tooling absorption, cross-cloud egress reduction,
and cross-cloud egress cost during dual-run (a negative
lever). Every lever carries year-1 value, year-2 run-rate,
assumptions, dependency on integration milestones, and a
quarterly trajectory. Rubric hard check (dimension 8):
sensitivity on four variables — GCP early-termination
±50%, headcount overlap ±20%, cross-cloud migration timing
±3 months, vendor renegotiation ±30%. The CFO must be able
to re-derive $42M from the model without asking the author
what an assumption means; if a lever ties to a variable the
CFO cannot audit, that lever is not credible.

The **KPI + fitness-function set** (paired brief
`architecture.md` §14). Six fitness functions, reviewed
monthly for the first 6 months and quarterly thereafter:

- Continuity fitness — zero customer-facing SLA breaches
  attributable to integration. Owner: SRE lead. Cadence:
  weekly for first 3 months; monthly.
- Talent fitness — month-over-month retention rate for the
  8 named scientists (leading indicator) and the broader
  cohort (lagging). Intervention: trend deterioration for 2
  consecutive months triggers a founder + Chief Scientific
  Officer review. Owner: CTO + Lumen founder.
- Regulatory fitness — zero HIPAA breaches; zero
  substantial-change determinations triggered without plan;
  HITRUST recert on schedule. Intervention: any
  substantial-change trigger pauses the affected wave.
  Owner: RAL + CISO Designate.
- Synergy fitness — actual quarterly run-rate vs. plan. ±15%
  triggers IMO review; ±25% triggers steering escalation.
  Owner: CFO + IMO Finance.
- Reversibility fitness — quarterly rollback drill on the
  most recently migrated cutover; pass / fail recorded per
  IR-12. Owner: SRE lead + relevant cutover owner.
- Cultural fitness — monthly retrospective sentiment; joint
  working group attendance; promotion equity Argent vs.
  ex-Lumen. Intervention: a Lumen-side promotion-equity gap
  exceeding 15% triggers an HR + IMO review. Owner: CTO +
  HR.

Every fitness function fails to a **named intervention
path**, not to a monthly report. A fitness-function set that
would emit dashboards but not decisions is instrumentation
theater and grades in the half-credit band on dimensions 4
and 8.

**Board Audit Committee pack** (paired brief
`architecture.md` §11 gates; `deliverables/d10-board-pack/`).
≤ 30 slides. Named required slides:

1. Deal thesis recap in ≤ 3 slides — one memorable headline
   number ($42M synergy at M24 or $180M/yr revenue synergy;
   pick one, not both).
2. 90-day plan + Day-1 readiness summary — 3 slides.
3. 18-month roadmap by wave with critical path — 4 slides.
4. System-of-record decisions with "Lumen wins" highlighted
   — 3 slides.
5. Multi-cloud question and Option D resolution — 3 slides.
6. Regulatory continuity (HIPAA / FDA / HITRUST) — 3 slides.
7. Cultural integration + talent retention — 3 slides.
8. Synergy realization lever-by-lever — 3 slides.
9. **"What would make us re-baseline"** slide — the
   distinction bar. Explicit abandonment triggers named,
   with the CTO or CFO's name on each.
10. Backup material entry points — up to 4 slides.

**Three backup decks**, one per audience: CFO (synergy model
deep-dive), CISO (regulatory continuity detail), Lumen
founder (talent + cultural integration design; shared with
her ahead of the board meeting as courtesy). A pack whose
board slides are the union of the backup decks is missing
the synthesis; a pack whose board slides duplicate the
backup deck content is over-designed.

**Coalition moments — mapped per stakeholder group**
(consistent with the coalition mechanics in
[`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)):

- Board Audit Committee: quarterly cadence Day 90 onward;
  the "what would make us re-baseline" slide is the
  standing invitation to interrupt. Audit-chair pre-meeting
  signal is the leading indicator of coalition erosion
  (paired brief risk 12).
- Argent CTO (sponsor): monthly 1:1; the integration
  architecture reports up this line and is judged as a
  service to the IMO, not a parallel power center.
- CFO: quarterly synergy readout with the CFO-rederivable
  model; ±15% variance is the standing intervention
  threshold.
- CISO: monthly regulatory continuity readout; DFCR
  throughput and BAA chain audit dates are the reporting
  spine.
- Chief Medical Officer + CCO: FDA SaMD change-control log
  review at each substantial-change determination.
- Lumen founder: bi-weekly for the first 90 days, monthly
  after; the founder's countersignature on the D7
  retention design is the primary retention receipt for the
  board.
- Lumen CTO (workstream co-chair): standing weekly on the
  Technology workstream; the co-chair relationship is the
  visible symmetry that keeps the integration from reading
  as colonization.
- Argent platform team: monthly TR-4 joint working group
  review; a joint working group whose attendance from the
  Argent side drops below 70% is a leading indicator of NIH
  and is surfaced immediately.

**Meta-integration** — the amend-the-plan process. The
distinction bar. Named triggers for a formal re-baseline
(fitness-function failure per §2.5; TR-3 founder departure;
material FDA SaMD event), the amendment authority (IMO
Technology co-chairs escalate to Steering, which escalates
to the board Audit Committee), and a stage gate at month 6
(re-charter or absorb amendments). An integration plan
whose own amendment process is undesigned is a plan that
cannot survive the first fitness-function failure.

## 3. Validation steps

There is no build to run at this altitude. Validation is a
sequence of reviews the package must survive, adapted from
the sequences in
[`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md) §3,
[`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md) §3,
and
[`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md) §3,
specialized to the M&A-integration altitude.

1. **Requirement-traceability check.** Every requirement ID
   in the paired brief's `requirements.md` (IR-*, RR-*, TR-*,
   SR-*, CON-*, ASM-*) traces to at least one section of the
   package above. Requirements with no home are gaps;
   sections with no requirement are decoration.
2. **Internal consistency check.** Re-read the five blocks
   in order. Every commitment in the DD memo (§2.1) — a
   material finding, a Day-30 activity, a cost-of-rebuild
   assumption — appears in the 90-day plan (§2.2, D3), the
   SoR register (§2.3, D5), or the risk register (D4). Every
   SoR row (§2.3) has a cutover file (D6). Every cutover
   has a reversibility mechanism (not just a window) and an
   abandonment criterion tied to a leading indicator in §2.5.
   Every fitness function in §2.5 has a named intervention
   owner. Cells that fail any of these links are decorative
   — cut them or add the links.
3. **DD-to-plan traceability.** For each Blocker / Material
   finding in §2.1, name the D3 or D4 section that
   addresses it. A Material finding with no home in D3 / D4
   is decoration; a Blocker with no closure conversation
   before Day 0 is a deal-terms escalation the memo failed
   to trigger.
4. **Delegation audit.** For each of the 15 SoR rows in
   §2.3, name the delegation from IMO Technology to
   workstream owner. A register where IMO Technology co-
   chairs sign every row is not a register; it is a bottleneck.
5. **Leading-vs-lagging audit.** Count the fitness functions
   in §2.5 tagged **leading** (the ones whose failure would
   let you intervene before an outcome is unrecoverable).
   Target: ≥ 3 with named intervention rules. A plan whose
   fitness functions all fire on lagging indicators is a
   plan that only learns after the outcome is unrecoverable.
6. **Peer-principal cold read.** Give D1 (the integration
   vision) and D10 (the board pack) to a peer principal
   architect with no context. The
   [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md)
   test — the reader should be able to disagree with the
   design and still articulate the reasoning — applies here
   too. If they say "I cannot tell what would make you
   pause a wave," rewrite the abandonment triggers before
   submitting.
7. **Hostile-CFO read.** Read D9 as the CFO whose Q4 board
   meeting will feature the synergy variance conversation.
   Every lever should be re-derivable from a named
   assumption; every sensitivity should point back to a
   dependency in D4. If the CFO would ask "where is the
   $180M revenue synergy in your model" and the answer is
   "that is the commercial workstream's number," the
   boundary is defensible and should be stated on the slide;
   if the answer is "we did not model it," the pack has
   left revenue synergy uncovered where the board will
   look for it.
8. **Hostile-CMO read.** Read D8 as the Chief Medical
   Officer whose signature is on the FDA SaMD submissions.
   Every substantial-change decision tree leaf should be
   defensible against a regulator; every dual-run window
   should be defensible against a patient-safety review. If
   the CMO would push back on the parallel-run duration for
   SaMD-cleared modules (paired brief §13.5 sets 90 days;
   the distinction bar is the submission that names the
   trigger under which 90 days extends to 180), the plan
   has understood the regulatory altitude.
9. **Lumen-founder read.** Read D5 (SoR register) + D7
   (retention design) as the Lumen founder deciding whether
   to sign her deputy to the ratification gate. If she
   cannot find at least one "Lumen wins" decision that
   would let her tell her team "this integration will
   respect the work we did," the retention design has
   failed pre-close.
10. **Audit walkthrough dry run.** Read D8 (regulatory) +
    D2 (DD memo) + D3 (Day-30 audit cadence) as if you were
    an internal auditor with 45 CFR 160 / 162 / 164 (HIPAA
    Privacy + Security), FDA SaMD guidance, and HITRUST CSF
    in hand. Every "documented risk acceptance" surfaces in
    an audit-visible record? Every HIPAA-touching data flow
    is tied to a signed BAA? Every SaMD substantial-change
    determination is retained for ≥ 7 years? Gaps here are
    audit findings by month 12.
11. **Rollout-abandonment plausibility.** Read the 6-wave
    plan's Abandon column. Would you actually invoke it
    under the named trigger, or would you argue for one
    more quarter? A rollout whose abandon triggers no one
    would ever pull is a rollout with no kill criteria —
    see
    [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
    §"No exit criteria."
12. **Reversibility drill dry run.** For at least one Wave
    1 cutover, name the rollback command sequence and the
    responsible on-call runbook line. If the answer is "we
    would roll back," the reversibility is aspirational; if
    the answer is a named snapshot, a named traffic-shift
    rule, a named feature-flag flip, the reversibility is
    real.
13. **Meta-integration replay.** Assume the integration has
    been running for two quarters and one fitness function
    (talent) has failed twice. Does the meta-integration
    process (§2.5) let the plan revise, and does the
    revision leave the acquisition better off than the
    pre-plan baseline? A plan whose own amendment process
    is undesigned is a plan that cannot learn.
14. **Standards-legibility pass.** For every position that
    touches an area covered by an external standard (FDA
    SaMD guidance, HIPAA CFR references, HITRUST CSF,
    Fowler's strangler fig, Newman's parallel-run and
    ACL patterns, Humble & Farley's branch-by-abstraction,
    Sirower on synergy realization), confirm the position
    is stated in terms that standard would recognize. This
    costs little now and avoids audit-cycle retrofits
    later.

## 4. Rubric or review checklist

The checklist below is the principal-track spine and is
consistent with the learning brief's nine-dimension, 100-point
rubric
([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/rubric.md)):
integration architecture vision and pattern fitness (20%),
DD rigor (15%), 90-day plan executability (10%), 18-month
roadmap with abandonment criteria (15%), SoR decisions
defensibility (10%), regulatory continuity (10%), cultural
integration and talent retention (10%), synergy realization
credibility (5%), board / Audit Committee communication (5%).
§4.4 shows how each checklist item and each block maps onto
the D1–D10 artifact set the brief actually grades against.

A pass on this capstone requires all of the following.
Missing even one item is grounds for revision, not partial
credit — the integration plan is graded as a package.

- [ ] All five strategic-package blocks present (D1
      references each in its outline), at roughly the target
      lengths; longer is not better and usually means a
      reversibility mechanism was described in prose instead
      of drawn.
- [ ] §2.1's DD memo carries ≥ 15 findings in a checked-in
      log, each categorized (Blocker / Material / Monitor /
      Resolved), each with an action owner; Day-30
      confirmation activity named per unknown with an owner;
      cost-of-rebuild estimate documented; executive summary
      with an unambiguous deal recommendation
      (Proceed / Proceed-with-conditions / Escalate).
- [ ] §2.2's Day-1 checklist has ≥ 25 items, each with a
      named owner role and a pass / fail criterion; **no
      architectural change items on Day 1**; Day-30
      stabilization milestones are measurable; Day-90
      ratification gate has hard criteria and requires the
      Lumen founder's or her deputy's signoff.
- [ ] §2.2 identifies ≥ 3 quick-win synergies bookable in
      the 90-day window with named run-rates (per SR-2).
- [ ] §2.3's SoR register covers 10–15 shared concerns, each
      with the five-dimension framework applied (capability
      fit, regulatory weight, migration cost, talent signal,
      reversibility); ≥ 1 "Lumen wins" row with technical +
      strategic + cultural rationale; cross-decision
      dependencies noted.
- [ ] §2.3's patterns playbook documents 8–12 concrete
      cutovers, each with pattern + reversibility window +
      abandonment criterion + regulatory implication; **no
      big-bang on cross-cloud, customer-facing, or
      SaMD-touching cutovers**; the playbook is framed as
      reusable for future M&A.
- [ ] §2.3's cross-cloud analysis presents 4 options with
      the five-dimension scoring and defends Option D (or an
      equivalently reasoned alternative) with the
      re-evaluation gate at month 24.
- [ ] §2.4's regulatory continuity plan documents the HIPAA
      DFCR process with 5-business-day SLA; the FDA SaMD
      substantial-change decision tree; the HITRUST
      recertification path with a stated flip trigger; SOC 2
      continuity; a named Regulatory Affairs Liaison
      embedded in the IMO Technology workstream.
- [ ] §2.4 profiles all 8 named ML scientists with per-person
      retention design across the four architecture-side
      levers (toolchain / authority / identity / respect);
      broader cohort retention design with measurable
      targets (TR-1, TR-2); Lumen founder retention design
      with role + authority + earn-out alignment; 4 cultural
      anti-patterns named with design responses.
- [ ] §2.5's roadmap is 6 waves over 18 months, capacity-
      respecting (≤ 38 FTE effective per CON-2), with the
      four-outcome gate on every wave (success / refine /
      pivot / abandon), critical path marked with regulatory
      events, and ≥ 1 abandonment trigger the author would
      actually pull.
- [ ] §2.5's synergy model documents ≥ 8 levers with year-1
      + year-2 run-rate, sensitivity on 4 variables (GCP
      termination ±50%, headcount ±20%, cross-cloud timing
      ±3 months, vendor renegotiation ±30%), reconciles to
      $42M ±15%, and is CFO-rederivable.
- [ ] §2.5's board pack is ≤ 30 slides with an explicit
      **"what would make us re-baseline"** slide, one
      memorable headline number, three backup decks (CFO,
      CISO, Lumen founder), and a rehearsal complete note.
- [ ] Every requirement ID (IR-*, RR-*, TR-*, SR-*, CON-*)
      in the paired brief's `requirements.md` traces to a
      section of D1 or to a named deliverable D2–D10.
- [ ] Every fitness function (§2.5) has an owner and a
      failure-triggered path into meta-integration
      amendment.
- [ ] The package would be legible to a peer principal
      architect reading it cold, per the test in
      [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).
- [ ] The package contains at least one explicit "what would
      make this integration wrong" statement and at least
      one explicit "what we are deliberately not integrating
      here and why" statement (matches paired-brief
      `requirements.md` §7 non-requirements).

A distinction-level submission additionally does all of the
following (per the paired-brief §rubric distinction bar):

- [ ] A **"Lumen wins" SoR decision** with technical +
      strategic + cultural rationale, and a peer reviewer
      agrees it would not have happened without the explicit
      framework.
- [ ] A **named cutover where you chose parallel-run over
      strangler fig** with explicit reasoning (the
      unfashionable choice for regulatory safety — the SaMD
      parallel-run in §2.3 is the canonical example).
- [ ] A **specific Day-30 confirmation activity** whose
      negative outcome would credibly re-baseline the
      integration, not just refine a wave.
- [ ] A **cultural integration mechanism that costs
      synergy** but you defend (e.g., joint working groups
      slow some workstreams but save talent).
- [ ] A **reflection that names a mistake** in your own
      design — a place where you predict you will be wrong,
      and what would prompt the correction.
- [ ] Notes on what would change at a 20-employee
      acqui-hire scale and at a $50B-plus mega-deal scale,
      showing the author knows the assumed acquisition size
      is a choice (per §1 above).
- [ ] Explicitly cites at least one external standard (an
      FDA SaMD guidance document, a HIPAA CFR reference, a
      HITRUST CSF control, an integration-patterns
      canonical source such as Fowler, Newman, or Humble &
      Farley, or an M&A framework such as Sirower's
      *Synergy Trap*) as the anchor for a specific position
      rather than inventing terminology internally.

### 4.4 Mapping to the learning-repo deliverable set

The five-block strategic package above is the principal-track
spine; the learner-facing brief expects a wider ten-artifact
portfolio (D1–D10). Each block maps to one or more graded
artifacts and to specific rubric dimensions:

| Strategic-package block (this SOLUTION) | Learning-repo artifacts | Rubric dimensions primarily exercised |
|---|---|---|
| 2.1 Pre-close DD memo (memo + findings log + cost-of-rebuild) | D2 (DD memo + findings CSV + Day-30 confirmation plan + cost-of-rebuild worksheet) | DD rigor (15%) |
| 2.2 90-day operational plan (Day-1 + Day-30 + Day-90) | D3 (Day-1 checklist, Day-30 stabilization, Day-90 ratification gate, quick-wins) | 90-day plan executability (10%), Board / Audit Committee comms (5%) |
| 2.3 SoR decisions + patterns playbook + cross-cloud | D5 (SoR register), D6 (patterns playbook per-cutover files + cross-cloud analysis) | Integration architecture vision & pattern fitness (20%), SoR decisions defensibility (10%) |
| 2.4 Regulatory continuity + cultural integration | D7 (cultural + talent), D8 (regulatory) | Regulatory continuity (10%), Cultural integration + talent retention (10%) |
| 2.5 18-month roadmap + synergy + board comms | D4 (18-month roadmap), D9 (synergy), D10 (board pack), and D1 (integration vision) as the umbrella | 18-month roadmap with abandonment (15%), Synergy realization (5%), Board / Audit Committee comms (5%) |

The eight key questions the learning brief asks (pre-close DD,
SoR decisions, cloud strategy, integration patterns, 90-day
plan, cultural integration, regulatory continuity, synergy
realization — see
[`README.md §4`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/README.md))
are stress-tests against §2.1's finding categorization, §2.3's
SoR framework and Option D defense, §2.4's DFCR process and
retention design, and §2.5's lever model and abandonment
triggers. A submission that answers all eight without
touching every row of §2.3's SoR register or every cutover in
§2.3's playbook has misjudged the altitude and needs to push
back up.

## 5. Common mistakes

Patterns graders reliably see on this capstone. Most are
variants of failure modes named in the paired brief's
`rubric.md` "Common failure modes" section or in the
module-level `SOLUTION.md` files; they show up here because
the capstone is where DD, integration patterns, cultural
work, and regulatory continuity converge on a single
brownfield integration.

1. **The colonization plan.** Every SoR row (§2.3) files
   against Argent's system. Every cutover routes Lumen to
   Argent's stack. The 8-scientist retention design is
   "competitive comp." The Lumen team detects colonization
   inside Day 60; TR-1 breaches by month 6; the deal thesis
   unwinds. Rubric dimension 5 caps at half without a
   defensible "Lumen wins" decision; dimension 7 caps at
   half without per-person retention design.
2. **DD as inventory only.** ≥ 15 findings listed but no
   categorization, no owner, no Day-30 confirmation
   activity, no cost-of-rebuild estimate. The memo has
   surveyed the data room without producing a deal
   recommendation. Rubric dimension 2 caps at 10/15.
3. **The optimistic 90-day plan.** Day-1 checklist contains
   architectural change items (identity unification, secrets
   migration, observability consolidation on Day 1). Day-30
   stabilization is actually integration in disguise. Day-90
   ratification is a rubber-stamp on documents the steering
   has not read. Rubric dimension 3 caps at 6/10.
4. **Wish-list 18-month roadmap.** Six waves named, no
   abandonment criteria, no capacity check against the 38
   FTE cap in CON-2. Every wave "succeeds" by construction;
   nothing pauses. Rubric dimension 4 caps at 7/15.
5. **Big-bang for SaMD serving.** The playbook files the
   Triton → KServe cutover as big-bang. The reversibility
   window is 24h. This violates the framework's explicit
   prohibition (paired brief §6.6) and would trigger a 510(k)
   supplement determination; the rubric dimension 1 hard
   check zeroes on this row and caps dimension 1 at 13/20.
6. **Regulatory as an appendix.** D8 sits at the back of the
   package. HIPAA / FDA / HITRUST are named but not
   designed. No DFCR process; no substantial-change decision
   tree; no Regulatory Affairs Liaison. Rubric dimension 6
   caps at 4/10.
7. **"Competitive comp" as retention.** The 8 named
   scientists have a comp comparable-to-market plan attached.
   No toolchain-continuity design, no decision-authority
   design, no visible-respect design. The retention rests
   on money that a competitor can match. Rubric dimension 7
   caps at 5/10. See paired brief `rubric.md` "Common
   failure modes."
8. **Cross-cloud avoidance.** The submission leaves the
   GCP / AWS position "to be decided" or "provisional
   pending further analysis." The largest single
   architectural decision in the integration has not been
   made. Rubric dimension 1 caps at 13/20 regardless of the
   rest of the package.
9. **Fitness functions without intervention rules.** Six
   fitness functions listed; each has a target and a
   dashboard; none has a named rule for what changes if the
   target is missed. A fitness function without an
   intervention is a report, not instrumentation. Rubric
   dimensions 4 and 8 each drop half a band. Mirror of
   [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
   §5 item 6.
10. **The single-point synergy estimate.** $42M appears as a
    number without lever buildup; no sensitivity analysis;
    the CFO cannot re-derive from assumptions. The board
    receives a headline the CFO cannot defend at the next
    variance review. Rubric dimension 8 caps at 2/5. See
    paired brief `rubric.md` "Common failure modes."
11. **Rollback as aspiration.** Every cutover carries a
    "reversibility window" but no cutover names the
    rollback mechanism (traffic-shift rule, snapshot
    restore, feature-flag flip). The first rollback drill
    at month 3 fails; the credibility of every subsequent
    wave drops. Rubric dimension 1 hard-check on
    reversibility fails.
12. **Silent contradictions between D2, D3, and D4.** D2
    surfaces a Blocker finding on the Vertex-AI-specific
    dependency; D3 lists no Day-30 activity to confirm it;
    D4's Wave 3 assumes the dependency has been resolved.
    Any one of these might be true; not all three.
    Validation step §3.3 exists to catch this; most authors
    skip it and pay for the skip in review.
13. **Bypassing the Lumen founder read.** The submission
    passes internal review but has not been read by anyone
    playing the Lumen founder. When the founder reviews at
    Day 60, she surfaces two "Lumen wins" opportunities the
    plan missed and one retention design she disagrees with;
    the integration re-baselines on her signal, not on the
    plan's fitness functions. See paired brief
    `STEP_BY_STEP.md` §12 — the simulated Lumen-leadership
    review is the most-often-skipped and
    highest-leverage review persona.
14. **Presenting inevitability instead of a bet.** If the
    integration reads as "this is obviously how you
    integrate Lumen," the author has hidden the trade-off —
    often from themselves. Every graded principal-track
    deliverable makes the bet explicit; this one is no
    exception. Mirror of
    [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
    §5 item 10,
    [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
    §5 item 10, and
    [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
    §5 item 13.
15. **Skipping the "make a call" open questions.** The
    paired brief's `architecture.md` §15 lists seven
    decisions the submission must close (GCP unwind
    economics, identity cutover date, model registry ACL
    ownership, SaMD parallel-run duration, Argent platform
    team's role in Lumen tooling adoption, Backstage merger
    timing, per-scientist retention design credibility).
    A submission that leaves any open forfeits the
    coalition's trust that the integration will decide
    anything, since it could not decide about itself. Close
    ≥ 6 of 7 with a defended position or the plan is
    unfinished.

## 6. References

### Local curriculum context

- [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
  design philosophy across the principal-architect track;
  the "strategy survives stakeholder rotation" and peer-
  principal cold-read tests are the load-bearing frames for
  this capstone's DD memo and integration vision.
- [`../project-01-enterprise-platform/SOLUTION.md`](../project-01-enterprise-platform/SOLUTION.md)
  — the enterprise-platform capstone whose EAIP-equivalent
  is Argent's incumbent platform; the invariants and
  guardrails there are the object the SoR decisions in §2.3
  either preserve or displace.
- [`../project-02-technology-roadmap/SOLUTION.md`](../project-02-technology-roadmap/SOLUTION.md)
  — the roadmap capstone whose horizons and abandonment-
  criterion shape reappear here as the 6-wave 18-month plan
  in §2.5.
- [`../project-03-governance-framework/SOLUTION.md`](../project-03-governance-framework/SOLUTION.md)
  — the governance capstone whose ARB tiers, ADR practice,
  and exception process the integration *uses* (integration
  ADRs are filed against Argent's template, integration
  exceptions route through Argent's exception process). The
  meta-integration process in §2.5 borrows the meta-
  governance amendment pattern from §2.5 of `project-03`.
- [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  — the "sequence by blast radius" and "no exit criteria"
  patterns that make the wave-by-wave plan in §2.5 survive
  contact with the org.
- [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  — the coalition-mechanics module; the coalition moments
  in §2.5, the founder retention design in §2.4, and the
  hostile-CFO / hostile-CMO / Lumen-founder reads in §3
  all borrow from its "disagreement is information" and
  "coalitions decay" framings.
- [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md)
  — the altitude at which SoR decisions and standards
  positions land.
- [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)
  — the FinOps-credibility discipline the synergy model in
  §2.5 must survive when the CFO reads it.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — path
  parity and repo rules the capstone submission is expected
  to follow.

### Paired learning repository

- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/README.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/README.md)
  — the Argent Health / Lumen Bio Intelligence scenario,
  ten deliverables (D1–D10), the eight key questions the
  portfolio must answer, and the 60-hour duration
  breakdown.
- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/requirements.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/requirements.md)
  — the traceable requirement set (IR-*, RR-*, TR-*, SR-*,
  CON-*, ASM-*) every deliverable must map back to; §6
  acceptance criteria per D1–D10; §7 the non-requirements
  list.
- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/architecture.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/architecture.md)
  — the integration-system design doc with the 3-loop
  topology, the 15-row provisional SoR register, the
  pattern landscape, the cross-cloud options analysis, the
  cultural integration design, the regulatory-continuity
  architecture, the synergy model, the stage gates, and
  the seven "make a call" open questions the submission
  must close.
- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/rubric.md)
  — the nine-dimension, 100-point rubric with per-dimension
  hard checks, the six most common failure modes, and the
  distinction-grade bar ("Lumen wins" SoR decision,
  parallel-run over strangler fig, Day-30 confirmation
  activity that could re-baseline, culture-costs-synergy
  mechanism, mistake-naming reflection).
- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/STEP_BY_STEP.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/STEP_BY_STEP.md)
  — the 13-phase, 60-hour build guide; Phase 1 (DD),
  Phase 4 (pattern selection), and Phase 12 (reviewer
  rotation with a required simulated Lumen-leadership
  read) are the highest-leverage phases.
- [`../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/deliverables/README.md`](../../../ai-infra-principal-architect-learning/projects/project-04-ma-integration/deliverables/README.md)
  — the D1–D10 directory layout, per-deliverable
  checklists, and file-naming conventions the submission
  is expected to follow.

### External standards and canonical references

The capstone does not require any particular external
framework, but a distinction-level submission tends to
anchor its language to at least one of these widely used
references. The URLs are canonical entry points; the exact
clause an integration element maps to depends on the
regulatory and contractual context of the acquisition the
integration is written for.

Integration and modernization patterns:

- **Strangler fig — Martin Fowler** —
  <https://martinfowler.com/bliki/StranglerFigApplication.html>
  — the canonical name for the incremental-replacement
  pattern used across §2.3's playbook.
- **Anti-corruption layer — Eric Evans, *Domain-Driven
  Design*** — the DDD ACL pattern that §2.3 applies to the
  model registry and lineage cutovers; Evans's book is the
  citation of record.
- **Newman, *Building Microservices* (2nd ed., O'Reilly)**
  — <https://samnewman.io/books/building_microservices_2nd_edition/>
  — the reference for the parallel-run and dark-launch
  patterns in §2.3.
- **Newman, *Monolith to Microservices* (O'Reilly)** —
  <https://samnewman.io/books/monolith-to-microservices/>
  — the reference for pattern selection under brownfield
  migration constraints.
- **Humble & Farley, *Continuous Delivery* (Addison-Wesley)** —
  <https://continuousdelivery.com/> — the canonical
  reference for the branch-by-abstraction pattern applied
  to the training-orchestration cutover.
- **Feathers, *Working Effectively with Legacy Code*
  (Prentice Hall)** — the safe-refactor patterns behind the
  big-bang-with-reversibility-window cutovers in §2.3.

M&A integration and synergy:

- **Sirower, *The Synergy Trap* (Free Press)** —
  <https://www.simonandschuster.com/books/The-Synergy-Trap/Mark-L-Sirower/9781439137703>
  — the canonical anchor for §2.5's lever model and the
  discipline of naming the sensitivity variables the CFO
  would re-derive from.
- **Harding & Rovit, *Mastering the Merger* (Harvard
  Business Review Press)** —
  <https://store.hbr.org/product/mastering-the-merger-four-critical-decisions-that-make-or-break-the-deal/2607>
  — the reference for the four critical decisions (deal
  thesis, culture, integration approach, talent) that
  §2.4's cultural integration design and §2.5's
  ratification gate mirror.
- **Bain & Company — annual M&A reports** —
  <https://www.bain.com/insights/topics/mergers-and-acquisitions/>
  — the industry reference for the general M&A landscape
  and integration-value-realization patterns.
- **McKinsey — M&A and integration research** —
  <https://www.mckinsey.com/capabilities/m-and-a/our-insights>
  — the industry reference for cost / revenue synergy
  benchmarking; a submission that cites a specific McKinsey
  benchmark should link to the article and note the
  publication date, since benchmarks decay.

Regulatory references cited in the learning-repo brief:

The paired brief scopes the capstone to Argent Health, a
publicly traded health-tech acquirer subject to HIPAA, and
to Lumen Bio Intelligence, whose two cleared modules are
FDA-regulated SaMD and whose organization is HITRUST CSF
certified. Distinction-level submissions cite these
authoritative sources directly rather than paraphrasing
them:

- **HIPAA Privacy Rule — 45 CFR Part 160 and Subparts A
  and E of Part 164** —
  <https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164>
  — the codified Privacy Rule whose scope-management
  obligations §2.4's DFCR process is designed to satisfy.
- **HIPAA Security Rule — 45 CFR Part 160 and Subparts A
  and C of Part 164** —
  <https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html>
  — the codified Security Rule whose administrative,
  technical, and physical safeguards the BAA chain
  preservation in §2.4 protects.
- **HIPAA Business Associate Contracts — HHS OCR guidance**
  — <https://www.hhs.gov/hipaa/for-professionals/covered-entities/sample-business-associate-agreement-provisions/index.html>
  — the reference for the BAA chain audit cadence in §2.4.
- **FDA — "Deciding When to Submit a 510(k) for a Software
  Change to an Existing Device" (2017 final guidance)** —
  <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/deciding-when-submit-510k-software-change-existing-device>
  — the FDA guidance whose decision logic the SaMD
  substantial-change decision tree in §2.4 mirrors.
- **FDA — Software as a Medical Device (SaMD) guidance and
  IMDRF SaMD documents** —
  <https://www.fda.gov/medical-devices/digital-health-center-excellence/software-medical-device-samd>
  — the FDA program page linking the current SaMD
  guidances the cleared and pending Lumen modules operate
  under.
- **IEC 62304 — Medical device software — software life
  cycle processes** —
  <https://www.iso.org/standard/38421.html>
  — the international standard for medical device software
  lifecycles; the substantial-change decision tree and
  validation-evidence chain in §2.4 align to its Section 5
  process requirements.
- **HITRUST CSF** —
  <https://hitrustalliance.net/product-tool/hitrust-csf/>
  — the control framework whose certification path in §2.4
  Option 1 recommends recertifying under new ownership at
  the next cycle.
- **AICPA SOC 2 Trust Services Criteria** —
  <https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2>
  — the reference for the SOC 2 Type II continuity plan in
  §2.4.
- **ONC Information Blocking Rule (21st Century Cures Act,
  45 CFR Part 171)** —
  <https://www.healthit.gov/topic/information-blocking>
  — the reference for RR-6's information-blocking
  compliance posture (Lumen's existing posture maintained
  through the integration).

Adjacent standards worth citing where a specific position
touches an area they cover:

- **NIST AI Risk Management Framework (AI RMF 1.0)** —
  <https://www.nist.gov/itl/ai-risk-management-framework>
  — standard vocabulary for AI risk practices when a SoR
  decision on MRM or model observability touches AI-model
  risk (particularly relevant to §2.3's row 9 MRM split).
- **CNCF project maturity levels (Sandbox / Incubating /
  Graduated)** —
  <https://www.cncf.io/project-lifecycle-guidelines/>
  — the reference for evaluating OSS adoption timing on
  any SoR decision where the choice is an OSS project (e.g.
  Argo Workflows, KServe, Marquez).

Version pins, article references, and internal-policy
mappings should be added by the learner when defending the
submission inside a specific organization; the URLs above
are the canonical entry points, but the exact clause an
integration element maps to depends on the regulatory and
contractual context.
