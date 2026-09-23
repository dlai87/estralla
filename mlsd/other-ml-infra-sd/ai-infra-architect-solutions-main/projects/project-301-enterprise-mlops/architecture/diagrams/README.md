# Architecture Diagrams

This directory is the canonical index of architecture diagrams for the Enterprise
MLOps Platform. Every diagram here is rendered inline in Mermaid so the source of
truth is version-controlled with the rest of the project and reviewable in pull
requests. Static image exports (`.png`, `.svg`) belong in `./exports/` and must be
regenerated from the inline source — never edited directly.

Diagrams are grouped by the architectural concern they address. Each diagram has:
- A **purpose** statement (what question it answers and for whom)
- A **scope** statement (what's in, what's deliberately out)
- A **last-validated** marker (Git commit + date the diagram was last walked
  against the running system or the latest ADR)

For the textual narrative, see [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md).
For the architectural views (logical/process/deployment/physical), see
[`../views/README.md`](../views/README.md). For the decision rationale behind any
boundary drawn below, see [`../adrs/`](../adrs/).

---

## Diagram 1 — High-Level Platform Architecture (C4 Container View)

**Purpose**: Onboarding diagram for a new platform engineer or architect. Shows the
top-level containers, the platform API boundary, and what's hosted inside vs
outside the Kubernetes cluster.

**Scope**: In — control plane, data plane, identity, model serving, observability,
data lake interaction. Out — individual microservices, per-tenant namespaces (see
Diagram 6), specific node groups (see physical view).

**Last validated**: 2026-04 against ADR-001 and ADR-008.

```mermaid
graph TB
  subgraph Users["User & Client Layer"]
    DS[Data Scientists<br/>JupyterHub + MLflow SDK]
    MLE[ML Engineers<br/>kubectl + Argo CLI]
    BIZ[Business / Consumers<br/>REST + gRPC clients]
    AUD[Auditors<br/>Read-only dashboards]
  end

  subgraph Edge["Edge & Identity"]
    ALB[AWS ALB + WAF<br/>TLS termination]
    OIDC[Okta OIDC<br/>SSO + MFA]
  end

  subgraph Platform["Enterprise MLOps Platform (EKS 1.30)"]
    APIGW[Platform API Gateway<br/>FastAPI + Envoy]
    subgraph Control["Control Plane"]
      MLFLOW[MLflow 2.14<br/>Tracking + Registry]
      KF[Kubeflow Pipelines 1.9]
      FEAST[Feast 0.39<br/>Feature Registry]
      ARGO[Argo CD 2.11 + Workflows]
    end
    subgraph Data["Data Plane"]
      KSERVE[KServe 0.13<br/>Inference Services]
      JHUB[JupyterHub 4.x]
      TRAIN[Training Jobs<br/>Kubeflow + Volcano]
    end
    subgraph Obs["Observability"]
      PROM[Prometheus<br/>Thanos LTS]
      GRAF[Grafana 11]
      LOKI[Loki 3.x]
      TEMPO[Tempo 2.x]
    end
  end

  subgraph Backing["Backing AWS Services"]
    S3[(S3<br/>Artifacts + Datasets)]
    RDS[(RDS Postgres 15<br/>Multi-AZ)]
    REDIS[(ElastiCache Redis 7<br/>Online Feature Store)]
    SM[Secrets Manager<br/>+ KMS CMK]
    ECR[ECR<br/>Image Registry]
  end

  DS --> ALB
  MLE --> ALB
  BIZ --> ALB
  AUD --> ALB
  ALB --> OIDC
  ALB --> APIGW

  APIGW --> Control
  APIGW --> Data
  Control --> Data
  Data --> Backing
  Control --> Backing
  Obs -.scrape.-> Platform
  Obs --> S3
```

---

## Diagram 2 — Training Data Flow (Source → Feature → Training → Registry)

**Purpose**: Show the lifecycle of a feature value from raw source through
training. Used to explain lineage capture and reproducibility guarantees to
auditors and ML teams.

**Scope**: In — batch and streaming ingestion, materialization, training-time
read, model artifact promotion. Out — inference-time reads (see Diagram 4).

**Last validated**: 2026-04 against ADR-002 (Feast) and ADR-006 (streaming).

