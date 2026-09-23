# Cloud Provider Comparison — AWS vs GCP vs Azure

**Owner**: Cloud Architecture
**Status**: Input to ADR-001 (multi-cloud strategy)
**Date of source data**: Q1 2026, refreshed every 6 months
**Audience**: Architects, finance, procurement

---

## 1. How to read this document

This is not a "pick the winner" memo. The point of multi-cloud is precisely that no single provider wins across all dimensions. The document compares AWS, GCP, and Azure across the dimensions that *actually* matter for our AI infrastructure: ML services, GPU and accelerator availability, data services, networking, identity, pricing, lock-in, and support. Each section ends with **"What this means for us"** — the workload-placement implication.

---

## 2. AI/ML services

### 2.1 Managed training and serving

| Capability | AWS | GCP | Azure |
|---|---|---|---|
| Managed training | SageMaker Training + HyperPod (managed clusters for foundation-model training) | Vertex AI Training; GKE + JobSet for self-managed | Azure ML + Azure ML compute clusters |
| Managed inference | SageMaker Inference (real-time, async, batch); Bedrock for foundation models | Vertex AI Endpoints; Cloud Run for stateless | Azure ML Online Endpoints; Azure OpenAI Service for hosted GPT-4/o4 |
| Pipeline orchestration | SageMaker Pipelines; Step Functions | Vertex AI Pipelines (Kubeflow Pipelines DSL); Workflows | Azure ML Pipelines |
| Model registry | SageMaker Model Registry | Vertex AI Model Registry | Azure ML Model Registry |
| Feature store | SageMaker Feature Store | Vertex AI Feature Store / Feast on GKE | Azure ML Feature Store (GA 2025) |
| LLM/foundation model service | Bedrock (Claude, Llama, Mistral, Titan, Cohere) | Vertex AI Model Garden (Gemini, Claude, Llama, Mistral) | Azure OpenAI Service (GPT-4, GPT-4o, o1, o3 family) |
| Notebook hosting | SageMaker Studio | Vertex AI Workbench / Colab Enterprise | Azure ML Studio |

**What this means for us**: Vertex AI Pipelines is the most Kubeflow-aligned managed orchestrator, which matches our existing pipeline DSL. SageMaker is the most full-stack and the most opinionated; we use it where teams want managed end-to-end. Azure OpenAI is the **only** way to get GPT-4-family models under an enterprise contract with EU data residency, which is contractually required by two of our enterprise customers. Across the three, the only **unique** capability is the model family itself; pipelines are converging.

### 2.2 Foundation models

| Model family | AWS Bedrock | GCP Vertex Model Garden | Azure OpenAI |
|---|---|---|---|
| Claude (Sonnet, Opus, Haiku) | Yes | Yes | No (only via partner) |
| Gemini (1.5, 2.0, 2.5) | No | Yes | No |
| GPT-4 / GPT-4o / o1 / o3 | No | No | Yes |
| Llama 3 / 3.1 / 4 | Yes | Yes | Yes (limited) |
| Mistral | Yes | Yes | Yes |
| Custom fine-tuned hosting | Yes (Bedrock custom models) | Yes (Vertex deploy) | Yes (Azure ML) |
| Inference latency (typical p50, region-local) | 200–600ms first token | 150–500ms first token | 100–400ms first token (GPT-4o) |
| Throughput billing | Provisioned units or pay-per-token | Pay-per-token or PTU equivalent | PTU (Provisioned Throughput Units) or pay-as-you-go |

**What this means for us**: each cloud is *non-substitutable* for its respective model family. The decision is: where does the workload need to live (residency, dependency proximity), and which model family does the team want?

### 2.3 Accelerator-aware managed services

- **AWS**: SageMaker HyperPod manages multi-node training clusters with built-in checkpointing, EFA networking, and Trainium support; Inferentia2 for inference cost reduction.
- **GCP**: Vertex AI Training has first-class TPU v5e / v5p / v6e support; auto-shaped distributed JAX/Flax training; TPU Pods at >1000 chips.
- **Azure**: AML supports H100 / H200 / MI300X clusters with InfiniBand; ND series VMs are the workhorse.

**What this means for us**: TPU access is exclusive to GCP and is the single largest cost lever in our training portfolio (see `architecture/business/cost-analysis.md` §5). Trainium has improved but is workload-sensitive — promising for selected LLM inference, not yet our training default.

