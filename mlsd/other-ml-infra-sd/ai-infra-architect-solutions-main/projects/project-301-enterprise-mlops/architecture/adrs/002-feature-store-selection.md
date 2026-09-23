# ADR-002: Feature Store Technology Selection

**Status**: Accepted
**Date**: 2024-10-16
**Decision Makers**: Principal Architect, VP Engineering, Lead ML Engineer
**Stakeholders**: Data Science Teams, ML Platform Team, Data Engineering Team

## Context

Our enterprise ML platform needs a feature store to:
- Enable feature reuse across teams (reduce duplicate feature engineering)
- Ensure training-serving consistency
- Support both online and offline feature retrieval
- Track feature lineage and governance
- Scale to 1000+ features and 500+ models

### Current Pain Points

**Problem 1: Duplicate Feature Engineering**
- Each team builds same features independently (e.g., "user_30day_activity" implemented 5 times)
- Estimated waste: 30% of data engineering effort ($2M/year)
- Inconsistent implementations lead to model discrepancies

**Problem 2: Training-Serving Skew**
- Features computed differently in training vs serving
- Causes 5-15% accuracy degradation in production
- Hard to debug, costly to fix

**Problem 3: No Feature Discovery**
- Teams don't know what features exist
- Can't assess feature impact across models
- No feature lineage or governance

**Problem 4: Complex Data Pipelines**
- Teams build custom pipelines for each feature
- Mix of batch and streaming, hard to maintain
- Data quality issues not caught early

**Total Cost**: $3M/year in inefficiency and production issues

### Forces

- **Budget**: Feature store must be cost-effective (<$500K/year)
- **Data Sovereignty**: Must support HIPAA compliance (on-premise data option)
- **Team Skills**: Strong Python/K8s, limited Java/Scala
- **Integration**: Must work with existing data lake (S3) and data warehouse (Redshift)
- **Performance**: <10ms p99 latency for online serving
- **Offline Access**: Support for training (batch feature extraction)

## Decision

We will implement **Feast (Feature Store)** as an open-source, Kubernetes-native solution.

### Selected: Feast 0.34+

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                     Feast Feature Store                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Feature Definition (YAML)                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ features/user_features.yaml                          │   │
│  │ features/product_features.yaml                       │   │
│  │ features/transaction_features.yaml                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│                           ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Feast Registry (PostgreSQL)                 │   │
│  │  - Feature definitions                               │   │
│  │  - Entity types                                      │   │
│  │  - Data sources                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│              │                               │                │
│     Offline  │                               │  Online        │
│              ▼                               ▼                │
│  ┌────────────────────────┐   ┌─────────────────────────┐   │
│  │  Offline Store         │   │  Online Store           │   │
│  │  (S3 + Redshift)       │   │  (Redis/DynamoDB)       │   │
│  │  - Historical features │   │  - Low-latency serving  │   │
│  │  - Training datasets   │   │  - Real-time features   │   │
│  └────────────────────────┘   └─────────────────────────┘   │
│              │                               │                │
│              ▼                               ▼                │
│  ┌────────────────────────┐   ┌─────────────────────────┐   │
│  │  Batch Jobs            │   │  Inference Services     │   │
│  │  (Training pipelines)  │   │  (Model serving)        │   │
│  └────────────────────────┘   └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Capabilities**:
- **Feature Definition as Code**: YAML/Python feature definitions in Git
- **Dual Stores**: Offline (S3/Redshift) for training, Online (Redis) for serving
- **Point-in-Time Correctness**: Ensures no data leakage in training
- **Flexible**: Works with existing data sources (no data migration)
- **Open Source**: No licensing costs, community-driven

**Technology Stack**:
- **Feature Registry**: PostgreSQL (managed via RDS)
- **Offline Store**: S3 (Parquet files) + Redshift (for complex queries)
- **Online Store**: Redis (ElastiCache) for <10ms latency
- **Orchestration**: Kubernetes Jobs for materialization
- **SDK**: Python SDK for feature definition and retrieval

## Alternatives Considered

### Alternative 1: Tecton (Managed Feature Platform)

**Pros**:
- Fully managed (less operational burden)
- Enterprise support and SLAs
- Advanced features (real-time aggregations, feature monitoring)
- Strong governance and lineage tracking
- Proven at scale (Uber, Atlassian, etc.)

