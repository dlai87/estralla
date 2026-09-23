# ADR-009: Cost Management and FinOps Strategy

**Status**: Accepted
**Date**: 2024-10-20
**Decision Makers**: Principal Architect, VP Engineering, CFO, VP Finance
**Stakeholders**: ML Platform Team, Finance Team, Data Science Teams, Executive Leadership

## Context

ML infrastructure is expensive (GPUs, compute, storage). Need strategy to:
- Track and allocate costs to teams
- Optimize spend without impacting performance
- Forecast future costs as platform scales
- Enable cost-conscious culture (FinOps)
- Stay within $3M/year budget

### Current Spending (Projected)
- Compute (CPUs): $1.2M/year
- GPUs (training): $1.5M/year
- Storage (S3, EBS): $180K/year
- Networking: $60K/year
- Managed services (RDS, ElastiCache): $120K/year
- **Total**: $3.06M/year (slightly over budget!)

### Cost Challenges
- No cost visibility by team
- GPU utilization: 35% (industry average: 70%)
- Idle resources overnight/weekends
- No cost optimization culture
- Difficult to forecast as platform grows

## Decision

**Comprehensive FinOps Strategy** with cost allocation, optimization, and governance.

### Cost Architecture

```
┌──────────────────────────────────────────────────────┐
│              FinOps Architecture                      │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Layer 1: Cost Visibility                             │
│  ┌────────────────────────────────────────────┐     │
│  │ Kubecost (Kubernetes cost allocation)      │     │
│  │ - Per-namespace cost breakdown             │     │
│  │ - Per-pod, per-deployment metrics          │     │
│  │ - GPU cost attribution                     │     │
│  │ - Real-time dashboards                     │     │
│  │                                             │     │
│  │ AWS Cost Explorer                          │     │
│  │ - S3, RDS, data transfer costs             │     │
│  │ - Tag-based cost allocation                │     │
│  │ - Monthly reports                          │     │
│  │                                             │     │
│  │ Cost Allocation Tags                       │     │
│  │ - team:<team-name>                         │     │
│  │ - cost-center:<id>                         │     │
│  │ - project:<project-name>                   │     │
│  │ - environment:<prod|staging|dev>           │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 2: Cost Optimization                           │
│  ┌────────────────────────────────────────────┐     │
│  │ Compute Optimization                       │     │
│  │ - Spot instances (70% savings)             │     │
│  │ - Cluster Autoscaler (scale to zero)       │     │
│  │ - Right-sizing recommendations             │     │
│  │ - Reserved Instances (1-year, 40% savings) │     │
│  │                                             │     │
│  │ GPU Optimization                           │     │
│  │ - Multi-tenancy (MPS, time-slicing)        │     │
│  │ - Auto-shutdown idle GPUs (>1 hour)        │     │
│  │ - Spot GPUs for non-critical jobs          │     │
│  │ - GPU utilization monitoring               │     │
│  │                                             │     │
│  │ Storage Optimization                       │     │
│  │ - S3 Intelligent-Tiering                   │     │
│  │ - Lifecycle policies (Glacier after 90d)   │     │
│  │ - EBS snapshot cleanup                     │     │
│  │ - Delete unused volumes                    │     │
│  │                                             │     │
│  │ Network Optimization                       │     │
│  │ - VPC Endpoints (avoid NAT costs)          │     │
│  │ - Minimize cross-AZ traffic                │     │
│  │ - CloudFront for static assets             │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 3: Cost Governance                             │
│  ┌────────────────────────────────────────────┐     │
│  │ Budgets & Alerts                           │     │
│  │ - Team budgets (per namespace)             │     │
│  │ - Alerts at 80%, 90%, 100%                │     │
│  │ - Automatic notifications (Slack)          │     │
│  │                                             │     │
│  │ Chargeback Model                           │     │
│  │ - Monthly cost reports to teams            │     │
│  │ - Chargeback to cost centers               │     │
│  │ - Transparency in spending                 │     │
│  │                                             │     │
│  │ Policies                                   │     │
│  │ - Require ResourceQuotas                   │     │
│  │ - No untagged resources                    │     │
│  │ - Approval for >$10K/month                │     │
│  │ - Monthly cost reviews                     │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 4: Forecasting & Planning                      │
│  ┌────────────────────────────────────────────┐     │
│  │ Cost Modeling                              │     │
│  │ - Cost per model trained                   │     │
│  │ - Cost per inference request               │     │
│  │ - Growth projections                       │     │
│  │                                             │     │
│  │ Capacity Planning                          │     │
│  │ - Predict resource needs (6 months ahead)  │     │
│  │ - Reserved Instance planning               │     │
│  │ - Budget requests                          │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### Key Cost Optimization Strategies

**1. Spot Instances (70% savings)**
- Use Spot for fault-tolerant workloads (training, batch jobs)
- On-Demand for production serving (reliability)
- Spot interruption handling (checkpointing, job resubmission)
- **Savings**: $600K/year (50% of compute on Spot)

**2. GPU Optimization (Target: 70% utilization)**
- Multi-tenancy: NVIDIA MPS or time-slicing
- Auto-shutdown: GPUs idle >1 hour automatically terminated
- Job scheduling: Pack jobs efficiently (Kubernetes scheduler)
- **Savings**: $500K/year (eliminate waste)

**3. Reserved Instances (40% savings)**
- 1-year RI for base capacity (predictable workloads)
- Cover 40% of compute with RI
- **Savings**: $200K/year

**4. Storage Lifecycle (50% savings)**
- S3 Intelligent-Tiering: Auto-move to cheaper tiers
- Glacier after 90 days for training data
- Delete old experiment artifacts (>6 months)
- **Savings**: $80K/year

**5. Cluster Autoscaling (Scale to Zero)**
- Scale down nodes when idle (evenings, weekends)
- Scale up quickly when needed (<3 minutes)
- **Savings**: $150K/year

**Total Estimated Savings**: $1.53M/year
**Optimized Budget**: $1.53M (from $3.06M baseline)
**Well below target**: $3M/year

### Cost Allocation (Chargeback)

**Monthly Cost Reports to Teams**:
- Compute costs (CPU, GPU hours)
- Storage costs (S3, EBS)
- Network costs (data transfer)
- Shared service allocation (MLflow, Prometheus)

**Example Report**:
```
Team: Data Science
Month: October 2025

