# SOLUTION — Emerging Technology

> Read this *after* you have attempted the emerging-tech
> deliverables. This document explains the architect's framework
> for evaluating emerging technology.

## What this module is really teaching

Architects sit at the boundary between mature tech (good
defaults) and emerging tech (potential bets). The skill is
recognizing which emerging tech is worth piloting *now* versus
*later* versus *not yet*.

## What the deliverables should actually look like

### Emerging-tech radar (exercise 01)

A 2x2 (or Thoughtworks-style ring) of technologies sorted by
maturity + relevance to the organization. Updated quarterly.

### Pilot proposal (exercise 02)

For an emerging tech: scope of pilot, success criteria, kill
criteria, timeline. Pilots that don't have kill criteria become
zombie projects.

### Tech-debt impact analysis (exercise 03)

Every adoption decision considers: what does this make easier
in 2 years? What does it make harder? What's the migration cost
out if we pick wrong?

### Vendor / OSS evaluation framework (exercise 04)

Criteria: community size, governance model, ownership concerns,
migration cost out, vendor financial health.

### Roadmap integration (exercise 05)

Emerging-tech decisions feed back into the multi-year roadmap
(architect/mod-603 / mod-501 territory).

## Trade-offs we deliberately accepted

- Emerging tech is high-risk: most pilots fail.
- Conservative architects miss windows; aggressive ones
  bet wrong.
- Frameworks help but don't eliminate judgment.

## Common mistakes graders see

1. **Tech radar as marketing** instead of decision tool.
2. **Pilots without kill criteria**.
3. **No follow-through on pilot learnings**.
4. **Vendor evaluation based on demos**, not architecture
   review.

## When to go beyond this implementation

- Adopt **deliberate experimentation budget** (5-10% of
  engineering time).
- Move to **portfolio-style emerging tech management** with
  explicit bets.

## Related curriculum touchpoints

- ``principal-engineer/mod-505-long-term-technical-bets`` —
  the long-bet framework.
- ``principal-architect/mod-602-industry-standards`` —
  standards-adoption frame.
