# Enterprise MLOps Platform — Troubleshooting Runbook

**Audience**: On-call SRE, platform engineers, tenant platform liaisons
**Scope**: The 20 production failure scenarios that account for ~85% of pages on this platform
**Cadence**: Maintained continuously; each scenario re-verified at least every 180 days
**Owner**: Platform SRE (`#mlops-sre`)

---

## 0. Using this runbook

Every scenario is structured identically:

1. **Symptoms** — what the on-call sees first (alert text, dashboard panel, customer report)
2. **Diagnosis** — concrete commands and queries that confirm or rule out the cause
3. **Remediation** — the minimum action to stop bleeding, then the cleanup
4. **Prevention** — controls to push this back to the long-tail

Read the symptoms first. If the page doesn't match, **stop** and search Notion before guessing — guessing is how we make a SEV-3 into a SEV-2.

Conventions:
- `${NS}` and `${TENANT}` are placeholders the on-call fills in from the alert
- Commands assume `kubectl` context set to the impacted cluster
- Loki commands are written for LogQL via `logcli`; Datadog equivalents exist via `dogql`

---

## 1. Tenant ResourceQuota exhaustion

**Symptoms**

- Page: `TenantQuotaExhaustionCritical{tenant="${TENANT}"}`
- Tenant Slack message: "my training jobs sit in Pending forever"
- `kubectl describe pod` shows `0/N nodes are available: pods would exceed quota`

**Diagnosis**

```bash
kubectl get resourcequota -n tenant-${TENANT} -o yaml \
  | yq '.status'

kubectl get events -n tenant-${TENANT} --sort-by=.lastTimestamp \
  | grep -i 'quota\|exceeded' | tail -20
```

Confirm which dimension is saturated. Common: `requests.nvidia.com/gpu`, `requests.memory`, `count/trainingjobs.kubeflow.org`.

Grafana panel: `MLOps / Tenants / Quota Heatmap` filtered by tenant.

**Remediation**

1. If a runaway controller is creating jobs: identify with
   ```bash
   kubectl get trainingjobs -n tenant-${TENANT} \
     --sort-by=.metadata.creationTimestamp -o wide | tail
   ```
   Coordinate with tenant lead before deleting; document in incident channel.
2. If genuine workload spike and headroom exists (§1.3 of `operations-manual.md`), apply a **temporary** quota bump capped at +25% with a 24h expiry annotation:
   ```bash
   kubectl annotate resourcequota tenant-quota -n tenant-${TENANT} \
     acme.io/temporary-bump-expires=$(date -u -d '+24 hours' +%FT%TZ) --overwrite
   ```
   Apply the bump via GitOps PR (`infra-gitops/tenants/${TENANT}/quota.yaml`) — never `kubectl edit` directly; the next Argo CD sync would revert and re-page you.
3. If no headroom: deny the bump and route the tenant to the capacity planner.

**Prevention**

- Quota saturation alert fires at 85% (warning) and 95% (critical), not at 100%
- Tenant chargeback report (§1.4) makes overshoot visible monthly
- Quota request workflow forces a capacity review for any > 25% increase

---

## 2. NCCL training stall (multi-node distributed)

**Symptoms**

- Page: `TrainingJobNoProgress{tenant,job,minutes=15}` — loss/throughput metrics flat for ≥ 15 minutes mid-training
- Pod logs show `NCCL WARN Call to ibv_modify_qp failed` or repeated `[Rank 3] Watchdog caught collective operation timeout`
- GPU utilization at near-100% on one rank, near-0% on others (deadlock)

**Diagnosis**

```bash
# Identify ranks and pods
kubectl get pods -n tenant-${TENANT} -l training.kubeflow.org/job-name=${JOB} -o wide

# Pull recent NCCL logs (NCCL_DEBUG=INFO must be set in image)
kubectl logs -n tenant-${TENANT} ${POD} --tail=500 | grep -E 'NCCL|nccl'

# Check NCCL topology
kubectl exec -n tenant-${TENANT} ${POD} -- nvidia-smi topo -m

# Verify network plane (EFA, RDMA, or TCP fallback)
kubectl exec -n tenant-${TENANT} ${POD} -- fi_info -p efa
kubectl exec -n tenant-${TENANT} ${POD} -- ip link show | grep -E 'efa|ib'
```

