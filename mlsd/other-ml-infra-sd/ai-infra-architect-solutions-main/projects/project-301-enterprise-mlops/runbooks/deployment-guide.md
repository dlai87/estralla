# Enterprise MLOps Platform — Production Deployment Guide

**Audience**: Platform SRE, Release Engineers, On-Call MLE
**Scope**: All platform services (MLflow, Feast, KServe, training operator, registry, gateway, monitoring)
**Cadence**: Up to 3 promotions per service per week to `prod`, change-windowed
**Owner**: Platform SRE (`#mlops-sre` on Slack, PagerDuty service `mlops-platform`)

---

## 0. How to read this guide

Every production change to the MLOps platform — whether a Helm chart bump, a new service version, a CRD migration, or a feature flag flip — passes through the same nine stages:

1. Pre-flight gates (CI green, ADR check, security clearance)
2. Change record opened in ServiceNow
3. Change window confirmed
4. Staging soak completed
5. Promotion to `prod-canary` via Argo CD sync wave
6. Progressive rollout via Argo Rollouts or Flagger
7. Validation gates (SLO burn check, smoke suite, synthetic probes)
8. Promotion to `prod-stable` or rollback
9. Post-deploy review and ticket close

You do not skip stages. You may **wait** at a stage; you may **roll back** from a stage; you do not **leap over** a stage. If a service does not yet support a stage (for example, no canary surface for a control-plane operator), that exception lives in the service's `service.yaml` under `deployment.exemptions:` with an explicit reason and an expiry date.

---

## 1. Pre-flight checks

Run all of these **before** opening a CR. If any fail, fix root cause; do not bypass.

### 1.1 CI must be green on the release commit

```bash
gh run list --commit "${RELEASE_SHA}" --json conclusion,name | jq '.[] | select(.conclusion != "success")'
```

Expected: empty list. Any non-success aborts the deploy.

### 1.2 Image must be signed and SBOM published

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/acme/mlops-.*/.github/workflows/release.yml' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/acme/mlops-${SERVICE}:${VERSION}

cosign verify-attestation --type cyclonedx \
  --certificate-identity-regexp 'https://github.com/acme/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/acme/mlops-${SERVICE}:${VERSION} | jq '.payload | @base64d | fromjson.predicate.components | length'
```

The SBOM component count must be > 0. If the image was retagged or rebuilt, the signature breaks — rebuild from source.

### 1.3 Vulnerability gates

```bash
trivy image --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed \
  ghcr.io/acme/mlops-${SERVICE}:${VERSION}
```

Policy: zero `CRITICAL`. Up to 3 `HIGH` allowed only with a tracked Jira ticket and a fix-by date within 14 days. The CR comment must link the tickets.

### 1.4 Chart lint and policy

```bash
helm lint charts/${SERVICE}
helm template charts/${SERVICE} -f envs/prod/values.yaml \
  | kyverno apply policies/ --resource -
```

Kyverno must report `pass` for every policy. Required policies:

- `require-runAsNonRoot`
- `disallow-host-namespaces`
- `require-resource-limits`
- `require-image-digest` (no floating tags in prod)
- `require-tenant-label` (`acme.io/tenant` on every workload)
- `require-cost-center-annotation`

### 1.5 Schema and CRD compatibility

If the chart bumps a CRD version:

```bash
./scripts/check-crd-compat.sh charts/${SERVICE}/crds/ ${PREVIOUS_VERSION} ${VERSION}
```

The script enforces:

- No removed fields without 2-version deprecation
- No required-field additions on existing CRD versions
- Conversion webhook present if multiple stored versions exist

A failure here is a hard stop. CRD breakage in a multi-tenant control plane creates incidents that span hours.

### 1.6 Database migration plan present

For services with a database (MLflow, registry, feature store registry, audit log):

- The PR must include a `migrations/` entry
- The migration must be **expand–contract** (additive forward, no destructive change in the same release)
- The migration must be marked `ONLINE` or `OFFLINE` in the header; `OFFLINE` requires a maintenance window

### 1.7 Capacity headroom

```bash
kubectl get nodes -l workload-class=platform -o json \
  | jq '.items | map({name: .metadata.name, alloc_cpu: .status.allocatable.cpu, alloc_mem: .status.allocatable.memory})'
