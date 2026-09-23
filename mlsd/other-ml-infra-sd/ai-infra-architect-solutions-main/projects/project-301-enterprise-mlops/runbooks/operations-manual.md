# Enterprise MLOps Platform — Day-2 Operations Manual

**Audience**: Platform SRE, Platform Engineering, Tenant Platform Liaisons
**Scope**: Steady-state operation of the multi-tenant MLOps platform after general availability
**Cadence**: Continuous; reviewed quarterly with the SRE leadership and platform PM
**Owner**: Platform SRE (`#mlops-sre` on Slack, PagerDuty service `mlops-platform`)

---

## 0. Operating model at a glance

The MLOps platform runs as a **single multi-tenant control plane** on four EKS clusters (two prod regions, two non-prod) with **per-tenant data planes** logically isolated by namespace, network policy, ResourceQuota, and per-tenant identity. The platform team is **on-call for the platform**; tenants are on-call for **their own models**. Day-2 operations is the discipline of keeping that contract stable.

The four day-2 surfaces:

1. **Capacity** — fitting tenants into a fixed (or slowly growing) footprint without starving anyone
2. **Identity & secrets** — making sure the right thing has the right credential and only as long as needed
3. **Reliability mechanics** — backups, DR drills, certificate renewal, dependency upgrades
4. **People & process** — on-call, postmortems, capacity reviews, error-budget governance

Each is covered below with the runbook commands, dashboards, and meeting cadences that the platform team is actually expected to execute.

---

## 1. Capacity planning

### 1.1 Per-tenant quotas

Every tenant lives in a namespace `tenant-${SLUG}` with a `ResourceQuota`, a `LimitRange`, and a `PriorityClass`. Defaults are committed in `infra-gitops/tenants/${SLUG}/quota.yaml` and rendered through Argo CD.

Baseline quotas (tier-1 tenants):

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-acme
spec:
  hard:
    requests.cpu:        "200"
    requests.memory:     "800Gi"
    requests.nvidia.com/gpu: "16"      # H100 default; A100 quota tracked separately
    limits.cpu:          "400"
    limits.memory:       "1600Gi"
    persistentvolumeclaims: "100"
    requests.storage:    "10Ti"
    count/inferenceservices.serving.kserve.io: "30"
    count/trainingjobs.kubeflow.org:           "50"
```

Tier-2 tenants get 1/4 of the above. Tier-3 (experimentation only) get 1/16.

Quota changes:

- < 25% increase: SRE primary approves, takes effect on next Argo CD sync
- 25–100% increase: requires capacity-planner sign-off (see §1.3)
- \> 100% increase or new GPU class: requires platform PM + finance sign-off because of cost impact

### 1.2 Autoscaling

Three layers, each with a specific signal:

| Layer | Tool | Signal | Notes |
|---|---|---|---|
| Pod | HPA v2 | CPU + custom metric (`inflight_requests`, `queue_depth`) | Min 2 for tier-1 services; scaling stabilization 5 min up, 10 min down |
| Node | Karpenter | Unschedulable pods | Provisioners per workload class: `cpu-general`, `gpu-h100`, `gpu-a100`, `inference-cpu`, `inference-gpu` |
| Cluster | Cluster autoscaler (fallback only) | Karpenter unavailability | Disabled by default; manual enable during Karpenter incidents |

Karpenter provisioner discipline:

- GPU provisioners use **on-demand only** for training pools (interruption mid-step costs real money). Spot allowed for inference pools with a fallback NodePool to on-demand.
- TTL `consolidation.enabled: true` with `consolidationPolicy: WhenEmptyOrUnderutilized`. Idle GPU node TTL: 10 minutes. Idle CPU node TTL: 30 minutes.
- `expirationTTL: 14d` to force node recycling and pick up AMI updates.

KEDA is used for queue-driven scalers (batch scoring, training queue):

```yaml
triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123/mlops-train-queue
      queueLength: "5"
      awsRegion: us-east-1
