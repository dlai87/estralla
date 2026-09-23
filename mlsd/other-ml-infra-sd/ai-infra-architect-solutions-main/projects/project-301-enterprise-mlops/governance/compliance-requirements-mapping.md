# Compliance Requirements Mapping

## Document Information

- **Document ID**: GOV-003
- **Version**: 1.0.0
- **Last Updated**: 2025-10-17
- **Owner**: Compliance Team / AI Infrastructure Architecture
- **Status**: Active
- **Related Documents**:
  - GOV-001: Model Governance Framework
  - GOV-002: Data Governance Policy
  - ADR-007: Security & Compliance Architecture

## Executive Summary

This document provides comprehensive mapping of regulatory and compliance requirements to the Enterprise MLOps Platform's controls, policies, and technical implementations. It covers SOC 2 Type II, HIPAA, GDPR, and CCPA requirements with specific evidence locations and responsible parties.

This mapping serves as:
1. **Audit Preparation**: Quick reference for auditors and assessment teams
2. **Gap Analysis**: Identify areas needing additional controls
3. **Compliance Monitoring**: Track control effectiveness
4. **Implementation Guide**: Direct engineers to compliance requirements

### Compliance Framework Status

| Framework | Status | Last Assessment | Next Assessment | Certification |
|-----------|--------|----------------|-----------------|---------------|
| SOC 2 Type II | ✅ Compliant | 2024-12-15 | 2025-12-15 | Active |
| HIPAA | ✅ Compliant | 2025-01-10 | 2025-07-10 | Active |
| GDPR | ✅ Compliant | 2025-02-20 | 2025-08-20 | Ongoing |
| CCPA | ✅ Compliant | 2025-02-20 | 2025-08-20 | Ongoing |
| ISO 27001 | 🔄 In Progress | - | 2026-06-01 | Target |

## 1. SOC 2 Type II Requirements Mapping

### 1.1 Common Criteria (CC)

#### CC1: Control Environment

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC1.1 | Organization demonstrates commitment to integrity and ethical values | Code of Conduct, Ethics Policy, Background checks for employees | `/policies/code-of-conduct.pdf` | HR |
| CC1.2 | Board of directors demonstrates independence and oversight | Quarterly board reviews, Audit committee oversight | Board minutes | Executive |
| CC1.3 | Management establishes structures, reporting lines, authorities, and responsibilities | Org chart, RACI matrix, Governance framework | `/docs/organization-structure.md` | HR |
| CC1.4 | Organization demonstrates commitment to competence | Training programs, Role-based certifications, Performance reviews | Learning management system | HR/Engineering |
| CC1.5 | Organization holds individuals accountable | Performance metrics, Code reviews, Incident accountability | Performance review system | Management |

#### CC2: Communication and Information

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC2.1 | Organization obtains or generates relevant, quality information | Automated monitoring, Data quality checks, Logging infrastructure | CloudWatch, Prometheus dashboards | Platform Eng |
| CC2.2 | Organization internally communicates information necessary to support functioning of internal control | Slack channels, Email distribution lists, Status pages, Weekly all-hands | Slack archives, Email logs | Engineering |
| CC2.3 | Organization communicates with external parties | Customer notifications, Privacy policy, Terms of service, Incident communications | Website, Email records | Product/Legal |

#### CC3: Risk Assessment

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC3.1 | Organization specifies objectives with sufficient clarity | Business case, Architecture docs, Project roadmaps | `/business/business-case.md` | Product/Eng |
| CC3.2 | Organization identifies and assesses risks | Risk assessment, Threat modeling, Vendor assessments | `/business/risk-assessment.md` | Security/Eng |
| CC3.3 | Organization considers potential for fraud | Fraud detection models, Access controls, Separation of duties | Audit logs, RBAC policies | Security |
| CC3.4 | Organization identifies and assesses changes | Change management process, CAB reviews, Impact analysis | CAB meeting minutes | Engineering |

#### CC4: Monitoring Activities

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC4.1 | Organization selects, develops, and performs ongoing and/or separate evaluations | Automated monitoring, Security scanning, Internal audits | Prometheus, GuardDuty alerts | Security/SRE |
| CC4.2 | Organization evaluates and communicates deficiencies | Incident management, Retrospectives, Corrective action tracking | Jira tickets, Incident reports | Engineering |

#### CC5: Control Activities

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC5.1 | Organization selects and develops control activities | Governance framework, Security controls, Operational procedures | Governance docs, Runbooks | Engineering |
| CC5.2 | Organization selects and develops general controls over technology | Access controls, Encryption, Patch management, Network security | AWS Config, Security Hub | Security |
| CC5.3 | Organization deploys control activities through policies and procedures | Standard operating procedures, Deployment runbooks, Incident response | `/docs/runbooks/` | SRE |

#### CC6: Logical and Physical Access Controls

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC6.1 | Organization implements logical access security measures | AWS IAM, Multi-factor authentication, Role-based access control (RBAC) | IAM policies, Okta logs | Security |
| CC6.2 | Organization restricts logical access | Principle of least privilege, Access reviews (quarterly), Just-in-time access | IAM access analyzer, Review records | Security |
| CC6.3 | Organization manages access credentials | Password policies, MFA enforcement, Credential rotation, Secrets management | Okta, AWS Secrets Manager | Security |
| CC6.4 | Organization restricts physical access | AWS-managed data centers (SOC compliance), Badge access logs (office) | AWS compliance reports | Facilities/AWS |
| CC6.5 | Organization removes access when no longer required | Automated de-provisioning, Termination checklist, Access reviews | HR tickets, IAM logs | HR/Security |
| CC6.6 | Organization manages endpoints | Endpoint detection and response (EDR), Device encryption, Mobile device management (MDM) | CrowdStrike, Jamf | Security |
| CC6.7 | Organization restricts access to IT resources | Network segmentation, Security groups, VPC isolation, WAF | AWS network config | Security/Network |
| CC6.8 | Organization implements controls to prevent or detect malicious software | Antivirus, Vulnerability scanning, Container scanning, SIEM | GuardDuty, ECR scanning | Security |

