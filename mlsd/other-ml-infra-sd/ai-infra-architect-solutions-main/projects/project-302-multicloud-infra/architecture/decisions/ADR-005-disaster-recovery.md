# ADR-005: Disaster Recovery Strategy

**Status**: Accepted
**Date**: 2024-01-15
**Impact**: Critical - Business Continuity

---

## Context

**Business Requirements**:
- RTO (Recovery Time Objective): <1 hour
- RPO (Recovery Point Objective): <15 minutes data loss
- 99.95% availability target (26 minutes downtime/month)

**Disaster Scenarios**:
1. Single-region failure (e.g., AWS us-east-1 outage)
2. Cloud provider-wide outage (rare but possible)
3. Data corruption or ransomware attack
4. Network partition between clouds

---

## Decision

**Active-Active Multi-Cloud Disaster Recovery**

### Architecture

```
Normal State (Active-Active):
┌──────────────┬──────────────┬──────────────┐
│ AWS us-east-1│ GCP us-cent1 │ Azure eastus │
│ 40% traffic  │ 35% traffic  │ 25% traffic  │
│ ✅ ACTIVE    │ ✅ ACTIVE    │ ✅ ACTIVE    │
└──────────────┴──────────────┴──────────────┘

Disaster State (AWS failure):
┌──────────────┬──────────────┬──────────────┐
│ AWS us-east-1│ GCP us-cent1 │ Azure eastus │
│ ❌ FAILED    │ 60% (scaled) │ 40% (scaled) │
│              │ ✅ ACTIVE    │ ✅ ACTIVE    │
└──────────────┴──────────────┴──────────────┘
```

### Key Components

**1. Global Load Balancer** (Cloudflare)
- Health checks every 30 seconds
- Automatic failover on health check failure
- Geo-routing for latency optimization

**2. Data Replication**
- **Databases**: Multi-master PostgreSQL (BDR) with 5-minute replication lag
- **Object Storage**: Near-real-time replication (S3 CRR, gsutil rsync)
- **Achieved RPO**: 8 minutes P99 (target: <15 min)

**3. Automated Failover**

```yaml
# Failover automation
failover_procedure:
  - detection: "Health check fails for 2 consecutive checks (60 sec)"
  - notification: "PagerDuty alert to on-call (instantly)"
  - action: "Load balancer removes failed region (10 sec)"
  - scaling: "Auto-scale remaining regions to handle load (5 min)"
  - total_rto: "~6 minutes" # Well under 1-hour target
```

**4. Quarterly DR Drills**

| Test Date | Scenario | RTO Achieved | RPO Achieved | Result |
|-----------|----------|--------------|--------------|--------|
| 2024-01-10 | AWS region failure | 42 min | 6 min | ✅ Pass |
| 2023-10-15 | Database corruption | 35 min | 10 min | ✅ Pass |
| 2023-07-20 | Network partition | 28 min | 8 min | ✅ Pass |

---

## Alternatives Considered

**Alternative 1**: Cold Standby (Single Cloud)
- AWS primary, us-west-2 cold standby
- ❌ Rejected: RTO >4 hours (must provision capacity), doesn't solve cloud-wide outage

**Alternative 2**: Warm Standby (Single Cloud)
- AWS primary + secondary running at 25% capacity
- ❌ Rejected: Still doesn't solve cloud-wide outage, wasted capacity (25% idle)

**Alternative 3**: Active-Passive Multi-Cloud
- AWS primary (100% traffic), GCP passive (0% traffic)
- ❌ Rejected: Wasted GCP capacity, doesn't test failover in prod traffic

**Alternative 4**: Active-Active Single Cloud (AWS multi-region)
- ✅ Partial: Used within AWS, but doesn't solve cloud dependency

---

## Consequences

### Positive

✅ **RTO**: 42 minutes actual (target: <1 hour) - Exceeds SLO
✅ **RPO**: 8 minutes P99 (target: <15 min) - Exceeds SLO
✅ **Availability**: 99.97% actual (target: 99.95%) - Exceeds SLO
✅ **No Idle Resources**: All clouds serve production traffic (no wasted DR capacity)
✅ **Cloud Provider Independence**: Survives complete cloud outage

### Negative

⚠️ **Cost**: Running active-active in 3 clouds more expensive than single cloud with cold DR
- **Justification**: Cost offset by:
  - No wasted DR resources (everything serves production)
  - Cost savings from multi-cloud optimization ($8M/year) exceed DR premium

⚠️ **Complexity**: Managing 3 active production environments
- **Mitigation**: Unified observability (Datadog), GitOps (ArgoCD), runbooks

⚠️ **Data Consistency**: Multi-master replication can have conflicts
- **Mitigation**: Conflict-free replicated data types (CRDTs), application-level conflict resolution

### Testing and Validation

**Automated Tests** (weekly):
- Health check validation
- Failover simulation in staging
- Data replication lag monitoring

**Manual DR Drills** (quarterly):
- Full region failover test
- Runbook validation
- Team readiness assessment

**Metrics Tracking**:
```prometheus
# RTO tracking (Prometheus query)
histogram_quantile(0.95,
  rate(failover_duration_seconds_bucket[30d])
)

# RPO tracking
histogram_quantile(0.99,
  rate(data_replication_lag_seconds_bucket[30d])
)
```

---

## Recovery Procedures

### Scenario 1: Single Region Failure

```bash
# Automatic (no manual intervention)
1. Health checks fail (30 sec)
2. Load balancer removes region (10 sec)
3. Auto-scaling increases capacity in healthy regions (5 min)
4. Monitor and validate (15 min)
Total: ~6 minutes
```

### Scenario 2: Database Corruption

```bash
# Manual intervention required
1. Detect corruption (automated alerts)
2. Identify last known good snapshot (5 min)
3. Restore from snapshot (20 min)
4. Replay transaction logs to minimize data loss (10 min)
5. Validate and switch traffic (10 min)
Total: ~45 minutes
```

### Scenario 3: Ransomware Attack

```bash
# Manual intervention required
1. Isolate affected resources (immediate)
2. Identify infection point and time (30 min)
3. Restore from immutable backups (pre-infection) (60 min)
4. Apply security patches (30 min)
5. Gradual traffic ramp-up with monitoring (60 min)
Total: ~3 hours (acceptable for ransomware scenario)
```

---

## Backup Strategy

**Multi-Tiered Backups**:

| Backup Type | Frequency | Retention | Storage | Immutable |
|-------------|-----------|-----------|---------|-----------|
| **Continuous** | Real-time | 7 days | Multi-cloud replication | No |
| **Snapshots** | Hourly | 30 days | S3/GCS/Blob (regional) | Yes |
| **Daily** | Daily | 90 days | S3 Glacier / GCS Coldline | Yes |
| **Compliance** | Weekly | 7 years | Glacier Deep Archive | Yes |

**Immutability**: Backups locked with object lock (S3) / retention policy (GCS) to prevent ransomware deletion.

---

**Approved By**: CTO, VP Engineering, Cloud Architect, Security Lead
**Last DR Drill**: 2024-01-10 (Result: ✅ Pass, RTO 42 min, RPO 6 min)
**Next Review**: 2024-04-15 (Quarterly)
