# SOLUTION — Exercise 5: Data Governance Application

> Pairs with
> `ai-infra-architect-learning/lessons/mod-303-security-compliance/exercises/exercise-5.md`.
> Factored from the module-level `SOLUTION.md` in this directory's parent.

## 1. Solution overview

This exercise applies the module solution's **standards
document** and **threat-modeling template** deliverables to a
**data governance** frame. The architect-tier answer is a small
set of linked artifacts:

1. A **data classification framework** that covers the AI/ML
   data classes (training, fine-tuning, eval, embeddings, prompt
   / response logs, model artifacts).
2. A **data-governance standards document** that says, for each
   class, what engineering teams **must do** (retention, access,
   movement, lineage, deletion), and that is enforced through
   admission control rather than left as policy.
3. A **threat-modeling template** that surfaces governance-
   relevant ML threats so the standards stay current.

The module rationale puts it directly: the standards document
tells engineering *what* they must do, references implementation
patterns, is versioned, and records exceptions. That framing is
the spine of this exercise.

## 2. Worked answer

### Data classification framework

A passing classification framework explicitly addresses AI/ML
data classes that engineer-tier classification schemes
frequently miss:

| Class | Examples | Governance treatment |
| --- | --- | --- |
| `training-data` | Curated datasets used to train base or fine-tuned models | Lineage to source, lawful basis recorded, retention bounded, deletion fan-out defined |
| `eval-data` | Benchmarks, golden sets | Lineage + license; isolated from training data |
| `fine-tuning-data` | Customer or domain-specific data used for tuning | Treated at the highest classification of any source row |
| `embeddings` | Vector representations derived from any of the above | Inherits classification of source; treated as re-identifying by default |
| `prompt-and-response-logs` | Captured inputs / outputs from inference endpoints | Classified by what could plausibly appear (often: same as training-data) |
| `model-artifacts` | Weights, adapters, checkpoints | Access scope, signing, and provenance tracked |

Each class is mapped to:

- **Retention policy** — bounded, with a default.
- **Access policy** — workload + human identity, brokered.
- **Movement policy** — what crossings of trust boundaries are
  allowed, under what controls.
- **Deletion policy** — the deletion fan-out (e.g., deleting a
  training row reaches embeddings, caches, and any model
  trained on it that is still in scope for retraining).

### Standards document

Per the module rationale, the standards document tells
engineering teams *what they must do*. For data governance, the
mandatory standards the learner is expected to write include:

- **No long-lived credentials** for data-store access.
- **All datasets registered** in a data catalog with lineage,
  classification, owner, and lawful basis.
- **All images / artifacts signed** (including model artifacts).
- **Default-deny network posture** at trust boundaries.
- **All deletions fan out** through the dataset → derived-data
  graph; no silent orphaning.
- **Exceptions are recorded** with an expiry date.

Each standard cites the **implementation pattern** that an
engineer can adopt to satisfy it (catalog tool, signing tool,
policy engine, etc.) — the module rationale calls out
*"standards without enforcement (admission control)"* as a
failure mode, so the standards must be enforceable via tooling
rather than honor system.

### Threat-modeling template

The threat-modeling template (the fifth module deliverable)
plugs in here:

- Default frame is **STRIDE / LINDDUN** with ML-specific
  extensions explicitly called out in the module rationale:
  **training-data poisoning, model inversion, prompt
  injection**.
- Threat enumeration draws ML adversary techniques from
  **OWASP Machine Learning Security Top 10** and **MITRE
  ATLAS** so the template is anchored to recognized
  catalogues.
- The template is **revisited** on a stated cadence; one-shot
  threat models are called out in the module rationale as a
  recurring failure mode.

### Decision rationale

Data governance is the bridge between the security architecture
(exercise 1) and the per-frame compliance mappings (exercises 2-4).
The architect-tier point is that the same classification +
standards + lineage substrate underlies GDPR data-subject rights,
HIPAA PHI handling, and SOC 2 confidentiality criteria — so it is
built **once** and re-used. The module rationale's "common
mistakes" list — security architecture as a product list,
checkbox mappings, unenforced standards, stale threat models —
all show up first in data governance when it is treated as a
policy document rather than as code.

## Implementation

