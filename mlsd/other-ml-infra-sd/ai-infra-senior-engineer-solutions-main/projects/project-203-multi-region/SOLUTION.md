# SOLUTION — Multi-Region ML Platform

> Read this *after* attempting the learning-side project.

## What problem this solves

A multi-region platform answers four operational questions a
single-region platform cannot:

1. **What's the latency floor for a user in Mumbai?** — bounded by
   geography, not engineering.
2. **What happens if `us-west-2` goes dark for 4 hours?** — single
   region = single point of failure for the whole company.
3. **Are we compliant with regional data-residency requirements?** —
   answered by *where data lives*, not by where compute runs.
4. **Are we paying $X to a single vendor we cannot replace?** —
   negotiation leverage and vendor risk.

This project addresses (1)–(3). Vendor leverage (4) is an
architecture-track concern; see `architect-solutions/project-302`.

## Architectural decisions and *why*

### Active-active across **regions** (within a cloud), active-passive
across **clouds**

Cross-region active-active within a single cloud (EKS in two AWS
regions) is operationally well-understood and reasonably cheap.
Cross-cloud active-active is expensive, hard to operate, and rarely
necessary. The reference uses cross-region active-active within each
cloud, and cross-cloud only as planned failover.

### DNS-based global routing (Route53 latency / geo policies), not
service-mesh global routing

Global Anycast service meshes exist but are expensive, brittle, and
add a third concept (global mesh) you have to operate. DNS-based
routing is well-understood, cheap, and good enough for sub-second
latency-class workloads.

### Data replication tier'd by classification, not "everything
everywhere"

Replicating *everything* to every region multiplies storage cost
without serving most use cases. The reference replicates regulated
data per residency rules, hot-path features globally, and cold data
back to a single archival region.

### Cost optimization via right-sizing per region, not RI everywhere

Reserved Instances reduce cost for stable baseline, but a region that
peaks 4 hours a day shouldn't be RI-heavy. The reference picks
RI/spot/on-demand per region based on the regional traffic shape.

### Unified monitoring via federated Prometheus with regional
long-term storage

A single global Prometheus is a single point of failure. Federated
Prometheus (regional Prometheus pushing aggregates to a global
viewer) preserves per-region durability while giving a single pane of
glass.

## How to read the code

Execution-order reading path:

1. Terraform for per-region cluster setup (note shared modules with
   per-cloud overlays).
2. Cross-region replication topology — what travels where, what
   doesn't.
3. DNS routing policies and failover triggers.
4. Federated Prometheus configuration.
5. Failover runbook — the most important artifact.

## What's deliberately simplified

- **No cross-cloud active-active.** Cross-cloud is planned failover
  only.
- **No global consensus store.** Each region is independent; no
  cross-region strongly-consistent writes are assumed.
- **No cross-region streaming.** Streams are regional; cross-region
  data exchange is batch-only.
- **No regulatory compliance certification.** GDPR / CCPA / PIPL are
  *supported* by the design, not *certified*.

## Cross-references

| Topic | Deeper reference |
|---|---|
| Architecture-level multi-cloud reasoning | `architect-solutions/projects/project-302-multicloud-infra/` |
| Terraform module patterns | `engineer-solutions/mod-109` |
| GitOps multi-env promotion | `engineer-solutions/mod-109 exercise-10` |
| Federated observability | `senior-engineer-solutions/modules/` (per-module exercises) |

## Production gap checklist

- [ ] Documented regional RTO/RPO commitments with monitoring
- [ ] Cross-cloud DR drill cadence (quarterly)
- [ ] Egress-cost monitoring with per-workload attribution
- [ ] Regulated-data residency audit (run periodically by compliance,
      not just engineering)
- [ ] Tested rollback paths for each Terraform module
- [ ] Capacity headroom per region sufficient to absorb regional
      failure of any one peer

## Time budget

- **Skim**: 1 hour.
- **Deep**: 2–3 weeks — run a planned failover end-to-end, measure
  the *actual* RTO/RPO, compare to the documented commitment.
