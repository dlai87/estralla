# Monitoring Stack — Reference Implementation

**Scope**: The observability platform that backs the Enterprise MLOps Platform — metrics, logs, traces, and SLO tooling. Multi-tenant, regulated-friendly, retention-aware.

**Owner**: Platform SRE (`#mlops-observability`)
**Status**: In production since 2025 Q2; this README describes the v2 stack (Thanos receive + Loki 3 + Tempo 2.4 + OTel 0.103+).

---

## 1. Why this stack

We had three forced moves:

1. **Long retention for compliance**: 13 months of metric history at 1-minute resolution for SOC 2 and HIPAA evidence. Vanilla Prometheus can't hold that.
2. **Per-tenant isolation**: each tenant must see only its own metrics/logs/traces, even when sharing the underlying storage. Required for the per-tenant SLA dashboards we sell.
3. **Bounded cost at growth**: 20× series growth projected over 24 months. Single-instance Prometheus scales the wrong way (vertically); we needed horizontal ingest and tiered storage.

The chosen stack:

| Concern | Tool | Why |
|---|---|---|
| Metrics ingest | Prometheus 2.54 (agent mode) + Thanos Receive 0.36 | Push model fits multi-region fan-in; agent mode minimizes per-shard footprint |
| Metrics long retention | Thanos Store + S3 + downsampling | 1m raw (90d) → 5m (365d) → 1h (3y); object store is the cheapest possible long-tail |
| Logs | Loki 3.0 (microservices mode) | Cost per GB ≈ 1/10 of an ELK equivalent at our scale; label-driven instead of full-text-indexed |
| Traces | Tempo 2.4 + S3 backend | TraceQL is good enough; ingest cost trivial when only sampled traces persist |
| Collectors | OpenTelemetry Collector 0.103 | One agent, one config language for metrics/logs/traces; vendor-neutral |
| Dashboards | Grafana 11 LTS | Native datasource for all four backends; per-tenant orgs |
| SLO authoring | Sloth + OpenSLO | Declarative SLO → Prometheus recording rules + multi-window burn alerts |
| Synthetic | Datadog Synthetic | Independent control plane (so we can alert when Grafana/Prometheus are down) |

We deliberately did not use a single vendor SaaS for everything: the SLO program needs to keep working even when the primary metric backend is itself the incident.

---

## 2. Topology

```
                 ┌───────────────────────────────────────────────────────────────┐
                 │                       Per Cluster                              │
                 │  ┌──────────┐   ┌──────────┐   ┌──────────────────────────┐   │
                 │  │ Workloads│──▶│ OTel DS  │──▶│ OTel Gateway (per AZ)    │   │
                 │  └──────────┘   └──────────┘   └────────────┬─────────────┘   │
                 │                                                │                │
                 │                                                ▼                │
                 │                                ┌───────────────┴──────────────┐ │
                 │                                │ Prom agent (scrapes node-    │ │
                 │                                │ local + remote write to RX)  │ │
                 │                                └───────────────┬──────────────┘ │
                 └────────────────────────────────────────────────┼────────────────┘
                                                                  │ remote write
                                                                  ▼
                          ┌────────────────────────────────────────────────────┐
                          │              Region Aggregation Tier               │
                          │   Thanos Receive (hashring, 6 replicas)            │
                          │   Loki distributor → ingester (12 replicas)        │
                          │   Tempo distributor → ingester (6 replicas)        │
                          └─────────────┬──────────────────────┬───────────────┘
                                        │                      │
                                        ▼                      ▼
                          ┌─────────────────────────┐  ┌─────────────────────┐
                          │ S3 (Thanos blocks)      │  │ S3 (Loki + Tempo)   │
                          │ S3 Object Lock 90d hot  │  │ Lifecycle to        │
                          │ → Glacier after 365d    │  │ Glacier at 30d      │
                          └─────────────────────────┘  └─────────────────────┘
                                        │                      │
                                        ▼                      ▼
                          ┌─────────────────────────────────────────────────┐
                          │      Read Tier (per region, replicated)         │
                          │  Thanos Query + Query Frontend                  │
                          │  Loki Query Frontend + Querier                  │
                          │  Tempo Query Frontend + Querier                 │
                          └─────────────────────────────────────────────────┘
                                                │
                                                ▼
                          ┌─────────────────────────────────────────────────┐
                          │ Grafana 11 (per-tenant orgs) + Alertmanager     │
                          └─────────────────────────────────────────────────┘
```

Cross-region read federation is via Thanos Query → Thanos Query (peer), so a Grafana user in EMEA can join AMER metrics into the same panel.

---

## 3. OpenTelemetry collector

We deploy two OTel collector modes per cluster:

### 3.1 DaemonSet — agent