```

If the rollout doubles replica count temporarily (Argo Rollouts `maxSurge: 100%`), confirm headroom or queue a node pool scale-up.

### 1.8 Pre-flight checklist (paste into CR)

```
[ ] CI green on release SHA
[ ] Image signed (cosign)
[ ] SBOM attested
[ ] Trivy: 0 CRITICAL, HIGH within policy
[ ] Helm + Kyverno: pass
[ ] CRD compatibility verified (or N/A)
[ ] DB migration expand-contract (or N/A)
[ ] Capacity headroom confirmed
[ ] Staging soak ≥ 24h with green SLOs
[ ] Rollback path tested in staging within 14d
```

---

## 2. Change record (ServiceNow `CHG`)

Every prod change has a CR. The CR template lives at `https://acme.service-now.com/chg_request.do?sys_id=mlops_template`. Required fields:

| Field | Value |
|---|---|
| Service | `mlops-${SERVICE}` |
| Risk | `low` / `medium` / `high` (see §3) |
| Type | `standard` / `normal` / `emergency` |
| Window | See §3 |
| Backout plan | Link to §7 of this guide + service-specific notes |
| Validation plan | Link to §6 of this guide + smoke suite name |
| Affected tenants | All / list / blast-radius percentage |
| Comms | Slack channel(s) for status updates |

The CR is opened **at least 24h ahead** for normal changes and **2h ahead** for low-risk standard changes. Emergency changes follow §9.

---

## 3. Change windows and risk classes

### 3.1 Risk classes

| Class | Examples | Approval | Window |
|---|---|---|---|
| **Low** | Helm value tweak, HPA bump, log level, dashboard | Service tech lead | Any business hour, Mon–Thu |
| **Medium** | Container image bump within same minor, config rotation | Tech lead + 1 SRE | Tue/Wed/Thu 10:00–16:00 local |
| **High** | Minor/major version bump, CRD change, schema migration, network policy change | CAB (weekly Tue 09:00 UTC) | Wed 14:00–18:00 UTC |
| **Emergency** | Rollback of a bad deploy, security CVE, customer outage | On-call SRE + EM | Immediate |

### 3.2 Freeze windows

The platform observes the following freezes (no medium/high changes):

- Friday 16:00 local → Monday 06:00 local
- 7 days before and 2 days after each quarter-end financial close
- Any active SEV-1 or SEV-2 incident on a dependency (EKS control plane, Vault, RDS, GitHub, GHCR)

Low-risk standard changes are still allowed during the weekly freeze with EM approval. They are never allowed during an active incident.

---

## 4. Staging soak

Before promotion to prod, the same chart + image must run in `staging` for **at least 24 hours** with:

- Synthetic load at 30% of prod RPS
- All SLOs green (no burn alerts)
- No `CrashLoopBackOff`, no `OOMKilled`
- No new error budgets consumed beyond steady-state baseline

Check:

```bash
argocd app get mlops-${SERVICE}-staging --refresh
argocd app history mlops-${SERVICE}-staging | head -5

# SLO burn over the soak window
curl -sG https://grafana.acme.io/api/datasources/proxy/1/api/v1/query \
  --data-urlencode 'query=slo:error_budget_burn_rate_1h{service="'${SERVICE}'",env="staging"}' \
  | jq '.data.result'
```

If burn > 1× in the last hour, do not promote. Investigate; consider a longer soak or a config tweak in staging.

---

## 5. Rollout strategy per service class

We use two progressive delivery controllers because they serve different needs:

- **Argo Rollouts** for north–south request services (model gateways, platform API, MLflow UI, registry UI, KServe inference services). Native canary + analysis templates against Prometheus + Datadog.
- **Flagger** for service-mesh-native east–west services that already sit behind Istio (feature store online layer, internal model serving). Flagger drives the Istio `VirtualService` weights.

For batch/control-plane components without a request surface (training operator, pipeline runner, GC controller, governance reconciler) we use **Argo CD sync waves with blue/green Deployments** and validate by reconciling a canary CR (e.g., a synthetic `TrainingJob`) before flipping the Service selector.

### 5.1 Sync waves

`Application` manifests declare sync waves so that the order is deterministic:

| Wave | Resources |
|---|---|
| -2 | Namespaces, ResourceQuotas, NetworkPolicies, PriorityClasses |
| -1 | CRDs, ConfigMaps, Secrets (via External Secrets Operator) |
| 0 | RBAC (ServiceAccount, Role, RoleBinding) |
| 1 | Services, ServiceMonitors, PodMonitors |
| 2 | Deployments, StatefulSets, Rollouts |
| 3 | HPA, PodDisruptionBudget |
| 4 | Ingress, Gateway, VirtualService |
| 5 | Post-sync Jobs (smoke tests, schema migrations marked ONLINE) |