Implementation produces the three artifacts from section 2 as
living tooling, not a binder:

1. **Encode the classification framework in the data catalog** —
   every dataset row carries `class`, `lineage`, `owner`,
   `lawful_basis`, and `retention`. Embeddings, prompt logs, and
   model artifacts are first-class classes in the catalog.
2. **Author the standards document as code** — versioned in a
   repository, each standard linked to the enforcement mechanism
   (admission controller, CI gate, policy engine) that makes it
   actually fail closed when violated.
3. **Wire deletion fan-out** — deleting a source row propagates
   through the dataset → embeddings → caches → retraining-
   pipeline graph; the design records exactly which derived
   artifacts are touched.
4. **Stand up the threat-modeling template** — STRIDE / LINDDUN
   with ML extensions (training-data poisoning, model
   inversion, prompt injection), anchored to OWASP ML Top 10
   and MITRE ATLAS, refreshed on a published cadence.
5. **Establish an exception register** — every exception to a
   standard has a recorded owner, expiry date, and link to the
   compensating control. The register is reviewed at the same
   cadence as the threat model.
6. **Re-use across compliance frames** — the same
   classification + lineage + standards substrate is what the
   GDPR (exercise 2), HIPAA (exercise 3), and SOC 2 (exercise
   4) mappings draw from; they do not maintain parallel
   artifacts.

## 3. Validation steps

1. Confirm the classification framework includes embeddings,
   prompt logs, and model artifacts as distinct classes; if any
   of these collapses into "internal data," that is a fail.
2. Pick a dataset. Confirm the catalog shows lineage,
   classification, owner, lawful basis, retention, and the
   downstream artifacts (embeddings, models) derived from it.
3. Trigger a deletion fan-out from a single training row in the
   reference design. Confirm the design specifies which
   downstream caches, embeddings, and retraining pipelines must
   honor it.
4. Pick any standard from the standards document. Confirm the
   document points at an **enforcement mechanism** (admission
   controller, CI gate, policy engine) and not at a policy URL.
5. Confirm the threat-modeling template references OWASP ML Top
   10 and MITRE ATLAS, and includes the three ML-specific
   extensions called out in the module rationale: training-data
   poisoning, model inversion, prompt injection.
6. Confirm exceptions are tracked with owners and expiry; an
   exception register without expiry is a fail.

## 4. Rubric or review checklist

| Area | Pass criterion | Fail signal |
| --- | --- | --- |
| Classification | ML data classes explicit (embeddings, prompt logs, model artifacts) | "PII / non-PII" only |
| Catalog | Lineage, owner, lawful basis, retention all populated | Catalog rows missing owner or lineage |
| Deletion fan-out | Design specifies downstream propagation | Deletion of source row leaves derived data intact |
| Standards format | Versioned, with referenced implementation patterns | Static policy document |
| Enforcement | Standards enforced via admission control / CI gates | Honor-system standards |
| Exceptions | Tracked with owner + expiry | Open-ended exceptions |
| Threat model | STRIDE / LINDDUN + ML extensions, anchored to OWASP ML Top 10 / MITRE ATLAS | Generic threat list, no ML extensions |
| Cross-frame reuse | Governance substrate visibly reused by GDPR / HIPAA / SOC 2 mappings | Parallel artifacts per compliance frame |

## 5. Common mistakes

Drawn directly from the module rationale's "common mistakes":

1. **Security architecture as a product list.** The data
   governance design defaults to naming tools instead of stating
   what each class must do.
2. **Checkbox-theater mapping.** Classification rows exist but
   point at no enforcement and feed no audit query.
3. **Standards without enforcement (admission control).** The
   standards document reads aspirationally; nothing fails CI
   when a standard is violated.
4. **Threat models done once, never updated.** STRIDE / LINDDUN
   template exists, but no cadence and no integration into the
   security review process.

## 6. References

- NIST AI Risk Management Framework (AI RMF 1.0) —
  <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST AI 600-1, Generative AI Profile —
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- OWASP Machine Learning Security Top 10 —
  <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS — <https://atlas.mitre.org/>
- VeriSwarm Trust Center (example practitioner data-governance
  posture) — <https://veriswarm.ai/trust>
- Module-level rationale: `../SOLUTION.md`
