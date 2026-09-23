# Compliance Requirements

This document is the authoritative compliance matrix for the Enterprise MLOps
Platform. It maps each in-scope regulatory framework to the controls the
platform implements, the evidence collected, the audit cadence, and the
accountable owner.

For the supporting governance processes (approval flows, audit procedures, data
governance), see siblings in this directory:
- [`./model-governance-framework.md`](./model-governance-framework.md)
- [`./audit-procedures.md`](./audit-procedures.md)
- [`./data-governance-policy.md`](./data-governance-policy.md)
- [`./compliance-requirements-mapping.md`](./compliance-requirements-mapping.md) (legacy mapping, retained for diff)

For the technical security architecture, see [ADR-007](../architecture/adrs/007-security-compliance-architecture.md).

## How to use this document

1. **For auditors** — start at the framework table for the engagement in
   progress (SOC 2, ISO 27001, GDPR, HIPAA, FedRAMP). Each control row points
   to the system of record where evidence is generated automatically.
2. **For engineers** — when changing a control, find the control ID in the
   relevant matrix and update the "evidence" column in the same PR. Failure to
   do so will block the change at the policy-as-code gate.
3. **For the GRC team** — the audit cadence column drives the annual evidence
   calendar. Re-validate dates each January.

## Shared responsibility

The platform sits on AWS. AWS owns the security _of_ the cloud (physical
infrastructure, hypervisor, managed-service operations); we own the security
_in_ the cloud (configuration, identity, data classification, application).
Each framework section below assumes AWS's relevant attestation (SOC 2, ISO
27001, HIPAA BAA, FedRAMP High for GovCloud) and only enumerates _our_
controls. AWS attestations are downloaded quarterly from AWS Artifact and
filed in `s3://mlops-audit-worm/aws-attestations/`.

---

## 1. SOC 2 Type II

**Scope**: All five Trust Services Criteria — Security, Availability,
Processing Integrity, Confidentiality, Privacy.

**Audit window**: 12 months (Jan 1 – Dec 31 each year). Type II report issued
by Feb 28 of the following year.

**Accountable owner**: VP Engineering (executive sponsor), Director of Platform
Engineering (operational owner), Security Compliance Manager (evidence).

**Auditor**: External CPA firm, currently A-LIGN. Pre-assessment in October.

### Control matrix

| Control ID | TSC | Description | Implementation | Evidence (automatic) | Audit cadence |
|---|---|---|---|---|---|
| CC6.1 | Security | Logical access controls | Okta SSO + Kubernetes RBAC + IRSA; no static AWS keys | Okta access logs, K8s audit log → OpenSearch | Continuous; sampled quarterly |
| CC6.2 | Security | New access provisioning | JIT via Okta group assignment, approved in ServiceNow | ServiceNow ticket + Okta `user.account.update` event | Per-change; quarterly review |
| CC6.3 | Security | Access removal on termination | Okta deprovision triggers K8s RBAC removal within 15min via reconciler | Reconciler audit log + Okta deactivation event | Monthly orphan-account scan |
| CC6.6 | Security | Network controls | VPC isolation, NACLs, Security Groups, NetworkPolicy default-deny | Terraform state + Cilium Hubble flow logs | Quarterly |
| CC6.7 | Security | Data-at-rest encryption | All S3 SSE-KMS, RDS KMS, EBS KMS using customer-managed keys | KMS key policy + Config rule `s3-bucket-server-side-encryption-enabled` | Continuous |
| CC6.8 | Security | Data-in-transit encryption | TLS 1.3 perimeter, Istio mTLS intra-cluster | Istio telemetry, ALB access logs | Continuous |
| CC7.1 | Security | Vulnerability management | Trivy scan in CI; Wiz runtime; SLA: critical 7d, high 30d | Trivy report in build artifact + Wiz dashboard export | Weekly scan, monthly review |
| CC7.2 | Security | Security incident detection | Falco runtime detection, GuardDuty, AWS Security Hub | Falco alerts → PagerDuty + Slack #sec-incident | Per-incident |
| CC7.3 | Security | Incident response | Runbook-driven, postmortem within 5 business days | Postmortem in `incidents/` repo, signed by IC | Per-incident |
| CC8.1 | Security | Change management | All prod changes via GitOps; Argo CD enforces signed commits | Git history + Argo CD sync events | Continuous; quarterly sample audit |
| A1.1 | Availability | Capacity planning | Quarterly capacity reviews; HPA + cluster autoscaler | Capacity review doc, K8s metrics dashboards | Quarterly |
| A1.2 | Availability | Backup & DR | RDS PITR 7d + manual snapshots 30d; S3 CRR to DR region | Backup status in AWS Backup console; quarterly DR drill report | Monthly backup verify; quarterly DR drill |
| A1.3 | Availability | SLO monitoring | 99.9% API SLO; multi-burn-rate alerting | Prometheus recording rules + monthly SLO report | Monthly |
| PI1.1 | Processing Integrity | Input validation | All Platform API inputs Pydantic-validated; OpenAPI strict | Schema in repo + API gateway 422 metrics | Continuous |
| PI1.5 | Processing Integrity | Model output validation | Schema validation on KServe response; drift alerts | KServe transformer logs + drift dashboard | Continuous |
| C1.1 | Confidentiality | Data classification | All S3 prefixes labeled `pii`, `phi`, `pci`, `public` | S3 tag policy + Config rule | Quarterly tag audit |
| C1.2 | Confidentiality | Data handling | DLP via Macie; egress block via VPC endpoints + SCP | Macie findings, VPC flow logs | Continuous |
| P1–P8 | Privacy | See GDPR section §3 | — | — | — |