- Receives OTLP/HTTP and OTLP/gRPC from workloads on `localhost:4317/4318`
- Receives `kubeletstats`, `hostmetrics` (CPU, memory, disk, network)
- Tail-sampling logic deferred to gateway (DS sends 100% to gateway)
- Hard memory limit 512 MiB; spillover dropped with metric `otelcol_processor_dropped_spans`

### 3.2 Deployment — gateway

- Receives from DS agents over OTLP/gRPC
- Tail-sampling: keep 100% of error traces (`status.code=ERROR`), 100% of slow traces (`duration > p95 + 2σ`), 5% baseline
- Routes to backends:
  - **metrics** → Prometheus remote-write to Thanos Receive
  - **logs** → Loki via `loki` exporter
  - **traces** → Tempo via `otlp` exporter
- Per-tenant attributes enforced via the `attributesprocessor`:
  - Inject `acme.tenant` from `k8s.namespace.name` if it starts with `tenant-`
  - Reject spans/logs without a valid tenant tag (metric `otelcol_processor_rejected`)

Gateway sized 6 replicas per region; HPA on CPU (target 60%).

### 3.3 Sample config (gateway)

```yaml
receivers:
  otlp: { protocols: { grpc: { endpoint: 0.0.0.0:4317 }, http: { endpoint: 0.0.0.0:4318 } } }

processors:
  batch: { send_batch_size: 8192, timeout: 5s }
  k8sattributes:
    auth_type: serviceAccount
    extract:
      metadata: [k8s.namespace.name, k8s.pod.name, k8s.node.name, k8s.deployment.name]
      labels: [{tag_name: tenant, key: acme.io/tenant, from: pod}]
  attributes:
    actions:
      - key: acme.tenant
        action: insert
        from_attribute: k8s.namespace.name
      - key: acme.tenant
        action: extract
        pattern: ^tenant-(?P<tenant>.+)$
  tail_sampling:
    decision_wait: 10s
    policies:
      - { name: errors, type: status_code, status_code: { status_codes: [ERROR] }}
      - { name: slow, type: latency, latency: { threshold_ms: 1500 }}
      - { name: baseline, type: probabilistic, probabilistic: { sampling_percentage: 5 }}

exporters:
  prometheusremotewrite:
    endpoint: http://thanos-receive.observability:19291/api/v1/receive
    external_labels: { cluster: $CLUSTER, region: $REGION }
  loki:
    endpoint: http://loki-distributor.observability:3100/loki/api/v1/push
    tenant_id: "{{ attributes.acme.tenant }}"
  otlp/tempo:
    endpoint: tempo-distributor.observability:4317
    headers: { x-scope-orgid: "{{ attributes.acme.tenant }}" }

service:
  pipelines:
    metrics: { receivers: [otlp], processors: [k8sattributes, batch], exporters: [prometheusremotewrite] }
    logs:    { receivers: [otlp], processors: [k8sattributes, attributes, batch], exporters: [loki] }
    traces:  { receivers: [otlp], processors: [k8sattributes, attributes, tail_sampling, batch], exporters: [otlp/tempo] }
```

---

## 4. Prometheus + Thanos

### 4.1 Prometheus agent mode

Per-cluster Prometheus runs in **agent mode** only (`--enable-feature=agent`). No local TSDB. Scrapes:

- `kube-state-metrics` (cluster object state)
- `node-exporter` (per node)
- `nvidia-dcgm-exporter` (per GPU node)
- Service `Endpoints` discovered by `ServiceMonitor` / `PodMonitor`
- Karpenter, Argo CD, cert-manager, ESO, Velero metrics endpoints

Scrape interval defaults 30s; tier-1 services override to 15s.

### 4.2 Thanos Receive

- 6 replicas per region in a consistent-hashring (`replication_factor=3`)
- Block creation every 2h, uploaded to S3
- Storage: NVMe local + cross-AZ S3 for blocks
- Multi-tenancy: receiver writes a `tenant_id` label from `THANOS_TENANT_HEADER` per-request

### 4.3 Compactor and downsampling

Single `thanos-compact` per bucket, performing:

- Compaction every 30 minutes
- Downsampling to 5m at 40h offset, 1h at 10d offset
- Retention: raw 90d, 5m 365d, 1h 3y

### 4.4 Query and federation

- `thanos-query` per region with `--query.replica-label=replica` to dedupe
- Cross-region: each region's query peers with the other regions over mTLS

### 4.5 Cardinality budget

Per-cluster series budget: 5M. Alert at 80% (`prometheus_tsdb_head_series`). The series-explosion runbook lives in §11 of `runbooks/troubleshooting.md`.

Allow-listed labels (managed in `prometheus-config-reloader` configmap):

- Universal: `cluster`, `region`, `namespace`, `pod`, `container`, `service`, `tenant`, `cost_center`, `workload_class`
- HTTP: `method`, `route_template`, `status_code` (status code, not status text)
- KServe: `model`, `revision`, `tenant`

