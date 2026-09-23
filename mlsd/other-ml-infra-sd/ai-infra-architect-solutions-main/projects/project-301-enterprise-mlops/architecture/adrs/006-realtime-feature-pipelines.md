# ADR-006: Real-Time Feature Pipeline Architecture

**Status**: Accepted
**Date**: 2024-10-19
**Decision Makers**: Principal Architect, Lead ML Engineer, Data Engineering Lead
**Stakeholders**: Data Science Teams, ML Platform Team, Data Engineering Team

## Context

Some ML models require real-time features computed from streaming data (e.g., "user clicked in last 5 minutes"). Batch processing insufficient for these use cases.

### Requirements
- Process 10K-100K events/second
- <1 second latency (event to feature available)
- Exactly-once processing semantics
- Feature values must be identical in training and serving
- Integrate with Feast feature store

### Current Gap
- Only batch features available (computed daily)
- Real-time models use stale features (24-hour lag)
- Training-serving skew from different code paths
- Business impact: Fraud detection misses 20% of fraud (delayed features)

## Decision

**Flink on Kubernetes** for stream processing, integrated with Feast.

### Architecture

```
┌──────────────────────────────────────────────────────┐
│         Real-Time Feature Pipeline                    │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Event Sources                                         │
│  ┌────────────────────────────────────────────┐     │
│  │ Kafka Topics                               │     │
│  │ - user_events (clicks, views)              │     │
│  │ - transactions                             │     │
│  │ - application_logs                         │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Stream Processing (Flink on EKS)                    │
│  ┌────────────────────────────────────────────┐     │
│  │ Flink Jobs (streaming aggregations)        │     │
│  │                                             │     │
│  │ Example: user_clicks_last_5min             │     │
│  │ - Tumbling window (5 min)                  │     │
│  │ - Count by user_id                         │     │
│  │ - Write to Kafka + Redis                   │     │
│  │                                             │     │
│  │ State: RocksDB (checkpointed to S3)        │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Feature Store Integration                            │
│  ┌────────────────────────────────────────────┐     │
│  │ Kafka → Redis (Feast online store)         │     │
│  │ - Flink sink to Redis                      │     │
│  │ - Feature key: user_id:feature_name        │     │
│  │ - TTL: 7 days                              │     │
│  │                                             │     │
│  │ Kafka → S3 (training data)                 │     │
│  │ - Parquet files for point-in-time joins    │     │
│  │ - Used by Feast for training               │     │
│  └────────────────────────────────────────────┘     │
│              │                                        │
│              ▼                                        │
│  Serving (same code path!)                           │
│  ┌────────────────────────────────────────────┐     │
│  │ Model Inference: Feast SDK                 │     │
│  │ feast.get_online_features(...)             │     │
│  │ → Reads from Redis (<5ms)                  │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Flink over Spark Streaming**
- True streaming (not micro-batch)
- Exactly-once semantics (critical for financial features)
- Lower latency (<1 sec vs 5-10 sec Spark)
- Stateful operations (windowing) more efficient

**2. Kafka as Event Bus**
- Standard for event streaming
- Decouples producers/consumers
- Replay capability for retraining
- Retention: 7 days

**3. Single Code Path (Training & Serving)**
- Flink computes feature → writes to both Redis (serving) and S3 (training)
- Feast SDK used for both training and serving
- Eliminates training-serving skew
- Feature definitions in Feast (not duplicated)

**4. Checkpointing to S3**
- Flink state checkpointed every 1 minute
- Enables exactly-once processing
- Fast recovery from failures (<2 minutes)

## Alternatives Considered

**Alternative 1: Spark Structured Streaming**
- Pros: Team familiar with Spark
- Cons: Micro-batch (higher latency), less efficient for stateful ops
- **Decision**: Rejected - latency requirements

**Alternative 2: AWS Kinesis Data Analytics**
- Pros: Fully managed
- Cons: Expensive ($1+/hour per app), limited to AWS, less flexible
- **Decision**: Rejected - cost and lock-in

**Alternative 3: Lambda Functions (Serverless)**
- Pros: Simple, serverless
- Cons: No stateful operations (windowing), cold start latency, expensive at scale
- **Decision**: Rejected - can't handle windowed aggregations

**Alternative 4: Feature Computation at Inference Time**
- Pros: No streaming infrastructure needed
- Cons: High latency (compute on every request), duplicated logic, doesn't scale
- **Decision**: Rejected - too slow

## Consequences

### Positive
✅ **Low Latency**: <1 sec event-to-feature
✅ **No Skew**: Same code for training and serving
✅ **Scalable**: Flink scales to 100K+ events/sec
✅ **Reliable**: Exactly-once semantics, checkpointing
✅ **Cost-Effective**: $10K/month (vs $50K+ for managed Kinesis)

### Negative
⚠️ **Operational Complexity**: Managing Flink clusters
- *Mitigation*: Flink Kubernetes Operator, automation, monitoring

⚠️ **Learning Curve**: Team needs to learn Flink
- *Mitigation*: Training, start with simple jobs, hire Flink expert

⚠️ **State Management**: RocksDB state can grow large
- *Mitigation*: TTL on state, state compaction, monitoring

## Implementation

**Phase 1** (Months 1-2): Flink on EKS setup, 1 pilot job
**Phase 2** (Months 3-4): Kafka integration, 5 feature pipelines
**Phase 3** (Months 5-6): Feast integration, training data pipelines
**Phase 4** (Months 7-8): Production readiness, monitoring, documentation

**Estimated Cost**: $10K/month (compute + storage)

## Success Metrics

| Metric | Target |
|--------|--------|
| Event Processing Latency (p99) | <1 second |
| Feature Freshness | <2 seconds |
| Pipeline Uptime | >99.9% |
| Exactly-Once Guarantee | 100% |
| Training-Serving Skew | <1% |

## Related Decisions
- [ADR-002: Feature Store Selection](./002-feature-store-selection.md)
- [ADR-004: Data Platform Architecture](./004-data-platform-architecture.md)

---

**Approved by**: Principal Architect, Lead ML Engineer, Data Engineering Lead
**Date**: 2024-10-19