### Evidence collection

Evidence is generated automatically wherever possible. The
`grc-evidence-collector` CronJob runs daily, pulls from Kubernetes, AWS, Okta,
and GitHub, and writes immutable evidence packages to
`s3://mlops-audit-worm/soc2/YYYY/MM/DD/` (Object Lock, 7-year retention).
Auditor access is read-only via a dedicated IAM role with `aws:MultiFactorAuthPresent` required.

Manual evidence (training records, policy acknowledgments) is stored in the
GRC system of record (Vanta) and synced nightly to the same bucket.

---

## 2. ISO/IEC 27001:2022

**Scope**: The Enterprise MLOps Platform and its supporting teams (Platform
Engineering, SRE, Security, Data Platform). The ISMS scope statement explicitly
includes data scientists' use of the platform but excludes their local
workstations.

**Certification cycle**: 3-year cycle — initial certification audit, then two
annual surveillance audits, then recertification.

**Accountable owner**: CISO (executive sponsor), ISMS Manager (operational
owner).

**Certification body**: Schellman.

### Annex A control implementation (selected — full SoA in Vanta)

| Control | Title | Implementation note | Evidence | Cadence |
|---|---|---|---|---|
| A.5.1 | Information security policies | Policies in `security-policies` repo, reviewed annually, acknowledged in Vanta | Vanta acknowledgment report | Annual |
| A.5.7 | Threat intelligence | Subscriptions to AWS Security Hub, GitHub Advisory DB; weekly digest to security team | Digest archive | Weekly |
| A.5.15 | Access control | Same as SOC 2 CC6.1 | See CC6.1 | Continuous |
| A.5.23 | Information security for cloud services | AWS shared-responsibility doc maintained; vendor reviews quarterly | Vendor review log | Quarterly |
| A.5.34 | Privacy and PII protection | Cross-reference GDPR + HIPAA sections | See §3, §4 | Continuous |
| A.6.3 | Awareness, education, training | Annual security training via KnowBe4; new-hire onboarding includes platform-specific module | KnowBe4 completion report | Annual + onboarding |
| A.8.1 | User endpoint devices | MDM (Jamf for Mac, Intune for Windows); compliance required for Okta SSO | Jamf/Intune compliance reports | Continuous |
| A.8.2 | Privileged access rights | Production access requires PR-merged JIT request via `tf-iam-jit` module, max 4h | JIT audit table in DynamoDB | Per-grant |
| A.8.5 | Secure authentication | WebAuthn required for admin roles; FIDO2 keys issued to all platform engineers | Okta authentication report | Continuous |
| A.8.7 | Protection against malware | EDR (CrowdStrike Falcon) on all workstations; container scanning (Trivy + Wiz Runtime) | EDR + scan reports | Continuous |
| A.8.8 | Management of technical vulnerabilities | See SOC 2 CC7.1 | See CC7.1 | Weekly |
| A.8.9 | Configuration management | Terraform + Helm; drift detection runs hourly | `tf-drift` Slack alerts | Hourly |
| A.8.16 | Monitoring activities | Centralized in Prometheus + Loki + Tempo + OpenSearch | Dashboards + alert history | Continuous |
| A.8.23 | Web filtering | Egress proxy for cluster nodes via Squid + allowlist | Proxy logs | Continuous |
| A.8.24 | Use of cryptography | KMS-only, no application-layer crypto without crypto-board review | KMS key inventory | Annual review |
| A.8.25 | Secure development lifecycle | SDLC policy mandates threat modeling for new services; semgrep + CodeQL in CI | Threat model docs in repo, scan results | Per-change |
| A.8.28 | Secure coding | Coding standards enforced via linters; security champions per team | Linter pass rate, champion roster | Continuous |
| A.8.34 | Protection of information systems during audit testing | Audit access via read-only role, no production write access | IAM policy doc | Per-engagement |

