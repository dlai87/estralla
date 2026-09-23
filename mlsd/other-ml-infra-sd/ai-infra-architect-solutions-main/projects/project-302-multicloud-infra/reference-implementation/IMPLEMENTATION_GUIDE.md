# Multi-Cloud AI Infrastructure — Implementation Guide

**Owner**: Cloud Architecture + Platform Engineering
**Status**: v1 (matches the v1.0 architecture described in `ARCHITECTURE.md` and ADR-001 through ADR-005)
**Audience**: Platform engineers implementing or extending the reference architecture
**Reading order**: After `ARCHITECTURE.md`, ADR-001 through ADR-005, and `architecture/governance/data-residency-matrix.md`

This guide is the **executable interpretation** of the multi-cloud architecture: bootstrap order, module layouts, identity wiring, networking topology, observability fan-in, and verification at each stage. It is opinionated. Where it disagrees with a general blog post, prefer this guide — the rationale is in the ADRs.

---

## 1. Topology recap

Three clouds, four pillars per cloud, one shared control plane:

```
                       ┌──────────────────────────────────────┐
                       │   Shared control & policy plane      │
                       │   - Crossplane (mgmt cluster)        │
                       │   - Argo CD ApplicationSets          │
                       │   - Vault (HA, per region)           │
                       │   - SPIRE root (cross-cloud trust)   │
                       │   - Sloth + Thanos federation        │
                       └────────────┬─────────────────────────┘
                                    │
   ┌────────────────────────────────┼────────────────────────────────┐
   ▼                                ▼                                ▼
┌────────┐                     ┌────────┐                       ┌────────┐
│  AWS   │                     │  GCP   │                       │ Azure  │
│ EKS    │                     │ GKE    │                       │ AKS    │
│ S3,RDS │                     │ GCS,   │                       │ Blob,  │
│ DDB    │                     │ BQ,    │                       │ Cosmos │
│ IAM    │                     │ AlloyD │                       │        │
│ Direct │                     │ Cloud  │                       │ Expr.  │
│ Connect│                     │ Inter. │                       │ Route  │
└────┬───┘                     └────┬───┘                       └────┬───┘
     │           Megaport ECX Fabric (Ashburn, Frankfurt, Singapore)│
     └─────────────────────────────┴─────────────────────────────────┘
```

The remainder of this guide walks the bootstrap from nothing to the first end-to-end inference call routed cross-cloud.

---

## 2. Bootstrap order (Day 0 → Day 30)

### Stage 0 — accounts, projects, subscriptions

- AWS: a 3-tier Org (root → security OU → workload OUs). `prod-platform`, `prod-data`, `nonprod`, `security`, `network`, `logs` accounts created via AWS Control Tower customizations
- GCP: a 3-tier Org (folders → environments → projects). `acme-platform-prod`, `acme-platform-nonprod`, `acme-data-prod`, `acme-network`, `acme-security`, `acme-logs`
- Azure: a single tenant in Microsoft Entra; subscriptions `acme-platform-prod`, `acme-platform-nonprod`, `acme-data-prod`, `acme-network`, `acme-security`, `acme-logs`; management groups mirror the AWS OU shape

Naming is identical across clouds where the cloud allows it (some characters differ). Tags are normalized via the same `acme:*` keys.

### Stage 1 — identity hub

1. Stand up **Microsoft Entra ID** as the workforce identity hub.
2. Configure SSO into AWS (IAM Identity Center), GCP (Cloud Identity sync via SCIM), and Azure (native).
3. Create Entra groups mapped 1:1 to cross-cloud roles (`platform-sre`, `platform-admin`, `data-engineer`, etc.). Group-to-cloud-role maps live in `infra/identity/`.

### Stage 2 — federated identity (workloads)

This is the foundation of "no long-lived cloud credentials anywhere." We use **OIDC + WIF** end to end:

