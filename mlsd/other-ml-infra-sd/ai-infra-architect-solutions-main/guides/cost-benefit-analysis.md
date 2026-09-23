# Cost-Benefit Analysis Guide

> Companion to `architecture-patterns.md`, `enterprise-standards.md`, and `stakeholder-communication.md`. How a senior architect produces financial analysis that engineers respect and CFOs trust.

---

## What this guide is

A staff/principal architect proposing a multi-quarter investment will get asked, "what's the ROI?" The answer needs to be defensible to a CFO partner who's seen every flavor of optimistic engineering forecast. This guide is the field manual for producing analysis that holds up to scrutiny.

The goal isn't to learn finance from scratch. It's to learn enough financial vocabulary and modeling discipline to have substantive conversations with the people who control the budget.

---

## The vocabulary you need

A small set of terms that come up in every conversation:

| Term | Plain-English definition |
|---|---|
| **TCO (Total Cost of Ownership)** | Everything you'll spend over the full life of a system — purchase, ops, maintenance, eventual replacement. |
| **NPV (Net Present Value)** | Future cash flows discounted to "today's dollars" at some discount rate. Comparable across projects with different timelines. |
| **IRR (Internal Rate of Return)** | The discount rate at which NPV equals zero. "How fast does the investment grow?" |
| **Payback period** | How long until cumulative savings equal initial investment. |
| **Discount rate** | The opportunity cost of capital — typically 8-12% for a well-funded org. CFO sets this. |
| **OpEx vs CapEx** | Operating expense (subscriptions, salaries) vs capital expense (one-time purchases that depreciate). Matters for tax treatment and cash flow. |
| **Hurdle rate** | The minimum IRR your org will accept to fund a project. Below the hurdle rate, money goes elsewhere. |
| **Sunk cost** | Money already spent. Should not influence future decisions (though it often does). |
| **Opportunity cost** | What you give up by choosing this investment over the next-best alternative. |
| **Sensitivity analysis** | "What happens to the answer if assumption X is wrong by 20%?" |

You don't need to be the org's Excel model expert; you need to know what these mean so you can read the analysis the finance team puts together and challenge it intelligently.

---

## The four-question check before any analysis

Before building a model, answer these:

1. **What's the alternative we're being compared against?** "Do nothing" is an alternative; so is "do the cheaper version." Without a comparison baseline, the analysis is incoherent.
2. **What's the decision horizon?** 12 months? 36 months? Decisions that pay back in year 5 will be evaluated very differently from decisions that pay back in year 1.
3. **What's the certainty range?** Some numbers are well-known (current spend); some are speculative (future adoption). Mark each.
4. **Who's the audience and what's their hurdle rate?** A series-B startup will fund projects at IRR > 30%; a Fortune-500 IT org will fund at IRR > 15%. Don't propose a 12% IRR to either.

If you can't answer these in two sentences each, you're not ready to model.

---

## A defensible cost model

Structure (whether in a spreadsheet, a YAML file, or a doc):

### Inputs sheet

Every assumption explicit, sourced, and dated. Format suggestion:

```yaml
inputs:
  - id: current_compute_spend
    value: 4_100_000
    unit: USD/year
    source: AWS Cost Explorer, FY-2024 actual
    confidence: high
    last_updated: 2026-04-12

  - id: post_migration_compute_spend
    value: 2_700_000
    unit: USD/year
    source: Vendor A quote + pilot extrapolation; see Appendix A
    confidence: medium
    last_updated: 2026-05-08

  - id: migration_engineering_hours
    value: 6_400
    unit: hours
    source: Estimate based on team size + similar migrations
    confidence: medium
    last_updated: 2026-05-15

  - id: engineering_fully_loaded_cost
    value: 275_000
    unit: USD/year/FTE
    source: HR comp band P75 + 35% overhead
    confidence: high
    last_updated: 2026-05-01
```

Why this format: it's reviewable. A skeptic can challenge any specific input, and the conversation becomes about that input, not about the model.

### Calculation sheet

Derived quantities from inputs. Every formula visible. Common derivations:

```text
annual_savings = current_compute_spend - post_migration_compute_spend
              = 4_100_000 - 2_700_000
              = 1_400_000

migration_cost_engineering = migration_engineering_hours / 2080 * engineering_fully_loaded_cost
                           = 6_400 / 2080 * 275_000
                           = 846_154

migration_cost_total = migration_cost_engineering + vendor_setup + risk_buffer
                     = 846_154 + 400_000 + 200_000
                     = 1_446_154

simple_payback_months = migration_cost_total / (annual_savings / 12)
                      = 1_446_154 / (1_400_000 / 12)
                      = 12.4 months
```

### Output sheet

The headline numbers in the format the audience expects:

```text
SUMMARY (5-year horizon)

  Investment Year 1:       $1.45M
  Annual savings (steady): $1.40M
  Simple payback:          12 months
  5-year NPV (10% disc):   $4.9M
  5-year IRR:              94%
  Hurdle rate (org):       15%

CONFIDENCE
  High confidence:   current spend, FTE cost
  Medium confidence: post-migration spend, migration hours
  Low confidence:    realized adoption rate
```

### Scenarios sheet

Three scenarios minimum: pessimistic, base, optimistic. Vary the inputs you marked "medium" or "low" confidence; hold the "high" confidence ones steady.

```text
SCENARIO COMPARISON

                       Pessimistic    Base       Optimistic
Migration hours          9,600       6,400       4,800
Post-mig spend (yr1)   $3.2M        $2.7M       $2.4M
Annual savings yr 1    $900K        $1.4M       $1.7M
5-yr NPV                $1.1M       $4.9M       $7.3M
5-yr IRR                 24%        94%         165%
Payback (months)         24         12          8
```

The pessimistic scenario should still clear the hurdle rate. If it doesn't, the project is too risky to fund as proposed; either de-risk it (smaller scope, pilot first) or accept that it might not happen.

---

## Common mistakes engineers make in cost models

### Conflating savings with revenue

Saving $1M on compute is good. Generating $1M in new revenue is also good. They're not interchangeable; finance treats them very differently. A model that mixes them under "value created" will be pushed back on.

Be explicit: "$1.4M annual operating cost savings + $X potential revenue protection (separately quantified, lower confidence)."

### Ignoring opportunity cost

"We'll have 4 engineers work on this for 6 months." OK — but what would those engineers be doing otherwise? If the alternative is shipping a $10M revenue feature, the migration project is much more expensive than the labor cost suggests.

Always include the opportunity-cost note: "These 4 engineers would otherwise have shipped [feature]; estimated business impact of delay is $X."

### Counting cash flow that doesn't exist

"We'll save 30% on observability spend" — but if those vendors are on annual contracts that don't expire for 18 months, the savings don't materialize until then. Cash flow modeling has to respect contract terms, not just steady-state economics.

### Optimistic adoption assumptions

The model assumes 80% of teams will migrate in year 1. Real-world migration projects achieve 30-50% in year 1. Adjust accordingly, or run the pessimistic scenario at the lower number.

### Forgetting transition costs

During migration, you often run both systems simultaneously (old and new). That's double-paying for a period. Model it explicitly.

### Sunk-cost rationalization

"We already invested $2M in the current system; we should keep using it." Wrong question. The right question is "given today's choices, what's the best path forward?" Sunk cost is irrelevant to future decisions.

### Single-point estimates

"It will cost $1.8M." Real cost is a distribution. Present as a range or, better, with explicit scenarios. Single-point estimates get treated as either over-confident (and challenged) or as soft (and discounted).

---

## Building the analysis collaboratively

The strongest cost models are built with the finance team, not handed to them. Sequence:

1. **Initial conversation with finance partner** (45 minutes). Share the problem, your initial sense of the numbers, ask: what's the org's hurdle rate, what discount rate to use, what level of detail finance needs, who else needs to see the analysis. Save substantial rework later.

2. **Draft model** (a few days). Build the inputs sheet first; circulate just the inputs for sanity-checking before doing any math.

3. **Review with finance partner** (60 minutes). Walk through the model live. They'll find errors. Fix them.