```mermaid
flowchart LR
  subgraph Sources["Source Systems"]
    KAFKA[Kafka Topics<br/>events.*]
    SNOWFLAKE[(Snowflake<br/>warehouse.*)]
    S3RAW[(S3 raw zone<br/>parquet)]
  end

  subgraph Ingest["Ingestion & Transform"]
    FLINK[Flink 1.18<br/>streaming features]
    DBT[dbt + Spark on EMR<br/>batch features]
  end

  subgraph FeatStore["Feast Feature Store"]
    OFFLINE[(Offline Store<br/>Iceberg on S3)]
    ONLINE[(Online Store<br/>Redis Cluster)]
    REGFS[Feature Registry<br/>Postgres metadata]
  end

  subgraph Train["Training"]
    NB[Jupyter Notebook]
    KFP[Kubeflow Pipeline<br/>train.yaml]
    TJOB[Distributed Training<br/>PyTorch + Volcano<br/>A100/H100 nodes]
  end

  subgraph Reg["Model Registry"]
    MLR[MLflow Registry<br/>Staging → Prod gates]
    ARTS[(S3 model artifacts<br/>+ SHA256)]
  end

  KAFKA --> FLINK --> ONLINE
  SNOWFLAKE --> DBT --> OFFLINE
  S3RAW --> DBT
  OFFLINE -. materialize .-> ONLINE
  FLINK --> OFFLINE
  REGFS -.governs.-> OFFLINE
  REGFS -.governs.-> ONLINE

  NB -->|fs.get_historical_features| OFFLINE
  NB --> KFP --> TJOB
  TJOB --> ARTS
  TJOB --> MLR
  MLR -. lineage edge .-> REGFS
```

---

## Diagram 3 — Training Pipeline (Kubeflow + Argo Workflows Detail)

**Purpose**: Reference diagram for ML engineers building new pipelines. Shows the
canonical step graph, retry boundaries, and which steps are gate-blocked.

**Scope**: In — DAG of a standard supervised-training pipeline. Out — RL or LLM
fine-tuning variants (covered in separate diagrams).

**Last validated**: 2026-03 against `reference-implementations/cicd/model-deployment-pipeline.yaml`.

```mermaid
flowchart TB
  Start([Pipeline Triggered<br/>git push or schedule]) --> Validate
  Validate{Schema +<br/>Lineage Valid?}
  Validate -- no --> Fail([Fail fast,<br/>page on-call])
  Validate -- yes --> Materialize[Materialize Features<br/>Feast batch job]
  Materialize --> Split[Train/Val/Test Split<br/>deterministic seed]
  Split --> Train[Distributed Train<br/>TorchElastic on Volcano<br/>checkpoint to S3]
  Train --> Eval[Offline Evaluation<br/>metrics + slice analysis]
  Eval --> BiasCheck{Bias +<br/>fairness gates}
  BiasCheck -- fail --> Quarantine[Quarantine artifact<br/>notify model owner]
  BiasCheck -- pass --> Register[Register in MLflow<br/>stage=Staging]
  Register --> Shadow[Shadow Deploy<br/>5% mirrored traffic]
  Shadow --> Compare{Champion vs<br/>Challenger}
  Compare -- regression --> Quarantine
  Compare -- improvement --> Approval{High-risk?<br/>see ADR-010}
  Approval -- automated --> Promote[Promote stage=Production]
  Approval -- human --> ReviewQ[Approval queue<br/>Slack + dashboard]
  ReviewQ --> Promote
  Promote --> Rollout[Argo Rollouts canary<br/>5→25→50→100%]
  Rollout --> Done([Done])
```

---

## Diagram 4 — Inference Path (Request → Prediction → Observation)

**Purpose**: Explain the per-request latency budget and the components on the hot
path. Drives SLO conversations and capacity planning.

**Scope**: In — synchronous online inference. Out — async batch scoring (separate
diagram in `./batch-inference.mmd`).

**Last validated**: 2026-04 against KServe deployment manifests.

```mermaid
sequenceDiagram
  autonumber
  participant C as Client App
  participant ALB as ALB + WAF
  participant Envoy as Istio Ingress<br/>(mTLS)
  participant Gate as Platform API<br/>(authn + quota)
  participant KSv as KServe Predictor<br/>(transformer + model)
  participant Feast as Feast Online<br/>(Redis)
  participant Prom as Prometheus<br/>+ ML Monitor

  C->>ALB: POST /v1/models/fraud-detector:predict<br/>JWT, ≤2KB
  ALB->>Envoy: TLS terminated, mTLS upstream
  Envoy->>Gate: Forward + trace headers
  Gate->>Gate: Validate JWT, check tenant quota, rate limit
  Gate->>KSv: Internal call (gRPC)
  KSv->>Feast: get_online_features(entity_keys)
  Feast-->>KSv: feature vector (<5ms p99)
  KSv->>KSv: transformer (preprocess) → model.predict
  KSv-->>Gate: prediction + model_version
  Gate-->>C: 200 OK, X-Model-Version, X-Request-ID
  KSv-->>Prom: emit prediction (async),<br/>features hash, latency
  Prom->>Prom: drift detector + perf metrics
  Note over Prom: Alert if PSI > 0.2 over 1h window
```

