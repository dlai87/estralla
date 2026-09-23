# SOLUTION — Enterprise Architecture

> Read this *after* you have attempted the strategic deliverables.
> The "solutions" here are rubrics, not code. This document
> explains the *enterprise architect* lens.

## What this module is really teaching

Enterprise architecture is system design at the *organization*
level: which capabilities the business should have, how they
should compose, and which standards make that composition
possible. The exercises target deliverable shapes — capability
maps, architecture documents, reference architectures — rather
than implementation code.

## What the deliverables should actually look like

### Capability map (exercise 01)

A capability map is a 2-3 layer hierarchy of *what* the org
does, not *how*. Each capability has an owner team. The
discipline: map the business, not the org chart.

### Reference architecture (exercise 02)

A reference architecture document at the enterprise tier
includes:
- Capability mapping.
- System inventory with capability assignments.
- Integration patterns (event-driven, API, batch).
- Cross-cutting concerns (identity, observability, data
  governance).
- Future state vs. current state, with a migration path.

### Architecture decision records (exercise 03)

Every significant architectural decision gets an ADR with
context / decision / consequences / alternatives-considered.
ADRs are version-controlled. The reference uses Markdown +
GitHub conventions, not a separate tool.

### Cross-cutting concerns review (exercise 04)

Identity / observability / security / cost / data-governance
need consistent treatment across all systems. The reference's
cross-cutting review template enforces this.

### Architecture review board prep (exercise 05)

ARB packages document the change, its alternatives, the
recommendation, and the implementation plan. The deliverable is
one PDF a busy executive can read in 15 minutes.

## Trade-offs we deliberately accepted

- ADRs over heavy enterprise-architecture tools (TOGAF, Archi).
- Markdown-based documents over PDF — version-control is the
  audit trail.
- Capability maps stay simple (≤30 top-level capabilities).

## Common mistakes graders see

1. **Capability maps that are org charts**.
2. **Reference architectures that don't show *current* state**
   — only the aspirational future.
3. **ADRs missing the alternatives-rejected section**.
4. **Cross-cutting concerns treated per-system, inconsistently**.

## When to go beyond this implementation

- Adopt **C4 model** diagrams for clarity at scale.
- Move to **arc42** template if the team prefers heavier
  structure.

## Related curriculum touchpoints

- ``principal-architect/mod-601-org-wide-architecture`` — the
  next altitude.
- ``architect/projects/project-301-enterprise-mlops`` — the
  enterprise architecture in practice.