---

## 3. GPU and accelerator availability

This is the most volatile dimension. Numbers below reflect Q1 2026 reality, not list-price marketing.

| Accelerator | AWS instance | GCP machine type | Azure VM | Realistic availability today |
|---|---|---|---|---|
| H100 80GB SXM (8-GPU node) | `p5.48xlarge` | A3 high / A3 mega (`a3-highgpu-8g`) | `ND H100 v5` | Tight on AWS unless capacity reservation; better on Azure ND H100 v5; GCP A3 with reservation works |
| H200 141GB SXM | `p5e.48xlarge` | A3 ultra (`a3-ultragpu-8g`) | `ND H200 v5` (limited regions) | Constrained on all three; reservation required |
| B200 (Blackwell) | `p6-b200` (limited regions) | A4 (`a4-highgpu`) | `ND B200 v6` (preview/early GA depending on region) | All three rolling out; AWS and Azure leading in US, GCP leading in EU |
| MI300X (AMD) | Limited via Bedrock-backed (not general EC2) | Not generally available | `ND MI300X v5` | Azure is the only practical large-volume option |
| TPU v5p | — | `ct5p-hightpu-4t` and Pod slices | — | Exclusive to GCP; plentiful availability in `us-central1` and `europe-west4` |
| TPU v6e (Trillium) | — | `ct6e-standard-*` | — | GA in 2025; capacity reservations work |
| Trainium2 | `trn2.48xlarge` and UltraServer | — | — | AWS-exclusive; capacity OK in `us-east-1`, `us-east-2` |
| Inferentia2 | `inf2.*` | — | — | AWS-exclusive; abundant |

Effective quota signals (informal, based on negotiated commitments and current ticket turnaround):

- **AWS H100**: 64–128 chips with reservation in 4-6 weeks; 256+ requires EDP renegotiation
- **GCP H100 / A3**: 128–256 chips in 2-4 weeks with reservation; **TPU v5p 256–1024 chips** typically in 1–2 weeks
- **Azure H100 / H200**: very strong availability in `eastus2`, `swedencentral`; tighter in `westeurope`

Cost (effective, 3-year reserved, 8-GPU node):

| Node class | AWS | GCP | Azure |
|---|---|---|---|
| 8× H100 80GB | ~$50–55K/mo | ~$45–50K/mo | ~$45–52K/mo |
| 8× H200 141GB | ~$60–68K/mo | ~$55–62K/mo | ~$56–64K/mo |
| 4-chip TPU v5p | — | ~$18–22K/mo | — |

(Ranges reflect spot/uncommitted vs reserved variance; commitments cut these by 20–35%.)

**What this means for us**:
- For large *training* workloads, GCP TPU v5p remains the best $-per-FLOP for our model mix.
- For *foundation-model inference* with NVIDIA software, AWS Inferentia2 closes the gap for our high-throughput tier-1 endpoints.
- Azure ND H100 v5 has been the most *reliable to provision in EU regions* over the last 6 months — useful when EU residency constrains the training region.

---

## 4. Data services

### 4.1 Object storage

| | AWS S3 | GCP Cloud Storage | Azure Blob Storage |
|---|---|---|---|
| Strong-consistency reads | Yes (since 2020) | Yes | Yes |
| Single-zone class | One Zone-IA | Single Region | LRS |
| Archive tier | Glacier Deep Archive ($1.0/TB/mo) | Archive ($1.2/TB/mo) | Archive ($0.99/TB/mo) |
| Object lock (compliance) | Yes | Yes (retention policies) | Yes (immutable storage) |
| Cross-region replication | Built-in (CRR) | Multi-region buckets | Object replication / GZRS |
| Native lifecycle | Yes | Yes | Yes |

S3 has the broadest ecosystem and the most mature multipart-upload throughput; GCS handles multi-region buckets with a simpler model (one bucket, multiple regions); Azure ADLS Gen2 hierarchical namespace makes it the strongest for large-file analytics workloads.

**What this means for us**: S3 stays the primary object store. GCS holds the training-data hot tier in EU regions to avoid cross-cloud reads during TPU training. ADLS Gen2 holds a mirrored dataset for Azure-resident workloads.