```

### 1.3 Capacity reviews

Cadence: **monthly**, second Wednesday at 10:00 UTC, 60 minutes. Required attendees: SRE primary + secondary, platform PM, finance partner, two largest tenants by spend.

Agenda (paste from `templates/capacity-review.md`):

1. Trailing 30 days: CPU, memory, GPU utilization per node pool — target 65–75% sustained
2. Top 10 tenants by request growth and by quota saturation (`max(quota_used / quota_hard) > 0.85` over 7d triggers a conversation)
3. Karpenter cost vs forecast (`kubecost` per provisioner)
4. GPU reservation utilization (H100 reserved instances and Savings Plan coverage)
5. Forward 90-day forecast: anticipated tenant onboarding, model launches, training campaigns
6. Decisions: quota changes, provisioner changes, RI/SP commitments, headroom adjustments

Headroom rule: maintain ≥ 20% slack on CPU/memory and ≥ 15% on each GPU class. Drop below twice in a 30-day window → capacity expansion ticket within 5 business days.

### 1.4 Per-tenant chargeback

Kubecost in shared mode emits per-namespace and per-label cost. We label every workload with `acme.io/tenant`, `acme.io/cost-center`, `acme.io/workload-class`. Monthly chargeback report:

```bash
kubectl-cost namespace \
  --window 30d \
  --show-cpu --show-memory --show-gpu --show-pv \
  --show-asset-type \
  --output json > /tmp/chargeback.json

python3 ops/chargeback/build_report.py /tmp/chargeback.json \
  --out s3://acme-mlops-finops/$(date +%Y-%m)/chargeback.csv
```

The report is shared with tenant leads on the 5th business day of the following month. Disputes route to `#mlops-finops` and are resolved within 10 business days.

---

## 2. Secrets management

### 2.1 Architecture

- **HashiCorp Vault** (1.16+) is the source of truth. Deployed HA with 3 nodes per region, integrated storage (Raft), auto-unseal via AWS KMS.
- **External Secrets Operator (ESO)** (0.10+) projects Vault secrets into Kubernetes `Secret` resources via `ClusterSecretStore` per region.
- **Vault dynamic secrets** for short-lived database credentials, AWS STS tokens, and Snowflake users. Static long-lived secrets are explicitly disallowed for any new use case.

ClusterSecretStore example:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata: { name: vault-prod }
spec:
  provider:
    vault:
      server: https://vault.prod.acme.io
      path: kv
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes-prod-use1
          role: eso
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

### 2.2 Rotation policy

| Secret type | TTL | Rotation owner | Mechanism |
|---|---|---|---|
| Database creds (RDS, Aurora) | 24h max | Vault DB engine | Dynamic, no manual step |
| Snowflake creds | 24h max | Vault DB engine | Dynamic |
| AWS IAM (legacy long-lived) | 30d max | Vault AWS engine | Dynamic STS preferred; legacy keys phased out by 2026 Q3 |
| OIDC client secrets (Okta) | 180d | SRE | Vault KV + ESO; rotation runbook §2.4 |
| Webhook signing secrets | 365d | Service owner | Vault KV + ESO |
| Service mesh CA (Istio root) | 5y | Platform SRE | cert-manager + Vault PKI; intermediate rotates 1y |
| Workload identity (SPIFFE/SPIRE) | 1h | SPIRE | Automatic; no human touch |

A secret beyond its TTL is treated as a SEV-3 finding and gets ticketed automatically by `vault-policy-auditor` (cron, daily 06:00 UTC).

### 2.3 Vault dynamic DB secrets

Tenants do not hold static DB passwords. Their workloads request short-lived creds via an init container:

```bash
vault read -format=json database/creds/mlflow-readonly \
  | jq -r '.data | "POSTGRES_USER=\(.username)\nPOSTGRES_PASSWORD=\(.password)"' \
  > /vault/secrets/.env
```

Lease TTL 1h, max TTL 24h. Background job `vault-lease-renewer` runs as a sidecar to renew within the lease window.

### 2.4 Manual rotation runbook (OIDC client secret example)

