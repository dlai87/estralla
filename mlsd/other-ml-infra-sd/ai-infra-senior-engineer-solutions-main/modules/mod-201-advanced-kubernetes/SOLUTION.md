# SOLUTION — Advanced Kubernetes

> Read this *after* you have built the reference resources on a real
> cluster. This document explains *why* the advanced K8s patterns
> are what they are.

## What this module is really teaching

Engineer-tier K8s (mod-104) is "ship a stateless service safely."
Senior-tier is **operating shared clusters as a platform team**:

- Multi-tenant isolation that's actually enforced.
- Cluster API and operator-pattern resources.
- Admission control that catches bad configurations before they
  reach the cluster.
- Cluster upgrade strategies that don't take down workloads.

## Architectural decisions and *why*

### Decision 1: Operators for non-trivial stateful workloads

For workloads like Postgres, Kafka, or Spark, the reference uses
the upstream operator (Zalando, Strimzi, spark-operator) rather
than hand-managed StatefulSets. The reason: stateful workloads
need rolling-rotation, backup, restore, and failover logic. The
operator encodes this once; hand-managed StatefulSets reinvent
it badly.

### Decision 2: Admission control via Kyverno or OPA Gatekeeper

Cluster-wide policy is enforced at admission, not at PR review.
The reason: PR-time review is human; admission is deterministic.
Policies like "no ``hostNetwork``", "all images from approved
registries", "every Deployment has a PDB" become impossible to
violate.

### Decision 3: NetworkPolicy + Cilium for tenant isolation

Network isolation between namespaces is enforced via
NetworkPolicy resources, with Cilium as the CNI. The reason:
NetworkPolicy alone requires a CNI that actually enforces it
(Calico, Cilium); some popular CNIs treat them as advisory.

### Decision 4: Cluster Autoscaler + Karpenter for node management

The reference combines the standard Cluster Autoscaler for the
general node pool with Karpenter for specialized workloads (GPU,
ARM, spot). Karpenter's flexible provisioning is the right
answer for ML workloads; CAS handles the stable baseline.

### Decision 5: Multi-cluster federation via Argo CD App-of-Apps

Cluster bootstrapping uses Argo CD's app-of-apps pattern, with
one Argo CD per cluster managing local resources, and a central
Argo CD managing the per-cluster Argo CDs. The reason: a single
control-plane Argo CD becomes a single point of failure at
scale.

## Trade-offs we deliberately accepted

### Vanilla Kubernetes, not OpenShift / Rancher

The reference uses upstream Kubernetes plus selected add-ons.
Distributions add opinions (some good, some bad); learning the
patterns at the upstream level transfers.

### Cilium over Calico

Cilium's eBPF data plane is more capable and modern. Calico
remains a reasonable choice but is the conservative pick.

### Single-mesh service-mesh decision deferred

The reference doesn't pick a service mesh (Istio / Linkerd /
Cilium Service Mesh). The reason: service meshes add real
operational cost; deferring the decision until the team has a
concrete need is correct.

## Common mistakes graders see

1. **Operators installed without RBAC review**: the operator's
   service account often has cluster-wide read or write on
   secrets.
2. **No PDB on the operator itself**: the operator gets evicted
   during a node drain and stateful workloads stall.
3. **Cluster Autoscaler with mixed node types in one pool**:
   produces unpredictable scaling. Use separate pools.
4. **Kyverno / OPA in audit mode forever**: policies are
   defined but never enforced. Move to enforce mode.
5. **No version skew policy**: nodes and control plane drift
   across multiple minor versions and upgrades become painful.

## When to go beyond this implementation

- Adopt **Cluster API** for cluster lifecycle management.
- Add **vCluster** for cheap per-tenant clusters within a parent.
- Move to **multi-cluster GitOps** with Argo CD ApplicationSets.

## Related curriculum touchpoints

- ``engineer/mod-104-kubernetes`` — the foundation.
- ``senior-engineer/mod-208-iac-gitops`` — declarative cluster
  management.
- ``ml-platform/mod-003-multi-tenancy-resources`` — multi-tenancy
  at the platform layer.