#### CC7: System Operations

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC7.1 | Organization ensures system is designed and operated in compliance with requirements | Architecture review, Security assessment, Compliance mapping | ARCHITECTURE.md, This document | Architecture |
| CC7.2 | Organization monitors system components | Infrastructure monitoring, Application monitoring, Log aggregation | Prometheus, Grafana, CloudWatch | SRE |
| CC7.3 | Organization evaluates incidents | Incident management, Post-incident reviews, Root cause analysis | PagerDuty, Incident reports | SRE |
| CC7.4 | Organization identifies and addresses problems | Ticketing system, Problem management, Change management | Jira, CAB minutes | Engineering |
| CC7.5 | Organization implements controls to prevent unauthorized changes | Change management, Code review, Infrastructure as Code (IaC) | GitHub PR reviews, Terraform | Engineering |

#### CC8: Change Management

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC8.1 | Organization authorizes, designs, develops, configures, documents, tests, approves, and implements changes | Change Advisory Board (CAB), Pull request process, CI/CD pipeline, Testing automation | GitHub, Jenkins, CAB minutes | Engineering |

#### CC9: Risk Mitigation

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| CC9.1 | Organization identifies, selects, and develops risk mitigation activities | Risk register, Mitigation strategies, Security controls | `/business/risk-assessment.md` | Security/Eng |
| CC9.2 | Organization assesses and manages risks associated with vendors and business partners | Vendor risk assessment, Due diligence, Ongoing monitoring, Business associate agreements | Vendor assessment docs | Procurement/Legal |

### 1.2 Additional Criteria for Availability (A)

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| A1.1 | Organization maintains, monitors, and evaluates current processing capacity | Resource monitoring, Capacity planning, Auto-scaling, Load testing | Prometheus metrics, Load test reports | SRE |
| A1.2 | Organization authorizes, designs, develops, implements, operates, approves, maintains, and monitors environmental protections | AWS infrastructure (climate controlled, redundant power), Monitoring of environmental controls | AWS SOC 2 report | AWS/Facilities |
| A1.3 | Organization authorizes, designs, develops, implements, operates, approves, maintains, and monitors procedures for recovery and failover | Disaster recovery plan, Automated backups, Multi-AZ deployment, Failover testing | DR runbooks, RTO/RPO metrics | SRE |

### 1.3 Additional Criteria for Confidentiality (C)

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| C1.1 | Organization identifies and maintains confidential information | Data classification, Metadata tagging, Data catalog | Data catalog, Classification tags | Data Governance |
| C1.2 | Organization disposes of confidential information | Secure deletion procedures, Cryptographic erasure, Data retention policies | Retention policy docs | Data Governance |

### 1.4 Additional Criteria for Processing Integrity (PI)

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| PI1.1 | Organization obtains or generates, uses, and communicates relevant, quality information regarding the objectives related to processing | Data quality framework, Validation checks, Model monitoring | Data quality dashboards | Data Engineering |
| PI1.2 | Organization implements policies and procedures over system inputs | Input validation, Schema enforcement, Data contracts | API validations, Schema registry | Engineering |
| PI1.3 | Organization implements policies and procedures over system processing | Processing controls, Idempotent operations, Error handling | Pipeline code, Tests | Data Engineering |
| PI1.4 | Organization implements policies and procedures to make available or deliver output | API rate limiting, Access controls, Monitoring | API gateway config | Engineering |
| PI1.5 | Organization implements policies and procedures to store inputs, items in processing, and outputs | Data versioning, Immutable storage, Backup procedures | S3 versioning, Backup logs | Data Engineering |

### 1.5 Additional Criteria for Privacy (P)

| Control ID | Control Requirement | Platform Implementation | Evidence Location | Owner |
|------------|-------------------|------------------------|------------------|-------|
| P1.1 | Organization provides notice to data subjects | Privacy policy, Cookie notices, Terms of service | Website privacy page | Legal/Product |
| P2.1 | Organization communicates choices available regarding collection, use, retention, disclosure, and disposal | Consent management, Opt-out mechanisms, Cookie preferences | Consent management platform | Product/Legal |
| P3.1 | Organization collects personal information only for purposes identified in notice | Purpose limitation, Data minimization, Collection controls | Data governance policy | Data Governance |
| P3.2 | Organization retains personal information for time necessary to fulfill stated purposes | Retention policies, Automated deletion, Legal hold management | Retention schedules | Data Governance |
| P4.1 | Organization limits use of personal information to purposes identified in notice | Access controls, Purpose tracking, Usage auditing | Audit logs | Security |
| P4.2 | Organization retains personal information consistent with its objectives | Retention policies aligned with business case | GOV-002 | Data Governance |
| P4.3 | Organization securely disposes of personal information | Secure deletion, Cryptographic erasure, Certificate of destruction | Deletion logs | Data Engineering |
| P5.1 | Organization grants identified and authenticated data subjects ability to access their personal information | Self-service portal, DSR automation, Identity verification | Privacy portal | Product/Legal |
| P5.2 | Organization corrects personal information | Data correction workflows, Propagation to downstream systems | DSR logs | Data Engineering |
| P6.1 | Organization obtains consent for collection, use, retention, disclosure, and disposal | Consent management, Opt-in workflows, Consent records | Consent platform | Product/Legal |
| P6.2 | Organization provides data subjects with mechanism to revoke consent | Opt-out mechanism, Consent withdrawal, Data deletion | Privacy portal | Product/Legal |
| P7.1 | Organization discloses personal information to third parties with consent | Vendor agreements, Data processing agreements (DPA), Disclosure logs | DPA repository | Legal |
| P8.1 | Organization implements process to receive and respond to inquiries, complaints, and disputes | Privacy mailbox, DSR portal, Complaint tracking | Support ticketing system | Legal/Support |

