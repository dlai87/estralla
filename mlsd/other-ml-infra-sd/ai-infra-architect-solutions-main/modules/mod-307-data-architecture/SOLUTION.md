# SOLUTION — Data Architecture

> Read this *after* you have designed the reference enterprise
> data architecture. This document explains the architect-tier
> data-platform frame.

## What this module is really teaching

ML lives on data; data architecture decisions made before ML
shows up determine what's possible. The architect frames:
- Lake-house vs. warehouse vs. lakehouse.
- Streaming vs. batch ingestion.
- Data ownership / domains.
- Schema evolution policy.

## What the deliverables should actually look like

### Data architecture reference document (exercise 01)

The document describes:
- Bronze / silver / gold tiers.
- Ingestion patterns per source.
- Catalog and discovery layer.
- Access-control model.

### Data-mesh vs. centralized decision (exercise 02)

Centralized data platforms scale to ~5-10 producing teams; past
that, data mesh (domain ownership) tends to scale better.
The deliverable picks one with reasoning.

### Schema evolution policy (exercise 03)

Forward / backward / full compatibility per data class.
Breaking changes require version bumps and consumer migration
windows.

### Data contract template (exercise 04)

Producer / consumer / SLA / schema / change-process. Contracts
are versioned alongside producing code.

### Catalog strategy (exercise 05)

Discovery + lineage + glossary. The reference uses DataHub or
Amundsen; the decision considers OSS-maturity vs. vendor
support.

## Trade-offs we deliberately accepted

- Data-mesh has organizational prerequisites (mature
  engineering culture, willing domain owners).
- Schema evolution discipline is constant work.
- Catalog tooling is fragmented in 2026.

## Common mistakes graders see

1. **Data-mesh declared but no domain ownership**: chaos.
2. **Contracts that producers don't sign onto**: not real
   contracts.
3. **Catalog without entry curation**: useless search.
4. **Schema changes pushed without consumer review**:
   downstream breakage.

## When to go beyond this implementation

- Adopt **Iceberg / Delta Lake** for ACID lake storage.
- Move to **streaming-first** for low-latency use cases.

## Related curriculum touchpoints

- ``engineer/mod-105-data-pipelines`` — data engineering
  foundations.
- ``architect/projects/project-304-data-platform`` — the
  enterprise data platform.