- **GitHub Actions** → all three clouds via OIDC token exchange (no static keys for any pipeline)
- **AWS workloads → GCP**: GCP Workload Identity Federation with AWS as the OIDC issuer (`https://oidc.eks.*.amazonaws.com/...` or the AWS STS OIDC)
- **GCP workloads → AWS**: AWS IAM OIDC provider for Google's token issuer; assume-role with web identity
- **Azure workloads → AWS/GCP**: Workload Identity Federation in Entra; AWS or GCP trusts the Entra tenant's OIDC issuer
- **In-cluster**: IRSA on EKS, Workload Identity on GKE, Workload Identity on AKS — these are the *last mile* identities; cross-cloud calls happen via the federation layer above

Bootstrap recipe — example: a GKE pod needs to read an S3 bucket in the same account:

```yaml
# 1) In GCP: bind a Google SA to a K8s SA via Workload Identity
gcloud iam service-accounts add-iam-policy-binding \
  acme-sa@acme-platform-prod.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member='serviceAccount:acme-platform-prod.svc.id.goog[mlops/inference]'

# 2) In AWS: trust GCP's OIDC issuer
aws iam create-open-id-connect-provider \
  --url https://accounts.google.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list <fingerprint>

# 3) In AWS: create role with trust policy on the GCP SA's `sub` claim
#    (uniqueId of the Google SA), allow s3:GetObject on the bucket
```

The pod calls AWS STS `AssumeRoleWithWebIdentity` using its GCP-issued ID token. No static credentials on either side.

### Stage 3 — network spine

We pre-build the network before any workload lands. See §5 for full topology.

1. Megaport ports provisioned in Ashburn, Frankfurt, Singapore (10 Gbps each)
2. AWS Direct Connect Dedicated Connection from each Megaport port to AWS Direct Connect Gateways in `us-east-1`, `eu-central-1`, `ap-southeast-1`
3. GCP Cloud Interconnect (Dedicated) similarly to `us-east4`, `europe-west4`, `asia-southeast1`
4. Azure ExpressRoute similarly to `eastus2`, `westeurope`, `southeastasia`
5. Hub-and-spoke per cloud: a `network` account/project/subscription holds the transit VPC/VPC/VNet; workload VPCs/VNets peer in
6. Cross-cloud routes via Megaport VXC (one per cloud pair × region pair); BGP advertised, RFC 1918 with non-overlapping CIDRs

### Stage 4 — secrets and PKI

1. Stand up **HashiCorp Vault** in a 3-node HA cluster per region per cloud (so 9 clusters in steady state). Auto-unseal via the cloud-native KMS in that region.
2. Cross-cloud Vault federation is intentionally **not** used; secrets are tenant- and region-scoped and replicated only where compliance allows.
3. **SPIRE** root server runs in the management cluster; per-cloud SPIRE upstream-authority servers chain to the root; per-cluster SPIRE agents issue SVIDs to workloads. This gives a single SPIFFE trust domain `spiffe://acme.io/` across clouds.
4. cert-manager in every cluster issues TLS certs via Let's Encrypt (public) and Vault PKI (internal).

### Stage 5 — management Kubernetes cluster

A single management cluster (the "mgmt cluster") hosts the control plane shared across clouds. It runs on AWS `us-east-1` for latency to our HQ; a warm standby is in GCP `us-central1`. Components:

- Crossplane v1.16+ with providers for AWS, GCP, Azure, Vault, GitHub
- Argo CD v2.12+ with one ApplicationSet per cluster
- Vault (replica)
- SPIRE root
- Sloth, Prometheus + Thanos receive (federation hub)
- Backstage developer portal

This cluster is itself bootstrapped via OpenTofu (see §3). After it exists, *everything else* is reconciled into it as code.

### Stage 6 — workload clusters

For each cloud × region:

1. OpenTofu creates the cluster (EKS / GKE / AKS) + node pools
2. The cluster is registered with Argo CD as a destination
3. ApplicationSets target the cluster with the right overlay (`overlays/aws-use1-prod`, etc.)
4. Initial sync brings up: cert-manager, ESO, Vault agent injector, SPIRE agent, Istio, ingress, OTel collectors, KEDA, Karpenter (AWS) / equivalents (GCP, Azure), metrics-server, kube-state-metrics
5. Smoke: a "hello-world" deployment that hits a cross-cloud endpoint via SPIFFE-authenticated mTLS

### Stage 7 — data plane