CRD changes always land one sync ahead of the workloads that consume them. Argo CD honors the wave order with `argocd.argoproj.io/sync-wave` annotations on each manifest.

### 5.2 Helm + helm-secrets

Charts are rendered by Argo CD from `infra-gitops` using the Helm plugin. Sensitive values use `helm-secrets` with SOPS + AWS KMS (one KMS key per environment, separate IAM roles):

```yaml
plugin:
  name: helm-secrets
  env:
    - name: HELM_SECRETS_DRIVER
      value: sops
    - name: HELM_SECRETS_HELM_PATH
      value: /usr/local/bin/helm
```

Never commit a decrypted `secrets.yaml`. CI fails on `*.dec.yaml` in the diff.

### 5.3 Canary recipe — request services

Default Argo Rollouts strategy for inference and gateway services:

```yaml
strategy:
  canary:
    canaryService: ${SERVICE}-canary
    stableService: ${SERVICE}-stable
    trafficRouting:
      istio:
        virtualService:
          name: ${SERVICE}
          routes: [primary]
    steps:
      - setWeight: 5
      - pause: { duration: 10m }
      - analysis:
          templates:
            - templateName: success-rate-and-latency
            - templateName: error-budget-burn
      - setWeight: 25
      - pause: { duration: 15m }
      - analysis: { templates: [{ templateName: success-rate-and-latency }] }
      - setWeight: 50
      - pause: { duration: 20m }
      - setWeight: 100
```

`AnalysisTemplate` `success-rate-and-latency` checks:

- `sum(rate(http_requests_total{service="${SERVICE}",code!~"5.."}[5m])) / sum(rate(http_requests_total{service="${SERVICE}"}[5m]))` ≥ 0.995
- `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="${SERVICE}",surface="canary"}[5m]))` ≤ 1.5 × stable baseline

`error-budget-burn` aborts on a 14.4× 1h burn (fast burn) per Google SRE workbook.

### 5.4 Canary recipe — mesh-native services (Flagger)

```yaml
analysis:
  interval: 1m
  threshold: 5
  maxWeight: 50
  stepWeight: 10
  metrics:
    - name: request-success-rate
      thresholdRange: { min: 99.5 }
      interval: 1m
    - name: request-duration
      thresholdRange: { max: 800 }
      interval: 1m
  webhooks:
    - name: smoke
      url: http://flagger-loadtester.test/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 50 -c 5 http://${SERVICE}-canary.${NS}:80/healthz"
```

### 5.5 Blue/green recipe — control-plane

```yaml
strategy:
  blueGreen:
    activeService: ${SERVICE}
    previewService: ${SERVICE}-preview
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 600
    prePromotionAnalysis:
      templates: [{ templateName: control-plane-reconcile }]
```

`control-plane-reconcile` posts a synthetic CR (e.g., a `TrainingJob` with a no-op image) against the preview controller endpoint and waits for `status.phase=Succeeded` within 5 minutes.

### 5.6 KServe inference services

For tenant-owned `InferenceService` resources, the platform controls the runtime image only. Promotion uses KServe's built-in canary:

```yaml
spec:
  predictor:
    canaryTrafficPercent: 10
    model:
      modelFormat: { name: pytorch }
      storageUri: s3://acme-models/${TENANT}/${MODEL}/v${VERSION}/
```

Platform-side validation runs against `${MODEL}-predictor-canary` and uses the tenant's golden dataset published under `s3://acme-models/${TENANT}/${MODEL}/golden/`. Promotion to 100% requires:

- p95 latency within 10% of the stable revision
- Cosine similarity of output embeddings ≥ 0.98 across the golden set
- No drift alerts (PSI < 0.2 on top-5 features) in the first 30 minutes

---

## 6. Validation gates

A rollout is **not** successful when the chart syncs. It is successful when validation passes. Each stage of the canary has a gate.

### 6.1 Automated smoke

Every service ships a `smoke/` directory with a Pytest suite tagged `@pytest.mark.smoke`. The post-sync job runs:

```bash
pytest smoke/ -m smoke --base-url=https://${SERVICE}.prod.acme.io --canary --maxfail=1 --timeout=60
```

