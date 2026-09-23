# SOLUTION — project-01-enterprise-platform

> Read this *after* attempting the capstone deliverables. This is a
> principal-architect track project: the solution is a rubric plus
> a worked structural template, not a runnable system. For runnable
> platform artifacts see the architect and senior-architect tracks.

The paired learner brief ([`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/README.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/README.md))
has been read and its contents are integrated throughout this
SOLUTION — the scope, deliverable list, and rubric below are
the final grading form, aligned with that brief.
The brief frames the capstone as the **Helix Financial Group
Enterprise AI Platform (EAIP)** — a 3-year, $120M program
consolidating 23 legacy stacks across 12 lines of business,
1,500+ engineers, and 600+ production models, under SR 11-7,
OCC 2011-12, GDPR, DORA, and EU AI Act obligations. The
learner's portfolio comprises ten graded artifacts (D1 vision
doc through D10 worked-LOB reference architecture) scored
against a seven-dimension rubric
([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/rubric.md)):
architectural soundness (25%), brownfield realism (15%),
regulatory fitness (15%), FinOps credibility (15%), tenancy
depth (10%), operating model (10%), and executive communication
(10%). Pass ≥70% overall with no dimension below 50%.

The five-document package rubric below is the **principal-track
rubric** — the strategic spine a peer principal architect would
grade before reading any of the D1–D10 depth artifacts. Every
generic invariant/guardrail row and every common mistake in this
SOLUTION maps directly to one or more of D1–D10; §4.4 gives the
mapping. Sections 2 (worked answer) and 4 (rubric) below have
been written against the brief's actual deliverable list and
grading criteria — they are the final graded form.

## 1. Solution overview

The `project-01-enterprise-platform` capstone asks the learner to
produce the **strategic package a principal architect would submit
to defend an enterprise-wide AI infrastructure platform**. It sits
downstream of `mod-601-org-wide-architecture` and pulls in material
from every other module in the track:

- from `mod-601` — the architectural altitude, invariants, and
  guardrails that let many teams build against one platform;
- from `mod-602` — the standards and interoperability positions
  that keep the platform legible to the outside world;
- from `mod-603` — the multi-year investment thesis that funds it;
- from `mod-604` — the coalition plan that gets it adopted;
- from `mod-605` — the modernization sequence that migrates
  incumbent workloads onto it without breaking the business.

A passing submission is not one artifact. It is a **package** of
five short, mutually consistent documents that could sit inside a
board-review binder. The value the principal is being graded on is
*coherence across the package*, not depth in any single document.

### What the deliverable is *not*

- Not a system design document. There are no component boxes at
  this altitude; those live in the architect track.
- Not a vendor selection. Pinned vendor bets have poor track
  records at multi-year horizons (see `mod-603` SOLUTION.md).
- Not a "platform vision" essay. Essays are cheap; commitments
  and success criteria are what get graded.
- Not runnable code. If the submission contains Terraform or
  Helm charts, the learner mistook the altitude of the exercise.

### What "enterprise" means for grading

For this project, assume the target organization has on the order
of five to ten platform teams and fifty to one hundred product
teams — the middle band `mod-601` frames its rubrics around. A
submission that works at that scale, and explicitly notes what
would change at the 100-engineer or 10,000-engineer scale, is
grading well above one that assumes a universal answer.

## 2. Worked answer or implementation

The package below is the shape a strong submission takes. Titles
and section counts should match; wording is the learner's.

### 2.1 The platform thesis (~1 page)

One page, one bet, stated as an imperative. Anchored on the memo
shape from `mod-601` SOLUTION.md (context → decision → rejected
alternatives → what we're betting → 30-60-90):

- **Context.** What is the current state of AI infrastructure
  across the org? What forces (regulatory, competitive, workload
  growth, cost) are pushing on it?
- **The decision.** State the platform commitment as an imperative
  the reader can agree or disagree with.
- **Rejected alternatives.** The most important section. At
  minimum: "let each business unit self-serve", "buy an end-to-end
  managed platform", "wait 12 months and re-evaluate". Say why
  each was rejected and what would flip the decision.
- **What we're betting.** If the thesis is wrong, what does the
  next re-platforming cost, and by what date will a leading
  indicator have surfaced the mistake?
- **30-60-90 day plan.** Concrete, dated commitments — the first
  standard published, the first migrated workload, the first
  budget approval.

### 2.2 The architecture position (~2 pages)

Not a component diagram. A **statement of the invariants** the
platform will enforce so that many teams can build on it without
coordinating with the principal architect on every decision. A
strong position document names, for each invariant, both the
guardrail *and* the escape hatch:

| Invariant | Guardrail | Escape hatch (with owner) |
|---|---|---|
| Identity and access | Federated SSO + workload identity mandatory | Break-glass root with weekly attestation, owned by security |
| Data plane isolation | Per-tenant namespaces + network policy | Shared research namespace, owned by ML platform lead |
| Model lineage | Every deployed model has a registry record | Research/experimental tier bypass, expires after 90 days |
| Cost attribution | Tagged workloads, chargeback ready | Central R&D budget for unlabeled prototyping |
| Change management | Progressive rollout, feature-flagged | Regulator-driven rollback path, owned by compliance |

The rows above are illustrative shapes; the learner fills in the
actual invariants their org needs. What is being graded is
whether the *structure* — guardrail plus explicit escape hatch
plus named owner — is present for each row. A guardrail without
an escape hatch produces shadow platforms; an escape hatch
without an owner produces permanent exceptions.

### 2.3 The investment thesis (~2 pages)

Draws directly on `mod-603` SOLUTION.md. The strongest
submissions include:

1. **Current spend profile.** What is the org spending today, on
   what cadence, on which line items (compute, storage, egress,
   SaaS, headcount)?
2. **The bet.** Over the horizon of the plan, spend on the
   platform will move from A to B under a stated assumption
   about workload growth. Investment C is required now to
   position for that.
3. **Two scenarios.** What happens if the growth assumption is
   right? If it is wrong? At what quarterly checkpoint does the
   answer become knowable?
4. **Reversibility.** Which commitments (reserved capacity,
   multi-year vendor terms, hiring) are hard to undo, and what
   would undoing them cost?
5. **Financial structure.** Capex vs opex, reserved vs on-demand
   mix, vendor concentration vs diversification, and the
   depreciation treatment the CFO will care about.

Guardrail: no numbers appear without an uncertainty band and a
stated assumption. A forecast presented as a point estimate is
wrong with probability approaching one, and a CFO reader will
know it.

### 2.4 The coalition plan (~1 page)

An influence-vs-interest map (see `mod-601` SOLUTION.md,
stakeholder mapping) with, for each named stakeholder:

- current position (supportive / neutral / opposed);
- what they need to hear the argument framed as (numbers,
  capability changes, contract terms, regulatory posture);
- the specific *ask* being made of them (approval, headcount,
  co-signature, deprecation of a competing initiative);
- the sequence — who must be convinced first, whose "yes"
  unlocks the next conversation.

The plan is graded on whether the sequence is credible, not on
its length. A stakeholder map with only one person per quadrant
is a warning sign that the political landscape has not been
mapped honestly.

### 2.5 The modernization sequence (~1 page)

The order in which incumbent workloads move onto the new
platform, **sequenced by blast radius** (see `mod-605`
SOLUTION.md and the cross-cutting principles in
`SOLUTION_OVERVIEW.md`):

- earliest: workloads whose failure is small, whose owners are
  volunteers, and whose migration validates the platform's
  guardrails;
- middle: workloads that are business-important but not
  business-critical, where the platform's operational maturity
  is proven before the next tier moves;
- last: workloads whose failure would be visible to customers or
  regulators, and which require the coalition plan above to
  have already delivered the necessary sponsorship.

For each tier, name the kill criterion — the specific signal
that would pause the migration and trigger replanning. A
modernization sequence with no kill criteria is a plan that
cannot admit it is wrong.

## 3. Validation steps

There is no build to run at this altitude. Validation is a
sequence of reviews the package must survive:

1. **Internal consistency check.** Re-read the five documents in
   order. Every claim in the thesis must be traceable to a
   commitment somewhere else in the package (a stakeholder ask,
   a budget line, an invariant, a migration wave). Claims with
   no downstream commitment are rhetorical; strip them or add
   the commitment.
2. **Rejected-alternatives audit.** For each document that
   states a decision, does the "rejected alternatives" section
   name at least the two most plausible alternatives, with a
   reason for rejection that a reasonable peer could disagree
   with? If not, the document is closer to propaganda than to
   argument.
3. **Peer-principal cold read.** Give the package to a peer
   principal architect (or the closest available proxy — a
   senior architect from an adjacent org, an ex-CTO advisor)
   with no context. The test from `SOLUTION_OVERVIEW.md`
   applies: they should be able to disagree with the decision
   and still articulate the reasoning. If they say "I can't
   tell what you were weighing," rewrite before submitting.
4. **CFO-mode read of section 2.3.** Read the investment thesis
   as if you had to defend every number to a skeptical CFO.
   Every dollar figure must have an assumption attached; every
   forecast must have an uncertainty band; every commitment
   must have a reversibility note.
5. **Sequencing sanity check.** Read the coalition plan and the
   modernization sequence side by side. The stakeholders whose
   "yes" is required for wave N of migration must be in the
   coalition plan and must have been sequenced to be convinced
   *before* wave N begins. If the calendar does not line up,
   one of the two documents is fictional.
6. **Standards-legibility pass.** For any position that touches
   an area covered by an external standard the org already
   engages with (for instance, the NIST AI Risk Management
   Framework for AI risk practices, or MLCommons benchmarks for
   performance claims), confirm that the position is stated in
   terms the standard would recognize. This costs little now and
   avoids retrofits later.

## 4. Rubric or review checklist

The checklist below is the principal-track spine and is
consistent with the learning brief's seven-dimension,
100-point rubric ([`rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/rubric.md)) —
architectural soundness (25%), brownfield realism (15%),
regulatory fitness (15%), FinOps credibility (15%), tenancy
depth (10%), operating model (10%), executive communication
(10%). §4.4 shows how each checklist item and each strategic
document maps onto the D1–D10 artifact set the brief actually
grades. The checklist here is the live grading rubric used to
score submissions.