- S3 buckets in AWS (data-prod account), with replication policies per region
- GCS buckets in GCP (data-prod project)
- Blob storage in Azure
- Aurora clusters in AWS (region-specific); AlloyDB in GCP for the migrated workload; Cosmos DB in Azure for the global workload
- BigQuery dataset created in GCP for cross-cloud analytics; external tables federate to S3 and ADLS
- Snowflake account established with cross-cloud replication enabled

### Stage 8 — observability fan-in

- Per-cluster OTel collectors send to per-region Thanos Receive, Loki distributor, Tempo distributor
- Region-level read tier (Thanos Query, Loki Query Frontend, Tempo Query Frontend) federates upward to the mgmt cluster's read federation
- Grafana in the mgmt cluster sees all clouds in one panel

### Stage 9 — policy and compliance

- OPA Gatekeeper installed in every cluster with the same policy bundle
- Cloud Custodian scheduled in each cloud for drift detection
- Macie / DLP API / Purview enabled per residency requirements

### Stage 10 — first real workload

A pilot tenant lands. Their training runs on GCP (TPU), their inference runs on AWS (cost) and Azure (EU residency), their analytics on Snowflake. The cross-cloud path is exercised end to end and characterized.

This is Day 30. After Day 30 the implementation is incremental — new tenants, new regions, new services.

---

## 3. OpenTofu module structure

OpenTofu (Terraform fork) is the primary IaC. We keep three layers:

```
infra/
├── modules/
│   ├── _shared/
│   │   ├── tagging/         # acme:* tag standard
│   │   ├── naming/          # cluster, bucket, network naming
│   │   └── policy/          # OPA bundles, residency guards
│   ├── aws/
│   │   ├── network/         # transit gateway, VPC, subnets, route propagation
│   │   ├── eks/             # EKS cluster + Karpenter
│   │   ├── s3/              # standard S3 with CMK, lifecycle, replication
│   │   ├── aurora/
│   │   ├── iam/             # roles, OIDC providers (incl. for GCP / Azure / GH)
│   │   ├── direct-connect/
│   │   └── vault-bootstrap/
│   ├── gcp/
│   │   ├── network/         # shared VPC, Cloud Router, Cloud Interconnect attachments
│   │   ├── gke/
│   │   ├── gcs/
│   │   ├── alloydb/
│   │   ├── iam/             # WIF, service accounts
│   │   └── cloud-interconnect/
│   └── azure/
│       ├── network/         # vnet, hub-spoke, ExpressRoute gateway
│       ├── aks/
│       ├── blob/
│       ├── cosmosdb/
│       ├── identity/
│       └── expressroute/
└── envs/
    ├── prod/
    │   ├── aws-use1/
    │   │   ├── main.tf      # composes modules
    │   │   ├── backend.tf   # remote state in S3 + DDB lock
    │   │   └── tfvars
    │   ├── aws-use2/
    │   ├── aws-euw1/
    │   ├── gcp-us-central1/
    │   ├── gcp-europe-west4/
    │   ├── azure-eastus2/
    │   └── azure-westeurope/
    └── nonprod/
```

Key conventions:

- Every module accepts `class` (data class C1–C5) and `region_class` (US, EU, etc.). Resources that violate the matrix (e.g., C4 in US for an EU tenant) fail at `tofu plan`.
- Every resource gets the `acme:*` tag set via the `tagging` module — no exceptions.
- State is per-environment, per-region, per-cloud — `aws-use1` is one state file. Avoids blast-radius incidents.
- A single global "shared" state holds Org/IAM/identity primitives. Treated as production-only with extra protection.

Module promotion: `feature/` → `dev` → `staging` → `prod`. Each promotion is a tagged release of the module; `envs/` pin module versions.

### 3.1 Provider configuration

Providers authenticate via the federated identity bootstrapped in Stage 2:

```hcl
provider "aws" {
  region = var.region
  assume_role_with_web_identity {
    role_arn                = var.deploy_role_arn
    session_name            = "tofu-${var.env}-${var.region}"
    web_identity_token_file = "/var/run/secrets/tokens/oidc-token"
  }
  default_tags { tags = module.tags.standard }
}

provider "google" {
  project                     = var.gcp_project
  region                      = var.region
  credentials                 = null
  impersonate_service_account = var.deploy_sa
}

provider "azurerm" {
  features {}
  use_oidc          = true
  subscription_id   = var.azure_subscription
  tenant_id         = var.azure_tenant
  client_id         = var.azure_client_id
}
```