**Cons**:
- **Expensive**: $500K-1M/year based on usage
- **Vendor lock-in**: Proprietary system, difficult to migrate away
- **Compliance**: SaaS model problematic for HIPAA (would need dedicated instance +$200K)
- **Limited customization**: Can't modify for specific governance needs
- **Overkill**: Many advanced features we don't need yet

**Financial Analysis**:
- Year 1: $500K (base) + $100K (setup) = $600K
- Year 2-3: $750K/year (usage grows with scale)
- **3-Year TCO**: $2.1M

**Decision**: Rejected due to cost and vendor lock-in

---

### Alternative 2: Databricks Feature Store

**Pros**:
- Integrated with Databricks platform
- Good for Spark-based pipelines
- Unity Catalog integration for governance
- Managed service

**Cons**:
- **Requires Databricks**: Must use Databricks for all data engineering ($1M+/year)
- **Limited adoption**: Newer product, smaller community
- **Spark-centric**: Teams use Python/pandas, not Spark
- **Online serving**: Requires separate setup (not native)

**Decision**: Rejected as we don't use Databricks platform

---

### Alternative 3: AWS SageMaker Feature Store

**Pros**:
- Fully managed by AWS
- Good integration with SageMaker
- Enterprise support from AWS
- Offline and online stores built-in

