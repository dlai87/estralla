# SOLUTION — Exercise 4: SOC 2 Application

> Pairs with
> `ai-infra-architect-learning/lessons/mod-303-security-compliance/exercises/exercise-4.md`.
> Factored from the module-level `SOLUTION.md` in this directory's parent.

## 1. Solution overview

This exercise applies the module solution's **compliance-mapping**
and **security-review process** deliverables to **SOC 2** as the
chosen compliance frame. The architect-tier answer covers two
linked artifacts:

1. A **Trust Services Criteria (TSC) mapping** for the AI/ML
   platform — which TSC criteria are in audit scope, what
   implementation pattern satisfies them, and where the
   continuous evidence lives.
2. A **security-review process** that produces the operating
   evidence the SOC 2 audit will sample.

The module rationale explicitly recommends moving to *continuous
compliance* (e.g., Drata / Vanta) when going beyond a baseline
SOC 2 posture. The architect-tier point is that SOC 2 attestation
is a side-effect of a working control program, not a separate
workstream.

## 2. Worked answer

### Trust Services Criteria scope

SOC 2 organizes around the **Trust Services Criteria** published
by the AICPA: Security (required common criteria), Availability,
Processing Integrity, Confidentiality, and Privacy. The
architect's first decision is which criteria are in scope. For an
AI/ML platform, a defensible scoping is typically:

- **Security (common criteria, required).**
- **Availability** — included when the platform offers an
  inference SLA.
- **Confidentiality** — included when customer model artifacts,
  fine-tuning data, or embeddings are held.
- **Processing Integrity** — included when the platform's
  inference output is consumed directly by customer business
  processes.
- **Privacy** — included when the platform processes personal
  data on the customer's behalf; often deferred when GDPR /
  HIPAA mappings already cover the same surface.

Scoping decisions and their rationale must be written down — the
module rationale calls out *"compliance scope creep"* as a
recurring problem.

### Mapping artifact

Same column structure as the GDPR and HIPAA mappings:

| Column | Meaning |
| --- | --- |
| `tsc_id` | Stable TSC criterion id (e.g., `CC6.1`) |
| `criterion_text` | Short paraphrase + link to AICPA source |
| `applies_to` | Platform component(s) the criterion hits |
| `control_owner` | Team accountable for the control |
| `implementation_pattern` | Reusable enforcement pattern |
| `evidence_source` | Where audit can pull evidence |
| `sampling_population` | What the auditor would sample over |
| `review_cadence` | How often the row is re-validated |

ML-specific implementation patterns the learner should populate:

- **CC6 (Logical and Physical Access)** — workload identity for
  model-serving components, brokered access to model
  registries, evidence pulled from the identity provider.
- **CC7 (System Operations)** — change-management evidence for
  model artifact promotion (training → staging → production);
  monitoring evidence for inference endpoints; incident
  evidence from the IR process.
- **CC8 (Change Management)** — model release process treated
  as change management. Training-pipeline reproducibility
  evidence (dataset, code, config hashes) lives here.
- **A1 (Availability)** — inference-endpoint SLO evidence;
  capacity / DR posture from the HA/DR module.
- **C1 (Confidentiality)** — encryption baselines from the
  security architecture; access controls on customer
  embeddings and fine-tuned model artifacts.
- **PI1 (Processing Integrity)** — input validation on
  inference requests; output sanity checks where the
  contract states it.

### Security-review process

The same artifact closes the loop on the **security-review
process** deliverable from the module rationale:

- **When review is required** — new external integration, new
  data class, new compliance scope, new model architecture
  class, new third-party model provider.
- **Who reviews** — a named security architect plus a domain
  reviewer (data, ML, infra). Avoid "security reviews
  everything" as the only path.
- **Depth-to-risk mapping** — low / medium / high risk classes
  with corresponding review depth. Risk classification
  references OWASP ML Top 10 and MITRE ATLAS to keep AI-
  specific threats represented.
- **Service-level expectation** — published turnaround targets
  so engineering can plan around the process.

### Decision rationale

The module rationale identifies two failure modes that bear
directly on a SOC 2 program:

- *"Compliance mapping that's checkbox theater"* — the mapping
  must point at evidence that exists *as a side-effect of how
  the platform operates*, not at evidence that someone produces
  for the auditor.