CI assumes the deploy roles via GitHub Actions OIDC; humans assume them via Entra-issued OIDC; no static keys exist.

---

## 4. Crossplane

Crossplane lives in the mgmt cluster and exposes higher-level **Compositions** to platform users. We use Crossplane for resources that benefit from continuous reconciliation and tenant-friendly CRDs; we use OpenTofu for cluster-foundation and one-time-ish resources.

Composition examples:

- `XCloudBucket` — a tenant-friendly CRD that maps to S3, GCS, or ADLS depending on `spec.cloud`; enforces CMK, lifecycle, residency
- `XManagedPostgres` — Aurora / Cloud SQL / Azure DB for PG with the same surface
- `XKServeRuntime` — KServe runtime resources per cluster
- `XTenantNamespace` — namespaces, NetworkPolicies, ResourceQuotas, RoleBindings, monitoring dashboards

Compositions are versioned via `CompositionRevision`; tenant CRs reference an explicit revision (no implicit upgrades).

### 4.1 Why both Crossplane and OpenTofu

- OpenTofu: things you create once and rarely change (network spine, cluster, IAM org roots). Plan/apply discipline matches operational reality.
- Crossplane: things tenants create and we reconcile continuously (buckets, databases, namespaces). The CRD shape is easier to govern at admission time and aligns with GitOps.

The seam: OpenTofu provisions Crossplane's IAM and provider configs; Crossplane then takes ownership of tenant-shaped resources.

---

## 5. Cross-cloud networking

### 5.1 Megaport topology

```
                Region pair: NA (Ashburn)              Region pair: EU (Frankfurt)         Region pair: APAC (Singapore)
              ┌──────────────────────┐               ┌──────────────────────┐               ┌──────────────────────┐
              │  Megaport ECX (ASH)  │               │  Megaport ECX (FRA)  │               │  Megaport ECX (SIN)  │
              └─┬───┬───┬─────┬──────┘               └─┬───┬───┬─────┬──────┘               └─┬───┬───┬─────┬──────┘
                │   │   │     │                        │   │   │     │                        │   │   │     │
        AWS DX◀┘   │   │     └▶GCP CI            AWS DX◀┘   │   │     └▶GCP CI            AWS DX◀┘   │   │     └▶GCP CI
        (us-east-1)│   │       (us-east4)         (eu-central-1)│   │     (europe-west4)   (ap-se-1) │   │     (asia-se1)
                  │   └▶Azure ER                       │   └▶Azure ER                      │   └▶Azure ER
              On-prem DC (hybrid)                   On-prem DC (hybrid)                  (n/a today)
```

VXCs (virtual cross-connects) inside Megaport stitch any pair: `AWS↔GCP`, `AWS↔Azure`, `GCP↔Azure`. BGP is used; we advertise per-cloud RFC 1918 supernets and avoid overlap.

### 5.2 Cloud-native edges

- AWS: Direct Connect Gateways + Transit Gateways per region; route tables segregate by environment (prod vs nonprod)
- GCP: Cloud Routers per region with VLAN attachments to Cloud Interconnect; Shared VPC at the project layer
- Azure: ExpressRoute circuits with ExpressRoute Gateway per region; vWAN hub for east-west across regions

### 5.3 Service mesh (Istio multi-cluster)

We run a single Istio mesh that spans clusters via the **multi-network multi-primary** topology. Each cluster has its own istiod; mesh-level CA roots are shared via a SPIFFE trust bundle. Cross-cluster service discovery uses east-west gateways exposed inside the private interconnect network.

This gives:

- Workloads see remote services via standard Kubernetes service DNS
- mTLS is end-to-end with SPIFFE identities; no cross-cloud TLS termination on a public endpoint
- Traffic shifting (canary, mirror) works across clouds

### 5.4 DNS