**Cons**:
- **AWS lock-in**: Can't easily migrate to GCP/Azure
- **Expensive**: $300-500K/year at our scale
- **SageMaker dependency**: Works best within SageMaker ecosystem (we're using KServe)
- **Limited customization**: Hard to add custom governance workflows
- **Python SDK**: Less flexible than Feast

**Decision**: Rejected due to lock-in and SageMaker dependency

---

### Alternative 4: Custom-Built Feature Store

**Pros**:
- Perfect fit for our needs
- Full control and customization
- No licensing costs

**Cons**:
- **High development cost**: $2-3M (12-18 months, 8 engineers)
- **High risk**: Complex system, may fail to deliver
- **Ongoing maintenance**: 3-4 engineers full-time
- **Opportunity cost**: Delays platform launch by 12+ months
- **Reinventing wheel**: Mature OSS solutions exist

**TCO Analysis**:
- Development: $2.5M (Year 1)
- Maintenance: $1M/year (ongoing)
- **3-Year TCO**: $4.5M

**Decision**: Rejected as too expensive and risky

---

### Alternative 5: Hopsworks Feature Store

**Pros**:
- Open source (Community Edition)
- Comprehensive feature platform
- Good documentation
- Real-time and batch support

**Cons**:
- **Java/Scala-based**: Team has limited Java expertise
- **Complex setup**: Requires significant Hopsworks infrastructure
- **Smaller community**: Less adoption than Feast
- **Enterprise version**: Need paid version for governance ($200K+/year)

**Decision**: Rejected due to technology stack mismatch

## Consequences

### Positive

✅ **Cost Savings**: $0 licensing costs vs $500K-2.1M/year (alternatives)
✅ **Flexibility**: Can customize governance, compliance, and workflows
✅ **No Vendor Lock-In**: Open source, can migrate or fork if needed
✅ **Team Alignment**: Python-first, Kubernetes-native (matches our skills)
✅ **Cloud Agnostic**: Works on AWS, GCP, Azure (future multi-cloud ready)
✅ **Active Community**: 5K+ GitHub stars, regular releases, growing adoption
✅ **Compliance**: Full data control, can deploy on-premise if needed

### Negative

⚠️ **Operational Burden**: We manage infrastructure and operations
- *Mitigation*: Use managed services (RDS for registry, ElastiCache for Redis)
- *Effort*: 1 SRE allocated to feature store operations

⚠️ **Maturity**: Less mature than Tecton (founded 2022 vs 2019)
- *Mitigation*: Feast is production-proven (Gojek, Twitter, Zillow)
- *Risk*: Low - project is active and growing

⚠️ **Advanced Features**: Missing some advanced features (vs Tecton)
- *Missing*: Real-time stream aggregations, advanced feature monitoring
- *Mitigation*: Build custom extensions if needed (we have engineering capacity)
- *Impact*: Low - we don't need these features in Year 1

⚠️ **Support**: Community support vs enterprise SLAs
- *Mitigation*: Engage with Feast community, contribute back
- *Fallback*: Tecton commercial support available if critical ($50K/year)

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Feast project abandoned | Low | High | Active community, multiple companies using it. Fallback: migrate to Tecton |
| Performance issues at scale | Medium | Medium | POC validated <10ms p99. Monitor and optimize Redis config |
| Operational burden too high | Medium | Medium | 1 dedicated SRE, runbooks, monitoring. Re-evaluate at 6 months |
| Missing critical features | Low | Medium | Roadmap review, custom extensions, Feast contributions |
| Integration complexity | Medium | Medium | POC completed successfully, documented patterns |

## Validation

### Proof of Concept (8 weeks)

**Setup**:
- Deployed Feast on EKS
- 50 features across 3 entities (user, product, transaction)
- Online store: Redis (single node)
- Offline store: S3 (Parquet)
- 2 pilot teams (10 data scientists)

**Results**:
- ✅ <5ms p99 latency for online retrieval
- ✅ Point-in-time joins working correctly
- ✅ Successfully trained 3 models using Feast features
- ✅ Deployed 2 models with online feature serving
- ✅ Teams gave 8.5/10 satisfaction rating
- ✅ Feature reuse: 3 features reused across teams (validation of value prop)

**Issues Found**:
1. Redis connection pooling needed tuning (fixed)
2. S3 permissions required careful setup (documented)
3. Feature freshness monitoring needed (built custom dashboard)

### Cost Validation

**Estimated 3-Year TCO**:
- **Infrastructure**: $250K/year (RDS, Redis, S3, compute)
- **Development**: $400K (Year 1 - custom extensions and integrations)
- **Operations**: $300K/year (1 SRE fully allocated)
- **Total 3-Year**: $1.55M

**vs Tecton**: Savings of $550K ($2.1M - $1.55M)

**Payback Period**: Immediate (no upfront licensing)

### Expert Validation

Consulted with:
- **Gojek**: Shared their Feast setup (1000+ features, <3ms latency)
- **Twitter (X)**: Validated our architecture approach
- **Feast Maintainers**: Reviewed our design, provided guidance

**Recommendation**: All recommended Feast for our use case

## Implementation Plan

### Phase 1: Core Setup (Months 1-2)
- Deploy Feast registry (PostgreSQL on RDS)
- Setup offline store (S3 + Redshift)
- Setup online store (Redis ElastiCache, multi-AZ)
- Basic monitoring and alerting

### Phase 2: Feature Migration (Months 3-4)
- Define 100 core features (user, product, transaction entities)
- Migrate 3 pilot teams (30 data scientists)
- Build feature discovery UI (simple web app)
- Documentation and training

### Phase 3: Advanced Features (Months 5-6)
- Custom governance extensions (approval workflows)
- Feature monitoring dashboards
- Automated materialization pipelines
- Feature lineage tracking

### Phase 4: Scale (Months 7-9)
- All teams migrated (1000+ features)
- Performance optimization (caching, connection pooling)
- HA setup (Redis Cluster, multi-AZ registry)
- Disaster recovery tested

## Success Metrics

| Metric | Baseline | 6 Months | 12 Months |
|--------|----------|----------|-----------|
| **Features Defined** | 0 | 200 | 1000 |
| **Feature Reuse Rate** | 0% | 30% | 50% |
| **Online Latency (p99)** | N/A | <10ms | <5ms |
| **Training-Serving Consistency** | 70% | 95% | 99% |
| **Data Engineering Efficiency** | Baseline | +20% | +40% |
| **Teams Adopted** | 0 | 10/20 | 20/20 |

## Related Decisions

- [ADR-001: Platform Technology Stack](./001-platform-technology-stack.md) - Overall platform choices
- [ADR-004: Data Platform Architecture](./004-data-platform-architecture.md) - How Feast integrates with data lake
- [ADR-006: Real-Time Feature Pipelines](./006-realtime-feature-pipelines.md) - Streaming feature computation
- [ADR-010: Governance Framework](./010-governance-framework.md) - Feature governance policies

## Review and Update

- **Next Review**: Q2 2025 (6 months post-deployment)
- **Trigger for Revision**:
  - Performance issues (p99 >20ms sustained)
  - Operational burden too high (>2 SREs needed)
  - Critical features missing (blocking teams)
  - Feast project health deteriorates
- **Owner**: Lead ML Engineer

## References

- Feast Documentation: https://docs.feast.dev/
- Feast GitHub: https://github.com/feast-dev/feast
- Gojek Case Study: https://feast.dev/blog/gojek-ml-platform
- Feature Store Comparison: [Internal Doc - feature-store-evaluation.pdf]

---

**Approved by**: VP Engineering (John Doe), Principal Architect (Your Name), Lead ML Engineer (Jane Chen)
**Date**: 2024-10-16