The Statement of Applicability (SoA), risk register, and treatment plan are
maintained in Vanta and reviewed by the ISMS committee monthly.

---

## 3. GDPR (Regulation EU 2016/679)

**Scope**: All personal data of EU/UK data subjects processed by the platform.
Concretely, this covers ML features and training datasets for the EU
customer-facing product lines: `risk`, `recommendations`, `support-routing`.

**Lawful bases used**: Contract (Art. 6(1)(b)) for service-essential processing;
Legitimate Interest (Art. 6(1)(f)) for fraud prevention with documented LIA;
Consent (Art. 6(1)(a)) for opt-in personalization features.

**Accountable owner**: Data Protection Officer (DPO), Privacy Counsel,
Director of Data Platform.

**Cross-border transfers**: EU data stored and processed exclusively in
`eu-west-1` (cluster `mlops-prod-eu`). SCCs in place with AWS. Transfer Impact
Assessment (TIA) on file for any model whose inference traffic crosses regions.

### Article-by-article control mapping

| Article | Requirement | Implementation | Evidence | Cadence |
|---|---|---|---|---|
| Art. 5 | Principles (lawfulness, minimization, accuracy, storage limitation) | Data classification + retention policy enforced via S3 lifecycle; feature minimization reviewed at feature registration | Data inventory, lifecycle config | Quarterly |
| Art. 6 | Lawful basis | LIA + ROPA maintained in OneTrust per processing activity | OneTrust export | Annual |
| Art. 13–14 | Information to data subjects | Privacy notice covers ML processing; updated at each material change | Public privacy notice version history | Per-change |
| Art. 15 | Right of access | DSAR pipeline: identity verification → automated extract via `dsar-extract` job → privacy-counsel review → 30-day SLA | DSAR ticket + extract artifact | Per-request |
| Art. 16 | Rectification | DSAR pipeline updates upstream source; feature recomputed within 24h | Same as Art. 15 | Per-request |
| Art. 17 | Erasure | `dsar-erase` job tombstones subject in Snowflake + S3 + Feast online + model retraining queue | Erasure proof artifact | Per-request |
| Art. 18 | Restriction | Quarantine flag in entity registry blocks new feature reads for the subject | Registry audit log | Per-request |
| Art. 20 | Portability | Same extract format as Art. 15 (JSON), machine-readable | Extract artifact | Per-request |
| Art. 22 | Automated decision-making | Inventory of solely-automated decisions; human-in-the-loop required for credit/fraud actions per ADR-010 | Decision inventory, approval policy | Quarterly review |
| Art. 25 | Privacy by design and default | Privacy review required for any new feature involving PII via OPA gate | OPA decision log | Per-change |
| Art. 28 | Processor obligations | DPAs in place with all sub-processors; vendor inventory in OneTrust | Vendor inventory | Annual |
| Art. 30 | ROPA | Maintained in OneTrust per processing activity | ROPA export | Annual + per-change |
| Art. 32 | Security of processing | Inherits SOC 2 + ISO controls | See §1, §2 | Continuous |
| Art. 33–34 | Breach notification | Incident runbook includes 72-hour notification path to DPO + supervisory authority | Incident records | Per-incident |
| Art. 35 | DPIA | Required for "high risk" processing; template in `privacy/dpia-template.md` | DPIA per applicable system | Per-applicable-system |

### Special category data (Art. 9)

The platform does not process special category data by default. If a use case
arises, it must go through a DPIA + explicit consent path before any
ingestion. Currently zero special-category datasets in production.

---

## 4. HIPAA (US 45 CFR Parts 160, 162, 164)

