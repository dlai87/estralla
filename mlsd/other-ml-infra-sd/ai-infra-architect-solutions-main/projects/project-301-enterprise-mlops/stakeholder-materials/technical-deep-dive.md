# Enterprise MLOps Platform — Technical Deep Dive

**Audience**: Senior engineers, staff engineers, architects, and SREs joining
the platform team or evaluating the design for their own organization.

**Read time**: ~45 minutes.

**Companion docs**: [ARCHITECTURE.md](../ARCHITECTURE.md) for the long-form
narrative, [ADRs](../architecture/adrs/) for the decision-by-decision audit
trail, [architecture/diagrams/](../architecture/diagrams/README.md) for
diagrams, and the [reference implementation](../reference-implementations/) for
the actual code.

The executive version of this material is in
[executive-presentation.md](./executive-presentation.md). This document trades
the business framing for technical depth and includes trade-offs we made,
alternatives we considered, and lessons we wish we'd known going in.

---

## Section 1 — Problem framing in engineering terms

Most ML platform discussions start with a feature wish list. We started with a
constraints inventory, because the wish list is largely the same everywhere
and the constraints are what make a design defensible.

The constraints, in priority order:

1. **Compliance is a hard gate, not a feature.** SOC 2 Type II is required for
   sales; HIPAA is required for a $40M product line; GDPR is required to
   operate in the EU. Any design that can't pass an audit is disqualified
   regardless of how elegant it is.
2. **Multi-tenancy at ~25 teams, growing to ~60.** Teams have wildly different
   risk profiles (a marketing churn model vs a clinical decision support
   model), but should share the same control plane and a meaningfully shared
   data plane.
3. **GPU economics dominate the cost equation.** A single p5.48xlarge is
   ~$98/hour on-demand. At 35% utilization we burned ~$4M/year in idle GPU
   cycles. Any design that doesn't address this is leaving the largest cost
   lever on the table.
4. **Self-service is non-negotiable.** A 6-week ticket-driven deployment
   process is the status quo we're replacing; any new platform that requires a
   ticket per deployment is a regression.
5. **The team has to support this on day 365.** We have a 12-person platform
   team, not 60. Operational simplicity is a first-order concern, not a
   nice-to-have.

If you don't share these constraints, your design will rightly diverge from
ours. The most common failure mode is to import an architecture wholesale
without re-deriving it from your own constraints.

---

## Section 2 — Architecture choices, the reasons, and what we considered instead

This section pairs each major choice with the alternative we rejected and the
specific reasoning. The ADRs have the full record; this is the executive
summary an engineer can read in one sitting.

### 2.1 Kubernetes (EKS) as the substrate — ADR-001, ADR-008

**Choice**: AWS EKS 1.30 with managed node groups + Karpenter for ML pools.

**Alternatives considered**:

- **AWS SageMaker** — fully managed, but couples training, serving, registry,
  and the rest into one opinionated stack. We rejected it because (a) we have
  existing investment in K8s skills, (b) per-tenant isolation is awkward, (c)
  cost optimization knobs are limited compared to raw EC2, and (d) vendor
  lock-in conflicts with the multi-cloud Year-2 roadmap.
- **GKE / AKS** — capable, but no business case to switch clouds; data gravity
  is in AWS.
- **On-prem K8s + Run:ai or similar** — capital-heavy, and we don't have the
  facilities team to support GPU servers at scale.
- **HashiCorp Nomad** — simpler, but the ML ecosystem assumes K8s (KServe,
  Kubeflow, KEDA, etc.).

**Trade-offs we accepted**: K8s is operationally heavy. We mitigate with a
small set of opinions: EKS managed node groups, Karpenter for elasticity,
Argo CD for everything-is-a-manifest, and a strict "no kubectl in prod"
policy. We don't run our own etcd, our own control plane, or our own DNS.

**Lessons learned**:
- **Karpenter > Cluster Autoscaler** for ML pools. Bin-packing and instance
  diversity are too valuable to skip. We migrated 4 months in.
- **Avoid the "one cluster per tenant" trap.** The operational cost is ~linear
  in cluster count and the per-tenant security wins are mostly achievable with
  namespaces + NetworkPolicy + IRSA. We have _one_ tenant (healthcare) on a
  dedicated node pool, no others on dedicated clusters.

