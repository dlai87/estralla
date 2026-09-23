# SOLUTION — Industry Standards

> Read this *after* you have attempted the strategic deliverables.
> The "solutions" here are rubrics and frameworks rather than
> running code. This document explains *why* the principal-level
> approach to industry standards is what it is — and where most
> principals get it wrong.

## What this module is really teaching

"Industry standards" sounds dry. The real subject is:

- **When to adopt** an emerging standard (Kubernetes, OpenTelemetry,
  OpenAPI, MLflow, Model Cards).
- **When to ignore** an emerging standard (most blockchain
  proposals, most ML "frameworks of the month").
- **When to *create*** a standard for your org or industry — and
  the rare conditions under which that's a good idea.
- **How standards become defaults** (the political and economic
  dynamics, not just the technical merits).

Principal architects sit at the boundary between their company and
the industry. Their job is to read the standards landscape
clearly enough that the company picks the right bets *before* the
market has fully decided. This is a skill, not a memorization
exercise.

## What the strategic deliverables should actually look like

### Case study (exercise 01)

Pick a standard that became dominant (Kubernetes, gRPC, JSON,
OpenAPI) or a standard that didn't (CORBA, SOAP, OpenSocial). Then
argue the **causal story** — what made adoption tip one way and not
the other?

Good case studies usually find that the winning standard had:
- A reference implementation that "worked on Tuesday" (you could
  run it in an afternoon).
- A vendor or large-employer pushing it (Google for Kubernetes,
  Stripe for OpenAPI tooling).
- A clear story about *what it replaced* (Kubernetes vs Mesos +
  Marathon, gRPC vs Thrift + REST).
- A community big enough to provide answers, small enough to
  agree on direction.

Common failure modes:
- **Reading the standard's RFC and concluding "this is good"**: the
  RFC does not predict adoption. Read the ecosystem around it.
- **Confusing "I use this every day" with "the industry adopted
  this"**: every team's tech stack feels universal from the inside.
- **Treating losing standards as obvious losers in hindsight**:
  CORBA had 80% of enterprise mindshare in 1998. The reasons it
  lost are not the reasons it looked weak at the time.

### Strategy memo (exercise 02): adopt, wait, or ignore

The principal-level strategy memo on a new standard answers three
questions:

1. **Is this standard durable enough to bet on?** What's the
   signal-to-noise: number of independent implementations, number
   of large adopters, age, governance model.
2. **What does *not adopting* cost us?** Interop with partners,
   recruiting friction, vendor pricing, future migration cost.
3. **What does adopting *too early* cost us?** Engineering
   investment that lands on a soon-deprecated spec, lock-in to a
   reference implementation that loses, training cost.

The shape of the recommendation:

> "Adopt now. The market has tipped. Cost of adoption is X; cost
> of *not* adopting will be Y by Q3 next year."

OR

> "Wait. The market has not yet picked between standard A and B.
> Cost of waiting is small; cost of betting wrong is large. We
> re-evaluate in N months when condition C is met."

OR

> "Ignore. The standard solves a problem we don't have, or solves
> it worse than what we already use."

Common failure modes:
- **"Adopt because it's the standard"** without quantifying the
  cost: the migration is six months of two engineers, often more
  than the long-term benefit.
- **"Wait" with no re-evaluation criteria**: becomes "ignore
  forever."
- **Conflating "popular on Hacker News" with "industry adopted"**:
  Hacker News volume is a leading indicator at best.

### Stakeholder mapping (exercise 03): the standards politics

Standards adoption is intensely political. The stakeholders that
matter:

- **Engineering teams** that will own the migration. They will
  resist if the migration looks like work without payoff.
- **Procurement / vendor management**, because adopting a standard
  changes vendor leverage.
- **Security and compliance**, because a new standard may break
  audit assumptions.
- **External partners** whose interop with you depends on the
  current standard.

Map them, and explicitly identify who has **veto power**. A
standards adoption that hasn't survived security review is not
adopted; it's just "in flight forever."

Common failure modes:
- **Skipping procurement** until late, then discovering vendor
  contracts forbid the migration.
- **Underweighting "this is the way we've always done it"
  resistance**: the cost is real and shows up as missed deadlines.

### Roadmap (exercise 04): the adoption curve

A standards adoption roadmap has a distinctive shape:

| Phase | Duration | Activities |
|---|---|---|
| Pilot | 1-2 quarters | One team adopts, instrumented for honest comparison |
| Reference implementation | 1 quarter | Platform team productionizes the pilot's setup |
| Migration wave 1 | 2-3 quarters | Volunteer teams migrate, learnings captured |
| Mandate | 1-2 quarters | All new systems use the standard |
| Sunset | 6-18 months | Old systems migrate (most teams) or are deprecated |

The principal architect's job is to set the cadence and resist
two failure modes:

- **Big-bang migration** (mandate without pilot) — recurring
  disaster.
- **Pilot forever** (pilot without ever mandating) — wastes the
  pilot's learnings.

### Presentation (exercise 05): selling standards adoption

Presenting a standards-adoption decision to executives requires a
specific framing: **the cost of *not* deciding**. Executives
respond poorly to "this is technically better" and well to "if we
don't make this decision in Q2, we will be locked out of partner
ecosystem X by Q4."

The presentation should include:
1. The decision being asked for.
2. The cost of inaction with a date.
3. The cost of adoption with a number.
4. The cost of adopting the *wrong* standard if there are
   competing ones — and how the decision criteria handle that.

## Trade-offs we deliberately accepted

### Standards selection biased toward consensus

The exercises assume the company is roughly mainstream and gains
from network effects. A research-heavy org that publishes its own
frameworks has a different calculus (the value is in *not*
adopting). The framework still applies; the weights change.

### No specific tooling recommendations

The right answer for "which standard for X" changes every 18
months. This module teaches the *evaluation framework*, not the
current answer. The current answer lives in the engineer-track
modules where it can be updated more frequently.

## Common mistakes graders see

1. **Treating "the standard exists" as evidence of stability**: ISO
   has standards that nobody uses; W3C has standards that
   languished for a decade before adoption (or never made it).
2. **Underweighting the cost of internal standards**: an
   org-internal standard that has 50 engineers maintaining it is
   the most expensive standard you'll ever adopt.
3. **Adopting a standard mid-flight**: a project halfway through
   implementation does not "swap to the new standard" cheaply.
   Either start over or finish on the old standard.
4. **Believing the vendor's adoption claims**: vendors always
   over-claim. Cross-reference adoption against independent
   sources (CNCF survey data, JetBrains developer survey,
   StackOverflow survey).
5. **Forgetting recruiting**: the standard your future hires
   already know is cheaper to adopt than the one they don't.
   Recruiting friction is a real cost.

## When to go beyond this module

- Sit in on a **standards body meeting** (CNCF TOC, OpenAPI
  steering committee, MLCommons) to see how the sausage is made.
  The politics will surprise you.
- Write a **post-mortem of a standards adoption** that didn't
  pan out at your company. Why did it fail? Was the failure a
  standard issue or an implementation issue?
- Cross-reference the **engineer track** on actual tooling for
  the standards in question, so the strategic memo is grounded in
  current implementation costs.

## Related curriculum touchpoints

- `principal-architect/mod-601-org-wide-architecture` — the
  architectural shape your standards plug into.
- `principal-architect/mod-603-multi-year-investment` — the
  financial framing of standards adoption.
- `principal-architect/mod-604-stakeholder-coalition` — the
  political execution.
- `senior-architect/mod-401-architectural-decision-making` — the
  decision frameworks that underpin standards selection at a
  smaller scope.
