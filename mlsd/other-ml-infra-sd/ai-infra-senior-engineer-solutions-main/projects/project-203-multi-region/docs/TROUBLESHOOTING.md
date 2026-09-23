# Troubleshooting Guide: Multi-Region ML Platform

This guide documents the twelve most common failure modes for the multi-cloud, multi-region serving platform (AWS EKS in `us-west-2`, GCP GKE in `eu-west-1`, Azure AKS in `ap-south-1`). Each entry follows the same structure: **Symptoms** that surface in dashboards or logs, **Diagnosis** commands to confirm root cause, and **Remediation** steps with rollback notes.

The guide assumes you are running:

- Terraform >= 1.5.0
- kubectl >= 1.28 (matched to each cluster's control-plane minor version)
- AWS CLI v2.15, gcloud 463+, Azure CLI 2.57+
- Argo CD 2.10 with `ApplicationSet` controller
- External-DNS 0.14 backed by Route 53
- cert-manager 1.14 with cluster-issuer per region
- Prometheus 2.51 federated to a central Thanos 0.34 store

---

## 1. Regional Failover Stuck (DNS updated, traffic not draining)

### Symptoms

- `failover_controller` logs show `state=DRAINING` for >300 seconds with no progression to `EVACUATED`.
- Route 53 health checks for the failed region report `Failure` but the secondary region's `request_rate` is flat in Grafana.
- `kubectl get pods -n ml-serving --context=us-west-2` shows pods `Running` while Envoy access logs in `eu-west-1` show no spike.
- `dig +short api.ml.example.com @8.8.8.8` still returns the failed-region IP for some resolvers.

### Diagnosis

```bash
# Check Route53 record state and TTL
aws route53 list-resource-record-sets --hosted-zone-id Z2FDTNDATAQYW2 \
  | jq '.ResourceRecordSets[] | select(.Name=="api.ml.example.com.")'

# Confirm health check status across regions
aws route53 get-health-check-status --health-check-id <id>

# Inspect failover controller state machine
kubectl logs -n platform deployment/failover-controller --tail=200 \
  | grep -E "state_transition|health_score"
```

The most common cause is a **TTL mismatch**: the A record advertises `TTL=300` but downstream resolvers (notably Google Public DNS and some ISP resolvers) honor the upstream TTL. A second cause is `evaluate_target_health=false` on the Route 53 alias.

### Remediation

1. Confirm the secondary regions are actually healthy: `./scripts/health_check.sh --region eu-west-1 --region ap-south-1`.
2. Reduce TTL **before** any planned failover to 30 seconds at least one hour in advance (Route 53 propagates the lower TTL itself within one TTL cycle).
3. If a live incident, force the failover controller to escalate to **traffic-shift mode**, which uses GeoDNS weighted records (10/90 split) rather than relying on health-check eviction:
   ```bash
   kubectl exec -n platform deploy/failover-controller -- \
     failoverctl shift --from us-west-2 --to eu-west-1 --weight 90
   ```
4. Drain at the load-balancer layer too. EKS NLB has a `deregistration_delay.timeout_seconds=300` default; verify and shorten with `aws elbv2 modify-target-group-attributes`.
5. Post-incident, set `evaluate_target_health = true` in `terraform/modules/dns/main.tf` and re-apply.

---

## 2. Cross-Region Replication Lag Exceeding SLO

### Symptoms

- Prometheus alert `ReplicationLagHigh` (defined as `replication_lag_seconds > 300`) firing for one or more model-version pairs.
- `model_replicator` logs show `boto3.exceptions.S3UploadFailedError` or `google.api_core.exceptions.DeadlineExceeded`.
- Predictions in `ap-south-1` use model version `v2024.05.14` while `us-west-2` is already on `v2024.05.15`.

### Diagnosis

```bash
# Per-region model versions
for r in us-west-2 eu-west-1 ap-south-1; do
  kubectl --context=$r get configmap -n ml-serving active-model \
    -o jsonpath='{.data.version}'
  echo
done

# Replicator queue depth and last success
curl -s http://replicator.platform.svc:9100/metrics \
  | grep -E "replication_queue_depth|replication_last_success_timestamp"

# Inter-region egress saturation (AWS NAT Gateway is a frequent bottleneck)
aws cloudwatch get-metric-statistics --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination --statistics Maximum \
  --start-time $(date -u -d '1 hour ago' +%FT%TZ) \
  --end-time $(date -u +%FT%TZ) --period 60
```

### Remediation

- If NAT throughput is saturated, enable **VPC endpoints** for `s3` and `dynamodb` (gateway endpoints, free) and **PrivateLink** for the destination bucket (interface endpoint, ~$7.20/endpoint/AZ/month).
- For cross-cloud transfers, switch the replicator from object-stream copy to a **manifest + parallel chunk** strategy: split files >100 MB into 16 MiB parts and upload concurrently (`max_concurrent=32`). The `src/replication/model_replicator.py` constant `CHUNK_SIZE_BYTES` controls this.
- Backpressure: if the queue is >500 items, pause client uploads via the registry API (`POST /v1/registry/pause`) until the replicator drains. Do not drop items; the queue is persisted to Redis with `appendonly yes`.
- Long-term, replace point-to-point copying with **S3 Replication Time Control (RTC)** for AWS→AWS pairs (15-minute SLA) and **Storage Transfer Service** for AWS↔GCP. Cross-cloud RTC equivalents do not exist; expect 5-10 minute baseline lag.

---

## 3. Model Drift Between Regions

### Symptoms

- Prediction parity tests (`tests/integration/test_region_parity.py`) report `drift_pct > 0.5` for the same input feature vector.
- Inference confidence histograms in Grafana diverge between regions for the `recommendation-v3` model.
- Customer reports inconsistent results when their traffic shifts between regions.

### Diagnosis

```bash
# Hash the loaded model artifact on each pod
for r in us-west-2 eu-west-1 ap-south-1; do
  kubectl --context=$r exec -n ml-serving deploy/inference \
    -- sha256sum /var/lib/models/active/model.onnx
done

# Compare feature pipeline versions
for r in us-west-2 eu-west-1 ap-south-1; do
  kubectl --context=$r get deploy -n ml-serving inference \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
done
```

If the SHA-256 digests differ, replication itself is suspect (see entry 2). If digests match but predictions diverge, the **feature pipeline** is the culprit—commonly because feature-store TTLs differ between regions or a region is serving from a stale read replica.

### Remediation

1. Pin the model SHA in the inference deployment's `MODEL_DIGEST` env var and refuse to start if local artifact mismatches; this turns silent drift into a `CrashLoopBackOff` that paging can detect.
2. Centralize the feature store on a single writer (e.g., AWS Aurora Global Database with `us-west-2` as the writer region) and treat regional replicas as **strict read-only**. Reject writes from non-writer regions at the application layer.
3. Add a synthetic-canary test job (`CronJob` every 5 minutes) that runs the same 100 fixed inputs against all three regions and exports `region_parity_drift_pct` to Prometheus.
4. For model-promotion races, use an **atomic registry pointer**: clients read the active version from a single source (DynamoDB Global Table, conditional write with `version > previous_version`).

---

## 4. DNS Cache Poisoning During Failover (Resolver Stickiness)

### Symptoms

- Failover completed in Route 53, but `kubectl logs -n ml-serving deploy/inference --context=eu-west-1` shows 5-15% of clients still resolving the old IP for **hours** after the TTL expired.
- Mostly affects mobile clients and a long tail of corporate networks behind NATs.

### Diagnosis

```bash
# Check authoritative TTL vs what resolvers return
dig +noall +answer api.ml.example.com @ns-1.awsdns-00.com
dig +noall +answer api.ml.example.com @8.8.8.8
dig +noall +answer api.ml.example.com @1.1.1.1

# Look for "negative caching" in resolver responses (SOA minimum)
dig +trace api.ml.example.com | grep -i soa
```

The root cause is rarely the authoritative TTL; it is usually one of:

- A client SDK caching the IP at the process level for the JVM/Python default of "forever".
- A corporate egress proxy with a hard-coded host file.
- A CDN edge that ignores client TTLs (Cloudflare Workers, Akamai EdgeWorkers).

### Remediation

- **Application-level health-aware clients**: ship an SDK that does `getaddrinfo()` per request or uses a 30-second cache, not the JVM `networkaddress.cache.ttl=-1` default.
- Use **Anycast IPs** (AWS Global Accelerator, GCP Global LB, Azure Front Door) so the same IP routes to whichever region is healthy. This eliminates DNS as a failover dependency for ~90% of traffic, leaving only direct API consumers exposed to DNS-cache issues.
- For the long tail, expose a `/region-hint` endpoint that returns the current healthy region; SDKs use this as a fallback.
- Document a hard rule: **TTL = 60s** for production hostnames, **TTL = 300s** for low-tier services. Enforce via OPA Gatekeeper policy on the External-DNS `DNSEndpoint` CRD.

---

## 5. Certificate Expiry in One Region (Cascade Risk)

### Symptoms

- Browsers show `NET::ERR_CERT_DATE_INVALID` for `api.eu.ml.example.com`.
- `cert-manager` controller logs in `eu-west-1` show `ACME order failed: rateLimited: too many requests`.
- Other regions are healthy. Failover routing shifts all traffic to `us-west-2` and overloads it.

### Diagnosis

```bash
# Check certificate expiry across regions
for r in us-west-2 eu-west-1 ap-south-1; do
  echo "=== $r ==="
  kubectl --context=$r get certificate -A \
    -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,EXPIRES:.status.notAfter
done

# Inspect cert-manager events
kubectl --context=eu-west-1 -n cert-manager logs deploy/cert-manager --tail=100 \
  | grep -i 'order\|challenge\|rate'
```

### Remediation

- Set `Certificate.spec.renewBefore=720h` (30 days) so renewals begin a month before expiry. cert-manager default of 30 days is acceptable; **never** set this below `168h` (7 days).
- Use **DNS-01** challenges (with Route 53 IAM permissions scoped per region) instead of HTTP-01. DNS-01 works even when the cluster's ingress is unreachable from the public internet, which is critical during partial outages.
- Configure two issuers per region: `letsencrypt-primary` and a fallback `letsencrypt-backup` with a different ACME account. Rate limits are per-account.
- Add Prometheus alert `CertificateExpiringSoon` at 21 days (warning) and 7 days (critical). Page on the critical alert.
- Maintain a **break-glass procedure**: a pre-issued long-lived wildcard cert (90 days, DigiCert/Sectigo) stored in AWS Secrets Manager + GCP Secret Manager + Azure Key Vault. Document the manual install steps.

---

## 6. IAM / Workload-Identity Propagation Lag

### Symptoms

- New pods in `gke-eu-west-1` get `403: caller does not have permission` for the first 30-180 seconds after startup, then succeed.
- Argo CD `Sync` operations briefly fail with `denied: requested access to the resource is denied` when pulling from ECR.
- After a Terraform apply that added a new IAM binding, only some pods see the binding.

### Diagnosis

```bash
# Confirm the service account annotation is in place
kubectl get sa -n ml-serving inference -o yaml | grep -E "iam\.gke\.io|eks\.amazonaws\.com"

# On AWS, check IRSA assume-role from inside the pod
kubectl exec -n ml-serving deploy/inference -- aws sts get-caller-identity

# On GCP, dump the metadata server's token
kubectl exec -n ml-serving deploy/inference -- \
  curl -s -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
```

### Remediation

- IRSA (AWS) updates propagate via the EKS Pod Identity webhook within ~10 seconds, but the **trust policy update** on the IAM role can lag 30-60 seconds. After `terraform apply`, sleep 90 seconds before scheduling workloads.
- For GCP Workload Identity, binding propagation is **eventually consistent up to 7 minutes**. Use `kubectl rollout restart` after binding changes and add `initialDelaySeconds=30` on readiness probes that depend on the credential.
- Add a startup retry loop in application code: wrap the first cloud-SDK call in exponential backoff (1s, 2s, 4s, 8s, 16s, 32s = max 63s) and fail-fast only after that.
- Use **separate service accounts per workload** (least privilege). Sharing a single `default` SA across the cluster amplifies blast radius when bindings change.
- For Azure, prefer **Workload Identity (federated tokens)** over the deprecated AAD Pod Identity; the former is consistent within seconds, the latter could take minutes.

---

## 7. Billing Surprises (Cross-Region Egress, NAT, Inter-Cloud Transfer)

### Symptoms

- Monthly AWS bill jumps 40% with no traffic increase. The delta lives in `AWS Data Transfer - DataTransfer-Regional-Bytes` and `NatGateway-Bytes`.
- GCP "Network → Internet egress (Americas to Asia)" line item appears for the first time at ~$0.12/GB.
- Azure bandwidth charges show outbound to `Other Continents`.

### Diagnosis

```bash
# AWS - identify top egress sources
aws ce get-cost-and-usage --time-period Start=2026-04-01,End=2026-05-01 \
  --granularity DAILY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=USAGE_TYPE \
  | jq '.ResultsByTime[].Groups[] | select(.Keys[] | test("DataTransfer|Nat"))'

# Use VPC Flow Logs queried via Athena for offender pods
# (assumes flow logs are exported to S3 + Athena table 'vpc_flow_logs')
```

### Remediation

- **Tag everything**. Enforce `cost-center`, `team`, `service` tags via Kyverno or OPA Gatekeeper. Untagged resources should be quarantined.
- Re-architect the replicator to use **same-cloud-first**: AWS→AWS replication is $0.02/GB, AWS→GCP is $0.09/GB plus GCP ingress (free) plus GCP→Azure egress for the next hop. Hub-and-spoke through one cloud's region can cost 3-5x.
- Use **VPC Endpoints** (gateway endpoints for S3/DynamoDB are free; interface endpoints are billed but cheaper than NAT egress at >1 TB/month).
- For Prometheus federation, do **not** federate raw 15-second samples cross-region. Use a remote-write pipeline with `relabel_configs` to drop high-cardinality labels and aggregate to 1-minute resolution. This typically cuts egress 90%.
- Set up **budget alerts** at 50%, 80%, 100%, 120% of forecast. AWS Budgets, GCP Budgets, Azure Cost Management each have free tier alerts.
- Run `src/cost/cost_analyzer.py` daily as a `CronJob`; export `cloud_cost_usd` to Prometheus; alert on `predict_linear(cloud_cost_usd[7d], 86400 * 30) > monthly_budget`.

---

## 8. Request Routed to Wrong Region (GeoDNS Misclassification)

### Symptoms

- A user in Mumbai is consistently routed to `us-west-2`, adding 220 ms RTT.
- Datadog RUM shows `region=us-west-2, client_country=IN` for ~2% of traffic.
- Anycast (Global Accelerator) is enabled but a specific IP block is not seeing the expected closest PoP.

### Diagnosis

```bash
# Verify Route 53 geolocation rules
aws route53 list-resource-record-sets --hosted-zone-id Z2FDTNDATAQYW2 \
  | jq '.ResourceRecordSets[] | select(.GeoLocation)'

# Test resolution from a specific resolver
curl -s "https://1.1.1.1/dns-query?name=api.ml.example.com&type=A" \
  -H "Accept: application/dns-json"

# Confirm Global Accelerator endpoint groups
aws globalaccelerator list-endpoint-groups \
  --listener-arn arn:aws:globalaccelerator::...
```

### Remediation

- GeoDNS misclassifications often come from **mobile-carrier CGNAT** exit points; a carrier's APN may exit to the public internet in Singapore even for users physically in Mumbai. The fix is client-side: app sends its `country-hint` header derived from device locale or GPS.
- Switch from country-level to **continent-level** routing for the common case, plus explicit country overrides (`IN, BD, LK → ap-south-1`).
- Use **Latency-Based Routing (LBR)** as the primary and Geolocation as a fallback. LBR uses AWS's measured latencies, which are more accurate than IP geolocation databases.
- For a known systemic miss (e.g., a specific ASN), use `aws route53 change-resource-record-sets` with `Subnet`-based routing (paid Resolver feature).

---

## 9. etcd Quorum Loss in a Regional Cluster

### Symptoms

- `kubectl --context=eu-west-1 get nodes` hangs or returns `etcdserver: request timed out`.
- API server logs flood with `rafthttp: lost the TCP streaming connection`.
- All control-plane operations fail for that cluster; workloads still run on existing nodes.

### Diagnosis

This is largely transparent on managed clusters (EKS, GKE, AKS) because the cloud provider runs etcd. However, you can experience the same symptoms when:

- A regional AZ outage takes down enough etcd members. EKS spans 3 AZs by default; losing 2 causes quorum loss.
- A misbehaving controller floods the API with `Update` requests, exhausting etcd's `--max-request-bytes`.

```bash
# EKS control-plane logs (must be enabled at cluster creation)
aws logs tail /aws/eks/ml-platform-eu-west-1/cluster --since 30m \
  | grep -E "etcdserver|raft"

# GKE — view in Cloud Logging
gcloud logging read 'resource.type=k8s_control_plane_component AND severity>=WARNING' \
  --project=$PROJECT --limit=100
```

### Remediation

- During a partial AZ outage, **do not** attempt to scale node groups. The control plane needs etcd to be quorate first.
- Trigger failover at the global level: shift 100% of traffic to other regions. The failover controller's `etcd_unavailable` rule does this automatically when the API server returns >10 consecutive 5xx within 60 seconds.
- Once the AZ recovers, perform a `kubectl rollout restart` on critical controllers (Argo CD, External-DNS, cert-manager) since they may have cached stale state.
- Architectural fix: never have more than 33% of a cluster's nodes in a single AZ. Use `topologySpreadConstraints` with `maxSkew=1`.

---

## 10. Prometheus Federation Cardinality Explosion

### Symptoms

- Central Thanos store reports `prometheus_tsdb_head_series` >10M.
- Grafana queries time out.
- Inter-region egress bill spikes (see entry 7).

### Diagnosis

```bash
# Top 20 metrics by series count (run against central Prometheus)
curl -s 'http://prometheus.central:9090/api/v1/query' \
  --data-urlencode 'query=topk(20, count by (__name__)({__name__=~".+"}))' \
  | jq '.data.result'

# Common offenders: kube-state-metrics with pod-level labels, Istio per-request metrics
```

### Remediation

- Apply `metric_relabel_configs` at the federation source. Drop `pod`, `instance`, `container_id` labels for metrics that aggregate cleanly without them.
- Move from federation to **Prometheus remote-write** with `queue_config` (capacity 10000, max_samples_per_send 2000, batch_send_deadline 5s). Federation is a pull model that fails badly during inter-region congestion.
- Use **Thanos Receive** for ingest and **Thanos Compactor** with `--retention.resolution-raw=14d --retention.resolution-5m=90d --retention.resolution-1h=2y` to bound storage.
- Pre-aggregate with recording rules at the source region; federate only the recording-rule output. Example: `instance:request_latency_p99:5m` aggregates 50,000 series down to 50.

---

## 11. Stale Read After Region Recovery (Replication Direction Wrong)

### Symptoms

- After `us-west-2` recovered from a failover, customers who were served by `eu-west-1` during the outage see their data revert to the pre-outage state.
- New model versions trained in `eu-west-1` during the outage are not visible in `us-west-2`.

### Diagnosis

The replicator was configured for **one-way** sync (`us-west-2 → others`). When `us-west-2` failed, writes accumulated in `eu-west-1`. When `us-west-2` came back, its (stale) state was treated as authoritative.

```bash
# Inspect replicator config
kubectl get configmap -n platform replicator-config -o yaml \
  | yq '.data."replication.yaml"'
```

### Remediation

- Use **multi-master** with conflict resolution. For models, prefer the higher monotonic version number; for arbitrary blobs, last-write-wins on object metadata `x-amz-meta-mtime` (synced from NTP-disciplined hosts).
- For databases, use a globally consistent store: **DynamoDB Global Tables**, **Spanner**, or **CockroachDB**. Self-managed multi-master Postgres is achievable (BDR, pglogical) but operationally expensive.
- During recovery, run a **reconciliation job** before re-admitting traffic: compare object inventories between regions, replay newer objects to the recovered region.
- Implement a recovery quarantine: the recovered region runs in `synced=false` mode and refuses traffic until reconciliation completes (the `failover_controller` has a `--require-reconcile` flag).

---

## 12. Argo CD ApplicationSet Drift Across Regions

### Symptoms

- `eu-west-1` runs `inference:v3.2.1`; `us-west-2` runs `inference:v3.2.0`; `ap-south-1` runs `inference:v3.2.1-hotfix`.
- Argo CD UI shows all three Applications as `Synced` and `Healthy`.
- A bug fix that was supposed to be deployed to all regions only made it to two.

### Diagnosis

```bash
# Inspect the ApplicationSet generator state
kubectl get applicationset -n argocd inference-multiregion -o yaml

# Compare desired vs actual revision per region
argocd app list -o json \
  | jq '.[] | {name, sync: .status.sync.revision, image: .status.summary.images}'
```

### Remediation

- Use a single **Git source of truth** with Kustomize overlays per region (`kubernetes/overlays/<region>/`). The base manifest pins the image tag; overlays patch only region-specific config (DNS names, secrets references).
- Avoid `--auto-prune=false` on ApplicationSet members; orphaned resources cause drift over time.
- Add a **PR check** that runs `kustomize build kubernetes/overlays/<region>` for all three regions and diffs against the previous revision. Block merges that change only one overlay's image tag.
- Use Argo CD's **PostSync hook** to write the deployed revision to a central audit log (e.g., a DynamoDB table indexed by `service+region+timestamp`). Alert on `divergent_revisions > 0` after a 30-minute grace window.

---

## Appendix: Common Diagnostic Bundles

When opening an incident ticket, attach:

```bash
./scripts/diagnostic_bundle.sh --region <region> --output /tmp/bundle.tar.gz
```

The bundle collects: `kubectl get events -A --sort-by=.lastTimestamp`, controller logs from `kube-system`, `cert-manager`, `argocd`, `external-dns`, `platform`, current Terraform state hash, last 100 Route 53 change records, and a 24-hour Grafana dashboard PDF.

For SEV-1 incidents, also page the regional on-call and post in `#incidents` with the bundle attached within 10 minutes of declaration.
