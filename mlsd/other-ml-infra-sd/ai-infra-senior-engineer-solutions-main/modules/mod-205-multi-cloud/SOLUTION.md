# SOLUTION — Multi-Cloud

> Read this *after* you have stood up the reference multi-cloud
> infrastructure. This document explains *why* multi-cloud is
> hard, when it's worth it, and how to do it without paying the
> "lowest common denominator" tax.

## What this module is really teaching

Multi-cloud is mostly a tax — extra abstraction, slower iteration,
operational complexity — *unless* you have a concrete reason for
it. The reference solutions teach you to recognize the cases
where multi-cloud is worth the tax and to architect for those
cases specifically.

## Architectural decisions and *why*

### Decision 1: Active/active vs. active/passive vs. federated

The reference distinguishes three multi-cloud patterns:

- **Active/active**: traffic served from all clouds, replicated
  state. Highest cost; highest resilience.
- **Active/passive**: one cloud serves; others on standby.
  Medium cost; recovery requires failover orchestration.
- **Federated**: workloads pinned to clouds by purpose (training
  on AWS, serving on GCP). Lower cost; complex but coherent.

Multi-cloud projects fail when they don't pick which pattern
they're targeting and end up with the worst attributes of all
three.

### Decision 2: Terraform as the unifying interface

The reference uses Terraform across all clouds, with provider-
specific modules composed at the stack layer. The reason:
Terraform's syntax is identical across clouds; the resources
aren't. Hiding the differences (multi-cloud abstraction layers)
produces lowest-common-denominator interfaces; exposing them
keeps optionality.

### Decision 3: Data-tier multi-cloud is the hard part

Compute multi-cloud is straightforward; data multi-cloud is
where it breaks. The reference advice: pick one cloud as the
data master and replicate to others. Multi-master is research-
grade territory and the reference doesn't try.

### Decision 4: Network connectivity via dedicated interconnect

For active/active or federated patterns, the reference uses
Direct Connect / Cloud Interconnect / ExpressRoute — not
public-internet VPNs. The reason: data transfer costs at scale
make VPN economics worse than dedicated lines after a couple
TB / month.

### Decision 5: Per-cloud identity, not federated

The reference uses each cloud's IAM directly, with a sync layer
(SCIM, Okta) for human identity. We don't try to make one
cloud's IAM authoritative for another's resources. The reason:
each cloud's IAM is best-of-breed for that cloud; trying to
federate creates a translation layer nobody can debug.

## Trade-offs we deliberately accepted

### Higher operational cost

Multi-cloud doubles many ops surfaces (monitoring, IAM,
networking). The reference is explicit about this: don't go
multi-cloud unless the benefits justify the doubled ops.

### Slower iteration

Every new feature has to ship on N clouds. Iteration speed drops
30-50% in multi-cloud orgs.

### Cloud-specific runbooks

The reference maintains separate runbooks per cloud rather than
generic runbooks. Cloud APIs differ in subtle ways that produce
different incident shapes.

## Common mistakes graders see

1. **"Multi-cloud ready" architecture for a single-cloud
   deployment**: pays the tax without using the benefit.
2. **Lowest-common-denominator services**: refusing to use S3
   intelligent tiering because GCS lacks an exact equivalent.
3. **Data replication without a master**: split-brain incidents.
4. **One cloud's IAM as the source of truth**: the second
   cloud's IAM is now manually managed and drifts.
5. **No cost attribution per cloud**: the multi-cloud bill is a
   mystery for years.

## When to go beyond this implementation

- Consider **sovereign-cloud requirements** (data residency)
  that mandate multi-cloud in specific regions.
- Adopt **multi-region single-cloud** before multi-cloud —
  often delivers most of the resilience benefit at a fraction
  of the complexity.

## Related curriculum touchpoints

- ``engineer/mod-102-cloud-computing`` — single-cloud
  foundations.
- ``architect/projects/project-302-multicloud-infra`` — the
  architect-level companion.
- ``senior-engineer/mod-208-iac-gitops`` — managing the IaC
  surface across clouds.
