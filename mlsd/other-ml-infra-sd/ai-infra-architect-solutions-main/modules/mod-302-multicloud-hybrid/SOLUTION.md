# SOLUTION — Multi-Cloud and Hybrid

> Read this *after* you have designed the reference multi-cloud
> architecture. This document explains the architect-tier lens on
> multi-cloud / hybrid topologies.

## What this module is really teaching

The senior-engineer track (mod-205) teaches the technical
implementation of multi-cloud. The architect tier focuses on
**when to choose** multi-cloud at all:
- Sovereign-cloud / data-residency mandates.
- Vendor concentration risk.
- M&A leaving the org on multiple clouds.
- Workload-specific cost differentials.

## What the deliverables should actually look like

### Multi-cloud decision document (exercise 01)

The deliverable answers:
- Why multi-cloud, specifically?
- Active/active, active/passive, or federated?
- What's the data master?
- What's the ops cost?

If the document can't answer "why specifically multi-cloud," the
decision is wrong.

### Reference topology (exercise 02)

Network topology, identity federation, observability federation,
deployment patterns. The reference uses Terraform across clouds
with cloud-specific modules at the leaf level.

### Hybrid integration patterns (exercise 03)

On-prem + cloud requires explicit connectivity (Direct Connect,
ExpressRoute, Interconnect) and identity bridging. The
deliverable enumerates patterns for synchronous vs. async
integration.

### Cost-comparison model (exercise 04)

Per-workload TCO across clouds, including hidden costs (data
egress, support tiers, professional services). The deliverable
is a spreadsheet model with documented assumptions.

### Migration strategy (exercise 05)

Existing single-cloud to multi-cloud: which workloads move
first, which never move, what the rollback plan is.

## Trade-offs we deliberately accepted

- Multi-cloud has a real ops tax.
- LCD (lowest common denominator) services lose features.
- Architecture team has to maintain N-cloud expertise.

## Common mistakes graders see

1. **Multi-cloud chosen for resilience without a triggering
   event**: doubles cost without value.
2. **Data master ambiguous**: split-brain incidents.
3. **No exit strategy if multi-cloud doesn't pay off**.
4. **Federated identity not designed; manual sync forever**.

## When to go beyond this implementation

- Consider **sovereign-cloud** specifics (China cloud, Govcloud).
- Move to **multi-region single-cloud** if the requirement is
  geographic, not vendor.

## Related curriculum touchpoints

- ``senior-engineer/mod-205-multi-cloud`` — the engineering
  view.
- ``architect/projects/project-302-multicloud-infra`` — the
  user-facing project.