### 2.2 MLflow as registry, but with custom governance — ADR-005

**Choice**: MLflow 2.14 Model Registry as the system of record, with a custom
Governance Service in front for approval workflows.

**Alternatives considered**:

- **Pure SageMaker Model Registry** — rejected with SageMaker overall.
- **Weights & Biases Artifacts** — strong UX, but expensive at our scale
  ($350K+/yr quoted), and we'd still need a governance layer on top.
- **Build it ourselves end-to-end** — rejected as YAGNI. MLflow does 80% out
  of the box.
- **Vertex AI Model Registry** — wrong cloud.

**Trade-offs we accepted**: MLflow's permission model is weak. We compensate
by putting the Platform API in front of MLflow and never exposing the MLflow
UI to end users — all writes go through the API where we enforce RBAC, tenant
scoping, and the governance workflow.

**Lesson learned**: The "MLflow as black box behind your API" pattern is the
right one. Many teams expose MLflow directly and end up reinventing RBAC
poorly. Don't.

### 2.3 Feast as feature store — ADR-002

**Choice**: Feast 0.39, online store on Redis Cluster, offline store on
Iceberg on S3, registry on Postgres.

**Alternatives considered**:

- **Tecton** — best-in-class managed feature store, ~$500K/year at our scale.
  Rejected on cost and on data-control concerns for HIPAA tenant.
- **SageMaker Feature Store** — vendor lock-in and weaker offline semantics.
- **Custom (DynamoDB online + Glue offline)** — estimated $1.5M build, 6
  engineer-quarters. Not justified when Feast covers the requirements.
- **Hopsworks** — interesting, smaller community, rejected on operational
  surface area.

**Trade-offs we accepted**:
- Feast doesn't enforce point-in-time correctness at write time, only at read
  time. We compensate by code-reviewing every materialization job and using
  the Feast feature server gRPC for production reads, never the Python SDK.
- We accept some operational burden: Feast Postgres registry, Feast
  materialization jobs, Redis Cluster ops. Mitigated by treating it as a
  first-class component with its own runbook.

**Lesson learned**: Iceberg on S3 for the offline store has aged extremely
well. Time-travel queries are gold for retraining old models against
historical feature values.

### 2.4 Kubeflow Pipelines + Argo Workflows for orchestration

**Choice**: Argo Workflows 3.5 as the execution engine, Kubeflow Pipelines 1.9
as the user-facing DSL.

**Alternatives considered**:

- **Airflow** — strong for ETL, weak for ML (no native artifact passing, awkward
  for GPU-heavy DAGs).
- **Dagster** — excellent typing and asset model, smaller ML ecosystem.
- **Flyte** — closest competitor. Considered seriously, lost on team familiarity
  with Kubeflow + Argo.
- **Step Functions** — AWS-locked, weak for parallel fan-out at our scale.
- **Prefect** — managed control plane wasn't acceptable for HIPAA tenant.

**Trade-offs we accepted**: Two layers (KFP → Argo) means two failure modes
and two upgrade cycles. We accept this because KFP gives us typed
inputs/outputs and Argo gives us scale and reliability.

**Lesson learned**: Use **Volcano** for gang scheduling of multi-pod training
jobs. Default K8s scheduler will happily schedule 6 of your 8 workers and
leave the job stuck. Wasted weeks debugging this before installing Volcano.

### 2.5 KServe for serving

**Choice**: KServe 0.13 with Knative for autoscaling, mostly Triton
Inference Server as the runtime, ONNX where possible.

**Alternatives considered**:

- **Seldon Core** — capable, license change to BSL in 2024 ruled it out.
- **BentoML** — great DX, but operationally we already had KServe in
  production for Kubeflow integration.
- **AWS SageMaker endpoints** — fine for one model, painful at our scale (50
  endpoints today, going to 500).
- **Plain Flask + HPA** — what most teams had before the platform. We've spent
  considerable effort discouraging this path.

**Trade-offs we accepted**: Knative's cold-start (scale-to-zero) is painful
for latency-sensitive models. We disable scale-to-zero for inference services
with a p99 SLO under 200ms.

**Lesson learned**: Standardize the **transformer** (pre/post-processing) as a
separate container. Lets data scientists iterate on transformer logic without
re-shipping the model.