A pass on this capstone requires all of the following. Missing
even one item is grounds for revision, not partial credit — the
package is graded as a whole.

- [ ] All five documents present, at roughly the target lengths.
      Longer is not better; a memo that exceeds one page usually
      buried the trade-off.
- [ ] The platform thesis states the decision as an imperative
      and names at least two rejected alternatives with reasons.
- [ ] The architecture position lists invariants with matched
      guardrails, escape hatches, and named owners.
- [ ] The investment thesis includes current spend, a stated
      assumption, two scenarios, a reversibility note, and a
      financial-structure section.
- [ ] Every forecast in the investment thesis has an uncertainty
      band or a stated assumption. No point estimates on
      multi-year lines.
- [ ] The coalition plan uses influence-vs-interest quadrants,
      lists more than one stakeholder per relevant quadrant, and
      names the sequence of asks.
- [ ] The modernization sequence orders waves by blast radius
      and gives each wave an explicit kill criterion.
- [ ] Cross-references between documents are consistent — a
      commitment in one is not silently contradicted by another.
- [ ] The package contains at least one explicit "what would
      make us wrong" and at least one explicit "what we are
      deliberately not solving" statement. A submission that
      surfaces no failure modes has not thought hard enough.
- [ ] The package would be legible to a peer principal architect
      reading it cold, per the test in
      [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).

