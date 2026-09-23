# SOLUTION — Exercise 04: Vendor / OSS Evaluation Framework (Responsible AI Application)

Reference for the matching learning exercise
[`lessons/mod-310-emerging-tech/exercises/exercise-4.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-4.md).
See also the module-level rationale in [`../SOLUTION.md`](../SOLUTION.md).

## 1. Solution overview

The learning exercise is an applied prompt: pick a responsible-AI
capability under evaluation (a bias-testing tool, a red-team / eval
harness, a policy / guardrail engine, a model-risk-management
platform) and treat it as the vendor or OSS candidate under review.
At the architect tier, the concrete deliverable is the one named in
the module SOLUTION as exercise 04: a **vendor / OSS evaluation
framework** that scores the candidate across a fixed set of criteria
so the decision does not depend on a demo.

A complete submission produces:

1. A **criteria set** — the fixed list of dimensions the framework
   scores against.
2. A **scored evaluation** of the chosen tool against the criteria.
3. A **risk framing** that maps the tool to the AI risks the
   organization has already committed to managing.
4. A **recommendation** with a named deciding factor.

## 2. Worked answer

### 2a. Criteria set

The module SOLUTION names the criteria: **community size, governance
model, ownership concerns, migration cost out, vendor financial
health.** For a responsible-AI tool the architect adds one more axis
because the tool's purpose is risk management:

| Criterion | What the architect is judging |
|---|---|
| Community size | Is there a user base large enough that bugs surface without our team finding them first? |
| Governance model | Is the project run by a foundation, a single vendor, or a small maintainer set? What is the succession plan? |
| Ownership concerns | Who owns the IP? What happens on acquisition? For OSS: what license and what CLA? |
| Migration cost out | How coupled is the tool to our pipeline? Can we swap it? |
| Vendor financial health | Is the vendor likely to be here in three years? (Applies to OSS-with-commercial-backer too.) |
| Risk-framework alignment | Does the tool actually address risks the organization has committed to managing, or is it addressing a different risk model? |

### 2b. Scored evaluation

The candidate is scored on each criterion. Scores are defended in
one sentence per criterion — a bare number is not defensible.

### 2c. Risk framing

A responsible-AI tool only matters insofar as it addresses risks the
organization has taken a position on. The architect maps the tool's
capabilities to at least one authoritative AI-risk taxonomy the
organization uses. Three widely-referenced sources:

- **NIST AI Risk Management Framework** — the AI RMF's Govern / Map /
  Measure / Manage functions and their subcategories provide the
  vocabulary for stating which risk function the tool supports.
- **OWASP Machine Learning Security Top 10** — for risks framed as
  ML-specific security issues (e.g., input manipulation, model
  extraction).
- **MITRE ATLAS** — for adversarial-ML tactics and techniques the
  tool claims coverage against.

A submission that says "this tool improves responsible AI" without
naming which function / risk / tactic it covers has not done the
risk framing.

### 2d. Recommendation

The recommendation is one of: *adopt*, *pilot* (see exercise 02),
*shortlist without adopting*, or *decline*. The recommendation names
the deciding factor — commonly a specific weakness on migration
cost out or governance that would leave the organization exposed
if the vendor's trajectory changes.

### 2e. Trade-offs the architect should call out

From the module SOLUTION: **frameworks help but don't eliminate
judgment.** A scored table is the argument, not the answer. The
architect owns the recommendation.

## 3. Validation steps

- [ ] All five module-SOLUTION criteria are present, plus a
      risk-framework-alignment criterion.
- [ ] Every score is defended in at least one sentence.
- [ ] The tool is mapped to at least one authoritative AI-risk
      taxonomy (NIST AI RMF, OWASP ML Top 10, or MITRE ATLAS) with
      the specific function / category named.
- [ ] Migration cost out is treated as a first-class score, not a
      footnote.
- [ ] Recommendation names the deciding factor.

## 4. Rubric

| Criterion (weight) | Excellent | Adequate | Insufficient |
|---|---|---|---|
| Architecture quality (40%) | All six criteria scored and defended; tool mapped to a specific AI-risk taxonomy entry. | Criteria scored but risk mapping is generic. | Criteria list without scores or defense. |
| Documentation (30%) | Scored table + written rationale + explicit deciding factor. | Table + short rationale. | Table only. |
| Strategic thinking (20%) | "Frameworks help but don't eliminate judgment" is honored — the recommendation is not a mechanical sum of scores. | Recommendation aligned with the highest total. | Recommendation ignores the scores. |
| Communication (10%) | A stakeholder can read the recommendation and the deciding factor in the first paragraph. | Recommendation is derivable but not surfaced. | No recommendation. |

## 5. Common mistakes

From the module SOLUTION's "common mistakes graders see":

1. **Vendor evaluation based on demos**, not architecture review.
   The named failure mode for this exercise — a demo shows the happy
   path only.
2. Scoring the tool without mapping it to the organization's
   committed AI-risk taxonomy — the tool solves a problem the
   organization has not agreed it has.
3. Skipping the migration-cost-out criterion because the current
   vendor "seems fine."
4. Treating the scored total as the decision, not as one input to
   the recommendation.

## 6. References

- Learning exercise: [`lessons/mod-310-emerging-tech/exercises/exercise-4.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-4.md)
- Module-level architect-tier framing: [`../SOLUTION.md`](../SOLUTION.md) §"Vendor / OSS evaluation framework (exercise 04)"
- NIST AI Risk Management Framework: <https://www.nist.gov/itl/ai-risk-management-framework>
- OWASP Machine Learning Security Top 10: <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS: <https://atlas.mitre.org/>
- Companion in this module: [`../exercise-01/SOLUTION.md`](../exercise-01/SOLUTION.md) — the evaluation feeds the maturity axis of the radar.

<!-- needs-research: cite the specific AI RMF function ("Govern" / "Map" / "Measure" / "Manage") and playbook subcategory that a responsible-AI evaluation should map to, once the current NIST AI RMF 1.0 playbook contents can be quoted directly. -->
