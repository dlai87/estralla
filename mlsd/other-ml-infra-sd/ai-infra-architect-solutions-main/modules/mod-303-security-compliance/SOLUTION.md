# SOLUTION — Architect-Tier Security and Compliance

> Read this *after* you have designed the reference enterprise
> security architecture. This document explains the architect-
> tier security frame and acts as a high-level index for the
> per-exercise solutions in this directory.

## Per-exercise solutions

The rationale below is factored into per-exercise `SOLUTION.md`
files. Start here for orientation, then go to the exercise file
that matches the deliverable you are reviewing.

| Exercise | Topic | File |
| --- | --- | --- |
| Exercise 1 | Zero-Trust Application | [`exercise-1/SOLUTION.md`](exercise-1/SOLUTION.md) |
| Exercise 2 | GDPR Application | [`exercise-2/SOLUTION.md`](exercise-2/SOLUTION.md) |
| Exercise 3 | HIPAA Application | [`exercise-3/SOLUTION.md`](exercise-3/SOLUTION.md) |
| Exercise 4 | SOC 2 Application | [`exercise-4/SOLUTION.md`](exercise-4/SOLUTION.md) |
| Exercise 5 | Data Governance Application | [`exercise-5/SOLUTION.md`](exercise-5/SOLUTION.md) |

The legacy `exercise-01/` … `exercise-05/` directories remain as
pointer READMEs into the learning repository; the depth lives in
the new `exercise-1/` … `exercise-5/` directories above.

## What this module is really teaching

Engineer-tier security (senior-engineer/mod-209) is about
controls and implementations. Architect-tier security is about:
- Designing a security architecture that the org can sustain.
- Choosing a compliance frame (SOC 2 / ISO 27001 / HIPAA /
  FedRAMP / EU AI Act) and engineering toward it.
- Defining standards that the engineering org follows.
- Building security review processes that scale.

## What the deliverables should actually look like

Each bullet below is the spine of the matching per-exercise
file. The exercise file carries the worked example, validation
steps, rubric, and references.

### Security architecture document → exercise 1 (Zero-Trust)

The reference security architecture document covers:
- Trust boundaries.
- Identity and access management approach.
- Network segmentation strategy.
- Data classification framework.
- Encryption-at-rest / in-transit policies.
- Incident response governance.

### Compliance mapping → exercises 2-4 (GDPR, HIPAA, SOC 2)

Each requirement of the chosen compliance frame is mapped to a
control owner + implementation pattern. The deliverable is a
spreadsheet/database that audit can query. Exercises 2, 3, and
4 apply this same mapping discipline to GDPR, HIPAA, and SOC 2
respectively.

### Standards document → exercise 5 (Data Governance)

The standards document tells engineering teams *what* they must
do (no long-lived credentials, all images signed, etc.) and
references implementation patterns. Standards are versioned;
exceptions are recorded.

### Security review process → exercise 4 (SOC 2)

The review process defines:
- When security review is required (new external integration,
  new data class, new compliance scope).
- Who reviews.
- What review depth maps to which risk class.
- Service-level expectation for review turnaround.

### Threat modeling template → exercise 5 (Data Governance)

Reference threat models follow STRIDE / LINDDUN with ML-specific
extensions (training-data poisoning, model inversion, prompt
injection).

## Trade-offs we deliberately accepted

- Architect-tier security adds ceremony.
- Strict standards slow some engineering decisions.
- Compliance scope creep is a recurring issue.

## Common mistakes graders see

1. **Security architecture that's a list of products**, not a
   coherent design.
2. **Compliance mapping that's checkbox theater**.
3. **Standards without enforcement (admission control)**.
4. **Threat models done once, never updated**.

## When to go beyond this implementation

- Adopt **zero-trust architecture** as the unifying frame.
- Move to **continuous compliance** (Drata / Vanta).
- Add **EU AI Act** mapping for ML-heavy orgs serving the EU.

## Related curriculum touchpoints

- ``senior-engineer/mod-209-security-compliance`` — engineer
  view.
- ``architect/projects/project-305-security-framework`` — the
  user-facing project.
