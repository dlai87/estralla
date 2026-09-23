# ADR-004: Data Platform Architecture for ML

**Status**: Accepted
**Date**: 2024-10-18
**Decision Makers**: Principal Architect, VP Data Engineering, Lead ML Engineer
**Stakeholders**: Data Engineering Team, Data Science Teams, ML Platform Team

## Context

ML platform needs access to training data, feature storage, and model artifacts. Must integrate with existing data infrastructure and provide high-performance access for training and serving.

### Requirements
- Support 100TB+ training data
- Low-latency access for model serving (<10ms p99)
- Batch processing for feature engineering
- Real-time streaming for online features
- Data versioning and lineage
- Cost-effective storage ($0.02-0.10/GB-month)

## Decision

**Layered Data Architecture** with S3 data lake, Redshift warehouse, and specialized stores:

```
┌──────────────────────────────────────────────────────┐
│           ML Data Platform Architecture               │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Layer 1: Raw Data Ingestion                          │
│  ┌────────────────────────────────────────────┐     │
│  │ S3 Data Lake (Raw Zone)                    │     │
│  │ - Event logs, application databases        │     │
│  │ - Parquet format, partitioned by date      │     │
│  │ - Lifecycle: 90 days → Glacier            │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Layer 2: Data Processing                            │
│  ┌────────────────────────────────────────────┐     │
│  │ Spark on EKS (Feature Engineering)         │     │
│  │ - Batch jobs for feature computation       │     │
│  │ - Data quality checks                      │     │
│  │ - PySpark, Pandas UDFs                     │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Layer 3: Analytical Storage                         │
│  ┌────────────────────────────────────────────┐     │
│  │ Redshift Data Warehouse                    │     │
│  │ - Aggregated features (historical)         │     │
│  │ - SQL access for data scientists          │     │
│  │ - Feast offline store                      │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Layer 4: ML-Specific Storage                        │
│  ┌────────────────────────────────────────────┐     │
│  │ Training Data: S3 (processed zone)         │     │
│  │ - Versioned datasets (DVC)                 │     │
│  │ - Fast access for training                 │     │
│  │                                             │     │
│  │ Model Artifacts: S3 (models bucket)        │     │
│  │ - MLflow artifact store                    │     │
│  │ - Versioned model files                    │     │
│  │                                             │     │
│  │ Online Features: Redis (ElastiCache)       │     │
│  │ - <10ms latency for serving               │     │
│  │ - Feast online store                       │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### Key Components

**1. S3 Data Lake** (Primary Storage)
- Raw zone: Ingested data (Parquet, 90-day retention)
- Processed zone: Feature-engineered data (optimized for training)
- Models zone: Model artifacts and metadata
- Cost: ~$0.023/GB-month (S3 Standard)
- Lifecycle policies: Intelligent-Tiering after 90 days

**2. Redshift Data Warehouse** (Analytical Queries)
- Aggregated features for training
- SQL access for data exploration
- Feast offline store backend
- Size: 10-node cluster (ra3.4xlarge)
- Cost: ~$8K/month

**3. Redis (Low-Latency Serving)**
- Feast online store
- <5ms p99 latency
- ElastiCache Multi-AZ (cache.r6g.xlarge)
- Cost: ~$300/month

**4. Spark on EKS** (Feature Processing)
- PySpark jobs for batch feature engineering
- Kubernetes-native (scales 0 to 100 workers)
- Spot instances for cost savings (70% reduction)

## Alternatives Considered

**Alternative 1: Databricks Lakehouse**
- Pros: Integrated, managed
- Cons: Expensive ($1M+/year), vendor lock-in
- **Decision**: Rejected - cost

**Alternative 2: Snowflake Data Warehouse**
- Pros: Great SQL performance, easy to use
- Cons: Expensive ($500K+/year), compute/storage coupling
- **Decision**: Rejected - cost, less flexible

**Alternative 3: All-in-S3 (no Redshift)**
- Pros: Cheapest, simplest
- Cons: Slow SQL queries, no caching
- **Decision**: Rejected - poor query performance

## Consequences

### Positive
✅ **Cost-Effective**: $100K/year (vs $1M+ for Databricks)
✅ **Flexible**: Mix-and-match storage for use case
✅ **Scalable**: S3 infinite scale, Redshift/Spark scale independently
✅ **Fast**: <10ms serving (Redis), fast training (S3 optimized)
✅ **Standard**: S3/Redshift/Spark are industry standards

### Negative
⚠️ **Operational Complexity**: Multiple systems to manage
- *Mitigation*: Managed services (RDS, ElastiCache, Redshift), automation

⚠️ **Data Movement**: Moving data between stores
- *Mitigation*: Efficient pipelines, minimize data movement, co-locate processing

⚠️ **Cost Optimization Required**: Multiple storage costs to track
- *Mitigation*: S3 lifecycle policies, Redshift pause/resume, Kubecost

## Implementation

**Phase 1** (Months 1-2): S3 data lake + basic pipelines
**Phase 2** (Months 3-4): Redshift warehouse + Feast integration
**Phase 3** (Months 5-6): Redis online store + Spark on EKS
**Phase 4** (Months 7-8): Optimization, monitoring, cost management

**Total Estimated Cost**: $150K/year (storage + compute)

## Success Metrics

| Metric | Target |
|--------|--------|
| Training Data Access Latency | <1 second (first batch) |
| Online Feature Latency (p99) | <10ms |
| Data Quality Issues | <1% of batches |
| Storage Cost per TB | <$30/month |
| Data Pipeline Success Rate | >99% |

## Related Decisions
- [ADR-002: Feature Store Selection](./002-feature-store-selection.md)
- [ADR-001: Platform Technology Stack](./001-platform-technology-stack.md)

---

**Approved by**: Principal Architect, VP Data Engineering, Lead ML Engineer
**Date**: 2024-10-18
