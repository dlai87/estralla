# Kubernetes — Reference Implementation

This document describes the Kubernetes layout of the Enterprise MLOps Platform:
namespace structure, multi-tenancy boundaries, the platform components running
in-cluster, and the conventions every service follows.

For the running examples (e.g. the MLflow deployment manifest), see
[`../../reference-implementations/kubernetes/`](../../reference-implementations/kubernetes/).
This document is the design intent the manifests implement.

Cross-references: [ADR-003](../../architecture/adrs/003-multi-tenancy-design.md)
multi-tenancy, [ADR-007](../../architecture/adrs/007-security-compliance-architecture.md)
security, [ADR-008](../../architecture/adrs/008-kubernetes-distribution.md) EKS
distribution, [process view](../../architecture/views/README.md#2-process-view)
runtime topology.

## Cluster baseline

| Concern | Choice |
|---|---|
| Distribution | EKS 1.30 (managed control plane), `kubeadm`-style is out of scope |
| Node provisioning | Karpenter 1.0 (Cluster Autoscaler retired in our environment) |
| Container runtime | containerd 1.7, image GC tuned |
| CNI | VPC CNI + Cilium (Cilium for NetworkPolicy + Hubble flow logs; VPC CNI for ENI assignment) |
| Service mesh | Istio 1.22 — **ambient mode** by default, sidecar mode opt-in for L7 policy workloads |
| Ingress | AWS Load Balancer Controller → ALB (Istio ingress gateway behind it) |
| DNS | CoreDNS 1.11 (default), with `cluster-local` zone for in-cluster service discovery |
| Storage | EBS CSI (gp3 default), EFS CSI for shared notebook home dirs, S3 mountpoint for read-only training data |
| Secrets | External Secrets Operator → AWS Secrets Manager (via IRSA) |
| Policy | Kyverno (in-tree validation/mutation), OPA Gatekeeper (legacy, being phased out) |
| GitOps | Argo CD 2.11 with App-of-Apps + ApplicationSet generators |
| Observability | Prometheus + Thanos + Grafana + Loki + Tempo (see [`../monitoring/README.md`](../monitoring/README.md)) |

We **do not** run the Kubernetes Dashboard. All cluster access is via
`kubectl` with `aws eks update-kubeconfig` for engineers (read-only by
default, JIT-elevated to write through `tf-iam-jit`) and via the Platform API
for end users.

## Namespace map

The cluster has ~60 namespaces in production. They fall into four classes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Platform namespaces (managed by platform team, ArgoCD-controlled)       │
├─────────────────────────────────────────────────────────────────────────┤
│  kube-system, kube-public, kube-node-lease   (Kubernetes core)           │
│  istio-system, istio-ingress                 (service mesh)              │
│  cilium                                       (CNI policy)               │
│  karpenter                                    (autoscaler)               │
│  cert-manager                                 (TLS issuance)             │
│  external-secrets                             (secret sync)              │
│  argocd, argo-workflows, argo-rollouts        (GitOps + workflows)       │
│  external-dns                                 (DNS)                      │
│  aws-load-balancer-controller                                            │
│  kyverno                                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Platform service namespaces                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  platform-control                            (Platform API, Governance)  │
│  mlflow                                       (tracking + registry)      │
│  feast                                        (feature server, registry) │
│  kubeflow, kubeflow-pipelines                                            │
│  kserve                                       (controller + webhook)     │
│  jupyterhub                                                               │
├─────────────────────────────────────────────────────────────────────────┤
│  Observability namespaces                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  monitoring        (Prometheus, Alertmanager, Thanos sidecars)           │
│  logging           (Loki, Promtail/Vector)                               │
│  tracing           (Tempo)                                                │
│  grafana                                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Tenant namespaces (per team, isolated)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  tenant-risk, tenant-recommendations, tenant-search, tenant-marketing,   │
│  tenant-fraud, tenant-personalization, tenant-pricing, tenant-healthcare,│
│  …                                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Shadow namespaces (per tenant, for canary inference services)           │
├─────────────────────────────────────────────────────────────────────────┤
│  tenant-risk-canary, tenant-fraud-canary, …                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Label conventions

Every namespace and every workload carries a consistent label set. These drive
RBAC, network policy, cost allocation, and observability filters.

| Label | Required on | Values | Purpose |
|---|---|---|---|
| `app.kubernetes.io/name` | Workloads | service name | Standard K8s convention |
| `app.kubernetes.io/component` | Workloads | `api` / `worker` / `db` / `cache` | Component within an app |
| `app.kubernetes.io/managed-by` | Workloads | `argocd` / `helm` | Owner |
| `app.kubernetes.io/version` | Workloads | semver or `git-sha` | Released version |
| `app.kubernetes.io/part-of` | Workloads | high-level system | Grouping in dashboards |
| `mlops.io/tenant` | Tenant ns + workloads in them | `risk`, `fraud`, `healthcare`, … | Tenant attribution |
| `mlops.io/tier` | All namespaces | `platform-system` / `platform-service` / `observability` / `tenant` / `tenant-canary` | RBAC + NetworkPolicy match |
| `mlops.io/data-classification` | Workloads handling data | `public` / `internal` / `pii` / `phi` | Compliance routing |
| `mlops.io/cost-center` | All namespaces | from finance | Chargeback |
| `mlops.io/owner-team` | All namespaces | Okta group name | Paging + escalation |
| `mlops.io/slo-tier` | Workloads with SLO | `1` / `2` / `3` | Alert routing + on-call |

Labels are enforced by a Kyverno policy `require-mlops-labels` (audit mode in
dev, enforce mode in staging+prod). PRs that introduce non-conforming
manifests fail in CI before they reach the cluster.

## Multi-tenancy enforcement

Tenancy is by **namespace**, per ADR-003. The boundaries are layered:

### 1. Identity (who you are)

- Okta group → RBAC ClusterRoleBinding. There is no path to cluster access
  that doesn't start with an Okta SSO session.
- IRSA (IAM Roles for Service Accounts) per tenant. The `tenant-fraud`
  namespace has a service account that assumes
  `arn:aws:iam::...:role/mlops-tenant-fraud` which has S3 access to
  `s3://mlops-data/fraud/` and nothing else.

### 2. RBAC (what you can do)

Each tenant namespace has three roles:

| Role | Bound to | Capabilities |
|---|---|---|
| `tenant-viewer` | Tenant Okta group "view" tier | get/list/watch pods, services, jobs, MLflow CRs |
| `tenant-developer` | Tenant Okta group "dev" tier | + create/update workflows, secrets via ESO, KServe CRs |
| `tenant-admin` | Tenant lead | + modify NetworkPolicy (within tenant ns), modify quotas (read-only on quota in prod) |

No tenant role has any cluster-scoped permission. The `cluster-admin` role is
held by 4 named individuals on the platform team, with break-glass logging.

### 3. Quotas (how much you can consume)

`ResourceQuota` per tenant namespace caps CPU, memory, ephemeral storage,
PVC count, and pod count. `LimitRange` enforces default and max per container.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-fraud
spec:
  hard:
    requests.cpu: "200"
    requests.memory: 800Gi
    requests.nvidia.com/gpu: "8"
    limits.cpu: "400"
    limits.memory: 1600Gi
    persistentvolumeclaims: "50"
    pods: "300"
    services.loadbalancers: "0"   # tenants don't get LBs; ingress via Istio gateway
```

GPU quota is administered through the **GPU quota service**, a custom
controller that knows about cross-tenant borrowing (a tenant with idle GPU
hours can lend; chargeback follows).

### 4. Network policy (who you can talk to)

The cluster has a default-deny NetworkPolicy in every namespace. Tenants then
add explicit `Allow` policies:

- Tenant pods can talk to the Platform API (`platform-control` namespace)
- Tenant pods can talk to MLflow (`mlflow` namespace) — through Platform API in
  practice
- Tenant pods can talk to Feast feature server (`feast` namespace)
- Tenant pods can talk to their _own_ namespace (intra-tenant)
- Tenant pods can be _called by_ Istio ingress gateway (`istio-ingress`)
- Tenant pods **cannot** talk to other tenant namespaces
- Tenant pods can talk to AWS APIs only via VPC endpoints (enforced at the
  IRSA + SCP layer)

Cilium NetworkPolicy is preferred over the in-tree `NetworkPolicy` because we
want L7 rules (e.g., allow GET on `/feast/v1/features/*` but deny POST) for
Platform API → Feast.

### 5. Mesh policy (who the mesh trusts you to talk to)

Istio `PeerAuthentication` mandates STRICT mTLS cluster-wide. Each tenant
has an `AuthorizationPolicy` that mirrors its NetworkPolicy at L7, granting
SPIFFE identities. This is belt-and-suspenders — if NetworkPolicy is
misconfigured, the mesh policy still blocks the call.

### 6. Node isolation (special tenants only)

The `healthcare` tenant runs on a dedicated node pool tainted
`tenant=healthcare:NoSchedule`. Healthcare pods tolerate the taint; nothing
else can be scheduled there. This is per ADR-007 to limit PHI exposure to a
discrete set of nodes.

## Argo CD App-of-Apps

There is **one** root `Application` per cluster. It points to
`gitops-repo/apps/<env>/_root/`. That `_root` is an `ApplicationSet` that
generates one `Application` per service. Sync waves order things:

| Wave | Generates |
|---|---|
| -3 | CRDs (Istio, KServe, Kubeflow, ArgoCD itself) |
| -2 | Cluster-scoped operators (Karpenter, External Secrets, cert-manager, Kyverno) |
| -1 | Cluster policies (Kyverno ClusterPolicies, default NetworkPolicies) |
| 0 | Platform services (MLflow, Feast, Kubeflow control plane, Governance) |
| 1 | Observability (Prometheus, Grafana, Loki, Tempo) |
| 2 | Tenant ApplicationSet generator (per-tenant Apps) |
| 3 | Per-tenant workloads (KServe InferenceServices, Argo Workflows) |

A tenant onboarding is then a PR that adds the tenant to
`gitops-repo/tenants/<env>/<tenant>.yaml`. The ApplicationSet generator
creates everything else.

## External Secrets pattern

We don't put secrets in Git, not even encrypted with SOPS. The pattern is:

1. Terraform creates the AWS Secrets Manager secret and outputs its ARN
2. Operator commits a `SecretStore` + `ExternalSecret` referencing the ARN
3. External Secrets Operator (running with IRSA) pulls the secret and
   materializes a K8s `Secret` in the target namespace
4. Workloads mount the K8s `Secret` like any other

Secrets refresh on a 1-minute interval by default; on rotate, the K8s
`Secret` is updated and we use Reloader to restart consuming pods.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: mlflow-db-credentials
  namespace: mlflow
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: mlflow-db-credentials
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: prod/mlflow/db-credentials
```

## Observability hooks (per-workload requirements)

Every workload _must_:

1. Expose Prometheus metrics on `/metrics` (or set a `prometheus.io/path`
   annotation if non-standard).
2. Emit structured JSON logs to stdout. Promtail/Vector picks them up and ships
   to Loki, parsing the `tenant`, `trace_id`, `level` fields.
3. Propagate W3C traceparent headers. Istio adds them by default at the mesh
   layer.
4. Define an `SLO` CR (custom resource consumed by our SLO generator) if the
   workload has user-facing SLOs.

A workload that fails these checks is caught by a Kyverno policy
`require-observability-baseline` (audit only — we warn but don't block, since
adding metrics to legacy code takes time).

## Capacity profiles (Karpenter NodePools)

Karpenter NodePools defined in Terraform (see
[`../terraform/README.md`](../terraform/README.md)), exposed to workloads via
node selectors and taints:

| Pool | Selector | Taint | Use |
|---|---|---|---|
| `system-on-demand` | `workload=system` | — | Control-plane workloads (Platform API, ArgoCD) |
| `system-spot` | `workload=system, lifecycle=spot` | — | Stateless backend workers |
| `inference-cpu` | `workload=inference-cpu` | — | CPU-bound predictors |
| `inference-gpu` | `workload=inference-gpu` | `nvidia.com/gpu` | L40S inference |
| `training-gpu-spot` | `workload=training-gpu, lifecycle=spot` | `training` | H100 training (Spot OK) |
| `training-gpu-od` | `workload=training-gpu, lifecycle=on-demand` | `training-critical` | H100 training (no Spot reclaim) |
| `healthcare` | `tenant=healthcare` | `tenant=healthcare` | PHI-isolated nodes |

## Upgrade philosophy

- **Control plane** (EKS) upgraded on AWS's cadence, one minor at a time, with
  a two-week staging soak between staging and prod.
- **Node pools** drained one at a time; Karpenter handles consolidation. PDBs
  ensure no SLO violations during drain.
- **Operators** (Istio, KServe, Argo) upgraded via Argo CD, version pin
  bumped in a PR that goes through dev → staging → prod with the same gates as
  application code.
- **CRDs** are pre-applied in sync wave -3, never auto-pruned.

## Anti-patterns we actively prevent

| Anti-pattern | Why it's bad | Enforcement |
|---|---|---|
| `kubectl apply` in prod | Drift, no audit | RBAC: prod cluster has no `write` role for humans except break-glass |
| `:latest` image tag | Non-reproducible rollouts | Kyverno policy `disallow-latest-tag` |
| `cluster-admin` for an app's service account | Lateral movement risk | Kyverno policy `restrict-clusterrole-bindings` |
| HostPath volumes | Node compromise | Kyverno policy `disallow-host-path` |
| Privileged containers | Container escape | Kyverno policy `disallow-privileged-containers` (PSA `restricted` baseline) |
| Tenants depending on cluster-scoped resources | Multi-tenancy break | Namespace-scoped APIs only; ClusterRole bindings reviewed |
| Direct DB access from a notebook | Lineage gap | Feast / Platform API is the only path; DB security groups deny notebook subnets |
| Sidecar injection on training pods | Container restart races kill training | Pods opt-out via `sidecar.istio.io/inject: "false"` annotation, justified by template |

## See also

- [`../monitoring/README.md`](../monitoring/README.md) — observability stack
  detail
- [`../platform-api/README.md`](../platform-api/README.md) — the API that
  tenants interact with instead of `kubectl`
- [`../../runbooks/operations-manual.md`](../../runbooks/operations-manual.md)
  — day-2 ops including upgrades and capacity planning
