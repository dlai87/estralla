# SOLUTION — Exercise 01: Emerging-Tech Radar (Emerging AI Hardware Application)

Reference for the matching learning exercise
[`lessons/mod-310-emerging-tech/exercises/exercise-1.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-1.md).
See also the module-level rationale in [`../SOLUTION.md`](../SOLUTION.md).

## 1. Solution overview

The learning exercise is an applied prompt: pick an emerging AI-hardware
option (novel accelerator, specialized inference chip, non-x86 host,
domain-specific silicon) and treat it as the technology under
evaluation. At the architect tier, the concrete deliverable behind that
prompt is the one named in the module SOLUTION as exercise 01: an
**emerging-tech radar** that sorts candidate hardware by maturity and
relevance and is updated on a defined cadence.

A complete submission produces:

1. A **radar artifact** (2x2 or Thoughtworks-style ring) placing the
   chosen AI-hardware options against the organization.
2. A **placement rationale** — for each entry, why it sits where it
   sits.
3. A **cadence and ownership statement** — who updates the radar,
   how often, on what signals.

## 2. Worked answer

### 2a. Radar shape

Per the module SOLUTION, the radar is a **2x2 or a Thoughtworks-style
ring** sorted by *maturity* and *relevance to the organization*. The
architect chooses one shape and holds to it — mixing shapes across
updates destroys comparability quarter-over-quarter.

Rings, if used, follow the widely-cited *adopt / trial / assess / hold*
convention.

<!-- needs-research: cite the ThoughtWorks Technology Radar methodology (the "adopt/trial/assess/hold" ring definitions and the FAQ description of how items move between rings) once a vetted link is available. -->

### 2b. Placement rationale

Every entry on the radar carries a one-paragraph rationale. Two axes
drive placement:

| Axis | What the architect is judging |
|---|---|
| Maturity | Is the vendor / project shipping to real customers? Is the tooling stable enough to build against? |
| Relevance | Does this hardware map to a workload the organization actually runs (training, high-throughput inference, edge inference, batch)? |

Entries without both a maturity and a relevance judgement are radar
decoration, not decision inputs.

### 2c. Cadence and ownership

Per the module SOLUTION, the radar is **updated quarterly**. The
architect names the owner (typically the platform-architecture team)
and the trigger events that can force an off-cycle update — a vendor
acquisition, a major benchmark change, or a change in the
organization's workload mix.

### 2d. Trade-offs the architect should call out

From the module SOLUTION: the radar is a **decision tool**, not a
marketing artifact. The common failure mode named for this exercise
is "tech radar as marketing" — a submission that reads like a vendor
brochure has missed the point.

## 3. Validation steps

- [ ] Radar shape is one of: 2x2, or a ring diagram, and is used
      consistently.
- [ ] Every entry has a placement rationale that names both a
      maturity signal and a relevance signal.
- [ ] Update cadence is named (per module SOLUTION: quarterly).
- [ ] Owner of the radar is named.
- [ ] Off-cycle update triggers are enumerated.
- [ ] The radar reads as a decision tool, not a marketing artifact.

## 4. Rubric

| Criterion (weight) | Excellent | Adequate | Insufficient |
|---|---|---|---|
| Architecture quality (40%) | Radar shape held consistently; maturity + relevance both defended per entry; workload-to-hardware fit is explicit. | Entries placed with reasoning on one axis only. | Radar is a list of names; placement unjustified. |
| Documentation (30%) | Cadence and ownership stated; off-cycle triggers listed; entries carry short rationales. | Cadence stated but no ownership or triggers. | No cadence, no ownership, no rationales. |
| Strategic thinking (20%) | "Radar is a decision tool" is treated as the central insight; entries would survive a skeptical exec review. | Some entries survive skepticism, others read as hype. | Reads as a vendor brochure. |
| Communication (10%) | Radar is legible in one glance; a stakeholder can act on it. | Legible but requires walk-through. | Requires the author to explain. |

## 5. Common mistakes

From the module SOLUTION's "common mistakes graders see":

1. **Tech radar as marketing.** The single named failure mode for this
   exercise. A radar full of "cool tech" without organizational
   relevance is not the deliverable.
2. Radar shape drifts between updates so quarter-over-quarter
   comparison is impossible.
3. No cadence and no owner — the radar goes stale within a quarter.
4. Vendor demos treated as maturity signals. The module SOLUTION
   explicitly calls out vendor evaluation based on demos as a common
   failure elsewhere in the module; the same trap applies to the
   maturity axis here.

## 6. References

- Learning exercise: [`lessons/mod-310-emerging-tech/exercises/exercise-1.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-1.md)
- Module-level architect-tier framing: [`../SOLUTION.md`](../SOLUTION.md) §"Emerging-tech radar (exercise 01)"
- Companion in this module: [`../exercise-04/SOLUTION.md`](../exercise-04/SOLUTION.md) — the vendor / OSS evaluation framework feeds the maturity axis of this radar.

<!-- needs-research: cite the ThoughtWorks Technology Radar public volumes as the canonical example of the ring-based radar shape and its cadence, once a vetted link is available. -->