## 2. HIPAA Requirements Mapping

### 2.1 Administrative Safeguards (§164.308)

#### Security Management Process (§164.308(a)(1))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(1)(i) | Risk Analysis (R) | Annual risk assessment, Threat modeling, Vulnerability scanning | Risk assessment document | Security |
| §164.308(a)(1)(ii)(A) | Risk Management (R) | Risk register, Mitigation plans, Security controls | Risk management plan | Security |
| §164.308(a)(1)(ii)(B) | Sanction Policy (R) | Employee handbook, Incident response, Disciplinary procedures | HR policies | HR |
| §164.308(a)(1)(ii)(C) | Information System Activity Review (R) | SIEM, Audit log review, Quarterly access reviews | CloudWatch Logs, Splunk | Security |

#### Assigned Security Responsibility (§164.308(a)(2))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(2) | Security Official (R) | Designated HIPAA Security Officer, Contact info published | Security team page | CISO |

#### Workforce Security (§164.308(a)(3))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(3)(i) | Authorization/Supervision (A) | Manager approval for PHI access, Documented authorization | Access request tickets | Managers |
| §164.308(a)(3)(ii)(A) | Workforce Clearance (A) | Background checks, HIPAA training required before PHI access | HR records | HR |
| §164.308(a)(3)(ii)(B) | Termination Procedures (A) | Automated access revocation upon termination, Exit checklist | HR/IAM integration | HR/Security |

#### Information Access Management (§164.308(a)(4))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(4)(i) | Isolating Healthcare Clearinghouse (R) | N/A - Not a clearinghouse | - | - |
| §164.308(a)(4)(ii)(A) | Access Authorization (A) | Role-based access control (RBAC), Minimum necessary principle, Access request workflow | IAM policies | Security |
| §164.308(a)(4)(ii)(B) | Access Establishment/Modification (A) | Automated provisioning, Access reviews (quarterly), Just-in-time access | Access management logs | Security |
| §164.308(a)(4)(ii)(C) | Terminate Access (A) | Automated de-provisioning, Access removal upon role change | IAM logs | Security |

#### Security Awareness and Training (§164.308(a)(5))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(5)(i) | Security Reminders (A) | Monthly security newsletter, Phishing simulations, Security tips | Email archives | Security |
| §164.308(a)(5)(ii)(A) | Protection from Malware (A) | Antivirus (CrowdStrike), Email filtering, Training on malware threats | Security training LMS | Security |
| §164.308(a)(5)(ii)(B) | Log-in Monitoring (A) | Failed login alerts, Anomalous access detection, Session monitoring | SIEM alerts | Security |
| §164.308(a)(5)(ii)(C) | Password Management (A) | Password policy (12+ chars, complexity), MFA required, Credential manager | Okta configuration | Security |

#### Security Incident Procedures (§164.308(a)(6))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(6)(i) | Response and Reporting (R) | Incident response plan, 24/7 on-call, PagerDuty escalation, Breach assessment | Incident response plan | Security |
| §164.308(a)(6)(ii) | Breach Notification | Breach notification procedures, 60-day timeline, HHS reporting | Breach response plan | Legal/Security |

#### Contingency Plan (§164.308(a)(7))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(7)(i) | Data Backup Plan (R) | Automated daily backups, Multi-region replication, Backup testing (monthly) | Backup logs, Test results | SRE |
| §164.308(a)(7)(ii)(A) | Disaster Recovery Plan (R) | Disaster recovery plan, RPO: 1 hour, RTO: 4 hours, Annual DR testing | DR runbooks, Test results | SRE |
| §164.308(a)(7)(ii)(B) | Emergency Mode Operation (R) | Emergency procedures, Degraded mode operations, Manual processes | Emergency operations plan | SRE |
| §164.308(a)(7)(ii)(C) | Testing and Revision (A) | Annual DR test, Post-incident reviews, Plan updates | Test schedules, Review docs | SRE |
| §164.308(a)(7)(ii)(D) | Applications and Data Criticality (A) | Business impact analysis, System criticality classification, Recovery priorities | BIA document | Business Continuity |

#### Evaluation (§164.308(a)(8))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(a)(8) | Security Evaluation (R) | Annual security assessment, Penetration testing, Vulnerability scanning | Assessment reports | Security |

#### Business Associate Contracts (§164.308(b)(1))

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.308(b)(1) | Written Contract or Other Arrangement (R) | Business Associate Agreements (BAA) with all vendors processing PHI | Vendor BAAs | Legal |
| §164.308(b)(4) | Subcontractors | BAA requirements flow down to subcontractors | Subcontractor BAAs | Legal |