- Internal: a delegated Route53 Private Hosted Zone for `*.internal.acme.io`, mirrored via aliased records in GCP Cloud DNS and Azure Private DNS; updated via Crossplane controllers on namespace creation
- External: Route53 public for `acme.io`; GeoDNS routes users to the nearest healthy cloud (latency-based for public APIs, geo-based for residency-bound endpoints)

---

## 6. Observability fan-in (detailed)

Each cluster pushes telemetry to its **regional** aggregation tier; regional tiers federate to a **global** read tier in the mgmt cluster.

- **Metrics**: Prometheus agent → Thanos Receive (regional) → S3 (regional). Mgmt-cluster Thanos Query peers with each regional Thanos Query over mTLS. Cross-region/cross-cloud queries are transparent in Grafana.
- **Logs**: OTel collector → Loki (regional). Cross-region queries via Loki query frontend chain; tenant scoping enforced by `X-Scope-OrgID` propagation.
- **Traces**: OTel → Tempo (regional). Tail sampling at the cloud edge (5% baseline + errors + slow). Cross-cluster traces flow because trace context is preserved in mesh.
- **SLOs**: Sloth rules compiled into Prometheus recording rules per cluster, but burn evaluation happens at the federated query layer to span clouds. Per-tenant SLO dashboards work even when a tenant straddles two clouds.
- **Alerting**: Alertmanager per region with gossip-based cross-region deduplication; PagerDuty routes by `severity` and `team`.

Cost note: the federated query pattern keeps long-term storage cheap (per region, S3) and only pulls cross-region data on demand. The mgmt cluster does not store metrics.

---

## 7. Disaster recovery posture (link to ADR-005)

- Per cloud: active-active across two regions per cloud (e.g., AWS `us-east-1` + `us-west-2`; GCP `us-central1` + `us-east4`; Azure `eastus2` + `westeurope` for the global mix)
- Cross-cloud failover: workloads tier-classified. Tier-1 workloads have a *warm* replica in a second cloud (data replicated, capacity reserved at 50%). Tier-2/3 have *cold* DR with documented RTO.
- DNS-level failover via Route53 health checks + Cloud DNS + Azure Traffic Manager.
- Velero for cluster object backup + cross-cloud blob copies (where residency allows).
- Quarterly DR exercise per cloud pair; annual cross-cloud failover game-day.

---

## 8. Deployment pipeline

### 8.1 GitOps repos

- `infra-tofu/` — OpenTofu code, structured per §3
- `infra-gitops/` — Argo CD ApplicationSets, Crossplane Compositions, Helm chart overlays
- `policies/` — OPA bundles, Cloud Custodian policies, Kyverno policies
- `apps/${name}/` — application charts and overlays per service

### 8.2 PR flow

1. PR opens against `infra-tofu` or `infra-gitops`
2. CI runs:
   - `tofu fmt`, `tofu validate`, `tofu plan` per target
   - `conftest` against OPA bundles (residency, tagging, encryption)
   - `kyverno test` for cluster manifests
   - `trivy config` for misconfig scan
   - `infracost diff` for cost delta
3. Reviewers approve; merge to `main` triggers:
   - `tofu apply` per target via change-windowed pipeline
   - Argo CD detects manifest change and syncs

### 8.3 Promotion

Environments promote `nonprod` → `staging` → `prod`. Pinning is explicit (module versions, chart versions, image digests). No "latest" tags anywhere in prod.

---

## 9. Verification checklist (Day 30 readiness)

Before declaring the architecture in production:

