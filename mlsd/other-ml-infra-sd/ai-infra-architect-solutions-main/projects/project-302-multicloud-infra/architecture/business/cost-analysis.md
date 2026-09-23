# Multi-Cloud Cost Analysis

**Owner**: FinOps + Cloud Architecture
**Status**: Approved input to ADR-001 (multi-cloud strategy)
**Format**: Originally maintained as a spreadsheet; this Markdown summary is the canonical, version-controlled view in the repo. The spreadsheet (cell-level formulas) lives at `gdrive://acme-finops/multicloud-tco-v3.xlsx` for active modeling.

---

## 1. What this document is

A reconciliation of:

1. The **baseline** cost of staying 100% AWS over a 3-year horizon
2. The **planned** cost of the multi-cloud split (AWS 48% / GCP 32% / Azure 20%)
3. The **savings** delivered by the split, decomposed into pricing arbitrage, workload-fit, and commitment optimization
4. The **TCO model** including hidden costs (egress, training, support uplift, migration, FinOps tooling)
5. The **FinOps governance** required to *realize* the modeled savings instead of leaking them

Numbers are in USD, annual run-rate unless explicitly marked otherwise. Currency hedging is not modeled here — finance carries that separately.

All figures are based on:

- Q1 2026 cloud list prices
- Negotiated EDP (AWS), CUD/EA (GCP), MACC (Azure) discounts in our committed agreements
- 18 months of internal billing data normalized via the FinOps tagging policy

---

## 2. Baseline: 100% AWS

Current AWS run-rate: **$38.0M / year**, distributed:

| Service family | Annual $ | % | Notes |
|---|---|---|---|
| EC2 + EBS (general compute) | $11.4M | 30% | Mixed reserved/on-demand; ~38% RI coverage |
| EKS (managed cluster) | $0.6M | 2% | Control plane fee, ~70 clusters |
| GPU (P4d, P5) | $9.5M | 25% | Training + inference; partially reserved |
| S3 + Glacier | $3.0M | 8% | 4 PB hot, 18 PB warm/cold |
| RDS + Aurora | $2.7M | 7% | 30 clusters, Multi-AZ |
| DynamoDB | $1.1M | 3% | Two top tables driving cost |
| Networking (NAT, ELB, data transfer **out**) | $4.2M | 11% | NAT egress dominates |
| Bedrock / SageMaker | $2.3M | 6% | LLM API + a few training jobs |
| CloudWatch + observability adjacent | $1.2M | 3% | Logs largest line |
| Support (Enterprise) | $1.5M | 4% | Flat 3% of spend with floor |
| Other (KMS, Lambda, etc.) | $0.5M | 1% | |

**Annualized growth without intervention**: +18% / year, driven by GPU and S3.

3-year forward (no change): $38.0M → $44.8M → $52.9M. **Cumulative 3-year baseline: $135.7M**.

---

## 3. Target distribution

Per ADR-001, the **steady-state target** is:

| Cloud | Share | Annual $ at target | Primary uses |
|---|---|---|---|
| AWS | 48% | $12.0M | Mature prod APIs, S3 primary, EKS general, DynamoDB |
| GCP | 32% | $8.0M | Training (TPU + H100), Vertex pipelines, BigQuery analytics |
| Azure | 20% | $5.0M | Microsoft-tied enterprise customers, hybrid on-prem connectivity |
| **Total target** | 100% | **$25.0M** | |

Steady-state delta vs baseline at the same workload footprint: **$38.0M − $25.0M = $13.0M / year**.

We **do not** project all $13M as net savings in year 1. After migration, support uplifts, multi-cloud tooling, and team uplift costs, the realized year-1 savings target is **$6.0M** rising to **$10.0M / year by year 3**.

Realized cumulative 3-year savings vs baseline: **$24M** (year 1: $6M; year 2: $8M; year 3: $10M).

---

## 4. Per-cloud cost detail

### 4.1 AWS (target $12.0M / yr)

| Line | $ / yr | Note |
|---|---|---|
| EC2 + EBS | $4.0M | 80% RI, m6i/m7i families |
| EKS | $0.4M | 40 clusters across us-east-1 + us-west-2 + eu-west-1 |
| GPU (P5) | $2.5M | Inference + spot training only; large training moves to GCP |
| S3 | $2.0M | Remains primary object store; cross-region replication |
| RDS / Aurora | $1.6M | Customer-facing OLTP |
| Networking | $1.0M | Reduced by intelligent egress (see §6) |
| Support + KMS + misc | $0.5M | Enterprise Support |

Negotiated EDP commitment: **$36M over 3y** (effectively $12M/y floor with up to 22% effective discount versus list).

