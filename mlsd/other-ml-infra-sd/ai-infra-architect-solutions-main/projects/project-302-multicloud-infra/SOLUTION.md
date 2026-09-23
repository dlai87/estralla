# SOLUTION — Multi-Cloud AI Infrastructure

> Read this *after* attempting the learning-side project. This file
> explains the architectural reasoning. Most "multi-cloud" architectures
> in the wild are *also-cloud* architectures that pay the multi-cloud
> tax without getting the multi-cloud benefit; this file is honest about
> when that happens and what you can do about it.

## What an architect is actually being asked to defend

The brief asks for multi-cloud, but the *real* architectural question
is: which of the following four motivations is driving the design?

1. **Regulatory** — data residency rules force you into a specific
   cloud in a specific region.
2. **Risk** — single-vendor concentration risk for a critical workload.
3. **Best-of-breed** — a specific service (e.g. Vertex AI, Bedrock) is
   materially better for a specific workload.
4. **Negotiation leverage** — being credibly able to move makes vendors
   sharpen their pencils.

These four require different architectures. (1) tolerates per-cloud
"islands." (2) demands true workload portability. (3) accepts that
workloads are pinned per cloud. (4) just needs the *capability* to
move, exercised occasionally.

The reference design here primarily addresses (1) and (2). Read the
architecture's "Goals" section first; if your situation is mostly (3)
or (4), the trade-offs shift.

## Key architectural decisions and *why*

### 1. Kubernetes as the portability layer (not "all native services")

Every cloud offers a managed Kubernetes (EKS, GKE, AKS). The
abstraction the platform exposes — pods, services, persistent volumes —
is identical across them. Native services (SageMaker, Vertex,
Azure ML) are *not* used as the primary compute abstraction; they
appear behind adapters when (3) above is the motivation.

Trade-off: you give up some "best-of-breed" capability. Each adapter
adds a maintenance surface.

### 2. Terraform as the IaC layer, with cloud-specific modules

Terraform's provider model accepts that the underlying APIs differ.
Pretending the clouds are isomorphic (with Crossplane abstractions or
a single multi-cloud DSL) usually fails: the abstraction either leaks
or covers only the lowest common denominator. The reference design
uses per-cloud modules with consistent *interfaces*.

### 3. Data residency = data lakes per region with replication
policies, not a globally distributed store

Globally consistent storage across clouds is a hard, expensive
problem. Most regulatory requirements only require that data stays
*in region*, not that compute follows users globally. The design uses
regional data lakes with explicit replication rules (encrypted, with
cross-cloud signing).

### 4. Active-active per cloud, not active-active across clouds

Cross-cloud active-active is technically possible but extremely
expensive operationally (network egress, consistency, drift). Per-cloud
active-active gives you the resilience you usually need; cross-cloud
failover is exercised as a planned drill, not a real-time path.

### 5. Cost mix (RI 70%, spot 20%, on-demand 10%) is a *starting*
position, not a target

The 70/20/10 mix in the project's numbers is a reasonable mature
default. Brand-new workloads should run on-demand until usage
stabilizes; spot allocations require fault-tolerant training code; RIs
require trustworthy demand forecasts. Treat the mix as the *outcome*
of doing the work, not as a target.

## How to read the deliverable

1. **`ARCHITECTURE.md`** — the engineering deliverable. Pay attention
   to the "Goals" / "Non-goals" section: this design is honest about
   what multi-cloud is and isn't buying you.
2. **`reference-implementation/`** — Terraform skeletons and
   adapter-pattern code.
3. **`governance/`** — data-residency policy as code, cross-cloud audit
   chain.
4. **`business/`** — the cost model and the SLA framework.

## What's deliberately *not* in scope

- **No "one pane of glass" for cross-cloud operations.** That promise
  is usually unkept. Per-cloud operational tooling with consistent
  *metrics* is what the reference design ships.
- **No cross-cloud training jobs.** Training crosses cloud boundaries
  only via offline data sync. Real-time cross-cloud training is a
  research problem, not an enterprise deliverable.
- **No promise that "cloud-agnostic" means zero per-cloud expertise.**
  Operating on three clouds means employing engineers who know all
  three; the design doesn't make that go away.

## Production gap checklist

- [ ] Independent verification of the cost-savings figures against
      historical billing data
- [ ] Cross-cloud DR drill cadence (quarterly at minimum)
- [ ] Egress-cost monitoring with per-workload attribution
- [ ] Per-region capacity quotas with automatic alerting on quota
      consumption
- [ ] Cross-cloud identity federation (one identity, three providers)
      that survives auditor review
- [ ] Tested rollback paths for each Terraform module
- [ ] Sovereign-cloud variant evaluation (China / India / Russia
      depending on your customer footprint)
- [ ] Contractual remedies aligned with the SLA framework (uptime SLAs
      are uninteresting without commercial remedies)

## Reading order across the curriculum

| Phase | Read this |
|---|---|
| Implementation references | `ai-infra-engineer-solutions/mod-109` (Terraform, GitOps, policy) |
| Tenancy implications | `ai-infra-ml-platform-learning/lessons/mod-001-platform-fundamentals/lecture-notes/03-multi-tenancy-patterns.md` |
| Cost engineering | `ai-infra-engineer-solutions/mod-104 ex-15` |
| Multi-cluster operations | `ai-infra-senior-engineer-solutions/mod-104` |

## Time budget for studying this solution

- **Executive read**: 90 min.
- **Engineering read**: 2 days, plus drawing your own architecture
  with the four motivations (regulatory / risk / best-of-breed /
  leverage) ranked for *your* environment.
- **Adoption read**: 3–4 weeks to run the Terraform modules in two
  clouds, measure egress costs honestly, and decide which of the four
  motivations actually applies.
