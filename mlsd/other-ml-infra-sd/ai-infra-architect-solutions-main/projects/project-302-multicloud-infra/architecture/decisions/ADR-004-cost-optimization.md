# ADR-004: Cost Optimization and Workload Placement

**Status**: Accepted
**Date**: 2024-01-15
**Impact**: High - $8M/year savings target

---

## Context

Current: $38M/year on AWS alone
Target: $25M/year across three clouds (35% reduction)
Must achieve without compromising performance or availability.

---

## Decision

**Multi-Pronged Cost Optimization Strategy**:

### 1. Intelligent Workload Placement

**Decision Matrix** (priority order):

| Priority | Criterion | Impact on Cost |
|----------|-----------|----------------|
| 1 | Data Residency (compliance) | Constrains options |
| 2 | Compute Cost | Primary cost driver (60% of spend) |
| 3 | Storage + Egress Cost | Secondary driver (24%) |
| 4 | Managed Service Premium | Convenience vs savings tradeoff |

**Placement Examples**:

| Workload | Optimal Cloud | Cost Savings | Rationale |
|----------|---------------|--------------|-----------|
| LLM Training | GCP (TPU v5) | $2.5M/year | TPU 50% cheaper than GPU, 2x faster |
| Object Storage | AWS S3 | $1.2M/year | Lowest egress within AWS ecosystem |
| Batch Jobs | AWS Spot | $3.0M/year | 70% spot savings, fault-tolerant |
| Enterprise Apps | Azure | $500K/year | Native AD integration avoids third-party SSO costs |

### 2. Reserved Instance Portfolio (70% of Compute)

| Cloud | Annual Commitment | Discount | Savings |
|-------|-------------------|----------|---------|
| AWS | $8M (1-year convertible RI) | 30% | $3.4M/year |
| GCP | $5M (1-year committed use) | 35% | $2.7M/year |
| Azure | $3M (1-year reserved VMs) | 28% | $1.2M/year |
| **Total** | $16M/year | 31% avg | **$7.3M/year** |

**Strategy**: 70% reserved (baseload), 20% spot (batch), 10% on-demand (burst)

### 3. Spot/Preemptible Instances (20% of Compute)

- **Training**: 80% on spot (checkpointing for fault tolerance)
- **Batch processing**: 100% on spot
- **Inference**: 0% spot (requires high availability)
- **Savings**: 60-80% vs on-demand

### 4. Storage Lifecycle Management

```hcl
# Automatic tiering policy
lifecycle_rules = {
  hot_tier = {
    days = 0-30
    storage_class = "STANDARD"
    cost_per_gb = "$0.023"
  }
  warm_tier = {
    days = 31-90
    storage_class = "INTELLIGENT_TIERING"
    cost_per_gb = "$0.010"  # 56% cheaper
  }
  cold_tier = {
    days = 91+
    storage_class = "GLACIER"
    cost_per_gb = "$0.004"  # 83% cheaper
  }
}
```

- **Savings**: $1.5M/year on storage (40% reduction)

### 5. FinOps Automation

**Cost-Aware Scheduler**:
```python
class CostAwareScheduler:
    def schedule_training_job(self, job):
        # Calculate cost per cloud
        costs = {}
        for cloud in eligible_clouds:
            gpu_cost = job.gpu_hours * pricing[cloud]['gpu_hour']
            egress_cost = job.output_size_gb * pricing[cloud]['egress_per_gb']
            costs[cloud] = gpu_cost + egress_cost

        return min(costs, key=costs.get)  # Place on cheapest
```

**Auto-Shutdown** for dev/staging:
- Non-prod environments scale to zero after hours
- Savings: $2M/year (50% of non-prod costs)

---

## Alternatives Considered

**Alternative 1**: Stay 100% on-demand for simplicity
- ❌ Rejected: Forfeits $7.3M/year in reserved savings

**Alternative 2**: 100% reserved instances
- ❌ Rejected: No flexibility for traffic spikes, overcommitment risk

**Alternative 3**: Serverless-first (Lambda, Cloud Functions, Azure Functions)
- ⚠️ Partially Accepted: Use for event-driven workloads, not suitable for long-running ML jobs

---

## Consequences

✅ **Cost Savings**: $8M/year achieved through:
  - Reserved instances: $7.3M/year
  - Workload placement: $2.5M/year
  - Spot instances: $3.0M/year
  - Storage optimization: $1.5M/year
  - Auto-shutdown: $2.0M/year
  - **Total**: $16.3M gross savings, $8M net after accounting for overlaps

✅ **Maintained Performance**: No degradation in latency or availability
⚠️ **Operational Overhead**: FinOps engineer required ($200K/year salary)
⚠️ **Spot Instance Risk**: Training jobs may get interrupted (mitigated with checkpointing)

**Validation**: Monthly FinOps review, automated cost anomaly detection

---

**Approved By**: CFO, CTO, VP Engineering, FinOps Lead
