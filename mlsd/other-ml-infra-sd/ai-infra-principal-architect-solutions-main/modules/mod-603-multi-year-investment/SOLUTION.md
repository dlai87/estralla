# SOLUTION — Multi-Year Investment

> Read this *after* you have attempted the strategic deliverables.
> The "solutions" are rubrics and patterns. This document
> explains *why* the principal architect's view on multi-year
> investment is what it is, and where the most common failures
> live.

## What this module is really teaching

Multi-year investment is where architecture meets finance. Most
engineers (and many architects) treat money as someone else's
problem; the principal architect treats capital allocation as a
core part of the job.

The truths the module teaches:

1. **Compute is the dominant line item now** — for any org doing
   serious ML, GPU spend is comparable to engineering headcount
   spend within 24 months.
2. **Build-vs-buy is rarely "build" at this scale.** Most
   in-house platforms cost 3-10x what teams expect; most managed
   alternatives cost 1.2-3x more per workload but include the
   operational burden.
3. **TCO is not what the vendor's calculator shows.** Hidden
   costs (integration, migration, training, opportunity) routinely
   double the sticker price.
4. **You buy options, not just outcomes.** Reserved capacity at
   3-year terms is cheap for committed workloads and expensive
   for exploratory ones. The right mix depends on confidence.
5. **The CFO is your peer, not your obstacle.** Principal
   architects who learn to read financial statements get a 10x
   amplifier on their influence.

## What the strategic deliverables should actually look like

### Case study (exercise 01)

Pick a company that made a large infrastructure investment that
either paid off massively (Netflix → AWS, Stripe → Postgres,
OpenAI → custom training cluster) or failed (any company that
built a "private cloud" in 2014-2018, most early Kubernetes
on-prem projects).

The right case study answers:

- What was the **bet**? State the alternative they could have
  chosen.
- What was the **horizon**? 1-year payback? 5-year? Indefinite?
- What were the **decision criteria** at the time, and what
  information would have changed the decision?
- What's the **transfer** to our situation?

Common failure modes:
- **Comparing 2014 decisions to 2026 conditions** without
  acknowledging that cloud GPU pricing has dropped 5x. A bad bet
  in 2014 might be a good bet in 2026 because the inputs changed.
- **Counterfactual cherry-picking**: "If they'd done X instead,
  they'd have won." Most counterfactuals are post-hoc.
- **No transfer**: a case study that doesn't answer "what would
  we do" is exercise without purpose.

### Strategy memo (exercise 02): the investment thesis

A multi-year investment memo is **a bet stated as a bet**. It
should include:

1. **The current spend profile** — what are we spending where, on
   what cadence?
2. **The bet** — over N years, we expect compute spend to
   move from A to B because (specific assumptions). We propose
   to invest C now to position for that.
3. **The two scenarios** — what happens if our assumptions are
   right? What happens if they're wrong? At what point do we
   know?
4. **The reversibility analysis** — what part of this commitment
   can we undo? At what cost?
5. **The financial structure** — capex vs opex, reserved vs
   on-demand, vendor concentration vs diversification.

A common shape:

> "Over the next 24 months, our training compute spend will move
> from $X/month to ~$3X/month if our current ML strategy
> succeeds. We recommend committing to a 3-year reserved-capacity
> agreement for the *baseline* portion (50% of current spend) and
> staying on-demand for the rest. This saves ~40% on the
> baseline, preserves flexibility on the variable, and is
> reversible after 18 months if the variable forecast is wrong."

Common failure modes:
- **The "everything will grow" assumption**: leadership decisions
  to slow ML investment do happen; the memo should plan for it.
- **Single-vendor lock-in without a multi-vendor backup plan**:
  the discount you got from concentration becomes the leverage
  the vendor uses against you in renewal.
- **Ignoring depreciation**: when you "buy" GPUs through reserved
  capacity, you've effectively pre-paid; the accounting
  treatment matters to the CFO and to your headroom.

### Stakeholder mapping (exercise 03): finance is a stakeholder

For multi-year investment, the stakeholder map has different
quadrants than usual:

- **CFO and finance partners**: high influence, will appear
  low-interest until the number is large enough; then very high
  interest.
