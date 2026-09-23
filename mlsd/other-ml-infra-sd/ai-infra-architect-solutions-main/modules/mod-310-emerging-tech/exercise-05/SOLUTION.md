# SOLUTION — Exercise 05: Roadmap Integration (Responsible AI Application)

Reference for the matching learning exercise
[`lessons/mod-310-emerging-tech/exercises/exercise-5.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-5.md).
See also the module-level rationale in [`../SOLUTION.md`](../SOLUTION.md).

## 1. Solution overview

The learning exercise is an applied prompt: take a responsible-AI
capability the organization has committed to (a governance program,
a bias-and-eval pipeline, a model-risk-management practice, a
guardrails / red-team capability) and integrate the emerging-tech
work from exercises 01–04 into the multi-year roadmap around it. At
the architect tier, the concrete deliverable is the one named in the
module SOLUTION as exercise 05: **roadmap integration** — closing
the loop so radar / pilot / impact / vendor decisions feed the
organization's multi-year plan.

A complete submission produces:

1. A **feedback path** from radar (exercise 01), pilots (exercise
   02), impact analyses (exercise 03), and vendor evaluations
   (exercise 04) into the multi-year roadmap.
2. A **roadmap view** that shows responsible-AI capability
   commitments and the emerging-tech decisions that support them.
3. A **cadence** for roadmap-emerging-tech reconciliation.
4. A **hand-off** to the broader long-bet framework (see the module
   SOLUTION's "Related curriculum touchpoints").

## 2. Worked answer

### 2a. Feedback path

Each emerging-tech artifact has one place it lands in the roadmap:

| Input | Roadmap effect |
|---|---|
| Radar movement (adopt / trial / assess / hold) | Adds, removes, or moves a capability line item on the roadmap. |
| Pilot exit (adopt / defer / drop) | Confirms a roadmap bet or removes it. |
| Impact analysis (adopt / pilot / defer / decline) | Sets the "next-review" date on the roadmap line item. |
| Vendor evaluation recommendation | Chooses the vendor / OSS backing the roadmap line item. |

Without this mapping the emerging-tech work is done in a vacuum.

### 2b. Roadmap view

For a responsible-AI application, the roadmap shows capability
commitments — not tools. A capability such as "the organization can
detect bias in production models within X of deployment" is the line
item; the tool chosen in exercise 04 is the current implementation.
If the vendor changes, the capability line item is stable and the
implementation swaps under it.

Capability commitments are anchored to an authoritative AI-risk
taxonomy so the roadmap can be defended to leadership and to
audit:

- **NIST AI Risk Management Framework** — capability lines can be
  mapped to Govern / Map / Measure / Manage functions.
- **OWASP Machine Learning Security Top 10** — capability lines can
  be mapped to specific ML-security risks the organization is
  committing to address.
- **MITRE ATLAS** — capability lines can be mapped to adversarial-ML
  tactics the organization is committing to defend against.

### 2c. Cadence

The module SOLUTION names quarterly as the radar cadence. Roadmap
reconciliation happens on the same cadence, immediately after the
radar update, so the roadmap always reflects the most recent radar
state.

### 2d. Hand-off

The module SOLUTION points at two follow-on modules where the long
horizon lives:

- ``principal-engineer/mod-505-long-term-technical-bets`` for the
  long-bet framework itself.
- ``principal-architect/mod-602-industry-standards`` for the
  standards-adoption frame.

A roadmap integration that does not name where the multi-year view
is maintained upstream is incomplete.

### 2e. Trade-offs the architect should call out

From the module SOLUTION: emerging-tech decisions **feed back into
the multi-year roadmap**, not the reverse. A submission that lets the
roadmap dictate which emerging tech gets on the radar has inverted
the flow.

## 3. Validation steps

- [ ] Every emerging-tech artifact (radar, pilot, impact, vendor)
      has a named point of entry into the roadmap.
- [ ] Roadmap line items are stated as capabilities, not tools.
- [ ] Capability lines are mapped to an authoritative AI-risk
      taxonomy (NIST AI RMF, OWASP ML Top 10, or MITRE ATLAS) so
      leadership can defend them.
- [ ] Cadence for reconciliation is stated (matches radar cadence).
- [ ] Hand-off to the principal-tier long-bet frame is named.

## 4. Rubric

| Criterion (weight) | Excellent | Adequate | Insufficient |
|---|---|---|---|
| Architecture quality (40%) | All four inputs land somewhere on the roadmap; capabilities mapped to a named AI-risk taxonomy. | Some inputs land, others are inferred; taxonomy mapping is generic. | Roadmap is a wish list of tools with no linkage to emerging-tech work. |
| Documentation (30%) | Roadmap view is legible to leadership; cadence and hand-off both stated. | Roadmap view legible; cadence stated but hand-off omitted. | Roadmap view technical-only; no cadence. |
| Strategic thinking (20%) | "Capabilities not tools" is honored throughout; vendor swaps do not break the roadmap. | Capabilities used at the top level, tools used at the leaf level. | Roadmap is tool-anchored. |
| Communication (10%) | Leadership can read the roadmap and see the emerging-tech dependencies without a walk-through. | Requires walk-through. | Requires the author to explain. |

## 5. Common mistakes

From the module SOLUTION's "common mistakes graders see":

1. **No follow-through on pilot learnings.** For this exercise the
   analogue is a roadmap that never integrates what pilots found —
   the emerging-tech work runs beside the roadmap instead of into
   it.
2. Roadmap items expressed as tools; when the vendor changes the
   roadmap breaks.
3. No cadence, so radar / pilot / vendor updates never reach the
   roadmap.
4. Emerging-tech decisions treated as inputs to the current
   quarter's plan instead of the multi-year roadmap.

## 6. References

- Learning exercise: [`lessons/mod-310-emerging-tech/exercises/exercise-5.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-5.md)
- Module-level architect-tier framing: [`../SOLUTION.md`](../SOLUTION.md) §"Roadmap integration (exercise 05)"
- NIST AI Risk Management Framework: <https://www.nist.gov/itl/ai-risk-management-framework>
- OWASP Machine Learning Security Top 10: <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS: <https://atlas.mitre.org/>
- Companion in this module: [`../exercise-01/SOLUTION.md`](../exercise-01/SOLUTION.md), [`../exercise-02/SOLUTION.md`](../exercise-02/SOLUTION.md), [`../exercise-03/SOLUTION.md`](../exercise-03/SOLUTION.md), [`../exercise-04/SOLUTION.md`](../exercise-04/SOLUTION.md) — this exercise integrates all of them.
- Upstream long-horizon frame (per module SOLUTION): ``principal-engineer/mod-505-long-term-technical-bets`` and ``principal-architect/mod-602-industry-standards``.

<!-- needs-research: cite the specific NIST AI RMF playbook subcategories that a capability-anchored roadmap should map to, once the current NIST AI RMF 1.0 playbook contents can be quoted directly. -->
