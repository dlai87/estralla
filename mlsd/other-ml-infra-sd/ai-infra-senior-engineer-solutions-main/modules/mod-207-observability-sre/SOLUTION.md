# SOLUTION — Observability and SRE

> Read this *after* you have built the reference SRE-grade
> observability and incident-response infrastructure. This
> document explains *why* the senior-tier observability patterns
> exist beyond what mod-108 covers.

## What this module is really teaching

Engineer-tier (mod-108) is "wire up Prometheus + Grafana + Loki."
Senior-tier is **operating systems with SLOs**:

- Error budgets driving feature-velocity decisions.
- Burn-rate alerts that page only when they should.
- Incident retros that produce action items, not blame.
- Chaos engineering that finds weak spots before production
  does.

## Architectural decisions and *why*

### Decision 1: SLOs over uptime percentages

The reference sets SLOs (e.g., "99% of requests under 200ms over
30 days") rather than uptime targets. The reason: uptime is a
post-hoc accounting metric; SLOs are operational targets that
drive engineering decisions.

### Decision 2: Multi-window multi-burn-rate alerts

Alerting rules use two windows:
- Fast burn: page if error budget burns at >14x normal over 1
  hour (large incident).
- Slow burn: notify if burn >3x normal over 6 hours (creeping
  degradation).

The reason: single-window alerts either page constantly on
short spikes or miss slow degradation. Two windows cover both.

### Decision 3: Incident severity tied to error budget

The reference uses a clear severity ladder:
- SEV1: production down for ≥X% of users.
- SEV2: significant degradation; error budget burning fast.
- SEV3: degraded but service is working.

Each severity has a defined response pattern. Severity is not
the on-caller's call; it's defined by the data.

### Decision 4: Postmortem culture is blameless

The reference postmortem template explicitly forbids personal
blame. The reason: blame produces hidden incidents; blameless
postmortems produce systemic fixes. This is a culture decision
encoded in the template.

### Decision 5: Chaos engineering as a scheduled discipline

The reference includes ChaosMesh / LitmusChaos experiments run
on a regular cadence (monthly, quarterly). The reason:
production failures expose weaknesses you can't reason about
ahead of time. Scheduled chaos lets you find them at convenient
times.

### Decision 6: Per-team error budgets

Each team owns specific SLOs and the corresponding error
budgets. When a team burns its budget, feature work pauses for
reliability work. The reason: this aligns engineering effort
with reliability without requiring constant top-down decisions.

## Trade-offs we deliberately accepted

### Per-SLO complexity

Defining and maintaining SLOs has overhead. The reference
recommends starting with 3-5 SLOs per service, not a SLO per
endpoint.

### Synthetic monitoring cost

Synthetic monitoring (continuous canary requests) costs real
compute. The reference uses synthetics for the user-critical
paths only.

### Error budget conversations are political

Pausing feature work for reliability is unpopular with PMs.
The reference frames this as a *contract*, not a *negotiation*
— if the team accepts the SLO, they accept the budget-burning
consequences. This requires upfront agreement.

## Common mistakes graders see

1. **SLOs too tight**: 99.99% uptime SLO when the dependencies
   are at 99.9%. Impossible to meet; demoralizing.
2. **Pageable alerts that aren't actionable**: the on-call
   gets paged at 3am, looks at the alert, has no idea what to
   do.
3. **No links from alert to runbook**: same problem from a
   different angle.
4. **Status pages updated manually**: lags incidents by
   minutes-to-hours. Automate from monitoring.
5. **Postmortems with no follow-through**: action items
   defined but never tracked.
6. **Chaos engineering as a one-time stunt**: produces a flashy
   demo and zero ongoing reliability improvement.

## When to go beyond this implementation

- Adopt **error-budget-driven release management** — actual
  pauses, not just dashboards.
- Move to **continuous compliance** (Drata, Vanta) for
  regulated workloads.
- Add **game days** — full-day exercises simulating large
  outages.

## Related curriculum touchpoints

- ``engineer/mod-108-monitoring-observability`` — foundation.
- ``ml-platform/mod-008-observability`` — multi-tenant
  observability.
- ``team-lead/mod-701-team-operations`` — the team-management
  layer for on-call.