### 2.2 Physical Safeguards (§164.310)

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.310(a)(1) | Facility Access Controls (R) | AWS managed data centers (SOC compliance), Badge access for office | AWS compliance report, Badge logs | AWS/Facilities |
| §164.310(a)(2)(i) | Contingency Operations (A) | Alternate processing site (multi-region), Failover procedures | DR plan | SRE |
| §164.310(a)(2)(ii) | Facility Security Plan (A) | AWS physical security, Office security procedures | AWS compliance docs, Facility plan | AWS/Facilities |
| §164.310(a)(2)(iii) | Access Control and Validation (A) | Badge access, Visitor logs, Security cameras | Access logs | Facilities |
| §164.310(a)(2)(iv) | Maintenance Records (A) | AWS maintenance (managed), Office facility maintenance logs | Maintenance records | Facilities |
| §164.310(b) | Workstation Use (R) | Workstation security policy, Screen lock (5 min), Clear desk policy | Security policy | Security |
| §164.310(c) | Workstation Security (R) | Endpoint encryption, EDR (CrowdStrike), MDM (Jamf) | Device inventory | Security |
| §164.310(d)(1) | Device and Media Controls (R) | Media disposal policy, Cryptographic erasure, Certificate of destruction | Disposal records | Security |
| §164.310(d)(2)(i) | Disposal (R) | Secure deletion procedures, Degaussing for magnetic media, Destruction for paper | Asset disposal logs | Security |
| §164.310(d)(2)(ii) | Media Re-use (R) | Secure wipe before re-use, Encryption verification | Device lifecycle records | IT |
| §164.310(d)(2)(iii) | Accountability (A) | Asset inventory, Chain of custody, Check-in/check-out logs | Asset management system | IT |
| §164.310(d)(2)(iv) | Data Backup and Storage (A) | Encrypted backups, Offsite storage (S3), Retention per policy | Backup configuration | SRE |

### 2.3 Technical Safeguards (§164.312)

| Requirement | Standard/Implementation Spec | Platform Implementation | Evidence Location | Owner |
|------------|----------------------------|------------------------|------------------|-------|
| §164.312(a)(1) | Access Control (R) | Role-based access control (RBAC), Principle of least privilege | IAM policies | Security |
| §164.312(a)(2)(i) | Unique User Identification (R) | Individual user accounts (no shared), Email as username | Okta user list | Security |
| §164.312(a)(2)(ii) | Emergency Access (R) | Break-glass procedures, Temporary elevated access, Logged and reviewed | Emergency access logs | Security |
| §164.312(a)(2)(iii) | Automatic Logoff (A) | 15-minute session timeout, Idle session termination | Application config | Engineering |
| §164.312(a)(2)(iv) | Encryption/Decryption (A) | AES-256 encryption at rest, TLS 1.3 in transit, FIPS 140-2 for PHI | Encryption config | Security |
| §164.312(b) | Audit Controls (R) | Comprehensive audit logging, CloudWatch Logs, Splunk SIEM, 7-year retention | Logging configuration | Security |
| §164.312(c)(1) | Integrity (R) | Checksums for data integrity, Version control, Immutable logs | Data integrity checks | Engineering |
| §164.312(c)(2) | Mechanism to Authenticate ePHI (A) | Digital signatures, Hash verification, Audit trails | Authentication mechanisms | Engineering |
| §164.312(d) | Person or Entity Authentication (R) | Multi-factor authentication (MFA) required for PHI access, Okta SSO | Okta MFA config | Security |
| §164.312(e)(1) | Transmission Security (R) | TLS 1.3 for data in transit, VPN for remote access, No unencrypted PHI transmission | Network config | Network/Security |
| §164.312(e)(2)(i) | Integrity Controls (A) | TLS integrity checks, Checksums for file transfers | Transfer logs | Engineering |
| §164.312(e)(2)(ii) | Encryption (A) | Mandatory encryption for PHI transmission, Certificate-based authentication | Encryption policies | Security |

**Note**: (R) = Required implementation specification, (A) = Addressable implementation specification

## 3. GDPR Requirements Mapping

### 3.1 Lawfulness, Fairness, and Transparency (Art. 5(1)(a))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 6 | Lawfulness of processing | Legal basis documented per dataset, Consent management, Legitimate interest assessments | Data catalog metadata | Legal/Data Gov |
| Art. 12 | Transparent information | Privacy policy, Cookie notices, Clear language, Free of charge | Website privacy page | Legal/Product |
| Art. 13 | Information to be provided (direct collection) | Privacy notice at collection, Purpose disclosure, Retention periods, Rights information | Data collection forms | Product |
| Art. 14 | Information to be provided (indirect collection) | Notification within 1 month, Source disclosure, Categories disclosed | Notification logs | Product |

### 3.2 Purpose Limitation (Art. 5(1)(b))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(1)(b) | Purpose limitation | Purpose documented in data catalog, Usage monitoring, Access controls by purpose | Data catalog, Audit logs | Data Governance |
| Art. 6(4) | Compatible further processing | Compatibility assessment required, Link between purposes, Safeguards documented | Compatibility assessments | Legal |

### 3.3 Data Minimization (Art. 5(1)(c))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(1)(c) | Data minimization | Required fields only, Purpose-based collection limits, Regular data reviews | Schema definitions | Data Governance |
| Art. 32(1) | Pseudonymization | Pseudonymization for ML training, Token-based access, Separate key storage | Pseudonymization configs | Engineering |

### 3.4 Accuracy (Art. 5(1)(d))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(1)(d) | Accuracy | Data quality framework, Validation checks, Correction workflows | Data quality dashboards | Data Engineering |
| Art. 16 | Right to rectification | Self-service correction portal, 72-hour update SLA, Propagation to all systems | DSR portal | Product/Engineering |

