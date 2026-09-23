# SOLUTION — Exercise 3: HIPAA Application

> Pairs with
> `ai-infra-architect-learning/lessons/mod-303-security-compliance/exercises/exercise-3.md`.
> Factored from the module-level `SOLUTION.md` in this directory's parent.

## 1. Solution overview

This exercise applies the **compliance-mapping** deliverable from
the module solution to **HIPAA** as the chosen compliance frame.
The architect-tier answer is a mapping artifact that:

- Distinguishes the **Security Rule** (administrative, physical,
  technical safeguards) from the **Privacy Rule** (uses,
  disclosures, minimum necessary) and the **Breach
  Notification Rule**.
- Names where each safeguard lives in the AI/ML platform.
- Treats the platform as a *Business Associate* of the covered
  entity unless the org is itself a covered entity, and reflects
  that in BAA scope.

HIPAA-relevant ML surfaces are deliberately enumerated, because
the failure mode the module rationale calls out — *"compliance
mapping that's checkbox theater"* — is especially common with
HIPAA in AI contexts.

## 2. Worked answer

The architect-tier worked answer is a mapping artifact that, for
the AI/ML platform under design, fills out:

| Column | Meaning |
| --- | --- |
| `safeguard_id` | Stable id (e.g., `hipaa-security-tech-312-a-1`) |
| `safeguard_text` | Short paraphrase + link to source |
| `applies_to` | Platform component(s) the safeguard hits |
| `control_owner` | Team accountable for the control |
| `implementation_pattern` | Reusable enforcement pattern |
| `evidence_source` | Where audit can pull evidence |
| `phi_data_class` | Which PHI data class is in scope |
| `review_cadence` | How often the row is re-validated |

The rows the learner is expected to populate, grouped by HIPAA
section, are conceptually:

- **Administrative safeguards** — workforce access controls,
  workforce training, audit / monitoring program, contingency
  planning, incident response that ties into the breach
  notification clock.
- **Physical safeguards** — facility / device controls
  delegated to the chosen cloud provider via a signed BAA;
  the platform records *which BAAs cover which workloads*.
- **Technical safeguards** — access control (unique user ID,
  emergency access, automatic logoff, encryption / decryption);
  audit controls (recording and examining activity in systems
  that contain PHI); integrity controls; transmission
  security.
- **Privacy Rule hooks** — minimum-necessary enforcement at
  query / inference time; controls on **use of PHI for model
  training** vs. **treatment / payment / operations**; de-
  identification standard (Safe Harbor or Expert
  Determination) made explicit when the platform claims data
  has been de-identified.
- **Breach Notification Rule hooks** — incident-response
  governance plugged into the 60-day notification window for
  covered entities and the BA-to-CE notification path.

### ML-specific surfaces the mapping must cover

- **Training data containing PHI** — lawful basis under HIPAA
  (typically requires authorization or a defined exception);
  de-identification pathway and the standard used.
- **Embeddings derived from PHI** — embeddings can be re-
  identifying; the mapping must treat them as PHI by default.
- **Prompt and response logs for clinical LLM use cases** —
  logged PHI gets the same safeguards as the source PHI.
- **Model artifacts** — possible memorization of PHI; controls
  on model artifact access and red-teaming for memorized PHI.

### Decision rationale

The module-level solution treats HIPAA as one of the named
compliance frames the architect chooses between. The architect's
job is to engineer toward the chosen frame, not to discover it at
audit time. The HIPAA-specific implication is that the platform
should:

- Treat all training, fine-tuning, eval, and prompt-log data
  containing PHI as subject to the full Security Rule unless an
  attested de-identification step has run.
- Make BAAs structural to the architecture (which subprocessors
  are under BAA, for which workloads) instead of a procurement
  artifact filed elsewhere.
- Treat embeddings and model weights as carrying PHI risk by
  default, because the module rationale calls out *one-shot
  threat models* as a recurring mistake.

### What stays out of scope

The architect-tier answer does not interpret specific HIPAA
provisions, fines, or OCR enforcement actions. It does not
substitute for the org's privacy officer or counsel.

