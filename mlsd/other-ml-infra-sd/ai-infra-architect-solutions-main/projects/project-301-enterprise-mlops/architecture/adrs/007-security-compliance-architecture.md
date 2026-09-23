# ADR-007: Security and Compliance Architecture

**Status**: Accepted
**Date**: 2024-10-19
**Decision Makers**: Principal Architect, Security Architect, Chief Compliance Officer, CTO
**Stakeholders**: Security Team, Compliance Team, ML Platform Team, Legal

## Context

ML platform must meet security and compliance requirements for:
- SOC2 Type II certification (customer requirement)
- HIPAA compliance (healthcare models)
- GDPR (EU data processing)
- Internal security policies (zero-trust, least-privilege)

### Security Requirements
- Encryption at rest and in transit
- Least-privilege access control
- Audit logging (7-year retention)
- Network segmentation
- Secret management
- Vulnerability management
- Incident response capability

### Compliance Requirements
- SOC2 CC6.1: Logical access controls
- SOC2 CC7.2: System monitoring
- HIPAA §164.308: Administrative safeguards
- HIPAA §164.312: Technical safeguards
- GDPR Article 32: Security of processing

## Decision

**Defense-in-Depth Security Architecture** with layered controls:

```
┌──────────────────────────────────────────────────────┐
│      Security Architecture (Defense-in-Depth)         │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Layer 1: Network Security                            │
│  ┌────────────────────────────────────────────┐     │
│  │ VPC Isolation                              │     │
│  │ - Private subnets (no internet access)     │     │
│  │ - NAT Gateway for egress                   │     │
│  │ - VPC Endpoints (S3, ECR, etc.)           │     │
│  │                                             │     │
│  │ Network Policies (Kubernetes)              │     │
│  │ - Default deny all                         │     │
│  │ - Explicit allow rules per namespace       │     │
│  │ - Pod-to-pod isolation                     │     │
│  │                                             │     │
│  │ Security Groups                            │     │
│  │ - Least-privilege rules                    │     │
│  │ - No 0.0.0.0/0 inbound (except ALB)       │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 2: Identity & Access                           │
│  ┌────────────────────────────────────────────┐     │
│  │ IAM Roles for Service Accounts (IRSA)     │     │
│  │ - Pod-level IAM permissions                │     │
│  │ - No shared credentials                    │     │
│  │ - Automatic rotation                       │     │
│  │                                             │     │
│  │ RBAC (Kubernetes)                          │     │
│  │ - Namespace-scoped roles                   │     │
│  │ - Least-privilege principle                │     │
│  │ - Regular access reviews (quarterly)       │     │
│  │                                             │     │
│  │ SSO Integration (Okta)                     │     │
│  │ - MFA required                             │     │
│  │ - SAML for AWS/K8s access                 │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 3: Data Protection                             │
│  ┌────────────────────────────────────────────┐     │
│  │ Encryption at Rest                         │     │
│  │ - EBS volumes: KMS encryption              │     │
│  │ - S3: SSE-KMS (per-team keys)             │     │
│  │ - RDS: Encryption enabled                  │     │
│  │ - etcd: Encrypted by EKS                   │     │
│  │                                             │     │
│  │ Encryption in Transit                      │     │
│  │ - TLS 1.3 everywhere                       │     │
│  │ - Certificate management (cert-manager)    │     │
│  │ - mTLS for service-to-service (Istio)     │     │
│  │                                             │     │
│  │ Secrets Management                         │     │
│  │ - AWS Secrets Manager (rotation enabled)   │     │
│  │ - No secrets in code/config                │     │
│  │ - External Secrets Operator (K8s)         │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 4: Monitoring & Audit                          │
│  ┌────────────────────────────────────────────┐     │
│  │ Audit Logging                              │     │
│  │ - CloudTrail (all API calls)               │     │
│  │ - EKS audit logs (all K8s API)            │     │
│  │ - Application audit logs                   │     │
│  │ - 7-year retention (S3 Glacier)            │     │
│  │ - Immutable logs (WORM)                    │     │
│  │                                             │     │
│  │ Security Monitoring                        │     │
│  │ - GuardDuty (threat detection)             │     │
│  │ - Security Hub (compliance dashboard)      │     │
│  │ - Falco (runtime security, K8s)           │     │
│  │ - CloudWatch alarms (anomalies)            │     │
│  │                                             │     │
│  │ Vulnerability Scanning                     │     │
│  │ - ECR image scanning                       │     │
│  │ - Trivy (container scanning)               │     │
│  │ - Dependabot (dependency scanning)         │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
│  Layer 5: Compliance Controls                         │
│  ┌────────────────────────────────────────────┐     │
│  │ SOC2 Controls                              │     │
│  │ - CC6.1: Access control matrices           │     │
│  │ - CC7.2: Monitoring dashboards             │     │
│  │ - CC7.3: Incident response plan            │     │
│  │                                             │     │
│  │ HIPAA Controls (for PHI workloads)         │     │
│  │ - Dedicated node pools (tainted)           │     │
│  │ - Enhanced encryption (FIPS 140-2)         │     │
│  │ - BAA with AWS                             │     │
│  │ - PHI access logging                       │     │
│  │                                             │     │
│  │ GDPR Controls                              │     │
│  │ - Data residency (EU regions)              │     │
│  │ - Right to deletion (automated)            │     │
│  │ - Data processing records                  │     │
│  └────────────────────────────────────────────┘     │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### Key Security Controls

**1. Zero-Trust Network**
- No implicit trust based on network location
- Default deny, explicit allow
- Pod-to-pod mTLS (Istio service mesh)
- Private EKS endpoint (VPC-only)

**2. Least-Privilege Access**
- IRSA for pod-level IAM
- RBAC for Kubernetes access
- No shared credentials, no long-lived keys
- Regular access reviews (quarterly)
- Automatic session timeout (8 hours)

**3. Data Encryption**
- At rest: KMS encryption (EBS, S3, RDS)
- In transit: TLS 1.3, mTLS
- Key rotation: Automatic (90 days)
- Per-team KMS keys (cost center isolation)

**4. Secrets Management**
- AWS Secrets Manager (automatic rotation)
- External Secrets Operator (K8s integration)
- No secrets in Git, env vars, or logs
- Secrets scanned in CI/CD (GitGuardian)

**5. Audit & Compliance**
- Complete audit trail (CloudTrail, K8s audit)
- Immutable logs (S3 WORM, 7-year retention)
- Compliance dashboards (Security Hub)
- Automated compliance checks (Config Rules)

### HIPAA-Specific Controls

For models processing PHI (Protected Health Information):

**Infrastructure Isolation**:
- Dedicated node pool with `compliance=hipaa` taint
- Encrypted EBS volumes (FIPS 140-2 KMS)
- No internet egress (strict network isolation)
- Separate VPC for PHI workloads

**Access Controls**:
- MFA required for PHI access
- Break-glass procedures for emergencies
- PHI access logged and reviewed weekly
- Minimum necessary principle

**Business Associate Agreement (BAA)**:
- BAA signed with AWS
- BAA terms in vendor contracts
- Regular BAA compliance audits

## Alternatives Considered

**Alternative 1: Minimal Security (MVP)**
- Pros: Faster to implement
- Cons: Non-compliant, high risk, blocks enterprise customers
- **Decision**: Rejected - compliance is mandatory

**Alternative 2: Commercial Security Platform (e.g., Sysdig, Aqua)**
- Pros: Comprehensive, managed
- Cons: Expensive ($200K+/year), overlaps with AWS tools
- **Decision**: Rejected - cost, AWS-native tools sufficient

**Alternative 3: Self-Built Security Tools**
- Pros: Customized for needs
- Cons: Expensive to build/maintain, reinventing wheel
- **Decision**: Rejected - use proven tools (Falco, GuardDuty)

## Consequences

### Positive
✅ **Compliant**: Meets SOC2, HIPAA, GDPR requirements
✅ **Secure**: Defense-in-depth, zero-trust
✅ **Auditable**: Complete audit trail (7 years)
✅ **Automated**: Compliance checks automated (Config Rules)
✅ **Cost-Effective**: AWS-native tools ($50K/year vs $200K+ commercial)

### Negative
⚠️ **Complexity**: Multiple security layers to manage
- *Mitigation*: Automation, IaC (Terraform), runbooks

⚠️ **Operational Overhead**: Security monitoring, incident response
- *Mitigation*: Dedicated security engineer, on-call rotation

⚠️ **Development Friction**: Security controls slow some operations
- *Mitigation*: Self-service tools, clear documentation, training

## Implementation

**Phase 1** (Months 1-2): Network security, IAM/RBAC
**Phase 2** (Months 3-4): Encryption, secrets management
**Phase 3** (Months 5-6): Audit logging, monitoring
**Phase 4** (Months 7-9): HIPAA controls, SOC2 audit preparation
**Phase 5** (Months 10-12): SOC2 Type II audit

**Cost**: $50K/year (AWS security tools) + $150K (security engineer)

## Success Metrics

| Metric | Target |
|--------|--------|
| SOC2 Audit Findings | 0 |
| Security Incidents | <1 per year |
| Mean Time to Detect (MTTD) | <15 minutes |
| Mean Time to Respond (MTTR) | <2 hours |
| Vulnerability Remediation | <7 days (critical) |
| Access Review Completion | 100% quarterly |

## Related Decisions
- [ADR-003: Multi-Tenancy Design](./003-multi-tenancy-design.md) - Namespace isolation
- [ADR-008: Kubernetes Distribution](./008-kubernetes-distribution.md) - EKS security features
- [ADR-010: Governance Framework](./010-governance-framework.md) - Model governance

---

**Approved by**: CTO, Security Architect, Chief Compliance Officer, Principal Architect
**Date**: 2024-10-19