### 2.6 Istio for service mesh — ADR-007

**Choice**: Istio 1.22 (ambient mode for stateless services, sidecar mode for
specific workloads needing L7 policies).

**Alternatives considered**:

- **Linkerd** — simpler, lighter, but weaker policy model. Considered;
  Istio won on the strength of `AuthorizationPolicy` and the team's prior
  experience.
- **Cilium service mesh** — strong eBPF story, smaller adoption surface,
  rejected as too new for a HIPAA workload at the time of the decision.
- **No mesh; just NetworkPolicy + TLS** — viable, but mTLS for free across
  every service has paid off in audit alone.

**Trade-off**: Istio is the most operationally complex component in the
platform. We minimize blast radius by pinning the version, vetting upgrades
in staging for two full weeks, and keeping a "revert to sidecar mode" runbook
for ambient-mode incidents.

**Lesson learned**: Ambient mode (no sidecars) drastically reduces resource
overhead and makes most workloads "just work" without per-pod injection
config. For workloads that genuinely need L7 policy (anything talking to
MLflow, anything in the healthcare tenant), use sidecars.

---

## Section 3 — Things we tried and walked back

A deep dive that lists only the wins is misleading. Here are the things we
shipped, ran in anger, and reversed.

### 3.1 Sidecar-mode Istio everywhere → ambient mode for most workloads

We started with sidecar mode for every workload. Resource overhead was ~15%
of cluster CPU just for sidecars. Pod startup time was 8–12s longer than
without. We moved to ambient mode for everything except workloads with strict
L7 policy requirements. Resource overhead dropped to ~3% and startup time to
baseline.

### 3.2 Tracking server on Aurora Serverless → moved to provisioned RDS

Aurora Serverless v2's cold-start behavior under MLflow's connection-storm
pattern (new run = new connection) caused tail-latency spikes. Moved to
provisioned `db.r6g.4xlarge` Multi-AZ with PgBouncer for connection
pooling. Latency stabilized.

### 3.3 In-house feature store → Feast

A previous attempt had built a custom DynamoDB-based feature store. It worked,
but six months in we had three engineers maintaining glue code that Feast
provides natively. Migration took one quarter; we have not looked back.

### 3.4 KServe scale-to-zero for all models → disabled for latency-critical

Knative cold-start is ~6–10s for our typical Triton container. Fine for batch,
disqualifying for online inference with a 200ms SLO. We disabled scale-to-zero
(minimum replicas = 2) for any inference service with a p99 SLO under 200ms.

### 3.5 Tenant-per-cluster for the healthcare team → dedicated node pool

We initially provisioned a dedicated cluster for the healthcare tenant. The
operational overhead (separate Argo CD, separate observability, separate
upgrade cycle) was disproportionate to the security gain. We collapsed back to
a single cluster with a dedicated node pool tainted for healthcare workloads,
a dedicated KMS key, and stricter NetworkPolicy. Audit accepted this design.

### 3.6 GitHub Actions for everything → GitHub Actions + Argo Workflows for ML pipelines

GHA was hitting concurrency limits when we had multiple teams running large
hyperparameter sweeps. Moved long-running ML jobs to Argo Workflows on the
cluster (where the GPUs are anyway), kept GHA for CI of platform code.

---

## Section 4 — Trade-offs that haven't aged well (yet) and are on the radar

Honest about the work that remains.

### 4.1 Monolithic Platform API

The Platform API is one FastAPI service. It's getting big (~25 routers, ~200
endpoints). We've resisted splitting it because the cognitive overhead of a
microservice split is real and the service is healthy. Plan: split out the
governance bits into a separate service when the team's ownership boundaries
make that natural — likely Q3 next year.

### 4.2 Single-region primary

Prod-EU is genuinely independent for GDPR reasons. Prod-US is single-region
(us-east-1) with cross-region async DR (us-west-2). We've accepted RTO of 4h.
There is real risk in this, and a multi-region active/active design is on the
Year-2 roadmap if a single-region outage materializes.

### 4.3 Custom governance code

We built ~3K LOC of governance code (Go). It's our largest "not invented here"
bet. So far the maintenance burden is bounded (≈0.5 engineer-quarter per
year), but if Datadog/Truera/Fiddler ever ships a better OSS approval engine,
we should evaluate replacement.

