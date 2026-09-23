# SOLUTION — Organization-Wide Architecture

> Read this *after* you have attempted the strategic deliverables
> for this module. There is no working code at this level — the
> "solutions" are rubrics, frameworks, and worked patterns from
> real-world principal architects. This document explains *why*
> the strategic deliverables are shaped the way they are.

## What this module is really teaching

Organization-wide architecture is not "system design at a larger
scale." It is a fundamentally different job:

- A senior engineer designs *the system*.
- An architect designs *systems across one product*.
- A principal architect designs *the conditions under which
  many systems can be designed well*.

That distinction matters. Principal architects don't draw a single
big diagram; they create the **standards, guardrails, and
investment patterns** that let dozens of engineers make local
decisions that compose into a coherent whole. The exercises in
this module — case study, strategy memo, stakeholder mapping,
roadmap, presentation — are practice for that job.

## What the strategic deliverables should actually look like

### The case study (exercise 01)

A good case study is not a re-telling of what a famous company
did. It is an **argument with a thesis**, of the form:

> "Company X faced trade-off T. They chose Y. The trade-off was
> visible in metrics M. The cost of the choice was C. Here is
> the analogous trade-off in our org, and the path I'd choose
> given our constraints."

Common failure modes:
- **Hagiography**: "Netflix is brilliant, here's their architecture."
  Tells the reader nothing. The reader knows Netflix is brilliant.
- **Ignoring counter-evidence**: every architectural choice has
  failures attached to it. A case study that doesn't surface the
  failure modes is incomplete.
- **No transfer**: the case study has to *transfer* a lesson. If
  the principal can't articulate "this is what we should do
  differently next quarter," the exercise was theater.

### The strategy memo (exercise 02)

A strategy memo is **one page, one decision, one trade-off**.
Bezos's six-pager works at executive level but is the wrong shape
for engineering strategy memos — those should be tighter. Format:

1. **Context** (3-5 sentences): What is the current state? What
   forces are pushing on it?
2. **The decision** (1-2 sentences): What are we choosing? State
   it as an imperative.
3. **The alternatives we considered and rejected** (bullets):
   This is the most important section. A memo without rejected
   alternatives is propaganda.
4. **What we're betting** (1 paragraph): If we're wrong, what
   does the next migration cost? When will we know we're wrong?
5. **The 30-60-90 day plan** (bullets): Concrete commitments.

Common failure modes:
- **No rejected alternatives section**: the reader can't tell
  whether the author considered the obvious counter-proposals.
- **Mushy commitments**: "We will work toward improving X" is
  not a 90-day plan. "X's p99 latency will be under 300ms by
  Q3" is.
- **Avoiding the trade-off**: every real decision has a cost. If
  the memo presents only upside, the author is hiding something
  (often from themselves).

### Stakeholder mapping (exercise 03)

Stakeholder maps are political artifacts disguised as
engineering ones. The right shape is a 2x2 matrix on **influence**
vs **interest** — but the value is not the matrix; it's the
conversations the matrix forces you to have with the people in
each quadrant.

The four quadrants and what to do:

| Quadrant | What it looks like | What to do |
|---|---|---|
| High influence, high interest | VP Eng, CTO, lead architect | Keep informed continuously; co-author when possible |
| High influence, low interest | CFO, head of legal | Surface only the 1-2 things they need to act on |
| Low influence, high interest | Senior IC engineers, SREs | Bring in early; their detailed feedback prevents rework |
| Low influence, low interest | Adjacent teams, vendor PMs | Monitor; don't over-invest |

Common failure modes:
- **Treating the map as a one-time artifact**: stakeholders shift
  position with each org change. The map needs a quarterly review.
- **Skipping the "low influence, high interest" quadrant**: this
  is the engineers who actually know what's broken. Their
  feedback is the highest-signal information you can get.
- **Confusing role with influence**: a senior IC with the CTO's
  ear has more influence than a director without it. Map the
  reality, not the org chart.

### The roadmap (exercise 04)