A distinction-level submission additionally does the following,
though none are required to pass:

- [ ] Notes what would change at the 100-engineer and
      10,000-engineer scales, showing the author knows the
      assumed org size is a choice.
- [ ] Explicitly cites at least one external standard the
      platform will conform to (for example, an entry in the
      NIST AI Risk Management Framework) rather than inventing
      one internally.
- [ ] Includes a written post-mortem plan for the platform bet —
      how the org will audit the decision 12–18 months in, and
      what evidence would trigger a course correction.

### 4.4 Mapping to the learning-repo deliverable set

The five-document strategic package above is the principal-track
spine; the learner-facing brief expects a wider ten-artifact
portfolio (D1–D10). Each strategic-package document maps to one
or more graded artifacts and to specific rubric dimensions:

| Strategic-package document (this SOLUTION) | Learning-repo artifacts | Rubric dimensions primarily exercised |
|---|---|---|
| 2.1 Platform thesis | D1 vision doc, D9 board pack | Executive communication (10%), Architectural soundness (25%) |
| 2.2 Architecture position | D1, D2 C4 diagrams, D3 ADR set (≥20, target 30), D4 tenancy design, D10 worked LOB reference | Architectural soundness (25%), Multi-tenancy depth (10%) |
| 2.3 Investment thesis | D6 FinOps & TCO model, D9 board pack | FinOps & business-case credibility (15%) |
| 2.4 Coalition plan | D8 operating model & RACI, D9 board-pack backup decks | Operating model & org design (10%), Executive communication (10%) |
| 2.5 Modernization sequence | D7 36-month migration roadmap, D5 governance & MRM control catalogue | Brownfield realism (15%), Regulatory & governance fitness (15%) |

