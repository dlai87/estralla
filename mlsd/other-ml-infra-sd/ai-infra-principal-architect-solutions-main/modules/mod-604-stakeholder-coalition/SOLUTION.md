# SOLUTION — Stakeholder Coalition

> Read this *after* you have attempted the strategic deliverables.
> The "solutions" are political-engineering rubrics. This document
> explains *why* coalition-building is a first-class principal
> architect skill — and why most engineers who skip it stall at
> staff level.

## What this module is really teaching

The shorthand "stakeholder coalition" is academic. The real
subject is **organizational power dynamics applied to
architecture decisions**. Principal architects who don't read
politics are blocked at every senior architecture review and
don't know why their proposals "go nowhere."

The truths the module teaches:

1. **Good ideas don't sell themselves.** A technically superior
   proposal that hasn't been pre-sold to three key stakeholders
   loses to a mediocre proposal that has.
2. **The first decision is who's in the room.** A meeting with
   the wrong audience can't produce the right decision no matter
   what you say.
3. **Vetoes are silent until they matter.** Security, compliance,
   procurement, and finance can each kill a project; engineers
   typically learn this after their first such killing.
4. **Coalitions decay.** A coalition built in Q1 starts to
   fragment by Q3 as people rotate, priorities shift, and
   memory of the original commitment fades.
5. **Disagreement is information.** A stakeholder pushing back
   knows something. The principal's job is to extract what.

## What the strategic deliverables should actually look like

### Case study (exercise 01): a real coalition that worked or didn't

A good case study here is **specific and recent enough that the
politics are visible**. Examples:

- Kubernetes adoption at a Fortune 500: who championed it, who
  blocked, what tipped the decision?
- Migrating an org from Spark to Ray (or back) — who was on each
  side?
- A failed "platform team" reorg — what coalition did the
  founders fail to build?

The case study should expose:
- The **map of interests** at the start.
- The **moves** the proponent made (white papers, prototypes,
  exec briefings, side conversations).
- The **counter-moves** by skeptics.
- The **point of decision** — what tipped, and why.

Common failure modes:
- **Treating organizational outcomes as deterministic**:
  "Kubernetes won because it was better." Mesos was arguably
  better technically; Kubernetes won on community + Google
  endorsement + reference implementation quality.
- **Ignoring the role of luck**: a championed project survives
  because a senior champion stayed at the company; another fails
  because the champion left. The case study should acknowledge
  this.

### Strategy memo (exercise 02): the coalition plan

A coalition-building memo for a major architectural change should
identify:

1. **The decision** being sought.
2. **The decision-maker(s)** — who has authority to approve, who
   has veto power.
3. **The supporters** — who will champion this in their team /
   org? What do they need from you to do so?
4. **The skeptics** — who is likely to object? On what grounds?
5. **The neutrals** — who is currently neutral but could be moved
   to either side?
6. **The plan**: 30-60-90 days of specific conversations,
   prototypes, and artifacts.

Coalition-building memos are private working documents, not
public propaganda. They name names. They describe people's
positions candidly. They never go to anyone outside the proposal
team.

Common failure modes:
- **Writing the memo to be sharable**: hedging in private
  documents produces meaningless plans.
- **Treating skeptics as obstacles instead of information sources**:
  every skeptic knows something the proposer doesn't. Find out
  what.
- **No "what does each stakeholder need from me?"** column. The
  coalition is built one transaction at a time, and you have to
  know what each party gets.

### Stakeholder mapping (exercise 03): the influence map

For coalition work, the stakeholder map gets a **third dimension**
beyond influence and interest: **position** (support, neutral,
oppose). The right artifact is two views:

1. The **current state** map — where everyone sits today.
2. The **target state** map — where they need to be for the
   decision to pass.

The difference between the two is the **work to be done**. A
realistic plan should show 5-10 specific stakeholders moving from
neutral to support, not the entire org flipping.

Common failure modes:
- **All-or-nothing thinking**: "we need everyone aligned" is
  fantasy. Most architectural decisions pass with 60-70%
  support, vocal opposition from 10-15%, and the rest
  indifferent.
