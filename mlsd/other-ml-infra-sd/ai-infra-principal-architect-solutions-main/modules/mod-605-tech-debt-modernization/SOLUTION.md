# SOLUTION — Tech Debt and Modernization

> Read this *after* you have attempted the strategic deliverables.
> The "solutions" are frameworks and rubrics. This document
> explains *why* the principal-level view on tech debt is what it
> is, and where the most expensive mistakes hide.

## What this module is really teaching

Most engineers think of tech debt as "code that should be cleaner."
Principal architects have to treat it as a **portfolio of
financial liabilities**: each piece of debt has an interest rate
(ongoing cost), a principal balance (cost to retire), and an
optionality cost (what it prevents you from doing).

The truths the module teaches:

1. **Not all tech debt should be paid down.** Some debt is the
   cheapest option for the foreseeable future. Distinguishing
   debt that's costing you from debt that's not is the central
   skill.
2. **Modernization fails when it's framed as "rewrite."** The
   companies that succeeded at modernization (Stripe → newer
   Postgres, Shopify → Rails modernization) treated it as
   *incremental migration with continuous business value*, not
   as a stop-the-world rewrite.
3. **The carrying cost is invisible until you measure it.** Debt
   shows up as "everything takes longer" — without instrumentation,
   no one believes the cost.
4. **Modernization projects are mostly about people.** The
   technical work is 30%; communication, coordination, and
   maintaining business velocity is 70%.
5. **The right time to modernize is **before** the system breaks.**
   By the time it breaks, the cost is 5-10x higher and the
   options are worse.

## What the strategic deliverables should actually look like

### Case study (exercise 01): a modernization that worked or didn't

Pick a real modernization. Useful ones:

- Twitter's migration from Ruby on Rails to Scala (Mostly worked,
  took years, taught lessons).
- LinkedIn's monolith decomposition (Took 10+ years).
- Stack Overflow's deliberate decision **not** to modernize (Has
  worked well for them).
- A2A failed migrations — companies that spent years on a
  Kubernetes migration that didn't reduce ops cost.

Good case studies extract:
- The **trigger** for modernization. Was it a specific failure?
  A growth wall? Recruiting friction?
- The **strategy** — strangler fig, big bang, parallel build?
- The **business continuity story** — how did revenue stay
  intact during the migration?
- The **transfer** — what would we do differently in our org?

Common failure modes:
- **Survivorship bias**: the cases we hear about are the ones
  someone wrote a blog post about. Many successful "we just kept
  going on the old stack" stories don't have blog posts.
- **Underestimating duration**: every successful modernization
  took 2-3x longer than initially planned. Don't model your
  plan on the optimistic initial estimate.

### Strategy memo (exercise 02): the tech-debt portfolio view

A principal-level tech-debt memo treats debt as a portfolio:

1. **Inventory** — what are our 10-20 biggest debt items? Don't
   try to list everything. Pick the items worth $100k+/year in
   carrying cost.
2. **Per-item analysis**:
   - **Carrying cost** (in engineer-time or dollar-equivalent).
   - **Retirement cost** (one-time).
   - **Interest rate** (carrying cost / retirement cost).
   - **Optionality cost** (what this debt blocks).
3. **Recommendations** — which 2-3 items do we pay down this
   year? Which can we let coast?
4. **What we're *not* paying down**, and why. The decision to
   *not* modernize is as important as the decision to modernize.

A common, calibrated recommendation:

> "Item A has a carrying cost of ~$2M/year (two engineers full-time
> debugging deploy failures), retirement cost of ~$4M (one team,
> 9 months). 50% interest rate — pay it down now.
> Item B has a carrying cost of ~$500k/year and a retirement
> cost of ~$6M. 8% interest — keep paying the carry; we can
> afford it.
> Item C is the right tool for the job; what we called 'debt'
> is actually the right choice. No action."

Common failure modes:
- **Listing every annoyance as debt**: the memo loses focus.
  Filter to items above a cost threshold.
- **No "do nothing" option**: every memo should have a baseline
  of "what happens if we approve no remediation?"
- **Conflating personal preference with debt**: "We should use
  Rust instead of Python" is not tech debt; it's a preference.

### Stakeholder mapping (exercise 03): the modernization politics

Modernization projects threaten people. The stakeholder map needs
to include:

- **The team that owns the legacy system** — they will resist
  unless they're brought into the modernization team. The
  modernization team should be the legacy team, augmented, not
  a separate "new team" that puts the legacy team out of a job.
- **The teams that depend on the legacy system** — they have
  veto power over the migration timing. Their concerns are
  legitimate.
