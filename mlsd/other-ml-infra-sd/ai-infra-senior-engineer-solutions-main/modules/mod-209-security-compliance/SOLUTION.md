# SOLUTION — Security and Compliance

> Read this *after* you have implemented the reference security
> controls. This document explains *why* the security architecture
> is what it is and which compliance frames matter for ML.

## What this module is really teaching

Security for ML infrastructure is **almost** the same as security
for any infrastructure, but the ML-specific parts (data handling,
model artifacts, GPU clusters, supply chains) deserve explicit
attention. The reference solutions treat ML security as
"infrastructure security + a few important specializations."

## Architectural decisions and *why*

### Decision 1: No long-lived credentials anywhere

The reference uses short-lived credentials throughout: IAM Roles
for Service Accounts (IRSA / Workload Identity), Vault dynamic
secrets, sigstore / cosign for artifact signing. The reason:
long-lived credentials are the most common cause of cloud
breaches. Their absence is structural, not procedural.

### Decision 2: Supply-chain security via SLSA + cosign

Every container image is signed at build time (cosign), with
provenance attestations (SLSA L2-3). Admission control verifies
signatures at deploy time. The reason: typosquatting and supply-
chain attacks are real. Signature verification makes them
impossible at the deploy boundary.

### Decision 3: Network-as-code with default-deny

NetworkPolicies default to deny-all; only explicit allows let
traffic through. The reason: default-allow networks let
lateral-movement attacks succeed; default-deny forces every
connection to be intentional.

### Decision 4: Secrets via Vault / Secret Manager, never env vars

Kubernetes secrets are base64-encoded, not encrypted. The
reference uses External Secrets Operator pulling from HashiCorp
Vault (or cloud secret managers) so secrets are decrypted only
at pod creation time and rotate on a schedule.

### Decision 5: ML-specific: data classification + training-set lineage

The reference's ML-specific controls:
- Training data classified (PII / non-PII) and quarantined
  appropriately.
- Lineage tracks which model was trained on which data.
- Model artifacts tagged with their data sensitivity.
- Inference requests with PII inputs flagged for special
  handling.

These come from regulatory frames (GDPR, HIPAA, EU AI Act) that
care about training-data provenance specifically.

### Decision 6: Compliance gates in CI, not just post-deploy audit

Compliance checks (CIS benchmarks, NIST controls, custom
policies) run in CI against IaC and Helm charts. The reason:
catching a violation in CI is minutes of fix; catching it
post-deploy in audit is weeks of remediation.

## Trade-offs we deliberately accepted

### Vault as a hard dependency

Vault is operationally heavy. The reference treats this as worth
the cost; small teams sometimes prefer cloud-native secret
managers (AWS Secrets Manager, GCP Secret Manager) which lose
multi-cloud parity.

### Cosign / Sigstore as the signing default

Notary v2 is the alternative; cosign has gentler ergonomics and
better Kubernetes integration. The space is consolidating around
sigstore.

### Compliance-as-code adds CI time

Adding Checkov, tfsec, Kyverno-test, OPA-test, conftest, etc.
adds 30-90 seconds to every PR. The reference accepts this cost.

## Common mistakes graders see

1. **Hardcoded API keys in code**: still the #1 cloud breach
   cause.
2. **Kubernetes RBAC with cluster-admin role**: every service
   account is admin. Apply least-privilege.
3. **Security groups with 0.0.0.0/0**: works once, becomes a
   CVE.
4. **No data classification at ingestion**: PII flows
   downstream undetected.
5. **SLSA L0 (no provenance) in production**: supply-chain
   attacks succeed silently.
6. **Compliance audit only at year-end**: drift accumulates;
   findings are unfixable in the time window.

## When to go beyond this implementation

- Adopt **service mesh mTLS** (Istio, Linkerd) for pod-to-pod
  encryption.
- Move to **confidential computing** (Nitro Enclaves, SGX) for
  workloads with strict data-sensitivity requirements.
- Implement **continuous compliance** (Drata, Vanta) for SOC 2 /
  ISO / HIPAA frames.

## Related curriculum touchpoints

- ``engineer/mod-104-kubernetes`` — Kubernetes-native security
  primitives.
- ``architect/projects/project-305-security-framework`` —
  enterprise-architecture-level companion.
- ``ml-platform/mod-009-security-governance`` — platform-
  layer governance.
