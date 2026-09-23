# SOLUTION — Cost and FinOps

> Read this *after* you have built the reference FinOps
> infrastructure. This document explains the architect-tier
> cost-management frame.

## What this module is really teaching

ML workloads are unusually expensive. The architect's job is to
design a cost-management capability that lets the business see,
attribute, forecast, and optimize spend.

## What the deliverables should actually look like

### Cost-attribution architecture (exercise 01)

Every resource is tagged with: environment, team, service, cost-
center, workload-type, model-name (for ML). Tagging is enforced
at provisioning. The deliverable is the tagging policy + the
attribution pipeline (cloud billing -> warehouse -> per-team
dashboards).

### FinOps team structure (exercise 02)

The reference defines:
- Central FinOps team for tooling, dashboards, anomaly
  detection.
- Embedded FinOps champions per platform team.
- Quarterly review cadence with engineering leadership.

### Reserved-capacity strategy (exercise 03)

Reserved instances / savings plans / committed-use discounts:
which to choose, what coverage % to target, how to handle
forecast uncertainty.

### Cost-anomaly detection (exercise 04)

Daily anomaly detection on per-service spend with PagerDuty
escalation for runaway costs. The reference uses cloud-native
anomaly detection (AWS Cost Anomaly Detection / GCP equivalent)
augmented with custom rules for ML workloads.

### Workload-level optimization playbook (exercise 05)

Per-workload optimization patterns: spot-instance handling,
right-sizing, scheduled scaling, cache hit-rate improvement.

## Trade-offs we deliberately accepted

- Tagging discipline requires enforcement (we accept the
  friction).
- Reserved capacity is a forecast bet.
- Cost anomaly detection has false-positives.

## Common mistakes graders see

1. **Cost dashboards no one looks at**.
2. **Tagging policy without enforcement**.
3. **Over-commitment to reservations**: pay for unused
   capacity.
4. **No on-call for cost anomalies**: a $50k/day runaway runs
   for a week.

## When to go beyond this implementation

- Adopt **showback / chargeback** beyond pure attribution.
- Integrate **carbon-footprint accounting** alongside cost.

## Related curriculum touchpoints

- ``mlops/08-production-ops`` — ML-specific cost concerns.
- ``architect/projects/project-301-enterprise-mlops`` —
  enterprise FinOps in context.