### 3.5 Storage Limitation (Art. 5(1)(e))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(1)(e) | Storage limitation | Retention policies per data type, Automated deletion, Legal hold management | Retention schedules | Data Governance |
| Art. 17 | Right to erasure | 30-day deletion SLA, Automated erasure workflows, Verification procedures | DSR logs | Engineering |

### 3.6 Integrity and Confidentiality (Art. 5(1)(f))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(1)(f) | Security | Encryption (AES-256 at rest, TLS 1.3 in transit), Access controls (RBAC), Security monitoring | Security configuration | Security |
| Art. 32 | Security of processing | Risk-based security measures, Pseudonymization, Regular security testing, Incident response plan | Security assessments | Security |
| Art. 33 | Breach notification to authority | 72-hour breach notification to DPA, Breach assessment procedures, Notification templates | Incident response plan | Legal/Security |
| Art. 34 | Breach notification to data subjects | Notification to affected individuals (high risk), Clear communication, Mitigation measures disclosed | Breach notification plan | Legal |

### 3.7 Accountability (Art. 5(2))

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 5(2) | Accountability | Records of processing activities, Data protection policies, Audit trails, DPO appointed | Processing records | DPO |
| Art. 24 | Controller responsibility | Data protection by design and default, Regular reviews, Staff training | Compliance dashboard | DPO |
| Art. 25 | Data protection by design | Privacy impact assessments, Default privacy settings, Minimization built-in | DPIA documents | Engineering/DPO |
| Art. 30 | Records of processing | Processing activity register, Updated regularly, Available to supervisory authority | Processing register | DPO |
| Art. 35 | Data protection impact assessment (DPIA) | DPIA for high-risk processing, Consultations documented, Mitigation measures | DPIA repository | DPO |
| Art. 37-39 | Data Protection Officer | DPO appointed and contact published, Independent, Expert knowledge | DPO designation | Executive |

### 3.8 Data Subject Rights

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 15 | Right of access | Self-service DSR portal, 30-day SLA (1 month), Machine-readable format, Free of charge | DSR portal | Product |
| Art. 16 | Right to rectification | Correction workflows, 72-hour SLA, Propagation to downstream | DSR system | Engineering |
| Art. 17 | Right to erasure | Deletion workflows, 30-day SLA, Exceptions documented | DSR system | Engineering |
| Art. 18 | Right to restriction | Processing restriction capability, Marked records, Limited processing | DSR system | Engineering |
| Art. 20 | Right to data portability | Export in JSON/CSV, Automated export, Direct transmission if feasible | DSR portal | Product |
| Art. 21 | Right to object | Objection workflows, Opt-out mechanisms, Processing stopped unless compelling basis | Consent management | Product |
| Art. 22 | Automated decision-making and profiling | Human review for significant decisions, Explainability, Opt-out available, Logic disclosed | Model governance | Data Science |

### 3.9 International Data Transfers

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 44-50 | Transfers to third countries | Adequacy decision compliance (US-EU Data Privacy Framework), Standard Contractual Clauses (SCCs), Transfer Impact Assessments (TIA) | SCCs, TIA documents | Legal |
| Art. 46 | Appropriate safeguards | EU data stored in eu-west-1 (Ireland), US data in us-east-1, Data residency controls | AWS region config | Engineering |

### 3.10 Vendor Management

| Article | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| Art. 28 | Processor obligations | Data Processing Agreements (DPA) with all processors, Subprocessor approval, Security requirements, Audit rights | Vendor DPAs | Legal |
| Art. 28(3) | Written contract requirements | DPA template with all required clauses, Legal review, Countersignature | DPA template | Legal |

## 4. CCPA Requirements Mapping

### 4.1 Consumer Rights

| Section | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| §1798.100 | Right to know (categories) | Annual disclosure of data categories collected | Privacy policy | Legal |
| §1798.110 | Right to know (specific pieces) | DSR portal for data access, 45-day SLA, 2 free requests per year | DSR portal | Product |
| §1798.105 | Right to delete | Deletion workflows, 45-day SLA, Exceptions documented (legal obligation, etc.) | DSR system | Engineering |
| §1798.115 | Right to know (sale/disclosure) | Annual disclosure, Categories of third parties, Business purpose | Privacy policy | Legal |
| §1798.120 | Right to opt-out of sale | "Do Not Sell My Personal Information" link, Opt-out mechanism, No sale without consent | Website, Consent mgmt | Product/Legal |
| §1798.121 | Right to limit use of sensitive personal information | Opt-in for sensitive data uses beyond what's necessary | Consent management | Product |
| §1798.130 | Notice at collection | Notice at or before collection, Categories, Purposes, Retention periods, Rights information | Data collection forms | Product |
| §1798.135 | Opt-out and opt-in rights | Clear opt-out for sale, Opt-in for <13 years old, Opt-in for sensitive data | Consent management | Product |

### 4.2 Business Obligations

| Section | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| §1798.100(b) | Disclosure requirements | Privacy policy updated annually, Posted on website, Accessible format | Website privacy page | Legal |
| §1798.130(a)(5) | Two or more methods for requests | Online DSR portal, Toll-free number, Email address | Contact us page | Product/Support |
| §1798.140(w) | Definition of "sell" | Verification that no personal information is sold for monetary value, Vendor contracts prohibit sale | Vendor contracts | Legal |
| §1798.145(a)(3) | Service provider exception | Service provider agreements with required provisions, Purpose limitation, Compliance certification | Service provider agreements | Legal |
| §1798.145(m) | Employee data exception | Separate notices for employee data, B2B contact exemption applied | Employee privacy notice | HR/Legal |
| §1798.150 | Private right of action (data breaches) | Security measures to prevent breach, Incident response plan, Notification procedures | Security program | Security |
| §1798.155 | Enforcement and compliance | Annual compliance review, Records of DSRs, Training for staff | Compliance dashboard | Legal/Privacy |