- **The finance partner** — modernization is a capital
  expenditure; finance needs to see the carrying-cost math.
- **Product / business leaders** — they're worried about
  feature velocity during the migration. They have a legitimate
  point.

Common failure modes:
- **"Skunkworks" modernization** by a separate team: produces a
  new system that doesn't match real-world usage and fails to
  win the migration.
- **Forgetting the depending teams**: they discover the migration
  three weeks before cutover and revolt.

### Roadmap (exercise 04): the modernization cadence

A modernization roadmap must show **business value at each phase**,
not just engineering progress. The standard shape:

| Phase | Duration | Business value visible |
|---|---|---|
| Instrumentation | 1 quarter | Measured carrying cost; baseline established |
| Strangler-fig start | 1-2 quarters | New writes go to new system; reads stay split |
| Migration wave 1 | 2-4 quarters | First major workload migrated; carrying cost drops |
| Migration wave 2-N | 1-2 quarters each | Progressive workload migration |
| Decommission | 1-2 quarters | Legacy system shut off; carrying cost zero |

Common failure modes:
- **All cost, no visible value until phase N**: the project loses
  funding mid-flight.
- **No "are we still on track to retire the old system?"
  checkpoint**: the new system gets adopted alongside the old
  one, and you now have two systems forever (the *worst*
  outcome).
- **Underweighting decommission**: the last 10% of users on the
  legacy system are the hardest to migrate and the most likely to
  cause the project to stall indefinitely.

### Presentation (exercise 05): selling the modernization

Modernization presentations have a specific failure mode: they
focus on the *new system's* properties when the audience cares
about the *current pain*. The framing that works:

1. **The current cost** — quantify the carrying cost in terms
   leadership cares about (velocity, incidents, hiring).
2. **The proposed investment** — what we're spending, over what
   horizon.
3. **The milestones with business value** — when does the carrying
   cost first drop? When does it reach zero?
4. **What can go wrong** — and what's our plan when it does.

Don't lead with "we're building a new platform." Lead with "the
current platform is costing us $X/year and blocking Y; here's a
24-month plan to eliminate that."

## Trade-offs we deliberately accepted

### Strangler-fig assumed as the default

Big-bang rewrites work for very small systems or for situations
where the old system has reached a true end-of-life (vendor went
bankrupt, hardware unsupportable). For nearly everything else,
incremental migration is the right pattern. The exercises assume
this.

### Carrying-cost math over architectural purity

The framework biases toward keeping debt that's cheap and paying
down debt that's expensive — even when the cheap debt is
"architecturally wrong." Architectural purity is a luxury;
carrying cost is real.

### No language-specific examples

The patterns apply across language stacks. The migration from
Python 2 → 3, Scala → Kotlin, JS → TS are all the same shape:
strangler fig, instrumentation, phased rollout. The exercises
stay at the shape level.

## Common mistakes graders see

1. **No baseline measurement**: claiming a system is "slow" or
   "fragile" without metrics. The first phase of every
   modernization is instrumentation, period.
2. **Optimistic timelines**: take your estimate, double it, then
   add a quarter for the long tail. That's still optimistic.
3. **Modernization as "engineering reward project"**: the team
   sees modernization as "we get to use the cool new stack." The
   business sees it as cost. The framing matters.
4. **Skipping the decommission**: the new system goes live, the
   old one keeps running for "edge cases," and you now have two
   systems forever. Always plan the shut-off.
5. **No exit criteria**: "we'll modernize until it's done" is
   not a plan. "We'll modernize until carrying cost is below $X
   or we hit milestone Y, whichever comes first" is.
6. **Letting the modernization team drift from the original
   business problem**: 18 months in, the new system is
   technically beautiful and solves a problem the business no
   longer has.

## When to go beyond this module

- Read **"Working Effectively with Legacy Code"** (Feathers).
  Tactical but transferable.
- Find a **stalled modernization** at your org and run the
  framework against it. Why did it stall? What would unstick
  it?
- Cross-reference the **mlops track** — ML pipelines accumulate
  their own special kind of debt (dataset drift, model registry
  cruft, feature-store version mismatch) that fits this
  framework.

## Related curriculum touchpoints

- `principal-architect/mod-601-org-wide-architecture` — the
  systems that accumulate the debt.
- `principal-architect/mod-603-multi-year-investment` — the
  financial framing of modernization.
- `principal-architect/mod-604-stakeholder-coalition` — the
  political path to actually shipping a modernization.
- `mlops/projects/project-4-governance` — ML-specific
  governance, which is often the lever that exposes ML tech
  debt.
