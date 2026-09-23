# SOLUTION — Technical Leadership

> Read this *after* you have attempted the leadership deliverables.
> This document explains the *senior engineer* lens on technical
> leadership — how it differs from staff / principal leadership
> and what the right deliverables look like at this altitude.

## What this module is really teaching

Senior engineers transitioning toward staff often confuse
"leadership" with "management." The senior-engineer-leadership
skill set is:

- **Tech-lead-of-project**: owning a project's technical
  direction without owning people management.
- **Cross-team coordination**: aligning two or three teams on
  shared work.
- **Mentorship of mid-level engineers**: bringing 2-3 colleagues
  up to your level.
- **Author of technical documents** that survive months.

The leadership tracks (team-lead, principal-engineer, principal-
architect) cover the next altitudes; this module is the bridge.

## What the deliverables should actually look like

### The tech spec (exercise 01)

A senior-engineer tech spec is ~5-10 pages and contains:

1. **Problem** (1-2 paragraphs): What are we solving?
2. **Goals + non-goals** (bullets).
3. **Proposed approach** (technical design, with diagrams).
4. **Alternatives considered + rejected** (with reasons).
5. **Risks and mitigations**.
6. **Open questions**.
7. **Rollout plan**.

The right scope: a senior engineer can author this in 1-2 days,
review takes 2-3 days. Larger specs belong to staff / principal.

### The PR review checklist (exercise 02)

A good senior-engineer review covers:
- Correctness (does it work).
- Test coverage and test quality.
- Architectural fit.
- Performance implications.
- Security implications.
- Documentation completeness.

The shape of the review matters: comments are direct, refer to
specific lines, include the *why* not just the *what*. Senior
engineers' PR reviews are how the bar gets transmitted across
the team.

### The mentorship plan (exercise 03)

At this altitude, mentorship is 1-2 mentees, weekly check-ins,
focused on specific growth areas. The plan documents:
- Who you're mentoring.
- What they're growing into.
- What you'll do in the next quarter to help.

### The architecture review (exercise 04)

When a senior engineer reviews someone else's design:
- Read the spec twice before commenting.
- Comment on the *trade-offs*, not just the *choice*.
- Ask "what did you consider and reject?" not "why didn't you
  do X?"
- Be specific about which concerns are blocking vs. nice-to-have.

### The post-mortem write-up (exercise 05)

Senior-engineer-authored postmortems:
- Stick to the timeline.
- Avoid blame.
- Identify systemic causes, not personal mistakes.
- End with concrete action items (with owners + dates).

## Trade-offs we deliberately accepted

### Tech-lead-without-people-management is the focus

The senior engineer in this module does not have direct reports.
The leadership-track modules (team-lead, principal-*) handle
people management. The split keeps the rubric clean.

### Western corporate culture assumed

The mentorship and feedback patterns assume direct-communication
norms. Adapt for high-context cultures.

### Small-blast-radius decisions

The decisions a senior engineer makes affect their team (5-10
engineers) and adjacent teams. Org-wide decisions live at
principal+ levels.

## Common mistakes graders see

1. **Tech specs that don't include alternatives**: signals the
   author didn't consider any.
2. **PR reviews that nit-pick formatting and miss
   architecture**: the team learns nothing from those reviews.
3. **Mentorship reduced to answering Slack questions**: not
   mentorship, just a help desk.
4. **Postmortems with "the engineer should have known"
   findings**: blame disguised as analysis.
5. **Architecture reviews dominated by personal preferences**:
   "I'd use X instead" without engineering justification.

## When to go beyond this module

- Take on a **multi-team initiative** — see the principal-
  engineer track.
- Move into **management** if people leadership appeals — see
  the team-lead track.
- Become a **subject-matter authority** in one area — the path
  toward principal engineer.

## Related curriculum touchpoints

- ``principal-engineer/mod-501-technical-strategy`` — the next
  altitude.
- ``principal-engineer/mod-502-mentorship-leadership`` — deeper
  mentorship rubric.
- ``team-lead/mod-702-people-management`` — the people-
  management option.
