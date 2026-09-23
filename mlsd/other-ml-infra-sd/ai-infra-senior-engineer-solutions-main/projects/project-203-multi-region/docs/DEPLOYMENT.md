# Deployment Guide: Multi-Region ML Platform

This guide covers the end-to-end deployment of the multi-region ML serving platform across AWS (`us-west-2`), GCP (`eu-west-1`), and Azure (`ap-south-1`). It assumes you have completed the bootstrap procedures in [STEP_BY_STEP.md](STEP_BY_STEP.md) (cloud accounts created, IAM bootstrap user provisioned, Terraform state buckets created).

The deployment philosophy is **GitOps with regional autonomy**: every deploy is a Git commit, every region is an independently reconciled Argo CD `ApplicationSet`, and every change rolls out one region at a time with explicit promotion gates.

Tooling versions used:

- Terraform 1.7.4
- kubectl 1.29.3
- Argo CD 2.10.4
- Helm 3.14.2
- Kustomize 5.3.0 (built into kubectl)
- External Secrets Operator 0.9.13
- cert-manager 1.14.4

---

## 1. Per-Region Cluster Bring-Up

Each region's cluster is created from a single Terraform module, parameterized by region and cloud provider. The order matters: networking first, cluster second, add-ons third, workloads last.

### 1.1 Terraform State Layout

```
terraform/
├── envs/
│   ├── prod/
│   │   ├── us-west-2/
│   │   │   ├── backend.tf       # s3 backend in us-west-2
│   │   │   └── main.tf          # references modules/aws
│   │   ├── eu-west-1/
│   │   │   ├── backend.tf       # gcs backend in eu-west-1
│   │   │   └── main.tf          # references modules/gcp
│   │   └── ap-south-1/
│   │       ├── backend.tf       # azurerm backend in centralindia
│   │       └── main.tf          # references modules/azure
│   └── staging/
│       └── ... (same shape, smaller)
└── modules/
    ├── aws/
    ├── gcp/
    ├── azure/
    └── dns/
```

Each region has its **own state file in the local cloud's storage**. We deliberately avoid a single global state because:

- A `terraform apply` for `eu-west-1` should not require AWS credentials.
- State locking is per-state; a global state means one stuck lock blocks all regions.
- Blast radius of a bad `terraform destroy` is contained.

### 1.2 Bring-Up Order

For each region, in parallel (because they share no Terraform state):

```bash
cd terraform/envs/prod/us-west-2
terraform init
terraform plan -out=plan.tfplan
# Review the plan; expected resources: VPC, subnets, EKS, node groups, ECR, S3 buckets
terraform apply plan.tfplan
```

After all three regions complete:

```bash
# Configure kubectl contexts
aws eks update-kubeconfig --region us-west-2 --name ml-prod-us-west-2 --alias prod-us
gcloud container clusters get-credentials ml-prod-eu-west-1 --region europe-west1 --project ml-prod
kubectl config rename-context gke_ml-prod_europe-west1_ml-prod-eu-west-1 prod-eu
az aks get-credentials --resource-group ml-prod-rg --name ml-prod-ap-south-1 --context prod-ap
```

### 1.3 Add-On Installation Order

Per region, install add-ons in this strict order. Each waits for the previous to be healthy:

1. **CNI / Network Policy**: AWS VPC CNI 1.16 / Cilium 1.15 on GKE / Azure CNI on AKS. Wait for all nodes `Ready`.
2. **External Secrets Operator** (Helm chart `external-secrets/external-secrets` v0.9.13). Reconciles `SecretStore` resources pointing at the region's native secret manager.
3. **cert-manager** (Helm chart `jetstack/cert-manager` v1.14.4) with `installCRDs=true`. Creates `ClusterIssuer` for the region.
4. **Argo CD** (Helm chart `argo/argo-cd` v6.7.10). Bootstrap from a static admin password stored in the region's secret manager, then immediately disable password auth in favor of OIDC.
5. **Istio** (operator) v1.21. Profile `default` with mTLS strict; ingress gateway exposed via NLB.
6. **Prometheus + Thanos sidecar** (Helm chart `prometheus-community/kube-prometheus-stack` v57.x). Object store config points at the region's bucket.
7. **External-DNS** v0.14, pointed at the central Route 53 hosted zone with credentials scoped to records prefixed `<region>.ml.example.com`.

The order matters because:

- Argo CD reconciles `Applications` that reference secrets (External Secrets must exist first).
- `Applications` deploy services that need TLS certificates (cert-manager must exist first).
- `Applications` create Istio `VirtualService` resources (Istio CRDs must exist first).