```bash
# 1. Generate a new client secret in Okta admin
okta apps secrets create ${APP_ID}

# 2. Write to Vault (versioned KV v2)
vault kv put kv/platform/oidc/${APP_ID} \
  client_id=${ID} client_secret=${NEW_SECRET}

# 3. ESO will refresh within `refreshInterval`. Force-refresh:
kubectl annotate externalsecret/${NAME} -n ${NS} \
  force-sync=$(date +%s) --overwrite

# 4. Validate
kubectl get secret ${NAME} -n ${NS} -o jsonpath='{.data.client_secret}' \
  | base64 -d | head -c 8 && echo "..."

# 5. After 1 successful auth round trip, revoke the old Okta secret
okta apps secrets delete ${APP_ID} ${OLD_SECRET_ID}
```

Always keep the previous secret alive for ≥ 30 minutes for token-rotation overlap.

---

## 3. Certificate management

### 3.1 cert-manager topology

- cert-manager 1.15+ is the only issuer for TLS in the cluster
- Two `ClusterIssuer` types: `letsencrypt-prod` (public DNS-01 via Route53) and `vault-pki` (internal mesh and platform-internal)
- All `Certificate` resources set `renewBefore: 720h` (30 days). Default duration: 90 days public, 365 days internal

### 3.2 What needs a cert and who owns it

| Surface | Issuer | Owner |
|---|---|---|
| `*.prod.acme.io` ingress | letsencrypt-prod | Platform SRE |
| `*.mlops.acme.io` ingress | letsencrypt-prod | Platform SRE |
| Istio mesh mTLS | vault-pki | Platform SRE (auto) |
| Vault server cert | vault-pki bootstrap, then self-renewal | Platform SRE |
| MLflow web certs | letsencrypt-prod | Platform SRE |
| Tenant `InferenceService` ingress | letsencrypt-prod (via shared LB) | Platform SRE |

### 3.3 Renewal monitoring

Prometheus alert:

```yaml
- alert: CertificateNearExpiry
  expr: (certmanager_certificate_expiration_timestamp_seconds - time()) / 86400 < 14
  for: 1h
  labels: { severity: warning }
  annotations:
    summary: "Cert {{ $labels.name }}/{{ $labels.namespace }} expires in <14d"
```

A renewal that fails (`Ready=False` for 6h) pages SRE secondary. The most common cause is a DNS-01 zone delegation change or a missing Route53 IAM permission after a role rotation.

### 3.4 Annual mesh root rotation

The Istio mesh root CA rotates every 5 years; the intermediate every 1 year. Annual intermediate rotation runbook:

1. Generate new intermediate in Vault: `vault write pki/intermediate/generate/internal ...`
2. Sign with root, push back to Vault: `vault write pki/intermediate/set-signed certificate=@signed.pem`
3. Roll out new intermediate to Istio via `cacerts` secret, `kubectl rollout restart` istiod
4. Wait 24h dual-trust period; sidecars pick up new chain on next push
5. Revoke previous intermediate

Practice this in staging every January. Production rotation each March.

---

## 4. Backup and recovery

### 4.1 Velero scope

Velero 1.13+ is the cluster-level backup tool. Backed-up resources:

- All namespaces matching `tenant-*`
- `mlops-*` platform namespaces (config + secrets, **not** PVCs that are replicas of S3 data)
- Cluster-scoped CRDs and their instances
- PVCs in `kubeflow`, `mlflow`, `feast` only (small metadata volumes)

NOT backed up by Velero (handled by source-system snapshots):

- RDS / Aurora — automated backups + cross-region replicas, 35-day retention
- ElastiCache Redis — daily snapshots to S3
- S3 — versioning + cross-region replication; lifecycle archives to Glacier at 90d
- Snowflake — Time Travel 7d + Fail-safe 7d + zero-copy clones for DR

Velero schedules:

```yaml
- name: hourly-tenant
  schedule: "5 * * * *"
  template:
    includedNamespaces: ["tenant-*"]
    ttl: 168h
    storageLocation: aws-use1-velero
- name: daily-platform
  schedule: "30 2 * * *"
  template:
    includedNamespaces: ["mlops-*","kubeflow","monitoring","argocd"]
    ttl: 720h
    storageLocation: aws-use1-velero
```

Cross-region: `aws-use2-velero` mirrors via S3 cross-region replication. Object lock enabled (compliance mode, 30d) on both buckets.

### 4.2 Backup verification

Verification is mandatory: an unverified backup is a hope, not a backup.