The eight key questions the learning brief asks (tenancy, build
vs. buy, multi-cloud, gen-AI gateway, MRM/EU AI Act encoding,
migration, operating model, exit/reversibility — see
[`README.md §4`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/README.md))
are stress-tests against §2.2 (invariants + escape hatches) and
§2.3 (reversibility notes). A submission that answers all eight
without touching every row of §2.2's table has misjudged the
altitude and needs to push back up.

## 5. Common mistakes

Patterns graders reliably see on this capstone. Most are variants
of failure modes named in the module-level `SOLUTION.md` files;
they show up here because the capstone is where all five converge.

1. **The essay masquerading as a strategy.** Long, chatty, no
   dated commitments. Fix by rewriting to the memo shape in
   `mod-601` SOLUTION.md; if a paragraph does not lead to a
   commitment, cut it.
2. **Rejected-alternatives section is a straw man.** "We could
   have done nothing, but that would be bad." The rejected
   alternatives must be the ones a smart peer would actually
   propose. If the reader would not have proposed them, they
   are decorative.
3. **Invariants without escape hatches.** Every guardrail that
   ships without an escape hatch produces a shadow platform
   inside a year. The rubric requires the escape hatch and its
   owner explicitly.
4. **Point-estimate financial forecasts.** A number without an
   assumption is a hostage to fortune. `mod-603` SOLUTION.md
   makes this case at length; the capstone re-checks it.
5. **Vendor pinning at multi-year horizon.** Concrete vendor
   selection is out of scope for this altitude and turns the
   package into a purchase order. State the *class* of vendor
   commitment (single, dual, portable) and the reason.
6. **Coalition plan built around one sponsor.** A plan that
   depends on the current VP of Engineering staying in the role
   is a project, not a strategy. Cross-check against the
   "strategy survives stakeholder rotation" principle in
   [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md).
7. **Modernization sequence with no kill criteria.** The
   modernization plan implicitly assumes every wave succeeds.
   Real programs have at least one wave that stalls; the plan
   must say what "stall" looks like and what to do about it.
8. **Silent contradictions between documents.** The thesis
   promises a 30% cost reduction; the investment section forecasts
   flat spend; the coalition plan tells the CFO the platform is
   revenue-enabling, not cost-out. All three cannot be true. The
   internal-consistency validation step exists to catch this;
   most authors skip it and pay for the skip in review.
9. **Under-serving the low-influence / high-interest quadrant.**
   Senior ICs and SREs know where the incumbent platform is
   broken and where the guardrails need escape hatches. A
   coalition plan that treats them as informational rather than
   consultative loses the highest-signal feedback available.
10. **Presenting inevitability instead of a bet.** If the
    package reads as "this is obviously the right platform,"
    the author has hidden the trade-off — often from themselves.
    The grading team will spend the review looking for what
    was hidden.

## 6. References

### Local curriculum context

- [`../../SOLUTION_OVERVIEW.md`](../../SOLUTION_OVERVIEW.md) —
  design philosophy across the principal-architect track. The
  memo tests and "strategy survives stakeholder rotation" idea
  are the load-bearing frames for this capstone.
- [`../../modules/mod-601-org-wide-architecture/SOLUTION.md`](../../modules/mod-601-org-wide-architecture/SOLUTION.md)
  — the memo, stakeholder-map, and roadmap rubrics reused
  throughout the capstone.
- [`../../modules/mod-602-industry-standards/SOLUTION.md`](../../modules/mod-602-industry-standards/SOLUTION.md)
  — feeds the standards-legibility validation step.
- [`../../modules/mod-603-multi-year-investment/SOLUTION.md`](../../modules/mod-603-multi-year-investment/SOLUTION.md)
  — investment-thesis shape, TCO components, forecast
  uncertainty guidance.