A canary smoke covers: health, auth (valid + invalid token), tenant isolation (request as tenant A must not see tenant B data), one happy-path API call, one expected-failure call.

### 6.2 Synthetic probes

Datadog synthetics run every 60s against the canary FQDN. The CR is auto-aborted if 3 consecutive failures occur within 5 minutes.

### 6.3 SLO burn

A 14.4× 1h burn or 6× 6h burn on any tier-1 SLO triggers `AbortRollout`. Tier-1 SLOs for the platform:

| SLO | Target | Window |
|---|---|---|
| Platform API availability | 99.9% | 30d rolling |
| Inference p99 latency (per model) | < 1.5 × stable | 7d rolling |
| Model registration success | 99.5% | 30d rolling |
| Training submission success | 99% | 30d rolling |
| Feature serving freshness | < 60s | 30d rolling |

### 6.4 Human gate (high-risk only)

Before promoting beyond 50% on a high-risk change, the on-call SRE manually approves in Argo Rollouts UI. They check:

- Datadog APM error rate
- Loki error logs grouped by `service`, `tenant`, `route`
- Any open incidents on dependencies

---

## 7. Rollback

### 7.1 When to roll back

Roll back, do not "fix forward" in prod, when any of these hold:

- Tier-1 SLO burning > 14.4× on the canary
- Any tenant-impacting 5xx rate above baseline + 0.5%
- Data loss, corruption, or cross-tenant data leak (even one event)
- Auth or authz regression on any path
- Latency p99 > 2× stable for > 5 minutes
- A CRD migration partially applied and reconcile loop stuck

### 7.2 How to roll back

**Argo Rollouts**:

```bash
kubectl -n ${NS} argo rollouts abort ${ROLLOUT}
kubectl -n ${NS} argo rollouts undo  ${ROLLOUT}
kubectl -n ${NS} argo rollouts status ${ROLLOUT} --watch
```

`undo` flips traffic back to the previous stable replica set immediately and scales the new replica set to zero after `scaleDownDelaySeconds`.

**Flagger**:

```bash
kubectl -n ${NS} patch canary ${SERVICE} --type merge \
  -p '{"spec":{"skipAnalysis":false},"status":{"phase":"Failed"}}'
```

Flagger reverts mesh weight to 100% primary within one analysis interval.

**Argo CD blue/green**:

```bash
argocd app set mlops-${SERVICE} --revision ${PREVIOUS_SHA}
argocd app sync mlops-${SERVICE} --prune
```

The `previous` ReplicaSet remains scaled for 600s by `scaleDownDelaySeconds` to enable instant rollback without a cold-start hit.

**Database migrations**: because all migrations are expand–contract, a rollback of the application does not require a backward schema change. The new columns simply become unused until the next forward release. Never run a `DROP COLUMN` in the same release that added it.

### 7.3 Verifying rollback worked

```bash
kubectl -n ${NS} get rollout ${ROLLOUT} -o jsonpath='{.status.stableRS}{"\n"}'
kubectl -n ${NS} get pods -l rollouts-pod-template-hash=<STABLE_HASH>
```

Then re-run the smoke suite against the stable FQDN and confirm SLO burn is decreasing.

---

## 8. Observability during deploys

A deploy without dashboards is a guess. Open these before clicking "Sync":

1. `Grafana / MLOps / Deploy Cockpit / ${SERVICE}` — overlays canary vs stable for RPS, error rate, p50/p95/p99, CPU, memory, GC pauses
2. `Grafana / MLOps / SLO Burn` — current burn rate per SLO with rollout markers
3. `Grafana / MLOps / Tenant Heatmap` — per-tenant error rate, used to spot single-tenant regressions
4. Datadog APM `service:${SERVICE}` filtered by `env:prod` and `version:${VERSION}`
5. Loki query: `{namespace="${NS}", app="${SERVICE}"} | json | level="error" | rate(5m)`

The deploy bot posts a thread in `#mlops-deploys` with:

- CR link
- Argo CD app URL
- Argo Rollouts UI URL
- Three dashboard deep links
- Timestamped events (start, 5%, 25%, 50%, 100%, complete)

Event markers are written to Grafana via the Datadog event API so they show up as vertical lines on every dashboard.

---

## 9. Emergency change procedure

An emergency change skips the CAB but **not** the validation gates. To run one:

1. Page the platform SRE primary and EM. They must both ack within 10 minutes.
2. Open a SEV-2 incident in the incident channel.
3. Open the CR with `Type=emergency`, `Risk=high`. Backout plan is mandatory.
4. Run §1 pre-flight checks (no exceptions for §1.1–§1.4). §1.5–§1.7 may be deferred only with EM written approval recorded in the incident channel.
5. Skip §3 windows and §4 staging soak only if the emergency is itself a regression in `prod` that staging cannot reproduce.
6. Execute §5 with `maxSurge: 100%` and `pause: 2m` (faster steps, same gates).
7. §6 validation gates are not skippable.
8. After mitigation, file a postmortem within 5 business days. Postmortems for skipped gates require an action item to add the gate to the next release.

---

## 10. Post-deploy

Within 30 minutes of a successful promotion:

- Close the CR with timeline (start, 5%, 25%, 50%, 100%, complete) and screenshots of dashboards
- Tag the release in Git: `git tag -s ${SERVICE}/v${VERSION} -m "prod ${TIMESTAMP}"`
- Update the service's `RELEASES.md` with the version, SHA, CR link, and notable changes
- If the deploy consumed any error budget, log it in the weekly SRE review

Within 1 business day:

- Confirm cost dashboard shows the new version's per-tenant cost is within ±10% of the previous version. A regression beyond ±10% opens a Jira `mlops-cost` ticket against the service team.
- Confirm audit log entries for the deploy reached the immutable store (`s3://acme-mlops-audit/${YYYY}/${MM}/${DD}/`).

Within 7 days:

- Hold a deploy retro if the change was high-risk. Outputs feed the next release.

---

## 11. Service-specific notes

### 11.1 MLflow tracking server

- Stateful: PostgreSQL backend (RDS Multi-AZ) + S3 artifact store. Migrations run by `mlflow db upgrade` in a pre-sync Job.
- Default rollout: blue/green with `autoPromotionEnabled: false` because UI session draining is needed.
- Always confirm artifact-store path versioning is enabled in S3.

### 11.2 Feast feature store

- Online store: Redis cluster (ElastiCache). Use Flagger canary for the serving layer.
- Offline store: Snowflake. Schema changes go through a separate Snowflake release pipeline; the Feast registry only references them.
- Validate freshness < 60s on the canary using a synthetic feature view named `_canary_freshness`.

### 11.3 KServe + model gateways

- The platform owns the runtime; tenants own the `InferenceService`. Coordinate runtime image bumps with a 14-day tenant notice.
- Canary uses KServe native split + platform-side golden-set validator (see §5.6).

### 11.4 Training operator (Kubeflow training)

- Control-plane component, no request surface. Use blue/green + synthetic `TrainingJob` validator (§5.5).
- Coordinated with node-pool autoscaler — never deploy during an active multi-node distributed job (`kubectl get pytorchjobs -A | grep Running`).

### 11.5 Platform API gateway

- North-south. Use Argo Rollouts canary §5.3.
- Validate authz with a per-role token matrix in smoke. A 200 for a token that should get 403 is an instant abort.

### 11.6 Governance / audit reconciler

- High blast radius if it gets stuck: missed audit events become compliance findings.
- Always run with `--dry-run=server` in staging soak for 24h after CRD changes.
- Alert `AuditEventBacklog > 5000` is a hard rollback trigger.

---

## 12. Appendix — commands cheat sheet

```bash
# Watch a rollout
kubectl -n ${NS} argo rollouts get rollout ${ROLLOUT} --watch

# Promote a step manually
kubectl -n ${NS} argo rollouts promote ${ROLLOUT}

# Abort + undo
kubectl -n ${NS} argo rollouts abort ${ROLLOUT} && \
kubectl -n ${NS} argo rollouts undo  ${ROLLOUT}

# Force a single Argo CD sync wave
argocd app sync mlops-${SERVICE} --resource apps:Deployment:${DEPLOY}

# Diff a chart before sync
argocd app diff mlops-${SERVICE}

# Inspect SOPS-encrypted values
helm secrets dec envs/prod/secrets.yaml
# (decrypted file is gitignored; remove after use)

# Pull current release notes
gh release view ${SERVICE}/v${VERSION} --repo acme/mlops-${SERVICE}
```

See also:

- `runbooks/operations-manual.md` — day-2 operations
- `runbooks/troubleshooting.md` — failure scenarios and remediation
- `reference-implementation/monitoring/README.md` — observability stack details
- `reference-implementation/platform-api/README.md` — API contract and SDK