### 4.2 GCP (target $8.0M / yr)

| Line | $ / yr | Note |
|---|---|---|
| GKE Autopilot + Standard | $0.6M | 12 clusters |
| TPU v5p + H100 (A3) | $3.2M | Primary training; ~45% cost advantage on the training mix vs AWS H100 list |
| Vertex AI Pipelines + Model Monitoring | $0.4M | Managed training orchestration |
| BigQuery + storage | $1.4M | Analytics warehouse + ML feature backfills |
| GCS | $0.6M | Training data hot tier |
| Networking | $0.8M | Cloud Interconnect to AWS (Megaport) |
| AlloyDB | $0.5M | One workload migrated from Aurora |
| Support (Enhanced) + misc | $0.5M | |

Negotiated CUD: **$22M over 3y** with 1- and 3-year CUDs across compute and TPU.

### 4.3 Azure (target $5.0M / yr)

| Line | $ / yr | Note |
|---|---|---|
| AKS + VMs | $1.2M | 8 clusters; reserved instances |
| Azure OpenAI Service | $1.6M | Required for some enterprise contracts |
| Cosmos DB | $0.4M | One global workload |
| Blob Storage | $0.5M | Mirrored data set for EU + Middle East |
| ExpressRoute + VNet peering | $0.6M | Microsoft 365 + on-prem hybrid |
| Azure ML | $0.3M | Limited use; mostly compliance-driven |
| Support (Pro Direct) + misc | $0.4M | |

Negotiated MACC: **$14M over 3y**.

---

## 5. Savings decomposition

Where do the savings come from? Not from "multi-cloud is cheaper" — that is folklore. They come from four specific levers.

| Lever | Annual savings | Mechanism |
|---|---|---|
| Training-workload arbitrage | $4.8M | Move large training to TPU v5p (45–55% TCO advantage on our model mix vs H100 on AWS) |
| Reservation right-sizing | $2.6M | 3-year reserved + Savings Plans rebalanced across the three providers; eliminate idle RI |
| Storage tiering | $1.4M | Move 60% of "warm" data from S3 Standard to S3 IT + Glacier IR; cross-cloud replicate cold tier into cheaper provider |
| Negotiation pressure | $1.2M | Credible second/third source enables 6–8% better effective discounts in renewal |
| Egress optimization | $1.0M | Megaport + Direct Connect / Cloud Interconnect reduce internet egress; intelligent routing keeps hot data colocated |
| **Gross savings (steady state)** | **$11.0M** | |

Net of new costs (see §7), realized savings settle at $10M/y by year 3.

---

## 6. Networking and egress

Egress is where multi-cloud strategies historically lose money. The plan keeps egress under control via:

- **Megaport ECX Fabric** in three metros (Ashburn, Frankfurt, Singapore) — flat $X per port + per-GB on the carrier
- **AWS Direct Connect** 10 Gbps per region pair to Megaport, 1-year commit
- **GCP Cloud Interconnect (Dedicated)** 10 Gbps per region pair to Megaport
- **Azure ExpressRoute** 5 Gbps per region pair (lower because Azure footprint is smaller)

Effective egress unit cost via Megaport: ~$0.02–0.04/GB versus $0.05–0.09/GB for cloud internet egress. At our projected 800 TB/month cross-cloud traffic, the saving is ~$0.6–1.5M/yr depending on routing decisions, which we modeled at $1.0M.

We pay for the private interconnect even when underused — break-even is ~120 TB/month. We are well above that today.

---

## 7. Hidden / non-obvious costs

The savings table is gross; these costs are real and consume part of the gross.

| Item | One-time | Annual | Note |
|---|---|---|---|
| Migration program (engineering, PMO) | $3.0M | — | 18 months; includes contractor surge |
| Multi-cloud tooling (Crossplane, OpenTofu, Vault, ESO, Velero across clouds) | $0.4M | $0.6M | Build + run |
| Observability fan-in (Datadog or Thanos federation across clouds) | $0.3M | $1.2M | Observability is the place where you most feel multi-cloud sprawl |
| Support uplift (Enhanced on GCP, Pro Direct on Azure) | — | $0.6M | In addition to AWS Enterprise Support |
| FinOps tooling (Kubecost, CloudHealth or Apptio Cloudability) | $0.1M | $0.5M | |
| Team skill uplift (training, certifications, hiring) | $0.5M | $0.3M | |
| **Total** | **$4.3M one-time** | **$3.2M / yr** | |

After accounting for these, the **net** picture:

| Year | Baseline (no change) | New target run-rate | Net savings | Cumulative |
|---|---|---|---|---|
| 1 | $38.0M | $32.0M (transition) | $6.0M | $6.0M |
| 2 | $44.8M | $34.8M | $10.0M | $16.0M |
| 3 | $52.9M | $42.9M | $10.0M | $26.0M (less $4.3M one-time = $21.7M net) |

ROI on the $4.3M migration spend: payback in ~10 months, IRR > 60% on a 3-year horizon.

---

## 8. Workload placement rubric

To stay disciplined about *where* a new workload lands, we use a decision rubric. Cost is third in the order, after compliance and dependency.

| Factor | Weight | Notes |
|---|---|---|
| 1. Data residency / regulation | hard constraint | Workload must live where its data is allowed |
| 2. Dependency proximity | hard constraint | Avoid cross-cloud joins on hot paths |
| 3. Cost (3-year TCO) | 35% | Including egress and reserved instance fit |
| 4. Service capability (e.g., TPU, OpenAI) | 30% | Differentiated services are why we're multi-cloud |
| 5. Team capability | 20% | Skills exist or can be built |
| 6. Risk and lock-in | 15% | Prefer portable services unless capability gap justifies lock-in |

A placement decision is logged in `architecture/decisions/placement-log.md` for every new workload above $50K/y projected spend.

---

## 9. Commitment portfolio

| Type | Cloud | Term | Coverage of baseline | Annual $ committed |
|---|---|---|---|---|
| Savings Plan (Compute) | AWS | 3y | 65% | $5.5M/y |
| RI (RDS, ElastiCache) | AWS | 1y | 80% | $1.5M/y |
| CUD (compute) | GCP | 3y | 60% | $3.0M/y |
| CUD (TPU) | GCP | 1y | 40% | $1.0M/y |
| Reserved VM | Azure | 3y | 70% | $2.5M/y |
| Reserved Cosmos DB | Azure | 1y | 50% | $0.2M/y |

Commitment refresh cadence: quarterly review, annual rebalance, with override authority for the FinOps lead.

---

## 10. FinOps governance

Savings exist on paper until governance forces realization. The program runs on four practices:

### 10.1 Tagging policy

Every cloud resource must carry:

- `acme:owner` (email)
- `acme:team`
- `acme:cost-center`
- `acme:environment` (`prod`, `staging`, `dev`)
- `acme:workload` (free-form short identifier)
- `acme:expires-at` (ISO-8601 for ephemeral)

Untagged resources are alerted within 24 hours and, after a 7-day grace, are scheduled for stop (non-prod) or escalation (prod).

### 10.2 Showback and chargeback

- **Showback** (monthly): every team sees their AWS/GCP/Azure spend, broken by service and tag, in a Looker dashboard backed by BigQuery (Cloud Billing export normalized across providers)
- **Chargeback** (quarterly): cost is allocated to BUs based on tags, with shared infrastructure allocated by RPS or storage proportion

### 10.3 Anomaly detection

- CloudHealth / Cloudability anomaly detection on daily cost per `(cloud, service, tag)` triple
- Slack alert on >25% deviation vs 28-day moving average
- Auto-ticket for >50% deviation; manual triage within 1 business day

### 10.4 Quarterly business review

- Per-team review of spend vs budget, forecast accuracy, savings realized
- Decisions on commitment renewals, retirements, workload moves
- Outputs feed `architecture/decisions/`-level ADRs when material

---

## 11. Risks and sensitivities

| Risk | $ impact | Mitigation |
|---|---|---|
| TPU availability < forecast | -$2M (forced fallback to GPU) | Maintain dual-stack training image; secondary commitment with NVIDIA H100 on GCP |
| Cross-cloud egress underestimated | -$1M | Monthly egress review; Megaport overage cap with alerting |
| Migration slips by 6 months | -$3M | Delivery program with monthly steerco; contingent contractor budget reserved |
| Team can't run 3 clouds | indirect | Skills uplift plan + 2 senior hires per cloud completed by end Q2 |
| GPU spot prices crater (good problem) | +$0.5M | Quarterly commitment review can rebalance into spot |
| Regulator forbids data leaving region | -$1M (forced overprovision) | Architecture already region-scoped; cost-modeled per region |

Sensitivity analysis: a ±10% movement in GPU/TPU pricing changes 3-year net savings by ±$2.4M.

---

## 12. References

- ADR-001 (multi-cloud strategy)
- ADR-004 (cost optimization)
- `architecture/research/cloud-comparison.md`
- AWS EDP terms (acme/aws/legal/EDP-2025)
- GCP EA terms (acme/gcp/legal/EA-2025)
- Microsoft MACC (acme/azure/legal/MACC-2025)
- Megaport master service agreement (acme/network/legal/MSA-2024)
- FinOps Foundation framework, used as the basis for our governance model