- *"Standards without enforcement (admission control)"* — every
  control whose evidence is "engineer attests" should be
  pushed toward automated admission control or guardrail
  enforcement.

The continuous-compliance direction (Drata / Vanta) named in the
module rationale is the natural endpoint of these two principles.

### What stays out of scope

The architect-tier answer does not predict audit outcomes,
auditor opinions, or specific exception language. Scope of audit,
selection of auditor, and report distribution are management
decisions.

## Implementation

Implementation builds the two artifacts from section 2 into the
day-to-day operation of the platform:

1. **Publish the scoping decision** — a dated, written record
   naming which Trust Services Criteria are in scope and which
   are excluded, with rationale.
2. **Author the TSC mapping as code** — versioned,
   machine-readable, ingestible by a continuous-compliance
   platform (Drata, Vanta, or equivalent) so auditor sampling
   pulls directly from operating evidence.
3. **Wire change management for model artifacts** — model
   promotion (training → staging → production) flows through
   the same change-management surface as code, with
   reproducibility evidence (dataset, code, config hashes)
   attached.
4. **Stand up the security-review process** — published
   triggers, named reviewers, depth-to-risk mapping anchored to
   OWASP ML Top 10 / MITRE ATLAS, and a published service-level
   expectation for turnaround.
5. **Automate evidence collection** — every mapping row whose
   evidence is "engineer attests" is rewritten so the evidence
   is emitted by the platform (identity provider,
   change-management tool, monitoring stack) without engineer
   intervention.
6. **Treat exceptions as first-class** — exceptions to a control
   carry an owner, an expiry, and a compensating control; an
   open-ended exception is itself a violation.

## 3. Validation steps

1. Confirm a written, dated **scoping decision** that names
   which TSC are in scope and which are excluded, with reasons.
2. Spot-check three mapping rows for evidence quality: pull
   the evidence source and verify it can be retrieved without
   engineer intervention.
3. Confirm change-management evidence covers model-artifact
   promotion (CC8), not just code deploys.
4. Confirm the security-review process has a written depth-to-
   risk mapping with explicit AI/ML risk categories drawn from
   OWASP ML Top 10 / MITRE ATLAS.
5. Confirm the mapping is **machine-readable** and versioned;
   the module rationale insists the deliverable is something
   audit can query.

## 4. Rubric or review checklist

| Area | Pass criterion | Fail signal |
| --- | --- | --- |
| TSC scoping | Written scoping with named in/out criteria and rationale | Implied scope, no rationale |
| Common Criteria coverage | CC1-CC9 each mapped, with ML-specific patterns | CC mapped but ML surfaces excluded |
| Evidence quality | Evidence pulled automatically; auditor can sample | "On request" evidence only |
| Change management | Model promotion treated as change management | Only code deploys covered |
| AI/ML risk in review | Review depth uses OWASP ML Top 10 / MITRE ATLAS | Generic risk classes |
| Service level | Published review SLAs | Review timeline unclear |
| Format | Machine-readable, versioned | Static document |
| Continuous-compliance path | Mapping ingestible by a continuous-compliance platform | Mapping is human-readable only |

## 5. Common mistakes

Drawn from the module-level "common mistakes" section, applied
to SOC 2:

1. **Checkbox theater.** Mapping rows claim control coverage
   that is not enforced or evidenced as a side-effect of normal
   operations.
2. **Standards without enforcement.** Controls written as
   policy but not realized via admission control or pipeline
   guardrails — the module rationale calls this out
   specifically.
3. **Scope creep.** Adding TSC criteria without a written
   scoping decision; the module rationale identifies this as a
   recurring problem.
4. **Model artifacts excluded from change management.** Code
   change is governed, model release is not.
5. **AI/ML threats absent from risk model.** The security-
   review process uses only generic risk classes; OWASP ML Top
   10 and MITRE ATLAS are not referenced.

## 6. References

- NIST AI Risk Management Framework (AI RMF 1.0) —
  <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST AI 600-1, Generative AI Profile —
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- OWASP Machine Learning Security Top 10 —
  <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS — <https://atlas.mitre.org/>
- VeriSwarm Trust Center (example of an externally published
  SOC 2-style trust posture) —
  <https://veriswarm.ai/trust>
- Module-level rationale: `../SOLUTION.md`
