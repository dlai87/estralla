# Enterprise Standards Guide

> Companion to `architecture-patterns.md`. How to define, propagate, and enforce technical standards across a large engineering organization without becoming the bottleneck.

---

## What this guide is

A standards organization that issues mandates is dead on arrival. A standards organization that ships paved roads and measures adoption succeeds. This guide is about how to build the second kind.

The audience is staff/principal engineers and architecture leaders. The implicit assumption is that you have organizational standing to define standards but not unlimited political capital to enforce them.

---

## Why standards fail

The pathologies recur:

| Pathology | Symptom | Root cause |
|---|---|---|
| The Wishlist | Standards document grows to 200 pages; nobody reads it | No editorial discipline; everything is a standard |
| The Wall-of-Mandates | Standards page is a list of "must do X"; teams ignore | Mandates without paved roads; teams left to figure out compliance alone |
| The Stale Doc | Standards published 2 years ago; tech has moved on | No ownership for ongoing maintenance |
| The Theater | Compliance dashboards green; production audit reveals nothing matches | Standards measured on documentation conformance, not behavior |
| The Petty Authority | Standards committee blocks legitimate work over trivial deviations | Standards used as power, not as alignment |

Each of these is a leadership failure, not a tooling failure. Better tools won't fix any of them.

---

## A different shape

A standard, in the model proposed here, has four components:

1. **The principle** — one sentence stating what we believe.
2. **The rationale** — 1-3 paragraphs explaining why we believe it.
3. **The paved road** — the supported way to comply (template, library, golden path, reference architecture).
4. **The escape hatch** — the explicit acknowledgment that the paved road won't fit every case, and the process for going off-road.

Without all four, the standard is incomplete and will be ignored or worked around.

### Example

```text
PRINCIPLE
Every production service must emit structured logs, metrics, and traces
that flow into the central observability platform.

RATIONALE
Without standardized observability we cannot operate the platform
consistently, debug incidents across team boundaries, or measure
cross-cutting health. Each team rebuilding observability differently
multiplies on-call cost and slows MTTR.

PAVED ROAD
Use the @company/observability SDK in your service. It instruments
HTTP handlers, DB calls, and outbound API calls automatically and emits
to the central OTEL collector. The Backstage scaffold (`scaffold new
http-service`) includes it by default.

ESCAPE HATCH
If the SDK doesn't fit (non-HTTP service, exotic runtime, embedded
constraint), submit an Observability Variance Request via the
"observability-variance" template in `ops/proposals/`. Reviews complete
within one week. Variances are time-boxed for one quarter and require
a follow-up review.
```

---

## Standard tiers

Not every standard carries the same weight. Three tiers:

| Tier | What it is | Compliance |
|---|---|---|
| **Mandatory** | Required by law, regulation, or board-level commitment | 100% expected; non-compliance is an incident |
| **Default** | The org's chosen way; deviation requires written justification | Adopted by all greenfield; brownfield migrated on roadmaps |
| **Recommended** | A pattern that's worked well but isn't yet org-wide policy | Teams choose; the standards body tracks adoption to inform whether to promote |

Most standards live at Default. Promoting to Mandatory is a one-way door; do it deliberately.

---

## How standards get written

The bad pattern: standards committee writes a doc, publishes it, expects compliance.

The good pattern:

1. **Discover** — patterns that work emerge from actual teams. Standards body's first job is observation.
2. **Codify** — once a pattern is working in 2-3 places and an architect spots the generalization, write it up.
3. **Socialize** — circulate the draft, gather feedback from teams that will be affected.
4. **Pilot** — name 1-2 pilot teams; help them adopt; document what breaks.
5. **Promote** — after pilots succeed, promote from Recommended to Default.
6. **Maintain** — quarterly review of every Default+ standard; sunset what's no longer current.

The cycle takes 6-12 months per standard. That's by design. Faster cycles produce shelfware.

---

## The standards backlog

Maintain a visible backlog with three sections:

- **In effect** — current Mandatory, Default, Recommended standards
- **In review** — drafts circulating, pilots in progress
- **Sunset / replaced** — historical record of standards no longer in effect (and what replaced them)

The "Sunset" section is the most important and most often skipped. It's how you avoid having teams cite obsolete standards as gospel two years later.