### 4.3 Verification and Security

| Section | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| §1798.185(a)(7) | Verification methods | Multi-factor authentication for DSRs, Identity verification procedures, Risk-based verification | DSR portal | Product/Security |
| §999.323 | Verification for deletion | Match 2-3 data points for verification, Higher bar for sensitive data | DSR verification logic | Engineering |
| §999.325 | Authorized agent | Authorized agent portal, Written authorization required, Verify consumer identity | Agent portal | Product |

### 4.4 Non-Discrimination

| Section | Requirement | Platform Implementation | Evidence Location | Owner |
|---------|------------|------------------------|------------------|-------|
| §1798.125 | Non-discrimination | No denial of goods/services, Same price/quality, No suggestion of inferior service | Product design | Product |
| §1798.125(b)(1) | Financial incentive | Notice of financial incentives, Material terms disclosed, Opt-in required, Withdrawable | Incentive programs | Marketing/Legal |

## 5. Cross-Framework Control Mapping

### 5.1 Encryption Controls

| Framework | Requirement | Control Implementation | Testing/Validation |
|-----------|------------|----------------------|-------------------|
| SOC 2 | CC6.7 - Encryption in transit | TLS 1.3 for all external connections, TLS 1.2 minimum for internal | SSL Labs scan (A+ rating) |
| SOC 2 | C1.1 - Encryption at rest | AES-256 encryption for all storage | AWS Config rule verification |
| HIPAA | §164.312(a)(2)(iv) - Encryption | FIPS 140-2 encryption for PHI | FIPS compliance testing |
| HIPAA | §164.312(e)(2)(ii) - Transmission encryption | Mandatory encryption for PHI transmission | Network traffic analysis |
| GDPR | Art. 32 - Security measures | Encryption as appropriate security measure | Penetration test validation |
| GDPR | Art. 6(4)(e) - Safeguards for further processing | Encryption for secondary uses | Technical assessment |

**Evidence**: `/security/encryption-standards.md`, AWS KMS configuration, SSL certificates

### 5.2 Access Control

| Framework | Requirement | Control Implementation | Testing/Validation |
|-----------|------------|----------------------|-------------------|
| SOC 2 | CC6.1 - Logical access controls | AWS IAM with MFA, Okta SSO | IAM Access Analyzer |
| SOC 2 | CC6.2 - Least privilege | Role-based access control (RBAC), Just-in-time access | Quarterly access reviews |
| HIPAA | §164.312(a)(1) - Access control | RBAC with minimum necessary principle | Access audit logs |
| HIPAA | §164.308(a)(4) - Information access management | Access request workflow, Manager approval | Access request tickets |
| GDPR | Art. 32(1)(b) - Ability to ensure confidentiality | Access controls limit data exposure | Access pattern analysis |
| CCPA | §1798.185(a)(7) - Verification | MFA for DSRs, Identity verification | DSR audit logs |

**Evidence**: IAM policies, Access review reports, RBAC role definitions

### 5.3 Audit Logging

| Framework | Requirement | Control Implementation | Testing/Validation |
|-----------|------------|----------------------|-------------------|
| SOC 2 | CC7.2 - Monitoring | CloudWatch, Prometheus, Grafana dashboards | Alert testing |
| SOC 2 | CC4.1 - Ongoing evaluations | Automated log analysis, SIEM alerts | Incident detection time |
| HIPAA | §164.312(b) - Audit controls | Comprehensive audit logging, 7-year retention | Log completeness audit |
| HIPAA | §164.308(a)(1)(ii)(C) - Activity review | Quarterly log review, Anomaly detection | Review meeting minutes |
| GDPR | Art. 5(2) - Accountability | Audit trails for all personal data processing | Log sampling |
| GDPR | Art. 30 - Records of processing | Processing activity logs maintained | Records register review |

**Evidence**: CloudWatch Logs configuration, Splunk SIEM, Log retention policies

### 5.4 Data Subject Rights / DSR

| Framework | Requirement | Control Implementation | Testing/Validation |
|-----------|------------|----------------------|-------------------|
| SOC 2 | P5.1 - Data subject access | Self-service DSR portal | Portal functionality test |
| SOC 2 | P5.2 - Data correction | Correction workflows with propagation | End-to-end testing |
| HIPAA | §164.524 - Access to PHI | Individual access within 30 days | DSR SLA tracking |
| HIPAA | §164.526 - Amendment of PHI | Amendment procedures documented | Amendment logs |
| GDPR | Art. 15-22 - Data subject rights | Comprehensive DSR portal supporting all rights | Annual rights exercise test |
| GDPR | Art. 12(3) - Timing | 30-day SLA (1 month), Extension with justification | DSR completion metrics |
| CCPA | §1798.100-120 - Consumer rights | DSR portal with all CCPA rights, 45-day SLA | DSR audit |

**Evidence**: DSR portal, DSR logs, SLA metrics dashboard

### 5.5 Vendor Management