**Scope**: The platform is in scope when the `healthcare` team processes
Protected Health Information (PHI) for clinical decision-support models. AWS
BAA executed at the account level; a complementary BAA covers any third-party
ML tooling that touches PHI (currently: none — all PHI processing happens
on the platform).

**Accountable owner**: HIPAA Security Officer (CISO), HIPAA Privacy Officer
(General Counsel), Healthcare Product Lead.

**Hosting**: PHI workloads run in a dedicated tenant namespace `tenant-healthcare`
with stricter controls: dedicated KMS key, dedicated S3 prefix with bucket
policy denying any non-VPC access, dedicated node pool (no shared GPU with
non-PHI tenants).

### Safeguard mapping

#### Administrative safeguards (164.308)

| Safeguard | Implementation | Evidence | Cadence |
|---|---|---|---|
| 164.308(a)(1)(ii)(A) Risk Analysis | Annual HIPAA-specific risk analysis by external firm; mid-year self-assessment | Risk analysis report | Annual + mid-year |
| 164.308(a)(1)(ii)(B) Risk Management | Treatment plan tracked in Vanta with quarterly review | Vanta export | Quarterly |
| 164.308(a)(3) Workforce Security | Background checks for workforce with PHI access; access requires HIPAA training | HR + KnowBe4 records | Per-hire; annual training |
| 164.308(a)(4) Information Access Management | Minimum-necessary enforced via OPA policy on Platform API; PHI access requires explicit role | Access decisions logged | Continuous |
| 164.308(a)(5) Security Awareness Training | HIPAA module in KnowBe4 required for workforce with PHI access | Completion report | Annual |
| 164.308(a)(6) Security Incident Procedures | HIPAA-specific incident runbook; 60-day breach notification path | Incident records | Per-incident |
| 164.308(a)(7) Contingency Plan | DR plan + drill specific to healthcare tenant; tabletop annually | DR drill report | Annual |
| 164.308(b) Business Associate Contracts | BAAs with AWS + every sub-processor that may touch PHI | Vendor inventory | Per-vendor + annual |

#### Physical safeguards (164.310)

Inherited from AWS BAA. AWS attestation downloaded quarterly. We do not
operate physical infrastructure that touches PHI.

#### Technical safeguards (164.312)

| Safeguard | Implementation | Evidence | Cadence |
|---|---|---|---|
| 164.312(a) Access Control — unique user ID | Okta `sub` propagated end-to-end as `X-User-ID`; logged in audit trail | Audit log | Continuous |
| 164.312(a) Emergency access | Break-glass role `mlops-healthcare-breakglass`, requires two-person approval, auto-expires in 1h, logged | Break-glass log | Per-use |
| 164.312(a) Automatic logoff | JupyterHub session 8h max; API tokens 1h max | Session audit | Continuous |
| 164.312(a) Encryption + decryption | KMS-encrypted at rest and in transit | KMS + TLS audit | Continuous |
| 164.312(b) Audit Controls | Every PHI access logged to WORM S3; reviewed weekly | Audit log review record | Weekly |
| 164.312(c) Integrity | S3 Object Lock + KMS; SHA256 of artifacts in MLflow | Object Lock config | Continuous |
| 164.312(d) Person/entity authentication | MFA via WebAuthn required for PHI-tenant access | Okta MFA report | Continuous |
| 164.312(e) Transmission security | TLS 1.3 + Istio mTLS | mTLS coverage report | Continuous |

### Breach response

A suspected PHI breach triggers the HIPAA incident runbook in
[`../runbooks/troubleshooting.md`](../runbooks/troubleshooting.md) §scenario
"HIPAA-suspected access pattern". HIPAA Privacy Officer is paged within 1
hour. Notifications to affected individuals and HHS OCR follow the 60-day rule
(or 500+ individuals → media notice).

---

## 5. FedRAMP Moderate (planned — Year 3)

**Scope (planned)**: A separate platform instance in AWS GovCloud (US) for
public-sector workloads. Out of scope for the commercial platform.

**Status**: Not yet authorized. Year-3 roadmap item. This section is included
so engineering decisions today can be made with FedRAMP-compatibility in mind
(e.g., FIPS 140-3 validated crypto modules, US-person workforce for in-scope
operations).

**Accountable owner**: TBD — to be staffed in Q1 of Year 3.

**Authorization path**: Agency-sponsored ATO. Initial sponsor in discussion;
target P-ATO via JAB if scope expands.