A bootstrap script `scripts/bring_up_region.sh <region>` automates this and exits non-zero on any health-check failure, before proceeding to the next step.

---

## 2. Secrets Distribution

Secrets are managed centrally in source-of-truth secret stores (one per region's native service) and synced into the cluster via External Secrets Operator. The platform supports two distribution modes:

### 2.1 Per-Region Secrets (Default)

Most secrets are scoped to a single region:

- Database credentials (each region has its own DB instance)
- Per-region API keys for cloud-provider APIs
- TLS private keys for region-specific certificates (when not using ACME)

These live in the local secret store (`us-west-2` → AWS Secrets Manager, `eu-west-1` → GCP Secret Manager, `ap-south-1` → Azure Key Vault) and are pulled into the cluster as Kubernetes `Secret` resources by ESO `ExternalSecret` CRDs.

Example (`us-west-2`):

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: ml-serving
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-irsa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: inference-db-credentials
  namespace: ml-serving
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: inference-db-credentials
  data:
    - secretKey: password
      remoteRef:
        key: prod/ml-platform/inference/db
        property: password
```

### 2.2 Globally Replicated Secrets

A small set of secrets must be identical across regions:

- The HMAC secret used to sign inter-service tokens
- The signing key for JWTs issued by the auth service
- The shared secret for cross-region admin operations

These are managed via a **one-way replication job** that runs every 6 hours:

```
source: AWS Secrets Manager (us-west-2)
   ↓ (replicator with KMS re-encryption)
   ├→ GCP Secret Manager (eu-west-1)
   └→ Azure Key Vault (ap-south-1)
```

The replicator (`src/replication/secret_replicator.py`) uses **versioned writes**: each secret version is written with a monotonically increasing version label. Consumers always read the highest version. This means a key rotation can be performed safely:

1. Add v2 to the source (workloads continue using v1 because v2 hasn't propagated yet)
2. Wait 1 hour for propagation to all regions
3. Cut over consumers to v2 via a rolling restart
4. After 24 hours of v2 stability, mark v1 for deletion (deletion happens 7 days later)

We deliberately avoid hot-reloading secrets in workloads; a restart is required to pick up rotated secrets. This makes rotation auditable (deployments log the secret version they loaded) and avoids partial-rotation states.

---

## 3. Config Drift Prevention (GitOps via Argo CD)

### 3.1 Repository Layout

```
gitops-repo/
├── apps/
│   ├── inference/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── virtualservice.yaml
│   │   │   ├── hpa.yaml
│   │   │   ├── pdb.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── prod-us/
│   │       │   ├── kustomization.yaml
│   │       │   ├── patch-replicas.yaml      # production sizing
│   │       │   ├── patch-region-config.yaml  # AWS-specific config
│   │       │   └── secrets-binding.yaml
│   │       ├── prod-eu/
│   │       │   └── ...
│   │       └── prod-ap/
│   │           └── ...
│   ├── replicator/
│   ├── failover-controller/
│   └── cost-analyzer/
└── applicationsets/
    └── all-services-all-regions.yaml
```

### 3.2 ApplicationSet for Fan-Out

A single `ApplicationSet` generates one Argo CD `Application` per (service × region) combination:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: ml-platform-prod
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          - list:
              elements:
                - service: inference
                - service: replicator
                - service: failover-controller
                - service: cost-analyzer
          - list:
              elements:
                - region: prod-us
                  cluster: https://kubernetes.default.svc  # in-cluster for hub model
                - region: prod-eu
                  cluster: https://gke-eu-west-1.example.com
                - region: prod-ap
                  cluster: https://aks-ap-south-1.example.com
  template:
    metadata:
      name: '{{service}}-{{region}}'
    spec:
      project: ml-platform
      source:
        repoURL: https://github.com/example/gitops-repo
        targetRevision: HEAD
        path: 'apps/{{service}}/overlays/{{region}}'
      destination:
        server: '{{cluster}}'
        namespace: ml-serving
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        retry:
          limit: 5
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
```

This produces 12 Argo `Application` resources (4 services × 3 regions), all reconciling continuously.

### 3.3 Drift Detection and Auto-Heal

Argo CD's `selfHeal: true` reverts manual `kubectl edit` changes within 3 minutes. In production, we **enable self-heal in staging but disable in prod**, replacing it with an alert:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: false   # prod: do not auto-revert; alert instead
```

The alert (`ArgoCDApplicationOutOfSync` firing >10 minutes) pages the on-call. Rationale: in prod, a manual override is usually an emergency action that should not be automatically undone; staging drift is always a bug.

### 3.4 Preventing Region-Scoped Drift in PRs

A CI check runs `kustomize build apps/<service>/overlays/<region>` for all three regions on every PR, then diffs the rendered output against the previous revision. The check **fails** if:

- The image tag changed in only some regions (catches the "I forgot to update prod-ap" bug).
- The replica count changed by more than 50%.
- A resource was added or removed in only some regions.

This is implemented as a GitHub Action (`.github/workflows/render-check.yaml`) using `kustomize` directly and `dyff` for structured YAML diffs.

---

## 4. Rollout Choreography (Canary One Region First)

A new deploy proceeds through five gates. No gate is skipped, even for hotfixes.

### 4.1 Gate 1: CI in `main`

PR merges to `main`. CI builds the container image, signs it with cosign, pushes to all three regional registries (ECR, Artifact Registry, ACR) in parallel, and updates the image tag in `apps/<service>/base/kustomization.yaml` via a follow-up PR auto-merged after green tests.

```bash
# Image pushed as:
123456789012.dkr.ecr.us-west-2.amazonaws.com/inference:v3.2.0
europe-west1-docker.pkg.dev/ml-prod/registry/inference:v3.2.0
mlprodacr.azurecr.io/inference:v3.2.0
```

The cosign signature is verified by an admission controller (`policy-controller`) in each cluster before the image is allowed to run.

### 4.2 Gate 2: Canary in `prod-us`

A canary Argo CD Application targets 10% of `prod-us` traffic via Istio `VirtualService` weights. The canary runs for **30 minutes**, during which an automated **Argo Rollouts AnalysisRun** evaluates:

- Error rate <0.5% (vs production baseline)
- P99 latency <300 ms
- No new alerts firing on the canary's pod labels

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate-and-latency
spec:
  metrics:
    - name: error-rate
      interval: 60s
      successCondition: result[0] < 0.005
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{job="inference",version="{{args.canary-version}}",code=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{job="inference",version="{{args.canary-version}}"}[5m]))
    - name: p99-latency-ms
      interval: 60s
      successCondition: result[0] < 300
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            histogram_quantile(0.99,
              sum by (le) (rate(http_request_duration_seconds_bucket{job="inference",version="{{args.canary-version}}"}[5m]))
            ) * 1000
```

If the analysis fails, Argo Rollouts auto-aborts and traffic returns to the baseline within 30 seconds.

### 4.3 Gate 3: Full Rollout in `prod-us`

If the canary passes, traffic ramps to 50%, then 100%, with 15-minute holds at each step. Total time from canary start to full `prod-us`: ~75 minutes.

### 4.4 Gate 4: Soak in `prod-us`

After `prod-us` reaches 100%, the new version soaks for **2 hours** with no automated promotion to other regions. During this window, on-call monitors for slow-burn issues (memory leaks, log volume changes, cost anomalies) that the 30-minute canary would miss.

### 4.5 Gate 5: Parallel Rollout to `prod-eu` and `prod-ap`

After the soak, both remaining regions roll out in parallel using the same canary-then-full pattern. They are not serialized because:

- Independent rollout failures in different regions are easier to debug.
- Serialized rollout doubles the total time without meaningfully reducing risk after `prod-us` has already soaked.

A failure in either region triggers an alert but does **not** automatically revert `prod-us`. The on-call decides whether to globally revert or to investigate the regional issue.

Total end-to-end deploy time: **~6 hours** for a normal release. Hotfixes can shorten the soak gate to 30 minutes with explicit approval from a second engineer.

---

## 5. Rollback Playbook

### 5.1 Single-Region Rollback (Most Common)

If a specific region is misbehaving and other regions are fine:

```bash
# Identify the bad revision
argocd app history inference-prod-eu

# Roll back to the previous revision
argocd app rollback inference-prod-eu <revision-id>

# Verify
kubectl --context=prod-eu rollout status -n ml-serving deploy/inference --timeout=5m
```

This rolls back **only the affected region's** Argo CD Application. The Git source-of-truth is **unchanged**, which is why you must also create a follow-up PR that reverts the image tag in `apps/inference/base/kustomization.yaml`—otherwise Argo CD will re-sync to the bad version on the next reconciliation (every 3 minutes by default).

A faster alternative: pause the Application before rolling back, which prevents reconciliation:

```bash
argocd app set inference-prod-eu --sync-policy none
argocd app rollback inference-prod-eu <revision-id>
# Now create the Git revert PR; once merged:
argocd app set inference-prod-eu --sync-policy auto
```

### 5.2 Global Rollback

If a release is broken everywhere, revert via Git:

```bash
git revert <release-commit>
git push origin main
# Argo CD will detect the new HEAD and roll back all 12 Applications within 3 minutes
```

This works for both the application image tag and any infrastructure manifests in the GitOps repo. For Terraform-managed infrastructure changes that turn out broken, you must `terraform apply` the previous module version explicitly (Git revert on Terraform code is necessary but not sufficient).

### 5.3 Emergency Region Eviction

If a region is causing production issues and you want to drain it without waiting for code rollback:

```bash
# Drain via the failover controller (preferred; gradual)
failoverctl drain --region eu-west-1 --duration 5m

# Or via Route 53 directly (faster but blunter; resolvers may cache)
aws route53 change-resource-record-sets --hosted-zone-id Z2FDTNDATAQYW2 \
  --change-batch file://emergency-drain-eu.json

# Or scale down the deployment to refuse traffic
kubectl --context=prod-eu scale -n ml-serving deploy/inference --replicas=0
```

After the immediate fire is out, roll back the code change normally.

### 5.4 Database/Stateful Rollback

Image rollbacks are safe; **database migration rollbacks are not** unless the migration was explicitly designed to be backward-compatible.

Our migration policy requires every migration to be a **two-step expand-contract**:

1. Expand: add new column with default, deploy code that writes both columns.
2. Contract: stop writing the old column, deploy code that reads only new column. **Wait two release cycles.** Drop the old column.

A rollback in the expand phase is safe (drop the new column). A rollback in the contract phase is **not safe** without first running the contract reverse migration. The migration tool (`golang-migrate` v4.17) enforces this with `up.sql` and `down.sql` per migration, and the CI checks that `down.sql` exists for every `up.sql`.

### 5.5 Cluster-Level Rollback (Catastrophic)

If a cluster is unrecoverable (etcd corruption, bad CNI update, etc.):

1. Failover all traffic away from the region (see §5.3).
2. `terraform destroy` the cluster in that region's state.
3. `terraform apply` to rebuild from the pinned module version.
4. Argo CD's `ApplicationSet` controller automatically re-creates Applications when the new cluster's API endpoint comes online (the cluster URL is well-known and unchanged).
5. Wait for all Applications to reach `Healthy`. Run smoke tests.
6. Gradually re-admit traffic via `failoverctl restore --region <region> --ramp 10%/15m`.

This procedure has been rehearsed quarterly and takes ~90 minutes for an EKS cluster, 75 for GKE, 100 for AKS. The numbers come from game-day exercises Q1 2026.

---

## 6. Pre-Deploy Checklist

Before merging a release PR:

- [ ] CI is green on all three target architectures (amd64, arm64).
- [ ] Image is signed by cosign and the signature is verifiable.
- [ ] If the change touches database schema, `down.sql` exists and is tested.
- [ ] If the change adds or removes a config key, all three region overlays are updated.
- [ ] If the change touches the API contract, the OpenAPI spec is regenerated and committed.
- [ ] Release notes are written and posted to `#deploys`.
- [ ] On-call is aware and not in the middle of another incident.
- [ ] No competing deploys in flight (only one release per service per day in normal ops).

After the deploy:

- [ ] All 12 Argo Applications show `Synced` and `Healthy`.
- [ ] No new alerts firing for >5 minutes.
- [ ] Error rates and latencies match pre-deploy baselines.
- [ ] Synthetic-canary parity test passes (see [TROUBLESHOOTING.md §3](TROUBLESHOOTING.md)).
- [ ] Update the deploy log (audit DynamoDB table).

---

## 7. Common Deploy-Time Failures

- **Image pull errors in one region**: usually a cross-cloud registry replication lag. Wait 5 minutes and retry; if persistent, check the registry replicator logs.
- **Pod stuck `Pending` with `insufficient cpu`**: the cluster autoscaler is provisioning nodes. Wait 5 minutes; if pods remain pending, check the autoscaler logs for AWS service quotas (Spot capacity, EBS volume limits).
- **`ImagePullBackOff` with `signature not verified`**: cosign signature missing or wrong key. Re-run the signing step in CI.
- **Argo CD `OutOfSync` immediately after sync**: a Kubernetes-side mutating admission controller (e.g., Istio injection) is changing the manifest after Argo applies it. Add `ignoreDifferences` to the Application spec.
- **TLS errors after deploy**: cert-manager hasn't issued the cert yet. Check `kubectl get certificate -A` for `Ready=False` and inspect events.

For everything else, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