| Framework | Requirement | Control Implementation | Testing/Validation |
|-----------|------------|----------------------|-------------------|
| SOC 2 | CC9.2 - Vendor risk management | Vendor risk assessment, Due diligence, Ongoing monitoring | Vendor assessment docs |
| HIPAA | §164.308(b) - Business associate contracts | BAAs with all PHI processors | BAA repository |
| HIPAA | §164.314(a)(2)(i) - Subcontractors | BAA requirements for subcontractors | Subcontractor list |
| GDPR | Art. 28 - Processor obligations | DPAs with required clauses, Audit rights | DPA repository |
| GDPR | Art. 28(2) - Subprocessor approval | Subprocessor list, Prior authorization | Subprocessor register |
| CCPA | §1798.140(w)(2)(C) - Service providers | Service provider agreements, No sale clauses | Contract audit |

**Evidence**: Vendor assessment templates, BAA/DPA templates, Vendor risk register

## 6. Compliance Evidence Repository

### 6.1 Document Locations

| Category | Document | Location | Update Frequency |
|----------|----------|----------|------------------|
| Policies | Information Security Policy | `/policies/information-security-policy.pdf` | Annual |
| Policies | Data Governance Policy | `GOV-002` | Semi-annual |
| Policies | Model Governance Framework | `GOV-001` | Semi-annual |
| Policies | Incident Response Plan | `/security/incident-response-plan.md` | Annual |
| Policies | Disaster Recovery Plan | `/operations/disaster-recovery-plan.md` | Annual |
| Policies | Privacy Policy (External) | `https://company.com/privacy` | As needed |
| Architecture | Architecture Documentation | `ARCHITECTURE.md` | Quarterly |
| Architecture | Architecture Decision Records | `/architecture/adrs/*.md` | As created |
| Architecture | Security Architecture | `ADR-007` | Annual |
| Business | Risk Assessment | `/business/risk-assessment.md` | Quarterly |
| Business | Business Impact Analysis | `/business/business-case.md` | Annual |
| Compliance | This Document | `GOV-003` | Quarterly |
| Compliance | SOC 2 Report | `/compliance/soc2-report-2024.pdf` | Annual |
| Compliance | HIPAA Risk Analysis | `/compliance/hipaa-risk-analysis-2025.pdf` | Annual |
| Compliance | DPIA Repository | `/compliance/dpias/` | As needed |
| Training | Security Awareness Training | Learning Management System | Annual |
| Training | HIPAA Training Records | LMS + HR System | Annual |
| Training | Role-Based Training | LMS | Annual |
| Operations | Runbooks | `/docs/runbooks/` | Quarterly |
| Operations | Change Management Logs | Jira | Continuous |
| Operations | Incident Logs | PagerDuty + Jira | Continuous |
| Security | Access Review Reports | `/security/access-reviews/` | Quarterly |
| Security | Penetration Test Reports | `/security/pentests/` | Annual |
| Security | Vulnerability Scan Reports | Security Hub | Weekly |
| Audit | Audit Logs | CloudWatch Logs + S3 | Continuous (7-year retention) |
| Audit | CAB Meeting Minutes | `/governance/cab-minutes/` | Weekly |
| Audit | DSR Logs | Privacy Portal Database | Continuous (7-year retention) |

### 6.2 Automated Compliance Monitoring

**Daily Checks**:
- Encryption verification (AWS Config)
- Access control validation (IAM Access Analyzer)
- Vulnerability scanning (Security Hub)
- Log integrity checks (CloudWatch)
- Data classification verification (Data Catalog)

**Weekly Checks**:
- Security group configuration review
- Exposed data scan (DLP)
- Certificate expiration monitoring
- Backup validation
- Vendor compliance status

**Monthly Checks**:
- Access reviews for sensitive data
- Security metrics reporting
- Training completion tracking
- Policy exception reviews
- Incident trend analysis

**Quarterly Checks**:
- Comprehensive access recertification
- Risk assessment updates
- Policy effectiveness reviews
- Third-party audit preparation
- Compliance metric dashboards

**Annual Checks**:
- SOC 2 audit
- HIPAA risk analysis
- Penetration testing
- Policy comprehensive review
- Training curriculum updates
- Vendor comprehensive assessment

## 7. Audit Readiness

### 7.1 Audit Preparation Checklist

**30 Days Before Audit**:
- [ ] Review all evidence locations
- [ ] Ensure documents are current
- [ ] Run compliance scans
- [ ] Prepare evidence packages
- [ ] Identify any gaps
- [ ] Assign audit liaisons

**7 Days Before Audit**:
- [ ] Conduct mock audit
- [ ] Prepare conference rooms
- [ ] Ensure system access for auditors
- [ ] Gather evidence samples
- [ ] Brief audit participants
- [ ] Prepare opening presentation

**During Audit**:
- [ ] Daily status meetings
- [ ] Evidence tracking
- [ ] Issue log maintenance
- [ ] Timely response to requests
- [ ] Document open items

**Post-Audit**:
- [ ] Address findings
- [ ] Update documentation
- [ ] Implement corrective actions
- [ ] Schedule follow-up audits
- [ ] Update compliance calendar

### 7.2 Common Audit Requests

| Request Category | Typical Evidence | Preparation Notes |
|-----------------|------------------|-------------------|
| Access Controls | IAM policies, RBAC roles, Access review reports | Export from AWS IAM, Prepare narratives |
| Encryption | KMS configuration, TLS certificates, Encryption validation | AWS Config reports, SSL Labs results |
| Logging | Log configuration, Sample logs, Retention validation | CloudWatch setup, S3 lifecycle policies |
| Change Management | CAB minutes, Change tickets, Deployment logs | Jira reports, GitHub PR logs |
| Incident Management | Incident tickets, Retrospectives, Response times | PagerDuty reports, Incident summaries |
| Vendor Management | Vendor assessments, BAAs/DPAs, Monitoring reports | Vendor repository exports |
| Training | Training records, Completion rates, Test scores | LMS reports |
| Data Subject Rights | DSR logs, Response times, Completed requests | DSR portal exports |
| Policies | All current policies, Version history, Approval records | Policy repository |
| Risk Management | Risk register, Mitigation status, Review meeting minutes | Risk tracking system |