## Implementation

Implementation follows the mapping artifact in section 2 and
lands as platform-level controls:

1. **Author the mapping as code** — versioned CSV / YAML /
   database rows; diffs show when new subprocessors, data
   classes, or workloads enter scope.
2. **Apply the technical safeguards** — unique workforce
   identity, automatic logoff, encryption at rest / in transit,
   audit logging on every system that contains PHI.
3. **Tag PHI through the pipeline** — propagate the
   `phi_data_class` tag through training data, fine-tuning
   data, embeddings, prompt / response logs, and model
   artifacts. Embeddings and model artifacts are treated as PHI
   by default unless an attested de-identification step has run.
4. **Codify the de-identification choice** — when the platform
   claims data has been de-identified, name the HIPAA standard
   used (Safe Harbor or Expert Determination) and record the
   attesting party.
5. **Make BAAs structural** — record BAA scope per subprocessor
   and workload in the same mapping artifact; deny inflow of
   PHI to workloads not under BAA.
6. **Enforce minimum necessary** — push minimum-necessary checks
   into query and inference admission control rather than
   relying on policy alone.
7. **Wire breach notification** — the incident-response runbook
   drives the 60-day covered-entity clock and the BA-to-CE
   notification path.

## 3. Validation steps

1. Pick any platform component handling PHI. Confirm the
   mapping names the safeguard rows, the control owner, and
   the evidence source.
2. Pick the training data pipeline. Confirm the mapping states
   whether PHI is processed under authorization, an exception,
   or a documented de-identification standard.
3. Confirm embeddings and prompt logs are treated as PHI by
   default in the mapping (not silently exempted).
4. Confirm the BAA structure is captured in the mapping:
   which subprocessors hold a BAA, scoped to which workloads.
5. Confirm the breach-notification clock is wired into the
   incident response runbook called out in the architecture.
6. Confirm the mapping is **machine-readable** and versioned;
   per the module rationale, the deliverable is something audit
   can query.

## 4. Rubric or review checklist

| Area | Pass criterion | Fail signal |
| --- | --- | --- |
| Rule coverage | Security, Privacy, Breach Notification each addressed | Only Security Rule technical safeguards |
| PHI inventory | Training data, embeddings, model artifacts, prompt logs each classified | "PHI lives in the EHR" — ML surfaces ignored |
| De-identification | Safe Harbor or Expert Determination explicitly stated | "We de-identify" with no standard named |
| BAA structure | BAA scope per subprocessor / workload | Single global statement about cloud BAA |
| Minimum necessary | Enforced at query / inference time | Asserted in policy only |
| Audit controls | Activity logs for PHI access exist and are reviewed | Logs exist but no review process |
| Breach clock | IR runbook references the notification window | Generic IR plan, no clock |
| Format | Machine-readable, versioned | Static document |

## 5. Common mistakes

Specialized from the module-level "common mistakes":

1. **Checkbox theater.** Asserting compliance with a safeguard
   without pointing at how it is enforced or evidenced for the
   ML platform specifically.
2. **De-identification by assertion.** Claiming data is "de-
   identified" without naming the HIPAA standard used (Safe
   Harbor or Expert Determination) and without an attested
   process.
3. **Embeddings exempted.** Treating embeddings or model
   activations as not-PHI by default — a known re-
   identification risk.
4. **Single-shot threat model.** No re-review when a new model,
   data source, or subprocessor enters scope. The module
   solution calls this out as a recurring failure mode.
5. **Policy-only minimum-necessary.** Stating the minimum-
   necessary principle in policy without enforcing it at query
   or inference time.

## 6. References

- NIST AI Risk Management Framework (AI RMF 1.0) —
  <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST AI 600-1, Generative AI Profile —
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- OWASP Machine Learning Security Top 10 —
  <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS — <https://atlas.mitre.org/>
- VeriSwarm Trust Center (example practitioner trust posture) —
  <https://veriswarm.ai/trust>
- Module-level rationale: `../SOLUTION.md`
