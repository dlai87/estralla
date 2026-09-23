# SOLUTION — Data Platform for AI

> Read this *after* attempting the learning-side project. This file
> explains the architectural reasoning for the unified data platform
> and the parts that are most contested in the field today.

## What an architect is being asked to defend

The brief looks like a list of capabilities (lakehouse, streaming, data
quality, lineage) but the real architectural question is:

> Where do you put the **integration cost** between batch and
> real-time, between ad-hoc analytics and production ML training, and
> between raw and curated layers?

A well-designed data platform makes one set of these trade-offs
*explicit*. A poorly-designed one absorbs the cost in every consumer
("each team builds its own pipeline").

## Key architectural decisions and *why*

### 1. Lakehouse over separate lake + warehouse

The historical pattern (raw lake + curated warehouse) doubles your
data movement, halves your freshness, and produces two sources of
truth. Lakehouse formats (Delta Lake, Iceberg, Hudi) give you ACID on
object storage, schema evolution, and time travel — at the cost of
needing engines that respect the format (Spark, Trino, Snowflake).

Trade-off: format ecosystems are still consolidating. The architecture
nominates Delta Lake but is explicit about Iceberg and Hudi as
substitutes; the rest of the platform survives the swap.

### 2. Kafka + Flink for streaming (not Kinesis or Pub/Sub)

The choice is principally about portability and skills market. Kafka
is the de-facto open standard; Flink is the strongest open-source
streaming compute engine. The trade-off is operational cost: managed
Kafka (Confluent, MSK, Aiven) exists for teams that don't want to
operate it themselves.

### 3. Feature store as a *consumer* of the lakehouse, not a parallel
system

Feature stores in early MLOps designs lived alongside the data lake
and re-implemented half of it. The reference design makes the feature
store a *view* over lakehouse tables — features are SQL-defined,
materialization is a scheduled job, point-in-time correctness comes
from the lakehouse's time travel.

This is the single most important decision for keeping the platform
maintainable. Two parallel data systems is two parallel data problems.

### 4. DataHub for lineage and governance

Lineage is non-negotiable for any regulated environment. The choice
between DataHub, Amundsen, OpenMetadata, and Unity Catalog hinges on
your existing ecosystem; DataHub is the default here because its
plugin model handles the most heterogeneous environments.

### 5. Medallion layers (bronze / silver / gold) as a *naming
convention*, not as a hard architectural boundary

The bronze/silver/gold pattern is useful as a convention so teams
know what they're consuming (raw, conformed, curated). It is *not* a
reason to copy data three times or operate three separate stores.
The reference design uses the names as table prefixes within a single
lakehouse, with promotion via SQL.

## How to read the deliverable

1. **`ARCHITECTURE.md`** — the engineering deliverable. The
   lakehouse-as-substrate diagram is the most important figure.
2. **Cross-references to engineer-solutions modules** are how you
   actually build it: pipeline architecture in `mod-105 ex-01`,
   streaming in `mod-105 ex-11`, feature engineering in `mod-106 ex-07`.

This project's deliverable is intentionally more "decision document"
than the others; the implementation has so many viable options that
prescribing code-level patterns would not survive contact with your
existing stack.

## What's deliberately *not* in scope

- **No multi-cloud data plane.** This design assumes a single cloud
  for the lakehouse storage layer. Cross-cloud is project-302's
  problem.
- **No real-time feature serving SLOs.** The architecture supports
  real-time features; the SLO for serving them lives in the platform
  architecture (project-301), not here.
- **No specific GDPR erasure mechanics.** Tombstones / vacuum /
  reorganization is mentioned but the regulated erasure path lives
  in `ai-infra-mlops-learning/projects/project-4-governance/`.

## Production gap checklist

- [ ] Schema-evolution governance (who approves backward-incompatible
      changes, how consumers are notified)
- [ ] Cost-per-pipeline observability with per-team attribution
- [ ] Data-quality SLOs with measurable freshness, accuracy,
      completeness
- [ ] Lineage coverage SLO (target % of production-consumed datasets
      with traced lineage)
- [ ] Tombstone / vacuum cadence for the lakehouse
- [ ] Snapshot retention policy aligned with regulatory requirements
- [ ] Streaming SLA framework (delivery guarantees per stream)
- [ ] Disaster-recovery plan for the metadata catalog (not just the
      data)

## Reading order across the curriculum

| Phase | Read this |
|---|---|
| Pipeline architecture | `ai-infra-engineer-solutions/mod-105 ex-01` |
| Streaming patterns | `ai-infra-engineer-solutions/mod-105 ex-11` |
| Feature store internals | `ai-infra-engineer-solutions/mod-106 ex-07` |
| Backfill safety | `ai-infra-engineer-solutions/mod-105 ex-09` |
| Data-quality monitoring | `ai-infra-mlops-solutions/04-data-quality/` |

## Time budget for studying this solution

- **Executive read**: 90 min.
- **Engineering read**: 2 days, with a side-by-side comparison of
  Delta / Iceberg / Hudi to surface the trade-offs.
- **Adoption read**: 1–2 months to migrate an existing lake + warehouse
  setup to lakehouse and measure whether the unified model actually
  reduces the integration cost in *your* environment.