### 4.2 Data warehouse and analytics

| Workload | AWS | GCP | Azure |
|---|---|---|---|
| Cloud-native warehouse | Redshift (RA3 / Serverless) | BigQuery (most-used by us) | Synapse Analytics; Fabric Warehouse |
| Lakehouse | Athena + Glue + Iceberg (or EMR + Hudi/Delta) | BigLake + BigQuery | Microsoft Fabric (Lakehouse + OneLake) |
| Streaming | Kinesis + MSK | Pub/Sub + Dataflow | Event Hubs + Stream Analytics |
| ETL/orchestration | Glue, Step Functions | Dataflow, Composer (managed Airflow) | Data Factory, Synapse Pipelines |
| Managed Airflow | MWAA | Cloud Composer | Microsoft Fabric Data Factory (Airflow integration) |

BigQuery's serverless model and slot-based pricing wins for analytical workloads at our scale. Snowflake (cross-cloud SaaS) is also part of our stack and is described in §4.3.

### 4.3 Operational databases

| Category | AWS | GCP | Azure |
|---|---|---|---|
| Relational (managed) | Aurora (PostgreSQL/MySQL), RDS | Cloud SQL (PG/MySQL), AlloyDB (PG-compatible, HTAP) | Azure Database for PostgreSQL / MySQL, Azure SQL Database |
| NoSQL document | DynamoDB | Firestore, Bigtable | Cosmos DB (multi-API), Azure Table |
| Key-value | DynamoDB, ElastiCache | Memorystore (Redis/Memcached), Bigtable | Azure Cache for Redis, Cosmos DB |
| Graph | Neptune | Spanner Graph (preview / early GA) | Cosmos DB Gremlin API |
| Vector | OpenSearch + Aurora pgvector | AlloyDB (vector), Vertex Vector Search | Cosmos DB vector, Azure AI Search |

**What this means for us**:
- Aurora PostgreSQL stays the customer-facing OLTP default.
- AlloyDB is in evaluation for one analytics-leaning workload (HTAP characteristics, Postgres compatible).
- Cosmos DB is used for one global multi-region workload that needs <10ms p99 anywhere.
- For vectors, we use pgvector on Aurora for general; Vertex Vector Search for the dataset that already lives in BigQuery; Azure AI Search where AzureOpenAI integrations are needed.

### 4.4 Snowflake (cross-cloud)

- Snowflake runs on AWS, GCP, and Azure with cross-cloud replication (database / share / listing replication)
- Pricing: per-second compute on credits ($2–4 per credit depending on edition/cloud); storage at ~cloud rates
- Why we use it: avoids data-gravity lock-in in any single cloud; one query layer across regions; first-class Snowpark for ML feature engineering

---

## 5. Networking

| Capability | AWS | GCP | Azure |
|---|---|---|---|
| Region count (general purpose) | 33 | 41 | 60+ |
| AZs per region | 3 typically (some 4–6) | 3 typically (some 4) | Mixed (some regions are AZ-paired only) |
| Backbone latency | Strong, especially intra-US | Strongest globally — single private backbone | Strong, depends on region pairing |
| Private interconnect | Direct Connect | Cloud Interconnect (Dedicated, Partner) | ExpressRoute |
| Cross-cloud private | Direct Connect → Megaport → others | Cloud Interconnect → Megaport → others | ExpressRoute → Megaport → others |
| Egress (internet, $/GB after free tier) | $0.05–0.09 | $0.08–0.12 | $0.08–0.12 |
| Cross-region egress | $0.02–0.04 | $0.01–0.05 | $0.02–0.05 |
| Service mesh-friendly load balancing | Network Load Balancer + AWS LB Controller | Network Endpoint Groups + GLB | Azure Load Balancer + Application Gateway |
| Anycast global LB | Global Accelerator | Cloud Load Balancing (GCLB anycast) | Front Door |

GCP's network typically wins benchmark comparisons for cross-region and global routing because of its private global backbone; AWS catches up via Global Accelerator with comparable real-world performance for application traffic. Azure has the broadest region presence and the best Microsoft-property network adjacency (M365, Dynamics).

**What this means for us**: cross-cloud private connectivity via Megaport ECX Fabric (see `cost-analysis.md` §6) is the unifying layer.