**Latency budget (p99, end-to-end 80ms)**: ALB 5ms, Envoy 3ms, Gate 7ms,
feature fetch 5ms, model inference 50ms, overhead 10ms.

---

## Diagram 5 — Security Boundaries & Trust Zones

**Purpose**: Compliance and threat-modeling reference. Shows trust zones, where
authn/authz happens, and which links are mTLS vs TLS vs plaintext-on-loopback.

**Scope**: In — perimeter, identity, secrets, mTLS mesh, audit trail. Out —
detailed STRIDE per service (in `governance/audit-procedures.md`).

**Last validated**: 2026-04 against ADR-007.

```mermaid
flowchart TB
  subgraph Internet["UNTRUSTED — Internet"]
    user[End User / Client]
  end

  subgraph Perim["TRUST BOUNDARY 1 — Perimeter (AWS edge)"]
    WAF[AWS WAF<br/>OWASP CRS]
    ALB[ALB<br/>TLS 1.3 only]
    OIDC[Okta OIDC<br/>SSO + WebAuthn]
  end

  subgraph Cluster["TRUST BOUNDARY 2 — Cluster (EKS, mTLS via Istio)"]
    subgraph CtrlNS["ns: platform-control"]
      API[Platform API]
      MLF[MLflow]
    end
    subgraph TenantNS["ns: tenant-<team> (per-tenant)"]
      TWL[Training + Inference Workloads]
    end
    NP[NetworkPolicies<br/>default-deny + allowlist]
  end

  subgraph DataLayer["TRUST BOUNDARY 3 — Data (encrypted at rest)"]
    S3E[(S3 + SSE-KMS<br/>bucket policy:<br/>VPC endpoint only)]
    RDSE[(RDS + KMS<br/>private subnet)]
    SMV[Secrets Manager<br/>VPC endpoint]
    KMS[(KMS CMK<br/>per-tenant key)]
  end

  Audit[(CloudTrail + OpenSearch<br/>WORM, 7-year retention)]

  user --TLS 1.3--> WAF --> ALB
  ALB --signed JWT--> OIDC
  ALB --mTLS--> API
  API --mTLS--> MLF
  API --mTLS + RBAC--> TWL
  TWL --IRSA + IAM--> S3E
  MLF --IRSA + IAM--> S3E
  MLF --TLS + IAM auth--> RDSE
  TWL --IRSA--> SMV --> KMS
  S3E -. encrypted .- KMS
  RDSE -. encrypted .- KMS
  NP -.enforces.- CtrlNS
  NP -.enforces.- TenantNS
  Cluster -.audit events.-> Audit
  DataLayer -.audit events.-> Audit
  Perim -.audit events.-> Audit
```

**Trust transitions and what's enforced at each boundary**:

| Boundary | Authn | Authz | Encryption | Audit Sink |
|---|---|---|---|---|
| 1 → 2 | Okta OIDC (JWT) | Group → RBAC role mapping | TLS 1.3 | CloudTrail + ALB logs |
| 2 → 2 (intra-cluster) | SPIFFE / Istio mTLS | NetworkPolicy + AuthorizationPolicy | mTLS | Istio access logs → Loki |
| 2 → 3 | IRSA (no static keys) | IAM resource policy + SCP | TLS + KMS at rest | CloudTrail + S3 access logs |

---

## Diagram 6 — Multi-Tenancy Namespace Map (informative)

See [`../views/README.md`](../views/README.md) §Logical View for the canonical
tenant namespace map and quota model. It's reproduced there because the view
narrative explains why namespaces are the unit of tenancy (ADR-003).

---

## Conventions

- **Mermaid only**. Do not commit `drawio` or PowerPoint sources.
- One concern per diagram. If a diagram needs more than ~40 nodes, split it.
- **No vendor logos** in diagrams — use text labels with versions.
- **Annotate ADRs**: every non-obvious boundary references the ADR that justifies it.
- **Re-validate quarterly**: walk each diagram against the running system; bump
  the `Last validated` line in the same commit as any drift fix.