- **Procurement / vendor management**: high influence on
  contract terms; medium interest in technical merits.
- **VP Engineering**: shares the bet; wants to see the
  reasoning.
- **Workload owners** (ML team leads, product leads): low
  influence on the financial decision, high interest in the
  technical impact.

The mapping forces the principal to plan **separate
conversations** with each. The CFO needs the bet stated as
numbers; the ML team leads need it stated as capability changes;
procurement needs it stated as contract clauses.

### Roadmap (exercise 04): the investment cadence

Multi-year roadmaps must align with the **budgeting cycle**, not
just the engineering cycle. The typical company runs annual
budgets with quarterly true-ups. A roadmap that ignores this
calendar will hit budget walls.

Roadmap structure:
- Quarter 1: commit, deploy reserved capacity, start workload
  migration.
- Quarter 2: midpoint review; adjust the variable portion based
  on actual utilization.
- Quarter 3: prepare next-year budget; the roadmap forecasts
  next year's spend so finance can budget.
- Quarter 4: contract renewal preparation; the roadmap informs
  vendor negotiations.

Common failure modes:
- **Roadmaps that don't surface contract decision points**: the
  vendor knows your renewal date; the roadmap should too.
- **No utilization metrics in the roadmap**: a reserved
  commitment without ongoing utilization tracking is a slow
  budget bleed.

### Presentation (exercise 05): selling the bet

Multi-year investment presentations are mostly to executives who
do not have ML domain knowledge. The framing that works:

- **Frame the bet in terms of revenue or product capability**, not
  GPU counts. "We can serve our top-tier customers' AI features
  at 99.9% SLO if we commit X now" is intelligible. "We are
  buying 256 H100s" is not.
- **Quantify the cost of inaction with a date**. Executives
  respond to ticking clocks.
- **Show three options, not one**. Aggressive, baseline,
  conservative. Executives like choosing; they hate being told.
- **Be ready for "can we delay six months?"** because that's the
  most common executive reaction.

## Trade-offs we deliberately accepted

### Assumes a real budget process

The exercises assume the org has annual budgeting and a CFO who
will approve infrastructure spend. Startups without that structure
have different (often simpler) dynamics. The frameworks still
work; the labels change.

### GPU-centric examples

The financial examples lean toward GPU and ML compute because
that's the line item that has grown fastest in the last 3 years.
The same patterns apply to storage, networking, and SaaS spend
with different multipliers.

### No specific vendor pricing

Specific vendor pricing changes quarterly. The exercises teach
the framework (TCO components, contract negotiation principles)
rather than a snapshot of prices.

## Common mistakes graders see

1. **TCO models that ignore engineering time**: an "in-house"
   solution that requires 4 engineers to maintain is more
   expensive than a managed service that's nominally 2x the
   price.
2. **Forecasts with no uncertainty bands**: a roadmap that says
   "spend will be $X in 2028" is wrong with probability ~1. Say
   "spend will be $X ± Y under assumption Z."
3. **Reserved capacity for workloads with high uncertainty**:
   reservations are cheap if used, expensive if not. Match the
   commitment level to the workload's certainty.
4. **No multi-vendor negotiation leverage**: signing a 5-year
   exclusive in year 1 saves nothing in year 5 when the vendor
   has no competition for your renewal.
5. **Treating "we don't know" as a reason to delay**: every
   delay has a cost. State the cost of waiting; sometimes the
   right answer is to commit despite uncertainty.

## When to go beyond this module

- Walk through your org's **actual budget** with finance. Until
  you've seen the line items, the abstractions stay abstract.
- Sit in on a **vendor negotiation** as an observer. The leverage
  moves are different from anything in an architecture document.
- Cross-reference the **senior-architect track** on executive
  finance — there's another altitude of detail (cap tables,
  unit economics) that becomes relevant at C-suite level.

## Related curriculum touchpoints

- `principal-architect/mod-601-org-wide-architecture` — the
  architectural shape these investments fund.
- `principal-architect/mod-602-industry-standards` — the
  standards-adoption cost component.
- `principal-architect/mod-604-stakeholder-coalition` — the
  political path to budget approval.
- `team-lead/mod-703-resource-management` — the operational layer
  for managing spend day-to-day.