---

## 6. Identity and access

| Capability | AWS | GCP | Azure |
|---|---|---|---|
| Workload identity (OIDC) federation | OIDC providers + IAM Roles | Workload Identity Federation | Workload Identity Federation (entra-managed identity) |
| Kubernetes pod identity | IRSA, EKS Pod Identity | Workload Identity for GKE | Azure AD Workload Identity for AKS |
| Cross-cloud SSO | IAM Identity Center | Cloud Identity | Microsoft Entra ID (Azure AD) |
| Secrets | Secrets Manager, Parameter Store | Secret Manager | Key Vault |
| HSM | CloudHSM, KMS HSM-backed | Cloud HSM, EKM | Managed HSM (FIPS 140-2 L3) |

We standardize on **Microsoft Entra ID** as the human-identity hub (workforce SSO into all three clouds), and **SPIFFE/SPIRE** for workload identity inside the mesh. Cloud-native workload identity (IRSA, GKE WI, Azure WI) is used at the cloud boundary.

---

## 7. Pricing models

### 7.1 Discount mechanisms

| Provider | Mechanism | Term | Typical effective discount |
|---|---|---|---|
| AWS | Savings Plans (Compute / EC2 Instance / SageMaker) | 1y / 3y | 17–66% depending on coverage + term |
| AWS | Reserved Instances | 1y / 3y | up to ~75% |
| AWS | Spot | hourly | up to 90% (with interruption risk) |
| AWS | EDP (Enterprise Discount Program) | 3y commit | Add 5–20% on top of public pricing |
| GCP | Committed Use Discounts (CUD) | 1y / 3y | 25–55% |
| GCP | Sustained Use Discounts | automatic | up to 30% |
| GCP | Spot VMs | hourly | up to 91% |
| GCP | EA discount | 3y commit | 5–20% additional |
| Azure | Reservations | 1y / 3y | up to 72% |
| Azure | Savings Plan for Compute | 1y / 3y | up to 65% |
| Azure | Spot VMs | hourly | up to 90% |
| Azure | MACC (Microsoft Azure Consumption Commitment) | 3y / 5y | Stacking discount + ELA leverage |

### 7.2 Egress pricing structure

All three providers waived first-1GB-per-month internet egress per region and offer free intra-region traffic between same-AZ resources. Cross-AZ and cross-region traffic still costs. The EU has forced waivers for **migration egress** (provider switch), which is now operational; cross-cloud everyday egress remains chargeable.

### 7.3 Where vendor TCO differs in practice

- For **steady-state CPU compute** with high reservation coverage, the three are within ~10% of each other.
- For **GPU**, GCP TPU v5p is 30–55% cheaper on our training mix than equivalent H100 capacity on any provider (measured via tokens/$).
- For **storage**, S3 + Glacier is ~5–15% cheaper than equivalent GCS or ADLS for our retention profile.
- For **data warehouse**, BigQuery slot-based pricing is favorable for our irregular query pattern.
- For **LLM API**, Azure OpenAI is the only path to GPT-4-family with EU residency and enterprise SLAs; pay-as-you-go is comparable to Anthropic on AWS Bedrock and Vertex.

---

## 8. Vendor lock-in risk

| Lock-in vector | AWS | GCP | Azure | Mitigation |
|---|---|---|---|---|
| Proprietary services (DynamoDB, BigQuery, Cosmos DB) | Yes | Yes | Yes | Workload-by-workload TCO decision; use only when capability gap is real |
| Proprietary AI (Bedrock, Vertex Garden, Azure OpenAI) | Medium | Medium | High | Standardized SDK abstraction in `mlops-sdk`; LiteLLM gateway for portability |
| Networking (region IDs, VPC mental model) | Medium | Medium | Medium | OpenTofu modules abstract |
| Identity (IAM model differences) | Medium | Medium | Medium | Entra ID + SPIFFE common layer |
| Data formats | Low (Parquet, Iceberg are open) | Low | Low | Standardize on Iceberg + Parquet |
| Egress economics (data gravity) | High | High | High | Megaport; replicate hot data; minimize cross-cloud read paths |

The honest assessment: **multi-cloud reduces lock-in at the org level but accepts more local lock-in inside each cloud's specialty workload.** TPU lock-in to GCP for training, Azure OpenAI lock-in for GPT-4 — both are accepted because the alternative is to forgo the capability.