A multi-year architecture roadmap is **mostly wrong on the
out-years**. That is fine. The point is not to predict the future
accurately; it is to make the **dependencies** visible so today's
decisions are aware of next year's commitments.

Good roadmaps have:

1. **Three to five horizons** (now / next / later, or 6mo / 1yr /
   2yr / 3yr) — not month-by-month.
2. **Explicit cross-team dependencies** drawn between horizons.
3. **Bets and decision points** flagged — "if we ship X by Q2,
   we proceed; if not, we re-plan."
4. **Sunset items** as visible as build items — what are we
   *retiring* to make room for what we're building?
5. **A note on what's *not* on the roadmap and why.**

Common failure modes:
- **All build, no sunset**: an architecture team that only adds
  systems is generating future tech debt at a constant rate.
- **No decision points**: a roadmap with no "we'll know by Q3"
  moments becomes a fiction the team has to defend forever.
- **One person's opinion**: a roadmap that hasn't survived
  pushback from at least three senior engineers is untested.

### The presentation (exercise 05)

A principal-level presentation is **persuasion, not data dump**.
The format that works:

1. **The picture** (the architectural diagram you want everyone to
   walk away remembering).
2. **The problem the picture solves** (in 30 seconds, without
   acronyms the audience doesn't share).
3. **What we're asking the audience for** (budget, headcount,
   permission, decision).
4. **The two questions you expect them to ask** (and your
   answers).
5. **Backup slides** for the questions that arise outside the
   two you anticipated.

Common failure modes:
- **More than one big diagram**: the audience can only remember
  one. Pick it.
- **Burying the ask**: every executive in the room is asking
  "what do you want from me?" within the first minute. Tell them.
- **Defensive pre-emption**: 15 slides of "common objections" up
  front signals that the speaker doesn't trust the audience.

## Trade-offs we deliberately accepted

### Frameworks over templates

This module gives shapes and rubrics, not fill-in-the-blank
templates. Templates produce identical memos that say nothing;
frameworks force the author to think.

### No metrics for strategic quality

There's no quantitative grading for a strategy memo. The right
test is: would a peer principal architect, reading this memo cold,
disagree with the decision but understand the reasoning? If yes,
the memo is good. If they say "I have no idea what they were
weighing," the memo is bad regardless of length.

### Org structure assumed: ~1000-engineer org

The exercises assume an org with 5-10 platform teams and 50-100
product teams. The shapes change at 100-engineer and
10,000-engineer scales. The exercises lean toward the middle
because that's where most "principal architect" jobs sit.

## Common mistakes graders see

1. **Writing the case study about the wrong company**: a study of
   a 50-engineer Y Combinator startup teaches little about
   running architecture at a 5000-engineer org. Match the
   reference to your context.
2. **Memos that read like internal blog posts**: chatty,
   anecdotal, no concrete commitments. A memo without commitments
   is an essay.
3. **Stakeholder maps with only one stakeholder per quadrant**:
   real orgs have 5-15 people per quadrant. If you're missing
   people, you're missing politics.
4. **Roadmaps with no kill criteria**: a project with no "we'd
   stop this if X" is a project that will live forever.
5. **Presentations that re-explain the basics**: at the principal
   level, the audience already knows what a Kubernetes cluster
   is. Skip the primer; show the picture.

## When to go beyond this module

- Author a **real** architecture review document for a system in
  flight. Run it past two principals and incorporate their
  feedback.
- Sit in on (or lead) a **post-mortem of a strategic decision**
  that didn't pan out. Why did it not? What information was
  missing at decision time? What would have been a leading
  indicator?
- Cross-reference the senior-architect track's executive
  leadership module for the *next* level — what changes when the
  audience is the board, not the engineering org.

## Related curriculum touchpoints

- `principal-architect/mod-602-industry-standards` — the external
  reference points your strategy memos draw on.
- `principal-architect/mod-603-multi-year-investment` — the
  financial dimension of the roadmap.
- `principal-architect/mod-604-stakeholder-coalition` — the
  political dimension of the rollout.
- `senior-architect/mod-402-executive-leadership` — the next
  altitude up, where the audience is C-suite, not the eng org.