- **Ignoring the strength of the position**: a strong "neutral"
  who can be moved is more valuable than a weak "support" who
  will flake. Weight by intensity.

### Roadmap (exercise 04): the coalition timeline

A coalition-building roadmap is sequenced around **decision
points**, not engineering milestones:

- Weeks 1-4: discovery conversations. Each meeting ends with
  "what would change your mind?"
- Weeks 5-8: prototype or proof-of-concept that addresses the top
  3 objections.
- Weeks 9-12: drafted strategy memo circulated to coalition
  members for feedback before going to the decision meeting.
- Weeks 13+: decision meeting; post-decision implementation.

The cadence: most coalitions take 90 days to build for a
significant decision. Compressing to 30 days produces a coalition
that hasn't been pressure-tested; expanding past 180 days lets
the political winds shift mid-flight.

### Presentation (exercise 05): the decision meeting

The decision meeting is the **culmination, not the start, of the
coalition work**. By the time you present:

- Every key stakeholder has seen the proposal and given input.
- Major objections have been addressed in the doc.
- The decision-maker knows what they're being asked.

The presentation in this meeting is **brief**. Most of the
preparation has happened in 1-1s. The meeting itself should:

1. State the decision being asked (1 minute).
2. Walk through the proposal at altitude (5 minutes).
3. Acknowledge the dissent that was not resolved (2 minutes) —
   this builds credibility.
4. Surface the open questions and proposed answers (5 minutes).
5. Move to decision (2 minutes).

Common failure modes:
- **Treating the meeting as the moment of persuasion**: if you're
  persuading in the meeting, you've already lost. Persuade in
  1-1s; ratify in the meeting.
- **Hiding the dissent**: the decision-maker will hear about it
  later. Better to surface it yourself and frame the response.

## Trade-offs we deliberately accepted

### Politically realistic, not idealistic

The module assumes politics is a real and necessary skill, not a
character flaw. Engineers who insist "good ideas should win on
merit" lose to engineers who do the political work. The
exercises don't moralize about this; they teach the skill.

### Heavily 1-1 oriented

The recommended cadence (lots of 1-1s, few large meetings) is
the right shape for most enterprise orgs. Smaller orgs and
heavily-async companies have different shapes; the underlying
principle (build agreement before the meeting) still holds.

### Anglo-corporate cultural assumption

The patterns lean toward US/UK/Northern European corporate
norms. Other cultures have different norms around hierarchy,
public dissent, and consensus-building. Adapt the implementation;
the strategic frame still applies.

## Common mistakes graders see

1. **Confusing alignment with agreement**: people can be aligned
   on a decision without agreeing with it. Aligned means
   "willing to support the outcome publicly"; agreement means
   "thinks it's right." You need alignment; you don't always
   get agreement.
2. **Ignoring the manager chain**: most senior engineers do
   coalition work peer-to-peer and forget to brief their own
   manager. Then the manager hears about it from someone else
   and the project is wounded.
3. **Skipping security and compliance until late**: they have
   veto power and they exercise it. Bring them in at week 1, not
   week 11.
4. **No follow-through after the decision**: a coalition that
   approves a project and never hears back fragments before the
   project ships.
5. **Burning relationships for one win**: a coalition built by
   high-pressure tactics works once. The next decision is
   harder. Treat reputation as a long-term resource.

## When to go beyond this module

- Volunteer to run a **post-mortem on a stalled architecture
  decision** at your org. The reasons it stalled are almost
  always political, not technical.
- Shadow a **senior architecture review** as a notetaker. The
  dynamics in the room — who speaks, who defers to whom, who is
  silent — are the curriculum.
- Read **"Getting to Yes"** (Fisher & Ury) and **"Crucial
  Conversations"** (Patterson et al.). The frameworks transfer
  directly.

## Related curriculum touchpoints

- `principal-architect/mod-601-org-wide-architecture` — the
  architectural decisions that need coalitions to ship.
- `principal-architect/mod-603-multi-year-investment` — the
  budget decisions that especially need coalition work.
- `principal-architect/mod-605-tech-debt-modernization` —
  modernization projects that fail or succeed based on coalition
  quality.
- `team-lead/mod-702-people-management` — the day-to-day
  relationship work that makes coalitions easier.