---

## Tooling

Standards exist in three artifacts:

1. **The catalog** — a single source of truth (a `docs/standards/` repo, a Backstage TechDocs site). Every standard has a stable ID (`STD-001`, `STD-002`). External links point to the ID, not to the URL.

2. **The decision log** — Architecture Decision Records (ADRs) for every standard's introduction, modification, and retirement. Format: MADR or Nygard. Numbered sequentially.

3. **The compliance signal** — automated where possible. Linters check for required patterns (logging structure, header presence). CI gates check for required artifacts (test coverage, SBOM presence). The compliance signal goes into a per-team dashboard; teams own their own compliance.

What to avoid: a separate "compliance team" that produces spreadsheets of who violates what. That turns into adversarial bookkeeping. Teams should see their own gaps and fix them.

---

## Governance pitfalls

### Over-centralization

Symptom: every team waits for the standards body to weigh in before making decisions. Standards body becomes a bottleneck.

Fix: delegate by domain. The data team owns data standards. The infra team owns infra standards. Cross-cutting standards (security, observability) get a virtual team with representatives from each domain.

### Under-centralization

Symptom: each team picks its own standards; cross-team integration is painful.

Fix: name a single owner per cross-cutting concern (e.g., "the org's observability owner is X"). The owner doesn't have to do all the work, but they're accountable for the integrated outcome.

### Standards as career capital

Symptom: standards proliferate because writing a standard is a visible deliverable. Quantity over quality.

Fix: incentive structure. Promote engineers for measured adoption of standards (teams using them, business outcomes), not for shipping standards docs.

### Standards as religion

Symptom: standards body refuses to revisit standards even when conditions change.

Fix: every standard has an explicit "review cadence" (quarterly, annually). When the cadence fires, the question is "is this still right?" The answer must be defended, not assumed.

---

## A starter standards set

If you're starting from zero, this is a reasonable first-year scope. Don't try to do all of them at once; pick 3-5 and ship them well.

| Standard | Tier | Owner |
|---|---|---|
| Observability (logs, metrics, traces) | Mandatory | Platform team |
| Authentication (workforce + workload) | Mandatory | Security |
| Secret management (no secrets in code, in env without rotation, etc.) | Mandatory | Security |
| Container image signing + provenance | Default | Platform / Security |
| Service API design (REST conventions, error envelopes) | Default | API platform team |
| Database schema migration process | Default | Database team |
| Incident response process | Mandatory | SRE |
| ADR practice (when and how to write ADRs) | Default | Architecture |
| Public communication / press protocol | Mandatory | Comms / Legal |

Notice: more process standards than tech-pick standards. "Use technology X" is rarely the highest-leverage standard. "Document your decisions" is.

---

## Measuring success

Lagging indicators (3-12 month horizon):

- Adoption rate per standard (% of services / teams compliant)
- Time-from-greenfield-start to first-production-deploy (lower = paved roads working)
- Cross-team incident MTTR (lower = observability + runbook standards working)
- External audit findings (lower = compliance standards working)

Leading indicators (1-3 month horizon):

- Number of variance requests filed (high but stable = healthy escape hatch use; growing = paved road has gaps)
- NPS / CSAT from product teams for the standards experience (high = standards are help, not friction)
- ADR write rate (high = decisions are being captured)

Treat the lagging indicators as the actual scoreboard. Leading indicators inform, but they don't substitute for outcomes.

---

## Closing note

The standards function is upstream of every product launch. Get it right and the org compounds. Get it wrong and every team duplicates the same wheel, slightly differently, forever.

The hardest skill in standards leadership is restraint. Not every pattern needs to be a standard. Not every standard needs to be enforced. The reputational damage from a bad mandate exceeds the upside of ten correct ones. Pick your battles, ship paved roads, and let the standards prove themselves through adoption.

---

## See also

- [`architecture-patterns.md`](./architecture-patterns.md) — the canonical patterns this guide propagates
- [`stakeholder-communication.md`](./stakeholder-communication.md) — how to socialize standards with non-engineering stakeholders
- [`cost-benefit-analysis.md`](./cost-benefit-analysis.md) — how to justify standards investments to finance