---

## 9. Support SLAs

| Tier | AWS (Enterprise) | GCP (Enhanced) | Azure (Pro Direct) |
|---|---|---|---|
| Response — critical | <15 min | <15 min | <15 min |
| Response — production | <1 hr | <1 hr | <2 hr |
| TAM included | Yes | Yes (large customers) | Yes |
| Architecture reviews | Yes | Yes | Yes |
| Annual cost | Greater of $15K/mo or 3% of monthly spend (with tiering) | Greater of $12.5K/mo or 4% (with tiering) | Greater of $1K/mo or 10% (with tiering, capped) |
| Severity-1 phone bridge | Yes | Yes | Yes |

**What this means for us**: AWS Enterprise Support is the most expensive in absolute dollars but justified at our $12M+ AWS spend. GCP Enhanced and Azure Pro Direct are at lower spend and lower fee. Critical-path runbooks should not depend on cloud-support response — the team must be capable of mitigating without it.

---

## 10. Compliance and certifications

| Standard | AWS | GCP | Azure |
|---|---|---|---|
| SOC 2 Type II | Yes | Yes | Yes |
| ISO 27001 / 27017 / 27018 | Yes | Yes | Yes |
| HIPAA (BAA) | Yes | Yes | Yes |
| PCI-DSS L1 | Yes | Yes | Yes |
| FedRAMP High | Yes | Yes | Yes |
| HDS (France) | Yes | Yes | Yes |
| C5 (Germany) | Yes | Yes | Yes |
| IL5 (US DoD) | Yes (GovCloud) | Limited | Yes (Azure Government) |
| EU sovereign cloud | EU Sovereign Cloud (2026) | Sovereign Cloud partners (T-Systems, Thales, etc.) | Microsoft Cloud for Sovereignty |

All three meet our baseline compliance needs. Sector-specific certifications drive workload placement at the margin (HDS in France → AWS Paris, etc.).

---

## 11. Operational ergonomics (subjective, from our team)

Based on internal survey of 28 engineers, scored 1–5 (5 = best). Not a benchmark, an honest signal.

| Dimension | AWS | GCP | Azure |
|---|---|---|---|
| Documentation quality | 3.5 | 4.5 | 3.0 |
| Console UX | 3.0 | 4.0 | 3.0 |
| CLI ergonomics | 4.0 | 4.5 | 3.5 |
| API consistency | 3.0 | 4.0 | 3.0 |
| Service breadth | 5.0 | 4.0 | 4.5 |
| K8s integration | 4.0 | 5.0 | 4.0 |
| Permissions model clarity | 2.5 | 4.0 | 3.0 |
| Time to debug an outage | 3.5 | 4.0 | 3.0 |

**What this means for us**: GCP wins the developer ergonomics race; AWS wins on breadth; Azure is the strongest fit when the workload pulls Microsoft identity, productivity, or enterprise integration.

---

## 12. Synthesis

The three clouds map naturally onto three roles in our portfolio:

- **AWS — the platform of record**: mature production APIs, S3 as primary, the broadest ecosystem, the EDP-backed economic floor.
- **GCP — the AI/ML accelerator**: TPU economics, Vertex pipelines, BigQuery as the analytical core.
- **Azure — the enterprise hinge**: GPT-4 family under EU residency, Microsoft identity integration, hybrid on-prem reach.

Single-cloud was attractive when our portfolio was narrower. The combination of AI/ML workload diversity, regulatory geography, and procurement leverage justifies the operational tax of running three. The numbers in `architecture/business/cost-analysis.md` quantify it.

---

## 13. References

- AWS pricing pages, AWS calculator (`https://calculator.aws/`)
- GCP pricing pages, GCP calculator (`https://cloud.google.com/products/calculator`)
- Azure pricing pages, Azure calculator (`https://azure.microsoft.com/en-us/pricing/calculator/`)
- Internal benchmark suite (`bench/cross-cloud/`) — synthetic training and inference comparisons updated quarterly
- ADR-001, ADR-003, ADR-004
- `architecture/business/cost-analysis.md`
- `architecture/governance/data-residency-matrix.md`
- `reference-implementation/IMPLEMENTATION_GUIDE.md`