### 4.4 Spot for training, not for inference

We use Spot for training (saves ~60% on training spend) and never for
inference. Spot reclaims would violate SLOs. We tolerate the cost; we will
re-evaluate when EC2 Capacity Blocks for ML get more competitive pricing.

---

## Section 5 — Operational realities

What it actually feels like to run this platform.

### 5.1 On-call load

Per-week, on-call engineer sees ~3–5 pages (target: <10). Most common pages:
- Tenant exceeded `ResourceQuota`, KServe pod can't schedule → tenant action
- Feast online (Redis) latency spike → usually upstream Kafka backpressure
- ArgoCD `OutOfSync` for a slow rollout that timed out → almost always benign

### 5.2 Upgrade cadence

| Component | Cadence | Strategy |
|---|---|---|
| EKS | One minor version every 6 months | Pre-tested in staging for 2 weeks |
| Karpenter | Quarterly | Rolling, one nodepool at a time |
| Istio | Quarterly | Two-week staging soak; revisions, never in-place |
| MLflow | Twice a year | Schema migrations gated, backup before |
| KServe / Knative | Quarterly | Tied to Kubeflow release |
| Argo CD / Argo Workflows | Monthly patches, quarterly minor | Self-managing via App-of-Apps |
| Platform API | Daily as needed | Rolling, no downtime |

### 5.3 Things data scientists complain about most

- **Cold notebook starts** — JupyterHub pod scheduling on GPU nodes can take
  30–60s. We've improved with image pre-pulling and warm pools, still not
  great.
- **Feast SDK ergonomics** — Python SDK is OK, not joyful. We've wrapped it in
  a thinner internal SDK.
- **KServe deployment manifests** — verbose. We've added a Helm-based template
  exposed via the Platform API to hide the YAML.

---

## Section 6 — If you're considering adopting this design

Practical advice for a team setting out to build a similar platform.

1. **Don't start with everything.** Foundation phase (cluster, MLflow, basic
   CI) is enough to deliver value. Add Feast, KServe, governance in phases.
2. **Pick one pilot team that wants to be there.** Forcing reluctant adopters
   into Phase 1 is the surest way to fail. Adoption follows demonstrated wins.
3. **Treat your platform like a product.** PM, roadmap, OKRs, customer
   interviews with data scientists. The internal platforms that fail are the
   ones run as side-of-desk projects.
4. **Pay the compliance tax up front.** Adding HIPAA-grade controls to an
   existing platform is 3–5x more expensive than building them in. The
   inverse is rarely true.
5. **Buy where the differentiation is zero.** RDS, ElastiCache, EKS managed
   control plane, KMS — all worth their margin. Build where your specific
   trade-off matters (governance, FinOps, internal SDK).
6. **Standardize ruthlessly.** One feature store, one tracking server, one
   model registry, one serving stack. The cost of choice is greater than the
   cost of constraint at platform scale.

---

## Section 7 — Q&A pre-empts

A short list of questions that come up in every architecture review.

**Q: Why not Ray for training?**
A: Ray on K8s via KubeRay is a real option. We use it for specific workloads
(RLHF). For mainstream supervised training, PyTorch + TorchElastic + Volcano
covers the use case with less moving parts.

**Q: Why not vLLM for inference?**
A: We do use vLLM, behind KServe. KServe is the deployment surface; vLLM is
the runtime inside the predictor container for LLM workloads. Triton for
classical ML, vLLM for generative.

**Q: Why not Prefect/Dagster instead of Kubeflow?**
A: Both are credible. We chose Kubeflow for K8s-native scheduling and for the
existing team familiarity. Dagster's asset-centric model is genuinely better
for some teams; we expose Argo Workflows as the lower-level interface so a
team that wants to integrate Dagster can do so cleanly.

**Q: How do you handle GPU quotas across teams?**
A: ResourceQuota per namespace + a custom quota service that handles
"borrowing" of unused GPU hours between teams (with chargeback). Without
borrowing, a single team's quarterly budget peak left the platform
underutilized for two weeks.

**Q: What's the worst incident you've had?**
A: A bad Istio upgrade that caused intermittent mTLS handshake failures on a
new revision. Affected ~12% of inference traffic for 22 minutes before we
rolled back the revision. Postmortem led to the current "two-week staging
soak before any Istio touch" policy.
