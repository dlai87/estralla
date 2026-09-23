# SOLUTION — Security and Compliance Framework

> Read this *after* attempting the learning-side project. This file
> explains the architectural reasoning behind the security framework
> and how it relates to the security-track projects.

## What an architect is being asked to defend

The brief lists capabilities — zero-trust, SOC 2 / HIPAA / ISO 27001
compliance, automated audit, encryption everywhere. The harder
architectural question is:

> How do you produce a security framework that an engineering org can
> *operate*, not just a security org can *demand*?

A framework that engineering perceives as friction will be routed
around. A framework that auditors perceive as theater will fail
certification. The reference design tries to land in the middle by
treating security as **policy-as-code with engineering ownership**,
not as gatekeeping.

## Key architectural decisions and *why*

### 1. Zero-trust via service mesh (Istio + SPIFFE), not VPN-based
network perimeter

Network-perimeter trust collapses at the cluster boundary. Service-mesh
mTLS keyed on workload identity gives you per-call authentication,
authorization, and audit. The mesh choice is Istio for the reasons
discussed in `ai-infra-security-solutions/project-1-zero-trust/SOLUTION.md`;
Cilium L7 policy is a credible substitute.

### 2. HashiCorp Vault as the secret-management substrate (not cloud
KMS-only)

Cloud KMS is excellent for cloud-native secrets but ties you to a
cloud. Vault gives you a portable abstraction with KV, database,
PKI, and SSH engines, and it integrates with cloud KMS for the actual
encryption operations. The design recommends Vault *with* KMS
backing, not Vault *instead of* KMS.

### 3. Encryption in use (confidential computing) only where it
materially changes the threat model

Confidential computing (Intel SGX, AMD SEV, Nitro Enclaves) is
operationally expensive and limits which workloads can run.
The architecture reserves it for the small set of cases where the
threat model includes "the cloud provider's privileged operators".
For most workloads, encryption at rest + in transit + strong IAM is
sufficient.

### 4. Policy-as-code (OPA / Kyverno) at *every* enforcement point

A policy that lives only in Confluence is not a policy. The reference
design encodes policies as OPA rego or Kyverno YAML at every
enforcement point: admission controllers, CI gates, runtime
guardrails. Policies are reviewed via Git, tested in CI, and audited
in the same way as application code.

### 5. Automated compliance reporting tied to the audit hash chain

The "85% audit-time reduction" claim is realistic *if* compliance
evidence is produced continuously, not generated when the auditor
arrives. The framework generates per-quarter evidence packs from the
hash chain (cross-ref project-2-compliance) and signs them at
generation, so post-hoc tampering is detectable.

### 6. Zero-trust for *humans* too (not just service-to-service)

Workforce access uses short-lived, workload-aware credentials
(Teleport, Boundary, or equivalent). SSH bastions and shared SA keys
are explicitly not part of the design. Most "breach" stories involve
long-lived human credentials; the framework treats human access as
the highest-risk path.

## How to read the deliverable

1. **`README.md`** — the executive narrative.
2. **`ARCHITECTURE.md`** — the engineering deliverable. Read the
   threat model section first; the rest of the design only makes
   sense in its light.
3. **Cross-references to `ai-infra-security-solutions/`** — that
   repository contains the implementation patterns this architecture
   builds on. Read those projects' `SOLUTION.md` files for the depth.

This project's deliverable is intentionally a *framework* — a set of
opinionated defaults and decision rationales — not a tool list.

## What's deliberately *not* in scope

- **No specific SOC 2 / HIPAA / ISO 27001 control mappings.** The
  architecture flags which controls each design element covers, but a
  real certification requires a control-by-control traceability matrix
  produced with your auditor.
- **No "zero security incidents" guarantee.** The figure in the brief
  is an aspirational outcome metric, not a deliverable. The
  architecture's job is to make incidents survivable and learnable,
  not impossible.
- **No insider-threat detection (UEBA).** A specialized domain; the
  framework points at where it slots in.
- **No physical security or supply-chain hardware controls.** Out of
  scope for this curriculum.

## Production gap checklist

- [ ] Control-by-control traceability matrix for each target
      certification, signed off by your auditor
- [ ] HSM-backed root of trust for signing identities
- [ ] Continuous-control monitoring (not just point-in-time scans)
- [ ] Insider-threat program with UEBA tooling
- [ ] Vendor / third-party risk assessment cadence
- [ ] Tested incident-response playbooks with cross-functional
      (legal, comms, exec) involvement
- [ ] Independent penetration test on a known cadence
- [ ] Customer-facing trust documentation (security whitepaper,
      SOC 2 report, audit summaries)

## Reading order across the curriculum

| Phase | Read this |
|---|---|
| Zero-trust patterns | `ai-infra-security-solutions/project-1-zero-trust/SOLUTION.md` |
| Compliance + audit chain | `ai-infra-security-solutions/project-2-compliance/SOLUTION.md` |
| Adversarial defense | `ai-infra-security-solutions/project-3-adversarial-defense/SOLUTION.md` |
| Secure CI/CD | `ai-infra-security-solutions/project-4-secure-cicd/SOLUTION.md` |
| Security operations | `ai-infra-security-solutions/project-5-security-operations/SOLUTION.md` |
| Implementation references | `ai-infra-engineer-solutions/mod-109` (Terraform / policy / GitOps) |

## Time budget for studying this solution

- **Executive read**: 2 hours.
- **Engineering read**: 3 days reading the architecture plus the
  five linked `SOLUTION.md` files in `ai-infra-security-solutions/`.
- **Adoption read**: 6–12 months — security frameworks are adopted
  in phases, with each phase certified before the next begins.