**Weekly** (cron, Sunday 03:00 UTC):

```bash
velero backup create verify-$(date +%Y%m%d) \
  --include-namespaces mlops-mlflow \
  --wait

velero restore create verify-$(date +%Y%m%d) \
  --from-backup verify-$(date +%Y%m%d) \
  --namespace-mappings mlops-mlflow:verify-mlflow \
  --wait

kubectl get all -n verify-mlflow
./scripts/smoke-mlflow.sh https://verify-mlflow.staging.acme.io
kubectl delete namespace verify-mlflow
```

**Monthly**: full-platform restore in the `dr-staging` cluster. The exit criterion is a green smoke suite across MLflow, registry, gateway, and one synthetic tenant.

**Quarterly**: cross-region DR drill (§5).

### 4.3 RDS / Aurora point-in-time recovery

```bash
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier mlops-mlflow-prod \
  --db-cluster-identifier mlops-mlflow-prod-pit-$(date +%s) \
  --restore-to-time "${TIMESTAMP_ISO8601}" \
  --use-latest-restorable-time
```

PIT is the recovery path for accidental schema/data damage. Always restore to a new cluster, validate, then swap connection strings via the Vault-managed DB engine — never overwrite the live cluster.

---

## 5. Disaster recovery

### 5.1 DR targets

| Tier | RPO | RTO | Includes |
|---|---|---|---|
| 1 (revenue) | 15 min | 1 hr | Platform API, model gateways, KServe serving, Feast online |
| 2 (productivity) | 1 hr | 4 hr | MLflow, registry, training operator, pipeline runner |
| 3 (analytics) | 24 hr | 24 hr | Feast offline (Snowflake), Kubecost, audit warehouse |

### 5.2 Region pairing

- Primary: `us-east-1`. DR: `us-west-2`.
- EU primary: `eu-west-1`. DR: `eu-central-1`.

Each region pair runs an Argo CD instance with the same `infra-gitops` source of truth. Cluster state diverges only via region-specific `values-${REGION}.yaml`.

### 5.3 Failover steps (tier-1, us-east-1 → us-west-2)

1. Confirm primary is unrecoverable within RTO (avoid premature failover; document the decision in the incident)
2. Promote Aurora global cluster: `aws rds failover-global-cluster --global-cluster-identifier mlops-global --target-db-cluster-identifier arn:aws:rds:us-west-2:...`
3. Update Route53 weighted records to send 100% to `us-west-2` (TTL ≤ 60s in DR records)
4. Scale up `us-west-2` Karpenter provisioners to match prod (warm minimum capacity is half of prod)
5. Trigger `mlops-dr-failover` Argo CD ApplicationSet to apply DR-specific overlays (e.g., reduced feature-store TTL while caches warm)
6. Smoke against `us-west-2`: `pytest dr/smoke/ -m tier1 --base-url=https://api.us-west-2.acme.io`
7. Post in `#mlops-status`, page Comms

### 5.4 DR drill cadence

- **Quarterly**: tier-1 game day in production (failover and fail-back). 4-hour scheduled window. Required participants: SRE rotation, platform PM, one customer-success rep, one tenant rep
- **Monthly**: tier-2 partial-restore exercise from Velero in `dr-staging`
- **Annual**: cross-region full failover including DNS, payments, third-party callbacks

Drill output: an updated `dr-drill-${YYYY}-${QQ}.md` in `runbooks/dr-drills/`. Action items become Jira tickets with a 30-day SLA.

---

## 6. On-call

### 6.1 Rotation shape

- **Primary**: 1 week, Mon 09:00 local → next Mon 09:00 local. PagerDuty `mlops-platform-primary`.
- **Secondary**: same week, paged after 5 min of unacked primary, or directly for any SEV-1.
- **Manager on call**: month-long rotation across EMs and staff engineers. Paged for SEV-1, customer-impact, security, and any escalation involving comms.

Rotation participants must be SRE L3+ or platform engineering L4+ with the on-call qualification (completed shadow week + DR drill + 3 successful incident-leads as understudy).

### 6.2 Coverage hours

The platform is global; on-call is follow-the-sun across three regions:

- AMER: `us-east` primary
- EMEA: `dublin` primary
- APAC: `singapore` primary

Handoff at 09:00 local in the outgoing region's time zone, with a 30-minute overlap. Handoff template:

```
- Active incidents:
- Open SEV-3/4:
- Hot dependencies (degraded upstreams):
- Deploys in flight:
- Things I want you to watch:
- Outstanding pages from last shift:
```

### 6.3 Compensation and protection

- Pages outside 09:00–18:00 local in shift week are compensated (per HR policy)
- An engineer who is paged > 3 times in a single sleep period is auto-rotated off the next night with secondary swap
- On-call carry forward: any engineer paged > 6 times in a week files an `oncall-overload` ticket; the EM must respond within 2 business days

### 6.4 Tools

- PagerDuty (paging, escalation, schedules)
- Slack `#mlops-incidents` (one channel per incident, opened by `/incident new`)
- Datadog APM + Logs + Synthetic
- Grafana (linked from every alert)
- Statuspage (`status.acme.io`) — comms publishes; on-call drafts
- Notion incident workspace (single source of truth for the timeline)

---

## 7. Postmortems

### 7.1 When required

- All SEV-1 and SEV-2
- Any SEV-3 with customer impact or breached SLO
- Any near-miss flagged by on-call (e.g., near-miss data leak, near-miss outage avoided by retry)

### 7.2 Cadence

- Draft within 5 business days of incident
- Review meeting within 10 business days, 60 minutes, on Zoom with recording
- Published within 15 business days to `https://wiki.acme.io/mlops/postmortems`
- Action items tracked in Jira project `MLOPS-PM`; each has an owner and a due date; overdue items surface in the weekly SRE review

### 7.3 Template (abbreviated)

1. Summary (1 paragraph, blameless)
2. Impact (tenants, users, dollars, time)
3. Timeline (UTC, 1-minute granularity around mitigation)
4. Root cause (5-whys; not "human error")
5. Contributing factors
6. What went well
7. What didn't
8. Action items (Owner, Jira, Due)

### 7.4 Quarterly postmortem-of-postmortems

Every quarter the SRE leadership runs a meta-review: which classes of incident keep recurring, which action items keep slipping, which dependencies are most fragile. Outputs feed roadmap and capacity planning.

---

## 8. Error-budget governance

Every tier-1 SLO carries an error budget. Burn governs deployment pace.

| Burn over 30d | Result |
|---|---|
| < 50% | Normal velocity |
| 50–80% | Reduce risk-medium deploys to 1/day; increase canary soak by 50% |
| 80–100% | Freeze all non-fix changes; only fixes and security |
| > 100% | Incident; halt onboarding, postmortem the program (not just events) |

The error-budget burn dashboard is posted weekly to `#mlops-leadership`. Tenants whose models exhaust *their* SLO budget receive a "model on probation" note from the platform PM — the platform reduces autoscaling headroom and requires a remediation plan before further releases.

---

## 9. Dependency hygiene

### 9.1 What we track

- EKS control plane version (target N or N-1; never N-2)
- Karpenter, Argo CD, Argo Rollouts, Flagger, cert-manager, ESO, Velero (target N or N-1)
- KServe, Kubeflow, MLflow, Feast (target current minor with patches)
- Base images (distroless, alpine) — rebuild monthly
- Python dependency floors (annual; security patches within 14 days)

### 9.2 Upgrade cadence

- EKS minor upgrade: quarterly, full game-day, two-cluster soak (non-prod first)
- Karpenter and CRD-bearing operators: monthly review, upgrade with sync waves
- KServe: each minor, soak in `staging` for 14 days, then prod
- MLflow / Feast: each minor, coordinated with tenant comms (some tenants pin SDK versions)
- Base images: monthly automated PR via Renovate; SRE merges after Trivy passes

### 9.3 Upgrade preflight

A 2-page Notion doc for each upgrade:

- Versions: from → to
- Changelog highlights
- Breaking changes and our exposure
- Test plan
- Rollback plan
- Owner + reviewer

Stored under `wiki.acme.io/mlops/upgrades/${COMPONENT}/${VERSION}`.

---

## 10. Tenant lifecycle