Disallowed (will be silently dropped):

- `request_id`, `trace_id`, `user_id`, `email`, anything unbounded

---

## 5. Loki

### 5.1 Layout

Microservices mode, components:

- `distributor` (3 replicas) — ingest + tenant routing
- `ingester` (12 replicas, StatefulSet, NVMe) — WAL + chunk building
- `compactor` (1) — compaction + retention enforcement
- `querier` (8 replicas, HPA on CPU)
- `query-frontend` (4 replicas) — splits queries, caches results
- `index-gateway` (3 replicas) — TSDB index
- `ruler` (3 replicas) — recording rules + alerts on logs

Backend: TSDB index in S3, chunks in S3, both with lifecycle rules to Glacier at 30d.

### 5.2 Multi-tenancy

Tenant ID = `acme.tenant` resolved by the OTel gateway. Loki `auth_enabled: true`. Grafana datasources are per-tenant org, each with a `X-Scope-OrgID` header set to the tenant slug.

Per-tenant limits (`runtime_config.yaml`):

```yaml
overrides:
  acme:
    ingestion_rate_mb: 50
    max_global_streams_per_user: 100000
    max_query_length: 720h
    retention_period: 90d
  vendor-x:
    ingestion_rate_mb: 5
    max_global_streams_per_user: 20000
    retention_period: 30d
```

### 5.3 Log shapes we enforce

- JSON structured logs only on `stdout`. Plain text is allowed only from third-party sidecars (`istio-proxy`, `vault-agent`) and is parsed by Loki promtail templates.
- Required fields: `ts`, `level`, `service`, `tenant`, `request_id` (if request-scoped), `trace_id` (if available), `msg`.
- Forbidden in log body: secrets, raw model inputs/outputs for PII-class tenants (those go to dedicated audit pipelines, not Loki).

---

## 6. Tempo

### 6.1 Layout

Microservices mode: distributor, ingester, compactor, querier, query-frontend, metrics-generator.

Backend: S3, lifecycle to Glacier at 30d. Retention: 14 days hot, 90 days cold.

### 6.2 Metrics from spans

The `metrics-generator` emits RED metrics (rate, error rate, duration) per service from spans and writes them back into the metrics pipeline. This avoids forcing every service to emit RED metrics themselves and gives uniform service maps in Grafana.

### 6.3 TraceQL examples (tenant queries)

```
{ resource.acme.tenant="acme" && span.http.status_code >= 500 } | rate() by (resource.service.name)
{ resource.acme.tenant="acme" && span.model.name="recsys-v3" && duration > 2s }
```

---

## 7. SLO definitions (per-tenant + platform-wide)

We author SLOs declaratively. Sloth compiles `OpenSLO` YAML into Prometheus recording rules and multi-window burn alerts (1h/6h/24h/72h).

### 7.1 Platform-wide SLOs

| SLO | SLI | Target | Window |
|---|---|---|---|
| Platform API availability | non-5xx / total | 99.9% | 30d |
| Platform API latency (p99 < 500ms) | ratio of fast requests | 99% | 30d |
| Model registration success | successful registrations / submitted | 99.5% | 30d |
| Training submission success | jobs reaching Running within 10m / submitted | 99% | 30d |
| Feature serving freshness | served features with age ≤ 60s / total | 99% | 30d |

### 7.2 Per-tenant SLOs

Each tenant gets a default SLO bundle, automatically created on onboarding:

| SLO | SLI |
|---|---|
| Tenant inference availability | non-5xx / total for tenant's models |
| Tenant inference latency | requests under tenant-configured p99 target / total |
| Tenant training success | training jobs Completed / Submitted |

Tenants can author additional SLOs in their own namespace via `PrometheusRule`-like CRDs (validated by Sloth at admission time).

### 7.3 Burn-rate alerting

Per the Google SRE workbook:

| Burn | Window | Severity | Notification |
|---|---|---|---|
| 14.4× | 1h | critical | page |
| 6×    | 6h | critical | page |
| 3×    | 24h | warning | ticket |
| 1×    | 72h | info | dashboard only |

Example Sloth rule output (abbreviated):

```yaml
- alert: SLOErrorBudgetBurnFast
  expr: |
    (slo:error_budget_burn_rate_1h{service="platform-api"} > 14.4)
    and
    (slo:error_budget_burn_rate_5m{service="platform-api"} > 14.4)
  for: 2m
  labels: { severity: critical, slo: platform-api-availability }
```

---

## 8. Alerting

### 8.1 Alertmanager topology

- Two Alertmanager instances per region in a gossip cluster
- Cross-region federation via `cluster.peer` for global silence visibility
- Routing tree: `severity=critical` → PagerDuty; `severity=warning` → Slack + Jira; `severity=info` → dashboard only

