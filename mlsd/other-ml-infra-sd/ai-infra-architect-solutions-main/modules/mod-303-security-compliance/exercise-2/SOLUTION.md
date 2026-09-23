# SOLUTION — Exercise 2: GDPR Application

> Pairs with
> `ai-infra-architect-learning/lessons/mod-303-security-compliance/exercises/exercise-2.md`.
> Factored from the module-level `SOLUTION.md` in this directory's parent.

## 1. Solution overview

This exercise is the **compliance-mapping** deliverable from the
module solution applied to the **GDPR** compliance frame. The
architect-tier answer is *not* a GDPR clause-by-clause checklist;
it is a mapping artifact that:

- Names every GDPR obligation that touches the AI/ML platform.
- Assigns each obligation to a **control owner** and an
  **implementation pattern**.
- Produces a single source of truth that audit and DPO functions
  can query.

The module rationale explicitly states that the deliverable for
the compliance-mapping exercise is "a spreadsheet/database that
audit can query"; that is the form the learner should be working
toward, with GDPR as the chosen frame.

## 2. Worked answer

The worked mapping artifact is a table where each row is a GDPR
obligation that affects the ML platform. Suggested columns:

| Column | Meaning |
| --- | --- |
| `obligation_id` | Stable id (e.g., `gdpr-art-5-1-a`) |
| `obligation_text` | Short paraphrase, with a link to the source |
| `applies_to` | Which platform component(s) the obligation hits |
| `control_owner` | The team accountable for the control |
| `implementation_pattern` | The reusable pattern that satisfies it |
| `evidence_source` | Where audit can pull the evidence |
| `review_cadence` | How often the mapping row is re-validated |

A passing submission populates this table for the **GDPR
obligations that have direct architectural impact on an AI
platform**. The architect-tier categories the learner should
recognize as in-scope:

- **Lawful basis & purpose limitation** — the platform must be
  able to attest which dataset / model / endpoint is operating
  under which lawful basis.
- **Data subject rights (access, rectification, erasure,
  portability, objection)** — the platform needs an inventory
  that can answer "where does subject X's data live, including
  in training data, embeddings, and prompt logs."
- **Data Protection Impact Assessment (DPIA)** — required for
  high-risk processing; the architect calls out which ML
  surfaces are presumptively high-risk (e.g., profiling,
  automated decision-making).
- **Cross-border data transfers** — region pinning for training
  data, model artifacts, embeddings, and prompt logs; transfer
  mechanism (e.g., Standard Contractual Clauses) recorded per
  data flow.
- **Records of processing activities (ROPA)** — the ML platform
  must surface its processing activities into the ROPA, not
  maintain a parallel one.
- **Breach notification readiness** — incident response
  governance hooks into the GDPR 72-hour notification window.

### Decision rationale

The module-level solution flags two failure modes that apply
directly here: *"compliance mapping that's checkbox theater"* and
*"standards without enforcement."* The GDPR mapping needs to be
operable, not aspirational:

- Each row must point at an **enforceable** implementation
  pattern (admission control, pipeline guardrail, automated
  data-lineage capture) rather than a policy document.
- The mapping should be versioned and treated as code — diffs
  show when scope changes (new data class, new region, new
  processor).
- The control owner column forces accountability. A row without
  an owner is an unmet obligation.

### What stays out of scope

The architect-tier answer **does not** invent specific GDPR
fine amounts, regulator interpretations, or case law. Where the
learner needs that level of detail, they should defer to legal
counsel and the EDPB / national DPA guidance.

## Implementation

Implementation follows the mapping artifact in section 2. The
architect's build steps are:

1. **Author the mapping as code** — store the table as CSV /
   YAML / database rows in a versioned repository so diffs
   surface scope changes (new data class, new region, new
   processor).
2. **Wire data-subject rights** — instrument lineage capture
   across training data, embeddings, prompt logs, and caches so
   the platform can answer "where does subject X appear" and
   execute erasure across derived data, not just the user table.
3. **Plumb DPIA gates** — flag high-risk ML surfaces
   (profiling, automated decision-making, large-scale
   processing) so the security-review process triggers a DPIA
   before launch.
4. **Encode transfer mechanism per data flow** — capture region
   pinning and the contractual mechanism (e.g., Standard
   Contractual Clauses) alongside each data flow, not as a
   single global statement.
5. **Feed ROPA** — emit the mapping into the organization's
   Records of Processing Activities rather than maintaining a
   parallel artifact.
6. **Hook breach notification** — wire the incident-response
   runbook so the 72-hour notification clock starts the moment a
   breach is declared.

## 3. Validation steps

1. Spot-check three rows for completeness. Each must have all
   seven columns populated; missing `control_owner` or
   `evidence_source` is a fail.
2. Trace one data subject rights obligation end-to-end. Confirm
   the architecture can answer the underlying question (e.g.,
   "where does subject X appear in training data?") rather than
   asserting it can.
3. Confirm the mapping covers cross-border data flow for at
   least one ML-specific artifact (e.g., embeddings, model
   weights, prompt logs), not just user PII.
4. Confirm the mapping is **machine-readable** (CSV, YAML, DB
   table) — a Word document with the same content is a fail by
   the module rationale.
5. Confirm the mapping is referenced from, or feeds into, the
   organization's **ROPA**, rather than living in isolation.

## 4. Rubric or review checklist

| Area | Pass criterion | Fail signal |
| --- | --- | --- |
| Scope | Covers training data, embeddings, prompt logs, model artifacts | Treats GDPR scope as "the user PII table" only |
| Control ownership | Every row has a named accountable team | Owners default to "Security" for everything |
| Implementation pattern | Points to an enforceable mechanism | Points to a policy document only |
| Evidence | Audit can pull evidence without engineer intervention | Evidence is "screenshot on request" |
| DPIA hooks | High-risk ML surfaces flagged for DPIA | DPIA treated as a one-time form |
| Transfers | Per-flow transfer mechanism recorded | Single global statement about region |
| Format | Machine-readable, versioned | Static document, no diff history |
| Integration with ROPA | Mapping feeds the ROPA | Parallel artifact maintained by hand |

## 5. Common mistakes

Drawn from the module-level "common mistakes graders see"
section, mapped to the GDPR frame:

1. **Checkbox-theater mapping.** Rows assert compliance without
   pointing at how the control is enforced or where evidence
   lives.
2. **Standards without enforcement.** Stating "we honor erasure
   requests" without showing the data-lineage and pipeline
   guardrails that make erasure actually achievable across
   training data, embeddings, and caches.
3. **One-shot mapping.** Built once for an audit and never
   re-derived when new data sources or model surfaces are
   added.
4. **PII-only scope.** Treating GDPR as something that only
   touches the user table, ignoring that training data,
   fine-tuning data, embeddings, and prompt logs may carry
   personal data.

## 6. References

- NIST AI Risk Management Framework (AI RMF 1.0) — for the
  Govern / Map / Measure / Manage framing the mapping sits
  inside — <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST AI 600-1, Generative AI Profile — for generative-AI
  specific risks the GDPR mapping must cover —
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- OWASP Machine Learning Security Top 10 — adversary catalogue
  used when scoping DPIA risk for ML surfaces —
  <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS — <https://atlas.mitre.org/>
- VeriSwarm Trust Center (example of an externally published
  compliance posture) — <https://veriswarm.ai/trust>
- Module-level rationale: `../SOLUTION.md`