- [ ] All three clouds reachable from mgmt cluster via private interconnect (mtr from a debug pod shows hop count and latency within budget)
- [ ] OIDC federation works in all 6 directions (GH→AWS, GH→GCP, GH→Azure, AWS↔GCP, AWS↔Azure, GCP↔Azure)
- [ ] A pod in EKS can read a GCS bucket using its IRSA-derived federated identity (no static keys)
- [ ] Istio mesh shows services from all clusters in `istioctl proxy-status`
- [ ] A test inference request hits a model in AWS, fetches features from Snowflake (GCP), and logs to Loki in the same region; full trace shows in Tempo
- [ ] Grafana dashboards aggregate metrics across AWS, GCP, Azure in a single panel
- [ ] Vault secrets dynamically issued for an Aurora connection; pod gets fresh credentials within lease window
- [ ] Crossplane creates an `XCloudBucket` and the result is a CMK-encrypted bucket in the right cloud + region for the tenant's residency
- [ ] OPA blocks a deliberately-bad PR (C4 data in non-EU region for an EU tenant)
- [ ] DR drill: forced failover from `us-east-1` to `us-west-2` for a tier-1 workload completes within 1 hour RTO
- [ ] Cost dashboards (Kubecost in mgmt cluster + CloudHealth) show per-cloud, per-tenant, per-cost-center spend with weekly reports
- [ ] On-call rotations active in PagerDuty with runbooks linked from every alert
- [ ] Statuspage configured with per-region health
- [ ] DPA template updated to reflect actual subprocessor list

---

## 10. Common pitfalls (and what we did about them)

### 10.1 "Multi-cloud doubles ops cost"

It can. We mitigate by:

- A single mesh, a single observability story, a single CI surface across clouds
- Tooling that's cloud-agnostic by default (OpenTofu, Crossplane, Vault, Argo, Istio)
- Hiring one senior per cloud rather than expecting any one engineer to be deeply expert in all three

### 10.2 Egress bills you didn't model

Megaport (§5) makes cross-cloud egress affordable per-GB but you still pay per-GB. Solve at the architecture layer: keep hot data colocated with compute; replicate cold tier only where compliance demands; alert at the per-pair traffic threshold.

### 10.3 Identity sprawl

Centralize on Entra ID for humans and SPIFFE for workloads early. Do not let each cloud's IAM model leak up into application code; abstract behind workload-identity primitives.

### 10.4 Inconsistent network CIDRs

Plan the CIDR map in a spreadsheet **before** any VPC exists. Reserve large enough blocks per cloud × region × env. We use `/12` per cloud, `/16` per region, `/20` per workload tier. Documented in `infra/network/cidr-plan.md`.

### 10.5 Diverging tooling per cloud

The temptation is to use cloud-native tooling that "comes free" in each cloud. We resist where the gain is small (e.g., we do not use CloudWatch dashboards alongside Grafana — we use Grafana with the CloudWatch datasource). Tooling diversity is the tax that kills multi-cloud teams.

### 10.6 Slow rollouts because three clouds

Pipeline parallelism is mandatory; do not gate cloud-B on cloud-A unless the dependency is real. Argo CD ApplicationSets fan out naturally; CI parallelizes per target.

### 10.7 Forgotten Crossplane drift

A Crossplane resource updated outside of Git is silently corrected at the next reconcile. People find this confusing. We surface it in a Grafana panel "Crossplane forced reconciles" and review weekly.

---

## 11. Reference implementations in this repo

(Once the reference modules are populated):

- `reference-implementation/tofu-modules/` — the modules described in §3
- `reference-implementation/crossplane-compositions/` — `XCloudBucket`, `XManagedPostgres`, `XTenantNamespace`
- `reference-implementation/argo-cd/` — ApplicationSets and the bootstrap app
- `reference-implementation/istio-multicluster/` — mesh bootstrap manifests
- `reference-implementation/observability/` — Prometheus/Thanos, Loki, Tempo, Grafana provisioning
- `reference-implementation/policies/` — OPA bundles, Kyverno policies, Cloud Custodian rules
- `reference-implementation/network/cidr-plan.md`

---

## 12. References

- `ARCHITECTURE.md`
- ADR-001 (multi-cloud strategy)
- ADR-002 (data sovereignty)
- ADR-003 (intercloud networking)
- ADR-004 (cost optimization)
- ADR-005 (disaster recovery)
- `architecture/business/cost-analysis.md`
- `architecture/governance/data-residency-matrix.md`
- `architecture/research/cloud-comparison.md`
- OpenTofu docs: <https://opentofu.org/docs/>
- Crossplane docs: <https://docs.crossplane.io/>
- Istio multi-cluster: <https://istio.io/latest/docs/setup/install/multicluster/>
- SPIFFE / SPIRE: <https://spiffe.io/>
- Vault: <https://developer.hashicorp.com/vault>
- Megaport ECX: <https://docs.megaport.com/>
