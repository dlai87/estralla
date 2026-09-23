# SOLUTION — Enterprise MLOps Platform Architecture

> Read this *after* attempting the learning-side project. This file
> explains the architectural reasoning behind the reference design and
> the trade-offs that produced it. The deliverable is an *architecture*
> — not a running system — so the focus here is on the decisions, not
> the code.

## What an architect is being asked to do

The brief is a platform supporting ~100 data scientists across ~20
teams, with governed, auditable lifecycle management end-to-end. The
hard part is not any single technical choice — it's keeping the
following properties true *simultaneously*:

1. **Self-service for data scientists** (otherwise the platform team
   becomes the bottleneck).
2. **Strong tenancy** (one team's experiment cannot starve another).
3. **Defensible governance** (every artifact has provenance, every
   prediction has lineage, every action is auditable).
4. **Cost attributable** (you cannot defend a $15M build without
   chargeback that survives finance scrutiny).

If you weaken any of these, the design unravels at scale.

## Key architectural decisions and *why*

### 1. Self-service at the *interface* layer, not the *infrastructure* layer

The platform exposes higher-order primitives ("submit a training run",
"register a model", "deploy v2 to staging") — not Kubernetes objects.
This is the single most important decision in the whole design. If data
scientists are writing pod specs, you do not have a platform, you have
a Kubernetes cluster with extra steps.

The interface layer is implemented as a control plane API (REST + gRPC)
with a Python SDK on top. The control plane translates platform intents
to Kubernetes objects and stamps every action with tenancy and
provenance metadata.

### 2. Multi-tenancy via *namespace per team* + Kueue cohorts

Hard tenancy (cluster per team) is too expensive at 20 teams. Soft
tenancy (single namespace, RBAC-only) leaks: a runaway training job
will saturate node-local resources. The middle ground is namespace per
team with Kueue cohorts for fair-share queueing.

This trades absolute isolation for operational simplicity. The
*compliance* gaps it leaves (kernel-shared, network policies are
defense-in-depth not airtight) are explicitly listed in the gap
checklist below.

### 3. Two-plane data architecture

Feature data and model artifacts live in different stores with
different retention models. Features are heavily versioned with
point-in-time correctness; model artifacts are append-only with signed
lineage back to a feature snapshot ID. This separation matters because
the regulated questions ("can you reproduce this prediction?") need
both planes to answer.

### 4. Cost attribution via per-namespace OpenCost + per-run tagging

Per-team Kubernetes cost attribution is well-understood. Per-*run*
attribution is harder — a single tenant's training job consumes GPU
time across nodes. The reference design tags every workload with
`platform/run-id` at admission and aggregates GPU-hour cost back through
OpenCost. This lets finance see "Team X's experimentation cost in Q2".

### 5. Defer the "platform UI" decision

The architecture deliberately leaves the developer-facing UI to a
later phase. Building a UI before the API is stable is the most common
way platform teams produce a UI nobody uses. The API+SDK is the
contract; UIs (CLI, web, notebook integration) follow.

## How to read the deliverable

The architecture package is multi-document on purpose; auditors,
engineers, and executives read different things.

1. **`README.md`** — the executive narrative.
2. **`ARCHITECTURE.md`** — the *engineering* deliverable: components,
   contracts, data flows.
3. **`reference-implementations/`** — partial implementations of the
   most-contested decisions (so they can be prototyped without
   committing to them).
4. **`runbooks/`** — operations-level documentation that proves the
   design is operable, not just buildable.
5. **`governance/`** — policy-as-code skeletons and the audit-trail
   contract.
6. **`business/`** and **`stakeholder-materials/`** — what gets shown
   in funding reviews and steering committees.

If you read only one section, read `ARCHITECTURE.md`. Everything else
amplifies it.

## What's deliberately *not* in scope

- **No tool brand lock-in beyond reasonable defaults.** The design
  names MLflow / Feast / Kueue / Vault as defaults, but every choice
  has a `## Alternatives considered` paragraph. The architecture
  survives substitution.
- **No promise that the cost figures will replicate.** The "$30M NPV"
  number is a *defensible* number derived from the included
  assumptions sheet. A real enterprise will plug in its own numbers
  and get a different result.
- **No execution plan for the org-change side.** Platform-engineering
  adoption is half the work; that lives in the leadership tracks.

## Production gap checklist

- [ ] HSM-backed root of trust for signing identities (artifacts and
      attestations)
- [ ] Multi-region active-active control plane (the design as drawn is
      regional)
- [ ] Differential privacy budget accounting if any feature derives
      from regulated PII
- [ ] Continuous compliance scanning (not just admission-time)
- [ ] Tenant-level disaster-recovery contracts (RPO/RTO per tenant
      tier, not just per cluster)
- [ ] Independent auditor's review of the audit chain implementation
- [ ] Capacity-planning model that connects the cost projections back
      to scaling triggers
- [ ] Procurement-validated benchmark numbers for the GPU SKUs assumed
      in the cost model

## Reading order across the curriculum

| Phase | Read this |
|---|---|
| Setting context | `ai-infra-architect-learning/projects/project-301-enterprise-mlops/` |
| Implementation reference | `ai-infra-engineer-solutions/mod-105` (pipelines), `mod-106` (deployment) |
| Governance internals | `ai-infra-mlops-learning/projects/project-4-governance/` |
| Cost attribution | `ai-infra-engineer-solutions/mod-104 ex-15` |
| Tenancy patterns | `ai-infra-ml-platform-learning/lessons/mod-001-platform-fundamentals/lecture-notes/03-multi-tenancy-patterns.md` |

## Time budget for studying this solution

- **Executive read**: 90 min — `README.md`, executive summary in
  `ARCHITECTURE.md`, stakeholder slides.
- **Engineering read**: 1–2 days — full `ARCHITECTURE.md`, walk every
  reference implementation, trace one end-to-end data flow.
- **Adoption read**: 1–2 weeks — re-derive the cost model with your
  own assumptions, identify the three decisions you would change for
  your environment, document why.