- [`../../modules/mod-604-stakeholder-coalition/SOLUTION.md`](../../modules/mod-604-stakeholder-coalition/SOLUTION.md)
  — coalition-plan mechanics.
- [`../../modules/mod-605-tech-debt-modernization/SOLUTION.md`](../../modules/mod-605-tech-debt-modernization/SOLUTION.md)
  — blast-radius sequencing and kill-criteria patterns for the
  migration wave plan.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — path parity
  and repo rules the capstone submission is expected to follow.

### Paired learning repository

- [`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/README.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/README.md)
  — the Helix Financial Group scenario, ten deliverables (D1–D10),
  the eight key questions the portfolio must answer, and the
  80-hour duration breakdown.
- [`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/requirements.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/requirements.md)
  — the traceable requirement set (REG-x, NFR-x) that D5's control
  catalogue and D4's tenancy design must map back to.
- [`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/architecture.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/architecture.md)
  — the C4 depth expectation (L1, L2 ≥ 6 subsystems, L3 ≥ 3
  subsystems) the D2 diagrams are graded against.
- [`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/rubric.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/rubric.md)
  — the seven-dimension, 100-point rubric with hard checks per
  dimension and the distinction-grade bar (an overridden ADR,
  a runnable fitness function, an unfashionable-choice trade-off,
  a cancelled migration wave).
- [`../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/STEP_BY_STEP.md`](../../../ai-infra-principal-architect-learning/projects/project-01-enterprise-platform/STEP_BY_STEP.md)
  — the day-level schedule the 80-hour plan expands into.

### External standards commonly referenced at this altitude

The capstone does not require any particular external framework,
but a distinction-level submission tends to align its language
with at least one of these widely used references:

- **NIST AI Risk Management Framework (AI RMF 1.0)** —
  <https://www.nist.gov/itl/ai-risk-management-framework> —
  the standard vocabulary for AI risk management inside U.S.
  regulated industries. Useful when the architecture position
  needs to talk about model governance in terms the compliance
  organization will already recognize.
- **MLCommons benchmarks** — <https://mlcommons.org/benchmarks/>
  — when the platform makes a performance claim, stating it in
  MLCommons terms is more defensible than an internal benchmark.
- **CNCF project maturity levels (Sandbox / Incubating /
  Graduated)** —
  <https://www.cncf.io/project-lifecycle-guidelines/> — a
  widely understood shorthand for build-vs-adopt decisions on
  open-source components.
- **Architecture Decision Records (ADRs)** —
  <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
  and the community template at
  <https://adr.github.io/> — Michael Nygard's original ADR
  format is the low-friction way to make the architecture
  position's per-invariant decisions reviewable over time.

### Regulatory references cited in the learning-repo brief

The paired brief scopes the capstone to Helix Financial Group, a
regulated bank. Distinction-level submissions cite these
authoritative sources directly rather than paraphrasing them:

- **Federal Reserve SR 11-7 — Supervisory Guidance on Model Risk
  Management** —
  <https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm>
  — the load-bearing model-risk framework for U.S. banks.
- **OCC 2011-12 — Sound Practices for Model Risk Management** —
  <https://www.occ.treas.gov/news-issuances/bulletins/2011/bulletin-2011-12.html>
  — the OCC's parallel guidance, cited alongside SR 11-7 in the
  brief.
- **EU AI Act (Regulation 2024/1689), especially Articles 6, 9,
  10, 11, 14, 15** —
  <https://eur-lex.europa.eu/eli/reg/2024/1689/oj> — obligations
  for high-risk AI systems that D5's control catalogue must
  encode in platform primitives, not process documents.
- **EU DORA (Regulation 2022/2554) — Digital Operational
  Resilience Act** —
  <https://eur-lex.europa.eu/eli/reg/2022/2554/oj> — ICT-risk
  and third-party-provider obligations that D4's tenancy design
  and D7's roadmap must satisfy.
- **GDPR (Regulation 2016/679)** —
  <https://eur-lex.europa.eu/eli/reg/2016/679/oj> — data-subject
  and cross-border transfer constraints on the data plane.

Specific version pins, page references, and internal-policy
mappings should be added by the learner when defending the
submission inside a specific organization; the URLs above are
the canonical entry points, but the exact clause a control maps
to depends on the regulatory and industry context.
