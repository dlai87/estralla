# SOLUTION — Architectural Communication

> Read this *after* you have attempted the architectural-
> communication deliverables. This document explains the
> architect-tier communication frame.

## What this module is really teaching

Architecture decisions that aren't communicated well don't
land. The architect's communication skill includes:
- Picking the right artifact (memo, slide, diagram, ADR).
- Picking the right altitude per audience.
- Translating "engineering" into "business" without losing
  signal.

## What the deliverables should actually look like

### Audience map (exercise 01)

For a given architecture proposal, who needs to be persuaded?
What's their altitude? What format do they consume?

### Strategy memo for executives (exercise 02)

One page. State the decision, the alternatives, the
recommendation, the ask. Executives want decisions, not
expositions.

### Technical deep-dive for senior engineers (exercise 03)

10-30 pages. Trade-offs, alternatives, implementation
considerations, risks. Engineers want detail.

### Architecture diagram set (exercise 04)

C4 model: context diagram, container diagram, component
diagram, code (optional). Different altitudes for different
conversations.

### Pre-read packet for ARB (exercise 05)

Distributed 48 hours before the meeting. Includes context,
proposal, alternatives, recommendation, supporting analysis.
ARB members come prepared.

## Trade-offs we deliberately accepted

- One-page memos require painful editing.
- Multiple-altitude documents mean producing the same content
  in different shapes.
- Diagrams age fast and need maintenance.

## Common mistakes graders see

1. **One document, all audiences**: serves none well.
2. **Diagrams too dense**: nobody reads them.
3. **Memos that bury the recommendation**.
4. **Pre-reads sent the morning of**: nobody prepares.

## When to go beyond this implementation

- Adopt **diagram-as-code** (Structurizr, Mermaid) for
  version-controlled diagrams.
- Move to **video walkthroughs** for async-first orgs.

## Related curriculum touchpoints

- ``principal-architect/mod-601-org-wide-architecture`` —
  presentation patterns at higher altitude.
- ``senior-engineer/mod-210-technical-leadership`` — peer-
  audience communication.
