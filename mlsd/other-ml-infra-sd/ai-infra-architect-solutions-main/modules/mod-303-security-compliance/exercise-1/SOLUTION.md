# SOLUTION — Exercise 1: Zero-Trust Application

> Pairs with
> `ai-infra-architect-learning/lessons/mod-303-security-compliance/exercises/exercise-1.md`.
> Factored from the module-level `SOLUTION.md` in this directory's parent.

## 1. Solution overview

The architect-tier deliverable for this exercise is **a reference
zero-trust security architecture** for an AI/ML platform, not a
list of products. The learner should:

- Frame zero-trust as the unifying design principle for the
  platform, not as a vendor stack.
- Define the trust boundaries that the platform must defend
  (control plane, data plane, model registry, training data
  pipelines, inference endpoints, third-party integrations).
- Show that identity, network segmentation, data classification,
  and encryption policies are *consequences* of the trust model,
  not independent workstreams.
- Cover incident-response governance so the architecture is
  sustainable, not just designed once.

The module-level rationale is the spine of the answer; this file
turns that rationale into a worked example, validation steps, and
a grading rubric.

## 2. Worked answer

A passing zero-trust architecture document covers, at minimum,
the six elements called out by the module solution:

1. **Trust boundaries** — explicit boundary diagram. Each
   boundary names: what crosses it, what authenticates the
   crossing, and what is logged. ML-specific boundaries to call
   out: training-data ingress, model artifact promotion, prompt /
   response egress for hosted LLM endpoints.
2. **Identity and access management** — workload identity for
   every component (no long-lived shared credentials), short-
   lived tokens, brokered access to data stores. Human access is
   modeled the same way (SSO + short-lived role assumption).
3. **Network segmentation** — segmentation that aligns with the
   trust boundaries above. The document must state the default
   posture (deny) and the exception process.
4. **Data classification** — at least three tiers (e.g.,
   `public` / `internal` / `restricted`), and an ML-data tier
   that maps training data, fine-tuning data, eval data, and
   prompt logs to classifications.
5. **Encryption policy** — encryption-at-rest and in-transit
   baselines, key custody, and the rotation cadence the
   architecture commits to.
6. **Incident-response governance** — who declares an incident,
   who runs the response, and where the runbooks live. ML-
   specific incident classes worth naming: model exfiltration,
   training-data poisoning, prompt-injection-driven data
   exposure.

The architecture should explicitly map these elements back to
recognized frameworks:

- **NIST AI Risk Management Framework (AI RMF 1.0)** — used to
  frame the *Govern / Map / Measure / Manage* functions on top
  of the zero-trust controls.
- **NIST AI 600-1 (Generative AI Profile)** — used for any
  generative-AI surface (RAG endpoints, hosted LLM access,
  agent tooling).
- **OWASP Machine Learning Security Top 10** and **MITRE
  ATLAS** — used to enumerate the ML-specific adversary
  techniques the trust boundaries are defending against.

### Decision rationale

The module-level solution explicitly identifies *"adopt
zero-trust architecture as the unifying frame"* as the way to go
beyond a baseline compliance posture. The architect-tier point is
that zero-trust replaces perimeter assumptions with per-request
authentication and authorization — which is what lets identity,
segmentation, and data-classification choices line up into a
single design rather than five disconnected programs.

Trade-offs the learner should explicitly accept (these are also
called out in the module rationale):

- Adds ceremony to engineering workflows.
- Slows some engineering decisions because more access requires
  brokered identity and policy.
- Creates more telemetry and therefore more audit surface to
  maintain.

## Implementation

Implementation of this design lands in the platform as a layered
set of controls anchored to the trust boundary diagram described
in section 2:

1. **Identity layer** — wire workload identity (SPIFFE/SVID or
   cloud-native equivalents) onto every service. Bind short-lived
   tokens to data-store access. Federate human SSO with
   short-lived role assumption.
2. **Network layer** — encode segmentation as policy (service
   mesh authorization policies or network policies) that matches
   the boundary diagram, with a default-deny posture and a
   recorded exception / waiver process.
3. **Data layer** — emit the data classification framework into
   the catalog and enforce per-tier movement rules in pipeline
   tooling so crossings are evaluated, not just documented.
4. **Encryption layer** — codify at-rest and in-transit
   baselines in module / IaC defaults; record key custody,
   rotation cadence, and key-management owners.
5. **Incident-response layer** — publish runbooks for the
   ML-specific incident classes (model exfiltration, training-
   data poisoning, prompt-injection-driven exposure) and
   rehearse them on a stated cadence.

These layers are deliberately built so the operating evidence is
a side-effect of normal platform operation, not artifact work
created for an audit.

## 3. Validation steps

A grader can validate a learner's submission by walking these
checks:

1. Pick any component in the architecture diagram. Confirm the
   document states *which identity* it uses, *which boundary* it
   sits behind, and *which data classification* it can touch.
2. Pick any data flow that crosses a trust boundary. Confirm the
   document names the authentication mechanism, the
   authorization policy, and where the crossing is logged.
3. Confirm the document distinguishes workload identity from
   human identity and does not rely on long-lived shared
   credentials.
4. Confirm the document includes an exception / waiver process
   for the deny-by-default posture. A zero-trust design without
   an exception process is not operable.
5. Confirm the document references at least one official
   framework (NIST AI RMF or NIST AI 600-1) and at least one
   adversary catalogue (OWASP ML Top 10 or MITRE ATLAS) when
   discussing ML-specific threats.

## 4. Rubric or review checklist

| Area | Pass criterion | Fail signal |
| --- | --- | --- |
| Trust boundaries | Boundary diagram with named crossings | Generic "DMZ + internal" diagram |
| Identity | Workload + human identity, short-lived credentials | Shared service accounts, long-lived keys |
| Segmentation | Default-deny + exception process | Default-allow or no exception process |
| Data classification | Tiers explicitly cover ML data classes | Only "PII / non-PII" with no ML-data tier |
| Encryption | At-rest + in-transit baselines, key custody named | "We use TLS and KMS" with no policy |
| Incident response | Roles, declaration criteria, runbooks, ML incident classes | Generic IR plan with no ML-specific classes |
| Framework anchoring | Maps to NIST AI RMF / AI 600-1 + ML adversary catalogue | Architecture detached from any external frame |

## 5. Common mistakes

These are the recurring mistakes called out in the module-level
solution; they apply directly to a zero-trust submission:

1. **A list of products instead of a design.** A vendor
   inventory ("we use Okta + Cloudflare + Vault") is not an
   architecture.
2. **Standards without enforcement.** Stating that a zero-trust
   policy exists without describing the admission control that
   enforces it.
3. **One-shot design.** Zero-trust architecture that is never
   reviewed against new components, new data classes, or new
   integrations decays quickly.
4. **Compliance-mapping checkbox theater.** Mapping NIST AI RMF
   subcategories to controls without showing how the controls
   are actually implemented or evidenced.

## 6. References

- NIST AI Risk Management Framework (AI RMF 1.0) —
  <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST AI 600-1, Generative AI Profile —
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- OWASP Machine Learning Security Top 10 —
  <https://owasp.org/www-project-machine-learning-security-top-10/>
- MITRE ATLAS — <https://atlas.mitre.org/>
- VeriSwarm Trust Center (practitioner example of a published
  trust posture) — <https://veriswarm.ai/trust>
- Module-level rationale: `../SOLUTION.md`