## 8. Compliance Contacts

### 8.1 Internal Contacts

| Role | Name | Email | Phone | Responsibilities |
|------|------|-------|-------|-----------------|
| Chief Information Security Officer (CISO) | TBD | ciso@company.com | - | Overall security & compliance |
| HIPAA Security Officer | TBD | hipaa-security@company.com | - | HIPAA compliance program |
| Data Protection Officer (DPO) | TBD | dpo@company.com | - | GDPR/CCPA compliance, DSRs |
| Compliance Manager | TBD | compliance@company.com | - | SOC 2, audit coordination |
| Legal Counsel | TBD | legal@company.com | - | Regulatory interpretation |
| Privacy Manager | TBD | privacy@company.com | - | Privacy program, DSRs |
| ML Architect | TBD | ml-architecture@company.com | - | Technical compliance, platform |
| Engineering Manager | TBD | engineering@company.com | - | Implementation, remediation |

### 8.2 External Contacts

| Entity | Purpose | Contact Method |
|--------|---------|----------------|
| SOC 2 Auditor | Annual audit | Engagement letter |
| HIPAA Auditor | Risk analysis, compliance review | As needed |
| Penetration Testing Firm | Annual pentest | Annual engagement |
| Legal Counsel (External) | Regulatory advice | As needed |
| Supervisory Authority (GDPR) | Breach notification, consultations | See GDPR Art. 55-56 |
| HHS OCR (HIPAA) | Breach notification | https://ocrportal.hhs.gov/ |
| California Attorney General (CCPA) | Enforcement | https://oag.ca.gov/ |

### 8.3 Emergency Contacts

| Incident Type | Contact | Response Time | Notes |
|--------------|---------|---------------|-------|
| Data Breach | security@company.com, PagerDuty | Immediate | 24/7 on-call |
| HIPAA Breach | hipaa-security@company.com, legal@company.com | Immediate | Assess within 24 hours |
| GDPR Breach | dpo@company.com, legal@company.com | Immediate | 72-hour notification window |
| Compliance Violation | compliance@company.com | 1 business day | Document immediately |
| Audit Issue | compliance@company.com, audit-liaison@company.com | 1 business day | Track in issue log |

## 9. Compliance Calendar

### 9.1 Annual Compliance Activities

| Month | Activity | Framework | Owner |
|-------|----------|-----------|-------|
| January | SOC 2 audit kickoff | SOC 2 | Compliance |
| January | Q4 access reviews complete | All | Security |
| February | HIPAA training renewal | HIPAA | HR/Security |
| February | Annual policy review begins | All | Legal/Compliance |
| March | SOC 2 audit fieldwork | SOC 2 | Compliance |
| March | Annual penetration test | All | Security |
| April | Q1 access reviews complete | All | Security |
| April | Vendor risk assessments begin | All | Procurement |
| May | SOC 2 report issuance | SOC 2 | Compliance |
| May | GDPR/CCPA privacy audit | GDPR/CCPA | DPO |
| June | HIPAA risk analysis update | HIPAA | Security |
| July | Q2 access reviews complete | All | Security |
| July | Disaster recovery test | All | SRE |
| August | Security awareness training | All | Security |
| August | Annual policy updates approved | All | Legal |
| September | ISO 27001 prep activities (target 2026) | ISO 27001 | Compliance |
| October | Q3 access reviews complete | All | Security |
| October | Vendor risk assessment renewals | All | Procurement |
| November | Compliance metrics annual review | All | Compliance |
| November | Budget planning for compliance | All | Finance/Compliance |
| December | Year-end compliance reporting | All | Compliance |
| December | Q4 access reviews begin | All | Security |

### 9.2 Quarterly Compliance Activities

**Every Quarter**:
- Access recertification for confidential/restricted data
- Risk register updates
- Compliance metrics dashboard review
- Policy exception reviews
- Vendor compliance status checks
- CAB effectiveness review
- Incident trend analysis
- Training compliance review

### 9.3 Monthly Compliance Activities

**Every Month**:
- Security metrics reporting
- Data quality metrics review
- DSR metrics tracking
- Incident metrics review
- Change management metrics
- Backup validation tests
- Certificate expiration reviews

## 10. Document Control

### 10.1 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-17 | Compliance Team & AI Infrastructure Team | Initial compliance mapping |

### 10.2 Review and Approval

- **Authors**: Compliance Manager, HIPAA Security Officer, Data Protection Officer, ML Architect
- **Reviewed by**: Legal Counsel, CISO, Engineering Manager
- **Approved by**: Chief Compliance Officer, CTO, Chief Legal Officer
- **Next Review**: 2026-01-17 (Quarterly)

### 10.3 Related Documents

- [Model Governance Framework](./model-governance-framework.md)
- [Data Governance Policy](./data-governance-policy.md)
- [Audit Procedures](./audit-procedures.md)
- [ADR-007: Security & Compliance Architecture](../architecture/adrs/007-security-compliance-architecture.md)
- [Risk Assessment](../business/risk-assessment.md)

---

**Document Classification**: Internal Use (Sensitive)
**Last Review Date**: 2025-10-17
**Next Review Date**: 2026-01-17