### Gap analysis (high level vs current commercial posture)

| NIST 800-53 family | Status today | Gap to FedRAMP Moderate |
|---|---|---|
| AC — Access Control | Strong (Okta + RBAC + IRSA) | Need PIV/CAC support; need US-person enforcement for in-scope roles |
| AT — Awareness & Training | Annual KnowBe4 | Need FedRAMP-specific role-based training |
| AU — Audit & Accountability | OpenSearch + WORM 7y | Already meets; need formal log review process documented |
| CA — Assessment & Authorization | Annual SOC 2 | Need 3PAO assessment; SSP authoring |
| CM — Configuration Management | Terraform + GitOps | Need formal CCB and baseline configs documented |
| CP — Contingency Planning | RPO 15min / RTO 4h | Already meets; need formal Contingency Plan doc |
| IA — Identification & Authentication | MFA via WebAuthn | Need PIV/CAC for privileged users; FIPS 140-3 modules |
| IR — Incident Response | Runbook + on-call | Need US-CERT reporting integration |
| PE — Physical & Environmental | AWS-inherited | Need AWS GovCloud (P-ATO inheritance) |
| RA — Risk Assessment | Annual + mid-year | Already meets |
| SA — System & Services Acquisition | Vendor reviews | Need FedRAMP-authorized vendor preference |
| SC — System & Communications Protection | TLS 1.3 + mTLS | Need FIPS-validated cipher suites end-to-end |
| SI — System & Information Integrity | EDR + runtime + scanning | Already meets; need integrity monitoring formalized |

The cost-benefit will be re-evaluated in Q3 of Year 2 against pipeline of
public-sector demand. Decision logged in ADR-011 (to be drafted).

---

## Cross-framework control reuse

Many controls satisfy multiple frameworks. The matrix below shows the
"one-control-many-frameworks" mapping to avoid duplicated effort.

| Control | SOC 2 | ISO 27001 | GDPR | HIPAA | FedRAMP |
|---|---|---|---|---|---|
| Okta SSO + MFA | CC6.1 | A.5.15, A.8.5 | Art. 32 | 164.312(d) | IA-2 |
| KMS encryption at rest | CC6.7 | A.8.24 | Art. 32 | 164.312(a)(2)(iv) | SC-13, SC-28 |
| Istio mTLS in cluster | CC6.8 | A.8.24 | Art. 32 | 164.312(e) | SC-8 |
| GitOps + signed commits | CC8.1 | A.8.9, A.8.25 | Art. 32 | 164.312(c) | CM-2, CM-3 |
| WORM audit log | CC7.2 | A.8.16 | Art. 30 | 164.312(b) | AU-2, AU-9 |
| RDS Multi-AZ + S3 CRR | A1.2 | A.5.30 | Art. 32 | 164.308(a)(7) | CP-9, CP-10 |
| Trivy + Wiz vulnerability mgmt | CC7.1 | A.8.8 | Art. 32 | 164.308(a)(1)(ii)(B) | RA-5 |

## Audit calendar (annual)

| Month | Event | Owner |
|---|---|---|
| Jan | Set SOC 2 scope, kick off evidence collection for next window | GRC Manager |
| Feb | SOC 2 Type II report issued | Auditor |
| Mar | ISO 27001 surveillance audit prep | ISMS Manager |
| Apr | ISO 27001 surveillance audit | ISMS Manager + Certifier |
| May | HIPAA mid-year self-assessment | HIPAA Security Officer |
| Jun | DPIA refresh for any new EU products | DPO |
| Jul | DR drill (full failover) | SRE Lead |
| Aug | Penetration test (external, scoped) | Security Engineering |
| Sep | Annual HIPAA risk analysis (external firm) | HIPAA Security Officer |
| Oct | SOC 2 pre-assessment with auditor | GRC Manager |
| Nov | Annual policy review + workforce re-acknowledgment | ISMS Manager |
| Dec | Close out SOC 2 evidence window | GRC Manager |

## Open issues

- **FedRAMP**: Pending sponsorship and demand validation (Q3 Yr 2 decision).
- **EU AI Act**: High-risk AI system classification analysis underway for the
  fraud-detection and credit-scoring models. Implementation expected in Yr 2.
- **PCI DSS**: Not currently in scope. Will become in scope if the
  `payments` team migrates onto the platform — current target Yr 3.