Compute (CPU): $15,000
Compute (GPU): $25,000
Storage (S3): $2,000
Storage (EBS): $1,500
Network: $800
Shared Services: $3,000 (prorated)
-------------------------
Total: $47,300

Budget: $50,000
Remaining: $2,700 (5%)
Status: ✅ On track

Recommendations:
- GPU utilization: 45% (target: 70%) → Consider smaller instances
- Old experiments: 50GB in S3 (>6 months) → Archive to Glacier (save $500/mo)
```

### Cost Governance Policies

**1. Resource Quotas Required**
- Every namespace must have ResourceQuota
- Prevents runaway costs

**2. Tagging Enforced**
- All resources must have tags: team, cost-center, project
- Automated tagging via Terraform
- Untagged resources flagged in daily report

**3. Budget Alerts**
- 80%: Warning (Slack notification)
- 90%: Alert (email to team lead)
- 100%: Critical (escalate to VP, auto-approval required for overages)

**4. Monthly Cost Reviews**
- Each team reviews costs with platform team
- Identify optimization opportunities
- Forecast next month

**5. Approval for Large Spend**
- >$10K/month new spend requires approval
- Business justification required
- Cost-benefit analysis

## Alternatives Considered

**Alternative 1: No Cost Management (Continue as-is)**
- Pros: No effort required
- Cons: Costs spiral out of control ($5M+/year), no accountability
- **Decision**: Rejected - financially unsustainable

**Alternative 2: Manual Cost Tracking (Spreadsheets)**
- Pros: Simple, no tools needed
- Cons: Inaccurate, labor-intensive, doesn't scale
- **Decision**: Rejected - error-prone, not real-time

**Alternative 3: Commercial FinOps Platform (e.g., CloudHealth, Apptio)**
- Pros: Comprehensive, enterprise features
- Cons: Expensive ($100K+/year), overkill for our needs
- **Decision**: Rejected - Kubecost + AWS Cost Explorer sufficient

**Alternative 4: Strict Cost Caps (Hard limits)**
- Pros: Guaranteed budget compliance
- Cons: Blocks innovation, teams hit limits unexpectedly
- **Decision**: Rejected - too rigid, discourages experimentation

## Consequences

### Positive
✅ **Cost Savings**: $1.53M/year (50% reduction)
✅ **Visibility**: Teams see their costs in real-time
✅ **Accountability**: Chargeback creates cost-conscious culture
✅ **Optimized**: GPU utilization 35% → 70%
✅ **Predictable**: Accurate forecasting, no surprises

### Negative
⚠️ **Overhead**: Cost management takes time (2-3 hours/week)
- *Mitigation*: Automation, dashboards, efficient processes

⚠️ **Spot Interruptions**: Training jobs may be interrupted
- *Mitigation*: Checkpointing, automatic retry, critical jobs on On-Demand

⚠️ **Cultural Change**: Teams must think about costs
- *Mitigation*: Training, incentives, celebrate optimization wins

## Implementation

**Phase 1** (Months 1-2): Kubecost deployment, tagging strategy
**Phase 2** (Months 3-4): Spot instances, autoscaling, RI purchasing
**Phase 3** (Months 5-6): GPU optimization, lifecycle policies
**Phase 4** (Months 7-8): Chargeback implementation, monthly reviews
**Phase 5** (Months 9-12): Continuous optimization, forecasting

**Implementation Cost**: $50K (Kubecost license + engineering time)
**Annual Savings**: $1.53M
**ROI**: 30x

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| **Total Annual Cost** | $3.06M | <$2M |
| **GPU Utilization** | 35% | >70% |
| **Spot Instance Adoption** | 0% | >50% |
| **Cost per Model Trained** | $500 | <$200 |
| **Teams with Budget Overruns** | N/A | <10% |
| **Cost Allocation Accuracy** | N/A | >95% |

## Related Decisions
- [ADR-003: Multi-Tenancy Design](./003-multi-tenancy-design.md) - Namespace cost allocation
- [ADR-008: Kubernetes Distribution](./008-kubernetes-distribution.md) - EKS cost optimization

---

**Approved by**: VP Engineering, CFO, VP Finance, Principal Architect
**Date**: 2024-10-20