4. **Stakeholder pre-wire** (30 min each, sponsor + product partner + others). Share the model + summary; gather concerns; refine.

5. **Final presentation to sponsor** (30 minutes). Lead with the summary; the model is the backup.

Cycle time: 2-4 weeks for a meaningful investment proposal. Less than that and you haven't gathered enough feedback; more than that and the underlying conditions have probably changed.

---

## Worked example: vendor consolidation

Problem: org has 3 observability vendors. Cost is high; engineer experience is fragmented.

**Inputs:**

| Input | Value | Confidence | Source |
|---|---|---|---|
| Current annual spend | $4.1M | High | AWS Cost Explorer, vendor invoices, FY-2024 |
| New vendor (Vendor A) annual spend at full migration | $2.4M | Medium | Vendor quote + pilot extrapolation |
| Migration engineering effort | 6,400 hrs | Medium | Bottom-up estimate by team |
| Fully-loaded engineering cost | $275K/FTE/year | High | HR comp band + overhead |
| Existing contract early-termination penalty | $400K | High | Contract review |
| Risk buffer | 15% | Conventional | Industry rule of thumb |

**Calc:**

```text
Migration cost = engineering + termination + risk buffer
              = (6400 / 2080 * 275_000) + 400_000 + (0.15 * 846_154 + 400_000)
              = 846_154 + 400_000 + 186_923
              = 1_433_077

Annual savings = 4_100_000 - 2_400_000
              = 1_700_000

Simple payback = 1_433_077 / (1_700_000 / 12) = 10.1 months

5-year cumulative savings (undiscounted) = 5 * 1_700_000 - 1_433_077 = 7_066_923

5-year NPV (10% discount rate) = sum over years 1-5 of (savings_y / 1.1^y) - migration_cost
                              ≈ 5_010_000 (using flat $1.7M annual savings)
```

**Scenarios:**

```text
                         Pess    Base    Optim
Migration hrs           9_600   6_400   4_800
Spend post-mig (yr 1)  $3.0M   $2.4M   $2.1M
Savings yr 1            $700K  $1.4M   $1.7M
5-yr NPV               $1.0M   $5.0M   $7.5M
Payback (mo)            22      10      7
```

**Headline:**

"$1.4M one-time investment for $1.7M/year recurring savings. 10-month payback in the base case; 22-month payback in the pessimistic case (which still clears the org's 15% hurdle rate)."

That's the number that goes in the one-page brief. The model is the backup material.

---

## When the math doesn't justify the project

This happens. The cost-benefit comes out negative, the payback is past the decision horizon, the hurdle rate isn't cleared. Three options:

1. **Don't pursue.** Honestly the most common right answer. Not every good idea is a good investment right now.

2. **Re-scope.** Smaller pilot, tighter scope, faster payback. "We can't fund the whole thing; we can fund the first phase and re-evaluate."

3. **Make the qualitative case explicitly.** Some investments are worth doing even when the math is marginal — strategic optionality, regulatory necessity, retention risk, brand. State the qualitative case directly: "This doesn't meet the 15% hurdle rate, but we recommend approval because of [explicit qualitative factor], which we estimate at $X if quantified."

Don't fudge the numbers to make a marginal project look good. The CFO partner will spot it; trust takes a hit; future analyses get more scrutinized.

---

## A reading list

- *Investing in Innovation* — Anita McGahan & David Bach (HBR series). The framing for tech investment decisions.
- *Financial Intelligence for IT Professionals* — Karen Berman & Joe Knight. Best engineer-friendly intro to accounting + finance.
- *The Phoenix Project* / *The Unicorn Project* — Gene Kim et al. Not finance per se, but excellent on how to communicate IT investment value to business.
- The CFO's annual letter to investors. Read it. The CFO writes about what they care about; if your proposals align with those themes, they're easier to fund.

---

## See also

- [`architecture-patterns.md`](./architecture-patterns.md) — the patterns whose adoption you're justifying
- [`enterprise-standards.md`](./enterprise-standards.md) — standards governance, where cost-benefit shows up regularly
- [`stakeholder-communication.md`](./stakeholder-communication.md) — how to present cost-benefit findings effectively