### 8.2 Routing example

```yaml
route:
  group_by: [alertname, cluster, service]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: slack-warnings
  routes:
    - matchers: [severity="critical"]
      receiver: pagerduty-platform
      continue: true
    - matchers: [severity="critical", team="ml"]
      receiver: pagerduty-ml-team
    - matchers: [severity="info"]
      receiver: blackhole

receivers:
  - name: pagerduty-platform
    pagerduty_configs:
      - service_key: ${PD_PLATFORM_KEY}
  - name: slack-warnings
    slack_configs:
      - api_url: ${SLACK_URL}
        channel: "#mlops-alerts"
        title: "{{ .CommonAnnotations.summary }}"
        text: |
          {{ range .Alerts }}*{{ .Labels.alertname }}* ({{ .Labels.severity }})
          {{ .Annotations.description }}
          <{{ .Annotations.runbook_url }}|runbook> · <{{ .Annotations.dashboard_url }}|dashboard>
          {{ end }}
```

### 8.3 Required annotations

Every alert must include:

- `summary` (one line, human readable)
- `description` (with `{{ $labels }}` interpolations)
- `runbook_url` pointing into `runbooks/troubleshooting.md`
- `dashboard_url` deep-linked to the relevant Grafana dashboard with time range pre-set

Alerts without these annotations are rejected by the Prometheus rules validator in CI.

---

## 9. Dashboards

### 9.1 Naming and folders

```
Grafana / MLOps /
  ├── Platform /
  │     ├── Overview (RPS, SLO burn, error budget remaining)
  │     ├── Inference Mesh
  │     ├── Control Plane
  │     ├── Deploy Cockpit (template per service)
  │     └── Capacity (CPU, memory, GPU, by node pool)
  ├── Tenants /
  │     ├── Overview (heatmap, quota saturation)
  │     ├── Per-Tenant Drilldown (template)
  │     └── Cost Heatmap
  ├── Data Plane /
  │     ├── MLflow
  │     ├── Feast (online + offline)
  │     ├── Model Registry
  │     └── Training Operator
  └── Observability /
        ├── Pipeline Health (OTel + Loki + Thanos)
        └── Cardinality Cop
```

### 9.2 Per-tenant dashboards

Auto-provisioned at onboarding. Each tenant's Grafana org sees only:

- Overview: RPS, error rate, p50/p95/p99 across all their models
- Per-model: latency histogram, request volume, error breakdown, GPU utilization
- SLO: budget remaining, burn history, recent alerts
- Cost: spend trend, per-model cost, vs forecast

### 9.3 Dashboard upkeep

Dashboards are JSON in `infra-gitops/grafana/`, applied by the Grafana operator. Every dashboard PR requires:

- A screenshot in the PR description
- A `tags` entry identifying the audience (`platform`, `tenant`, `oncall`)
- A `links` entry pointing to the runbook section relevant when the panel is "red"

---

## 10. Cost and capacity

Approximate per-month spend at current scale (50 clusters, 5K tenants worth of telemetry, ~30M active series):

| Component | Monthly |
|---|---|
| Thanos S3 storage (raw + 5m + 1h) | ~$8K |
| Thanos compute (receive, query, store) | ~$12K |
| Loki storage (S3 + Glacier) | ~$5K |
| Loki compute | ~$10K |
| Tempo storage + compute | ~$4K |
| OTel collector compute | ~$3K |
| Grafana Enterprise license | ~$6K |
| Datadog Synthetic | ~$2K |
| **Total** | **~$50K/month** |

Cardinality and retention are the two cost levers. The Cardinality Cop dashboard surfaces top series-producing tenants/labels weekly; we ticket the top three.

---

## 11. Failure modes (cross-references)

- Cardinality explosion / pipeline back-pressure → `runbooks/troubleshooting.md` §11
- Loki ingester rate-limiting → `runbooks/troubleshooting.md` §11
- Thanos receive hashring rebalance → operator wiki `wiki.acme.io/observability/thanos`

The observability stack itself has SLOs:

- Metric ingest end-to-end latency p99 < 30s
- Log ingest end-to-end latency p99 < 60s
- Query availability 99.9%
- Synthetic probe outage → automatic call to PagerDuty even if Alertmanager is down

---

## 12. References

- `runbooks/deployment-guide.md` — how observability changes get rolled out
- `runbooks/operations-manual.md` §6 (on-call) — who acts on alerts
- `runbooks/troubleshooting.md` §11 — pipeline back-pressure scenario
- `reference-implementation/platform-api/README.md` — API metrics the platform itself emits
- Sloth docs: <https://sloth.dev/>
- OpenSLO: <https://github.com/OpenSLO/OpenSLO>
- Thanos: <https://thanos.io/tip/components/>