### 10.1 Onboarding

1. Tenant submits intake form (workspace name, expected GPU class, data classification, expected RPS)
2. Platform PM reviews capacity impact; SRE reviews security and quota
3. `infra-gitops/tenants/${SLUG}/` PR opens with: namespace, ResourceQuota, NetworkPolicy, IAM role (IRSA), Vault policy, registry path, dashboards
4. Auto-provisioned: MLflow experiment root, Feast project, KServe runtime config, monitoring dashboards from template
5. Welcome session with tenant lead; pointers to platform docs and SDKs

SLO: time from approved intake to first successful tenant API call ≤ 3 business days.

### 10.2 Offboarding

Triggered by HR/Workspace closure or explicit request. 30-day archival window then deletion.

```bash
./scripts/tenant-offboard.sh \
  --tenant ${SLUG} \
  --archive-bucket s3://acme-mlops-archive/${SLUG}/$(date +%Y%m%d)/ \
  --confirm
```

The script:

1. Sets `acme.io/archived=true` on the namespace; KEDA scales replicas to zero
2. Snapshots MLflow experiments to Parquet in the archive bucket
3. Snapshots model artifacts under `models/${SLUG}/`
4. Exports audit log entries for the tenant to immutable storage
5. Schedules deletion at +30 days via a `CronJob`

Tenants can request restoration within the 30-day window; after that, only the immutable audit log is retained (per data-retention policy 7y).

---

## 11. Audit and compliance

- Every API call to the platform produces an audit event (actor, action, resource, tenant, outcome, timestamp, request id). Events are written by the API gateway and the Kubernetes audit webhook; both sinks land in Kinesis → S3 (`s3://acme-mlops-audit/${YYYY}/${MM}/${DD}/`) and Snowflake.
- S3 object lock (compliance mode, 7y) on the audit bucket. The platform SRE primary cannot delete those objects. Even root cannot.
- Quarterly access review: every IAM role, every Vault policy, every K8s RoleBinding. Findings tracked in Jira `MLOPS-COMP`. SOC 2 evidence pipeline pulls from the same source of truth.
- SOC 2 Type II annual; HIPAA controls validated quarterly; GDPR DSR (data subject request) playbook in `runbooks/dsr-playbook.md`. DSR response SLA: 30 days.

---

## 12. Runbook upkeep

A runbook that does not get edited is a lie. Rules:

- Every page from an alert opens a feedback loop: was the runbook linked from the alert helpful? Captured in the postmortem template.
- Each runbook page has a `Last Verified` and `Owner` header. Anything > 180 days unverified triggers a review ticket.
- Runbook PRs are reviewed by an SRE who did not write the change.
- The deployment guide, this manual, and `troubleshooting.md` are walked end-to-end during each on-call shadow week.

---

## 13. Appendix — commonly used commands

```bash
# Per-tenant quota saturation
kubectl get resourcequota -A -o json \
  | jq -r '.items[] | select(.metadata.namespace | test("^tenant-")) |
      "\(.metadata.namespace)\t\(.status.used."requests.cpu" // "0")/\(.spec.hard."requests.cpu" // "0")"'

# Top GPU consumers
kubectl get pods -A -o json \
  | jq -r '.items[] | select(.spec.containers[].resources.requests."nvidia.com/gpu" != null) |
      "\(.metadata.namespace)\t\(.metadata.name)\t\(.spec.containers[].resources.requests."nvidia.com/gpu")"' \
  | sort -k3 -nr | head

# Force a cert renewal
kubectl cert-manager renew ${CERT_NAME} -n ${NS}

# Velero one-off backup
velero backup create adhoc-${WHY} --include-namespaces ${NS} --wait

# Vault lease list for a namespace's service account
vault list sys/leases/lookup/kubernetes-prod-use1/role/${SA}
```

See also:

- `runbooks/deployment-guide.md` — release process
- `runbooks/troubleshooting.md` — failure scenarios
- `runbooks/dsr-playbook.md` — GDPR / CCPA data subject requests
- `runbooks/dr-drills/` — past DR exercise records
- `reference-implementation/monitoring/README.md` — observability stack
- `reference-implementation/platform-api/README.md` — API contract