Typical root causes:

- A node was cordoned mid-job (Karpenter consolidation; should not happen on training pools — verify provisioner spec)
- EFA device missing on one node (mixed instance types in pool, or AMI without EFA driver)
- NCCL version mismatch across nodes (image drift)
- A noisy neighbor consumed PCIe bandwidth (rare on training pools, which should be exclusive)

**Remediation**

1. Capture state for forensics:
   ```bash
   for p in $(kubectl get pods -n tenant-${TENANT} -l training.kubeflow.org/job-name=${JOB} -o name); do
     kubectl logs -n tenant-${TENANT} $p --tail=1000 > /tmp/${JOB}-$(basename $p).log
   done
   ```
2. Restart the job from the last checkpoint (tenant action). The platform validates checkpointing is configured at submission; if it isn't, that's a tenant-side gap (link them to the docs and stop the job).
3. If a node is the culprit, cordon and drain it:
   ```bash
   kubectl cordon ${NODE}
   kubectl drain ${NODE} --ignore-daemonsets --delete-emptydir-data
   ```
   Karpenter will spin a replacement from the same provisioner.
4. If NCCL version mismatch suspected, force a fresh pod schedule (the chart's pod template uses a digest, so a delete+recreate will re-pull the canonical image).

**Prevention**

- Training provisioners have `nodeSelector: workload-class=gpu-h100-exclusive` and `taint: training=true:NoSchedule` to prevent neighbor contention
- Karpenter consolidation disabled on training pools (`consolidateAfter: Never`)
- EFA driver baked into the GPU AMI; image promotion runs a multi-node NCCL `all_reduce` test as a gate
- Tenant SDK warns if checkpoint interval is unset for jobs > 4 hours

---

## 3. Model serving latency spike (single tenant)

**Symptoms**

- Page: `InferenceLatencyP99Burn{tenant,model}` 14.4× over 1h
- Tenant Slack: "p99 jumped from 80ms to 600ms 20 minutes ago"
- Grafana `MLOps / Inference / Per-Tenant` shows divergence on one model

**Diagnosis**

```bash
# Recent deploys on the model
kubectl get inferenceservice ${MODEL} -n tenant-${TENANT} -o yaml \
  | yq '.spec.predictor.canaryTrafficPercent, .status.components.predictor.traffic'

# Pod resource saturation
kubectl top pods -n tenant-${TENANT} -l serving.kserve.io/inferenceservice=${MODEL}

# GPU utilization and memory
kubectl exec -n tenant-${TENANT} ${POD} -- nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

# HPA state
kubectl get hpa -n tenant-${TENANT} ${MODEL}-predictor
```

Loki:

```
{namespace="tenant-${TENANT}",app="${MODEL}-predictor"} |= "" | json
  | duration_ms > 500
  | line_format "{{.request_id}} {{.route}} {{.duration_ms}}ms {{.status}}"
```

Common causes:

- Recent canary promotion to a model with a regression — check `kserve` `canaryTrafficPercent` and §5.6 of `deployment-guide.md`
- GPU memory pressure from a larger batch size or longer sequence input (LLM tenants)
- Cold-start storm after a scale-from-zero event (KEDA / Knative)
- Upstream Feast online latency rising (see §6)

**Remediation**

1. If canary is implicated, abort:
   ```bash
   kubectl patch inferenceservice ${MODEL} -n tenant-${TENANT} \
     --type=merge -p '{"spec":{"predictor":{"canaryTrafficPercent":0}}}'
   ```
2. If genuine load spike and HPA at max replicas, bump max temporarily (24h expiry) and notify tenant. Coordinate with Karpenter capacity.
3. If cold-start storm, raise `minReplicas` from 0 to 1 for that model. Document the trade-off with the tenant.
4. If GPU memory pressure, ask tenant to cap batch/seq length; this is a model-side fix not a platform fix.

**Prevention**

- Canary deploys require golden-set p95 regression check (≤ 10% of stable)
- KServe autoscaler uses `concurrency` target, not request rate, for LLM models
- Per-tenant `InferenceService` template ships with sensible defaults (no scale-to-zero for tier-1 models)

---

## 4. Model serving latency spike (platform-wide)

**Symptoms**

- Burn alerts on multiple tenants simultaneously
- Grafana `MLOps / Platform / Inference Mesh` shows envoy p99 climbing across all gateways

**Diagnosis**

```bash
# Mesh control plane
kubectl get pods -n istio-system | grep -v Running

# Envoy connection pool exhaustion
kubectl logs -n istio-system -l app=istiod --tail=200 | grep -i 'envoy\|push\|fail'

# Look for slow upstream: feature store, model registry, secrets
kubectl top pods -n mlops-feast -l app=feast-serving
kubectl top pods -n mlops-registry
```

Datadog APM: open the `mlops-gateway` service and pivot by `peer.service` to find which downstream's latency exploded.

**Remediation**

1. If `istiod` is degraded: scale up `istiod` replicas, then check for an Envoy config push storm caused by a recent CRD apply (`kubectl get push -A`).
2. If a shared dependency is the cause (feast, vault, RDS), pivot to its scenario (§6, §10, §11).
3. If Karpenter is failing to add nodes (cluster autoscaler-style starvation), see §13.

**Prevention**

- Istio `pilot.env.PILOT_PUSH_THROTTLE` tuned; large CRD applies use sync waves to spread Envoy pushes
- Shared dependencies have per-caller circuit breakers in the mesh (`DestinationRule` `outlierDetection`)

---

## 5. Model registry promotion stuck

**Symptoms**

- Tenant report: "I clicked Promote-to-Staging 30 minutes ago, still says Pending"
- Page: `RegistryPromotionBacklog > 50` for ≥ 15 minutes

**Diagnosis**

```bash
# Registry controller state
kubectl logs -n mlops-registry deploy/registry-controller --tail=300

# Pending promotions queue
kubectl get modelpromotions -A --field-selector status.phase=Pending -o wide

# DB lock contention
kubectl exec -n mlops-mlflow deploy/mlflow -- \
  psql $MLFLOW_DB_URL -c "SELECT pid, state, wait_event_type, wait_event, query
                          FROM pg_stat_activity WHERE state != 'idle';"
```

Common causes:

- DB row lock held by a long-running migration or analytics query
- Registry controller leader-election flap (etcd quorum loss; rare)
- Webhook approval call out to an external system (Jira, ServiceNow) timing out
- Argo CD sync still in progress for the destination namespace

**Remediation**

1. If DB lock: identify the blocking session, coordinate kill with the owner team:
   ```bash
   psql -c "SELECT pg_cancel_backend(${PID});"
   ```
2. If controller flapping, restart with leader-election trace:
   ```bash
   kubectl rollout restart deploy/registry-controller -n mlops-registry
   ```
3. If external webhook timing out, drain the queue by temporarily relaxing the `ManualApproval` step (admin override; logged to audit).
4. Re-enqueue stuck promotions:
   ```bash
   kubectl annotate modelpromotion ${ID} -n ${NS} \
     mlops.acme.io/requeue=$(date +%s) --overwrite
   ```

**Prevention**

- Registry DB has slow-query and lock-wait alerting
- External webhook calls have 5s timeout + 3 retries with circuit breaker
- Approver SLA is 4 business hours; expired approvals fall back to a backup approver group

---

## 6. Feast online store latency / staleness

**Symptoms**

- Page: `FeatureFreshnessSlo{feast_project}` breached (`> 60s`)
- Inference services serving stale features
- Loki: `feast-serving` logs `Redis SLOWLOG` entries

**Diagnosis**

```bash
# Redis cluster health
kubectl exec -n mlops-feast feast-serving-0 -- redis-cli -h redis-online.prod cluster info
kubectl exec -n mlops-feast feast-serving-0 -- redis-cli -h redis-online.prod info stats | grep -E 'connected_clients|used_memory|evicted_keys'

# Materialization lag
curl -s https://feast.prod.acme.io/metrics | grep feast_materialization_lag_seconds

# Source freshness (Snowflake side)
snowsql -q "SELECT MAX(event_ts) FROM analytics.feature_source_${FEATURE_VIEW};"
```

**Remediation**

1. If Redis evicting (`evicted_keys` rising), the working set exceeds memory. Short-term: scale Redis vertically. Long-term: shard or shrink TTL on hot features.
2. If materialization is lagging, the upstream Snowflake job is the culprit. Page the data platform team; meanwhile, set the feature view to `online_only` if the offline source is recoverable later.
3. If connection pool exhaustion, scale `feast-serving` horizontally (`kubectl scale deploy feast-serving -n mlops-feast --replicas=N`).

**Prevention**

- Redis max-memory policy is `allkeys-lru` with 30% headroom; we alert at 70% memory used
- Materialization jobs run every 5 minutes for tier-1 features; alerts at 2× expected interval
- Connection pool sized to N concurrent inference replicas × 2

---

## 7. KServe inference pod CrashLoopBackOff

**Symptoms**

- Page: `KServeReplicaUnhealthy{tenant,model}`
- `kubectl get pods` shows `CrashLoopBackOff` on predictor pods

**Diagnosis**

```bash
kubectl describe pod -n tenant-${TENANT} ${POD}
kubectl logs -n tenant-${TENANT} ${POD} -c kserve-container --previous --tail=200

# Common: storage init failed
kubectl logs -n tenant-${TENANT} ${POD} -c storage-initializer --previous
```

Common causes:

- `storageUri` points to an S3 path the IRSA role can't read (tenant published model under wrong key)
- Image pull failure (private registry, missing `imagePullSecret`)
- Model framework runtime mismatch (Triton model loaded into TorchServe)
- OOMKill on init (model too large for requested memory)

**Remediation**

1. For S3 permission: validate the tenant's IRSA role:
   ```bash
   aws sts assume-role --role-arn arn:aws:iam::${ACC}:role/tenant-${TENANT}-mlops \
     --role-session-name debug
   aws s3 ls ${STORAGE_URI}
   ```
2. For OOM: bump requests/limits via the `InferenceService` spec; if tenant misjudged size, link them to model sizing guide.
3. For runtime mismatch: check `predictor.model.modelFormat.name` matches the published artifact.

**Prevention**

- Tenant SDK validates `storageUri` accessibility at publish-time, not at deploy-time
- Default `InferenceService` template sizes resources from the registry's recorded model footprint
- Registry rejects publishes that don't include a `framework` and `min_memory_gb` field

---

## 8. GitOps (Argo CD) drift

**Symptoms**

- Page: `ArgoAppOutOfSync{app}` persisting > 30 minutes
- Drift dashboard shows resources changed outside of Git

**Diagnosis**

```bash
argocd app get ${APP}
argocd app diff ${APP}
# Identify who touched what:
kubectl get events -n ${NS} --sort-by=.lastTimestamp | head -50
kubectl get ${KIND} ${NAME} -n ${NS} -o yaml | yq '.metadata.managedFields'
```

Common causes:

- Operator wrote a status-like field into spec (controller mutation)
- Someone ran `kubectl edit` (audit log will tell you who)
- A HelmRelease default re-injected a value because `valueFrom` resolution changed
- Webhook mutation (e.g., istio-injection sidecar resource bumps)

**Remediation**

1. If it's a benign controller mutation, add `argocd.argoproj.io/sync-options: ServerSideApply=true` and `.spec.ignoreDifferences` entry for the field.
2. If a human edited the cluster, force a hard sync, then file a Sev-3 against the offender:
   ```bash
   argocd app sync ${APP} --force
   ```
3. If webhook mutation, exclude the field from drift via `ignoreDifferences`.

**Prevention**

- RBAC: `kubectl edit` on prod is gated by `kyverno` to platform SREs only; tenants get read-only on namespace plus `argo create app` for their own apps
- Argo CD self-heal enabled for tier-1 platform namespaces
- Audit log forwards `kubectl` user identity to Datadog for traceability

---

## 9. Secrets unavailability (ESO / Vault)

**Symptoms**

- Page: `ExternalSecretReconcileFailed{namespace,name}` or `VaultSealed`
- Pods stuck in `CreateContainerConfigError`, `Secret not found`
- Loki: `external-secrets` logs `permission denied` from Vault

**Diagnosis**

```bash
kubectl get externalsecret -A | grep -v SecretSynced
kubectl describe externalsecret ${NAME} -n ${NS}

# Vault status
kubectl exec -n vault vault-0 -- vault status
kubectl exec -n vault vault-0 -- vault read sys/health

# Auth path check
kubectl exec -n vault vault-0 -- vault read auth/kubernetes-prod-use1/role/eso
```

Common causes:

- Vault auto-unseal failed after a KMS region issue
- Service account JWT iss/aud mismatch after a cluster upgrade
- Vault policy missing a path the application added in a new version
- Network policy regression blocks ESO from reaching Vault

**Remediation**

1. If Vault sealed: confirm auto-unseal config, then manually unseal as last resort. Validate Raft quorum.
2. If JWT mismatch: update Vault's Kubernetes auth `issuer` to the new OIDC issuer URL of the cluster (post-EKS upgrade scenario).
3. If policy missing: PR the policy through GitOps, do not `vault policy write` ad hoc except in active incident.
4. While remediating, **do not** create local `Secret` resources by hand — they will desync and you will be paged again at the next ESO refresh.

**Prevention**

- Vault auto-unseal monitored; quorum loss alerts immediately
- Policies live in `infra-gitops/vault/policies/` and are diffed before apply
- ESO `refreshInterval` defaults to 1h; tier-1 secrets use 5m
- EKS upgrade runbook includes "validate Vault Kubernetes auth issuer" step

---

## 10. RDS / Aurora performance regression

**Symptoms**

- Page: `MLflowApiLatencyHigh` or `RegistryDbCpuHigh`
- RDS Performance Insights shows top SQL waiting on locks or buffer pool

**Diagnosis**

```bash
aws rds describe-db-clusters --db-cluster-identifier mlops-mlflow-prod
aws cloudwatch get-metric-statistics --namespace AWS/RDS \
  --metric-name CPUUtilization --statistics Average \
  --start-time $(date -u -d '1 hour ago' +%FT%TZ) --end-time $(date -u +%FT%TZ) \
  --period 60 --dimensions Name=DBClusterIdentifier,Value=mlops-mlflow-prod

# In-cluster psql jump-host
kubectl run pg --rm -it --image=postgres:16 -- bash
# Inside: PGPASSWORD=$(vault read -field=password ...) psql ...
\d+ experiments
SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
```

**Remediation**

1. If a single query dominates, ask the owning team to fix (index missing, full table scan, no `LIMIT`).
2. If autovacuum is behind: tune `autovacuum_vacuum_scale_factor` per table; for large tables, scheduled vacuum cron is preferred.
3. If genuine load, scale the writer instance class; reads should already be served by reader endpoints.
4. As last resort, fail over to the secondary to clear connection state. Coordinate; this kills in-flight connections.

**Prevention**

- pg_stat_statements always enabled; weekly top-N reviewed by data platform
- Per-table autovacuum tuning for MLflow `runs`, `tags`, `metrics`
- Connection pooler (PgBouncer) in front of writer with `transaction` pool mode

---

## 11. Observability pipeline back-pressure

**Symptoms**

- Page: `OtelCollectorQueueSaturated > 80%` or `LokiIngesterBackoff`
- Dashboards show gaps in metrics/logs in the last N minutes
- Grafana panels labeled `No data` for tier-1 SLOs

**Diagnosis**

```bash
# OTel collector queue
kubectl -n observability exec deploy/otel-collector -- \
  curl -s localhost:8888/metrics | grep -E 'otelcol_exporter_queue_size|otelcol_exporter_send_failed'

# Loki ingester
kubectl -n observability logs -l app=loki,role=ingester --tail=200 | grep -i 'rate\|throttle\|429'

# Thanos receive
kubectl -n observability logs -l app=thanos-receive --tail=200 | grep -E 'remote_write|hashring'
```

Common causes:

- A tenant logged a high-cardinality label (e.g., `request_id` as a label) — explodes series count
- Loki S3 backend rate-limited
- Thanos receive hashring rebalance in progress
- OTel collector pinned to a single replica due to recent config change

**Remediation**

1. Identify the noisy tenant:
   ```
   logcli query --limit=5 'topk(10, count by (label) ({namespace=~"tenant-.+"}))'
   ```
2. Apply a Loki streams limit override for the offender (`runtime_config.yaml`), notify the tenant, and open a `MLOPS-OBS` ticket for them to drop the label.
3. Scale OTel collectors horizontally (DaemonSet → already per-node; for gateway collector, scale replicas).
4. If Thanos receive rebalance, wait it out; receivers shed load to peers automatically.

**Prevention**

- Prometheus relabel rules drop labels not in an allow-list
- Tenant SDK rejects `request_id` and similar high-cardinality fields as labels (forces them into log body or trace attributes)
- Loki global limit on series per tenant; per-tenant burn alert

---

## 12. Argo Workflows / Kubeflow Pipelines stuck

**Symptoms**

- Tenant: "my pipeline shows Running but no step is making progress"
- Page: `WorkflowDurationP99 > 2h` for a known-fast pipeline

**Diagnosis**

```bash
kubectl get workflow -n tenant-${TENANT} ${WF} -o yaml | yq '.status'
kubectl logs -n argo deploy/workflow-controller --tail=300 | grep ${WF}
kubectl get pods -n tenant-${TENANT} -l workflows.argoproj.io/workflow=${WF}
```

Common causes:

- Controller leader-election lost; workflows pause
- Artifact upload to S3 failing (bucket policy change)
- A step container stuck in `ImagePullBackOff` from a private registry rate-limit

**Remediation**

1. Restart `workflow-controller` if leader is unhealthy.
2. For artifact failure, verify IRSA + S3 policy, then `argo retry ${WF}`.
3. For image pull issue, switch to GHCR pull-through cache (configured at the node containerd level).

**Prevention**

- Workflow controller redundancy with active-passive leader election and PodDisruptionBudget
- Node-level containerd pull-through cache for `ghcr.io`, `docker.io`, `quay.io`
- IRSA policy changes go through Argo CD with a smoke test that submits a no-op workflow

---

## 13. Karpenter cannot provision nodes (GPU)

**Symptoms**

- Page: `KarpenterProvisioningFailed{nodepool="gpu-h100"}` or `PodPendingHighGpu > 10 min`
- Datadog: AWS API errors `InsufficientInstanceCapacity` in the karpenter logs

**Diagnosis**

```bash
kubectl logs -n karpenter deploy/karpenter --tail=300 | grep -i 'provision\|insufficient\|error'

# Show pending pods with their requested instance type / zone
kubectl get pods -A --field-selector=status.phase=Pending -o json \
  | jq '.items[] | select(.spec.nodeSelector["karpenter.k8s.aws/instance-family"]=="p5") |
        {ns:.metadata.namespace, name:.metadata.name, zones:.spec.nodeSelector["topology.kubernetes.io/zone"]}'

# Reserved capacity vs in-use
aws ec2 describe-capacity-reservations \
  --filters Name=instance-type,Values=p5.48xlarge Name=state,Values=active
```

Common causes:

- Genuine AWS capacity shortage for H100 (`p5.48xlarge`)
- Capacity Reservation expired or not attached to the right account
- AZ constraint too narrow (pool restricted to one AZ)
- Service quotas (e.g., `vCPUs for P5 instances`) hit

**Remediation**

1. Confirm quota:
   ```bash
   aws service-quotas get-service-quota \
     --service-code ec2 \
     --quota-code L-A4F6F8D2  # "Running On-Demand P instances"
   ```
   Request increase via AWS console if applicable (24–48h turnaround).
2. Widen AZ allowance temporarily (`spec.requirements.topology.kubernetes.io/zone`). Be aware of cross-AZ training cost.
3. Fail over batch training to the DR region if EU/US balance allows.
4. Communicate to tenants: capacity event, ETA, workarounds.

**Prevention**

- Maintain Savings Plan + Capacity Reservation for committed baseline H100 capacity
- Karpenter pool spans ≥ 2 AZs by default
- Capacity dashboard tracks reservation utilization weekly

---

## 14. EKS control-plane upgrade aftermath

**Symptoms**

- After an EKS minor upgrade, intermittent webhook calls fail; some operators report API server timeouts
- New pods take 30+ seconds to schedule

**Diagnosis**

```bash
kubectl get apiservices | grep -v True
kubectl logs -n kube-system kube-controller-manager... | grep -i 'webhook\|deprecat'
```

Common causes:

- Mutating/validating webhook with TLS cert that lost a SAN after CA rotation
- Deprecated APIs were removed; controllers still calling them
- Aggregated API server (custom metrics) lost connection to its backing service

**Remediation**

1. Restart impacted webhooks; verify cert SANs include the new control-plane endpoint where applicable.
2. Roll back to N-1 EKS only if SEV-1; otherwise patch forward.
3. For deprecated APIs, ship the controller upgrade that fixed them.

**Prevention**

- EKS upgrade preflight runs `pluto detect-api-resources` and `kube-no-trouble` on all manifests
- Webhooks use cert-manager-managed certs with SAN auto-updated from cluster info
- Upgrade game-day in non-prod first

---

## 15. Cross-tenant data leak suspected (SEV-1)

**Symptoms**

- Tenant report: "I see tenant B's experiment in my MLflow UI"
- Or: API log shows a tenant token returning a result for a resource owned by another tenant

**Diagnosis**

**Do not** start with debugging. Start with containment.

1. Open SEV-1 incident; page security on-call.
2. Quarantine the suspected request path: identify the gateway route or service; if it can be turned off without total outage, turn it off.
3. Capture evidence: API gateway access logs for the time window, audit log entries, MLflow access logs.

Then:

```bash
# Audit log slice (Snowflake or S3 → Athena)
SELECT actor_tenant, target_tenant, resource, action, outcome, request_id, ts
FROM mlops_audit.events
WHERE ts BETWEEN '${T1}' AND '${T2}'
  AND actor_tenant <> target_tenant
ORDER BY ts;
```

**Remediation**

1. If a single bug, ship the smallest possible fix on emergency change track (§9 of `deployment-guide.md`).
2. Revoke any tokens that may have observed cross-tenant data; require reauth.
3. Notify affected tenants per the contractual SLA (most tenants are 72h; check the contract).
4. File regulator notification if PII / PHI involved (legal-driven).
5. Postmortem mandatory; will involve security, legal, and platform leadership.

**Prevention**

- Tenant scoping enforced at three layers: gateway claim check, service-side tenant filter on every query, database row-level security on the MLflow schema
- Per-tenant integration tests in CI assert "tenant A request never returns tenant B data" across a matrix of endpoints
- Audit log dashboards include a panel "actor_tenant ≠ target_tenant" which should always be zero except for explicit admin actions

---

## 16. Regulator / audit data request (SOC 2, HIPAA, GDPR)

**Symptoms**

- Internal ticket: legal/compliance requests "all model decisions for subject X between dates Y and Z" or "all access events for system A in 2025"
- Auditor onsite: requests evidence on a control

**Diagnosis**

```bash
# Identify data location for the request
./scripts/dsr-locator.py --subject-id ${ID} \
  --systems mlflow,feast-offline,inference-logs,audit-events
```

The script emits a JSON manifest of: which buckets/tables hold what, retention windows, and the export plan.

**Remediation**

1. Acknowledge the request in the compliance ticketing system; start the SLA clock.
2. Pull the data from the immutable audit store (`s3://acme-mlops-audit/`) for access events; from MLflow + registry for model history; from inference logs for decisions.
3. Package with chain of custody: signed manifest, SHA256 hashes, exporter identity.
4. Legal reviews before transmission. Platform never sends data directly to a regulator; that goes through legal.

**Prevention**

- Immutable audit storage with S3 Object Lock (compliance mode, 7y)
- Inference log retention per data class (PII: 90 days, non-PII: 1 year); retention enforced by lifecycle policy
- Quarterly tabletop exercise: simulate a regulator data request end to end

---

## 17. Vault sealed after KMS regional event

**Symptoms**

- All `external-secrets` reconcilers fail
- `vault status` shows `Sealed: true` and `Initialized: true`
- AWS KMS shows API errors in the region

**Diagnosis**

```bash
kubectl exec -n vault vault-0 -- vault status
aws kms describe-key --key-id ${VAULT_AUTO_UNSEAL_KEY_ARN}
```

**Remediation**

1. Confirm KMS regional incident on AWS Health Dashboard.
2. If KMS recovers within minutes, restart Vault pods to retry auto-unseal:
   ```bash
   kubectl delete pod -n vault -l app=vault
   ```
3. If KMS outage is prolonged, fail over to the DR Vault cluster in the paired region (Raft cluster mirror with its own KMS key).
4. Once primary KMS restores, re-mirror data and re-elect primary at next maintenance window — do not flap leadership during the event.

**Prevention**

- Multi-region Vault with independent KMS keys in each region
- Auto-unseal failure paged immediately; not lumped into a generic Vault alert
- Annual drill: induce KMS denial in a non-prod region and verify automatic failover

---

## 18. Container image registry (GHCR) rate-limited

**Symptoms**

- Many pods stuck in `ImagePullBackOff` with `429 Too Many Requests`
- New tenant onboarding fails at first pod schedule

**Diagnosis**

```bash
kubectl describe pod ${POD} -n ${NS} | grep -A3 'Failed to pull'
```

**Remediation**

1. Confirm the pull-through cache is healthy:
   ```bash
   kubectl get pods -n harbor -l app=harbor-registry
   ```
2. Force critical pods to the cached path: `harbor.acme.io/ghcr-proxy/...`.
3. If the cache itself is the bottleneck, scale registry replicas and S3 backend throughput.

**Prevention**

- All node containerd configs route through Harbor pull-through cache for `ghcr.io`
- Pre-pull tier-1 images via a `DaemonSet` at boot
- Authenticate to GHCR even for "public" images to access higher rate limits

---

## 19. Per-namespace network policy regression

**Symptoms**

- Tenant: "my training job can no longer reach the feature store"
- Page: `EgressBlocked{from,to}` from the network policy auditor

**Diagnosis**

```bash
kubectl get networkpolicies -n tenant-${TENANT}
# Trace a representative connection:
kubectl exec -n tenant-${TENANT} ${POD} -- nc -vz feast-serving.mlops-feast 6566
```

Common causes:

- A new default-deny policy applied without the tenant's egress carve-outs
- Calico/Cilium plugin upgrade silently changed semantics (e.g., DNS egress no longer auto-allowed)
- A tenant-managed policy collided with a platform-managed one

**Remediation**

1. Restore prior policy from Argo CD history if a platform PR caused it:
   ```bash
   argocd app history mlops-network-policies
   argocd app sync mlops-network-policies --revision ${PREVIOUS}
   ```
2. Add the missing egress; coordinate with the tenant on the proper allow-list pattern (avoid `to: {}` wildcards).

**Prevention**

- Per-tenant policy linter runs in CI on tenant-namespace PRs
- Mesh tests (`hey`-driven, post-deploy) include cross-namespace probes for known dependency edges

---

## 20. Mass tenant onboarding burst

**Symptoms**

- 5+ tenants land in the same week; control plane shows spike in API server load
- Argo CD reconciliation latency rises
- Per-tenant dashboards take minutes to render

**Diagnosis**

```bash
kubectl get applications -n argocd --no-headers | wc -l
kubectl top pods -n argocd
kubectl get events -n argocd --sort-by=.lastTimestamp | tail
```

**Remediation**

1. Throttle the onboarding pipeline temporarily; serialize new tenant Applications.
2. Scale Argo CD `application-controller` replicas; bump `controller.shardingAlgorithm` if needed.
3. For dashboard pressure, ensure Grafana datasource caching is on; precompute heavy panels into Thanos rules.

**Prevention**

- Onboarding pipeline rate-limited to N tenants/day (default 3) with override only by platform PM
- Argo CD sharded by cluster from day one; each shard sized for 5× expected growth
- Per-tenant dashboards instantiated from a template that has been load-tested
