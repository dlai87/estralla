# Terraform — Reference Implementation

This directory describes the Terraform layout that provisions the Enterprise
MLOps Platform's AWS infrastructure: VPCs, EKS clusters, RDS, ElastiCache, S3,
KMS, IAM, and shared platform-level resources.

The companion sibling at
[`../../reference-implementations/terraform/`](../../reference-implementations/terraform/)
contains the actual concrete Terraform modules (currently `vpc/` and `eks/`).
This README describes the **target layout** — the full multi-account, multi-
environment structure that the modules slot into when productionized. Treat
this as the authoritative guidance; the in-repo modules under
`reference-implementations/` are illustrative starting points.

Cross-references: [ADR-007](../../architecture/adrs/007-security-compliance-architecture.md)
for security architecture, [ADR-008](../../architecture/adrs/008-kubernetes-distribution.md)
for EKS choice, [physical view](../../architecture/views/README.md#4-physical-view)
for the cloud footprint inventory.

## Toolchain (pinned)

| Tool | Version | Purpose |
|---|---|---|
| Terraform | 1.9.x (pinned via `required_version`) | Core |
| AWS provider | `~> 5.60` | AWS resources |
| Helm provider | `~> 2.14` | Bootstrap a few in-cluster controllers (Karpenter, ArgoCD, External Secrets) |
| Kubernetes provider | `~> 2.31` | CRDs and bootstrap manifests only |
| tflint | 0.51+ | Lint, AWS ruleset |
| tfsec / Trivy | latest | Security scan |
| Terraform Cloud | — | Remote backend + remote runs |
| Atlantis | optional | PR workflows for any team preferring Git-flow over TFC |

Why Terraform Cloud over Spacelift / Atlantis / pure CLI: native VCS workflow,
managed remote state with strict locking, easy team-based RBAC, and the cost
estimation feature pays for itself when ML teams casually propose new GPU
pools.

## Directory layout

```
terraform/
├── README.md                      # this file
├── versions.tf                    # required_version, required_providers (shared)
├── modules/                       # reusable modules (versioned via Git tag)
│   ├── network/
│   │   ├── vpc/                   # VPC, subnets (public/private/db), NAT, VPC endpoints
│   │   ├── transit-gateway/       # TGW attachment for corp peering
│   │   └── route53-private/       # Private zones for in-cluster DNS
│   ├── platform/
│   │   ├── eks-cluster/           # EKS control plane + add-ons + OIDC provider
│   │   ├── eks-nodepool/          # Karpenter NodePool + EC2NodeClass
│   │   ├── karpenter/             # Karpenter IAM + Helm install
│   │   ├── external-secrets/      # External Secrets Operator + IRSA
│   │   ├── argocd/                # Argo CD bootstrap + ApplicationSet for app-of-apps
│   │   └── istio/                 # Istio install via Helm (ambient mode)
│   ├── data/
│   │   ├── rds-postgres/          # Multi-AZ Postgres for MLflow / Governance / Feast registry
│   │   ├── elasticache-redis/     # Redis Cluster for Feast online store
│   │   └── s3-bucket/             # Hardened S3 with SSE-KMS, lifecycle, Object Lock
│   ├── security/
│   │   ├── kms/                   # Customer-managed KMS keys per purpose
│   │   ├── iam-roles/             # Common cross-account IAM roles
│   │   ├── irsa/                  # IAM Roles for Service Accounts factory
│   │   ├── secrets-manager/       # Secrets-Manager with KMS + rotation
│   │   └── guardduty-securityhub/ # GuardDuty + Security Hub baseline
│   └── observability/
│       ├── cloudwatch-baseline/   # Account-level CloudWatch + alarms
│       └── prometheus-thanos-s3/  # S3 bucket + IAM for Thanos LTS
├── live/                          # one directory per (account, environment, region)
│   ├── _global/
│   │   └── tf-backend/            # bootstrap S3 + DynamoDB for state (one-time)
│   ├── shared-services/
│   │   └── us-east-1/             # ECR, Route53 public zones, shared OIDC
│   ├── dev/
│   │   └── us-east-1/
│   │       ├── 010-network/
│   │       ├── 020-security/
│   │       ├── 030-data/
│   │       ├── 040-platform/
│   │       └── terragrunt.hcl     # or stack.yaml if using TFC stacks
│   ├── staging/
│   │   └── us-east-1/             # same shape as dev
│   ├── prod/
│   │   ├── us-east-1/             # primary
│   │   └── us-west-2/             # DR (read-replicas, S3 CRR target)
│   └── prod-eu/
│       └── eu-west-1/             # GDPR data residency, independent
└── policies/                      # OPA / Sentinel policies attached at runtime
    ├── deny-public-s3.rego
    ├── require-tags.rego
    ├── require-kms-cmk.rego
    └── max-instance-types.rego
```

### Why this layout

- **`modules/` is versioned, `live/` is composed.** Modules are released by Git
  tag (`network/vpc/v3.2.0`); `live/` pins module versions so promotion is a
  PR that bumps the pin in staging first, then prod.
- **Numbered subdirectories (`010-network`, `020-security`, …)** make the
  dependency order obvious and lexical. There is _no_ circular dependency
  between numbered stacks.
- **Per-(account, region) directories** prevent accidental cross-environment
  blast radius. There is no way to `terraform apply` to prod from staging's
  directory because the AWS provider is configured per directory.
- **`policies/` is enforced at runtime** by Sentinel (TFC) or OPA (Atlantis).
  Soft-mandatory by default (advisory in dev, hard-mandatory in staging+prod).

## State backend

We use **Terraform Cloud workspaces** as the primary backend, one workspace per
`live/` directory. For organizations that prefer self-managed backends, the
fallback is S3+DynamoDB:

```hcl
terraform {
  required_version = ">= 1.9"
  backend "s3" {
    bucket         = "mlops-tf-state-${env}"   # bootstrapped in live/_global/tf-backend/
    key            = "live/${env}/${region}/${stack}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:${shared_services_account}:key/<tf-state-key>"
    dynamodb_table = "mlops-tf-lock-${env}"
  }
}
```

Bootstrapping rules:
- The state bucket and DynamoDB table are created _once_ in
  `live/_global/tf-backend/` with local state, then the state is migrated into
  the bucket itself on the second `apply` (the bootstrap chicken-and-egg).
- The state bucket has **versioning enabled**, **MFA-delete required**,
  **Object Lock in compliance mode** with 7-day minimum, and a bucket policy
  that allows only the `terraform-runner` role to write.
- A nightly Lambda copies state objects to a second bucket in another account
  for off-site backup. This has saved us once.

## Secret management

**Hard rule: no secrets in Terraform code, no secrets in state.**

- Database passwords are generated by `random_password` _into_ AWS Secrets
  Manager and never read back. The application reads the secret at runtime via
  IRSA. Terraform output is the secret's ARN, never its value.
- For values that must round-trip (e.g., bootstrap credentials), we use
  `aws_secretsmanager_secret_version` with `ignore_changes = [secret_string]`
  and rotate out-of-band.
- KMS keys are customer-managed, one per purpose (`rds`, `s3-data`,
  `s3-artifacts`, `secrets`, `ebs`, `tf-state`, `audit-worm`, `per-tenant-cmk`).
- Secrets are surfaced to workloads via External Secrets Operator pulling from
  Secrets Manager. The K8s `Secret` is recreated on every reconcile so a
  rotated value propagates within ~60s.

## Multi-account strategy

We follow AWS Control Tower with one OU per environment:

| Account | OU | Purpose |
|---|---|---|
| `aws-mlops-management` | Root | Org root, billing, IAM Identity Center |
| `aws-mlops-shared` | Shared Services | ECR, public Route53, central log archive |
| `aws-mlops-security` | Security | Security Hub aggregator, audit log archive |
| `aws-mlops-dev` | Workloads-Dev | Dev environment |
| `aws-mlops-stg` | Workloads-Nonprod | Staging |
| `aws-mlops-prod` | Workloads-Prod | US production |
| `aws-mlops-prod-eu` | Workloads-Prod-EU | EU production (GDPR) |
| `aws-mlops-dr` | Workloads-Prod | DR target |

SCPs at the OU level enforce:
- Deny non-approved regions
- Deny disabling CloudTrail, GuardDuty, Security Hub, Config
- Require KMS CMK for S3 (no SSE-S3)
- Deny public S3 buckets
- Deny IAM user creation (Identity Center only)

## tfvars convention

Each `live/<env>/<region>/<stack>/` directory has a `terraform.tfvars` for the
defaults of that environment, plus optional `secrets.auto.tfvars` (gitignored,
sourced from TFC variable sets at run time).

Example `live/staging/us-east-1/040-platform/terraform.tfvars`:

```hcl
# === environment context ===
environment = "staging"
region      = "us-east-1"
account_id  = "234567890123"

cost_center        = "ml-platform"
data_classification = "internal"
owner_team         = "platform-engineering"
owner_slack        = "#mlops-platform"

# === networking ===
vpc_id            = "vpc-0a1b2c3d4e5f6g7h8"  # output from 010-network
private_subnet_ids = ["subnet-aaa", "subnet-bbb", "subnet-ccc"]
db_subnet_ids      = ["subnet-ddd", "subnet-eee", "subnet-fff"]

# === EKS ===
cluster_name             = "mlops-stg"
cluster_version          = "1.30"
endpoint_public_access   = false   # private endpoint, accessed via TGW
service_ipv4_cidr        = "172.20.0.0/16"
kms_key_arn              = "arn:aws:kms:us-east-1:234567890123:key/<eks-secrets>"

# === node pools (consumed by Karpenter NodePool/EC2NodeClass) ===
nodepools = {
  system_on_demand = {
    instance_categories = ["m"]
    instance_generation = ["6", "7"]
    capacity_type       = ["on-demand"]
    min_size            = 3
    max_size            = 20
    taints              = []
    labels              = { workload = "system", lifecycle = "on-demand" }
  }
  inference_cpu = {
    instance_categories = ["c"]
    instance_generation = ["7"]
    capacity_type       = ["on-demand"]
    min_size            = 0
    max_size            = 40
    taints              = []
    labels              = { workload = "inference-cpu" }
  }
  inference_gpu = {
    instance_families   = ["g6e"]
    capacity_type       = ["on-demand"]
    min_size            = 1
    max_size            = 10
    taints              = [{ key = "nvidia.com/gpu", value = "true", effect = "NoSchedule" }]
    labels              = { workload = "inference-gpu", accelerator = "nvidia-l40s" }
  }
  training_gpu_spot = {
    instance_families   = ["p5"]
    capacity_type       = ["spot"]
    min_size            = 0
    max_size            = 8
    taints              = [{ key = "training", value = "true", effect = "NoSchedule" }]
    labels              = { workload = "training-gpu", lifecycle = "spot" }
  }
}

# === RDS (driven by 030-data, here just module flags) ===
rds_engine_version  = "15.7"
rds_instance_class  = "db.r6g.2xlarge"  # smaller than prod
rds_multi_az        = true
rds_backup_retention_days = 14

# === required tags (enforced by SCP + tflint rule) ===
default_tags = {
  Environment       = "staging"
  CostCenter        = "ml-platform"
  Owner             = "platform-engineering"
  DataClassification = "internal"
  TerraformManaged  = "true"
}
```

Prod deltas are minimal (instance sizes, retention windows, `data_classification`
values, KMS ARNs, network CIDR ranges). Resist the urge to diverge module
parameters between staging and prod beyond size — your DR-drill confidence is
inversely proportional to the delta.

## Drift detection

**Two layers**:

1. **`terraform plan` in CI on every PR** — detects intent drift (the code
   doesn't match what we want).
2. **Scheduled drift plan** — `terraform plan -detailed-exitcode` runs hourly
   in TFC. Exit code 2 (changes detected without a corresponding code change)
   sends a Slack alert to `#mlops-platform`. Drift is investigated within 1
   business day.

We treat drift as an incident category, not as noise. Root-cause is almost
always one of: out-of-band console change (rare, individuals get coached),
AWS-side mutation (a managed service rotation), or our own module changing
defaults silently (the worst category; the fix is to make module defaults
stable across versions).

## Promotion workflow

1. Feature PR against `modules/<module>/` → tflint + tfsec + unit tests
   (terratest) → review → merge → Git tag.
2. PR against `live/dev/.../<stack>/` bumping `module_version` → TFC plan run
   → speculative output reviewed → merge → TFC apply.
3. After 1 business day in dev, PR against `live/staging/.../<stack>/`. Same
   flow.
4. After 1 business week in staging, PR against `live/prod/.../<stack>/`.
   Requires two reviewers, one of whom is SRE on-call.
5. After 1 business week in prod-US, PR against `live/prod-eu/.../<stack>/`.
   GDPR posture requires the EU change window.

A change can be aborted at any step. There is no "skip staging" gate.

## Module testing

Each module has:

- `examples/basic/` — smallest viable invocation, used by Terratest
- `tests/<name>_test.go` — Terratest that `apply`s into a sandbox account,
  asserts outputs, then `destroy`s
- `README.md` — generated by `terraform-docs`
- `.tflint.hcl` — module-specific lint rules

Test runs are nightly against the `sandbox` account, with a 24-hour TTL on
any resources created.

## Cost guardrails

- TFC's Infracost integration posts cost diff on every PR. Diffs > $5K/month
  require two approvers.
- AWS Budgets per account with anomaly detection. 80% threshold pages the
  FinOps on-call; 100% notifies VP Eng.
- Kubecost (in-cluster) attributes Kubernetes spend to tenant via the
  `tenant=<team>` label. Chargeback report monthly.

## What this README intentionally doesn't cover

- Workstation setup for engineers (`asdf`, `aws-vault`, etc.) — see internal
  `eng-onboarding` docs.
- Application Helm charts and Kubernetes manifests — see
  [`../kubernetes/README.md`](../kubernetes/README.md).
- CI/CD pipelines for application code — see
  [`../../reference-implementations/cicd/`](../../reference-implementations/cicd/).
